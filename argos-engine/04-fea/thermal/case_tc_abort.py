"""Forward-case over-temperature abort: TC station, predicted maxima, allowable temperature, threshold (04-fea/thermal, v1, 2026-10-13, Mechanical).

Question (lead relay 2026-10-13, Electronics firmware v2.7): the firmware aborts at a case TC of 423.15 K held 0.2 s (ASSUMED limit).
Give the TC station(s), the predicted maximum there for A1 p99 / B1 p99 / B1 max (thermal v1.1 on the dispersed duty cycles), the
allowable temperature at the station (strength at temperature under MEOP stress, with margin), and a recommended threshold and hold.

Method
  Station: the hottest case-OD band of the axisymmetric thermal FE (run_thermal.py v1.1, extract_histories.py bands of 5 mm, node
  maximum of the band) = case OD r 31.75 mm at z 95-100 mm in the thermal-model frame = 12.6-17.6 mm below the injector face (z 112.6),
  i.e. the plain 6061-T6 tube around the TC-06 pre-chamber insulator.  The OD is within 3-4 K of the ID (wall 3.175 mm).
  Predicted maxima: during burns (pressurised), in flight, and after the last shutdown (soak, unpressurised), per run.
  Allowable: primary membrane stress of the plain tube (Lame, closed end) at chamber MEOP 4.5 MPa (LC2: SF_y 1.5, SF_u 2.0 at part
  temperature) and the blocked-nozzle bound 6.308 MPa (BN: SF_y 1.0), Tresca; strength vs temperature from engmat AL6061-T6 (ASTM B221 /
  B241 minimum x ASM 10 000 h typical ratios: CONSERVATIVE for the seconds-to-minutes exposures here; MMPDS 0.5 h curves would be higher
  but are not taken: open item).  Secondary (thermal) stress from the axial gradient of the hot band is NOT in this screen: it belongs to
  the LC5 structural FEA at the critical instant.
  Threshold window: lower bound = predicted in-burn maximum (upper heat-flux bound) + nuisance margin; upper bound = allowable - (TC lag
  + hold + pressure-decay time) x the in-burn heating rate - circumferential/model margin.  Every margin is ASSUMED and tagged.
"""
from __future__ import annotations
import sys, json, math, hashlib, argparse
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
import engmat

RUNS = Path("/home/claude/work/mechanical/runs/thermal")
STATION = "case_OD_z95_100_max"
GEOM = {"ri_mm": 57.15 / 2, "ro_mm": 31.75, "tag": "CAD v3.3/v3.4 TC-01 6061-T6 tube 63.5 x 3.175 (plain section at the pre-chamber)"}
LOADS = {"MEOP_Pa": (4.5e6, 1.5, 2.0, "LC2 chamber MEOP 45 bar (lead 2026-10-12), SF_y 1.5 / SF_u 2.0 at part temperature"),
         "BN_Pa": (6.308e6, 1.0, None, "BN blocked-nozzle bound 63.08 bar (lead 2026-10-12), SF_y 1.0 at temperature")}
MARGINS = {"nuisance_K": (15.0, "ASSUMED: threshold above the upper-bound in-burn prediction (sensor accuracy Class 1 +/-1.5 K, TC placement, "
                                "burn-to-burn scatter beyond the p99 cycle)"),
           "tau_TC_s": (1.0, "ASSUMED bonded bare-bead / 0.5 mm sheathed TC on the case OD (cemented + Al tape): first-order lag 0.3-1 s"),
           "hold_s": (0.2, "firmware v2.7 hold time"),
           "decay_s": (0.35, "ASSUMED: NC valve close <= 0.15 s (combustion.json isolation_valve) + chamber blow-down ~0.2 s"),
           "circ_model_K": (20.0, "ASSUMED: circumferential hot streaks (axisymmetric model), TC-06 thickness tolerance, OD-ID difference 3-4 K")}


def lame(P, ri, ro):
    k = (ro * ro + ri * ri) / (ro * ro - ri * ri)
    s_t, s_r, s_z = P * k, -P, P * ri * ri / (ro * ro - ri * ri)
    tresca = max(s_t, s_r, s_z) - min(s_t, s_r, s_z)
    vm = math.sqrt(0.5 * ((s_t - s_r) ** 2 + (s_r - s_z) ** 2 + (s_z - s_t) ** 2))
    return {"hoop_ID_MPa": s_t / 1e6, "radial_MPa": s_r / 1e6, "axial_MPa": s_z / 1e6, "tresca_MPa": tresca / 1e6, "vm_MPa": vm / 1e6}


