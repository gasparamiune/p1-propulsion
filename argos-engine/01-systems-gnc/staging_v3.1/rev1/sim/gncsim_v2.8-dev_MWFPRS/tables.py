"""Property tables used by the GNC simulation (generated once, cached as .npz).

1. CEA table (NASA CEA via RocketCEA, shifting equilibrium), N2O / ABS with the lead's
   fuel card (ENGINE-BASELINE-v0: C15H17N, hf=+62.6 kJ/mol, ASSUMED/verify):
   c*(Pc, O/F) [m/s], Isp_vac(eps=3) [s], Isp at sea-level ambient (RocketCEA
   estimate_Ambient_Isp, which includes its own flow-separation estimate) [s], Pe/Pc.
   Tag: CEA (run = this file, gncsim/tables.py v1).
2. N2O saturation table from CoolProp 'NitrousOxide' (Helmholtz EOS):
   T [K] -> Psat [Pa], rho_l, rho_v [kg/m3], u_l, u_v, h_l, h_v [J/kg].
   Tag: LITERATURE (CoolProp 8.0 NitrousOxide EOS); validity near the critical point
   (309.5 K, 7.25 MPa) is the Combustion specialist's to confirm.

SI units everywhere. Versioned by file name.
"""
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")
CEA_FILE = os.path.join(DATA, "cea_N2O_ABS_eps3_v1.npz")
N2O_FILE = os.path.join(DATA, "n2o_saturation_v1.npz")

PC_GRID_BAR = np.array([2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0, 12.0, 15.0, 18.0, 21.0, 25.0, 28.0, 31.0])
OF_GRID = np.array([1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 8.0, 9.0, 10.0])
EPS = 3.0
PA_SL_BAR = 1.01325


def build_cea_table(force=False):
    if os.path.exists(CEA_FILE) and not force:
        return dict(np.load(CEA_FILE))
    from rocketcea.cea_obj_w_units import CEA_Obj
    from rocketcea.cea_obj import add_new_fuel
    add_new_fuel('ABS_v0', "fuel ABS  C 15 H 17 N 1  wt%=100.  h,kj/mol=62.6  t(k)=298.15  rho=1.05\n")
    c = CEA_Obj(oxName='N2O', fuelName='ABS_v0', pressure_units='bar', cstar_units='m/s',
                temperature_units='K', isp_units='sec')
    n1, n2 = len(PC_GRID_BAR), len(OF_GRID)
    cstar = np.zeros((n1, n2)); ispv = np.zeros((n1, n2)); ispsl = np.zeros((n1, n2))
    pepc = np.zeros((n1, n2)); sep = np.zeros((n1, n2))
    for i, pc in enumerate(PC_GRID_BAR):
        for j, of in enumerate(OF_GRID):
            cstar[i, j] = c.get_Cstar(Pc=pc, MR=of)
            ispv[i, j] = c.get_Isp(Pc=pc, MR=of, eps=EPS)
            isp, mode = c.estimate_Ambient_Isp(Pc=pc, MR=of, eps=EPS, Pamb=PA_SL_BAR)
            ispsl[i, j] = isp
            sep[i, j] = 1.0 if 'Separated' in mode else 0.0
            pepc[i, j] = 1.0 / c.get_PcOvPe(Pc=pc, MR=of, eps=EPS)
    os.makedirs(DATA, exist_ok=True)
    np.savez(CEA_FILE, pc_bar=PC_GRID_BAR, of=OF_GRID, cstar=cstar, isp_vac=ispv,
             isp_sl=ispsl, pe_pc=pepc, separated=sep, eps=EPS)
    return dict(np.load(CEA_FILE))


def build_n2o_table(force=False):
    if os.path.exists(N2O_FILE) and not force:
        return dict(np.load(N2O_FILE))
    import CoolProp.CoolProp as CP
    T = np.linspace(240.0, 308.0, 273)
    out = {k: np.zeros_like(T) for k in ["p", "rho_l", "rho_v", "u_l", "u_v", "h_l", "h_v"]}
    for i, t in enumerate(T):
        out["p"][i] = CP.PropsSI('P', 'T', t, 'Q', 0, 'NitrousOxide')
        out["rho_l"][i] = CP.PropsSI('D', 'T', t, 'Q', 0, 'NitrousOxide')
        out["rho_v"][i] = CP.PropsSI('D', 'T', t, 'Q', 1, 'NitrousOxide')
        out["u_l"][i] = CP.PropsSI('U', 'T', t, 'Q', 0, 'NitrousOxide')
        out["u_v"][i] = CP.PropsSI('U', 'T', t, 'Q', 1, 'NitrousOxide')
        out["h_l"][i] = CP.PropsSI('H', 'T', t, 'Q', 0, 'NitrousOxide')
        out["h_v"][i] = CP.PropsSI('H', 'T', t, 'Q', 1, 'NitrousOxide')
    os.makedirs(DATA, exist_ok=True)
    np.savez(N2O_FILE, T=T, **out)
    return dict(np.load(N2O_FILE))


if __name__ == "__main__":
    t = build_cea_table(force=True)
    print("CEA table", t["cstar"].shape)
    print("c* at 25 bar vs O/F:", np.round(t["cstar"][12], 1))
    print("Isp_SL at 25 bar vs O/F:", np.round(t["isp_sl"][12], 1))
    print("Isp_SL at 7 bar vs O/F:", np.round(t["isp_sl"][5], 1))
    print("separated flag at 5 bar:", t["separated"][3])
    n = build_n2o_table(force=True)
    print("N2O table: T", n["T"][0], n["T"][-1], " Psat(293.15)=", np.interp(293.15, n["T"], n["p"]))
