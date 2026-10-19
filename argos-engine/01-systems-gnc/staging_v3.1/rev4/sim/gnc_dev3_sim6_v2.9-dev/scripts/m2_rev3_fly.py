"""m2_rev3_fly v1.1 (GNC rev3, 2026-10-13; v1.1 adds the P2opt arms and a second comparator, earlier arms unchanged): flights for lead CHANGELOG line 181 items P2 (landing mass at the 285 m trim, with
the CAD v3.5 brackets relayed by the coordinator, line 182 (7)) and P3 (285 m coverage, RV3-06) on the rev2 configuration:
sim6 v2.9-dev, FSW-R2, decided purge G73, decided release rule, Combustion v2.4 line-state tables, seed 101, 500 paired runs.
The fly loop, the line states, the purge / plateau / bleed settings and the statistics are imported unchanged from
m2_rg01_refly v1.3 (rev2); this file only adds arms, the mass representations and the evaluation tables. No change to the
simulator or the flight software.

Arms (name = state|purge[|plateau][|mass][|h<target>]):
  repro         liq|G73|h285, pw|G73|h285 on A1_none / A1J_pc: re-flown and compared byte for byte with the staged rev2 tables
  P2 sweep      st|G73|dm<g>g|h285, st in (liq, pw), +0.10 / +0.20 / +0.30 / +0.45 kg point mass at the P07 station (the rev2
                M60 location, lead line 164 (7)); paired against st|G73|h285 (nominal mass)
  P2 CAD v3.5   st|G73|v35a|h285 (CAD v3.5 with ASSUMED bleed valves 2 x 0.30 kg, landing mass +1.168 kg against ledger v3d),
                st|G73|v35t|h285 (valves at the 0.15 kg target, +0.868 kg), liq|G73|v35g|h285 (attribution: gimballed engine,
                ring and P07 from CAD v3.5 only, +0.341 kg); interface set iface_v35a + cfg ballast from
                out/rev3/mass_v35/mass_v35_vs_v3d.json (m2_mass_v35 v1.0); paired against st|G73|h285
  P3            285 m: liq|none, liq|G73, pw|G73, pl|G73, e19|G73 on all four bases (as at 300 m in rev2); liq|none|L400,
                liqP|G73, pwP|G73, liq|G73|L400, pw|G73|L400, e19|G73|L400, nrLO|G73z (PURGE NOT RUN LO), nrLO|none on the
                two main bases (A1_none, A1J_pc; compute budget on the shared machine); paired against liq|none
                (|L400) at 285 m (total cost of the purge fix), against liq|G73 at 285 m (line-state effect) and against the
                same arm at 300 m (rev2 staged table, trim effect)
Statistics: exact McNemar (scipy binomtest), Wilson 95 %; 'loses' = below the comparator with p < 0.05; wind (W10, the
run's mean wind at 10 m, U(0, 8) m/s): failures by 2 m/s bin and P inside W10 < 6 m/s (launch-commit, lead line 181).
P_total = P|lit x (1 - P_abort) x (1 - p_nl) per state (RG-02 accounting), no weighted mean.
Env: m2r3_env.sh; GNC_REV3_ARMS (comma list of arm names or groups repro,P2,P2v35,P3), GNC_REV3_BASES (comma list),
GNC_REV3_PARTS (mc,eval), GNC_REV3_OUT. The v35 arms run only with GNC_IFACE = iface_v35a and its pin list.
Output: <out>/rf_<base>_<arm>.csv (+ meta/<same>.json), <out>/rev3_fly.json. SIM only; no physical validation."""
import csv
import gzip
import hashlib
import json
import os
import sys
import time
from collections import OrderedDict
import numpy as np

SP = "/home/claude/work/space"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_rg01_refly as F  # noqa: E402
from gncsim import run6 as R, sim6 as s6  # noqa: E402

VERSION = "m2_rev3_fly v1.1"
OUT = os.environ.get("GNC_REV3_OUT", f"{SP}/out/rev3/fly")
PARTS = os.environ.get("GNC_REV3_PARTS", "mc,eval").split(",")
HUBR2 = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev2"
R2T = f"{HUBR2}/results/rg01_refly"
MASS_V35 = f"{SP}/out/rev3/mass_v35/mass_v35_vs_v3d.json"
IF35 = f"{SP}/iface_v35a"
ALL4 = F.BASES_MAIN + F.BASES_EXTRA
H = 285.0
DM = (0.10, 0.20, 0.30, 0.45)


