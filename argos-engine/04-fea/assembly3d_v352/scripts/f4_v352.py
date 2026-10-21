#!/usr/bin/env python3
"""F4 secondary-joint re-check on CAD v3.5.2 (fea3d 2026-10-20, lead v3.5.2 re-check item 3): J-FD01 and J-FD09 with the v3.5.2 hardware.

Same formulas as f4_secondary.py (FEA3D F4 v1, CAD v3.5.1; Mechanical re-implemented them in 04-fea/v352/joints_v352_v1.json):
  preload F = T / (K d), K 0.20 (ASSUMED, hardware rule), +/-25 % scatter (ASSUMED); bounding Phi 0 (separation, slip) / Phi 1 (screw,
  host thread) and the Phi 0.2 variant; hot screw strength k_T = SS316L Fty(T)/Fty(20 C) proxy (ASSUMED, TO-VERIFY); SF per 188 (9);
  host thread strip area FED-STD-H28/2 form (AS RECALLED); limit accelerations gnc.json v3.1 (SIM) + 10 g envelope + 3 g transport.
New in v3.5.2: per-joint grade (A4-80: Rp0.2 600 / Rm 800 MPa, ISO 3506-1 minima, engmat SS-A4-80, LITERATURE), J-FD01 3-screw pattern.

J-FD01 (HW-103 2x M4x20 DIN 7984 A4-80, lower pair y +/-8.5 z 146.51, engagement 8.5; HW-103B 1x M4x16, upper y 0 z 165.51, engagement 5.5;
1.8 N m M-T1; TC-02 6061 host at the soak-back head-top temperature).  Two load distributions:
  (a) 'F4 bounding' (= Mechanical joints_v352_v1): cap force (P_MAN x A, R7 bounding or groove OD 9.9) split by the elastic bolt group
      about the pattern centroid (rigid block, joint plane in contact), inertia force and hose wrench F + M / s (s 19.0 mm) added in full
      to every screw (as the v3.5.1 F4);
  (b) 'elastic bolt group, vector loads' (independent check): the same cap force; inertia m a applied AT the supported-mass CG and the
      hose engine-end wrench (hose_end_reactions_v341_v1, 36 stop-axis rows, F and M vectors) applied AT the hose engine end, both
      reduced to the pattern centroid; screw tension P_i = N/3 + M_z dy_i / sum dy^2 - M_y dz_i / sum dz^2, shear V_i = |F_t| / 3 +
      |M_n| r_i / sum r^2 (bounding sum); lateral acceleration swept over 24 directions x 2 axial signs, every hose row combined with every
      inertia direction (bounding: the stop direction and the touchdown acceleration direction are not correlated here).
  The whole hose wrench and all listed masses are taken by the 3 screws (FD-04 riser clamp on the case not credited: bounding).
J-FD09 (HW-127 2x M4x12 ISO 4762 A4-80, 1.8 N m, into GM-09 with helicoil): v3.5.1 F4 loads and geometry (prying lever 5 mm), EI 0.184 / 0.5.
usage: f4_v352.py   -> results/v352/f4_v352.json, results/v352/tables/f4_v352.md
"""
import json, math, sys, hashlib
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import asm3d as A3  # noqa: E402

ROOT = Path("/home/claude/work/fea3d")
OUT = ROOT / "results" / "v352"
HUB = Path("/home/claude/work/shared-fallback/engine")
SRC = {"hardware": HUB / "03-cad/v3.5.2/data/hardware_v352.json", "massprops": HUB / "03-cad/v3.5.2/massprops_v3.5.2.json",
       "gnc": HUB / "interfaces/gnc.json", "hose": HUB / "03-cad/calcs/hose_end_reactions_v341_v1.json",
       "net_v2c": HUB / "04-fea/thermal/networks/servo_mount_net_v2c.json", "net_v2d": HUB / "04-fea/thermal/networks/servo_mount_net_v2d.json",
       "mech_joints_v352": HUB / "04-fea/v352/joints_v352_v1.json"}
