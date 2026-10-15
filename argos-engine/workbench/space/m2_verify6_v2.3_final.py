"""M2 verification of the 6-DOF (sim6 v2.3, RV-1c): conservation checks, time-step convergence, zero-dispersion
landings, comparison with the independent 1-D reference (sim1d v1.2 on the same engine map and mass)
and with the lead's point-mass seed (00-requirements/calc/lift_and_landing_v0.py).

Outputs: OUT/verify6_<SUFFIX>.json and OUT/verify6_*.csv.
Run: nice -n 10 python scripts/m2_verify6.py
"""
import contextlib
import io
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, sim6 as s6, run1d, sim1d, engine_v2  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/m2")
os.makedirs(OUT, exist_ok=True)
SUFFIX = os.environ.get("GNC_SUFFIX", "v2")
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
# lead seed: shared folder, else the fallback hub, else the local verified copy (data/lead_seed/PROVENANCE.txt)
SEED_CANDIDATES = [os.environ.get("GNC_SEED_PY", ""),
                   "/mnt/project-files/engine/00-requirements/calc/lift_and_landing_v0.py",
                   "/home/claude/work/shared-fallback/engine/00-requirements/calc/lift_and_landing_v0.py",
                   os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "lead_seed",
                                "lift_and_landing_v0.py")]


def seed_path():
    for p in SEED_CANDIDATES:
        try:
            if p and os.path.exists(p):
                return p
        except OSError:
            continue
    return None


def qmat(q):
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def torque_free(dt):
    cfg = R.cfg_of(profile="A-D", fins=True, m_n2o=1.45, test_mode=1, w0=(0.5, 0.2, 3.0), dt=dt, tmax=20.0,
                   rec_dt=0.01, noise=False)
    res, rec, info = R.fly(cfg, nrec=2500)
    It, Ir = info["It0"], info["Ir0"]
    H = []
    Ek = []
    qn = []
    for row in rec:
        q = row[[I["q0"], I["q1"], I["q2"], I["q3"]]]
        w = row[[I["wx"], I["wy"], I["wz"]]]
        Hb = np.array([It * w[0], It * w[1], Ir * w[2]])
        H.append(qmat(q) @ Hb)
        Ek.append(0.5 * (It * (w[0] ** 2 + w[1] ** 2) + Ir * w[2] ** 2))
        qn.append(np.linalg.norm(q))
    H = np.array(H)
    H0 = H[0]
    dH = np.linalg.norm(H - H0, axis=1) / np.linalg.norm(H0)
    Ek = np.array(Ek)
    return dict(dt=dt, t_end=float(rec[-1, 0]), H_rel_drift_max=float(dH.max()),
                Ek_rel_drift_max=float(np.abs(Ek / Ek[0] - 1).max()), qnorm_err_max=float(np.abs(np.array(qn) - 1).max()),
                It=It, Ir=Ir, note="torque-free axisymmetric body: |H| and its inertial direction and T are invariants")


def vacuum_ballistic(dt):
    h0, v0 = 100.0, 50.0
    cfg = R.cfg_of(profile="A-D", fins=True, m_n2o=1.45, test_mode=2, h0=h0, v0z=v0, dt=dt, tmax=10.0,
                   rec_dt=0.01, noise=False)
    res, rec, info = R.fly(cfg, nrec=1200)
    t = rec[:, 0]
    z = rec[:, I["z"]]
    vz = rec[:, I["vz"]]
    E = 0.5 * vz ** 2 + R.G0 * z
    z_ex = h0 + v0 * t - 0.5 * R.G0 * t ** 2
    return dict(dt=dt, E_rel_drift_max=float(np.abs(E / E[0] - 1).max()), z_err_max_m=float(np.abs(z - z_ex).max()),
                note="engine off, no aero: specific energy 1/2 v^2 + g h conserved; exact parabola")


def nominal(profile, dt, wind=0.0, fins=True, floor=0.20, m=None):
    cfg = R.cfg_of(profile=profile, fins=fins, floor=floor, noise=False, dt=dt, wind=wind, gust=False)
    if m is None:
        m, _ = R.size_load(cfg)
        m *= 1.15
    cfg = R.cfg_of(profile=profile, fins=fins, floor=floor, noise=False, dt=dt, wind=wind, gust=False, m_n2o=m)
    res, rec, info = R.fly(cfg)
    keep = ["landed", "td_vz", "td_vh", "td_tilt", "td_rate", "td_miss", "td_t", "prop_used", "h_max", "t_meco",
            "v_meco", "h_ign", "v_ign", "burn_time", "max_gim", "max_axial_g", "peak_leg_force", "m_land"]
    out = {k: float(res[k]) for k in keep}
    out.update(profile=profile, dt=dt, wind=wind, m_n2o=m, success=R.success(res), m_liftoff=info["m_liftoff"])
    return out, info, rec


