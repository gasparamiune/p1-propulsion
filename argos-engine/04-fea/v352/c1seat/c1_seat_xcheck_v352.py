#!/usr/bin/env python3
"""c1_seat_xcheck_v352.py -- F1 cross-check (lead brief 2026-10-21T08:05:00Z, F1 caveat 3).
The F1 script (c1_seat_v352.py fe1f41a73f25a0bc, json c1_seat_v352_v1.json) compared its frd 'monitor' nodes with monitors.csv and found
differences up to 0.35 / 1.76 / 0.91 K (A1: foot / bore / r12) and 0.58 / 3.44 / 1.36 K (B1); F1 carried an extraction caveat of +/-0.6 K.
The lead asked: re-stream one frd for nodes 236 / 206 (A1), locate the time of the maximum difference, compare with the .dat NODE PRINT
times, and report whether the frd frame time or the monitors.csv time is shifted.
This script, read-only on the run folders (no new FE, no ccx):
 (1) node numbering: the run meta lists each monitor with a node number one LESS than the node at the stated (r, z) in the .inp; the NMON
     set and the .dat NODE PRINT use the .inp numbers (meta + 1) in the meta's order; monitors.csv is the .dat NODE PRINT.  This is the
     thermal writer's convention (04-fea/thermal/ax_thermal.py: the meta keeps the 0-based mesh index k, the NMON set is written as k + 1
     and read_monitors adds 1); c1_seat_v352.py took the meta number as an frd node ID;
 (2) streams each frd for the meta nodes (m), the true monitor nodes (m + 1) and the F1 seat-point element nodes;
 (3) frame times: frd frames against the .dat print times;
 (4) values: frd(m + 1) against the .dat / monitors.csv at the same time, frd(m) against monitors.csv (the F1 comparison, reproduced) with
     the time of the largest difference;
 (5) F1 seat values: the diaphragm and depth points recomputed from this stream with F1's own weights (element connectivity from the .inp,
     so not affected) and compared with c1_seat_v352_v1.json;
 (6) F1's MON_ proxy columns (taken at node m) re-stated at the monitor node (m + 1): every drift that moves, with the change.
Tags: SIM values (FE nodal results), DERIVED comparisons.  Writes c1_seat_xcheck_v352_v1.json next to this script.
usage: python3 -B -I c1_seat_xcheck_v352.py
"""
import bisect, glob, hashlib, json, math, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c1_seat_v352 as F1                                       # read_inp, stream_frd, interp, read_mon, events_for, drifts_for (same code path)

F1_PY, F1_JSON = os.path.join(HERE, "c1_seat_v352.py"), os.path.join(HERE, "c1_seat_v352_v1.json")
F1_PY_SHA, F1_JSON_SHA = "fe1f41a73f25a0bc", None
MON = F1.MON


def sha16(p):
    return F1.sha16(p)


def read_nmon(inp):
    """the *NSET, NSET=NMON node list in file order"""
    out, on = [], False
    with open(inp) as f:
        for line in f:
            if line.startswith("*"):
                on = line.upper().replace(" ", "").startswith("*NSET,NSET=NMON")
                continue
            if on and line.strip() and not line.startswith("**"):
                out += [int(x) for x in line.replace(",", " ").split()]
    return out


def read_dat(p, nodes):
    """NODE PRINT temperatures for set NMON: list of times and {node: [T]}"""
    times, vals, cur_t, on = [], {n: [] for n in nodes}, None, False
    rx = re.compile(r"temperatures for set NMON and time\s+(\S+)")
    with open(p) as f:
        for line in f:
            m = rx.search(line)
            if m:
                cur_t = float(m.group(1)); times.append(cur_t); on = True
                for n in nodes:
                    vals[n].append(float("nan"))
                continue
            if on:
                a = line.split()
                if len(a) == 2 and a[0].isdigit():
                    n = int(a[0])
                    if n in vals:
                        vals[n][-1] = float(a[1])
                elif a and not a[0].isdigit():
                    on = False
    return times, vals


