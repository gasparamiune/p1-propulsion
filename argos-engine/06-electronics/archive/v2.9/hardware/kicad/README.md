# ARGOS engine ECU: KiCad project (v2.3, 2026-10-13)

**Status:** this is a design schematic. It has not been built and no PCB has been routed. A clean ERC and a matching netlist show that the drawing is self-consistent; they do not validate the hardware.

| Item | Value |
|---|---|
| KiCad version used | **7.0.11** (Ubuntu 24.04 package `7.0.11+dfsg-1build4`), installed with `apt-get install kicad` in the cloud container |
| File format | KiCad 7 (schematic `20230121`, symbol library `20220914`, footprints `20221018`). KiCad 8 and 9 open it and upgrade the format on save. |
| Open with | `argos_ecu.kicad_pro` |
| Sheets | Root plus 8 sub-sheets |
| ERC | **0 errors, 0 warnings** on all 9 sheets (`erc/argos_ecu_erc.rpt`, 2026-10-13 06:56; screenshot `erc/shots/03_erc_result.png`). One test is ignored ("SPICE model issue"), which is also KiCad's default. |
| Netlist cross-check | 424 symbols, 266 nets and 1184 intended pins match the design source pin by pin, with 0 errors and 0 warnings (`erc/netlist_crosscheck.txt`). KiCad exports 1196 pins; the 12 extra pins are no-connect-type library pins, listed as INFO. |
| Grouped component list | 424 symbols in 173 lines, no DNP parts (`argos_ecu_bom_grouped.csv`) |

## What changed from v2.2 to v2.3

v2.2 lagged firmware v2.3 to v2.8.3 and the lead decisions of 2026-10-13. v2.3 draws the hardware that the firmware already assumes.

| Area | Change | Basis |
|---|---|---|
| Pintle rail (new sheet, 8xx) | TPS552882 buck-boost (U801) with **external buck-leg FETs** Q801/Q802 (CSD17578Q5A); L801 XAL1010-472 4.7 uH; a designed COMP network (28.0k / 12 nF / 100 pF); FB 24.9k/4.75k 0.1 % 10 ppm/K; sense resistor R807 12 mOhm; LTC4365 OV/UV disconnect (U802 + Q803); two 220 uF polymer output capacitors; rail current sense U803 INA181A2 | Lead decision on pintle_rail_v3 (CHANGELOG line 62). The external FETs were missing in pintle_rail_v1/v2: the TPS552882 integrates only the boost-leg FETs. |
| PRAIL_OK hardware gate | U306 SN74LVC1G08 makes the MV latch gate `MV_LATCH_GB AND PRAIL_OK`, so an LTC4365 trip drops the MV latch without firmware | Firmware v2.7 rail-loss abort |
| Sensors B (new sheet, 9xx) | Second ADS131M04 (U901) for P_torch 070BG (J901), PRAIL, rail current and PREG. MAX31856 channels TC4 (type K, bore top), TC5 (type T, MSS-1) and TC6 (type T, MSS-2) | Firmware v2.7/v2.8; lead lines 73, 75, 83 |
| SPI chip selects | U203 SN74LVC138 3-to-8 decoder. Address on pins 8/9/10, enable on pin 20 with a 10k pull-up so that nothing is selected in reset. Y0 ADC1, Y1 ADC2, Y2-Y7 TC1-TC6 | Eight SPI0 devices and too few Teensy pins |
| Mode strap | J620 resistor-coded harness strap on A3 (pin 17): FLIGHT 2.27 V, STAND 1.65 V, open 3.30 V, both 1.35 V. The two invalid states refuse ARM. | Lead line 85 |
| Tank-heater interlock | J616 GSE heater permit: Q616 DMN6075S is driven by HTR_PERMIT_DRV through U305 and inhibited in hardware by ARM_PLUG (Q617) and ARM_BUS (Q618). Contact limits are <= 28 V and <= 1 A. | Firmware heater permit (SAFE only) |
| Bay temperature | J614: DS18B20 #3 on a separate 1-Wire connector (ONEWIRE_EXT) | Firmware v2.8 bay-temperature ARM inhibit |
| TVC servo switch | F401 removed. Q401 and Q403 AOD4185 in parallel, sources on VBAT | TVC chain approval (CHANGELOG line 24) |
| Igniter | V12 divider (R501/R502/C503) removed, because the firmware does not read it. TP502 IGN_ISENSE added. | |
| Transducers | Pc and P_torch are M3234-000005-070BG; P_feed and P_tank are M3234-000005-170BG. The OVP divider R332 is set for 31.47 bar g on the 070BG. | Lead line 73 (3); Combustion RC-04 |
| Head-end bleed | **Not drawn.** A DNP provision was drawn in run 1 and then removed: the lead holds the bleed as a fallback only (line 126), and the coordinator asked for no design. | See "Fallback bleed" below |

