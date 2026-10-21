"""m2_relight_seq_sens v1 (2026-10-13): sensitivity of the A1 relight to a longer NC-closed relight sequence (lead request
2026-10-13: Combustion found that with the NC valve closed through the coast the valve-to-seat line can be vapour-filled at
relight; purging it through the ignition lift takes ~0.31 s against the 0.23 s slot; Electronics adds a pre-purge or a
temperature-gated ignition check that lengthens the relight sequence by ~0.1-0.3 s, exact figure to follow. Carry +0.3 s on
the relight planning value; report P(landing) and the propellant effect for A1 and B1).

Basis: sim6/run6 v2.6 on GNC_IFACE (iface_v3c: combustion.json v2.3, mechanical.json v2, electronics.json v1), N2O 2.00 kg,
v3 flight software with the ratchet, NC-closed relight sequence from combustion.json (0.80 s) on the start delay and on the
planning value (0.6 + 0.8 = 1.4 s). 500 runs, seed 101, the same draws as the baselines (the shift is added after the draw).
  A1, closure basis (m2_prop_closure pc2 configuration; paired against pc2 pc_A1_2kg):
    rs_A1_seq+0.3_planned    start delay + 0.30 s on every run and on the nominal; planning value 1.4 + 0.3 = 1.7 s
    rs_A1_seq+0.3_unplanned  start delay + 0.30 s; planning value left at 1.4 s (flight software not updated)
  A1, ENG-07d basis (m2_mechv2_mc m2_J1.6_n15: servo pair 6.6 V, J_int 1.6e-3, notch +/-15 %; paired against it):
    rs_A1J_seq+0.3_planned / rs_A1J_seq+0.3_unplanned
  B1 85 m (pc2 pc_B1_h85_2kg): one continuous burn from the pad, no in-flight relight; in sim6 the start delay and the
    planning value enter only the A-profile relight: checked here (nominal compared value by value, MC paired).
Nominal A1 flights (no wind, no noise) for +0.0 / 0.1 / 0.2 / 0.3 s, planned and unplanned: relight command altitude and
speed, N2O burned, usable liquid at touchdown, reserve under the lead's +25 % rule.
Pre-purge N2O is NOT in the 6-DOF (sim6 models no flow before the torch lights): upper bound = extra time x the ignition-
lift flow (20 % of the max-thrust N2O flow, combustion.json operating_points.max_thrust, liquid; vapour flow is lower),
subtracted from the usable liquid. For B1 it applies only if the pre-purge is also run at the pad start (a pre-liftoff
loss: the B1 nominal is re-flown at the reduced load).
Env: GNC_IFACE, GNC_ACT_RATE, GNC_RS_OUT (default out/relight_seq_sens), GNC_RS_DT (default 0.3), GNC_RS_PARTS (nominal,mc).
Output: <out>/relight_seq_sens.json + mc6_runs_<case>_rs.csv"""
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
OUT = os.environ.get("GNC_RS_OUT", f"{S}/relight_seq_sens")
DT = float(os.environ.get("GNC_RS_DT", "0.3"))
PARTS = os.environ.get("GNC_RS_PARTS", "nominal,mc").split(",")
BASE_CSV = {"pc_A1_2kg": f"{S}/prop_closure_m2/mc6_runs_pc_A1_2kg_pc2.csv",
            "m2_J1.6_n15": f"{S}/mechv2_mc/mc6_runs_m2_J1.6_n15_m2.csv",
            "pc_B1_h85_2kg": f"{S}/prop_closure_m2/mc6_runs_pc_B1_h85_2kg_pc2.csv"}
IGN_LIFT_FLOW_FRAC = 0.20    # combustion.json igniter.sequence: ignition lift 12.5-20 % flow (upper end taken)


def rows_csv(p):
    import csv
    return list(csv.DictReader(open(p))) if os.path.exists(p) else None


def pair(a, b):
    oa = np.array([float(r["ok"]) for r in a]) > 0.5
    ob = np.array([float(r["ok"]) for r in b]) > 0.5
    lost, gained = int(np.sum(oa & ~ob)), int(np.sum(~oa & ob))
    p = binomtest(lost, lost + gained, 0.5).pvalue if lost + gained else 1.0
    return dict(lost=lost, gained=gained, p=float(p), P_base=float(oa.mean()), P_case=float(ob.mean()),
                loses=bool(p < 0.05 and lost > gained))


