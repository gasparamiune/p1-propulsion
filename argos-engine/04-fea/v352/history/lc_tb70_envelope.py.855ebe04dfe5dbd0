"""LC-TB70 envelope in pressure-time form (lead resume 2026-10-19 item 9; lead CHANGELOG 216 (3), REV-ELEC-2 R2-15): the head-end pressure
histories that Mechanical's structural load cases cover, for Electronics v2.11 S6 in-window genuine over-pressure cases (50 bar step, ramps
to 60 bar, FA-1 followed by 35-50 bar plateaus), which must abort with the head pressure-time inside this envelope.

Basis (every structural case is QUASI-STATIC: the pressure-structure breathing modes are ~0.04-0.05 ms (S-AX modal), far below any rise
time >= 0.8 ms, so DLF 1.0 for the stand transients; the time axis below is therefore the ANALYSED duration basis of each case, not a
structural time limit; the thermal state of the stand cases is the ASSUMED bounding 'TB' field: B1 end-of-burn shifted uniformly so the
case maximum equals the 448.15 K case abort, sax.py T_CASE_ABORT):
  Z0  P <= 45.0 bar abs (MEOP, LC2): nominal, SF 1.5 / 2.0 (188 (9)), any time in the burn thermal envelope.
  Z1  45.0 < P <= 58.1 bar abs: LC-TB70 (S6 70 % throat block; 58.1 = the v2.7 transducer peak, plant 55.7 bar abs, line 88), nominal
      SF 1.5 / 2.0, blocked distribution, + manifold 70 bar; analysed duration basis 300 ms above MEOP per event (the LC-TB-S basis).
  Z2  58.1 < P <= 63.1 bar abs: LC-TB-S (blocked static, 63.1 bar abs = the blocked-nozzle feed limit, BN 63.08 bar), ABNORMAL SF 1.0 / 1.5,
      0.30 s (relay-2, line 106 (2)).
  Z3  63.1 < P <= 75.52 bar abs: FA-1-class pulse only (sax.py FA1: Combustion late_light_spike_v2p4 57fce738164fd571 worst of 48 rows,
      head 75.52 bar abs, 3.0 ms above 45 bar abs, 10-90 % rise 0.8 ms); FA-1 rule SF 1.0 (188 (9)), structure checked at FA1S = DLF 2.0 x the
      peak = 151.04 bar abs (the bound for every period, line 230 (2)); J-FWD v3.5.2 O1 sized there (v352/jfwd/jfwd_v352_v1.json).
  Rule J-FWD: any head excursion above 60 bar abs (Pc channel) -> J-FWD screws replaced + holes / taps gauged (v352/jfwd inspect-or-replace).
  Outside the envelope (no structural claim): P > 75.52 bar abs; P > 63.1 bar abs for more than 3.0 ms; P > 45 bar abs later than 300 ms
  after the first crossing; a Z3 pulse with a 10-90 % rise faster than 0.8 ms.
Mechanical, 2026-10-20.  DERIVED from the analysed cases; margins are the S-AX tables (negatives SHOWN AS FOUND)."""
import csv, hashlib, json, math
from pathlib import Path

OUT = Path("/home/claude/work/mechanical/v352/tb70/lc_tb70_envelope_v1.json")
MEOP, P_TB70, P_TBS, P_FA1 = 45.0, 58.1, 63.1, 75.519
T_EVENT, T_FA1, TR_FA1 = 0.300, 0.0030, 0.0008
P_JFWD_RULE = 60.0


def inside(t, p, rise_10_90_s=None):
    """t [s], p [bar abs] samples of one event; returns (inside, zone_max, reasons)."""
    reasons, zone = [], 0
    above = [ti for ti, pi in zip(t, p) if pi > MEOP]
    if not above:
        return True, 0, []
    t0 = above[0]
    t_hi = [ti for ti, pi in zip(t, p) if pi > P_TBS]
    for ti, pi in zip(t, p):
        tau = ti - t0
        if pi > P_FA1:
            reasons.append(f"P {pi:.2f} > {P_FA1} bar abs at tau {tau * 1e3:.1f} ms")
        if pi > MEOP and tau > T_EVENT:
            reasons.append(f"P {pi:.2f} > MEOP at tau {tau * 1e3:.1f} ms > {T_EVENT * 1e3:.0f} ms")
        zone = max(zone, 3 if pi > P_TBS else 2 if pi > P_TB70 else 1 if pi > MEOP else 0)
    if t_hi and (t_hi[-1] - t_hi[0]) > T_FA1:
        reasons.append(f"P > {P_TBS} bar abs for {(t_hi[-1] - t_hi[0]) * 1e3:.2f} ms > {T_FA1 * 1e3:.1f} ms")
    if zone == 3 and rise_10_90_s is not None and rise_10_90_s < TR_FA1:
        reasons.append(f"Z3 pulse rise {rise_10_90_s * 1e3:.2f} ms < {TR_FA1 * 1e3:.1f} ms")
    return (not reasons), zone, reasons


