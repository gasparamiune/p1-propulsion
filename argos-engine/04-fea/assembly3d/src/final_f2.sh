#!/bin/bash
# fea3d 2026-10-19: F2 / F3 wrap-up after the 9 cone poses are solved and posted (post_cones.sh). Light posts only, nice 15.
cd /home/claude/work/fea3d || exit 1
LOG=logs/final_f2.log
PY="nice -n 15 /opt/engine-venv/bin/python -I -B"
export FEA3D_CAD=v351
CONES="pose_neutral_c71,pose_alpha+_c71,pose_alpha-_c71,pose_beta+_c71,pose_beta-_c71,pose_combined045_c71,pose_combined135_c71,pose_combined225_c71,pose_combined315_c71"
echo "$(date -u +%FT%TZ) start final_f2" >> $LOG
for p in ${CONES//,/ }; do
  until grep -q "end post $p rc=" logs/post_cones.log; do sleep 15; done
done
echo "$(date -u +%FT%TZ) all cones posted" >> $LOG
$PY scripts/post_k.py $CONES tag=cone_c71 >> $LOG 2>&1; echo "$(date -u +%FT%TZ) post_k rc=$?" >> $LOG
$PY scripts/k_range.py >> $LOG 2>&1; echo "$(date -u +%FT%TZ) k_range rc=$?" >> $LOG
$PY scripts/s3d_summary.py >> $LOG 2>&1; echo "$(date -u +%FT%TZ) s3d_summary rc=$?" >> $LOG
$PY scripts/chart_s3d.py >> $LOG 2>&1; echo "$(date -u +%FT%TZ) chart rc=$?" >> $LOG
$PY scripts/icd_export.py >> $LOG 2>&1; echo "$(date -u +%FT%TZ) icd_export rc=$?" >> $LOG
$PY scripts/margin_matrix.py >> $LOG 2>&1; echo "$(date -u +%FT%TZ) margin_matrix rc=$?" >> $LOG
$PY scripts/lc3_bound.py lc1_run=lc1v351_c71 poses=$CONES envpfx=s3d_env_ out=_s3d >> $LOG 2>&1; echo "$(date -u +%FT%TZ) lc3_bound s3d rc=$?" >> $LOG
echo "$(date -u +%FT%TZ) end final_f2" >> $LOG
