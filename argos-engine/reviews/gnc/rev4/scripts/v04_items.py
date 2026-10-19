"""REV-GNC-6 v04: reviewer checks of rev4 items [11] landing mass, [13] RE-24, [14](b) frame-noise estimate, [15] payload
and the RV5-06 withdrawn-value sidecars, from the STAGED tables / JSON only (no author evaluation code is imported).
 [11] P(80 g) by touchdown-mass bin on the P2 h210 tables (N=1000 per main base, both states), Fisher exact test of
      >= 16.15 kg vs below, what drives the dispersed touchdown mass (correlations, least squares), and the PAIRED payload
      arms (same seed, same draw) that change the nominal touchdown mass.
 [13] the undetected-jam population of the RE-24 abort arms: run ids across servo arms / bases, time-to-go at the jam,
      excursion, monitor metric; detected-jam counts; mon2 false aborts; rec0 vs P2 table column equality.
 [14](b) Monte Carlo of the window maximum of the 3-frame running minimum of iid N(0, 5 N) frame noise on a flat signal
      (the author's stated assumptions) over 50 and 80 frames, and on a single-peak signal.
 [15] every payload arm vs the v3d reference and vs P2 h210 (pooled main bases, line-208 statistics), the full sim6
      failure-criterion breakdown, burn time, throat growth, touchdown mass; bands under the strict line-208 rule (every
      lower FLOWN band, including the N=250 screens) and with the author's 180 m floor.
 RV5-06: target sha256 of every sidecar against the staged rev3 file; leaf-path coverage of the withdrawn sets W1 (rh220 /
      rh250) and W2 (lit_k*, gap_N, T_mid_N) by an independent JSON walk; withdrawn tokens in the v3.2 proposal texts.
SIM tables -> DERIVED.  Usage: python -I v04_items.py <out.json>"""
import csv, gzip, hashlib, json, math, os, re, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import rv6lib as L

OUT = sys.argv[1]
R4O = f"{L.R4}/out_rev4"
res = dict(script="v04_items (REV-GNC-6)", tag="DERIVED from staged SIM tables / JSON; [14](b) is a reviewer Monte Carlo on ASSUMED noise")


def f(r, k):
    return float(r[k])


def ok80(r, onset=80.0):
    return f(r, "ok") > 0.5 and 1e3 * f(r, "liq_left") >= onset


def fisher2(a, b, c, d):
    """two-sided Fisher exact p for [[a, b], [c, d]] (sum of tables with prob <= observed)."""
    r1, r2, c1, n = a + b, c + d, a + c, a + b + c + d
    def pr(x):
        return math.comb(r1, x) * math.comb(r2, c1 - x) / math.comb(n, c1)
    p0 = pr(a)
    lo, hi = max(0, c1 - r2), min(r1, c1)
    return min(1.0, sum(pr(x) for x in range(lo, hi + 1) if pr(x) <= p0 * (1 + 1e-9)))


def pct(xs, p):
    return round(float(L.q(list(xs), p)), 4)


