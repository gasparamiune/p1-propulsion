"""J-FWD FA1S screw fix sizing and the no-slack knock-ons, for the lead's joint ruling (lead 10:24Z (b) rulings 1-4, 10:28Z V basis,
10:47Z basis and additions).  Mechanical, 2026-10-20, v1.  CALC / DERIVED unless tagged; nothing here is physical approval.

FA1S screw cell [LITERATURE criterion]: NASA-STD-5020A sec. 4.4.4 Eq. 22 (threads in the shear plane, elastic bending, no plastic
credit): (Psu / Psu-allow)^1.2 + (Ptu / Ptu-allow + fbu / Ftu)^2 <= 1, Psu-allow = Fsu Am (Eq. 13, Am = minor-diameter area),
Fsu = 0.6 Ftu (TO-VERIFY), Ptu-allow = Ftu As.  Eq. 23 (fbu / Fbu with Fbu = 1.70 Ftu, a section-geometry factor, NOT a sourced Fbu) is
information.  MS = lambda - 1, lambda scaling V and M together with N fixed (the FA1S pressure loads), by bisection.
Preload OMITTED (governing, lead 10:47Z [LITERATURE] 5020A 4.4.4 p. 33 / 5020B; the 2012 NASA-STD-5020 A.7 rationale; A4-80 0.3d
full-size elongation, Bossard T.019): Ptu = 0 (the FE FA1S screw tension falls below the preload, 3092.8-3211.6 N vs 3680-3820 N at
PRELOAD, so the external tensile part is zero).  Preload INCLUDED (information, required beside it): Ptu = 3211.6 N, FEA3D's FA1S
maximum-section tension (screw_bend.json b15096bcd367dae2, 3750 N installation), kept for every option (same installed band).
V (lead 10:28Z): CALC 3888.1 N per screw (151.04 bar abs on pi/4 57.25^2, / 10) or the gauge value 3862.0; FE V rows are information.
Arm to the thread entry: 0.920 mm sharp (FEA3D FA1S M 3339.1 / V 3629.5 at x' 28.6) and +0.2 for the R0.2 bore-side break (governing,
1.120 mm), the same arm for every option (ASSUMED for the M6 and 12x rows until an FE arm exists); arm sensitivity 1.32 / 1.52 shown.
Screw allowables at 45.6 C: A4-80 Rm 800 x kTu (SS316L Ftu ratio, engmat) = 792.5; class 100 (A4-100) Rm 1000 x kTu = 990.6
(ISO 3506-1:2020 class 100 TO-VERIFY; BUMAX 109 catalogue Rm 1000 / Rp0.2 900 / 0.2d up to M12); IN718 Ftu(T) engmat DATASHEET (Special
Metals SMC-045, AMS 5662/5663 minimum 1241 MPa RT, linear to 965 at 649 C) = 1229.8.
TC-01 joint rows (lead 10:15Z (a)): hole bearing sigma = V / (D L_eff), L_eff = wall - 0.2 (bore-side R0.2 hard max) - 0.1 (flat-side
0.1 x 45), at the nominal and the drawing-limit wall (bore 57.296, flat at its low end); shear-out, net section and ligament Pm+Pb as
jfwd_seat_v352_v1 (a371bdc9fe2d9986) with the option's hole, spot face and count; Fbry / Fbru = 1.4 Fty / 1.6 Ftu (engmat, e/D 2.0).
TC-02 rows as jfwd_v352 (tapped-thread bearing V / (D1 L_eff), L_eff = L_e - 0.5; internal-thread shear at F_max + the 45.6 C thermal
rise (3965 N, 3.0 N m band, kept for every option at the same preload band); tap-row net ligament; shear-out to the g2 groove).
No-slack knock-ons: jfwd_relax_v352_v3.json (read here; the 24 cases on the seat-line and ring-line bounds per option, the select-fit
and higher-preload fixes, the information sensitivities).  Availability, CAD, BOM and mass deltas per option are stated with sources."""
import json, math, hashlib
from pathlib import Path
import numpy as np

