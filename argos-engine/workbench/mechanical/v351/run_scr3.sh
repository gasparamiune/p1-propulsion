#!/bin/bash
# v3.5.1 M1 screening 3: args TAG then extra run_thermal args (A1 first 3.5 s + 6 s soak)
cd /home/claude/work/mechanical/v351/engine/04-fea/thermal
PY=/opt/engine-venv/bin/python
TAG=$1; shift
COMMON="--dc DC-A1scr3p5 --bound hi --level 2.5 --soak 6 --threads 1 --ov D_pre=0.0499 --ovs tc03_material=IN718 --ovs nozzle_joint=J1 --ovs insert_sleeve_material=CARBON-PHENOLIC --mat ENG-TC-09=IN718"
export OMP_NUM_THREADS=1
nice -n 10 $PY -u run_thermal.py $COMMON "$@" --tag v351scr_$TAG > /home/claude/work/mechanical/v351/logs/scr3_$TAG.log 2>&1
echo SCR3_DONE >> /home/claude/work/mechanical/v351/logs/scr3_$TAG.log
