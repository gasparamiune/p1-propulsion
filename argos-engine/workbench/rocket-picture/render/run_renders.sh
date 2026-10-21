#!/bin/bash
# Final renders: one Blender process at a time, 2 threads, nice 10. Raw RGBA PNGs go to work/ (deleted by post).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CAD=/home/claude/work/shared-fallback/engine/03-cad/v3.5.1
export PYTHONPATH=/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/pylib312   # numpy for the glTF importer
SS="${SS:-1.5}"; SPP="${SPP:-64}"
for v in exterior cutaway; do
  SECONDS=0
  nice -n 10 blender -b -t 2 -P "$HERE/rocket_render_blender.py" -- --glb "$CAD/assembly/ENGINE_v3.5.1_neutral.glb" \
    --bom "$CAD/BOM_v3.5.1.json" --view $v --out "$HERE/work/raw_$v.png" --meta "$HERE/work/meta_$v.json" \
    --w 1000 --h 1800 --ss "$SS" --spp "$SPP" > "$HERE/work/blender_$v.log" 2>&1
  echo "$v ${SECONDS}s"
done
