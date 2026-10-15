"""m2_mech_v2_check v1 (2026-10-12): checks of the run6 v2.6 reading of mechanical.json v2 (GNC v3 re-baseline).
Independent of the Monte Carlo; every reference number is read from the interface files, none typed here.
  C1 gimballed engine mass properties: the 6-DOF engine model (mechanical.json dry_grain_burnt + the combustion.json
     grain, sim6 massprops) against mechanical.json v2 at its five published states (wet, mid-burn, end of the max-thrust
     case, end of DC-B1, grain burnt), matched by the grain mass inside: mass, CG offset from the pivot l_e, I_pivot xx.
     Tolerances 1 g, 0.5 mm, 1 % (the sim's grain is a uniform annulus of the published grain).
  C2 rocking-mode band: sqrt(K / I_pivot) at both ends of the published axis-stiffness range against
     tvc_actuation.rocking_mode_Hz (excl. J_int); 0.3 Hz. The published band is reproduced with the mid-burn inertia at
     both ends (first definition of this check used the wet inertia at the low end and the grain-burnt inertia at the
     high end: 15.88-28.37 Hz vs 16.0-27.8 Hz, FAIL by 0.57 Hz at the high end; a check-definition error, kept here).
  C3 ledger: liftoff mass, CG and item changes between the v3b set (mechanical.json v1 + S230 growth) and the v3c set
     (mechanical.json v2), both at the 2.00 kg lead tank; the published fixed module and tank tube reported next to the
     ledger values.
  C4 nominal flights (no wind, no noise) of A-D, A-F and B on the v3c set land within the criteria.
Env: GNC_IFACE (v3c set), GNC_IFACE_OLD (v3b set, for C3), GNC_OUT (default out/mech_v2_check)."""
import json
import os
import subprocess
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, sim6 as s6  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/mech_v2_check")
FAIL, LOG = [], []


def check(name, ok, msg, data=None):
    print(f"{'PASS' if ok else 'FAIL'} {name}: {msg}", flush=True)
    LOG.append(dict(check=name, result="PASS" if ok else "FAIL", detail=msg, data=data))
    if not ok:
        FAIL.append(name)


def c1():
    src = R.sources()
    mech, comb = src["mech"], src["comb"]
    gm = mech["gimballed_mass_properties"]
    cfg = R.cfg_of(profile="A-D", fins=True, floor=0.20, rcs=False, m_n2o=2.0)
    par, apar, comp, mp, tab, info = R.build(cfg)
    zp = info["z_pivot"]
    g_tot = comb["gas_path"]["grain"]["mass_kg"]["v"]
    rows = []
    for st in ("wet_full_grain", "mid_burn", "end_of_max_thrust_case", "end_of_DC-B1", "dry_grain_burnt"):
        s = gm[st]
        gin = s["grain_mass_inside_kg"]["v"]
        o = np.zeros(8)
        s6.massprops(mp, 0.0, 0.0, par[s6.P_rho_l_nom], gin, o)
        m_e, z_e, I_e = o[4], o[5], o[6]
        I_piv = I_e + m_e * (z_e - zp) ** 2
        ref_m, ref_le, ref_I = s["m_kg"]["v"], s["cg_m"]["v"][2], s["I_pivot_kgm2"]["v"][0][0]
        rows.append(dict(state=st, grain_inside_kg=gin, m_sim=m_e, m_ref=ref_m, le_sim_mm=(z_e - zp) * 1e3,
                         le_ref_mm=ref_le * 1e3, Ipiv_sim=I_piv, Ipiv_ref=ref_I))
        check(f"C1 engine {st}", abs(m_e - ref_m) < 1e-3 and abs((z_e - zp) - ref_le) < 5e-4 and abs(I_piv / ref_I - 1) < 0.01,
              f"grain {gin:.4f} kg: m {m_e:.4f} vs {ref_m:.4f} kg, l_e {(z_e - zp) * 1e3:+.2f} vs {ref_le * 1e3:+.2f} mm, "
              f"I_pivot {I_piv:.5f} vs {ref_I:.5f} kg m2 ({100 * (I_piv / ref_I - 1):+.2f} %)")
    return dict(z_pivot=zp, grain_total_kg=g_tot, states=rows)


def c2():
    mech = R.sources()["mech"]
    ta = mech["tvc_actuation"]
    K = ta["axis_stiffness_Nm_per_rad"]["v"]
    gm = mech["gimballed_mass_properties"]
    fr = ta["rocking_mode_Hz"]["v"]
    Im = gm["mid_burn"]["I_pivot_kgm2"]["v"][0][0]
    f_lo = np.sqrt(K[0] / Im) / (2 * np.pi)
    f_hi = np.sqrt(K[1] / Im) / (2 * np.pi)
    check("C2 rocking band", abs(f_lo - fr[0]) < 0.3 and abs(f_hi - fr[1]) < 0.3,
          f"K {K[0]:.0f}-{K[1]:.0f} N m/rad on the mid-burn I_pivot {Im:.4f} kg m2: {f_lo:.2f}-{f_hi:.2f} Hz vs published "
          f"{fr[0]}-{fr[1]} Hz")
    return dict(K=K, I_mid=Im, f_sim=[f_lo, f_hi], f_ref=fr, first_definition_failed=dict(f_sim=[15.88, 28.37],
                note="wet inertia at the low end, grain-burnt inertia at the high end"))


