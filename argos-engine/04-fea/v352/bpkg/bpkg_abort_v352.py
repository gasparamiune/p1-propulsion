"""v3.5.2 (b) package and abort decision input (lead CHANGELOG 236 (5), 239 (7); lead 14:34Z 'Next as you have it: the (b) package and
the abort decision with 2(b) and 2(c)').  Mechanical, 2026-10-20, v1.  Reads only (no solver run, no thermal run); SIM / CALC / DERIVED /
ASSUMED as tagged per row; not physical approval; negatives SHOWN AS FOUND.  The lead sets the abort value.

Per gap-conductance bound (GVLO conservative, GVHI; rev-4 fields, lead 236 (2) / (11)) and per trial case-abort value A (175 = the line-188
(5) value 448.15 K, then 165 / 150 / 135 / 120 / 105 C on the case TC):
  1  seat (TC-02 / TC-03): the T-F2 rev-4 seat matrix (tf2_r4_refine_v352_v1.json: 236 (9)(b) rule = min over C5, C3n, C4n and C7 outside
     the stick-edge zone; cells per the 234 (4) rule; also min(C5, C3n, C4n)) for TB70 at SF 1.5 / 2.0 and TBS at 1.0 / 1.5 (188 (9),
     239 (7)): 183 (1) (a) primary on the mechanical increment, (b) P+Q <= 2 Fty(T), (c) LCF; combined MS at the case SF (line 106 type,
     TS-183 where (a)-(c) pass) and SF 1.0 (information);
  2  no leak (T-F2): floor (S03 lands) contact state, thread radial gap, top gap, seat-entry cavity, S03 land temperature vs the FFKM rating;
  3  global S-AX v352r4 rows of every part at each state (the seat parts are governed by T-F2; non-seat negatives FLAGGED);
  4  (d) exposure per A (tf1_exposure_v352_v1.json: TB state part maxima and the ASSUMED shifted-history times above 150 C), FD-01 and
     TC-03 GlidCop (c) / (d);
  5  normal-operation case-TC station maxima in every armed phase (the abort is armed while the MV is open) and the false-trip margin;
  6  surrogate validity with open joints (shift, station offset, joint states, bound spread);
  7  flight-state allowable ratios (T-F1 re-stated): the Ftu(T) / Ftu,RT and Fty(T) / Fty,RT each governing TC-02 cell needs for MS = 0;
  8  screw LCF input to the slack-fix ruling (lead 15:37Z order item 2, 16:07Z item 5): 2(b) life-limit rows on LCF v2 (universal
     slopes GOVERN, lead 15:46Z; the Brinkman-Korth column is "LITERATURE via the UWaterloo FD+E database (JTE10109J, 1974), unread,
     TO-VERIFY, information only"), 2(c) bending-reduction proposals sized on LCF v2 (propose, do not apply), and the slack-fix inputs:
     route (i) disc spring with a drawn pilot (spring v3) against route (iii) the open negative plus the preload-retention audit (relax v7
     openings in um), with (a) added series compliance as the alternative; all on FEA3D's ADOPTED envelope v3 0872de4ea7e3601d ('worst
     computed instance, not a proven bound');
  9  the abort table and Mechanical's recommendation.
Usage: bpkg_abort_v352.py -> v352/bpkg/bpkg_abort_v352_v1.json"""
import json, math, hashlib, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/04-fea/src")
import engmat

V = Path("/home/claude/work/mechanical/v352")
SR = Path("/home/claude/work/mechanical/runs/structural")
REFJ = V / "contact/tf2_r4_refine_v352_v1.json"
SAXJ = {bd: V / f"engine/04-fea/structural/results/sax_results_L1_thv352_NF2b_R4_{bd}_r10free_cad352r4_eh0p1_v1.json" for bd in ("GVLO", "GVHI")}
TF1J = V / "texts/tf1_exposure_v352_v1.json"
HIST = V / "tb70/hist"
F3D = {"GVLO": Path("/home/claude/work/fea3d/results/f1_post_tb352g.json"), "GVHI": Path("/home/claude/work/fea3d/results/f1_post_tb352h.json")}
SCREW = V / "jfwd/jfwd_screw_lcf_v352_v2.json"                 # LCF v2 (US governs; BK information column)
RELAXJ = V / "jfwd/jfwd_relax_v352_v7.json"                    # no-slack 24-case, openings, (a) series compliance
ROWSJ = V / "jfwd/jfwd_in718_rows_v352_v6.json"                # rows v6 (THE ROW thread basis)
SPRINGJ = V / "jfwd/jfwd_spring_v352_v3.json"                  # route (i) disc spring, spring v3
ENV_SHA16 = "0872de4ea7e3601d"
SEALT = V / "engine/04-fea/thermal/seal_table_v1p2.json"
OUT = V / "bpkg/bpkg_abort_v352_v1.json"
BDS = ("GVLO", "GVHI")
A_, B_ = "ENG-TC-02", "ENG-TC-03"
ZF = 107.51342601773104
STATES = {"TB": 175.0, "TB_a165": 165.0, "TB_a150": 150.0, "TB_a135": 135.0, "TB_a120": 120.0, "TB_a105": 105.0}
SF = {"TB70": (1.5, 2.0), "TBS": (1.0, 1.5), "LC1": (1.5, 2.0), "LC2": (1.5, 2.0)}
LIM6061, LIFE = 150.0, 50
CRIT_A, CRIT_B, CRIT_C = ("MS_prim_y", "MS_prim_u"), ("MS_PQ",), ("MS_LCF",)
CRIT_INFO = ("MS_y", "MS_u", "MS_y_SF1")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def r4(x):
    return None if x is None else round(float(x), 4)


def mtab(mat, key, TC):
    d = engmat.MATERIALS[mat][key]
    return float(np.interp(TC, d["T_C"], d["v"])) / 1e6


def us_N(de, Su, E, ra):
    """Manson universal slopes: N for the total strain range de (bisection on log10 N, 0 .. 15)."""
    D = math.log(1.0 / (1.0 - ra))
    lo, hi = 0.0, 15.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        f = 3.5 * Su / E * 10.0 ** (-0.12 * mid) + D ** 0.6 * 10.0 ** (-0.6 * mid) - de
        lo, hi = (mid, hi) if f > 0 else (lo, mid)
    return 10.0 ** (0.5 * (lo + hi))


def lcf_point(vm, Fy, Su, E, ra, life=LIFE):
    """method (ii) assembly from zero (accepted line 212 (c) / 237 (3)): de = vm / E, or the Neuber strain vm^2 / (E Fty) above Fty."""
    de = vm / E if vm <= Fy else vm ** 2 / (E * Fy)
    N2, N1 = us_N(2.0 * de, Su, E, ra), us_N(de, Su, E, ra)
    Na = min(N2, N1 / 20.0)
    return {"de": round(de, 6), "N_f_de": float(f"{N1:.4g}"), "N_f_2de": float(f"{N2:.4g}"), "N_allow": float(f"{Na:.4g}"), "MS_LCF": round(Na / life - 1.0, 3)}


