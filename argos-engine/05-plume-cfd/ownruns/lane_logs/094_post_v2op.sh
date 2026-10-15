# Post-processing of the coarse run at the combustion.json v2.1 S230 point: fields, afterburning (exhaust composition
# consistent with the flow field: CFD_OPPOINTS makes afterburn.py use O/F 10.435 at frac 1.0), synthetic image.
cd /home/claude/work/combustion/cfd/own
R=/home/claude/work/combustion/cfd/ownruns
export CFD_OPPOINTS=/home/claude/work/combustion/data/v2/combustion_interface_v2p1_as_published.json
[ -f $R/c_2s_100_v2op/final.npz ] || { echo "v2op run produced no final.npz"; exit 1; }
/opt/engine-venv/bin/python post_plume.py $R/c_2s_100_v2op/final.npz $R/c_2s_100_v2op/fig c2s_v2op
/opt/engine-venv/bin/python -W ignore afterburn.py $R/c_2s_100_v2op/final.npz $R/c_2s_100_v2op/afterburn_v3.npz --frac 1.0 | tail -n 60
/opt/engine-venv/bin/python plot_afterburn.py $R/c_2s_100_v2op/final.npz $R/c_2s_100_v2op/afterburn_v3.npz $R/c_2s_100_v2op/fig c2s_v2op > /dev/null
/opt/engine-venv/bin/python synth_photo.py $R/c_2s_100_v2op/final.npz $R/c_2s_100_v2op/afterburn_v3.npz $R/c_2s_100_v2op/fig/c2s_v2op_synth_photo.png --title "ARGOS H1 plume at 500 N, combustion.json v2.1 point (Pc 25.0 bar, O/F 10.44), coarse grid (20k cells)" --xmax 30 --ymax 3
echo "exit $?"
