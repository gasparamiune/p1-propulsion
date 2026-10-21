"""J-FWD screw-dependent rows re-issued for the ruled screw IN718 M5 x10 (ENG-HW-101-IN718), lead 11:25Z item 2, 11:41Z, 12:09Z item 5,
relay 12:28Z, relay 13:14Z, lead 14:03Z item 3, lead 14:14Z items 3-4, lead 14:34Z items 2-3, lead 15:37Z item 1, lead 16:53Z R2 / R4.
Mechanical, 2026-10-20, v7 (v6 d44587001b0b3c36 / json dbdb965a4160ec6e kept as jfwd_in718_rows_v352_v6.py;
v5 cc985da00b81ce97 / json 4d12e0187ac1a9c4 kept as jfwd_in718_rows_v352_v5.py; v4 802559c3a4e10834
/ json 6b41f1ce01e489f1 kept as jfwd_in718_rows_v352_v4.py; v3 0a8aa3f87c0fc8bc ACCEPTED by the lead 14:03Z, kept as jfwd_in718_rows_v352_v3.py;
v2 b92cef86a2bc3919 kept).  [DERIVED] from SIM (FEA3D js5 complete run + seat patches (a), (a') and (a'')); no new run.  CALC / DERIVED,
not physical approval.

v7 (lead 16:53Z R2 'ROUTE (i) ADOPTED, conditional on the rev-5 CAD check' (the CAD check passed: checks/test_rev5_jfwd_v2.json
32c41e1e207f9d64, reported 17:49:15Z, ACCEPTED 17:55:55Z) and R4 (union basis 36.401, rows v6 wording fix, datum B), and the lead's
rulings of 17:55:55Z on F1-F5: F1 the J-F1 MAXIMUM PRELOAD IS CAPPED AT 3750 N (J-F1 sets the flight-lot torque so that the lot's K_min
gives <= 3750 N; today's K window 0.1465-0.267 -> 2.747 N m and a minimum of 2058 N): the 3750 column is FE-anchored and GOVERNS every
row, the 4096 column is INFORMATION (superseded maximum); the under-head row is quoted at FULL FLOAT at 3750 N as a FLAG with the ASSUMED
mean-pressure tag; F2 the C4 registration (two GSE shoulder screws) is adopted: the tangential basis is the registered stack, 0.4865
(the method does not show that the drilling registration is reproduced, so the two-registration value is used, not 0.4085); F3 the head
form is adopted (fillet r 0.2-0.3 undercut into the head, pilot 5.15 h9 x 0.25-0.30, da 5.55-5.80); F4 the axial basis is 0.3705; F5
clocking +/-0.25 deg at match-drilling.  The screw-dependent rows move to route (i): ENG-HW-101-IN718 M5 x 10.7 +/-0.1 with the pilot and
the disc spring HW-170 (DIN EN 16983 A10 10 x 5.2 x 0.5, spring A baseline; spring B t 0.4 on M5 x 10.6 is the alternate) solid under
the head.
 - THE ROW (thread shear) on L 10.7 +/-0.1 with the spring under the head (t 0.44-0.52): L_e min 7.294, A_n 67.93 mm2 (flag +0.005 at
   SOAK52 4096 N, quoted as a flag by the lead 16:53Z R2); the no-spring L 10.2 row (68.13) is kept as the record.
 - TC-01 FLAT BEARING on the spring footprint (the spring is solid at every hot frame, spring v3): A_supp = spring annulus (De 9.85 h12
   minimum, Di 5.32 H12 maximum) on the worst-stack flat (half chord 4.6633 after the 0.1 flat-to-OD break) outside the 5.82 hole-break
   circle on the hole axis, the spring centre offset tangentially by the stated basis (raster, 0.002 mm; the exact paper area matches CAD
   within 0.052 mm2 at 9 points, test_rev5_jfwd_v2 (e)); quoted at the registered stack 0.4865 (F2), full float beside; the v6 head-
   direct row on the ADOPTED union basis (36.401, R4) is kept as the no-spring record.
 - TC-01 UNDER-HEAD BAND (Neuber) re-stated on the spring footprint (lead 16:53Z R2): sigma_el x A_ANN / A_supp (mean-pressure scaling,
   ASSUMED; FEA3D's band is under its centred head ring A_ANN 47.12; edge loading where the spring overhangs the flat's tangential edge is
   not represented: FE confirmation is the closure); every tangential basis is tabled (nominal centred, worst concentric, ruled 0.328,
   method 0.4085 (+0.04 axial), registered stack 0.4865, full float 0.557); quoted at FULL FLOAT (F1) as a FLAG, tag ASSUMED (the v6
   force-scaled value is kept beside as the record).
 - HEAD ON SPRING (IN718 side): dk 9.14 minimum / da 5.80 maximum (head form F3 PROPOSED 17:49:15Z: fillet r 0.2-0.3 undercut into the head,
   pilot 5.15 h9 x 0.25-0.30, ADOPTED F3), N / A vs IN718 Fty / Ftu at the screw temperature; the spring side (1.4568) is TO-SOURCE.
 - R4: SLACK_TXT wording corrected (the 24-case minimum is reached at the 2250 N and at the 4096 N installations alike; no number
   changes); rev5_drawing_items carry the datum frame as built in rev 5 (A = the 57.25 H8 bore axis, B = the TC-01 fwd end face).
 - the spring module jfwd_spring_v352.py asserts A_THE_ROW == 68.13 (no-spring basis): it is re-based on route (i) at its next run.

v6 (lead 15:37Z item 1, (b2) rulings R1-R3): every FE-anchored row is re-mapped on the adopted envelope = the worst of sharp + (b2)
('worst computed instance, not a proven bound'), read through relax v7: (b2) seat_s6L12_mu0 (drawn R0.2 bore-side break) is the fifth
history and its repeats SOAK_rep / SOAK52_rep are further instances of SOAK / SOAK52; the k_b bracket hi is re-calibrated on (b2) SOAK70
7471.8 N.  The ring-line family takes, for the (b2) instances, the d+6.051 z'0 line (the contact ring sits on it).  Items 3 and 4 (the
H12 / position-0.10 ring and the minimum wall) as v5.  Every quoted row that turns negative is flagged (flags_within_0.05_or_negative).
v6 corrections before publishing (lead 16:07Z items 2 and 3):
 - TC-02 THREAD ROW BASIS: THE ROW is the drawn M5 x 10.2 +/-0.1 (RULED 12:52Z) on the rev-5 flat (r_flat 31.313 +0.020/0 from the bore axis,
   ADOPTED 14:03Z) with the TC-01 wall seated: L_e min = (10.2 - 0.1) - wall max 2.708 - the 0.078 radial gap bound = 7.314 mm, A_n =
   strip area at L_e - 0.5 mouth (68.13 mm2); the local-gap-0 value (L_e 7.392) is information.  FEA3D's cell A_n 63.48 (v3.5.1 L_e 6.85)
   and the L 10.0 drawing bases were superseded at 13:14Z (2) and 14:03Z (2): kept only as labelled superseded records.  The per-state rows
   (states/*/rows/*/TC02_thread_shear_An), the full row and its fixes block (J-F1 maximum, length options) are re-based on THE ROW.
 - LABELS: the IN718 relax case key is relax v7's IN_KEY ('flight L 10.2 +/-0.1 ... k_b calibrated on the FE L 10.0, length effect ASSUMED
   small'); the A4-80 FE sub-rows carry js5 forces (SOAK70 5694.7, SOAK 7382.8, SOAK52 6559.9 N), not the envelope: relabelled
   'INFO_js5_history_A4-80_withdrawn' (information).

v5 (lead 14:14Z items 3 and 4; lead 14:34Z item 2 'C1 (g) Option A ADOPTED: d5.5 +0.12/0 (H12) ... Rows v5 use hole max 5.62 for both the
ring ID (max(5.62 + 0.2, da max 5.7 TO-VERIFY)) and the float' and item 3 'C1 (h) ADOPTED: hole position 0.10 dia to A|B, spot face coaxial
to its hole within 0.10 dia ... Rows v5 carry the resulting eccentricity in the flat stack, together with float, OD h9 and runout'):
 (a) THE QUOTED TC-01 FLAT-BEARING ROW is on the rev-5 minimum bearing ring, not on FEA3D's jfwd_spotface.py A_ANN 47.12 mm2 (dk 9.5,
     superseded for quoted rows): A = pi/4 (dk_min^2 - ID^2) - worst-stack loss, dk_min 9.14 (ISO 7380-1 M5), ID = max(hole max 5.62 + 2 x 0.1
     flat-side break, da max 5.7 TO-VERIFY) = 5.82; worst stack: OD 63.426 (63.5 h9 minimum), eccentricity 0.02 (runout 0.04 / 2), r_flat
     31.333 (31.313 +0.020/0 maximum), flat-to-OD break 0.1 (C1 (c), ISO 13715 removal read along the flat: the conservative reading, the
     value without it is shown beside), head offset toward the flat edge = float (5.62 - 4.826) / 2 = 0.397 (M5 6g major minimum 4.826)
     + hole position 0.10 dia / 2 = 0.05; MS = (1 + MS_full) x A / A_ANN - 1 on the row's own force (A_ANN = FEA3D's 47.12 basis of
     MS_full).  FOUND, shown beside as information and RECOMMENDED: with the screw at full float the da circle (screw axis) and the
     hole-break circle (hole axis) are 0.397 apart, so the unsupported inner region is their UNION, not the larger circle; the
     union-based ring is quoted beside the ruled row (numerical raster, cross-checked on the ruled ring).  Head clear of the d10.5 +0.2/0
     pocket wall: float + coaxiality 0.397 + 0.05 = 0.447 <= 0.5 (dk max 9.5).
 (b) THE TC-01 CASE MEMBRANE ROWS (03-cad/calcs hand_calcs_v2.json, Lame + end load at the bore, von Mises, 20 C allowables, T_allow =
     highest T with MS >= 0) on the MINIMUM WALL: OD 63.5 h9 minimum 63.426; bore 57.15 max 57.25 (NO DRAWN TOLERANCE TODAY: rev 5 gets
     '57.15 +/-0.10', the maximum equal to the 57.25 H8 seal-land clean-up bound); fwd seal land 57.25 H8 maximum 57.296 (the forward end
     load on 57.296); collar groove 62.50 h9 minimum 62.426; aft seal land 61.0 f7 minimum 60.940; aft thread M63 x 1.5 root d3 minimum
     61.160 - 0.067 - 0.160 = 60.933 (6e: es = -(50 + 11 P) um, Td2(6) = 90 P^0.4 d^0.1 um, ISO 965-1 formulas AS RECALLED, TO-VERIFY;
     d3 minimum taken as d3 + es - Td2).  The aft rows keep the hand calc's end load on d 61.0 (its bound); T_allow is compared with the
     SIM TC-01 part maximum while pressurised (burn, rev-4 thermal both bounds; the soak is unpressurised).  FLAGS for rev 5: the TC-01
     drawing fits list says M63x1.5-6e, its notes say 6g (6e used here: the thinner root); the datum frame is 'fwd end face A, axis B', so
     the lead's 14:03Z 'r_flat from datum A' and 'runout 0.04 to A' read as 'from axis B' and 'to B'.

v4 (lead 14:03Z item 3, rev 5: r_flat 31.313 +0.020/0 from A, TC-01 OD 63.5 h9 with circular runout 0.04 to A, both ADOPTED):
 (a) every TC-01 flat-bearing row carries the worst-stack supported-area loss on the row's own area basis.  The row is FEA3D's
     jfwd_spotface.py head_bearing 'flat_seat_MS_vs_Fbry' = Fbry / (F_head / A_ANN) - 1 with A_ANN = pi/4 (9.5^2 - 5.5^2) = 47.12 mm2 (dk 9.5);
     at the worst stack (OD 63.426 = 63.5 h9 minimum, eccentricity 0.02 = runout 0.04 / 2, r_flat 31.333 = rule maximum, head at the full
     float 0.337 tangentially) the head ring beyond the flat's tangential edge is CALC 0.749 mm2 for dk 9.5 and 0.218 mm2 for dk 9.14; on the
     47.12 basis the smaller supported area is 47.12 - 0.749 -> the row x (1 - 0.749 / 47.12).  The full-flat value is kept beside.
     INFORMATION (not applied, the row's own basis is kept as ruled): the 47.12 basis is the dk 9.5 MAXIMUM head; at the dk 9.14 minimum the
     ring is 41.85 mm2 (41.63 after its 0.218 loss).
 (b) the TC-01 case membrane rows (03-cad/calcs hand_calcs_v2.json, Lame + end load at the bore) use the NOMINAL OD 63.5 and the nominal
     bore (walls 3.175 full wall / 3.125 fwd seal land / 2.675 collar groove): the h9 radial -0.037 (and the H8 maximum bore +0.023 at the
     fwd seal land) re-evaluated on every row whose outer surface is the 63.5 OD; the aft seal land (61.0) and the aft thread (M63 x 1.5) are
     separate diameters.
 Otherwise as v3 (the screw LCF row is jfwd_screw_lcf_v352, on this json).

v3: relaxation v6 (four histories: (a'') = seat_s5L12_mu0_go joins; FEA3D envelope 336568296bdb896f): every row takes the worst of the four
histories per state and quantity; k_b lo re-calibrated on (a'') SOAK70; the PRELOAD moment envelope is (a'')'s.  Otherwise as v2.

v2: (1) the envelope is FEA3D's 12:21Z three-history envelope (js5, (a), (a'); results/v352/jfwd_soak_envelope_v352.json 1d970741cb95a885,
read through relax v5 which cross-checks it): SOAK70 N max 6389 (a), SOAK 7383 (js5), SOAK52 6742 (a'); (2) the k_b bracket of relax v5
(lo on (a') SOAK70 5627.3 N, hi on (a) SOAK70 6389.1 N); (3) FEA3D's TC-01 ligament-station P+Q is scaled per history (js5 only reports
that station: N_IN,js5 / N_js5) and carried as INFORMATION (contact-edge field, 0.08 mm from the hole wall, like the hole-edge line class
of 239 (9)); the envelope-scaled value is quoted beside it; (4) the TC-02 A_n thread-shear FULL ROW (lead 12:09Z item 5) with the
engagement basis and the cheapest fixes and their slack effect.

Basis (stated per row in the output):
 - FE ANCHOR = the worst of the sharp-edge histories per state and per quantity (lead 11:41Z): highest screw N, lowest seat window,
   lowest MS per line, highest screw section moment.  A4-80 values are the FE's own (the FE screw is A4-80); IN718 is mapped onto them.
 - IN718 screw force per history h and state: N_IN = F_V + (N_h - F_V) x r, r = (model IN718 soak gain) / (model A4-80 soak gain) at that
   state's temperatures (relax v5 joint model; max over the k_b bracket; F_V = 3750 N, the FE preload).  dF_S / dF_V = 1.000 in the
   model at every soak state, so the J-F1 maximum 4096 N adds 346 N.  Rows are given at 3750 N (the FE basis, as FEA3D's cells) and at
   4096 N (the J-F1 maximum: 239 (3) 'strength checks at the maximum preload'; 239 (8)(a) P+Q at 3750 and 4096 N).
 - force-driven rows scale with N_IN / N_h on the FE row of the same history (screw tension, thread shear, flat bearing, under-head band,
   Pm line counts): conservative where part of the stress is thermal and of the same sign.
 - seat / ring-line P+Q: (i) model-consistent, P+Q x F_sh,model(IN718) / F_sh,model(A4-80) (the lines track the shell pull, relax v4
   item 4); (ii) bound, P+Q x N_IN / N_h.  The row is (i); (ii) is quoted beside and flagged where the two straddle zero.
 - screw moment for IN718: M_h x E ratio (imposed rotation) x max(1, F_c,IN / F_c,h) (the extra screw force goes to the seat contact,
   K_C / (K_C + k_sh) of it): the product, conservative.
 - allowables: IN718 Fty / Ftu(T) AMS 5662/5663 minima (Special Metals SMC-045, engmat DATASHEET); AL6061-T6 engmat (10,000 h basis,
   LITERATURE); TC-02 thread Fsy = 0.577 Fty, Fsu = 0.6 Ftu (FEA3D's rule, back-computed from its cells and verified); FEA3D's Neuber
   (eps = s / E + 0.002 (s / Fty)^n, n 15 and 30, eps_limit of the node, the lower MS) reproduced exactly on js5 SOAK.
 - TC-02 A_n (v6 correction, lead 16:07Z (2)): THE ROW = the drawn M5 x 10.2 +/-0.1 on the rev-5 flat, TC-01 wall seated, 0.078 gap
   bound (L_e 7.314, A_n 68.13 mm2).  SUPERSEDED RECORD (13:14Z (2), 14:03Z (2)): FEA3D's cell A_n = N / tau = 63.48 mm2 (strip area at
   L_eff 6.35 = the v3.5.1 engagement 6.85 less the 0.5 mm mouth) and the L 10.0 drawing bases.
 - every row within 0.05 of zero (or negative) is flagged for an FE confirmation (lead 11:25Z)."""
