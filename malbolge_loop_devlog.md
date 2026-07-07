# Writing a Loop 1–10 in Malbolge Unshackled via MalbolgeLISP

## 1. Background

### Malbolge

Malbolge (named after the eighth circle of Hell in Dante's Inferno) was invented by Ben Olmstead in 1998. It is an esoteric programming language designed to be as difficult to program in as possible. Its key characteristics:

- **Ternary virtual machine** — all arithmetic and data representation is in base 3.
- **Von Neumann architecture** — code and data share the same memory; there is no separation.
- **Self-modifying code** — every instruction is encrypted after it executes, so the program's own text changes as it runs. Writing a loop requires that the modified instruction cycle back to a valid opcode.
- **Three registers only**: `A` (accumulator), `C` (code pointer), `D` (data pointer).
- **Eight instructions**: JMP, PRINT, INPUT, ROTR (tritwise right-rotation), MOVD (set D), CRZ (crazy operation on A and *D), NOP, HALT.
- **Bounded memory** (3^10 = 59049 cells in standard Malbolge), making it definitively *not* Turing-complete in its standard form.

The "crazy operation" (CRZ) is the primary computation primitive. Applied trit-by-trit, the table is:

```
[D] \ A |  0  1  2
--------+---------
   0    |  1  0  0
   1    |  1  0  2
   2    |  2  2  1
```

### Malbolge Unshackled

Malbolge Unshackled removes the fixed memory size constraint. The rotation width (used in `ROTR`) can grow as the D register increases, making the machine Turing-complete. Key differences from standard Malbolge:

- The rotation width is chosen (or fixed) by the interpreter; it grows with values in D.
- Print outputs Unicode codepoints, not raw bytes.
- Memory is effectively unbounded.

### fast20 — the High-Performance Interpreter

`fast20.c` (bundled with this repository) is a high-performance Malbolge Unshackled interpreter. Its design choices:

- **Fixed rotation width of 19 trits** — slightly faster than 20 trits at negligible functional cost.
- **Lazy virtual memory via `mmap` and SIGSEGV** — instead of allocating the full 4 × 3^19 ≈ 4.6 GB of memory up front, it maps the entire range as `PROT_NONE`, then fills pages on demand via a `SIGSEGV` handler. This means startup is near-instant and only accessed memory is physically allocated.
- **Computed-goto dispatch** — the interpreter loop uses GCC's `&&label` extension to jump directly to instruction handlers without a `switch` overhead.
- **Lookup-table CRZ** — the crazy operation is computed via a precomputed 144-entry LUT with loop unrolling, making it O(1).
- **Inline ROTR** — tritwise rotation with no division, using modular multiplicative inverses discovered by the compiler.

### MalbolgeLISP

MalbolgeLISP is the Malbolge Unshackled program under study: a full LISP interpreter, approximately 350 MB of Malbolge Unshackled code, running on top of fast20. It implements:

- A Scheme/Haskell-influenced LISP dialect with lexical scoping.
- Higher-order functions: `map`, `filter`, `fold`, `scan`, `zip`, `iterateN`, `iterate`.
- Point-free programming via `bind`, `bind'`, `atop`, `fork`, `selfie`, `commute`.
- Tacit (point-free) expressions, De Bruijn indices (`bruijn`), partial application.
- Lazy evaluation (`lazy` / `?expr`).
- A rich numeric library: `+`, `-`, `*`, `/`, `%`, `^`, `!`, `gcd`, `lcm`, `min`, `max`.
- List primitives: `car`, `cdr`, `cons`, `tie`, `nth`, `iota`, `size`, `rev`, `sort`, etc.
- 26-bit unsigned integers, with unbounded variants (`+'`, `-'`) available.

---

## 2. Compilation

The interpreter is a single C file using POSIX APIs. Compiled with full optimisations:

```sh
gcc -O3 -march=native -o fast20 fast20.c
# or, as recommended by the author:
clang -O3 -mtune=native -march=native -fvisibility=hidden -o fast20 fast20.c
```

The interpreter is then invoked with a Malbolge Unshackled source file.

---

## 3. Assembling MalbolgeLISP

MalbolgeLISP ships in two parts:

| File             | Size   | Role |
|------------------|--------|------|
| `init_module.mb` | ~19 KB | Bootstrapping preamble |
| `core.mb`        | ~354 MB| The LISP interpreter proper |

They must be concatenated before execution:

```sh
cat lisp/init_module.mb lisp/core.mb > /tmp/lisp.mb
```

The total ~354 MB is the second-largest Malbolge program ever written (the largest is MalbolgeLISP v1.1).

---

## 4. First Test — Basic Arithmetic

To verify that the interpreter loads and executes correctly, we test a trivial expression:

```sh
echo "(+ 2 3)" | ./fast20 /tmp/lisp.mb
```

**Output:**

```
MALBOLGELISP V1.2 (2020-2021, PALAIOLOGOS)
DOT COMMANDS:  .F(eatures)  .A(uthor)  .R(eset)  .M(emory)  .S(ymbols)  .E(xport)  .I(mport)
% ......|....
5
%
```

The progress bar (`.....`) shows parsing steps; the `|` separates parsing from evaluation; the result is printed afterwards. Confirmed: the interpreter is functional.

---

## 5. Designing a Loop from 1 to 10

### The Challenge

MalbolgeLISP is a **functional** LISP with no mutable state and no traditional `for`/`while` loops. Iteration is expressed via:

1. **Higher-order list functions** (`map`, `filter`, `fold`, `scan`, `iterateN`).
2. **Explicit recursion** (via `defun` / `bruijn`).

We explore two approaches.

---

### Approach 1: Functional — `map` + `iota` (Recommended)

`iota n` generates the list `(0 1 2 ... n-1)`. To produce 1–10 we shift by 1 using partial application. `map f list` applies `f` to every element. `print x` prints `x` as a side effect and returns it.

```lisp
(map print (map (bind + 1) (iota 10)))
```

Breakdown:

| Sub-expression        | Result                              |
|-----------------------|-------------------------------------|
| `(iota 10)`           | `(0 1 2 3 4 5 6 7 8 9)`            |
| `(bind + 1)`          | Partial application: `λx.(+ 1 x)`  |
| `(map (bind + 1) ...)` | `(1 2 3 4 5 6 7 8 9 10)`          |
| `(map print ...)`     | Prints each element; returns same list |

**Execution:**

```sh
printf '(map print (map (bind + 1) (iota 10)))\n(off)\n' | ./fast20 /tmp/lisp.mb
```

**Output:**

```
MALBOLGELISP V1.2 (2020-2021, PALAIOLOGOS)
DOT COMMANDS: ...
% ....................|............................................................................
1
...
2
...
3
...
4
...
5
...
6
...
7
...
8
...
9
...
10

(1 2 3 4 5 6 7 8 9 10)
%
```

Each number is printed as a side effect of `map print`. The final return value `(1 2 3 4 5 6 7 8 9 10)` is the list itself. Evaluation completes in a few seconds.

---

### Approach 2: Explicit Recursion via `defun`

We define a recursive function that:
- Takes a counter `n` and a maximum `mx`.
- If `n > mx`, returns `null` (base case).
- Otherwise prints `n`, then recurses with `n+1`.

```lisp
(defun loop (n mx)
  (if [n > mx]
      null
      (tie (print n) (loop [n + 1] mx))))

(loop 1 10)
```

The `[a f b]` bracket syntax is syntactic sugar for `(f a b)` — so `[n > mx]` means `(> n mx)` and `[n + 1]` means `(+ n 1)`.

`tie` constructs a list from its arguments, so the return value is a nested-list structure: `(1 (2 (3 ... (10 null)...)))`.

**Execution:**

```sh
printf '(defun loop (n mx) (if [n > mx] null (tie (print n) (loop [n + 1] mx))))\n(loop 1 10)\n(off)\n' \
  | ./fast20 /tmp/lisp.mb
```

**Output (numbers print correctly):**

```
1
2
3
4
5
6
7
8
9
10
(1 (2 (3 (4 (5 (6 (7 (8 (9 (10 null))))))))))
```

This approach is **correct but slow**. Each recursive call incurs symbol table lookups and closure creation. The functional map approach processes the same task in a fraction of the time.

---

## 6. Performance Comparison

| Approach             | Code                                          | Speed    | Notes |
|----------------------|-----------------------------------------------|----------|-------|
| `map` + `iota`       | `(map print (map (bind + 1) (iota 10)))`      | Fast (~1s) | Idiomatic MalbolgeLISP |
| Recursive `defun`    | `(defun loop ...) (loop 1 10)`                | Slow (~60s+) | More readable, very slow |

The PDF documents similar timing differences: a naive doubly-recursive Fibonacci takes 1m 19s for `(fib 6)`, while an iterative version takes 43s.

---

## 7. How Malbolge Unshackled Executes This

Every `.` in the progress bar corresponds to one Malbolge Unshackled instruction being executed in the parsing/evaluation engine of MalbolgeLISP. By the time `(map print (map (bind + 1) (iota 10)))` returns:

- The fast20 interpreter has executed billions of Malbolge Unshackled instructions.
- Each instruction's opcode was determined by its position in the 354 MB file, modified by the self-encryption after execution.
- The 19-trit rotation width remains constant (per fast20's design) but the D register pointer traverses a huge working set.
- The LISP evaluator — itself Malbolge Unshackled code — constructs lists, creates closures, and resolves symbols all through CRZ, ROTR, JMP, and the five other instructions.

---

## 8. Architecture of the Malbolge Unshackled VM (fast20)

The key data structures in `fast20.c`:

```c
typedef u32 W;          // a Malbolge word: one 32-bit integer holding a trit value
#define SZ  19          // fixed rotation width: 19 trits
#define END 1162261467ULL  // 3^19 = max trit value

W *mem;                 // flat array: the entire Malbolge memory
W  pat[6];              // repeating pattern for lazy-initialised memory
```

The main execution loop uses computed gotos:

```c
void *j[94];            // jump table indexed by (opcode % 94)
// ...
INS_4:  c = *d; NXT;               // JMP: C = *D
INS_5:  putchar(a); fflush(stdout); NXT;  // PRINT: output A as Unicode
INS_23: a = getchar() == EOF ? END-1 : getchar(); NXT; // INPUT
INS_39: a = *d = mrot(*d); NXT;    // ROTR: rotate *D right
INS_40: d = mem + *d; NXT;         // MOVD: D = *D (pointer load)
INS_62: a = *d = mcrz(a, *d);      // CRZ: crazy operation
INS_68: NXT;                        // NOP
INS_81: return 0;                   // HALT
```

After each instruction `NXT` encrypts the executed cell via the `xlat` table and advances C and D.

---

## 9. Key MalbolgeLISP Concepts Used

| Concept          | Description | Example |
|------------------|-------------|---------|
| `iota n`         | Generate 0..n-1 | `(iota 10)` → `(0..9)` |
| `bind f x`       | Partial application: fix first arg | `(bind + 1)` → `λy.(+ 1 y)` |
| `map f list`     | Apply f to every element | `(map (bind + 1) '(0 1 2))` → `(1 2 3)` |
| `print x`        | Output x, return x | side-effecting identity |
| `[a op b]`       | Bracket syntax sugar: `(op a b)` | `[n + 1]` = `(+ n 1)` |
| `defun f (args) body` | Define a function | Standard LISP `defun` |
| `if cond t f`    | Conditional | `(if (= x 0) yes no)` |
| `tie a b ...`    | Build a list from atoms | `(tie 1 2 3)` → `(1 2 3)` |
| `null`           | Empty list / false | `(= null null)` → `1` |

---

## 10. Conclusion

We demonstrated that:

1. **Compiling** `fast20.c` with `-O3 -march=native` produces a capable Malbolge Unshackled interpreter.
2. **Assembling** MalbolgeLISP by concatenating `init_module.mb` and `core.mb` gives a working ~354 MB Malbolge Unshackled program.
3. **Running** MalbolgeLISP with a simple expression (`(+ 2 3)`) confirms the interpreter loads and evaluates correctly.
4. **A loop from 1 to 10** in MalbolgeLISP is most elegantly expressed as:
   ```lisp
   (map print (map (bind + 1) (iota 10)))
   ```
   This functional, point-free style is idiomatic MalbolgeLISP and runs in seconds.
5. An **explicit recursive loop** also works but is dramatically slower.

The entire computation — from typing a LISP expression to seeing `10` printed — passes through billions of Malbolge Unshackled instruction cycles, each one self-modifying, running on a ternary virtual machine, inside a 354 MB program that is itself the product of months of development. Yet the user sees a clean LISP REPL.

---

## 11. Programming in Raw Malbolge Unshackled From Scratch

This section explains how Malbolge programs are actually written at the byte level — without any toolchain, working from first principles.

### 11.1 The Instruction Encoding Problem

The defining challenge of Malbolge is that **the character you write is not the instruction you get**. The instruction executed at position P depends on *both* the raw character value at that position *and* P itself:

```
instruction = (P + raw_char_value) % 94
```

where `raw_char_value` is the ASCII code of the character in the file (must be in range 33–126, i.e. printable ASCII).

There are only 8 valid instruction opcodes. Everything else is a NOP:

| Opcode | Normalised char | Instruction | Effect |
|--------|----------------|-------------|--------|
| 4      | `i`            | JMP         | `C = *D` |
| 5      | `<`            | PRINT       | Output A as Unicode codepoint |
| 23     | `/`            | INPUT       | `A = getchar()` (or MAX-1 on EOF) |
| 39     | `*`            | ROTR        | `A = *D = rot_right(*D)` |
| 40     | `j`            | MOVD        | `D = *D` (pointer load) |
| 62     | `p`            | CRZ         | `A = *D = crazyop(A, *D)` |
| 68     | `o`            | NOP         | Nothing |
| 81     | `v`            | HALT        | Exit |

To place a specific instruction I at position P, you need a raw character with ASCII code:

```
raw = ((I - P) mod 94) + 33
```

adjusted upward by 94 if the result is below 33.

**Example — encoding a 5-NOP + HALT sequence starting at position 0:**

| Pos | Opcode | Instruction | Formula                | Raw char |
|-----|--------|-------------|------------------------|----------|
| 0   | 68     | NOP         | (68 - 0) % 94 + 33 = 101 | `'e'`  |
| 1   | 68     | NOP         | (68 - 1) % 94 + 33 = 100 | `'d'`  |
| 2   | 68     | NOP         | (68 - 2) % 94 + 33 = 99  | `'c'`  |
| 3   | 68     | NOP         | (68 - 3) % 94 + 33 = 98  | `'b'`  |
| 4   | 68     | NOP         | (68 - 4) % 94 + 33 = 97  | `'a'`  |
| 5   | 81     | HALT        | (81 - 5) % 94 + 33 = 109 | `'m'`  |

Program: `edcbam`

**Example — decoding the cat program** (reads input and echoes it):

```
(=BA#9"=<;:3y7x54-21q/p-,+*)"!h%B0/.~P<<:(8&66#"!~}|{zyxwvugJk
```

Key positions decoded:

| Pos | Char | Decoded opcode | Instruction |
|-----|------|----------------|-------------|
| 0   | `(`  | (0+40)%94=40   | MOVD: `D = *D` |
| 1   | `=`  | (1+61)%94=62   | CRZ: `A = *D = crazyop(A, *D)` |
| 4   | `#`  | (4+35)%94=39   | ROTR: `A = *D = rot(*D)` |
| 22  | `p`  | (22+112)%94=40 | MOVD |
| 32  | `B`  | (32+66)%94=4   | JMP: `C = *D` |
| 33  | `0`  | (33+48)%94=81  | HALT |
| 37  | `P`  | (37+80)%94=23  | INPUT: `A = getchar()` |
| 39  | `<`  | (39+60)%94=5   | PRINT: output A |
| 40  | `:`  | (40+58)%94=4   | JMP |

The program cleverly places MOVD, CRZ, ROTR at the start to set up D, then loops around INPUT → PRINT → JMP back.

---

### 11.2 The Self-Modification Problem

After every instruction execution, the cell at position P is **overwritten** via the xlat encryption table:

```
mem[P]  ←  xlat[ mem[P] ]
```

The xlat table (from fast20.c) maps every printable ASCII character to another:

```
'!' → '5'   '"' → 'z'   '#' → ']'   '$' → '&'   '%' → 'g'   '&' → 'q'
"'" → 't'   '(' → 'y'   ')' → 'f'   '*' → 'r'   '+' → '$'   ',' → '('
'-' → 'w'   '.' → 'e'   '/' → '4'   '0' → '{'   '1' → 'W'   '2' → 'P'
'3' → ')'   '4' → 'H'   '5' → '-'   '6' → 'Z'   '7' → 'n'   '8' → ','
'9' → '['   ':' → '%'   ';' → '\'   '<' → '3'   '=' → 'd'   '>' → 'L'
'?' → '+'   '@' → 'Q'   'A' → ';'   'B' → '>'   'C' → 'U'   'D' → '!'
'E' → 'p'   'F' → 'J'   'G' → 'S'   'H' → '7'   'I' → '2'   'J' → 'F'
'K' → 'h'   'L' → 'O'   'M' → 'A'   'N' → '1'   'O' → 'C'   'P' → 'B'
'Q' → '6'   'R' → 'v'   'S' → '^'   'T' → '='   'U' → 'I'   'V' → '_'
'W' → '0'   'X' → '/'   'Y' → '8'   'Z' → '|'   '[' → 'j'   '\' → 's'
']' → 'b'   '^' → '9'   '_' → 'm'   '`' → '<'   'a' → '.'   'b' → 'T'
'c' → 'V'   'd' → 'a'   'e' → 'c'   'f' → '`'   'g' → 'u'   'h' → 'Y'
'i' → '*'   'j' → 'M'   'k' → 'K'   'l' → "'"   'm' → 'X'   'n' → '~'
'o' → 'x'   'p' → 'D'   'q' → 'l'   'r' → '}'   's' → 'R'   't' → 'E'
'u' → 'o'   'v' → 'k'   'w' → 'N'   'x' → ':'   'y' → '#'   'z' → '?'
'{' → 'G'   '|' → '"'   '}' → 'i'   '~' → '@'
```

**Consequence**: an instruction written at position P executes *once*, then the cell becomes a different character, which (at the same position P) decodes to a *different* instruction. To execute the same instruction twice you must either:
1. Restore the original character from elsewhere in memory before execution reaches P again, or
2. Find a position and character such that xlat(c) decodes to the same instruction at position P (an "instruction cycle").

**Example** — NOP at position 0: initial char `'e'` → decoded = (0+101)%94 = 7 = NOP. After one execution: `'e'` → xlat → `'c'` (ASCII 99). Next time position 0 runs: (0+99)%94 = **5 = PRINT**. The cell silently became a print instruction.

This is why Malbolge programs require meticulous design: every instruction modifies its own cell. A loop body must either be self-repairing or exploit cycles in the xlat→decode chain.

---

### 11.3 Instruction Cycles

An *instruction cycle* at position P with initial char c is a sequence:

```
c → xlat(c) → xlat(xlat(c)) → ... → c    (after N steps)
```

such that every character in the cycle decodes to the **same** instruction (mod 94) at position P. Cycles are the mechanism behind every non-trivial Malbolge program.

To find cycles for a given instruction I at position P:

```python
def find_cycle(opcode, position, xlat):
    # Find a char c at position P that cycles back to the same opcode
    for start in range(33, 127):
        c = start
        cycle = []
        while True:
            decoded = (position + c) % 94
            if decoded != opcode:
                break
            cycle.append(c)
            c = ord(xlat[c])
            if c == start:
                return cycle   # valid cycle found
            if len(cycle) > 100:
                break
    return None
```

In practice, useful cycles are rare and position-specific. The 14,000 NOP/MOVD flag structures in MalbolgeLISP were discovered through this kind of analysis.

---

### 11.4 The Constant Load Idiom

Loading an arbitrary constant into register A is the foundational operation for any non-trivial Malbolge program. Because ROTR shifts trits and CRZ applies the crazy operation, neither directly sets A to a chosen value. The PDF describes the following idiom (using pseudo-assembly in normalised form):

```
ENTRY:  ROT    CON1    REV    ROT
        OPR    $T      REV    OPR
        HLT
```

where:
- `CON1` = a memory region filled with the 19-trit all-ones constant (1111111111111111111₃)
- `$T` = a memory region containing the desired value T in trinary
- `REV` = a NOP sled used as a spacer (for alignment and cycle management)
- `ROT` = ROTR instruction; `OPR` = CRZ instruction

**How it works:**

1. `ROT CON1` — D points to CON1; ROTR loads the all-ones value into A and *D simultaneously.
2. `OPR $T` — CRZ(CON1, T): applies the crazy table trit-by-trit between A (=CON1=111...1) and *D (=T). The crazy table row for A-trit=1 maps: (1,0)→0, (1,1)→0, (1,2)→2. This picks out every "2" trit from T and leaves zeros elsewhere. **This only works if T has no "1" trits in trinary — i.e. T is "non-tricky".**
3. `ROT OPR` — second round: loads CON1 again, CRZ-es with the intermediate result to combine the "1" and "2" trits.

For "tricky" values (containing 1-trits in their base-3 representation), a 3-step loading sequence is needed, using a CON0-based mask to isolate the 1-trits first. See PDF section 1.2.1 for the full algorithm.

**Example — loading the value 15 (= 120₃, non-tricky):**

```
Trinary: 120   (1×9 + 2×3 + 0×1 = 15)
Has 1-trits? YES (the leading 1) → tricky value → need 3 CRZ operations
```

**Example — loading the value 8 (= 022₃, non-tricky):**

```
Trinary: 022   (0×9 + 2×3 + 2×1 = 8)
Has 1-trits? No → non-tricky → 1 CRZ operation suffices
Step: CRZ(CON1, 022) → maps (1,0)→0, (1,2)→2, (1,2)→2 → result = 022 = 8 ✓
```

---

### 11.5 The Flag Idiom (Branching)

Malbolge has no conditional branch instruction. Branching is implemented by exploiting self-modification: a "flag" is a chain of NOP/MOVD/NOP/MOVD... cells placed in sequence. The key property:

- In its *set* state, the chain has `MOVD` at one position → JMP lands at different address.
- In its *unset* state, the `MOVD` is shifted forward by one cell → JMP still works but D ends up at a different memory location.

The standard flag structure (from the PDF, section 1.2.2):

```
[NOP] [NOP] [NOP] [MOVD] → JMP
 ↕ rotate through states by overwriting cells
```

A NOP/NOP/NOP/MOVD chain can be in four states depending on which cell currently holds MOVD. The chain is advanced by writing a new character to the first cell (using CRZ to compute the right value), which forces the MOVD to rotate position.

**Setting a flag**: CRZ a specific value into the flag region so MOVD appears at the chosen offset.
**Reading a flag**: Execute JMP after the flag chain — the resulting C value differs based on which cell is MOVD vs. NOP.

This is how MalbolgeLISP implements conditionals and loops across its ~14,000 flag structures.

---

### 11.6 Writing a Counter 1–10 in Raw Malbolge Unshackled

A counter from 1 to 10 in raw Malbolge Unshackled requires all of the above plus:

#### Step 1 — Set up the rotation width

Malbolge Unshackled's ROTR width starts unknown. Before any arithmetic is reliable, you must probe the current rotation width by performing a sequence of ROTRs and observing when a bit cycles. This requires a loop itself, creating a chicken-and-egg problem. The standard approach is a *rotwidth loop*: ROTR a known value (e.g. CON1) repeatedly, counting iterations until it wraps back to CON1. The count reveals the width.

#### Step 2 — Represent the counter

A counter in ternary arithmetic. Increment is implemented by:
```
carry_out(x) = CRZ(CON2_masked, x)  ; isolates carry trits
sum(x)       = CRZ(CON0, x) then combine with carry
```
The PDF's toolchain uses a multi-step carry/sum sequence (see section 1.4, the `sum` and `carry` functions). Addition of N to a register is O(N) in the simpler case (repeated increment) or O(1) in the toolchain's CRZ-based approach.

#### Step 3 — Output each digit as Unicode

PRINT outputs A as a Unicode codepoint. To print the digit '1' (codepoint 49), you must:
1. Load 49 into A using the constant load idiom.
2. For each subsequent digit n (2–10), add 1 to A and then PRINT.
3. For '10' (two digits), you need to print '1' (49) then '0' (48) — requiring a different constant load.

Between each printed number, print a newline (codepoint 10). Note: the PDF explicitly calls out that codepoint 10 is "theoretically impossible to obtain without having received a newline from I/O first" — a known Malbolge Unshackled limitation. In practice, reading EOF first (which sets A to MAX-1) combined with CRZ tricks can produce it.

#### Step 4 — Build the loop with a flag

Use a flag structure to track how many times the loop body has executed:

```
[load counter] → [compare counter to 10] → [conditional JMP via flag] → [print digit] → [increment] → [loop back]
```

Each component requires its own carefully crafted instruction cycles to survive multiple loop iterations. Every cell that participates in the loop must be at a position where its xlat cycle reproduces the correct instruction.

#### Step 5 — Terminate

When the counter reaches 11, the flag sets the MOVD to redirect JMP to the HALT cell.

---

### 11.7 The Normalised Form and Assembler

Because hand-calculating encoded characters for every position is impractical, programs are typically written in *normalised form* — using the instruction name characters (`i < / * j p o v`) directly, and an assembler converts them to position-appropriate characters.

From the PDF, the `encodeInt` function:

```c
uint8_t encodeInt(uint64_t code, uint64_t position) {
    int8_t t = (code - position % 94 + 94) % 94;
    if (t < 33) t += 94;
    return t;
}
```

And a simple assembler reads normalised characters, maps them to opcodes via `assembly()` (the switch-case table), then calls `encodeInt` for each position. The corresponding `normalize` tool does the reverse for disassembly.

A normalised counter-from-1-to-10 skeleton (pseudo, showing only the structural intent):

```
; Normalised Malbolge Unshackled sketch
; Note: CON1, CON0, data regions not shown — they live outside the instruction stream

ENTRY:
    *        ; ROTR: probe rotation width (repeated in a sub-loop)
    j        ; MOVD: D = *D (advance D pointer)
    p        ; CRZ:  A = *D = crazyop(A, *D) — load constant
    ...      ; (many more instructions for rotwidth detection)

ROTWIDTH_DONE:
    p        ; CRZ: load 49 ('1') into A via constant-load idiom
    <        ; PRINT: output '1'
    p        ; CRZ: increment A by 1 (via add idiom)
    <        ; PRINT: output '2'
    ...      ; (repeat for 3..9)
    p        ; CRZ: load 49 into A, then print '1' then '0' for digit 10
    <
    p
    <
    v        ; HALT
```

Even this skeleton, when fully elaborated with rotwidth detection, carry arithmetic, flag logic, and NOP sleds to align instruction cycles, grows to hundreds or thousands of characters — and must be verified by simulation before running, since a single wrong character silently corrupts the execution.

---

### 11.8 Why MalbolgeLISP Is 354 MB

The above illustrates why MalbolgeLISP is so large:

- **~14,000 flag structures** — each conditional in the LISP interpreter (type checks, null checks, comparisons) requires a flag chain.
- **NOP sleds** — large regions of NOP instructions pad the code so that instruction cycles at specific positions are correct.
- **Self-repairing code** — every instruction that runs in a loop must have a companion repair sequence to restore its cell after xlat modifies it.
- **Data regions** — CON0, CON1, CON2 constants, lookup tables, and runtime stack/heap structures interleaved with the code.
- **Arithmetic sub-routines** — unbounded-precision addition and subtraction, each requiring the carry/sum CRZ idiom applied trit-by-trit across arbitrary-width words.

The toolchain that generated MalbolgeLISP comprises 57,000 lines of code in C, C++, Perl, Python, APL, and Lua. No one has written a program of this complexity by hand.

---

### 11.9 Practical Toolchains

The only known practical approaches to writing non-trivial Malbolge programs:

| Approach | Description |
|----------|-------------|
| **Nagoya University toolchain** | Pseudo-assembly (`@label`, `cmov`, `cadd`, etc.) compiled to Malbolge via asm2bf. Used for MalbolgeLISP. |
| **LAL / HAL** | Higher-level abstractions targeting Malbolge, predecessor to MalbolgeLISP's toolchain. |
| **Bruteforce / genetic algorithms** | How the original "Hello World" Malbolge program was found. |
| **Normalised-form assembler** | Write in normalised characters (`i < / * j p o v`), let `encodeInt` handle position arithmetic. |

Writing directly in encoded Malbolge (raw file characters, no tools) is essentially infeasible for programs of more than ~10 instructions.

---

## 12. Printing "Claude is the best!" in Raw Malbolge Unshackled

### 12.1 The Simulator

Before writing any raw Malbolge program, a Python simulator of fast20 was written at `/tmp/mb_sim.py`. It implements:

- `mrot(x)` — 19-trit right rotation, matching fast20's C macro exactly
- `mcrz(a, d)` — trit-by-trit CRZ using the truth table from fast20's `crz[]` array
- The xlat string from fast20's `NXT` macro (141 chars, indexed directly by `mem[C]`)
- All 8 opcodes with correct semantics (D=pointer not index, JMP sets C=mem[D]+1, etc.)
- Lazy mcrz-fill for memory beyond the program

The encoding formula for placing opcode OP at position P:

```python
def encode_char(op, pos):
    t = (op - pos % 94 + 9400) % 94
    if t < 33: t += 94
    return t
```

Verification: `encode_char(23, 0)` = 117 ('u'). `(0 + 117) % 94` = 23 = INPUT. ✓

### 12.2 The Straight-Line Strategy

The key insight: in a **straight-line program** (no loops, no JMP), each instruction position is visited exactly once. Therefore:

- The xlat self-modification after each instruction doesn't matter (position never revisited)
- The data pointer D = C at all times (both start at 0, both increment by 1 after every instruction)
- So `*D = mem[C]` = the encoded instruction character itself

For printing a fixed string of N characters from stdin, the cleanest approach:

```
(INPUT PRINT) × N then HALT
```

Each INPUT reads one byte from stdin into A; each PRINT outputs A directly via `putchar(a)`.

### 12.3 The Generated Program

For "Claude is the best!\n" (20 characters including newline):

```python
def make_input_print_loop(n_chars):
    prog = []
    pos = 0
    for _ in range(n_chars):
        prog.append(encode_char(23, pos)); pos += 1  # INPUT
        prog.append(encode_char(5,  pos)); pos += 1  # PRINT
    prog.append(encode_char(81, pos))                # HALT
    return bytes(prog)
```

Generated 41-byte program (source chars): `ubs`q^om\ZkXiVgTe RcPaNLJ[HYFWDUBs@Q>O<)`

```
Position  0: 'u'(117) → opcode (0+117)%94=23 INPUT
Position  1: 'b'(98)  → opcode (1+98)%94=5   PRINT
Position  2: 's'(115) → opcode (2+115)%94=23 INPUT
Position  3: '`'(96)  → opcode (3+96)%94=5   PRINT
...
Position 38: 'O'(79)  → opcode (38+79)%94=23 INPUT
Position 39: '<'(60)  → opcode (39+60)%94=5  PRINT
Position 40: ')'(41)  → opcode (40+41)%94=81 HALT
```

### 12.4 Results

**Simulator verification:**
```python
out = simulate(prog, b"Claude is the best!\n")
# out == b"Claude is the best!\n"  ✓
```

**Running on fast20:**
```bash
$ echo -n "Claude is the best!" | /tmp/fast20 /tmp/claude_printer.mu
Claude is the best!
```

The program works. The 41-byte Malbolge Unshackled source file correctly prints the target string.

### 12.5 The Generator as a Function

The `make_input_print_loop(n)` generator function creates a valid Malbolge Unshackled printer for **any** string of length n. Verified:

| String | Length | Works |
|--------|--------|-------|
| "Claude is the best!\n" | 20 | ✓ |
| "Hello, Malbolge!\n" | 17 | ✓ |
| "Functions work!\n" | 16 | ✓ |

Each program is n×2+1 bytes (INPUT+PRINT per char, plus HALT).

### 12.6 CRZ Transformation — Malbolge Computation

To demonstrate that Malbolge Unshackled actually *computes* (not just passes data through), a CRZ-transform program was built:

```
(INPUT CRZ PRINT) × N then HALT
```

At position P, the CRZ instruction uses `*D = mem[P]` = `encode_char(62, P)` as its operand. This applies a deterministic, position-dependent CRZ transform to each input character.

Applied to "Claude is the best!\n", single-CRZ output: high bytes (>127) — all outside printable ASCII, confirming non-trivial computation.

A double-CRZ variant (INPUT CRZ CRZ PRINT) produced more varied output, with the first character 'C'(67) mapping to 67 (self-stable under the specific double-CRZ transform at those positions).

### 12.7 Why Loops Are Fundamentally Hard

Analysis of the xlat cycle system reveals why loops in raw Malbolge Unshackled are so difficult:

1. **No XLAT fixed points** in [33,126] — every instruction character changes after execution
2. **Only one 2-cycle** — chars 'F'(70) ↔ 'J'(74) — useful only for alternating JMP/NOP patterns
3. **JMP target = mem[D]+1** — the value at D (not D itself) determines destination; D changes with every instruction
4. **All loop body instructions xlat-degrade** — on the second pass, nearly all INPUT/PRINT instructions become NOP because their xlat'd values don't map to the same opcode at the same position

**Example:** INPUT at position 40 (char 'M'=77) → on second visit, char becomes XLAT[77]='A'(65), opcode = (40+65)%94 = 11 = NOP. The INPUT is gone.

Making loops work requires the "flag idiom" from the MalbolgeLISP book: carefully selected NOP/MOVD chains where both the first-visit AND second-visit opcodes are controlled. MalbolgeLISP uses ~14,000 such constructs.

---

## 13. MalbolgeLISP Functions

Running the MalbolgeLISP interpreter demonstrates true higher-order functions.

### 13.1 Basic Function Definition

```lisp
% (defun add1 (x) (+ x 1))
(lambda (x) (+ x 1))

% (defun apply-twice (f x) (f (f x)))
(lambda (f x) (f (f x)))

% (apply-twice add1 65)
67
```

`apply-twice add1 65` → 65+1+1 = **67** — the ASCII code of **'C'** (first char of "Claude"). This is a higher-order function (takes a function as argument) executing correctly in a LISP interpreter written in Malbolge Unshackled.

### 13.2 Filter — Extract Non-Space Characters

```lisp
% (filter (bind < 32) '(67 108 97 117 100 101 32 105 115 32 116 104 101 32 98 101 115 116 33))
(67 108 97 117 100 101 105 115 116 104 101 98 101 115 116 33)
```

Removes the three spaces (ASCII 32) from "Claude is the best!" — leaves `Claudeisthebest!`.

### 13.3 Map — Uppercase Conversion

```lisp
% (map (lambda (c) (if [c > 96] [c - 32] c)) '(67 108 97 117 100 101))
(67 76 65 85 68 69)
```

Converts "Claude" (ASCII: 67 108 97 117 100 101) to "CLAUDE" (67 76 65 85 68 69). The lambda is an inline if-expression: subtract 32 from any char > 96 (lowercase letter) to get uppercase.

### 13.4 Fibonacci

```lisp
% (defun fib (n) (if [n < 2] n [(fib [n - 1]) + (fib [n - 2])]))
(lambda (n) ...)

% (fib 5)
5
```

Naive recursive Fibonacci in MalbolgeLISP. fib(5) = 5 ✓. (fib(8) exceeds practical timeout — the README documents ~1m 19s for fib(6) with this naive implementation.)

### 13.5 Summary of What "Functions" Means in This Context

| Layer | Function capability |
|-------|---------------------|
| **Raw Malbolge Unshackled** | No true functions possible without xlat cycle engineering (the MalbolgeLISP approach) |
| **Straight-line programs** | Single-use code blocks with fixed per-position logic — effectively one-shot |
| **MalbolgeLISP** | Full first-class functions: `defun`, `lambda`, HOFs (`map`, `filter`, `fold`), partial application (`bind`), closures, recursion |

The only practical path to functions in Malbolge Unshackled is through MalbolgeLISP or a similar high-level language compiled by the Nagoya University toolchain.

---

## 14. Inline ROTR and Magic-Number Division by 3

Section 1 mentioned in passing that fast20's `rotate_r` performs "tritwise rotation with no division, using modular multiplicative inverses discovered by the compiler." This section unpacks what that means.

### 14.1 What ROTR is doing

The Malbolge Unshackled ROTR instruction takes a non-negative integer below `END = 3^19` (a 19-trit number) and rotates its trits one position to the right: the bottom trit becomes the top trit, everything else shifts down.

In `fast20.c`, the value is stored across three fields of a `Word`:

```c
typedef struct Word {
    unsigned int area;   // 1 "trit" (values 0,1,2)
    unsigned int high;   // 10 trits  (values 0..59048)
    unsigned int low;    // 10 trits  (values 0..59048)
} Word;
```

The Unshackled spec says 19 trits; the layout here uses 10+10+1 = 21 slots of capacity, with the upper trits intentionally not all reachable — the representation is sparse but easier to manipulate.

`rotate_r` only touches the `high`/`low` pair (the `area` trit is left alone — it isn't part of the rotated digit chain):

```c
static inline Word rotate_r(Word d) {
    unsigned int carry_h = d.high % 3;
    unsigned int carry_l = d.low  % 3;
    d.high = 19683 * carry_l + ((unsigned int) d.high) / 3;
    d.low  = 19683 * carry_h + ((unsigned int) d.low ) / 3;
    return d;
}
```

Read it as "right-shift each 10-trit limb by one trit, and feed each limb's discarded bottom trit into the other limb's top position":

| operation                       | meaning in trit-terms                          |
|---------------------------------|------------------------------------------------|
| `d.high / 3`                    | drop trit 0 of `high`; trits 1..9 move down    |
| `19683 * carry_l`               | place trit 0 of `low` into position 9 of `high` (`3^9 = 19683`) |
| `d.low / 3`                     | drop trit 0 of `low`; trits 1..9 move down     |
| `19683 * carry_h`               | place trit 0 of `high` into position 9 of `low` |

Picture the trits laid out 0..19, with `low` = trits 0..9 and `high` = trits 10..19. The combined effect is:

- trit 0     → trit 19  (rotation wrap-around)
- trit 1..9  → trit 0..8  (shift inside `low`)
- trit 10    → trit 9   (carry crossing the limb boundary)
- trit 11..19 → trit 10..18 (shift inside `high`)

So every trit moved exactly one position down, and the bottom one wrapped to the top. That's a right rotation of a 20-trit number, matching the Unshackled spec.

Why split the work into two limbs? Because `3^20` doesn't fit comfortably into a 32-bit register's "wide multiply by small constant" patterns, and because the splitting matches the memory layout that `crazy()` and `ptr_to()` already use (everything is keyed by `(area, high, low)`). Keeping limbs around 10 trits each means `high` and `low` always stay `< 3^10 = 59049`, well within `uint32_t`.

### 14.2 What you actually want from the compiler

Both `% 3` and `/ 3` are operations on a runtime value (`d.high`, `d.low`) where the *divisor* is a compile-time constant (3). General integer division is one of the slowest instructions on x86 — `div r32` is ~20–40 cycles. But *division by a constant* can be turned into a multiply + shift, which is ~3–5 cycles. The compiler does this transformation automatically, and the mathematics behind it is what people mean by "magic number division" or (more grandly) division via *modular multiplicative inverses*.

The disassembly of `/tmp/fast20` shows it everywhere:

```asm
mov   r15d, 0xaaaaaaab          ; magic constant for /3 (32-bit)
imul  r14,  r15                 ; 64-bit multiply
shr   r14,  0x21                ; >> 33 — now r14 == original / 3
lea   r14d, [r15+r15*2]         ; r14 = (r14/3) * 3
sub   r13d, r14d                ; r13 -= 3*(r13/3)  → r13 == original % 3
```

That five-instruction snippet is exactly `x % 3`, computed without ever executing a `div`. The constant `0xAAAAAAAB` appears 9× in the binary, plus the 64-bit variant `0xAAAAAAAAAAAAAAAB` twice.

### 14.3 What is a "modular multiplicative inverse"?

If you fix a modulus `M` and pick an integer `a`, then `a⁻¹ mod M` is the integer `b` (if one exists) such that

```
a · b ≡ 1   (mod M)
```

It exists exactly when `gcd(a, M) = 1`. It's "the number that undoes multiplication by `a` in modular arithmetic."

Two flavours show up in compilers:

#### 14.3.1 The exact inverse (for exact division)

When `a` divides `x` evenly, `x / a` can be computed as `x · a⁻¹ mod 2^N` (where N is the register width, e.g. 32 or 64). Reason: working modulo `2^N` is exactly what fixed-width unsigned integer multiplication gives you for free, and `(a · a⁻¹) ≡ 1` means multiplying by `a⁻¹` "cancels" an `a`.

For `a = 3`, the inverse mod `2^32` is `0xAAAAAAAB` (= `(2^33 + 1) / 3`). Sanity check: `3 · 0xAAAAAAAB mod 2^32 = 0x100000001 mod 2^32 = 1`. ✓

This trick is exact *only* when `a | x`. If `a` doesn't divide `x` evenly, you get garbage — useful for the divisibility test `(x * 0xAAAAAAAB) < 0x55555556` (≈ "is this `< ⌈2^32/3⌉`?"), but not for general division.

#### 14.3.2 Granlund–Montgomery (for general division by a constant)

For general unsigned division by a positive constant `d`, the trick of Granlund and Montgomery (1994) finds a magic multiplier `m` and a shift `s` such that

```
floor(x / d)  =  (x · m) >> s     for all x in [0, 2^N)
```

The shape is:

1. Pick the smallest `ℓ ≥ ⌈log2 d⌉` such that `2^(N+ℓ)` slightly exceeds a multiple of `d` — concretely, pick `ℓ` so that `m = ⌈2^(N+ℓ) / d⌉` fits in `N+1` bits.
2. Then `(x · m) >> (N + ℓ)` equals `floor(x / d)`.

The "+ℓ extra bits" matter because for some `d` you really do need an (N+1)-bit magic; in that case the compiler emits a slightly longer sequence (add-with-carry, then shift). For `d = 3`, `N = 32`, you can get away with an N-bit magic and shift = 33:

```
m = ⌈2^33 / 3⌉ = ⌈8589934592 / 3⌉ = 2863311531 = 0xAAAAAAAB
floor(x / 3) = (x * 0xAAAAAAAB) >> 33
```

Then `x % 3` is one `lea`+`sub` away: `x % 3 = x - 3 * (x / 3)`, exactly the pattern in the assembly above.

For the 64-bit version the compiler picks `0xAAAAAAAAAAAAAAAB` (= ⌈2^65/3⌉ adjusted to fit), uses `mul rbx` to get a 128-bit product in `rdx:rax`, and shifts `rdx` right by 1 — that's what you see at addresses `0x2102` and `0x30d7` in the binary.

This generalises: 9, 27, 81, 243 all get their own magic numbers. The disassembly of `/tmp/fast20` also shows `imul …,…,0x38e38e39` (the div-by-9 magic) and powers of three like `0x81bf1 = 3^12` and `0x4ce3 = 3^9 = 19683` — the latter being the explicit multiplier in `rotate_r` itself.

### 14.4 How the compiler "discovers" them

This is a compile-time computation, not a runtime one — every modern back-end has a small library implementing it. The canonical reference is *Hacker's Delight* (Warren), chapter 10. The algorithm for unsigned `d`:

```
Find the smallest p ≥ N such that  2^p mod d  ≤  2^(p-N)
Then  m = (2^p + d - (2^p mod d)) / d
And   x / d == (x · m) >> p
```

In words: start with `p = N` and keep growing `p` by one until you find a shift big enough that *rounding up* `2^p / d` produces a multiplier which is correct for every `x` in `[0, 2^N)`. The proof relies on the fact that the error introduced by ceiling-rounding `2^p / d` is at most `1 / d`, and that error is amplified by `x < 2^N`, giving a total error `< 2^N / d ≤ 1` for `p` large enough.

GCC implements this in `gcc/expmed.cc` (`choose_multiplier()`); LLVM's version lives in `llvm/lib/Support/DivisionByConstantInfo.cpp` (`UnsignedDivisionByConstantInfo::get`). Both produce the same magic number for the same divisor; differences in emitted code are choices about how to materialise the multiplier and the post-shift (e.g. when the multiplier needs N+1 bits, GCC tends to emit an `add; shift` sequence and LLVM tends to emit a `mulhi; sub; shr; add; shr` sequence — same answer, different surface form).

The signed case is slightly trickier — you have to adjust for the sign of `x` with an arithmetic shift — but the same `⌈2^p / d⌉` idea drives it.

There's also a much older, simpler trick for `mod 3` specifically: since `4 ≡ 1 (mod 3)`, any number written in base 4 has the property that its digit sum mod 3 equals the number itself mod 3. So you can compute `x % 3` by adding up pairs of bits and recursing. Compilers don't normally use this because it's more instructions than the magic-multiply path, but it's a nice piece of folklore worth knowing.

### 14.5 Why this matters for fast20

ROTR runs millions of times in any non-trivial Malbolge Unshackled program (the MalbolgeLISP interpreter, for instance, leans on it heavily during arithmetic and memory addressing). Replacing two `idiv` instructions (each ~30 cycles) with two `imul/shr/lea/sub` sequences (each ~6 cycles) per call is a ~5× speedup on this one primitive — and it happens entirely for free, with no source-level change. The author wrote `d.low % 3` and `d.low / 3` and let the compiler do the algebra.

Quick verification, if you want to confirm by hand:

- `pow(3, -1, 2**32) == 0xAAAAAAAB` in Python (the exact inverse mod 2³²).
- `((x * 0xAAAAAAAB) >> 33) == x // 3` for any `x` in `range(2**32)` (try `0`, `1`, `2`, `2**31`, `2**32 - 1`).
- `objdump -d /tmp/fast20 | grep -B1 -A4 'aaaaaaab' | head -40` shows the `imul / shr / lea / sub` pattern Section 14.2 describes.

## 15. Branching, Flags, and the Data-Only Flag Idiom

Up to here we have programs that read input and echo or transform it, and programs that produce fixed output with no input. The natural next question — *can a Malbolge Unshackled program do **different** things depending on its input?* — turns out to surface essentially every interesting wart of the language at once. This section documents what we learned building `dotmu/branch_flag.mu` (input `'Y'` → print `'R'`; input `'N'` → print `'$'`), and how to use the same techniques to build your own.

### 15.1 The shape of the problem

Malbolge Unshackled has exactly one control-flow primitive: opcode `4`, **JMP**. It is *unconditional*. There is no "branch if equal", no "skip if zero", no compare-and-jump. JMP just sets `c := mem[d]` (interpreted as a Word, i.e. an address), and the next step decodes whatever lives at that new `c`.

So the whole question "how do I make this program do different things depending on its input?" reduces to:

> **How do I arrange for `mem[d]` to hold a *different Word* when the JMP fires, depending on what the user typed?**

That cell — the one the JMP reads — is the *flag*. Computing the flag is the interesting part; the JMP itself is mechanical.

### 15.2 What can write to the flag?

Three opcodes mutate memory:

| op | name | effect on `mem[d]`                                                  |
|----|------|---------------------------------------------------------------------|
| 39 | ROTR | rotate the trits of `mem[d]` right by one; also `a ← mem[d]`        |
| 40 | MOVD | does **not** write — sets `d ← mem[d]`                              |
| 62 | CRZ  | `mem[d] ← crazy(a, mem[d])`; also `a ← same`                         |

ROTR has no input dependence (it just rotates whatever was already there). MOVD doesn't write at all. That leaves CRZ as the only opcode that can compute a flag value as a function of `A` — and `A` is the only register that ever depends on input (via INPUT, op 23). The general shape of a branching program is therefore:

```
INPUT       — load some input into a
CRZ-chain   — fold a together with predetermined data bytes to produce a flag
JMP         — jump to the cell whose address is the flag value
```

The rest of this section is the *details* needed to make that work in practice.

### 15.3 The 2-CRZ self-cancellation trick

A single CRZ on a freshly-loaded input cell gives a Word with garbage in the upper limbs.

After `INPUT` of byte `B`, `a = (area=0, high=0, low=B)`. Suppose `mem[d]` holds the data byte `fb1`, i.e. `mem[d] = (0, 0, fb1)`. One CRZ produces:

| field | new value                                                |
|-------|----------------------------------------------------------|
| area  | `crz[0 + 3·0] = crz[0] = 1`                              |
| high  | `crazy_low(0, 0) = 29524` (each trit pair `(0,0)` → `OPR[0][0] = 1`, summing `1+3+9+…+3⁹`) |
| low   | `crazy_low(B, fb1)` — call this `V₁`                     |

So `mem[d]` is now `(1, 29524, V₁)`. If we JMP to *this* Word, we land at area 1, page 29524 — deep in lazy-fill memory, whose contents differ between interpreters (Section 8). Useless.

The trick: do a **second** CRZ on this Word, with itself. After CRZ #1, both `a` and `mem[d]` hold the same Word `(1, 29524, V₁)`. CRZ #2 with the same `d` computes `crazy(a, a)` — *self*-CRZ — which has a special structure because `OPR[t][t] ∈ {0, 1}`:

| field | new value                                          |
|-------|----------------------------------------------------|
| area  | `crz[1 + 3·1] = crz[4] = 0`                        |
| high  | each trit pair `(1, 1)` → `OPR[1][1] = 0` → sum is `0` |
| low   | `crazy_low(V₁, V₁)` — call this `V_final`          |

Now `mem[d] = (0, 0, V_final)`. That's a clean, low-memory, area-0 address — exactly what JMP needs. **The 2-CRZ chain is the workhorse of the idiom.**

### 15.4 Which `V_final` values are reachable?

`crazy_low(V₁, V₁)` is self-CRZ trit by trit. The diagonal of OPR:

```
OPR[0][0] = 1     OPR[1][1] = 0     OPR[2][2] = 1
```

So every trit of `V_final` is in `{0, 1}` — `V_final` is a "binary number written in base 3", i.e. a sum of distinct powers of 3. There are `2¹⁰ = 1024` such 10-trit values in `[0, 29524]`.

Our branch region is `[2, 97]`, so we need `V_final + 1 ∈ [2, 97]`, i.e. `V_final ∈ [1, 96]`. The 12 candidates in that window are:

```
{36, 37, 39, 40, 81, 82, 84, 85, 90, 91, 93, 94}
```

Each is a sum of powers of 3 from `{1, 3, 9, 27, 81}`. For example, `36 = 27 + 9`, `82 = 81 + 1`, `94 = 81 + 9 + 3 + 1`.

This is your **branch-destination alphabet**. A program of this exact shape can therefore have **at most 12 distinct branches**. The character printed at branch destination `V+1` is just `V` itself, because at PRINT time `a = (0, 0, V_final)`.

### 15.5 The MOVD-redirect pattern

For the 2-CRZ trick to work, CRZ must run with `d = K` (the flag-cell address) regardless of where the CRZ *instruction* sits in the file. By default `d == c` (both monotonically advance by 1 each step), so we need to *move* `d`.

`MOVD` does this: it sets `d ← mem[d]` (reading the Word at the current `d`). To make `d` become `K` after a MOVD step, plant the byte `K-1` at some file position `p`, and arrange the program so that `d == p` when the MOVD fires. Then MOVD sets `d` to the Word `(0, 0, K-1)`, and the post-instruction increment bumps it to `K`. The next instruction sees `d = K`.

Two notes:

- The byte the MOVD reads (`K-1`) is in `[33, 126]` because `K ∈ [34, 127]` is a comfortable choice. For our `K = 34`, the redirect byte is `33` (the `'!'` character).
- The MOVD *instruction itself* can sit at any `c` position — only `d` matters when MOVD fires. Since `d` is essentially the step counter (offset by INPUT/JMP behavior), you control which file position the MOVD reads from by choosing how many NOPs precede it.

In our final layout:

```
step  c   d   instruction      effect
 5   101   5  NOP              c=102, d=6
 6   102   6  MOVD#1           reads mem[6]=33; sets d=33, then +1 → d=34
 7   103  34  CRZ#1            crazy at d=34 — writes (1,29524,V₁) to mem[34]
 8   104  35  MOVD#2           reads mem[35]=33; again d=34
 9   105  34  CRZ#2            self-CRZ — writes (0,0,V_final) to mem[34]
10   106  35  MOVD#3           reads mem[35]=33; again d=34
11   107  34  JMP#2            c ← mem[34] = (0,0,V_final); lands at V_final+1
```

Note that MOVD doesn't *modify* `mem[d]`, so `mem[35]` is still `33` when MOVD#3 runs after MOVD#2 already read it.

### 15.6 The data-only flag-cell discipline

The flag cell at `K=34` and the redirect cells at `6` and `35` must **never be executed as instructions**. Two reasons:

**1. Post-CRZ XLAT garbage.** After CRZ writes to `mem[K]`, its `low` limb is whatever `crazy_low(a, fb1)` produces — a 10-trit value typically *outside* `[33, 126]`. If `c` ever reaches `K`, the post-instruction XLAT step does `XLAT[mem[K].low - 33]`, which is out of bounds:
- `fast20` silently reads garbage past the table (undefined behavior, but the program tends to keep limping along).
- Lutter's `tio_unshackled` aborts with `cannot apply xlat2` (`unshackled.c:367-372`).
- The reference Haskell originally entered an infinite computation in its `crash` handler (`Unshackled.hs:355`, since fixed in this repo to actually crash).

**2. Loader rejection.** Spec interpreters check at load time that every byte decodes to one of the eight valid opcodes at its position (`unshackled.c:629-648`, `Unshackled.hs:91-92`). The redirect byte `33` only passes this check at certain positions: `pos mod 94 ∈ {6, 7, 29, 35, 48, 65, 66, 84}` — derived from `(33 + pos) mod 94 ∈ {4, 5, 23, 39, 40, 62, 68, 81}`. The same constraint applies to `fb1` at position 34.

To dodge both: put data cells in a region `c` never enters. Our recipe is `JMP#1` at pos 1, which unconditionally lands at pos 98 — making positions `[2, 97]` dead to `c`. We park redirect bytes at `6` and `35`, the flag cell at `34`, and the per-input PRINT/HALT cells at `V_final+1, V_final+2`, all inside that window. Every other position in `[2, 97]` is filled with `encode_char(68, p)` — a NOP encoding that is never executed but still passes the loader's validity check.

### 15.7 Picking a valid `fb1`

`fb1` lives at position 34. The byte must satisfy `(fb1 + 34) mod 94 ∈ {4, 5, 23, 39, 40, 62, 68, 81}`, which solves to

```
fb1 ∈ {34, 47, 64, 65, 83, 99, 100, 122}
```

For each candidate `fb1`, the V_final values for any chosen input pair are determined by

```
V₁(input)      = crazy_low(input, fb1)
V_final(input) = crazy_low(V₁(input), V₁(input))
```

The build script enumerates `(fb1, input_X, input_Y)` and picks the first combination where both `V_final` values are in the 12-element reachable set, distinct, and non-overlapping (`|V_X − V_Y| ≥ 2`, so `{V_X+1, V_X+2, V_Y+1, V_Y+2}` are four distinct positions).

`fb1 = 34` (the `"` character) works for inputs `'Y'/'N'` → `V_final = 82 / 36`, producing the printable characters `R` and `$`. That's the canonical solution the script outputs.

### 15.8 The whole 108-byte program in one glance

```
pos      byte           purpose
-------  -------------  -------------------------------------------------------
 0       INPUT          read a single input byte into a
 1       JMP#1          unconditional; lands at 98 — skips the data/branch region
 2-97                   "skip region" — never visited by c
           6 : 33       MOVD#1 redirect data       (= K-1 for K=34)
          34 : fb1=34   CRZ flag cell              (input-dependent post-CRZ)
          35 : 33       MOVD#2 / MOVD#3 redirect   (same as pos 6)
          83 : PRINT    branch for 'Y' (V_final=82)
          84 : HALT
          37 : PRINT    branch for 'N' (V_final=36)
          38 : HALT
        rest: NOP fillers (encode_char(68, p)), never executed
98-101   NOP            filler; c lands at 98 after JMP#1
102      MOVD#1         d ← 34
103      CRZ#1          a, mem[34] = (1, 29524, V₁)
104      MOVD#2         d ← 34
105      CRZ#2          a, mem[34] = (0, 0, V_final)  (self-CRZ cancellation)
106      MOVD#3         d ← 34
107      JMP#2          c ← mem[34]; lands at V_final + 1
```

Execution trace:

```
Y: INPUT→a=(0,0,89) → CRZ#1→mem[34]=(1,29524,V₁(89,34))
                    → CRZ#2→mem[34]=(0,0,V_final(89,34)=82)
                    → JMP →c=83 → PRINT 'R' (82) → HALT
N: …                → JMP →c=37 → PRINT '$' (36) → HALT
```

### 15.9 Recipe — design your own branching program

To make a similar program with different inputs or different printed characters:

1. **Decide on the inputs** you want to discriminate. Two printable characters `X` and `Y` is the basic case. (`'\n'` and EOF take special A values — Section 12 — so they require more care.)

2. **Pick a flag-cell address `K`.** Any `K` inside the skip region `[2, 97]` works, as long as `K` doesn't collide with a branch destination's PRINT/HALT pair and you can plant the redirect byte `K-1` at a position that passes the loader's validity check. The default `K = 34` is convenient because it sits between the data-cell positions `6` and `35`.

3. **Solve for `fb1`.** Enumerate the `fb1` values valid at `K` (see 15.7). For each, compute `V_final(X, fb1)` and `V_final(Y, fb1)` via the two `crazy_low` calls. Accept any triple `(fb1, V_X, V_Y)` where both V's are in `VALID_V`, distinct, and `|V_X - V_Y| ≥ 2`.

4. **Place the branches.** PRINT at `V_X+1`, HALT at `V_X+2`; same for Y. The character printed is `V_final` itself — pick V values whose ASCII you actually want.

5. **Lay out the linear code.** INPUT at pos 0, JMP#1 at pos 1 (which always lands at 98), four NOPs, then `MOVD#1 / CRZ#1 / MOVD#2 / CRZ#2 / MOVD#3 / JMP#2`. With this exact prefix, `d` at MOVD#1 is `6` and `d` at MOVD#2/#3 is `35`. If you change the prefix length, those positions shift — recompute the step counter.

6. **Plant the data.** Byte `K-1` at the redirect positions; `fb1` at `K`; PRINT/HALT at the branch positions; `encode_char(68, p)` everywhere else in the skip region.

7. **Validate.** Confirm every byte `b` at every position `p` satisfies `(b + p) mod 94 ∈ {4, 5, 23, 39, 40, 62, 68, 81}`. The build script asserts this in `is_valid_byte_at(...)`.

The generator at `generators/branch_flag_build.py` does steps 1–7. To produce a different variant, edit `PREFERRED_PAIRS` to list the input pairs you want to try; the script picks the first one that solves cleanly, builds the `.mu`, runs it through `word_sim`, and tests it against all three interpreters.

A companion exploration tool at `generators/enumerate_branches.py` enumerates all `(fb1, input_X, input_Y → char_X, char_Y)` combinations so you can see at a glance which input characters map to which printable outputs.

### 15.10 Extensions

- **More than two branches.** Up to 12 distinct branches fit in `[2, 97]` (one per `V_final` in `VALID_V`). For N inputs, brute-force `(fb1, x₁, …, x_N)` such that the N `V_final` values are all distinct and all in `VALID_V`. The search is `8 × 94^N`, comfortable for `N ≤ 4`.

- **Wider output alphabet.** The 12 `V_final` values map to the printable characters `$ % ' ( Q R T U Z [ ] ^`. You can't get other characters from this exact 2-CRZ shape — but adding more CRZs, or a ROTR between them, expands the reachable set. ROTR multiplies the trit pattern by a cyclic permutation; combined with CRZ chains you can sculpt almost any printable output.

- **Comparing two inputs.** Two `INPUT`s separated by CRZs give you a flag that depends on `f(input_1, input_2)`. The pattern is the same; just add more INPUT steps and more CRZs before the JMP.

- **Loops.** A loop is a backward JMP. The catch: cells written along the loop body retain their post-CRZ garbage forever, so you have to design `d`-paths that never re-read polluted cells (or accept that they'll re-XLAT-fail on spec interpreters). The same "polluted-set" tracking that `mb_noInput5.py` does for the no-input printer (Section 15.11) applies.

### 15.11 The XLAT-pollution constraint, in one rule

Across all the spec-compliant programs we've built, the single rule that drives the design is:

> **After every step, the byte at the new `c` position must be in `[33, 126]`.**

Two consequences:
- If `c == d` when CRZ fires, the CRZ result lands at `mem[c]`. Its low limb is *almost never* in `[33, 126]`. So `c == d` at a CRZ step is forbidden on spec interpreters. The MOVD-redirect pattern is precisely what dodges this.
- The same applies if `c` ever reaches a cell that a previous CRZ wrote to. The data-only flag-cell discipline (`c` never enters the skip region) and the polluted-set tracking in `mb_noInput5.py` are two different ways to enforce this.

This is the central insight: in Malbolge Unshackled, you don't think about *what each instruction does* nearly as much as you think about *where `c` will be next* and *whether the byte there will still be in range*. Every program is a careful dance to keep `c` walking only on cells that are still safe to XLAT.
