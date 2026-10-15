"""run6 v2.9-dev (v2.9-dev amendments G (decided purge sequence and trigger gate pgg_*), K (freeze on Pc invalid kfz_on) and V (Pc invalid inside [E2, release], release alternatives pcf_*); v2.8-dev amendments M (flown mass estimator mest_*, kest_comp), W (fuel-web state web_*, burn-limit action web_act, B apex predictor on Pc bpred_pc) and F (stuck-pintle fault flt_*, in-loop detectors det_* / fct_*, abort abt_*, geofence proposal geo_dh) and P (A-relight forced purge prg_*, stuck-open bleed fault blf_*, bleed jet bl_vj / bl_az) and R (drogue release rule rel_mode / rel_Pc / rel_dt) and S (A-relight start plateau st_on / st_Pc / st_T, release persistence branch rel_to / rel_rise_Pc): parameters passed to sim6, off by default; v2.7.1-dev: regression-law band reg_band / reg_a / reg_n (gncsim.regband, own generator seed 20261017) and relight start-delay quantile table t_ign_q (own generator seed 20261018; nominal flight at the table median); v2.7: throat growth throat_g / throat_jref / throat_g_band / throat_loop (own generator seed 20261013), k_est_asc, floor_comp_min; v2.6: sim6 v2.6 flight-software options - gimbal command tracker, attitude reference governor, lift-ramp
shutdown (gncsim.tailoff), pre-MECO throttle-down, relight start rule, start-delay shift, ENG-07d notch fixed or tracking the
run's own rocking mode, engine-axis stiffness range override for the MC, wet engine inertia about the pivot override, start-delay shift also on the
nominal (sizing) flight; v2.5.2: S230 growth also when combustion.json v2.x flies on mechanical.json v1; v2.5.1: combustion v2
map reader promoted; act_model/servo_V/act_n/act_Jint/supply_chain/supply_Vrest for sim6 v2.5; rot_int for sim6 v2.4; t_hand for sim6 v2.3; combustion v2 relay engine model, roll_amp): build sim6 parameter vectors from the interface JSON + tagged GNC assumptions; nominal
flights, propellant sizing on the 6-DOF, Monte Carlo with the brief C.7 dispersions.

Sources read at run time (never hard-coded): interfaces/combustion.json (throttle map, grain, gas path,
ignition timing), interfaces/electronics.json (servo datasheet values, TVC loop dynamics, latencies),
interfaces/mechanical.json (pivot station, gimballed-engine mass properties, gimbal ring, linkage ratio,
backlash/resolution at the engine, hose stiffness, friction, conical stop, engine-bay ID).
Vehicle RV-1c (default) = RV-1b + mechanical.json engine module + 140 mm bay ID (founder decision 2026-10-12, final);
RV-1b (cfg vehicle="RV-1b") is kept for comparison with the gnc.json v1 / pre-mechanical runs.
Every parameter set by this module is recorded with a tag in `info["tags"]`.
"""
import json
import os
import numpy as np
import CoolProp.CoolProp as CP
from . import sim6 as s6
from . import engine_v2
from . import vehicle as veh
from . import aero
from .sizing import tank_volume_for
from . import tailoff
from . import regband

IFACE = os.environ.get("GNC_IFACE", "/mnt/project-files/engine/interfaces")  # lead fallback hub during mount outages
G0 = 9.80665
_C = {}


SNAP = engine_v2.SNAP


def snapshot():
    """Copy the interface files used by the 6-DOF (and the throttle-map CSV) to a local snapshot with
    a manifest (sha256, size), so long Monte Carlo runs survive shared-mount outages. Returns manifest."""
    import hashlib
    import shutil
    os.makedirs(SNAP, exist_ok=True)
    man = {}
    names = ["combustion.json", "electronics.json", "mechanical.json", "ENGINE-BASELINE-v0.json"]
    for n in names:
        p = os.path.join(IFACE, n)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(SNAP, n))
    comb = json.load(open(os.path.join(SNAP, "combustion.json")))
    mp_ = comb["operating_points"]["throttle_map_csv"]
    src_csv = os.environ.get("GNC_MAP_CSV", mp_)
    shutil.copy2(src_csv, os.path.join(SNAP, os.path.basename(mp_)))
    man_src = dict(interfaces=IFACE, throttle_map=src_csv)
    for n in sorted(os.listdir(SNAP)):
        if n == "manifest.json":
            continue
        b = open(os.path.join(SNAP, n), "rb").read()
        v = None
        if n.endswith(".json"):
            try:
                v = json.loads(b).get("version")
            except Exception:
                v = None
        man[n] = dict(sha256=hashlib.sha256(b).hexdigest(), bytes=len(b), version=v)
    man["_sources"] = man_src
    with open(os.path.join(SNAP, "manifest.json"), "w") as f:
        json.dump(man, f, indent=1)
    return man


# interface versions asserted in strict mode (v2.9-dev, REV-GNC-2 N4/N5)
IFACE_VERSIONS = {"combustion.json": os.environ.get("GNC_COMB_VERSION", "v2.4"), "electronics.json": "v1", "mechanical.json": "v2"}


def _json(name):
    """Interface file from the shared folder; local snapshot if the mount is unavailable. v2.9-dev (REV-GNC-2 N4): with
    GNC_STRICT (default) an unreadable GNC_IFACE file raises instead of falling back, and the file must match the pin list
    GNC_IFACE_PIN when it is set."""
    p = os.path.join(IFACE, name)
    try:
        if os.path.exists(p):
            engine_v2.pin_check(p)
            with open(p) as f:
                return json.load(f), "shared"
    except OSError:
        pass
    if engine_v2.STRICT:
        raise RuntimeError(f"run6 v2.9-dev: interface file {p} unreadable (GNC_IFACE {IFACE}); strict mode, no snapshot "
                           "fallback (set GNC_STRICT=0 to allow it)")
    s = os.path.join(SNAP, name)
    if os.path.exists(s):
        with open(s) as f:
            return json.load(f), "snapshot"
    return None, "absent"


def sources():
    if "comb" not in _C:
        _C["comb"], _C["comb_src"] = _json("combustion.json")
        _C["el"], _C["el_src"] = _json("electronics.json")
        _C["mech"], _C["mech_src"] = _json("mechanical.json")
        # v2.9-dev (REV-GNC-2 N4/N5): assert the interface versions this simulator was verified on. electronics.json v2
        # has no dynamics_for_GNC (KeyError in build), so the TVC dynamics stay on the electronics.json v1 pin.
        if engine_v2.STRICT:
            for k_, n_ in (("comb", "combustion.json"), ("el", "electronics.json"), ("mech", "mechanical.json")):
                v_ = str((_C[k_] or {}).get("version"))
                if v_ != IFACE_VERSIONS[n_]:
                    raise RuntimeError(f"run6 v2.9-dev: {n_} version {v_} != expected {IFACE_VERSIONS[n_]} "
                                       f"(GNC_IFACE {IFACE}; strict mode)")
        _C["tab_v1"] = engine_v2.combustion_tables(_C["comb"])
        # combustion v2 relay (lead, 2026-10-12): applied only while the hub carries the combustion.json version
        # named in data/relay/engine_correction_v2.json (m2_engine_relay.py)
        _C["relay"] = engine_v2.load_relay_correction(_C["comb"])
        if _C["relay"] is not None:
            _C["tab_relay"] = engine_v2.apply_relay(_C["tab_v1"], _C["relay"])
            _C["comb_relay"] = engine_v2.relay_combustion(_C["comb"], _C["relay"])
        _C["tab"] = _C.get("tab_relay", _C["tab_v1"])
    return _C


SUPPLY_FILE = os.environ.get("GNC_EL_SUPPLY", "/home/claude/work/electronics/results/tvc_supply_budget_v1.json")


def supply_sources():
    """Electronics calc/tvc_supply_budget_v1 results (servo supply chains, servo currents): read from the Electronics work
    folder (read-only for GNC) and copied to the local snapshot; the snapshot is used when the file is unavailable."""
    if "supply" not in _C:
        d, src = None, "absent"
        if engine_v2.STRICT and not os.path.exists(SUPPLY_FILE):
            raise RuntimeError(f"run6 v2.9-dev: {SUPPLY_FILE} unreadable (GNC_EL_SUPPLY); strict mode, no snapshot fallback")
        if os.path.exists(SUPPLY_FILE):
            engine_v2.pin_check(SUPPLY_FILE)
        try:
            if os.path.exists(SUPPLY_FILE):
                b = open(SUPPLY_FILE, "rb").read()
                d, src = json.loads(b), SUPPLY_FILE
                os.makedirs(SNAP, exist_ok=True)
                with open(os.path.join(SNAP, os.path.basename(SUPPLY_FILE)), "wb") as f:
                    f.write(b)
        except (OSError, ValueError):
            d = None
        if d is None:
            sp = os.path.join(SNAP, os.path.basename(SUPPLY_FILE))
            if os.path.exists(sp):
                with open(sp) as f:
                    d, src = json.load(f), "snapshot"
        _C["supply"], _C["supply_src"] = d, src
    return _C["supply"], _C["supply_src"]


def supply_chain(name):
    """(R_source, R_common, R_branch) [ohm], servo current model and other loads for a chain 'config/column/pack'
    of tvc_supply_budget_v1 (e.g. 'v2.2_as_drawn/typ/15', 'v2.3_proposal/typ/15', 'basis_SIL_v2.2/typ/None')."""
    sup, src = supply_sources()
    if sup is None:
        raise RuntimeError("supply_chain needs Electronics results/tvc_supply_budget_v1.json (or its snapshot)")
    cname, col, pack = name.split("/")
    pk = None if pack == "None" else float(pack)
    row = [r for r in sup["B_cases"] if r["config"] == cname and r["column"] == col
           and ((r["pack_mohm"] is None and pk is None) or (r["pack_mohm"] is not None and pk is not None
                                                           and abs(float(r["pack_mohm"]) - pk) < 1e-9))]
    if len(row) != 1:
        raise KeyError(f"supply chain {name} not found in {src}")
    r = row[0]
    ist = sup["inputs"]["servo"]["stall_current_A"]["v"]
    (va, ia), (vb, ib) = sorted((float(k), float(x)) for k, x in ist.items())[:2]
    k_ = (ib - ia) / (vb - va)
    irun = sup["inputs"]["servo"]["running_current_A"]["v"]
    irun_v = float(irun["7.4"]) if "7.4" in irun else max(float(x) for x in irun.values())
    return dict(Rs=r["R_source_mohm"] * 1e-3, Rc=r["R_common_mohm"] * 1e-3, Rb=r["R_branch_mohm"] * 1e-3,
                Ia=ia - va * k_, Ik=k_, Irun=irun_v, Io=float(sup["inputs"]["I_other_A"]["v"]), src=src,
                tool=sup.get("tool"), date=sup.get("date"), row=r)


def hold_plug_voltage(ch, V_rest):
    """Plug voltage with both TVC servos at stall (Electronics plug_voltage_hold closed form)."""
    req = 2 * ch["Rs"] + 2 * ch["Rc"] + ch["Rb"]
    return (V_rest - ch["Io"] * ch["Rs"] - ch["Ia"] * req) / (1 + ch["Ik"] * req)


def rest_for_hold(ch, V_hold):
    req = 2 * ch["Rs"] + 2 * ch["Rc"] + ch["Rb"]
    return V_hold * (1 + ch["Ik"] * req) + ch["Io"] * ch["Rs"] + ch["Ia"] * req


def ignition_nominal(comb):
    """Nominal command-to-90 % Pc time of a start: combustion.json v1 igniter_electrical.timing_per_start_s
    main_Pc_90pct_expected; combustion.json v2 igniter.model_transients (SIM: relights reach 90 % 0.28-0.29 s after
    the command -> 0.29 s). The Monte Carlo disperses it U(0.2, 0.6) s per the brief either way."""
    if "igniter_electrical" in comb:
        ign = comb["igniter_electrical"]["timing_per_start_s"]
        return ign["main_Pc_90pct_expected"], "combustion.json v1 main_Pc_90pct_expected (DERIVED target)"
    mt = comb.get("igniter", {}).get("model_transients", {})
    return 0.29, ("combustion.json " + str(comb.get("version")) + " igniter.model_transients (" + str(mt.get("tag", "SIM"))
                  + "): relight 90 % at 0.28-0.29 s after the command -> 0.29 s")


def engine_sources(cfg):
    """(comb, tab, relay or None) for cfg["engine"]: "relay" = combustion.json map x relay factors + S230 grain
    (falls back to the plain map when no correction applies, e.g. once combustion.json v2 is published);
    "v1" = combustion.json map as published."""
    src = sources()
    if cfg["engine"] == "relay" and src["relay"] is not None:
        return src["comb_relay"], src["tab_relay"], src["relay"]
    return src["comb"], src["tab_v1"], None


