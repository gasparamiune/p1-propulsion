# Validation v2.2: afterburning rise dT_ab on coarse/medium/fine at the same time (3.25 ms) + temporal band 2.50-3.25 ms
# (v1 operating point; CFD_OPPOINTS deliberately unset so afterburn.py uses the runs' own O/F 7.76).
cd /home/claude/work/combustion/cfd/own
unset CFD_OPPOINTS
/opt/engine-venv/bin/python -W ignore afterburn_timegrid.py /home/claude/work/combustion/cfd/validation/results/afterburn_grid_time_v2.json /home/claude/work/combustion/cfd/validation/figs/afterburn_grid_time_v2.png
echo "exit $?"
