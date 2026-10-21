"""REV-GNC-6 v07: small additions to v04 and the comparison of the re-flown R2 starve JSON with the staged one.
 (1) [11] Fisher exact test of P(80 g) at touchdown mass >= 16.15 kg vs below, pooled over the two main bases per line
     state (unstratified; the bases are different vehicles flown on the same draw indices), and per mass bin pooled.
 (2) [14](b) exceedance probabilities of the frame-noise increase over the R2 v2 W10 < 6 margins (iid N(0, 5 N), flat
     signal; 50 frames for the 0.5 s window, 80 frames for 0.8 s).
 (3) [14](c) re-flown r2_starve.json (reviewer tree7 = staged gnc_dev7 with work paths redirected) vs the staged JSON:
     every released / aborted / landed count and release-time statistic.
 (4) [15] throat growth at the end of the flight and engine-on time of the payload options from the v04 result.
DERIVED.  Usage: python -I v07_extra.py <v04.json> <r2s_mine.json> <out.json>"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import rv6lib as L


def fisher2(a, b, c, d):
    """two-sided Fisher exact p for [[a, b], [c, d]] (same implementation as v04_items)."""
    r1, r2, c1, n = a + b, c + d, a + c, a + b + c + d

    def pr(x):
        return math.comb(r1, x) * math.comb(r2, c1 - x) / math.comb(n, c1)
    p0 = pr(a)
    lo, hi = max(0, c1 - r2), min(r1, c1)
    return min(1.0, sum(pr(x) for x in range(lo, hi + 1) if pr(x) <= p0 * (1 + 1e-9)))

V04, R2M, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
res = dict(script="v07_extra (REV-GNC-6)", tag="DERIVED")
v04 = json.load(open(V04))

# (1)
pool = {}
for st in ("liq", "pw"):
    a = b = c = d = 0
    for base in L.MAIN:
        g = v04["landing_mass_h210"][f"{base}|{st}"]["ge16p15_vs_lt"]
        a += g["ok_hi"]; b += g["fail_hi"]; c += g["ok_lo"]; d += g["fail_lo"]
    pool[st] = dict(ok_hi=a, fail_hi=b, ok_lo=c, fail_lo=d, P_hi=round(a / (a + b), 4), P_lo=round(c / (c + d), 4),
                    fisher_p=float(f"{fisher2(a, b, c, d):.4g}"))
res["landing_mass_pooled_bases"] = pool

# (2)
rng = np.random.default_rng(20261019)
exc = {}
for nfr, marg in ((50, 37.16 - 31.18), (80, 37.16 - 31.86), (50, 37.16 - 20.85)):
    x = rng.normal(0.0, 5.0, size=(100000, nfr))
    m3 = np.minimum(np.minimum(x[:, :-2], x[:, 1:-1]), x[:, 2:]).max(axis=1)
    exc[f"{nfr}fr|margin{marg:.2f}N"] = dict(P_exceed=round(float(np.mean(m3 > marg)), 4), p50=round(float(np.median(m3)), 3),
                                            p99=round(float(np.percentile(m3, 99)), 3))
res["r2_noise_exceedance"] = exc

# (3)
st = json.load(open(f"{L.R4}/out_rev4/r2_starve/r2_starve.json"))
mine = json.load(open(R2M)) if os.path.exists(R2M) else None
cmpr = dict(available=mine is not None)
if mine:
    nd, first = 0, []
    for w, c in st["cases"].items():
        for k, v in c["by_st_T"].items():
            for sub in ("all", "W10lt6"):
                a, b = v[sub], mine["cases"][w]["by_st_T"][k][sub]
                for kk in a:
                    x, y = a[kk], b[kk]
                    eq = (x == y) or (isinstance(x, float) and isinstance(y, float) and abs(x - y) < 1e-9)
                    if not eq:
                        nd += 1
                        first.append([w, k, sub, kk, x, y])
        if c.get("starve_threshold_s") != mine["cases"][w].get("starve_threshold_s"):
            nd += 1
            first.append([w, "threshold", c.get("starve_threshold_s"), mine["cases"][w].get("starve_threshold_s")])
    cmpr.update(n_values_differing=nd, first=first[:10], settings_equal=(st["settings"] == mine["settings"]),
                sim_equal=(st["sim"] == mine["sim"]), N=[st["N"], mine["N"]], wall_s_mine=mine.get("wall_s"),
                thresholds_mine={w: c.get("starve_threshold_s") for w, c in mine["cases"].items()})
res["r2_starve_refly_vs_staged"] = cmpr

# (4)
opt = {}
for k, e in v04["payload"]["arms"].items():
    if k in ("pl0|h210|m2.00|n500", "pl1|h210|m2.20|n500", "pl2|h210|m2.45|n500", "pl2|h210|m2.55|n500", "pl0.5|h190|m2.00|n500"):
        opt[k] = {b: dict(burn_time=e[b]["burn_time"], throat_g_end_p99=e[b]["throat_g_end_p99"], m_land_p50=e[b]["m_land_p50"],
                          liq_left_p50_g=e[b]["liq_left_p50_g"], max_tilt_land_p99=e[b]["max_tilt_land_p99"]) for b in L.MAIN}
res["payload_options"] = opt
json.dump(res, open(OUT, "w"), indent=1, default=str)
print(json.dumps(res, default=str)[:6000])
