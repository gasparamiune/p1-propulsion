# Medium grid continued 3.0 -> 3.25 ms so the three GCI levels compare at the same time (fine run ends at 3.25 ms;
# coarse has a frame at 3.25 ms). Same level -> direct copy of the state (plume2s.init_from), time kept.
cd /home/claude/work/combustion/cfd/own
/opt/engine-venv/bin/python run_plume.py /home/claude/work/combustion/cfd/ownruns/m_2s_100_c325 --level 1 --init /home/claude/work/combustion/cfd/ownruns/m_2s_100/final.npz --keep_time --tend 0.0032500186513072836 --frame 0
echo "exit $?"
