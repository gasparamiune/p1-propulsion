"""T-F1 exposure basis for the founder action text (lead 09:59Z; CHANGELOG 239 (12)): per-firing temperatures and times above the 150 C
usable limit of 6061-T6 for TC-01 and TC-02 (and TC-03 for the (b) package), from the v3.5.2 rev-4 thermal runs on both gap-conductance bounds,
plus the TB surrogate per trial abort value.  Mechanical, 2026-10-20, v1.  Reads only; SIM (CalculiX thermal) + ASSUMED surrogate as tagged.

Sources: v352/tb70/hist/<label>_hist.npz (case_tc_hist_v352.py: every output frame of the run, all TC-01 / TC-02 / TC-03 nodes), and the
S-AX v352r4 run.json of each TB state (the uniform shift applied by sax.py state_temperature 'case_to_abort').
Definitions:
  part maximum   = max over the part's thermal nodes at each frame; 'time above X' integrates the frames with linear crossing interpolation;
  J-FWD row      = TC-01 nodes within +/- 2.75 mm (hole radius) of the screw axis, 12 mm from the TC-01 forward end (axisymmetric model:
                   no holes; the row value is the band maximum over r);
  case TC station= TC-01 OD nodes 12.6-17.6 mm aft of the injector face (Electronics case over-temperature abort TCs, CHANGELOG 86 / 90);
  TB state       = ASSUMED surrogate (sax.py): the B1 end-of-burn field (t 21.651 s) shifted uniformly so that the TC-01 maximum equals the
                   abort value A (shift_K read from the S-AX run.json); 'TB shifted history' = the whole B1 history (burn + soak) with that
                   shift: an ASSUMED bound for sizing only, not a modelled stand history;
  design life    = 50 hot cycles (CHANGELOG 183 (1)(c)).
Usage: tf1_exposure_v352.py -> v352/texts/tf1_exposure_v352_v1.json"""
import json, hashlib
from pathlib import Path
import numpy as np

H = Path("/home/claude/work/mechanical/v352/tb70/hist")
S = Path("/home/claude/work/mechanical/runs/structural")
OUT = Path("/home/claude/work/mechanical/v352/texts/tf1_exposure_v352_v1.json")
RUNS = {"GVLO": "DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_R4_GVLO", "GVHI": "DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_R4_GVHI"}
SAX = {"GVLO": "L1_thv352_NF2b_R4_GVLO_r10free_cad352r4_eh0p1", "GVHI": "L1_thv352_NF2b_R4_GVHI_r10free_cad352r4_eh0p1"}
ABORTS = {"TB": 175.0, "TB_a165": 165.0, "TB_a150": 150.0, "TB_a135": 135.0, "TB_a120": 120.0, "TB_a105": 105.0}
T_EOB, LIM, LIFE = 21.651, 150.0, 50


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def t_above(t, T, thr):
    tot = 0.0
    for k in range(len(t) - 1):
        a, b, dt = T[k] - thr, T[k + 1] - thr, t[k + 1] - t[k]
        if a >= 0 and b >= 0:
            tot += dt
        elif a >= 0 > b:
            tot += dt * a / (a - b)
        elif a < 0 <= b:
            tot += dt * b / (b - a)
    return tot


def find(x, key):
    if isinstance(x, dict):
        for k, v in x.items():
            if k == key:
                return v
            r = find(v, key)
            if r is not None:
                return r
    elif isinstance(x, list):
        for v in x:
            r = find(v, key)
            if r is not None:
                return r
    return None


def curve_stats(t, T):
    k = int(np.argmax(T))
    return {"max_C": round(float(T[k]), 1), "t_of_max_s": round(float(t[k]), 2),
            "t_above_150C_s": round(t_above(t, T, LIM), 1), "t_above_175C_s": round(t_above(t, T, 175.0), 1),
            "t_above_200C_s": round(t_above(t, T, 200.0), 1)}


