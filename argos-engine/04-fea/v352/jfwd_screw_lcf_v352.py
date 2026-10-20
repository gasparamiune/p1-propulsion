"""v3.5.2 J-FWD screw LCF row on the IN718 thread-form basis (lead 12:52Z item 2, 13:20Z order; 183 (1)(c) criterion).  Mechanical, 2026-10-20.
v2 (lead 15:37Z order item 1, plan ACCEPTED 15:41Z, basis ruling 15:46Z; v1 9c110e7a8e53b820 / json 1b91bb73d9d34a24 kept as
jfwd_screw_lcf_v352_v1.py): re-run on rows v6 (jfwd_in718_rows_v352_v6.json, on relax v7 and FEA3D's ADOPTED envelope v3
results/v352/jfwd_soak_envelope_v352_v3.json 0872de4ea7e3601d: "worst of the computed histories and edge forms (sharp, R0.2); the contact
solution depends on the predecessor state, so this is the worst computed instance, not a proven bound").  The history classes are read from
the rows: js5, (a), (a'), (a''), (b2) and "(b2) rep" (SOAK_rep / SOAK52_rep as further instances of SOAK / SOAK52).
GOVERNING BASIS (lead 15:46Z): the Manson universal slopes on the AMS 5663 minimum RA, below; no 538 / 22 C knock-down.
INFORMATION COLUMN (lead 15:46Z, label verbatim): "LITERATURE via the UWaterloo FD+E database (JTE10109J, 1974), unread, TO-VERIFY,
information only" = Brinkman and Korth's 'HT940C' 22 C fit as printed in the database (sigma_f' 1539 MPa, b -0.0587, eps_f' 1.6159,
c -0.7673, E 205 GPa from the literature); raw strain amplitudes in the database cover about 0.0033-0.0243, so the from-zero rows at Kf 3.0
lie above the data (extrapolated) and the eps_f' term is not physical there (lead 15:46Z).  It never governs; the check that the universal
slopes give the lower life in every row is recorded ('US_lower_in_every_row').
NEW in v2: per preload end (3750 / 4096) governing rows for the 2(b) life-limit row; the bending split of every governing case (axial
N_section / A_s and bending M / Z_3, A_s 14.18, Z_3 6.373 from relax v7) and the soak bending moment at which each governing row reaches
MS 0 (input to the 2(c) bending-reduction proposals: propose, do not apply).
Status: 183 (1)(c) is a FOUND NEGATIVE (lead 14:14Z): quoted as negative, never as passing; no hardware decision before the joint ruling.
v1 notes follow.

Screw: ENG-HW-101-IN718, M5 x 10 ISO 7380-1 form, AMS 5662 bar aged to AMS 5663, threads ROLLED AFTER AGEING (TO-DEFINE on the drawing).
Requirement 183 (1)(c): >= 50 hot cycles with a factor 2 on strain range or 20 on cycles -> N_f(de) >= 1000 AND N_f(2 de) >= 50.
Loading (rows, worst of histories per state and quantity, lead 11:41Z): the nominal screw fibre (axial + bending at the max-moment
section, threaded sections included) per state, history and preload (3750 = FE basis, 4096 = J-F1 max):
  (i)  per firing: cold preload -> hot soak state -> cold, range = fibre_hot - fibre_cold (rows "range_MPa"); every soak state of a firing
       is one excursion of the same cycle, so the governing range is the largest over SOAK70 / SOAK / SOAK52;
  (ii) assembly from zero -> hot soak (one per assembly): range = fibre_hot from zero, first loading on the monotonic curve (the larger
       strain, as the accepted TC-01 mid-bay method 237 (3) does); (ii') information: the same range on the cyclic (Masing) curve, the
       stable re-assembly cycle once the root has shaken down.
Thread root: Neuber with the fatigue notch factor Kf (Topper form, sigma*eps = (Kf * S)^2 / E), FEA3D's curve eps = s / E + 0.002 (s / Fty)^n
(n 15 and 30, the lower life governs; the rows' convention), cyclic ranges by Masing doubling (de = ds / E + 2 * 0.002 (ds / 2 Fty)^n).
Kf = 3.0: rolled thread, property class 8.8 and above (DANotes 'Threaded fasteners: Bolt fatigue', D. Wright, University of Western Australia,
Table 6, last updated May 2005, https://danotes.mech.uwa.edu.au/threads/fatigue/fatigue.html, accessed 2026-10-20; LITERATURE, the table is
unattributed and is for steel bolts: TO-VERIFY for IN718 rolled after ageing); sensitivity at 2.2 (class 5.8 rolled) and 3.8 (8.8 cut).
Life: Manson universal slopes (the LCF method accepted at line 212 (c) / 183 (1)(c)): de_t = 3.5 (Su / E) N^-0.12 + D^0.6 N^-0.6,
D = ln(1 / (1 - RA)).  Su = engmat IN718 Ftu(T) (SMC-045 AMS 5662/5663 minima, DATASHEET, transverse 180 ksi RT basis), E(T) engmat
(LITERATURE-approx), RA = 0.15: AMS 5663 minimum per Rolled Alloys bulletin 136USe 'AMS 5662 vs AMS 5663 vs API 6A' (02/15,
https://www.rolledalloys.ca/wp-content/uploads/718vsAMSvsAPI_USA.pdf) and Premium Alloys AMS 5663 page
(https://premiumalloys.com/products/inconel-718/ams-5663/), both accessed 2026-10-20, DISTRIBUTOR; TO-VERIFY against AMS 5663.
Mean stress is not credited or charged (universal slopes, fully reversed basis; the root runs plastic, so the mean relaxes).
Software estimate, not a test.  Negatives SHOWN AS FOUND."""
import json, math, hashlib, sys
from pathlib import Path
import numpy as np

