"""m2_v27_tests v1.1 (2026-10-13; v1.1: T12 paired with the comparator k_est_asc 0 under the same perturbation and the
wind case split into steady / gust realisations - v1 required every perturbed flight to land and FAILED on wind 8 m/s +
gusts (seed 7), which the comparator also fails (loss of attitude at floor thrust, tilt 92 deg, tip-over): a wind-limit
case, not an estimator effect; v1 output kept as v27_tests_v1.json. Output env renamed GNC_V27_OUT because m2_throat_mc
sets GNC_OUT for m2_prop_closure - v1 wrote its JSON into out/prop_closure_m2, moved by hand): verification tests of the sim6/run6 v2.7-dev additions (in-flight throat growth, FSW option
k_est_asc 2). Each test prints PASS / FAIL / INFO with its numbers; exit code = failures. Nominal flights (no wind, no noise)
unless stated; B1 = B hop 85 m on the pc2 configuration (ratchet), N2O 2.00 kg.
  T10 throat-growth model (sim6 v2.7 header equations):
      a  Pc loop (throat_loop 1), g 0.09: in the steady 20 % floor descent the delivered thrust per Pc-equivalent thrust
         F / F_pc equals (1 + g(t))(1 + k_cf(20 %) g(t)) within 0.1 % (g(t) from the recorder), and the N2O flow per command
         relative to the same flight without growth equals 1 + g(t) within 1 % (port-diameter difference allowed);
      b  compensated loop (throat_loop 0): F / F_pc = 1 and the flow ratio 1 / (1 + k_cf g(t)) within 1 %;
      c  growth law: g non-decreasing, g_end = g x min(1, J / J_ref) exactly, recorder end value = result value;
      d  J_ref of the cycle reproduces the value used by the Monte Carlo (m2_throat_mc throat_growth.json) exactly;
      e  defaults bit-identical: m2_bitcheck_v27 (v2.6 runs, iface_v3c) and m2_bitcheck_v26 re-run with v2.7 code (v2.5 runs,
         iface_v3a) report bit_identical (read from their result files).
  T11 FSW option k_est_asc 2 (provisional baseline, lead 2026-10-13):
      a  unbiased on the nominal B1 (no growth): |k_hat - 1| <= 0.01 through ascent, apex and floor descent (t > 1.5 s);
      b  tracks the growth (g 0.09): |k_hat / (F / F_pc) - 1| <= 0.02 over the last 2 s of the floor descent;
      c  floor compensation: floor command = quantised 100 N / k_hat (within half a 5 N step) and delivered floor thrust
         within 3 % of 100 N in the same window;
      d  closure: B1 85 m with g 0.11 closes the +25 % rule at 2.00 kg and burns <= the 19.0 s DC-B1 v2 time (both as
         engine-on counters; v1.1);
      e  INFO evidence of the rejected first form (option 1): minimum k_hat in the B1 ascent / floor with no growth.
  T12 estimator failure modes: B1 85 m, no growth, one perturbation per flight, each flown with k_est_asc 2 AND with the
      comparator k_est_asc 0 (v1.1): accelerometer bias +/-0.05 m/s2 (axial), accelerometer scale factor +/-0.5 %, truth
      tail-first CA x 0.7 / 1.3 and retro factor 0.25 / 0.75 (drag-model error; the FSW keeps its nominal model), wind 8 m/s
      steady, wind 6 m/s + gusts (seed 7), wind 8 m/s + gusts (seeds 3 and 7), thrust scale 0.95 / 1.05 (the error the
      option exists to remove). INFO numbers per case; analytic sensitivity printed next to each: dk = da m / F (bias),
      dk = sf (scale factor). PASS criterion (v1.1): k_est_asc 2 loses no perturbed flight that the comparator lands.
  T13 A1 with k_est_asc 2 (signed drag + legs in the landing-burn estimator; no floor compensation in the A profile): INFO
      k_hat range in the landing burn with option 0 and 2, nominal and with g 0.11; landing kept.
Env: GNC_IFACE (iface_v3c), GNC_ACT_RATE, GNC_V27_OUT (default out/v27_checks; writes v27_tests.json)."""
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("GNC_PC_RATCHET", "1")
from gncsim import run6 as R, sim6 as s6  # noqa: E402
from gncsim.propulsion import _bilin  # noqa: E402
import m2_throat_mc as TG  # noqa: E402

