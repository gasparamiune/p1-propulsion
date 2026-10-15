# REV-GNC-4 (e): every occurrence of a REV-GNC-3 reviewer number must carry a REVIEWER attribution in its string, an
# ancestor key/tag naming the reviewer, or a sibling 'tag'/'source' naming REVIEWER / REV-GNC-3 / reviews/gnc/rev2.
import json, re, sys
d = json.load(open(sys.argv[1]))
NUMS = {
 "RG16": [r"4\.197", r"4\.20 ?%", r"4\.76", r"4\.760", r"4\.488", r"5\.107", r"3\.876", r"3\.497", r"3\.225", r"3\.086", r"2\.973", r"2\.78 ?%", r"2\.780", r"3\.835", r"3\.098", r"2\.477", r"2\.145", r"1\.804", r"1\.342", r"2\.319", r"5\.069", r"5\.616", r"4\.86 ?%", r"3\.51 ?%", r"4\.015", r"3\.508", r"0\.012 ?%", r"61,?318", r"11\.5 ?%"],
 "V": [r"35\.2", r"27\.14", r"29\.92", r"20\.68", r"21\.0 ?N", r"18\.75", r"20\.06", r"32\.98", r"20\.85", r"1\.96 ?N", r"44 of 500", r"44/500", r"run 218"],
 "G": [r"7\.4 ?%", r"22\.4 ?%", r"26\.5 ?%", r"46 ?%", r"6\.2 ?%", r"4\.1 ?%", r"21\.1 ?%", r"9\.4 ?%", r"8\.2 ?%", r"4\.9 ?%", r"0\.949", r"0\.842", r"0\.724", r"2\.66 ?s", r"91 ?%", r"64 ?%", r"40 ?%"],
 "MASS": [r"0\.07-0\.28", r"0\.07–0\.28", r"10\.3 ?g", r"26-28 ?g", r"-10\.7 ?g", r"-39\.2 ?g", r"4\.8 ?/ ?9\.6", r"9\.6 ?g"],
 "WIND": [r"6\.96", r"7\.84"],
}
ATTR = re.compile(r"REVIEWER|REV-GNC-3|reviewer|reviews/gnc/rev2|RV3-\d\d")
out = []
def walk(x, path, anc_attr):
    if isinstance(x, dict):
        sib = any(isinstance(v, str) and ATTR.search(v) and k in ("tag", "source", "sources") for k, v in x.items())
        for k, v in x.items():
            walk(v, path + [k], anc_attr or sib or bool(ATTR.search(k)))
    elif isinstance(x, list):
        for i, v in enumerate(x): walk(v, path + [str(i)], anc_attr)
    elif isinstance(x, (str, int, float)) and not isinstance(x, bool):
        s = str(x)
        for grp, pats in NUMS.items():
            for pat in pats:
                for m in re.finditer(pat, s):
                    win = s[max(0, m.start() - 400): m.end() + 400]
                    att = anc_attr or bool(ATTR.search(win))
                    out.append((grp, pat, "/".join(path), att, s[max(0, m.start() - 100): m.end() + 80]))
walk(d, [], False)
un = [o for o in out if not o[3] and "verbatim" not in o[2]]
print("hits", len(out), "unattributed (excluding verbatim lead lines)", len(un))
for o in un: print(f"  [{o[0]} {o[1]}] {o[2][:100]} :: {o[4]!r}")
