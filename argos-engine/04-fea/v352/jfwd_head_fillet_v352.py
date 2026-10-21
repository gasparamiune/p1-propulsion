"""J-FWD ENG-HW-101-IN718 head-to-shank undercut fillet: a static row and an LCF row on the FE moment at the head end (lead 17:55:55Z F3
ADD: 'the screw's own head-to-shank undercut fillet needs a static row and an LCF row on the FE moment at the head end, with a sourced Kt
cited by page (TO-SOURCE).  Time-box it like the MJ box.  If it governs over the thread root, say so.').  Mechanical, 2026-10-20, v1.
v2 (2026-10-21; v1 54404487e7c42a74 / json 337883c3f2076a32 kept as jfwd_head_fillet_v352_v1.py): re-run on relax v8 / rows v8 (lead 2026-10-21T05:50:45Z re-map brief R1-R8: FEA3D-2's FINAL envelope v6 43a5d78b67c615fc with the input record jfwd_v7inputs_cD_v352.json 5a41c8d74897bdda; instances add (b1), (b1) rep, (b2'), (cD));
the head-end moment of every shank.json instance ((b2), (b1), (b2'), (cD), and the repeats) is read from its own shank.json; LCF v3.
CALC on SIM temperatures and FE section resultants; DERIVED unless tagged; software estimate, not a test; negatives SHOWN AS FOUND.

Geometry (F3 ADOPTED): undercut fillet r 0.2-0.3 into the head, entirely above the bearing face; pilot 5.15 h9 (5.120-5.150) x 0.25-0.30;
da 5.55-5.80; head dk 9.14-9.5 (ISO 7380-1 M5, the rows' fasten.it basis).  The fillet root section is the pilot, d_f = 5.120 (h9 minimum).
Loads, per state and history (relax v7 / rows v7 histories on FEA3D's ADOPTED envelope v3 0872de4ea7e3601d): the FE section resultants at
the HEAD END: M_he = the largest |M| over the screw sections at x' >= 30.9 mm (the seat, i.e. the head bearing face, is at x' 31.313):
compare.json 'screw_sections' x' 31.0 for js5 (patch (a)'s global columns) and (a) / (a') / (a'') (patch columns); shank.json x' 31.0 and
31.25 for (b2) and '(b2) rep'.  N = the rows' section force N_section_max (the largest over the shank; conservative at the head end).  Both
are scaled to IN718 exactly as the rows' screw-fibre row (N x N_IN718 / N_head; M x tilt ratio x max(1, Fc_IN718 / Fc_FE)) at the J-F1 cap
3750 N (GOVERNING, lead F1) and 4096 N (information).  The cold end of the firing range is the lowest PRELOAD section force and head-end
moment x F_V / 3750 (the rows' convention).  The FE has no spring, no pilot and no fillet: its head-end resultants are carried to the
route-(i) screw over the solid spring (a flat washer) - ASSUMED.
Kt (the time-boxed search, 18:12-18:25Z, closed as below):
  QUOTED (web source, BOOK PAGE TO-SOURCE): stepped round bar with a shoulder fillet, Kt = C1 + C2 (2h/D) + C3 (2h/D)^2 + C4 (2h/D)^3 for
  2.0 <= h/r <= 20.0, tension and bending coefficients as printed on AMESweb 'Shoulder fillet in a stepped circular shaft'
  (https://amesweb.info/StressConcentrationFactor/SteppedShaftWithShoulderFillet.aspx, accessed 2026-10-20, read twice), which cites
  W. D. Pilkey, Formulas for Stress, Strain, and Structural Matrices, 2nd ed., John Wiley & Sons, 2005 (no chart, table or page given on the
  web page: the page number in Pilkey 2005 is TO-SOURCE).  h = (D - d) / 2 (ASSUMED: the page does not define h); the page renders the cubic
  as '(C3 (2h/D))^2 + (C4 (2h/D))^3': the standard form is quoted and the page's literal reading is a sensitivity (it gives the larger Kt).
  NOT SOURCED: the bolt-head (T-head) loading, the head-bearing reaction next to the fillet, which the stepped-bar fit does not contain (it can
  be unconservative there).  Found, not usable: F. I. Baratta, 'Stress Concentration Factors in T-Heads', AMRA TR 66-36, U.S. Army Materials
  Research Agency, Nov 1966 (DTIC AD0649808; WebFetch text of a scan), Heywood's empirical formula (R. B. Heywood, Designing by
  Photoelasticity, Chapman & Hall, 1952, p. 178) as its Eq. 9-10 (p. 5): two-dimensional, validity D/d >= 2.0 and head depth h/d >= 3.0
  (the ISO 7380-1 head here: D/d 1.78-1.86, head height about 0.54 d): outside its range, and the scan's equation text is not legible
  (TO-VERIFY).  Not reachable: fchartsoftware.com and the Kyutech repository PDFs (Noda et al.) and apps.dtic.mil by curl (proxy 403, not
  retried), sack.de (robots).  Roark 8th ed. bending fit (via L. Rogers and R. A. Fleming, ASEE Midwest 2025, peer.asee.org/57831.pdf):
  0.25 <= h/r <= 2.0 only, not applicable (h/r here 6.6-11.0).
  So the rows quote the stepped-bar Kt AND the BREAK-EVEN Kt at which the fillet would govern over the thread root and at which it reaches
  N_allow 50 (MS 0).
Static row: net section at the fillet root: nominal fibre S = N / A_f + M / Z_f at each hot state (SOAK70 / SOAK / SOAK52, and FA1S) against
  IN718 Fty(T) (MS_y) and Ftu(T) (MS_u) at the rows' screw temperature (engmat SMC-045 minima), no Kt (ductile; the rows' screw-fibre
  convention); the local elastic peak Kt_t S_ax + Kt_b S_b and its Neuber strain (FEA3D's curve, n 15 / 30) as information.
LCF row: the screw LCF v2 method unchanged (183 (1)(c): N_allow = min(N_f(de) / 20, N_f(2 de)) >= 50; Neuber with Kf; Manson universal slopes
  on the AMS 5663 minimum RA 0.15, Su = Ftu(T); Masing for the cyclic range) with Kf = Kt (notch sensitivity q = 1, ASSUMED: no credit),
  the tension and bending peaks combined as Kt_eff = (Kt_t S_ax + Kt_b S_b) / (S_ax + S_b); ranges (i) per firing (cold preload -> hot soak),
  (ii) assembly from zero (monotonic), (ii') stable re-assembly (information), as the thread-root rows.  The functions are copied from
  jfwd_screw_lcf_v352.py and one LCF v2 thread-root row is reproduced exactly before use.
Comparison: the thread-root LCF v2 rows (Kf 3.0 on A_s 14.18 / Z_3 6.373 at the max-moment section) at the same preload: the fillet governs
  where its N_allow is the lower."""
