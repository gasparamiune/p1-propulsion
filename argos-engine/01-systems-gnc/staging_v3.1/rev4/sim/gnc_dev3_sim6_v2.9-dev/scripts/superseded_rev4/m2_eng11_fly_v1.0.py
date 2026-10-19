"""m2_eng11_fly v1.0 (GNC rev4, 2026-10-13): ENG-11 in the 6-DOF. Paired landing P at the two ends and the nominal value of
Mechanical's V5c gimbal stiffness (structure + rod chain 3133 / 5353 / 7406 N m/rad, servo rigid), the companion of the linear
margins of m2_eng11 v1.1 (coordinator rev4 item 1; lead CHANGELOG 188 (7) and 204 (6)).

Mass and trajectory (coordinator: 'Fly 285 m at the v35t bracket for now and state which mass you used'): the rev3 arm
liq|G73|v35t|h285 = interface set iface_v35a + the v35t cfg ballast 0.52665 kg at z 0.4578 m (CAD v3.5 with the bleed valves
at the 0.15 kg target, landing mass +0.868 kg against ledger v3d; out/rev3/mass_v35/mass_v35_vs_v3d.json), 285 m, purge G73,
line state liq, FSW-R2, sim6 v2.9-dev (gnc_dev3), seed 101, 500 paired runs. NOT the frozen v3.5.1 ledger (+1.367 kg): that
mass loses at 285 m (P2) and is flown by m2_rev4_p2; the stiffness comparison is paired within one mass.
Fly loop: m2_rev3_fly v1.1 .fly copied line for line with one per-run hook (a 'check' part re-flies the first runs with the
hook off and compares every column with the rev3 table, which is verified against the hub rev3 MANIFEST).

Per-run hook (only the stiffness, the reflected rotor inertia and the notch centre change; every random draw is the base's):
  u      = (rock_K_base - 552.5) / (1681 - 552.5), the base draw's own uniform number (mechanical.json v2.1 MC range)
  K_s    = 58 + 116 u (ASSUMED servo output stiffness range, electronics.json v1 via mechanical.json v2.1), or fixed per arm
  K_tot  = 1 / (1/S + 1/(K_s g)) on the engine axis -> disp rock_K (one value for both axes: the 6-DOF has one rocking K;
           each end arm puts BOTH axes at that end, conservative)
  J      = act_Jint 1.6e-3 x g / n^2 (consistent kinematics: the rotor reflects through the same pose ratio as the servo
           spring; A1J_pc only, act_model 1; A1_none flies act_model 0 where J is not modelled)
  notch  (A1J_pc, which flies the ECU notch Q 1 / -12 dB): FIXED at e x the centre-pose mode of the same build (same K_s,
           chain variant and J), the landing-state engine inertia of the run (the sim's tracking path is used with
           notch_mis = e x f_centre / f_run, so gim_notch_f = e x f_centre exactly); e ~ U(0.95, 1.05) from its own generator
           (seed 20261113; the ENG-07d +/-5 % B-TVC-1 basis). The base's own-mode notch x U(0.85, 1.15) is replaced.
           A1_none has no notch (as its base).
Arms (S, pose kinematics g from 04-fea/stiffness/gimbal_k_summary_V5c_v1.json, read-only):
  nom       S 5353.1 (V5c mean), g = n^2 23.04 (centre), notch on its own mode x e
  lo        S 3133 (betam7 beta, chain-low), g 17.715; notch at the centre-pose beta mode (chain-low) x e
  hi        S 7406 (betam7 alpha), g 25.242; notch at the centre-pose alpha mode x e
  lo_ks58, nom_ks58, lo_ks174: the same with K_s fixed (the linear worst corner is K_s 58)
Comparators (exact McNemar on the same draws, as rev3): (a) the rev3 table liq|G73|v35t|h285 of the same base (mechanical.json
v2.1 stiffness draw U(552.5, 1681) with the base notch rule); (b) the nom arm (the V5c spread alone). Pooled A1J_pc + A1_none
and per base. Loads: ENG-07b saturation episodes (act_sat_max_dur, lead 2026-10-12: none longer than 0.1 s in the landing
burn), hinge-moment demand, gimbal rate / acceleration p99.
Parts: GNC_E11F_PARTS (ip, check, mc, eval); GNC_E11F_ARMS; GNC_E11F_BASES. Env as m2r3_env.sh with GNC_IFACE =
iface_v35a and GNC_IFACE_PIN = pins_rev3/pins_rev3_v35a.sha256 (checked).
SIM only (the rocking model is the linear spring-damper of sim6 v2.1; no hardware data). Not physical approval."""
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
VERSION = "m2_eng11_fly v1.0"
SP = "/home/claude/work/space"
HUB = "/home/claude/work/shared-fallback/engine"
V5C = f"{HUB}/04-fea/stiffness/gimbal_k_summary_V5c_v1.json"
MECH_HUB = f"{HUB}/interfaces/mechanical.json"
HUBR3 = f"{HUB}/01-systems-gnc/staging_v3.1/rev3"
REF_DIR = f"{SP}/out/rev3/fly"
OUT = os.environ.get("GNC_E11F_OUT", f"{SP}/out/rev4/eng11/fly")
PARTS = [p for p in os.environ.get("GNC_E11F_PARTS", "ip,check,mc,eval").split(",") if p]
ARM0 = "liq|G73|v35t|h285"
IFACE = f"{SP}/iface_v35a"
PIN = f"{SP}/pins_rev3/pins_rev3_v35a.sha256"
BASES = ("A1J_pc", "A1_none")
KS = (58.0, 174.0)
E_W = 0.05
E_SEED = 20261113
N_CHECK = 12


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def v5c():
    d = json.load(open(V5C))
    n_m = float(json.load(open(MECH_HUB))["tvc_actuation"]["gear_ratio_n"]["v"])
    T = {}
    for p, q in d["poses"].items():
        for a in ("alpha", "beta"):
            k = f"K_{a}"
            st = q["mech_T"][k]
            T[(p, a)] = dict(T=st, low=q["mech_T_chainlow"][k], g=1.0 / (1.0 / q["smin_T"][k] - 1.0 / st) / 58.0)
    return d, T, n_m