J = Path("/home/claude/work/mechanical/v352/jfwd")
OUT = J / "jfwd_screw_lcf_v352_v2.json"
ROWS = J / "jfwd_in718_rows_v352_v6.json"
RELAXJ = J / "jfwd_relax_v352_v7.json"
ENV_SHA16 = "0872de4ea7e3601d"
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/04-fea/src")
import engmat
MAT = engmat.MATERIALS["IN718"]


def tab(k, T):
    d = MAT[k]
    return float(np.interp(T, d["T_C"], d["v"])) / 1e6


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


RA = 0.15
D = math.log(1.0 / (1.0 - RA))
KF = 3.0
KF_SENS = (2.2, 3.0, 3.8)
NS = (15, 30)
N_REQ, FAC_N, FAC_E = 50, 20.0, 2.0
BK_LABEL = "LITERATURE via the UWaterloo FD+E database (JTE10109J, 1974), unread, TO-VERIFY, information only"
BK = {"E": 205000.0, "sf": 1539.0, "b": -0.0587, "ef": 1.6159, "c": -0.7673,
      "src": "https://fde.uwaterloo.ca/Fde/Materials/Other/brinkmanIN718-HT940C-22T_fc.html (accessed 2026-10-20); C. R. Brinkman and "
             "G. E. Korth, J. Test. Eval. 2 (4), 1974, pp. 249-259, DOI 10.1520/JTE10109J (paper unread)",
      "data_coverage_eps_a": [0.0033, 0.0243], "test_temperature_C": 22.0}
METHODS = ("i_firing", "ii_assembly_from_zero", "ii_stable_reassembly_info")


def T_of_Fty(fty):
    """the screw temperature of a state, back from the rows' Fty(T) (engmat linear 20-649 C)"""
    return float(np.interp(fty, [862.0, 1034.0], [649.0, 20.0]))


def us_de(N, Su, E):
    return 3.5 * Su / E * N ** -0.12 + D ** 0.6 * N ** -0.6


def us_N(de, Su, E):
    lo, hi = 0.0, 12.0                                    # log10 N
    if us_de(10 ** hi, Su, E) > de:
        return float("inf")
    if us_de(1.0, Su, E) < de:
        return 0.0
    for _ in range(200):
        m = 0.5 * (lo + hi)
        lo, hi = (m, hi) if us_de(10 ** m, Su, E) > de else (lo, m)
    return 10 ** (0.5 * (lo + hi))


def bk_N(de):
    """BK information column: cycles to failure for the total strain range de (bisection on log10(2N) in 0 .. 12; eps_a = de / 2)."""
    ea = de / 2.0
    lo, hi = 0.0, 12.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        x = 10.0 ** mid
        f = BK["sf"] / BK["E"] * x ** BK["b"] + BK["ef"] * x ** BK["c"] - ea
        lo, hi = (mid, hi) if f > 0 else (lo, mid)
    return 0.5 * 10.0 ** (0.5 * (lo + hi))


# the fitted rows printed on the database page reproduce (2Nf 50 / 1000 / 10000 -> 0.08628 / 0.01307 / 0.00575 strain amplitude)
for _twoN, _ea in ((50, 0.08628), (1000, 0.01307), (10000, 0.00575)):
    _e = BK["sf"] / BK["E"] * _twoN ** BK["b"] + BK["ef"] * _twoN ** BK["c"]
    assert abs(_e / _ea - 1.0) < 0.01, (_twoN, _e, _ea)


