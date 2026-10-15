"""m2_abort_tailoff v1.1 (2026-10-13; v1.1: valve-to-seat line volume from Combustion low_inlet_check_v2p3, relayed by
the lead 2026-10-13 - Mechanical re-measures it on CAD v3.4): thrust tail-off of an ABORT shutdown, as the lead decided on 2026-10-13 (review RC-01):
every abort de-energises the NC isolation valve at once (spring closes it) and closes the pintle in parallel. Normal shutdowns
(MECO, touchdown cut) keep the pintle-first sequence and are unchanged.

GNC model (bracket, DERIVED): the reduced lift-ramp shutdown model of sim6 toff_model 1 (gncsim.tailoff, fitted by GNC to
Combustion's grain_q1d v2 shutdown runs) gives the PINTLE-ONLY tail-off; that is the UPPER bound of the abort tail-off
impulse, because closing the valve upstream can only cut the injector flow earlier. The LOWER bound assumes the injector
flow stops when the valve reaches closed (zero valve-to-pintle line volume, no line blowdown); after that the thrust decays
with the fitted chamber lag only. The line volume between the valve and the pintle seat, its vapour fraction and its
blowdown through the closing pintle are NOT known to GNC (Combustion / Mechanical item), so the true abort tail-off lies
between the two.
Valve close times are read from the interfaces: electronics.json actuators.main_valve.close_time_s (ASSUMED requirement on
the spring design) and combustion.json valves_and_actuators.isolation_valve.close_time_max_s (DERIVED).
Levels: 100 % (abort in the ascent), 72 % (abort after the pre-MECO throttle-down), 20 % / 12.5 % (abort near the floor).
Env: GNC_IFACE, GNC_ACT_RATE, GNC_AB_OUT (default out/abort_tailoff). Output: <out>/abort_tailoff.json"""
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, tailoff  # noqa: E402

OUT = os.environ.get("GNC_AB_OUT", "/home/claude/work/space/out/abort_tailoff")
LINE = os.environ.get("GNC_AB_LINE", "/home/claude/work/shared-fallback/engine/02-combustion/data/v2/low_inlet_check_v2p3.json")
from gncsim.propulsion import _bilin  # noqa: E402


def ox_after(F0, tl, tf, vs, lag_a, lag_c, l_cut, t_vc, tab, dt=1e-3):
    """N2O mass [kg] the pintle-only shutdown from F0 passes after the valve close time t_vc (published map flow at the
    delivered thrust, initial port)."""
    xl = np.array([l_cut] + list(tl)); xf = np.array([0.0] + list(tf))
    l_r = float(np.interp(F0, xf, xl)); l_a = l_r; Fa = F0; t = 0.0; m = 0.0
    for _ in range(5000):
        l_r = max(0.0, l_r - vs * dt)
        l_a += (l_r - l_a) * dt / max(lag_a, dt)
        Fq = float(np.interp(l_a, xl, xf))
        Fa += (Fq - Fa) * dt / max(lag_c, dt)
        t += dt
        if Fa < 0.5:
            Fa = 0.0
        if t > t_vc and Fa > 0.0:
            m += _bilin(tab["Fg"], tab["Dg"], tab["mox"], Fa, tab["Dg"][0]) * dt
        if Fa == 0.0:
            break
    return m


def sim_valve(F0, tl, tf, vs, lag_a, lag_c, l_cut, t_vc, dt=1e-3):
    """Lift-ramp shutdown with the injector flow cut at the valve close time t_vc (lower bound)."""
    xl = np.array([l_cut] + list(tl)); xf = np.array([0.0] + list(tf))
    l_r = float(np.interp(F0, xf, xl)); l_a = l_r; Fa = F0; imp = 0.0; t = 0.0; t10 = None
    for _ in range(5000):
        l_r = max(0.0, l_r - vs * dt)
        l_a += (l_r - l_a) * dt / max(lag_a, dt)
        Fq = float(np.interp(l_a, xl, xf)) if t < t_vc else 0.0
        Fa += (Fq - Fa) * dt / max(lag_c, dt)
        t += dt
        if Fa < 0.5:
            Fa = 0.0
        imp += Fa * dt
        if t10 is None and Fa < 0.1 * F0:
            t10 = t
        if Fa == 0.0:
            break
    return t10, imp


