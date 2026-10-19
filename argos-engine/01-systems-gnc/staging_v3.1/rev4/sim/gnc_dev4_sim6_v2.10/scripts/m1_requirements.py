"""Assemble gnc.json (v1, M1 first pass) from the GNC models and results.

Reads: interface JSON (ENGINE-BASELINE v0, combustion, electronics, mechanical if present),
       OUT/m1/landing_closure_mc1d_<SUF>.json, sweeps_<SUF>.csv, ballast_trade_<SUF>.csv,
       sensitivity_<SUF>.json, OUT/duty_cycles/duty_cycles_index_v1.json and DC-A1 CSV,
       gncsim.vehicle (RV-1 ledger), gncsim.aero (static coefficients), gncsim.tvc_analytic.
Writes: OUT/gnc_v1.json (copied to /mnt/project-files/engine/interfaces/gnc.json by the publisher),
        OUT/vehicle/mass_ledger_v1.csv/.json, OUT/vehicle/massprops_states_v1.csv, OUT/vehicle/aero_static_v1.csv.
Every number carries a tag (REQ/DATASHEET/LITERATURE/SIM/DERIVED/ASSUMED) and a rationale.
"""
import csv
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import vehicle as veh, aero, tvc_analytic as tvc, params as prm, mc1d, run1d as r1, sizing  # noqa

OUT = os.environ.get("GNC_OUT_ROOT", "/home/claude/work/space/out")
SUF = os.environ.get("GNC_SUFFIX", "v1p2")
SHARED = "/mnt/project-files/engine"
G0 = 9.80665
DATE = "2026-10-11"


def P(v, tag, note=None):
    d = {"v": v, "tag": tag}
    if note:
        d["note"] = note
    return d


def rnd(x, n=4):
    if isinstance(x, (list, tuple)):
        return [rnd(y, n) for y in x]
    if isinstance(x, (float, np.floating)):
        return float(round(float(x), n))
    return x


def read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def massprops_at(geo, led, m_liq, m_vap, m_fuel, tank_V, rho_l=785.0, liquid_forward=False):
    mp = veh.build_mp(geo, led, tank_V=tank_V)
    o = np.zeros(8)
    veh.massprops(mp, m_liq, m_vap, rho_l, m_fuel, o)
    if liquid_forward and m_liq > 0:
        # liquid collected at the forward end (nose-first coast, drag deceleration): shift its CG
        A = mp[veh.MP_TAIN]
        h = min(m_liq / (rho_l * A), mp[veh.MP_TLIN])
        dz = mp[veh.MP_TLIN] - h
        m = o[0]
        zc_new = o[1] + m_liq * dz / m
        # transverse inertia about the new CG (parallel-axis update of the liquid column; vapour neglected)
        zl_aft = mp[veh.MP_TZB] + 0.5 * h
        zl_fwd = zl_aft + dz
        It = o[2] + m * o[1] ** 2 - m * zc_new ** 2 + m_liq * (zl_fwd ** 2 - zl_aft ** 2)
        o[1], o[2] = zc_new, It
    return o


