#!/usr/bin/env python3
"""Word-based Malbolge Unshackled simulator matching fast20.c semantics exactly.

A Word is a tuple (area, high, low) with:
  area ∈ {0, 1, 2}   (1 "trit")
  high ∈ [0, 59048]  (10 trits)
  low  ∈ [0, 59048]  (10 trits)
"""
import sys

XLAT_TABLE = ("5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72Fh"
              "OA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@")


def zero():
    return (0, 0, 0)


def increment(w):
    a, h, l = w
    l += 1
    if l >= 59049:
        l = 0
        h += 1
    return (a, h, l)


def crazy_low_10(a, d):
    """10-trit CRZ for the high/low fields."""
    crz = [[1,1,2],[0,0,2],[0,2,1]]
    r, k = 0, 1
    for _ in range(10):
        r += k * crz[a % 3][d % 3]
        a //= 3; d //= 3; k *= 3
    return r


def crazy(a_w, d_w):
    """Word CRZ matching fast20.c's crazy() function.
    Same flat array indexed by a + 3*d as crazy_low_10."""
    crz_flat = [1, 0, 0, 1, 0, 2, 2, 2, 1]
    return (
        crz_flat[a_w[0] + 3 * d_w[0]],
        crazy_low_10(a_w[1], d_w[1]),
        crazy_low_10(a_w[2], d_w[2]),
    )


def rotate_r(w):
    a, h, l = w
    carry_h = h % 3
    carry_l = l % 3
    return (a, 19683 * carry_l + h // 3, 19683 * carry_h + l // 3)


def encode_char(opcode, pos):
    t = (opcode - pos % 94 + 9400) % 94
    if t < 33:
        t += 94
    return t


def simulate(prog_bytes, input_bytes=b"", max_steps=2_000_000, trace=False):
    # Memory is a dict from address (area, high, low) -> Word
    # Initial program is loaded at (0, 0, p) for p = 0..len(prog)-1
    # Beyond program, lazy fill with crazy(prev, prev2)
    mem = {}
    for i, b in enumerate(prog_bytes):
        # Skip whitespace as fast20 does
        if b in (ord(' '), ord('\r'), ord('\n')):
            continue
        mem[(0, 0, len(mem))] = (0, 0, b)
    n_loaded = len(mem)

    # Post-load: fill rest of (0,0,...) up to (0,0,59048)
    def get_mem(addr):
        if addr not in mem:
            a, h, l = addr
            # Lazy initialization (simplified)
            if (a, h, l-1) in mem and (a, h, l-2) in mem:
                mem[addr] = crazy(mem[(a, h, l-1)], mem[(a, h, l-2)])
            elif h > 0 and (a, h-1, 59048) in mem and (a, h-1, 59047) in mem:
                # Page boundary: approximate
                mem[addr] = crazy(mem[(a, h-1, 59048)], mem[(a, h-1, 59047)])
            else:
                mem[addr] = (0, 0, 0)
        return mem[addr]

    def set_mem(addr, w):
        mem[addr] = w

    # Fill positions n_loaded to 59047 in area 0 high 0
    for p in range(n_loaded, 59049):
        a1 = (0, 0, p-1)
        a2 = (0, 0, p-2)
        if a1 in mem and a2 in mem:
            mem[(0, 0, p)] = crazy(mem[a1], mem[a2])
        else:
            break

    c = zero()
    d = zero()
    a = zero()
    inp_pos = 0
    output = bytearray()
    op_names = {4:'JMP',5:'PRINT',23:'INPUT',39:'ROTR',40:'MOVD',62:'CRZ',68:'NOP',81:'HALT'}

    for step in range(max_steps):
        mc = get_mem(c)
        # Decode: (mc.low + c.low + 59049*c.high + area_offset) % 94
        area_offset = 52 if c[0] == 1 else (10 if c[0] == 2 else 0)
        opcode = (mc[2] + c[2] + 59049 * c[1] + area_offset) % 94

        if trace:
            md = get_mem(d) if d in mem else 'lazy'
            print(f"  [{step:6d}] C={c} D={d} A={a} mc={mc} op={opcode}({op_names.get(opcode,'?')})", file=sys.stderr)

        if opcode == 4:    # JMP: C = mem[D]
            c = get_mem(d)
        elif opcode == 5:  # PRINT
            if a[0] == 0:
                ch = (a[2] + 59049 * a[1]) & 0xFF
                output.append(ch)
                if trace: print(f"    >> PRINT {ch} '{chr(ch) if 32<=ch<127 else '?'}'", file=sys.stderr)
            else:
                output.append(ord('\n'))
                if trace: print(f"    >> PRINT \\n (area={a[0]})", file=sys.stderr)
        elif opcode == 23: # INPUT
            if inp_pos < len(input_bytes):
                ch = input_bytes[inp_pos]
                inp_pos += 1
                if ch == ord('\n'):
                    a = (2, 59048, 59047)
                else:
                    a = (0, 0, ch)
            else:
                a = (2, 59048, 59048)  # EOF
        elif opcode == 39: # ROTR
            v = rotate_r(get_mem(d)); set_mem(d, v); a = v
        elif opcode == 40: # MOVD
            d = get_mem(d)
        elif opcode == 62: # CRZ
            v = crazy(a, get_mem(d)); set_mem(d, v); a = v
        elif opcode == 68: # NOP
            pass
        elif opcode == 81: # HALT
            break
        # else: NOP

        # XLAT modifies mem[c].low using mem[c].low - 33 as index
        mc_now = get_mem(c)
        if 33 <= mc_now[2] <= 126:
            xlat_v = ord(XLAT_TABLE[mc_now[2] - 33])
            set_mem(c, (mc_now[0], mc_now[1], xlat_v))
        # else: out-of-bounds XLAT (UB in fast20); we just skip

        c = increment(c)
        d = increment(d)

    return bytes(output)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: word_sim.py <prog.mb> [input_string]", file=sys.stderr)
        sys.exit(1)
    with open(sys.argv[1], "rb") as f:
        prog = f.read()
    inp = sys.argv[2].encode() if len(sys.argv) > 2 else b""
    trace = "--trace" in sys.argv
    out = simulate(prog, inp, trace=trace)
    sys.stdout.buffer.write(out)
