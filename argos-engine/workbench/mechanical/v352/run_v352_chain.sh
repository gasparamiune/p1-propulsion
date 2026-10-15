#!/bin/bash
# v3.5.2 (lead CHANGELOG 206 (2a)) TC-09 thinning re-run chain, Mechanical 2026-10-13: thermal B1 -> thermal A1 -> (gate SAX_READY) -> S-AX L1.
# Same thermal settings as v351_TB1GC (run_full.sh) plus the TC-09 keys; one solver at a time, niced.
PY=/opt/engine-venv/bin/python
L=/home/claude/work/mechanical/v352/logs
TAG=v352_TC09
COMMON="--bound hi --level 2.5 --aft SS316L --soak 3600 --threads 1 --ov D_pre=0.0499 --ovs nozzle_joint=J1 --ovs insert_sleeve_material=CARBON-PHENOLIC --mat ENG-TC-09=IN718 --ovs tc03_material=GLIDCOP-AL15 --ovs tc03_face=TB1 --ov tc09_barrel_wall=0.0018 --ov tc09_socket_R2=0.0345"
export OMP_NUM_THREADS=1
echo "chain start $(date -u +%FT%TZ) pid $$" >> $L/chain.log
cd /home/claude/work/mechanical/v352/engine/04-fea/thermal
for DC in DC-B1v3p99_tg711 DC-A1dispp99_tg711; do
  echo "thermal $DC start $(date -u +%FT%TZ)" >> $L/chain.log
  nice -n 15 $PY -u run_thermal.py --dc $DC $COMMON --tag $TAG > $L/full_${DC}_${TAG}.log 2>&1
  echo "thermal $DC exit $? $(date -u +%FT%TZ)" >> $L/chain.log
done
n=0
while [ ! -f /home/claude/work/mechanical/v352/SAX_READY ] && [ $n -lt 360 ]; do sleep 30; n=$((n+1)); done
echo "sax gate n=$n $(date -u +%FT%TZ)" >> $L/chain.log
[ -f /home/claude/work/mechanical/v352/SAX_READY ] || { echo "SAX_READY missing: stop" >> $L/chain.log; exit 1; }
cd /home/claude/work/mechanical/v352/engine/04-fea/structural
export SAX_CAD=v352 SAX_THERMAL_TAG=$TAG
nice -n 15 $PY -u sax.py solve --level 1 > $L/solve_L1_v352.log 2>&1
echo "SOLVE_EXIT $?" >> $L/solve_L1_v352.log
nice -n 15 $PY -u sax.py post --level 1 > $L/post_L1_v352.log 2>&1
echo "POST_EXIT $?" >> $L/post_L1_v352.log
echo "CHAIN_DONE $(date -u +%FT%TZ)" >> $L/chain.log