J = Path("/home/claude/work/mechanical/v352/jfwd")
OUT = J / "jfwd_fix_v352_v1.json"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
SRC = (J / "jfwd_v352.py").read_text()
NS = {}
exec(compile(SRC.split("\nOPTS = [")[0], str(J / "jfwd_v352.py"), "exec"), NS)
tab, MAT, ro_neuber, strip_area, TH, kT, kTu = NS["tab"], NS["MAT"], NS["ro_neuber"], NS["strip_area"], NS["TH"], NS["kT"], NS["kTu"]
GEO = NS["GEO"]
RELAX = J / "jfwd_relax_v352_v3.json"
SEAT = J / "jfwd_seat_v352_v1.json"
SB = Path("/home/claude/work/shared-fallback/engine/04-fea/assembly3d_v352/jfwd_interim/js5_mu0_T3750_g078_upto4_screw_bend.json")
RX = json.loads(RELAX.read_text())
SBJ = json.loads(SB.read_text())
T = 45.6
P_ABS, P_AMB, D_SEAL = 151.04, 1.01325, 57.25
A_P = math.pi / 4.0 * D_SEAL ** 2
F_ABS, F_G = P_ABS * 0.1 * A_P, (P_ABS - P_AMB) * 0.1 * A_P
R_O, E_EDGE = 63.5 / 2.0, 12.0
R_I_NOM, R_I_MAX = 57.25 / 2.0, 57.296 / 2.0
Fty, Ftu = tab("AL6061-T6", "Fty", T), tab("AL6061-T6", "Ftu", T)
E_AL = tab("AL6061-T6", "E", T)
Fbry, Fbru = MAT["AL6061-T6"]["Fbry_over_Fty_eD2"]["v"] * Fty, MAT["AL6061-T6"]["Fbru_over_Ftu_eD2"]["v"] * Ftu
Fsy, Fsu_al = 0.577 * Fty, MAT["AL6061-T6"]["Fsu_over_Ftu"]["v"] * Ftu
ms = lambda cap, dem: round(cap / dem - 1.0, 3)
FA1S = SBJ["steps"]["FA1S"]
N_INC = max(s_["N"] for s_ in FA1S["sections"])                     # 3211.6
ARM_SHARP = FA1S["checks"]["x28.6_thread_entry_extrapolated"]["M_Nmm"] / FA1S["checks"]["x28.6_thread_entry_extrapolated"]["V_N"]
ARM_GOV = ARM_SHARP + 0.2
F_FA1S_PRE = 3965.0                                                  # F_max + 45.6 C thermal rise, 3.0 N m band (jfwd_seat_v352_v1)

SCREWS = {"A4-80": {"Ftu": 800.0 * kTu(T), "Fty": 600.0 * kT(T), "src": "ISO 3506-1 class 80 minima Rm 800 / Rp0.2 600 x SS316L ratios (engmat "
                    "LITERATURE); A 0.3d full size (Bossard 'Materials screws & nuts' 2005 T.019; BUMAX 88 catalogue Rm 800 / Rp0.2 640 / 0.3d)"},
          "A4-100": {"Ftu": 1000.0 * kTu(T), "Fty": 800.0 * kT(T), "src": "property class 100 minima Rm 1000 / Rp0.2 800 (ISO 3506-1:2020 class 100: "
                     "TO-VERIFY, table not readable) x SS316L ratios; BUMAX 109 (catalogue) Rm 1000 / Rp0.2 900 / 0.2d up to M12"},
          "IN718": {"Ftu": tab("IN718", "Ftu", T), "Fty": tab("IN718", "Fty", T), "src": "IN718 AMS 5662/5663 minima (Special Metals SMC-045, engmat "
                    "DATASHEET), linear 20-649 C; Fsu / Ftu 0.6 (engmat LITERATURE-approx, TO-VERIFY)"}}
SEC = {"M5": {"d": 5.0, "d3": 4.019, "As": 14.18}, "M6": {"d": 6.0, "d3": 4.773, "As": 20.12}}
for k_, v_ in SEC.items():
    v_["Am"] = math.pi / 4.0 * v_["d3"] ** 2
    v_["Z3"] = math.pi * v_["d3"] ** 3 / 32.0


def eq22(V, M, N, Psa, Pta, Ftu_, plastic=None):
    """5020A Eq. 22 (or Eq. 23 with plastic = Fbu) interaction value; MS = lambda - 1 with V and M scaled by lambda, N fixed."""
    def f(l):
        rs = (l * V / Psa) ** 1.2
        if plastic is None:
            return rs + (N / Pta + l * M / sec_z[0] / Ftu_) ** 2
        return rs + (N / Pta) ** 2 + l * M / sec_z[0] / plastic
    lo, hi = 0.0, 5.0
    if f(hi) < 1.0:
        return f(1.0), 4.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if f(mid) < 1.0 else (lo, mid)
    return f(1.0), 0.5 * (lo + hi) - 1.0


sec_z = [None]


