"""m2_mass_v352 v1.0 (GNC rev4, 2026-10-13): simulator inputs for the v3.5.2 P2 sensitivity arm from Mechanical's
massprops_v3.5.2.json (hub 03-cad/v3.5.2, 8f887d83896aa7dd; lead CHANGELOG line 209: realised saving -91.6 g mid, engine
group -78.0 g from the TC-09 thinning, fixed -13.6 g from the Ti screws HW-121 / HW-123; SENSITIVITY, not a baseline; the
DERIVED -0.31 kg lever arm v352L of m2_mass_v351 v1.0 is WITHDRAWN by line 209 and is not flown).

Method: the m2_mass_v351 v1.0 mapping, unchanged, applied to the v3.5.2 file (P00 gimballed engine dry <- states.nograin.
engine; P06 ring <- states.mid.ring; P07 <- fixed GM-08/09/10/11/13/14/15 + EL-04; every other fixed item, the horns and the
pushrods -> one cfg point-mass ballast at the station that keeps the first moment exact, after removing the v3d P09 / P10
items it replaces; bleed valves 2 x 0.30 kg ASSUMED as in v3.5.1). The mapping function derive() is checked first on the
v3.5.1 file: it must reproduce m2_mass_v351 v1.0's v351 variant (ballast mass and station, landing-mass delta) and its
derived mechanical.json (iface_v351) byte for byte, so the v3.5.2 arm differs from v351 only through the CAD file.
Outputs: out/rev4/mass_v352/mass_v352_vs_v3d.json (variant v352), iface_v352 (+ README, MANIFEST), pins_rev4/
pins_rev4_v352.sha256. Closure through R.build (A1_none) and the 6-DOF engine-model check against the v3.5.2 engine states.
DERIVED; no hardware data; not physical approval."""
import csv
import hashlib
import json
import os
import sys
from collections import OrderedDict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_mass_v35 as M35  # noqa: E402
import m2_mass_v351 as M1  # noqa: E402  (helpers only: sha, z_of, closure, write_iface, constants; main() not run)

VERSION = "m2_mass_v352 v1.0"
SP = M1.SP
HUB = M1.HUB
OUT = f"{SP}/out/rev4/mass_v352"
MP351 = M1.MP351
MP352 = f"{HUB}/03-cad/v3.5.2/massprops_v3.5.2.json"
MD352 = f"{HUB}/03-cad/v3.5.2/massdelta_v3.5.2_vs_v3.5.1.json"
SHA = {MP351: "488b47f9d55ff91b", MP352: "8f887d83896aa7dd", MD352: "7e1726c9d9c0dfe5"}
V351_JSON = f"{SP}/out/rev4/mass_v351/mass_v351_vs_v3d.json"
IFACE = f"{SP}/iface_v352"
PIN = f"{SP}/pins_rev4/pins_rev4_v352.sha256"


