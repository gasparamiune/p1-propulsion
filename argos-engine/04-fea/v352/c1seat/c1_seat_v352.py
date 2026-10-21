#!/usr/bin/env python3
"""c1_seat_v352.py -- F1 (lead routing 2026-10-21T07:37:34Z / 07:54:43Z).
C1 seat-mounted Pc transducer (1/8-27 NPT seat, r 25 mm on the TC-02 head top, LEAD 205):
metal temperature history at the diaphragm depth (r 25.0, z zt - 9.5) and at nearby depths,
from the EXISTING v352 SIM thermal runs (CalculiX CAX6, .frd.gz).  No new FE, no ccx.
Read-only on the run folders; writes c1_seat_v352_v1.json next to this script.
Tags: values are [SIM] (FE nodal results) interpolated [DERIVED] in space (CAX6 quadratic
shape functions) and time (linear between frd frames); bar shifts use the C1 thermal-zero
coefficient 0.0248 bar/K typical [DATASHEET] x k [ASSUMED sweep], maximum MISSING (F-10)."""
import gzip, json, glob, hashlib, os, bisect, math

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = "/home/claude/work/mechanical/runs/thermal"
RUNSET = [("A1_NF2b", "DC-A1dispp99_tg711_hi_SS316L_L2.5_v352_NF2b"),
          ("B1_R4_GVLO", "DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_R4_GVLO"),
          ("B1_R4_GVHI", "DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_R4_GVHI")]
# points (r, dz from zt): diaphragm at the bottom of the 8.7 x 10 tap drill (zt - 9.5)
PTS = [("diaphragm_zt-9.5", 25.0, -9.5), ("zt-8.0", 25.0, -8.0), ("zt-11.0", 25.0, -11.0),
       ("tap_mid_zt-4.75", 25.0, -4.75), ("tap_mouth_zt-0.5", 25.0, -0.5)]
MON = ["T1_head_top_bracket_foot", "head_bore_N2O", "head_top_r12"]
C1_BAR_PER_K = 0.0248
KS = [1.0, 1.5, 2.0, 3.0]
COAST_A1 = 22.211 - 3.541   # A1 coast MECO -> E0 [SIM timeline, reviewer r3_01]


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


def read_inp(p):
    nodes, elems, mode, eset = {}, [], None, None
    with open(p) as f:
        for line in f:
            if line.startswith("**"):
                continue
            if line.startswith("*"):
                u = line.upper().replace(" ", "")
                if u.startswith("*NODE,") or u.strip() == "*NODE":
                    mode = "N"
                elif u.startswith("*ELEMENT"):
                    mode = "E" if "TYPE=CAX6" in u else None
                    eset = None
                    for part in line.strip().split(","):
                        kv = part.strip()
                        if kv.upper().startswith("ELSET="):
                            eset = kv[6:].strip()
                else:
                    mode = None
                continue
            if mode == "N":
                a = line.split(",")
                nodes[int(a[0])] = (float(a[1]), float(a[2]))
            elif mode == "E":
                a = [int(x) for x in line.replace(",", " ").split()]
                assert len(a) == 7, line
                elems.append((a[0], eset, a[1:7]))
    return nodes, elems


