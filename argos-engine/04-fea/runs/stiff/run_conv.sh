#!/bin/bash
# gimbal axis stiffness: mesh study at the centre pose (collar/ring/horn size h; frame 4 mm), 62.5 N thrust
cd /home/claude/work/mechanical/runs/stiff
PY=/opt/engine-venv/bin/python
G=/home/claude/work/mechanical/engine/04-fea/stiffness/gimbal_k.py
export OMP_NUM_THREADS=2
for h in 4 3 2.5; do
  $PY -u $G --poses centre --h $h --hf 4 --thrust 62.5 >> conv.log 2>&1
done
echo CONV_DONE >> conv.log
