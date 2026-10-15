"""Pc port / sense line acoustic period (lead CHANGELOG 194 (2), 203 (2)), v1, 2026-10-13, Mechanical.  DERIVED (lossless 1-D acoustics).
Model: gas column in a chain of uniform segments, chamber end p = 0 (pressure-release: the chamber is the driving source), closed end
at the transducer with a lumped end volume V_end (transducer cavity + seat gap): A_n P'(L) = k^2 V_end P(L); fundamental k from the
transfer of (P, A P') through the segments.  Period T = 2 pi / (k c).  Uniform line limits: x tan x = V_line / V_end (x = kL);
V_end -> 0: quarter wave T = 4 L / c; V_end >> V_line: Helmholtz.  Viscous/thermal losses (Womersley >> 1 at 1 kHz, 70 bar) are neglected:
they damp the overshoot but barely shift the period.  The gas sound speed c is the governing unknown (gas state in the passage at the
FA-1 instant is MISSING from Combustion): bounds 222 m/s (N2O vapour 200 K), 245 (250 K), 268 (300 K), 400 m/s (cooled products ~400 K)."""
import json, math
import numpy as np
from scipy.optimize import brentq

def period(segs, V_end_mm3, c):
    """segs: [(length_mm, diameter_mm)] from the chamber end to the transducer end."""
    def resid(k):
        P, Q = 0.0, 1.0                          # P(0) = 0, Q = A P' (flux) at the chamber end (arbitrary scale)
        for (l, d) in segs:
            A = math.pi * d * d / 4.0
            Pp = Q / A                           # P'
            P, Pp = P * math.cos(k * l) + Pp / k * math.sin(k * l), -P * k * math.sin(k * l) + Pp * math.cos(k * l)
            Q = A * Pp
        return Q - k * k * V_end_mm3 * P
    L = sum(l for l, _ in segs)
    ks = np.linspace(1e-6, 2 * math.pi / L * 1.01, 4000)    # k in 1/mm, up to one wavelength over L
    r = [resid(k) for k in ks]
    for i in range(len(ks) - 1):
        if r[i] * r[i + 1] < 0:
            k = brentq(resid, ks[i], ks[i + 1])
            return 2 * math.pi / (k * 1e3 * c) * 1e3          # ms (k in 1/mm -> 1/m)
    return float("nan")

C = {"N2O_vap_200K": 222.0, "N2O_vap_250K": 245.0, "N2O_vap_300K": 268.0, "products_400K": 400.0}
# v3.5.1 CAD (parts_engine.py, HV69 layout): 1/8-27 NPT seat (tap drill 8.7 x 10) at r 25 / 142 deg on the head top (z 169.513);
# Ø2.0 passage from the seat bottom (z 159.513) to the head metal face (z 105.513, inclined 4.5 mm inward: 54.17 mm), then the Ø3.0 hole in
# the 2 mm TC-10 phenolic disc to the chamber face (z 103.513).
HEAD = [(2.0, 3.0), (54.17, 2.0)]
cases = {
    "CC-1 seat-mounted transducer, V_end = transducer dead volume": HEAD,
}
V_list = [0.0, 10.0, 17.0, 25.0, 36.0, 50.0, 100.0, 210.0, 400.0]
out = {"id": "pc_line_period", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "status": "DERIVED (lossless 1-D acoustics); c and V_end ASSUMED/MISSING",
       "geometry_cad_v3.5.1": {"seat": "1/8-27 NPT, tap drill 8.7 x 10, r 25 / 142 deg, head top z 169.513 (engine frame)",
                               "passage": "Ø2.0 x 54.17 mm (TC-02, seat bottom z 159.513 to the head metal face z 105.513, 4.5 mm radial inclination)",
                               "disc_hole": "Ø3.0 x 2.0 mm (TC-10 phenolic face disc) to the chamber face z 103.513 at r 20.5",
                               "line_volume_mm3": round(sum(math.pi * d * d / 4 * l for l, d in HEAD), 1),
                               "free_envelope_above_seat": "Ø12 x 30 mm clear at neutral (nearest TC-04 1.0 mm, PD-01 2.7 mm); Ø19 x 60 (070BG class) "
                                                           "intersects TC-04, PD-01, PD-02, BL-01 (v351/pc/pc_space_v1.json)"},
       "c_m_s": C, "rows": []}
