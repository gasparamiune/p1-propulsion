"""m2_regband_mc v1.1 (GNC, 2026-10-13; v1.1 adds the lead's provisional 62 m cap cases, GNC_RB_LEADCAP): B1 with the fuel-regression-law band (review RC-07) together with throat growth (lead
request 2026-10-13: add the regression band a x0.6-1.5, n 0.35-0.68, with Combustion's recommended distribution or uniform if
none, to the B1 MC dispersion together with throat growth; report P at 85 m and the apex cap that meets the 25 % reserve rule;
the 85 m cap is provisional, the final cap follows the T1-T4 regression data).

Model: sim6/run6 v2.7.1-dev regression band (gncsim.regband v1, built and validated by m2_regband_model v1 on Combustion's band
runs, data/v2/dc_gncv3_band): oxidiser and fuel flow per thrust x phi(a, n, X), X = oxidiser burned at the map flows; per-run
(a, n) ~ U(0.6, 1.5) x U(0.35, 0.68) from its own generator (seed 20261017; no recommended distribution was found in the band
files), so the other draws (seed 101) and the growth draw (seed 20261013) are unchanged and every case pairs run by run with its
no-band baseline. Liquid depletion cuts the thrust in the 6-DOF (no vapour phase): conservative against Combustion's vapour tail.
Flight software v2.7 provisional (k_est_asc 2, ratchet); N2O 2.00 kg; growth g_end U(0.07, 0.11), ECU Pc loop.
Parts (GNC_RB_PARTS, default nominal,mc,eval; scan on request):
  nominal  B1 85 m flights without dispersion at the 3 x 3 corners and g = 0 / 0.07 / 0.11; the largest hop closing the +25 %
           rule at every corner for g = 0 and 0.11 (bisection; J_ref of each height = full growth on every flight, and J_ref
           fixed at 85 m = growth per unit exposure); governing cap = the lowest over the corners at g 0.11 (flight mode)
  mc       500-run cases (GNC_RB_CASES selects): rb_B1_none_k2 (band) vs tg_B1_none_k2; rb_B1_pc_k2 (band + growth) vs
           tg_B1_pc_k2; at the governing cap: tgc_B1_cap_pc_k2 (growth only) and rbc_B1_cap_pc_k2 (band + growth); at the
           lead's provisional cap (GNC_RB_LEADCAP, default 62.0 m; 0 disables): tgl_B1_lead62_pc_k2 (growth only) and
           rbl_B1_lead62_pc_k2 (band + growth)
  scan     closing flag on a 0.25 m grid around the governing cap (bisection monotonicity check)
  eval     merge into regband_mc.json (paired exact McNemar, Wilson CI, failure modes, P by band region, web region from
           Combustion's B1 p99 results)
Env: GNC_IFACE, GNC_ACT_RATE, GNC_RB_OUT (default out/regband), GNC_RB_PARTS, GNC_RB_CASES, GNC_RB_LEADCAP.
Output: <out>/regband_nominal.json, <out>/rb_case_<case>.json, <out>/mc6_runs_<case>_rb.csv, <out>/regband_mc.json"""
import csv
import json
import os
import sys
import time
import numpy as np

os.environ.setdefault("GNC_PC_RATCHET", "1")
os.environ.setdefault("GNC_OUT", "/home/claude/work/space/out/prop_closure_m2")
os.environ.setdefault("GNC_SUFFIX", "pc2")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6, regband as RB  # noqa: E402
import m2_mc6 as M  # noqa: E402
import m2_prop_closure as PC  # noqa: E402
import m2_throat_mc as TG  # noqa: E402

VERSION = "m2_regband_mc v1.1"
S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_RB_OUT", f"{S}/regband")
PARTS = os.environ.get("GNC_RB_PARTS", "nominal,mc,eval").split(",")
A_BAND = (0.6, 1.5)           # REQ lead 2026-10-13 / combustion.json regression_law (ASSUMED band)
N_BAND = (0.35, 0.68)         # REQ lead 2026-10-13 / combustion.json regression_law (ASSUMED band)
BAND = dict(reg_band=(A_BAND, N_BAND))
G_BAND = TG.BAND
TG_CSV = {"tg_B1_none_k2": f"{S}/throat_growth/mc6_runs_tg_B1_none_k2_tg.csv",
          "tg_B1_pc_k2": f"{S}/throat_growth/mc6_runs_tg_B1_pc_k2_tg.csv"}
