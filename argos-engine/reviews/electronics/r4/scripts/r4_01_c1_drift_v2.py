#!/usr/bin/env python3
"""REV-ELEC-4 reviewer re-derivation of the v2.12 C1 thermal-zero drift budget (R3-01 items 1-4, 7, 8), independent of the author's
calc/v2p12/c1_drift_v2p12.py. Inputs (hub, read-only): Mechanical 04-fea/v352/c1seat/c1_seat_v352_v1.json (diaphragm point, SIM nodal,
DERIVED interpolation), c1_seat_xcheck_v352_v1.json (the restated MONITOR-NODE values of T1_head_top_bracket_foot = the seat-TC node;
the old MON_ columns of c1_seat_v352_v1.json are NOT used), torch_port_bl08_v352_v1.json. Coefficient 0.0248 bar/K typical [DATASHEET],
k ASSUMED 1-3, T0 factor (T_aw - T0) / (T_aw - 293.15) with T_aw 1500 K [ASSUMED, Mechanical F1]. Every output is DERIVED on SIM inputs.
usage: python3 -I r4_01_c1_drift_v2.py <out.json>"""
import hashlib, json, sys
from pathlib import Path

HUB = Path("/home/claude/work/shared-fallback/engine/04-fea/v352/c1seat")
SEAT, XCHK, TORCH = HUB / "c1_seat_v352_v1.json", HUB / "c1_seat_xcheck_v352_v1.json", HUB / "torch_port_bl08_v352_v1.json"
EXP = {SEAT: "435f5d71f6213160", XCHK: "02a9f27c7965f223", TORCH: "20220647d32cbbbc"}
C = 0.01 * 137.9 / (100.0 / 1.8)       # 0.024822 bar/K [DATASHEET 1 %FS / 100 F on 2000 psia]
C_ROUND = 0.0248                      # the value the author and the firmware comments use
KS = (1.0, 1.5, 2.0, 3.0)
TAW = 1500.0
LIM = 0.30                            # kPcRezeroMax_Pa [bar]
ADD = 0.05 + 0.05 + 0.0012            # zero drift (ASSUMED) + outgassing (DESIGN) + block noise (DERIVED) [bar], author's adders
TAU, TCERR = 0.25, 0.30               # ASSUMED seat-TC lag [s] and differential error [K]
U330_TRIP, U330_HALF, FW30 = 32.59, 1.513, 30.0

