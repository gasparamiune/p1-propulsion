"""m2_re24 v1.0 (GNC rev4, 2026-10-13): RE-24 - does an UNDETECTED gimbal jam at the SIL detection bound lose a landing?
(coordinator rev4 item 4; Electronics REVIEW RE-24 / bench_plan_v3 'Jam threshold'.)

Bound (ASSUMED, Electronics S6, SIL v2.10 results/sil_v2p10/sil_run_log.txt 4a1698f2476e4928 and bench_plan_v3.md line 154):
the ECU monitor detects a jam only once the command moves >= 3 deg per axis (2.12 deg along the jammed servo's line) away
from the jam (1.5 deg threshold + 40 ms x model-rate allowance, 50 ms persistence); smaller excursions stay undetected. The
flights carry that monitor with the firmware constants (sim6 v2.13-dev amendment J, gfm_*, config.h v2.10 values; checked
against the SIL S6 classes by m2_bitcheck_v213 part B4) and the jam truth model (jam_*: the servo output locks, the free
servo keeps moving, linkage on the Cardan kinematics of mechanical.json).

Configuration: the P2 A1 arm at the line-208 band (GNC_RE24_ARM, default liq|G73|v351|h210): CAD v3.5.1 (488b47f9d55ff91b)
via iface_v351 + cfg ballast from out/rev4/mass_v351 (landing mass +1.3672 kg vs ledger v3d), purge G73, FSW-R2, seed 101,
500 paired runs per base on A1_none and A1J_pc, sim6 v2.13-dev (gnc_dev7) - the jam-off flight equals the P2 table of the
same arm (sim6 v2.9-dev, gnc_dev3) column for column (checked on every run of the rec0 arm).
Arms (all paired on the same draws):
  rec0   no jam, monitor RECORD (gfm_on 1): the reference (equals the P2 table) + per-run false-trip margins gfm_x50 / s50
  mon2   no jam, monitor ABORT (gfm_on 2): false GIMBAL_FAULT aborts of the flown firmware in nominal flights
  lbA1 / lbA2   servo 1 (lever act_az1) jams in the landing burn at u T_lb after the light (u ~ U(0, 0.95), own generator
                seed 20261114; T_lb = touchdown - light of the run's rec0 flight), monitor RECORD / ABORT
  lbB1 / lbB2   the same with servo 2 (lever act_az2)
  coA1 / coA2   servo 1 jams in the coast 1.0 s after MECO (near neutral): the whole landing burn flies jammed
  ascA1 / ascA2 servo 1 jams in the ascent burn at u t_MECO (u ~ U(0.05, 0.95), same generator, next stream)
Reading: in an ABORT arm a run is DETECTED when the monitor tripped while the engine was lit (gfm_abt 1; the GIMBAL_FAULT
abort then follows); otherwise the jam stayed UNDETECTED and the run is identical to its RECORD twin. The answer to RE-24 is
the landing outcome of the UNDETECTED jam runs (and its failure modes), against the paired no-jam reference; the RECORD arm
also gives the counterfactual 'continue with the jam' for the detected runs (input to the abort policy, research only).
Not modelled: the jammed servo's stall current on the shared supply (act_sag off in both bases), jam onset during a servo
reversal transient inside one 1 ms step, encoder faults, a roll manoeuvre to recover authority (no such FSW mode).
Parts: GNC_RE24_PARTS (check, rec0, arms, eval); GNC_RE24_BASES; GNC_RE24_ARMS. Env: m2r3_env.sh with GNC_IFACE =
iface_v351 and GNC_IFACE_PIN = pins_rev4/pins_rev4_v351.sha256. SIM only; no hardware data; not physical approval."""
import csv
import gzip
import hashlib
import json
import os
import sys
import time
from collections import OrderedDict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_rev3_fly as F3  # noqa: E402
from gncsim import run6 as R, sim6 as s6  # noqa: E402

