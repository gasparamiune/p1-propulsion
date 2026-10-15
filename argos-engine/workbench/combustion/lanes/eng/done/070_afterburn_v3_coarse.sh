cd /home/claude/work/combustion/cfd/own
R=/home/claude/work/combustion/cfd/ownruns
mkdir -p $R/c_2s_100/fig/afterburn_v2_superseded
for f in $R/c_2s_100/fig/c2s_Teq_*.png $R/c_2s_100/fig/c2s_dT_afterburn_*.png $R/c_2s_100/fig/c2s_XCO_*.png $R/c_2s_100/fig/c2s_XOH_*.png $R/c_2s_100/fig/c2s_afterburn_axis.png $R/c_2s_100/fig/c2s_afterburn_stats.json $R/c_2s_100/fig/c2s_synth_photo.png; do [ -f "$f" ] && mv "$f" $R/c_2s_100/fig/afterburn_v2_superseded/; done
[ -f $R/c_2s_100/afterburn.npz ] && mv $R/c_2s_100/afterburn.npz $R/c_2s_100/afterburn_v2_superseded.npz
/opt/engine-venv/bin/python -W ignore afterburn.py $R/c_2s_100/final.npz $R/c_2s_100/afterburn_v3.npz --frac 1.0
/opt/engine-venv/bin/python plot_afterburn.py $R/c_2s_100/final.npz $R/c_2s_100/afterburn_v3.npz $R/c_2s_100/fig c2s
/opt/engine-venv/bin/python synth_photo.py $R/c_2s_100/final.npz $R/c_2s_100/afterburn_v3.npz $R/c_2s_100/fig/c2s_synth_photo.png --title "ARGOS H1 plume, 500 N, coarse grid (20k cells)" --xmax 30 --ymax 3
