"""First-pass electronics sizing (M1), v1 2026-10-11, Senior Electronics (06-electronics).

Reads interfaces/*.json when they exist (gnc, combustion, mechanical); otherwise uses the ASSUMED
defaults below, each tagged. Writes results/first_pass_v1.json and a text log.

Sections
  A. Pc plant: chamber filling time, fuel thermal lag, quasi-steady throttle map, deep-throttle
     stroke resolution (pintle injector per REQUIREMENTS ENG-02 rev 1)
  B. Pintle actuator: crank kinematics, torque, full-stroke time, resolution
  C. TVC actuator: hinge-moment estimate, engine-side torque-speed vs lever ratio, margins,
     stiffness and first-mode estimate, resolution, small-signal rate bound
  D. Power: load table, energy budget (30 min pad hold + flight; static-fire day), peak current,
     brownout, wire drop
Usage: /opt/engine-venv/bin/python first_pass_v1.py [--iface /mnt/project-files/engine/interfaces]
"""
import json, math, os, sys, argparse
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parts_db as P

g0 = 9.80665
ap = argparse.ArgumentParser()
ap.add_argument("--iface", default="/mnt/project-files/engine/interfaces")
ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results"))
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)

def load(name):
    p = os.path.join(args.iface, name)
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return None

base = load("ENGINE-BASELINE-v0.json")
gnc, comb, mech = load("gnc.json"), load("combustion.json"), load("mechanical.json")
inputs_used = {"ENGINE-BASELINE": base.get("version") if base else None,
               "gnc.json": gnc.get("version") if gnc else "ABSENT (ASSUMED values used)",
               "combustion.json": comb.get("version") if comb else "ABSENT (ASSUMED values used)",
               "mechanical.json": mech.get("version") if mech else "ABSENT (ASSUMED values used)"}
out = {"id": "electronics-first-pass", "version": "v1", "date": "2026-10-11", "inputs": inputs_used,
       "script": "06-electronics/calc/first_pass_v1.py"}
log = []
def L(s=""):
    print(s); log.append(s)

# =============================================================================================
# A. Pc plant (baseline v0 gas path; pintle injector)
# =============================================================================================
gp = base["gas_path_v0"]; th = base["thermochemistry_CEA"]
At = gp["At_m2"]; Pc_max = gp["Pc_max_Pa"]; F_max = base["requirements"]["F_max_SL_N"]["v"]
gam = th["gamma_chamber"]; eps = th["eps"]; eta_cs = gp["eta_cstar"]["v"]; eta_cf = gp["eta_cf"]["v"]
Ae = At * eps
Gam = math.sqrt(gam) * (2 / (gam + 1)) ** ((gam + 1) / (2 * (gam - 1)))
cf_sl_ideal = th["Cf_SL_ideal"]; pa = 101325.0
cf_vac = (cf_sl_ideal + pa / Pc_max * eps) * eta_cf          # DERIVED: Cf_vac = Cf_SL + (pa/Pc)*eps
# ideal c*(O/F) at 25 bar from calc/cea_quick_v0_output.txt (CEA); O/F<3 is a LINEAR EXTRAPOLATION (ASSUMED)
OF_tab = np.array([2.0, 3.0, 4.0, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 9.0])
cs_tab = np.array([1445.2 - 104.8, 1445.2, 1550.0, 1595.5, 1600.8, 1598.2, 1591.5, 1582.9, 1573.5, 1563.9, 1545.0])
def cstar(of):
    return eta_cs * float(np.interp(of, OF_tab, cs_tab))
# regression placeholder (baseline v0, ASSUMED): r = a*G^n, single port
a_reg, n_reg, rho_f = 0.0577e-3, 0.5, 1050.0
Dp, Lg = base["grain_v0_placeholder"]["Dport0_m"], base["grain_v0_placeholder"]["L_grain_m"]
Aport = math.pi * Dp ** 2 / 4
def mdot_fuel(mox):
    G = mox / Aport
    return rho_f * math.pi * Dp * Lg * a_reg * G ** n_reg
