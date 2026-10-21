"""Lead publication build of gnc.json v3.2 and DATASHEET-INPUTS-GNC.md v3.2 (2026-10-21).
Usage: python3 -I build_v32_publication.py OUTDIR --line N --stamp HH:MM:SSZ
Input: the lead's independent apply of the 34 REV-GNC-7 ops (lead_apply_inplace.json 236107a89ca4a240, byte-equal to the
reviewer trial fea33eacdd8a7d56 without its trial marker). Lead folds L1-L4 (header fields and four text-consistency
folds that reuse the reviewer's op 6 / 7 / 13 texts verbatim); DS ops 1-7 of the corrections file, then lead edits D1-D3."""
import json, sys, hashlib
P = "/tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/v32/"
H = "/home/claude/work/shared-fallback/engine/"
s16 = lambda b: hashlib.sha256(b).hexdigest()[:16]
out = sys.argv[1].rstrip("/") + "/"
LINE = sys.argv[sys.argv.index("--line") + 1]; STAMP = sys.argv[sys.argv.index("--stamp") + 1]
raw = open(P + "lead_apply_inplace.json", "rb").read(); assert s16(raw) == "236107a89ca4a240"
d = json.loads(raw)
corr = json.loads(open(H + "reviews/gnc/rev4b/data/b/rv7_v32_corrections.json", "rb").read())
op = corr["ops"]
def rep1(s, old, new, tag):
    c = s.count(old); assert c == 1, (tag, c); return s.replace(old, new)
# L1 status: publication header, and item (4) with the reviewer's op 6 / op 7 texts
st = d["status"]
st = rep1(st, "gnc.json v3.2 (2026-10-19): built as staging rev4b from gnc.json v3.1 (4f3209323b0e0ed4), a document change with no new flight (lead 227 (10)):",
 f"gnc.json v3.2 (2026-10-21): published by the lead at {STAMP} (CHANGELOG 258 (1) accepts REV-GNC-7; the publication is line {LINE}) after the independent delta re-check REV-GNC-7 (reviews/REVIEW-GNC-R5.md; PUBLISHABLE WITH CORRECTIONS, 0 BLOCKING), with its 34 corrections applied (reviews/gnc/rev4b/data/b/rv7_v32_corrections.json f7c0c6051efd5a08). Built 2026-10-19 as staging rev4b from gnc.json v3.1 (4f3209323b0e0ed4), a document change with no new flight (lead 227 (10)):", "L1 header")
st = rep1(st, "and 227 (2)-(9); the lead publishes. WHAT THE NUMBERS ARE", "and 227 (2)-(9). WHAT THE NUMBERS ARE", "L1 publishes")
st = rep1(st, "Electronics v2.11 carries 0.8 s into its S17 sweep and confirms it or returns it to the lead;",
 op[6]["new"].rstrip(".") + ";", "L1 op6 text")
assert op[7]["old"] in st
st = rep1(st, op[7]["old"], op[7]["new"], "L1 op7 text")
d["status"] = st
# L2 mode3_filter_reinit with the reviewer's op 13 text
m3 = d["flight_software"]["rev4b_entries"]["mode3_filter_reinit"]
m3["v"] = rep1(m3["v"], op[13]["old"], op[13]["new"], "L2")
# L3 item status notes (pattern of op 30)
note = ("text superseded where it has Electronics v2.11 confirm or return 0.8 s, implement or run S17, or state the frame-noise budget: "
        "S17 v2.11 CONFIRMED 0.8 s for the W10 < 6 m/s envelope (227 (5)) with conditions (requirements.ignition.relight_conditions.s17_v2p11_conditions); "
        "FC frame-noise budget <= 2.51 N rms iid at 0.8 s; GNC re-runs the R2 v2 statistics with the flush (open_items[47]) (lead fold L3, line " + LINE + ")")
for i in (6, 14):
    it = d["v32_items_rev4b"]["items"][i]; assert "status_after_rev_gnc_7" not in it; it["status_after_rev_gnc_7"] = note
# L4 header fields
assert d["version"] == "v3.2"; d["date"] = "2026-10-21"
d["supersedes"] = d["supersedes"] + "; v3.1 archived as 01-systems-gnc/superseded/gnc_v3.1_4f3209323b0e0ed4.json"
pn = d["publication_note"]; assert "published_v3p2" not in pn
pn["published_v3p2"] = ("Published by the lead 2026-10-21 at " + STAMP + " (CHANGELOG " + LINE + "; REV-GNC-7 accepted in 258 (1)): the staging rev4b candidate "
 "01-systems-gnc/staging_v3.1/rev4b/v32/gnc_v3.2_rev4b.json (43d58c4aff164b86) with the 34 REV-GNC-7 operations of "
 "reviews/gnc/rev4b/data/b/rv7_v32_corrections.json (f7c0c6051efd5a08), applied independently by the lead (scratchpad apply_rv7_lead.py) and "
 "byte-equal to the reviewer trial gnc_v3.2_rv7_trial.json (fea33eacdd8a7d56) without its trial marker (236107a89ca4a240); then the lead folds "
 "L1 (this header, the status date and the status item (4) sentences replaced by the texts of ops 6 and 7), L2 (flight_software.rev4b_entries."
 "mode3_filter_reinit.v with the text of op 13), L3 (status_after_rev_gnc_7 on v32_items_rev4b items 6 and 14) and L4 (date, supersedes, this note). "
 "t10_postcheck v3 --publication --rv7 exits 0 on the published file. Simulation and analysis evidence only; nothing here is physical approval.")
