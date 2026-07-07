# Nagoya Toolchain Retarget Plan: Malbolge20 → Malbolge Unshackled

**Goal**: Make programs compiled by the Nagoya toolchain
(`/home/datahoard/repos/malbolge_nagoya`) run correctly on all three
Malbolge Unshackled interpreters:
- `fast20` (inside malbolge-lisp)
- `tio_unshackled` (C, spec-strict)
- Reference Haskell (`Unshackled.hs`)

---

## 1. Why the Current Output Doesn't Work

The Nagoya pipeline emits **Malbolge20** — a dialect with fixed 20-trit
addresses. The three interpreters all implement **Malbolge Unshackled**
(MUI), a related but incompatible spec. The gaps matter for every instruction.

### Dialect Gap Table

| Feature | Malbolge20 | Malbolge Unshackled |
|---|---|---|
| Word / address width | 20 trits fixed (`3^20 = 3 486 784 401`) | Variable; starts at 10–15 trits, grows on MOVD |
| "Area" trit | Not present | 1 leading trit prepended on MOVD-extended cells |
| Lazy fill | On load, each uninitialised cell = `crazy(prev, prev-2)` iteratively | 6-cycle repeating pattern `[40, 53, 27, 7, 93, 7]` before xlat |
| PRINT | Outputs `mem[d] % 256` | Outputs `mem[d] % 256` **but** area ≠ 0 → outputs `'\n'` in fast20 |
| INPUT encoding | Stores char as low 8 bits of a 20-trit word | Stores char in low 8 bits; high trits zeroed |
| Load-time validity | Loader doesn't enforce opcode bytes | Spec loaders require `(byte + pos) % 94 ∈ {4,5,23,39,40,62,68,81}` |
| CRZ on area-trit | N/A | `crz[a1%3][a2%3]` on area trits propagated; area≠0 corrupts PRINT |
| Rotation width | 20 fixed | Grows with each MOVD beyond initial extent |

The **critical** incompatibilities are:
1. **Lazy fill** — different uninitialised cell content breaks every control-flow assumption.
2. **Area trit after CRZ** — even in a 10-trit-only program, CRZ on two `area=0` words produces `area=1`, so the next PRINT outputs `'\n'`.
3. **Load validity** — `tio_unshackled` and the Haskell reference reject programs where any byte fails `(byte+pos) % 94 ∉ valid_opcodes`.

---

## 2. Strategy Options

### Option A — Thin shim (do nothing to Nagoya, post-process output)
Write a Python script that takes a `.mb` binary and adjusts it byte-by-byte
to be spec-valid. Cannot fix the area-trit or lazy-fill divergence at
instruction level — not viable.

### Option B — Restrict to 10-trit addresses; rewrite mid + back-end (recommended)
Keep the high-level C-like language and its parser. Rewrite:
- The intermediate representation (IR) to model 10-trit MUI semantics
- The code generator to emit `.mc` (ternary assembly) targeting MUI
- The assembler (`lowass`) to emit spec-valid bytes

Working entirely in the range `[0, 3^10) = [0, 59048]` avoids rotation-width
complications (width never grows beyond 10 trits unless MOVD is used with
a value ≥ 59049). Area-trit issue is avoided by never letting CRZ produce a
non-zero area trit — achievable by keeping all data words in `area=0` and
never CRZ-ing two words that would produce `area=1`.

### Option C — Target 20-trit MUI
Allow MOVD to grow the address space to 20 trits by prepending a long MOVD
chain at program start. Correct but much harder: rotation-width management
is subtle and the lazy-fill bootstrap is complex.

### Option D — Fork fast20 to match Malbolge20 semantics
Patch `fast20.c` to use Malbolge20 lazy-fill and no area trit. Easiest path
for fast20, but programs still won't run on `tio_unshackled` or the Haskell
reference.

