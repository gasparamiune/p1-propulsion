"""m2_rev3_p5 v1.0 (GNC rev3, 2026-10-13): P5 - trajectory consequence of the PROVISIONAL RG-16 detection-latency allowance
(LEAD CHANGELOG line 181 (3): 0.5 s from the onset of the 670 N plateau) on A1 and B1, flown in the 6-DOF loop (sim6 v2.11-dev
amendment L: forced abort decision flt_dla after the plateau onset, every detector off).

Fault (m2_fault_f v1.1 definitions, same onset generator and draws): stuck pintle, ramp 2.5 kN/s to the 670 N plateau (L670),
onsets A1asc (boost, U(0.3, 2.5) s), A1land (U(0.2, 2.0) s after the landing-burn start), B1asc (U(0.3, 0.8) s), B1floor
(U(1.2, 10.0) s, floor phases), B1land (U(0.2, 2.0) s after the landing-burn start). Bases: V = Pc valid, linkage failure
(A1_none / tgl_B1_lead62_pc_k2, tot_cal_comp); Lhi = Pc lost, flow and thrust per command x 1.143 (A1_none / B1_62_none,
pclhi_re_comp) - the case where FC_THRUST is the only over-thrust detector. Arms per onset: dla05 (decision 0.5 s after the
plateau onset), dla00 (decision at the plateau onset: the zero-latency comparator, V only); per profile and base: nom (no
fault, same draws). The abort follows amendment F (relight lockout, MV commanded abt_lat later, seated abt_seat after,
Combustion tail-off impulse); an aborted flight is a lost vehicle (the landing flag is reported, not a success criterion).
A forced decision needs the engine lit: when the flight software shut the engine down before the allowance (MECO / landing
cut), the fault ends with that shutdown (linkage failure: servo seat, MV closes, no lockout) and re-activates at the next
start (flt_persist), where the plateau clock restarts.
Metrics: velocity gained during the allowance (v_z at the decision - v_z at the plateau onset) and from the fault onset to the
end of the first tail-off; DERIVED cross-check (670 / m - g) x 0.5 s; apex (whole flight) and highest true height after the
onset, paired against the nominal flight and the zero-latency arm (same draw); touchdown vertical speed and distance;
landing criteria met (Wilson 95 %); the in-loop FC_THRUST statistic (sim6 amendment F, detector computed but not acting):
largest 3-frame held estimate after the onset (> 650 N = the detector would have tripped inside the allowance) and its trip
time after the plateau onset. SIM on ASSUMED fault shape and white vibration model; no hardware data.
Env: m2r3_env.sh; GNC_P5_OUT (out/rev3/p5); GNC_P5_N (200); GNC_P5_PARTS (mc,eval).
Output: <out>/p5_<arm>.csv, <out>/p5_latency.json."""
import hashlib
import json
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_fault_f as FF  # noqa: E402
import m2_mc6 as M  # noqa: E402
from gncsim import run6 as R, sim6 as s6  # noqa: E402

VERSION = "m2_rev3_p5 v1.0"
S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_P5_OUT", f"{S}/rev3/p5")
N = int(os.environ.get("GNC_P5_N", "200"))
PARTS = os.environ.get("GNC_P5_PARTS", "mc,eval").split(",")
G0 = 9.80665
NEW = ("flt_tpl", "flt_vz0", "flt_h0", "flt_vzpl", "flt_hpl", "flt_vzdec", "flt_hdec", "flt_mdec", "flt_ttoe", "flt_vztoe",
       "flt_htoe")
KEEP = tuple(FF.KEEP) + NEW
ONS = ("A1asc", "A1land", "B1asc", "B1floor", "B1land")
BRS = {"V": "Vblind", "Lhi": "Lhi_blind"}


def arms():
    a = {}
    for on in ONS:
        a[f"{on}|dla05|V"] = dict(on=on, br="V", dla=0.5)
        a[f"{on}|dla00|V"] = dict(on=on, br="V", dla=0.0)
        a[f"{on}|dla05|Lhi"] = dict(on=on, br="Lhi", dla=0.5)
    for prof in ("A1", "B1"):
        for br in BRS:
            a[f"{prof}|nom|{br}"] = dict(on=None, prof=prof, br=br, dla=None)
    return a


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def fname(name):
    return os.path.join(OUT, "p5_" + name.replace("|", "_") + ".csv")


