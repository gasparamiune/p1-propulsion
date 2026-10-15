#!/bin/bash
# GNC RG-16 purge / bleed terms (fct): waits until fewer than 2 solver processes run (2-process cap), then flies the cases
cd /home/claude/work/space/gnc_dev28
while [ "$(pgrep -f '^/opt/engine-venv/bin/python scripts/m2_' | wc -l)" -ge 2 ]; do sleep 10; done
export NUMBA_NUM_THREADS=1 GNC_IFACE=/home/claude/work/space/iface_v3c GNC_ACT_RATE=/home/claude/work/space/iface_v3c/actuator_rate_check_v2.json
GNC_RG16_PARTS=fct,eval nice -n 10 /opt/engine-venv/bin/python scripts/m2_rg16_fct_terms.py > /home/claude/work/space/logs/rg16_fct.log 2>&1
echo "rg16 fct done $(date -u +%H:%M:%S)" >> /home/claude/work/space/logs/rg16_fct.log
