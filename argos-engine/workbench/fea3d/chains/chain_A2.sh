#!/bin/bash
# fea3d chain A2 (2026-10-13, replaces chain A before it started): modal (60 modes, Pc transducer ASSUMED 26 g), FA-1 state,
# neutral hinge/angular/actuator steps, 8 stop poses and 9 cone poses (engine pressure parts at level 2).
# One heavy solve at a time (sequential), nice 15, ccx memory cap 6 GB in ccxrun.
cd /home/claude/work/fea3d
export FEA3D_CAD=v351 FEA3D_THREADS=2
PY="nice -n 15 /opt/engine-venv/bin/python -I -B -u scripts/run_f1.py"
LOG=runs/chain_A2.log
echo "$(date -u +%FT%TZ) start chain A2" >> $LOG
run() {  # name level state args...
  local name=$1; shift
  if [ -f runs/$name/DONE ]; then echo "$(date -u +%FT%TZ) skip $name (DONE)" >> $LOG; return; fi
  echo "$(date -u +%FT%TZ) run $name $*" >> $LOG
  $PY $name "$@" >> runs/$name.log 2>&1
  local rc=$?
  echo "$(date -u +%FT%TZ) end $name rc=$rc" >> $LOG
  if [ $rc -eq 0 ]; then
    for f in runs/$name/*/f1.inp; do [ -f "$f" ] && gzip -f "$f"; done
    for f in runs/$name/*/f1.dat; do [ -f "$f" ] && [ $(stat -c %s "$f") -gt 2000000 ] && gzip -f "$f"; done
    touch runs/$name/DONE
  fi
}
run modal_v351 1.0 B1_21.65 steps=FREQ60
run fa1_v351 1.0 A1_22.2
run nx_v351 1.0 B1_21.65 steps=EAX,EAY,R1,R2
for d in 000 045 090 135 180 225 270 315; do
  run pose_stop$d 1.0 B1_21.65 posename=stop$d coarse=2 steps=OP,GX,GY,GZ,EAX,EAY,R1,R2,BUMP
done
for p in neutral alpha+ alpha- beta+ beta- combined045 combined135 combined225 combined315; do
  run pose_$p 1.0 B1_21.65 posename=$p coarse=2 steps=OP,GX,GY,GZ,EAX,EAY,R1,R2
done
echo "$(date -u +%FT%TZ) chain A2 done" >> $LOG
