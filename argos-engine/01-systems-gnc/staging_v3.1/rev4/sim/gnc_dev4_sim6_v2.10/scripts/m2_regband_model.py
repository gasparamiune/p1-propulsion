"""m2_regband_model v1 (GNC, 2026-10-13): reduced model of the fuel-regression-law band (RC-07: a x0.6-1.5, n 0.35-0.68)
for the 6-DOF Monte Carlo, calibrated on Combustion's band runs of GNC's duty cycles (lead request 2026-10-13: add the band to
the B1 MC dispersion together with throat growth).

What the band does to the engine GNC flies (read from Combustion's runs, data/v2/dc_gncv3_band, grain_q1d v2.4):
  the run follows GNC's thrust command with the ECU holding Pc on the nominal map; a different regression law changes the fuel
  flow, the O/F and c*, so the oxidiser flow needed per unit thrust changes (and the fuel flow with it). Pc per thrust changes by
  < 0.3 % (median of Pc_corner / Pc_nominal-corner on the same command; checked here), so thrust per command is not modelled.
Model (hypotheses H1-H4, stated in the output):
  mdot_ox = mdot_ox,map x phi_ox(a, n, X),  mdot_f = mdot_f,map x phi_f(a, n, X)
  X = cumulative oxidiser burned at the map flows (kg; "nominal-equivalent" progress of the port opening)
  phi tables: ratios of Combustion's corner run to its nominal-corner run (a x1.0, n 0.5) of the SAME duty cycle and command,
  per bin of X, using only samples with liquid in the tank (m_liq > 0.02 kg) and thrust > 5 N; calibration cycle DC-B1 85 m disp
  p99 (k_est_asc 2, no throat growth); (a, n) between the 3 x 3 corners: bilinear; X outside the knots: end values held.
  H1 the corner effect is a function of the oxidiser burned, not of the throttle history (B1 hops all fly the 20 % floor +
     top-up profile; checked by predicting the other B1 cycles below)
  H2 throat growth and the corner effect compose multiplicatively (checked on the tg711 cycles)
  H3 after liquid depletion the 6-DOF cuts the thrust (no vapour phase): conservative against Combustion's vapour tail
     (thrust shortfall <= 112 N, impulse deficit <= ~6 %)
  H4 the regression band is independent of the existing isp_scale N(1, 0.05) draw (ASSUMED; may double count part of the Isp
     uncertainty: conservative)
Validation: the tables applied to Combustion's nominal-corner history of each other cycle predict the corner's oxidiser and fuel
burned up to the earlier of the two depletion times; errors reported per cycle and corner.
Output: <out>/regband_model_v1.json. Env: GNC_RB_SRC (band folder), GNC_RB_OUT (default out/regband)."""
import hashlib
import json
import os

import numpy as np
import pandas as pd

VERSION = "m2_regband_model v1"
HUB_BAND = "/home/claude/work/shared-fallback/engine/02-combustion/data/v2/dc_gncv3_band"
WORK_BAND = "/home/claude/work/combustion/data/v2/dc_gncv3_band"
SRC = os.environ.get("GNC_RB_SRC") or (HUB_BAND if os.path.isfile(os.path.join(HUB_BAND, "summary_v2p4.json")) else WORK_BAND)
OUT = os.environ.get("GNC_RB_OUT", "/home/claude/work/space/out/regband")
A_GRID = (0.6, 1.0, 1.5)        # REQ / combustion.json regression_law band a x0.6-1.5 (ASSUMED there)
N_GRID = (0.35, 0.5, 0.68)      # REQ / combustion.json regression_law band n 0.35-0.68 (ASSUMED there)
CAL = "DC-B1v3p99"              # calibration cycle (Combustion tag of GNC's DC-B1_hop_85m_disp_p99_kest2_v3)
VAL = ("DC-B1v3p99_tg711", "DC-B1v3max", "DC-B1v3max_tg711", "DC-A1dispp99", "DC-A1dispp99_tg711")
X_EDGES = np.round(np.arange(0.0, 1.7001, 0.05), 3)   # kg oxidiser, 0.05 kg bins (DESIGN of the model; 0.15 kg bins gave up to 1.5 % self-check error)
M_LIQ_MIN = 0.02
F_MIN = 5.0


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def fname(tag, a, n):
    return f"{tag}-S230_neqE1e+03_reg{dict(zip(A_GRID, ('0.6', '1', '1.5')))[a]}_n{dict(zip(N_GRID, ('0.35', '0.5', '0.68')))[n]}.csv"


def load(tag, a, n):
    p = os.path.join(SRC, fname(tag, a, n))
    if not os.path.isfile(p):
        return None, None
    d = pd.read_csv(p)
    return d, p