def compare_1d(profile, m_n2o, info):
    """sim1d v1.2 with the 6-DOF's engine model (combustion.json map, relay-corrected by default), the 6-DOF liftoff
    dry mass and the same grain."""
    comb, tab, _relay = R.engine_sources(R.cfg_of())
    run1d._TAB = tab
    gr = comb["gas_path"]["grain"]
    m_fuel0 = gr["mass_kg"]["v"]
    m_dry = info["m_liftoff"] - m_n2o - m_fuel0
    kw = dict(profile=0 if profile.startswith("A") else 1, h_target=300.0 if profile.startswith("A") else 100.0,
              floor=0.20, m_n2o=m_n2o, tank_V=info["tank_V"], m_dry=m_dry, t_ign=0.3)
    if profile == "A-D":
        kw.update(descent="drogue", drogue_CdA=0.5, kd=0.6, t_ign_est=0.6)
    elif profile == "A-F":
        kw.update(t_ign_est=0.6)
    par = run1d.make_par(**kw)
    par[sim1d.I_M_FUEL0] = m_fuel0
    par[sim1d.I_RHOF] = gr["density_kg_m3"]["v"]
    par[sim1d.I_GL] = gr["length_m"]["v"]
    par[sim1d.I_GDO] = gr["outer_diameter_m"]["v"]
    res, rec = run1d.fly(par)
    run1d._TAB = None
    return {k: float(res[k]) for k in ["td_v", "h_max", "prop_used", "h_ign", "v_ign", "burn_time", "m_land"]}


def lead_seed(m_dry, apogee=300.0):
    """Run the lead's point-mass seed function (constant Isp 205 s, T/W 2 constant-thrust relight logic)."""
    import hashlib
    ns = {}
    sp = seed_path()
    src = open(sp).read()
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(src, sp, "exec"), ns)
    mp = 0.5
    r = None
    for _ in range(40):
        r = ns["sim"](m_dry, mp, apogee)
        if r is None:
            mp *= 1.3
            continue
        need = r["total"] * 1.25
        if abs(need - mp) < 1e-3:
            break
        mp = need
    return dict(m_dry=m_dry, prop_loaded=mp, prop_used=r["total"], v_ign=r["v_ign"], h_ign=r["h_ign"],
                h_apo=r["h_apo"], t_total=r["t_total"], m_land=r["m_land"], seed_file=sp,
                seed_sha256=hashlib.sha256(src.encode()).hexdigest())


def main():
    out = dict(version=f"m2_verify6 {SUFFIX}", sim=s6.SIM6_VERSION)
    out["torque_free"] = [torque_free(dt) for dt in (5e-4, 1e-3, 2e-3)]
    out["vacuum_ballistic"] = [vacuum_ballistic(dt) for dt in (5e-4, 1e-3, 2e-3)]
    conv = []
    for prof in ["A-D", "B"]:
        base, info, rec = nominal(prof, 1e-3, fins=(prof != "B"))
        m = base["m_n2o"]
        for dt in (5e-4, 1e-3, 2e-3):
            r, _, _ = nominal(prof, dt, fins=(prof != "B"), m=m)
            conv.append(r)
        for dt in (5e-4, 1e-3, 2e-3):
            r, _, _ = nominal(prof, dt, wind=5.0, fins=(prof != "B"), m=m)
            conv.append(r)
    out["dt_convergence"] = conv
    zero = []
    infos = {}
    for prof, fins in [("A-D", True), ("A-D", False), ("A-F", False), ("B", False)]:
        r, info, rec = nominal(prof, 1e-3, fins=fins)
        r["fins"] = fins
        zero.append(r)
        infos[(prof, fins)] = (r, info)
    out["zero_dispersion"] = zero
    cmp1d = []
    for prof, fins in [("A-D", True), ("A-F", False), ("B", False)]:
        r6, info = infos[(prof, fins)]
        r1 = compare_1d(prof, r6["m_n2o"], info)
        cmp1d.append(dict(profile=prof, sim6=r6, sim1d=r1))
    out["compare_sim1d"] = cmp1d
    # lead seed: the A-F (freefall) flight is the closest analogue of the seed's profile
    r6, info = infos[("A-F", False)]
    m_dry = info["m_liftoff"] - r6["m_n2o"]
    out["compare_lead_seed"] = dict(seed=lead_seed(m_dry), sim6_AF=r6,
                                    note="seed: Isp 205 s constant, Cd 0.6 up / 0.9 down, ignition when the stop distance at "
                                         "T/W 2 equals height, +25 % reserve; sim6: combustion.json v1 map (Isp 130-199 s), "
                                         "component aero, velocity-tracking guidance, 20 % reserve x 1.15")
    with open(os.path.join(OUT, f"verify6_{SUFFIX}.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print(json.dumps({k: out[k] for k in ["torque_free", "vacuum_ballistic"]}, indent=1, default=float))
    for r in conv:
        print("conv", r["profile"], r["dt"], r["wind"], {k: round(r[k], 4) for k in ["td_vz", "td_vh", "td_miss", "h_max",
                                                                                    "prop_used", "h_ign", "td_t"]})
    for r in zero:
        print("zero", r["profile"], r["fins"], r["success"], round(r["td_vz"], 3), round(r["prop_used"], 3))
    for c in cmp1d:
        print("1d", c["profile"], {k: round(c["sim6"][k], 3) for k in ["h_max", "prop_used", "h_ign", "v_ign", "td_vz"]},
              {k: round(c["sim1d"][k], 3) for k in ["h_max", "prop_used", "h_ign", "v_ign", "td_v"]})
    print("seed", out["compare_lead_seed"]["seed"])


if __name__ == "__main__":
    main()
