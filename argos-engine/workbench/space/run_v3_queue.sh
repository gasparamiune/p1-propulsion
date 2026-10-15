#!/bin/bash
# GNC v3 priority queue (2026-10-12, one core, nice 10). Order: (1) NC-closed relight MC (lead request 22:18Z) + MECO eval,
# (2) ENG-07d rocking-mode target (ftarget) + breakdown, (3) ENG-07d FEA-stiffness 6-DOF MC + eval, (4) anti-windup MC
# + ctrlfix eval, (5) ENG-07d time-domain flights, (6) A-F / B profile cases + MECO eval, (7) v2.6 tests, bit-identity
# check, nominal MECO flights. Each step logs "step <name> <exit> <time>" to logs/v3_queue.log.
set -u
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
S=/home/claude/work/space
PY="nice -n 10 /opt/engine-venv/bin/python"
export GNC_IFACE=$S/iface_v3b GNC_ACT_RATE=$S/iface_v3b/actuator_rate_check_v2.json
LOG=$S/logs/v3_queue.log
cd $S/gnc_dev
echo "start $(date -u +%FT%TZ)" > $LOG
step() {  # step <name> <command...>
  local name=$1; shift
  echo "== $name $(date -u +%T)" >> $LOG
  "$@" 2>&1 | grep --line-buffered -v "RuntimeWarning\|y = y \* x" >> $LOG
  echo "step $name ${PIPESTATUS[0]} $(date -u +%FT%TZ)" >> $LOG
}
# (1) relight with the NC valve closed through the coast
step meco_nc env GNC_MR_CASES=mr_td72_ncmin,mr_td72_nc,mr_td72_nc_unplanned,mr_td72_nc_m10,mr_td72_nc_m20,mr_td72_nc_m30,mr_fsw_J1.6,mr_fsw_J1.6_nc,mr_f125_rs20_nc $PY scripts/m2_meco_mc.py
step meco_eval1 $PY scripts/m2_meco_eval.py
# (2) ENG-07d: rocking-mode frequency target per damping and filter, then the per-corner breakdown
step csi_ftarget env GNC_OUT=$S/out/csi_v3 GNC_CSI_TAG=fea GNC_CSI_PART=ftarget $PY scripts/m2_csi_v3.py
step csi_breakdown env GNC_OUT=$S/out/csi_v3 GNC_CSI_TAG=fea GNC_CSI_NOTCH="1,-12,0.85,1,1.15" $PY scripts/m2_csi_v3_breakdown.py
# (3) ENG-07d in the 6-DOF MC on the FEA stiffness envelope
step fea_mc $PY scripts/m2_csi_v3_mc.py
step fea_mc_eval $PY scripts/m2_csi_v3_mc_eval.py
# (4) encoder anti-windup re-init in the MC (single-run crash on run 323 is the evidence so far)
step aw_mc env GNC_CF_CASES=cf_J2.7_aw2,cf_J2.7_acc2000_aw2 $PY scripts/m2_ctrlfix_mc.py
step ctrlfix_eval $PY scripts/m2_ctrlfix_eval.py
# (5) ENG-07d nonlinear time-domain flights (v2.5 / v2.6 flight software, J 0 / 1.6e-3, ECU notch Q1 -12 dB)
step csi_td env GNC_OUT=$S/out/csi_v3 GNC_CSI_TAG=fea $PY scripts/m2_csi_v3_td.py
# (6) other profiles on the v2.6 flight software
step meco_af_b env GNC_MR_CASES=mr_AF,mr_AF_fix,mr_AF_fix_td72,mr_AF_fix_td72_nc,mr_B,mr_B_fix,mr_B_fix_toff $PY scripts/m2_meco_mc.py
step meco_eval2 $PY scripts/m2_meco_eval.py
# (7) verification
step v26_tests env GNC_OUT=$S/out/v26_checks $PY scripts/m2_v26_tests.py
step bitcheck env GNC_IFACE=$S/iface_v3a GNC_ACT_RATE= $PY scripts/m2_bitcheck_v26.py
step meco_nominal env GNC_OUT=$S/out/meco GNC_SUFFIX=mr $PY scripts/m2_meco_nominal.py
echo "end $(date -u +%FT%TZ)" >> $LOG
