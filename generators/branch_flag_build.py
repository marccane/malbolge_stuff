#!/usr/bin/env python3
"""Spec-compliant flag-idiom branching program for Malbolge Unshackled.

Earlier versions of this build script were valid only for fast20-flavored
interpreters: data cells held bytes that did not decode to one of the eight
valid opcodes at their positions, which the strict loaders in Lutter's C
interpreter and the Haskell reference (tio_unshackled / Unshackled.hs) reject
at load time.

This redesign keeps every program byte spec-compliant by putting all data
cells inside the JMP#1-skipped region [2, 97] (so they never get XLAT'd) and
by picking flag-cell values fb1 so they decode to a valid opcode at pos 34.

Layout (steps in linear flow):
  step  c=pos  instruction
  ----  -----  -----------
   0      0    INPUT
   1      1    JMP#1            (jumps to 98)
   2-5  98-101 4 × NOP
   6     102   MOVD#1           reads mem[d=6]  = 33  → d := 34
   7     103   CRZ#1            mem[34] := crazy(a, fb1) = (1, 29524, V1)
   8     104   MOVD#2           reads mem[d=35] = 33  → d := 34
   9     105   CRZ#2            mem[34] := crazy(a, (1,29524,V1)) = (0,0,V_final)
   10    106   MOVD#3           reads mem[d=35] = 33  → d := 34
   11    107   JMP#2            c := mem[34] = (0,0,V_final); lands at V_final+1
   12    V+1   PRINT            outputs a.low = V_final
   13    V+2   HALT

Data cells (all in [2, 97], never visited by c, hence never XLAT'd):
  mem[6]  = 33   (33+6)%94 = 39 (ROTR — valid opcode encoding, never executed)
  mem[34] = fb1  picked so (fb1+34)%94 ∈ {valid opcodes}
  mem[35] = 33   (33+35)%94 = 68 (NOP encoding, never executed)

Branch cells (placed inside [2, 97], populated post-JMP#2):
  mem[V_X+1] PRINT, mem[V_X+2] HALT  (input X branch)
  mem[V_Y+1] PRINT, mem[V_Y+2] HALT  (input Y branch)

V_final ∈ {36,37,39,40,81,82,84,85,90,91,93,94} (10-trit values whose trits
are all in {0,1}), so V_final+1 lands inside the skipped branch region.
"""

import sys, subprocess

# Make the simulator importable
sys.path.insert(0, '/home/markus/projects/malbolge_stuff/generators')
from word_sim import simulate, encode_char


VALID_OPCODES = {4, 5, 23, 39, 40, 62, 68, 81}
VALID_V = {36, 37, 39, 40, 81, 82, 84, 85, 90, 91, 93, 94}


def crazy_low(a, d, n=10):
    crz = [[1, 1, 2], [0, 0, 2], [0, 2, 1]]
    r, k = 0, 1
    for _ in range(n):
        r += k * crz[a % 3][d % 3]
        a //= 3
        d //= 3
        k *= 3
    return r


def is_valid_byte_at(byte, pos):
    return 33 <= byte <= 126 and (byte + pos) % 94 in VALID_OPCODES


def valid_fb1_at(pos):
    return sorted({b for b in range(33, 127) if is_valid_byte_at(b, pos)})


def v_finals(fb1, ix, iy):
    V1x = crazy_low(ix, fb1)
    V1y = crazy_low(iy, fb1)
    return crazy_low(V1x, V1x), crazy_low(V1y, V1y)


FLAG_ADDR = 34
PREFERRED_PAIRS = [
    ('0', '1'), ('1', '0'),
    ('a', 'b'), ('b', 'a'),
    ('A', 'B'), ('B', 'A'),
    ('y', 'n'), ('Y', 'N'),
    ('+', '-'),
    ('1', '2'), ('2', '1'),
]


def find_solution():
    """Find (fb1, ix, iy, V_X, V_Y, ix_ch, iy_ch). fb1 must be valid at FLAG_ADDR."""
    fb1_candidates = valid_fb1_at(FLAG_ADDR)
    for fb1 in fb1_candidates:
        for ix_ch, iy_ch in PREFERRED_PAIRS:
            ix, iy = ord(ix_ch), ord(iy_ch)
            V_X, V_Y = v_finals(fb1, ix, iy)
            if V_X in VALID_V and V_Y in VALID_V and V_X != V_Y \
                    and abs(V_X - V_Y) >= 2:
                return fb1, ix, iy, V_X, V_Y, ix_ch, iy_ch
    # Fallback: any printable input pair
    for fb1 in fb1_candidates:
        for ix in range(33, 127):
            for iy in range(33, 127):
                if ix == iy:
                    continue
                V_X, V_Y = v_finals(fb1, ix, iy)
                if V_X in VALID_V and V_Y in VALID_V and V_X != V_Y \
                        and abs(V_X - V_Y) >= 2:
                    return fb1, ix, iy, V_X, V_Y, chr(ix), chr(iy)
    return None