def derive(mp, m3, led3d, zp):
    """m2_mass_v351 v1.0 main() mapping steps for one massprops file (variant 'as built')."""
    L = mp["ledger_mid"]
    fixed = [i for i in L if i["group"] == "fixed"]
    used = set()

    def take(pred):
        out = [i for i in fixed if pred(i) and id(i) not in used]
        for i in out:
            used.add(id(i))
        return out
    p07 = take(lambda i: i["pn"] in M1.P07_PN)
    fs = take(lambda i: i["pn"].startswith("ENG-FS-"))
    fd = take(lambda i: i["pn"].startswith("ENG-FD-"))
    bl = take(lambda i: i["pn"].startswith("ENG-BL-"))
    el = take(lambda i: i["pn"] in ("ENG-EL-11", "ENG-EL-12"))
    hw = take(lambda i: i["pn"].startswith("ENG-HW-"))
    if len(used) != len(fixed):
        raise RuntimeError(f"unassigned fixed items: {[i['pn'] for i in fixed if id(i) not in used]}")
    horn = [i for i in L if i["group"] == "horn"]
    push = [i for i in L if i["group"] == "pushrod"]
    st = mp["states"]
    eng_ng, ring = st["nograin"]["engine"], st["mid"]["ring"]
    gin = OrderedDict((s_, round(st[s_]["engine"]["m_kg"] - eng_ng["m_kg"], 6)) for s_ in ("wet", "mid", "burnout", "nograin"))
    rows = []
    rows.append(OrderedDict(item="P00 gimballed engine dry (no grain)", m_kg=eng_ng["m_kg"],
                            z_m=round(zp + eng_ng["cg_mm"][2] * 1e-3, 5), v3d_m_kg=led3d["P00"][0], v3d_z_m=led3d["P00"][1],
                            delta_m_kg=round(eng_ng["m_kg"] - led3d["P00"][0], 5),
                            delta_first_moment_kgm=round(eng_ng["m_kg"] * (zp + eng_ng["cg_mm"][2] * 1e-3)
                                                         - led3d["P00"][0] * led3d["P00"][1], 5), gimballed=True))
    rows.append(OrderedDict(item="P06 gimbal ring group", m_kg=ring["m_kg"], z_m=round(zp + ring["cg_mm"][2] * 1e-3, 5),
                            v3d_m_kg=led3d["P06"][0], v3d_z_m=led3d["P06"][1], delta_m_kg=round(ring["m_kg"] - led3d["P06"][0], 5),
                            delta_first_moment_kgm=round(ring["m_kg"] * (zp + ring["cg_mm"][2] * 1e-3)
                                                         - led3d["P06"][0] * led3d["P06"][1], 5), gimballed=False))
    sums = OrderedDict()
    for nm, its, key in (("P07 fixed TVC module", p07, "P07"), ("P09 <- MV module ENG-FS-*", fs, "P09"),
                         ("P10 <- fixed feed items ENG-FD-*", fd, "P10"), ("NEW bleed fixed side ENG-BL-*", bl, None),
                         ("NEW EL-11 + EL-12", el, None), ("NEW standard hardware ENG-HW-* (fixed)", hw, None),
                         ("NEW horns", horn, None), ("NEW pushrods", push, None)):
        r, m, mz = M35.group_row(nm, its, zp, (led3d[key][0], led3d[key][1]) if key else None)
        r = OrderedDict((k.replace("v35_", ""), v) for k, v in r.items())
        r["gimballed"] = False
        rows.append(r)
        sums[key or nm] = (m, mz)
    dM = sum(r["delta_m_kg"] for r in rows)
    dMZ = sum(r["delta_first_moment_kgm"] for r in rows)
    m07, mz07 = sums["P07"]
    cg07 = [sum(i["m_kg"] * i["cg_mm"][k] for i in p07) / m07 for k in range(3)]
    rest = [v for k, v in sums.items() if k != "P07"]
    mb = sum(m for m, _ in rest) - led3d["P09"][0] - led3d["P10"][0]
    mzb = sum(mz for _, mz in rest) - led3d["P09"][0] * led3d["P09"][1] - led3d["P10"][0] * led3d["P10"][1]
    zb = mzb / mb
    return dict(rows=rows, dM=dM, dMZ=dMZ, mb=mb, zb=zb, m07=m07, cg07=cg07, eng_ng=eng_ng, ring=ring, gin=gin, st=st)


def mech_json(m3, d, src_tag, mp_sha, vname, base_sha):
    """Derived mechanical.json as m2_mass_v351 v1.0 (same keys, same values; source strings name the file used)."""
    md = json.loads(json.dumps(m3))
    gd = md["gimballed_mass_properties"]
    g3 = m3["gimballed_mass_properties"]
    ring3 = g3.get("ring_alpha_axis_only") or m3["gimbal"]["ring_alpha_axis_only"]
    eng, ring = d["eng_ng"], d["ring"]
    src_ = f"{src_tag} ({mp_sha}) states.nograin.engine; GNC-DERIVED copy"
    gd["dry_grain_burnt"] = OrderedDict(
        m_kg=dict(v=eng["m_kg"], tag="CAD v3.5.1 (DERIVED+ASSUMED+ESTIMATE+CALC items)" if vname == "v351" else
                  "CAD v3.5.2 (DERIVED+ASSUMED+ESTIMATE+CALC items)", src=src_),
        cg_m=dict(v=[round(x * 1e-3, 7) for x in eng["cg_mm"]], tag="CAD v3.5.1" if vname == "v351" else "CAD v3.5.2",
                  src="engine frame, from the pivot"),
        I_pivot_kgm2=dict(v=eng["I_pivot_kgm2"], tag="CAD v3.5.1" if vname == "v351" else "CAD v3.5.2",
                          src="tensor about the pivot, engine axes"),
        I_cg_kgm2=dict(v=eng["I_cg_kgm2"], tag="CAD v3.5.1" if vname == "v351" else "CAD v3.5.2",
                       src="tensor about the own CG, engine axes"),
        grain_mass_inside_kg=dict(v=0.0, tag="DERIVED", src="state nograin"), superseded_v2_value=g3["dry_grain_burnt"])
    t = "CAD v3.5.1" if vname == "v351" else "CAD v3.5.2"
    rr = OrderedDict(m_kg=dict(v=ring["m_kg"], tag=t, src=f"{src_tag.split(' (')[0]} states.mid.ring"),
                     I_xx_pivot_kgm2=dict(v=ring["I_pivot_kgm2"][0][0], tag=t, src="ring group about the outer (X) axis"),
                     I_tensor_pivot_kgm2=dict(v=ring["I_pivot_kgm2"], tag=t), superseded_v2_value=ring3)
    if "ring_alpha_axis_only" in gd:
        gd["ring_alpha_axis_only"] = rr
    else:
        md["gimbal"]["ring_alpha_axis_only"] = rr
    fg = md["fixed_module"]["fixed_group_total_CAD_kg"]
    md["fixed_module"]["fixed_group_total_CAD_kg"] = dict(v=round(d["m07"], 6), tag=f"{t} (P07 subset: GM-08/09/10/11/"
                                                          "13/14/15, EL-04)", src=src_, cg_mm=[round(x, 3) for x in d["cg07"]],
                                                          superseded_v2_value=fg)
    md["gnc_derived_v351"] = dict(
        by=M1.VERSION if vname == "v351" else VERSION, date="2026-10-13", variant=vname,
        status="GNC-DERIVED simulator input; NOT a Mechanical publication",
        base_file=f"iface_v3d/mechanical.json v2 ({base_sha})",
        replaced=["gimballed_mass_properties.dry_grain_burnt", "gimbal.ring_alpha_axis_only", "fixed_module.fixed_group_total_CAD_kg"],
        not_replaced="every other key = v2 (stiffness, linkage, frames); version field kept 'v2' for the run6 strict check",
        rest_as_ballast=("see out/rev4/mass_v351/mass_v351_vs_v3d.json variants" if vname == "v351"
                         else "see out/rev4/mass_v352/mass_v352_vs_v3d.json variants"))
    return md


