#!/bin/bash
# gnc.json v3 re-baseline (lead request 2026-10-12): interface set iface_v3 = hub mechanical.json v2 + combustion.json v2.x
# (+ its throttle map) + electronics.json, pinned by MANIFEST.sha256. Stage A answers the lead (P, TWD, liftoff mass);
# stage B adds the actuator case limits, the combustion OI cases, the analysis and the CSI on the new stiffness.
# Comparisons: v2 -> v3 (total change) and v3a -> v3 (mechanical.json v2 only; v3a = combustion v2.1 on mechanical v1,
# run_v3a_attrib.sh). The linkage-as-published cases (nmech) of v3 pair with the explicit n 4.8 cases of v2 / v3a.
set -u
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
S=/home/claude/work/space
L=$S/logs
PY="nice -n 10 /opt/engine-venv/bin/python"
export GNC_IFACE=$S/iface_v3 GNC_SUFFIX=v3 GNC_OUT=$S/out/m3 GNC_RES=$S/out/results_v3 GNC_VEH_OUT=$S/out/vehicle_v3 \
       GNC_VEH_TAG=v3d GNC_DC_OUT=$S/out/duty_cycles_v3
MAP="AD_prov_act_nmech_6V6_sagD=AD_prov_act_n48_6V6_sagD,AD_prov_act_nmech_6V6_J1_sagD=AD_prov_act_n48_6V6_J1_sagD"
mkdir -p $S/out/m3 $S/out/results_v3 $S/out/vehicle_v3 $S/out/duty_cycles_v3
cd $S/gnc
LOG=$L/v3_rebaseline.log
echo "start $(date -u +%FT%TZ)" > $LOG
(cd $GNC_IFACE && sha256sum -c MANIFEST.sha256) >> $LOG 2>&1
# ---- stage A
GNC_CASES=AD_fins_f20,AD_prov_2kg,AD_prov_act_nmech_6V6_sagD,AD_prov_act_n48_6V6_sagD \
  $PY scripts/m2_mc6.py > $L/m3_mc6_a.log 2>&1; echo "mc6_a $? $(date -u +%FT%TZ)" >> $LOG
$PY scripts/m2_vehicle.py > $L/m3_vehicle.log 2>&1; echo "vehicle $? $(date -u +%FT%TZ)" >> $LOG
GNC_CASE_MAP=$MAP GNC_OUT_OLD=$S/out/m2 GNC_SUFFIX_OLD=v2 GNC_VEH_OLD=$S/out/vehicle GNC_VEH_TAG_OLD=v3c \
  $PY scripts/m2_rebaseline_compare.py > $L/m3_compare_a.log 2>&1; echo "compare_a $? $(date -u +%FT%TZ)" >> $LOG
GNC_CASE_MAP=$MAP GNC_OUT_OLD=$S/out/m3a GNC_SUFFIX_OLD=v3a GNC_VEH_OLD=$S/out/vehicle_v3a GNC_VEH_TAG_OLD=v3c2 \
  $PY scripts/m2_rebaseline_compare.py > $L/m3_compare_a_mech.log 2>&1; echo "compare_a_mech $? $(date -u +%FT%TZ)" >> $LOG
echo "STAGE_A_DONE $(date -u +%FT%TZ)" >> $LOG
# ---- stage B
GNC_APPEND=1 GNC_CASES=AD_prov_act_nmech_6V6_J1_sagD,AD_prov_plant2,AF_prov_2kg,B_prov_2kg_h100,B_prov_2kg_h50 \
  $PY scripts/m2_mc6.py > $L/m3_mc6_b.log 2>&1; echo "mc6_b $? $(date -u +%FT%TZ)" >> $LOG
$PY scripts/m2_actuator_study.py > $L/m3_actuator_study.log 2>&1; echo "study $? $(date -u +%FT%TZ)" >> $LOG
$PY scripts/m2_analysis.py > $L/m3_analysis.log 2>&1; echo "analysis $? $(date -u +%FT%TZ)" >> $LOG
GNC_CSI_TAG=v3 $PY scripts/m2_csi.py > $L/m3_csi.log 2>&1; echo "csi $? $(date -u +%FT%TZ)" >> $LOG
GNC_CSI_JINT=1e-3 GNC_CSI_TAG=v3_J1 $PY scripts/m2_csi.py > $L/m3_csi_J1.log 2>&1; echo "csi_J1 $? $(date -u +%FT%TZ)" >> $LOG
GNC_CASE_MAP=$MAP GNC_OUT_OLD=$S/out/m2 GNC_SUFFIX_OLD=v2 GNC_VEH_OLD=$S/out/vehicle GNC_VEH_TAG_OLD=v3c \
  $PY scripts/m2_rebaseline_compare.py > $L/m3_compare_b.log 2>&1; echo "compare_b $? $(date -u +%FT%TZ)" >> $LOG
GNC_CASE_MAP=$MAP GNC_OUT_OLD=$S/out/m3a GNC_SUFFIX_OLD=v3a GNC_VEH_OLD=$S/out/vehicle_v3a GNC_VEH_TAG_OLD=v3c2 \
  $PY scripts/m2_rebaseline_compare.py > $L/m3_compare_b_mech.log 2>&1; echo "compare_b_mech $? $(date -u +%FT%TZ)" >> $LOG
echo "end $(date -u +%FT%TZ)" >> $LOG