def _arms():
    a = OrderedDict()
    for st in ("liq", "pw"):
        a[f"{st}|G73|h285"] = dict(state=st, purge="G73", plat="", bases=ALL4, ex=dict(h_target=H), group="repro",
                                   ref=None)
    for st in ("liq", "pw"):
        for dm in DM:
            a[f"{st}|G73|dm{int(round(dm * 1000))}g|h285"] = dict(state=st, purge="G73", plat="", bases=F.BASES_MAIN,
                                                                  ex=dict(h_target=H, ballast=dm, ballast_z="P07"),
                                                                  group="P2", ref=f"{st}|G73|h285")
    for v, sts in (("v35a", ("liq", "pw")), ("v35t", ("liq", "pw")), ("v35g", ("liq",))):
        for st in sts:
            a[f"{st}|G73|{v}|h285"] = dict(state=st, purge="G73", plat="", bases=F.BASES_MAIN, ex=dict(h_target=H),
                                           v35=v, iface=IF35, group="P2v35", ref=f"{st}|G73|h285")
    # v1.1 P2 options (lead 175 (2) / 181 (5)): the v3.5 ledger re-exhausts at 285 m; trims below 275 m and landing-burn
    # reserve levers inside the 2.0 kg tank (planned deceleration fraction kd 0.6 -> 0.7; terminal gate 8 -> 5 m)
    for v in ("v35a", "v35t"):
        for st in ("liq", "pw"):
            for h in (275, 265, 255, 245):
                a[f"{st}|G73|{v}|h{h}"] = dict(state=st, purge="G73", plat="", bases=F.BASES_MAIN, ex=dict(h_target=float(h)),
                                              v35=v, iface=IF35, group=f"P2opt_{v}", ref=f"{st}|G73|h285",
                                              ref2=f"{st}|G73|{v}|h285")
            for nm, ex in (("kd70", dict(kd=0.7)), ("ht5", dict(ht=5.0))):
                a[f"{st}|G73|{v}|{nm}|h285"] = dict(state=st, purge="G73", plat="", bases=F.BASES_MAIN,
                                                   ex=dict(ex, h_target=H), v35=v, iface=IF35, group=f"P2opt_{v}",
                                                   ref=f"{st}|G73|h285", ref2=f"{st}|G73|{v}|h285")
    for st, pu, pl in (("liq", "none", ""), ("liq", "none", "L400"), ("pl", "G73", ""), ("e19", "G73", ""),
                       ("liqP", "G73", ""), ("pwP", "G73", ""), ("liq", "G73", "L400"), ("pw", "G73", "L400"),
                       ("e19", "G73", "L400"), ("nrLO", "G73z", ""), ("nrLO", "none", "")):
        nm = f"{st}|{pu}" + (f"|{pl}" if pl else "") + "|h285"
        a[nm] = dict(state=st, purge=pu, plat=pl, bases=ALL4 if (pl == "" and st in ("liq", "pl", "e19")) else F.BASES_MAIN,
                     ex=dict(h_target=H), group="P3",
                     ref=None if (st, pu) == ("liq", "none") else ("liq|none" + (f"|{pl}" if pl else "") + "|h285"))
    for nm in ("liq|G73|h285", "pw|G73|h285"):
        a[nm]["ref"] = "liq|none|h285"
    return a


ARMS = _arms()


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def v35_spec(v):
    j = json.load(open(MASS_V35))
    s = j["simulator"]["variants"][v]
    return dict(ballast=float(s["ballast_kg"]), ballast_z=(float(s["ballast_z_m"]) if s["ballast_z_m"] is not None else 0.6),
                iface=s["iface"], mech_sha16=j["simulator"]["derived_mechanical_json"]["sha256_16"],
                landing_mass_delta_kg=s["landing_mass_delta_kg"], src=f"{MASS_V35} ({sha16(MASS_V35)})")


def cfg_extra(spec, p07z):
    ex = dict(spec.get("ex") or {})
    if ex.get("ballast_z") == "P07":
        ex["ballast_z"] = p07z
    if spec.get("v35"):
        vs = v35_spec(spec["v35"])
        if vs["ballast"] > 0:
            ex["ballast"], ex["ballast_z"] = vs["ballast"], vs["ballast_z"]
    return ex