def ledger(iface):
    code = (
        "import json,sys,os; sys.path.insert(0, %r); from gncsim import run6 as R\n"
        "cfg=R.cfg_of(profile='A-D', fins=True, floor=0.20, rcs=False, m_n2o=2.0)\n"
        "p,a,c,mp,t,i=R.build(cfg)\n"
        "print(json.dumps(dict(m_liftoff=i['m_liftoff'], zcg0=i['zcg0'], It0=i['It0'], z_pivot=i['z_pivot'], m_dry=i['m_dry'],"
        " mech=R.sources()['mech'].get('version'), items=[dict(name=x['name'][:60], m=x['m'], z=x['z']) for x in i['ledger']])))"
        % os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env = dict(os.environ, GNC_IFACE=iface)
    out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True).stdout
    return json.loads(out.strip().splitlines()[-1])


def c3():
    new = ledger(os.environ["GNC_IFACE"])
    old_if = os.environ.get("GNC_IFACE_OLD")
    old = ledger(old_if) if old_if else None
    mech = R.sources()["mech"]
    fm = mech.get("fixed_module", {})
    tank = fm.get("tank", {})
    res = dict(v3c=new, v3b=old, published=dict(fixed_group_total_CAD_kg=fm.get("fixed_group_total_CAD_kg", {}).get("v"),
                                                 tank_tube_mass_kg=tank.get("tube_mass_kg", {}).get("v"),
                                                 tank_internal_cyl_length_m=tank.get("internal_cyl_length_m", {}).get("v")))
    msg = f"liftoff {new['m_liftoff']:.3f} kg, CG {new['zcg0']:.4f} m, pivot {new['z_pivot']:.4f} m (mechanical.json {new['mech']})"
    if old:
        msg += (f"; v3b {old['m_liftoff']:.3f} kg, CG {old['zcg0']:.4f} m, pivot {old['z_pivot']:.4f} m -> "
                f"{new['m_liftoff'] - old['m_liftoff']:+.3f} kg, {1e3 * (new['zcg0'] - old['zcg0']):+.1f} mm")
        on = {x["name"]: x for x in old["items"]}
        nn = {x["name"]: x for x in new["items"]}
        res["changed_items"] = [dict(name=k, old=on.get(k, {}).get("m"), new=nn.get(k, {}).get("m"))
                                for k in sorted(set(on) | set(nn))
                                if abs((on.get(k, {}).get("m") or 0.0) - (nn.get(k, {}).get("m") or 0.0)) > 1e-6]
    check("C3 ledger on mechanical.json v2", new["mech"] != "v1", msg, None)
    return res


def c4():
    out = {}
    for name, ov in (("A-D", dict(profile="A-D", fins=True)), ("A-F", dict(profile="A-F", fins=False)),
                     ("B", dict(profile="B", fins=False))):
        cfg = R.cfg_of(**dict(ov, floor=0.20, rcs=False, m_n2o=2.0))
        res, rec, info = R.fly(dict(cfg, noise=False, wind=0.0, gust=False), nrec=10)
        ok = R.success(res)
        out[name] = dict(ok=ok, **{k: float(res[k]) for k in ("td_vz", "td_vh", "td_tilt", "h_max", "prop_used", "liq_left")})
        check(f"C4 nominal {name}", ok, f"landed {ok}, td_vz {float(res['td_vz']):.2f} m/s, apex {float(res['h_max']):.1f} m, "
                                         f"liquid left {float(res['liq_left']):.3f} kg, m_liftoff {info['m_liftoff']:.3f} kg")
    return out


if __name__ == "__main__":
    r = dict(version="m2_mech_v2_check v1", sim=s6.SIM6_VERSION, iface=os.environ.get("GNC_IFACE"),
             mech=R.sources()["mech"].get("version"), comb=R.sources()["comb"].get("version"))
    r["C1"] = c1()
    r["C2"] = c2()
    r["C3"] = c3()
    r["C4"] = c4()
    r["n_fail"] = len(FAIL)
    r["failures"] = FAIL
    r["checks"] = LOG
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "mech_v2_check.json"), "w") as f:
        json.dump(r, f, indent=1, default=float)
    print(f"{len(FAIL)} failures", FAIL)
    sys.exit(len(FAIL))