def main():
    ifc = prm.load_interfaces()
    comb, elec, mech = ifc.get("combustion.json"), ifc.get("electronics.json"), ifc.get("mechanical.json")
    base = ifc.get("ENGINE-BASELINE-v0.json") or {}
    cl = json.load(open(os.path.join(OUT, "m1", f"landing_closure_mc1d_{SUF}.json")))
    clm = json.load(open(os.path.join(OUT, "m1", f"landing_closure_mc1d_{SUF}_m115.json")))
    sw = read_csv(os.path.join(OUT, "m1", f"sweeps_{SUF}.csv"))
    bt = read_csv(os.path.join(OUT, "m1", f"ballast_trade_{SUF}.csv"))
    sens = json.load(open(os.path.join(OUT, "m1", f"sensitivity_{SUF}.json")))
    dci = json.load(open(os.path.join(OUT, "duty_cycles", "duty_cycles_index_v1.json")))
    vdir = os.path.join(OUT, "vehicle")
    os.makedirs(vdir, exist_ok=True)

    # ------------------------------------------------------------------ reference vehicle RV-1
    out = {}
    geo = veh.reference_geometry(pivot="mid")
    geo_f = veh.reference_geometry(pivot="forward")
    LOAD = 1.30
    V = sizing.tank_volume_for(LOAD)
    led = veh.mass_ledger(geo, descent_option="drogue", tank_V=V)
    rows = veh.ledger_table(led)
    with open(os.path.join(vdir, "mass_ledger_v1.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for x in rows:
            w.writerow(x)
    m_dry = sum(i["m"] for i in led)
    m_dry_min = sum(i["m_min"] for i in led)
    m_dry_max = sum(i["m_max"] for i in led)
    m_prop_dry = sum(i["m"] for i in led if i["owner"] == "propulsion")
    p = prm.default_params()
    m_fuel0 = p["rho_f"]["v"] * np.pi / 4 * (p["D_grain_o"]["v"] ** 2 - p["D_port0"]["v"] ** 2) * p["L_grain"]["v"]
    json.dump(dict(version="mass_ledger_v1", date=DATE, vehicle="RV-1 (A-D configuration, drogue option)",
                   frame="stations z [m] from the airframe aft datum (base plane), +z toward the nose",
                   tank_V_m3=V, items=led, sums=dict(dry_kg=m_dry, dry_min_kg=m_dry_min, dry_max_kg=m_dry_max)),
              open(os.path.join(vdir, "mass_ledger_v1.json"), "w"), indent=1, default=float)

    # mass-property states from the DC-A1 record (v1.2 guidance)
    dc_rows = read_csv(os.path.join(OUT, "duty_cycles", "DC-A1_full_flight_drogue_300m_v1.csv"))
    ph = np.array([float(x["phase"]) for x in dc_rows])
    tt = np.array([float(x["t_s"]) for x in dc_rows])

    def first(cond):
        k = int(np.argmax(cond))
        return dc_rows[k]
    ev = {"liftoff": dc_rows[0], "MECO": first(ph >= 2), "apogee": first(ph >= 3),
          "relight_command": first(ph >= 4), "landing_burn_start": first(ph >= 5),
          "terminal_gate": first(ph >= 6), "touchdown": dc_rows[-1]}
    states = []
    for k, x in ev.items():
        states.append(dict(event=k, t_s=rnd(float(x["t_s"]), 2), h_m=rnd(float(x["h_m"]), 2),
                           v_mps=rnd(float(x["v_mps"]), 2), m_kg=rnd(float(x["m_kg"]), 3),
                           z_cg_m=rnd(float(x["z_cg_m"]), 4), I_transverse_kgm2=rnd(float(x["I_transverse_kgm2"]), 4),
                           I_roll_kgm2=rnd(float(x["I_roll_kgm2"]), 4)))
    # liquid-forward CG excursion at MECO (nose-first coast, drag decel pushes the liquid forward)
    rec_meco = ev["MECO"]
    with open(os.path.join(vdir, "massprops_states_v1.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(states[0].keys()))
        w.writeheader()
        for x in states:
            w.writerow(x)
    # gimballed subassembly and TVC geometry for both pivots (landing state)
    tw = tvc.sizing_table()
    gim = {}
    for row in tw:
        key = f"{row['pivot']}_{row['state']}"
        gim[key] = {k: rnd(v, 4) for k, v in row.items() if k not in ("pivot", "state")}
    # CG excursion from liquid position (full load, coast)
    mlq = 1.05
    o_aft = massprops_at(geo, led, mlq, 0.10, m_fuel0 * 0.75, V)
    o_fwd = massprops_at(geo, led, mlq, 0.10, m_fuel0 * 0.75, V, liquid_forward=True)

    # CG extremes from the ledger item ranges (landing state: N2O residual ~0.2 kg, fuel 0.35 kg ignored -> dry items)
    zc_nom = sum(i["m"] * i["z"] for i in led) / sum(i["m"] for i in led)
    def cg_ext(fwd):
        num = den = 0.0
        for i in led:
            hi_side = (i["z"] > zc_nom) == fwd
            mm = i["m_max"] if hi_side else i["m_min"]
            num += mm * i["z"]; den += mm
        return num / den
    cg_fwd_ext, cg_aft_ext = cg_ext(True), cg_ext(False)

    # aero static coefficients (nominal and adverse), CG at landing state
    zc_land = float(ev["touchdown"]["z_cg_m"])
    ap_n, cp_n = aero.build_aero_params(geo, None)
    ap_a, cp_a = aero.build_aero_params(geo, tvc.ADVERSE)
    alphas = [0, 2, 5, 10, 20, 30, 45, 60, 90, 120, 150, 160, 170, 175, 178, 180]
    a_rows = []
    for lab, ap, cp in (("nominal", ap_n, cp_n), ("adverse", ap_a, cp_a)):
        for legs in (0.0, 1.0):
            ap2 = ap.copy()
            ap2[aero.A_LEGS_DEPLOYED] = legs
            sc = aero.static_coefficients(ap2, cp, zc_land, alphas)
            for a, CN, CA, Cm, zcp in sc:
                a_rows.append(dict(set=lab, legs_deployed=int(legs), alpha_deg=a, CN=rnd(CN, 4), CA=rnd(CA, 4),
                                   Cm_about_cg=rnd(Cm, 4), z_cp_m=rnd(zcp, 4) if np.isfinite(zcp) else ""))
    with open(os.path.join(vdir, "aero_static_v1.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(a_rows[0].keys()))
        w.writeheader()
        for x in a_rows:
            w.writerow(x)
    # small-angle slopes
    def slope(ap, cp, a0, legs=0.0):
        ap2 = ap.copy()
        ap2[aero.A_LEGS_DEPLOYED] = legs
        sc = aero.static_coefficients(ap2, cp, zc_land, [a0, a0 + 1.0])
        dCN = (sc[1, 1] - sc[0, 1]) / np.radians(1.0)
        zcp = sc[1, 4]
        return dCN, zcp
    CNa_nf, zcp_nf = slope(ap_n, cp_n, 0.0)
    CNa_tf_n, zcp_tf_n = slope(ap_n, cp_n, 179.0 - 1.0)
    CNa_tf_a, zcp_tf_a = slope(ap_a, cp_a, 179.0 - 1.0)

    # TVC demand cases
    wind_mid = tvc.terminal_wind_cases("mid", winds=(8.0, 11.0), legs=False)
    wind_mid_legs = tvc.terminal_wind_cases("mid", winds=(8.0, 11.0), legs=True)
    wind_fwd = tvc.terminal_wind_cases("forward", winds=(8.0, 11.0), legs=False)
    hb_mid = tvc.hinge_budget(tvc.mass_case("mid", 1.3, 0.50))
    hb_fwd = tvc.hinge_budget(tvc.mass_case("forward", 1.3, 0.50))

    def wc(lst, wind, aero_set):
        for x in lst:
            if x["wind"] == wind and x["aero"] == aero_set:
                return x
    w11_mid = wc(wind_mid, 11.0, "adverse")
    w11_fwd = wc(wind_fwd, 11.0, "adverse")
    w11_mid_l = wc(wind_mid_legs, 11.0, "adverse")
    trim_mid = gim["mid_landing"]["trim_deg"]
    trim_fwd = gim["forward_landing"]["trim_deg"]
    range_mid = w11_mid["delta_aero_deg"] + trim_mid
    range_fwd = w11_fwd["delta_aero_deg"] + trim_fwd

    # ------------------------------------------------------------------ landing closure summary
    def case(prof, fl, mode, src=None):
        for c in (src or clm)["cases"]:
            if c.get("profile") == prof and abs(c.get("floor", -1) - fl) < 1e-9 and c.get("mode") == mode:
                return c
        return None
    closure = []
    for c in clm["cases"]:
        closure.append({k: c.get(k) for k in ("profile", "floor", "mode", "ballast_kg", "m_n2o_sized_kg", "m_n2o_mc_kg",
                                              "m_liftoff_kg", "m_land_nom_kg", "n", "P_success", "ci_lo", "ci_hi",
                                              "td_v_mean", "td_v_p01", "exhausted", "hoverslam_fraction",
                                              "cut_fraction", "prop_used_mean_kg", "note") if k in c})

    def sweep_val(prof, param):
        return [(float(x["value"]), float(x["P"]), float(x["lo"]), float(x["prop_used_mean_kg"]),
                 float(x["h_ign_mean_m"])) for x in sw if x["profile"] == prof and x["param"] == param]

    # throttle response threshold: largest t10-90 with P >= 0.99 on both A profiles
    thr = {}
    for prof in ["A_drogue_300m", "A_freefall_300m"]:
        ok = [v for v, P_, lo, *_ in sweep_val(prof, "t10_90_s") if P_ >= 0.99]
        thr[prof] = max(ok) if ok else None
    t1090_sim = min(v for v in thr.values() if v is not None)
    slew_ok = {}
    for prof in ["A_drogue_300m", "A_freefall_300m", "B_hop_100m"]:
        ok = [v for v, P_, *_ in sweep_val(prof, "slew_Fmax_per_s") if P_ >= 0.99 * max(
            P2 for _, P2, *_ in sweep_val(prof, "slew_Fmax_per_s"))]
        slew_ok[prof] = min(ok) if ok else None
    ign = {}
    for prof in ["A_drogue_300m", "A_freefall_300m"]:
        ign[prof] = {f"mean{m}": [(h, P_, pu, hi) for h, P_, lo, pu, hi in sweep_val(prof, f"ign_mean{m}_halfwidth")]
                     for m in [0.3, 0.5, 0.8, 1.2]}

    # ballast/payload trade (20 % floor)
    lift = []
    for x in bt:
        if x.get("closes") == "True":
            lift.append({k: (float(v) if k not in ("profile", "closes") else v) for k, v in x.items()})

    # ------------------------------------------------------------------ design loads (MC on baseline)
    rng_rows = []
    pk = dict(profile=0, h_target=300.0, descent="drogue", drogue_CdA=0.5, kd=0.6, t_ign_est=0.6)
    rng = np.random.default_rng(7)
    d = mc1d.draw(rng, 300)
    for i in range(300):
        par = r1.make_par(floor=0.20, m_n2o=LOAD, tank_V=V, thrust_scale=d["thrust_scale"][i],
                          isp_scale=d["isp_scale"][i], dry_scale=d["dry_scale"][i], T0=d["T0"][i],
                          t_ign=d["t_ign"][i], tau=0.1 / 2.197 * d["tau_f"][i], **pk)
        res, _ = r1.fly(par, rec_dt=0.05, nrec=3000)
        rng_rows.append((res["max_acc"], res["min_acc"], res["F_land_max"]))
    acc = np.array(rng_rows)
    a_max_p999 = float(np.max(acc[:, 0]))
    a_nom = float(dci["cycles"][0]["max_axial_specific_mps2"])

    # ------------------------------------------------------------------ assemble
    meta = dict(
        id="gnc", version="v1", date=DATE, owner="Space/GNC (01-systems-gnc)",
        status=("M1 FIRST PASS. 1-D vertical simulation (sim1d) + analytic TVC sizing + component-build-up aero. "
                "The 6-DOF Monte Carlo (attitude, lateral, wind, sensors, TVC dynamics) supersedes the tilt/lateral "
                "items in v2. Engine map = GNC placeholder from ENGINE-BASELINE v0 (eps 3, port 30 mm): "
                "combustion.json v1 (eps 2, helical port, Isp map) and electronics.json v1 arrived during M1 and are "
                "integrated in gnc.json v2 (M2). Predictions, not hardware validation."),
        units="SI (m, kg, s, N, Pa, K, rad) unless the key names another unit (_deg, _dps, _Hz, _g, _L)",
        conventions={
            "body_frame": "z_b along the vehicle axis toward the nose; x_b, y_b = gimbal axes A (pitch) / B (yaw)",
            "stations": "z [m] from the airframe aft datum (base plane, foot-plane offset in mass ledger), +z toward the nose; nozzle exit at z = -0.03 m",
            "world_frame_6dof": "ENU, flat earth, ISA (site density rho0 parameter)",
            "throttle_frac": "F / 500 N (F_max)",
            "gimbal_angle": "angle between thrust line and body axis, per axis, 0 = aligned",
        },
        inputs_read={
            "ENGINE-BASELINE-v0.json": base.get("version", "v0") if base else "absent",
            "REQUIREMENTS.md": "rev 1 (ENG-02 pintle baseline; floors req 25 %, target 20 %, stretch 12.5 %)",
            "combustion.json": (comb or {}).get("version", "absent") + " (read; integrated in v2: eps 2.0, Isp_SL 199.3 s at 500 N, floor 12.5 % at Pc 4.36 bar)" if comb else "absent",
            "electronics.json": (elec or {}).get("version", "absent") + " (read; servo model used for the actuator/CSI check in v2)" if elec else "absent",
            "mechanical.json": (mech or {}).get("version", "absent") if mech else "absent at v1 (gimballed mass/inertia/pivot ASSUMED in mass ledger v1)",
        },
        scripts=["01-systems-gnc/sim/gncsim/*.py", "01-systems-gnc/sim/scripts/m1_duty_cycles.py",
                 "01-systems-gnc/sim/scripts/m1_landing_mc_v1p1.py", "01-systems-gnc/sim/scripts/m1_sweeps.py",
                 "01-systems-gnc/sim/scripts/m1_requirements.py"],
    )
    out.update(meta)

    out["reference_vehicle"] = {
        "name": "RV-1 (GNC reference vehicle v1, parametric; owner of the real airframe: Lauty/airframe)",
        "length_overall_m": P(2.03, "ASSUMED REQUIREMENTS ref. vehicle ~2.0 m + 0.03 m nozzle protrusion"),
        "body_diameter_m": P(geo["d"], "ASSUMED airframe ID 0.120 m (ENGINE-BASELINE) + 3 mm wall"),
        "nose": P("tangent ogive, L 0.30 m", "ASSUMED"),
        "fins": P("none (finless: tail-first aero is unstable with aft fins; see aero)", "DERIVED aero trade"),
        "landing_legs": P({"n": 4, "foot_radius_m": geo["r_foot"], "deploy": "at relight command (A) / fixed (B tests)",
                           "stroke_m": 0.10}, "ASSUMED (Lauty to confirm; stroke drives the landing load)"),
        "mass_ledger_csv": "01-systems-gnc/vehicle/mass_ledger_v1.csv",
        "dry_mass_kg": P(rnd(m_dry, 3), "DERIVED mass ledger v1 (sum of ASSUMED items, no N2O, no fuel)",
                         f"range {m_dry_min:.2f}-{m_dry_max:.2f} kg (item min/max); propulsion items {m_prop_dry:.2f} kg"),
        "fuel_grain_mass_kg": P(rnd(m_fuel0, 3), "DERIVED ENGINE-BASELINE v0 placeholder grain (combustion.json v1: 0.351 kg, used in v2)"),
        "n2o_load_kg": P(LOAD, "SIM sizing (A-D, 300 m): nominal need 1.13 kg incl. 20 % reserve on liquid used, x1.15 MC margin"),
        "tank_volume_L": P(rnd(V * 1e3, 3), "DERIVED load / (0.85 x rho_l(25 C)) - 15 % ullage at 25 C (ASSUMED fill rule)"),
        "liftoff_mass_kg": P(rnd(float(ev['liftoff']['m_kg']), 3), "SIM DC-A1 (A-D baseline)"),
        "landing_mass_kg": P(rnd(float(ev['touchdown']['m_kg']), 3), "SIM DC-A1 (A-D baseline)",
                             "landing mass = dry + unburnt fuel + residual N2O; dispersions +/-5 % (1 sigma) on dry mass"),
        "mass_properties_vs_time": {
            "events": states,
            "full_histories": "every duty-cycle CSV carries m_kg, z_cg_m, I_transverse_kgm2, I_roll_kgm2 (see duty_cycles)",
            "tag": "SIM sim1d DC-A1 + DERIVED vehicle.massprops (liquid settled aft, rigid in pitch, excluded from roll)",
        },
        "liquid_level_cg_shift": P({"liquid_aft_z_cg_m": rnd(o_aft[1], 4), "liquid_forward_z_cg_m": rnd(o_fwd[1], 4),
                                    "delta_m": rnd(o_fwd[1] - o_aft[1], 4), "m_liq_kg": mlq},
                                   "DERIVED vehicle.massprops: liquid column at the aft (thrusting/descending) or forward end (nose-first coast, drag deceleration)"),
        "gimballed_subassembly": P({"pivot_options": {
            "mid": {"z_pivot_m": geo["z_pivot"], **gim["mid_landing"]},
            "forward": {"z_pivot_m": geo_f["z_pivot"], **gim["forward_landing"]}},
            "recommended_pivot": "mid (near the gimballed CG)"},
            "DERIVED tvc_analytic.sizing_table (mass ledger v1 ASSUMED engine items; mechanical.json absent)",
            "l_p = z_cg - z_pivot; J_twd = I_e + m_e l_e (l_e + l_p); w_twd = sqrt(T l_p / J_twd) tail-wags-dog zero"),
        "aero": {
            "method": "component build-up (Barrowman nose, blunt-base leading term, Allen-Perkins/Jorgensen crossflow, legs); evaluated at local velocity incl. omega x r",
            "static_table_csv": "01-systems-gnc/vehicle/aero_static_v1.csv",
            "nose_first_CNa_per_rad": P(rnd(CNa_nf, 3), "DERIVED Barrowman + crossflow (alpha 0-1 deg)"),
            "nose_first_z_cp_m": P(rnd(zcp_nf, 3), "DERIVED", f"CG at landing {zc_land:.3f} m: finless body is statically UNSTABLE nose-first (CP ahead of CG)"),
            "tail_first_CNa_per_rad_nominal": P(rnd(CNa_tf_n, 3), "ASSUMED k_base_lead 0.75, k_nose_trail 0.25 (unvalidated)"),
            "tail_first_CNa_per_rad_adverse": P(rnd(CNa_tf_a, 3), "ASSUMED k_base_lead 1.0, k_nose_trail 0.5"),
            "tail_first_z_cp_m_nominal": P(rnd(zcp_tf_n, 3), "ASSUMED", "tail-first: unstable at small AoA, stable beyond ~20 deg off-axis (crossflow on the long forward body)"),
            "CA_nose_first": P(geo["CA0_nf"], "ASSUMED (Cd0 0.45 finless ogive body at M<0.3, +/-30 %)"),
            "CA_tail_first": P(geo["CA0_tf"], "ASSUMED blunt-base-first bluff body 1.05 (+/-30 %); engine-on retropropulsion factor 0.5-1.0 (ASSUMED)"),
            "CA_legs_deployed_increment": P(geo["CA_legs"], "ASSUMED 4 legs crossflow-equivalent"),
            "unknowns": "Tail-first aero (CNa, CP, base/plume interaction) is UNKNOWN to better than ~x2: only CFD (05-plume-cfd), wind tunnel or flight data close it. All tail-first TVC sizing uses the adverse set.",
        },
    }

    dc1 = dci["cycles"][0]["summary"]
    out["flight_profile"] = {
        "recommended_baseline": P("A-D", "DERIVED descent-attitude trade (1-D + analytic TVC; 6-DOF confirmation in v2)",
            "Full-thrust ascent -> MECO on predicted apogee (300 m) -> nose-first coast -> nose drogue at apogee -> "
            "engine-down (tail-first) descent at ~18-21 m/s under drogue -> relight planned on the worst-case ignition delay "
            "(0.6 s) at ~25-30 m -> drogue released on Pc-confirmed ignition -> throttled TVC landing burn (velocity-tracking "
            "guidance, gate 4 m / 1 m/s) -> touchdown ~1 m/s -> engine cut on contact."),
        "why": [
            "drogue sets attitude (engine-down) and settles the N2O liquid aft for the relight (drag ~ weight -> ~1 g settling)",
            "relight speed ~20 m/s instead of ~57 m/s free-fall: landing burn impulse and propellant ~25 % lower, TVC demand at relight 1-2 deg instead of 4-7 deg (adverse aero)",
            "drogue doubles as a degraded recovery path (vehicle loss but low-energy impact ~20 m/s, 2.4 kJ) if the relight fails",
            "single relight only (2 starts per flight) - ENG-04 >= 3 leaves one spare start",
        ],
        "costs_and_risks": [
            "wind drift under drogue: ~15 s from 300 m -> 100-120 m downwind at 8 m/s unless the ascent is biased upwind (6-DOF v2 quantifies)",
            "drogue release mechanism and line/plume clearance at relight (Lauty: release + swivel at the nose)",
            "relight at ~25-30 m leaves no time for a backup main parachute if ignition fails (ignition reliability is mission-critical)",
        ],
        "baseline_numbers": P({"apogee_m": rnd(dc1["h_max"], 1), "ascent_burn_s": rnd(float(ev["MECO"]["t_s"]), 2),
                               "relight_altitude_m": rnd(dc1["h_ign"], 1), "relight_speed_mps": rnd(dc1["v_ign"], 2),
                               "total_burn_s": rnd(dc1["burn_time"], 2), "propellant_used_kg": rnd(dc1["prop_used"], 3),
                               "touchdown_speed_mps": rnd(dc1["td_v"], 2), "starts": int(dc1["starts"]),
                               "landing_mass_kg": rnd(dc1["m_land"], 3)},
                              "SIM sim1d DC-A1 nominal (floor 20 %, placeholder engine map)"),
        "alternatives": {
            "A-F free-fall": "same as A-D without drogue: ~57 m/s tail-first relight at ~120 m, needs an attitude solution during the unstable tail-first fall (no aero stability at small AoA) - not recommended",
            "B continuous-burn hop": "no relight; ascent, throttle to the floor through apex and descent. Propellant cost grows steeply with floor and apex (100 m: 1.44 kg at 12.5 %, 2.06 kg at 20 %, 3.1 kg at 25 %); infeasible without ballast when T_floor >= W. Used for the test campaign (low hops) and as an ACEMA fallback only with the 12.5 % floor.",
            "A-RCS (N2O cold-gas attitude) / A-flaps (nose flaps)": "kept as research options in REPORT (impulse, mass, valve count); not baseline at v1",
        },
        "test_campaign": [
            "T1 static fires (DC-D): ignition latency/repeatability (>= 30 starts), throttle map and Pc loop (10-90 % time, slew, resolution, floor stability), 3 starts per run, gimbal sweeps under thrust, thrust-vector alignment, ENGINE ROLL TORQUE measurement",
            "T2 tethered hover (DC-C): 0.5-2 m, hover/doublets/TVC attitude hold, estimator and thrust-effectiveness estimator check, abort on tether",
            "T3 low hops (B, 5-50 m) with the hover-capable floor; legs fixed; landing guidance and lateral divert",
            "T4 relight hop (A-D mini: MECO ~60-100 m, drogue, relight at ~25 m)",
            "T5 full profile A-D 300 m (ACEMA 2027-09-01)",
        ],
    }

    # ------------------------------------------------------------------ requirements
    floors = [0.125, 0.20, 0.25, 0.40]
    window = {f"{int(fl*1000)/10}%": rnd(fl * 500.0 / (0.9 * G0), 2) for fl in floors}
    cAD = {fl: case("A_drogue_300m", fl, "auto") for fl in floors}
    cAD0 = {fl: case("A_drogue_300m", fl, "auto", cl) for fl in floors}
    cAF0 = {fl: case("A_freefall_300m", fl, "auto", cl) for fl in floors}
    cAF = {fl: case("A_freefall_300m", fl, "auto") for fl in floors}
    cB = {fl: case("B_hop_100m", fl, "auto") for fl in floors}
    cAD_bal = {fl: case("A_drogue_300m", fl, "hover_with_ballast") for fl in [0.25, 0.40]}

    def pf(c):
        return None if c is None else c.get("P_success")
    req = {}
    req["throttle"] = {
        "floor_frac_required_max": P(0.20, "DERIVED landing closure (SIM mc1d " + SUF + "_m115) + hover rule",
            "GNC requirement for HOVER CAPABILITY of RV-1 (landing mass 11.9-12.4 kg): T_floor <= 0.9 W needs floor <= 20 % "
            "(11.3 kg window). Needed for the tethered-hover tests (DC-C), low hops (B: P 0.978 at 20 % vs 0.864 at 25 %, 1-D) and "
            "the hover-capable landing mode (terminal 1 m/s descent with time for lateral/attitude correction). "
            "ENG-02 'required <= 25 %' remains ACCEPTABLE FOR THE A-D FLIGHT through the hoverslam fallback "
            "(1-D P = 1.000 at 25 %, 0.992 at 40 %, with the accelerometer thrust-effectiveness estimator) - provisional "
            "until the 6-DOF shows hoverslam meets the lateral (<= 0.5 m/s) and tilt (<= 5 deg) touchdown criteria."),
        "floor_frac_acceptable_flight_with_hoverslam": P(0.25, "REQ ENG-02 rev1 + SIM mc1d " + SUF + "_m115 (1-D)",
            "provisional (6-DOF v2); 40 % would also close in 1-D (P 0.99) but leaves T_floor/W ~1.7 at touchdown"),
        "floor_frac_goal": P(0.125, "REQ ENG-02 rev1 stretch (8:1)", "keeps the hover window open down to 7.1 kg landing mass; best propellant economy for hops"),
        "hover_rule": P("hover-capable if T_floor <= 0.9 W_land; otherwise flight software selects hoverslam (decided at the descent trigger from the estimated mass)",
                        "DERIVED (lead update 2026-10-11; 0.9 W ~ 1.1 m/s2 net descent authority at the floor)"),
        "landing_mass_window_min_kg_by_floor": P(window, "DERIVED m_land >= F_floor / (0.9 g0)",
                                                  "RV-1 nominal landing mass 12.0-12.4 kg (dry +/-5 % 1 sigma): 12.5 % large margin, 20 % marginal (T_floor/W 0.82-0.87), 25 %/40 % below the window"),
        "landing_closure_P_by_floor": P({f"{fl}": {"A_drogue_auto": pf(cAD[fl]), "A_freefall_auto": pf(cAF[fl]),
                                                    "B_hop_100m_auto": pf(cB[fl])} for fl in floors},
                                        f"SIM mc1d {SUF}_m115 (500 runs/case; N2O = sized nominal x 1.15; 1-D success: |v_td| <= 2 m/s, no exhaustion)",
                                        "auto = mode chosen by flight software (hoverslam at 25/40 %). 1-D only: lateral/tilt criteria in 6-DOF v2. "
                                        "At the bare sized load (x1.00) P drops to " + ", ".join(
                                            f"{fl}: A-D {pf(cAD0[fl])}, A-F {pf(cAF0[fl])}" for fl in floors) +
                                        " - limited by propellant exhaustion (1.6-2.6 %), hence the x1.15 load margin."),
        "t10_90_s": P(0.15, "REQ ENG-03 (target 0.10 s)",
                      f"1-D landing closure holds P >= 0.99 up to t10-90 = {t1090_sim:.2f} s (sweep); ENG-03 keeps x2 margin for the 6-DOF hover/attitude coupling"),
        "pc_loop_bandwidth_Hz": P(2.3, "DERIVED first-order equivalent of t10-90 0.15 s (f = 2.197/(2 pi t10-90)); target 3.5 Hz (0.10 s)",
                                  "pintle actuator small-signal bandwidth >= 8 Hz (combustion.json v1) is consistent"),
        "slew_min_Fmax_per_s": P(2.0, f"SIM mc1d {SUF} slew sweep", f"smallest slew with no loss of P (A-D {slew_ok.get('A_drogue_300m')}, A-F {slew_ok.get('A_freefall_300m')}, hop {slew_ok.get('B_hop_100m')} F_max/s); = 1000 N/s; target 5 F_max/s"),
        "resolution_frac": P(0.02, "REQ ENG-03", "1-D closure insensitive up to 5 %; hover altitude limit cycle checked in 6-DOF v2"),
        "overshoot_max_frac": P(0.10, "ASSUMED (to verify in the 6-DOF with the combustion valve->Pc plant model)"),
        "deadband_max_frac": P(0.005, "ASSUMED (as simulated)"),
        "ceiling_at_landing_min_N": P(rnd(1.5 * float(ev['touchdown']['m_kg']) * G0, 1), "DERIVED 1.5 x landing weight (braking authority a_d = 0.6 (F/m - g))",
                                      "ceiling vs tank temperature/blowdown from combustion.json v2 map"),
        "thrust_effectiveness_estimation": P("flight software estimates delivered/commanded thrust from the accelerometer (tau 0.1 s) during the landing burn",
                                             f"SIM mc1d {SUF}: hoverslam P at 40 % floor 0.66 -> 0.97-1.0 with the estimator (1-D)", "requires Pc and accelerometer data at >= 100 Hz in the FC"),
    }
    def ign_cost(prof, mean):
        x = ign[prof][f"mean{mean}"]
        return {"P_at_halfwidths_0_0.05_0.1_0.2_0.3": [rnd(v[1], 3) for v in x],
                "prop_used_kg": [rnd(v[2], 3) for v in x], "relight_alt_m": [rnd(v[3], 1) for v in x]}
    req["ignition"] = {
        "latency_cmd_to_90pct_max_s": P(0.5, "REQ ENG-04 (target 0.3 s)",
                                        "1-D closure is insensitive to latency 0.3-1.2 s when guidance plans on the worst case; the cost is relight altitude and propellant (see sweep). 0.5 s keeps the relight below ~30 m under drogue."),
        "repeatability_s": P(0.05, "REQ ENG-04 (+/-50 ms)", "1-D insensitive up to +/-0.3 s (worst-case planning); tighter spread lowers propellant cost and shortens the unpowered tail-first phase"),
        "latency_sweep": P({"A_drogue": {f"mean_{m}_s": ign_cost("A_drogue_300m", m) for m in [0.3, 0.5, 0.8, 1.2]},
                            "A_freefall": {f"mean_{m}_s": ign_cost("A_freefall_300m", m) for m in [0.3, 0.5, 0.8, 1.2]}},
                           f"SIM mc1d {SUF} (250 runs/point)"),
        "starts_per_flight_used": P({"A-D": 2, "B": 1, "tethered_hover": 1}, "SIM profiles"),
        "starts_per_flight_required": P(3, "REQ ENG-04", "one spare relight attempt"),
        "relight_conditions": P("liquid settled aft by drag (drogue: ~1 g); tank P >= 3.5 MPa; chamber purged; ignition commanded at the floor setting; drogue release only on Pc >= 50 % of floor Pc",
                                "DERIVED CONOPS"),
        "shutdown_tail_off": P("< 10 % thrust within 0.10 s", "REQ ENG-05", "simulated as tau_off 35 ms"),
    }
    req["gimbal"] = {
        "range_deg": P(7.0, "DERIVED tvc_analytic (mid pivot) - meets ENG-07 baseline +/-7 deg",
                       f"governing case: terminal descent at T~W in 11 m/s wind (8 m/s + gust), legs stowed, ADVERSE aero: "
                       f"{w11_mid['delta_aero_deg']:.1f} deg + trim {trim_mid:.1f} deg (5 mm CG offset, 0.25 deg misalignment) = {range_mid:.1f} deg; "
                       f"legs deployed: {w11_mid_l['delta_aero_deg']:.1f} deg. FORWARD pivot needs {range_fwd:.1f} deg -> +/-10 deg"),
        "range_deg_if_forward_pivot": P(10.0, "DERIVED tvc_analytic (forward pivot z 0.40 m)"),
        "rate_min_dps": P(60.0, "REQ ENG-07", "8 Hz small-signal at 1 deg amplitude needs 2 pi 8 x 1 = 50 deg/s; electronics.json v1 servo: 122 deg/s no-load, 60 deg/s at 9.8 N m"),
        "angular_accel_min_rad_s2": P(52.0, "DERIVED reach 60 deg/s within 20 ms"),
        "bandwidth_min_Hz": P(8.0, "REQ ENG-07", "attitude-loop crossover planned <= 1.5-2 Hz (6-DOF v2): actuator >= 4x crossover"),
        "resolution_max_deg": P(0.1, "REQ ENG-07", "electronics.json v1: 0.014 deg at the engine"),
        "backlash_max_deg": P(0.1, "DERIVED limit-cycle amplitude allowance (electronics.json v1: 0.029 deg with preload)"),
        "latency_cmd_to_motion_max_s": P(0.010, "DERIVED: 5 deg phase at 1.5 Hz crossover", "electronics.json v1: 7.7 ms max"),
        "hinge_moment_design_Nm": P({"mid_pivot": rnd(hb_mid["total_worst_linear_sum"], 2),
                                     "forward_pivot": rnd(hb_fwd["total_worst_linear_sum"], 2),
                                     "terms_mid": {k: rnd(v, 3) for k, v in hb_mid.items()},
                                     "terms_forward": {k: rnd(v, 3) for k, v in hb_fwd.items()}},
                                    "DERIVED tvc_analytic.hinge_budget (ASSUMED gimballed inertia; hose stiffness 2 N m/rad ASSUMED)",
                                    "linear worst-case sum; mechanical.json replaces the inertia/hose terms. electronics.json v1 assumed 11.7 N m (forward pivot)"),
        "actuator_stall_load_on_structure_Nm": P(rnd(4.413 * 7.0 * 0.9, 2) if elec else None,
                                                  "DERIVED electronics.json v1 Savox SB-2292SG 4.413 N m @ 8.4 V x lever 7 x eta 0.9",
                                                  "gimbal ring, pins, arms and pushrods must carry the actuator stall torque"),
    }
    # engine rocking mode (gimballed engine on actuator stiffness)
    Kst = None
    if elec:
        try:
            Kst = elec["actuators"]["tvc_A"]["stiffness"]["v"]["at_engine_Nm_per_rad"]
        except Exception:
            Kst = None
    I_piv_mid = hb_mid["I_pivot_kgm2"]
    I_piv_fwd = hb_fwd["I_pivot_kgm2"]
    rock = {}
    if Kst:
        rock = {"mid_pivot_Hz": [rnd(np.sqrt(k / I_piv_mid) / (2 * np.pi), 1) for k in Kst],
                "forward_pivot_Hz": [rnd(np.sqrt(k / I_piv_fwd) / (2 * np.pi), 1) for k in Kst]}
    req["structure"] = {
        "gimballed_engine_first_mode_min_Hz": P(25.0, "DERIVED ENG-11: >= 3 x actuator bandwidth (8 Hz)",
            f"rocking mode on actuator stiffness (electronics.json v1 2560-7681 N m/rad, linkage compliance excluded): {rock}. "
            "Forward pivot is marginal at the low-stiffness end -> another reason for the mid pivot"),
        "airframe_first_bending_min_Hz": P(10.0, "DERIVED >= 5 x attitude crossover (<= 2 Hz); goal 15 Hz", "Lauty to provide the airframe FE mode; notch filter if 10-15 Hz"),
        "tail_wags_dog_zero_min_rad_s": P(25.0, "DERIVED >= ~3 x attitude crossover at the floor thrust",
                                          f"mid pivot: {gim['mid_landing']['w_twd_floor']:.1f} rad/s at 100 N; forward pivot: {gim['forward_landing']['w_twd_floor']:.1f} rad/s (FAILS)"),
    }
    req["roll"] = {
        "decision": P("roll control REQUIRED unless the measured engine roll torque is <= 0.007 N m (A-D, 5.4 s burn) / <= 0.002 N m (100 m hop, 20.7 s burn)",
                      "DERIVED: roll impulse budget I_roll x 30 deg/s = 0.078 x 0.52 = 0.041 N m s (no aero roll damping on the finless body; roll rate from the ascent persists through the coast); touchdown roll rate <= 30 deg/s keeps the foot tangential speed <= 0.2 m/s at r 0.40 m"),
        "engine_roll_torque_estimate_Nm": P([0.01, 0.1], "DERIVED order-of-magnitude: helical-port swirl, mdot r_h v_ax tan(helix) (combustion.json v1 helix r 4 mm, pitch 50 mm)",
                                            "unverified - combustion to quantify; static-fire stand to measure roll torque"),
        "touchdown_roll_rate_max_dps": P(30.0, "DERIVED foot tangential speed"),
        "proposed_provider": P("N2O-vapour cold-gas roll thrusters from the tank ullage: 2 couples (4 nozzles) on 2 NC solenoids, >= 0.2 N m (2x worst estimate), ~30-60 g N2O per flight, ~0.25 kg hardware",
                               "DERIVED (REPORT option 3); provider: airframe/Lauty plumbing + electronics 2 extra low-side drivers; alternative: engine de-swirl vanes (combustion research proposal)"),
    }
    req["tank"] = {
        "temperature_at_liftoff_C": P([17.0, 23.0], "REQ ENG-12 (20 +/- 3 C)", "GNC Monte Carlo spans 15-25 C"),
        "n2o_load_A_D_kg": P(LOAD, "SIM sizing + MC margin (see reference_vehicle)"),
        "n2o_load_B_hop100_floor20_kg": P(2.35, "SIM sizing 2.06 kg x 1.15"),
        "fill_rule": P("liquid fraction <= 0.85 at 25 C", "ASSUMED (hydraulic-lock margin); Mechanical/Combustion to confirm"),
        "usable_liquid_reserve": P(0.20, "DERIVED sizing rule: usable liquid left >= 20 % of liquid used (nominal)"),
        "residual_liquid_frac": P(0.03, "ASSUMED outlet/dip-tube residual"),
    }
    req["navigation_and_loop_rates"] = {
        "fc_to_ecu_command_rate_Hz": P(500, "DERIVED/accepted electronics.json v1 (500 Hz CAN)"),
        "attitude_loop_rate_Hz": P(250, "ASSUMED (6-DOF v2 checks 100-500 Hz)"),
        "guidance_rate_Hz": P(50, "ASSUMED"),
        "altitude_error_1sigma_m_below_10m": P(0.05, "ASSUMED as simulated (LiDAR class); 6-DOF v2 sensor models"),
        "vertical_velocity_error_1sigma_mps": P(0.05, "ASSUMED as simulated"),
        "accelerometer_axial_bias_1sigma_mps2": P(0.10, "ASSUMED after pad calibration"),
        "imu_class": P("TBD in v2 (ADIS16470 vs BMI088/ICM-42688 comparison in the 6-DOF MC)", "open"),
        "link_loss_policy_in_RUN": P("ascent: SHUTDOWN after 0.1 s (backup chute); landing burn: HOLD last Pc setpoint and gimbal 0.3 s, then SHUTDOWN",
                                     "DERIVED answer to electronics.json v1 request (HOLD_N_S with N = 0.3 s in the landing phase)"),
    }

    out["requirements"] = req

    out["design_limit_loads"] = {
        "note": "LIMIT loads (expected maxima incl. dispersions). Mechanical applies ENG-10 factors (1.5 yield, 2.0 ultimate). Engine-mount values unless stated.",
        "axial_accel_flight_g": P(rnd(max(4.5, 1.1 * a_max_p999 / G0), 2), f"SIM mc1d (300 dispersed A-D runs: max {a_max_p999/G0:.2f} g; nominal {a_nom/G0:.2f} g at MECO) x1.1, min 4.5 g"),
        "axial_accel_landing_shock_g": P(10.0, "DERIVED 3 m/s off-nominal touchdown (1.5 x the 2 m/s criterion), 0.10 m leg stroke, 50 % stroke efficiency: v^2/(2 s eta) + 1 g",
                                         "duration ~30-60 ms; Lauty's leg design sets the real pulse - request"),
        "lateral_accel_flight_g": P(1.5, "DERIVED 7 deg gimbal at 500 N (0.5 g rigid) + body angular acceleration x arm to the engine (~0.6 g) + gusts, rounded up"),
        "lateral_accel_landing_g": P(3.0, "ASSUMED (0.5 m/s lateral + 5 deg tilt at contact, foot friction); 6-DOF touchdown model in v2"),
        "body_angular_rate_max_rad_s": P(1.0, "ASSUMED control-law limit (6-DOF v2 confirms)"),
        "body_angular_accel_max_rad_s2": P(rnd(500 * 0.437 * np.sin(np.radians(7.0)) / 3.1, 2), "DERIVED T l_p sin(7 deg) / I_t (mid pivot, 500 N, I_t 3.1 kg m2)"),
        "gimbal_angular_accel_actuator_max_rad_s2": P(rnd(4.413 * 7.0 * 0.9 / I_piv_mid, 0) if elec else None,
                                                      "DERIVED actuator stall torque / I_pivot (mid pivot) - transient the engine can be driven to"),
        "transport_handling_g": P(3.0, "ASSUMED any axis, gimbal locked by transport pins (request to Mechanical)"),
        "duty_cycle_loads": "time histories of F, a_axial, m, CG, inertia in every duty-cycle CSV",
    }

    out["duty_cycles"] = {
        "index": "01-systems-gnc/duty_cycles/duty_cycles_index_v1.json",
        "files": {c["name"]: {"file": "01-systems-gnc/duty_cycles/" + c["file"], "burn_s": rnd(c["burn_time_s"], 2),
                              "impulse_Ns": rnd(c["total_impulse_Ns"], 0), "starts": c["starts"],
                              "max_axial_specific_mps2": rnd(c.get("max_axial_specific_mps2"), 2)}
                  for c in dci["cycles"]},
        "columns": dci["cycles"][0]["columns"],
        "tag": "SIM sim1d (flights) / DERIVED commanded test sequences through the GNC engine model; gimbal columns zero in v1",
        "note": "longest single burn in flight: hop B1 20.7 s > ENG-06 15 s (hop is a test/fallback profile); A-D baseline 5.4 s in 2 starts; static-fire qualification DC-D 49 s with 3 starts",
    }

    out["landing_closure"] = {
        "cases": closure,
        "tag": f"SIM mc1d {SUF} (1-D vertical; dispersions per brief C.7; success |v_td| <= 2 m/s and no exhaustion)",
        "hoverslam_vs_hover": "floors 12.5/20 %: forced hoverslam and hover-capable give the same 1-D P (hoverslam uses ~2-5 % more N2O); 25/40 %: RV-1 cannot hover (T_floor > 0.9 W) - hoverslam P vs hover-with-ballast P in cases",
        "failure_evidence": "v1 (no thrust estimator, cut needing h_nav > 3 cm): hoverslam P 0.92 at 25 %, 0.62-0.78 at 40 % (stopping aloft, then falling). Kept in landing_closure_mc1d_v1/v1p1 files.",
    }
    out["lift_capability"] = {
        "TW_vs_liftoff_mass": P({f"{m}_kg": rnd(500.0 / (m * G0), 2) for m in [12, 13, 15, 17, 20, 25.5, 34, 51]},
                                "DERIVED T/W = 500 N / (m g0)"),
        "liftoff_TW_min": P(2.0, "ASSUMED design rule for rail-less TVC liftoff with 8 m/s wind (6-DOF v2 to confirm)",
                            "-> max liftoff mass ~25.5 kg; hover-only limit (T = W) 51 kg"),
        "payload_or_ballast_trade_300m_A_D": P([x for x in lift if x["profile"] == "A_drogue_300m"],
                                              f"SIM sizing {SUF} (20 % floor, 20 % reserve)", "ballast_kg = mass added to RV-1"),
        "answer": "500 N lifts RV-1 (13 kg) at T/W 3.9; adding ~5 kg payload keeps T/W 2.7 and closes the 300 m A-D profile with ~1.9 kg N2O; ~12 kg added mass reaches the T/W 2 limit (needs ~3.5 kg N2O, ~5 L tank).",
    }
    out["requests"] = [
        "REQUEST combustion: engine roll torque vs throttle from the helical port (estimate 0.01-0.1 N m) and a de-swirl option; throttle map vs port diameter and tank pressure in combustion.json (F, mdot_ox, mdot_f, Pc, Isp) for the GNC engine model v2; ignition-delay distribution (mean, spread) for the torch; tail-off time constant; thrust ceiling vs tank temperature with the pintle (ceiling rule Pc <= P_inlet/1.25).",
        "REQUEST mechanical: gimballed mass, CG and inertia about the pivot; pivot station (GNC prefers mid pivot near the gimballed CG, z ~0.23 m in RV-1 stations); hose torsional/bending stiffness; engine rocking mode with linkage compliance (>= 25 Hz); transport lock; tank length/volume for 1.30 kg (2.06 L).",
        "REQUEST electronics: FC IMU/LiDAR/GNSS selection after the 6-DOF sensor trade (v2); 2 extra NC-solenoid low-side drivers for roll thrusters; landing-phase link-loss policy HOLD 0.3 s; Pc and accelerometer at >= 100 Hz to the FC for thrust-effectiveness estimation.",
        "REQUEST lead: decide the throttle-floor requirement (GNC derives <= 20 % for RV-1 hover-capable landing; ENG-02 says 25 %); confirm A-D baseline profile; roll-control ownership.",
        "REQUEST airframe (Lauty): leg stroke and efficiency (0.10 m / 50 % assumed), airframe first bending mode (>= 10 Hz), drogue + release + swivel at the nose, CG range below.",
    ]
    out["icd_inputs_for_airframe"] = {
        "landing_mass_window_kg": P({"floor_12.5%": [7.1, 16.0], "floor_20%": [11.3, 16.0], "floor_25%": [14.2, 16.0],
                                     "floor_40%": "none below 22.7 kg (hoverslam or ballast)"},
                                    "DERIVED hover rule m >= F_floor/(0.9 g0); upper bound REQ ref. vehicle 16 kg"),
        "cg_range_z_m": P({"flight_history_RV1": [rnd(min(float(s["z_cg_m"]) for s in states), 3), rnd(max(float(s["z_cg_m"]) for s in states), 3)],
                           "ledger_extremes": [rnd(cg_aft_ext, 3), rnd(cg_fwd_ext, 3)],
                           "liquid_forward_excursion_m": rnd(o_fwd[1] - o_aft[1], 3)},
                          "SIM DC-A1 (RV-1 stations) + DERIVED ledger min/max extremes (all items at min/max pushing the CG aft/forward)"),
        "touchdown_vertical_speed_max_mps": P(2.0, "REQ"), "touchdown_lateral_speed_max_mps": P(0.5, "REQ"),
        "touchdown_tilt_max_deg": P(5.0, "REQ brief"), "touchdown_tilt_rate_max_dps": P(10.0, "REQ brief"),
        "leg_stroke_min_m": P(0.10, "ASSUMED (drives the 10 g landing-shock limit)"),
        "drogue_CdA_m2": P(0.5, "DERIVED descent ~19-21 m/s at 12-13 kg (A-D baseline)"),
    }
    out["open_items"] = [
        "6-DOF Monte Carlo (attitude, lateral, wind/gusts, sensors, TVC actuator, slosh, touchdown) -> gimbal range/rate confirmation, miss distance, tilt/rate at touchdown (v2).",
        "Engine model v2 from combustion.json v1 (eps 2, helical port, Isp map 199 s max, 133 s at 12.5 %); re-size loads and regenerate duty cycles.",
        "Tail-first aerodynamics unknown to ~x2 (CFD request to 05-plume-cfd).",
        "Engine roll torque unknown (order 0.01-0.1 N m estimate) -> roll control decision.",
        "Ignition reliability at relight is mission-critical for A-D (no time for a backup main chute after a failed relight at ~25 m).",
        "Hoverslam robustness in 6-DOF (no hover margin for lateral/tilt corrections at 25/40 % floors).",
    ]
    os.makedirs(os.path.join(OUT, "gnc_json"), exist_ok=True)
    with open(os.path.join(OUT, "gnc_json", "gnc_v1.json"), "w") as f:
        json.dump(out, f, indent=1, default=lambda o: float(o) if isinstance(o, np.floating) else str(o))
    print("written", os.path.join(OUT, "gnc_json", "gnc_v1.json"))
    print("t10-90 sim threshold", t1090_sim, "slew ok", slew_ok, "range mid/fwd", range_mid, range_fwd, "rock", rock,
          "a_max", a_max_p999 / G0)


if __name__ == "__main__":
    main()