## Files

| File | Content |
|---|---|
| `argos_ecu.kicad_pro`, `argos_ecu.kicad_sch` | Project file and root sheet (notes and sheet index) |
| `power.kicad_sch` (1xx) | Battery XT60 input, 25 A fuse, battery shunt with INA181, TVS, 5 V TPS54202 buck, LDOs (+3V3A, +3V3_ENC, +5V_SNS), sense dividers, test points |
| `mcu_can.kicad_sch` (2xx) | Teensy 4.1 on sockets, MCP2562FD CAN transceiver, split termination, ESD, U203 chip-select decoder |
| `safety_arming.kicad_sch` (3xx) | XT30 arming plug; fused ARM high-side switch (AOD4185) driven by ARM_REQ AND WD_OK AND OVP_OK; SN74LVC1G123 hardware watchdog; two SN74AHCT244 gate buffers (U304 ARM-gated, U305 SAFE-allowed); hardware Pc over-pressure comparator and latch (U330/U331); U306 PRAIL_OK gate |
| `actuators.kicad_sch` (4xx) | Watchdog-gated TVC servo power switch (Q401 + Q403); four Micro-Fit servo connectors (TVC A/B on the switched VBAT, pintle on PRAIL, MV opener on ARM_BUS); MV-opener reservoir C403 |
| `igniter_valves.kicad_sch` (5xx) | 12 V boost (Pololu U3V70F12) on the ARM bus, spark-coil IGBT driver with a hardware-limited dwell, five low-side solenoid/latch channels, vent solenoid, MV switches |
| `sensors.kicad_sch` (6xx/7xx) | ADC1 ADS131M04 (Pc, P_feed, P_tank, load cell), 2.5 V excitation, MAX31856 TC1-TC3, 1-Wire (tank and bay), NTC, three AS5048A encoder ports, mode strap, heater interlock |
| `pintle_rail.kicad_sch` (8xx) | TPS552882 pintle rail, LTC4365 disconnect, rail current sense |
| `sensors_b.kicad_sch` (9xx) | ADC2 ADS131M04 (P_torch, PRAIL, IPINT, PREG), MAX31856 TC4-TC6 |
| `argos_ecu.kicad_sym` | Project symbol library. It holds flattened copies of the KiCad 7.0.11 stock symbols used, plus custom Teensy41, ADS131M04_PW, Pololu_U3V70F12, TPS552882_RPM and power symbols. The project does not depend on the founder's global libraries. |
| `argos_ecu.pretty/` | Custom footprints: `Teensy41_Socket`, `Pololu_U3V70_WireAttach` (placeholder) and **`TI_RPM0026A_PLACEHOLDER`** (26 pads, marked NOT FOR FABRICATION). All other footprints are KiCad stock footprints. |
| `pin_map_v2p3.csv` | Teensy pin map, written by the generator from the same source |
| `sym-lib-table`, `fp-lib-table` | Project library tables, using `${KIPRJMOD}` paths |
| `argos_ecu_schematic.pdf` | Plot of all 9 sheets |
| `argos_ecu_bom_grouped.csv` | Grouped component list, without prices. The priced BOM is `../../calc/bom_v2.py` -> `../../results/bom_v2.csv`. |
| `intended_netlist.json` | Pin-to-net map written by the generator, used by the cross-check |
| `erc/` | ERC reports, screenshots, the exported netlist, the cross-check results and the v2.3 negative control |

