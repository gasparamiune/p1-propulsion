"""Wetted seat-face temperature from MECO to E1 on the A1 relight (04-fea/thermal, v1, 2026-10-13, Mechanical).

Request: Combustion v2.4 (REPORT 9.1 hazard H1, OI-21; combustion.json v2.4 469727032124329f): "the wetted seat face <= 800 K from
MECO to E1 (Mechanical FE)"; at 850 K the gas-phase N2O induction time is 43 s, at 900 K 8.0 s (Combustion, Cantera gri30, SIM).
Coordinator 2026-10-13 item (2): report it from the thermal run or state it as open.

Model: the design A1 thermal run (rev B, 2-D axisymmetric CAX6, run_thermal v1.3, 'hi' bound = upper-bound heat transfer, DC
DC-A1dispp99_tg711: burn 1 0.001-3.541 s, coast 18.67 s, relight 22.211 s).  The N2O-wetted faces are the 45 boundary edges the deck
films with the N2O amplitudes (ENG-TC-03 seat insert r 2.75-5.0 mm, ENG-TC-02 head bore r 5.0, ENG-TC-04 bonnet r 5.0-5.36).  The
needle (pintle) is not in the axisymmetric model: its tip temperature is not covered here.
Two coasts restarted from the design run's MECO field (same mesh, materials, coast boundary conditions; the full run's output at
MECO is the initial condition):
  BASE       the design coast: stagnant liquid N2O, total 1 W/K (376 W/m2K at 289 K) on the wetted faces (Combustion headend_thermal_v2)
  ADIABATIC  wetted faces adiabatic in the coast (vapour-blanketed or drained annulus): upper bound for the wetted faces
QA: BASE must reproduce the full run's coast at the seat monitor within 1 K (restart method check).
The relight purge flow (V1/V2 taps, 2.5 s before E0) is not modelled: it can only cool the passage (lower temperature).

Restart method history (kept as evidence): try 1 (v1, 2026-10-13 11:35, fixed increments 0.09984 s copied from the design deck)
FAILED the QA: seat monitor 10.4 K below the full run at the end of the coast.  In the first increment the liner hot faces (ENG-TC-06,
ENG-TC-08: 2348 K at MECO, radiating to 288 K) went to -1777 / -1882 K, the spurious negative root of the implicit radiation balance
(T^4 is even); the energy removed by that excursion cooled the head end for the rest of the coast (non-conservative).  The full run
does not show it (all its frames >= 290.7 K; its coast starts from the burn's state, the restart from rest).  Try-1 outputs are kept
as seat_face_temp_v1_try1_FAILED_QA.json/.csv and runs/thermal/<design>_seatcoast_v1/.
v1.1 (try 2): automatic incrementation from 1e-4 s with DELTMX = 25 K (max increment 0.09984 s = the design run's); every node on a
radiating or N2O-wetted edge plus the monitors is printed each increment, and any printed node below 250 K fails the QA.

Usage: python seat_face_coast.py [--run]   (--run solves both decks with ccx, OMP 1, sequentially; without it, post only)
Outputs: seat_face_temp_v1p1.json, seat_face_temp_v1p1.csv (this folder); decks in runs/thermal/<design>_seatcoast_v1p1/<variant>/
"""
from __future__ import annotations
import argparse, csv, hashlib, json, os, subprocess, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ax_thermal as at

