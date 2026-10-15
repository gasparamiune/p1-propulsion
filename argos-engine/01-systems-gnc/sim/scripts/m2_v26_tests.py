"""m2_v26_tests v1.3: sim6/run6 v2.6 verification tests (2026-10-12). Each test prints PASS/FAIL with its numbers; exit code = failures.
  T1 notch biquad (sim6 code path, python port): (a) code path = exact bilinear transform of the continuous RBJ
     peaking-EQ prototype pre-warped at f0 (< 0.01 dB at every test frequency up to 0.5 x Nyquist), unity at DC, depth
     at f0; (b) deviation from the un-warped continuous notch < 1 dB up to 100 Hz (0.2 x Nyquist; loop crossover and
     the 12-35 Hz structural band lie below), the value at 250 Hz printed for information (bilinear warping).
     v1.2 applied (b) up to 250 Hz and FAILED the Q 0.5 / -30 dB stress case (1.06 dB at 250 Hz); kept as evidence in
     v26_tests_v1.2_first_run.json. The flight setting (Q 1, -12 dB) deviates 0.04 dB up to 250 Hz.
  T2 tail-off reduced model vs Combustion actuator_rate_check_v2 (0.25 s stroke): t10 within 3 ms, impulse within 8 %
  T3 in-sim tail-off impulse (nominal A-D flight, toff_model 1) equals gncsim.tailoff.simulate from the MECO thrust
  T4 MECO rule (meco_td 0.72): MECO thrust <= 0.75 F_max, reduced-model t10 <= 0.100 s (ENG-05)
  T5 relight rule: floor 12.5 % with relight_start 0.20 -> start command 100 N held to 90 %, t90 recorded
  T6 notch in the 6-DOF (v1.3): A-D flight with wind 5 m/s + gusts and sensor noise (seed 7), 1 kHz record of the
     post-notch engine command over the powered ascent 0.5-2.5 s: notch 20 Hz Q 0.7 -20 dB lowers the 17-23 Hz band
     power by >= 6 dB, changes the 0-5 Hz band power by < 3 dB, both flights land. v1.2 flew without wind or noise:
     the gimbal never moved (0.000 deg both), the test could not see the notch and FAILED (vacuous; kept as evidence)
  T7 run6 v2.6 MC options: FEA stiffness range keeps the random numbers, tracking notch centre, wet inertia override
  T8 start-delay shift t_ign_add: applied once to the nominal (sizing) flight and once to each dispersed run; the nominal
     relight t90 moves by the shift when the planning value moves with it (v1.1)
  T9 reference-governor ratchet att_ref_mode (v1.2): default off; a nominal A-D landing with the 40 deg/s governor is kept
     with the ratchet on; regression example A-F draw 1 (seed 101, full v2.6 FSW, NC-closed relight timeline): the
     tumbling vehicle is driven back toward its attitude at governor start without the ratchet (fails) and lands with it
     (v1.3: the example is pinned to combustion v2.2 / mechanical v1 (iface_v3b); on other bases it is printed as INFO:
     on mechanical v2 draw 1 lands without the ratchet, so it is no longer a discriminating example; the first v3c
     run that judged it is kept as v26_tests_v1.3_first_run_T9pinned_fail.json)
Env: GNC_IFACE (interface set with combustion.json >= v2.2), GNC_ACT_RATE (optional), GNC_OUT (default out/v26_checks;\nwrites v26_tests.json)."""
import os
import sys
import numpy as np
import control as ct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, sim6 as s6, tailoff  # noqa: E402

FAIL = []
LOG = []
T9_BASIS = ("v2.2", "v1")   # v1.3: (combustion.json, mechanical.json) versions on which the T9 regression example was found


def check(name, ok, msg):
    print(f"{'PASS' if ok else 'FAIL'} {name}: {msg}", flush=True)
    LOG.append(dict(test=name, result="PASS" if ok else "FAIL", detail=msg))
    if not ok:
        FAIL.append(name)


def info(name, msg):
    """v1.3: a basis-specific example run on another basis is reported, not judged."""
    print(f"INFO {name}: {msg}", flush=True)
    LOG.append(dict(test=name, result="INFO", detail=msg))


