"""COSTING of one mu 0 convergence check of the governing seat line d+6.051 z'0 finer than s6 (FEA3D-2, 2026-10-21; lead 01:30:18Z (5b)).
No solve.  Candidate meshes were BUILT (gmsh, no deck) with a scratch copy of jfwd_sub.py (runs/cost_convcheck_v352/jfwd_sub_cost.py: TC-01
read from 03-cad/v3.5.2/history/ENG-TC-01.step.1ad07e472709b1b2 because parts/ now holds the FINAL d11.2 TC-01 fcb3b5b93bebdb01; optional
local Ball fields) and their L12 / xcut 26 patch counted with the jfwd_seat.py box rule (runs/cost_convcheck_v352/patch_count.py).
The scratch rebuild of s6 gives 104,678 patch nodes from the mesh vs 107,611 in the production model (interface duplicates): candidate
patch nodes are scaled by that ratio [DERIVED].  Peak RSS: power law through the two measured mu 0 patch runs (b2) s6 and (b2') s9
[ESTIMATE, +/-10 % assumed].  Runtime: s/increment ~ N^1.5 through the same two runs, 7 increments (the 6-step (b2') form) to 9 (as (b2))
[ESTIMATE].  Folder peak: the v6 frd model n (125 + 248 k_out) B, k_out 5, gz 0.22 x frd, deck 141.6 B/node (as (b2')), + 2 MB
(runs/disk_peak_jfwd.json; it over-predicted (b2') by 17 %).  Gate: 1.86 GiB + 1.25 x peak + 0.10 GiB on the whole peak (as js5b).
usage: jfwd_convcheck_costing_v352.py -> results/v352/jfwd_convcheck_costing_v352.json + results/v352/tables/jfwd_convcheck_costing_v352.md"""
import hashlib, json, math
from pathlib import Path

