"""Extract the sentences that name standard hardware from every part's name/notes/dwg (RM1-12 census, dev)."""
import sys, re, json
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/03-cad/src")
import config, build
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=False, overrides=dict(config.V351_ON))
pat = re.compile(r"(\d+\s*x\s*)?(M\d(\.\d)?(x\d+(\.\d+)?)?(\s*x\s*\d+(\.\d+)?)?\b|AS568-\d{3}|O-ring|DIN \d+|ISO \d+|helicoil|dowel|rivet|\bnut\b|screw|bolt|washer|circlip|P-clip|Loctite|torque|N\.m|N m|Nm|A4-80|A2-70|12\.9|10\.9|seal)", re.I)
out = {}
for p in reg:
    txt = f"{p.name}. {p.notes}. " + " ".join(f"{k}: {v}." for k, v in (p.dwg or {}).items()) if isinstance(p.dwg, dict) else f"{p.name}. {p.notes}. {json.dumps(p.dwg)}"
    sents = re.split(r"(?<=[.;])\s+", txt)
    hit = [s for s in sents if pat.search(s)]
    if hit:
        out[p.pn] = {"qty": p.qty, "cots": p.cots, "material": p.material, "groups": sorted({build.group_of(g) for (_, g) in p.placements}), "name": p.name, "sents": hit}
json.dump(out, open("/home/claude/work/mechanical/v351/gm/hw_sentences.json", "w"), indent=1)
with open("/home/claude/work/mechanical/v351/gm/hw_sentences.txt", "w") as f:
    for pn, d in out.items():
        f.write(f"=== {pn} qty {d['qty']} cots {d['cots']} {d['groups']} {d['material']} | {d['name']}\n")
        for s in d["sents"]:
            f.write("   - " + s.strip()[:700] + "\n")
print(len(out))
