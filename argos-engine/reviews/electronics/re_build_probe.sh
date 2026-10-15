#!/bin/bash
# REV-ELEC-1: build the reviewer SIL probe against COPIES of the published v2.9 firmware (hub 06-electronics/firmware is never modified).
#   base   : unchanged core (as published)
#   bpc1   : config.h with kBpc1Shown = true (the post-B-PC-1 configuration: floor 2.0 bar abs, baseline check 0.4 bar)
#   a5off  : config.h with the A5 threshold moved out of reach (1e9 Pa) - shows what the late-light starts do without A5
# Usage: re_build_probe.sh <scratch_dir>
set -euo pipefail
HUB_FW=/home/claude/work/shared-fallback/engine/06-electronics/firmware
HERE=$(cd "$(dirname "$0")" && pwd)
S=${1:?scratch dir}
mkdir -p "$S"
for v in base bpc1 a5off; do
  rm -rf "$S/fw_$v"; mkdir -p "$S/fw_$v"
  cp -r "$HUB_FW/src" "$HUB_FW/sil" "$S/fw_$v/"
  case $v in
    bpc1)  sed -i 's/^constexpr bool kBpc1Shown = false;/constexpr bool kBpc1Shown = true; /' "$S/fw_$v/src/core/config.h"
           grep -q '^constexpr bool kBpc1Shown = true;' "$S/fw_$v/src/core/config.h" ;;
    a5off) sed -i 's/^constexpr float kIgnHoldOverPAbs_Pa = 8.0e5f;/constexpr float kIgnHoldOverPAbs_Pa = 1.0e9f;/' "$S/fw_$v/src/core/config.h"
           grep -q '^constexpr float kIgnHoldOverPAbs_Pa = 1.0e9f;' "$S/fw_$v/src/core/config.h" ;;
  esac
  ( cd "$S/fw_$v" && nice -n 10 g++ -std=c++17 -O2 -Wall -Wextra -Wno-unused-parameter -Isrc/core -Isil -DECU_SIL_TEST_HOOKS \
      -o "$S/re_sil_probe_$v" "$HERE/re_sil_probe.cpp" sil/sim.cpp sil/plant.cpp src/core/control.cpp src/core/engine_ecu.cpp \
      src/core/protocol.cpp src/core/sensor_scale.cpp )
  sha256sum "$S/fw_$v/src/core/config.h" | cut -c1-16 | sed "s/^/$v config.h sha256\/16 /"
done
