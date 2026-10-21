"""J-FWD: the final-envelope seat-line inputs in Mechanical's v7 quantities (lead 2026-10-21T01:01:13Z, correction to ruling (4)).

Mechanical's jfwd_relax_v352_v7.json (345e27062d54ad20; block PQ_select_fit_band_on_envelope_IN718 [DERIVED]) sizes the seat-line P+Q
select-fit band on its v7 history envelope (instances js5 + patches a / a2 / a3 / b2 / b2r; no (b1)).  Mechanical re-runs that grid on
the final envelope in its re-map.  This script gives Mechanical the inputs of that re-run.  It is read-only on Mechanical's file and on
FEA3D's posted run files, and makes no new run.  Per state (PRELOAD, SOAK70, SOAK, SOAK52, FA1S; the _rep instances kept as separate
rows, lead 00:39:30Z (5)) it reports the values in v7's own definitions (Mechanical jfwd_relax_v352.py 82221fdf0035f338, hist_row() /
envelope()), with the instance each value comes from:
  N_head_N        seatforce.json steps[step].screw.HEAD_on_screw_along_n_N (max over the instances; the min beside it)
  seat_window_N   seatforce.json steps[step].seat_TC02.footprint.window_daz9_zp9_N (min over the instances)
  seat line       compare.json steps[step].z0_gradient, family 'seat', delta +6.051 deg, z' 0: PmPb (the patch column; js5 = the global
                  column of patch (a)'s file) and MS_PQ = 2 Fty(T) / PmPb - 1 (max PmPb / min MS over the instances)
  M_max_Nmm       max of 'M' over compare.json steps[step][side].screw_sections plus M_max_threaded / M_max_shank_in_TC01 (s5 patches: their
                  runcmp_js5 'A' column; js5: patch (a)'s runcmp 'B' column; (b2), (b1), (b2'): shank.json, whose repeats exist only there,
                  checked against runcmp 'A' where both exist)
  and, as v7, N_section_max_N, UH_band_MS_strain_min (min of the n15 / n30 Neuber strain MS) and spread_N_rel.
Step 1 rebuilds v7's history_envelope and fea3d_envelope_crosscheck from the v7 instance set and asserts the match (this checks the
extraction, not the physics).  Step 2 adds (b1) seat_s9L12_mu02A with its repeats, and (b2') seat_s9L12_mu0 once its run is DONE and posted.
Step 3 lists every v7 input that moves, with the instance that moves it and the change.  Views per state: 'primary' (no repeats),
'rep' (the SOAK_rep / SOAK52_rep instances only) and 'v7 convention' (primary + rep, as v7's history_envelope merges (b2) rep).
C1 view (lead 2026-10-21T01:30:18Z (5), C1 ADOPTED): the same views with (b1)'s seat line (d+6.051 z'0) at its C1 value, PmPb x max(1, r),
r = s6 / s9 at mu 0 on that line and state ((b2) / (b2')), the repeats at their state's ratio [ASSUMED]; read from
results/v352/jfwd_b1_meshcorr_v352.json and checked against the as-solved value here; resultants as solved.  [DERIVED]
[SIM values from the posts; DERIVED envelopes; this is not a physical approval]
Separate file (FEA3D-2, 2026-10-21 02:3xZ): scripts/jfwd_v7inputs_v352.py 653e00189c5c52fc and its outputs (json 753431eb50f36f58, md
fdc96347e9a87025) are cited in the lead's line notes, so they stay as they are; this copy adds the C1 view and writes its own files.
usage: jfwd_v7inputs_c1_v352.py -> results/v352/jfwd_v7inputs_c1_v352.json, results/v352/tables/jfwd_v7inputs_c1_v352.md   (FEA3D-2, 2026-10-21)"""
from __future__ import annotations
import json, hashlib
from pathlib import Path

RUNS = Path("/home/claude/work/fea3d/jfwd/runs")
V7 = Path("/home/claude/work/mechanical/v352/jfwd/jfwd_relax_v352_v7.json")
V7_SHA16 = "345e27062d54ad20"
V7_SCRIPT = Path("/home/claude/work/mechanical/v352/jfwd/jfwd_relax_v352.py")
OUT = Path("/home/claude/work/fea3d/results/v352/jfwd_v7inputs_c1_v352.json")
OUT_MD = Path("/home/claude/work/fea3d/results/v352/tables/jfwd_v7inputs_c1_v352.md")
MESHCORR = Path("/home/claude/work/fea3d/results/v352/jfwd_b1_meshcorr_v352.json")    # C1 (lead 01:30:18Z (5)); DERIVED

