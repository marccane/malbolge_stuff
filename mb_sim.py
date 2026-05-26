#!/usr/bin/env python3
"""Malbolge Unshackled simulator matching fast20.c exactly (19-trit fixed rotation)."""
import sys

END = 3**19  # 1162261467

def mrot(x):
    t = END // 3
    b = x % t
    m = b % 3
    d = b // 3
    return d + m * (t // 3) + (x - b)

def mcrz(a, d):
    crz = [[1,1,2],[0,0,2],[0,2,1]]
    r = 0
    k = 1
    for _ in range(19):
        r += k * crz[a % 3][d % 3]
        a //= 3
        d //= 3
        k *= 3
    return r

# From fast20.c NXT macro (C string literal escapes resolved)
XLAT_STR = (
    "SOMEBODY MAKE ME FEEL ALIVE"
    "[hj9>,5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"
    "AND SHATTER ME"
)
XLAT = [ord(c) for c in XLAT_STR]

def simulate(prog_bytes, input_bytes=b"", max_steps=2_000_000, trace=False):
    mem = list(prog_bytes)

    def grow(n):
        while len(mem) <= n:
            i = len(mem)
            mem.append(mcrz(mem[i-1], mem[i-2]) if i >= 2 else 0)

    def gm(addr): grow(addr); return mem[addr]
    def sm(addr, v): grow(addr); mem[addr] = v

    c = 0; d = 0; a = 0
    inp_pos = 0
    output = bytearray()

    for step in range(max_steps):
        mc = gm(c)
        opcode = (c + mc) % 94

        if trace:
            names = {4:'JMP',5:'PRINT',23:'INPUT',39:'ROTR',40:'MOVD',62:'CRZ',68:'NOP',81:'HALT'}
            print(f"  [{step:6d}] C={c} D={d} A={a} mc={mc}('{chr(mc) if 32<mc<127 else '?'}') op={opcode}({names.get(opcode,'?')})", file=sys.stderr)

        if opcode == 4:    # JMP: C = mem[D]
            c = gm(d)
        elif opcode == 5:  # PRINT: putchar(a)
            ch = a & 0xFF
            output.append(ch)
            if trace: print(f"    >> PRINT {ch} '{chr(ch) if 32<=ch<127 else '?'}'", file=sys.stderr)
        elif opcode == 23: # INPUT: a = getchar()
            a = input_bytes[inp_pos] if inp_pos < len(input_bytes) else END - 1
            inp_pos += 1
        elif opcode == 39: # ROTR: a = *d = mrot(*d)
            v = mrot(gm(d)); sm(d, v); a = v
        elif opcode == 40: # MOVD: d = mem[d]
            d = gm(d)
        elif opcode == 62: # CRZ: a = *d = mcrz(a, *d)
            v = mcrz(a, gm(d)); sm(d, v); a = v
        elif opcode == 68: # NOP
            pass
        elif opcode == 81: # HALT
            break
        # else: NOP

        sm(c, XLAT[mc] if mc < len(XLAT) else mc)  # xlat self-modify
        c += 1
        d += 1

    return bytes(output)

def encode_char(opcode, pos):
    """Encode opcode at position pos -> character byte."""
    t = (opcode - pos % 94 + 94 * 100) % 94
    if t < 33:
        t += 94
    return t

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: mb_sim.py <prog.mb> [input_string]", file=sys.stderr)
        sys.exit(1)
    with open(sys.argv[1], "rb") as f:
        prog = f.read()
    inp = sys.argv[2].encode() if len(sys.argv) > 2 else b""
    trace = "--trace" in sys.argv
    out = simulate(prog, inp, trace=trace)
    sys.stdout.buffer.write(out)