**Connections.** Nets connect through global labels and power symbols. Net names match the signal names in the firmware HAL comments and in `pin_map_v2p3.csv`.

**Units.** Millimetres, on a 1.27 mm connection grid.

**Computed values.** `../../calc/ecu_v2p3_values_v1.py` checks the v2.3 component values. It reads `../kicad_gen/ecu_design.py` and writes `../../results/ecu_v2p3_values_v1.json`. It checks:
- strap levels;
- TPS552882 output, enable, current limit and loop;
- FET losses;
- LTC4365 thresholds;
- ADC2 scaling;
- the heater interlock;
- the CS-decoder truth table;
- a regression of the unchanged OVP and transducer parts.

## HAL rules (the hardware HAL is not yet written)

- **CS decoder.** Set the address on pins 8/9/10 first. Then drive CS_EN_N (pin 20) low and wait >= 1 us before the first SCK edge. This is a DESIGN value, far above the decoder delay of <= 6.7 ns. Raise CS_EN_N before changing the address; never change the address while CS_EN_N is low.
- **ADC2 timing.** ADC2 DRDY goes only to TP901. ADC2 shares the 8.192 MHz clock (ADC_CLK) and SYNC/RESET (ADC_SYNC_N) with ADC1, so ADC2 is read after ADC1's DRDY (pin 7).
- **Mode strap (pin 17).** Decision thresholds are 2.786 / 1.961 / 1.498 V, with a worst margin of 0.136 V. OPEN and BOTH-LOW are invalid and refuse ARM.
- **Heater permit (pin 15 HTR_PERMIT_CMD).** Driven only in SAFE. Hardware cuts the permit when the arming plug is inserted or the ARM bus is on, and the watchdog gates U305.

## How it was produced

The generator `../kicad_gen/make_ecu_kicad.py` builds the project from the single design source `../kicad_gen/ecu_design.py`, which holds the parts, values, nets and the Teensy pin map. Each component carries `Spec` and `Function` fields with its source tag.

`../kicad_gen/run_all.sh` repeats the full chain:
1. Generate the project.
2. Export the netlist with `kicad-cli`.
3. Run the cross-check.
4. Build the grouped BOM.
5. Export the PDF.
6. Run ERC.

**Warning: regenerating overwrites hand edits.** From the moment the founder edits the schematic in KiCad, KiCad is the master. After that, use `SKIP_GEN=1 ./run_all.sh` to run only the checks.

## ERC

KiCad 7.0's `kicad-cli` has no `sch erc` command (it was added in KiCad 8). The real eeschema ERC engine was therefore run through the GUI on a virtual display (Xvfb + xdotool, script `../kicad_gen/gui_erc.sh`). KiCad's own report is saved to `erc/argos_ecu_erc.rpt`, with dialog screenshots in `erc/shots/`.

**Severities.** All checks are set to error or warning in `argos_ecu.kicad_pro`, except `simulation_model_issue`, which is set to `ignore` as in KiCad's default. No SPICE models are assigned in this schematic.

**v2.3 evidence:**
- **Run 1, kept.** It included the drawn DNP bleed provision and found 0 errors and 0 warnings (`erc/argos_ecu_erc_v2p3_run1_with_bleed_dnp_provision.rpt`).
- **Final run.** Without the provision, after a comment-only source edit: 0 errors, 0 warnings (`erc/argos_ecu_erc.rpt`).
- **Negative control** (`erc/negative_control_v2p3/`). With the PREG `PWR_FLAG` removed on the new Pintle_Rail sheet, ERC reports one error, `power_pin_not_driven` on U802 pin 1. The check is therefore live on the new sheet.

**Independent cross-check** (`../kicad_gen/check_netlist.py`). It compares the KiCad-exported netlist pin by pin with the generator's intent. It also re-applies KiCad 7's default pin-conflict matrix and its driver rules, and checks that every footprint exists in the stock or project libraries.

