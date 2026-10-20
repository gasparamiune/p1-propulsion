"""2(a) (lead 14:14Z, ~30 min box): the J-FWD screw LCF rows of jfwd_screw_lcf_v352_v1.json on a SOURCED IN718 strain-life basis in place
of the Manson universal slopes.  Mechanical, 2026-10-20, v1.  Reads only; the local strain ranges (Neuber with Kf on FEA3D's curve, method
(i) per firing and (ii) assembly from zero) are taken unchanged from the v1 rows; only the life curve changes.  CALC on LITERATURE data;
negatives SHOWN AS FOUND (the row stays a FOUND NEGATIVE, lead 14:14Z, until the joint ruling after (b2)).

Basis (LITERATURE, a peer-reviewed test series reproduced in a public fatigue database):
  C. R. Brinkman and G. E. Korth, 'Strain Fatigue and Tensile Behavior of Inconel 718 from Room Temperature to 650C', Journal of Testing
  and Evaluation, Vol. 2, No. 4, July 1974, pp. 249-259, as reproduced by the University of Waterloo Fatigue Design and Evaluation (FD+E)
  materials database (GPL v2+ data files), accessed 2026-10-20:
  PRIMARY  'HT940C', tested 22 C, https://fde.uwaterloo.ca/Fde/Materials/Other/brinkmanIN718-HT940C-22T_fc.html
           solution 940 C 2 h AC + 718 C 8 h FC to 621 C 8 h AC (the AMS 5662 solution range 941-1010 C and the AMS 5663 duplex age),
           3 heats, Su 1418 MPa, Sy 1127 MPa (Fig. 3), E 205 GPa (literature, not reported), sigma_f' 1539 MPa, b -0.0587,
           eps_f' 1.6159, c -0.7673 (fitted coefficients as printed);
  HOT CHECK 'HT1038C', tested 427 C, https://fde.uwaterloo.ca/Fde/Materials/Other/brinkmanIN718-HT1038C-427T_fc.html
           solution 1038 C 2 h AC + 760 C 10 h FC to 649 C 8 h AC (an AMS 5664-type high solution, NOT the AMS 5663 state), heat 2,
           Su 1212 MPa, Sy 1020 MPa, RA 28 %, E 178 GPa (literature), sigma_f' 1889 MPa, b -0.0799, eps_f' 6.4667, c -1.0154.
  Database warnings carried: hourglass specimens, diametral strain ('Diametral tests(?)'); E not reported (from the literature); 'difficult
  to correlate strain-life-stress'; the fitted rows are computed from the fitted coefficients.
Strain-life: eps_a = sigma_f' / E (2 N)^b + eps_f' (2 N)^c, eps_a = de / 2 (fully reversed; mean stress neither credited nor charged, as v1).
Criterion 183 (1)(c) as v1: N_allow = min(N_f(2 de), N_f(de) / 20) >= 50 hot cycles.
The screw runs at 158.6 C at SOAK70 (127-159 C over the soak states): the 22 C curve is the closer temperature; the 427 C curve is a
different heat treatment and is shown only as a hot sensitivity.
Usage: jfwd_screw_lcf_sourced_v352.py -> v352/jfwd/jfwd_screw_lcf_sourced_v352_v1.json"""
import json, math, hashlib
from pathlib import Path

J = Path("/home/claude/work/mechanical/v352/jfwd")
SRC = J / "jfwd_screw_lcf_v352_v1.json"
OUT = J / "jfwd_screw_lcf_sourced_v352_v1.json"
BASES = {
    "BK74_HT940C_22C": {"E": 205000.0, "sf": 1539.0, "b": -0.0587, "ef": 1.6159, "c": -0.7673, "Su": 1418.0, "Sy": 1127.0,
                        "url": "https://fde.uwaterloo.ca/Fde/Materials/Other/brinkmanIN718-HT940C-22T_fc.html", "role": "PRIMARY (AMS 5662/5663 state, RT)"},
    "BK74_HT1038C_427C": {"E": 178000.0, "sf": 1889.0, "b": -0.0799, "ef": 6.4667, "c": -1.0154, "Su": 1212.0, "Sy": 1020.0,
                          "url": "https://fde.uwaterloo.ca/Fde/Materials/Other/brinkmanIN718-HT1038C-427T_fc.html", "role": "HOT SENSITIVITY (other heat treatment)"}}