def screw_cells(size, grade, n):
    s_, g_ = SEC[size], SCREWS[grade]
    sec_z[0] = s_["Z3"]
    Ftu_ = g_["Ftu"]
    Psa, Pta = 0.6 * Ftu_ * s_["Am"], Ftu_ * s_["As"]
    rows = {}
    for vn, V in (("CALC_abs_3888.1", F_ABS / n), ("gauge_3862.0", F_G / n)):
        for an, arm in (("arm_+0.2_governing", ARM_GOV), ("arm_sharp_info", ARM_SHARP), ("arm_+0.4_sens", ARM_GOV + 0.2), ("arm_+0.6_sens", ARM_GOV + 0.4)):
            M = V * arm
            io, mo = eq22(V, M, 0.0, Psa, Pta, Ftu_)
            ii, mi = eq22(V, M, N_INC, Psa, Pta, Ftu_)
            _, m23o = eq22(V, M, 0.0, Psa, Pta, Ftu_, plastic=1.70 * Ftu_)
            rows[f"{vn}|{an}"] = {"V_N": round(V, 1), "arm_mm": round(arm, 3), "M_Nmm": round(M, 1), "fbu_MPa": round(M / s_["Z3"], 1),
                                  "Psu_over_allow": round(V / Psa, 4), "fbu_over_Ftu": round(M / s_["Z3"] / Ftu_, 4),
                                  "MS_omitted_governing": round(mo, 3), "interaction_omitted": round(io, 3),
                                  "MS_included_info": round(mi, 3), "interaction_included": round(ii, 3),
                                  "MS_eq23_omitted_info_Fbu_1.70Ftu_geometry_only": round(m23o, 3)}
    if size == "M5" and n == 10:
        Vfe, Mfe = FA1S["checks"]["x28.6_thread_entry_extrapolated"]["V_N"], FA1S["checks"]["x28.6_thread_entry_extrapolated"]["M_Nmm"]
        _, mo = eq22(Vfe, Mfe, 0.0, Psa, Pta, Ftu_)
        _, mi = eq22(Vfe, Mfe, N_INC, Psa, Pta, Ftu_)
        rows["FE_V_3629.5_sharp_info_only"] = {"V_N": Vfe, "M_Nmm": Mfe, "MS_omitted": round(mo, 3), "MS_included": round(mi, 3),
                                               "note": "information only (lead 10:28Z: FE V is 0.934 of the load balance)"}
    return {"size": size, "grade": grade, "n": n, "Ftu_45.6C_MPa": round(Ftu_, 1), "Fsu_MPa": round(0.6 * Ftu_, 1), "A_m_mm2": round(s_["Am"], 3),
            "A_s_mm2": s_["As"], "Z_3_mm3": round(s_["Z3"], 3), "Psu_allow_N": round(Psa, 1), "Ptu_allow_N": round(Pta, 1), "N_included_N": N_INC,
            "allowable_src": g_["src"], "rows": rows,
            "governing": rows["CALC_abs_3888.1|arm_+0.2_governing"]["MS_omitted_governing"],
            "included_at_governing_row": rows["CALC_abs_3888.1|arm_+0.2_governing"]["MS_included_info"],
            "gauge_governing": rows["gauge_3862.0|arm_+0.2_governing"]["MS_omitted_governing"]}


def net_area(r_i, n, dh, r_flat, d_sf):
    A_ring = math.pi * (R_O ** 2 - r_i ** 2)
    y = np.linspace(-dh / 2.0, dh / 2.0, 20001)
    strip = np.trapezoid(np.sqrt(R_O ** 2 - y ** 2) - np.sqrt(r_i ** 2 - y ** 2), y)
    hc = math.sqrt(R_O ** 2 - r_flat ** 2)
    yy = np.linspace(dh / 2.0, min(hc, d_sf / 2.0), 20001)
    seg = 2.0 * np.trapezoid(np.clip(np.sqrt(R_O ** 2 - yy ** 2) - r_flat, 0.0, None), yy)
    return A_ring - n * strip - n * seg, strip, seg


def spot_face_volume(r_flat, d_sf):
    """material removed by one flat spot face d_sf at r_flat on the R_O cylinder (outside the hole: the hole volume is counted apart)."""
    x = np.linspace(-d_sf / 2.0, d_sf / 2.0, 801)
    X, Y = np.meshgrid(x, x)
    inside = X ** 2 + Y ** 2 <= (d_sf / 2.0) ** 2
    depth = np.clip(np.sqrt(np.clip(R_O ** 2 - X ** 2, 0.0, None)) - r_flat, 0.0, None)
    return float(np.sum(depth * inside) * (x[1] - x[0]) ** 2)