G0 = 9.80665
MAT = A3.engmat.MATERIALS


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def interp(mat, key, T_C):
    d = MAT[mat][key]
    return float(np.interp(T_C, d["T_C"], d["v"])) / 1e6 if "T_C" in d else d["v"] / 1e6


gnc = json.loads(SRC["gnc"].read_text())
DLL = gnc["design_limit_loads"]
A_LAT_TD, A_AX_TD = DLL["lateral_accel_at_pivot_touchdown_g"]["v"], DLL["axial_accel_touchdown_g"]["v"]
A_AX_ENV, ALPHA_TD = DLL["axial_accel_landing_shock_envelope_g"]["v"], DLL["body_angular_accel_touchdown_rad_s2"]["v"]
A_AX_FL, A_LAT_FL, ALPHA_FL = DLL["axial_accel_flight_g"]["v"], DLL["lateral_accel_at_pivot_flight_g"]["v"], DLL["body_angular_accel_flight_rad_s2"]["v"]
A_TRANSPORT = DLL["transport_handling_g"]["v"]
M_DRY = gnc["reference_vehicle"]["dry_mass_kg"]["v"]
A_AX_FA1 = 2.0 * 1800.0 / (M_DRY * G0)
P_MAN = 7.0
mp = json.loads(SRC["massprops"].read_text())
ROWS = mp["ledger_mid"]
hw = json.loads(SRC["hardware"].read_text())
HWL = {r["id"]: r for r in hw["lines"]}
hose_all = json.loads(SRC["hose"].read_text())
hose = hose_all["reactions_8deg"]
X_HOSE_ENG = np.asarray(hose_all["nodes_m"]["engine_end"]) * 1e3          # mm, engine frame (pivot origin)
net = {k: json.loads(SRC[k].read_text()) for k in ("net_v2c", "net_v2d")}
T_HEADTOP_SOAK = max(n["runs"][0]["boundary_peaks_C"]["head_top_r20_26_mean"] for n in net.values())
TH = {"M4": dict(d=4.0, P=0.7, d2=3.545, d3=3.141, As=8.78, Ds_min=3.838, En_max=3.663, dk=7.0, dh=4.5)}
K_NUT, SCATTER, MU_SLIP, PHI_TYP = hw["rules"]["K_nut"], 0.25, 0.20, 0.2
GRADE = {"A4-70": "SS-A4-70", "A4-80": "SS-A4-80"}


def strength(grade):
    m = GRADE[grade]
    return interp(m, "Fty", 20.0), interp(m, "Ftu", 20.0), MAT[m]["Fsu_over_Ftu"]["v"]


def k_T_bolt(T_C):
    return interp("SS316L", "Fty", max(T_C, 20.0)) / interp("SS316L", "Fty", 20.0)


def strip_area(th, L_e):
    n = 1.0 / th["P"]
    return math.pi * n * L_e * th["Ds_min"] * (1.0 / (2.0 * n) + 0.57735 * (th["Ds_min"] - th["En_max"]))


def preload(size, T_Nm, grade, dk=None):
    th = TH[size]
    rp, _, _ = strength(grade)
    F = T_Nm * 1e3 / (K_NUT * th["d"])
    Db = 0.5 * ((dk or th["dk"]) + th["dh"])
    a = th["P"] / (2 * math.pi)
    b = th["d2"] / (2 * math.cos(math.radians(30.0)))
    mu = (K_NUT * th["d"] - a) / (b + 0.5 * Db)
    ds = 0.5 * (th["d2"] + th["d3"])
    Wp = math.pi * ds ** 3 / 16.0

    def nu(Fp):
        s, t = Fp / th["As"], Fp * (a + mu * b) / Wp
        return math.sqrt(s * s + 3 * t * t) / rp
    return {"T_Nm": T_Nm, "F_nom_N": F, "F_min_N": (1 - SCATTER) * F, "F_max_N": (1 + SCATTER) * F, "mu_implied": mu,
            "nu_assembly_nom": nu(F), "nu_assembly_max": nu((1 + SCATTER) * F)}


