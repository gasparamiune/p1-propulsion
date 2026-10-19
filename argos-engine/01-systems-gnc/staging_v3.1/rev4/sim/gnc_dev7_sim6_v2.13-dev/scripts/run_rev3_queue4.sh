#!/bin/bash
# GNC rev3 flight queue 4 (sequential, nice 10, one process at a time; waits for queue 3c, PIDs 32451/32452, and runs after
# the sim6 v2.12-dev bit-check: part A ALL IDENTICAL (bitcheck_v212_offparts.json), part B v1.1 ALL PASS
# (bitcheck_v212_func_v1p1.json; v1.0 FAIL kept, criterion defect). Lead line 194 (3): P6c release-hold comparator with the
# population hold table and the post-E2 command profile. Kill by PID only.
LOG=/home/claude/work/space/out/rev3/logs
step() { echo "=== $(date -u +%H:%M:%S) $1" ; }
while kill -0 32452 2>/dev/null || kill -0 32451 2>/dev/null; do sleep 20; done
step "queue 3c finished"
set -a; . /home/claude/work/space/gnc_dev3/scripts/m2r3_env.sh; set +a
P3=/home/claude/work/space/pins_rev3/pins_rev3.sha256
cd /home/claude/work/space/gnc_dev6/scripts
step "P6c release-hold comparator (sim6 v2.12-dev, m2_rev3_fly v2.2)"; GNC_IFACE_PIN=$P3 GNC_REV3_ARMS='P6c' GNC_REV3_PARTS=mc nice -n 10 $PY m2_rev3_fly.py
step "P6 evaluation v1.1 (m2_rev3_p6)"; GNC_IFACE_PIN=$P3 nice -n 10 $PY m2_rev3_p6.py > $LOG/p6_late_commit_v1p1.log 2>&1
step "reserve dip (m2_rev3_reserve_dip)"; nice -n 10 $PY m2_rev3_reserve_dip.py > $LOG/reserve_dip.log 2>&1
step "eval all (v2.2)"; GNC_IFACE_PIN=$P3 GNC_REV3_PARTS=eval nice -n 10 $PY m2_rev3_fly.py > $LOG/rev3_fly_eval_v22.log 2>&1
step "done"