F = F3.F
VERSION = "m2_re24 v1.0"
SP = "/home/claude/work/space"
MASS = f"{SP}/out/rev4/mass_v351/mass_v351_vs_v3d.json"
P2DIR = f"{SP}/out/rev4/p2"
ARM0 = os.environ.get("GNC_RE24_ARM", "liq|G73|v351|h210")
OUT = os.environ.get("GNC_RE24_OUT", f"{SP}/out/rev4/re24/{ARM0.split('|')[2]}_{ARM0.split('|')[3]}")
PARTS = [p for p in os.environ.get("GNC_RE24_PARTS", "check,rec0,arms,eval").split(",") if p]
BASES = ("A1_none", "A1J_pc")
U_SEED = 20261114
N_CHECK = 8
ARMS = OrderedDict([
    ("rec0", dict(jam=None, gfm=1)),
    ("mon2", dict(jam=None, gfm=2)),
    ("lbA1", dict(jam=("lb", 1), gfm=1)), ("lbA2", dict(jam=("lb", 1), gfm=2)),
    ("lbB1", dict(jam=("lb", 2), gfm=1)), ("lbB2", dict(jam=("lb", 2), gfm=2)),
    ("coA1", dict(jam=("co", 1), gfm=1)), ("coA2", dict(jam=("co", 1), gfm=2)),
    ("ascA1", dict(jam=("asc", 1), gfm=1)), ("ascA2", dict(jam=("asc", 1), gfm=2)),
])


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def arm_spec():
    st, pu, v, h = ARM0.split("|")
    var = json.load(open(MASS))["simulator"]["variants"][v]
    spec = dict(state=st, purge=pu, plat="", ex=dict(h_target=float(h[1:]), ballast=float(var["ballast_kg"]),
                                                     ballast_z=float(var["ballast_z_m"])),
                iface=var["iface"], pin=var["pin"], variant=v)
    if os.path.realpath(os.environ.get("GNC_IFACE", "")) != os.path.realpath(spec["iface"]) or \
            os.path.realpath(os.environ.get("GNC_IFACE_PIN", "")) != os.path.realpath(spec["pin"]):
        raise RuntimeError(f"{ARM0} needs GNC_IFACE {spec['iface']} and GNC_IFACE_PIN {spec['pin']}")
    return spec


def p2_table(base):
    fn = F3.fname(base, ARM0)
    p = os.path.join(P2DIR, fn + ".gz")
    meta = json.load(open(os.path.join(P2DIR, "meta", fn + ".json")))
    if meta["table_sha16"] != sha16(p) or meta["arm"] != ARM0:
        raise RuntimeError(f"P2 table {fn} does not match its meta")
    return p


def load(p):
    with gzip.open(p, "rt") as f:
        return list(csv.DictReader(f))


def setup(base, spec):
    p07z = F.engine_bay_mid()[0]
    cfg, m = F.base_cfg(base, spec["state"], F3.cfg_extra(spec, p07z))
    jr = json.load(open(F.TG))["j_ref"]
    F.MV.TG_JREF_DEFAULT = float(jr["A1J" if base.startswith("A1J") else "A1"])
    D = R.draw(np.random.default_rng(101), F.N, cfg)
    ms = F.MV.case_specs()["tot_cal_comp"]
    return cfg, D, ms, m


def u_draws():
    g = np.random.default_rng(U_SEED)
    u_lb = 0.95 * g.random(F.N)
    u_asc = 0.05 + 0.90 * g.random(F.N)
    return u_lb, u_asc


def onset(arm, row0, u_lb, u_asc, i, tlb_med):
    """(jam_ph, jam_t) of run i from its rec0 row."""
    kind = arm["jam"][0]
    if kind == "lb":
        t5, td = float(row0["lb_t5"]), float(row0["td_t"])
        T = td - t5 if (t5 > 0.0 and td > t5) else tlb_med
        return 3, float(u_lb[i] * T)
    if kind == "co":
        return 2, float(row0["t_meco"]) + 1.0
    return 1, float(u_asc[i] * float(row0["t_meco"]))


