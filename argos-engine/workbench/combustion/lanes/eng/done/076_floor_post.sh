cd /home/claude/work/combustion/cfd/own
R=/home/claude/work/combustion/cfd/ownruns
/opt/engine-venv/bin/python post_plume.py $R/c_2s_sweep/final.npz $R/c_2s_sweep/fig c2s_floor
/opt/engine-venv/bin/python -W ignore afterburn.py $R/c_2s_sweep/final.npz $R/c_2s_sweep/afterburn_v3_floor.npz --frac 0.125
/opt/engine-venv/bin/python plot_afterburn.py $R/c_2s_sweep/final.npz $R/c_2s_sweep/afterburn_v3_floor.npz $R/c_2s_sweep/fig c2s_floor
/opt/engine-venv/bin/python synth_photo.py $R/c_2s_sweep/final.npz $R/c_2s_sweep/afterburn_v3_floor.npz $R/c_2s_sweep/fig/c2s_floor_synth_photo.png --title "ARGOS H1 plume at the 12.5 % floor (Pc 4.4 bar, O/F 3.11), coarse grid, 1.5 ms after reaching the floor" --xmax 20 --ymax 3
