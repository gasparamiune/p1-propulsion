"""J-FD01 / J-FD09 design change (v3.5.2, lead 2026-10-19 items 2-3) on the FEA3D F4 method (hub 04-fea/assembly3d/src/f4_secondary.py,
results/f4_secondary.json): same loads, same formulas (preload F = T/(K d), K 0.2, scatter +/-25 %; bounding Phi 0 separation/slip and Phi 1
screw/host thread; Phi 0.2 variant; hot strength factor k_T = SS316L Fty(T)/Fty(20 C) proxy; SF per 188 (9)), re-implemented here and first
checked against the FEA3D v3.5.1 numbers.  Mechanical, 2026-10-19.  Every value DERIVED unless tagged."""
import json, math, hashlib, sys
import numpy as np
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/04-fea/src")
import engmat
F4 = json.load(open("/home/claude/work/shared-fallback/engine/04-fea/assembly3d/results/f4_secondary.json"))
IN = F4["inputs"]
G0 = 9.80665
MAT = engmat.MATERIALS


def interp(mat, key, T):
    d = MAT[mat][key]
    return float(np.interp(T, d["T_C"], d["v"])) / 1e6 if "T_C" in d else d["v"] / 1e6


TH = {"M3": dict(d=3.0, P=0.5, d2=2.675, d3=2.387, As=5.03, Ds_min=2.874, En_max=2.775, dk=5.5, dh=3.4),
      "M4": dict(d=4.0, P=0.7, d2=3.545, d3=3.141, As=8.78, Ds_min=3.838, En_max=3.663, dk=7.0, dh=4.5)}   # as FEA3D F4 (AS RECALLED there)
GRADE = {"A4-70": (interp("SS-A4-70", "Fty", 20), interp("SS-A4-70", "Ftu", 20)), "A4-80": (interp("SS-A4-80", "Fty", 20), interp("SS-A4-80", "Ftu", 20))}
K = IN["K_nut"]
MU = IN["mu_slip"]


def kT(T):
    return interp("SS316L", "Fty", max(T, 20.0)) / interp("SS316L", "Fty", 20.0)


def strip_area(th, L_e):
    n = 1.0 / th["P"]
    return math.pi * n * L_e * th["Ds_min"] * (1.0 / (2.0 * n) + 0.57735 * (th["Ds_min"] - th["En_max"]))


def preload(size, grade, T_Nm, scatter, dk=None):
    th = TH[size]
    Rp = GRADE[grade][0]
    F = T_Nm * 1e3 / (K * th["d"])
    Db = 0.5 * ((dk or th["dk"]) + th["dh"])
    a = th["P"] / (2 * math.pi)
    b = th["d2"] / (2 * math.cos(math.radians(30.0)))
    mu = (K * th["d"] - a) / (b + 0.5 * Db)
    ds = 0.5 * (th["d2"] + th["d3"])
    Wp = math.pi * ds ** 3 / 16.0

    def nu(Fp):
        s, t = Fp / th["As"], Fp * (a + mu * b) / Wp
        return math.sqrt(s * s + 3 * t * t) / Rp
    return {"T_Nm": T_Nm, "scatter": scatter, "F_nom_N": F, "F_min_N": (1 - scatter) * F, "F_max_N": (1 + scatter) * F,
            "nu_nom": nu(F), "nu_max": nu((1 + scatter) * F)}


def margins(size, grade, pre, P, V, SFy, SFu, T_bolt, T_host, L_e, host="AL6061-T6"):
    th = TH[size]
    Rp, Rm = GRADE[grade]
    k = kT(T_bolt)
    out = {}
    Fsu_host = MAT[host]["Fsu_over_Ftu"]["v"] * interp(host, "Ftu", T_host)
    for tag, phi in (("", None), ("_phi02", 0.2)):
        loss = SFy * P if phi is None else (1 - phi) * SFy * P
        add_y = SFy * P if phi is None else phi * SFy * P
        add_u = SFu * P if phi is None else phi * SFu * P
        Fb_u = max(pre["F_max_N"] + add_u, SFu * P)
        out["sep" + tag] = pre["F_min_N"] / loss - 1 if loss > 0 else None
        out["slip" + tag] = (MU * max(pre["F_min_N"] - loss, 0.0) / (SFy * V) - 1) if V > 1e-9 else None
        out["bolt_y" + tag] = k * Rp * th["As"] / (pre["F_max_N"] + add_y) - 1
        out["bolt_u" + tag] = k * Rm * th["As"] / Fb_u - 1
        out["thread_host" + tag] = Fsu_host * strip_area(th, L_e) / Fb_u - 1
    out = {kk: (round(v, 3) if v is not None else None) for kk, v in out.items()}
    out["k_T"] = round(k, 3)
    out["hot_preload_utilisation"] = round(pre["F_max_N"] / (k * Rp * th["As"]), 3)
    return out


