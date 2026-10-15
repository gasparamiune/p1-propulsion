#!/bin/bash
# RG-01 start-transient re-fly (sim6 v2.8-dev amendment S): 6 arms x 2 bases, 2 processes, then eval
cd /home/claude/work/space/gnc_dev28
export NUMBA_NUM_THREADS=1 GNC_IFACE=/home/claude/work/space/iface_v3c GNC_ACT_RATE=/home/claude/work/space/iface_v3c/actuator_rate_check_v2.json
GNC_ST_PARTS=mc GNC_ST_SPLIT=0/2 nice -n 10 /opt/engine-venv/bin/python scripts/m2_start_transient.py > /home/claude/work/space/logs/st_s0.log 2>&1 &
GNC_ST_PARTS=mc GNC_ST_SPLIT=1/2 nice -n 10 /opt/engine-venv/bin/python scripts/m2_start_transient.py > /home/claude/work/space/logs/st_s1.log 2>&1 &
wait
GNC_ST_PARTS=eval nice -n 10 /opt/engine-venv/bin/python scripts/m2_start_transient.py > /home/claude/work/space/logs/st_eval.log 2>&1
echo "start transient done $(date +%T)" >> /home/claude/work/space/logs/st_eval.log