def ms(cap, dem):
    return None if dem <= 1e-9 else cap / dem - 1.0


def margins(j, P, V, SFy, SFu, T_bolt_C, T_host_C, L_e):
    th, pl = TH[j["size"]], j["pre"]
    rp, rm, fsu = strength(j["grade"])
    kT = k_T_bolt(T_bolt_C)
    out = {"P_N": round(P, 2), "V_N": round(V, 2), "SF": [SFy, SFu], "T_bolt_C": round(T_bolt_C, 1), "T_host_C": round(T_host_C, 1),
           "k_T_bolt": round(kT, 3), "L_e_mm": L_e, "hot_preload_utilisation": round(pl["F_max_N"] / (kT * rp * th["As"]), 3)}
    Fsu_host = MAT[j["host"]]["Fsu_over_Ftu"]["v"] * interp(j["host"], "Ftu", T_host_C)
    for tag, phi in (("", None), ("_phi02", PHI_TYP)):
        loss = SFy * P if phi is None else (1.0 - phi) * SFy * P
        add_y = SFy * P if phi is None else phi * SFy * P
        add_u = SFu * P if phi is None else phi * SFu * P
        Fb_u = max(pl["F_max_N"] + add_u, SFu * P)
        out["MS_sep" + tag] = ms(pl["F_min_N"], loss)
        out["MS_slip" + tag] = None if V <= 1e-9 else MU_SLIP * max(pl["F_min_N"] - loss, 0.0) / (SFy * V) - 1.0
        out["MS_bolt_y" + tag] = ms(kT * rp * th["As"], pl["F_max_N"] + add_y)
        out["MS_bolt_u" + tag] = ms(kT * rm * th["As"], Fb_u)
        out["MS_thread_host" + tag] = ms(Fsu_host * strip_area(th, L_e), Fb_u)
    out["MS_bolt_shear"] = ms(kT * fsu * rm * math.pi / 4 * th["d3"] ** 2, SFu * V)
    for k in list(out):
        if k.startswith("MS_") and out[k] is not None:
            out[k] = round(out[k], 3)
    return out


def msmin(m, phi=False):
    v = {k: x for k, x in m.items() if k.startswith("MS_") and x is not None and (k.endswith("_phi02") == phi or k == "MS_bolt_shear")}
    k = min(v, key=v.get)
    return v[k], k


def rows_sel(pred):
    sel = [r for r in ROWS if pred(r["pn"].replace("ENG-", ""), r)]
    m = sum(r["m_kg"] for r in sel)
    cg = sum(r["m_kg"] * np.asarray(r["cg_mm"]) for r in sel) / m
    return m, cg, sorted({r["pn"].replace("ENG-", "") for r in sel})


def accel_cases(z_mm, rxy_mm):
    z, r = abs(z_mm) / 1e3, rxy_mm / 1e3
    return [("LC1 flight", 1.5, 2.0, A_LAT_FL + ALPHA_FL * z / G0, A_AX_FL + ALPHA_FL * r / G0),
            ("LC3 touchdown (5.43 g SIM)", 1.5, 2.0, A_LAT_TD + ALPHA_TD * z / G0, A_AX_TD + ALPHA_TD * r / G0),
            ("LC3 hard-landing envelope (10 g)", 1.5, 2.0, A_LAT_TD + ALPHA_TD * z / G0, A_AX_ENV + ALPHA_TD * r / G0),
            ("FA-1 spike (equipment bound)", 1.0, 1.0, A_LAT_FL, A_AX_FA1),
            ("transport 3 g any axis", 1.5, 2.0, A_TRANSPORT, A_TRANSPORT)]


