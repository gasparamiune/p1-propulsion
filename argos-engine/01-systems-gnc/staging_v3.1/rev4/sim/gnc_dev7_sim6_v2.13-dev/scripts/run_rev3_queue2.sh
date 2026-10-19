#!/bin/bash
# GNC rev3 flight queue 2 (sequential, nice 10, one process at a time; waits for queue 1, PID 22826). Kill by PID only.
LOG=/home/claude/work/space/out/rev3/logs
step() { echo "=== $(date -u +%H:%M:%S) $1" ; }
while kill -0 22826 2>/dev/null; do sleep 20; done
step "queue 1 finished"
set -a; . /home/claude/work/space/gnc_dev3/scripts/m2r3_env.sh; set +a
P3=/home/claude/work/space/pins_rev3/pins_rev3.sha256
cd /home/claude/work/space/gnc_dev4/scripts
step "P4s R2 v2 statistics (sim6 v2.10-dev)"; GNC_IFACE_PIN=$P3 GNC_REV3_ARMS='P4s' GNC_REV3_PARTS=mc nice -n 10 $PY m2_rev3_fly.py
step "r2v2 eval (statistics)"; GNC_IFACE_PIN=$P3 nice -n 10 $PY m2_rev3_r2v2_eval.py > $LOG/r2v2_eval_stats.log 2>&1
step "P6 P8 (sim6 v2.10-dev)"; GNC_IFACE_PIN=$P3 GNC_REV3_ARMS='P6,P8' GNC_REV3_PARTS=mc nice -n 10 $PY m2_rev3_fly.py
cd /home/claude/work/space/gnc_dev3/scripts
step "P2opt v35a (sim6 v2.9-dev)"; GNC_IFACE=/home/claude/work/space/iface_v35a GNC_IFACE_PIN=/home/claude/work/space/pins_rev3/pins_rev3_v35a.sha256 GNC_REV3_ARMS='P2opt_v35a' GNC_REV3_PARTS=mc nice -n 10 $PY m2_rev3_fly.py
cd /home/claude/work/space/gnc_dev4/scripts
step "eval all (v2.0)"; GNC_IFACE_PIN=$P3 GNC_REV3_PARTS=eval nice -n 10 $PY m2_rev3_fly.py > $LOG/rev3_fly_eval_v2.log 2>&1
step "done"
