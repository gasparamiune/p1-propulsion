CLAIM
- No v2.10 change exists in the firmware, SIL, hardware, BOM or the hub.
- One unverified script fix in the workdir (the gnc v3 lookup in make_interface_json_v2.py).
- v2.9 remains the latest built and tested state: test_core 287/0, SIL record results/sil_v2p9.

CONFIGURATION
- Workdir /home/claude/work/electronics: firmware v2.9, unchanged.
- Hub: v2.9 as published; REV-ELEC-1 hold respected.

FILES
- Changed: calc/make_interface_json_v2.py (the lookup fix and the OI-GNC-V3 removal from item 3). Not run.

CODE MAP FOR v2.10 (for the next session)
- **Item 1, A5 deletion:**
  - config.h lines 302-306: kIgnHoldOverPAbs_Pa 8.0e5, kIgnHoldOverPTime_s 0.005.
  - config.h line 326: a static_assert ties the A7 start-band top to the A5 limit. It has to be rewritten when A5 goes.
  - engine_ecu.cpp lines 763-764: the p_ihold_ check that aborts HARD_START. This becomes the LIGHT_SPIKE log/EVENT, with raw and filtered peak, time above 8 and above 30 bar abs, and time from the light.
  - Tests to update: test_v28 (19)(a)/(b), and test_v29 groups that expect A5.
- **Item 2, the 30 bar abort:**
  - config.h line 273: kPcOverPressureTime_s = 0.003. Its comment says the persistence runs on the filtered 1 kHz Pc.
  - engine_ecu.cpp line 748 uses pc_abs. It is unverified whether that is the raw or the filtered value; check it before changing the constant to 5 ms.
  - The comparator-first proof on S6 throat_blocked comes from the S6 aborts JSON fields inj_to_hw_comparator_trip_s and cause. v2.9: HW_OVERPRESSURE at +8 ms.
- **A HARD_START source that stays after A5 is deleted:** engine_ecu.cpp line 1162. A Pc sensor voltage at or above 4.75 V (about 74 bar g) in IGNITION aborts HARD_START. Decide whether that remains.
- **Item 4:** riseTrack in engine_ecu.cpp (the drogue-support function just above startMonitors). b7 uses rise_now_, which is filtered AND raw. Add a filtered-only term for RISE_HELD/RISE_HELD_T; E2 keeps both channels. Test (25)/(26) need updating.
- **Items 3 and 5:** need inspection of monitors() (engine_ecu.cpp about 718-890) and the pc_sensor_ok_ assignment.

ANSWERS TO ITEM 5 (only the parts I can confirm from the v2.9 code; the rest must be verified)
- **TLM_FAST behaviour:**
  - d2-d3 = 0xFFFF exactly when Outputs::pc_valid is false.
  - pc_valid is set from pc_sensor_ok_ (engine_ecu.cpp line ~1354).
  - The d1 state nibble and b4 (E2, from det::LIT) do not depend on pc_valid, so they stay valid while d2-d3 = 0xFFFF.
  - b5 and b6 drop on the first invalid tick: riseTrack requires pc_sensor_ok_. So b6 clears for the rest of the start, and b7 cannot latch after that tick.
  - This matches your interim FC rule: release at E2 + 0.10 s on state RUN with an invalid Pc.
- **A3 and A7:** they run in startMonitors, which is called only with the Pc channel valid. They are therefore suspended while Pc is invalid. The source comment says this; I did not re-read the call site this session.
- **Not verified this session:**
  - every condition that sets pc_sensor_ok_ false. Known from config: the transducer voltage window 0.25-4.75 V and the +5V_SNS excitation window. Whether an A7 trip also sets it is unknown;
  - whether flight RUN switches the Pc loop to open loop (fault::OPEN_LOOP) on a PC_SENSOR fault;
  - therefore whether item 3 needs the E2 to E2 + 0.45 s blanking of the START high side.

ITEMS 6, 7, 9 (not started)
- **Item 7:** the SIL plant already adds the bleed in parallel. It draws mdot_hb from the tank separately, and the shared line loss uses (mox + mdot_hb). The ~1 g/s injector drop seen in v2.9 is that shared line loss. Producing the flow-split evidence is still open.
- **Item 6:** the purge cap of 2.5 + 0.3 s conflicts with the current kPurgeHoldMax_s 2.0 s hold. Today a pre-scheduled purge can keep the valves open up to 4.5 s. This must change in v2.10.
- **Item 6 also needs:**
  - "closure not confirmed → relight proceeds + BLEED_FAULT to the FC" (today it aborts at E0 + 0.15 s);
  - a hardware inhibit of the bleed drivers outside the purge window;
  - new 12 V peak-and-hold valve candidates (seat ≥ 2 mm or Kv at 55 bar), TO-QUOTE to DK-6400.
- **Item 9:** the GSE anemometer BOM row.

TESTS
- None run for v2.10.

UNKNOWNS
- Listed under ANSWERS TO ITEM 5 and the code map above.

NEXT CLOSURE
- Fresh session: items 1, 2 and 4 first (small, and they decide S6), then 3/5 after inspecting monitors().
- Then 6 and 7, then 8 (finish the generator v1-path fix), then 9.
- Then test_core, S5/S6/S11/S12/S13, ERC and the netlist check.
- I will report "workdir build ready" only after those pass.