import importlib.util, json, math, hashlib, time
from pathlib import Path
import numpy as np

T0 = time.time()
J = Path("/home/claude/work/mechanical/v352/jfwd")
OUT = J / "jfwd_head_fillet_v352_v2.json"
ROWS_PY, ROWS7J = J / "jfwd_in718_rows_v352.py", J / "jfwd_in718_rows_v352_v8.json"
LCF_PY, LCFJ = J / "jfwd_screw_lcf_v352.py", J / "jfwd_screw_lcf_v352_v3.json"
SHA = {"rows_py": "62fd8d590ade2875", "rows7j": "af072cc2e70711ca"}
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
assert sha(ROWS_PY) == SHA["rows_py"] and sha(ROWS7J) == SHA["rows7j"], "rows v8"
_sw = importlib.util.spec_from_file_location("jfwd_in718_rows_v352_v8", str(ROWS_PY))
W = importlib.util.module_from_spec(_sw)
_sw.loader.exec_module(W)
R, IN = W.R, W.IN
rws = json.loads(ROWS7J.read_text())
lcf = json.loads(LCFJ.read_text())
assert rws["version"] == "v8" and lcf["version"] == "v3"
FV0, FVMAX = W.FV0, W.FVMAX
assert FV0 == 3750.0 and FVMAX == 4096.0

