#!/bin/bash
# REV-ELEC-4 reviewer chain 3 (E4 F2 SIL confirmation): seat-TC reading step after E1 (unlit -> false E2?) and in RUN (lit), reviewer SIL
# variant fw_rv (author's v2.12 code + RV_* case selection only). Sequential, one process at a time, nice 15, single thread.
L=/dev/shm/rev_elec4/run/chain3_log.txt
st() { echo "$1 rc $2 $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L; }
echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ)" > $L
B=/dev/shm/rev_elec4/fw_rv/build/sil
O=/dev/shm/rev_elec4/run/rv
mkdir -p $O/tcs_stand $O/tcs_a1 $O/tcs_csv
CS="tcm55:0:-55:22.125;tcm20:0:-20:22.125;tcm10:0:-10:22.125;tcm6:0:-6:22.125;tcp90r:0:90:22.30"
CA="tcm30:0:-30:22.125;tcm15:0:-15:22.125;tcm8:0:-8:22.125;tcm5:0:-5:22.125;tcm3:0:-3:22.125;tcp90r:0:90:22.30"
RV_STAND_ONLY=1 RV_T0=24 RV_KS="1,3" RV_COMPS="$CS" nice -n 15 $B s13t $O/tcs_stand > $O/tcs_stand/S13T_tcs_stand_log.txt 2>&1; st tcs_stand $?
RV_T0=20 RV_KS="1,3" RV_COMPS="$CA" nice -n 15 $B s13t $O/tcs_a1 > $O/tcs_a1/S13T_tcs_a1_log.txt 2>&1; st tcs_a1 $?
X=/dev/shm/rev_elec4/scripts/csv_tlm_extract.py
for spec in "A1_flight_T0_20C_tcm8_s+1_k3.0_unlit|20|$CA" "stand_after_B1_GVHI_T0_24C_tcm20_s+1_k1.0_unlit|24|$CS" "A1_flight_T0_20C_tcp90r_s+1_k3.0_lit|20|$CA" "A1_flight_T0_20C_tcm8_s-1_k3.0_lit|20|$CA"; do
  nm=${spec%%|*}; rest=${spec#*|}; t0=${rest%%|*}; comps=${rest#*|}
  S13T_ONLY=$nm RV_T0=$t0 RV_KS="1,3" RV_COMPS="$comps" nice -n 15 $B s13t $O/tcs_csv > $O/tcs_csv/${nm}_log.txt 2>&1; st csv_$nm $?
  nice -n 15 python3 -I $X $O/tcs_csv/S13T_${nm}.csv $O/tcs_csv/${nm}_extract.json 21.9 > /dev/null 2>&1; st extract_$nm $?
  rm -f $O/tcs_csv/S13T_${nm}.csv
done
echo "end $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L
