"""Head-end bleed concept (coordinator 2026-10-13, concept (a)) and the coast vapour-generation history (lead relay 3 item 4).
v1, 2026-10-13, Mechanical.

Inputs (read only): calcs/segment_traps_v34_v1p1.json (trap capacities and crowns on the CAD v3.4 solids, drogue attitude) and
04-fea/thermal/segment_heat_budget_v1.json v1.1 (head-end heat input W(t) from MECO to RELIGHT, LO / HI bounds).

Method:
  1. Saturated N2O at T_coast 289.48 K from CoolProp (Span-Wagner class EOS; LITERATURE).
  2. Vapour generation V_gen(t) = integral Q dt / (h_fg rho_v) of the head-end series; the needle-tip energy (not time resolved,
     ESTIMATE 50 / 150 J) is spread uniformly over the coast.  t_fill = time at which V_gen reaches the trap capacity.
  3. Bleed orifice flow: choked HEM mass flux (isentropic, equilibrium, CoolProp) from saturated vapour (x = 1) and saturated
     liquid (x = 0) at p_sat; SPI liquid bound G = sqrt(2 rho_l (p_sat - p_amb)); Dyer mean (kappa = 1 at saturation) as the
     central liquid value.  Cd 0.6 / 0.8 ASSUMED (sharp-edged / short-tube orifice).
  4. Forced purge (MV open, pintle seated, bleed open): t_purge = rho_v V_trap / (Cd A G_v - rho_v q_gen), q_gen = vapour
     generation rate at relight (LO / HI head-end series end value).  Valid only with the MV OPEN: with the MV closed the bleed
     depressurises the isolated segment and flashes its liquid (not a purge).
  5. Failed-open bleed during a burn: liquid loss vs the engine flow 0.24 kg/s (segment_heat_budget h_flow basis).
  6. Element barrier: Taylor-bubble rise velocity 0.35 sqrt(g D) in the 8 mm legs, the liquid flow that sweeps a bubble down, and
     the element dp at the purge flow (filter requirement Cv >= 2.2, REQUIREMENTS sec. 3) against the bubble point range of the trap
     script (49-130 mm of liquid at 8 m/s2, ESTIMATE).
  7. Gimbal sensitivity per 10 g at the bleed location (v3.3 massprops I about the pivot, mid-burn mass; v3.4 values come from make_all).
Output: calcs/headend_bleed_concept_v1.json.  CONCEPT-LEVEL: DERIVED from ASSUMED discharge coefficients and literature properties;
valve selection, mass and overboard port are TO-DEFINE / TO-QUOTE.  Not a two-phase transient model.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
import CoolProp.CoolProp as CP

HERE = Path(__file__).resolve().parent
OUT = HERE / "headend_bleed_concept_v1.json"
TRAPS = HERE / "segment_traps_v34_v1p1.json"
BUDGET = HERE.parents[2] / "04-fea" / "thermal" / "segment_heat_budget_v1.json"
T = 289.48                  # K, coast saturation temperature (segment_heat_budget v1.1)
P_AMB = 0.1e6               # Pa, overboard back pressure (ASSUMED sea-level class)
CD = (0.6, 0.8)             # ASSUMED
D_ORIF = (0.3, 0.4, 0.5, 0.6, 0.8, 1.0)   # mm
MDOT_ENGINE = 0.24          # kg/s (segment_heat_budget h_flow basis)
G_DROGUE = 8.0              # m/s2 (lead: >= 11.4 s of +8 m/s2)
D_LEG = 8.0e-3              # m, FD-01 / TC-02 / TC-04 drillings (CAD v3.4)
CV_FILTER = 2.2             # REQUIREMENTS sec. 3, minimum
BUBBLE_MM = (49.0, 130.0)   # mm of liquid at 8 m/s2 (segment_traps_v34 method item 4, ESTIMATE)
MASSPROPS = {"I_pivot_kgm2": 0.0522, "m_kg": 2.417, "src": "massprops_v2.json (CAD v3.3, mid-burn); v3.4 values from make_all"}


def sat():
    p = CP.PropsSI("P", "T", T, "Q", 0, "N2O")
    out = {"p_sat_Pa": p}
    for q, k in ((0, "l"), (1, "v")):
        out[f"rho_{k}"] = CP.PropsSI("D", "T", T, "Q", q, "N2O")
        out[f"h_{k}"] = CP.PropsSI("H", "T", T, "Q", q, "N2O")
        out[f"s_{k}"] = CP.PropsSI("S", "T", T, "Q", q, "N2O")
    out["h_fg_J_kg"] = out["h_v"] - out["h_l"]
    out["sigma_N_m"] = CP.PropsSI("I", "T", T, "Q", 0, "N2O")
    return out


def hem_choked(p0, h0, s0, p_min=0.3e6, n=400):
    """Max over the downstream pressure of rho(p, s0) sqrt(2 (h0 - h(p, s0))): HEM critical mass flux, kg/m2 s."""
    best = (0.0, p0)
    for p in np.linspace(p0 * 0.999, p_min, n):
        try:
            h = CP.PropsSI("H", "P", p, "S", s0, "N2O")
            d = CP.PropsSI("D", "P", p, "S", s0, "N2O")
        except ValueError:
            continue
        if h >= h0:
            continue
        G = d * math.sqrt(2.0 * (h0 - h))
        if G > best[0]:
            best = (G, p)
    return {"G_kg_m2s": round(best[0], 1), "p_throat_MPa": round(best[1] / 1e6, 3)}


def series_fill(budget, caps):
    v = budget["head_end_W_vs_t"]["v"]
    out = {}
    for key in ("isothermal|LO", "isothermal|HI", "ARM_bay45C_liq24C|LO", "ARM_bay45C_liq24C|HI"):
        r = v[key]
        t = np.array(r["t_s"]); q = np.array(r["Q_head_end_W"])
        q_needle = r["needle_not_time_resolved_J"] / (t[-1] - t[0])
        qt = q + q_needle
        E = np.concatenate([[0.0], np.cumsum(0.5 * (qt[1:] + qt[:-1]) * np.diff(t))])
        return_rows = []
        for ts in (0.0, 1.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, t[-1] - t[0]):
            tt = t[0] + ts
            return_rows.append({"t_after_MECO_s": round(ts, 2), "Q_head_end_W": round(float(np.interp(tt, t, q)), 1),
                                "E_cum_J_incl_needle": round(float(np.interp(tt, t, E)), 1)})
        out[key] = {"rows": return_rows, "E_total_J_incl_needle": round(float(E[-1]), 1), "Q_at_relight_W": round(float(q[-1]), 1),
                    "q_needle_W_uniform": round(q_needle, 2), "t_meco_s": t[0], "t_relight_s": t[-1], "_t": t, "_E": E}
    return out


def main():
    S = sat()
    vpj = 1.0 / (S["h_fg_J_kg"] * S["rho_v"]) * 1e6          # cm3 of vapour per J
    traps = json.loads(TRAPS.read_text())
    budget = json.loads(BUDGET.read_text())
    cap = {"barrier": traps["cases_nominal_attitude"]["MV_closed|barrier|+Z"]["retained_total_cm3"],
           "open_element": traps["cases_nominal_attitude"]["MV_closed|open_element|+Z"]["retained_total_cm3"]}
    tilt = traps["tilt_sensitivity"]
    cap_tilt10 = {m: [min(r["trapped_cm3"] + r["isolated_cm3"] for r in tilt if r["model"] == m and r["tilt_deg"] == 10.0),
                      max(r["trapped_cm3"] + r["isolated_cm3"] for r in tilt if r["model"] == m and r["tilt_deg"] == 10.0)] for m in cap}
    fill = series_fill(budget, cap)
    hist = {}
    for k, r in fill.items():
        t, E = r.pop("_t"), r.pop("_E")
        V = E * vpj
        tf = {}
        for m, c in cap.items():
            idx = np.nonzero(V >= c)[0]
            tf[m] = None if len(idx) == 0 else round(float(np.interp(c, V, t) - t[0]), 2)
        for row in r["rows"]:
            row["V_gen_cm3"] = round(row["E_cum_J_incl_needle"] * vpj, 2)
        r["V_gen_total_cm3"] = round(float(V[-1]), 1)
        r["t_fill_capacity_after_MECO_s"] = tf
        r["retained_at_relight_cm3 (= min(V_gen, capacity))"] = {m: round(min(float(V[-1]), c), 2) for m, c in cap.items()}
        r["q_gen_at_relight_cm3_s"] = round((r["Q_at_relight_W"] + r["q_needle_W_uniform"]) * vpj, 2)
        hist[k] = r
    Gv = hem_choked(S["p_sat_Pa"], S["h_v"], S["s_v"])
    Gl_hem = hem_choked(S["p_sat_Pa"], S["h_l"], S["s_l"])
    G_spi = math.sqrt(2.0 * S["rho_l"] * (S["p_sat_Pa"] - P_AMB))
    G_dyer = 0.5 * (G_spi + Gl_hem["G_kg_m2s"])
    V_trap = cap["open_element"]
    rows = []
    for d in D_ORIF:
        A = math.pi / 4 * (d * 1e-3) ** 2
        for cd in CD:
            mv = cd * A * Gv["G_kg_m2s"]
            row = {"d_mm": d, "Cd": cd, "vapour_g_s": round(mv * 1e3, 2), "vapour_cm3_s": round(mv / S["rho_v"] * 1e6, 1)}
            for key in ("isothermal|LO", "isothermal|HI", "ARM_bay45C_liq24C|HI"):
                qg = hist[key]["q_gen_at_relight_cm3_s"] * 1e-6 * S["rho_v"]          # kg/s of vapour generated
                net = mv - qg
                row[f"t_purge_{V_trap:.1f}cm3_s|{key}"] = None if net <= 0 else round(S["rho_v"] * V_trap * 1e-6 / net, 2)
            ml = (cd * A * Gl_hem["G_kg_m2s"], cd * A * G_dyer, cd * A * G_spi)
            row["liquid_g_s_HEM_Dyer_SPI"] = [round(x * 1e3, 1) for x in ml]
            row["failed_open_share_of_engine_flow_pct"] = round(ml[2] / MDOT_ENGINE * 100, 1)
            rows.append(row)
    U_tb = 0.35 * math.sqrt(G_DROGUE * D_LEG)
    m_sweep = S["rho_l"] * U_tb * math.pi / 4 * D_LEG ** 2
    elem = []
    for mdot in (0.005, 0.015, 0.05, MDOT_ENGINE):
        Q_gpm = mdot / S["rho_l"] * 15850.3
        dp = (S["rho_l"] / 999.0) * (Q_gpm / CV_FILTER) ** 2 * 6894.76
        elem.append({"mdot_g_s": round(mdot * 1e3, 1), "element_dp_Pa_at_Cv2.2": round(dp, 1),
                     "vs_bubble_point_Pa": [round(S["rho_l"] * G_DROGUE * b * 1e-3, 1) for b in BUBBLE_MM]})
    sens = []
    for name, (r_mm, z_mm) in {"T4 port (TC-04 bonnet, crown z 192.6)": (20.4, 192.6), "FD-01 top (crown z 160.4)": (41.9, 160.4)}.items():
        dI = 0.010 * ((z_mm * 1e-3) ** 2 + 0.5 * (r_mm * 1e-3) ** 2)
        sens.append({"location": name, "dI_per_10g_kgm2": round(dI, 6), "dI_pct": round(dI / MASSPROPS["I_pivot_kgm2"] * 100, 2),
                     "dz_cg_per_10g_mm": round(0.010 * z_mm / MASSPROPS["m_kg"], 2)})
    crowns = traps["local_high_points"]
    out = {"id": "headend_bleed_concept", "version": "v1", "date": "2026-10-13", "owner": "mechanical",
           "script": "03-cad/src/calcs/headend_bleed_concept_v1.py", "method": __doc__.split("\n\n")[2],
           "inputs": {"traps": "calcs/segment_traps_v34_v1p1.json", "heat": "04-fea/thermal/segment_heat_budget_v1.json (v1.1)"},
           "n2o_sat": {k: (round(v, 4) if isinstance(v, float) else v) for k, v in S.items()}, "vapour_cm3_per_J": round(vpj, 5),
           "capacity_cm3_nominal": cap, "capacity_cm3_tilt10_min_max": cap_tilt10,
           "crowns_drogue_attitude": {"downstream_T4": crowns["MV_closed|barrier|downstream of the element (vent = element surface)"][0],
                                      "upstream_FD01": crowns["MV_closed|barrier|vent S1"][0]},
           "coast_history": hist,
           "orifice": {"G_vapour_HEM": Gv, "G_liquid_HEM": Gl_hem, "G_liquid_SPI_kg_m2s": round(G_spi, 1), "G_liquid_Dyer_kg_m2s": round(G_dyer, 1),
                       "rows": rows},
           "element_barrier": {"U_taylor_m_s_8mm_8g": round(U_tb, 4), "mdot_to_sweep_bubble_down_8mm_g_s": round(m_sweep * 1e3, 2),
                               "element_dp": elem,
                               "note": "with the element as a capillary barrier, a purge flow through a <= 1 mm bleed does not push the upstream "
                                       "pocket through the element (dp << bubble point): a bleed at the T4 port vents only the downstream region; the "
                                       "upstream crown needs its own bleed (FD-01 top) or the filter moved off the head end"},
           "gimbal_sensitivity": {"rows": sens, "basis": MASSPROPS},
           "tag": "CONCEPT, DERIVED from LITERATURE properties and ASSUMED Cd; valve, mass and overboard port TO-DEFINE / TO-QUOTE"}
    OUT.write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps({k: out[k] for k in ("n2o_sat", "vapour_cm3_per_J", "capacity_cm3_nominal", "capacity_cm3_tilt10_min_max")}, indent=0))
    for k, r in hist.items():
        print(k, r["E_total_J_incl_needle"], r["V_gen_total_cm3"], r["t_fill_capacity_after_MECO_s"], r["q_gen_at_relight_cm3_s"])
        print("   ", [(x["t_after_MECO_s"], x["Q_head_end_W"], x["V_gen_cm3"]) for x in r["rows"]])
    print(Gv, Gl_hem, round(G_spi, 1), round(G_dyer, 1))
    for r in rows:
        print(r)
    print(out["element_barrier"])
    print(sens)


if __name__ == "__main__":
    main()