def stats(rows, m_load):
    g = lambda k: np.array([float(r[k]) for r in rows])  # noqa: E731
    ok = g("ok") > 0.5
    liq = g("liq_left")
    use = liq - PC.TRAP * m_load
    landed = g("landed") > 0.5
    hi = g("h_ign")
    t90 = g("t90_relight")
    d = dict(n=len(rows), P=float(ok.mean()), ci95=M_wilson(int(ok.sum()), len(ok)),
             prop_used_mean_kg=float(g("prop_used").mean()), liq_left_p01_kg=float(np.percentile(liq, 1)),
             liq_left_min_kg=float(liq.min()), usable_left_p01_kg=float(np.percentile(use, 1)),
             n_exhausted=int(np.sum(g("exhausted") > 0.5)), td_vz_p99_mps=float(np.percentile(np.abs(g("td_vz")[landed]), 99)),
             relight_cmd_h_p01_p50_m=[float(np.percentile(hi, 1)), float(np.percentile(hi, 50))],
             t90_relight_p50_max_s=[float(np.percentile(t90[t90 > 0], 50)) if np.any(t90 > 0) else None,
                                    float(t90.max())])
    return d


def M_wilson(k, n, z=1.96):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [max(0.0, c - hw), min(1.0, c + hw)]


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    src = R.sources()
    comb = src["comb"]
    mdot_ox = comb["operating_points"]["max_thrust"]["mdot_ox_kg_s"]["v"]
    ncs = PC.MM.NCS["slots"]
    est0 = R.DEF["t_ign_est"] + ncs
    A1 = PC.DC["A1"]
    B1 = dict(PC.DC["B1"], h_target=85.0)
    out = dict(version="m2_relight_seq_sens v1", date="2026-10-13", sim=s6.SIM6_VERSION, iface=R.IFACE,
               interfaces={k: (src[k] or {}).get("version") for k in ("comb", "mech", "el")},
               nc_sequence_s=ncs, planning_value_s=est0, shift_s=DT, m_n2o_kg=PC.M_TANK,
               rule=dict(reserve=PC.RESERVE, trapped=PC.TRAP),
               purge_bound=dict(mdot_ox_max_kg_s=mdot_ox, ignition_lift_flow_frac=IGN_LIFT_FLOW_FRAC,
                                extra_time_s=DT, n2o_upper_bound_kg=DT * IGN_LIFT_FLOW_FRAC * mdot_ox,
                                tag="DERIVED upper bound (liquid flow at the 20 % ignition lift; a vapour-filled line flows less)"))
    mp = out["purge_bound"]["n2o_upper_bound_kg"]
    if "nominal" in PARTS:
        nom = {}
        for dt in (0.0, 0.1, 0.2, DT):
            for mode in ("planned", "unplanned"):
                if dt == 0.0 and mode == "unplanned":
                    continue
                over = dict(A1, t_ign_add=ncs + dt, t_ign_est=est0 + (dt if mode == "planned" else 0.0))
                r = PC.nominal(over, PC.M_TANK)
                r["usable_left_minus_purge_bound_kg"] = r["usable_left"] - (dt / DT) * mp if DT > 0 else r["usable_left"]
                r["reserve_frac_minus_purge_bound"] = r["usable_left_minus_purge_bound_kg"] / r["n2o_burned"]
                nom[f"A1|+{dt:.1f}s|{mode}"] = r
                print(f"A1 +{dt:.1f} s {mode:9s}: landed-ok {r['landed_ok']} relight cmd h {r['h_ign']:.1f} m v {r['v_ign']:.1f} m/s "
                      f"N2O burned {r['n2o_burned']:.4f} usable {r['usable_left']:.4f} reserve {100 * r['reserve_frac']:.1f} % "
                      f"(-purge bound {100 * r['reserve_frac_minus_purge_bound']:.1f} %) td_vz {r['td_vz']:.2f}", flush=True)
        # B1: the start delay is not used by the B profile -> compare the nominal value by value
        rb0 = PC.nominal(B1, PC.M_TANK)
        rb1 = PC.nominal(dict(B1, t_ign_add=ncs + DT, t_ign_est=est0 + DT), PC.M_TANK)
        same = all((rb0[k] == rb1[k]) or (isinstance(rb0[k], float) and np.isnan(rb0[k]) and np.isnan(rb1[k])) for k in rb0)
        rb2 = PC.nominal(B1, PC.M_TANK - mp)
        nom["B1_85m|+0.0s"] = rb0
        nom["B1_85m|+0.3s"] = dict(rb1, identical_to_baseline=bool(same))
        nom["B1_85m|pad_prepurge_loss"] = dict(rb2, load_kg=PC.M_TANK - mp,
                                               note="only if the pre-purge also runs at the pad start: load reduced by the bound")
        print(f"B1 85 m nominal: +{DT:.1f} s identical to baseline: {same}; reserve {100 * rb0['reserve_frac']:.1f} % -> with a pad "
              f"pre-purge loss of {mp * 1e3:.1f} g: {100 * rb2['reserve_frac']:.1f} % (closes {rb2['closes']})", flush=True)
        out["nominal"] = nom
    if "mc" in PARTS:
        J = MV.CASES["m2_J1.6_n15"][0]
        cases = {
            "rs_A1_seq+0.3_planned": ("pc_A1_2kg", dict(A1, m_fixed=PC.M_TANK, t_ign_add=ncs + DT, t_ign_est=est0 + DT),
                                      f"A1 (pc2 basis), relight sequence +{DT:.1f} s, planning value {est0 + DT:.1f} s"),
            "rs_A1_seq+0.3_unplanned": ("pc_A1_2kg", dict(A1, m_fixed=PC.M_TANK, t_ign_add=ncs + DT, t_ign_est=est0),
                                        f"A1 (pc2 basis), relight sequence +{DT:.1f} s, planning value NOT updated ({est0:.1f} s)"),
            "rs_A1J_seq+0.3_planned": ("m2_J1.6_n15", dict(J, t_ign_add=ncs + DT, t_ign_est=est0 + DT),
                                       f"A1 ENG-07d basis (servo pair 6.6 V, J 1.6e-3, notch), sequence +{DT:.1f} s, planned"),
            "rs_A1J_seq+0.3_unplanned": ("m2_J1.6_n15", dict(J, t_ign_add=ncs + DT, t_ign_est=est0),
                                         f"A1 ENG-07d basis, sequence +{DT:.1f} s, planning value NOT updated"),
            "rs_B1_85m_seq+0.3": ("pc_B1_h85_2kg", dict(B1, m_fixed=PC.M_TANK, t_ign_add=ncs + DT, t_ign_est=est0 + DT),
                                  "B1 85 m with the shift (no in-flight relight: expected identical)"),
        }
        mc = {}
        for name, (base, over, note) in cases.items():
            o, rows = M.run_case(name, over, note)
            M.write_csv(os.path.join(OUT, f"mc6_runs_{name}_rs.csv"), rows)
            rr = rows_csv(os.path.join(OUT, f"mc6_runs_{name}_rs.csv"))
            st = stats(rr, o["m_n2o_mc_kg"])
            bb = rows_csv(BASE_CSV[base])
            st.update(note=note, base=base, fail_modes=o["summary"]["fail_modes"], m_liftoff_kg=o["m_liftoff_kg"],
                      config_t_ign_add_s=over.get("t_ign_add"), config_t_ign_est_s=over.get("t_ign_est"), cpu_s=o["cpu_s"])
            if bb:
                st["vs_base"] = pair(bb, rr)
                st["base_stats"] = stats(bb, o["m_n2o_mc_kg"])
                if base == "pc_B1_h85_2kg":
                    keys = ("ok", "td_vz", "td_vh", "prop_used", "liq_left", "h_max")
                    st["identical_to_base"] = bool(all(abs(float(a[k]) - float(b[k])) == 0.0 for a, b in zip(bb, rr) for k in keys))
            mc[name] = st
            v = st.get("vs_base", {})
            print(f"{name:26s} P {st['P']:.3f} [{st['ci95'][0]:.3f},{st['ci95'][1]:.3f}] vs {base} {v.get('P_base', float('nan')):.3f}: "
                  f"-{v.get('lost')}/+{v.get('gained')} p {v.get('p', float('nan')):.2g} | prop mean {st['prop_used_mean_kg']:.4f} "
                  f"(base {st.get('base_stats', {}).get('prop_used_mean_kg', float('nan')):.4f}) liq p01 {st['liq_left_p01_kg']:.3f} "
                  f"min {st['liq_left_min_kg']:.3f} | relight h p01/p50 {st['relight_cmd_h_p01_p50_m'][0]:.1f}/"
                  f"{st['relight_cmd_h_p01_p50_m'][1]:.1f} m | fails {st['fail_modes']} ({o['cpu_s']:.0f}s)", flush=True)
        out["monte_carlo"] = mc
    out["cpu_s"] = time.time() - t0
    with open(os.path.join(OUT, "relight_seq_sens.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "relight_seq_sens.json"))


if __name__ == "__main__":
    main()