def tc01_cells(V, n, size, d_sf):
    th = TH[size]
    D, dh = th["d"], th["hole"]
    r_flat = math.sqrt(R_O ** 2 - (d_sf / 2.0) ** 2)
    out = {"r_flat_mm": round(r_flat, 4), "spot_face_d_mm": d_sf, "hole_d_mm": dh}
    for wn, r_i in (("nominal_wall", R_I_NOM), ("drawing_limit_wall", R_I_MAX)):
        t = r_flat - r_i
        L = t - 0.3
        sbr = V / (D * L)
        A_so = 2.0 * t * (E_EDGE - dh / 2.0)
        tso = V / A_so
        A_n, strip, seg = net_area(r_i, n, dh, r_flat, d_sf)
        Pm = F_ABS / A_n
        w_lig = math.pi * (2.0 * R_O + 2.0 * r_i) / 2.0 / n - dh
        Pb = V / (w_lig * t)
        V8 = F_G / 8.0
        W_D = math.pi * 2.0 * R_O / n / D
        K_tb = 4.0 / (W_D - 1.0)
        s_el = max(399.0 * V / V8, K_tb * sbr)
        m2 = 0.52 * (0.98 - Fty / Ftu)
        worst = max((ro_neuber(s_el, E_AL, Fty, nn) + (nn,) for nn in (15.0, 30.0)), key=lambda q: q[1])
        out[wn] = {"t_wall_mm": round(t, 4), "L_eff_bearing_mm": round(L, 4),
                   "hole_bearing": {"sigma_MPa": round(sbr, 1), "MS_y": ms(Fbry, sbr), "MS_u": ms(Fbru, sbr)},
                   "shear_out": {"tau_MPa": round(tso, 1), "MS_y": ms(Fsy, tso), "MS_u": ms(Fsu_al, tso)},
                   "net_section": {"A_net_mm2": round(A_n, 2), "Pm_MPa": round(Pm, 1), "MS_y": ms(Fty, Pm), "MS_u": ms(Ftu, Pm)},
                   "ligament_PmPb": {"w_lig_mm": round(w_lig, 2), "PmPb_MPa": round(Pm + Pb, 1), "MS_y": ms(Fty, Pm + Pb), "MS_u": ms(Ftu, Pm + Pb)},
                   "hole_edge_neuber_info": {"sigma_el_MPa": round(s_el, 1), "eps_local": round(worst[1], 5), "eps_limit": round(m2, 4), "MS_strain": ms(m2, worst[1])}}
    return out


def tc02_cells(V, n, size, t_wall, L_screw, F_pre):
    th = TH[size]
    L_e = L_screw - t_wall - 0.025
    L_eff = L_e - 0.5
    sbt = V / (th["D1"] * L_eff)
    An = strip_area(th, min(L_eff, 8.0 - 0.5))
    A_pl = math.pi / 4.0 * (GEO["plug_OD"] ** 2 - GEO["manifold_bore_d"] ** 2) - n * th["tap"] * 9.0
    s_pl = F_ABS / A_pl
    dz = GEO["bolt_z"] - GEO["g2_fwd_wall_z"] - th["d"] / 2.0
    tso2 = V / (2.0 * dz * L_eff)
    return {"L_e_mm": round(L_e, 3), "L_eff_mm": round(L_eff, 3),
            "tapped_thread_bearing": {"sigma_MPa": round(sbt, 1), "MS_y": ms(Fbry, sbt), "MS_u": ms(Fbru, sbt)},
            "internal_thread_shear_at_F_max_thermal": {"F_N": F_pre, "A_n_mm2": round(An, 1), "tau_MPa": round(F_pre / An, 1),
                                                      "MS_y": ms(Fsy, F_pre / An), "MS_u": ms(Fsu_al, F_pre / An)},
            "tap_row_net_ligament_compression": {"Pm_MPa": round(s_pl, 1), "MS_y": ms(Fty, s_pl)},
            "shear_out_to_g2": {"ligament_mm": round(dz, 2), "Pm_vm_MPa": round(math.sqrt(3.0) * tso2, 1), "MS_y": ms(Fty, math.sqrt(3.0) * tso2)}}


def screw_mass_g(size, rho):
    th = TH[size]
    dk, k = th["dk"], th["k"]
    s_, t_ = {"M5": (3.0, 1.6), "M6": (4.0, 2.2)}[size]          # hex socket AS RECALLED (hardware_v351 class)
    v_head = math.pi * k * (3.0 * (dk / 2.0) ** 2 + k ** 2) / 6.0
    v = v_head - math.sqrt(3.0) / 2.0 * s_ ** 2 * t_ + math.pi / 4.0 * th["d2"] ** 2 * 10.0
    return v * 1e-3 * rho


