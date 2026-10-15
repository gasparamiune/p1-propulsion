cd /home/claude/work/combustion/cfd/own
R=/home/claude/work/combustion/cfd/ownruns
/opt/engine-venv/bin/python plot_afterburn.py $R/c_2s_100/final.npz $R/c_2s_100/afterburn_v3.npz $R/c_2s_100/fig c2s > /dev/null
/opt/engine-venv/bin/python plot_afterburn.py $R/c_2s_sweep/final.npz $R/c_2s_sweep/afterburn_v3_floor.npz $R/c_2s_sweep/fig c2s_floor > /dev/null
echo replot done