ref = json.loads(REFJ.read_text())
tf1 = json.loads(TF1J.read_text())
seal = json.loads(SEALT.read_text())
s03 = next(r for r in seal["table"] if r["id"] == "S03")
out = {"id": "bpkg_abort_v352", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "status": "SIM / CALC / DERIVED / ASSUMED as tagged per row; not physical approval; negatives SHOWN AS FOUND; the lead sets the abort value",
       "inputs": {"tf2_r4_refine": {"path": str(REFJ), "sha256_16": sha(REFJ)},
                  "sax_results": {bd: {"path": str(p), "sha256_16": sha(p)} for bd, p in SAXJ.items()},
                  "tf1_exposure": {"path": str(TF1J), "sha256_16": sha(TF1J)},
                  "fea3d_tb_post": {bd: {"path": str(p), "sha256_16": sha(p)} for bd, p in F3D.items()},
                  "screw_lcf_v2": {"path": str(SCREW), "sha256_16": sha(SCREW)},
                  "relax_v7": {"path": str(RELAXJ), "sha256_16": sha(RELAXJ)},
                  "rows_v6": {"path": str(ROWSJ), "sha256_16": sha(ROWSJ)},
                  "spring_v3": {"path": str(SPRINGJ), "sha256_16": sha(SPRINGJ)},
                  "seal_table": {"path": str(SEALT), "sha256_16": sha(SEALT), "S03": {k: s03[k] for k in ("item", "location", "material", "rating_cont_C")}}}}

# ------------------------------------------------------------------ 1 + 2: seat matrix and no-leak per state
MESH = {}


def mesh01(bd):
    if bd not in MESH:
        d = SR / f"L1_thv352_NF2b_R4_{bd}_r10free_cad352r4_eh0p1"
        z = np.load(d / "mesh.npz", allow_pickle=True)
        X, E, pn = z["X"], z["E"], z["pn"]
        part = np.empty(len(X), object)
        for p in (A_, B_):
            part[np.unique(E[pn == p])] = p
        MESH[bd] = (X, part)
    return MESH[bd]


def s03_land_T(bd, key):
    """max T (C) of the S03 lands: TC-02 counterbore-floor and TC-03 flange-top nodes at z = zf, r 7.8 .. 9.8 (seal table v1.2 zone)."""
    X, part = mesh01(bd)
    rd = SR / f"contact_tc0203_sub_r4_L1_thv352_NF2b_R4_{bd}_r10free_cad352r4_eh0p1" / key
    if not (rd / "res.npz").exists():
        return None
    z = np.load(rd / "res.npz")
    n = z["nodes"]
    x = X[n]
    k = (np.abs(x[:, 1] - ZF) < 2e-3) & (x[:, 0] >= 7.8) & (x[:, 0] <= 9.8)
    T = z["T"][k].astype(float) - 273.15
    return {"T_max_C": round(float(T.max()), 1), "n_nodes": int(k.sum()), "parts": sorted(set(str(p) for p in part[n[k]]))}


def cellrow(c):
    """compact seat-matrix cell: value, variant, min(C5, C3n, C4n), node / class, the h 0.05 estimate and the refinement flag."""
    pv = c["per_variant"][c["from"]]
    v = pv["value"]
    est = pv.get("h0p05_estimate") or {}
    flags = sorted(set(q["refinement_flag"] for q in c["per_variant"].values() if q.get("refinement_flag")))
    return {"MS": r4(c["seat_matrix"]), "from": c["from"], "min_C5_C3n_C4n": r4(c["min_C5_C3n_C4n"]), "from_3": c["from_3"],
            "node": v[1], "r_z_mm": [v[2], v[3]], "T_C": v[4], "vm_MPa": v[5], "d_singular_mm": v[6], "class": v[7], "basis": pv["basis"],
            "MS_h0p05_estimate": est.get("MS_h0p05_estimate"), "estimate_factor": est.get("factor"),
            "all_node_min": {"MS": pv["all_node"][0], "r_z_mm": pv["all_node"][2:4], "class": pv["all_node"][7]} if pv.get("all_node") else None,
            "refinement_flags": flags or None}


seat, leak = {}, {}
for bd in BDS:
    seat[bd], leak[bd] = {}, {}
    for case in ("TB70", "TBS"):
        seat[bd][case], leak[bd][case] = {}, {}
        for st, A in STATES.items():
            k = f"{bd}|{case}|{st}"
            if k not in ref["seat_matrix"] or not ref["seat_matrix"][k].get(A_):
                seat[bd][case][st] = {"abort_C": A, "status": "NOT RUN (chain 11 pending or not in the T-F2 rev-4 set)"}
                continue
            m = ref["seat_matrix"][k]
            row = {"abort_C": A, "SF": SF[case]}
            for p in (A_, B_):
                pr = {}
                for cr in CRIT_A + CRIT_B + CRIT_C + CRIT_INFO:
                    if cr in m[p]:
                        pr[cr] = cellrow(m[p][cr])
                abc = [pr[c]["MS"] for c in CRIT_A + CRIT_B + CRIT_C if c in pr] + [pr[c]["min_C5_C3n_C4n"] for c in CRIT_A + CRIT_B + CRIT_C if c in pr and pr[c]["min_C5_C3n_C4n"] is not None]
                est = [pr[c]["MS_h0p05_estimate"] for c in CRIT_A + CRIT_B if c in pr and pr[c]["MS_h0p05_estimate"] is not None]
                comb = min(pr[c]["MS"] for c in ("MS_y", "MS_u") if c in pr)
                pr["verdict_183_1_abc"] = ("PASS" if min(abc) >= 0 else "FAIL") + f" (min {min(abc):+.3f} over (a) / (b) / (c), seat matrix and min(C5, C3n, C4n))"
                pr["verdict_abc_at_h0p05_estimate"] = None if not est else ("PASS" if min(est) >= 0 else "FAIL") + f" (min {min(est):+.3f}, (a) / (b))"
                pr["combined_at_case_SF"] = ("MS >= 0: line 106 passes directly" if comb >= 0 else
                                             f"NEGATIVE {comb:+.3f} (combined at the case SF): TS-183 candidate, accepted only with (a)-(c) passing and (d)")
                row[p] = pr
            seat[bd][case][st] = row
            # no leak
            cs = ref["runs"][k]
            lv = {}
            for vn, cl in cs.items():
                itf = cl.get("interfaces")
                if not itf:
                    continue
                fl, th, up, tg = itf["floor"], itf["thread_radial"], itf["unpaired_proximity"], itf.get("top_gap", {})
                lv[vn] = {"floor_closed": f"{fl['n_closed']} / {fl['n_pairs']}", "floor_open_r_mm": fl["open_r_mm"],
                          "floor_opening_max_um": round(fl["opening_max_mm"] * 1e3, 2), "floor_p_max_MPa_penalty": fl["p_max_MPa_penalty"],
                          "thread_radial_gap_um": [round(-th["overclosure_max_mm"] * 1e3, 2), round(-th["overclosure_min_mm"] * 1e3, 2)],
                          "thread_n_in_contact": th["n_in_contact"], "top_gap_min_mm": tg.get("min_nominal_mm"),
                          "top_gap_min_at_drawing_min_mm": tg.get("min_at_drawing_minimum_0.125_mm"),
                          "unpaired_closest_gap_um": round(up["closest"][0]["gap_mm"] * 1e3, 2) if up.get("closest") else None,
                          "unpaired_closest_at_r_z_mm": up["closest"][0]["at_r_z_mm"] if up.get("closest") else None}
            s3 = s03_land_T(bd, f"C5_{case}_{st}")
            ok = all(q["top_gap_min_at_drawing_min_mm"] is not None and q["top_gap_min_at_drawing_min_mm"] > 0 and
                     (q["unpaired_closest_gap_um"] is None or q["unpaired_closest_gap_um"] > 0) and q["floor_opening_max_um"] < 5.0 for q in lv.values())
            leak[bd][case][st] = {"abort_C": A, "per_variant": lv, "S03_land_T": s3, "S03_rating_C": s03["rating_cont_C"],
                                  "verdict": ("NO LEAK INDICATED" if ok and s3 and s3["T_max_C"] < s03["rating_cont_C"] else "CHECK") +
                                             ": the flange stays seated (top gap open at the 0.125 drawing minimum), the seat-entry cavity stays open, the "
                                             "S03-land opening stays at the micrometre level (criterion used here: < 5 um, a negligible fraction of the "
                                             "AS568-016 squeeze), S03 land temperature below the FFKM rating; the S03 groove itself is not modelled (open item)"}
