"""J-FWD screw-dependent rows re-issued for the ruled screw IN718 M5 x10 (ENG-HW-101-IN718), lead 11:25Z item 2, 11:41Z, 12:09Z item 5,
relay 12:28Z, relay 13:14Z, lead 14:03Z item 3.  Mechanical, 2026-10-20, v4 (v3 0a8aa3f87c0fc8bc / json f69595255aa9543d ACCEPTED by the
lead 14:03Z, kept as jfwd_in718_rows_v352_v3.py; v2 b92cef86a2bc3919 kept).  [DERIVED] from SIM (FEA3D js5 complete run + seat patches (a),
(a') and (a'')); no new run.  CALC / DERIVED, not physical approval.

v4 (lead 14:03Z item 3, rev 5: r_flat 31.313 +0.020/0 from A, TC-01 OD 63.5 h9 with circular runout 0.04 to A, both ADOPTED):
 (a) every TC-01 flat-bearing row carries the worst-stack supported-area loss on the row's own area basis.  The row is FEA3D's
     jfwd_spotface.py head_bearing 'flat_seat_MS_vs_Fbry' = Fbry / (F_head / A_ANN) - 1 with A_ANN = pi/4 (9.5^2 - 5.5^2) = 47.12 mm2 (dk 9.5);
     at the worst stack (OD 63.426 = 63.5 h9 minimum, eccentricity 0.02 = runout 0.04 / 2, r_flat 31.333 = rule maximum, head at the full
     float 0.337 tangentially) the head ring beyond the flat's tangential edge is CALC 0.749 mm2 for dk 9.5 and 0.218 mm2 for dk 9.14; on the
     47.12 basis the smaller supported area is 47.12 - 0.749 -> the row x (1 - 0.749 / 47.12).  The full-flat value is kept beside.
     INFORMATION (not applied, the row's own basis is kept as ruled): the 47.12 basis is the dk 9.5 MAXIMUM head; at the dk 9.14 minimum the
     ring is 41.85 mm2 (41.63 after its 0.218 loss).
 (b) the TC-01 case membrane rows (03-cad/calcs hand_calcs_v2.json, Lame + end load at the bore) use the NOMINAL OD 63.5 and the nominal
     bore (walls 3.175 full wall / 3.125 fwd seal land / 2.675 collar groove): the h9 radial -0.037 (and the H8 maximum bore +0.023 at the
     fwd seal land) re-evaluated on every row whose outer surface is the 63.5 OD; the aft seal land (61.0) and the aft thread (M63 x 1.5) are
     separate diameters.
 Otherwise as v3 (the screw LCF row is jfwd_screw_lcf_v352, on this json).

v3: relaxation v6 (four histories: (a'') = seat_s5L12_mu0_go joins; FEA3D envelope 336568296bdb896f): every row takes the worst of the four
histories per state and quantity; k_b lo re-calibrated on (a'') SOAK70; the PRELOAD moment envelope is (a'')'s.  Otherwise as v2.

v2: (1) the envelope is FEA3D's 12:21Z three-history envelope (js5, (a), (a'); results/v352/jfwd_soak_envelope_v352.json 1d970741cb95a885,
read through relax v5 which cross-checks it): SOAK70 N max 6389 (a), SOAK 7383 (js5), SOAK52 6742 (a'); (2) the k_b bracket of relax v5
(lo on (a') SOAK70 5627.3 N, hi on (a) SOAK70 6389.1 N); (3) FEA3D's TC-01 ligament-station P+Q is scaled per history (js5 only reports
that station: N_IN,js5 / N_js5) and carried as INFORMATION (contact-edge field, 0.08 mm from the hole wall, like the hole-edge line class
of 239 (9)); the envelope-scaled value is quoted beside it; (4) the TC-02 A_n thread-shear FULL ROW (lead 12:09Z item 5) with the
engagement basis and the cheapest fixes and their slack effect.

Basis (stated per row in the output):
 - FE ANCHOR = the worst of the sharp-edge histories per state and per quantity (lead 11:41Z): highest screw N, lowest seat window,
   lowest MS per line, highest screw section moment.  A4-80 values are the FE's own (the FE screw is A4-80); IN718 is mapped onto them.
 - IN718 screw force per history h and state: N_IN = F_V + (N_h - F_V) x r, r = (model IN718 soak gain) / (model A4-80 soak gain) at that
   state's temperatures (relax v5 joint model; max over the k_b bracket; F_V = 3750 N, the FE preload).  dF_S / dF_V = 1.000 in the
   model at every soak state, so the J-F1 maximum 4096 N adds 346 N.  Rows are given at 3750 N (the FE basis, as FEA3D's cells) and at
   4096 N (the J-F1 maximum: 239 (3) 'strength checks at the maximum preload'; 239 (8)(a) P+Q at 3750 and 4096 N).
 - force-driven rows scale with N_IN / N_h on the FE row of the same history (screw tension, thread shear, flat bearing, under-head band,
   Pm line counts): conservative where part of the stress is thermal and of the same sign.
 - seat / ring-line P+Q: (i) model-consistent, P+Q x F_sh,model(IN718) / F_sh,model(A4-80) (the lines track the shell pull, relax v4
   item 4); (ii) bound, P+Q x N_IN / N_h.  The row is (i); (ii) is quoted beside and flagged where the two straddle zero.
 - screw moment for IN718: M_h x E ratio (imposed rotation) x max(1, F_c,IN / F_c,h) (the extra screw force goes to the seat contact,
   K_C / (K_C + k_sh) of it): the product, conservative.
 - allowables: IN718 Fty / Ftu(T) AMS 5662/5663 minima (Special Metals SMC-045, engmat DATASHEET); AL6061-T6 engmat (10,000 h basis,
   LITERATURE); TC-02 thread Fsy = 0.577 Fty, Fsu = 0.6 Ftu (FEA3D's rule, back-computed from its cells and verified); FEA3D's Neuber
   (eps = s / E + 0.002 (s / Fty)^n, n 15 and 30, eps_limit of the node, the lower MS) reproduced exactly on js5 SOAK.
 - TC-02 A_n: FEA3D's cell A_n = N / tau = 63.48 mm2 = the strip area of jfwd_v352 at L_eff 6.35 mm (= the v3.5.1 engagement 6.85 less the
   0.5 mm mouth, the jfwd_preload v2 basis).  The v3.5.2 spot-face engagement is longer (jfwd_seat_v352_v1: L_e 7.287 CAD, 7.257 at the
   drawing minimum of the f7 plug): quoted as a BASIS CHECK for FEA3D, not credited in the row.
 - every row within 0.05 of zero (or negative) is flagged for an FE confirmation (lead 11:25Z)."""
