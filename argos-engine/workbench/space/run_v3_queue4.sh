#!/bin/bash
# GNC v3 queue, part 4 (2026-10-12): re-baseline on mechanical.json v2 (interface set iface_v3c: combustion.json v2.3,
# mechanical.json v2, electronics.json v1) in the lead's order: (1) propellant closure, (2) mechanical.json v2 reading
# checks and the ENG-07d / wn x 0.75 Monte Carlo on mech v2, then the remaining v3b items (wn x 0.75 paired on the ctrlfix
# basis, CSI frequency target on mech v2, anti-windup) and verification. One core, nice 10.
set -u
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
S=/home/claude/work/space
PY="nice -n 10 /opt/engine-venv/bin/python"
C3="GNC_IFACE=$S/iface_v3c GNC_ACT_RATE=$S/iface_v3c/actuator_rate_check_v2.json"
B3="GNC_IFACE=$S/iface_v3b GNC_ACT_RATE=$S/iface_v3b/actuator_rate_check_v2.json"
LOG=$S/logs/v3_queue4.log
cd $S/gnc_dev
echo "start $(date -u +%FT%TZ)" > $LOG
step() {  # step <name> <command...>
  local name=$1; shift
  echo "== $name $(date -u +%T)" >> $LOG
  "$@" 2>&1 | grep --line-buffered -v "RuntimeWarning\|y = y \* x" >> $LOG
  echo "step $name ${PIPESTATUS[0]} $(date -u +%FT%TZ)" >> $LOG
}
step pc_m2 env $C3 GNC_PC_RATCHET=1 GNC_OUT=$S/out/prop_closure_m2 GNC_SUFFIX=pc2 GNC_PC_PART=all $PY scripts/m2_prop_closure.py
step mech_v2_check env $C3 GNC_IFACE_OLD=$S/iface_v3b GNC_OUT=$S/out/mech_v2_check $PY scripts/m2_mech_v2_check.py
step mechv2_mc env $C3 $PY scripts/m2_mechv2_mc.py
step wn_mc env $B3 GNC_CF_CASES=cf_J1.6_acc2000_ref40_wn4.5,cf_J1.6_acc2000_ref40_wn5 $PY scripts/m2_ctrlfix_mc.py
step csi_ftarget_m2 env $C3 GNC_OUT=$S/out/csi_v3c GNC_CSI_TAG=m2 GNC_CSI_PART=ftarget \
  GNC_CSI_F_EXTRA="lpf50_wn0.75=50,0,0,0,0.75;lpf50+notchQ1-12_mis5_wn0.75=50,1,-12,0.05,0.75;lpf50+notchQ1-12_mis15_wn0.75=50,1,-12,0.15,0.75;lpf50+notchQ2-12_mis5=50,2,-12,0.05" \
  GNC_CSI_F_VARIANTS="lpf50,lpf50+notchQ1-12_mis15,lpf50+notchQ1-12_mis5,lpf50_wn0.75,lpf50+notchQ1-12_mis15_wn0.75,lpf50+notchQ1-12_mis5_wn0.75,lpf50+notchQ2-12_mis5" \
  $PY scripts/m2_csi_v3.py
step aw_mc env $B3 GNC_CF_CASES=cf_J2.7_aw2,cf_J2.7_acc2000_aw2 $PY scripts/m2_ctrlfix_mc.py
step ctrlfix_eval env $B3 $PY scripts/m2_ctrlfix_eval.py
step v26_tests env $B3 GNC_OUT=$S/out/v26_checks $PY scripts/m2_v26_tests.py
step bitcheck env GNC_IFACE=$S/iface_v3a GNC_ACT_RATE= $PY scripts/m2_bitcheck_v26.py
step meco_nominal env $B3 GNC_OUT=$S/out/meco GNC_SUFFIX=mr $PY scripts/m2_meco_nominal.py
echo "end $(date -u +%FT%TZ)" >> $LOG
