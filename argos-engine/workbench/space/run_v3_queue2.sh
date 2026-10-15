#!/bin/bash
# GNC v3 queue, part 2 (2026-10-12), after the propellant-closure Monte Carlo (lead request, high priority) has finished.
# Resumes the v3 queue that was stopped at the breakdown step, and adds the ENG-07d controller option (landing attitude
# bandwidth) and the notch rigid-margin cost per mode frequency. One core, nice 10. Each step logs "step <name> <exit>".
set -u
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
S=/home/claude/work/space
PY="nice -n 10 /opt/engine-venv/bin/python"
until grep -q "^wrote" $S/logs/prop_closure_mc.log 2>/dev/null; do sleep 10; done
export GNC_IFACE=$S/iface_v3b GNC_ACT_RATE=$S/iface_v3b/actuator_rate_check_v2.json
LOG=$S/logs/v3_queue2.log
cd $S/gnc_dev
echo "start $(date -u +%FT%TZ)" > $LOG
step() {  # step <name> <command...>
  local name=$1; shift
  echo "== $name $(date -u +%T)" >> $LOG
  "$@" 2>&1 | grep --line-buffered -v "RuntimeWarning\|y = y \* x" >> $LOG
  echo "step $name ${PIPESTATUS[0]} $(date -u +%FT%TZ)" >> $LOG
}
# (0) A-F / B on the lead tank, isolating the v2.6 flight software and the NC-closed relight (propellant-closure context)
step meco_af_b env GNC_MR_CASES=mr_AF,mr_AF_nc,mr_AF_td72_nc,mr_AF_fix,mr_AF_fix_td72,mr_AF_fix_td72_nc,mr_B,mr_B_fix,mr_B_fix_toff $PY scripts/m2_meco_mc.py
step meco_eval2 $PY scripts/m2_meco_eval.py
# (1) ENG-07d: rigid PM with the notch at each mode frequency, narrower notch, landing attitude bandwidth x 0.75
step csi_ftarget2 env GNC_OUT=$S/out/csi_v3 GNC_CSI_TAG=fea GNC_CSI_PART=ftarget GNC_CSI_F_MERGE=1 \
  GNC_CSI_F_EXTRA="lpf50_wn0.75=50,0,0,0,0.75;lpf50+notchQ1-12_mis5_wn0.75=50,1,-12,0.05,0.75;lpf50+notchQ1-12_mis15_wn0.75=50,1,-12,0.15,0.75;lpf50+notchQ2-12_mis5=50,2,-12,0.05" \
  GNC_CSI_F_VARIANTS="lpf50+notchQ1-12_mis15,lpf50+notchQ1-12_mis5,lpf50_wn0.75,lpf50+notchQ1-12_mis5_wn0.75,lpf50+notchQ1-12_mis15_wn0.75,lpf50+notchQ2-12_mis5" \
  $PY scripts/m2_csi_v3.py
# (2) the controller option in the 6-DOF MC (P cost of a slower landing attitude loop), with the chosen fix, J 1.6e-3
step wn_mc env GNC_CF_CASES=cf_J1.6_acc2000_ref40_wn4.5,cf_J1.6_acc2000_ref40_wn5 $PY scripts/m2_ctrlfix_mc.py
# (3) ENG-07d FEA-stiffness 6-DOF MC + eval, breakdown, time-domain flights
step fea_mc $PY scripts/m2_csi_v3_mc.py
step fea_mc_eval $PY scripts/m2_csi_v3_mc_eval.py
step csi_breakdown env GNC_OUT=$S/out/csi_v3 GNC_CSI_TAG=fea GNC_CSI_NOTCH="1,-12,0.85,1,1.15" $PY scripts/m2_csi_v3_breakdown.py
step csi_td env GNC_OUT=$S/out/csi_v3 GNC_CSI_TAG=fea $PY scripts/m2_csi_v3_td.py
# (4) anti-windup MC + ctrlfix eval (all cf cases)
step aw_mc env GNC_CF_CASES=cf_J2.7_aw2,cf_J2.7_acc2000_aw2 $PY scripts/m2_ctrlfix_mc.py
step ctrlfix_eval $PY scripts/m2_ctrlfix_eval.py
# (6) verification
step v26_tests env GNC_OUT=$S/out/v26_checks $PY scripts/m2_v26_tests.py
step bitcheck env GNC_IFACE=$S/iface_v3a GNC_ACT_RATE= $PY scripts/m2_bitcheck_v26.py
step meco_nominal env GNC_OUT=$S/out/meco GNC_SUFFIX=mr $PY scripts/m2_meco_nominal.py
echo "end $(date -u +%FT%TZ)" >> $LOG