import json, math, hashlib, importlib.util
from pathlib import Path

J = Path("/home/claude/work/mechanical/v352/jfwd")
OUT = J / "jfwd_in718_rows_v352_v4.json"
_spec = importlib.util.spec_from_file_location("jfwd_relax_v352_v6", str(J / "jfwd_relax_v352.py"))
R = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R)
assert "v6 (v5 95409d512c83bb44" in R.__doc__
sha = R.sha
tab = R.tab
CELLS = json.loads(R.F_CELLS.read_text())["steps"]
FIX2 = J / "jfwd_fix_v352_v2.json"
fix2 = json.loads(FIX2.read_text())
SEAT1 = J / "jfwd_seat_v352_v1.json"
seat1 = json.loads(SEAT1.read_text())
_ns = {}
exec(compile((J / "jfwd_v352.py").read_text().split("\nOPTS = [")[0], str(J / "jfwd_v352.py"), "exec"), _ns)
strip_area, TH = _ns["strip_area"], _ns["TH"]["M5"]
IN, A4 = R.IN718_S, R.A4_80
FV0, FVMAX = 3750.0, 4096.0
A_S, Z_3 = IN.A_s, IN.Z_3
HS = R.H
LBL = R.LABEL
FLAG = 0.05


def flag(ms):
    return None if ms is None else ("NEGATIVE: FE confirmation" if ms < 0 else ("within 0.05: FE confirmation" if ms < FLAG else None))


def ms(allow, act):
    return round(allow / act - 1.0, 3)


def neuber(sel, E, Fty, n):
    lo, hi = 1e-9, max(sel, 1e-6)
    for _ in range(200):
        s = 0.5 * (lo + hi)
        e = s / E + 0.002 * (s / Fty) ** n
        lo, hi = (s, hi) if s * e < sel * sel / E else (lo, s)
    return s, s / E + 0.002 * (s / Fty) ** n


def cmp_side(h, st):
    """the compare-file column of history h at state st: js5 = the global columns of patch (a)'s compare (identical in every patch's file,
    checked in relax v5); a patch = its own 'patch' columns."""
    return R._CM["patch_a"]["steps"][st]["global_same_sets"] if h == "js5" else R._CM[h]["steps"][st]["patch"]


def cmp_lines(h, st):
    f = "patch_a" if h == "js5" else h
    return R._CM[f]["steps"][st]["relax_seat_lines_cmp"], ("Pm_global" if h == "js5" else "Pm_patch")


# ---- IN718 / A4-80 gain ratio per state (model, both k_b ends; max) and the FA1S thermal delta (uniform 45.6 C, no pressure)
RATIO, FSH_RATIO = {}, {}
for st in R.SOAKS:
    rs, fs = [], []
    for e, kb in R.KB.items():
        a = R.model_state(st, kb, A4)
        b = R.model_state(st, kb, IN)
        rs.append((b[0] - FV0) / (a[0] - FV0))
        fs.append(b[3] / a[3])
    RATIO[st], FSH_RATIO[st] = max(rs), max(fs)
DFA1S = []
for e, kb in R.KB.items():
    _, dwa, dra = A4.deltas(45.6, 45.6)
    _, dwi, dri = IN.deltas(45.6, 45.6)
    DFA1S.append(R.state_s(FV0, R.G0, dwi, dri, 0, 0, R.K_SH_JS5, kb * IN.kb_ratio)[0] - R.state_s(FV0, R.G0, dwa, dra, 0, 0, R.K_SH_JS5, kb)[0])
D_FA1S = max(DFA1S)
D_FVMAX = max(R.model_state("SOAK", kb, IN, FV=FVMAX)[0] - R.model_state("SOAK", kb, IN, FV=FV0)[0] for kb in R.KB.values())


def n_in(st, h, FV=FV0):
    N = R.HISTS[st][h]["N_head_N"]
    if st == "PRELOAD":
        base = FV0
    elif st == "FA1S":
        base = N + D_FA1S
    else:
        base = FV0 + (N - FV0) * RATIO[st]
    return base + (FV - FV0) * (1.0 if st in ("PRELOAD", "FA1S") else D_FVMAX / (FVMAX - FV0))


# ---- v4 (a): rev-5 worst-stack supported area of the head ring on the TC-01 flat (CALC; lead 14:03Z item 3(a))
A_ANN = math.pi / 4.0 * (9.5 ** 2 - 5.5 ** 2)          # FEA3D jfwd_spotface.py A_ANN (the flat-bearing row's own basis)


def _segment(rh, d):
    """area of a circle of radius rh beyond a straight line at distance d from its centre"""
    if d >= rh:
        return 0.0
    if d <= -rh:
        return math.pi * rh * rh
    return rh * rh * math.acos(d / rh) - d * math.sqrt(rh * rh - d * d)


def flat_stack(od_min=63.5 - 0.074, ecc=0.02, rf_max=31.333, flt=0.337):
    R_loc = od_min / 2.0 - ecc
    half = math.sqrt(R_loc ** 2 - rf_max ** 2)
    out = {"OD_min_mm": od_min, "eccentricity_mm": ecc, "r_flat_max_mm": rf_max, "float_mm": flt, "chord_mm": round(2 * half, 3),
           "chord_nominal_OD_no_runout_mm": round(2 * math.sqrt(31.75 ** 2 - rf_max ** 2), 3)}
    for dk in (9.5, 9.14):
        out[f"loss_dk{dk:g}_mm2"] = round(_segment(dk / 2.0, half - flt), 3)
        out[f"ring_dk{dk:g}_mm2"] = round(math.pi / 4.0 * (dk ** 2 - 5.5 ** 2), 2)
        out[f"overhang_dk{dk:g}_mm"] = round(max(0.0, flt + dk / 2.0 - half), 3)
    out["supported_fraction_row_basis"] = round(1.0 - out["loss_dk9.5_mm2"] / A_ANN, 5)
    out["info_dk9.14_min_head_supported_mm2"] = round(out["ring_dk9.14_mm2"] - out["loss_dk9.14_mm2"], 2)
    out["info_dk9.14_fraction_of_row_basis"] = round(out["info_dk9.14_min_head_supported_mm2"] / A_ANN, 5)
    return out


