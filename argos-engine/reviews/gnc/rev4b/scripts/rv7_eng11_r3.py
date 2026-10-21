"""rv7_eng11_r3 v1.0 (REV-GNC-7 reviewer, 2026-10-21): ENG-07d loop on the v3.5.2 R3 pose stiffness table and at both ends
of its range_over_posted_R3_poses band (lead CHANGELOG 250 (6)), with the GNC author's linear tooling (m2_eng11_fe v1.0 and
m2_eng11 v1.1, imported unchanged).  Only the FE structure input is replaced:

  S(p, a)  FE rigid-servo K of the R3 pose runs (k_table_r3_v352.json f3c7cfbcfb98bcd7, 'FE_coupled_<axis>' R3 value: other
           axis moment-free, the same quantity as the c71 K_FE_engine the author used: equal to its v351 column within 0.5 N m/rad).
  g(p, a)  as the author: V5c g on the 9 cone poses, exact CAD kinematics at the 8 stops ('v5c'); or the factor implied by the
           R3 with-servo k_s58 value, g = 1 / (58 (1/K_s58 - 1/S)) ('r3': FEA3D's RM2-05 r_eff servo factor).
  Band ends ('Sfix'): S = the band minimum (lo) or maximum (hi) of the axis at EVERY pose (cone + stops), g per pose; the ECU
           notch stays referenced on the bench plant = the R3 table at the centre pose (T_REF, rigid fixture), since B-TVC-1
           measures the hardware at neutral.
Everything else (conditions floor20 on iface_v351 + v351 ballast, notch rule Q 1 / -12 dB at e x landing centre mode,
e 0.95 / 1 / 1.05, zeta 0.02 / 0.05 / 0.10, continuous pose envelope, ENG-07d = stable and upper GM >= 6 dB) is the author's.
DERIVED (linear) from SIM FE stiffness; K_s, J, bending, damping ASSUMED; not physical approval.
Env: RV7_VARIANTS=<comma list>, GNC_E11FE_OUT=<dir>; RV7_KS=<comma list of K_s> (default the author's 90-160 step 5)."""
import json
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_eng11_fe as F  # noqa: E402
import m2_eng11 as E  # noqa: E402

VERSION = "rv7_eng11_r3 v1.0"
KT = f"{F.HUB}/04-fea/assembly3d_v352/results/v352/k_table_r3_v352.json"
KT_SHA16 = "f3c7cfbcfb98bcd7"


def load_r3():
    if F.sha16(KT) != KT_SHA16:
        raise RuntimeError("k_table_r3_v352.json sha mismatch")
    d = json.load(open(KT))
    rows = {r["pose"]: r for r in d["rows"]}
    rng = d["range_over_posted_R3_poses"]
    band = {}
    for a in F.AXES:
        band[a] = dict(lo=min(rng[f"FE_coupled_{a}"]["min"], rng[f"FE_diagonal_{a}"]["min"]),
                       hi=max(rng[f"FE_coupled_{a}"]["max"], rng[f"FE_diagonal_{a}"]["max"]))
    return d, rows, band


R3D, R3ROWS, R3BAND = load_r3()
_orig_fe_runs = F.fe_runs


def fe_runs_r3():
    """Same structure as m2_eng11_fe.fe_runs, with the R3 values: K = FE coupled R3, g_fea = implied by the R3 k_s58 value,
    g_fea174 = implied by the k_s174 value; the compliant-airframe spring of the author's c71 run is kept (unused here)."""
    out0, chk0 = _orig_fe_runs()
    out = {}
    for nm, r0 in out0.items():
        row = R3ROWS[nm]
        if [round(x, 3) for x in row["pose_deg"]] != [round(x, 3) for x in r0["pose_deg"]]:
            raise RuntimeError(f"pose mismatch {nm}: {row['pose_deg']} vs {r0['pose_deg']}")
        ax = {}
        for a in F.AXES:
            v = row["values"]
            S = float(v[f"FE_coupled_{a}"]["R3"])
            k58 = float(v[f"k_s58_coupled_{a}"]["R3"])
            k174 = float(v[f"k_s174_coupled_{a}"]["R3"])
            ax[a] = dict(K=S, K_noz=None, g_fea=1.0 / (58.0 * (1.0 / k58 - 1.0 / S)), g_fea174=1.0 / (174.0 * (1.0 / k174 - 1.0 / S)),
                         share=None, K_rods=None, K_v351=float(v[f"FE_coupled_{a}"]["v351"]), K_c71=r0["axes"][a]["K"])
        out[nm] = dict(pose_deg=r0["pose_deg"], run=row["run"], airframe="rigid", axes=ax)
    chk = dict(chk0, r3_table=KT, r3_table_sha16=KT_SHA16, r3_band=R3BAND,
               c71_vs_r3_v351_max_abs=max(abs(out[n]["axes"][a]["K_c71"] - out[n]["axes"][a]["K_v351"]) for n in out for a in F.AXES))
    return out, chk


