"""Mass delta v3.5.2 vs the frozen v3.5.1 (lead CHANGELOG 206 (2): 'a mass-delta file and a second massprops for a P2 sensitivity').
Mechanical, 2026-10-13, v1.  Inputs: 03-cad/massprops_v3.5.1.json (frozen, 488b47f9d55ff91b) and 03-cad/massprops_v3.5.2.json.
v2 (2026-10-19, INTERIM v3.5.2 set, lead resume items 1-3 + 11): + N-F2 (NZ-01 shoulder R 1.0, NZ-06 foil 0.25), GM-01/GM-02 lever
roots, J-FWD 10x M5 (lead 231 (1); no case land), J-FD01 (TC-02 flat / FD-01 ears / 3x M4), J-FD09 A4-80, hardware v1.2; GNC re-fly trigger
statement (>= 0.10 kg confirmed landing-mass growth vs the v3.5.1 ledger).
v3 (2026-10-20, lead DC ~03:55Z, FEA3D INTERIM 1 item 1): GM-01/GM-02 arm + back-web / root junction loop fillet R1.5 with the far-side
top S-curve (R1.0 convex / R2.41 concave) and the under-arm web outer corner at r 39.0: +78.6 mm3 each (CAD, 7075-T6).
v4 (2026-10-20, lead DC 6(b) ~04:45Z, interim rev 3): GM-01/GM-02 far-side S-curve cutter run out over the full arm length (-0.512 mm3
each) and a vertical R0.5 corner fill between the cheek low-u end face and the back-web near face above the cheek extension top
(+0.009 mm3 each beyond rev 2): -0.499 mm3 each (CAD, 7075-T6); hardware v1.4 (HW-101 3.0 N m; torque / test fields only, no mass change).
v5 (2026-10-20, interim rev 4, lead DC 05:42Z item 4 / 06:05Z item 4 / 06:23Z items 2, 3, 6): TC-02 seat-bore entry d14.0 x 0.5 + R0.5 and
d14.5 thread relief at the d10 shoulder (-39.95 mm3, 6061-T6); TC-03 thread undercut d12.5 R0.6, 0.70 x 45 deg + R0.25 top edge, top 0.15
below the shoulder (-61.03 mm3, GlidCop AL-15); J-FWD head-seat option (a) d10.5 OD spot face kept as a rev-4 parameter, OFF in this set
(-0.505 g if the lead adopts it at FA1S; v352/checks/test_r4_v1.json).
v6 (2026-10-20, interim rev 4 + J-FWD head seat (a), lead 07:21Z: d10.5 spot face ADOPTED on FEA3D's FA1S [DERIVED] seat checks):
TC-01 10x d10.5 flat at r 31.313 (wall 2.688 at the hole), -0.505 g (CAD, 6061-T6; v352/checks/test_r4s_v1.json).
v7 (2026-10-20, lead 08:40Z item 3 'HW-150 sourced size (AS568-226, ID 50.39 x CS 3.53) accepted. Publish massdelta v7 (+0.37 g)'):
hardware_v352 v1.6, HW-150 2x AS568-226 FKM 90A unit mass 2.965 -> 3.150 g (CALC torus on the sourced ID, FKM 1900 kg/m3 ASSUMED).
v8 (2026-10-20, interim r5h: hardware_v352 v1.7, J-FWD route (i), lead 16:53Z R2 / R3, 17:55:55Z F1-F5, 18:36:37Z): HW-101 = ENG-HW-101-IN718
M5 x 10.7 with the pilot (CALC 2.028 -> 2.179 g each, IN718 8190 kg/m3), HW-170 disc spring x 10 (CALC 0.226 g each, SS-SPRING 7900 kg/m3):
+3.77 g; the part files stay rev 4 + head seat (a) until the FINAL set (rev 5 TC-01 changes come with it).
v9 (2026-10-20, FINAL v3.5.2 set, lead release 19:09:50Z): rev-5 part files (dev rev-5 source; only ENG-TC-01 differs from the interim
r4h6 part files: 10x J-FWD flats cut with the d11.2 cutter on the depth rule, lead 16:53Z R2 P(i)-1 / R4, -0.280 g CAD) with hardware v1.7."""
import json, hashlib, sys
from pathlib import Path
CAD = Path(__file__).resolve().parents[2]
A = CAD / "massprops_v3.5.1.json"
B = CAD / "massprops_v3.5.2.json"
OUT = CAD / "massdelta_v3.5.2_vs_v3.5.1.json"
sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()[:16]
a, b = json.loads(A.read_text()), json.loads(B.read_text())
def led(m):
    d = {}
    for r in m["ledger_mid"]:
        k = (r["pn"], r["group"])
        d[k] = d.get(k, 0.0) + r["m_kg"]
    return d
