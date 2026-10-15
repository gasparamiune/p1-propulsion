"""Pc transducer temperature from MECO to RELIGHT on the A1 coast (04-fea/thermal, v1, 2026-10-13, Mechanical).

Request: lead decision on REV-ELEC-1 RE-07 (CHANGELOG line 166, item 5): "B-PC-1 measures zero TC and 20 s drift (Mechanical supplies the
transducer temperature MECO->RELIGHT)"; coordinator 2026-10-13: a bounded estimate is acceptable if tagged.

What exists (CAD v3.4.1 rev B): the Pc tap is a 1/8-27 NPT port in the head top (ENG-TC-02) at r 25 mm / 142 deg with a 2 mm passage
to the injector face at r 20.5 (parts_engine.py, HV69 layout); the lead requires a 1/8 in sense line < 0.3 m (config pc_sense_line_max_len);
the transducer (Electronics: TE M3234-000005-070BG, 1/4-18 NPT male) has a reservation only (config pc_sensor_env_mm 30 x 30 x 80,
ASSUMED 50 g) and is NOT placed in the CAD; Electronics' harness crosses the gimbal with the Pc wires (transducer on the engine side).
So the transducer temperature depends on a mount that is not yet defined (OPEN, CAD run 6 places it).  This script gives bounds:

  D  DIRECT (upper bound): transducer body at the head-top surface temperature at the tap radius (axisymmetric thermal FE, band r 20-26 mm,
     max over the band).  Covers a transducer screwed into the tap with an adapter or a very short line.
  L  LAGGED: a lumped transducer body (C = m cp, ASSUMED 50 g x 500 J/kg K = 25 J/K) coupled to the head top by a conductance G
     (ASSUMED 0.2 / 0.5 / 2 W/K: thread + adapter), dT/dt = (G/C) (T_mount - T): the body lags the mount.
  R  REMOTE (sense line, transducer on its own bracket): the 1/8 x 0.035 in 316 tube conducts k A / L = 16 x 5.51e-6 / 0.30 = 2.9e-4 W/K
     (gas stagnant in the coast), i.e. < 6 mW for a 20 K difference: the engine adds < 0.05 K to a 25 J/K body over 20 s.  The
     transducer then follows its bracket / bay air (not modelled here: Electronics' bay TC is the measurement).

Thermal source: the rev B design A1 run (2-D axisymmetric thermal FE, run_thermal v1.3, 'hi' bound = upper-bound heat transfer, DC
DC-A1dispp99_tg711: burn 1 0.001-3.541 s, coast 18.67 s, relight 22.211 s).  The gnc v3 nominal coast is 20.599 s (REV-ELEC-1 R13): the
history is extended beyond the run's coast with the slope of its last 1.7 s (the soak-back curve is concave, so the extension is an upper
bound).  Sensitivity: the v11-geometry run DC-A1_gncv2 (coast 20.97 s, older head / seat insert) heats faster and is reported alongside
(not the design geometry).

Usage: python pc_transducer_temp.py  -> pc_transducer_temp_v1.json + pc_transducer_temp_v1.csv (this folder)
"""
from __future__ import annotations
import csv, hashlib, json, math
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
RUNS = Path("/home/claude/work/mechanical/runs/thermal")
DESIGN = "DC-A1dispp99_tg711_hi_SS316L_L2.5_v13pre36IN_J1revB"
SENS = "DC-A1_gncv2_hi_SS316L_L2.5_v11"
COAST_NOM_S = 20.599                     # gnc.json v3 DC-A1 burn-off to burn-on (REV-ELEC-1 R13)
C_BODY = 0.050 * 500.0                   # J/K, ASSUMED (50 g reservation mass x stainless cp)
G_MOUNT = (0.2, 0.5, 2.0)                # W/K, ASSUMED thread / adapter conductance band
WINDOWS = (3.0, 4.0, 5.0)                # s before RELIGHT: second re-zero ends before PURGE (E0 - 2.90 s); E0 -> light <= 0.63 s


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def history(label):
    run = RUNS / label
    h = np.load(run / "histories.npz")
    meta = json.loads((run / f"{label}_meta.json").read_text())
    seg = meta["segments_s"]
    t_meco, t_rl = seg[0][1], seg[1][0]
    t = h["t_s"]
    T = h["head_top_r20_26_max"] - 273.15
    keep = np.concatenate([[True], np.diff(t) > 1e-9])           # drop repeated step-boundary samples
    return t[keep], T[keep], t_meco, t_rl, {"histories_npz_sha256_16": sha16(run / "histories.npz"), "meta_sha256_16": sha16(run / f"{label}_meta.json"),
                                            "frd": f"{label}.frd", "segments_s": seg, "dc_history": meta.get("dc_history"),
                                            "config_overrides": meta.get("config_overrides")}


