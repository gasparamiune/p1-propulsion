#!/bin/bash
# REV-ELEC-4 chain 5 (E4-01 scope): is the FIRST start exposed too? Seat-TC step after the first-start E1 (A1 pad first start, stand B1
# first start), reviewer SIL variant fw_rv. Waits for chain4 to end. Sequential, nice 15, single thread.
L=/dev/shm/rev_elec4/run/chain5_log.txt
st() { echo "$1 rc $2 $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L; }
echo "wait $(date -u +%Y-%m-%dT%H:%M:%SZ)" > $L
while ! grep -q '^end ' /dev/shm/rev_elec4/run/chain4_log.txt; do sleep 15; done
echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L
BR=/dev/shm/rev_elec4/fw_rv/build/sil
O=/dev/shm/rev_elec4/run/rv/fs; mkdir -p $O
X=/dev/shm/rev_elec4/scripts/first_start_extract.py
run1() {  # name T0 comps
  S13T_ONLY=$1 RV_T0=$2 RV_KS="1,3" RV_COMPS="$3" nice -n 15 $BR s13t $O > $O/$1_log.txt 2>&1; st csv_$1 $?
  nice -n 15 python3 -I $X $O/S13T_$1.csv $O/$1_fs.json 0.0 8.0 > /dev/null 2>&1; st fs_$1 $?
  rm -f $O/S13T_$1.csv
}
run1 A1_flight_T0_20C_fs0_s+1_k3.0_lit 20 "fs0:0:0:99"
run1 stand_after_B1_GVHI_T0_24C_fs0_s+1_k1.0_lit 24 "fs0:0:0:99"
EA=$(python3 -I -c "import json; print(json.load(open('$O/A1_flight_T0_20C_fs0_s+1_k3.0_lit_fs.json'))['E1_s'])")
ES=$(python3 -I -c "import json; print(json.load(open('$O/stand_after_B1_GVHI_T0_24C_fs0_s+1_k1.0_lit_fs.json'))['E1_s'])")
TA=$(python3 -I -c "print(round($EA + 0.004, 4))"); TS=$(python3 -I -c "print(round($ES + 0.004, 4))")
echo "first-start E1 A1 $EA step $TA; stand $ES step $TS" >> $L
CA="fsm8:0:-8:$TA;fsm30:0:-30:$TA"; CS="fsm8:0:-8:$TS;fsm20:0:-20:$TS"
run1 A1_flight_T0_20C_fsm8_s+1_k3.0_lit 20 "$CA"
run1 A1_flight_T0_20C_fsm30_s+1_k3.0_lit 20 "$CA"
run1 A1_flight_T0_20C_fsm30_s+1_k1.0_lit 20 "$CA"
run1 stand_after_B1_GVHI_T0_24C_fsm20_s+1_k1.0_lit 24 "$CS"
run1 stand_after_B1_GVHI_T0_24C_fsm8_s+1_k3.0_lit 24 "$CS"
echo "end $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L
