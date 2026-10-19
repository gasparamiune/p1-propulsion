#!/bin/bash
# GNC rev3: sim6 v2.11-dev (amendment L) bit-check against v2.10-dev and functional checks; nice 10, sequential. Kill by PID only.
set -a; . /home/claude/work/space/gnc_dev3/scripts/m2r3_env.sh; set +a
export GNC_IFACE_PIN=/home/claude/work/space/pins_rev3/pins_rev3.sha256
O=/home/claude/work/space/out/rev3/bitcheck_v211
BC=/home/claude/work/space/gnc_dev5/scripts/m2_bitcheck_v211.py
cd /home/claude/work/space/gnc_dev5/scripts
step() { echo "=== $(date -u +%H:%M:%S) $1" ; }
step "fly v2.10 (gnc_dev4)"; GNC_TREE=/home/claude/work/space/gnc_dev4 GNC_BC_OUT=$O/bc_v210.npz nice -n 10 $PY $BC fly
step "fly v2.11 (gnc_dev5)"; GNC_TREE=/home/claude/work/space/gnc_dev5 GNC_BC_OUT=$O/bc_v211.npz nice -n 10 $PY $BC fly
step "compare"; GNC_TREE=/home/claude/work/space/gnc_dev5 nice -n 10 $PY $BC compare $O/bc_v210.npz $O/bc_v211.npz $O/bitcheck_v211_offparts.json
step "functional"; GNC_TREE=/home/claude/work/space/gnc_dev5 nice -n 10 $PY $BC func $O/bitcheck_v211_func.json
step "done"