def mins(m, phi=False):
    v = {kk: x for kk, x in m.items() if x is not None and not kk.startswith(("k_T", "hot")) and kk.endswith("_phi02") == phi}
    kmin = min(v, key=v.get)
    return v[kmin], kmin


def accel_cases(z_mm, rxy_mm):
    z, r = abs(z_mm) / 1e3, rxy_mm / 1e3
    return [("LC1 flight", 1.5, 2.0, IN["A_LAT_FL_g"] + IN["ALPHA_FL_rad_s2"] * z / G0, IN["A_AX_FL_g"] + IN["ALPHA_FL_rad_s2"] * r / G0),
            ("LC3 touchdown (5.43 g SIM)", 1.5, 2.0, IN["A_LAT_TD_g"] + IN["ALPHA_TD_rad_s2"] * z / G0, IN["A_AX_TD_g"] + IN["ALPHA_TD_rad_s2"] * r / G0),
            ("LC3 hard-landing envelope (10 g)", 1.5, 2.0, IN["A_LAT_TD_g"] + IN["ALPHA_TD_rad_s2"] * z / G0, IN["A_AX_ENV_g"] + IN["ALPHA_TD_rad_s2"] * r / G0),
            ("FA-1 spike (equipment bound)", 1.0, 1.0, IN["A_LAT_FL_g"], IN["A_AX_FA1_g"]),
            ("transport 3 g any axis", 1.5, 2.0, IN["A_TRANSPORT_g"], IN["A_TRANSPORT_g"])]


out = {"id": "joints_v352", "version": "v1", "date": "2026-10-19", "owner": "mechanical", "method": __doc__.strip(),
       "source_f4": {"path": "04-fea/assembly3d/results/f4_secondary.json",
                     "sha256_16": hashlib.sha256(open("/home/claude/work/shared-fallback/engine/04-fea/assembly3d/results/f4_secondary.json", "rb").read()).hexdigest()[:16]},
       "joints": {}}
# ---------------------------------------------------------------------------------------------------- J-FD01
JF = F4["joints"]["J-FD01"]
mFD, cg = JF["mass_supported_kg"], JF["cg_mm"]
P_MAN = IN["P_MAN_MPa"]
A_R7 = JF["pressure"]["A_bound_mm2"]
A_g99 = math.pi / 4 * 9.9 ** 2                      # CAD FD-01 face groove OD 9.9 (parts_inlet: groove 6.2 / 9.9 x 1.30): seal pressure area DERIVED
he = JF["hose_engine_end_at_stop"]
T_hot = IN["T_headtop_soak_C"]


def fd01_cases(layout, A):
    """Per-screw external loads.  layout 'v351': 2 screws 22.4 mm apart, P = p A / 2 + m a g (+ hose F + M / s) as FEA3D.
    layout 'v352': 3 screws (2 lower at zb+5, 1 upper at zb+24; seal at zb+14): pressure shared by the lever rule (upper 9/19, each lower 5/19);
    inertia and hose wrench put in full on EACH screw (bounding, as FEA3D does for 2)."""
    res = []
    for cname, SFy, SFu, alat, aax in accel_cases(cg[2], math.hypot(cg[0], cg[1])):
        a = math.hypot(alat, aax)
        if layout == "v351":
            shares, s = [("each", 0.5)], 22.4
        else:
            shares, s = [("upper", 9.0 / 19.0), ("lower", 5.0 / 19.0)], 19.0
        for who, sh in shares:
            P = P_MAN * A * sh + mFD * a * G0
            V = mFD * a * G0
            if cname.startswith("LC3"):
                P += he["F_N"] + he["M_Nm"] * 1e3 / s
                V += he["F_N"]
            res.append((cname, who, SFy, SFu, P, V))
    return res


variants = {
    "v351 check: 2x M3 A4-70, 1.0 N m, +/-25 %, L_e 5.5": ("v351", "M3", "A4-70", 1.0, 0.25, {"each": 5.5}),
    "v352: 3x M4 DIN 7984 A4-80, 1.8 N m, +/-25 %, L_e upper 5.5 / lower 8.5": ("v352", "M4", "A4-80", 1.8, 0.25, {"upper": 5.5, "lower": 8.5}),
    "v352 sens: 3x M4 A4-80, 1.5 N m, +/-25 %": ("v352", "M4", "A4-80", 1.5, 0.25, {"upper": 5.5, "lower": 8.5}),
    "v352 sens: 3x M4 A4-80, 2.1 N m, +/-25 %": ("v352", "M4", "A4-80", 2.1, 0.25, {"upper": 5.5, "lower": 8.5}),
    "v352 sens: 3x M4 A4-70, 1.8 N m, +/-25 %": ("v352", "M4", "A4-70", 1.8, 0.25, {"upper": 5.5, "lower": 8.5}),
    "alt (not chosen): 2x M3 A4-80, 0.7 N m, +/-15 % (screw path through the riser socket NOT fixed)": ("v351", "M3", "A4-80", 0.7, 0.15, {"each": 5.5}),
}
jo = {"geometry_finding": ("v3.5.1 J-FD01 lower M3 screw (z zb+2.8 = 144.31, y 0) runs through the FD-01 riser socket and the FD-03 riser tube "
                           "(probe v352/jfd/probe_fd01.py: FD-03 material at r 33.25-34.25 and 42.0-43.0 on the screw axis) - the joint cannot be "
                           "assembled as modelled; this is the 'grip 3.0' of the hole census.  v3.5.2 relocates the screws."),
      "mass_supported_kg": mFD, "cg_mm": cg, "T_soak_C": T_hot, "areas_mm2": {"R7_bounding_FEA3D": round(A_R7, 1), "groove_OD_9.9_CAD": round(A_g99, 1)},
      "variants": {}}
