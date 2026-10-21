"""J-FWD: TC-01 wall relaxation, screw plastic set and the no-slack check over two consecutive firings.
Mechanical, 2026-10-21, v8 (v7 82221fdf0035f338 / json 345e27062d54ad20 kept as jfwd_relax_v352_v7.py; v6 9465eaeac9af407f / json
b157ebc2027833e4 kept as jfwd_relax_v352_v6.py; v5 95409d512c83bb44 ACCEPTED by the lead 12:52Z
and kept as jfwd_relax_v352_v5.py; v4 80e1df3323c19340 kept as jfwd_relax_v352_v4.py; v3 48c2ab7d2698bb2f kept as jfwd_relax_v352_v3.py and
imported for the shared joint machinery: Screw, state_s, u_install, the rev-4 row histories, engmat tables).

v8 (lead 2026-10-21T05:50:45Z re-map brief, rulings R1-R8; CHANGELOG 249, 250, 252): the re-map ONCE on FEA3D-2's FINAL envelope v6,
hub 04-fea/assembly3d_v352/results/v352/jfwd_soak_envelope_v352_v6.json 43a5d78b67c615fc (script ac75b2c41146aead), with the input record
results/v352/jfwd_v7inputs_cD_v352.json 5a41c8d74897bdda (md 424146c89c8c9f01, script 0cc1c2bf2d3f0092) [SIM / DERIVED / CALC; none of it
is physical approval].
 - INSTANCES (hub jfwd_patches; every file read is sha16-asserted): js5, (a), (a'), (a''), (b2), (b2) rep and, new, (b1) = seat_s9L12_mu02A
   (s9, R0.2, mu 0.2) with (b1) rep (its SOAK_rep / SOAK52_rep), (b2') = seat_s9L12_mu0 (s9, R0.2, mu 0) and (cD) = seat_sDL12_mu0 (sD,
   FINAL TC-01 d11.2, mu 0).  Screw moments from shank.json for (b2), (b1), (b2'), (cD) (equal to runcmp 'A' where both exist; asserted).
 - C1 (R3; lead 01:30:18Z (5)): (b1)'s seat line d+6.051 z'0 = as solved x ratio_floored (s6 / s9 at mu 0, that line and state) from
   results/v352/jfwd_b1_meshcorr_v352.json adac16afd42ef7bd, MS = 2 Fty(T) / PmPb - 1 (checked); (b2') as solved.  s6 + C1 stand and the
   anchors are FINAL (cD / s6 0.927 / 0.947 / 0.966 / 0.959 / 0.985 in PRELOAD / SOAK52 / SOAK / SOAK70 / FA1S).  cD's LOCAL values (seat
   line, ring family, under-head band) are recorded BESIDE, not entered; cD's resultants (head, plane and section forces, seat window, seat
   radial force, screw moments) enter as solved (worst-of), as in v6.
 - MF NOTE (R4): the seat-line P+Q is NOT shown mesh-converged (s9 -> s6 +12 to +18 %, s6 -> cD -1.5 to -7.3 %, not monotonic); it is
   quoted as found; extrapolations are information only.
 - ring family: (b1), (b2'), (cD) carry the drawn R0.2 edge, so (as (b2) in v7) the ring-family P+Q IS the seat line.
 - the per-state envelope here (v7 convention: the repeats are instances) is ASSERTED equal to the record's v7_convention view (9 numbers,
   M_max_at_x and 7 'from' fields per state, FEA3D-2's tolerances) and to v6's per-instance N_plane / seat window / seat line.
 - CAD BASIS (R8): every J-FWD FE except cD is on the interim TC-01 (history/ENG-TC-01.step.1ad07e472709b1b2, d10.5 flats); the final
   part fcb3b5b93bebdb01 (d11.2) removes 104.037 mm3, the wall at the hole (2.688 mm) is unchanged and the head footprint is inside both
   flats: the effect is ASSUMED small.
 - the moves against v7 are in 'v7_to_v8_moves'.

v7 (lead 15:37Z (b2) rulings R1-R3 and order item 1, plan ACCEPTED 15:41Z): FEA3D's (b2) = seat_s6L12_mu0 (mesh s6 with the drawn R0.2
bore-side edge break, L12, mu 0, 3750 N, FIT 0.078, A4-80; step order SEAT-PRELOAD-SOAK52-SOAK-SOAK70-FA1S-SOAK_rep-SOAK52_rep) joins as the
FIFTH history; its repeats SOAK_rep / SOAK52_rep are further INSTANCES of SOAK / SOAK52 (entered from FA1S / SOAK_rep).  R1: the adopted
envelope is the worst of sharp + (b2) per state and quantity, 'worst computed instance, not a proven bound'.  R2: the FA1S arm stays CALC
1.120 (FE 0.724 information).
 - k_b bracket: hi re-calibrated on (b2) SOAK70 7471.8 N (v6 hi (a) 6389.1); lo stays on the lowest SOAK70 instance.
 - SEAT-LINE / RING-LINE RE-ARBITRATION: in (b2) the governing line is d+6.051 z'0 in every state and the contact ring sits on it, just
   past the end of the break (FEA3D 15:37Z relay).  The ring family therefore takes, for the (b2) instances, the d+6.051 z'0 P+Q (the
   ring IS on the seat line); its d8.02 z'3 line is carried as information.  Both families stay in the output.
 - screw moments of (b2) from its shank.json (patch values, the runcmp 'A' column where both exist; the repeats are only in shank.json).
 - ENVELOPE (lead 15:55Z): FEA3D's ADOPTED v3, results/v352/jfwd_soak_envelope_v352_v3.json 0872de4ea7e3601d (instances sharp js5 / (a)
   / (a') / (a''), R0.2 (b2) and '(b2) rep'), cross-checked here instance by instance (N plane, window, seat line d+6.051 z'0).  Basis,
   verbatim: "worst of the computed histories and edge forms (sharp, R0.2); the contact solution depends on the predecessor state, so
   this is the worst computed instance, not a proven bound".  v2 jfwd_soak_envelope_v352.json 336568296bdb896f (sharp only) and v1
   1d970741cb95a885 are superseded records.
 - LABEL (lead 16:07Z (3)): the IN718 case key reads 'IN718 M5 flight L 10.2 +/-0.1 (RULED, ENG-HW-101-IN718; k_b calibrated on the FE
   L 10.0, length effect ASSUMED small)' (was 'IN718 M5 x10 (RULED, ENG-HW-101-IN718)'); IN718 k_b = the A4-80 calibration x E ratio
   (hi 1,061,522 x 1.0363 = 1,100,023 N/mm; lo 403,723 x 1.0363 = 418,365 N/mm).
v6 notes follow.

v6 (lead relay 13:14Z item 1: FEA3D's (a'') = seat_s5L12_mu0_go, the full-width L12 patch, a third sharp-edge footprint; envelope
results/v352/jfwd_soak_envelope_v352.json 336568296bdb896f, was 1d970741cb95a885):
 - FOUR histories: js5, (a), (a'), (a''); (a'') runs js5's step order like (a') (SEAT-PRELOAD-SOAK70-FA1S-SOAK-SOAK52).  Every
   envelope quantity is the worst of the four, per state and per quantity (the v5 rule).
 - the PRELOAD screw moment envelope rises to (a'')'s value (FEA3D: 744.8 N mm at x' 28.6; v5 651.5 (a')): the fibre / set check
   takes it; the cold end of the fibre range keeps the LOWEST PRELOAD moment (js5 298.7).
 - k_b bracket: lo is re-calibrated if (a'') SOAK70 lies below the v5 lo history ((a') 5627.3 N); hi unchanged unless above (a) 6389.1.
 - the model seat force against the lowest seat window per state (FEA3D window minima: SOAK70 1351.3 (a''), FA1S 1126.1 (a'')).
v5 notes follow.

v5 (lead relay 12:28Z: FEA3D's sharp-edge soak envelope changed at 12:21Z, results/v352/jfwd_soak_envelope_v352.json 1d970741cb95a885):
 - THREE histories: js5, patch (a) seat_s5L8_mu0 and patch (a') seat_s5L8_mu0_go (same patch, js5's step order and SEAT d1 0.05; it
   reproduced js5 only at SOAK70 and FA1S: the sharp corner depends on the increment path too).  Every envelope quantity is the worst
   of the three, per state and per quantity (SOAK52 N max 6742.0 (a'), SOAK seat line MS -0.035 (a'), SOAK70 N min 5627.3 (a')).
   Patch (a'') (L12) joins only when the lead sends its delta (flag --with-a3 reads it if its posts exist).
 - k_b BRACKET WIDENED (lead 12:28Z item 2): (a') SOAK70 5627.3 N lies below js5's 5694.7, so k_b,lo is calibrated to the LOWEST SOAK70
   head force over the histories and k_b,hi to the highest (patch (a) 6389.1 N); the 24-case runs at both ends, the worse is quoted.
 - c per family folds the (a') states in (worst-history P+Q over the model F_sh); the tilt basis takes the (a') soak points and the
   PRELOAD moment envelope over the three histories (max for the fibre / set check; the LOWEST PRELOAD moment for the cold end of the
   fibre range, shakedown and LCF: the histories differ 2x at PRELOAD, 298.7 js5 / 318.8 (a) / 651.5 (a') N mm); N_ratio over the three.
 - NEW: the seat-line (and ring-line) P+Q select-fit band re-sized on the envelope (information for the fix ruling): per soak state
   P+Q(g, F_V) = P+Q_env(state) x F_sh,model(IN718, g, F_V) / F_sh,model(A4-80, 0.078, 3750), both k_b ends, 3750 and 4096 N.

v4 notes follow (unchanged where not superseded above).  CALC on SIM temperatures and SIM (FEA3D) calibration states; every number
DERIVED unless tagged.  H8 / f7 stays (lead 08:40Z).

v4 (lead 11:25Z items 1-4, lead 11:41Z):
 - SCREW RULED: IN718 M5 x10, ENG-HW-101-IN718 (AMS 5662 bar aged to AMS 5663, ISO 7380-1 form).  A4-80 is WITHDRAWN for J-FWD (its rows
   are information); M6 A4-80 is the FALLBACK (ESTIMATE rows, not a passed design).
 - FE inputs: the COMPLETE js5 run (hub jfwd_interim relax / seatforce / screw_bend / cells) and FEA3D's seat patch (a) seat_s5L8_mu0
   (run dir, read only): same mesh s5, mu 0, 3750 N, FIT 0.078, cut boundary driven by js5; step order SEAT-PRELOAD-SOAK52-SOAK-SOAK70-FA1S
   against js5's PRELOAD-SOAK70-FA1S-SOAK-SOAK52.  The patch reproduces js5 within 5 % at PRELOAD and FA1S; at the soak steps the state
   depends on the step history (sharp-corner penalty-contact non-uniqueness, lead 11:41Z).  RULED: until a history-robust model exists,
   every sharp-edge soak quantity is the WORST of the two histories, per state and per quantity: the highest screw N (SOAK 7383, SOAK52
   6560, SOAK70 6389), the lowest seat window force, the lowest MS per line, and (here) the highest screw section moment.
 - k_b BRACKET (lead 11:41Z): k_b,lo = the v3 calibration to js5 SOAK70 (head force 5694.7 N); k_b,hi = calibrated the same way to the
   patch SOAK70 (head force 6389.1 N; seat 2318.1 N main cluster, 2385.0 N window, 2430.0 N along n).  Every 24-case check runs at both
   ends and the worse is quoted.
 - model check against BOTH histories at SOAK70 / SOAK / SOAK52 (model = history free: one value per state).
 - c (P+Q per unit model shell pull) per family and per k_b end = the max over PRELOAD / SOAK70 / SOAK / SOAK52 of the worst-history
   FE P+Q divided by the model's F_sh at that state (seat line d+6.051 z'0; ring line d-8.126 z'3 with the patch's d-8.02 z'3 beside it).
 - TILT MOMENT (v4 basis 'Fc'; the v3 basis linear in the capped shell pull is WITHDRAWN: at SOAK / SOAK52 js5 carries 3849 / 2661 N mm
   at about the SOAK70 shell pull, where v3 gave 1281): soak moment = an upper-bound line in the seat contact force over the six soak FE
   points of both histories (max section moment along the shank, the threaded sections included), M_soak(F_c) = a + b F_c (b the
   least-squares slope, a raised until every point lies on or below the line); cold / preload moment M_pre(F_S) = the PRELOAD envelope
   moment x F_S / 3750; at a frame M = M_pre + w max(0, M_soak(F_c) - M_pre) with w = d_r / d_r(SOAK70) >= 0 (not capped above); the screw
   moment scales with the screw E (tilt ratio, as v3).  Fibre = N_ratio F_S / A_s + M / Z_3 with N_ratio the max section N / head force
   over all FE states of both histories.
 - shakedown, the fibre history for the screw LCF, embedding, the wall cap and the two-firing structure as v3.
Joint model (jfwd_embed_v352 head): F_sh = k_sh (g - s + d_r - u); F_c = k_c (-u) for u < 0; F_S = F_V + k_b (d_w - f - delta_p + u - u0);
equilibrium F_S = F_sh + F_c; F_S <= 0 = slack.  Frames: rev-4 B1 row histories at the J-FWD screw plane (v352_NF2b_R4_GVLO / _GVHI), every
frame, then a cold frame (20 C), two consecutive firings; embedding f_Z basis 8 / sensitivity 21 um; installations 2250 / 4096 N; gaps
0.040 / 0.059 / 0.078: 3 x 2 x 2 x 2 = 24 cases."""
import json, math, hashlib, sys, os, importlib.util
from pathlib import Path
import numpy as np

