"""Engine relay correction v2 (2026-10-12): bring the combustion v2 performance relayed by the lead into the GNC
engine model before combustion.json v2 is published.

Inputs (read, never hard-coded here):
  * data/relay/lead_relay_combustion_v2_20261012.json: record of the lead's relay message (values + provenance);
  * combustion's unpublished duty-cycle runs behind those totals (S230 straight-port grain, nominal regression,
    non-equilibrium tank E = 1e3), paths in the relay record: time histories of F, mdot_ox, mdot_f, port diameter;
  * interfaces/combustion.json v1 throttle map through gncsim.engine_v2 (the map the 6-DOF uses);
  * GNC duty cycles v1 (out/duty_cycles/*_v1.csv): the thrust profiles combustion flew.

Method: thrust-binned factors k_ox(F) = sum(mdot_ox,comb dt) / sum(mdot_ox,map(F) dt) and k_f(F) likewise over the
four S230 nominal runs (run state only, F >= 100 N, bins with >= 0.75 s of data). The 6-DOF scales its map by
k(F) (linear between bin centres, constant outside). Validation: the corrected map flown on the same four
thrust profiles against combustion's totals (N2O, fuel, Isp); regression band x0.6 / x1.5 reported for DC-A1.
S230 grain: length 0.230 m (combustion grain_q1d.py variant), mass = v1 mass x 0.230 / 0.200 (DERIVED, same OD,
port and density).

Output: data/relay/engine_correction_v2.json (read by run6/engine_v2), GNC_RES/engine_relay_v2.png/.json.
Run: nice -n 10 python scripts/m2_engine_relay.py
"""
import csv
import hashlib
import json
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from gncsim import engine_v2  # noqa: E402

RELAY = os.path.join(HERE, "data", "relay", "lead_relay_combustion_v2_20261012.json")
OUTF = os.path.join(HERE, "data", "relay", "engine_correction_v2.json")
RES = os.environ.get("GNC_RES", "/home/claude/work/space/out/results_v2")
DC1 = os.environ.get("GNC_DC1_DIR", "/home/claude/work/space/out/duty_cycles")
EDGES = [100, 125, 150, 200, 250, 300, 350, 400, 450, 525]
MIN_T = 0.75
G0 = 9.80665
os.makedirs(RES, exist_ok=True)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def comb_run(path):
    rows = list(csv.DictReader(open(path)))
    t = np.array([float(r["t"]) for r in rows])
    F = np.array([float(r["F"]) for r in rows])
    mo = np.array([float(r["mox"]) for r in rows])
    mf = np.array([float(r["mf"]) for r in rows])
    st = np.array([r["state"] for r in rows])
    dt = np.diff(t, append=t[-1])
    return t, F, mo, mf, st, dt


def profile_totals(dc_csv, Fg, tmox, tmf):
    rows = list(csv.DictReader(ln for ln in open(dc_csv) if not ln.startswith("#")))
    t = np.array([float(r["t_s"]) for r in rows])
    F = np.array([float(r["F_N"]) for r in rows])
    dt = np.diff(t, append=t[-1])
    on = F > 1.0
    mo = np.interp(F, Fg, tmox)
    mf = np.interp(F, Fg, tmf)
    I = float(np.sum(F * dt))
    ox = float(np.sum(mo[on] * dt[on]))
    fu = float(np.sum(mf[on] * dt[on]))
    return dict(impulse_Ns=I, ox_kg=ox, fuel_kg=fu, Isp_s=I / ((ox + fu) * G0), ox_per_kNs=ox / I * 1e3)


