# REV-GNC-4: statements in the rev2.1 JSON affected by lead CHANGELOG line 186 (1)-(2) (arrived after the rev2.1 build)
import json, re, sys
J = sys.argv[1]
d = json.load(open(J))
flat = []
def walk(x, p):
    if isinstance(x, dict):
        for k, v in x.items(): walk(v, p + "/" + str(k))
    elif isinstance(x, list):
        for i, v in enumerate(x): walk(v, p + f"[{i}]")
    elif isinstance(x, str): flat.append((p, x))
walk(d, "")
PAT = {
 "L186a_interim_1p7": r"(?i)interim[^.;]{0,20}1\.7 ?s|1\.7 ?s[^.;]{0,30}interim|L\* ?= ?1\.7|L\*[^.;]{0,40}1\.7 ?s",
 "L186b_unpurged_relight": r"(?i)relight (proceeds )?unpurged|proceeds unpurged|unpurged relight|relight unpurged",
 "L186c_PNR_LO_075": r"(?i)PURGE NOT RUN LO[^.;]{0,40}0\.7[45]|P_total ~?0\.75|~0\.75|0\.743|0\.754",
 "L186d_LO_HI_open": r"(?i)LO ?/ ?HI|LO or HI|if HI|if an unpurged start is LO",
 "L186e_cmd_hold": r"(?i)start level|62\.5 ?N|command hold|open-loop command",
 "L186f_cold_flow": r"(?i)cold[- ]flow",
 "L186g_E2_022": r"E2 ?\+ ?0\.22",
}
for name, pat in PAT.items():
    rx = re.compile(pat)
    hits = [(p, m.start(), s) for p, s in flat for m in rx.finditer(s)]
    print(f"## {name}: {len(hits)}")
    for p, pos, s in hits:
        if "verbatim" in p: 
            print(f"   [verbatim] {p}"); continue
        print(f"   {p[:100]} :: {s[max(0,pos-110):pos+150]!r}")
