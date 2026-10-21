"""J-FWD: Mechanical's v7-quantity inputs on the FINAL envelope v6, with cD (FEA3D-2, 2026-10-21; lead 2026-10-21T05:27Z (1)-(3)).

This file is Mechanical's re-map input record together with envelope v6 (lead 05:27Z (3)); it is not information only.  It is read-only
on the cited files and makes no new run:
  base   results/v352/jfwd_v7inputs_c1_v352.json (384c1a472add7a4c): the final-envelope inputs in v7's definitions with the C1 seat-line
         view (lead 01:30:18Z (5)), views 'primary' (no repeats), 'rep' (the repeat instances) and 'v7_convention' (all instances);
  cD     seat_sDL12_mu0 (s6 + Ball h 0.04 mm at the governing-line ends, FINAL TC-01, mu 0, no repeats), its row in v7's definitions from
         hist_row() of scripts/jfwd_v7inputs_v352.py (653e00189c5c52fc, imported read-only; the run table is extended in memory only).
Rule per input (lead 2026-10-21T05:27Z):
  (2) resultant-type inputs take cD as an instance as solved (worst-of, as in v6, lead 05:17:36Z (3)): N_head_N (max), N_head_min_N
      (min), seat_window_N (min), M_max_Nmm (max, with its x'), N_section_max_N (max), spread_N_rel = (N_head max - min) / min;
  (1) local values stay on the base, with cD's refined-mesh value beside: UH_band_MS_strain_min ('cD refined-mesh local value beside,
      strain ratio 1.023, within the (C) 5 % band; the MF note applies' in SOAK52; the strain ratio is (1 + MS_base) / (1 + MS_cD)), and
      the seat line d+6.051 z'0 (lead 02:01:34Z (C), 05:17:36Z (1): s6 + C1 stand; cD's value and its cD / s6 ratio beside).
cD joins the views 'primary' and 'v7_convention' ('rep' holds repeat instances only and is unchanged).  'moved_by_cD' lists every input
that differs from the base.  Check: the base's resultant-type inputs are recomputed from the run files with v7's envelope() and must agree
(extraction check).  [values SIM; envelopes, ratios and moves DERIVED]
usage: jfwd_v7inputs_cD_v352.py -> results/v352/jfwd_v7inputs_cD_v352.json + results/v352/tables/jfwd_v7inputs_cD_v352.md"""
import json, hashlib, importlib.util
from pathlib import Path

