# Re-run of 093 (stopped at t 1.41 ms at 21:02:57 to run the lead's actuator/head-end requests first). Same settings.
cd /home/claude/work/combustion/cfd/own
rm -rf /home/claude/work/combustion/cfd/ownruns/c_2s_100_v2op
export CFD_OPPOINTS=/home/claude/work/combustion/data/v2/combustion_interface_v2p1_as_published.json
/opt/engine-venv/bin/python run_plume.py /home/claude/work/combustion/cfd/ownruns/c_2s_100_v2op --level 0.5 --tend 0.004 --frame 5e-5
echo "exit $?"