def fly_arm(a):
    br = BRS[a["br"]]
    sk, pcl, enc = FF.BR[br]
    prof = FF.ONS[a["on"]][0] if a["on"] else a["prof"]
    jr = json.load(open(f"{S}/throat_growth/throat_growth.json"))["j_ref"]
    FF.MV.TG_JREF_DEFAULT = float(jr["A1" if prof == "A1" else "B1"])
    cfg, D = FF.cfg_for(prof, "V" if sk == "V" else "L")
    spec = FF.spec_of(sk)
    if a["on"]:
        _, ph, _ = FF.ONS[a["on"]]
        F_, rate_ = FF.LEV["L670"]
        tt, fph = FF.onset_draws(a["on"], N)
    rows = []
    for i in range(N):
        c, disp = FF.MV.run_cfg_case(cfg, D[i], spec, i, "comb")
        if a["on"]:
            c = dict(c, flt_on=1, flt_ph=ph, flt_t=float(tt[i]), flt_F=F_, flt_rate=rate_, flt_enc=enc, flt_pcl=pcl,
                     fct_ph=float(fph[i]), fct_comp=1, det_fct=0, det_op=0, det_pf=0, det_geo=0, flt_dla=a["dla"])
        res = R.fly(c, disp, nrec=10)[0]
        row = dict(run=i, onset_draw_s=float(tt[i]) if a["on"] else -1.0, ok=int(R.success(res)))
        row.update({k: float(res[k]) for k in KEEP if k != "ok"})
        rows.append(row)
    return rows


def part_mc():
    os.makedirs(OUT, exist_ok=True)
    if FF.MV.COMB is None:
        FF.MV.COMB = FF.MV.comb_draws(500)
    for name, a in arms().items():
        p = fname(name)
        if os.path.exists(p) and os.path.getsize(p) > 100 and os.environ.get("GNC_P5_FORCE") != "1":
            print("exists", name, flush=True)
            continue
        t0 = time.time()
        rows = fly_arm(a)
        M.write_csv(p, rows)
        dec = np.array([r["flt_tdec"] >= 0.0 and r["flt_t0"] >= 0.0 for r in rows]) if a["on"] else np.zeros(len(rows), bool)
        print(f"{name:22s}: n {len(rows)} forced {int(dec.sum())} ok {sum(r['ok'] for r in rows)} ({time.time() - t0:.0f} s)",
              flush=True)


def col(rows, k):
    return np.array([float(r[k]) for r in rows])


def pct(x, qs=(1, 50, 99)):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return None
    return dict({f"p{q:02d}": round(float(np.percentile(x, q)), 3) for q in qs}, min=round(float(x.min()), 3),
                max=round(float(x.max()), 3), n=int(x.size))