# ------------------------------------------------------------------------------------------------ [11] landing mass
lm = {}
BINS = [(0, 15.0), (15.0, 15.5), (15.5, 16.0), (16.0, 16.15), (16.15, 16.5), (16.5, 17.0), (17.0, 99)]
for b in L.MAIN:
    for st in ("liq", "pw"):
        rows = L.rows_of(L.case_files(b, st, "v351", 210))
        m = np.array([f(r, "m_land") for r in rows])
        o = np.array([ok80(r) for r in rows])
        ll = np.array([f(r, "liq_left") for r in rows])
        e = dict(n=len(rows), m_land=dict(min=round(m.min(), 3), p01=pct(m, 1), p50=pct(m, 50), p99=pct(m, 99), max=round(m.max(), 3)))
        e["bins"] = []
        for lo, hi in BINS:
            k = (m >= lo) & (m < hi)
            e["bins"].append(dict(bin=f"[{lo},{hi})", n=int(k.sum()), P80=(round(float(o[k].mean()), 4) if k.any() else None),
                                  fails=int((~o[k]).sum()), liq_left_p50_g=(round(1e3 * float(np.median(ll[k])), 1) if k.any() else None)))
        hi_ = m >= 16.15
        a_, b_, c_, d_ = int((o & hi_).sum()), int((~o & hi_).sum()), int((o & ~hi_).sum()), int((~o & ~hi_).sum())
        e["ge16p15_vs_lt"] = dict(ok_hi=a_, fail_hi=b_, ok_lo=c_, fail_lo=d_, P_hi=round(a_ / (a_ + b_), 4), P_lo=round(c_ / (c_ + d_), 4),
                                  fisher_p=float(f"{fisher2(a_, b_, c_, d_):.4g}"))
        # drivers of the dispersed touchdown mass
        X = {k: np.array([f(r, k) for r in rows]) for k in ("dry_scale", "liq_left", "fuel_left", "prop_used", "m_est_err", "thrust_scale", "isp_scale")}
        e["corr_m_land"] = {k: round(float(np.corrcoef(m, v)[0, 1]), 3) for k, v in X.items() if np.std(v) > 0}
        A = np.column_stack([np.ones(len(m)), X["dry_scale"], X["liq_left"], X["fuel_left"]])
        coef, *_ = np.linalg.lstsq(A, m, rcond=None)
        pred = A @ coef
        e["ls_m_land_on_dry_scale_liq_left_fuel_left"] = dict(coef=[round(float(c), 4) for c in coef],
                                                             R2=round(float(1 - np.var(m - pred) / np.var(m)), 4))
        # dry-mass part only: touchdown mass with liq_left and fuel_left removed
        md = m - X["liq_left"] - X["fuel_left"]
        e["m_land_minus_propellant_left"] = dict(p01=pct(md, 1), p50=pct(md, 50), p99=pct(md, 99), corr_dry_scale=round(float(np.corrcoef(md, X["dry_scale"])[0, 1]), 3))
        k = md >= np.percentile(md, 57.4)
        e["P80_by_dry_part_top_42pct_vs_rest"] = [round(float(o[k].mean()), 4), round(float(o[~k].mean()), 4), int(k.sum())]
        a2, b2, c2, d2 = int((o & k).sum()), int((~o & k).sum()), int((o & ~k).sum()), int((~o & ~k).sum())
        e["P80_by_dry_part_fisher_p"] = float(f"{fisher2(a2, b2, c2, d2):.4g}")
        lm[f"{b}|{st}"] = e
res["landing_mass_h210"] = lm

# ------------------------------------------------------------------------------------------------ [15] payload tables
PT5 = f"{R4O}/payload_n500/tables"
PT2 = f"{R4O}/payload/tables"
pat = re.compile(r"rf_(A1J?_[a-z]+)_liq_G73_v351_pl([0-9.]+)_tz58_h(\d+)(?:_m([0-9.]+))?_n(\d+)\.csv\.gz")
arms = defaultdict(dict)
for d_ in (PT5, PT2):
    for fn_ in sorted(os.listdir(d_)):
        mm = pat.fullmatch(fn_)
        if not mm:
            continue
        b, pl, h, mn, n = mm.groups()
        key = f"pl{pl}|h{h}|m{mn or '2.00'}|n{n}"
        arms[key][b] = os.path.join(d_, fn_)
ref_all = {b: L.rows_of(L.ref_files(b, "liq")) for b in L.MAIN}
p2_all = {b: L.rows_of(L.case_files(b, "liq", "v351", 210)) for b in L.MAIN}


def paired(case_rows_by_base, comp_rows_by_base):
    prs = []
    for b in L.MAIN:
        c = case_rows_by_base[b]
        n = len(c)
        oc = {int(f(r, "run")): ok80(r) for r in c}
        orf = {int(f(r, "run")): ok80(r) for r in comp_rows_by_base[b] if int(f(r, "run")) < n}
        prs.append(L.counts(orf, oc))
    return L.stats(*L.pooled_counts(prs))


