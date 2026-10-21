#!/bin/bash
# usage: run_r3.sh <label> <variants> <outdir> [KS list]
# v2 (REV-GNC-7, 2026-10-21T09:5xZ, time box): label remap, installed by atomic mv while master_q.sh runs (running copies keep
# the old inode): d_r3_b3b runs the band-end corners R3Lo_JLO,R3Hi_JHI before R3C_JC; d_r3_b4g runs the (c) A02 / B07 edge
# reproductions and the rest of C01 (bending x 0.9) before R3G_JC (the later run_repro.sh calls in master_q.sh then find every row done and only reload).
W=/dev/shm/rev_gnc7
V="$2"
case "$1" in
  d_r3_b3b) V="R3Lo_JLO,R3Hi_JHI,R3C_JC" ;;
  d_r3_b4g)
    $W/scripts/run_repro.sh c_edgeA02 A02 $W/out/c_repro_A02e 105,110,125,130
    $W/scripts/run_repro.sh c_edgeB07 B07 $W/out/c_repro_B07e 90,95,115,120,145,150
    $W/scripts/run_repro.sh c_full_r C01 $W/out/c_repro ;;
esac
source $W/scripts/env7.sh
export RV7_VARIANTS="$V" GNC_E11FE_OUT="$3" GNC_E11FE_PART=none
[ -n "$4" ] && export RV7_KS="$4"
mkdir -p "$3"
LOG=$W/logs/$1.log
echo "== $(date -u +%Y-%m-%dT%H:%M:%SZ) start $1: rv7_eng11_r3 variants=$V out=$3 KS=${4:-default}" >> $LOG
nice -n 10 /opt/engine-venv/bin/python -I $W/scripts/guard_run.py $W/tree/scripts/rv7_eng11_r3.py >> $LOG 2>&1
rc=$?
echo "EXIT $rc $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $LOG
