#!/usr/bin/env python3
"""Spec-compliant no-input "Claude is the best!\\n" printer.

The previous noInput generator does CRZ at c (since c==d in linear flow).
That overwrites mem[c] with a value whose low limb often falls outside
[33, 126], so spec-compliant interpreters refuse to apply xlat2.

This generator decouples c and d with a single MOVD early on. After it,
d permanently trails c by OFFSET. CRZ then writes to mem[d] = mem[c-OFFSET],
which is BEHIND c (c never revisits it). mem[c] stays as the original
instruction byte through XLAT — always in [33, 126]. Spec-compliant.

Layout:
  pos 0..126: NOPs (so MOVD at pos 127 reads a byte <= 126 → small d)
  pos 127:    MOVD. mem[127] = encode_char(40, 127) = 101. After MOVD:
              d = (0,0,101); then increment puts c=128, d=102. Offset 26.
  pos 128+:   per-char cycles: INPUT, NOPs, CRZ#1, NOPs, CRZ#2,
              NOPs, CRZ#3, PRINT. CRZ #i placed so mem[d=c-26] has
              the desired XLAT'd-NOP value.
  finally:    HALT.

The 3-CRZ chain transforms a=EOF (low=59048) into target_char (mod 256).
d values are drawn from XLAT[encode_char(68, p) - 33] which covers all
94 distinct XLAT table entries — wide enough to hit every target.
"""

import sys

XLAT_STR = ("5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72Fh"
            "OA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@")
assert len(XLAT_STR) == 94

OFFSET = 26  # d trails c by this much after the MOVD at pos 127
A_EOF_LOW = 59048  # all-2s in 10 trits


def xlat(b):
    return ord(XLAT_STR[b - 33])


def encode_char(opcode, pos):
    t = (opcode - pos % 94 + 9400) % 94
    if t < 33:
        t += 94
    return t


def crazy_low(a, d, n=10):
    crz = [[1, 1, 2], [0, 0, 2], [0, 2, 1]]
    r, k = 0, 1
    for _ in range(n):
        r += k * crz[a % 3][d % 3]
        a //= 3
        d //= 3
        k *= 3
    return r


def find_triple(target):
    """Pick (v1, v2, v3) from XLAT values so 3-CRZ chain mod 256 = target."""
    target %= 256
    xlat_vals = sorted({xlat(b) for b in range(33, 127)})
    for v1 in xlat_vals:
        a1 = crazy_low(A_EOF_LOW, v1)
        for v2 in xlat_vals:
            a2 = crazy_low(a1, v2)
            for v3 in xlat_vals:
                if crazy_low(a2, v3) % 256 == target:
                    return (v1, v2, v3)
    return None


# Inverse XLAT for finding which raw byte b satisfies xlat(b) == v
XLAT_INV = {xlat(b): b for b in range(33, 127)}


def positions_for_value(v, min_p, polluted):
    """Yield positions p >= min_p, p not in polluted, where XLAT'd NOP at p == v."""
    if v not in XLAT_INV:
        return
    b = XLAT_INV[v]
    t = b if b <= 93 else b - 94
    p_mod = (68 - t) % 94
    p = min_p + ((p_mod - min_p) % 94)
    while True:
        if p not in polluted:
            yield p
        p += 94


TARGET = "Claude is the best!\n"

print("=== Finding 3-CRZ triples ===")
triples = []
for ch in TARGET:
    t = find_triple(ord(ch))
    if t is None:
        print(f"  FAIL: '{ch}' ({ord(ch)})")
        sys.exit(1)
    triples.append(t)
    print(f"  '{ch}' ({ord(ch)}): v1={t[0]:3d} v2={t[1]:3d} v3={t[2]:3d}")

print()
print("=== Building program ===")
prog = []
pos = 0

# Phase 1: 127 NOPs so MOVD at pos 127 reads byte <= 126
while pos < 127:
    prog.append(encode_char(68, pos))
    pos += 1

# Phase 2: MOVD at pos 127 (sets d=101 → after increment c=128, d=102)
prog.append(encode_char(40, 127))
pos += 1
assert pos == 128

# Sanity check that the offset is what we expect
mb127 = encode_char(40, 127)
assert mb127 == 101, f"encode_char(40,127) = {mb127}"
# After MOVD c=127 sets d=(0,0,101), then both increment → c=128, d=102.
# offset c-d = 26 ✓

# polluted = positions whose mem value is NOT XLAT'd-NOP:
#   - MOVD at 127 (XLAT'd MOVD encoding, not NOP encoding)
#   - every INPUT/CRZ/PRINT instruction position visited in prior cycles
#   - every d-position previously written to by CRZ
polluted = {127}

# Phase 3: per-character cycles
for ch_idx, ch in enumerate(TARGET):
    v1, v2, v3 = triples[ch_idx]

    # INPUT
    polluted.add(pos)
    prog.append(encode_char(23, pos))
    pos += 1

    for v in (v1, v2, v3):
        gen = positions_for_value(v, max(0, pos - OFFSET), polluted)
        chosen = None
        for d_pos in gen:
            pos_crz = d_pos + OFFSET
            if pos_crz >= pos:
                chosen = (pos_crz, d_pos)
                break
            if d_pos > pos + 5000:
                break
        if chosen is None:
            print(f"Couldn't place CRZ for v={v} at char '{ch}'")
            sys.exit(1)
        pos_crz, d_pos = chosen
        while pos < pos_crz:
            prog.append(encode_char(68, pos))
            pos += 1
        polluted.add(pos)      # CRZ instruction position
        polluted.add(d_pos)    # CRZ d-target (mem overwritten)
        prog.append(encode_char(62, pos))
        pos += 1

    # PRINT
    polluted.add(pos)
    prog.append(encode_char(5, pos))
    pos += 1

# Phase 4: HALT
prog.append(encode_char(81, pos))
pos += 1

print(f"Program length: {len(prog)} bytes")

out_path = "/home/markus/projects/malbolge_stuff/dotmu/claude_noInput5.mu"
with open(out_path, "wb") as f:
    f.write(bytes(prog))
print(f"Written {out_path}")
