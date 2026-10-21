"""Item 5b tables (fea3d 2026-10-20 ~15:10Z): the re-posts of repost_5b_v352.py on the gap-conductance variant, per bound, and the
bound that is conservative for each part (brief item 5b; CHANGELOG 234 (7) = REV-MECH-2 RM2-13 corrections 5 and 6).

Reads (read-only):
  results/v352/repost_5b_lc1v352g.json   GVLO (S-AX L1_thv352_NF2b_GVLO_r10free_cad352 mapped; 'thread' TB1 tie)
  results/v352/repost_5b_lc1v352h.json   GVHI (same, GVHI field); shown '[pending lc1v352h]' while it does not exist
  results/v352/repost_5b_lc1v352.json    the v3.5.1 merged map L1_thv351_TB1GC_cad351 on the v3.5.2 model: information only (the
                                         perfect-contact side; no LC1 was solved on the v3.5.2 NF2b merged field)
  hub 04-fea/v352/gapvar_fields_v352_v2.json (Mechanical): the S-AX thermal part maxima and their instants (envelope_parts)
Writes results/v352/tables/repost_5b_v352.{json,md}:
  A. per region x bound x case: all-node and regular minimum over the four burn states B1_21.65 / B1_19 / B1_2 / B1_1 (MS y / u on the
     total stress at SF 1.5 / 2.0, node, class, state, T, vM, thermal share vM_TH / vM), with the primary-only MS (mechanical stress
     only) and the nodal P+Q (2 Fty(T) / vM - 1) at that node, and their minima over the region;
  B. the four states one by one for the TC-03 corner point n46040, TC-03 whole, the TC-02 seat, the TC-02 forward face (which holds
     the S-AX TC-02 maximum point) and NZ-01 at the v3.5.1 n72033 location;
  C. the bound that is conservative for each region (the lower all-node MS_y, then MS_u), with the merged-map value beside it;
  D. part T max per state (TC-02 / TC-03) per bound, against the S-AX thermal maxima and their instants;
  E. the instant of the S-AX TC-02 maximum (21.5 s; not an S-AX L1 state, bracketed by B1_19 and B1_21.65): the rows of
     results/v352/tc02_t215_v352.json (tc02_t215_v352.py): T at each TC-02 governing node from Mechanical's 21.501 s thermal frame, and
     the constant-stress MS with the node's vM held at the larger bracketing state [DERIVED; not a solved state];
  F. the plug-to-bore dT per state and bound, with the closure dT (37.0 / 59.3 / 115.6 K), whether the variant's own cold gap closes,
     and the closure ruling (lead 10:36Z);
  G. the merged-map surrogate check (results/v352/merged_surrogate_check_v352.json): the v3.5.1 merged map against the v3.5.2 merged
     NF2b field on TC-02 / TC-03 / NZ-01 at the four states;
  H. the TC-02 T-F1 requirement at the variant temperature (RM2-13 correction 6; line 212 (1)): at each TC-02 governing location, the
     ratio of the sourced short-time strength to the room-temperature minimum (Ftu,RT,min 260 / Fty,RT,min 240 MPa, ASTM B221/B241, as
     engmat) that a positive combined margin needs, k_u = 2.0 vM / 260 and k_y = 1.5 vM / 240, at the location's own variant temperature,
     beside the engmat 10,000 h ratio there [DERIVED; T-F1 itself (sourced data) is Mechanical's (b) package and is NOT OBTAINED].
Evidence: SIM (3-D linear elastic FE re-posts, mapped S-AX fields) + DERIVED (this tabulation and the E rows).
usage: FEA3D_CAD=v352 python -I -B repost_5b_tables_v352.py"""
from __future__ import annotations
import sys, json, hashlib, time
from pathlib import Path
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
RES = Path("/home/claude/work/fea3d/results/v352")
OUT = RES / "tables"
IDX = Path("/home/claude/work/shared-fallback/engine/04-fea/v352/gapvar_fields_v352_v2.json")
BOUNDS = [("GVLO", "lc1v352g", "v352_NF2b_GVLO"), ("GVHI", "lc1v352h", "v352_NF2b_GVHI"),
          ("merged v3.5.1 map (info)", "lc1v352", None)]
