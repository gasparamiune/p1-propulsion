"""REV-GNC-6 v09: the ENG-11 plant (rev4 item [12]) against the 3D FE modal of CAD v3.5.1 (CHANGELOG 221, REPORT-FEA3D 9A),
frequency arithmetic only.  No margin is evaluated here (a margin re-run with the FE inputs is GNC's job).
Imports the staged m2_eng11 v1.1 unchanged for the V5c pose table (S, g), n and the flight-condition engine inertia I_piv,
and reads the FE modal summary, the Electronics J_int estimate, my v05 result and the author's eng11_grid from the hub.
  f = sqrt(K_tot / (I + J_refl)) / 2 pi,  K_tot = 1 / (1/S + 1/(K_s g)),  J_refl = J g   (m2_eng11.Model, 'cons')
FE-structure variant: S(p, a) x [K_FE neutral(a) / S_T centre(a)] (uniform scale over the 9 V5c poses ASSUMED; the FE cone
poses are not posted yet), V5c g, ENG-11 I_piv and J.  Hot E: S x 0.90 / 0.95 (REPORT 9A: 6061 E -5 to -10 %).
Coincidence band: the full-tank rocking frequencies of the failing ENG-07d corners at the nominal bending (24.30 Hz full),
from my v05 part B and the author's grid / sens rows.
DERIVED (from SIM V5c, SIM 3D FE, DERIVED/DATASHEET J_int); K_s, J ASSUMED; not physical approval.
Usage: python -I v09_fe_plant.py <tree> <fe_modal_summary.json> <servo_jint.json> <v05.json> <eng11_grid.json> <eng11_sens.json> <out.json>"""
import hashlib, json, os, re, sys
TREE, FEJ, JIJ, V05J, GRIDJ, SENSJ, OUT = sys.argv[1:8]
sys.path.insert(0, TREE)
sys.path.insert(0, os.path.join(TREE, "scripts"))
import numpy as np  # noqa: E402
import m2_eng11 as E  # noqa: E402


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def r(x, n=4):
    return None if x is None else round(float(x), n)


d5, T, n_m, gchk = E.v5c_table()
conds, meta, src, extra, cchk = E.conditions()
M = E.Model(T, n_m, conds)
AX = ("alpha", "beta")
I = dict(full=meta["full"]["I_piv"], landing=meta["landing"]["I_piv"])
FB = dict(full=meta["full"]["f_bend_Hz"], landing=meta["landing"]["f_bend_Hz"])
fe = json.load(open(FEJ))
FEM = {("beta" if m["dof"] == "r_y" else "alpha"): m for m in fe["engine_mount_modes"] if m["dof"] in ("r_x", "r_y")}
ji = json.load(open(JIJ))["servos"]["SB-2292SG"]["by_voltage"]["7.4"]
JS = dict(J0=0.0, J_LO=E.J_LO, J_C=E.J_C, J_HI=E.J_HI)
out = dict(script="v09_fe_plant (REV-GNC-6)", tag="DERIVED frequency arithmetic; no margins evaluated",
           inputs=dict(m2_eng11=[E.VERSION, sha16(E.__file__)], fe_modal=[FEJ, sha16(FEJ)], servo_jint=[JIJ, sha16(JIJ)],
                       v05=[V05J, sha16(V05J)], grid=[GRIDJ, sha16(GRIDJ)], sens=[SENSJ, sha16(SENSJ)],
                       iface=os.environ.get("GNC_IFACE"), mass_variant=E.MASS_VARIANT, cfg_ballast=extra))

# 1. conventions and inertia
gc = {a: T[("centre", a)]["g"] for a in AX}
out["J_convention"] = dict(
    model="J = servo internal (rotor + gear train) inertia at the servo OUTPUT shaft; J_refl = J g(p, a) added to the engine I_piv",
    n=n_m, n2=n_m * n_m, g_centre=dict((a, r(gc[a], 5)) for a in AX),
    g_range_9poses=dict((a, [r(min(T[(p, a)]["g"] for p in M.poses), 4), r(max(T[(p, a)]["g"] for p in M.poses), 4)]) for a in AX),
    J_values=JS, J_refl_centre=dict((k, dict((a, r(v * gc[a], 5)) for a in AX)) for k, v in JS.items()),
    electronics_SB2292SG_7V4=dict(J_int_central=ji["J_int_central_kgm2"], J_int_range=ji["J_int_range_kgm2"],
                                  engine_side_central=ji["engine_side_central_kgm2"]),
    engine_I_piv=dict(full=r(I["full"], 6), landing=r(I["landing"], 6), m_e_full=r(meta["full"]["m_e"], 4),
                      m_e_landing=r(meta["landing"]["m_e"], 4)))