**Pins left open on purpose:**
- Pins with a no-connect flag:
  - U102 TPS54202 EN: floating means enabled (TI SLVSD26C).
  - PS501 Pololu ENABLE: 100 kOhm internal pull-up.
  - U801 TPS552882 CDC (pin 16): may float (TI datasheet).
  - Spare buffer outputs, and MAX31856 FAULT/DRDY.
- Library pins of electrical type NC need no flag: BAT54W pin 2, the ADR4525 NC pins, and MAX31856 DNC (U604-U606, U904-U906).

**Earlier evidence.** The v2.0-v2.2 evidence is in `../kicad_archive/v2p2/kicad/erc/`:
- SPICE-check run 1: 102 "no simulation model" warnings and 12 off-grid warnings, later fixed.
- VBAT negative control.
- v2.2 report: 299 symbols, 193 nets, 822 pins, 0 errors.

**From KiCad 8 on:** `kicad-cli sch erc --severity-all -o erc.rpt argos_ecu.kicad_sch`.

## Archive

`../kicad_archive/v2p2/` holds the complete v2.2 output and its generator sources:
- `custom_symbols.py` was rebuilt by reverting the three v1.1 edits, because the first archive copy was taken after the edit. `ARCHIVE_NOTE.txt` records this.
- `kicad_writer.py` is a byte copy.

## Fallback bleed (not drawn)

The head-end prime bleed is a lead fallback only (CHANGELOG line 126). If it is ever activated, it would use:
- one SOL1-type DMN6075S low-side channel on +12V_ARM, through the ARM-gated spare buffer channel U304 2A2 (pin 13) -> 2Y2 (pin 7);
- a coil current of <= 0.75 A (ASSUMED), about 9 W while open, which fits the U3V70F12 budget if it does not overlap the spark and torch solenoids.

No Teensy pin is free. The bleed would either share pin 15 with the heater permit (the two are separated in hardware by the ARM state) or need an I/O expander.

## Known limitations (open)

- **No PCB layout yet.** The 120 x 60 mm board in `interfaces/electronics.json` is a DESIGN reservation, not a routed board.
- **`TI_RPM0026A_PLACEHOLDER` is not a land pattern.** It only gives the 26 pins a footprint for the netlist. Replace it with TI's RPM0026A drawing before layout.
- **`Teensy41_Socket`** assumes 2 x 1x24 female headers and a 61.0 x 17.8 mm outline. Check it against the PJRC drawing before ordering a board.
- **`Pololu_U3V70_WireAttach`** contains wire pads only.
- **TPS552882 loop compensation** uses the datasheet equations 22 and 24-26 as extracted. The extraction was garbled, so the equations are TO-VERIFY against the TI PDF. Phase margin is measured at B-PWR-1.
- **LTC4365 UV threshold** uses V_UV = V_OV, which is ASSUMED (4.88/5.04/5.21 V). TO-CONFIRM from the ADI datasheet, which the proxy blocks (analog.com 403).
- **Q803 enhancement.** Whether the CSD17578Q5A is fully enhanced at the LTC4365 gate drive (3.0-4.2 V at VIN 5 V) is TO-CONFIRM. The computed dissipation is 0.26 W only if it is fully enhanced.
- **ARM bus peak current vs F301 15 A** is TO-CHECK against the Littelfuse 0297015 time-current curve. Known loads are the MV-opener servo stall (9.2 A at 7.4 V DATASHEET, 10.4 A at 8.4 V ASSUMED) and the pintle rail input (<= 4.33 A, current limit, DERIVED); the 12 V boost loads come on top.
- **Part choice.** Footprints were chosen for hand assembly (0603, TSSOP or larger). Availability was not checked: every price in `bom_v2.csv` is TO-QUOTE or a dated catalogue entry.
- **Label-connected schematic.** Nets connect by label (net-label style), which suits editing and review in KiCad; wire routing inside each block is minimal.