PC = TG.PC
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
S = "/home/claude/work/space/out"
FAIL, LOG = [], []
B1 = dict(PC.DC["B1"], h_target=85.0)


def check(name, ok, msg):
    print(f"{'PASS' if ok else 'FAIL'} {name}: {msg}", flush=True)
    LOG.append(dict(test=name, result="PASS" if ok else "FAIL", detail=msg))
    if not ok:
        FAIL.append(name)


def info(name, msg):
    print(f"INFO {name}: {msg}", flush=True)
    LOG.append(dict(test=name, result="INFO", detail=msg))


def fly(over, disp=None, **kw):
    cfg = R.cfg_of(**dict(over, m_n2o=PC.M_TANK, **kw))
    c = dict(dict(noise=False, wind=0.0, gust=False), **{k: v for k, v in kw.items() if k in ("noise", "wind", "gust", "seed",
                                                                                           "wind_dir")})
    res, rec, info_ = R.fly(dict(cfg, **c, rec_dt=0.01), disp, nrec=6000)
    return res, rec, info_


def floor_window(rec, span=2.0):
    """steady floor-descent samples: phase 3, the last `span` s before the landing burn, thrust settled."""
    t, ph, F = rec[:, I["t"]], rec[:, I["phase"]], rec[:, I["F"]]
    p3 = np.where(ph == 3)[0]
    if p3.size == 0:
        return np.array([], dtype=int)
    t_end = t[p3[-1]]
    w = p3[(t[p3] >= t_end - span)]
    dF = np.abs(np.gradient(F))
    return w[dF[w] < 0.5]


def t10(jB):
    k = TG.j_ref(B1)[1]
    k1 = k[1]
    g = 0.09
    r0, rec0, _ = fly(dict(B1, throat_g=1e-9, throat_jref=jB))
    for loop in (1, 0):
        r1, rec1, _ = fly(dict(B1, throat_g=g, throat_jref=jB, throat_loop=loop))
        w = floor_window(rec1)
        F, Fpc, gt = rec1[w, I["F"]], rec1[w, I["Fpc"]], rec1[w, I["thg"]]
        t1_ = rec1[w, I["t"]]
        # flow per command vs the no-growth flight at the same time (both on the 100 N floor command)
        j0 = np.searchsorted(rec0[:, I["t"]], t1_)
        ok0 = (j0 < len(rec0)) & (rec0[np.minimum(j0, len(rec0) - 1), I["phase"]] == 3)
        mr = rec1[w, I["mox"]][ok0] / rec0[j0[ok0], I["mox"]]
        if loop == 1:
            e_thr = np.max(np.abs(F / Fpc / ((1 + gt) * (1 + k1 * gt)) - 1.0)) if w.size else np.inf
            e_flow = np.max(np.abs(mr / (1 + gt[ok0]) - 1.0)) if mr.size else np.inf
            check("T10a Pc loop: thrust and flow per command", w.size > 50 and e_thr < 1e-3 and e_flow < 0.01,
                  f"{w.size} floor samples, g(t) {gt.min():.4f}-{gt.max():.4f}, k_cf(20 %) {k1:.4f}: max |F/F_pc / ((1+g)(1+k g)) - 1| "
                  f"{e_thr:.2e}, max |flow ratio / (1+g) - 1| {e_flow:.4f} ({mr.size} paired samples)")
        else:
            e_thr = np.max(np.abs(F / Fpc - 1.0)) if w.size else np.inf
            e_flow = np.max(np.abs(mr * (1 + k1 * gt[ok0]) - 1.0)) if mr.size else np.inf
            check("T10b compensated loop: thrust and flow per command", w.size > 50 and e_thr < 1e-9 and e_flow < 0.01,
                  f"{w.size} floor samples: max |F/F_pc - 1| {e_thr:.1e}, max |flow ratio x (1 + k g) - 1| {e_flow:.4f}")
        if loop == 1:
            th = rec1[:, I["thg"]]
            mono = bool(np.all(np.diff(th) >= -1e-15))
            ge = float(r1["throat_g_end"]); J = float(r1["throat_J"])
            law = abs(ge - g * min(1.0, J / jB)) < 1e-12
            check("T10c growth law", mono and law and abs(th[-1] - ge) < 1e-12,
                  f"g non-decreasing {mono}; g_end {ge:.6f} = g min(1, J/J_ref) {g * min(1.0, J / jB):.6f} (J {J:.4f}, J_ref {jB:.4f}); "
                  f"recorder end {th[-1]:.6f}")
    tg = json.load(open(f"{S}/throat_growth/throat_growth.json"))
    check("T10d J_ref reproduces the Monte Carlo value", tg["j_ref"]["B1"] == jB,
          f"J_ref B1 {jB!r} vs throat_growth.json {tg['j_ref']['B1']!r}")
    b27 = json.load(open(f"{S}/v27_checks/bitcheck_v27_vs_v26.json"))
    b26 = json.load(open(f"{S}/v27_checks/bitcheck_v26_vs_v25.json"))
    n27 = sum(v["values_compared"] for v in b27["cases"].values()); n26 = sum(v["values_compared"] for v in b26["cases"].values())
    check("T10e defaults bit-identical", b27["bit_identical"] and b26["bit_identical"] and "v2.7" in b26["sim"],
          f"vs v2.6 runs (iface_v3c): {b27['bit_identical']} ({n27} values, {len(b27['cases'])} cases); vs v2.5 runs (iface_v3a) "
          f"with {b26['sim']}: {b26['bit_identical']} ({n26} values)")


