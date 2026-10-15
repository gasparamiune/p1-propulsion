"""m2_bitcheck_v213 v1.0 (GNC rev4, 2026-10-13): sim6 / run6 v2.13-dev (amendment J: servo jam jam_*, ECU gimbal fault
monitor gfm_*; Electronics RE-24) against v2.12-dev.

Part A (off = identical): the cases of m2_bitcheck_v212 (decided A1 path with records, R2 flame-out path, unpurged nrLO, the
V2 release hold, the V2 start-level hold with the cold-flow bound, the stuck-pintle fault of amendment F on its onsets) are
flown in gnc_dev7 (sim6 v2.13-dev) with jam_on 0 / gfm_on 0 and compared with the stored v2.12-dev file
out/rev3/bitcheck_v212/bc_v212.npz (sim6 b0d9d8a0ded64e28, run6 a1df28f35a2576f1; flown by m2_bitcheck_v212 with the same env).
One more case flies the decided path with the monitor in RECORD mode (gfm_on 1, no jam): every common result and record column
must still equal v2.12 (the monitor has no side effect unless it aborts).
Part B (functional, gnc_dev7 only):
  B1 _jam_proj on random linkage states (|angles| <= 8 deg, rates <= 3 rad/s) with the flown lever geometry: the jammed
     coordinate equals its onset value and has zero rate, the free coordinate and rate are unchanged (all to 1e-12 m, m/s).
  B2 small-angle geometry: servo 1 (azimuth act_az1) jammed at neutral, an alpha command a moves the linkage to about
     (a/2, -a/2) (Electronics SIL note: 1.0 deg per-axis mismatch at a 2 deg command) within 2 % for a = 1-4 deg.
  B3 _gfm_step unit tests: persistence (mismatch above the threshold for 49 ticks: no trip; 50 ticks: trip), the rate
     allowance (a mismatch equal to win |shaped - model| / tau + 1.4 deg does not trip), and the window-minimum record.
  B4 bench harness of the Electronics SIL S6 cases with the same two functions (_gfm_step, _jam_proj) and a simple per-axis
     servo (the build's gim_wn / gim_zeta / gim_delay, command tracker and low-pass, rigid linkage, encoder quantisation):
     expected classes as the SIL v2.10 run log (results/sil_v2p10/sil_run_log.txt 4a1698f2476e4928): 2 deg alpha sine jam
     undetected; 4 deg detected (SIL +175 ms); jam at the commanded angle undetected; full slews without a jam no trip; jam
     during full slews detected (SIL +79 ms). The trip latencies are reported beside the SIL values; the plants differ, so
     only the class is a pass criterion.
  B5 flights (decided path, A1_none liq, runs 0-3): (i) jam in the landing burn, monitor RECORD: the records before the
     onset equal the jam-off flight; after it the jammed coordinate (from the recorded servo angles) is constant to 1e-9 m;
     (ii) forced abort path: monitor ABORT with gfm_thr 1e-5 rad (trips on the encoder quantisation in the ascent): abort
     flag set while lit in phase 1, no relight (starts 1), thrust below 1 N 0.5 s after the abort.
Usage: GNC_TREE=<gnc_dev7> GNC_BC_OUT=<npz> python m2_bitcheck_v213.py fly; python m2_bitcheck_v213.py compare <bc_v212.npz>
<bc_v213.npz> <out json>; python m2_bitcheck_v213.py func <out json>. Env as m2r3_env.sh with GNC_IFACE_PIN =
pins_rev3/pins_rev3.sha256 (as m2_bitcheck_v212). SIM only."""
import hashlib
import json
import os
import sys
import numpy as np

TREE = os.environ.get("GNC_TREE", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, TREE)
sys.path.insert(0, os.path.join(TREE, "scripts"))
import m2_rg01_refly as F  # noqa: E402
import m2_bitcheck_v211 as B11  # noqa: E402
import m2_bitcheck_v212 as B12  # noqa: E402
from gncsim import run6 as R, sim6 as s6  # noqa: E402

