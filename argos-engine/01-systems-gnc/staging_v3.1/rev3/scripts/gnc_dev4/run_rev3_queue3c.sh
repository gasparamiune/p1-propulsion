#!/bin/bash
# GNC rev3 flight queue 3c (sequential, nice 10, one process at a time; waits for queue 2, PID 23486). Replaces queue 3b
# (stopped in its waiting loop, nothing started): lead line 194 (REV-COMB-3) withdraws the 62.5 N x pcf_k lit model of R2 v2
# (P4c not flown; lit side PENDING Combustion v2.4b) and the E2 + 0.22 s hold (P6 comparator re-flown later on sim6 v2.12-dev).
# Kill by PID only.
LOG=/home/claude/work/space/out/rev3/logs
step() { echo "=== $(date -u +%H:%M:%S) $1" ; }
while kill -0 23486 2>/dev/null; do sleep 20; done
step "queue 2 finished"
set -a; . /home/claude/work/space/gnc_dev3/scripts/m2r3_env.sh; set +a
P3=/home/claude/work/space/pins_rev3/pins_rev3.sha256
cd /home/claude/work/space/gnc_dev4/scripts
step "P6b late commit, nominal start (sim6 v2.10-dev, m2_rev3_fly v2.1)"; GNC_IFACE_PIN=$P3 GNC_REV3_ARMS='P6b' GNC_REV3_PARTS=mc nice -n 10 $PY m2_rev3_fly.py
step "P6 evaluation (m2_rev3_p6)"; GNC_IFACE_PIN=$P3 nice -n 10 $PY m2_rev3_p6.py > $LOG/p6_late_commit.log 2>&1
cd /home/claude/work/space/gnc_dev5/scripts
step "P5 latency allowance flights + eval (sim6 v2.11-dev)"; GNC_IFACE_PIN=$P3 nice -n 10 $PY m2_rev3_p5.py > $LOG/p5_latency.log 2>&1
cd /home/claude/work/space/gnc_dev4/scripts
step "eval all (v2.1)"; GNC_IFACE_PIN=$P3 GNC_REV3_PARTS=eval nice -n 10 $PY m2_rev3_fly.py > $LOG/rev3_fly_eval_v21.log 2>&1
cd /home/claude/work/space/gnc_dev5/scripts
step "P5 RG-16 windowed budget A1 / B1 + vibration sensitivity (sim6 v2.11-dev)"; GNC_IFACE_PIN=$P3 nice -n 10 $PY m2_rev3_rg16w.py > $LOG/p5_rg16w.log 2>&1
step "done"
