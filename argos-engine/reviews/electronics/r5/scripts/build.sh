#!/bin/sh
# REV-ELEC-5 rebuild of v2.13 (v2.11 base + v2.12 overlay + v2.13 overlay), make -j1, nice 15, one process; then the two unit-test suites
L=/dev/shm/rev_elec5
date -u +%Y-%m-%dT%H:%M:%SZ > $L/run/build.start
nice -n 15 make -j1 -C $L/fw build/test_core build/test_core_nohooks build/sil build/sil_bpc1 > $L/run/build_v213.log 2>&1
echo "make rc $?" >> $L/run/build_v213.log
date -u +%Y-%m-%dT%H:%M:%SZ > $L/run/build.done
mkdir -p $L/run/tc $L/run/tcn
nice -n 15 $L/fw/build/test_core $L/run/tc > $L/run/test_core_out.txt 2>&1; echo "exit $?" >> $L/run/test_core_out.txt
nice -n 15 $L/fw/build/test_core_nohooks $L/run/tcn > $L/run/test_core_nohooks_out.txt 2>&1; echo "exit $?" >> $L/run/test_core_nohooks_out.txt
date -u +%Y-%m-%dT%H:%M:%SZ > $L/run/tests.done
