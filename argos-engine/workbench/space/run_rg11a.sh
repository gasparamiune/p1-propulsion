#!/bin/bash
# RG-11 (a) growth law: band and corner Monte Carlo, frozen vs J-proportional, 2 processes, then eval
cd /home/claude/work/space/gnc_dev28
export NUMBA_NUM_THREADS=1 GNC_IFACE=/home/claude/work/space/iface_v3c GNC_ACT_RATE=/home/claude/work/space/iface_v3c/actuator_rate_check_v2.json
GNC_RG11A_PARTS=mc GNC_RG11A_SPLIT=0/2 nice -n 10 /opt/engine-venv/bin/python scripts/m2_rg11a_growth.py > /home/claude/work/space/logs/rg11a_s0.log 2>&1 &
GNC_RG11A_PARTS=mc GNC_RG11A_SPLIT=1/2 nice -n 10 /opt/engine-venv/bin/python scripts/m2_rg11a_growth.py > /home/claude/work/space/logs/rg11a_s1.log 2>&1 &
wait
GNC_RG11A_PARTS=eval nice -n 10 /opt/engine-venv/bin/python scripts/m2_rg11a_growth.py > /home/claude/work/space/logs/rg11a_eval.log 2>&1
echo "rg11a done $(date +%T)" >> /home/claude/work/space/logs/rg11a_eval.log
