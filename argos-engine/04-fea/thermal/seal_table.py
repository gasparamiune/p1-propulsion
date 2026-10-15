"""Engine seal temperature table: every seal / polymer sealing item, B1 and A1, in-burn and post-burn (04-fea/thermal, v1, 2026-10-13).

Lead relay 2026-10-13 (3rd): "a table of every seal in the engine: location, material, max temperature (B1/A1, in-burn and soak),
rating and margin.  Every seal above 175 C becomes FFKM or metal."

Method: 2-D axisymmetric transient runs (run_thermal.py v1.1, hi flux bound, TC-06 3.6 mm, TC-03 IN718 unless the run says otherwise).
Per seal a zone (part, r0..r1, z0..z1 in the thermal-mesh frame = CAD v3.3 pivot frame - 0.57 mm: injector face zf 112.02, head top
zt 178.02, cap bottom 150.02, bonnet top zb 210.02) covering the gland/groove or the sealing face; T = MAX over the zone nodes per frd
frame (conservative vs the seal cross-section mean).  In-burn = frames inside a burn segment; post-burn = every other frame after the
first ignition (coasts + the 1 h soak).  Off-axis features (E1-M face seals, Pc and T4 ports, torch seat) are not in the 2-D section
(cut at az 214 deg): their zone is the same (r, z) region of the axisymmetric head/bonnet (ESTIMATE: the local block/port is not
modelled).  Items outside the FE model (riser-foot TEE, O3b hose, FS-01 module) are bounded by the nearest modelled temperature, tagged.
Ratings are class values (LITERATURE-approx unless the compound data sheet is cited); the compound data sheet confirms each.
usage: seal_table.py <label> [<label> ...]  ->  seal_table_v1.json (merged per label)
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ax_thermal as at

RUNS = Path("/home/claude/work/mechanical/runs/thermal")
OUT = HERE / "seal_table_v1.json"
ZF, ZT, ZCB, ZB = 112.02, 178.02, 150.02, 210.02
Z_F = ZCB + 14.0                      # E1-M filter-bore axis
Z_X = ZT + 22.0                       # E1-M bonnet cross-drilling axis (bore top - 4)
LIMIT_RULE_C = 175.0                  # lead 2026-10-13: every seal above 175 C becomes FFKM or metal

RATING = {   # continuous / short-term service limit, C
    "FKM": (204.0, 250.0, "LITERATURE-approx: Parker ORD 5700 FKM -26..+204 C continuous; short excursions ~250 C (compound data sheet to confirm)"),
    "FFKM": (327.0, 327.0, "LITERATURE: DuPont Kalrez 7075 data sheet max continuous 327 C (TO-QUOTE, compound to confirm)"),
    "PTFE": (260.0, 260.0, "LITERATURE-approx: PTFE (tape, spring-energised seal jacket) 260 C continuous"),
    "PTFE-glass": (260.0, 260.0, "LITERATURE-approx: PTFE + 25 % glass 260 C"),
    "PCTFE": (150.0, 150.0, "LITERATURE-approx: engmat v1.1 PCTFE service to ~150 C (creep at seat stress above ~100 C TO-VERIFY)"),
    "Cu": (400.0, 400.0, "ASSUMED: annealed copper crush washer, sealing/oxidation limit ~400 C (maker to confirm)"),
    "MICA": (900.0, 900.0, "LITERATURE-approx: phlogopite mica / Thermiculite 866 class gasket 900+ C (Flexitallic / Klinger data sheet)"),
    "PTFE-hose": (204.0, 232.0, "LITERATURE-approx: SAE 100R14 / PTFE smooth-bore braided hose -54..+204 C (some makers 232 C); data sheet to confirm"),
    "METAL": (None, None, "metal-to-metal (37 deg flare / weld): no polymer"),
    # v1.1 (2026-10-13): nozzle joint J1 (CAD v3.4.1)
    "FLEX-GRAPHITE-OI": (500.0, 650.0, "ASSUMED class: oxidation-inhibited flexible graphite in oxidising service ~450-650 C as recalled (engmat v1.2 "
                                       "T_max 500 ASSUMED); supplier class rating required; J1 rule (lead 2026-10-13): in-burn seal face <= class rating - 100 K"),
    "CARBON-PHENOLIC-HOT": (None, None, "J1 hot layer (bearing thermal break, NO sealing function): requirement T_service >= FE peak + 100 K "
                                        "(Combustion nozzle_joint_v2p4); char strength / shrinkage at temperature TO-VERIFY"),
}

# (id, item, location, material, rating key, zones [(pn, r0, r1, z0, z1)], basis tag)
SEALS = [
    ("S01", "TC-02 head plug gland, lower: AS568-226 FKM 90A", "head plug OD r 25.8-28.6, z 115.0-119.9 (chamber seal)", "FKM 90A", "FKM",
     [("ENG-TC-02", 25.7, 28.7, 115.0, 119.9)], "FE zone"),
    ("S02", "TC-02 head plug gland, upper: AS568-226 FKM 90A", "head plug OD r 25.8-28.6, z 122.9-127.7 (chamber seal, back-up)", "FKM 90A", "FKM",
     [("ENG-TC-02", 25.7, 28.7, 122.9, 127.7)], "FE zone"),
    ("S03", "TC-03 insert flange: AS568-016 (FFKM since 2026-10-13)", "TC-02 counterbore floor r 7.8-9.8, z zf+1.95..zf+3.35 (manifold -> chamber bypass)",
     "FFKM (was FKM)", "FFKM", [("ENG-TC-02", 7.8, 9.8, ZF + 1.95, ZF + 3.35)], "FE zone"),
    ("S04", "TC-04 bonnet face: AS568-013 FKM 75", "bonnet bottom groove r 6.0-7.2 on the head top z zt..zt+1.3 (manifold bore seal)", "FKM 75", "FKM",
     [("ENG-TC-04", 5.9, 7.3, ZT - 0.05, ZT + 1.35), ("ENG-TC-02", 5.9, 7.3, ZT - 0.6, ZT + 0.05)], "FE zone"),
    ("S05", "TC-04 E1-M transfer face seal: AS568-012 FKM 75", "bonnet bottom face around the axial 8 mm at r 16 / az 180 (ring r 9.5-22.5 in the 2-D section)",
     "FKM 75", "FKM", [("ENG-TC-04", 9.5, 20.1, ZT - 0.05, ZT + 1.35), ("ENG-TC-02", 9.5, 22.5, ZT - 0.6, ZT + 0.05)], "FE zone at the same (r, z); feature off the 2-D section (ESTIMATE)"),
    ("S06", "TC-04 stem seal: PTFE spring-energised rod seal (Variseal M2 class) on the 3 mm stem", "bonnet gland zb-9.0..zb-5.4, r 1.5-3.7", "PTFE + SS spring", "PTFE",
     [("ENG-TC-04", 0.0, 4.6, ZB - 9.5, ZB - 5.0)], "FE zone (v3.3 bonnet section; v3.4 gland at the same zb offset)"),
    ("S07", "TC-11 stem guide bushing (PTFE + 25 % glass)", "bonnet top zb-4..zb, r 1.5-2.5", "PTFE-glass", "PTFE-glass",
     [("ENG-TC-04", 0.0, 4.6, ZB - 4.5, ZB + 0.05)], "FE zone"),
    ("S08", "FD-01 face seal to the cartridge cap: AS568-010 FKM 75", "flat r 30.5, az 180, z_f +/- 5 (block face)", "FKM 75", "FKM",
     [("ENG-TC-02", 29.0, 31.8, Z_F - 5.0, Z_F + 5.0)], "head OD region at the same z (bound: FD-01 is bolted on, not modelled)"),
    ("S09", "FD-02 cartridge cap radial O-ring: AS568-013 FKM 75", "14 mm filter bore at the cap, r 27.5-30.5, z_f +/- 7", "FKM 75", "FKM",
     [("ENG-TC-02", 27.0, 31.0, Z_F - 7.0, Z_F + 7.0)], "FE zone at the same (r, z) (ESTIMATE, off-section)"),
    ("S10", "Pc tap 1/8-27 NPT male fitting: PTFE tape (oxygen grade)", "TC-02 top r 25 / az 142, z zt-10..zt", "PTFE tape", "PTFE",
     [("ENG-TC-02", 20.6, 29.4, ZT - 10.0, ZT + 0.05)], "FE zone at the same (r, z) (ESTIMATE, off-section)"),
    ("S11", "IG-01 torch seat M10x1: copper crush washer", "TC-02 top face r 25 / az 0, z zt", "Cu (annealed)", "Cu",
     [("ENG-TC-02", 20.0, 30.0, ZT - 1.0, ZT + 0.05)], "FE zone at the same (r, z) (ESTIMATE, off-section)"),
    ("S12", "T4 port flush plug 1/8-27 NPT: PTFE tape", "TC-04 E1-M boss, cross-drilling end r 17.9-28.2, z_x", "PTFE tape", "PTFE",
     [("ENG-TC-04", 11.0, 12.1, Z_X - 5.0, Z_X + 5.0), ("ENG-TC-02", 15.0, 28.5, ZT - 1.0, ZT + 0.05)],
     "BOUND: max of the v3.3 bonnet OD (r 12) at z_x and the head top under the boss (r 15-28.5); boss not in the 2-D model (ESTIMATE)"),
    ("S13", "TC-09 aft section rod gland: AS568-229 FKM 75 on the case land", "case land r 30.5, z ~ -146..-141 (aft closure seal)", "FKM 75", "FKM",
     [("ENG-TC-01", 29.5, 31.8, -146.5, -140.5), ("ENG-TC-09", 30.4, 34.0, -146.5, -140.5)], "FE zone"),
    ("S14", "NZ-03 insert shoulder gasket (mica / vermiculite 1 mm)", "aft-section lip, r ~ 14-23, z ~ -223", "mica/vermiculite", "MICA",
     [("ENG-NZ-03", 0.0, 40.0, -240.0, -200.0)], "FE part"),
    ("S15", "MSS-1 TC fitting in the riser-foot TEE: 1/8 NPT (SS-100-1-2BT) with PTFE tape", "FD-05 TEE r ~42, az 180, z ~56-80 (CAD v3.4)", "PTFE tape", "PTFE",
     [("ENG-TC-01", 31.0, 31.8, 50.0, 85.0)], "BOUND: case OD max over the TEE height band (TEE is 10 mm off the case, radiation + air)"),
    ("S16", "O3b feed hose: PTFE smooth-bore liner, -6 SS braid", "coil around the case r 42-54, z 45-64 (CAD v3.4)", "PTFE (hose)", "PTFE-hose",
     [("ENG-TC-01", 31.0, 31.8, 35.0, 70.0)], "BOUND: case OD max over the coil height band (hose 10-22 mm off the case)"),
]

# v1.1 (2026-10-13): CAD v3.4.1 table (--j1): S14 becomes the J1 lip-face seal NZ-04 plus the hot layer NZ-03 (listed, not a seal);
# S16 follows the re-routed FD-07 coil (CAD v3.4.1 z 72-74 engine frame = ~80-83 in the thermal-mesh frame, which sits ~8.5 mm above the
# v3.4.1 pivot frame: band widened to 60-100).  Every other zone is unchanged (the J1 stack sits inside the same lip / aft section).
SEALS_J1 = [s for s in SEALS if s[0] not in ("S13", "S14", "S16")] + [
    ("S13", "TC-09 aft section rod gland: AS568-229 FFKM (Kalrez 7075 class; lead 2026-10-13, was FKM 75) on the case land",
     "case land r 30.5, z ~ -146..-141 (aft closure seal)", "FFKM (was FKM 75)", "FFKM",
     [("ENG-TC-01", 29.5, 31.8, -146.5, -140.5), ("ENG-TC-09", 30.4, 34.0, -146.5, -140.5)], "FE zone"),
    ("S14", "NZ-04 J1 lip-face seal: 0.5 mm oxidation-inhibited flexible graphite", "lip top face r ~15.3-24.9, z ~ -223 (thermal frame)",
     "flexible graphite (OI grade)", "FLEX-GRAPHITE-OI", [("ENG-NZ-04", 0.0, 40.0, -240.0, -200.0)], "FE part"),
    ("S14H", "NZ-03 J1 hot layer: 2.0 mm carbon-phenolic (bearing thermal break, not a seal)", "insert shoulder r ~15.3-24.9, z ~ -221",
     "carbon-phenolic", "CARBON-PHENOLIC-HOT", [("ENG-NZ-03", 0.0, 40.0, -240.0, -200.0)], "FE part"),
    ("S16", "FD-07 feed hose: convoluted PTFE liner, 316 braid (CAD v3.4.1 re-route)", "coil around the case r 43.5-56, z 72-74 (CAD v3.4.1 frame)",
     "PTFE (hose)", "PTFE-hose", [("ENG-TC-01", 31.0, 31.8, 60.0, 100.0)], "BOUND: case OD max over z 60-100 (thermal frame; hose 12-24 mm off the case)"),
]


# v1.2 (2026-10-13, '--v341'): the v1.0/v1.1 zones were written in the CAD v3.3 thermal-mesh frame (zf 112.02, zt 178.02).  The CAD
# v3.4.1 runs (v12 / v13 rev B) put the head 3.39 mm higher (head-top monitor z 181.41) and the aft gland lower: the v1.1 head-end zones
# were 3.4 mm aft of the glands (S01 zone 115.0-119.9 vs the gland 118.41-123.26) and S13 3.9 mm aft of its gland.  v1.2 shifts every
# head-end zone (S01-S12) by dz_head = z(head_top_r12 monitor) - 178.02 per run, re-derives S13 from the v3.4.1 aft gland (structural
# frame z -154.49..-149.64, thermal = structural + 11.90 mm: -142.59..-137.74, +/- 0.5) and widens the S15/S16 case-OD bands to the
# v3.4.1 coil/TEE heights (bound).  Each zone is checked to contain its monitor node where one exists.
def seals_v341(meta):
    mon = {m[0]: m for m in meta["monitors"]}
    dzh = float(mon["head_top_r12"][3]) - ZT
    out = []
    for sid, item, loc, matl, rk, zones, basis in SEALS_J1:
        if sid in ("S13", "S14", "S14H"):
            if sid == "S13":
                zones = [("ENG-TC-01", 29.5, 31.8, -143.1, -137.2), ("ENG-TC-09", 30.4, 34.0, -143.1, -137.2)]
                loc = "case land r 30.5, gland z -142.59..-137.74 (v3.4.1 thermal frame; aft closure seal)"
            out.append((sid, item, loc, matl, rk, zones, basis))
        elif sid in ("S15", "S16"):
            zones = [("ENG-TC-01", 31.0, 31.8, 55.0, 100.0)]
            out.append((sid, item, loc + "; v1.2 band z 55-100 (thermal frame) covers the v3.4.1 TEE and coil heights", matl, rk, zones,
                        "BOUND: case OD max over z 55-100 (thermal frame)"))
        elif sid == "S06":
            # the thermal runs carry the v3.3 bonnet internals (the HV69 flag is not among their config overrides): its rod-seal gland
            # r 2.0-4.45 lies mostly inside the 10 mm bore; the zone takes the gland band with the bore-wall nodes (r <= 5.4)
            zones = [("ENG-TC-04", 0.0, 5.4, ZB - 9.6 + dzh, ZB - 5.0 + dzh)]
            out.append((sid, item, loc + f" [v1.2: gland band z {ZB - 9.6 + dzh:.2f}-{ZB - 5.0 + dzh:.2f} incl. the bore wall r <= 5.4; thermal "
                        "model bonnet = v3.3 internals (HV69 flag off), see 04-fea REPORT]", matl, rk, zones, basis))
        else:
            zones = [(pn_, r0, r1, z0 + dzh, z1 + dzh) for (pn_, r0, r1, z0, z1) in zones]
            out.append((sid, item, loc + f" [v1.2: zone shifted {dzh:+.2f} mm to the v3.4.1 thermal frame]", matl, rk, zones, basis))
    checks = {"S01": "head_oring_lower", "S02": "head_oring_upper", "S04": "bonnet_face_oring", "S06": "bonnet_rod_seal", "S13": "aft_land_oring"}
    zz = {o[0]: o[5] for o in out}
    for sid, mn in checks.items():
        r_, z_ = float(mon[mn][2]), float(mon[mn][3])
        # tolerance 1.0 mm: run_thermal's head_oring_lower monitor is a hard-coded v3.3 position (z 118.0 -> node 117.75), 0.65 mm below
        # the v3.4.1 lower gland (118.41): the zone, not the monitor, follows the gland
        assert any(r0 - 0.3 <= r_ <= r1 + 0.3 and z0 - 1.0 <= z_ <= z1 + 1.0 for (_, r0, r1, z0, z1) in zz[sid]), (sid, mn, r_, z_, zz[sid])
    return out, dzh


# Items outside the 2-D FE model with a bound from another analysis (not per run)
EXTRA = [
    ("S17", "FS-01 MV-P poppet soft seat (PCTFE insert)", "FS-01 module at the zone top (z >= 257, fixed side)", "PCTFE", "PCTFE", 61.0,
     "BOUND: upper-bay air 61 C stratified (servo-mount V3 network, mechanical 2026-10-13, ASSUMED stratification); engine-top radiation not included"),
    ("S18", "FS-01 MV-P balance piston seal (PTFE spring-energised) and stem seal", "FS-01 module", "PTFE + SS spring", "PTFE", 61.0, "as S17"),
    ("S19", "FS-01 static O-rings (plug, bonnet, port adapters), FKM 75", "FS-01 module", "FKM 75", "FKM", 61.0, "as S17"),
    ("S20", "FS-01 ports 1/8 NPT (MSS-2 TC, check, vent plug) and 7/16-20 J602 port seal", "FS-01 module", "PTFE tape / FKM", "PTFE", 61.0, "as S17"),
    ("S21", "-6 JIC 37 deg flares (TEE side, hose ends, union, wall line, FS-01 outlet)", "feed route", "316 metal-to-metal", "METAL", None,
     "no polymer: flare seal; tube-nut torque per SAE J514 / maker"),
]


def zone_ids(X, E, pn, zones):
    ids = set()
    for (p, r0, r1, z0, z1) in zones:
        nn = np.unique(E[pn == p])
        ids |= {int(q) for q in nn if r0 <= X[q][0] <= r1 and z0 <= X[q][1] <= z1}
    return sorted(ids)


def main(labels):
    # v1.1: '--j1' uses the CAD v3.4.1 / J1 seal list, '--out NAME' writes NAME (default seal_table_v1.json, v1 behaviour)
    global SEALS, OUT
    v341 = "--v341" in labels
    if "--j1" in labels or v341:
        SEALS = SEALS_J1
        labels = [l for l in labels if l not in ("--j1", "--v341")]
    if "--out" in labels:
        i = labels.index("--out")
        OUT = HERE / labels[i + 1]
        labels = labels[:i] + labels[i + 2:]
    res = json.loads(OUT.read_text()) if OUT.exists() else {"runs": {}}
    res.update({"script": "04-fea/thermal/seal_table.py v1.2" if v341 else "04-fea/thermal/seal_table.py v1.1", "date": "2026-10-13",
                "method": __doc__.split("\n\n")[1] + (" v1.2: zones moved to the CAD v3.4.1 thermal frame per run (seals_v341)." if v341 else ""),
                "rule_C": LIMIT_RULE_C, "ratings": {k: {"cont_C": v[0], "short_C": v[1], "src": v[2]} for k, v in RATING.items()},
                "seals": [{"id": s[0], "item": s[1], "location": s[2], "material": s[3], "rating": s[4], "zones": s[5], "basis": s[6]} for s in SEALS]})
    for lab in labels:
        run = RUNS / lab
        meta = json.loads((run / f"{lab}_meta.json").read_text())
        segs = meta["segments_s"]
        d = np.load(run / "envelope_nodes.npz", allow_pickle=True)
        X, E, pn = d["X"], d["E"], d["pn"]
        dzh = None
        if v341:
            SEALS, dzh = seals_v341(meta)
            res["seals"] = [{"id": s[0], "item": s[1], "location": s[2], "material": s[3], "rating": s[4], "zones": s[5], "basis": s[6]} for s in SEALS]
        ids = {s[0]: zone_ids(X, E, pn, s[5]) for s in SEALS}
        empty = [k for k, v in ids.items() if not v]
        if empty:
            raise SystemExit(f"{lab}: empty zones {empty}")
        ts, T = [], {k: [] for k in ids}
        for t, vals in at.read_frd_nt(run / f"{lab}.frd"):
            ts.append(t)
            for k, v in ids.items():
                T[k].append(max(vals[q + 1] for q in v))
        ts = np.array(ts)
        inb = np.zeros(len(ts), bool)
        for (a, b) in segs:
            inb |= (ts > a - 1e-6) & (ts <= b + 1e-6)
        post = (~inb) & (ts > segs[0][0])
        row = {"dc": meta["case"].get("dc"), "segments_s": segs, "material_overrides": meta.get("material_overrides"), "dz_head_mm": dzh,
               "config_overrides": meta.get("config_overrides"), "n_frames": int(len(ts)), "seals": {}}
        for k, v in ids.items():
            y = np.array(T[k]) - 273.15
            dt = np.diff(ts)
            hot = (y[1:] > LIMIT_RULE_C) & (y[:-1] > LIMIT_RULE_C)
            ib, pb = int(np.argmax(np.where(inb, y, -1e9))), int(np.argmax(np.where(post, y, -1e9)))
            row["seals"][k] = {"n_nodes": len(v), "T_inburn_max_C": round(float(y[ib]), 1), "t_inburn_max_s": round(float(ts[ib]), 2),
                               "T_postburn_max_C": round(float(y[pb]), 1), "t_postburn_max_s": round(float(ts[pb]), 2),
                               "s_above_175C": round(float(np.sum(dt[hot])), 2)}
        res["runs"][lab] = row
        print(lab, json.dumps({k: (v["T_inburn_max_C"], v["T_postburn_max_C"]) for k, v in row["seals"].items()}))
    # ---------------------------------------------------------------- table over the runs present
    tab = []
    for s in SEALS:
        k = s[0]
        cont, short, src = RATING[s[4]]
        cells = {}
        Tall = -1e9
        for lab, row in res["runs"].items():
            r = row["seals"].get(k)
            if r is None:
                continue
            cells[lab] = [r["T_inburn_max_C"], r["T_postburn_max_C"], r["s_above_175C"]]
            Tall = max(Tall, r["T_inburn_max_C"], r["T_postburn_max_C"])
        tab.append({"id": k, "item": s[1], "location": s[2], "material": s[3], "rating_cont_C": cont, "rating_short_C": short,
                    "T_max_all_runs_C": round(Tall, 1), "margin_to_cont_K": round(cont - Tall, 1) if cont else None,
                    "above_175C": bool(Tall > LIMIT_RULE_C), "per_run_inburn_postburn_s175": cells, "basis": s[6]})
    for (k, item, loc, matl, rk, Tb, basis) in EXTRA:
        cont, short, src = RATING[rk]
        tab.append({"id": k, "item": item, "location": loc, "material": matl, "rating_cont_C": cont, "rating_short_C": short,
                    "T_max_all_runs_C": Tb, "margin_to_cont_K": round(cont - Tb, 1) if (cont and Tb is not None) else None,
                    "above_175C": bool(Tb is not None and Tb > LIMIT_RULE_C), "per_run_inburn_postburn_s175": {}, "basis": basis})
    res["table"] = tab
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
