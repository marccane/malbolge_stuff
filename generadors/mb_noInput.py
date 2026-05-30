#!/usr/bin/env python3
"""
Build a Malbolge Unshackled program that prints 'Claude is the best!\n'
with NO INPUT — all character values loaded via CRZ sequences.

Key insight: in a straight-line program D=C, so CRZ at position P uses
mem[P] = encode_char(62, P) as its data operand. We search for pairs
(D1, D2) in [33,126] such that mcrz(mcrz(A_prev, D1), D2) = A_target.
"""
import sys
sys.path.insert(0, '/tmp')
from mb_sim import simulate, encode_char, mcrz, XLAT

TARGET = "Claude is the best!\n"

def find_crz_pair(a_prev, a_target):
    """Find D1,D2 in [33,126] with mcrz(mcrz(a_prev,D1),D2)==a_target."""
    for d1 in range(33, 127):
        a1 = mcrz(a_prev, d1)
        for d2 in range(33, 127):
            if mcrz(a1, d2) == a_target:
                return (d1, d2)
    return None

def find_crz_quad(a_prev, a_target):
    """Try 4 CRZs: find D1,D2 then D3,D4."""
    for d1 in range(33, 127):
        a1 = mcrz(a_prev, d1)
        for d2 in range(33, 127):
            a2 = mcrz(a1, d2)
            result = find_crz_pair(a2, a_target)
            if result:
                return (d1, d2) + result
    return None

def find_pos_for_data(data_val, min_pos):
    """Find smallest pos >= min_pos where encode_char(62, pos) == data_val."""
    base = (62 - data_val % 94 + 9400) % 94
    # base is in [0,93]; encode_char(62, base) should equal data_val
    # Verify and find the right offset
    p = base
    while p < min_pos:
        p += 94
    # Verify
    assert encode_char(62, p) == data_val, f"pos={p} data={encode_char(62,p)} != {data_val}"
    return p

print("Searching for CRZ sequences for each character...")
sequences = []  # list of (data_values_list, target_char)

a_current = 0
for ch in TARGET:
    v = ord(ch)
    pair = find_crz_pair(a_current, v)
    if pair:
        sequences.append((pair, v))
        print(f"  '{ch}'({v}): 2-CRZ [{pair[0]},{pair[1]}]")
    else:
        quad = find_crz_quad(a_current, v)
        if quad:
            sequences.append((quad, v))
            print(f"  '{ch}'({v}): 4-CRZ {list(quad)}")
        else:
            print(f"  '{ch}'({v}): FAILED to find sequence!")
            sys.exit(1)
    a_current = v

print()
print("Building program...")

# Build the program bytewise
prog = []
pos = 0  # current program position

for data_vals, target_char in sequences:
    # Place CRZs at the right positions, NOPs in between
    crz_positions = []
    min_p = pos
    for d in data_vals:
        p = find_pos_for_data(d, min_p + 1 if crz_positions else min_p)
        crz_positions.append(p)
        min_p = p + 1

    # Fill from pos to last CRZ + PRINT
    last_crz = crz_positions[-1]
    print_pos = last_crz + 1

    for p in range(pos, print_pos + 1):
        if p in crz_positions:
            prog.append(encode_char(62, p))  # CRZ
        elif p == print_pos:
            prog.append(encode_char(5, p))   # PRINT
        else:
            prog.append(encode_char(68, p))  # NOP

    pos = print_pos + 1

# HALT
prog.append(encode_char(81, pos))

prog_bytes = bytes(prog)
print(f"Program size: {len(prog_bytes)} bytes")

# Verify with simulator
out = simulate(prog_bytes, b"", max_steps=5_000_000)
if out == TARGET.encode():
    print(f"Simulator: PASS — output = {repr(out.decode())}")
else:
    print(f"Simulator: FAIL — got {repr(out)}")
    sys.exit(1)

with open('/tmp/claude_noInput.mb', 'wb') as f:
    f.write(prog_bytes)
print("Written to /tmp/claude_noInput.mb")