def neuber_cyc(dS, E, Fty, n, kf):
    """local stress and strain RANGE at the root (Masing), sigma_r * eps_r = (kf dS)^2 / E"""
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


def n_allow(S, E, Su, fty, kf, f):
    """US N_allow (worst of n 15 / 30) and its record for nominal range S"""
    worst = None
    for n in NS:
        s, e = f(S, E, fty, n, kf)
        Nf, Nf2 = us_N(e, Su, E), us_N(FAC_E * e, Su, E)
        r = {"n": n, "local_sigma_MPa": round(s, 1), "local_de": round(e, 5), "N_f": round(Nf, 1), "N_f_at_2de": round(Nf2, 1),
             "N_allow_cycles_factor20": round(Nf / FAC_N, 1), "N_allow_strain_factor2": round(Nf2, 1), "N_allow": round(min(Nf / FAC_N, Nf2), 1)}
        r["MS_cycles_vs_50"] = round(r["N_allow"] / N_REQ - 1.0, 3)
        b1, b2 = bk_N(e), bk_N(FAC_E * e)
        bna = min(b1 / FAC_N, b2)
        r["BK_info"] = {"label": BK_LABEL, "N_f": float(f"{b1:.4g}"), "N_f_at_2de": float(f"{b2:.4g}"), "N_allow": float(f"{bna:.4g}"),
                        "MS_cycles_vs_50": round(bna / N_REQ - 1.0, 3),
                        "eps_a_within_data": bool(BK["data_coverage_eps_a"][0] <= e / 2.0 <= BK["data_coverage_eps_a"][1]),
                        "eps_a_at_2de_within_data": bool(BK["data_coverage_eps_a"][0] <= e <= BK["data_coverage_eps_a"][1])}
        if worst is None or r["N_allow"] < worst["N_allow"]:
            worst = r
    return worst


def S_at_MS0(E, Su, fty, kf, f):
    """nominal range (MPa) at which the US N_allow reaches 50 (bisection; N_allow falls with S)"""
    ms = lambda S: n_allow(S, E, Su, fty, kf, f)["N_allow"] / N_REQ - 1.0
    lo, hi = 1.0, 3000.0
    if ms(lo) < 0:
        return 0.0
    for _ in range(80):
        m = 0.5 * (lo + hi)
        lo, hi = (m, hi) if ms(m) > 0 else (lo, m)
    return 0.5 * (lo + hi)


rows = json.loads(ROWS.read_text())
assert rows["version"] == "v6" and rows["inputs"]["fea3d_soak_envelope"]["sha256_16"] == ENV_SHA16, rows["inputs"]["fea3d_soak_envelope"]
rel = json.loads(RELAXJ.read_text())
A_S, Z_3 = rel["inputs"]["constants"]["A_s_mm2"], rel["inputs"]["constants"]["Z_3_mm3"]
out = {"id": "jfwd_screw_lcf_v352", "version": "v2", "date": "2026-10-20", "owner": "mechanical", "method": __doc__.strip(),
       "inputs": {"rows_v6_json": {"path": str(ROWS), "sha256_16": sha(ROWS)}, "relax_v7_json": {"path": str(RELAXJ), "sha256_16": sha(RELAXJ)},
                  "fea3d_soak_envelope": rows["inputs"]["fea3d_soak_envelope"],
                  "engmat_IN718_Ftu": MAT["Ftu"]["src"], "engmat_IN718_E": MAT["E"]["src"],
                  "RA": RA, "D_true_fracture_ductility": round(D, 4), "Kf_basis": KF, "Kf_sensitivity": KF_SENS, "n_curve": NS,
                  "A_s_mm2": A_S, "Z_3_mm3": Z_3},
       "governing_basis": "Manson universal slopes, AMS 5663 minimum RA 0.15 (lead 15:46Z)",
       "information_basis": {"label": BK_LABEL, **BK},
       "status_183_1c": "FOUND NEGATIVE (lead 14:14Z): quoted as negative, never as passing",
       "allowable_universal_slopes": {}, "cases": {}, "governing": {}}