VERSION = "m2_bitcheck_v213 v1.0"
CASES = B12.CASES
FCASES = B12.FCASES
GFM1 = ("dec_pw_gfm1", "A1_none", "pw", "G73", "", dict(gfm_on=1), 12, 2)   # compared with v2.12 dec_pw
SIL_LOG = "/home/claude/work/shared-fallback/engine/06-electronics/results/sil_v2p10/sil_run_log.txt"


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def part_fly():
    out = {}
    for name, base, st, pu, pl, ex, n, nrec in CASES + [GFM1]:
        r, recs = B11.fly_case(base, st, pu, pl, ex, n, nrec)
        out[f"{name}|res"] = r
        for k, rc in enumerate(recs):
            out[f"{name}|rec{k}"] = rc
        print(name, "done", flush=True)
    for name, on, lv, br, kind, n, nrec in FCASES:
        r, recs = B11.fly_fault(on, lv, br, kind, n, nrec)
        out[f"{name}|res"] = r
        for k, rc in enumerate(recs):
            out[f"{name}|rec{k}"] = rc
        print(name, "done", flush=True)
    p = os.environ["GNC_BC_OUT"]
    np.savez_compressed(p, res_names=np.array(s6.RES_NAMES), rec_names=np.array(s6.REC_NAMES),
                        sim=np.array(s6.SIM6_VERSION), sim6_sha16=np.array(sha16(s6.__file__)),
                        run6_sha16=np.array(sha16(R.__file__)), **out)
    print("wrote", p, flush=True)


def part_compare(pa, pb, pout):
    a = np.load(pa, allow_pickle=False)
    b = np.load(pb, allow_pickle=False)
    ra, rb = list(a["res_names"]), list(b["res_names"])
    ca, cb = list(a["rec_names"]), list(b["rec_names"])
    common_r = [k for k in ra if k in rb]
    common_c = [k for k in ca if k in cb]
    ia_r = [ra.index(k) for k in common_r]; ib_r = [rb.index(k) for k in common_r]
    ia_c = [ca.index(k) for k in common_c]; ib_c = [cb.index(k) for k in common_c]
    rep = dict(version=VERSION, a=dict(path=pa, sim=str(a["sim"]), sim6_sha16=str(a["sim6_sha16"]), run6_sha16=str(a["run6_sha16"])),
               b=dict(path=pb, sim=str(b["sim"]), sim6_sha16=str(b["sim6_sha16"]), run6_sha16=str(b["run6_sha16"])),
               common_results=len(common_r), new_results=[k for k in rb if k not in ra], common_record_columns=len(common_c),
               new_record_columns=[k for k in cb if k not in ca], cases={}, all_identical=True)
    pairs = [(c[0], c[0], "v2.13 J off") for c in CASES + FCASES] + [(GFM1[0], "dec_pw", "v2.13 monitor RECORD (gfm_on 1)")]
    for nb, na, lab in pairs:
        A = a[f"{na}|res"][:, ia_r]; Bm = b[f"{nb}|res"][:, ib_r]
        same = bool(np.array_equal(A, Bm, equal_nan=True))
        nd = int(np.sum(~((A == Bm) | (np.isnan(A) & np.isnan(Bm)))))
        recs = []
        k = 0
        while f"{na}|rec{k}" in a.files and f"{nb}|rec{k}" in b.files:
            X = a[f"{na}|rec{k}"]; Y = b[f"{nb}|rec{k}"]
            ok = X.shape[0] == Y.shape[0] and np.array_equal(X[:, ia_c], Y[:, ib_c], equal_nan=True)
            recs.append(dict(rows=int(X.shape[0]), identical=bool(ok)))
            same = same and ok
            k += 1
        rep["cases"][f"{nb}|{lab}"] = dict(against=na, runs=int(A.shape[0]), results_identical=bool(np.array_equal(A, Bm, equal_nan=True)),
                                           differing_values=nd, records=recs)
        rep["all_identical"] = rep["all_identical"] and same
    json.dump(rep, open(pout, "w"), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != "cases"}, indent=1))
    for k, v in rep["cases"].items():
        print(k, v["results_identical"], v["differing_values"], [r["identical"] for r in v["records"]])
    print("ALL IDENTICAL" if rep["all_identical"] else "DIFFERENCES FOUND", flush=True)


# ------------------------------------------------------------------------------------------------------------ part B
def geometry():
    cfg, m = F.base_cfg("A1_none", "pw", dict(h_target=285.0))
    par = R.build(cfg)[0]
    g = {k: float(par[getattr(s6, "P_" + k)]) for k in ("act_re", "act_zb", "act_az1", "act_az2", "gim_wn", "gim_zeta",
                                                         "gim_delay", "gim_cmd_rate", "gim_cmd_acc", "gim_lpf_w", "gim_lpf_z",
                                                         "gim_enc_q", "gfm_thr", "gfm_win", "gfm_tau", "gfm_tp", "dt")}
    return g


