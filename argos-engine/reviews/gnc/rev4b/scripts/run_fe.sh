#!/bin/bash
# usage: run_fe.sh <label> <script> <part> <variants> <outdir>
W=/dev/shm/rev_gnc7
source $W/scripts/env7.sh
export GNC_E11FE_PART="$3" GNC_E11FE_VARIANTS="$4" GNC_E11FE_OUT="$5"
mkdir -p "$5"
LOG=$W/logs/$1.log
echo "== $(date -u +%Y-%m-%dT%H:%M:%SZ) start $1: $2 part=$3 variants=$4 out=$5" >> $LOG
nice -n 10 /opt/engine-venv/bin/python -I $W/scripts/guard_run.py "$2" >> $LOG 2>&1
rc=$?
echo "EXIT $rc $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $LOG