STATES = ["B1_21.65", "B1_19", "B1_2", "B1_1"]
CASES = ["LC1", "LC2"]
KEY_REGIONS = ["TC-03 corner point (r 9.8 z 105.513)", "TC-03 whole", "TC-02 seat (r <= 12, z 105-118)",
               "TC-02 forward face (z 103.513, 12 < r < 28.6)", "NZ-01 at v3.5.1 n72033"]
TC02_GOV_REGIONS = ["TC-02 seat (r <= 12, z 105-118)", "TC-02 forward face (z 103.513, 12 < r < 28.6)", "TC-02 whole"]


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def f3(x):
    return "-" if x is None else f"{x:+.3f}"


def load():
    data = {}
    for name, run, _ in BOUNDS:
        p = RES / f"repost_5b_{run}.json"
        data[name] = (json.loads(p.read_text()), sha16(p), str(p)) if p.exists() else None
    return data


def region_min(d, rg, cs, which):
    """minimum over the four states of the region's 'all' or 'regular' row (by MS_y, then MS_u); returns (state, row, region)."""
    best = None
    for st in STATES:
        S = d["states"].get(st) or {}
        if S.get("missing"):
            continue
        R = S["cases"][cs]["regions"].get(rg)
        if not R or not R.get(which):
            continue
        row = R[which]
        k = (row["MS_y"], row["MS_u"] if row["MS_u"] is not None else 9e9)
        if best is None or k < best[0]:
            best = (k, st, row, R)
    return None if best is None else best[1:]


def summarise(row, st, R):
    o = {"state": st, "node": row["node"], "r_theta_z": row["r_theta_z"], "T_C": row["T_C"], "MS_y": row["MS_y"], "MS_u": row["MS_u"],
         "vm_MPa": row["vm_MPa"], "vm_thermal_only_MPa": row.get("vm_thermal_only_MPa"), "thermal_share_vm": row.get("thermal_share_vm"),
         "node_class": row["node_class"], "class_detail": row.get("class_detail"), "d_class_mm": row.get("d_class_mm"),
         "Fty_MPa": row.get("Fty_MPa"), "Ftu_MPa": row.get("Ftu_MPa"), "material": R["material"], "brittle": R["brittle"]}
    for k in ("MS_primary_y_at_node", "MS_primary_u_at_node", "MS_PQ_2Fty_at_node", "MS_primary_y_set_min", "MS_primary_u_set_min",
              "MS_PQ_2Fty_set_min"):
        o[k] = row.get(k)
    return o


