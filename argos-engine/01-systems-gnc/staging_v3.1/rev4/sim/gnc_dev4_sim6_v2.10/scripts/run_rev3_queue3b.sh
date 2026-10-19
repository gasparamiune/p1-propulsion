#!/bin/bash
# GNC rev3 flight queue 3b (sequential, nice 10, one process at a time; waits for queue 2, PID 23486). Replaces queue 3
# (stopped in its waiting loop, nothing started). Kill by PID only.
LOG=/home/claude/work/space/out/rev3/logs
step() { echo "=== $(date -u +%H:%M:%S) $1" ; }
while kill -0 23486 2>/dev/null; do sleep 20; done
step "queue 2 finished"
set -a; . /home/claude/work/space/gnc_dev3/scripts/m2r3_env.sh; set +a
P3=/home/claude/work/space/pins_rev3/pins_rev3.sha256
cd /home/claude/work/space/gnc_dev4/scripts
step "P6b late commit, nominal start (sim6 v2.10-dev, m2_rev3_fly v2.1)"; GNC_IFACE_PIN=$P3 GNC_REV3_ARMS='P6b' GNC_REV3_PARTS=mc nice -n 10 $PY m2_rev3_fly.py
cd /home/claude/work/space/gnc_dev5/scripts
step "P5 latency allowance flights + eval (sim6 v2.11-dev)"; GNC_IFACE_PIN=$P3 nice -n 10 $PY m2_rev3_p5.py > $LOG/p5_latency.log 2>&1
cd /home/claude/work/space/gnc_dev4/scripts
step "P4c R2 v2 confirmation (sim6 v2.10-dev, m2_rev3_fly v2.1)"; GNC_IFACE_PIN=$P3 GNC_REV3_ARMS='P4c' GNC_REV3_PARTS=mc nice -n 10 $PY m2_rev3_fly.py
step "r2v2 eval (statistics + confirmation)"; GNC_IFACE_PIN=$P3 nice -n 10 $PY m2_rev3_r2v2_eval.py > $LOG/r2v2_eval_conf.log 2>&1
step "eval all (v2.1)"; GNC_IFACE_PIN=$P3 GNC_REV3_PARTS=eval nice -n 10 $PY m2_rev3_fly.py > $LOG/rev3_fly_eval_v21.log 2>&1
cd /home/claude/work/space/gnc_dev5/scripts
step "P5 RG-16 windowed budget A1 / B1 + vibration sensitivity (sim6 v2.11-dev)"; GNC_IFACE_PIN=$P3 nice -n 10 $PY m2_rev3_rg16w.py > $LOG/p5_rg16w.log 2>&1
step "done"
