#!/bin/bash
cd /home/claude/work/combustion/src
echo "=== $(date -u +%FT%TZ) abort_cases"
nice -n 5 /opt/engine-venv/bin/python -I abort_cases_v2p4.py /home/claude/work/combustion/data/v2/v2p4 > /home/claude/work/combustion/data/v2/v2p4/abort_cases_run.log 2>&1; echo "rc=$?"
echo "=== $(date -u +%FT%TZ) hard_start"
nice -n 5 /opt/engine-venv/bin/python -I hard_start_v2p4.py /home/claude/work/combustion/data/v2/v2p4 > /home/claude/work/combustion/data/v2/v2p4/hard_start_run.log 2>&1; echo "rc=$?"
H=/home/claude/work/shared-fallback/engine/01-systems-gnc/duty_cycles
for pair in "DC-B1_hop_85m_disp_p99_kest2_v3.csv DC-B1v3p99" "DC-B1_hop_85m_disp_max_kest2_v3.csv DC-B1v3max"; do
  set -- $pair
  echo "=== $(date -u +%FT%TZ) regression $2"
  nice -n 5 /opt/engine-venv/bin/python -I run_dispersed_v2p4.py --dc $H/$1 --tag $2 --index $H/duty_cycles_index_v3.json --out /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/regtest_v3 > /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/regtest_v3/$2.log 2>&1; echo "rc=$?"
done
echo "=== $(date -u +%FT%TZ) done"