def arms():
    d, T, n_m = v5c()
    n2 = n_m * n_m
    S_nom = float(d["variant"]["mean"])
    lo = dict(S=T[("betam7", "beta")]["low"], g=T[("betam7", "beta")]["g"], Sc=T[("centre", "beta")]["low"],
              gc=T[("centre", "beta")]["g"], where="betam7 beta chain-low; notch at the centre-pose beta mode (chain-low)")
    hi = dict(S=T[("betam7", "alpha")]["T"], g=T[("betam7", "alpha")]["g"], Sc=T[("centre", "alpha")]["T"],
              gc=T[("centre", "alpha")]["g"], where="betam7 alpha; notch at the centre-pose alpha mode")
    nom = dict(S=S_nom, g=n2, Sc=S_nom, gc=n2, where="V5c mean, centre kinematics n^2; notch on its own mode")
    a = OrderedDict()
    a["nom"] = dict(nom, Ks=None)
    a["lo"] = dict(lo, Ks=None)
    a["hi"] = dict(hi, Ks=None)
    a["lo_ks58"] = dict(lo, Ks=58.0)
    a["nom_ks58"] = dict(nom, Ks=58.0)
    a["lo_ks174"] = dict(lo, Ks=174.0)
    return a, n2


def ref_table(base):
    fn = F3.fname(base, ARM0) + ".gz"
    p = os.path.join(REF_DIR, fn)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    man = {}
    for ln in open(os.path.join(HUBR3, "MANIFEST_rev3.sha256")):
        if ln.strip():
            x, y = ln.split(None, 1)
            man[y.strip().lstrip("*").lstrip("./")] = x
    if man.get(f"tables/fly/{fn}") != h:
        raise RuntimeError(f"reference {fn} does not match the hub rev3 MANIFEST")
    return p


