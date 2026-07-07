# The Malbolge Unshackled interpreters — who's who

Four interpreters, two of which hide behind the name "fast20". Names used
across mucc/malbolge_stuff docs from now on:

| name | source | binary here | speed (ELVM hello) |
|---|---|---|---|
| **fast20-flat19** | `malbolge-lisp/fast20.c` (68 lines) | `fast20/fast20_malbolgelisp` | n/a (wrong output) |
| **fast20-area20** | `fast20/fast20_readable.c` | `../elvm_experiments/tio_hack/fast20_steps` (+step counter), `fast20_clean` | ~1 s |
| **tio** | `tio_unshackled/unshackled.c` | `tio_unshackled/unshackled` | 77 s |
| **haskell-ref** | Ørjan Johansen's `Unshackled.hs` | `referenceImplementation/Unshackled` | 625 s |

Compatibility matrix (all verified 2026-06-10, see
`mucc/research/ELVM_LMFAO_CROSSTEST.md` and `R14A_REPORT.md`):

| program class | fast20-flat19 | fast20-area20 | tio | haskell-ref |
|---|---|---|---|---|
| MalbolgeLISP (`lisp.mb`) | ✓ | ✗ segfault | (untested, slow) | ✓ (slow) |
| mucc raw-byte spikes | ✓ | ✓ | ✓ | ✓ |
| LMFAO/ELVM/mucc-hell code | ✗ garbage | ✓ | ✓ | ✓ |
| unicode output (emoji) | ✗ byte-truncated | ✗ byte-truncated | ✓ UTF-8 | ✓ UTF-8 |

## fast20-flat19 (`fast20.c`, the shipped `fast20_malbolgelisp`)

Purpose-built to run MalbolgeLISP fast. Heavily UB-reliant; build **exactly**
as the malbolge-lisp README says (`clang -O3 -march=native fast20.c`) and
test against `lisp.mb` before trusting a binary.

Model and deviations from spec:
- Flat 19-trit words (`SZ=19`, `END=3^19`); memory is one flat `3^19` array,
  lazy-filled by a SIGSEGV handler with the 6-cycle pattern.
- The **top trit doubles as the tail marker**; `mrot` rotates only the low
  18 trits (keeps trit 18). No width growth, ever.
- Instruction decode adds per-third `offs[]` corrections approximating the
  spec's canonical residue rule; exact only on the value/address slice
  MalbolgeLISP exercises.
- I/O: `putchar(a)` (byte truncation, no UTF-8, no 2t1-newline rule);
  input `'\n'` stays codepoint 10 (no tail-2 encoding); EOF → all-2s.
- No load-time or runtime validity checks — out-of-range cells silently
  corrupt (xlat table read OOB) where tio/haskell-ref error out.

Use for: running `lisp.mb`, mucc raw-byte-backend work targeting the
MalbolgeLISP slice. Never use as an oracle for LMFAO-style code.

## fast20-area20 (`fast20_readable.c`)

"Loosely based on" Lutter's public-domain interpreter; a different, more
faithful model than fast20-flat19 — not just a readable transcription.

Model:
- Word = (area trit, 10-trit high, 10-trit low): 20 explicit trits plus a
  real tail trit. Rotation is a clean 20-trit rotation, area untouched.
- Decode corrections (+52 area=1, +10 area=2) are **exactly** the spec
  canonical residue rule for width-20 representations (verified
  arithmetically and by a 2M-step trace match against width-pinned tio).
- Lazy fill: 6-cycle per page; phase formula ignores the area trit (differs
  from spec for area≠0 pages in general — in practice agreed with tio on
  everything LMFAO code read).

Known bugs/restrictions:
- **Segfaults on `lisp.mb`** (not RAM exhaustion — 15 GiB box, both -O2 and
  -DMEMORY builds; unchecked mallocs suspected; not yet diagnosed).
- Output: area==0 → `putchar` byte truncation (codepoints > 255 print
  wrong — emoji impossible); area≠0 → `'\n'` (overbroad vs the spec's
  exact-2t1 rule, correct in practice).
- No load/runtime validity checks (same silent-corruption caveat).

Builds: `gcc -O2 fast20_readable.c` works. `fast20_steps` = same + an
executed-step counter printed to stderr at HALT (source:
`elvm_experiments/tio_hack/fast20_steps.c`). This is the **dev-loop
interpreter for mucc's HeLL backend** (`mucc/tests/run_hell.sh` uses it) —
50–500× faster than tio/haskell-ref.

## tio (`tio_unshackled/unshackled.c`)

Spec-strict C implementation with arbitrary-precision numbers.
- Rotation width starts at random 10–15 and grows randomly (`rand()` in the
  growth policies, seeded from time) — every run exercises different widths,
  which makes it a great portability fuzzer and a poor step-count oracle.
- Strict: rejects invalid load bytes, errors on out-of-range instruction
  cells at runtime, validates unicode.
- Full UTF-8 I/O (emoji fine). Newline input → 2t1, EOF → 2t2.
- Memory-hungry tree model: ELVM fizzbuzz OOM-killed it (~453 s).
- Hacked builds for experiments live in `elvm_experiments/tio_hack/`
  (`unshackled_w20*.c`: width pinned to 20, growth disabled, JMP/lazy/value
  tracing) — the canonical-residue rule was extracted from its `mod()`.

## haskell-ref (`referenceImplementation/Unshackled`)

Johansen's reference — the semantics ground truth. Slowest of the four
(hello world ≈ 10 min). Full unicode. Use as the final arbiter when
fast20-area20 and tio agree but doubt remains.

## Practical guidance

- Developing mucc HeLL-backend code: iterate on **fast20-area20**
  (`fast20_steps`), confirm on **tio**, spot-check **haskell-ref**.
- Running MalbolgeLISP: **fast20-flat19** only.
- Byte-exact output beyond ASCII: impossible portably (spec I/O is
  codepoints; 128–255 become 2-byte UTF-8 on tio/haskell-ref, truncated
  bytes on the fast20s). Unicode-exact output: spec interpreters only.
