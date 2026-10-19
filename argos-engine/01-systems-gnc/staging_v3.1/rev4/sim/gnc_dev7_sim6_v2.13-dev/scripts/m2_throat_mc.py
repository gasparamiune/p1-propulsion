"""m2_throat_mc v1.1 (2026-10-13; v1.1 adds the A1 no-growth k_est_asc 2 cases on both bases for the lead's paired A1
check of the provisional FSW baseline, and case_defs() for the dispersed duty cycles): in-flight throat-area growth in the GNC Monte Carlo (lead decision 2026-10-13 on review
RC-06 / REQUIREMENTS rev 2 ENG-06: "the Pc/thrust loop must tolerate 7-11 % throat-area growth within a flight"; report
P(landing) with and without growth).

Model (sim6/run6 v2.7-dev, off by default; see the sim6 header comment and run6.throat_cf_coeffs):
  At = At0 (1 + g(t)); g(t) = g_end x min(1, J(t) / J_ref), J = int (Pc/Pc_max)^0.68 dt (literature erosion-rate scaling
  used in review RC-06, no 1.5 s onset: growth starts with the burn, conservative for the ascent), J_ref = J of the
  cycle's nominal flight (computed here, not typed in). MC: g_end ~ U(0.07, 0.11) per run from its own generator (seed
  20261013), so the other 500 draws (seed 101) are unchanged and every case pairs run-by-run with its no-growth baseline.
  throat_loop 1 (the ECU as specified: Pc held on the nominal map): thrust per command x (1 + g)(1 + k_cf g), propellant
    flow x (1 + g) (c* and O/F unchanged, ASSUMED), flow-limited ceiling x (1 + k_cf g); the flight software does not
    know g (its thrust estimate is the Pc map).
  throat_loop 0 (bound of a throat-compensated thrust loop): thrust per command unchanged, flow per thrust / (1 + k_cf g).
  k_cf = relative change of the sea-level CF per unit g at the eroded expansion ratio (1-D nozzle, combustion.json gamma,
  eps and Pc map) at 12.5 / 20 / 60 / 100 % thrust.
  FSW option k_est_asc 2 (v2.7-dev DESIGN proposal, not adopted): the accelerometer thrust-effectiveness estimator with a
  signed, direction-dependent nominal drag model runs through the B-profile ascent, apex and floor descent, and the
  open-loop floor / top-up commands are divided by the estimate (bounded [0.8, 1.25]; compensated floor >= 12.5 %).
  Option 1 (first form) is kept as evidence: it subtracted the tail-first drag in the ascent (bias -2 D / F) and made B1
  worse (scratch trace 2026-10-13: k_hat 0.89 at the throttle-down with no growth).
Cycles: A1 (A-D 300 m) with the relight placeholder of the lead (0.8 + 0.3 s on the start delay and on the planning
value, 1.1 / 1.7 s), on the closure basis (pc2) and on the ENG-07d basis (servo pair 6.6 V, J 1.6e-3, notch +/-15 %);
B1 85 m hop (pc2 basis). N2O 2.00 kg. Baselines (no growth, same draws): m2_relight_seq_sens rs_A1_seq+0.3_planned,
rs_A1J_seq+0.3_planned; m2_prop_closure pc2 pc_B1_h85_2kg.
Parts (GNC_TG_PARTS, default nominal,mc): nominal = J_ref, k_cf, nominal closure table per loop mode and growth, B1
largest closing hop height under growth; mc = the 500-run cases below.
Env: GNC_IFACE, GNC_ACT_RATE, GNC_TG_OUT (default out/throat_growth), GNC_TG_CASES (comma list).
Output: <out>/throat_growth.json + mc6_runs_<case>_tg.csv"""
import csv
import json
import os
import sys
import time
import numpy as np
from scipy.stats import binomtest

