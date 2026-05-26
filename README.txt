● Python scripts:
  - mb_sim.py — Python simulator of the fast20 Malbolge Unshackled VM (exact match: CRZ, ROTR, XLAT, lazy memory, all 8 opcodes)
  - mb_gen.py — Generates straight-line INPUT/PRINT programs; used to build claude_printer.mb
  - mb_cycles.py — Analysis of XLAT table cycle structure and which positions can reach HALT via JMP
  - mb_crz_transform.py — Demo of CRZ as a "function": reads stdin, applies CRZ/ROTR transforms, shows the mapping
  - mb_loop_design.py — Scratch analysis of loop/flag idioms (explored but abandoned)
  - mb_noInput.py — First no-input attempt: exact-equality CRZ search; fails on 'l'=108 due to trit-4 constraint
  - mb_noInput2.py — Second attempt: mod-256 comparison; also fails (same underlying constraint)
  - mb_noInput3.py — Third attempt: BFS with CRZ+ROTR; had a bug (ROTR rotates mem[D], not A)
  - mb_noInput4.py — Final working version: INPUT (→ A=END-1 on EOF) + 3 CRZs per character

  Malbolge programs (.mb):
  - claude_printer.mb — 41-byte straight-line printer; reads "Claude is the best!\n" from stdin and echoes it
  - claude_noInput.mb — 3724-byte no-input printer; run with fast20 claude_noInput.mb < /dev/null
  - claude_crz1.mb — Reads stdin, applies one CRZ transform per character, prints result
  - claude_crz2.mb — Same but two CRZ transforms per character
  - hello_printer.mb — 35-byte stdin printer for "Hello, Malbolge!\n" (same technique as claude_printer)

  Docs:
  - malbolge_loop_devlog.md — Running devlog covering the VM internals, xlat analysis, why loops are hard, and the string printer approaches