# ------------------------------------------------------------------ sensor classes (1 sigma, per axis)
# Residual errors after a pre-launch pad calibration (gyro bias averaged on the pad, accelerometer
# levelling). Datasheet numbers are quoted from vendor pages (see REPORT sources); residuals that the
# datasheets do not give (temperature/g-sensitivity over a 30-60 s flight) are ASSUMED and tagged.
IMU = {
    "ADIS16470": dict(
        g_nd=np.radians(0.008), g_bias=np.radians(0.03), g_sf=0.002,
        a_nd=1.0e-3, a_bias=0.0098, a_sf=0.002, align=1.0e-3, yaw=np.radians(2.0), a_range_g=40.0,
        tag="DATASHEET ADIS16470 (0.008 deg/s/rtHz, 8 deg/h, 13 ug in-run, 0.015 deg/s/g); residual gyro bias "
            "0.03 deg/s = in-run + 2 g x 0.015 deg/s/g DERIVED; accel noise 100 ug/rtHz and residual bias 1 mg ASSUMED"),
    "BMI088": dict(
        g_nd=np.radians(0.014), g_bias=np.radians(0.125), g_sf=0.005,
        a_nd=2.26e-3, a_bias=0.022, a_sf=0.005, align=2.2e-3, yaw=np.radians(2.0), a_range_g=24.0,
        tag="DATASHEET Bosch BMI088 flyer (gyro 0.014 deg/s/rtHz, TCO 0.015 deg/s/K; accel 230 ug/rtHz, TCO 0.2 mg/K); "
            "residual gyro bias 0.125 deg/s = 5 K x TCO + ASSUMED 0.05 deg/s/g x 2 g; accel 2.2 mg = 5 K x TCO + 2 mg cal ASSUMED"),
    "ICM42688": dict(
        g_nd=np.radians(0.0028), g_bias=np.radians(0.103), g_sf=0.005,
        a_nd=6.9e-4, a_bias=0.0196, a_sf=0.005, align=2.0e-3, yaw=np.radians(2.0), a_range_g=16.0,
        tag="DATASHEET TDK ICM-42688-P page (gyro 2.8 mdps/rtHz, TC 0.005 dps/K; accel 70 ug/rtHz, +/-16 g); "
            "residual gyro bias = 5 K x TC + ASSUMED 0.05 deg/s/g x 2 g; accel 2 mg ASSUMED"),
}
GNSS = {
    "standalone": dict(sp_h=0.3, sp_v=0.5, sv=0.10, rate=10.0, lat=0.02, bsh=0.5, bsv=1.0,
                       tag="ASSUMED u-blox M9/M10 class with pad zeroing: bias drift over the flight 0.5 m H / 1.0 m V, "
                           "white 0.3/0.5 m, velocity 0.10 m/s, 10 Hz, 20 ms uncompensated latency"),
    "rtk": dict(sp_h=0.01, sp_v=0.02, sv=0.05, rate=10.0, lat=0.02, bsh=0.02, bsv=0.03,
                tag="ASSUMED ZED-F9P class RTK fixed with a base at the pad: 1-2 cm, velocity 0.05 m/s, 10 Hz"),
}
DEF = dict(
    profile="A-D", vehicle="RV-1c", h_target=None, floor=0.20, pivot="mid", fins=False, imu="ADIS16470", gnss="standalone",
    lidar_range=40.0, lidar=True, lat_mode=0, vert_mode=0, dff=True, dff_tau=0.3, ht=8.0, vt=1.0, gim_lpf_w=50.0, gim_lpf_z=0.5, gim_cmd_rate=100.0, gim_cmd_acc=0.0, gim_aw_thr=0.0, gim_aw_tau=0.004, gim_enc_q=0.022, att_ref_rate=0.0, att_ref_win=0.0, att_ref_rate2=0.0, att_ref_mode=0, toff_model=0, pintle_full_stroke=0.25, meco_td=0.0, meco_td_max=0.75, meco_td_hold=0.25, relight_start=0.0, t_ign_add=0.0, throat_g=0.0, throat_jref=None, throat_g_band=None, throat_loop=1, reg_band=None, reg_a=None, reg_n=None, reg_model=None, t_ign_q=None, k_est_asc=0, floor_comp_min=0.125, rate_map=None, rmap_close=0, rmap_cap=1, rmap_k=1.0, thr_lat=0.0, thr_tau_s=0.0, thr_ff_rise=0.0, thr_drive=0, thr_tau_p=0.0085, thr_tau_v=0.008, mest_mode=0, mest_w=0.0, mest_dq=0.0, mest_kcal=1.0, mest_ghat=0.0, mest_jref=0.0, mest_s1=0.0, mest_s2=0.0, mest_pcl_t=-1.0, mest_pcl_re=1, mest_tau=0.0455, kest_comp=0, web_on=0, web_D0=0.025, web_Do=0.0535, web_lim=0.001, web_kt=None, web_nt=None, web_kqs=1.016, web_kf=None, web_nf1=None, web_nf2=None, web_kcal=None, web_ghat=0.0, web_jref=None, web_act=0, bpred_pc=0, flt_on=0, flt_ph=1, flt_t=0.5, flt_F=670.0, flt_rate=2500.0, flt_enc=0, flt_pcl=0, flt_persist=1, det_fct=1, det_op=1, det_pf=1, det_geo=0, fct_thr=650.0, fct_n=3, fct_tau=0.020, fct_hz=100.0, fct_ph=0.005, fct_comp=0, det_op_Pabs=3.0e6, det_op_t=0.003, det_pf_t=0.100, det_pf_err_m=0.15e-3, geo_dh=15.0, abt_lat=0.00168, abt_seat=0.0394, abt_sdto=0.30, abt_sdenc=0.08, abt_imp=38.2, prg_on=0, prg_T=2.5, prg_lead=0.5, prg_mdot=0.0200, prg_mdot_hat=None, prg_book=1, prg_jet=1, prg_prio=1, blf_on=0, blf_ph=4, blf_mdot=0.0194, blf_mode=0, blf_n=0.5, blf_fmax=0.14, bl_vj=105.8, bl_az=0.0, rel_mode=0, rel_Pc=3.0e5, rel_dt=0.0, st_on=0, st_Pc=2.4e5, st_T=0.4, rel_to=0.0, rel_rise_Pc=2.11325e5, pgg_on=0, pgg_Tc=2.90, pgg_ton=0.35, pgg_Tp=2.5, pgg_toff=0.05, pgg_tcl=0.077, pgg_Tmin=1.9, pgg_cap=2.5, pgg_gate=1, pgg_aqs=1.5, pgg_tqs=0.5, pgg_tau=0.2, pgg_tdmin=1.0, pgg_cv=1, pgg_ant=2.90, pgg_ovr=1, pgg_hfl=0.0, kfz_on=0, pcf_on=0, pcf_dt=0.0, pcf_k=1.0, pcf_rule=0, pcf_Facc=None, pcf_n=3, pcf_tmax=0.5, pcf_tbl=0.5, pcf_fo=0, gim_notch_f=0.0, gim_notch_q=1.0, gim_notch_db=-12.0, gim_notch_track=0.0, gim_notch_mis_w=0.0, rock_K_eng=None, eng_I_pivot_wet=None, roll_comp_tau=0.0, kt_lat=1.5, t_hand=0.5, rot_int=1, act_model=0, servo_V=7.4, act_n=None, act_Jint=0.0, supply_chain=None, supply_Vrest=None, engine="relay", roll_amp=0.02, gim_wn_hz=None, quant=0.01, rock=True, rock_zeta=0.05, hslam=None, ballast=0.0, ballast_z=0.60,
    m_n2o=None, load_margin=1.15, wind=0.0, wind_dir=0.0, gust=False, gust_scale=1.0, rcs=True,
    rcs_torque=None, rcs_thrust=0.5, rcs_deadband_dps=5.0, roll_torque=0.0, dt=1e-3, tmax=90.0, seed=1, noise=True,
    slosh=True, fuel_phi=0.0, tau_fuel=0.3, gim_max_deg=7.0, att_wn=6.0, att_wn_asc=7.0, att_zeta=0.7,
    lat_wn=1.0, lat_zeta=1.0, tilt_max_land=25.0, tilt_term=4.5, tilt_term_hi=10.0, tilt_max_asc=10.0, kd=None,
    t_ign=None, t_ign_est=0.6, tau=0.100 / 2.197, slew=5.0, ascent_bias=(0.0, 0.0), drogue_CdA=0.5,
    legs_k=2500.0, legs_c=120.0, legs_stroke=0.10, legs_mu=0.5, test_mode=0, w0=(0.0, 0.0, 0.0), v0z=0.0,
    h0=0.0, rho0=1.225, T0=293.15, div_margin=1.0, t_hmin=2.0, aero_unc=None, rec_dt=0.02, ascent_bias_auto=None,
)


def cfg_of(**kw):
    c = dict(DEF)
    for k in kw:
        if k not in DEF and k not in DISP_KEYS:
            raise KeyError(k)
    c.update(kw)
    if c["h_target"] is None:
        c["h_target"] = 100.0 if c["profile"] == "B" else 300.0
    if c["kd"] is None:
        c["kd"] = 0.6 if c["profile"] == "A-D" else 0.7
    return c


# per-run dispersion keys (multipliers/offsets), defaults = no dispersion
DISP = dict(thrust_scale=1.0, isp_scale=1.0, tau_f=1.0, dry_scale=1.0, m_est_err=0.0, cg_x=0.0, cg_y=0.0,
            dz_air=0.0, mis_x=0.0, mis_y=0.0, g_b=(0.0, 0.0, 0.0), a_b=(0.0, 0.0, 0.0), g_sf=0.0, a_sf=0.0,
            align=(0.0, 0.0, 0.0), gnss_b=(0.0, 0.0, 0.0), baro_b=0.0, gim_wn_f=1.0, gim_delay_add=0.0,
            legs_k_f=1.0, legs_c_f=1.0, slosh_zeta=0.01, drogue_f=1.0, hose_K=None, rock_K=None, rock_zeta=None, notch_mis=None,
            throat_g=None, reg_a=None, reg_n=None)
DISP_KEYS = set(DISP)


def throat_cf_coeffs(comb, tab, Fmax=500.0, g_ref=0.09, pa=101325.0):
    """v2.7: relative change of the sea-level thrust coefficient per unit throat-area growth, k_cf = (CF(eps/(1+g)) /
    CF(eps) - 1) / g at g_ref, at 12.5 / 20 / 60 / 100 % thrust (Pc from the published map at the initial port; frozen
    gamma of the max-thrust point; ideal 1-D nozzle, no separation model). DERIVED from combustion.json."""
    from scipy.optimize import brentq
    from .propulsion import _bilin
    gm = comb["operating_points"]["max_thrust"]["gamma_chamber"]["v"]
    eps = comb["gas_path"]["nozzle"]["expansion_ratio"]["v"]

    def cf(e, pc):
        ar = lambda M: (1 / M) * ((2 / (gm + 1)) * (1 + 0.5 * (gm - 1) * M * M)) ** ((gm + 1) / (2 * (gm - 1)))  # noqa: E731
        Me = brentq(lambda M: ar(M) - e, 1.0001, 10.0)
        pe = pc * (1 + 0.5 * (gm - 1) * Me * Me) ** (-gm / (gm - 1))
        mom = np.sqrt(2 * gm * gm / (gm - 1) * (2 / (gm + 1)) ** ((gm + 1) / (gm - 1)) * (1 - (pe / pc) ** ((gm - 1) / gm)))
        return mom + (pe - pa) / pc * e
    out = []
    for fr in (0.125, 0.20, 0.60, 1.00):
        pc = float(_bilin(tab["Fg"], tab["Dg"], tab["pc"], fr * Fmax, tab["Dg"][0]))
        out.append((cf(eps / (1 + g_ref), pc) / cf(eps, pc) - 1.0) / g_ref)
    return out


def servo_line(tvc, V):
    """Servo stall torque [N m] and no-load speed [deg/s] at supply V from the electronics.json DATASHEET points
    (stall_torque_Nm, noload_speed_dps per voltage): torque linear in V, time per 60 deg linear in V between the
    bracketing points, end segments extrapolated (same rule as Electronics calc/tvc_slew_check_v1.servo)."""
    tq = {float(k.rstrip("V")): float(x) for k, x in tvc["stall_torque_Nm"]["v"].items()}
    sp = {float(k.rstrip("V")): 60.0 / float(x) for k, x in tvc["noload_speed_dps"]["v"].items()}
    pts = sorted(tq)
    if V <= pts[0]:
        a, b = pts[0], pts[1]
    elif V >= pts[-1]:
        a, b = pts[-2], pts[-1]
    else:
        a = max(x for x in pts if x <= V)
        b = min(x for x in pts if x > V)
    Ts = tq[a] + (tq[b] - tq[a]) * (V - a) / (b - a)
    s60 = sp[a] + (sp[b] - sp[a]) * (V - a) / (b - a)
    return Ts, 60.0 / s60