import json, math, hashlib, importlib.util
from pathlib import Path

J = Path("/home/claude/work/mechanical/v352/jfwd")
OUT = J / "jfwd_in718_rows_v352_v7.json"
_spec = importlib.util.spec_from_file_location("jfwd_relax_v352_v6", str(J / "jfwd_relax_v352.py"))
R = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R)
assert "v7 (v6 9465eaeac9af407f" in R.__doc__
sha = R.sha
tab = R.tab
CELLS = json.loads(R.F_CELLS.read_text())["steps"]
FIX2 = J / "jfwd_fix_v352_v2.json"
fix2 = json.loads(FIX2.read_text())
SEAT1 = J / "jfwd_seat_v352_v1.json"
seat1 = json.loads(SEAT1.read_text())
_ns = {}
exec(compile((J / "jfwd_v352.py").read_text().split("\nOPTS = [")[0], str(J / "jfwd_v352.py"), "exec"), _ns)
strip_area, TH = _ns["strip_area"], _ns["TH"]["M5"]
IN, A4 = R.IN718_S, R.A4_80
FV0, FVMAX = 3750.0, 4096.0
# v7 (lead 17:55:55Z F1): the J-F1 maximum is CAPPED at 3750 N = FV0 (the FE preload): the 3750 column governs; FVMAX 4096 is INFORMATION
JF1_K_WIN, JF1_D = (0.1465, 0.267), 5.0                               # J-F1 K window (today's lot basis) and the M5 nominal diameter
JF1_T_NMM = FV0 * JF1_K_WIN[0] * JF1_D                                # torque that gives 3750 N at K_min: 2746.9 N mm (2.747 N m)
JF1_MIN = JF1_T_NMM / (JF1_K_WIN[1] * JF1_D)                          # 2057.6 N at K_max (lead: 'about 2060 N'; or the J-F1 lot result)
JF1_TAG = {"3750": "GOVERNING (J-F1 maximum, FE-anchored)", "4096": "INFORMATION (superseded maximum, lead 17:55:55Z F1)"}
A_S, Z_3 = IN.A_s, IN.Z_3
HS = R.H
LBL = R.LABEL
_RXJ = J / "jfwd_relax_v352_v7.json"                                  # v6: the relax v7 24-case result (run before this script)
_RX = json.loads(_RXJ.read_text())["worse_end_quoted"]
_INK = R.IN_KEY                                                       # lead 16:07Z (3) label
SLACK_TXT = (f"none from this fix: the 24-case minimum is reached at the 2250 N and at the 4096 N installations alike (the first-firing "
             f"wall set at the Fty(T) cap absorbs the installation preload; relax v7, worse k_b end: seat line "
             f"{_RX[_INK + '|seat']['F_S_min_N']} N, {_RX[_INK + '|seat']['n_unseated']} of 24 unseated; ring family "
             f"{_RX[_INK + '|ring']['F_S_min_N']} N, {_RX[_INK + '|ring']['n_unseated']} of 24 unseated)")
FLAG = 0.05


def flag(ms):
    return None if ms is None else ("NEGATIVE: FE confirmation" if ms < 0 else ("within 0.05: FE confirmation" if ms < FLAG else None))


def ms(allow, act):
    return round(allow / act - 1.0, 3)


def neuber(sel, E, Fty, n):
    lo, hi = 1e-9, max(sel, 1e-6)
    for _ in range(200):
        s = 0.5 * (lo + hi)
        e = s / E + 0.002 * (s / Fty) ** n
        lo, hi = (s, hi) if s * e < sel * sel / E else (lo, s)
    return s, s / E + 0.002 * (s / Fty) ** n


def cmp_side(h, st):
    """the compare-file column of history h at state st: js5 = the global columns of patch (a)'s compare (identical in every patch's file,
    checked in relax v5); a patch = its own 'patch' columns; v6: the (b2) repeat instances read their *_rep steps (relax v7 src_of)."""
    if h == "js5":
        return R._CM["patch_a"]["steps"][st]["global_same_sets"]
    hp, step = R.src_of(h, st)
    return R._CM[hp]["steps"][step]["patch"]


def cmp_lines(h, st):
    if h == "js5":
        return R._CM["patch_a"]["steps"][st]["relax_seat_lines_cmp"], "Pm_global"
    hp, step = R.src_of(h, st)
    return R._CM[hp]["steps"][step]["relax_seat_lines_cmp"], "Pm_patch"


# ---- IN718 / A4-80 gain ratio per state (model, both k_b ends; max) and the FA1S thermal delta (uniform 45.6 C, no pressure)
RATIO, FSH_RATIO = {}, {}
for st in R.SOAKS:
    rs, fs = [], []
    for e, kb in R.KB.items():
        a = R.model_state(st, kb, A4)
        b = R.model_state(st, kb, IN)
        rs.append((b[0] - FV0) / (a[0] - FV0))
        fs.append(b[3] / a[3])
    RATIO[st], FSH_RATIO[st] = max(rs), max(fs)
DFA1S = []
for e, kb in R.KB.items():
    _, dwa, dra = A4.deltas(45.6, 45.6)
    _, dwi, dri = IN.deltas(45.6, 45.6)
    DFA1S.append(R.state_s(FV0, R.G0, dwi, dri, 0, 0, R.K_SH_JS5, kb * IN.kb_ratio)[0] - R.state_s(FV0, R.G0, dwa, dra, 0, 0, R.K_SH_JS5, kb)[0])
D_FA1S = max(DFA1S)
D_FVMAX = max(R.model_state("SOAK", kb, IN, FV=FVMAX)[0] - R.model_state("SOAK", kb, IN, FV=FV0)[0] for kb in R.KB.values())


def n_in(st, h, FV=FV0):
    N = R.HISTS[st][h]["N_head_N"]
    if st == "PRELOAD":
        base = FV0
    elif st == "FA1S":
        base = N + D_FA1S
    else:
        base = FV0 + (N - FV0) * RATIO[st]
    return base + (FV - FV0) * (1.0 if st in ("PRELOAD", "FA1S") else D_FVMAX / (FVMAX - FV0))


# ---- v4 (a): rev-5 worst-stack supported area of the head ring on the TC-01 flat (CALC; lead 14:03Z item 3(a))
A_ANN = math.pi / 4.0 * (9.5 ** 2 - 5.5 ** 2)          # FEA3D jfwd_spotface.py A_ANN (the flat-bearing row's own basis)


def _segment(rh, d):
    """area of a circle of radius rh beyond a straight line at distance d from its centre"""
    if d >= rh:
        return 0.0
    if d <= -rh:
        return math.pi * rh * rh
    return rh * rh * math.acos(d / rh) - d * math.sqrt(rh * rh - d * d)


def flat_stack(od_min=63.5 - 0.074, ecc=0.02, rf_max=31.333, flt=0.337):
    R_loc = od_min / 2.0 - ecc
    half = math.sqrt(R_loc ** 2 - rf_max ** 2)
    out = {"OD_min_mm": od_min, "eccentricity_mm": ecc, "r_flat_max_mm": rf_max, "float_mm": flt, "chord_mm": round(2 * half, 3),
           "chord_nominal_OD_no_runout_mm": round(2 * math.sqrt(31.75 ** 2 - rf_max ** 2), 3)}
    for dk in (9.5, 9.14):
        out[f"loss_dk{dk:g}_mm2"] = round(_segment(dk / 2.0, half - flt), 3)
        out[f"ring_dk{dk:g}_mm2"] = round(math.pi / 4.0 * (dk ** 2 - 5.5 ** 2), 2)
        out[f"overhang_dk{dk:g}_mm"] = round(max(0.0, flt + dk / 2.0 - half), 3)
    out["supported_fraction_row_basis"] = round(1.0 - out["loss_dk9.5_mm2"] / A_ANN, 5)
    out["info_dk9.14_min_head_supported_mm2"] = round(out["ring_dk9.14_mm2"] - out["loss_dk9.14_mm2"], 2)
    out["info_dk9.14_fraction_of_row_basis"] = round(out["info_dk9.14_min_head_supported_mm2"] / A_ANN, 5)
    return out