RES = {"id": "f4_v352", "version": "v1", "date": "2026-10-20", "owner": "fea3d", "cad": "v3.5.2",
       "doc": __doc__.split("usage:")[0].strip(), "sources": {k: {"path": str(v.relative_to(HUB)), "sha256_16": sha16(v)} for k, v in SRC.items()},
       "inputs": {"K_nut": K_NUT, "scatter": SCATTER, "mu_slip": MU_SLIP, "Phi_typ": PHI_TYP, "T_headtop_soak_C": T_HEADTOP_SOAK, "P_MAN_MPa": P_MAN,
                  "A_AX_FA1_g": round(A_AX_FA1, 3), "hose_engine_end_mm": X_HOSE_ENG.round(2).tolist(),
                  "strength_MPa": {g: dict(zip(("Rp02", "Rm", "Fsu_over_Ftu"), strength(g))) for g in GRADE}}, "joints": {}}

# ============================================================================================ J-FD01 (3x M4 A4-80)
h103, h103b = HWL["HW-103"], HWL["HW-103B"]
assert h103["torque_Nm"] == h103b["torque_Nm"] and h103["grade"] == h103b["grade"] == "A4-80"
jfd = {"size": "M4", "grade": h103["grade"], "host": "AL6061-T6", "T_Nm": h103["torque_Nm"]}
jfd["pre"] = preload("M4", jfd["T_Nm"], jfd["grade"], dk=7.0)
SCREWS = [("lower +y", 8.5, 146.51, 8.5), ("lower -y", -8.5, 146.51, 8.5), ("upper", 0.0, 165.51, 5.5)]   # (name, y, z, L_e) CAD v3.5.2 tap axes
X_FL = -29.5
yc = np.mean([s[1] for s in SCREWS]); zc = np.mean([s[2] for s in SCREWS])
dy = np.array([s[1] - yc for s in SCREWS]); dz = np.array([s[2] - zc for s in SCREWS])
Syy, Szz = float((dy ** 2).sum()), float((dz ** 2).sum())
rr = np.hypot(dy, dz); Srr = float((rr ** 2).sum())
C_PAT = np.array([X_FL, yc, zc])
Z_PORT = 155.513                                   # TC-02 filter bore R7 axis (x), CAD v3.5.2 mesh entity (DERIVED)
A_bound, A_seal = math.pi * 7.0 ** 2, math.pi / 4 * 9.9 ** 2      # R7 bounding (F1 PM cap) / groove OD 9.9 (Mechanical CAD value)
mFD, cgFD, pnFD = rows_sel(lambda pn, r: r["group"] == "engine" and pn in ("FD-01", "BL-01", "BL-02", "BL-03A", "BL-03E", "BL-04A", "BL-04",
                                                                              "FD-03", "FD-05", "FD-07A", "FD-07"))
n_out = np.array([-1.0, 0.0, 0.0])                 # joint normal: tension = force on FD-01 along -x (away from the TC-02 flat)


def pattern(Fv, Mc):
    """Fv (N) and moment about the pattern centroid Mc (N mm) acting ON FD-01 -> per-screw tension P_i, shear V_i (elastic bolt group)."""
    N = float(Fv @ n_out)
    # screw forces -P_i n on FD-01 at dr_i = (0, dy, dz): moment sum = -(0, -sum P dz, sum P dy); equilibrium -> sum P dz = -M_y, sum P dy = M_z
    P = N / 3.0 + Mc[2] * dy / Syy - Mc[1] * dz / Szz
    Ft = math.hypot(Fv[1], Fv[2])
    V = Ft / 3.0 + abs(Mc[0]) * rr / Srr
    return P, V