def build(cfg, disp=None):
    """Return par, apar, comp, mp, tables, info for a configuration (+ optional per-run dispersions)."""
    src = sources()
    el, mech = src["el"], src["mech"]
    comb, tab, relay = engine_sources(cfg)
    rv1c = cfg["vehicle"] == "RV-1c"
    if rv1c and mech is None:
        raise RuntimeError("RV-1c needs mechanical.json (interfaces or snapshot)")
    d = dict(DISP)
    if disp:
        d.update(disp)
    tags = {}

    def T(name, v, tag):
        tags[name] = (v, tag)
        return v
    prof = cfg["profile"]
    descent = "drogue" if prof == "A-D" else "none"
    if rv1c:
        geo = veh.reference_geometry_v3(legs="deployable", comb=comb, mech=mech, fins=cfg["fins"])
    else:
        geo = veh.reference_geometry_v2(pivot=cfg["pivot"], legs="deployable", comb=comb, fins=cfg["fins"])
    m_n2o = cfg["m_n2o"]
    V = tank_volume_for(m_n2o)
    if rv1c:
        growth = None
        # the relayed S230 engine growth applies only on the CAD v2 engine of mechanical.json v1; later mechanical.json
        # versions carry the S230 gas path in their own mass properties (no double count)
        if relay is not None and str(mech.get("version")) == "v1":
            rv = relay["relay_values"]["engine_dry_mass_growth_kg"]
            growth = dict(m=rv["v"], tag=rv["tag"] + " (lead relay 2026-10-12; at the engine CG; mechanical.json v2 pending)")
        elif str(mech.get("version")) == "v1" and str(comb.get("version", "")).startswith("v2"):
            # run6 v2.5.2: the published S230 engine (combustion.json v2.x) on the CAD v2 engine of mechanical.json v1
            # carries the same growth (attribution run v3a; before v2.5.2 this combination had no growth)
            rv = engine_v2.s230_growth_on_cad_v2()
            if rv is not None:
                growth = dict(m=rv["v"], tag=rv["tag"] + " (lead relay 2026-10-12, S230 on mechanical.json v1; "
                                                         "combustion.json " + str(comb.get("version")) + " flown)")
        led = veh.mass_ledger_v3(geo, mech=mech, el=el, descent_option=descent, tank_V=V, fins=cfg["fins"],
                                  roll_rcs=cfg["rcs"], eng_growth=growth)
    else:
        led = veh.mass_ledger_v2(geo, descent_option=descent, tank_V=V, fins=cfg["fins"])
    if cfg["ballast"] > 0:
        led.append(dict(name="B01 ballast", owner="gnc", m=cfg["ballast"], m_min=cfg["ballast"],
                        m_max=cfg["ballast"], z=cfg["ballast_z"], shape="point", dims=[], gimballed=False,
                        tag="ASSUMED landing-mass ballast near the CG (trade)"))
    # dispersions on the ledger: dry mass scale and axial shift of the airframe items
    led_d = []
    for it in led:
        it2 = dict(it)
        if not it["name"].startswith("B01"):
            it2["m"] = it["m"] * d["dry_scale"]
        if it["owner"] == "airframe":
            it2["z"] = it["z"] + d["dz_air"]
        led_d.append(it2)
    mp = veh.build_mp(geo, led_d, legs_deployed=True, tank_V=V)
    mp_nom = veh.build_mp(geo, led, legs_deployed=True, tank_V=V)
    T0 = cfg["T0"]
    rho_l = CP.PropsSI("D", "T", T0, "Q", 0, "NitrousOxide")
    m_fuel0 = comb["gas_path"]["grain"]["mass_kg"]["v"]
    if cfg.get("eng_I_pivot_wet") is not None:
        # v2.6: engine own transverse inertia shifted so the wet engine (full grain) inertia about the pivot equals the
        # given value (e.g. the CAD v3.3 0.052 kg m2 relayed by the lead with the FEA stiffness); mass and CG unchanged
        if not rv1c:
            raise ValueError("eng_I_pivot_wet needs vehicle RV-1c")
        for mp_ in (mp, mp_nom):
            o_ = np.zeros(8)
            veh.massprops(mp_, 0.0, 0.0, 800.0, m_fuel0, o_)
            mp_[veh.MP_G2] += float(cfg["eng_I_pivot_wet"]) - (o_[6] + o_[4] * (mp_[veh.MP_ZP] - o_[5]) ** 2)
    # liftoff mass properties, nominal vs dispersed (for the controller's moment-arm error)
    E = s6.tank_init(m_n2o, T0, V, 1.0)
    out_d = np.zeros(8); out_n = np.zeros(8)
    Tt, Pt, ml, mv, hl = s6.tank_solve(m_n2o, E, V, 1.0)
    veh.massprops(mp, ml, mv, rho_l, m_fuel0, out_d)
    veh.massprops(mp_nom, ml, mv, rho_l, m_fuel0, out_n)
    unc = dict(cfg["aero_unc"] or {})
    apar, comp = aero.build_aero_params(dict(geo, drogue_CdA=cfg["drogue_CdA"] * d["drogue_f"]
                                             if prof == "A-D" else 0.0), unc)
    tvc = el["actuators"]["tvc_A"]
    dyn = tvc["dynamics_for_GNC"]["v"]
    eng_side = tvc["engine_side_at_n7_7V4"]["v"]
    lat = el["loop_rates_and_latency"]["latency_s"]["v"]
    t_ign_nom, t_ign_tag = ignition_nominal(comb)
    m_tank = [i for i in led if i["name"].startswith("P11")][0]["m"]
    par = np.zeros(s6.NP)

    def S(name, v, tag):
        par[getattr(s6, "P_" + name)] = v
        T(name, v, tag)
    S("profile", 0 if prof.startswith("A") else 1, "CONFIG (A = ballistic + relight, B = continuous-burn hop)")
    S("h_target", cfg["h_target"], "REQ/CONFIG apogee or hop height")
    S("Fmax", 500.0, "REQ ENG-01 500 N")
    S("floor", cfg["floor"], "CONFIG throttle floor fraction (REQ 25 %, target 20 %, stretch 12.5 %)")
    S("tau", cfg["tau"] * d["tau_f"], "ASSUMED closed-loop thrust response tau (ENG-03 t10-90 = 2.197 tau); MC x U(0.7,1.5)")
    S("slew", cfg["slew"], "ASSUMED thrust slew limit [F_max/s]")
    S("deadb", 0.005, "ASSUMED command deadband [fraction F_max]")
    S("quant", cfg["quant"], "ASSUMED command resolution [fraction F_max] (ENG-03 <= 2 %; baseline flies 1 %)")
    # v2.6: the start-delay shift t_ign_add applies to the nominal (sizing) flight as well as to the dispersed draws
    # (run_cfg adds it to the draw); the first v2.6-dev runs shifted the draws only, which biased the sized load of the
    # shifted cases (the Monte Carlo runs themselves are unaffected)
    tq_ = cfg.get("t_ign_q")
    if tq_ and cfg["t_ign"] is None:
        # v2.7.1-dev: nominal (sizing) flight at the median of the start-delay quantile table
        S("t_ign", float(np.interp(0.5, np.linspace(0.0, 1.0, len(tq_)), np.asarray(tq_, dtype=float))) + cfg["t_ign_add"],
          "DERIVED median of the start-delay quantile table t_ign_q (MC draws the table)"
          + (f"; + t_ign_add {cfg['t_ign_add']:g} s" if cfg["t_ign_add"] else ""))
    else:
        S("t_ign", cfg["t_ign"] if cfg["t_ign"] is not None else t_ign_nom + cfg["t_ign_add"],
          t_ign_tag + "; MC U(0.2, 0.6) s per brief" + (f"; + t_ign_add {cfg['t_ign_add']:g} s" if cfg["t_ign_add"] else ""))
    S("t_ign_est", cfg["t_ign_est"], f"DESIGN relight planning value = latest start delay planned on ({cfg['t_ign_est']:g} s; "
                                     "0.6 s = top of the MC draw U(0.2, 0.6) s; + the NC-closed sequence time when planned)")
    S("t_rise", 0.05, "ASSUMED thrust build-up allowance after ignition in the relight planner")
    S("t_off", 0.035, "DERIVED ENG-05 (< 10 % in <= 100 ms)")
    S("thrust_scale", d["thrust_scale"], "MC N(1, 0.05) per brief")
    S("isp_scale", d["isp_scale"], "MC N(1, 0.05) per brief")
    S("k_est_asc", float(cfg.get("k_est_asc", 0) or 0), "DESIGN GNC v2.7 option: thrust-effectiveness estimator also in the "
                                                       "B-profile ascent / apex / floor descent (default off; 1 = v2.7-dev "
                                                       "first form, rejected: ascent drag-sign bias; 2 = signed nominal "
                                                       "drag model + compensated floor / top-up commands)")
    apk_, _ = aero.build_aero_params(dict(geo, drogue_CdA=0.0), {})
    S("kest_cda_nf", apk_[aero.A_SREF] * (apk_[aero.A_CA0_NF] + apk_[aero.A_CA_ENGON_NF]),
      "DESIGN k_est_asc 2 nominal nose-first axial force area S (CA0_nf + CA_engine-on) [m2] (not the dispersed truth)")
    S("kest_cda_legs", apk_[aero.A_SREF] * apk_[aero.A_CA_LEGS], "DESIGN k_est_asc 2 nominal leg axial force area [m2]")
    S("floor_comp_min", float(cfg.get("floor_comp_min", 0.125)),
      "DESIGN k_est_asc 2 lowest compensated floor command / F_max (combustion.json floor_stretch_12p5pct: modelled, "
      "low-flux stability UNVERIFIED until T3)")
    # v2.7 in-flight throat growth (ENG-06 rev 2, review RC-06): growth at the end of the cycle; off by default
    g_thr = float(d["throat_g"]) if d.get("throat_g") is not None else float(cfg.get("throat_g") or 0.0)
    S("throat_g", g_thr, "REQ ENG-06 rev 2 (7-11 % throat-area growth within a flight; MC U(0.07, 0.11) when "
                         "throat_g_band is set) - Pc-loop model, sim6 v2.7")
    if g_thr > 0.0:
        if not cfg.get("throat_jref"):
            raise ValueError("throat_g > 0 needs throat_jref (the nominal flight's int (Pc/Pc_max)^0.68 dt)")
        S("throat_jref", float(cfg["throat_jref"]), "DERIVED nominal flight of this cycle: int (F/F_max)^0.68 dt [s]")
        S("throat_loop", float(cfg.get("throat_loop", 1)), "ASSUMED ECU loop: 1 = Pc held on the nominal map (uncompensated), "
                                                            "0 = throat-compensated thrust loop")
        kc_ = throat_cf_coeffs(comb, tab)
        for i_, k_ in enumerate(kc_):
            S(f"throat_k{i_}", k_, "DERIVED 1-D nozzle (combustion.json gamma, eps, Pc map): dCF/CF per unit g at "
                                   f"{(0.125, 0.2, 0.6, 1.0)[i_] * 100:g} % thrust")
    # v2.7.1-dev: regression-law band (review RC-07), gncsim.regband; off unless (reg_a, reg_n) are given (draw or config)
    ra_ = d.get("reg_a") if d.get("reg_a") is not None else cfg.get("reg_a")
    rn_ = d.get("reg_n") if d.get("reg_n") is not None else cfg.get("reg_n")
    if ra_ is not None and rn_ is not None:
        xs_, po_, pu_ = regband.knots(ra_, rn_, cfg.get("reg_model"))
        S("reg_on", 1.0, "DESIGN GNC v2.7.1 option: regression-law band (gncsim.regband " + regband.VERSION + ")")
        S("reg_nk", float(xs_.size), "DERIVED regband knots")
        for k_ in range(xs_.size):
            par[getattr(s6, f"P_reg_x{k_}")] = xs_[k_]
            par[getattr(s6, f"P_reg_o{k_}")] = po_[k_]
            par[getattr(s6, f"P_reg_u{k_}")] = pu_[k_]
        T("reg_a_scale", float(ra_), "ASSUMED band x0.6-1.5 (combustion.json regression_law; review RC-07)")
        T("reg_n", float(rn_), "ASSUMED band 0.35-0.68 (combustion.json regression_law; review RC-07)")
        T("reg_phi_ox_first_last", (float(po_[0]), float(po_[-1])), "DERIVED regband tables (Combustion band runs)")
    # v2.8-dev ENG-03 state-dependent thrust-rate map (Electronics), servo lag and rate-aware feed-forward; off by default
    rm_ = cfg.get("rate_map")
    if rm_ is not None:
        Pp_ = np.asarray(rm_["P_tank_Pa"], float); Ff_ = np.asarray(rm_["F_N"], float)
        Ro_ = np.asarray(rm_["open_N_per_s"], float); Rc_ = np.asarray(rm_["close_N_per_s"], float)
        if Pp_.size > 8 or Ff_.size > 20 or Ro_.shape != (Pp_.size, Ff_.size) or Rc_.shape != Ro_.shape:
            raise ValueError("rate_map: up to 8 pressures x 20 thrust levels, open/close arrays [P x F]")
        if np.any(np.diff(Pp_) <= 0) or np.any(np.diff(Ff_) <= 0):
            raise ValueError("rate_map axes must increase")
        S("rmap_on", 1.0, "DESIGN GNC v2.8-dev ENG-03 option: state-dependent thrust-rate map " + str(rm_.get("source", "?")))
        S("rmap_np", float(Pp_.size), "DERIVED rate-map grid")
        S("rmap_nf", float(Ff_.size), "DERIVED rate-map grid")
        for k_ in range(Pp_.size):
            par[getattr(s6, f"P_rmap_p{k_}")] = Pp_[k_]
        for k_ in range(Ff_.size):
            par[getattr(s6, f"P_rmap_f{k_}")] = Ff_[k_]
        for i_ in range(Pp_.size):
            for j_ in range(Ff_.size):
                par[getattr(s6, f"P_rmap_o{i_ * Ff_.size + j_}")] = Ro_[i_, j_]
                par[getattr(s6, f"P_rmap_c{i_ * Ff_.size + j_}")] = Rc_[i_, j_]
        T("rate_map_source", rm_.get("source"), rm_.get("tag", "SIM Electronics (see source)"))
        S("rmap_close", float(cfg["rmap_close"]), "DESIGN 1 = closing rate from the map, 0 = slew x F_max")
        S("rmap_cap", float(cfg["rmap_cap"]), "DESIGN 1 = map limits capped at slew x F_max (the map only slows the plant)")
        S("rmap_k", float(cfg["rmap_k"]), "SENSITIVITY multiplier on the map rates")
    S("thr_lat", float(cfg["thr_lat"]), "ASSUMED servo latency on the thrust command [s] (0 = off; Electronics eng03 4 ms)")
    S("thr_tau_s", float(cfg["thr_tau_s"]), "ASSUMED first-order servo stage in series [s] (0 = off)")
    S("thr_ff_rise", float(cfg["thr_ff_rise"]), "DESIGN rate-aware feed-forward: extra landing-burn planning lag [s] (0 = off)")
    S("thr_drive", float(cfg["thr_drive"]), "DESIGN 1 = Electronics reduced drive model B in series (pintle_rate_map_v1), 0 = off")
    S("thr_tau_p", float(cfg["thr_tau_p"]), "FIT Electronics pintle_rate_map_v1 model B tau_p (nonlinear drive simulation, ASSUMED servo)")
    S("thr_tau_v", float(cfg["thr_tau_v"]), "FIT Electronics pintle_rate_map_v1 model B tau_v (nonlinear drive simulation, ASSUMED servo)")
    # v2.8-dev amendment M: flown FSW mass estimator (review RG-16); off by default (mest_mode 0 = m (1 + m_est_err))
    S("mest_mode", float(cfg["mest_mode"]), "DESIGN 1 = flown FSW mass estimator (sim6 v2.8-dev amendment M), 0 = m (1 + m_est_err)")
    S("mest_w", float(cfg["mest_w"]), "ASSUMED/REQ per-run ARM weighing error [kg] (scale TO-DEFINE)")
    S("mest_dq", float(cfg["mest_dq"]), "DERIVED per-run Pc transducer offset x map flow per Pc [kg/s] (electronics.json v1 TE M3234 band)")
    S("mest_kcal", float(cfg["mest_kcal"]), "DESIGN FSW flow-map calibration factor (1 = nominal map; static-fire calibration residual)")
    S("mest_ghat", float(cfg["mest_ghat"]), "DESIGN FSW throat-growth model end value (REQ ENG-06 rev 2 band 0.07-0.11; 0 = off)")
    S("mest_jref", float(cfg["mest_jref"]), "DESIGN FSW growth-model reference J (nominal flight)")
    S("mest_s1", float(cfg["mest_s1"]), "ASSUMED first start: truth start-transient N2O minus the FSW allowance [kg] (Combustion <= 8.7 g)")
    S("mest_s2", float(cfg["mest_s2"]), "ASSUMED later starts: as mest_s1 [kg]")
    S("mest_pcl_t", float(cfg["mest_pcl_t"]), "DESIGN time of the Pc loss for the estimator [s] (< 0 = never)")
    S("mest_pcl_re", float(cfg["mest_pcl_re"]), "DESIGN Pc-lost rule: 1 = rocket equation in the FC_THRUST window, 0 = commanded-thrust model only")
    S("mest_tau", float(cfg["mest_tau"]), "REQ ENG-03 nominal closed-loop t10-90 100 ms / 2.197 [s] (FSW commanded-thrust model)")
    S("kest_comp", float(cfg["kest_comp"]), "DESIGN 1 = accelerometer lever-arm and nozzle-direction compensation (k_hat, F_acc)")
    # v2.8-dev amendment W (review RG-03, RG-10): fuel-web state, burn limit and action; B apex predictor on Pc. Off by default.
    # Truth law defaults: the run's regression band (reg_a, reg_n) x web_kqs, else the band's nominal corner (a 1.0, n 0.5).
    # FSW law defaults: k = 1.1 x the truth a (measured a exact), n = truth n -/+ 0.05, flow calibration 1 / isp_scale.
    a_w = float(ra_) if ra_ is not None else 1.0
    n_w = float(rn_) if rn_ is not None else 0.5
    S("web_on", float(cfg["web_on"]), "DESIGN 1 = fuel-web states and burn limit (sim6 v2.8-dev amendment W)")
    S("web_D0", float(cfg["web_D0"]), "DATASHEET/DERIVED Combustion law_for_gnc D0 (burn_limit_proxy_v2p4.json)")
    S("web_Do", float(cfg["web_Do"]), "DATASHEET/DERIVED Combustion law_for_gnc D_outer (burn_limit_proxy_v2p4.json)")
    S("web_lim", float(cfg["web_lim"]), "REQ ENG-06 web >= 1 mm; lead rule burn limit at w = 1 mm")
    S("web_kt", float(cfg["web_kt"]) if cfg.get("web_kt") is not None else a_w * float(cfg["web_kqs"]),
      "DERIVED truth rate scale = band a x web_kqs (Combustion verification: quasi-steady proxy x 1.004-1.016 matches the "
      "grain_q1d t(w = 1 mm); ASSUMED until T1-T4)")
    S("web_nt", float(cfg["web_nt"]) if cfg.get("web_nt") is not None else n_w, "ASSUMED truth exponent = band n of the run")
    S("web_kf", float(cfg["web_kf"]) if cfg.get("web_kf") is not None else 1.1 * a_w,
      "DESIGN FSW rate scale = 1.1 x measured a (lead rule 2026-10-13)")
    S("web_nf1", float(cfg["web_nf1"]) if cfg.get("web_nf1") is not None else n_w - 0.05,
      "DESIGN FSW exponent, low end of the measured-n band")
    S("web_nf2", float(cfg["web_nf2"]) if cfg.get("web_nf2") is not None else n_w + 0.05,
      "DESIGN FSW exponent, high end of the measured-n band")
    S("web_kcal", float(cfg["web_kcal"]) if cfg.get("web_kcal") is not None else 1.0 / float(d["isp_scale"]),
      "DESIGN FSW oxidiser-flow calibration on the map at the Pc-implied thrust (static-fire calibration)")
    S("web_ghat", float(cfg["web_ghat"]), "DESIGN FSW growth model end value for the oxidiser flow (0 = off)")
    S("web_jref", float(cfg["web_jref"]) if cfg.get("web_jref") is not None else float(cfg.get("throat_jref") or 0.0),
      "DESIGN FSW growth-model reference J")
    S("web_act", float(cfg["web_act"]), "DESIGN action at the burn limit: 0 monitor, 1 end ascent before apex / continue after, "
                                        "2 shutdown (comparison only)")
    S("bpred_pc", float(cfg["bpred_pc"]), "DESIGN 1 = B apex predictor ramp-down terms on the Pc-implied thrust (review RG-10)")
    S("tank_V", V, "DERIVED sizing.tank_volume_for (85 % liquid fill at 25 C)")
    S("m_n2o", m_n2o, "SIM sized load x margin (run6.size_load)")
    S("T0", T0, "REQ ENG-12 20 +/- 3 C; MC U(15, 25) C per brief")
    S("c_wall", 0.5 * m_tank * 896.0, "ASSUMED 50 % of tank-wall heat capacity (Al 896 J/kg/K)")
    S("resid", 0.03, "ASSUMED unusable liquid fraction")
    S("rho_l_nom", rho_l, "CoolProp saturated liquid N2O at T0")
    S("m_fuel0", m_fuel0, comb["gas_path"]["grain"]["mass_kg"]["tag"] + f" (combustion.json {comb.get('version')})")
    T("engine_model", cfg["engine"] if relay is not None else "v1",
      ("combustion.json " + str(src["comb"].get("version")) + " map x relay factors k_ox(F), k_f(F) "
       + str(relay["version"]) + " (combustion v2 S230 runs, lead relay 2026-10-12)") if relay is not None
      else f"combustion.json {src['comb'].get('version')} map as published ({tab['meta'].get('map_format', 'v1: T_tank x F')})")
    S("z_tip", geo["z_tip"], "ASSUMED RV-1 airframe")
    S("z_foot", geo["z_foot"], "ASSUMED RV-1 legs (foot plane 0.25 m below the aft datum)")
    S("r_foot", geo["r_foot"], "ASSUMED RV-1 legs (foot radius 0.40 m)")
    S("z_imu", 1.15, "ASSUMED avionics bay station")
    S("legs_mode", 1.0 if prof == "B" else 0.0, "CONFIG legs deployed at t0 (hop) / at relight (A)")
    S("legs_k", cfg["legs_k"] * d["legs_k_f"], "ASSUMED leg spring per leg [N/m]; MC x U(0.8,1.2)")
    S("legs_c", cfg["legs_c"] * d["legs_c_f"], "ASSUMED leg damper per leg [N s/m]; MC x U(0.8,1.2)")
    S("legs_stroke", cfg["legs_stroke"], "ASSUMED leg stroke before hard stop [m]")
    S("legs_mu", cfg["legs_mu"], "ASSUMED foot friction coefficient")
    S("kd", cfg["kd"], "DESIGN braking reference uses kd x max deceleration")
    S("ht", cfg["ht"], "DESIGN terminal gate height [m]")
    S("vt", cfg["vt"], "DESIGN touchdown speed target [m/s]")
    S("kv", 2.0, "DESIGN vertical velocity loop gain [1/s]")
    S("hslam", -1.0 if cfg["hslam"] is None else (1.0 if cfg["hslam"] else 0.0), "CONFIG -1 auto, 1 hoverslam, 0 hover")
    S("hcut", 0.15, "DESIGN hoverslam cut when v_z > -0.15 m/s")
    S("hover_k", 0.9, "DESIGN hoverslam if T_floor > 0.9 W_est (lead update)")
    S("hs_margin", 3.0, "DESIGN hoverslam terminal deceleration margin [m/s2] (sim1d v1.2)")
    S("k_est", 1.0, "DESIGN accelerometer thrust-effectiveness estimator on")
    S("k_est_tau", 0.1, "DESIGN estimator time constant [s]")
    S("gim_max", cfg["gim_max_deg"], "REQ commanded limit on the gimbal VECTOR norm (gnc.json v1 7 deg; mechanical.json v1 REQUEST)")
    if cfg["gim_wn_hz"] is None:
        S("gim_wn", dyn["omega_n_rad_s"] * d["gim_wn_f"], "electronics.json v1 dynamics_for_GNC omega_n (ASSUMED there); MC over its range")
    else:
        S("gim_wn", 2.0 * np.pi * cfg["gim_wn_hz"], "CONFIG actuator natural frequency fixed (bandwidth requirement case; no dispersion)")
    S("gim_zeta", dyn["zeta"], "electronics.json v1 dynamics_for_GNC zeta")
    S("gim_delay", dyn["transport_delay_s"] + lat["fc_cmd_to_ecu_tick_max"] + 0.001 + d["gim_delay_add"],
      "electronics.json v1 transport delay + FC->ECU max + half 500 Hz frame; MC adds U(0, 3.2 ms)")
    if rv1c:
        ta = mech["tvc_actuation"]
        n_g = ta["gear_ratio_n"]["v"]
        eta = 0.9
        S("gim_n", n_g, f"mechanical.json {mech['version']} gear ratio r_e/r_h (crank nonlinearity: engine rate x cos psi, torque / cos psi)")
        S("gim_rate_nl", tvc["noload_speed_dps"]["v"]["7.4V"] / n_g,
          "DERIVED electronics.json servo no-load speed 7.4 V (DATASHEET) / n at neutral [deg/s]")
        S("gim_stall_engine", eta * n_g * tvc["stall_torque_Nm"]["v"]["7.4V"],
          "DERIVED electronics.json stall torque 7.4 V (DATASHEET) x n x eta 0.9 (electronics ASSUMED) at neutral [N m]")
        S("gim_deadband", ta["resolution_deg_engine"]["v"], f"mechanical.json {mech['version']} resolution at the engine [deg]")
        S("gim_backlash", ta["backlash_deg_engine"]["v"], f"mechanical.json {mech['version']} backlash at the engine [deg]")
        kh = mech["feed_across_gimbal"]["hinge_stiffness_Nm_per_rad"]["v"]
        S("hose_K", kh[1] if d["hose_K"] is None else d["hose_K"],
          f"mechanical.json {mech['version']} hose hinge stiffness (ASSUMED there) upper {kh[1]} N m/rad nominal; MC U({kh[0]}, {kh[1]})")
        hmt_ = ta["hinge_moment_terms_Nm"]
        S("gim_fric", hmt_["bearing_seal_friction" if "bearing_seal_friction" in hmt_ else "bearing_seal_friction_per_axis"]["v"],
          f"mechanical.json {mech['version']} bearing seal friction (ASSUMED there) [N m]")
        S("gim_stop", mech["gimbal"]["mechanical_stop_deg"]["v"], f"mechanical.json {mech['version']} conical stop [deg]")
        # v2.5: linkage-ratio override (act_n) and servo supply voltage (servo_V); torque/speed-limited servo pair (act_model 1)
        n_act = n_g if cfg["act_n"] is None else float(cfg["act_n"])
        Ts_v, wnl_v = servo_line(tvc, float(cfg["servo_V"]))
        vtag = f"{cfg['servo_V']:.2f} V"
        if cfg["act_n"] is not None or float(cfg["servo_V"]) != 7.4:
            S("gim_n", n_act, f"CONFIG linkage ratio n = r_e / r_h = {n_act:.3f} (mechanical.json {mech['version']} has {n_g}; "
                              "lead 2026-10-12 provisional n 4.8)")
            S("gim_rate_nl", wnl_v / n_act, f"DERIVED servo no-load speed at {vtag} (electronics.json DATASHEET points, "
                                            "s/60 deg linear in V) / n at neutral [deg/s]")
            S("gim_stall_engine", eta * n_act * Ts_v, f"DERIVED servo stall torque at {vtag} (DATASHEET points, linear in V) "
                                                      "x n x eta 0.9 at neutral [N m] (reference servo, act_model 0)")
        if cfg["act_n"] is not None:
            S("gim_deadband", ta["resolution_deg_engine"]["v"] * n_g / n_act,
              f"DERIVED mechanical.json {mech['version']} resolution x n_mech / n (servo-side deadband / n) [deg]")
            S("gim_backlash", ta["backlash_deg_engine"]["v"] * n_g / n_act,
              f"DERIVED mechanical.json {mech['version']} backlash x n_mech / n (servo-side backlash / n) [deg]")
        S("act_model", int(cfg["act_model"]), "CONFIG 0 = reference servo (2nd-order + engine-side torque/speed limit at "
                                              "neutral, sim6 <= v2.4); 1 = servo pair on its torque-speed lines through the "
                                              "Cardan kinematics (sim6 v2.5)")
        S("act_Ts", Ts_v, f"DERIVED SB-2292SG stall torque at {vtag} from the electronics.json DATASHEET points [N m]")
        S("act_wnl", np.radians(wnl_v), f"DERIVED SB-2292SG no-load speed at {vtag} from the DATASHEET s/60 deg points [rad/s]")
        S("act_re", ta["lever_radius_m"]["v"], f"mechanical.json {mech['version']} collar lever radius [m]")
        S("act_rh", ta["lever_radius_m"]["v"] / n_act, f"DERIVED horn radius r_e / n [m]")
        S("act_zb", ta["lever_ball_z_m"]["v"], f"mechanical.json {mech['version']} lever-ball height below the pivot [m]")
        S("act_az1", np.radians(ta["lever_azimuth_deg"]["v"][0]), f"mechanical.json {mech['version']} lever 1 azimuth [rad]")
        S("act_az2", np.radians(ta["lever_azimuth_deg"]["v"][1]), f"mechanical.json {mech['version']} lever 2 azimuth [rad]")
        S("act_Jint", float(cfg["act_Jint"]) * n_act ** 2,
          "ASSUMED servo output-referred inertia x n^2 on each engine axis [kg m2] (Electronics SIL J_INT 2e-3 ASSUMED; "
          "0 = not modelled; used by act_model 1 only)")
        # servo DATASHEET points for the voltage-dependent torque-speed line (supply-sag model)
        tqp = sorted((float(k.rstrip("V")), float(x)) for k, x in tvc["stall_torque_Nm"]["v"].items())
        spp = sorted((float(k.rstrip("V")), 60.0 / float(x)) for k, x in tvc["noload_speed_dps"]["v"].items())
        if len(tqp) != 3 or [x[0] for x in tqp] != [x[0] for x in spp]:
            raise ValueError("supply-sag model expects three DATASHEET voltage points for torque and speed")
        for j_ in range(3):
            S(f"act_V{j_}", tqp[j_][0], "electronics.json DATASHEET voltage point [V]")
            S(f"act_T{j_}", tqp[j_][1], f"electronics.json DATASHEET stall torque at {tqp[j_][0]} V [N m]")
            S(f"act_s{j_}", spp[j_][1], f"DERIVED electronics.json DATASHEET time per 60 deg at {spp[j_][0]} V [s]")
        if cfg["supply_chain"] is not None and int(cfg["act_model"]) != 1:
            raise ValueError("supply_chain (plug-voltage sag) acts through act_model 1 only")
        if cfg["supply_chain"] is None:
            S("act_sag", 0, f"CONFIG fixed servo plug voltage {vtag} for the whole flight")
        else:
            ch = supply_chain(cfg["supply_chain"])
            if cfg["supply_Vrest"] is None:
                v_rest = rest_for_hold(ch, float(cfg["servo_V"]))
                vr_tag = (f"DERIVED rest voltage for a plug voltage of {vtag} with both servos at stall (HOLD) on chain "
                          f"{cfg['supply_chain']}")
            else:
                v_rest = float(cfg["supply_Vrest"])
                vr_tag = f"CONFIG rest voltage (HOLD plug voltage {hold_plug_voltage(ch, v_rest):.3f} V on chain {cfg['supply_chain']})"
            ctag = f"Electronics {ch['tool']} {ch['date']} chain {cfg['supply_chain']} ({ch['src']})"
            S("act_sag", 1, "CONFIG resistive supply chain: plug voltage sags with the servo currents (sim6 v2.5)")
            S("act_Vrest", v_rest, vr_tag + " [V]")
            S("act_Rs", ch["Rs"], ctag + ": shared source resistance incl. pack [ohm] (elements ASSUMED/DATASHEET there)")
            S("act_Rc", ch["Rc"], ctag + ": TVC common path resistance [ohm]")
            S("act_Rb", ch["Rb"], ctag + ": per-servo branch resistance [ohm]")
            S("act_Io", ch["Io"], ctag + ": other loads during the landing burn [A] (ASSUMED there)")
            S("act_Irun", ch["Irun"], ctag + ": servo running (no-load) current [A] (DATASHEET)")
            S("act_Ia", ch["Ia"], ctag + ": servo stall current I = Ia + Ik V, intercept [A] (DATASHEET 2 points)")
            S("act_Ik", ch["Ik"], ctag + ": servo stall current slope [A/V] (DATASHEET 2 points)")
    else:
        S("gim_n", 0.0, "linear linkage (RV-1b)")
        S("gim_rate_nl", eng_side["noload_rate_dps"], "electronics.json v1 engine-side no-load rate at 7.4 V [deg/s]")
        S("gim_stall_engine", eng_side["stall_torque_Nm"], "electronics.json v1 engine-side stall torque [N m]")
        S("gim_deadband", dyn["deadband_deg_engine"], "electronics.json v1 deadband at the engine [deg]")
        S("gim_backlash", dyn["backlash_deg_engine"], "electronics.json v1 backlash at the engine [deg]")
        hb = tvc["hinge_moment_assumed_Nm"]["v"]["breakdown"]
        S("hose_K", hb["hose"] / np.radians(7.0), "DERIVED electronics.json v1 hose hinge share at 7 deg -> N m/rad")
        S("gim_fric", hb["friction"], "electronics.json v1 hinge friction share [N m]")
        S("gim_stop", 0.0, "per-axis clamp at 1.05 x gim_max (RV-1b)")
        if int(cfg["act_model"]) != 0 or cfg["act_n"] is not None:
            raise ValueError("act_model 1 / act_n need the RV-1c Cardan linkage (mechanical.json)")
        S("act_model", 0, "CONFIG reference servo (RV-1b linear linkage)")
    S("att_wn", cfg["att_wn"], "DESIGN attitude bandwidth landing [rad/s]")
    S("att_zeta", cfg["att_zeta"], "DESIGN attitude damping")
    S("att_ki", 0.1 * cfg["att_wn"] ** 3, "DESIGN attitude integral gain 0.1 wn^3")
    S("att_wn_asc", cfg["att_wn_asc"], "DESIGN attitude bandwidth ascent [rad/s]")
    S("tilt_max_land", cfg["tilt_max_land"], "DESIGN tilt limit during the landing burn [deg]")
    S("tilt_max_asc", cfg["tilt_max_asc"], "DESIGN tilt limit during ascent [deg]")
    S("tilt_term", cfg["tilt_term"], "DESIGN tilt limit below 1 m (touchdown criterion 5 deg) [deg]")
    S("tilt_term_hi", cfg["tilt_term_hi"], "DESIGN tilt limit at the terminal gate (ht), tapering to tilt_term at 1 m [deg]")
    S("lat_mode", cfg["lat_mode"], "CONFIG 0 PD / 1 ZEM-ZEV / 2 convex-lite")
    S("lat_wn", cfg["lat_wn"], "DESIGN lateral PD bandwidth [rad/s]")
    S("lat_zeta", cfg["lat_zeta"], "DESIGN lateral PD damping")
    S("target_x", 0.0, "CONFIG pad"); S("target_y", 0.0, "CONFIG pad")
    S("vert_mode", cfg["vert_mode"], "CONFIG 0 reference+PI / 1 ZEM-ZEV")
    S("div_margin", cfg["div_margin"], "DESIGN divert-radius margin")
    S("t_hmin", cfg["t_hmin"], "DESIGN horizon floor for ZEM/ZEV and convex-lite gains [s]")
    S("mis_x", d["mis_x"], "MC U(-0.25, 0.25) deg per axis (brief)")
    S("mis_y", d["mis_y"], "MC U(-0.25, 0.25) deg per axis (brief)")
    S("cg_x", d["cg_x"], "MC N(0, 2 mm) lateral CG offset ASSUMED"); S("cg_y", d["cg_y"], "MC N(0, 2 mm)")
    S("zcg_err", out_d[1] - out_n[1], "DERIVED axial CG error vs the nominal used by the controller")
    S("roll_torque", cfg["roll_torque"], "ASSUMED engine roll torque at F_max: straight port (relay) has no designed "
      "torque; residual MC U(-roll_amp, +roll_amp), roll_amp 0.02 N m ASSUMED (v1 helical-port estimate 0.01-0.1 N m)")
    S("rcs_on", 1.0 if cfg["rcs"] else 0.0, "CONFIG roll RCS")
    S("rcs_torque", cfg["rcs_torque"] if cfg["rcs_torque"] is not None else 2.0 * cfg["rcs_thrust"] * geo["d"] / 2.0,
      "DERIVED N2O-vapour RCS couple [N m] = 2 x rcs_thrust (ASSUMED 0.5 N per nozzle) x body radius")
    S("rcs_deadband", np.radians(cfg["rcs_deadband_dps"]), "DESIGN RCS roll-rate deadband")
    S("wind_u", cfg["wind"], "MC U(0, 8) m/s at 10 m per brief")
    S("wind_dir", cfg["wind_dir"], "MC U(0, 2 pi)")
    S("wind_alpha", 0.14, "ASSUMED power-law shear exponent (open terrain)")
    S("gust_on", 1.0 if cfg["gust"] else 0.0, "CONFIG Dryden turbulence (MIL-F-8785C low altitude)")
    S("gust_scale", cfg["gust_scale"], "MC U(0.5, 1.5) on sigma_w = 0.1 W20")
    S("rho0", cfg["rho0"], "MC U(1.10, 1.25) kg/m3 (ACEMA elevation and temperature unknown)")
    S("drogue_CdA", cfg["drogue_CdA"] * d["drogue_f"] if prof == "A-D" else 0.0, "ASSUMED 0.9 m drogue class; MC x U(0.85, 1.15)")
    S("descent_mode", 1.0 if prof == "A-D" else 0.0, "CONFIG")
    S("fins_on", 1.0 if cfg["fins"] else 0.0, "CONFIG")
    S("ascent_bias_x", cfg["ascent_bias"][0], "DESIGN upwind ascent bias velocity [m/s]")
    S("ascent_bias_y", cfg["ascent_bias"][1], "DESIGN")
    S("slosh_on", 1.0 if cfg["slosh"] else 0.0, "CONFIG")
    S("slosh_zeta", d["slosh_zeta"], "ASSUMED unbaffled slosh damping; MC U(0.005, 0.02)")
    imu = IMU[cfg["imu"]]
    n_on = 1.0 if cfg["noise"] else 0.0
    S("g_bx", d["g_b"][0], imu["tag"]); S("g_by", d["g_b"][1], "IMU class"); S("g_bz", d["g_b"][2], "IMU class")
    S("a_bx", d["a_b"][0], "IMU class"); S("a_by", d["a_b"][1], "IMU class"); S("a_bz", d["a_b"][2], "IMU class")
    S("g_sf", d["g_sf"], "IMU class"); S("a_sf", d["a_sf"], "IMU class")
    S("g_arw", imu["g_nd"] * n_on, "IMU class noise density [rad/s/rtHz]")
    S("a_vrw", imu["a_nd"] * n_on, "IMU class noise density [m/s2/rtHz]")
    S("vib_sigma", 2.0 * n_on, "ASSUMED thrust-proportional accelerometer vibration noise at F_max [m/s2 per 1 kHz sample]")
    S("align_x", d["align"][0], "IMU class levelling error"); S("align_y", d["align"][1], "IMU class")
    S("align_z", d["align"][2], "ASSUMED heading error 2 deg")
    gn = GNSS[cfg["gnss"]]
    S("gnss_sp_h", gn["sp_h"] * n_on, gn["tag"]); S("gnss_sp_v", gn["sp_v"] * n_on, "GNSS class")
    S("gnss_sv", gn["sv"] * n_on, "GNSS class"); S("gnss_rate", gn["rate"], "GNSS class")
    S("gnss_lat", gn["lat"], "GNSS class"); S("gnss_bx", d["gnss_b"][0], "GNSS class")
    S("gnss_by", d["gnss_b"][1], "GNSS class"); S("gnss_bz", d["gnss_b"][2], "GNSS class")
    S("gnss_bsh", gn["bsh"], "GNSS class (filter R)"); S("gnss_bsv", gn["bsv"], "GNSS class (filter R)")
    S("lidar_on", 1.0 if cfg["lidar"] else 0.0, "CONFIG")
    S("lidar_sigma", 0.03, "ASSUMED 40 m-class single-beam LiDAR, 3 cm + 1 % of range")
    S("lidar_frac", 0.01, "ASSUMED")
    S("lidar_range", cfg["lidar_range"], "ASSUMED")
    S("baro_sigma", 0.2 * n_on + 1e-3, "ASSUMED barometer noise [m]")
    S("baro_bias", d["baro_b"], "ASSUMED pad-zeroed baro drift + descent static-pressure error N(0, 1 m)")
    S("baro_bsig", 1.0, "ASSUMED (filter R)")
    S("mest", d["m_est_err"], "MC N(0, 0.03) guidance mass-knowledge error")
    S("dt", cfg["dt"], "SIM integration step")
    S("tmax", cfg["tmax"], "SIM")
    S("seed", cfg["seed"], "SIM")
    S("rec_dt", cfg["rec_dt"], "SIM")
    S("hold_tw", 1.0, "CONFIG release at T/W = 1 (stand)")
    S("t_post", 2.0, "SIM post-touchdown time for tip-over check [s]")
    S("h_bias_nav", 0.0, "SIM")
    S("fuel_phi", cfg["fuel_phi"], "combustion.json v1 plant phi (0 = Pc closed loop compensates the fuel lag)")
    S("tau_fuel", cfg["tau_fuel"], "combustion.json v1 plant tau_f 0.1-0.5 s")
    apn, _ = aero.build_aero_params(dict(geo, drogue_CdA=0.0), {})
    S("drag_cda_nom", apn[aero.A_SREF] * apn[aero.A_CA0_TF] * (0.5 + 0.5 * apn[aero.A_K_RETRO]),
      "DESIGN guidance drag model: NOMINAL S x CA0_tf x (0.5 + 0.5 k_retro) [m2] (not the dispersed truth)")
    S("dff", 1.0 if cfg["dff"] else 0.0, "DESIGN lateral disturbance feed-forward in the landing burn (on/off)")
    S("dff_tau", cfg["dff_tau"], "DESIGN disturbance-estimate low-pass time constant [s]")
    S("gim_lpf_w", cfg["gim_lpf_w"], "DESIGN structural low-pass on the gimbal command [rad/s] (m2_csi filter trade: 2nd order, 0 = off)")
    S("gim_lpf_z", cfg["gim_lpf_z"], "DESIGN structural low-pass damping")
    S("gim_cmd_rate", cfg["gim_cmd_rate"], "DESIGN gimbal command slew-rate limit at the engine [deg/s] (0 = off)")
    S("gim_cmd_acc", cfg["gim_cmd_acc"], "DESIGN gimbal command acceleration limit at the engine [deg/s2] (0 = off; "
                                         "sim6 v2.6 rate/acceleration-limited tracker)")
    S("gim_aw_thr", cfg["gim_aw_thr"], "DESIGN ECU command re-initialisation threshold |shaped command - encoder| [deg] "
                                       "(0 = off; sim6 v2.6)")
    S("gim_aw_tau", cfg["gim_aw_tau"], "DESIGN ECU engine-rate estimate filter [s]")
    S("att_ref_rate", cfg["att_ref_rate"], "DESIGN attitude-command reference governor: max slew of the commanded "
                                           "thrust direction [deg/s] (0 = off; sim6 v2.6)")
    S("att_ref_win", cfg["att_ref_win"], "DESIGN reference-governor window after each loop activation [s] (0 = always)")
    S("att_ref_rate2", cfg["att_ref_rate2"], "DESIGN reference-governor slew after the window [deg/s]")
    S("att_ref_mode", cfg["att_ref_mode"], "DESIGN reference-governor mode (0 = rate limit only; 1 = ratchet: the reference "
                                           "restarts from the estimated body axis when the body is closer to the demand; "
                                           "sim6 v2.6)")
    S("gim_notch_f", cfg["gim_notch_f"], "DESIGN ENG-07d notch centre on the engine-angle command [Hz] (0 = off; ECU "
                                         "Notch2, set from the B-TVC-1 measured rocking mode)")
    S("gim_notch_q", cfg["gim_notch_q"], "DESIGN ENG-07d notch Q (ECU config default 1.0)")
    S("gim_notch_db", cfg["gim_notch_db"], "DESIGN ENG-07d notch depth [dB] (ECU config default -12)")
    S("gim_enc_q", np.radians(cfg["gim_enc_q"]), "DATASHEET AS5048A 14-bit (0.022 deg/LSB, electronics.json v1) [rad]")
    S("kt_lat", cfg["kt_lat"], "DESIGN terminal-phase lateral velocity gain [1/s]")
    S("t_hand", cfg["t_hand"], "DESIGN ZEM/ZEV vertical (vert_mode 1): hand-over to the terminal law when tgo < t_hand [s] (sim6 v2.3)")
    S("rot_int", cfg["rot_int"], "NUMERICAL rotational integrator: 1 = torque kick + exact axisymmetric free motion (sim6 v2.4), "
                                 "0 = explicit Euler (sim6 v2.3)")
    S("roll_comp_tau", cfg["roll_comp_tau"], "DESIGN roll-rate compensation of the gimbal command, effective lag [s] (0 = off)")
    # v2.6 shutdown/MECO/relight (lead decisions 2026-10-12 on the MKS HV69 pintle drive; all off by default)
    S("toff_model", cfg["toff_model"], "CONFIG shutdown model: 0 = first-order t_off (v2.5), 1 = pintle lift ramp on the "
                                       "Combustion lift-thrust table (gncsim.tailoff)")
    if int(cfg["toff_model"]) == 1 or cfg["meco_td"] > 0.0:
        chk, chk_sha, chk_path = tailoff.load_checks(comb, SNAP)
        tl_, tf_, vs_, _tg = tailoff.table(chk, cfg["pintle_full_stroke"])
        cal = tailoff.calibration(chk_sha, cfg["pintle_full_stroke"])
        src_ = (f"combustion.json {comb.get('version')} speed_checks {os.path.basename(chk_path)} "
                f"(sha256 {chk_sha[:12]}), full stroke {cfg['pintle_full_stroke']} s")
        S("toff_vs", vs_, "SIM pintle closing speed [mm/s] at " + src_ + " (lead: MKS HV69 ~0.25 s full stroke, provisional)")
        S("toff_lag_a", cal["lag_a_s"], "DERIVED GNC fit (data/tailoff/tailoff_fit_v1.json) to Combustion t10/impulse "
                                        "(Combustion ASSUMES a 10 ms actuator lag) [s]")
        S("toff_lag_c", cal["lag_c_s"], "DERIVED GNC fit, chamber/feed lag of the reduced model [s]")
        S("toff_l0", cal["l_cut_mm"], "DERIVED GNC fit, lift where thrust reaches zero [mm]")
        for i_ in range(5):
            S(f"toff_l{i_ + 1}", tl_[i_], "SIM pre-shutdown lift [mm], " + src_)
            S(f"toff_f{i_ + 1}", tf_[i_], "SIM pre-shutdown thrust [N], " + src_)
    S("meco_td", cfg["meco_td"], "DESIGN pre-MECO throttle-down command [fraction F_max] (0 = off; lead decision "
                                 "2026-10-12: MECO from <= 75 % so a 0.25 s stroke meets ENG-05)")
    S("meco_td_max", cfg["meco_td_max"], "REQ-derived MECO allowed only when measured thrust <= this fraction of F_max "
                                         "(lead rule <= 75 %)")
    S("meco_td_hold", cfg["meco_td_hold"], "DESIGN planned hold at the throttle-down level in the MECO predictor [s]")
    S("relight_start_frac", cfg["relight_start"], "DESIGN relight start level [fraction F_max] held until 90 % of it is "
                                                  "reached, then guidance throttles (0 = start at the floor)")
    if int(cfg["act_model"]) != 0 and not (rv1c and cfg["rock"]):
        raise ValueError("act_model 1 acts through the flexible engine mount: needs vehicle RV-1c and rock=True")
    if rv1c and cfg["rock"]:
        kax = mech["tvc_actuation"]["axis_stiffness_Nm_per_rad"]["v"]
        k0_ = kax[0] if d["rock_K"] is None else d["rock_K"]
        if cfg["act_n"] is None:
            S("rock_K", k0_,
              f"mechanical.json {mech['version']} axis stiffness (low end {kax[0]} nominal; MC U({kax[0]}, {kax[1]})) [N m/rad]")
        else:
            n_m = mech["tvc_actuation"]["gear_ratio_n"]["v"]
            if str(mech.get("version")) != "v1" and abs(float(cfg["act_n"]) - n_m) > 1e-9:
                # run6 v2.6: from mechanical.json v2 the range is the FEA structure in series with the servo, so only the
                # servo part would scale with n^2; a different linkage ratio needs the split, not a rescale
                raise ValueError(f"act_n {cfg['act_n']} differs from mechanical.json {mech.get('version')} n {n_m}: the "
                                 "published axis stiffness includes the structure (no n^2 rescale)")
            fk_ = (float(cfg["act_n"]) / n_m) ** 2
            if str(mech.get("version")) != "v1":
                S("rock_K", k0_, f"mechanical.json {mech['version']} axis stiffness: FEA structure + rods (9 poses) in series "
                                 f"with the ASSUMED servo 58-174 N m/rad x n^2 (nominal {kax[0]:.0f}; MC U({kax[0]:.0f}, "
                                 f"{kax[1]:.0f})) [N m/rad]")
        if cfg["act_n"] is not None and str(mech.get("version")) == "v1":
            S("rock_K", k0_ * fk_,
              f"DERIVED mechanical.json {mech['version']} axis stiffness (k_servo x n^2) rescaled by (n / {n_m})^2 = {fk_:.4f} "
              f"(nominal {kax[0] * fk_:.0f}; MC U({kax[0] * fk_:.0f}, {kax[1] * fk_:.0f})) [N m/rad]")
        S("rock_zeta", cfg["rock_zeta"] if d["rock_zeta"] is None else d["rock_zeta"],
          "ASSUMED engine-mount rocking damping (not published; MC U(0.02, 0.10))")
    else:
        S("rock_K", 0.0, "rigid engine mount")
        S("rock_zeta", 0.0, "rigid engine mount")
    if float(cfg.get("gim_notch_track", 0.0) or 0.0) > 0.0:
        # v2.6: ENG-07d notch centred on this run's own rocking mode in the landing burn (K on the engine axis over the
        # landing-state engine inertia about the pivot + reflected rotor), times a mistune factor (B-TVC-1 measurement
        # error + in-flight shift): disp notch_mis if drawn, else cfg gim_notch_track
        if not (rv1c and cfg["rock"]):
            raise ValueError("gim_notch_track needs the flexible engine mount (RV-1c, rock=True)")
        o_ = np.zeros(8)
        veh.massprops(mp, 0.3, 0.0, par[s6.P_rho_l_nom], m_fuel0 * 0.75, o_)
        Ip_ = o_[6] + o_[4] * (mp[15] - o_[5]) ** 2
        f_r_ = float(np.sqrt(par[s6.P_rock_K] / (Ip_ + par[s6.P_act_Jint])) / (2.0 * np.pi))
        mis_ = d["notch_mis"] if d.get("notch_mis") is not None else float(cfg["gim_notch_track"])
        S("gim_notch_f", mis_ * f_r_, f"DESIGN ENG-07d notch tracking the run's landing-burn rocking mode {f_r_:.2f} Hz x "
                                      f"mistune {mis_:.3f} [Hz]")
    # v2.8-dev amendment F (review RG-18): stuck-pintle fault, in-loop detectors, abort (off by default)
    S("flt_on", float(cfg["flt_on"]), "CONFIG 1 = stuck-pintle over-thrust fault flown (sim6 v2.8-dev amendment F)")
    S("flt_ph", float(cfg["flt_ph"]), "CONFIG fault onset phase: 1 boost, 2 B floor phases, 5 landing burn")
    S("flt_t", float(cfg["flt_t"]), "CONFIG/MC onset time: flight time (phases 1-2) or time after the landing-burn start (5) [s]")
    S("flt_F", float(cfg["flt_F"]), "REQ review RG-18 stuck level [N] (670 N = threshold + 20 N; 876 N Combustion full-open "
                                    "MEOP stuck-pintle case)")
    S("flt_rate", float(cfg["flt_rate"]), "ASSUMED excursion ramp [N/s] (m2_fc_thrust v1.1 synthetic ramps 2.5 / 3.6 kN/s)")
    S("flt_enc", float(cfg["flt_enc"]), "CONFIG 1 = the pintle encoder sees the jam (PINTLE_FAULT path); 0 = linkage failure "
                                        "the encoder does not see")
    S("flt_pcl", float(cfg["flt_pcl"]), "CONFIG 1 = Pc invalid (ECU over-pressure check blind)")
    S("flt_persist", float(cfg["flt_persist"]), "CONFIG 1 = the fault persists through a normal close and re-activates at "
                                                "the next start (linkage still broken)")
    S("det_fct", float(cfg["det_fct"]), "CONFIG FC_THRUST over-thrust abort active (firmware v2.8.1: also with a valid Pc)")
    S("det_op", float(cfg["det_op"]), "CONFIG ECU over-pressure abort active (firmware kPcOverPressureAbs_Pa, Pc valid)")
    S("det_pf", float(cfg["det_pf"]), "CONFIG PINTLE_FAULT stall/tracking abort active (firmware v2.6 time path)")
    S("det_geo", float(cfg["det_geo"]), "CONFIG geofence abort (GNC PROPOSAL, research; off in the baseline)")
    S("fct_thr", float(cfg["fct_thr"]), "REQ LEAD 2026-10-13 ADOPTED over-thrust threshold [N] (firmware kOverThrust_N)")
    S("fct_n", float(cfg["fct_n"]), "REQ LEAD 2026-10-13 ADOPTED consecutive frames (firmware kOverThrustFrames)")
    S("fct_tau", float(cfg["fct_tau"]), "REQ LEAD / GNC m2_fc_thrust v1.1 first-order estimate filter [s]")
    S("fct_hz", float(cfg["fct_hz"]), "REQ interface FC_THRUST frame rate [Hz] (firmware kFcThrustRate_Hz)")
    S("fct_ph", float(cfg["fct_ph"]), "MC frame phase [s] (U(0, 1 / fct_hz) per run in the fault Monte Carlo)")
    S("fct_comp", float(cfg["fct_comp"]), "DESIGN 1 = lever-arm / encoder-direction compensation in F_acc (RG-16 proposal)")
    pcm_ = np.asarray(tab["pc"], float)[:, 0]
    Fgm_ = np.asarray(tab["Fg"], float)
    if not (np.all(np.diff(pcm_) > 0) and pcm_[0] < float(cfg["det_op_Pabs"]) < pcm_[-1]):
        raise ValueError("amendment F: the map Pc(F) must be increasing and bracket the over-pressure threshold")
    S("det_op_F", float(np.interp(float(cfg["det_op_Pabs"]), pcm_, Fgm_)),
      f"DERIVED map thrust at the ECU over-pressure abort {cfg['det_op_Pabs'] / 1e5:.1f} bar abs (firmware kPcAbortAbs_Pa via "
      "engine_params.h; combustion map Pc(F), port-independent) [N, Pc-equivalent]")
    S("det_op_t", float(cfg["det_op_t"]), "DESIGN firmware kPcOverPressureTime_s persistence [s] (Pc filter lag not modelled)")
    # v2.8-dev amendment R (coordinator relay 2026-10-13, light-detection fix): drogue release rule
    S("rel_mode", float(cfg["rel_mode"]), "CONFIG 0 = v2.8 model (F > 0.5 floor); 1 = adopted rule: E2 (relative light "
                                          "confirmation) AND measured Pc >= rel_Pc")
    if not (pcm_[0] < float(cfg["rel_Pc"]) < pcm_[-1]):
        raise ValueError("amendment R: the map Pc(F) must bracket the release pressure")
    S("rel_F", float(np.interp(float(cfg["rel_Pc"]), pcm_, Fgm_)),
      f"DERIVED map thrust at the drogue-release pressure {cfg['rel_Pc'] / 1e5:.2f} bar abs (LEAD 2026-10-13 fixed value, not "
      "tied to the floor; combustion map Pc(F), port-independent) [N, Pc-equivalent]")
    S("rel_dt", float(cfg["rel_dt"]), "ASSUMED E2 (relative rule: +0.8 bar over the pre-lift baseline, 10 ms) after the 6-DOF "
                                      "light [s]; 0 = the relative E2 (14.0-15.5 ms after main ignition, Combustion "
                                      "ignition_detect_v2p4) precedes the 6-DOF light drawn on the old 3.0 bar rule")
    # v2.8-dev amendment S (review RG-01 start-transient re-fly; LEAD 2026-10-13 release rule): A-relight start plateau and the
    # drogue-release persistence branch
    S("st_on", float(cfg["st_on"]), "CONFIG 1 = A-relight start plateau after the light (sim6 v2.8-dev amendment S)")
    for k_ in ("st_Pc", "rel_rise_Pc"):
        if not (pcm_[0] < float(cfg[k_]) < pcm_[-1]):
            raise ValueError(f"amendment S: the map Pc(F) must bracket {k_}")
    S("st_F", float(np.interp(float(cfg["st_Pc"]), pcm_, Fgm_)),
      f"DERIVED map thrust at the plateau Pc {cfg['st_Pc'] / 1e5:.2f} bar abs (Combustion ignition_detect_v2p4 part B / "
      "drogue_hold_check_v2p4 fuel-starved start bracket 2.4-3.6 bar abs; combustion map Pc(F)) [N, Pc-equivalent]")
    S("st_T", float(cfg["st_T"]), "DERIVED plateau duration after the 6-DOF light [s] (Combustion bracket 0.1-0.4 s)")
    S("rel_to", float(cfg["rel_to"]), "DESIGN release persistence timeout after E2 [s] (LEAD 2026-10-13: 0.10 s); 0 = branch off")
    S("rel_Frise", float(np.interp(float(cfg["rel_rise_Pc"]), pcm_, Fgm_)),
      f"DERIVED map thrust at the rise threshold {cfg['rel_rise_Pc'] / 1e5:.4f} bar abs = pre-lift baseline (ISA 1.01325 bar "
      "ASSUMED + torch 0.3 bar, Combustion B-PC-1 target, upper) + 0.8 bar (LEAD rule) [N, Pc-equivalent]")
    S("det_pf_t", float(cfg["det_pf_t"]), "DESIGN firmware kPintleStallTime_s, no-progress time path [s] (LEAD approved)")
    if par[s6.P_toff_l5] > par[s6.P_toff_l1] > 0.0:
        tl_ = [par[getattr(s6, f"P_toff_l{i_}")] for i_ in range(6)]
        tf_ = [0.0] + [par[getattr(s6, f"P_toff_f{i_}")] for i_ in range(1, 6)]
        slope_ = max((tf_[i_ + 1] - tf_[i_]) / (tl_[i_ + 1] - tl_[i_]) for i_ in range(5))
        S("det_pf_dF", float(cfg["det_pf_err_m"]) * 1e3 * slope_,
          f"DERIVED firmware kPintleStallErr_m {cfg['det_pf_err_m'] * 1e3:.2f} mm x the steepest slope {slope_:.1f} N/mm of "
          "the lift-thrust table (latest trip) [N, Pc-equivalent]")
    else:
        S("det_pf_dF", 60.0, "ASSUMED tracking band in thrust when the lift table is not loaded [N]")
    S("geo_dh", float(cfg["geo_dh"]), "PROPOSAL GNC geofence margin above h_target [m] (research, RG-18)")
    S("abt_lat", float(cfg["abt_lat"]), "DERIVED Electronics over_thrust_v3.json (770bf284d14b1336): CAN <= 0.48 ms incl. the "
                                        "ABORT frame + ECU <= 1.2 ms [s]")
    S("abt_seat", float(cfg["abt_seat"]), "ESTIMATE Electronics over_thrust_v3: latch release 9.4 ms + MV-P close 30 ms "
                                          "(ESTIMATE; B-MV-1 bound 0.10 s close) [s]")
    S("abt_sdto", float(cfg["abt_sdto"]), "DESIGN firmware kMvSeatTimeout_s (COMB v2.4 / LEAD 2026-10-13) [s]")
    S("abt_sdenc", float(cfg["abt_sdenc"]), "ASSUMED normal pintle closing from <= 75 % in 0.059-0.083 s (ENG-05, MECH "
                                            "pintle_dynamics_v2) + 5 x 1 ms seat confirmation [s]")
    S("abt_imp", float(cfg["abt_imp"]), "SIM Combustion v2.4 tail-off 37.5-38.2 N s after the MV closes (upper value) [N s]")
    # v2.8-dev amendment P (coordinator relay 2026-10-13, RG-01 re-fly model): A-relight forced purge and stuck-open bleed
    S("prg_on", float(cfg["prg_on"]), "CONFIG 1 = forced purge before the A relight lift (sim6 v2.8-dev amendment P)")
    S("prg_T", float(cfg["prg_T"]), "DESIGN LEAD relay 2026-10-13: bleed open 2-3 s ending at the lift [s] (Combustion "
                                    "purge_sizing_v2p4 P_abort 0 needs 1.0-2.0 s)")
    S("prg_lead", float(cfg["prg_lead"]), "PROPOSAL GNC extra anticipation of the purge-start trigger [s]")
    S("prg_mdot", float(cfg["prg_mdot"]), "DERIVED Combustion purge_sizing_v2p4 (workdir, hub pending): liquid through the "
                                          "bleed 11.25 g/s (0.6 mm) / 20.0 g/s (0.8 mm) at the coast state, Cd 0.70 ASSUMED; "
                                          "the whole purge taken as liquid (upper bound) [kg/s]")
    pmh_ = cfg["prg_mdot_hat"] if cfg["prg_mdot_hat"] is not None else cfg["prg_mdot"]
    S("prg_mdot_hat", float(pmh_), "DESIGN flight-software purge flow booked into m_hat [kg/s] (nominal = truth unless set; "
                                   "CF-4 cold flow calibrates it)")
    S("prg_book", float(cfg["prg_book"]), "DESIGN 1 = the flight software books the commanded purge into m_hat")
    S("prg_jet", float(cfg["prg_jet"]), "CONFIG 1 = the purge jet acts as a radial force (vent direction TO-DEFINE)")
    S("prg_prio", float(cfg["prg_prio"]), "PROPOSAL GNC 1 = the lift keeps the plain relight trigger and a late purge is "
                                          "truncated; 0 = the lift waits for prg_T (a 2 s wait at the drogue descent rate "
                                          "crashes: test_P smoke run)")
    S("blf_on", float(cfg["blf_on"]), "CONFIG 1 = stuck-open head-end bleed fault flown (amendment P)")
    S("blf_ph", float(cfg["blf_ph"]), "CONFIG bleed fault onset: 0 = first ignition, 4 = the A relight lift (fails to close)")
    S("blf_mdot", float(cfg["blf_mdot"]), "DERIVED coordinator relay of Combustion 2026-10-13: stuck-open bleed during a burn "
                                          "6.3-19.4 g/s (3-8 % of the engine flow at 0.6 mm, up to 14 % at 0.8 mm) [kg/s]")
    S("blf_mode", float(cfg["blf_mode"]), "CONFIG 0 = additive bracket (engine flow kept, tank loses more); 1 = subtractive "
                                          "bracket (bleed taken from the injector flow, thrust drops)")
    S("blf_n", float(cfg["blf_n"]), "ASSUMED fuel-flow exponent on the oxidiser flux for the subtractive bracket")
    S("blf_fmax", float(cfg["blf_fmax"]), "DERIVED coordinator relay: bleed share of the engine flow up to 14 % (0.8 mm); cap of "
                                          "the subtractive bracket")
    S("bl_vj", float(cfg["bl_vj"]), "DERIVED Combustion purge_sizing_v2p4 jet thrust / liquid flow = 1.190 N / 11.25 g/s = "
                                    "2.116 N / 20.0 g/s = 105.8 m/s; 0 = balanced or axial vent [m/s]")
    S("bl_az", float(cfg["bl_az"]), "ASSUMED radial vent azimuth in the body frame [rad] (T4 port cross-drilling; direction "
                                    "TO-DEFINE by Mechanical)")
    # v2.9-dev amendment G (LEAD 2026-10-13, CHANGELOG lines 161 (4) and 164 (2)): decided purge sequence and trigger gate
    if float(cfg["pgg_on"]) > 0.5 and float(cfg["prg_on"]) < 0.5:
        raise ValueError("amendment G needs prg_on 1 (it replaces the amendment-P purge start and keeps its mass model)")
    S("pgg_on", float(cfg["pgg_on"]), "CONFIG 1 = decided purge sequence with the trigger gate (sim6 v2.9-dev amendment G)")
    S("pgg_Tc", float(cfg["pgg_Tc"]), "DESIGN LEAD line 164 (2): PURGE command at E0 - 2.90 s; T_fire = commit + pgg_Tc [s]")
    S("pgg_ton", float(cfg["pgg_ton"]), "DERIVED Combustion rg01_line_states_v2p4 timing MV_open_ramp_s 0.35: command to flow [s]")
    S("pgg_Tp", float(cfg["pgg_Tp"]), "DESIGN LEAD line 164 (1): 2.5 s of FLOW (both taps) ending at E0 - 0.05 s [s]")
    S("pgg_toff", float(cfg["pgg_toff"]), "DESIGN LEAD line 164 (1): flow stopped 0.05 s before E0 [s]")
    S("pgg_tcl", float(cfg["pgg_tcl"]), "DERIVED Combustion timing note (Electronics S12): valve closing 77 ms after the close "
                                        "command, used when the plain trigger brings E0 forward [s]")
    S("pgg_Tmin", float(cfg["pgg_Tmin"]), "DESIGN LEAD line 164 (2) / Combustion line 163: never commit T_fire before 1.9 s of "
                                          "flow (P_abort <= 1e-3 unlined, 0-2 deg) [s]")
    S("pgg_cap", float(cfg["pgg_cap"]), "DESIGN LEAD line 164 (2): ECU cap = 2.5 s of flow + measured valve times (flow-time "
                                        "cap in sim6) [s]")
    S("pgg_gate", float(cfg["pgg_gate"]), "DESIGN LEAD line 161 (4): 1 = commit predictor only once the drogue descent is "
                                          "quasi-steady")
    S("pgg_aqs", float(cfg["pgg_aqs"]), "PROPOSAL GNC amendment a: quasi-steady band of the filtered vertical acceleration [m/s2]")
    S("pgg_tqs", float(cfg["pgg_tqs"]), "PROPOSAL GNC amendment a: time inside the band before the gate opens [s]")
    S("pgg_tau", float(cfg["pgg_tau"]), "PROPOSAL GNC amendment a: low-pass time constant of the vertical acceleration [s]")
    S("pgg_tdmin", float(cfg["pgg_tdmin"]), "PROPOSAL GNC amendment a: minimum time after the drogue deployment [s]")
    S("pgg_cv", float(cfg["pgg_cv"]), "DESIGN LEAD line 161 (4): 1 = constant-velocity extrapolation beyond the plain lag; "
                                      "0 = constant acceleration (amendment-P form, comparison only)")
    S("pgg_ant", float(cfg["pgg_ant"]), "DESIGN commit-predictor horizon beyond the plain lag (= pgg_Tc nominal; sweeps only) [s]")
    S("pgg_ovr", float(cfg["pgg_ovr"]), "DESIGN reading of LEAD line 164 (2): 1 = the plain trigger may bring T_fire forward, "
                                        "never before pgg_Tmin of flow; 0 = T_fire fixed at commit + pgg_Tc")
    S("pgg_hfl", float(cfg["pgg_hfl"]), "PROPOSAL GNC amendment a: height floor that forces the commit [m]; 0 = off")
    # v2.9-dev amendment K (LEAD line 113 (2), review RG-15)
    S("kfz_on", float(cfg["kfz_on"]), "DESIGN LEAD line 113 (2): 1 = k_hat and the B apex-predictor thrust input freeze while "
                                      "Pc is invalid (sim6 v2.9-dev amendment K)")
    # v2.9-dev amendment V (LEAD line 161 (2), fault arm c)
    S("pcf_on", float(cfg["pcf_on"]), "CONFIG 1 = Pc invalid from E2 + pcf_dt with the drogue attached (amendment V fault arm)")
    S("pcf_dt", float(cfg["pcf_dt"]), "CONFIG Pc-invalid onset after the 6-DOF light (E2 in sim6) [s]")
    S("pcf_k", float(cfg["pcf_k"]), "ASSUMED open-loop thrust and flow per command factor after the onset (Cd band x1.143 / "
                                    "x0.875 as m2_mass_est v2 Pc-lost specs; 1 = none)")
    S("pcf_rule", float(cfg["pcf_rule"]), "CONFIG release alternative with Pc invalid: 0 none, 1 interim (LEAD line 161 (2)), "
                                          "2 accelerometer-gated (GNC PROPOSAL), 3 hold the drogue and abort")
    pfa_ = cfg["pcf_Facc"] if cfg["pcf_Facc"] is not None else par[s6.P_rel_F]
    S("pcf_Facc", float(pfa_), "PROPOSAL GNC accelerometer thrust threshold under the drogue [N] (default = rel_F, the map "
                               "thrust at the 3.0 bar abs release pressure)")
    S("pcf_n", float(cfg["pcf_n"]), "PROPOSAL GNC consecutive 100 Hz frames above pcf_Facc")
    S("pcf_tmax", float(cfg["pcf_tmax"]), "PROPOSAL GNC accelerometer confirmation deadline after E2, then abort (hold) [s]")
    S("pcf_tbl", float(cfg["pcf_tbl"]), "PROPOSAL GNC low-pass time constant of the drogue-descent axial specific force [s]")
    S("pcf_fo", float(cfg["pcf_fo"]), "CONFIG 1 = truth flame-out at the Pc-invalid onset, undetected (ECU stays in RUN; sim6 v2.9-dev V)")
    S("test_mode", cfg["test_mode"], "VERIFICATION")
    S("w0x", cfg["w0"][0], "VERIFICATION"); S("w0y", cfg["w0"][1], "VERIFICATION"); S("w0z", cfg["w0"][2], "VERIFICATION")
    S("v0z", cfg["v0z"], "VERIFICATION"); S("h0", cfg["h0"], "VERIFICATION")
    if cfg["test_mode"] > 0:
        par[s6.P_wind_u] = 0.0
    info = dict(tags=tags, geo=geo, ledger=led, mp=mp, m_liftoff=out_d[0], zcg0=out_d[1], It0=out_d[2],
                Ir0=out_d[3], tank_V=V, z_pivot=geo["z_pivot"], m_dry=sum(i["m"] for i in led_d) + 0.0,
                vehicle=cfg["vehicle"], d=geo["d"], m_e0=out_d[4], z_e0=out_d[5], I_e0=out_d[6])
    return par, apar, comp, mp, tab, info


