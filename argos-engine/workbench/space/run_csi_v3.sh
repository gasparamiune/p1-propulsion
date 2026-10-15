#!/bin/bash
# ENG-07d CSI re-check on Mechanical's FEA stiffness (lead request 2026-10-12), v1b grid (Q 1-3, -12..-20 dB, mistune
# 0.85/1/1.15; floor-20 % set and 12.5 % stretch set; gain clamp at 62.5 N; K_struct sweep). One core.
set -u
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
S=/home/claude/work/space
export GNC_IFACE=$S/iface_v3b GNC_ACT_RATE=$S/iface_v3b/actuator_rate_check_v2.json
LOG=$S/logs/csi_v3.log
cd $S/gnc_dev
mv $S/out/csi_v3/csi_v3_fea.json $S/out/csi_v3/csi_v3_fea_run1_partial.json 2>/dev/null
echo "start $(date -u +%FT%TZ) (v1b grid; run 1 stopped after 3 notch configs: wider/deeper notches lowered the margin)" > $LOG
for part in base notch sweep; do
  GNC_OUT=$S/out/csi_v3 GNC_CSI_TAG=fea GNC_CSI_PART=$part nice -n 10 /opt/engine-venv/bin/python scripts/m2_csi_v3.py 2>&1 | grep -v "RuntimeWarning\|y = y \* x" >> $LOG
  echo "part $part $? $(date -u +%FT%TZ)" >> $LOG
done
echo "end $(date -u +%FT%TZ)" >> $LOG