RHO_AL, RHO_A4, RHO_718 = 2.70, 8.00, 8.19
V_SF105 = spot_face_volume(math.sqrt(R_O ** 2 - 5.25 ** 2), 10.5)
V_SF115 = spot_face_volume(math.sqrt(R_O ** 2 - 5.75 ** 2), 11.5)
m5, m6 = screw_mass_g("M5", RHO_A4), screw_mass_g("M6", RHO_A4)
hole = lambda d, t: math.pi / 4.0 * d ** 2 * t
tap = lambda d: math.pi / 4.0 * d ** 2 * 9.0
MASS = {
    "A4-80 M5 x10 (baseline)": {"delta_g": 0.0},
    "A4-100 M5 x10": {"delta_g": 0.0, "parts": "screw grade only"},
    "IN718 M5 x10": {"delta_g": round(10 * m5 * (RHO_718 / RHO_A4 - 1.0), 2), "parts": "screw material only (density 8.19 vs 8.00)"},
    "A4-80 M6 x10": {"delta_g": round(10 * (m6 - m5) - 10 * RHO_AL * 1e-3 * (hole(6.6, 2.600) - hole(5.5, 2.688) + (V_SF115 - V_SF105) + tap(5.0) - tap(4.2)), 2),
                     "parts": f"screws +10 x {m6 - m5:.3f} g; TC-01 holes 6.6 and d11.5 spot faces, TC-02 drill 5.0 x 9.0 (Al removed)"},
    "A4-80 12x M5": {"delta_g": round(2 * m5 - 2 * RHO_AL * 1e-3 * (hole(5.5, 2.688) + V_SF105 + tap(4.2)), 2),
                     "parts": f"+2 screws ({m5:.3f} g each), +2 TC-01 holes / spot faces, +2 TC-02 taps (Al removed)"}}
OPT = {
    "A4-80 M5 x10 (baseline)": ("M5", "A4-80", 10, 10.5),
    "A4-100 M5 x10": ("M5", "A4-100", 10, 10.5),
    "IN718 M5 x10": ("M5", "IN718", 10, 10.5),
    "A4-80 M6 x10": ("M6", "A4-80", 10, 11.5),
    "A4-80 12x M5": ("M5", "A4-80", 12, 10.5)}
RELAX_KEY = {"A4-80 M5 x10 (baseline)": ["A4-80 M5 x10 (baseline)"], "A4-100 M5 x10": ["A4-100 M5 x10"], "IN718 M5 x10": ["IN718 M5 x10"],
             "A4-80 M6 x10": ["A4-80 M6 x10"], "A4-80 12x M5": ["A4-80 12x M5 (local k_sh)", "A4-80 12x M5 (ring k_sh x10/12)"]}
AVAIL = {
    "A4-80 M5 x10 (baseline)": {"status": "STOCK (A4-80-class)", "part": "BUMAX 88-MKT M5 x 10, ISO 7380 button head, hexalobular drive, 316L HiMo "
                                "(1.4436), Rm 800 / Rp0.2 640 / A 0.3d", "src": "BUMAX product catalogue (Bufab Stainless AB, SE-693 03 Svarta; "
                                "https://local.bufab.com/wp-content/uploads/sites/4/2014/10/BUMAX-product-catalogue.pdf, accessed 2026-10-20; "
                                "catalogue date not printed); Bufab Denmark folder https://local.bufab.com/wp-content/uploads/sites/4/2013/08/Folder-Bumax_DK.pdf",
                                "delivery_DK6400": "Bufab DK distributor: TO-QUOTE (price, lead time); current range vs the catalogue TO-VERIFY"},
    "A4-100 M5 x10": {"status": "NOT FOUND", "part": "no class-100 stainless M5 head part fitting the d10.5 spot face and the 1.0 mm FD-04 envelope found",
                      "src": "BUMAX catalogue: BUMAX 109 only as ISO 4762 M6-M12 (no M5, no button head; BUMAX 88 is the only ISO 7380); web search "
                             "'ISO 7380 A4-100 M5', 'A4-100 M5 ISO 4762 / 7380 / 14580' (2026-10-20): no stock listing",
                      "delivery_DK6400": "a special-order class-100 M5 button head would be a custom part (TO-QUOTE); per the lead: go to the next option"},
    "IN718 M5 x10": {"status": "CUSTOM (no stock part found)", "part": "M5 x 10 button head in IN718 (AMS 5662 bar, aged to AMS 5663), drawing to ISO 7380-1 "
                     "dk 9.5 / k 2.75, rolled thread after ageing TO-DEFINE", "src": "Fasteners Clearinghouse network search 'ISO 7380 superalloy' "
                     "(2026-10-20): Inconel 600 M5 x 12 and 1/4-20 IN718 ANNEALED button heads only, US stock",
                     "delivery_DK6400": "custom fastener maker TO-SELECT, TO-QUOTE (lead time weeks)"},
    "A4-80 M6 x10": {"status": "STOCK (A4-80-class)", "part": "BUMAX 88-MKT M6 x 10, ISO 7380 button head (catalogue lists M5, M6, M8)",
                     "src": "BUMAX product catalogue (as above)", "delivery_DK6400": "Bufab DK: TO-QUOTE"},
    "A4-80 12x M5": {"status": "STOCK", "part": "as baseline, qty 12", "src": "as baseline", "delivery_DK6400": "TO-QUOTE"}}