def square(p_peak, t_above, dt=0.0005):
    """Trapezoid history: 0.5 ms ramp from 45 bar to the peak, plateau, 0.5 ms ramp down (bounding the reported 'peak / time above MEOP')."""
    t, p, k = [], [], 0
    while k * dt <= t_above + 0.002:
        tt = k * dt
        if tt < 0.0005:
            pp = MEOP + (p_peak - MEOP) * tt / 0.0005
        elif tt <= t_above - 0.0005:
            pp = p_peak
        elif tt <= t_above:
            pp = p_peak - (p_peak - MEOP) * (tt - (t_above - 0.0005)) / 0.0005
        else:
            pp = 40.0
        t.append(tt); p.append(pp); k += 1
    return t, p


def fa1_pulse(dt=2e-5):
    q = (MEOP - 1.01325) / (P_FA1 - 1.01325)
    tau = (T_FA1 - TR_FA1 / 0.8 * (1.0 - q)) / (-math.log(q))   # sax.py fa1_tau with t_r = 10-90 % / 0.8
    tr = TR_FA1 / 0.8
    t, p = [], []
    for k in range(int(0.02 / dt)):
        tt = k * dt
        x = tt / tr if tt <= tr else math.exp(-(tt - tr) / tau)
        t.append(tt); p.append(1.01325 + (P_FA1 - 1.01325) * x)
    return t, p


cases = []
for name, pk, ta, src in (("S6 v2.10 throat_blocked_70pct_500N_24C_Cd0p8", 53.419, 0.034,
                           "06-electronics/results/sil_v2p10/S6_aborts.json Pc_max_abs_Pa 5341909, t_Pc_above_MEOP_s 0.034 (SIM)"),
                          ("S6 v2.7 throat block 70 % (plant)", 55.7, 0.072, "CHANGELOG line 88 (SIM): plant 55.7 bar abs, > MEOP 72 ms"),
                          ("S6 v2.7 throat block 70 % (transducer peak, as LC-TB70)", 58.1, 0.072, "CHANGELOG line 88 (SIM): transducer 58.1"),
                          ("S6 v2.11 in-window: 50 bar step, abort", 50.0, 0.150, "illustration: plateau 50 bar abs, 150 ms above MEOP"),
                          ("S6 v2.11 in-window: ramp to 60 bar, abort", 60.0, 0.150, "illustration: plateau 60 bar abs (Z2 abnormal + J-FWD rule)")):
    t, p = square(pk, ta)
    ok, z, why = inside(t, p)
    cases.append({"case": name, "peak_bar_abs": pk, "t_above_MEOP_ms": ta * 1e3, "inside": ok, "zone_max": z, "reasons": why,
                  "jfwd_rule_triggered": pk > P_JFWD_RULE, "src": src})
t, p = fa1_pulse()
ok, z, why = inside(t, p, rise_10_90_s=TR_FA1)
cases.append({"case": "FA-1 pulse (Combustion v2.4 worst row)", "peak_bar_abs": P_FA1, "t_above_MEOP_ms": round(sum(1 for x in p if x > MEOP) * 2e-2, 2),
              "inside": ok, "zone_max": z, "reasons": why, "jfwd_rule_triggered": True, "src": "sax.py FA1 (SIM)"})
t2, p2 = fa1_pulse()
t2 = t2 + [t2[-1] + 0.0005 * k for k in range(1, 400)]
p2 = [max(x, 0.0) if i < len(p) else 0.0 for i, x in enumerate(p2)] + [48.0] * 399
ok2, z2, why2 = inside(t2, p2, rise_10_90_s=TR_FA1)
cases.append({"case": "FA-1 pulse followed by a 48 bar plateau for 200 ms", "peak_bar_abs": P_FA1, "inside": ok2, "zone_max": z2,
              "reasons": why2, "jfwd_rule_triggered": True, "src": "illustration of the S6 'FA-1 followed by 35-50 bar plateaus' family"})

# purge tail (line 230 (3) ONE flow basis 29.25 g/s at 289.5 K): chamber pressure if the purge flow leaves through a 70 %-blocked throat
R_N2O, gam = 8.314462 / 0.0440128, 1.27                    # N2O vapour, gamma ASSUMED (cold vapour 1.26-1.30)
Gam = math.sqrt(gam) * (2.0 / (gam + 1.0)) ** ((gam + 1.0) / (2.0 * (gam - 1.0)))
cstar = math.sqrt(R_N2O * 289.5) / Gam
A_t = math.pi / 4.0 * 13.72 ** 2 * 1e-6
purge = {"basis": "lead CHANGELOG 230 (3): 29.25 g/s at 289.5 K (ADOPTED); warm-end band 27.58-31.06 g/s; Cd sensitivity 25.30-33.13 g/s",
         "model": "choked cold-gas flow of N2O vapour through the open throat fraction: P0 = mdot c* / A*, c* = sqrt(R T) / Gamma(gamma 1.27 ASSUMED)",
         "c_star_m_s": round(cstar, 1), "rows": []}