W = Path("/home/claude/work/fea3d")
BASE = W / "results/v352/jfwd_v7inputs_c1_v352.json"
V7I = W / "scripts/jfwd_v7inputs_v352.py"
ENV6 = W / "results/v352/jfwd_soak_envelope_v352_v6.json"
CDRES = W / "results/v352/jfwd_cD_result_v352.json"
OUT, OUT_MD = W / "results/v352/jfwd_v7inputs_cD_v352.json", W / "results/v352/tables/jfwd_v7inputs_cD_v352.md"
CD_KEY, CD_RUN, CD_LAB = "patch_cD", "seat_sDL12_mu0", "(cD)"
STATES = ("PRELOAD", "SOAK70", "SOAK", "SOAK52", "FA1S")
HI = {"N_head_N": "N_head_from", "M_max_Nmm": "M_from", "N_section_max_N": None}
LO = {"N_head_min_N": "N_head_min_from", "seat_window_N": "seat_window_from"}
ROWKEY = {"N_head_min_N": "N_head_N"}        # v7's envelope(): the head-force minimum is the minimum of the instances' N_head_N
UH_LABEL = "cD refined-mesh local value beside, strain ratio {r:.3f}, within the (C) 5 % band; the MF note applies"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main():
    spec = importlib.util.spec_from_file_location("v7i", V7I)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.RUN[CD_KEY] = CD_RUN
    m.LABEL[CD_KEY] = CD_LAB
    m.FORM[CD_KEY] = "s6 + Ball h 0.04 mm at the governing-line ends, FINAL TC-01, R0.2, mu 0"
    m.SHANK_MOMENTS.add(CD_KEY)
    assert m.posted(CD_KEY), "cD not posted"
    B = json.loads(BASE.read_text())
    cr = json.loads(CDRES.read_text())
    out = {"id": "jfwd_v7inputs_cD_v352", "doc": __doc__.split("usage:")[0].strip(), "date": "2026-10-21", "author": "fea3d (FEA3D-2)",
           "status": ("Mechanical's re-map input record together with envelope v6 (lead 2026-10-21T05:27Z (3)); v6 "
                      "results/v352/jfwd_soak_envelope_v352_v6.json"),
           "rule": {"resultants": "lead 2026-10-21T05:27Z (2): cD enters as an instance as solved (worst-of), as in v6 (05:17:36Z (3))",
                    "UH_band": "lead 2026-10-21T05:27Z (1): (C)-style; the base value stands, cD's refined-mesh local value beside",
                    "seat_line": "lead 2026-10-21T02:01:34Z (C), 05:17:36Z (1): s6 + C1 stand; cD's value beside"},
           "inputs_sha16": {"results/v352/jfwd_v7inputs_c1_v352.json": sha(BASE), "scripts/jfwd_v7inputs_v352.py": sha(V7I),
                            "results/v352/jfwd_soak_envelope_v352_v6.json": sha(ENV6), "results/v352/jfwd_cD_result_v352.json": sha(CDRES)},
           "cD_rows": {}, "views": {}, "beside": {}, "moved_by_cD": {}, "extraction_check": {}}
    for f in ("seatforce.json", "compare.json", "shank.json", "runcmp_js5_mu0_T3750_g078.json"):
        out["inputs_sha16"][f"{CD_RUN}/{f}"] = sha(m.RUNS / CD_RUN / f)
    for st in STATES:
        base_views = B["C1_view"]["views"][st]
        rows = {h: r for h in B["rows"][st] if (r := m.hist_row(h, st))}
        # extraction check: v7's envelope() over the base instances, resultant-type inputs only (C1 touches the seat line only)
        chk = {}
        for vname, hs in (("primary", [h for h in rows if not h.endswith("r")]), ("v7_convention", list(rows))):
            e = m.envelope({h: rows[h] for h in hs})
            for k in list(HI) + list(LO) + ["spread_N_rel", "UH_band_MS_strain_min"]:
                chk[f"{vname}/{k}"] = e[k] == base_views[vname][k]
        assert all(chk.values()), (st, {k: v for k, v in chk.items() if not v})
        out["extraction_check"][st] = "base resultant-type inputs and UH band reproduced by v7's envelope() (%d values)" % len(chk)
        rc = m.hist_row(CD_KEY, st)
        out["cD_rows"][st] = {k: rc[k] for k in ("N_head_N", "N_plane_N", "seat_window_N", "seat_line_PmPb_MPa", "seat_line_MS_PQ",
                                                  "M_max_Nmm", "M_max_at_x_mm", "N_section_max_N", "UH_band_MS_strain_min", "src")}
        out["views"][st] = {"rep": base_views["rep"]}
        moved = []
        for vname in ("primary", "v7_convention"):
            b = dict(base_views[vname])
            f = dict(b)
            mfrom = b.get("M_from")
            f["M_max_at_x_mm"] = rows[mfrom]["M_max_at_x_mm"] if mfrom in rows else None
            for k, fk in HI.items():
                if rc[k] > f[k]:
                    f[k] = rc[k]
                    if fk:
                        f[fk] = CD_KEY
                    if k == "M_max_Nmm":
                        f["M_max_at_x_mm"] = rc["M_max_at_x_mm"]
            for k, fk in LO.items():
                v = rc[ROWKEY.get(k, k)]
                if v < f[k]:
                    f[k], f[fk] = v, CD_KEY
            nmax = max(b["N_head_N"], rc["N_head_N"])
            nmin = min(b["N_head_min_N"], rc["N_head_N"])
            sp = round((nmax - nmin) / nmin, 4)
            if rc["N_head_N"] > b["N_head_N"] or rc["N_head_N"] < b["N_head_min_N"]:
                f["spread_N_rel"] = sp
            f["instances_resultants"] = b["instances"] + [CD_LAB]
            f["instances_local"] = b["instances"]
            f.pop("instances", None)
            out["views"][st][vname] = f
            for k in list(HI) + list(LO) + ["spread_N_rel"]:
                if f[k] != b[k]:
                    moved.append({"view": vname, "quantity": k, "base": b[k], "base_from": b.get(HI.get(k) or LO.get(k) or "", None),
                                  "final": f[k], "final_from": CD_KEY if (HI.get(k) or LO.get(k)) else None,
                                  "x_mm": f.get("M_max_at_x_mm") if k == "M_max_Nmm" else None})
        # beside: the local values (lead 05:27Z (1); 02:01:34Z (C))
        bv = base_views["v7_convention"]
        r_uh = round((1 + bv["UH_band_MS_strain_min"]) / (1 + rc["UH_band_MS_strain_min"]), 4)
        gl = cr["states"][st]["governing_line"]
        out["beside"][st] = {
            "UH_band_MS_strain_min": {"stands": bv["UH_band_MS_strain_min"], "stands_from": bv["UH_from"], "cD": rc["UH_band_MS_strain_min"],
                                      "strain_ratio_cD_over_base": r_uh,
                                      "label": (UH_LABEL.format(r=r_uh) if rc["UH_band_MS_strain_min"] < bv["UH_band_MS_strain_min"] else
                                                "cD refined-mesh local value beside (not lower than the base)")},
            "seat_line_d+6.051_z0": {"stands_PmPb_MPa": bv["seat_line_PmPb_MPa"], "stands_from": bv["seat_line_PmPb_from"],
                                     "stands_MS_PQ": bv["seat_line_MS_PQ"], "cD_PmPb_MPa": rc["seat_line_PmPb_MPa"], "cD_MS_PQ": rc["seat_line_MS_PQ"],
                                     "cD_over_s6": gl["cD_over_s6"], "verdict_C": gl["verdict"]}}
        out["moved_by_cD"][st] = moved
    OUT.write_text(json.dumps(out, indent=1))
    L = ["# J-FWD: Mechanical's v7-quantity inputs on the final envelope v6, with cD [SIM values; DERIVED]", "",
         "Mechanical's re-map input record together with `results/v352/jfwd_soak_envelope_v352_v6.json` "
         f"`{sha(ENV6)}` (lead 2026-10-21T05:27Z (3)). Base: `jfwd_v7inputs_c1_v352.json` `{sha(BASE)}` (C1 seat-line view). "
         "Resultant-type inputs take cD as an instance as solved (05:27Z (2)); the UH band and the seat line keep the base value with "
         "cD's refined-mesh value beside (05:27Z (1); 02:01:34Z (C)).", "",
         "## Final inputs, v7 convention (all instances; cD in the resultant-type inputs)", "",
         "| state | N_head max (from) | N_head min (from) | seat window min (from) | M_max N mm (from, x') | N_section max | spread N | "
         "seat line PmPb / MS (from) | UH band strain MS min (from) |", "|---|---|---|---|---|---|---|---|---|"]
    lab = lambda k: m.LABEL.get(k, k) if k else ""          # noqa: E731
    for st in STATES:
        f = out["views"][st]["v7_convention"]
        L.append(f"| {st} | {f['N_head_N']} ({lab(f['N_head_from'])}) | {f['N_head_min_N']} ({lab(f['N_head_min_from'])}) | "
                 f"{f['seat_window_N']} ({lab(f['seat_window_from'])}) | {f['M_max_Nmm']} ({lab(f['M_from'])}, {f['M_max_at_x_mm']}) | "
                 f"{f['N_section_max_N']} | {f['spread_N_rel']} | {f['seat_line_PmPb_MPa']} / {f['seat_line_MS_PQ']:+.3f} "
                 f"({lab(f['seat_line_from'])}) | {f['UH_band_MS_strain_min']} ({lab(f['UH_from'])}) |")
    L += ["", "## Inputs cD moves (against the base)", "", "| state | view | input | base (from) | final (from) |", "|---|---|---|---|---|"]
    for st in STATES:
        for r in out["moved_by_cD"][st]:
            fb = f" ({lab(r['base_from'])})" if r["base_from"] else ""
            ff = ", ".join(x for x in (lab(r["final_from"]), f"x' {r['x_mm']}" if r["x_mm"] is not None else "") if x)
            L.append(f"| {st} | {r['view']} | {r['quantity']} | {r['base']}{fb} | {r['final']}" + (f" ({ff})" if ff else "") + " |")
        if not out["moved_by_cD"][st]:
            L.append(f"| {st} | - | none | | |")
    L += ["", "## Local values: the base stands, cD beside", "",
          "| state | UH band strain MS: stands (from) / cD, strain ratio | label | seat line d+6.051 z'0 PmPb stands (from) / cD, cD / s6 |",
          "|---|---|---|---|"]
    for st in STATES:
        u, s = out["beside"][st]["UH_band_MS_strain_min"], out["beside"][st]["seat_line_d+6.051_z0"]
        L.append(f"| {st} | {u['stands']} ({lab(u['stands_from'])}) / {u['cD']}, {u['strain_ratio_cD_over_base']:.3f} | {u['label']} | "
                 f"{s['stands_PmPb_MPa']} ({lab(s['stands_from'])}) / {s['cD_PmPb_MPa']}, {s['cD_over_s6']:.3f} |")
    L += ["", f"Inputs (sha256/16): {json.dumps(out['inputs_sha16'])}", "", "Nothing here is physical approval."]
    OUT_MD.write_text("\n".join(L) + "\n")
    print("\n".join(L))
    print(OUT, sha(OUT), OUT_MD, sha(OUT_MD))


if __name__ == "__main__":
    main()