RUN = {"js5": "js5_mu0_T3750_g078", "patch_a": "seat_s5L8_mu0", "patch_a2": "seat_s5L8_mu0_go", "patch_a3": "seat_s5L12_mu0_go",
       "patch_b2": "seat_s6L12_mu0", "patch_b1": "seat_s9L12_mu02A", "patch_b2p": "seat_s9L12_mu0"}
LABEL = {"js5": "js5", "patch_a": "(a)", "patch_a2": "(a')", "patch_a3": "(a'')", "patch_b2": "(b2)", "patch_b2r": "(b2) rep",
         "patch_b1": "(b1)", "patch_b1r": "(b1) rep", "patch_b2p": "(b2')"}
FORM = {"js5": "s5 global, sharp, mu 0", "patch_a": "s5 L8, sharp, mu 0", "patch_a2": "s5 L8 js5 order, sharp, mu 0",
        "patch_a3": "s5 L12 js5 order, sharp, mu 0", "patch_b2": "s6 L12, R0.2, mu 0", "patch_b2r": "s6 L12, R0.2, mu 0 (repeat)",
        "patch_b1": "s9 L12, R0.2, mu 0.2", "patch_b1r": "s9 L12, R0.2, mu 0.2 (repeat)", "patch_b2p": "s9 L12, R0.2, mu 0"}
REP = {"patch_b2r": ("patch_b2", {"SOAK": "SOAK_rep", "SOAK52": "SOAK52_rep"}),
       "patch_b1r": ("patch_b1", {"SOAK": "SOAK_rep", "SOAK52": "SOAK52_rep"})}
SHANK_MOMENTS = {"patch_b2", "patch_b1", "patch_b2p"}       # v7 treatment of (b2) (repeats only in shank.json); same for the s9 patches
V7_SET = ("js5", "patch_a", "patch_a2", "patch_a3", "patch_b2", "patch_b2r")
NEW = ("patch_b1", "patch_b1r", "patch_b2p")
STATES = ("PRELOAD", "SOAK70", "SOAK", "SOAK52", "FA1S")
NUM_KEYS = ("N_head_N", "N_head_min_N", "seat_window_N", "seat_line_PmPb_MPa", "seat_line_MS_PQ", "M_max_Nmm", "N_section_max_N",
            "UH_band_MS_strain_min", "spread_N_rel")
FROM_KEYS = {"N_head_N": "N_head_from", "N_head_min_N": "N_head_min_from", "seat_window_N": "seat_window_from",
             "seat_line_MS_PQ": "seat_line_from", "M_max_Nmm": "M_from", "UH_band_MS_strain_min": "UH_from"}
TOL = {"N_head_N": 0.05, "N_head_min_N": 0.05, "seat_window_N": 0.05, "seat_line_PmPb_MPa": 0.05, "seat_line_MS_PQ": 0.0005,
       "M_max_Nmm": 0.05, "N_section_max_N": 0.05, "UH_band_MS_strain_min": 0.0005, "spread_N_rel": 0.00005}

_C: dict = {}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def J(hp, name):
    k = (hp, name)
    if k not in _C:
        _C[k] = json.loads((RUNS / RUN[hp] / name).read_text())
    return _C[k]


def posted(hp):
    d = RUNS / RUN[hp]
    need = ["DONE", "seatforce.json", "compare.json"] + (["shank.json"] if hp in SHANK_MOMENTS else ["runcmp_js5_mu0_T3750_g078.json"])
    return all((d / n).exists() for n in need)


def src_of(h, st):
    if h in REP:
        base, steps = REP[h]
        return (base, steps[st]) if st in steps else None
    return ("patch_a" if h == "js5" else h, st)


