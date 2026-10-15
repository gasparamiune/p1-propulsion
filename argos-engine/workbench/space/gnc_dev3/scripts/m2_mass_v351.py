"""m2_mass_v351 v1.0 (GNC rev4, 2026-10-13): landing-mass delta of the FROZEN CAD v3.5.1 mass properties (hub
03-cad/v3.5.1/massprops_v3.5.1.json, lead CHANGELOG line 206 (1)) against the GNC mass ledger v3d, and the derived simulator
inputs for the P2 apogee re-fly (lead 204 (3); coordinator rev4 P2 message):
  v351   CAD v3.5.1 as built: standard hardware CALC 0.22387 kg (above the 0.20 kg allowance, carried as max(allowance,
         CALC) by Mechanical), bleed valves 2 x 0.30 kg ASSUMED
  v351t  sensitivity (a): bleed valves at the 0.15 kg target each (-0.30 kg at the valve stations; DESIGN TARGET, no datasheet)
  v352L  sensitivity (b): the v3.5.2 levers approved in line 206 (2) applied to the v3.5.1 ledger, DERIVED here from the
         lead's lever masses (Mechanical's v3.5.2 massprops is pending and replaces this arm):
           (a) TC-09 IN718 socket OD step + barrel wall 1.8 mm: -0.11 kg at the TC-09 CG (gimballed)
           (b) Ti-6Al-4V non-wetted screws: -0.09 kg spread over the HARDWARE CALC items in proportion to their mass
               (which screws are non-wetted is not in the ledger: proportional spread ASSUMED)
           (c) feed 316L -> 6061-T6 upstream of the main valve: -0.086 kg spread over the fixed-group SS316L ENG-FD items
               in proportion to their mass (the exact part list is not in the ledger: ASSUMED)
           (d) BL-07 pocketing: -0.02 kg at the BL-07 CG
         Gimballed shares are removed from the derived engine group as point masses (mass, CG and inertia about the pivot
         exact for point masses; the parts' own inertia change is neglected); fixed shares go into the ballast.
Method: as m2_mass_v35 v1.0 (rev3), imported where possible: P00 gimballed engine dry <- 'engine' state 'nograin' (grain from
combustion.json as in v3d); P06 ring <- 'ring' (mid); P07 <- fixed GM-08/09/10/11/13/14/15 + EL-04; every other fixed item
(MV module FS, feed FD, bleed BL incl. the valves, EL-11/12, the standard hardware HW now counted, and the horns and pushrods)
is one cfg point-mass ballast whose station keeps the first moment exact, after removing the v3d P09 and P10 items it
replaces. Derived mechanical.json = the v3d-flown v2 with dry_grain_burnt, the ring and fixed_group_total_CAD_kg replaced
(block gnc_derived_v351; version field kept 'v2' for the run6 strict check; NOT a Mechanical publication).
Checks: every v3.5.1 fixed item assigned once; closure of mass and first moment through R.build (A1_none) per variant; the
6-DOF engine model (derived dry engine + combustion grain) against massprops v3.5.1 engine states wet / mid / burnout /
nograin (mass, CG offset, I_pivot mean of xx / yy): 'use the v3.5.1 inertia for the TVC loop' (coordinator).
Outputs: out/rev4/mass_v351/mass_v351_vs_v3d.json, iface_v351 and iface_v352L (+ README, MANIFEST), pins_rev4/
pins_rev4_v351.sha256 and pins_rev4_v352L.sha256. SI units; vehicle stations in m, engine-frame values in mm as in the source.
DERIVED; no hardware data; not physical approval."""
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from collections import OrderedDict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_mass_v35 as M35  # noqa: E402  (tag_class, group_row; nothing else is run on import)