def env_check():
    if os.path.realpath(os.environ.get("GNC_IFACE", "")) != os.path.realpath(IFACE):
        raise RuntimeError(f"GNC_IFACE must be {IFACE}")
    if os.path.realpath(os.environ.get("GNC_IFACE_PIN", "")) != os.path.realpath(PIN):
        raise RuntimeError(f"GNC_IFACE_PIN must be {PIN}")


def setup(base):
    """(cfg, D, ms, spec) exactly as m2_rev3_fly.fly for ARM0 on this base."""
    spec = F3.ARMS[ARM0]
    p07z = F.engine_bay_mid()[0]
    cfg, m = F.base_cfg(base, spec["state"], F3.cfg_extra(spec, p07z))
    jr = json.load(open(F.TG))["j_ref"]
    F.MV.TG_JREF_DEFAULT = float(jr["A1J" if base.startswith("A1J") else "A1"])
    D = R.draw(np.random.default_rng(101), F.N, cfg)
    ms = F.MV.case_specs()["tot_cal_comp"]
    return cfg, D, ms, spec, m


def run_case(cfg, D, ms, spec, i):
    c, disp = F.MV.run_cfg_case(cfg, D[i], ms, i, "base")
    c.update(F.DEC)
    c.update(F.PURGE[spec["purge"]])
    c.update(F.PLAT[spec["plat"]])
    if spec.get("gex"):
        c.update(spec["gex"])
    return c, disp


def e_draws():
    rng = np.random.default_rng(E_SEED)
    return 1.0 + E_W * (2.0 * rng.random(F.N) - 1.0)


def ip_path(base):
    return os.path.join(OUT, f"ip_{base}.json")


def part_ip(base):
    """Landing-state engine inertia about the pivot of every run (the sim's own notch-tracking formula, dispersed mass
    properties): probe build with the tracking notch on and mistune 1, I_p = K / (2 pi f)^2 - J."""
    cfg, D, ms, spec, m = setup(base)
    out = []
    for i in range(F.N):
        c, disp = run_case(cfg, D, ms, spec, i)
        c2 = dict(c, gim_notch_track=1.0)
        d2 = dict(disp, notch_mis=1.0)
        par = R.build(c2, d2)[0]
        f = float(par[s6.P_gim_notch_f])
        out.append(float(par[s6.P_rock_K]) / (2.0 * np.pi * f) ** 2 - float(par[s6.P_act_Jint]))
    json.dump(dict(version=VERSION, base=base, arm=ARM0, I_p_landing_kgm2=out), open(ip_path(base), "w"))
    print(f"ip {base}: I_p landing mean {np.mean(out):.5f} sd {np.std(out):.5f} min {min(out):.5f} max {max(out):.5f}",
          flush=True)


def hook(arm, base, cfg, D, i, c, disp, Ip, e, n2):
    """Apply one ENG-11 arm to run i. Returns the record of what was set."""
    klo, khi = R._kax_range(cfg)
    u = (float(D[i]["rock_K"]) - klo) / (khi - klo)
    Ks = arm["Ks"] if arm["Ks"] is not None else KS[0] + (KS[1] - KS[0]) * u
    Kt = 1.0 / (1.0 / arm["S"] + 1.0 / (Ks * arm["g"]))
    Kc = 1.0 / (1.0 / arm["Sc"] + 1.0 / (Ks * arm["gc"]))
    disp["rock_K"] = Kt
    am1 = int(cfg["act_model"]) == 1
    J0 = float(cfg["act_Jint"]) if am1 else 0.0
    nact2 = float(cfg["act_n"]) ** 2 if am1 else n2
    if am1:
        c["act_Jint"] = J0 * arm["g"] / nact2
    Jr, Jc = J0 * arm["g"], J0 * arm["gc"]
    f_run = float(np.sqrt(Kt / (Ip + Jr)) / (2.0 * np.pi))
    f_c = float(np.sqrt(Kc / (Ip + Jc)) / (2.0 * np.pi))
    rec = dict(e11_u=u, e11_Ks=Ks, e11_K_tot=Kt, e11_J_eng=Jr, e11_f_run_Hz=f_run, e11_f_centre_Hz=f_c)
    if float(cfg.get("gim_notch_track", 0.0) or 0.0) > 0.0:
        disp["notch_mis"] = float(e * f_c / f_run)
        rec.update(e11_e=float(e), e11_notch_Hz=float(e * f_c))
    return rec