def main():
    os.makedirs(OUT, exist_ok=True)
    for p, h in SHA.items():
        if M1.sha(p) != h:
            raise RuntimeError(f"{p} sha256/16 {M1.sha(p)} != {h}")
    m3 = json.load(open(f"{M1.IF3D}/mechanical.json"))
    zp = float(m3["frames"]["rv1_station_of_pivot_m"]["v"])
    led3d = OrderedDict()
    with open(f"{SP}/out/vehicle_v3d/mass_ledger_v3d.csv") as f:
        for r in csv.DictReader(f):
            led3d[r["item"][:3]] = (float(r["m_kg"]), float(r["z_m"]), r["item"], r["tag"])
    base_sha = M1.sha(f"{M1.IF3D}/mechanical.json")
    # (1) self-check on v3.5.1 against m2_mass_v351 v1.0
    mp1 = json.load(open(MP351))
    d1 = derive(mp1, m3, led3d, zp)
    v1 = json.load(open(V351_JSON))
    w1 = v1["simulator"]["variants"]["v351"]
    md1 = mech_json(m3, d1, "massprops_v3.5.1.json", SHA[MP351], "v351", base_sha)
    s_md1 = hashlib.sha256(json.dumps(md1, indent=1).encode()).hexdigest()[:16]
    want_md1 = v1["simulator"]["derived_mechanical_json"]["v351"]["sha256_16"]
    chk = dict(ballast_kg=[round(d1["mb"], 5), w1["ballast_kg"]], ballast_z_m=[round(d1["zb"], 4), w1["ballast_z_m"]],
               landing_mass_delta_kg=[round(d1["dM"], 4), w1["landing_mass_delta_kg"]],
               derived_mechanical_json_sha16=[s_md1, want_md1])
    chk_ok = all(a == b for a, b in chk.values())
    print("self-check on v3.5.1 vs m2_mass_v351 v1.0:", chk, "OK" if chk_ok else "FAIL", flush=True)
    if not chk_ok:
        raise RuntimeError("derive() does not reproduce m2_mass_v351 v1.0 on v3.5.1")
    # (2) v3.5.2
    mp2 = json.load(open(MP352))
    if mp2.get("cad_version") != "v3.5.2":
        raise RuntimeError("not the v3.5.2 massprops")
    d2 = derive(mp2, m3, led3d, zp)
    md2 = mech_json(m3, d2, "massprops_v3.5.2.json", SHA[MP352], "v352", base_sha)
    M1.IFACES["v352"] = IFACE
    M1.PINS["v352"] = PIN
    hm = M1.write_iface("v352", md2)
    rd = open(os.path.join(IFACE, "README.txt")).read().replace("massprops_v3.5.1.json values", "massprops_v3.5.2.json values "
                                                                "(lead line 209 sensitivity)").replace(
        "out/rev4/mass_v351/mass_v351_vs_v3d.json", "out/rev4/mass_v352/mass_v352_vs_v3d.json")
    open(os.path.join(IFACE, "README.txt"), "w").write(rd.replace(f"({M1.VERSION})", f"({VERSION})"))
    variant = dict(label="sensitivity (b'): CAD v3.5.2 as built (Mechanical file, line 209): TC-09 thinning (conditional) + "
                         "Ti screws HW-121/123; bleed valves 2 x 0.30 kg ASSUMED", iface=IFACE, pin=PIN,
                   ballast_kg=round(d2["mb"], 5), ballast_z_m=round(d2["zb"], 4), landing_mass_delta_kg=round(d2["dM"], 4),
                   vs_v351_kg=round(d2["dM"] - d1["dM"], 4))
    # closure and engine-model check (as m2_mass_v351 v1.0)
    M1.GIN.clear()
    M1.GIN.extend(d2["gin"].values())
    c3 = M1.closure(M1.IF3D, M1.PINS_REV2)
    c = M1.closure(IFACE, PIN, variant["ballast_kg"], variant["ballast_z_m"])
    clos = dict(ledger_dm_kg=round(c["m"] - c3["m"], 5), mapped_dm_kg=variant["landing_mass_delta_kg"],
                ok=abs((c["m"] - c3["m"]) - variant["landing_mass_delta_kg"]) < 2e-4,
                ledger_dfirst_moment_kgm=round(c["mz"] - c3["mz"], 5), mapped_dfirst_moment_kgm=round(d2["dMZ"], 5),
                first_moment_ok=abs((c["mz"] - c3["mz"]) - d2["dMZ"]) < 2e-3, gimballed_dm_kg=round(c["gimb_m"] - c3["gimb_m"], 5))
    eng_chk = []
    for s_, g_ in d2["gin"].items():
        me_, le_, Ip_ = c["eng"][str(g_)]
        ref = d2["st"][s_]["engine"]
        ref_I = 0.5 * (ref["I_pivot_kgm2"][0][0] + ref["I_pivot_kgm2"][1][1])
        eng_chk.append(dict(state=s_, grain_inside_kg=g_, m_sim=round(me_, 5), m_ref=ref["m_kg"], le_sim_mm=round(le_, 3),
                            le_ref_mm=ref["cg_mm"][2], Ipiv_sim=round(Ip_, 6), Ipiv_ref_mean_xx_yy=round(ref_I, 6),
                            dI_pct=round(100 * (Ip_ / ref_I - 1), 3),
                            ok=bool(abs(me_ - ref["m_kg"]) < 1e-3 and abs(le_ - ref["cg_mm"][2]) < 0.5 and abs(Ip_ / ref_I - 1) < 0.01)))
    res = OrderedDict(
        version=VERSION, date="2026-10-13",
        inputs={os.path.basename(p): dict(path=p, sha256_16=h) for p, h in SHA.items()},
        status="SENSITIVITY (line 209): v3.5.2 is not a baseline; TC-09 thinning conditional on its thermal / S-AX re-run",
        self_check_on_v351=dict(values=chk, ok=chk_ok),
        mapping=d2["rows"],
        totals=dict(landing_mass_delta_kg=dict(v=round(d2["dM"], 4), tag="DERIVED (CAD v3.5.2 groups mapped on ledger v3d)"),
                    vs_v351_kg=round(d2["dM"] - d1["dM"], 4), first_moment_delta_kgm=round(d2["dMZ"], 5)),
        grain_inside_by_state_kg=d2["gin"], engine_model_check=dict(v352=eng_chk),
        simulator=dict(derived_mechanical_json=dict(v352=dict(path=f"{IFACE}/mechanical.json", sha256_16=hm)),
                       pin_lists=dict(v352=dict(path=PIN, sha256_16=M1.sha(PIN))), variants=dict(v352=variant),
                       closure=dict(v352=clos, v3d_ledger_dry_kg=round(c3["m"], 4))),
        withdrawn=dict(v352L="the DERIVED -0.31 kg lever arm of m2_mass_v351 v1.0 (iface_v352L) is WITHDRAWN by line 209 "
                             "(realised -91.6 g); not flown"),
        open_items=["bleed valves 2 x 0.30 kg ASSUMED (MASS RISK) until a datasheet",
                    "not in massprops v3.5.2: the close-coupled Pc transducer and the tank (OI-32 MISSING), as v3.5.1"])
    p = f"{OUT}/mass_v352_vs_v3d.json"
    with open(p, "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(dict(variant=variant, closure=clos, engine_model_check=eng_chk), indent=1))
    print("out", p, M1.sha(p))


if __name__ == "__main__":
    main()
