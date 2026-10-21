#!/usr/bin/env python3
"""Electronics v2.11, lead ruling 2026-10-20T21:46:49Z item 4 (T-F1 basis rate).

r = the larger of the GVLO and GVHI rev-4 B1 end-of-burn case-TC station rates, read read-only from the R4 hist npz that
04-fea/v352/texts/tf1_exposure_v352_v1.json (d23e72f089cca33a) cites; A1 and rev-3 merged rates for information.
Station = the maximum over the TC-01 OD nodes 12.6-17.6 mm aft of the injector face (bpkg normal_operation_case_TC.station),
the same definition as calc/v2p11/case_tc_channel_v1.py. Rate methods: (m1) backward difference over the last output
interval (the v1 method), (m2) the last 0.5 s output interval before it, (m3) least squares over the outputs in the last 0.65 s.
Mapping (lead item 4): TC-01 maximum at the trip = 150 C + tol_lo(r) + station offset (GVLO 1.43 K / GVHI 1.54 K, bpkg
surrogate_validity); tol_lo(r) = 9.05 + 0.630 r K worst case (lead item 2, case_tc_channel_v1); the A 165 rows hold for
r <= 7.17 K/s (GVLO) and <= 7.00 K/s (GVHI). SIM inputs; CALC / DERIVED; nothing here is physical approval.
Usage: nice -n 15 python3 -I calc/v2p11/tf1_rate_v1.py -> results/tf1_rate_v1.json
"""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path("/home/claude/work/electronics")
OUT = ROOT / "results" / "tf1_rate_v1.json"
HIST = Path("/home/claude/work/mechanical/v352/tb70/hist")
TF1 = Path("/home/claude/work/shared-fallback/engine/04-fea/v352/texts/tf1_exposure_v352_v1.json")
STATION_MM = (12.6, 17.6)
T_END_B1 = 21.651
RUNS = {
    "B1_rev4_GVLO": ("DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_R4_GVLO", T_END_B1),
    "B1_rev4_GVHI": ("DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_R4_GVHI", T_END_B1),
    "B1_rev3_merged": ("DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b", T_END_B1),
    "A1_rev3_merged_burn2_end": ("DC-A1dispp99_tg711_hi_SS316L_L2.5_v352_NF2b", 26.781),
}
OFFSET_K = {"B1_rev4_GVLO": 1.43, "B1_rev4_GVHI": 1.54}       # [MECH bpkg surrogate_validity, lead item 4]
R_LIMIT = {"B1_rev4_GVLO": 7.17, "B1_rev4_GVHI": 7.00}        # [LEAD item 4]


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


def tol_lo(r):
    return 9.05 + 0.630 * r