# N2O feed (CoolProp, saturated liquid at 20 C): p_sat 50.53 bar, rho_l 785.1 kg/m3
p_tank = 50.53e5; rho_l = 785.1
dp_line_100 = 2.5e5          # ASSUMED main valve + line + flex hose loss at 100 % flow (range 1-4 bar)
Cd = 0.65                    # ASSUMED pintle discharge coefficient (SPI form; Dyer two-phase -> Combustion)
x_max = 4.0e-3               # ASSUMED pintle full stroke [m] (lead: 'a few mm'; range 2-6 mm)
mox100 = gp["mdot_ox_kgps"]
def pfeed(mox):
    return p_tank - dp_line_100 * (mox / mox100) ** 2
dp_inj_100 = pfeed(mox100) - Pc_max
A100 = mox100 / (Cd * math.sqrt(2 * rho_l * dp_inj_100))
A_max = 1.10 * A100          # DERIVED: full stroke sized for 110 % ox flow (control authority above 100 %)
def area(x):                  # ASSUMED linear area-stroke characteristic until combustion.json
    return A_max * min(max(x, 0.0), x_max) / x_max
def thrust(Pc):
    return Pc * At * cf_vac - pa * Ae   # quasi-1D; ignores separation at the floor (Combustion owns)
def pc_from_thrust(F):
    return (F + pa * Ae) / (At * cf_vac)
def steady_state(x):
    """quasi-steady Pc for stroke x: fixed point on Pc"""
    Pc = 10e5
    for _ in range(200):
        A = area(x)
        mox = Cd * A * math.sqrt(2 * rho_l * max(pfeed_guess(Pc, A) - Pc, 0.0))
        mf = mdot_fuel(mox) if mox > 0 else 0.0
        of = mox / mf if mf > 0 else 9.0
        Pc_new = (mox + mf) * cstar(of) / At
        if abs(Pc_new - Pc) < 1.0:
            break
        Pc = 0.5 * Pc + 0.5 * Pc_new
    return Pc, mox, mf
def pfeed_guess(Pc, A):
    # feed pressure depends on flow; iterate once with the SPI flow at p_tank
    mox0 = Cd * A * math.sqrt(2 * rho_l * max(p_tank - Pc, 0.0))
    return pfeed(mox0)
def x_for_thrust(F):
    lo, hi = 0.0, x_max
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if thrust(steady_state(mid)[0]) < F:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)

L("== A. Pc plant (pintle injector, baseline v0 gas path; ASSUMED where combustion.json absent)")
L(f"Gamma(gamma={gam}) = {Gam:.4f};  Cf_vac(delivered) = {cf_vac:.4f};  Ae = {Ae*1e6:.1f} mm2")
V_pre_post = 1.4e-4           # ASSUMED pre+post chamber free volume [m3] (range 0.8-2.5e-4)
V_c0 = Aport * Lg + V_pre_post
V_c1 = math.pi * 0.045 ** 2 / 4 * Lg + V_pre_post   # ASSUMED end-of-burn port 45 mm
tau_fill = [V / (Gam ** 2 * cstar(6.0) * At) for V in (V_c0, V_c1)]
L(f"Chamber free volume {V_c0*1e6:.0f} -> {V_c1*1e6:.0f} cm3; filling time tau = V/(Gamma^2 c* At) = "
  f"{tau_fill[0]*1e3:.2f} -> {tau_fill[1]*1e3:.2f} ms (independent of Pc to first order)")
alpha_abs = 0.18 / (1050 * 1400)  # ASSUMED ABS thermal diffusivity k/(rho c) ~1.2e-7 m2/s
rows = []
for frac in [1.10, 1.00, 0.75, 0.50, 0.25, 0.20, 0.15, 0.125]:
    F = frac * F_max
    x = x_for_thrust(F)
    Pc, mox, mf = steady_state(x)
    dx = 1e-6
    dF = (thrust(steady_state(x + dx)[0]) - thrust(steady_state(x - dx)[0])) / (2 * dx)
    dPc = (steady_state(x + dx)[0] - steady_state(x - dx)[0]) / (2 * dx)
    rdot = a_reg * (mox / Aport) ** n_reg
    tau_tl = alpha_abs / rdot ** 2
    rows.append({"thrust_frac": frac, "F_N": F, "x_mm": x * 1e3, "Pc_bar": Pc / 1e5, "mdot_ox": mox, "mdot_f": mf,
                 "OF": mox / mf, "dF_dx_N_per_mm": dF / 1e3, "dPc_dx_bar_per_mm": dPc / 1e8,
                 "fuel_frac": mf / (mox + mf), "tau_thermal_lag_s": tau_tl,
                 "dp_inj_over_Pc": (pfeed(mox) - Pc) / Pc})