FLAT = flat_stack()


def rows_state(st):
    c = CELLS[st]
    out = {"state": st, "kind": c["kind"], "histories": {}}
    for h in HS:
        out["histories"][LBL[h]] = {"entered_from": R.HISTS[st][h]["entered_from"], "N_FE_A4-80_N": R.HISTS[st][h]["N_head_N"],
                                    "N_IN718_3750_N": round(n_in(st, h), 1), "N_IN718_4096_N": round(n_in(st, h, FVMAX), 1)}
    henv = max(HS, key=lambda h: n_in(st, h))
    out["N_envelope_from"] = LBL[henv]
    rows = {}
    for FV, tag in ((FV0, "3750"), (FVMAX, "4096")):
        Nenv = n_in(st, henv, FV)
        r = {}
        # (1) screw tension 234 (1)(b) (soak form; PRELOAD and FA1S tension shown for information, FA1S governing = Eq. 22 below)
        Ts = c["SCREW"]["T_C"]
        sig = Nenv / A_S
        Fy, Fu = tab("IN718", "Fty", Ts), tab("IN718", "Ftu", Ts)
        r["screw_tension_234_1b"] = {"N_N": round(Nenv, 1), "from": LBL[henv], "sigma_As_MPa": round(sig, 1), "T_C": Ts, "Fty_IN718_MPa": round(Fy, 1),
                                     "Ftu_IN718_MPa": round(Fu, 1), "MS_y": ms(Fy, sig), "MS_u": ms(Fu, sig),
                                     "A4-80_FE_MS_y_at_FE_N": c["SCREW"].get("MS_y") if st != "FA1S" else None}
        # (2) TC-02 internal thread shear on FEA3D's A_n (back-computed from its cell; allowables back-computed and checked against engmat)
        th = c["TC-02"]["thread_shear_An"]
        Nfe_js5 = R.HISTS[st]["js5"]["N_head_N"] if st != "FA1S" else c["SCREW"]["N_exact_N"]
        A_n = Nfe_js5 / th["tau_MPa"]
        fsy, fsu = (1 + th["MS_y"]) * th["tau_MPa"], (1 + th["MS_u"]) * th["tau_MPa"]
        T2 = th["T_C"]
        assert abs(fsy - 0.577 * tab("AL6061-T6", "Fty", T2)) < 0.6 and abs(fsu - 0.6 * tab("AL6061-T6", "Ftu", T2)) < 0.6
        tau = Nenv / A_n
        r["TC02_thread_shear_An"] = {"A_n_mm2_FEA3D": round(A_n, 2), "T_C": T2, "N_N": round(Nenv, 1), "tau_MPa": round(tau, 1), "Fsy_MPa": round(fsy, 1),
                                     "Fsu_MPa": round(fsu, 1), "MS_y": ms(fsy, tau), "MS_u": ms(fsu, tau),
                                     "A4-80_FE": {"MS_y": th["MS_y"], "MS_u": th["MS_u"], "at_N": Nfe_js5}}
        # (3) TC-01 spot-face flat bearing (FEA3D seat_values_DERIVED, head force on the flat) and the under-head band (Neuber)
        if st != "FA1S":
            fb = c["TC-01"]["cell"]["seat_values_DERIVED"]["flat_seat_bearing_MS_vs_Fbry"]
            full = (1 + fb) * Nfe_js5 / Nenv - 1.0
            r["TC01_flat_bearing"] = {"MS_vs_Fbry": round((1 + full) * FLAT["supported_fraction_row_basis"] - 1.0, 3), "MS_vs_Fbry_full_flat": round(full, 3),
                                      "area_basis_mm2": round(A_ANN, 2), "area_loss_mm2": FLAT["loss_dk9.5_mm2"], "A4-80_FE_MS_at_FE_N": fb}
        uh = {}
        for h in HS:
            Nh = R.HISTS[st][h]["N_head_N"]
            Ni = n_in(st, h, FV)
            if h == "js5":
                nb = c["TC-01"]["neuber_band"]
                sel0, T, E, Fty, el = nb["sigma_el_MPa"], nb["T_C"], nb["E_MPa"], nb["Fty_MPa"], nb["eps_limit"]
            else:
                ub = cmp_side(h, st)["under_head_band"]
                sel0, T, Fty, el = ub["vm_MPa"], ub["T_C"], ub["Fty_MPa"], ub["eps_limit"]
                E = tab("AL6061-T6", "E", T)
            sel = sel0 * Ni / Nh
            mss = []
            for n in (15, 30):
                s_, e_ = neuber(sel, E, Fty, n)
                mss.append(round(el / e_ - 1.0, 3))
            uh[LBL[h]] = {"sigma_el_A4-80_MPa": sel0, "sigma_el_IN718_MPa": round(sel, 1), "T_C": T, "eps_limit": el, "MS_strain_n15_n30": mss, "MS_strain": min(mss)}
        hw = min(uh, key=lambda k: uh[k]["MS_strain"])
        r["TC01_under_head_band_neuber"] = {"per_history": uh, "MS_strain": uh[hw]["MS_strain"], "from": hw}
        # (4) FEA3D's TC-01 ligament-station P+Q (cell, js5 station delta 5.688 side +): js5-history scaling; INFORMATION (contact-edge field)
        if st != "FA1S":
            lg = c["TC-01"]["SCL_PQ_ligament_station_max_cad"]
            Tl = R.HISTS[st]["js5"]["seat_line_T_C"]
            two_fy = 2.0 * tab("AL6061-T6", "Fty", Tl)
            pq = lg["PmPb"] * n_in(st, "js5", FV) / Nfe_js5
            pqb = lg["PmPb"] * Nenv / Nfe_js5
            r["TC01_ligament_station_PQ_FEA3D_cell_INFO"] = {
                "PmPb_A4-80_MPa": lg["PmPb"], "PmPb_IN718_js5_history_MPa": round(pq, 1), "two_Fty_MPa": round(two_fy, 1), "MS_PQ_2Fty_info": ms(two_fy, pq),
                "envelope_scaled_bound_info": {"PmPb_MPa": round(pqb, 1), "MS": ms(two_fy, pqb), "N_from": LBL[henv]}, "A4-80_FE_MS": lg["MS_PQ_2Fty"],
                "class": ("INFORMATION: contact-edge field (station 0.08 mm from the hole wall, inside the near-edge gradient: 572 / 346 / ~262 MPa at "
                          "0.08 / 0.26 / 0.52 mm at js5 SOAK70), like the hole-edge line class of 239 (9); only js5 reports this station, so the "
                          "row scales with the js5 history's own force; not a cell")}
        # (5) seat line d+6.051 z'0 and ring line: P+Q vs 2 Fty(T), per history; (i) F_sh-consistent, (ii) head-force bound
        if st in R.SOAKS + ("PRELOAD",):
            for fam, key in (("seat_line_d6p051_z0", "seat_line_PmPb_MPa"), ("ring_line", None)):
                per = {}
                for h in HS:
                    x = R.HISTS[st][h]
                    if key:
                        pq0, T = x[key], x["seat_line_T_C"]
                    else:
                        cand = [(x["ring_line_d8p02_PmPb_MPa"], cmp_side(h, st)["lines"]["ring"]["T_mean_C"])]
                        if h == "js5" and x.get("ring_line_d8p126_PmPb_MPa") is not None:
                            g = R._rel["steps"][st if st != "PRELOAD" else "SOAK70"]["families"]["ring"]["governing_by_soak_PQ"]
                            cand.append((x["ring_line_d8p126_PmPb_MPa"], g["T_soak_mean_C"] if st != "PRELOAD" else 20.0))
                        pq0, T = max(cand)
                    if st == "PRELOAD":
                        T = 20.0
                    two_fy = 2.0 * tab("AL6061-T6", "Fty", T)
                    fr = FSH_RATIO.get(st, 1.0) if st != "PRELOAD" else 1.0
                    if FV == FVMAX:
                        # +346 N installation: the shell pull rises by dF_sh / dF_V of the model at that state (hi end; the lo end is within 0.1 %)
                        kb = R.KB["hi"]
                        a_ = R.model_state(st, kb, IN, FV=FV0) if st != "PRELOAD" else R.state_s(FV0, R.G0, 0, 0, 0, 0, R.K_SH_JS5, kb * IN.kb_ratio)
                        b_ = R.model_state(st, kb, IN, FV=FVMAX) if st != "PRELOAD" else R.state_s(FVMAX, R.G0, 0, 0, 0, 0, R.K_SH_JS5, kb * IN.kb_ratio)
                        fr = fr * b_[3] / a_[3]
                    pq_i = pq0 * fr
                    pq_ii = pq0 * n_in(st, h, FV) / x["N_head_N"]
                    per[LBL[h]] = {"PmPb_A4-80_MPa": pq0, "T_C": T, "two_Fty_MPa": round(two_fy, 1), "PmPb_IN718_Fsh_MPa": round(pq_i, 1), "MS_PQ_Fsh": ms(two_fy, pq_i),
                                   "PmPb_IN718_headforce_bound_MPa": round(pq_ii, 1), "MS_PQ_headforce_bound": ms(two_fy, pq_ii)}
                hw = min(per, key=lambda k: per[k]["MS_PQ_Fsh"])
                hb = min(per, key=lambda k: per[k]["MS_PQ_headforce_bound"])
                r[fam + "_PQ"] = {"per_history": per, "MS_PQ_2Fty": per[hw]["MS_PQ_Fsh"], "from": hw,
                                  "bound_MS": per[hb]["MS_PQ_headforce_bound"], "bound_from": hb}
        # (6) number of TC-01 lines with Pm > Fty(T) (54 seat + 10 hole-edge lines), per history, head-force scaling (bound) and F_sh scaling
        if st in R.SOAKS:
            cnt = {}
            for h in HS:
                Nh = R.HISTS[st][h]["N_head_N"]
                k_n = n_in(st, h, FV) / Nh
                k_s = FSH_RATIO[st]
                lines, pmk = cmp_lines(h, st)
                fam_counts = {}
                for fam in ("seat", "hole_edge"):
                    ls = [q for q in lines if q["family"] == fam]
                    fy = lambda q: tab("AL6061-T6", "Fty", q["T_mean_C"])
                    fam_counts[fam] = {"A4-80": sum(1 for q in ls if q[pmk] > fy(q)), "IN718_Fsh": sum(1 for q in ls if q[pmk] * k_s > fy(q)),
                                       "IN718_headforce_bound": sum(1 for q in ls if q[pmk] * k_n > fy(q)),
                                       "max_Pm_over_Fty_bound": round(max(q[pmk] * k_n / fy(q) for q in ls), 3), "n_lines": len(ls)}
                cnt[LBL[h]] = fam_counts
            r["TC01_lines_Pm_gt_Fty"] = {"per_history": cnt,
                                         "envelope": {fam: {k: max(cnt[LBL[h]][fam][k] for h in HS) for k in ("A4-80", "IN718_Fsh", "IN718_headforce_bound", "max_Pm_over_Fty_bound")}
                                                      for fam in ("seat", "hole_edge")},
                                         "js5_relax_json_count_A4-80": {fam: R._rel["steps"][st]["families"][fam]["n_lines_soak_Pm_gt_Fty"] for fam in ("seat", "hole_edge")}}
        # (7) screw fibre at the soak (secondary bending, ruling 10:08:57Z): fibre yield = screw plastic set; shakedown vs 2 Fty_IN718(T)
        if st in R.SOAKS:
            fib = {}
            pre = R.HISTS["PRELOAD"]
            # cold end of the range: the LOWEST PRELOAD section force and moment over the histories (conservative for the range)
            Nsec_pre = min(pre[h]["N_section_max_N"] for h in HS) * FV / FV0
            M_pre = R.M_PRE_MIN * IN.tilt_ratio * FV / FV0
            f_pre = Nsec_pre / A_S + M_pre / Z_3
            for h in HS:
                x = R.HISTS[st][h]
                Ni = n_in(st, h, FV)
                Nsec = x["N_section_max_N"] * Ni / x["N_head_N"]
                Fc_in = x["seat_radial_N"] + (Ni - x["N_head_N"]) * R.K_C / (R.K_C + R.K_SH_JS5)
                M_in = x["M_max_Nmm"] * IN.tilt_ratio * max(1.0, Fc_in / x["seat_radial_N"])
                f = Nsec / A_S + M_in / Z_3
                rp = tab("IN718", "Fty", Ts)
                rngf = f - f_pre
                # plastic set estimate: elastic section N/A + M y / I over the circular d3 section; the yielded segment's excess integrated
                # (section-averaged), as an equivalent uniform axial set over the free length L_FREE (upper estimate of the preload loss)
                d3 = (32.0 * Z_3 / math.pi) ** (1.0 / 3.0)
                cc = d3 / 2.0
                sN, sM = Nsec / A_S, M_in / Z_3
                exc, ny = 0.0, 400
                for i in range(ny):
                    y = -cc + (i + 0.5) * 2 * cc / ny
                    wdt = 2.0 * math.sqrt(max(cc * cc - y * y, 0.0))
                    s_ = sN + sM * y / cc
                    exc += max(0.0, s_ - rp) * wdt * (2 * cc / ny)
                dp_um = exc / (R.tab("IN718", "E", Ts) * 1e-6 * 1e6) * R.RV3.L_FREE / (math.pi * cc * cc) * 1e3 if exc > 0 else 0.0
                fib[LBL[h]] = {"N_section_N": round(Nsec, 1), "M_Nmm": round(M_in, 1), "fibre_MPa": round(f, 1), "Fty_IN718_MPa": round(rp, 1), "MS_y_fibre": ms(rp, f),
                               "fibre_cold_MPa": round(f_pre, 1), "range_MPa": round(rngf, 1), "two_Fty_MPa": round(2 * rp, 1), "MS_shakedown": ms(2 * rp, rngf),
                               "section_excess_N": round(exc, 1), "equiv_axial_set_um": round(dp_um, 3)}
            hw = min(fib, key=lambda k: fib[k]["MS_y_fibre"])
            r["screw_fibre_soak"] = {"per_history": fib, "MS_y_fibre": fib[hw]["MS_y_fibre"], "MS_shakedown": min(v["MS_shakedown"] for v in fib.values()),
                                     "range_max_MPa": max(v["range_MPa"] for v in fib.values()), "max_equiv_axial_set_um": max(v["equiv_axial_set_um"] for v in fib.values()),
                                     "from": hw}
        rows[tag] = r
    out["rows"] = rows
    return out