def h16(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
def f0(T0C): return (TAW - (273.15 + T0C)) / (TAW - 293.15)

def main():
    for p, s in EXP.items(): assert h16(p) == s, (p, h16(p))
    seat, xchk = json.loads(SEAT.read_text()), json.loads(XCHK.read_text())
    out = {"script": "r4_01_c1_drift_v2.py (REV-ELEC-4)", "inputs": {p.name: s for p, s in EXP.items()}, "coef_exact_bar_per_K": round(C, 6),
           "tags": "DERIVED on SIM (Mechanical) x DATASHEET typical coefficient; k, eps, tau, TC error, T_aw ASSUMED"}
    ev = {"A1_NF2b": {"rz1": "rezero1_end_COAST+1.4s", "rz2": "rezero2_end", "E1": "E1", "light": "light", "end": "shutdown2"},
          "B1_R4_GVHI": {"rz1": "rezero1_end_S+1.4s", "rz2": "stand_rezero2_end_S+15.72s", "E1": "stand_E1_S+18.715s",
                         "light": "stand_light_S+19.03s", "end": "shutdown"},
          "B1_R4_GVLO": {"rz1": "rezero1_end_S+1.4s", "rz2": "stand_rezero2_end_S+15.72s", "E1": "stand_E1_S+18.715s",
                         "light": "stand_light_S+19.03s", "end": "shutdown"}}
    # sensor (seat-TC) node = the restated monitor node of T1_head_top_bracket_foot (xcheck at_monitor_node_K)
    def mon(rn, key): return xchk["runs"][rn]["MON_proxy_drifts"][key + "|T1_head_top_bracket_foot"]["at_monitor_node_K"]
    sens = {"A1_NF2b": {"rz1": mon("A1_NF2b", "ARM->rezero1_end"), "E1": mon("A1_NF2b", "ARM->E1"), "light": mon("A1_NF2b", "ARM->light")}}
    sens["A1_NF2b"]["rz2"] = sens["A1_NF2b"]["E1"] - mon("A1_NF2b", "rezero2_end->E1")
    for rn in ("B1_R4_GVHI", "B1_R4_GVLO"):
        sens[rn] = {"rz1": mon(rn, "ARM->rezero1_end"), "E1": mon(rn, "ARM->stand_E1"), "light": mon(rn, "ARM->stand_light")}
        sens[rn]["rz2"] = sens[rn]["E1"] - mon(rn, "stand_rezero2_end->stand_E1")
    rise, rate, grad = {}, {}, {}
    for rn, m in ev.items():
        a = seat["runs"][rn]; T0 = a["T_K_at_events"]["ARM"]["diaphragm_zt-9.5"]; h = a["history_diaphragm"]
        rise[rn] = {k: a["T_K_at_events"][v]["diaphragm_zt-9.5"] - T0 for k, v in m.items()}
        rate[rn] = {}
        for k, v in m.items():
            t = a["T_K_at_events"][v]["t_s"]
            lo = max(x for x in h if x[0] <= t - 0.4); hi = min(x for x in h if x[0] >= t + 0.4)
            rate[rn][k] = (hi[1] - lo[1]) / (hi[0] - lo[0])
        grad[rn] = {k: sens[rn][k] - rise[rn][k] for k in sens[rn]}
    out["rise_K_diaphragm"] = {rn: {k: round(v, 3) for k, v in d.items()} for rn, d in rise.items()}
    out["rise_K_sensor_node"] = {rn: {k: round(v, 3) for k, v in d.items()} for rn, d in sens.items()}
    out["gradient_K_sensor_minus_diaphragm"] = {rn: {k: round(v, 3) for k, v in d.items()} for rn, d in grad.items()}
    out["diaphragm_rate_K_per_s"] = {rn: {k: round(v, 3) for k, v in d.items()} for rn, d in rate.items()}
    F = f0(0.0)
    out["T0_factor_0C_40C"] = [round(f0(0.0), 4), round(f0(40.0), 4)]
    st = ("B1_R4_GVHI", "B1_R4_GVLO")
    unc, opt_a, kb = {}, {}, {}
    for k in KS:
        a = k * C_ROUND
        r = {"A1_rz2_shift": a * rise["A1_NF2b"]["rz2"] * F, "A1_rz1_shift": a * rise["A1_NF2b"]["rz1"] * F,
             "A1_ARM_E1": a * rise["A1_NF2b"]["E1"] * F, "A1_rz2_E1": a * (rise["A1_NF2b"]["E1"] - rise["A1_NF2b"]["rz2"]) * F,
             "stand_rz1_shift": a * max(rise[s]["rz1"] for s in st) * F, "stand_rz2_shift": a * max(rise[s]["rz2"] for s in st) * F,
             "stand_ARM_E1": a * max(rise[s]["E1"] for s in st) * F, "stand_rz2_E1": a * max(rise[s]["E1"] - rise[s]["rz2"] for s in st) * F}
        unc[str(k)] = {x: round(y, 4) for x, y in r.items()}
        LA, LS = r["A1_rz2_shift"] + ADD, r["stand_rz2_shift"] + ADD
        opt_a[str(k)] = {"limit_A1": round(LA, 3), "limit_stand": round(LS, 3), "nonvented_accepted_A1": round(LA + r["A1_rz2_shift"], 3),
                         "nonvented_accepted_stand": round(LS + r["stand_rz2_shift"], 3)}
    out["uncompensated_bar"] = unc; out["option_a_bar"] = opt_a
    out["k_v211_rz2_rejected"] = {"A1_F1.0166": round(LIM / (C_ROUND * rise["A1_NF2b"]["rz2"] * F), 3),
                                  "A1_T0_20C": round(LIM / (C_ROUND * rise["A1_NF2b"]["rz2"]), 3),
                                  "stand_F1.0166": round(LIM / (C_ROUND * max(rise[s]["rz2"] for s in st) * F), 3)}
    # option (b) residual, worst-case linear sum: eps k c rise F + k c (|grad| + tau rate + TC err)
    def resid(rn, ev_, k, eps, tcerr=TCERR, tau=TAU):
        a = k * C_ROUND
        return eps * a * rise[rn][ev_] * F + a * (abs(grad[rn][ev_]) + tau * abs(rate[rn][ev_]) + tcerr)
    ob = {}
    for eps in (0.10, 0.05, 0.04, 0.0):
        for k in KS:
            A1 = resid("A1_NF2b", "rz2", k, eps); S = max(resid(s, "rz2", k, eps) for s in st)
            S1 = max(resid(s, "rz1", k, eps) for s in st)
            ob["eps%.2f_k%.1f" % (eps, k)] = {"A1_rz2": round(A1, 3), "A1_rz2_plus_adders": round(A1 + ADD, 3), "A1_accepted": A1 + ADD <= LIM,
                                              "stand_rz1": round(S1, 3), "stand_rz2": round(S, 3), "stand_rz2_plus_adders": round(S + ADD, 3),
                                              "stand_rz2_accepted_with_adders": S + ADD <= LIM, "stand_rz2_accepted_without_adders": S <= LIM}
    out["option_b_residual_bar"] = ob
    # largest k at which the stand re-zero2 is accepted, by eps, with and without the 0.1012 bar adders
    def kmax(eps, add):
        k = 0.0
        while k < 5.0 and max(resid(s, "rz2", k + 0.001, eps) for s in st) + add <= LIM: k += 0.001
        return round(k, 3)
    out["stand_rz2_kmax_by_eps"] = {"%.2f" % e: {"with_adders": kmax(e, ADD), "without_adders": kmax(e, 0.0)} for e in (0.0, 0.03, 0.04, 0.05, 0.10)}
    def kmaxA(eps, add):
        k = 0.0
        while k < 8.0 and resid("A1_NF2b", "rz2", k + 0.001, eps) + add <= LIM: k += 0.001
        return round(k, 3)
    out["A1_rz2_kmax_by_eps"] = {"%.2f" % e: {"with_adders": kmaxA(e, ADD), "without_adders": kmaxA(e, 0.0)} for e in (0.05, 0.10, 0.15, 0.20)}
    # U330 band shift s k c ((T0 - 20 C) + F rise) at the burn ends and the stand relight light
    u = {}
    for k in KS:
        a = k * C_ROUND
        for lab, rn, e_, T0C in (("A1_relight_end_T0_40C", "A1_NF2b", "end", 40.0), ("A1_relight_end_T0_20C", "A1_NF2b", "end", 20.0),
                                 ("B1_end_T0_24C", "B1_R4_GVLO", "end", 24.0), ("stand_relight_light_T0_24C", "B1_R4_GVLO", "light", 24.0),
                                 ("stand_relight_light_T0_24C_GVHI", "B1_R4_GVHI", "light", 24.0)):
            sh = a * ((T0C - 20.0) + F * rise[rn][e_])
            u["k%.1f_%s" % (k, lab)] = {"shift_bar": round(sh, 3), "low_end_bar_abs": round(U330_TRIP - U330_HALF - sh, 2),
                                        "high_end_bar_abs": round(U330_TRIP + U330_HALF + sh, 2)}
    out["U330_band"] = u
    lowlim = U330_TRIP - U330_HALF - FW30
    out["U330_k_low_end_below_30"] = {lab: round(lowlim / (C_ROUND * ((T0C - 20.0) + F * rise[rn][e_])), 3) for lab, rn, e_, T0C in
                                     (("A1_relight_end_T0_40C", "A1_NF2b", "end", 40.0), ("A1_relight_end_T0_20C", "A1_NF2b", "end", 20.0),
                                      ("B1_end_T0_24C", "B1_R4_GVLO", "end", 24.0), ("stand_relight_light_T0_24C", "B1_R4_GVLO", "light", 24.0),
                                      ("stand_relight_light_T0_0C", "B1_R4_GVLO", "light", 0.0))}
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1, sort_keys=True))
    print(json.dumps(out, indent=1, sort_keys=True))

if __name__ == "__main__":
    main()
