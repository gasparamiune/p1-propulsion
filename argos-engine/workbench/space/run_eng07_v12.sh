#!/bin/bash
# ENG-07 v1.2: re-routed coil at EI 0.5 with a 7.4 V supply (2 arms x 2 bases), 2 processes, then eval
cd /home/claude/work/space/gnc_dev28
export NUMBA_NUM_THREADS=1 GNC_IFACE=/home/claude/work/space/iface_v3c GNC_ACT_RATE=/home/claude/work/space/iface_v3c/actuator_rate_check_v2.json
export GNC_E7_ARMS=RR74_EI05,PR74_EI05 GNC_E7_PARTS=run
GNC_E7_SPLIT=0/2 nice -n 10 /opt/engine-venv/bin/python scripts/m2_eng07_6v6.py > /home/claude/work/space/logs/eng07_v12_s0.log 2>&1 &
GNC_E7_SPLIT=1/2 nice -n 10 /opt/engine-venv/bin/python scripts/m2_eng07_6v6.py > /home/claude/work/space/logs/eng07_v12_s1.log 2>&1 &
wait
unset GNC_E7_ARMS
GNC_E7_PARTS=eval nice -n 10 /opt/engine-venv/bin/python scripts/m2_eng07_6v6.py > /home/claude/work/space/logs/eng07_v12_eval.log 2>&1
echo "eng07 v1.2 done $(date +%T)" >> /home/claude/work/space/logs/eng07_v12_s0.log
