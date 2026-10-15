#!/usr/bin/env python3
"""REV-ELEC-1 independent recomputation (reviewer script, v1, 2026-10-13).

Recomputes, from the component values and datasheet numbers QUOTED in the published files (ecu_design.py, config.h,
mv_ladder_table.h, electronics.json, combustion.json, gnc.json, bom_v2p1.csv), the electrical, timing and logic numbers the
Electronics v2.9 handback relies on. It does NOT import or execute any author script. Every output carries an evidence tag:
DERIVED (computed here from the quoted inputs), DATASHEET / ASSUMED / SIM (as quoted from the source), TO-VERIFY (an input that
nothing published supports). A reproduced number shows arithmetic consistency only; it is not hardware evidence.

Usage: /opt/engine-venv/bin/python -I re_recompute_v1.py <engine_root> <out_prefix>
"""
import csv
import hashlib
import json
import math
import os
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/work/shared-fallback/engine'
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'reviews/electronics/re_recompute_v1')
REV = os.path.join(ROOT, 'reviews/electronics')
PAMB = 1.01325e5
res = {'review': 'REV-ELEC-1', 'script': 're_recompute_v1.py', 'note': 'reviewer recomputation; no author script imported or run'}
lines = []


def sha16(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def out(key, v, tag, src, unit=''):
    res[key] = {'v': v, 'unit': unit, 'tag': tag, 'src': src}
    vs = ('%.6g' % v) if isinstance(v, float) else str(v)
    lines.append('%-58s %-26s %-8s %-10s %s' % (key, vs, unit, tag, src))


def par(*r):
    return 1.0 / sum(1.0 / x for x in r)


inputs = ['06-electronics/hardware/kicad_gen/ecu_design.py', '06-electronics/firmware/src/core/config.h',
          '06-electronics/firmware/src/core/mv_ladder_table.h', '06-electronics/firmware/src/core/filters.h',
          'interfaces/electronics.json', 'interfaces/combustion.json', 'interfaces/gnc.json', '06-electronics/results/bom_v2p1.csv',
          'interfaces/CHANGELOG.md', '00-requirements/REQUIREMENTS.md', '00-requirements/ICD-AIRFRAME.md']
res['inputs_sha256_16'] = {p: sha16(os.path.join(ROOT, p)) for p in inputs}

# ------------------------------------------------------------------ (A) Pc chain, firmware and hardware over-pressure
lines.append('\n(A) Pc chain: TE M3234 070BG (0.5-4.5 V ratiometric on 5 V, 0-70 bar g), divider 12.7k/4.02k, ADS131M04 (1.2 V, 2^23)')
VEXC, FS070 = 5.0, 70.0e5
vsig = lambda pg, fs=FS070: VEXC * (0.1 + 0.8 * pg / fs)
pg_of = lambda v, fs=FS070: (v / VEXC - 0.1) / 0.8 * fs
for zin in (330e3, 300e3, None):
    rb = 4.02e3 if zin is None else par(4.02e3, zin)
    k = rb / (12.7e3 + rb)
    out('A_k_div_Zin_%s' % ('inf' if zin is None else '%dk' % (zin / 1e3)), k, 'DERIVED', 'ecu_design.py l.568-570; config.h l.672 Zin 330k [DS]')
k330 = par(4.02e3, 330e3) / (12.7e3 + par(4.02e3, 330e3))
out('A_adc_clip_at_PC_SIG_V', 1.2 / k330, 'DERIVED', 'Vref 1.2 V / k_div(330k); window top kPcSensorMax_V 4.75 V', 'V')
out('A_pc_Pa_per_count', (1.2 / 2 ** 23) / k330 / VEXC / 0.8 * FS070, 'DERIVED', 'LSB referred to Pc', 'Pa')
out('A_fw_ovp_30barabs_gauge_bar', (30e5 - PAMB) / 1e5, 'DERIVED', 'config.h l.271 kPcOverPressureAbs 30 bar abs', 'bar g')
out('A_fw_ovp_PC_SIG_V', vsig(30e5 - PAMB), 'DERIVED', 'ratiometric 070BG', 'V')
tap = 31.6 / 131.6
vref = VEXC * 29.4 / (237 + 29.4)
v_trip = vref / tap
out('A_hw_ovp_tap', tap, 'DERIVED', 'ecu_design.py l.364-365 R330 100k / R331 31.6k')
out('A_hw_ovp_Vref_V', vref, 'DERIVED', 'ecu_design.py l.368-371 R332 237k / R333 29.4k from +5V_SNS', 'V')
out('A_hw_ovp_trip_PC_SIG_V', v_trip, 'DERIVED', '', 'V')
out('A_hw_ovp_trip_bar_g', pg_of(v_trip) / 1e5, 'DERIVED', 'claim 31.47 bar g (ecu_design.py l.369)', 'bar g')
# electronic tolerance band (0.1 % resistors worst case + LMV331 Vio 9 mV DATASHEET as quoted l.374); the transducer TEB is
# common to the firmware and hardware paths (same PC_SIG), so it does not change their order
band = []
for e330 in (-1, 1):
    for e331 in (-1, 1):
        for e332 in (-1, 1):
            for e333 in (-1, 1):
                for vio in (-9e-3, 9e-3):
                    t_ = 31.6 * (1 + 1e-3 * e331) / (31.6 * (1 + 1e-3 * e331) + 100 * (1 + 1e-3 * e330))
                    vr = VEXC * 29.4 * (1 + 1e-3 * e333) / (29.4 * (1 + 1e-3 * e333) + 237 * (1 + 1e-3 * e332))
                    band.append(pg_of((vr + vio) / t_) / 1e5)
out('A_hw_ovp_band_electronic_bar_g', [round(min(band), 3), round(max(band), 3)], 'DERIVED', '0.1 % resistors + Vio +/-9 mV (DS as quoted)', 'bar g')
out('A_hw_ovp_band_min_minus_fw_ovp_bar', min(band) - (30e5 - PAMB) / 1e5, 'DERIVED', '> 0: the hardware path always trips after the firmware path (backup), electronics only', 'bar')
out('A_teb_070BG_bar', 0.015 * 70.0, 'DATASHEET (as quoted)', 'config.h TEB 1.5 % FS', 'bar')
rth = par(100e3, 31.6e3)
tau = rth * 220e-9
out('A_hw_ovp_rc_tau_ms', tau * 1e3, 'DERIVED', 'Rth(R330||R331) x C330 220 nF', 'ms')


def trip_time(p0_abs, p1_abs):
    a0, a1 = vsig(p0_abs - PAMB) * tap, vsig(p1_abs - PAMB) * tap
    if a1 <= vref:
        return float('nan')
    return -tau * math.log(1 - (vref - a0) / (a1 - a0)) * 1e3


for p0, p1 in ((PAMB, 45e5), (PAMB, 63e5), (25e5, 45e5), (25e5, 35e5)):
    out('A_hw_ovp_step_trip_ms_%.0f_to_%.0f_bar_abs' % (p0 / 1e5, p1 / 1e5), trip_time(p0, p1), 'DERIVED', 'ideal step at PC_SIG, RC only (comparator and latch delays < 10 us ignored)', 'ms')

# ------------------------------------------------------------------ (B) P_mid comparator U570
lines.append('\n(B) P_mid comparator: 170BG on +5V_SNS, R573 4.75k in, R574 1M feedback, R575 10k pull-up, ref R576 10.2k / R577 1.74k')
FS170 = 170.0e5


def pmid_thresholds(r573=4.75e3, r574=1e6, r575=10e3, r576=10.2e3, r577=1.74e3, vio=0.0, vol=0.0):
    vr = VEXC * r577 / (r576 + r577) + vio
    # output LOW (P_mid low state): IN+ = Vsig*R574/(R573+R574) + Vol*R573/(R573+R574) -> rises to vr
    vs_rise = (vr * (r573 + r574) - vol * r573) / r574
    # output HIGH (open collector off): node PMID_CMP pulled to 5 V through R575 and loaded by R574 into IN+; solve IN+ = vr
    # IN+ = (Vsig/R573 + Vcmp/R574)/(1/R573+1/R574), Vcmp = (5/R575 + vr/R574)/(1/R575+1/R574)
    vcmp = (VEXC / r575 + vr / r574) / (1 / r575 + 1 / r574)
    vs_fall = (vr * (1 / r573 + 1 / r574) - vcmp / r574) * r573
    return pg_of(vs_rise, FS170) / 1e5, pg_of(vs_fall, FS170) / 1e5


r, f = pmid_thresholds()
out('B_pmid_rise_bar_g', r, 'DERIVED', 'claim 9.86 bar g (ecu_design.py l.520-532)', 'bar g')
out('B_pmid_fall_bar_g', f, 'DERIVED', 'claim 8.86 bar g', 'bar g')
out('B_pmid_rise_bar_g_with_Vol_0p15V', pmid_thresholds(vol=0.15)[0], 'DERIVED', 'LMV331 output-low saturation ~0.15 V at 0.5 mA ASSUMED', 'bar g')
corners = []
for s in range(32):
    e = [(1 if (s >> i) & 1 else -1) * 0.01 for i in range(5)]
    for vio in (-9e-3, 9e-3):
        corners.append(pmid_thresholds(4.75e3 * (1 + e[0]), 1e6 * (1 + e[1]), 10e3 * (1 + e[2]), 10.2e3 * (1 + e[3]), 1.74e3 * (1 + e[4]), vio))
rr = [c[0] for c in corners]
ff = [c[1] for c in corners]
out('B_pmid_rise_band_electronic_bar_g', [round(min(rr), 2), round(max(rr), 2)], 'DERIVED', '1 % resistors (ASSUMED class) + Vio 9 mV', 'bar g')
out('B_pmid_fall_band_electronic_bar_g', [round(min(ff), 2), round(max(ff), 2)], 'DERIVED', '', 'bar g')
out('B_pmid_rise_band_with_TEB_bar_g', [round(min(rr) - 2.55, 2), round(max(rr) + 2.55, 2)], 'DERIVED', '+/- TEB 2.55 bar (config.h, 170BG class)', 'bar g')
out('B_pmid_fall_band_with_TEB_bar_g', [round(min(ff) - 2.55, 2), round(max(ff) + 2.55, 2)], 'DERIVED', '', 'bar g')
out('B_pmid_purge_level', 'NOT PUBLISHED', 'TO-VERIFY', 'P_mid with V1 and V2 both open (orifice ratio V1 : restriction) must sit outside the band above; not stated in electronics.json or the SIL record')

# ------------------------------------------------------------------ (C) MV switch + P_mid ladder on pin 23
lines.append('\n(C) Ladder: R_top 10k to +3V3 (ratiometric), R0 82.5k EOL, R1 9.53k OPEN, R2 17.8k CLOSED (J508 backshell), R3 33.2k via Q570')
RT, R0, R1, R2, R3 = 10e3, 82.5e3, 9.53e3, 17.8e3, 33.2e3
thr = [0.34773, 0.38521, 0.43259, 0.48234, 0.54917, 0.64891, 0.73608, 0.83102, 0.94690]
bits = [15, 11, 13, 9, 14, 10, 12, 4, 8, 0]


def ratio(rb):
    return 1.0 if rb is None else rb / (RT + rb)


def decode(x):
    if not (x >= 0.02) or x > 1.05:
        return 'INVALID(short/open)'
    k = 0
    while k < 9 and x > thr[k]:
        k += 1
    b = bits[k]
    if not (b & 8):
        return 'INVALID(code %d)' % b
    return 'valid open=%d closed=%d pmid=%d' % (b & 1, (b >> 1) & 1, (b >> 2) & 1)


codes = {}
for harness in (1, 0):
    for o in (0, 1):
        for c in (0, 1):
            for p in (0, 1):
                if not harness and (o or c):
                    continue
                rs = [x for x, on in ((R0, harness), (R1, harness and o), (R2, harness and c), (R3, p)) if on]
                rb = par(*rs) if rs else None
                codes['harness%d_open%d_closed%d_pmid%d' % (harness, o, c, p)] = round(ratio(rb), 5)
out('C_ladder_nominal_ratios', codes, 'DERIVED', 'matches kLadderNom (mv_ladder_table.h) if equal to 5 decimals')
out('C_ladder_physically_impossible_code_OPEN_and_CLOSED_decodes', decode(codes['harness1_open1_closed1_pmid0']), 'DERIVED',
    'sensor_scale.cpp mvLadderDecode: both limit switches closed is reported VALID (no plausibility check in engine_ecu.cpp l.567/879)')
out('C_soft_short_region', '[0.02, %.5f) decodes as bits 15 (OPEN+CLOSED+P_mid high, VALID)' % thr[0], 'DERIVED',
    'a partial short of the pin 23 node to GND above 0.02 x 3.3 V is not reported as a fault')
for z in (0.10, 0.20, 0.30):
    rb = z / (1 - z) * RT
    out('C_soft_short_R_to_GND_for_ratio_%.2f_ohm' % z, rb, 'DERIVED', 'decode: %s' % decode(z), 'ohm')


def leak_to_flip(rb_nom, t):
    rb_t = t / (1 - t) * RT
    return 1.0 / (1.0 / rb_t - 1.0 / rb_nom) if rb_t < rb_nom else float('nan')


for name, rb, t, what in (('coast_closed_pmid_lo', par(R0, R2), thr[4], 'closed + P_mid HIGH: coast leak flag / pad BLEED_FAULT / stand abort'),
                          ('burn_open_pmid_lo', par(R0, R1), thr[2], 'open + P_mid HIGH: in-burn leak flag (flight) / BLEED_FAULT (stand)'),
                          ('harness_R0_only', R0, thr[7], 'invalid code 4 (harness open + P_mid high)')):
    out('C_leak_to_GND_that_flips_%s_ohm' % name, leak_to_flip(rb, t), 'DERIVED', what, 'ohm')
taus = {k: (par(RT, (v / (1 - v)) * RT) + 1e3) * 100e-9 * 1e3 for k, v in codes.items() if v < 1.0}
out('C_ladder_rc_tau_ms_max', max(taus.values()), 'DERIVED', '(R_top || R_bottom + R571 1k) x C570 100 nF', 'ms')
gaps = [min(abs(codes[a] - t) for t in thr) for a in codes]
out('C_settle_to_half_min_gap_ms', max(taus.values()) * math.log(0.6 / (0.0193 / 2)), 'DERIVED', 'worst full-swing 0.6 to within half the 0.0193 gap', 'ms')

# ------------------------------------------------------------------ (D)(E) pintle rail
lines.append('\n(D)(E) Pintle rail: TPS552882 FB 24.9k/4.75k (1.2 V ref as quoted), LTC4365 OV 154k/10.0k, UV 90.9k/10.0k')
out('E_tps552882_vout_V', 1.2 * (1 + 24.9 / 4.75), 'DERIVED', 'ecu_design.py l.703-742; 1.2 V reference as quoted by the author (TO-VERIFY on the TI datasheet)', 'V')
out('E_sim_h_stale_comment_vout_V', 1.2 * (1 + 100 / 19.1), 'DERIVED', 'sim.h l.62 comment "FB 100k/19.1k": stale values, same voltage class')
ov = [g * (1 + 154e3 * (1 + a * 1e-3) / (10e3 * (1 + b * 1e-3))) for g in (0.4925, 0.5075) for a in (-1, 1) for b in (-1, 1)]
out('D_ltc4365_ov_nominal_V', 0.5 * (1 + 15.4), 'DERIVED', 'claim 8.20 V', 'V')
out('D_ltc4365_ov_band_V', [round(min(ov), 3), round(max(ov), 3)], 'DERIVED', 'OV pin 492.5-507.5 mV (DS as quoted) + 0.1 % resistors', 'V')
out('D_ov_band_top_vs_jam_failure_case_8p34V', round(max(ov), 3) - 8.34, 'DERIVED', 'REQUIREMENTS amendment: failure case 933.7 N at 8.34 V', 'V')
out('D_ov_band_bottom_minus_rail_7p49V', round(min(ov), 3) - 1.2 * (1 + 24.9 / 4.75), 'DERIVED', 'headroom for regulation tolerance and load-release overshoot (TO-VERIFY at B-PNT-1)', 'V')
uv = [0.5 * (1 + 90.9e3 * (1 + a * 1e-2) / (10e3 * (1 + b * 1e-2))) for a in (-1, 1) for b in (-1, 1)]
out('D_ltc4365_uv_band_V', [round(min(uv), 3), round(max(uv), 3)], 'DERIVED', 'UV threshold 0.5 V ASSUMED by the author (TO-CONFIRM); 1 % resistors', 'V')
out('D_firmware_prail_lost_V', 5.5, 'DESIGN', 'config.h l.514 kPrailLost_V (above the UV band: firmware sees the loss first)', 'V')
out('D_ov_uv_bench_test_in_plan', False, 'DERIVED', 'bench_plan_v2.md has no test of the LTC4365 OV/UV or the OVP comparator thresholds')

# ------------------------------------------------------------------ (F) +12V_ARM boost (U3V70F12) and ARM_BUS
lines.append('\n(F) +12V_ARM loads vs U3V70F12 input limits (6 A prolonged / 7 A seconds / 10 A cycle, DATASHEET as quoted l.466)')
loads_W = {
    'bleed_V1_V2_16W': 2 * 16.0, 'bleed_V1_V2_21W': 2 * 21.0,                      # electronics.json coil 16/21 W (column mapping TO-VERIFY)
    'V2_only_16W': 16.0, 'V2_only_21W': 21.0,
    'torch_SOL1_SOL2': 2 * 0.8 * 12.0,                                               # combustion.json igniter.electrical 0.8 A each (DERIVED)
    'roll_pair_2x0p75A': 2 * 0.75 * 12.0,                                            # LEAD ASSUMED 0.75 A per coil
    'spark_peak_4A': 4.0 * 12.0,                                                     # combustion.json coil_primary_peak 4 A (dwell 3 ms ASSUMED)
}
cases = {
    'purge_both_valves': ['bleed_V1_V2_16W'], 'purge_both_valves_warm': ['bleed_V1_V2_21W'],
    'purge_plus_roll_pair': ['bleed_V1_V2_21W', 'roll_pair_2x0p75A'],
    'E0_overlap_V2_torch': ['V2_only_21W', 'torch_SOL1_SOL2'],
    'E0_overlap_V2_torch_roll': ['V2_only_21W', 'torch_SOL1_SOL2', 'roll_pair_2x0p75A'],
    'E0_overlap_V2_torch_spark_dwell_peak': ['V2_only_21W', 'torch_SOL1_SOL2', 'spark_peak_4A'],
}
tab = {}
for cname, ls in cases.items():
    pw = sum(loads_W[x] for x in ls)
    row = {'P_out_W': pw}
    for vin in (6.6, 7.4, 8.1):
        for eta in (0.85, 0.90):
            row['Iin_A_vin%.1f_eta%.2f' % (vin, eta)] = round(pw / eta / vin, 2)
    tab[cname] = row
out('F_boost_input_current_table', tab, 'DERIVED', 'loads ASSUMED/DERIVED as noted; VIN 6.6 V = kTvcSupplyMin, 8.1 V = kBattArmMin; eta 0.85-0.90 ASSUMED')
out('F_purge_duration_max_s', 2.5 + 2.0, 'DESIGN', 'kPurgeRelight_s 2.5 + kPurgeHoldMax_s 2.0 (config.h l.603-604)', 's')
mv_open = (9.2, 10.4)
arm = {'MV_opener_stall_A': mv_open, 'pintle_rail_input_A_max': 4.33, 'boost_input_purge_A': (tab['purge_both_valves']['Iin_A_vin7.4_eta0.90'], tab['purge_both_valves_warm']['Iin_A_vin6.6_eta0.85']),
       'MV_latch_A': round(4.0 / 7.4, 2)}
lo = mv_open[0] + 0.0 + arm['boost_input_purge_A'][0] + arm['MV_latch_A']
hi = mv_open[1] + 4.33 + arm['boost_input_purge_A'][1] + arm['MV_latch_A']
out('F_ARM_BUS_at_PURGE_start_A', [round(lo, 1), round(hi, 1)], 'DERIVED', 'MV opener stall (DATASHEET 9.2 A / ASSUMED 10.4 A) + pintle rail 0-4.33 A + boost (purge) + latch 4 W; vs F301 15 A (fuse I2t TO-VERIFY)', 'A')

# ------------------------------------------------------------------ (G) timing
lines.append('\n(G) Timing')
for d_mm, mdot in ((1.0, 31.3), (0.8, 20.1), (0.6, 11.3)):        # electronics.json / handback bleed flows (SIM)
    m_liq_g = 0.5 * 0.78                                             # 0.5 cm3 MID at ~780 kg/m3 (LITERATURE class, as the author)
    t_liq = m_liq_g / mdot * 1e3
    t_vap = 8.877 * (1.0 / d_mm) ** 2                                # author 8.9 ms at 1.0 mm, scaled with flow area (ideal-gas blowdown)
    lo_ = 50 + t_liq + t_vap + 5 + 2.4
    hi_ = 80 + t_liq + t_vap + 5 + 2.4
    out('G_close_confirm_ms_restriction_%.1fmm' % d_mm, [round(lo_, 1), round(hi_, 1)], 'DERIVED',
        'valve 50-80 ms (DATASHEET as quoted) + liquid %.1f + vapour %.1f + 5 ticks + ladder RC 2.4; limit 150 ms, bench pass <= 120 ms' % (t_liq, t_vap), 'ms')
# discrete Butterworth (firmware filters.h LowPass2: bilinear with pre-warp, Q 0.7071, 50 Hz, 1 kHz)
fc, dt, q = 50.0, 1e-3, 0.70710678
k = math.tan(math.pi * fc * dt)
n = 1 / (1 + k / q + k * k)
b0 = k * k * n; b1 = 2 * b0; b2 = b0; a1 = 2 * (k * k - 1) * n; a2 = (1 - k / q + k * k) * n


def gd(w):
    import cmath
    z = cmath.exp(1j * w * dt)
    H = lambda zz: (b0 + b1 / zz + b2 / zz ** 2) / (1 + a1 / zz + a2 / zz ** 2)
    e = 1e-4
    return -(cmath.phase(H(cmath.exp(1j * (w + e) * dt))) - cmath.phase(H(cmath.exp(1j * (w - e) * dt)))) / (2 * e)


out('G_butterworth_group_delay_DC_ms', gd(2 * math.pi * 1.0) * 1e3, 'DERIVED', 'firmware LowPass2 replicated (filters.h)', 'ms')


class LP2:
    def __init__(self, x):
        self.z1 = x * (1 - b0); self.z2 = x * (b2 - a2)

    def step(self, x):
        y = b0 * x + self.z1
        self.z1 = b1 * x - a1 * y + self.z2
        self.z2 = b2 * x - a2 * y
        return y


def race(pf_abs, tau_s, floor_abs=1.8e5, p0g=0.0):
    """Light rule (10 ticks rise >= 0.8 bar filtered AND raw, floor) vs A5 (filtered > 8 bar abs for 5 ms) on a first-order chamber
    rise from P0 to pf_abs starting at tick 0; state logic before monitors (engine_ecu.cpp l.1183 / l.1322). Returns the winner."""
    lp = LP2(p0g)
    nl = na = 0
    for i in range(2000):
        t = i * dt
        pg = p0g + (pf_abs - PAMB - p0g) * (1 - math.exp(-t / tau_s)) if tau_s > 0 else pf_abs - PAMB
        f = lp.step(pg)
        ok = (f - p0g) >= 0.8e5 and (pg - p0g) >= 0.8e5 and f + PAMB >= floor_abs and pg + PAMB >= floor_abs
        nl = nl + 1 if ok else 0
        if nl >= 10:
            return 'LIGHT', i
        na = na + 1 if f + PAMB > 8.0e5 else 0
        if na >= 5:
            return 'A5_HARD_START', i
    return 'NONE', -1


bound = {}
for pf in (8.5e5, 10e5, 12e5, 15.85e5, 20e5, 25e5, 30e5):
    taus_ms = [x * 0.25 for x in range(0, 401)]
    worst = None
    for tms in taus_ms:
        w, _ = race(pf, tms * 1e-3)
        if w == 'A5_HARD_START':
            worst = tms
    bound['%.2f_bar_abs' % (pf / 1e5)] = worst
out('G_A5_race_tau_max_ms_that_aborts', bound, 'DERIVED',
    'largest first-order chamber rise time constant (0-100 ms grid) for which A5 completes before the 10-tick light confirmation; None = never')
out('G_A5_race_note', 'A5 wins when the FILTERED Pc goes from the light threshold to 8 bar abs in < 5 ticks; the 10-tick confirmation and A5 overlap by design',
    'DERIVED', 'config.h l.305-306 vs l.542-543')
c = json.load(open(os.path.join(ROOT, 'interfaces/gnc.json')))
burns = c['duty_cycles']['v']['current']['DC-A1_full_flight_drogue_fins_300m_v3']['burns_s']
coast = burns[1][0] - burns[0][1]
out('G_A1_coast_burn_off_to_burn_on_s', coast, 'DERIVED', 'gnc.json v3 DC-A1 burns_s %s' % burns, 's')
out('G_rezero_end_to_T_fire_s', [round(coast - 1.2 - 0.81 - 0.30, 1), round(coast - 1.2, 1)], 'DERIVED',
    're-zero block ends COAST + 1.2 s (config.h l.565-567); T_fire = burn-on minus 0-0.81 s; COAST entry 0-0.30 s after burn-off', 's')
out('G_vented_check_drift_allowance_bar', [0.0, 0.10], 'DERIVED', '0.10 bar limit minus captured outgassing (ASSUMED ~0.05 bar by the author) minus re-zero span bias (<= 0.05 bar accepted)', 'bar')
out('G_transducer_dT_to_exhaust_0p1bar_K', 0.10 / 0.01, 'DERIVED', 'author linear-TEB estimate 0.01 bar/K (config.h l.560; TO-VERIFY at B-PC-1)', 'K')
out('G_relight_worst_ms', {'direct': (0.16 + 0.65) * 1e3, 'prep_path': (0.06 + 0.35 + 0.15 + 0.81) * 1e3, 'purge_integrated': (2.5 + 0.81) * 1e3},
    'DERIVED', 'config.h torch gate 0.16 + W 0.65; prep bleed 0.06 + ramp 0.35 + hold 0.15; PURGE 2.5; GNC plans 0.81 / 1.41 s', 'ms')

# ------------------------------------------------------------------ (H) BASE_AMB high-side fallback, analytical windows
lines.append('\n(H) BASE_AMB: |P0| > check -> P0 := 0 (engine_ecu.cpp l.135); false light needs r > check AND r + c >= max(0.8, floor - 1.01325)')
for name, chk, flo in (('base_v2p9', 0.70, 1.8), ('post_B_PC_1', 0.40, 2.0)):
    for cu in (0.41, 0.43, 0.50):
        lo_r = max(chk, max(0.8, flo - PAMB / 1e5) - cu)
        out('H_false_light_window_%s_c%.2f_bar' % (name, cu), [round(lo_r, 3), 1.0], 'DERIVED',
            'c = unlit pre-light rise (COMB plateau 0.41-0.44 bar g; SIL nominal 0.43, SIL MC max 0.50); upper edge ~1.0 bar g = torch gate kTorchGateMaxPcG (TORCH_FAULT above)', 'bar')
comb = json.load(open(os.path.join(ROOT, 'interfaces/combustion.json')))
ts = comb['igniter']['torch_sizing']['v']
At = math.pi / 4 * 0.01372 ** 2
out('H_torch_flow_chamber_rise_upper_bound_bar', ts['mdot_total_kg_s'] * ts['cstar_m_s'] / At / 1e5, 'DERIVED',
    'combustion.json torch mdot %.3g kg/s x c* %.0f m/s / main At (Dt 13.72 mm) as a CHOKED upper bound; the main throat is not choked at this level' % (ts['mdot_total_kg_s'], ts['cstar_m_s']), 'bar')
out('H_offset_sources_not_bounded', 'spark-train EMI / ground shift on PC_SIG (spark 4 A peak, 50 Hz, runs through [E1-20 ms, E1]); Pc tap near the torch jet; sensor fault',
    'TO-VERIFY', 'B-IGN-1 must bound the DC shift of filtered and raw Pc during the spark train')

# ------------------------------------------------------------------ (I) BOM v2.1 audit
lines.append('\n(I) BOM v2.1 audit (bom_v2p1.csv)')
rows = list(csv.DictReader(open(os.path.join(ROOT, '06-electronics/results/bom_v2p1.csv'))))
pb = {}
for r_ in rows:
    pb[r_['price_basis']] = pb.get(r_['price_basis'], 0) + 1
out('I_rows', len(rows), 'DERIVED', 'bom_v2p1.csv')
out('I_price_basis_counts', pb, 'DERIVED', '')
zero = [r_['line'] for r_ in rows if r_['unit_price'].strip() in ('0', '0.0', '0.00')]
frm = [r_['line'] for r_ in rows if 'from ' in (r_['unit_price'] + r_['price_basis'] + r_['delivered_price_DK6400']).lower()]
out('I_zero_price_rows', zero, 'DERIVED', 'must be empty (ENG-14)')
out('I_from_price_rows', frm, 'DERIVED', 'must be empty (ENG-14)')
deliv = sum(1 for r_ in rows if 'DK-6400' in r_['delivered_price_DK6400'])
out('I_rows_delivered_TO_QUOTE_DK6400', deliv, 'DERIVED', 'n/a rows are no-purchase lines')
mpn_tbd = sum(1 for r_ in rows if 'TO-SELECT' in (r_['order_key'] + r_['note']))
out('I_rows_MPN_TO_SELECT', mpn_tbd, 'DERIVED', 'temperature grade not fixed while the MPN is TO-SELECT')
wet = [r_ for r_ in rows if r_['section'][0] in 'CDEF' and any(s in r_['part'] for s in ('M3234', 'Burkert', '6027', 'SS-100-1-2BT'))]
out('I_N2O_wetted_rows', [(r_['line'], r_['part'][:48], ('oxygen-clean' in r_['note'].lower())) for r_ in wet], 'DERIVED',
    '(line, part, oxygen-clean note present); ENG-16 requires O2-clean wetted paths')
import re as _re
parts = [r_['part'].lower() for r_ in rows]
need = {'coriolis mass-flow reference (CF-3)': r'coriolis', 'reference pressure gauge (B-PC-1)': r'reference (pressure )?gauge|calibrator',
        'bleed tee / restriction orifice / -2 line (B-BLEED-1)': r'\btee\b|restriction|orifice plate|-2 line|tube fitting',
        'N2 bottle + regulator (B-PC-1, B-BLEED-1)': r'\bn2\b|nitrogen', 'resistor decade box (B-ECU-1 ladder)': r'resistor (decade )?box|decade',
        'transducer simulator (B-FC-1)': r'simulator', 'cold-flow catch volume / back-pressure (ENG-16)': r'catch volume|back-pressure'}
for k_, rx in need.items():
    hit = [r_['line'] for r_, pt in zip(rows, parts) if _re.search(rx, pt)]
    out('I_bom_row_for: %s' % k_, hit if hit else 'NONE', 'DERIVED', 'searched the part field of bom_v2p1.csv')

# ------------------------------------------------------------------ (J) reviewer SIL probes (summaries of re_sil_probe outputs)
lines.append('\n(J) reviewer SIL probes (re_sil_probe.cpp on reviewer copies; SIM, plant parameters as published)')
pj = {}
for fn in sorted(os.listdir(REV)):
    if fn.startswith('re_probe') and fn.endswith('.json'):
        d = json.load(open(os.path.join(REV, fn)))
        pj[fn] = {'sha256_16': sha16(os.path.join(REV, fn)), 'n_cases': len(d['cases']), 'kBpc1Shown': d.get('kBpc1Shown')}
        ab = {}
        for cs in d['cases']:
            ab[cs['abort']] = ab.get(cs['abort'], 0) + 1
        pj[fn]['abort_counts'] = ab
out('J_probe_files', pj, 'SIM', 're_probe*.json in reviews/electronics')

with open(OUT + '.json', 'w') as fo:
    json.dump(res, fo, indent=1, sort_keys=False)
with open(OUT + '.txt', 'w') as fo:
    fo.write('REV-ELEC-1 re_recompute_v1 (reviewer). Inputs sha256/16:\n')
    for p_, h_ in res['inputs_sha256_16'].items():
        fo.write('  %s  %s\n' % (h_, p_))
    fo.write('\n'.join(lines) + '\n')
print('\n'.join(lines))