GEOM = {
    "A4-80 M5 x10 (baseline)": "no change",
    "A4-100 M5 x10": "no CAD change (screw grade only)",
    "IN718 M5 x10": "no CAD change; HW-101 becomes a drawn special part (IN718, ageing, thread rolling, cleanliness)",
    "A4-80 M6 x10": ("TC-01: 10x d6.6 holes (match-drilled), d11.5 flat spot faces at r 31.225 (wall 2.600 nominal, 2.577 at the drawing limit; "
                     "depth 0.525 at the screw axis); TC-02: 10x M6-6H taps, drill 5.0 x 9.0, full thread 8.0 (engagement 7.375 with M6 x 10); the "
                     "tap-to-cavity walls drop by the 0.5 mm larger major radius: 1.906 -> about 1.41 mm at az 18 / 342 (torch passage) and 2.719 -> "
                     "about 2.22 at az 126 (CAD probe of the M5 set, checks/test_interim352b_v1.json; TO-PROBE on the M6 set); FD-04: head dk 10.5 "
                     "-> foil and upper clip top trimmed 0.5 mm more (z_cap = screw axis - 5.25 - 1.0; RC-04 re-check); GSE fitting plugs for d6.6 "
                     "holes; ISO 7380 M6 head k 3.3 (0.55 taller, minus the 0.088 deeper flat)"),
    "A4-80 12x M5": ("NO UNIFORM PATTERN FITS: at a 30 deg pitch no phase keeps every screw >= 16-18 deg from both the torch passage (0 deg) and the "
                     "Pc passage (142 deg) (the 10-pitch set at 18 + 36k already has the minimum walls 1.906 mm at 18 deg from the torch and "
                     "2.719 mm at 16 deg from the Pc, CAD probe; jfwd_v352_v1 O2 note); a non-uniform pattern breaks equal load sharing; "
                     "+2 TC-01 holes / spot faces (ligament w 10.31 mm at the bore vs 12.49 for 10), +2 TC-02 taps, +2 O-ring passage holes "
                     "for the S01 / S02 assembly (2 more GSE fitting plugs, same item C callout and fitting aid)")}
TORQUE = {"A4-80 M5 x10 (baseline)": "3.0 N m (F_nom 3000 N, K 0.20 ASSUMED, J-F1 TO-DO)",
          "A4-100 M5 x10": "3.0 N m kept (same band); K TO-VERIFY by J-F1 on the flight lot",
          "IN718 M5 x10": "3.0 N m for the same band; IN718 on 6061 with LOCTITE 243: K TO-VERIFY by J-F1 (new lot, new pair)",
          "A4-80 M6 x10": "3.6 N m for the same band (0.20 x 3000 x 6 mm); K TO-VERIFY by J-F1 (M6 into 6061)",
          "A4-80 12x M5": "3.0 N m (as baseline)"}
CORR = {"A4-80 M5 x10 (baseline)": "taps on the DRY side (forward of both bore seals, CAD): not N2O-wetted; A4 / 6061 couple sealed by the locker; as v3.5.2",
        "A4-100 M5 x10": "as baseline (same alloy family, A4)",
        "IN718 M5 x10": "as baseline for wetting (dry side); IN718 / 6061 couple: both cathodic to Al like A4 (no change in kind); oxygen service not "
                        "a driver (dry side); new material on the engine: Combustion's compatibility list TO-UPDATE",
        "A4-80 M6 x10": "as baseline, provided the M6 taps keep a positive wall to the torch and Pc passages (TO-PROBE): a breakthrough would wet the "
                        "tap with torch gas and the locker would then be in oxygen service",
        "A4-80 12x M5": "as baseline; the 12-pitch clash with the torch / Pc passages is a wetting risk (see geometry)"}

