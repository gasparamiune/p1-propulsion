"""m2_b1_of_phases v1.0 (GNC rev2, 2026-10-13): per-phase O/F of the B1 duty-cycle records, for Combustion's revised T1-T4 spec
(lead line 172 (3): show that the default B1 grain gate errs safe in the low-O/F phases). Read-only export, no new flight:
the published gnc.json v3 B1 records (01-systems-gnc/duty_cycles/DC-B1_hop_85m_*_v3.csv, sha256 checked against
gnc.json v3 duty_cycles.current) and the v3.1 staging B1 62 m records (staging_v3.1/duty_cycles/DC-B1_hop_62m_*_v3.csv, sha256
from duty_cycles_records_b1_62m_v3.1.json when listed there).
Per record and sim6 phase code (1 ascent burn, 2 apex / post-MECO hold, 3 descent, 5 landing burn, 6 terminal, 7 cut; labels
read from the sim6 code): time span, time with fuel flow, oxidiser and fuel mass, mass-weighted O/F = sum(mdot_ox dt) /
sum(mdot_fuel dt), instantaneous O/F p01 / p50 / p99 / min / max over the samples with fuel flow > 1e-5 kg/s, mean thrust.
Tags: SIM (6-DOF record of the sim6 engine model: map O/F x the regression-law band of the record's draw), DERIVED (sums).
Output: out/rev2/b1_of/b1_of_phases.json and .csv"""
import csv
import glob
import hashlib
import json
import os
import numpy as np

HUB = "/home/claude/work/shared-fallback/engine"
OUT = os.environ.get("GNC_B1OF_OUT", "/home/claude/work/space/out/rev2/b1_of")
VERSION = "m2_b1_of_phases v1.0"
LAB = {0: "pad", 1: "ascent burn", 2: "apex / post-MECO hold", 3: "descent", 4: "relight command (A only)", 5: "landing burn",
       6: "terminal", 7: "cut"}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def known_hashes():
    h = {}
    g = json.load(open(f"{HUB}/interfaces/gnc.json"))
    for k, v in g["duty_cycles"]["v"]["current"].items():
        if isinstance(v, dict) and "file" in v:
            h[os.path.basename(v["file"])] = (v.get("sha256"), "gnc.json v3 duty_cycles.current." + k)
    p = f"{HUB}/01-systems-gnc/staging_v3.1/duty_cycles/duty_cycles_records_b1_62m_v3.1.json"
    if os.path.exists(p):
        txt = json.load(open(p))

        def walk(x):
            if isinstance(x, dict):
                f, s = x.get("file") or x.get("csv"), x.get("sha256")
                if f and s:
                    h[os.path.basename(f)] = (s, os.path.basename(p))
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
        walk(txt)
    return h


def one(p, kh):
    rows = list(csv.DictReader(open(p)))
    t = np.array([float(r["t_s"]) for r in rows])
    mo = np.array([float(r["mdot_ox_kgps"]) for r in rows])
    mf = np.array([float(r["mdot_fuel_kgps"]) for r in rows])
    F = np.array([float(r["F_N"]) for r in rows])
    ph = np.array([int(float(r["phase"])) for r in rows])
    dt = np.diff(np.concatenate([[0.0], t]))
    h = sha(p)
    exp = kh.get(os.path.basename(p))
    out = dict(file=p, sha256_16=h[:16], listed_in=(exp[1] if exp else None),
               hash_matches_listing=(None if not exp or not exp[0] else bool(str(exp[0]).startswith(h[:16]) or exp[0] == h)),
               phases={})
    for c in sorted(set(ph.tolist())):
        m = ph == c
        on = m & (mf > 1e-5)
        of = mo[on] / mf[on]
        e = dict(label=LAB.get(c, str(c)), t_start_s=float(t[m].min()), t_end_s=float(t[m].max()), fuel_flow_time_s=float(dt[on].sum()),
                 ox_kg=float(np.sum(mo[m] * dt[m])), fuel_kg=float(np.sum(mf[m] * dt[m])), mean_thrust_N=float(np.mean(F[m])))
        e["OF_mass_weighted"] = e["ox_kg"] / e["fuel_kg"] if e["fuel_kg"] > 0 else None
        if of.size:
            e.update(OF_p01=float(np.percentile(of, 1)), OF_p50=float(np.percentile(of, 50)), OF_p99=float(np.percentile(of, 99)),
                     OF_min=float(of.min()), OF_max=float(of.max()))
        out["phases"][str(c)] = e
    tot_o, tot_f = float(np.sum(mo * dt)), float(np.sum(mf * dt))
    out["whole_flight"] = dict(ox_kg=tot_o, fuel_kg=tot_f, OF_mass_weighted=tot_o / tot_f if tot_f > 0 else None)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    kh = known_hashes()
    files = sorted(glob.glob(f"{HUB}/01-systems-gnc/duty_cycles/DC-B1_*_v3.csv")) + \
        sorted(glob.glob(f"{HUB}/01-systems-gnc/staging_v3.1/duty_cycles/DC-B1_*_v3.csv"))
    res = dict(version=VERSION, date="2026-10-13", method=__doc__.split("\n\n")[0], tags="SIM records; DERIVED sums",
               records={os.path.basename(p): one(p, kh) for p in files})
    with open(os.path.join(OUT, "b1_of_phases.json"), "w") as f:
        json.dump(res, f, indent=1)
    with open(os.path.join(OUT, "b1_of_phases.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["record", "sha256_16", "phase", "label", "t_start_s", "t_end_s", "fuel_flow_time_s", "ox_kg", "fuel_kg",
                    "OF_mass_weighted", "OF_p01", "OF_p50", "OF_p99", "OF_min", "OF_max", "mean_thrust_N"])
        for n, r in res["records"].items():
            for c, e in r["phases"].items():
                w.writerow([n, r["sha256_16"], c, e["label"], round(e["t_start_s"], 3), round(e["t_end_s"], 3), round(e["fuel_flow_time_s"], 3),
                            round(e["ox_kg"], 4), round(e["fuel_kg"], 4)] +
                           [round(e[k], 3) if e.get(k) is not None else "" for k in ("OF_mass_weighted", "OF_p01", "OF_p50", "OF_p99", "OF_min", "OF_max")]
                           + [round(e["mean_thrust_N"], 1)])
    for n, r in res["records"].items():
        print(n, r["sha256_16"], "listed", r["hash_matches_listing"], {c: (e["label"], round(e["OF_mass_weighted"], 2) if e["OF_mass_weighted"] else None,
                                                                         round(e.get("OF_min", float("nan")), 2)) for c, e in r["phases"].items()})
    print("wrote", OUT)


if __name__ == "__main__":
    main()