L(" frac  F[N]   x[mm]  Pc[bar] mox[kg/s] O/F  dF/dx[N/mm] dPc/dx[bar/mm] fuel%  tauTL[s] dPinj/Pc")
for r in rows:
    L(f" {r['thrust_frac']:5.3f} {r['F_N']:6.1f} {r['x_mm']:6.3f} {r['Pc_bar']:6.2f}  {r['mdot_ox']:.4f}  {r['OF']:4.2f}"
      f"  {r['dF_dx_N_per_mm']:8.1f}   {r['dPc_dx_bar_per_mm']:8.2f}    {100*r['fuel_frac']:4.1f}  {r['tau_thermal_lag_s']:.3f}   {r['dp_inj_over_Pc']:.2f}")
out["pc_plant"] = {
    "tag": "DERIVED (first_pass_v1.py) from ENGINE-BASELINE v0 + ASSUMED pintle/feed values; replace with combustion.json plant",
    "Gamma": Gam, "Cf_vac_delivered": cf_vac, "A_pintle_max_m2": A_max, "Cd_pintle": {"v": Cd, "tag": "ASSUMED", "range": [0.5, 0.8]},
    "x_max_m": {"v": x_max, "tag": "ASSUMED", "range": [2e-3, 6e-3]},
    "p_tank_Pa": {"v": p_tank, "tag": "DERIVED CoolProp N2O sat. 20 C"}, "rho_l": {"v": rho_l, "tag": "DERIVED CoolProp"},
    "dp_line_100_Pa": {"v": dp_line_100, "tag": "ASSUMED", "range": [1e5, 4e5]},
    "V_chamber_m3": [V_c0, V_c1], "tau_fill_s": tau_fill,
    "combustion_delay_s": {"v": 0.003, "tag": "ASSUMED", "range": [0.001, 0.008]},
    "alpha_ABS_m2ps": {"v": alpha_abs, "tag": "ASSUMED (k 0.18 W/mK, rho 1050, c 1400)"},
    "thermal_lag_model": "tau_TL = alpha/rdot^2 (Karabeyoglu et al., J. Propulsion & Power 21(6) 2005, 'Modeling of hybrid rocket low frequency instabilities'; citation from memory - VERIFY)",
    "table": rows}

# =============================================================================================
# B. Pintle actuator: SB-2292SG + crank (rotary-to-linear)
# =============================================================================================
L("\n== B. Pintle (throttle) actuator: Savox SB-2292SG + crank, ASSUMED force until combustion.json")
s = P.SB2292SG
def servo_pts(V):
    vs = [6.0, 7.4, 8.4]
    T = np.interp(V, vs, [s["torque_kgcm"]["v"][k] for k in ("6.0", "7.4", "8.4")]) * P.KGCM_TO_NM
    t60 = np.interp(V, vs, [s["speed_s_per_60deg"]["v"][k] for k in ("6.0", "7.4", "8.4")])
    w = math.radians(60) / t60
    return T, w   # stall torque [N m], no-load speed [rad/s]  (linear interpolation between listed points: ASSUMED)
