#!/bin/bash
# REV-ELEC-2: compare every file of the reviewer SIL re-runs with the author's record (06-electronics/results/sil_v2p10), by sha256.
# Usage: compare_rerun_vs_record.sh <scratch out dir> <record dir>
OUT="$1"; REC="$2"
for d in r2hold aborts startmc mc probef v210 coast206 bleed ignruleb_base ignruleb_bpc1 test_core; do
  [ -d "$OUT/$d" ] || continue
  for f in "$OUT/$d"/*; do
    b=$(basename "$f")
    case "$b" in stdout.txt|time.txt) continue;; esac
    m=$(find "$REC" -name "$b" -type f | head -1)
    hs=$(sha256sum "$f" | cut -c1-16)
    if [ -z "$m" ]; then echo "NO-RECORD $d/$b $hs"; continue; fi
    hr=$(sha256sum "$m" | cut -c1-16)
    if [ "$hs" = "$hr" ]; then echo "IDENTICAL $d/$b $hs ${m#$REC/}"; else echo "DIFFERENT $d/$b $hs vs ${m#$REC/} $hr"; fi
  done
done
