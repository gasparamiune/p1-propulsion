"""TC-02 plug glands S01 / S02 (2x AS568-226 FKM 90A, no back-up ring): extrusion gap at the drawing maximum clearance plus the case's
radial growth under pressure, plus the rev-4 thermal differential; squeeze / stretch / fill; seal positions vs the J-FWD holes.
Lead 07:43Z items 1 and 4.  Mechanical, 2026-10-20, v1.  CALC on SIM temperatures; DATASHEET values as cited; every other number DERIVED.

Sources:
 [D1] Freudenberg-NOK Sealing Technologies, 'O-Ring Design Quick Reference' (no date / edition printed), p. 6 'Maximum Recommended
      Extrusion Gap in Inches (mm)', static applications below 1500 psi; gap = bore - piston (diameters), 'unless the hardware can ensure
      the bore and the piston or rod remain concentric, we have to assume that all of the gap possible can shift to one side'; above
      1500 psi 'consult Freudenberg-NOK'; no temperature note; p. 5 squeeze >= 5 %, target 20 %, max 30 %; gland fill target 75 %, max 85 %;
      p. 16 AS568-226 ID 1.984 +/- 0.018 in (50.39 +/- 0.46 mm), CS 0.139 +/- 0.004 in (3.53 +/- 0.10 mm).
      URL https://fst.com/~/media/files/fst,-d-,com/markets/mobility/broschueren/fnst%20o-ring%20reference%20as568%20sizes.ashx,
      accessed 2026-10-20.  The durometer columns are not labelled 'Shore A' in the source (presumed Shore A).
 [C1] CAD v3.5.2 (parts_engine.py; TC-01 / TC-02 drawing fits): bore 57.25 H8 (+0.046 / 0), plug 57.20 f7 (-0.030 / -0.060), groove
      51.65 h9 (0 / -0.074) x 4.85 +0.13 / 0, glands at zf + 3.0 and + 3.0 + 4.85 + 3.0 (zf = injector face z 103.513), J-FWD holes d5.5 at
      z 127.513 (taps M5-6H), case OD 63.5.
 [M1] engmat 6061-T6 E(T), alpha (secant from 20 C), nu 0.33 (LITERATURE, project tables).
 [T1] rev-4 B1 thermal fields (v352_NF2b_R4_GVLO / _GVHI, chain 8), node histories tb70/hist/<label>_hist.npz (case_tc_hist_v352.py).
Pressure growth of the case bore: Lame thick cylinder, closed end (the case carries the end load aft of the screw row), at the g1 land
with E at the land's burn maximum temperature; the full far-field value is used (the land is at the end of the pressurised length, where
a shell would give about half: not credited).  Plug OD: hollow cylinder (manifold bore d10) under the same external pressure (conservative:
the land forward of the ring is not pressurised, and the plug's Poisson expansion under its end load would close the gap: not credited).
Thermal: the change of the bore - plug diametral clearance at the g1 forward land from the case and plug temperatures (secant alpha),
largest opening over the burn frames (pressurised period), both gap bounds.  Pressure across S01: chamber gauge pressure (the inter-seal
cavity at ambient: the full differential)."""
import json, math, hashlib, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/04-fea/src")
import engmat

J = Path("/home/claude/work/mechanical/v352/jfwd")
HIST = Path("/home/claude/work/mechanical/v352/tb70/hist")
OUT = J / "gland_fwd_v352_v1.json"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
M = engmat.MATERIALS["AL6061-T6"]
E_T = lambda T: float(np.interp(T, M["E"]["T_C"], M["E"]["v"])) / 1e6        # MPa
A_T = lambda T: float(np.interp(T, M["alpha"]["T_C"], M["alpha"]["v"]))
NU = M["nu"]["v"]
BAR_PSI = 14.5038
# [D1] p. 6, 90 durometer column, (psi, gap mm)
D1_90 = [(500.0, 0.64), (750.0, 0.58), (1000.0, 0.46), (1250.0, 0.38), (1500.0, 0.30)]
ZF, BOLT_Z, GW = 103.5134, 127.5134, 4.85
G1 = (ZF + 3.0, ZF + 3.0 + GW)
G2 = (G1[1] + 3.0, G1[1] + 3.0 + GW)
LAND = (G1[1], G2[0])                                   # S01 forward land (the extrusion side of S01)
BORE, PLUG, GROOVE = (57.250, 57.296), (57.140, 57.170), (51.576, 51.650)
GW_TOL = (4.85, 4.98)
ID, CS = (50.39 - 0.46, 50.39 + 0.46), (3.53 - 0.10, 3.53 + 0.10)
a_b, b_o, r_m = 57.296 / 2.0, 63.5 / 2.0, 5.0         # bore radius (max), case OD radius, plug manifold bore radius
PRESS = {"MEOP_45_bar_abs": 45.0, "proof_67.5_bar_abs": 67.5, "FA1S_151.04_bar_abs": 151.04}
P_AMB = 1.01325


