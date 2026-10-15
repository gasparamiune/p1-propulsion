"""Census of standard hardware named in the CAD part notes / names (RM1-12), v3.5.1 dev build."""
import sys, re, json
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/03-cad/src")
import config, build
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=False, overrides=dict(config.V351_ON))
pat = re.compile(r"(\d+\s*x\s*)?(M\d(\.\d)?(x\d+(\.\d+)?)?(\s*x\s*\d+(\.\d+)?)?|AS568-\d{3}|O-ring|DIN \d+|ISO \d+|helicoil|dowel|rivet|nut|screw|bolt|washer|circlip|clip|Loctite)", re.I)
out = []
for p in reg:
    txt = f"{p.name} || {p.notes} || {json.dumps(p.dwg)}"
    hits = sorted(set(m.group(0) for m in pat.finditer(txt)))
    if hits:
        out.append({"pn": p.pn, "qty": p.qty, "cots": p.cots, "groups": sorted({build.group_of(g) for (_, g) in p.placements}), "hits": hits, "notes": p.notes[:600], "name": p.name})
json.dump(out, open("/home/claude/work/mechanical/v351/gm/hw_census_raw.json", "w"), indent=1)
for o in out:
    print(o["pn"], o["qty"], o["groups"], o["hits"])
