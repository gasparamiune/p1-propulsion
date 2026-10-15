cd /home/claude/work/combustion/cfd/own
B=/home/claude/work/combustion/cfd/blender
mkdir -p $B/test4
timeout 900 blender -b --factory-startup -P blender_render.py -- $B/m2s_fields $B/test4/t4_KE3_q005.png 32 640 224 3 0.3 threequarter 0 wien 0.005 5 2>&1 | grep -E "RENDERED|DENOISE|Error|error|Traceback" | head -5
timeout 900 blender -b --factory-startup -P blender_render.py -- $B/m2s_fields $B/test4/t4_KE3_q002_side.png 32 640 224 3 0.3 side 0 wien 0.002 5 2>&1 | grep -E "RENDERED|DENOISE|Error|error|Traceback" | head -5
ls -la $B/test4