def fly(cfg, disp=None, nrec=6000):
    par, apar, comp, mp, tab, info = build(cfg, disp)
    rec = np.zeros((nrec, s6.NREC))
    r = s6.run6(par, apar.copy(), comp, mp, tab["Fg"], tab["Dg"], tab["mox"], tab["mf"], tab["Pg"], tab["ceil"], rec)
    res = dict(zip(s6.RES_NAMES, r))
    return res, rec[: int(res["nrec"])], info


CRIT = dict(vz=2.0, vh=0.5, tilt=5.0, rate=10.0)   # REQ landing criteria (REQUIREMENTS sec. 1 item 8 + brief)


def success(res):
    return bool(res["landed"] > 0.5 and res["crash"] < 0.5 and abs(res["td_vz"]) <= CRIT["vz"]
                and res["td_vh"] <= CRIT["vh"] and res["td_tilt"] <= CRIT["tilt"]
                and res["td_rate"] <= CRIT["rate"] and res["exhausted"] < 0.5 and res["tipover"] < 0.5)


def size_load(cfg, reserve=0.20, lo=0.4, hi=6.0, iters=16):
    """Smallest N2O load whose deterministic nominal 6-DOF flight (no wind, no sensor noise) lands within
    the criteria with usable liquid >= reserve x liquid used."""
    def trial(m):
        c = dict(cfg, m_n2o=m, noise=False, wind=0.0, gust=False)
        res, rec, info = fly(c, nrec=10)
        liq0 = m  # liquid at t0 is ~ m (vapour mass small); use the record of used liquid instead
        used = res["prop_used"]
        usable = max(res["liq_left"] - 0.03 * m, 0.0)
        ok = success(res) and usable >= reserve * used
        return ok, res
    ok, res = trial(hi)
    if not ok:
        return None, res
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if trial(mid)[0]:
            hi = mid
        else:
            lo = mid
    ok, res = trial(hi)
    return hi, res