def main():
    t0 = time.time()
    assert sha16(F1_PY) == F1_PY_SHA, "F1 script changed"
    AXT = "/home/claude/work/shared-fallback/engine/04-fea/thermal/ax_thermal.py"
    axt = open(AXT).read()
    assert sha16(AXT) == "cd00f37a02ddbfd2" and '"\\n".join(str(k + 1) for _, k, *_ in mon)' in axt and "ids.setdefault(k + 1, []).append(nm)" in axt
    f1 = json.load(open(F1_JSON))
    out = {"script": "c1_seat_xcheck_v352.py", "date": "2026-10-21", "owner": "mechanical",
           "basis": __doc__.strip(), "inputs": {"c1_seat_v352.py": F1_PY_SHA, "c1_seat_v352_v1.json": sha16(F1_JSON), "ax_thermal.py (hub)": "cd00f37a02ddbfd2"},
           "root_cause": ("04-fea/thermal/ax_thermal.py (hub cd00f37a02ddbfd2) writes the NMON set as k + 1 and read_monitors adds 1: the meta 'monitors' node "
                          "field is the 0-based mesh index; c1_seat_v352.py (fe1f41a73f25a0bc) used it as the 1-based frd node ID for its MON_ columns and the "
                          "cross-check; its seat points take their nodes from the .inp element connectivity and are not affected"), "runs": {}}
    for tag, d in F1.RUNSET:
        D = os.path.join(F1.RUNS, d)
        inp = glob.glob(D + "/*.inp")[0]; frd = glob.glob(D + "/*.frd.gz")[0]; dat = glob.glob(D + "/*.dat")[0]
        metap = glob.glob(D + "/*_meta.json")[0]; monp = os.path.join(D, "monitors.csv")
        f1r = f1["runs"][tag]
        shas = {"inp": sha16(inp), "frd_gz": sha16(frd), "dat": sha16(dat), "meta": sha16(metap), "monitors_csv": sha16(monp)}
        assert (shas["inp"], shas["frd_gz"], shas["meta"], shas["monitors_csv"]) == (f1r["inp_sha16"], f1r["frd_gz_sha16"], f1r["meta_sha16"], f1r["monitors_csv_sha16"]), (tag, shas)
        meta = json.load(open(metap))
        nodes, elems = F1.read_inp(inp)
        nmon = read_nmon(inp)
        mlist = meta["monitors"]
        # (1) numbering
        assert len(nmon) == len(mlist)
        off = [nm - m[1] for nm, m in zip(nmon, mlist)]
        numbering = {"NMON_equals_meta_node_plus_1_all": all(o == 1 for o in off), "n_monitors": len(mlist), "per_monitor": {}}
        for mname in MON:
            m = next(x for x in mlist if x[0] == mname)
            n_meta, r, z = m[1], m[2], m[3]
            d_meta = math.hypot(nodes[n_meta][0] - r, nodes[n_meta][1] - z)
            d_true = math.hypot(nodes[n_meta + 1][0] - r, nodes[n_meta + 1][1] - z)
            numbering["per_monitor"][mname] = {"meta_node": n_meta, "meta_r_z_mm": [round(r, 4), round(z, 4)],
                                               "inp_node_meta_xy_mm": [round(nodes[n_meta][0], 4), round(nodes[n_meta][1], 4)], "distance_meta_node_mm": round(d_meta, 4),
                                               "inp_node_meta_plus_1_xy_mm": [round(nodes[n_meta + 1][0], 4), round(nodes[n_meta + 1][1], 4)], "distance_meta_plus_1_mm": round(d_true, 6)}
            assert d_true < 1e-6 and d_meta > 0.1, (tag, mname, d_meta, d_true)
        # (3)-(4) .dat, monitors.csv, frd
        true_nodes = {mname: next(x for x in mlist if x[0] == mname)[1] + 1 for mname in MON}
        meta_nodes = {mname: true_nodes[mname] - 1 for mname in MON}
        dt_, dv_ = read_dat(dat, sorted(set(true_nodes.values())))
        hdr, rows = F1.read_mon(monp)
        mt = [row[0] for row in rows]
        assert len(mt) == len(dt_) and max(abs(a - b) for a, b in zip(mt, dt_)) < 5e-4, (tag, len(mt), len(dt_))
        csv_vs_dat = {}
        for mname in MON:
            ci = hdr.index(mname)
            csv_vs_dat[mname] = round(max(abs(row[ci] - v) for row, v in zip(rows, dv_[true_nodes[mname]])), 5)
        pts = f1r["points"]
        need = set(true_nodes.values()) | set(meta_nodes.values())
        for nm in pts:
            need.update(pts[nm]["hits"][0]["nodes"])
        ts, vals = F1.stream_frd(frd, sorted(need))
        assert len(ts) == f1r["n_frames"]
        # frame times against the .dat print times
        j_of = []
        for t in ts:
            i = bisect.bisect_left(dt_, t - 1e-9)
            cand = [k for k in (i - 1, i, i + 1) if 0 <= k < len(dt_)]
            j_of.append(min(cand, key=lambda k: abs(dt_[k] - t)))
        dts = [abs(dt_[j] - t) for j, t in zip(j_of, ts)]
        frames = {"n_frd_frames": len(ts), "n_dat_prints": len(dt_), "n_monitors_csv_rows": len(mt),
                  "max_abs_frd_minus_dat_time_s": max(dts), "frd_frames_matched_to_a_dat_time_within_1e-3_s": sum(x < 1e-3 for x in dts),
                  "dat_times_not_in_frd": len(set(range(len(dt_))) - set(j for j, x in zip(j_of, dts) if x < 1e-3)),
                  "first_last_frd_time_s": [ts[0], ts[-1]], "first_last_dat_time_s": [dt_[0], dt_[-1]]}
        assert frames["max_abs_frd_minus_dat_time_s"] < 1e-3 and frames["frd_frames_matched_to_a_dat_time_within_1e-3_s"] == len(ts), (tag, frames)
        vals_cmp = {}
        for mname in MON:
            ci = hdr.index(mname)
            mv = [row[ci] for row in rows]
            d_true = [abs(vals[true_nodes[mname]][k] - dv_[true_nodes[mname]][j]) for k, (j, x) in enumerate(zip(j_of, dts)) if x < 1e-3]
            dm = [(abs(F1.interp(mt, mv, t) - vals[meta_nodes[mname]][k]), t, vals[meta_nodes[mname]][k], F1.interp(mt, mv, t), vals[true_nodes[mname]][k])
                  for k, t in enumerate(ts) if not math.isnan(F1.interp(mt, mv, t))]
            worst = max(dm)
            # a time shift would show as frd(m + 1) at t matching monitors.csv at t + dt: best shift of frd(m+1) against the csv over +/- 2 frames
            vals_cmp[mname] = {"true_node": true_nodes[mname], "meta_node": meta_nodes[mname],
                               "max_abs_frd_true_node_minus_dat_same_time_K": round(max(d_true), 5),
                               "max_abs_frd_meta_node_minus_monitors_csv_K_F1_comparison": round(worst[0], 4),
                               "F1_json_value_K": f1r["monitor_crosscheck"][mname]["max_abs_diff_K_frd_vs_monitors_csv"],
                               "at_t_s": worst[1], "there_frd_meta_node_K": round(worst[2], 3), "there_monitors_csv_K": round(worst[3], 3),
                               "there_frd_true_node_K": round(worst[4], 3)}
            assert abs(worst[0] - f1r["monitor_crosscheck"][mname]["max_abs_diff_K_frd_vs_monitors_csv"]) < 1e-6, (tag, mname)
            assert max(d_true) < 2e-3, (tag, mname, max(d_true))
        # (5) seat points with F1's weights
        seat = {}
        hist = {}
        for nm in pts:
            h0 = pts[nm]["hits"][0]
            hist[nm] = [sum(w * vals[n][j] for w, n in zip(h0["w"], h0["nodes"])) for j in range(len(ts))]
        hd = f1r["history_diaphragm"]
        seat["diaphragm_history_max_abs_diff_K_vs_F1_json"] = round(max(abs(round(v, 3) - b) for v, (a, b) in zip(hist["diaphragm_zt-9.5"], hd)), 5)
        ev = F1.events_for(tag, meta)
        evd = 0.0
        for lab, t in ev:
            for nm in pts:
                evd = max(evd, abs(F1.interp(ts, hist[nm], t) - f1r["T_K_at_events"][lab][nm]))
        seat["seat_points_at_events_max_abs_diff_K_vs_F1_json"] = evd
        assert evd < 1e-9 and seat["diaphragm_history_max_abs_diff_K_vs_F1_json"] <= 5e-4
        # (6) the MON_ proxies at the monitor node
        for mname in MON:
            hist["MON_" + mname] = vals[true_nodes[mname]]
        moved = {}
        for lab, a, b in F1.drifts_for(tag):
            for mname in MON:
                key = "MON_" + mname
                tA = next(t for l_, t in ev if l_ == a); tB = next(t for l_, t in ev if l_ == b)
                new = F1.interp(ts, hist[key], tB) - F1.interp(ts, hist[key], tA)
                old = f1r["drifts"][lab][key]["dT_K"]
                moved[f"{lab}|{mname}"] = {"F1_at_meta_node_K": round(old, 4), "at_monitor_node_K": round(new, 4), "change_K": round(new - old, 4)}
        rises_moved = {}
        for lab, t in ev:
            for mname in MON:
                key = "MON_" + mname
                new = F1.interp(ts, hist[key], t) - F1.interp(ts, hist[key], ev[0][1])
                old = f1r["rise_K_vs_ARM"][lab][key]
                rises_moved[f"{lab}|{mname}"] = round(new - old, 4)
        seat_drifts = {lab: round(f1r["drifts"][lab]["diaphragm_zt-9.5"]["dT_K"], 4) for lab, _, _ in F1.drifts_for(tag)}
        out["runs"][tag] = {"dir": d, "sha16": shas, "numbering": numbering, "frames": frames, "monitors_csv_vs_dat_max_abs_K": csv_vs_dat,
                            "monitor_values": vals_cmp, "seat_points": seat, "seat_drifts_K_unchanged": seat_drifts,
                            "MON_proxy_drifts": moved,
                            "MON_proxy_drifts_moving_more_than_0p1K": {k: v for k, v in moved.items() if abs(v["change_K"]) > 0.1},
                            "MON_proxy_rise_vs_ARM_max_abs_change_K": round(max(abs(v) for v in rises_moved.values()), 4)}
        print("RUN", tag, json.dumps({"frames": frames, "csv_vs_dat": csv_vs_dat, "values": vals_cmp, "seat": seat,
                                      "moved_gt_0p1": out["runs"][tag]["MON_proxy_drifts_moving_more_than_0p1K"]}), f"{time.time() - t0:.0f} s", flush=True)
    out["verdict"] = ("NEITHER TIME IS SHIFTED: the frd frames and the .dat NODE PRINT (= monitors.csv) carry the same times, and the frd value at the monitor's own node equals "
                      "the .dat value at the same time to the print precision. The F1 differences come from node numbering: the run meta lists each monitor one node number "
                      "below the .inp node at the stated (r, z) (the thermal writer keeps the 0-based mesh index there, ax_thermal.py; the NMON set, the .dat and monitors.csv "
                      "use the .inp number), so F1 compared a neighbouring node, 2.13-2.45 mm away, with the monitor. F1's seat points use the .inp element connectivity and are unchanged (0 K): the +/-0.6 K extraction caveat is WITHDRAWN for the seat values; "
                      "F1's MON_ proxy columns were at the neighbouring node and are re-stated here (the published F1 numbers are the seat values) [SIM, DERIVED]")
    out["t_run_s"] = round(time.time() - t0, 1)
    op = os.path.join(HERE, "c1_seat_xcheck_v352_v1.json")
    s = json.dumps(out, indent=1, sort_keys=True)
    with open(op, "w") as f:
        f.write(s)
    print("WROTE", op, hashlib.sha256(s.encode()).hexdigest()[:16], len(s), out["t_run_s"])


if __name__ == "__main__":
    main()
