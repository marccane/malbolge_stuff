#!/usr/bin/env python3
"""Generate Malbolge Unshackled programs."""

def encode_char(opcode, pos):
    t = (opcode - pos % 94 + 94 * 100) % 94
    if t < 33:
        t += 94
    return t

def make_input_print_loop(n_chars):
    """Generate a straight-line program: (INPUT PRINT) * n_chars, then HALT."""
    prog = []
    pos = 0
    for _ in range(n_chars):
        prog.append(encode_char(23, pos)); pos += 1  # INPUT
        prog.append(encode_char(5,  pos)); pos += 1  # PRINT
    prog.append(encode_char(81, pos))                # HALT
    return bytes(prog)

if __name__ == "__main__":
    import sys
    s = "Claude is the best!\n"
    prog = make_input_print_loop(len(s))
    print(f"Generated {len(prog)}-byte straight-line INPUT/PRINT program", file=sys.stderr)
    print(f"Target string: {repr(s)}", file=sys.stderr)

    out_path = "/tmp/claude_printer.mb"
    with open(out_path, "wb") as f:
        f.write(prog)
    print(f"Written to {out_path}", file=sys.stderr)
    print(f"Chars: {[chr(b) for b in prog]}", file=sys.stderr)
