#!/bin/bash
# pre-scheduled purge cost in the A1 reserve with the decided release rule (m2_purge_cost v1): 3 arms x 2 bases, 2 processes, then eval
cd /home/claude/work/space/gnc_dev28
export NUMBA_NUM_THREADS=1 GNC_IFACE=/home/claude/work/space/iface_v3c GNC_ACT_RATE=/home/claude/work/space/iface_v3c/actuator_rate_check_v2.json
GNC_PCOST_PARTS=mc GNC_PCOST_SPLIT=0/2 nice -n 10 /opt/engine-venv/bin/python scripts/m2_purge_cost.py > /home/claude/work/space/logs/pc_s0.log 2>&1 &
GNC_PCOST_PARTS=mc GNC_PCOST_SPLIT=1/2 nice -n 10 /opt/engine-venv/bin/python scripts/m2_purge_cost.py > /home/claude/work/space/logs/pc_s1.log 2>&1 &
wait
GNC_PCOST_PARTS=eval nice -n 10 /opt/engine-venv/bin/python scripts/m2_purge_cost.py > /home/claude/work/space/logs/pc_eval.log 2>&1
echo "purge cost done $(date +%T)" >> /home/claude/work/space/logs/pc_eval.log
