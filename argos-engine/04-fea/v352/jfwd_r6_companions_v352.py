"""R6 companions (information): the J-FWD FA1S rows that sit beside the HW-101 Eq. 22 criterion row, restated on the R6 basis
(lead 2026-10-21T05:50:45Z R6: 'HW-101 Eq. 22 at max(CALC, FE) per resultant: V 4079.2 N (FE, (b1) FA1S) and M 4354.7 N mm (CALC);
hole bearing stays on the CALC row (+0.005 / +0.239)').  Mechanical, 2026-10-21, v1.  CALC on SIM inputs; information only, no criterion
row changes here (the Eq. 22 criterion row is rows v8 FA1S_screw_5020A_eq22.governing_omitted).
  (1) Eq. 22 at arm +0.4 mm (sensitivity): rows v8 carries fix v2's CALC row (V 3888.1, arm 1.32, M 5132.2: +0.165 / included -0.035);
      on the R6 basis V = max(3888.1, FE 4079.2), M = max(CALC 5132.2, FE 4269.8).
  (2) TC-02 tapped-thread bearing (231 (1)(ii)) on FEA3D's d x L_e basis: rows v8 FA1S_tap_bearing at V 3888.1; here at V 4079.2.
  (3) the R6 criterion row reproduced (rows v8 eq22_ms, the same allowables), as the check of this script.
Usage: jfwd_r6_companions_v352.py -> v352/jfwd/jfwd_r6_companions_v352_v1.json"""
import hashlib, json
from pathlib import Path

J = Path("/home/claude/work/mechanical/v352/jfwd")
FIX = Path("/home/claude/work/shared-fallback/engine/04-fea/v352/jfwd_fix_v352_v2.json")
ROWS = J / "jfwd_in718_rows_v352_v8.json"
OUT = J / "jfwd_r6_companions_v352_v1.json"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


assert sha(FIX) == "760d6c6f2d7d46d5" and sha(ROWS) == "af072cc2e70711ca"
sc = json.loads(FIX.read_text())["options"]["IN718 M5 x10"]["screw_FA1S_5020A"]
R8 = json.loads(ROWS.read_text())
E8, TB8 = R8["FA1S_screw_5020A_eq22"], R8["FA1S_tap_bearing"]
PSA, PTA, FTU, Z3F, NINC = sc["Psu_allow_N"], sc["Ptu_allow_N"], sc["Ftu_45.6C_MPa"], sc["Z_3_mm3"], sc["N_included_N"]


def eq22_ms(V, M, N):                          # rows v8 (jfwd_in718_rows_v352.py lines 959-965), unchanged
    f = lambda l: (l * V / PSA) ** 1.2 + (N / PTA + l * M / Z3F / FTU) ** 2     # noqa: E731
    lo, hi = 0.0, 5.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if f(mid) < 1.0 else (lo, mid)
    return round(f(1.0), 3), round(0.5 * (lo + hi) - 1.0, 3)


R6 = E8["R6_basis"]
V6, M6 = R6["V_N"], R6["M_Nmm"]
assert (V6, M6) == (4079.2, 4354.6)
assert eq22_ms(V6, M6, 0.0) == (R6["interaction_omitted"], E8["governing_omitted"]) == (0.678, 0.278)       # (3)
assert eq22_ms(V6, M6, NINC)[1] == E8["included"] == 0.065
r4 = sc["rows"]["CALC_abs_3888.1|arm_+0.4_sens"]
assert eq22_ms(r4["V_N"], r4["M_Nmm"], 0.0) == (r4["interaction_omitted"], r4["MS_omitted_governing"]) == (0.777, 0.165)
assert {k: r4[k] for k in ("MS_omitted_governing", "MS_included_info")} == E8["arm_+0.4_sens"]
M4 = max(r4["M_Nmm"], R6["FE_values"]["M_max_Nmm"])
i4, m4 = eq22_ms(V6, M4, 0.0)
i4i, m4i = eq22_ms(V6, M4, NINC)
c = TB8["CALC_3888.1"]
fby, fbu = (1 + c["MS_y"]) * c["sigma_MPa"], (1 + c["MS_u"]) * c["sigma_MPa"]
sig6 = c["sigma_MPa"] * V6 / c["V_N"]
res = {"id": "jfwd_r6_companions_v352", "version": "v1", "date": "2026-10-21", "owner": "mechanical", "basis": __doc__.strip(),
       "inputs": {"fix_v2": {"path": str(FIX), "sha256_16": sha(FIX)}, "rows_v8": {"path": str(ROWS), "sha256_16": sha(ROWS)}},
       "check_R6_criterion_row_reproduced": {"V_N": V6, "M_Nmm": M6, "interaction": 0.678, "MS_omitted": 0.278, "MS_included_info": 0.065},
       "eq22_arm_+0.4_sens_R6_basis_INFO": {"arm_mm": r4["arm_mm"], "V_N": V6, "V_from": R6["V_from"], "M_Nmm": M4,
                                             "M_from": "CALC 3888.1 x arm 1.32 (fix v2 row; above the FE (b1) 4269.8)",
                                             "interaction_omitted": i4, "MS_omitted": m4, "interaction_included_info": i4i, "MS_included_info": m4i,
                                             "fix_v2_basis_record": {"V_N": r4["V_N"], "MS_omitted": r4["MS_omitted_governing"], "MS_included_info": r4["MS_included_info"]}},
       "TC02_tap_bearing_at_R6_V_INFO": {"V_N": V6, "sigma_MPa": round(sig6, 1), "MS_y": round(fby / sig6 - 1, 3), "MS_u": round(fbu / sig6 - 1, 3),
                                         "basis": "rows v8 FA1S_tap_bearing (FEA3D's d x L_e, allowables back-computed) scaled to V 4079.2",
                                         "CALC_3888.1_record": {"MS_y": c["MS_y"], "MS_u": c["MS_u"]}},
       "tag": "CALC on SIM (FE (b1) V) and fix v2 allowables; INFORMATION, not criterion rows"}
s = json.dumps(res, indent=1)
OUT.write_text(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
print("arm +0.4 R6:", i4, m4, "| included", i4i, m4i, "| tap bearing at V6:", res["TC02_tap_bearing_at_R6_V_INFO"])