def hist_row(h, st):
    """v7 hist_row(): the instance h at state st, in v7's definitions (only the fields the envelope uses, plus the sources)."""
    s_ = src_of(h, st)
    if s_ is None:
        return None
    hp, step = s_
    sf = json.loads((RUNS / RUN["js5"] / "seatforce.json").read_text()) if h == "js5" else J(hp, "seatforce.json")
    if step not in sf["steps"] or step not in J(hp, "compare.json")["steps"]:
        return None
    side, key = ("global_same_sets", "B") if h == "js5" else ("patch", "A")
    s = sf["steps"][step]
    fp = s["seat_TC02"]["footprint"]
    cm = J(hp, "compare.json")["steps"][step]
    c = cm[side]
    z0 = [r for r in cm["z0_gradient"] if r["family"] == "seat" and abs(r["delta_deg"] - 6.051) < 0.01 and abs(r["z_prime_mm"]) < 0.01]
    assert len(z0) == 1, (h, st, len(z0))
    z0 = z0[0]
    if hp in SHANK_MOMENTS:
        sh = J(hp, "shank.json")["steps"][step]
        mm = [sh["M_max_threaded"], sh["M_max_shank_in_TC01"]]
        rcj = RUNS / RUN[hp] / "runcmp_js5_mu0_T3750_g078.json"
        if rcj.exists() and step in J(hp, "runcmp_js5_mu0_T3750_g078.json")["steps"]:
            rc = J(hp, "runcmp_js5_mu0_T3750_g078.json")["steps"][step]
            for k_ in ("M_max_threaded", "M_max_shank_in_TC01"):
                assert abs(rc[k_]["A"]["M"] - sh[k_]["M"]) < 0.05, (h, st, k_, rc[k_]["A"]["M"], sh[k_]["M"])
        msrc = f"{RUN[hp]}/shank.json"
    else:
        rc = J(hp, "runcmp_js5_mu0_T3750_g078.json")["steps"][st]
        mm = [rc["M_max_threaded"][key], rc["M_max_shank_in_TC01"][key]]
        msrc = f"{RUN[hp]}/runcmp_js5_mu0_T3750_g078.json '{key}'"
    secs = list(c["screw_sections"].values()) + mm
    xs = [float(k[1:]) if k.startswith("x") else None for k in c["screw_sections"]] + [x.get("x") for x in mm]   # section key 'x28.7' -> x' 28.7
    uh = c["under_head_band"]
    m_arg = {"x": xs[max(range(len(secs)), key=lambda i: secs[i]["M"])]}
    return {"instance": LABEL[h], "form": FORM[h], "run": RUN["js5"] if h == "js5" else RUN[hp], "step": step,
            "N_head_N": s["screw"]["HEAD_on_screw_along_n_N"], "N_plane_N": s["screw"]["N_plane_N_tension_pos"],
            "seat_window_N": fp.get("window_daz9_zp9_N"),
            "seat_line_PmPb_MPa": z0["PmPb_global" if h == "js5" else "PmPb_patch"],
            "seat_line_MS_PQ": z0["MS_PQ_global" if h == "js5" else "MS_PQ_patch"], "seat_line_T_C": z0["T_mean_C"],
            "M_max_Nmm": max(x["M"] for x in secs), "M_max_abs_Nmm": max(abs(x["M"]) for x in secs), "M_max_at_x_mm": m_arg.get("x"),
            "N_section_max_N": max(x["N"] for x in secs),
            "UH_band_MS_strain_min": min(uh["neuber_MS_strain_n15"], uh["neuber_MS_strain_n30"]),
            "src": {"seatforce": f"{RUN['js5'] if h == 'js5' else RUN[hp]}/seatforce.json", "compare": f"{RUN[hp]}/compare.json "
                    f"[{side}; z0 {'PmPb_global' if h == 'js5' else 'PmPb_patch'}]", "moments": msrc}}


