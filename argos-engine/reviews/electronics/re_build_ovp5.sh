#!/bin/bash
# REV-ELEC-1 probe F: does the lead's CHANGELOG l.160 item (2) change of the 30 bar firmware abort persistence (3 -> 5 ms) remove the
# S5 run-127 PC_OVERPRESSURE abort, and how long do the S5 high-overshoot runs stay above 30 bar abs?
# Builds the UNCHANGED SIL (sil_main.cpp) from COPIES of the published v2.9 sources:
#   base    : as published (kPcOverPressureTime_s = 0.003 on the FILTERED Pc, engine_ecu.cpp l.748)
#   ovp5    : kPcOverPressureTime_s = 0.005, channel unchanged (filtered)
#   ovp5raw : kPcOverPressureTime_s = 0.005 and the check moved to the RAW zeroed Pc (in.pc_Pa - pc_zero_ + pamb), the wording of l.160 (2)
# Then runs 'sil mcone <out> k' for the S5 runs with plant Pc max >= 29.5 bar abs. Hub sources are never modified.
# Usage: re_build_ovp5.sh <scratch_dir> [variant ...]   (default: base ovp5 ovp5raw)
set -euo pipefail
HUB_FW=/home/claude/work/shared-fallback/engine/06-electronics/firmware
S=${1:?scratch dir}; shift || true
VARIANTS=${*:-"base ovp5 ovp5raw"}
mkdir -p "$S"
for v in $VARIANTS; do
  rm -rf "$S/fwF_$v"; mkdir -p "$S/fwF_$v"
  cp -r "$HUB_FW/src" "$HUB_FW/sil" "$S/fwF_$v/"
  if [ "$v" = ovp5 ] || [ "$v" = ovp5raw ]; then
    sed -i 's/^constexpr float kPcOverPressureTime_s = 0.003f;/constexpr float kPcOverPressureTime_s = 0.005f;/' "$S/fwF_$v/src/core/config.h"
    grep -q '^constexpr float kPcOverPressureTime_s = 0.005f;' "$S/fwF_$v/src/core/config.h"
  fi
  if [ "$v" = ovp5raw ]; then
    sed -i 's/p_hard_.step(pc_abs > kPcOverPressureAbs_Pa, kPcOverPressureTime_s, dt)/p_hard_.step(in.pc_Pa - pc_zero_ + pamb_Pa > kPcOverPressureAbs_Pa, kPcOverPressureTime_s, dt)/' \
      "$S/fwF_$v/src/core/engine_ecu.cpp"
    grep -q 'p_hard_.step(in.pc_Pa - pc_zero_ + pamb_Pa > kPcOverPressureAbs_Pa' "$S/fwF_$v/src/core/engine_ecu.cpp"
  fi
  ( cd "$S/fwF_$v" && nice -n 10 g++ -std=c++17 -O2 -Wall -Wextra -Wno-unused-parameter -Isrc/core -Isil -DECU_SIL_TEST_HOOKS \
      -o "$S/sil_$v" sil/sil_main.cpp sil/sim.cpp src/core/control.cpp src/core/engine_ecu.cpp src/core/protocol.cpp \
      src/core/sensor_scale.cpp sil/plant.cpp )
  sha256sum "$S/fwF_$v/src/core/config.h" "$S/fwF_$v/src/core/engine_ecu.cpp" | cut -c1-16 | sed "s/^/$v config.h, engine_ecu.cpp sha256\/16 /"
  mkdir -p "$S/outF_$v"
  for k in 12 92 107 127 140 174 215 281 283 286 290; do
    nice -n 10 "$S/sil_$v" mcone "$S/outF_$v" "$k" | grep '^S5 run' | sed "s/^/$v /"
  done
done