def t11(jB):
    r, rec, _ = fly(dict(B1, k_est_asc=2))
    t, ph, kh = rec[:, I["t"]], rec[:, I["phase"]], rec[:, I["keff"]]
    m = (t > 1.5) & (ph >= 1) & (ph <= 3)
    e = float(np.max(np.abs(kh[m] - 1.0)))
    check("T11a k_est_asc 2 unbiased on the nominal B1", e <= 0.01, f"max |k_hat - 1| {e:.4f} over {int(m.sum())} samples (t > 1.5 s, "
                                                                     "ascent / apex / floor)")
    r1, rec1, _ = fly(dict(B1, k_est_asc=2, throat_g=0.09, throat_jref=jB))
    w = floor_window(rec1)
    ktrue = rec1[w, I["F"]] / rec1[w, I["Fpc"]]
    e1 = float(np.max(np.abs(rec1[w, I["keff"]] / ktrue - 1.0))) if w.size else np.inf
    check("T11b k_est_asc 2 tracks the growth (g 0.09)", w.size > 50 and e1 <= 0.02,
          f"{w.size} floor samples: true k {ktrue.min():.4f}-{ktrue.max():.4f}, max |k_hat / k - 1| {e1:.4f}")
    q = 0.01 * 500.0
    ec = np.abs(rec1[w, I["Fcmd"]] - 100.0 / rec1[w, I["keff"]])
    eF = np.abs(rec1[w, I["F"]] / 100.0 - 1.0)
    check("T11c floor compensation", w.size > 50 and float(ec.max()) <= 0.5 * q + 0.5 and float(eF.max()) <= 0.03,
          f"max |F_cmd - 100 N / k_hat| {ec.max():.2f} N (half step {0.5 * q:.1f} N + 0.5 N deadband), delivered floor "
          f"{rec1[w, I['F']].min():.1f}-{rec1[w, I['F']].max():.1f} N")
    n = PC.nominal(dict(B1, k_est_asc=2, throat_g=0.11, throat_jref=jB), PC.M_TANK)
    dci = json.load(open(f"{S}/duty_cycles_v3/duty_cycles_index_v3.json"))
    # engine-on counter vs the envelope's counter (index rev b: burn_time_s = thrust-on; the counter is kept separately)
    env = dci.get("conservative_thermal_envelope_engine_on_counter_s", dci.get("conservative_thermal_envelope_burn_s"))
    check("T11d B1 85 m closes with g 0.11 and k_est_asc 2", n["closes"] and n["burn_time_s"] <= env,
          f"reserve {100 * n['reserve_frac']:.1f} % (rule 25 %), burn {n['burn_time_s']:.2f} s vs {env:.2f} s (engine-on "
          f"counters), apex {n['h_max']:.1f} m")
    r2, rec2, _ = fly(dict(B1, k_est_asc=1))
    m2 = (rec2[:, I["t"]] > 1.0) & (rec2[:, I["phase"]] >= 1) & (rec2[:, I["phase"]] <= 3)
    info("T11e rejected first form (k_est_asc 1)", f"no growth: k_hat min {rec2[m2, I['keff']].min():.3f} / max "
                                                    f"{rec2[m2, I['keff']].max():.3f} in ascent / floor (truth 1.000), apex "
                                                    f"{float(r2['h_max']):.1f} m vs {float(r['h_max']):.1f} m with option 2")


