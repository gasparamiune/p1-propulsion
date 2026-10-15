"""m2_relight_attitude v1 (GNC, 2026-10-13): coordinator request 2026-10-13, items 1-2 (the retained vapour of the re-routed FD-07
coil depends on attitude: the hose rises 2 mm over 180 mm, so a tilt of more than about 0.6 deg between the body axis and the
specific force forms vapour humps; Combustion uses these numbers for the purge sizing): over the 10 s before RELIGHT and at
RELIGHT, the angle between the body +z axis and the specific-force vector with its azimuth, and the gimbal pose. Item 3 (drain
pose) was withdrawn by the coordinator (Mechanical refuted it at 10 deg tilt). Extraction only: no FSW or model change is flown.

Definitions
  RELIGHT   sim6 t_relight = the relight command E0 (phase 4 entry, the lift; the forced purge of amendment P ends here; the
            light follows after the start delay). 'At RELIGHT' = the 1 ms record stamped t_relight (end of the last step before
            the relight decision). Windows: the W s before it, records stamped in (t_relight - W, t_relight]; 'purge' = from
            the purge start (prg_t0) to t_relight (P25 arms); 'E0-light' = from t_relight to the first record of phase 5.
  f         specific force (non-gravitational force / mass, what an ideal accelerometer reads) in body axes. At the CG:
            f = R(q)^T (dv/dt + g z_world) from the 1 ms record, q of the previous record (the attitude the step used); the
            reconstructed f_z is checked against the recorded sim6 fb[2] ('fax'). At a body station z_s on the axis:
            f_s = f_CG + alpha x r + w x (w x r), r = (0, 0, z_s - z_cg), alpha from the recorded body rates (the method of
            m2_coast_accel_a1 v1; CG lateral offset, 2 mm sd, neglected).
  theta     angle between body +z and f_s: atan2(|f_lat|, f_z), deg (0 = f along the body axis).
  az        azimuth of the lateral part of f_s in body axes, atan2(f_y, f_x) mod 360, deg, from +x toward +y. The gimbal is at
            neutral in these windows (below), so body axes = engine axes. Mechanical's coil_tilt_screen_v341 'up' vector
            u = (sin th cos az, sin th sin az, cos th) is f / |f| here if the CAD X, Y, Z axes are the sim body axes (the sim's
            servo-lever azimuths 135 / 225 deg are read from mechanical.json in that convention; frame identity TO-CONFIRM).
  stations  'hose': the coil at z_pivot + 0.073 m (ASSUMED: coil z 72-74 mm in coil_tilt_screen_v341_v1 with the CAD origin
            taken at the gimbal pivot, TO-CONFIRM); 'seat': z_pivot + 0.1106 m (mechanical.json v2 z_seat, as
            m2_coast_accel_a1); 'pivot'; 'mv': z 0.5 m (ASSUMED, as m2_coast_accel_a1); 'cg'. The lateral specific force
            depends on the station (a nose-drogue force change rotates the body about a centre of percussion about
            I_t / (m l_tip) = 0.22 m below the CG, near the engine: stations near it see the smallest theta), so the station
            values are reported side by side. 'imu_meas': the IMU station z_imu with the run's accelerometer bias and scale factor
            (white noise omitted: 1 mm/s/sqrt(s) is 0.0014 m/s2, 0.01 deg, on a 0.5 s average; sim6 has no IMU mounting
            misalignment: the installed misalignment adds to theta and is TO-DEFINE).
  gimbal    truth engine angles (dgx, dgy) and command (dcx, dcy), |delta| = hypot of the two axes, deg.
Configuration: the A1 base of m2_purge_bleed (A1_none, liquid plan 0.81 s, relight NOT CLOSED (RG-01), flown mass estimator
tot_cal_comp; seed 101, N runs; wind U(0, 8) m/s at the reference height, Dryden-like gusts x U(0.5, 1.5)), sim6 v2.8-dev MWFPR,
1 ms recorder. Arms: ref (no purge); P25 (forced purge 2.5 s + 0.5 s anticipation, 20.0 g/s, jet 2.1 N whose reaction acts
toward body azimuth bl_az = 0 deg at the pivot height: vent location and direction ASSUMED, TO-DEFINE); P25_nojet (balanced or
axial vent).
Model limits: nose drogue = quasi-steady massless canopy, tension along -v_rel at the nose tip (no canopy pendulum oscillation,
riser elasticity, swivel friction or inflation: a real canopy's oscillation can dominate theta; drop-test or literature data
for the chosen canopy are needed before this distribution is used as a design value); first-order gust model; rigid-body
specific force (no line fluid dynamics); the hump volumes of the coordinator relay (Mechanical screen, worst direction) are
applied only as a conditional screen.
Env: GNC_IFACE, GNC_ACT_RATE, GNC_RA_OUT (out/relight_attitude), GNC_RA_N (500), GNC_RA_PARTS (identity, mc, eval, hub),
GNC_RA_ARMS, GNC_RA_HUB (hub folder).
Outputs: ra_<arm>.npz (pooled histograms), ra_runs_<arm>.csv (per run), relight_attitude_v1.json."""
import csv
import json
import os
import sys
import time
import numpy as np

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_RA_OUT", f"{S}/relight_attitude")
os.environ.setdefault("GNC_PC_RATCHET", "1")
os.environ.setdefault("GNC_PB_OUT", OUT)          # m2_purge_bleed reads its output folder at import (nothing is written)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_purge_bleed as PB  # noqa: E402
import m2_mass_est_v2 as MV  # noqa: E402

