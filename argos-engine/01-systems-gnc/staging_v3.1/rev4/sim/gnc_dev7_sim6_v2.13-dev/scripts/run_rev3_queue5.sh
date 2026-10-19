#!/bin/bash
# GNC rev3 queue 5 (P9, lead 181 (8) / rev3 plan P9): the full m2_bitcheck_v29 v1.2 run (parts A0, A1, G, K, V, N, RF) on the
# rev3 code (gnc_dev6: sim6 v2.12-dev, run6 v2.12-dev; amendments V2, L, V3 off by default). Waits for queue 4b (PIDs
# 4820/4822). nice 10, one process. Output out/rev3/bitcheck_v29_rev3 (rev2 evidence in out/rev2/bitcheck_v29 untouched),
# scratch /home/claude/work/space/scratch_bit29_rev3. Kill by PID only.
LOG=/home/claude/work/space/out/rev3/logs
step() { echo "=== $(date -u +%H:%M:%S) $1" ; }
while kill -0 4822 2>/dev/null || kill -0 4820 2>/dev/null; do sleep 20; done
step "queue 4b finished"
set -a; . /home/claude/work/space/gnc_dev3/scripts/m2r3_env.sh; set +a
export GNC_IFACE_PIN=/home/claude/work/space/pins_rev3/pins_rev3.sha256
export GNC_RES=/home/claude/work/space/out/rev3/bitcheck_v29_rev3
export GNC_BIT_SCRATCH=/home/claude/work/space/scratch_bit29_rev3
mkdir -p $GNC_RES $GNC_BIT_SCRATCH
cd /home/claude/work/space/gnc_dev6/scripts
step "m2_bitcheck_v29 v1.2 full run on gnc_dev6 (sim6 v2.12-dev)"; nice -n 10 $PY m2_bitcheck_v29.py > $LOG/bitcheck_v29_rev3.log 2>&1; echo "exit $?"
step "done"
