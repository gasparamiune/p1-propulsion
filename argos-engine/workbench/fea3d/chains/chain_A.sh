#!/bin/bash
# fea3d chain A (2026-10-13): modal, FA-1 state, neutral hinge/angular steps, 8 stop poses (coarse engine), 9 cone poses (coarse engine).
# One heavy solve at a time (sequential), nice 15, ccx memory cap 6 GB in ccxrun.  Waits for the LC1 v3.5.1 job to finish first.
cd /home/claude/work/fea3d
export FEA3D_CAD=v351 FEA3D_THREADS=2
PY="nice -n 15 /opt/engine-venv/bin/python -I -B -u scripts/run_f1.py"
LOG=runs/chain_A.log
while ! grep -q "^EXIT" runs/lc1v351_design_rigid.log 2>/dev/null; do sleep 30; done
echo "$(date -u +%FT%TZ) start chain A" >> $LOG
run() {  # name level state args...
  local name=$1; shift
  if [ -f runs/$name/DONE ]; then echo "$(date -u +%FT%TZ) skip $name (DONE)" >> $LOG; return; fi
  echo "$(date -u +%FT%TZ) run $name $*" >> $LOG
  $PY $name "$@" >> runs/$name.log 2>&1
  local rc=$?
  echo "$(date -u +%FT%TZ) end $name rc=$rc" >> $LOG
  if [ $rc -eq 0 ]; then
    for f in runs/$name/*/f1.inp; do [ -f "$f" ] && gzip -f "$f"; done
    touch runs/$name/DONE
  fi
}
run modal_v351 1.0 B1_21.65 steps=FREQ30
run fa1_v351 1.0 A1_22.2
run nx_v351 1.0 B1_21.65 steps=EAX,EAY,R1,R2
for d in 000 045 090 135 180 225 270 315; do
  run pose_stop$d 1.0 B1_21.65 posename=stop$d coarse=2 steps=OP,GX,GY,GZ,EAX,EAY,R1,R2,BUMP
done
for p in neutral alpha+ alpha- beta+ beta- combined045 combined135 combined225 combined315; do
  run pose_$p 1.0 B1_21.65 posename=$p coarse=2 steps=OP,GX,GY,GZ,EAX,EAY,R1,R2
done
echo "$(date -u +%FT%TZ) chain A done" >> $LOG