la, lb = led(a), led(b)
rows = []
for k in sorted(set(la) | set(lb)):
    dm = lb.get(k, 0.0) - la.get(k, 0.0)
    if abs(dm) > 1e-5:
        rows.append({"pn": k[0], "group": k[1], "v351_kg": round(la.get(k, 0.0), 6), "v352_kg": round(lb.get(k, 0.0), 6), "delta_kg": round(dm, 6)})
WHY = {"ENG-TC-09": "lead 206 (2a) TC-09 thinning: barrel radial wall 2.47 -> 1.80 mm, socket OD 72.0 -> 69.0 above the gland (CALC, IN718 8190 kg/m3); "
                    "CONDITIONAL: accepted only if the v352 thermal + S-AX re-run meets 183 (1) with the 194 period domain",
       "ENG-HW-121": "lead 206 (2b) Ti-6Al-4V (ASTM F468 R56400) for A4-70 (CALC x 4430/8000)",
       "ENG-HW-123": "lead 206 (2b) Ti-6Al-4V (ASTM F468 R56400) for A4-70 (CALC x 4430/8000)",
       "ENG-GM-01": "item 1 (lead 2026-10-19): lever-root redesign, through-band root r 33.25-38.5 +/-22 deg, boss r 38.5, R_v 2.5 / R_j 1.25 / R_b 1.0 / R_arm 1.5; "
                    "v3.5.2 rev (lead 2026-10-20 DC): arm + back-web / root junction loop fillet R1.5 + far-side top S-curve, +78.6 mm3 = +0.22 g (CAD, 7075-T6); "
                    "rev 3 (lead DC 6(b)): far-side cutter run-out + cheek / back-web corner R0.5, -0.50 mm3 (-0.001 g)",
       "ENG-GM-02": "item 1 (lead 2026-10-19): lever-root redesign, as GM-01; v3.5.2 rev (lead 2026-10-20 DC): junction loop fillet as GM-01, +78.6 mm3 = +0.22 g (CAD, 7075-T6); "
                    "rev 3 (lead DC 6(b)): as GM-01, -0.50 mm3 (-0.001 g)",
       "ENG-TC-01": "item 11 (lead CHANGELOG 231 (1)): J-FWD 8 -> 10 radial 5.5 holes at az 18 + 36k deg (CAD, 6061-T6); no case land; "
                    "J-FWD head seat (a) (lead 07:21Z): 10x d10.5 spot face flat at r 31.313, wall 2.688 at the hole, -0.505 g (CAD); "
                    "rev 5 (lead 16:53Z R2 P(i)-1 / R4, FINAL set): the 10 flats cut with the d11.2 cutter at r_flat 31.313 +0.020/0 from datum A "
                    "(depth rule), -0.280 g vs the d10.5 flats (CAD)",
       "ENG-TC-02": "item 2: J-FD01 flat r 30.5 -> 29.5, +/-10 -> +/-13, 2x M3 taps -> 3x M4 taps; item 11: J-FWD 8 -> 10 M5 taps (CAD, 6061-T6); "
                    "rev 4 (lead 05:42Z / 06:05Z / 06:23Z): seat-bore entry d14.0 x 0.5 + R0.5, d14.5 thread relief at the d10 shoulder, -39.95 mm3 = -0.108 g (CAD)",
       "ENG-TC-03": "rev 4 (lead 05:42Z / 06:05Z / 06:23Z): thread undercut d12.5 R0.6 at the flange, 0.70 x 45 deg + R0.25 top edge, top 0.15 below the "
                    "TC-02 shoulder, -61.03 mm3 = -0.543 g (CAD, GlidCop AL-15 8900 kg/m3)",
       "ENG-FD-01": "item 2: J-FD01 lower ears +/-13.5 (zb+0.5..zb+10, +y ear relieved round BL-03E), 3x M4 clearance + cbore d8 (CAD, 316L)",
       "ENG-FD-04": "item 11 follow-on: FD-04 shield top trimmed to 1 mm below the J-FWD screw heads (ISO 7380-1 M5 heads not modelled; hidden v3.5.1 clash, 1.6 mm3 at az 157.5 / 202.5, also present in the frozen set) (CAD, 316L)",
       "ENG-NZ-01": "lead 212 N-F2: NZ-01 shoulder edge R 1.0 (CAD)",
       "ENG-NZ-02": "lead 212 N-F2: sleeve 0.25 mm shorter (the foil adds 0.25 mm to the J1 stack, the insert shoulder rises 0.25 mm) (CAD, carbon-phenolic)",
       "ENG-NZ-06": "lead 212 N-F2: NZ-06 flexible-graphite foil 0.25 mm (CAD)",
       "ENG-HW-101": "item 11 (lead 231 (1)): HW-101 8 -> 10x ISO 7380-1 M5 x 10 A4-80 (CALC); hardware v1.7 (route (i), lead 16:53Z R2): "
                     "ENG-HW-101-IN718 M5 x 10.7 +/-0.1 with the pilot 5.15 x 0.30, 2.179 g each (CALC, IN718 8190 kg/m3)",
       "ENG-HW-170": "hardware v1.7 (route (i), lead 16:53Z R2): 10x disc spring DIN EN 16983 A10 (10 x 5.2 x 0.5, 1.4568), 0.226 g each "
                     "(CALC flat annulus x SS-SPRING 7900 kg/m3)",
       "ENG-HW-103": "item 2: HW-103 2x M3 x 16 A4-70 -> 2x M4 x 20 A4-80 (CALC)",
       "ENG-HW-103B": "item 2: HW-103B 1x M4 x 16 A4-80 added (CALC)",
       "ENG-HW-150": "hardware v1.6 (lead 08:40Z item 3): 2x AS568-226 FKM 90A on the sourced size ID 50.39 x CS 3.53 (FNST p. 16), CALC torus x FKM "
                     "1900 kg/m3 ASSUMED, 2.965 -> 3.150 g each (the v3.5.1 CALC used the -225 ID 47.22, AS RECALLED)"}