fe_i = {}
for a in AX:
    m = FEM[a]
    w = 2 * np.pi * m["f_FE_rigid_servo_Hz"]
    g58 = 1.0 / (1.0 / m["K_with_servo_k58_Nm_per_rad"] - 1.0 / m["K_static_pose_model_Nm_per_rad"]) / 58.0
    g174 = 1.0 / (1.0 / m["K_with_servo_k174_Nm_per_rad"] - 1.0 / m["K_static_pose_model_Nm_per_rad"]) / 174.0
    fe_i[a] = dict(I_eff=m["I_eff_kgm2"], I_K_over_w2=r(m["K_static_same_mesh_Nm_per_rad"] / w ** 2, 6),
                   K_pose_model=r(m["K_static_pose_model_Nm_per_rad"], 1), K_same_mesh=r(m["K_static_same_mesh_Nm_per_rad"], 1),
                   g_implied_k58=r(g58, 4), g_implied_k174=r(g174, 4), f_rigid_FE=r(m["f_FE_rigid_servo_Hz"], 3),
                   f_prod_K=r(m["f_scaled_to_pose_model_K_Hz"], 3), f_k58=r(m["f_with_servo_k58_Hz_DERIVED"], 3),
                   f_k174=r(m["f_with_servo_k174_Hz_DERIVED"], 3),
                   I_piv_full_over_I_eff=r(I["full"] / m["I_eff_kgm2"], 4), I_piv_landing_over_I_eff=r(I["landing"] / m["I_eff_kgm2"], 4),
                   lead_check=dict(J_C_g_over_I_eff=r(E.J_C * gc[a] / m["I_eff_kgm2"], 4), I_eff_over_g=r(m["I_eff_kgm2"] / gc[a], 7),
                                   servo_side_total_C=r(I["landing"] / gc[a] + E.J_C, 7),
                                   total_over_FE=r((I["landing"] + E.J_C * gc[a]) / m["I_eff_kgm2"], 4)))
out["fe_inertia_kinematics"] = fe_i

# 2. structure
S_T = {a: T[("centre", a)]["S"]["T"] for a in AX}
STOP = dict(alpha=(6400.0, 8577.0), beta=(3888.0, 6570.0))      # REPORT-FEA3D 9 (a9f7f30055063c8e): 8 stop poses, rigid servo
out["structure"] = {a: dict(V5c_centre_T=S_T[a], V5c_centre_low=T[("centre", a)]["S"]["low"], V5c_centre_high=T[("centre", a)]["S"]["high"],
                            V5c_T_9poses=[min(T[(p, a)]["S"]["T"] for p in M.poses), max(T[(p, a)]["S"]["T"] for p in M.poses)],
                            FE_neutral=fe_i[a]["K_pose_model"], FE_over_V5c_centre=r(fe_i[a]["K_pose_model"] / S_T[a], 4),
                            FE_stop_8poses=STOP[a]) for a in AX}


# 3. like-for-like rocking frequency at J = 0 (the FE leaves out the servo rotor) and with J
def fr(S, Ks, g, Ip, J):
    Kt = 1.0 / (1.0 / S + (0.0 if Ks is None else 1.0 / (Ks * g)))
    return float(np.sqrt(Kt / (Ip + J * g)) / (2 * np.pi))


lfl = {}
for a in AX:
    for Ks in (None, 58.0, 100.0, 130.0, 174.0):
        k = f"{a}|Ks{'rigid' if Ks is None else int(Ks)}"
        lfl[k] = dict(
            ENG11_centre_J0_landing=r(fr(S_T[a], Ks, gc[a], I["landing"], 0.0), 3),
            ENG11_centre_J0_full=r(fr(S_T[a], Ks, gc[a], I["full"], 0.0), 3),
            FEstruct_FEinertia_J0=r(fr(fe_i[a]["K_pose_model"], Ks, gc[a], fe_i[a]["I_eff"], 0.0), 3),
            FEstruct_FE_K_over_w2_J0=r(fr(fe_i[a]["K_pose_model"], Ks, gc[a], fe_i[a]["I_K_over_w2"], 0.0), 3),
            FE_reported=(fe_i[a]["f_prod_K"] if Ks is None else fe_i[a].get(f"f_k{int(Ks)}")),
            ENG11_centre_JC_full=r(fr(S_T[a], Ks, gc[a], I["full"], E.J_C), 3),
            FEstruct_JC_full=r(fr(fe_i[a]["K_pose_model"], Ks, gc[a], I["full"], E.J_C), 3),
            J_factor_full=r(np.sqrt(I["full"] / (I["full"] + E.J_C * gc[a])), 4))
out["like_for_like_centre_Hz"] = lfl

# 4. coincidence band from the failing corners at the nominal bending
fails = []
v05 = json.load(open(V05J))
for k, v in v05["B"].items():
    for s in v.get("first_fails", []):
        mm = re.search(r"\|f([0-9.]+)\|", s)
        if mm and s.startswith("full"):
            fails.append(("v05B", k, float(mm.group(1))))