js = json.dumps(d, indent=1, ensure_ascii=False).encode()
open(out + "gnc.json", "wb").write(js)
print("gnc.json v3.2", s16(js), len(js))
# DATASHEET-INPUTS-GNC.md
ds = open(H + "01-systems-gnc/staging_v3.1/rev4b/DATASHEET-INPUTS-GNC.md", "rb").read(); assert s16(ds) == "9aacdefaaa0df250"
t = ds.decode()
for k, o in enumerate(corr["datasheet_ops"]):
    t = rep1(t, o["old"], o["new"], f"DS {k+1}")
# D1 title, D2 basis paragraph
t = rep1(t, "# DATASHEET-INPUTS-GNC (rev4b, 2026-10-19)", "# DATASHEET-INPUTS-GNC (gnc.json v3.2, published 2026-10-21)", "D1")
t = rep1(t, "**The basis is the candidate gnc.json v3.2,** `01-systems-gnc/staging_v3.1/rev4b/v32/gnc_v3.2_rev4b.json` (43d58c4aff164b86). It folds the lead decisions of CHANGELOG lines 204-227 and the REV-GNC-6 corrections. The lead has not published it yet.",
 "**The basis is the published gnc.json v3.2,** `interfaces/gnc.json` (" + s16(js) + ", published by the lead 2026-10-21, CHANGELOG " + LINE + "). It is the candidate `01-systems-gnc/staging_v3.1/rev4b/v32/gnc_v3.2_rev4b.json` (43d58c4aff164b86) with the REV-GNC-7 corrections (reviews/REVIEW-GNC-R5.md) and the lead folds L1-L4 (publication_note.published_v3p2). It folds the lead decisions of CHANGELOG lines 204-227, the REV-GNC-6 corrections and the REV-GNC-7 folds of lines 250 (6), 253 (7), 256 (2), 257 (2) and 258. This file is the rev4b file (9aacdefaaa0df250) with the REV-GNC-7 datasheet operations DS 1-7 and rows 11m-11q added by the lead.", "D2")
# D3 rows for the new open items 53-57, after row 11l
anchor = "| 11l | Open item: B1 cap |"
i = t.index(anchor); j = t.index("\n", i) + 1
rows = (
"| 11m | Open item: FC Pc branch (OI-FC-PC-BRANCH) | The FC Pc branch of the release predicate (Pc valid AND Pc >= 300 kPa abs) releases every normal-family run at the E2 frame in S17 (Pc_f at E2 3.04 bar abs), including runs that flame out 1-50 ms later outside R2. State the branch margin or move it, then re-fly the release statistics. | SIM (Electronics v2.11 S17) | REV-ELEC-3 R3-04 | **Owner:** GNC / FC owner; v3.2 `open_items[53]` |\n"
"| 11n | Open item: photodiode view (OI-PHOTODIODE-VIEW, HIGH) | pcf_tmax 0.8 s (W10 < 6 m/s, 227 (5)) holds on the dead side only with the photodiode main-chamber view (FLAMEOUT_OPT armed) or the GNC reference re-taken at the ECU E2 / light; photodiode-blind families release 42 / 98 of 1000 dead runs at 0.8 s. Closes at IGN-1. | SIM (S17) | REV-COMB-4; Electronics v2.11 | **Owner:** Combustion / Mechanical (view); GNC (reference option); v3.2 `open_items[54]` |\n"
"| 11o | Open item: lit-side F_min (OI-FMIN-LIT) | At the 0.21776 mm start-level lift 3 of 72 P4c corners never reach 37.16 N within 0.8 s (F_min 33.14 N): a lost relight in the Pc-invalid branch. 37.16 N and 0.8 s are kept. The start-level lift is TO-VERIFY at CF-3. | SIM; TO-VERIFY (CF-3) | 230 (4)-(5); REV-COMB-4 R4-03 | **Owner:** GNC / lead; Combustion (CF-3); v3.2 `open_items[55]` |\n"
"| 11p | Open item: C1 thermal zero (R3-01, REV-ELEC-3 MAJOR) | The C1 transducer thermal zero is not in the re-zero / BASE limits: a negative drift loses the A1 relight (PC_SENSOR), with drogue descent and vehicle loss. GNC's A1 P does not include it. The maximum coefficient is MISSING (F-10). | DERIVED (REVIEWER); MISSING (F-10) | lead 253 (7)(iii) HELD | **Owner:** Electronics v2.12; Mechanical (seat node); founders (F-10); GNC (re-fly); v3.2 `open_items[56]` |\n"
"| 11q | Open item: purge condition (d) | kPurgeFlow_s and the both-open cap are re-set from the CF-4 / B-BLEED-1 measured N2O Cd x A (upper 95 % bound) with the mass flow at 297.15 K, never above 2.43 / 2.39 s, and CF-4 shows the 283.15 K need at the re-set flow. Without the re-set: measured Cd x A <= 1.08 x the Cd 0.70 value, or GNC re-runs the A1 reserve test at the measured vent. | REQ (lead 257 (2), 258 (2)) on DERIVED | REV-GNC-7 RV7-04 | **Owner:** Combustion / Electronics (CF-4, constants); GNC (reserve test if needed); v3.2 `open_items[57]` |\n")
t = t[:j] + rows + t[j:]
db = t.encode()
open(out + "DATASHEET-INPUTS-GNC.md", "wb").write(db)
print("DATASHEET-INPUTS-GNC.md", s16(db), len(db))