# ---- TC-02 A_n thread shear: the full row, the engagement basis and the cheapest fixes (lead 12:09Z item 5; no hardware change before the ruling)
ENG = seat1["tc02_engagement"]
R_FLAT_CAD = ENG["r_flat_mm"]                      # 31.3129: the d10.5 flat on R31.75
R_PLUG_CAD, R_PLUG_DWG = 28.6, (57.140 / 2.0, 57.170 / 2.0)
D_SPOT_TOL = 0.2                                   # spot-face diameter, ISO 2768-m general tolerance for 6-30 mm (ASSUMED until the drawing states one)
R_OD = 63.5 / 2.0


def r_flat(d_spot):
    return math.sqrt(R_OD ** 2 - (d_spot / 2.0) ** 2)


R_FLAT_RANGE = (r_flat(10.5 + D_SPOT_TOL), r_flat(10.5 - D_SPOT_TOL))     # deeper flat (larger spot face) .. shallower flat
FULL_THREAD = 8.0                                  # TC-02 M5-6H full-thread depth from the TC-02 OD (CAD jfwd_tap_drill_mm 9.0 / full thread 8.0)
MOUTH = 0.5                                        # first 0.5 mm of the tap mouth not credited (jfwd_preload basis)
TIP_CLEAR_MIN = 0.2                                # screw tip at least 0.2 mm short of the full-thread end at the worst stack (no run into the runout)
ISO_L_TOL = 0.29                                   # ISO 4759-1 grade A length tolerance js15 at l = 10 (AS RECALLED, TO-VERIFY) - standard ISO 7380-1 part
assert abs(r_flat(10.5) - R_FLAT_CAD) < 2e-4


