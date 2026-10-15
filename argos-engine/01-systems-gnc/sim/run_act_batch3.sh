#!/bin/bash
# Actuator study batch 3 (sim6 v2.5): J_int bracket for n 4.8 on the governing supply and at 7.6 V; analysis re-run.
# Interface set pinned to the v1 snapshot (like-for-like with batches 1-2).
set -u
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export GNC_IFACE=/home/claude/work/space/gnc/data/iface_snapshot
export GNC_SUFFIX=v2 GNC_OUT=/home/claude/work/space/out/m2 GNC_RES=/home/claude/work/space/out/results_v2
cd /home/claude/work/space/gnc
L=/home/claude/work/space/logs
echo "start $(date -u +%FT%TZ)" > $L/act_batch3.log
C=AD_prov_act_n48_6V6_J6_sagD,AD_prov_act_n48_6V6_J8_sagD,AD_prov_act_n48_6V6_J12_sagD,AD_prov_act_n48_7V6_J4,AD_prov_act_n48_7V6_J8
GNC_APPEND=1 GNC_CASES=$C nice -n 10 /opt/engine-venv/bin/python scripts/m2_mc6.py > $L/m2_mc6_act3_v2.log 2>&1; echo "mc6 $? $(date -u +%FT%TZ)" >> $L/act_batch3.log
nice -n 10 /opt/engine-venv/bin/python scripts/m2_actuator_study.py > $L/m2_actuator_study_v2b.log 2>&1; echo "study $? $(date -u +%FT%TZ)" >> $L/act_batch3.log
echo "end $(date -u +%FT%TZ)" >> $L/act_batch3.log
