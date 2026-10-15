#!/bin/bash
# gimbal axis stiffness v1: 7 deg poses, lever-web candidate, thrust sensitivity, frame-mesh check (h 3 = within 0.4 % of h 2.5)
# pinned to one core (taskset -c 0) so that the Mechanical total stays <= 2 cores while the thermal FEA runs on the other
cd /home/claude/work/mechanical/runs/stiff
PY=/opt/engine-venv/bin/python
G=/home/claude/work/mechanical/engine/04-fea/stiffness/gimbal_k.py
export OMP_NUM_THREADS=1
taskset -c 0 $PY -u $G --poses alpha+7,alpha-7,beta+7,beta-7,cone7_045,cone7_135,cone7_225,cone7_315 --h 3 --hf 4 --thrust 62.5 >> poses.log 2>&1
taskset -c 0 $PY -u $G --poses centre --h 3 --hf 4 --thrust 62.5 --lever_web >> poses.log 2>&1
taskset -c 0 $PY -u $G --poses centre --h 3 --hf 4 --thrust 160,500 >> poses.log 2>&1
taskset -c 0 $PY -u $G --poses centre --h 3 --hf 3 --thrust 62.5 >> poses.log 2>&1
echo POSES_DONE >> poses.log
