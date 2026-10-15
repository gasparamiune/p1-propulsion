"""Python driver for sim1d: builds parameter vectors from params/vehicle and runs flights."""
import numpy as np
from . import sim1d as s
from . import params as prm
from . import vehicle as veh

_TAB = None


def tables():
    global _TAB
    if _TAB is None:
        p = prm.default_params()
        _TAB = prm.engine_tables(p)
    return _TAB


def make_par(profile=0, h_target=300.0, floor=0.20, m_n2o=1.6, tank_V=2.5e-3, ballast=0.0,
             descent="freefall", drogue_CdA=0.0, kd=0.70, ht=4.0, vt=1.0, kv=2.0, hslam=None,
             hcut=0.15, tau=0.100 / 2.197, slew=5.0, deadb=0.005, quant=0.01, t_ign=0.40,
             t_ign_est=0.40, thrust_scale=1.0, isp_scale=1.0, T0=293.15, rho0=1.225, dt=1e-3,
             legs_at_ign=1.0, k_retro=0.5, tmax=120.0, ascent_thr=1.0, CA_nf=None, CA_tf=None,
             CA_legs=None, m_dry=None, pivot="forward", meco_bias=0.0, hover_k=0.9,
             h_bias=0.0, v_bias=0.0, m_est_err=0.0, dry_scale=1.0, a_bias=0.0, k_est=1.0,
             k_est_tau=0.1, hs_margin=3.0):
    """Parameter vector for sim1d.run. Guidance defaults (v1.2): accelerometer thrust-effectiveness
    estimator on (k_est=1, tau 0.1 s); hoverslam terminal deceleration margin 3.0 m/s2 above the
    floor deceleration; hover rule hover_k = 0.9 (hoverslam if T_floor > 0.9 W_est)."""
    p = prm.default_params()
    geo = veh.reference_geometry(pivot=pivot)
    led = veh.mass_ledger(geo, descent_option=("drogue" if descent == "drogue" else "none"), tank_V=tank_V)
    mdry = (sum(i["m"] for i in led) if m_dry is None else m_dry) * dry_scale
    gr_Do, gr_Dp, gr_L = p["D_grain_o"]["v"], p["D_port0"]["v"], p["L_grain"]["v"]
    m_fuel0 = p["rho_f"]["v"] * np.pi / 4 * (gr_Do ** 2 - gr_Dp ** 2) * gr_L
    par = np.zeros(s.N_PAR)
    par[s.I_PROFILE] = profile
    par[s.I_H_TARGET] = h_target
    par[s.I_FMAX] = p["F_max"]["v"]
    par[s.I_FLOOR] = floor
    par[s.I_TAU] = tau
    par[s.I_SLEW] = slew
    par[s.I_DEADB] = deadb
    par[s.I_QUANT] = quant
    par[s.I_TIGN] = t_ign
    par[s.I_TRISE] = p["tau_rise"]["v"]
    par[s.I_TOFF] = p["tau_off"]["v"]
    par[s.I_THRUST_SCALE] = thrust_scale
    par[s.I_ISP_SCALE] = isp_scale
    par[s.I_TANK_V] = tank_V
    par[s.I_M_N2O] = m_n2o
    par[s.I_T0] = T0
    m_tank = [i for i in led if i["name"].startswith("P11")][0]["m"]
    par[s.I_CWALL] = p["wall_part"]["v"] * m_tank * 896.0
    par[s.I_RESID] = p["residual_liq"]["v"]
    par[s.I_M_DRY] = mdry
    par[s.I_M_FUEL0] = m_fuel0
    par[s.I_RHOF] = p["rho_f"]["v"]
    par[s.I_GL] = gr_L
    par[s.I_GDO] = gr_Do
    par[s.I_S_REF] = np.pi * geo["d"] ** 2 / 4
    par[s.I_CA_NF] = geo["CA0_nf"] if CA_nf is None else CA_nf
    par[s.I_CA_TF] = geo["CA0_tf"] if CA_tf is None else CA_tf
    par[s.I_CA_LEGS] = geo["CA_legs"] if CA_legs is None else CA_legs
    par[s.I_DROGUE_CDA] = drogue_CdA
    par[s.I_KD] = kd
    par[s.I_HT] = ht
    par[s.I_VT] = vt
    par[s.I_KV] = kv
    par[s.I_HSLAM] = -1.0 if hslam is None else (1.0 if hslam else 0.0)
    par[s.I_HCUT] = hcut
    par[s.I_RHO0] = rho0
    par[s.I_DT] = dt
    par[s.I_TIGN_EST] = t_ign_est
    par[s.I_LEGS_AT_IGN] = legs_at_ign
    par[s.I_KRETRO] = k_retro
    par[s.I_TMAX] = tmax
    par[s.I_ASCENT_THR] = ascent_thr
    par[s.I_BALLAST] = ballast
    par[s.I_MECO_BIAS] = meco_bias
    par[s.I_HOVER_K] = hover_k
    par[s.I_HBIAS] = h_bias
    par[s.I_VBIAS] = v_bias
    par[s.I_MEST] = m_est_err
    par[s.I_ABIAS] = a_bias
    par[s.I_KEST] = k_est
    par[s.I_KEST_TAU] = k_est_tau
    par[s.I_HS_MARGIN] = hs_margin
    return par


REC_COLS = ["t_s", "h_m", "v_mps", "a_axial_specific_mps2", "F_N", "F_cmd_N", "mdot_kgps", "mdot_ox_kgps",
            "mdot_fuel_kgps", "P_tank_Pa", "T_tank_K", "m_kg", "m_n2o_liquid_kg", "m_fuel_kg", "phase",
            "F_ceiling_N", "throttle_frac"]
RES_KEYS = ["landed", "td_v", "h_max", "prop_used", "m_n2o_left", "m_liq_left", "m_fuel_left", "t_end",
            "burn_time", "starts", "max_acc", "min_acc", "m_land", "nrec", "F_land_max", "v_ign", "h_ign",
            "exhausted", "P_tank_end", "T_tank_end", "hslam_used", "cut_before_contact"]


def fly(par, rec_dt=0.01, nrec=20000):
    t = tables()
    rec = np.zeros((nrec, len(REC_COLS)))
    r = s.run(par, t["Fg"], t["Dg"], t["mox"], t["mf"], t["Pg"], t["ceil"], rec_dt, rec)
    res = dict(zip(RES_KEYS, r))
    return res, rec[: int(r[13])]