W = Path("/home/claude/work/fea3d")
EV = W / "runs" / "cost_convcheck_v352"
OUTJ = W / "results" / "v352" / "jfwd_convcheck_costing_v352.json"
OUTM = W / "results" / "v352" / "tables" / "jfwd_convcheck_costing_v352.md"
GIB = 1024 ** 3
CAP_GIB, COMB_GIB = 8.0, 9.0
CAND = {   # tag: (family, description, local h at the line ends, h ratio to s6 there)
    "cA5": ("(i) global step", "h_brk 0.064 / transition 0.6 (whole break zone)", 0.064, 1.25),
    "cA3": ("(i) global step", "h_brk 0.060 / transition 0.6", 0.060, 1.333),
    "cA2": ("(i) global step", "h_brk 0.056 / transition 0.6", 0.056, 1.429),
    "cD": ("(i-b) local on s6", "s6 + Ball h 0.04, r 0.3 + 0.3 at both ends of the governing line (bore R0.2 end, flat chamfer end)", 0.04, 2.0),
    "cD3": ("(i-b) local on s6", "s6 + Ball h 0.05, r 0.3 + 0.3 at both ends", 0.05, 1.6),
    "cD2": ("(i-b) local on s6", "s6 + Ball h 0.04, r 0.4 + 0.4 at both ends", 0.04, 2.0),
    "cB": ("(i-b) local on s6", "s6 + Ball h 0.04, r 0.45 + 0.5 at the bore end only", 0.04, 2.0),
    "cB2": ("(i-b) local on s6", "s6 + Ball h 0.04, r 0.3 + 0.3 at the bore end only", 0.04, 2.0),
}


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main():
    counts = {}
    for ln in (EV / "patch_counts.jsonl").read_text().splitlines():
        if ln.strip():
            d = json.loads(ln)
            counts[d["tag"]] = d
    runs = {}
    for j, sel in (("seat_s6L12_mu0", "seat_s6L12"), ("seat_s9L12_mu0", "seat_s9L12")):
        cr = json.loads((W / "jfwd" / "runs" / j / "ccx_run.json").read_text())
        n = json.loads((W / "jfwd" / f"{sel}.json").read_text())["n_nodes"]
        sta = (W / "jfwd" / "runs" / j / f"{j}.sta").read_text().splitlines()[2:]
        ninc = sum(1 for s in sta if len(s.split()) >= 7)
        runs[j] = {"n_nodes": n, "peak_rss_GiB": cr["peak_rss_GB"], "seconds": cr["seconds"], "increments": ninc,
                   "s_per_inc": round(cr["seconds"] / ninc, 1)}
    a, b = runs["seat_s6L12_mu0"], runs["seat_s9L12_mu0"]
    e_rss = math.log(a["peak_rss_GiB"] / b["peak_rss_GiB"]) / math.log(a["n_nodes"] / b["n_nodes"])
    e_inc = math.log(a["s_per_inc"] / b["s_per_inc"]) / math.log(a["n_nodes"] / b["n_nodes"])
    cal = a["n_nodes"] / counts["cs6"]["patch_nodes"]
    dpk = json.loads((W / "runs" / "disk_peak_jfwd.json").read_text())["jobs"]["seat_s9L12_mu0"]
    deck_b_per_node = dpk["deck_MB"] * 1e6 / b["n_nodes"]
    gz = dpk["frd_gz_MB"] / dpk["frd_MB"]
    out = {"id": "jfwd_convcheck_costing_v352", "doc": __doc__.split("usage:")[0].strip(), "ruling": "lead 2026-10-21T01:30:18Z (5b): costing only, no start without the lead's go",
           "evidence": {"folder": "runs/cost_convcheck_v352", "patch_counts_sha16": sha16(EV / "patch_counts.jsonl"), "jfwd_sub_cost_sha16": sha16(EV / "jfwd_sub_cost.py"),
                        "interim_TC01_step": "03-cad/v3.5.2/history/ENG-TC-01.step.1ad07e472709b1b2 (read-only)", "disk_peak_jfwd_sha16": sha16(W / "runs" / "disk_peak_jfwd.json")},
           "measured": runs, "model": {"rss_exponent": round(e_rss, 3), "s_per_inc_exponent": round(e_inc, 3), "patch_node_calibration": round(cal, 4),
                                        "deck_B_per_node": round(deck_b_per_node, 1), "frd_gz_ratio": round(gz, 4), "k_out": 5, "increments": [7, 9],
                                        "tags": "patch nodes DERIVED (built meshes); RSS / runtime / disk ESTIMATE"},
           "scratch_rebuild_check": {"cs6_patch_nodes": counts["cs6"]["patch_nodes"], "cs6_mesh_nodes": counts["cs6"]["mesh_nodes"], "s6_recorded_mesh_nodes": 159178,
                                     "cs9_patch_nodes": counts["cs9"]["patch_nodes"], "s9_production_patch_nodes": b["n_nodes"]},
           "candidates": {}}
    for tag, (fam, desc, hl, hr) in CAND.items():
        c = counts[tag]
        n = round(c["patch_nodes"] * cal)
        x = n / a["n_nodes"]
        rss = a["peak_rss_GiB"] * x ** e_rss
        spi = a["s_per_inc"] * x ** e_inc
        frd = n * (125 + 248 * 5) / 1e6
        deck = n * deck_b_per_node / 1e6
        peak = deck + frd + gz * frd + 2.0
        gate = 1.86 + 1.25 * peak * 1e6 / GIB + 0.10
        fits_cap = rss * 1.10 <= CAP_GIB
        out["candidates"][tag] = {"family": fam, "mesh": desc, "h_line_ends_mm": hl, "h_ratio_to_s6_there": hr, "scratch_patch_nodes": c["patch_nodes"],
                                  "patch_nodes_est": n, "peak_rss_GiB_est": round(rss, 2), "rss_plus_10pct_GiB": round(rss * 1.10, 2),
                                  "fits_8GiB_cap_with_10pct": fits_cap, "room_for_other_ccx_GiB": round(COMB_GIB - rss, 2),
                                  "runtime_h_est": [round(spi * 7 / 3600, 2), round(spi * 9 / 3600, 2)], "folder_peak_MB_est": round(peak, 1),
                                  "gate_GiB": round(gate, 3)}
    OUTJ.write_text(json.dumps(out, indent=1))
    md = ["# J-FWD governing-line convergence check finer than s6: COSTING (lead 01:30:18Z (5b)); no solve", "",
          f"Measured (b2) s6: {a['n_nodes']:,} nodes, {a['peak_rss_GiB']} GiB, {a['seconds']:.0f} s / {a['increments']} inc; (b2') s9: {b['n_nodes']:,}, "
          f"{b['peak_rss_GiB']} GiB, {b['seconds']:.0f} s / {b['increments']} inc [SIM].  RSS ~ N^{e_rss:.2f}, s/inc ~ N^{e_inc:.2f} [ESTIMATE].  "
          f"Patch nodes from built meshes x {cal:.3f} (scratch s6 rebuild {counts['cs6']['patch_nodes']:,} vs 107,611) [DERIVED].", "",
          "| tag | family | mesh | patch nodes | peak RSS GiB (+10 %) | fits 8.0 cap with 10 % | runtime h (7-9 inc) | folder peak MB | gate GiB |",
          "|---|---|---|---|---|---|---|---|---|"]
    for tag, r in out["candidates"].items():
        md.append(f"| {tag} | {r['family']} | {r['mesh']} | {r['patch_nodes_est']:,} | {r['peak_rss_GiB_est']} ({r['rss_plus_10pct_GiB']}) | "
                  f"{'yes' if r['fits_8GiB_cap_with_10pct'] else 'no'} | {r['runtime_h_est'][0]}-{r['runtime_h_est'][1]} | {r['folder_peak_MB_est']} | {r['gate_GiB']} |")
    OUTM.write_text("\n".join(md) + "\n")
    print(json.dumps({k: (v["patch_nodes_est"], v["peak_rss_GiB_est"], v["runtime_h_est"], v["folder_peak_MB_est"], v["gate_GiB"]) for k, v in out["candidates"].items()}))
    print(sha16(OUTJ), sha16(OUTM))


if __name__ == "__main__":
    main()
