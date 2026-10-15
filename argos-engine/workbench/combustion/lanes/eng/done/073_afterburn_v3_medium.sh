cd /home/claude/work/combustion/cfd/own
R=/home/claude/work/combustion/cfd/ownruns
mkdir -p $R/m_2s_100/fig/afterburn_v2_superseded
for f in $R/m_2s_100/fig/m2s_Teq_*.png $R/m_2s_100/fig/m2s_dT_afterburn_*.png $R/m_2s_100/fig/m2s_XCO_*.png $R/m_2s_100/fig/m2s_XOH_*.png $R/m_2s_100/fig/m2s_afterburn_axis.png $R/m_2s_100/fig/m2s_afterburn_stats.json $R/m_2s_100/fig/m2s_synth_photo.png; do [ -f "$f" ] && mv "$f" $R/m_2s_100/fig/afterburn_v2_superseded/; done
[ -f $R/m_2s_100/afterburn.npz ] && mv $R/m_2s_100/afterburn.npz $R/m_2s_100/afterburn_v2_superseded.npz
/opt/engine-venv/bin/python -W ignore afterburn.py $R/m_2s_100/final.npz $R/m_2s_100/afterburn_v3.npz --frac 1.0
/opt/engine-venv/bin/python plot_afterburn.py $R/m_2s_100/final.npz $R/m_2s_100/afterburn_v3.npz $R/m_2s_100/fig m2s
/opt/engine-venv/bin/python synth_photo.py $R/m_2s_100/final.npz $R/m_2s_100/afterburn_v3.npz $R/m_2s_100/fig/m2s_synth_photo.png --title "ARGOS H1 plume at 500 N (Pc 25 bar, O/F 7.76), medium grid (80k cells)" --xmax 30 --ymax 3