def _hose_range():
    m = sources()["mech"]
    return tuple(m["feed_across_gimbal"]["hinge_stiffness_Nm_per_rad"]["v"])


def _kax_range(cfg=None):
    """MC range of the mount stiffness in the mechanical.json basis (gear_ratio_n): mechanical.json axis_stiffness, or
    (v2.6) cfg rock_K_eng = (lo, hi) on the engine axis at the flown linkage ratio act_n, converted to that basis (build
    multiplies by (act_n / n_mech)^2). Only the bounds change: the uniform draw uses the same random number."""
    m = sources()["mech"]
    if cfg is not None and cfg.get("rock_K_eng") is not None:
        n_m = m["tvc_actuation"]["gear_ratio_n"]["v"]
        fk = ((float(cfg["act_n"]) if cfg.get("act_n") is not None else n_m) / n_m) ** 2
        lo, hi = cfg["rock_K_eng"]
        return (lo / fk, hi / fk)
    return tuple(m["tvc_actuation"]["axis_stiffness_Nm_per_rad"]["v"])


def draw(rng, n, cfg):
    imu = IMU[cfg["imu"]]
    gn = GNSS[cfg["gnss"]]
    D = []
    # v2.6: notch mistune (B-TVC-1 measurement + in-flight shift) from its own generator, so the main draws are unchanged
    w_mis = float(cfg.get("gim_notch_mis_w", 0.0) or 0.0)
    rng_mis = np.random.default_rng(20261012) if w_mis > 0.0 else None
    # v2.7: throat growth per run from its own generator (main draws unchanged)
    tgb = cfg.get("throat_g_band")
    rng_thr = np.random.default_rng(20261013) if tgb else None
    # v2.7.1-dev: regression-law band (a scale, n) per run from its own generator (main draws unchanged); uniform on each
    # (lead 2026-10-13: Combustion's recommended distribution or uniform if none)
    rgb = cfg.get("reg_band")
    rng_reg = np.random.default_rng(20261017) if rgb else None
    # v2.7.1-dev: relight start delay from a quantile table (t_ign_q: equally spaced quantiles 0..1 of the command-to-light
    # delay, e.g. Combustion RC-03 E0->E2) instead of the U(0.2, 0.6) s brief draw; own generator (main draws unchanged)
    tq = cfg.get("t_ign_q")
    rng_tq = np.random.default_rng(20261018) if tq else None
    for i in range(n):
        D.append(dict(
            thrust_scale=rng.normal(1.0, 0.05), isp_scale=rng.normal(1.0, 0.05), tau_f=rng.uniform(0.7, 1.5),
            dry_scale=rng.normal(1.0, 0.05), m_est_err=rng.normal(0.0, 0.03),
            cg_x=rng.normal(0.0, 0.002), cg_y=rng.normal(0.0, 0.002), dz_air=rng.normal(0.0, 0.03),
            mis_x=np.radians(rng.uniform(-0.25, 0.25)), mis_y=np.radians(rng.uniform(-0.25, 0.25)),
            g_b=tuple(rng.normal(0.0, imu["g_bias"], 3)), a_b=tuple(rng.normal(0.0, imu["a_bias"], 3)),
            g_sf=rng.normal(0.0, imu["g_sf"]), a_sf=rng.normal(0.0, imu["a_sf"]),
            align=(rng.normal(0.0, imu["align"]), rng.normal(0.0, imu["align"]), rng.normal(0.0, imu["yaw"])),
            gnss_b=(rng.normal(0.0, gn["bsh"]), rng.normal(0.0, gn["bsh"]), rng.normal(0.0, gn["bsv"])),
            baro_b=rng.normal(0.0, 1.0), gim_wn_f=rng.uniform(62.8, 157.1) / 94.2,
            gim_delay_add=rng.uniform(0.0, 0.0032), legs_k_f=rng.uniform(0.8, 1.2), legs_c_f=rng.uniform(0.8, 1.2),
            slosh_zeta=rng.uniform(0.005, 0.02), drogue_f=rng.uniform(0.85, 1.15),
            hose_K=(rng.uniform(*_hose_range()) if cfg["vehicle"] == "RV-1c" else None),
            rock_K=(rng.uniform(*_kax_range(cfg)) if cfg["vehicle"] == "RV-1c" else None),
            rock_zeta=(rng.uniform(0.02, 0.10) if cfg["vehicle"] == "RV-1c" else None),
            # configuration-level dispersions
            _t_ign=rng.uniform(0.2, 0.6), _T0=rng.uniform(288.15, 298.15), _wind=rng.uniform(0.0, 8.0),
            _wind_dir=rng.uniform(0.0, 2 * np.pi), _gust_scale=rng.uniform(0.5, 1.5), _rho0=rng.uniform(1.10, 1.25),
            _roll=rng.uniform(-0.1, 0.1), _legs_mu=rng.uniform(0.3, 0.7),
            _k_base_lead=rng.uniform(0.5, 1.0), _k_nose_trail=rng.uniform(0.0, 0.5), _crossflow=rng.uniform(0.75, 1.25),
            _ca_tf=rng.uniform(0.7, 1.3), _k_retro=rng.uniform(0.25, 0.75), _seed=int(rng.integers(1, 2**31 - 1)),
        ))
        if rng_mis is not None:
            D[-1]["notch_mis"] = float(1.0 + w_mis * (2.0 * rng_mis.random() - 1.0))
        if rng_thr is not None:
            D[-1]["throat_g"] = float(rng_thr.uniform(tgb[0], tgb[1]))
        if rng_reg is not None:
            D[-1]["reg_a"] = float(rng_reg.uniform(rgb[0][0], rgb[0][1]))
            D[-1]["reg_n"] = float(rng_reg.uniform(rgb[1][0], rgb[1][1]))
        if rng_tq is not None:
            u_ = float(rng_tq.random())
            D[-1]["_t_ign_q"] = float(np.interp(u_, np.linspace(0.0, 1.0, len(tq)), np.asarray(tq, dtype=float)))
            D[-1]["_t_ign_u"] = u_
    return D