def locate(nodes, elems, r, z):
    hits = []
    for eid, es, nn in elems:
        (x1, y1), (x2, y2), (x3, y3) = nodes[nn[0]], nodes[nn[1]], nodes[nn[2]]
        if (r < min(x1, x2, x3) - 1e-9 or r > max(x1, x2, x3) + 1e-9 or
                z < min(y1, y2, y3) - 1e-9 or z > max(y1, y2, y3) + 1e-9):
            continue
        det = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
        L1 = ((y2 - y3) * (r - x3) + (x3 - x2) * (z - y3)) / det
        L2 = ((y3 - y1) * (r - x3) + (x1 - x3) * (z - y3)) / det
        L3 = 1.0 - L1 - L2
        if min(L1, L2, L3) >= -1e-9:
            dev = 0.0
            for (a, b, m) in ((0, 1, 3), (1, 2, 4), (2, 0, 5)):
                pa, pb, pm = nodes[nn[a]], nodes[nn[b]], nodes[nn[m]]
                dev = max(dev, math.hypot(pm[0] - (pa[0] + pb[0]) / 2, pm[1] - (pa[1] + pb[1]) / 2))
            w = [L1 * (2 * L1 - 1), L2 * (2 * L2 - 1), L3 * (2 * L3 - 1), 4 * L1 * L2, 4 * L2 * L3, 4 * L3 * L1]
            hits.append({"elem": eid, "elset": es, "nodes": nn, "L": [L1, L2, L3], "w": w,
                         "midside_dev_mm": dev})
    return hits


def stream_frd(p, need):
    keys = {"%10d" % n: n for n in need}
    times, vals, cur, cur_t, in_t = [], {n: [] for n in need}, {}, None, False
    with gzip.open(p, "rt", errors="replace") as f:
        for line in f:
            if line.startswith(" -1"):
                if in_t:
                    n = keys.get(line[3:13])
                    if n is not None:
                        cur[n] = float(line[13:25])
                continue
            if line.startswith("  100CL"):
                cur_t = float(line.split()[2])
                in_t = False
            elif line.startswith(" -4"):
                in_t = line.split()[1].startswith("NDTEMP")
                cur = {}
            elif line.startswith(" -3"):
                if in_t:
                    times.append(cur_t)
                    for n in need:
                        vals[n].append(cur.get(n, float("nan")))
                in_t = False
    return times, vals


def interp(ts, vs, t):
    i = bisect.bisect_left(ts, t)
    if i < len(ts) and abs(ts[i] - t) < 1e-9:
        return vs[i]
    if i == 0 or i >= len(ts):
        return float("nan")
    t0, t1 = ts[i - 1], ts[i]
    if t1 == t0:
        return vs[i]
    return vs[i - 1] + (vs[i] - vs[i - 1]) * (t - t0) / (t1 - t0)


def read_mon(p):
    rows, hdr = [], None
    with open(p) as f:
        for line in f:
            if line.startswith("t_s,"):
                hdr = line.strip().split(",")
                continue
            if hdr is None or line.startswith("#") or not line.strip():
                continue
            rows.append([float(x) for x in line.strip().split(",")])
    return hdr, rows


def events_for(tag, meta):
    S = meta["t_last_shutdown_s"]
    if tag.startswith("A1"):
        ev = [("ARM", 0.001), ("MECO", 3.541), ("rezero1_start_COAST+1.0s", 4.541),
              ("rezero1_end_COAST+1.4s", 4.941), ("rezero2_end", 19.261), ("PURGE_cmd", 19.311),
              ("E0", 22.211), ("E1", 22.256), ("light", 22.571), ("shutdown2", S)]
    else:
        ev = [("ARM", 0.001), ("first_light_rise_by_construction", 0.361), ("shutdown", S),
              ("rezero1_start_S+1.0s", S + 1.0), ("rezero1_end_S+1.4s", S + 1.4),
              ("S+5s", S + 5), ("S+10s", S + 10),
              ("stand_rezero2_end_S+15.72s", S + (19.261 - 3.541)),
              ("stand_PURGE_cmd_S+15.77s", S + (19.311 - 3.541)),
              ("stand_E0_S+18.67s", S + COAST_A1), ("stand_E1_S+18.715s", S + COAST_A1 + 0.045),
              ("stand_light_S+19.03s", S + COAST_A1 + 0.36),
              ("S+30s", S + 30), ("S+60s", S + 60), ("S+120s", S + 120), ("S+300s", S + 300),
              ("S+600s", S + 600)]
    return ev


