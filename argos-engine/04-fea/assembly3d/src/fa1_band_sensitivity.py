"""FA-1 column sensitivity at TC-01 (lead CHANGELOG 223 (3)(a); fea3d 2026-10-19).  Post-processing of the modal already solved
(modal_v351ca2b_c71: all bodies at mesh level 2, 60 modes to 5130 Hz, unstressed T_REF); no new eigen run.

For the TC-01 J-FWD node (FA1S / FA1D / FA1U governing node, L1 node 8314) and the TC-01 LC1 governing node (L1 node 8843), mapped to the
nearest TC-01 node of the L2 mesh, plus every TC-01 node within 2 mm (neighbour spread):
  static unit-pressure stress s0 (OP step, this mesh) and its modal decomposition  s0 = sum_i s_i (phi_i . F_OP) / omega_i^2 + residual;
  functional = s0 projected on its dominant principal direction (as post_modal.py) and, as a check, the tensor projection
  (s_i : s0) / (s0 : s0) (closer to what von Mises sees under proportional loading);
  band shares of the static value: slow T > 1 ms, 0.1-1 ms, residual (modes above f_max: T < 1 / f_max, fast);
  frequency scalings s = 1.00 / 0.90 / 0.85 (FE frequencies x s; a uniform scaling multiplies every modal term and the static value by
  1/s^2, so only the band membership changes);  shares of the 1010 Hz mode and of every mode in 1.0-1.2 kHz.
FA-1 margin at the shares (lead 223 (2) method): Peq = slow x 151.04 + (1 - slow) x 93 bar (yield) / 102 bar (ultimate), stress
proportional to pressure (checked against the four F1 columns at this node: break-even pressure P x (1 + MS)), MS = P_be / Peq - 1,
with P_be from FA1D (yield) and FA1U (ultimate); also the affine fit through the four columns and the |share| variant (conservative
when shares have mixed signs).  Tags: shares SIM (modal decomposition), margins DERIVED.
usage: fa1_band_sensitivity.py [run=modal_v351ca2b_c71]  -> results/fa1_band_sensitivity.json, results/tables/fa1_band_sensitivity.md
"""
from __future__ import annotations
import sys, json, math
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import post_f1 as PF        # noqa: E402
import post_modal as PMd    # noqa: E402
import asm_build as AB      # noqa: E402

RES = PF.RES
SCALES = (1.00, 0.90, 0.85)
P = {"FA1Q": 90.0, "FA1D": 93.0, "FA1U": 102.0, "FA1S": 151.04}


def col_ms(fa, case, l1node):
    r = [m for m in fa[case]["margins"] if m["part"] == "TC-01" and m["set"] == "regular"][0]
    assert int(r["node"]) == l1node, (case, r["node"])
    return r["MS"], r.get("MS_ult"), r["vm_MPa"], r["xyz_mm"]