def fail_breakdown(rows):
    c = Counter()
    unexpl = 0
    for r in rows:
        if ok80(r):
            continue
        modes = []
        if f(r, "landed") < 0.5: modes.append("not_landed")
        if f(r, "crash") > 0.5: modes.append("crash")
        if f(r, "exhausted") > 0.5: modes.append("exhausted")
        if f(r, "tipover") > 0.5: modes.append("tipover")
        if abs(f(r, "td_vz")) > 2.0: modes.append("vz>2")
        if f(r, "td_vh") > 0.5: modes.append("vh>0.5")
        if f(r, "td_tilt") > 5.0: modes.append("tilt>5")
        if f(r, "td_rate") > 10.0: modes.append("rate>10")
        if f(r, "ok") > 0.5 and 1e3 * f(r, "liq_left") < 80: modes.append("below_80g")
        for x in modes:
            c[x] += 1
        if not set(modes) & {"vh>0.5", "tilt>5", "exhausted", "tipover", "crash", "vz>2", "below_80g"}:
            unexpl += 1
        c["n_fail"] += 1
    c["fails_not_in_author_mode_list"] = unexpl
    return dict(c)


pay = {}
for key, fb in sorted(arms.items()):
    if set(fb) != set(L.MAIN):
        continue
    case = {b: L.read(fb[b]) for b in L.MAIN}
    e = dict(files={b: [os.path.basename(fb[b]), L.sha16(fb[b])] for b in L.MAIN}, n_per_base=len(case["A1_none"]))
    e["vs_v3d_ref"] = paired(case, ref_all)
    e["vs_P2_v351_h210"] = paired(case, p2_all)
    e["rule_pass_vs_ref"] = L.rule_pass(e["vs_v3d_ref"])
    for b in L.MAIN:
        rows = case[b]
        bt = [f(r, "burn_time") for r in rows]
        e[b] = dict(P80=round(float(np.mean([ok80(r) for r in rows])), 4), fail=fail_breakdown(rows),
                    m_land_p50=pct([f(r, "m_land") for r in rows], 50), liq_left_p01_g=pct([1e3 * f(r, "liq_left") for r in rows], 1),
                    liq_left_p50_g=pct([1e3 * f(r, "liq_left") for r in rows], 50),
                    burn_time=dict(p50=pct(bt, 50), p99=pct(bt, 99), max=round(max(bt), 3)),
                    throat_g_end_p99=pct([f(r, "throat_g_end") for r in rows], 99),
                    max_tilt_land_p99=pct([f(r, "max_tilt_land") for r in rows], 99),
                    h_ign_p01=pct([f(r, "h_ign") for r in rows], 1), m_n2o=rows[0]["m_n2o"])
    pay[key] = e
# paired payload-to-payload comparisons (same seed and run index; the case-to-case pairing the author did not report)
def rows_key(k):
    return {b: L.read(arms[k][b]) for b in L.MAIN}
pp = {}
for a_, c_ in (("pl0|h210|m2.00|n500", "pl0.5|h210|m2.00|n500"), ("pl0|h210|m2.00|n500", "pl0.5|h190|m2.00|n500"),
               ("pl0|h210|m2.00|n500", "pl1|h210|m2.20|n500"), ("pl0|h210|m2.00|n500", "pl2|h210|m2.45|n500"),
               ("pl0|h210|m2.00|n500", "pl2|h210|m2.55|n500"), ("pl0|h210|m2.00|n500", "pl1|h210|m2.00|n500")):
    if a_ in arms and c_ in arms:
        pp[f"{c_} vs {a_}"] = paired(rows_key(c_), rows_key(a_))
