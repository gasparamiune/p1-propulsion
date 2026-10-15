#!/bin/bash
# MECO throttle-down / tail-off / relight study on iface_v3b (mechanical.json v1, combustion.json v2.2, electronics v1)
set -u
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
S=/home/claude/work/space
export GNC_IFACE=$S/iface_v3b GNC_OUT=$S/out/meco GNC_SUFFIX=mr GNC_ACT_RATE=$S/iface_v3b/actuator_rate_check_v2.json
mkdir -p $GNC_OUT
LOG=$S/logs/meco.log
cd $S/gnc_dev
echo "start $(date -u +%FT%TZ)" > $LOG
(cd $GNC_IFACE && sha256sum -c MANIFEST.sha256) >> $LOG 2>&1
sha256sum /home/claude/work/shared-fallback/engine/02-combustion/data/v2/engine_S230/throttle_map_v2.csv >> $LOG
GNC_MR_CASES=${1:-AD_prov_2kg,mr_toff,mr_td72,mr_td70,mr_td72_fix,mr_td72_fix_rs20,mr_td72_tign10,mr_td72_tign20,mr_td72_tign30,mr_f125,mr_f125_td72_floorstart,mr_f125_td72_rs20,mr_J2.7_fix,mr_J2.7_fix_td72,mr_J1.6_fix_td72,mr_fins_f20,mr_fins_f20_td72_fix} \
  nice -n 10 /opt/engine-venv/bin/python scripts/m2_meco_mc.py >> $LOG 2>&1; echo "mc $? $(date -u +%FT%TZ)" >> $LOG
nice -n 10 /opt/engine-venv/bin/python scripts/m2_meco_eval.py > $S/logs/meco_eval.log 2>&1; echo "eval $? $(date -u +%FT%TZ)" >> $LOG
sha256sum /home/claude/work/shared-fallback/engine/02-combustion/data/v2/engine_S230/throttle_map_v2.csv >> $LOG
echo "end $(date -u +%FT%TZ)" >> $LOG
