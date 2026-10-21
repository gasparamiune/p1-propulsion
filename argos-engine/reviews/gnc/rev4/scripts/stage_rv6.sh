#!/bin/bash
# REV-GNC-6: copy the reviewer scripts, results, logs and re-flown tables to hub reviews/gnc/rev4/ and write the
# manifest (sha256sum format, paths relative to reviews/gnc/rev4). Writes only under reviews/gnc/rev4/.
set -euo pipefail
S=/tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv6
D=/home/claude/work/shared-fallback/engine/reviews/gnc/rev4
mkdir -p $D/scripts $D/results/refly $D/results/refly_full $D/logs $D/tables
cp $S/scripts/{rv6lib.py,guard_run.py,env6.sh,env7.sh,v01_p2_band.py,v02_dcrit_duty.py,v03_refly4.py,v03_run.sh,v03_full.sh,v04_items.py,v05_eng11_env.py,v07_extra.py,v08_eng11_fly.py,v09_fe_plant.py,stage_rv6.sh} $D/scripts/
cp $S/res/{v01_p2_band.json,v02_dcrit_duty.json,v04_items.json,v05_eng11_env.json,v07_extra.json,v08_eng11_fly.json,v09_fe_plant.json} $D/results/
cp $S/out/refly/*.json $D/results/refly/
cp $S/out/refly_full/*.json $D/results/refly_full/
cp $S/out/r2s/r2_starve.json $D/results/r2_starve_refly_tree7.json
cp $S/out/refly_full/*.csv.gz $D/tables/
cp $S/logs/{v01.log,v02.log,v03_case.log,v03_ref.log,v03_full_case.log,v03_full_ref.log,v03_tree_path_diff.out,v04.log,v05.log,v06_r2s.log,v06_tree7_path_diff.out,v07.log,v08.log,v09.log} $D/logs/
cd $D
rm -f MANIFEST_REV-GNC-6.sha256
find . -type f ! -name MANIFEST_REV-GNC-6.sha256 | sed 's#^\./##' | sort | xargs sha256sum > MANIFEST_REV-GNC-6.sha256
sha256sum -c MANIFEST_REV-GNC-6.sha256 | grep -vc ": OK$" || true
wc -l < MANIFEST_REV-GNC-6.sha256
du -sh $D
