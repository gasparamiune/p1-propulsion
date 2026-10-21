#!/bin/sh
# v2.13 after the SIL chain (sequential, nice 15): S12 bleed on the standard build (E4-05 (9): S12_bleed.json with the FINAL mass basis;
# S12 regression against v2.12), then the two unit-test builds on the final sources
O=/dev/shm/elec_v213/out
date -u +%Y-%m-%dT%H:%M:%SZ > $O/post.start
nice -n 15 /dev/shm/elec_v213/build/sil bleed $O/s12 > $O/s12/S12_run_log.txt 2>&1; echo "exit $?" >> $O/s12/S12_run_log.txt
date -u +%Y-%m-%dT%H:%M:%SZ > $O/s12.done
sh /dev/shm/elec_v213/tools/build.sh tc tcn
date -u +%Y-%m-%dT%H:%M:%SZ > $O/post.done
