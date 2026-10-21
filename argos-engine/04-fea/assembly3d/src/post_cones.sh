#!/bin/bash
# fea3d 2026-10-19: post each F2 cone pose (post_s3d.py) as soon as its solve has a DONE marker; one at a time, nice 10.
cd /home/claude/work/fea3d
export FEA3D_CAD=v351
LOG=logs/post_cones.log
for p in neutral alpha+ alpha- beta+ beta- combined045 combined135 combined225 combined315; do
  r=pose_${p}_c71
  until [ -f runs/$r/DONE ] || grep -q "end $r rc=[1-9]" runs/chain_C.log; do sleep 20; done
  if [ -f runs/$r/DONE ] && [ ! -f results/s3d_$r.json ]; then
    echo "$(date -u +%FT%TZ) post $r" >> $LOG
    nice -n 10 /opt/engine-venv/bin/python -B scripts/post_s3d.py $r >> logs/post_s3d_$r.log 2>&1
    echo "$(date -u +%FT%TZ) end post $r rc=$?" >> $LOG
  fi
done
echo "$(date -u +%FT%TZ) post_cones done" >> $LOG