out = {"id": "tf1_exposure_v352", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(), "bounds": {}}
for bd, lab in RUNS.items():
    p = H / f"{lab}_hist.npz"
    z = np.load(p, allow_pickle=True)
    info = json.loads(str(z["info"]))
    t = z["t_s"].astype(float)
    i_eob = int(np.argmin(np.abs(t - T_EOB)))
    burn = t <= T_EOB + 1e-6
    rec = {"thermal_run": lab, "hist": {"path": str(p), "sha256_16": sha(p)}, "frd_sha256_16": info["frd_sha256_16"], "steps": info["steps"], "parts": {}}
    for pn, key in (("ENG-TC-01", "TC01"), ("ENG-TC-02", "TC02"), ("ENG-TC-03", "TC03")):
        X, T = z[f"X_{key}"], z[f"T_{key}"].astype(float) - 273.15
        pm = T.max(axis=1)
        kn = int(np.unravel_index(int(np.argmax(T)), T.shape)[1])
        r = {"part_max": curve_stats(t, pm), "max_node_r_z_thermal_mm": [round(float(X[kn, 0]), 3), round(float(X[kn, 1]), 3)],
             "burn_max_C": round(float(pm[burn].max()), 1), "end_of_burn_max_C": round(float(pm[i_eob]), 2),
             "life_hours_above_150C_at_part_max": round(LIFE * t_above(t, pm, LIM) / 3600.0, 2)}
        if key == "TC01":
            zf = float(X[:, 1].max())
            m = np.abs(X[:, 1] - (zf - 12.0)) <= 2.75
            r["jfwd_row"] = curve_stats(t, T[:, m].max(axis=1))
            r["jfwd_row"]["z_thermal_mm"] = round(zf - 12.0, 3)
            zi = info["inj_face_z_mm"]
            odX, odT = z["od_X"], z["od_T"].astype(float) - 273.15
            ms = (odX[:, 1] <= zi - 12.6) & (odX[:, 1] >= zi - 17.6)
            st = odT[:, ms].max(axis=1)
            r["case_TC_station"] = {"burn_max_C": round(float(st[burn].max()), 1), "t_of_burn_max_s": round(float(t[burn][int(np.argmax(st[burn]))]), 2),
                                    "soak_max_C": round(float(st.max()), 1), "n_od_nodes": int(ms.sum()),
                                    "note": "the abort is armed while the MV is open (burn only); the soak value is not an abort input"}
        rec["parts"][pn] = r
    # TB surrogate per abort value
    tb = {}
    for stn, A in ABORTS.items():
        rj = S / SAX[bd] / stn / "run.json"
        shift = float(find(json.loads(rj.read_text()), "shift_K"))
        row = {"abort_C": A, "shift_K": round(shift, 3), "run_json": {"path": str(rj), "sha256_16": sha(rj)},
               "nominal_false_abort_check": ("abort below the nominal end-of-burn case maximum: a nominal B1 burn would trip it" if shift < 0 else
                                             "abort above the nominal end-of-burn case maximum")}
        for pn, key in (("ENG-TC-01", "TC01"), ("ENG-TC-02", "TC02"), ("ENG-TC-03", "TC03")):
            T = z[f"T_{key}"].astype(float) - 273.15
            pm = T.max(axis=1)
            row[pn] = {"TB_state_field_max_C": round(float(pm[i_eob] + shift), 1),
                       "shifted_history_ASSUMED": curve_stats(t, pm + shift)}
        tb[stn] = row
    rec["TB_surrogate_per_abort"] = tb
    out["bounds"][bd] = rec
s = json.dumps(out, indent=1)
OUT.write_text(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
for bd, rec in out["bounds"].items():
    for pn, r in rec["parts"].items():
        print(bd, pn, r["part_max"], "burn", r["burn_max_C"], "eob", r["end_of_burn_max_C"], r.get("jfwd_row", ""), r.get("case_TC_station", ""))
    for stn, row in rec["TB_surrogate_per_abort"].items():
        print("  ", bd, stn, row["shift_K"], {pn: (row[pn]["TB_state_field_max_C"], row[pn]["shifted_history_ASSUMED"]["max_C"], row[pn]["shifted_history_ASSUMED"]["t_above_150C_s"]) for pn in ("ENG-TC-01", "ENG-TC-02", "ENG-TC-03")})
