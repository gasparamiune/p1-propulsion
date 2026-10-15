"""rev2p2_number_provenance v1.0 (GNC, 2026-10-13): every number in a changed or added live string of rev2.2 (keys outside *superseded*, the verbatim lead lines and the build records) must already occur in a cited source (rev2.1 JSON, REVIEW-GNC-R2P1, REVIEW-GNC-R2, REVIEW-MECHANICAL-R1, CHANGELOG lines 151-190, s15, s03, cold_flow json, vehicle_v3d, mechanical v2). A weak test: an occurrence is not proof of correct attribution."""
import json, re, sys
HUB = "/home/claude/work/shared-fallback/engine"
a = json.load(open(f"{HUB}/01-systems-gnc/staging_v3.1/rev2p1/results/gnc_json/gnc_v3.1_staging_rev2p1.json"))
b = json.load(open(f"{HUB}/01-systems-gnc/staging_v3.1/rev2p2/results/gnc_json/gnc_v3.1_rev2p2.json"))
srcs = {
 "rev2p1_json": open(f"{HUB}/01-systems-gnc/staging_v3.1/rev2p1/results/gnc_json/gnc_v3.1_staging_rev2p1.json").read(),
 "REVIEW-GNC-R2P1": open(f"{HUB}/reviews/REVIEW-GNC-R2P1.md").read(),
 "REVIEW-GNC-R2": open(f"{HUB}/reviews/REVIEW-GNC-R2.md").read(),
 "REVIEW-MECH-R1": open(f"{HUB}/reviews/REVIEW-MECHANICAL-R1.md").read(),
 "CHANGELOG": "\n".join(open(f"{HUB}/interfaces/CHANGELOG.md").read().split("\n")[150:190]),
 "s15": open(f"{HUB}/reviews/gnc/rev2/logs/s15_g_decided.out").read(),
 "s03": open(f"{HUB}/reviews/gnc/rev2/logs/s03_trim.out").read(),
 "cold_json": open(f"{HUB}/02-combustion/data/v2p4a/cold_flow_thrust_v2p4a.json").read(),
 "vehicle_v3d": open(f"{HUB}/01-systems-gnc/vehicle/vehicle_v3d.json").read(),
 "mech_v2": open("/home/claude/work/space/iface_v3d/mechanical.json").read(),
}
def strings(x, p=""):
    if isinstance(x, dict):
        for k, v in x.items(): yield from strings(v, f"{p}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x): yield from strings(v, f"{p}/{i}")
    elif isinstance(x, str): yield p, x
    elif isinstance(x, (int, float)) and not isinstance(x, bool): yield p, repr(x)
def get(d, p):
    for k in p.strip("/").split("/"):
        if isinstance(d, list):
            try: d = d[int(k)]
            except Exception: return None
        elif isinstance(d, dict):
            if k not in d: return None
            d = d[k]
        else: return None
    return d
old = set(s for _, s in strings(a))
skip = ("superseded", "/verbatim/", "rev2p2_document_self_check", "inputs_read/rev2p2", "/sha256", "scripts_rev2p2")
num = re.compile(r"(?<![\w.])[-+]?\d+(?:\.\d+)?(?:e-?\d+)?")
trivial = set(str(i) for i in range(0, 13)) | {"2026", "10", "13"}
miss = []
n = 0
for p, s in strings(b):
    if any(k in p for k in skip) or s in old: continue
    if re.fullmatch(r"[0-9a-f]{16}", s): continue
    for m in num.finditer(s):
        t = m.group(0).lstrip("+")
        if t in trivial or t.lstrip("-") in trivial: continue
        ctx = s[max(0, m.start()-25): m.end()+12]
        if re.search(r"[0-9a-f]{16}", s[max(0, m.start()-16): m.end()+16]) and re.fullmatch(r"[0-9a-f]+", s[max(0,m.start()-1):m.end()+1].strip(" ()")):
            continue
        n += 1
        found = [k for k, txt in srcs.items() if re.search(r"(?<![\d.])" + re.escape(t.lstrip("-")) + r"(?![\d])", txt)]
        if not found:
            miss.append((p, t, ctx))
print(f"numbers checked {n}; without a source occurrence {len(miss)}")
for p, t, ctx in miss: print(" MISS", t, "|", p, "|", ctx)
