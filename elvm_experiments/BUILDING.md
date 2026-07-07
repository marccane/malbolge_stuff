# Building the toolchain (LMFAO, ELVM, interpreters)

The `LMFAO/` and `elvm/` submodules are **pristine upstream checkouts** — no
local patches are committed. Build workarounds live here instead.

## LMFAO

```sh
cd ../LMFAO && make        # needs bison, flex, gcc; produces ./lmfao
```

## ELVM — needs a -Werror workaround on modern gcc

Upstream pins `-Werror` in `COMMONFLAGS` (Makefile line 1) and gcc ≥ 14
promotes warnings in `target/go.c` (and others) to errors. Do **not** patch
the submodule; override CFLAGS on the command line:

```sh
cd ../elvm
make out/8cc out/elc CFLAGS="-std=gnu99 -O2 -MMD -MP -Wno-missing-field-initializers"
```

(8cc builds via its own sub-Makefile and is unaffected.)

Pipeline reminder:

```sh
elvm/out/8cc -S -I elvm -Ielvm/libc -o prog.eir prog.c   # #include <stdio.h> needed for % and /
elvm/out/elc -hell prog.eir > prog.hell
LMFAO/lmfao -o prog.mu prog.hell
```

## Interpreters

See `../interpreters/INTERPRETERS.md` for which is which. Builds:

```sh
gcc -O2 -o tio_hack/fast20_steps tio_hack/fast20_steps.c   # fast20-area20 + step counter
clang -O3 -march=native <malbolge-lisp>/fast20.c            # fast20-flat19 (lisp.mb only)
```
