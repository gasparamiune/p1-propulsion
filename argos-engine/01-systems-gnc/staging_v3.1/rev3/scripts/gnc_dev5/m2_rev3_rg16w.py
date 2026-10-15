"""m2_rev3_rg16w v1.0 (GNC rev3, 2026-10-13): P5 - RG-16 under the PROVISIONAL detection-latency allowance (LEAD CHANGELOG
line 181 (3): 0.5 s from the onset of the 670 N plateau, strict windowed form, no window-gain credit): the windowed miss-side
budget at the FC_THRUST detector output for A1 (GNC re-implementation of the REV-GNC-3 reviewer method, which must reproduce
the reviewer's 2.973 % / 4.015 %) and for B1 (new: B1 comparator, B1 mass terms, no purge), and the sensitivity of that budget
to non-white vibration (ASSUMED spectra; no measured spectrum exists).

Flights: A1 H_cal_comp_path / H_cal_path = m2_rg16_fct_terms v2.1 cases (decided path, FSW-R2 release rule, purge G73), B1
H_cal_comp / H_cal = m2_mass_est v2 FCT cases on the m2_fc_thrust B1 configuration (no purge); 200 runs each, seed-101 draws,
the same reconstruction RNG streams as the stored comparators (per-run statistics must reproduce them exactly).
Detector stream (m2_fc_thrust v1.1): estimate F_acc = m_hat f_z + D_model (comp: lever-arm / direction compensation),
first-order 20 ms filter, 100 Hz frames at the run's random phase, 0.1 N steps; ft = truth through the same filter and frames;
selection = FC window past the 0.1 s guard with F_true > 300 N.
Statistics (relative error r = fa / ft - 1): D0 single frame; H1 held output = minimum of r over 3 consecutive selected
frames; MW = maximum of H1 over W consecutive frames (the sustained fault is detected within W iff 670 (1 + MW) > 650).
Budget (author convention, m2_rg16_fct_terms v2.1 side_budget, reviewer's detector-output form): s = (p50 - p1) / 2.326 of the
statistic; total = 3 hypot(s, s_mass) + bias; bias = mass-estimate bias bound + purge term + |median b_sys|; passes iff
670 (1 - total) > 650 (allowed 2.985 %). STRICT WINDOWED FORM = MW over W = 500 ms, no credit for the median shift of the
windowed statistic (the window gain). B1 terms: mest_budget_v1 base tgl_B1_lead62_pc_k2 fc line (random 1 sigma, bias
bound), purge term 0 (B1 has no purge), b_sys median of the stored B1 comparator.
Vibration sensitivity (ASSUMED): the accelerometer error per 1 ms sample is sensor white noise a_vrw / sqrt(dt) plus the
thrust-proportional vibration vib_sigma F / Fmax. Baseline (white, the flown model): one common white sample scales both terms
(identical to m2_mass_est v2). Variants keep the sensor term white and replace the vibration sample by: AR(1) (first-order
Gauss-Markov) with correlation time 5 / 20 / 100 ms built from the same white sequence, or a single tone at 10 / 30 Hz
(random phase per run); (a) at the SAME VIBRATION RMS (the spectrum moves energy into the detector band), (b) suffix _fr,
scaled to the SAME FRAME-LEVEL vibration RMS after the 20 ms filter as the white model (closed-form gain; only the
correlation shape changes). Strict total = 3 hypot(s, s_mass) + bias + max(0, shift), shift = single-frame median minus the
windowed median (an adverse shift is charged, a favourable one is not credited; for the flown white model the shift is
favourable and the strict total equals the reviewer's figure). A real spectrum is TO-VERIFY (Electronics / Mechanical: IMU mount, static
fire or CF accelerometer record).
SIM / DERIVED on ASSUMED noise models; no hardware data; not a physical approval.
Env: m2r3_env.sh; GNC_RG16W_OUT (out/rev3/rg16w); GNC_RG16W_PARTS (fly,eval).
Output: <out>/rg16w_<prof>_<case>.npz (frame streams), <out>/rg16w.json."""
import hashlib
import json
import os
import sys
import time
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view as swv
from scipy.signal import lfilter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_rg16_fct_terms_v2 as RG  # noqa: E402
import m2_fc_thrust as FT  # noqa: E402
from gncsim import run6 as R, sim6 as s6  # noqa: E402