def build_program(fb1, V_X, V_Y):
    N = 108
    prog = [encode_char(68, p) for p in range(N)]  # NOPs by default

    # Linear flow instructions
    prog[0]   = encode_char(23, 0)     # INPUT
    prog[1]   = encode_char(4, 1)      # JMP#1 → 98
    prog[102] = encode_char(40, 102)   # MOVD#1
    prog[103] = encode_char(62, 103)   # CRZ#1
    prog[104] = encode_char(40, 104)   # MOVD#2
    prog[105] = encode_char(62, 105)   # CRZ#2
    prog[106] = encode_char(40, 106)   # MOVD#3
    prog[107] = encode_char(4, 107)    # JMP#2

    # Data cells inside the JMP-skipped region [2, 97]
    prog[6]  = 33    # MOVD#1 reads here → d := 33, then +1 → 34
    prog[34] = fb1   # CRZ#1/#2 flag cell
    prog[35] = 33    # MOVD#2 and MOVD#3 read here

    # Branch cells (post-JMP#2 lands at V_final+1)
    for V in (V_X, V_Y):
        prog[V + 1] = encode_char(5, V + 1)    # PRINT
        prog[V + 2] = encode_char(81, V + 2)   # HALT

    # Validate every byte against the spec loader check
    for p, b in enumerate(prog):
        if not is_valid_byte_at(b, p):
            raise AssertionError(
                f"pos {p}: byte {b} decodes to opcode "
                f"{(b + p) % 94} (not a valid Malbolge Unshackled opcode)")
    return bytes(prog)


if __name__ == "__main__":
    sol = find_solution()
    if sol is None:
        print("No solution found")
        sys.exit(1)
    fb1, ix, iy, V_X, V_Y, ix_ch, iy_ch = sol
    print(f"Solution: fb1={fb1} ('{chr(fb1)}')")
    print(f"  input '{ix_ch}' ({ix}) → V_final={V_X} → PRINT '{chr(V_X)}' at pos {V_X+1}")
    print(f"  input '{iy_ch}' ({iy}) → V_final={V_Y} → PRINT '{chr(V_Y)}' at pos {V_Y+1}")

    prog = build_program(fb1, V_X, V_Y)
    out_path = '/home/markus/projects/malbolge_stuff/dotmu/branch_flag.mu'
    with open(out_path, 'wb') as f:
        f.write(prog)
    print(f"\nWrote {len(prog)} bytes to {out_path}")

    print("\nSimulation (word_sim):")
    for inp_ch, exp_ch in [(ix_ch, chr(V_X)), (iy_ch, chr(V_Y))]:
        out = simulate(prog, inp_ch.encode(), max_steps=2000)
        ok = '✓' if out == exp_ch.encode() else '✗'
        print(f"  '{inp_ch}' → {out!r}  (expected '{exp_ch}')  {ok}")

    bins = [
        ("fast20_malbolgelisp",
         "/home/markus/projects/malbolge_stuff/interpreters/fast20/fast20_malbolgelisp"),
        ("tio_unshackled",
         "/home/markus/projects/malbolge_stuff/interpreters/tio_unshackled/unshackled"),
        ("reference Haskell",
         "/home/markus/projects/malbolge_stuff/interpreters/referenceImplementation/Unshackled"),
    ]
    for name, binp in bins:
        print(f"\n{name}:")
        for inp_ch, exp_ch in [(ix_ch, chr(V_X)), (iy_ch, chr(V_Y))]:
            try:
                res = subprocess.run([binp, out_path], input=inp_ch.encode(),
                                     capture_output=True, timeout=15)
                ok = '✓' if res.stdout == exp_ch.encode() else '✗'
                print(f"  '{inp_ch}' → {res.stdout!r}  exit={res.returncode}  {ok}")
            except subprocess.TimeoutExpired:
                print(f"  '{inp_ch}' → TIMEOUT")
