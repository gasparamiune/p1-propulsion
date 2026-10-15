#!/bin/bash
# GNC v3 queue, part 5 (2026-10-12): after the lead's OI-1 decision (option (a)).
# (1) ratchet effect on mechanical.json v2: the plan cycles A1, B1 85 m and the A2 stress case WITHOUT the ratchet on
#     the same 500 draws as pc2 (pairs against pc2); (2) re-tuned reduced-bandwidth fallback on mech v2 (m2_mechv2_mc
#     v1.1 _rt cases); (3) reference vehicle v3d on the duty-cycle A1 v3 configuration; (4) duty cycles v3 (A1 300 m,
#     B1 85 m); (5) v2.6 tests v1.3 on v3b and v3c; (6) closure evaluation v1.1. One core, nice 10.
set -u
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
S=/home/claude/work/space
PY="nice -n 10 /opt/engine-venv/bin/python"
C3="GNC_IFACE=$S/iface_v3c GNC_ACT_RATE=$S/iface_v3c/actuator_rate_check_v2.json"
B3="GNC_IFACE=$S/iface_v3b GNC_ACT_RATE=$S/iface_v3b/actuator_rate_check_v2.json"
LOG=$S/logs/v3_queue5.log
cd $S/gnc_dev
echo "start $(date -u +%FT%TZ)" > $LOG
step() {  # step <name> <command...>
  local name=$1; shift
  echo "== $name $(date -u +%T)" >> $LOG
  "$@" 2>&1 | grep --line-buffered -v "RuntimeWarning\|y = y \* x" >> $LOG
  echo "step $name ${PIPESTATUS[0]} $(date -u +%FT%TZ)" >> $LOG
}
mkdir -p $S/out/prop_closure_m2n
# the MC case list (B1 85 m) is derived from the pc2 nominal trades: seed the pc2n file with them (nominal flights are
# no-wind and identical with and without the ratchet, v2.6 test T9)
[ -f $S/out/prop_closure_m2n/prop_closure_pc2n.json ] || cp $S/out/prop_closure_m2/prop_closure_pc2.json $S/out/prop_closure_m2n/prop_closure_pc2n.json
step pc2n env $C3 GNC_PC_RATCHET=0 GNC_PC_PART=mc GNC_OUT=$S/out/prop_closure_m2n GNC_SUFFIX=pc2n \
  GNC_PC_CASES=pc_A1_2kg,pc_B1_h85_2kg,pc_A2_2kg $PY scripts/m2_prop_closure.py
step mechv2_rt env $C3 GNC_V3C_CASES=m2_J1.6_wn4.5_rt,m2_J1.6_wn4.5_rt_n15 $PY scripts/m2_mechv2_mc.py
step vehicle_v3d env $C3 GNC_VEH_OUT=$S/out/vehicle_v3d GNC_VEH_TAG=v3d GNC_SUFFIX=v3d GNC_VEH_BASE=@dc_v3_A1 GNC_VEH_M=2.0 \
  $PY scripts/m2_vehicle.py
step duty_cycles_v3 env $C3 $PY scripts/m2_duty_cycles_v3.py
step v26_tests_b env $B3 GNC_OUT=$S/out/v26_checks $PY scripts/m2_v26_tests.py
step v26_tests_c env $C3 GNC_OUT=$S/out/v26_checks_v3c $PY scripts/m2_v26_tests.py
step pc_eval env GNC_OUT=$S/out/prop_closure_eval $PY scripts/m2_prop_closure_eval.py
echo "end $(date -u +%FT%TZ)" >> $LOG
