#!/bin/sh
# REV-ELEC-4 rebuild of v2.12 (v2.11 base + v2.12 overlay), make -j1, nice 15, one process
L=/dev/shm/rev_elec4
date -u +%Y-%m-%dT%H:%M:%SZ > $L/build.start
nice -n 15 make -j1 -C $L/fw build/test_core build/test_core_nohooks build/sil build/sil_bpc1 > $L/build_v212.log 2>&1
echo "make rc $?" >> $L/build_v212.log
date -u +%Y-%m-%dT%H:%M:%SZ > $L/build.done