J = Path("/home/claude/work/mechanical/v352/jfwd")
OUT = J / "jfwd_relax_v352_v8.json"
V3 = J / "jfwd_relax_v352_v3.py"
_spec = importlib.util.spec_from_file_location("jfwd_relax_v352_v3", str(V3))
RV3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(RV3)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
state_s, u_install, Screw, A4_80, ROWS4, SRC4 = RV3.state_s, RV3.u_install, RV3.Screw, RV3.A4_80, RV3.ROWS4, RV3.SRC4
tab, kT, K_C, EMB, GAPS, INSTALL = RV3.tab, RV3.kT, RV3.K_C, RV3.EMB, RV3.GAPS, RV3.INSTALL
L_G, A_S, Z_3 = RV3.L_G, RV3.A_S, RV3.Z_3

HUBI = Path("/home/claude/work/shared-fallback/engine/04-fea/assembly3d_v352/jfwd_interim")
F_RELAX = HUBI / "js5_mu0_T3750_g078_relax.json"
F_SEATF = HUBI / "js5_mu0_T3750_g078_seatforce.json"
F_BEND = HUBI / "js5_mu0_T3750_g078_screw_bend.json"
F_CELLS = HUBI / "js5_mu0_T3750_g078_cells.json"
RUNS = Path("/home/claude/work/shared-fallback/engine/04-fea/assembly3d_v352/jfwd_patches")   # v8: the hub copies (FEA3D-2, CHANGELOG 252)
PATCHES = {"patch_a": RUNS / "seat_s5L8_mu0", "patch_a2": RUNS / "seat_s5L8_mu0_go", "patch_a3": RUNS / "seat_s5L12_mu0_go",   # v6: (a'') joins
           "patch_b2": RUNS / "seat_s6L12_mu0",
           "patch_b1": RUNS / "seat_s9L12_mu02A", "patch_b2p": RUNS / "seat_s9L12_mu0", "patch_cD": RUNS / "seat_sDL12_mu0"}   # v8: (b1), (b2'), (cD) join;                                                                                # v7: (b2) joins
LABEL = {"js5": "js5", "patch_a": "(a)", "patch_a2": "(a')", "patch_a3": "(a'')", "patch_b2": "(b2)", "patch_b2r": "(b2) rep",
         "patch_b1": "(b1)", "patch_b1r": "(b1) rep", "patch_b2p": "(b2')", "patch_cD": "(cD)"}
H = ("js5", "patch_a", "patch_a2", "patch_a3", "patch_b2", "patch_b2r", "patch_b1", "patch_b1r", "patch_b2p", "patch_cD")   # v8: FEA3D-2's order;            # v7: 'patch_b2r' = the (b2) repeat instances (SOAK_rep, SOAK52_rep)
REP = {"patch_b2r": ("patch_b2", {"SOAK": "SOAK_rep", "SOAK52": "SOAK52_rep"}), "patch_b1r": ("patch_b1", {"SOAK": "SOAK_rep", "SOAK52": "SOAK52_rep"})}
SHANK_MOMENTS = ("patch_b2", "patch_b1", "patch_b2p", "patch_cD")   # v8: screw moments from shank.json (the v7 treatment of (b2))
RING_ON_SEAT = ("patch_b2", "patch_b1", "patch_b2p", "patch_cD")    # drawn R0.2 edge: the ring-family P+Q is the seat line
LOCAL_EXCLUDE = ("patch_cD",)                                       # R3: cD's local values beside, not entered
C1_INST = ("patch_b1", "patch_b1r")                                 # R3: (b1)'s seat line at C1
MF_NOTE = ("the seat-line P+Q is NOT shown mesh-converged: s9 -> s6 +12 to +18 %, s6 -> cD -1.5 to -7.3 %, not monotonic, mesh and geometry "
           "not split (FEA3D-2, CHANGELOG 252 (1)); quoted as found; extrapolations are information only (lead R4)")
CAD_BASIS = ("every J-FWD FE except cD is on the interim TC-01 (history/ENG-TC-01.step.1ad07e472709b1b2, d10.5 flats); the final part "
             "fcb3b5b93bebdb01 (d11.2) removes 104.037 mm3; the wall at the hole (2.688 mm) is unchanged and the head footprint is inside "
             "both flats; the effect is ASSUMED small (lead R8; CHANGELOG 249 (11))")
PATCH_SHA = {   # v8: hub jfwd_patches files read, sha256/16 (FEA3D-2 publication, CHANGELOG 252)
    "seat_s5L8_mu0": {"seatforce.json": "881bd80f1f7e50f4", "compare.json": "57724671790d58e0", "shank.json": "412becc103964e88",
                      "runcmp_js5_mu0_T3750_g078.json": "bb4b1bf65698cf59", "meta.json": "7d83b099b59efc1b"},
    "seat_s5L8_mu0_go": {"seatforce.json": "31809993c76bdbba", "compare.json": "08fd149167aed345", "shank.json": "a9df8135a22c50f0",
                         "runcmp_js5_mu0_T3750_g078.json": "a9ded921af87e2a5", "meta.json": "893bb4314f5a962c"},
    "seat_s5L12_mu0_go": {"seatforce.json": "2866b53d2a0142d2", "compare.json": "5041b4179e3bb536", "shank.json": "06e7090b26995c9e",
                          "runcmp_js5_mu0_T3750_g078.json": "3cda6193a39c4a86", "meta.json": "02528aa52fd491a4"},
    "seat_s6L12_mu0": {"seatforce.json": "9eb36a729ef6b5a5", "compare.json": "727e10ba6c8fb41b", "shank.json": "280e383e5b87dd07",
                       "runcmp_js5_mu0_T3750_g078.json": "d3b1ec0ec36b25e6", "meta.json": "b333ee2994cc6fb0",
                       "envelope_candidate.json": "de99e3cd582d7f8f", "summary.json": "961b19102a002f6b"},
    "seat_s9L12_mu02A": {"seatforce.json": "553a0ed1cbe51548", "compare.json": "eba047e47f69e8af", "shank.json": "a7c05620613b091a",
                         "runcmp_js5_mu0_T3750_g078.json": "65dce4c6b8eeca3d", "meta.json": "806ecf80a7992d4f"},
    "seat_s9L12_mu0": {"seatforce.json": "722b28f49473b8dc", "compare.json": "0ae76ed185599268", "shank.json": "c402e74c125b5182",
                       "runcmp_js5_mu0_T3750_g078.json": "2ba6a90e8f45c033", "meta.json": "0cd19a44ade24b9f"},
    "seat_sDL12_mu0": {"seatforce.json": "52ab8f40fae1bb75", "compare.json": "c891db7dcb3445c9", "shank.json": "0ef43b2e27a72e8c",
                       "runcmp_js5_mu0_T3750_g078.json": "9388cce4e668e44d", "meta.json": "675917103538c9b3"}}
