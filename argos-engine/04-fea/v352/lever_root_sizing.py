"""GM-01 / GM-02 lever-root design change (v3.5.2, lead 2026-10-19 item 1): hand-calc sizing from the FEA3D loads.

Method [DERIVED]: the rod force F (vertical at neutral, at the lever eye rho_F 53.075 mm along the arm azimuth a_ch, tau_F 6.453 mm off the arm
plane toward the eye; CAD v3.5.1 numbers from tvc_kinematics.geometry) is carried into the collar band through the root/band junction
(horizontal section at the band bottom z -9.95).  Nominal stress on that section = eccentric normal force: s = -F/A - F(rho_F-rho_c)(rho-rho_c)/I_t
- F tau_F tau / I_r (beam theory on the junction footprint, numerical integration).  The FEA3D R3 regular-node peaks (LC3 runaway SR 609 N:
GM-02 435.1 MPa, GM-01 431.0 MPa; F2 GS 552 N: GM-02 403 MPa (alpha-), GM-01 396 MPa (alpha+)) calibrate an effective concentration factor
Kt_eff = s_FE / s_nom(v3.5.1 footprint).  The changed footprint is then scored as s_peak = Kt_eff x s_nom(new) x Kt_ratio, with Kt_ratio 1.00
(same local fillet scale: R1.2 side / R0.5 inner -> one R1.25 chain, corners rounded) and a +15 % sensitivity.  Hot increment x1.05 (FEA3D
hot bounds: LC3 L1 +0.182 -> +0.128, F2 -0.330 -> -0.362).  7075-T6 Fty 470 / Ftu 540 MPa [LITERATURE, engmat; temperature table RM1-06 open],
SF 1.5 / 2.0 (188 (9)).  Mechanical, 2026-10-19.
"""
import json, math, hashlib
import numpy as np

FTY, FTU, SFY, SFU = 470.0, 540.0, 1.5, 2.0
RHO_F, TAU_F = 53.075, 6.453
FE = {"SR_GM02": (609.0, 435.1), "SR_GM01": (609.0, 431.0), "GS_GM02": (552.0, 403.0), "GS_GM01": (552.0, 396.0)}
HOT = 1.05


def footprint(r_in, r_out, ha_deg, R_v=0.0, n=900):
    """Junction footprint in the arm frame (rho along a_ch, tau tangential): annular sector r_in..r_out, +/-ha, inner corners rounded R_v.
    Returns sample points (rho, tau, dA) on a fine polar grid, plus the boundary points (excluding nothing)."""
    ha = math.radians(ha_deg)
    rr = np.linspace(r_in, r_out, n)
    aa = np.linspace(-ha, ha, n)
    R, Aa = np.meshgrid(0.5 * (rr[1:] + rr[:-1]), 0.5 * (aa[1:] + aa[:-1]), indexing="ij")
    dA = R * (rr[1] - rr[0]) * (aa[1] - aa[0])
    rho, tau = R * np.cos(Aa), R * np.sin(Aa)
    keep = np.ones_like(R, dtype=bool)
    if R_v > 0:
        # corner-round centre: R_v inside both the inner arc (r = r_in + R_v) and the side plane (distance R_v from the radial plane)
        for s in (+1, -1):
            # centre at radius rc, angle s*(ha - d) with rc*sin(d) = R_v and rc = r_in + R_v (tangent to the inner arc)
            rc = r_in + R_v
            d = math.asin(R_v / rc)
            cx, cy = rc * math.cos(s * (ha - d)), rc * math.sin(s * (ha - d))
            # region to remove: points outside the circle but inside the corner wedge (r < rc and |angle| > ha - d)
            inwedge = (R < rc) & (s * Aa > (ha - d))
            outside = (rho - cx) ** 2 + (tau - cy) ** 2 > R_v ** 2
            keep &= ~(inwedge & outside)
    return rho[keep], tau[keep], dA[keep]


def section(r_in, r_out, ha_deg, R_v=0.0):
    rho, tau, dA = footprint(r_in, r_out, ha_deg, R_v)
    A = dA.sum()
    rc = (rho * dA).sum() / A
    It = (((rho - rc) ** 2) * dA).sum()
    Ir = ((tau ** 2) * dA).sum()
    return dict(A=A, rho_c=rc, I_t=It, I_r=Ir, pts=(rho, tau))


def s_nom(sec, F, tau_F=TAU_F):
    rho, tau = sec["pts"]
    s = -F / sec["A"] - F * (RHO_F - sec["rho_c"]) * (rho - sec["rho_c"]) / sec["I_t"] - F * tau_F * tau / sec["I_r"]
    i = int(np.argmax(np.abs(s)))
    return float(abs(s[i])), (float(rho[i]), float(tau[i])), float(s[i])