def biquad(f0, q, depth, dt):
    w0 = 2.0 * np.pi * f0 * dt
    A = 10.0 ** (depth / 40.0)
    al = np.sin(w0) / (2.0 * q); c = np.cos(w0)
    a0 = 1.0 + al / A
    return (1.0 + al * A) / a0, -2.0 * c / a0, (1.0 - al * A) / a0, -2.0 * c / a0, (1.0 - al / A) / a0


def t1():
    dt = 1e-3
    for f0, q, dep in ((20.0, 1.0, -12.0), (15.0, 0.7, -20.0), (25.0, 0.5, -30.0)):
        b0, b1, b2, a1, a2 = biquad(f0, q, dep, dt)
        f = np.array([0.0, 1.0, 5.0, 0.5 * f0, f0, 2.0 * f0, 100.0, 250.0])
        z = np.exp(1j * 2 * np.pi * f * dt)
        Hd = (b0 + b1 / z + b2 / z ** 2) / (1 + a1 / z + a2 / z ** 2)
        w0 = 2 * np.pi * f0; A = 10 ** (dep / 40)

        def Hc(fr):
            s = 1j * 2 * np.pi * fr
            return (s * s + A * w0 / q * s + w0 * w0) / (s * s + w0 / (A * q) * s + w0 * w0)
        fw = np.tan(np.pi * f * dt) / np.tan(np.pi * f0 * dt) * f0          # bilinear frequency map, pre-warped at f0
        dd = 20 * np.log10(np.abs(Hd)); dc = 20 * np.log10(np.abs(Hc(f))); dw = 20 * np.log10(np.abs(Hc(fw)))
        ok = abs(dd[0]) < 1e-6 and abs(dd[4] - dep) < 0.05 and np.max(np.abs(dd - dw)) < 0.01
        check(f"T1a notch code path f0 {f0} Q {q} {dep} dB", ok, f"DC {dd[0]:.2e} dB, at f0 {dd[4]:.2f} dB, max |disc - "
              f"bilinear(prototype)| {np.max(np.abs(dd - dw)):.1e} dB")
        b = f <= 100.0
        check(f"T1b notch vs continuous f0 {f0} Q {q} {dep} dB", np.max(np.abs(dd - dc)[b]) < 1.0,
              f"max |disc - cont| {np.max(np.abs(dd - dc)[b]):.2f} dB up to 100 Hz; {abs(dd[-1] - dc[-1]):.2f} dB at 250 Hz "
              f"(bilinear warping, information)")
        # time-domain: the sim6 update order on a sine at f0 settles to the depth
        x = np.sin(2 * np.pi * f0 * np.arange(0, 2.0, dt))
        z1 = z2 = 0.0; y = np.zeros_like(x)
        for i, xi in enumerate(x):
            yi = b0 * xi + z1
            z1 = b1 * xi - a1 * yi + z2; z2 = b2 * xi - a2 * yi
            y[i] = yi
        amp = np.max(np.abs(y[-int(0.5 / dt):]))
        check(f"T1 notch time-domain f0 {f0}", abs(20 * np.log10(amp) - dep) < 0.3, f"steady amplitude {20 * np.log10(amp):.2f} dB vs {dep}")


def t2():
    comb = R.sources()["comb"]
    chk, sha, path = tailoff.load_checks(comb)
    tl, tf, vs, tg = tailoff.table(chk, 0.25)
    cal = tailoff.calibration(sha, 0.25)
    for F0, t10c, impc in tg:
        t10, imp = tailoff.simulate(F0, tl, tf, vs, cal["lag_a_s"], cal["lag_c_s"], cal["l_cut_mm"])
        check(f"T2 tail-off from {F0:.0f} N", abs(t10 - t10c) <= 0.003 and abs(imp / impc - 1) <= 0.08,
              f"t10 {t10:.3f} vs {t10c:.3f} s, impulse {imp:.2f} vs {impc:.2f} N s ({100 * (imp / impc - 1):+.1f} %)")
    return tl, tf, vs, cal


def nominal(**ov):
    cfg = R.cfg_of(**dict(dict(profile="A-D", fins=True, floor=0.20, rcs=False, m_n2o=2.00), **ov))
    res, rec, info = R.fly(dict(cfg, noise=False, wind=0.0, gust=False), nrec=10)
    return res


