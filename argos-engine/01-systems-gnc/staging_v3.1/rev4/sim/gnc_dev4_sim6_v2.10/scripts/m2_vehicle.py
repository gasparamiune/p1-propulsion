"""RV-1c reference vehicle outputs (vehicle v3c for gnc.json v2; v3d for gnc.json v3 with mechanical.json v2).

Mass ledger (mechanical.json engine module + ASSUMED airframe), mass properties versus propellant state and
versus mission events (nominal 6-DOF A-D flight), CG range, all-attitude aero coefficients with uncertainty
bands (nose-first and tail-first, legs, fins), tail-wags-dog / control-moment table at the CG pivot, and a
station layout figure.

Outputs (GNC_VEH_OUT, default /home/claude/work/space/out/vehicle):
  mass_ledger_<TAG>.csv/.json, massprops_vs_propellant_<TAG>.csv, massprops_events_<TAG>.csv,
  aero_static_<SUFFIX>.csv, twd_table_<SUFFIX>.csv, vehicle_<TAG>.json, vehicle_layout_<TAG>.png, aero_static_<SUFFIX>.png,
  massprops_<TAG>.png   (TAG = GNC_VEH_TAG, default v3c; SUFFIX = GNC_SUFFIX, default v2)
Run: nice -n 10 python scripts/m2_vehicle.py   (reads GNC_IFACE interface files, GNC_OUT/mc6_summary_<SUFFIX>.json)
v1.1 (2026-10-12, gnc.json v3): env GNC_VEH_BASE (JSON dict of run6 config overrides merged into the A-D baseline, or '@dc_v3_A1' for the
DC-A1 v3 configuration of m2_duty_cycles_v3: rcs off, v3 flight software, as-drawn actuator chain) and GNC_VEH_M (fixed N2O load [kg], e.g. the lead tank 2.00 kg) for vehicle v3d;
without them the behaviour is that of v1 (v3c).
v1.2 (2026-10-13): GNC_VEH_DATE (run date in the outputs); vehicle v3d re-run on DC-A1 v3 with the relight placeholder
(lead decision 2026-10-13: 0.8 + 0.3 s on the start delay and on the planning value).
"""
import csv
import json
import os
import sys
import numpy as np
import CoolProp.CoolProp as CP

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, sim6 as s6, vehicle as veh, aero  # noqa: E402

OUT = os.environ.get("GNC_VEH_OUT", "/home/claude/work/space/out/vehicle")
MC_OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/m2")
SUFFIX = os.environ.get("GNC_SUFFIX", "v2")
VTAG = os.environ.get("GNC_VEH_TAG", "v3c")   # vehicle/ledger tag in the file names (v3d: mechanical.json v2)
os.makedirs(OUT, exist_ok=True)
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
DATE = os.environ.get("GNC_VEH_DATE", "2026-10-12")   # v1.2: date of the run (vehicle v3d re-run 2026-10-13 on DC-A1 v3 with the relight placeholder)
# aero uncertainty sets (factors of aero.build_aero_params; ranges = the MC dispersions of run6.draw)
AERO_SETS = {
    "nominal": dict(k_base_lead=0.75, k_nose_trail=0.25, crossflow=1.0, legs=1.0, ca_nf=1.0, ca_tf=1.0, k_retro=0.5),
    "benign_tail_first": dict(k_base_lead=0.5, k_nose_trail=0.0, crossflow=1.25, legs=1.0, ca_nf=0.7, ca_tf=0.7,
                              k_retro=0.25),
    "adverse_tail_first": dict(k_base_lead=1.0, k_nose_trail=0.5, crossflow=0.75, legs=1.0, ca_nf=1.3, ca_tf=1.3,
                               k_retro=0.75),
}
ALPHAS = [0, 1, 2, 5, 10, 20, 30, 45, 60, 90, 120, 135, 150, 160, 170, 175, 178, 179, 180]