# P2 (tank at 0.55 m) vs pl0 (tank moved to 0.58 m), runs 0-499
pp["pl0|h210 (tank 0.58) vs P2 v351 h210 (tank 0.55)"] = paired(rows_key("pl0|h210|m2.00|n500"), p2_all)
# bands: strict line-208 (every lower flown band) and the 180 m floor, per payload, using the largest N flown at each h
bands = {}
for pl in ("0", "0.5", "1", "2", "3"):
    hs = {}
    for key, e in pay.items():
        p_, h_, m_, n_ = key.split("|")
        if p_ != f"pl{pl}" or m_ != "m2.00":
            continue
        h = int(h_[1:]); n = int(n_[1:])
        if h not in hs or n > hs[h][0]:
            hs[h] = (n, e["vs_v3d_ref"], L.rule_pass(e["vs_v3d_ref"]))
    hs_sorted = sorted(hs)
    strict = None
    for h in hs_sorted:
        if all(hs[x][2] for x in hs_sorted if x <= h):
            strict = h
    floor180 = None
    for h in [x for x in hs_sorted if x >= 180]:
        if all(hs[x][2] for x in hs_sorted if 180 <= x <= h):
            floor180 = h
    bands[f"pl{pl}"] = dict(flown={h: dict(n_per_base=hs[h][0], lost=hs[h][1]["lost"], gained=hs[h][1]["gained"], p=hs[h][1]["p"],
                                           ub95_pp=hs[h][1]["ub95_pp"], passes=hs[h][2]) for h in hs_sorted},
                            band_strict_every_lower_flown=strict, band_floor_180=floor180)
# author's JSON values for the same arms
auth = {}
for nm, p in (("n500", f"{R4O}/payload_n500/payload_rev4.json"), ("n250", f"{R4O}/payload/payload_rev4.json")):
    d = json.load(open(p))
    for k, v in d["mc"]["arms"].items():
        auth[f"{nm}|{k}"] = dict(vs_ref=v.get("vs_v3d_ref_l208"), vs_P2=v.get("vs_P2_v351_h210"))
cmp_ = {}
for key, e in pay.items():
    p_, h_, m_, n_ = key.split("|")
    ak = f"{n_}|liq|G73|v351|{p_}|tz58|{h_}" + ("" if m_ == "m2.00" else f"|{m_}")
    a = auth.get(ak)
    if a and a["vs_ref"]:
        cmp_[key] = dict(author=[a["vs_ref"]["lost"], a["vs_ref"]["gained"], a["vs_ref"]["ub95_pp"]],
                         mine=[e["vs_v3d_ref"]["lost"], e["vs_v3d_ref"]["gained"], e["vs_v3d_ref"]["ub95_pp"]],
                         equal=(a["vs_ref"]["lost"] == e["vs_v3d_ref"]["lost"] and a["vs_ref"]["gained"] == e["vs_v3d_ref"]["gained"]
                                and abs(a["vs_ref"]["ub95_pp"] - e["vs_v3d_ref"]["ub95_pp"]) < 0.006))
res["payload"] = dict(arms=pay, paired_payload=pp, bands=bands, author_vs_mine=cmp_,
                      n_equal=sum(v["equal"] for v in cmp_.values()), n_cmp=len(cmp_))

