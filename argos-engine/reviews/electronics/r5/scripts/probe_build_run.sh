#!/bin/sh
# REV-ELEC-5: pause the SIL chain between items, then build and run the probe (default, B-PC-1-shown, hold-disabled control), nice 15, sequential
R=/dev/shm/rev_elec5/run; FW=/dev/shm/rev_elec5/fw; P=/dev/shm/rev_elec5/scripts/probe_v213.cpp; B=/dev/shm/rev_elec5/probe
mkdir -p $B
touch $R/pause.req
while [ ! -f $R/paused ] && [ ! -f $R/chain.done ]; do sleep 2; done
echo "probe start $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $R/probe.log
FL="-std=c++17 -O2 -Wall -Wextra -Wno-unused-parameter -I$FW/src/core -I$FW/sil -DECU_SIL_TEST_HOOKS"
CORE_OTHER="$FW/src/core/control.cpp $FW/src/core/protocol.cpp $FW/src/core/sensor_scale.cpp"
nice -n 15 g++ $FL -o $B/probe_def $P $CORE_OTHER $FW/src/core/engine_ecu.cpp > $R/probe_build_def.txt 2>&1; echo "build def rc $?" >> $R/probe.log
nice -n 15 g++ $FL -DECU_BPC1_SHOWN_VARIANT -o $B/probe_bpc1 $P $CORE_OTHER $FW/src/core/engine_ecu.cpp > $R/probe_build_bpc1.txt 2>&1; echo "build bpc1 rc $?" >> $R/probe.log
nice -n 15 g++ $FL -DREV5_NO_HOLD -o $B/probe_nohold $P $CORE_OTHER /dev/shm/rev_elec5/fw_nohold/src/core/engine_ecu.cpp > $R/probe_build_nohold.txt 2>&1; echo "build nohold rc $?" >> $R/probe.log
nice -n 15 $B/probe_def > $R/probe_v213_def_out.txt 2>&1; echo "run def rc $? $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $R/probe.log
nice -n 15 $B/probe_bpc1 > $R/probe_v213_bpc1_out.txt 2>&1; echo "run bpc1 rc $? $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $R/probe.log
nice -n 15 $B/probe_nohold > $R/probe_v213_nohold_out.txt 2>&1; echo "run nohold rc $? $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $R/probe.log
rm -f $R/pause.req
echo "probe done $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $R/probe.log