VERSION = "m2_relight_attitude v1"
PARTS = os.environ.get("GNC_RA_PARTS", "mc,eval").split(",")
N = int(os.environ.get("GNC_RA_N", "500"))
ARMS = {"A1|ref": {}, "A1|P25": dict(PB.P25), "A1|P25_nojet": dict(PB.P25, prg_jet=0)}
ARM_SEL = [a for a in os.environ.get("GNC_RA_ARMS", ",".join(ARMS)).split(",") if a]
G0 = s6.G0
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
P = {n: i for i, n in enumerate(s6.PAR_NAMES)}
DT = 1.0e-3
NROWS = 40000                                   # 40 s of 1 ms records (relight command at 21-25 s)
WINS = (10.0, 5.0, 2.5)
Z_HOSE_ABOVE_PIVOT = 0.073                      # ASSUMED (see the docstring)
Z_SEAT_ABOVE_PIVOT = 0.1106                     # mechanical.json v2 envelope.stations_from_pivot_m.z_seat (DERIVED+ESTIMATE)
Z_MV = 0.5                                      # ASSUMED main-valve station (m2_coast_accel_a1: GNC ledger P09, tank bottom - 0.05 m)
STATIONS = ("hose", "seat", "pivot", "mv", "cg", "imu_meas")
TH_NB, TH_MAX = 18000, 180.0                    # theta histogram: 0.01 deg bins (uniform: numpy fast path)
TH_EDGES = np.linspace(0.0, TH_MAX, TH_NB + 1)
AZ_NB = 720                                     # azimuth histogram: 0.5 deg bins (sector edges at 22.5 + 45 k fall on edges)
AZ_EDGES = np.linspace(0.0, 360.0, AZ_NB + 1)
FM_NB, FM_MAX = 10000, 10.0                     # |f| / g histogram: 0.001 g bins
THR = (0.6, 1.0, 2.0, 2.42, 4.0, 7.0, 10.0)
AZ_THR = (0.6, 2.42)
# coordinator relay 2026-10-13 (Mechanical screen of the re-routed coil): hump volume vs tilt, worst direction (az ~45 deg)
HUMP_T = (0.6, 1.0, 2.0, 4.0, 10.0)
HUMP_V = (0.0, 1.9, 4.2, 9.6, 17.1)
TRAP_REROUTE, TRAP_ZERO_ABORT = 13.53, 18.86    # cm3: re-routed trap (P_abort 0) and the zero-abort limit (W 0.65 s)
WIND_LIM = 6.0                                  # m/s: proposed mean-wind criterion (RG-06)


def fly_rec(c, disp):
    """run6.fly with the 1 ms recorder; also returns the parameter vector (accelerometer errors, IMU station)."""
    c = dict(c, rec_dt=DT)
    par, apar, comp, mp, tab, info = R.build(c, disp)
    rec = np.zeros((NROWS, s6.NREC))
    r = s6.run6(par, apar.copy(), comp, mp, tab["Fg"], tab["Dg"], tab["mox"], tab["mf"], tab["Pg"], tab["ceil"], rec)
    res = dict(zip(s6.RES_NAMES, r))
    return res, rec[: int(res["nrec"])], par, info


def specific_force(sub):
    """body-axis specific force at the CG for records 1..n-1 of sub (dv/dt with the attitude of the previous record)."""
    t = sub[:, I["t"]]
    v = sub[:, [I["vx"], I["vy"], I["vz"]]]
    dt = np.diff(t)
    a = np.diff(v, axis=0) / dt[:, None]
    a[:, 2] += G0
    w, x, y, z = (sub[:-1, I[k]] for k in ("q0", "q1", "q2", "q3"))
    A, B, C = a[:, 0], a[:, 1], a[:, 2]
    fx = (1 - 2 * (y * y + z * z)) * A + 2 * (x * y + w * z) * B + 2 * (x * z - w * y) * C
    fy = 2 * (x * y - w * z) * A + (1 - 2 * (x * x + z * z)) * B + 2 * (y * z + w * x) * C
    fz = 2 * (x * z + w * y) * A + 2 * (y * z - w * x) * B + (1 - 2 * (x * x + y * y)) * C
    return fx, fy, fz, dt


def at_station(fx, fy, fz, wx, wy, wz, ax, ay, r):
    return fx + ay * r + wx * wz * r, fy - ax * r + wy * wz * r, fz - (wx * wx + wy * wy) * r


def ang(fx, fy, fz):
    return np.degrees(np.arctan2(np.hypot(fx, fy), fz)), np.mod(np.degrees(np.arctan2(fy, fx)), 360.0)


def trailing_mean(x, n):
    """trailing moving average over n samples (first n-1 use the available samples)."""
    c = np.cumsum(np.insert(x, 0, 0.0))
    k = np.arange(1, len(x) + 1)
    lo = np.maximum(k - n, 0)
    return (c[k] - c[lo]) / (k - lo)


