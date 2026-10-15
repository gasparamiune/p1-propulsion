cd /home/claude/work/combustion/cfd/own
B=/home/claude/work/combustion/cfd/blender
mkdir -p $B/final
for V in threequarter side; do
  timeout 2400 blender -b --factory-startup -P blender_render.py -- $B/m2s_fields $B/final/argos_plume_artistic_${V}_raw.png 160 1600 560 3 0.15 $V 0 wien 0.008 5 2>&1 | grep -E "RENDERED|DENOISE|Error|error|Traceback" | head -5
  /opt/engine-venv/bin/python blender_caption.py $B/final/argos_plume_artistic_${V}_raw.png $B/final/argos_plume_artistic_${V}.png "ARGOS H1 plume at 500 N, v1 design point (Pc 25 bar, O/F 7.76); fields: medium-grid 2-D axisymmetric CFD (t = 3 ms) with the fast-chemistry afterburning increment, revolved"
done
ls -la $B/final
