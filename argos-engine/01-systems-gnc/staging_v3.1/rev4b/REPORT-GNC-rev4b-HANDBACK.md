BEGIN GNC-REV4B-HANDBACK

(Re-sent at the harness's request. Since the first send, B02 has finished (17 of 24 variants) and I stopped my log monitor bqh3gnly2. Everything else is unchanged.)

STATUS: deliverable 1 is done and staged. Deliverable 2 is 17 of 24 variants done and still running in the background, not staged. Deliverable 3 is drafted in the work area, not staged. The CHANGELOG line is NOT appended (proposed text below). Nothing installed; interfaces/gnc.json not written; rev1-rev4 untouched.

STAGING LOCATION (my choice): hub 01-systems-gnc/staging_v3.1/rev4b/

== CLAIMS ==

D1. gnc.json v3.2 candidate: STAGED in rev4b/v32/ and rev4b/withdrawn_markers/.
- Built by m2_gnc_json_v32_rev4b v1.0 from interfaces/gnc.json v3.1 (4f3209323b0e0ed4). It is a document change with no new flight.
- It folds RV6-01 to RV6-14 with the exact review texts and lead lines 227 (2)-(9), plus 204, 208, 213, 214, 219 and 222. An independent check confirms every RV6 text and lead quote is present and every replaced old text is gone.
- Line 222: icd_inputs_for_airframe is kept as engine data and open items.
- Line 227 (2): the 223 (5) J reading is not carried. It appears only inside the verbatim copy of line 227, marked WITHDRAWN.
- Decided state in the text:
  - ENG-11 is the RV6-01 wording plus the RV6-14 sentence.
  - Landing mass: nominal planning touchdown <= 16.15 kg; above that a paired arm is needed; lower bounds unchanged; 14.18-18.13 kg is a record only.
  - pcf_tmax is 0.8 s for W10 < 6, scoped per RV6-08.
  - The mode-3 filter is re-initialised at the Pc-invalid onset (Electronics implements it).
  - RE-24: the GIMBAL_FAULT abort is NOT inhibited near touchdown.
  - The 210 m gate-delay arm is a GNC open item before flight acceptance.
  - The line-213 duty-cycle correction and the RV6-09 payload record are in.
- Withdrawn values carry markers: *_superseded_rev4b keys, inline [SUPERSEDED rev4b: ...] markers and SUPERSEDED (rev4b; ...) list prefixes.
- RV6-10: a new sidecar for rev3_results.json.
  - W2 now has 60 leaves: the 32 from rev4, the 27 lit_k100_hold leaves, and hold_trace_lit_k875 (kept as a code fact only).
  - The RV6-10 ranges 52.39-60.30 N and 59.5-65.3 N equal the target values.
  - Beyond the RV6-10 list, for consistency, W1 adds release_hold_0p22.
  - A rev4b WITHDRAWN_INDEX points to the rev4 index.
- Checks:
  - Two builds give identical bytes (candidate, diff, keydiff, corrections log).
  - Self-check: 132 hits, 0 unmarked; structural 15/15.
  - Keydiff: changed 41, added 76, removed 4; open_items 42 -> 53.
- The status text states SIM / DERIVED / ASSUMED / DATASHEET / TO-VERIFY and that nothing is physical approval.
- t10_postcheck v2 --publication exits 1 with 8 critical hits, all C06 "pcf_tmax 0.8 s". C06 encodes the v3.1 NOT-ADOPTED state that 227 (5) reverses, so the reviewer needs to update C06. I did not reword the texts to pass it. numeric_300 is 0 and required_failed is 0. My reading is in v32/logs/t10_postcheck_rev4b_reading.json.

D2. ENG-11 FE-plant re-run (RV6-14 (a)-(e)): IN PROGRESS, 17 of 24 variants done. All results are DERIVED (linear, one fixed bench notch, K_s 90-160 in steps of 5, edges known to ±5 N m/rad; "<=90" and ">=160" are the grid limits).
- The check passed. It reproduces REV-GNC-6 v05 part B on V5c exactly, the two-mass limits pass, and the kinematic g equals V5c's within 2.36 %.

| Plant / variant | Both-axes window (N m/rad) | Edge that sets it |
|---|---|---|
| V5c A12 (v3.2 basis) | 100-130 (reproduced) | lower: beta max-q fins corner at 95; upper: alpha coincidence at 135 |
| V5c, bending x0.9 (C03) | none | |
| V5c, bending x1.1 (C04) | 95->=160 | |
| FE J 1.6e-3 cons, rigid T_REF (A01) | <=90-120 | top: alpha at 125 (full tank, max 500 N, fast actuator, no aero; rocking mode 24.06 Hz in the bending band; e 0.95, zeta 0.02; GM 5.94, block min 5.61 dB) |
| FE + stop poses (A08) | <=90-120 | both axes fail at 125 |
| FE hot E -10 % (A05) | <=90-130 | |
| FE compliant airframe (A06) | <=90-135 | |
| FE compliant + hot E -10 % (A07) | <=90-140 (and 160) | |
| FE with FEA3D g (B04) | <=90-130 | non-conservative by 10 |
| FE J 0.76e-3 cons (A02) | 130->=160 | lower: beta coincidence at 125, GM 5.95 |
| FE J 2.7e-3 cons (A03) | 120->=160 | lower: beta max-q corner at 115, 18.0 Hz, zeta 0.10, GM 5.98 |
| FE n48, J 1.6e-3 (B01) | none | beta coincidence at every K_s |
| FE n48, J 2.7e-3 (B03) | none | |
| FE n48, J 0.76e-3 (B02) | finished, not yet summarised | |
| FE two-mass rotor (B07) | 150->=160 | |
| FE bending x0.9 (C01) | none | some corners unstable |
| FE bending x1.1 (C02) | <=90->=160 | |

- No K_s passes for all three J values together.
- Cause: the FE centre stiffness is +11 % / +24 % above V5c, so the full-tank pose envelope reaches the 24.14-24.71 Hz bending band at K_s 125 / 129 instead of 132 / 156.
- Still pending: A04, A07o, A09, A10, A11, B05, B06.
- Proposed datasheet sentence (PROVISIONAL until those 7 are in): "ENG-11 servo output stiffness K_s: design-to 100-120 N m/rad at the nominal servo J 1.6e-3 kg m2 (cons). This is the V5c window intersected with the CAD v3.5.1 FE window (DERIVED, linear ENG-07d, one fixed ECU notch). It is not robust: it moves with J (0.76e-3: 130->=160; 2.7e-3: 120->=160), the inertia convention (n48: none) and the rotor model (two-mass: 150->=160), and it is empty at 0.9x bending. K_s is frozen only on an ENG-07d PASS with the B-TVC-1 measured K_s, J, convention and rocking modes and the measured or airframe-FE bending mode. On a FAIL the notch set changes first (227 (3))."
- Finding for FEA3D / Mechanical: FEA3D's post_k servo factor is low off-centre (g_kin / g_fea 1.085-1.339 on the 7 deg cone, 1.103-1.587 at the 8 deg stops). Its "with servo" stiffnesses overstate the window top.

D3. DATASHEET-INPUTS-GNC.md: DRAFTED, not staged, at /home/claude/work/space/out/rev4b/datasheet/DATASHEET-INPUTS-GNC.md.
- One table: 10 headline rows plus 12 open-item rows with owners. Row 8 (ENG-11) is still a placeholder.
- Headline rows:
  - A1 210 m (REQ 213/214/227 (1) on SIM; liq -25/+20, p 0.551, UB95 0.802 pp; N=1000 per main base).
  - B1 cap 62 m PROVISIONAL (P 0.996 at N=500, ledger v3d; not re-flown at v3.5.1).
  - Landing P 0.9835 pooled (0.984 / 0.983; N=1000 per base; liq|G73; v3.5.1).
  - T/W at liftoff 2.92, touchdown 3.16, floor ratio 0.633 (DERIVED).
  - Gimbal: ±7 deg command, 8 deg stop; slew >= 100 deg/s at 7 deg / 7.4 V; 34.9 rad/s2; >= 8 Hz.
  - Landing mass <= 16.15 kg.
  - Payload: 0.5 kg at 190 m; 1 kg only with the 2.20 kg tank (A1 engine-on p99 8.92 / 8.71 s, max 9.24 s > 8.258 s), TO-VERIFY.

NOT DONE:
- The last 7 ENG-11 variants and the final summary.
- eng11_fe staging and its MANIFEST.
- Datasheet row 8 and staging the datasheet in the hub.
- The top-level MANIFEST_rev4b.
- CHANGELOG line 229.
- The 210 m gate-delay arm (not flown, per "NOT NOW").

STILL RUNNING (my processes, nice 10, kill by PID only if needed):
- Queue P1: bash 3175 / 3178, python 3182.
- Queue P3: bash 3349 / 8556, python 8558 (m2_eng11_fe_q.py).
- The log monitor is stopped.
- Both queues exit by themselves after the last variant, expected about 23:30-23:45Z. They write only to /home/claude/work/space/out/rev4b/eng11_fe/ and out/rev4b/logs/.
- The one numpy overflow RuntimeWarning per process is benign; it also appears in the check that reproduces v05 exactly.

TO FINISH (successor):
1. Wait until both out/rev4b/logs/eng11fe_run_P1.log and _P3.log contain "EXIT".
2. Run: cd /home/claude/work/space/gnc_dev3/scripts && GNC_E11FE_OUT=/home/claude/work/space/out/rev4b/eng11_fe /opt/engine-venv/bin/python -I m2_eng11_fe_summary.py > ../../out/rev4b/logs/eng11fe_summary.log
3. Stage with: bash /tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/stage_eng11fe.sh
4. Fill datasheet row 8 from the summary's proposal and matrix_detail, then stage the datasheet as rev4b/DATASHEET-INPUTS-GNC.md (use .txt if the .md write is refused).
5. Stage out/rev4b/notes/PROGRESS.txt to rev4b/rev4b_notes/.
6. Build MANIFEST_rev4b.sha256 with the tmp file outside the folder, then run sha256sum -c.
7. Append the CHANGELOG line: assert 228 lines first, read it back after 10 s.

== FILES (sha256/16) ==

Staged in hub 01-systems-gnc/staging_v3.1/rev4b/:

| File | sha16 |
|---|---|
| v32/gnc_v3.2_rev4b.json | 43d58c4aff164b86 |
| v32/gnc_v3.2_rev4b_vs_v3.1.diff | f223df0dfaf8f736 |
| v32/gnc_v3.2_rev4b_keydiff.json | 9c15a392574cd511 |
| v32/v32_corrections_log_rev4b.json | 8044476e09d9aeef |
| v32/scripts/m2_gnc_json_v32_rev4b.py | cbb4d11f9c52c63e |
| v32/scripts/m2_rev4b_wmark.py | 4b423851442b6487 |
| v32/logs/builder_run5.log | 545e8a2b0114738e |
| v32/logs/builder_run6_repro.log | 7386fa4b7b312e74 |
| v32/logs/t10_postcheck_rev4b.json | a8bec3b39c539df9 |
| v32/logs/t10_postcheck_rev4b.log | 61284e6cde227c3e |
| v32/logs/t10_postcheck_rev4b_reading.json | 9add730b30235d3b |
| v32/logs/wmark_run1.log | ba56b473390c145f |
| v32/logs/wmark_run2_repro.log | 8e2adec3dbdfcba3 |
| withdrawn_markers/WITHDRAWN_INDEX.json | a47bb1371dfbbea3 |
| withdrawn_markers/results/rev3_results.json.WITHDRAWN.json | ab7263582cfd207a |
| v32/MANIFEST_v32_rev4b.sha256 (15 files, -c OK) | b98396533551b26e |

Work area, not staged:

| File | sha16 |
|---|---|
| gnc_dev3/scripts/m2_eng11_fe.py v1.0 | fab0f05eb87d8e61 |
| gnc_dev3/scripts/m2_eng11_fe_q.py | cd342564440c9d73 |
| gnc_dev3/scripts/m2_eng11_fe_summary.py v1.0 | not recorded |
| out/rev4b/eng11_fe/eng11fe_*.json | being written |
| out/rev4b/datasheet/DATASHEET-INPUTS-GNC.md (draft) | not recorded |

Dependencies are byte-identical to the staged rev4/sim/gnc_dev3_sim6_v2.9-dev copies:

| Dependency | sha16 |
|---|---|
| m2_eng11.py | aaad9a07a0551b9b |
| m2_csi.py | 2928d4decb6eac03 |
| m2_csi_v3.py | edd32bb4c3fbff79 |
| gncsim | 16 files, identical |
| iface_v351 | identical |
| pins_rev4_v351 | cf6d8d010833a274 |

== CHANGELOG LINE (NOT APPENDED; file is still 228 lines, 4ab6945a31b8cc01) ==
2026-10-19 | gnc | (result) | GNC rev4b deliverable 1 STAGED for the REV-GNC document diff (not gnc.json; document change, no new flight; SIM / DERIVED / ASSUMED, no hardware data, not physical approval): staging_v3.1/rev4b/v32/MANIFEST_v32_rev4b.sha256 b98396533551b26e (15 files, sha256sum -c OK); candidate gnc_v3.2_rev4b.json 43d58c4aff164b86 (v3.2 from v3.1 4f3209323b0e0ed4; diff f223df0dfaf8f736; keydiff changed 41 / added 76 / removed 4; open items 42 -> 53) folding RV6-01..RV6-14 verbatim and lead 227 (2)-(9), 204, 208, 213, 214, 219, 222; builder deterministic (2 runs identical); self-check 0 unmarked, structural 15/15; t10_postcheck v2 --publication C06 x8 only (pcf_tmax 0.8 s: the v3.1 NOT-ADOPTED state reversed by 227 (5)), numeric_300 0, required 0; RV6-10 sidecar ab7263582cfd207a (W2 60 leaves). ENG-11 FE re-run in progress (DERIVED, 17/24): FE J 1.6e-3 cons <=90-120 N m/rad (top: alpha bending coincidence at 125), V5c 100-130 reproduced; J 0.76e-3 130->=160, J 2.7e-3 120->=160, n48 none, two-mass 150->=160, bending x0.9 none. Nothing here is physical approval | 01-systems-gnc/staging_v3.1/rev4b/; why: lead 227 (10)

== OPEN ITEMS (owner) ==
1. 210 m gate-delay arm (about 16,000 flights) and the canopy deploy-to-inflation bound, before flight acceptance (227 (8)). Owner: GNC (arm); recovery / airframe with GNC (bound).
2. ENG-11 FE re-run: finish the last 7 variants, stage, then the REV-GNC delta check and the lead's datasheet sentence. Owner: GNC, then the reviewer, then the lead.
3. B-TVC-1 bench: K_s with its uncertainty, J, the reflected-inertia convention and the rocking modes; K_s frozen only on an ENG-07d PASS. Owner: founders / Electronics; GNC re-runs.
4. Airframe first bending mode, measured or from the airframe FE (10 Hz is not consistent with ENG-07d). Owner: airframe work (deferred, line 222); GNC re-runs.
5. Second ECU notch study (research proposal). Owner: GNC.
6. Mode-3 filter re-initialisation, S17, the FC frame-noise budget and pcf_tmax 0.8 s confirmation. Owner: Electronics v2.11. Lit side: Combustion v2.4b. Then GNC re-runs R2 v2.
7. 2.20 kg tank B1 / thermal / erosion check. Owner: Combustion / Mechanical.
8. 210 m coverage set and A1 duty-cycle record. Owner: GNC.
9. Sim relight start level 100 N vs 62.5 N. Owner: GNC.
10. GIMBAL_FAULT revisit when a jam rate exists. Owner: lead; Electronics / founders; GNC.
11. Delivered slew at 7 deg / 7.4 V with exact kinematics (DERIVED 97.8-111.2 deg/s). Owner: Mechanical / Electronics.
12. B1 cap final after T1-T4. Owner: lead with Combustion data. B1 is not re-flown on v3.5.1. Owner: GNC.
13. t10 C06 rule update for v3.2. Owner: REV-GNC reviewer.
14. FEA3D post_k servo factor correction. Owner: FEA3D / Mechanical.

END GNC-REV4B-HANDBACK