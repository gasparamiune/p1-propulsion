"""REV-GNC-6 v05: attack on the ENG-11 K_s requirement (rev4 item [12]) with the author's own linear model, imported
unchanged from the staged m2_eng11 v1.1 (V5c structure, nominal J 1.6e-3, 'cons' kinematics, fixed ECU notch Q 1 / -12 dB
at e x the landing centre-pose mode, e 0.95 / 1 / 1.05, zeta 0.02 / 0.05 / 0.10, floor20 conditions; ENG-07d: stable and
upper GM >= 6 dB at every corner).
 (A) reproduction: selected rows of the author's 10 N m/rad grid recomputed with E.scan (9 discrete V5c poses).
 (B) continuous pose envelope: the loop depends on (f, zeta) only, and the rocking-mode frequency moves continuously with
     the gimbal angle between the 9 FE poses (continuity ASSUMED; the FE gives stiffness at the 9 poses only), so every
     frequency between the condition's pose minimum and maximum is reachable inside the 7 deg cone.  Each corner is
     re-evaluated on a dense frequency grid over [f_min, f_max] of its condition (0.1 Hz + 0.02 Hz within +/-1 Hz of the
     condition's bending frequency).  A K_s that passes on the 9 poses but fails here passes only by pose sampling.
 (C) bending-frequency sweep: every condition's bending frequency scaled so the full-tank mode is 10 / 12 / 15 / 18 / 20 /
     22 / 24.3 / 27 / 30 Hz (gnc.json v3.1 airframe_first_bending_min_Hz is 10 Hz, goal 15 Hz) for K_s 100 / 110 / 120 / 130,
     discrete poses and continuous envelope.
DERIVED (linear); K_s, J, bending, damping ASSUMED; no hardware data; not physical approval.
Usage: python -I v05_eng11_env.py <tree> <out.json> [parts A,B,C]"""
import json, os, sys, time
TREE, OUT = sys.argv[1], sys.argv[2]
PARTS = (sys.argv[3] if len(sys.argv) > 3 else "A,B,C").split(",")
sys.path.insert(0, TREE)
sys.path.insert(0, os.path.join(TREE, "scripts"))
import numpy as np  # noqa: E402
import m2_eng11 as E  # noqa: E402

t00 = time.time()
d5, T, n_m, gchk = E.v5c_table()
conds, meta, src, extra, cchk = E.conditions()
M = E.Model(T, n_m, conds)
NOTCH = ("fixed", 1.0) + E.NOTCH_ECU
fb0 = {k: v["w_b"] / (2 * np.pi) for k, v in conds.items()}
out = dict(script="v05_eng11_env (REV-GNC-6)", tag="DERIVED (linear, author's model imported unchanged)", base=E.VERSION,
           base_sha16=E.sha16(E.__file__), iface=os.environ.get("GNC_IFACE"), mass_variant=E.MASS_VARIANT, cfg_ballast=extra,
           bending_Hz=fb0, poses=M.poses, A={}, B={}, C={})
print(f"v05: {E.VERSION} mass {E.MASS_VARIANT} {extra}; poses {M.poses}; bending full {fb0['full|max500N|act_nom|noaero']:.3f} Hz", flush=True)


def discrete(a, Ks):
    r = E.scan(M, (Ks,), E.J_C, "cons", "T", NOTCH, axes=(a,))[f"{a}|Ks{Ks:g}"]["floor20"]
    return dict(pass_6dB=r["pass_6dB"], gm_up_min_dB=r["gm_up_min_dB"], n_below_6dB=r["n_below_6dB"], n=r["n"], worst=r["worst"])


