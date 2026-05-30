#!/usr/bin/env python3
"""
Build a Malbolge Unshackled printer for 'Claude is the best!\n' with no stdin data.
Strategy: INPUT (reads EOF -> A=END-1=all-2s) then 3 CRZs then PRINT per character.
Run with: fast20 claude_noInput.mu < /dev/null
"""
import sys
sys.path.insert(0, '/tmp')
from mb_sim import simulate, encode_char, mcrz, END

TARGET = "Claude is the best!\n"
A_EOF = END - 1  # value INPUT returns when stdin is empty

def find_3crz(a_start, target_char):
    """Find smallest (D1,D2,D3) in [33,126] such that mcrz(mcrz(mcrz(a_start,D1),D2),D3)%256==target_char."""
    t = target_char % 256
    for d1 in range(33, 127):
        a1 = mcrz(a_start, d1)
        for d2 in range(33, 127):
            a2 = mcrz(a1, d2)
            for d3 in range(33, 127):
                a3 = mcrz(a2, d3)
                if a3 % 256 == t:
                    return (d1, d2, d3), a3
    return None, None

def find_pos_for_data(data_val, min_pos):
    """Smallest pos >= min_pos where encode_char(62, pos) == data_val."""
    base = (62 - data_val % 94 + 9400) % 94
    p = base
    while p < min_pos:
        p += 94
    assert encode_char(62, p) == data_val, f"p={p} enc={encode_char(62,p)} want={data_val}"
    return p

def find_pos_for_input(min_pos):
    """Smallest pos >= min_pos where encode_char(23, pos) decodes to INPUT."""
    base = (23 - 0 + 9400) % 94  # pos%94 = (23-23+9400)%94... actually:
    # encode_char(23, pos) gives byte B such that (B + pos) % 94 = 23
    # We just need any pos where this holds, and encode_char(23, pos) is in [33,126].
    # By construction of encode_char, any pos works.
    return min_pos  # INPUT can go at any position

print("Finding INPUT+3CRZ sequences for each character...")
sequences = []
for ch in TARGET:
    v = ord(ch)
    triple, a_new = find_3crz(A_EOF, v)
    if triple is None:
        print(f"  '{ch}'({v}): FAILED")
        sys.exit(1)
    sequences.append((ch, v, triple, a_new))
    print(f"  '{ch}'({v}): INPUT->CRZ{triple}->A={a_new}(A%256={a_new%256})")

print()
print("Building program...")

prog = []
pos = 0

for ch, v, (d1, d2, d3), a_new in sequences:
    # INPUT at current pos
    inp_byte = encode_char(23, pos)
    prog.append(inp_byte)
    pos += 1

    # CRZ(d1): find pos where encode_char(62, pos) == d1
    p1 = find_pos_for_data(d1, pos)
    while pos < p1:
        prog.append(encode_char(68, pos))  # NOP
        pos += 1
    prog.append(encode_char(62, pos))  # CRZ with data=d1
    pos += 1

    # CRZ(d2): find pos where encode_char(62, pos) == d2
    p2 = find_pos_for_data(d2, pos)
    while pos < p2:
        prog.append(encode_char(68, pos))  # NOP
        pos += 1
    prog.append(encode_char(62, pos))  # CRZ with data=d2
    pos += 1

    # CRZ(d3): find pos where encode_char(62, pos) == d3
    p3 = find_pos_for_data(d3, pos)
    while pos < p3:
        prog.append(encode_char(68, pos))  # NOP
        pos += 1
    prog.append(encode_char(62, pos))  # CRZ with data=d3
    pos += 1

    # PRINT
    prog.append(encode_char(5, pos))
    pos += 1

# HALT
prog.append(encode_char(81, pos))

prog_bytes = bytes(prog)
print(f"Program size: {len(prog_bytes)} bytes")

# Verify with simulator (provide empty input)
out = simulate(prog_bytes, b"", max_steps=50_000_000)
if out == TARGET.encode():
    print(f"Simulator: PASS — '{out.decode()}'")
else:
    print(f"Simulator: FAIL — got {repr(out[:60])}")
    for i, (a, b) in enumerate(zip(out, TARGET.encode())):
        if a != b:
            print(f"  First diff at pos {i}: got {a!r} ({chr(a)!r}) expected {b!r} ({chr(b)!r})")
            break

with open('/tmp/claude_noInput.mu', 'wb') as f:
    f.write(prog_bytes)
print("Written /tmp/claude_noInput.mu")
print("Run with: /tmp/fast20 /tmp/claude_noInput.mu < /dev/null")
