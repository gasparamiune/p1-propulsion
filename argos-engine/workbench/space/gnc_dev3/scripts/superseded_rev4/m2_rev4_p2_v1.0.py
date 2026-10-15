"""m2_rev4_p2 v1.0 (GNC rev4, 2026-10-13): P2 apogee re-fly on the FROZEN massprops v3.5.1 (lead CHANGELOG 206 (1)) by the
line 204 (3) rule: the A1 apogee target is the highest 5 m band with no significant pooled loss against the v3d reference,
with the tank-outlet dip onset applied on both arms. Coordinator rev4 P2 message: as-built v3.5.1 plus two sensitivity arms,
(a) the 0.15 kg valve target (-0.30 kg) and (b) the approved v3.5.2 levers (about -0.31 kg, DERIVED); the TVC loop uses the
v3.5.1 engine inertia; state plainly if no band at or above 200 m survives.

Flights: the rev3 fly loop m2_rev3_fly v1.1 .fly (itself m2_rg01_refly v1.3) imported and run unchanged: sim6 v2.9-dev
(gnc_dev3), FSW-R2, decided purge G73, decided release rule, Combustion v2.4 line-state tables, seed 101, 500 paired runs,
bases A1_none and A1J_pc (the rev3 pooled pair), line states liq and pw. Each arm is registered in m2_rev3_fly.ARMS with its
cfg extras (h_target, ballast, ballast_z) from out/rev4/mass_v351/mass_v351_vs_v3d.json (m2_mass_v351 v1.0); the variant's
derived interface set and pin list must be the active GNC_IFACE / GNC_IFACE_PIN (checked).
Arms: st|G73|<variant>|h<h>, st in (liq, pw), variant in (v351, v351t, v352L), h in 5 m bands (env GNC_P2_BANDS per variant).
Reference: st|G73|h285 on ledger v3d (rev3 tables, verified against the hub rev3 MANIFEST), same state, same base.
Statistics: exact McNemar pooled over A1_none + A1J_pc (1000 paired runs) as m2_rev3_reserve_dip v1.1 paired_adjusted, at the
flown 60 g residual and with the R3-17 dip onsets 62 / 69 / 80 g applied to BOTH tables (a landed run with liquid left below
the onset counts as lost). A band qualifies when it does not lose (lower with p < 0.05) at the flown basis, 69 g and 80 g
(the rev3 / line 204 reading); 62 g is reported. Bands, not thresholds: each band is one paired comparison, no correction
for multiple bands; the answer is reported with the neighbouring bands.
Env: m2r3_env.sh + GNC_IFACE / GNC_IFACE_PIN of the variant; GNC_P2_PARTS (mc,eval), GNC_P2_VARIANTS, GNC_P2_STATES,
GNC_P2_BASES, GNC_P2_BANDS ('v351=250:200;v351t=270:220'), GNC_P2_OUT (default out/rev4/p2).
SIM only; no physical validation."""
import gzip
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import time
from collections import OrderedDict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_rev3_fly as F3  # noqa: E402
from gncsim import run6 as R, sim6 as s6  # noqa: E402

