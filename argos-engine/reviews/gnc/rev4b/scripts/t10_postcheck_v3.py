"""REV-GNC-4 post-correction check v3 (reviewer tool, read-only; v3 = REV-GNC-7, 2026-10-21, for gnc.json v3.2).
Usage: python -I t10_postcheck_v3.py <json> [out.json] [--publication] [--rv7]
v3 changes (only these): C06 is restated for v3.2. Lead 227 (5) ADOPTED pcf_tmax 0.8 s for the W10 < 6 m/s envelope, so a
  live 'pcf_tmax ... 0.8' is no longer a critical word by itself; v3 flags (C06a) a live 'pcf_tmax ... 0.8' with neither
  'W10 < 6' nor '227 (5)' within 200 characters (unscoped), and (C06b) a live 'pcf_tmax ... 0.5 s' with no marker word,
  'v3.1' or 'replac' within 120 characters (the v3.1 value presented as current); the recorded reviewer probes and
  the document self-check rules state the setting a value was flown or checked at and are exempt from C06a / C06b.  --rv7 adds R08-R11, the REV-GNC-7
  required content (0.8 s conditions after S17 v2.11 / REV-ELEC-3 R3-04 / REV-COMB-4; purge 2.43 s / 2.39 s; R3 K band).
  C01-C19 (critical words): every hit must sit under a key containing 'superseded'/'history', in the verbatim lead lines,
          in a string prefixed SUPERSEDED/HISTORY, or have a marker word within 120 characters.
  N01     (numeric): no A1/A2 apogee target of 300 m outside a section that carries a status_/note_rev2p[1-9] or *_superseded key.
  R01-R07 (required content, corrections C1-C5 of REV-GNC-4): must be present.
  U01-U04 (--publication only): the staging wording is gone.
Exit 1 if any C or N hit is unmarked, any R check fails, or (with --publication) any U check fails.
It checks words, not meaning: a pass is necessary, not sufficient (read the changed keys).
v2 (2026-10-13): C10 no longer flags the correct line-186 wording ('no unpurged relight', 'the alternative: unpurged
relight ... held to >= E2 + 0.22 s'); C17-C19 (citations) and R/U checks added; I01-I05 of v1 became R01-R05."""
import json, re, sys, hashlib
args = [a for a in sys.argv[1:] if not a.startswith("--")]
PUB = "--publication" in sys.argv
J = args[0]
raw = open(J, "rb").read()
d = json.loads(raw)
MARK = re.compile(r"SUPERSEDED|WITHDRAWN|NOT ADOPTED|NOT adopted|REFUTED|REPLACED|HISTORY|[Ss]uperseded|[Ww]ithdrawn|[Rr]efuted|[Rr]eplac(ed|es|ing)\b|no longer")
CRIT = {
 "C01 650 N confirmed": r"(?i)650 ?N[^.;]{0,80}confirm",
 "C02 mass estimate <= 1 % (1 sigma)": r"(?i)(<=|≤)\s*1(\.0)?\s*%\s*\(?\s*(1\s*-?\s*sigma|1σ)",
 "C03 FC_THRUST budget OPEN / script staged": r"(?i)error budget: OPEN|script staged, not run",
 "C04 0.6 s delay costs no P": r"(?i)costs? no (measurable )?P\b|no measurable P\b",
 "C05 time-only release term": r"0xFFFF AND t >= t_E2",
 "C07 per-flight RG-16 support": r"(?i)provisional support",
 "C08 0.30 kg trigger": r"(?i)0\.30 kg[^.;]{0,40}trigger|trigger[^.;]{0,40}0\.30 kg|adds > 0\.30 kg",
 "C09 L* interim 1.7 s (line 186 (1))": r"(?i)interim[^.;]{0,20}1\.7 ?s|L\* ?= ?1\.7",
 "C10 unpurged relight fallback (line 186 (1))": r"(?i)(?<!no )(?<!alternative: )(relight (proceeds )?unpurged|proceeds unpurged|unpurged relight)(?![^.;]{0,80}(E2 ?\+ ?0\.22|held to))",
 "C11 PURGE NOT RUN LO P_total ~0.75 (line 186 (1))": r"(?i)P_total ~?0\.75",
 "C12 pre-R2 drogue predicate": r"RELEASE iff b4 AND \[\(d2-d3 != 0xFFFF",
 "C13 unscoped '0.81 s plan holds'": r"(?i)0\.81 s plan holds(?![^.;]{0,80}predictor path)",
 "C14 RV-1c pivot station 0.2223 m in conventions": r"pivot at 0\.2223 m",
 "C15 cold-flow unbounded (line 185/186 (2))": r"(?i)cold-flow apparent thrust unbounded|0 / 5 / 10 N parametric",
 "C16 H20/OI-31 still 'not decided' (line 186 (1))": r"(?i)(H20|OI-31|no relight on that pass)[^\n]{0,200}?(not decided by the lead|pending a lead decision)",
 "C17 '2000 runs' where the plain trigger fired in 649": r"(?i)plain trigger fired \(2000 runs",
 "C18 W10 6.96-7.84 m/s cited to s04_wind.out": r"6\.96-7\.84 m/s \(REVIEWER reviews/gnc/rev2/logs/s04_wind\.out",
 "C19 'RG-16 margin 0.012 %' (unit: percentage points; REVIEWER number)": r"(?i)RG-16 margin 0\.012 ?%",
}
flat = []
def walk(x, path):
    if isinstance(x, dict):
        for k, v in x.items(): walk(v, path + [str(k)])
    elif isinstance(x, list):
        for i, v in enumerate(x): walk(v, path + [str(i)])
    else:
        flat.append(("/".join(path), x))