def fly(base, spec, name, rows0=None, n=None):
    """m2_rev3_fly.fly body (unchanged) + the arm's jam / monitor parameters per run."""
    arm = ARMS[name]
    cfg, D, ms, m = setup(base, spec)
    u_lb, u_asc = u_draws()
    tlb_med = None
    if arm["jam"] is not None:
        T = [float(r["td_t"]) - float(r["lb_t5"]) for r in rows0 if float(r["lb_t5"]) > 0 and float(r["td_t"]) > float(r["lb_t5"])]
        tlb_med = float(np.median(T))
    rows = []
    for i in range(F.N if n is None else n):
        c, disp = F.MV.run_cfg_case(cfg, D[i], ms, i, "base")
        c.update(F.DEC)
        c.update(F.PURGE[spec["purge"]])
        c.update(F.PLAT[spec["plat"]])
        if spec.get("gex"):
            c.update(spec["gex"])
        ex = dict(gfm_on=arm["gfm"])
        if arm["jam"] is not None:
            ph, tj = onset(arm, rows0[i], u_lb, u_asc, i, tlb_med)
            ex.update(jam_on=1, jam_srv=arm["jam"][1], jam_ph=ph, jam_t=tj)
        c.update(ex)
        res = R.fly(c, disp, nrec=10)[0]
        row = R.flat_row(i, D[i], res, R.success(res), cfg)
        row["m_n2o"] = m
        row["mest_kcal"] = float(c.get("mest_kcal", float("nan")))
        if arm["jam"] is not None:
            row["re24_jam_ph_set"] = float(ex["jam_ph"])
            row["re24_jam_t_set"] = float(ex["jam_t"])
        rows.append(row)
    return rows


def tab_path(base, name):
    return os.path.join(OUT, f"re24_{base}_{name}.csv")


def write(base, name, rows, t0):
    p = tab_path(base, name)
    F.M.write_csv(p, rows)
    with open(p, "rb") as fi, gzip.GzipFile(p + ".gz", "wb", mtime=0) as fo:
        fo.write(fi.read())
    os.remove(p)
    ok = np.array([r["ok"] for r in rows]) > 0.5
    meta = dict(version=VERSION, base=base, arm=name, spec=ARMS[name], arm0=ARM0, iface=os.environ.get("GNC_IFACE"),
                pin=os.environ.get("GNC_IFACE_PIN"), sim=s6.SIM6_VERSION, sim6_sha16=sha16(s6.__file__),
                run6_sha16=sha16(R.__file__), wall_s=round(time.time() - t0, 1), P=float(ok.mean()),
                table_sha16=sha16(p + ".gz"))
    os.makedirs(os.path.join(OUT, "meta"), exist_ok=True)
    json.dump(meta, open(os.path.join(OUT, "meta", f"re24_{base}_{name}.json"), "w"), indent=1)
    return meta


def same(a, b):
    a, b = float(a), float(b)
    return a == b or (np.isnan(a) and np.isnan(b)) or abs(a - b) <= 1e-9 * max(1.0, abs(b))


def compare_p2(rows, ref):
    bad = []
    for r, q in zip(rows, ref):
        for k in q:
            if k not in r:
                bad.append((r["run"], k, "missing"))
                continue
            if not same(r[k], q[k]):
                bad.append((r["run"], k, float(r[k]), float(q[k])))
    return bad


def part_check(base, spec):
    ref = load(p2_table(base))
    rows = fly(base, spec, "rec0", n=N_CHECK)
    bad = compare_p2(rows, ref[:N_CHECK])
    res = dict(base=base, n=N_CHECK, n_mismatch=len(bad), mismatches=bad[:20], ok=not bad)
    print(f"check {base}: rec0 (monitor RECORD, sim6 v2.13-dev) vs P2 table ({ARM0}): "
          f"{'OK' if not bad else 'FAIL'} ({len(bad)} mismatches over {N_CHECK} runs)", flush=True)
    return res


def part_rec0(base, spec):
    p = tab_path(base, "rec0") + ".gz"
    if os.path.exists(p):
        print("exists", base, "rec0", flush=True)
        return
    t0 = time.time()
    rows = fly(base, spec, "rec0")
    bad = compare_p2(rows, load(p2_table(base)))
    meta = write(base, "rec0", rows, t0)
    meta["p2_repro"] = dict(n=len(rows), n_mismatch=len(bad), mismatches=bad[:20], ok=not bad)
    json.dump(meta, open(os.path.join(OUT, "meta", f"re24_{base}_rec0.json"), "w"), indent=1)
    if bad:
        raise RuntimeError(f"rec0 {base}: {len(bad)} mismatches against the P2 table")
    print(f"{base:8s} rec0: P {meta['P']:.3f}; equals the P2 table on all {len(rows)} runs ({time.time() - t0:.0f} s)", flush=True)