VERSION = "m2_rev3_rg16w v1.0"
S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_RG16W_OUT", f"{S}/rev3/rg16w")
PARTS = os.environ.get("GNC_RG16W_PARTS", "fly,eval").split(",")
MV = RG.MV
I, PN = MV.I, MV.PN
Z = 2.326
ALLOW = 1.0 - 650.0 / 670.0
WS = (5, 10, 20, 30, 50, 100)
W_STRICT = 50
CASES = {  # (prof, case): stored comparator json (per-run statistics to reproduce)
    ("A1", "H_cal_comp_path"): f"{S}/rev2/rg16_v2/fct2_A1_H_cal_comp_path.json",
    ("A1", "H_cal_path"): f"{S}/rev2/rg16_v2/fct2_A1_H_cal_path.json",
    ("B1", "H_cal_comp"): f"{S}/mass_est_v2/fct2_B1_H_cal_comp.json",
    ("B1", "H_cal"): f"{S}/mass_est_v2/fct2_B1_H_cal.json",
}
VIB = {"white": None, "ar5ms": ("ar", 0.005, 0), "ar20ms": ("ar", 0.020, 0), "ar100ms": ("ar", 0.100, 0),
       "tone10Hz": ("tone", 10.0, 0), "tone30Hz": ("tone", 30.0, 0),
       "ar5ms_fr": ("ar", 0.005, 1), "ar20ms_fr": ("ar", 0.020, 1), "ar100ms_fr": ("ar", 0.100, 1),
       "tone10Hz_fr": ("tone", 10.0, 1), "tone30Hz_fr": ("tone", 30.0, 1)}
TAU_F = 0.020


def frame_norm(model):
    """1 / (filtered RMS of the model's unit-variance vibration sample / filtered RMS of a white one) for the 20 ms first-order
    filter at 1 ms (FT.lp: y_k = c y_k-1 + b x_k, b = dt / (tau + dt), c = 1 - b). AR(1) pole a: variance ratio
    (1 + a c) / (1 - a c); tone at f: |H(f)|^2 / (b / (2 - b))."""
    b = FT.DT / (TAU_F + FT.DT)
    c = 1.0 - b
    if model[0] == "ar":
        a = float(np.exp(-FT.DT / model[1]))
        ratio = (1.0 + a * c) / (1.0 - a * c)
    else:
        th = 2.0 * np.pi * model[1] * FT.DT
        h2 = b * b / (1.0 - 2.0 * c * np.cos(th) + c * c)
        ratio = h2 / (b / (2.0 - b))
    return 1.0 / float(np.sqrt(ratio))
RG16_V2 = f"{S}/rev2/rg16_v2/rg16_fct_terms_v2.json"
MBUD = f"{S}/mass_est_v2/mest_budget_v1.json"
B1_MBASE = "tgl_B1_lead62_pc_k2"


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def spec_of(prof, case):
    if prof == "A1":
        return RG.cases()[("A1", case)][1], RG.run_cfg_case_bias
    return dict(MV.FCT_CASES[case]), MV.run_cfg_case


def recon(par, rec, w, prof, comp, model, ph):
    """m2_mass_est v2 reconstruct_flown with the vibration sample replaced per model (None = the flown white model)."""
    F = rec[:, I["F"]]
    Fmax = par[PN["Fmax"]]
    rz = par[PN["z_imu"]] - rec[:, I["zcg"]]
    lev = (rec[:, I["wx"]] ** 2 + rec[:, I["wy"]] ** 2) * rz
    fimu = rec[:, I["fax"]] - lev
    vib = np.where(F > 1.0, par[PN["vib_sigma"]] * F / Fmax, 0.0)
    fm = fimu * (1.0 + par[PN["a_sf"]]) + par[PN["a_bz"]]
    if model is None:
        fm = fm + (par[PN["a_vrw"]] / np.sqrt(FT.DT) + vib) * w
    else:
        if model[0] == "ar":
            a = float(np.exp(-FT.DT / model[1]))
            b = float(np.sqrt(1.0 - a * a))
            x, _ = lfilter([b], [1.0, -a], w, zi=[w[0] * (1.0 - b)])
        else:
            t = rec[:, I["t"]]
            x = np.sqrt(2.0) * np.sin(2.0 * np.pi * model[1] * t + ph)
        if model[2]:
            x = x * frame_norm(model)
        fm = fm + (par[PN["a_vrw"]] / np.sqrt(FT.DT)) * w + vib * x
    m_hat = rec[:, I["mex"]] * (1.0 + rec[:, I["mhe"]])
    vze = rec[:, I["vze"]]
    cda = np.where(vze > 0.0, par[PN["kest_cda_nf"]], par[PN["drag_cda_nom"]]) + np.where(FT.legs_state(par, rec, prof),
                                                                                          par[PN["kest_cda_legs"]], 0.0)
    dd = 0.5 * 1.2 * cda * vze * vze
    cd = np.ones(len(F))
    if comp:
        fm = fm + lev
        cd = np.cos(np.radians(rec[:, I["dgx"]])) * np.cos(np.radians(rec[:, I["dgy"]]))
    return (fm * m_hat + np.where(vze > 0.0, dd, -dd)) / cd


