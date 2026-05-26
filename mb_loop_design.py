#!/usr/bin/env python3
"""
Design a Malbolge Unshackled loop that prints 'A' multiple times.
Key insight: at position 54, char ',' gives JMP twice then HALT.
Challenge: make JMP loop back to the right position.
"""
import sys
sys.path.insert(0, '/tmp')
from mb_sim import simulate, encode_char, mcrz, XLAT

END = 3**19

def char_opcode(ch, pos):
    return (pos + ch) % 94

# Strategy: find a position P and memory layout such that:
# - loop body prints 'A' (65) with PRINT instruction
# - JMP at position P loops back to start of body
# - Loop terminates naturally via xlat cycle

# Key observation: JMP at position P with char C jumps to mem[D]+1
# In a straight-line execution, D = P when instruction at P executes.
# So JMP target = mem[P] + 1.
# After JMP, mem[P] is xlat'd: mem[P] = XLAT[C].
# On next visit to P, JMP target = mem[P] + 1 = XLAT[C] + 1.

# For a loop: we want JMP target to be the SAME position each time.
# This means XLAT[C] = C (fixed point of XLAT) -- but there may be none.
# OR: target changes but lands in a valid loop body region.

# Let's find XLAT fixed points (XLAT[c] = c):
print("XLAT fixed points:")
for c in range(33, 127):
    if XLAT[c] == c:
        print(f"  c={c} ('{chr(c)}'): opcode at pos P = (P+{c})%94")

print()

# Alternative: find a 2-element xlat cycle (XLAT[a]=b, XLAT[b]=a)
print("XLAT 2-cycles:")
for c in range(33, 127):
    if XLAT[XLAT[c]] == c and XLAT[c] != c:
        print(f"  {c}('{chr(c)}') <-> {XLAT[c]}('{chr(XLAT[c])}')")

print()

# For a loop that executes N times with JMP at the END position:
# We need: D=P when JMP executes, and mem[P] = some_value
# such that mem[P]+1 = loop_start_position.
# After xlat, mem[P] = XLAT[JMP_char_at_P].
# Next visit: mem[P] = XLAT[JMP_char_at_P]+1 (jump again).
# For this to point to the same loop_start: XLAT[JMP_char_at_P] must equal JMP_char_at_P-1
# Or loop start can differ each time.

# A different approach: use xlat cycle at JMP position to control loop count.
# At pos=54, ',' (44): JMP -> JMP -> HALT (3 visits total)
# Jump target each visit:
#   Visit 1: mem[54]=44(',') -> jump to 45 (= 44+1)
#   Visit 2: mem[54]=XLAT[44]='(' (40) -> jump to 41 (= 40+1)
#   Visit 3: mem[54]=XLAT[40]='y' (121) -> HALT (opcode at 54: (54+121)%94=81=HALT!)

print("JMP at pos=54 with char ',' (44):")
c = 44
for i in range(4):
    op = char_opcode(c, 54)
    target = c + 1  # JMP target = mem[D]+1, D=54 initially
    opname = {4:'JMP', 81:'HALT', 40:'MOVD', 68:'NOP'}.get(op, f'OP{op}')
    print(f"  Visit {i+1}: char={c}('{chr(c)}') op={opname} -> target position {target}")
    c = XLAT[c]

print()
# So visits 1,2,3:
# V1: JMP -> 45 (D=54, after xlat C=45)
# V2: JMP -> 41 (D=54, after xlat C=41)
# V3: HALT

# Wait - but this is only if D=54 when JMP executes!
# The key is: what does D equal when position 54 is reached?

# In a straight-line program, D=C at all times (both start at 0).
# If we design the loop so D=54 when JMP at 54 executes, mem[D]=mem[54]=JMP char.

# First visit to pos 54: D=54, mem[54]=44, JMP goes to 45 (not back to loop start!)
# The loop body would need to END before position 41-44 for this to make sense.

# Let's design: loop body at positions 41-43 (3 positions).
# Visit 1: JMP from 54 -> 45 (outside loop body!)
# This doesn't work.

# New approach: have the loop body BEFORE position 44.
# Loop body: positions 0-40.
# JMP at position 54 on visit 2 -> 41. So loop reruns from 41 to 54.
# Sub-loop: positions 41-54.

print("=== Designing a loop with body at positions 41-53, JMP at 54 ===")
print("Visit 1 (D=54): JMP -> pos 45. After JMP, C=45, D=55.")
print("Visit 2 (D=?): depends on D when we next reach 54")
print()
print("Problem: after JMP to 45, D=55 (not 54). D increments to reach 54 again.")
print("At pos 54 second time: D = 55 + (54-45) = 55+9 = 64.")
print(f"mem[64]: in mcrz fill (beyond program). Value = mcrz(mem[63], mem[62])")
print()
print("This is very hard to control. Different approach needed.")
print()
print("=== Approach: use the INPUT/PRINT straight-line as a 'function body' ===")
print("Demonstrate 'functions' by creating a program that:")
print("1. Reads a string, transforms it, prints it")
print("2. Shows CRZ-based character transformation")
print()

# Let's design a program that reads chars and applies CRZ(A, A) to each
# CRZ(A,A) = ? For each trit t: CRZ(t,t) = {0:1, 1:0, 2:1}
# This is like a bitwise complement of the "1-trit" positions
# Let's see what CRZ(C, C) gives for 'C' = 67

def mcrz_py(a, d):
    crz = [[1,1,2],[0,0,2],[0,2,1]]
    r, k = 0, 1
    for _ in range(19):
        r += k * crz[a%3][d%3]
        a //= 3; d //= 3; k *= 3
    return r

c_code = 67
result = mcrz_py(c_code, c_code)
print(f"CRZ('C'=67, 'C'=67) = {result} = '{chr(result & 0xFF) if 32 <= (result&0xFF) < 127 else '?'}' (low byte)")
print()

# Actually, let's think about an achievable "function" demo:
# Write a program: INPUT, CRZ(A, [constant via *D]), PRINT
# Where [constant] is stored at a data position

# At position 0: INPUT -> A = input char
# At position 1: CRZ -> A = mcrz(A, mem[1]) where mem[1] = CRZ char at pos 1
# At position 2: PRINT -> outputs A & 0xFF

# CRZ char at pos 1: encode_char(62, 1)
crz_char_1 = encode_char(62, 1)
print(f"CRZ char at pos 1: {crz_char_1} = '{chr(crz_char_1)}'")
print(f"For 'C'(67): CRZ(67, {crz_char_1}) = {mcrz_py(67, crz_char_1)} = '{chr(mcrz_py(67,crz_char_1)&0xFF) if 32<=(mcrz_py(67,crz_char_1)&0xFF)<127 else '?'}'")
print()

# Let's make a transformation demo: INPUT -> [2 CRZs] -> PRINT
# and show what transformation it produces on 'Claude is the best!'
target = "Claude is the best!\n"
print("=== Testing transformations on 'Claude is the best!' ===")
# Program: INPUT CRZ PRINT (3 instructions, 3 chars)
prog = bytes([encode_char(23, 0), encode_char(62, 1), encode_char(5, 2), encode_char(81, 3)])
out = simulate(prog, target.encode())
print(f"INPUT CRZ PRINT: {out}")
print(f"  Raw bytes: {list(out)}")