def fly_arm(base, name, arm, n2, n=None, hook_on=True):
    cfg, D, ms, spec, m = setup(base)
    Ip = json.load(open(ip_path(base)))["I_p_landing_kgm2"]
    E = e_draws()
    rows = []
    for i in range(F.N if n is None else n):
        c, disp = run_case(cfg, D, ms, spec, i)
        rec = hook(arm, base, cfg, D, i, c, disp, Ip[i], E[i], n2) if hook_on else {}
        res = R.fly(c, disp, nrec=10)[0]
        row = R.flat_row(i, D[i], res, R.success(res), cfg)
        row["m_n2o"] = m
        row["mest_kcal"] = float(c.get("mest_kcal", float("nan")))
        row.update(rec)
        rows.append(row)
    return rows, cfg


def load(p):
    import csv
    with gzip.open(p, "rt") as f:
        return list(csv.DictReader(f))


def part_check(base, A, n2):
    """Hook off: the first runs equal the rev3 table column for column. Hook on: the build sees the intended values."""
    ref = load(ref_table(base))
    rows, cfg = fly_arm(base, "check", None, n2, n=N_CHECK, hook_on=False)
    bad = []
    for r, q in zip(rows, ref[:N_CHECK]):
        for k, v in r.items():
            a, b = float(v), float(q[k])
            if not ((np.isnan(a) and np.isnan(b)) or a == b or abs(a - b) <= 1e-9 * max(1.0, abs(b))):
                bad.append((r["run"], k, a, b))
    # hook on: probe builds of run 0..2 for every arm
    cfg, D, ms, spec, m = setup(base)
    Ip = json.load(open(ip_path(base)))["I_p_landing_kgm2"]
    E = e_draws()
    probes = OrderedDict()
    for nm, arm in A.items():
        lst = []
        for i in range(3):
            c, disp = run_case(cfg, D, ms, spec, i)
            rec = hook(arm, base, cfg, D, i, c, disp, Ip[i], E[i], n2)
            par = R.build(c, disp)[0]
            got = dict(rock_K=float(par[s6.P_rock_K]), J_eng=float(par[s6.P_act_Jint]) if int(cfg["act_model"]) == 1 else 0.0,
                       notch_Hz=float(par[s6.P_gim_notch_f]))
            ok = (abs(got["rock_K"] - rec["e11_K_tot"]) < 1e-6 * rec["e11_K_tot"]
                  and abs(got["J_eng"] - rec["e11_J_eng"]) < 1e-9
                  and (abs(got["notch_Hz"] - rec["e11_notch_Hz"]) < 1e-6 * rec["e11_notch_Hz"] if "e11_notch_Hz" in rec
                       else got["notch_Hz"] == 0.0))
            lst.append(dict(run=i, set=rec, build=got, ok=bool(ok)))
        probes[nm] = lst
    res = dict(base=base, n_rows=N_CHECK, mismatches=bad[:20], n_mismatch=len(bad), repro_ok=not bad,
               probes=probes, probes_ok=all(x["ok"] for v in probes.values() for x in v))
    print(f"check {base}: repro {'OK' if not bad else 'FAIL'} ({len(bad)} mismatches over {N_CHECK} runs); probes "
          f"{'OK' if res['probes_ok'] else 'FAIL'}", flush=True)
    return res