opts = {}
for nm, (size, grade, n, d_sf) in OPT.items():
    V = F_ABS / n
    t1 = tc01_cells(V, n, size, d_sf)
    t_nom = t1["nominal_wall"]["t_wall_mm"]
    opts[nm] = {"screw_FA1S_5020A": screw_cells(size, grade, n), "TC01": t1, "TC02": tc02_cells(V, n, size, t_nom, 10.0, F_FA1S_PRE),
                "no_slack": {k: {"seat_line": {kk: RX["c_screw_options_no_slack"][k]["seat_line"][kk] for kk in ("n_unseated", "F_S_min_N", "max_wall_set_um", "F_S_max_N", "fibre_over_Rp_max")},
                                 "ring_line": {kk: RX["c_screw_options_no_slack"][k]["ring_line"][kk] for kk in ("n_unseated", "F_S_min_N", "max_wall_set_um")},
                                 "tag": RX["c_screw_options_no_slack"][k]["tag"]} for k in RELAX_KEY[nm]},
                "availability": AVAIL[nm], "CAD_geometry": GEOM[nm], "mass": MASS[nm], "torque_tension": TORQUE[nm], "corrosion_oxygen": CORR[nm],
                "BOM": {"A4-80 M5 x10 (baseline)": "ENG-HW-101 ISO 7380-1 M5 x 10 A4-80 x10 (supplier TO-SELECT: BUMAX 88-MKT M5 x 10 candidate)",
                        "A4-100 M5 x10": "ENG-HW-101 grade A4-100: no part",
                        "IN718 M5 x10": "ENG-HW-101 -> special part ENG-HW-101-IN718 (drawing, AMS 5662/5663, x10 + spares)",
                        "A4-80 M6 x10": "ENG-HW-101 -> ISO 7380 M6 x 10 A4-80 x10 (BUMAX 88-MKT M6 x 10 candidate); TC-01 / TC-02 / FD-04 drawings; GSE plugs d6.6",
                        "A4-80 12x M5": "ENG-HW-101 qty 12; TC-01 / TC-02 drawings (pattern); GSE plugs x12"}[nm]}
SHOULDER = ("NONE FITS: the stock full-body option, ISO 7379 hexagon socket shoulder screw with an M5 thread (d_s 6.5, dk max 10, k max 4.5, thread "
            "b max 9.75, nominal shoulder lengths 10-120; fasten.it ISO 7379 table, ISO 7379:1983, https://fasten.it/en/norms/norm/iso_7379, accessed "
            "2026-10-20), breaks the 1.0 mm FD-04 envelope (dk / 2 + 1.0 = 6.0 > 5.75 below the screw axis) and its shortest 10 mm shoulder through "
            "the 2.688 wall puts the thread end about 19.5 mm into TC-02 (r ~ 9 vs the 9.0 mm tap to r 19.6 now) through the TC-02 cavities; it also "
            "clamps on its shoulder end, not on TC-01; no part-threaded M5 in a ~10 mm length was found (short ISO 4762 / 7380 M5 are threaded to the head)")
# ---- fix (ii) knock-ons at the first all-seated band (seat-line bound): installation yield, TC-02 internal thread at the run's F_S max (6061 at
#      the TC-02 tap-zone maximum 119.6 C, jfwd_variant_v352_v2 row maxima), flat-seat head bearing at the TC-01 158.0 C maximum, torque
T02_MAX, T01_MAX = 119.6, 158.0
A_HEAD = math.pi / 4.0 * (TH["M5"]["dk"] ** 2 - TH["M5"]["hole"] ** 2)
An_M5 = strip_area(TH["M5"], 7.287 - 0.5)
kno = {}
RP20 = {"A4-80 M5 x10 (baseline)": 600.0, "A4-100 M5 x10": 800.0, "IN718 M5 x10": tab("IN718", "Fty", 20.0)}
for nm, v in RX["fix_ii_higher_preload"].items():
    b = v["seat_line"]["first_all_seated_band"]
    if not b:
        kno[nm] = "no all-seated band up to F_min 12250 N"
        continue
    Fsy2, Fsu2 = 0.577 * tab("AL6061-T6", "Fty", T02_MAX), MAT["AL6061-T6"]["Fsu_over_Ftu"]["v"] * tab("AL6061-T6", "Ftu", T02_MAX)
    tau = b["F_S_max_N"] / An_M5
    p = b["F_S_max_N"] / A_HEAD
    Fb = MAT["AL6061-T6"]["Fbry_over_Fty_eD2"]["v"] * tab("AL6061-T6", "Fty", T01_MAX)
    kno[nm] = {"band_N": [b["F_min_N"], b["F_max_N"]], "F_nom_N": b["F_nom_N"], "torque_Nm_K0.20": b["torque_Nm_K0p20"],
               "install_F_max_over_proof_Rp20_As": round(b["F_max_N"] / (RP20[nm] * 14.18), 3),
               "TC02_thread_at_F_S_max": {"F_S_max_N": b["F_S_max_N"], "A_n_mm2": round(An_M5, 1), "tau_MPa": round(tau, 1), "MS_y": ms(Fsy2, tau), "MS_u": ms(Fsu2, tau)},
               "flat_seat_head_bearing": {"p_MPa": round(p, 1), "Fbry_158C_MPa": round(Fb, 1), "MS_y": ms(Fb, p)},
               "screw_set_um": b["max_screw_set_um"], "wall_set_um": b["max_wall_set_um"], "seat_line_P_Q_over_Fty_max": b["max_seat_over_Fty"]}