grid = json.load(open(GRIDJ))
for e in grid["grid"]:
    if not e["pass_6dB"] and "|z0.02|full|" in e["worst"]:
        fails.append(("grid", f"{e['axis']}|Ks{e['K_s']:g}", float(re.search(r"\|f([0-9.]+)", e["worst"]).group(1))))
sens = json.load(open(SENSJ))
for kk, v in sens["result"].items():
    if not kk.endswith("fixed_c1_Q1_-12"):
        continue
    for kk2, vv in v.items():
        w = vv["floor20"]["worst"]
        if not vv["floor20"]["pass_6dB"] and "|z0.02|full|" in w:
            fails.append(("sens", f"{kk.split('|')[0]}|{kk2}", float(re.search(r"\|f([0-9.]+)", w).group(1))))
band = [min(x[2] for x in fails), max(x[2] for x in fails)]
out["coincidence_band_full_Hz"] = dict(band=band, n=len(fails), bending_full=r(FB["full"], 3), bending_landing=r(FB["landing"], 3),
                                       rows=sorted({(x[0], x[1]) for x in fails}))


# 5. window map: full-tank 9-pose rocking range per plant variant, K_s 100-130
def rng(a, Ks, J, sS=1.0, chain="T", kin="cons", Ip=None):
    Ip = I["full"] if Ip is None else Ip
    fs = []
    for p in M.poses:
        t = T[(p, a)]
        Kt = 1.0 / (1.0 / (sS * t["S"][chain]) + 1.0 / (Ks * t["g"]))
        Jr = J * (t["g"] if kin == "cons" else M.n2)
        fs.append(float(np.sqrt(Kt / (Ip + Jr)) / (2 * np.pi)))
    return [r(min(fs), 3), r(max(fs), 3)]


def hits(x):
    return bool(x[1] >= band[0] and x[0] <= band[1])


wm = {}
for a in AX:
    sfe = fe_i[a]["K_pose_model"] / S_T[a]
    for Ks in (100.0, 110.0, 116.0, 120.0, 130.0):
        row = {}
        for jn in ("J_LO", "J_C", "J_HI"):
            for lab, sS in (("V5c", 1.0), ("FE", sfe), ("FE_hot10", 0.90 * sfe), ("FE_hot5", 0.95 * sfe)):
                x = rng(a, Ks, JS[jn], sS)
                row[f"{jn}|{lab}"] = dict(f=x, in_band=hits(x))
        for lab, kw in (("n48|V5c", dict(kin="n48")), ("n48|FE", dict(kin="n48", sS=sfe)), ("chain_low|V5c", dict(chain="low")),
                        ("chain_high|V5c", dict(chain="high"))):
            x = rng(a, Ks, E.J_C, **kw)
            row[lab] = dict(f=x, in_band=hits(x))
        # FE stop-pose structure range with g = n^2 (ASSUMED at the 8 deg stops), centre-type single DOF
        lo, hi = STOP[a]
        x = [r(fr(lo, Ks, M.n2, I["full"], E.J_C), 3), r(fr(hi, Ks, M.n2, I["full"], E.J_C), 3)]
        row["J_C|FE_stops_g_n2"] = dict(f=x, in_band=hits(x))
        wm[f"{a}|Ks{Ks:g}"] = row
out["window_map_full_Hz"] = wm

# 6. K_s at which the full-tank pose maximum reaches the band's lower edge, per variant (bisection on frequency only)
def ks_edge(a, J, sS):
    lo, hi = 50.0, 400.0
    if rng(a, lo, J, sS)[1] >= band[0]:
        return lo
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if rng(a, mid, J, sS)[1] >= band[0]:
            hi = mid
        else:
            lo = mid
    return r(hi, 1)


out["Ks_where_pose_max_reaches_band"] = {a: {f"{jn}|{lab}": ks_edge(a, JS[jn], sS) for jn in ("J_LO", "J_C", "J_HI")
                                             for lab, sS in (("V5c", 1.0), ("FE", fe_i[a]["K_pose_model"] / S_T[a]),
                                                             ("FE_hot10", 0.9 * fe_i[a]["K_pose_model"] / S_T[a]))} for a in AX}
json.dump(out, open(OUT, "w"), indent=1, default=str)
print(json.dumps({k: out[k] for k in ("J_convention", "fe_inertia_kinematics", "structure", "coincidence_band_full_Hz", "Ks_where_pose_max_reaches_band")}, default=str))
for k, v in lfl.items():
    print("LFL", k, v)
for k, v in wm.items():
    print("WM", k, {kk: (vv["f"], "IN" if vv["in_band"] else "-") for kk, vv in v.items()})
