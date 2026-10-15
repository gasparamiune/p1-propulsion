#!/bin/bash
# Combustion v2.4 RC-06/RC-07: (a, n) band on the GNC v3 dispersed cycles + B2 v2 - one process, sequential
H=/home/claude/work/shared-fallback/engine/01-systems-gnc/duty_cycles
IDX=$H/duty_cycles_index_v3.json
OUT=/home/claude/work/combustion/data/v2
cd /home/claude/work/combustion/src
run() {  # file tag band n extra...
  f=$1; t=$2; b=$3; n=$4; shift 4
  echo "=== $(date -u +%FT%TZ) start $t a$b n$n $*"
  nice -n 5 /opt/engine-venv/bin/python -I run_dispersed_v2p4.py --dc $H/$f --tag $t --band $b --n $n --out $OUT --sub dc_gncv3_band "$@" > /dev/null 2>> /home/claude/work/combustion/logs/run_band_queue.err
  echo "=== $(date -u +%FT%TZ) end $t a$b n$n rc=$?"
}
# priority: the web corners first (a x1.5 with n 0.35), then the rest
for spec in \
 "DC-B1_hop_85m_disp_p99_kest2_tg711_v3.csv DC-B1v3p99_tg711 --index $IDX --throat-growth" \
 "DC-B1_hop_85m_disp_p99_kest2_v3.csv DC-B1v3p99 --index $IDX" \
 "DC-B1_hop_85m_disp_max_kest2_v3.csv DC-B1v3max --index $IDX" \
 "DC-B1_hop_85m_disp_max_kest2_tg711_v3.csv DC-B1v3max_tg711 --index $IDX --throat-growth" \
 "DC-B2_hop_50m_floor20_v2.csv DC-B2v2 --index /nonexistent_use_baseline_tank" \
 "DC-A1_full_flight_disp_p99_kest2_v3.csv DC-A1dispp99 --index $IDX" \
 "DC-A1_full_flight_disp_p99_kest2_tg711_v3.csv DC-A1dispp99_tg711 --index $IDX --throat-growth"; do
  set -- $spec; f=$1; t=$2; shift 2
  run $f $t 1.5 0.35 "$@"
done
for spec in \
 "DC-B1_hop_85m_disp_p99_kest2_tg711_v3.csv DC-B1v3p99_tg711 --index $IDX --throat-growth" \
 "DC-B1_hop_85m_disp_p99_kest2_v3.csv DC-B1v3p99 --index $IDX" \
 "DC-B1_hop_85m_disp_max_kest2_v3.csv DC-B1v3max --index $IDX" \
 "DC-B2_hop_50m_floor20_v2.csv DC-B2v2 --index /nonexistent_use_baseline_tank" \
 "DC-A1_full_flight_disp_p99_kest2_v3.csv DC-A1dispp99 --index $IDX" \
 "DC-A1_full_flight_disp_p99_kest2_tg711_v3.csv DC-A1dispp99_tg711 --index $IDX --throat-growth"; do
  set -- $spec; f=$1; t=$2; shift 2
  for bn in "1.0 0.35" "1.5 0.5" "1.5 0.68" "1.0 0.5" "1.0 0.68" "0.6 0.35" "0.6 0.5" "0.6 0.68"; do
    set -- $bn; b=$1; n=$2
    run $f $t $b $n ${spec#* * }
  done
done
for bn in "1.0 0.35" "1.5 0.5"; do set -- $bn; run DC-B1_hop_85m_disp_max_kest2_tg711_v3.csv DC-B1v3max_tg711 $1 $2 --index $IDX --throat-growth; done
echo "=== $(date -u +%FT%TZ) ALL DONE"