out["seat_TC02_TC03"] = seat
out["no_leak"] = leak
out["stick_edge_zone_d_mm"] = ref.get("d_zone_mm")

# ------------------------------------------------------------------ 3: global S-AX rows per state (all parts)
glob = {}
for bd in BDS:
    sj = json.loads(SAXJ[bd].read_text())
    glob[bd] = {}
    for case in ("TB70", "TBS"):
        glob[bd][case] = {}
        for st, A in STATES.items():
            rows = [r for r in sj["rows"] if r["case"] == case and r["state"] == st]
            parts = {}
            for r in rows:
                q = parts.setdefault(r["part"], {"material": r["material"], "role": r["role"], "T_part_max_C": round(r["T_part_max_C"], 1),
                                                 "T_limit_C": r["T_limit_C"], "T_limit_exceeded": r["T_limit_exceeded"]})
                q[r["set"]] = {"MS": r4(r["MS"]), "MS_ult": r4(r["MS_ult"]), "MS_primary_only": r4(r["MS_primary_only"]),
                               "MS_PQ": r4(r["MS_PQ_nodal_shakedown"]), "T_C": round(r["T_C"], 1), "at_r_z_mm": r["at_r_z_mm"]}
            flags = []
            for pn, q in parts.items():
                if pn in (A_, B_):
                    continue
                for s in ("regular", "all"):
                    c = q.get(s)
                    if c and ((c["MS"] is not None and c["MS"] < 0) or (c["MS_ult"] is not None and c["MS_ult"] < 0)):
                        ts = ""
                        if c["MS_primary_only"] is not None and c["MS_PQ"] is not None:
                            ts = " (a) %+.3f (b) %+.3f" % (c["MS_primary_only"], c["MS_PQ"])
                        flags.append(f"{pn} {s} MS {c['MS']:+.3f}" + (f" / ult {c['MS_ult']:+.3f}" if c["MS_ult"] is not None else "") + ts)
                if q["T_limit_exceeded"]:
                    flags.append(f"{pn} part maximum {q['T_part_max_C']} C above its T_limit {q['T_limit_C']} C")
            glob[bd][case][st] = {"abort_C": A, "parts": parts, "non_seat_flags": flags}
out["global_sax_rows"] = glob
out["global_sax_note"] = ("S-AX v352r4 global (C0 u_z tie at the seat): the TC-02 / TC-03 seat rows are information, governed by T-F2 (section 1). "
                          "NZ-01 / NZ-02 / NZ-03 / NZ-04 / NZ-06 rows move by less than 0.02 in MS over the abort range (the uniform surrogate shift "
                          "moves the nozzle with the case; a surrogate artefact for the nozzle): NZ-01 stays on its 183 (2) test-based containment, "
                          "NZ-03 stays negative until N-F1 (212 (2), 239 (7)); the NZ-04 / NZ-06 T_limit flags follow the shift (NZ-04 above 500 C "
                          "for A >= 150 on GVLO) and are not abort decisions.")

# ------------------------------------------------------------------ 4: (d) exposure per A; TC-03 GlidCop and FD-01 (c) / (d)
expo = {}
for bd in BDS:
    rec = tf1["bounds"][bd]
    expo[bd] = {"nominal": {pn: {"part_max_C": rec["parts"][pn]["part_max"]["max_C"], "t_above_150C_s": rec["parts"][pn]["part_max"]["t_above_150C_s"],
                                 "burn_max_C": rec["parts"][pn]["burn_max_C"]} for pn in rec["parts"]}, "per_abort": {}}
    for st, row in rec["TB_surrogate_per_abort"].items():
        e = {"abort_C": row["abort_C"], "shift_K": row["shift_K"]}
        for pn in ("ENG-TC-01", "ENG-TC-02", "ENG-TC-03"):
            sh = row[pn]["shifted_history_ASSUMED"]
            e[pn] = {"TB_state_max_C": row[pn]["TB_state_field_max_C"], "shifted_history_max_C": sh["max_C"], "t_above_150C_s": sh["t_above_150C_s"],
                     "t_above_175C_s": sh["t_above_175C_s"], "t_above_200C_s": sh["t_above_200C_s"]}
        e["d_TC01_TC02"] = "OPEN (T-F1 gate; 6061-T6 above the 150 C long-time limit: TC-02 at the TB state, TC-01 in the shifted soak)"
        g = e["ENG-TC-03"]["TB_state_max_C"]
        e["d_TC03"] = (f"part maximum {g} C vs the engmat GlidCop AL-15 T_max 600 C, which is ASSUMED (no sourced time-at-temperature limit; "
                       "datasheet qualitative only): passes on an ASSUMED limit only; FLAG for a sourced limit")
        expo[bd]["per_abort"][st] = e
out["exposure_d"] = expo
out["exposure_note"] = ("TB state = the B1 end-of-burn field shifted uniformly until the TC-01 maximum equals A (ASSUMED surrogate, sax.py); the "
                        "shifted history applies the same shift to the whole B1 history (burn + soak) and is for sizing only, not a modelled stand "
                        "history. (d) stays OPEN for TC-01 and TC-02 at every A and in nominal operation until T-F1 closes (239 (12)).")

# FD-01 at A = 175 (FEA3D tb352g / tb352h; only TB exists): (a), (b) from FEA3D, (c) here, (d) per the 239 (7) FD-01 rule
fd = {}
RA_316 = 0.40
for bd in BDS:
    fj = json.loads(F3D[bd].read_text())
    fd[bd] = {}
    for case in ("TB70", "TBS"):
        for m in fj["states"]["TB"]["cases"][case]["margins"]:
            if m["part"] != "FD-01":
                continue
            T = m["T_C"]
            Fy, Su, E = mtab("SS316L", "Fty", T), mtab("SS316L", "Ftu", T), mtab("SS316L", "E", T)
            c = lcf_point(m["vm_MPa"], Fy, Su, E, RA_316)
            c10 = lcf_point(m["vm_MPa"], Fy, Su, E, 0.10)
            fd[bd][f"{case}|{m['set']}"] = {"MS": r4(m["MS"]), "MS_ult": r4(m["MS_ult"]), "a_MS_primary_only": r4(m["MS_primary_only"]),
                                            "b_MS_PQ": r4(m["MS_PQ_nodal_shakedown"]), "vm_MPa": round(m["vm_MPa"], 1), "T_C": round(T, 1),
                                            "T_part_max_C": round(m["T_part_max_C"], 1), "node": m["node"],
                                            "c_LCF_RA0p40_ASSUMED": c, "c_LCF_RA0p10_floor": c10,
                                            "d": f"part maximum {m['T_part_max_C']:.1f} C <= 150 C: passes on the sourced long-time allowable (lead 239 (7) FD-01 rule)"}
out["FD01_at_A175"] = fd
out["FD01_note"] = ("FEA3D has FD-01 only at A = 175 (tb352g / tb352h). RA 0.40 for 316L is ASSUMED (taken equal to the EN 10088-3 1.4404 bar "
                    "minimum elongation 40 %); the 0.10 floor shows the verdict does not hang on RA. Lower A lowers the FD-01 temperature with the "
                    "shift; that the FD-01 stress falls with it (mismatch-driven against the hotter parts) is ASSUMED, not computed: an FEA3D TB "
                    "row at the adopted A closes it.")

