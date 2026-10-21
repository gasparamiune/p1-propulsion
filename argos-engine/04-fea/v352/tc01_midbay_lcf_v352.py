"""TC-01 bore mid-bay at the J-FWD screw plane (sector boundary between screws): line 183 (1) (c) low-cycle fatigue and (d) usable temperature,
for the TS-183 class the lead accepted provisionally (lead 08:04Z).  Mechanical, 2026-10-20, v1.  CALC on FEA3D's js4 stresses (SIM, relayed);
every number DERIVED unless tagged.

Lead 08:04Z: 'FEA3D's js4 post shows the TC-01 bore mid-bay ... at the soak: LC6 -0.408 / -0.525 (SF 1.5/2.0 on combined elastic stress); P+Q
+0.79 vs 2 Fty(T) (Pm+Pb 190 MPa at 158 C); preload only (20 C) 88.4 MPa, LC6 +0.787 / +0.452; the ~100 MPa increment is the thermal rise in
screw force and ring bending. I accepted class TS-183 provisionally. Line 183 (1) needs your LCF check: at least 50 hot cycles with a factor of
2 on strain range or 20 on cycles, at the mid-bay range (preload-only to soak, and assembly-from-zero to soak), 6061-T6 at 158 C. Please also
confirm 158 C is within TC-01's usable temperature limit.'

Method (the line-212 (c) method, accepted there for TC-02): Manson universal slopes (Manson 1965), total strain range
de = 3.5 Su/E N^-0.12 + D^0.6 N^-0.6, D = ln(1 / (1 - RA)), RA 0.30 ASSUMED (6061-T6 lower bound), Su = Ftu(T) and E(T) of engmat AL6061-T6
(ASTM B221 minimum x ASM 10 000 h ratio; conservative for a short exposure).  183 (1) (c): N(2 de) >= 50 AND N(de) / 20 >= 50.
Stresses: the soak peak (combined elastic, the stress LC6 is built on) is back-computed from FEA3D's LC6 margins with engmat Fty / Ftu at
158 C (both must give the same value if the tables agree; the larger is used, and never less than the 190 MPa Pm+Pb); the preload-only
value is the 88.4 MPa as relayed.  Ranges: (i) preload-only -> soak, proportional (the increment is the same screw-pull pattern plus ring
bending, as relayed): de = (s_soak - s_pre) / E(158 C); bound without proportionality: s_soak + s_pre (von Mises triangle inequality);
(ii) assembly-from-zero -> soak: s_soak.  Every range is <= 2 Fty(158 C) (shakedown, 183 (1) (b)): the stable cycle is elastic, de = ds / E;
where s_soak > Fty(158 C), the first loading is plastic: range (ii) also uses the Neuber strain s^2 / (E Fty) (elastic-perfectly plastic),
the larger strain.  E at 158 C for every range (the lower E: the larger strain).
Temperature (183 (1) (d)): engmat AL6061-T6 T_max_C 150 (LITERATURE-approx, 'overaging / strength loss accelerates above ~150 C; design limit
for loaded parts'); the J-FWD row temperatures and the time above 150 C per firing from the B1 node histories (rev 3 as js4, rev 4 both bounds);
the TC-01 part maximum and where."""
import json, math, hashlib, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/04-fea/src")
import engmat

J = Path("/home/claude/work/mechanical/v352/jfwd")
HIST = Path("/home/claude/work/mechanical/v352/tb70/hist")
OUT = J / "tc01_midbay_lcf_v352_v1.json"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
M = engmat.MATERIALS["AL6061-T6"]
tabv = lambda k, T: float(np.interp(T, M[k]["T_C"], M[k]["v"])) / 1e6        # MPa
T_SOAK, T_PRE = 158.0, 20.0
FE = {"soak_LC6_MS": (-0.408, -0.525), "soak_PQ_MS": 0.79, "soak_PmPb_MPa": 190.0, "pre_MPa": 88.4, "pre_LC6_MS": (0.787, 0.452),
      "source": "FEA3D js4 post (SIM), relayed by the lead 08:04Z; TC-01 bore mid-bay, sector boundary between screws, screw plane"}