B2 = ("patch_b2", "patch_b2r")


def src_of(h, st):
    """(run key, step name) of instance h at state st; None where the instance does not exist (the repeats exist only at SOAK / SOAK52)."""
    if h in REP:
        base, steps = REP[h]
        return (base, steps[st]) if st in steps else None
    return ("patch_a" if h == "js5" else h, st)


def H_at(st):
    return tuple(h for h in H if src_of(h, st) is not None)


PATCH = PATCHES["patch_a"]
P_SEATF, P_CMP, P_RUNCMP, P_META = (PATCH / n for n in ("seatforce.json", "compare.json", "runcmp_js5_mu0_T3750_g078.json", "meta.json"))
HUBA = Path("/home/claude/work/shared-fallback/engine/04-fea/assembly3d_v352")
F_ENV = HUBA / "results/v352/jfwd_soak_envelope_v352_v6.json"     # v8: the FINAL envelope v6 (lead R1; v7 read the ADOPTED v3 0872de4ea7e3601d)
ENV_SHA16 = "43a5d78b67c615fc"
F_V7IN = HUBA / "results/v352/jfwd_v7inputs_cD_v352.json"        # v8: the input record with v6 (lead 05:27Z (3))
F_MC = HUBA / "results/v352/jfwd_b1_meshcorr_v352.json"          # v8: the C1 record
assert sha(F_V7IN) == "5a41c8d74897bdda" and sha(F_MC) == "adac16afd42ef7bd", (sha(F_V7IN), sha(F_MC))
assert sha(F_ENV) == ENV_SHA16, ("adopted envelope changed", sha(F_ENV))
F_B2C = PATCHES["patch_b2"] / "envelope_candidate.json"                                # FEA3D's (b2) candidate (cross-check of the (b2) rows)
INPUT_FILES = {"js5_relax": F_RELAX, "js5_seatforce": F_SEATF, "js5_screw_bend": F_BEND, "js5_cells": F_CELLS, "relax_v3_module": V3,
               "fea3d_soak_envelope": F_ENV, "patch_b2_envelope_candidate": F_B2C, "patch_b2_shank": PATCHES["patch_b2"] / "shank.json",
               "patch_b2_summary": PATCHES["patch_b2"] / "summary.json", "fea3d_v7inputs_cD_record": F_V7IN, "fea3d_b1_meshcorr": F_MC}
for h, d in PATCHES.items():
    for n in ("seatforce.json", "compare.json", "runcmp_js5_mu0_T3750_g078.json", "meta.json"):
        INPUT_FILES[f"{h}_{n.split('.')[0]}"] = d / n
for h, d in PATCHES.items():                       # v8: every hub patch file read is sha16-asserted
    for n, s16 in PATCH_SHA[d.name].items():
        assert sha(d / n) == s16, (d.name, n, sha(d / n))
        INPUT_FILES[f"{h}_{n.split('.')[0]}"] = d / n

_rel = json.loads(F_RELAX.read_text())
_sfj = json.loads(F_SEATF.read_text())
_SF = {h: json.loads((d / "seatforce.json").read_text()) for h, d in PATCHES.items()}
_CM = {h: json.loads((d / "compare.json").read_text()) for h, d in PATCHES.items()}
_RC = {h: json.loads((d / "runcmp_js5_mu0_T3750_g078.json").read_text()) for h, d in PATCHES.items()}
_MT = {h: json.loads((d / "meta.json").read_text()) for h, d in PATCHES.items()}
_SH = {h: json.loads((PATCHES[h] / "shank.json").read_text()) for h in SHANK_MOMENTS}        # v7: (b2) screw moments incl. the repeats
_B2C = json.loads(F_B2C.read_text())
_sfp, _cmp, _rc, _meta = _SF["patch_a"], _CM["patch_a"], _RC["patch_a"], _MT["patch_a"]
_env = json.loads(F_ENV.read_text())
assert _env["version"] == "v6" and _env["status"].startswith("FINAL"), (_env["version"], _env["status"])
_V7IN = json.loads(F_V7IN.read_text())
_MC = json.loads(F_MC.read_text())
assert _V7IN["inputs_sha16"]["results/v352/jfwd_soak_envelope_v352_v6.json"] == ENV_SHA16
SP = _rel["shell_pull"]
FE = {k: {"F_S": SP[k]["screw_force_N"], "F_fit": SP[k]["FIT_radial_N"], "F_sh": SP[k]["F_sh_N"]} for k in ("PRELOAD", "SOAK70", "SOAK", "SOAK52")}
assert abs(FE["SOAK70"]["F_S"] - 5694.7) < 0.05 and abs(FE["SOAK"]["F_S"] - 7382.8) < 0.05 and abs(FE["SOAK52"]["F_S"] - 6559.9) < 0.05
FV0, G0 = 3750.0, 0.078
K_SH_JS5 = FE["PRELOAD"]["F_sh"] / (G0 + FE["PRELOAD"]["F_fit"] / K_C)
assert abs(K_SH_JS5 - RV3.K_SH_JS5) < 1.0
ORDER = {"js5": ["PRELOAD", "SOAK70", "FA1S", "SOAK", "SOAK52"]}
ORDER.update({h: list(_MT[h]["steps"]) for h in PATCHES})
assert ORDER["patch_a"] == ["SEAT", "PRELOAD", "SOAK52", "SOAK", "SOAK70", "FA1S"]
assert ORDER["patch_a2"] == ["SEAT", "PRELOAD", "SOAK70", "FA1S", "SOAK", "SOAK52"]
assert ORDER["patch_a3"] == ["SEAT", "PRELOAD", "SOAK70", "FA1S", "SOAK", "SOAK52"]
assert ORDER["patch_b2"] == ["SEAT", "PRELOAD", "SOAK52", "SOAK", "SOAK70", "FA1S", "SOAK_rep", "SOAK52_rep"]
ORDER["patch_b2r"] = ORDER["patch_b2"]
assert _MT["patch_b2"]["step_base"] == {"SOAK_rep": "SOAK", "SOAK52_rep": "SOAK52"}
assert ORDER["patch_b1"] == ORDER["patch_b2"] and _MT["patch_b1"]["step_base"] == _MT["patch_b2"]["step_base"]
assert ORDER["patch_b2p"] == ORDER["patch_cD"] == ["SEAT", "PRELOAD", "SOAK52", "SOAK", "SOAK70", "FA1S"]
ORDER["patch_b1r"] = ORDER["patch_b1"]
SOAKS = ("SOAK70", "SOAK", "SOAK52")
STATES = ("PRELOAD", "SOAK70", "SOAK", "SOAK52", "FA1S")


def entered_from(h, st):
    o = ORDER[h]
    i = o.index(src_of(h, st)[1])
    return o[i - 1] if i > 0 else "assembly"


def _ring_relax(st):
    """js5 relax.json ring family, governing soak P+Q line (d-8.126 z'3) at a soak step; PRELOAD = its preload-only value."""
    if st == "PRELOAD":
        g = _rel["steps"]["SOAK70"]["families"]["ring"]["governing_by_soak_PQ"]
        return g["preload_only"]["PmPb"], None
    g = _rel["steps"][st]["families"]["ring"]["governing_by_soak_PQ"]
    return g["preload_plus_soak"]["PmPb"], g["preload_plus_soak"]["MS_PQ_2Fty"]


