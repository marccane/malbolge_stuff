#!/usr/bin/env python3
"""Find xlat cycles and search for loop-enabling instruction patterns."""

XLAT_STR = (
    "SOMEBODY MAKE ME FEEL ALIVE"
    "[hj9>,5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"
    "AND SHATTER ME"
)
XLAT = [ord(c) for c in XLAT_STR]

def xlat_apply(c, n=1):
    for _ in range(n): c = XLAT[c]
    return c

def xlat_cycle(start):
    seen = [start]
    c = XLAT[start]
    while c != start:
        seen.append(c)
        c = XLAT[c]
    return seen

def opcode(char_val, pos):
    return (pos + char_val) % 94

def encode_char(op, pos):
    t = (op - pos % 94 + 9400) % 94
    if t < 33: t += 94
    return t

# Compute all cycles
visited = set()
all_cycles = []
for start in range(33, 127):
    if start not in visited:
        cycle = xlat_cycle(start)
        all_cycles.append(cycle)
        visited.update(cycle)

print(f"Found {len(all_cycles)} xlat cycles for chars [33..126]")
print()

# For each position P, find chars that give a pattern of N JMPs then HALT
print("=== Searching for JMP^N then HALT patterns ===")
OPNAMES = {4:'JMP', 5:'PRINT', 23:'INPUT', 39:'ROTR', 40:'MOVD', 62:'CRZ', 68:'NOP', 81:'HALT'}

for pos in range(0, 50):
    jmp_char = encode_char(4, pos)  # char that gives JMP at this pos
    cycle = xlat_cycle(jmp_char)
    ops_in_cycle = [(opcode(c, pos), OPNAMES.get(opcode(c, pos), '?'), c, chr(c)) for c in cycle]
    # Check if cycle has JMP followed by HALT
    for i, (op, name, c, ch) in enumerate(ops_in_cycle):
        if op == 4:  # JMP
            # How many JMPs in a row?
            n_jmp = 0
            while n_jmp < len(ops_in_cycle) and ops_in_cycle[(i + n_jmp) % len(ops_in_cycle)][0] == 4:
                n_jmp += 1
            next_op = ops_in_cycle[(i + n_jmp) % len(ops_in_cycle)][0]
            if next_op == 81:  # HALT after JMPs
                print(f"  pos={pos} char='{ch}'({c}): {n_jmp} JMPs then HALT (cycle len={len(cycle)})")
                break

print()
# Find NOP^N then HALT patterns at various positions
print("=== Searching for positions where JMP cycles to HALT within 3 steps ===")
for pos in range(0, 100):
    jmp_char = encode_char(4, pos)
    ops = []
    c = jmp_char
    for _ in range(10):
        ops.append((opcode(c, pos), c))
        c = XLAT[c]
    # Check if first op is JMP and within 5 steps we see HALT
    if ops[0][0] == 4:
        for i in range(1, 6):
            if ops[i][0] == 81:
                print(f"  pos={pos}: JMP at step 0, HALT at step {i}. Chars: {[chr(o[1]) for o in ops[:i+1]]}")
