"""REV-GNC-7 (d): compact margin / failure table per reviewer variant (m2_eng11_fe-format JSONs): both-axes window, worst upper GM
inside it, and per axis the first failing corner (mechanism, frequency, GM) at each failing K_s edge."""
import json, os, sys
D = sys.argv[2:]
out = {}
for p in D:
    if not os.path.exists(p): continue
    j = json.load(open(p)); rows = j["rows"]; v = j["variant"]
    ks = sorted({float(k.split("Ks")[1]) for k in rows})
    r = dict(J=j["J_kgm2"], spec={k: j["spec"].get(k) for k in ("Sfix", "g", "poses", "J")}, done=j.get("done"), axes={})
    for a in ("alpha", "beta"):
        ax = []
        for k in ks:
            x = rows.get(f"{a}|Ks{k:g}")
            if x is None: continue
            ax.append((k, x["pass_6dB"], x["gm_up_min_dB"] if x["pass_6dB"] else None, x.get("first_fail")))
        r["axes"][a] = ax
    both = [k for k in ks if rows.get(f"alpha|Ks{k:g}", {}).get("pass_6dB") and rows.get(f"beta|Ks{k:g}", {}).get("pass_6dB")]
    r["both_Ks"] = both
    r["gm_min_both"] = {f"{k:g}": min(rows[f"alpha|Ks{k:g}"]["gm_up_min_dB"], rows[f"beta|Ks{k:g}"]["gm_up_min_dB"]) for k in both}
    out[f"{os.path.basename(os.path.dirname(p))}/{v}"] = r
json.dump(out, open(sys.argv[1], "w"), indent=1)
for v, r in out.items():
    print(f"== {v} J {r['J']:.2e} {r['spec']} done {r['done']} both {r['both_Ks']}")
    for a, ax in r["axes"].items():
        s = []
        for k, ok, gm, ff in ax:
            if ok: s.append(f"{k:g}:{gm:.3f}")
            else:
                parts = (ff or "").split("|")
                fr = [x for x in parts if x.startswith("f")]
                g = [x for x in parts if x.startswith("GM")]
                s.append(f"{k:g}:x({parts[3] if len(parts) > 3 else ''},{fr[-1] if fr else ''},{g[-1] if g else ''})")
        print(f"   {a:5s} " + " ".join(s))