def hist_row(h, st):
    hp, step = src_of(h, st)                       # v7: run key and step name (the (b2) repeats read their *_rep steps)
    sf = _sfj if h == "js5" else _SF[hp]
    side, key = ("global_same_sets", "B") if h == "js5" else ("patch", "A")
    s = sf["steps"][step]
    fp = s["seat_TC02"]["footprint"]
    cl = max(fp["clusters"], key=lambda c: c["Fn_N"])
    c = _CM[hp]["steps"][step][side]
    z0 = [r for r in _CM[hp]["steps"][step]["z0_gradient"] if r["family"] == "seat" and abs(r["delta_deg"] - 6.051) < 0.01 and abs(r["z_prime_mm"]) < 0.01]
    assert len(z0) == 1
    z0 = z0[0]
    if hp in SHANK_MOMENTS:                        # v7: (b2) moments from its shank.json (patch values; equal to runcmp 'A' where both exist); v8: + (b1), (b2'), (cD)
        sh = _SH[hp]["steps"][step]
        mm = [sh["M_max_threaded"], sh["M_max_shank_in_TC01"]]
        if step in _RC[hp]["steps"]:
            for k_ in ("M_max_threaded", "M_max_shank_in_TC01"):
                assert abs(_RC[hp]["steps"][step][k_]["A"]["M"] - sh[k_]["M"]) < 0.05, (h, st, k_)
    else:
        rc = _RC[hp]["steps"][st]
        mm = [rc["M_max_threaded"][key], rc["M_max_shank_in_TC01"][key]]
    secs = list(c["screw_sections"].values()) + mm
    xs = [float(k[1:]) if k.startswith("x") else None for k in c["screw_sections"]] + [x.get("x") for x in mm]   # v8: x' of the max (FEA3D-2's rule)
    uh = c["under_head_band"]
    nh = s["screw"]["HEAD_on_screw_along_n_N"]
    seat_n = s["seat_TC02"]["along_n_inward_N"]
    out = {"entered_from": entered_from(h, st), "N_head_N": nh, "N_plane_N": s["screw"]["N_plane_N_tension_pos"],
           "seat_window_N": fp.get("window_daz9_zp9_N"), "seat_along_n_N": seat_n, "seat_radial_N": s["seat_TC02"]["normal_force_radial_sum_N"],
           "seat_main_cluster_N": cl["Fn_N"], "main_cluster_zp_mm": cl["z_prime_mm"], "centroid_zp_mm": fp["centroid_force_weighted"]["z_prime_mm"],
           "r_prime_force_weighted_mm": fp.get("r_prime_force_weighted_mm"), "r_prime_5_95_mm": fp.get("r_prime_quantiles_5_95_mm"),
           "CPRESS_r_prime_extent_mm": fp.get("extent_CPRESS_pos", {}).get("r_prime_mm"), "zp_5_95_mm": fp.get("quantiles_5_95_of_Fn", {}).get("z_prime_mm"),
           "F_sh_TC01_N": round(nh - seat_n, 1),
           "seat_line_PmPb_MPa": z0["PmPb_global" if h == "js5" else "PmPb_patch"], "seat_line_MS_PQ": z0["MS_PQ_global" if h == "js5" else "MS_PQ_patch"],
           "seat_line_T_C": z0["T_mean_C"],
           "ring_line_d8p02_PmPb_MPa": c["lines"]["ring"]["PmPb"], "ring_line_d8p02_MS_PQ": c["lines"]["ring"]["MS_PQ_2Fty"],
           "M_max_Nmm": max(x["M"] for x in secs), "M_max_at_x_mm": xs[max(range(len(secs)), key=lambda i: secs[i]["M"])],
           "N_section_max_N": max(x["N"] for x in secs),
           "UH_band_vm_MPa": uh["vm_MPa"], "UH_band_T_C": uh["T_C"],
           "UH_band_MS_strain_min_n15_n30": min(uh["neuber_MS_strain_n15"], uh["neuber_MS_strain_n30"])}
    if h == "js5":
        r, m = _ring_relax(st) if st != "FA1S" else (None, None)
        out["ring_line_d8p126_PmPb_MPa"], out["ring_line_d8p126_MS_PQ"] = r, m
    # v7 re-arbitration: the ring family's P+Q line per instance.  Sharp edge: the ring lines (d8.02 z'3, js5 d-8.126 z'3).  (b2): the contact
    # ring sits on d+6.051 z'0 (FEA3D 15:37Z), so its ring-family P+Q IS the seat line; its d8.02 z'3 line stays as information.
    if h in C1_INST:                               # v8 (R3): (b1)'s seat line at C1 = as solved x ratio_floored (meshcorr governing line)
        g = _MC["states"][st]["instances"][step]["governing_line"]
        assert abs(g["PmPb_b1_MPa"] - out["seat_line_PmPb_MPa"]) <= 0.05 and abs(g["MS_b1"] - out["seat_line_MS_PQ"]) <= 0.0005, (h, st, g)
        _2fty = g["PmPb_b1_MPa"] * (1.0 + g["MS_b1"])
        assert abs(_2fty / g["C1_PmPb_MPa"] - 1.0 - g["C1_MS"]) < 0.002, (h, st, _2fty, g)
        assert abs(g["PmPb_b1_MPa"] * g["ratio_floored"] - g["C1_PmPb_MPa"]) <= 0.1, (h, st, g)
        out["seat_line_as_solved_s9"] = {"PmPb_MPa": g["PmPb_b1_MPa"], "MS_PQ": g["MS_b1"], "ratio_floored": g["ratio_floored"]}
        out["seat_line_PmPb_MPa"], out["seat_line_MS_PQ"] = g["C1_PmPb_MPa"], g["C1_MS"]
    if hp in RING_ON_SEAT:
        out["ring_family_PmPb_MPa"], out["ring_family_line"] = out["seat_line_PmPb_MPa"], f"d+6.051 z'0 (contact ring on the seat line, drawn R0.2 edge, {LABEL[h]})"
    else:
        rv = [v for v in (out["ring_line_d8p02_PmPb_MPa"], out.get("ring_line_d8p126_PmPb_MPa")) if v is not None]
        out["ring_family_PmPb_MPa"], out["ring_family_line"] = max(rv), "ring lines d8.02 z'3 / d-8.126 z'3 (sharp edge)"
    out["step"] = step
    return out


HISTS = {st: {h: hist_row(h, st) for h in H_at(st)} for st in STATES}
# js5's rows come from (a)'s global columns; every other patch's compare file carries the same js5 global columns: check.  (b2) is on the
# s6 mesh with its own line sets mapped on js5 (FEA3D 'global_sets_from' (a'')): its global columns are checked against (a'')'s instead.
B2_GLOBAL_CHECK = {}
for _h in PATCHES:
    for _st in STATES:
        _ref = "patch_a3" if _h in RING_ON_SEAT else "patch_a"
        _g1, _g2 = _CM[_ref]["steps"][_st]["global_same_sets"], _CM[_h]["steps"][_st]["global_same_sets"]
        if _h in RING_ON_SEAT:                      # v8: (b1), (b2'), (cD) are on their own meshes too: recorded, not asserted
            B2_GLOBAL_CHECK[_st if _h == "patch_b2" else f"{_st}|{LABEL[_h]}"] = {"ring_global_b2": _g2["lines"]["ring"]["PmPb"], "ring_global_a3": _g1["lines"]["ring"]["PmPb"],
                                    "seat_global_b2": _g2["lines"]["seat"]["PmPb"], "seat_global_a3": _g1["lines"]["seat"]["PmPb"]}
            continue
        assert abs(_g1["lines"]["ring"]["PmPb"] - _g2["lines"]["ring"]["PmPb"]) < 0.05, (_h, _st)
# FEA3D envelope cross-check (its N_plane / window / seat line d+6.051 z'0 per run) against the rows read here
ENV_XCHK = {}
for _st in STATES:
    _e = _env["states"][_st]
    for _h in H_at(_st):
        _l = LABEL[_h]
        if _l not in _e["N_plane_N"]:
            continue
        _r = HISTS[_st][_h]
        ENV_XCHK[f"{_st}|{_l}"] = {"N_plane_fea3d": _e["N_plane_N"][_l], "N_plane_here": _r["N_plane_N"], "N_head_here": _r["N_head_N"],
                                   "window_fea3d": _e["seat_window_N"][_l], "window_here": _r["seat_window_N"],
                                   "seat_line_PmPb_fea3d": _e["lines"]["d+6.051_z+0.0"]["PmPb_MPa"].get(_l), "seat_line_PmPb_here": _r["seat_line_PmPb_MPa"]}
        assert abs(_e["N_plane_N"][_l] - _r["N_plane_N"]) < 0.5 and abs(_e["seat_window_N"][_l] - _r["seat_window_N"]) < 0.5, (_st, _l)
        if _l in _e["lines"]["d+6.051_z+0.0"]["PmPb_MPa"]:
            assert abs(_e["lines"]["d+6.051_z+0.0"]["PmPb_MPa"][_l] - _r["seat_line_PmPb_MPa"]) < 0.15, (_st, _l)
        else:
            assert _h in LOCAL_EXCLUDE, (_st, _l)          # v8: cD is not in v6's lines (R3)


def envelope(st):
    X = HISTS[st]
    HH = tuple(X)
    HL = tuple(h for h in HH if h not in LOCAL_EXCLUDE)               # v8 (R3): the local quantities without cD
    hi = lambda k, S=HH: max(S, key=lambda h: X[h][k])
    lo = lambda k, S=HH: min(S, key=lambda h: X[h][k])
    ring = [X[h]["ring_family_PmPb_MPa"] for h in HL]                 # v7: (b2)'s ring family = its seat line (v8: also (b1), (b2'))
    Ns = [X[h]["N_head_N"] for h in HH]
    e = {"N_head_N": X[hi("N_head_N")]["N_head_N"], "N_head_from": hi("N_head_N"), "N_head_min_N": X[lo("N_head_N")]["N_head_N"], "N_head_min_from": lo("N_head_N"),
         "seat_window_N": X[lo("seat_window_N")]["seat_window_N"], "seat_window_from": lo("seat_window_N"),
         "seat_line_PmPb_MPa": X[hi("seat_line_PmPb_MPa", HL)]["seat_line_PmPb_MPa"], "seat_line_PmPb_from": hi("seat_line_PmPb_MPa", HL),
         "seat_line_MS_PQ": X[lo("seat_line_MS_PQ", HL)]["seat_line_MS_PQ"], "seat_line_from": lo("seat_line_MS_PQ", HL),
         "ring_line_PmPb_MPa": max(ring), "M_max_Nmm": X[hi("M_max_Nmm")]["M_max_Nmm"], "M_from": hi("M_max_Nmm"),
         "M_max_at_x_mm": X[hi("M_max_Nmm")]["M_max_at_x_mm"], "N_section_max_N": X[hi("N_section_max_N")]["N_section_max_N"],
         "UH_band_MS_strain_min": X[lo("UH_band_MS_strain_min_n15_n30", HL)]["UH_band_MS_strain_min_n15_n30"],
         "UH_from": lo("UH_band_MS_strain_min_n15_n30", HL),
         "spread_N_rel": round((max(Ns) - min(Ns)) / min(Ns), 4),
         "instances_resultants": [LABEL[h] for h in HH], "instances_local": [LABEL[h] for h in HL]}
    return e


