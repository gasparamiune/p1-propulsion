# Coarse two-species RANS at the combustion.json v2.1 S230 max-thrust point (O/F 10.435, Pc 25.01 bar, T0 2757 K):
# same grid/model/settings as c_2s_100 (v1 point O/F 7.76), so v2 - v1 differences are free of grid error.
# Geometry unchanged (v2 contour = v1 shape, +30 mm x_face). make_case.py CFD_OPPOINTS override (2026-10-12).
cd /home/claude/work/combustion/cfd/own
export CFD_OPPOINTS=/home/claude/work/combustion/data/v2/combustion_interface_v2p1_as_published.json
/opt/engine-venv/bin/python run_plume.py /home/claude/work/combustion/cfd/ownruns/c_2s_100_v2op --level 0.5 --tend 0.004 --frame 5e-5
echo "exit $?"
