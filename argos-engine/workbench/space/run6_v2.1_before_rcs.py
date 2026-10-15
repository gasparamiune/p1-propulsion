"""run6 v2.1: build sim6 parameter vectors from the interface JSON + tagged GNC assumptions; nominal
flights, propellant sizing on the 6-DOF, Monte Carlo with the brief C.7 dispersions.

Sources read at run time (never hard-coded): interfaces/combustion.json (throttle map, grain, gas path,
ignition timing), interfaces/electronics.json (servo datasheet values, TVC loop dynamics, latencies),
interfaces/mechanical.json (pivot station, gimballed-engine mass properties, gimbal ring, linkage ratio,
backlash/resolution at the engine, hose stiffness, friction, conical stop, engine-bay ID).
Vehicle RV-1c (default) = RV-1b + mechanical.json engine module + 140 mm bay ID (lead decision, provisional);
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


def _json(name):
    """Interface file from the shared folder; local snapshot if the mount is unavailable."""
    p = os.path.join(IFACE, name)
    try:
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f), "shared"
    except OSError:
        pass
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
        _C["tab"] = engine_v2.combustion_tables(_C["comb"])
    return _C


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
    lidar_range=40.0, lidar=True, lat_mode=0, vert_mode=0, dff=True, dff_tau=0.3, ht=8.0, vt=1.0, gim_lpf_w=50.0, gim_lpf_z=0.5, gim_cmd_rate=100.0, roll_comp_tau=0.0, kt_lat=1.5, rock=True, rock_zeta=0.05, hslam=None, ballast=0.0, ballast_z=0.60,
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
            legs_k_f=1.0, legs_c_f=1.0, slosh_zeta=0.01, drogue_f=1.0, hose_K=None, rock_K=None, rock_zeta=None)
DISP_KEYS = set(DISP)


def build(cfg, disp=None):
    """Return par, apar, comp, mp, tables, info for a configuration (+ optional per-run dispersions)."""
    src = sources()
    comb, el, tab, mech = src["comb"], src["el"], src["tab"], src["mech"]
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
        led = veh.mass_ledger_v3(geo, mech=mech, el=el, descent_option=descent, tank_V=V, fins=cfg["fins"])
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
    ign = comb["igniter_electrical"]["timing_per_start_s"]
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
    S("quant", 0.01, "ASSUMED command resolution [fraction F_max] (ENG-03 <= 2 %)")
    S("t_ign", cfg["t_ign"] if cfg["t_ign"] is not None else ign["main_Pc_90pct_expected"],
      "combustion.json v1 main_Pc_90pct_expected (DERIVED target); MC U(0.2, 0.6) s per brief")
    S("t_ign_est", cfg["t_ign_est"], "DESIGN relight planned on the latest ignition (0.6 s)")
    S("t_rise", 0.05, "ASSUMED thrust build-up allowance after ignition in the relight planner")
    S("t_off", 0.035, "DERIVED ENG-05 (< 10 % in <= 100 ms)")
    S("thrust_scale", d["thrust_scale"], "MC N(1, 0.05) per brief")
    S("isp_scale", d["isp_scale"], "MC N(1, 0.05) per brief")
    S("tank_V", V, "DERIVED sizing.tank_volume_for (85 % liquid fill at 25 C)")
    S("m_n2o", m_n2o, "SIM sized load x margin (run6.size_load)")
    S("T0", T0, "REQ ENG-12 20 +/- 3 C; MC U(15, 25) C per brief")
    S("c_wall", 0.5 * m_tank * 896.0, "ASSUMED 50 % of tank-wall heat capacity (Al 896 J/kg/K)")
    S("resid", 0.03, "ASSUMED unusable liquid fraction")
    S("rho_l_nom", rho_l, "CoolProp saturated liquid N2O at T0")
    S("m_fuel0", m_fuel0, "combustion.json v1 grain mass")
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
    S("gim_wn", dyn["omega_n_rad_s"] * d["gim_wn_f"], "electronics.json v1 dynamics_for_GNC omega_n (ASSUMED there); MC over its range")
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
        S("gim_fric", ta["hinge_moment_terms_Nm"]["bearing_seal_friction"]["v"],
          f"mechanical.json {mech['version']} bearing seal friction (ASSUMED there) [N m]")
        S("gim_stop", mech["gimbal"]["mechanical_stop_deg"]["v"], f"mechanical.json {mech['version']} conical stop [deg]")
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
    S("att_wn", cfg["att_wn"], "DESIGN attitude bandwidth landing [rad/s]")
    S("att_zeta", cfg["att_zeta"], "DESIGN attitude damping")
    S("att_ki", 0.1 * cfg["att_wn"] ** 3, "DESIGN attitude integral gain 0.1 wn^3")
    S("att_wn_asc", cfg["att_wn_asc"], "DESIGN attitude bandwidth ascent [rad/s]")
    S("tilt_max_land", cfg["tilt_max_land"], "DESIGN tilt limit during the landing burn [deg]")
    S("tilt_max_asc", cfg["tilt_max_asc"], "DESIGN tilt limit during ascent [deg]")
    S("tilt_term", cfg["tilt_term"], "DESIGN tilt limit below 1 m (touchdown criterion 5 deg) [deg]")
    S("tilt_term_hi", cfg["tilt_term_hi"], "DESIGN tilt limit at the 4 m gate, tapering to tilt_term at 1 m [deg]")
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
    S("roll_torque", cfg["roll_torque"], "ASSUMED engine roll torque at F_max (helical-port swirl estimate 0.01-0.1 N m)")
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
    S("kt_lat", cfg["kt_lat"], "DESIGN terminal-phase lateral velocity gain [1/s]")
    S("roll_comp_tau", cfg["roll_comp_tau"], "DESIGN roll-rate compensation of the gimbal command, effective lag [s] (0 = off)")
    if rv1c and cfg["rock"]:
        kax = mech["tvc_actuation"]["axis_stiffness_Nm_per_rad"]["v"]
        S("rock_K", kax[0] if d["rock_K"] is None else d["rock_K"],
          f"mechanical.json {mech['version']} axis stiffness (low end {kax[0]} nominal; MC U({kax[0]}, {kax[1]})) [N m/rad]")
        S("rock_zeta", cfg["rock_zeta"] if d["rock_zeta"] is None else d["rock_zeta"],
          "ASSUMED engine-mount rocking damping (not published; MC U(0.02, 0.10))")
    else:
        S("rock_K", 0.0, "rigid engine mount")
        S("rock_zeta", 0.0, "rigid engine mount")
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


def _kax_range():
    m = sources()["mech"]
    return tuple(m["tvc_actuation"]["axis_stiffness_Nm_per_rad"]["v"])


def draw(rng, n, cfg):
    imu = IMU[cfg["imu"]]
    gn = GNSS[cfg["gnss"]]
    D = []
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
            rock_K=(rng.uniform(*_kax_range()) if cfg["vehicle"] == "RV-1c" else None),
            rock_zeta=(rng.uniform(0.02, 0.10) if cfg["vehicle"] == "RV-1c" else None),
            # configuration-level dispersions
            _t_ign=rng.uniform(0.2, 0.6), _T0=rng.uniform(288.15, 298.15), _wind=rng.uniform(0.0, 8.0),
            _wind_dir=rng.uniform(0.0, 2 * np.pi), _gust_scale=rng.uniform(0.5, 1.5), _rho0=rng.uniform(1.10, 1.25),
            _roll=rng.uniform(-0.1, 0.1), _legs_mu=rng.uniform(0.3, 0.7),
            _k_base_lead=rng.uniform(0.5, 1.0), _k_nose_trail=rng.uniform(0.0, 0.5), _crossflow=rng.uniform(0.75, 1.25),
            _ca_tf=rng.uniform(0.7, 1.3), _k_retro=rng.uniform(0.25, 0.75), _seed=int(rng.integers(1, 2**31 - 1)),
        ))
    return D


def run_one(cfg, dr):
    c = dict(cfg)
    c.update(t_ign=dr["_t_ign"], T0=dr["_T0"], wind=dr["_wind"], wind_dir=dr["_wind_dir"], gust=True,
             gust_scale=dr["_gust_scale"], rho0=dr["_rho0"], roll_torque=dr["_roll"], legs_mu=dr["_legs_mu"],
             seed=dr["_seed"], aero_unc=dict(k_base_lead=dr["_k_base_lead"], k_nose_trail=dr["_k_nose_trail"],
                                             crossflow=dr["_crossflow"], ca_tf=dr["_ca_tf"], k_retro=dr["_k_retro"]))
    if cfg.get("ascent_bias_auto"):
        c["ascent_bias"] = cfg["ascent_bias_auto"](c, dr)
    disp = {k: v for k, v in dr.items() if not k.startswith("_")}
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


def flat_row(i, dr, res, ok):
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
                rcs_ang_imp_p99=pct("rcs_ang_imp", 99), max_q_p99=pct("max_q", 99))


def sensitivity(rows, keys=None):
    from scipy.stats import spearmanr
    keys = keys or ([k.lstrip("_") for k in SCALAR_DISP] +
                    ["mis_deg", "cg_off_mm", "g_bias_dps", "a_bias_h", "align_deg", "gnss_bv", "gnss_bh", "baro_b"])
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
