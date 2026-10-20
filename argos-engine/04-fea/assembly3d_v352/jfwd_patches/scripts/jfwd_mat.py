"""J-FWD screw material switch (fea3d 2026-10-20 ~11:55Z; lead 11:25Z ruling 3: the J-FWD screw is IN718 M5 (ISO 7380 form); A4-80 withdrawn.
(a) / (a') / (b2) / (b2') / (b1) stay on A4-80 (consistent with js5); js5b runs with IN718 E and alpha from Mechanical's engmat).

A480   E 193 GPa x SS316L E(T)/E(20), SS316L alpha(T) secant from 20 C, nu 0.29 (engmat SS316L proxy, ASSUMED; as all js runs so far);
       allowables Rp0.2 600 / Rm 800 MPa x SS316L Fty(T)/Fty(20), Ftu(T)/Ftu(20) (Mechanical's jfwd_preload_v352 form, AS RECALLED).
IN718  engmat v1.6 (hub 04-fea/src/engmat.py 46ba163b864c7fc5 = snap/engmat_v1p6): E 200/191/181/170/164 GPa at 20/200/400/600/700 C,
       mean alpha from 20 C 13.0/13.4/14.0/14.8/15.4e-6 (LITERATURE-approx, Special Metals 718 trend), nu 0.29, rho 8190;
       allowables Fty / Ftu (T) = AMS 5662/5663 bar minimums 1034 / 1241 MPa at 20 C, 862 / 965 at 649 C, linear between (DATASHEET,
       engmat).  Fastener-specific allowables (e.g. a bolt spec's Ftu) are Mechanical's to set; the FE rows quote these and say so.
Units: MPa, K (ccx deck units)."""
from __future__ import annotations
import sys
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import asm3d as A3   # noqa: E402

TK = 273.15
MAT = A3.engmat.MATERIALS
AL_ROWS = ([[6.890e4, 293.15], [6.620e4, 373.15], [6.340e4, 423.15], [6.0e4, 473.15], [5.58e4, 523.15], [5.1e4, 573.15]], 0.33,
           [[2.32e-5, 293.15], [2.36e-5, 373.15], [2.43e-5, 473.15], [2.52e-5, 573.15]])
A480_ROWS = ([[1.93e5, 293.15], [1.8721e5, 373.15], [1.7949e5, 473.15], [1.72735e5, 573.15], [1.6598e5, 673.15]], 0.29,
             [[1.6e-5, 293.15], [1.6e-5, 373.15], [1.65e-5, 473.15], [1.7e-5, 573.15], [1.75e-5, 673.15]])


def _in718_rows():
    d = MAT["IN718"]
    E = [[v / 1e6, Tc + TK] for Tc, v in zip(d["E"]["T_C"], d["E"]["v"])]
    a = [[v, Tc + TK] for Tc, v in zip(d["alpha"]["T_C"], d["alpha"]["v"])]
    return (E, float(d["nu"]["v"]), a)


ROWS = {"AL": AL_ROWS, "A480": A480_ROWS, "IN718": _in718_rows()}
DENS = {"A480": 8.0e-9, "IN718": float(MAT["IN718"]["rho"]["v"]) * 1e-12}


def screw_mat(meta):
    return str((meta or {}).get("screw_mat", "A480"))


def deck_block(name):
    """ccx *MATERIAL block (same E(T) / alpha(T) rows as the posts use)."""
    E, nu, a = ROWS[name]
    s = [f"*MATERIAL, NAME={name}", "*DENSITY", f"{DENS[name]:.4e}", "*ELASTIC"]
    s += [f"{e:.6e}, {nu}, {T:.2f}" for e, T in E]
    s.append(f"*EXPANSION, ZERO={A3.T_REF}")
    s += [f"{v:.6e}, {T:.2f}" for v, T in a]
    return "\n".join(s) + "\n"


def _tab(mat, key, T):
    d = MAT[mat][key]
    return float(np.interp(T, d["T_C"], d["v"])) / 1e6


def allowables(name, T_C):
    """(Rp, Rm, kT, kTu, basis) at the screw temperature."""
    T = max(float(T_C), 20.0)
    if name == "IN718":
        Rp, Rm = _tab("IN718", "Fty", T), _tab("IN718", "Ftu", T)
        return Rp, Rm, Rp / _tab("IN718", "Fty", 20.0), Rm / _tab("IN718", "Ftu", 20.0), "IN718 engmat Fty/Ftu(T) (AMS 5662/5663 bar min, DATASHEET)"
    kt = _tab("SS316L", "Fty", T) / _tab("SS316L", "Fty", 20.0)
    ktu = _tab("SS316L", "Ftu", T) / _tab("SS316L", "Ftu", 20.0)
    return 600.0 * kt, 800.0 * ktu, kt, ktu, "A4-80 600/800 x SS316L k_T/k_Tu (ASSUMED proxy)"