ENV = {st: envelope(st) for st in STATES}
# v8: the envelope here reproduces FEA3D-2's input record (v7_convention view): 9 numbers, M_max_at_x and 7 'from' fields per state
_NUMK = ("N_head_N", "N_head_min_N", "seat_window_N", "seat_line_PmPb_MPa", "seat_line_MS_PQ", "M_max_Nmm", "N_section_max_N",
         "UH_band_MS_strain_min", "spread_N_rel", "M_max_at_x_mm")
_TOLK = {"seat_line_MS_PQ": 0.0005, "UH_band_MS_strain_min": 0.0005, "spread_N_rel": 0.00005}
_FROMK = ("N_head_from", "N_head_min_from", "seat_window_from", "seat_line_PmPb_from", "seat_line_from", "M_from", "UH_from")
V7IN_XCHK = {}
for _st in STATES:
    _v = _V7IN["views"][_st]["v7_convention"]
    for _k in _NUMK:
        assert abs(ENV[_st][_k] - _v[_k]) <= _TOLK.get(_k, 0.05), (_st, _k, ENV[_st][_k], _v[_k])
    for _k in _FROMK:
        assert ENV[_st][_k] == _v[_k], (_st, _k, ENV[_st][_k], _v[_k])
    assert ENV[_st]["instances_resultants"] == _v["instances_resultants"] and ENV[_st]["instances_local"] == _v["instances_local"], _st
    V7IN_XCHK[_st] = {"equal_within_FEA3D2_tolerances": True, "numbers": list(_NUMK), "from_fields": list(_FROMK)}

# ---- model temperatures per FE state (A4-80 deltas: the FE screw is A4-80)
_tL, _aL, _cL = ROWS4["GVLO"]


def frame_near(t0):
    i = int(np.argmin(np.abs(_tL - t0)))
    return float(_aL[i]), float(_cL[i]), round(float(_tL[i]), 3)


TST = {"SOAK70": frame_near(70.7), "SOAK52": frame_near(51.7), "SOAK": (158.0, 96.0, "uniform per part (FEA3D jfwd_deck SOAK: TC-01 158.0, TC-02 96.0, screw 127.0)")}
_, DW70, DR70 = A4_80.deltas(*TST["SOAK70"][:2])
assert abs(DW70 - RV3.DW70) < 1e-12 and abs(DR70 - RV3.DR70) < 1e-12


def model_state(st, kb, scr=A4_80, FV=FV0, g=G0, ksh=None):
    if st == "PRELOAD":
        return state_s(FV, g, 0.0, 0.0, 0.0, 0.0, ksh or K_SH_JS5, kb * scr.kb_ratio)
    T01, T02 = TST[st][:2]
    _, dw, dr = scr.deltas(T01, T02)
    return state_s(FV, g, dw, dr, 0.0, 0.0, ksh or K_SH_JS5, kb * scr.kb_ratio)


def calib_kb(ksh, target):
    _, dw, dr = A4_80.deltas(*TST["SOAK70"][:2])
    lo, hi = 1.0e3, 5.0e7
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if state_s(FV0, G0, dw, dr, 0.0, 0.0, ksh, mid)[0] < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


N70 = {h: HISTS["SOAK70"][h]["N_head_N"] for h in H_at("SOAK70")}
H70_LO, H70_HI = min(N70, key=N70.get), max(N70, key=N70.get)
KB = {"lo": calib_kb(K_SH_JS5, N70[H70_LO]), "hi": calib_kb(K_SH_JS5, N70[H70_HI])}
KB_SRC = {"lo": f"{LABEL[H70_LO]} SOAK70 head force {N70[H70_LO]} N", "hi": f"{LABEL[H70_HI]} SOAK70 head force {N70[H70_HI]} N"}
KB_V4 = {"lo_js5_SOAK70": RV3.K_B5, "hi_patch_SOAK70": calib_kb(K_SH_JS5, N70["patch_a"])}

# ---- c per family and per k_b end: worst-history FE P+Q over the model's F_sh at each state
PQ_SEAT = {st: max(HISTS[st][h]["seat_line_PmPb_MPa"] for h in H_at(st) if h not in LOCAL_EXCLUDE) for st in ("PRELOAD",) + SOAKS}
PQ_RING = {st: ENV[st]["ring_line_PmPb_MPa"] for st in ("PRELOAD",) + SOAKS}


def c_family(pq, kb):
    per = {st: pq[st] / model_state(st, kb)[3] for st in pq}
    st = max(per, key=per.get)
    return per[st], st, {k: round(v, 5) for k, v in per.items()}


CFAM = {e: {"seat": c_family(PQ_SEAT, kb), "ring": c_family(PQ_RING, kb)} for e, kb in KB.items()}
# v4's c (two histories, v4 bracket) for the 'does c move' answer
_PQ_SEAT_V4 = {st: max(HISTS[st][h]["seat_line_PmPb_MPa"] for h in ("js5", "patch_a")) for st in ("PRELOAD",) + SOAKS}
_PQ_RING_V4 = {st: max(v for h in ("js5", "patch_a") for v in (HISTS[st][h]["ring_line_d8p02_PmPb_MPa"], HISTS[st][h].get("ring_line_d8p126_PmPb_MPa"))
                      if v is not None) for st in ("PRELOAD",) + SOAKS}
CFAM_V4 = {e: {"seat": c_family(_PQ_SEAT_V4, kb), "ring": c_family(_PQ_RING_V4, kb)} for e, kb in KB_V4.items()}

# ---- tilt moment basis 'Fc'
SOAK_PTS = [(HISTS[st][h]["seat_radial_N"], HISTS[st][h]["M_max_Nmm"], f"{h}:{st}") for st in SOAKS for h in H_at(st)]
_x = np.array([p[0] for p in SOAK_PTS])
_y = np.array([p[1] for p in SOAK_PTS])
B_M = float(np.sum((_x - _x.mean()) * (_y - _y.mean())) / np.sum((_x - _x.mean()) ** 2))
A_M = float(np.max(_y - B_M * _x))
M_PRE_ENV = max(HISTS["PRELOAD"][h]["M_max_Nmm"] for h in H_at("PRELOAD"))
M_PRE_MIN = min(HISTS["PRELOAD"][h]["M_max_Nmm"] for h in H_at("PRELOAD"))     # the cold end of the fibre RANGE (shakedown / LCF) takes the lowest PRELOAD moment
N_RATIO = max(HISTS[st][h]["N_section_max_N"] / HISTS[st][h]["N_head_N"] for st in ("PRELOAD",) + SOAKS for h in H_at(st))


def m_soak(Fc):
    return A_M + B_M * Fc


def m_tilt(FS, Fc, w, mpre=None):
    mp = (M_PRE_ENV if mpre is None else mpre) * max(FS, 0.0) / FV0
    return mp + max(w, 0.0) * max(0.0, m_soak(Fc) - mp)


def fibre(FS, Fc, w, scr, mpre=None):
    if FS <= 0.0:
        return 0.0
    return N_RATIO * FS / scr.A_s + scr.tilt_ratio * m_tilt(FS, Fc, w, mpre) / scr.Z_3


def fire(FV, g, f, fr, s0, dp0, c, ksh, kb, scr, screw_set=True, cap=True):
    """one firing (every frame, then a cold frame) from wall set s0 and screw set dp0 (v3 structure, v4 tilt)."""
    t, T01, T02 = fr
    s, dp = s0, dp0
    rec = []
    for i in list(range(len(t))) + [None]:
        if i is None:
            a_, b_, dw, dr, ti = 20.0, 20.0, 0.0, 0.0, "cold"
        else:
            a_, b_ = float(T01[i]), float(T02[i])
            _, dw, dr = scr.deltas(a_, b_)
            ti = round(float(t[i]), 3)
        w = dr / DR70
        Fy = float(tab("AL6061-T6", "Fty", a_))
        Rp = scr.rp(a_)
        wy = sy = False
        for _ in range(60):
            FS, u, Fc, Fsh = state_s(FV, g, dw, dr, f + dp, s, ksh, kb)
            changed = False
            if cap and FS > 0.0 and c * Fsh > Fy * (1 + 1e-9):
                lo, hi = s, s + 1.0
                for _ in range(100):
                    mid = 0.5 * (lo + hi)
                    lo, hi = (mid, hi) if c * state_s(FV, g, dw, dr, f + dp, mid, ksh, kb)[3] > Fy else (lo, mid)
                s, wy, changed = hi, True, True
                FS, u, Fc, Fsh = state_s(FV, g, dw, dr, f + dp, s, ksh, kb)
            if screw_set and FS > 0.0 and fibre(FS, Fc, w, scr) > Rp * (1 + 1e-9):
                lo, hi = dp, dp + 0.2
                for _ in range(100):
                    mid = 0.5 * (lo + hi)
                    q = state_s(FV, g, dw, dr, f + mid, s, ksh, kb)
                    lo, hi = (mid, hi) if fibre(q[0], q[2], w, scr) > Rp else (lo, mid)
                dp, sy, changed = hi, True, True
                FS, u, Fc, Fsh = state_s(FV, g, dw, dr, f + dp, s, ksh, kb)
            if not changed:
                break
        rec.append({"t": ti, "T01": a_, "T02": b_, "FS": FS, "Fsh": Fsh, "Fc": Fc, "u": u, "w": w, "sig": c * Fsh, "Fty": Fy, "set": s,
                    "dp": dp, "M": m_tilt(FS, Fc, w) * scr.tilt_ratio, "fib": fibre(FS, Fc, w, scr), "fib_lo": fibre(FS, Fc, w, scr, M_PRE_MIN),
                    "Rp": Rp, "wyield": wy, "syield": sy,
                    "slack": FS <= 0.0})
    return rec, s, dp


