# REV-GNC-4 (d): reviewer re-derivation of the v1.2 G6 verdicts from the STORED rev2 bit-check G6 blocks (no author code)
import json, hashlib
H = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev2/results/bitcheck_v29"
for fn in ("bitcheck_v29_run1_FAIL.json", "bitcheck_v29.json"):
    p = f"{H}/{fn}"; raw = open(p, "rb").read()
    g6 = json.loads(raw)["parts"]["G"]["G6_P30_reproduction"]
    print("==", fn, hashlib.sha256(raw).hexdigest()[:16], "stored passed", g6.get("passed"), "stored P30_reproduced", g6.get("P30_reproduced"))
    for k, v in g6.items():
        if isinstance(v, dict): print("   ", k, {kk: v.get(kk) for kk in ("starts_above_200m", "spurious", "commit_before_gate", "start_h_max")})
    dec = g6.get("G_decided", {}); p30 = g6.get("oldP_P30")
    ca = [v for k, v in g6.items() if k.startswith("G_gate0_CA") and isinstance(v, dict)]
    dc = dec.get("spurious") == 0 and dec.get("commit_before_gate") == 0 and dec.get("starts_above_200m") == 0
    pr = p30 is not None and p30.get("starts_above_200m", 0) > 0
    cr = bool(ca) and ca[0].get("starts_above_200m", 0) > 0 and ca[0].get("spurious", 0) > 0
    print("    reviewer criterion (decided clean AND exact P30 arm > 0 starts above 200 m AND gate-off CA arm flags them):",
          "decided_clean", dc, "P30", pr, "CA", cr, "-> PASS" if (dc and pr and cr) else "-> FAIL")
