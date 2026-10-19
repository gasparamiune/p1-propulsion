"""m2_relight_181 v1 (2026-10-13): A1 re-run at the relight planning value 1.81 s (lead decision 2026-10-13 (2), interfaces/
CHANGELOG.md: planning value = 0.6 s + Electronics' worst-case relight sequence 1.21 s = 1.81 s; GNC re-runs A1 at 1.81 s and
puts the result in gnc.json v3).

Sources of the two sequence times (Electronics firmware v2.7 SIL, CHANGELOG 2026-10-13, Electronics line):
  SEQ_WORST 1.21 s  worst relight sequence, valve command -> Pc confirm (1.15 s primed + 0.06 s bleed; lead message: 0.35 MV
                    ramp + 0.15 cock hold + 0.35 check + 0.30 C7 + 0.06 bleed)
  SEQ_SIL   0.76 s  SIL nominal relight; lead message: may serve as the lower end of the latency distribution until
                    Combustion's RC-03 distribution arrives
Mapping onto the 6-DOF (sim6/run6 v2.7-dev; same construction as the 1.1 / 1.7 s placeholder runs of m2_throat_mc):
  relight start delay in the Monte Carlo = ignition draw U(0.2, 0.6) s (run6.draw, brief) + t_ign_add; planning value
  t_ign_est = 0.6 s (top of that draw) + the planned sequence time.
  LATE  (the planned case, 'A1 at 1.81 s'): t_ign_add = SEQ_WORST 1.21 s -> start delay U(1.41, 1.81) s, top = planning value
  EARLY (latency lower end):              t_ign_add = SEQ_SIL - 0.2 = 0.56 s -> start delay U(0.76, 1.16) s, bottom = SIL
                                          nominal; planning value 1.81 s (the FSW plans on the worst case)
  UNPLANNED (sensitivity): t_ign_add 1.21 s with the planning value left at 1.7 s (FSW not updated)
  The two brackets cover start delays 0.76-1.81 s. Adding the ignition draw to a sequence time that already contains the
  0.35 s ignition check is the lead's planning rule (conservative for the late end); it is not a latency model.
Cases (flight software v2.7 provisional: k_est_asc 2, ratchet; N2O 2.00 kg; 500 runs, draws seed 101 = the same draws as
the 1.7 s runs; growth g_end U(0.07, 0.11) from its own generator as in m2_throat_mc, J_ref FIXED at the 1.7 s nominal flight
of each basis (growth per unit exposure unchanged, so the relight timing is the only change)):
  rl181_A1_none_k2 / rl181_A1_pc_k2 / rl181_A1J_none_k2 / rl181_A1J_pc_k2   LATE, paired against tg_* (1.7 s) runs
  rl181e_A1_none_k2 / rl181e_A1_pc_k2 / rl181e_A1J_none_k2 / rl181e_A1J_pc_k2 EARLY, paired against the LATE case
  rl181u_A1_none_k2                                                         UNPLANNED, paired against the LATE case
A1 = closure basis (pc2), A1J = ENG-07d basis (servo pair 6.6 V, J_int 1.6e-3, notch +/-15 %).
Nominal part: A1 flights without wind or noise for LATE / EARLY / UNPLANNED / the 1.7 s reference, flight software with and
without k_est_asc 2: relight command altitude and speed, N2O burned, usable liquid, reserve under the +25 % rule, minus the
unignited N2O of a relight from the Electronics SIL (successful relight max 8.8 g, vapour line; no-light inventory 26.59 g,
liquid line with the C7 extension; Electronics work area results/sil_v2p7/S10_review_foldin.json, read at run time).
Duty-cycle check: engine-on counter p99 / max of each case against the published A1 sizing cycle (index, read at run time).
Env: GNC_IFACE, GNC_ACT_RATE, GNC_RL181_OUT (default out/relight_181), GNC_RL181_CASES (comma list), GNC_RL181_PARTS
(nominal,mc). Output: <out>/relight_181.json + mc6_runs_<case>_rl181.csv"""
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
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_mc6 as M  # noqa: E402
import m2_prop_closure as PC  # noqa: E402
import m2_mechv2_mc as MV  # noqa: E402
import m2_throat_mc as TG  # noqa: E402

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_RL181_OUT", f"{S}/relight_181")
PARTS = os.environ.get("GNC_RL181_PARTS", "nominal,mc").split(",")
TG_JSON = {"tg": f"{S}/throat_growth/throat_growth.json", "tga": f"{S}/throat_growth_a1k2/throat_growth.json"}
TG_CSV = {"tg_A1_none_k2": f"{S}/throat_growth_a1k2/mc6_runs_tg_A1_none_k2_tg.csv",
          "tg_A1J_none_k2": f"{S}/throat_growth_a1k2/mc6_runs_tg_A1J_none_k2_tg.csv",
          "tg_A1J_pc_k2": f"{S}/throat_growth_a1k2/mc6_runs_tg_A1J_pc_k2_tg.csv",
          "tg_A1_pc_k2": f"{S}/throat_growth/mc6_runs_tg_A1_pc_k2_tg.csv"}
