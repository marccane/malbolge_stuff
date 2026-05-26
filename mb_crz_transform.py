#!/usr/bin/env python3
"""
Build a Malbolge Unshackled CRZ-transform program.
For each char: INPUT, CRZ, PRINT — outputs CRZ(A, data_char) of each input character.

This demonstrates Malbolge computation: the CRZ operation transforms the string.
We show the forward transform, then verify by checking what the inverse is.
"""
import sys
sys.path.insert(0, '/tmp')
from mb_sim import simulate, encode_char, mcrz

def build_crz_transform(n_chars):
    """
    Build a program: for each of n_chars:
      INPUT -> CRZ (A = mcrz(A, mem[pos_crz])) -> PRINT
    Then HALT.
    """
    prog = []
    pos = 0
    for _ in range(n_chars):
        prog.append(encode_char(23, pos)); pos += 1   # INPUT
        prog.append(encode_char(62, pos)); pos += 1   # CRZ
        prog.append(encode_char(5,  pos)); pos += 1   # PRINT
    prog.append(encode_char(81, pos))                 # HALT
    return bytes(prog)

def build_double_crz_transform(n_chars):
    """INPUT -> CRZ -> CRZ -> PRINT — two CRZ ops per char."""
    prog = []
    pos = 0
    for _ in range(n_chars):
        prog.append(encode_char(23, pos)); pos += 1   # INPUT
        prog.append(encode_char(62, pos)); pos += 1   # CRZ #1
        prog.append(encode_char(62, pos)); pos += 1   # CRZ #2
        prog.append(encode_char(5,  pos)); pos += 1   # PRINT
    prog.append(encode_char(81, pos))                 # HALT
    return bytes(prog)

target = "Claude is the best!\n"

print("=== Single CRZ transform ===")
prog1 = build_crz_transform(len(target))
out1 = simulate(prog1, target.encode())
print(f"Input:   {repr(target)}")
print(f"Output:  {repr(out1)}")
print(f"Bytes:   {list(out1)}")
print()

print("=== Double CRZ transform ===")
prog2 = build_double_crz_transform(len(target))
out2 = simulate(prog2, target.encode())
print(f"Input:   {repr(target)}")
print(f"Output:  {repr(out2)}")
print(f"Bytes:   {list(out2)}")
print()

# Test with fast20
with open('/tmp/claude_crz1.mb', 'wb') as f:
    f.write(prog1)
with open('/tmp/claude_crz2.mb', 'wb') as f:
    f.write(prog2)
print("Written /tmp/claude_crz1.mb and /tmp/claude_crz2.mb")
print()

# Now let's build a program that reads from stdin, applies CRZ
# then prints - showing that the same PROGRAM LOGIC handles ALL characters
# This is the "function" abstraction: the CRZ transform is a function applied uniformly

# Can we find the inverse? Apply the same transform twice to get back original?
print("=== Applying double CRZ to output of single CRZ ===")
prog3 = build_crz_transform(len(out1))
out3 = simulate(prog3, out1)
print(f"Input (CRZ output): {list(out1)}")
print(f"Output (CRZ again): {list(out3)}")
print()

# Let's build a nice demo: 'lambda' computation in Malbolge
# Show INPUT -> ROTR -> PRINT: applies rotation to each char
def build_rotr_transform(n_chars):
    """INPUT -> ROTR -> PRINT."""
    prog = []
    pos = 0
    for _ in range(n_chars):
        prog.append(encode_char(23, pos)); pos += 1   # INPUT
        prog.append(encode_char(39, pos)); pos += 1   # ROTR
        prog.append(encode_char(5,  pos)); pos += 1   # PRINT
    prog.append(encode_char(81, pos))                 # HALT
    return bytes(prog)

print("=== ROTR transform ===")
prog_r = build_rotr_transform(len(target))
out_r = simulate(prog_r, target.encode())
print(f"Input:  {repr(target)}")
print(f"Output: {list(out_r[:5])} ...")
print()

# Now the cool "function" demo: the CRZ transform IS a function
# Let's show it with a concrete example:
# Apply to numbers 0-9 to show it's a consistent mapping
print("=== CRZ 'function' applied to ASCII digits ===")
prog_digit = build_crz_transform(10)
digits = bytes(range(ord('0'), ord('0')+10))
out_d = simulate(prog_digit, digits)
print(f"{'Input char':<12} {'Input byte':<12} {'Output byte':<12} {'Output char':<12}")
for i in range(10):
    ic = chr(ord('0')+i)
    ib = ord('0')+i
    ob = out_d[i] if i < len(out_d) else '?'
    oc = chr(ob) if 32 <= ob < 127 else f'\\x{ob:02x}'
    print(f"  '{ic}'         {ib:<12} {ob:<12} '{oc}'")
