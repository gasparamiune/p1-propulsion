#!/bin/bash
# Mechanical compute slot runner (2026-10-12). Lead rule: at most 2 concurrent solver processes, OMP_NUM_THREADS 2 in total.
# One runner per slot (slot 0 -> core 0, slot 1 -> core 1); each job is one bash file in slot<N>/pending, run in name order,
# one at a time, pinned to the slot's core with OMP_NUM_THREADS=1. Optional first arg after core: a PID to wait for before starting.
# Stop: touch slot<N>/STOP (the runner exits when idle or after the current job).
SLOT=$1; CORE=$2; WAITPID=$3
Q=/home/claude/work/mechanical/runs/queue/slot$SLOT
mkdir -p $Q/pending $Q/running $Q/done $Q/failed
echo "$(date +%F' '%T) runner slot $SLOT core $CORE pid $$ waitpid ${WAITPID:-none}" >> $Q/runner.log
if [ -n "$WAITPID" ]; then while kill -0 $WAITPID 2>/dev/null; do sleep 15; done; fi
echo "$(date +%F' '%T) start processing" >> $Q/runner.log
while [ ! -f $Q/STOP ]; do
  J=$(ls $Q/pending/*.sh 2>/dev/null | sort | head -1)
  if [ -z "$J" ]; then sleep 20; continue; fi
  B=$(basename $J .sh)
  mv $J $Q/running/$B.sh
  echo "$(date +%F' '%T) START $B" >> $Q/runner.log
  OMP_NUM_THREADS=1 taskset -c $CORE bash $Q/running/$B.sh > $Q/running/$B.log 2>&1
  RC=$?
  if [ $RC -eq 0 ]; then D=done; else D=failed; fi
  mv $Q/running/$B.sh $Q/running/$B.log $Q/$D/
  echo "$(date +%F' '%T) END $B rc $RC -> $D" >> $Q/runner.log
done
echo "$(date +%F' '%T) STOP seen, exit" >> $Q/runner.log
