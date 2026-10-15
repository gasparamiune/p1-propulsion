"""m2_mass_v35 v1.0 (GNC rev3, 2026-10-13): landing-mass delta of CAD v3.5 (massprops_v3.5.json) against the GNC mass ledger
v3d with the gimballed / fixed split (coordinator relay of lead CHANGELOG line 182 (7)), and the derived simulator inputs of the
bracketing case "v3.5 with ASSUMED valves" (v35a), the valve-target variant (v35t) and the gimballed-only attribution (v35g).

Method (DERIVED from the cited files; no new geometry, no new mass data):
 1. Inputs verified by sha256/16: massprops_v3.5.json, BOM_v3.5.csv (part names), massprops_v2.json (CAD v3.3, the basis of
    the v3d-flown mechanical.json v2), hub mechanical.json v2.1, iface_v3d/mechanical.json v2 (the file ledger v3d flew),
    mass_ledger_v3d.csv.
 2. Check: hub v2.1 gimballed_mass_properties (dry_grain_burnt, ring, fixed total) equals the v3d-flown v2 values.
 3. Mapping of the v3.5 groups onto the v3d ledger items (every v3.5 fixed item assigned exactly once, asserted):
      P00 gimballed engine dry <- v3.5 'engine' group, state 'nograin' (the grain is flown from combustion.json, as in v3d)
      P06 gimbal ring          <- v3.5 'ring' group
      P07 fixed TVC module     <- v3.5 fixed GM-08/09/10/11/13/14/15, HW-20 (yoke posts), EL-04 (= the CAD v3.3 fixed set)
      P09 NC isolation valve   <- v3.5 MV module ENG-FS-*
      P10 feed fixed share     <- v3.5 fixed ENG-FD-*
      not in v3d               <- bleed fixed side ENG-BL-* (valves 2 x 0.30 kg ASSUMED), EL-11 P_feed transducer, EL-12
                                  thermocouple, horns (GM-16 group) and pushrods (GM-17 group). v3d omitted horns and
                                  pushrods: fixed_group_total_CAD_kg 0.7875 excludes them (CAD v3.3 massprops_v2 has them
                                  as separate groups), although the v3d P07 item label names them (labelling error, v3d).
 4. Simulator representation (vehicle station z = pivot station 0.203 m + engine-frame z; engine frame +Z forward):
      derived mechanical.json = the v3d-flown v2 file with gimballed_mass_properties.dry_grain_burnt <- v3.5 nograin engine
      group (m, CG, I about the pivot and the CG), gimbal.ring_alpha_axis_only <- v3.5 ring group, and
      fixed_module.fixed_group_total_CAD_kg <- the v3.5 P07 subset (m, CG); every other key unchanged; the version field
      stays 'v2' for the run6 strict schema check and the block 'gnc_derived_v35' states the derivation (NOT a Mechanical
      publication). The remaining fixed delta (P09 / P10 replacements and the new items) is one point mass 'ballast' whose
      station keeps the first moment exact; the own inertia of the spread items about their common CG is not modelled
      (reported below as a number). The ring stays a non-gimballed item at the pivot station, as in v3d (its 7.6 mm CG
      offset and its alpha-axis share of the TVC inertia, 0.5 %, are not modelled: unchanged v3d limitation).
 5. Closure check (subprocess per interface set, R.build of A1_none): ledger mass and first moment of the derived sets minus
    the v3d set equal the mapped delta.
Outputs: out/rev3/mass_v35/mass_v35_vs_v3d.json, /home/claude/work/space/iface_v35a/ (derived interface set + README +
MANIFEST), /home/claude/work/space/pins_rev3/pins_rev3_v35a.sha256 (rev2 pin list with the derived mechanical.json).
SI units; masses kg, stations m (vehicle), engine-frame values mm as in the source."""
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from collections import OrderedDict, defaultdict

