#!/bin/bash
# REV-ELEC-4 chain 6: the v2.11 record command r2v2 (S17v2) on the rebuilt v2.12 binary, re-run after the shorter steps, with a wall-time
# cap of 35 min (timeout, own process). Waits for chain5 to end. nice 15, single thread.
L=/dev/shm/rev_elec4/run/chain6_log.txt
st() { echo "$1 rc $2 $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L; }
echo "wait $(date -u +%Y-%m-%dT%H:%M:%SZ)" > $L
while ! grep -q '^end ' /dev/shm/rev_elec4/run/chain5_log.txt; do sleep 15; done
echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L
B=/dev/shm/rev_elec4/fw/build
R=/dev/shm/rev_elec4/run/rec
timeout 2100 nice -n 15 $B/sil r2v2 $R > $R/S17v2_log.txt 2>&1; st r2v2 $?
echo "end $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L