Fty_s, Ftu_s, E_s = tabv("Fty", T_SOAK), tabv("Ftu", T_SOAK), tabv("E", T_SOAK)
Fty_p, Ftu_p = tabv("Fty", T_PRE), tabv("Ftu", T_PRE)
s_soak_y = Fty_s / (1.5 * (1.0 + FE["soak_LC6_MS"][0]))
s_soak_u = Ftu_s / (2.0 * (1.0 + FE["soak_LC6_MS"][1]))
s_pre_y = Fty_p / (1.5 * (1.0 + FE["pre_LC6_MS"][0]))
s_pre_u = Ftu_p / (2.0 * (1.0 + FE["pre_LC6_MS"][1]))
S_SOAK = max(s_soak_y, s_soak_u, FE["soak_PmPb_MPa"])
S_PRE = FE["pre_MPa"]
PQ_check = 2.0 * Fty_s / FE["soak_PmPb_MPa"] - 1.0


def n_cycles(de, Su, E, RA=0.30):
    D = math.log(1.0 / (1.0 - RA))
    f = lambda N: 3.5 * Su / E * N ** -0.12 + D ** 0.6 * N ** -0.6 - de
    lo, hi = 1.0, 1e15
    if f(hi) > 0:
        return hi
    for _ in range(300):
        mid = math.sqrt(lo * hi)
        lo, hi = (mid, hi) if f(mid) > 0 else (lo, mid)
    return math.sqrt(lo * hi)


def lcf(ds, label, neuber_peak=None):
    de = ds / E_s
    if neuber_peak is not None and neuber_peak > Fty_s:
        de = max(de, neuber_peak ** 2 / (E_s * Fty_s))
    N2, N1 = n_cycles(2.0 * de, Ftu_s, E_s), n_cycles(de, Ftu_s, E_s)
    gov = min(N2, N1 / 20.0)
    return {"range": label, "stress_range_MPa": round(ds, 1), "within_2Fty_shakedown": bool(ds <= 2.0 * Fty_s), "strain_range": round(de, 6),
            "N_at_2x_strain": float(f"{N2:.3g}"), "N_over_20": float(f"{N1 / 20.0:.3g}"), "N_allowed_governing": float(f"{gov:.3g}"),
            "required": 50, "life_ratio": float(f"{gov / 50.0:.3g}"), "verdict": "PASS" if gov >= 50.0 else "FAIL"}


ranges = [lcf(S_SOAK - S_PRE, "(i) preload-only (20 C) -> soak (158 C), proportional"),
          lcf(S_SOAK + S_PRE, "(i') preload-only -> soak, non-proportional bound s_soak + s_pre"),
          lcf(S_SOAK, "(ii) assembly-from-zero -> soak (stable elastic cycle / first-loading Neuber, the larger)", neuber_peak=S_SOAK)]
# ---- temperature: J-FWD row (thermal z 134.06 +/- 2.6, as jfwd_embed v1) and the TC-01 part maximum, per history
Z_ROW, DZ = 134.06, 2.6
temps = {}
for lab, tag in (("DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_GVLO", "rev3_GVLO (js4 basis)"), ("DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b", "rev3_merged"),
                 ("DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_R4_GVLO", "rev4_GVLO"), ("DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_R4_GVHI", "rev4_GVHI")):
    fh = HIST / f"{lab}_hist.npz"
    z = np.load(fh, allow_pickle=True)
    info = json.loads(str(z["info"]))
    off = info["inj_face_z_mm"] - 103.5134
    t = np.asarray(z["t_s"], float)
    X1, T1 = z["X_TC01"], z["T_TC01"] - 273.15
    m = np.abs(X1[:, 1] - Z_ROW) <= DZ
    row, rown = T1[:, m].mean(axis=1), T1[:, m].max(axis=1)
    dt = np.gradient(t)
    k = np.unravel_index(int(np.argmax(T1)), T1.shape)
    temps[tag] = {"hist": f"tb70/hist/{fh.name}", "sha256_16": sha(fh),
                  "row_mean_max_C": round(float(row.max()), 1), "t_row_mean_max_s": round(float(t[int(np.argmax(row))]), 3),
                  "row_node_max_C": round(float(rown.max()), 1), "s_above_150C_per_firing_row_mean": round(float(dt[row > 150.0].sum()), 1),
                  "s_above_150C_per_firing_row_node_max": round(float(dt[rown > 150.0].sum()), 1),
                  "TC01_part_max_C": round(float(T1.max()), 1), "TC01_part_max_t_s": round(float(t[k[0]]), 3),
                  "TC01_part_max_at_r_z_sax_mm": [round(float(X1[k[1], 0]), 3), round(float(X1[k[1], 1] - off), 3)],
                  "TC01_s_above_150C_any_node": round(float(dt[T1.max(axis=1) > 150.0].sum()), 1)}
