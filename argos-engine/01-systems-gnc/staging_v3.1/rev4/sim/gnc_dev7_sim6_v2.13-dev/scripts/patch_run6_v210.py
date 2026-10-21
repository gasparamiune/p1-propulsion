"""patch_run6_v210 v1.0 (GNC rev3, 2026-10-13): run6 v2.10-dev, the parameters of sim6 v2.10-dev amendment V2 (pv2_*) and the
pinned Combustion cold-flow tables (cold_flow_thrust_v2p4a.csv e094c4be80d12f66 / .json a226dfacf494cb2c). Source run6 v2.9-dev
b054a222eff38b6e; every anchor must occur exactly once."""
import hashlib
import sys

P = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/work/space/gnc_dev4/gncsim/run6.py"
SRC16 = "b054a222eff38b6e"
s = open(P).read()
h = hashlib.sha256(s.encode()).hexdigest()[:16]
if h != SRC16:
    raise SystemExit(f"{P}: sha256/16 {h} != v2.9-dev {SRC16} (already patched?)")


def rep(old, new, count=1):
    global s
    n = s.count(old)
    if n != count:
        raise SystemExit(f"anchor found {n} times (expected {count}): {old[:90]!r}")
    s = s.replace(old, new)


rep('"""run6 v2.9-dev (v2.9-dev amendments G', '"""run6 v2.10-dev (v2.10-dev amendment V2 (R2 v2: command hold, baseline modes, cold-flow thrust after an '
    'undetected flame-out from the pinned Combustion v2.4a tables, release hold; pv2_*); v2.9-dev amendments G')
