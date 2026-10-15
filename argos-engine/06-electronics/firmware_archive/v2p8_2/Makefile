# ARGOS engine ECU firmware - native SIL build (g++). v2.8.2 (2026-10-13; v2.8.1, v2.8 and v2.7 same day). The Teensy HAL and its PlatformIO project are NOT written yet
# (open item); 'make arm' cross-compiles the platform-independent core for the Cortex-M7 (Teensy 4.1 FPU ABI) as a
# compile and size check only.
CXX ?= g++
CXXFLAGS ?= -std=c++17 -O2 -Wall -Wextra -Wno-unused-parameter -Isrc/core -Isil
CORE = src/core/control.cpp src/core/engine_ecu.cpp src/core/protocol.cpp src/core/sensor_scale.cpp
PLANT = sil/plant.cpp
ENGINE_ROOT ?= /mnt/project-files/engine
# while the shared mount is down (2026-10-12): make ENGINE_ROOT=/home/claude/work/shared-fallback/engine
PY ?= /opt/engine-venv/bin/python
OUT ?= ../results/sil

all: build/sil build/test_core

# v2.5: all generated headers (engine_params.h, valve_map_table.h from Combustion's throttle_map_v2.csv, plant_tables.h,
# gnc_tables.h) come from tools/gen_tables.py (explicit: make tables)
tables: tools/gen_tables.py
	$(PY) tools/gen_tables.py --engine-root $(ENGINE_ROOT)

build/gen_valve_map: sil/gen_valve_map.cpp $(PLANT) sil/plant.h sil/plant_tables.h src/core/control.cpp src/core/valve_map_table.h
	@mkdir -p build
	$(CXX) $(CXXFLAGS) -o $@ sil/gen_valve_map.cpp $(PLANT) src/core/control.cpp

# v2.5: cross-check only (Combustion map vs ECU table vs SIL plant); the v2.1 generator is tools/archive/gen_valve_map_v2p1.cpp
valve_map: build/gen_valve_map
	./build/gen_valve_map $(ENGINE_ROOT)/02-combustion/data/v2/engine_S230/throttle_map_v2.csv 0.025 | tee ../results/valve_map_check_v3.txt

mech: tools/gen_mech_params.py
	$(PY) tools/gen_mech_params.py --engine-root $(ENGINE_ROOT)

# the SIL compiles the unchanged core with ECU_SIL_TEST_HOOKS (adds the test-only switch that disables the firmware
# over-pressure check, so the hardware trip can be shown alone); build/test_core and the Teensy build do not define it
build/sil: sil/sil_main.cpp sil/sim.cpp sil/sim.h $(CORE) $(PLANT) src/core/*.h sil/*.h src/core/valve_map_table.h src/core/n2o_sat_table.h
	@mkdir -p build
	$(CXX) $(CXXFLAGS) -DECU_SIL_TEST_HOOKS -o $@ sil/sil_main.cpp sil/sim.cpp $(CORE) $(PLANT)

# v2.8: ignition-lift derivation in the SIL cold-flow model (firmware default kIgnLiftTab_m until CF-3) -> ../results/ignition_lift_v1.json
build/ign_lift_cal: sil/ign_lift_cal.cpp $(PLANT) sil/plant.h sil/plant_tables.h src/core/config.h
	@mkdir -p build
	$(CXX) $(CXXFLAGS) -o $@ sil/ign_lift_cal.cpp $(PLANT)

ign_lift_cal: build/ign_lift_cal
	./build/ign_lift_cal ../results/ignition_lift_v1.json

# v2.7: transducer ranges + hardware over-pressure trip (070BG, OI-6) -> sil/ovp_hw_params.h (v1 script archived in calc/archive)
ovp: ../calc/pc_transducer_v2.py ../hardware/kicad_gen/ecu_design.py src/core/config.h
	$(PY) ../calc/pc_transducer_v2.py --engine-root $(ENGINE_ROOT)

build/test_core: sil/test_core.cpp sil/test_v27.inc sil/test_v28.inc $(CORE) src/core/*.h src/core/valve_map_table.h
	@mkdir -p build
	$(CXX) $(CXXFLAGS) -o $@ sil/test_core.cpp $(CORE)

test: build/test_core
	./build/test_core

run: build/sil
	@mkdir -p $(OUT)
	nice -n 10 ./build/sil all $(OUT)

ARMCXX ?= arm-none-eabi-g++
ARMFLAGS = -std=c++17 -Os -mcpu=cortex-m7 -mthumb -mfloat-abi=hard -mfpu=fpv5-d16 -fno-exceptions -fno-rtti -Wall -Wextra \
           -Wno-unused-parameter -Wdouble-promotion -Isrc/core
arm: $(CORE) src/core/*.h
	@mkdir -p build/arm
	for f in $(CORE); do $(ARMCXX) $(ARMFLAGS) -c $$f -o build/arm/$$(basename $$f .cpp).o || exit 1; done
	arm-none-eabi-size build/arm/*.o | tee build/arm/size.txt

clean:
	rm -rf build
.PHONY: all test run clean valve_map mech arm ovp tables ign_lift_cal