def envelope(rows):
    """v7 envelope() over the instances in rows ({key: row}); the 'from' fields keep v7's instance keys."""
    HH = tuple(rows)
    if not HH:
        return None
    hi = lambda k: max(HH, key=lambda h: rows[h][k])        # noqa: E731
    lo = lambda k: min(HH, key=lambda h: rows[h][k])        # noqa: E731
    Ns = [rows[h]["N_head_N"] for h in HH]
    return {"N_head_N": rows[hi("N_head_N")]["N_head_N"], "N_head_from": hi("N_head_N"),
            "N_head_min_N": rows[lo("N_head_N")]["N_head_N"], "N_head_min_from": lo("N_head_N"),
            "seat_window_N": rows[lo("seat_window_N")]["seat_window_N"], "seat_window_from": lo("seat_window_N"),
            "seat_line_PmPb_MPa": rows[hi("seat_line_PmPb_MPa")]["seat_line_PmPb_MPa"], "seat_line_PmPb_from": hi("seat_line_PmPb_MPa"),
            "seat_line_MS_PQ": rows[lo("seat_line_MS_PQ")]["seat_line_MS_PQ"], "seat_line_from": lo("seat_line_MS_PQ"),
            "M_max_Nmm": rows[hi("M_max_Nmm")]["M_max_Nmm"], "M_from": hi("M_max_Nmm"),
            "N_section_max_N": rows[hi("N_section_max_N")]["N_section_max_N"],
            "UH_band_MS_strain_min": rows[lo("UH_band_MS_strain_min")]["UH_band_MS_strain_min"], "UH_from": lo("UH_band_MS_strain_min"),
            "spread_N_rel": round((max(Ns) - min(Ns)) / min(Ns), 4), "instances": [LABEL[h] for h in HH]}


