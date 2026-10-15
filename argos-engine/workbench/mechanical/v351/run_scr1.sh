#!/bin/bash
# v3.5.1 M1 screening: TC-02 head hot spot, A1 burn 1 (3.54 s) + 6.5 s coast, BASE vs TB1 (dev copy CAD), same settings as the v13 TC09IN design runs
cd /home/claude/work/mechanical/v351/engine/04-fea/thermal
PY=/opt/engine-venv/bin/python
COMMON="--dc DC-A1scr3p5 --bound hi --level 2.5 --soak 6 --threads 2 --ov D_pre=0.0499 --ovs tc03_material=IN718 --ovs nozzle_joint=J1 --ovs insert_sleeve_material=CARBON-PHENOLIC --mat ENG-TC-09=IN718"
for V in BASE TB1; do
  nice -n 10 $PY -u run_thermal.py $COMMON --ovs tc03_face=$V --tag v351scr_$V > /home/claude/work/mechanical/v351/logs/scr1_$V.log 2>&1
done
echo SCR1_DONE >> /home/claude/work/mechanical/v351/logs/scr1_BASE.log
