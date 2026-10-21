"""F2 (lead brief 2026-10-21T08:05:00Z; CHANGELOG 253 (10) 'the torch-port dT and the BL-08 temperature [MISSING]'): the torch-port
temperature rise over the F1 event times (ARM, re-zero1, re-zero2, E1, light) for A1 and the B1 stand relight, and the BL-08 (P_mid)
temperature for the U570 comparator band.  Mechanical, 2026-10-21.  Paper / Python only: reads the published-to-work-tree F1 result
c1_seat_v352_v1.json (435f5d71f6213160; script c1_seat_v352.py fe1f41a73f25a0bc) and the CAD v3.5.2 geometry; no new FE.

TORCH PORT.  The torch seat (ENG-TC-02 head top, M10x1 x 10 at r 25, az 0; parts_engine.py: seat zt-10 ... zt, then the 5.2 mm passage
from r 25, zt-9.5 inward to the 30 deg 3 mm outlet) lies on the same ring r 25 as the C1 Pc seat (az 105 in parts_engine.py).  The thermal
FE is axisymmetric, so its metal history at the torch seat IS the F1 history at r 25 (tap mouth zt-0.5, mid zt-4.75, zt-8, zt-9.5, zt-11):
the event-to-event rises below are those F1 values [SIM, the A1 / B1 UPPER-bound heat-transfer runs as F1].  They are the HEAD's
contribution only.  NOT in any model (MISSING): the local heat in the seat and the passage (the torch flame and hot gas from E0 to the
light and in any torch-on time; the chamber gas that fills the 5.2 mm passage and the 3 mm outlet during each burn), conduction from the
ENG-IG-01 body, and the 3-D seat boss.  Sign: the relight torch adds heat inside re-zero2 -> E1 / light, while the local heat of the
earlier light and burn decays over the same coast interval; both are MISSING and the net sign is not shown, so NO interval below is a
bound on the torch-port rise (the predecessor's 'lower bound' reading is withdrawn).  The P_torch transducer (TE M3234-000005-070BG, J901, electronics.json)
is on the torch, not in the head: its own temperature is MISSING, and its zero coefficient is Electronics' (not restated here).
What it would take: Combustion's torch heat input to the passage wall (torch gas temperature and h, the torch-on schedule E0 -> light and
in the burns) with a 3-D local thermal model of the seat boss and the ENG-IG-01 nose (new FE), or a thermocouple at the torch seat and on
the ENG-IG-01 body beside the 070BG in B-TC-1 / static fire.

BL-08.  ENG-BL-08 (P_mid, Kulite XTL-190SM-2000A on the C1 chain, U570 comparator) sits on the bleed manifold ENG-BL-07 boss at
(12.58, 32.77) mm, z 268.0 (r 35.1, az 69; checks/bleed_topology_v3.5.2.json d4e0639e319e3581), about 92 mm above the head top, on the
FIXED module (parts_bleed.py places BL-05 / BL-07 / BL-08 'fixed'; airframe mount TO-DEFINE, ICD-14).  Its only links to the engine are
the 1/8 x 0.028 in 316L fixed line BL-03F and the -2 PTFE / 316 braid crossing hose BL-04: no structural conduction path from the head.
Its temperature is set by the bay air, radiation from the engine (TC-01 case, TC-02 head, feed parts), the airframe mount and, with V1
open, the bleed N2O; none is in a Mechanical model: MISSING (no number is given).  What it would take: a bay thermal model (view factors
from the A1 / B1 SIM engine surface fields to BL-07 / BL-08, bay air, the mount once ICD-14 defines it, the purge N2O) or a thermocouple
on the BL-08 body in B-TC-1 / static fire and on the A1 vehicle.
Tags: SIM (F1 values), DERIVED (differences), MISSING as stated.  Not physical approval.
usage: python3 -B -I torch_port_bl08_v352.py
"""
import hashlib, json
from pathlib import Path

MECH = Path("/home/claude/work/mechanical/v352")
HUBE = Path("/home/claude/work/shared-fallback/engine")
OUT = MECH / "c1seat/torch_port_bl08_v352_v1.json"
INP = {"c1_seat_v352_v1_json": (MECH / "c1seat/c1_seat_v352_v1.json", "435f5d71f6213160"),
       "c1_seat_v352_py": (MECH / "c1seat/c1_seat_v352.py", "fe1f41a73f25a0bc"),
       "bleed_topology_v3.5.2_json": (HUBE / "03-cad/v3.5.2/checks/bleed_topology_v3.5.2.json", "d4e0639e319e3581"),
       "parts_engine_py": (HUBE / "03-cad/v3.5.2/src/parts_engine.py", "8e3df6841d149c88"),
       "parts_bleed_py": (HUBE / "03-cad/v3.5.2/src/parts_bleed.py", "c1d6b20859038456"),
       "electronics_json": (HUBE / "interfaces/electronics.json", "11f7896ad0d0613b")}
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
for k, (p, s16) in INP.items():
    assert sha(p) == s16, (k, sha(p))