def summary(rec):
    j = min(range(len(rec)), key=lambda k: rec[k]["FS"])
    r = rec[j]
    jf = max(range(len(rec)), key=lambda k: rec[k]["fib"])
    return {"F_S_min_N": round(r["FS"]), "at_t_s": r["t"], "T01_T02_C": [round(r["T01"], 1), round(r["T02"], 1)],
            "fit_at_min": "closed" if r["Fc"] > 0 else ("SLACK" if r["slack"] else "open"),
            "slack_frames": int(sum(1 for q in rec if q["slack"])), "wall_yield_frames": int(sum(1 for q in rec if q["wyield"])),
            "screw_yield_frames": int(sum(1 for q in rec if q["syield"])),
            "wall_set_end_um": round(rec[-1]["set"] * 1e3, 3), "screw_set_end_um": round(rec[-1]["dp"] * 1e3, 3),
            "cold_end_F_S_N": round(rec[-1]["FS"]), "F_S_max_N": round(max(q["FS"] for q in rec)),
            "F_c_max_N": round(max(q["Fc"] for q in rec)), "F_c_min_N": round(min(q["Fc"] for q in rec)),
            "max_sig_over_Fty": round(max(q["sig"] / q["Fty"] for q in rec), 3),
            "fibre_max_MPa": round(rec[jf]["fib"], 1), "fibre_max_at": rec[jf]["t"], "M_at_fibre_max_Nmm": round(rec[jf]["M"], 1),
            "fibre_min_MPa": round(min(q["fib"] for q in rec), 1), "fibre_min_range_basis_MPa": round(min(q["fib_lo"] for q in rec), 1),
            "Rp_at_fibre_max_MPa": round(rec[jf]["Rp"], 1)}


def run_case(FV, g, f, fr, c, ksh, kb, scr, screw_set=True, cap=True, keep=False):
    rec1, s1, d1 = fire(FV, g, f, fr, 0.0, 0.0, c, ksh, kb, scr, screw_set, cap)
    rec2, s2, d2 = fire(FV, g, f, fr, s1, d1, c, ksh, kb, scr, screw_set, cap)
    FS_cold0 = state_s(FV, g, 0.0, 0.0, f, 0.0, ksh, kb)[0]
    j2 = max(range(len(rec2)), key=lambda k: rec2[k]["fib"])
    rng = rec2[j2]["fib"] - min(q["fib_lo"] for q in rec2)          # v5: range cold end with the lowest PRELOAD moment (conservative)
    out = {"gap_mm": g, "F_install_N": FV, "embedding_um": round(f * 1e3, 1), "k_sh_N_mm": round(ksh), "k_b_N_mm": round(kb),
           "c_MPa_per_N": round(c, 5), "screw": scr.name, "installed_cold_after_embedding_N": round(FS_cold0),
           "firing_1": summary(rec1), "firing_2": summary(rec2),
           "wall_set_after_firing_1_um": round(s1 * 1e3, 3), "wall_set_after_firing_2_um": round(s2 * 1e3, 3),
           "screw_set_after_firing_1_um": round(d1 * 1e3, 3), "screw_set_after_firing_2_um": round(d2 * 1e3, 3),
           "relaxation_loss_cold_N": round(FS_cold0 - rec1[-1]["FS"]),
           "heads_seated_both_firings": not any(q["slack"] for q in rec1 + rec2),
           "second_firing_elastic": (s2 - s1) < 1e-9 and (d2 - d1) < 1e-9,
           "screw_shakedown": {"fibre_range_firing2_MPa": round(rng, 1), "two_Rp_hot_MPa": round(2.0 * rec2[j2]["Rp"], 1),
                               "MS": round(2.0 * rec2[j2]["Rp"] / max(rng, 1e-9) - 1.0, 3)}}
    if keep:
        out["_rec2"] = rec2
    return out


def run_grid(gaps, installs, ksh, kb, c, scr, screw_set=True, cap=True, emb=None, rows=None):
    out = {}
    for gn, g in gaps.items():
        for iname, FV in installs.items():
            for en, f in (emb or EMB).items():
                for gv, fr in (rows or ROWS4).items():
                    out[f"{gn}|{iname}|{en}|{gv}"] = run_case(FV, g, f, fr, c, ksh, kb, scr, screw_set, cap)
    return out


def run24(ksh, kb, c, scr, screw_set=True, cap=True):
    return run_grid(GAPS, INSTALL, ksh, kb, c, scr, screw_set, cap)


def vsum(d):
    mn = lambda x: min(x["firing_1"]["F_S_min_N"], x["firing_2"]["F_S_min_N"])
    j = min(d, key=lambda k: mn(d[k]))
    jf = max(d, key=lambda k: d[k]["firing_2"]["fibre_max_MPa"] / max(d[k]["firing_2"]["Rp_at_fibre_max_MPa"], 1e-9))
    j_cold = min(d, key=lambda k: d[k]["firing_2"]["cold_end_F_S_N"])
    return {"all_seated": all(x["heads_seated_both_firings"] for x in d.values()), "n_cases": len(d),
            "n_unseated": sum(1 for x in d.values() if not x["heads_seated_both_firings"]),
            "unseated_cases": [k for k, x in d.items() if not x["heads_seated_both_firings"]],
            "min_case": j, "F_S_min_N": mn(d[j]), "min_at": d[j]["firing_2" if d[j]["firing_2"]["F_S_min_N"] <= d[j]["firing_1"]["F_S_min_N"] else "firing_1"]["at_t_s"],
            "F_S_max_N": max(max(x["firing_1"]["F_S_max_N"], x["firing_2"]["F_S_max_N"]) for x in d.values()),
            "F_c_max_N": max(max(x["firing_1"]["F_c_max_N"], x["firing_2"]["F_c_max_N"]) for x in d.values()),
            "fibre_over_Rp_max": round(d[jf]["firing_2"]["fibre_max_MPa"] / d[jf]["firing_2"]["Rp_at_fibre_max_MPa"], 3), "fibre_over_Rp_max_case": jf,
            "screw_fibre_max_MPa": max(max(x["firing_1"]["fibre_max_MPa"], x["firing_2"]["fibre_max_MPa"]) for x in d.values()),
            "max_seat_over_Fty": max(max(x["firing_1"]["max_sig_over_Fty"], x["firing_2"]["max_sig_over_Fty"]) for x in d.values()),
            "max_wall_set_um": max(x["wall_set_after_firing_2_um"] for x in d.values()),
            "max_screw_set_um": max(x["screw_set_after_firing_2_um"] for x in d.values()),
            "max_cold_loss_N": max(x["relaxation_loss_cold_N"] for x in d.values()),
            "all_second_firing_elastic": all(x["second_firing_elastic"] for x in d.values()),
            "n_second_firing_not_elastic": sum(1 for x in d.values() if not x["second_firing_elastic"]),
            "screw_shakedown_min_MS": min(x["screw_shakedown"]["MS"] for x in d.values()),
            "screw_fibre_range_max_MPa": max(x["screw_shakedown"]["fibre_range_firing2_MPa"] for x in d.values()),
            "cold_end_F_S_min_N": d[j_cold]["firing_2"]["cold_end_F_S_N"], "cold_end_min_case": j_cold,
            "cold_end_F_S_min_2250_N": min(x["firing_2"]["cold_end_F_S_N"] for k, x in d.items() if "2250" in k)}


# ---- screws (v3 definitions; IN718 is the ruled screw)
E20 = {"A4": 193000.0, "IN718": tab("IN718", "E", 20.0)}
IN718_S = Screw("IN718", "IN718", E20["IN718"] / E20["A4"], lambda T: tab("IN718", "Fty", T),
                "IN718 AMS 5662/5663 minimum Fty(T) (Special Metals SMC-045, DATASHEET in engmat; linear 20-649 C)")
L_EFF5, L_EFF6 = (2.688 + 0.025) + 0.4 * 5.0 + 0.5 * 5.0, (2.600 + 0.025) + 0.4 * 6.0 + 0.5 * 6.0
KB_M6 = (20.12 / L_EFF6) / (14.18 / L_EFF5)
M6_S = Screw("M6 A4-80", "SS316L", 1.0, lambda T: RV3.RP20 * kT(T), "as A4-80 (ISO 3506-1 class 80)", A_s=20.12, Z_3=math.pi * 4.773 ** 3 / 32.0,
             L_g=L_G * (2.600 + 0.025) / (2.688 + 0.025), kb_ratio=KB_M6, tilt_ratio=(4.773 / 4.019) ** 4)
IN_KEY = "IN718 M5 flight L 10.2 +/-0.1 (RULED, ENG-HW-101-IN718; k_b calibrated on the FE L 10.0, length effect ASSUMED small)"   # lead 16:07Z (3)
OPTS = {IN_KEY: (IN718_S, 1.0, 1.0, "grade: alpha IN718, k_b x E ratio"),
        "A4-80 M5 x10 (WITHDRAWN, information)": (A4_80, 1.0, 1.0, "FE-calibrated screw"),
        "M6 A4-80 x10 (FALLBACK, ESTIMATE)": (M6_S, (2.600 / 2.688) ** 3, (2.688 / 2.600) ** 2, "ESTIMATE (no FE): v3 size factors")}


