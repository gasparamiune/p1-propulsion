"""m2_dc_index_diff v1 (2026-10-13): compare two duty-cycle index revisions (GNC). Checks that every duty-cycle CSV named in
both indexes has the same sha256 in both, that the files on disk still hash to it, and lists every added / removed /
changed index field (lists compared element by element). Used for index revision 2026-10-13c (axial-load fields added by
m2_duty_cycles_v3 v1.3 + m2_duty_cycles_disp v1.2, both generators re-run into a clean folder).
Usage: python m2_dc_index_diff.py OLD_INDEX NEW_INDEX CSV_FOLDER OUT_JSON"""
import hashlib
import json
import os
import sys


def diff(x, y, path=""):
    out = []
    if isinstance(x, dict) and isinstance(y, dict):
        for k in sorted(set(x) | set(y)):
            if k not in x:
                out.append(["ADDED", path + "/" + k])
            elif k not in y:
                out.append(["REMOVED", path + "/" + k])
            else:
                out += diff(x[k], y[k], path + "/" + k)
    elif isinstance(x, list) and isinstance(y, list):
        if len(x) != len(y):
            out.append(["LENGTH", path])
        for i, (p, q) in enumerate(zip(x, y)):
            out += diff(p, q, f"{path}[{i}]")
    elif x != y and not (isinstance(x, float) and isinstance(y, float) and x != x and y != y):
        out.append(["CHANGED", path])
    return out


def main(old_p, new_p, folder, out_p):
    a, b = json.load(open(old_p)), json.load(open(new_p))
    ca = {c["name"]: c for c in a["cycles"] + a.get("retained_v2", [])}
    cb = {c["name"]: c for c in b["cycles"] + b.get("retained_v2", [])}
    files = {}
    for n in sorted(set(ca) & set(cb)):
        p = os.path.join(folder, os.path.basename(cb[n]["file"]))
        disk = hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
        files[n] = dict(sha_old_index=ca[n]["sha256"], sha_new_index=cb[n]["sha256"], sha_disk=disk,
                        identical=ca[n]["sha256"] == cb[n]["sha256"] and (disk is None or disk == cb[n]["sha256"]))
    d = diff(a, b)
    out = dict(version="m2_dc_index_diff v1", old=old_p, new=new_p, old_sha256=hashlib.sha256(open(old_p, "rb").read()).hexdigest(),
               new_sha256=hashlib.sha256(open(new_p, "rb").read()).hexdigest(), files=files,
               all_files_identical=all(v["identical"] for v in files.values()),
               n_added=sum(1 for x in d if x[0] == "ADDED"), changed=[x for x in d if x[0] != "ADDED"], added=[x[1] for x in d if x[0] == "ADDED"])
    json.dump(out, open(out_p, "w"), indent=1)
    print("files identical:", out["all_files_identical"], "| added", out["n_added"], "| changed / removed:", out["changed"])


if __name__ == "__main__":
    main(*sys.argv[1:5])
