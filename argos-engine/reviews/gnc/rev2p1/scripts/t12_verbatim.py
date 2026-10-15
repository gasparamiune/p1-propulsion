# REV-GNC-4 (b): the folded lead lines are byte-identical to the CHANGELOG lines; quoted-lines hash recomputed
import json, hashlib, sys
J = sys.argv[1]; C = "/home/claude/work/shared-fallback/engine/interfaces/CHANGELOG.md"
d = json.load(open(J)); raw = open(C, "rb").read(); L = raw.decode("utf-8").split("\n")
print("CHANGELOG sha256/16", hashlib.sha256(raw).hexdigest()[:16], "newline-separated lines", len(L))
V = d["lead_decisions_2026-10-13"]["rev2p1_lines_175_183"]["verbatim"]
for k, v in V.items(): print("line", k, "identical", v == L[int(k) - 1], "len", len(v))
print("sha256/16 of lines 174-183 joined by newline", hashlib.sha256("\n".join(L[n - 1] for n in range(174, 184)).encode()).hexdigest()[:16],
      "(JSON states", d["lead_decisions_2026-10-13"]["rev2p1_lines_175_183"]["source"].split("quoted lines ")[-1] + ")")
print("fold map keys", list(d["lead_decisions_2026-10-13"]["rev2p1_lines_175_183"]["folded"].keys()))
for n in range(184, len(L) + 1):
    if L[n - 1].strip(): print(f"line {n} after the build: {L[n - 1][:110]}")