ROLL_DRAW = 0.1   # draw() samples U(-0.1, 0.1); the run scales it to cfg["roll_amp"] (pairing kept across cases)


def run_cfg(cfg, dr):
    """(config, per-run dispersions) of one MC run: draw dr applied to cfg (shared by run_one and forensics)."""
    c = dict(cfg)
    t_draw = dr["_t_ign_q"] if dr.get("_t_ign_q") is not None else dr["_t_ign"]
    c.update(t_ign=t_draw + cfg.get("t_ign_add", 0.0), T0=dr["_T0"], wind=dr["_wind"], wind_dir=dr["_wind_dir"], gust=True,
             gust_scale=dr["_gust_scale"], rho0=dr["_rho0"], roll_torque=dr["_roll"] * cfg["roll_amp"] / ROLL_DRAW,
             legs_mu=dr["_legs_mu"],
             seed=dr["_seed"], aero_unc=dict(k_base_lead=dr["_k_base_lead"], k_nose_trail=dr["_k_nose_trail"],
                                             crossflow=dr["_crossflow"], ca_tf=dr["_ca_tf"], k_retro=dr["_k_retro"]))
    if cfg.get("ascent_bias_auto"):
        c["ascent_bias"] = cfg["ascent_bias_auto"](c, dr)
    disp = {k: v for k, v in dr.items() if not k.startswith("_")}
    return c, disp


