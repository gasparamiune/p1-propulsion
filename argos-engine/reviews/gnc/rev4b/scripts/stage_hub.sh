#!/bin/bash
# REV-GNC-7: stage the reviewer's scripts, data and logs into the hub review folder and write MANIFEST_REV-GNC-7.sha256.
# Writes only reviews/gnc/rev4b/ (brief). Usage: stage_hub.sh
set -e
W=/dev/shm/rev_gnc7
R=/home/claude/work/shared-fallback/engine/reviews/gnc/rev4b
mkdir -p $R/scripts $R/data/out $R/data/h $R/data/a $R/data/b $R/data/chk $R/logs
cp -p $W/scripts/*.py $W/scripts/*.sh $W/scripts/*.diff $R/scripts/
rm -f $R/scripts/rv7_v32_corrections_v1_draft.py
cp -p $W/tree/scripts/rv7_eng11_r3.py $W/tree/scripts/rv7_repro.py $R/scripts/
for d in d_r3 d_r3_ks58_174 c_repro c_repro_A02e c_repro_B07e; do
  [ -d $W/out/$d ] && mkdir -p $R/data/out/$d && cp -p $W/out/$d/*.json $R/data/out/$d/
done
cp -p $W/h/*.json $R/data/h/
cp -p $W/a/*.json $R/data/a/
cp -p $W/b/rv7_v32_corrections.json $W/b/gnc_v3.2_rv7_trial.json $W/b/t10v3_*.json $W/b/t10v3_*.log $R/data/b/
cp -p $W/chk/*.sha256 $R/data/chk/
cp -p $W/logs/*.log $W/logs/*.sha256 $R/logs/
# no cd (brief): hash by absolute path, write paths relative to reviews/gnc/rev4b/
find $R -type f ! -name MANIFEST_REV-GNC-7.sha256 -printf "%P\n" | LC_ALL=C sort | while read -r f; do sha256sum "$R/$f" | sed "s#  $R/#  #"; done > $R/MANIFEST_REV-GNC-7.sha256
# verify: recompute every listed file and compare
while read -r h f; do [ "$(sha256sum "$R/$f" | cut -d' ' -f1)" = "$h" ] || { echo "MISMATCH $f"; exit 1; }; done < $R/MANIFEST_REV-GNC-7.sha256
echo "MANIFEST OK $(wc -l < $R/MANIFEST_REV-GNC-7.sha256) files"
du -sb $R
