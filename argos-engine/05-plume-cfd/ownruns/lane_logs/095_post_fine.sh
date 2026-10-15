# Fine-grid (320k) post-processing after run f_2s_100 (CFD lane, PID 2948) ends: fields + afterburning (v1 point) so
# the afterburning increment is available on three grids.
cd /home/claude/work/combustion/cfd/own
R=/home/claude/work/combustion/cfd/ownruns
while kill -0 2948 2>/dev/null; do sleep 15; done
[ -f $R/f_2s_100/final.npz ] || { echo "fine run produced no final.npz"; exit 1; }
/opt/engine-venv/bin/python post_plume.py $R/f_2s_100/final.npz $R/f_2s_100/fig f2s
/opt/engine-venv/bin/python -W ignore afterburn.py $R/f_2s_100/final.npz $R/f_2s_100/afterburn_v3.npz --frac 1.0 | tail -n 60
/opt/engine-venv/bin/python plot_afterburn.py $R/f_2s_100/final.npz $R/f_2s_100/afterburn_v3.npz $R/f_2s_100/fig f2s > /dev/null
echo "exit $?"