def main():
    rel = json.load(open(RELAY))
    wf = rel["combustion_work_files_read"]
    comb = engine_v2.load_combustion()
    tab = engine_v2.combustion_tables(comb)
    Fg = tab["Fg"]
    mox_map = tab["mox"][:, 0]
    mf_map = tab["mf"][:, 0]
    S = json.load(open(os.path.join(wf["dir"], wf["summary"])))
    files = {}
    Fs, mos, mfs, dts = [], [], [], []
    for fn in wf["runs"]:
        p = os.path.join(wf["dir"], fn)
        files[fn] = sha(p)
        t, F, mo, mf, st, dt = comb_run(p)
        m = (st == "run") & (F >= EDGES[0])
        Fs.append(F[m]); mos.append(mo[m]); mfs.append(mf[m]); dts.append(dt[m])
    F = np.concatenate(Fs); mo = np.concatenate(mos); mf = np.concatenate(mfs); dt = np.concatenate(dts)
    mo_m = np.interp(F, Fg, mox_map)
    mf_m = np.interp(F, Fg, mf_map)
    bins = []
    for a, b in zip(EDGES[:-1], EDGES[1:]):
        s = (F >= a) & (F < b)
        w = dt[s]
        if w.sum() <= 0:
            continue
        bins.append(dict(F_lo=a, F_hi=b, time_s=float(w.sum()), F_mean=float(np.sum(F[s] * w) / w.sum()),
                         k_ox=float(np.sum(mo[s] * w) / np.sum(mo_m[s] * w)),
                         k_f=float(np.sum(mf[s] * w) / np.sum(mf_m[s] * w)),
                         Isp_comb=float(np.sum(F[s] * w) / np.sum((mo[s] + mf[s]) * w) / G0),
                         Isp_map_v1=float(np.sum(F[s] * w) / np.sum((mo_m[s] + mf_m[s]) * w) / G0),
                         OF_comb=float(np.sum(mo[s] * w) / np.sum(mf[s] * w)), used=bool(w.sum() >= MIN_T)))
    use = [b for b in bins if b["used"]]
    anchors = dict(F_N=[b["F_mean"] for b in use], k_ox=[b["k_ox"] for b in use], k_f=[b["k_f"] for b in use])
    kox = np.interp(Fg, anchors["F_N"], anchors["k_ox"])
    kf = np.interp(Fg, anchors["F_N"], anchors["k_f"])
    # validation on the thrust profiles combustion flew (GNC duty cycles v1)
    val = []
    pairs = [("DC-A1_full_flight_drogue_300m_v1.csv", "DC-A1-S230_neqE1e+03_reg1"),
             ("DC-A2_full_flight_freefall_300m_v1.csv", "DC-A2-S230_neqE1e+03_reg1"),
             ("DC-B1_hop_100m_floor20_v1.csv", "DC-B1-S230_neqE1e+03_reg1"),
             ("DC-B2_hop_50m_floor20_v1.csv", "DC-B2-S230_neqE1e+03_reg1")]
    for dcf, key in pairs:
        p = os.path.join(DC1, dcf)
        v1 = profile_totals(p, Fg, mox_map, mf_map)
        cr = profile_totals(p, Fg, mox_map * kox, mf_map * kf)
        c = S[key]
        cb = dict(impulse_Ns=c["impulse_Ns"], ox_kg=c["ox_used_kg"], fuel_kg=c["fuel_used_kg"], Isp_s=c["Isp_mean_s"],
                  ox_per_kNs=c["ox_used_kg"] / c["impulse_Ns"] * 1e3)
        val.append(dict(profile=dcf, combustion_run=key, map_v1=v1, map_corrected=cr, combustion=cb,
                        ox_per_impulse_err_v1=v1["ox_per_kNs"] / cb["ox_per_kNs"] - 1.0,
                        ox_per_impulse_err_corrected=cr["ox_per_kNs"] / cb["ox_per_kNs"] - 1.0,
                        Isp_err_corrected=cr["Isp_s"] / cb["Isp_s"] - 1.0))
    band = {}
    for k in ("DC-A1-S230_neqE1e+03_reg0.6", "DC-A1-S230_neqE1e+03_reg1", "DC-A1-S230_neqE1e+03_reg1.5"):
        c = S[k]
        band[k] = dict(Isp_s=c["Isp_mean_s"], ox_kg=c["ox_used_kg"], fuel_kg=c["fuel_used_kg"], OF_mean=c["OF_mean"],
                       min_F_ceiling_N=c["min_F_ceiling_N"], ox_per_kNs=c["ox_used_kg"] / c["impulse_Ns"] * 1e3)
    i500 = int(np.argmin(abs(Fg - 500.0)))
    g = comb["gas_path"]["grain"]
    L1 = g["length_m"]["v"]
    L2 = 0.230
    grain = dict(length_m=L2, mass_kg=g["mass_kg"]["v"] * L2 / L1,
                 tag_length="RELAY S230 (combustion grain_q1d.py variant v2_S230_straight_L230: L 0.230 m)",
                 tag_mass=f"DERIVED combustion.json {comb.get('version')} grain mass x 0.230/{L1} (same OD, port, density)")
    out = dict(id="engine_correction_v2", version="c1 (2026-10-12)", owner="Space/GNC",
               applies_to_combustion_json_version=comb.get("version"),
               source=f"lead relay {rel['id']} + combustion work files (S230, reg 1.0, neq tank) sha256 below",
               relay_values=rel["values"], combustion_files_sha256=files,
               method=f"thrust-binned mass-flow ratios combustion/map, run state, F >= {EDGES[0]} N, bins >= {MIN_T} s",
               bins=bins, anchors=anchors,
               at_500N=dict(k_ox=float(kox[i500]), k_f=float(kf[i500]), mox_corrected=float(mox_map[i500] * kox[i500]),
                            mf_corrected=float(mf_map[i500] * kf[i500]),
                            OF_corrected=float(mox_map[i500] * kox[i500] / (mf_map[i500] * kf[i500])),
                            Isp_corrected=float(500.0 / ((mox_map[i500] * kox[i500] + mf_map[i500] * kf[i500]) * G0)),
                            OF_relay=rel["values"]["OF_at_500N"]["v"]),
               validation=val, regression_band_DC_A1=band, grain=grain,
               ceiling_note="v1 ceiling kept: relay minimum ceiling 548 N > 500 N; in the 6-DOF the v1 ceiling never "
                            "binds (tank 40-50 bar)",
               limitations=["factors are averages over the port diameters met in combustion's runs (25-45 mm)",
                            "combustion's start/shutdown transients (< 100 N) are excluded; the 6-DOF keeps its own "
                            "ignition/tail-off model",
                            "replace by the combustion.json v2 map when published"])
    with open(OUTF, "w") as f:
        json.dump(out, f, indent=1)
    json.dump(out, open(os.path.join(RES, "engine_relay_v2.json"), "w"), indent=1)
    for b in bins:
        print(f"F {b['F_lo']:3d}-{b['F_hi']:3d} t {b['time_s']:6.2f} k_ox {b['k_ox']:.3f} k_f {b['k_f']:.3f} "
              f"Isp comb {b['Isp_comb']:.1f} map {b['Isp_map_v1']:.1f} {'used' if b['used'] else 'skip'}")
    for v in val:
        print(f"{v['profile'][:5]} ox/I err v1 {100*v['ox_per_impulse_err_v1']:+.1f} % corrected "
              f"{100*v['ox_per_impulse_err_corrected']:+.1f} %  Isp corr {v['map_corrected']['Isp_s']:.1f} vs comb "
              f"{v['combustion']['Isp_s']:.1f}")
    print("500 N:", out["at_500N"])
    print("grain:", grain)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    ax[0].plot(Fg, kox, label="k_ox(F) applied")
    ax[0].plot(Fg, kf, label="k_f(F) applied")
    for b in bins:
        ax[0].plot(b["F_mean"], b["k_ox"], "o" if b["used"] else "x", color="C0")
        ax[0].plot(b["F_mean"], b["k_f"], "o" if b["used"] else "x", color="C1")
    ax[0].set_xlabel("thrust F [N]"); ax[0].set_ylabel("combustion v2 / map v1 mass flow"); ax[0].grid(alpha=0.3)
    ax[0].legend(fontsize=8); ax[0].set_title("relay correction factors (o used, x < 0.75 s of data)", fontsize=9)
    m = Fg > 20
    ax[1].plot(Fg[m], Fg[m] / ((mox_map[m] + mf_map[m]) * G0), label="map v1 (combustion.json v1)")
    ax[1].plot(Fg[m], Fg[m] / ((mox_map[m] * kox[m] + mf_map[m] * kf[m]) * G0), label="map v1 x relay factors")
    ax[1].plot([b["F_mean"] for b in bins], [b["Isp_comb"] for b in bins], "k.", label="combustion v2 runs (binned)")
    ax[1].set_xlabel("thrust F [N]"); ax[1].set_ylabel("Isp [s]"); ax[1].grid(alpha=0.3); ax[1].legend(fontsize=8)
    ax[1].set_title("delivered Isp vs thrust", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "engine_relay_v2.png"), dpi=110)


if __name__ == "__main__":
    main()