def main():
    tf1 = json.loads(TF1.read_text())
    out = {"script": "calc/v2p11/tf1_rate_v1.py", "date": "2026-10-20", "status": "CALC / DERIVED on SIM inputs; not physical approval",
           "inputs": {"tf1_exposure_v352_v1.json": {"file": str(TF1), "sha256_16": sha16(TF1)}}, "rates": {}}
    for k, (lab, t_end) in RUNS.items():
        p = HIST / f"{lab}_hist.npz"
        s16 = sha16(p)
        cited = None
        for b, v in tf1["bounds"].items():
            if v["hist"]["path"] == str(p):
                cited = v["hist"]["sha256_16"]
                assert cited == s16, f"{p} sha {s16} != cited {cited}"
        z = np.load(p, allow_pickle=False)
        info = json.loads(str(z["info"]))
        t, X, T = z["t_s"], z["od_X"], z["od_T"] - 273.15
        aft = -(X[:, 1] - info["inj_face_z_mm"])
        sel = np.where((aft >= STATION_MM[0] - 1e-6) & (aft <= STATION_MM[1] + 1e-6))[0]
        sm = T[:, sel].max(axis=1)
        ke = int(np.argmin(abs(t - t_end)))
        m1 = (sm[ke] - sm[ke - 1]) / (t[ke] - t[ke - 1])
        m2 = (sm[ke - 1] - sm[ke - 2]) / (t[ke - 1] - t[ke - 2])
        w = (t >= t[ke] - 0.65 - 1e-9) & (t <= t[ke] + 1e-9)
        m3 = float(np.polyfit(t[w], sm[w], 1)[0])
        row = {"file": str(p), "sha256_16": s16, "cited_by_tf1_exposure": cited is not None, "t_end_s": float(t[ke]),
               "station_nodes_aft_mm": [round(float(a), 2) for a in sorted(aft[sel])], "station_max_end_C": round(float(sm[ke]), 3),
               "rate_K_per_s": {"m1_last_interval": round(float(m1), 3), "m1_interval_s": round(float(t[ke] - t[ke - 1]), 3),
                                "m2_previous_interval": round(float(m2), 3), "m3_lsq_last_0p65s": round(m3, 3)}}
        if k in OFFSET_K:
            rr = max(m1, m2, m3)
            row["lead_item4_check"] = {"r_used_K_per_s": round(float(m1), 3), "r_max_of_methods_K_per_s": round(float(rr), 3),
                                       "tol_lo_K_at_r_used": round(tol_lo(m1), 3),
                                       "TC01_max_at_trip_C_at_r_used": round(150.0 + tol_lo(m1) + OFFSET_K[k], 3),
                                       "TC01_max_at_trip_C_at_r_max_of_methods": round(150.0 + tol_lo(rr) + OFFSET_K[k], 3),
                                       "r_limit_K_per_s": R_LIMIT[k], "inside_A165_rows_at_r_used": bool(m1 <= R_LIMIT[k] + 1e-12),
                                       "inside_A165_rows_all_methods": bool(rr <= R_LIMIT[k] + 1e-12),
                                       "margin_to_limit_K_per_s": round(R_LIMIT[k] - float(m1), 3)}
        out["rates"][k] = row
    g = out["rates"]
    r = max(g["B1_rev4_GVLO"]["rate_K_per_s"]["m1_last_interval"], g["B1_rev4_GVHI"]["rate_K_per_s"]["m1_last_interval"])
    out["T_F1_basis_rate"] = {
        "r_K_per_s": r, "rule": "larger of the GVLO / GVHI rev-4 B1 end-of-burn station rates (lead 21:46:49Z item 4), method m1 (last output "
                                "interval, 0.15 s) as in case_tc_channel_v1",
        "tol_lo_K": round(tol_lo(r), 3), "station_true_at_trip_C": round(150.0 + tol_lo(r), 3),
        "formula": "tol_lo = 9.05 + 0.630 r K (worst case, any rate r; DESIGN install, tau <= 0.25 s, B-TC-1 to verify)",
        "basis_rows": "A 165 (TB_a165, both bounds) if r <= 7.17 K/s (GVLO) and <= 7.00 K/s (GVHI) and tau <= 0.25 s; else A 175",
        "verdict_method_m1_only": "A165" if (g["B1_rev4_GVLO"]["lead_item4_check"]["inside_A165_rows_at_r_used"] and
                                             g["B1_rev4_GVHI"]["lead_item4_check"]["inside_A165_rows_at_r_used"]) else "A175",
    }
    # the stated rate is the largest of the three methods (the m1 margin 0.007 K/s is below what the derivative method resolves)
    r_st = max(max(g[k]["rate_K_per_s"][m] for m in ("m1_last_interval", "m2_previous_interval", "m3_lsq_last_0p65s"))
               for k in ("B1_rev4_GVLO", "B1_rev4_GVHI"))
    lim_ok = all(max(g[k]["rate_K_per_s"][m] for m in ("m1_last_interval", "m2_previous_interval", "m3_lsq_last_0p65s")) <= R_LIMIT[k]
                 for k in ("B1_rev4_GVLO", "B1_rev4_GVHI"))
    out["T_F1_basis_rate"]["stated_r_K_per_s"] = round(r_st, 3)
    out["T_F1_basis_rate"]["stated_r_rule"] = "largest of the three methods over GVLO / GVHI (Electronics 21:49:44Z)"
    out["T_F1_basis_rate"]["verdict"] = "A165" if lim_ok else "A175"
    out["T_F1_basis_rate"]["lead_ruling"] = ("LEAD 2026-10-20T21:51:07Z: A 175 CONFIRMED as the T-F1 exposure basis (r_GVHI 7.03 K/s > 7.00 K/s); "
                                             "A 165 not confirmed (0.004 K margin below the method resolution); re-basing on A 165 possible after "
                                             "a B-TC-1 calibration, before T-F1 is run")
    # calibrated channel (case_tc_channel_v1 after_B_TC_1_calibration: static worst 4.36 K + placement 0.38 + surface steady 1.11
    # + r (tau 0.25 + t_det 0.38) = 5.85 + 0.630 r)
    cal = {}
    for k in ("B1_rev4_GVLO", "B1_rev4_GVHI"):
        rk = max(g[k]["rate_K_per_s"][m] for m in ("m1_last_interval", "m2_previous_interval", "m3_lsq_last_0p65s"))
        tl = 4.36 + 0.38 + 1.11 + 0.630 * rk
        cal[k] = {"r_K_per_s": round(rk, 3), "tol_lo_cal_K": round(tl, 2), "TC01_max_at_trip_C": round(150.0 + tl + OFFSET_K[k], 2),
                  "inside_165_by_K": round(165.0 - (150.0 + tl + OFFSET_K[k]), 2)}
    out["T_F1_basis_rate"]["after_B_TC_1_calibration"] = {
        "formula": "tol_lo_cal = 5.85 + 0.630 r K (static worst 4.36 K after the 150 C coupon calibration + placement 0.38 + surface steady 1.11)",
        "at_7p03_K_per_s_K": round(5.85 + 0.630 * 7.03, 2), "per_bound": cal}
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    for k, v in g.items():
        print(k, v["station_max_end_C"], v["rate_K_per_s"], v.get("lead_item4_check", ""))
    print(out["T_F1_basis_rate"])


if __name__ == "__main__":
    main()