CORNERS = [(a, n) for a in (0.6, 1.0, 1.5) for n in (0.35, 0.5, 0.68)]
B1 = dict(PC.DC["B1"], h_target=85.0, k_est_asc=2)
LEADCAP_JREF = {}


def jl(p):
    try:
        return json.load(open(p))
    except (OSError, ValueError):
        return None


def nom(over):
    r = PC.nominal({k: v for k, v in over.items() if k != "m_fixed"}, PC.M_TANK)
    keep = ("landed_ok", "closes", "n2o_burned", "usable_left", "reserve_frac", "burn_time_s", "impulse_Ns", "h_max", "td_vz",
            "td_vh", "exhausted")
    return {k: r[k] for k in keep}


def max_h(base, lo=30.0, hi=85.0, iters=10, jmode="flight", jr85=None):
    def closes(h):
        o = dict(base, h_target=h)
        if o.get("throat_g", 0.0) > 0.0:
            o["throat_jref"] = jr85 if jmode == "rate" else TG.j_ref({k: v for k, v in o.items() if k not in ("throat_g", "throat_jref")})[0]
        return PC.nominal(o, PC.M_TANK)["closes"], o
    c_lo, _ = closes(lo)
    if not c_lo:
        return None, None
    c_hi, o_hi = closes(hi)
    if c_hi:
        return hi, o_hi
    o_best = None
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        c, o = closes(mid)
        if c:
            lo, o_best = mid, o
        else:
            hi = mid
    if o_best is None:
        _, o_best = closes(lo)
    return lo, o_best