FLAT_V4 = flat_stack()

# ---- v5 (a): the rev-5 minimum bearing ring and the worst stack (lead 14:14Z item 3, 14:34Z items 2-3)
DK_MIN, DK_MAX, DA_MAX = 9.14, 9.5, 5.7          # ISO 7380-1 M5: dk 9.14-9.5; da max 5.7 (TO-VERIFY against the standard)
HOLE_MAX, BRK_HOLE, BRK_OD = 5.5 + 0.12, 0.1, 0.1  # d5.5 +0.12/0 (H12, ADOPTED 14:34Z); C1 (b) flat-side hole break 0.1 max; C1 (c) flat-to-OD 0.1 max
D_MAJ_MIN = 4.826                                 # M5 6g major diameter minimum (jfwd_v352 strip-area basis)
POS_DIA, COAX_DIA, POCKET_D = 0.10, 0.10, 10.5   # hole position 0.10 dia to A|B; spot face coaxial 0.10 dia; spot face d10.5 +0.2/0


def _ring_union_area(rh, r_da, r_hole, off_head, off_hole, half_eff, step=0.002):
    """head bearing area by raster: inside the head circle (radius rh, centre off_head from the flat's chord centre, tangential), inside
    the flat strip |t| <= half_eff, outside the da circle (centre = head) and outside the hole-break circle (centre off_hole)."""
    import numpy as np
    n = int(math.ceil(2 * rh / step))
    g = (np.arange(n) + 0.5) * step - rh
    T, Z = np.meshgrid(g, g, indexing="ij")
    rr = T * T + Z * Z
    t_abs = T + off_head
    ins = (rr <= rh * rh) & (np.abs(t_abs) <= half_eff) & (rr >= r_da * r_da) & ((t_abs - off_hole) ** 2 + Z * Z >= r_hole * r_hole)
    return float(ins.sum()) * step * step


def flat_stack_v5(od_min=63.5 - 0.074, ecc=0.02, rf_max=31.333):
    R_loc = od_min / 2.0 - ecc
    half = math.sqrt(R_loc ** 2 - rf_max ** 2)
    flt = (HOLE_MAX - D_MAJ_MIN) / 2.0
    pos = POS_DIA / 2.0
    off = flt + pos                                 # screw (head) axis to the chord centre, toward one flat edge
    idr = max(HOLE_MAX + 2 * BRK_HOLE, DA_MAX)
    rh = DK_MIN / 2.0
    ring = math.pi / 4.0 * (DK_MIN ** 2 - idr ** 2)
    out = {"inputs": {"OD_min_mm": od_min, "eccentricity_mm": ecc, "r_flat_max_mm": rf_max, "dk_min_mm": DK_MIN, "da_max_mm_TO-VERIFY": DA_MAX,
                      "hole_max_mm": HOLE_MAX, "hole_flat_side_break_mm": BRK_HOLE, "flat_to_OD_break_mm": BRK_OD, "screw_major_min_mm": D_MAJ_MIN,
                      "float_mm": round(flt, 4), "hole_position_radius_mm": pos, "spot_face_coaxiality_radius_mm": COAX_DIA / 2.0},
           "half_chord_mm": round(half, 4), "half_chord_after_OD_break_mm": round(half - BRK_OD, 4), "head_offset_to_chord_centre_mm": round(off, 4),
           "ring_ID_ruled_mm": idr, "ring_ruled_mm2": round(ring, 3)}
    for tag, he in (("row_with_OD_break", half - BRK_OD), ("info_without_OD_break", half)):
        loss = _segment(rh, he - off)
        out[tag] = {"half_eff_mm": round(he, 4), "edge_distance_from_head_axis_mm": round(he - off, 4), "loss_mm2": round(loss, 3),
                    "A_ruled_mm2": round(ring - loss, 3)}
    # the union of the da circle (screw axis) and the hole-break circle (hole axis, the screw displaced by the full float toward the edge)
    he = half - BRK_OD
    a_union = _ring_union_area(rh, DA_MAX / 2.0, (HOLE_MAX + 2 * BRK_HOLE) / 2.0, off, pos, he)
    a_check = _ring_union_area(rh, idr / 2.0, idr / 2.0, off, off, he)          # concentric ruled ring by the same raster
    out["info_union_inner_boundary"] = {"A_mm2": round(a_union, 3), "raster_check_ruled_ring_mm2": round(a_check, 3),
                                        "raster_check_vs_analytic_mm2": round(a_check - out["row_with_OD_break"]["A_ruled_mm2"], 3),
                                        "difference_to_ruled_mm2": round(a_union - out["row_with_OD_break"]["A_ruled_mm2"], 3),
                                        "note": ("with the screw at full float the head's da circle (centred on the screw) and the hole-break circle "
                                                 "(centred on the hole, 0.397 away) do not coincide; the head bears nowhere inside either, so the "
                                                 "unsupported inner region is their union (RECOMMENDED basis; the lead's rule takes the larger circle "
                                                 "on the screw axis)")}
    out["pocket_wall_check"] = {"head_offset_in_pocket_mm": round(flt + COAX_DIA / 2.0, 4), "radial_clearance_dk_max_mm": round((POCKET_D - DK_MAX) / 2.0, 4),
                                "clear": bool(flt + COAX_DIA / 2.0 <= (POCKET_D - DK_MAX) / 2.0 + 1e-9)}
    out["far_edge_check"] = {"far_edge_distance_mm": round(he + off, 4), "head_radius_mm": rh, "no_loss_at_far_edge": bool(he + off >= rh)}
    return out


FLAT = flat_stack_v5()
A_ROW = FLAT["row_with_OD_break"]["A_ruled_mm2"]
A_ROW_NOBRK = FLAT["info_without_OD_break"]["A_ruled_mm2"]
A_UNION = FLAT["info_union_inner_boundary"]["A_mm2"]

# ---- v7 route (i): the disc spring footprint on the TC-01 flat (lead 16:53Z R2, 17:55:55Z F1 / F2; CAD check test_rev5_jfwd_v2 (e), (h))
CK5 = Path("/home/claude/work/mechanical/v352/checks/test_rev5_jfwd_v2.json")
_ck5 = json.loads(CK5.read_text())
assert hashlib.sha256(CK5.read_bytes()).hexdigest()[:16] == "32c41e1e207f9d64", "CAD check v2"
_h5 = _ck5["h_positional_stack_on_the_method"]
SPR_DE, SPR_DI = (9.85, 10.0), (5.20, 5.32)      # DIN EN 16983 De h12 / Di H12 (Schnorr brochure 2024-02 p. 10; Lesjofors 7909 'Di tol +0.12')
HOLE_BRK = HOLE_MAX + 2 * BRK_HOLE                # 5.82: hole max + the 0.1 flat-side break each side (C1 (b))
UH_BASES = {      # spring centre offset from its hole / flat axis: (tangential, axial) mm; None = the nominal centred like-for-like case
    "nominal_centred_like_for_like_v6": None,
    "worst_stack_concentric": (0.0, 0.0),
    "ruled_0.328_withdrawn_F4": (0.328, 0.0),
    "method_tangential_stack_0.4085": (_h5["tangential_stack_mm"], 0.040),
    "registered_stack_0.4865_F2": (_h5["tangential_stack_two_registrations_mm"], 0.040),
    "full_float_0.557": (_h5["full_float_info_mm"]["value"], 0.0)}
assert abs(UH_BASES["registered_stack_0.4865_F2"][0] - 0.4865) < 1e-9 and abs(UH_BASES["full_float_0.557"][0] - 0.557) < 1e-9
QUOTED_UH_BASIS = "full_float_0.557"              # lead 17:55:55Z F1: under-head row at FULL FLOAT, 3750 N, FLAG, ASSUMED
QUOTED_FLAT_BASIS = "registered_stack_0.4865_F2"  # lead 17:55:55Z F2: the tangential basis is the registered stack (0.4865)


def _spring_area(ro, ri, he, rh, e_t, e_z, step=0.002):
    """spring annulus (ro, ri) centred (e_t, e_z) from the hole axis, inside the flat strip |t| <= he, outside the hole-break circle (rh) on
    the hole axis; raster (v7; the CAD check v2 (e) cross-checks the same construction within 0.052 mm2)"""
    import numpy as np
    n = int(math.ceil(2 * ro / step)) + 2
    g = (np.arange(n) + 0.5) * step - ro - step
    T, Z = np.meshgrid(g, g, indexing="ij")
    rr = T * T + Z * Z
    tt, zz = T + e_t, Z + e_z
    ins = (rr <= ro * ro) & (rr >= ri * ri) & (np.abs(tt) <= he) & (tt * tt + zz * zz >= rh * rh)
    return float(ins.sum()) * step * step


HE_WS = FLAT["half_chord_after_OD_break_mm"]
HC_NOM = math.sqrt(31.75 ** 2 - 31.313 ** 2)
A_SPR = {}
for _k, _v in UH_BASES.items():
    if _v is None:   # nominal: De 10.0 / Di 5.2, hole 5.5 + 0.1 break each side, nominal OD and r_flat (half chord 5.2496 - 0.1), centred
        A_SPR[_k] = round(_spring_area(5.0, 2.6, HC_NOM - BRK_OD, (5.5 + 2 * BRK_HOLE) / 2.0, 0.0, 0.0), 3)
    else:
        A_SPR[_k] = round(_spring_area(SPR_DE[0] / 2.0, SPR_DI[1] / 2.0, HE_WS, HOLE_BRK / 2.0, _v[0], _v[1]), 3)
# the raster on the CAD check's own construction (De 10 / Di 5.2, no breaks) against every CAD point that returned a body
_e5 = _ck5["e_supported_area"]
XCHK = {}
for _blk, (_he, _rh) in (("nominal_CAD", (HC_NOM, 2.75)), ("worst_stack_tube", (_e5["worst_stack_tube_basis"]["half_chord_mm"], 2.81))):
    for _key, _rec in _e5[_blk].items():
        if _rec["A_CAD_mm2"] <= 1.0:
            continue
        _et, _ez = (float(_x[3:]) for _x in _key.split("|"))
        _ar = _spring_area(5.0, 2.6, _he, _rh, _et, _ez)
        XCHK[f"{_blk}|{_key}"] = {"A_CAD_mm2": _rec["A_CAD_mm2"], "A_raster_mm2": round(_ar, 3), "diff_mm2": round(_rec["A_CAD_mm2"] - _ar, 3)}
assert len(XCHK) == 9 and max(abs(_v["diff_mm2"]) for _v in XCHK.values()) < 0.06, XCHK
DA_HEAD_MAX, DK_HEAD_MIN = 5.80, DK_MIN          # F3 ADOPTED 17:55:55Z: fillet r 0.2-0.3 undercut into the head, da 5.55-5.80, dk 9.14 min
A_HEAD_SPRING = math.pi / 4.0 * (DK_HEAD_MIN ** 2 - DA_HEAD_MAX ** 2)