# ------------------------------------------------------------------------------------------------ [13] RE-24
RE = f"{R4O}/re24/v351_h210"
re24 = {}
und_sets = {}
for b in L.MAIN:
    rec = {int(f(r, "run")): r for r in L.read(f"{RE}/re24_{b}_rec0.csv.gz")}
    # rec0 vs P2 h210 runs 0-499: every common column equal as written
    p2 = {int(f(r, "run")): r for r in L.read(L.case_files(b, "liq", "v351", 210)[0])}
    common = [c for c in next(iter(p2.values())) if c in next(iter(rec.values()))]
    neq = sum(1 for k in p2 if any(rec[k][c] != p2[k][c] for c in common))
    mon = L.read(f"{RE}/re24_{b}_mon2.csv.gz")
    e = dict(rec0_vs_P2_rows_differing=neq, rec0_common_cols=len(common),
             rec0_mon2_files_identical=(L.sha16(f"{RE}/re24_{b}_rec0.csv.gz") == L.sha16(f"{RE}/re24_{b}_mon2.csv.gz")),
             mon2_aborts=sum(f(r, "gfm_abt") > 0.5 for r in mon), mon2_trips=sum(f(r, "gfm_t1") >= 0 for r in mon),
             rec0_trips=sum(f(r, "gfm_t1") >= 0 for r in rec.values()),
             rec0_x50_max=round(max(f(r, "gfm_x50") for r in rec.values()), 4), rec0_s50_lit_max=round(max(f(r, "gfm_s50_lit") for r in rec.values()), 4))
    for srv in ("A", "B"):
        r1 = {int(f(r, "run")): r for r in L.read(f"{RE}/re24_{b}_lb{srv}1.csv.gz")}
        r2 = {int(f(r, "run")): r for r in L.read(f"{RE}/re24_{b}_lb{srv}2.csv.gz")}
        jam = [k for k in r2 if f(r2[k], "jam_t0") >= 0]
        det = [k for k in jam if f(r2[k], "gfm_abt") > 0.5]
        und = sorted(k for k in jam if k not in det)
        und_sets[f"{b}|{srv}"] = set(und)
        tgo = {k: f(rec[k], "td_t") - f(r2[k], "jam_t0") for k in jam}      # time to the no-jam twin's touchdown
        u = {k: f(r2[k], "re24_jam_t_set") / (f(rec[k], "td_t") - f(rec[k], "lb_t5")) for k in jam if f(rec[k], "td_t") > f(rec[k], "lb_t5") > 0}
        ok0 = {k: f(rec[k], "ok") > 0.5 for k in rec}
        ok1 = {k: f(r1[k], "ok") > 0.5 for k in r1}
        ok2 = {k: f(r2[k], "ok") > 0.5 for k in r2}
        ttg_und = [tgo[k] for k in und]
        ttg_det = [tgo[k] for k in det]
        dm_und = [f(r2[k], "jam_dmax") for k in und]
        dm_rec_und = [f(r1[k], "jam_dmax") for k in und]
        # detected runs by time-to-go: continue (record twin) vs abort
        bins = [(0, 0.5), (0.5, 1), (1, 2), (2, 3), (3, 99)]
        bt = []
        for lo, hi in bins:
            ks = [k for k in det if lo <= tgo[k] < hi]
            bt.append(dict(bin=f"[{lo},{hi})", n=len(ks), ok_continue=sum(ok1[k] for k in ks), ok_abort=sum(ok2[k] for k in ks)))
        e[f"servo_{srv}"] = dict(
            n_jammed=len(jam), detected=len(det), undetected=len(und), undetected_runs=und,
            undetected_ok=sum(ok2[k] for k in und), undetected_ok_twin_rec0=sum(ok0[k] for k in und),
            undetected_lost_vs_rec0=sum(ok0[k] and not ok2[k] for k in und), undetected_gained=sum(ok2[k] and not ok0[k] for k in und),
            undetected_equal_record_twin_ok=all(ok1[k] == ok2[k] for k in und),
            undetected_rows_identical_to_record_twin=sum(all(r1[k][c] == r2[k][c] for c in r1[k] if not c.startswith("gfm_")) for k in und),
            undetected_ttg_s=dict(min=round(min(ttg_und), 3), p50=round(float(np.median(ttg_und)), 3), max=round(max(ttg_und), 3)) if und else None,
            undetected_u=dict(min=round(min(u[k] for k in und if k in u), 4), max=round(max(u[k] for k in und if k in u), 4)) if und else None,
            undetected_jam_dmax_deg=dict(min=round(min(dm_und), 3), p50=round(float(np.median(dm_und)), 3), max=round(max(dm_und), 3)) if und else None,
            undetected_jam_dmax_record_twin_deg_max=round(max(dm_rec_und), 3) if und else None,
            undetected_x50_max_deg=round(max(f(r2[k], "gfm_x50") for k in und), 3) if und else None,
            detected_ttg_min_s=round(min(ttg_det), 3), detected_ttg_p50_s=round(float(np.median(ttg_det)), 3),
            detected_continue_ok=sum(ok1[k] for k in det), detected_abort_ok=sum(ok2[k] for k in det),
            detected_by_ttg=bt,
            cp_ub95_one_sided_loss_rate_undetected=round(1 - 0.05 ** (1 / len(und)), 4) if und else None)
    re24[b] = e
