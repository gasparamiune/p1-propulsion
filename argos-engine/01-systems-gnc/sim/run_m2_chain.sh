#!/bin/bash
# M2 production chain (sequential, 1 core, nice 10): MC -> verification -> CSI -> CSI time domain -> duty cycles
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export GNC_IFACE=/home/claude/work/shared-fallback/engine/interfaces
export GNC_SUFFIX=v2
export GNC_OUT=/home/claude/work/space/out/m2
export GNC_DC_OUT=/home/claude/work/space/out/duty_cycles_v2
cd /home/claude/work/space/gnc
PY=/opt/engine-venv/bin/python
echo "start $(date -u +%FT%TZ)"
nice -n 10 $PY scripts/m2_mc6.py > /home/claude/work/space/logs/m2_mc6_v2.log 2>&1; echo "mc done $? $(date -u +%FT%TZ)"
nice -n 10 $PY scripts/m2_verify6.py > /home/claude/work/space/logs/m2_verify6_v2.log 2>&1; echo "verify done $? $(date -u +%FT%TZ)"
nice -n 10 $PY scripts/m2_csi.py > /home/claude/work/space/logs/m2_csi_v2.log 2>&1; echo "csi done $? $(date -u +%FT%TZ)"
nice -n 10 $PY scripts/m2_csi_timedomain.py > /home/claude/work/space/logs/m2_csi_td_v2.log 2>&1; echo "csi td done $? $(date -u +%FT%TZ)"
nice -n 10 $PY scripts/m2_duty_cycles.py > /home/claude/work/space/logs/m2_dc_v2.log 2>&1; echo "dc done $? $(date -u +%FT%TZ)"
echo "end $(date -u +%FT%TZ)"