def rows_state(st):
    c = CELLS[st]
    out = {"state": st, "kind": c["kind"], "histories": {}}
    for h in R.H_at(st):
        out["histories"][LBL[h]] = {"entered_from": R.HISTS[st][h]["entered_from"], "N_FE_A4-80_N": R.HISTS[st][h]["N_head_N"],
                                    "N_IN718_3750_N": round(n_in(st, h), 1), "N_IN718_4096_N": round(n_in(st, h, FVMAX), 1)}
    henv = max(R.H_at(st), key=lambda h: n_in(st, h))
    out["N_envelope_from"] = LBL[henv]
    rows = {}
    for FV, tag in ((FV0, "3750"), (FVMAX, "4096")):
        Nenv = n_in(st, henv, FV)
        r = {}
        # (1) screw tension 234 (1)(b) (soak form; PRELOAD and FA1S tension shown for information, FA1S governing = Eq. 22 below)
        Ts = c["SCREW"]["T_C"]
        sig = Nenv / A_S
        Fy, Fu = tab("IN718", "Fty", Ts), tab("IN718", "Ftu", Ts)
        r["screw_tension_234_1b"] = {"N_N": round(Nenv, 1), "from": LBL[henv], "sigma_As_MPa": round(sig, 1), "T_C": Ts, "Fty_IN718_MPa": round(Fy, 1),
                                     "Ftu_IN718_MPa": round(Fu, 1), "MS_y": ms(Fy, sig), "MS_u": ms(Fu, sig),
                                     "INFO_js5_history_A4-80_withdrawn_MS_y_at_FE_N": c["SCREW"].get("MS_y") if st != "FA1S" else None}
        # (2) TC-02 internal thread shear on THE ROW (v6 correction, lead 16:07Z (2)): the drawn M5 x 10.2 +/-0.1 on the rev-5 flat, TC-01 wall
        #     seated, 0.078 gap bound (A_n 68.13); allowables at FEA3D's TC-02 thread temperature (back-computed from its cell, checked
        #     against engmat); FEA3D's cell A_n (63.48, v3.5.1 L_e 6.85) is a SUPERSEDED RECORD only
        th = c["TC-02"]["thread_shear_An"]
        Nfe_js5 = R.HISTS[st]["js5"]["N_head_N"] if st != "FA1S" else c["SCREW"]["N_exact_N"]
        A_n_fea = Nfe_js5 / th["tau_MPa"]
        fsy, fsu = (1 + th["MS_y"]) * th["tau_MPa"], (1 + th["MS_u"]) * th["tau_MPa"]
        T2 = th["T_C"]
        assert abs(fsy - 0.577 * tab("AL6061-T6", "Fty", T2)) < 0.6 and abs(fsu - 0.6 * tab("AL6061-T6", "Ftu", T2)) < 0.6
        tau = Nenv / A_THE_ROW
        r["TC02_thread_shear_An"] = {"basis": THE_ROW_LABEL, "A_n_mm2": A_THE_ROW, "L_e_min_mm": THE_ROW["L_e_gap_bound_mm"], "T_C": T2,
                                     "N_N": round(Nenv, 1), "from": LBL[henv], "tau_MPa": round(tau, 1), "Fsy_MPa": round(fsy, 1),
                                     "Fsu_MPa": round(fsu, 1), "MS_y": ms(fsy, tau), "MS_u": ms(fsu, tau),
                                     "info_local_gap_0": {"L_e_mm": THE_ROW["L_e_gap0_mm"], "A_n_mm2": THE_ROW["A_n_gap0_mm2"],
                                                          "MS_y": ms(fsy, Nenv / THE_ROW["A_n_gap0_mm2"]), "MS_u": ms(fsu, Nenv / THE_ROW["A_n_gap0_mm2"])},
                                     "SUPERSEDED_RECORD_FEA3D_cell_A_n": {"A_n_mm2": round(A_n_fea, 2), "tau_MPa": round(Nenv / A_n_fea, 1),
                                                                          "MS_y": ms(fsy, Nenv / A_n_fea), "MS_u": ms(fsu, Nenv / A_n_fea),
                                                                          "label": "v3.5.1 L_e 6.85 - 0.5; superseded 13:14Z (2) / 14:03Z (2), record only"},
                                     "INFO_js5_history_A4-80_withdrawn": {"MS_y": th["MS_y"], "MS_u": th["MS_u"], "at_N": Nfe_js5}}
        # (3) TC-01 spot-face flat bearing (FEA3D seat_values_DERIVED, head force on the flat) and the under-head band (Neuber)
        if st != "FA1S":
            fb = c["TC-01"]["cell"]["seat_values_DERIVED"]["flat_seat_bearing_MS_vs_Fbry"]
            full = (1 + fb) * Nfe_js5 / Nenv - 1.0
            spr_fb = {k: round((1 + full) * A / A_ANN - 1.0, 3) for k, A in A_SPR.items()}
            r["TC01_flat_bearing"] = {"MS_vs_Fbry": spr_fb[QUOTED_FLAT_BASIS], "area_mm2": A_SPR[QUOTED_FLAT_BASIS],
                                      "area_basis": (f"route (i): spring footprint at the {QUOTED_FLAT_BASIS} tangential basis (De 9.85 / Di 5.32 on the "
                                                     "worst-stack flat after the 0.1 OD break, outside the 5.82 hole-break circle)"),
                                      "MS_by_spring_basis": spr_fb, "areas_by_spring_basis_mm2": A_SPR,
                                      "NO_SPRING_RECORD_union_basis_R4": round((1 + full) * A_UNION / A_ANN - 1.0, 3), "no_spring_union_area_mm2": A_UNION,
                                      "NO_SPRING_RECORD_A_ROW": round((1 + full) * A_ROW / A_ANN - 1.0, 3), "no_spring_A_ROW_mm2": A_ROW,
                                      "info_MS_full_flat_on_A_ANN_47.12_superseded": round(full, 3),
                                      "F_over_Fbry_mm2": round(A_ANN / (1 + full), 3), "INFO_js5_history_A4-80_withdrawn_MS_at_FE_N": fb}
        uh = {}
        for h in R.H_at(st):
            Nh = R.HISTS[st][h]["N_head_N"]
            Ni = n_in(st, h, FV)
            if h == "js5":
                nb = c["TC-01"]["neuber_band"]
                sel0, T, E, Fty, el = nb["sigma_el_MPa"], nb["T_C"], nb["E_MPa"], nb["Fty_MPa"], nb["eps_limit"]
            else:
                ub = cmp_side(h, st)["under_head_band"]
                sel0, T, Fty, el = ub["vm_MPa"], ub["T_C"], ub["Fty_MPa"], ub["eps_limit"]
                E = tab("AL6061-T6", "E", T)
            sel = sel0 * Ni / Nh
            mss = []
            for n in (15, 30):
                s_, e_ = neuber(sel, E, Fty, n)
                mss.append(round(el / e_ - 1.0, 3))
            spr_uh = {}
            for k, A in A_SPR.items():
                spr_uh[k] = min(round(el / neuber(sel * A_ANN / A, E, Fty, n)[1] - 1.0, 3) for n in (15, 30))
            uh[LBL[h]] = {"sigma_el_A4-80_MPa": sel0, "sigma_el_IN718_MPa": round(sel, 1), "T_C": T, "eps_limit": el,
                          "V6_RECORD_MS_strain_n15_n30_head_direct_force_scaled": mss, "V6_RECORD_MS_strain": min(mss),
                          "sigma_el_spring_quoted_MPa": round(sel * A_ANN / A_SPR[QUOTED_UH_BASIS], 1),
                          "MS_strain_by_spring_basis": spr_uh, "MS_strain": spr_uh[QUOTED_UH_BASIS]}
        hw = min(uh, key=lambda k: uh[k]["MS_strain"])
        r["TC01_under_head_band_neuber"] = {"per_history": uh, "MS_strain": uh[hw]["MS_strain"], "from": hw,
                                            "quoted_basis": f"{QUOTED_UH_BASIS} (lead 17:55:55Z F1), mean-pressure scaling ASSUMED",
                                            "tag": "ASSUMED (sigma_el x A_ANN 47.12 / A_supp; edge loading at the tangential overhang not represented)",
                                            "by_basis_min": {k: min(uh[q]["MS_strain_by_spring_basis"][k] for q in uh) for k in A_SPR},
                                            "V6_RECORD_min": min(uh[q]["V6_RECORD_MS_strain"] for q in uh)}
        # v7: head on the spring (IN718 side), dk 9.14 min / da 5.80 max (F3 ADOPTED); the spring side is TO-SOURCE
        sig_hs = Nenv / A_HEAD_SPRING
        r["head_on_spring_IN718"] = {"A_mm2": round(A_HEAD_SPRING, 2), "N_N": round(Nenv, 1), "from": LBL[henv], "sigma_MPa": round(sig_hs, 1), "T_C": Ts,
                                     "MS_y": ms(Fy, sig_hs), "MS_u": ms(Fu, sig_hs),
                                     "basis": "dk 9.14 min / da 5.80 max (F3 ADOPTED 17:55:55Z); allowables IN718 Fty / Ftu at the screw temperature, no bearing credit",
                                     "spring_side": "1.4568 (17-7 PH) condition and allowable: TO-SOURCE from the maker"}
        # (4) FEA3D's TC-01 ligament-station P+Q (cell, js5 station delta 5.688 side +): js5-history scaling; INFORMATION (contact-edge field)
        if st != "FA1S":
            lg = c["TC-01"]["SCL_PQ_ligament_station_max_cad"]
            Tl = R.HISTS[st]["js5"]["seat_line_T_C"]
            two_fy = 2.0 * tab("AL6061-T6", "Fty", Tl)
            pq = lg["PmPb"] * n_in(st, "js5", FV) / Nfe_js5
            pqb = lg["PmPb"] * Nenv / Nfe_js5
            r["TC01_ligament_station_PQ_FEA3D_cell_INFO"] = {
                "PmPb_A4-80_MPa": lg["PmPb"], "PmPb_IN718_js5_history_MPa": round(pq, 1), "two_Fty_MPa": round(two_fy, 1), "MS_PQ_2Fty_info": ms(two_fy, pq),
                "envelope_scaled_bound_info": {"PmPb_MPa": round(pqb, 1), "MS": ms(two_fy, pqb), "N_from": LBL[henv]}, "INFO_js5_history_A4-80_withdrawn_MS": lg["MS_PQ_2Fty"],
                "class": ("INFORMATION: contact-edge field (station 0.08 mm from the hole wall, inside the near-edge gradient: 572 / 346 / ~262 MPa at "
                          "0.08 / 0.26 / 0.52 mm at js5 SOAK70), like the hole-edge line class of 239 (9); only js5 reports this station, so the "
                          "row scales with the js5 history's own force; not a cell")}
        # (5) seat line d+6.051 z'0 and ring line: P+Q vs 2 Fty(T), per history; (i) F_sh-consistent, (ii) head-force bound
        if st in R.SOAKS + ("PRELOAD",):
            for fam, key in (("seat_line_d6p051_z0", "seat_line_PmPb_MPa"), ("ring_line", None)):
                per = {}
                for h in R.H_at(st):
                    x = R.HISTS[st][h]
                    if key:
                        pq0, T = x[key], x["seat_line_T_C"]
                    elif h in R.B2:                       # v6 / relax v7: (b2)'s contact ring sits on d+6.051 z'0: its ring family IS the seat line
                        pq0, T = x["ring_family_PmPb_MPa"], x["seat_line_T_C"]
                    else:
                        cand = [(x["ring_line_d8p02_PmPb_MPa"], cmp_side(h, st)["lines"]["ring"]["T_mean_C"])]
                        if h == "js5" and x.get("ring_line_d8p126_PmPb_MPa") is not None:
                            g = R._rel["steps"][st if st != "PRELOAD" else "SOAK70"]["families"]["ring"]["governing_by_soak_PQ"]
                            cand.append((x["ring_line_d8p126_PmPb_MPa"], g["T_soak_mean_C"] if st != "PRELOAD" else 20.0))
                        pq0, T = max(cand)
                    if st == "PRELOAD":
                        T = 20.0
                    two_fy = 2.0 * tab("AL6061-T6", "Fty", T)
                    fr = FSH_RATIO.get(st, 1.0) if st != "PRELOAD" else 1.0
                    if FV == FVMAX:
                        # +346 N installation: the shell pull rises by dF_sh / dF_V of the model at that state (hi end; the lo end is within 0.1 %)
                        kb = R.KB["hi"]
                        a_ = R.model_state(st, kb, IN, FV=FV0) if st != "PRELOAD" else R.state_s(FV0, R.G0, 0, 0, 0, 0, R.K_SH_JS5, kb * IN.kb_ratio)
                        b_ = R.model_state(st, kb, IN, FV=FVMAX) if st != "PRELOAD" else R.state_s(FVMAX, R.G0, 0, 0, 0, 0, R.K_SH_JS5, kb * IN.kb_ratio)
                        fr = fr * b_[3] / a_[3]
                    pq_i = pq0 * fr
                    pq_ii = pq0 * n_in(st, h, FV) / x["N_head_N"]
                    per[LBL[h]] = {"PmPb_A4-80_MPa": pq0, "T_C": T, "two_Fty_MPa": round(two_fy, 1), "PmPb_IN718_Fsh_MPa": round(pq_i, 1), "MS_PQ_Fsh": ms(two_fy, pq_i),
                                   "PmPb_IN718_headforce_bound_MPa": round(pq_ii, 1), "MS_PQ_headforce_bound": ms(two_fy, pq_ii)}
                hw = min(per, key=lambda k: per[k]["MS_PQ_Fsh"])
                hb = min(per, key=lambda k: per[k]["MS_PQ_headforce_bound"])
                r[fam + "_PQ"] = {"per_history": per, "MS_PQ_2Fty": per[hw]["MS_PQ_Fsh"], "from": hw,
                                  "bound_MS": per[hb]["MS_PQ_headforce_bound"], "bound_from": hb}
        # (6) number of TC-01 lines with Pm > Fty(T) (54 seat + 10 hole-edge lines), per history, head-force scaling (bound) and F_sh scaling
        if st in R.SOAKS:
            cnt = {}
            for h in R.H_at(st):
                Nh = R.HISTS[st][h]["N_head_N"]
                k_n = n_in(st, h, FV) / Nh
                k_s = FSH_RATIO[st]
                lines, pmk = cmp_lines(h, st)
                fam_counts = {}
                for fam in ("seat", "hole_edge"):
                    ls = [q for q in lines if q["family"] == fam]
                    fy = lambda q: tab("AL6061-T6", "Fty", q["T_mean_C"])
                    fam_counts[fam] = {"A4-80": sum(1 for q in ls if q[pmk] > fy(q)), "IN718_Fsh": sum(1 for q in ls if q[pmk] * k_s > fy(q)),
                                       "IN718_headforce_bound": sum(1 for q in ls if q[pmk] * k_n > fy(q)),
                                       "max_Pm_over_Fty_bound": round(max(q[pmk] * k_n / fy(q) for q in ls), 3), "n_lines": len(ls)}
                cnt[LBL[h]] = fam_counts
            r["TC01_lines_Pm_gt_Fty"] = {"per_history": cnt,
                                         "envelope": {fam: {k: max(cnt[LBL[h]][fam][k] for h in R.H_at(st)) for k in ("A4-80", "IN718_Fsh", "IN718_headforce_bound", "max_Pm_over_Fty_bound")}
                                                      for fam in ("seat", "hole_edge")},
                                         "js5_relax_json_count_A4-80": {fam: R._rel["steps"][st]["families"][fam]["n_lines_soak_Pm_gt_Fty"] for fam in ("seat", "hole_edge")}}
        # (7) screw fibre at the soak (secondary bending, ruling 10:08:57Z): fibre yield = screw plastic set; shakedown vs 2 Fty_IN718(T)
        if st in R.SOAKS:
            fib = {}
            pre = R.HISTS["PRELOAD"]
            # cold end of the range: the LOWEST PRELOAD section force and moment over the histories (conservative for the range)
            Nsec_pre = min(pre[h]["N_section_max_N"] for h in R.H_at("PRELOAD")) * FV / FV0
            M_pre = R.M_PRE_MIN * IN.tilt_ratio * FV / FV0
            f_pre = Nsec_pre / A_S + M_pre / Z_3
            for h in R.H_at(st):
                x = R.HISTS[st][h]
                Ni = n_in(st, h, FV)
                Nsec = x["N_section_max_N"] * Ni / x["N_head_N"]
                Fc_in = x["seat_radial_N"] + (Ni - x["N_head_N"]) * R.K_C / (R.K_C + R.K_SH_JS5)
                M_in = x["M_max_Nmm"] * IN.tilt_ratio * max(1.0, Fc_in / x["seat_radial_N"])
                f = Nsec / A_S + M_in / Z_3
                rp = tab("IN718", "Fty", Ts)
                rngf = f - f_pre
                # plastic set estimate: elastic section N/A + M y / I over the circular d3 section; the yielded segment's excess integrated
                # (section-averaged), as an equivalent uniform axial set over the free length L_FREE (upper estimate of the preload loss)
                d3 = (32.0 * Z_3 / math.pi) ** (1.0 / 3.0)
                cc = d3 / 2.0
                sN, sM = Nsec / A_S, M_in / Z_3
                exc, ny = 0.0, 400
                for i in range(ny):
                    y = -cc + (i + 0.5) * 2 * cc / ny
                    wdt = 2.0 * math.sqrt(max(cc * cc - y * y, 0.0))
                    s_ = sN + sM * y / cc
                    exc += max(0.0, s_ - rp) * wdt * (2 * cc / ny)
                dp_um = exc / (R.tab("IN718", "E", Ts) * 1e-6 * 1e6) * R.RV3.L_FREE / (math.pi * cc * cc) * 1e3 if exc > 0 else 0.0
                fib[LBL[h]] = {"N_section_N": round(Nsec, 1), "M_Nmm": round(M_in, 1), "fibre_MPa": round(f, 1), "Fty_IN718_MPa": round(rp, 1), "MS_y_fibre": ms(rp, f),
                               "fibre_cold_MPa": round(f_pre, 1), "range_MPa": round(rngf, 1), "two_Fty_MPa": round(2 * rp, 1), "MS_shakedown": ms(2 * rp, rngf),
                               "section_excess_N": round(exc, 1), "equiv_axial_set_um": round(dp_um, 3)}
            hw = min(fib, key=lambda k: fib[k]["MS_y_fibre"])
            r["screw_fibre_soak"] = {"per_history": fib, "MS_y_fibre": fib[hw]["MS_y_fibre"], "MS_shakedown": min(v["MS_shakedown"] for v in fib.values()),
                                     "range_max_MPa": max(v["range_MPa"] for v in fib.values()), "max_equiv_axial_set_um": max(v["equiv_axial_set_um"] for v in fib.values()),
                                     "from": hw}
        rows[tag] = r
    out["rows"] = rows
    return out


