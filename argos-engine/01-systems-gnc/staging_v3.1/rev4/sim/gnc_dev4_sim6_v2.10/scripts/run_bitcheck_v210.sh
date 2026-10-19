#!/bin/bash
# sim6 v2.10-dev bit-check (GNC rev3); nice 10, one process at a time
cd /home/claude/work/space/gnc_dev4/scripts
set -a; . /home/claude/work/space/gnc_dev3/scripts/m2r3_env.sh; set +a
O=/home/claude/work/space/out/rev3/bitcheck_v210
echo "=== $(date -u +%H:%M:%S) fly v2.9 (gnc_dev3)"
GNC_TREE=/home/claude/work/space/gnc_dev3 GNC_BC_OUT=$O/bc_v29.npz nice -n 10 $PY m2_bitcheck_v210.py fly
echo "=== $(date -u +%H:%M:%S) fly v2.10 (gnc_dev4)"
GNC_TREE=/home/claude/work/space/gnc_dev4 GNC_BC_OUT=$O/bc_v210.npz nice -n 10 $PY m2_bitcheck_v210.py fly
echo "=== $(date -u +%H:%M:%S) compare"
GNC_TREE=/home/claude/work/space/gnc_dev4 nice -n 10 $PY m2_bitcheck_v210.py compare $O/bc_v29.npz $O/bc_v210.npz $O/bitcheck_v210_offparts.json
echo "=== $(date -u +%H:%M:%S) functional"
GNC_TREE=/home/claude/work/space/gnc_dev4 GNC_IFACE_PIN=/home/claude/work/space/pins_rev3/pins_rev3.sha256 nice -n 10 $PY m2_bitcheck_v210.py func $O/bitcheck_v210_func.json
echo "=== $(date -u +%H:%M:%S) done"
