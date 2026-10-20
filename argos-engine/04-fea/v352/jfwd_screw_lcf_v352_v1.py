"""v3.5.2 J-FWD screw LCF row on the IN718 thread-form basis (lead 12:52Z item 2, 13:20Z order; 183 (1)(c) criterion).  Mechanical, 2026-10-20.
Screw: ENG-HW-101-IN718, M5 x 10 ISO 7380-1 form, AMS 5662 bar aged to AMS 5663, threads ROLLED AFTER AGEING (TO-DEFINE on the drawing).
Requirement 183 (1)(c): >= 50 hot cycles with a factor 2 on strain range or 20 on cycles -> N_f(de) >= 1000 AND N_f(2 de) >= 50.
Loading (rows v4 on relax v6, worst of histories per state and quantity, lead 11:41Z): the nominal screw fibre (axial + bending at the
max-moment section, threaded sections included) per state, history and preload (3750 = FE basis, 4096 = J-F1 max; identical to rows v3):
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
import json, math, hashlib, sys, importlib.util
from pathlib import Path
import numpy as np

J = Path("/home/claude/work/mechanical/v352/jfwd")
OUT = J / "jfwd_screw_lcf_v352_v1.json"
ROWS = J / "jfwd_in718_rows_v352_v4.json"
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


rows = json.loads(ROWS.read_text())
out = {"id": "jfwd_screw_lcf_v352", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "method": __doc__.strip(),
       "inputs": {"rows_v3_json": [str(ROWS), sha(ROWS)], "engmat_IN718_Ftu": MAT["Ftu"]["src"], "engmat_IN718_E": MAT["E"]["src"],
                  "RA": RA, "D_true_fracture_ductility": round(D, 4), "Kf_basis": KF, "Kf_sensitivity": KF_SENS, "n_curve": NS},
       "allowable_universal_slopes": {}, "cases": {}, "governing": {}}
res = {}
for st in ("SOAK70", "SOAK", "SOAK52"):
    for load in ("3750", "4096"):
        ph = rows["states"][st]["rows"][load]["screw_fibre_soak"]["per_history"]
        for h, x in ph.items():
            fty = x["Fty_IN718_MPa"]
            T = T_of_Fty(fty)
            E, Su = tab("E", T), tab("Ftu", T)
            for kf in KF_SENS:
                rec = {"T_C": round(T, 1), "E_MPa": round(E), "Su_MPa": round(Su, 1), "Fty_MPa": fty, "fibre_hot_MPa": x["fibre_MPa"],
                       "fibre_cold_MPa": x["fibre_cold_MPa"], "range_firing_MPa": x["range_MPa"], "Kf": kf}
                for lab, S, f in (("i_firing", x["range_MPa"], neuber_cyc), ("ii_assembly_from_zero", x["fibre_MPa"], neuber_mono),
                                  ("ii_stable_reassembly_info", x["fibre_MPa"], neuber_cyc)):
                    worst = None
                    for n in NS:
                        s, e = f(S, E, fty, n, kf)
                        Nf, Nf2 = us_N(e, Su, E), us_N(FAC_E * e, Su, E)
                        r = {"n": n, "local_sigma_MPa": round(s, 1), "local_de": round(e, 5), "N_f": round(Nf, 1), "N_f_at_2de": round(Nf2, 1),
                             "N_allow_cycles_factor20": round(Nf / FAC_N, 1), "N_allow_strain_factor2": round(Nf2, 1),
                             "N_allow": round(min(Nf / FAC_N, Nf2), 1)}
                        r["MS_cycles_vs_50"] = round(r["N_allow"] / N_REQ - 1.0, 3)
                        if worst is None or r["N_allow"] < worst["N_allow"]:
                            worst = r
                    rec[lab] = worst
                res[f"{st}|{load}|{h}|Kf{kf}"] = rec
out["cases"] = res
# allowable strain ranges at the requirement (for reference), at the SOAK temperature
T0 = T_of_Fty(rows["states"]["SOAK"]["rows"]["4096"]["screw_fibre_soak"]["per_history"]["js5"]["Fty_IN718_MPa"])
E0, Su0 = tab("E", T0), tab("Ftu", T0)
out["allowable_universal_slopes"] = {"T_C": round(T0, 1), "E_MPa": round(E0), "Su_MPa": round(Su0, 1),
                                     "de_at_N_1000": round(us_de(1000.0, Su0, E0), 5), "de_at_N_50_over_2": round(us_de(50.0, Su0, E0) / 2, 5),
                                     "de_allow_183_1c": round(min(us_de(1000.0, Su0, E0), us_de(50.0, Su0, E0) / 2), 5)}
# governing per (range type, Kf, history class): the minimum N_allow over states and preloads
gov = {}
for kf in KF_SENS:
    for lab in ("i_firing", "ii_assembly_from_zero", "ii_stable_reassembly_info"):
        for hc in ("worst_of_histories", "js5", "(a)", "(a')", "(a'')"):
            best = None
            for k, r in res.items():
                st, load, h, kk = k.split("|")
                if kk != f"Kf{kf}" or (hc != "worst_of_histories" and h != hc):
                    continue
                if best is None or r[lab]["N_allow"] < best[1][lab]["N_allow"]:
                    best = (k, r)
            gov[f"{lab}|Kf{kf}|{hc}"] = {"case": best[0], "N_allow": best[1][lab]["N_allow"], "MS_cycles_vs_50": best[1][lab]["MS_cycles_vs_50"],
                                         "local_de": best[1][lab]["local_de"], "nominal_MPa": best[1]["range_firing_MPa"] if lab == "i_firing" else best[1]["fibre_hot_MPa"],
                                         "N_f": best[1][lab]["N_f"], "N_f_at_2de": best[1][lab]["N_f_at_2de"]}
out["governing"] = gov
# the nominal range at which the row reaches MS 0 (Kf 3.0, n 15/30 worst, SOAK temperature): inverse
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
    if "Kf3.0" in k:
        print(k, v)
print("allow", out["allowable_universal_slopes"], "range at MS0", out["nominal_firing_range_at_MS0_MPa"])
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