# ---- geometry (F3)
D_HEAD = (W.DK_MIN, W.DK_MAX)          # 9.14 / 9.5
D_PILOT = (5.120, 5.150)               # 5.15 h9
R_FIL = (0.2, 0.3)
D_F = D_PILOT[0]
A_F, Z_F = math.pi * D_F ** 2 / 4.0, math.pi * D_F ** 3 / 32.0
A_S, Z_3 = lcf["inputs"]["A_s_mm2"], lcf["inputs"]["Z_3_mm3"]


def kt_pilkey(D, d, r, mode, literal=False):
    h = (D - d) / 2.0
    x, t = h / r, 2.0 * h / D
    assert 2.0 <= x <= 20.0, (D, d, r, x)
    sx = math.sqrt(x)
    if mode == "tension":
        C = (1.200 + 0.860 * sx - 0.022 * x, -1.805 - 0.346 * sx - 0.038 * x, 2.198 - 0.486 * sx + 0.165 * x, -0.593 - 0.028 * sx - 0.106 * x)
    else:
        C = (1.232 + 0.832 * sx - 0.008 * x, -3.813 + 0.968 * sx - 0.260 * x, 7.423 - 4.868 * sx + 0.869 * x, -3.839 + 3.070 * sx - 0.600 * x)
    if literal:
        return C[0] + C[1] * t + (C[2] * t) ** 2 + (C[3] * t) ** 3
    return C[0] + C[1] * t + C[2] * t ** 2 + C[3] * t ** 3


KT = {}
for D in D_HEAD:
    for d in D_PILOT:
        for r in R_FIL:
            for mode in ("tension", "bending"):
                KT[f"D{D}|d{d}|r{r}|{mode}"] = {"standard": round(kt_pilkey(D, d, r, mode), 4), "page_literal_sensitivity": round(kt_pilkey(D, d, r, mode, True), 4),
                                                "h_over_r": round((D - d) / 2.0 / r, 3), "two_h_over_D": round((D - d) / D, 4)}
KT_Q = {m: max(v["standard"] for k, v in KT.items() if k.endswith(m) and "|r0.2|" in k) for m in ("tension", "bending")}
KT_LIT = {m: max(v["page_literal_sensitivity"] for k, v in KT.items() if k.endswith(m) and "|r0.2|" in k) for m in ("tension", "bending")}
KT_R03 = {m: max(v["standard"] for k, v in KT.items() if k.endswith(m) and "|r0.3|" in k) for m in ("tension", "bending")}

# ---- the LCF v2 method (copied from jfwd_screw_lcf_v352.py; reproduced below)
lsrc = LCF_PY.read_text()
for frag in ("RA = 0.15", "def us_de(N, Su, E):\n    return 3.5 * Su / E * N ** -0.12 + D ** 0.6 * N ** -0.6", "N_REQ, FAC_N, FAC_E = 50, 20.0, 2.0", "NS = (15, 30)",
             "e = s / E + 2 * 0.002 * (s / (2 * Fty)) ** n", "e = s / E + 0.002 * (s / Fty) ** n"):
    assert frag in lsrc, frag
RA = 0.15
DD = math.log(1.0 / (1.0 - RA))
NS = (15, 30)
N_REQ, FAC_N, FAC_E = 50, 20.0, 2.0


def us_de(N, Su, E):
    return 3.5 * Su / E * N ** -0.12 + DD ** 0.6 * N ** -0.6


def us_N(de, Su, E):
    lo, hi = 0.0, 12.0
    if us_de(10 ** hi, Su, E) > de:
        return float("inf")
    if us_de(1.0, Su, E) < de:
        return 0.0
    for _ in range(200):
        m = 0.5 * (lo + hi)
        lo, hi = (m, hi) if us_de(10 ** m, Su, E) > de else (lo, m)
    return 10 ** (0.5 * (lo + hi))


def neuber_cyc(dS, E, Fty, n, kf):
    tgt = (kf * dS) ** 2 / E
    lo, hi = 1e-9, kf * dS
    for _ in range(200):
        s = 0.5 * (lo + hi)
        e = s / E + 2 * 0.002 * (s / (2 * Fty)) ** n
        lo, hi = (s, hi) if s * e < tgt else (lo, s)
    return s, s / E + 2 * 0.002 * (s / (2 * Fty)) ** n