for frac_open in (1.0, 0.30, 0.10):
    for md in (0.02925, 0.03313):
        P0 = md * cstar / (A_t * frac_open) / 1e5
        purge["rows"].append({"throat_open_fraction": frac_open, "mdot_kg_s": md, "P0_bar_abs": round(P0, 2)})
purge["verdict"] = ("the purge cannot re-enter the envelope: <= 7.9 bar abs even with 90 % of the throat blocked at the top of the Cd band "
                    "(DERIVED); rows below ~1.8 bar abs are not choked (the chamber stays near ambient, the formula value is only a bound); "
                    "a fully blocked throat is the BN / LC-TB-S static case (<= 63.1 bar abs, Z2)")

# v3.5.1 S-AX minimum margins per zone (valid L1 tables, hub 04-fea/structural/results/*_thv351_TB1GC_cad351_v1.csv); v3.5.2 after the chain
tab = Path("/home/claude/work/shared-fallback/engine/04-fea/structural/results/sax_margin_table_L1_thv351_TB1GC_cad351_v1.csv")
rows = list(csv.DictReader(open(tab)))
zm = {}
for case in ("LC2", "TB70", "TBS", "FA1S"):
    sel = [r for r in rows if r["case"] == case]
    neg = [{"part": r["part"], "MS": r["MS"], "MS_ult": r["MS_ult"], "MS_all_nodes": r["MS_all_nodes"], "T_C": r["T_C"], "SF": [r["SF_y"], r["SF_u"]]}
           for r in sel if any(v not in ("", "n/a", "None") and float(v) < 0 for v in (r["MS"], r["MS_ult"]))]
    zm[case] = {"n_parts": len(sel), "negatives_regular_set": neg}
out = {"id": "lc_tb70_envelope", "version": "v1", "date": "2026-10-20", "owner": "mechanical",
       "status": "DERIVED from the analysed structural cases (S-AX / FEA3D SIM); not physical approval; v3.5.2 margins replace the v3.5.1 rows after the v352 chain",
       "pressure": "head-end static pressure, bar abs (the Pc channel at the head); tau = time since the first crossing of MEOP 45 bar abs in the event",
       "zones": {
           "Z0": {"P_bar_abs": [None, MEOP], "tau_s": [0, None], "case": "LC2 (MEOP)", "SF": "1.5 / 2.0 (188 (9))"},
           "Z1": {"P_bar_abs": [MEOP, P_TB70], "tau_s": [0, T_EVENT], "case": "LC-TB70 (S6 70 % throat block, blocked distribution, case at the 448.15 K abort)", "SF": "1.5 / 2.0"},
           "Z2": {"P_bar_abs": [P_TB70, P_TBS], "tau_s": [0, T_EVENT], "case": "LC-TB-S (blocked static, BN feed limit)", "SF": "1.0 / 1.5 (abnormal)"},
           "Z3": {"P_bar_abs": [P_TBS, P_FA1], "tau_s": [0, T_FA1], "case": "FA-1 pulse (structure at FA1S 151.04 bar abs, DLF 2.0 bound)", "SF": "1.0 (FA-1 rule)",
                  "extra": f"total time above {P_TBS} bar abs <= {T_FA1 * 1e3:.1f} ms; 10-90 % rise >= {TR_FA1 * 1e3:.1f} ms"}},
       "polyline_nominal_SF1p5_2p0": [[0.0, P_TB70], [T_EVENT, P_TB70], [T_EVENT, MEOP], [10.0, MEOP]],
       "polyline_all_cases": [[0.0, P_FA1], [T_FA1, P_FA1], [T_FA1, P_TBS], [T_EVENT, P_TBS], [T_EVENT, MEOP], [10.0, MEOP]],
       "rules": [f"any head excursion above {P_JFWD_RULE} bar abs: replace all J-FWD screws (HW-101) and gauge the TC-01 holes / TC-02 taps before the next run",
                 "an event that leaves the envelope is outside the structural basis: no margin claim, engine quarantined for inspection"],
       "cases_checked": cases, "purge_tail": purge, "v351_min_margins_regular_set": zm,
       "note_negatives": "Z1 (LC-TB70) is analysed but NOT all-positive: v3.5.1 TC-02 MS_ult -0.152, NZ-01 -0.039, NZ-03 -0.158 (SF 1.5 / 2.0, SHOWN AS "
                         "FOUND; items 4 / 5 of the resume); Z2 (LC-TB-S, SF 1.0 / 1.5) has no negative in the regular set",
       "how_to_use": "Electronics: sample the S6 head-pressure trace (plant Pc at the head), find tau from the first sample above 45 bar abs, and check "
                     "every sample against the zones (function inside() in lc_tb70_envelope.py); report the zone reached and the J-FWD rule flag"}
s = json.dumps(out, indent=1)
OUT.write_text(s)
print(OUT.name, hashlib.sha256(s.encode()).hexdigest()[:16])
for c in cases:
    print(f"  {c['case'][:60]:60s} inside {c['inside']} zone {c['zone_max']} jfwd {c['jfwd_rule_triggered']} {c['reasons'][:1]}")
print(json.dumps(purge["rows"]))
print(json.dumps(zm)[:1500])