def part_arms(base, spec, sel):
    rows0 = load(tab_path(base, "rec0") + ".gz")
    for nm in ARMS:
        if nm == "rec0" or (sel and nm not in sel):
            continue
        if os.path.exists(tab_path(base, nm) + ".gz"):
            print("exists", base, nm, flush=True)
            continue
        t0 = time.time()
        rows = fly(base, spec, nm, rows0)
        meta = write(base, nm, rows, t0)
        print(f"{base:8s} {nm:6s}: P {meta['P']:.3f} ({time.time() - t0:.0f} s)", flush=True)


# --------------------------------------------------------------------------------------------------------- evaluation
def col(rows, k):
    return np.array([float(r[k]) for r in rows])


def mcn(a, b):
    from scipy.stats import binomtest
    lost, gained = int(np.sum(a & ~b)), int(np.sum(~a & b))
    p = float(binomtest(lost, lost + gained, 0.5).pvalue) if lost + gained else 1.0
    return OrderedDict(n=int(len(a)), P_ref=round(float(a.mean()), 4), P_case=round(float(b.mean()), 4), lost=lost,
                       gained=gained, p_exact=float(f"{p:.3g}"))


def fail_modes(rows, mask):
    out = OrderedDict()
    for k, crit in (("exhausted", lambda r: float(r["exhausted"]) > 0.5), ("tipover", lambda r: float(r["tipover"]) > 0.5),
                    ("crash", lambda r: float(r["crash"]) > 0.5), ("not_landed", lambda r: float(r["landed"]) < 0.5),
                    ("vz_gt_2", lambda r: abs(float(r["td_vz"])) > R.CRIT["vz"]), ("vh_gt_0p5", lambda r: float(r["td_vh"]) > R.CRIT["vh"]),
                    ("tilt_gt_5", lambda r: float(r["td_tilt"]) > R.CRIT["tilt"]), ("rate_gt_10", lambda r: float(r["td_rate"]) > R.CRIT["rate"])):
        out[k] = int(sum(1 for r, m_ in zip(rows, mask) if m_ and float(r["ok"]) < 0.5 and crit(r)))
    return out


def q(x):
    x = np.asarray(x, float)
    if not len(x):
        return None
    return dict(n=int(len(x)), min=round(float(x.min()), 4), p50=round(float(np.median(x)), 4), p99=round(float(np.percentile(x, 99)), 4),
                max=round(float(x.max()), 4))


