"""Tagged parameters for the GNC models, with interface-file overrides.

Every parameter is (value, tag, note). Tags follow the team charter: REQ, DATASHEET, LITERATURE,
CEA/SIM/FEA, DERIVED, ASSUMED. Scripts read interface JSON from /mnt/project-files/engine/
interfaces/ and never hard-code another discipline's numbers: load_interfaces() records which
file and version supplied each value; missing files fall back to the tagged defaults below.
"""
import json
import os
import numpy as np
from . import propulsion as pr

IFACE = os.environ.get("GNC_IFACE", "/mnt/project-files/engine/interfaces")  # lead fallback hub during mount outages
G0 = 9.80665


def P(v, tag, note=""):
    return {"v": v, "tag": tag, "note": note}


def _read(name):
    p = os.path.join(IFACE, name)
    if not os.path.exists(p):
        return None
    try:
        with open(p) as f:
            return json.load(f)
    except Exception as e:  # keep the failure as evidence
        return {"_read_error": str(e)}


def load_interfaces():
    """Return dict name -> parsed json (or None) for the four interface files."""
    out = {}
    for n in ["ENGINE-BASELINE-v0.json", "combustion.json", "mechanical.json", "electronics.json", "gnc.json"]:
        out[n] = _read(n)
    return out


def default_params():
    """Nominal parameter set (tagged). Values are replaced by interface data where available."""
    base = _read("ENGINE-BASELINE-v0.json") or {}
    gp = base.get("gas_path_v0", {})
    gr = base.get("grain_v0_placeholder", {})
    p = {}
    # ---- engine (Combustion owns; placeholders) ----
    p["F_max"] = P(500.0, "REQ founder 2026-10-11 (ENG-01)")
    p["At"] = P(gp.get("At_m2", 1.4265e-4), "DERIVED ENGINE-BASELINE-v0 gas_path_v0")
    p["eta_cstar"] = P(gp.get("eta_cstar", {}).get("v", 0.92), "ASSUMED ENGINE-BASELINE-v0")
    p["eta_cf"] = P(gp.get("eta_cf", {}).get("v", 0.975), "ASSUMED ENGINE-BASELINE-v0")
    p["a_reg"] = P(0.0577e-3, "ASSUMED ENGINE-BASELINE-v0 placeholder r = a G^n (SI)")
    p["n_reg"] = P(0.5, "ASSUMED ENGINE-BASELINE-v0 placeholder")
    p["rho_f"] = P(1050.0, "ASSUMED ABS density (baseline fuel card rho=1.05)")
    p["L_grain"] = P(gr.get("L_grain_m", 0.354), "ASSUMED ENGINE-BASELINE-v0 grain placeholder")
    p["D_port0"] = P(gr.get("Dport0_m", 0.030), "ASSUMED ENGINE-BASELINE-v0 grain placeholder")
    p["D_grain_o"] = P(gr.get("D_grain_outer_m", 0.052), "ASSUMED ENGINE-BASELINE-v0 grain placeholder")
    p["T_design_inj"] = P(288.15, "ASSUMED: injector sized for F_max at Psat(15 C) (ENG-01 '>= 15 C')")
    p["throttle_floor"] = P(0.20, "REQ/DERIVED ENG-02 rev1 target 20 % (req 25 %, stretch 12.5 %)")
    p["tau_thr"] = P(0.100 / 2.197, "ASSUMED ENG-03 target 10-90 % = 100 ms -> first-order tau")
    p["slew_thr"] = P(5.0, "ASSUMED thrust slew limit [F_max/s] (= 500 %/s)")
    p["deadband_thr"] = P(0.005, "ASSUMED command deadband [fraction of F_max]")
    p["quant_thr"] = P(0.01, "ASSUMED command resolution [fraction of F_max] (ENG-03 <= 2 %)")
    p["t_ign"] = P(0.40, "ASSUMED nominal command-to-ignition delay; MC U(0.2, 0.6) s per brief")
    p["tau_rise"] = P(0.05, "ASSUMED thrust rise time constant after ignition")
    p["tau_off"] = P(0.035, "DERIVED ENG-05: < 10 % in <= 100 ms -> tau <= 43 ms")
    p["residual_liq"] = P(0.03, "ASSUMED unusable liquid fraction of load (outlet/dip-tube residual)")
    # ---- tank ----
    p["tank_V"] = P(2.5e-3, "ASSUMED ENGINE-BASELINE-v0 tank_v0 (resized by Space/GNC sizing)")
    p["m_n2o"] = P(1.6, "ASSUMED ENGINE-BASELINE-v0 tank_v0 (resized)")
    p["T_tank0"] = P(293.15, "REQ ENG-12 tank conditioned to 20 +/- 3 C")
    p["wall_part"] = P(0.5, "ASSUMED fraction of tank-wall heat capacity in equilibrium with fluid")
    # ---- environment ----
    p["site_alt"] = P(0.0, "ASSUMED ACEMA site elevation unknown (0-800 m sensitivity)")
    p["wind_max"] = P(8.0, "REQ brief MC dispersion: steady wind 0-8 m/s + gusts")
    # ---- landing criteria ----
    p["td_vz_max"] = P(2.0, "REQ REQUIREMENTS sec. 1 item 8")
    p["td_vh_max"] = P(0.5, "REQ REQUIREMENTS sec. 1 item 8")
    p["td_tilt_max"] = P(5.0, "REQ brief success criterion")
    p["td_rate_max"] = P(10.0, "REQ brief success criterion [deg/s]")
    return p


