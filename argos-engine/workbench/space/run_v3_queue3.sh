#!/bin/bash
# GNC v3 queue, part 3 (2026-10-12). Queue part 2 stopped at the CSI step (the pause signal used to free the core for a
# one-run test ended the background job; no output was half-written: csi_v3_fea.json unchanged since 22:48Z).
# Order: (0) governor-ratchet cases (A-F failure mode found in the propellant-closure MC), MECO evaluation, propellant
# closure with the ratchet (lead request, high priority); then the rest of part 2 (ENG-07d, anti-windup, verification).
# One core, nice 10. Each step logs "step <name> <exit>".
set -u
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
S=/home/claude/work/space
PY="nice -n 10 /opt/engine-venv/bin/python"
export GNC_IFACE=$S/iface_v3b GNC_ACT_RATE=$S/iface_v3b/actuator_rate_check_v2.json
LOG=$S/logs/v3_queue3.log
cd $S/gnc_dev
echo "start $(date -u +%FT%TZ)" > $LOG
step() {  # step <name> <command...>
  local name=$1; shift
  echo "== $name $(date -u +%T)" >> $LOG
  "$@" 2>&1 | grep --line-buffered -v "RuntimeWarning\|y = y \* x" >> $LOG
  echo "step $name ${PIPESTATUS[0]} $(date -u +%FT%TZ)" >> $LOG
}
step rat_mc env GNC_MR_CASES=mr_AF_fix_td72_nc_rat,mr_fsw_J1.6_nc_rat,mr_B_fix_toff_rat $PY scripts/m2_meco_mc.py
step meco_eval $PY scripts/m2_meco_eval.py
step pc_rat env GNC_PC_RATCHET=1 GNC_SUFFIX=pcr GNC_PC_PART=all $PY scripts/m2_prop_closure.py
step csi_ftarget2 env GNC_OUT=$S/out/csi_v3 GNC_CSI_TAG=fea GNC_CSI_PART=ftarget GNC_CSI_F_MERGE=1 \
  GNC_CSI_F_EXTRA="lpf50_wn0.75=50,0,0,0,0.75;lpf50+notchQ1-12_mis5_wn0.75=50,1,-12,0.05,0.75;lpf50+notchQ1-12_mis15_wn0.75=50,1,-12,0.15,0.75;lpf50+notchQ2-12_mis5=50,2,-12,0.05" \
  GNC_CSI_F_VARIANTS="lpf50+notchQ1-12_mis15,lpf50+notchQ1-12_mis5,lpf50_wn0.75,lpf50+notchQ1-12_mis5_wn0.75,lpf50+notchQ1-12_mis15_wn0.75,lpf50+notchQ2-12_mis5" \
  $PY scripts/m2_csi_v3.py
step wn_mc env GNC_CF_CASES=cf_J1.6_acc2000_ref40_wn4.5,cf_J1.6_acc2000_ref40_wn5 $PY scripts/m2_ctrlfix_mc.py
step fea_mc $PY scripts/m2_csi_v3_mc.py
step fea_mc_eval $PY scripts/m2_csi_v3_mc_eval.py
step csi_breakdown env GNC_OUT=$S/out/csi_v3 GNC_CSI_TAG=fea GNC_CSI_NOTCH="1,-12,0.85,1,1.15" $PY scripts/m2_csi_v3_breakdown.py
step csi_td env GNC_OUT=$S/out/csi_v3 GNC_CSI_TAG=fea $PY scripts/m2_csi_v3_td.py
step aw_mc env GNC_CF_CASES=cf_J2.7_aw2,cf_J2.7_acc2000_aw2 $PY scripts/m2_ctrlfix_mc.py
step ctrlfix_eval $PY scripts/m2_ctrlfix_eval.py
step v26_tests env GNC_OUT=$S/out/v26_checks $PY scripts/m2_v26_tests.py
step bitcheck env GNC_IFACE=$S/iface_v3a GNC_ACT_RATE= $PY scripts/m2_bitcheck_v26.py
step meco_nominal env GNC_OUT=$S/out/meco GNC_SUFFIX=mr $PY scripts/m2_meco_nominal.py
echo "end $(date -u +%FT%TZ)" >> $LOG
