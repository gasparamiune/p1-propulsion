#!/bin/bash
# Actuator study batch 2 (sim6 v2.5 with the stall/speed split): bit-check, actuator MC cases, CSI variants, analysis.
# Interface set pinned to the v1 snapshot (mechanical.json v1, combustion.json v1 + relay) for a like-for-like comparison.
set -u
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export GNC_IFACE=/home/claude/work/space/gnc/data/iface_snapshot
export GNC_SUFFIX=v2 GNC_OUT=/home/claude/work/space/out/m2 GNC_RES=/home/claude/work/space/out/results_v2
cd /home/claude/work/space/gnc
L=/home/claude/work/space/logs
echo "start $(date -u +%FT%TZ)" > $L/act_batch2.log
nice -n 10 /opt/engine-venv/bin/python scripts/m2_bitcheck_v25.py > $L/m2_bitcheck_v25b.log 2>&1; echo "bitcheck $? $(date -u +%FT%TZ)" >> $L/act_batch2.log
C=AD_prov_act_n48_6V6_sagD,AD_prov_act_n48_6V6,AD_prov_act_n60_6V6_sagD,AD_prov_act_n60_6V6,AD_prov_act_n48_7V6,AD_prov_act_n60_7V6,AD_prov_act_n60_7V4,AD_prov_act_n48_rest8V1_sagD,AD_prov_act_n48_6V6_J2_sagD,AD_prov_act_n60_6V6_J2_sagD
C=$C,AD_prov_act_n48_6V0,AD_prov_act_n48_6V0_sagD,AD_prov_act_n48_6V6_J1_sagD,AD_prov_act_n48_6V6_J4_sagD,AD_prov_act_n60_6V6_J1_sagD,AD_prov_act_n60_6V6_J4_sagD,AD_prov_act_n48_6V6_J2
GNC_APPEND=1 GNC_CASES=$C nice -n 10 /opt/engine-venv/bin/python scripts/m2_mc6.py > $L/m2_mc6_act2_v2.log 2>&1; echo "mc6 $? $(date -u +%FT%TZ)" >> $L/act_batch2.log
GNC_CSI_N=4.8 GNC_CSI_TAG=v2_n48 nice -n 10 /opt/engine-venv/bin/python scripts/m2_csi.py > $L/m2_csi_n48.log 2>&1; echo "csi_n48 $? $(date -u +%FT%TZ)" >> $L/act_batch2.log
GNC_CSI_N=4.8 GNC_CSI_JINT=2e-3 GNC_CSI_TAG=v2_n48_J2 nice -n 10 /opt/engine-venv/bin/python scripts/m2_csi.py > $L/m2_csi_n48_J2.log 2>&1; echo "csi_n48_J2 $? $(date -u +%FT%TZ)" >> $L/act_batch2.log
GNC_CSI_JINT=2e-3 GNC_CSI_TAG=v2_n60_J2 nice -n 10 /opt/engine-venv/bin/python scripts/m2_csi.py > $L/m2_csi_n60_J2.log 2>&1; echo "csi_n60_J2 $? $(date -u +%FT%TZ)" >> $L/act_batch2.log
nice -n 10 /opt/engine-venv/bin/python scripts/m2_actuator_study.py > $L/m2_actuator_study_v2.log 2>&1; echo "study $? $(date -u +%FT%TZ)" >> $L/act_batch2.log
echo "end $(date -u +%FT%TZ)" >> $L/act_batch2.log