# ------------------------------------------------------------------ 5: normal-operation case-TC station maxima per armed phase
RUNS_NO = {"B1 rev 4 GVLO": "DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_R4_GVLO", "B1 rev 4 GVHI": "DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_R4_GVHI",
           "B1 rev 3 GVLO": "DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_GVLO", "B1 rev 3 GVHI": "DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_GVHI",
           "B1 rev 3 merged (perfect contact)": "DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b",
           "A1 rev 3 merged (perfect contact)": "DC-A1dispp99_tg711_hi_SS316L_L2.5_v352_NF2b"}
no = {}
for name, lab in RUNS_NO.items():
    p = HIST / f"{lab}_hist.npz"
    z = np.load(p, allow_pickle=True)
    info = json.loads(str(z["info"]))
    t = z["t_s"].astype(float)
    zi = info["inj_face_z_mm"]
    odX, odT = z["od_X"], z["od_T"].astype(float) - 273.15
    ms = (odX[:, 1] <= zi - 12.6) & (odX[:, 1] >= zi - 17.6)
    st = odT[:, ms].max(axis=1)
    tc1 = (z["T_TC01"].astype(float) - 273.15).max(axis=1)
    ph = []
    for i, (t0, t1) in enumerate(info["segments_s"]):
        k = (t >= t0 - 1e-6) & (t <= t1 + 1e-6)
        j = int(np.argmax(np.where(k, st, -1e9)))
        ie = int(np.argmin(np.abs(t - t1)))
        ph.append({"phase": f"burn {i + 1} (MV open, abort armed)", "t_s": [t0, t1], "station_max_C": round(float(st[j]), 2), "t_of_max_s": round(float(t[j]), 2),
                   "TC01_max_C_in_phase": round(float(tc1[k].max()), 2), "end_of_burn_TC01_minus_station_K": round(float(tc1[ie] - st[ie]), 2)})
    kb = np.zeros(len(t), bool)
    for t0, t1 in info["segments_s"]:
        kb |= (t >= t0 - 1e-6) & (t <= t1 + 1e-6)
    no[name] = {"thermal_run": lab, "hist_sha256_16": sha(p), "frd_sha256_16": info["frd_sha256_16"], "gap_variant": info["gap_variant"],
                "armed_phases": ph, "armed_max_C": max(q["station_max_C"] for q in ph),
                "soak_station_max_C_information": round(float(st[~kb].max()), 2) if (~kb).any() else None, "n_station_nodes": int(ms.sum())}
floor_run = max(no, key=lambda q: no[q]["armed_max_C"])
out["normal_operation_case_TC"] = {"runs": no, "station": "TC-01 OD nodes 12.6-17.6 mm aft of the injector face (the case over-temperature abort TCs, "
                                   "CHANGELOG 86 / 90)", "false_trip_floor_C": no[floor_run]["armed_max_C"], "false_trip_floor_run": floor_run,
                                   "note": "the merged runs are rev 3 (perfect contact, the conductance upper bound kept by 236 (2)); no rev-4 merged run "
                                           "exists and none is started (no new thermal run without the lead). Rev 4 changes the seat heat paths; the rev-3 "
                                           "vs rev-4 GV station rows show its effect on the station."}

# ------------------------------------------------------------------ 6: surrogate validity with open joints
sv = {}
for bd in BDS:
    rec = tf1["bounds"][bd]
    eob = next(q for q in no[f"B1 rev 4 {bd}"]["armed_phases"])
    sv[bd] = {"station_offset_K": eob["end_of_burn_TC01_minus_station_K"],
              "shift_K_per_A": {st: rec["TB_surrogate_per_abort"][st]["shift_K"] for st in STATES},
              "TC02_TB_state_C_per_A": {st: rec["TB_surrogate_per_abort"][st]["ENG-TC-02"]["TB_state_field_max_C"] for st in STATES},
              "TC03_TB_state_C_per_A": {st: rec["TB_surrogate_per_abort"][st]["ENG-TC-03"]["TB_state_field_max_C"] for st in STATES},
              "joint_states": {st: {case: (leak[bd][case][st]["per_variant"].get("C5") if st in leak[bd].get(case, {}) else None) for case in ("TB70",)} for st in STATES}}


def interp_ms(bd, case, p, cr, A):
    """linear interpolation of a seat cell in A between the computed abort states (for the station-offset sensitivity)."""
    pts = sorted((v["abort_C"], v[p][cr]["MS"]) for st, v in seat[bd][case].items() if p in v and cr in v[p])
    if len(pts) < 2:
        return None
    xs, ys = zip(*pts)
    return float(np.interp(A, xs, ys))


sens = {}
for bd in BDS:
    off = sv[bd]["station_offset_K"]
    sens[bd] = {}
    for A in (150.0, 135.0, 165.0):
        row = {}
        for p in (A_, B_):
            for cr in ("MS_prim_u", "MS_PQ", "MS_u"):
                a0, a1 = interp_ms(bd, "TB70", p, cr, A), interp_ms(bd, "TB70", p, cr, A + off)
                if a0 is not None:
                    row[f"{p}|{cr}"] = [round(a0, 4), round(a1, 4)]
        sens[bd][f"A{A:.0f}"] = row
out["surrogate_validity"] = {"per_bound": sv, "station_offset_sensitivity_TB70": sens,
                             "notes": ["The surrogate's field shape is the nominal B1 end-of-burn shape; a real abort follows an off-nominal burn whose "
                                       "shape is not modelled (ASSUMED, sizing only).",
                                       "Station offset: at the end of the nominal burn the case TC station reads 1.4-1.5 K below the TC-01 maximum, so a "
                                       "trip at a station reading A leaves the TC-01 maximum at about A + offset; the surrogate sets the TC-01 maximum to A, "
                                       "non-conservative by the offset; its effect on the TB70 seat cells (interpolated in A, [at A, at A + offset]) is in "
                                       "station_offset_sensitivity_TB70.",
                                       "Open joints: GVLO / GVHI carry the joints as gap conductances (open-joint bounds); the T-F2 joint states at each "
                                       "TB state (floor closed over the S03 lands with um-level openings at the flange OD, thread radially open, top gap "
                                       "open) are consistent with an open thread gap and a closed flange land; the GVLO-GVHI spread at the same A "
                                       "(TC-02 about 15 K) is the joint-conductance sensitivity of the surrogate."]}

# ------------------------------------------------------------------ 7: flight-state allowable ratios (T-F1 re-stated), TC-02
FTY_RT, FTU_RT = mtab("AL6061-T6", "Fty", 20.0), mtab("AL6061-T6", "Ftu", 20.0)


def ratio_row(c, which):
    T = c["T_C"]
    rt = (mtab("AL6061-T6", "Fty", T) / FTY_RT) if which == "y" else (mtab("AL6061-T6", "Ftu", T) / FTU_RT)
    return {"MS": c["MS"], "T_C": T, "r_z_mm": c["r_z_mm"], "class": c["class"], f"engmat_10000h_ratio_F{'ty' if which == 'y' else 'tu'}": round(rt, 4),
            "required_ratio_for_MS0": round(rt / (1.0 + c["MS"]), 4), "from": c["from"]}