def t12():
    base_n = PC.nominal(dict(B1, k_est_asc=2), PC.M_TANK)
    rows = []
    cases = [("accel bias +0.05 m/s2", dict(disp=dict(a_b=(0.0, 0.0, 0.05))), lambda m, F: 0.05 * m / F),
             ("accel bias -0.05 m/s2", dict(disp=dict(a_b=(0.0, 0.0, -0.05))), lambda m, F: 0.05 * m / F),
             ("accel scale +0.5 %", dict(disp=dict(a_sf=0.005)), lambda m, F: 0.005),
             ("accel scale -0.5 %", dict(disp=dict(a_sf=-0.005)), lambda m, F: 0.005),
             ("truth CA_tf x 0.7", dict(kw=dict(aero_unc=dict(ca_tf=0.7))), None),
             ("truth CA_tf x 1.3", dict(kw=dict(aero_unc=dict(ca_tf=1.3))), None),
             ("truth k_retro 0.25", dict(kw=dict(aero_unc=dict(k_retro=0.25))), None),
             ("truth k_retro 0.75", dict(kw=dict(aero_unc=dict(k_retro=0.75))), None),
             ("wind 8 m/s steady", dict(kw=dict(wind=8.0, gust=False, seed=7, wind_dir=0.7)), None),
             ("wind 6 m/s + gusts seed 7", dict(kw=dict(wind=6.0, gust=True, seed=7, wind_dir=0.7)), None),
             ("wind 8 m/s + gusts seed 3", dict(kw=dict(wind=8.0, gust=True, seed=3, wind_dir=0.7)), None),
             ("wind 8 m/s + gusts seed 7", dict(kw=dict(wind=8.0, gust=True, seed=7, wind_dir=0.7)), None),
             ("thrust scale 0.95", dict(disp=dict(thrust_scale=0.95)), None),
             ("thrust scale 1.05", dict(disp=dict(thrust_scale=1.05)), None)]
    for lab, d, ana in cases:
        kw = d.get("kw", {})
        over = dict(B1, k_est_asc=2, **{k: v for k, v in kw.items() if k == "aero_unc"})
        r, rec, _ = fly(over, d.get("disp"), **{k: v for k, v in kw.items() if k != "aero_unc"})
        r0, rec0, _ = fly(dict(over, k_est_asc=0), d.get("disp"), **{k: v for k, v in kw.items() if k != "aero_unc"})
        w = floor_window(rec)
        kt = rec[w, I["F"]] / rec[w, I["Fpc"]]
        ke = float(np.mean(rec[w, I["keff"]] / kt - 1.0)) if w.size else float("nan")
        m_ = float(np.mean(rec[w, I["m"]])) if w.size else float("nan")
        an = ana(m_, 100.0) if ana else None
        p23 = (rec[:, I["phase"]] >= 2) & (rec[:, I["phase"]] <= 3)
        k23 = rec[p23, I["keff"]] / np.maximum(rec[p23, I["F"]] / np.maximum(rec[p23, I["Fpc"]], 1e-9), 1e-9)
        ok, ok0 = R.success(r), R.success(r0)
        rows.append(dict(case=lab, k_err_floor=ke, analytic=an, k_ratio_min_max_floor_ascent_descent=[float(k23.min()),
                                                                                                      float(k23.max())],
                         max_tilt_phase23_deg=float(np.max(rec[p23, I["tilt"]])), apex_m=float(r["h_max"]),
                         burn_s=float(r["burn_time"]), landed_ok=ok, td_vz=float(r["td_vz"]), td_vh=float(r["td_vh"]),
                         comparator_k0=dict(landed_ok=ok0, apex_m=float(r0["h_max"]), burn_s=float(r0["burn_time"]),
                                            td_vh=float(r0["td_vh"]), tipover=bool(r0["tipover"] > 0.5),
                                            max_tilt_phase23_deg=float(np.max(rec0[(rec0[:, I["phase"]] >= 2) &
                                                                                  (rec0[:, I["phase"]] <= 3), I["tilt"]])))))
        info(f"T12 {lab}", f"k_hat error on the floor {100 * ke:+.2f} %" + (f" (analytic {100 * an:.2f} %)" if an is not None else "")
             + f", k_hat / k_true {k23.min():.3f}-{k23.max():.3f} (phases 2-3, max tilt {rows[-1]['max_tilt_phase23_deg']:.1f} deg)"
             + f", apex {float(r['h_max']):.1f} m, burn {float(r['burn_time']):.2f} s, landed-ok {ok}, td_vh {float(r['td_vh']):.2f}"
             + f" | comparator k_est_asc 0: landed-ok {ok0}, apex {float(r0['h_max']):.1f} m, burn {float(r0['burn_time']):.2f} s, "
               f"td_vh {float(r0['td_vh']):.2f}, max tilt {rows[-1]['comparator_k0']['max_tilt_phase23_deg']:.1f} deg")
    lost = [x["case"] for x in rows if x["comparator_k0"]["landed_ok"] and not x["landed_ok"]]
    both = [x["case"] for x in rows if not x["comparator_k0"]["landed_ok"] and not x["landed_ok"]]
    gained = [x["case"] for x in rows if not x["comparator_k0"]["landed_ok"] and x["landed_ok"]]
    check("T12 k_est_asc 2 loses no perturbed flight the comparator lands", not lost,
          f"{len(rows)} perturbations; lost vs k_est_asc 0: {lost or 'none'}; both fail: {both or 'none'}; gained: "
          f"{gained or 'none'}; nominal apex {base_n['h_max']:.1f} m, burn {base_n['burn_time_s']:.2f} s")
    info("T12 low-thrust start", "not flown: the B start is a full-thrust step and the vehicle is airborne before the 1 s gate; on "
                                 "the pad the accelerometer reads the ground reaction (specific force = g whatever the thrust), so "
                                 "a slow start would bias the estimate: option 2 also requires h_est > 1 m (airborne gate, "
                                 "sim6 v2.7); the gate changes no Monte Carlo run (tg_B1_none_k2 and tg_B1_pc_k2 byte-identical)")
    return rows


