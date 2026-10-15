#!/bin/bash
# GNC ENG-07 v1.1 (re-routed coil arms): waits for the release-rule process to end (2-process solver cap), then flies the arms
cd /home/claude/work/space/gnc_dev28
while kill -0 2988 2>/dev/null; do sleep 5; done
export NUMBA_NUM_THREADS=1 GNC_IFACE=/home/claude/work/space/iface_v3c GNC_ACT_RATE=/home/claude/work/space/iface_v3c/actuator_rate_check_v2.json
GNC_E7_PARTS=run GNC_E7_ARMS=RR66_EI0184,RR66_EI025,RR66_EI005,RR66_EI05,PR66_EI0184,PR66_EI025,RR74_EI0184,RR74_EI025,RRv66_EI0184,PR66_EI05 \
  nice -n 10 /opt/engine-venv/bin/python scripts/m2_eng07_6v6.py > /home/claude/work/space/logs/eng07_v11_run.log 2>&1
echo "eng07 v1.1 run done $(date -u +%H:%M:%S)" >> /home/claude/work/space/logs/eng07_v11_run.log
