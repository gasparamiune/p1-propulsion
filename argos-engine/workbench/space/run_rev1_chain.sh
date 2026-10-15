#!/bin/bash
# GNC rev1 MC chain (two solver processes): P1 = purge_bleed 0/2 -> rg07 -> cap a1; P2 = purge_bleed 1/2 -> cap grid,kscan -> cap cond
cd /home/claude/work/space/gnc_dev28
export NUMBA_NUM_THREADS=1 GNC_IFACE=/home/claude/work/space/iface_v3c GNC_ACT_RATE=/home/claude/work/space/iface_v3c/actuator_rate_check_v2.json
PY="nice -n 10 /opt/engine-venv/bin/python"
L=/home/claude/work/space/logs
if [ "$1" = "P1" ]; then
  GNC_PB_PARTS=mc GNC_PB_SPLIT=0/2 $PY scripts/m2_purge_bleed.py > $L/pb_mc_0.log 2>&1
  GNC_RG07_PARTS=mc $PY scripts/m2_rg07_b1_eng07d.py > $L/rg07_mc.log 2>&1
  GNC_CAP_PARTS=a1 $PY scripts/m2_cap_rule.py > $L/cap_a1.log 2>&1
else
  GNC_PB_PARTS=mc GNC_PB_SPLIT=1/2 $PY scripts/m2_purge_bleed.py > $L/pb_mc_1.log 2>&1
  GNC_CAP_PARTS=grid,kscan $PY scripts/m2_cap_rule.py > $L/cap_grid.log 2>&1
  GNC_CAP_PARTS=cond $PY scripts/m2_cap_rule.py > $L/cap_cond.log 2>&1
fi
echo "chain $1 done" >> $L/chain_rev1.log