F_pintle_nom, F_pintle_max = 60.0, 120.0   # ASSUMED [N]: p_feed*A_stem (3.5 mm stem ~46 N) + seal friction; range 20-150
theta_half = math.radians(25.0)            # crank swing +/-25 deg -> stroke = 2 r sin(25)
r_c = x_max / (2 * math.sin(theta_half))
pint = {}
for V in (7.0, 7.4, 8.4):
    T_s, w_s = servo_pts(V)
    tq = F_pintle_max * r_c                # worst-case at crank centre (cos=1)
    w_load = w_s * (1 - tq / T_s)          # linear torque-speed (ASSUMED model)
    t_acc = 0.010                          # ASSUMED servo acceleration/settling overhead
    t_full = 2 * theta_half / w_load + t_acc
    pint[str(V)] = {"T_stall_Nm": T_s, "w_noload_dps": math.degrees(w_s), "load_torque_Nm": tq,
                    "load_frac": tq / T_s, "w_loaded_dps": math.degrees(w_load), "t_full_stroke_s": t_full}
    L(f" V={V}: stall {T_s:.2f} N m, no-load {math.degrees(w_s):.0f} deg/s, crank r={r_c*1e3:.2f} mm, load {tq:.3f} N m "
      f"({100*tq/T_s:.0f} % stall) -> {math.degrees(w_load):.0f} deg/s, full stroke {t_full*1e3:.0f} ms (req <= 100 ms)")
db_us = s["deadband_us"]["v"]; deg_per_us = 100.0 / 1000.0     # operating travel 100 deg over 1000 us (DATASHEET)
db_deg = db_us * deg_per_us; q_deg = 1400.0 / 4096 * deg_per_us
floor = [r for r in rows if abs(r["thrust_frac"] - 0.125) < 1e-9][0]
x_fl = floor["x_mm"] * 1e-3
th_fl = math.asin(x_fl / r_c - math.sin(theta_half))
dx_db = r_c * math.cos(th_fl) * math.radians(db_deg)
dx_q = r_c * math.cos(th_fl) * math.radians(q_deg)
L(f" Floor (12.5 %): x = {x_fl*1e3:.3f} mm, crank angle {math.degrees(th_fl):.1f} deg; deadband {db_deg:.2f} deg -> "
  f"{dx_db*1e6:.1f} um -> {dx_db*1e3*floor['dF_dx_N_per_mm']:.2f} N ({100*dx_db*1e3*floor['dF_dx_N_per_mm']/F_max:.2f} % of Fmax); "
  f"12-bit step {q_deg:.3f} deg -> {dx_q*1e6:.2f} um")
out["pintle_actuator"] = {"servo": s["model"], "crank_radius_m": {"v": r_c, "tag": "DERIVED"},
                          "crank_swing_deg": {"v": [-25, 25], "tag": "DERIVED (proposal to Mechanical)"},
                          "force_N": {"nom": F_pintle_nom, "max": F_pintle_max, "tag": "ASSUMED until combustion.json", "range": [20, 150]},
                          "per_voltage": pint,
                          "floor_resolution": {"x_floor_m": x_fl, "deadband_deg": db_deg, "dx_deadband_m": dx_db,
                                               "dF_deadband_N": dx_db * 1e3 * floor["dF_dx_N_per_mm"],
                                               "cmd_quant_deg": q_deg, "dx_quant_m": dx_q, "tag": "DERIVED"}}

# =============================================================================================
# C. TVC actuators
# =============================================================================================
L("\n== C. TVC gimbal actuators (2x SB-2292SG), hinge moment ASSUMED until mechanical.json")
theta_max = math.radians(7.0)       # ENG-07 baseline (ASSUMED until gnc.json)
rate_req = math.radians(60.0)       # ENG-07
bw_req = 8.0                        # Hz, ENG-07
res_req = 0.1                       # deg, ENG-07
m_g = 2.5; L_e = 0.40; d_cg = 0.18  # ASSUMED gimballed mass [kg], length [m], pivot->CG [m] (forward pivot, conservative)
I_piv = m_g * (L_e ** 2 / 12 + d_cg ** 2)
alpha_req = max((2 * math.pi * bw_req) ** 2 * math.radians(1.0), rate_req / 0.025)  # 8 Hz x 1 deg, or 60 deg/s in 25 ms
a_ax, a_lat = 40.0, 5.0             # ASSUMED specific force [m/s2]: 500 N / 12.5 kg; lateral from 7 deg gimbal
k_hose = 0.2 * 180 / math.pi        # ASSUMED 0.2 N m/deg -> N m/rad (range 0.05-0.5 N m/deg)
e_mis = 1.0e-3                      # ASSUMED thrust-line offset from pivot [m]
M_fric = 0.3                        # ASSUMED pivot friction [N m]
M = {"inertial": I_piv * alpha_req, "axial_accel": m_g * a_ax * d_cg * math.sin(theta_max),
     "lateral_accel": m_g * a_lat * d_cg, "hose": k_hose * theta_max, "misalignment": F_max * e_mis, "friction": M_fric}