VERSION = "m2_mass_v35 v1.0"
SP = "/home/claude/work/space"
MECHW = "/home/claude/work/mechanical/engine/03-cad"
HUB = "/home/claude/work/shared-fallback/engine"
OUT = f"{SP}/out/rev3/mass_v35"
IF3D = f"{SP}/iface_v3d"
IF35 = f"{SP}/iface_v35a"
PINS_REV2 = f"{SP}/gnc_dev29/data/pins/pins_rev2.sha256"
PINS_V35 = f"{SP}/pins_rev3/pins_rev3_v35a.sha256"
INPUTS = OrderedDict([
    ("massprops_v3.5.json", (f"{MECHW}/massprops_v3.5.json", "8c11e1e136fc59d8")),
    ("BOM_v3.5.csv", (f"{MECHW}/BOM_v3.5.csv", "503e412b31fe4794")),
    ("massprops_v2.json (CAD v3.3)", (f"{MECHW}/src/calcs/massprops_v2.json", "e730fca4c5ddda18")),
    ("hub mechanical.json v2.1", (f"{HUB}/interfaces/mechanical.json", "e4d3e7c9df529171")),
    ("iface_v3d mechanical.json v2", (f"{IF3D}/mechanical.json", "4f024ed4ccb4618c")),
    ("mass_ledger_v3d.csv", (f"{SP}/out/vehicle_v3d/mass_ledger_v3d.csv", None)),
])
P07_PN = ("ENG-GM-08", "ENG-GM-09", "ENG-GM-10", "ENG-GM-11", "ENG-GM-13", "ENG-GM-14", "ENG-GM-15", "ENG-HW-20", "ENG-EL-04")
VALVE_PN = "ENG-BL-05"
VALVE_TARGET_EACH = 0.15     # lead line 182 (3) target <= 0.15 kg each (DESIGN TARGET, no datasheet yet)


def sha(p, n=16):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:n]


def tag_class(t):
    t = str(t)
    if t.startswith("CAD volume"):
        return "CAD"
    for k in ("DATASHEET", "ASSUMED", "ESTIMATE", "DERIVED", "INTERFACE"):
        if f"({k}" in t or t.startswith(k):
            return k
    return "OTHER"


def wsum(items, zp):
    m = sum(i["m_kg"] for i in items)
    mz = sum(i["m_kg"] * (zp + i["cg_mm"][2] * 1e-3) for i in items)
    return m, mz


def group_row(name, items, zp, v3d=None):
    m, mz = wsum(items, zp)
    by = defaultdict(float)
    for i in items:
        by[tag_class(i["tag"])] += i["m_kg"]
    r = OrderedDict(item=name, v35_m_kg=round(m, 5), v35_z_m=round(mz / m, 4) if m > 0 else None,
                    v35_pn=sorted({i["pn"] for i in items}), v35_mass_by_tag_kg={k: round(v, 5) for k, v in sorted(by.items())})
    if v3d is not None:
        r.update(v3d_m_kg=v3d[0], v3d_z_m=v3d[1], delta_m_kg=round(m - v3d[0], 5),
                 delta_first_moment_kgm=round(mz - v3d[0] * v3d[1], 5))
    else:
        r.update(v3d_m_kg=0.0, v3d_z_m=None, delta_m_kg=round(m, 5), delta_first_moment_kgm=round(mz, 5))
    return r, m, mz