def envelope(a, Ks, step=0.1, fine=0.02, near=1.0):
    fn_c = M.f("centre", a, Ks, E.J_C, "cons", "T")          # notch reference: landing-state centre-pose mode
    worst, nbad, n, fails = None, 0, 0, []
    per_cond = {}
    for cn, cond in M.conds.items():
        if E.is62(cn):
            continue
        fp = [M.f(p, a, Ks, E.J_C, "cons", "T", Ip=cond["I_piv"]) for p in M.poses]
        lo, hi = min(fp), max(fp)
        fbend = cond["w_b"] / (2 * np.pi)
        grid = set(np.round(np.arange(lo, hi + 1e-9, step), 4).tolist()) | set(np.round(fp, 6).tolist())
        grid |= set(np.round(np.arange(max(lo, fbend - near), min(hi, fbend + near) + 1e-9, fine), 4).tolist())
        grid = sorted(x for x in grid if lo - 1e-9 <= x <= hi + 1e-9)
        cw = None
        for e in E.ERRS:
            nt = (NOTCH[1] * e * fn_c, NOTCH[2], NOTCH[3])
            for zr in E.ZETAS:
                for f_r in grid:
                    st, gm, pm, ok, pma, sm = E.ev(cn, cond, float(f_r), zr, nt)
                    n += 1
                    g = gm if st else -99.0
                    if g is not None and (cw is None or g < cw[0]):
                        cw = (g, f_r, e, zr)
                    if not ok:
                        nbad += 1
                        if len(fails) < 12:
                            fails.append(f"{cn}|e{e:g}|z{zr:g}|f{f_r:.2f}|GM{(gm if st else float('nan')):.2f}")
        per_cond[cn] = dict(f_range_Hz=[round(lo, 3), round(hi, 3)], bending_Hz=round(fbend, 3), n_f=len(grid),
                            worst_gm_dB=(None if cw is None else round(cw[0], 3)), worst_at=(None if cw is None else [round(cw[1], 3), cw[2], cw[3]]))
        if cw is not None and (worst is None or cw[0] < worst[0]):
            worst = (cw[0], cn, cw[1], cw[2], cw[3])
    return dict(pass_6dB=(nbad == 0), n_corners=n, n_below_6dB=nbad, gm_up_min_dB=(None if worst is None else round(worst[0], 3)),
                worst=(None if worst is None else f"{worst[1]}|f{worst[2]:.3f}|e{worst[3]:g}|z{worst[4]:g}"), first_fails=fails,
                per_cond=per_cond, notch_ref_Hz=round(fn_c, 3))


def with_bending(scale, fn):
    c0 = M.conds
    M.conds = {k: dict(v, w_b=v["w_b"] * scale) for k, v in c0.items()}
    E._CACHE.clear()
    try:
        return fn()
    finally:
        M.conds = c0
        E._CACHE.clear()


A_ROWS = [("alpha", 100.0), ("alpha", 130.0), ("alpha", 140.0), ("alpha", 160.0), ("beta", 100.0), ("beta", 150.0),
          ("beta", 160.0), ("beta", 190.0), ("beta", 220.0)]
B_ROWS = [("alpha", k) for k in (100.0, 110.0, 120.0, 130.0, 160.0, 190.0, 220.0, 250.0, 270.0)] + \
         [("beta", k) for k in (100.0, 110.0, 120.0, 130.0, 140.0, 150.0, 190.0, 220.0, 230.0, 250.0, 270.0)]
if "A" in PARTS:
    for a, k in A_ROWS:
        t0 = time.time()
        out["A"][f"{a}|Ks{k:g}"] = discrete(a, k)
        r = out["A"][f"{a}|Ks{k:g}"]
        print(f"A {a:5s} Ks {k:5.0f}: {'PASS' if r['pass_6dB'] else 'fail'} GM {r['gm_up_min_dB']:.2f} <6dB {r['n_below_6dB']}/{r['n']} ({time.time() - t0:.0f} s)", flush=True)
if "B" in PARTS:
    for a, k in B_ROWS:
        t0 = time.time()
        r = envelope(a, k)
        out["B"][f"{a}|Ks{k:g}"] = r
        print(f"B {a:5s} Ks {k:5.0f}: continuous {'PASS' if r['pass_6dB'] else 'FAIL'} GM {r['gm_up_min_dB']} <6dB {r['n_below_6dB']}/{r['n_corners']} worst {r['worst']} ({time.time() - t0:.0f} s)", flush=True)
        json.dump(out, open(OUT, "w"), indent=1, default=str)
if "C" in PARTS:
    f_full0 = fb0["full|max500N|act_nom|noaero"]
    for fb in (10.0, 12.0, 15.0, 18.0, 20.0, 22.0, 24.3, 27.0, 30.0):
        sc = fb / f_full0
        for a in ("alpha", "beta"):
            for k in (100.0, 110.0, 120.0, 130.0):
                t0 = time.time()
                rd = with_bending(sc, lambda: discrete(a, k))
                rc = with_bending(sc, lambda: envelope(a, k, step=0.2, fine=0.05, near=1.0))
                out["C"][f"fb{fb:g}|{a}|Ks{k:g}"] = dict(scale=sc, discrete=rd, continuous={kk: rc[kk] for kk in ("pass_6dB", "gm_up_min_dB", "n_below_6dB", "n_corners", "worst", "first_fails")})
                print(f"C fb {fb:5.1f} Hz {a:5s} Ks {k:5.0f}: discrete {'PASS' if rd['pass_6dB'] else 'fail'} {rd['gm_up_min_dB']:.2f} | continuous {'PASS' if rc['pass_6dB'] else 'FAIL'} {rc['gm_up_min_dB']} ({time.time() - t0:.0f} s)", flush=True)
                json.dump(out, open(OUT, "w"), indent=1, default=str)
out["wall_s"] = round(time.time() - t00, 1)
json.dump(out, open(OUT, "w"), indent=1, default=str)
print("done", out["wall_s"], flush=True)