def rnd(x, n=4):
    return float(round(float(x), n))


def wcsv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)


def split_sat(m_tot, V, T):
    """Saturated N2O at T in volume V: liquid and vapour masses (equilibrium, no wall/ullage gas)."""
    rl = CP.PropsSI("D", "T", T, "Q", 0, "NitrousOxide")
    rv = CP.PropsSI("D", "T", T, "Q", 1, "NitrousOxide")
    ml = (m_tot - rv * V) / (1.0 - rv / rl)
    ml = min(max(ml, 0.0), m_tot)
    return ml, m_tot - ml, rl


def massprops(mp, ml, mv, rl, mf, liquid_forward=False):
    o = np.zeros(8)
    veh.massprops(mp, ml, mv, rl, mf, o)
    if liquid_forward and ml > 0:
        A = mp[veh.MP_TAIN]
        h = min(ml / (rl * A), mp[veh.MP_TLIN])
        dz = mp[veh.MP_TLIN] - h
        m = o[0]
        zc_new = o[1] + ml * dz / m
        zl_aft = mp[veh.MP_TZB] + 0.5 * h
        zl_fwd = zl_aft + dz
        It = o[2] + m * o[1] ** 2 - m * zc_new ** 2 + ml * (zl_fwd ** 2 - zl_aft ** 2)
        o[1], o[2] = zc_new, It
    return o


def slope(apar, comp, zc, a0, da=1.0):
    sc = aero.static_coefficients(apar, comp, zc, [a0, a0 + da])
    return (sc[1, 1] - sc[0, 1]) / np.radians(da), sc[1, 4]