for V in V_list:
    row = {"case": "CC-1 head passage + seat-mounted transducer", "V_end_mm3": V}
    for kc, c in C.items():
        row[f"T_ms_{kc}"] = round(period(HEAD, V, c), 3)
    out["rows"].append(row)
# max V_end for T <= 1 ms per c
out["V_end_max_mm3_for_T_le_1ms"] = {}
for kc, c in C.items():
    f = lambda V: period(HEAD, V, c) - 1.0
    if f(0.0) > 0:
        out["V_end_max_mm3_for_T_le_1ms"][kc] = "impossible (T(V_end=0) = %.3f ms)" % period(HEAD, 0.0, c)
    else:
        out["V_end_max_mm3_for_T_le_1ms"][kc] = round(brentq(f, 0.0, 2000.0), 1)
# 070BG variants (M3234-000005-070BG, 1/4-18 NPT male; internal port volume MISSING -> ASSUMED 50..300 mm3)
NPT_GAP = 210.0   # 1/8-27 NPT seat: tap drill 8.7 x 10 with ~6.5 mm engagement of a male fitting -> ~3.5 mm x 59.4 mm2 (ASSUMED)
for name, segs, Vt in [
        ("070BG direct at the seat via a 1/8 NPT x 1/4 NPT adapter (does NOT fit: space)", HEAD + [(25.0, 4.0)], [50.0, 150.0, 300.0]),
        ("070BG on an engine bracket, 1/8 in tube ID 1.75 x 100 mm (no location found)", HEAD + [(25.0, 2.0), (100.0, 1.75)], [50.0, 150.0, 300.0]),
        ("070BG on the 0.30 m sense line (lead 2026-10-12 baseline, ID 1.75 ASSUMED)", HEAD + [(25.0, 2.0), (300.0, 1.75)], [50.0, 150.0, 300.0])]:
    for v in Vt:
        row = {"case": name, "V_end_mm3": v + (NPT_GAP if "adapter" in name else 0.0)}
        for kc, c in C.items():
            row[f"T_ms_{kc}"] = round(period(segs, row["V_end_mm3"], c), 3)
        out["rows"].append(row)
# CC-2: shorter passage (deeper seat), passage Ø2 x L
for Lp in (20.0, 30.0, 40.0):
    for V in (0.0, 30.0, 60.0):
        row = {"case": f"CC-2 deeper seat: Ø2.0 x {Lp:.0f} mm passage + disc", "V_end_mm3": V}
        for kc, c in C.items():
            row[f"T_ms_{kc}"] = round(period([(2.0, 3.0), (Lp, 2.0)], V, c), 3)
        out["rows"].append(row)
json.dump(out, open("/home/claude/work/mechanical/v351/pc/pc_line_period_v1.json", "w"), indent=1)
print("line volume", out["geometry_cad_v3.5.1"]["line_volume_mm3"], "mm3")
for r in out["rows"]:
    print(f"{r['case'][:70]:70s} V {r['V_end_mm3']:6.0f}  T(222) {r['T_ms_N2O_vap_200K']:6.3f}  T(245) {r['T_ms_N2O_vap_250K']:6.3f}  T(268) {r['T_ms_N2O_vap_300K']:6.3f}  T(400) {r['T_ms_products_400K']:6.3f}")
print(out["V_end_max_mm3_for_T_le_1ms"])
# sanity: uniform line check vs x tan x
L, d = 54.17, 2.0
Vl = math.pi * d * d / 4 * L
for V in (10.0, 100.0):
    x = brentq(lambda x: x * math.tan(x) - Vl / V, 1e-6, math.pi / 2 - 1e-9)
    print("check uniform", V, round(2 * math.pi * L / (x * 268.0), 4), round(period([(L, d)], V, 268.0), 4))