res = {"id": "jfwd_fix_v352", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "inputs": {"jfwd_relax_v352_v3.json": sha(RELAX), "jfwd_seat_v352_v1.json": sha(SEAT), "screw_bend.json": sha(SB), "jfwd_v352.py": sha(J / "jfwd_v352.py"),
                  "V_abs_N": round(F_ABS / 10, 1), "V_gauge_N": round(F_G / 10, 1), "arm_sharp_mm": round(ARM_SHARP, 4), "arm_gov_mm": round(ARM_GOV, 4),
                  "N_included_N": N_INC, "T_C": T,
                  "Al_allowables_MPa": {"Fty": round(Fty, 1), "Ftu": round(Ftu, 1), "Fbry": round(Fbry, 1), "Fbru": round(Fbru, 1), "Fsy": round(Fsy, 1), "Fsu": round(Fsu_al, 1)},
                  "spot_face_volumes_mm3": {"d10.5": round(V_SF105, 2), "d11.5": round(V_SF115, 2)}, "screw_mass_g_A4": {"M5x10": round(m5, 3), "M6x10": round(m6, 3)}},
       "options": opts, "shoulder_or_part_threaded": SHOULDER,
       "slack_fixes": {"i_select_fit": RX["fix_i_select_fit_gap_cap"], "ii_higher_preload": {k: {b: v[b]["first_all_seated_band"] for b in v} for k, v in RX["fix_ii_higher_preload"].items()},
                       "ii_knock_ons_seat_line_band": kno,
                       "info": RX["info_sensitivities"], "break_even_k_sh": RX["break_even_k_sh"], "screw_set_bounds": RX["screw_set_bounds"]}}
s = json.dumps(res, indent=1, default=float)
OUT.write_text(s)
print(OUT.name, hashlib.sha256(s.encode()).hexdigest()[:16])
print("arm sharp", round(ARM_SHARP, 4), "gov", round(ARM_GOV, 4), "N_inc", N_INC, "V", round(F_ABS / 10, 1), round(F_G / 10, 1))
for nm, o in opts.items():
    sc = o["screw_FA1S_5020A"]
    r = sc["rows"]
    t1 = o["TC01"]
    t2 = o["TC02"]
    print(f"== {nm}: screw omitted {sc['governing']:+.3f} (gauge {sc['gauge_governing']:+.3f}) included {sc['included_at_governing_row']:+.3f} | "
          f"sharp {r['CALC_abs_3888.1|arm_sharp_info']['MS_omitted_governing']:+.3f}/{r['CALC_abs_3888.1|arm_sharp_info']['MS_included_info']:+.3f} "
          f"arm+0.4 {r['CALC_abs_3888.1|arm_+0.4_sens']['MS_omitted_governing']:+.3f}/{r['CALC_abs_3888.1|arm_+0.4_sens']['MS_included_info']:+.3f} "
          f"arm+0.6 {r['CALC_abs_3888.1|arm_+0.6_sens']['MS_omitted_governing']:+.3f}/{r['CALC_abs_3888.1|arm_+0.6_sens']['MS_included_info']:+.3f} | eq23 {r['CALC_abs_3888.1|arm_+0.2_governing']['MS_eq23_omitted_info_Fbu_1.70Ftu_geometry_only']:+.3f}")
    for wn in ("nominal_wall", "drawing_limit_wall"):
        w = t1[wn]
        print(f"   TC01 {wn:18s} t {w['t_wall_mm']:.3f} L {w['L_eff_bearing_mm']:.3f} brg {w['hole_bearing']['MS_y']:+.3f}/{w['hole_bearing']['MS_u']:+.3f} "
              f"so {w['shear_out']['MS_y']:+.3f} Pm {w['net_section']['MS_y']:+.3f} PmPb {w['ligament_PmPb']['MS_y']:+.3f}/{w['ligament_PmPb']['MS_u']:+.3f} "
              f"neu {w['hole_edge_neuber_info']['MS_strain']:+.3f}")
    print(f"   TC02 L_e {t2['L_e_mm']} tap brg {t2['tapped_thread_bearing']['MS_y']:+.3f}/{t2['tapped_thread_bearing']['MS_u']:+.3f} thread shear "
          f"{t2['internal_thread_shear_at_F_max_thermal']['MS_y']:+.3f}/{t2['internal_thread_shear_at_F_max_thermal']['MS_u']:+.3f} so-g2 {t2['shear_out_to_g2']['MS_y']:+.3f} "
          f"| mass {o['mass']['delta_g']} g | {o['availability']['status']}")
    for k, v in o["no_slack"].items():
        print(f"   slack {k}: seat {v['seat_line']['n_unseated']} unseated min {v['seat_line']['F_S_min_N']} | ring {v['ring_line']['n_unseated']} min {v['ring_line']['F_S_min_N']} ({v['tag']})")
print("== fix (ii) knock-ons (seat-line band)")
for k, v in kno.items():
    print("  ", k, json.dumps(v))
