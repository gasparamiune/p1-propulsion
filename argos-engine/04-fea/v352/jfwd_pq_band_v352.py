"""J-FWD P+Q select-fit band, re-sized ONCE on the final anchors (lead 2026-10-21T05:50:45Z re-map brief R2; R3 / R4 / R8 as cited).
Mechanical, 2026-10-21, v1.  Paper / Python only: no FE run, no ccx.  CALC / DERIVED on SIM inputs, none of it physical approval.

R2 (verbatim essentials): 'the P+Q select-fit band APPLIES (line 240: IN718 [0.040, 0.0761] mm radial, narrower TC-02 spigot OD
tolerance); re-size it once from the v7 grid (MS at 0.040 / 0.059 / 0.070 / 0.078) on the final anchors (SOAK52 370.3 MPa under C1);
lead CALC to confirm or correct: "With the bore at 57.25 H8 (0/+0.046) a [0.040, 0.0684] radial band leaves a spigot OD window of about
0.011 mm unless the spigot is select-fitted to the measured bore"; if no band inside [0.040, 0.0761] closes the seat line it stays a
FOUND NEGATIVE; the band goes on the TC-02 drawing text only after the re-size; no geometry change without asking the lead first.'

Method: relax v8 (jfwd_relax_v352.py cc0db230aaf77ac1, json 51e9eddb9b9e6711; FEA3D-2's FINAL envelope v6 43a5d78b67c615fc and the cD
input record 5a41c8d74897bdda) is imported for its module-level model only (its __main__ block, which writes its json, is not run).  Its
band function is restated here unchanged: per soak state, MS(g) = 2 Fty(T_line) / (PQ_env x F_sh,IN718(g, F_V) / F_sh,A4-80(0.078,
3750)) - 1, with PQ_env the seat-line P+Q of the final anchors (s6 + C1; cD excluded and recorded beside, R3) and T_line the FE
line temperature.  Every grid value of relax v8 is re-computed and asserted equal; the new points (0.0680 / 0.0684 / 0.0685 / 0.0686,
the line-240 edge 0.0761) and g at MS = +0.05 use the same function.  Criterion at the J-F1 cap 3750 N; 4096 N is information.
R4: the seat-line P+Q is NOT shown mesh-converged (s9 -> s6 +12 to +18 %, s6 -> cD -1.5 to -7.3 %, not monotonic); the FE are at the
drawn bound g 0.078, outside the band, so every band MS is the model's scaling of the 0.078 FE [DERIVED], quoted as found with the MF note.
R8: every J-FWD FE except cD is on the interim TC-01 (d10.5 flats); the effect of the final d11.2 part is ASSUMED small.
Usage: jfwd_pq_band_v352.py -> v352/jfwd/jfwd_pq_band_v352_v1.json"""
import hashlib, importlib.util, json, math
from pathlib import Path

J = Path("/home/claude/work/mechanical/v352/jfwd")
P_RELAX, P_RELAXJ, P_ROWS = J / "jfwd_relax_v352.py", J / "jfwd_relax_v352_v8.json", J / "jfwd_in718_rows_v352_v8.json"
OUT = J / "jfwd_pq_band_v352_v1.json"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


assert sha(P_RELAX) == "cc0db230aaf77ac1" and sha(P_RELAXJ) == "51e9eddb9b9e6711" and sha(P_ROWS) == "af072cc2e70711ca"
_sp = importlib.util.spec_from_file_location("jfwd_relax_v8_module", str(P_RELAX))
R = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(R)                      # module level only; __name__ != "__main__", so relax v8 writes nothing
RJ = json.loads(P_RELAXJ.read_text())
ROWS = json.loads(P_ROWS.read_text())
assert RJ["version"] == "v8" and ROWS["version"] == "v8"
BAND = RJ["PQ_select_fit_band_on_envelope_IN718"]
lines_T = {st: R._env["states"][st]["lines"]["d+6.051_z+0.0"]["T_mean_C"] for st in R.SOAKS}