def part_fly():
    os.makedirs(OUT, exist_ok=True)
    C, _ = FT.cfgs()
    for (prof, case), pst in CASES.items():
        p = os.path.join(OUT, f"rg16w_{prof}_{case}.npz")
        if os.path.exists(p) and os.environ.get("GNC_RG16W_FORCE") != "1":
            print("exists", prof, case, flush=True)
            continue
        t0 = time.time()
        stored = json.load(open(pst))
        spec, rcc = spec_of(prof, case)
        cfg = C[prof]
        D = R.draw(np.random.default_rng(101), 500, cfg)
        arrs, chk, pooled = {}, [], []
        for i in range(MV.NFCT):
            c, disp = rcc(cfg, D[i], spec, i, "fct")
            c = dict(c, rec_dt=FT.DT)
            par = R.build(c, disp)[0]
            res, rec, _ = R.fly(c, disp, nrec=100000)
            rng = np.random.default_rng(20261019 + i + (0 if case.startswith("H") else 100000) + (0 if prof == "A1" else 200000))
            w = rng.standard_normal(len(rec))
            p0 = int(rng.integers(0, FT.KF))
            ph = float(np.random.default_rng(20261101 + i + (0 if prof == "A1" else 200000)).uniform(0.0, 2.0 * np.pi))
            air, fc, lit, drog = FT.windows(par, res, rec, prof)
            ft = FT.filt(rec[:, I["F"]], 0.020)[p0::FT.KF]
            fw = fc[p0::FT.KF]
            fs = (fc & (FT.open_time(fc) >= FT.GUARD))[p0::FT.KF]
            sel = fs & (ft > 300.0)
            comp = spec.get("comp", 0)
            ks = np.where(sel)[0]
            k0, k1 = (max(int(ks[0]) - 2, 0), int(ks[-1]) + 1) if len(ks) else (0, 0)   # stored slice: the selected span
            for vk, model in VIB.items():
                Fr = recon(par, rec, w, prof, comp, model, ph)
                fa = np.round(FT.filt(Fr, 0.020)[p0::FT.KF] * 10.0) / 10.0
                arrs[f"fa_{vk}_{i}"] = fa[k0:k1] if vk == "white" else fa[k0:k1].astype(np.float32)
                if vk == "white":
                    hm, kh = FT.held_max(fa, fw)
                    eps = fa[sel] / ft[sel] - 1.0
                    pooled.append(eps.astype(np.float32))
                    r_ = stored["runs"][i]
                    chk.append(dict(run=i, held_max=(float(hm), r_["held_max_fc_N"]), n=(int(sel.sum()), r_["n_frames"]),
                                    eps_min=(float(eps.min()) if len(eps) else None, r_["eps_min"]),
                                    eps_p01=(float(np.percentile(eps, 1)) if len(eps) else None, r_["eps_p01"]),
                                    eps_med=(float(np.median(eps)) if len(eps) else None, r_["eps_med"])))
            arrs[f"ft_{i}"] = ft[k0:k1]
            arrs[f"sel_{i}"] = sel[k0:k1]
        allx = np.concatenate(pooled)
        qv = [float(np.percentile(allx, q)) for q in MV.EPS_Q]
        bad = [c_ for c_ in chk if any(a != b for a, b in (c_["held_max"], c_["n"], c_["eps_min"], c_["eps_p01"], c_["eps_med"]))]
        repro = dict(pooled_quantiles=qv, stored_quantiles=stored["eps_pooled"]["values"],
                     pooled_quantiles_identical=qv == stored["eps_pooled"]["values"], n_frames=int(len(allx)),
                     stored_n_frames=stored["eps_pooled"]["n_frames"], per_run_mismatches=len(bad), first_mismatches=bad[:3],
                     stored=dict(path=pst, sha256_16=sha16(pst), sim=stored.get("sim")), sim=s6.SIM6_VERSION,
                     sim6_sha16=sha16(s6.__file__), run6_sha16=sha16(R.__file__), cpu_s=time.time() - t0)
        np.savez_compressed(p, repro=np.array(json.dumps(repro)), **arrs)
        print(f"{prof}|{case}: identical quantiles {repro['pooled_quantiles_identical']} per-run mismatches {len(bad)} "
              f"({time.time() - t0:.0f} s)", flush=True)