def t3_t4(tl, tf, vs, cal):
    r = nominal(toff_model=1)
    t10, imp = tailoff.simulate(float(r["F_meco_cmd"]), tl, tf, vs, cal["lag_a_s"], cal["lag_c_s"], cal["l_cut_mm"])
    check("T3 in-sim tail-off impulse", abs(float(r["tailoff_imp"]) / imp - 1) < 0.005,
          f"sim {float(r['tailoff_imp']):.3f} vs reference {imp:.3f} N s from F_meco {float(r['F_meco_cmd']):.1f} N")
    r = nominal(toff_model=1, meco_td=0.72)
    fm = float(r["F_meco_cmd"])
    t10, imp = tailoff.simulate(fm, tl, tf, vs, cal["lag_a_s"], cal["lag_c_s"], cal["l_cut_mm"])
    check("T4 MECO rule", fm <= 0.75 * 500.0 and t10 <= 0.100 and R.success(r),
          f"F_meco {fm:.1f} N ({fm / 5:.1f} %), t10 {t10:.3f} s, apogee {float(r['h_max']):.1f} m, landed {R.success(r)}")


def t5():
    r = nominal(floor=0.125, toff_model=1, meco_td=0.72, relight_start=0.20)
    check("T5 relight rule", abs(float(r["F_start_cmd"]) - 100.0) < 1e-6 and float(r["t90_relight"]) > 0 and R.success(r),
          f"start command {float(r['F_start_cmd']):.1f} N, t90 {float(r['t90_relight']):.3f} s, landed {R.success(r)}")
    r0 = nominal(floor=0.125, toff_model=1, meco_td=0.72)
    check("T5 floor start", abs(float(r0["F_start_cmd"]) - 62.5) < 1e-6, f"start command {float(r0['F_start_cmd']):.1f} N")


def t6():
    from scipy.signal import welch
    kw = dict(wind=5.0, gust=True, wind_dir=0.7, noise=True, seed=7, rec_dt=1e-3)
    out = []
    for nt in (dict(), dict(gim_notch_f=20.0, gim_notch_q=0.7, gim_notch_db=-20.0)):
        cfg = R.cfg_of(**dict(dict(profile="A-D", fins=True, floor=0.20, rcs=False, m_n2o=2.00), **nt))
        res, rec, info = R.fly(dict(cfg, **kw), nrec=60000)
        t = rec[:, 0]
        w = (t >= 0.5) & (t <= 2.5)
        pw = {}
        for col in ("dcx", "dcy"):
            fr, P = welch(rec[w, s6.REC_NAMES.index(col)], fs=1000.0, nperseg=512)
            pw[col] = (P[(fr >= 17) & (fr <= 23)].sum(), P[fr <= 5].sum())
        out.append((res, pw))
    (r0, p0), (r1, p1) = out
    hb = {c: 10 * np.log10(p1[c][0] / p0[c][0]) for c in p0}
    lb = {c: 10 * np.log10(p1[c][1] / p0[c][1]) for c in p0}
    ok = R.success(r0) and R.success(r1) and max(hb.values()) <= -6.0 and max(abs(v) for v in lb.values()) < 3.0
    check("T6 notch in 6-DOF", ok,
          f"landed {R.success(r0)}/{R.success(r1)} (off/on); 17-23 Hz command band power x {hb['dcx']:+.1f} / y {hb['dcy']:+.1f} dB; "
          f"0-5 Hz x {lb['dcx']:+.2f} / y {lb['dcy']:+.2f} dB; max gimbal {float(r0['max_gim']):.3f} / {float(r1['max_gim']):.3f} deg, "
          f"td_vh {float(r0['td_vh']):.3f} / {float(r1['td_vh']):.3f} m/s")


