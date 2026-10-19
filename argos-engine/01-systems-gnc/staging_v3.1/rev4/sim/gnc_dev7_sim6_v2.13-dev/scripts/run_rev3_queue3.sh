#!/bin/bash
# GNC rev3 flight queue 3 (sequential, nice 10; waits for queue 2, PID 23486). P5: RG-16 latency allowance (sim6 v2.11-dev). Kill by PID only.
LOG=/home/claude/work/space/out/rev3/logs
step() { echo "=== $(date -u +%H:%M:%S) $1" ; }
while kill -0 23486 2>/dev/null; do sleep 20; done
step "queue 2 finished"
set -a; . /home/claude/work/space/gnc_dev3/scripts/m2r3_env.sh; set +a
export GNC_IFACE_PIN=/home/claude/work/space/pins_rev3/pins_rev3.sha256
cd /home/claude/work/space/gnc_dev5/scripts
step "P5 latency allowance flights + eval"; nice -n 10 $PY m2_rev3_p5.py > $LOG/p5_latency.log 2>&1
step "P5 RG-16 windowed budget A1 / B1 + vibration sensitivity"; nice -n 10 $PY m2_rev3_rg16w.py > $LOG/p5_rg16w.log 2>&1
step "done"