res = {}
HCLS = []
for st in ("SOAK70", "SOAK", "SOAK52"):
    for load in ("3750", "4096"):
        ph = rows["states"][st]["rows"][load]["screw_fibre_soak"]["per_history"]
        for h, x in ph.items():
            if h not in HCLS:
                HCLS.append(h)
            fty = x["Fty_IN718_MPa"]
            T = T_of_Fty(fty)
            E, Su = tab("E", T), tab("Ftu", T)
            ax, bd = x["N_section_N"] / A_S, x["M_Nmm"] / Z_3
            assert abs(ax + bd - x["fibre_MPa"]) < 1.0, (st, load, h, ax + bd, x["fibre_MPa"])
            for kf in KF_SENS:
                rec = {"T_C": round(T, 1), "E_MPa": round(E), "Su_MPa": round(Su, 1), "Fty_MPa": fty, "fibre_hot_MPa": x["fibre_MPa"],
                       "fibre_hot_axial_MPa": round(ax, 1), "fibre_hot_bending_MPa": round(bd, 1), "M_hot_Nmm": x["M_Nmm"], "N_section_N": x["N_section_N"],
                       "fibre_cold_MPa": x["fibre_cold_MPa"], "range_firing_MPa": x["range_MPa"], "Kf": kf}
                for lab in METHODS:
                    S = x["range_MPa"] if lab == "i_firing" else x["fibre_MPa"]
                    rec[lab] = n_allow(S, E, Su, fty, kf, FUN[lab])
                res[f"{st}|{load}|{h}|Kf{kf}"] = rec
out["cases"] = res
out["history_classes"] = HCLS
# the universal slopes give the lower life in every row (lead 15:46Z: 'they are the lower life in every row anyway'): recorded, not assumed
viol = [f"{k}|{lab}" for k, r in res.items() for lab in METHODS if r[lab]["BK_info"]["N_allow"] < r[lab]["N_allow"]]
out["US_lower_in_every_row"] = {"holds": not viol, "n_rows": len(res) * len(METHODS), "rows_where_BK_lower": viol}
# allowable strain ranges at the requirement (for reference), at the SOAK temperature
T0 = T_of_Fty(rows["states"]["SOAK"]["rows"]["4096"]["screw_fibre_soak"]["per_history"]["js5"]["Fty_IN718_MPa"])
E0, Su0 = tab("E", T0), tab("Ftu", T0)
out["allowable_universal_slopes"] = {"T_C": round(T0, 1), "E_MPa": round(E0), "Su_MPa": round(Su0, 1),
                                     "de_at_N_1000": round(us_de(1000.0, Su0, E0), 5), "de_at_N_50_over_2": round(us_de(50.0, Su0, E0) / 2, 5),
                                     "de_allow_183_1c": round(min(us_de(1000.0, Su0, E0), us_de(50.0, Su0, E0) / 2), 5)}
# governing per (range type, Kf, history class) and per preload end: the minimum US N_allow over the soak states (and preloads)
gov = {}
for kf in KF_SENS:
    for lab in METHODS:
        for hc in ("worst_of_histories",) + tuple(HCLS):
            for pe in ("both", "3750", "4096"):
                best = None
                for k, r in res.items():
                    st, load, h, kk = k.split("|")
                    if kk != f"Kf{kf}" or (hc != "worst_of_histories" and h != hc) or (pe != "both" and load != pe):
                        continue
                    if best is None or r[lab]["N_allow"] < best[1][lab]["N_allow"]:
                        best = (k, r)
                if best is None:
                    continue
                k, r = best
                q = r[lab]
                key = f"{lab}|Kf{kf}|{hc}" + ("" if pe == "both" else f"|{pe}")
                gov[key] = {"case": k, "N_allow": q["N_allow"], "MS_cycles_vs_50": q["MS_cycles_vs_50"], "local_de": q["local_de"],
                            "nominal_MPa": r["range_firing_MPa"] if lab == "i_firing" else r["fibre_hot_MPa"],
                            "N_f_information": q["N_f"], "N_f_at_2de": q["N_f_at_2de"],
                            "BK_info": {kk2: q["BK_info"][kk2] for kk2 in ("label", "N_allow", "MS_cycles_vs_50", "N_f", "eps_a_within_data")}}
out["governing"] = gov
# bending split and the soak bending moment at MS 0 (2(c) input: propose, do not apply).  A bending reduction acts on every state and
# history at once, so the needed reduction is the LARGEST over all cases of the preload end (each at its own temperature), not only
# the governing-life case; a case whose axial part alone already exceeds the MS-0 value cannot be closed by bending.
_S0 = {}


def S0_of(r, kf, lab):
    k = (r["E_MPa"], r["Su_MPa"], r["Fty_MPa"], kf, lab)
    if k not in _S0:
        _S0[k] = S_at_MS0(r["E_MPa"], r["Su_MPa"], r["Fty_MPa"], kf, FUN[lab])
    return _S0[k]