def neuber_mono(S, E, Fty, n, kf):
    tgt = (kf * S) ** 2 / E
    lo, hi = 1e-9, kf * S
    for _ in range(200):
        s = 0.5 * (lo + hi)
        e = s / E + 0.002 * (s / Fty) ** n
        lo, hi = (s, hi) if s * e < tgt else (lo, s)
    return s, s / E + 0.002 * (s / Fty) ** n


FUN = {"i_firing": neuber_cyc, "ii_assembly_from_zero": neuber_mono, "ii_stable_reassembly_info": neuber_cyc}
METHODS = tuple(FUN)


def n_allow(S, E, Su, fty, kf, f):
    worst = None
    for n in NS:
        s, e = f(S, E, fty, n, kf)
        Nf, Nf2 = us_N(e, Su, E), us_N(FAC_E * e, Su, E)
        r = {"n": n, "local_sigma_MPa": round(s, 1), "local_de": round(e, 5), "N_f": round(Nf, 1), "N_f_at_2de": round(Nf2, 1),
             "N_allow": round(min(Nf / FAC_N, Nf2), 1)}
        r["MS_cycles_vs_50"] = round(r["N_allow"] / N_REQ - 1.0, 3)
        if worst is None or r["N_allow"] < worst["N_allow"]:
            worst = r
    return worst


def T_of_Fty(fty):
    return float(np.interp(fty, [862.0, 1034.0], [649.0, 20.0]))


import sys
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/04-fea/src")
import engmat
MAT = engmat.MATERIALS["IN718"]
tabm = lambda k, T: float(np.interp(T, MAT[k]["T_C"], MAT[k]["v"])) / 1e6
# reproduce one LCF v2 thread-root row exactly (the governing i_firing at 3750, Kf 3.0)
_g = lcf["governing"]["i_firing|Kf3.0|worst_of_histories|3750"]
_c = lcf["cases"][_g["case"]]
_r = n_allow(_c["range_firing_MPa"], _c["E_MPa"], _c["Su_MPa"], _c["Fty_MPa"], 3.0, neuber_cyc)
assert _r["N_allow"] == _c["i_firing"]["N_allow"] == _g["N_allow"], (_r, _c["i_firing"])
_r2 = n_allow(_c["fibre_hot_MPa"], _c["E_MPa"], _c["Su_MPa"], _c["Fty_MPa"], 3.0, neuber_mono)
assert _r2["N_allow"] == _c["ii_assembly_from_zero"]["N_allow"], (_r2, _c["ii_assembly_from_zero"])


# ---- FE head-end section resultants
def head_end(h, st):
    if R.src_of(h, st)[0] in R.SHANK_MOMENTS:          # v2: every shank.json instance (relax v8 SHANK_MOMENTS)
        hp, step = R.src_of(h, st)
        secs = R._SH[hp]["steps"][step]["sections"]
        cand = [(abs(q["M"]), q["x"], q["N"]) for q in secs if q["x"] >= 30.9]
        src = f"shank.json {step}"
    else:
        ss = W.cmp_side(h, st)["screw_sections"]
        cand = [(abs(v["M"]), float(k[1:]), v["N"]) for k, v in ss.items() if float(k[1:]) >= 30.9]
        src = "compare.json " + ("patch_a global_same_sets" if h == "js5" else "patch") + f" {st}"
    m, x, n = max(cand)
    return m, x, n, src


STATES_LCF = tuple(R.SOAKS)
STATES_STATIC = tuple(R.SOAKS) + ("FA1S",)
LBL = R.LABEL


