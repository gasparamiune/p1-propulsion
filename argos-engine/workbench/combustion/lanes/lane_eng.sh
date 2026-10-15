#!/bin/bash
# Engine lane: runs one CPU-bound job at a time from queue/ (lowest name first); waits for PID $1 first if given.
# Lead cap 2026-10-12: Combustion runs at most 2 concurrent CPU-bound processes (this lane + the CFD lane).
B=/home/claude/work/combustion/lanes/eng; L=$B/lane.log
log() { echo "$(date -u +%H:%M:%S) $*" >> $L; }
if [ -n "$1" ]; then log "waiting for PID $1"; while kill -0 "$1" 2>/dev/null; do sleep 15; done; log "PID $1 finished"; fi
while [ ! -f $B/STOP ]; do
  j=$(ls $B/queue/*.sh 2>/dev/null | sort | head -1)
  if [ -z "$j" ]; then sleep 10; continue; fi
  n=$(basename $j .sh); log "start $n"
  mv $j $B/done/$n.sh
  taskset -c 0,1 nice -n 5 bash $B/done/$n.sh > $B/logs/$n.log 2>&1
  log "end $n rc=$?"; touch $B/done/$n.finished
done
log "lane stopped"
