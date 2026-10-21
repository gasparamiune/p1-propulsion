#!/bin/sh
# v2.12 rebuild after the ARM static term (sequential, nice 15, single process at a time)
F=/home/claude/work/electronics/firmware; B=/dev/shm/elec_v212/build; L=/dev/shm/elec_v212
FL="-std=c++17 -O2 -Wall -Wextra -Wno-unused-parameter -I$F/src/core -I$F/sil"
CORE="$F/src/core/control.cpp $F/src/core/engine_ecu.cpp $F/src/core/protocol.cpp $F/src/core/sensor_scale.cpp"
date -u +%Y-%m-%dT%H:%M:%SZ > $L/build2.start
nice -n 15 g++ $FL -DECU_SIL_TEST_HOOKS -o $B/test_core $F/sil/test_core.cpp $CORE > $L/build2_tc.txt 2>&1 || { echo FAIL_tc > $L/build2.done; exit 1; }
nice -n 15 $B/test_core > $L/test_core_run3.txt 2>&1; echo "tc exit $?" >> $L/build2_tc.txt
nice -n 15 g++ $FL -o $B/test_core_nohooks $F/sil/test_core.cpp $CORE > $L/build2_tcn.txt 2>&1 || { echo FAIL_tcn > $L/build2.done; exit 1; }
nice -n 15 $B/test_core_nohooks > $L/test_core_nohooks_run2.txt 2>&1; echo "tcn exit $?" >> $L/build2_tcn.txt
nice -n 15 g++ $FL -DECU_SIL_TEST_HOOKS -o $B/sil $F/sil/sil_main.cpp $F/sil/sim.cpp $CORE $F/sil/plant.cpp > $L/build2_sil.txt 2>&1 || { echo FAIL_sil > $L/build2.done; exit 1; }
nice -n 15 g++ $FL -DECU_SIL_TEST_HOOKS -DECU_BPC1_SHOWN_VARIANT -o $B/sil_bpc1 $F/sil/sil_main.cpp $F/sil/sim.cpp $CORE $F/sil/plant.cpp > $L/build2_silb.txt 2>&1 || { echo FAIL_silb > $L/build2.done; exit 1; }
date -u +%Y-%m-%dT%H:%M:%SZ > $L/build2.done