VERSION = "m2_mass_v351 v1.0"
SP = "/home/claude/work/space"
HUB = "/home/claude/work/shared-fallback/engine"
MECHW = "/home/claude/work/mechanical/engine/03-cad"
OUT = f"{SP}/out/rev4/mass_v351"
IF3D = f"{SP}/iface_v3d"
IFACES = dict(v351=f"{SP}/iface_v351", v352L=f"{SP}/iface_v352L")
PINS_REV2 = f"{SP}/gnc_dev29/data/pins/pins_rev2.sha256"
PINS = dict(v351=f"{SP}/pins_rev4/pins_rev4_v351.sha256", v352L=f"{SP}/pins_rev4/pins_rev4_v352L.sha256")
MP351 = f"{HUB}/03-cad/v3.5.1/massprops_v3.5.1.json"
INPUTS = OrderedDict([
    ("massprops_v3.5.1.json (FROZEN, line 206 (1))", (MP351, "488b47f9d55ff91b")),
    ("BOM_v3.5.csv (part names only)", (f"{MECHW}/BOM_v3.5.csv", "503e412b31fe4794")),
    ("hub mechanical.json v2.1", (f"{HUB}/interfaces/mechanical.json", "e4d3e7c9df529171")),
    ("iface_v3d mechanical.json v2", (f"{IF3D}/mechanical.json", "4f024ed4ccb4618c")),
    ("mass_ledger_v3d.csv", (f"{SP}/out/vehicle_v3d/mass_ledger_v3d.csv", None)),
    ("hub CHANGELOG.md (lines 204-206 read)", (f"{HUB}/interfaces/CHANGELOG.md", None)),
])
P07_PN = ("ENG-GM-08", "ENG-GM-09", "ENG-GM-10", "ENG-GM-11", "ENG-GM-13", "ENG-GM-14", "ENG-GM-15", "ENG-EL-04")
VALVE_PN = "ENG-BL-05"
VALVE_TARGET_EACH = 0.15
LEVERS = OrderedDict([("TC-09 socket OD step + barrel 1.8 mm", -0.11), ("Ti-6Al-4V non-wetted screws", -0.09),
                      ("feed 316L -> 6061-T6 upstream of the MV", -0.086), ("BL-07 pocketing", -0.02)])


def sha(p, n=16):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:n]


def z_of(i, zp):
    return zp + i["cg_mm"][2] * 1e-3


def remove_points(grp, pts):
    """Engine-group mass properties after removing point masses pts = [(dm > 0, r_mm)] (engine frame about the pivot)."""
    m = grp["m_kg"]
    c = np.array(grp["cg_mm"]) * 1e-3
    Ip = np.array(grp["I_pivot_kgm2"], dtype=float)
    fm = m * c
    for dm, r in pts:
        r = np.array(r) * 1e-3
        m -= dm
        fm = fm - dm * r
        Ip = Ip - dm * (np.dot(r, r) * np.eye(3) - np.outer(r, r))
    c2 = fm / m
    Icg = Ip - m * (np.dot(c2, c2) * np.eye(3) - np.outer(c2, c2))
    return dict(m_kg=round(float(m), 6), cg_mm=[round(float(x) * 1e3, 4) for x in c2],
                I_pivot_kgm2=[[round(float(x), 7) for x in row] for row in Ip],
                I_cg_kgm2=[[round(float(x), 7) for x in row] for row in Icg])