def drifts_for(tag):
    if tag.startswith("A1"):
        return [("ARM->rezero1_end", "ARM", "rezero1_end_COAST+1.4s"),
                ("rezero1_end->rezero2_end", "rezero1_end_COAST+1.4s", "rezero2_end"),
                ("rezero1_end->E1", "rezero1_end_COAST+1.4s", "E1"),
                ("rezero1_end->light", "rezero1_end_COAST+1.4s", "light"),
                ("rezero2_end->E1", "rezero2_end", "E1"),
                ("rezero2_end->light", "rezero2_end", "light"),
                ("ARM->E1", "ARM", "E1"), ("ARM->light", "ARM", "light")]
    return [("ARM->rezero1_end", "ARM", "rezero1_end_S+1.4s"),
            ("rezero1_end->stand_rezero2_end", "rezero1_end_S+1.4s", "stand_rezero2_end_S+15.72s"),
            ("rezero1_end->stand_E1", "rezero1_end_S+1.4s", "stand_E1_S+18.715s"),
            ("rezero1_end->stand_light", "rezero1_end_S+1.4s", "stand_light_S+19.03s"),
            ("stand_rezero2_end->stand_E1", "stand_rezero2_end_S+15.72s", "stand_E1_S+18.715s"),
            ("stand_rezero2_end->stand_light", "stand_rezero2_end_S+15.72s", "stand_light_S+19.03s"),
            ("ARM->stand_E1", "ARM", "stand_E1_S+18.715s"),
            ("ARM->stand_light", "ARM", "stand_light_S+19.03s")]


