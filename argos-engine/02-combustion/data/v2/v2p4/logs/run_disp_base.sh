#!/bin/bash
# Combustion v2.4: dispersed GNC v3 duty cycles, base (no throat growth) - sequential, one process at a time
H=/home/claude/work/shared-fallback/engine/01-systems-gnc/duty_cycles
IDX=$H/duty_cycles_index_v3.json
OUT=/home/claude/work/combustion/data/v2
cd /home/claude/work/combustion/src
for pair in "DC-B1_hop_85m_disp_p99_kest2_v3.csv DC-B1v3p99" "DC-B1_hop_85m_disp_max_kest2_v3.csv DC-B1v3max" "DC-A1_full_flight_disp_p99_kest2_v3.csv DC-A1dispp99"; do
  set -- $pair
  echo "=== $(date -u +%FT%TZ) start $2"
  nice -n 5 /opt/engine-venv/bin/python -I run_dispersed_v2p4.py --dc $H/$1 --tag $2 --index $IDX --out $OUT
  echo "=== $(date -u +%FT%TZ) end $2 rc=$?"
done