fd_rows = {"a_F4_bounding": [], "b_bolt_group_vector": []}
for area_tag, A in (("R7 bounding", A_bound), ("groove OD 9.9", A_seal)):
    Fcap = P_MAN * A
    Pcap, _ = pattern(Fcap * n_out, np.cross(np.array([X_FL, 0.0, Z_PORT]) - C_PAT, Fcap * n_out))
    for cname, SFy, SFu, alat, aax in accel_cases(cgFD[2], math.hypot(cgFD[0], cgFD[1])):
        hose_on = cname.startswith("LC3")          # as the v3.5.1 F4 / Mechanical: hose wrench at the 8 deg stop in the LC3 cases
        a = math.hypot(alat, aax)
        # (a) F4 bounding (Mechanical joints_v352_v1 reproduction)
        add = mFD * a * G0 + ((hose["0.184"]["max"]["F_eng"]["norm"] + hose["0.184"]["max"]["M_eng"]["norm"] * 1e3 / 19.0) if hose_on else 0.0)
        Vb = mFD * a * G0 + (hose["0.184"]["max"]["F_eng"]["norm"] if hose_on else 0.0)
        for i, (nm, y_, z_, Le) in enumerate(SCREWS):
            m = margins(jfd, Pcap[i] + add, Vb, SFy, SFu, T_HEADTOP_SOAK, T_HEADTOP_SOAK, Le)
            m.update({"case": cname, "area": area_tag, "screw": nm, "P_cap_N": round(float(Pcap[i]), 1)})
            fd_rows["a_F4_bounding"].append(m)
        # (b) vector loads: inertia at the CG, hose wrench at the hose engine end, both to the centroid
        hrows = hose["0.184"]["rows"] if hose_on else [None]
        worst = [None] * 3
        for ph in range(0, 360, 15):
            for sg in (1.0, -1.0):
                acc = np.array([alat * math.cos(math.radians(ph)), alat * math.sin(math.radians(ph)), sg * aax]) * G0   # m/s2 (engine frame)
                Fi = -mFD * acc                                      # inertial force on the supported masses (N)
                Mi = np.cross(cgFD - C_PAT, Fi)
                for hr in hrows:
                    Fv, Mc = Fcap * n_out + Fi, np.cross(np.array([X_FL, 0.0, Z_PORT]) - C_PAT, Fcap * n_out) + Mi
                    if hr is not None:
                        for sgn_h in (1.0, -1.0):            # the 36 rows cover the axis directions over 360 deg; both senses kept
                            Fh = sgn_h * np.asarray(hr["F_eng_N"]); Mh = sgn_h * np.asarray(hr["M_eng_Nm"]) * 1e3
                            P, V = pattern(Fv + Fh, Mc + Mh + np.cross(X_HOSE_ENG - C_PAT, Fh))
                            for i in range(3):
                                if worst[i] is None or P[i] > worst[i][0] or (abs(P[i] - worst[i][0]) < 1e-9 and V[i] > worst[i][1]):
                                    worst[i] = (float(P[i]), float(V[i]), ph, sg, hr["axis_az_deg"], sgn_h)
                    else:
                        P, V = pattern(Fv, Mc)
                        for i in range(3):
                            if worst[i] is None or P[i] > worst[i][0]:
                                worst[i] = (float(P[i]), float(V[i]), ph, sg, None, None)
        for i, (nm, y_, z_, Le) in enumerate(SCREWS):
            Pw, Vw, ph, sg, haz, hs = worst[i]
            # shear at the max-tension combination plus the bounding max shear over the sweep is not needed: slip uses V at that combination
            m = margins(jfd, Pw, Vw, SFy, SFu, T_HEADTOP_SOAK, T_HEADTOP_SOAK, Le)
            m.update({"case": cname, "area": area_tag, "screw": nm, "lat_dir_deg": ph, "ax_sign": sg, "hose_axis_az_deg": haz, "hose_sense": hs})
            fd_rows["b_bolt_group_vector"].append(m)