M_peak = sum(M.values()); M_slew = M_peak - M["inertial"]
L(f" Gimballed: m={m_g} kg, L={L_e} m, d_cg={d_cg} m -> I_pivot={I_piv:.4f} kg m2; alpha_req={alpha_req:.1f} rad/s2")
for k, v in M.items():
    L(f"   {k:14s} {v:6.2f} N m")
L(f" Peak hinge moment (linear sum, conservative) {M_peak:.2f} N m; constant-slew moment {M_slew:.2f} N m")
eta_link = 0.90                      # ASSUMED linkage efficiency
tvc = {}
for V in (7.0, 7.4, 8.4):
    T_s, w_s = servo_pts(V)
    best = None
    for n in np.arange(3.0, 12.01, 0.25):
        Te_stall = n * eta_link * T_s; we = w_s / n
        Te_60 = Te_stall * (1 - rate_req / we) if rate_req < we else 0.0
        mp, ms = Te_stall / M_peak, Te_60 / M_slew
        score = min(mp, ms)
        if best is None or score > best[0]:
            best = (score, n, Te_stall, math.degrees(we), Te_60, mp, ms)
    tvc[str(V)] = dict(zip(["min_margin", "n_opt", "Te_stall_Nm", "we_noload_dps", "Te_at_60dps_Nm", "margin_peak", "margin_slew"], best))
    L(f" V={V}: best lever ratio n={best[1]:.2f}: engine stall {best[2]:.1f} N m, no-load {best[3]:.0f} deg/s, "
      f"T@60deg/s {best[4]:.1f} N m; margins peak {best[5]:.2f}, slew {best[6]:.2f}")
n_sel = 7.0                          # proposal to Mechanical: servo horn r_h = 15 mm, engine arm R_e = 105 mm
T_s74, w_s74 = servo_pts(7.4)
servo_travel_deg = math.degrees(math.asin(min(1.0, n_sel * math.sin(theta_max))))  # horn angle for +/-7 deg (parallel linkage)
K_s = [T_s74 / math.radians(pb) for pb in (3.0, 1.0)]   # ASSUMED proportional band 1-3 deg -> output stiffness
K_e = [n_sel ** 2 * eta_link * k for k in K_s]
f1 = [math.sqrt(k / I_piv) / (2 * math.pi) for k in K_e]
res_e = db_deg / n_sel; q_e = q_deg / n_sel
we74 = math.degrees(w_s74) / n_sel
f_rate_1deg = math.radians(we74) / (2 * math.pi * math.radians(1.0))
L(f" Selected n={n_sel}: horn {servo_travel_deg:.1f} deg for +/-7 deg (operating travel +/-50 deg); resolution: deadband {res_e:.4f} deg, "
  f"12-bit {q_e:.4f} deg (req <= {res_req})")
L(f" Servo output stiffness (ASSUMED PB 1-3 deg) {K_s[0]:.0f}-{K_s[1]:.0f} N m/rad -> engine {K_e[0]:.0f}-{K_e[1]:.0f} N m/rad -> "
  f"rigid-engine-on-actuator mode {f1[0]:.0f}-{f1[1]:.0f} Hz (ENG-11 needs >= {3*bw_req:.0f} Hz)")