def t7():
    """run6 v2.6 MC options: FEA stiffness range (same random numbers), tracking notch, wet engine inertia override."""
    base = dict(profile="A-D", fins=True, floor=0.20, rcs=False, m_n2o=2.0, act_model=1, servo_V=6.6, act_n=4.8, act_Jint=1.6e-3)
    c0 = R.cfg_of(**base)
    c1 = R.cfg_of(**dict(base, rock_K_eng=(729.0, 1515.0), gim_notch_track=1.0, gim_notch_mis_w=0.15, eng_I_pivot_wet=0.052))
    D0 = R.draw(np.random.default_rng(101), 20, c0)
    D1 = R.draw(np.random.default_rng(101), 20, c1)
    mech = R.sources()["mech"]
    n_m = mech["tvc_actuation"]["gear_ratio_n"]["v"]; kax = mech["tvc_actuation"]["axis_stiffness_Nm_per_rad"]["v"]
    fk = (4.8 / n_m) ** 2
    du = max(abs((a["rock_K"] - kax[0]) / (kax[1] - kax[0]) - (b["rock_K"] - 729.0 / fk) / ((1515.0 - 729.0) / fk))
             for a, b in zip(D0, D1))
    same = all(str(a[k]) == str(b[k]) for a, b in zip(D0, D1) for k in a if k != "rock_K")
    mis = [b["notch_mis"] for b in D1]
    check("T7 FEA stiffness draw", du < 1e-12 and same and min(mis) >= 0.85 and max(mis) <= 1.15,
          f"max |u_old - u_new| {du:.1e}, other draws identical {same}, mistune {min(mis):.3f}-{max(mis):.3f}")
    dd = {k: v for k, v in D1[0].items() if not k.startswith("_")}
    par, apar, comp, mp, tab, info = R.build(c1, dd)
    o = np.zeros(8)
    s6.massprops(mp, 0.0, 0.0, 800.0, R.sources()["comb"]["gas_path"]["grain"]["mass_kg"]["v"], o)
    Iw = o[6] + o[4] * (mp[15] - o[5]) ** 2
    o2 = np.zeros(8)
    s6.massprops(mp, 0.3, 0.0, par[s6.P_rho_l_nom], R.sources()["comb"]["gas_path"]["grain"]["mass_kg"]["v"] * 0.75, o2)
    Il = o2[6] + o2[4] * (mp[15] - o2[5]) ** 2
    f_ref = dd["notch_mis"] * np.sqrt(par[s6.P_rock_K] / (Il + par[s6.P_act_Jint])) / (2 * np.pi)
    p0, a0, c0_, mp0, t0_, i0 = R.build(c0, {k: v for k, v in D0[0].items() if not k.startswith("_")})
    check("T7 inertia override + tracking notch", abs(Iw - 0.052) < 1e-9 and abs(par[s6.P_gim_notch_f] - f_ref) < 1e-9
          and abs(info["m_liftoff"] - i0["m_liftoff"]) < 1e-12 and abs(info["zcg0"] - i0["zcg0"]) < 1e-12,
          f"wet I_pivot {Iw:.6f} kg m2, notch {par[s6.P_gim_notch_f]:.3f} Hz vs {f_ref:.3f} Hz, liftoff mass/CG unchanged")


def t8():
    """t_ign_add (NC-closed relight timeline): shifts the nominal start delay and each MC draw exactly once."""
    base = dict(profile="A-D", fins=True, floor=0.20, rcs=False, m_n2o=2.0)
    c0 = R.cfg_of(**base)
    c1 = R.cfg_of(**dict(base, t_ign_add=0.8, t_ign_est=1.4))
    p0 = R.build(c0)[0]
    p1 = R.build(c1)[0]
    D = R.draw(np.random.default_rng(101), 3, c1)
    cr, dd = R.run_cfg(c1, D[0])
    pr_ = R.build(cr, dd)[0]
    ok1 = abs(p1[s6.P_t_ign] - p0[s6.P_t_ign] - 0.8) < 1e-12 and abs(pr_[s6.P_t_ign] - (D[0]["_t_ign"] + 0.8)) < 1e-12
    check("T8 start-delay shift applied once", ok1 and abs(p1[s6.P_t_ign_est] - 1.4) < 1e-12,
          f"nominal {p0[s6.P_t_ign]:.3f} -> {p1[s6.P_t_ign]:.3f} s, run 0 draw {D[0]['_t_ign']:.3f} -> {pr_[s6.P_t_ign]:.3f} s, "
          f"planning value {p1[s6.P_t_ign_est]:.2f} s")
    r0 = nominal()
    r1 = nominal(t_ign_add=0.8, t_ign_est=1.4)
    d90 = float(r1["t90_relight"]) - float(r0["t90_relight"])
    check("T8 nominal relight with the shift planned", R.success(r0) and R.success(r1) and abs(d90 - 0.8) < 0.02,
          f"t90 {float(r0['t90_relight']):.3f} -> {float(r1['t90_relight']):.3f} s (shift {d90:.3f} s), relight command "
          f"h {float(r0['h_ign']):.1f} -> {float(r1['h_ign']):.1f} m, landed {R.success(r0)}/{R.success(r1)}")