def T_where(key, need_Pa):
    """highest temperature (C) at which engmat AL6061-T6 'key' >= need (linear interpolation of the table)"""
    m = engmat.MATERIALS["AL6061-T6"][key]
    T, v = np.array(m["T_C"], float), np.array(m["v"], float)
    if v[0] < need_Pa:
        return None
    for i in range(len(T) - 1):
        if v[i + 1] < need_Pa <= v[i]:
            return float(T[i] + (v[i] - need_Pa) / (v[i] - v[i + 1]) * (T[i + 1] - T[i]))
    return float(T[-1])


def allowable():
    ri, ro = GEOM["ri_mm"], GEOM["ro_mm"]
    out = {}
    for nm, (P, sfy, sfu, tag) in LOADS.items():
        s = lame(P, ri, ro)
        st = s["tresca_MPa"] * 1e6
        Ty = T_where("Fty", sfy * st)
        Tu = T_where("Ftu", sfu * st) if sfu else None
        out[nm] = {"P_bar": P / 1e5, "stress": {k: round(v, 2) for k, v in s.items()}, "SF_y": sfy, "SF_u": sfu,
                   "T_allow_yield_C": None if Ty is None else round(Ty, 1), "T_allow_ult_C": None if Tu is None else round(Tu, 1),
                   "T_allow_C": round(min(x for x in (Ty, Tu) if x is not None), 1), "tag": tag}
    gov = min(out.values(), key=lambda d: d["T_allow_C"])
    return out, gov["T_allow_C"]


def check_T(T_C):
    """margins at a given case temperature (e.g. the 548 K figure)"""
    ri, ro = GEOM["ri_mm"], GEOM["ro_mm"]
    fty, ftu = engmat.prop("AL6061-T6", "Fty", T_C), engmat.prop("AL6061-T6", "Ftu", T_C)
    rows = {}
    for nm, (P, sfy, sfu, tag) in LOADS.items():
        st = lame(P, ri, ro)["tresca_MPa"] * 1e6
        rows[nm] = {"Fty_MPa": round(fty / 1e6, 1), "Ftu_MPa": round(ftu / 1e6, 1), "tresca_MPa": round(st / 1e6, 1),
                    "SF_y_actual": round(fty / st, 2), "SF_y_req": sfy, "SF_u_actual": round(ftu / st, 2), "SF_u_req": sfu,
                    "pass": bool(fty / st >= sfy and (sfu is None or ftu / st >= sfu))}
    for pc in (25.0, 15.0):
        st = lame(pc * 1e5, ri, ro)["tresca_MPa"] * 1e6
        rows[f"Pc_{pc:.0f}bar"] = {"tresca_MPa": round(st / 1e6, 1), "SF_y_actual": round(fty / st, 2), "SF_u_actual": round(ftu / st, 2)}
    return rows


def run_stats(label):
    rd = RUNS / label
    h = np.load(rd / "histories.npz")
    meta = json.loads((rd / f"{label}_meta.json").read_text())
    t = h["t_s"]
    segs = [tuple(s) for s in meta["segments_s"]]
    tl = meta["t_last_shutdown_s"]
    y = h[STATION] - 273.15
    burn = np.zeros(len(t), bool)
    for a, b in segs:
        burn |= (t >= a - 1e-9) & (t <= b + 1e-6)
    fl = t <= tl + 1e-6
    dydt = np.gradient(y, t)
    r = {"label": label, "segments_s": segs, "D_pre_override": meta.get("config_overrides"),
         "histories_sha256_16": hashlib.sha256((rd / "histories.npz").read_bytes()).hexdigest()[:16],
         "bound": meta.get("bound", {}).get("tag", ""),
         "T_max_burn_C": round(float(y[burn].max()), 1), "T_max_burn_K": round(float(y[burn].max()) + 273.15, 1),
         "T_max_flight_C": round(float(y[fl].max()), 1), "T_max_overall_C": round(float(y.max()), 1),
         "t_max_overall_s": round(float(t[int(np.argmax(y))]), 1),
         "rate_max_burn_K_s": round(float(dydt[burn].max()), 1),
         "seg_end": [{"t_s": b, "T_C": round(float(np.interp(b, t, y)), 1), "rate_last_1s_K_s": round(float(np.interp(b, t, y) - np.interp(b - 1.0, t, y)), 1)}
                     for a, b in segs],
         "first_burn_crossing_s": {}}
    for thr in (150.0, 175.0, 200.0, 217.0):
        c = np.where((y >= thr) & burn)[0]
        r["first_burn_crossing_s"][f"{thr:.0f}C"] = round(float(t[c[0]]), 2) if len(c) else None
    # profile of the in-burn maximum along the case OD (to show the station is the peak)
    bands = sorted([k for k in h.files if k.startswith("case_OD_z") and k.endswith("_max")], key=lambda k: int(k.split("_z")[1].split("_")[0]))
    r["burn_max_by_band_C"] = {k.replace("case_OD_", "").replace("_max", ""): round(float(h[k][burn].max()) - 273.15, 0) for k in bands}
    return r


