#!/bin/bash
# After the CSI v3 chain: A-F / B MECO-rule cases + eval, then the CSI time-domain cross-check. One core.
set -u
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
S=/home/claude/work/space
until grep -q "^end" $S/logs/csi_v3.log 2>/dev/null; do sleep 5; done
export GNC_IFACE=$S/iface_v3b GNC_ACT_RATE=$S/iface_v3b/actuator_rate_check_v2.json
LOG=$S/logs/after_csi.log
cd $S/gnc_dev
echo "start $(date -u +%FT%TZ)" > $LOG
GNC_OUT=$S/out/meco GNC_SUFFIX=mr GNC_MR_CASES=mr_AF,mr_AF_fix,mr_AF_fix_td72,mr_B,mr_B_fix,mr_B_fix_toff \
  nice -n 10 /opt/engine-venv/bin/python scripts/m2_meco_mc.py >> $S/logs/meco.log 2>&1; echo "meco2 $? $(date -u +%FT%TZ)" >> $LOG
GNC_OUT=$S/out/meco GNC_SUFFIX=mr nice -n 10 /opt/engine-venv/bin/python scripts/m2_meco_eval.py > $S/logs/meco_eval.log 2>&1
echo "eval $? $(date -u +%FT%TZ)" >> $LOG
GNC_OUT=$S/out/csi_v3 GNC_CSI_TAG=fea nice -n 10 /opt/engine-venv/bin/python scripts/m2_csi_v3_td.py > $S/logs/csi_v3_td.log 2>&1
echo "td $? $(date -u +%FT%TZ)" >> $LOG
echo "end $(date -u +%FT%TZ)" >> $LOG
