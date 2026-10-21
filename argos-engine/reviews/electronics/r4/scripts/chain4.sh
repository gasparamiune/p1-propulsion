#!/bin/bash
# REV-ELEC-4 reviewer chain 4: (1) E4-01 CSV timing of selected false-E2 cases, (2) probe B build + run, (3) the v2.11 record commands not
# run in chain1 (part B), on the rebuilt v2.12 binaries. Sequential, one process at a time, nice 15, single thread.
L=/dev/shm/rev_elec4/run/chain4_log.txt
st() { echo "$1 rc $2 $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L; }
echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ)" > $L
BR=/dev/shm/rev_elec4/fw_rv/build/sil
O=/dev/shm/rev_elec4/run/rv/tcs_csv
CA="tcm30:0:-30:22.125;tcm15:0:-15:22.125;tcm8:0:-8:22.125;tcm5:0:-5:22.125;tcm3:0:-3:22.125;tcp90r:0:90:22.30"
X=/dev/shm/rev_elec4/scripts/csv_tlm_extract.py
for nm in A1_flight_T0_20C_tcm8_s+1_k3.0_unlit A1_flight_T0_20C_tcm30_s+1_k3.0_unlit A1_flight_T0_20C_tcm30_s+1_k1.0_unlit A1_flight_T0_20C_tcm30_s+1_k3.0_lit; do
  S13T_ONLY=$nm RV_T0=20 RV_KS="1,3" RV_COMPS="$CA" nice -n 15 $BR s13t $O > $O/${nm}_log.txt 2>&1; st csv_$nm $?
  nice -n 15 python3 -I $X $O/S13T_${nm}.csv $O/${nm}_extract2.json 22.0 > /dev/null 2>&1; st extract2_$nm $?
  rm -f $O/S13T_${nm}.csv
done
FW=/dev/shm/rev_elec4/fw
nice -n 15 g++ -std=c++17 -O2 -Wall -Wextra -Wno-unused-parameter -I$FW/src/core -I$FW/sil -DECU_SIL_TEST_HOOKS \
  /dev/shm/rev_elec4/scripts/probe_v212b.cpp $FW/src/core/control.cpp $FW/src/core/engine_ecu.cpp $FW/src/core/protocol.cpp $FW/src/core/sensor_scale.cpp \
  -o /dev/shm/rev_elec4/probe_v212b > /dev/shm/rev_elec4/run/probe_b_build_log.txt 2>&1; st probe_b_build $?
nice -n 15 /dev/shm/rev_elec4/probe_v212b > /dev/shm/rev_elec4/run/probe_v212b_out.txt 2>&1; st probe_b_run $?
# part B remainder (sil_v2p11_runmap.json command forms, as chain1)
B=/dev/shm/rev_elec4/fw/build
R=/dev/shm/rev_elec4/run/rec
mkdir -p $R/S13 $R/S14 $R/S15 $R/S16 $R/S17 $R/probeF
nice -n 15 $B/sil s6r $R > $R/S6R_log.txt 2>&1; st s6r $?
nice -n 15 $B/sil rccost $R > $R/S6C_log.txt 2>&1; st rccost $?
nice -n 15 $B/sil coast206 $R/S16 > $R/S16/S16_run_log.txt 2>&1; st coast206 $?
nice -n 15 $B/sil r2hold $R/S17 > $R/S17/S17_run_log.txt 2>&1; st r2hold $?
nice -n 15 $B/sil r2v2 $R > $R/S17v2_log.txt 2>&1; st r2v2 $?
nice -n 15 $B/sil v210 $R/S14 > $R/S14/S14_run_log.txt 2>&1; st v210 $?
nice -n 15 $B/sil_bpc1 ignruleb $R/S13 > $R/S13/S13B_ext_bpc1_true_run_log.txt 2>&1; st ignruleb $?
nice -n 15 $B/sil probef $R/probeF > $R/probeF/probeF_run_log.txt 2>&1; st probef $?
nice -n 15 $B/sil startmc $R/S15 300 > $R/S15/S15_run_log.txt 2>&1; st startmc $?
echo "end $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L
