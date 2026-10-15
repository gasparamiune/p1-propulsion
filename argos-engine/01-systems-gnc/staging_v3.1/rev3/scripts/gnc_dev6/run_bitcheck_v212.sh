#!/bin/bash
# GNC rev3: sim6 v2.12-dev (amendment V3) bit-check against v2.11-dev and functional checks; nice 10, sequential. Kill by PID only.
set -a; . /home/claude/work/space/gnc_dev3/scripts/m2r3_env.sh; set +a
export GNC_IFACE_PIN=/home/claude/work/space/pins_rev3/pins_rev3.sha256
O=/home/claude/work/space/out/rev3/bitcheck_v212
BC=/home/claude/work/space/gnc_dev6/scripts/m2_bitcheck_v212.py
cd /home/claude/work/space/gnc_dev6/scripts
step() { echo "=== $(date -u +%H:%M:%S) $1" ; }
step "fly v2.11 (gnc_dev5)"; GNC_TREE=/home/claude/work/space/gnc_dev5 GNC_BC_OUT=$O/bc_v211.npz nice -n 10 $PY $BC fly
step "fly v2.12 (gnc_dev6)"; GNC_TREE=/home/claude/work/space/gnc_dev6 GNC_BC_OUT=$O/bc_v212.npz nice -n 10 $PY $BC fly
step "compare"; GNC_TREE=/home/claude/work/space/gnc_dev6 nice -n 10 $PY $BC compare $O/bc_v211.npz $O/bc_v212.npz $O/bitcheck_v212_offparts.json
step "functional"; GNC_TREE=/home/claude/work/space/gnc_dev6 nice -n 10 $PY $BC func $O/bitcheck_v212_func.json
step "done"
