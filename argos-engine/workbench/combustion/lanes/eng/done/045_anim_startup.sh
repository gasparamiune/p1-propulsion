cd /home/claude/work/combustion/cfd/own
R=/home/claude/work/combustion/cfd/ownruns
mkdir -p /home/claude/work/combustion/cfd/anim
/opt/engine-venv/bin/python make_anim.py $R/m_2s_100 /home/claude/work/combustion/cfd/anim/startup_500N_medium --bottom schlieren --xmax 30 --rmax 4 --label "start-up transient to 500 N (Pc 25 bar), medium grid 80k cells, own solver plume2s" --fps 12
