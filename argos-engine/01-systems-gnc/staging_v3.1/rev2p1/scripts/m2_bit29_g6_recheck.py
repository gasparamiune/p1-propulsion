"""m2_bit29_g6_recheck v1.0 (GNC rev2.1, 2026-10-13, RV3-08): NO FLIGHT. Applies the m2_bitcheck_v29 v1.2 G6 criterion
(g6_pass: decided arm clean AND positive control) to the G6 blocks STORED by rev2 bit-check run 1 (tool v1.0) and run 2
(tool v1.1), and records the v1.2 code/data hash table of the current work tree. Expected: run 1 FAILS under v1.2 (no P30 arm,
no positive control), run 2 PASSES (P30 reproduced 6 starts > 200 m by the rev1 arm and 6 flagged spurious by the gate-off CA
arm). Output: $GNC_G6R_OUT (default out/rev3/rev2p1/bit29_g6_recheck.json)."""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_bitcheck_v29 as B  # noqa: E402

HUB = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev2/results/bitcheck_v29"
OUT = os.environ.get("GNC_G6R_OUT", "/home/claude/work/space/out/rev3/rev2p1/bit29_g6_recheck.json")


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def main():
    out = dict(version="m2_bit29_g6_recheck v1.0", tool=B.VERSION, tool_sha256_16=sha16(B.__file__), runs={})
    for tag, fn in (("run1_tool_v1.0", "bitcheck_v29_run1_FAIL.json"), ("run2_tool_v1.1", "bitcheck_v29.json")):
        p = os.path.join(HUB, fn)
        d = json.load(open(p))
        g6 = d["parts"]["G"]["G6_P30_reproduction"]
        v = B.g6_pass(g6)
        out["runs"][tag] = dict(source=f"{p} (sha256/16 {sha16(p)})", stored_passed=g6.get("passed"),
                                stored_P30_reproduced=g6.get("P30_reproduced"), arms=[k for k in g6 if isinstance(g6[k], dict)],
                                v12_verdict=v)
        print(tag, "stored passed", g6.get("passed"), "-> v1.2", v, flush=True)
    out["expected"] = dict(run1_tool_v1_0=False, run2_tool_v1_1=True)
    out["test_passed"] = bool(out["runs"]["run1_tool_v1.0"]["v12_verdict"]["passed"] is False
                              and out["runs"]["run2_tool_v1.1"]["v12_verdict"]["passed"] is True)
    out["code_and_data_sha256_16"] = B.code_hashes()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1)
    print("test_passed", out["test_passed"], "modules/data hashed", len(out["code_and_data_sha256_16"]), "->", OUT, sha16(OUT))


if __name__ == "__main__":
    main()
