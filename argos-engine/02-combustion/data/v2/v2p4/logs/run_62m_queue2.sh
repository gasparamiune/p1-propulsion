#!/bin/bash
# Combustion v2.4 RC-07 (GNC 62 m records): nominal-law burn limit (a x1.1, n 0.35) and axial-law sensitivity (law 'total')
# for the gating-rule check, plus one law-'ox' reproduction check of run_dispersed_v2p4 (p99_tg711 a1.375 n0.35).
# Two lanes (<= 2 CPU-bound processes), each sequential; separate summary files per lane sub-directory.
H=/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/duty_cycles
IDX=$H/duty_cycles_records_b1_62m_v3.1.json
OUT=/home/claude/work/combustion/data/v2
PY=/opt/engine-venv/bin/python
RDV=/home/claude/work/combustion/src/run_dispersed_v2p4.py
AX=/home/claude/work/combustion/src/b1_62m_axial_v2p4.py
LOG=/home/claude/work/combustion/logs/run_62m_queue2.log
ERR=/home/claude/work/combustion/logs/run_62m_queue2.err
P=DC-B1_hop_62m_disp_p99_kest2_v3.csv; M=DC-B1_hop_62m_disp_max_kest2_v3.csv
PT=DC-B1_hop_62m_disp_p99_kest2_tg711_v3.csv; MT=DC-B1_hop_62m_disp_max_kest2_tg711_v3.csv
rd() {  # lane file tag band n extra...
  lane=$1; f=$2; t=$3; b=$4; n=$5; shift 5
  echo "=== $(date -u +%FT%TZ) lane$lane start RD $t a$b n$n $*" >> $LOG
  nice -n 5 $PY -I $RDV --dc $H/$f --tag $t --band $b --n $n --index $IDX --out $OUT --sub dc_gncv31_62m/lane$lane --no-bc "$@" > /dev/null 2>> $ERR
  echo "=== $(date -u +%FT%TZ) lane$lane end RD $t a$b n$n rc=$?" >> $LOG
}
ax() {  # lane file tag band n law extra...
  lane=$1; f=$2; t=$3; b=$4; n=$5; law=$6; shift 6
  echo "=== $(date -u +%FT%TZ) lane$lane start AX $t a$b n$n law$law $*" >> $LOG
  nice -n 5 $PY -I $AX --dc $H/$f --tag $t --band $b --n $n --law $law --index $IDX --out $OUT --sub dc_gncv31_62m/laneT$lane "$@" > /dev/null 2>> $ERR
  echo "=== $(date -u +%FT%TZ) lane$lane end AX $t a$b n$n law$law rc=$?" >> $LOG
}
laneC() {
  ax C $PT DC-B1v31_62m_p99_tg711 1.375 0.35 ox --throat-growth
  rd C $P DC-B1v31_62m_p99 1.1 0.35
  rd C $M DC-B1v31_62m_max 1.1 0.35
  ax C $PT DC-B1v31_62m_p99_tg711 1.375 0.35 total --throat-growth
  ax C $PT DC-B1v31_62m_p99_tg711 1.65 0.5 total --throat-growth
}
laneD() {
  rd D $PT DC-B1v31_62m_p99_tg711 1.1 0.35 --throat-growth
  rd D $MT DC-B1v31_62m_max_tg711 1.1 0.35 --throat-growth
  ax D $MT DC-B1v31_62m_max_tg711 1.375 0.35 total --throat-growth
  ax D $PT DC-B1v31_62m_p99_tg711 1.1 0.35 total --throat-growth
  ax D $MT DC-B1v31_62m_max_tg711 1.1 0.35 total --throat-growth
}
echo "=== $(date -u +%FT%TZ) queue2 start (waits for queue1 ALL DONE)" >> $LOG
while ! grep -q "ALL DONE" /home/claude/work/combustion/logs/run_62m_queue.log; do sleep 5; done
laneC & PC=$!
laneD & PD=$!
wait $PC $PD
echo "=== $(date -u +%FT%TZ) ALL DONE" >> $LOG