### Option E — Emit Malbolge (original, fixed 8-trit) instead
Radically different instruction encoding; most Nagoya abstractions don't
translate. Not recommended.

**Recommendation: Option B.** It gives a clean target for all three
interpreters and keeps the Nagoya high-level language intact.

---

## 3. Pre-Work: Validation Harness

Before changing anything, build a test suite that can be run against all
three interpreters.

- **`tests/hello_world.mu`** — hand-written "Hello, World!" in MUI assembly;
  must print correctly on all three interpreters.
- **`tests/run_all.sh`** — runs each `.mu` file through all three interpreters,
  diffs output against expected.
- **`tests/check_valid.py`** — static checker: asserts every byte in a `.mu`
  file satisfies `(byte+pos) % 94 ∈ {4,5,23,39,40,62,68,81}`.

Reference hand-written programs already exist in
`/home/markus/projects/malbolge_stuff/dotmu/`.

---

## 4. Phased Plan

### Phase 0 — Understand and document the existing pipeline (0.5 weeks)

| Task | File(s) |
|---|---|
| Trace a `hello.c` compile end-to-end | `highlevel/parser.yy`, `highlevel/scanner.ll` |
| Document IR nodes emitted by the high-level parser | `highlevel/Block.cc`, `Instruction.h` |
| Document what `.mc` (ternary assembly) looks like | `ternary/parser.yy`, `ternary/scanner.ll` |
| Document what `lowass` (low-level assembler) produces | `lowass/` |
| Write a table: each Malbolge20 opcode → intended MUI opcode | N/A (brain-only) |

**Deliverable**: A short `ARCHITECTURE.md` in the repo root explaining the
three-stage pipeline.

### Phase 1 — MUI semantics model (1 week)

Create `mui_model/` (or extend existing headers) with:

| Item | Description |
|---|---|
| `Word` type (10-trit) | `uint32_t low` only; `area` always 0 |
| `crz10(a, b)` | trit-by-trit CRZ, returns `area=0` word always (assert input areas are 0) |
| `rot10(a)` | right-rotate 10-trit word: bottom trit → top, rest shift down |
| `lazy_fill_mui(pos, prev, prev2)` | 6-cycle repeating pattern for uninitialised cells |
| `xlat_step(byte, pos)` | `(byte - 33 + pos) % 94 + 33` — the post-instruction byte advance |
| `valid_opcode(byte, pos)` | returns true iff byte satisfies load-time validity |

Write unit tests for each. This is the ground truth that the code generator
will rely on.

### Phase 2 — Rewrite the code generator (2 weeks)

The code generator (`Generator.cc` / `Generator.h`) currently emits Malbolge20
instruction sequences. Rewrite it to emit MUI-compatible `.mc` ternary assembly.

**Key changes**:

