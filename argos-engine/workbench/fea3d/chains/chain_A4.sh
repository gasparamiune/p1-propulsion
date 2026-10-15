#!/bin/bash
# fea3d chain A4 (2026-10-13): replaces chain A3 after its modal deck failed again (ccx add_sm_st: MASS element on an MPC-dependent
# node; fixed: point masses on independent nodes + SPRING2 links).  Waits for the running nx_v351 python (PID $1), closes it, then:
# modal (OP, PM static at T_REF + 60 modes, Pc transducer ASSUMED 26 g), 8 stop poses, 9 cone poses (engine pressure parts at level 2).
cd /home/claude/work/fea3d
export FEA3D_CAD=v351 FEA3D_THREADS=2
PY="nice -n 15 /opt/engine-venv/bin/python -I -B -u scripts/run_f1.py"
LOG=runs/chain_A4.log
echo "$(date -u +%FT%TZ) start chain A4 (waiting for PID $1)" >> $LOG
while kill -0 $1 2>/dev/null; do sleep 20; done
if grep -q "extracted" runs/nx_v351.log && [ -f runs/nx_v351/B1_21.65/fields.npz ]; then
  gzip -f runs/nx_v351/B1_21.65/f1.inp; touch runs/nx_v351/DONE; echo "$(date -u +%FT%TZ) nx_v351 closed (DONE)" >> $LOG
else
  echo "$(date -u +%FT%TZ) nx_v351 NOT complete" >> $LOG
fi
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
run modal_v351 1.0 B1_21.65 steps=OP,PM,FREQ60
run nx_v351 1.0 B1_21.65 steps=EAX,EAY,R1,R2
for d in 000 045 090 135 180 225 270 315; do
  run pose_stop$d 1.0 B1_21.65 posename=stop$d coarse=2 steps=OP,GX,GY,GZ,EAX,EAY,R1,R2,BUMP
done
for p in neutral alpha+ alpha- beta+ beta- combined045 combined135 combined225 combined315; do
  run pose_$p 1.0 B1_21.65 posename=$p coarse=2 steps=OP,GX,GY,GZ,EAX,EAY,R1,R2
done
echo "$(date -u +%FT%TZ) chain A4 done" >> $LOG