def stats(case_npz, vk, s_mass, bias, bias_lin):
    z = np.load(case_npz)
    n = len([k for k in z.files if k.startswith("ft_")])
    E, H1, MW = [], [], {w: [] for w in WS}
    seg_len = []
    for i in range(n):
        fa, ft, sel = z[f"fa_{vk}_{i}"].astype(np.float64), z[f"ft_{i}"], z[f"sel_{i}"]
        r = np.full(len(fa), np.nan)
        ok = ft > 1.0
        r[ok] = fa[ok] / ft[ok] - 1.0
        E.append(r[sel])
        if len(fa) < 3:
            continue
        s3 = swv(sel, 3).all(axis=1)
        e1 = swv(np.where(np.isnan(r), np.inf, r), 3).min(axis=1)
        H1.append(e1[s3])
        # contiguous selected segments (frames) of the run
        d_ = np.diff(np.concatenate([[0], sel.astype(int), [0]]))
        seg_len += list(np.where(d_ == -1)[0] - np.where(d_ == 1)[0])
        for w in WS:
            if len(e1) < w:
                continue
            full = swv(s3, w).all(axis=1)
            mx = swv(np.where(s3, e1, -np.inf), w).max(axis=1)
            MW[w].append(mx[full])
    E = np.concatenate(E)
    p50E = float(np.percentile(E, 50))

    def line(x, label):
        if x.size == 0:
            return dict(label=label, n=0, computable=False)
        p1, p50 = float(np.percentile(x, 1)), float(np.percentile(x, 50))
        s = (p50 - p1) / Z
        tot = 3.0 * float(np.hypot(s, s_mass)) + bias
        sh = p50E - p50
        st_ = tot + max(0.0, sh)
        return dict(label=label, n=int(x.size), p1=p1, p50=p50, s_1sigma=s, total=tot, passes=bool(670.0 * (1.0 - tot) > 650.0),
                    strict_total=st_, strict_passes=bool(670.0 * (1.0 - st_) > 650.0), strict_margin_pct_points=100.0 * (ALLOW - st_),
                    margin_pct_points=100.0 * (ALLOW - tot), median_shift_vs_single_frame=sh, total_with_shift_credit=tot + sh,
                    share_below_allow=float(np.mean(x <= -ALLOW)), share_below_allow_after_bias=float(np.mean(x - bias_lin <= -ALLOW)))
    out = dict(single_frame=line(E, "D0 single frame"), held_inst=line(np.concatenate(H1) if H1 else np.zeros(0), "D1 held output (min of 3 frames)"),
               windowed={f"W{w}_{w * 10}ms": line(np.concatenate(MW[w]) if MW[w] else np.zeros(0), f"D2 max of held output over {w * 10} ms")
                         for w in WS},
               selected_segments_frames=dict(n=len(seg_len), p50=float(np.median(seg_len)) if seg_len else None,
                                             max=int(max(seg_len)) if seg_len else None,
                                             share_ge_52=float(np.mean(np.array(seg_len) >= W_STRICT + 2)) if seg_len else None))
    out["strict_windowed_500ms"] = out["windowed"][f"W{W_STRICT}_{W_STRICT * 10}ms"]
    return out