def window(stats, T_allow):
    """threshold window from the runs given (upper heat-flux bound predictions)"""
    M = {k: v[0] for k, v in MARGINS.items()}
    T_pred = max(s["T_max_burn_C"] for s in stats)
    rate = max(max(e["rate_last_1s_K_s"] for e in s["seg_end"]) for s in stats)
    lag = rate * (M["tau_TC_s"] + M["hold_s"] + M["decay_s"])
    lo = T_pred + M["nuisance_K"]
    hi = T_allow - M["circ_model_K"] - lag
    rec = None
    if lo <= hi:
        rec = 5.0 * math.floor(min(max(lo, 0.5 * (lo + hi)), hi) / 5.0)
    return {"T_pred_max_burn_C": T_pred, "rate_end_burn_K_s": rate, "lag_K": round(lag, 1), "lower_C": round(lo, 1), "upper_C": round(hi, 1),
            "feasible": lo <= hi, "recommended_C": rec, "recommended_K": None if rec is None else round(rec + 273.15, 2), "hold_s": M["hold_s"]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="comma list of run labels, TC-06 1.6 mm (baseline)")
    ap.add_argument("--pre36", default="", help="comma list of run labels, TC-06 3.6 mm (D_pre 49.9)")
    ap.add_argument("--ref", default="", help="comma list of reference runs (nominal bound, DC-B1 v2)")
    ap.add_argument("--out", default="case_tc_abort_v1.json")
    a = ap.parse_args()
    allow, T_allow = allowable()
    out = {"id": "case_tc_abort", "version": "v1", "date": "2026-10-13", "script": "04-fea/thermal/case_tc_abort.py",
           "station": {"history_key": STATION, "where": "TC-01 case OD r 31.75 mm, z 95-100 mm thermal-model frame = 12.6-17.6 mm below the injector "
                       "face (TC-06 pre-chamber section, plain tube); the in-burn maximum of every run peaks in this band (see burn_max_by_band_C)",
                       "geometry": GEOM},
           "allowable": allow, "T_allow_C": T_allow, "T_allow_K": round(T_allow + 273.15, 2),
           "material_basis": engmat.MATERIALS["AL6061-T6"]["Fty"]["src"],
           "check_548K": check_T(548.0 - 273.15), "margins": {k: {"v": v[0], "tag": v[1]} for k, v in MARGINS.items()},
           "runs": {}}
    groups = {"base_TC06_1p6": [x for x in a.base.split(",") if x], "pre36_TC06_3p6": [x for x in a.pre36.split(",") if x],
              "reference": [x for x in a.ref.split(",") if x]}
    for g, labs in groups.items():
        st = [run_stats(l) for l in labs if (RUNS / l / "histories.npz").exists()]
        out["runs"][g] = st
        if st and g != "reference":
            out[f"window_{g}"] = window(st, T_allow)
    p = HERE / a.out
    p.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in out if k.startswith("window") or k in ("T_allow_C", "T_allow_K")}, indent=1))
    print("548 K check", json.dumps(out["check_548K"]))
    for g, st in out["runs"].items():
        for s in st:
            print(g, s["label"], "burn max", s["T_max_burn_C"], "C /", s["T_max_burn_K"], "K; flight", s["T_max_flight_C"], "; overall", s["T_max_overall_C"],
                  "at", s["t_max_overall_s"], "s; seg ends", s["seg_end"], "; crossings", s["first_burn_crossing_s"])
    print(p, hashlib.sha256(p.read_bytes()).hexdigest()[:16])