def b1_proj(g, n=2000):
    rng = np.random.default_rng(20261114)
    out = np.zeros(5)
    worst = dict(jam_coord=0.0, jam_rate=0.0, free_coord=0.0, free_rate=0.0)
    h = 1e-6
    dz = s6._act_dz
    for i in range(n):
        a, b = np.radians(8.0) * (2 * rng.random(2) - 1)
        wa, wb = 3.0 * (2 * rng.random(2) - 1)
        srv = 1 + (i % 2)
        azj = g["act_az1"] if srv == 1 else g["act_az2"]
        azf = g["act_az2"] if srv == 1 else g["act_az1"]
        a0, b0 = np.radians(8.0) * (2 * rng.random(2) - 1)
        sj = dz(a0, b0, azj, g["act_re"], g["act_zb"])
        sf = dz(a, b, azf, g["act_re"], g["act_zb"])
        jf = np.array([(dz(a + h, b, azf, g["act_re"], g["act_zb"]) - dz(a - h, b, azf, g["act_re"], g["act_zb"])) / (2 * h),
                       (dz(a, b + h, azf, g["act_re"], g["act_zb"]) - dz(a, b - h, azf, g["act_re"], g["act_zb"])) / (2 * h)])
        wf = float(jf @ np.array([wa, wb]))
        s6._jam_proj(a, b, wa, wb, sj, azj, azf, g["act_re"], g["act_zb"], out)
        x0, x1, w0, w1 = out[:4]
        jj = np.array([(dz(x0 + h, x1, azj, g["act_re"], g["act_zb"]) - dz(x0 - h, x1, azj, g["act_re"], g["act_zb"])) / (2 * h),
                       (dz(x0, x1 + h, azj, g["act_re"], g["act_zb"]) - dz(x0, x1 - h, azj, g["act_re"], g["act_zb"])) / (2 * h)])
        jf2 = np.array([(dz(x0 + h, x1, azf, g["act_re"], g["act_zb"]) - dz(x0 - h, x1, azf, g["act_re"], g["act_zb"])) / (2 * h),
                        (dz(x0, x1 + h, azf, g["act_re"], g["act_zb"]) - dz(x0, x1 - h, azf, g["act_re"], g["act_zb"])) / (2 * h)])
        worst["jam_coord"] = max(worst["jam_coord"], abs(dz(x0, x1, azj, g["act_re"], g["act_zb"]) - sj))
        worst["free_coord"] = max(worst["free_coord"], abs(dz(x0, x1, azf, g["act_re"], g["act_zb"]) - sf))
        worst["jam_rate"] = max(worst["jam_rate"], abs(float(jj @ np.array([w0, w1]))))
        worst["free_rate"] = max(worst["free_rate"], abs(float(jf2 @ np.array([w0, w1])) - wf))
    ok = all(v < 1e-12 for v in worst.values())
    return dict(n=n, worst=worst, pass_=bool(ok))


def b2_small(g):
    out = np.zeros(5)
    rows = []
    for a_deg in (1.0, 2.0, 3.0, 4.0):
        a = np.radians(a_deg)
        s6._jam_proj(a, 0.0, 0.0, 0.0, 0.0, g["act_az1"], g["act_az2"], g["act_re"], g["act_zb"], out)
        x0, x1 = np.degrees(out[0]), np.degrees(out[1])
        rows.append(dict(cmd_alpha_deg=a_deg, linkage_deg=[round(x0, 5), round(x1, 5)],
                         per_axis_mismatch_deg=[round(a_deg - x0, 5), round(-x1, 5)],
                         along_servo1_line_cmd_deg=round(a_deg / np.sqrt(2.0), 4),
                         rel_err=max(abs(x0 / (a_deg / 2) - 1), abs(-x1 / (a_deg / 2) - 1))))
    return dict(rows=rows, pass_=all(r["rel_err"] < 0.02 for r in rows))