RUNS = Path("/home/claude/work/mechanical/runs/thermal")
DESIGN = "DC-A1dispp99_tg711_hi_SS316L_L2.5_v13pre36IN_J1revB"
OUTDIR = RUNS / f"{DESIGN}_seatcoast_v1p1"
TRY1DIR = RUNS / f"{DESIGN}_seatcoast_v1"           # try 1, FAILED QA (kept as evidence)
OUT_STEM = "seat_face_temp_v1p1"
COAST_NOM_S = 20.599            # gnc.json v3 DC-A1 burn-off to burn-on (REV-ELEC-1 R13); E1 <= E0 + 0.16 s (combustion.json v2.4)
T_LIMIT_K = 800.0
DELTMX_K = 25.0                 # max nodal temperature change per increment (automatic incrementation)
DT_MAX_S = 0.09984              # the design run's coast increment
T_PHYS_MIN_K = 250.0            # QA: below this a printed node is non-physical (coast sinks 288-289 K)
QA_TOL_K = 1.0
EDGE = {"F1": (0, 1, 3), "F2": (1, 2, 4), "F3": (2, 0, 5)}
VARIANTS = ("BASE", "ADIABATIC")


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def deck_parts(label):
    run = RUNS / label
    lines = (run / f"{label}.inp").read_text().split("\n")
    i_pc = next(i for i, L in enumerate(lines) if L.startswith("*PHYSICAL CONSTANTS"))
    model = lines[:i_pc + 1]
    steps = [i for i, L in enumerate(lines) if L.startswith("*STEP")]
    ends = [i for i, L in enumerate(lines) if L.startswith("*END STEP")]
    meta = json.loads((run / f"{label}_meta.json").read_text())
    kinds = [s[0] for s in meta["steps"]]
    k = next(j for j, s in enumerate(meta["steps"]) if s[0] == "COAST" and s[1] > 0.0)
    coast = lines[steps[k]:ends[k] + 1]
    # N2O-wetted edges: the burn's ATN/AHN film block
    i_n = next(i for i, L in enumerate(lines) if L.startswith("*FILM, AMPLITUDE=ATN"))
    n2o = []
    for L in lines[i_n + 1:]:
        if L.startswith("*"):
            break
        a = L.split(",")
        n2o.append((int(a[0]), a[1].strip()))
    # the coast's N2O block = the plain '*FILM' block whose edges are the N2O edges
    j0 = next(j for j, L in enumerate(coast) if L.strip() == "*FILM")
    j1 = next(j for j in range(j0 + 1, len(coast)) if coast[j].startswith("*"))
    blk = [(int(L.split(",")[0]), L.split(",")[1].strip()) for L in coast[j0 + 1:j1]]
    assert sorted(blk) == sorted(n2o), "coast N2O film block does not match the burn's N2O edges"
    return model, coast, (j0, j1), n2o, meta, kinds


def meco_field(label, t_meco):
    for t, vals in at.read_frd_nt(RUNS / label / f"{label}.frd"):
        if abs(t - t_meco) < 1e-6:
            return t, vals
    raise RuntimeError(f"no frd frame at MECO {t_meco}")


def wetted_nodes(label, n2o):
    d = np.load(RUNS / label / "envelope_nodes.npz", allow_pickle=True)
    X, E, pn = d["X"], d["E"], d["pn"]
    grp = {}
    for el, f in n2o:
        for q in EDGE[f]:
            grp.setdefault(str(pn[el - 1]), set()).add(int(E[el - 1, q]) + 1)     # frd/ccx node id = index + 1
    return {k: sorted(v) for k, v in grp.items()}, X


def radiating_nodes(coast, label):
    """Nodes on the coast's *RADIATE edges (the surfaces that can find the spurious radiation root)."""
    d = np.load(RUNS / label / "envelope_nodes.npz", allow_pickle=True)
    E = d["E"]
    i0 = next(j for j, L in enumerate(coast) if L.startswith("*RADIATE, OP=NEW"))
    nodes = set()
    for L in coast[i0 + 1:]:
        if L.startswith("*"):
            break
        a = L.split(",")
        if len(a) < 2:
            continue
        el, f = int(a[0]), a[1].strip().replace("R", "F")
        for q in EDGE[f]:
            nodes.add(int(E[el - 1, q]) + 1)
    return sorted(nodes)


def nset_lines(name, ids):
    return [f"*NSET, NSET={name}"] + [", ".join(str(n) for n in ids[i:i + 12]) for i in range(0, len(ids), 12)]