1. **Lazy-fill awareness**: The generator must know what value each uninitialised
   memory cell will have at runtime (given MUI's 6-cycle pattern), so it can
   select instruction positions that decode to the intended opcode.

2. **CRZ area-trit safety**: Any CRZ on user data must ensure both operands have
   `area=0`. After a CRZ, the result has `area = crz[a1%3][a2%3]`; if both
   inputs are `area=0`, the result is `area=1`. This means:
   - Data cells used as CRZ targets must be initialised to `area=0` words.
   - After CRZ, if the result will be printed or used in another CRZ, the area
     trit must be zeroed. This typically requires a ROTR sequence to shift the
     area out, or avoiding CRZ on cells that will be printed.
   - **Simplest fix**: never CRZ into a cell that will be PRINTed; use a
     dedicated "scratchpad" cell for CRZ results, then copy the low 8 trits to
     a PRINT-safe cell.

3. **MOVD semantics**: In MUI, MOVD sets `d = mem[d]`. The generated code must
   track the value of `d` at each program point so it can predict which cell
   will be read/written by OPR-equivalent sequences.

4. **Rotation width**: Restrict all addresses to < 59049. If MOVD is used,
   ensure the value stored at `mem[d]` is also < 59049 so the rotation width
   never grows.

5. **Load-time validity**: Every byte position in the emitted binary must
   satisfy `(byte + pos) % 94 ∈ {4,5,23,39,40,62,68,81}`. The generator must
   check this for every instruction it places and pad with valid NOPs as
   needed.

**Suggested approach**: Start with the simplest program (`hello.c` → print a
string), get it working end-to-end, then add arithmetic, conditionals, loops.

### Phase 3 — Rewrite or adapt the ternary assembler (1 week)

`ternary/` takes `.mc` ternary assembly and produces `.mu` binaries. Changes:

| Item | Change |
|---|---|
| Address space | Cap at 59048 (10 trits); error if out of range |
| Lazy-fill | Emit MUI 6-cycle fill, not Malbolge20 iterative fill |
| Byte validity | After placing each instruction, assert `(byte+pos)%94` is valid; if not, find a NOP that is |
| Output extension | Emit `.mu` not `.mb` |

The 6-cycle MUI lazy-fill formula: for position `p ≥ program_length`,
the cell value before xlat is `[40, 53, 27, 7, 93, 7][p % 6]`. After
xlat: `xlat_step(fill_value, p)`. The assembler must either:
- Place explicit initialisation code at the start of the program to fill
  data cells before use, or
- Choose data cell positions such that the lazy-fill value xlat-decodes to
  a valid NOP, and then overwrite them with actual data before first use.

### Phase 4 — Adapt the high-level front-end (1 week)

The C-like high-level language (`highlevel/`) maps onto the IR nodes in
`Block.cc`. These nodes must now lower to MUI instructions. The main
semantic changes:

| High-level construct | Malbolge20 lowering | MUI lowering |
|---|---|---|
| Variable assignment | OPR sequence | OPR sequence with area-trit guard |
| Arithmetic (`+`, `-`) | Repeated OPR+ROT | Same, but verify area stays 0 |
| Conditional branch | Flag cell + JMP | Flag cell + JMP (same idiom, but data-only cells must be in JMP-skipped region) |
| Function call | CALL/RETURN | Same; push return address onto a stack using CRZ chain |
| Input | INPUT | INPUT (same opcode, different cell effect) |
| Output | OUTPUT | OUTPUT (same opcode, guard area=0 first) |

The **data-only flag idiom** (documented in `malbolge_loop_devlog.md`
Section 15) works on MUI without change, provided the flag cell is in a
JMP-skipped region and all bytes satisfy load-time validity.

### Phase 5 — Integration, testing, documentation (0.5 weeks)

- Run the full test suite against all three interpreters.
- Fix any remaining byte-validity or area-trit issues.
- Write `highlevel-examples/hello.mu` and `highlevel-examples/cat.mu` as
  reference outputs.
- Update `highlevel-examples/README.md` to point to MUI interpreters.

---

## 5. File-by-File Change List

```
malbolge_nagoya/
├── highlevel/
│   ├── Generator.cc        REWRITE  (MUI semantics, area-trit guards, validity checks)
│   ├── Generator.h         UPDATE   (new method signatures)
│   ├── Instruction.cc      MINOR    (add MUI-specific instruction types if needed)
│   ├── Block.cc            MINOR    (lower to new Generator methods)
│   └── Makefile            DONE     (already fixed in commits a2cd346)
├── ternary/
│   ├── Generator.cc        REWRITE  (MUI lazy-fill, 10-trit cap, byte validity)
│   ├── Generator.h         UPDATE
│   └── Makefile            DONE     (already fixed in commit f370687)
├── lowass/
│   ├── (assembler files)   UPDATE   (emit .mu, MUI fill, validity check)
│   └── Makefile            LIKELY   (same -ll / parser.h fixes)
├── tests/                  NEW DIR
│   ├── hello_world.mu      NEW
│   ├── run_all.sh          NEW
│   └── check_valid.py      NEW
└── ARCHITECTURE.md         NEW
```

---

## 6. Smallest Possible First Deliverable (1–2 days)

Before touching any Nagoya source, hand-build a "hello.c equivalent" `.mu`
program using the knowledge from `malbolge_loop_devlog.md` and the existing
`dotmu/` examples:

1. Take the reference `claude_noInput5.mu` (prints a hardcoded string, works
   on all three interpreters).
2. Verify it prints "Hello, World!" correctly on all three.
3. Write it "by hand" using the generator script `mb_noInput5.py` as a model.

This confirms the MUI target is correctly understood before any toolchain work
starts.

---

## 7. Risks and Open Questions

| Risk | Likelihood | Mitigation |
|---|---|---|
| Area-trit after CRZ is hard to avoid in generated code | Medium | Use scratchpad cells; avoid PRINTing CRZ results directly |
| 10-trit address space too small for large programs | Low (initially) | Enough for hello.c, cat.c, small arithmetic; revisit for Phase C later |
| MUI rotation-width growth breaks assumptions | Low (if MOVD values are capped) | Assert all MOVD-stored values < 59049 |
| Lazy-fill 6-cycle doesn't match fast20 | Investigate | fast20 may use same fill; check source |
| Bison/flex version issues in lowass/ | Medium | Apply same Makefile fixes as highlevel/ and ternary/ |
| High-level language has features (arrays, recursion) that are hard in 10-trit MUI | Medium | Implement a subset first; arrays and recursion require stack which needs MOVD chains |

### Open Question: Does fast20 use the same 6-cycle lazy-fill as spec MUI?

Check `/home/datahoard/repos/malbolge-lisp/fast20.c` around the memory
initialisation loop. If not, programs generated for spec MUI may still diverge
on fast20. This must be verified in Phase 0.

---

## 8. Effort Summary

| Phase | Description | Estimated effort |
|---|---|---|
| 0 | Understand pipeline | 0.5 weeks |
| 1 | MUI semantics model | 1 week |
| 2 | Code generator rewrite | 2 weeks |
| 3 | Ternary assembler | 1 week |
| 4 | High-level front-end | 1 week |
| 5 | Integration + tests | 0.5 weeks |
| **Total** | | **~6 weeks** |

This assumes one person working full-time. With Claude's help on boilerplate,
probably closer to **3–4 weeks** of human attention.

---

## 9. Quick-Reference: MUI Opcode Encoding

For any byte `b` at position `p`, the opcode is `(b + p) % 94`:

| Decimal | Opcode | Effect |
|---|---|---|
| 4 | JMP | `c = mem[c]; d = mem[d]` |
| 5 | PRINT | Output `mem[d] % 256`; area must be 0 for non-`'\n'` output |
| 23 | INPUT | Read one byte; store in `mem[d]` |
| 39 | ROTR | `mem[d] = rot(mem[d]); a = mem[d]` |
| 40 | MOVD | `d = mem[d]` |
| 62 | CRZ | `mem[d] = crz(a, mem[d]); a = mem[d]` |
| 68 | NOP | No effect |
| 81 | HALT | Stop |

After each instruction: `mem[c] = xlat(mem[c])`, then `c++; d++`.

CRZ table (trit-by-trit): `crz[a%3][d%3]`

```
    d%3: 0  1  2
a%3=0: [ 1, 1, 2 ]
a%3=1: [ 0, 0, 2 ]
a%3=2: [ 0, 2, 1 ]
```

Area trit follows the same table applied to the area trits of both operands.
If `a.area = 0` and `mem[d].area = 0`, then result area = `crz[0][0] = 1`.
**This is the area-trit trap**: even two "clean" words CRZ to an area-1 result.

---

*Written 2026-05-31. See also: `malbolge_loop_devlog.md` §15 for the branching/flag idiom details.*