# ---- TC-02 A_n thread shear: the full row, the engagement basis and the cheapest fixes (lead 12:09Z item 5; no hardware change before the ruling)
ENG = seat1["tc02_engagement"]
R_FLAT_CAD = ENG["r_flat_mm"]                      # 31.3129: the d10.5 flat on R31.75
R_PLUG_CAD, R_PLUG_DWG = 28.6, (57.140 / 2.0, 57.170 / 2.0)
D_SPOT_TOL = 0.2                                   # spot-face diameter, ISO 2768-m general tolerance for 6-30 mm (ASSUMED until the drawing states one)
R_OD = 63.5 / 2.0


def r_flat(d_spot):
    return math.sqrt(R_OD ** 2 - (d_spot / 2.0) ** 2)


R_FLAT_RANGE = (r_flat(10.5 + D_SPOT_TOL), r_flat(10.5 - D_SPOT_TOL))     # deeper flat (larger spot face) .. shallower flat
FULL_THREAD = 8.0                                  # TC-02 M5-6H full-thread depth from the TC-02 OD (CAD jfwd_tap_drill_mm 9.0 / full thread 8.0)
MOUTH = 0.5                                        # first 0.5 mm of the tap mouth not credited (jfwd_preload basis)
TIP_CLEAR_MIN = 0.2                                # screw tip at least 0.2 mm short of the full-thread end at the worst stack (no run into the runout)
ISO_L_TOL = 0.29                                   # ISO 4759-1 grade A length tolerance js15 at l = 10 (AS RECALLED, TO-VERIFY) - standard ISO 7380-1 part
assert abs(r_flat(10.5) - R_FLAT_CAD) < 2e-4
# v6 correction (lead 16:07Z (2); 13:14Z (2), 14:03Z (2)): THE ROW engagement basis = the drawn M5 x 10.2 +/-0.1 on the rev-5 flat
RF5 = (31.313, 31.333)                                                # r_flat 31.313 +0.020/0 from the bore axis (rev 5, ADOPTED 14:03Z)
GAP_MIN, GAP_MAX = R.GAPS["H8f7_min"], R.GAPS["H8f7_max"]             # buildable radial gaps 0.040 / 0.078 (239 (3))
R_BORE5 = (R_PLUG_DWG[1] + GAP_MIN, R_PLUG_DWG[0] + GAP_MAX)          # TC-01 bore radius 28.625 / 28.648
WALL5 = (RF5[0] - R_BORE5[1], RF5[1] - R_BORE5[0])                    # TC-01 wall at the hole 2.665 / 2.708 (flat to bore)


def eng_rev5(L_nom, tol, t_under=(0.0, 0.0)):
    """rev-5 engagement: shortest screw, thickest wall (r_flat max, bore min); TC-01 wall seated on the plug at the hole (local gap 0) and
    the 0.078 radial gap bound (THE ROW); tip clearance to the 8.0 full-thread end with the wall seated, thinnest wall, longest screw
    (the plug size drops out); t_under = (min, max) height of a part under the head."""
    Le0 = (L_nom - tol) - (WALL5[1] + t_under[1])
    LeG = Le0 - GAP_MAX
    clr = WALL5[0] + t_under[0] + FULL_THREAD - (L_nom + tol)
    return {"L_nom_mm": L_nom, "L_tol_mm": tol, "wall_at_hole_mm": [round(x, 4) for x in WALL5], "L_e_gap0_mm": round(Le0, 3),
            "L_e_gap_bound_mm": round(LeG, 3), "A_n_gap0_mm2": round(strip_area(TH, Le0 - MOUTH), 2),
            "A_n_gap_bound_mm2": round(strip_area(TH, LeG - MOUTH), 2), "tip_clearance_to_full_thread_end_min_mm": round(clr, 3),
            "tip_ok": clr >= TIP_CLEAR_MIN - 1e-9}


THE_ROW_NS = eng_rev5(10.2, 0.1)                                      # v7: the no-spring row (RULED 12:52Z), kept as the record
assert abs(THE_ROW_NS["L_e_gap_bound_mm"] - 7.314) < 0.0015 and abs(THE_ROW_NS["A_n_gap_bound_mm2"] - 68.13) < 0.01, THE_ROW_NS
T_SPRING_A, T_SPRING_B = (0.44, 0.52), (0.34, 0.42)                    # DIN EN 16983 t 0.20-0.60 +0.02 / -0.06 (Schnorr brochure 2024-02 p. 10)
THE_ROW = eng_rev5(10.7, 0.1, T_SPRING_A)                              # v7 route (i): spring A under the head (lead 16:53Z R2)
THE_ROW_B = eng_rev5(10.6, 0.1, T_SPRING_B)                            # alternate spring B (t 0.4) on M5 x 10.6 +/-0.1
A_THE_ROW = THE_ROW["A_n_gap_bound_mm2"]
assert abs(THE_ROW["L_e_gap_bound_mm"] - 7.294) < 0.0015 and abs(A_THE_ROW - 67.93) < 0.01, THE_ROW
assert THE_ROW_B["A_n_gap_bound_mm2"] == A_THE_ROW and THE_ROW["tip_ok"] and THE_ROW_B["tip_ok"], (THE_ROW, THE_ROW_B)
THE_ROW_LABEL = ("THE ROW (route (i), lead 16:53Z R2): ENG-HW-101-IN718 M5 x 10.7 +/-0.1 with the disc spring solid under the head (t 0.44-0.52) "
                 "on the rev-5 flat (r_flat 31.313 +0.020/0 from A), TC-01 wall seated, 0.078 radial gap bound: L_e min 7.294, A_n 67.93 mm2 "
                 "(local gap 0: L_e 7.372, information); spring B on M5 x 10.6 +/-0.1 gives the same L_e; the no-spring M5 x 10.2 row (L_e 7.314, "
                 "A_n 68.13, RULED 12:52Z) is the record")


def eng_case(L_nom, tol, h_under=0.0):
    """min engagement (shortest screw, shallowest flat, smallest plug) and tip clearance to the full-thread end (longest screw, deepest flat,
    largest plug incl. the CAD nominal); h_under = a part under the head (min height for the tip, max height for the engagement)."""
    hu = (h_under, h_under) if not isinstance(h_under, tuple) else h_under
    Le_min = (L_nom - tol) - (R_FLAT_RANGE[1] + hu[1] - R_PLUG_DWG[0])
    clr = (R_FLAT_RANGE[0] + hu[0] - (L_nom + tol)) - (max(R_PLUG_CAD, R_PLUG_DWG[1]) - FULL_THREAD)
    Leff = Le_min - MOUTH
    return {"L_nom_mm": L_nom, "L_tol_mm": tol, "L_e_min_mm": round(Le_min, 3), "L_eff_min_mm": round(Leff, 3), "A_n_mm2": round(strip_area(TH, Leff), 2),
            "tip_clearance_to_full_thread_end_min_mm": round(clr, 3), "tip_ok": clr >= TIP_CLEAR_MIN - 1e-9}


