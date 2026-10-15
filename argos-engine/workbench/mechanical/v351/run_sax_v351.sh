#!/bin/bash
# S-AX on CAD v3.5.1 (TB1 + GlidCop TC-03), thermal v351_TB1GC, design ties (axial) then the bonded bound; level given as $1
cd /home/claude/work/mechanical/v351/engine/04-fea/structural
export SAX_CAD=v351 SAX_THERMAL_TAG=v351_TB1GC OMP_NUM_THREADS=1
L=/home/claude/work/mechanical/runs/structural/logs
LEV=${1:-1}
nice -n 10 /opt/engine-venv/bin/python -u sax.py solve --level $LEV > $L/solve_L${LEV}_v351.log 2>&1
echo "SOLVE_EXIT $?" >> $L/solve_L${LEV}_v351.log
nice -n 10 /opt/engine-venv/bin/python -u sax.py post --level $LEV > $L/post_L${LEV}_v351.log 2>&1
echo "POST_EXIT $?" >> $L/post_L${LEV}_v351.log
