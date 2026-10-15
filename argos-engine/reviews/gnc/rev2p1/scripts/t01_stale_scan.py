# REV-GNC-4 reviewer stale-pattern scan (own patterns, own marker rule; independent of the author's self-check)
import json, re, sys, hashlib
J = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else None
raw = open(J, 'rb').read()
print("json sha256/16", hashlib.sha256(raw).hexdigest()[:16])
d = json.loads(raw)
flat = []
def walk(x, p):
    if isinstance(x, dict):
        for k, v in x.items(): walk(v, p + "/" + str(k))
    elif isinstance(x, list):
        for i, v in enumerate(x): walk(v, p + f"[{i}]")
    else:
        flat.append((p, x))
walk(d, "")
print("leaves", len(flat), "string leaves", sum(isinstance(v, str) for _, v in flat))
PAT = {
 "P01_650N_confirm": r"(?i)650 ?N[^.;]{0,80}confirm|confirm[^.;]{0,60}650 ?N",
 "P02_20ms_confirm": r"(?i)20 ?ms[^.;]{0,40}confirm",
 "P03_1pct_1sigma": r"(?i)(<=|≤|within|to|of)\s*1(\.0)?\s*%\s*,?\s*\(?\s*(1\s*-?\s*sigma|1σ|1-σ|one sigma)",
 "P04_massest_1pct": r"(?i)mass[ _-]?estimat[^.;]{0,80}\b1(\.0)? ?%",
 "P05_300m": r"(?i)\b300 ?m\b(?! ?/)",
 "P07_OPEN_script": r"(?i)script staged|staged, not run|error budget: OPEN",
 "P08_costs_no": r"(?i)costs? no (measurable )?P\b|no measurable P\b|costs nothing|no P cost|without (a )?(measurable )?P loss|no measurable (loss|cost)",
 "P09_delay_0p6": r"(?i)(delay|T_fire)[^.;]{0,60}0\.6 ?s|0\.6 ?s[^.;]{0,60}(delay|T_fire)",
 "P10_minus_1p7": r"(?i)(-|−|minus) ?1\.7 ?s|trigger ?(-|−) ?1\.7",
 "P11_FC_delays": r"(?i)delays? T_fire|FC delays",
 "P12_0xFFFF": r"0xFFFF",
 "P13_time_only": r"(?i)time-only|time only",
 "P14_pcf_tmax_0p8": r"(?i)pcf_tmax[^.;]{0,30}0\.8|0\.8 ?s[^.;]{0,40}pcf_tmax|tmax[^.;]{0,12}0\.8",
 "P16_per_flight": r"(?i)per-flight|per flight",
 "P17_prov_support": r"(?i)provisional support",
 "P18_2p49": r"2\.49 ?%|2\.486",
 "P19_credit": r"(?i)credit",
 "P20_freeze": r"(?i)\bfreez|\bfrozen",
 "P21_0p30kg": r"0\.30? ?kg",
 "P22_gt_0p3": r"(?i)>\s*0\.3",
 "P23_line172": r"(?i)line 172\b|to 172\b|through 172\b|l\.172\b|lines? [0-9, ]*172\b",
 "P24_provisional": r"(?i)provisional",
 "P25_W10": r"W10",
 "P26_armed": r"(?i)\barm(ed|ing|s)?\b[^.;]{0,40}FC_THRUST|FC_THRUST[^.;]{0,60}\barm(ed|ing|s)?\b",
 "P27_R1": r"\bR1\b",
 "P28_pred_adopted": r"(?i)adopted release predicate|release predicate[^.;]{0,40}adopted",
 "P29_0p81": r"0\.81 ?s",
 "P30_Lstar": r"L\*",
 "P31_PcVALID": r"(?i)Pc[ _]?VALID",
 "P32_launch_commit": r"(?i)launch[- _]commit",
 "P34_PNR": r"PURGE NOT RUN",
 "P35_unpurged": r"(?i)proceeds unpurged|relight unpurged|unpurged relight",
 "P36_no_later": r"(?i)no later than",
 "P38_budget_nums": r"4\.453|5\.268|3\.707",
 "P39_0p10kg": r"0\.10? ?kg",
 "P40_275m": r"\b275 ?m\b",
 "P41_trim": r"(?i)\btrim\b",
 "P42_HARD": r"\bHARD\b",
}
MARK = re.compile(r"SUPERSEDED|WITHDRAWN|NOT ADOPTED|NOT adopted|REFUTED|REPLACED|HISTORY|[Ss]uperseded|[Ww]ithdrawn|[Rr]efuted|[Rr]eplaced\b")
def anc_marked(p):
    pl = p.lower()
    return ("superseded" in pl) or ("history" in pl)
res = {}
for name, pat in PAT.items():
    rx = re.compile(pat)
    hits = []
    for p, v in flat:
        if not isinstance(v, str): continue
        for m in rx.finditer(v):
            if anc_marked(p):
                st, dist = "ANC", 0
            else:
                ds = [min(abs(mm.start() - m.start()), abs(mm.start() - m.end())) for mm in MARK.finditer(v)]
                dist = min(ds) if ds else None
                st = "MARK" if (dist is not None and dist <= 120) else ("FAR" if dist is not None else "NONE")
            hits.append((p, m.start(), st, dist, v[max(0, m.start() - 150): m.end() + 150]))
    res[name] = hits
    c = {}
    for h in hits: c[h[2]] = c.get(h[2], 0) + 1
    print(f"{name:20s} hits {len(hits):4d}  {c}")
# numeric leaves
print("numeric checks:")
for p, v in flat:
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        pl = p.lower()
        if ("pcf_tmax" in pl and abs(v - 0.8) < 1e-9) or (("h_target" in pl or "apogee_target" in pl) and abs(v - 300) < 1e-9) \
           or ("trigger" in pl and abs(v - 0.3) < 1e-9) or ("mass_est" in pl and abs(v - 0.01) < 1e-9):
            print("  NUM", p, v, "ANC" if anc_marked(p) else "")
if OUT:
    json.dump({k: [list(h) for h in v] for k, v in res.items()}, open(OUT, "w"), ensure_ascii=False, indent=0)