def main():
    import post_f1 as PF
    data = load()
    I = json.loads(IDX.read_text())
    have = [b for b, _, _ in BOUNDS if data[b] is not None]
    pending = [b for b, _, _ in BOUNDS if data[b] is None]
    ref = data["GVLO"][0]
    regions = list(ref["states"]["B1_1"]["cases"]["LC1"]["regions"].keys())
    out = {"id": "repost_5b_tables_v352", "date": time.strftime("%Y-%m-%d"), "owner": "fea3d",
           "doc": __doc__.split("usage:")[0].strip(), "evidence": "SIM (3-D FE re-posts) + DERIVED (tabulation, constant-stress rows)",
           "inputs": {b: ({"path": data[b][2], "sha16": data[b][1], "sax": data[b][0].get("sax"), "tb1": data[b][0].get("tb1")}
                          if data[b] else "pending") for b, _, _ in BOUNDS},
           "gapvar_index": {"path": str(IDX), "sha16": sha16(IDX)}, "pending": pending,
           "A": {}, "B": {}, "C": {}, "D": {}, "E": {}, "F": {}, "G": {}, "H": {}}
    # ---------------- A
    for rg in regions:
        out["A"][rg] = {}
        for b in have:
            d = data[b][0]
            out["A"][rg][b] = {}
            for cs in CASES:
                e = {}
                for which in ("all", "regular"):
                    m = region_min(d, rg, cs, which)
                    e[which] = summarise(m[1], m[0], m[2]) if m else None
                # primary-only and P+Q minima of the region over ALL four states (they need not occur at the total-stress governing state)
                pm = [(S["cases"][cs]["regions"][rg]["all"], st) for st in STATES for S in [d["states"].get(st) or {}]
                      if not S.get("missing") and S["cases"][cs]["regions"].get(rg, {}).get("all")
                      and S["cases"][cs]["regions"][rg]["all"].get("MS_primary_y_set_min") is not None]
                if pm:
                    a, st = min(pm, key=lambda t: t[0]["MS_primary_y_set_min"])
                    q, sq = min(pm, key=lambda t: t[0]["MS_PQ_2Fty_set_min"])
                    e["primary_min_over_states"] = {"MS_y": a["MS_primary_y_set_min"], "MS_u": a["MS_primary_u_set_min"],
                                                    "node": a["MS_primary_y_set_min_node"], "state": st}
                    e["PQ_min_over_states"] = {"MS": q["MS_PQ_2Fty_set_min"], "state": sq}
                out["A"][rg][b][cs] = e
    # ---------------- B
    for rg in KEY_REGIONS:
        out["B"][rg] = {}
        for b in have:
            d = data[b][0]
            out["B"][rg][b] = {}
            for st in STATES:
                S = d["states"].get(st) or {}
                if S.get("missing"):
                    continue
                out["B"][rg][b][st] = {}
                for cs in CASES:
                    R = S["cases"][cs]["regions"][rg]
                    out["B"][rg][b][st][cs] = {w: (summarise(R[w], st, R) if R.get(w) else None) for w in ("all", "regular")}
                    out["B"][rg][b][st][cs]["T_max_C"] = R["T_max_C"]
    # ---------------- C
    for rg in regions:
        c = {}
        for cs in CASES:
            cand = [(b, out["A"][rg][b][cs]["all"]) for b in ("GVLO", "GVHI") if b in have and out["A"][rg][b][cs]["all"]]
            if not cand:
                continue
            gb, gr = min(cand, key=lambda t: (t[1]["MS_y"], t[1]["MS_u"] if t[1]["MS_u"] is not None else 9e9))
            mg = out["A"][rg].get("merged v3.5.1 map (info)", {}).get(cs, {}).get("all") if "merged v3.5.1 map (info)" in have else None
            c[cs] = {"conservative_bound": gb + ("" if "GVHI" in have else " (GVHI pending lc1v352h)"), "row": gr,
                     "other_bound": {b: out["A"][rg][b][cs]["all"] for b in ("GVLO", "GVHI") if b in have and b != gb},
                     "merged_info": mg}
        out["C"][rg] = c
    # ---------------- D
    env = {}
    for b, run, key in BOUNDS:
        if key and key in I["fields"]:
            ep = I["fields"][key].get("envelope_parts") or {}
            env[b] = {p: ep.get(p) for p in ("ENG-TC-02", "ENG-TC-03")}
    env["merged NF2b (Mechanical, perfect contact)"] = {p: (I["fields"]["v352_NF2b"].get("envelope_parts") or {}).get(p)
                                                        for p in ("ENG-TC-02", "ENG-TC-03")}
    out["D"]["sax_thermal_envelope"] = env
    out["D"]["mapped_T_max_per_state"] = {}
    for b in have:
        d = data[b][0]
        out["D"]["mapped_T_max_per_state"][b] = {
            st: {"TC-02": d["states"][st]["cases"]["LC1"]["regions"]["TC-02 whole"]["T_max_C"],
                 "TC-02_at": d["states"][st]["cases"]["LC1"]["regions"]["TC-02 whole"]["T_max_r_z_mm"],
                 "TC-03": d["states"][st]["cases"]["LC1"]["regions"]["TC-03 whole"]["T_max_C"],
                 "TC-03_at": d["states"][st]["cases"]["LC1"]["regions"]["TC-03 whole"]["T_max_r_z_mm"]}
            for st in STATES if not (d["states"].get(st) or {}).get("missing")}
    # ---------------- E
    t215 = RES / "tc02_t215_v352.json"
    if t215.exists():
        T5 = json.loads(t215.read_text())
        out["E"] = {"source": {"path": str(t215), "sha16": sha16(t215)}, "bounds": T5["bounds"]}
    # ---------------- G
    msc = RES / "merged_surrogate_check_v352.json"
    if msc.exists():
        out["G"] = {"source": {"path": str(msc), "sha16": sha16(msc)}, "states": json.loads(msc.read_text())["states"]}
    # ---------------- H
    FTU_RT, FTY_RT = 260.0, 240.0
    for b in [x for x in ("GVLO", "GVHI") if x in have]:
        d = data[b][0]
        rows = []
        for rg in ("TC-02 seat (r <= 12, z 105-118)", "TC-02 forward face (z 103.513, 12 < r < 28.6)"):
            for which in ("all", "regular"):
                cand = [(r["MS_u"], st, cs, r) for st in STATES for cs in CASES
                        for r in [d["states"][st]["cases"][cs]["regions"][rg][which]] if r]
                mu, st, cs, r = min(cand, key=lambda t: t[0])
                Fty, Ftu = (float(v) for v in PF.allowables("AL6061-T6", np.array(r["T_C"] + 273.15)))
                rows.append({"region": rg, "node_set": which, "node": r["node"], "node_class": r["node_class"], "state": st, "case": cs,
                             "T_C": r["T_C"], "vm_MPa": r["vm_MPa"], "MS_y": r["MS_y"], "MS_u": r["MS_u"],
                             "k_u_required": round(2.0 * r["vm_MPa"] / FTU_RT, 3), "k_y_required": round(1.5 * r["vm_MPa"] / FTY_RT, 3),
                             "engmat_10000h_ratio_u": round(Ftu / FTU_RT, 3), "engmat_10000h_ratio_y": round(Fty / FTY_RT, 3)})
        t5 = (out.get("E") or {}).get("bounds", {}).get(b, {})
        for k, n in (t5.get("nodes") or {}).items():
            a = n.get("at_21.5s")
            if a and "forward face" in k and "regular" in k:
                Fty, Ftu = (float(v) for v in PF.allowables("AL6061-T6", np.array(a["T_C"] + 273.15)))
                rows.append({"region": "TC-02 forward face at 21.5 s (S-AX TC-02 maximum instant; constant stress)", "node_set": "regular",
                             "node": int(k.split()[0][1:]), "node_class": n["node_class"], "state": "21.5 s", "case": a["vm_from"],
                             "T_C": a["T_C"], "vm_MPa": a["vm_held_MPa"], "MS_y": a["MS_y"], "MS_u": a["MS_u"],
                             "k_u_required": round(2.0 * a["vm_held_MPa"] / FTU_RT, 3), "k_y_required": round(1.5 * a["vm_held_MPa"] / FTY_RT, 3),
                             "engmat_10000h_ratio_u": round(Ftu / FTU_RT, 3), "engmat_10000h_ratio_y": round(Fty / FTY_RT, 3)})
        out["H"][b] = {"Ftu_RT_min_MPa": FTU_RT, "Fty_RT_min_MPa": FTY_RT, "rows": rows,
                       "v351_reference": "v3.5.1 seat node (merged field, 159.2 C): k_u >= 0.788 (REV-MECH-2 RM2-13 (e)); line 212: Ftu(149 C) >= 0.765 and Ftu(181 C) >= 0.661 of Ftu,RT,min"}
    # ---------------- F
    for b in have:
        d = data[b][0]
        out["F"][b] = {st: {"dT_max_K": d["states"][st]["fit_dT"]["dT_plug_minus_bore_K"]["max"],
                            "z_at_max_mm": d["states"][st]["fit_dT"]["at_max"]["z_mm"],
                            "land_A_dT_max_K": d["states"][st]["fit_dT"]["per_land"]["A"]["dT_max_K"],
                            "variant_gap_left_mm_at_max": d["states"][st]["fit_dT"].get("variant_gap_left_mm_at_max"),
                            "closure_dT_K": d["states"][st]["fit_dT"]["closure_dT_K"],
                            "needs_fit_contact": d["states"][st]["fit_dT"]["needs_fit_contact (dT >= 37-59 K)"],
                            "closes_variant_cold_gap": d["states"][st]["fit_dT"].get("closes_variant_cold_gap_by_max")}
                       for st in STATES if not (d["states"].get(st) or {}).get("missing")}
        out["F"]["closure_ruling"] = ref["states"]["B1_1"]["fit_dT"].get("closure_ruling")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "repost_5b_v352.json").write_text(json.dumps(out, indent=1))
    (OUT / "repost_5b_v352.md").write_text(render(out, have, pending))
    print("wrote", OUT / "repost_5b_v352.json", sha16(OUT / "repost_5b_v352.json"), OUT / "repost_5b_v352.md", sha16(OUT / "repost_5b_v352.md"))