def main():
    assert sha(V7) == V7_SHA16, ("Mechanical v7 changed", sha(V7))
    v7 = json.loads(V7.read_text())
    have_new = [h for h in NEW if posted(REP[h][0] if h in REP else h)]
    rows = {st: {} for st in STATES}
    for st in STATES:
        for h in V7_SET + tuple(have_new):
            r = hist_row(h, st)
            if r is not None:
                rows[st][h] = r
    # ---- step 1: reproduce v7 (extraction check)
    repro = {}
    for st in STATES:
        e = envelope({h: rows[st][h] for h in V7_SET if h in rows[st]})
        ve = v7["history_envelope"][st]
        chk = {}
        for k in NUM_KEYS:
            chk[k] = {"v7": ve[k], "here": e[k], "ok": abs(ve[k] - e[k]) <= TOL[k]}
        for k, fk in FROM_KEYS.items():
            chk[fk] = {"v7": ve[fk], "here": e[fk], "ok": ve[fk] == e[fk]}
        repro[st] = chk
        bad = {k: v for k, v in chk.items() if not v["ok"]}
        assert not bad, (st, bad)
    xchk = {}
    for kx, vx in v7["fea3d_envelope_crosscheck"].items():
        st, lab = kx.split("|")
        h = next(k for k, v in LABEL.items() if v == lab)
        r = rows[st][h]
        ok = (abs(vx["N_head_here"] - r["N_head_N"]) <= 0.05 and abs(vx["window_here"] - r["seat_window_N"]) <= 0.05
              and abs(vx["seat_line_PmPb_here"] - r["seat_line_PmPb_MPa"]) <= 0.05)
        xchk[kx] = ok
        assert ok, (kx, vx, r["N_head_N"], r["seat_window_N"], r["seat_line_PmPb_MPa"])
    # ---- step 2: final views; step 3: moves of the v7 inputs (v7 convention = primary + rep, as v7 merges (b2) rep)
    def make_views(rws):
        vw = {}
        for st in STATES:
            allh = tuple(rws[st])
            prim = {h: rws[st][h] for h in allh if h not in REP}
            rep = {h: rws[st][h] for h in allh if h in REP}
            vw[st] = {"primary": envelope(prim), "rep": envelope(rep) if rep else None, "v7_convention": envelope(dict(rws[st]))}
        return vw

    def make_moves(vw):
        mvs = {}
        for st in STATES:
            ve, fe = v7["history_envelope"][st], vw[st]["v7_convention"]
            mv = []
            for k in NUM_KEYS:
                d = fe[k] - ve[k]
                if abs(d) > TOL[k]:
                    fk = FROM_KEYS.get(k) or ("seat_line_PmPb_from" if k == "seat_line_PmPb_MPa" else None)
                    mv.append({"quantity": k, "v7": ve[k], "v7_from": ve.get(FROM_KEYS.get(k, ""), None), "final": fe[k],
                               "final_from": fe.get(fk) if fk else None, "final_from_label": LABEL.get(fe.get(fk)) if fk else None,
                               "delta": round(d, 4), "delta_rel": round(d / abs(ve[k]), 4) if ve[k] else None})
            mvs[st] = mv
        return mvs

    views = make_views(rows)
    moves = make_moves(views)
    # ---- C1 view (lead 01:30:18Z (5)): (b1)'s seat line at its C1 value; resultants as solved
    mc = json.loads(MESHCORR.read_text())
    rows_c1 = {st: {h: dict(r) for h, r in rows[st].items()} for st in STATES}
    c1_line = {}
    for st in STATES:
        for h in ("patch_b1", "patch_b1r"):
            if h not in rows_c1[st]:
                continue
            r = rows_c1[st][h]
            g = mc["states"][st]["instances"][r["step"]]["governing_line"]
            assert abs(g["PmPb_b1_MPa"] - r["seat_line_PmPb_MPa"]) <= 0.05 and abs(g["MS_b1"] - r["seat_line_MS_PQ"]) <= 0.0005, (st, h, g)
            c1_line[f"{st}|{LABEL[h]}"] = {"as_solved_PmPb_MPa": g["PmPb_b1_MPa"], "as_solved_MS": g["MS_b1"], "ratio_floored": g["ratio_floored"],
                                           "C1_PmPb_MPa": g["C1_PmPb_MPa"], "C1_MS": g["C1_MS"]}
            r["seat_line_PmPb_MPa"], r["seat_line_MS_PQ"] = g["C1_PmPb_MPa"], g["C1_MS"]
    views_c1 = make_views(rows_c1)
    moves_c1 = make_moves(views_c1)
    out = {"doc": __doc__.split("usage:")[0].strip(), "date": "2026-10-21", "author": "FEA3D-2",
           "mechanical_v7": {"file": str(V7), "sha256_16": sha(V7), "script": str(V7_SCRIPT), "script_sha256_16": sha(V7_SCRIPT)},
           "instances_v7": [LABEL[h] for h in V7_SET], "instances_added": [LABEL[h] for h in have_new],
           "instances_pending": [LABEL[h] for h in NEW if h not in have_new],
           "inputs_sha16": {f"{RUN[h if h not in REP else REP[h][0]]}/{n}": sha(RUNS / RUN[h if h not in REP else REP[h][0]] / n)
                            for h in V7_SET + tuple(have_new) for n in ("seatforce.json", "compare.json", "shank.json",
                                                                         "runcmp_js5_mu0_T3750_g078.json")
                            if (RUNS / RUN[h if h not in REP else REP[h][0]] / n).exists()},
           "step1_reproduction_of_v7": {"history_envelope": repro, "fea3d_envelope_crosscheck": xchk,
                                        "result": "v7 history_envelope and crosscheck reproduced (extraction check, not physics)"},
           "rows": rows, "views": views, "v7_inputs_moved": moves,
           "C1_view": {"rule": mc["ruling"], "meshcorr": {"file": str(MESHCORR), "sha256_16": sha(MESHCORR)}, "b1_seat_line": c1_line,
                       "views": views_c1, "v7_inputs_moved": moves_c1,
                       "note": "only (b1)'s seat line changes (C1, DERIVED); N_head, window, M_max, N_section, UH band, spread as solved"},
           "tags": "values SIM (exact nodal-force resultants, SCL lines of the posts); envelopes and deltas DERIVED; fit 0.078 throughout"}
    OUT.write_text(json.dumps(out, indent=1))
    # ---- md
    L = ["# J-FWD final-envelope inputs in Mechanical's v7 quantities (FEA3D-2, 2026-10-21)", "",
         f"Mechanical v7 `jfwd_relax_v352_v7.json` {sha(V7)} (script {sha(V7_SCRIPT)}); FEA3D runs read-only, fit 0.078 throughout, no new run. "
         f"Instances: v7 = {', '.join(LABEL[h] for h in V7_SET)}; added = {', '.join(LABEL[h] for h in have_new) or 'none'}; "
         f"pending = {', '.join(LABEL[h] for h in NEW if h not in have_new) or 'none'}. Step 1 reproduces v7's history_envelope and "
         "crosscheck exactly (extraction check). [SIM values; DERIVED envelopes]", "",
         "## Per instance (v7 definitions)", "",
         "| state | instance | form | N_head N | seat window N | seat line d+6.051 z'0 PmPb MPa | MS_PQ | M_max N mm (x') | step |",
         "|---|---|---|---|---|---|---|---|---|"]
    for st in STATES:
        for h, r in rows[st].items():
            L.append(f"| {st} | {r['instance']} | {r['form']} | {r['N_head_N']:.1f} | {r['seat_window_N']:.1f} | {r['seat_line_PmPb_MPa']:.1f} | "
                     f"{r['seat_line_MS_PQ']:+.3f} | {r['M_max_Nmm']:.1f} ({r['M_max_at_x_mm']}) | {r['step']} |")
    L += ["", "## Envelope per state (primary = no repeats; rep = SOAK_rep / SOAK52_rep rows; v7 convention = both)", "",
          "| state | view | N_head max (from) | N_head min (from) | window min (from) | seat-line PmPb max (from) | MS_PQ min (from) | M_max (from) |",
          "|---|---|---|---|---|---|---|---|"]
    for st in STATES:
        for vn in ("primary", "rep", "v7_convention"):
            e = views[st][vn]
            if e is None:
                continue
            L.append(f"| {st} | {vn} | {e['N_head_N']:.1f} ({LABEL[e['N_head_from']]}) | {e['N_head_min_N']:.1f} ({LABEL[e['N_head_min_from']]}) | "
                     f"{e['seat_window_N']:.1f} ({LABEL[e['seat_window_from']]}) | {e['seat_line_PmPb_MPa']:.1f} ({LABEL[e['seat_line_PmPb_from']]}) | "
                     f"{e['seat_line_MS_PQ']:+.3f} ({LABEL[e['seat_line_from']]}) | {e['M_max_Nmm']:.1f} ({LABEL[e['M_from']]}) |")
    L += ["", "## v7 inputs that move (v7 convention)", ""]
    for st in STATES:
        if not moves[st]:
            L.append(f"- {st}: none")
        for m in moves[st]:
            L.append(f"- {st} {m['quantity']}: v7 {m['v7']} ({m['v7_from']}) -> {m['final']} ({m['final_from_label']}); "
                     f"delta {m['delta']:+} ({(m['delta_rel'] or 0) * 100:+.1f} %)")
    L += ["", "## C1 view (lead 01:30:18Z (5), C1 ADOPTED): (b1) seat line at x max(1, s6/s9) [DERIVED]; resultants as solved", "",
          "| state | instance | as solved PmPb MPa (MS) | ratio floored | C1 PmPb MPa (MS) |", "|---|---|---|---|---|"]
    for k, v in c1_line.items():
        st, lab = k.split("|")
        L.append(f"| {st} | {lab} | {v['as_solved_PmPb_MPa']:.1f} ({v['as_solved_MS']:+.3f}) | {v['ratio_floored']:.4f} | {v['C1_PmPb_MPa']:.1f} ({v['C1_MS']:+.3f}) |")
    L += ["", "| state | view | seat-line PmPb max (from) | MS_PQ min (from) |", "|---|---|---|---|"]
    for st in STATES:
        for vn in ("primary", "rep", "v7_convention"):
            e = views_c1[st][vn]
            if e is None:
                continue
            L.append(f"| {st} | {vn} | {e['seat_line_PmPb_MPa']:.1f} ({LABEL[e['seat_line_PmPb_from']]}) | {e['seat_line_MS_PQ']:+.3f} ({LABEL[e['seat_line_from']]}) |")
    L += ["", "C1 view, v7 inputs that move (v7 convention; the seat-line rows only differ from the as-solved list above):", ""]
    for st in STATES:
        for m in moves_c1[st]:
            if m["quantity"].startswith("seat_line"):
                L.append(f"- {st} {m['quantity']}: v7 {m['v7']} ({m['v7_from']}) -> {m['final']} ({m['final_from_label']}); "
                         f"delta {m['delta']:+} ({(m['delta_rel'] or 0) * 100:+.1f} %)")
    OUT_MD.write_text("\n".join(L) + "\n")
    print("added", have_new, "| pending", [h for h in NEW if h not in have_new])
    for st in STATES:
        print(st, "moves:", [(m["quantity"], m["v7"], m["final"], m["final_from_label"]) for m in moves[st]])
    print("wrote", OUT, sha(OUT), OUT_MD, sha(OUT_MD))


if __name__ == "__main__":
    main()