def part_eval():
    A = arms()
    rows = {n: FF.rows_csv(fname(n)) for n in A}
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, sim6_sha16=sha16(s6.__file__), run6_sha16=sha16(R.__file__),
               method=__doc__.split("\n\n")[1].strip(), n=N, rng_onset=FF.RNG_F, level=dict(F_N=670.0, rate_N_s=2500.0),
               allowance_s=0.5, abort_chain_s=dict(abt_lat=float(R.DEF["abt_lat"]), abt_seat=float(R.DEF["abt_seat"]),
                                                   abt_imp_Ns=float(R.DEF["abt_imp"])), arms={}, missing=[])
    for name, a in A.items():
        r = rows[name]
        if not r:
            out["missing"].append(name)
            continue
        ok = col(r, "ok") > 0.5
        e = dict(a, n=len(r), landing_criteria_met=int(ok.sum()), P=float(ok.mean()),
                 P_wilson=[float(x) for x in R.wilson(int(ok.sum()), len(r))], apex_m=pct(col(r, "h_max")),
                 touchdown_vz_mps=pct(col(r, "td_vz")), touchdown_distance_m=pct(np.hypot(col(r, "td_x"), col(r, "td_y"))))
        if a["on"]:
            t0, tpl, dec = col(r, "flt_t0"), col(r, "flt_tpl"), col(r, "flt_tdec")
            on = t0 >= 0.0
            fz = on & (dec >= 0.0)
            m_ = col(r, "flt_mdec")
            dva = col(r, "flt_vzdec") - col(r, "flt_vzpl")
            te = col(r, "flt_ttoe") >= 0.0
            hp = col(r, "fct_held_post")
            trf = col(r, "flt_tr_fct")
            e.update(onset_reached=int(on.sum()), forced_decisions=int(fz.sum()),
                     no_forced_decision=int((on & ~fz).sum()),
                     no_forced_detail=dict(ended_by_fsw_shutdown=int(np.sum(on & ~fz & (col(r, "flt_tsd") >= 0.0))),
                                           liquid_exhausted=int(np.sum(on & ~fz & (col(r, "flt_end") == 7.0)))),
                     activations=pct(col(r, "flt_n_on")[on], (50, 100)),
                     ramp_s=pct((tpl - t0)[on & (tpl >= 0)], (50, 100)),
                     dv_allowance_mps=pct(dva[fz]), dv_allowance_derived_mps=pct(((670.0 / m_ - G0) * a["dla"])[fz]),
                     dv_onset_to_tailoff_end_mps=pct((col(r, "flt_vztoe") - col(r, "flt_vz0"))[fz & te]),
                     dh_onset_to_tailoff_end_m=pct((col(r, "flt_htoe") - col(r, "flt_h0"))[fz & te]),
                     vz_at_decision_mps=pct(col(r, "flt_vzdec")[fz]), h_at_decision_m=pct(col(r, "flt_hdec")[fz]),
                     h_at_onset_m=pct(col(r, "flt_h0")[on]), max_true_height_after_onset_m=pct(col(r, "flt_hmax")[on]),
                     max_vz_after_onset_mps=pct(col(r, "flt_vzmax")[on]), mass_at_decision_kg=pct(m_[fz]),
                     impulse_after_onset_Ns=pct(col(r, "flt_imp")[on]),
                     fct_inloop=dict(held_post_N=pct(hp[on]), tripped_650_inside_allowance=int(np.sum(on & (trf >= 0) & (trf <= dec + 1e-9) & fz)),
                                     held_post_gt_650=int(np.sum(on & (hp > 650.0))),
                                     trip_after_plateau_ms=pct(1e3 * (trf - tpl)[on & (trf >= 0) & (tpl >= 0)], (50, 99, 100)),
                                     note="sim6 amendment F FC_THRUST computed in the loop (same ASSUMED white noise model), det_fct 0"))
            # paired against the nominal flight and the zero-latency arm (same draw)
            prof = FF.ONS[a["on"]][0]
            for ref in (f"{prof}|nom|{a['br']}", f"{a['on']}|dla00|{a['br']}"):
                rr = rows.get(ref)
                if rr and ref != name:
                    hm0 = col(rr, "h_max")
                    ok0 = col(rr, "ok") > 0.5
                    d_ = dict(apex_minus_ref_m=pct((col(r, "h_max") - hm0)[on]), P_ref=float(ok0.mean()),
                              both_ok=int(np.sum(ok & ok0)), ref_ok_only=int(np.sum(ok0 & ~ok)), this_ok_only=int(np.sum(ok & ~ok0)))
                    if "dla00" in ref:
                        z0 = (col(rr, "flt_tdec") >= 0) & (col(rr, "flt_ttoe") >= 0) & fz & te
                        d_["dv_onset_to_tailoff_end_minus_ref_mps"] = pct(((col(r, "flt_vztoe") - col(r, "flt_vz0"))
                                                                           - (col(rr, "flt_vztoe") - col(rr, "flt_vz0")))[z0])
                        d_["max_height_after_onset_minus_ref_m"] = pct((col(r, "flt_hmax") - col(rr, "flt_hmax"))[on])
                        d_["td_vz_minus_ref_mps"] = pct((col(r, "td_vz") - col(rr, "td_vz"))[on])
                    e[f"paired_vs_{ref}"] = d_
        out["arms"][name] = e
    pj = os.path.join(OUT, "p5_latency.json")
    json.dump(out, open(pj, "w"), indent=1, default=float)
    print("wrote", pj, sha16(pj))
    for name, e in out["arms"].items():
        if e.get("on"):
            dv = e["dv_allowance_mps"] or {}
            ap = e.get(f"paired_vs_{FF.ONS[e['on']][0]}|nom|{e['br']}", {}).get("apex_minus_ref_m") or {}
            fc = e["fct_inloop"]
            print(f"{name:20s} forced {e['forced_decisions']:3d}/{e['onset_reached']:3d} dv_allow p50/p99 {dv.get('p50')}/{dv.get('p99')} "
                  f"(derived p50 {(e['dv_allowance_derived_mps'] or {}).get('p50')}) | hmax after onset p50/p99 "
                  f"{(e['max_true_height_after_onset_m'] or {}).get('p50')}/{(e['max_true_height_after_onset_m'] or {}).get('p99')} | "
                  f"apex-nom p50/p99 {ap.get('p50')}/{ap.get('p99')} | td_vz p01 {(e['touchdown_vz_mps'] or {}).get('p01')} | "
                  f"P {e['P']:.3f} | FC held>650 {fc['held_post_gt_650']} trip-pl p99 {(fc['trip_after_plateau_ms'] or {}).get('p99')} ms",
                  flush=True)
        else:
            print(f"{name:20s} nominal P {e['P']:.3f} apex p50 {(e['apex_m'] or {}).get('p50')}", flush=True)


if __name__ == "__main__":
    if "mc" in PARTS:
        part_mc()
    if "eval" in PARTS:
        part_eval()
