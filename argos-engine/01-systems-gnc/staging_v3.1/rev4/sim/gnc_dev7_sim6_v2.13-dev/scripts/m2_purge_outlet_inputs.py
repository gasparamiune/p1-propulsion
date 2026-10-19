"""m2_purge_outlet_inputs v1.1 (GNC rev2, 2026-10-13; v1.1: body rate split into transverse (as the MC metric prg_rate_max) and roll; v1.0 reported |w| including roll): GNC inputs for Combustion's tank-outlet coverage check during PURGE
(Combustion v2.4 ask, folded in where cheap; NO coverage verdict). Decided path: FSW-R2 + sim6 v2.9-dev amendment G (G73,
29.2 g/s, 2.5 s flow), line states pw (purged_unlined_Tp2.5 worst) and pl (least), bases A1_none and A1J_pc, seed 101.
(i) 500-run distributions from the stored re-fly tables (m2_rg01_refly, no new flight): largest tilt and body rate inside the
    purge flow, height at the commit and at E0, purge mass.
(ii) 10 ms records of selected runs re-flown with identical draws (run 0, the largest-tilt run, the largest-rate run of each
    base and state): inside the flow window [t_flow_start, t_flow_start + t_flow] the axial specific force (sim6 record fax =
    body-z specific force), the angle between the body axis and the specific-force vector (finite difference of the record
    velocity, raw and 0.1 s moving mean; quasi-static liquid-surface tilt relative to the tank axis), tilt from the vertical,
    transverse and roll body rates, liquid mass, height and vertical speed. Each re-flown run is checked against its stored row (ok, td_vz,
    prg_mass, pgg_fl equal).
Not computed: the free-surface position and outlet coverage (needs tank and outlet geometry and fill: Combustion /
Mechanical); slosh dynamics (sim6 liquid is a lumped mass); canopy pendulum (drogue quasi-steady, massless).
Tags: SIM (sim6 6-DOF), DERIVED (statistics). Output: out/rev2/purge_outlet/purge_outlet_inputs.json"""
import csv
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_mass_est_v2 as MV  # noqa: E402
import m2_rg01_refly as F  # noqa: E402

VERSION = "m2_purge_outlet_inputs v1.1"
OUT = os.environ.get("GNC_PO_OUT", "/home/claude/work/space/out/rev2/purge_outlet")
RF = F.OUT
I = {n: k for k, n in enumerate(s6.REC_NAMES)}


def table(base, arm):
    p = os.path.join(RF, f"rf_{base}_{arm.replace('|', '_')}.csv")
    return list(csv.DictReader(open(p))), p


def refly(base, arm, runs):
    spec = F.ARMS[arm]
    cfg, m = F.base_cfg(base, spec["state"], F.arm_extra(spec, F.engine_bay_mid()[0]))
    jr = json.load(open(F.TG))["j_ref"]
    MV.TG_JREF_DEFAULT = float(jr["A1J" if base.startswith("A1J") else "A1"])
    D = R.draw(np.random.default_rng(101), F.N, cfg)
    ms = MV.case_specs()["tot_cal_comp"]
    out = {}
    for i in runs:
        c, disp = MV.run_cfg_case(cfg, D[i], ms, i, "base")
        c.update(F.DEC)
        c.update(F.PURGE[spec["purge"]])
        c.update(rec_dt=0.01)
        res, rec, _ = R.fly(c, disp, nrec=20000)
        out[i] = (res, rec)
    return out


