#!/bin/bash
# GNC rev3 flight queue (sequential, nice 10, one process at a time). Started by the GNC rev3 session; kill by PID only.
cd /home/claude/work/space/gnc_dev3/scripts
set -a; . ./m2r3_env.sh; set +a
LOG=/home/claude/work/space/out/rev3/logs
V35="GNC_IFACE=/home/claude/work/space/iface_v35a GNC_IFACE_PIN=/home/claude/work/space/pins_rev3/pins_rev3_v35a.sha256"
step() { echo "=== $(date -u +%H:%M:%S) $1" ; }
step "v35a"; env $V35 GNC_REV3_ARMS='liq|G73|v35a|h285,pw|G73|v35a|h285' GNC_REV3_PARTS=mc nice -n 10 $PY m2_rev3_fly.py
step "P2 sweep"; GNC_REV3_ARMS='P2' GNC_REV3_PARTS=mc nice -n 10 $PY m2_rev3_fly.py
step "v35t v35g"; env $V35 GNC_REV3_ARMS='liq|G73|v35t|h285,pw|G73|v35t|h285,liq|G73|v35g|h285' GNC_REV3_PARTS=mc nice -n 10 $PY m2_rev3_fly.py
step "eval P2"; GNC_REV3_PARTS=eval nice -n 10 $PY m2_rev3_fly.py > $LOG/rev3_fly_eval_P2.log 2>&1
step "P3 all4 decided + extra"; GNC_REV3_ARMS='liq|none|h285,liq|G73|h285,pw|G73|h285,pl|G73|h285,e19|G73|h285' GNC_REV3_PARTS=mc nice -n 10 $PY m2_rev3_fly.py
step "P3 main2"; GNC_REV3_ARMS='P3' GNC_REV3_PARTS=mc nice -n 10 $PY m2_rev3_fly.py
step "eval all"; GNC_REV3_PARTS=eval nice -n 10 $PY m2_rev3_fly.py > $LOG/rev3_fly_eval.log 2>&1
step "done"