def pq_ms(st, fam, kb, g, FV):                 # relax v8 lines 712-717, unchanged
    env_pq = R.PQ_SEAT[st] if fam == "seat" else R.PQ_RING[st]
    f0 = R.model_state(st, kb, R.A4_80, R.FV0, R.G0)[3]
    f1 = R.model_state(st, kb, R.IN718_S, FV, g)[3]
    return 2.0 * float(R.tab("AL6061-T6", "Fty", lines_T[st])) / (env_pq * f1 / f0) - 1.0


def g_at(st, fam, kb, FV, target):
    lo, hi = 0.0, 0.2
    assert pq_ms(st, fam, kb, lo, FV) >= target > pq_ms(st, fam, kb, hi, FV)
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if pq_ms(st, fam, kb, mid, FV) >= target else (lo, mid)
    return lo


GRID = (0.040, 0.059, 0.070, 0.078)
NEW = (0.0631, 0.0680, 0.0684, 0.0685, 0.0686, 0.0761)
per, n_chk = {}, 0
for e, kb in R.KB.items():
    for fam in ("seat", "ring"):
        for FV in (3750.0, 4096.0):
            key = f"{e}|{fam}|{FV:.0f}"
            ref = BAND[key]
            blk = {}
            for st in R.SOAKS:
                for g in GRID:                  # the relax v8 grid, re-computed and asserted
                    assert round(pq_ms(st, fam, kb, g, FV), 4) == ref["per_state"][st]["MS_at_gap"][f"{g:g}"], (key, st, g)
                    n_chk += 1
                gz = g_at(st, fam, kb, FV, 0.0)
                assert round(gz, 5) == ref["per_state"][st]["g_at_MS0_mm"], (key, st, gz)
                blk[st] = {"PQ_env_MPa": ref["per_state"][st]["PQ_env_MPa"], "T_line_C": lines_T[st],
                           "Fty_AL6061-T6_at_T_line_MPa": round(float(R.tab("AL6061-T6", "Fty", lines_T[st])), 2),
                           "MS_at_gap_relax_v8_grid": ref["per_state"][st]["MS_at_gap"],
                           "MS_at_gap_new_points": {f"{g:g}": round(pq_ms(st, fam, kb, g, FV), 4) for g in NEW},
                           "g_at_MS0_mm": round(gz, 5), "g_at_MS_+0.05_mm": round(g_at(st, fam, kb, FV, 0.05), 5)}
            gov = min(blk, key=lambda s: blk[s]["g_at_MS0_mm"])
            assert round(blk[gov]["g_at_MS0_mm"], 5) == ref["g_max_mm"]
            per[key] = {"g_max_at_MS0_mm": ref["g_max_mm"], "governing_state": gov,
                        "g_max_at_MS_+0.05_mm": min(v["g_at_MS_+0.05_mm"] for v in blk.values()), "per_state": blk}
assert n_chk == 2 * 2 * 2 * 3 * 4
for e in R.KB:                                 # the ring family is on the seat line (RING_ON_SEAT): identical, as in relax v8
    for FV in ("3750", "4096"):
        assert per[f"{e}|seat|{FV}"]["per_state"] == per[f"{e}|ring|{FV}"]["per_state"]

# ---- the band (criterion at 3750 N, the J-F1 cap; both k_b ends; the seat family governs = the ring family)
g0_3750 = min(per[f"{e}|seat|3750"]["g_max_at_MS0_mm"] for e in R.KB)
g0_4096 = min(per[f"{e}|seat|4096"]["g_max_at_MS0_mm"] for e in R.KB)
g05_3750 = min(per[f"{e}|seat|3750"]["g_max_at_MS_+0.05_mm"] for e in R.KB)
G_UP = math.floor(g0_3750 * 1e4) / 1e4          # 4 decimals, rounded down
G_LO = 0.040                                    # line 240 lower edge = the drawn f7 minimum (no new interference)
assert (round(g0_3750, 5), round(g0_4096, 5), G_UP) == (0.06862, 0.0684, 0.0686), (g0_3750, g0_4096, G_UP)