def loads(FV):
    pre = R.HISTS["PRELOAD"]
    Nsec_pre = min(pre[h]["N_section_max_N"] for h in R.H_at("PRELOAD")) * FV / FV0
    Mhe_pre = min(head_end(h, "PRELOAD")[0] for h in R.H_at("PRELOAD")) * IN.tilt_ratio * FV / FV0
    out = {}
    for st in STATES_STATIC:
        Ts = W.CELLS[st]["SCREW"]["T_C"]
        fty, ftu, E = R.tab("IN718", "Fty", Ts), R.tab("IN718", "Ftu", Ts), R.tab("IN718", "E", Ts)
        for h in R.H_at(st):
            x = R.HISTS[st][h]
            Ni = W.n_in(st, h, FV)
            Nsec = x["N_section_max_N"] * Ni / x["N_head_N"]
            Fc_in = x["seat_radial_N"] + (Ni - x["N_head_N"]) * R.K_C / (R.K_C + R.K_SH_JS5)
            fac = IN.tilt_ratio * max(1.0, Fc_in / x["seat_radial_N"])
            mhe, xm, nfe, src = head_end(h, st)
            out[f"{st}|{LBL[h]}"] = {"T_C": Ts, "Fty_MPa": fty, "Ftu_MPa": ftu, "E_MPa": E, "N_IN718_N": Ni, "N_section_N": Nsec,
                                     "M_head_end_FE_A4-80_Nmm": mhe, "M_head_end_x_mm": xm, "M_head_end_src": src, "M_max_FE_A4-80_Nmm": x["M_max_Nmm"],
                                     "M_head_end_IN718_Nmm": mhe * fac, "M_max_IN718_Nmm": x["M_max_Nmm"] * fac,
                                     "Nsec_pre_N": Nsec_pre, "M_he_pre_Nmm": Mhe_pre}
    return out


LD = {f"{FV:.0f}": loads(FV) for FV in (FV0, FVMAX)}
# the thread-root fibre of the rows is reproduced from the same loads (ties the scaling to rows v7)
for st in STATES_LCF:
    for k, v in LD["3750"].items():
        if not k.startswith(st + "|"):
            continue
        h = k.split("|", 1)[1]
        ref = rws["states"][st]["rows"]["3750"]["screw_fibre_soak"]["per_history"][h]
        f = v["N_section_N"] / W.A_S + v["M_max_IN718_Nmm"] / W.Z_3
        assert abs(f - ref["fibre_MPa"]) < 0.11 and abs(v["M_max_IN718_Nmm"] - ref["M_Nmm"]) < 0.11, (k, f, ref["fibre_MPa"])
        assert abs(v["Fty_MPa"] - ref["Fty_IN718_MPa"]) < 0.11
assert abs(R.tab("IN718", "Ftu", 127.1) - tabm("Ftu", 127.1)) < 0.5 and abs(R.tab("IN718", "E", 127.1) - tabm("E", 127.1)) < 50.0


def fillet_rows(FVk, kt_t, kt_b):
    rows = {}
    for k, v in LD[FVk].items():
        st = k.split("|")[0]
        Sax, Sb = v["N_section_N"] / A_F, v["M_head_end_IN718_Nmm"] / Z_F
        S = Sax + Sb
        Spre = v["Nsec_pre_N"] / A_F + v["M_he_pre_Nmm"] / Z_F
        kt_eff = (kt_t * Sax + kt_b * Sb) / S
        peak = kt_t * Sax + kt_b * Sb
        loc = [W.neuber(peak, v["E_MPa"], v["Fty_MPa"], n) for n in (15, 30)]
        r = {"T_C": v["T_C"], "N_section_N": round(v["N_section_N"], 1), "M_head_end_IN718_Nmm": round(v["M_head_end_IN718_Nmm"], 1),
             "M_head_end_x_mm": v["M_head_end_x_mm"], "M_head_end_src": v["M_head_end_src"],
             "S_axial_MPa": round(Sax, 1), "S_bending_MPa": round(Sb, 1), "S_nominal_MPa": round(S, 1),
             "Fty_MPa": round(v["Fty_MPa"], 1), "Ftu_MPa": round(v["Ftu_MPa"], 1),
             "static_MS_y_net": round(v["Fty_MPa"] / S - 1.0, 3), "static_MS_u_net": round(v["Ftu_MPa"] / S - 1.0, 3),
             "local_elastic_peak_MPa_info": round(peak, 1), "Kt_eff": round(kt_eff, 4),
             "local_neuber_strain_n15_n30_info": [round(x[1], 5) for x in loc], "local_yield_on_loading_info": bool(peak > v["Fty_MPa"]),
             "thread_root_nominal_fibre_MPa": round(v["N_section_N"] / A_S + v["M_max_IN718_Nmm"] / Z_3, 1)}
        if st in STATES_LCF:
            Su, E, fty = v["Ftu_MPa"], v["E_MPa"], v["Fty_MPa"]
            r["cold_fibre_MPa"] = round(Spre, 1)
            r["range_firing_MPa"] = round(S - Spre, 1)
            for lab in METHODS:
                Sr = S - Spre if lab == "i_firing" else S
                r[lab] = n_allow(Sr, E, Su, fty, kt_eff, FUN[lab])
        rows[k] = r
    return rows