def part_nominal():
    t0 = time.time()
    jB, kc = TG.j_ref(dict(PC.DC["B1"], h_target=85.0))
    rows = {}
    for a, n in [(None, None)] + CORNERS:
        for g in (0.0, 0.07, 0.11):
            o = dict(B1)
            if a is not None:
                o.update(reg_a=a, reg_n=n)
            if g > 0:
                o.update(throat_g=g, throat_jref=jB, throat_loop=1)
            r = nom(o)
            key = f"{'no_band' if a is None else f'a{a}|n{n}'}|g{g:.2f}"
            rows[key] = r
            print(f"nominal 85 m {key:18s} landed {r['landed_ok']} closes {r['closes']} burned {r['n2o_burned']:.4f} reserve "
                  f"{100 * r['reserve_frac']:5.1f} % burn {r['burn_time_s']:.2f} s exhausted {r['exhausted']}", flush=True)
    caps = {}
    for a, n in [(None, None)] + CORNERS:
        for g, jm in ((0.0, "flight"), (0.11, "flight"), (0.11, "rate")):
            o = dict(B1)
            if a is not None:
                o.update(reg_a=a, reg_n=n)
            if g > 0:
                o.update(throat_g=g, throat_loop=1)
            h, ob = max_h(o, jmode=jm, jr85=jB)
            key = f"{'no_band' if a is None else f'a{a}|n{n}'}|g{g:.2f}|{jm}"
            caps[key] = dict(h_cap_m=h, nominal=nom(ob) if ob else None, throat_jref=(ob or {}).get("throat_jref"))
            print(f"cap {key:26s} h {h if h is None else round(h, 2)} m"
                  + (f" reserve {100 * caps[key]['nominal']['reserve_frac']:.1f} %" if ob else ""), flush=True)
    gov = min(((v["h_cap_m"], k) for k, v in caps.items() if k.endswith("|g0.11|flight") and v["h_cap_m"] is not None),
              default=(None, None))
    out = dict(version=VERSION, sim=s6.SIM6_VERSION, regband=RB.VERSION, regband_model=RB.load()[1], j_ref_B1_85m=jB, k_cf=kc,
               nominal_85m=rows, caps=caps, governing_cap=dict(h_m=gov[0], case=gov[1],
                                                               rule="lowest closing hop over the 3 x 3 corners with g 0.11 on "
                                                                    "every flight (flight mode)"),
               cpu_s=time.time() - t0)
    with open(os.path.join(OUT, "regband_nominal.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("governing cap", gov, flush=True)
    return out


def cases(nomj):
    if nomj is None:   # the 85 m cases do not need the nominal part (run in parallel with it)
        nomj = dict(j_ref_B1_85m=TG.j_ref(dict(PC.DC["B1"], h_target=85.0))[0], governing_cap=dict(h_m=None, case=None))
    jB = nomj["j_ref_B1_85m"]
    gov = nomj["governing_cap"]
    hc = gov["h_m"]
    GA = dict(throat_g_band=G_BAND, throat_loop=1)
    c = {"rb_B1_none_k2": (dict(B1, m_fixed=PC.M_TANK, **BAND), "tg_B1_none_k2",
                           "B1 85 m, k_est_asc 2, regression band U(0.6, 1.5) x U(0.35, 0.68), no growth"),
         "rb_B1_pc_k2": (dict(B1, m_fixed=PC.M_TANK, throat_jref=jB, **GA, **BAND), "tg_B1_pc_k2",
                         "B1 85 m, k_est_asc 2, regression band + growth U(0.07, 0.11), ECU Pc loop")}
    if hc is not None:
        hc = float(np.floor(hc * 10.0) / 10.0)
        jc = nomj["caps"][gov["case"]]["throat_jref"]
        c["tgc_B1_cap_pc_k2"] = (dict(B1, h_target=hc, m_fixed=PC.M_TANK, throat_jref=jc, **GA), None,
                                 f"B1 at the governing cap {hc:.1f} m, k_est_asc 2, growth only (J_ref of the {hc:.1f} m flight)")
        c["rbc_B1_cap_pc_k2"] = (dict(B1, h_target=hc, m_fixed=PC.M_TANK, throat_jref=jc, **GA, **BAND), "tgc_B1_cap_pc_k2",
                                 f"B1 at the governing cap {hc:.1f} m, k_est_asc 2, regression band + growth")
    # v1.1: the lead's provisional cap (REQ lead decision 2026-10-13: B1 cap 62 m, the GNC 62.9 m rounded down, until the T1-T4
    # regression data). J_ref = the no-band B1 flight at that height (the convention of rb_B1_pc_k2 at 85 m: full growth g_end on
    # every flight of that height).
    hl = float(os.environ.get("GNC_RB_LEADCAP", "62.0"))
    if hl > 0.0:
        if hl not in LEADCAP_JREF:
            LEADCAP_JREF[hl] = TG.j_ref(dict(B1, h_target=hl))[0]
        jl_ = LEADCAP_JREF[hl]
        c["tgl_B1_lead62_pc_k2"] = (dict(B1, h_target=hl, m_fixed=PC.M_TANK, throat_jref=jl_, **GA), None,
                                    f"B1 at the lead's provisional cap {hl:.1f} m, k_est_asc 2, growth only (J_ref of the "
                                    f"no-band {hl:.1f} m flight)")
        c["rbl_B1_lead62_pc_k2"] = (dict(B1, h_target=hl, m_fixed=PC.M_TANK, throat_jref=jl_, **GA, **BAND), "tgl_B1_lead62_pc_k2",
                                    f"B1 at the lead's provisional cap {hl:.1f} m, k_est_asc 2, regression band + growth")
    return c


def rows_csv(p):
    return list(csv.DictReader(open(p))) if os.path.exists(p) else None


def part_mc(nomj):
    cs = cases(nomj)
    sel = os.environ.get("GNC_RB_CASES")
    if sel:
        cs = {k: v for k, v in cs.items() if k in sel.split(",")}
    for name, (over, comp, note) in cs.items():
        o, rows = M.run_case(name, over, note)
        p = os.path.join(OUT, f"mc6_runs_{name}_rb.csv")
        M.write_csv(p, rows)
        keep = {k: o.get(k) for k in ("case", "note", "m_n2o_mc_kg", "m_liftoff_kg", "cpu_s", "sim")}
        keep["fail_modes"] = o["summary"]["fail_modes"]
        keep["config"] = {k: over.get(k) for k in ("h_target", "throat_g_band", "throat_jref", "throat_loop", "k_est_asc", "reg_band")}
        keep["comparator"] = comp
        with open(os.path.join(OUT, f"rb_case_{name}.json"), "w") as f:
            json.dump(keep, f, indent=1, default=float)
        print(f"{name}: P {np.mean([r['ok'] for r in rows]):.3f} fails {o['summary']['fail_modes']} ({o['cpu_s']:.0f} s)", flush=True)


def web_region():
    """Combustion's B1 p99 residual web over the corners (band summary): fraction of the (a, n) rectangle below 1 mm."""
    M_ = RB.load()[0]
    b1 = M_.get("combustion_summary_B1", {})
    grid = {}
    for k, v in b1.items():
        if k.startswith("DC-B1v3p99-") and v.get("w_min_end_mm") is not None:
            grid[(v["regression_scale"], v["n"])] = v["w_min_end_mm"]
    if len(grid) < 9:
        return None
    ag, ng = (0.6, 1.0, 1.5), (0.35, 0.5, 0.68)
    W = np.array([[grid[(a, n)] for n in ng] for a in ag])
    A, Nn = np.meshgrid(np.linspace(*A_BAND, 181), np.linspace(*N_BAND, 133), indexing="ij")
    from scipy.interpolate import RegularGridInterpolator
    f = RegularGridInterpolator((ag, ng), W)
    w = f(np.column_stack([A.ravel(), Nn.ravel()]))
    return dict(corner_web_mm={f"a{a}|n{n}": grid[(a, n)] for a in ag for n in ng}, fraction_below_1mm=float(np.mean(w < 1.0)),
                fraction_burnthrough=float(np.mean(w <= 0.0)), interp=f, note="bilinear over Combustion's 9 corners of DC-B1 v3 "
                "p99 (no growth); web <= 0 = burn-through")


def part_eval(nomj):
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, regband=RB.VERSION, iface=R.IFACE,
               model_file=RB.load()[1], band=dict(a_scale=A_BAND, n=N_BAND, distribution="uniform x uniform, independent, own "
                                                  "generator seed 20261017 (no recommended distribution found)"),
               growth_band=G_BAND, nominal=nomj, rule=dict(reserve=PC.RESERVE, trapped=PC.TRAP))
    wr = web_region()
    mc = {}
    for name, (over, comp, note) in cases(nomj).items():
        rr = rows_csv(os.path.join(OUT, f"mc6_runs_{name}_rb.csv"))
        cj = jl(os.path.join(OUT, f"rb_case_{name}.json"))
        if not rr or not cj:
            continue
        st = TG.stats(rr, cj["m_n2o_mc_kg"], None)
        st.update(note=note, fail_modes=cj["fail_modes"], config=cj["config"], m_liftoff_kg=cj["m_liftoff_kg"])
        if comp:
            bp = TG_CSV.get(comp) or os.path.join(OUT, f"mc6_runs_{comp}_rb.csv")
            bb = rows_csv(bp)
            if bb:
                st["vs_comparator"] = dict(TG.pair(bb, rr), comparator=comp, comparator_csv=os.path.basename(bp))
        if "reg_a" in rr[0]:
            a = np.array([float(r["reg_a"]) for r in rr]); n = np.array([float(r["reg_n"]) for r in rr])
            ok = np.array([float(r["ok"]) for r in rr]) > 0.5
            ex = np.array([float(r["exhausted"]) for r in rr]) > 0.5
            liq = np.array([float(r["liq_left"]) for r in rr])
            bur = np.array([float(r["prop_used"]) for r in rr])
            regions = {}
            for lab, m in (("a<0.8", a < 0.8), ("0.8<=a<1.2", (a >= 0.8) & (a < 1.2)), ("a>=1.2", a >= 1.2),
                           ("n<0.46", n < 0.46), ("0.46<=n<0.57", (n >= 0.46) & (n < 0.57)), ("n>=0.57", n >= 0.57),
                           ("a<0.8 & n>=0.57", (a < 0.8) & (n >= 0.57))):
                regions[lab] = dict(n=int(m.sum()), P=float(ok[m].mean()) if m.any() else None,
                                    n_exhausted=int(ex[m].sum()))
            st["by_band_region"] = regions
            st["reg_drawn_min_max"] = dict(a=[float(a.min()), float(a.max())], n=[float(n.min()), float(n.max())])
            fails = [dict(run=int(r["run"]), a=float(r["reg_a"]), n=float(r["reg_n"]), exhausted=bool(float(r["exhausted"]) > 0.5),
                          liq_left=float(r["liq_left"]), wind=float(r["wind"])) for r in rr if float(r["ok"]) < 0.5]
            st["failed_runs"] = fails
            if wr:
                w = wr["interp"](np.column_stack([a, n]))
                st["runs_in_combustion_web_below_1mm_region"] = int(np.sum(w < 1.0))
                st["runs_in_combustion_burnthrough_region"] = int(np.sum(w <= 0.0))
        mc[name] = st
        v = st.get("vs_comparator", {})
        print(f"{name:18s} P {st['P']:.3f} [{st['ci95'][0]:.3f},{st['ci95'][1]:.3f}]"
              + (f" vs {v.get('comparator')} {v.get('P_base'):.3f}: -{v.get('lost')}/+{v.get('gained')} p {v.get('p'):.2g}" if v else "")
              + f" | exhausted {st['n_exhausted']} usable p01 {st['usable_left_p01_kg']:.3f} | fails {st['fail_modes']}", flush=True)
    out["monte_carlo"] = mc
    out["cap_scan"] = jl(os.path.join(OUT, "regband_capscan.json"))
    if wr:
        out["combustion_web_region"] = {k: v for k, v in wr.items() if k != "interp"}
    with open(os.path.join(OUT, "regband_mc.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "regband_mc.json"))


def part_scan(nomj):
    """Monotonicity check of the bisection: closing flag and reserve on a 0.25 m grid around the governing cap (worst corner,
    g 0.11, J_ref of each height) and at the same corner without growth."""
    gov = nomj["governing_cap"]
    a, n = [float(x[1:]) for x in gov["case"].split("|")[:2]]
    hc = gov["h_m"]
    out = {}
    for g in (0.11, 0.0):
        rows = []
        for h in np.arange(np.floor(hc) - 3.0, np.floor(hc) + 3.01, 0.25):
            o = dict(B1, h_target=float(h), reg_a=a, reg_n=n)
            if g > 0:
                o.update(throat_g=g, throat_loop=1)
                o["throat_jref"] = TG.j_ref({k: v for k, v in o.items() if k not in ("throat_g", "throat_jref")})[0]
            r = nom(o)
            rows.append(dict(h_m=float(h), closes=bool(r["closes"]), reserve_frac=float(r["reserve_frac"]), landed=bool(r["landed_ok"])))
        cl = [x["h_m"] for x in rows if x["closes"]]
        nc = [x["h_m"] for x in rows if not x["closes"]]
        out[f"g{g:.2f}"] = dict(rows=rows, highest_closing_m=max(cl) if cl else None, lowest_not_closing_m=min(nc) if nc else None,
                                monotone=bool(not cl or not nc or max(cl) < min(nc)))
        print(f"scan a{a} n{n} g{g:.2f}: highest closing {out[f'g{g:.2f}']['highest_closing_m']} lowest not closing "
              f"{out[f'g{g:.2f}']['lowest_not_closing_m']} monotone {out[f'g{g:.2f}']['monotone']}", flush=True)
    with open(os.path.join(OUT, "regband_capscan.json"), "w") as f:
        json.dump(dict(version=VERSION, corner=dict(a=a, n=n), governing_cap_m=hc, scans=out), f, indent=1)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    nomj = part_nominal() if "nominal" in PARTS else jl(os.path.join(OUT, "regband_nominal.json"))
    if "scan" in PARTS:
        part_scan(nomj)
    if "mc" in PARTS:
        part_mc(nomj)
    if "eval" in PARTS:
        part_eval(nomj)


if __name__ == "__main__":
    main()