def worst_of(rows, phi=False):
    w = min(rows, key=lambda r: msmin(r, phi)[0])
    v, k = msmin(w, phi)
    return {"MS": v, "criterion": k, "case": w["case"], "area": w["area"], "screw": w["screw"], "P_N": w["P_N"], "V_N": w["V_N"]}


mech = json.loads(SRC["mech_joints_v352"].read_text())
mv = mech["joints"]["J-FD01"]["variants"]["v352: 3x M4 DIN 7984 A4-80, 1.8 N m, +/-25 %, L_e upper 5.5 / lower 8.5"]
RES["joints"]["J-FD01"] = {
    "hardware": "HW-103 2x M4x20 DIN 7984 A4-80 (lower, y +/-8.5, z 146.51, engagement 8.5) + HW-103B 1x M4x16 (upper, y 0, z 165.51, engagement 5.5), "
                "1.8 N m M-T1, into the TC-02 flat x -29.5 (hardware_v352.json)",
    "preload": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in jfd["pre"].items()},
    "pattern": {"centroid_mm": C_PAT.round(3).tolist(), "sum_dy2": Syy, "sum_dz2": round(Szz, 3), "port_axis_z_mm": Z_PORT,
                "cap_share_upper_lower": [round(float(v), 4) for v in pattern(n_out, np.cross(np.array([X_FL, 0.0, Z_PORT]) - C_PAT, n_out))[0]]},
    "mass_supported_kg": round(mFD, 5), "cg_mm": cgFD.round(2).tolist(), "items": pnFD, "T_host_and_screw_C": T_HEADTOP_SOAK,
    "worst": {"a_F4_bounding": {"bounding": worst_of(fd_rows["a_F4_bounding"]), "phi02": worst_of(fd_rows["a_F4_bounding"], True)},
              "b_bolt_group_vector": {"bounding": worst_of(fd_rows["b_bolt_group_vector"]), "phi02": worst_of(fd_rows["b_bolt_group_vector"], True)}},
    "mechanical_joints_v352_v1": mv["by_area"]["R7_bounding"]["worst"], "rows": fd_rows}

# ============================================================================================ J-FD09 (2x M4 A4-80 into GM-09)
h127 = HWL["HW-127"]
j9 = {"size": "M4", "grade": h127["grade"], "host": "AL6061-T6", "T_Nm": h127["torque_Nm"]}
j9["pre"] = preload("M4", j9["T_Nm"], j9["grade"])
m9, cg9, pn9 = rows_sel(lambda pn, r: r["group"] == "fixed" and pn in ("FD-09", "FD-07B", "FD-07"))
Z_GM09_TOP, H_SLEEVE, E_EDGE = 32.0, 42.0, 5.0
c9 = []
for EI in ("0.184", "0.5"):
    hf = hose[EI]["max"]
    for cname, SFy, SFu, alat, aax in accel_cases(cg9[2], math.hypot(cg9[0], cg9[1])):
        Fi = m9 * math.hypot(alat, aax) * G0
        Fh, Mh = (hf["F_fix"]["norm"], hf["M_fix"]["norm"] * 1e3) if cname.startswith(("LC3", "LC1")) else (0.0, 0.0)
        F = Fh + Fi
        M = Fh * H_SLEEVE + Mh + Fi * (cg9[2] - Z_GM09_TOP)
        P, V = F / 2.0 + M / (2.0 * E_EDGE), F / 2.0
        m = margins(j9, P, V, SFy, SFu, 60.0, 60.0, 6.0)
        m.update({"case": cname, "area": f"EI {EI}", "screw": "each", "hose_EI_Nm2": float(EI), "F_N": round(F, 2), "M_Nmm": round(M, 1)})
        c9.append(m)