def b3_gfm(g):
    dt = 1e-3
    thr, win, tau, tp = g["gfm_thr"], g["gfm_win"], g["gfm_tau"], g["gfm_tp"]
    nw = int(tp / dt + 0.5)
    res = {}

    def run(mis_ticks, mis_deg, shaped=None):
        gm, pt, buf, wm = np.zeros(2), np.zeros(2), np.full((4, 400), -1e9), np.zeros(4)
        i = 0
        trips = []
        x50 = -1e9
        for k in range(400):
            c0 = 0.0 if shaped is None else shaped(k)
            m0 = np.radians(mis_deg) if 100 <= k < 100 + mis_ticks else 0.0
            tr, i = s6._gfm_step(gm, pt, buf, i, nw, c0, 0.0, m0, 0.0, True, thr, win, tau, tp, dt, 0.7071, 0.7071, -0.7071,
                                 0.7071, wm)
            x50 = max(x50, max(wm[0], wm[1]))
            trips.append(tr)
        return any(trips), (trips.index(True) - 100 + 1 if any(trips) else None), np.degrees(x50)

    t49, _, _ = run(49, 2.0)
    t50, k50, x50 = run(50, 2.0)
    res["persistence"] = dict(ticks_49_trip=t49, ticks_50_trip=t50, trip_tick=k50, pass_=bool((not t49) and t50 and k50 == 50))
    res["window_min_record"] = dict(x50_deg=round(float(x50), 6), expected_deg=round(2.0 - np.degrees(0.0), 6),
                                    pass_=bool(abs(x50 - 2.0) < 1e-9))
    # rate allowance: shaped command a ramp at 50 deg/s -> model lags; the encoder follows the model plus 1.4 deg offset
    # beyond the allowance: x = 1.4 deg < 1.5 deg -> no trip although |model - encoder| exceeds 1.5 deg by the allowance
    gm, pt, buf, wm = np.zeros(2), np.zeros(2), np.full((4, 400), -1e9), np.zeros(4)
    i = 0
    trip = False
    maxmis = 0.0
    for k in range(300):
        c0 = np.radians(50.0) * k * dt
        gm_next = gm[0] + (c0 - gm[0]) * (dt / tau)
        allow = win * abs(c0 - gm_next) / tau
        m0 = gm_next - (allow + np.radians(1.4))
        tr, i = s6._gfm_step(gm, pt, buf, i, nw, c0, 0.0, m0, 0.0, True, thr, win, tau, tp, dt, 0.7071, 0.7071, -0.7071,
                             0.7071, wm)
        maxmis = max(maxmis, abs(gm[0] - m0))
        trip = trip or tr
    res["rate_allowance"] = dict(max_mismatch_deg=round(float(np.degrees(maxmis)), 4), trip=trip,
                                 pass_=bool((not trip) and np.degrees(maxmis) > 1.5))
    res["pass_"] = all(v["pass_"] for v in res.values() if isinstance(v, dict))
    return res