def main(argv):
    opts = dict(a.split("=", 1) for a in argv)
    run = opts.get("run", "modal_v351ca2b_c71")
    M, meta = PF.load_model(run)
    AB.pressure_sets(M)
    sd = PF.RUNS / run / "B1_21.65"
    Z = np.load(sd / "fields.npz")
    Uf = Z["U_FREQ"].astype(np.float64)
    U_op = Z["U_OP"].astype(np.float64)
    S_ccx = Z["S_OP"].astype(np.float64) if "S_OP" in Z.files else None
    md = json.loads((sd / "modal.json").read_text())
    nmode = Uf.shape[0]
    f = np.array([r["f_Hz"] for r in md["modes"]][:nmode])
    om2 = (2 * math.pi * f) ** 2
    N1 = M.next_n + 1
    Uf, U_op = Uf[:, :N1], U_op[:N1]
    F_op = PMd.nodal_force(M, "OP")
    p = np.einsum("kij,ij->k", Uf, F_op)
    fa = json.loads((RES / "f1_post_fa1_c71.json").read_text())["states"]["A1_22.2"]["cases"]
    lc1 = json.loads((RES / "f1_post_lc1v351_c71.json").read_text())["states"]
    # the two L1 points
    jy = col_ms(fa, "FA1S", 8314)[3]
    lc1row = min((m for st in lc1.values() for m in st["cases"]["LC1"]["margins"] if m["part"] == "TC-01" and m["set"] == "regular"),
                 key=lambda m: m["MS"])
    pts = {"TC-01 J-FWD (FA-1 governing, L1 node 8314)": np.asarray(jy, float),
           f"TC-01 LC1 governing (L1 node {lc1row['node']}, {lc1row['state']})": np.asarray(lc1row["xyz_mm"], float)}
    b = M.bodies["TC-01"]
    tree = cKDTree(M.Xp["TC-01"])
    out = {"run": run, "doc": __doc__.split("usage:")[0].strip(), "f_max_Hz": float(f.max()), "modes_1_to_1p2kHz": [], "points": {}}
    band = [(i + 1, float(f[i])) for i in range(nmode) if 1000.0 <= f[i] < 1200.0]
    out["modes_1_to_1p2kHz"] = band
    for lab, x in pts.items():
        d0, i0 = tree.query(x, k=1)
        near = sorted(set([int(i0)] + [int(i) for i in tree.query_ball_point(x, 2.0)]))
        rows = []
        for li in near:
            nd = b.noff + li
            pr = PMd.StressProbe(M, nd)
            s0 = pr.stress(U_op)
            sm = pr.stress(Uf)
            T0 = PMd.tens(s0)
            w, V = np.linalg.eigh(T0)
            kk = int(np.argmax(np.abs(w)))
            n = V[:, kk]
            Tk = np.stack([PMd.tens(v) for v in sm])
            fun = {"principal": (float(w[kk]), np.einsum("i,kij,j->k", n, Tk, n)),
                   "tensor": (1.0, np.einsum("kij,ij->k", Tk, T0) / np.einsum("ij,ij->", T0, T0))}
            row = {"node": int(nd), "dist_mm": float(np.linalg.norm(M.Xp["TC-01"][li] - x)), "nearest": li == int(i0),
                   "s0_principal_MPa_per_MPa": float(w[kk]), "s0_vm_probe": float(PF.vm(s0[None])[0]),
                   "s0_vm_ccx": (float(PF.vm(S_ccx[nd][None])[0]) if S_ccx is not None else None)}
            for fk, (st, vals) in fun.items():
                c = vals * p / om2 / st                          # share of the static value carried by each mode
                rr = {"residual": float(1.0 - c.sum())}
                for s in SCALES:
                    fs = s * f
                    rr[f"s{s:.2f}"] = {"slow_T_gt_1ms": float(c[fs < 1000.0].sum()), "abs_slow": float(np.abs(c[fs < 1000.0]).sum()),
                                       "mid_0p1_1ms": float(c[(fs >= 1000.0) & (fs < 10000.0)].sum()), "residual_fast": float(1.0 - c.sum())}
                rr["mode_shares"] = {f"{i}@{fz:.0f}Hz": float(c[i - 1]) for i, fz in band}
                # how far the frequencies would have to drop for the slow share to reach the lead's break-even (0.40 yield / 0.485 ult)
                order = np.argsort(f)
                cum = np.cumsum(c[order])
                for thr in (0.40, 0.485):
                    hit = np.nonzero(cum >= thr)[0]
                    rr[f"scale_for_slow_share_{thr}"] = (float(1000.0 / f[order][hit[0]]) if hit.size else None)
                rr["cum_share_below_2kHz"] = float(c[f < 2000.0].sum())
                rr["cum_share_below_3kHz"] = float(c[f < 3000.0].sum())
                top = np.argsort(-np.abs(c))[:6]
                rr["top_modes"] = [[int(i + 1), float(f[i]), float(c[i])] for i in top]
                row[fk] = rr
            rows.append(row)
        out["points"][lab] = {"xyz_L1_mm": x.tolist(), "nearest_L2_node_dist_mm": float(d0), "nodes": rows}
    # FA-1 columns at the J-FWD node: proportionality check and MS at the shares
    cols = {c: col_ms(fa, c, 8314) for c in ("FA1Q", "FA1D", "FA1U", "FA1S")}
    be_y = {c: P[c] * (1 + v[0]) for c, v in cols.items()}
    be_u = {c: P[c] * (1 + v[1]) for c, v in cols.items() if v[1] is not None}
    # affine fit of 1/(1+MS) (= stress / allowable) vs pressure through the four columns
    pp = np.array([P[c] for c in cols])
    fy = np.polyfit(pp, [1 / (1 + cols[c][0]) for c in cols], 1)
    fu = np.polyfit(pp, [1 / (1 + cols[c][1]) for c in cols], 1)

    def ms_at(x, kind="y", how="prop"):
        if kind == "y":
            peq = x * P["FA1S"] + (1 - x) * P["FA1D"]
            return (be_y["FA1D"] / peq - 1) if how == "prop" else (1 / np.polyval(fy, peq) - 1), peq
        peq = x * P["FA1S"] + (1 - x) * P["FA1U"]
        return (be_u["FA1U"] / peq - 1) if how == "prop" else (1 / np.polyval(fu, peq) - 1), peq

    def x_be(kind, how):
        lo, hi = 0.0, 1.0
        for _ in range(60):
            m = 0.5 * (lo + hi)
            lo, hi = (m, hi) if ms_at(m, kind, how)[0] > 0 else (lo, m)
        return 0.5 * (lo + hi)

    out["fa1_columns_at_JFWD"] = {c: {"P_bar_abs": P[c], "MS_y": v[0], "MS_u": v[1], "vm_MPa": v[2], "breakeven_bar_yield": be_y[c],
                                      "breakeven_bar_ult": be_u.get(c)} for c, v in cols.items()}
    out["proportionality_spread_pct"] = {"yield": 100 * (max(be_y.values()) / min(be_y.values()) - 1),
                                          "ult": 100 * (max(be_u.values()) / min(be_u.values()) - 1)}
    out["breakeven_slow_share"] = {"yield_prop_FA1D": x_be("y", "prop"), "ult_prop_FA1U": x_be("u", "prop"),
                                   "yield_affine_4col": x_be("y", "aff"), "ult_affine_4col": x_be("u", "aff")}
    ms_tab = []
    for lab, pt in out["points"].items():
        for r in pt["nodes"]:
            for fk in ("principal", "tensor"):
                for s in SCALES:
                    sh = r[fk][f"s{s:.2f}"]
                    for which, x in (("signed", sh["slow_T_gt_1ms"]), ("abs", sh["abs_slow"])):
                        my, py = ms_at(max(x, 0.0) if which == "signed" else x, "y")
                        mu, pu = ms_at(max(x, 0.0) if which == "signed" else x, "u")
                        ms_tab.append({"point": lab, "node": r["node"], "nearest": r["nearest"], "functional": fk, "scale": s, "share": which,
                                       "slow": x, "Peq_y_bar": py, "MS_y": my, "Peq_u_bar": pu, "MS_u": mu,
                                       "MS_y_affine": ms_at(max(x, 0.0), "y", "aff")[0], "MS_u_affine": ms_at(max(x, 0.0), "u", "aff")[0]})
    out["ms_at_shares"] = ms_tab
    (RES / "fa1_band_sensitivity.json").write_text(json.dumps(out, indent=1, default=float))
    # table
    L = [f"FA-1 column sensitivity at TC-01 ({run}: all bodies at mesh level 2, f_max {f.max():.0f} Hz). Shares of the static unit-pressure stress "
         "(dominant principal direction; tensor projection in brackets) [SIM]; MS [DERIVED] with Peq = slow x 151.04 + (1 - slow) x 93 / 102 bar.", "",
         "| point (nearest L2 node) | f scale | slow T > 1 ms | 0.1-1 ms | residual (fast) | " + " | ".join(f"mode {i} ({fz:.0f} Hz)" for i, fz in band) +
         " | Peq yield / ult bar | MS_y / MS_u |", "|---|---|---|---|---|" + "---|" * len(band) + "---|---|"]
    for lab, pt in out["points"].items():
        r = [q for q in pt["nodes"] if q["nearest"]][0]
        for s in SCALES:
            a, t = r["principal"][f"s{s:.2f}"], r["tensor"][f"s{s:.2f}"]
            msr = [m for m in ms_tab if m["node"] == r["node"] and m["functional"] == "principal" and m["scale"] == s and m["share"] == "signed"][0]
            L.append(f"| {lab} (node {r['node']}, {pt['nearest_L2_node_dist_mm']:.2f} mm) | {s:.2f} | {a['slow_T_gt_1ms']:+.3f} ({t['slow_T_gt_1ms']:+.3f}) | "
                     f"{a['mid_0p1_1ms']:+.3f} ({t['mid_0p1_1ms']:+.3f}) | {a['residual_fast']:+.3f} ({t['residual_fast']:+.3f}) | "
                     + " | ".join(f"{r['principal']['mode_shares'][k]:+.3f} ({r['tensor']['mode_shares'][k]:+.3f})" for k in r["principal"]["mode_shares"])
                     + f" | {msr['Peq_y_bar']:.1f} / {msr['Peq_u_bar']:.1f} | {msr['MS_y']:+.3f} / {msr['MS_u']:+.3f} |")
    L += ["", "Distance to the break-even (nearest node, principal functional): uniform frequency scale at which modes would carry a slow share of 0.40 / 0.485, "
          "and the share carried by all modes below 2 / 3 kHz:", ""]
    for lab, pt in out["points"].items():
        r = [q for q in pt["nodes"] if q["nearest"]][0]["principal"]
        fm = lambda v: "never (computed modes)" if v is None else f"x{v:.3f}"
        L.append(f"- {lab}: slow share 0.40 at f {fm(r['scale_for_slow_share_0.4'])}, 0.485 at f {fm(r['scale_for_slow_share_0.485'])}; "
                 f"modes below 2 kHz carry {r['cum_share_below_2kHz']:+.3f}, below 3 kHz {r['cum_share_below_3kHz']:+.3f}")
    L += ["", "Neighbour spread (every TC-01 node within 2 mm of the L1 point; principal functional; slow share at f scale 1.00 / 0.90 / 0.85):", ""]
    for lab, pt in out["points"].items():
        sl = {s: [q["principal"][f"s{s:.2f}"]["slow_T_gt_1ms"] for q in pt["nodes"]] for s in SCALES}
        L.append(f"- {lab}: {len(pt['nodes'])} nodes; " + "; ".join(f"x{s:.2f}: {min(v):+.3f} .. {max(v):+.3f}" for s, v in sl.items()))
    c = out["fa1_columns_at_JFWD"]
    L += ["", "F1 columns at the J-FWD node (L1 node 8314) and the proportionality check (break-even pressure P x (1 + MS)) [SIM / DERIVED]:", "",
          "| column | P bar abs | MS_y | MS_u | vm MPa | break-even yield bar | break-even ult bar |", "|---|---|---|---|---|---|---|"]
    for k, v in c.items():
        L.append(f"| {k} | {v['P_bar_abs']:.2f} | {v['MS_y']:+.3f} | {v['MS_u']:+.3f} | {v['vm_MPa']:.1f} | {v['breakeven_bar_yield']:.1f} | {v['breakeven_bar_ult']:.1f} |")
    be = out["breakeven_slow_share"]
    L += ["", f"Spread of the break-even pressure across the four columns: yield {out['proportionality_spread_pct']['yield']:.2f} %, ultimate "
          f"{out['proportionality_spread_pct']['ult']:.2f} %. Break-even slow share: yield {be['yield_prop_FA1D']:.3f} (proportional, from FA1D) / "
          f"{be['yield_affine_4col']:.3f} (affine fit of the four columns); ultimate {be['ult_prop_FA1U']:.3f} / {be['ult_affine_4col']:.3f}."]
    (RES / "tables" / "fa1_band_sensitivity.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main(sys.argv[1:])