def t13(jA):
    A1 = dict(PC.DC["A1"], t_ign_add=PC.MM.NCS["slots"] + TG.DT_RL, t_ign_est=R.DEF["t_ign_est"] + PC.MM.NCS["slots"] + TG.DT_RL)
    out = []
    for lab, ov in (("option 0", A1), ("option 2", dict(A1, k_est_asc=2)), ("option 0, g 0.11", dict(A1, throat_g=0.11, throat_jref=jA)),
                    ("option 2, g 0.11", dict(A1, k_est_asc=2, throat_g=0.11, throat_jref=jA))):
        r, rec, _ = fly(ov)
        m = (rec[:, I["phase"]] >= 5) & (rec[:, I["phase"]] <= 6) & (rec[:, I["F"]] > 75.0)
        kt = rec[m, I["F"]] / np.maximum(rec[m, I["Fpc"]], 1e-9)
        out.append(f"{lab}: k_hat {rec[m, I['keff']].min():.3f}-{rec[m, I['keff']].max():.3f} (true {kt.min():.3f}-{kt.max():.3f}), "
                   f"landed-ok {R.success(r)}, td_vz {float(r['td_vz']):.2f}")
    info("T13 A1 landing-burn estimator", "; ".join(out))


if __name__ == "__main__":
    jB, _ = TG.j_ref(B1)
    A1_ = dict(PC.DC["A1"], t_ign_add=PC.MM.NCS["slots"] + TG.DT_RL, t_ign_est=R.DEF["t_ign_est"] + PC.MM.NCS["slots"] + TG.DT_RL)
    jA, _ = TG.j_ref(A1_)
    t10(jB)
    t11(jB)
    rows12 = t12()
    t13(jA)
    print(f"{len(FAIL)} failures", FAIL)
    out = os.environ.get("GNC_V27_OUT", f"{S}/v27_checks")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "v27_tests.json"), "w") as f:
        json.dump(dict(version="m2_v27_tests v1.1", sim=s6.SIM6_VERSION, iface=os.environ.get("GNC_IFACE"), n_fail=len(FAIL),
                       failures=FAIL, n_info=sum(1 for x in LOG if x["result"] == "INFO"), checks=LOG, t12_rows=rows12),
                  f, indent=1, default=float)
    sys.exit(len(FAIL))