F = F3.F
VERSION = "m2_rev4_p2 v1.0"
SP = "/home/claude/work/space"
OUT = os.environ.get("GNC_P2_OUT", f"{SP}/out/rev4/p2")
PARTS = os.environ.get("GNC_P2_PARTS", "mc,eval").split(",")
MASS = f"{SP}/out/rev4/mass_v351/mass_v351_vs_v3d.json"
REF_DIR = f"{SP}/out/rev3/fly"
HUBR3 = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev3"
RD_PATH = f"{SP}/gnc_dev6/scripts/m2_rev3_reserve_dip.py"
BASES = ("A1_none", "A1J_pc")
STATES = ("liq", "pw")
DEFAULT_BANDS = OrderedDict(v351=(250, 200), v351t=(270, 220), v352L=(270, 220))
ONSETS = OrderedDict([("flown_60g", None), ("125N_62g", 62.0), ("250N_69g", 69.0), ("500N_80g", 80.0)])
RULE_ONSETS = ("flown_60g", "250N_69g", "500N_80g")


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def _rd():
    spec = importlib.util.spec_from_file_location("m2_rev3_reserve_dip_v11", RD_PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def bands():
    out = OrderedDict((k, v) for k, v in DEFAULT_BANDS.items())
    for spec in [x for x in os.environ.get("GNC_P2_BANDS", "").split(";") if x.strip()]:
        k, v = spec.split("=")
        hi, lo = (int(x) for x in v.split(":"))
        out[k.strip()] = (hi, lo)
    return OrderedDict((k, list(range(hi, lo - 1, -5))) for k, (hi, lo) in out.items())


def variants():
    return json.load(open(MASS))["simulator"]["variants"]


def arm(st, v, h):
    return f"{st}|G73|{v}|h{h}"


def register():
    """Add the P2 v3.5.1 arms to m2_rev3_fly.ARMS (the rev3 fly() reads its spec from there)."""
    vs = variants()
    names = []
    for v, hs in bands().items():
        s = vs[v]
        for h in hs:
            for st in STATES:
                nm = arm(st, v, h)
                F3.ARMS[nm] = dict(state=st, purge="G73", plat="", bases=BASES,
                                   ex=dict(h_target=float(h), ballast=float(s["ballast_kg"]), ballast_z=float(s["ballast_z_m"])),
                                   iface=s["iface"], pin=s["pin"], group=f"P2_{v}", ref=f"{st}|G73|h285", variant=v)
                names.append(nm)
    return names


def part_mc():
    os.makedirs(os.path.join(OUT, "meta"), exist_ok=True)
    names = register()
    vsel = [x for x in os.environ.get("GNC_P2_VARIANTS", "v351").split(",") if x]
    ssel = [x for x in os.environ.get("GNC_P2_STATES", ",".join(STATES)).split(",") if x]
    bsel = [x for x in os.environ.get("GNC_P2_BASES", ",".join(BASES)).split(",") if x]
    iface = os.path.realpath(os.environ.get("GNC_IFACE", ""))
    pin = os.path.realpath(os.environ.get("GNC_IFACE_PIN", ""))
    p07z = F.engine_bay_mid()[0]
    mass_sha = sha16(MASS)
    print(f"{VERSION}: GNC_IFACE {iface}; pin {pin}; variants {vsel}; states {ssel}; bases {bsel}; mass file {mass_sha}",
          flush=True)
    for nm in names:
        spec = F3.ARMS[nm]
        if spec["variant"] not in vsel or spec["state"] not in ssel:
            continue
        if os.path.realpath(spec["iface"]) != iface or os.path.realpath(spec["pin"]) != pin:
            print(f"skip {nm}: needs GNC_IFACE {spec['iface']} and pin {spec['pin']}", flush=True)
            continue
        for base in bsel:
            p = os.path.join(OUT, F3.fname(base, nm))
            if os.path.exists(p) or os.path.exists(p + ".gz"):
                print("exists", base, nm, flush=True)
                continue
            t0 = time.time()
            rows, cfg = F3.fly(base, nm, p07z)
            F.M.write_csv(p, rows)
            with open(p, "rb") as fi, gzip.GzipFile(p + ".gz", "wb", mtime=0) as fo:
                fo.write(fi.read())
            os.remove(p)
            ok = np.array([r["ok"] for r in rows]) > 0.5
            ex = int(np.sum([r["exhausted"] > 0.5 for r in rows]))
            liq = 1e3 * np.array([r["liq_left"] for r in rows])
            meta = dict(version=VERSION, fly_loop=f"{F3.VERSION} fly() (unchanged)", base=base, arm=nm,
                        spec={k: v for k, v in spec.items() if k != "bases"}, cfg_extra=F3.cfg_extra(spec, p07z),
                        iface=iface, pin=pin, pin_sha16=sha16(pin), mech_sha16=sha16(os.path.join(iface, "mechanical.json")),
                        mass_file=dict(path=MASS, sha256_16=mass_sha), sim=s6.SIM6_VERSION, wall_s=round(time.time() - t0, 1),
                        P=float(ok.mean()), exhausted=ex, liq_left_g_p01_of_landed=(float(np.percentile(liq[ok], 1)) if ok.any() else None),
                        table_sha16=sha16(p + ".gz"))
            ms = variants()[spec["variant"]]
            want = json.load(open(MASS))["simulator"]["derived_mechanical_json"]["v352L" if spec["variant"] == "v352L" else "v351"]["sha256_16"]
            if meta["mech_sha16"] != want:
                raise RuntimeError(f"derived mechanical.json changed since m2_mass_v351 ({meta['mech_sha16']} != {want})")
            meta["variant"] = dict(name=spec["variant"], label=ms["label"], landing_mass_delta_kg=ms["landing_mass_delta_kg"])
            json.dump(meta, open(os.path.join(OUT, "meta", F3.fname(base, nm) + ".json"), "w"), indent=1)
            print(f"{base:9s} {nm:22s}: P {ok.mean():.3f} exhausted {ex} liq p01 {meta['liq_left_g_p01_of_landed']} g "
                  f"({time.time() - t0:.0f} s)", flush=True)


def ref_table(base, st):
    """rev3 v3d reference table, verified against the hub rev3 MANIFEST."""
    fn = F3.fname(base, f"{st}|G73|h285") + ".gz"
    p = os.path.join(REF_DIR, fn)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    man = {}
    for ln in open(os.path.join(HUBR3, "MANIFEST_rev3.sha256")):
        if ln.strip():
            a, b = ln.split(None, 1)
            man[b.strip().lstrip("*").lstrip("./")] = a
    if man.get(f"tables/fly/{fn}") != h:
        raise RuntimeError(f"reference {fn} does not match the hub rev3 MANIFEST")
    return p


def part_eval():
    RD = _rd()
    register()
    vs = variants()
    res = OrderedDict(version=VERSION, date=time.strftime("%Y-%m-%d"), sim=s6.SIM6_VERSION,
                      rule=("A1 apogee target = the highest 5 m band with no significant pooled loss (exact McNemar, pooled "
                            "A1_none + A1J_pc, lower with p < 0.05) against the v3d reference st|G73|h285, dip onset applied "
                            "to both tables; a band qualifies when it does not lose at the flown 60 g basis, 69 g and 80 g "
                            "(lead CHANGELOG 204 (3), rev3 reading); 62 g reported"),
                      mass_file=dict(path=MASS, sha256_16=sha16(MASS)),
                      reserve_dip_script=dict(path=RD_PATH, sha256_16=sha16(RD_PATH), version=RD.VERSION),
                      references={}, variants=OrderedDict())
    refs = {}
    for st in STATES:
        for b in BASES:
            p = ref_table(b, st)
            refs[(b, st)] = p
            res["references"][f"{b}|{st}"] = dict(path=p, sha256_16=sha16(p))
    for v, hs in bands().items():
        ve = OrderedDict(label=vs[v]["label"], landing_mass_delta_kg=vs[v]["landing_mass_delta_kg"],
                         ballast=[vs[v]["ballast_kg"], vs[v]["ballast_z_m"]], states=OrderedDict())
        for st in STATES:
            se = OrderedDict(bands=OrderedDict())
            for h in hs:
                nm = arm(st, v, h)
                paths = [os.path.join(OUT, F3.fname(b, nm) + ".gz") for b in BASES]
                if not all(os.path.exists(p) for p in paths):
                    continue
                e = OrderedDict(per_base=OrderedDict())
                for b, p in zip(BASES, paths):
                    rows = RD.load(p)
                    ok = np.array([float(r["ok"]) for r in rows]) > 0.5
                    exh = int(np.sum(np.array([float(r["exhausted"]) for r in rows]) > 0.5))
                    liq = 1e3 * np.array([float(r["liq_left"]) for r in rows])
                    e["per_base"][b] = dict(P=round(float(ok.mean()), 4), exhausted=exh,
                                            liq_left_landed_p01_g=(round(float(np.percentile(liq[ok], 1)), 1) if ok.any() else None),
                                            table_sha16=sha16(p))
                for k, on in ONSETS.items():
                    A, B = [], []
                    for b, p in zip(BASES, paths):
                        ra, runa, wa = RD.outcomes(refs[(b, st)], on)
                        rb, runb, wb = RD.outcomes(p, on)
                        if not (np.array_equal(runa, runb) and np.allclose(wa, wb)):
                            raise RuntimeError(f"not paired: {b} {nm} vs reference")
                        A.append(ra)
                        B.append(rb)
                    e[k] = RD.mcnemar(np.concatenate(A), np.concatenate(B))
                e["qualifies"] = bool(not any(e[k]["loses"] for k in RULE_ONSETS))
                se["bands"][h] = e
            q = [h for h, e in se["bands"].items() if e["qualifies"]]
            se["highest_qualifying_band_m"] = max(q) if q else None
            se["bands_flown"] = list(se["bands"])
            se["losing_bands"] = [h for h, e in se["bands"].items() if not e["qualifies"]]
            se["non_monotone"] = bool(q and any(h < max(q) for h in se["losing_bands"]))
            ve["states"][st] = se
        hq = [ve["states"][st]["highest_qualifying_band_m"] for st in STATES if st in ve["states"]]
        ve["band_all_states_m"] = (min(hq) if hq and all(x is not None for x in hq) else None)
        ve["no_band_at_or_above_200m"] = bool(all(x is None for x in hq)) if hq else None
        res["variants"][v] = ve
    p = os.path.join(OUT, "p2_v351.json")
    json.dump(res, open(p, "w"), indent=1, default=float)
    print("wrote", p, sha16(p))
    for v, ve in res["variants"].items():
        print(f"== {v} ({ve['label'][:60]}; +{ve['landing_mass_delta_kg']} kg): band all states {ve['band_all_states_m']}")
        for st, se in ve["states"].items():
            print(f"  {st}: highest qualifying {se['highest_qualifying_band_m']} losing {se['losing_bands']} "
                  f"non-monotone {se['non_monotone']}")
            for h, e in se["bands"].items():
                print(f"    h{h}: " + " | ".join(f"{k} {e[k]['P_case']:.3f}/{e[k]['P_ref']:.3f} -{e[k]['lost']}/+{e[k]['gained']} "
                                               f"p {e[k]['p_exact']:.3g}{' L' if e[k]['loses'] else ''}" for k in ONSETS)
                      + " | ex " + "/".join(str(e['per_base'][b]['exhausted']) for b in BASES))


if __name__ == "__main__":
    if "mc" in PARTS:
        part_mc()
    if "eval" in PARTS:
        part_eval()
