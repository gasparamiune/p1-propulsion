#!/bin/bash
# fea3d chain B (successor, 2026-10-15): queue-driven (runs/queue_B.txt, re-read before each run; lines "name level state args...").
# Skips runs with a DONE marker and runs already attempted in this chain (runs/queue_B.attempted). One solve at a time, nice 15.
cd /home/claude/work/fea3d
export FEA3D_CAD=v351 FEA3D_THREADS=2 FEA3D_MEMCAP=8.0
PY="nice -n 15 /opt/engine-venv/bin/python -I -B -u scripts/run_f1.py"
LOG=runs/chain_B.log
Q=runs/queue_B.txt; ATT=runs/queue_B.attempted
touch $ATT
echo "$(date -u +%FT%TZ) start chain B (pid $$)" >> $LOG
run() {  # name level state args...
  local name=$1; shift
  echo "$(date -u +%FT%TZ) run $name $* (df $(df --output=avail -BM / | tail -1))" >> $LOG
  $PY $name "$@" >> runs/$name.log 2>&1
  local rc=$?
  echo "$(date -u +%FT%TZ) end $name rc=$rc" >> $LOG
  if [ $rc -eq 0 ]; then
    for f in runs/$name/*/f1.inp; do [ -f "$f" ] && gzip -f "$f"; done
    for f in runs/$name/*/f1.dat; do [ -f "$f" ] && [ $(stat -c %s "$f") -gt 2000000 ] && gzip -f "$f"; done
    touch runs/$name/DONE
  else
    for f in runs/$name/*/f1.frd; do [ -f "$f" ] && rm -f "$f"; done
  fi
}
while true; do
  next=""
  while read -r line; do
    [ -z "$line" ] && continue
    case "$line" in \#*) continue;; esac
    nm=${line%% *}
    [ -f runs/$nm/DONE ] && continue
    grep -qx "$nm" $ATT && continue
    next="$line"; break
  done < $Q
  [ -z "$next" ] && break
  echo "${next%% *}" >> $ATT
  run $next
done
echo "$(date -u +%FT%TZ) chain B done" >> $LOG
