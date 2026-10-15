# Lead request 2026-10-12 (HV69 pintle drive): does the 0.08 s full stroke have a combustion basis? start/shutdown
# transients, ENG-05 tail-off, start-rule timeline, hard-start inventory vs full-stroke time 0.08-0.40 s.
cd /home/claude/work/combustion/src
/opt/engine-venv/bin/python actuator_rate_check.py /home/claude/work/combustion/data/v2 /home/claude/work/combustion/figs/v2
echo "exit $?"