def eng_case(L_nom, tol, h_under=0.0):
    """min engagement (shortest screw, shallowest flat, smallest plug) and tip clearance to the full-thread end (longest screw, deepest flat,
    largest plug incl. the CAD nominal); h_under = a part under the head (min height for the tip, max height for the engagement)."""
    hu = (h_under, h_under) if not isinstance(h_under, tuple) else h_under
    Le_min = (L_nom - tol) - (R_FLAT_RANGE[1] + hu[1] - R_PLUG_DWG[0])
    clr = (R_FLAT_RANGE[0] + hu[0] - (L_nom + tol)) - (max(R_PLUG_CAD, R_PLUG_DWG[1]) - FULL_THREAD)
    Leff = Le_min - MOUTH
    return {"L_nom_mm": L_nom, "L_tol_mm": tol, "L_e_min_mm": round(Le_min, 3), "L_eff_min_mm": round(Leff, 3), "A_n_mm2": round(strip_area(TH, Leff), 2),
            "tip_clearance_to_full_thread_end_min_mm": round(clr, 3), "tip_ok": clr >= TIP_CLEAR_MIN - 1e-9}


def thread_full_row(states):
    out = {"basis": ("tau = N_IN718 (envelope history, per state) / A_n; Fsy = 0.577 Fty(T), Fsu = 0.6 Ftu(T) at FEA3D's TC-02 thread temperature; "
                     "A_n = jfwd_v352 strip area (M5-6H / 6g: Ds_min 4.826, En_max 4.605, P 0.8) x L_eff"),
           "A_n_bases": {}, "rows": {}, "fixes": {}}
    th0 = CELLS["SOAK"]["TC-02"]["thread_shear_An"]
    An_fea = R.HISTS["SOAK"]["js5"]["N_head_N"] / th0["tau_MPa"]
    bases = {"FEA3D_cell_A_n_mm2 (L_eff 6.35 = v3.5.1 L_e 6.85 - 0.5; THE ROW)": round(An_fea, 2),
             "check_strip_area_at_6.35_mm2": round(strip_area(TH, 6.35), 2)}
    e_dwg = eng_case(10.0, 0.0)
    e_iso = eng_case(10.0, ISO_L_TOL)
    bases["v3.5.2 drawing engagement, nominal screw length (BASIS CHECK for FEA3D)"] = e_dwg
    bases["v3.5.2 drawing engagement, ISO 4759-1 length tolerance -0.29 (AS RECALLED)"] = e_iso
    out["A_n_bases"] = bases
    out["engagement_geometry"] = {"r_flat_CAD_mm": R_FLAT_CAD, "r_flat_range_spot_d10.5+/-0.2_mm": [round(x, 4) for x in R_FLAT_RANGE],
                                  "r_plug_CAD_mm": R_PLUG_CAD, "r_plug_drawing_f7_mm": [round(x, 4) for x in R_PLUG_DWG], "full_thread_mm": FULL_THREAD,
                                  "mouth_not_credited_mm": MOUTH, "tip_clearance_min_mm": TIP_CLEAR_MIN,
                                  "src": f"jfwd_seat_v352_v1.json {sha(SEAT1)} tc02_engagement (L_e CAD 7.287, drawing 7.257-7.272); CAD config jfwd_tap_drill_mm 9.0"}
    for st in states:
        th = CELLS[st]["TC-02"]["thread_shear_An"]
        T2 = th["T_C"]
        fsy, fsu = 0.577 * tab("AL6061-T6", "Fty", T2), 0.6 * tab("AL6061-T6", "Ftu", T2)
        henv = max(HS, key=lambda h: n_in(st, h))
        rr = {}
        for FV in (FV0, FVMAX):
            N = n_in(st, henv, FV)
            row = {"N_N": round(N, 1), "from": LBL[henv], "T_C": T2, "Fsy_MPa": round(fsy, 1), "Fsu_MPa": round(fsu, 1)}
            for nm, An in (("FEA3D_A_n", An_fea), ("drawing_nominal_L", e_dwg["A_n_mm2"]), ("drawing_ISO_L_tol", e_iso["A_n_mm2"])):
                row[nm] = {"A_n_mm2": round(An, 2), "tau_MPa": round(N / An, 1), "MS_y": ms(fsy, N / An), "MS_u": ms(fsu, N / An)}
            rr[f"{FV:.0f}"] = row
        out["rows"][st] = rr
    gov = min(states, key=lambda st: out["rows"][st]["4096"]["FEA3D_A_n"]["MS_y"])
    out["governing_state"] = gov
    th = CELLS[gov]["TC-02"]["thread_shear_An"]
    fsy = 0.577 * tab("AL6061-T6", "Fty", th["T_C"])
    henv = max(HS, key=lambda h: n_in(gov, h))
    slope = D_FVMAX / (FVMAX - FV0)
    N3750 = n_in(gov, henv, FV0)
    fv_for = lambda target: FV0 + (fsy * An_fea / (1.0 + target) - N3750) / slope
    # (a) lower J-F1 acceptance maximum
    out["fixes"]["a_lower_J-F1_max"] = {"F_max_for_MS_y_0_N": round(fv_for(0.0)), "F_max_for_MS_y_0.05_N": round(fv_for(0.05)),
                                        "note": ("on FEA3D's A_n; the J-F1 band at 3.0 N m is 2250-4096 N: a maximum near 4000 N cuts the low-K tail of the "
                                                 "lot (J-F1 acceptance statistics decide the reject rate); +0.05 would need a maximum below the 3750 N nominal "
                                                 "(not practical)"),
                                        "slack_effect": "none: the 24-case minimum is set by the 2250 N installation (relax v5: seat -205 / ring +89 N at 2250 N, hi end)",
                                        "other_effects": "none on CAD or FD-04; J-F1 acceptance rule only"}
    # (b) custom IN718 length within the 8.0 full thread (the IN718 screw is a custom part: TO-SELECT / TO-QUOTE; its length is a drawing number)
    opts = {}
    for L_nom, tol in ((10.0, 0.1), (10.2, 0.1), (10.4, 0.08), (10.5, 0.08)):
        e = eng_case(L_nom, tol)
        rws = {}
        for FV in (FV0, FVMAX):
            N = n_in(gov, henv, FV)
            rws[f"{FV:.0f}"] = {"tau_MPa": round(N / e["A_n_mm2"], 1), "MS_y": ms(fsy, N / e["A_n_mm2"])}
        e["rows_at_governing_state"] = rws
        opts[f"M5 x {L_nom} +/-{tol}"] = e
    out["fixes"]["b_custom_IN718_length"] = {"options": opts,
                                             "slack_effect": ("none: the free length (grip + 0.5 mouth) is unchanged; in the VDI-form resilience of jfwd_embed the "
                                                              "engaged thread is 0.5 d / A_d3 and the tapped part 0.33 d, independent of L_e, so k_b and the 24-case "
                                                              "do not move"),
                                             "other_effects": ("no CAD change (tap 4.2 x 9.0 / full thread 8.0 kept), no head-height or FD-04 change; J-F1 calibrates "
                                                               "K at the flight length; drawing length tolerance +/-0.08..0.1 instead of ISO js15"),
                                             "note": ("credits the v3.5.2 spot-face engagement (head on the flat at r 31.31) that FEA3D's A_n (v3.5.1 6.85) does not; "
                                                      "FEA3D to confirm the A_n basis")}
    # (c) insert: tap-wall effect (catalogue tap drill; the STI major diameter is TO-SOURCE)
    out["fixes"]["c_helical_insert"] = {"part": "Boellhoff HELICOIL plus M5 x 0.8, 1d / 1.5d (order no. 4189 005 0005 / 4189 005 0075)",
                                        "source": ("RS 471-017 (mfr part 41890050005): 'Drill Size 5.2mm', 'Thread Length 5mm' (https://uk.rs-online.com/web/p/"
                                                   "thread-repair-inserts/0471017, accessed 2026-10-20); HELICOIL plus datasheet 0180/10.02 "
                                                   "(https://docs.rs-online.com/5ddb/0900766b810150a0.pdf, accessed 2026-10-20) lists M 5 x 5 / 7.5 / 10; its "
                                                   "STI tap table (pp. 36/37) is not in that file: the STI major diameter is TO-SOURCE"),
                                        "tap_wall_effect": ("torch-passage tap wall 1.906 mm at az 18 / 342 (measured from the M5 major 5.0): the tap drill grows "
                                                            "4.2 -> 5.2 (-0.50 mm on the drilled wall) and the tapped major grows from 5.0 to the STI major (each 0.1 "
                                                            "mm of diameter thins the 1.906 wall by 0.05 mm; at an STI major near 6.0 the wall is about 1.41 mm, the "
                                                            "M6-fallback value): probe + FE re-run needed"),
                                        "slack_effect": "a coil insert adds thread compliance (k_b down, slightly favourable); not quantified without data",
                                        "other_effects": "CAD + TC-02 drawing change, insert installation / tang removal on flight hardware, new J-F1 pair (IN718 / insert)"}
    out["fixes"]["d_disc_spring_interaction"] = ("a disc spring under the head that is solid (flat) at the soak force leaves the soak force and this row "
                                                 "unchanged; only a spring still active at the soak would lower it (jfwd_spring_v352)")
    return out