def lcf_min(rows, lab):
    k = min((k for k in rows if lab in rows[k]), key=lambda k: rows[k][lab]["N_allow"])
    return k, rows[k][lab]["N_allow"]


def kt_scale_for(target, FVk, lab):
    """the factor s on (Kt_t, Kt_b) = s x (quoted) at which the fillet's worst N_allow (method lab) falls to target"""
    f = lambda s: lcf_min(fillet_rows(FVk, s * KT_Q["tension"], s * KT_Q["bending"]), lab)[1]
    lo, hi = 0.2, 6.0
    if f(hi) > target:
        return None
    if f(lo) < target:
        return 0.0
    for _ in range(40):
        m = 0.5 * (lo + hi)
        lo, hi = (m, hi) if f(m) > target else (lo, m)
    return 0.5 * (lo + hi)


res = {"id": "jfwd_head_fillet_v352", "version": "v2", "date": "2026-10-21", "owner": "mechanical", "basis": __doc__.strip(),
       "status": "CALC; Kt basis WEB-SOURCED, BOOK PAGE TO-SOURCE; bolt-head (T-head) loading NOT SOURCED; negatives SHOWN AS FOUND",
       "inputs": {"rows_v8_module": {"path": str(ROWS_PY), "sha256_16": sha(ROWS_PY)}, "rows_v8_json": {"path": str(ROWS7J), "sha256_16": sha(ROWS7J)},
                  "relax_v8_module": {"path": str(J / "jfwd_relax_v352.py"), "sha256_16": sha(J / "jfwd_relax_v352.py")},
                  "screw_lcf_v3": {"path": str(LCF_PY), "sha256_16": sha(LCF_PY), "json": str(LCFJ), "json_sha256_16": sha(LCFJ)},
                  "fea3d_soak_envelope": rws["inputs"]["fea3d_soak_envelope"],
                  "fe_sections": "compare.json screw_sections (x' 28.7-31.0) and the shank.json sections of (b2), (b1), (b2'), (cD) (x' 26.4-31.25); seat x' 31.313"},
       "geometry_F3": {"pilot_d_mm": D_PILOT, "fillet_r_mm": R_FIL, "head_dk_mm": D_HEAD, "d_f_used_mm": D_F,
                       "A_f_mm2": round(A_F, 3), "Z_f_mm3": round(Z_F, 3), "thread_A_s_mm2": A_S, "thread_Z_3_mm3": Z_3,
                       "section_ratio_axial_A_s_over_A_f": round(A_S / A_F, 4), "section_ratio_bending_Z_3_over_Z_f": round(Z_3 / Z_F, 4)},
       "Kt_search_time_box": {"window": "18:12-18:25Z (2026-10-20)",
                              "quoted": {"source": "AMESweb 'Shoulder fillet in a stepped circular shaft', https://amesweb.info/StressConcentrationFactor/"
                                                   "SteppedShaftWithShoulderFillet.aspx (accessed 2026-10-20), citing W. D. Pilkey, Formulas for Stress, "
                                                   "Strain, and Structural Matrices, 2nd ed., Wiley, 2005",
                                         "page": "TO-SOURCE (not given on the web page)", "form": "Kt = C1 + C2 (2h/D) + C3 (2h/D)^2 + C4 (2h/D)^3, 2 <= h/r <= 20",
                                         "h_definition": "h = (D - d) / 2 ASSUMED (not defined on the page)",
                                         "status": "WEB-SOURCED; book page TO-SOURCE; geometry = stepped bar, not a bolt head"},
                              "not_sourced": "bolt-head (T-head) loading: the head-bearing reaction next to the fillet",
                              "found_not_usable": [
                                  "F. I. Baratta, Stress Concentration Factors in T-Heads, AMRA TR 66-36, Nov 1966, DTIC AD0649808: Heywood's formula "
                                  "(Designing by Photoelasticity, 1952, p. 178) as Eq. 9-10 (p. 5); 2-D; valid D/d >= 2.0 and h/d >= 3.0 (here D/d 1.78-1.86, "
                                  "head height ~0.54 d); scan text not legible (TO-VERIFY)",
                                  "Roark 8th ed. (Young, Budynas, Sadegh 2011) bending fit via Rogers & Fleming, ASEE Midwest 2025 (peer.asee.org/57831.pdf): "
                                  "0.25 <= h/r <= 2.0 only (here 6.6-11.0)"],
                              "not_reachable": ["fchartsoftware.com (curl: proxy 403)", "kyutech.repo.nii.ac.jp PDFs, Noda et al. (curl: proxy 403)",
                                                "apps.dtic.mil PDF by curl (proxy 403)", "sack.de (robots)"],
                              "closed": "PARTLY SOURCED: stepped-bar Kt quoted (web source, page TO-SOURCE); the bolt-head factor is NOT SOURCED; the "
                                        "break-even Kt below says how far the quoted Kt may be wrong before the fillet governs"},
       "Kt_table": KT, "Kt_quoted_r0.2": KT_Q, "Kt_page_literal_r0.2_sensitivity": KT_LIT, "Kt_r0.3_info": KT_R03}