def extract(res, rec, par, info):
    t = rec[:, I["t"]]
    tr = float(res["t_relight"])
    if not tr > 0.0:
        return None
    k_rel = int(np.searchsorted(t, tr + 0.5 * DT)) - 1
    k0 = int(np.searchsorted(t, tr - WINS[0] + 0.5 * DT))
    ph = rec[:, I["phase"]]
    i5 = np.where((ph >= 5) & (np.arange(len(t)) > k_rel))[0]
    k_end = int(i5[0]) if len(i5) else k_rel
    if k0 < 1 or k_end >= len(t):
        return None
    sub = rec[k0 - 1:k_end + 1]
    fx, fy, fz, dts = specific_force(sub)
    tt = sub[1:, I["t"]]
    w = sub[:, [I["wx"], I["wy"], I["wz"]]]
    al = np.diff(w, axis=0) / dts[:, None]
    wx, wy, wz = w[1:, 0], w[1:, 1], w[1:, 2]
    zcg = sub[1:, I["zcg"]]
    zp = float(info["z_pivot"])
    fs = {"cg": (fx, fy, fz)}
    fs["hose"] = at_station(fx, fy, fz, wx, wy, wz, al[:, 0], al[:, 1], zp + Z_HOSE_ABOVE_PIVOT - zcg)
    fs["seat"] = at_station(fx, fy, fz, wx, wy, wz, al[:, 0], al[:, 1], zp + Z_SEAT_ABOVE_PIVOT - zcg)
    fs["pivot"] = at_station(fx, fy, fz, wx, wy, wz, al[:, 0], al[:, 1], zp - zcg)
    fs["mv"] = at_station(fx, fy, fz, wx, wy, wz, al[:, 0], al[:, 1], Z_MV - zcg)
    ix, iy, iz = at_station(fx, fy, fz, wx, wy, wz, al[:, 0], al[:, 1], float(par[P["z_imu"]]) - zcg)
    k_ = 1.0 + float(par[P["a_sf"]])
    fs["imu_meas"] = (ix * k_ + float(par[P["a_bx"]]), iy * k_ + float(par[P["a_by"]]), iz * k_ + float(par[P["a_bz"]]))
    th = {}
    az = {}
    for s_, (a_, b_, c_) in fs.items():
        th[s_], az[s_] = ang(a_, b_, c_)
    jr = k_rel - k0                                  # index of the RELIGHT record in the arrays
    m = dict(t=tt, jr=jr, th=th, az=az, fs=fs,
             fmag_g=np.sqrt(fs["hose"][0] ** 2 + fs["hose"][1] ** 2 + fs["hose"][2] ** 2) / G0,
             dg=np.hypot(sub[1:, I["dgx"]], sub[1:, I["dgy"]]), dc=np.hypot(sub[1:, I["dcx"]], sub[1:, I["dcy"]]),
             tilt=sub[1:, I["tilt"]], rate=np.degrees(np.sqrt(wx * wx + wy * wy + wz * wz)),
             chk_fz=float(np.max(np.abs(fz - sub[1:, I["fax"]]))), gaps=int(np.sum(dts > 1.5 * DT)),
             ph=sub[1:, I["phase"]])
    # trailing 1 s and 0.25 s averages of the measured vector (what a flight-software estimate would use)
    for nm, n_ in (("avg1s", 1000), ("avg0p25s", 250)):
        a_, b_, c_ = (trailing_mean(x, n_) for x in fs["imu_meas"])
        m["th_meas_" + nm], m["az_meas_" + nm] = ang(a_, b_, c_)
    # context from the full record
    vz = rec[:, I["vz"]]
    ia = np.where(vz < 0.0)[0]
    idr = np.where(ph >= 3)[0]
    m.update(t_rel=tr, t_light=float(t[k_end]) if k_end > k_rel else float("nan"), h_rel=float(rec[k_rel, I["z"]]),
             vz_rel=float(vz[k_rel]), t_apo=float(t[ia[0]]) if len(ia) else float("nan"),
             t_dro=float(t[idr[0]]) if len(idr) else float("nan"))
    return m


def window_mask(m, which, res):
    t = m["t"]
    tr = m["t_rel"]
    if which == "E0_light":
        return (t > tr + 0.5 * DT)
    if which == "purge":
        # sim6 writes prg_t0 / prg_dur only when the purge is enabled (0.0 otherwise): require a purge that ran
        t0 = float(res.get("prg_t0", -1.0))
        if not (t0 > 0.0 and float(res.get("prg_dur", -1.0)) > 0.0):
            return None
        return (t > t0 - 0.5 * DT) & (t <= tr + 0.5 * DT)
    W = float(which[1:])
    return (t > tr - W + 0.5 * DT) & (t <= tr + 0.5 * DT)


WINDOWS = ("W10", "W5", "W2.5", "purge", "E0_light")


