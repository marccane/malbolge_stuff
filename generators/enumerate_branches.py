#!/usr/bin/env python3
"""Enumerate every (fb1, input_X, input_Y → V_X, V_Y) combination for the
data-only flag-idiom branching shape (see Section 15 of malbolge_loop_devlog.md).

Use this to discover which input pairs you can discriminate and which
printable characters you can print at the branches.

Usage:
  python3 enumerate_branches.py                  # all printable input pairs
  python3 enumerate_branches.py --inputs YN      # only inputs 'Y' and 'N'
  python3 enumerate_branches.py --char R         # only solutions printing 'R'
"""

import argparse
import sys

VALID_OPCODES = {4, 5, 23, 39, 40, 62, 68, 81}
VALID_V = {36, 37, 39, 40, 81, 82, 84, 85, 90, 91, 93, 94}
FLAG_ADDR = 34


def crazy_low(a, d, n=10):
    crz = [[1, 1, 2], [0, 0, 2], [0, 2, 1]]
    r, k = 0, 1
    for _ in range(n):
        r += k * crz[a % 3][d % 3]
        a //= 3
        d //= 3
        k *= 3
    return r


def valid_fb1_at(pos):
    return sorted(b for b in range(33, 127)
                  if (b + pos) % 94 in VALID_OPCODES)


def v_final(input_byte, fb1):
    V1 = crazy_low(input_byte, fb1)
    return crazy_low(V1, V1)


def enumerate_pairs(inputs_filter=None, char_filter=None):
    """Yield (fb1, ix, iy, V_X, V_Y) tuples satisfying the branching shape."""
    fb1_list = valid_fb1_at(FLAG_ADDR)
    inputs = (range(33, 127) if inputs_filter is None
              else [ord(c) for c in inputs_filter])
    for fb1 in fb1_list:
        # Group inputs by their V_final under this fb1
        by_v = {}
        for inp in inputs:
            V = v_final(inp, fb1)
            if V in VALID_V:
                if char_filter is not None and chr(V) not in char_filter:
                    continue
                by_v.setdefault(V, []).append(inp)
        # Yield every distinct-V pair
        vs = sorted(by_v)
        for i, V_X in enumerate(vs):
            for V_Y in vs[i + 1:]:
                if abs(V_X - V_Y) < 2:
                    continue
                for ix in by_v[V_X]:
                    for iy in by_v[V_Y]:
                        yield (fb1, ix, iy, V_X, V_Y)


def main():
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__)
    p.add_argument("--inputs",
                   help="Restrict to these input characters (e.g. 'YN' or '01ab')")
    p.add_argument("--char",
                   help="Restrict to solutions printing these characters")
    p.add_argument("--limit", type=int, default=200,
                   help="Maximum rows to print (default 200)")
    args = p.parse_args()

    rows = list(enumerate_pairs(args.inputs, args.char))
    if not rows:
        print("No matching solutions.")
        sys.exit(1)

    # Sort: prefer printable inputs, then by V_X
    def key(t):
        fb1, ix, iy, vx, vy = t
        printable = (32 < ix < 127) + (32 < iy < 127)
        return (-printable, vx, vy, fb1, ix, iy)

    rows.sort(key=key)
    shown = rows[:args.limit]

    print(f"{'fb1':>3}  {'input_X':>7}  {'input_Y':>7}  {'V_X':>3}  "
          f"{'V_Y':>3}  {'char_X':>6}  {'char_Y':>6}")
    print("-" * 50)
    for fb1, ix, iy, vx, vy in shown:
        sx = repr(chr(ix)) if 32 < ix < 127 else f"{ix}"
        sy = repr(chr(iy)) if 32 < iy < 127 else f"{iy}"
        cx = repr(chr(vx))
        cy = repr(chr(vy))
        print(f"{fb1:>3}  {sx:>7}  {sy:>7}  {vx:>3}  {vy:>3}  {cx:>6}  {cy:>6}")
    if len(rows) > args.limit:
        print(f"... ({len(rows) - args.limit} more, use --limit to see)")
    print()
    print(f"Total solutions: {len(rows)}")
    print(f"Reachable output characters (V_final ∈ VALID_V): "
          f"{''.join(sorted(chr(v) for v in VALID_V))!r}")
    print(f"Valid fb1 values at position {FLAG_ADDR}: "
          f"{valid_fb1_at(FLAG_ADDR)}")


if __name__ == "__main__":
    main()