def part_mc(base, A, n2, sel):
    os.makedirs(os.path.join(OUT, "meta"), exist_ok=True)
    for nm, arm in A.items():
        if sel and nm not in sel:
            continue
        p = os.path.join(OUT, f"e11_{base}_{nm}.csv")
        if os.path.exists(p + ".gz"):
            print("exists", base, nm, flush=True)
            continue
        t0 = time.time()
        rows, cfg = fly_arm(base, nm, arm, n2)
        F.M.write_csv(p, rows)
        with open(p, "rb") as fi, gzip.GzipFile(p + ".gz", "wb", mtime=0) as fo:
            fo.write(fi.read())
        os.remove(p)
        ok = np.array([r["ok"] for r in rows]) > 0.5
        meta = dict(version=VERSION, base=base, arm=nm, spec=arm, iface=os.environ.get("GNC_IFACE"),
                    pin_sha16=sha16(PIN), sim=s6.SIM6_VERSION, wall_s=round(time.time() - t0, 1), P=float(ok.mean()),
                    table_sha16=sha16(p + ".gz"), v5c_sha16=sha16(V5C))
        json.dump(meta, open(os.path.join(OUT, "meta", f"e11_{base}_{nm}.json"), "w"), indent=1)
        print(f"{base:8s} {nm:9s}: P {ok.mean():.3f} ({time.time() - t0:.0f} s)", flush=True)


def mcn(a, b):
    from scipy.stats import binomtest
    lost, gained = int(np.sum(a & ~b)), int(np.sum(~a & b))
    p = float(binomtest(lost, lost + gained, 0.5).pvalue) if lost + gained else 1.0
    return OrderedDict(P_ref=round(float(a.mean()), 4), P_case=round(float(b.mean()), 4), lost=lost, gained=gained,
                       p_exact=float(f"{p:.3g}"), n=int(len(a)), loses=bool(b.mean() < a.mean() and p < 0.05))


def col(rows, k):
    return np.array([float(r[k]) for r in rows])


def loads(rows):
    ok = col(rows, "ok") > 0.5
    out = OrderedDict()
    for k in ("act_sat_max_dur", "act_sat_time_land", "max_hinge_dem", "max_gim_acc", "max_gim_rate", "max_gim"):
        if k in rows[0]:
            x = col(rows, k)
            out[k] = dict(p50=float(np.percentile(x, 50)), p99=float(np.percentile(x, 99)), max=float(np.max(x)))
    if "act_sat_max_dur" in rows[0]:
        out["n_sat_episode_gt_0p1s"] = int(np.sum(col(rows, "act_sat_max_dur") > 0.1))
    out["P"] = float(ok.mean())
    out["exhausted"] = int(np.sum(col(rows, "exhausted") > 0.5))
    return out


