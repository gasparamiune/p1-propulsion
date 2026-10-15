#!/bin/bash
# GNC run queue 1 (2026-10-13): keep at most 2 solver processes. Starts the RG-03 web-limit MC as eng07 slots free up.
cd /home/claude/work/space/gnc_dev28
ENVV="NUMBA_NUM_THREADS=1 GNC_IFACE=/home/claude/work/space/iface_v3c GNC_ACT_RATE=/home/claude/work/space/iface_v3c/actuator_rate_check_v2.json"
until [ "$(pgrep -fc 'scripts/m2_eng07_6v6.py')" -le 1 ]; do sleep 5; done
env $ENVV GNC_WEB_PARTS=check,mc GNC_WEB_SPLIT=0/2 nice -n 10 /opt/engine-venv/bin/python scripts/m2_web_limit.py > /home/claude/work/space/logs/web_limit_mc0.log 2>&1 &
until [ "$(pgrep -fc 'scripts/m2_eng07_6v6.py')" -eq 0 ]; do sleep 5; done
env $ENVV GNC_WEB_PARTS=mc GNC_WEB_SPLIT=1/2 nice -n 10 /opt/engine-venv/bin/python scripts/m2_web_limit.py > /home/claude/work/space/logs/web_limit_mc1.log 2>&1 &
wait
echo done
