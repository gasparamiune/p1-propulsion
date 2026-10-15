cd /home/claude/work/combustion/cfd/own
B=/home/claude/work/combustion/cfd/blender
mkdir -p $B/test3
for KE in 0.5 2 8; do
  timeout 900 blender -b --factory-startup -P blender_render.py -- $B/m2s_fields $B/test3/wien_KE${KE}.png 16 640 224 $KE 0.3 threequarter 0 wien 2>&1 | grep -E "RENDERED|Error|error|Traceback" | head -5
done
timeout 900 blender -b --factory-startup -P blender_render.py -- $B/m2s_fields $B/test3/wien_side_KE2.png 16 640 224 2 0.3 side 0 wien 2>&1 | grep -E "RENDERED|Error|error|Traceback" | head -5
ls -la $B/test3