DC_INDEX = f"{S}/duty_cycles_v3/duty_cycles_index_v3.json"
SIL_FOLDIN = os.environ.get("GNC_SIL_FOLDIN", "/home/claude/work/electronics/results/sil_v2p7/S10_review_foldin.json")
# Electronics firmware v2.7 SIL (interfaces/CHANGELOG.md 2026-10-13, Electronics line) and lead decision 2026-10-13 (2)
SEQ_WORST = 1.21
SEQ_SIL = 0.76
SEQ_SRC = ("Electronics firmware v2.7 SIL via interfaces/CHANGELOG.md 2026-10-13 (worst relight sequence valve command -> Pc "
           "confirm 1.15 s primed / 1.21 s with 0.06 s bleed; SIL nominal 0.76 s) + lead decision 2026-10-13 (2) (planning value "
           "0.6 + 1.21 = 1.81 s) + lead message to GNC (0.76 s as the lower end of the latency distribution until RC-03)")
IGN_DRAW = (0.2, 0.6)   # run6.draw: _t_ign = U(0.2, 0.6) s (brief); checked against the draws below


def rows_csv(p):
    return list(csv.DictReader(open(p))) if os.path.exists(p) else None


def stats(rows, m_load, env_c):
    d = TG.stats(rows, m_load, env_c)
    g = lambda k: np.array([float(r[k]) for r in rows])  # noqa: E731
    hi, t90 = g("h_ign"), g("t90_relight")
    d["relight_cmd_h_p01_p50_m"] = [float(np.percentile(hi, 1)), float(np.percentile(hi, 50))]
    d["t90_relight_p50_max_s"] = [float(np.percentile(t90[t90 > 0], 50)) if np.any(t90 > 0) else None, float(t90.max())]
    return d