fr = {}
for k, m in ref["seat_matrix"].items():
    bd, case, st = k.split("|")
    if A_ not in m or not m[A_]:
        continue
    c = {cr: cellrow(m[A_][cr]) for cr in ("MS_u", "MS_y", "MS_prim_u", "MS_PQ") if cr in m[A_]}
    fr[k] = {"SF": SF.get(case), "combined_ult (Ftu, at the case SF)": ratio_row(c["MS_u"], "u"), "combined_yield (Fty, at the case SF)": ratio_row(c["MS_y"], "y"),
             "a_primary_ult (Ftu)": ratio_row(c["MS_prim_u"], "u"), "b_PQ (Fty, P+Q <= 2 Fty)": ratio_row(c["MS_PQ"], "y")}
fa1s = {"cell": "TC-02 FA1S thread cell (FEA3D js4, 151.04 bar abs, 45.6 C, SF 1.0 / 1.0; lead 236 (3), 239 (2)): MS_y +1.144 / MS_u +1.404"}
for which, ms in (("y", 1.144), ("u", 1.404)):
    rt = (mtab("AL6061-T6", "Fty", 45.6) / FTY_RT) if which == "y" else (mtab("AL6061-T6", "Ftu", 45.6) / FTU_RT)
    fa1s[f"F{'ty' if which == 'y' else 'tu'}"] = {"engmat_ratio_at_45.6C": round(rt, 4), "required_ratio_for_MS0": round(rt / (1 + ms), 4)}
soak = {}
for bd in BDS:
    sj = json.loads(SAXJ[bd].read_text())
    for r in sj["rows"]:
        if r["part"] == A_ and r["set"] == "regular" and r["case"] in ("LC6", "TS2") and r["state"] in ("B1_51.7", "B1_70.7"):
            T = r["T_C"]
            rt = mtab("AL6061-T6", "Ftu", T) / FTU_RT
            soak[f"{bd}|{r['case']}|{r['state']}"] = {"MS_ult": r4(r["MS_ult"]), "T_C": round(T, 1), "T_part_max_C": round(r["T_part_max_C"], 1),
                                                       "engmat_ratio_Ftu": round(rt, 4), "required_ratio_for_MS0": round(rt / (1 + r["MS_ult"]), 4)}
out["flight_state_allowable_ratios_TC02"] = {"seat_cells": fr, "FA1S": fa1s, "soak_global_regular": soak,
                                             "rule": "required ratio = engmat 10,000 h ratio at the cell temperature / (1 + MS): the strength ratio "
                                                     "F(T) / F(RT) at which the cell reaches MS = 0 (RT basis ASTM B221 / B241 Fty 240 / Ftu 260 MPa). "
                                                     "A sourced short-time value at or above the required ratio closes the cell for (d)'s strength "
                                                     "part; the post-exposure RT check of T-F1 is separate. TS-183 cells (heat-driven combined "
                                                     "negatives) are governed by (a) / (b); the combined rows are shown for the line-106 type check."}

# ------------------------------------------------------------------ 8: screw LCF input (2(b) life-limit rows, 2(c) bending-reduction
#                                                                     proposals) and the slack-fix inputs (spring (i) vs (iii), (a))
sc = json.loads(SCREW.read_text())
rel = json.loads(RELAXJ.read_text())
rws = json.loads(ROWSJ.read_text())
spr = json.loads(SPRINGJ.read_text())
assert sc["version"] == "v2" and sc["US_lower_in_every_row"]["holds"], sc["US_lower_in_every_row"]
assert rel["inputs"]["fea3d_soak_envelope"]["sha256_16_at_read"] == ENV_SHA16 and rws["inputs"]["fea3d_soak_envelope"]["sha256_16"] == ENV_SHA16
assert spr["inputs"]["fea3d_soak_envelope"]["sha256_16"] == ENV_SHA16 and spr["version"] == "v3"
F_ENVJ = Path(rel["inputs"]["fea3d_soak_envelope"]["path"])
assert sha(F_ENVJ) == ENV_SHA16, ("adopted envelope changed", sha(F_ENVJ))
envj = json.loads(F_ENVJ.read_text())
M_FE = {st: envj["states"][st]["M_x28.6_Nmm"] for st in ("SOAK70", "SOAK", "SOAK52")}
L_G_MODEL = 3.15        # joint-model grip length L_G (jfwd_relax_v352_v3.py; the tilt moment is rotation-driven over it)
HC = sc["history_classes"]
KFS = ("Kf2.2", "Kf3.0", "Kf3.8")
life = {}
for kf in KFS:
    for meth in ("i_firing", "ii_assembly_from_zero", "ii_stable_reassembly_info"):
        for h in HC:
            for pre in ("3750", "4096"):
                g = sc["governing"].get(f"{meth}|{kf}|{h}|{pre}")
                if g is None:
                    continue
                life[f"{meth}|{kf}|{h}|{pre}"] = {"state": g["case"].split("|")[0], "N_allow": g["N_allow"], "MS_cycles_vs_50": g["MS_cycles_vs_50"],
                                                  "N_f_information": g["N_f_information"], "N_f_at_2de": g["N_f_at_2de"], "local_de": g["local_de"],
                                                  "BK_info_N_allow": g["BK_info"]["N_allow"]}
viab = {}
for kf in KFS:
    for pre in ("3750", "4096"):
        r0 = {h: life[f"ii_assembly_from_zero|{kf}|{h}|{pre}"]["N_allow"] for h in HC if f"ii_assembly_from_zero|{kf}|{h}|{pre}" in life}
        ri = {h: life[f"i_firing|{kf}|{h}|{pre}"]["N_allow"] for h in HC if f"i_firing|{kf}|{h}|{pre}" in life}
        b0 = {h: life[f"ii_assembly_from_zero|{kf}|{h}|{pre}"]["BK_info_N_allow"] for h in r0}
        bi = {h: life[f"i_firing|{kf}|{h}|{pre}"]["BK_info_N_allow"] for h in ri}
        nmin = min(min(r0.values()), min(ri.values()))
        viab[f"{kf}|{pre}"] = {"N_allow_from_zero_by_instance": r0, "N_allow_per_firing_by_instance": ri,
                               "life_limit_firings_worst_of_instances": math.floor(nmin), "viable_(>=1_firing)": bool(nmin >= 1.0),
                               "BK_info_N_allow_from_zero_by_instance": b0, "BK_info_N_allow_per_firing_by_instance": bi}
v30, v38, v22 = viab["Kf3.0|4096"], viab["Kf3.8|4096"], viab["Kf2.2|4096"]
fz = lambda v: min(v["N_allow_from_zero_by_instance"].values())
pf = lambda v: min(v["N_allow_per_firing_by_instance"].values())
life_find = (f"On the universal slopes (GOVERNING, lead 15:46Z), worst of the instances at the 4096 N end: from zero N_allow {fz(v22):g} / "
             f"{fz(v30):g} / {fz(v38):g} and per firing {pf(v22):g} / {pf(v30):g} / {pf(v38):g} at Kf 2.2 / 3.0 / 3.8 (3750 N: from zero "
             f"{fz(viab['Kf3.0|3750']):g}, per firing {pf(viab['Kf3.0|3750']):g} at Kf 3.0). A replace-every-N-firings life limit (every "
             f"firing counted at the from-zero range) is "
             + "; ".join((f"NOT VIABLE at {k.replace('Kf', 'Kf ')} (below one firing at both preload ends)" if not (viab[k + "|4096"]["viable_(>=1_firing)"] or viab[k + "|3750"]["viable_(>=1_firing)"])
                          else f"{viab[k + '|4096']['life_limit_firings_worst_of_instances']} firings at {k.replace('Kf', 'Kf ')} (4096 N; "
                               f"{viab[k + '|3750']['life_limit_firings_worst_of_instances']} at 3750 N)") for k in ("Kf3.0", "Kf3.8", "Kf2.2"))
             + "; far below the 50-cycle life in every case, so a life "
             f"limit alone does not close 183 (1)(c), which stays a FOUND NEGATIVE (lead 14:14Z). The BK column (information only) gives "
             f"longer lives in every row (US lower in all {sc['US_lower_in_every_row']['n_rows']} rows).")
