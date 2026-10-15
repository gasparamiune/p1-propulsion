cd /home/claude/work/combustion/cfd/own
R=/home/claude/work/combustion/cfd/ownruns
mkdir -p $R/c_2s_100/fig/v2comp_sens $R/c_2s_sweep/fig/v2comp_sens
/opt/engine-venv/bin/python -W ignore afterburn.py $R/c_2s_100/final.npz $R/c_2s_100/afterburn_v3_v2comp_OF10p43.npz --OF 10.435 | tail -n 40
/opt/engine-venv/bin/python plot_afterburn.py $R/c_2s_100/final.npz $R/c_2s_100/afterburn_v3_v2comp_OF10p43.npz $R/c_2s_100/fig/v2comp_sens c2s_v2comp > /dev/null
/opt/engine-venv/bin/python -W ignore afterburn.py $R/c_2s_sweep/final.npz $R/c_2s_sweep/afterburn_v3_floor_v2comp_OF4p06.npz --frac 0.125 --OF 4.059 | tail -n 40
/opt/engine-venv/bin/python plot_afterburn.py $R/c_2s_sweep/final.npz $R/c_2s_sweep/afterburn_v3_floor_v2comp_OF4p06.npz $R/c_2s_sweep/fig/v2comp_sens c2s_floor_v2comp > /dev/null
echo done
