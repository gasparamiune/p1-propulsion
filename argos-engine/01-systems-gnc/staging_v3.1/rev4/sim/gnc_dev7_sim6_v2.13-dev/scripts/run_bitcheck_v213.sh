#!/bin/bash
# GNC rev4: sim6 v2.13-dev (amendment J, RE-24) bit-check against the stored v2.12-dev file and functional checks; nice 10, sequential. Kill by PID only.
set -a; . /home/claude/work/space/gnc_dev3/scripts/m2r3_env.sh; set +a
export GNC_IFACE_PIN=/home/claude/work/space/pins_rev3/pins_rev3.sha256
O=/home/claude/work/space/out/rev4/bitcheck_v213
BC=/home/claude/work/space/gnc_dev7/scripts/m2_bitcheck_v213.py
cd /home/claude/work/space/gnc_dev7/scripts
step() { echo "=== $(date -u +%H:%M:%S) $1" ; }
step "fly v2.13 (gnc_dev7)"; GNC_TREE=/home/claude/work/space/gnc_dev7 GNC_BC_OUT=$O/bc_v213.npz nice -n 10 $PY $BC fly
step "compare"; GNC_TREE=/home/claude/work/space/gnc_dev7 nice -n 10 $PY $BC compare /home/claude/work/space/out/rev3/bitcheck_v212/bc_v212.npz $O/bc_v213.npz $O/bitcheck_v213_offparts.json
step "functional"; GNC_TREE=/home/claude/work/space/gnc_dev7 nice -n 10 $PY $BC func $O/bitcheck_v213_func.json
step "done"
