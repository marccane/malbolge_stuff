#!/bin/bash
# run3.sh <file.mu> [stdin_file] [timeout_secs] — run on all 3 interpreters, show outputs
MU="$1"; STDIN="${2:-/dev/null}"; TMO="${3:-60}"
I=/home/markus/projects/malbolge_stuff/interpreters
declare -A BIN=( [fast20]="$I/fast20/fast20_malbolgelisp" [tio]="$I/tio_unshackled/unshackled" [haskell]="$I/referenceImplementation/Unshackled" )
for name in fast20 tio haskell; do
  start=$(date +%s.%N)
  out=$(timeout "$TMO" "${BIN[$name]}" "$MU" < "$STDIN" 2>/home/markus/projects/malbolge_stuff/elvm_experiments/.err_$name)
  rc=$?
  dur=$(echo "$(date +%s.%N) - $start" | bc)
  printf '%-8s rc=%-3s t=%5.1fs out=%q\n' "$name" "$rc" "$dur" "$out"
  if [ -s /home/markus/projects/malbolge_stuff/elvm_experiments/.err_$name ]; then echo "         stderr: $(head -c 200 /home/markus/projects/malbolge_stuff/elvm_experiments/.err_$name)"; fi
done