m9v = mech["joints"]["J-FD09"]["variants"]["v352: M4 ISO 4762 A4-80 1.8 N m +/-25 %"]
RES["joints"]["J-FD09"] = {"hardware": "HW-127 2x M4x12 ISO 4762 A4-80, 1.8 N m M-T1, into GM-09 with helicoil 1.5 D (thread check as a direct M4 tap in 6061, 6.0 mm: conservative)",
                           "preload": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in j9["pre"].items()},
                           "mass_kg": round(m9, 5), "cg_mm": cg9.round(2).tolist(), "items": pn9, "temperature_C": 60.0,
                           "worst": {EI: {"bounding": worst_of([r for r in c9 if r["area"] == f"EI {EI}"]),
                                          "phi02": worst_of([r for r in c9 if r["area"] == f"EI {EI}"], True)} for EI in ("0.184", "0.5")},
                           "mechanical_joints_v352_v1": m9v.get("worst", m9v.get("by_EI")), "rows": c9}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "f4_v352.json").write_text(json.dumps(RES, indent=1, default=float))
L = ["# F4 v3.5.2 re-check: J-FD01 and J-FD09 (fea3d 2026-10-20; DERIVED hand calcs on the FEA3D F4 formulas)", "",
     f"Preload K {K_NUT} +/-25 % (ASSUMED), mu {MU_SLIP} (ASSUMED); A4-80 Rp0.2 600 / Rm 800 MPa (ISO 3506-1 minima, LITERATURE); hot factor SS316L proxy (ASSUMED).", "",
     "| joint | distribution | MS min bounding (criterion; case / area / screw) | MS min Phi 0.2 (criterion) | Mechanical joints_v352_v1 (bounding / Phi 0.2) |", "|---|---|---|---|---|"]
for tag in ("a_F4_bounding", "b_bolt_group_vector"):
    w = RES["joints"]["J-FD01"]["worst"][tag]
    mvw = RES["joints"]["J-FD01"]["mechanical_joints_v352_v1"]
    L.append(f"| J-FD01 3x M4 A4-80 1.8 N m | {tag} | {w['bounding']['MS']:+.3f} ({w['bounding']['criterion'][3:]}; {w['bounding']['case']} / {w['bounding']['area']} / {w['bounding']['screw']}; P {w['bounding']['P_N']:.1f} N) | "
             f"{w['phi02']['MS']:+.3f} ({w['phi02']['criterion'][3:]}) | {mvw['bounding'][0]:+.3f} / {mvw['phi02'][0]:+.3f} |")
for EI in ("0.184", "0.5"):
    w = RES["joints"]["J-FD09"]["worst"][EI]
    mw = RES["joints"]["J-FD09"]["mechanical_joints_v352_v1"][EI]
    L.append(f"| J-FD09 2x M4 A4-80 1.8 N m | EI {EI} | {w['bounding']['MS']:+.3f} ({w['bounding']['criterion'][3:]}; {w['bounding']['case']}; P {w['bounding']['P_N']:.1f} N) | "
             f"{w['phi02']['MS']:+.3f} ({w['phi02']['criterion'][3:]}) | {mw['bounding'][0]:+.3f} / {mw['phi02'][0]:+.3f} |")
L += ["", f"J-FD01 preload: F_nom {jfd['pre']['F_nom_N']:.0f} N, min {jfd['pre']['F_min_N']:.0f}, max {jfd['pre']['F_max_N']:.0f}; assembly nu {jfd['pre']['nu_assembly_nom']:.2f} nominal / {jfd['pre']['nu_assembly_max']:.2f} at +25 %.",
      f"Cap share (elastic bolt group, port axis z {Z_PORT}): upper {RES['joints']['J-FD01']['pattern']['cap_share_upper_lower'][2]:.4f}, each lower {RES['joints']['J-FD01']['pattern']['cap_share_upper_lower'][0]:.4f}.",
      f"Supported mass {mFD:.4f} kg at {cgFD.round(1).tolist()} mm; hose engine end {X_HOSE_ENG.round(1).tolist()} mm (hose_end_reactions_v341_v1, EI 0.184)."]
(OUT / "tables" / "f4_v352.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
