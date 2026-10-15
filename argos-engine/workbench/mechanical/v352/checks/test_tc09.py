"""v3.5.2 TC-09 thinning: solid validity, volume, mass and key stations for V351_ON vs V352_ON (engine include only). Mechanical 2026-10-13."""
import sys, json, time
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/03-cad/src")
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/04-fea/src")
import config, build
out = {}
for name, ov in (("v351", dict(config.V351_ON)), ("v352", dict(config.V352_ON))):
    t0 = time.time()
    P, S, reg, clog = build.build(include=("engine",), iterate_cg=False, overrides=ov)
    p = [x for x in reg if x.pn == "ENG-TC-09"][0]
    rows, _ = build.mass_ledger(reg, P, state="wet", S=S)
    mrow = sum(r["m"] for r in rows if r["pn"] == "ENG-TC-09")
    eng_m = sum(r["m"] for r in rows if r["group"] == "engine")
    V = p.shape.Volume()
    rho = mrow / (V * 1e-9)
    out[name] = {"valid": bool(p.shape.isValid()), "V_mm3": round(V, 1), "material": p.material, "rho": rho,
                 "m_kg": round(mrow, 5), "engine_group_wet_kg": round(eng_m, 5),
                 "aft_section": S.get("aft_section"), "aft_socket_step": S.get("aft_socket_step"), "aft_cone": S.get("aft_cone"),
                 "tube_aft": S.get("tube_aft"), "aft_land_top": S.get("aft_land_top"), "aft_thread_top": S.get("aft_thread_top"),
                 "aft_gland": S.get("aft_gland"), "t_s": round(time.time() - t0, 1)}
    print(name, json.dumps(out[name], default=str)[:900], flush=True)
json.dump(out, open("/home/claude/work/mechanical/v352/checks/test_tc09_v1.json", "w"), indent=1, default=str)