def bench(g, cmd, jam_at, t_end=5.0):
    """Electronics SIL S6 bench in the sim's own terms: FC command -> tracker + low-pass -> delay -> per-axis 2nd-order
    servo -> jam constraint (servo 1) -> rigid linkage = engine -> AS5048A quantisation -> monitor (_gfm_step)."""
    dt = 1e-3
    n = int(t_end / dt)
    kdel = max(int(round(g["gim_delay"] / dt)), 0)
    buf = np.zeros((kdel + 1, 2))
    vmax, amax = np.radians(g["gim_cmd_rate"]), np.radians(g["gim_cmd_acc"])
    wf, zf = g["gim_lpf_w"], g["gim_lpf_z"]
    wn, zg = g["gim_wn"], g["gim_zeta"]
    rlc, rlv, lf, lfr = np.zeros(2), np.zeros(2), np.zeros(2), np.zeros(2)
    dsv, dsr = np.zeros(2), np.zeros(2)
    gm, pt, gb, wm = np.zeros(2), np.zeros(2), np.full((4, 400), -1e9), np.zeros(4)
    nw = int(g["gfm_tp"] / dt + 0.5)
    gi = 0
    out = np.zeros(5)
    jam = False
    sj = 0.0
    t_trip = None
    q = g["gim_enc_q"]
    g1x, g1y = np.sin(g["act_az1"]), -np.cos(g["act_az1"])
    g2x, g2y = np.sin(g["act_az2"]), -np.cos(g["act_az2"])
    maxmis = 0.0
    for k in range(n):
        t = k * dt
        u = cmd(t)
        for a in range(2):
            e_ = u[a] - rlc[a]
            vd = min(np.sqrt(2 * amax * abs(e_)), abs(e_) / dt, vmax) * np.sign(e_)
            dv = np.clip(vd - rlv[a], -amax * dt, amax * dt)
            rlv[a] += dv
            rlc[a] += rlv[a] * dt
            lfr[a] += (wf * wf * (rlc[a] - lf[a]) - 2 * zf * wf * lfr[a]) * dt
            lf[a] += lfr[a] * dt
        shaped = lf.copy()
        meas = np.round(dsv / q) * q if q > 0 else dsv.copy()
        tr, gi = s6._gfm_step(gm, pt, gb, gi, nw, shaped[0], shaped[1], meas[0], meas[1], True, g["gfm_thr"], g["gfm_win"],
                              g["gfm_tau"], g["gfm_tp"], dt, g1x, g1y, g2x, g2y, wm)
        maxmis = max(maxmis, abs(gm[0] - meas[0]), abs(gm[1] - meas[1]))
        if tr and t_trip is None:
            t_trip = t
        buf = np.roll(buf, 1, axis=0)
        buf[0] = shaped
        uc = buf[kdel]
        if jam_at is not None and (not jam) and t >= jam_at:
            jam = True
            sj = s6._act_dz(dsv[0], dsv[1], g["act_az1"], g["act_re"], g["act_zb"])
        for a in range(2):
            dsr[a] += (wn * wn * (uc[a] - dsv[a]) - 2 * zg * wn * dsr[a]) * dt
            dsv[a] += dsr[a] * dt
        if jam:
            s6._jam_proj(dsv[0], dsv[1], dsr[0], dsr[1], sj, g["act_az1"], g["act_az2"], g["act_re"], g["act_zb"], out)
            dsv[:] = out[:2]
            dsr[:] = out[2:4]
    return dict(trip=t_trip is not None, t_trip=t_trip, latency_ms=(None if (t_trip is None or jam_at is None)
                                                                     else round(1e3 * (t_trip - jam_at), 1)),
                max_mismatch_deg=round(float(np.degrees(maxmis)), 3))


def b4_sil(g):
    D2R = np.pi / 180

    def sine(A):
        return lambda t: (A * D2R * np.sin(2 * np.pi * (t - 2.0)) if t > 2.0 else 0.0, 0.0)

    def slews(t):
        if 3.0 <= t < 3.6:
            return ((7.0 if (t - 3.0) % 0.3 < 0.15 else -7.0) * D2R, 0.0)
        if 3.6 <= t < 4.0:
            return (0.0, (7.0 if (t - 3.6) % 0.2 < 0.1 else -7.0) * D2R)
        if 4.0 <= t < 4.4:
            d = (7.0 if (t - 4.0) % 0.2 < 0.1 else -7.0) * D2R
            return (d * np.cos(65 * D2R), d * np.sin(65 * D2R))
        return (0.0, 0.0)
    cases = [("gimbal_jam_moving_cmd", sine(2.0), 3.0, False, None),
             ("gimbal_jam_moving_cmd_4deg", sine(4.0), 3.0, True, 175.0),
             ("gimbal_jam_at_commanded_angle_undetectable", lambda t: (0.0, 0.0), 3.0, False, None),
             ("gimbal_full_slews_no_false_fault", slews, None, False, None),
             ("gimbal_jam_during_full_slews", slews, 3.3, True, 79.0)]
    rows = {}
    for nm, c, ja, want, sil_ms in cases:
        r = bench(g, c, ja)
        r.update(sil_expect_trip=want, sil_latency_ms=sil_ms, class_ok=bool(r["trip"] == want))
        rows[nm] = r
    return dict(sil_log=dict(path=SIL_LOG, sha256_16=sha16(SIL_LOG)), cases=rows, pass_=all(r["class_ok"] for r in rows.values()))


def fly_one(base, st, ex, n, nrec=4):
    return B11.fly_case(base, st, "G73", "", ex, n, nrec)