def allow90(psi):
    if psi > D1_90[-1][0]:
        return None
    if psi <= D1_90[0][0]:
        return D1_90[0][1]
    return float(np.interp(psi, [p for p, _ in D1_90], [g for _, g in D1_90]))


def lame_bore_growth(p, E):
    """radial displacement (mm) of the bore of a closed-end thick cylinder under internal gauge pressure p (MPa)."""
    k = b_o ** 2 - a_b ** 2
    st, sr, sz = p * (b_o ** 2 + a_b ** 2) / k, -p, p * a_b ** 2 / k
    return a_b / E * (st - NU * (sr + sz))


def plug_shrink(p, E):
    """radial displacement (mm, negative = inward) of the OD of a hollow plug (bore r_m) under external pressure p (MPa), plane stress."""
    b = 57.170 / 2.0
    return -p * b / E * ((b ** 2 + r_m ** 2) / (b ** 2 - r_m ** 2) - NU)


# ---- thermal (rev-4 fields): land temperatures and the clearance change, both bounds
OFF = None
therm = {}
for gv in ("GVLO", "GVHI"):
    lab = f"DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_R4_{gv}"
    fh = HIST / f"{lab}_hist.npz"
    z = np.load(fh, allow_pickle=True)
    info = json.loads(str(z["info"]))
    off = info["inj_face_z_mm"] - ZF
    OFF = off
    t = np.asarray(z["t_s"], float)
    X1, T1, X2, T2 = z["X_TC01"], z["T_TC01"], z["X_TC02"], z["T_TC02"]
    w1 = (X1[:, 1] >= LAND[0] + off - 1e-6) & (X1[:, 1] <= LAND[1] + off + 1e-6)
    w2 = (X2[:, 1] >= LAND[0] + off - 1e-6) & (X2[:, 1] <= LAND[1] + off + 1e-6)
    rb = X1[w1, 0].min()
    m1 = w1 & (X1[:, 0] <= rb + 0.15)
    rp = X2[w2, 0].max()
    m2 = w2 & (X2[:, 0] >= rp - 0.15)
    Tc = T1[:, m1].mean(axis=1) - 273.15
    Tp = T2[:, m2].mean(axis=1) - 273.15
    dD = np.array([57.25 * (A_T(c) * (c - 20.0) - A_T(q) * (q - 20.0)) for c, q in zip(Tc, Tp)])      # mm, + = clearance opens
    burn = (t > 0.0) & (t <= 21.651 + 1e-6)
    ib = int(np.argmax(np.where(burn, dD, -np.inf)))
    ia = int(np.argmax(dD))
    # S01 groove: TC-02 groove-bottom / flank nodes and the bore over the groove (the ring's bounding surfaces)
    g1z = (G1[0] + off, G1[1] + off)
    mg2 = (X2[:, 1] >= g1z[0] - 1e-6) & (X2[:, 1] <= g1z[1] + 1e-6) & (X2[:, 0] >= GROOVE[0] / 2.0 - 0.1)
    mg1 = (X1[:, 1] >= g1z[0] - 1e-6) & (X1[:, 1] <= g1z[1] + 1e-6) & (X1[:, 0] <= rb + 0.15)
    Tring = np.maximum(T2[:, mg2].max(axis=1), T1[:, mg1].max(axis=1)) - 273.15
    therm[gv] = {"hist": f"tb70/hist/{fh.name}", "sha256_16": sha(fh), "frd_sha256_16": info.get("frd_sha256_16"), "z_offset_thermal_mm": round(off, 4),
                 "n_nodes_land": [int(m1.sum()), int(m2.sum())], "r_bore_plug_nodes_mm": [round(float(rb), 3), round(float(rp), 3)],
                 "burn_max_opening": {"t_s": round(float(t[ib]), 3), "T_case_C": round(float(Tc[ib]), 1), "T_plug_C": round(float(Tp[ib]), 1),
                                      "dD_mm": round(float(dD[ib]), 4)},
                 "any_frame_max_opening": {"t_s": round(float(t[ia]), 3), "T_case_C": round(float(Tc[ia]), 1), "T_plug_C": round(float(Tp[ia]), 1),
                                           "dD_mm": round(float(dD[ia]), 4)},
                 "burn_min_dD_mm": round(float(dD[burn].min()), 4),
                 "case_land_T_burn_max_C": round(float(Tc[burn].max()), 1), "plug_land_T_burn_max_C": round(float(Tp[burn].max()), 1),
                 "ring_T_burn_max_C": round(float(Tring[burn].max()), 1), "ring_T_max_C": round(float(Tring.max()), 1),
                 "t_ring_T_max_s": round(float(t[int(np.argmax(Tring))]), 2)}
