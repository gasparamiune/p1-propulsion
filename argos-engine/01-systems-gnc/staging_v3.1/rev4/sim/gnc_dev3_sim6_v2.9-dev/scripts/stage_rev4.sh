#!/bin/bash
# stage_rev4.sh v1.0 (GNC rev4, 2026-10-19): copy the rev4 evidence to the hub staging folder staging_v3.1/rev4/ and write
# MANIFEST_rev4.sha256 (sha256sum format, paths relative to rev4/) and NOT_STAGED_rev4.txt. Writes only under rev4/.
# rev1/rev2/rev2p1/rev2p2/rev3 are never touched. __pycache__ / numba caches are excluded (regenerated on import).
# rev4_notes/ (live PROGRESS note) is outside the manifest by design.
set -euo pipefail
SP=/home/claude/work/space
R4=/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev4
case "$R4" in */staging_v3.1/rev4) ;; *) echo "bad target"; exit 2;; esac
mkdir -p "$R4"
cp_tree() {  # src dst : copy a tree without caches
  mkdir -p "$2"
  tar -C "$1" -cf - --exclude=__pycache__ --exclude='*.nbi' --exclude='*.nbc' --exclude='*.pyc' --exclude='*.lock' . | tar -C "$2" -xf -
}
# evidence outputs (JSON, compressed tables, npz, logs); withdrawn markers go to their own folder
rm -rf "$R4/out_rev4" "$R4/withdrawn_markers" "$R4/sim" "$R4/pins"
mkdir -p "$R4/out_rev4"
tar -C "$SP/out/rev4" -cf - --exclude=./wmark --exclude='*.lock' . | tar -C "$R4/out_rev4" -xf -
cp_tree "$SP/out/rev4/wmark" "$R4/withdrawn_markers"
# simulator trees (gncsim + scripts) and their shared data
for pair in "gnc_dev3:gnc_dev3_sim6_v2.9-dev" "gnc_dev4:gnc_dev4_sim6_v2.10" "gnc_dev5:gnc_dev5_sim6_v2.11" "gnc_dev7:gnc_dev7_sim6_v2.13-dev"; do
  src=${pair%%:*}; dst=${pair##*:}
  cp_tree "$SP/$src/gncsim" "$R4/sim/$dst/gncsim"
  cp_tree "$SP/$src/scripts" "$R4/sim/$dst/scripts"
  echo "data -> ../data (work area: $SP/$src/data -> $(readlink -f $SP/$src/data))" > "$R4/sim/$dst/DATA_LINK.txt"
done
cp_tree "$(readlink -f $SP/gnc_dev3/data)" "$R4/sim/data"
for d in iface_v3c iface_v351 iface_v352 iface_v352L; do cp_tree "$SP/$d" "$R4/sim/$d"; done
echo "WITHDRAWN (lead CHANGELOG 209: realised v3.5.2 saving -91.6 g, not the -0.31 kg lever estimate): the v352L interface set and pins_rev4_v352L are staged as record only; no arm was flown on them." > "$R4/sim/iface_v352L/WITHDRAWN.txt"
cp_tree "$SP/pins_rev4" "$R4/pins/pins_rev4"
# not staged list (work-area caches only)
{
  echo "# GNC rev4: work-area files NOT copied to the hub (caches regenerated on import). sha256  size_bytes  path"
  for t in gnc_dev3 gnc_dev4 gnc_dev5 gnc_dev7; do
    find "$SP/$t/gncsim" "$SP/$t/scripts" \( -name '*.nbi' -o -name '*.nbc' -o -name '*.pyc' \) -type f -print0 | sort -z | \
      xargs -0 -r -I{} sh -c 'printf "%s  %s  %s\n" "$(sha256sum "$1" | cut -d" " -f1)" "$(stat -c %s "$1")" "$1"' _ {}
  done
} > "$R4/NOT_STAGED_rev4.txt"
# manifest (everything under rev4/ except the manifest itself and rev4_notes/)
TMPM=$SP/out/stage_rev4_manifest.tmp
rm -f "$R4/MANIFEST_rev4.sha256" "$R4/MANIFEST_rev4.sha256.tmp"
( cd "$R4" && find . -type f ! -path './MANIFEST_rev4.sha256' ! -path './rev4_notes/*' -print0 | sort -z | xargs -0 sha256sum ) > "$TMPM"
mv "$TMPM" "$R4/MANIFEST_rev4.sha256"
( cd "$R4" && sha256sum -c --quiet MANIFEST_rev4.sha256 ) && echo "MANIFEST OK $(wc -l < "$R4/MANIFEST_rev4.sha256") files"
du -sh "$R4"
sha256sum "$R4/MANIFEST_rev4.sha256"