os.environ.setdefault("GNC_PC_RATCHET", "1")          # the pc2 flight software (ratchet adopted)
os.environ.setdefault("GNC_OUT", "/home/claude/work/space/out/prop_closure_m2")
os.environ.setdefault("GNC_SUFFIX", "pc2")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_mc6 as M  # noqa: E402
import m2_prop_closure as PC  # noqa: E402
import m2_mechv2_mc as MV  # noqa: E402

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_TG_OUT", f"{S}/throat_growth")
PARTS = os.environ.get("GNC_TG_PARTS", "nominal,mc").split(",")
BAND = (0.07, 0.11)          # REQ ENG-06 rev 2 (lead decision 2026-10-13)
DT_RL = 0.3                  # lead decision 2026-10-13: relight placeholder 0.8 + 0.3 s
BASE_CSV = {"A1": f"{S}/relight_seq_sens/mc6_runs_rs_A1_seq+0.3_planned_rs.csv",
            "A1J": f"{S}/relight_seq_sens/mc6_runs_rs_A1J_seq+0.3_planned_rs.csv",
            "B1": f"{S}/prop_closure_m2/mc6_runs_pc_B1_h85_2kg_pc2.csv"}
DC_INDEX = f"{S}/duty_cycles_v3/duty_cycles_index_v3.json"
I = {n: i for i, n in enumerate(s6.REC_NAMES)}


def rows_csv(p):
    return list(csv.DictReader(open(p))) if os.path.exists(p) else None


def wilson(k, n, z=1.96):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [max(0.0, c - hw), min(1.0, c + hw)]


def pair(a, b):
    oa = np.array([float(r["ok"]) for r in a]) > 0.5
    ob = np.array([float(r["ok"]) for r in b]) > 0.5
    lost, gained = int(np.sum(oa & ~ob)), int(np.sum(~oa & ob))
    p = binomtest(lost, lost + gained, 0.5).pvalue if lost + gained else 1.0
    return dict(lost=lost, gained=gained, p=float(p), P_base=float(oa.mean()), P_case=float(ob.mean()),
                loses=bool(p < 0.05 and lost > gained), gains=bool(p < 0.05 and gained > lost),
                lost_runs=[int(r["run"]) for r, x, y in zip(b, oa, ob) if x and not y],
                gained_runs=[int(r["run"]) for r, x, y in zip(b, oa, ob) if y and not x])


def stats(rows, m_load, env_s):
    g = lambda k: np.array([float(r[k]) for r in rows])  # noqa: E731
    ok = g("ok") > 0.5
    liq = g("liq_left")
    use = liq - PC.TRAP * m_load
    landed = g("landed") > 0.5
    bt = g("burn_time")
    d = dict(n=len(rows), P=float(ok.mean()), ci95=wilson(int(ok.sum()), len(ok)),
             prop_used_mean_kg=float(g("prop_used").mean()), liq_left_p01_kg=float(np.percentile(liq, 1)),
             liq_left_min_kg=float(liq.min()), usable_left_p01_kg=float(np.percentile(use, 1)),
             n_usable_below_zero=int(np.sum(use < 0.0)), n_exhausted=int(np.sum(g("exhausted") > 0.5)),
             td_vz_p99_mps=float(np.percentile(np.abs(g("td_vz")[landed]), 99)) if np.any(landed) else None,
             burn_time_p50_p99_max_s=[float(np.percentile(bt, 50)), float(np.percentile(bt, 99)), float(bt.max())],
             n_burn_over_envelope=int(np.sum(bt > env_s)) if env_s else None,
             h_max_p50_p99_m=[float(np.percentile(g("h_max"), 50)), float(np.percentile(g("h_max"), 99))])
    if "throat_g_end" in rows[0]:
        ge = g("throat_g_end")
        d["throat_g_end_p01_p50_p99"] = [float(np.percentile(ge, 1)), float(np.percentile(ge, 50)), float(np.percentile(ge, 99))]
    if "throat_g" in rows[0]:
        gd = g("throat_g")
        d["throat_g_drawn_min_max"] = [float(gd.min()), float(gd.max())]
        # P by drawn growth tercile (ok rate where the growth is lowest / middle / highest)
        q = np.percentile(gd, [33.333, 66.667])
        d["P_by_drawn_g_tercile"] = [float(ok[gd <= q[0]].mean()), float(ok[(gd > q[0]) & (gd <= q[1])].mean()),
                                     float(ok[gd > q[1]].mean())]
    return d