def closure(iface, pin, ballast=0.0, ballast_z=0.6):
    code = ("import json,os,sys;sys.path.insert(0,'%s');sys.path.insert(0,'%s');"
            "import numpy as np;from gncsim import run6 as R, sim6 as s6;import m2_rg01_refly as F;"
            "cfg=F.base_cfg('A1_none',extra=dict(ballast=%r,ballast_z=%r))[0];par,apar,comp,mp,tab,info=R.build(cfg);"
            "L=info['ledger'];m=sum(i['m'] for i in L);mz=sum(i['m']*i['z'] for i in L);"
            "g=[i for i in L if i.get('gimballed')];zp=info['z_pivot'];"
            "eng={str(gin):(lambda o:(s6.massprops(mp,0.0,0.0,par[s6.P_rho_l_nom],gin,o),[o[4],(o[5]-zp)*1e3,"
            "o[6]+o[4]*(o[5]-zp)**2])[1])(np.zeros(8)) for gin in %r};"
            "print(json.dumps(dict(m=m,mz=mz,n=len(L),gimb_m=sum(i['m'] for i in g),eng=eng,"
            "items={i['name'][:3]:[i['m'],i['z']] for i in L})))") % (
        f"{SP}/gnc_dev3", f"{SP}/gnc_dev3/scripts", float(ballast), float(ballast_z), GIN)
    env = dict(os.environ, GNC_IFACE=iface, GNC_IFACE_PIN=pin, GNC_STRICT="1")
    r = subprocess.run([sys.executable, "-I", "-c", code], env=env, capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-3000:])
    return json.loads(r.stdout.strip().splitlines()[-1])


GIN = []


def write_iface(name, md):
    d = IFACES[name]
    os.makedirs(d, exist_ok=True)
    for fn in os.listdir(IF3D):
        if fn in ("mechanical.json", "MANIFEST.sha256", "README.txt"):
            continue
        shutil.copy2(os.path.join(IF3D, fn), os.path.join(d, fn))
    with open(os.path.join(d, "mechanical.json"), "w") as f:
        json.dump(md, f, indent=1)
    man = [f"{sha(os.path.join(d, fn), 64)}  {fn}" for fn in sorted(os.listdir(d)) if fn not in ("MANIFEST.sha256", "README.txt")]
    open(os.path.join(d, "MANIFEST.sha256"), "w").write("\n".join(man) + "\n")
    open(os.path.join(d, "README.txt"), "w").write(
        f"{os.path.basename(d)} (GNC rev4, 2026-10-13): derived GNC_IFACE ({VERSION}). Every file = iface_v3d except\n"
        "mechanical.json: GNC-DERIVED from the v3d-flown v2 with the dry gimballed engine, the ring and the P07 fixed set\n"
        "replaced by massprops_v3.5.1.json values" + (" minus the v3.5.2 lever shares on the gimballed engine (DERIVED)"
                                                      if name == "v352L" else "") +
        " (block gnc_derived_v351 inside). Not a Mechanical publication. The other\nfixed items are flown as one cfg ballast "
        "(out/rev4/mass_v351/mass_v351_vs_v3d.json).\n")
    os.makedirs(os.path.dirname(PINS[name]), exist_ok=True)
    hm = sha(os.path.join(d, "mechanical.json"), 64)
    pl = []
    for ln in open(PINS_REV2):
        s = ln.strip()
        if s and not s.startswith("#") and os.path.basename(s.split(None, 1)[1].strip().lstrip("*")) == "mechanical.json":
            pl.append(f"{hm}  mechanical.json")
        else:
            pl.append(ln.rstrip("\n"))
    if not any(x.endswith("  mechanical.json") for x in pl):
        pl.append(f"{hm}  mechanical.json")
    open(PINS[name], "w").write("\n".join(pl) + "\n")
    return hm[:16]


