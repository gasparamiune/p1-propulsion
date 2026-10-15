#!/bin/bash
# Attribution step of the gnc.json v3 re-baseline: the combustion.json v2.1 engine (published map, S230 grain, run6
# v2.5.2 S230 growth on the CAD v2 engine) flown on mechanical.json v1, i.e. the v2 vehicle with only the engine model
# changed. v2 -> v3a isolates the combustion change; v3a -> v3 (mechanical.json v2) isolates the mechanical change.
set -u
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
S=/home/claude/work/space
L=$S/logs
PY="nice -n 10 /opt/engine-venv/bin/python"
export GNC_IFACE=$S/iface_v3a GNC_SUFFIX=v3a GNC_OUT=$S/out/m3a GNC_RES=$S/out/results_v3a GNC_VEH_OUT=$S/out/vehicle_v3a \
       GNC_VEH_TAG=v3c2 GNC_DC_OUT=$S/out/duty_cycles_v3a
mkdir -p $S/out/m3a $S/out/results_v3a $S/out/vehicle_v3a
cd $S/gnc
LOG=$L/v3a_attrib.log
echo "start $(date -u +%FT%TZ)" > $LOG
(cd $GNC_IFACE && sha256sum -c MANIFEST.sha256) >> $LOG 2>&1
GNC_CASES=AD_fins_f20,AD_prov_2kg,AD_prov_act_n48_6V6_sagD,AD_prov_act_n48_6V6_J1_sagD \
  $PY scripts/m2_mc6.py > $L/m3a_mc6.log 2>&1; echo "mc6 $? $(date -u +%FT%TZ)" >> $LOG
$PY scripts/m2_vehicle.py > $L/m3a_vehicle.log 2>&1; echo "vehicle $? $(date -u +%FT%TZ)" >> $LOG
GNC_OUT_OLD=$S/out/m2 GNC_SUFFIX_OLD=v2 GNC_VEH_OLD=$S/out/vehicle GNC_VEH_TAG_OLD=v3c \
  $PY scripts/m2_rebaseline_compare.py > $L/m3a_compare.log 2>&1; echo "compare $? $(date -u +%FT%TZ)" >> $LOG
echo "end $(date -u +%FT%TZ)" >> $LOG