L(f" Rate bound: engine no-load slew {we74:.0f} deg/s @7.4 V -> 1 deg sine can be followed to {f_rate_1deg:.1f} Hz without rate saturation")
out["tvc_actuator"] = {"servo": s["model"], "lever_ratio_proposal": {"v": n_sel, "tag": "DERIVED proposal (r_h 15 mm, R_e 105 mm)", "range": [6, 8]},
                       "hinge_moment_assumptions": {"m_g_kg": m_g, "L_e_m": L_e, "d_cg_m": d_cg, "I_pivot_kgm2": I_piv,
                                                    "alpha_req_radps2": alpha_req, "a_axial": a_ax, "a_lat": a_lat,
                                                    "k_hose_Nm_per_deg": 0.2, "e_misalign_m": e_mis, "M_friction_Nm": M_fric,
                                                    "tag": "ASSUMED until mechanical.json/gnc.json"},
                       "hinge_moments_Nm": M, "M_peak_Nm": M_peak, "M_slew_Nm": M_slew, "per_voltage_best": tvc,
                       "servo_horn_travel_deg_for_7deg": servo_travel_deg,
                       "resolution_deg": {"deadband": res_e, "cmd_quant": q_e, "tag": "DERIVED from ASSUMED deadband 1 us"},
                       "stiffness": {"servo_output_Nm_per_rad": K_s, "engine_Nm_per_rad": K_e, "f1_rigid_engine_Hz": f1,
                                     "tag": "ASSUMED proportional band 1-3 deg (not published); bench-measure"},
                       "rate_bound_freq_1deg_Hz": f_rate_1deg, "engine_noload_slew_dps_7V4": we74}

# =============================================================================================
# D. Power
# =============================================================================================
L("\n== D. Power budget (2S LiPo, servos direct on battery; logic via buck)")
loads = [  # name, rail, V, I_typ [A], I_peak [A], tag/source
    ("Teensy 4.1 @600 MHz", "5V", 5.0, 0.100, 0.150, "DATASHEET PJRC (typ ~100 mA); peak ASSUMED"),
    ("ADS131M04 x2 + 8.192 MHz osc", "3V3", 3.3, 0.012, 0.015, "ASSUMED pending TI SBAS890 check"),
    ("MAX31856 x4", "3V3", 3.3, 0.008, 0.010, "ASSUMED pending ADI datasheet check"),
    ("AS5048A x3", "5V", 5.0, 0.045, 0.060, "ASSUMED ~15 mA each pending ams datasheet"),
    ("M3200 transducers x3", "5V_SNS", 5.0, 0.015, 0.015, "DATASHEET TE M3200 5 mA each"),
    ("CAN transceivers x2", "5V", 5.0, 0.020, 0.140, "ASSUMED (recessive/dominant)"),
    ("Watchdog, supervisors, LEDs, buzzer", "5V", 5.0, 0.020, 0.060, "ASSUMED"),
]
eta_buck = 0.85
P_logic = sum(V * I for _, _, V, I, _, _ in loads) / eta_buck
P_logic_pk = sum(V * Ip for _, _, V, _, Ip, _ in loads) / eta_buck
for l in loads:
    L(f"   {l[0]:36s} {l[1]:6s} {l[2]:.1f} V  typ {l[3]*1e3:6.1f} mA  peak {l[4]*1e3:6.1f} mA  [{l[5]}]")
L(f" Logic from battery (buck eta {eta_buck}): typ {P_logic:.2f} W, peak {P_logic_pk:.2f} W")
Vb = 7.4
I_stall = s["stall_current_A"]["v"]["7.4"] * 8.4 / 7.4   # ASSUMED scale to 8.4 V (not published)
phases = {
    "pad_hold_30min": {"t": 1800, "P": P_logic + 2 * Vb * 0.05 + Vb * 0.05, "note": "TVC+pintle powered, holding (ASSUMED 50 mA each)"},
    "flight": {"t": 60, "P": P_logic + 2 * Vb * 1.5 + Vb * 0.5 + 3.0 * 25 / 60, "note": "ASSUMED avg 1.5 A per TVC servo, 0.5 A pintle; latch 3 W x 25 s burn"},
    "igniter_3_starts": {"t": 6, "P": 36.0 / 0.85, "note": "IGN rail cap 36 W for 2 s x 3 (boost eta 0.85)"},
    "mv_opener_3x": {"t": 1.0, "P": Vb * 4.0, "note": "ASSUMED 4 A x 0.33 s per opening"},
}
E_flight_Wh = sum(p["t"] * p["P"] for p in phases.values()) / 3600
static_day = {"t_on_s": 3600, "burns": 3, "burn_s": 20}
E_static_Wh = (P_logic + 3 * Vb * 0.05) * 3600 / 3600 + 3 * (20 * (2 * Vb * 1.0 + Vb * 0.5 + 3.0) + 2 * 36 / 0.85) / 3600
batt = {"chem": "LiPo 2S1P", "C_Ah": 2.2, "V_nom": 7.4, "E_Wh": 2.2 * 7.4, "usable_frac": 0.8,
        "R_int_ohm": {"v": 0.010, "tag": "ASSUMED new 2S 2.2 Ah 25C+ pack, range 0.006-0.020"}}
