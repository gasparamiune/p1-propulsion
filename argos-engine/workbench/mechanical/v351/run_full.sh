#!/bin/bash
# v3.5.1 M1 full thermal runs (design-run settings of v13pre36IN_J1revB_TC09IN + the v3.5.1 TC-03 design): args DC TAG then extra args
cd /home/claude/work/mechanical/v351/engine/04-fea/thermal
PY=/opt/engine-venv/bin/python
DC=$1; TAG=$2; shift; shift
COMMON="--bound hi --level 2.5 --aft SS316L --soak 3600 --threads 1 --ov D_pre=0.0499 --ovs nozzle_joint=J1 --ovs insert_sleeve_material=CARBON-PHENOLIC --mat ENG-TC-09=IN718"
export OMP_NUM_THREADS=1
nice -n 10 $PY -u run_thermal.py --dc $DC $COMMON "$@" --tag $TAG > /home/claude/work/mechanical/v351/logs/full_${DC}_${TAG}.log 2>&1
echo FULL_DONE >> /home/claude/work/mechanical/v351/logs/full_${DC}_${TAG}.log
