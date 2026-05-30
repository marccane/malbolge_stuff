#!/usr/bin/env python3
"""
Build a no-input Malbolge Unshackled printer using CRZ + ROTR.
Uses BFS to find the minimum CRZ/ROTR sequence to reach each target char.
"""
import sys
sys.path.insert(0, '/tmp')
from mb_sim import simulate, encode_char, mcrz, mrot

TARGET = "Claude is the best!\n"

END = 3**19

def get_trits(A, n=19):
    trits = []
    for _ in range(n):
        trits.append(A % 3)
        A //= 3
    return trits

def state_of(A):
    """Compact state: (low5 trits, high14 trits as int)."""
    trits = get_trits(A)
    low5 = tuple(trits[:5])
    high14 = 0
    for t in reversed(trits[5:]):
        high14 = high14 * 3 + t
    return (low5, high14)

def bfs_to_target(A_start, target_mod256):
    """Find shortest sequence of (CRZ(D) for D in 33..126 / ROTR) to reach A%256==target."""
    from collections import deque

    target = target_mod256 % 256

    # BFS state: (A, path)
    # Use state_of(A) to detect duplicates
    seen = {state_of(A_start): (0, [])}
    queue = deque([(A_start, [])])

    if A_start % 256 == target:
        return [], A_start

    while queue:
        A, path = queue.popleft()
        depth = len(path)

        if depth >= 10:
            continue

        # Try ROTR
        nA = mrot(A)
        ns = state_of(nA)
        if ns not in seen:
            npath = path + [('R', None)]
            seen[ns] = (depth+1, npath)
            if nA % 256 == target:
                return npath, nA
            queue.append((nA, npath))

        # Try CRZ with each D in [33,126]
        for d in range(33, 127):
            nA = mcrz(A, d)
            ns = state_of(nA)
            if ns not in seen:
                npath = path + [('C', d)]
                seen[ns] = (depth+1, npath)
                if nA % 256 == target:
                    return npath, nA
                queue.append((nA, npath))

    return None, None

def find_pos_for_data(data_val, min_pos):
    """Smallest pos >= min_pos where encode_char(62, pos) == data_val."""
    base = (62 - data_val % 94 + 9400) % 94
    if encode_char(62, base) != data_val:
        # Try with offset
        base = (base + 94 - 33) % 94  # shouldn't happen if formula is right
    p = base
    while p < min_pos:
        p += 94
    assert encode_char(62, p) == data_val, f"pos={p} got={encode_char(62,p)} want={data_val}"
    return p

print("Finding CRZ+ROTR sequences for each character...")
sequences = []  # list of (ops, target_char_val, A_after)

a_current = 0
all_found = True
for ch in TARGET:
    v = ord(ch)
    ops, A_new = bfs_to_target(a_current, v)
    if ops is None:
        print(f"  '{ch}'({v}): FAILED from A={a_current}")
        all_found = False
        a_current = 0  # reset to keep going
    else:
        sequences.append((ops, v, A_new))
        print(f"  '{ch}'({v}): {len(ops)} ops {ops} -> A={A_new} (A%256={A_new%256})")
        a_current = A_new

if not all_found:
    sys.exit(1)

print()
print("Building program...")

prog = []
pos = 0

for ops, target_char, A_after in sequences:
    # Place the ops in order, then PRINT
    # ops is a list of ('R', None) for ROTR or ('C', D) for CRZ

    op_positions = []  # (pos, instruction_byte)

    for kind, d in ops:
        if kind == 'R':
            # ROTR at current pos
            op_positions.append((pos, encode_char(39, pos)))
            pos += 1
        elif kind == 'C':
            # CRZ: find pos where encode_char(62, pos) == d
            p = find_pos_for_data(d, pos)
            # Fill NOPs from pos to p-1
            while pos < p:
                op_positions.append((pos, encode_char(68, pos)))
                pos += 1
            op_positions.append((pos, encode_char(62, pos)))
            pos += 1

    # PRINT at current pos
    print_byte = encode_char(5, pos)
    op_positions.append((pos, print_byte))
    pos += 1

    prog.extend(b for _, b in op_positions)

# HALT
prog.append(encode_char(81, pos))

prog_bytes = bytes(prog)
print(f"Program size: {len(prog_bytes)} bytes")

# Verify with simulator
out = simulate(prog_bytes, b"", max_steps=20_000_000)
if out == TARGET.encode():
    print(f"Simulator: PASS — '{out.decode()}'")
else:
    print(f"Simulator: FAIL — got {repr(out[:60])}")
    for i, (a, b) in enumerate(zip(out, TARGET.encode())):
        if a != b:
            print(f"  First diff at pos {i}: got {a!r} ({chr(a)!r}) expected {b!r} ({chr(b)!r})")
            break

with open('/tmp/claude_noInput.mb', 'wb') as f:
    f.write(prog_bytes)
print("Written /tmp/claude_noInput.mb")