def ms(vm):
    return FTY / (SFY * vm) - 1.0, FTU / (SFU * vm) - 1.0


cur = section(32.5, 37.0, 16.0)
out = {"id": "lever_root_sizing", "version": "v1", "date": "2026-10-19", "owner": "mechanical", "method": __doc__.strip(),
       "loads_fea3d": {k: {"F_rod_N": v[0], "vm_R3_MPa": v[1]} for k, v in FE.items()},
       "eye_in_arm_frame_mm": {"rho_F": RHO_F, "tau_F": TAU_F, "z_eye": -28.0, "z_junction": -9.95},
       "v351": {}, "candidates": {}}
c = cur
out["v351"] = {"footprint": "r 32.5..37.0 (band OD), +/-16 deg, sharp inner corners (R1.2 side / R0.5 inner junction fillets)",
               "A_mm2": round(c["A"], 2), "rho_c_mm": round(c["rho_c"], 3), "I_t_mm4": round(c["I_t"], 1), "I_r_mm4": round(c["I_r"], 1)}
kt = {}
for k, (F, vm) in FE.items():
    sn, loc, sgn = s_nom(cur, F)
    kt[k] = vm / sn
    out["v351"][k] = {"s_nom_MPa": round(sn, 1), "at_rho_tau_mm": [round(loc[0], 2), round(loc[1], 2)], "Kt_eff": round(vm / sn, 3)}
KT = max(kt.values())
out["Kt_eff_used"] = round(KT, 3)
cands = {
    "C1 boss r38.5, r_in 32.5, +/-16": (32.5, 38.5, 16.0, 0.0),
    "C2 boss r38.5, r_in 33.25, +/-16, Rv 2.5": (33.25, 38.5, 16.0, 2.5),
    "C3 boss r38.5, r_in 33.25, +/-20, Rv 2.5": (33.25, 38.5, 20.0, 2.5),
    "C4 boss r38.5, r_in 33.25, +/-22, Rv 2.5": (33.25, 38.5, 22.0, 2.5),
    "C5 no boss (r37), r_in 32.5, +/-22": (32.5, 37.0, 22.0, 0.0),
    "C6 boss r38.5, r_in 33.0, +/-20, Rv 2.5": (33.0, 38.5, 20.0, 2.5),
}
for name, (ri, ro, ha, rv) in cands.items():
    sec = section(ri, ro, ha, rv)
    rec = {"r_in": ri, "r_out": ro, "half_ang_deg": ha, "R_v": rv, "A_mm2": round(sec["A"], 2), "rho_c_mm": round(sec["rho_c"], 3),
           "I_t_mm4": round(sec["I_t"], 1), "I_r_mm4": round(sec["I_r"], 1), "cases": {}}
    for k, (F, vm) in FE.items():
        sn, loc, sgn = s_nom(sec, F)
        sn0, _, _ = s_nom(cur, F)
        pk = kt[k] * sn
        r = {"s_nom_MPa": round(sn, 1), "ratio_to_v351": round(sn / sn0, 3), "vm_est_cold_MPa": round(pk, 1),
             "MS_y_u_cold": [round(x, 3) for x in ms(pk)], "MS_y_u_hot": [round(x, 3) for x in ms(pk * HOT)],
             "MS_y_u_cold_Kt+15%": [round(x, 3) for x in ms(pk * 1.15)], "MS_y_u_hot_Kt+15%": [round(x, 3) for x in ms(pk * 1.15 * HOT)]}
        rec["cases"][k] = r
    out["candidates"][name] = rec
# rod-force alternative: stall limit for MS_u = +0.10 (and 0) on the v3.5.1 geometry, hot
for tgt in (0.0, 0.10):
    vm_allow = FTU / (SFU * (1 + tgt)) / HOT
    out.setdefault("rod_force_alternative", {})[f"MS_u_{tgt:+.2f}_hot"] = {
        "vm_allow_MPa": round(vm_allow, 1),
        "F_SR_N": round(609.0 * vm_allow / 435.1, 1), "F_GS_cone_N": round(552.0 * vm_allow / 403.0, 1)}
s = json.dumps(out, indent=1)
open("/home/claude/work/mechanical/v352/gm/lever_root_sizing_v1.json", "w").write(s)
print(json.dumps({k: v for k, v in out.items() if k not in ("method",)}, indent=1)[:9000])
print("sha256/16", hashlib.sha256(s.encode()).hexdigest()[:16])
