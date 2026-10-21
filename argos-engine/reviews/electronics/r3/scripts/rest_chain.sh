#!/bin/bash
# REV-ELEC-3 reviewer re-run chain (sequential, one process at a time, nice 15); commands as the v2.11 runmap (sil_v2p11_runmap.json)
B=/dev/shm/rev_elec3/fw/build
O=/dev/shm/rev_elec3/run/rest
L=$O/chain_log.txt
echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ)" > $L
nice -n 15 $B/sil ignrule $O/S13 "286.70,1.16,0.032213" 300 > $O/S13/S13_run_log.txt 2>&1; echo "S13 ignrule rc $? $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L
nice -n 15 $B/sil_bpc1 ignruleb $O/S13 > $O/S13/S13B_ext_bpc1_true_run_log.txt 2>&1; echo "S13B bpc1 rc $? $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L
nice -n 15 $B/sil r2hold $O/S17 > $O/S17/S17_run_log.txt 2>&1; echo "S17 r2hold rc $? $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L
nice -n 15 $B/sil startmc $O/S15 300 > $O/S15/S15_run_log.txt 2>&1; echo "S15 startmc rc $? $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L
nice -n 15 $B/sil v210 $O/S14 > $O/S14/S14_run_log.txt 2>&1; echo "S14 v210 rc $? $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L
nice -n 15 $B/sil coast206 $O/S16 > $O/S16/S16_run_log.txt 2>&1; echo "S16 coast206 rc $? $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L
nice -n 15 $B/sil probef $O/probeF > $O/probeF/probeF_run_log.txt 2>&1; echo "probeF rc $? $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L
echo "end $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L