bend = sc["bending_split_and_M_at_MS0"]
b_i30, b_i30l = bend["i_firing|Kf3.0|4096"], bend["i_firing|Kf3.0|3750"]
b_i22, b_i38 = bend["i_firing|Kf2.2|4096"], bend["i_firing|Kf3.8|4096"]
b_z30, b_z22 = bend["ii_assembly_from_zero|Kf3.0|4096"], bend["ii_assembly_from_zero|Kf2.2|4096"]
b_i22l, b_z22l = bend["i_firing|Kf2.2|3750"], bend["ii_assembly_from_zero|Kf2.2|3750"]
_ink = next(k.rsplit("|", 2)[0] for k in rel["verdict_24"] if k.startswith("IN718"))
_uns = {}
for _end in ("lo", "hi"):
    _cs = rel["cases_24"][f"{_ink}|{_end}|seat"]
    _uns[_end] = {pre: sum(1 for k, x in _cs.items() if k.split("|")[1] == pre and min(x["firing_1"]["F_S_min_N"], x["firing_2"]["F_S_min_N"]) <= 0)
                  for pre in ("J-F1_min_2250", "J-F1_max_4096")}
unseat_txt = "; ".join(f"k_b {e}: {_uns[e]['J-F1_min_2250']} of 12 at 2250 N, {_uns[e]['J-F1_max_4096']} of 12 at 4096 N, F_S min "
                       f"{rel['verdict_24'][_ink + '|' + e + '|seat']['F_S_min_N']:g} N" for e in ("lo", "hi"))
sizing = {k: {kk: v[kk] for kk in ("governing_life_case", "N_allow", "largest_reduction_case", "nominal_MPa", "nominal_at_MS0_MPa", "axial_part_MPa",
                                   "bending_part_MPa", "M_hot_Nmm", "M_hot_at_MS0_Nmm", "M_reduction_needed_pct", "closes_by_bending_alone",
                                   "cases_not_closable_by_bending")} for k, v in bend.items()}
props = [
    (f"(1) CUT THE SOAK BENDING AT ITS SOURCE (sized, DERIVED on LCF v2): per firing at Kf 3.0 the soak screw moment must fall by "
     f"{b_i30['M_reduction_needed_pct']:g} % (4096 N) / {b_i30l['M_reduction_needed_pct']:g} % (3750 N) in every soak state and instance "
     f"(largest case {b_i30['largest_reduction_case']}: M {b_i30['M_hot_Nmm']:g} -> {b_i30['M_hot_at_MS0_Nmm']:g} N mm); "
     f"{b_i22['M_reduction_needed_pct']:g} % at Kf 2.2 and {b_i38['M_reduction_needed_pct']:g} % at Kf 3.8. The from-zero row cannot be "
     f"closed by bending alone at Kf 3.0 ({len(b_z30['cases_not_closable_by_bending'])} cases have an axial part above the MS-0 value, "
     f"{b_z30['axial_part_MPa']:g} vs {b_z30['nominal_at_MS0_MPa']:g} MPa at {b_z30['largest_reduction_case']}); at Kf 2.2 it needs "
     f"{b_z22['M_reduction_needed_pct']:g} %. The bending is the seat tilt of the TC-01 ring under the shell pull (FE envelope v3, M at "
     f"x'28.6 at SOAK70 {min(M_FE['SOAK70'].values()):g}-{max(M_FE['SOAK70'].values()):g} N mm over the instances, "
     f"{max(M_FE['SOAK70'], key=M_FE['SOAK70'].get)} highest; SOAK {min(M_FE['SOAK'].values()):g}-{max(M_FE['SOAK'].values()):g}, "
     f"{max(M_FE['SOAK'], key=M_FE['SOAK'].get)} highest; the IN718 rows carry the threaded-section maximum x the E ratio x the seat "
     f"contact-force ratio, rows v6 (7)): the seat footprint (edge break, spot-face bearing ring) and the shell pull (the select-fit gap; "
     f"P+Q band g <= 0.068 mm on relax v7) are the levers; each needs an FE instance before it can be credited."),
    ("(2) THREAD-ROOT Kf: specify the ENG-HW-101-IN718 thread rolled after ageing with a controlled root radius (an MJ-form external "
     f"thread, ISO 5855-2, mates with the M5-6H tapped TC-02): at Kf 2.2 the per-firing row needs {b_i22l['M_reduction_needed_pct']:g} % "
     f"less bending at 3750 N and {b_i22['M_reduction_needed_pct']:g} % at 4096 N (from zero still {b_z22l['M_reduction_needed_pct']:g} / "
     f"{b_z22['M_reduction_needed_pct']:g} %); the Kf of such a root on IN718 is TO-SOURCE (no as-recalled value); the MJ / M mating "
     f"(thread class, root clearance) is TO-CHECK against ISO 5855-2 before any ruling."),
    ("(3) LOWER J-F1 MAXIMUM PRELOAD: the from-zero fibre falls with the preload (axial part and the tilt contact force); the per-firing "
     "range falls only through the bending term (dF_S/dF_V = 1.000 at the soak); bounded below by the 2250 N minimum. The 239 (3) "
     f"every-head-seated requirement already fails at BOTH install ends on the envelope (relax v7, seat family: {unseat_txt}), so a lower "
     "maximum does not change the slack verdict."),
    (f"(4) LONGER GRIP (lower curvature for the same imposed end rotation, M ~ 1 / L for a rotation-driven moment): a "
     f"{b_i30['M_reduction_needed_pct']:g} % cut needs {1.0 / (1.0 - b_i30['M_reduction_needed_pct'] / 100.0):.2f} x the grip, i.e. about "
     f"+{L_G_MODEL * (1.0 / (1.0 - b_i30['M_reduction_needed_pct'] / 100.0) - 1.0):.1f} mm on the model grip L_G {L_G_MODEL:g} mm, against "
     f"the 0.5 mm under-head FD-04 budget: does not fit; not proposed."),
    ("(5) A DISC SPRING (route (i)) does NOT reduce the soak fibre: spring v3 shows it solid at every hot frame (T01 >= 140 C), so the hot "
     "fibre and the per-firing range of the seated cases are unchanged; it only removes the slack end of the slack cases.")]
out["screw_LCF_input"] = {"source": {"path": str(SCREW), "sha256_16": sha(SCREW)},
                          "status": "183 (1)(c) FOUND NEGATIVE (lead 14:14Z): quoted as negative, never as passing",
                          "governing_basis": sc["governing_basis"], "information_basis_label": sc["information_basis"]["label"],
                          "2b_life_limit_rows": {"rule": "N_allow = min(N_f(2 de), N_f(de) / 20) per instance and preload end (factor 20 on life, 2 on "
                                                         "strain), N_f for information; worst over the soak states of each instance (the 2250 N "
                                                         "minimum end is not in the screw fibre rows: TO-COMPUTE with the slack fix)",
                                                 "rows": life, "viability": viab, "finding": life_find},
                          "2c_bending_reduction_proposals_propose_do_not_apply": {"sizing_from_LCF_v2": sizing, "proposals": props}}