F.fe_runs = fe_runs_r3


class CtxR3(F.Ctx):
    def table(self, spec, bench=False):
        T = super().table(spec, bench=bench)
        if spec.get("Sfix") and not bench:
            for (p, a), v in T.items():
                v["S"]["T"] = float(R3BAND[a][spec["Sfix"]])
        if spec.get("g") == "r3":
            for (p, a), v in T.items():
                v["g"] = float(self.FE[F.V5C2FE.get(p, p)]["axes"][a]["g_fea"])
        return T


_B = dict(F._B, poses="cone+stop", src="R3")
NEW = {
    "R3P_JC": dict(_B), "R3P_JLO": dict(_B, J="J_LO"), "R3P_JHI": dict(_B, J="J_HI"),
    "R3Hi_JC": dict(_B, Sfix="hi"), "R3Lo_JC": dict(_B, Sfix="lo"),
    "R3Hi_JLO": dict(_B, Sfix="hi", J="J_LO"), "R3Lo_JLO": dict(_B, Sfix="lo", J="J_LO"),
    "R3Hi_JHI": dict(_B, Sfix="hi", J="J_HI"), "R3Lo_JHI": dict(_B, Sfix="lo", J="J_HI"),
    "R3C_JC": dict(_B, poses="cone"), "R3G_JC": dict(_B, g="r3"),
}
for k, v in NEW.items():
    if v.get("g") == "r3":
        v = dict(v)
    F.VARIANTS[k] = v
if os.environ.get("RV7_KS"):
    F.KS = tuple(float(x) for x in os.environ["RV7_KS"].split(","))


def g_compare(ctx):
    """Implied R3 servo factor (k_s58 and k_s174) against the loop's g (V5c cone / kin stops) per pose and axis."""
    rows = {}
    for p in F.CONE + F.STOPS:
        fe = ctx.FE[F.V5C2FE.get(p, p)]["axes"]
        r = {}
        for a in F.AXES:
            gl = ctx.T5[(p, a)]["g"] if p in F.V5C2FE else ctx.kin[p][a]
            r[a] = dict(g_loop=round(gl, 4), g_r3_58=round(fe[a]["g_fea"], 4), g_r3_174=round(fe[a]["g_fea174"], 4),
                        r3_over_loop=round(fe[a]["g_fea"] / gl, 4), S_R3=fe[a]["K"], S_v351=fe[a]["K_v351"],
                        S_ratio=round(fe[a]["K"] / fe[a]["K_v351"], 4))
        rows[p] = r
    return rows


def main():
    os.makedirs(F.OUT, exist_ok=True)
    ctx = CtxR3()
    gc = g_compare(ctx)
    json.dump(dict(version=VERSION, r3_band=R3BAND, fe_chk=ctx.fe_chk, g_compare=gc), open(os.path.join(F.OUT, "rv7_r3_inputs.json"), "w"),
              indent=1, default=str)
    print(f"{VERSION} on {F.VERSION} / {E.VERSION}; band {R3BAND}; KS {F.KS}", flush=True)
    for vid in [v for v in os.environ.get("RV7_VARIANTS", "").split(",") if v]:
        F.run_variant(ctx, vid)
        print(f"== {vid} done", flush=True)


if __name__ == "__main__":
    main()