for name, (lay, size, grade, T, sc, Le) in variants.items():
    pre = preload(size, grade, T, sc, dk=(5.5 if size == "M3" else 7.0))
    rec = {"preload": {k: round(v, 3) for k, v in pre.items()}, "by_area": {}}
    for at, A in (("R7_bounding", A_R7), ("groove_OD_9.9", A_g99)):
        worst = {"bounding": (9, None), "phi02": (9, None)}
        rows = []
        for cname, who, SFy, SFu, P, V in fd01_cases(lay, A):
            m = margins(size, grade, pre, P, V, SFy, SFu, T_hot, T_hot, Le[who])
            mb, kb = mins(m, False)
            mp, kp = mins(m, True)
            rows.append({"case": cname, "screw": who, "P_N": round(P, 1), "V_N": round(V, 1), "MS_min_bounding": [round(mb, 3), kb], "MS_min_phi02": [round(mp, 3), kp], **m})
            if mb < worst["bounding"][0]:
                worst["bounding"] = (round(mb, 3), f"{cname} / {who} / {kb}")
            if mp < worst["phi02"][0]:
                worst["phi02"] = (round(mp, 3), f"{cname} / {who} / {kp}")
        rec["by_area"][at] = {"worst": worst, "rows": rows}
    jo["variants"][name] = rec
out["joints"]["J-FD01"] = jo
# ---------------------------------------------------------------------------------------------------- J-FD09
J9 = F4["joints"]["J-FD09"]
jo9 = {"basis": J9["hardware"], "variants": {}}
v9 = {"v351 check: M4 A4-70 2.05 N m +/-25 %": ("A4-70", 2.05, 0.25),
      "v352: M4 ISO 4762 A4-80 1.8 N m +/-25 %": ("A4-80", 1.8, 0.25),
      "v352 sens: M4 A4-70 1.8 N m +/-25 %": ("A4-70", 1.8, 0.25),
      "v352 sens: M4 A4-80 1.5 N m +/-25 %": ("A4-80", 1.5, 0.25)}
for name, (grade, T, sc) in v9.items():
    pre = preload("M4", grade, T, sc)
    rec = {"preload": {k: round(v, 3) for k, v in pre.items()}, "by_EI": {}}
    for EI in (0.184, 0.5):
        worst = {"bounding": (9, None), "phi02": (9, None)}
        for c in J9["cases"]:
            if abs(c["hose_EI_Nm2"] - EI) > 1e-6:
                continue
            m = margins("M4", grade, pre, c["P_N"], c["V_N"], c["SF"][0], c["SF"][1], c["T_bolt_C"], c["T_host_C"], 6.0)
            mb, kb = mins(m, False)
            mp, kp = mins(m, True)
            if mb < worst["bounding"][0]:
                worst["bounding"] = (round(mb, 3), f"{c['case']} / {kb}")
            if mp < worst["phi02"][0]:
                worst["phi02"] = (round(mp, 3), f"{c['case']} / {kp}")
        rec["by_EI"][str(EI)] = worst
    jo9["variants"][name] = rec
out["joints"]["J-FD09"] = jo9
s = json.dumps(out, indent=1)
open("/home/claude/work/mechanical/v352/jfd/joints_v352_v1.json", "w").write(s)
for J in ("J-FD01", "J-FD09"):
    for name, rec in out["joints"][J]["variants"].items():
        pr = rec["preload"]
        if J == "J-FD01":
            w = {a: rec["by_area"][a]["worst"] for a in rec["by_area"]}
        else:
            w = rec["by_EI"]
        print(J, "|", name, "| F_nom", round(pr["F_nom_N"]), "nu", round(pr["nu_nom"], 3), round(pr["nu_max"], 3), "|", json.dumps(w))
print("sha256/16", hashlib.sha256(s.encode()).hexdigest()[:16])