def coast_curve(t, T, t_meco, t_rl, coast_target):
    """T(tau) for tau = t - t_meco in [0, coast_target]; beyond the run's coast: linear at the slope of its last 1.7 s (upper bound)."""
    m = (t >= t_meco - 1e-9) & (t <= t_rl + 1e-9)
    tau, Tc = t[m] - t_meco, T[m]
    coast_run = t_rl - t_meco
    k = tau >= coast_run - 1.7
    slope = float(np.polyfit(tau[k], Tc[k], 1)[0])
    tg = np.arange(0.0, coast_target + 1e-9, 0.1)
    Tg = np.where(tg <= coast_run, np.interp(tg, tau, Tc), Tc[-1] + slope * (tg - coast_run))
    return tg, Tg, slope, coast_run


def lag(tg, Tm, G, C=C_BODY):
    """First-order body response to the mount temperature (exact for piecewise-linear input, dt 0.1 s)."""
    tau = C / G
    x = np.empty_like(Tm)
    x[0] = Tm[0]
    for i in range(1, len(tg)):
        dt = tg[i] - tg[i - 1]
        a = math.exp(-dt / tau)
        s = (Tm[i] - Tm[i - 1]) / dt
        x[i] = Tm[i] - s * tau + (x[i - 1] - Tm[i - 1] + s * tau) * a
    return x


def summary(tg, Tx, coast):
    i_end = int(np.argmin(abs(tg - coast)))
    out = {"T_MECO_C": round(float(Tx[0]), 2), "T_RELIGHT_C": round(float(Tx[i_end]), 2),
           "dT_coast_K": round(float(Tx[i_end] - Tx[0]), 2),
           "dT_from_first_rezero_end_K": round(float(Tx[i_end] - np.interp(1.2, tg, Tx)), 2),   # re-zero at COAST + 1.0 s over 200 samples
           "slope_at_RELIGHT_K_s": round(float((Tx[i_end] - np.interp(coast - 1.0, tg, Tx)) / 1.0), 3)}
    for w in WINDOWS:
        out[f"dT_last_{w:g}s_K"] = round(float(Tx[i_end] - np.interp(coast - w, tg, Tx)), 2)
    return out


