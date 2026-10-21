#!/bin/sh
# REV-ELEC-5 SIL re-runs, sequential, nice 15, one process at a time, my own binaries in /dev/shm/rev_elec5/fw/build.
# Pause protocol: if R/pause.req exists between items, write R/paused and wait until pause.req is removed (so my probe never overlaps a SIL run).
B=/dev/shm/rev_elec5/fw/build; O=/dev/shm/rev_elec5/out; R=/dev/shm/rev_elec5/run
run1() { # bin scen outdir
  while [ -f $R/pause.req ]; do date -u +%Y-%m-%dT%H:%M:%SZ > $R/paused; sleep 2; done; rm -f $R/paused
  echo "$1 $2 start $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $R/chain.log
  nice -n 15 $B/$1 $2 $3 > $3/run_log_$2.txt 2>&1; rc=$?
  echo "$1 $2 done rc $rc $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $R/chain.log
}
date -u +%Y-%m-%dT%H:%M:%SZ > $R/chain.start
run1 sil a5 $O/silF
run1 sil_bpc1 a5 $O/silT
run1 sil s13f $O/silF
run1 sil_bpc1 s13f $O/silT
run1 sil s13t13ts $O/silF
run1 sil s13t13 $O/silF
run1 sil bleed $O/s12
run1 sil_bpc1 s13t13ts $O/silT
date -u +%Y-%m-%dT%H:%M:%SZ > $R/chain.done