ids = list(und_sets.values())
re24["undetected_run_id_overlap"] = {f"{k1} & {k2}": len(und_sets[k1] & und_sets[k2]) for i, k1 in enumerate(und_sets) for k2 in list(und_sets)[i + 1:]}
re24["undetected_union_size"] = len(set().union(*ids))
re24["mon2_cp_ub95_one_sided_false_abort_rate_1000"] = round(1 - 0.05 ** (1 / 1000), 5)
res["re24"] = re24

# ------------------------------------------------------------------------------------------------ [14](b) noise MC
rng = np.random.default_rng(20261019)
nmc = {}
for nfr in (50, 80):
    for shape in ("flat", "peak"):
        K = 100000
        x = rng.normal(0.0, 5.0, size=(K, nfr))
        if shape == "peak":
            # single-frame-wide peak: the clean signal is 0 at the peak frame and -10 N elsewhere (3-frame min of the clean
            # signal is then -10 N everywhere: the noise-free window max is -10 N); increase measured against that
            sig = np.full(nfr, -10.0); sig[nfr // 2] = 0.0
            x = x + sig
            base = -10.0
        else:
            base = 0.0
        m3 = np.minimum(np.minimum(x[:, :-2], x[:, 1:-1]), x[:, 2:])
        mx = m3.max(axis=1) - base
        nmc[f"{nfr}fr|{shape}"] = dict(p50=round(float(np.median(mx)), 3), p90=round(float(np.percentile(mx, 90)), 3),
                                       p99=round(float(np.percentile(mx, 99)), 3), mean=round(float(mx.mean()), 3))
res["r2_noise_mc"] = dict(assumption="iid N(0, 5 N) per 10 ms frame (author's 'independent frames ASSUMED'); increase of the window maximum of the 3-frame running minimum over the noise-free value",
                          results=nmc, margins_N=dict(R2_v1_v3p1_W10lt6=round(37.16 - 20.85, 2), R2_v2_mode3_0p5s_W10lt6=round(37.16 - 31.18, 2),
                                                     R2_v2_mode3_0p8s_W10lt6=round(37.16 - 31.86, 2)))
st = json.load(open(f"{R4O}/r2_starve/r2_starve.json"))
res["r2_starve_from_json"] = {w: {k: dict(all=[v["all"]["released"], v["all"]["aborted"], v["all"]["landed"], v["all"]["rel_t_max_s"] and round(v["all"]["rel_t_max_s"], 3)],
                                          W10lt6=[v["W10lt6"]["n"], v["W10lt6"]["released"], v["W10lt6"]["aborted"], v["W10lt6"]["landed"]])
                                  for k, v in c["by_st_T"].items()} | dict(threshold=c.get("starve_threshold_s"))
                              for w, c in st["cases"].items()}
res["r2_starve_sha16"] = L.sha16(f"{R4O}/r2_starve/r2_starve.json")

# ------------------------------------------------------------------------------------------------ RV5-06 sidecars
WM = f"{L.R4}/withdrawn_markers"
idx = json.load(open(f"{WM}/WITHDRAWN_INDEX.json"))
R3 = idx["rev3_root"]


def leaves(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from leaves(v, f"{p}/{k}")
    elif isinstance(o, list):
        for v in o:
            yield from leaves(v, f"{p}[]")
    else:
        yield p


W1 = re.compile(r"rh2[25]0")
W2 = re.compile(r"lit_k|/gap_N|/T_mid_N")
side = {}
for tgt, info in idx["files"].items():
    s = json.load(open(f"{WM}/{info['sidecar']}"))
    tpath = f"{R3}/{tgt}"
    e = dict(target_exists=os.path.exists(tpath))
    if e["target_exists"]:
        e["target_sha_match"] = hashlib.sha256(open(tpath, "rb").read()).hexdigest() == s["target_sha256"]
    if "table" in info:
        tp = f"{R3}/{info['table']}"
        e["table_sha_match"] = os.path.exists(tp) and hashlib.sha256(open(tp, "rb").read()).hexdigest() == info["table_sha256"]
        e["whole_file_withdrawn"] = s.get("whole_file_withdrawn")
    if tgt.endswith(".json") and e["target_exists"] and not s.get("whole_file_withdrawn"):
        lv = Counter(leaves(json.load(open(tpath))))
        e["n_leaf_total_mine"] = sum(lv.values())
        e["n_leaf_total_sidecar"] = s.get("n_leaf_paths_total")
        for sset in s["sets"]:
            rx = W1 if sset["id"] == "W1" else W2
            pats = sset.get("path_patterns", {})
            mine = {k: v for k, v in lv.items() if rx.search(k)}
            missing = {k: v for k, v in mine.items() if pats.get(k) != v}
            extra = {k: v for k, v in pats.items() if k not in mine}
            e[sset["id"]] = dict(n_leaf_sidecar=sset.get("n_leaf_paths"), n_leaf_regex_mine=sum(mine.values()),
                                 regex_leaves_not_covered=dict(list(missing.items())[:6]), n_regex_not_covered=len(missing),
                                 sidecar_extra_beyond_regex=dict(list(extra.items())[:8]), n_extra=len(extra))
    side[tgt] = e
res["rv5_06_sidecars"] = side
# withdrawn tokens in the v3.2 proposal texts (rev4)
for nm in ("v32_proposals_rev4.json", "v32_new_items_rev4.json"):
    s = open(f"{R4O}/v32/{nm}").read()
    res.setdefault("withdrawn_tokens_in_v32", {})[nm] = {t: len(re.findall(t, s)) for t in ("rh220", "rh250", "lit_k100", "lit_k875", "gap_N", "T_mid_N", "60 g")}

json.dump(res, open(OUT, "w"), indent=1, default=str)
print(json.dumps(dict(lm={k: [v["ge16p15_vs_lt"], v["corr_m_land"], v["ls_m_land_on_dry_scale_liq_left_fuel_left"], v["P80_by_dry_part_top_42pct_vs_rest"], v["P80_by_dry_part_fisher_p"]] for k, v in lm.items()}), default=str))
print("payload author==mine", res["payload"]["n_equal"], "/", res["payload"]["n_cmp"])
for k, v in res["payload"]["author_vs_mine"].items():
    if not v["equal"]:
        print("  DIFF", k, v)
print("bands", json.dumps({k: (v["band_strict_every_lower_flown"], v["band_floor_180"]) for k, v in bands.items()}))
for k, v in pp.items():
    print("paired", k, v["lost"], v["gained"], v["p"], v["ub95_pp"], L.rule_pass(v))
for k, v in pay.items():
    print("arm", k, v["vs_v3d_ref"]["lost"], v["vs_v3d_ref"]["gained"], v["vs_v3d_ref"]["ub95_pp"], "|", {b: (v[b]["P80"], v[b]["m_land_p50"], v[b]["burn_time"]["p99"], v[b]["fail"]) for b in L.MAIN})
for b in L.MAIN:
    e = re24[b]
    print("re24", b, {k: v for k, v in e.items() if not k.startswith("servo")})
    for srv in ("A", "B"):
        x = dict(e[f"servo_{srv}"]); x.pop("undetected_runs")
        print("   ", srv, x)
print("overlap", re24["undetected_run_id_overlap"], "union", re24["undetected_union_size"])
print("noise", nmc)
for k, v in side.items():
    print("side", k, {kk: vv for kk, vv in v.items() if kk not in ("W1", "W2")}, {s_: (v[s_]["n_leaf_sidecar"], v[s_]["n_leaf_regex_mine"], v[s_]["n_regex_not_covered"], v[s_]["n_extra"]) for s_ in ("W1", "W2") if s_ in v})
print("tokens", res["withdrawn_tokens_in_v32"])
