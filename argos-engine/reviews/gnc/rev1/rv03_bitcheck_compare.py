"""rv03_bitcheck_compare v1.0 (REV-GNC-R1, independent reviewer, 2026-10-13).

Compares the reviewer's re-run of m2_bitcheck_v28 v1.5 with EVERY part (A-H, W, X, P, R, S) on the final rev1 code
(sim6 f9094b63e64f2324, run6 35b5c808487b9339; rv01_bitcheck/bitcheck_v28.json) against the bitcheck files GNC published:
  v28_checks_v15 (v1.5, parts A-F, P, R, S on the final code)
  v28_checks_v13 (v1.3, parts A-H, W, X, P on the pre-R code, sim6 b4fe41a270488d9e)
Every leaf value is compared exactly (floats bit for bit through JSON); path strings that name a folder are reported, not
failed. Output: rv03_bitcheck_compare.json. Reads only.
"""
import json
import os

HUB = "/home/claude/work/shared-fallback/engine"
REV1 = f"{HUB}/01-systems-gnc/staging_v3.1/rev1/results"
HERE = os.path.dirname(os.path.abspath(__file__))


def leaves(x, p=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from leaves(v, f"{p}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from leaves(v, f"{p}[{i}]")
    else:
        yield p, x


def diff(a, b):
    la, lb = dict(leaves(a)), dict(leaves(b))
    keys = sorted(set(la) | set(lb))
    eq, ne, only_a, only_b = 0, [], [], []
    for k in keys:
        if k not in lb:
            only_a.append(k)
        elif k not in la:
            only_b.append(k)
        elif la[k] == lb[k]:
            eq += 1
        else:
            ne.append((k, la[k], lb[k]))
    return dict(equal=eq, different=len(ne), first_different=ne[:12], only_mine=len(only_a), only_published=len(only_b),
                only_mine_first=only_a[:6], only_published_first=only_b[:6])


def main():
    mine = json.load(open(os.path.join(HERE, "rv01_bitcheck", "bitcheck_v28.json")))
    v15 = json.load(open(f"{REV1}/v28_checks_v15/bitcheck_v28.json"))
    v13 = json.load(open(f"{REV1}/v28_checks_v13/bitcheck_v28.json"))
    out = dict(version="rv03_bitcheck_compare v1.0", mine=dict(tool=mine["tool"], sim=mine["sim"], iface=mine["iface"],
                                                                  parts=list(mine["parts"]), all_passed=mine["all_passed"]),
               published_v15=dict(tool=v15["tool"], sim=v15["sim"], parts=list(v15["parts"]), all_passed=v15["all_passed"]),
               published_v13=dict(tool=v13["tool"], sim=v13["sim"], parts=list(v13["parts"]), all_passed=v13["all_passed"]),
               vs_v15={}, vs_v13={}, passed_flags={})
    for part in mine["parts"]:
        if part in v15["parts"]:
            out["vs_v15"][part] = diff(mine["parts"][part], v15["parts"][part])
        if part in v13["parts"]:
            out["vs_v13"][part] = diff(mine["parts"][part], v13["parts"][part])
    for p, v in leaves(mine["parts"]):
        if p.endswith("/passed"):
            out["passed_flags"][p] = v
    out["n_passed_flags"] = len(out["passed_flags"])
    out["n_false_flags"] = sum(1 for v in out["passed_flags"].values() if v is not True)
    with open(os.path.join(HERE, "rv03_bitcheck_compare.json"), "w") as f:
        json.dump(out, f, indent=1, default=str)
    print("mine:", out["mine"])
    for k in ("vs_v15", "vs_v13"):
        for part, d in out[k].items():
            print(k, part, "equal", d["equal"], "different", d["different"], "only_mine", d["only_mine"], "only_pub",
                  d["only_published"], d["first_different"][:3])
    print("passed flags", out["n_passed_flags"], "false", out["n_false_flags"])


if __name__ == "__main__":
    main()