# ---- gap budget per pressure: drawing max clearance + 2 x (case growth - plug OD displacement) + thermal opening (burn max, >= 0)
c0 = BORE[1] - PLUG[0]
dth = max(max(therm[g]["burn_max_opening"]["dD_mm"] for g in therm), 0.0)
Tcase = max(therm[g]["case_land_T_burn_max_C"] for g in therm)
E_c, E_20 = E_T(Tcase), E_T(20.0)
rows = {}
for nm, pa in PRESS.items():
    pg = (pa - P_AMB) * 0.1
    ub, up = lame_bore_growth(pg, E_c), plug_shrink(pg, E_c)
    gap = c0 + 2.0 * (ub - up) + dth
    psi = (pa - P_AMB) * BAR_PSI
    al = allow90(psi)
    rows[nm] = {"p_gauge_bar": round(pa - P_AMB, 2), "p_gauge_psi": round(psi, 0), "case_bore_growth_radial_mm": round(ub, 4),
                "case_bore_growth_radial_mm_at_20C": round(lame_bore_growth(pg, E_20), 4), "plug_OD_radial_mm": round(up, 4),
                "gap_bore_minus_piston_mm": {"drawing_max_rest": round(c0, 3), "plus_pressure": round(2.0 * (ub - up), 4), "plus_thermal_burn_max": round(dth, 4),
                                             "total": round(gap, 4)},
                "allowable_D1_90duro_mm": al, "MS": (round(al / gap - 1.0, 3) if al else None),
                "verdict": ("PASS" if al and gap <= al else ("FAIL" if al else "OUTSIDE THE SOURCE TABLE (> 1500 psi: maker to be consulted)"))}
# ---- squeeze / stretch / fill (static radial gland, [D1] p. 5 criteria)
L_min, L_max = (BORE[0] - GROOVE[1]) / 2.0, (BORE[1] - GROOVE[0]) / 2.0
sq_min, sq_max = (CS[0] - L_max) / CS[0], (CS[1] - L_min) / CS[1]
st_min, st_max = GROOVE[0] / ID[1] - 1.0, GROOVE[1] / ID[0] - 1.0
fill_max = (math.pi / 4.0 * CS[1] ** 2) / (L_min * GW_TOL[0])
gland = {"gland_depth_mm": [round(L_min, 3), round(L_max, 3)], "squeeze_pct": [round(100 * sq_min, 1), round(100 * sq_max, 1)],
         "stretch_pct": [round(100 * st_min, 2), round(100 * st_max, 2)], "fill_max_pct": round(100 * fill_max, 1),
         "criteria_D1": "squeeze >= 5 %, target 20 %, max 30 %; fill target 75 %, max 85 %",
         "pass": bool(sq_min >= 0.05 and sq_max <= 0.30 and fill_max <= 0.85)}
pos = {"S01_z_mm": [round(G1[0], 3), round(G1[1], 3)], "S02_z_mm": [round(G2[0], 3), round(G2[1], 3)], "S01_forward_land_z_mm": [round(LAND[0], 3), round(LAND[1], 3)],
       "injector_face_z_mm": ZF, "jfwd_hole_d5.5_z_mm": [round(BOLT_Z - 2.75, 3), round(BOLT_Z + 2.75, 3)], "tap_M5_major_z_mm": [round(BOLT_Z - 2.5, 3), round(BOLT_Z + 2.5, 3)],
       "hole_edge_to_S02_forward_wall_mm": round(BOLT_Z - 2.75 - G2[1], 3), "M5_major_to_S02_forward_wall_mm": round(BOLT_Z - 2.5 - G2[1], 3),
       "statement": ("S01 (gland 1) and S02 lie between the chamber (aft of the injector face) and the J-FWD holes: from the chamber, the "
                     "bore / plug annulus is gas-wetted only up to S01; the holes and taps are forward of S02 in the dry annulus, which is "
                     "vented to ambient through the holes and the case end; the holes are not wetted unless both S01 and S02 leak")}
out = {"id": "gland_fwd_v352", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "o_ring": {"part": "HW-150 SAE AS568-226 FKM 90A (BOM; TC-02 drawing note), qty 2 (S01, S02), no back-up ring (groove 4.85 wide, no "
                          "back-up ring line in the BOM)", "ID_mm": [round(x, 2) for x in ID], "CS_mm": [round(x, 2) for x in CS],
                  "dims_source": "[D1] p. 16 (the BOM line HW-150 gives ID 47.22 = the -225 ID, AS RECALLED: corrected in hardware v1.5)"},
       "positions": pos, "thermal_rev4": therm, "E_case_MPa_at_T": {"T_C": Tcase, "E_MPa": round(E_c, 0)}, "extrusion": rows, "gland": gland,
       "notes": ["the [D1] table carries no temperature statement; the ring temperature at its bounding surfaces is listed per bound "
                 "(FKM compound rating and hot hardness TO-SOURCE for the purchased ring)",
                 "MEOP / proof treated as absolute pressures; as gauge they change the gap by < 0.001 mm"]}
s = json.dumps(out, indent=1, default=float)
OUT.write_text(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
print(json.dumps(pos))
for g, v in therm.items():
    print(g, {k: v[k] for k in ("z_offset_thermal_mm", "n_nodes_land", "r_bore_plug_nodes_mm", "burn_max_opening", "any_frame_max_opening", "burn_min_dD_mm", "case_land_T_burn_max_C", "ring_T_burn_max_C", "ring_T_max_C", "t_ring_T_max_s")})
for k, v in rows.items():
    print(k, v)
print(gland)