def ms_min(g, FV):
    return min(pq_ms(st, "seat", kb, g, FV) for kb in R.KB.values() for st in R.SOAKS)


def gov_at(g, FV):
    c = [(pq_ms(st, "seat", kb, g, FV), st, e) for e, kb in R.KB.items() for st in R.SOAKS]
    m = min(c)
    return {"MS": round(m[0], 4), "state": m[1], "k_b_end": m[2]}


L240 = 0.0761
ms_l240 = gov_at(L240, 3750.0)
assert ms_l240["MS"] < 0.0                     # the line-240 band as drawn does NOT close the seat line
ms_up = gov_at(G_UP, 3750.0)
assert ms_up["MS"] >= 0.0

# ---- fit arithmetic (bore 57.25 H8 = 57.250 / 57.296; plug drawn 57.20 f7 = 57.140 / 57.170; radial gap g = (D - d) / 2)
D_MIN, D_MAX = 57.250, 57.296
d_f7 = (57.140, 57.170)
g_f7 = (round((D_MIN - d_f7[1]) / 2, 4), round((D_MAX - d_f7[0]) / 2, 4))
assert g_f7 == (0.04, 0.078)


def od_window(g_lo, g_hi):
    d_max, d_min = D_MIN - 2 * g_lo, D_MAX - 2 * g_hi
    return {"band_mm_radial": [g_lo, g_hi], "plug_OD_max_mm": round(d_max, 4), "plug_OD_min_mm": round(d_min, 4),
            "OD_window_mm": round(d_max - d_min, 4), "formula": "window = 2 (g_hi - g_lo) - 0.046 (H8 bore tolerance)"}


win_band, win_lead, win_flag, win_240 = od_window(G_LO, G_UP), od_window(G_LO, 0.0684), od_window(G_LO, round(g05_3750, 4)), od_window(G_LO, L240)
assert win_band["OD_window_mm"] == 0.0112 and win_lead["OD_window_mm"] == 0.0108
DRAWN = {}
for lab, dmin in (("57.20 -0.030/-0.041 (57.159-57.170)", 57.159), ("57.20 -0.030/-0.040 (57.160-57.170)", 57.160)):
    gmax = round((D_MAX - dmin) / 2, 5)
    DRAWN[lab] = {"g_radial_mm": [0.04, gmax], "OD_window_mm": round(57.170 - dmin, 3),
                  "MS_min_3750_criterion": gov_at(gmax, 3750.0), "MS_min_4096_info": gov_at(gmax, 4096.0),
                  "flag_0.05": gov_at(gmax, 3750.0)["MS"] < 0.05}
SELECT = {"rule": ("select fit: the TC-02 plug OD is ground to the MEASURED TC-01 bore D_meas: OD = D_meas - 2 g with g in the band, i.e. "
                   f"D_meas - {2 * G_UP:.4f} <= OD <= D_meas - {2 * G_LO:.3f} (window {2 * (G_UP - G_LO):.4f} mm on the diameter), less twice "
                   "the combined measurement uncertainty of bore and OD at each end (TO-DEFINE by the shop; the bore and OD are measured at "
                   "20 +/- 1 C, at the seat line and the two lands, and recorded with the part serials)"),
          "window_on_diameter_mm": round(2 * (G_UP - G_LO), 4),
          "flag_free_variant": (f"for MS >= +0.05 (no 0.05 flag) g <= {g05_3750:.4f} mm: D_meas - {2 * g05_3750:.4f} <= OD <= D_meas - 0.080 "
                                f"(window {2 * (g05_3750 - G_LO):.4f} mm); a drawn-tolerance version of it leaves {win_flag['OD_window_mm']:.4f} mm, "
                                "not drawable")}

# ---- information only: the stand T0 rule (CHANGELOG 249 (2): stand ambient <= 24 C; the FE fields are at T0 20 C, no hot-day FE run).
# ASSUMED: the seat-line temperature shifts 1:1 with T0 (+4 K) and the FE P+Q is unchanged; only Fty(T_line) moves.  Not a criterion.
DT0 = 4.0