def fly(base, name, p07z):
    """m2_rg01_refly.fly_arm with the arm's cfg extras (unchanged loop)."""
    spec = ARMS[name]
    st = spec["state"]
    stc = "pw" if st == "bf" else st
    cfg, m = F.base_cfg(base, stc, cfg_extra(spec, p07z))
    jr = json.load(open(F.TG))["j_ref"]
    F.MV.TG_JREF_DEFAULT = float(jr["A1J" if base.startswith("A1J") else "A1"])
    D = R.draw(np.random.default_rng(101), F.N, cfg)
    ms = F.MV.case_specs()["tot_cal_comp"]
    rows = []
    for i in range(F.N):
        c, disp = F.MV.run_cfg_case(cfg, D[i], ms, i, "base")
        c.update(F.DEC)
        c.update(F.PURGE[spec["purge"]])
        c.update(F.PLAT[spec["plat"]])
        if spec.get("gex"):
            c.update(spec["gex"])
        if st == "bf":
            c.update(F.BLEED)
        res = R.fly(c, disp, nrec=10)[0]
        row = R.flat_row(i, D[i], res, R.success(res), cfg)
        row["m_n2o"] = m
        row["mest_kcal"] = float(c.get("mest_kcal", float("nan")))
        rows.append(row)
    return rows, cfg


def fname(base, name):
    return f"rf_{base}_{name.replace('|', '_')}.csv"


def part_mc():
    os.makedirs(os.path.join(OUT, "meta"), exist_ok=True)
    sel = [s for s in os.environ.get("GNC_REV3_ARMS", "repro").split(",") if s]
    bsel = [s for s in os.environ.get("GNC_REV3_BASES", "").split(",") if s]
    names = [n for n in ARMS if n in sel or ARMS[n]["group"] in sel]
    iface = os.path.realpath(os.environ.get("GNC_IFACE", ""))
    p07z = F.engine_bay_mid()[0]
    print(f"{VERSION}: GNC_IFACE {iface}; P07 station {p07z}; arms {len(names)}", flush=True)
    for name in names:
        spec = ARMS[name]
        need = os.path.realpath(spec.get("iface", f"{SP}/iface_v3d"))
        if need != iface:
            print(f"skip {name}: needs GNC_IFACE {need}", flush=True)
            continue
        for base in spec["bases"]:
            if bsel and base not in bsel:
                continue
            p = os.path.join(OUT, fname(base, name))
            if (os.path.exists(p) or os.path.exists(p + ".gz")) and os.environ.get("GNC_REV3_FORCE") != "1":
                print("exists", base, name, flush=True)
                continue
            t0 = time.time()
            rows, cfg = fly(base, name, p07z)
            F.M.write_csv(p, rows)
            ok = np.array([r["ok"] for r in rows]) > 0.5
            ex = int(np.sum([r["exhausted"] > 0.5 for r in rows]))
            meta = dict(version=VERSION, base=base, arm=name, spec={k: v for k, v in spec.items() if k != "bases"},
                        cfg_extra=cfg_extra(spec, p07z), iface=iface, pin=os.environ.get("GNC_IFACE_PIN"),
                        pin_sha16=sha16(os.environ["GNC_IFACE_PIN"]) if os.environ.get("GNC_IFACE_PIN") else None,
                        mech_sha16=sha16(os.path.join(iface, "mechanical.json")), sim=s6.SIM6_VERSION,
                        wall_s=round(time.time() - t0, 1), P=float(ok.mean()), exhausted=ex, table_sha16=sha16(p))
            if spec.get("v35"):
                meta["v35"] = v35_spec(spec["v35"])
                if meta["v35"]["mech_sha16"] != meta["mech_sha16"]:
                    raise RuntimeError("derived mechanical.json changed since m2_mass_v35")
            json.dump(meta, open(os.path.join(OUT, "meta", fname(base, name) + ".json"), "w"), indent=1)
            print(f"{base:9s} {name:22s}: P {ok.mean():.3f} exhausted {ex} ({time.time() - t0:.0f} s)", flush=True)


# ------------------------------------------------------------------------------------------------------------- evaluation
_MAN2 = {}


