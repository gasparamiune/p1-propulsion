#!/bin/sh
# v2.12 SIL chain 2 (one heavy process at a time, nice 15, single thread)
B=/dev/shm/elec_v212/build; O=/dev/shm/elec_v212/sil_out
date -u +%Y-%m-%dT%H:%M:%SZ > $O/chain2.start
nice -n 15 $B/sil s13t $O > $O/S13T_run_log_bpc1_false.txt 2>&1
date -u +%Y-%m-%dT%H:%M:%SZ > $O/chain2.s13t_false.done
nice -n 15 $B/sil_bpc1 s13t $O > $O/S13T_run_log_bpc1_true.txt 2>&1
date -u +%Y-%m-%dT%H:%M:%SZ > $O/chain2.s13t_true.done
nice -n 15 $B/sil bleed $O > $O/S12_run_log.txt 2>&1
S6R_ONLY=fa1rep_max_face S6R_TRACE_DIR=$O/s6r_traces nice -n 15 $B/sil s6r $O/s6r_traces > $O/s6r_traces/S6R_maxface_run_log.txt 2>&1
nice -n 15 $B/sil trace0 $O/trace0 > $O/trace0/trace0_run_log.txt 2>&1
V212_BAND_EXTRA_PA=4.456e5 nice -n 15 $B/sil s6r $O/a8_bandhigh > $O/a8_bandhigh/S6R_bandhigh_run_log.txt 2>&1
V212_BAND_EXTRA_PA=4.456e5 nice -n 15 $B/sil rccost $O/a8_bandhigh > $O/a8_bandhigh/S6C_bandhigh_run_log.txt 2>&1
date -u +%Y-%m-%dT%H:%M:%SZ > $O/chain2.done
