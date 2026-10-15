#!/bin/bash
# m2_purge_bleed v1.2: 1.0 mm (31.3 g/s) purge / stuck-open arms with a balanced vent + both refs (identity), own folder
cd /home/claude/work/space/gnc_dev28
export NUMBA_NUM_THREADS=1 GNC_IFACE=/home/claude/work/space/iface_v3c GNC_ACT_RATE=/home/claude/work/space/iface_v3c/actuator_rate_check_v2.json
export GNC_PB_OUT=/home/claude/work/space/out/purge_bleed_1mm
export GNC_PB_ARMS='A1|ref,A1|PS10_nojet,A1|S313_0_nojet,A1|S313_1_nojet,B1|ref,B1|B313_0_nojet,B1|B313_1_nojet'
mkdir -p $GNC_PB_OUT
GNC_PB_PARTS=mc GNC_PB_SPLIT=0/2 nice -n 10 /opt/engine-venv/bin/python scripts/m2_purge_bleed.py > /home/claude/work/space/logs/pb1mm_s0.log 2>&1 &
GNC_PB_PARTS=mc GNC_PB_SPLIT=1/2 nice -n 10 /opt/engine-venv/bin/python scripts/m2_purge_bleed.py > /home/claude/work/space/logs/pb1mm_s1.log 2>&1 &
wait
GNC_PB_PARTS=eval nice -n 10 /opt/engine-venv/bin/python scripts/m2_purge_bleed.py > /home/claude/work/space/logs/pb1mm_eval.log 2>&1
echo "pb 1mm done $(date +%T)" >> /home/claude/work/space/logs/pb1mm_eval.log