walk(d, [])
def exempt(p, s, pos):
    pl = p.lower()
    if "superseded" in pl or "history" in pl or "/verbatim/" in pl or pl.startswith("rev2p1_document_self_check") or pl.startswith("rev_gnc_4"):
        return True
    if isinstance(s, str) and s.startswith(("SUPERSEDED", "HISTORY")): return True
    win = s[max(0, pos - 120): pos + 120]
    return bool(MARK.search(win))
res = {}; bad = 0
SCOPE = re.compile(r"W10 ?(<|&lt;) ?6|227 \(5\)")
C06 = {"C06a pcf_tmax 0.8 s without its W10 < 6 / 227 (5) scope (v3.2)": re.compile(r"(?i)pcf_tmax[^.;]{0,30}0\.8"),
       "C06b pcf_tmax 0.5 s presented as current (v3.2)": re.compile(r"(?i)pcf_tmax[^.;]{0,30}0\.5 ?s")}
for name, rx in C06.items():
    hits = []
    for p, s in flat:
        if not isinstance(s, str): continue
        for m in rx.finditer(s):
            if exempt(p, s, m.start()): continue
            if "/reviewer_probes/" in p or p.lower().startswith(("rev4b_document_self_check", "rev2p2_document_self_check")): continue
            if name.startswith("C06a") and SCOPE.search(s[max(0, m.start() - 200): m.end() + 200]): continue
            if name.startswith("C06b") and re.search(r"v3\.1|[Rr]eplac", s[max(0, m.start() - 120): m.end() + 120]): continue
            hits.append(dict(path=p, context=s[max(0, m.start() - 90): m.end() + 90]))
    res[name] = hits; bad += len(hits)
    print(f"{name:60s} unmarked {len(hits)}")
    for h in hits: print(f"     {h['path'][:110]} :: {h['context']!r}")
for name, pat in CRIT.items():
    rx = re.compile(pat); hits = []
    for p, s in flat:
        if not isinstance(s, str): continue
        for m in rx.finditer(s):
            if not exempt(p, s, m.start()):
                hits.append(dict(path=p, context=s[max(0, m.start() - 90): m.end() + 90]))
    res[name] = hits; bad += len(hits)
    print(f"{name:60s} unmarked {len(hits)}")
    for h in hits: print(f"     {h['path'][:110]} :: {h['context']!r}")
def anc_status(p):
    # a numeric leaf is exempt when an ancestor dict carries a rev2.1+ status / note / superseded key
    x = d; parts = p.split("/")
    for depth, tok in enumerate(parts[:-1]):
        if isinstance(x, dict):
            if depth > 0 and any(re.search(r"(?i)^(status|note)_rev2p[1-9]|_superseded", k) for k in x): return True
            x = x.get(tok)
        elif isinstance(x, list):
            x = x[int(tok)]
    return False
num = [(p, v) for p, v in flat if isinstance(v, (int, float)) and not isinstance(v, bool)
       and re.search(r"(?i)apogee_target|h_target", p) and abs(float(v) - 300.0) < 1e-9 and not exempt(p, "", 0)
       and not anc_status(p)]
print(f"{'N01 numeric A1/A2 apogee target 300 m outside history':60s} unmarked {len(num)}")
for p, v in num: print("     ", p, v)
# required content (REV-GNC-4 corrections C1-C5)
live = " \n".join(s for p, s in flat if isinstance(s, str) and not exempt(p, "", 0) and not s.startswith(("SUPERSEDED", "HISTORY")))
ref = set(re.findall(r"rev3 P(\d)", live))
for a, b in re.findall(r"rev3 P(\d)\s*[-–]\s*P(\d)", live): ref |= {str(i) for i in range(int(a), int(b) + 1)}
defined = set()
def keys(x):
    if isinstance(x, dict):
        for k, v in x.items():
            m = re.match(r"(?i)^(rev3[ _]?)?P(\d)\b", str(k))
            if m: defined.add(m.group(2))
            keys(v)
    elif isinstance(x, list):
        for v in x: keys(v)