def sil_unlit():
    """Unignited N2O of a relight from the Electronics SIL fold-in (successful relights and no-light cases)."""
    try:
        d = json.load(open(SIL_FOLDIN))
    except (OSError, ValueError):
        return None
    ok, nolight = [], []
    for c in d["cases"]:
        st = c.get("starts") or []
        if len(st) < 2 or "ox_unlit_kg" not in st[1]:
            continue
        (ok if c.get("first_abort") == "NONE" else nolight).append((c["case"], float(st[1]["ox_unlit_kg"])))
    import hashlib
    return dict(file="Electronics work area results/sil_v2p7/S10_review_foldin.json (not in the hub)",
                sha256_16=hashlib.sha256(open(SIL_FOLDIN, "rb").read()).hexdigest()[:16],
                successful_relight_max_kg=max(v for _, v in ok) if ok else None, successful_relight_cases=ok,
                no_light_relight_max_kg=max(v for _, v in nolight) if nolight else None, no_light_relight_cases=nolight,
                tag="SIL (Electronics firmware v2.7 plant model; not measured)")


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    src = R.sources()
    tg = json.load(open(TG_JSON["tg"]))
    tga = json.load(open(TG_JSON["tga"]))
    ph = tg["relight_placeholder"]
    ncs = PC.MM.NCS["slots"]
    est0 = R.DEF["t_ign_est"]
    plan = est0 + SEQ_WORST
    add_late, add_early = SEQ_WORST, SEQ_SIL - IGN_DRAW[0]
    jr = tg["j_ref"]
    dci = json.load(open(DC_INDEX)) if os.path.exists(DC_INDEX) else {}
    a1dc = {c["name"]: c for c in dci.get("cycles", []) if c["name"].startswith("DC-A1_full_flight_disp_p99")}
    env_c = max((c.get("engine_on_counter_s") or 0.0) for c in a1dc.values()) if a1dc else None
    sil = sil_unlit()
    out = dict(version="m2_relight_181 v1", date="2026-10-13", sim=s6.SIM6_VERSION, iface=R.IFACE,
               interfaces={k: (src[k] or {}).get("version") for k in ("comb", "mech", "el")}, m_n2o_kg=PC.M_TANK,
               rule=dict(reserve=PC.RESERVE, trapped=PC.TRAP),
               sequence=dict(worst_s=SEQ_WORST, sil_nominal_s=SEQ_SIL, source=SEQ_SRC, planning_rule_base_s=est0,
                             planning_value_s=plan, nc_slots_previous_s=ncs,
                             previous_placeholder=dict(t_ign_add_s=ph["t_ign_add_s"], t_ign_est_s=ph["t_ign_est_s"])),
               mapping=dict(ignition_draw_s=IGN_DRAW, late=dict(t_ign_add_s=add_late, t_ign_est_s=plan,
                                                                start_delay_range_s=[IGN_DRAW[0] + add_late, IGN_DRAW[1] + add_late]),
                            early=dict(t_ign_add_s=add_early, t_ign_est_s=plan,
                                       start_delay_range_s=[IGN_DRAW[0] + add_early, IGN_DRAW[1] + add_early]),
                            unplanned=dict(t_ign_add_s=add_late, t_ign_est_s=ph["t_ign_est_s"]),
                            note="start delay = ignition draw + t_ign_add; the planning value is the top of the late range"),
               j_ref_fixed=dict(A1=jr["A1"], A1J=jr["A1J"], source="throat_growth.json j_ref (1.7 s nominal flights)"),
               growth_band=TG.BAND, sil_unignited=sil,
               a1_sizing_cycles={k: dict(engine_on_counter_s=v.get("engine_on_counter_s"), burn_time_s=v.get("burn_time_s"),
                                         sha256=v.get("sha256")) for k, v in a1dc.items()})
    A1b = PC.DC["A1"]
    A1Jb = MV.CASES["m2_J1.6_n15"][0]
    if "nominal" in PARTS:
        nom = {}
        sets = {"ref_1.7s": (ph["t_ign_add_s"], ph["t_ign_est_s"]), "late_1.81s": (add_late, plan),
                "early_1.81s": (add_early, plan), "unplanned_1.7s": (add_late, ph["t_ign_est_s"])}
        b_ok = (sil or {}).get("successful_relight_max_kg") or 0.0
        b_nl = (sil or {}).get("no_light_relight_max_kg") or 0.0
        for lab, (ad, es) in sets.items():
            for fsw in (0, 2):
                r = PC.nominal(dict(A1b, t_ign_add=ad, t_ign_est=es, k_est_asc=fsw), PC.M_TANK)
                keep = {k: r[k] for k in ("landed_ok", "closes", "h_ign", "v_ign", "n2o_burned", "usable_left", "reserve_frac",
                                          "burn_time_s", "impulse_Ns", "h_max", "td_vz", "starts", "exhausted")}
                keep["t_ign_add_s"], keep["t_ign_est_s"], keep["k_est_asc"] = ad, es, fsw
                keep["nominal_start_delay_s"] = float(R.build(R.cfg_of(**dict(A1b, t_ign_add=ad, t_ign_est=es,
                                                                              m_n2o=PC.M_TANK)))[0][s6.P_t_ign])
                for nm, b in (("successful_relight_sil", b_ok), ("no_light_inventory_sil", b_nl)):
                    keep[f"reserve_frac_minus_{nm}"] = (r["usable_left"] - b) / r["n2o_burned"]
                nom[f"A1|{lab}|k{fsw}"] = keep
                print(f"A1 {lab:15s} k{fsw}: delay {keep['nominal_start_delay_s']:.2f} s plan {es:.2f} s | relight cmd h "
                      f"{r['h_ign']:.1f} m v {r['v_ign']:.1f} m/s | burned {r['n2o_burned']:.4f} usable {r['usable_left']:.4f} "
                      f"reserve {100 * r['reserve_frac']:.1f} % (-SIL ok {100 * keep['reserve_frac_minus_successful_relight_sil']:.1f}"
                      f" / -no-light {100 * keep['reserve_frac_minus_no_light_inventory_sil']:.1f} %) burn {r['burn_time_s']:.2f} s "
                      f"td_vz {r['td_vz']:.2f} ok {r['landed_ok']} closes {r['closes']}", flush=True)
        out["nominal"] = nom
    if "mc" in PARTS:
        GA = dict(throat_g_band=TG.BAND)

        def mk(base, ad, es, growth):
            b = dict(A1b, m_fixed=PC.M_TANK) if base == "A1" else dict(A1Jb)
            o = dict(b, t_ign_add=ad, t_ign_est=es, k_est_asc=2)
            if growth:
                o.update(throat_jref=jr[base], throat_loop=1, **GA)
            return o
        cases = {}
        for base in ("A1", "A1J"):
            for gr, gl in ((False, "none"), (True, "pc")):
                cases[f"rl181_{base}_{gl}_k2"] = (mk(base, add_late, plan, gr), f"tg_{base}_{gl}_k2",
                                                  f"{base} {'growth' if gr else 'no growth'}, k_est_asc 2, LATE: sequence "
                                                  f"{add_late:.2f} s, planning value {plan:.2f} s")
                cases[f"rl181e_{base}_{gl}_k2"] = (mk(base, add_early, plan, gr), f"rl181_{base}_{gl}_k2",
                                                   f"{base} {'growth' if gr else 'no growth'}, k_est_asc 2, EARLY: start delay "
                                                   f"U({IGN_DRAW[0] + add_early:.2f}, {IGN_DRAW[1] + add_early:.2f}) s, planning "
                                                   f"value {plan:.2f} s")
        cases["rl181u_A1_none_k2"] = (mk("A1", add_late, ph["t_ign_est_s"], False), "rl181_A1_none_k2",
                                      f"A1 no growth, k_est_asc 2, UNPLANNED: sequence {add_late:.2f} s, planning value left at "
                                      f"{ph['t_ign_est_s']:.2f} s")
        sel = os.environ.get("GNC_RL181_CASES")
        if sel:
            cases = {k: v for k, v in cases.items() if k in sel.split(",")}
        mc = {}
        for name, (over, comp, note) in cases.items():
            o, rows = M.run_case(name, over, note)
            p = os.path.join(OUT, f"mc6_runs_{name}_rl181.csv")
            M.write_csv(p, rows)
            rr = rows_csv(p)
            tig = np.array([float(r["t_ign"]) for r in rr]) if "t_ign" in rr[0] else None
            st = stats(rr, o["m_n2o_mc_kg"], env_c)
            st.update(note=note, fail_modes=o["summary"]["fail_modes"], m_liftoff_kg=o["m_liftoff_kg"], cpu_s=o["cpu_s"],
                      config={k: over.get(k) for k in ("throat_g_band", "throat_jref", "throat_loop", "k_est_asc", "t_ign_add",
                                                       "t_ign_est")},
                      start_delay_drawn_min_max_s=[float(tig.min()), float(tig.max())] if tig is not None else None)
            for lab, cp in (("vs_comparator", comp), ("vs_1.7s", f"tg_{name.split('_', 1)[1]}" if not name.startswith("rl181_")
                                                     else None)):
                if not cp:
                    continue
                bp = TG_CSV.get(cp) or os.path.join(OUT, f"mc6_runs_{cp}_rl181.csv")
                bb = rows_csv(bp)
                if bb:
                    st[lab] = dict(TG.pair(bb, rr), comparator=cp, comparator_csv=bp)
            if sil:
                use = np.array([float(r["liq_left"]) for r in rr]) - PC.TRAP * o["m_n2o_mc_kg"]
                st["usable_p01_minus_sil_successful_relight_kg"] = float(np.percentile(use, 1) - sil["successful_relight_max_kg"])
                st["n_usable_below_sil_successful_relight"] = int(np.sum(use < sil["successful_relight_max_kg"]))
            if env_c:
                bt = np.array([float(r["burn_time"]) for r in rr])
                st["engine_on_counter_over_a1_sizing_cycle"] = dict(sizing_counter_s=env_c, n_over=int(np.sum(bt > env_c)),
                                                                    p99_s=float(np.percentile(bt, 99)), max_s=float(bt.max()))
            mc[name] = st
            v = st.get("vs_comparator", {})
            print(f"{name:20s} P {st['P']:.3f} [{st['ci95'][0]:.3f},{st['ci95'][1]:.3f}] vs {comp} {v.get('P_base', float('nan')):.3f}: "
                  f"-{v.get('lost')}/+{v.get('gained')} p {v.get('p', float('nan')):.2g} | usable p01 {st['usable_left_p01_kg']:.3f} "
                  f"<0 {st['n_usable_below_zero']} | relight h p01/p50 {st['relight_cmd_h_p01_p50_m'][0]:.1f}/"
                  f"{st['relight_cmd_h_p01_p50_m'][1]:.1f} m | counter p99/max {st['burn_time_p50_p99_max_s'][1]:.2f}/"
                  f"{st['burn_time_p50_p99_max_s'][2]:.2f} s (A1 sizing {env_c}) | fails {st['fail_modes']} ({o['cpu_s']:.0f}s)",
                  flush=True)
        out["monte_carlo"] = mc
    out["cpu_s"] = time.time() - t0
    with open(os.path.join(OUT, "relight_181.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "relight_181.json"))


if __name__ == "__main__":
    main()
