#!/bin/bash
# REV-ELEC-4 reviewer re-run chain on the rebuilt v2.12 binaries (sequential, one process at a time, nice 15, single thread)
B=/dev/shm/rev_elec4/fw/build
A=/dev/shm/rev_elec4/run/a
R=/dev/shm/rev_elec4/run/rec
L=/dev/shm/rev_elec4/run/chain1_log.txt
st() { echo "$1 rc $2 $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L; }
echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ)" > $L
# part A: the author's v2.12 runs (chain2.sh commands)
nice -n 15 $B/sil s13t $A > $A/S13T_run_log_bpc1_false.txt 2>&1; st s13t_false $?
nice -n 15 $B/sil_bpc1 s13t $A > $A/S13T_run_log_bpc1_true.txt 2>&1; st s13t_true $?
nice -n 15 $B/sil bleed $A > $A/S12_run_log.txt 2>&1; st bleed $?
S6R_ONLY=fa1rep_max_face S6R_TRACE_DIR=$A/s6r_traces nice -n 15 $B/sil s6r $A/s6r_traces > $A/s6r_traces/S6R_maxface_run_log.txt 2>&1; st s6r_maxface $?
nice -n 15 $B/sil trace0 $A/trace0 > $A/trace0/trace0_run_log.txt 2>&1; st trace0 $?
V212_BAND_EXTRA_PA=4.456e5 nice -n 15 $B/sil s6r $A/a8_bandhigh > $A/a8_bandhigh/S6R_bandhigh_run_log.txt 2>&1; st s6r_bandhigh $?
V212_BAND_EXTRA_PA=4.456e5 nice -n 15 $B/sil rccost $A/a8_bandhigh > $A/a8_bandhigh/S6C_bandhigh_run_log.txt 2>&1; st rccost_bandhigh $?
# part B: the v2.11 SIL record commands (sil_v2p11_runmap.json) on the v2.12 binaries
(time SIL_NO_CSV=1 nice -n 15 $B/sil all $R 300 > $R/sil_run_log.txt 2>&1) 2> $R/sil_all_time.txt; st all $?
nice -n 15 $B/sil ignrule $R/S13 "286.70,1.16,0.032213" 300 > $R/S13/S13_run_log.txt 2>&1; st ignrule $?
nice -n 15 $B/sil_bpc1 ignruleb $R/S13 > $R/S13/S13B_ext_bpc1_true_run_log.txt 2>&1; st ignruleb $?
nice -n 15 $B/sil r2hold $R/S17 > $R/S17/S17_run_log.txt 2>&1; st r2hold $?
nice -n 15 $B/sil startmc $R/S15 300 > $R/S15/S15_run_log.txt 2>&1; st startmc $?
nice -n 15 $B/sil v210 $R/S14 > $R/S14/S14_run_log.txt 2>&1; st v210 $?
nice -n 15 $B/sil coast206 $R/S16 > $R/S16/S16_run_log.txt 2>&1; st coast206 $?
nice -n 15 $B/sil probef $R/probeF > $R/probeF/probeF_run_log.txt 2>&1; st probef $?
nice -n 15 $B/sil s6r $R > $R/S6R_log.txt 2>&1; st s6r $?
nice -n 15 $B/sil rccost $R > $R/S6C_log.txt 2>&1; st rccost $?
nice -n 15 $B/sil r2v2 $R > $R/S17v2_log.txt 2>&1; st r2v2 $?
echo "end $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L
