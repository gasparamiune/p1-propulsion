cd /home/claude/work/combustion/cfd/own
R=/home/claude/work/combustion/cfd/ownruns
B=/home/claude/work/combustion/cfd/blender
mkdir -p $B/test
/opt/engine-venv/bin/python blender_prep.py $R/m_2s_100/final.npz $R/m_2s_100/afterburn_v3.npz ../../data/v2/nozzle_contour_v2.csv $B/m2s_fields --xmax 30 --rmax 4
for KE in 1 4 16; do
  timeout 600 blender -b --factory-startup -P blender_render.py -- $B/m2s_fields $B/test/test_KE${KE}.png 8 480 168 $KE 0.3 threequarter 2>&1 | grep -E "RENDERED|Error|error|Traceback" | head -5
done
timeout 600 blender -b --factory-startup -P blender_render.py -- $B/m2s_fields $B/test/test_side_KE4.png 8 480 168 4 0.3 side 2>&1 | grep -E "RENDERED|Error|error|Traceback" | head -5
ls -la $B/test