def part_mc():
    os.makedirs(OUT, exist_ok=True)
    jr = json.load(open(f"{S}/throat_growth/throat_growth.json"))["j_ref"]
    MV.TG_JREF_DEFAULT = float(jr["A1"])
    cfg, D, _ = PB.base("A1")
    spec = MV.case_specs()["tot_cal_comp"]
    for arm in ARM_SEL:
        p_csv = os.path.join(OUT, f"ra_runs_{arm.replace('|', '_')}.csv")
        p_npz = os.path.join(OUT, f"ra_{arm.replace('|', '_')}.npz")
        if os.path.exists(p_csv) and os.path.exists(p_npz) and os.environ.get("GNC_RA_FORCE") != "1":
            print("exists", arm, flush=True)
            continue
        t0 = time.time()
        H = {}            # (subset, window, station) -> theta histogram; ('az', subset, window, station, thr) -> az hist
        MX = {}           # exact maxima
        rows = []
        for i in range(N):
            c, disp = MV.run_cfg_case(cfg, D[i], spec, i, "base")
            c.update({k: v for k, v in ARMS[arm].items() if not k.startswith("_")})
            res, rec, par, info = fly_rec(c, disp)
            m = extract(res, rec, par, info)
            ok = int(R.success(res))
            if m is None:
                rows.append(dict(run=i, ok=ok, extracted=0))
                continue
            wind = float(c["wind"])
            subsets = ("all", "wind_lt_6") if wind < WIND_LIM else ("all",)
            row = dict(run=i, ok=ok, extracted=1, wind=wind, gust_scale=float(c["gust_scale"]), t_ign=float(c["t_ign"]),
                       t_relight=m["t_rel"], t_light=m["t_light"], t_apogee=m["t_apo"], t_drogue=m["t_dro"],
                       drogue_to_relight=m["t_rel"] - m["t_dro"], h_relight=m["h_rel"], vz_relight=m["vz_rel"],
                       prg_t0=float(res["prg_t0"]), prg_dur=float(res["prg_dur"]), chk_fz=m["chk_fz"], gaps=m["gaps"],
                       fmag_g_rel=float(m["fmag_g"][m["jr"]]))
            jr_ = m["jr"]
            for s_ in STATIONS:
                row[f"th_rel_{s_}"] = float(m["th"][s_][jr_])
                row[f"az_rel_{s_}"] = float(m["az"][s_][jr_])
            for nm in ("avg1s", "avg0p25s"):
                row[f"th_rel_meas_{nm}"] = float(m["th_meas_" + nm][jr_])
                row[f"az_rel_meas_{nm}"] = float(m["az_meas_" + nm][jr_])
            row["dg_rel"] = float(m["dg"][jr_])
            row["dc_rel"] = float(m["dc"][jr_])
            row["tilt_rel"] = float(m["tilt"][jr_])
            for wname in WINDOWS:
                msk = window_mask(m, wname, res)
                if msk is None or not msk.any():
                    continue
                tag = wname.replace(".", "p")
                for s_ in STATIONS:
                    th_ = m["th"][s_][msk]
                    row[f"thmax_{tag}_{s_}"] = float(th_.max())
                    if s_ == "hose":
                        row[f"t_thmax_{tag}_hose_after_drogue"] = float(m["t"][msk][int(np.argmax(th_))] - m["t_dro"])
                        row[f"t_thmax_{tag}_hose_before_E0"] = float(m["t_rel"] - m["t"][msk][int(np.argmax(th_))])
                    if s_ in ("hose", "imu_meas"):
                        row[f"thp95_{tag}_{s_}"] = float(np.percentile(th_, 95))
                        # angle of the window-mean vector (slow redistribution of the line contents)
                        mv_ = [float(np.mean(x[msk])) for x in m["fs"][s_]]
                        row[f"thmean_{tag}_{s_}"] = float(np.degrees(np.arctan2(np.hypot(mv_[0], mv_[1]), mv_[2])))
                        row[f"azmean_{tag}_{s_}"] = float(np.mod(np.degrees(np.arctan2(mv_[1], mv_[0])), 360.0))
                    for sb in subsets:
                        k = (sb, wname, s_)
                        H[k] = H.get(k, 0) + np.histogram(np.clip(th_, 0.0, TH_MAX - 1e-6), bins=TH_NB, range=(0.0, TH_MAX))[0]
                        MX[k] = max(MX.get(k, 0.0), float(th_.max()))
                        for thr in AZ_THR:
                            sel = th_ > thr
                            ka = ("az", sb, wname, s_, thr)
                            H[ka] = H.get(ka, 0) + np.histogram(m["az"][s_][msk][sel], bins=AZ_NB, range=(0.0, 360.0))[0]
                fm = m["fmag_g"][msk]
                row[f"fmin_g_{tag}"] = float(fm.min())
                row[f"dgmax_{tag}"] = float(m["dg"][msk].max())
                row[f"dcmax_{tag}"] = float(m["dc"][msk].max())
                row[f"tiltmax_{tag}"] = float(m["tilt"][msk].max())
                row[f"ratemax_{tag}"] = float(m["rate"][msk].max())
                for sb in subsets:
                    kf = ("fmag", sb, wname)
                    H[kf] = H.get(kf, 0) + np.histogram(np.clip(fm, 0.0, FM_MAX - 1e-6), bins=FM_NB, range=(0.0, FM_MAX))[0]
            rows.append(row)
            if (i + 1) % 100 == 0:
                print(f"  {arm} {i + 1}/{N} ({time.time() - t0:.0f} s)", flush=True)
        keys = sorted({k for r in rows for k in r}, key=lambda k: (k != "run", k))
        with open(p_csv, "w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=keys)
            wr.writeheader()
            for r in rows:
                wr.writerow(r)
        np.savez_compressed(p_npz, keys=np.array([json.dumps(list(k)) for k in H], dtype=object),
                            vals=np.array([H[k] for k in H], dtype=object),
                            mx_keys=np.array([json.dumps(list(k)) for k in MX], dtype=object),
                            mx_vals=np.array([MX[k] for k in MX]))
        print(f"{arm}: {len(rows)} runs, P {np.mean([r['ok'] for r in rows]):.3f} ({time.time() - t0:.0f} s)", flush=True)


def hist_q(h, edges, qs):
    c = np.cumsum(h)
    n = c[-1]
    out = {}
    for q in qs:
        j = int(np.searchsorted(c, q / 100.0 * n))
        out[f"p{q:g}"] = float(edges[min(j + 1, len(edges) - 1)])       # bin upper edge (0.01 deg resolution)
    return out


def q_runs(x, qs=(50, 95, 99)):
    x = np.asarray([v for v in x if np.isfinite(v)], float)
    if x.size == 0:
        return None
    return dict({f"p{q:g}": float(np.percentile(x, q)) for q in qs}, max=float(x.max()), n=int(x.size))


def sectors(h_az):
    """share in 8 sectors of 45 deg centred on 0, 45, ..., 315 deg (sector k = [45 k - 22.5, 45 k + 22.5)) from the 0.5 deg
    azimuth histogram (the sector edges fall on bin edges: exact)."""
    c = 0.5 * (AZ_EDGES[1:] + AZ_EDGES[:-1])
    sec = (np.floor(np.mod(c + 22.5, 360.0) / 45.0)).astype(int)
    tot = float(np.sum(h_az))
    return {f"{45 * k}": (round(float(np.sum(h_az[sec == k])) / tot, 4) if tot > 0 else None) for k in range(8)}


def hump(th):
    return float(np.interp(th, HUMP_T, HUMP_V, left=0.0, right=HUMP_V[-1]))


def _doc_part(start, end):
    d = __doc__
    i = d.index(start)
    j = d.index(end, i)
    return " ".join(d[i:j].split())


def part_eval():
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, owner="GNC (01-systems-gnc)",
               request="coordinator 2026-10-13, items 1-2 (item 3 drain pose withdrawn: Mechanical refuted it at 10 deg tilt); "
                       "for Mechanical (coil vapour humps) and Combustion (purge sizing)",
               method=_doc_part("Definitions", "Configuration:"), configuration=_doc_part("Configuration:", "Model limits:"),
               model_limits=_doc_part("Model limits:", "Env:"), arms={},
               tags=dict(theta_az_fmag="SIM (sim6 v2.8-dev 6-DOF Monte Carlo, seed 101)", hose_station="ASSUMED",
                         hump_table="coordinator relay 2026-10-13 (Mechanical screen; worst direction; additivity to the "
                                    "13.53 cm3 trap ASSUMED for the conditional screen only)",
                         drogue_model="ASSUMED quasi-steady massless canopy (no pendulum oscillation)"))
    for arm in ARMS:
        p_csv = os.path.join(OUT, f"ra_runs_{arm.replace('|', '_')}.csv")
        p_npz = os.path.join(OUT, f"ra_{arm.replace('|', '_')}.npz")
        if not (os.path.exists(p_csv) and os.path.exists(p_npz)):
            continue
        rows = [r for r in csv.DictReader(open(p_csv)) if r.get("extracted") == "1"]
        z = np.load(p_npz, allow_pickle=True)
        H = {tuple(json.loads(k)): v for k, v in zip(z["keys"], z["vals"])}
        MX = {tuple(json.loads(k)): float(v) for k, v in zip(z["mx_keys"], z["mx_vals"])}

        def col(k, rs=None):
            return np.array([float(r[k]) if r.get(k) not in (None, "") else np.nan for r in (rs or rows)])

        e = dict(n_runs=len(rows), P_context=float(np.mean(col("ok"))),
                 checks=dict(fz_reconstruction_max_abs_err_mps2=float(np.nanmax(col("chk_fz"))),
                             record_gaps=int(np.nansum(col("gaps")))),
                 timing=dict(t_relight_s=q_runs(col("t_relight"), (1, 50, 99)),
                             drogue_to_relight_s=q_runs(col("drogue_to_relight"), (1, 50, 99)),
                             h_relight_m=q_runs(col("h_relight"), (1, 50, 99)), vz_relight_mps=q_runs(col("vz_relight"), (1, 50, 99)),
                             E0_to_light_s=q_runs(col("t_light") - col("t_relight"), (1, 50, 99))))
        subs = {"all": rows, "wind_lt_6": [r for r in rows if float(r["wind"]) < WIND_LIM]}
        for sb, rs in subs.items():
            d = dict(n_runs=len(rs))
            for wname in WINDOWS:
                tag = wname.replace(".", "p")
                wd = {}
                for s_ in STATIONS:
                    h = H.get((sb, wname, s_))
                    if h is None:
                        continue
                    sd = dict(pooled_time=dict(hist_q(h, TH_EDGES, (50, 95, 99)), max=MX[(sb, wname, s_)]),
                              per_run_max=q_runs(col(f"thmax_{tag}_{s_}", rs)))
                    if s_ in ("hose", "imu_meas"):
                        sd["per_run_window_mean_vector"] = q_runs(col(f"thmean_{tag}_{s_}", rs))
                        tot = float(np.sum(h))
                        cum = np.cumsum(h)
                        sd["time_fraction_above_deg"] = {f"{thr:g}": round(1.0 - float(cum[int(round(thr / 0.01)) - 1]) / tot, 5)
                                                         for thr in THR}
                        for thr in AZ_THR:
                            ha = H.get(("az", sb, wname, s_, thr))
                            if ha is not None and np.sum(ha) > 0:
                                sd[f"azimuth_sectors_time_share_theta_gt_{thr:g}"] = sectors(ha)
                    wd[s_] = sd
                if not any(s_ in wd for s_ in STATIONS):
                    continue                      # window absent in this arm (e.g. no purge)
                hf = H.get(("fmag", sb, wname))
                if hf is not None:
                    wd["fmag_g_hose_pooled"] = hist_q(hf, np.linspace(0.0, FM_MAX, FM_NB + 1), (1, 5, 50, 99))
                wd["gimbal_deg"] = dict(truth_per_run_max=q_runs(col(f"dgmax_{tag}", rs)),
                                        command_per_run_max=q_runs(col(f"dcmax_{tag}", rs)))
                wd["body_tilt_from_vertical_deg_per_run_max"] = q_runs(col(f"tiltmax_{tag}", rs))
                wd["body_rate_dps_per_run_max"] = q_runs(col(f"ratemax_{tag}", rs))
                if wd:
                    d[wname] = wd
            at = {}
            for s_ in STATIONS:
                th_ = col(f"th_rel_{s_}", rs)
                at[s_] = dict(theta_deg=q_runs(th_), runs_above_deg={f"{thr:g}": int(np.sum(th_ > thr)) for thr in THR})
                az_ = col(f"az_rel_{s_}", rs)
                sel = th_ > 0.6
                if sel.any():
                    h_ = np.histogram(az_[sel], bins=AZ_NB, range=(0.0, 360.0))[0]
                    at[s_]["azimuth_sectors_runs_share_theta_gt_0.6"] = sectors(h_)
            for nm in ("avg1s", "avg0p25s"):
                at[f"imu_meas_{nm}"] = dict(theta_deg=q_runs(col(f"th_rel_meas_{nm}", rs)))
            thh = col("th_rel_hose", rs)
            hv = np.array([hump(x) for x in thh])
            at["hump_screen_hose"] = dict(
                note="coordinator table (worst direction, applied to every azimuth: conservative); conditional on the humps "
                     "adding to the 13.53 cm3 re-routed trap (ASSUMED): allowance 18.86 - 13.53 = 5.33 cm3, reached at "
                     f"theta {np.interp(TRAP_ZERO_ABORT - TRAP_REROUTE, HUMP_V, HUMP_T):.2f} deg",
                hump_cm3=q_runs(hv), runs_exceeding_allowance=int(np.sum(hv > TRAP_ZERO_ABORT - TRAP_REROUTE)),
                runs_with_humps_theta_gt_0p6=int(np.sum(thh > 0.6)))
            at["gimbal_deg"] = dict(truth=q_runs(col("dg_rel", rs)), command=q_runs(col("dc_rel", rs)))
            at["fmag_g_hose"] = q_runs(col("fmag_g_rel", rs), (1, 50, 99))
            d["at_relight"] = at
            d["W10_hose_max_timing_s"] = dict(after_drogue_deploy=q_runs(col("t_thmax_W10_hose_after_drogue", rs), (1, 50, 99)),
                                              before_E0=q_runs(col("t_thmax_W10_hose_before_E0", rs), (1, 50, 99)))
            e[sb] = d
        out["arms"][arm] = e
    out["answer_item2_gimbal"] = ("sim6 FSW: the attitude loop is inactive in the coast and the drogue descent (phase 2-4: no "
                                  "thrust, no control authority) and the gimbal command returns to neutral through the shaping "
                                  "chain (slew/acceleration limit + low-pass); the engine is held at neutral by the servos "
                                  "(hose spring and base excitation only). See gimbal_deg per window.")
    with open(os.path.join(OUT, "relight_attitude_v1.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    for arm, e in out["arms"].items():
        a = e["all"]
        w10 = a["W10"]["hose"]["pooled_time"]
        rel = a["at_relight"]["hose"]["theta_deg"]
        print(f"{arm:14s} n {e['n_runs']} | hose W10 pooled p50/p95/p99/max {w10['p50']:.2f}/{w10['p95']:.2f}/{w10['p99']:.2f}/"
              f"{w10['max']:.2f} deg | at E0 p50/p95/p99/max {rel['p50']:.2f}/{rel['p95']:.2f}/{rel['p99']:.2f}/{rel['max']:.2f} | "
              f"gimbal W10 max {a['W10']['gimbal_deg']['truth_per_run_max']['max']:.3f} deg | fz chk "
              f"{e['checks']['fz_reconstruction_max_abs_err_mps2']:.2e}", flush=True)


def part_identity():
    """the 1 ms recorder does not change the flight: res (except nrec) equals run6.fly at the default recorder, 3 runs/arm."""
    jr = json.load(open(f"{S}/throat_growth/throat_growth.json"))["j_ref"]
    MV.TG_JREF_DEFAULT = float(jr["A1"])
    cfg, D, _ = PB.base("A1")
    spec = MV.case_specs()["tot_cal_comp"]
    bad = []
    for arm in ARM_SEL:
        for i in (0, 1, 2):
            c, disp = MV.run_cfg_case(cfg, D[i], spec, i, "base")
            c.update({k: v for k, v in ARMS[arm].items() if not k.startswith("_")})
            a = R.fly(c, disp, nrec=10)[0]
            b = fly_rec(c, disp)[0]
            d = [k for k in s6.RES_NAMES if k != "nrec" and not (a[k] == b[k] or (np.isnan(a[k]) and np.isnan(b[k])))]
            if d:
                bad.append((arm, i, d))
    print("identity:", "OK" if not bad else bad, flush=True)
    with open(os.path.join(OUT, "identity_check.json"), "w") as f:
        json.dump(dict(version=VERSION, runs_per_arm=3, arms=ARM_SEL, mismatches=[list(map(str, b)) for b in bad],
                       passed=not bad), f, indent=1)


HUB = os.environ.get("GNC_RA_HUB", "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/relight_attitude")


def _atomic(dst, data):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst + ".tmp_stage"
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, dst)


def compact():
    """the small summary for the coordinator, Mechanical and Combustion (from the full evaluation json)."""
    full = json.load(open(os.path.join(OUT, "relight_attitude_v1.json")))

    def q4(d, keys=("p50", "p95", "p99", "max")):
        return {k: round(float(d[k]), 3) for k in keys if d and k in d} if d else None

    res = {}
    for arm, e in full["arms"].items():
        a = e["all"]
        hz = {}
        for wname in WINDOWS:
            w = a.get(wname, {}).get("hose")
            if w:
                hz[f"{wname}_time"] = q4(w["pooled_time"])
                hz[f"{wname}_run_max"] = q4(w["per_run_max"])
        hz["at_RELIGHT"] = q4(a["at_relight"]["hose"]["theta_deg"])
        hz["W10_time_fraction_above_deg"] = a["W10"]["hose"]["time_fraction_above_deg"]
        hz["at_RELIGHT_runs_above_deg"] = a["at_relight"]["hose"]["runs_above_deg"]
        im = dict(W10_time=q4(a["W10"]["imu_meas"]["pooled_time"]), at_RELIGHT=q4(a["at_relight"]["imu_meas"]["theta_deg"]),
                  at_RELIGHT_1s_trailing_mean=q4(a["at_relight"]["imu_meas_avg1s"]["theta_deg"]))
        az = {"W10_time_theta_gt_0.6": a["W10"]["hose"].get("azimuth_sectors_time_share_theta_gt_0.6"),
              "W10_time_theta_gt_2.42": a["W10"]["hose"].get("azimuth_sectors_time_share_theta_gt_2.42"),
              "W2.5_time_theta_gt_0.6": a["W2.5"]["hose"].get("azimuth_sectors_time_share_theta_gt_0.6"),
              "at_RELIGHT_runs_theta_gt_0.6": a["at_relight"]["hose"].get("azimuth_sectors_runs_share_theta_gt_0.6")}
        if "purge" in a:
            az["purge_time_theta_gt_0.6"] = a["purge"]["hose"].get("azimuth_sectors_time_share_theta_gt_0.6")
        gm = dict(W10_truth_run_max=q4(a["W10"]["gimbal_deg"]["truth_per_run_max"]),
                  W10_command_run_max=q4(a["W10"]["gimbal_deg"]["command_per_run_max"]),
                  at_RELIGHT_truth=q4(a["at_relight"]["gimbal_deg"]["truth"]),
                  E0_light_truth_run_max=q4(a["E0_light"]["gimbal_deg"]["truth_per_run_max"]) if "E0_light" in a else None)
        fm = dict(W10_time={k: round(v, 3) for k, v in a["W10"]["fmag_g_hose_pooled"].items()},
                  at_RELIGHT={k: round(float(v), 3) for k, v in a["at_relight"]["fmag_g_hose"].items() if k != "n"})
        st_rel = {s_: q4(a["at_relight"][s_]["theta_deg"]) for s_ in STATIONS}
        st_w10 = {s_: q4(a["W10"][s_]["per_run_max"]) for s_ in STATIONS}
        st_w5 = {s_: q4(a["W5"][s_]["per_run_max"]) for s_ in STATIONS}
        w6 = e["wind_lt_6"]
        res[arm] = dict(n_runs=e["n_runs"], P_context=round(e["P_context"], 3), timing=e["timing"], theta_hose_deg=hz,
                        theta_imu_measured_deg=im, azimuth_hose_sector_share=az, fmag_g_hose=fm, gimbal_deg=gm,
                        body_tilt_from_vertical_deg_W10_run_max=q4(a["W10"]["body_tilt_from_vertical_deg_per_run_max"]),
                        wind_lt_6=dict(n_runs=w6["n_runs"], theta_hose_W10_time=q4(w6["W10"]["hose"]["pooled_time"]),
                                       theta_hose_W2p5_time=q4(w6["W2.5"]["hose"]["pooled_time"]),
                                       theta_hose_at_RELIGHT=q4(w6["at_relight"]["hose"]["theta_deg"])),
                        hump_screen_at_RELIGHT=a["at_relight"]["hump_screen_hose"],
                        theta_by_station_deg=dict(at_RELIGHT=st_rel, W10_run_max=st_w10, W5_run_max=st_w5),
                        W10_hose_max_timing_s=a["W10_hose_max_timing_s"],
                        checks=e["checks"])
    return dict(id="relight_attitude", version="v1", date="2026-10-13", owner="GNC (01-systems-gnc)", sim=full["sim"],
                script="01-systems-gnc/staging_v3.1/relight_attitude/m2_relight_attitude.py", request=full["request"],
                definitions=full["method"], configuration=full["configuration"], model_limits=full["model_limits"],
                tags=full["tags"], answer_item2_gimbal=full["answer_item2_gimbal"], results=res,
                files=dict(full="relight_attitude_full_v1.json", per_run="ra_runs_<arm>.csv.gz", identity="identity_check.json",
                           script="m2_relight_attitude.py"))


def findings(full):
    """numeric findings for the compact file (numbers read from the full evaluation, not transcribed)."""
    A = full["arms"]
    r, p, nj = A["A1|ref"]["all"], A["A1|P25"]["all"], A["A1|P25_nojet"]["all"]

    def f2(d, k="p50"):
        return f"{d[k]:.2f}"

    def q(d):
        return "/".join(f2(d, k) for k in ("p50", "p95", "p99", "max"))

    rh, ph = r["at_relight"]["hose"], p["at_relight"]["hose"]
    out = [
        "Gimbal (item 2): commanded neutral in the whole window (sim6 FSW: attitude loop inactive without thrust, command returned "
        "to 0 through the shaping chain; |command| < 1e-80 deg); the engine angle stays within "
        f"{r['W10']['gimbal_deg']['truth_per_run_max']['max']:.3f} deg of neutral (hose spring and base excitation only), so body "
        "axes = engine axes for the angles below.",
        f"No purge (A1|ref), hose station: theta at RELIGHT p50/p95/p99/max {q(rh['theta_deg'])} deg; {rh['runs_above_deg']['0.6']}/500 runs "
        f"above 0.6 deg, {rh['runs_above_deg']['1']} above 1 deg. Over the 10 s before RELIGHT (time-pooled) {q(r['W10']['hose']['pooled_time'])} "
        f"deg; share of time above 0.6 / 1 / 2 / 4 deg: {r['W10']['hose']['time_fraction_above_deg']['0.6']:.4f} / "
        f"{r['W10']['hose']['time_fraction_above_deg']['1']:.4f} / {r['W10']['hose']['time_fraction_above_deg']['2']:.4f} / "
        f"{r['W10']['hose']['time_fraction_above_deg']['4']:.4f}.",
        f"The large angles of the 10 s window are the drogue-deployment swing: the per-run maximum (p50/p95/p99/max "
        f"{q(r['W10']['hose']['per_run_max'])} deg) occurs p50 {r['W10_hose_max_timing_s']['after_drogue_deploy']['p50']:.1f} s after the "
        f"deployment, i.e. at the start of the window for the runs whose descent is short. Over the last 5 s the per-run maximum is "
        f"{q(r['W5']['hose']['per_run_max'])} deg and the share of time above 0.6 deg is {r['W5']['hose']['time_fraction_above_deg']['0.6']:.4f}.",
        "Azimuth without purge: no preferred direction (time share of theta > 0.6 deg per 45-deg sector, W10: "
        + ", ".join(f"{k} {v:.2f}" for k, v in r["W10"]["hose"]["azimuth_sectors_time_share_theta_gt_0.6"].items())
        + "); Mechanical's worst direction (az 45 deg sector) holds "
        f"{r['W10']['hose']['azimuth_sectors_time_share_theta_gt_0.6']['45']:.2f} of it.",
        f"Forced purge with a lateral vent (A1|P25: 2.1 N reaction toward body az {0} deg at the pivot height, ASSUMED): theta at RELIGHT "
        f"{q(ph['theta_deg'])} deg, all 500 runs above 0.6 deg ({ph['runs_above_deg']['1']} above 1 deg, {ph['runs_above_deg']['2']} above 2 "
        f"deg), azimuth in the jet-reaction sector (sector 0: {ph['azimuth_sectors_runs_share_theta_gt_0.6']['0']:.3f} of the runs); during "
        f"the purge (time-pooled) {q(p['purge']['hose']['pooled_time'])} deg. The vent reaction tilts the specific force by about "
        "F_jet / (m g) = 0.8 deg toward the reaction azimuth and the drogue restoring moment adds about 0.3 deg. With a balanced or "
        f"axial vent (A1|P25_nojet) theta at RELIGHT is {q(nj['at_relight']['hose']['theta_deg'])} deg (as without purge). The vent "
        "direction is therefore a design input for the hump volume (Mechanical: per-azimuth pockets; Combustion: purge sizing).",
        "Station dependence (theta at RELIGHT p95 / max, no purge): "
        + ", ".join(f"{s_} {r['at_relight'][s_]['theta_deg']['p95']:.2f} / {r['at_relight'][s_]['theta_deg']['max']:.2f}"
                     for s_ in ("seat", "hose", "mv", "pivot", "cg", "imu_meas"))
        + " deg. A change of the nose-drogue force rotates the vehicle about a centre of percussion about 0.22 m below the CG, near "
          "the engine, so the engine-end stations see the smallest lateral specific force; the hose station height is ASSUMED.",
        f"Measured (IMU) vector: the IMU is 0.48 m above the CG, so the raw measured angle is larger than at the hose (RELIGHT "
        f"p50/p95/p99/max {q(r['at_relight']['imu_meas']['theta_deg'])} deg); a 1 s trailing mean gives "
        f"{q(r['at_relight']['imu_meas_avg1s']['theta_deg'])} deg. The physical angle for the line contents is the hose-station value.",
        f"Specific-force magnitude at the hose: 10 s window p1/p5/p50 {r['W10']['fmag_g_hose_pooled']['p1']:.2f}/"
        f"{r['W10']['fmag_g_hose_pooled']['p5']:.2f}/{r['W10']['fmag_g_hose_pooled']['p50']:.2f} g (lowest values at the start of the "
        f"window, drogue build-up); at RELIGHT {r['at_relight']['fmag_g_hose']['p1']:.2f}-{r['at_relight']['fmag_g_hose']['max']:.2f} g.",
        "Mean wind < 6 m/s (proposed launch criterion, "
        f"{A['A1|ref']['wind_lt_6']['n_runs']} runs): theta at RELIGHT {q(A['A1|ref']['wind_lt_6']['at_relight']['hose']['theta_deg'])} deg "
        f"(no purge) and {q(A['A1|P25']['wind_lt_6']['at_relight']['hose']['theta_deg'])} deg (P25).",
        "Conditional hump screen (coordinator table, worst direction applied to every azimuth, humps ASSUMED additive to the 13.53 cm3 "
        f"trap; allowance 5.33 cm3 reached at 2.42 deg): at RELIGHT no run exceeds it (no purge: hump max "
        f"{r['at_relight']['hump_screen_hose']['hump_cm3']['max']:.2f} cm3; P25: max {p['at_relight']['hump_screen_hose']['hump_cm3']['max']:.2f} "
        "cm3). This screen is conservative on direction and NOT conservative on the drogue model (next item).",
        "Model limit that governs: the 6-DOF drogue is a quasi-steady massless canopy at the nose tip (no canopy pendulum oscillation, "
        "riser elasticity, swivel friction or inflation). A real canopy oscillates and its swing adds directly to theta; the values "
        "above are a lower-fidelity baseline until drop-test or literature data for the chosen canopy are folded in (HYPOTHESIS to "
        "refute: theta at the hose stays below 0.6 deg in the last 5 s of a real drogue descent).",
    ]
    return out


def part_hub():
    """write the compact json, the full json, the per-run CSVs (gz), the identity check and this script to the hub folder
    (atomic), wait 10 s, read back against the manifest."""
    import gzip
    import hashlib
    c = compact()
    c["findings"] = findings(json.load(open(os.path.join(OUT, "relight_attitude_v1.json"))))
    jobs = [("relight_attitude_v1.json", json.dumps(c, indent=1, default=float).encode()),
            ("relight_attitude_full_v1.json", open(os.path.join(OUT, "relight_attitude_v1.json"), "rb").read()),
            ("identity_check.json", open(os.path.join(OUT, "identity_check.json"), "rb").read()),
            ("m2_relight_attitude.py", open(os.path.abspath(__file__), "rb").read())]
    for arm in ARMS:
        p = os.path.join(OUT, f"ra_runs_{arm.replace('|', '_')}.csv")
        if os.path.exists(p):
            jobs.append((os.path.basename(p) + ".gz", gzip.compress(open(p, "rb").read(), compresslevel=9, mtime=0)))
    man = {}
    try:
        for rel, data in jobs:
            _atomic(os.path.join(HUB, rel), data)
            man[rel] = hashlib.sha256(data).hexdigest()
        _atomic(os.path.join(HUB, "MANIFEST.sha256"),
                ("# " + VERSION + "\n" + "\n".join(f"{h}  {r}" for r, h in sorted(man.items())) + "\n").encode())
    finally:
        for f_ in os.listdir(HUB):
            if f_.endswith(".tmp_stage"):
                os.remove(os.path.join(HUB, f_))
    time.sleep(10.0)
    bad = [r for r, h in man.items() if hashlib.sha256(open(os.path.join(HUB, r), "rb").read()).hexdigest() != h]
    print("hub:", HUB, len(man), "files; read-back", "OK" if not bad else f"MISMATCH {bad}", flush=True)
    print("compact json sha256/16", man["relight_attitude_v1.json"][:16], "size", len(jobs[0][1]), "B", flush=True)
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if "identity" in PARTS:
        part_identity()
    if "mc" in PARTS:
        part_mc()
    if "eval" in PARTS:
        part_eval()
    if "hub" in PARTS:
        part_hub()