def j_ref(over):
    """J of the cycle's nominal flight (no wind, no noise): the growth model's normalisation."""
    cfg = R.cfg_of(**dict({k: v for k, v in over.items() if k != "m_fixed"}, m_n2o=PC.M_TANK, throat_g=1e-9, throat_jref=1.0))
    res, rec, info = R.fly(dict(cfg, noise=False, wind=0.0, gust=False), nrec=10)
    kc = [float(info["tags"][f"throat_k{i}"][0]) for i in range(4)]
    return float(res["throat_J"]), kc


def nom_row(over, m=None):
    r = PC.nominal({k: v for k, v in over.items() if k != "m_fixed"}, PC.M_TANK if m is None else m)
    keep = ("landed_ok", "closes", "n2o_burned", "usable_left", "reserve_frac", "burn_time_s", "impulse_Ns", "h_max", "td_vz",
            "td_vh", "isp_delivered_s", "exhausted")
    return {k: r[k] for k in keep}


def max_h_closing(base, g, jmode, jref85, lo=50.0, hi=85.0, iters=9):
    """Largest B hop height closing the +25 % rule at 2.00 kg with growth g (bisection). jmode 'rate': J_ref fixed at
    the 85 m flight (growth per unit exposure; lower hops grow less); 'flight': J_ref of each height (g per flight)."""
    def closes(h):
        over = dict(base, h_target=h)
        if g > 0.0:
            jr = jref85 if jmode == "rate" else j_ref(over)[0]
            over.update(throat_g=g, throat_jref=jr)
        return PC.nominal(over, PC.M_TANK)["closes"]
    if not closes(lo):
        return None
    if closes(hi):
        return hi
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if closes(mid):
            lo = mid
        else:
            hi = mid
    return lo


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    src = R.sources()
    env_s = json.load(open(DC_INDEX)).get("conservative_thermal_envelope_burn_s") if os.path.exists(DC_INDEX) else None
    ncs = PC.MM.NCS["slots"]
    est0 = R.DEF["t_ign_est"] + ncs
    A1 = dict(PC.DC["A1"], t_ign_add=ncs + DT_RL, t_ign_est=est0 + DT_RL)
    A1J = dict(MV.CASES["m2_J1.6_n15"][0], t_ign_add=ncs + DT_RL, t_ign_est=est0 + DT_RL)
    B1 = dict(PC.DC["B1"], h_target=85.0)
    jr = {}
    for nm, ov in (("A1", A1), ("A1J", A1J), ("B1", B1)):
        jr[nm], kc = j_ref(ov)
    out = dict(version="m2_throat_mc v1.1", date="2026-10-13", sim=s6.SIM6_VERSION, iface=R.IFACE,
               interfaces={k: (src[k] or {}).get("version") for k in ("comb", "mech", "el")}, m_n2o_kg=PC.M_TANK,
               rule=dict(reserve=PC.RESERVE, trapped=PC.TRAP), growth_band=BAND,
               growth_band_tag="REQ ENG-06 rev 2 / lead decision 2026-10-13 (review RC-06 literature-scaled A1 v2 7.1-10.9 % "
                               "per flight; B1 v2 0.48-1.03 flights per insert at the 5 % limit = 4.9-10.4 % per flight)",
               relight_placeholder=dict(t_ign_add_s=ncs + DT_RL, t_ign_est_s=est0 + DT_RL,
                                        tag="lead decision 2026-10-13: 0.8 + 0.3 s placeholder until the Combustion v2.4 "
                                            "RC-03 latency distribution"),
               j_ref=dict(jr, tag="DERIVED nominal flight of each cycle, int (F/F_max)^0.68 dt [s]"),
               k_cf=dict(thrust_frac=[0.125, 0.2, 0.6, 1.0], v=kc, tag="DERIVED run6.throat_cf_coeffs (1-D nozzle)"),
               thermal_envelope_burn_s=env_s,
               thermal_envelope_tag="GNC DC-B1 v2 (100 m hop) conservative thermal envelope (duty_cycles_index_v3)")
    print(f"J_ref A1 {jr['A1']:.4f} A1J {jr['A1J']:.4f} B1 {jr['B1']:.4f}; k_cf {np.round(kc, 4).tolist()}; envelope {env_s}", flush=True)
    if "nominal" in PARTS:
        nom = {}
        for nm, ov in (("A1", A1), ("B1", B1)):
            nom[f"{nm}|none"] = nom_row(ov)
            nom[f"{nm}|none|fsw_k2"] = nom_row(dict(ov, k_est_asc=2))
            for g in (0.07, 0.09, 0.11):
                gg = dict(throat_g=g, throat_jref=jr[nm])
                nom[f"{nm}|g{g:.2f}|pc_loop"] = nom_row(dict(ov, throat_loop=1, **gg))
                nom[f"{nm}|g{g:.2f}|comp_bound"] = nom_row(dict(ov, throat_loop=0, **gg))
                nom[f"{nm}|g{g:.2f}|pc_loop+fsw_k2"] = nom_row(dict(ov, throat_loop=1, k_est_asc=2, **gg))
        for k, r in nom.items():
            over_env = (env_s is not None and r["burn_time_s"] > env_s)
            r["burn_over_thermal_envelope"] = bool(over_env)
            print(f"{k:26s} landed {r['landed_ok']} closes {r['closes']} burned {r['n2o_burned']:.4f} reserve "
                  f"{100 * r['reserve_frac']:.1f} % burn {r['burn_time_s']:.2f} s{' > envelope' if over_env else ''} "
                  f"apex {r['h_max']:.1f} m td_vz {r['td_vz']:.2f}", flush=True)
        hmax = {}
        for lab, g, jm, fsw in (("pc_loop|g0.11|rate", 0.11, "rate", 0), ("pc_loop|g0.11|flight", 0.11, "flight", 0),
                                ("pc_loop|g0.07|rate", 0.07, "rate", 0), ("pc_loop+fsw_k2|g0.11|rate", 0.11, "rate", 2)):
            base = dict(B1, k_est_asc=fsw) if fsw else B1
            h = max_h_closing(base, g, jm, jr["B1"])
            r = None
            if h is not None:
                ov = dict(base, h_target=h)
                ov.update(throat_g=g, throat_jref=jr["B1"] if jm == "rate" else j_ref(ov)[0])
                r = nom_row(ov)
            hmax[lab] = dict(h_target_m=h, nominal=r)
            print(f"B1 largest closing hop {lab}: {h if h is None else round(h, 1)} m"
                  + (f" (reserve {100 * r['reserve_frac']:.1f} %, burn {r['burn_time_s']:.2f} s)" if r else ""), flush=True)
        out["nominal"] = nom
        out["B1_max_closing_hop"] = dict(hmax, note="bisection 50-85 m, 9 iterations (~0.07 m); 'rate' = growth per unit "
                                                    "exposure fixed at the 85 m flight (lower hops grow less), 'flight' = "
                                                    "the full g on every height")
    if "mc" in PARTS:
        GA = dict(throat_g_band=BAND)
        cases = {
            "tg_A1_pc": ("A1", dict(A1, m_fixed=PC.M_TANK, throat_jref=jr["A1"], throat_loop=1, **GA),
                         "A1 (pc2 basis, relight placeholder), growth U(0.07, 0.11), ECU Pc loop (uncompensated)"),
            "tg_A1J_pc": ("A1J", dict(A1J, throat_jref=jr["A1J"], throat_loop=1, **GA),
                          "A1 ENG-07d basis (servo pair 6.6 V, J 1.6e-3, notch +/-15 %, placeholder), growth, Pc loop"),
            "tg_B1_pc": ("B1", dict(B1, m_fixed=PC.M_TANK, throat_jref=jr["B1"], throat_loop=1, **GA),
                         "B1 85 m, growth U(0.07, 0.11), ECU Pc loop (uncompensated)"),
            "tg_B1_comp": ("B1", dict(B1, m_fixed=PC.M_TANK, throat_jref=jr["B1"], throat_loop=0, **GA),
                           "B1 85 m, growth, throat-compensated thrust loop (bound)"),
            "tg_B1_pc_k2": ("B1", dict(B1, m_fixed=PC.M_TANK, throat_jref=jr["B1"], throat_loop=1, k_est_asc=2, **GA),
                            "B1 85 m, growth, Pc loop + FSW option k_est_asc 2 (proposal)"),
            "tg_B1_none_k2": ("B1", dict(B1, m_fixed=PC.M_TANK, k_est_asc=2),
                              "B1 85 m, NO growth, FSW option k_est_asc 2 (does the proposal cost anything?)"),
            "tg_A1_pc_k2": ("A1", dict(A1, m_fixed=PC.M_TANK, throat_jref=jr["A1"], throat_loop=1, k_est_asc=2, **GA),
                            "A1 (pc2 basis, placeholder), growth, Pc loop + k_est_asc 2 (signed drag + legs in the "
                            "landing-burn estimator; no floor compensation in the A profile)"),
            # v1.1: lead 2026-10-13 - run k_est_asc 2 paired on A1 too (one FSW for both profiles if A1 does not degrade)
            "tg_A1_none_k2": ("A1", dict(A1, m_fixed=PC.M_TANK, k_est_asc=2),
                              "A1 (pc2 basis, placeholder), NO growth, k_est_asc 2"),
            "tg_A1J_none_k2": ("A1J", dict(A1J, k_est_asc=2), "A1 ENG-07d basis, NO growth, k_est_asc 2"),
            "tg_A1J_pc_k2": ("A1J", dict(A1J, throat_jref=jr["A1J"], throat_loop=1, k_est_asc=2, **GA),
                             "A1 ENG-07d basis, growth, Pc loop + k_est_asc 2"),
        }
        sel = os.environ.get("GNC_TG_CASES")
        if sel:
            cases = {k: v for k, v in cases.items() if k in sel.split(",")}
        mc = {}
        for name, (base, over, note) in cases.items():
            o, rows = M.run_case(name, over, note)
            M.write_csv(os.path.join(OUT, f"mc6_runs_{name}_tg.csv"), rows)
            rr = rows_csv(os.path.join(OUT, f"mc6_runs_{name}_tg.csv"))
            st = stats(rr, o["m_n2o_mc_kg"], env_s)
            bb = rows_csv(BASE_CSV[base])
            st.update(note=note, base=base, base_csv=BASE_CSV[base], fail_modes=o["summary"]["fail_modes"],
                      m_liftoff_kg=o["m_liftoff_kg"], cpu_s=o["cpu_s"],
                      config={k: over.get(k) for k in ("throat_g_band", "throat_jref", "throat_loop", "k_est_asc", "t_ign_add",
                                                       "t_ign_est", "h_target", "profile")})
            if bb:
                st["vs_base"] = pair(bb, rr)
                st["base_stats"] = stats(bb, o["m_n2o_mc_kg"], env_s)
            mc[name] = st
            v = st.get("vs_base", {})
            print(f"{name:14s} P {st['P']:.3f} [{st['ci95'][0]:.3f},{st['ci95'][1]:.3f}] vs {base} {v.get('P_base', float('nan')):.3f}: "
                  f"-{v.get('lost')}/+{v.get('gained')} p {v.get('p', float('nan')):.2g} | prop mean {st['prop_used_mean_kg']:.4f} "
                  f"(base {st.get('base_stats', {}).get('prop_used_mean_kg', float('nan')):.4f}) usable p01 "
                  f"{st['usable_left_p01_kg']:.3f} (base {st.get('base_stats', {}).get('usable_left_p01_kg', float('nan')):.3f}) "
                  f"<0: {st['n_usable_below_zero']} | burn p99/max {st['burn_time_p50_p99_max_s'][1]:.2f}/"
                  f"{st['burn_time_p50_p99_max_s'][2]:.2f} s >env {st['n_burn_over_envelope']} | g_end p50 "
                  f"{(st.get('throat_g_end_p01_p50_p99') or [0, float('nan')])[1]:.3f} | fails {st['fail_modes']} ({o['cpu_s']:.0f}s)",
                  flush=True)
        out["monte_carlo"] = mc
    out["cpu_s"] = time.time() - t0
    with open(os.path.join(OUT, "throat_growth.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "throat_growth.json"))


if __name__ == "__main__":
    main()