def engine_tables(p, isp_scale=1.0):
    """Precompute steady throttle-map and ceiling tables (numba-friendly arrays)."""
    At, ecs, ecf = p["At"]["v"], p["eta_cstar"]["v"], p["eta_cf"]["v"]
    a, n, rf, L = p["a_reg"]["v"], p["n_reg"]["v"], p["rho_f"]["v"], p["L_grain"]["v"]
    D0, Do = p["D_port0"]["v"], p["D_grain_o"]["v"]
    Fcap = p["F_max"]["v"]
    # calibrate injector for F_max at the design tank temperature
    import CoolProp.CoolProp as CP
    Pd = CP.PropsSI('P', 'T', p["T_design_inj"]["v"], 'Q', 0, 'NitrousOxide')
    mo = pr.mdot_ox_for_thrust(Fcap, D0, At, ecs, ecf, a, n, rf, L, 1.0)
    pc = pr.steady_point(mo, D0, At, ecs, ecf, a, n, rf, L, 1.0)[3]
    K_inj = mo / np.sqrt(Pd - pc)
    Dg = np.linspace(D0, Do, 6)
    Fg = np.linspace(0.0, 1.3 * Fcap, 66)
    mox = np.zeros((Fg.size, Dg.size)); mf = np.zeros_like(mox); pcs = np.zeros_like(mox); isp = np.zeros_like(mox)
    for i, F in enumerate(Fg):
        for j, D in enumerate(Dg):
            if F <= 0:
                continue
            m_o = pr.mdot_ox_for_thrust(F, D, At, ecs, ecf, a, n, rf, L, 1.0)
            r = pr.steady_point(m_o, D, At, ecs, ecf, a, n, rf, L, 1.0)
            mox[i, j], mf[i, j], pcs[i, j], isp[i, j] = m_o, r[2], r[3], r[5]
    Pg = np.linspace(2.0e6, 7.0e6, 41)
    ceil = np.zeros((Pg.size, Dg.size))
    for i, Pt in enumerate(Pg):
        for j, D in enumerate(Dg):
            ceil[i, j] = pr.thrust_ceiling(Pt, D, K_inj, At, ecs, ecf, a, n, rf, L, 1.0, 1e9)
    return dict(K_inj=K_inj, P_design=Pd, Dg=Dg, Fg=Fg, mox=mox, mf=mf, pc=pcs, isp=isp, Pg=Pg, ceil=ceil)