def main():
    src = R.sources()
    comb, el, mech = src["comb"], src["el"], src["mech"]
    # ---------------------------------------------------------------- baseline configuration and load
    m_mc = None
    p_mc = os.path.join(MC_OUT, f"mc6_summary_{SUFFIX}.json")
    if os.path.exists(p_mc):
        try:
            m_mc = json.load(open(p_mc))["cases"]["AD_fins_f20"]["m_n2o_mc_kg"]
        except (KeyError, ValueError):
            m_mc = None
    base = dict(profile="A-D", fins=True, floor=0.20)
    vb_ = os.environ.get("GNC_VEH_BASE", "{}")                            # v1.1 (vehicle v3d: rcs off, v3 flight software)
    if vb_ == "@dc_v3_A1":
        # the DC-A1 v3 configuration of m2_duty_cycles_v3 (no numbers of other disciplines typed here)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import m2_duty_cycles_v3 as DC3
        base.update({k: v for k, v in DC3.CYCLES[0][1].items() if k not in ("profile", "fins", "floor")})
    else:
        base.update(json.loads(vb_))
    if os.environ.get("GNC_VEH_M"):
        m_mc = float(os.environ["GNC_VEH_M"])                                # v1.1 (vehicle v3d: lead tank 2.00 kg)
    if m_mc is None:
        m_s, _ = R.size_load(R.cfg_of(**base))
        m_mc = m_s * 1.15
    cfg = R.cfg_of(**dict(base, m_n2o=m_mc))
    par, apar, comp, mp, tab, info = R.build(cfg)
    geo, led, V = info["geo"], info["ledger"], info["tank_V"]
    # grain of the engine model actually flown (the relay S230 grain while combustion.json v1 is published; the published
    # grain otherwise). vehicle v3c (gnc.json v2) used the published v1 grain (0.351 kg) here while the 6-DOF flew the relay
    # grain (0.404 kg): fixed for v3d, the effect on v3c is recorded in results (vehicle_v3c_grain_fix).
    comb_fly = R.engine_sources(cfg)[0]
    m_fuel0 = comb_fly["gas_path"]["grain"]["mass_kg"]["v"]
    T0 = 293.15

    # ---------------------------------------------------------------- mass ledger
    rows = veh.ledger_table(led)
    wcsv(os.path.join(OUT, f"mass_ledger_{VTAG}.csv"), rows)
    m_dry = sum(i["m"] for i in led)
    sums = dict(dry_kg=m_dry, dry_min_kg=sum(i["m_min"] for i in led), dry_max_kg=sum(i["m_max"] for i in led),
                propulsion_kg=sum(i["m"] for i in led if i["owner"] == "propulsion"),
                airframe_kg=sum(i["m"] for i in led if i["owner"] == "airframe"),
                gimballed_dry_kg=sum(i["m"] for i in led if i["gimballed"]), fuel_grain_kg=m_fuel0,
                n2o_load_kg=m_mc, tank_V_L=V * 1e3)
    json.dump(dict(version=f"mass_ledger_{VTAG}", date=DATE, vehicle="RV-1c (A-D configuration: drogue, aft fins, " + ("roll RCS" if base.get("rcs", True) else "roll RCS provision only, not fitted") + ")", config=base,
                   ledger_code=veh.LEDGER_VERSION, mechanical_json=mech.get("version"),
                   frame="stations z [m] from the airframe aft datum (base plane), +z toward the nose; "
                         "pivot station from mechanical.json frames.rv1_station_of_pivot_m",
                   geometry={k: geo[k] for k in ["d", "d_id", "wall", "z_base", "z_body_top", "z_tip", "L_nose", "z_pivot",
                                                 "tank_z_bot_inner", "tank_D_in", "z_foot", "r_foot"]},
                   items=led, sums=sums), open(os.path.join(OUT, f"mass_ledger_{VTAG}.json"), "w"), indent=1, default=float)

    # ---------------------------------------------------------------- mass properties vs propellant state
    mpv = []
    for fl in [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.03, 0.0]:
        for ff, flab in [(1.0, "full"), (0.5, "half"), (0.0, "burnt")]:
            m_tot = fl * m_mc
            ml, mv, rl = split_sat(m_tot, V, T0)
            for fwd in (False, True):
                if fwd and ml <= 0:
                    continue
                o = massprops(mp, ml, mv, rl, ff * m_fuel0, liquid_forward=fwd)
                mpv.append(dict(n2o_frac_of_load=fl, n2o_kg=rnd(m_tot, 4), liquid_kg=rnd(ml, 4), vapour_kg=rnd(mv, 4),
                                fuel_state=flab, fuel_kg=rnd(ff * m_fuel0, 4),
                                liquid_position="forward" if fwd else "aft (settled)", m_kg=rnd(o[0], 4),
                                z_cg_m=rnd(o[1], 4), I_transverse_kgm2=rnd(o[2], 4), I_roll_kgm2=rnd(o[3], 5),
                                m_gimballed_kg=rnd(o[4], 4), z_cg_gimballed_m=rnd(o[5], 4),
                                I_gimballed_own_cg_kgm2=rnd(o[6], 5)))
    wcsv(os.path.join(OUT, f"massprops_vs_propellant_{VTAG}.csv"), mpv)

    # ---------------------------------------------------------------- mission events (nominal 6-DOF A-D, no wind)
    res, rec, inf2 = R.fly(R.cfg_of(**dict(base, m_n2o=m_mc, noise=False, wind=0.0, gust=False, rec_dt=0.01)),
                           nrec=12000)
    ph = rec[:, I["phase"]]
    t = rec[:, I["t"]]
    z0 = rec[0, I["z"]]

    def first(cond):
        k = int(np.argmax(cond)) if np.any(cond) else len(cond) - 1
        return k
    kt = first(t >= res["td_t"]) if res["landed"] > 0.5 else len(t) - 1
    ev = {"liftoff": 0, "MECO": first(ph >= 2), "apogee": first(ph >= 3), "relight_command": first(ph >= 4),
          "landing_burn_start": first(ph >= 5), "terminal_gate": first(ph >= 6), "touchdown": kt}
    events = []
    for k, i in ev.items():
        events.append(dict(event=k, t_s=rnd(t[i], 3), h_cg_above_liftoff_m=rnd(rec[i, I["z"]] - z0, 2),
                           vz_mps=rnd(rec[i, I["vz"]], 2), F_N=rnd(rec[i, I["F"]], 1), m_kg=rnd(rec[i, I["m"]], 3),
                           z_cg_m=rnd(rec[i, I["zcg"]], 4), I_transverse_kgm2=rnd(rec[i, I["It"]], 4),
                           I_roll_kgm2=rnd(rec[i, I["Ir"]], 5), liquid_kg=rnd(rec[i, I["mliq"]], 3),
                           fuel_kg=rnd(rec[i, I["mfuel"]], 4), P_tank_Pa=rnd(rec[i, I["Ptank"]], 0),
                           T_tank_K=rnd(rec[i, I["Ttank"]], 2)))
    wcsv(os.path.join(OUT, f"massprops_events_{VTAG}.csv"), events)
    zc_hist = rec[: kt + 1, I["zcg"]]
    zc_land = float(rec[kt, I["zcg"]])
    zc_lift = float(rec[0, I["zcg"]])
    m_land = float(rec[kt, I["m"]])

    # ledger extremes (landing state, dry items at min/max pushing the CG one way)
    zc_nom = sum(i["m"] * i["z"] for i in led) / m_dry

    def cg_ext(fwd):
        num = den = 0.0
        for i in led:
            hi = (i["z"] > zc_nom) == fwd
            mm = i["m_max"] if hi else i["m_min"]
            num += mm * i["z"]
            den += mm
        return num / den
    ml_full, mv_full, rl_full = split_sat(m_mc, V, T0)
    o_aft = massprops(mp, ml_full, mv_full, rl_full, m_fuel0)
    o_fwd = massprops(mp, ml_full, mv_full, rl_full, m_fuel0, liquid_forward=True)
    # liquid at MECO (coast): the excursion that matters for the nose-first coast
    i_meco = ev["MECO"]
    ml_m = float(rec[i_meco, I["mliq"]])
    o_meco_aft = massprops(mp, ml_m, 0.0, rl_full, float(rec[i_meco, I["mfuel"]]))
    o_meco_fwd = massprops(mp, ml_m, 0.0, rl_full, float(rec[i_meco, I["mfuel"]]), liquid_forward=True)
    cg = dict(flight_history_m=[rnd(zc_hist.min()), rnd(zc_hist.max())], liftoff_m=rnd(zc_lift), landing_m=rnd(zc_land),
              ledger_extremes_dry_m=[rnd(cg_ext(False)), rnd(cg_ext(True))], dry_nominal_m=rnd(zc_nom),
              liquid_forward_excursion_full_m=rnd(o_fwd[1] - o_aft[1]),
              liquid_forward_excursion_meco_m=rnd(o_meco_fwd[1] - o_meco_aft[1]), meco_liquid_kg=rnd(ml_m, 3))

    # ---------------------------------------------------------------- aero with uncertainty bands
    a_rows = []
    aero_sum = {}
    for fins in (True, False):
        g2 = veh.reference_geometry_v3(legs="deployable", comb=comb_fly, mech=mech, fins=fins)
        for lab, unc in AERO_SETS.items():
            ap, cp = aero.build_aero_params(dict(g2, drogue_CdA=0.0), unc)
            for legs in (0.0, 1.0):
                ap2 = ap.copy()
                ap2[aero.A_LEGS_DEPLOYED] = legs
                for zc_lab, zc in (("liftoff", zc_lift), ("landing", zc_land)):
                    sc = aero.static_coefficients(ap2, cp, zc, ALPHAS)
                    for a, CN, CA, Cm, zcp in sc:
                        a_rows.append(dict(fins=int(fins), set=lab, legs_deployed=int(legs), cg_state=zc_lab, z_cg_m=rnd(zc),
                                           alpha_deg=a, CN=rnd(CN), CA=rnd(CA), Cm_about_cg_ref_d=rnd(Cm),
                                           z_cp_m=rnd(zcp) if np.isfinite(zcp) else ""))
            # small-angle slopes and static margins (positive = statically stable in that direction of flight)
            for legs in (0.0, 1.0):
                ap2 = ap.copy()
                ap2[aero.A_LEGS_DEPLOYED] = legs
                cna_nf, zcp_nf = slope(ap2, cp, zc_lift, 0.0, 2.0)
                cna_tf, zcp_tf = slope(ap2, cp, zc_land, 180.0, -2.0)    # dCN/dalpha near 180 (v1 convention), CP at 178
                _, zcp_tf10 = slope(ap2, cp, zc_land, 172.0, -2.0)       # CP at 170 deg (10 deg off the tail-first axis)
                d = g2["d"]
                aero_sum[f"fins{int(fins)}_{lab}_legs{int(legs)}"] = dict(
                    CNa_nose_first_per_rad=rnd(cna_nf), z_cp_nose_first_2deg_m=rnd(zcp_nf),
                    static_margin_nose_first_cal=rnd((zc_lift - zcp_nf) / d, 3),
                    CNa_tail_first_per_rad=rnd(cna_tf), z_cp_tail_first_2deg_m=rnd(zcp_tf),
                    static_margin_tail_first_cal=rnd((zcp_tf - zc_land) / d, 3),
                    z_cp_tail_first_10deg_m=rnd(zcp_tf10),
                    static_margin_tail_first_10deg_cal=rnd((zcp_tf10 - zc_land) / d, 3),
                    CA_nose_first=rnd(ap2[aero.A_CA0_NF]), CA_tail_first=rnd(ap2[aero.A_CA0_TF]),
                    CA_legs_increment=rnd(ap2[aero.A_CA_LEGS]), d_m=d)
    wcsv(os.path.join(OUT, f"aero_static_{SUFFIX}.csv"), a_rows)

    # ---------------------------------------------------------------- tail-wags-dog / control moment table
    twd = []
    zp = geo["z_pivot"]
    states = {"liftoff": (ml_full, mv_full, m_fuel0)}
    for e in ("MECO", "relight_command", "touchdown"):
        i = ev[e]
        states[e] = (float(rec[i, I["mliq"]]), 0.0, float(rec[i, I["mfuel"]]))
    for st, (ml, mv, mf) in states.items():
        o = massprops(mp, ml, mv, rl_full, mf)
        l_p = o[1] - zp
        m_e, z_e, I_e = o[4], o[5], o[6]
        l_e = zp - z_e
        J = I_e + m_e * l_e * (l_e + l_p)
        for F in (62.5, 100.0, 125.0, 0.0, 250.0, 500.0):
            Fx = F if F > 0 else o[0] * R.G0      # 0 -> hover thrust in this state
            w = np.sqrt(Fx * l_p / J) if J > 0 and l_p > 0 else float("nan")
            twd.append(dict(state=st, F_N=rnd(Fx, 1), F_label="hover (T=W)" if F == 0 else f"{F/5:.1f} %",
                            m_kg=rnd(o[0]), z_cg_m=rnd(o[1]), l_p_m=rnd(l_p), m_e_kg=rnd(m_e), z_e_m=rnd(z_e),
                            l_e_m=rnd(l_e, 5), I_e_own_kgm2=rnd(I_e, 5), J_twd_kgm2=rnd(J, 5), w_twd_rad_s=rnd(w, 2),
                            Mc_per_deg_Nm=rnd(Fx * l_p * np.sin(np.radians(1.0))),
                            Mc_at_7deg_Nm=rnd(Fx * l_p * np.sin(np.radians(7.0))),
                            ang_acc_at_7deg_rad_s2=rnd(Fx * l_p * np.sin(np.radians(7.0)) / o[2]),
                            I_transverse_kgm2=rnd(o[2])))
    wcsv(os.path.join(OUT, f"twd_table_{SUFFIX}.csv"), twd)

    # ---------------------------------------------------------------- summary json
    summ = dict(version=f"vehicle {VTAG}", date=DATE, vehicle="RV-1c", config=base, ledger=veh.LEDGER_VERSION, sim=s6.SIM6_VERSION,
                mechanical_json=mech.get("version"), combustion_json=comb.get("version"), electronics_json=el.get("version"),
                engine_model=info["tags"]["engine_model"][1], grain_kg_in_tables=m_fuel0,
                d_body_m=geo["d"], d_id_m=geo["d_id"], z_pivot_m=zp, n2o_load_kg=m_mc, tank_V_L=V * 1e3,
                tank_internal_length_m=V / (np.pi * geo["tank_D_in"] ** 2 / 4), m_liftoff_kg=float(rec[0, I["m"]]),
                m_land_nominal_kg=m_land, sums=sums, cg=cg, aero=aero_sum, events=events,
                nominal_flight={k: float(res[k]) for k in ["landed", "td_vz", "td_vh", "td_tilt", "h_max", "t_meco", "v_meco",
                                                           "h_ign", "v_ign", "burn_time", "prop_used", "m_land", "starts"]})
    json.dump(summ, open(os.path.join(OUT, f"vehicle_{VTAG}.json"), "w"), indent=1, default=float)

    # ---------------------------------------------------------------- figures
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    # layout
    fig, ax = plt.subplots(figsize=(11, 3.6))
    r = geo["d"] / 2
    ax.add_patch(plt.Rectangle((geo["z_base"], -r), geo["z_body_top"] - geo["z_base"], 2 * r, fc="none", ec="k"))
    ax.plot([geo["z_body_top"], geo["z_tip"], geo["z_body_top"]], [r, 0, -r], "k-")
    rt = geo["tank_D_in"] / 2
    L_in = V / (np.pi * rt * rt)
    ax.add_patch(plt.Rectangle((geo["tank_z_bot_inner"], -rt), L_in, 2 * rt, fc="#cfe3f7", ec="#2b6cb0", label="N2O tank"))
    if geo.get("z_exit_mech") is not None:
        ax.add_patch(plt.Rectangle((geo["z_exit_mech"], -0.035), geo["z_head_top"] - geo["z_exit_mech"], 0.07,
                                   fc="#f7d9c4", ec="#c05621", label="gimballed engine (mechanical.json)"))
    ax.axvline(zp, color="#c05621", ls=":", lw=1)
    ax.text(zp, r + 0.012, "pivot", ha="center", fontsize=8, color="#c05621")
    for lab, zc, col in (("CG liftoff", zc_lift, "g"), ("CG landing", zc_land, "b")):
        ax.plot(zc, 0, marker="o", color=col)
        ax.text(zc, -r - 0.03, lab, ha="center", fontsize=8, color=col)
    sn = aero_sum["fins1_nominal_legs0"]
    ax.plot(sn["z_cp_nose_first_2deg_m"], 0, marker="x", color="m", ms=9)
    ax.text(sn["z_cp_nose_first_2deg_m"], r + 0.03, "CP nose-first\n(fins, 2 deg)", ha="center", fontsize=8, color="m")
    for i in led:
        if i["shape"] == "point":
            ax.plot(i["z"], 0.6 * r, marker="|", color="0.4")
    ax.plot([geo["z_foot"], geo["z_base"] + 0.1], [-geo["r_foot"] * 0.25, -r], color="0.3")
    ax.plot([geo["z_foot"], geo["z_base"] + 0.1], [geo["r_foot"] * 0.25, r], color="0.3")
    ax.set_xlim(-0.35, 2.1)
    ax.set_ylim(-0.16, 0.16)
    ax.set_aspect("equal")
    ax.set_xlabel("station z [m] from the aft datum (+z to the nose); legs drawn schematically (foot radius 0.40 m)")
    ax.set_title(f"RV-1c reference vehicle (ASSUMED airframe, mechanical.json {mech.get('version')} engine module): "
                 f"d {geo['d']*1e3:.0f} mm, m0 {rec[0, I['m']]:.2f} kg, landing {m_land:.2f} kg")
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, f"vehicle_layout_{VTAG}.png"), dpi=130)
    plt.close(fig)
    # aero
    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    for lab, ls in (("nominal", "-"), ("benign_tail_first", "--"), ("adverse_tail_first", ":")):
        for fins, col in ((1, "C0"), (0, "C3")):
            sel = [x for x in a_rows if x["fins"] == fins and x["set"] == lab and x["legs_deployed"] == 0
                   and x["cg_state"] == "landing"]
            a = [x["alpha_deg"] for x in sel]
            axs[0].plot(a, [x["CN"] for x in sel], ls=ls, color=col, label=f"{'fins' if fins else 'finless'} {lab}")
            axs[1].plot(a, [x["Cm_about_cg_ref_d"] for x in sel], ls=ls, color=col)
    axs[0].set_xlabel("alpha [deg] (0 nose-first, 180 engine-first)")
    axs[0].set_ylabel("CN (ref. area pi d^2/4)")
    axs[1].set_xlabel("alpha [deg]")
    axs[1].set_ylabel("Cm about the landing CG (ref. d); restoring if dCm/dalpha < 0")
    axs[0].legend(fontsize=7)
    for a_ in axs:
        a_.grid(alpha=0.3)
    fig.suptitle("RV-1c static aero, legs stowed: component build-up, uncertainty sets (tail-first UNKNOWN to ~x2)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, f"aero_static_{SUFFIX}.png"), dpi=130)
    plt.close(fig)
    # mass properties vs propellant
    fig, axs = plt.subplots(1, 3, figsize=(12, 3.6))
    for flab, ls in (("full", "-"), ("burnt", "--")):
        for pos, col in (("aft (settled)", "C0"), ("forward", "C1")):
            sel = [x for x in mpv if x["fuel_state"] == flab and x["liquid_position"] == pos]
            n = [x["n2o_kg"] for x in sel]
            axs[0].plot(n, [x["m_kg"] for x in sel], ls=ls, color=col)
            axs[1].plot(n, [x["z_cg_m"] for x in sel], ls=ls, color=col, label=f"fuel {flab}, liquid {pos}")
            axs[2].plot(n, [x["I_transverse_kgm2"] for x in sel], ls=ls, color=col)
    axs[0].set_ylabel("m [kg]")
    axs[1].set_ylabel("z_cg [m]")
    axs[2].set_ylabel("I_transverse about CG [kg m2]")
    for a_ in axs:
        a_.set_xlabel("N2O in tank [kg]")
        a_.grid(alpha=0.3)
    axs[1].legend(fontsize=7)
    fig.suptitle("RV-1c mass properties vs propellant state (DERIVED vehicle.massprops, ledger " + VTAG + ")")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, f"massprops_{VTAG}.png"), dpi=130)
    plt.close(fig)
    print(json.dumps(dict(sums=sums, cg=cg, m_liftoff=summ["m_liftoff_kg"], m_land=m_land,
                          tank_L=summ["tank_internal_length_m"],
                          aero={k: aero_sum[k] for k in ["fins1_nominal_legs0", "fins0_nominal_legs0", "fins1_adverse_tail_first_legs1"]}),
                     indent=1, default=float))
    for x in twd:
        if x["F_label"] in ("12.5 %", "20.0 %", "hover (T=W)"):
            print(x["state"], x["F_label"], x["w_twd_rad_s"], x["l_p_m"], x["l_e_m"], x["J_twd_kgm2"])


if __name__ == "__main__":
    main()