def pq_ms_T(st, kb, g, FV, dT):
    f0 = R.model_state(st, kb, R.A4_80, R.FV0, R.G0)[3]
    f1 = R.model_state(st, kb, R.IN718_S, FV, g)[3]
    return 2.0 * float(R.tab("AL6061-T6", "Fty", lines_T[st] + dT)) / (R.PQ_SEAT[st] * f1 / f0) - 1.0


T0I = {}
for st in R.SOAKS:
    kb = R.KB["hi"]
    lo, hi = 0.0, 0.2
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if pq_ms_T(st, kb, mid, 3750.0, DT0) >= 0.0 else (lo, mid)
    T0I[st] = {"Fty_at_T_line_MPa": round(float(R.tab("AL6061-T6", "Fty", lines_T[st])), 2),
               "Fty_at_T_line_+4K_MPa": round(float(R.tab("AL6061-T6", "Fty", lines_T[st] + DT0)), 2),
               "MS_at_band_edge_+4K": round(pq_ms_T(st, kb, G_UP, 3750.0, DT0), 4), "g_at_MS0_+4K_mm": round(lo, 5)}
T0_INFO = {"label": ("INFORMATION (stand T0 rule 249 (2), ambient <= 24 C; FE at T0 20 C): ASSUMED uniform +4 K on the seat-line "
                     "temperature with the FE P+Q unchanged, k_b hi, 3750 N; not a criterion, not a hot-day FE run"),
           "per_state": T0I, "g_at_MS0_+4K_min_mm": min(v["g_at_MS0_+4K_mm"] for v in T0I.values()),
           "MS_at_band_edge_+4K_min": min(v["MS_at_band_edge_+4K"] for v in T0I.values())}