HC2 = Path("/home/claude/work/shared-fallback/engine/03-cad/calcs/hand_calcs_v2.json")


def membrane_h9(d_ro=-0.037, d_ri_seal=0.023):
    """re-evaluate hand_calcs_v2 case rows (Lame at the bore + forward closure end load, von Mises) with the OD radius changed by d_ro;
    the published applied value is reproduced first (assert)"""
    hc = json.loads(HC2.read_text())
    inp = hc["inputs"]
    OD, t = inp["case_OD"]["v"] * 1e3, inp["case_t"]["v"] * 1e3
    bore_seal = inp["case_bore_seal"]["v"] * 1e3
    ri0 = (OD - 2 * t) / 2
    secs = {"full wall 63.50/57.15": (OD / 2, ri0), "fwd seal land 57.25 bore": (OD / 2, bore_seal / 2),
            "collar groove 62.50 (pivot plane)": (OD / 2 - 0.5, ri0)}          # collar_groove_depth 0.0005 m (hand_calcs.py put(), DERIVED: OD groove)

    def vm(P, ro, ri):
        k = (ro ** 2 + ri ** 2) / (ro ** 2 - ri ** 2)
        sh, sr = P * k, -P
        sa = P * math.pi / 4 * bore_seal ** 2 / (math.pi * (ro ** 2 - ri ** 2))
        return math.sqrt(((sh - sa) ** 2 + (sa - sr) ** 2 + (sr - sh) ** 2) / 2), sh, sa

    out = {"source": {"path": str(HC2), "sha256_16": sha(HC2)}, "basis_answer": ("NOMINAL: hand_calcs_v2 uses case_OD 63.5 and the nominal bore "
           f"(full wall {OD / 2 - ri0:.3f}, fwd seal land {OD / 2 - bore_seal / 2:.3f}, collar groove {secs['collar groove 62.50 (pivot plane)'][0] - ri0:.3f} mm), "
           "not the minimum wall"), "d_ro_mm": d_ro, "d_ri_fwd_seal_land_mm": d_ri_seal, "rows": []}
    for r in hc["sections"]["case"]["rows"]:
        nm = next((n for n in secs if n in r["check"]), None)
        if nm is None:
            continue
        P = float(r["check"].split("[")[1].split()[1]) / 10.0          # bar -> MPa
        ro, ri = secs[nm]
        v0 = vm(P, ro, ri)[0]
        assert abs(v0 - r["applied"]) < 0.05, (r["check"], v0, r["applied"])
        sfy, sfu = r.get("SF_y"), r.get("SF_u")
        ay = (1 + r["MS_y"]) * sfy * r["applied"]
        au = (1 + r["MS_u"]) * sfu * r["applied"] if r.get("MS_u") is not None and sfu else None
        cases = {"h9": (ro + d_ro, ri)}
        if "fwd seal land" in nm:
            cases["h9_and_H8_max_bore"] = (ro + d_ro, ri + d_ri_seal)
        rec = {"row": r["check"], "applied_nominal_MPa": round(r["applied"], 2), "MS_y_nominal": round(r["MS_y"], 3),
               "MS_u_nominal": round(r["MS_u"], 3) if au else None, "SF": [sfy, sfu]}
        for cn, (ro2, ri2) in cases.items():
            v1 = vm(P, ro2, ri2)[0]
            rec[cn] = {"wall_mm": round(ro2 - ri2, 3), "applied_MPa": round(v1, 2), "MS_y": round(ay / (sfy * v1) - 1, 3),
                       "MS_u": round(au / (sfu * v1) - 1, 3) if au else None}
        out["rows"].append(rec)
    def key(x):
        return min(v for v in (x["MS_y_nominal"], x["MS_u_nominal"]) if v is not None)
    out["closest_row_on_the_63.5_OD"] = min(out["rows"], key=key)["row"]
    out["note"] = ("the aft seal land (61.0) and the aft thread root (M63 x 1.5) rows are on separate diameters, not the 63.5 OD; the collar "
                   "groove is evaluated as cut to a depth from the OD (if it is dimensioned as a diameter, h9 does not move it)")
    return out