for k, p in phases.items():
    L(f"   {k:18s} {p['t']:6.0f} s x {p['P']:6.2f} W = {p['t']*p['P']/3600:6.3f} Wh   ({p['note']})")
L(f" Flight-day energy (30 min hold + flight): {E_flight_Wh:.2f} Wh vs usable {batt['E_Wh']*batt['usable_frac']:.1f} Wh "
  f"-> margin x{batt['E_Wh']*batt['usable_frac']/E_flight_Wh:.1f}")
L(f" Static-fire session (60 min powered, 3 x 20 s burns): {E_static_Wh:.2f} Wh (stand also has GSE/umbilical power)")
I_peak = 3 * I_stall + P_logic_pk / 6.5 + 4.0
R_path = batt["R_int_ohm"]["v"] + 0.008 + 0.004 + 0.003   # pack + 16 AWG 0.6 m loop + XT60 + fuse (ASSUMED)
V_min = 3.5 * 2 - I_peak * R_path
L(f" Peak current: 3 servos stalled ({I_stall:.1f} A each, ASSUMED 8.4 V scaling) + logic + latch = {I_peak:.1f} A; "
  f"path R {R_path*1e3:.0f} mOhm -> sag {I_peak*R_path:.2f} V; at 3.5 V/cell OCV: {V_min:.2f} V at the ECU (buck needs >= 5.5 V)")
def awg_ohm_per_m(awg):
    d = 0.127e-3 * 92 ** ((36 - awg) / 39)
    return 1.724e-8 / (math.pi * d ** 2 / 4)
wires = []
for name, awg, length, I in [("Battery->ECU (loop 2x0.3 m)", 16, 0.6, I_peak), ("TVC servo lead (loop 2x0.6 m)", 20, 1.2, I_stall),
                             ("Pintle servo lead across gimbal (loop 2x1.0 m)", 20, 2.0, I_stall),
                             ("Igniter 12 V feed (loop 2x1.0 m)", 18, 2.0, 3.0), ("MV latch (loop 2x0.5 m)", 22, 1.0, 0.5)]:
    R = awg_ohm_per_m(awg) * length
    wires.append({"run": name, "AWG": awg, "loop_m": length, "I_A": I, "R_ohm": R, "drop_V": I * R})
    L(f"   {name:48s} AWG{awg}: R={R*1e3:5.1f} mOhm, I={I:5.1f} A -> drop {I*R:5.2f} V")
out["power"] = {"battery": batt, "loads": [dict(zip(["name", "rail", "V", "I_typ", "I_peak", "tag"], l)) for l in loads],
                "P_logic_W": {"typ": P_logic, "peak": P_logic_pk}, "phases": phases,
                "E_flight_day_Wh": E_flight_Wh, "E_static_session_Wh": E_static_Wh,
                "I_peak_A": I_peak, "R_path_ohm": R_path, "V_min_at_ECU_V": V_min, "wires": wires,
                "servo_stall_A_8V4": {"v": I_stall, "tag": "ASSUMED linear scaling of 9.2 A @7.4 V (DATASHEET listing)"}}

with open(os.path.join(args.out, "first_pass_v1.json"), "w") as f:
    json.dump(out, f, indent=1, default=float)
with open(os.path.join(args.out, "first_pass_v1.txt"), "w") as f:
    f.write("\n".join(log) + "\n")
print("\nwrote", os.path.join(args.out, "first_pass_v1.json"))
