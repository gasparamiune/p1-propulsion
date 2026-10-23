#!/bin/sh
# REV-ELEC-5: write MANIFEST_REV-ELEC-5.sha256 (full sha256, paths relative to reviews/electronics/r5) over every file in the folder but the manifest
R5=/home/claude/work/shared-fallback/engine/reviews/electronics/r5
( cd_dummy=1; find "$R5" -type f ! -name MANIFEST_REV-ELEC-5.sha256 -printf '%P\n' | LC_ALL=C sort | while read -r p; do printf '%s  %s\n' "$(sha256sum "$R5/$p" | cut -d' ' -f1)" "$p"; done ) > "$R5/MANIFEST_REV-ELEC-5.sha256"
wc -l "$R5/MANIFEST_REV-ELEC-5.sha256"
