"""m2_v3_rebuild_check v1 (GNC, 2026-10-13): REV-GNC-1 RG-20 builder defect. Rebuild gnc.json v3 with m2_gnc_json_v3 v5.1 (FC_THRUST
read removed) into a scratch file and compare it field by field with the published interfaces/gnc.json v3 (sha256/16
3e97c378cfebee95). Run the builder first:
  GNC_GJ3_DEST=<out>/gnc_v3_rebuild.json python scripts/m2_gnc_json_v3.py
Output: <out>/rebuild_check_v1.json (every differing path with both values, classified)."""
import hashlib
import json
import os
import sys

OUT = os.environ.get("GNC_RB3_OUT", "/home/claude/work/space/out/gnc_json/rebuild_v3_check")
PUB = os.environ.get("GNC_V3_PUB", "/home/claude/work/shared-fallback/engine/interfaces/gnc.json")
REB = os.path.join(OUT, "gnc_v3_rebuild.json")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


SIMV_NOW = "v2.8-dev (2026-10-13, amendments M, W)"
SIMV_V3 = "v2.7.1-dev (2026-10-13)"


def diff(x, y, p, out):
    if type(x) != type(y):
        out.append(dict(path=p, kind="type", rebuild=str(x)[:400], published=str(y)[:400]))
    elif isinstance(x, dict):
        for k in sorted(set(x) | set(y)):
            if k not in x:
                out.append(dict(path=f"{p}/{k}", kind="only_published", published=str(y[k])[:400]))
            elif k not in y:
                out.append(dict(path=f"{p}/{k}", kind="only_rebuild", rebuild=str(x[k])[:400]))
            else:
                diff(x[k], y[k], f"{p}/{k}", out)
    elif isinstance(x, list):
        if len(x) != len(y):
            out.append(dict(path=p, kind="length", rebuild=len(x), published=len(y)))
        for i, (u, v) in enumerate(zip(x, y)):
            diff(u, v, f"{p}[{i}]", out)
    elif x != y:
        simv = isinstance(x, str) and x.replace(SIMV_NOW, SIMV_V3) == y
        out.append(dict(path=p, kind="number" if isinstance(x, (int, float)) else "string", rebuild=str(x)[:400], published=str(y)[:400],
                        equal_after_sim_version_substitution=bool(simv)))
    return out


def classify(d):
    if "/inputs_read/" in d["path"] and "/files/" in d["path"]:
        return "input file hash changed since the v3 build (external workdir file)"
    if d.get("equal_after_sim_version_substitution"):
        return f"simulator version string only: equal after replacing '{SIMV_NOW}' by '{SIMV_V3}' (live import of gncsim.sim6)"
    return "UNEXPLAINED"


def main():
    a, b = json.load(open(REB)), json.load(open(PUB))
    d = diff(a, b, "", [])
    for x in d:
        x["class"] = classify(x)
    res = dict(version="m2_v3_rebuild_check v1", date="2026-10-13", builder="m2_gnc_json_v3 v5.1", rebuild=REB, rebuild_sha256=sha(REB),
               published=PUB, published_sha256=sha(PUB), byte_identical=sha(REB) == sha(PUB), n_differences=len(d),
               numeric_differences=sum(1 for x in d if x["kind"] == "number"),
               unexplained=sum(1 for x in d if x["class"] == "UNEXPLAINED"), differences=d)
    with open(os.path.join(OUT, "rebuild_check_v1.json"), "w") as f:
        json.dump(res, f, indent=1)
    print(f"byte identical {res['byte_identical']}; {len(d)} differences, numeric {res['numeric_differences']}, unexplained {res['unexplained']}")
    for x in d:
        print(" ", x["kind"], x["path"], "|", x["class"])
    return 0 if res["unexplained"] == 0 and res["numeric_differences"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