def thread_full_row(states):
    out = {"basis": ("tau = N_IN718 (envelope history, per state) / A_n; Fsy = 0.577 Fty(T), Fsu = 0.6 Ftu(T) at FEA3D's TC-02 thread temperature; "
                     "A_n = jfwd_v352 strip area (M5-6H / 6g: Ds_min 4.826, En_max 4.605, P 0.8) x L_eff"),
           "A_n_bases": {}, "rows": {}, "fixes": {}}
    th0 = CELLS["SOAK"]["TC-02"]["thread_shear_An"]
    An_fea = R.HISTS["SOAK"]["js5"]["N_head_N"] / th0["tau_MPa"]
    e_dwg = eng_case(10.0, 0.0)
    e_iso = eng_case(10.0, ISO_L_TOL)
    bases = {"THE_ROW": {"label": THE_ROW_LABEL, **THE_ROW},
             "route_i_spring_B_alternate (M5 x 10.6 +/-0.1, t 0.34-0.42)": THE_ROW_B,
             "RECORD_no_spring_M5x10.2 (RULED 12:52Z, THE ROW until route (i))": THE_ROW_NS,
             "SUPERSEDED_RECORD (13:14Z (2), 14:03Z (2))": {
                 "FEA3D_cell_A_n_mm2 (L_eff 6.35 = v3.5.1 L_e 6.85 - 0.5)": round(An_fea, 2),
                 "check_strip_area_at_6.35_mm2": round(strip_area(TH, 6.35), 2),
                 "v3.5.2 drawing engagement, L 10.0 nominal (d10.5 +/-0.2 spot face on the nominal OD)": e_dwg,
                 "v3.5.2 drawing engagement, L 10.0, ISO 4759-1 length tolerance -0.29 (AS RECALLED)": e_iso}}
    out["A_n_bases"] = bases
    out["engagement_geometry"] = {"r_flat_CAD_mm": R_FLAT_CAD, "r_flat_range_spot_d10.5+/-0.2_mm": [round(x, 4) for x in R_FLAT_RANGE],
                                  "r_plug_CAD_mm": R_PLUG_CAD, "r_plug_drawing_f7_mm": [round(x, 4) for x in R_PLUG_DWG], "full_thread_mm": FULL_THREAD,
                                  "mouth_not_credited_mm": MOUTH, "tip_clearance_min_mm": TIP_CLEAR_MIN,
                                  "src": f"jfwd_seat_v352_v1.json {sha(SEAT1)} tc02_engagement (L_e CAD 7.287, drawing 7.257-7.272); CAD config jfwd_tap_drill_mm 9.0"}
    for st in states:
        th = CELLS[st]["TC-02"]["thread_shear_An"]
        T2 = th["T_C"]
        fsy, fsu = 0.577 * tab("AL6061-T6", "Fty", T2), 0.6 * tab("AL6061-T6", "Ftu", T2)
        henv = max(R.H_at(st), key=lambda h: n_in(st, h))
        rr = {}
        for FV in (FV0, FVMAX):
            N = n_in(st, henv, FV)
            row = {"N_N": round(N, 1), "from": LBL[henv], "T_C": T2, "Fsy_MPa": round(fsy, 1), "Fsu_MPa": round(fsu, 1)}
            for nm, An in (("THE_ROW", A_THE_ROW), ("info_local_gap_0", THE_ROW["A_n_gap0_mm2"]),
                           ("SUPERSEDED_FEA3D_A_n_63.48", An_fea), ("SUPERSEDED_drawing_L10.0_nominal", e_dwg["A_n_mm2"]),
                           ("SUPERSEDED_drawing_L10.0_ISO_tol", e_iso["A_n_mm2"])):
                row[nm] = {"A_n_mm2": round(An, 2), "tau_MPa": round(N / An, 1), "MS_y": ms(fsy, N / An), "MS_u": ms(fsu, N / An)}
            row["flag"] = flag(row["THE_ROW"]["MS_y"])
            rr[f"{FV:.0f}"] = row
        out["rows"][st] = rr
    gov = min(states, key=lambda st: out["rows"][st]["4096"]["THE_ROW"]["MS_y"])
    out["governing_state"] = gov
    th = CELLS[gov]["TC-02"]["thread_shear_An"]
    fsy = 0.577 * tab("AL6061-T6", "Fty", th["T_C"])
    henv = max(R.H_at(gov), key=lambda h: n_in(gov, h))
    slope = D_FVMAX / (FVMAX - FV0)
    N3750 = n_in(gov, henv, FV0)
    fv_for = lambda target: FV0 + (fsy * A_THE_ROW / (1.0 + target) - N3750) / slope
    # (a) lower J-F1 acceptance maximum (re-derived on THE ROW, lead 16:07Z (2))
    fa0, fa5 = fv_for(0.0), fv_for(0.05)
    out["fixes"]["a_lower_J-F1_max"] = {"F_max_for_MS_y_0_N": round(fa0), "F_max_for_MS_y_0.05_N": round(fa5),
                                        "governing_state": gov, "N_from": LBL[henv], "A_n_mm2": A_THE_ROW,
                                        "note": (f"on THE ROW (route (i), A_n {A_THE_ROW} mm2); the J-F1 MAXIMUM IS CAPPED AT 3750 N (lead 17:55:55Z F1: torque "
                                                 f"= 3750 x K_min x d on the flight lot; today's K window {JF1_K_WIN[0]}-{JF1_K_WIN[1]} -> "
                                                 f"{JF1_T_NMM / 1e3:.3f} N m, band {JF1_MIN:.0f}-3750 N): "
                                                 + ("MS_y >= 0 holds at the 3750 N cap" if fa0 >= FV0 else f"MS_y >= 0 needs a maximum of {fa0:.0f} N")
                                                 + f" (MS_y 0 at {fa0:.0f} N); "
                                                 + ("MS_y >= 0.05 holds at 3750 N" if fa5 >= FV0 else f"MS_y >= 0.05 would need {fa5:.0f} N: the 3750 N row is a FLAG")
                                                 + "; the 4096 N column is information (superseded maximum)"),
                                        "J_F1_cap_N": FV0, "J_F1_min_N": round(JF1_MIN, 1), "J_F1_torque_Nm_today_K_window": round(JF1_T_NMM / 1e3, 3),
                                        "slack_effect": SLACK_TXT,
                                        "other_effects": "none on CAD or FD-04; J-F1 acceptance rule only"}
    # (b) custom IN718 length within the 8.0 full thread (the IN718 screw is a custom part: TO-SELECT / TO-QUOTE; its length is a drawing number)
    opts = {}
    for L_nom, tol, tu in ((10.2, 0.1, (0.0, 0.0)), (10.7, 0.1, T_SPRING_A), (10.6, 0.1, T_SPRING_B)):
        e = eng_rev5(L_nom, tol, tu)
        e["t_under_mm"] = list(tu)
        rws = {}
        for FV in (FV0, FVMAX):
            N = n_in(gov, henv, FV)
            rws[f"{FV:.0f}"] = {"tau_MPa": round(N / e["A_n_gap_bound_mm2"], 1), "MS_y": ms(fsy, N / e["A_n_gap_bound_mm2"])}
        e["rows_at_governing_state"] = rws
        e["status"] = ("record: no spring (RULED 12:52Z)" if L_nom == 10.2 else
                       ("THE ROW: route (i) spring A (lead 16:53Z R2)" if L_nom == 10.7 else "route (i) alternate: spring B"))
        opts[f"M5 x {L_nom} +/-{tol}" + (f" over t {tu[0]}-{tu[1]}" if tu[1] > 0 else "")] = e
    out["fixes"]["b_custom_IN718_length"] = {"options": opts,
                                             "slack_effect": ("none: the free length (grip + 0.5 mouth) is unchanged; in the VDI-form resilience of jfwd_embed the "
                                                              "engaged thread is 0.5 d / A_d3 and the tapped part 0.33 d, independent of L_e, so k_b and the 24-case "
                                                              "do not move"),
                                             "other_effects": ("no CAD change (tap 4.2 x 9.0 / full thread 8.0 kept), no head-height or FD-04 change; J-F1 calibrates "
                                                               "K at the flight length; drawing length tolerance +/-0.08..0.1 instead of ISO js15"),
                                             "note": ("rev-5 basis (r_flat 31.313 +0.020/0 from A, wall seated, 0.078 gap bound for L_e, wall min "
                                                      "seated for the tip); route (i) (lead 16:53Z R2): 10.7 +/-0.1 over spring A is THE ROW, 10.6 "
                                                      "+/-0.1 over spring B the alternate; 10.2 +/-0.1 (RULED 12:52Z) is the no-spring record")}
    # (c) insert: tap-wall effect (catalogue tap drill; the STI major diameter is TO-SOURCE)
    out["fixes"]["c_helical_insert"] = {"status": "REJECTED by the lead 12:52Z (record only)",
                                        "part": "Boellhoff HELICOIL plus M5 x 0.8, 1d / 1.5d (order no. 4189 005 0005 / 4189 005 0075)",
                                        "source": ("RS 471-017 (mfr part 41890050005): 'Drill Size 5.2mm', 'Thread Length 5mm' (https://uk.rs-online.com/web/p/"
                                                   "thread-repair-inserts/0471017, accessed 2026-10-20); HELICOIL plus datasheet 0180/10.02 "
                                                   "(https://docs.rs-online.com/5ddb/0900766b810150a0.pdf, accessed 2026-10-20) lists M 5 x 5 / 7.5 / 10; its "
                                                   "STI tap table (pp. 36/37) is not in that file: the STI major diameter is TO-SOURCE"),
                                        "tap_wall_effect": ("torch-passage tap wall 1.906 mm at az 18 / 342 (measured from the M5 major 5.0): the tap drill grows "
                                                            "4.2 -> 5.2 (-0.50 mm on the drilled wall) and the tapped major grows from 5.0 to the STI major (each 0.1 "
                                                            "mm of diameter thins the 1.906 wall by 0.05 mm; at an STI major near 6.0 the wall is about 1.41 mm, the "
                                                            "M6-fallback value): probe + FE re-run needed"),
                                        "slack_effect": "a coil insert adds thread compliance (k_b down, slightly favourable); not quantified without data",
                                        "other_effects": "CAD + TC-02 drawing change, insert installation / tang removal on flight hardware, new J-F1 pair (IN718 / insert)"}
    out["fixes"]["d_disc_spring_interaction"] = ("route (i) ADOPTED (lead 16:53Z R2, CAD check passed 17:49Z): the spring is solid (flat) at every hot "
                                                 "frame (spring v3), so the soak force is the FE-mapped one (the 0.5 mm longer IN718 screw lowers k_b "
                                                 "slightly: favourable, not credited); the row moves only through L_e (THE ROW above)")
    return out


HC2 = Path("/home/claude/work/shared-fallback/engine/03-cad/calcs/hand_calcs_v2.json")