def window(res, rec):
    t0 = float(res["pgg_tfl0"])
    t1 = t0 + float(res["pgg_fl"])
    t = rec[:, I["t"]]
    k = (t >= t0) & (t <= t1)
    v = rec[:, [I["vx"], I["vy"], I["vz"]]]
    dt = np.gradient(t)
    a = np.gradient(v, axis=0) / dt[:, None]
    f = a + np.array([0.0, 0.0, s6.G0])
    q = rec[:, [I["q0"], I["q1"], I["q2"], I["q3"]]]
    zb = np.stack([2 * (q[:, 1] * q[:, 3] + q[:, 0] * q[:, 2]), 2 * (q[:, 2] * q[:, 3] - q[:, 0] * q[:, 1]),
                   1 - 2 * (q[:, 1] ** 2 + q[:, 2] ** 2)], axis=1)
    fn = np.linalg.norm(f, axis=1)
    ang = np.degrees(np.arccos(np.clip(np.sum(f * zb, axis=1) / np.maximum(fn, 1e-9), -1, 1)))
    nm = 10
    fs = np.stack([np.convolve(f[:, j], np.ones(nm) / nm, mode="same") for j in range(3)], axis=1)
    angs = np.degrees(np.arccos(np.clip(np.sum(fs * zb, axis=1) / np.maximum(np.linalg.norm(fs, axis=1), 1e-9), -1, 1)))
    w = np.degrees(np.linalg.norm(rec[:, [I["wx"], I["wy"]]], axis=1))     # v1.1: transverse rate (as prg_rate_max)
    wr = np.degrees(np.abs(rec[:, I["wz"]]))                                 # v1.1: roll rate about the body axis
    fax = rec[:, I["fax"]]

    def st(x):
        x = x[k]
        return dict(min=float(x.min()), p50=float(np.percentile(x, 50)), max=float(x.max())) if x.size else None
    return dict(t_flow_start_s=t0, t_flow_s=t1 - t0, samples=int(k.sum()), fax_m_s2=st(fax), fax_g=st(fax / s6.G0),
                sf_axis_angle_deg_raw=st(ang), sf_axis_angle_deg_0p1s=st(angs), tilt_deg=st(rec[:, I["tilt"]]),
                transverse_rate_deg_s=st(w), roll_rate_deg_s=st(wr), m_liq_g=[float(1e3 * rec[k, I["mliq"]][0]), float(1e3 * rec[k, I["mliq"]][-1])] if k.any() else None,
                h_m=[float(rec[k, I["z"]][0]), float(rec[k, I["z"]][-1])] if k.any() else None, vz_m_s=st(rec[:, I["vz"]]))


def main():
    os.makedirs(OUT, exist_ok=True)
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, method=__doc__.split("\n\n")[0], distributions={},
               records={}, checks=[])
    for arm in ("pw|G73", "pl|G73"):
        for base in F.BASES_MAIN:
            rows, p = table(base, arm)
            col = lambda n: np.array([float(r[n]) for r in rows])  # noqa: E731
            tl, rt = col("prg_tilt_max"), col("prg_rate_max")
            out["distributions"][f"{base}|{arm}"] = dict(
                table=f"{p} (sha256/16 {F.sha16(p)})", n=len(rows),
                tilt_max_in_flow_deg=F.pct(tl, (50, 99)), transverse_rate_max_in_flow_deg_s=F.pct(rt, (50, 99)),
                commit_height_m=F.pct(col("pgg_h0"), (1, 50)), E0_height_m=F.pct(col("pgg_hE0"), (1, 50)),
                flow_s=F.pct(col("pgg_fl"), (1, 50)), purge_mass_g=F.pct(1e3 * col("prg_mass"), (1, 50, 99)))
            sel = sorted({0, int(np.argmax(tl)), int(np.argmax(rt))})
            fl = refly(base, arm, sel)
            for i in sel:
                res, rec = fl[i]
                r = rows[i]
                chk = dict(case=f"{base}|{arm}|run{i}", ok=(float(R.success(res)) > 0.5) == (float(r["ok"]) > 0.5),
                           td_vz=float(res["td_vz"]) == float(r["td_vz"]), prg_mass=float(res["prg_mass"]) == float(r["prg_mass"]),
                           pgg_fl=float(res["pgg_fl"]) == float(r["pgg_fl"]))
                chk["passed"] = all(v for k_, v in chk.items() if k_ != "case")
                out["checks"].append(chk)
                out["records"][f"{base}|{arm}|run{i}"] = dict(role=("run 0" if i == 0 else "") + (" largest tilt" if i == int(np.argmax(tl)) else "")
                                                             + (" largest rate" if i == int(np.argmax(rt)) else ""), **window(res, rec))
                w_ = out["records"][f"{base}|{arm}|run{i}"]
                print(f"{base}|{arm}|run{i:3d} chk {chk['passed']} fax g {w_['fax_g']['min']:.3f}/{w_['fax_g']['max']:.3f} "
                      f"sf-axis deg 0.1s max {w_['sf_axis_angle_deg_0p1s']['max']:.2f} raw max {w_['sf_axis_angle_deg_raw']['max']:.2f} "
                      f"tilt max {w_['tilt_deg']['max']:.2f} transverse rate max {w_['transverse_rate_deg_s']['max']:.1f} roll max {w_['roll_rate_deg_s']['max']:.1f} mliq {w_['m_liq_g']}", flush=True)
    out["all_checks_passed"] = all(c["passed"] for c in out["checks"])
    with open(os.path.join(OUT, "purge_outlet_inputs.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("checks", out["all_checks_passed"], "wrote", os.path.join(OUT, "purge_outlet_inputs.json"), flush=True)


if __name__ == "__main__":
    main()