T_LIM = M["T_max_C"]["v"]
temperature = {"usable_limit_C": T_LIM, "limit_basis": f"engmat AL6061-T6 T_max_C ({M['T_max_C']['tag']}): {M['T_max_C']['src']}",
               "query_158C_within_limit": bool(T_SOAK <= T_LIM), "excess_K": round(T_SOAK - T_LIM, 1), "histories": temps,
               "verdict": ("NOT WITHIN: 158 C exceeds the 150 C usable limit of 6061-T6 (the js4 soak frame; rev-4 GVLO row 158.1 C mean / 159.2 C "
                           "node, about 45 s above 150 C per firing; rev-4 GVHI 127.5 C and rev-3 merged 119.6 C stay below). TC-01 is above its limit "
                           "anyway at the chamber bore (rev-4 part maximum 191.7 / 187.0 C GVLO / GVHI), RM1-06 since line 187. 183 (1) (d) stays OPEN "
                           "for TC-01 as for TC-02 (line 212 (d)): it closes only with T-F1 (sourced short-time elevated-temperature 6061-T6 "
                           "allowables with the exposure basis, the (b) package) or a design change")}
out = {"id": "tc01_midbay_lcf_v352", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(), "inputs_FE": FE,
       "allowables_engmat_MPa": {"Fty_158C": round(Fty_s, 1), "Ftu_158C": round(Ftu_s, 1), "E_158C": round(E_s, 0), "Fty_20C": round(Fty_p, 1),
                                 "Ftu_20C": round(Ftu_p, 1), "2Fty_158C": round(2.0 * Fty_s, 1),
                                 "basis": "ASTM B221 / B241 minimum x ASM typical ratio after 10 000 h at temperature (engmat; LITERATURE)"},
       "stresses_MPa": {"soak_from_LC6_yield": round(s_soak_y, 1), "soak_from_LC6_ult": round(s_soak_u, 1), "soak_used": round(S_SOAK, 1),
                        "preload_only_from_LC6_yield": round(s_pre_y, 1), "preload_only_from_LC6_ult": round(s_pre_u, 1), "preload_only_used": S_PRE,
                        "PQ_check_2Fty_over_PmPb": round(PQ_check, 3),
                        "note": "the soak value from FEA3D's LC6 margins with engmat allowables; the relayed preload-only 88.4 MPa vs the value from its "
                                "LC6 margins at 20 C shows how far FEA3D's 20 C allowables are from engmat's"},
       "lcf_183_1_c": {"method": "Manson universal slopes (Manson 1965), RA 0.30 ASSUMED, Su = Ftu(158 C) and E(158 C) engmat; the line-212 (c) method",
                       "evidence": "CALC (universal-slopes LITERATURE method; material constants ASSUMED / engmat); FEA3D stresses SIM",
                       "ranges": ranges, "verdict": "PASS" if all(r["verdict"] == "PASS" for r in ranges) else "FAIL",
                       "not_assessed": "creep-fatigue interaction (hold of about 45 s above 150 C per firing at the row on GVLO; T-F1 exposure basis); "
                                       "mean-stress effect (strain-life universal slopes carry none; the soak peak is local and self-limiting)"},
       "temperature_183_1_d": temperature}
s = json.dumps(out, indent=1, default=float)
OUT.write_text(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
print(json.dumps(out["allowables_engmat_MPa"]), json.dumps(out["stresses_MPa"]))
for r in ranges:
    print(r)
for k, v in temps.items():
    print(k, {kk: v[kk] for kk in v if kk not in ("hist", "sha256_16")})
print(temperature["verdict"])