F1 = json.loads(INP["c1_seat_v352_v1_json"][0].read_text())
BT = json.loads(INP["bleed_topology_v3.5.2_json"][0].read_text())
PE = INP["parts_engine_py"][0].read_text()
PB = INP["parts_bleed_py"][0].read_text()
EL = json.loads(INP["electronics_json"][0].read_text())
assert 'ANG = {"pc": 105.0, "torch": 0.0' in PE and "TORCH_R = 25.0" in PE and "cuts.append(cyl(9.0, zt - 10, zt + 1, cto[0], cto[1]))" in PE
assert 'pm.place(T, "fixed")' in PB and '"manifold": {"z0": 255.0, "z1": 265.0' in PB
pmid = BT["items"]["P_mid"]
assert pmid["pn"] == "ENG-BL-08" and pmid["port_xy_mm"] == [12.58, 32.77] and pmid["z_port_mm"] == 268.0
pmc = EL["head_end_bleed_provision"]["pmid_comparator"]["v"]

SEAT = ["tap_mouth_zt-0.5", "tap_mid_zt-4.75", "zt-8.0", "diaphragm_zt-9.5", "zt-11.0"]   # r 25: seat zt-10 ... zt, passage from zt-9.5
EV = {"A1_NF2b": {"ARM": "ARM", "rezero1_end": "rezero1_end_COAST+1.4s", "rezero2_end": "rezero2_end", "E0": "E0", "E1": "E1", "light": "light"},
      "B1_R4_GVLO": {"ARM": "ARM", "rezero1_end": "rezero1_end_S+1.4s", "rezero2_end": "stand_rezero2_end_S+15.72s", "E0": "stand_E0_S+18.67s",
                     "E1": "stand_E1_S+18.715s", "light": "stand_light_S+19.03s"},
      "B1_R4_GVHI": {"ARM": "ARM", "rezero1_end": "rezero1_end_S+1.4s", "rezero2_end": "stand_rezero2_end_S+15.72s", "E0": "stand_E0_S+18.67s",
                     "E1": "stand_E1_S+18.715s", "light": "stand_light_S+19.03s"}}
PAIRS = [("ARM", "rezero1_end"), ("ARM", "E1"), ("ARM", "light"), ("rezero1_end", "rezero2_end"), ("rezero1_end", "E1"), ("rezero1_end", "light"),
         ("rezero2_end", "E1"), ("rezero2_end", "light")]
TORCH_IN = {("rezero2_end", "E1"), ("rezero2_end", "light")}             # intervals that contain the relight torch firing (E0)
runs = {}
for rk, ev in EV.items():
    R = F1["runs"][rk]
    T = R["T_K_at_events"]
    ts = {e: T[n]["t_s"] for e, n in ev.items()}
    assert ts["ARM"] < ts["rezero1_end"] < ts["rezero2_end"] < ts["E0"] < ts["E1"] < ts["light"]
    rows = {}
    for a, b in PAIRS:
        d = {pt: round(T[ev[b]][pt] - T[ev[a]][pt], 3) for pt in SEAT}
        rows[f"{a}->{b}"] = {"t_s": [ts[a], ts[b]], "dT_K_by_depth": d, "dT_K_min_max": [min(d.values()), max(d.values())],
                             "reading": ("head contribution only; NOT a bound: the relight torch heat from E0 (adds) and the decay of the earlier light's local heat (subtracts) are both MISSING" if (a, b) in TORCH_IN
                                         else "head contribution only; NOT a bound: the local heat of the earlier light and burn in the seat and passage (MISSING) decays over the interval"),
                             "tag": "SIM (F1 point values, A1 / B1 upper-bound runs) / DERIVED"}
        # cross-check against F1's own drift table where it has the pair
        key = f"{ev[a].replace('rezero1_end_COAST+1.4s', 'rezero1_end').replace('rezero1_end_S+1.4s', 'rezero1_end').replace('stand_rezero2_end_S+15.72s', 'stand_rezero2_end').replace('stand_E1_S+18.715s', 'stand_E1').replace('stand_light_S+19.03s', 'stand_light')}->" \
              f"{ev[b].replace('rezero1_end_COAST+1.4s', 'rezero1_end').replace('rezero1_end_S+1.4s', 'rezero1_end').replace('stand_rezero2_end_S+15.72s', 'stand_rezero2_end').replace('stand_E1_S+18.715s', 'stand_E1').replace('stand_light_S+19.03s', 'stand_light')}"
        if key in R["drifts"]:
            for pt in SEAT:
                assert abs(R["drifts"][key][pt]["dT_K"] - (T[ev[b]][pt] - T[ev[a]][pt])) < 1e-9, (rk, key, pt)
            rows[f"{a}->{b}"]["F1_drift_table_key_checked"] = key
    runs[rk] = {"dir": R["dir"], "zt_mm": R["zt_mm"], "event_times_s": ts, "rises": rows,
                "T_K_at_events_seat_points": {e: {pt: round(T[n][pt], 3) for pt in SEAT} for e, n in ev.items()}}