def part_eval():
    res = OrderedDict(version=VERSION, date=time.strftime("%Y-%m-%d"), sim=s6.SIM6_VERSION, arm0=ARM0,
                      bound="ASSUMED Electronics S6 / SIL v2.10: firmware monitor 1.5 deg + 40 ms x model rate, 50 ms",
                      arms=OrderedDict(), pooled=OrderedDict())
    T = {}
    for b in BASES:
        for nm in ARMS:
            p = tab_path(b, nm) + ".gz"
            if os.path.exists(p):
                T[(b, nm)] = load(p)
    for b in BASES:
        if (b, "rec0") not in T:
            continue
        r0 = T[(b, "rec0")]
        ok0 = col(r0, "ok") > 0.5
        e = OrderedDict()
        e["rec0"] = dict(P=float(ok0.mean()), gfm_trips=int(np.sum(col(r0, "gfm_t1") >= 0)),
                         x50_deg=q(col(r0, "gfm_x50")), x50_lit_deg=q(col(r0, "gfm_x50_lit")),
                         s50_deg=q(col(r0, "gfm_s50")), s50_lit_deg=q(col(r0, "gfm_s50_lit")),
                         servo_line_metric_would_trip_at_1p5deg=int(np.sum(col(r0, "gfm_s50_lit") > 1.5)))
        for nm in ARMS:
            if nm == "rec0" or (b, nm) not in T:
                continue
            r = T[(b, nm)]
            ok = col(r, "ok") > 0.5
            jam = col(r, "jam_t0") >= 0 if "jam_t0" in r[0] else np.zeros(len(r), bool)
            d = OrderedDict(vs_rec0=mcn(ok0, ok), n_jammed=int(jam.sum()))
            if ARMS[nm]["gfm"] == 2:
                det = col(r, "gfm_abt") > 0.5
                und = ~det
                d["aborts"] = int(det.sum())
                d["abort_height_m"] = q(col(r, "gfm_hab")[det]) if det.any() else None
                d["abort_phase"] = {str(int(k)): int(np.sum(col(r, "gfm_ph1")[det] == k)) for k in np.unique(col(r, "gfm_ph1")[det])} if det.any() else {}
                d["detected_runs_landed_ok"] = int(np.sum(ok & det))
                d["undetected_jam_runs"] = int(np.sum(und & jam))
                d["undetected_jam_runs_ok"] = int(np.sum(und & jam & ok))
                d["undetected_jam_runs_ref_ok"] = int(np.sum(und & jam & ok0))
                d["undetected_jam_vs_rec0"] = mcn(ok0[und & jam], ok[und & jam]) if (und & jam).any() else None
                d["undetected_jam_fail_modes"] = fail_modes(r, und & jam)
                rec = nm[:-1] + "1"
                if (b, rec) in T:
                    rr = T[(b, rec)]
                    okr = col(rr, "ok") > 0.5
                    d["detected_counterfactual_continue"] = dict(n=int(det.sum()), ok_if_continued=int(np.sum(okr & det)),
                                                                 ok_with_abort=int(np.sum(ok & det)))
                    same_und = bool(np.all(ok[und] == okr[und]))
                    d["undetected_identical_to_record_twin"] = same_und
            else:
                d["jam_dmax_deg"] = q(col(r, "jam_dmax")[jam]) if jam.any() else None
                d["jam_onset_height_m"] = q(col(r, "jam_h0")[jam]) if jam.any() else None
                d["first_trip_any_phase"] = int(np.sum(col(r, "gfm_t1") >= 0))
                d["fail_modes_jam"] = fail_modes(r, jam)
                if "td_t" in r[0]:
                    tgo = col(r, "td_t") - col(r, "jam_t0")
                    bins = [0, 1, 2, 3, 4, 6, 100]
                    d["ok_by_time_to_go_s"] = [dict(bin=f"[{lo},{hi})", n=int(np.sum(jam & (tgo >= lo) & (tgo < hi))),
                                                    ok=int(np.sum(jam & ok & (tgo >= lo) & (tgo < hi))))
                                               for lo, hi in zip(bins[:-1], bins[1:])]
            e[nm] = d
        res["arms"][b] = e
    for nm in ARMS:
        if nm == "rec0" or not all((b, nm) in T and (b, "rec0") in T for b in BASES):
            continue
        a0 = np.concatenate([col(T[(b, "rec0")], "ok") > 0.5 for b in BASES])
        a1 = np.concatenate([col(T[(b, nm)], "ok") > 0.5 for b in BASES])
        res["pooled"][nm] = mcn(a0, a1)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "re24.json")
    json.dump(res, open(p, "w"), indent=1, default=float)
    print("wrote", p, sha16(p), flush=True)
    for b, e in res["arms"].items():
        print(b, "rec0", {k: v for k, v in e["rec0"].items() if not isinstance(v, dict)}, flush=True)
        for nm, d in e.items():
            if nm == "rec0":
                continue
            s = f"  {nm:6s} P {d['vs_rec0']['P_case']:.3f} vs {d['vs_rec0']['P_ref']:.3f} -{d['vs_rec0']['lost']}/+{d['vs_rec0']['gained']}"
            if "aborts" in d:
                s += (f" | aborts {d['aborts']} | undetected jam {d['undetected_jam_runs']} ok {d['undetected_jam_runs_ok']}"
                      f" (ref ok {d['undetected_jam_runs_ref_ok']})")
            print(s, flush=True)


def main():
    spec = arm_spec()
    os.makedirs(OUT, exist_ok=True)
    bsel = [x for x in os.environ.get("GNC_RE24_BASES", ",".join(BASES)).split(",") if x]
    asel = [x for x in os.environ.get("GNC_RE24_ARMS", "").split(",") if x]
    print(f"{VERSION}: {ARM0} parts {PARTS} bases {bsel} arms {asel or list(ARMS)}; {s6.SIM6_VERSION}", flush=True)
    for b in bsel:
        if "check" in PARTS:
            c = part_check(b, spec)
            json.dump(c, open(os.path.join(OUT, f"check_{b}.json"), "w"), indent=1, default=str)
            if not c["ok"]:
                raise RuntimeError(f"check failed on {b}")
        if "rec0" in PARTS:
            part_rec0(b, spec)
        if "arms" in PARTS:
            part_arms(b, spec, asel)
    if "eval" in PARTS:
        part_eval()


if __name__ == "__main__":
    main()
