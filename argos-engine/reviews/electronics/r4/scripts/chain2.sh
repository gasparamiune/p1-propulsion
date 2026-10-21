#!/bin/bash
# REV-ELEC-4 reviewer chain 2: waits for chain1 to end, then (1) the probe, (2) the reviewer SIL variant build, (3) F3 and E1-timing runs.
# One process at a time, nice 15, single thread.
L=/dev/shm/rev_elec4/run/chain2_log.txt
st() { echo "$1 rc $2 $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L; }
echo "wait $(date -u +%Y-%m-%dT%H:%M:%SZ)" > $L
while ! grep -q '^end ' /dev/shm/rev_elec4/run/chain1_log.txt; do sleep 20; done
echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L
FW=/dev/shm/rev_elec4/fw
nice -n 15 g++ -std=c++17 -O2 -Wall -Wextra -Wno-unused-parameter -I$FW/src/core -I$FW/sil -DECU_SIL_TEST_HOOKS \
  /dev/shm/rev_elec4/scripts/probe_v212.cpp $FW/src/core/control.cpp $FW/src/core/engine_ecu.cpp $FW/src/core/protocol.cpp $FW/src/core/sensor_scale.cpp \
  -o /dev/shm/rev_elec4/probe_v212 > /dev/shm/rev_elec4/run/probe_build_log.txt 2>&1; st probe_build $?
nice -n 15 /dev/shm/rev_elec4/probe_v212 > /dev/shm/rev_elec4/run/probe_v212_out.txt 2>&1; st probe_run $?
nice -n 15 make -C /dev/shm/rev_elec4/fw_rv -j1 build/sil > /dev/shm/rev_elec4/run/rv/build_rv_log.txt 2>&1; st rv_build $?
B=/dev/shm/rev_elec4/fw_rv/build/sil
mkdir -p /dev/shm/rev_elec4/run/rv/f3 /dev/shm/rev_elec4/run/rv/csv
RV_STAND_ONLY=1 RV_T0=24 RV_KS="2,3" RV_COMPS="rv_m5_tcm:-0.05:-0.30;rv_m5_tc0:-0.05:0;rv_m4_tcm:-0.04:-0.30;rv_m3_tcm:-0.03:-0.30;rv_p5_tcp:0.05:0.30" \
  nice -n 15 $B s13t /dev/shm/rev_elec4/run/rv/f3 > /dev/shm/rev_elec4/run/rv/f3/S13T_rv_f3_log.txt 2>&1; st rv_f3 $?
S13T_ONLY=stand_after_B1_GVHI_T0_24C_comp_s+1_k1.0_unlit nice -n 15 $B s13t /dev/shm/rev_elec4/run/rv/csv > /dev/shm/rev_elec4/run/rv/csv/stand_log.txt 2>&1; st rv_csv_stand $?
S13T_ONLY=A1_flight_T0_20C_comp_s+1_k3.0_unlit nice -n 15 $B s13t /dev/shm/rev_elec4/run/rv/csv > /dev/shm/rev_elec4/run/rv/csv/a1_log.txt 2>&1; st rv_csv_a1 $?
echo "end $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L