def b5_flights(g):
    ri = {k: i for i, k in enumerate(s6.RES_NAMES)}
    ci = {k: i for i, k in enumerate(s6.REC_NAMES)}
    n = 4
    r0, rec0 = B11.fly_case("A1_none", "liq", "G73", "", {}, n, n)
    rj, recj = B11.fly_case("A1_none", "liq", "G73", "", dict(jam_on=1, jam_srv=1, jam_ph=3, jam_t=1.0, gfm_on=1), n, n)
    chk = []
    for i in range(n):
        t0 = rj[i, ri["jam_t0"]]
        X, Y = rec0[i], recj[i]
        tX, tY = X[:, ci["t"]], Y[:, ci["t"]]
        pre = tY < t0 - 1e-9
        npre = int(pre.sum())
        same_pre = bool(np.array_equal(X[:npre], Y[:npre], equal_nan=True))
        post = tY > t0 + 1e-9
        a, b = np.radians(Y[post, ci["dsx"]]), np.radians(Y[post, ci["dsy"]])
        sj = s6._act_dz(np.radians(rj[i, ri["jam_a0"]]), np.radians(rj[i, ri["jam_b0"]]), g["act_az1"], g["act_re"], g["act_zb"])
        dzs = np.array([s6._act_dz(x, y, g["act_az1"], g["act_re"], g["act_zb"]) for x, y in zip(a, b)])
        dev = float(np.max(np.abs(dzs - sj))) if len(dzs) else None
        chk.append(dict(run=i, jam_t0=float(t0), jam_ph0=float(rj[i, ri["jam_ph0"]]), records_before_onset=npre,
                        identical_before_onset=same_pre, records_after_onset=int(post.sum()), jam_coord_max_dev_m=dev,
                        jam_res=float(rj[i, ri["jam_res"]]), gfm_t1=float(rj[i, ri["gfm_t1"]]), ok_ref=float(r0[i, 0]),
                        landed_ok_jam=bool(R.success(dict(zip(s6.RES_NAMES, rj[i])))),
                        ok=bool(same_pre and npre > 0 and dev is not None and dev < 1e-9 and rj[i, ri["jam_res"]] < 1e-12)))
    # forced abort path
    ra, reca = B11.fly_case("A1_none", "liq", "G73", "", dict(gfm_on=2, gfm_thr=1e-5), 2, 2)
    ab = []
    for i in range(2):
        tab = ra[i, ri["gfm_tab"]]
        Y = reca[i]
        t = Y[:, ci["t"]]
        k = np.where(t >= tab + 0.5)[0]
        Fa = float(Y[k[0], ci["F"]]) if len(k) else None
        ab.append(dict(run=i, gfm_abt=float(ra[i, ri["gfm_abt"]]), gfm_tab=float(tab), gfm_ph1=float(ra[i, ri["gfm_ph1"]]),
                       starts=float(ra[i, ri["starts"]]), F_0p5s_after=Fa, h_max=float(ra[i, ri["h_max"]]),
                       ok=bool(ra[i, ri["gfm_abt"]] > 0.5 and ra[i, ri["gfm_ph1"]] == 1.0 and ra[i, ri["starts"]] == 1.0
                               and Fa is not None and Fa < 1.0)))
    return dict(jam_record=chk, forced_abort=ab, pass_=all(c["ok"] for c in chk) and all(c["ok"] for c in ab))


def part_func(pout):
    assert "jam_on" in s6.PAR_NAMES, "functional part needs the v2.13-dev tree"
    g = geometry()
    out = dict(version=VERSION, sim=s6.SIM6_VERSION, sim6_sha16=sha16(s6.__file__), run6_sha16=sha16(R.__file__),
               geometry=g, checks={})
    for nm, fn in (("B1_jam_projection", b1_proj), ("B2_small_angle", b2_small), ("B3_monitor_unit", b3_gfm),
                   ("B4_SIL_S6_bench", b4_sil), ("B5_flights", b5_flights)):
        r = fn(g)
        out["checks"][nm] = r
        print(nm, "PASS" if r["pass_"] else "FAIL", flush=True)
    out["all_pass"] = all(v["pass_"] for v in out["checks"].values())
    json.dump(out, open(pout, "w"), indent=1, default=float)
    print("ALL PASS" if out["all_pass"] else "FAILURES", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "fly":
        part_fly()
    elif sys.argv[1] == "compare":
        part_compare(sys.argv[2], sys.argv[3], sys.argv[4])
    elif sys.argv[1] == "func":
        part_func(sys.argv[2])
