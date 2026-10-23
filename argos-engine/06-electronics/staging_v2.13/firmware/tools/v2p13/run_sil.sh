#!/bin/sh
# v2.13 SIL runs, sequential, nice 15, one process at a time. Arg 1: binary (sil | sil_bpc1), arg 2: out dir, then the scenario list
BIN=/dev/shm/elec_v213/build/$1; O=$2; shift 2
for S in "$@"; do
  date -u +%Y-%m-%dT%H:%M:%SZ > $O/$S.start
  nice -n 15 $BIN $S $O > $O/$S.log 2>&1; echo "exit $?" >> $O/$S.log
  date -u +%Y-%m-%dT%H:%M:%SZ > $O/$S.done
done