LIFE = 50


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def Nf(de, k):
    """cycles to failure for the total strain range de on basis k (bisection on log10(2N) in 0 .. 12)."""
    ea = de / 2.0
    lo, hi = 0.0, 12.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        x = 10.0 ** mid
        f = k["sf"] / k["E"] * x ** k["b"] + k["ef"] * x ** k["c"] - ea
        lo, hi = (mid, hi) if f > 0 else (lo, mid)
    return 0.5 * 10.0 ** (0.5 * (lo + hi))


# the fitted rows printed on the primary page reproduce (2Nf 50 / 1000 / 10000 -> 0.08628 / 0.01307 / 0.00575 strain amplitude)
for twoN, ea in ((50, 0.08628), (1000, 0.01307), (10000, 0.00575)):
    k = BASES["BK74_HT940C_22C"]
    e = k["sf"] / k["E"] * twoN ** k["b"] + k["ef"] * twoN ** k["c"]
    assert abs(e / ea - 1.0) < 0.01, (twoN, e, ea)

v1 = json.loads(SRC.read_text())
rows, gov = {}, {}
for key, cs in v1["cases"].items():
    stt, pre, hist, kf = key.split("|")
    for meth in ("i_firing", "ii_assembly_from_zero", "ii_stable_reassembly_info"):
        de = cs[meth]["local_de"]
        r = {"local_de": de, "US_v1_N_allow": cs[meth]["N_allow"]}
        for bn, k in BASES.items():
            n1, n2 = Nf(de, k), Nf(2.0 * de, k)
            na = min(n2, n1 / 20.0)
            r[bn] = {"N_f": float(f"{n1:.4g}"), "N_f_at_2de": float(f"{n2:.4g}"), "N_allow": float(f"{na:.4g}"), "MS_cycles_vs_50": round(na / LIFE - 1.0, 3)}
        rows[f"{key}|{meth}"] = r
        for bn in BASES:
            for g in (f"{meth}|{kf}|{bn}|worst_of_histories", f"{meth}|{kf}|{bn}|{hist}"):
                if g not in gov or r[bn]["N_allow"] < gov[g]["N_allow"]:
                    gov[g] = {"case": key, "N_allow": r[bn]["N_allow"], "MS_cycles_vs_50": r[bn]["MS_cycles_vs_50"], "N_f": r[bn]["N_f"],
                              "local_de": de, "US_v1_N_allow": r["US_v1_N_allow"]}
summary = {}
for kf in ("Kf2.2", "Kf3.0", "Kf3.8"):
    for meth in ("i_firing", "ii_assembly_from_zero"):
        g = gov[f"{meth}|{kf}|BK74_HT940C_22C|worst_of_histories"]
        h = gov[f"{meth}|{kf}|BK74_HT1038C_427C|worst_of_histories"]
        summary[f"{meth}|{kf}"] = {"sourced_22C_N_allow": g["N_allow"], "sourced_22C_MS": g["MS_cycles_vs_50"], "case": g["case"],
                                   "hot_427C_N_allow": h["N_allow"], "US_v1_N_allow": g["US_v1_N_allow"],
                                   "verdict": "PASS" if g["MS_cycles_vs_50"] >= 0 else "FOUND NEGATIVE"}
out = {"id": "jfwd_screw_lcf_sourced_v352", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "inputs": {"screw_lcf_v1": {"path": str(SRC), "sha256_16": sha(SRC)}}, "strain_life_bases": BASES, "rows": rows, "governing": gov,
       "summary_worst_of_histories": summary,
       "finding": ("On the sourced Brinkman-Korth curve the lives move by a factor of a few against the universal slopes, and the sign of the "
                   "183 (1)(c) row does not change where the v1 row was negative at Kf 3.0 (see summary): the row stays a FOUND NEGATIVE; "
                   "the life-limit (2(b)) and design-change (2(c)) inputs are restated on this basis in summary.")}
s = json.dumps(out, indent=1)
OUT.write_text(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
for k, v in summary.items():
    print(k, v)