if __name__ == "__main__":
    res = {"id": "jfwd_in718_rows_v352", "version": "v4", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
           "inputs": {"relax_v6_module": {"path": str(J / "jfwd_relax_v352.py"), "sha256_16": sha(J / "jfwd_relax_v352.py")},
                      "js5_cells": {"path": str(R.F_CELLS), "sha256_16": sha(R.F_CELLS)},
                      "fea3d_soak_envelope": {"path": str(R.F_ENV), "sha256_16": sha(R.F_ENV)},
                      "patch_compare": {LBL[h]: {"path": str(R.PATCHES[h] / "compare.json"), "sha256_16": sha(R.PATCHES[h] / "compare.json")} for h in R.PATCHES},
                      "fix_v2_json": {"path": str(FIX2), "sha256_16": sha(FIX2)}, "seat_v1_json": {"path": str(SEAT1), "sha256_16": sha(SEAT1)}},
           "histories": [LBL[h] for h in HS], "k_b_bracket_N_mm": {k: round(v) for k, v in R.KB.items()},
           "IN718_over_A4-80_soak_gain_ratio": {k: round(v, 4) for k, v in RATIO.items()}, "F_sh_ratio_IN718_over_A4-80": {k: round(v, 4) for k, v in FSH_RATIO.items()},
           "FA1S_thermal_delta_IN718_N": round(D_FA1S, 1), "dF_S_per_dF_V_soak": round(D_FVMAX / (FVMAX - FV0), 4)}
    st_rows = {st: rows_state(st) for st in R.STATES}
    res["states"] = st_rows
    # FA1S screw cell: 5020A Eq. 22 (preload omitted governing, included at the max preload reported), from jfwd_fix_v352_v2
    sc = fix2["options"]["IN718 M5 x10"]["screw_FA1S_5020A"]
    res["FA1S_screw_5020A_eq22"] = {"governing_omitted": sc["governing"], "included": sc["included_at_governing_row"], "gauge_omitted": sc["gauge_governing"],
                                    "arm_+0.4_sens": {k: sc["rows"]["CALC_abs_3888.1|arm_+0.4_sens"][k] for k in ("MS_omitted_governing", "MS_included_info")},
                                    "direct_shear_minor_CALC": sc["direct_shear_minor_231ii"]["CALC_abs_3888.1"], "src": "jfwd_fix_v352_v2.json (published)"}
    # FA1S tap bearing at CALC V (screw-independent): FEA3D's tap_bearing_derived re-based from its V to V 3888.1 / gauge 3862.0
    tb = CELLS["FA1S"]["TC-02"]["tap_bearing_derived"]
    vfe = CELLS["FA1S"]["SCREW"]["V_bear_exact_N"]
    dl = vfe / tb["sigma_MPa"]
    fby, fbu = (1 + tb["MS_y"]) * tb["sigma_MPa"], (1 + tb["MS_u"]) * tb["sigma_MPa"]
    res["FA1S_tap_bearing"] = {V_: {"V_N": V, "sigma_MPa": round(V / dl, 1), "MS_y": ms(fby, V / dl), "MS_u": ms(fbu, V / dl)} for V_, V in (("CALC_3888.1", 3888.1), ("gauge_3862.0", 3862.0))}
    res["FA1S_tap_bearing"]["note"] = (f"FEA3D tap_bearing_derived sigma {tb['sigma_MPa']} at V {vfe} (d x L_e {dl:.2f} mm2, L_e {tb['L_e_mm']}), allowables back-computed "
                                       f"({fby:.1f} / {fbu:.1f} MPa); V-driven, the same for every screw grade")
    res["TC02_thread_shear_full_row"] = thread_full_row(("PRELOAD", "SOAK70", "SOAK", "SOAK52", "FA1S"))
    # v4 (a): the worst-stack flat geometry behind the flat-bearing rows
    res["TC01_flat_bearing_rev5_worst_stack"] = FLAT
    # v4 (b): TC-01 case membrane rows (hand_calcs_v2.json) on the h9 OD (radial -0.037) and, at the fwd seal land, the H8 maximum bore
    res["TC01_membrane_rows_OD_h9"] = membrane_h9()
    # flags (the ligament station is information and is listed separately)
    fl, fl_info = [], []
    for st, so in st_rows.items():
        for tag, r in so["rows"].items():
            for k, v in r.items():
                for mk in ("MS_y", "MS_u", "MS_vs_Fbry", "MS_strain", "MS_PQ_2Fty", "bound_MS", "MS_y_fibre", "MS_shakedown", "MS_PQ_2Fty_info"):
                    if isinstance(v, dict) and mk in v and v[mk] is not None and v[mk] < FLAG:
                        (fl_info if mk.endswith("_info") else fl).append({"state": st, "preload_N": tag, "row": k, "metric": mk, "MS": v[mk], "flag": flag(v[mk])})
    res["flags_within_0.05_or_negative"] = fl
    res["information_rows_negative_or_within_0.05"] = fl_info
    s = json.dumps(res, indent=1, default=float)
    OUT.write_text(s)
    print(OUT.name, hashlib.sha256(s.encode()).hexdigest()[:16])
    print("histories", res["histories"], "KB", res["k_b_bracket_N_mm"], "ratios", res["IN718_over_A4-80_soak_gain_ratio"], "Fsh", res["F_sh_ratio_IN718_over_A4-80"],
          "FA1S dN", res["FA1S_thermal_delta_IN718_N"], "dFS/dFV", res["dF_S_per_dF_V_soak"])
    for st, so in st_rows.items():
        print("==", st, "N env from", so["N_envelope_from"], {h: (v["N_IN718_3750_N"], v["N_IN718_4096_N"]) for h, v in so["histories"].items()})
        for tag, r in so["rows"].items():
            line = [f"[{tag}]"]
            for k, v in r.items():
                if k == "screw_tension_234_1b":
                    line.append(f"screw {v['sigma_As_MPa']}MPa y{v['MS_y']:+.3f} u{v['MS_u']:+.3f}")
                elif k == "TC02_thread_shear_An":
                    line.append(f"thread tau {v['tau_MPa']} y{v['MS_y']:+.3f} u{v['MS_u']:+.3f}")
                elif k == "TC01_flat_bearing":
                    line.append(f"flat {v['MS_vs_Fbry']:+.3f}")
                elif k == "TC01_under_head_band_neuber":
                    line.append(f"UH {v['MS_strain']:+.3f}({v['from']})")
                elif k == "TC01_ligament_station_PQ_FEA3D_cell_INFO":
                    line.append(f"lig(info) {v['MS_PQ_2Fty_info']:+.3f}/env {v['envelope_scaled_bound_info']['MS']:+.3f}")
                elif k.endswith("_PQ"):
                    line.append(f"{k[:4]} {v['MS_PQ_2Fty']:+.3f}({v['from']})/bnd {v['bound_MS']:+.3f}")
                elif k == "TC01_lines_Pm_gt_Fty":
                    e = v["envelope"]
                    line.append(f"Pm>Fty seat {e['seat']['A4-80']}->{e['seat']['IN718_Fsh']}/{e['seat']['IN718_headforce_bound']} hole {e['hole_edge']['A4-80']}->{e['hole_edge']['IN718_Fsh']}/{e['hole_edge']['IN718_headforce_bound']}")
                elif k == "screw_fibre_soak":
                    line.append(f"fibre y{v['MS_y_fibre']:+.3f} shk{v['MS_shakedown']:+.3f} rng {v['range_max_MPa']} set {v['max_equiv_axial_set_um']}um")
            print("  " + " | ".join(line))
    print(json.dumps(res["FA1S_tap_bearing"]))
    print(json.dumps(res["FA1S_screw_5020A_eq22"]))
    t = res["TC02_thread_shear_full_row"]
    print("A_n bases", json.dumps(t["A_n_bases"]))
    for st, rr in t["rows"].items():
        print("  thread", st, {k: (v["N_N"], v["FEA3D_A_n"]["MS_y"], v["FEA3D_A_n"]["MS_u"], v["drawing_nominal_L"]["MS_y"], v["drawing_ISO_L_tol"]["MS_y"]) for k, v in rr.items()})
    print("  governing", t["governing_state"], json.dumps(t["fixes"]["a_lower_J-F1_max"])[:200])
    for k, v in t["fixes"]["b_custom_IN718_length"]["options"].items():
        print("  ", k, v["L_e_min_mm"], v["A_n_mm2"], v["tip_clearance_to_full_thread_end_min_mm"], v["tip_ok"], v["rows_at_governing_state"])
    print("flags:")
    for f in fl:
        print("  ", f)
    print("information rows:")
    for f in fl_info:
        print("  ", f)