def main():
    os.makedirs(OUT, exist_ok=True)
    src = R.sources()
    comb, el = src["comb"], src["el"]
    chk, sha, path = tailoff.load_checks(comb)
    fs = float(R.DEF["pintle_full_stroke"])
    cal = tailoff.calibration(sha, fs)
    tl, tf = cal["lift_mm"], cal["thrust_N"]
    vs, la, lc, lcut = cal["speed_mm_s"], cal["lag_a_s"], cal["lag_c_s"], cal["l_cut_mm"]
    tvc_el = el["actuators"]["main_valve"]["close_time_s"]
    tvc_cb = comb["valves_and_actuators"]["isolation_valve"]["close_time_max_s"]
    Fmax = max(tf)
    import hashlib
    lj = json.load(open(LINE))
    lv = lj["3_volumes"]["valve_to_seat_cm3"]
    tl_ = lj["3_volumes"]["trapped_liquid"]
    line = dict(file=LINE, sha256=hashlib.sha256(open(LINE, "rb").read()).hexdigest(), version=lj.get("version"),
                volume_cm3={"valve_at_coil_fixed_end": lv["valve_at_coil_fixed_end"], "valve_at_zone_top": lv["valve_at_zone_top"]},
                volume_tag=lv.get("tag"), liquid_mass_g={T: {"valve_at_coil": v["mass_g_valve_at_coil"], "valve_at_top": v["mass_g_valve_at_top"]}
                                                         for T, v in tl_.items() if isinstance(v, dict) and "mass_g_valve_at_coil" in v},
                relay="lead 2026-10-13: 21.4 cm3 (valve at the coil fixed end); Mechanical re-measures it on CAD v3.4")
    tab = src["tab"]
    m_line_min = min(v["valve_at_coil"] for v in line["liquid_mass_g"].values()) / 1e3
    rows = []
    for frac in (1.0, 0.72, 0.20, 0.125):
        F0 = frac * Fmax
        t10p, impp = tailoff.simulate(F0, tl, tf, vs, la, lc, lcut)
        r = dict(level_frac_Fmax=frac, F0_N=F0, pintle_only=dict(t10_s=t10p, impulse_Ns=impp, tag="DERIVED upper bound"))
        for lab, tv in (("valve_electronics", tvc_el), ("valve_combustion_max", tvc_cb)):
            t10v, impv = sim_valve(F0, tl, tf, vs, la, lc, lcut, float(tv["v"]))
            r[lab] = dict(valve_close_s=tv["v"], valve_close_tag=tv["tag"], t10_s=t10v, impulse_Ns=impv,
                          tag="DERIVED lower bound (flow cut at valve closed; no line volume)")
        for lab, tv in (("valve_electronics", tvc_el), ("valve_combustion_max", tvc_cb)):
            m_after = ox_after(F0, tl, tf, vs, la, lc, lcut, float(tv["v"]), tab)
            r[lab]["n2o_after_valve_closed_g"] = 1e3 * m_after
            r[lab]["line_liquid_min_g"] = 1e3 * m_line_min
            r[lab]["line_can_feed_rest_of_closure"] = bool(m_line_min >= m_after)
        r["abort_tailoff_bound"] = ("pintle-only (upper bound reached: the valve-to-seat line holds more liquid N2O than the "
                                    "closing pintle passes after the valve shuts)") if all(
            r[k]["line_can_feed_rest_of_closure"] for k in ("valve_electronics", "valve_combustion_max")) else "between the bounds"
        rows.append(r)
        print(f"{100 * frac:5.1f} % F0 {F0:6.1f} N: pintle-only t10 {t10p:.3f} s I {impp:6.2f} N s | valve {tvc_el['v']} s: "
              f"t10 {r['valve_electronics']['t10_s']:.3f} s I {r['valve_electronics']['impulse_Ns']:6.2f} N s | valve "
              f"{tvc_cb['v']} s: I {r['valve_combustion_max']['impulse_Ns']:6.2f} N s", flush=True)
    out = dict(version="m2_abort_tailoff v1.1", date="2026-10-13", iface=R.IFACE,
               interfaces={k: (src[k] or {}).get("version") for k in ("comb", "el")}, speed_check_file=path,
               speed_check_sha256=sha, full_stroke_s=fs, fit=dict(lag_a_s=la, lag_c_s=lc, l_cut_mm=lcut, speed_mm_s=vs),
               rows=rows,
               law=("ABORT (any cause, any phase): the ECU de-energises the NC valve latch at once (spring closes the ball valve) "
                    "and commands the pintle closed at the drive speed in parallel; torch solenoids closed; no in-flight relight "
                    "retry (lead decision 2026-10-13). NORMAL shutdowns (MECO after the 72 % throttle-down, touchdown cut) "
                    "keep the pintle-first sequence"),
               line_volume=line,
               finding=("with the 21.4 cm3 valve-to-seat line (16-18 g of liquid N2O at 15-25 C) the closing pintle is fed from "
                        "the line after the valve shuts at every level checked: the abort tail-off equals the pintle-only one "
                        "(the parallel valve closure does not shorten it); the valve matters for what follows (no further "
                        "tank flow, trapped-liquid relief)"),
               unknowns=["vapour fraction of the line at the abort instant and its blowdown through the closing pintle (a "
                         "vapour-filled line feeds less: the lower bound then applies in part)",
                         "valve close time: ASSUMED requirement (electronics.json) / DERIVED maximum (combustion.json); spring "
                         "not yet sized", "chamber pressure decay of an abort from a non-steady state (start transient)"])
    with open(os.path.join(OUT, "abort_tailoff.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "abort_tailoff.json"))


if __name__ == "__main__":
    main()
