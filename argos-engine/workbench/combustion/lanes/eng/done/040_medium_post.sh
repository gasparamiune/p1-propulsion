cd /home/claude/work/combustion/cfd/own
R=/home/claude/work/combustion/cfd/ownruns
/opt/engine-venv/bin/python post_plume.py $R/m_2s_100/final.npz $R/m_2s_100/fig m2s
/opt/engine-venv/bin/python -W ignore afterburn.py $R/m_2s_100/final.npz $R/m_2s_100/afterburn.npz --frac 1.0
/opt/engine-venv/bin/python plot_afterburn.py $R/m_2s_100/final.npz $R/m_2s_100/afterburn.npz $R/m_2s_100/fig m2s
/opt/engine-venv/bin/python synth_photo.py $R/m_2s_100/final.npz $R/m_2s_100/afterburn.npz $R/m_2s_100/fig/m2s_synth_photo.png --title "ARGOS H1 plume at 500 N (Pc 25 bar, O/F 7.76), medium grid (80k cells)" --xmax 30 --ymax 3
/opt/engine-venv/bin/python synth_photo.py $R/m_2s_100/final.npz none $R/m_2s_100/fig/m2s_synth_photo_frozenT.png --title "ARGOS H1 plume at 500 N, medium grid, frozen CFD temperature (no afterburning)" --xmax 30 --ymax 3
