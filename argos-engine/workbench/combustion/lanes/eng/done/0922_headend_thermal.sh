# Lead request 2026-10-12: head-end thermal BC (injector face, forward closure, pintle stem) over burn, MECO coast,
# relight and post-landing soak, x0.5-2 band, for the HV69 servo-mount check (Mechanical).
cd /home/claude/work/combustion/src
/opt/engine-venv/bin/python headend_thermal_v2.py /home/claude/work/combustion/data/v2 /home/claude/work/combustion/figs/v2
echo "exit $?"