def cell(r):
    if not r:
        return "-"
    s = f"{f3(r['MS_y'])} / {f3(r['MS_u'])}"
    return s


def render(o, have, pending):
    L = ["# Item 5b re-posts on the gap-conductance variant (v3.5.2)", "",
         f"Generated by `scripts/repost_5b_tables_v352.py` ({o['date']}). Evidence: {o['evidence']}. Inputs: " +
         "; ".join(f"{b}: " + (f"`{Path(v['path']).name}` {v['sha16']} (S-AX {v['sax']}, TB1 '{v['tb1']}')" if isinstance(v, dict) else
                               "[pending lc1v352h]") for b, v in o["inputs"].items()) +
         f"; gap-variant index `gapvar_fields_v352_v2.json` {o['gapvar_index']['sha16']}.", "",
         "MS at SF 1.5 yield / 2.0 ultimate on the total stress at node temperature; primary-only = mechanical stress only; P+Q = 2 Fty(T) / vM - 1 "
         "at the node. Four states B1_21.65 / B1_19 / B1_2 / B1_1; LC1 and LC2, 4 lateral sub-cases each, node-wise envelope. NZ-01 is graphite "
         "(brittle criterion, yield column only). Merged column = the v3.5.1 merged map on the v3.5.2 model (information).", ""]
    if pending:
        L += [f"**Pending:** {', '.join(pending)} (GVHI = lc1v352h, chain E first run).", ""]
    # A
    L += ["## A. Region minima over the four states (all-node | regular)", "",
          "| Region | Bound | Case | All-node MS y / u | node, class, state, T C | vM MPa (thermal share) | primary-only y / u at node | P+Q at node | Regular MS y / u | node, state, T C | primary-only min y / u over the region and the four states (node, state) | P+Q min over the region and the four states (state) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for rg, B in o["A"].items():
        for b, C in B.items():
            for cs, e in C.items():
                a, g = e["all"], e["regular"]
                if not a:
                    continue
                L.append(f"| {rg} | {b} | {cs} | {cell(a)} | n{a['node']} {a['node_class']}{(' ' + a['class_detail']) if a.get('class_detail') else ''}, "
                         f"{a['state']}, {a['T_C']} | {a['vm_MPa']} ({a['thermal_share_vm']}) | {f3(a.get('MS_primary_y_at_node'))} / {f3(a.get('MS_primary_u_at_node'))} | "
                         f"{f3(a.get('MS_PQ_2Fty_at_node'))} | {cell(g)} | " + (f"n{g['node']}, {g['state']}, {g['T_C']}" if g else "-") +
                         (f" | {f3(e['primary_min_over_states']['MS_y'])} / {f3(e['primary_min_over_states']['MS_u'])} (n{e['primary_min_over_states']['node']}, "
                          f"{e['primary_min_over_states']['state']}) | {f3(e['PQ_min_over_states']['MS'])} ({e['PQ_min_over_states']['state']}) |"
                          if e.get("primary_min_over_states") else " | - | - |"))
    # B
    L += ["", "## B. The four states one by one (all-node | regular; LC1 and LC2)", "",
          "| Region | Bound | State | region T max C | LC1 all-node (node, T C, share) | LC1 regular | LC2 all-node (node, T C, share) | LC2 regular | primary-only y (LC1 / LC2, at node) | P+Q (LC1 / LC2, at node) |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for rg, B in o["B"].items():
        for b, S in B.items():
            for st, C in S.items():
                a1, g1, a2, g2 = C["LC1"]["all"], C["LC1"]["regular"], C["LC2"]["all"], C["LC2"]["regular"]

                def nt(a):
                    return f"{cell(a)} (n{a['node']}, {a['T_C']}, {a['thermal_share_vm']})" if a else "-"
                L.append(f"| {rg} | {b} | {st} | {C['LC1']['T_max_C']} | {nt(a1)} | {cell(g1)} | {nt(a2)} | {cell(g2)} | "
                         f"{f3(a1.get('MS_primary_y_at_node') if a1 else None)} / {f3(a2.get('MS_primary_y_at_node') if a2 else None)} | "
                         f"{f3(a1.get('MS_PQ_2Fty_at_node') if a1 else None)} / {f3(a2.get('MS_PQ_2Fty_at_node') if a2 else None)} |")
    # C
    L += ["", "## C. Bound conservative for each region (all-node, minimum over states)", "",
          "| Region | Case | Conservative bound | MS y / u (node, state) | other bound | merged v3.5.1 map (info) |", "|---|---|---|---|---|---|"]
    for rg, C in o["C"].items():
        for cs, e in C.items():
            r = e["row"]
            ob = "; ".join(f"{b} {cell(x)} (n{x['node']}, {x['state']})" for b, x in e["other_bound"].items()) or "[pending lc1v352h]"
            mg = e["merged_info"]
            L.append(f"| {rg} | {cs} | {e['conservative_bound']} | {cell(r)} (n{r['node']}, {r['state']}) | {ob} | "
                     + (f"{cell(mg)} (n{mg['node']}, {mg['state']})" if mg else "-") + " |")
    # D
    L += ["", "## D. Part temperature maxima", "", "S-AX thermal maxima (Mechanical, gapvar_fields_v352_v2 envelope_parts; thermal frame z = S-AX z + 6.544 mm):", "",
          "| Field | TC-02 T max C (t s, r z thermal frame) | TC-03 T max C (t s) |", "|---|---|---|"]
    for b, e in o["D"]["sax_thermal_envelope"].items():
        t2, t3 = e.get("ENG-TC-02") or {}, e.get("ENG-TC-03") or {}
        L.append(f"| {b} | {t2.get('T_max_C')} ({t2.get('t_max_s')} s, {t2.get('at_r_z_mm')}) | {t3.get('T_max_C')} ({t3.get('t_max_s')} s) |")
    L += ["", "Mapped 3-D part maxima at the four S-AX L1 states (they equal the S-AX L1 state maxima):", "",
          "| Bound | State | TC-02 T max C (r, z) | TC-03 T max C (r, z) |", "|---|---|---|---|"]
    for b, S in o["D"]["mapped_T_max_per_state"].items():
        for st, e in S.items():
            L.append(f"| {b} | {st} | {e['TC-02']} ({e['TC-02_at'][0]}, {e['TC-02_at'][1]}) | {e['TC-03']} ({e['TC-03_at'][0]}, {e['TC-03_at'][1]}) |")
    # E
    L += ["", "## E. TC-02 at the instant of the S-AX TC-02 maximum (21.5 s)", ""]
    E = o.get("E") or {}
    if E:
        L += [f"Source `tc02_t215_v352.json` {E['source']['sha16']}: T from Mechanical's 21.501 s thermal frame at the 3-D governing node "
              "(the 19.001 / 21.651 s frames reproduce the S-AX L1 states B1_19 / B1_21.65 exactly); MS at 21.5 s with the node's vM held at "
              "the larger of B1_19 / B1_21.65 x LC1 / LC2 and 6061-T6 allowables at T(21.5 s) [DERIVED; the 3-D model has no 21.5 s state].", "",
              "| Bound | Node (region; set) | class | T C at 19.0 / 21.5 / 21.65 s (thermal frames) | T C 3-D mapped B1_19 / B1_21.65 | posted MS y / u B1_19 LC1 / LC2 | vM held MPa (from) | MS y / u at 21.5 s |",
              "|---|---|---|---|---|---|---|---|"]
        for b, e in E["bounds"].items():
            L.append(f"| {b} | TC-02 part maximum | - | {e['TC02_part_max_C']['19.001']['T_C']} / {e['TC02_part_max_C']['21.501']['T_C']} / "
                     f"{e['TC02_part_max_C']['21.651']['T_C']} (r {e['TC02_part_max_C']['21.501']['r_z_thermal_mm'][0]}) | - | - | - | - |")
            own = "pending" not in e.get("governing_nodes_from", "")
            for k, n in e["nodes"].items():
                ti, tm, po = n["T_thermal_interp_C"], n["T_3D_mapped_C"], n["posted"]
                a = n.get("at_21.5s")
                L.append(f"| {b} | {k}{'' if own else ' (GVLO governing node; T only)'} | {n['node_class']} | {ti['19.001']} / {ti['21.501']} / {ti['21.651']} | "
                         + (f"{tm.get('B1_19 LC1')} / {tm.get('B1_21.65 LC1')} | "
                            f"{f3(po.get('B1_19 LC1', {}).get('MS_y'))} / {f3(po.get('B1_19 LC1', {}).get('MS_u'))} ; "
                            f"{f3(po.get('B1_19 LC2', {}).get('MS_y'))} / {f3(po.get('B1_19 LC2', {}).get('MS_u'))} | " if own else "[pending lc1v352h] | [pending lc1v352h] | ")
                         + (f"{a['vm_held_MPa']} ({a['vm_from']}) | {f3(a['MS_y'])} / {f3(a['MS_u'])} |" if a else "[pending lc1v352h] | - |"))
        L.append("")
    # F
    L += ["## F. Plug-to-bore dT at the TC-01 / TC-02 f7 / H8 fit (3-D mapped, TC-02 plug OD minus TC-01 bore)", "",
          "| Bound | State | dT max K (z mm) | land A dT max K | closure dT K (0.025 / 0.040 / 0.078) | above the RM2-13 37-59 K trigger | closes at the variant's own cold gap | variant gap left at max mm |",
          "|---|---|---|---|---|---|---|---|"]
    for b, S in o["F"].items():
        if b == "closure_ruling":
            continue
        for st, e in S.items():
            cz = e["closure_dT_K"]
            L.append(f"| {b} | {st} | {e['dT_max_K']} ({e['z_at_max_mm']}) | {e['land_A_dT_max_K']} | "
                     f"{cz.get('0.025 CAD')} / {cz.get('0.040 drawing min')} / {cz.get('0.078 drawing max')} | {'yes' if e['needs_fit_contact'] else 'no'} | "
                     f"{'-' if e['closes_variant_cold_gap'] is None else ('yes' if e['closes_variant_cold_gap'] else 'no')} | {e['variant_gap_left_mm_at_max']} |")
    L += ["", f"Closure ruling: {o['F'].get('closure_ruling')}", ""]
    G = o.get("G") or {}
    if G:
        L += ["## G. Merged-map surrogate check (v3.5.1 merged map used by lc1v352 against the v3.5.2 merged NF2b field)", "",
              f"Source `merged_surrogate_check_v352.json` {G['source']['sha16']}: T(NF2b merged) - T(v3.5.1 merged) at every S-AX v3.5.2 node of the part.", "",
              "| State | TC-03 max abs dT K (p95; at r, z) | TC-02 max abs dT K (p95; at r, z) | NZ-01 max abs dT K (p95) | TC-03 corner T new / old C | TC-02 seat r 6.5 T new / old C |",
              "|---|---|---|---|---|---|"]
        for st, e in G["states"].items():
            P = e["parts"]
            c = e["points"]["TC-03 corner (9.8, 105.513)"]
            q = e["points"]["TC-02 seat (6.5, 107.513)"]
            L.append(f"| {st} | {P['ENG-TC-03']['dT_max_abs_K']} ({P['ENG-TC-03']['dT_p95_abs_K']}; {P['ENG-TC-03']['at_r_z_mm']}) | "
                     f"{P['ENG-TC-02']['dT_max_abs_K']} ({P['ENG-TC-02']['dT_p95_abs_K']}; {P['ENG-TC-02']['at_r_z_mm']}) | "
                     f"{P['ENG-NZ-01']['dT_max_abs_K']} ({P['ENG-NZ-01']['dT_p95_abs_K']}) | {c['T_new_C']} / {c['T_old_C']} | {q['T_new_C']} / {q['T_old_C']} |")
        L.append("")
    H = o.get("H") or {}
    if H:
        L += ["## H. TC-02 T-F1 requirement at the variant temperature (DERIVED; T-F1 data NOT OBTAINED)", "",
              "k = the ratio of the sourced short-time strength at T to the room-temperature minimum (Ftu 260 / Fty 240 MPa) that MS >= 0 needs "
              "at the location's stress: k_u = 2.0 vM / 260, k_y = 1.5 vM / 240. engmat ratio = the 10,000 h LITERATURE ratio used in the posts.", "",
              "| Bound | Location (node set) | node, class | state, case | T C | vM MPa | posted MS y / u | k_y required | k_u required | engmat 10,000 h ratio y / u |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for b, e in H.items():
            for r in e["rows"]:
                L.append(f"| {b} | {r['region']} ({r['node_set']}) | n{r['node']} {r['node_class']} | {r['state']}, {r['case']} | {r['T_C']} | {r['vm_MPa']} | "
                         f"{f3(r['MS_y'])} / {f3(r['MS_u'])} | {r['k_y_required']} | {r['k_u_required']} | {r['engmat_10000h_ratio_y']} / {r['engmat_10000h_ratio_u']} |")
            L += ["", f"Reference: {e['v351_reference']}.", ""]
    return "\n".join(L)


if __name__ == "__main__":
    main()
