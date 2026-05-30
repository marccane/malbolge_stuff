#!/usr/bin/env python3
"""Final flag-idiom branching program (v3, clean).

Layout (cells executed in linear flow first, then post-JMP):
  pos 0:    INPUT
  pos 1:    JMP#1 — skips branch region (always lands at 98)
  pos 2-97: branch region (only executed via JMP#2 below)
            - PRINT+HALT at V_final_X+1, V_final_X+2 (input X branch)
            - PRINT+HALT at V_final_Y+1, V_final_Y+2 (input Y branch)
            - All other positions: NOPs
  pos 98-100:  NOPs (filler, executed after JMP#1)
  pos 101:  MOVD#1 — redirects d to 34 (reads mem[5]=33 → d=33+1=34)
  pos 102:  CRZ#1  — writes mem[34] = crazy(input, fb1) = (1, 29524, V1)
  pos 103-194: NOPs (92 NOPs)
  pos 195:  MOVD#2 — redirects d to 34 (reads mem[127]=33 → d=34)
  pos 196:  CRZ#2  — writes mem[34] = crazy(A=(1,29524,V1), (1,29524,V1)) = (0, 0, V_final)
  pos 197-288: NOPs (92 NOPs)
  pos 289:  MOVD#3 — redirects d to 34 (reads mem[127]=33 → d=34)
  pos 290:  JMP#2  — reads mem[34]=(0,0,V_final); lands at V_final+1 (in branch region)

Critical data cells (overridden):
  mem[5]   = 33  (MOVD#1 redirect data)
  mem[34]  = fb1 (initial value for the input-dependent CRZ chain)
  mem[127] = 33  (MOVD#2 and MOVD#3 redirect data)

V_final values for our inputs must land at branch positions in [2, 97].
"""
import sys, subprocess
sys.path.insert(0, '/tmp/branch')
sys.path.insert(0, '/tmp')
from word_sim import simulate, encode_char


def crazy_low(a, d, n=10):
    crz = [[1,1,2],[0,0,2],[0,2,1]]
    r, k = 0, 1
    for _ in range(n):
        r += k * crz[a % 3][d % 3]
        a //= 3; d //= 3; k *= 3
    return r


def v_finals(fb1, ix, iy):
    V1_X = crazy_low(ix, fb1)
    V1_Y = crazy_low(iy, fb1)
    return crazy_low(V1_X, V1_X), crazy_low(V1_Y, V1_Y)


def find_solution():
    """Find (fb1, ix, iy) where V_final_X, V_final_Y are different, both V+1 in [2, 97]."""
    valid_v_set = {36, 37, 39, 40, 81, 82, 84, 85, 90, 91, 93, 94}
    # Prefer natural input pairs
    preferred_pairs = [
        ('0','1'), ('1','0'), ('a','b'), ('b','a'), ('A','B'), ('B','A'),
        ('y','n'), ('Y','N'), ('+','-'), ('1','2'), ('2','1'),
    ]
    for fb1 in range(33, 127):
        for ix_ch, iy_ch in preferred_pairs:
            ix, iy = ord(ix_ch), ord(iy_ch)
            V_X, V_Y = v_finals(fb1, ix, iy)
            if V_X in valid_v_set and V_Y in valid_v_set and V_X != V_Y:
                # Check branches don't overlap
                pa, pb = V_X + 1, V_Y + 1
                if abs(pa - pb) >= 2:
                    return fb1, ix, iy, V_X, V_Y, ix_ch, iy_ch
    # Fallback: any inputs
    for fb1 in range(33, 127):
        for ix in range(33, 127):
            for iy in range(33, 127):
                if ix == iy: continue
                V_X, V_Y = v_finals(fb1, ix, iy)
                if V_X in valid_v_set and V_Y in valid_v_set and V_X != V_Y:
                    pa, pb = V_X + 1, V_Y + 1
                    if abs(pa - pb) >= 2:
                        return fb1, ix, iy, V_X, V_Y, chr(ix), chr(iy)
    return None


def build_program(fb1, ix, iy, V_X, V_Y):
    """Build the program file."""
    pa = V_X + 1
    pb = V_Y + 1
    N = 300

    # All NOPs by default
    prog = [encode_char(68, p) for p in range(N)]

    # Cells executed in linear flow (must decode correctly)
    prog[0]   = encode_char(23, 0)    # INPUT
    prog[1]   = encode_char(4, 1)     # JMP#1 (always lands at 98)
    prog[101] = encode_char(40, 101)  # MOVD#1
    prog[102] = encode_char(62, 102)  # CRZ#1
    prog[195] = encode_char(40, 195)  # MOVD#2
    prog[196] = encode_char(62, 196)  # CRZ#2
    prog[289] = encode_char(40, 289)  # MOVD#3
    prog[290] = encode_char(4, 290)   # JMP#2

    # Branch cells (executed post-JMP#2)
    prog[pa]   = encode_char(5, pa)
    prog[pa+1] = encode_char(81, pa+1)
    prog[pb]   = encode_char(5, pb)
    prog[pb+1] = encode_char(81, pb+1)

    # Data cells (read by MOVD/CRZ)
    prog[5]   = 33     # MOVD#1 data → redirects d to 34 (not XLAT'd: c≠5 in linear flow)
    prog[34]  = fb1    # CRZ data; flag cell (not XLAT'd: c≠34 in linear flow)
    # mem[127] IS visited as c in linear flow (in NOP region 103-194), so XLAT
    # changes it. We need post-XLAT value = 33. XLAT['D'(68)] = '!'(33), so use 68.
    prog[127] = 68     # MOVD#2 and MOVD#3 data: XLATs to 33 → redirects d to 34

    # Sanity
    for i, b in enumerate(prog):
        assert 33 <= b <= 126, f"pos {i}: byte {b} out of range"

    return bytes(prog), pa, pb


if __name__ == "__main__":
    sol = find_solution()
    if sol is None:
        print("No solution")
        sys.exit(1)
    fb1, ix, iy, V_X, V_Y, ix_ch, iy_ch = sol
    print(f"Solution: fb1={fb1} ('{chr(fb1)}'), input '{ix_ch}' ({ix}) → V_final={V_X} → branch at pos {V_X+1} (PRINT '{chr(V_X)}')")
    print(f"          input '{iy_ch}' ({iy}) → V_final={V_Y} → branch at pos {V_Y+1} (PRINT '{chr(V_Y)}')")

    prog, pa, pb = build_program(fb1, ix, iy, V_X, V_Y)
    out_path = '/tmp/branch/branch_v3.mb'
    with open(out_path, 'wb') as f:
        f.write(prog)
    print(f"\nWrote {len(prog)} bytes to {out_path}")

    print("\nSimulation:")
    for inp_ch, exp_ch in [(ix_ch, chr(V_X)), (iy_ch, chr(V_Y))]:
        out = simulate(prog, inp_ch.encode(), max_steps=2000)
        status = '✓' if out == exp_ch.encode() else '✗'
        print(f"  sim: '{inp_ch}' → {out!r}  (expected '{exp_ch}')  {status}")

    print("\nfast20:")
    for inp_ch, exp_ch in [(ix_ch, chr(V_X)), (iy_ch, chr(V_Y))]:
        res = subprocess.run(['/tmp/fast20', out_path], input=inp_ch.encode(), capture_output=True, timeout=10)
        status = '✓' if res.stdout == exp_ch.encode() else '✗'
        print(f"  fast20: '{inp_ch}' → {res.stdout!r}  (expected '{exp_ch}')  {status} exit={res.returncode}")