for r in rows:
    r["why"] = WHY.get(r["pn"], "hardware carried scale max(0.20 kg, CALC) / host CG redistribution" if r["pn"].startswith("ENG-HW") else "TO-EXPLAIN")
st = {}
for s in ("wet", "mid", "burnout", "nograin"):
    st[s] = {}
    for g in ("engine", "fixed", "ring", "horn", "pushrod", "all"):
        ea, eb = a["states"][s][g], b["states"][s][g]
        st[s][g] = {"m_v351_kg": ea["m_kg"], "m_v352_kg": eb["m_kg"], "dm_kg": round(eb["m_kg"] - ea["m_kg"], 5),
                    "cg_v351_mm": ea["cg_mm"], "cg_v352_mm": eb["cg_mm"], "dcg_mm": [round(y - x, 3) for x, y in zip(ea["cg_mm"], eb["cg_mm"])],
                    "I_pivot_diag_v351_kgm2": [ea["I_pivot_kgm2"][i][i] for i in range(3)], "I_pivot_diag_v352_kgm2": [eb["I_pivot_kgm2"][i][i] for i in range(3)],
                    "dI_pivot_diag_kgm2": [round(eb["I_pivot_kgm2"][i][i] - ea["I_pivot_kgm2"][i][i], 7) for i in range(3)]}
tc09 = sum(r["delta_kg"] for r in rows if r["pn"] == "ENG-TC-09")
dl = st["burnout"]["all"]["dm_kg"]
TRIG = 0.10
gnc = {"rule": "GNC re-fly if the CONFIRMED landing-mass growth vs the v3.5.1 ledger is >= 0.10 kg (lead / GNC trigger)",
       "landing_state": "burnout (group all); the delta is the same in every state (no propellant or grain change)",
       "dm_landing_kg": round(dl, 4), "dm_landing_without_TC09_thinning_kg": round(dl - tc09, 4), "TC09_thinning_kg": round(tc09, 4),
       "verdict": ("BELOW the trigger with and without the conditional TC-09 thinning: no re-fly by mass" if max(dl, dl - tc09) < TRIG
                   else "AT OR ABOVE the trigger: GNC re-fly"),
       "evidence": "CALC (CAD volume x engmat density + hardware CALC); not weighed, so not a 'confirmed' mass; COTS masses unchanged"}