bend = {}
for kf in KF_SENS:
    for lab in ("i_firing", "ii_assembly_from_zero"):
        for pe in ("3750", "4096"):
            g = gov[f"{lab}|Kf{kf}|worst_of_histories|{pe}"]
            per = {}
            for k, r in res.items():
                st, load, h, kk = k.split("|")
                if kk != f"Kf{kf}" or load != pe:
                    continue
                S0 = S0_of(r, kf, lab)
                # (i): range = axial_hot + M/Z3 - fibre_cold <= S0;  (ii): fibre_hot = axial_hot + M/Z3 <= S0
                base = r["fibre_hot_axial_MPa"] - (r["fibre_cold_MPa"] if lab == "i_firing" else 0.0)
                M0 = (S0 - base) * Z_3
                red = 1.0 - max(M0, 0.0) / r["M_hot_Nmm"] if r["M_hot_Nmm"] > 0 else 0.0
                per[k] = {"nominal_MPa": r["range_firing_MPa"] if lab == "i_firing" else r["fibre_hot_MPa"], "nominal_at_MS0_MPa": round(S0, 1),
                          "axial_part_MPa": r["fibre_hot_axial_MPa"], "bending_part_MPa": r["fibre_hot_bending_MPa"],
                          "fibre_cold_MPa": r["fibre_cold_MPa"], "M_hot_Nmm": r["M_hot_Nmm"], "M_hot_at_MS0_Nmm": round(M0, 1),
                          "M_reduction_needed_pct": round(100.0 * max(red, 0.0), 1), "closable_by_bending": bool(M0 >= 0.0),
                          "N_allow_now": r[lab]["N_allow"]}
            kmax = max(per, key=lambda k: (not per[k]["closable_by_bending"], per[k]["M_reduction_needed_pct"], -per[k]["M_hot_at_MS0_Nmm"]))
            nfail = [k for k, v in per.items() if not v["closable_by_bending"]]
            bend[f"{lab}|Kf{kf}|{pe}"] = {"governing_life_case": g["case"], "N_allow": g["N_allow"], "MS": g["MS_cycles_vs_50"],
                                          "largest_reduction_case": kmax, **per[kmax],
                                          "closes_by_bending_alone": not nfail, "cases_not_closable_by_bending": nfail,
                                          "note": ("bending removal alone cannot close these cases: the axial part already exceeds the MS-0 value; "
                                                   "a lower soak screw force (preload or thermal increment) is needed as well" if nfail else
                                                   "closes if the soak bending falls by M_reduction_needed_pct in every state and history"),
                                          "per_case": per}
out["bending_split_and_M_at_MS0"] = bend


# the nominal range at which the row reaches MS 0 (Kf, n 15/30 worst, SOAK temperature, Fty 1004.7): v1 definition, kept
def ms_at(dS, kf=KF):
    w = min(min(us_N(neuber_cyc(dS, E0, 1004.7, n, kf)[1], Su0, E0) / FAC_N, us_N(FAC_E * neuber_cyc(dS, E0, 1004.7, n, kf)[1], Su0, E0)) for n in NS)
    return w / N_REQ - 1.0


out["nominal_firing_range_at_MS0_MPa"] = {}
for kf in KF_SENS:
    lo, hi = 50.0, 1500.0
    for _ in range(100):
        m = 0.5 * (lo + hi)
        lo, hi = (m, hi) if ms_at(m, kf) > 0 else (lo, m)
    out["nominal_firing_range_at_MS0_MPa"][f"Kf{kf}"] = round(0.5 * (lo + hi), 1)
s = json.dumps(out, indent=1)
OUT.write_text(s)
for k, v in gov.items():
    if "Kf3.0|worst_of_histories" in k:
        print(k, {a: v[a] for a in ("case", "N_allow", "MS_cycles_vs_50", "nominal_MPa", "N_f_information")}, "BK", v["BK_info"]["N_allow"])
for k, v in bend.items():
    print("BEND", k, {a: v[a] for a in ("governing_life_case", "N_allow", "largest_reduction_case", "nominal_MPa", "nominal_at_MS0_MPa",
                                        "axial_part_MPa", "bending_part_MPa", "M_hot_Nmm", "M_hot_at_MS0_Nmm", "M_reduction_needed_pct",
                                        "closes_by_bending_alone")}, len(v["cases_not_closable_by_bending"]))
print("US lower in every row", out["US_lower_in_every_row"]["holds"], len(out["US_lower_in_every_row"]["rows_where_BK_lower"]))
print("allow", out["allowable_universal_slopes"], "range at MS0", out["nominal_firing_range_at_MS0_MPa"])
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
