# Medium grid continued 3.0 -> 3.25 ms WITH frames every 0.05 ms (replaces 092, which had no frames and was stopped):
# the coarse frames show the plume is unsteady (x_md, first Mach max, T at 10 De vary with time), so the validation
# needs time-consistent levels and a temporal band per level. Same level -> direct state copy, time kept.
cd /home/claude/work/combustion/cfd/own
/opt/engine-venv/bin/python run_plume.py /home/claude/work/combustion/cfd/ownruns/m_2s_100_c325 --level 1 --init /home/claude/work/combustion/cfd/ownruns/m_2s_100/final.npz --keep_time --tend 0.0032500186513072836 --frame 5e-5
echo "exit $?"