def membrane_h9(d_ro=-0.037, d_ri_seal=0.023):
    """re-evaluate hand_calcs_v2 case rows (Lame at the bore + forward closure end load, von Mises) with the OD radius changed by d_ro;
    the published applied value is reproduced first (assert)"""
    hc = json.loads(HC2.read_text())
    inp = hc["inputs"]
    OD, t = inp["case_OD"]["v"] * 1e3, inp["case_t"]["v"] * 1e3
    bore_seal = inp["case_bore_seal"]["v"] * 1e3
    ri0 = (OD - 2 * t) / 2
    secs = {"full wall 63.50/57.15": (OD / 2, ri0), "fwd seal land 57.25 bore": (OD / 2, bore_seal / 2),
            "collar groove 62.50 (pivot plane)": (OD / 2 - 0.5, ri0)}          # collar_groove_depth 0.0005 m (hand_calcs.py put(), DERIVED: OD groove)

    def vm(P, ro, ri):
        k = (ro ** 2 + ri ** 2) / (ro ** 2 - ri ** 2)
        sh, sr = P * k, -P
        sa = P * math.pi / 4 * bore_seal ** 2 / (math.pi * (ro ** 2 - ri ** 2))
        return math.sqrt(((sh - sa) ** 2 + (sa - sr) ** 2 + (sr - sh) ** 2) / 2), sh, sa

    out = {"source": {"path": str(HC2), "sha256_16": sha(HC2)}, "basis_answer": ("NOMINAL: hand_calcs_v2 uses case_OD 63.5 and the nominal bore "
           f"(full wall {OD / 2 - ri0:.3f}, fwd seal land {OD / 2 - bore_seal / 2:.3f}, collar groove {secs['collar groove 62.50 (pivot plane)'][0] - ri0:.3f} mm), "
           "not the minimum wall"), "d_ro_mm": d_ro, "d_ri_fwd_seal_land_mm": d_ri_seal, "rows": []}
    for r in hc["sections"]["case"]["rows"]:
        nm = next((n for n in secs if n in r["check"]), None)
        if nm is None:
            continue
        P = float(r["check"].split("[")[1].split()[1]) / 10.0          # bar -> MPa
        ro, ri = secs[nm]
        v0 = vm(P, ro, ri)[0]
        assert abs(v0 - r["applied"]) < 0.05, (r["check"], v0, r["applied"])
        sfy, sfu = r.get("SF_y"), r.get("SF_u")
        ay = (1 + r["MS_y"]) * sfy * r["applied"]
        au = (1 + r["MS_u"]) * sfu * r["applied"] if r.get("MS_u") is not None and sfu else None
        cases = {"h9": (ro + d_ro, ri)}
        if "fwd seal land" in nm:
            cases["h9_and_H8_max_bore"] = (ro + d_ro, ri + d_ri_seal)
        rec = {"row": r["check"], "applied_nominal_MPa": round(r["applied"], 2), "MS_y_nominal": round(r["MS_y"], 3),
               "MS_u_nominal": round(r["MS_u"], 3) if au else None, "SF": [sfy, sfu]}
        for cn, (ro2, ri2) in cases.items():
            v1 = vm(P, ro2, ri2)[0]
            rec[cn] = {"wall_mm": round(ro2 - ri2, 3), "applied_MPa": round(v1, 2), "MS_y": round(ay / (sfy * v1) - 1, 3),
                       "MS_u": round(au / (sfu * v1) - 1, 3) if au else None}
        out["rows"].append(rec)
    def key(x):
        return min(v for v in (x["MS_y_nominal"], x["MS_u_nominal"]) if v is not None)
    out["closest_row_on_the_63.5_OD"] = min(out["rows"], key=key)["row"]
    out["note"] = ("the aft seal land (61.0) and the aft thread root (M63 x 1.5) rows are on separate diameters, not the 63.5 OD; the collar "
                   "groove is evaluated as cut to a depth from the OD (if it is dimensioned as a diameter, h9 does not move it)")
    return out

TF1_EXPO = Path("/home/claude/work/mechanical/v352/texts/tf1_exposure_v352_v1.json")
HIST_MERGED = Path("/home/claude/work/mechanical/v352/tb70/hist/DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_hist.npz")
BORE_TOL_PROPOSED = 0.10                            # rev 5: 'bore 57.15 +/-0.10' (no drawn tolerance today)


def membrane_minwall():
    """v5 (b): hand_calcs_v2 case rows re-evaluated on the minimum wall (each diameter on its own drawn or rev-5 tolerance); the nominal row and
    its T_allow are reproduced first (asserts)."""
    import sys as _s
    _s.path.insert(0, "/home/claude/work/mechanical/v352/engine/04-fea/src")
    import engmat as _em
    import numpy as _np
    hc = json.loads(HC2.read_text())
    inp = hc["inputs"]
    OD, t = inp["case_OD"]["v"] * 1e3, inp["case_t"]["v"] * 1e3
    d_seal = inp["case_bore_seal"]["v"] * 1e3
    d_aft = 61.0                                                     # hand_calcs case_aft_land_d (aft closure end load, its bound)
    bore0 = OD - 2 * t
    od_min, bore_max, seal_max = 63.5 - 0.074, bore0 + BORE_TOL_PROPOSED, 57.25 + 0.046
    groove_min, aft_min = 62.50 - 0.074, 61.0 - 0.060
    P_th = 1.5
    es_e, td2 = -(50.0 + 11.0 * P_th) / 1000.0, 90.0 * P_th ** 0.4 * math.sqrt(45.0 * 90.0) ** 0.1 / 1000.0
    d3_nom = 63.0 - 1.22687 * P_th
    d3_min = d3_nom + es_e - td2
    secs = {"full wall 63.50/57.15": ((OD / 2, bore0 / 2, d_seal), (od_min / 2, bore_max / 2, seal_max),
                                      "OD 63.5 h9 min 63.426; bore 57.15 +/-0.10 (rev 5, NEW) max 57.25; fwd end load on 57.296"),
            "fwd seal land 57.25 bore": ((OD / 2, d_seal / 2, d_seal), (od_min / 2, seal_max / 2, seal_max),
                                         "OD 63.426; bore 57.25 H8 max 57.296; fwd end load on 57.296"),
            "collar groove 62.50 (pivot plane)": ((OD / 2 - 0.5, bore0 / 2, d_seal), (groove_min / 2, bore_max / 2, seal_max),
                                                  "groove 62.50 h9 min 62.426 (a diameter on the drawing); bore max 57.25; fwd end load 57.296"),
            "aft seal land 61.0 (above the gland)": ((d_aft / 2, bore0 / 2, d_aft), (aft_min / 2, bore_max / 2, d_aft),
                                                     "land 61.0 f7 min 60.940; bore max 57.25; aft end load on d 61.0 (hand calc bound, unchanged)"),
            "aft thread root M63x1.5 d3 61.16": ((d3_nom / 2, bore0 / 2, d_aft), (d3_min / 2, bore_max / 2, d_aft),
                                                 f"d3 min {d3_min:.3f} (6e: es {es_e * 1000:.1f} um, Td2(6) {td2 * 1000:.1f} um, AS RECALLED / TO-VERIFY); "
                                                 "bore max 57.25; aft end load on d 61.0")}

    def vm(P, ro, ri, d_end):
        k = (ro ** 2 + ri ** 2) / (ro ** 2 - ri ** 2)
        sh, sr = P * k, -P
        sa = P * math.pi / 4 * d_end ** 2 / (math.pi * (ro ** 2 - ri ** 2))
        return math.sqrt(((sh - sa) ** 2 + (sa - sr) ** 2 + (sr - sh) ** 2) / 2), sh, sa

    def t_allow(s, sfy, sfu):
        ok = None
        for T in _np.arange(20.0, 350.01, 0.5):
            y = _em.prop("AL6061-T6", "Fty", T) / 1e6 >= sfy * s if sfy else True
            u = _em.prop("AL6061-T6", "Ftu", T) / 1e6 >= sfu * s if sfu else True
            if y and u:
                ok = float(T)
            else:
                break
        return ok

    expo = json.loads(TF1_EXPO.read_text())
    zm = _np.load(HIST_MERGED, allow_pickle=True)
    infm = json.loads(str(zm["info"]))
    tm = zm["t_s"].astype(float)
    pm = zm["part_max"][list(zm["parts"]).index("ENG-TC-01"), :] - 273.15
    burn_m = float(pm[tm <= infm["segments_s"][0][1] + 1e-6].max())
    burn = {"rev4_GVLO_C": expo["bounds"]["GVLO"]["parts"]["ENG-TC-01"]["burn_max_C"], "rev4_GVHI_C": expo["bounds"]["GVHI"]["parts"]["ENG-TC-01"]["burn_max_C"],
            "rev3_merged_perfect_contact_C_info": round(burn_m, 1)}
    t_burn = max(burn.values())
    out = {"source": {"path": str(HC2), "sha256_16": sha(HC2)}, "tf1_exposure": {"path": str(TF1_EXPO), "sha256_16": sha(TF1_EXPO)},
           "merged_hist": {"path": str(HIST_MERGED), "sha256_16": sha(HIST_MERGED)},
           "minimum_wall_geometry": {k: {"nominal_ro_ri_mm": [round(v[0][0], 4), round(v[0][1], 4)], "min_wall_ro_ri_mm": [round(v[1][0], 4), round(v[1][1], 4)],
                                         "wall_nominal_mm": round(v[0][0] - v[0][1], 4), "wall_min_mm": round(v[1][0] - v[1][1], 4), "end_load_d_mm": v[1][2], "basis": v[2]}
                                     for k, v in secs.items()},
           "TC01_burn_max_C (pressurised)": burn, "rows": []}
    for r in hc["sections"]["case"]["rows"]:
        nm = next((n for n in secs if n in r["check"]), None)
        if nm is None:
            continue
        P = float(r["check"].split("[")[1].split()[1]) / 10.0
        (ro0, ri0, de0), (ro1, ri1, de1), _ = secs[nm]
        v0 = vm(P, ro0, ri0, de0)[0]
        assert abs(v0 - r["applied"]) < 0.05, (r["check"], v0, r["applied"])
        sfy, sfu = r.get("SF_y"), r.get("SF_u")
        Ta0 = t_allow(v0, sfy, sfu)
        assert Ta0 is not None and abs(Ta0 - r["T_allow_C"]) <= 0.5, (r["check"], Ta0, r["T_allow_C"])
        v1, sh1, sa1 = vm(P, ro1, ri1, de1)
        fy20, fu20 = _em.prop("AL6061-T6", "Fty", 20.0) / 1e6, _em.prop("AL6061-T6", "Ftu", 20.0) / 1e6
        Ta1 = t_allow(v1, sfy, sfu)
        rec = {"row": r["check"], "SF": [sfy, sfu], "nominal": {"applied_MPa": round(v0, 2), "MS_y": round(r["MS_y"], 3),
                                                                 "MS_u": round(r["MS_u"], 3) if r.get("MS_u") is not None else None, "T_allow_C": r["T_allow_C"]},
               "min_wall": {"wall_mm": round(ro1 - ri1, 4), "applied_MPa": round(v1, 2), "hoop_MPa": round(sh1, 1), "axial_MPa": round(sa1, 1),
                            "MS_y": round(fy20 / (sfy * v1) - 1, 3), "MS_u": round(fu20 / (sfu * v1) - 1, 3) if sfu else None, "T_allow_C": Ta1},
               "pressurised_TC01_max_C": (20.0 if "LC4" in r["check"] else t_burn),
               "T_margin_K": round(Ta1 - (20.0 if "LC4" in r["check"] else t_burn), 1)}
        out["rows"].append(rec)
    ms_all = [(x["min_wall"]["MS_u"] if x["min_wall"]["MS_u"] is not None else x["min_wall"]["MS_y"], x["row"]) for x in out["rows"]]
    out["governing_min_wall_row"] = min(ms_all)[1]
    out["lowest_T_allow_min_wall"] = min((x["min_wall"]["T_allow_C"], x["row"]) for x in out["rows"])
    out["rev5_drawing_items"] = [
        "TC-01 bore 57.15 +/-0.10 (ADOPTED 16:53Z R4; maximum 57.25 = the 57.25 H8 seal-land clean-up bound; minimum wall 3.088 at the h9 OD)",
        "TC-01 aft thread M63 x 1.5-6e in the fits list and in the notes (16:53Z R4; 6e is the basis of these rows)",
        "datum frame as built in rev 5 (16:53Z R4; CAD check (g): TC-02 seats axially on nothing): A = the 57.25 H8 bore axis, B = the TC-01 "
        "fwd end face; r_flat 31.313 +0.020/0 from A, OD 63.5 h9 circular runout 0.04 to A, the d5.5 H12 holes position 0.10 dia to A|B at "
        "12.000 BASIC from B, clocking free (match-drilled)"]
    out["note"] = ("pressure rows act only while pressurised (burn); the TC-01 burn maximum is the part maximum over the whole case (a bound for every "
                   "section; the aft sections run much cooler); the rev-3 merged (perfect-contact) run is the hottest burn case on file and is shown "
                   "as the bound; LC4 is the 20 C proof")
    return out