def tables(tag):
    """phi_ox, phi_f per corner vs X (bin centres) on one cycle; also the Pc ratio check."""
    d0, p0 = load(tag, 1.0, 0.5)
    t = d0.t.values
    dt = np.diff(t, prepend=0.0)
    X0 = np.cumsum(d0.mox.values * dt)
    xc = 0.5 * (X_EDGES[1:] + X_EDGES[:-1])
    out = {}
    files = {fname(tag, 1.0, 0.5): sha16(p0)}
    for a in A_GRID:
        for n in N_GRID:
            dc, pc = load(tag, a, n)
            if dc is None or len(dc) != len(d0) or np.max(np.abs(dc.t.values - t)) > 1e-9:
                out[f"{a}|{n}"] = None
                continue
            files[os.path.basename(pc)] = sha16(pc)
            on = (dc.F.values > F_MIN) & (d0.F.values > F_MIN) & (dc.m_liq.values > M_LIQ_MIN) & (d0.m_liq.values > M_LIQ_MIN)
            pox, pf, nn = [], [], []
            for i in range(len(xc)):
                m = on & (X0 >= X_EDGES[i]) & (X0 < X_EDGES[i + 1])
                nn.append(int(m.sum()))
                if m.sum() < 20:
                    pox.append(None); pf.append(None)
                    continue
                r0 = np.sum(d0.F.values[m] * dt[m])
                rc = np.sum(dc.F.values[m] * dt[m])
                pox.append(float((np.sum(dc.mox.values[m] * dt[m]) / rc) / (np.sum(d0.mox.values[m] * dt[m]) / r0)))
                pf.append(float((np.sum(dc.mf.values[m] * dt[m]) / rc) / (np.sum(d0.mf.values[m] * dt[m]) / r0)))
            pcr = dc.Pc.values[on] / d0.Pc.values[on]
            out[f"{a}|{n}"] = dict(phi_ox=pox, phi_f=pf, n_samples=nn, pc_ratio_median=float(np.median(pcr)),
                                   pc_ratio_p05_p95=[float(np.percentile(pcr, 5)), float(np.percentile(pcr, 95))])
    return dict(x_centres_kg=xc.tolist(), corners=out, files=files, x_end_nominal_kg=float(X0[-1]))


def fill(v):
    """Hold the end values over empty bins (beyond the oxidiser burned on the calibration cycle)."""
    v = list(v)
    idx = [i for i, x in enumerate(v) if x is not None]
    if not idx:
        return None
    for i in range(len(v)):
        if v[i] is None:
            j = min(idx, key=lambda k: abs(k - i))
            v[i] = v[j]
    return v


def phi_at(T, a, n, X, key):
    """Bilinear in (a, n) over the 3 x 3 corners, linear in X between bin centres, ends held."""
    ag, ng = np.array(A_GRID), np.array(N_GRID)
    a = float(np.clip(a, ag[0], ag[-1])); n = float(np.clip(n, ng[0], ng[-1]))
    i = min(int(np.searchsorted(ag, a, side="right")) - 1, len(ag) - 2)
    j = min(int(np.searchsorted(ng, n, side="right")) - 1, len(ng) - 2)
    u = (a - ag[i]) / (ag[i + 1] - ag[i]); w = (n - ng[j]) / (ng[j + 1] - ng[j])
    xc = np.array(T["x_centres_kg"])
    val = 0.0
    for di, wa in ((0, 1 - u), (1, u)):
        for dj, wn in ((0, 1 - w), (1, w)):
            v = T["filled"][f"{ag[i + di]}|{ng[j + dj]}"][key]
            val = val + wa * wn * np.interp(X, xc, v)
    return val


def knots_for(T, a, n):
    """Per-run knot values (what the 6-DOF receives)."""
    xc = np.array(T["x_centres_kg"])
    return xc, np.array([phi_at(T, a, n, x, "phi_ox") for x in xc]), np.array([phi_at(T, a, n, x, "phi_f") for x in xc])


