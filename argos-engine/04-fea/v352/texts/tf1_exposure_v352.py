"""T-F1 exposure basis RESTATED (lead 2026-10-21T05:50:45Z R9; CHANGELOG 249 (3)): the T-F1 exposure basis is the A 175 rows (TB;
FEA3D's tb352g GVLO / tb352h GVHI; both gap-conductance bounds; they cover a TC-01 rise rate r <= about 22.8 K/s), with the A 150 rows
beside them as the reading-equals-truth case.  A stays 150 C (249 (1) ACCEPTED).  Re-basing to A 165 is possible only after B-TC-1
calibrates (tol_lo 10.28 K, TC-01 max 161.82 C), by the lead.  Mechanical, 2026-10-21, v2 (v1 77539a6c62cc66e3 / json d23e72f089cca33a
kept as tf1_exposure_v352_v1.py, the computing script).  Reads only: the numbers are v1's, unchanged [SIM CalculiX thermal; the TB state
and the shifted histories are the ASSUMED sax.py surrogate as tagged in v1]; this version restates which rows are the basis.
Usage: tf1_exposure_v352.py -> v352/texts/tf1_exposure_v352_v2.json"""
import json, hashlib
from pathlib import Path

T = Path("/home/claude/work/mechanical/v352/texts")
V1 = T / "tf1_exposure_v352_v1.json"
OUT = T / "tf1_exposure_v352_v2.json"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]   # noqa: E731
assert sha(V1) == "d23e72f089cca33a"
v1 = json.loads(V1.read_text())
B = v1["bounds"]


def row(bd, stn):
    x = B[bd]["TB_surrogate_per_abort"][stn]
    o = {"abort_C": x["abort_C"], "shift_K": x["shift_K"], "run_json": x["run_json"]}
    for p in ("ENG-TC-01", "ENG-TC-02", "ENG-TC-03"):
        o[p] = {"TB_state_field_max_C": x[p]["TB_state_field_max_C"], "shifted_history_ASSUMED": x[p]["shifted_history_ASSUMED"]}
    return o


basis = {bd: row(bd, "TB") for bd in ("GVLO", "GVHI")}
beside = {bd: row(bd, "TB_a150") for bd in ("GVLO", "GVHI")}
a165 = {bd: row(bd, "TB_a165") for bd in ("GVLO", "GVHI")}
# the ruling's numbers (CHANGELOG 249 (3)) are these rows
q = lambda bd, p, k: basis[bd][p]["shifted_history_ASSUMED"][k]   # noqa: E731
assert (basis["GVLO"]["ENG-TC-02"]["TB_state_field_max_C"], q("GVLO", "ENG-TC-02", "t_above_150C_s"), q("GVLO", "ENG-TC-01", "max_C"),
        q("GVLO", "ENG-TC-01", "t_above_150C_s")) == (248.4, 1192.0, 257.1, 1435.8)
assert (basis["GVHI"]["ENG-TC-02"]["TB_state_field_max_C"], q("GVHI", "ENG-TC-02", "t_above_150C_s"), q("GVHI", "ENG-TC-01", "max_C")) == (233.0, 929.7, 243.4)
assert basis["GVLO"]["abort_C"] == 175.0 and beside["GVLO"]["abort_C"] == 150.0 and a165["GVLO"]["abort_C"] == 165.0
out = {"id": "tf1_exposure_v352", "version": "v2", "date": "2026-10-21", "owner": "mechanical", "basis": __doc__.strip(),
       "inputs": {"tf1_exposure_v1": {"path": str(V1), "sha256_16": sha(V1)}},
       "T-F1_exposure_basis_R9": {
           "rule": ("lead 2026-10-21T05:50:45Z R9: restate tf1_exposure_v352 (d23e72f089cca33a) and the T-F1 founder text on the A 175 rows (TB, "
                    "tb352g / h, both bounds), with the A 150 rows beside; re-basing to A 165 is possible only after B-TC-1, by the lead. "
                    "CHANGELOG 249 (3): T-F1 EXPOSURE BASIS on the A 175 rows (they cover r <= about 22.8 K/s); (a)-(c) PASS on both bounds "
                    "(lowest TC-02 TBS +0.409 / +0.745); (d) OPEN (T-F1); the A 150 rows go beside them as the reading-equals-truth case; A stays 150 C"),
           "basis_A175_TB_both_bounds": basis,
           "beside_A150_reading_equals_truth": beside,
           "A165_rebase_condition": {"rule": "only after B-TC-1 calibrates (tol_lo 10.28 K, TC-01 max 161.82 C), by the lead (249 (3))",
                                     "rows_record": a165},
           "criteria_status": {"a_to_c": "PASS on both bounds (lowest TC-02 TBS +0.409 / +0.745; lead, CHANGELOG 249 (3))",
                               "d": "OPEN (T-F1): no sourced short-time exposure allowable; the cells use the engmat 10,000 h basis"},
           "abort_value": "A = 150 C (CHANGELOG 249 (1) ACCEPTED)",
           "closed_abort_search_record": "the A 135 / 120 / 105 rows stay in 'bounds' as the record of the closed abort search"},
       "bounds": B}
s = json.dumps(out, indent=1)
OUT.write_text(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