ROWS = {}
for FVk in ("3750", "4096"):
    for tag, (kt, kb) in (("quoted_r0.2", (KT_Q["tension"], KT_Q["bending"])), ("page_literal_r0.2", (KT_LIT["tension"], KT_LIT["bending"])),
                          ("r0.3_info", (KT_R03["tension"], KT_R03["bending"]))):
        ROWS[f"{FVk}|{tag}"] = fillet_rows(FVk, kt, kb)
res["rows"] = ROWS
# governing and comparison with the thread root (LCF v2 at the same preload, Kf 3.0)
cmpr = {}
for FVk in ("3750", "4096"):
    rq = ROWS[f"{FVk}|quoted_r0.2"]
    ks = min(rq, key=lambda k: rq[k]["static_MS_y_net"])
    cmpr[FVk] = {"column": "GOVERNING (J-F1 cap)" if FVk == "3750" else "INFORMATION (superseded maximum)",
                 "static": {"case": ks, "MS_y_net": rq[ks]["static_MS_y_net"], "MS_u_net": rq[ks]["static_MS_u_net"], "S_nominal_MPa": rq[ks]["S_nominal_MPa"],
                            "thread_root_fibre_same_case_MPa": rq[ks]["thread_root_nominal_fibre_MPa"],
                            "rows_v8_screw_fibre_MS_y_min": min(rws["states"][st]["rows"][FVk]["screw_fibre_soak"]["MS_y_fibre"] for st in STATES_LCF)}}
    for lab in METHODS:
        kf, nf = lcf_min(rq, lab)
        kl, nl = lcf_min(ROWS[f"{FVk}|page_literal_r0.2"], lab)
        g = lcf["governing"][f"{lab}|Kf3.0|worst_of_histories|{FVk}"]
        cmpr[FVk][lab] = {"fillet_case": kf, "fillet_N_allow": nf, "fillet_MS": round(nf / N_REQ - 1.0, 3), "fillet_Kt_eff": rq[kf]["Kt_eff"],
                          "fillet_page_literal_N_allow": nl, "thread_root_case_lcf_v3": g["case"], "thread_root_N_allow": g["N_allow"],
                          "thread_root_MS": g["MS_cycles_vs_50"], "fillet_governs": bool(nf < g["N_allow"])}
        if lab != "ii_stable_reassembly_info":
            s_be = kt_scale_for(g["N_allow"], FVk, lab)
            s_50 = kt_scale_for(float(N_REQ), FVk, lab)
            cmpr[FVk][lab]["break_even_Kt_scale_vs_thread_root"] = None if s_be is None else round(s_be, 3)
            cmpr[FVk][lab]["break_even_Kt_t_Kt_b"] = None if s_be is None else [round(s_be * KT_Q["tension"], 3), round(s_be * KT_Q["bending"], 3)]
            cmpr[FVk][lab]["Kt_scale_at_N_allow_50"] = None if s_50 is None else round(s_50, 3)
            cmpr[FVk][lab]["Kt_t_Kt_b_at_N_allow_50"] = None if s_50 is None else [round(s_50 * KT_Q["tension"], 3), round(s_50 * KT_Q["bending"], 3)]