def _manifest2():
    if not _MAN2:
        for ln in open(f"{HUBR2}/MANIFEST_rev2.sha256"):
            if ln.strip():
                h, n = ln.split(None, 1)
                _MAN2[n.strip().lstrip("*").lstrip("./")] = h
    return _MAN2


def table(base, name, src=("rev3", "rev2")):
    """(rows, path, origin) of an arm table: rev3 output (csv or csv.gz) first, else the staged rev2 table (verified against
    MANIFEST_rev2.sha256)."""
    fn = fname(base, name)
    if "rev3" in src:
        for p in (os.path.join(OUT, fn), os.path.join(OUT, fn + ".gz")):
            if os.path.exists(p):
                op = gzip.open if p.endswith(".gz") else open
                with op(p, "rt") as f:
                    return list(csv.DictReader(f)), p, "rev3"
    if "rev2" in src:
        p = os.path.join(R2T, fn + ".gz")
        if os.path.exists(p):
            rel = os.path.relpath(p, HUBR2)
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()
            m = _manifest2()
            if m.get(rel) != h:
                raise RuntimeError(f"staged rev2 table {rel} does not match MANIFEST_rev2")
            with gzip.open(p, "rt") as f:
                return list(csv.DictReader(f)), p, "rev2-staged"
    return None, None, None


def wind_stats(rows):
    w = F.col(rows, "wind")
    ok = F.col(rows, "ok") > 0.5
    bins = [(0, 2), (2, 4), (4, 6), (6, 8.01)]
    by = OrderedDict()
    for lo, hi in bins:
        m = (w >= lo) & (w < hi)
        fm = {}
        for r in [rows[j] for j in np.where(m & ~ok)[0]]:
            k = F.fail_mode(r)
            fm[k] = fm.get(k, 0) + 1
        by[f"{lo}-{min(hi, 8):g}"] = dict(n=int(m.sum()), fail=int((m & ~ok).sum()), modes=fm)
    inside = w < 6.0
    k = int(ok[inside].sum())
    n = int(inside.sum())
    return dict(by_W10_bin=by, inside_W10_lt6=dict(n=n, ok=k, P=k / n if n else None,
                                                   P_wilson=[float(x) for x in R.wilson(k, n)] if n else None,
                                                   fails=[dict(run=int(rows[j]["run"]), wind=round(float(rows[j]["wind"]), 2),
                                                               mode=F.fail_mode(rows[j]))
                                                          for j in np.where(inside & ~ok)[0]]))


def pair(ra, rb):
    a, b = F.col(ra, "ok") > 0.5, F.col(rb, "ok") > 0.5
    if not (np.array_equal(F.col(ra, "run"), F.col(rb, "run")) and np.allclose(F.col(ra, "wind"), F.col(rb, "wind"))):
        raise RuntimeError("tables are not paired (run / wind columns differ)")
    d = F.mcnemar(a, b)
    d["reserve_shift_g"] = F.pct(F.usable_g(rb) - F.usable_g(ra), (1, 50))
    d["exhausted_ref_case"] = [int(np.sum(F.col(ra, "exhausted") > 0.5)), int(np.sum(F.col(rb, "exhausted") > 0.5))]
    w = F.col(ra, "wind") < 6.0
    d["inside_W10_lt6"] = F.mcnemar(a[w], b[w])
    return d