def part_eval(A):
    res = OrderedDict(version=VERSION, date=time.strftime("%Y-%m-%d"), sim=s6.SIM6_VERSION, arm0=ARM0,
                      mass=("iface_v35a + v35t cfg ballast 0.52665 kg at z 0.4578 m (CAD v3.5, bleed valves at the 0.15 kg "
                            "target; landing mass +0.868 kg against ledger v3d), 285 m"),
                      v5c=dict(path=V5C, sha256_16=sha16(V5C)), arms=OrderedDict(), pooled=OrderedDict())
    tabs = {}
    for b in BASES:
        rp = ref_table(b)
        tabs[(b, "rev3")] = load(rp)
        res.setdefault("references", {})[b] = dict(path=rp, sha256_16=sha16(rp))
        for nm in A:
            p = os.path.join(OUT, f"e11_{b}_{nm}.csv.gz")
            if os.path.exists(p):
                tabs[(b, nm)] = load(p)
    for nm in A:
        e = OrderedDict(spec=A[nm], per_base=OrderedDict())
        for b in BASES:
            if (b, nm) not in tabs:
                continue
            r, r0 = tabs[(b, nm)], tabs[(b, "rev3")]
            if not np.array_equal(col(r, "run"), col(r0, "run")):
                raise RuntimeError("not paired")
            ok, ok0 = col(r, "ok") > 0.5, col(r0, "ok") > 0.5
            pb = OrderedDict(loads=loads(r), vs_rev3=mcn(ok0, ok))
            if (b, "nom") in tabs and nm != "nom":
                pb["vs_nom"] = mcn(col(tabs[(b, "nom")], "ok") > 0.5, ok)
            if "e11_f_run_Hz" in r[0]:
                f = col(r, "e11_f_run_Hz")
                pb["f_run_Hz"] = dict(min=float(f.min()), p50=float(np.median(f)), max=float(f.max()))
                pb["K_tot"] = dict(min=float(col(r, "e11_K_tot").min()), max=float(col(r, "e11_K_tot").max()))
            if "e11_notch_Hz" in r[0]:
                rr = col(r, "e11_notch_Hz") / f
                pb["notch_over_mode"] = dict(min=float(rr.min()), p50=float(np.median(rr)), max=float(rr.max()))
            e["per_base"][b] = pb
        if all((b, nm) in tabs for b in BASES):
            a0 = np.concatenate([col(tabs[(b, "rev3")], "ok") > 0.5 for b in BASES])
            a1 = np.concatenate([col(tabs[(b, nm)], "ok") > 0.5 for b in BASES])
            e["pooled_vs_rev3"] = mcn(a0, a1)
            if nm != "nom" and all((b, "nom") in tabs for b in BASES):
                an = np.concatenate([col(tabs[(b, "nom")], "ok") > 0.5 for b in BASES])
                e["pooled_vs_nom"] = mcn(an, a1)
        res["arms"][nm] = e
    for b in BASES:
        res["pooled"][f"rev3_{b}_loads"] = loads(tabs[(b, "rev3")])
    p = os.path.join(OUT, "eng11_fly.json")
    json.dump(res, open(p, "w"), indent=1, default=float)
    print("wrote", p, sha16(p))
    for nm, e in res["arms"].items():
        s = " | ".join(f"{b} P {pb['loads']['P']:.3f} vs rev3 -{pb['vs_rev3']['lost']}/+{pb['vs_rev3']['gained']} p "
                       f"{pb['vs_rev3']['p_exact']:.3g} sat>0.1s {pb['loads'].get('n_sat_episode_gt_0p1s')} acc p99 "
                       f"{pb['loads']['max_gim_acc']['p99']:.0f}" for b, pb in e["per_base"].items())
        print(f"{nm:9s}: {s}" + (f" | pooled vs rev3 {e['pooled_vs_rev3']['P_case']:.3f}/{e['pooled_vs_rev3']['P_ref']:.3f} "
                                 f"p {e['pooled_vs_rev3']['p_exact']:.3g}" if "pooled_vs_rev3" in e else "")
              + (f" | vs nom -{e['pooled_vs_nom']['lost']}/+{e['pooled_vs_nom']['gained']} p {e['pooled_vs_nom']['p_exact']:.3g}"
                 if "pooled_vs_nom" in e else ""))


def main():
    env_check()
    os.makedirs(OUT, exist_ok=True)
    A, n2 = arms()
    bsel = [x for x in os.environ.get("GNC_E11F_BASES", ",".join(BASES)).split(",") if x]
    asel = [x for x in os.environ.get("GNC_E11F_ARMS", "").split(",") if x]
    print(f"{VERSION}: parts {PARTS} bases {bsel} arms {asel or list(A)}", flush=True)
    chk = {}
    for b in bsel:
        if "ip" in PARTS and not os.path.exists(ip_path(b)):
            part_ip(b)
        if "check" in PARTS:
            chk[b] = part_check(b, A, n2)
            json.dump(chk[b], open(os.path.join(OUT, f"check_{b}.json"), "w"), indent=1, default=float)
            if not (chk[b]["repro_ok"] and chk[b]["probes_ok"]):
                raise RuntimeError(f"check failed on {b}")
        if "mc" in PARTS:
            part_mc(b, A, n2, asel)
    if "eval" in PARTS:
        part_eval(A)


if __name__ == "__main__":
    main()