res["governing_and_thread_root_comparison"] = cmpr
c3 = cmpr["3750"]
gov_any = any(c3[l]["fillet_governs"] for l in ("i_firing", "ii_assembly_from_zero"))
res["verdict"] = (f"At the J-F1 cap 3750 N the fillet root (d 5.120, A {A_F:.2f} mm2, Z {Z_F:.2f} mm3; head-end FE moment, IN718-scaled) carries a nominal "
                  f"fibre of {c3['static']['S_nominal_MPa']} MPa at {c3['static']['case']} (thread root of the same case {c3['static']['thread_root_fibre_same_case_MPa']} MPa): "
                  f"static net-section MS_y {c3['static']['MS_y_net']:+.3f}, MS_u {c3['static']['MS_u_net']:+.3f} (the thread-root screw-fibre MS_y is "
                  f"{c3['static']['rows_v8_screw_fibre_MS_y_min']:+.3f}, rows v8).  LCF on the quoted stepped-bar Kt (r 0.2: Kt_t {KT_Q['tension']:.3f}, Kt_b "
                  f"{KT_Q['bending']:.3f}; Kf = Kt): (i) per firing N_allow {c3['i_firing']['fillet_N_allow']} (MS {c3['i_firing']['fillet_MS']:+.3f}) against the "
                  f"thread root {c3['i_firing']['thread_root_N_allow']} (MS {c3['i_firing']['thread_root_MS']:+.3f}); (ii) assembly from zero N_allow "
                  f"{c3['ii_assembly_from_zero']['fillet_N_allow']} (MS {c3['ii_assembly_from_zero']['fillet_MS']:+.3f}) against "
                  f"{c3['ii_assembly_from_zero']['thread_root_N_allow']} (MS {c3['ii_assembly_from_zero']['thread_root_MS']:+.3f}).  The fillet "
                  + ("GOVERNS over the thread root" if gov_any else "does NOT govern over the thread root")
                  + f": it would govern only at Kt x {c3['i_firing']['break_even_Kt_scale_vs_thread_root']} ((i); Kt_t / Kt_b "
                  f"{c3['i_firing']['break_even_Kt_t_Kt_b']}) or x {c3['ii_assembly_from_zero']['break_even_Kt_scale_vs_thread_root']} ((ii)) of the quoted values; "
                  f"it reaches N_allow 50 at Kt x {c3['i_firing']['Kt_scale_at_N_allow_50']} ((i)) / x {c3['ii_assembly_from_zero']['Kt_scale_at_N_allow_50']} ((ii)).  "
                  f"Kt: stepped-bar fit, web-sourced (AMESweb citing Pilkey 2005), page TO-SOURCE; the bolt-head (T-head) loading is NOT SOURCED.")
res["t_run_s"] = round(time.time() - T0, 1)
s = json.dumps(res, indent=1, default=float)
OUT.write_text(s)
print(OUT.name, hashlib.sha256(s.encode()).hexdigest()[:16], res["t_run_s"])
print("KT r0.2", KT_Q, "literal", KT_LIT, "r0.3", KT_R03)
print(res["verdict"])
for FVk in ("3750", "4096"):
    print(FVk, json.dumps(cmpr[FVk]))
for k, v in ROWS["3750|quoted_r0.2"].items():
    print(k, v["S_axial_MPa"], v["S_bending_MPa"], v["S_nominal_MPa"], v["static_MS_y_net"], v["thread_root_nominal_fibre_MPa"], v["M_head_end_IN718_Nmm"], v["M_head_end_x_mm"],
          {lab: (v[lab]["N_allow"], v[lab]["local_de"]) for lab in METHODS if lab in v})