def validate(T, tag):
    """Predict each corner's oxidiser / fuel burned on another cycle from its nominal-corner history."""
    d0, _ = load(tag, 1.0, 0.5)
    if d0 is None:
        return None
    t = d0.t.values
    dt = np.diff(t, prepend=0.0)
    X0 = np.cumsum(d0.mox.values * dt)
    rows = {}
    for a in A_GRID:
        for n in N_GRID:
            dc, _ = load(tag, a, n)
            if dc is None or len(dc) != len(d0):
                continue
            liq = (dc.m_liq.values > M_LIQ_MIN) & (d0.m_liq.values > M_LIQ_MIN)
            k = int(np.argmin(liq)) if not liq.all() else len(t)
            px = np.array([phi_at(T, a, n, x, "phi_ox") for x in X0[:k]])
            pfu = np.array([phi_at(T, a, n, x, "phi_f") for x in X0[:k]])
            # the model claims flow PER DELIVERED THRUST (the 6-DOF guidance sets the thrust): predict at the corner run's thrust
            F0, Fc = d0.F.values[:k], dc.F.values[:k]
            fr = np.where(F0 > F_MIN, Fc / np.maximum(F0, F_MIN), 1.0)
            ox_pred = float(np.sum(d0.mox.values[:k] * px * fr * dt[:k])); ox_true = float(np.sum(dc.mox.values[:k] * dt[:k]))
            f_pred = float(np.sum(d0.mf.values[:k] * pfu * fr * dt[:k])); f_true = float(np.sum(dc.mf.values[:k] * dt[:k]))
            ox_flow = float(np.sum(d0.mox.values[:k] * px * dt[:k]))
            ox_nom = float(np.sum(d0.mox.values[:k] * dt[:k]))
            rows[f"{a}|{n}"] = dict(window_s=float(t[k - 1]), ox_nominal_kg=ox_nom, ox_corner_kg=ox_true, ox_pred_kg=ox_pred,
                                    ox_err_frac=(ox_pred - ox_true) / ox_true, corner_effect_frac=(ox_true - ox_nom) / ox_nom,
                                    impulse_ratio_corner_to_nominal=float(np.sum(Fc * dt[:k]) / np.sum(F0 * dt[:k])),
                                    ox_err_frac_at_nominal_thrust=(ox_flow - ox_true) / ox_true,
                                    fuel_corner_kg=f_true, fuel_pred_kg=f_pred, fuel_err_frac=(f_pred - f_true) / f_true)
    errs = [abs(r["ox_err_frac"]) for r in rows.values()]
    eff = [abs(r["corner_effect_frac"]) for r in rows.values()]
    sgn = [r["ox_err_frac"] for r in rows.values()]
    return dict(corners=rows, ox_err_abs_max=max(errs) if errs else None, ox_err_min=min(sgn) if sgn else None,
                ox_err_max=max(sgn) if sgn else None, corner_effect_abs_max=max(eff) if eff else None)


def main():
    os.makedirs(OUT, exist_ok=True)
    summ_p = os.path.join(SRC, "summary_v2p4.json")
    S = json.load(open(summ_p))
    T = tables(CAL)
    T["filled"] = {k: dict(phi_ox=fill(v["phi_ox"]), phi_f=fill(v["phi_f"])) for k, v in T["corners"].items() if v}
    val = {tag: validate(T, tag) for tag in VAL}
    cal_self = validate(T, CAL)
    # Combustion's corner summary for B1 (liquid at the end, depletion, web) for the record
    b1 = {}
    for k, v in S.items():
        if k.startswith("DC-B1v3p99") or k.startswith("DC-B1v3max"):
            b1[k] = {q: v.get(q) for q in ("regression_scale", "n", "burn_s", "impulse_Ns", "ox_used_kg", "fuel_used_kg", "OF_mean",
                                           "Isp_mean_s", "m_liq_end_kg", "P_tank_end_Pa", "w_min_end_mm", "burnthrough_s", "sep_time_s")}
    pcr = [v["pc_ratio_median"] for v in T["corners"].values() if v]
    out = dict(version=VERSION, date="2026-10-13",
               source=dict(folder=SRC, in_hub=SRC.startswith(HUB_BAND), summary=os.path.basename(summ_p), summary_sha256_16=sha16(summ_p),
                           note="Combustion RC-07 band runs of GNC's duty cycles (grain_q1d v2.4; SIM on ASSUMED regression law); "
                                "the lead cites the hub path 02-combustion/data/v2/dc_gncv3_band/summary_v2p4.json"),
               band=dict(a_scale=list(A_GRID), n=list(N_GRID), distribution="uniform on a-scale and on n, independent (lead "
                         "2026-10-13: Combustion's recommended distribution, or uniform if none; none found in the band files)",
                         re_anchor="Combustion re-anchors a at r(300 kg/m2/s) = 1 mm/s when n changes (run_dispersed_v2p4)"),
               calibration_cycle=CAL, x_edges_kg=X_EDGES.tolist(), tables=T,
               pc_ratio_median_range=[min(pcr), max(pcr)],
               hypotheses=["H1 corner effect = f(oxidiser burned) for B1-like hops", "H2 growth x corner multiplicative",
                           "H3 depletion cuts the thrust in the 6-DOF (no vapour phase): conservative",
                           "H4 band independent of isp_scale N(1, 0.05) (may double count: conservative)"],
               validation=dict(self_check_calibration_cycle=cal_self, other_cycles=val),
               combustion_summary_B1=b1)
    p = os.path.join(OUT, "regband_model_v1.json")
    with open(p, "w") as f:
        json.dump(out, f, indent=1)
    print("source", SRC, "| Pc ratio median range", [round(x, 4) for x in out["pc_ratio_median_range"]])
    for tag, v in [(CAL, cal_self)] + list(val.items()):
        if v:
            print(f"{tag:22s} ox error max {100 * v['ox_err_abs_max']:.2f} % (corner effect up to {100 * v['corner_effect_abs_max']:.1f} %)")
            for c, r in v["corners"].items():
                print(f"   {c:9s} window {r['window_s']:6.2f} s ox nominal {r['ox_nominal_kg']:.4f} corner {r['ox_corner_kg']:.4f} "
                      f"pred {r['ox_pred_kg']:.4f} err {100 * r['ox_err_frac']:+.2f} % | fuel err {100 * r['fuel_err_frac']:+.2f} %")
    print("wrote", p)


if __name__ == "__main__":
    main()
