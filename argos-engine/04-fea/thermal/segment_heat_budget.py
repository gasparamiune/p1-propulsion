"""MV-to-seat segment heat input from MECO to RELIGHT, A1, Option A route (04-fea/thermal, v1, 2026-10-13, Mechanical).

Lead relay 2026-10-13 item 5: retained vapour in the MV-to-seat segment <= 19 cm3 at RELIGHT; if all vapour is retained
that is a mean heat input <= 24 W over ~22 s (lead basis ~528 J at 20 C properties).  Asked: the heat input along the
zone-top route (wall line, coil, block, head end) for A1, and insulation or a re-route if it exceeds 24 W.

Method (per element, DERIVED from DESIGN geometry + ASSUMED heat-transfer inputs, all listed in the output):
  1-D implicit finite-difference slab through the wetted wall (planar; layers per element), from ignition to RELIGHT.
  Inner face: burn = forced convection h_flow(t) to the liquid temperature T_liq(t) of the Combustion head-end BC CSV
  (Dittus-Boelter for the 3/8 line at 0.24 kg/s ~14.3 kW/m2K, scaled (mdot/0.24)^0.8 (7.75/D)^1.8; mu 0.07 mPa s ASSUMED);
  coast = static liquid at T_sat, two bounds:
     LO  h 376 W/m2K (the Combustion convention G_N2O_COAST 1 W/K on the 2660 mm2 manifold bore),
     HI  nucleate boiling, Cooper (1984) h = 55 pr^0.12 (-log10 pr)^-0.55 M^-0.5 q^0.67 (Rp 1 um), capped 20 kW/m2K
         (1-g pool-boiling correlation; in the ballistic coast the liquid is near 0 g -> the true value lies between LO and HI).
  Back face per element: adiabatic (thick bodies: heat-capacity depth = volume / wetted area), bay air, or the FE
  far-field temperature history of the head/bonnet region (segment_heat_coast_v1.json regions, A1 run) for the E1-M
  off-axis drillings, which are not in the 2-D section.
  The head-end manifold bore itself comes from the 2-D FE runs (segment_heat_coast_v1.json): G 1 W/K run = LO,
  G 10 W/K run = HI (when available).
  Heat into the liquid only counts when positive; all of it is taken as vapour (h_fg, rho_v at the coast T_sat, CoolProp).
  Not credited: liquid sensible heating inside the check-valve crack subcooling (~0.7 K, ~70 J for 36 g, Combustion
  segment_recheck_v2p4), vapour condensation, and any vapour expelled through the FS-01 back-relief check.
Hardware temperature at ignition: base = liquid temperature at ignition (isothermal pad soak); +5 K; ARM bound
(bay 45 C hardware, liquid 24 C).  The FE head end starts at its own T_INIT 293.15 K.

usage: segment_heat_budget.py [--fe_lo LABEL] [--fe_hi LABEL] [--dc DC-A1dispp99_tg711]
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "src"))
import engmat

COMB = Path("/home/claude/work/shared-fallback/engine/02-combustion/data/v2")
OUT = HERE / "segment_heat_budget_v1.json"
SEG = HERE / "segment_heat_coast_v1.json"

POLY = {"PTFE": {"rho": 2200.0, "k": 0.25, "cp": 1000.0, "tag": "LITERATURE-approx (PTFE handbook class: k 0.24-0.26, cp 1.0 kJ/kgK), verify"}}
H_FLOW_REF, D_REF, MDOT_REF = 14300.0, 7.75, 0.24
H_LO, H_CAP = 376.0, 20000.0
PC, MW = 72.45e5, 44.013


def props(mat):
    if mat in POLY:
        p = POLY[mat]
        return p["rho"], (lambda T: p["k"]), (lambda T: p["cp"])
    return engmat.rho(mat), (lambda T: engmat.prop(mat, "k", T - 273.15)), (lambda T: engmat.prop(mat, "cp", T - 273.15))


# ------------------------------------------------------------------------------------------- elements (Option A, CAD v3.4)
# A_mm2 wetted area, layers [(mat, t_mm)] from the wetted face outward, D_mm flow diameter, back: 'adiabatic' | ('air', h) |
# ('far', region).  All DESIGN/ESTIMATE until the CAD v3.4 solids are measured (03-cad/checks/inlet_e1m_volumes.json).
ELEMENTS = [
    {"name": "MV/FS-01 module, outlet side (316L body)", "A_mm2": 2600.0, "layers": [("SS316L", 10.0)], "D_mm": 10.0, "back": "adiabatic",
     "tag": "ESTIMATE planned layout: outlet chamber 14 x 18, outlet drilling 8 x 30, 5 ports (J602, disc, MSS-2, check, vent plug); depth = outlet-side body share ~25 cm3 / area"},
    {"name": "fixed wall line 3/8 x 0.035 316L, module -> coil (~250 mm)", "A_mm2": math.pi * 7.747 * 250.0, "layers": [("SS316L", 0.889)],
     "D_mm": 7.75, "back": ("air", 5.0), "tag": "DESIGN route r ~64, z 240 -> 62; bay air 5 W/m2K ASSUMED; case radiation <= 0.2 W (F 0.165) neglected"},
    {"name": "line-coil union / 90 deg elbow (316)", "A_mm2": 600.0, "layers": [("SS316L", 3.0)], "D_mm": 7.75, "back": "adiabatic", "tag": "ESTIMATE"},
    {"name": "coil hose ends 2x -6 JIC swivel + nipple (316)", "A_mm2": 1400.0, "layers": [("SS316L", 3.0)], "D_mm": 7.0, "back": "adiabatic",
     "tag": "ESTIMATE"},
    {"name": "coil hose O3b 0.252 m, PTFE liner 1.0 + SS braid 0.5 (equivalent)", "A_mm2": math.pi * 8.0 * 252.0,
     "layers": [("PTFE", 1.0), ("SS316L", 0.5)], "D_mm": 8.0, "back": "adiabatic",
     "tag": "ESTIMATE -6 PTFE-lined hose class (ID 8.0, liner 1.0 mm TO-CONFIRM with the hose maker)"},
    {"name": "FD-05 TEE + MSS-1 port (316L)", "A_mm2": 700.0, "layers": [("SS316L", 7.0)], "D_mm": 7.75, "back": "adiabatic", "tag": "ESTIMATE ~40 g block"},
    {"name": "FD-03 riser 3/8 x 0.035 316L (~130 mm)", "A_mm2": math.pi * 7.747 * 130.0, "layers": [("SS316L", 0.889)], "D_mm": 7.75,
     "back": ("air", 5.0), "tag": "DESIGN; behind the FD-04 foil shield (case radiation neglected)"},
    {"name": "FD-01 inlet block (316L, ~52 g)", "A_mm2": 614.0, "layers": [("SS316L", 10.0)], "D_mm": 8.0, "back": "adiabatic",
     "tag": "ESTIMATE socket + vertical 8 x 7.5 + radial 8 x 11; contact with the warming head cap not credited (adds heat)"},
    {"name": "TC-02 head cap: filter bore 14 x 21 + axial 8 x 7 (6061)", "A_mm2": 1254.0, "layers": [("AL6061-T6", 8.0)], "D_mm": 12.0,
     "back": ("far", "head_filter_bore"), "tag": "DESIGN E1-M; back face = FE head region mean (soak-back), depth 8 mm ASSUMED"},
    {"name": "TC-04 bonnet: axial 8 x 26 + cross 8 x 14 + T4 port (6061)", "A_mm2": 1278.0, "layers": [("AL6061-T6", 6.0)], "D_mm": 8.0,
     "back": ("far", "bonnet_boss"), "tag": "DESIGN E1-M; back face = FE bonnet region mean, depth 6 mm ASSUMED"},
]
NEEDLE = {"name": "TC-05 needle tip (not in the 2-D model)", "E_J": [50.0, 150.0],
          "tag": "ESTIMATE: 17-4PH cone below the seat ~0.56 g at 200-500 K above the liquid at MECO + the conduction-heated body; to be modelled"}


def cooper_C(Tsat):
    import CoolProp.CoolProp as CP
    pr = CP.PropsSI("P", "T", Tsat, "Q", 0, "NitrousOxide") / PC
    return 55.0 * pr ** 0.12 * (-math.log10(pr)) ** -0.55 * MW ** -0.5, pr


def h_boil(dT, C):
    """Cooper h(q) with q = h dT -> h = C^(1/0.33) dT^(0.67/0.33); capped."""
    if dT <= 0:
        return 0.0
    return min(H_CAP, C ** (1 / 0.33) * dT ** (0.67 / 0.33))


def slab(el, t_grid, T_liq, mdot, burning, T0, coast_mode, C, far=None, n_per_mm=4):
    xs, mats = [], []
    for mat, th in el["layers"]:
        n = max(3, int(round(th * n_per_mm)))
        xs += [th * 1e-3 / n] * n
        mats += [mat] * n
    dx = np.array(xs)
    N = len(dx)
    P = {m: props(m) for m in set(mats)}
    rho = np.array([P[m][0] for m in mats])
    T = np.full(N, float(T0))
    A = el["A_mm2"] * 1e-6
    E_coast, q_hist = 0.0, []
    for k in range(1, len(t_grid)):
        dt = t_grid[k] - t_grid[k - 1]
        t = t_grid[k]
        kk = np.array([P[m][1](T[i]) for i, m in enumerate(mats)])
        cp = np.array([P[m][2](T[i]) for i, m in enumerate(mats)])
        Cn = rho * cp * dx / dt
        kf = 2.0 / (dx[:-1] / kk[:-1] + dx[1:] / kk[1:])
        M = np.zeros((N, N)); b = Cn * T
        idx = np.arange(N - 1)
        M[idx, idx] += kf; M[idx, idx + 1] -= kf; M[idx + 1, idx + 1] += kf; M[idx + 1, idx] -= kf
        M[np.arange(N), np.arange(N)] += Cn
        Tl = T_liq[k]
        if burning[k]:
            h = H_FLOW_REF * max(mdot[k] / MDOT_REF, 1e-3) ** 0.8 * (D_REF / el["D_mm"]) ** 1.8
        else:
            h = H_LO if coast_mode == "LO" else h_boil(T[0] - Tl, C)
        M[0, 0] += h; b[0] += h * Tl
        bk = el["back"]
        if isinstance(bk, tuple) and bk[0] == "air":
            M[-1, -1] += bk[1]; b[-1] += bk[1] * T0
        elif isinstance(bk, tuple) and bk[0] == "far":
            kb = 2 * kk[-1] / dx[-1]
            M[-1, -1] += kb; b[-1] += kb * float(np.interp(t, far[0], far[1]))
        T = np.linalg.solve(M, b)
        q = h * (T[0] - Tl) * A                      # W into the liquid (implicit)
        if not burning[k]:
            E_coast += max(q, 0.0) * dt
            q_hist.append((round(float(t), 2), round(float(q), 2)))
    return E_coast, q_hist


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dc", default="DC-A1dispp99_tg711")
    ap.add_argument("--fe_lo", default="DC-A1dispp99_hi_SS316L_L2.5_v11pre36")
    ap.add_argument("--fe_hi", default=None)
    ap.add_argument("--far", default=None, help="FE label for the head/bonnet far-field histories (default fe_lo)")
    a = ap.parse_args()
    import CoolProp.CoolProp as CP
    f = COMB / f"headend_bc_{a.dc}_v2.csv"
    d = np.genfromtxt(f, delimiter=",", names=True, skip_header=1)
    t, b, TL, md = d["t_s"], d["burning"] > 0.5, d["T_N2O_liquid_K"], d["mdot_ox_kg_s"]
    on = np.nonzero(b)[0]
    k_meco = on[np.nonzero(np.diff(on) > 1)[0][0]]
    t_meco, t_rel = float(t[k_meco]), float(t[on[np.nonzero(np.diff(on) > 1)[0][0] + 1]])
    sel = t <= t_rel + 1e-9
    t_grid = np.unique(np.concatenate([np.arange(0.0, t_meco, 0.02), np.arange(t_meco, t_rel + 1e-9, 0.05), [t_meco, t_rel]]))
    T_liq = np.interp(t_grid, t[sel], TL[sel])
    mdot = np.interp(t_grid, t[sel], md[sel])
    burning = t_grid <= t_meco + 1e-9
    T_sat = float(T_liq[-1])
    C, pr = cooper_C(T_sat)
    hfg = CP.PropsSI("H", "T", T_sat, "Q", 1, "NitrousOxide") - CP.PropsSI("H", "T", T_sat, "Q", 0, "NitrousOxide")
    rv = CP.PropsSI("D", "T", T_sat, "Q", 1, "NitrousOxide")
    seg = json.loads(SEG.read_text())["runs"]
    far_lab = a.far or a.fe_lo
    reg = seg[far_lab]["regions"]
    far = {k: (np.array(reg["t_s"]), np.array(v)) for k, v in reg["T_mean_K"].items()}
    T_liq0 = float(T_liq[0])
    cases = {"isothermal": T_liq0, "hw+5K": T_liq0 + 5.0, "ARM_bay45C_liq24C": T_liq0 + 21.0}
    out = {"script": "04-fea/thermal/segment_heat_budget.py v1.1 (W(t) series added 2026-10-13)", "date": "2026-10-13", "dc": a.dc, "headend_csv": str(f),
           "t_meco_s": t_meco, "t_relight_s": t_rel, "coast_s": round(t_rel - t_meco, 3), "T_liq_ignition_K": round(T_liq0, 2),
           "T_sat_coast_K": round(T_sat, 2), "p_r": round(pr, 3), "h_fg_J_g": round(hfg / 1e3, 1), "rho_v_kg_m3": round(rv, 1),
           "budget": {"lead": "19 cm3 retained vapour <= 24 W x ~22 s = 528 J (20 C basis)",
                      "at_coast_Tsat_J": round(19e-6 * rv * hfg, 0)},
           "assumptions": {"h_flow": "Dittus-Boelter 14.3 kW/m2K at 0.24 kg/s in 7.75 mm, x (mdot/0.24)^0.8 (7.75/D)^1.8, ESTIMATE",
                           "coast_LO": f"h {H_LO} W/m2K (Combustion G_N2O_COAST 1 W/K convention)",
                           "coast_HI": f"Cooper nucleate boiling, C {C:.2f}, cap {H_CAP} W/m2K (1-g correlation, ESTIMATE)",
                           "PTFE": POLY["PTFE"]["tag"], "far_field": f"FE regions of {far_lab}"},
           "elements": [], "needle": NEEDLE, "fe_head_bore": {}}
    for lab, key in ((a.fe_lo, "LO"), (a.fe_hi, "HI")):
        if lab and lab in seg:
            r = seg[lab]
            out["fe_head_bore"][key] = {"label": lab, "G_W_K": r["G_N2O_COAST_W_K"], "E_coast_J": r["E_coast_J"], "coast_s": r["coast_s"],
                                        "E_22s_J": r.get("E_22s_extrapolated_J"), "E_by_part_J": r["E_by_part_J"],
                                        "material_overrides": r.get("material_overrides")}
    fe = out["fe_head_bore"]
    ratio = fe["HI"]["E_coast_J"] / fe["LO"]["E_coast_J"] if "HI" in fe and "LO" in fe else None
    out["far_field_HI_rule"] = ("E1-M off-axis drillings (back face = FE far field): the Dirichlet far field is an unlimited source under a "
                                "stiff boiling sink, so HI = LO x (FE head-bore E at G 10 W/K / E at G 1 W/K) = x " +
                                (f"{ratio:.2f}" if ratio else "n/a (no G 10 run given: HI not computed for these elements)"))
    for el in ELEMENTS:
        grp = "head" if (el["name"].startswith(("FD-01", "TC-02", "TC-04"))) else "route"
        row = {"name": el["name"], "group": grp, "A_mm2": round(el["A_mm2"], 0), "layers": el["layers"], "back": str(el["back"]), "tag": el["tag"],
               "E_coast_J": {}}
        is_far = isinstance(el["back"], tuple) and el["back"][0] == "far"
        for cn, T0 in cases.items():
            for mode in ("LO", "HI"):
                fr = far[el["back"][1]] if is_far else None
                T0e = float(fr[1][0]) + (T0 - T_liq0) if fr is not None else T0
                if fr is not None:
                    fr = (fr[0], fr[1] + (T0 - T_liq0))
                if is_far and mode == "HI":
                    lo = row["E_coast_J"][f"{cn}|LO"]
                    row["E_coast_J"][f"{cn}|HI"] = round(lo * ratio, 1) if ratio else None
                    if ratio and f"{cn}|LO" in row.get("Q_coast_W", {}):
                        row["Q_coast_W"][f"{cn}|HI"] = [round(v * ratio, 2) for v in row["Q_coast_W"][f"{cn}|LO"]]
                    continue
                E, qh = slab(el, t_grid, T_liq, mdot, burning, T0e, mode, C, far=fr)
                row["E_coast_J"][f"{cn}|{mode}"] = round(float(E), 1)
                if qh:
                    qa = np.array(qh)
                    ts_ = np.arange(t_meco, t_rel + 1e-9, 0.25)
                    row.setdefault("Q_coast_W", {})[f"{cn}|{mode}"] = [round(float(v), 2) for v in np.interp(ts_, qa[:, 0], qa[:, 1])]
                    row["Q_coast_t_s"] = [round(float(v), 2) for v in ts_]
        out["elements"].append(row)
        print(f"{el['name'][:60]:60s}", row["E_coast_J"])
    tot = {}
    coast = t_rel - t_meco
    for cn in cases:
        for mode in ("LO", "HI"):
            vals = [r["E_coast_J"][f"{cn}|{mode}"] for r in out["elements"]]
            if any(v is None for v in vals):
                tot[f"{cn}|{mode}"] = "incomplete (HI far-field elements need the FE G 10 W/K run)"
                continue
            e_route = sum(float(r["E_coast_J"][f"{cn}|{mode}"]) for r in out["elements"] if r["group"] == "route")
            e_head_el = sum(float(r["E_coast_J"][f"{cn}|{mode}"]) for r in out["elements"] if r["group"] == "head")
            fe = out["fe_head_bore"].get(mode, out["fe_head_bore"].get("LO"))
            e_fe = fe["E_coast_J"] if fe else float("nan")
            e_nd = NEEDLE["E_J"][0 if mode == "LO" else 1]
            e_head = e_head_el + e_fe + e_nd
            E = e_route + e_head
            tot[f"{cn}|{mode}"] = {"route_J": round(e_route, 0), "route_W": round(e_route / coast, 1),
                                   "head_end_J": round(e_head, 0), "head_end_W": round(e_head / coast, 1),
                                   "head_end_split_J": {"FD-01 + E1-M head/bonnet drillings": round(e_head_el, 0), "FE manifold bore": e_fe,
                                                        "needle (ESTIMATE)": e_nd},
                                   "fe_source": fe["label"] if fe else None,
                                   "E_total_J": round(E, 0), "P_mean_W": round(E / coast, 1), "vapour_cm3": round(E / hfg / rv * 1e6, 1)}
    out["totals"] = tot
    # head-end heat input W(t) over the coast (lead relay 3 item 4): FE manifold bore (2-D run series) + FD-01 block + E1-M head/bonnet
    # drillings (slabs); needle tip NOT time-resolved (ESTIMATE total only, listed separately)
    hist = {}
    head_rows = [r for r in out["elements"] if r["group"] == "head" and "Q_coast_W" in r]
    if head_rows:
        tq = np.array(head_rows[0]["Q_coast_t_s"])
        for cn in cases:
            for mode in ("LO", "HI"):
                fe = out["fe_head_bore"].get(mode)
                if not fe or any(f"{cn}|{mode}" not in r["Q_coast_W"] for r in head_rows):
                    continue
                ser = seg[fe["label"]]["series"]
                q_fe = np.interp(tq, np.array(ser["t_s"]), np.array(ser["Q_W"]))
                parts_ = {r["name"].split(" ")[0]: np.array(r["Q_coast_W"][f"{cn}|{mode}"]) for r in head_rows}
                tot_ = q_fe + sum(parts_.values())
                hist[f"{cn}|{mode}"] = {"t_s": [round(float(v), 2) for v in tq], "Q_head_end_W": [round(float(v), 2) for v in tot_],
                                        "split_W": {"FE manifold bore (" + fe["label"] + ")": [round(float(v), 2) for v in q_fe],
                                                    **{k: [round(float(v), 2) for v in vv] for k, vv in parts_.items()}},
                                        "E_J": round(float(np.trapezoid(tot_, tq)), 1),
                                        "needle_not_time_resolved_J": NEEDLE["E_J"][0 if mode == "LO" else 1]}
    out["head_end_W_vs_t"] = {"v": hist, "note": "t from MECO to RELIGHT of the duty cycle (s from ignition); Q into the trapped liquid (W); "
                                                 "FE bore series sampled at the frd steps (~1 s) and interpolated; the needle tip estimate "
                                                 "(50 LO / 150 HI J) is not in the series"}
    out["note_fe_hi"] = ("HI uses the FE G 10 W/K run when given (--fe_hi), otherwise the G 1 W/K value (then HI understates the "
                         "head-end bore)")
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k not in ("elements",)}, indent=1)[:4000])


if __name__ == "__main__":
    main()
