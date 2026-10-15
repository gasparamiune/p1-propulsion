#!/bin/bash
# Combustion v2.4, REV-GNC-1 RG-03 (relayed 2026-10-13): oxidiser-rich corners of the regression band on the GNC v3.1 62 m
# records (a x0.6 and x0.8; n 0.35 / 0.5 / 0.68), with and without throat growth. Two lanes (<= 2 CPU-bound processes).
H=/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/duty_cycles
IDX=$H/duty_cycles_records_b1_62m_v3.1.json
OUT=/home/claude/work/combustion/data/v2
PY=/opt/engine-venv/bin/python
RDV=/home/claude/work/combustion/src/run_dispersed_v2p4.py
LOG=/home/claude/work/combustion/logs/run_62m_queue3.log
ERR=/home/claude/work/combustion/logs/run_62m_queue3.err
P=DC-B1_hop_62m_disp_p99_kest2_v3.csv; M=DC-B1_hop_62m_disp_max_kest2_v3.csv
PT=DC-B1_hop_62m_disp_p99_kest2_tg711_v3.csv; MT=DC-B1_hop_62m_disp_max_kest2_tg711_v3.csv
rd() {  # lane file tag band n extra...
  lane=$1; f=$2; t=$3; b=$4; n=$5; shift 5
  echo "=== $(date -u +%FT%TZ) lane$lane start RD $t a$b n$n $*" >> $LOG
  nice -n 5 $PY -I $RDV --dc $H/$f --tag $t --band $b --n $n --index $IDX --out $OUT --sub dc_gncv31_62m/lane$lane --no-bc "$@" > /dev/null 2>> $ERR
  echo "=== $(date -u +%FT%TZ) lane$lane end RD $t a$b n$n rc=$?" >> $LOG
}
laneE() {
  rd E $P DC-B1v31_62m_p99 0.6 0.35
  rd E $P DC-B1v31_62m_p99 0.6 0.5
  rd E $P DC-B1v31_62m_p99 0.6 0.68
  rd E $P DC-B1v31_62m_p99 0.8 0.5
  rd E $PT DC-B1v31_62m_p99_tg711 0.6 0.68 --throat-growth
  rd E $MT DC-B1v31_62m_max_tg711 0.8 0.5 --throat-growth
}
laneF() {
  rd F $M DC-B1v31_62m_max 0.6 0.35
  rd F $M DC-B1v31_62m_max 0.6 0.5
  rd F $M DC-B1v31_62m_max 0.6 0.68
  rd F $M DC-B1v31_62m_max 0.8 0.5
  rd F $MT DC-B1v31_62m_max_tg711 0.6 0.35 --throat-growth
  rd F $MT DC-B1v31_62m_max_tg711 0.6 0.68 --throat-growth
}
echo "=== $(date -u +%FT%TZ) queue3 start" >> $LOG
laneE & PE=$!
laneF & PF=$!
wait $PE $PF
echo "=== $(date -u +%FT%TZ) ALL DONE" >> $LOG
