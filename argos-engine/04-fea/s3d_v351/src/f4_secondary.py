#!/usr/bin/env python3
"""F4 secondary-structure joint checks on CAD v3.5.1 (fea3d 2026-10-19; brief F4, lead CHANGELOG 188).

Joints
  J-PD01  4x M3 ISO 4762 A2-70 x 12, 0.6 N m, through the G11 washer PD-11 (7/3.4 x 2) into TC-02 (HW-105)
          loads: F1 FE connector forces PDFOOT_* per screw (SIM) + hand-calc increments (DERIVED)
  J-FD01  2x M3 DIN 7984 A4-70 x 16, 1.0 N m, FD-01 into TC-02, AS568-010 face seal (HW-103)            hand calc (DERIVED)
  J-FD09  2x M4 ISO 4762 A4-70 x 12, 2.05 N m, FD-09 hose-end clamp into GM-09 (helicoil 1.5 D) (HW-127)  hand calc
  J-FS15  2x M4 A4-70 x 12 MV module -> FS-15 (HW-136); 2x M5 A4-70 x 10 FS-15 -> airframe wall, ICD-2 (HW-137)  hand calc
  J-BL05  4x M3 A4-70 x 25 per bleed valve into BL-07 (HW-138; valve 0.30 kg ASSUMED, not selected)       hand calc
  ICD-14  BL-07 bleed cluster -> airframe: mass, CG and inertial resultant (mount TO-DEFINE, no screw check)

Margins (per screw, limit loads P = external tension, V = shear; SF per 188 (9): LC1/LC3/transport 1.5 y / 2.0 u, FA-1 1.0 / 1.0)
  separation   MS = F_min / (SF_y P) - 1                         (load factor Phi = 0: all external load relieves the clamp; bounding)
  slip         MS = mu (F_min - SF_y P) / (SF_y V) - 1           (mu ASSUMED)
  bolt yield   MS = k_T Rp0.2 As / (F_max + dF_th + SF_y P) - 1  (Phi = 1: all external load into the screw; bounding; tension only)
  bolt ult.    MS = k_T Rm As / (F_max + dF_th + SF_u P) - 1
  host thread  MS = 0.6 Ftu(T) A_n / (F_max + dF_th + SF_u P) - 1 (internal-thread shear area A_n, FED-STD-H28/2 form, AS RECALLED)
  G11 bearing  MS = Sc(T) A_w / (F_max + dF_th + SF_u P) - 1     (J-PD01 only)
  preload      F_nom = T / (K d), K 0.2 (Mechanical hardware rule, ASSUMED); F_min/F_max = 0.75/1.25 F_nom (scatter ASSUMED)
  assembly     nu = sigma_vM(tension + thread torsion) / Rp0.2 at F_nom and F_max (VDI 2230 guide nu <= 0.9 at nominal, AS RECALLED)

usage: f4_secondary.py [lc1=lc1v351_c71] [fa1=fa1_c71] [lc3sfx=_c71]
Output: results/f4_secondary.json, results/tables/f4_secondary.md
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import asm3d as A3  # noqa: E402

ROOT = Path("/home/claude/work/fea3d")
RES = ROOT / "results"
HUB = Path("/home/claude/work/shared-fallback/engine")
SRC = {"hardware": HUB / "03-cad/src/data/hardware_v351.json", "massprops": HUB / "03-cad/v3.5.1/massprops_v3.5.1.json",
       "gnc": HUB / "interfaces/gnc.json", "hose": HUB / "03-cad/calcs/hose_end_reactions_v341_v1.json",
       "net_v2c": HUB / "04-fea/thermal/networks/servo_mount_net_v2c.json", "net_v2d": HUB / "04-fea/thermal/networks/servo_mount_net_v2d.json"}
G0 = 9.80665
MAT = A3.engmat.MATERIALS


def sha16(p):
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def interp(mat, key, T_C):
    d = MAT[mat][key]
    return float(np.interp(T_C, d["T_C"], d["v"])) / 1e6 if "T_C" in d else d["v"] / 1e6


# ------------------------------------------------------------------------------------------------ inputs
args = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
LC1_RUN = args.get("lc1", "lc1v351_c71")
FA1_RUN = args.get("fa1", "fa1_c71")
LC3_SFX = args.get("lc3sfx", "_c71")

gnc = json.loads(SRC["gnc"].read_text())
DLL = gnc["design_limit_loads"]
A_LAT_TD = DLL["lateral_accel_at_pivot_touchdown_g"]["v"]          # 6.29 g SIM max
A_AX_TD = DLL["axial_accel_touchdown_g"]["v"]                      # 5.43 g SIM max
A_AX_ENV = DLL["axial_accel_landing_shock_envelope_g"]["v"]        # 10 g DERIVED v1 envelope (kept by GNC as the hard-landing envelope)
ALPHA_TD = DLL["body_angular_accel_touchdown_rad_s2"]["v"]         # 79.28 rad/s2
A_AX_FL = DLL["axial_accel_flight_g"]["v"]                         # 4.04 g
A_LAT_FL = DLL["lateral_accel_at_pivot_flight_g"]["v"]             # 0.61 g
ALPHA_FL = DLL["body_angular_accel_flight_rad_s2"]["v"]            # 11.01 rad/s2
A_TRANSPORT = DLL["transport_handling_g"]["v"]                     # 3 g ASSUMED (any axis)
M_DRY = gnc["reference_vehicle"]["dry_mass_kg"]["v"]               # 13.671 kg DERIVED (lowest vehicle mass -> highest spike acceleration)
F_SPIKE, DLF = 1800.0, 2.0                                         # lead 194: thrust spike 1.8 kN x 4 ms, DLF 2.0
A_AX_FA1 = DLF * F_SPIKE / (M_DRY * G0)                            # g, DERIVED equipment bound for the FA-1 spike
P_MAN = 7.0                                                        # MPa manifold MEOP (S-AX LC1 / F1 PM step)

mp = json.loads(SRC["massprops"].read_text())
ROWS = mp["ledger_mid"]
hw = json.loads(SRC["hardware"].read_text())
HWL = {r["id"]: r for r in hw["lines"]}
hose = json.loads(SRC["hose"].read_text())["reactions_8deg"]
net = {k: json.loads(SRC[k].read_text()) for k in ("net_v2c", "net_v2d")}
T_HEADTOP_SOAK = max(n["runs"][0]["boundary_peaks_C"]["head_top_r20_26_mean"] for n in net.values())   # 121.1 C (thermal network, soak-back)
T_FRAME_SOAK = max(max(v["bracket_max_C"] for v in n["conclusion"]["worst_by_variant"].values()) for n in net.values())  # PD-01 frame

# thread data, ISO 724 / ISO 965-1 6g/6H, ISO 4762 heads (AS RECALLED); stress areas as in Mechanical's hardware rule
TH = {"M3": dict(d=3.0, P=0.5, d2=2.675, d3=2.387, As=5.03, Ds_min=2.874, En_max=2.775, dk=5.5, dh=3.4),
      "M4": dict(d=4.0, P=0.7, d2=3.545, d3=3.141, As=8.78, Ds_min=3.838, En_max=3.663, dk=7.0, dh=4.5),
      "M5": dict(d=5.0, P=0.8, d2=4.480, d3=4.019, As=14.18, Ds_min=4.826, En_max=4.605, dk=8.5, dh=5.5)}
K_NUT, SCATTER, MU_SLIP = hw["rules"]["K_nut"], 0.25, 0.20
RP_BOLT, RM_BOLT = interp("SS-A4-70", "Fty", 20.0), interp("SS-A4-70", "Ftu", 20.0)   # 450 / 700 MPa (A2-70 same class minima, AS RECALLED)


def k_T_bolt(T_C):
    """Strength retention of A2/A4-70 at T: proxy = EN 10088 1.4404 Rp0.2(T)/Rp0.2(20) (engmat SS316L; ASSUMED proxy, TO-VERIFY)."""
    return interp("SS316L", "Fty", max(T_C, 20.0)) / interp("SS316L", "Fty", 20.0)


def strip_area(th, L_e):
    n = 1.0 / th["P"]
    return math.pi * n * L_e * th["Ds_min"] * (1.0 / (2.0 * n) + 0.57735 * (th["Ds_min"] - th["En_max"]))


def preload(size, T_Nm, dk=None):
    th = TH[size]
    F = T_Nm * 1e3 / (K_NUT * th["d"])
    Db = 0.5 * ((dk or th["dk"]) + th["dh"])
    a = th["P"] / (2 * math.pi)
    b = th["d2"] / (2 * math.cos(math.radians(30.0)))
    mu = (K_NUT * th["d"] - a) / (b + 0.5 * Db)                     # friction implied by K (thread = head), DERIVED
    ds = 0.5 * (th["d2"] + th["d3"])
    Wp = math.pi * ds ** 3 / 16.0

    def nu(Fp):
        s, t = Fp / th["As"], Fp * (a + mu * b) / Wp
        return math.sqrt(s * s + 3 * t * t) / RP_BOLT
    return {"F_nom_N": F, "F_min_N": (1 - SCATTER) * F, "F_max_N": (1 + SCATTER) * F, "mu_implied": mu,
            "nu_assembly_nom": nu(F), "nu_assembly_max": nu((1 + SCATTER) * F)}


def ms(cap, dem):
    return None if dem <= 1e-9 else cap / dem - 1.0


PHI_TYP = 0.2     # load factor of a stiff metal joint, ASSUMED typical (LITERATURE AS RECALLED, NASA-STD-5020 practice computes it per joint)


def margins(j, P, V, SFy, SFu, T_bolt_C, T_host_C, dF_th=0.0, Pc=None):
    """Two variants: bounding (Phi 0 for separation / slip, Phi 1 for the screw and the host thread) and Phi = 0.2 (suffix _phi02).
    P = external tension (limit), V = shear (limit), Pc = external compression through the washer (default P, bounding)."""
    th = TH[j["size"]]
    pl = j["pre"]
    kT = k_T_bolt(T_bolt_C)
    out = {"P_N": round(P, 2), "V_N": round(V, 2), "SF": [SFy, SFu], "T_bolt_C": round(T_bolt_C, 1), "T_host_C": round(T_host_C, 1),
           "k_T_bolt": round(kT, 3), "dF_th_N": round(dF_th, 1),
           "hot_preload_utilisation": round((pl["F_max_N"] + dF_th) / (kT * RP_BOLT * th["As"]), 3)}
    Fsu_host = (MAT[j["host"]]["Fsu_over_Ftu"]["v"] * interp(j["host"], "Ftu", T_host_C)) if j.get("host") else None
    for tag, phi in (("", None), ("_phi02", PHI_TYP)):
        loss = SFy * P if phi is None else (1.0 - phi) * SFy * P
        add_y = SFy * P if phi is None else phi * SFy * P
        add_u = SFu * P if phi is None else phi * SFu * P
        Fb_u = max(pl["F_max_N"] + dF_th + add_u, SFu * P)
        out["MS_sep" + tag] = ms(pl["F_min_N"], loss)
        out["MS_slip" + tag] = None if V <= 1e-9 else MU_SLIP * max(pl["F_min_N"] - loss, 0.0) / (SFy * V) - 1.0
        out["MS_bolt_y" + tag] = ms(kT * RP_BOLT * th["As"], pl["F_max_N"] + dF_th + add_y)
        out["MS_bolt_u" + tag] = ms(kT * RM_BOLT * th["As"], Fb_u)
        if Fsu_host is not None:
            out["MS_thread_host" + tag] = ms(Fsu_host * strip_area(th, j["L_e"]), Fb_u)
    out["MS_bolt_shear"] = ms(kT * MAT["SS-A4-70"]["Fsu_over_Ftu"]["v"] * RM_BOLT * math.pi / 4 * th["d3"] ** 2, SFu * V)
    if j.get("washer_A"):
        out["MS_G11_bearing"] = ms(interp("G11", "Sc", T_host_C) * j["washer_A"], pl["F_max_N"] + dF_th + SFu * (P if Pc is None else Pc))
    for k in list(out):
        if k.startswith("MS_") and out[k] is not None:
            out[k] = round(out[k], 3)
    return out


JIN = {}


def msmin(m, phi=False, slip=True):
    v = [x for k, x in m.items() if k.startswith("MS_") and x is not None and (k.endswith("_phi02") == phi or k in ("MS_bolt_shear", "MS_G11_bearing"))
         and (slip or not k.startswith("MS_slip"))]
    return min(v)


def M_(key, j, *a, **k):
    """margins() that also records its inputs for the torque-window scan."""
    JIN.setdefault(key, []).append((j, a, k))
    return margins(j, *a, **k)


def torque_window(key, T0, size, dk=None, n=281):
    """Torque range (N m) for which every recorded case keeps MS >= 0: bounding set and Phi 0.2 set (same K and scatter)."""
    res = {}
    for phi, slip in ((False, True), (True, True), (True, False)):
        ok = []
        for T in np.linspace(0.3 * T0, 1.6 * T0, n):
            pre = preload(size, float(T), dk=dk)
            good = True
            for j, a, k in JIN[key]:
                if msmin(margins(dict(j, pre=pre), *a, **k), phi, slip) < 0:
                    good = False
                    break
            ok.append((float(T), good))
        Ts = [T for T, g in ok if g]
        res[("phi02" if phi else "bounding") + ("" if slip else "_noslip")] = [round(min(Ts), 3), round(max(Ts), 3)] if Ts else None
    return res


def rows_sel(pred):
    sel = [r for r in ROWS if pred(r["pn"].replace("ENG-", ""), r)]
    m = sum(r["m_kg"] for r in sel)
    cg = sum(r["m_kg"] * np.asarray(r["cg_mm"]) for r in sel) / m
    return m, cg, sorted({r["pn"].replace("ENG-", "") for r in sel})


def accel_cases(z_mm, rxy_mm):
    """Limit acceleration sets at a point (engine frame, pivot origin): list of (case, SFy, SFu, a_lat_g, a_ax_g).  The angular
    acceleration is added as alpha x distance from the pivot (lateral alpha z, axial alpha r_xy) with the worst sign (bounding)."""
    z, r = abs(z_mm) / 1e3, rxy_mm / 1e3
    return [("LC1 flight", 1.5, 2.0, A_LAT_FL + ALPHA_FL * z / G0, A_AX_FL + ALPHA_FL * r / G0),
            ("LC3 touchdown (5.43 g SIM)", 1.5, 2.0, A_LAT_TD + ALPHA_TD * z / G0, A_AX_TD + ALPHA_TD * r / G0),
            ("LC3 hard-landing envelope (10 g)", 1.5, 2.0, A_LAT_TD + ALPHA_TD * z / G0, A_AX_ENV + ALPHA_TD * r / G0),
            ("FA-1 spike (equipment bound)", 1.0, 1.0, A_LAT_FL, A_AX_FA1),
            ("transport 3 g any axis", 1.5, 2.0, A_TRANSPORT, A_TRANSPORT)]


RESULT = {"id": "f4_secondary", "version": "v1", "date": "2026-10-19", "owner": "fea3d", "cad": "v3.5.1",
          "sources": {k: {"path": str(v.relative_to(HUB)), "sha256_16": sha16(v)} for k, v in SRC.items()},
          "inputs": {"A_LAT_TD_g": A_LAT_TD, "A_AX_TD_g": A_AX_TD, "A_AX_ENV_g": A_AX_ENV, "ALPHA_TD_rad_s2": ALPHA_TD, "A_AX_FL_g": A_AX_FL,
                     "A_LAT_FL_g": A_LAT_FL, "ALPHA_FL_rad_s2": ALPHA_FL, "A_TRANSPORT_g": A_TRANSPORT, "M_DRY_kg": M_DRY,
                     "A_AX_FA1_g": round(A_AX_FA1, 2), "P_MAN_MPa": P_MAN, "K_nut": K_NUT, "preload_scatter": SCATTER, "mu_slip": MU_SLIP,
                     "Rp_bolt_MPa": RP_BOLT, "Rm_bolt_MPa": RM_BOLT, "T_headtop_soak_C": T_HEADTOP_SOAK, "T_PD01_frame_soak_C": T_FRAME_SOAK,
                     "tags": {"A_*_g, ALPHA_*": "SIM (gnc.json v3.1 design_limit_loads) except A_AX_ENV (DERIVED v1 envelope) and A_TRANSPORT (ASSUMED)",
                              "A_AX_FA1_g": "DERIVED: DLF 2.0 x 1.8 kN (lead 194) / (dry mass 13.671 kg x g0): equipment bound for the FA-1 spike",
                              "P_MAN_MPa": "S-AX LC1 manifold MEOP (as in the F1 PM step)", "K_nut": "ASSUMED (Mechanical hardware rule)",
                              "preload_scatter": "ASSUMED +/-25 %", "mu_slip": "ASSUMED 0.20 (TO-VERIFY)",
                              "Rp/Rm_bolt": "LITERATURE ISO 3506-1 class 70 minima (engmat SS-A4-70; A2-70 same minima AS RECALLED)",
                              "T_*_soak_C": "DERIVED thermal network servo_mount_net v2c/v2d (max of both)"}},
          "joints": {}}

# ================================================================================================ J-PD01 (FE connectors)
def load_post(path):
    p = RES / path
    return json.loads(p.read_text()) if p.exists() else None


j = {"size": "M3", "n": 4, "T_Nm": HWL["HW-105"]["torque_Nm"], "host": "AL6061-T6", "L_e": 5.0, "washer_A": math.pi / 4 * (7.0 ** 2 - 3.4 ** 2)}
j["pre"] = preload("M3", j["T_Nm"])
mPD, cgPD, pnPD = rows_sel(lambda pn, r: r["group"] == "engine" and (pn.startswith("PD-") and pn != "PD-11" or pn in ("EL-05", "TC-05", "TC-11")))
# thermal preload change in the G11 stack (soak-back: head top 121 C, frame 64 C; assembled at 20 C).  Stack: PD-01 foot 4.5 mm 6061,
# G11 washer 2.0 mm, screw grip 6.5 mm.  G11 through-thickness CTE 50e-6 /K (30-70e-6 range) and E_z 10 GPa: LITERATURE AS RECALLED, TO-VERIFY.
E_b, a_b = 193e3, 17.3e-6                       # A2-70: E (engmat A4-70 value), alpha 17.3e-6 (1.4301, AS RECALLED)
a_al = interp("AL6061-T6", "alpha", 20.0) * 1e6
t_ft, t_w, Lk = 4.5, 2.0, 6.5
dT_ft = T_FRAME_SOAK - 20.0
dT_w = 0.5 * (T_HEADTOP_SOAK + T_FRAME_SOAK) - 20.0
dT_b = (t_ft * dT_ft + t_w * dT_w) / Lk
k_b = E_b * TH["M3"]["As"] / (Lk + 0.8 * 3.0)
A_cone = math.pi / 4 * ((5.5 + t_ft / 2) ** 2 - 3.4 ** 2)
dth = {}
for a_g11 in (30e-6, 50e-6, 70e-6):
    k_w = 10e3 * j["washer_A"] / t_w
    k_m = 1.0 / (1.0 / k_w + t_ft / (68.9e3 * A_cone))
    dd = a_al * t_ft * dT_ft + a_g11 * t_w * dT_w - a_b * Lk * dT_b
    dth[f"{a_g11 * 1e6:.0f}e-6"] = dd / (1.0 / k_b + 1.0 / k_m)
DF_TH_PD = dth["50e-6"]
cases = []
src_note = []
for run in (LC1_RUN, "lc1v351_design_rigid"):
    d = load_post(f"f1_post_{run}.json")
    if d:
        src_note.append(f"LC1 {run}")
        for st, sd in d["states"].items():
            for sc in sd["cases"]["LC1"]["connectors"]:
                f = sc["forces"]
                for lab in [k for k in f if k.startswith("PDFOOT")]:
                    P = max(-f[lab]["k2"], 0.0)
                    Pb = abs(f[lab]["k2"])
                    cases.append(("LC1", st, sc["subcase"], lab, P, Pb, math.hypot(f[lab]["k0"], f[lab]["k1"]), 1.5, 2.0))
        break
for run in (FA1_RUN, "fa1_v351"):
    d = load_post(f"f1_post_{run}.json")
    if d:
        src_note.append(f"FA-1 {run}")
        for st, sd in d["states"].items():
            for cid, cd in sd["cases"].items():
                if cid == "FA1T":
                    continue
                for sc in cd["connectors"]:
                    f = sc["forces"]
                    dP = A_AX_FA1 * G0 * mPD / 4.0
                    for lab in [k for k in f if k.startswith("PDFOOT")]:
                        P = max(-f[lab]["k2"], 0.0) + dP
                        cases.append((cid, st, sc["subcase"], lab, P, abs(f[lab]["k2"]) + dP, math.hypot(f[lab]["k0"], f[lab]["k1"]), 1.0, 1.0))
        break
lc3_used = None
for sfx in (LC3_SFX, ""):
    envs = []
    for az in ("000", "045", "090", "135", "180", "225", "270", "315"):
        d = load_post(f"f1_post_lc3_pose_stop{az}{sfx}.json")
        if d:
            envs.append((az, d["connectors_envelope"]))
    if len(envs) == 8:
        lc3_used = sfx or "(legacy v1.1)"
        src_note.append(f"LC3 pose_stopXXX{sfx}")
        dP = (A_AX_ENV - A_AX_TD) * G0 * mPD / 4.0
        for az, ce in envs:
            for lab in sorted({k.rsplit("_k", 1)[0] for k in ce if k.startswith("PDFOOT")}):
                k0, k1, k2 = (ce[f"{lab}_k{q}"]["max_abs_N"] for q in range(3))
                cases.append(("LC3", f"stop{az}", "envelope", lab, k2, k2, math.hypot(k0, k1), 1.5, 2.0))
                cases.append(("LC3+10g", f"stop{az}", "envelope", lab, k2 + dP, k2 + dP, math.hypot(k0, k1), 1.5, 2.0))
        break
gov = {}
for cid, st, sc, lab, P, Pb, V, SFy, SFu in cases:
    key = cid
    T_host_end = 40.0   # FE end-of-burn TC-02 at the taps <= 38.2 C (SIM, all states)
    for tag, Pv, Pc, Tb, Th, dF in (("FE sign (opening only)", P, (Pb if P <= 0 else 0.0), T_host_end, T_host_end, 0.0),
                                    ("bounding |k2| + soak-back thermal preload", Pb, Pb, 0.5 * (T_HEADTOP_SOAK + T_FRAME_SOAK), T_HEADTOP_SOAK, DF_TH_PD)):
        m = M_("J-PD01", j, Pv, V, SFy, SFu, Tb, Th, dF, Pc=Pc)
        m.update({"case": cid, "state": st, "subcase": sc, "screw": lab, "variant": tag})
        g = gov.setdefault((key, tag), m)
        if msmin(m) < msmin(g):
            gov[(key, tag)] = m
RESULT["joints"]["J-PD01"] = {"hardware": "HW-105 4x M3 ISO 4762 A2-70 x 12, 0.6 N m (DESIGN, PD-11 note), G11 washer 7/3.4 x 2, TC-02 M3 tap 8 deep, engagement 5.0-6.0 (5.0 used)",
                              "preload": j["pre"], "washer_area_mm2": round(j["washer_A"], 2), "mass_supported_kg": round(mPD, 4), "cg_mm": cgPD.round(1).tolist(),
                              "items": pnPD, "load_source": src_note, "lc3_formulation": lc3_used,
                              "thermal_preload_change_N": {k: round(v, 1) for k, v in dth.items()},
                              "thermal_note": (f"soak-back head top {T_HEADTOP_SOAK} C / frame {T_FRAME_SOAK} C (thermal network, DERIVED); stack foot 4.5 mm 6061 + G11 2.0 mm, "
                                               "screw grip 6.5 mm; G11 through-thickness CTE 30/50/70e-6 and E_z 10 GPa AS RECALLED (TO-VERIFY); the 50e-6 value is used in the bounding variant"),
                              "sign_note": "connector force on the PD-01 foot = +f e (asm v1.2); k2 < 0 = joint opening = screw tension; the bounding variant takes |k2|",
                              "governing": [dict(v, key=k[0]) for k, v in gov.items()]}

# ================================================================================================ J-FD01 (hand)
j = {"size": "M3", "n": 2, "T_Nm": HWL["HW-103"]["torque_Nm"], "host": "AL6061-T6", "L_e": 5.5}
j["pre"] = preload("M3", j["T_Nm"], dk=5.5)
mFD, cgFD, pnFD = rows_sel(lambda pn, r: r["group"] == "engine" and pn in ("FD-01", "BL-01", "BL-02", "BL-03A", "BL-03E", "BL-04A", "BL-04",
                                                                              "FD-03", "FD-05", "FD-07A", "FD-07"))
A_bound, A_seal = math.pi * 7.0 ** 2, math.pi / 4 * (6.07 + 2 * 1.78) ** 2
s_FD = 166.71 - 144.31
he = hose["0.184"]["max"]
gov = []
for area_tag, A in (("bounding R7 (as the F1 PM cap)", A_bound), ("AS568-010 OD 9.63 (AS RECALLED; groove OD TO-VERIFY)", A_seal)):
    for cname, SFy, SFu, alat, aax in accel_cases(cgFD[2], math.hypot(cgFD[0], cgFD[1])):
        a = math.hypot(alat, aax)
        P = P_MAN * A / 2.0 + mFD * a * G0
        V = mFD * a * G0
        if cname.startswith("LC3"):
            P += he["F_eng"]["norm"] + he["M_eng"]["norm"] * 1e3 / s_FD
            V += he["F_eng"]["norm"]
        m = M_("J-FD01" + ("" if A == A_bound else " sealOD"), j, P, V, SFy, SFu, T_HEADTOP_SOAK, T_HEADTOP_SOAK, 0.0)
        m.update({"case": cname, "seal_area": area_tag, "a_lat_g": round(alat, 2), "a_ax_g": round(aax, 2)})
        gov.append(m)
RESULT["joints"]["J-FD01"] = {"hardware": "HW-103 2x M3 DIN 7984 A4-70 x 16, 1.0 N m (DESIGN, FD-01 note), TC-02 M3 tap 8 deep, engagement 5.5 used (grip 10.5 hole; the grip 3.0 hole would bottom a 16 mm screw in the 8 mm tap: Mechanical action TO-VERIFY)",
                              "preload": j["pre"], "mass_supported_kg": round(mFD, 4), "cg_mm": cgFD.round(1).tolist(), "items": pnFD,
                              "pressure": {"P_MPa": P_MAN, "A_bound_mm2": round(A_bound, 1), "A_seal_mm2": round(A_seal, 1),
                                           "F_bound_N": round(P_MAN * A_bound, 1), "F_seal_N": round(P_MAN * A_seal, 1)},
                              "hose_engine_end_at_stop": {"EI_Nm2": 0.184, "F_N": he["F_eng"]["norm"], "M_Nm": he["M_eng"]["norm"],
                                                          "note": "FD-07 spec limit EI (break-even); bounding: the whole hose wrench reaches FD-01 through the riser"},
                              "thermal": "screw A4-70 and block 316L have the same CTE (16e-6, engmat): thermal preload change ~0 (DERIVED); host and screw taken at the soak-back head-top 121 C (bounding; FE end-of-burn at the taps <= 51.7 C SIM)",
                              "cases": gov}

# ================================================================================================ J-FD09 (hand)
j = {"size": "M4", "n": 2, "T_Nm": HWL["HW-127"]["torque_Nm"], "host": "AL6061-T6", "L_e": 6.0}
j["pre"] = preload("M4", j["T_Nm"])
m9, cg9, pn9 = rows_sel(lambda pn, r: r["group"] == "fixed" and pn in ("FD-09", "FD-07B", "FD-07"))
Z_GM09_TOP, H_SLEEVE, E_EDGE = 32.0, 42.0, 5.0
cases = []
for EI in ("0.184", "0.5"):
    hf = hose[EI]["max"]
    for cname, SFy, SFu, alat, aax in accel_cases(cg9[2], math.hypot(cg9[0], cg9[1])):
        Fi = m9 * math.hypot(alat, aax) * G0
        Fh, Mh = (hf["F_fix"]["norm"], hf["M_fix"]["norm"] * 1e3) if cname.startswith("LC3") or cname.startswith("LC1") else (0.0, 0.0)
        F = Fh + Fi
        M = Fh * H_SLEEVE + Mh + Fi * (cg9[2] - Z_GM09_TOP)
        P = F / 2.0 + M / (2.0 * E_EDGE)
        V = F / 2.0
        m = M_("J-FD09" + ("" if EI == "0.184" else " EI0.5"), j, P, V, SFy, SFu, 60.0, 60.0, 0.0)
        m.update({"case": cname, "hose_EI_Nm2": float(EI), "F_N": round(F, 2), "M_Nmm": round(M, 1)})
        cases.append(m)
RESULT["joints"]["J-FD09"] = {"hardware": "HW-127 2x M4 ISO 4762 A4-70 x 12, 2.05 N m (DERIVED by Mechanical), into GM-09 with helicoil 1.5 D (6.0 mm); thread check as a direct M4 tap in 6061 (conservative: the insert enlarges the shear diameter)",
                              "preload": j["pre"], "mass_kg": round(m9, 4), "cg_mm": cg9.round(1).tolist(), "items": pn9,
                              "geometry": f"sleeve axis {H_SLEEVE} mm above the GM-09 top face (z {Z_GM09_TOP}); screws 7.0 mm apart on a radial line; foot edge 5 mm beyond the holes (CAD parts_feed): prying lever 5 mm used for every moment axis (bounding)",
                              "hose_fixed_end_at_stop": {k: hose[k]["max"] for k in ("0.184", "0.5")},
                              "hose_note": "Mechanical hose_end_reactions_v341_v1 (DERIVED, EI ASSUMED; CAD v3.4.1 feed route, v3.5.1 route assumed unchanged TO-VERIFY); EI 0.184 = FD-07 spec limit, 0.5 = sensitivity; applied in LC1 and LC3 (engine at the 8 deg stop: bounding for LC1)",
                              "temperature": "GM-09 60 C (F1 thermal state of the fixed group, SIM/ASSUMED)", "cases": cases}

# ================================================================================================ J-FS15 (hand)
AZ = math.radians(219.5)
e_r, e_t = np.array([math.cos(AZ), math.sin(AZ), 0.0]), np.array([-math.sin(AZ), math.cos(AZ), 0.0])
O_mod = np.array([10.0 * math.cos(AZ), 10.0 * math.sin(AZ), 279.5])


def to_mod(x):
    d = np.asarray(x, float) - O_mod
    return np.array([d @ e_r, d @ e_t, d[2]])


def in_module(pn, r):
    if r["group"] != "fixed" or pn.startswith("BL-") or pn in ("FD-08", "FS-15", "FD-07", "FD-07B", "FD-09", "FD-11"):
        return False
    c = np.asarray(r["cg_mm"])
    return math.hypot(c[0] - O_mod[0], c[1] - O_mod[1]) <= 30.0 and 250.0 <= c[2] <= 350.0


mM, cgM, pnM = rows_sel(in_module)
mB, cgB, _ = rows_sel(lambda pn, r: pn == "FS-15")
uM, uMB = to_mod(cgM), to_mod((mM * cgM + mB * cgB) / (mM + mB))
jm4 = {"size": "M4", "n": 2, "T_Nm": HWL["HW-136"]["torque_Nm"], "host": "AL6061-T6", "L_e": 7.0}
jm4["pre"] = preload("M4", jm4["T_Nm"])
jm5 = {"size": "M5", "n": 2, "T_Nm": HWL["HW-137"]["torque_Nm"], "host": None}
jm5["pre"] = preload("M5", jm5["T_Nm"])
c4, c5 = np.array([15.5, 0.0, 15.0]), np.array([58.5, 0.0, 30.0])
res4, res5 = [], []
for cname, SFy, SFu, alat, aax in accel_cases(to_mod(cgM)[2] + 279.5, math.hypot(cgM[0], cgM[1])):
    worst4, worst5 = None, None
    for ph in range(0, 360, 15):
        for sgn in (1.0, -1.0):
            a = np.array([alat * math.cos(math.radians(ph)), alat * math.sin(math.radians(ph)), sgn * aax])  # g, module frame (u, v, w)
            # module -> M4 pair
            F = mM * G0 * a
            M = np.cross(uM - c4, F)
            P4 = abs(F[2]) / 2 + abs(M[0]) * 19.0 / (19.0 ** 2 + 5.0 ** 2) + abs(M[1]) / (2 * 3.5)
            V4 = math.hypot(F[0], F[1]) / 2 + abs(M[2]) / 14.0
            # module + bracket -> M5 pair (radial screws, axis u)
            F5 = (mM + mB) * G0 * a
            M5 = np.cross(uMB - c5, F5)
            P5 = abs(F5[0]) / 2 + abs(M5[1]) / (2 * 10.0) + abs(M5[2]) * 18.0 / (18.0 ** 2 + 6.0 ** 2)
            V5 = math.hypot(F5[1], F5[2]) / 2 + abs(M5[0]) / 12.0
            if worst4 is None or P4 + V4 > worst4[0] + worst4[1]:
                worst4 = (P4, V4, ph, sgn)
            if worst5 is None or P5 + V5 > worst5[0] + worst5[1]:
                worst5 = (P5, V5, ph, sgn)
    m = M_("J-FS15 M4", jm4, worst4[0], worst4[1], SFy, SFu, 60.0, 60.0)
    m.update({"case": cname, "lat_dir_deg": worst4[2], "ax_sign": worst4[3]})
    res4.append(m)
    m = M_("J-FS15 M5", jm5, worst5[0], worst5[1], SFy, SFu, 60.0, 60.0)
    m.update({"case": cname, "lat_dir_deg": worst5[2], "ax_sign": worst5[3]})
    res5.append(m)
RESULT["joints"]["J-FS15"] = {"hardware": "HW-136 2x M4 A4-70 x 12 module -> FS-15 (2.05 N m DERIVED, engagement 7.0 in FS-01A/B 6061); HW-137 2x M5 A4-70 x 10 FS-15 -> airframe wall (4.15 N m DERIVED; airframe insert TO-DEFINE: no host-thread check)",
                              "module_mass_kg": round(mM, 4), "module_cg_mm": cgM.round(1).tolist(), "module_cg_module_frame_uvw_mm": uM.round(1).tolist(),
                              "bracket_mass_kg": round(mB, 4), "items": pnM, "preload_M4": jm4["pre"], "preload_M5": jm5["pre"],
                              "geometry": "module frame u radial (axis r 10 az 219.5), w = z - 279.5; M4 pair at (u 15.5, v +/-7) vertical, plate v +/-12, inner edge u 12 (prying lever 3.5 mm); "
                                          "M5 pair at (u 58.5, v +/-6, w 30) radial, flange v +/-12, w 10..40 (prying lever 10 mm) (CAD parts_feed)",
                              "assumption": "FS-15 carries the whole module (the FD-08 line flange and the tank line FD-12F carry nothing: bounding for FS-15); lateral direction swept 0..345 deg, axial both signs",
                              "M4_cases": res4, "M5_cases": res5}

# ================================================================================================ J-BL05 (hand)
jv = {"size": "M3", "n": 4, "T_Nm": HWL["HW-138"]["torque_Nm"], "host": "AL6061-T6", "L_e": 6.0}
jv["pre"] = preload("M3", jv["T_Nm"])
M_V, H_V, PITCH = 0.30, 45.0, 22.0
resv = []
for zc, rxy, tag in ((310.0, math.hypot(43.1, 21.0), "V1 az 26"), (310.0, math.hypot(18.0, 44.5), "V2 az 112")):
    for cname, SFy, SFu, alat, aax in accel_cases(zc, rxy):
        c = PITCH / math.sqrt(2.0)
        Mlat = M_V * alat * G0 * H_V
        P = M_V * aax * G0 / 4.0 + Mlat * c / (4 * (PITCH / 2) ** 2)
        V = M_V * alat * G0 / 4.0
        m = M_("J-BL05", jv, P, V, SFy, SFu, 60.0, 60.0)
        req_pitch = None
        if SFy * P > 0:
            # pitch for MS_sep = 0: F_min = SFy (m aax g/4 + Mlat (p/sqrt2) / (p^2)) -> p = SFy Mlat / sqrt2 / (F_min - SFy m aax g / 4)
            den = jv["pre"]["F_min_N"] - SFy * M_V * aax * G0 / 4.0
            req_pitch = SFy * Mlat / math.sqrt(2.0) / den if den > 0 else float("inf")
        m.update({"case": cname, "valve": tag, "a_lat_g": round(alat, 2), "a_ax_g": round(aax, 2), "pitch_for_MS_sep_0_mm": round(req_pitch, 2) if req_pitch else None})
        resv.append(m)
RESULT["joints"]["J-BL05"] = {"hardware": "HW-138 4x M3 ISO 4762 A4-70 x 25 per valve (ASSUMED, valve not selected), 0.88 N m DERIVED; BL-07 6061 tap, engagement 6.0 ASSUMED (TO-VERIFY)",
                              "valve": {"m_kg": M_V, "tag": "ASSUMED 0.30 kg (BOM: MASS RISK)", "cg_above_subbase_mm": H_V, "pattern": f"square {PITCH} mm pitch ASSUMED (inside the Ø36 envelope; TO-VERIFY at selection)"},
                              "preload": jv["pre"], "cases": resv}

# ================================================================================================ ICD-14 cluster (no screw check)
mC, cgC, pnC = rows_sel(lambda pn, r: r["group"] == "fixed" and pn in ("BL-05", "BL-06", "BL-07", "BL-08", "BL-10"))
icd14 = []
for cname, SFy, SFu, alat, aax in accel_cases(cgC[2], math.hypot(cgC[0], cgC[1])):
    icd14.append({"case": cname, "a_lat_g": round(alat, 2), "a_ax_g": round(aax, 2), "F_lat_limit_N": round(mC * alat * G0, 1),
                  "F_ax_limit_N": round(mC * aax * G0, 1), "SF": [SFy, SFu]})
RESULT["joints"]["ICD-14"] = {"mass_kg": round(mC, 4), "cg_mm": cgC.round(1).tolist(), "items": pnC, "limit_loads": icd14,
                              "note": "BL-07 mount to the airframe TO-DEFINE (ICD-14; 2x M4 ASSUMED by Mechanical): inertial resultant at the cluster CG only; the moment follows from the mount position once defined"}

# ================================================================================================ summary + table
summary = []


def add(joint, sub, recs, label_keys):
    for r in recs:
        mss = {k: v for k, v in r.items() if k.startswith("MS_") and v is not None}
        bnd = {k: v for k, v in mss.items() if not k.endswith("_phi02")}
        p02 = {k: v for k, v in mss.items() if k.endswith("_phi02") or k in ("MS_bolt_shear", "MS_G11_bearing")}
        kmin, kmin2 = min(bnd, key=bnd.get), min(p02, key=p02.get)
        summary.append({"joint": joint, "sub": sub, "case": " / ".join(str(r.get(k)) for k in label_keys if r.get(k) is not None),
                        "P_N": r["P_N"], "V_N": r["V_N"], "MS_min": mss[kmin], "criterion": kmin, "MS_min_phi02": mss[kmin2],
                        "criterion_phi02": kmin2, "hot_preload_utilisation": r.get("hot_preload_utilisation"), **mss})


add("J-PD01", "4x M3 A2-70 / G11 / TC-02", RESULT["joints"]["J-PD01"]["governing"], ["key", "variant", "state", "screw"])
add("J-FD01", "2x M3 A4-70 / TC-02", RESULT["joints"]["J-FD01"]["cases"], ["case", "seal_area"])
add("J-FD09", "2x M4 A4-70 / GM-09", RESULT["joints"]["J-FD09"]["cases"], ["case", "hose_EI_Nm2"])
add("J-FS15", "2x M4 module->FS-15", RESULT["joints"]["J-FS15"]["M4_cases"], ["case"])
add("J-FS15", "2x M5 FS-15->wall (ICD-2)", RESULT["joints"]["J-FS15"]["M5_cases"], ["case"])
add("J-BL05", "4x M3 valve->BL-07", RESULT["joints"]["J-BL05"]["cases"], ["case", "valve"])
RESULT["summary"] = summary
worst = {}
for s in summary:
    k = (s["joint"], s["sub"])
    if k not in worst or s["MS_min"] < worst[k]["MS_min"]:
        worst[k] = s
RESULT["governing_per_joint"] = list(worst.values())
worst2 = {}
for s_ in summary:
    k = (s_["joint"], s_["sub"])
    if k not in worst2 or s_["MS_min_phi02"] < worst2[k]["MS_min_phi02"]:
        worst2[k] = s_
RESULT["governing_per_joint_phi02"] = list(worst2.values())
asm = {k: {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in RESULT["joints"][k].get("preload", {}).items()} for k in ("J-PD01", "J-FD01", "J-FD09", "J-BL05")}
asm["J-FS15 M4"] = {kk: round(vv, 3) for kk, vv in RESULT["joints"]["J-FS15"]["preload_M4"].items()}
asm["J-FS15 M5"] = {kk: round(vv, 3) for kk, vv in RESULT["joints"]["J-FS15"]["preload_M5"].items()}
RESULT["assembly_utilisation"] = asm
TW = {"J-PD01": ("M3", HWL["HW-105"]["torque_Nm"], None), "J-FD01": ("M3", HWL["HW-103"]["torque_Nm"], 5.5),
      "J-FD01 sealOD": ("M3", HWL["HW-103"]["torque_Nm"], 5.5), "J-FD09": ("M4", HWL["HW-127"]["torque_Nm"], None),
      "J-FD09 EI0.5": ("M4", HWL["HW-127"]["torque_Nm"], None), "J-FS15 M4": ("M4", HWL["HW-136"]["torque_Nm"], None),
      "J-FS15 M5": ("M5", HWL["HW-137"]["torque_Nm"], None), "J-BL05": ("M3", HWL["HW-138"]["torque_Nm"], None)}
RESULT["torque_window_Nm"] = {k: dict(torque_window(k, T0, sz, dk), specified=T0) for k, (sz, T0, dk) in TW.items()}
(RES / "f4_secondary.json").write_text(json.dumps(RESULT, indent=1, default=float))

L = ["# F4 secondary-structure joints, CAD v3.5.1 (fea3d 2026-10-19; DERIVED hand calcs, J-PD01 loads SIM from the F1 FE)", "",
     "Minimum margin per joint over all cases (limit loads x SF per 188 (9); preload K 0.2 and +/-25 % scatter ASSUMED; mu 0.20 ASSUMED).", "",
     "Bounding: Phi 0 for separation/slip, Phi 1 for screw and host thread; second set with load factor Phi 0.2 (ASSUMED typical).", "",
     "| joint | screws | governing case (bounding) | P N | V N | MS min (bounding) | criterion | MS sep | MS slip | MS bolt y | MS bolt u | MS host thread | MS bolt shear | MS min (Phi 0.2) | criterion | hot preload util. |",
     "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
fmt = lambda v: "-" if v is None else f"{v:+.2f}"   # noqa: E731
for s in RESULT["governing_per_joint"]:
    L.append(f"| {s['joint']} | {s['sub']} | {s['case']} | {s['P_N']:.1f} | {s['V_N']:.1f} | {fmt(s['MS_min'])} | {s['criterion'][3:]} | "
             f"{fmt(s.get('MS_sep'))} | {fmt(s.get('MS_slip'))} | {fmt(s.get('MS_bolt_y'))} | {fmt(s.get('MS_bolt_u'))} | {fmt(s.get('MS_thread_host'))} | "
             f"{fmt(s.get('MS_bolt_shear'))} | {fmt(s['MS_min_phi02'])} | {s['criterion_phi02'][3:]} | {s['hot_preload_utilisation']:.2f} |")
L += ["", "Worst case per joint with the load factor Phi 0.2 (ASSUMED):", "", "| joint | screws | case | P N | V N | MS min (Phi 0.2) | criterion |", "|---|---|---|---|---|---|---|"]
for s in RESULT["governing_per_joint_phi02"]:
    L.append(f"| {s['joint']} | {s['sub']} | {s['case']} | {s['P_N']:.1f} | {s['V_N']:.1f} | {fmt(s['MS_min_phi02'])} | {s['criterion_phi02'][3:]} |")
L += ["", "Assembly utilisation nu = sigma_vM(tension + thread torsion) / Rp0.2,min at the specified torque (K 0.2; VDI 2230 guide <= 0.9 at nominal, AS RECALLED):", "",
      "| joint | T N m | F_nom N | mu implied | nu nominal | nu at +25 % |", "|---|---|---|---|---|---|"]
for k, v in asm.items():
    Tq = {"J-PD01": HWL["HW-105"]["torque_Nm"], "J-FD01": HWL["HW-103"]["torque_Nm"], "J-FD09": HWL["HW-127"]["torque_Nm"], "J-BL05": HWL["HW-138"]["torque_Nm"],
          "J-FS15 M4": HWL["HW-136"]["torque_Nm"], "J-FS15 M5": HWL["HW-137"]["torque_Nm"]}[k]
    L.append(f"| {k} | {Tq} | {v['F_nom_N']:.0f} | {v['mu_implied']:.3f} | {v['nu_assembly_nom']:.2f} | {v['nu_assembly_max']:.2f} |")
L += ["", "Torque window (N m) keeping every case MS >= 0 (same K 0.2 and +/-25 % scatter; DERIVED, scan 0.3-1.6 x specified):", "",
      "| joint | specified | window, bounding | window, Phi 0.2 | window, Phi 0.2 without slip |", "|---|---|---|---|---|"]
for k, v in RESULT["torque_window_Nm"].items():
    L.append(f"| {k} | {v['specified']} | {v['bounding'] or 'none'} | {v['phi02'] or 'none'} | {v['phi02_noslip'] or 'none'} |")
L += ["", f"J-PD01 thermal preload change at soak-back (G11 CTE 30/50/70e-6): " + ", ".join(f"{v:+.0f} N" for v in dth.values()) + " (DERIVED, G11 data TO-VERIFY).",
      f"ICD-14 bleed cluster: {mC:.3f} kg at {cgC.round(1).tolist()} mm; limit inertial resultants per case in f4_secondary.json.",
      f"FA-1 equipment bound: {A_AX_FA1:.2f} g axial (DLF 2.0 x 1.8 kN / 13.671 kg dry, DERIVED)."]
(RES / "tables" / "f4_secondary.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
