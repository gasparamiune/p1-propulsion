#!/bin/bash
# REV-ELEC-2: reviewer runs after the 3000-run S5 (sequential, ONE heavy process at a time, nice 15 per the lead's load rule).
# 1 S5 tail statistics; 2 R2 probe sanity (no R2PROBE: must reproduce S17_r2hold.json); 3 R2 probe A-E; 4 FA-1 chain (window
# end times vs E2); 5 in-window ride-through probe; 6 transducer-lag sensitivity (tau 1.36 ms); 7 single runs 125 and 127 (TANK_COLD).
S=/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rev_elec2
H=/home/claude/work/shared-fallback/engine
PY=/opt/engine-venv/bin/python
ENV=$H/02-combustion/data/v2p4a/fa1_envelope_v2p4a.json
LOG=$S/out/after_mc_times.txt
tm() {  # name, then the command
  local name=$1; shift
  local t0=$(date +%s.%N)
  "$@"
  local rc=$?
  local t1=$(date +%s.%N)
  echo "$name rc=$rc wall $(echo "$t1 - $t0" | bc) s" >> $LOG
}
mkdir -p $S/out/r2probe_sanity $S/out/r2probe_all $S/out/fa1b $S/out/inwindow $S/out/tau $S/out/mcone_125 $S/out/mcone_127
cd $S/out || exit 1
tm s5tail nice -n 15 $PY -I $S/s5/s5_tail.py $H/06-electronics/results/sil_v2p10/S5_mc.csv $S/out/mc3000/S5_mc.csv > $S/out/mc3000/s5_tail_log.txt 2>&1
tm r2sanity nice -n 15 $S/fw/build/sil_r2probe r2hold $S/out/r2probe_sanity > $S/out/r2probe_sanity/run_log.txt 2>&1
tm r2all env R2PROBE=all nice -n 15 $S/fw/build/sil_r2probe r2hold $S/out/r2probe_all > $S/out/r2probe_all/probe_stdout.txt 2>&1
tm fa1b nice -n 15 $PY -I $S/fa1/rev_fa1_chain.py $ENV $S/out/fa1b > $S/out/fa1b/run_log.txt 2>&1
tm inwindow nice -n 15 $PY -I $S/fa1/rev_inwindow_probe.py $S/fa1/rev_fa1_chain.py $ENV $S/out/inwindow/rev_inwindow_probe.json > $S/out/inwindow/run_log.txt 2>&1
tm tau nice -n 15 $PY -I $S/fa1/rev_fa1_tau_sens.py $S/fa1/rev_fa1_chain.py $ENV > $S/out/tau/run_log.txt 2>&1
for k in 125 127; do
  tm mcone$k nice -n 15 $S/fw/build/sil mcone $S/out/mcone_$k $k > $S/out/mcone_$k/run_log.txt 2>&1
done
echo ALLDONE >> $LOG
