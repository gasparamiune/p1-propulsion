#!/bin/bash
# v3.5.1 M1 screening 2: TBC (APS YSZ 0.3 mm) on the TC-03 gas faces, BASE and TB1 geometry; A1 first 3.5 s + 6 s soak (DC-A1scr3p5)
cd /home/claude/work/mechanical/v351/engine/04-fea/thermal
PY=/opt/engine-venv/bin/python
COMMON="--dc DC-A1scr3p5 --bound hi --level 2.5 --soak 6 --threads 1 --ov D_pre=0.0499 --ovs tc03_material=IN718 --ovs nozzle_joint=J1 --ovs insert_sleeve_material=CARBON-PHENOLIC --mat ENG-TC-09=IN718"
V=$1; T=$2
export OMP_NUM_THREADS=1
nice -n 10 $PY -u run_thermal.py $COMMON --ovs tc03_face=$V --ov tc03_tbc_mm=$T --tag v351scr_${V}_tbc${T} > /home/claude/work/mechanical/v351/logs/scr2_${V}_tbc${T}.log 2>&1
echo SCR2_DONE >> /home/claude/work/mechanical/v351/logs/scr2_${V}_tbc${T}.log
