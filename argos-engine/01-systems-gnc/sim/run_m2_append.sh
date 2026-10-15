#!/bin/bash
# M2 append run (sim6 v2.3): comparator cases + lead baseline, then verification rerun (G0 coast fix)
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export GNC_IFACE=/home/claude/work/shared-fallback/engine/interfaces
export GNC_SUFFIX=v2
export GNC_OUT=/home/claude/work/space/out/m2
export GNC_DC_OUT=/home/claude/work/space/out/duty_cycles_v2
export GNC_RES=/home/claude/work/space/out/results_v2
export GNC_VEH_OUT=/home/claude/work/space/out/vehicle
cd /home/claude/work/space/gnc
PY=/opt/engine-venv/bin/python
L=/home/claude/work/space/logs
echo "start $(date -u +%FT%TZ)"
GNC_APPEND=1 GNC_CASES=AD_fins_f20_rate80,AD_prov_2kg,AD_fins_f20_norcs_r03,AD_fins_f20_norcs_r04,AD_fins_f20_bw8,AD_fins_f20_bw6,AD_fins_f20_slowPc,AD_fins_f20_q2 \
  nice -n 10 $PY scripts/m2_mc6.py > $L/m2_mc6_append_v2.log 2>&1; echo "mc6_append done $? $(date -u +%FT%TZ)"
nice -n 10 $PY scripts/m2_verify6.py > $L/m2_verify6_v2.log 2>&1; echo "verify6 done $? $(date -u +%FT%TZ)"
echo "end $(date -u +%FT%TZ)"
