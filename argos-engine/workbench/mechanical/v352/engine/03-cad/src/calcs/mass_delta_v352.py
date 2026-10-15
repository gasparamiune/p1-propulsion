"""Mass delta v3.5.2 vs the frozen v3.5.1 (lead CHANGELOG 206 (2): 'a mass-delta file and a second massprops for a P2 sensitivity').
Mechanical, 2026-10-13, v1.  Inputs: 03-cad/massprops_v3.5.1.json (frozen, 488b47f9d55ff91b) and 03-cad/massprops_v3.5.2.json."""
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
       "ENG-HW-123": "lead 206 (2b) Ti-6Al-4V (ASTM F468 R56400) for A4-70 (CALC x 4430/8000)"}
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
out = {"id": "massdelta_v3.5.2_vs_v3.5.1", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "units": "kg, mm, kg m2; engine frame, origin pivot (frozen)",
       "files": {"v351": {"path": "03-cad/v3.5.1/massprops_v3.5.1.json", "sha256_16": sha(A)}, "v352": {"path": "03-cad/v3.5.2/massprops_v3.5.2.json", "sha256_16": sha(B)}},
       "status": "SENSITIVITY for GNC P2 (lead 206 (2)); v3.5.2 is NOT a frozen baseline: TC-09 thinning is conditional on its re-run",
       "changes_in": ["TC-09 thinning (206 (2a), conditional)", "Ti-6Al-4V screws HW-121, HW-123 (206 (2b); R3 100 mm rule)"],
       "not_in": {"(2b) HW-126 ICD-1L Ti": "-7.47 g CALC, needs the airframe ICD agreement",
                  "(2b) HW-113 / HW-115 / HW-124 Ti": "-8.4 g CALC only if the lead accepts the 50 mm R3 distance (line of sight not credited)",
                  "(2c) 316L -> 6061 upstream of the MV": "only FD-12F (13.5 g 316L, socket for the 316L tank line: dissimilar braze/weld) is upstream; ~9 g; not pursued",
                  "(2d) BL-07 pocketing": "1.98 g free without the valve sub-base pattern and the P_mid port (v352/checks/bl07_pockets_v1.json); not implemented",
                  "(4) bleed valves <= 0.15 kg": "search continues; ASSUMED 0.30 kg each kept"},
       "rows_mid_by_part": rows, "states": st,
       "evidence": "CAD (volume x engmat density) and HARDWARE CALC; COTS masses unchanged (ASSUMED/ESTIMATE as in v3.5.1)"}
s = json.dumps(out, indent=1)
OUT.write_text(s)
print(OUT.name, sha(OUT))
for r in rows: print(f"  {r['pn']:12s} {r['group']:7s} {r['delta_kg']*1e3:+8.2f} g")
for s_ in ("wet", "mid", "burnout"):
    e = st[s_]["engine"]; f = st[s_]["fixed"]; al = st[s_]["all"]
    print(s_, "engine", e["dm_kg"], "dcg", e["dcg_mm"], "dI", e["dI_pivot_diag_kgm2"], "| fixed", f["dm_kg"], "| all", al["dm_kg"], al["m_v352_kg"])