res = {
    "id": "jfwd_pq_band_v352", "version": "v1", "date": "2026-10-21", "owner": "mechanical", "basis": __doc__.strip(),
    "inputs": {"relax_v8_script": {"path": str(P_RELAX), "sha256_16": sha(P_RELAX)},
               "relax_v8_json": {"path": str(P_RELAXJ), "sha256_16": sha(P_RELAXJ)},
               "rows_v8_json": {"path": str(P_ROWS), "sha256_16": sha(P_ROWS)},
               "envelope_v6_sha256_16": "43a5d78b67c615fc", "v7inputs_cD_sha256_16": "5a41c8d74897bdda", "meshcorr_sha256_16": "adac16afd42ef7bd"},
    "anchors_R3": {st: {"PQ_env_MPa": per["hi|seat|3750"]["per_state"][st]["PQ_env_MPa"],
                        "from": RJ["history_envelope"][st]["seat_line_PmPb_from"], "T_line_C": lines_T[st],
                        "rows_v8_MS_at_0.078_3750": ROWS["states"][st]["rows"]["3750"]["seat_line_d6p051_z0_PQ"]["MS_PQ_2Fty"],
                        "rows_v8_from": ROWS["states"][st]["rows"]["3750"]["seat_line_d6p051_z0_PQ"]["from"]} for st in R.SOAKS},
    "grid_check": f"{n_chk} relax v8 grid values re-computed and equal; g at MS 0 equal in all 24 state cases",
    "per_key": per,
    "RESULT": {
        "band_mm_radial": [G_LO, G_UP],
        "band_upper_edge_basis": (f"g at MS 0 at 3750 N = {g0_3750:.5f} mm (both k_b ends, governing {per['hi|seat|3750']['governing_state']} "
                                  f"{per['hi|seat|3750']['per_state'][per['hi|seat|3750']['governing_state']]['PQ_env_MPa']} MPa from "
                                  f"{RJ['history_envelope'][per['hi|seat|3750']['governing_state']]['seat_line_PmPb_from']}, k_b hi), rounded down"),
        "governs": ("SOAK ((b2) rep, s6 as solved, 366.8 MPa at T_line 158.0 C) sets the edge, not SOAK52 (370.3 MPa under C1 at 152.7 C: "
                    f"g at MS 0 {per['hi|seat|3750']['per_state']['SOAK52']['g_at_MS0_mm']:.5f} mm); the edge is the v7 value, unchanged by "
                    "the final anchors"),
        "MS_min_at_band_edge_3750": ms_up, "flag": "within the 0.05 flag (MS +0.000 at the edge): quoted FLAG, not a margin",
        "g_at_MS0_4096_info_mm": round(g0_4096, 5),
        "g_for_MS_+0.05_3750_mm": round(g05_3750, 5),
        "line_240_band_[0.040,0.0761]": {"MS_min_at_0.0761_3750": ms_l240,
                                          "verdict": "the line-240 band does NOT close the seat line at its upper edge (FOUND NEGATIVE as drawn there); a band inside it does"},
        "closes_seat_line": True,
        "lead_CALC_check": {"quoted": "With the bore at 57.25 H8 (0/+0.046) a [0.040, 0.0684] radial band leaves a spigot OD window of about 0.011 mm unless the spigot is select-fitted to the measured bore",
                            "computed_[0.040,0.0684]_window_mm": win_lead["OD_window_mm"],
                            "computed_[0.040,0.0686]_window_mm": win_band["OD_window_mm"],
                            "verdict": "CONFIRMED (0.0108 mm at 0.0684, the 4096 N information edge; 0.0112 mm at 0.0686, the 3750 N criterion edge)"},
        "fit_windows": {"drawn_f7_now": {"plug_OD_mm": list(d_f7), "g_radial_mm": list(g_f7), "seat_line_MS_min_3750": gov_at(0.078, 3750.0)},
                        "band": win_band, "lead_0.0684": win_lead, "flag_free_MS_0.05": win_flag, "line_240": win_240},
        "drawn_options": DRAWN,
        "select_fit": SELECT,
        "what_it_acts_on": ("the TC-01 seat-line P+Q rows only (seat d+6.051 z'0 and the ring family on it); the screw rows, the LCF and the "
                            "other J-FWD rows take no credit from the band (they stay at the FE gap 0.078)"),
        "MF_note_R4": ("seat-line P+Q NOT shown mesh-converged: s9 -> s6 +12 to +18 %, s6 -> cD -1.5 to -7.3 %, not monotonic; the band MS are "
                       "the relax v8 model's scaling of the FE at g 0.078 (outside the band) [DERIVED]; extrapolations are information only"),
        "cad_basis_R8": RJ["cad_basis_R8"],
        "stand_T0_24C_info": T0_INFO,
        "drawing_text_status": ("goes on the TC-02 drawing text (03-cad/v3.5.2/texts) after this re-size, per R2; the TC-02 STEP is unchanged "
                                "(no geometry change); the parts / BOM strings 'plug 57.20 f7' change only on the lead's word"),
    },
}
s = json.dumps(res, indent=1)
OUT.write_text(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
print("band", [G_LO, G_UP], "| 3750 g0", round(g0_3750, 5), "| 4096 g0", round(g0_4096, 5), "| g(MS 0.05)", round(g05_3750, 5))
print("edge", ms_up, "| line 240", ms_l240)
print("windows band / lead / flag-free / 240:", win_band["OD_window_mm"], win_lead["OD_window_mm"], win_flag["OD_window_mm"], win_240["OD_window_mm"])
for k, v in DRAWN.items():
    print("drawn", k, v)
print("select", SELECT["window_on_diameter_mm"], "|", SELECT["flag_free_variant"])
print("T0 +4 K info", T0_INFO["g_at_MS0_+4K_min_mm"], T0_INFO["MS_at_band_edge_+4K_min"], T0I)
for st in R.SOAKS:
    x = per["hi|seat|3750"]["per_state"][st]
    print(st, x["PQ_env_MPa"], x["T_line_C"], x["MS_at_gap_relax_v8_grid"], x["MS_at_gap_new_points"], x["g_at_MS0_mm"], x["g_at_MS_+0.05_mm"])