def main():
    os.makedirs(OUT, exist_ok=True)
    ins = OrderedDict()
    for k, (p, h) in INPUTS.items():
        s = sha(p)
        if h and s != h:
            raise RuntimeError(f"{k} {p} sha256/16 {s} != expected {h}")
        ins[k] = dict(path=p, sha256_16=s)
    mp = json.load(open(MP351))
    mh = json.load(open(INPUTS["hub mechanical.json v2.1"][0]))
    m3 = json.load(open(INPUTS["iface_v3d mechanical.json v2"][0]))
    if mp.get("cad_version") != "v3.5.1":
        raise RuntimeError("not the v3.5.1 massprops")
    names = {}
    with open(INPUTS["BOM_v3.5.csv (part names only)"][0]) as f:
        for r in csv.DictReader(f):
            names.setdefault(r["pn"], r["name"])
    led3d = OrderedDict()
    with open(INPUTS["mass_ledger_v3d.csv"][0]) as f:
        for r in csv.DictReader(f):
            led3d[r["item"][:3]] = (float(r["m_kg"]), float(r["z_m"]), r["item"], r["tag"])
    g3, gh = m3["gimballed_mass_properties"], mh["gimballed_mass_properties"]
    ring3 = g3.get("ring_alpha_axis_only") or m3["gimbal"]["ring_alpha_axis_only"]
    ringh = gh.get("ring_alpha_axis_only") or mh["gimbal"]["ring_alpha_axis_only"]
    same = dict(dry_grain_burnt=g3["dry_grain_burnt"] == gh["dry_grain_burnt"], ring=ring3 == ringh,
                fixed_total=m3["fixed_module"]["fixed_group_total_CAD_kg"] == mh["fixed_module"]["fixed_group_total_CAD_kg"])
    if not all(same.values()):
        raise RuntimeError(f"hub v2.1 differs from the v3d-flown v2 in the ledger keys: {same}")
    zp = float(m3["frames"]["rv1_station_of_pivot_m"]["v"])
    L = mp["ledger_mid"]
    fixed = [i for i in L if i["group"] == "fixed"]
    used = set()

    def take(pred):
        out = [i for i in fixed if pred(i) and id(i) not in used]
        for i in out:
            used.add(id(i))
        return out
    p07 = take(lambda i: i["pn"] in P07_PN)
    fs = take(lambda i: i["pn"].startswith("ENG-FS-"))
    fd = take(lambda i: i["pn"].startswith("ENG-FD-"))
    bl = take(lambda i: i["pn"].startswith("ENG-BL-"))
    el = take(lambda i: i["pn"] in ("ENG-EL-11", "ENG-EL-12"))
    hw = take(lambda i: i["pn"].startswith("ENG-HW-"))
    if len(used) != len(fixed):
        raise RuntimeError(f"unassigned v3.5.1 fixed items: {[i['pn'] for i in fixed if id(i) not in used]}")
    horn = [i for i in L if i["group"] == "horn"]
    push = [i for i in L if i["group"] == "pushrod"]
    st = mp["states"]
    eng_ng, ring351 = st["nograin"]["engine"], st["mid"]["ring"]
    # grain inside per state (engine group minus the nograin engine group)
    gin = OrderedDict((s_, round(st[s_]["engine"]["m_kg"] - eng_ng["m_kg"], 6)) for s_ in ("wet", "mid", "burnout", "nograin"))
    GIN.extend(gin.values())
    rows = []
    d3 = g3["dry_grain_burnt"]
    rows.append(OrderedDict(item="P00 gimballed engine dry (no grain)", v351_m_kg=eng_ng["m_kg"],
                            v351_z_m=round(zp + eng_ng["cg_mm"][2] * 1e-3, 5),
                            v351_source="states.nograin.engine (CAD v3.5.1 solids + COTS + standard hardware; grain excluded)",
                            v3d_m_kg=led3d["P00"][0], v3d_z_m=led3d["P00"][1],
                            delta_m_kg=round(eng_ng["m_kg"] - led3d["P00"][0], 5),
                            delta_first_moment_kgm=round(eng_ng["m_kg"] * (zp + eng_ng["cg_mm"][2] * 1e-3)
                                                         - led3d["P00"][0] * led3d["P00"][1], 5), gimballed=True))
    rows.append(OrderedDict(item="P06 gimbal ring group", v351_m_kg=ring351["m_kg"],
                            v351_z_m=round(zp + ring351["cg_mm"][2] * 1e-3, 5), v351_source="states.mid.ring",
                            v3d_m_kg=led3d["P06"][0], v3d_z_m=led3d["P06"][1], delta_m_kg=round(ring351["m_kg"] - led3d["P06"][0], 5),
                            delta_first_moment_kgm=round(ring351["m_kg"] * (zp + ring351["cg_mm"][2] * 1e-3)
                                                         - led3d["P06"][0] * led3d["P06"][1], 5), gimballed=False,
                            note="rotates about the outer (alpha) axis only; non-gimballed in the simulator as in v3d"))
    sums = OrderedDict()
    for nm, its, key in (("P07 fixed TVC module (GM-08/09/10/11/13/14/15 + EL-04)", p07, "P07"), ("P09 <- MV module ENG-FS-*", fs, "P09"),
                         ("P10 <- fixed feed items ENG-FD-*", fd, "P10"), ("NEW bleed fixed side ENG-BL-* (valves 2 x 0.30 ASSUMED)", bl, None),
                         ("NEW EL-11 P_feed transducer + EL-12 thermocouple", el, None),
                         ("NEW standard hardware, fixed group (ENG-HW-*: CALC / DATASHEET / ASSUMED)", hw, None),
                         ("NEW horns (GM-16 group, incl. hardware)", horn, None),
                         ("NEW pushrods (GM-17 group, incl. hardware)", push, None)):
        r, m, mz = M35.group_row(nm, its, zp, (led3d[key][0], led3d[key][1]) if key else None)
        r = OrderedDict((k.replace("v35_", "v351_"), v) for k, v in r.items())
        r["gimballed"] = False
        r["v351_items"] = [dict(pn=i["pn"], idx=i["idx"], name=names.get(i["pn"], "")[:110], m_kg=i["m_kg"],
                                z_m=round(z_of(i, zp), 4), tag=M35.tag_class(i["tag"])) for i in its]
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
    spread = fs + fd + bl + el + hw + horn + push
    i_spread = sum(i["m_kg"] * (z_of(i, zp) - zb) ** 2 for i in spread)
    i_removed = led3d["P09"][0] * (led3d["P09"][1] - zb) ** 2 + led3d["P10"][0] * (led3d["P10"][1] - zb) ** 2
    # (a) valve target
    vit = [i for i in bl if i["pn"] == VALVE_PN]
    vt = sum(i["m_kg"] for i in vit)
    zvt = sum(i["m_kg"] * z_of(i, zp) for i in vit) / vt
    dv = vt - len(vit) * VALVE_TARGET_EACH
    mb_t, zb_t = mb - dv, (mzb - dv * zvt) / (mb - dv)
    # (b) v3.5.2 levers on the v3.5.1 ledger (DERIVED)
    lev_items = []          # (dm_removed > 0, item, lever) at the item CG
    tc09 = [i for i in L if i["pn"] == "ENG-TC-09"]
    if len(tc09) != 1:
        raise RuntimeError("TC-09 not unique in the ledger")
    lev_items.append((0.11, tc09[0], "a"))
    calc = [i for i in L if "HARDWARE CALC" in i["tag"]]
    mc = sum(i["m_kg"] for i in calc)
    lev_items += [(0.09 * i["m_kg"] / mc, i, "b") for i in calc]
    fd316 = [i for i in fd if "SS316L" in i["tag"]]
    m316 = sum(i["m_kg"] for i in fd316)
    lev_items += [(0.086 * i["m_kg"] / m316, i, "c") for i in fd316]
    bl07 = [i for i in bl if i["pn"] == "ENG-BL-07"]
    if len(bl07) != 1:
        raise RuntimeError("BL-07 not unique in the fixed group")
    lev_items.append((0.02, bl07[0], "d"))
    tot_lev = sum(x[0] for x in lev_items)
    g_pts = [(dm, i["cg_mm"]) for dm, i, _ in lev_items if i["group"] == "engine"]
    f_pts = [(dm, z_of(i, zp)) for dm, i, _ in lev_items if i["group"] != "engine"]
    dm_g = sum(x[0] for x in g_pts)
    dm_f = sum(x[0] for x in f_pts)
    mb_l = mb - dm_f
    zb_l = (mzb - sum(dm * z for dm, z in f_pts)) / mb_l
    eng_ng_l = remove_points(eng_ng, g_pts)
    lev_summary = OrderedDict()
    for k, (nm, v) in zip("abcd", LEVERS.items()):
        its = [x for x in lev_items if x[2] == k]
        lev_summary[k] = dict(lever=nm, lead_mass_kg=v, applied_kg=-round(sum(x[0] for x in its), 5),
                              gimballed_kg=-round(sum(x[0] for x in its if x[1]["group"] == "engine"), 5),
                              n_items=len(its), items=sorted({x[1]["pn"] for x in its}))
    dM_l = dM - tot_lev
    dMZ_l = dMZ - sum(dm * (zp + r[2] * 1e-3) for dm, r in g_pts) - sum(dm * z for dm, z in f_pts)
    variants = OrderedDict(
        v351=dict(label="CAD v3.5.1 FROZEN as built: hardware CALC 0.22387 kg, bleed valves 2 x 0.30 kg ASSUMED",
                  iface=IFACES["v351"], pin=PINS["v351"], ballast_kg=round(mb, 5), ballast_z_m=round(zb, 4),
                  landing_mass_delta_kg=round(dM, 4)),
        v351t=dict(label=f"sensitivity (a): v3.5.1 with the bleed valves at the {VALVE_TARGET_EACH} kg target each (DESIGN "
                         "TARGET, no datasheet)", iface=IFACES["v351"], pin=PINS["v351"], ballast_kg=round(mb_t, 5),
                   ballast_z_m=round(zb_t, 4), landing_mass_delta_kg=round(dM - dv, 4)),
        v352L=dict(label="sensitivity (b): v3.5.1 minus the approved v3.5.2 levers (line 206 (2)), DERIVED until Mechanical's "
                         "v3.5.2 massprops", iface=IFACES["v352L"], pin=PINS["v352L"], ballast_kg=round(mb_l, 5),
                   ballast_z_m=round(zb_l, 4), landing_mass_delta_kg=round(dM_l, 4), levers=lev_summary,
                   gimballed_removed_kg=round(dm_g, 5), fixed_removed_kg=round(dm_f, 5)))
    # derived mechanical.json files
    hm = {}
    for vname, eng in (("v351", eng_ng), ("v352L", eng_ng_l)):
        md = json.loads(json.dumps(m3))
        gd = md["gimballed_mass_properties"]
        src_ = (f"massprops_v3.5.1.json ({ins['massprops_v3.5.1.json (FROZEN, line 206 (1))']['sha256_16']}) states.nograin.engine"
                + (" minus the v3.5.2 lever point masses (DERIVED)" if vname == "v352L" else "") + "; GNC-DERIVED copy")
        gd["dry_grain_burnt"] = OrderedDict(
            m_kg=dict(v=eng["m_kg"], tag="CAD v3.5.1 (DERIVED+ASSUMED+ESTIMATE+CALC items)", src=src_),
            cg_m=dict(v=[round(x * 1e-3, 7) for x in eng["cg_mm"]], tag="CAD v3.5.1", src="engine frame, from the pivot"),
            I_pivot_kgm2=dict(v=eng["I_pivot_kgm2"], tag="CAD v3.5.1", src="tensor about the pivot, engine axes"),
            I_cg_kgm2=dict(v=eng["I_cg_kgm2"], tag="CAD v3.5.1", src="tensor about the own CG, engine axes"),
            grain_mass_inside_kg=dict(v=0.0, tag="DERIVED", src="state nograin"), superseded_v2_value=d3)
        rr = OrderedDict(m_kg=dict(v=ring351["m_kg"], tag="CAD v3.5.1", src="massprops_v3.5.1.json states.mid.ring"),
                         I_xx_pivot_kgm2=dict(v=ring351["I_pivot_kgm2"][0][0], tag="CAD v3.5.1",
                                              src="ring group about the outer (X) axis"),
                         I_tensor_pivot_kgm2=dict(v=ring351["I_pivot_kgm2"], tag="CAD v3.5.1"), superseded_v2_value=ring3)
        if "ring_alpha_axis_only" in gd:
            gd["ring_alpha_axis_only"] = rr
        else:
            md["gimbal"]["ring_alpha_axis_only"] = rr
        fg = md["fixed_module"]["fixed_group_total_CAD_kg"]
        md["fixed_module"]["fixed_group_total_CAD_kg"] = dict(v=round(m07, 6), tag="CAD v3.5.1 (P07 subset: GM-08/09/10/11/"
                                                              "13/14/15, EL-04)", src=src_, cg_mm=[round(x, 3) for x in cg07],
                                                              superseded_v2_value=fg)
        md["gnc_derived_v351"] = dict(
            by=VERSION, date="2026-10-13", variant=vname, status="GNC-DERIVED simulator input; NOT a Mechanical publication",
            base_file=f"iface_v3d/mechanical.json v2 ({ins['iface_v3d mechanical.json v2']['sha256_16']})",
            replaced=["gimballed_mass_properties.dry_grain_burnt", "gimbal.ring_alpha_axis_only", "fixed_module.fixed_group_total_CAD_kg"],
            not_replaced="every other key = v2 (stiffness, linkage, frames); version field kept 'v2' for the run6 strict check",
            rest_as_ballast="see out/rev4/mass_v351/mass_v351_vs_v3d.json variants")
        hm[vname] = write_iface(vname, md)
    # closure + engine model check
    c3 = closure(IF3D, PINS_REV2)
    clos = OrderedDict()
    eng_chk = OrderedDict()
    for nm, v in variants.items():
        c = closure(v["iface"], v["pin"], v["ballast_kg"], v["ballast_z_m"])
        dm_ = c["m"] - c3["m"]
        want_mz = dMZ if nm == "v351" else (dMZ - dv * zvt if nm == "v351t" else dMZ_l)
        clos[nm] = dict(ledger_dm_kg=round(dm_, 5), mapped_dm_kg=v["landing_mass_delta_kg"], ok=abs(dm_ - v["landing_mass_delta_kg"]) < 2e-4,
                        ledger_dfirst_moment_kgm=round(c["mz"] - c3["mz"], 5), mapped_dfirst_moment_kgm=round(want_mz, 5),
                        first_moment_ok=abs((c["mz"] - c3["mz"]) - want_mz) < 2e-3,
                        gimballed_dm_kg=round(c["gimb_m"] - c3["gimb_m"], 5))
        if nm in ("v351", "v352L"):
            rows_ = []
            for s_, g_ in gin.items():
                me_, le_, Ip_ = c["eng"][str(g_)]
                ref = st[s_]["engine"]
                ref_I = 0.5 * (ref["I_pivot_kgm2"][0][0] + ref["I_pivot_kgm2"][1][1])
                if nm == "v352L":
                    ref = remove_points(ref, g_pts)
                    ref_I = 0.5 * (ref["I_pivot_kgm2"][0][0] + ref["I_pivot_kgm2"][1][1])
                rows_.append(dict(state=s_, grain_inside_kg=g_, m_sim=round(me_, 5), m_ref=ref["m_kg"], le_sim_mm=round(le_, 3),
                                  le_ref_mm=ref["cg_mm"][2], Ipiv_sim=round(Ip_, 6), Ipiv_ref_mean_xx_yy=round(ref_I, 6),
                                  dI_pct=round(100 * (Ip_ / ref_I - 1), 3),
                                  ok=bool(abs(me_ - ref["m_kg"]) < 1e-3 and abs(le_ - ref["cg_mm"][2]) < 0.5 and abs(Ip_ / ref_I - 1) < 0.01)))
            eng_chk[nm] = rows_
    clos["v3d_ledger_dry_kg"] = round(c3["m"], 4)
    clos["note"] = ("ledger = R.build(A1_none) item sum without propellant and grain (nominal, dry_scale 1); first-moment "
                    "tolerance 2e-3 kg m (the ring's CG offset is not represented, as v3d)")
    res = OrderedDict(
        version=VERSION, date="2026-10-13", inputs=ins, check_hub_v2p1_equals_v3d_flown=same, pivot_station_m=zp,
        frame="vehicle station z [m] = pivot station (mechanical.json frames.rv1_station_of_pivot_m) + engine-frame z",
        hardware=mp["hardware_carried"], mapping=rows,
        totals=OrderedDict(
            landing_mass_delta_kg=dict(v=round(dM, 4), tag="DERIVED (CAD v3.5.1 groups mapped on ledger v3d items)",
                                       note="same propellant and grain; dry vehicle and landing mass grow by the same amount"),
            gimballed_delta_kg=dict(v=round(rows[0]["delta_m_kg"], 4), tag="DERIVED"),
            fixed_delta_kg=dict(v=round(sum(r["delta_m_kg"] for r in rows[1:]), 4), tag="DERIVED"),
            first_moment_delta_kgm=round(dMZ, 5), delta_cg_station_m=round(dMZ / dM, 4),
            check_vs_lead_estimate="lead (line 206): about v35a + 0.20 kg, about +1.37 kg landing mass (DERIVED)"),
        grain_inside_by_state_kg=gin,
        engine_model_check=eng_chk,
        simulator=OrderedDict(
            derived_mechanical_json={k: dict(path=f"{IFACES[k]}/mechanical.json", sha256_16=v) for k, v in hm.items()},
            pin_lists={k: dict(path=p, sha256_16=sha(p)) for k, p in PINS.items()},
            p07_subset=dict(m_kg=round(m07, 6), cg_mm=[round(x, 3) for x in cg07]),
            ballast_inertia_note=dict(spread_items_second_moment_about_ballast_kgm2=round(i_spread, 5),
                                      removed_P09_P10_second_moment_kgm2=round(i_removed, 5), tag="DERIVED",
                                      note=f"the point-mass ballast omits this net transverse inertia ({i_spread - i_removed:+.4f} "
                                           "kg m2) against a vehicle pitch inertia of order 4.4 kg m2"),
            variants=variants, closure=clos),
        open_items=[
            "bleed valves 2 x 0.30 kg ASSUMED (MASS RISK) until a datasheet (line 206 (4)); v351t flies the 0.15 kg target",
            "v352L is DERIVED from the lead's lever masses with ASSUMED spreads (screws: proportional over the CALC hardware; "
            "feed: proportional over the fixed SS316L FD items); Mechanical's v3.5.2 massprops replaces it",
            "not in massprops v3.5.1: the close-coupled Pc transducer (Electronics reselection, line 205) and the tank (OI-32 "
            "MISSING); the v3d ledger items P11 (tank) and P12 (ECU, battery share, sensors) stay as v3d",
            "EL-11 / EL-12 (0.065 kg) may overlap the v3d P12 'tank sensors' allowance: counted here (conservative), as rev3"])
    with open(f"{OUT}/mass_v351_vs_v3d.json", "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(dict(totals=res["totals"], variants=variants, closure=clos, engine_model_check=eng_chk), indent=1))
    for r in rows:
        print(f"{r['item'][:60]:60s} v3d {r['v3d_m_kg']:.4f}  v3.5.1 {r['v351_m_kg']:.5f}  delta {r['delta_m_kg']:+.5f}")
    print("out", f"{OUT}/mass_v351_vs_v3d.json", sha(f"{OUT}/mass_v351_vs_v3d.json"))


if __name__ == "__main__":
    main()
