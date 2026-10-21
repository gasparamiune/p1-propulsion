#!/bin/bash
# ARGOS H1 engine datasheet (gen v0.3.0): produce every CAD render the datasheet uses, from the real assembly
# GLB and the BOM of one CAD version. One Blender process at a time, 2 threads, nice 10 (other
# solvers share the 4 CPUs; v0.3.0: nice 15 by default, 1 thread while any ccx runs). Renders are visualisation only (tessellated display geometry).
#
# Usage:
#   render_views.sh CAD_VERSION [CAD_DIR] [OUT_ROOT]
#     CAD_VERSION  e.g. v3.4.1 (files: CAD_DIR/assembly/ENGINE_<v>_neutral.glb, CAD_DIR/BOM_<v>.json)
#     CAD_DIR      default /home/claude/work/mechanical/engine/03-cad   (read only)
#     OUT_ROOT     default <07-datasheet>/build/renders
#   Environment overrides: GLB=..., BOM=..., PX (long side, default 1600), SPP (default 64),
#   FAMILY_PX (default 900), FAMILY_SPP (default 48), VIEWS (comma list), THREADS (default 2),
#   PYLIB (extra PYTHONPATH for Blender's Python, default the session pylib312 if present).
# Output: OUT_ROOT/<CAD_VERSION>/<view>.png + <view>_meta.json + render_manifest.json
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DS_ROOT="$(dirname "$HERE")"
V="${1:?CAD version, e.g. v3.4.1}"
CAD_DIR="${2:-/home/claude/work/mechanical/engine/03-cad}"
OUT_ROOT="${3:-$DS_ROOT/build/renders}"
GLB="${GLB:-$CAD_DIR/assembly/ENGINE_${V}_neutral.glb}"
BOM="${BOM:-$CAD_DIR/BOM_${V}.json}"
PX="${PX:-1600}"; SPP="${SPP:-64}"; FAMILY_PX="${FAMILY_PX:-900}"; FAMILY_SPP="${FAMILY_SPP:-48}"
THREADS="${THREADS:-2}"
NICE="${NICE:-15}"; export NICE
DEFAULT_PYLIB=/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/pylib312
PYLIB="${PYLIB:-$DEFAULT_PYLIB}"
for f in "$GLB" "$BOM"; do [ -f "$f" ] || { echo "missing input: $f" >&2; exit 2; }; done
OUT="$OUT_ROOT/$V"
mkdir -p "$OUT"

# Families present in this BOM (one render each), then the assembly views.
FAMS=$(/opt/engine-venv/bin/python -I -c "
import json,sys
b=json.load(open(sys.argv[1]))
fs=[]
for l in b['lines']:
    p=l['pn'].split('-'); f=p[1] if len(p)>2 else p[0]
    if l.get('groups')!='lock' and f not in fs: fs.append(f)
print(','.join('family:'+f for f in fs))" "$BOM")
VIEWS="${VIEWS:-iso,front,side,section,layout,$FAMS}"

export PYTHONPATH="$PYLIB"
LOG="$OUT/render_log.txt"
: > "$LOG"
START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
IFS=',' read -ra VV <<< "$VIEWS"
for v in "${VV[@]}"; do
  SECONDS=0
  # one Blender thread whenever a CalculiX solver of any agent is running (lead brief rule)
  T="$THREADS"; if pgrep ccx >/dev/null 2>&1; then T=1; fi
  echo "view $v threads $T nice $NICE $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT/render_times.txt"
  nice -n "$NICE" blender -b -t "$T" -P "$HERE/render_views_blender.py" -- \
      --glb "$GLB" --bom "$BOM" --out-dir "$OUT" --views "$v" \
      --px "$PX" --spp "$SPP" --family-px "$FAMILY_PX" --family-spp "$FAMILY_SPP" >> "$LOG" 2>&1 \
    || { echo "blender failed on view $v (see $LOG)" >&2; exit 3; }
  echo "$v ${SECONDS}s" | tee -a "$OUT/render_times.txt"
done
END=$(date -u +%Y-%m-%dT%H:%M:%SZ)

/opt/engine-venv/bin/python -I - "$OUT" "$V" "$GLB" "$BOM" "$START" "$END" "$PX" "$SPP" "$FAMILY_PX" "$FAMILY_SPP" "$THREADS" "$HERE/render_views_blender.py" <<'EOF'
import json, sys, os, glob, hashlib
out, v, glb, bom, start, end, px, spp, fpx, fspp, thr, script = sys.argv[1:13]
def h16(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''): h.update(c)
    return h.hexdigest()[:16]
views = []
for m in sorted(glob.glob(os.path.join(out, '*_meta.json'))):
    d = json.load(open(m))
    png = os.path.join(out, d['png'])
    views.append({'view': d['view'], 'png': d['png'], 'png_sha256_16': h16(png) if os.path.exists(png) else None,
                  'res': d['res'], 'render_s': d.get('render_s'), 'glb_sha256_16': d['glb_sha256_16']})
man = {'cad_version': v, 'glb': glb, 'glb_sha256_16': h16(glb), 'bom': bom, 'bom_sha256_16': h16(bom),
       'started_utc': start, 'finished_utc': end,
       'settings': {'px': int(px), 'spp': int(spp), 'family_px': int(fpx), 'family_spp': int(fspp),
                    'threads': int(thr), 'nice': int(os.environ.get('NICE', '15')), 'engine': 'Blender Cycles CPU, no denoiser'},
       'script': 'gen/render_views_blender.py', 'script_sha256_16': h16(script),
       'note': 'Visualisation only: tessellated display geometry from the GLB; not a drawing, tolerance or fabrication source.',
       'views': views}
json.dump(man, open(os.path.join(out, 'render_manifest.json'), 'w'), indent=1)
print('render_manifest.json:', len(views), 'views')
EOF