def run_one(cfg, dr):
    c, disp = run_cfg(cfg, dr)
    res, rec, info = fly(c, disp, nrec=10)
    return res


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    cc = (p + z * z / (2 * n)) / den
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, cc - hw), min(1.0, cc + hw))


SCALAR_DISP = ["thrust_scale", "isp_scale", "tau_f", "dry_scale", "m_est_err", "dz_air", "gim_wn_f", "gim_delay_add", "hose_K",
               "rock_K", "rock_zeta",
               "legs_k_f", "legs_c_f", "slosh_zeta", "drogue_f", "_t_ign", "_T0", "_wind", "_gust_scale", "_rho0",
               "_roll", "_legs_mu", "_k_base_lead", "_k_nose_trail", "_crossflow", "_ca_tf", "_k_retro"]


def flat_row(i, dr, res, ok, cfg=None):
    row = dict(run=i, ok=int(ok))
    for k in s6.RES_NAMES:
        row[k] = float(res[k])
    for k in SCALAR_DISP:
        row[k.lstrip("_")] = float(dr[k]) if dr[k] is not None else float("nan")
    row["mis_deg"] = float(np.degrees(np.hypot(dr["mis_x"], dr["mis_y"])))
    row["cg_off_mm"] = float(1e3 * np.hypot(dr["cg_x"], dr["cg_y"]))
    row["g_bias_dps"] = float(np.degrees(np.hypot(dr["g_b"][0], dr["g_b"][1])))
    row["a_bias_h"] = float(np.hypot(dr["a_b"][0], dr["a_b"][1]))
    row["align_deg"] = float(np.degrees(np.hypot(dr["align"][0], dr["align"][1])))
    row["gnss_bv"] = float(dr["gnss_b"][2])
    row["gnss_bh"] = float(np.hypot(dr["gnss_b"][0], dr["gnss_b"][1]))
    row["baro_b"] = float(dr["baro_b"])
    if dr.get("notch_mis") is not None:
        row["notch_mis"] = float(dr["notch_mis"])
    if dr.get("throat_g") is not None:
        row["throat_g"] = float(dr["throat_g"])
    if dr.get("reg_a") is not None:
        row["reg_a"] = float(dr["reg_a"])
        row["reg_n"] = float(dr["reg_n"])
    if dr.get("_t_ign_q") is not None:
        row["t_ign_q"] = float(dr["_t_ign_q"])
        row["t_ign_u"] = float(dr["_t_ign_u"])
        row["start_delay"] = float(dr["_t_ign_q"]) + (cfg.get("t_ign_add", 0.0) if cfg is not None else 0.0)
    row["roll_abs"] = abs(float(dr["_roll"]))   # rank-equivalent to |roll torque| (scaled by cfg roll_amp)
    if cfg is not None:
        row["roll_Nm"] = float(dr["_roll"]) * cfg["roll_amp"] / ROLL_DRAW
    return row