def write_and_run(run_ccx):
    model, coast, (j0, j1), n2o, meta, kinds = deck_parts(DESIGN)
    t_meco = meta["segments_s"][0][1]
    t_frame, field = meco_field(DESIGN, t_meco)
    grp, X = wetted_nodes(DESIGN, n2o)
    allw = sorted({n for v in grp.values() for n in v})
    nrad = radiating_nodes(coast, DESIGN)
    info = {"t_MECO_s": t_meco, "t_frame_s": t_frame, "n_field": len(field), "wetted_nodes": {k: len(v) for k, v in grp.items()},
            "radiating_nodes": len(nrad), "incrementation": {"initial_s": 1.0e-4, "max_s": DT_MAX_S, "DELTMX_K": DELTMX_K}}
    res = {}
    for var in VARIANTS:
        d = OUTDIR / var
        d.mkdir(parents=True, exist_ok=True)
        body = list(coast)
        # v1.1: automatic incrementation (try 1's fixed 0.09984 s first increment found the spurious negative radiation root)
        assert body[0].startswith("*STEP") and body[1].startswith("*HEAT TRANSFER, DIRECT")
        period = float(body[2].split(",")[1])
        assert abs(period - (meta["segments_s"][1][0] - t_meco)) < 1e-3, period          # the coast duration
        body[0] = "*STEP, INC=20000"
        body[1] = f"*HEAT TRANSFER, DELTMX={DELTMX_K:g}"
        body[2] = f"1.0e-4, {period:.6f}, 1.0e-9, {DT_MAX_S:.6f}"
        if var == "ADIABATIC":
            body = body[:j0] + ["** N2O coast film removed: wetted faces adiabatic (seat_face_coast.py ADIABATIC)"] + body[j1:]
        out = [f"** seat_face_coast.py v1.1 {var}: restart of {DESIGN} coast from its MECO field t = {t_frame:.4f} s"] + model
        out += nset_lines("NWET", allw) + nset_lines("NRAD", nrad)
        out.append("*INITIAL CONDITIONS, TYPE=TEMPERATURE")
        out += [f"{n}, {T:.4f}" for n, T in sorted(field.items())]
        k = 0
        while k < len(body):                # output requests rebuilt: NODE PRINT of the wetted, radiating and monitor sets, no NODE FILE
            L = body[k]
            if L.startswith("*NODE PRINT") or L.startswith("*NODE FILE"):
                k += 2                      # keyword + its variable line (NT)
                continue
            if L.startswith("*END STEP"):
                out += ["*NODE PRINT, NSET=NWET, FREQUENCY=1", "NT", "*NODE PRINT, NSET=NMON, FREQUENCY=1", "NT",
                        "*NODE PRINT, NSET=NRAD, FREQUENCY=1", "NT"]
            out.append(L)
            k += 1
        (d / "seat.inp").write_text("\n".join(out) + "\n")
        if run_ccx:
            t0 = time.time()
            env = dict(os.environ, OMP_NUM_THREADS="1")
            with open(d / "ccx.log", "w") as lf:
                r = subprocess.run(["ccx", "-i", "seat"], cwd=d, stdout=lf, stderr=subprocess.STDOUT, env=env)
            res[var] = {"returncode": r.returncode, "seconds": round(time.time() - t0, 1)}
            print(var, res[var], flush=True)
    (OUTDIR / "decks_info.json").write_text(json.dumps({"design": DESIGN, **info, "solve": res}, indent=1))
    return info


def read_dat(dat):
    out, cur = {}, None
    with open(dat) as fh:
        for line in fh:
            s = line.strip()
            if s.startswith("temperatures") and "time" in s:
                cur = float(s.split()[-1])
                out.setdefault(cur, {})
                continue
            p = s.split()
            if cur is not None and len(p) == 2:
                try:
                    out[cur][int(p[0])] = float(p[1])
                except ValueError:
                    pass
    ts = sorted(out)
    return np.array(ts), out


