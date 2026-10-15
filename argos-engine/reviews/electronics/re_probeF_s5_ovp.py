"""REV-ELEC-1 probe F analysis: S5 high-overshoot runs re-run with 'sil mcone' on the published v2.9 build (base, 3 ms) and on a copy
with the 30 bar firmware abort persistence at 5 ms on the FILTERED channel (ovp5) and on the RAW channel (ovp5raw; CHANGELOG l.160
item 2 wording).
Reads <scratch>/outF_{base,ovp5,ovp5raw}/S5_mc_run<k>.csv (written by re_build_ovp5.sh) and writes re_probeF_s5_ovp.{json,txt} here.
Columns used: t, Pc (plant chamber pressure, Pa abs), Pc_meas (ECU filtered Pc, Pa abs, sim.cpp l.345), Pc_xdcr (transducer output),
Pc_sp (ECU setpoint), state, abort.  Usage: python -I re_probeF_s5_ovp.py <scratch_dir>
"""
import csv, json, sys, os, hashlib

S = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = [12, 92, 107, 127, 140, 174, 215, 281, 283, 286, 290]
THR = 30.0e5


def longest(ts, flags):
    best = cur = 0.0
    prev_t = None
    for t, f in zip(ts, flags):
        if f:
            cur = cur + (t - prev_t if prev_t is not None and cur > 0 else 0.001)
            best = max(best, cur)
        else:
            cur = 0.0
        prev_t = t
    return best


out = {"id": "re_probeF_s5_ovp", "review": "REV-ELEC-1", "tag": "SIM (v2.9 SIL plant, ASSUMED dispersions as published)",
       "threshold_abs_Pa": THR, "runs": {}}
PUB = "/home/claude/work/shared-fallback/engine/06-electronics/results/sil_v2p9/S5_mc.csv"
with open(PUB) as f:
    span = {int(r["run"]): float(r["span_err"]) for r in csv.DictReader(f)}
for v in ("base", "ovp5", "ovp5raw"):
    for k in RUNS:
        p = os.path.join(S, "outF_%s" % v, "S5_mc_run%d.csv" % k)
        with open(p) as f:
            rows = list(csv.DictReader(f))
        t = [float(r["t"]) for r in rows]
        pc = [float(r["Pc"]) for r in rows]
        pm = [float(r["Pc_meas"]) for r in rows]
        px = [float(r["Pc_xdcr"]) for r in rows]
        sp = [float(r["Pc_sp"]) for r in rows]
        ab = [int(float(r["abort"])) for r in rows]
        # window of the 100 -> 500 N up-step (3.0 s to 4.2 s)
        w = [i for i, x in enumerate(t) if 3.0 <= x < 4.2]
        tw = [t[i] for i in w]
        first_ab = next((t[i] for i, a in enumerate(ab) if a), None)
        rec = {
            "plant_Pc_max_bar_abs": round(max(pc[i] for i in w) / 1e5, 3),
            "filtered_Pc_meas_max_bar_abs": round(max(pm[i] for i in w) / 1e5, 3),
            "xdcr_Pc_max_bar": round(max(px[i] for i in w) / 1e5, 3),
            "setpoint_max_bar_abs": round(max(sp[i] for i in w) / 1e5, 3),
            "plant_time_above_30_ms": round(1e3 * longest(tw, [pc[i] > THR for i in w]), 1),
            "filtered_time_above_30_ms": round(1e3 * longest(tw, [pm[i] > THR for i in w]), 1),
            "plant_time_above_25_ms": round(1e3 * longest(tw, [pc[i] > 25.0e5 for i in w]), 1),
            "first_abort_t_s": first_ab,
            "pc_span_err": span[k],
            "csv_sha256_16": hashlib.sha256(open(p, "rb").read()).hexdigest()[:16],
        }
        out["runs"]["%s_run%d" % (v, k)] = rec

lines = ["REV-ELEC-1 probe F: S5 high-overshoot runs (plant Pc max >= 29.5 bar abs in S5_mc.csv), up-step window 3.0-4.2 s",
         "build    run  plantPcmax filtPcmax xdcrmax  spmax  plant>30ms filt>30ms  span_err  abort_t"]
for key, r in out["runs"].items():
    v, k = key.split("_run")
    lines.append("%-7s %4s  %9.3f %9.3f %7.3f %6.3f %10.1f %9.1f  %+8.5f  %s" % (
        v, k, r["plant_Pc_max_bar_abs"], r["filtered_Pc_meas_max_bar_abs"], r["xdcr_Pc_max_bar"], r["setpoint_max_bar_abs"],
        r["plant_time_above_30_ms"], r["filtered_time_above_30_ms"], r["pc_span_err"], r["first_abort_t_s"]))
json.dump(out, open(os.path.join(HERE, "re_probeF_s5_ovp.json"), "w"), indent=1)
open(os.path.join(HERE, "re_probeF_s5_ovp.txt"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