def t9():
    """Reference-governor ratchet (att_ref_mode 1)."""
    import m2_meco_mc as MM
    p0 = R.build(R.cfg_of(profile="A-D", fins=True, floor=0.20, rcs=False, m_n2o=2.0))[0]
    check("T9 ratchet default off", p0[s6.P_att_ref_mode] == 0.0, f"att_ref_mode default {p0[s6.P_att_ref_mode]:g}")
    fsw = dict(gim_cmd_acc=2000.0, att_ref_rate=40.0, toff_model=1, meco_td=0.72, relight_start=0.20)
    r0 = nominal(**fsw)
    r1 = nominal(**fsw, att_ref_mode=1)
    check("T9 nominal A-D with the ratchet", R.success(r0) and R.success(r1),
          f"landed {R.success(r0)}/{R.success(r1)} (off/on), td_vh {float(r0['td_vh']):.3f}/{float(r1['td_vh']):.3f} m/s, "
          f"max tilt landing {float(r0['max_tilt_land']):.2f}/{float(r1['max_tilt_land']):.2f} deg, prop "
          f"{float(r0['prop_used']):.4f}/{float(r1['prop_used']):.4f} kg")
    over = dict(MM.CASES["mr_AF_fix_td72_nc"][0]); m = over.pop("m_fixed")
    out = []
    for mode in (0, 1):
        cfg = R.cfg_of(**dict(over, m_n2o=m, att_ref_mode=mode))
        D = R.draw(np.random.default_rng(101), 2, cfg)
        res = R.run_one(cfg, D[1])
        out.append(res)
    msg = (f"without ratchet: landed-ok {R.success(out[0])}, td_vh {float(out[0]['td_vh']):.2f} m/s, max tilt landing "
           f"{float(out[0]['max_tilt_land']):.1f} deg; with ratchet: landed-ok {R.success(out[1])}, td_vh "
           f"{float(out[1]['td_vh']):.2f} m/s, max tilt landing {float(out[1]['max_tilt_land']):.1f} deg")
    src = R.sources()
    basis = (str(src["comb"].get("version")), str(src["mech"].get("version")))
    if basis == T9_BASIS:
        check("T9 A-F regression example (draw 1)", (not R.success(out[0])) and R.success(out[1]), msg)
    else:   # v1.3: the example was found on combustion v2.2 / mechanical v1 and is not portable to other mass properties
        info("T9 A-F regression example (draw 1)", f"example pinned on combustion {T9_BASIS[0]} / mechanical {T9_BASIS[1]}; "
             f"this basis combustion {basis[0]} / mechanical {basis[1]}: " + msg + " (ratchet effect on this basis: paired "
             "Monte Carlo, propellant_closure_v3.ratchet_effect_mech_v2)")


if __name__ == "__main__":
    t1()
    tab = t2()
    t3_t4(*tab)
    t5()
    t6()
    t7()
    t8()
    t9()
    print(f"{len(FAIL)} failures", FAIL)
    out = os.environ.get("GNC_OUT", "/home/claude/work/space/out/v26_checks")
    os.makedirs(out, exist_ok=True)
    import json
    with open(os.path.join(out, "v26_tests.json"), "w") as f:
        json.dump(dict(version="m2_v26_tests v1.3", sim=s6.SIM6_VERSION, iface=os.environ.get("GNC_IFACE"), n_fail=len(FAIL),
                       failures=FAIL, n_info=sum(1 for x in LOG if x["result"] == "INFO"), checks=LOG), f, indent=1)
    sys.exit(len(FAIL))
