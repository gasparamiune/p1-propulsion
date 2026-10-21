"""Screw shear-plane bending check on the J-FWD contact sub-model resultants (fea3d 2026-10-20 ~10:00Z).

Why: the 234 (1)(b) screw rows (jfwd_post / jfwd_cells, and Mechanical's CALC jfwd_preload_v352_v2) take tension on A_s and shear on A_3
and no bending.  The FE screw (solid d 5.0, bonded thread in TC-02 from x' 21.5 to 28.6, clearance hole in TC-01, head on the spot face)
carries a bending moment at the shear plane whenever the shank bears (FA1S: V 3.6 kN): the resultant moment over the screw disc at x'
(jfwd_post.section_force, SIM) with dM/dx = V as the statics check.  This script states the bending stress and the combined checks it
gives, as DERIVED rows beside the published ones; which criterion applies to fastener bending is Mechanical's (TO-VERIFY against the
NASA-STD-5020A bending treatment).
Rows per step (x' 28.7 = first section in the TC-01 hole, and x' 28.6 = the thread entry, M + V x 0.1 mm extrapolated):
  sigma_t = N / A_s (14.18), sigma_b = M / Z_3 (Z_3 = pi d3^3 / 32, d3 4.019 AS RECALLED, threads in the shear plane as in the published
  shear rows), tau = V / A_3 (12.686);
  yield, extreme fibre: k_T Rp0.2 / (sigma_t + sigma_b) - 1 (beam shear is zero at the extreme fibre);
  yield, conservative: k_T Rp0.2 / sqrt((sigma_t + sigma_b)^2 + 3 tau^2) - 1 (average shear added at the extreme fibre);
  ultimate interaction (R_t + R_b)^2 + R_s^2 <= 1 with R_t = sigma_t / (k_Tu Rm), R_s = tau / (0.6 k_Tu Rm), and R_b = sigma_b / (k k_Tu Rm)
  for k = 1.0 (elastic bending) and k = 1.70 (fully plastic round section, 16 / (3 pi) = 1.698: upper bound, LITERATURE AS RECALLED;
  the Cozzone factor for the A4-80 proxy is TO-VERIFY and lies between).
Evidence: SIM resultants (contact sub-model, mu 0, 3750 N, fit 0.078) + DERIVED (this check; A4-80 proxy k_T / k_Tu ASSUMED as in the post).
usage: jfwd_screw_bend.py JOB -> jfwd/runs/JOB/screw_bend.json"""
import sys, json, math, hashlib
from pathlib import Path

RUNS = Path("/home/claude/work/fea3d/jfwd/runs")
D3, AS, A3 = 4.019, 14.18, 12.686
Z3 = math.pi * D3 ** 3 / 32.0
K_PL = 16.0 / (3.0 * math.pi)


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def rows(sec, sc):
    out = {}
    s0 = sec[0]
    for tag, x, M, N, V in (("x28.7", s0["x_prime_mm"], s0["M_bend_Nmm"], s0["N"], s0["V"]),
                            ("x28.6_thread_entry_extrapolated", 28.6, s0["M_bend_Nmm"] + s0["V"] * (s0["x_prime_mm"] - 28.6), s0["N"], s0["V"])):
        st, sb, tau = N / AS, M / Z3, V / A3
        Rp, Rm = sc["kT_Rp_MPa"], sc["kTu_Rm_MPa"]
        rt, rs = st / Rm, tau / (0.6 * Rm)
        r = {"x_prime_mm": round(x, 3), "N_N": round(N, 1), "V_N": round(V, 1), "M_Nmm": round(M, 1), "sigma_t_MPa": round(st, 1),
             "sigma_b_MPa": round(sb, 1), "tau_A3_MPa": round(tau, 1), "sigma_t_plus_b_MPa": round(st + sb, 1),
             "MS_y_fibre": round(Rp / (st + sb) - 1, 3), "MS_y_vm_conservative": round(Rp / math.sqrt((st + sb) ** 2 + 3 * tau ** 2) - 1, 3)}
        for k, lab in ((1.0, "elastic"), (K_PL, "plastic_1.70_upper")):
            rb = sb / (k * Rm)
            r[f"MS_u_interaction_{lab}"] = round(1 / math.sqrt((rt + rb) ** 2 + rs ** 2) - 1, 3)
        r["MS_u_interaction_no_bending"] = round(1 / math.sqrt(rt ** 2 + rs ** 2) - 1, 3)
        out[tag] = r
    return out


def main(job):
    wd = RUNS / job
    pf = wd / "post.json" if (wd / "post.json").exists() else wd / "post_partial.json"
    P = json.loads(pf.read_text())
    res = {"id": f"screw_bend_{job}", "date": "2026-10-20", "owner": "fea3d", "job": job, "post": pf.name, "post_sha16": sha16(pf),
           "d3_mm": D3, "A_s_mm2": AS, "A_3_mm2": A3, "Z_3_mm3": round(Z3, 3), "doc": __doc__.split("\n")[0],
           "evidence": "SIM resultants + DERIVED check (A4-80 proxy k_T, k_Tu ASSUMED; d3 AS RECALLED; bending criterion TO-VERIFY)", "steps": {}}
    for st, o in P["steps"].items():
        sec, sc = o.get("screw_sections"), o.get("screw_check")
        if not sec or not sc:
            continue
        ss = sorted(sec, key=lambda s: s["x_prime_mm"])
        dmdx = [round((ss[i]["M_bend_Nmm"] - ss[i + 1]["M_bend_Nmm"]) / (ss[i + 1]["x_prime_mm"] - ss[i]["x_prime_mm"]), 1) for i in range(len(ss) - 1)]
        rec = {"label": o.get("label"), "T_C": sc.get("T_screw_C"), "kT_Rp_MPa": sc["kT_Rp_MPa"], "kTu_Rm_MPa": sc["kTu_Rm_MPa"],
               "sections": [{"x": s["x_prime_mm"], "N": round(s["N"], 1), "V": round(s["V"], 1), "M": round(s["M_bend_Nmm"], 1)} for s in ss],
               "statics_check_dMdx_vs_V": {"dMdx_N": dmdx, "V_N": [round(s["V"], 1) for s in ss]},
               "bending_arm_mm_at_x28.7": round(ss[0]["M_bend_Nmm"] / max(ss[0]["V"], 1e-9), 3), "checks": rows(ss, sc)}
        res["steps"][st] = rec
        c = rec["checks"]["x28.7"], rec["checks"]["x28.6_thread_entry_extrapolated"]
        print(st, rec["label"], "| M", c[0]["M_Nmm"], "arm", rec["bending_arm_mm_at_x28.7"], "| sigma_t+b", c[0]["sigma_t_plus_b_MPa"], "/", c[1]["sigma_t_plus_b_MPa"],
              "| MS_y fibre", c[0]["MS_y_fibre"], "/", c[1]["MS_y_fibre"], "vm-cons", c[0]["MS_y_vm_conservative"], "| MS_u el", c[0]["MS_u_interaction_elastic"], "/",
              c[1]["MS_u_interaction_elastic"], "pl", c[0]["MS_u_interaction_plastic_1.70_upper"], "/", c[1]["MS_u_interaction_plastic_1.70_upper"],
              "no-bend", c[0]["MS_u_interaction_no_bending"], "| dM/dx", rec["statics_check_dMdx_vs_V"]["dMdx_N"], flush=True)
    out = wd / "screw_bend.json"
    out.write_text(json.dumps(res, indent=1))
    print("wrote", out, sha16(out))


if __name__ == "__main__":
    main(sys.argv[1])
