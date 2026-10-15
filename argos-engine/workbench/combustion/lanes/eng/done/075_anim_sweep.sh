cd /home/claude/work/combustion/cfd/own
R=/home/claude/work/combustion/cfd/ownruns
mkdir -p /home/claude/work/combustion/cfd/anim
/opt/engine-venv/bin/python make_anim.py $R/c_2s_sweep /home/claude/work/combustion/cfd/anim/sweep_100_20_12p5_coarse --bottom schlieren --xmax 25 --rmax 4 --label "throttle sweep 100 -> 20 % (hold) -> 12.5 % floor (hold), coarse grid 20k cells, own solver plume2s, quasi-steady inflow" --fps 12