res = {"id": "torch_port_bl08_v352", "version": "v1", "date": "2026-10-21", "owner": "mechanical", "basis": __doc__.strip(),
       "inputs": {k: {"path": str(p), "sha256_16": s16} for k, (p, s16) in INP.items()},
       "torch_port": {"geometry": "ENG-TC-02 head top: torch seat M10x1 x 10 at r 25.0, az 0 (seat zt-10 ... zt, modelled at 9.0 mm), 5.2 mm passage from r 25, zt-9.5 to the 30 deg 3 mm outlet (parts_engine.py); the C1 Pc seat is on the same ring r 25 (az 105)",
                      "points_r25": SEAT, "runs": runs,
                      "MISSING": ["the torch's own heat input to the seat, the 5.2 mm passage and the 3 mm outlet (torch flame / hot gas, E0 -> light and any torch-on time in a burn)",
                                  "conduction from the ENG-IG-01 torch body and nose", "the 3-D seat boss (the FE is axisymmetric)",
                                  "the temperature of the P_torch transducer itself (TE M3234-000005-070BG on the torch, J901)"],
                      "what_it_would_take": "Combustion's torch heat input to the passage wall (gas temperature and h, the torch-on schedule) with a 3-D local thermal model of the seat boss and the ENG-IG-01 nose (new FE), or thermocouples at the torch seat and on the ENG-IG-01 body beside the 070BG in B-TC-1 / static fire",
                      "summary": None},
       "BL-08": {"part": "ENG-BL-08 P_mid transducer (Kulite XTL-190SM-2000A, C1 chain, U570 comparator)",
                 "location": {"port_xy_mm": pmid["port_xy_mm"], "z_port_mm": pmid["z_port_mm"], "r_az": "r 35.1, az 69", "position": pmid["position"],
                              "above_head_top_mm": round(pmid["z_port_mm"] - F1["runs"]["A1_NF2b"]["zt_mm"], 1),
                              "module": "FIXED (parts_bleed.py places BL-05 / BL-07 / BL-08 'fixed'; airframe mount TO-DEFINE, ICD-14)",
                              "links_to_engine": "1/8 x 0.028 in 316L fixed line BL-03F and the -2 PTFE / 316 braid crossing hose BL-04 only: no structural conduction path from the head"},
                 "temperature": "MISSING (no Mechanical model covers it; no number given)",
                 "drivers_not_modelled": ["bay air", "radiation from the engine (TC-01 case, TC-02 head, feed parts)", "the airframe mount (ICD-14 TO-DEFINE)", "the bleed N2O with V1 open"],
                 "what_it_would_take": "a bay thermal model (view factors from the A1 / B1 SIM engine surface fields to BL-07 / BL-08, bay air, the mount once ICD-14 defines it, the purge N2O), or a thermocouple on the BL-08 body in B-TC-1 / static fire and on the A1 vehicle",
                 "for_U570": {"electronics_pmid_comparator_read": {k: pmc.get(k) for k in ("band_note", "low_threshold_option") if k in pmc},
                              "note": "Electronics' thermal-zero term at BL-08 stays MISSING: the low U570 threshold near 2 bar abs is not supported by a Mechanical temperature (lead 253 (7)(v): not credited as detection)"}}}
a1 = runs["A1_NF2b"]["rises"]; glo = runs["B1_R4_GVLO"]["rises"]; ghi = runs["B1_R4_GVHI"]["rises"]
fmt = lambda r: f"{r['dT_K_min_max'][0]:+.3f} to {r['dT_K_min_max'][1]:+.3f} K"
res["torch_port"]["summary"] = (
    f"Torch seat (r 25, az 0) head-metal rise, the five r 25 points zt-0.5 ... zt-11 [SIM / DERIVED]: A1 re-zero2 end -> E1 {fmt(a1['rezero2_end->E1'])}, "
    f"re-zero2 end -> light {fmt(a1['rezero2_end->light'])}, re-zero1 end -> light {fmt(a1['rezero1_end->light'])}, ARM -> light {fmt(a1['ARM->light'])}; "
    f"B1 stand relight GVLO / GVHI: re-zero2 end -> light {fmt(glo['rezero2_end->light'])} / {fmt(ghi['rezero2_end->light'])}, re-zero1 end -> E1 "
    f"{fmt(glo['rezero1_end->E1'])} / {fmt(ghi['rezero1_end->E1'])}. These are the head's contribution only, NOT bounds: the local heat in the seat and passage "
    f"(relight torch from E0, the earlier light and burn decaying), the ENG-IG-01 conduction, the 3-D boss and the 070BG's own temperature are MISSING.")
s = json.dumps(res, indent=1)
OUT.write_text(s)
print(OUT.name, hashlib.sha256(s.encode()).hexdigest()[:16], len(s))
print(res["torch_port"]["summary"])
