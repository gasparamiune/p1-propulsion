#!/bin/bash
# Combustion v2.4 RC-07 (GNC 62 m records, staging_v3.1): regression-band corners and the B1 gating-rule boundary cases.
# Two lanes (<= 2 CPU-bound processes), each sequential; separate summary files per lane (merged afterwards).
H=/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/duty_cycles
IDX=$H/duty_cycles_records_b1_62m_v3.1.json
OUT=/home/claude/work/combustion/data/v2
PY=/opt/engine-venv/bin/python
SRC=/home/claude/work/combustion/src/run_dispersed_v2p4.py
LOG=/home/claude/work/combustion/logs/run_62m_queue.log
ERR=/home/claude/work/combustion/logs/run_62m_queue.err
run() {  # lane file tag band n extra...
  lane=$1; f=$2; t=$3; b=$4; n=$5; shift 5
  echo "=== $(date -u +%FT%TZ) lane$lane start $t a$b n$n $*" >> $LOG
  nice -n 5 $PY -I $SRC --dc $H/$f --tag $t --band $b --n $n --index $IDX --out $OUT --sub dc_gncv31_62m/lane$lane --no-bc "$@" > /dev/null 2>> $ERR
  echo "=== $(date -u +%FT%TZ) lane$lane end $t a$b n$n rc=$?" >> $LOG
}
P=DC-B1_hop_62m_disp_p99_kest2_v3.csv; M=DC-B1_hop_62m_disp_max_kest2_v3.csv
PT=DC-B1_hop_62m_disp_p99_kest2_tg711_v3.csv; MT=DC-B1_hop_62m_disp_max_kest2_tg711_v3.csv
laneA() {
  for bn in "1.5 0.35" "1.375 0.35" "1.25 0.35" "1.5 0.5" "1.65 0.5" "1.0 0.35" "1.0 0.5"; do
    set -- $bn
    run A $P DC-B1v31_62m_p99 $1 $2
    run A $M DC-B1v31_62m_max $1 $2
  done
}
laneB() {
  for bn in "1.5 0.35" "1.375 0.35" "1.25 0.35" "1.5 0.5" "1.65 0.5" "1.0 0.35"; do
    set -- $bn
    run B $PT DC-B1v31_62m_p99_tg711 $1 $2 --throat-growth
    run B $MT DC-B1v31_62m_max_tg711 $1 $2 --throat-growth
  done
}
echo "=== $(date -u +%FT%TZ) queue start" >> $LOG
laneA & PA=$!
laneB & PB=$!
wait $PA $PB
echo "=== $(date -u +%FT%TZ) ALL DONE" >> $LOG
