#!/usr/bin/env python3
"""
Build a no-input Malbolge Unshackled printer.
Key insight: putchar(a) outputs a & 0xFF, so only low byte matters.
So mcrz(mcrz(A, D1), D2) % 256 == target is sufficient.
"""
import sys
sys.path.insert(0, '/tmp')
from mb_sim import simulate, encode_char, mcrz

TARGET = "Claude is the best!\n"

def find_crz_pair_mod(a_prev, a_target):
    """Find D1,D2 in [33,126] with mcrz(mcrz(a_prev,D1),D2) % 256 == a_target."""
    t = a_target % 256
    for d1 in range(33, 127):
        a1 = mcrz(a_prev, d1)
        for d2 in range(33, 127):
            if mcrz(a1, d2) % 256 == t:
                return (d1, d2), mcrz(a1, d2)
    return None, None

def find_crz_triple_mod(a_prev, a_target):
    """Find D1,D2,D3 with result % 256 == a_target. Uses 2-CRZ for each half."""
    t = a_target % 256
    for d1 in range(33, 127):
        a1 = mcrz(a_prev, d1)
        for d2 in range(33, 127):
            a2 = mcrz(a1, d2)
            for d3 in range(33, 127):
                if mcrz(a2, d3) % 256 == t:
                    return (d1, d2, d3), mcrz(a2, d3)
    return None, None

print("Searching for CRZ sequences (using mod-256 comparison)...")
sequences = []

a_current = 0
all_found = True
for ch in TARGET:
    v = ord(ch)
    pair, a_new = find_crz_pair_mod(a_current, v)
    if pair:
        sequences.append((pair, v, a_new))
        print(f"  '{ch}'({v}): 2-CRZ {list(pair)} -> A={a_new} (A%256={a_new%256})")
        a_current = a_new
    else:
        triple, a_new = find_crz_triple_mod(a_current, v)
        if triple:
            sequences.append((triple, v, a_new))
            print(f"  '{ch}'({v}): 3-CRZ {list(triple)} -> A={a_new} (A%256={a_new%256})")
            a_current = a_new
        else:
            print(f"  '{ch}'({v}): FAILED")
            all_found = False

if not all_found:
    sys.exit(1)

print()

# Now build the program
def find_pos_for_data(data_val, min_pos):
    """Smallest pos >= min_pos where encode_char(62, pos) == data_val."""
    base = (62 - data_val + 9400) % 94
    p = base
    while p < min_pos:
        p += 94
    assert encode_char(62, p) == data_val
    return p

prog = []
pos = 0

for data_vals, target_char, _ in sequences:
    crz_positions = []
    min_p = pos
    for d in data_vals:
        p = find_pos_for_data(d, min_p + (1 if crz_positions else 0))
        crz_positions.append(p)
        min_p = p + 1

    print_pos = max(crz_positions) + 1

    for p in range(pos, print_pos + 1):
        if p in crz_positions:
            prog.append(encode_char(62, p))
        elif p == print_pos:
            prog.append(encode_char(5, p))
        else:
            prog.append(encode_char(68, p))  # NOP

    pos = print_pos + 1

prog.append(encode_char(81, pos))  # HALT
prog_bytes = bytes(prog)
print(f"Program size: {len(prog_bytes)} bytes")

out = simulate(prog_bytes, b"", max_steps=10_000_000)
if out == TARGET.encode():
    print(f"Simulator: PASS — '{out.decode().strip()}'")
else:
    print(f"Simulator: got {repr(out[:40])}")
    # Check byte by byte
    for i, (a, b) in enumerate(zip(out, TARGET.encode())):
        if a != b:
            print(f"  First diff at pos {i}: got {a} expected {b}")
            break

with open('/tmp/claude_noInput.mb', 'wb') as f:
    f.write(prog_bytes)
print("Written /tmp/claude_noInput.mb")