rep('''def cfg_of(**kw):
''', '''# v2.10-dev amendment V2 (R2 v2; sim6 pv2_*), off by default
DEF.update(pv2_on=0, pv2_hold=0, pv2_Fh=62.5, pv2_bl=0, pv2_cold=0, pv2_ck=1.0, pv2_lrate=16.667, pv2_llag=0.010, pv2_rh=0.0)
COLD_DIR = os.environ.get("GNC_COMB_V2P4A", "/home/claude/work/shared-fallback/engine/02-combustion/data/v2p4a")
COLD_PIN16 = {"cold_flow_thrust_v2p4a.csv": "e094c4be80d12f66", "cold_flow_thrust_v2p4a.json": "a226dfacf494cb2c"}


def cold_tables():
    """Combustion v2.4a cold-flow tables for sim6 amendment V2: F / mdot (DERIVED adiabatic bound; DERIVED HEM nominal Cd
    0.70, optimum expansion) on (tank pressure, lift) from cold_flow_thrust_v2p4a.csv, and the open-loop map lift per ECU
    command (S230 map, Cd 0.70) per tank state from cold_flow_thrust_v2p4a.json (per_F_cmd). Both files must match their
    embedded sha256/16 and the GNC_IFACE_PIN list (engine_v2.pin_check)."""
    import csv
    import hashlib
    if "cold" in _C:
        return _C["cold"]
    pc = os.path.join(COLD_DIR, "cold_flow_thrust_v2p4a.csv")
    pj = os.path.join(COLD_DIR, "cold_flow_thrust_v2p4a.json")
    for p in (pc, pj):
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
        if h != COLD_PIN16[os.path.basename(p)]:
            raise RuntimeError(f"{p} sha256/16 {h} != pinned {COLD_PIN16[os.path.basename(p)]}")
        engine_v2.pin_check(p)
    rows = []
    with open(pc) as f:
        rd = csv.reader(f)
        hdr = None
        for r in rd:
            if not r:
                continue
            if hdr is None:
                if r[0] == "state":
                    hdr = r
                continue
            rows.append(dict(zip(hdr, r)))
    st = {}
    for r in rows:
        st.setdefault(r["state"], []).append(r)
    j = json.load(open(pj))
    keys = sorted(st, key=lambda k: float(st[k][0]["P_tank_Pa"]))
    lifts = [float(r["lift_mm"]) for r in st[keys[0]]]
    out = dict(states=keys, P=[], lifts=lifts, Fb=[], Fn=[], mb=[], mn=[], cmds=None, cl=[])
    for k in keys:
        rr = st[k]
        if [float(r["lift_mm"]) for r in rr] != lifts:
            raise RuntimeError(f"cold-flow table: lift grid of {k} differs")
        out["P"].append(float(rr[0]["P_tank_Pa"]))
        out["Fb"].append([float(r["F_bound_N"]) for r in rr])
        out["Fn"].append([float(r["F_nom_opt_N"]) for r in rr])
        out["mb"].append([float(r["mdot_bound_kg_s"]) for r in rr])
        out["mn"].append([float(r["mdot_nom_kg_s"]) for r in rr])
        pf = [e for e in j["states"][k]["per_F_cmd"] if isinstance(e.get("F_cmd_N"), (int, float))]
        cm = [float(e["F_cmd_N"]) for e in pf]
        if out["cmds"] is None:
            out["cmds"] = cm
        elif cm != out["cmds"]:
            raise RuntimeError(f"cold-flow json: command grid of {k} differs")
        out["cl"].append([float(e["lift_mm"]) for e in pf])
    out["src"] = f"{pc} (e094c4be80d12f66); {pj} (a226dfacf494cb2c)"
    _C["cold"] = out
    return out


def cfg_of(**kw):
''')
rep('''    S("pcf_fo", float(cfg["pcf_fo"]), "CONFIG 1 = truth flame-out at the Pc-invalid onset, undetected (ECU stays in RUN; sim6 v2.9-dev V)")
''', '''    S("pcf_fo", float(cfg["pcf_fo"]), "CONFIG 1 = truth flame-out at the Pc-invalid onset, undetected (ECU stays in RUN; sim6 v2.9-dev V)")
    # v2.10-dev amendment V2 (R2 v2; LEAD lines 181 (4), 186 (1)-(2))
    S("pv2_on", float(cfg["pv2_on"]), "CONFIG 1 = sim6 v2.10-dev amendment V2 (hold, baseline modes, cold flow, release hold)")
    S("pv2_hold", float(cfg["pv2_hold"]), "DESIGN LEAD line 186 (2): 1 = ECU open-loop command held at the start level while the "
                                          "drogue is attached with Pc invalid, until the release")
    S("pv2_Fh", float(cfg["pv2_Fh"]), "DESIGN LEAD line 186 (2) start level of the hold [N] (Combustion F_lift 62.5 N)")
    S("pv2_bl", float(cfg["pv2_bl"]), "PROPOSAL GNC R2 v2 baseline mode deciding the release: 0 E0-frozen (amendment V), 1 "
                                      "re-reference at E2, 2 = 0 + drogue-drag compensation, 3 = 1 + drogue-drag compensation")
    S("pv2_cold", float(cfg["pv2_cold"]), "CONFIG cold-flow thrust after the undetected flame-out: 0 none (amendment V), 1 "
                                          "DERIVED adiabatic bound (design case, LEAD 186 (2)), 2 DERIVED HEM nominal Cd 0.70 "
                                          "(sensitivity)")
    S("pv2_ck", float(cfg["pv2_ck"]), "ASSUMED cold-flow thrust factor (1.3 = chamber heat pick-up sensitivity, LEAD 186 (2); "
                                      "heat pick-up itself TO-VERIFY, CF-3 load cell / T-series post-burn pulse)")
    S("pv2_lrate", float(cfg["pv2_lrate"]), "DERIVED Combustion cold_flow_thrust_v2p4a constants: HV69 drive rate [mm/s]")
    S("pv2_llag", float(cfg["pv2_llag"]), "ASSUMED Combustion cold_flow_thrust_v2p4a constants: drive lag [s]")
    S("pv2_rh", float(cfg["pv2_rh"]), "PROPOSAL LEAD line 186 (1) alternative (unpurged relight): no release before E2 + pv2_rh "
                                      "[s]; 0 = off")
    if cfg["pv2_on"] and cfg["pv2_cold"]:
        ct = cold_tables()
        n_p, n_l, n_c = len(ct["P"]), len(ct["lifts"]), len(ct["cmds"])
        if n_p > 4 or n_l > 24 or n_c > 12:
            raise RuntimeError("cold-flow table larger than the sim6 pv2 slots")
        S("pv2_np", float(n_p), "DERIVED Combustion cold-flow table: tank states")
        S("pv2_nl", float(n_l), "DERIVED Combustion cold-flow table: lifts")
        S("pv2_nc", float(n_c), "DERIVED Combustion open-loop map: commands")
        for i_, pv_ in enumerate(ct["P"]):
            par[getattr(s6, f"P_pv2_P{i_}")] = pv_
        for j_, lv_ in enumerate(ct["lifts"]):
            par[getattr(s6, f"P_pv2_l{j_}")] = lv_
        for j_, cv_ in enumerate(ct["cmds"]):
            par[getattr(s6, f"P_pv2_c{j_}")] = cv_
        for i_ in range(n_p):
            for j_ in range(n_l):
                par[getattr(s6, f"P_pv2_Fb{i_ * n_l + j_}")] = ct["Fb"][i_][j_]
                par[getattr(s6, f"P_pv2_Fn{i_ * n_l + j_}")] = ct["Fn"][i_][j_]
                par[getattr(s6, f"P_pv2_mb{i_ * n_l + j_}")] = ct["mb"][i_][j_]
                par[getattr(s6, f"P_pv2_mn{i_ * n_l + j_}")] = ct["mn"][i_][j_]
            for j_ in range(n_c):
                par[getattr(s6, f"P_pv2_cl{i_ * n_c + j_}")] = ct["cl"][i_][j_]
        T("pv2_tables", ct["src"], "DERIVED Combustion v2.4a cold_flow_thrust (bound: Cd 0.80, no line loss, isentropic "
                                   "equilibrium to 1 atm, adiabatic; nominal: HEM Cd 0.70, optimum expansion); tank states "
                                   + ", ".join(ct["states"]))
''')
open(P, "w").write(s)
print("patched", P, hashlib.sha256(s.encode()).hexdigest()[:16])
