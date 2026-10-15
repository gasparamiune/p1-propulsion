cd /home/claude/work/combustion/cfd/own
R=/home/claude/work/combustion/cfd/ownruns
/opt/engine-venv/bin/python afterburn.py $R/c_2s_100/final.npz $R/c_2s_100/afterburn.npz --frac 1.0
/opt/engine-venv/bin/python plot_afterburn.py $R/c_2s_100/final.npz $R/c_2s_100/afterburn.npz $R/c_2s_100/fig c2s
/opt/engine-venv/bin/python synth_photo.py $R/c_2s_100/final.npz $R/c_2s_100/afterburn.npz $R/c_2s_100/fig/c2s_synth_photo.png --title "ARGOS H1 plume, 500 N, coarse grid (20k cells)" --xmax 30 --ymax 3