def post():
    model, coast, _, n2o, meta, _ = deck_parts(DESIGN)
    t_meco, t_rl = meta["segments_s"][0][1], meta["segments_s"][1][0]
    coast_run = t_rl - t_meco
    grp, X = wetted_nodes(DESIGN, n2o)
    mon = {m[0]: m for m in meta["monitors"]}
    seat_node = mon["insert_TC03_seat"][1] + 1
    # full design run: wetted maxima through burn 1 and the coast (frd frames), plus every monitor node (QA)
    ts, rows = [], []
    allw = sorted({n for v in grp.values() for n in v})
    mon_nodes = sorted({m[1] + 1 for m in meta["monitors"]})
    keys = sorted(set(allw) | set(mon_nodes))
    for t, vals in at.read_frd_nt(RUNS / DESIGN / f"{DESIGN}.frd"):
        if t > t_rl + 1e-6:
            break
        ts.append(t)
        rows.append([vals[n] for n in keys])
    ts, A = np.array(ts), np.array(rows)
    col = {n: k for k, n in enumerate(keys)}
    full = {p: A[:, [col[n] for n in v]].max(axis=1) for p, v in grp.items()}
    fr = (ts > t_meco + 1e-6) & (ts <= t_rl + 1e-6)          # full-run coast frames (every 10 increments = 0.9984 s)
    burn1 = ts <= t_meco + 1e-9
    i_b = int(np.argmax(np.where(burn1, full["ENG-TC-03"], -1)))
    res = {"id": "seat_face_temp", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "script": "04-fea/thermal/seat_face_coast.py",
           "request": "Combustion v2.4 OI-21 / REPORT 9.1 H1: wetted seat face <= 800 K from MECO to E1 (A1 relight); coordinator 2026-10-13 item (2)",
           "status": "SIM (2-D axisymmetric thermal FE, upper-bound heat transfer) + restart variants; needle not modelled; not a measurement",
           "source_run": {"label": DESIGN, "frd_sha256_16": sha16(RUNS / DESIGN / f"{DESIGN}.frd"),
                          "inp_sha256_16": sha16(RUNS / DESIGN / f"{DESIGN}.inp"), "segments_s": meta["segments_s"],
                          "bound": meta["bound"], "config_overrides": meta["config_overrides"],
                          "coast_N2O_film": {"G_total_W_K": meta["G_N2O_COAST_W_K"], "h_W_m2K": round(meta["h_n2o_coast_W_m2K"], 1),
                                             "A_wetted_mm2": round(meta["A_n2o_mm2"], 1)}},
           "wetted_faces": {k: {"nodes": len(v), "r_mm": [round(float(X[np.array(v) - 1][:, 0].min()), 2), round(float(X[np.array(v) - 1][:, 0].max()), 2)],
                                "z_thermal_mm": [round(float(X[np.array(v) - 1][:, 1].min()), 2), round(float(X[np.array(v) - 1][:, 1].max()), 2)]}
                            for k, v in grp.items()},
           "limit_K": T_LIMIT_K,
           "in_burn_1": {"TC03_wetted_max_K": round(float(full["ENG-TC-03"][i_b]), 1), "t_s": round(float(ts[i_b]), 3)},
           "variants": {}}
    rows_csv = []
    for var in VARIANTS:
        dat = OUTDIR / var / "seat.dat"
        if not dat.exists():
            res["variants"][var] = {"status": "NOT RUN"}
            continue
        tt, D = read_dat(dat)
        tau = tt
        if len(tt) < 3:                                       # v1.1 run 2026-10-13: ccx stopped in the first increment (see ccx.log)
            lg = OUTDIR / var / "ccx.log"
            msg = [ln.strip() for ln in (lg.read_text().splitlines() if lg.exists() else []) if ln.strip()][-4:]
            res["variants"][var] = {"status": "RUN FAILED (kept as evidence)", "n_increments": int(len(tt)), "ccx_log_tail": msg}
            continue
        v = {"tau_s": tau}
        for p, ids in grp.items():
            v[p] = np.array([max(D[t][n] for n in ids) for t in tt])
        seat = np.array([D[t][seat_node] for t in tt])
        # extension to the nominal 20.599 s coast: slope of the last 1.7 s (upper bound if the curve is concave or decaying)
        k = tau >= coast_run - 1.7
        sl = float(np.polyfit(tau[k], v["ENG-TC-03"][k], 1)[0])
        T_E1_nom = float(v["ENG-TC-03"][-1] + max(sl, 0.0) * (COAST_NOM_S - coast_run)) if sl > 0 else float(v["ENG-TC-03"][-1])
        i_mx = int(np.argmax(v["ENG-TC-03"]))
        r = {"TC03_wetted_max_K": round(float(v["ENG-TC-03"][i_mx]), 1), "tau_at_max_s": round(float(tau[i_mx]), 3),
             "TC03_wetted_at_run_relight_K": round(float(v["ENG-TC-03"][-1]), 1),
             "TC03_wetted_at_nominal_E1_K": round(T_E1_nom, 1),
             "slope_last_1p7s_K_s": round(sl, 3),
             "TC02_wetted_max_K": round(float(v["ENG-TC-02"].max()), 1), "TC04_wetted_max_K": round(float(v["ENG-TC-04"].max()), 1),
             "margin_to_800K_K": round(T_LIMIT_K - max(float(v["ENG-TC-03"].max()), T_E1_nom), 1),
             "verdict": "BELOW 800 K throughout MECO-E1" if max(float(v["ENG-TC-03"].max()), T_E1_nom) < T_LIMIT_K else "EXCEEDS 800 K"}
        for x in (0.5, 1.0, 2.0, 5.0, 10.0, coast_run):
            r[f"TC03_wetted_K_at_tau_{x:g}s"] = round(float(np.interp(x, tau, v["ENG-TC-03"])), 1)
        # non-physical check over every printed node (wetted, radiating, monitors), every increment
        tmin = min(min(D[t].values()) for t in tt)
        r["n_increments"] = int(len(tt))
        r["printed_nodes"] = int(len(D[tt[-1]]))
        r["printed_min_K"] = round(float(tmin), 2)
        r["nonphysical_check_pass"] = bool(tmin >= T_PHYS_MIN_K)
        if var == "BASE":
            # QA: reproduce the full run's coast at its frd frames (the restart is interpolated at the frame times)
            qa = {}
            for m in meta["monitors"]:
                n = m[1] + 1
                if n not in D[tt[-1]]:
                    continue
                g = np.array([D[t][n] for t in tt])
                dd = np.interp(ts[fr] - t_meco, tau, g) - A[fr, col[n]]
                qa[m[0]] = round(float(dd[np.argmax(np.abs(dd))]), 3)
            gw = np.array([[D[t][n] for n in grp["ENG-TC-03"]] for t in tt])
            dw = np.array([np.interp(ts[fr] - t_meco, tau, gw[:, j]) - A[fr, col[n]] for j, n in enumerate(grp["ENG-TC-03"])])
            r["QA_seat_monitor_max_abs_diff_K"] = abs(qa["insert_TC03_seat"])
            r["QA_TC03_wetted_nodes_max_abs_diff_K"] = round(float(np.abs(dw).max()), 3)
            r["QA_all_monitors_signed_worst_diff_K"] = qa
            r["QA_frames"] = int(fr.sum())
            r["QA_tolerance_K"] = QA_TOL_K
            r["QA_pass"] = bool(r["QA_seat_monitor_max_abs_diff_K"] <= QA_TOL_K and r["QA_TC03_wetted_nodes_max_abs_diff_K"] <= QA_TOL_K
                                and r["nonphysical_check_pass"])
        res["variants"][var] = r
        for i in range(len(tau)):
            rows_csv.append([var, round(float(tau[i]), 4), round(float(v["ENG-TC-03"][i]), 2), round(float(seat[i]), 2),
                             round(float(v["ENG-TC-02"][i]), 2), round(float(v["ENG-TC-04"][i]), 2)])
    # the design run's own coast (frd frames, 0.9984 s apart): the BASE coast without any restart
    fc = full["ENG-TC-03"][fr]
    res["full_run_coast_frames"] = {"frames": int(fr.sum()), "TC03_wetted_max_K": round(float(fc.max()), 1),
                                    "TC03_wetted_at_relight_K": round(float(fc[-1]), 1),
                                    "TC02_wetted_max_K": round(float(full["ENG-TC-02"][fr].max()), 1),
                                    "TC04_wetted_max_K": round(float(full["ENG-TC-04"][fr].max()), 1),
                                    "note": "first frame 0.9984 s after MECO; between MECO and that frame the restart (or the MECO value) applies"}
    t1 = HERE / "seat_face_temp_v1_try1_FAILED_QA.json"
    if t1.exists():
        j = json.loads(t1.read_text())
        res["try1_evidence"] = {"file": t1.name, "QA_seat_monitor_max_abs_diff_K": j["variants"]["BASE"].get("QA_seat_monitor_max_abs_diff_K"),
                                "cause": "fixed 0.09984 s first increment: liner hot faces ENG-TC-06/08 went to -1777/-1882 K (spurious "
                                         "negative radiation root), non-conservative cooling of the head end; results not used"}
    ran = [k for k in VARIANTS if "TC03_wetted_max_K" in res["variants"][k]]
    qa_ok = res["variants"].get("BASE", {}).get("QA_pass", False)
    phys_ok = all(res["variants"][k]["nonphysical_check_pass"] for k in ran)
    worst = max([res["variants"][k]["TC03_wetted_max_K"] for k in ran] + [res["in_burn_1"]["TC03_wetted_max_K"],
                                                                          res["full_run_coast_frames"]["TC03_wetted_max_K"]])
    if ran and qa_ok and phys_ok:
        res["summary"] = (f"Wetted seat-face peak over MECO-E1 = {worst:.1f} K (FE, 'hi' bound; coast variants run: {', '.join(ran)}) vs the "
                          f"800 K limit; the peak sits at MECO (in-burn value at the seat edge r 2.75 mm) and the face cools through the coast. "
                          "Needle tip not modelled (OPEN); thermocouple T4 confirmation required (Combustion verification list).")
    else:
        failed = [k for k in VARIANTS if str(res["variants"][k].get("status", "")).startswith("RUN FAILED")]
        res["summary"] = (f"RESTART {'RUN FAILED (' + ', '.join(failed) + ': ccx diverged in the first increment)' if failed else ('QA FAILED' if ran else 'NOT RUN')} (variants run: {ran or 'none'}; BASE QA pass {qa_ok}, non-physical "
                          f"check pass {phys_ok}): the restart variants are not usable. The design run's own coast frames give a wetted "
                          f"seat-face maximum of {res['full_run_coast_frames']['TC03_wetted_max_K']:.1f} K after MECO and "
                          f"{res['in_burn_1']['TC03_wetted_max_K']:.1f} K at MECO (BASE coast only); the ADIABATIC bound is OPEN.")
    res["version"] = "v1.1"
    (HERE / f"{OUT_STEM}.json").write_text(json.dumps(res, indent=1))
    with open(HERE / f"{OUT_STEM}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([f"# wetted seat-face temperature on the A1 coast (tau = t - MECO), restart of {DESIGN}; K; SIM"])
        w.writerow(["variant", "tau_s", "TC03_wetted_max_K", "TC03_seat_monitor_K", "TC02_wetted_max_K", "TC04_wetted_max_K"])
        w.writerows(rows_csv)
    print(json.dumps({k: res[k] for k in ("in_burn_1", "variants", "summary")}, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--decks", action="store_true", help="write decks only")
    a = ap.parse_args()
    if a.run or a.decks:
        print(json.dumps(write_and_run(a.run)), flush=True)
    post()
