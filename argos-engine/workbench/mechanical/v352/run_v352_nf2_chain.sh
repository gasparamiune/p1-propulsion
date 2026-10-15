#!/bin/bash
# v3.5.2 (lead CHANGELOG 206 (2a) + 212 N-F2) re-run chain, Mechanical 2026-10-13: TC-09 thinning + N-F2 (R 1.0 NZ-01 shoulder edge +
# 0.25 mm flexible-graphite foil NZ-06).  thermal B1 -> thermal A1 -> S-AX L1 (solve + post).  The A1 thermal is re-run ONLY because the
# geometry changed (FA-1 / 194 period domain and TS1 use the A1 relight state; lead 213: the ~210 m apogee target does not change the A1 cases).
# Waits for the T-F2 contact runs (one heavy solver at a time); niced; same thermal settings as v351_TB1GC plus the v3.5.2 keys.
PY=/opt/engine-venv/bin/python
L=/home/claude/work/mechanical/v352/logs
TAG=v352_NF2
COMMON="--bound hi --level 2.5 --aft SS316L --soak 3600 --threads 1 --ov D_pre=0.0499 --ovs nozzle_joint=J1 --ovs insert_sleeve_material=CARBON-PHENOLIC --mat ENG-TC-09=IN718 --ovs tc03_material=GLIDCOP-AL15 --ovs tc03_face=TB1 --ov tc09_barrel_wall=0.0018 --ov tc09_socket_R2=0.0345 --ov nz_foil_t=0.00025 --ov nz01_shoulder_R=0.0010"
export OMP_NUM_THREADS=1
echo "nf2 chain start $(date -u +%FT%TZ) pid $$" >> $L/chain_nf2.log
n=0
while pgrep -f "sax_contact_tc0203.py" > /dev/null && [ $n -lt 480 ]; do sleep 30; n=$((n+1)); done
echo "contact gate n=$n $(date -u +%FT%TZ)" >> $L/chain_nf2.log
cd /home/claude/work/mechanical/v352/engine/04-fea/thermal
for DC in DC-B1v3p99_tg711 DC-A1dispp99_tg711; do
  echo "thermal $DC start $(date -u +%FT%TZ)" >> $L/chain_nf2.log
  nice -n 15 $PY -u run_thermal.py --dc $DC $COMMON --tag $TAG > $L/full_${DC}_${TAG}.log 2>&1
  echo "thermal $DC exit $? $(date -u +%FT%TZ)" >> $L/chain_nf2.log
done
cd /home/claude/work/mechanical/v352/engine/04-fea/structural
export SAX_CAD=v352 SAX_THERMAL_TAG=$TAG
echo "sax solve start $(date -u +%FT%TZ)" >> $L/chain_nf2.log
nice -n 15 $PY -u sax.py solve --level 1 > $L/solve_L1_v352_NF2.log 2>&1
echo "SOLVE_EXIT $?" >> $L/solve_L1_v352_NF2.log
nice -n 15 $PY -u sax.py post --level 1 > $L/post_L1_v352_NF2.log 2>&1
echo "POST_EXIT $?" >> $L/post_L1_v352_NF2.log
echo "NF2_CHAIN_DONE $(date -u +%FT%TZ)" >> $L/chain_nf2.log
