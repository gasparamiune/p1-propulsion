"""REV-GNC-5 v10 compare (reviewer's own code): (i) the reviewer's re-flown v2.12 bit-check stream (staged v2.12 tree,
staged m2_bitcheck_v212 v1.1 'fly' part) against the author's staged bc_v212.npz, every array; (ii) the reviewer's v2.12
stream against the author's staged v2.11 stream (bc_v211.npz) on the common result names and record columns, i.e. an
independent re-run of Part A (options off = identical) on the v2.12 side (the v2.11 tree is not staged, so its stream is
the author's).  SIM streams; identical numbers show only that the computation repeats.
Usage: python -I v10_bc_compare.py <mine.npz> <staged_v212.npz> <staged_v211.npz> <out.json>"""
import json, sys, hashlib
import numpy as np
mine, s212, s211, pout = sys.argv[1:5]
A = np.load(mine, allow_pickle=False); B = np.load(s212, allow_pickle=False); C = np.load(s211, allow_pickle=False)
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
rep = dict(script="v10_bc_compare (REV-GNC-5)", files=dict(mine=sha(mine), staged_v212=sha(s212), staged_v211=sha(s211)),
           mine_sim=str(A["sim"]), mine_sim6=str(A["sim6_sha16"]), mine_run6=str(A["run6_sha16"]),
           staged212_sim6=str(B["sim6_sha16"]), staged211_sim6=str(C["sim6_sha16"]), vs_staged_v212={}, vs_staged_v211={})
# (i) every array
ka, kb = set(A.files), set(B.files)
rep["vs_staged_v212"]["keys_only_mine"] = sorted(ka - kb); rep["vs_staged_v212"]["keys_only_staged"] = sorted(kb - ka)
diff = []
for k in sorted(ka & kb):
    x, y = A[k], B[k]
    if x.dtype.kind in "fc":
        same = x.shape == y.shape and np.array_equal(x, y, equal_nan=True)
    else:
        same = x.shape == y.shape and bool(np.all(x == y))
    if not same:
        diff.append(k)
rep["vs_staged_v212"]["arrays_compared"] = len(ka & kb); rep["vs_staged_v212"]["arrays_differing"] = diff
rep["vs_staged_v212"]["all_identical"] = not diff and not (ka ^ kb)
# (ii) common columns against v2.11
ra, rc = list(A["res_names"]), list(C["res_names"]); ca, cc = list(A["rec_names"]), list(C["rec_names"])
cr = [k for k in rc if k in ra]; ccol = [k for k in cc if k in ca]
ia = [ra.index(k) for k in cr]; ic = [rc.index(k) for k in cr]
ja = [ca.index(k) for k in ccol]; jc = [cc.index(k) for k in ccol]
cases = sorted({k.split("|")[0] for k in C.files if "|" in k})
allid = True; per = {}
for nm in cases:
    if f"{nm}|res" not in A.files:
        per[nm] = "missing in mine"; allid = False; continue
    X = A[f"{nm}|res"][:, ia]; Y = C[f"{nm}|res"][:, ic]
    rid = X.shape == Y.shape and np.array_equal(X, Y, equal_nan=True)
    nrec = 0; recid = []
    while f"{nm}|rec{nrec}" in C.files and f"{nm}|rec{nrec}" in A.files:
        P = A[f"{nm}|rec{nrec}"]; Q = C[f"{nm}|rec{nrec}"]
        recid.append(bool(P.shape[0] == Q.shape[0] and np.array_equal(P[:, ja], Q[:, jc], equal_nan=True)))
        nrec += 1
    per[nm] = dict(runs=int(Y.shape[0]), results_identical=bool(rid), records_identical=recid)
    allid = allid and rid and all(recid)
rep["vs_staged_v211"] = dict(common_results=len(cr), new_results_in_v212=[k for k in ra if k not in rc], common_record_columns=len(ccol),
                             new_record_columns_in_v212=[k for k in ca if k not in cc], cases=per, all_identical=bool(allid))
json.dump(rep, open(pout, "w"), indent=1)
print(json.dumps(dict(files=rep["files"], mine_sim6=rep["mine_sim6"], staged212_sim6=rep["staged212_sim6"], staged211_sim6=rep["staged211_sim6"])))
print("vs staged v2.12:", rep["vs_staged_v212"]["arrays_compared"], "arrays; differing", rep["vs_staged_v212"]["arrays_differing"][:10],
      "only mine", rep["vs_staged_v212"]["keys_only_mine"][:5], "only staged", rep["vs_staged_v212"]["keys_only_staged"][:5],
      "ALL IDENTICAL" if rep["vs_staged_v212"]["all_identical"] else "DIFFERENCES")
v = rep["vs_staged_v211"]
print("vs staged v2.11 (common columns):", v["common_results"], "results,", v["common_record_columns"], "record columns; new in v2.12", v["new_results_in_v212"], v["new_record_columns_in_v212"])
for nm, d in v["cases"].items():
    print("  ", nm, d)
print("ALL IDENTICAL" if v["all_identical"] else "DIFFERENCES FOUND")