if __name__ == "__main__":
    res = {"id": "jfwd_in718_rows_v352", "version": "v7", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
           "inputs": {"relax_v7_module": {"path": str(J / "jfwd_relax_v352.py"), "sha256_16": sha(J / "jfwd_relax_v352.py")},
                      "js5_cells": {"path": str(R.F_CELLS), "sha256_16": sha(R.F_CELLS)},
                      "fea3d_soak_envelope": {"path": str(R.F_ENV), "sha256_16": sha(R.F_ENV)},
                      "patch_compare": {LBL[h]: {"path": str(R.PATCHES[h] / "compare.json"), "sha256_16": sha(R.PATCHES[h] / "compare.json")} for h in R.PATCHES},
                      "fix_v2_json": {"path": str(FIX2), "sha256_16": sha(FIX2)}, "seat_v1_json": {"path": str(SEAT1), "sha256_16": sha(SEAT1)},
                      "rev5_cad_check_v2": {"path": str(CK5), "sha256_16": sha(CK5)}},
           "J_F1": {"maximum_N": FV0, "minimum_N_today_K_window": round(JF1_MIN, 1), "torque_Nm_today_K_window": round(JF1_T_NMM / 1e3, 3),
                    "K_window": list(JF1_K_WIN), "rule": "lead 17:55:55Z F1: J-F1 sets the flight-lot torque so that the lot's K_min gives <= 3750 N",
                    "columns": JF1_TAG},
           "histories": [LBL[h] for h in HS], "k_b_bracket_N_mm": {k: round(v) for k, v in R.KB.items()},
           "IN718_over_A4-80_soak_gain_ratio": {k: round(v, 4) for k, v in RATIO.items()}, "F_sh_ratio_IN718_over_A4-80": {k: round(v, 4) for k, v in FSH_RATIO.items()},
           "FA1S_thermal_delta_IN718_N": round(D_FA1S, 1), "dF_S_per_dF_V_soak": round(D_FVMAX / (FVMAX - FV0), 4)}
    st_rows = {st: rows_state(st) for st in R.STATES}
    res["states"] = st_rows
    # FA1S screw cell: 5020A Eq. 22 (preload omitted governing, included at the max preload reported), from jfwd_fix_v352_v2
    sc = fix2["options"]["IN718 M5 x10"]["screw_FA1S_5020A"]
    res["FA1S_screw_5020A_eq22"] = {"governing_omitted": sc["governing"], "included": sc["included_at_governing_row"], "gauge_omitted": sc["gauge_governing"],
                                    "arm_+0.4_sens": {k: sc["rows"]["CALC_abs_3888.1|arm_+0.4_sens"][k] for k in ("MS_omitted_governing", "MS_included_info")},
                                    "direct_shear_minor_CALC": sc["direct_shear_minor_231ii"]["CALC_abs_3888.1"], "src": "jfwd_fix_v352_v2.json (published)"}
    # FA1S tap bearing at CALC V (screw-independent): FEA3D's tap_bearing_derived re-based from its V to V 3888.1 / gauge 3862.0
    tb = CELLS["FA1S"]["TC-02"]["tap_bearing_derived"]
    vfe = CELLS["FA1S"]["SCREW"]["V_bear_exact_N"]
    dl = vfe / tb["sigma_MPa"]
    fby, fbu = (1 + tb["MS_y"]) * tb["sigma_MPa"], (1 + tb["MS_u"]) * tb["sigma_MPa"]
    res["FA1S_tap_bearing"] = {V_: {"V_N": V, "sigma_MPa": round(V / dl, 1), "MS_y": ms(fby, V / dl), "MS_u": ms(fbu, V / dl)} for V_, V in (("CALC_3888.1", 3888.1), ("gauge_3862.0", 3862.0))}
    res["FA1S_tap_bearing"]["note"] = (f"FEA3D tap_bearing_derived sigma {tb['sigma_MPa']} at V {vfe} (d x L_e {dl:.2f} mm2, L_e {tb['L_e_mm']}), allowables back-computed "
                                       f"({fby:.1f} / {fbu:.1f} MPa); V-driven, the same for every screw grade")
    res["TC02_thread_shear_full_row"] = thread_full_row(("PRELOAD", "SOAK70", "SOAK", "SOAK52", "FA1S"))
    # v5 (a): the rev-5 minimum bearing ring and worst stack behind the flat-bearing rows (v4's stack kept for the record)
    res["route_i_spring_footprint"] = {
        "areas_mm2": A_SPR, "offsets_t_z_mm": UH_BASES, "quoted_flat_bearing_basis": QUOTED_FLAT_BASIS, "quoted_under_head_basis": QUOTED_UH_BASIS,
        "construction": ("spring annulus De 9.85 (h12 min) / Di 5.32 (H12 max) centred (t, z) from the hole axis, inside the worst-stack flat strip "
                         f"|t| <= {HE_WS} (OD 63.426, eccentricity 0.02, r_flat 31.333, 0.1 flat-to-OD break), outside the hole-break circle "
                         f"{HOLE_BRK} (hole 5.62 max + 0.1 break each side) on the hole axis; nominal: De 10 / Di 5.2, hole 5.5 + 0.2, half chord "
                         f"{HC_NOM - BRK_OD:.4f}, centred; raster 0.002 mm"),
        "cad_crosscheck_raster_vs_CAD": XCHK, "head_on_spring_area_mm2": round(A_HEAD_SPRING, 2),
        "under_head_scaling": "sigma_el,spring = sigma_el,IN718 (force-scaled FE band) x A_ANN 47.12 / A_supp: mean pressure, ASSUMED (TO-VERIFY: pressure-film footprint at J-F1, founder test item; FE spring-footprint run costed by FEA3D after (b1))",
        "rulings": "lead 16:53Z R2 / R4; 17:55:55Z F1 (J-F1 cap 3750 N, under-head at full float as a FLAG), F2 (registered stack 0.4865), F3 (head form), F4 (axial 0.3705), F5 (clocking +/-0.25 deg)"}
    res["TC01_flat_bearing_rev5_min_ring"] = FLAT
    res["TC01_flat_bearing_v4_stack_record"] = FLAT_V4
    # v5 (b): TC-01 case membrane rows (hand_calcs_v2.json) on the minimum wall; v4's h9-only re-evaluation kept for the record
    res["TC01_membrane_rows_min_wall"] = membrane_minwall()
    res["TC01_membrane_rows_OD_h9_v4_record"] = membrane_h9()
    # flags (the ligament station is information and is listed separately)
    fl, fl_info = [], []
    for st, so in st_rows.items():
        for tag, r in so["rows"].items():
            for k, v in r.items():
                for mk in ("MS_y", "MS_u", "MS_vs_Fbry", "MS_strain", "MS_PQ_2Fty", "bound_MS", "MS_y_fibre", "MS_shakedown", "MS_PQ_2Fty_info"):
                    if isinstance(v, dict) and mk in v and v[mk] is not None and v[mk] < FLAG:
                        rec = {"state": st, "preload_N": tag, "row": k, "metric": mk, "MS": v[mk], "flag": flag(v[mk])}
                        if k == "TC01_under_head_band_neuber" and mk == "MS_strain":
                            rec["tag"] = "ASSUMED (mean-pressure scaling on the spring footprint, full float)"
                        (fl_info if (mk.endswith("_info") or tag == "4096") else fl).append(rec)
    res["flags_within_0.05_or_negative"] = fl
    res["information_rows_negative_or_within_0.05"] = fl_info
    res["J_F1_columns"] = JF1_TAG
    s = json.dumps(res, indent=1, default=float)
    OUT.write_text(s)
    print(OUT.name, hashlib.sha256(s.encode()).hexdigest()[:16])
    print("histories", res["histories"], "KB", res["k_b_bracket_N_mm"], "ratios", res["IN718_over_A4-80_soak_gain_ratio"], "Fsh", res["F_sh_ratio_IN718_over_A4-80"],
          "FA1S dN", res["FA1S_thermal_delta_IN718_N"], "dFS/dFV", res["dF_S_per_dF_V_soak"])
    for st, so in st_rows.items():
        print("==", st, "N env from", so["N_envelope_from"], {h: (v["N_IN718_3750_N"], v["N_IN718_4096_N"]) for h, v in so["histories"].items()})
        for tag, r in so["rows"].items():
            line = [f"[{tag}]"]
            for k, v in r.items():
                if k == "screw_tension_234_1b":
                    line.append(f"screw {v['sigma_As_MPa']}MPa y{v['MS_y']:+.3f} u{v['MS_u']:+.3f}")
                elif k == "TC02_thread_shear_An":
                    line.append(f"thread tau {v['tau_MPa']} y{v['MS_y']:+.3f} u{v['MS_u']:+.3f}")
                elif k == "TC01_flat_bearing":
                    line.append(f"flat {v['MS_vs_Fbry']:+.3f} (ff {v['MS_by_spring_basis']['full_float_0.557']:+.3f} no-spring union {v['NO_SPRING_RECORD_union_basis_R4']:+.3f})")
                elif k == "TC01_under_head_band_neuber":
                    b_ = v["by_basis_min"]
                    line.append(f"UH {v['MS_strain']:+.3f}({v['from']}) [nom {b_['nominal_centred_like_for_like_v6']:+.3f} conc {b_['worst_stack_concentric']:+.3f} "
                                f"reg {b_['registered_stack_0.4865_F2']:+.3f} ff {b_['full_float_0.557']:+.3f} v6 {v['V6_RECORD_min']:+.3f}]")
                elif k == "head_on_spring_IN718":
                    line.append(f"head/spring {v['MS_y']:+.3f}")
                elif k == "TC01_ligament_station_PQ_FEA3D_cell_INFO":
                    line.append(f"lig(info) {v['MS_PQ_2Fty_info']:+.3f}/env {v['envelope_scaled_bound_info']['MS']:+.3f}")
                elif k.endswith("_PQ"):
                    line.append(f"{k[:4]} {v['MS_PQ_2Fty']:+.3f}({v['from']})/bnd {v['bound_MS']:+.3f}")
                elif k == "TC01_lines_Pm_gt_Fty":
                    e = v["envelope"]
                    line.append(f"Pm>Fty seat {e['seat']['A4-80']}->{e['seat']['IN718_Fsh']}/{e['seat']['IN718_headforce_bound']} hole {e['hole_edge']['A4-80']}->{e['hole_edge']['IN718_Fsh']}/{e['hole_edge']['IN718_headforce_bound']}")
                elif k == "screw_fibre_soak":
                    line.append(f"fibre y{v['MS_y_fibre']:+.3f} shk{v['MS_shakedown']:+.3f} rng {v['range_max_MPa']} set {v['max_equiv_axial_set_um']}um")
            print("  " + " | ".join(line))
    print(json.dumps(res["FA1S_tap_bearing"]))
    print(json.dumps(res["FA1S_screw_5020A_eq22"]))
    t = res["TC02_thread_shear_full_row"]
    print("A_n bases", json.dumps(t["A_n_bases"]))
    for st, rr in t["rows"].items():
        print("  thread", st, {k: (v["N_N"], v["THE_ROW"]["MS_y"], v["THE_ROW"]["MS_u"], v["info_local_gap_0"]["MS_y"], v["SUPERSEDED_FEA3D_A_n_63.48"]["MS_y"]) for k, v in rr.items()})
    print("  governing", t["governing_state"], json.dumps(t["fixes"]["a_lower_J-F1_max"])[:200])
    for k, v in t["fixes"]["b_custom_IN718_length"]["options"].items():
        print("  ", k, v["L_e_gap_bound_mm"], v["A_n_gap_bound_mm2"], v["tip_clearance_to_full_thread_end_min_mm"], v["tip_ok"], v["status"], v["rows_at_governing_state"])
    print("FLAT v5", json.dumps(FLAT))
    mw = res["TC01_membrane_rows_min_wall"]
    print("membrane min wall geometry", json.dumps(mw["minimum_wall_geometry"]))
    print("burn", mw["TC01_burn_max_C (pressurised)"])
    for x in mw["rows"]:
        print("  ", x["row"][:60], "nom", x["nominal"]["MS_y"], x["nominal"]["MS_u"], x["nominal"]["T_allow_C"], "| min", x["min_wall"]["wall_mm"], x["min_wall"]["applied_MPa"],
              x["min_wall"]["MS_y"], x["min_wall"]["MS_u"], x["min_wall"]["T_allow_C"], "Tmargin", x["T_margin_K"])
    print("governing", mw["governing_min_wall_row"], "lowest T_allow", mw["lowest_T_allow_min_wall"])
    print("flags:")
    for f in fl:
        print("  ", f)
    print("information rows:")
    for f in fl_info:
        print("  ", f)