def main():
    out = {"script": "c1_seat_v352.py", "basis": "existing v352 SIM thermal runs, no new FE",
           "C1_bar_per_K_typ": C1_BAR_PER_K, "k_sweep": KS, "runs": {}}
    for tag, d in RUNSET:
        D = os.path.join(RUNS, d)
        inp = glob.glob(D + "/*.inp")[0]
        frd = glob.glob(D + "/*.frd.gz")[0]
        metap = glob.glob(D + "/*_meta.json")[0]
        monp = os.path.join(D, "monitors.csv")
        meta = json.load(open(metap))
        mons = {m[0]: m for m in meta["monitors"]}
        zt = mons["T1_head_top_bracket_foot"][3]
        nodes, elems = read_inp(inp)
        pts = {}
        need = set()
        for name, r, dz in PTS:
            h = locate(nodes, elems, r, zt + dz)
            assert h, (tag, name)
            pts[name] = {"r": r, "z": zt + dz, "hits": [{k: v for k, v in x.items()} for x in h]}
            need.update(h[0]["nodes"])
        for mname in MON:
            need.add(mons[mname][1])
        ts, vals = stream_frd(frd, sorted(need))
        assert all(ts[i] <= ts[i + 1] for i in range(len(ts) - 1)), "frd times not monotone"
        hist = {}
        for name in pts:
            h0 = pts[name]["hits"][0]
            hist[name] = [sum(w * vals[n][j] for w, n in zip(h0["w"], h0["nodes"])) for j in range(len(ts))]
        for mname in MON:
            hist["MON_" + mname] = vals[mons[mname][1]]
        # cross-check frd monitor nodes vs monitors.csv at frd times
        hdr, rows = read_mon(monp)
        mt = [row[0] for row in rows]
        xc = {}
        for mname in MON:
            ci = hdr.index(mname)
            mv = [row[ci] for row in rows]
            diffs = [abs(interp(mt, mv, t) - v) for t, v in zip(ts, vals[mons[mname][1]])
                     if not math.isnan(interp(mt, mv, t))]
            xc[mname] = {"node": mons[mname][1], "r": mons[mname][2], "z": mons[mname][3],
                         "max_abs_diff_K_frd_vs_monitors_csv": max(diffs) if diffs else None,
                         "n_compared": len(diffs)}
        ev = events_for(tag, meta)
        evt = {}
        for lab, t in ev:
            evt[lab] = {"t_s": t}
            for name, hv in hist.items():
                evt[lab][name] = interp(ts, hv, t)
        T_arm = {name: evt["ARM"][name] for name in hist}
        rises = {lab: {name: evt[lab][name] - T_arm[name] for name in hist} for lab in evt}
        dr = {}
        for lab, a, b in drifts_for(tag):
            dr[lab] = {}
            for name in hist:
                dT = evt[b][name] - evt[a][name]
                dr[lab][name] = {"dT_K": dT, "bar_shift_by_k": {str(k): C1_BAR_PER_K * k * dT for k in KS}}
        dmax = max(range(len(ts)), key=lambda j: hist["diaphragm_zt-9.5"][j])
        out["runs"][tag] = {
            "dir": d, "inp_sha16": sha16(inp), "frd_gz_sha16": sha16(frd), "meta_sha16": sha16(metap),
            "monitors_csv_sha16": sha16(monp), "zt_mm": zt, "t_last_shutdown_s": meta["t_last_shutdown_s"],
            "segments_s": meta.get("segments_s"), "soak_end_s": meta.get("soak_end_s"),
            "bound": meta.get("bound"), "gap_variant": meta.get("gap_variant"),
            "n_frames": len(ts), "t_first": ts[0], "t_last": ts[-1],
            "points": pts, "monitor_crosscheck": xc,
            "T_K_at_events": evt, "rise_K_vs_ARM": rises, "drifts": dr,
            "diaphragm_max": {"T_K": hist["diaphragm_zt-9.5"][dmax], "t_s": ts[dmax],
                              "rise_K": hist["diaphragm_zt-9.5"][dmax] - T_arm["diaphragm_zt-9.5"]},
            "history_diaphragm": [[round(t, 4), round(v, 3)] for t, v in zip(ts, hist["diaphragm_zt-9.5"])],
        }
        print("RUN", tag, "zt", zt, "frames", len(ts), ts[0], ts[-1], "xc", {k: v["max_abs_diff_K_frd_vs_monitors_csv"] for k, v in xc.items()})
        for name in pts:
            h0 = pts[name]["hits"][0]
            print("  PT", name, "elem", h0["elem"], h0["elset"], "nhits", len(pts[name]["hits"]),
                  "sets", sorted(set(x["elset"] for x in pts[name]["hits"])), "dev", round(h0["midside_dev_mm"], 6))
        for lab in evt:
            print("  EV %-34s t %9.3f  dia %.3f K rise %+.3f | zt-8 %+.3f zt-11 %+.3f mid %+.3f mouth %+.3f | foot %+.3f bore %+.3f r12 %+.3f" % (
                lab, evt[lab]["t_s"], evt[lab]["diaphragm_zt-9.5"], rises[lab]["diaphragm_zt-9.5"],
                rises[lab]["zt-8.0"], rises[lab]["zt-11.0"], rises[lab]["tap_mid_zt-4.75"], rises[lab]["tap_mouth_zt-0.5"],
                rises[lab]["MON_T1_head_top_bracket_foot"], rises[lab]["MON_head_bore_N2O"], rises[lab]["MON_head_top_r12"]))
        for lab in dr:
            print("  DR %-32s dia %+.4f K (k1 %+.4f bar, k3 %+.4f bar) | foot %+.4f bore %+.4f" % (
                lab, dr[lab]["diaphragm_zt-9.5"]["dT_K"], dr[lab]["diaphragm_zt-9.5"]["bar_shift_by_k"]["1.0"],
                dr[lab]["diaphragm_zt-9.5"]["bar_shift_by_k"]["3.0"],
                dr[lab]["MON_T1_head_top_bracket_foot"]["dT_K"], dr[lab]["MON_head_bore_N2O"]["dT_K"]))
        print("  MAX diaphragm", out["runs"][tag]["diaphragm_max"])
    op = os.path.join(HERE, "c1_seat_v352_v1.json")
    with open(op, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print("WROTE", op, sha16(op), os.path.getsize(op))


if __name__ == "__main__":
    main()