def closure(iface, ballast=0.0, ballast_z=0.6):
    code = ("import json,os,sys;sys.path.insert(0,'%s');sys.path.insert(0,'%s');"
            "from gncsim import run6 as R;import m2_rg01_refly as F;"
            "cfg=F.base_cfg('A1_none',extra=dict(ballast=%r,ballast_z=%r))[0];info=R.build(cfg)[5];L=info['ledger'];"
            "m=sum(i['m'] for i in L);mz=sum(i['m']*i['z'] for i in L);"
            "g=[i for i in L if i.get('gimballed')];"
            "print(json.dumps(dict(m=m,mz=mz,n=len(L),gimb_m=sum(i['m'] for i in g),"
            "items={i['name'][:3]:[i['m'],i['z']] for i in L})))") % (
        f"{SP}/gnc_dev3", f"{SP}/gnc_dev3/scripts", float(ballast), float(ballast_z))
    env = dict(os.environ, GNC_IFACE=iface, GNC_IFACE_PIN=PINS_V35 if iface == IF35 else PINS_REV2, GNC_STRICT="1")
    r = subprocess.run([sys.executable, "-I", "-c", code], env=env, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-3000:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def main():
    os.makedirs(OUT, exist_ok=True)
    ins = OrderedDict()
    for k, (p, h) in INPUTS.items():
        s = sha(p)
        if h and s != h:
            raise RuntimeError(f"{k} {p} sha256/16 {s} != expected {h}")
        ins[k] = dict(path=p, sha256_16=s)
    mp = json.load(open(INPUTS["massprops_v3.5.json"][0]))
    m33 = json.load(open(INPUTS["massprops_v2.json (CAD v3.3)"][0]))
    mh = json.load(open(INPUTS["hub mechanical.json v2.1"][0]))
    m3 = json.load(open(INPUTS["iface_v3d mechanical.json v2"][0]))
    names = {}
    with open(INPUTS["BOM_v3.5.csv"][0]) as f:
        for r in csv.DictReader(f):
            names.setdefault(r["pn"], r["name"])
    led3d = OrderedDict()
    with open(INPUTS["mass_ledger_v3d.csv"][0]) as f:
        for r in csv.DictReader(f):
            led3d[r["item"][:3]] = (float(r["m_kg"]), float(r["z_m"]), r["item"], r["tag"])
    # 2. v2.1 = v3d-flown v2 for the keys the ledger reads
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
    if len(used) != len(fixed):
        raise RuntimeError(f"unassigned v3.5 fixed items: {[i['pn'] for i in fixed if id(i) not in used]}")
    horn = [i for i in L if i["group"] == "horn"]
    push = [i for i in L if i["group"] == "pushrod"]
    st = mp["states"]
    eng_ng, ring35 = st["nograin"]["engine"], st["mid"]["ring"]
    # 3. rows
    rows = []
    d3 = g3["dry_grain_burnt"]
    rows.append(OrderedDict(item="P00 gimballed engine dry (no grain)", v35_m_kg=eng_ng["m_kg"],
                            v35_z_m=round(zp + eng_ng["cg_mm"][2] * 1e-3, 5), v35_source="states.nograin.engine (CAD v3.5 "
                            "solids + COTS items; grain excluded)", v3d_m_kg=led3d["P00"][0], v3d_z_m=led3d["P00"][1],
                            delta_m_kg=round(eng_ng["m_kg"] - led3d["P00"][0], 5),
                            delta_first_moment_kgm=round(eng_ng["m_kg"] * (zp + eng_ng["cg_mm"][2] * 1e-3)
                                                         - led3d["P00"][0] * led3d["P00"][1], 5), gimballed=True))
    rows.append(OrderedDict(item="P06 gimbal ring group", v35_m_kg=ring35["m_kg"], v35_z_m=round(zp + ring35["cg_mm"][2] * 1e-3, 5),
                            v35_source="states.mid.ring", v3d_m_kg=led3d["P06"][0], v3d_z_m=led3d["P06"][1],
                            delta_m_kg=round(ring35["m_kg"] - led3d["P06"][0], 5),
                            delta_first_moment_kgm=round(ring35["m_kg"] * (zp + ring35["cg_mm"][2] * 1e-3)
                                                         - led3d["P06"][0] * led3d["P06"][1], 5), gimballed=False,
                            note="rotates about the outer (alpha) axis only; non-gimballed in the simulator as in v3d"))
    sums = {}
    for nm, its, key in (("P07 fixed TVC module (CAD v3.3 fixed set)", p07, "P07"), ("P09 <- MV module ENG-FS-*", fs, "P09"),
                         ("P10 <- fixed feed items ENG-FD-*", fd, "P10"), ("NEW bleed fixed side ENG-BL-*", bl, None),
                         ("NEW EL-11 P_feed transducer + EL-12 thermocouple", el, None),
                         ("NEW horns (GM-16 group; omitted in v3d)", horn, None),
                         ("NEW pushrods (GM-17 group; omitted in v3d)", push, None)):
        r, m, mz = group_row(nm, its, zp, (led3d[key][0], led3d[key][1]) if key else None)
        r["gimballed"] = False
        r["v35_items"] = [dict(pn=i["pn"], idx=i["idx"], name=names.get(i["pn"], "")[:110], m_kg=i["m_kg"],
                               z_m=round(zp + i["cg_mm"][2] * 1e-3, 4), tag=tag_class(i["tag"])) for i in its]
        rows.append(r)
        sums[key or nm] = (m, mz)
    d_g = rows[0]["delta_m_kg"]
    d_f = sum(r["delta_m_kg"] for r in rows[1:])
    # mapped delta, first moment
    dM = sum(r["delta_m_kg"] for r in rows)
    dMZ = sum(r["delta_first_moment_kgm"] for r in rows)
    # 4. simulator representation: derived mechanical.json (P00, P06, P07 from v3.5), ballast = the rest (P09/P10 replacement + new)
    m07, mz07 = sums["P07"]
    cg07 = [sum(i["m_kg"] * i["cg_mm"][k] for i in p07) / m07 for k in range(3)]
    rest_new = [sums["P09"], sums["P10"]] + [sums[k] for k in sums if k not in ("P07", "P09", "P10")]
    mb = sum(m for m, _ in rest_new) - led3d["P09"][0] - led3d["P10"][0]
    mzb = sum(mz for _, mz in rest_new) - led3d["P09"][0] * led3d["P09"][1] - led3d["P10"][0] * led3d["P10"][1]
    zb = mzb / mb
    # second moment check: point-mass ballast vs the spread items (about the ballast station)
    spread = fs + fd + bl + el + horn + push
    i_spread = sum(i["m_kg"] * (zp + i["cg_mm"][2] * 1e-3 - zb) ** 2 for i in spread)
    i_removed = led3d["P09"][0] * (led3d["P09"][1] - zb) ** 2 + led3d["P10"][0] * (led3d["P10"][1] - zb) ** 2
    vt = sum(i["m_kg"] for i in bl if i["pn"] == VALVE_PN)
    nvt = sum(1 for i in bl if i["pn"] == VALVE_PN)
    zvt = sum(i["m_kg"] * (zp + i["cg_mm"][2] * 1e-3) for i in bl if i["pn"] == VALVE_PN) / vt
    dv = vt - nvt * VALVE_TARGET_EACH
    mb_t = mb - dv
    zb_t = (mzb - dv * zvt) / mb_t
    variants = OrderedDict(
        v35a=dict(label="CAD v3.5 with ASSUMED bleed valves 2 x 0.30 kg (bracketing case, coordinator)", iface=IF35,
                  ballast_kg=round(mb, 5), ballast_z_m=round(zb, 4), landing_mass_delta_kg=round(dM, 4)),
        v35t=dict(label=f"CAD v3.5 with the bleed valves at the lead target {VALVE_TARGET_EACH} kg each (line 182 (3); DESIGN "
                        "TARGET, no datasheet)", iface=IF35, ballast_kg=round(mb_t, 5), ballast_z_m=round(zb_t, 4),
                  landing_mass_delta_kg=round(dM - dv, 4)),
        v35g=dict(label="attribution: gimballed engine, ring and P07 from CAD v3.5, fixed P09/P10/new items as v3d (no "
                        "ballast)", iface=IF35, ballast_kg=0.0, ballast_z_m=None,
                  landing_mass_delta_kg=round(rows[0]["delta_m_kg"] + rows[1]["delta_m_kg"] + rows[2]["delta_m_kg"], 4)))
    # derived mechanical.json
    md = json.loads(json.dumps(m3))
    gd = md["gimballed_mass_properties"]
    src_ = f"massprops_v3.5.json ({ins['massprops_v3.5.json']['sha256_16']}) states.nograin.engine; GNC-DERIVED copy"
    gd["dry_grain_burnt"] = OrderedDict(
        m_kg=dict(v=eng_ng["m_kg"], tag="CAD v3.5 (DERIVED+ASSUMED+ESTIMATE items)", src=src_),
        cg_m=dict(v=[round(x * 1e-3, 6) for x in eng_ng["cg_mm"]], tag="CAD v3.5", src="engine frame, from the pivot"),
        I_pivot_kgm2=dict(v=eng_ng["I_pivot_kgm2"], tag="CAD v3.5", src="tensor about the pivot, engine axes"),
        I_cg_kgm2=dict(v=eng_ng["I_cg_kgm2"], tag="CAD v3.5", src="tensor about the own CG, engine axes"),
        grain_mass_inside_kg=dict(v=0.0, tag="DERIVED", src="state nograin"),
        superseded_v2_value=d3)
    rr = OrderedDict(m_kg=dict(v=ring35["m_kg"], tag="CAD v3.5", src="massprops_v3.5.json states.mid.ring"),
                     I_xx_pivot_kgm2=dict(v=ring35["I_pivot_kgm2"][0][0], tag="CAD v3.5", src="ring group about the outer (X) axis"),
                     I_tensor_pivot_kgm2=dict(v=ring35["I_pivot_kgm2"], tag="CAD v3.5"), superseded_v2_value=ring3)
    if "ring_alpha_axis_only" in gd:
        gd["ring_alpha_axis_only"] = rr
    else:
        md["gimbal"]["ring_alpha_axis_only"] = rr
    fg = md["fixed_module"]["fixed_group_total_CAD_kg"]
    md["fixed_module"]["fixed_group_total_CAD_kg"] = dict(v=round(m07, 6), tag="CAD v3.5 (P07 subset: GM-08/09/10/11/13/14/15, "
                                                          "HW-20 posts, EL-04)", src=src_, cg_mm=[round(x, 3) for x in cg07],
                                                          superseded_v2_value=fg)
    md["gnc_derived_v35"] = dict(
        by=VERSION, date="2026-10-13", status="GNC-DERIVED simulator input; NOT a Mechanical publication",
        base_file=f"iface_v3d/mechanical.json v2 ({ins['iface_v3d mechanical.json v2']['sha256_16']}) = hub v2.1 "
                  f"({ins['hub mechanical.json v2.1']['sha256_16']}) in the ledger keys",
        replaced=["gimballed_mass_properties.dry_grain_burnt", "gimbal.ring_alpha_axis_only (or gimballed_mass_properties.)",
                  "fixed_module.fixed_group_total_CAD_kg"],
        not_replaced="every other key (linkage, stiffness, envelope, frames, other mass states) = v2; the version field is "
                     "kept 'v2' for the run6 strict schema check",
        rest_as_ballast=f"P09/P10 replacements + bleed fixed side + EL-11/12 + horns + pushrods = cfg ballast "
                        f"{mb:.5f} kg at z {zb:.4f} m (v35a); first moment exact")
    os.makedirs(IF35, exist_ok=True)
    for fn in os.listdir(IF3D):
        if fn in ("mechanical.json", "MANIFEST.sha256", "README.txt"):
            continue
        shutil.copy2(os.path.join(IF3D, fn), os.path.join(IF35, fn))
    with open(os.path.join(IF35, "mechanical.json"), "w") as f:
        json.dump(md, f, indent=1)
    man = []
    for fn in sorted(os.listdir(IF35)):
        if fn in ("MANIFEST.sha256", "README.txt"):
            continue
        man.append(f"{sha(os.path.join(IF35, fn), 64)}  {fn}")
    open(os.path.join(IF35, "MANIFEST.sha256"), "w").write("\n".join(man) + "\n")
    open(os.path.join(IF35, "README.txt"), "w").write(
        "iface_v35a (GNC rev3, 2026-10-13): derived GNC_IFACE for the CAD v3.5 mass brackets (m2_mass_v35 v1.0).\n"
        "Every file = iface_v3d except mechanical.json: GNC-DERIVED from the v3d-flown v2 with the dry gimballed engine, the\n"
        "ring and the P07 fixed set replaced by massprops_v3.5.json values (block gnc_derived_v35 inside). Not a Mechanical\n"
        "publication. The other fixed v3.5 items are flown as one cfg ballast (see out/rev3/mass_v35/mass_v35_vs_v3d.json).\n")
    os.makedirs(os.path.dirname(PINS_V35), exist_ok=True)
    pl = []
    hm = sha(os.path.join(IF35, "mechanical.json"), 64)
    for ln in open(PINS_REV2):
        s = ln.strip()
        if s and not s.startswith("#") and os.path.basename(s.split(None, 1)[1].strip().lstrip("*")) == "mechanical.json":
            pl.append(f"{hm}  mechanical.json")
        else:
            pl.append(ln.rstrip("\n"))
    if not any(x.endswith("  mechanical.json") for x in pl):
        pl.append(f"{hm}  mechanical.json")
    open(PINS_V35, "w").write("\n".join(pl) + "\n")
    # 5. closure
    c3 = closure(IF3D)
    ca = closure(IF35, mb, zb)
    ct = closure(IF35, mb_t, zb_t)
    cg_ = closure(IF35)
    clos = OrderedDict()
    for nm, c, want in (("v35a", ca, variants["v35a"]["landing_mass_delta_kg"]), ("v35t", ct, variants["v35t"]["landing_mass_delta_kg"]),
                        ("v35g", cg_, variants["v35g"]["landing_mass_delta_kg"])):
        dm_ = c["m"] - c3["m"]
        clos[nm] = dict(ledger_dm_kg=round(dm_, 5), mapped_dm_kg=want, ok=abs(dm_ - want) < 2e-4,
                        ledger_dfirst_moment_kgm=round(c["mz"] - c3["mz"], 5), gimballed_dm_kg=round(c["gimb_m"] - c3["gimb_m"], 5))
    clos["v35a"]["mapped_dfirst_moment_kgm"] = round(dMZ, 5)
    clos["v35a"]["first_moment_ok"] = abs(clos["v35a"]["ledger_dfirst_moment_kgm"] - dMZ) < 2e-3
    clos["v3d_ledger_dry_kg"] = round(c3["m"], 4)
    clos["note"] = ("ledger = R.build(A1_none) item sum without propellant and grain (nominal, dry_scale 1); the ring's 7.6 mm "
                    "CG offset is not represented (P06 at the pivot station, as v3d): first-moment tolerance 2e-3 kg m")
    gw3, gm3 = g3["wet_full_grain"], g3["mid_burn"]
    inert = OrderedDict()
    for nm, a, b in (("dry", d3["I_pivot_kgm2"]["v"], eng_ng["I_pivot_kgm2"]),
                     ("wet_full_grain", gw3["I_pivot_kgm2"]["v"], st["wet"]["engine"]["I_pivot_kgm2"]),
                     ("mid_burn", gm3["I_pivot_kgm2"]["v"], st["mid"]["engine"]["I_pivot_kgm2"])):
        inert[nm] = dict(v3d_Ixx_Iyy=[a[0][0], a[1][1]], v35_Ixx_Iyy=[b[0][0], b[1][1]],
                         change_pct=[round(100 * (b[0][0] / a[0][0] - 1), 2), round(100 * (b[1][1] / a[1][1] - 1), 2)])
    by_all = defaultdict(float)
    for r in rows[2:]:
        if r["item"].startswith("NEW"):
            for k, v in r["v35_mass_by_tag_kg"].items():
                by_all[k] += v
    res = OrderedDict(
        version=VERSION, date="2026-10-13", inputs=ins, check_hub_v2p1_equals_v3d_flown=same, pivot_station_m=zp,
        frame="vehicle station z [m] = pivot station 0.203 (mechanical.json frames.rv1_station_of_pivot_m) + engine-frame z",
        mapping=rows,
        totals=OrderedDict(
            landing_mass_delta_kg=dict(v=round(dM, 4), tag="DERIVED (CAD v3.5 groups mapped on ledger v3d items)",
                                       note="same propellant and grain; dry vehicle and landing mass grow by the same amount"),
            gimballed_delta_kg=dict(v=round(d_g, 4), tag="DERIVED", note="engine group nograin 2.39322 vs v3d P00 2.1565; "
                                    "+0.0565 v3.4.1 -> v3.5 (bleed lines engine side, GM-01/02 7075, TC-09 IN718) and the "
                                    "rest v3.3+ESTIMATE (mechanical.json v2) -> v3.4.1 CAD"),
            fixed_delta_kg=dict(v=round(d_f, 4), tag="DERIVED", note="ring + P07 + P09/P10 replacements + new items"),
            new_items_mass_by_tag_kg={k: round(v, 5) for k, v in sorted(by_all.items())},
            first_moment_delta_kgm=round(dMZ, 5),
            delta_cg_station_m=round(dMZ / dM, 4)),
        tvc_inertia_about_pivot_kgm2=inert,
        gimballed_cg_mm=dict(v3d_dry=[x * 1e3 for x in d3["cg_m"]["v"]], v35_nograin=eng_ng["cg_mm"],
                             v35_mid=st["mid"]["engine"]["cg_mm"],
                             note="v3.5 lateral CG offset x -2.8 mm (nograin) / -2.5 mm (mid) from the pivot (v3d +0.4 mm): "
                                  "static gimbal moment under axial load; not a thrust-line offset; not modelled in sim6"),
        simulator=OrderedDict(
            derived_mechanical_json=dict(path=f"{IF35}/mechanical.json", sha256_16=hm[:16]),
            pin_list=dict(path=PINS_V35, sha256_16=sha(PINS_V35)),
            p07_subset=dict(m_kg=round(m07, 6), cg_mm=[round(x, 3) for x in cg07], v3d=fg),
            ballast_inertia_note=dict(spread_items_second_moment_about_ballast_kgm2=round(i_spread, 5),
                                      removed_P09_P10_second_moment_kgm2=round(i_removed, 5),
                                      tag="DERIVED", note="the point-mass ballast omits this net transverse inertia "
                                                          f"({i_spread - i_removed:+.4f} kg m2) against a vehicle pitch "
                                                          "inertia of order 2-3 kg m2"),
            variants=variants, closure=clos),
        open_items=[
            "massprops_v3.5.1 (lead line 182 (8)) pending: TC-02 head fix (line 182 (1), 183 (1)), 608 bearing replacement "
            "(182 (2)), NZ-04 seal (182 (4)), bay-wall trims (182 (5)), GM-01/02 geometry change (183 (3)) may change mass "
            "-> re-fly v35a at v3.5.1 (coordinator)",
            "bleed valves 2 x 0.30 kg ASSUMED (MASS RISK) until a maker datasheet (line 182 (3)); v35t flies the 0.15 kg target",
            "EL-11 P_feed transducer and EL-12 thermocouple (0.065 kg) may overlap the v3d P12 'tank sensors' allowance "
            "(ASSUMED 0.25 kg): counted here (conservative); TO-VERIFY Electronics / Mechanical",
            "fasteners not modelled in CAD v3.5 (v3d P07 upper +15 % ASSUMED); torch propane line fixed share not in v3.5 "
            "(TO-VERIFY Mechanical)",
            "v3d omitted horns and pushrods (0.0366 kg) and labelled P07 as including them: ledger v3d error, corrected here"])
    with open(f"{OUT}/mass_v35_vs_v3d.json", "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(dict(totals=res["totals"], variants=variants, closure=clos, inertia=inert), indent=1))
    for r in rows:
        print(f"{r['item'][:52]:52s} v3d {r['v3d_m_kg']:.4f}  v3.5 {r['v35_m_kg']:.5f}  delta {r['delta_m_kg']:+.5f}")
    print("out", f"{OUT}/mass_v35_vs_v3d.json", sha(f"{OUT}/mass_v35_vs_v3d.json"))


if __name__ == "__main__":
    main()
