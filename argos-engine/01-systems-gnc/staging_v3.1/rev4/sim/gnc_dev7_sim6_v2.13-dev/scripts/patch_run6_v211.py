"""patch_run6_v211 v1.0 (GNC rev3, 2026-10-13): run6 v2.11-dev, the parameter of sim6 v2.11-dev amendment L (flt_dla, forced
abort decision at the RG-16 detection-latency allowance after the stuck-thrust plateau onset; off by default, -1). Source run6
v2.10-dev 8719591fd6f8cafb; every anchor must occur exactly once."""
import hashlib
import sys

P = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/work/space/gnc_dev5/gncsim/run6.py"
SRC16 = "8719591fd6f8cafb"
s = open(P).read()
h = hashlib.sha256(s.encode()).hexdigest()[:16]
if h != SRC16:
    raise SystemExit(f"{P}: sha256/16 {h} != v2.10-dev {SRC16} (already patched?)")


def rep(old, new, count=1):
    global s
    n = s.count(old)
    if n != count:
        raise SystemExit(f"anchor found {n} times (expected {count}): {old[:90]!r}")
    s = s.replace(old, new)


rep('"""run6 v2.10-dev (v2.10-dev amendment V2', '"""run6 v2.11-dev (v2.11-dev amendment L (flt_dla: forced abort decision at the RG-16 '
    'detection-latency allowance after the stuck-thrust plateau onset); v2.10-dev amendment V2')
rep('''def cfg_of(**kw):
''', '''# v2.11-dev amendment L (RG-16 latency allowance; sim6 flt_dla), off by default
DEF.update(flt_dla=-1.0)


def cfg_of(**kw):
''')
rep('''    S("det_geo", float(cfg["det_geo"]), "CONFIG geofence abort (GNC PROPOSAL, research; off in the baseline)")
''', '''    S("det_geo", float(cfg["det_geo"]), "CONFIG geofence abort (GNC PROPOSAL, research; off in the baseline)")
    S("flt_dla", float(cfg["flt_dla"]), "REQ LEAD line 181 (3) PROVISIONAL RG-16 detection-latency allowance [s] flown as a forced "
                                        "abort decision after the stuck-thrust plateau onset (sim6 v2.11-dev L); < 0 = off")
''')
open(P, "w").write(s)
print("patched", P, hashlib.sha256(s.encode()).hexdigest()[:16])