def part_eval():
    rv2 = json.load(open(RG16_V2))
    mb = json.load(open(MBUD))
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, method=__doc__.split("\n\n")[1].strip(),
               allowed_total=ALLOW, sources=dict(rg16_fct_terms_v2=dict(path=RG16_V2, sha256_16=sha16(RG16_V2)),
                                                 mest_budget_v1=dict(path=MBUD, sha256_16=sha16(MBUD))),
               reviewer_reference=dict(H_cal_comp_path=0.02973, H_cal_path=0.04015,
                                       source="reviews/gnc/rev2/logs/rv_rg16_budget.out (REV-GNC-3; W = 500 ms totals)"),
               cases={})
    for (prof, case), pst in CASES.items():
        p = os.path.join(OUT, f"rg16w_{prof}_{case}.npz")
        if not os.path.exists(p):
            continue
        z = np.load(p)
        repro = json.loads(str(z["repro"]))
        stored = json.load(open(pst))
        if prof == "A1":
            b = rv2["budget"][case]["miss_side"]
            s_mass, bias = b["mass_1sigma"], b["bias_sum"]
            bias_lin = b["purge_term"] + rv2["mass_budget_A1_fc"]["bias_linear_bound"]
            terms = dict(s_mass=s_mass, bias=bias, purge_term=b["purge_term"],
                         mass_bias_bound=rv2["mass_budget_A1_fc"]["bias_linear_bound"],
                         b_sys_median=bias - b["purge_term"] - rv2["mass_budget_A1_fc"]["bias_linear_bound"],
                         source=f"rg16_fct_terms_v2.json budget.{case}.miss_side (rev2)")
        else:
            fc = mb["bases"][B1_MBASE]["line"]["fc"]
            bsys = abs(float(stored["b_sys_at_onsets"]["values"][3]))
            s_mass = fc["random_rss_1sigma"]
            bias = fc["bias_linear_bound"] + 0.0 + bsys
            bias_lin = fc["bias_linear_bound"]
            terms = dict(s_mass=s_mass, bias=bias, purge_term=0.0, mass_bias_bound=fc["bias_linear_bound"], b_sys_median=bsys,
                         source=f"mest_budget_v1.json bases.{B1_MBASE}.line.fc (ASSUMED to apply to the m2_fc_thrust B1 "
                                f"configuration); b_sys median of {os.path.basename(pst)}; purge 0 (B1 has no purge)")
        e = dict(reproduction=repro, terms=terms, frame_norm={k: (frame_norm(m) if m and m[2] else 1.0) for k, m in VIB.items()}, vib={})
        for vk in VIB:
            e["vib"][vk] = stats(p, vk, s_mass, bias, bias_lin)
        out["cases"][f"{prof}|{case}"] = e
    pj = os.path.join(OUT, "rg16w.json")
    json.dump(out, open(pj, "w"), indent=1, default=float)
    print("wrote", pj, sha16(pj))
    for k, e in out["cases"].items():
        rp = e["reproduction"]
        print(f"== {k}: reproduction quantiles {rp['pooled_quantiles_identical']} mismatches {rp['per_run_mismatches']} | "
              f"s_mass {100 * e['terms']['s_mass']:.3f} % bias {100 * e['terms']['bias']:.3f} %")
        for vk, st in e["vib"].items():
            L = st["strict_windowed_500ms"]
            H = st["held_inst"]
            seg = st["selected_segments_frames"]
            if L.get("computable", True):
                print(f"   {vk:11s} W500 n {L['n']:6d} p1 {100 * L['p1']:+.3f} p50 {100 * L['p50']:+.3f} s {100 * L['s_1sigma']:.3f} "
                      f"total {100 * L['total']:.3f} % strict {100 * L['strict_total']:.3f} % {'PASS' if L['strict_passes'] else 'FAIL'} "
                      f"(strict margin {L['strict_margin_pct_points']:+.3f} pp; "
                      f"with shift credit {100 * L['total_with_shift_credit']:.3f}) | held-inst total {100 * H['total']:.3f} % | "
                      f"segments p50 {seg['p50']} max {seg['max']} share>=52 {seg['share_ge_52']:.2f}")
            else:
                print(f"   {vk:9s} W500 not computable (no 500 ms window inside the selection)")


if __name__ == "__main__":
    if "fly" in PARTS:
        part_fly()
    if "eval" in PARTS:
        part_eval()