def part_eval():
    cs = F.comb_states()
    out = OrderedDict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, method=__doc__.split("\n\n")[0].strip(),
                      arms_doc=__doc__.split("\n\n")[1].strip(), env=dict(iface=os.environ.get("GNC_IFACE"),
                                                                         pin=os.environ.get("GNC_IFACE_PIN")),
                      sources=dict(rg01_line_states=f"{F.COMB} ({sha16(F.COMB)})", rev2_tables=R2T,
                                   rev2_manifest=f"{HUBR2}/MANIFEST_rev2.sha256 ({sha16(HUBR2 + '/MANIFEST_rev2.sha256')})",
                                   mass_v35=f"{MASS_V35} ({sha16(MASS_V35)})" if os.path.exists(MASS_V35) else None),
                      repro={}, cases=OrderedDict(), paired=OrderedDict(), pooled=OrderedDict(), missing=[])
    # repro: rev3 re-fly against the staged rev2 tables, byte for byte
    for name in ("liq|G73|h285", "pw|G73|h285"):
        for base in ALL4:
            p3 = os.path.join(OUT, fname(base, name))
            p2 = os.path.join(R2T, fname(base, name) + ".gz")
            if os.path.exists(p2) and (os.path.exists(p3) or os.path.exists(p3 + ".gz")):
                b3 = (gzip.open(p3 + ".gz").read() if os.path.exists(p3 + ".gz") else open(p3, "rb").read())
                out["repro"][f"{base}|{name}"] = dict(identical=b3 == gzip.open(p2).read(), rev3_sha16=hashlib.sha256(b3).hexdigest()[:16],
                                                      rev2=os.path.relpath(p2, HUBR2))
    for name, spec in ARMS.items():
        P = {"ref": [], "ref2": [], "line_state": [], "trim_300m": []}
        rnames = {}
        for base in spec["bases"]:
            r, p, org = table(base, name)
            if not r:
                out["missing"].append(f"{base}|{name}")
                continue
            e = F.arm_stats(r, spec["state"], cs)
            e["wind"] = wind_stats(r)
            e["table"] = dict(path=p, origin=org, sha256_16=sha16(p))
            out["cases"][f"{base}|{name}"] = e
            d = OrderedDict()
            refs = []
            if spec.get("ref"):
                refs.append(("ref", spec["ref"]))
            if spec.get("ref2"):
                refs.append(("ref2", spec["ref2"]))
            if spec["group"] in ("P3", "repro") and spec["state"] != "liq":
                refs.append(("line_state", "liq|G73" + (f"|{spec['plat']}" if spec["plat"] else "") + "|h285"))
            if spec["group"] in ("P3", "repro"):
                refs.append(("trim_300m", name.replace("|h285", "")))
            for kind, rn in refs:
                rr, rp, ro = table(base, rn)
                if not rr:
                    out["missing"].append(f"{base}|{rn} (ref of {name})")
                    continue
                d[f"vs_{rn}"] = dict(pair(rr, r), kind=kind, ref_table=dict(path=rp, origin=ro))
                P[kind].append((base, F.col(rr, "ok") > 0.5, F.col(r, "ok") > 0.5, F.col(rr, "wind") < 6.0))
                rnames[kind] = rn
            out["paired"][f"{base}|{name}"] = d
        for kind, L in P.items():
            for lab, sel in (("main2", [x for x in L if x[0] in F.BASES_MAIN]), ("all4", L)):
                if (lab == "main2" and len(sel) == 2) or (lab == "all4" and len(sel) == 4):
                    a = np.concatenate([x[1] for x in sel]); b = np.concatenate([x[2] for x in sel])
                    w = np.concatenate([x[3] for x in sel])
                    out["pooled"][f"{name}|vs_{rnames[kind]}|{lab}"] = dict(F.mcnemar(a, b), kind=kind,
                                                                           inside_W10_lt6=F.mcnemar(a[w], b[w]))
    p = os.path.join(OUT, "rev3_fly.json")
    with open(p, "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", p, sha16(p), flush=True)
    for k, v in out["repro"].items():
        print(f"repro {k:28s} identical {v['identical']}", flush=True)
    for k, e in out["cases"].items():
        w = e["wind"]["inside_W10_lt6"]
        print(f"{k:34s} P {e['P']:.3f} ex {e['exhausted']} res p01/min {e['usable_reserve_g']['p01']:.0f}/"
              f"{e['usable_reserve_g']['min']:.0f} g apo p50 {e['apogee_m']['p50']:.1f} W<6 {w['ok']}/{w['n']} fm {e['fail_modes']}",
              flush=True)
    for k, e in out["pooled"].items():
        print(f"pooled {k:52s} {e['P_case']:.4f} vs {e['P_ref']:.4f} -{e['lost']}/+{e['gained']} p {e['p_exact']:.3g}"
              f"{' LOSES' if e['loses'] else ''} | W<6 -{e['inside_W10_lt6']['lost']}/+{e['inside_W10_lt6']['gained']}",
              flush=True)
    if out["missing"]:
        print("missing", len(out["missing"]), out["missing"][:12], flush=True)


def main():
    if "mc" in PARTS:
        part_mc()
    if "eval" in PARTS:
        part_eval()


if __name__ == "__main__":
    main()