# ---- slack-fix inputs (lead 15:37Z order item 2; 16:07Z item 5): route (i) disc spring + pilot vs route (iii) open negative + audit;
#      (a) added series compliance as the alternative
INK = next(k.rsplit("|", 2)[0] for k in rel["verdict_24"] if k.startswith("IN718"))
E20 = mtab("IN718", "E", 20.0)
A_S = rel["inputs"]["constants"]["A_s_mm2"]
opn = {}
for end in ("lo", "hi"):
    v = rel["verdict_24"][f"{INK}|{end}|seat"]
    kb, ksh = v["k_b_N_mm"], v["k_sh_N_mm"]
    opn[end] = {"k_b_IN718_N_mm": kb, "k_sh_N_mm": ksh, "F_S_min_N": v["F_S_min_N"], "n_unseated_of_24": v["n_unseated"],
                "unseated_cases": v["unseated_cases"], "min_case": v["min_case"], "min_at_t_s": v["min_at"],
                "opening_um": round(abs(min(v["F_S_min_N"], 0.0)) * (1.0 / kb + 1.0 / ksh) * 1e3, 2),
                "cold_end_F_S_min_2250_N": v["cold_end_F_S_min_2250_N"]}
asc = rel["a_series_compliance_IN718_seat_line"]
alt_a = {end: {"added_series_compliance_um_per_kN": asc[end]["added_series_compliance_um_per_kN"], "k_b_total_max_N_mm": asc[end]["k_b_at_f_N_mm"],
               "f_max": asc[end]["f_max"],
               "equivalent_extra_free_length_at_A_s_mm": round(asc[end]["added_series_compliance_um_per_kN"] * 1e-6 * E20 * A_S, 2)}
         for end in ("lo", "hi")}
l5 = spr["lead_16_07Z_item5_seated_and_solid"]
sA = {k.split("|", 1)[1]: v for k, v in l5.items() if k.startswith("A_DIN2093")}
sB = {k.split("|", 1)[1]: v for k, v in l5.items() if k.startswith("B_Lesjofors")}
ri = spr["route_i_pilot_centring_and_overhang"]
geoc = spr["geometry_length_tip_engagement"]["cases"]
spring_A_case = next(k for k in geoc if k.startswith("spring A"))
slack = {
    "route_i_disc_spring_with_pilot": {
        "spring_A_DIN2093_A10_17-7PH": {k: {kk: v[kk] for kk in ("all_seated", "F_S_min_N", "lift_max_um", "hot_F_S_min_N", "solid_at_every_hot_frame_all_cases",
                                                              "F_flat_derated_N", "k_b_N_mm")} for k, v in sA.items()},
        "spring_B_Lesjofors_7909": {k: {kk: v[kk] for kk in ("all_seated", "F_S_min_N", "solid_at_every_hot_frame_all_cases", "F_flat_derated_N")} for k, v in sB.items()},
        "relaxation_threshold": spr["relaxation_threshold_seat_family"],
        "geometry_spring_A": {k: geoc[spring_A_case][k] for k in ("L_nom_mm", "L_tol_mm", "t_solid_min_max_mm", "tip_clearance_to_full_thread_end_min_mm", "tip_ok",
                                                                  "L_e_gap_bound_mm", "A_n_gap_bound_mm2", "thread_row_min")},
        "geometry_no_spring_THE_ROW": {k: geoc[next(k2 for k2 in geoc if k2.startswith("no spring"))][k] for k in ("tip_clearance_to_full_thread_end_min_mm", "L_e_gap_bound_mm",
                                                                                                                   "A_n_gap_bound_mm2", "thread_row_min")},
        "bearing_max_soak_N": spr["bearing_max_soak_N"],
        "z_centring_stack_mm": ri["z_centring_stack_mm"], "tolerable_e_mm_by_cutter": ri["tolerable_e_mm_by_cutter"],
        "z_centring_verdict": ri["z_centring_verdict"], "tangential_overhang_14_01Z": ri["tangential_overhang_14_01Z"],
        "geometry_proposals_propose_do_not_apply": ri["PROPOSALS_do_not_apply"],
        "open_items": ["Schnorr 001 500 A in 1.4568 (17-7 PH) TO-QUOTE with relaxation data at about 160 C (R) and E(T) (13:20Z: F_S > 0 with a sourced R)",
                       "ENG-HW-101-IN718 drawing: pilot 5.15 h9 with an undercut fillet r >= 0.2, length 10.7 +/-0.1 (10.2 + t)",
                       "J-F1 at the flight length with the spring (K, slip interface, flat at the minimum install, lot load check, relaxation hold, crack-on torque)",
                       "TC-02 tap position tolerance (TO-DEFINE) and the cutter / overhang proposals above (CAD check before any ruling)"]},
    "route_iii_open_negative_plus_audit": {
        "no_slack_239_3": "FOUND NEGATIVE on the adopted envelope (both families): the select-fit cannot fix it (no band at the 0.040 minimum)",
        "per_end": opn,
        "opening_basis": "opening = |F_S min| x (1 / k_b + 1 / k_sh): at the minimum the fit is open, so screw and shell act in series (CALC)",
        "audit": ("PRELOAD-RETENTION AUDIT (adopted 11:25Z): J-F1 calibrates crack-on torque against clamp on the IN718 flight lot; after the "
                  "first hot fire or a TB soak test, before disassembly, each screw's crack-on torque is read and converted to residual clamp; "
                  "breakaway torque logged; 10x inspection for fretting and set"),
        "cold_residual_note": "the cold end keeps a residual clamp at every case (2250 N installation minimum above); the loss of contact is a hot transient"},
    "alternative_a_series_compliance": {"per_end": alt_a, "E_IN718_20C_MPa": round(E20), "A_s_mm2": A_S,
                                        "note": ("the added series compliance that seats all 24 at each k_b end; as free length at A_s it does not fit "
                                                 "(240 (10): extra free length does not fit; a TC-02 tap-mouth relief is NOT pursued); a disc spring is the "
                                                 "only compliant element that fits, and it acts as a force floor (route (i)), not as a linear compliance")},
    "common_to_both_routes": ["the strength rows are unchanged by either route (the spring is solid at every hot frame): the seat = ring line P+Q "
                              "negatives (SOAK70 / SOAK / SOAK52) and the screw fibre / LCF FOUND NEGATIVES stand; the TC-02 thread row is on THE "
                              "ROW (rows v6) in both (with the spring the length grows by t and the engagement is unchanged within t_max - t_nom)",
                              "everything is on the worst computed instance of the adopted envelope v3 (not a proven bound); (b2'), (b1) and js5b "
                              "join after chain E (R3)"]}
out["slack_fix_inputs"] = slack

# ------------------------------------------------------------------ 9: abort table and recommendation
floor = out["normal_operation_case_TC"]["false_trip_floor_C"]
gvhi_r4 = no["B1 rev 4 GVHI"]["armed_max_C"]
gvlo_r4 = no["B1 rev 4 GVLO"]["armed_max_C"]
table = []
for st, A in STATES.items():
    row = {"abort_C": A, "abort_K": round(A + 273.15, 2), "false_trip_margin_K": {"vs merged rev 3 (perfect contact)": round(A - floor, 2),
                                                                                 "vs B1 rev 4 GVHI": round(A - gvhi_r4, 2), "vs B1 rev 4 GVLO": round(A - gvlo_r4, 2)}}
    for bd in BDS:
        b = {}
        for case in ("TB70", "TBS"):
            s = seat[bd][case].get(st, {})
            if A_ not in s:
                b[case] = "NOT RUN"
                continue
            b[case] = {p[-5:]: {"abc": s[p]["verdict_183_1_abc"], "a_prim_u": s[p]["MS_prim_u"]["MS"], "b_PQ": s[p]["MS_PQ"]["MS"],
                                "c_LCF": s[p]["MS_LCF"]["MS"], "combined_y": s[p]["MS_y"]["MS"], "combined_u": s[p]["MS_u"]["MS"],
                                "SF1_info": s[p]["MS_y_SF1"]["MS"]} for p in (A_, B_)}
            b[case]["no_leak"] = leak[bd][case][st]["verdict"].split(":")[0]
        e = expo[bd]["per_abort"][st]
        b["d"] = {"TC02_TB_state_C": e["ENG-TC-02"]["TB_state_max_C"], "TC02_t_above_150C_s": e["ENG-TC-02"]["t_above_150C_s"],
                  "TC01_shifted_max_C": e["ENG-TC-01"]["shifted_history_max_C"], "TC01_t_above_150C_s": e["ENG-TC-01"]["t_above_150C_s"],
                  "TC03_TB_state_C": e["ENG-TC-03"]["TB_state_max_C"], "verdict": "OPEN (T-F1)"}
        b["non_seat_flags"] = glob[bd]["TB70"][st]["non_seat_flags"]
        row[bd] = b
    table.append(row)
