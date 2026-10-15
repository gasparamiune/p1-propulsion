#!/bin/bash
# Batch 4: (1) J_int refinement (J 1.5e-3, 5e-3; n 4.8, 6.6 V, as-drawn chain) + actuator study re-run, v1 interface snapshot;
# (2) gnc_v2.json rebuilt with the v2.4 code and the pre-actuator summary, interface record = the v1 snapshot actually flown;
# (3) combustion-v2 reader promoted gnc_dev -> gnc, then the v2.5 bit check (v1 snapshot) and the engine v2-map check.
set -u
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
S=/home/claude/work/space
L=$S/logs
PY="nice -n 10 /opt/engine-venv/bin/python"
SNAPI=$S/gnc/data/iface_snapshot
echo "start $(date -u +%FT%TZ)" > $L/batch4.log
cd $S/gnc
C=AD_prov_act_n48_6V6_J1.5_sagD,AD_prov_act_n48_6V6_J5_sagD
GNC_IFACE=$SNAPI GNC_SUFFIX=v2 GNC_OUT=$S/out/m2 GNC_RES=$S/out/results_v2 GNC_APPEND=1 GNC_CASES=$C $PY scripts/m2_mc6.py > $L/m2_mc6_act4_v2.log 2>&1; echo "mc6 $? $(date -u +%FT%TZ)" >> $L/batch4.log
GNC_IFACE=$SNAPI GNC_SUFFIX=v2 GNC_OUT=$S/out/m2 GNC_RES=$S/out/results_v2 $PY scripts/m2_actuator_study.py > $L/m2_actuator_study_v2c.log 2>&1; echo "study $? $(date -u +%FT%TZ)" >> $L/batch4.log
# (2) gnc_v2.json rebuild (temp package = v2.4 code)
T=$S/tmp_v24pub
cd $T/gnc
GNC_IFACE=$SNAPI GNC_OUT=$T/out/m2 GNC_RES=$S/out/results_v2 GNC_DC_OUT=$S/out/duty_cycles_v2 GNC_VEH_OUT=$S/out/vehicle \
  $PY scripts/m2_gnc_json.py > $L/m2_gnc_json_v2_rebuild.log 2>&1; echo "gnc_json_v2_rebuild $? $(date -u +%FT%TZ)" >> $L/batch4.log
# (3) promote the combustion-v2 reader
cd $S
cp gnc/gncsim/engine_v2.py $S/engine_v2_v2.5_final.py; cp gnc/gncsim/run6.py $S/run6_v2.5_final.py
cp gnc_dev/gncsim/engine_v2.py gnc/gncsim/engine_v2.py
cp gnc_dev/gncsim/run6.py gnc/gncsim/run6.py
cp gnc_dev/scripts/m2_engine_v2_check.py gnc/scripts/m2_engine_v2_check.py
find gnc -name '__pycache__' -type d -prune -exec rm -rf {} +
mkdir -p $S/out/check_comb2
cd $S/gnc
GNC_IFACE=$SNAPI GNC_OUT=$S/out/m2 GNC_RES=$S/out/check_comb2 $PY scripts/m2_bitcheck_v25.py > $L/m2_bitcheck_comb2.log 2>&1; echo "bitcheck_comb2 $? $(date -u +%FT%TZ)" >> $L/batch4.log
GNC_IFACE=$S/iface_v3 GNC_IFACE_V1=$SNAPI GNC_RES=$S/out/check_comb2 $PY scripts/m2_engine_v2_check.py > $L/m2_engine_v2_check.log 2>&1; echo "engine_v2_check $? $(date -u +%FT%TZ)" >> $L/batch4.log
echo "end $(date -u +%FT%TZ)" >> $L/batch4.log