def summarize(rows):
    n = len(rows)
    ok = np.array([r["ok"] for r in rows])
    k = int(ok.sum())

    def pct(key, p, absval=False):
        x = np.array([r[key] for r in rows if r["landed"] > 0.5])
        if x.size == 0:
            return float("nan")
        return float(np.percentile(np.abs(x) if absval else x, p))
    fails = {}
    for r in rows:
        if r["ok"]:
            continue
        why = []
        if r["landed"] < 0.5 or r["crash"] > 0.5:
            why.append("no_touchdown_or_crash")
        else:
            if abs(r["td_vz"]) > CRIT["vz"]:
                why.append("vz")
            if r["td_vh"] > CRIT["vh"]:
                why.append("vh")
            if r["td_tilt"] > CRIT["tilt"]:
                why.append("tilt")
            if r["td_rate"] > CRIT["rate"]:
                why.append("rate")
            if r["exhausted"] > 0.5:
                why.append("exhausted")
            if r["tipover"] > 0.5:
                why.append("tipover")
        for w_ in why:
            fails[w_] = fails.get(w_, 0) + 1
    return dict(n=n, success=k / n, ci95=wilson(k, n), fail_modes=fails,
                td_vz_p50=pct("td_vz", 50, True), td_vz_p99=pct("td_vz", 99, True),
                td_vh_p50=pct("td_vh", 50), td_vh_p99=pct("td_vh", 99),
                td_tilt_p50=pct("td_tilt", 50), td_tilt_p99=pct("td_tilt", 99),
                td_rate_p50=pct("td_rate", 50), td_rate_p99=pct("td_rate", 99),
                td_miss_p50=pct("td_miss", 50), td_miss_p95=pct("td_miss", 95), td_miss_max=pct("td_miss", 100),
                prop_used_p50=pct("prop_used", 50), prop_used_p99=pct("prop_used", 99),
                liq_left_p01=pct("liq_left", 1), exhausted=float(np.mean([r["exhausted"] for r in rows])),
                max_gim_p99=pct("max_gim", 99), max_gim_rate_p99=pct("max_gim_rate", 99),
                max_gim_acc_p99=pct("max_gim_acc", 99), max_hinge_p99=pct("max_hinge", 99),
                gim_sat_frac_p99=pct("gim_sat_frac", 99), max_axial_g_p99=pct("max_axial_g", 99),
                max_axial_g_max=pct("max_axial_g", 100), max_lat_g_eng_p99=pct("max_lat_g_eng", 99),
                peak_leg_force_p99=pct("peak_leg_force", 99), max_rate_coast_p50=pct("max_rate_coast", 50),
                max_rate_coast_p99=pct("max_rate_coast", 99), tumble_coast=float(np.mean([r["tumble_coast"] for r in rows])),
                td_roll_rate_p99=pct("td_roll_rate", 99), max_roll_rate_p99=pct("max_roll_rate", 99),
                h_max_p01=pct("h_max", 1), h_max_p50=pct("h_max", 50), h_max_p99=pct("h_max", 99),
                hslam_frac=float(np.mean([r["hslam_used"] for r in rows])),
                cut_frac=float(np.mean([r["cut"] for r in rows])),
                h_ign_p50=pct("h_ign", 50), v_ign_p50=pct("v_ign", 50),
                max_tilt_land_p99=pct("max_tilt_land", 99), att_err_td_p99=pct("att_err_td", 99),
                nav_h_err_td_p99=pct("nav_h_err_td", 99, True), max_pen_p99=pct("max_pen", 99),
                tipover=float(np.mean([r["tipover"] for r in rows])), rcs_time_p99=pct("rcs_time", 99),
                rcs_ang_imp_p99=pct("rcs_ang_imp", 99), max_q_p99=pct("max_q", 99),
                max_axial_g_flt_p99=pct("max_axial_g_flt", 99), max_axial_g_flt_max=pct("max_axial_g_flt", 100),
                max_lat_g_eng_flt_p99=pct("max_lat_g_eng_flt", 99), max_lat_g_eng_flt_max=pct("max_lat_g_eng_flt", 100),
                max_alpha_flt_p99=pct("max_alpha_flt", 99), max_alpha_flt_max=pct("max_alpha_flt", 100),
                max_axial_g_td_p99=pct("max_axial_g_td", 99), max_axial_g_td_max=pct("max_axial_g_td", 100),
                max_lat_g_eng_td_p99=pct("max_lat_g_eng_td", 99), max_lat_g_eng_td_max=pct("max_lat_g_eng_td", 100),
                max_alpha_td_p99=pct("max_alpha_td", 99), max_alpha_td_max=pct("max_alpha_td", 100),
                max_hinge_td_p99=pct("max_hinge_td", 99), max_hinge_td_max=pct("max_hinge_td", 100),
                peak_leg_force_max=pct("peak_leg_force", 100), max_hinge_max=pct("max_hinge", 100))


def sensitivity(rows, keys=None):
    from scipy.stats import spearmanr
    keys = keys or ([k.lstrip("_") for k in SCALAR_DISP] +
                    ["mis_deg", "cg_off_mm", "g_bias_dps", "a_bias_h", "align_deg", "gnss_bv", "gnss_bh", "baro_b",
                     "roll_abs"])
    L = [r for r in rows if r["landed"] > 0.5]
    out = {}
    fail = np.array([1.0 - r["ok"] for r in rows])
    for metric in ["td_vz", "td_vh", "td_tilt", "td_rate", "td_miss", "prop_used"]:
        y = np.abs(np.array([r[metric] for r in L]))
        lst = []
        for k in keys:
            x = np.array([r[k] for r in L])
            if not np.all(np.isfinite(x)) or x.std() == 0 or y.std() == 0:
                continue
            lst.append((k, float(spearmanr(x, y).statistic)))
        lst.sort(key=lambda t: -abs(t[1]))
        out[metric] = lst[:8]
    lst = []
    if fail.std() > 0:
        for k in keys:
            x = np.array([r[k] for r in rows])
            if not np.all(np.isfinite(x)) or x.std() == 0:
                continue
            lst.append((k, float(spearmanr(x, fail).statistic)))
        lst.sort(key=lambda t: -abs(t[1]))
    out["failure"] = lst[:8]
    return out
