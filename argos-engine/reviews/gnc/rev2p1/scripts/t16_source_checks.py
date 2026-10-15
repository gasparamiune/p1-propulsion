# REV-GNC-4 t16: source checks backing RV4-03 / RV4-04 (read-only; prints evidence lines)
import json, re, hashlib, sys
H = "/home/claude/work/shared-fallback/engine"
R = H + "/reviews/gnc/rev2/logs"
def h16(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
def lines(p): return open(p, encoding="utf-8", errors="replace").read().split("\n")
# 1. s15: plain-trigger fire count and min lead
p = R + "/s15_g_decided.out"; print("s15", h16(p))
for i, l in enumerate(lines(p), 1):
    if "plain trigger fired" in l: print(f"  s15:{i}: {l.strip()}")
# 2. s03 / s04: where the W10 6.96-7.84 m/s per-run winds live
for name in ("s03_trim.out", "s04_wind.out"):
    p = R + "/" + name; L = lines(p)
    trip = []
    for i, l in enumerate(L, 1):
        m = re.search(r"'wind': ([0-9.]+)", l); r = re.search(r"'run': ([0-9.]+)", l); o = re.search(r"'ok': ([0-9.]+)", l)
        if m: trip.append((i, r.group(1) if r else "?", o.group(1) if o else "?", float(m.group(1))))
    has = [s for s in ("6.96", "7.84", "7.836", "6.96") if any(s in l for l in L)]
    print(name, h16(p), "per-run wind fields", len(trip), "strings present", sorted(set(has)))
    if trip:
        ws = [t[3] for t in trip if t[2] == "0.0"]
        print("   failing-run (ok 0) winds min/max", (min(ws), max(ws)) if ws else None, "n", len(ws))
# 3. prior review text (lead-extracted) for W10 and the W<6 probe values
p = H + "/reviews/REVIEW-GNC-R2.md"; print("REVIEW-GNC-R2.md", h16(p))
for i, l in enumerate(lines(p), 1):
    if re.search(r"6\.96|18\.75|20\.85|20\.06", l): print(f"  R2:{i}: {l.strip()[:200]}")
# 4. pivot station: interface and vehicle v3d vs the JSON conventions
m = json.load(open(H + "/01-systems-gnc/staging_v3.1/rev2/sim/iface_v3d/mechanical.json"))
print("mechanical.json v2 frames.rv1_station_of_pivot_m", m["frames"]["rv1_station_of_pivot_m"]["v"])
v = json.load(open(H + "/01-systems-gnc/vehicle/vehicle_v3d.json")); print("vehicle_v3d.json z_pivot_m", v.get("z_pivot_m"))
J = H + "/01-systems-gnc/staging_v3.1/rev2p1/results/gnc_json/gnc_v3.1_staging_rev2p1.json"; d = json.load(open(J)); print("staged JSON", h16(J))
print("  conventions.stations:", json.dumps(d["conventions"]["stations"])[:260])
print("  reviewer_probes.inside_W10_lt6_N:", json.dumps(d["rev2"]["amendment_V_pc_invalid"]["reviewer_probes"]["inside_W10_lt6_N"]))
print("  publication_note.built_on:", d["publication_note"]["built_on"][:240])
print("  version:", d["version"], "| supersedes:", d["supersedes"][:80])
# 5. CHANGELOG state at hand-back
p = H + "/interfaces/CHANGELOG.md"; L = open(p, encoding="utf-8").read().splitlines()
print("CHANGELOG", h16(p), "lines", len(L), "| last line head:", L[-1][:90])