def main():
    res = {"id": "pc_transducer_temp", "version": "v1", "date": "2026-10-13", "owner": "mechanical",
           "script": "04-fea/thermal/pc_transducer_temp.py", "request": "REV-ELEC-1 RE-07; lead decision CHANGELOG line 166 (5)",
           "status": "BOUNDED ESTIMATE: SIM (2-D thermal FE, upper-bound heat transfer) + DERIVED extension + ASSUMED transducer body; "
                     "mount location OPEN (not in CAD); not a measurement",
           "geometry": {"tap": "1/8-27 NPT, head top (ENG-TC-02) r 25 mm / az 142 deg, 2 mm passage to the face at r 20.5 (CAD v3.4.1 rev B)",
                        "sense_line": "1/8 in OD x 0.035 in wall 316, < 0.30 m (lead, config pc_sense_line_max_len)",
                        "transducer": "TE M3234-000005-070BG (Electronics), 1/4-18 NPT male; reservation 30 x 30 x 80 mm, 50 g ASSUMED; NOT placed in CAD",
                        "sense_line_conductance_W_K": round(16.0 * math.pi / 4 * (3.175e-3 ** 2 - 1.753e-3 ** 2) / 0.30, 6)},
           "assumptions": {"C_body_J_K": C_BODY, "G_mount_W_K": G_MOUNT, "coast_nominal_s": COAST_NOM_S,
                           "head_top_band": "max over the head-top face nodes r 20-26 mm (tap at r 25)",
                           "extension": "linear at the last-1.7 s slope of the run's coast (concave curve: upper bound)"},
           "cases": {}}
    rows = []
    for tag, label in (("design_revB", DESIGN), ("sensitivity_v11_geometry", SENS)):
        t, T, t_meco, t_rl, src = history(label)
        coast = COAST_NOM_S
        tg, Tg, slope, coast_run = coast_curve(t, T, t_meco, t_rl, max(coast, t_rl - t_meco))
        c = {"source": src, "t_MECO_s": t_meco, "t_RELIGHT_run_s": t_rl, "coast_run_s": round(coast_run, 3),
             "coast_used_s": round(coast, 3), "extension_slope_K_s": round(slope, 3) if coast > coast_run else None,
             "D_direct_upper_bound": summary(tg, Tg, coast),
             "D_direct_at_run_coast": summary(tg, Tg, coast_run)}
        for G in G_MOUNT:
            c[f"L_lagged_G{G:g}_W_K"] = summary(tg, lag(tg, Tg, G), coast)
        c["R_remote"] = {"dT_from_engine_K": "< 0.05 (sense line 2.9e-4 W/K; stagnant gas)", "governed_by": "bracket / bay air (Electronics bay TC)"}
        res["cases"][tag] = c
        if tag == "design_revB":
            lags = {G: lag(tg, Tg, G) for G in G_MOUNT}
            for i in range(0, len(tg), 5):
                rows.append([round(tg[i], 2), round(float(Tg[i]), 3)] + [round(float(lags[G][i]), 3) for G in G_MOUNT]
                            + [int(tg[i] > coast_run)])
    res["drift_note"] = ("Drift = zero TC x dT. At the 0.01 bar/K placeholder (Electronics config.h l.558, TO-VERIFY at B-PC-1) the DIRECT "
                         "bound gives ~0.15-0.16 bar over the whole coast (> the 0.10 bar allowance after the first re-zero) and "
                         "<= ~0.03 bar over the last 3-5 s (second re-zero, lead RE-07 (5)). A remote mount removes the engine "
                         "contribution. Recommendation: mount the transducer remote from the head (bracket on the gimbal-side "
                         "structure with the 1/8 in line as the thermal break) and place it in CAD run 6.")
    out = HERE / "pc_transducer_temp_v1.json"
    out.write_text(json.dumps(res, indent=1))
    with open(HERE / "pc_transducer_temp_v1.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["# Pc transducer temperature bound on the A1 coast, design rev B thermal run " + DESIGN + "; tau = t - MECO; "
                    "BOUNDED ESTIMATE (SIM + DERIVED + ASSUMED); extended = beyond the run's 18.67 s coast"])
        w.writerow(["tau_s", "T_direct_upper_C"] + [f"T_lagged_G{G:g}_C" for G in G_MOUNT] + ["extended"])
        w.writerows(rows)
    print(json.dumps({k: v for k, v in res["cases"]["design_revB"].items() if k != "source"}, indent=1))
    print(json.dumps(res["cases"]["sensitivity_v11_geometry"]["D_direct_upper_bound"], indent=1))


if __name__ == "__main__":
    main()
