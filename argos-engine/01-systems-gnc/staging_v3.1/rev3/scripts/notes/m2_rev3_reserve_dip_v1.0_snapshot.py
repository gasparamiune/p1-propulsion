"""m2_rev3_reserve_dip v1.0 (GNC rev3, 2026-10-13): effect of the tank-outlet dip onset on the landing usable reserve and on P
(lead CHANGELOG line 194 (6), REV-COMB-3 R3-17), for every rev3 A1 flight table already flown (no re-fly).

The flights stop the thrust when the liquid reaches the sim6 unusable residual, 3 % of the liquid at t0 (ASSUMED; 60 g for
the 2.00 kg load: GNC rev1). REV-COMB-3 R3-17 (DERIVED; same correlation as Combustion, centre outlet, flat bulkhead, no
tilt, g' bounded below by F / 13.6706 kg) puts the dip onset at 60-62 g of liquid at 125 N, 68-69 g at 250 N and 78-80 g at
500 N. The outlet geometry is MISSING (Mechanical OI-32). The tables carry the liquid left at the end of the flight but no
thrust history, so the onset that applies near touchdown is bracketed: 62 g (125 N, about the hover thrust at the landing
mass), 69 g (250 N), 80 g (500 N, upper). A run that landed successfully with liquid left below the onset would have reached
the dip before touchdown; it is counted LOST in the adjusted P (conservative: a dip near touchdown is not shown to be
survivable). Usable reserve = liquid left - onset. DERIVED from SIM tables; the onset is DERIVED by the reviewer; no hardware
data; not a physical approval.
Output: <out>/reserve_dip.json; the log lists every arm."""
import csv
import glob
import gzip
import hashlib
import json
import os
from collections import OrderedDict
import numpy as np

VERSION = "m2_rev3_reserve_dip v1.0"
OUT = os.environ.get("GNC_REV3_OUT", "/home/claude/work/space/out/rev3/fly")
ONSETS = OrderedDict([("125N_62g", 62.0), ("250N_69g", 69.0), ("500N_80g", 80.0)])
R3T = "/home/claude/work/shared-fallback/engine/reviews/combustion/r3/r3_tank_outlet.json"
R3T_SHA16 = "1a15375ee2057478"


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def load(p):
    op = gzip.open if p.endswith(".gz") else open
    with op(p, "rt") as f:
        return list(csv.DictReader(f))


def main():
    if sha16(R3T) != R3T_SHA16:
        raise RuntimeError(f"{R3T} sha256/16 {sha16(R3T)} != pinned {R3T_SHA16}")
    out = OrderedDict(version=VERSION, date="2026-10-13", method=__doc__.split("\n\n")[1].strip(),
                      sources=OrderedDict(onsets="REV-COMB-3 R3-17 (reviews/REVIEW-COMBUSTION-R3.md a786101f28d45d6f); lead "
                                                 "CHANGELOG line 194 (6)", reviewer_tank_outlet=f"{R3T} ({R3T_SHA16})",
                                          tables=OUT),
                      onsets_g=ONSETS, arms=OrderedDict())
    files = sorted(set(glob.glob(os.path.join(OUT, "rf_A1*.csv")) + glob.glob(os.path.join(OUT, "rf_A1*.csv.gz"))))
    for p in files:
        name = os.path.basename(p).replace(".csv.gz", "").replace(".csv", "")[3:]
        rows = load(p)
        if not rows or "liq_left" not in rows[0]:
            continue
        ok = np.array([float(r["ok"]) for r in rows]) > 0.5
        liq = 1e3 * np.array([float(r["liq_left"]) for r in rows])
        m0 = 1e3 * np.array([float(r["m_n2o"]) for r in rows])
        ex = np.array([float(r["exhausted"]) for r in rows]) > 0.5
        old = liq - 0.03 * m0
        e = OrderedDict(table=dict(path=p, sha256_16=sha16(p)), n=len(rows), P_flown=round(float(ok.mean()), 4),
                        exhausted=int(ex.sum()), residual_flown_g=round(float(np.median(0.03 * m0)), 1),
                        usable_flown_basis_g=OrderedDict(p01=round(float(np.percentile(old[ok], 1)), 1) if ok.any() else None,
                                                         min=round(float(old[ok].min()), 1) if ok.any() else None))
        for k, on in ONSETS.items():
            u = liq - on
            lost = ok & (u < 0.0)
            e[k] = OrderedDict(P_adjusted=round(float((ok & ~lost).mean()), 4), lost_to_dip=int(lost.sum()),
                               usable_p01_g=round(float(np.percentile(u[ok], 1)), 1) if ok.any() else None,
                               usable_min_g=round(float(u[ok].min()), 1) if ok.any() else None)
        out["arms"][name] = e
    p = os.path.join(OUT, "reserve_dip.json")
    json.dump(out, open(p, "w"), indent=1)
    print("wrote", p, sha16(p), "arms", len(out["arms"]))
    print(f"{'arm':44s} {'P':>6s} ex  | usable(60 g) p01/min | " + " | ".join(f"{k}: P_adj lost u_min" for k in ONSETS))
    for k, e in out["arms"].items():
        u = e["usable_flown_basis_g"]
        print(f"{k:44s} {e['P_flown']:.3f} {e['exhausted']:3d} | {u['p01']!s:>7}/{u['min']!s:>7} | " +
              " | ".join(f"{e[o]['P_adjusted']:.3f} {e[o]['lost_to_dip']:3d} {e[o]['usable_min_g']!s:>6}" for o in ONSETS))


if __name__ == "__main__":
    main()
