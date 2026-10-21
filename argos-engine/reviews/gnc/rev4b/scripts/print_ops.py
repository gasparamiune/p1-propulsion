"""REV-GNC-7: print the corrections JSON (gnc.json ops and datasheet ops) as plain text for the review appendix."""
import json, sys
d = json.load(open(sys.argv[1]))
print("tool", d["tool"], "candidate", d["candidate_sha16"], "datasheet", d["datasheet_sha16"], "ops", d["n_ops"], "incomplete", d["incomplete_variants"])
for i, e in enumerate(d["ops"]):
    head = f"[{i}] {e['op']} {e['path']} ({e['finding']})" + (f" -> new key {e['new_key']}" if e["op"] == "rename" else "")
    print(head)
    if e["op"] == "replace" and len(e["old"]) < 400: print("   OLD:", e["old"])
    elif e["op"] == "replace": print("   OLD: (the ENG11 old segment, see RV7-01)" if e["old"].startswith("design-to window 100 <= K_s <= 130") else "   OLD: " + e["old"])
    if "new" in e:
        nv = e["new"]
        print("   NEW:", json.dumps(nv, ensure_ascii=False, indent=None) if isinstance(nv, dict) else nv)
for o in d["datasheet_ops"]:
    print(f"[DS row {o['row']}] ({o['finding']})"); print("   OLD:", o["old"]); print("   NEW:", o["new"])
