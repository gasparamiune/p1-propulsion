#!/bin/bash
# usage: run_repro.sh <label> <variants> <outdir> [KS list]
W=/dev/shm/rev_gnc7
source $W/scripts/env7.sh
export RV7_VARIANTS="$2" GNC_E11FE_OUT="$3" GNC_E11FE_PART=none
unset RV7_KS; [ -n "$4" ] && export RV7_KS="$4"
mkdir -p "$3"
LOG=$W/logs/$1.log
echo "== $(date -u +%Y-%m-%dT%H:%M:%SZ) start $1: rv7_repro variants=$2 out=$3 KS=${4:-default}" >> $LOG
nice -n 10 /opt/engine-venv/bin/python -I $W/scripts/guard_run.py $W/tree/scripts/rv7_repro.py >> $LOG 2>&1
echo "EXIT $? $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $LOG