keys(d)
fmea = json.dumps({k: v for k, v in d.items() if k.startswith("fmea_inputs")}, ensure_ascii=False)
probe = json.dumps(d.get("rev2", {}).get("amendment_V_pc_invalid", {}).get("reviewer_probes", {}), ensure_ascii=False)
REQ = {
 "R01 fold map names line 186": bool(re.search(r"\b186\b", json.dumps(d.get("lead_decisions_2026-10-13", {}), ensure_ascii=False))),
 "R02 R2 command hold (start level, 62.5 N) in requirements.ignition.relight_conditions": bool(re.search(r"(?i)start level|62\.5 ?N", json.dumps(d.get("requirements", {}).get("ignition", {}).get("relight_conditions", {}), ensure_ascii=False))),
 "R03 publication_note names sim6 v2.9-dev": "v2.9-dev" in json.dumps(d.get("publication_note", {})),
 f"R04 every live 'rev3 P#' reference is defined by a key (referenced {sorted(ref)}, defined {sorted(defined)})": ref <= defined,
 "R05 status states validity at ledger v3d (re-exhaustion / not demonstrated)": bool(re.search(r"(?i)not demonstrated|re-?exhaust|valid (only )?(at|on) (the )?ledger v3d", d.get("status", ""))),
 "R06 W<6 m/s probe carries its base (A1_none) and the binding A1J_pc 20.85 N": ("A1_none" in probe and "20.85" in probe),
 "R07 FMEA inputs carry line 186 (below-L* pass loss; cold-flow condition on the R2 flame-out hold)": bool(re.search(r"\b186\b", fmea) and re.search(r"(?i)cold", fmea)),
}
if "--rv7" in sys.argv:
    rc = json.dumps(d.get("requirements", {}).get("ignition", {}).get("relight_conditions", {}), ensure_ascii=False)
    pb = json.dumps(d.get("flight_software", {}).get("relight_sequence_placeholder", {}).get("v", {}).get("purge_bound", {}), ensure_ascii=False)
    REQ.update({
     "R08 relight_conditions carries the S17 v2.11 0.8 s conditions (photodiode view or reference re-taken; FC Pc branch; cold flow x 1.3)": bool(
         re.search(r"(?i)photodiode", rc) and re.search(r"(?i)Pc branch", rc) and re.search(r"(?i)cold[- ]flow[^.;]{0,80}1\.3|1\.3[^.;]{0,40}cold", rc) and re.search(r"2\.51 N", rc)),
     "R09 purge_bound carries the adopted 2.43 s flow / 2.39 s cap (256 (2)) and the 80.5 g Cd 0.80 sensitivity": bool(
         re.search(r"2\.43 s", pb) and re.search(r"2\.39 s", pb) and re.search(r"80\.5 g", pb)),
     "R10 gnc.json carries the R3 K band (range_over_posted_R3_poses, f3c7cfbcfb98bcd7)": "f3c7cfbcfb98bcd7" in json.dumps(d, ensure_ascii=False),
     "R11 lost-relight mission outcome stated (253 (7)(iv); unprimed / UNKNOWN line refused)": bool(re.search(r"(?i)(unprimed|UNKNOWN)[^\n]{0,300}refused", json.dumps(d, ensure_ascii=False))),
    })
if PUB:
    REQ.update({
     "U01 version carries no 'staging'": "staging" not in str(d.get("version", "")).lower(),
     "U02 status carries no 'NOT PUBLISHED' / 'STAGING'": not re.search(r"NOT PUBLISHED|STAGING", d.get("status", "")),
     "U03 supersedes names gnc.json v3 without 'nothing yet'": ("nothing yet" not in str(d.get("supersedes", ""))) and ("v3" in str(d.get("supersedes", ""))),
     "U04 no checkpoint 'Por revisar'": "Por revisar" not in json.dumps({k: v for k, v in d.items() if k.startswith("checkpoint")}, ensure_ascii=False),
    })
req_fail = 0
for k, v in REQ.items():
    print(f"{k:110s} {'yes' if v else 'NO'}"); req_fail += (not v)
out = dict(tool="t10_postcheck v3", json=J, sha256_16=hashlib.sha256(raw).hexdigest()[:16], publication_mode=PUB,
           critical_unmarked=bad, numeric_300=len(num), required_failed=req_fail, hits=res, numeric=num, required=REQ)
if len(args) > 1: json.dump(out, open(args[1], "w"), indent=1, ensure_ascii=False)
print("sha256/16", out["sha256_16"], "critical unmarked", bad, "numeric 300", len(num), "required failed", req_fail, "publication mode", PUB)
sys.exit(1 if (bad or num or req_fail) else 0)