out = {"id": "massdelta_v3.5.2_vs_v3.5.1", "version": "v9", "date": "2026-10-20", "owner": "mechanical", "units": "kg, mm, kg m2; engine frame, origin pivot (frozen)",
       "files": {"v351": {"path": "03-cad/v3.5.1/massprops_v3.5.1.json", "sha256_16": sha(A)}, "v352": {"path": "03-cad/v3.5.2/massprops_v3.5.2.json", "sha256_16": sha(B)}},
       "status": ("FINAL v3.5.2 set (lead release 19:09:50Z; lead resume 2026-10-19 items 1-11): lever roots, J-FD01, J-FD09, J-FWD route (i) "
                  "(rev 5 TC-01 flats with the d11.2 cutter, hardware v1.7: ENG-HW-101-IN718 + HW-170 disc springs), rev 4 TC-02 / TC-03 seat "
                  "relief, N-F2 / N-F2b; CAD / CALC, not weighed; TC-09 thinning stays conditional on its re-run (206 (2a)) as in the interim"),
       "gnc_trigger": gnc,
       "changes_in": ["TC-09 thinning (206 (2a), conditional)", "Ti-6Al-4V screws HW-121, HW-123 (206 (2b); R3 100 mm rule)",
                      "N-F2: NZ-01 shoulder R 1.0 + NZ-06 foil 0.25 (212)", "GM-01/GM-02 lever roots (item 1)",
                      "GM-01/GM-02 lever-root junction loop fillet R1.5 (lead DC 2026-10-20, +0.44 g for the pair)",
                      "GM-01/GM-02 rev 3: far-side cutter run-out + cheek / back-web corner R0.5 (lead DC 6(b) 2026-10-20, -0.003 g for the pair)",
                      "J-FWD 10x M5 A4-80, no case land (item 11, lead 231 (1))", "J-FD01: TC-02 flat + FD-01 ears + 3x M4 A4-80 (item 2)",
                      "J-FD09: A4-80 1.8 N m (item 3, no mass change)", "FD-04 shield top trim (J-FWD screw-head clearance 1.0 mm)",
                      "hardware_v352 v1.4 (v1.3 / v1.4 change torque, test and interval fields only: no mass change vs v1.2)",
                      "rev 4 TC-02 / TC-03 seat relief (lead 05:42Z item 4, 06:05Z item 4, 06:23Z items 2-3): -0.651 g for the pair",
                      "J-FWD head seat (a): TC-01 10x d10.5 spot face (lead 07:21Z, FEA3D FA1S seat checks): -0.505 g",
                      "hardware_v352 v1.6: HW-150 2x AS568-226 on the sourced size (lead 08:40Z item 3; CALC torus, FKM 1900 kg/m3 ASSUMED): +0.37 g",
                      "hardware_v352 v1.7: J-FWD route (i): ENG-HW-101-IN718 M5 x 10.7 with the pilot (+1.51 g for 10) and HW-170 disc spring x 10 "
                      "(+2.26 g) (lead 16:53Z R2, CALC): +3.77 g",
                      "rev 5 (FINAL set): TC-01 J-FWD flats with the d11.2 cutter on the depth rule (lead 16:53Z R2 P(i)-1 / R4): -0.280 g (CAD)"],
       "not_in": {"(2b) HW-126 ICD-1L Ti": "-7.47 g CALC, needs the airframe ICD agreement",
                  "(2b) HW-113 / HW-115 / HW-124 Ti": "-8.4 g CALC only if the lead accepts the 50 mm R3 distance (line of sight not credited)",
                  "(2c) 316L -> 6061 upstream of the MV": "only FD-12F (13.5 g 316L, socket for the 316L tank line: dissimilar braze/weld) is upstream; ~9 g; not pursued",
                  "(2d) BL-07 pocketing": "1.98 g free without the valve sub-base pattern and the P_mid port (v352/checks/bl07_pockets_v1.json); not implemented",
                  "(4) bleed valves <= 0.15 kg": "search continues; ASSUMED 0.30 kg each kept",
                  "item 11 J-FWD case land (line 230 (1) FA1S option, +21.7 g)": "WITHDRAWN by lead 231 (1); the 127 bar abs land option lapses with it",
                  "item 11 grade option O4": "8x M5 in a >= 800 / 1000 MPa stainless (A4-100 class): 0 g, needs a datasheet / availability; not implemented",
                  "item 1 rod-force limit": "alternative to the lever-root change (rod force <= ~326-344 N SR): not chosen, no mass effect",
                  "J-FWD head-seat option (b) saddle washer": "not chosen (lead 07:21Z adopted (a)); no CAD"},
       "rows_mid_by_part": rows, "states": st,
       "evidence": "CAD (volume x engmat density) and HARDWARE CALC; COTS masses unchanged (ASSUMED/ESTIMATE as in v3.5.1)"}
s = json.dumps(out, indent=1)
OUT.write_text(s)
print(OUT.name, sha(OUT))
print("GNC trigger:", json.dumps(gnc))
for r in rows: print(f"  {r['pn']:12s} {r['group']:7s} {r['delta_kg']*1e3:+8.2f} g")
for s_ in ("wet", "mid", "burnout"):
    e = st[s_]["engine"]; f = st[s_]["fixed"]; al = st[s_]["all"]
    print(s_, "engine", e["dm_kg"], "dcg", e["dcg_mm"], "dI", e["dI_pivot_diag_kgm2"], "| fixed", f["dm_kg"], "| all", al["dm_kg"], al["m_v352_kg"])
