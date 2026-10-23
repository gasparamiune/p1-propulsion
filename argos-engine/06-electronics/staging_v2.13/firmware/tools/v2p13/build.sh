#!/bin/sh
# v2.13 build in RAM (sequential, nice 15, one process at a time). Arg: list of targets (tc tcn sil silb)
F=/dev/shm/elec_v213/src; B=/dev/shm/elec_v213/build; L=/dev/shm/elec_v213/out
FL="-std=c++17 -O2 -Wall -Wextra -Wno-unused-parameter -I$F/src/core -I$F/sil"
CORE="$F/src/core/control.cpp $F/src/core/engine_ecu.cpp $F/src/core/protocol.cpp $F/src/core/sensor_scale.cpp"
for T in "$@"; do
  date -u +%Y-%m-%dT%H:%M:%SZ > $L/build_$T.start
  case $T in
    tc)  nice -n 15 g++ $FL -DECU_SIL_TEST_HOOKS -o $B/test_core $F/sil/test_core.cpp $CORE > $L/build_tc.txt 2>&1 || { echo FAIL > $L/build_$T.done; exit 1; }
         nice -n 15 $B/test_core $L > $L/test_core_out.txt 2>&1; echo "exit $?" >> $L/build_tc.txt ;;
    tcn) nice -n 15 g++ $FL -o $B/test_core_nohooks $F/sil/test_core.cpp $CORE > $L/build_tcn.txt 2>&1 || { echo FAIL > $L/build_$T.done; exit 1; }
         nice -n 15 $B/test_core_nohooks $L > $L/test_core_nohooks_out.txt 2>&1; echo "exit $?" >> $L/build_tcn.txt ;;
    sil) nice -n 15 g++ $FL -DECU_SIL_TEST_HOOKS -o $B/sil $F/sil/sil_main.cpp $F/sil/sim.cpp $CORE $F/sil/plant.cpp > $L/build_sil.txt 2>&1 || { echo FAIL > $L/build_$T.done; exit 1; } ;;
    silb) nice -n 15 g++ $FL -DECU_SIL_TEST_HOOKS -DECU_BPC1_SHOWN_VARIANT -o $B/sil_bpc1 $F/sil/sil_main.cpp $F/sil/sim.cpp $CORE $F/sil/plant.cpp > $L/build_silb.txt 2>&1 || { echo FAIL > $L/build_$T.done; exit 1; } ;;
  esac
  date -u +%Y-%m-%dT%H:%M:%SZ > $L/build_$T.done
done