out["abort_table"] = table
out["false_trip_reference"] = {"merged_rev3_B1_station_C": floor, "B1_rev4_GVHI_station_C": gvhi_r4, "B1_rev4_GVLO_station_C": gvlo_r4,
                               "A1_merged_station_C": [q["station_max_C"] for q in no["A1 rev 3 merged (perfect contact)"]["armed_phases"]]}

# ------------------------------------------------------------------ 10: recommendation (Mechanical's; the lead sets the value)
crit = {}
for st, A in STATES.items():
    ok_abc, ok_leak, missing = True, True, []
    for bd in BDS:
        for case in ("TB70", "TBS"):
            s = seat[bd][case].get(st, {})
            if A_ not in s:
                missing.append(f"{bd} {case}")
                continue
            for p in (A_, B_):
                ok_abc &= s[p]["verdict_183_1_abc"].startswith("PASS")
            ok_leak &= leak[bd][case][st]["verdict"].startswith("NO LEAK")
    e = {bd: expo[bd]["per_abort"][st] for bd in BDS}
    crit[st] = {"abort_C": A, "abc_and_no_leak_both_bounds": (ok_abc and ok_leak) if not missing else f"INCOMPLETE ({', '.join(missing)} not run)",
                "above_merged_armed_max": A > floor, "margin_to_merged_K": round(A - floor, 2),
                "TC02_post_trip_soak_below_150C (shifted history <= 60 s above 150 C, both bounds)": all(e[bd]["ENG-TC-02"]["t_above_150C_s"] <= 60.0 for bd in BDS),
                "TC01_at_trip_within_150C": A <= LIM6061,
                "TC02_TB_state_C": [e[bd]["ENG-TC-02"]["TB_state_max_C"] for bd in BDS],
                "TC02_t_above_150C_s": [e[bd]["ENG-TC-02"]["t_above_150C_s"] for bd in BDS],
                "TC01_t_above_150C_s": [e[bd]["ENG-TC-01"]["t_above_150C_s"] for bd in BDS], "d": "OPEN (T-F1)"}
cand = [c for c in crit.values() if c["abc_and_no_leak_both_bounds"] is True and c["above_merged_armed_max"]
        and c["TC02_post_trip_soak_below_150C (shifted history <= 60 s above 150 C, both bounds)"] and c["TC01_at_trip_within_150C"]]
rec = max(cand, key=lambda c: c["abort_C"]) if cand else None
out["recommendation"] = {
    "screening_per_A": crit,
    "recommended_abort_C": rec["abort_C"] if rec else None,
    "text": (("Mechanical recommends A = %.0f C (%.2f K) on the case TC station: the highest trial value that (1) passes 183 (1) (a)-(c) and "
              "no leak on both bounds for TB70 (1.5 / 2.0) and TBS (1.0 / 1.5) under the seat-matrix rule and under min(C5, C3n, C4n); (2) stays "
              "above every normal-operation armed-phase station maximum, by %+.1f K over the rev-3 merged perfect-contact B1 burn (%.2f C), "
              "%+.1f K over B1 rev 4 GVHI and %+.1f K over GVLO; (3) limits TC-02's time above 150 C after the trip to %s s (GVLO | GVHI; "
              "ASSUMED shifted history: the TC-02 soak plateau stays below 150 C), against 640-1192 s at 165-175 C; (4) holds the TC-01 "
              "maximum at the trip at its 150 C usable limit, within the station offset (the TC-01 maximum runs 1.4-1.5 K above the station "
              "on the GV bounds and 2.6 K on the merged run). (d) stays "
              "OPEN at every A and in nominal operation (T-F1 gate); at this A the T-F1 coupon temperature is the TB part maximum TC-02 %s C "
              "(GVLO | GVHI) and the TC-01 shifted-soak maximum %s C. The 175 C (448.15 K) value of line 188 (5) cannot be shown against a "
              "sourced short-time allowable (T-F1 not obtained) and leaves TC-01 above its usable limit at the trip and TC-02 above 150 C "
              "for about 20 min after it (ASSUMED). Electronics confirms that its channel tolerance fits inside the %.1f K margin to the "
              "merged armed maximum; if it does not, the next lower trial value (135 C) is BELOW the merged armed maximum and would trip "
              "a nominal burn in the perfect-contact bound.") % (
                 rec["abort_C"], rec["abort_C"] + 273.15, rec["abort_C"] - floor, floor, rec["abort_C"] - gvhi_r4, rec["abort_C"] - gvlo_r4,
                 " | ".join(f"{x:g}" for x in rec["TC02_t_above_150C_s"]), " | ".join(f"{x:g}" for x in rec["TC02_TB_state_C"]),
                 " | ".join(f"{expo[bd]['per_abort'][[k for k, v in STATES.items() if v == rec['abort_C']][0]]['ENG-TC-01']['shifted_history_max_C']:g}" for bd in BDS),
                 rec["abort_C"] - floor) if rec else
             "No trial abort value meets all four screens; see screening_per_A (the T-F3 / undercut-radius path of 239 (7) applies only "
             "where (a)-(c) fail)."),
    "notes": ["(a) on the frictional variants: the mechanical increment S2 - S1 at the TC-02 entry-tangent contact edge includes the change of "
              "the frictional contact state between the thermal-only and the total step (path-dependent); the C3n / C4n (a) cells are "
              "non-monotonic in A and all positive; C5 (frictionless) gives the larger values; shown as found.",
              "TC-02 / TC-03 regular cells at the entry-tangent contact edge: at the TB reference (TBS TB) the C5 / C3n / C4n regular value "
              "does not pass the 5 % refinement test (demand +8-9 % per halving, decreasing); the cells take the regular value by the 234 (4) "
              "thread-tie rule (the all-node minimum sits at the smeared-thread tie end, replaced by the J-TC03 CALC), are quoted at h 0.1 "
              "with the h 0.05 estimate beside them, and the verdicts hold at the estimate (verdict_abc_at_h0p05_estimate).",
              "Combined MS at the case SF is negative for TC-02 / TC-03 at TB70 for the higher A (TS-183 candidates): accepted only with "
              "(a)-(c) passing and (d), which is OPEN (T-F1).",
              "No new thermal run was made; no CAD change is proposed by this package."]}
out["recommendation"]["undercut_and_T_F3"] = ("Not triggered by (a)-(c): every computed A passes (a)-(c) on both bounds. (d) is a material-exposure "
                                              "item (T-F1), which the undercut radius does not move; T-F3 follows only if T-F1 fails.")
s = json.dumps(out, indent=1, default=float)
OUT.write_text(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
