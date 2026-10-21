"""First-pass (analytic) TVC sizing: authority, trim, aero moments, tail-wags-dog, hinge moments.

Rigid-vehicle pitch plane, gimbal pivot on the axis at station z_p, vehicle CG at z_cg:
  control moment       M_c = T l_p sin(delta),   l_p = z_cg - z_p
  tail-wags-dog        I_v th'' = -T l_p delta - J_twd delta'',  J_twd = I_e + m_e l_e (l_e + l_p)
                       -> imaginary zeros at w_twd = sqrt(T l_p / J_twd)  (Greensite 1970, ch. 6)
  hinge moment (actuator, about the pivot)
       H = (I_e + m_e l_e^2) delta'' + m_e a_x l_e sin(delta) + K_hose delta + H_fric + T e_mis + H_side
Aero moments from gncsim.aero (component build-up), evaluated with nominal and adverse
uncertainty factors.
"""
import numpy as np
from . import aero, vehicle as veh

ADVERSE = dict(k_base_lead=1.0, k_nose_trail=0.5, crossflow=1.25, legs=1.5, k_retro=1.0)
NOMINAL = {}


def mass_case(pivot, m_liq, m_fuel, m_vap=0.15, rho_l=785.0):
    geo = veh.reference_geometry(pivot=pivot)
    led = veh.mass_ledger(geo)
    mp = veh.build_mp(geo, led)
    o = np.zeros(8)
    veh.massprops(mp, m_liq, m_vap, rho_l, m_fuel, o)
    return dict(m=o[0], z_cg=o[1], I_t=o[2], I_r=o[3], m_e=o[4], z_e=o[5], I_e=o[6], z_p=geo["z_pivot"],
                l_p=o[1] - geo["z_pivot"], l_e=geo["z_pivot"] - o[5], geo=geo)


def aero_moment(geo, z_cg, V_axial, V_cross, engine_on=True, legs=True, unc=None, rho=1.225):
    ap, cp = aero.build_aero_params(geo, unc)
    ap[aero.A_LEGS_DEPLOYED] = 1.0 if legs else 0.0
    F = np.zeros(3); M = np.zeros(3)
    aero.aero_forces(np.array([V_cross, 0.0, V_axial]), np.zeros(3), rho, z_cg, engine_on, ap, cp, F, M)
    return abs(M[1]), abs(F[0])


def twd(mc, T):
    J = mc["I_e"] + mc["m_e"] * mc["l_e"] * (mc["l_e"] + mc["l_p"])
    return J, np.sqrt(T * mc["l_p"] / J) if J > 0 else np.inf


def hinge_budget(mc, delta_max_deg=7.0, ddelta_max=52.0, a_x_max=40.0, K_hose=(0.5, 2.0), mu=0.1,
                 r_pin=0.005, F_max=500.0, mis_deg=0.25, side_N=5.0):
    """Return dict of hinge-moment terms [N m] (nominal, worst)."""
    d = np.radians(delta_max_deg)
    I_piv = mc["I_e"] + mc["m_e"] * mc["l_e"] ** 2
    zthroat = mc["z_e"] - 0.13          # throat ~0.13 m aft of the gimballed CG (ASSUMED layout)
    arm_thr = abs(mc["z_p"] - zthroat)
    arm_exit = abs(mc["z_p"] - (-0.03))
    terms = {
        "inertia_I_pivot_x_delta_ddot": I_piv * ddelta_max,
        "axial_accel_m_e_a_l_e_sin_delta": mc["m_e"] * a_x_max * abs(mc["l_e"]) * np.sin(d),
        "flex_hose_K_delta": K_hose[1] * d,
        "pivot_friction": mu * F_max * r_pin * 2,
        "thrust_misalignment_T_e": F_max * arm_thr * np.radians(mis_deg),
        "nozzle_side_load_at_floor": side_N * arm_exit,
    }
    terms["total_worst_linear_sum"] = sum(terms.values())
    terms["I_pivot_kgm2"] = I_piv
    return terms


def sizing_table(F_floor=100.0, F_max=500.0, winds=(4.0, 8.0, 11.0), cg_off=0.005, mis_deg=0.25):
    """Gimbal angle demand by case, for both pivot options."""
    rows = []
    for pivot in ["mid", "forward"]:
        lo = mass_case(pivot, 1.3, 0.50)        # near lift-off
        ld = mass_case(pivot, 0.05, 0.30)       # landing
        for lab, mc in (("liftoff", lo), ("landing", ld)):
            trim = mis_deg + np.degrees(np.arctan(cg_off / mc["l_p"]))
            J, w_floor = twd(mc, F_floor)
            J, w_full = twd(mc, F_max)
            rows.append(dict(pivot=pivot, state=lab, m=mc["m"], z_cg=mc["z_cg"], l_p=mc["l_p"], l_e=mc["l_e"],
                             I_t=mc["I_t"], m_e=mc["m_e"], I_e=mc["I_e"], J_twd=J, w_twd_floor=w_floor,
                             w_twd_full=w_full, trim_deg=trim,
                             Mc_per_deg_floor=F_floor * mc["l_p"] * np.radians(1),
                             Mc_per_deg_W=mc["m"] * 9.80665 * mc["l_p"] * np.radians(1),
                             Mc_per_deg_full=F_max * mc["l_p"] * np.radians(1)))
    return rows


def terminal_wind_cases(pivot, winds=(4.0, 6.0, 8.0, 11.0), V_desc=1.0, legs=True):
    """Terminal descent / hover in wind: aero moment, side force, gimbal angle at T = W."""
    mc = mass_case(pivot, 0.05, 0.30)
    out = []
    for w in winds:
        for lab, unc in (("nominal", NOMINAL), ("adverse", ADVERSE)):
            M, Fx = aero_moment(mc["geo"], mc["z_cg"], -V_desc, w, engine_on=True, legs=legs, unc=unc)
            W = mc["m"] * 9.80665
            tilt = np.degrees(np.arctan(Fx / W))
            T = np.hypot(W, Fx)
            dl = np.degrees(np.arcsin(min(1.0, M / (T * mc["l_p"]))))
            out.append(dict(pivot=pivot, legs=legs, wind=w, aero=lab, M_aero=M, F_side=Fx, tilt_deg=tilt, T=T,
                            delta_aero_deg=dl))
    return out