def opt_params(nm, end, fam):
    scr, kf, cf, tag = OPTS[nm]
    c = CFAM[end][fam][0] * cf
    return scr, K_SH_JS5 * kf, KB[end] * scr.kb_ratio, c


if __name__ == "__main__":
    res = {"id": "jfwd_relax_v352", "version": "v8", "date": "2026-10-21", "owner": "mechanical", "basis": __doc__.strip(),
           "inputs": {k: {"path": str(p), "sha256_16_at_read": sha(p)} for k, p in INPUT_FILES.items()}}
    res["inputs"]["rows"] = SRC4
    res["inputs"]["constants"] = {"k_c_N_mm": round(K_C), "k_sh_K_js5_N_mm": round(K_SH_JS5, 1), "embedding_um": {k: v * 1e3 for k, v in EMB.items()},
                                  "A_s_mm2": A_S, "Z_3_mm3": round(Z_3, 3), "N_ratio": round(N_RATIO, 4),
                                  "k_sh_from_seatforce_exact_split_info": round(_sfj["steps"]["PRELOAD"]["shell_TC02"]["shell_pull_N_tie_minus_seat"]
                                                                                 / (G0 + _sfj["steps"]["PRELOAD"]["seat_TC02"]["normal_force_radial_sum_N"] / K_C), 1)}
    res["histories"] = {h: {"label": LABEL[h], "order": ORDER[h], "states": list(s_ for s_ in STATES if src_of(h, s_)),
                            "steps": {s_: src_of(h, s_)[1] for s_ in STATES if src_of(h, s_)},
                            "run": str(PATCHES[src_of(h, "SOAK")[0]]) if h != "js5" else "hub jfwd_interim js5"} for h in H}
    res["b2_global_columns_vs_a3"] = B2_GLOBAL_CHECK
    res["fea3d_envelope_crosscheck"] = ENV_XCHK
    res["fea3d_v7inputs_cD_crosscheck"] = V7IN_XCHK
    res["cD_beside_R3"] = {"rule": _V7IN["rule"], "beside": _V7IN["beside"], "cD_rows": _V7IN["cD_rows"], "MF_note": MF_NOTE}
    res["cad_basis_R8"] = CAD_BASIS
    res["k_b_bracket"] = {"lo_N_mm": round(KB["lo"]), "lo_from": KB_SRC["lo"], "hi_N_mm": round(KB["hi"]), "hi_from": KB_SRC["hi"],
                          "v4_bracket_N_mm": {k: round(v) for k, v in KB_V4.items()}, "widened": KB["lo"] < KB_V4["lo_js5_SOAK70"] - 1.0}
    res["c_move_v4_to_v5"] = {e5: {fam: {"v4": round(CFAM_V4[e4][fam][0], 5), "v4_state": CFAM_V4[e4][fam][1], "v5": round(CFAM[e5][fam][0], 5),
                                         "v5_state": CFAM[e5][fam][1], "rel": round(CFAM[e5][fam][0] / CFAM_V4[e4][fam][0] - 1.0, 4)} for fam in ("seat", "ring")}
                              for e5, e4 in (("lo", "lo_js5_SOAK70"), ("hi", "hi_patch_SOAK70"))}
    res["history_table"] = HISTS
    res["history_envelope"] = ENV
    res["model_frames"] = TST
    # ---- calibration bracket and the model check against both histories
    chk = {}
    for e, kb in KB.items():
        rows = {}
        for st in SOAKS:
            FS, u, Fc, Fsh = model_state(st, kb)
            r = {"model": {"F_S_N": round(FS, 1), "F_c_N": round(Fc, 1), "F_sh_N": round(Fsh, 1)}}
            for h in H_at(st):
                x = HISTS[st][h]
                r[h] = {"entered_from": x["entered_from"], "N_head_N": x["N_head_N"], "seat_window_N": x["seat_window_N"], "seat_main_cluster_N": x["seat_main_cluster_N"],
                        "F_sh_TC01_N": x["F_sh_TC01_N"],
                        "model_vs_FE_N_rel": round(FS / x["N_head_N"] - 1.0, 4), "model_vs_FE_seat_window_rel": round(Fc / x["seat_window_N"] - 1.0, 4)}
            r["model_vs_envelope_N_rel"] = round(FS / ENV[st]["N_head_N"] - 1.0, 4)
            r["model_vs_lowest_seat_window_rel"] = round(Fc / ENV[st]["seat_window_N"] - 1.0, 4)
            rows[st] = r
        chk[e] = {"k_b_N_mm": round(kb), "k_b_over_lo": round(kb / KB["lo"], 4), "states": rows,
                  "c_seat": {"used": round(CFAM[e]["seat"][0], 5), "governing_state": CFAM[e]["seat"][1], "per_state": CFAM[e]["seat"][2]},
                  "c_ring": {"used": round(CFAM[e]["ring"][0], 5), "governing_state": CFAM[e]["ring"][1], "per_state": CFAM[e]["ring"][2]}}
    res["calibration_bracket_and_model_check"] = chk
    res["tilt_basis_Fc"] = {"soak_points_Fc_N_M_Nmm": [[round(a, 1), round(b, 1), n] for a, b, n in SOAK_PTS], "slope_b": round(B_M, 4),
                            "intercept_a_Nmm": round(A_M, 1), "M_pre_env_Nmm_at_3750N": M_PRE_ENV, "M_pre_min_Nmm_at_3750N_range_basis": M_PRE_MIN,
                            "residuals_line_minus_FE_Nmm": {n: round(A_M + B_M * a - b, 1) for a, b, n in SOAK_PTS}}
    # ---- the 24-case no-slack check, both k_b ends, seat and ring bounds, per option
    cases, verdict = {}, {}
    for nm in OPTS:
        for e in KB:
            for fam in ("seat", "ring"):
                scr, ksh, kb, c = opt_params(nm, e, fam)
                d = run24(ksh, kb, c, scr, True)
                cases[f"{nm}|{e}|{fam}"] = d
                v = vsum(d)
                v.update({"k_sh_N_mm": round(ksh), "k_b_N_mm": round(kb), "c": round(c, 5)})
                verdict[f"{nm}|{e}|{fam}"] = v
    res["cases_24"] = cases
    res["verdict_24"] = verdict
    worse = {}
    for nm in OPTS:
        for fam in ("seat", "ring"):
            vs = {e: verdict[f"{nm}|{e}|{fam}"] for e in KB}
            we = min(vs, key=lambda e: (vs[e]["F_S_min_N"], -vs[e]["n_unseated"]))
            worse[f"{nm}|{fam}"] = {"worse_end": we, "F_S_min_N": vs[we]["F_S_min_N"], "n_unseated": vs[we]["n_unseated"], "min_case": vs[we]["min_case"],
                                    "both_ends": {e: {"F_S_min_N": vs[e]["F_S_min_N"], "n_unseated": vs[e]["n_unseated"], "cold_end_F_S_min_2250_N": vs[e]["cold_end_F_S_min_2250_N"],
                                                      "max_wall_set_um": vs[e]["max_wall_set_um"], "max_screw_set_um": vs[e]["max_screw_set_um"],
                                                      "fibre_over_Rp_max": vs[e]["fibre_over_Rp_max"], "screw_shakedown_min_MS": vs[e]["screw_shakedown_min_MS"]} for e in KB}}
    res["worse_end_quoted"] = worse
    # ---- (a) series compliance for IN718 on the seat line: the largest k_b factor that seats all 24 at each end
    IN = IN_KEY
    sc = {}
    for e in KB:
        scr, ksh, kb, c = opt_params(IN, e, "seat")
        if vsum(run24(ksh, kb, c, scr))["all_seated"]:
            sc[e] = {"f_max": 1.0, "note": "seated without added compliance"}
            continue
        lo, hi = 0.02, 1.0
        if not vsum(run24(ksh, kb * lo, c, scr))["all_seated"]:
            sc[e] = {"f_max": None, "note": "slack even at k_b x 0.02"}
            continue
        for _ in range(14):
            mid = math.sqrt(lo * hi)
            lo, hi = (mid, hi) if vsum(run24(ksh, kb * mid, c, scr))["all_seated"] else (lo, mid)
        vf = vsum(run24(ksh, kb * lo, c, scr))
        sc[e] = {"f_max": round(lo, 4), "k_b_at_f_N_mm": round(kb * lo), "added_series_compliance_um_per_kN": round((1.0 / (kb * lo) - 1.0 / kb) * 1e6, 3),
                 "F_S_min_at_f_N": vf["F_S_min_N"], "min_case": vf["min_case"], "cold_end_F_S_min_2250_N": vf["cold_end_F_S_min_2250_N"],
                 "F_S_max_N": vf["F_S_max_N"], "fibre_over_Rp_max": vf["fibre_over_Rp_max"]}
    res["a_series_compliance_IN718_seat_line"] = sc
    # ---- ring-line select-fit band for IN718 (information unless the ring line stands): largest gap with all 24 seated, per end
    def gap_cap(scr, ksh, kb, c):
        """band from the 0.040 drawing minimum upward (the minimum stays, lead 11:25Z): the largest gap with all cases seated; the sweep
        below 0.040 is information (not buildable)."""
        seated = lambda g: vsum(run_grid({f"g{g:.4f}": g}, INSTALL, ksh, kb, c, scr))["all_seated"]
        grid = [0.040 + 0.0025 * k for k in range(0, 33)]
        sweep = {round(g, 4): seated(g) for g in grid}
        below = {round(0.0025 * k, 4): seated(0.0025 * k) for k in range(0, 16)}
        if not sweep[0.04]:
            return {"g_cap_mm": None, "note": "not seated at the 0.040 drawing minimum: no band", "sweep_0.040_0.120": sweep, "below_0.040_info": below}
        bad = [g for g in grid if not seated(g)]
        if not bad:
            return {"g_cap_mm": "> 0.120", "sweep_0.040_0.120": sweep, "below_0.040_info": below}
        fb = min(bad)
        lo, hi = fb - 0.0025, fb
        for _ in range(14):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if seated(mid) else (lo, mid)
        return {"g_cap_mm": round(lo, 5), "contiguous_from_0.040": all(v for g, v in sweep.items() if g <= lo), "sweep_0.040_0.120": sweep,
                "below_0.040_info": below}
    sfb = {}
    for e in KB:
        for fam in ("seat", "ring"):
            scr, ksh, kb, c = opt_params(IN, e, fam)
            sfb[f"{e}|{fam}"] = gap_cap(scr, ksh, kb, c)
    res["select_fit_gap_cap_IN718"] = sfb
    # ---- P+Q select-fit band on the envelope (lead 12:28Z item 2, information for the fix ruling): per soak state and family,
    #      P+Q(g, F_V) = P+Q_env x F_sh,model(IN718, g, F_V) / F_sh,model(A4-80, 0.078, 3750) at the state's model temperatures; MS vs 2 Fty(T_line)
    lines_T = {st: _env["states"][st]["lines"]["d+6.051_z+0.0"]["T_mean_C"] for st in SOAKS}
    def pq_ms(st, fam, kb, g, FV, scr=IN718_S):
        env_pq = PQ_SEAT[st] if fam == "seat" else PQ_RING[st]
        T = lines_T[st]
        f0 = model_state(st, kb, A4_80, FV0, G0)[3]
        f1 = model_state(st, kb, scr, FV, g)[3]
        return 2.0 * float(tab("AL6061-T6", "Fty", T)) / (env_pq * f1 / f0) - 1.0
    band = {}
    for e, kb in KB.items():
        for fam in ("seat", "ring"):
            for FV in (3750.0, 4096.0):
                per = {}
                for st in SOAKS:
                    ms_at = {g: round(pq_ms(st, fam, kb, g, FV), 4) for g in (0.040, 0.059, 0.070, 0.078)}
                    lo_, hi_ = 0.0, 0.2
                    if pq_ms(st, fam, kb, 0.2, FV) >= 0.0:
                        gz = "> 0.2"
                    elif pq_ms(st, fam, kb, 0.0, FV) < 0.0:
                        gz = "< 0 (no band)"
                    else:
                        for _ in range(60):
                            mid = 0.5 * (lo_ + hi_)
                            lo_, hi_ = (mid, hi_) if pq_ms(st, fam, kb, mid, FV) >= 0.0 else (lo_, mid)
                        gz = round(lo_, 5)
                    per[st] = {"g_at_MS0_mm": gz, "MS_at_gap": ms_at, "PQ_env_MPa": PQ_SEAT[st] if fam == "seat" else PQ_RING[st], "T_line_C": lines_T[st]}
                gmin = min((v["g_at_MS0_mm"] for v in per.values() if isinstance(v["g_at_MS0_mm"], float)), default=None)
                band[f"{e}|{fam}|{FV:.0f}"] = {"g_max_mm": gmin, "per_state": per}
    res["PQ_select_fit_band_on_envelope_IN718"] = band
    # ---- v8: what moves from v7 (lead 15:37Z order: 'flag every quoted row that turns negative')
    _v7 = json.loads((J / "jfwd_relax_v352_v7.json").read_text())
    mv = {"k_b_bracket": {"v7": {k: _v7["k_b_bracket"][f"{k}_N_mm"] for k in ("lo", "hi")}, "v8": {k: round(KB[k]) for k in ("lo", "hi")},
                          "v7_from": {k: _v7["k_b_bracket"][f"{k}_from"] for k in ("lo", "hi")}, "v8_from": KB_SRC},
          "tilt": {"v7": {k: _v7["tilt_basis_Fc"][k] for k in ("slope_b", "intercept_a_Nmm", "M_pre_env_Nmm_at_3750N", "M_pre_min_Nmm_at_3750N_range_basis")},
                   "v8": {"slope_b": round(B_M, 4), "intercept_a_Nmm": round(A_M, 1), "M_pre_env_Nmm_at_3750N": M_PRE_ENV,
                          "M_pre_min_Nmm_at_3750N_range_basis": M_PRE_MIN}},
          "N_ratio": {"v7": _v7["inputs"]["constants"]["N_ratio"], "v8": round(N_RATIO, 4)},
          "c": {e: {fam: {"v7": _v7["calibration_bracket_and_model_check"][e][f"c_{fam}"]["used"], "v8": round(CFAM[e][fam][0], 5),
                          "v8_state": CFAM[e][fam][1]} for fam in ("seat", "ring")} for e in KB},
          "verdict_24": {}, "seat_force_vs_lowest_window": {}, "series_compliance_f_max": {}, "PQ_band_g_max": {}}
    for k, v in verdict.items():
        o = _v7["verdict_24"].get(k)
        keys = ("F_S_min_N", "n_unseated", "cold_end_F_S_min_2250_N", "fibre_over_Rp_max", "screw_shakedown_min_MS", "max_screw_set_um", "max_wall_set_um",
                "F_S_max_N", "screw_fibre_max_MPa")
        mv["verdict_24"][k] = {kk: {"v7": (o or {}).get(kk), "v8": v[kk], "moved": (o or {}).get(kk) != v[kk]} for kk in keys}
    for e in KB:
        for st in SOAKS + ("PRELOAD",):
            r7 = chk[e]["states"].get(st)
            r6_ = _v7["calibration_bracket_and_model_check"][e]["states"].get(st)
            if r7 is None:
                continue
            mv["seat_force_vs_lowest_window"][f"{e}|{st}"] = {"model_F_c_N": r7["model"]["F_c_N"], "lowest_window_N": ENV[st]["seat_window_N"],
                                                              "from": LABEL[ENV[st]["seat_window_from"]], "rel_v8": r7["model_vs_lowest_seat_window_rel"],
                                                              "rel_v7": (r6_ or {}).get("model_vs_lowest_seat_window_rel")}
    for e in KB:
        mv["series_compliance_f_max"][e] = {"v7": _v7["a_series_compliance_IN718_seat_line"].get(e, {}).get("f_max"), "v8": sc.get(e, {}).get("f_max")}
    for k, v in band.items():
        mv["PQ_band_g_max"][k] = {"v7": _v7["PQ_select_fit_band_on_envelope_IN718"].get(k, {}).get("g_max_mm"), "v8": v["g_max_mm"]}
    mv["FA1S_window_and_M"] = {"lowest_window_N": ENV["FA1S"]["seat_window_N"], "from": LABEL[ENV["FA1S"]["seat_window_from"]],
                               "M_max_Nmm": ENV["FA1S"]["M_max_Nmm"], "M_from": LABEL[ENV["FA1S"]["M_from"]]}
    res["v7_to_v8_moves"] = mv
    s = json.dumps(res, indent=1, default=float)
    OUT.write_text(s)
    print(OUT.name, hashlib.sha256(s.encode()).hexdigest()[:16])
    print("K_B", {k: round(v) for k, v in KB.items()}, "N_RATIO", round(N_RATIO, 4), "tilt a b", round(A_M, 1), round(B_M, 4), "M_pre", M_PRE_ENV)
    for st in STATES:
        print(st, json.dumps(ENV[st]))
    for e, v in chk.items():
        print("==", e, v["k_b_N_mm"], "c_seat", v["c_seat"]["used"], v["c_seat"]["governing_state"], "c_ring", v["c_ring"]["used"], v["c_ring"]["governing_state"])
        for st, r in v["states"].items():
            print(f"   {st:7s} model F_S {r['model']['F_S_N']:7.1f} F_c {r['model']['F_c_N']:7.1f} F_sh {r['model']['F_sh_N']:7.1f} | "
                  + " | ".join(f"{LABEL[h]} {r[h]['N_head_N']:7.1f} ({r[h]['model_vs_FE_N_rel']:+.3f}) seat {r[h]['seat_window_N']:7.1f} "
                               f"({r[h]['model_vs_FE_seat_window_rel']:+.3f})" for h in H_at(st)) + f" | env N {r['model_vs_envelope_N_rel']:+.3f}")
    for k, v in verdict.items():
        print(f"  {k:62s} seated {v['all_seated']!s:5s} unseated {v['n_unseated']:2d} min {v['F_S_min_N']:6d} ({v['min_case']}, t {v['min_at']}) cold2250 "
              f"{v['cold_end_F_S_min_2250_N']:5d} set {v['max_wall_set_um']:6.1f} sset {v['max_screw_set_um']:6.3f} fib/Rp {v['fibre_over_Rp_max']:.3f} "
              f"shk {v['screw_shakedown_min_MS']:+.3f} Fmax {v['F_S_max_N']}")
    print(json.dumps(worse, indent=0)[:3000])
    print(json.dumps(sc, indent=1))
    print(json.dumps(sfb, indent=1)[:2500])
    print("k_b bracket", json.dumps(res["k_b_bracket"]))
    print("c move", json.dumps(res["c_move_v4_to_v5"]))
    print("MOVES", json.dumps({k: v for k, v in mv.items() if k != "verdict_24"}, default=float)[:4000])
    for k, v in mv["verdict_24"].items():
        print("MV", k, {kk: (x["v7"], x["v8"]) for kk, x in v.items() if x["moved"]})
    for k, v in band.items():
        print("PQ band", k, v["g_max_mm"], {st: (x["g_at_MS0_mm"], x["MS_at_gap"][0.078]) for st, x in v["per_state"].items()})
