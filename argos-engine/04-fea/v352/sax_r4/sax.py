"""S-AX v1 - axisymmetric thermo-mechanical FE of the assembled engine pressure structure (04-fea/structural, 2026-10-13, Mechanical).

Question (founder, through the lead): full FEA of the assembled engine at max thrust - thermo-mechanical transient, MEOP and proof,
fasteners and seals, graphite insert, convergence, margin table.  This module is the AXISYMMETRIC part (pressure + thermal + axial
inertia).  The gimbal load path (lateral, moments, servo stall, stop) is S-3D (gimbal_strength.py); the fasteners and seals are the
FE-informed hand calculations of joints.py.

GEOMETRY (CAD v3.4.1 rev B DESIGN model, config.V34_ON: nozzle joint J1, TC-03 IN718, D_pre 49.9 mm, carbon-phenolic NZ-02), engine
frame of the v3.4.1 assembly (build.build(engine, gimbal, feed), pivot FROZEN at the rev A mid-burn CG, z_head_mid 155.513 mm; the
rev B mid-burn CG is 2.74 mm aft of it), cut by the half-plane at 214 deg (ax_section.ANGLE, clear of every non-axisymmetric
feature).  Rev B: the rev A TC-09 aft cone ran through the inner step corner (wall -0.38 mm, two disconnected section faces, rigid-body
nozzle in the first S-AX solve, 3.7e9 mm); parts_engine TC-09 rev B starts the cone so that the wall normal at the step is the aft
wall thickness.  The rev A runs are kept in runs/structural/revA_evidence.  Structural parts: TC-01 case, TC-02 head, TC-03 seat insert,
TC-04 bonnet, TC-09 aft section, NZ-01 graphite insert, NZ-02 sleeve, NZ-03 J1 hot layer, NZ-04 J1 lip seal.  The insulators
(TC-06/07/08/10) and the grain are NOT structural members: no seal acts on them, so the chamber gas reaches every insulator joint and
the pressure is applied to the metal behind them (bounded by the seals S01 head gland, S13 aft gland, NZ-04 lip face).
Non-axisymmetric features (8 x M5 radial screws, 4 x M4 bonnet bolts, ports, flats, TC wells) are smeared or omitted: their local
stresses are joints.py hand calculations.

JOINTS (every part has its own nodes; ties are *EQUATION couplings of coincident node pairs):
  TC-01/TC-02  head plug in the case bore: released (sliding fit, clearance), u_z tied over the M5 screw band (bolt_z_fwd +/- 2.5 mm).
  TC-01/TC-09  M63x1.5 thread over the engagement (aft_land_top .. aft_thread_top), smeared: DESIGN variant (SAX_TIES=axial, rev B
               run 2) u_z only (radial flank clearance); BOUND variant (bonded, = run 1) u_r and u_z; the 61.0 land below it released
               (sliding fit, S13 gland).
  TC-02/TC-03  M14x1 thread + flange seat: DESIGN u_z only (flange 0.1 mm radial clearance in its counterbore, thread flank clearance);
               BOUND u_r and u_z (run 1).  The radial gap change of the released thread interfaces is reported (overlap = the parts would
               wedge: the bound variant brackets it).
  TC-02/TC-04  bonnet flange: tied over the M4 bolt-head band (r 14.0 .. 19.0), released elsewhere (face O-ring at r 7.2).
  TC-09/NZ-04  lip face: u_z tied, radial sliding free (no friction credited: the lip carries the insert load without radial restraint).
  NZ-01/NZ-02  insert OD vent gap: released and pressurised (4 vent grooves, hand_calcs v2 design condition).
  NZ-01..NZ-04 stack (NZ-01/02 on NZ-03, NZ-03 on NZ-04): tied (pressure-energised bearing stack; no separation credited).
  Every released interface is checked after the solve (relative displacement normal to it: overlap = assumption violated, reported).

LOADS (linear superposition, exact for a fixed temperature field because E(T) does not depend on the load):
  step 1 thermal only (nodal temperatures mapped from the 2-D thermal FE, stress-free state 20 C);
  step 2 + unit chamber pressure 1 MPa, operating profile p(z)/Pc along the nozzle (Combustion thermal_bc_max_v2.csv);
  step 3 + unit chamber pressure 1 MPa, BLOCKED nozzle (Pc to the throat + the plug load P pi r_t^2 on the convergent band at the
          throat: total insert load P pi r_bore^2, loadcases v1 BN / LC4);
  step 4 + unit manifold pressure 1 MPa (head bore, TC-03 above the seat, bonnet to the stem seal);
  step 5 + 1 g axial body force toward -Z (inertia of a +Z acceleration: thrust, touchdown).
  Unit responses = step k - step 1.  Support (rev B run 2): step 1 u_z = 0 at ONE node of the case groove bottom (mid-plane,
  statically determinate: the thermal field is self-equilibrated and free to expand); steps 2-5 *BOUNDARY, FIXED on the whole groove
  band (v3.4.1 frame z -10..+10): the collar reacts the mechanical loads over the band at the thermally displaced position; radial free.
  Run 1 fixed u_z = 0 on the band in every step, which restrained the thermal growth of the 20 mm band (E alpha dT ~ 200 MPa in the soak
  states at the groove): superseded, kept in runs/structural/revB_run1_evidence.
THERMAL MAPPING (rev B run 2): part-aware; each structural part is interpolated on the thermal elements of the same part (nearest node
  of the same part when outside).  Run 1 used the whole thermal mesh: the TC-09 lip bore at the exit plane took the NZ-01 graphite
  temperature (1693 C) and TC-02 nodes next to the insert flange fell inside TC-03 thermal elements (the head is cut at 90 deg, the
  thermal model at 214 deg).
  Load cases (combos): LC1, LC2 (MEOP), BN (blocked nozzle 63.08 bar), LC4 (proof 67.5 bar, 20 C), TS1a/TS1b (A1 relight), TS2 (soak,
  thermal only), SEGP (manifold 99.75 bar), TB70 (S6 throat block 58.1 bar, BLOCKED distribution) and TBS (63.1 bar) with the case at the
  448.15 K abort (ASSUMED uniform shift of the B1 end-of-burn field), LC6 (touchdown 10 g axial on the soak states).
PART ROLES (lead 2026-10-13, PART_ROLE): load-bearing metals TC-01/02/03/04/09; NZ-01 graphite load-bearing brittle; NZ-03 load-bearing
ablative (J1 hot layer in the stack); NZ-02 ablative / insulating sleeve; NZ-04 seal.  Every margin row carries the role, the criterion
and a status: a negative margin is reported as a design change (load-bearing) or under its own criterion (ablative / seal), never as a
pass.  Carbon-phenolic above T_char (engmat, 450 C): char zone, no thermal-stress criterion; primary (mechanical-only) compression vs
the ASSUMED char strength Sc(T); no tension credit.
CRITERIA (loadcases v2): MS = allowable(T) / (SF x sigma_vM) - 1 with the combined (thermal + mechanical) elastic stress at the node,
6061/316L/IN718 Fty/Ftu tables of engmat v1.2 at the node temperature; graphite / carbon-phenolic: maximum principal stress vs
strength with the ultimate factor.  Peaks at re-entrant corners and tie ends are singular in a linear model: they are reported but the
margins use (a) linearised membrane+bending stresses on stress classification lines (SCL) and (b) the peak outside a 1.0 mm exclusion
radius around singular points; the convergence study (3 mesh levels) shows which quantities converge.  SCL: primary Pm and Pm+Pb
(mechanical only) vs Fty(T)/SF, and P+Q (thermal + mechanical) vs the shakedown limit 2 Fty(T).
Outputs: results/sax_results_<tag>_v1.json, margin and SCL tables (CSV), convergence json, VTU fields (cmd vtu), Ansys Mechanical APDL
decks (cmd ansys: PLANE183 axisymmetric, consistent nodal forces, coupled sets for the ties, FSUM check line).
Units: mm, N, MPa, K, t/mm3.  CalculiX 2.21 CAX6.  Forces of axisymmetric models are per 2 deg segment in ccx (x 180 = full ring).
"""
from __future__ import annotations
import argparse, csv, gzip, hashlib, json, math, os, re, shutil, subprocess, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
FEA = HERE.parent
CAD = FEA.parent / "03-cad" / "src"
sys.path.insert(0, str(CAD))
sys.path.insert(0, str(FEA / "src"))
sys.path.insert(0, str(FEA / "thermal"))
import engmat  # noqa: E402

VERSION = "v1"
RUNS = Path("/home/claude/work/mechanical/runs/structural")
THERMAL_RUNS = Path("/home/claude/work/mechanical/runs/thermal")
COMB_BC = Path("/home/claude/work/shared-fallback/engine/02-combustion/data/v2/thermal_bc_max_v2.csv")
ANGLE = 214.0
# v1: TC-02 and TC-04 are cut at 90 deg.  At 214 deg the plane crosses the E1-M radial filter bore of the v3.4 head (d 14 at az 180,
# r 9.5-33: covers az 180 +/- 47 deg at r 9.5) and the E1-M bonnet boss: in an axisymmetric model that becomes a ring void.  90 deg is
# clear in v3.4.1 for both (nearest: M5 67.5/112.5 +/-5.5, PD-01 feet 70/110 +/-2.8, bonnet bolts 60/120 +/-13 with the counterbore,
# Pc connector flat at 142 deg, torch flat |az| < 58).  TC-09 stays at 214 deg (its J1 T1 well is at az 90, r 17.5, 5 mm deep).
# The thermal FE (all parts at 214 deg) contains the filter-bore ring void: the mapped head temperatures carry that local artefact.
ANGLE_PART = {"ENG-TC-02": 90.0, "ENG-TC-04": 90.0}
PARTS = ["ENG-TC-01", "ENG-TC-02", "ENG-TC-03", "ENG-TC-04", "ENG-TC-09", "ENG-NZ-01", "ENG-NZ-02", "ENG-NZ-03", "ENG-NZ-04"]
PRIO = {p: i for i, p in enumerate(PARTS)}
SIZE = {"ENG-TC-01": 0.5, "ENG-TC-02": 0.9, "ENG-TC-03": 0.35, "ENG-TC-04": 0.9, "ENG-TC-09": 0.45, "ENG-NZ-01": 0.6, "ENG-NZ-02": 0.4,
        "ENG-NZ-03": 0.3, "ENG-NZ-04": 0.12}           # mm at level 1.0
SIZE_GAS = 0.2                                        # mm at level 1.0 on the gas-side curves of the insert and the TC-03 diffuser
DIST_GAS = 3.0                                        # mm growth distance
TOL_MM = 0.10                                         # CAD clearances <= 0.10 mm are closed (as the thermal mesh)
T_REF = 293.15                                        # K stress-free assembly temperature
# FMEA FA-1 (lead 2026-10-13): fuel-assisted fast part at an A1 relight (32.2 mm port), head-end pulse, SIM from Combustion
FA1 = {"P_head_abs_bar": 75.519, "P_aft_abs_bar": 72.743, "t_above_45bar_s": 0.0030, "tf_s": 0.001,
       "src": "Combustion 02-combustion/data/v2/v2p4/late_light_spike_v2p4.json 57fce738164fd571 fuel_assisted_relight"
              "['A1_relight|sharp_Cd0.65|0.200|tf1ms|tres0.06|fret1_q2.0'] (SIM on ASSUMED inputs, worst of 48 rows); the stored traces "
              "(flight_latest, tf 1 ms) rise 10-90 % in 0.8 ms"}
FA1Q_BAR = 90.0                                       # bar abs, FA-1 INTERIM quasi-static (lead CHANGELOG 172 (2); ENG-09 ultimate point)
FA1D_BAR, FA1U_BAR = 92.0, 102.0                      # bar abs, FA-1 final rule for 0.25-1 ms parts (lead CHANGELOG 173): design / sensitivity
# v3.5.1 (lead CHANGELOG 194, REV-COMB-3 R3-02/R3-04): period domain. T <= 0.1 ms: 90 bar abs (FA1Q); 0.1 < T <= 1 ms: yield at 93 bar abs
# (FA1D, replaces 92) and ultimate at 102 (FA1U); T > 1 ms: the all-case spectrum at the part's period, or FA1S (DLF 2.0 on the 75.5 bar
# head peak, ~151 bar abs) until the modal closure lists every pressure-loaded load path with its period.  SF 1.0 (188 (9)).
G = 9810.0                                            # mm/s2
MAT_MECH = ["AL6061-T6", "IN718", "SS316L", "GRAPHITE-ISO", "CARBON-PHENOLIC", "FLEX-GRAPHITE-OI", "ZIRCONIA-FS", "GLIDCOP-AL15", "FLEX-GRAPHITE-TH"]
BRITTLE = {"GRAPHITE-ISO": ("St", "Sc"), "CARBON-PHENOLIC": (None, "Sc"), "FLEX-GRAPHITE-OI": (None, "Sc"), "ZIRCONIA-FS": ("St", "Sc"),
           "FLEX-GRAPHITE-TH": (None, "Sc")}
EDGE = {1: (0, 1, 3), 2: (1, 2, 4), 3: (2, 0, 5)}     # CAX6 face -> (corner, corner, mid); ccx faces P1..P3
# rev B run 2: thread / insert-flange tie variant.  'axial' (DESIGN model): the M14x1 seat-insert thread + flange seat (TC-02/TC-03)
# and the M63x1.5 aft thread (TC-01/TC-09) transmit u_z only (smeared thread with radial flank clearance; the TC-03 flange has 0.1 mm
# radial clearance in its counterbore).  'bonded' (BOUND, the run-1 rule): u_r and u_z tied, which forces radial compatibility of parts
# at very different temperatures (upper bound of the thermal interaction stress).  Environment variable SAX_TIES; the run directory
# carries the variant (L<level> = axial, L<level>_bonded).
TIES = os.environ.get("SAX_TIES", "axial")
assert TIES in ("axial", "bonded"), TIES
# DESIGN-CHANGE SCREENING (2026-10-13): SAX_MATOV="ENG-TC-09=IN718[,PN=MAT]" re-assigns part materials (engmat keys) on the same
# conforming mesh and the SAME thermal fields (the thermal runs keep their own materials: a screening approximation until the thermal
# model is re-run with the new material).  The run directory carries the variant (e.g. L1_TC09IN718).
MATOV = dict(kv.split("=") for kv in os.environ.get("SAX_MATOV", "").split(",") if kv.strip())
# rev B run 3 (2026-10-13): SAX_THERMAL_TAG selects the thermal runs that feed the states (default: the design J1 rev B runs).  Used for
# the TC-09 IN718 design change with its own thermal runs ('v13pre36IN_J1revB_TC09IN', replaces the screening approximation above) and
# for the nozzle joint J2 screen ('v13pre36IN_J2revB', with SAX_MATOV="ENG-NZ-03=ZIRCONIA-FS": J2 has the J1 stack geometry).  The run
# directory carries '_th<tag without v13pre36IN_>'.
THERMAL_TAG_DESIGN = "v13pre36IN_J1revB"
THERMAL_TAG = os.environ.get("SAX_THERMAL_TAG", THERMAL_TAG_DESIGN)
# v3.5.1 (2026-10-13, Mechanical successor): SAX_CAD=v351 builds the section from config.V351_ON (TC-03 TB1 recessed flange + GlidCop AL-15,
# TC-09 IN718 from the CAD, J1) into the cache runs/structural/geom_v351, applies the lead 188 (9) safety-factor rule and the lead 194 FA-1
# period domain (FA1D at 93 bar); the run directory carries '_cad351'.  Default 'v341revB' reproduces the v3.5 runs.
CADV = os.environ.get("SAX_CAD", "v341revB")
# v3.5.2 (lead CHANGELOG 206 (2a), 2026-10-13): SAX_CAD=v352 builds config.V352_ON (TC-09 barrel wall 1.80 mm, socket OD 69.0 above the
# gland) into runs/structural/geom_v352; same SF rule and FA-1 period domain as v351; run directory and outputs carry '_cad352'.
# v3.5.2 rev 4 (2026-10-20, lead DC 05:42Z item 4, 06:05Z item 4, 06:23Z items 2-5): SAX_CAD=v352r4 builds config.V352_ON (rev 4 TC-02 /
# TC-03 seat: entry R0.5, thread undercut / relief, TC-03 top 0.15 below the shoulder) into geom_v352r4; 'v352' now builds
# config.V352_REV3_ON (= the V352_ON of every earlier v352 run).  The S-AX TC-02 section is cut to the thread major r 7.0 over the M14x1
# band (the smeared internal-thread teeth r 6.5-7.0 go to nothing; the overlap with TC-03 was owned by TC-03 before); TC-03 is fragmented
# in a second stage at TOL_TIGHT so the rev-4 clearances below TOL_MM are not bridged; SAX_ENTRY_H (mm, default 0.1) sets the element size
# on the rev-4 seat curves (entry radius / undercut / thread start, thread end / relief / chamfer / blend / top gap) within 0.2 mm; the
# run directory carries '_cad352r4_eh<h>'.
assert CADV in ("v341revB", "v351", "v352", "v352r4"), CADV
ENTRY_H = float(os.environ.get("SAX_ENTRY_H", "0.1")) if CADV == "v352r4" else None
TOL_TIGHT = 1.0e-4
if CADV in ("v352", "v352r4"):
    # v3.5.2 (2026-10-20, Mechanical): the J-FWD 10x M5 taps (lead CHANGELOG 231 (1), az 18 + 36k deg) put a tap AT 90 deg, the v3.5.1 TC-02 /
    # TC-04 cut; at 78 deg the TC-02 / TC-04 section areas equal the v3.5.1 90 deg section (plateau 74-82 deg: v352/checks/scan_tc02_angle.py,
    # scan_tc02_angle_v1.json), so the head and bonnet are cut there.  TC-01 stays at 214 deg (J-FWD holes at 198 / 234 +/- 5).
    ANGLE_PART = {"ENG-TC-02": 78.0, "ENG-TC-04": 78.0}
if CADV in ("v351", "v352", "v352r4"):
    FA1D_BAR = 93.0
CADTAG = {"v341revB": "", "v351": "_cad351", "v352": "_cad352",
          "v352r4": "_cad352r4_eh" + (f"{ENTRY_H:g}".replace(".", "p") if ENTRY_H else "")}[CADV]   # v3.5.1 / v3.5.2 outputs never overwrite the v3.5 files
# v3.5.2 gap-conductance variant (lead 2026-10-20 (2)): SAX_R10=free models the TC-02 / TC-03 r-10 clearance as the CAD has it (TC-03 flange
# OD 20.0 in the TC-02 counterbore 20.2, radial 0.10 mm; closed by the 0.10 mm fragment and tied in z like the rest of that interface in
# every earlier run): the flange-OD interface nodes (r >= 9.95, z below the counterbore floor z_fl1 = z_ins_top - 10 by > 0.01 mm) are
# released in r and z (free = frictionless contact that does not close; the released-interface gap check shows whether it closes);
# the flange top face on the counterbore floor and the M14x1 thread keep their z-tie.  The run directory carries '_r10free'.
R10 = os.environ.get("SAX_R10", "tied")
assert R10 in ("tied", "free"), R10
# v3.5.2 RM2-04 routing (lead CHANGELOG 234 (4), 2026-10-20): SAX_NZTIE=normal models the nozzle-stack interfaces (NZ-01/02/03/04/06) as
# frictionless contact that stays closed: on a horizontal interface run only z is tied, on a vertical run only r; a node on both (corner)
# keeps r and z; NZ-02 / NZ-06 (foil OD r 21.95 against the NZ-02 bore r 22.01: 0.06 mm radial clearance in the CAD, closed by the mesh
# fragment) is released as the CAD has it.  Bound with the tied run: tied = bonded (upper bound on edge shear), normal = mu 0 (lower bound).
# The run directory carries '_nznormal'.
NZTIE = os.environ.get("SAX_NZTIE", "tied")
assert NZTIE in ("tied", "normal"), NZTIE
NZ_STACK = {"ENG-NZ-01", "ENG-NZ-02", "ENG-NZ-03", "ENG-NZ-04", "ENG-NZ-06"}
NZ_ORIENT = {}                                    # (pa, pb sorted, r, z rounded) -> 'z' | 'r' | 'rz'; filled by duplicate() when NZTIE == normal


def _nz_orient(owners, X):
    """Interface orientation of every shared node of an NZ-stack pair: 'z' on a horizontal run, 'r' on a vertical run, 'rz' at a corner."""
    by = {}
    for n, ps in owners.items():
        ps = sorted(ps)
        for i in range(len(ps)):
            for j in range(i + 1, len(ps)):
                if {ps[i], ps[j]} <= NZ_STACK:
                    by.setdefault((ps[i], ps[j]), []).append(n)
    out = {}
    for pr, ns in by.items():
        P = X[np.array(ns)]
        for k, n in enumerate(ns):
            dr, dz = np.abs(P[:, 0] - P[k, 0]), np.abs(P[:, 1] - P[k, 1])
            hor = bool(((dz < 1e-4) & (dr > 1e-6) & (dr < 1.0)).any())
            ver = bool(((dr < 1e-4) & (dz > 1e-6) & (dz < 1.0)).any())
            out[(pr[0], pr[1], round(float(X[n, 0]), 4), round(float(X[n, 1]), 4))] = ("rz" if (hor and ver) or not (hor or ver)
                                                                                      else ("z" if hor else "r"))
    return out
# v3.5.2 N-F2 (lead CHANGELOG 212, 2026-10-13): the 0.25 mm flexible-graphite load-spreading foil NZ-06 between the NZ-01 shoulder (R 1.0
# outer edge) and the J1 hot layer NZ-03 joins the tied nozzle stack (as NZ-03 / NZ-04).  Present only in the v3.5.2 CAD.
if CADV in ("v352", "v352r4"):
    PARTS.append("ENG-NZ-06")
    PRIO = {p: i for i, p in enumerate(PARTS)}
    SIZE["ENG-NZ-06"] = 0.06                         # mm at level 1.0: >= 4 quadratic elements through the 0.25 mm foil


def run_dir(level):
    return RUNS / (f"L{level:g}" + ("" if TIES == "axial" else f"_{TIES}")
                   + "".join(f"_{k.replace('ENG-', '').replace('-', '')}{v.split('-')[0]}" for k, v in sorted(MATOV.items()))
                   + ("" if THERMAL_TAG == THERMAL_TAG_DESIGN else "_th" + THERMAL_TAG.replace("v13pre36IN_", ""))
                   + ("_r10free" if R10 == "free" else "") + ("_nznormal" if NZTIE == "normal" else "") + CADTAG)


def _matov_geometry(faces, info):
    if MATOV:
        for f in faces:
            if f["pn"] in MATOV:
                f["material"] = MATOV[f["pn"]]
        info["materials"] = {k: MATOV.get(k, v) for k, v in info["materials"].items()}
        info["material_overrides_screening"] = dict(MATOV)
    return faces, info


def _matov_mesh(d):
    if MATOV:
        mat = np.array(d["mat"], dtype=object)
        for pn_, m_ in MATOV.items():
            mat[np.asarray(d["pn"]) == pn_] = m_
        d["mat"] = mat.astype(str)
    return d


# Role of every structural part and the criterion its margin uses (lead 2026-10-13: state per part whether it carries the stress or
# is a sacrificial / ablative layer, and which criterion applies; a negative margin is never presented as a pass).
PART_ROLE = {
    "ENG-TC-01": ("LOAD-BEARING", "case, pressure vessel + thrust path: metal (Fty/Ftu at T; primary SF, P+Q shakedown 2 Fty)"),
    "ENG-TC-02": ("LOAD-BEARING", "forward closure (head): metal criterion as TC-01"),
    "ENG-TC-03": ("LOAD-BEARING", "seat insert, pressure + seat: metal criterion; hot face above the material usable limit is flagged"
                  + (" (v3.5.1 GlidCop AL-15: RT strength from the Hoganas datasheet x 0.8, hot retention ASSUMED: margins at T > 20 C CONDITIONAL)"
                     if os.environ.get("SAX_CAD", "v341revB") in ("v351", "v352", "v352r4") else " (IN718 usable 650 C)")),
    "ENG-TC-04": ("LOAD-BEARING", "bonnet, manifold pressure: metal criterion"),
    "ENG-TC-09": ("LOAD-BEARING", "aft section: aft closure + the lip that carries the nozzle stack (J1): metal criterion"),
    "ENG-NZ-01": ("LOAD-BEARING (brittle)", "graphite throat insert: carries the nozzle pressure load in bearing; brittle: s1 vs St, s3 vs "
                  "Sc at RT strength (rise with T not credited), total (thermal + mechanical) stress, SF 2.0 flight / 1.5 bound cases"),
    "ENG-NZ-02": ("ABLATIVE / INSULATING", "carbon-phenolic sleeve: virgin zone (T <= T_char) brittle compression on total stress; char "
                  "zone: not a stress member (char depth is the criterion, thermal FE); primary compression in the char reported"),
    "ENG-NZ-03": ("LOAD-BEARING + ABLATIVE", "carbon-phenolic J1 hot-layer washer in the stack load path: virgin zone brittle compression on "
                  "total stress; char zone: PRIMARY bearing stress vs char compressive strength (ASSUMED band, test required)"),
    "ENG-NZ-04": ("SEAL (bearing)", "flexible-graphite lip seal: compression vs maximum gasket stress (ASSUMED) and T vs the class limit"),
    "ENG-NZ-06": ("LOAD-SPREADER (sacrificial)", "v3.5.2 N-F2 flexible-graphite foil between the insert shoulder and NZ-03: compression vs "
                  "maximum gasket stress (ASSUMED); above its ~400 C in-air rating by design at the 1500 C shoulder (confined joint, "
                  "oxidation loss TO-VERIFY at T1); its purpose is the NZ-03 bearing distribution"),
}
if MATOV.get("ENG-NZ-03") == "ZIRCONIA-FS":
    PART_ROLE["ENG-NZ-03"] = ("LOAD-BEARING (brittle)", "J2 SCREEN: dense fully stabilised zirconia hot-layer washer in the stack load path: brittle "
                              "s1 vs St and s3 vs Sc on total (thermal + mechanical) stress, strengths ASSUMED (as recalled, engmat v1.4); "
                              "thermal-shock cracking acceptable only while confined and in compression (Combustion nozzle_joint_v2p4)")


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


# =============================================================================================== geometry
def geometry(cache=None, rebuild=False):
    """Section faces of the structural parts (x = r, y = z, mm, v3.4.1 frame) + stations.  Cached as BREP + JSON."""
    import cadquery as cq
    cache = cache or (RUNS / ("geom_v341revB" if CADV == "v341revB" else f"geom_{CADV}"))
    cache.mkdir(parents=True, exist_ok=True)
    fj = cache / "geometry.json"
    if fj.exists() and not rebuild:
        d = json.loads(fj.read_text())
        faces = [{"pn": f["pn"], "material": f["material"], "face": cq.Face(cq.Shape.importBrep(str(cache / f["brep"])).wrapped),
                  "area_mm2": f["area_mm2"]} for f in d["faces"]]
        return _matov_geometry(faces, d["info"])
    import build, config
    import ax_section
    from geom import apply
    t0 = time.time()
    P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=True,
                                  overrides={"v341revB": config.V34_ON, "v351": config.V351_ON, "v352": config.V352_REV3_ON,
                                             "v352r4": config.V352_ON}[CADV])
    zlo, zhi = S["aft_bottom"] - 30.0, S["bonnet_top"] + 30.0
    planes = {}
    for ang in set(ANGLE_PART.values()) | {ANGLE}:
        a = math.radians(ang)
        d = (math.cos(a), math.sin(a))
        pts = [cq.Vector(0, 0, zlo), cq.Vector(150 * d[0], 150 * d[1], zlo), cq.Vector(150 * d[0], 150 * d[1], zhi), cq.Vector(0, 0, zhi)]
        planes[ang] = (cq.Face.makeFromWires(cq.Wire.makePolygon(pts, close=True)), ax_section.T_to_2d(ang))
    faces, rec = [], []
    for pn, i, grp, shp, body in build.posed_instances(reg, S, 0, 0):
        if pn not in PARTS:
            continue
        plane, T2 = planes[ANGLE_PART.get(pn, ANGLE)]
        for k, f in enumerate(shp.intersect(plane).Faces()):
            f2 = apply(f, T2)
            if CADV == "v352r4" and pn == "ENG-TC-02" and S.get("tc02_r4"):
                # rev 4: TC-02 to the thread major r 7.0 over the M14x1 band (z_fl1 + 0.4 .. thread end + 0.01; the entry radius and the
                # relief run-out lie at r >= 7.0 there, so only the smeared tooth band r 6.5-7.0 is removed)
                z_fl1_, z_te_ = S["tc03_flange_z"][1], S["tc02_r4"]["thread_end_z_top"]
                bb_ = f2.BoundingBox()
                if bb_.xmin < 7.0 and bb_.ymin < z_te_ and bb_.ymax > z_fl1_:
                    cut_ = cq.Face.makeFromWires(cq.Wire.makePolygon([cq.Vector(5.5, z_fl1_ + 0.4, 0), cq.Vector(7.0, z_fl1_ + 0.4, 0),
                                                                      cq.Vector(7.0, z_te_ + 0.01, 0), cq.Vector(5.5, z_te_ + 0.01, 0)], close=True))
                    res_ = f2.cut(cut_).Faces()
                    assert len(res_) == 1, f"rev-4 TC-02 cut gave {len(res_)} faces"
                    f2 = res_[0]
            nm = f"{pn}_{k}.brep"
            f2.exportBrep(str(cache / nm))
            faces.append({"pn": pn, "material": reg.parts[pn].material, "face": f2, "area_mm2": f2.Area()})
            rec.append({"pn": pn, "material": reg.parts[pn].material, "brep": nm, "area_mm2": f2.Area()})
    keys = ("head_top", "head_bot", "inj_face", "grain_top", "grain_bot", "tube_fwd", "tube_aft", "aft_bottom", "throat", "insert_top",
            "insert_bot", "insert_shoulder", "lip_top", "post_bot", "bonnet_top", "aft_step", "aft_land_top", "aft_thread_top", "z_ins_top",
            "z_seat", "exit", "rt", "re", "bolt_z_fwd", "nz_seal_t", "nz_hot_layer_t", "r_insert_bore")
    info = {k: float(S[k]) for k in keys if k in S}
    info["fwd_glands"] = [float(x) for x in S["fwd_glands"]]
    info["aft_gland"] = [float(x) for x in S["aft_gland"]]
    info["collar_groove"] = [float(x) for x in S["collar_groove"]]
    info["aft_section"] = {k: (float(v) if isinstance(v, (int, float)) else v) for k, v in S["aft_section"].items()}
    info["contour"] = [(float(z), float(r)) for z, r in S["contour"]]
    info["z_head_mid_mm"] = P["z_head_mid"]["v"] * 1e3
    info["nozzle_joint"] = S.get("nozzle_joint")
    info["materials"] = {f["pn"]: f["material"] for f in faces}
    if CADV == "v352r4":                                       # rev-4 seat stations (S-AX frame, mm)
        info["seat_r4"] = S.get("tc0203_seat_r4")
        info["tc02_r4"] = S.get("tc02_r4")
        info["tc03_r4"] = S.get("tc03_r4")
        info["tc03_top_z"] = float(S["tc03_top_z"])
        info["z_fl1"] = float(S["tc03_flange_z"][1])
        info["tc0203_engagement_mm"] = S.get("tc0203_engagement_mm")
    info["params"] = {k: P[k]["v"] for k in ("case_OD", "case_t", "MEOP_chamber", "MEOP_tank", "Pc_max", "P_blocked_nozzle", "proof_factor",
                                             "SF_yield", "SF_ult", "F_max", "insert_OD", "insert_sleeve_t", "lip_ID", "lip_bore_d", "aft_lip_t",
                                             "aft_wall_t", "bolt_d_chamber", "n_bolts_chamber", "case_bore_seal", "case_aft_land_d", "aft_thread_len")}
    info["build_s"] = round(time.time() - t0, 1)
    fj.write_text(json.dumps({"faces": rec, "info": info, "cad": {"v341revB": "v3.4.1 config.V34_ON", "v351": "v3.5.1 config.V351_ON", "v352": "v3.5.2 config.V352_REV3_ON (rev 3)",
                                                                    "v352r4": "v3.5.2 config.V352_ON (rev 4 seat)"}[CADV],
                              "angle_deg": ANGLE, "angle_part_deg": ANGLE_PART}, indent=1))
    return _matov_geometry(faces, info)


# =============================================================================================== mesh
def mesh(faces, info, level=1.0, workdir=None, verbose=False):
    """Conforming CAX6 mesh of the structural faces (gmsh fragment, TOL 0.10 mm).  Returns X (N,2), E (M,6, CCW), pn (M,), mat (M,)."""
    import gmsh
    workdir = Path(workdir or RUNS / "mesh")
    workdir.mkdir(parents=True, exist_ok=True)
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1 if verbose else 0)
    gmsh.option.setNumber("General.NumThreads", 1)
    gmsh.model.add("sax")
    in_tags = []
    for k, f in enumerate(faces):
        b = workdir / f"s{k}.brep"
        f["face"].exportBrep(str(b))
        in_tags.append([t for d, t in gmsh.model.occ.importShapes(str(b)) if d == 2])
    gmsh.model.occ.synchronize()
    tight = [k for k, f in enumerate(faces) if f["pn"] == "ENG-TC-03"] if CADV == "v352r4" else []
    if not tight:
        gmsh.option.setNumber("Geometry.ToleranceBoolean", TOL_MM)
        allin = [(2, t) for ts in in_tags for t in ts]
        out, omap = gmsh.model.occ.fragment(allin[:1], allin[1:])
        gmsh.model.occ.synchronize()
        src_lists = [[k] for k, ts in enumerate(in_tags) for _ in ts]
    else:   # rev 4: stage 1 every face but TC-03 at TOL_MM, stage 2 with TC-03 at TOL_TIGHT (lead 06:23Z item 5)
        gmsh.option.setNumber("Geometry.ToleranceBoolean", TOL_MM)
        s1 = [(2, t) for k, ts in enumerate(in_tags) if k not in tight for t in ts]
        src1 = [k for k, ts in enumerate(in_tags) if k not in tight for _ in ts]
        out1, omap1 = gmsh.model.occ.fragment(s1[:1], s1[1:])
        gmsh.model.occ.synchronize()
        own1 = {}
        for j, lst in enumerate(omap1):
            for d, t in lst:
                if d == 2:
                    own1.setdefault(t, set()).add(src1[j])
        gmsh.option.setNumber("Geometry.ToleranceBoolean", TOL_TIGHT)
        objs = [(2, t) for t in sorted(own1)]
        tools = [(2, t) for k in tight for t in in_tags[k]]
        out, omap = gmsh.model.occ.fragment(objs, tools)
        gmsh.model.occ.synchronize()
        src_lists = [sorted(own1[t]) for t in sorted(own1)] + [[k] for k in tight for _ in in_tags[k]]
    owner, overl = {}, []
    for j, lst in enumerate(omap):
        for d, t in lst:
            if d != 2:
                continue
            for k in src_lists[j]:
                if t in owner and owner[t] != k:
                    a_old, a_new = faces[owner[t]]["area_mm2"], faces[k]["area_mm2"]
                    overl.append({"surf": t, "faces": [faces[owner[t]]["pn"], faces[k]["pn"]], "area_mm2": round(gmsh.model.occ.getMass(2, t), 4)})
                    if a_new < a_old:
                        owner[t] = k
                else:
                    owner.setdefault(t, k)
    surfs = [t for d, t in gmsh.model.getEntities(2)]
    # gas-side curves (insert contour and TC-03 diffuser) for refinement: curve midpoints on the nozzle contour or the diffuser cone
    c = np.array(info["contour"])
    o = np.argsort(c[:, 0])
    rz = lambda z: float(np.interp(z, c[o, 0], c[o, 1]))
    gas = []
    for d, cv in gmsh.model.getEntities(1):
        lo, hi = gmsh.model.getParametrizationBounds(1, cv)
        p = np.array(gmsh.model.getValue(1, cv, [0.5 * (lo[0] + hi[0])]))[:2]
        if info["exit"] - 0.5 <= p[1] <= info["insert_top"] + 0.5 and abs(p[0] - rz(p[1])) < 0.3:
            gas.append(cv)
        elif info["inj_face"] - 0.01 <= p[1] <= info["z_seat"] + 0.05 and p[0] < 7.4:
            gas.append(cv)
    fields = []
    for k, f in enumerate(faces):
        ss = [t for t in surfs if owner.get(t) == k]
        if not ss:
            continue
        fc = gmsh.model.mesh.field.add("Constant")
        gmsh.model.mesh.field.setNumbers(fc, "SurfacesList", ss)
        gmsh.model.mesh.field.setNumber(fc, "VIn", SIZE[f["pn"]] * level)
        gmsh.model.mesh.field.setNumber(fc, "VOut", 1e3)
        fields.append(fc)
    if gas:
        fd = gmsh.model.mesh.field.add("Distance")
        gmsh.model.mesh.field.setNumbers(fd, "CurvesList", gas)
        gmsh.model.mesh.field.setNumber(fd, "Sampling", 300)
        ft = gmsh.model.mesh.field.add("Threshold")
        gmsh.model.mesh.field.setNumber(ft, "InField", fd)
        gmsh.model.mesh.field.setNumber(ft, "SizeMin", SIZE_GAS * level)
        gmsh.model.mesh.field.setNumber(ft, "SizeMax", 50.0)
        gmsh.model.mesh.field.setNumber(ft, "DistMin", 0.0)
        gmsh.model.mesh.field.setNumber(ft, "DistMax", DIST_GAS * 50.0)
        fields.append(ft)
    seat_curves = []
    if CADV == "v352r4" and ENTRY_H and info.get("tc02_r4"):
        # rev 4 (lead 05:42Z: 'refine the new edges per 234 (4), not excluded'): size ENTRY_H on the seat curves of TC-02 / TC-03
        z1_, zt_ = info["z_fl1"], info["z_ins_top"]
        z_ue_ = z1_ + info["tc03_r4"]["thread_major_from_z_above_flange"]
        z_te_ = info["tc02_r4"]["thread_end_z_top"]
        sid = {t: faces[owner[t]]["pn"] for t in surfs if t in owner}
        for d_, cv in gmsh.model.getEntities(1):
            up, _ = gmsh.model.getAdjacencies(1, cv)
            if not any(sid.get(int(u)) in ("ENG-TC-02", "ENG-TC-03") for u in up):
                continue
            lo, hi = gmsh.model.getParametrizationBounds(1, cv)
            p = np.array(gmsh.model.getValue(1, cv, [0.5 * (lo[0] + hi[0])]))[:2]
            if (5.9 <= p[0] <= 7.8 and z1_ - 0.02 <= p[1] <= z_ue_ + 0.8) or (4.9 <= p[0] <= 7.4 and z_te_ - 0.8 <= p[1] <= zt_ + 0.02):
                seat_curves.append(cv)
        if seat_curves:
            fd2 = gmsh.model.mesh.field.add("Distance")
            gmsh.model.mesh.field.setNumbers(fd2, "CurvesList", seat_curves)
            gmsh.model.mesh.field.setNumber(fd2, "Sampling", 400)
            ft2 = gmsh.model.mesh.field.add("Threshold")
            gmsh.model.mesh.field.setNumber(ft2, "InField", fd2)
            gmsh.model.mesh.field.setNumber(ft2, "SizeMin", ENTRY_H)
            gmsh.model.mesh.field.setNumber(ft2, "SizeMax", 50.0)
            gmsh.model.mesh.field.setNumber(ft2, "DistMin", 0.2)
            gmsh.model.mesh.field.setNumber(ft2, "DistMax", 0.2 + (50.0 - ENTRY_H) / 0.5)
            fields.append(ft2)
    fm = gmsh.model.mesh.field.add("Min")
    gmsh.model.mesh.field.setNumbers(fm, "FieldsList", fields)
    gmsh.model.mesh.field.setAsBackgroundMesh(fm)
    for k_, v_ in (("Mesh.MeshSizeExtendFromBoundary", 0), ("Mesh.MeshSizeFromPoints", 0), ("Mesh.MeshSizeFromCurvature", 0),
                   ("Mesh.Algorithm", 6), ("Mesh.ElementOrder", 2), ("Mesh.SecondOrderLinear", 0), ("Mesh.HighOrderOptimize", 1)):
        gmsh.option.setNumber(k_, v_)
    t0 = time.time()
    gmsh.model.mesh.generate(2)
    tags, coords, _ = gmsh.model.mesh.getNodes()
    X = coords.reshape(-1, 3)[:, :2]
    idx = -np.ones(int(tags.max()) + 1, np.int64)
    idx[tags.astype(np.int64)] = np.arange(len(tags))
    E, PN, MT = [], [], []
    for t in surfs:
        et, _, en = gmsh.model.mesh.getElements(2, t)
        for typ, nn in zip(et, en):
            if typ != 9:
                continue
            cc = idx[np.array(nn, np.int64).reshape(-1, 6)]
            E.append(cc)
            k = owner.get(t, -1)
            PN += [faces[k]["pn"] if k >= 0 else "UNKNOWN"] * len(cc)
            MT += [faces[k]["material"] if k >= 0 else "UNKNOWN"] * len(cc)
    gmsh.finalize()
    E = np.vstack(E)
    used = np.unique(E)
    remap = -np.ones(len(X), np.int64)
    remap[used] = np.arange(len(used))
    X, E = X[used], remap[E]
    a = X[E[:, 1]] - X[E[:, 0]]
    b = X[E[:, 2]] - X[E[:, 0]]
    neg = (a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]) < 0
    E[neg] = E[neg][:, [0, 2, 1, 5, 4, 3]]
    return {"X": X, "E": E, "pn": np.array(PN), "mat": np.array(MT), "overlaps": overl, "n_gas_curves": len(gas),
            "t_mesh_s": round(time.time() - t0, 1), "level": level, "n_seat_curves_refined": len(seat_curves), "entry_h_mm": ENTRY_H,
            "fragment": ("two-stage: TOL_MM then TC-03 at TOL_TIGHT" if tight else "one-stage TOL_MM")}


# =============================================================================================== joints + duplication
def tie_rule(pa, pb, mid, info):
    """DOFs tied between parts pa, pb at an interface point mid = (r, z): '' (released), 'z' or 'rz'."""
    r, z = mid
    s = {pa, pb}
    if s == {"ENG-TC-01", "ENG-TC-02"}:
        return "z" if abs(z - info["bolt_z_fwd"]) <= 2.5 else ""
    if s == {"ENG-TC-01", "ENG-TC-09"}:
        if info["aft_land_top"] - 1e-3 <= z <= info["aft_thread_top"] + 1e-3:
            return "rz" if TIES == "bonded" else "z"
        return ""
    if s == {"ENG-TC-02", "ENG-TC-03"}:
        if R10 == "free" and r >= 9.95 and z < info["z_ins_top"] - 10.0 - 0.01:
            return ""
        return "rz" if TIES == "bonded" else "z"
    if s == {"ENG-TC-02", "ENG-TC-04"}:
        return "rz" if 14.0 <= r <= 19.0 else ""
    if s == {"ENG-TC-09", "ENG-NZ-04"}:
        return "z"
    if s == {"ENG-NZ-01", "ENG-NZ-02"}:
        return ""
    if s <= {"ENG-NZ-01", "ENG-NZ-02", "ENG-NZ-03", "ENG-NZ-04", "ENG-NZ-06"}:     # v352: NZ-06 foil in the tied stack
        if NZTIE == "normal":
            if s == {"ENG-NZ-02", "ENG-NZ-06"}:
                return ""
            q = sorted(s)
            return NZ_ORIENT.get((q[0], q[1], round(float(r), 4), round(float(z), 4)), "rz")
        return "rz"
    if "ENG-TC-09" in s and s & {"ENG-NZ-01", "ENG-NZ-02", "ENG-NZ-03", "ENG-NZ-06"}:
        return ""
    return "?"


def duplicate(m, info):
    """Give every part its own nodes.  Returns new X, E, origin map, interface pairs and the tie equations."""
    X, E, pn = m["X"], m["E"], m["pn"]
    owners = {}
    for e in range(len(E)):
        for n in E[e]:
            owners.setdefault(int(n), set()).add(pn[e])
    if NZTIE == "normal":
        NZ_ORIENT.clear()
        NZ_ORIENT.update(_nz_orient(owners, X))
    newid = {}
    Xn, orig = [], []
    for n in range(len(X)):
        for p in sorted(owners.get(n, ()), key=lambda q: PRIO[q]):
            newid[(n, p)] = len(Xn)
            Xn.append(X[n])
            orig.append(n)
    En = np.array([[newid[(int(n), pn[e])] for n in E[e]] for e in range(len(E))], np.int64)
    Xn = np.array(Xn)
    pairs, unknown = [], set()
    eqs = {1: [], 2: []}
    for n, ps in owners.items():
        if len(ps) < 2:
            continue
        ps = sorted(ps, key=lambda q: PRIO[q])
        for d, lab in ((1, "r"), (2, "z")):
            # union-find over the copies tied in this DOF
            parent = {p: p for p in ps}

            def f(p):
                while parent[p] != p:
                    p = parent[p]
                return p
            for i in range(len(ps)):
                for j in range(i + 1, len(ps)):
                    rule = tie_rule(ps[i], ps[j], X[n], info)
                    if rule == "?":
                        unknown.add(tuple(sorted((ps[i], ps[j]))))
                        rule = ""
                    if lab in rule:
                        a_, b_ = f(ps[i]), f(ps[j])
                        if a_ != b_:
                            parent[b_] = a_ if PRIO[a_] < PRIO[b_] else b_
                            if PRIO[a_] > PRIO[b_]:
                                parent[a_] = b_
            for p in ps:
                root = f(p)
                if root != p:
                    eqs[d].append((newid[(n, p)], newid[(n, root)]))
        for i in range(len(ps)):
            for j in range(i + 1, len(ps)):
                pairs.append((n, ps[i], ps[j], newid[(n, ps[i])], newid[(n, ps[j])], tie_rule(ps[i], ps[j], X[n], info)))
    return {"X": Xn, "E": En, "orig": np.array(orig), "pn": pn, "mat": m["mat"], "pairs": pairs, "eqs": eqs,
            "unknown_pairs": sorted(unknown)}


# =============================================================================================== boundary faces + pressure classes
def contour_r(info):
    c = np.array(info["contour"])
    o = np.argsort(c[:, 0])
    return lambda z: float(np.interp(z, c[o, 0], c[o, 1]))


def gas_profile(info):
    """p/Pc vs z (v3.4.1 frame) from Combustion thermal_bc_max_v2.csv (x_face from the injector face)."""
    rows = [r for r in csv.reader(l for l in open(COMB_BC) if not l.startswith("#"))]
    hdr = rows[0]
    ix, ip = hdr.index("x_face_m"), hdr.index("p_Pa")
    rows = [hdr] + [r for r in rows[1:] if len(r) > ip and r[ip].strip()]          # grain-port rows carry no gas state
    x = np.array([float(r[ix]) for r in rows[1:]])
    p = np.array([float(r[ip]) for r in rows[1:]])
    z = info["inj_face"] - 1e3 * x
    o = np.argsort(z)
    pc = p.max()
    return (lambda zz: float(np.interp(zz, z[o], p[o] / pc))), {"src": str(COMB_BC.name), "sha256_16": sha16(COMB_BC), "Pc_Pa": float(pc),
                                                                 "p_exit_over_Pc": float(p[-1] / pc)}


def classify(part, probe, info, rc):
    """Pressure region of a free face, from a probe point 0.05 mm outside it: 'PC' (chamber cavity), 'GAS' (nozzle gas path, p(z)),
    'PM' (N2O manifold), 'AMB'."""
    r, z = float(probe[0]), float(probe[1])
    g1, g2, gw = info["fwd_glands"]
    z_fwd_seal = g1 + gw                     # S01: lower gland of the head plug (the O-ring seals at its upper flank)
    zg0, gwa, gdia = info["aft_gland"]
    z_aft_seal = zg0 + gwa                   # S13: TC-09 gland on the case land (O-ring seals at its upper flank)
    z_lipseal = info["lip_top"] + info["nz_seal_t"]
    ht = info["head_top"]
    if part in ("ENG-TC-02", "ENG-TC-03", "ENG-TC-04"):
        if r < 5.3 and info["z_seat"] < z < info["bonnet_top"] - 9.0:
            return "PM"
        if info.get("tc02_r4") and part in ("ENG-TC-02", "ENG-TC-03"):
            # rev 4 (lead 06:23Z item 3): the seat-entry cavity (TC-03 undercut / TC-02 entry radius and bore, the free flange top inside
            # the S03 land) and the top gap / relief wedge are N2O at manifold pressure (connected through the thread clearance)
            z1_, zt_ = info["z_fl1"], info["z_ins_top"]
            z_ue_ = z1_ + info["tc03_r4"]["thread_major_from_z_above_flange"]
            z_te_ = info["tc02_r4"]["thread_end_z_top"]
            if 6.0 < r < 7.6 and z1_ - 0.06 < z < z_ue_ + 0.01:      # - 0.06: the probe of a TC-02 entry-radius face at the wedge
                return "PM"                                          # tip (r -> 7.5) lands in the TC-03 flange below z_fl1
            if 4.9 < r < 7.3 and z_te_ - 0.01 < z < zt_ + 0.06:
                return "PM"
        if abs(z - ht) < 1.4 and r < 7.25:
            return "PM"
        if part == "ENG-TC-03" and z <= info["z_seat"] and r < 10.5:
            return "PC"
        if part == "ENG-TC-02" and r < 28.6 and z < z_fwd_seal:
            return "PC"
        return "AMB"
    if part == "ENG-TC-01":
        if r < 28.6 and z < z_fwd_seal and z > info["tube_aft"] - 0.2:
            return "PC"
        if r < 30.6 and z_lipseal < z < z_aft_seal:
            return "PC"
        if 30.3 < r < gdia / 2 + 0.1 and zg0 - 0.1 < z < z_aft_seal + 0.1:
            return "PC"
        return "AMB"
    if part == "ENG-TC-09":
        r_in = 30.6 if z > info["aft_step"] + 0.01 else info["r_insert_bore"] + 0.05      # post-chamber bore / insert-holder bore
        if r < r_in and z_lipseal < z < z_aft_seal:
            return "PC"
        if 30.3 < r < gdia / 2 + 0.1 and zg0 - 0.1 < z < z_aft_seal + 0.1:
            return "PC"
        return "AMB"
    # nozzle stack
    if z < info["exit"] + 1e-3 and r < info["re"] + 0.5:
        return "AMB"
    if info["exit"] <= z <= info["insert_top"] + 0.3 and r <= rc(z) + 0.3:
        return "GAS"
    if part in ("ENG-NZ-03", "ENG-NZ-04", "ENG-NZ-06") and r < 16.0:
        return "AMB"
    if z < info["lip_top"] + 1e-3:
        return "AMB"
    if part == "ENG-NZ-01" and r < 15.6 and z < info["insert_shoulder"] + 0.05:
        return "AMB"                         # spigot in the lip bore (inside the J1 seal line)
    return "PC"


def boundary_faces(d, info):
    """Every part-boundary face (element edge used once within its part) that is not tied: [(elem, face, class, r, z, n, L)]."""
    X, E, pn = d["X"], d["E"], d["pn"]
    cnt = {}
    for e in range(len(E)):
        for f, (i, j, _) in EDGE.items():
            key = (min(E[e, i], E[e, j]), max(E[e, i], E[e, j]))
            cnt.setdefault(key, []).append((e, f))
    tied = set()
    for d_ in (1, 2):
        for a_, b_ in d["eqs"][d_]:
            tied.add(a_)
            tied.add(b_)
    rc = contour_r(info)
    out = []
    for key, lst in cnt.items():
        if len(lst) != 1:
            continue
        e, f = lst[0]
        i, j, k = EDGE[f]
        if E[e, i] in tied and E[e, j] in tied and E[e, k] in tied:
            continue
        p0, p1, pm = X[E[e, i]], X[E[e, j]], X[E[e, k]]
        t = p1 - p0
        L = float(np.linalg.norm(t))
        n = np.array([t[1], -t[0]]) / max(L, 1e-12)
        c = classify(pn[e], pm + 0.05 * n, info, rc)
        out.append((e, f, c, float(pm[0]), float(pm[1]), n, L))
    return out


# =============================================================================================== materials
def mat_cards(mat):
    """*MATERIAL block (mm, N, MPa, K, t/mm3)."""
    M = engmat.MATERIALS[mat]
    name = mat.replace("-", "_")
    s = [f"*MATERIAL, NAME={name}", "*DENSITY", f"{M['rho']['v'] * 1e-12:.6e}"]
    E = M["E"]
    nu = M["nu"]["v"]
    s.append("*ELASTIC")
    if "T_C" in E:
        for T, v in zip(E["T_C"], E["v"]):
            s.append(f"{v / 1e6:.6e}, {nu}, {T + 273.15:.2f}")
    else:
        s.append(f"{E['v'] / 1e6:.6e}, {nu}")
    al = M["alpha"]
    s.append(f"*EXPANSION, ZERO={T_REF}")
    if "T_C" in al:
        for T, v in zip(al["T_C"], al["v"]):
            s.append(f"{v:.6e}, {T + 273.15:.2f}")
    else:
        s.append(f"{al['v']:.6e}")
    return "\n".join(s) + "\n"


def allowables(mat, T_K):
    """(Fty, Ftu) in MPa at the node temperatures (metals), or (St, Sc) for brittle materials (None where not defined)."""
    TC = np.asarray(T_K) - 273.15
    M = engmat.MATERIALS[mat]
    def tab(key):
        if key is None or key not in M:
            return None
        d = M[key]
        if "T_C" in d:
            return np.interp(TC, d["T_C"], d["v"]) / 1e6
        return np.full(TC.shape, d["v"] / 1e6)
    if mat in BRITTLE:
        kt, kc = BRITTLE[mat]
        return tab(kt), tab(kc)
    return tab("Fty"), tab("Ftu")


# =============================================================================================== thermal fields
def thermal_mesh(run_dir):
    z = np.load(run_dir / "envelope_nodes.npz", allow_pickle=True)
    return z["X"], z["E"], z["pn"]


def extract_frames(run_dir, times, cache_name="frames.npz"):
    """Temperature frames (K) nearest to the requested times from the thermal .frd (single pass, cached)."""
    cache = run_dir / cache_name
    key = ",".join(f"{t:.4f}" for t in times)
    if cache.exists():
        z = np.load(cache, allow_pickle=True)
        if str(z["key"]) == key:
            return {float(t): (float(ta), T) for t, ta, T in zip(z["t_req"], z["t_act"], z["T"])}
    # v3.5.2 (2026-10-20, Mechanical): the thermal chain gzips the .frd after its post-processing -> read the .frd.gz when no .frd is left
    frds = sorted(run_dir.glob("*.frd"))
    if frds:
        _open = lambda: open(frds[0])
    else:
        import gzip
        _gz = next(run_dir.glob("*.frd.gz"))
        _open = lambda: gzip.open(_gz, "rt")
    all_t, keep = [], {}
    best = {t: (1e9, None, None) for t in times}
    with _open() as fh:
        t, inblk, vals = None, False, None
        for line in fh:
            if line.startswith("  100CL"):
                t = float(line[12:24])
                inblk = False
                continue
            if line.startswith(" -4  NDTEMP"):
                inblk = True
                vals = []
                continue
            if inblk:
                if line.startswith(" -1"):
                    vals.append(line[3:25])
                elif line.startswith(" -3"):
                    inblk = False
                    all_t.append(t)
                    for tr in times:
                        if abs(t - tr) < best[tr][0]:
                            ids = np.array([int(v[:10]) for v in vals])
                            T = np.array([float(v[10:22]) for v in vals])
                            arr = np.full(ids.max(), np.nan)
                            arr[ids - 1] = T
                            best[tr] = (abs(t - tr), t, arr)
    tr_ = list(times)
    np.savez_compressed(cache, key=key, t_req=np.array(tr_), t_act=np.array([best[t][1] for t in tr_]),
                        T=np.array([best[t][2] for t in tr_]), all_t=np.array(all_t))
    return {t: (best[t][1], best[t][2]) for t in tr_}


def map_temperature(Xs, Xt, Et, Tt, dz):
    """Interpolate a thermal field (nodes Xt (thermal frame), CAX6 Et, values Tt) at structural nodes Xs (v3.4.1 frame, z_th = z + dz).
    Each tri6 is split into 4 linear sub-triangles (keeps the quadratic resolution); points outside -> nearest node OF THESE ELEMENTS.
    Called per part by map_temperature_parts (rev B run 2)."""
    import matplotlib.tri as mtri
    from scipy.spatial import cKDTree
    used = np.unique(Et)
    rm = -np.ones(len(Xt), np.int64)
    rm[used] = np.arange(len(used))
    sub = rm[np.vstack([Et[:, [0, 3, 5]], Et[:, [3, 1, 4]], Et[:, [5, 4, 2]], Et[:, [3, 4, 5]]])]
    Xu, Tu = Xt[used], Tt[used]
    tri = mtri.Triangulation(Xu[:, 0], Xu[:, 1], sub)
    P = np.column_stack([Xs[:, 0], Xs[:, 1] + dz])
    v = mtri.LinearTriInterpolator(tri, Tu)(P[:, 0], P[:, 1])
    v = np.asarray(v.filled(np.nan) if hasattr(v, "filled") else v, float)
    miss = ~np.isfinite(v)
    if miss.any():
        kd = cKDTree(Xu)
        dd, ii = kd.query(P[miss])
        v[miss] = Tu[ii]
        return v, int(miss.sum()), float(dd.max())
    return v, 0, 0.0


def map_temperature_parts(Xs, node_part, Xt, Et, pnt, Tt, dz):
    """Part-aware mapping (rev B run 2): every structural part takes its temperature only from the thermal elements of the same part.
    Run 1 interpolated over the whole thermal mesh: structural nodes that fall outside it took the nearest node of ANY part (TC-09 lip
    bore at the exit plane took the NZ-01 graphite temperature, 1693 C), and TC-02 nodes cut at 90 deg fell inside TC-03 thermal
    elements cut at 214 deg (head next to the insert flange took the IN718 temperature)."""
    T = np.full(len(Xs), np.nan)
    stats = {}
    for p in PARTS:
        idx = np.nonzero(node_part == p)[0]
        Ep = Et[pnt == p]
        if not len(Ep):
            raise RuntimeError(f"thermal mesh has no elements of {p}")
        v, nmiss, dmax = map_temperature(Xs[idx], Xt, Ep, Tt, dz)
        T[idx] = v
        stats[p] = {"nodes": int(len(idx)), "outside_part_thermal_mesh": nmiss, "max_nearest_distance_mm": round(dmax, 4)}
    if not np.isfinite(T).all():
        raise RuntimeError("unmapped structural nodes")
    return T, stats


# =============================================================================================== deck
def write_deck(path, d, faces_b, info, T_nodes, gp, plug, title):
    """5-step linear deck (see module doc)."""
    X, E, pn, mat = d["X"], d["E"], d["pn"], d["mat"]
    lines = [f"*HEADING\n{title}\n", "*NODE, NSET=NALL\n"]
    lines += [f"{i + 1}, {x[0]:.6f}, {x[1]:.6f}\n" for i, x in enumerate(X)]
    for m_ in MAT_MECH:
        idx = np.nonzero(mat == m_)[0]
        if not len(idx):
            continue
        lines.append(f"*ELEMENT, TYPE=CAX6, ELSET=M_{m_.replace('-', '_')}\n")
        lines += [f"{e + 1}, " + ", ".join(str(int(n) + 1) for n in E[e]) + "\n" for e in idx]
    for p in PARTS:
        idx = np.nonzero(pn == p)[0]
        lines.append(f"*ELSET, ELSET=P_{p.replace('ENG-', '').replace('-', '_')}\n")
        lines += [", ".join(str(int(e) + 1) for e in idx[k:k + 12]) + "\n" for k in range(0, len(idx), 12)]
    sup = support_nodes(d, info)
    lines.append("*NSET, NSET=NSUP\n")
    lines += [", ".join(str(int(n) + 1) for n in sup[k:k + 12]) + "\n" for k in range(0, len(sup), 12)]
    # rev B run 2: the thermal step is supported statically determinately (u_z = 0 at ONE node of the groove bottom, mid-plane); the
    # mechanical steps fix the whole groove band at its thermal displacement (*BOUNDARY, FIXED): the collar reacts the mechanical loads
    # over the band but does not restrain the thermal growth of the case (run 1 fixed u_z = 0 on the 20 mm band in every step, which
    # restrained the axial thermal expansion of the band: ~E alpha dT, up to ~200 MPa at the groove in the soak states).
    sup0 = support_node0(d, info, sup)
    lines.append(f"*NSET, NSET=NSUP0\n{sup0 + 1}\n")
    for m_ in MAT_MECH:
        if (mat == m_).any():
            lines.append(mat_cards(m_))
            lines.append(f"*SOLID SECTION, ELSET=M_{m_.replace('-', '_')}, MATERIAL={m_.replace('-', '_')}\n")
    neq = 0
    for dof in (1, 2):
        for a_, b_ in d["eqs"][dof]:
            lines.append(f"*EQUATION\n2\n{a_ + 1}, {dof}, 1., {b_ + 1}, {dof}, -1.\n")
            neq += 1
    lines.append("*BOUNDARY\nNSUP0, 2, 2\n")
    lines.append(f"*INITIAL CONDITIONS, TYPE=TEMPERATURE\nNALL, {T_REF}\n")
    fixed = "*BOUNDARY, FIXED\nNSUP, 2, 2\n"
    out_req = "*NODE FILE\nU\n*EL FILE\nS\n*NODE PRINT, NSET=NSUP, TOTALS=ONLY\nRF\n"
    # step 1: thermal
    lines.append("*STEP\n*STATIC\n*TEMPERATURE\n")
    lines += [f"{i + 1}, {T:.3f}\n" for i, T in enumerate(T_nodes)]
    lines.append(out_req + "*END STEP\n")
    # pressure lists
    def dl(kind):
        s = []
        for (e, f, c, r, z, n, L) in faces_b:
            if kind == "OP":
                v = 1.0 if c == "PC" else (gp(z) if c == "GAS" else 0.0)
            elif kind == "BL":
                v = 1.0 if c == "PC" else ((1.0 if z >= info["throat"] else 0.0) if c == "GAS" else 0.0)
                v += plug.get((e, f), 0.0)
            else:
                v = 1.0 if c == "PM" else 0.0
            if v != 0.0:
                s.append(f"{e + 1}, P{f}, {v:.6f}\n")
        return s
    for kind in ("OP", "BL", "PM"):
        lines.append("*STEP\n*STATIC\n" + fixed + "*DLOAD, OP=NEW\n")
        lines += dl(kind)
        lines.append(out_req + "*END STEP\n")
    lines.append("*STEP\n*STATIC\n" + fixed + "*DLOAD, OP=NEW\n")
    for m_ in MAT_MECH:
        if (mat == m_).any():
            lines.append(f"M_{m_.replace('-', '_')}, GRAV, {G}, 0., -1., 0.\n")
    lines.append(out_req + "*END STEP\n")
    Path(path).write_text("".join(lines))
    return {"n_equations": neq, "n_support_nodes": int(len(sup)), "support_thermal_step_node": sup0 + 1,
            "support": "thermal step: u_z = 0 at one groove node (determinate); mechanical steps: *BOUNDARY, FIXED on the groove band",
            "ties": TIES}


def support_nodes(d, info):
    X, E, pn = d["X"], d["E"], d["pn"]
    rg, z0, z1 = info["collar_groove"]
    nodes = np.unique(E[pn == "ENG-TC-01"])
    sel = nodes[(np.abs(X[nodes, 0] - rg) < 0.02) & (X[nodes, 1] >= z0 - 1e-3) & (X[nodes, 1] <= z1 + 1e-3)]
    return sel


def support_node0(d, info, sup=None):
    """The single groove-bottom node (closest to the groove mid-plane) that supports the thermal step (rev B run 2)."""
    sup = support_nodes(d, info) if sup is None else sup
    zm = 0.5 * (info["collar_groove"][1] + info["collar_groove"][2])
    return int(sup[np.argmin(np.abs(d["X"][sup, 1] - zm))])


def plug_band(faces_b, info, X, E, band=2.0):
    """Blocked-nozzle plug load P pi r_t^2 as an extra normal pressure on the convergent within `band` mm of radius above the throat."""
    rt = info["rt"]
    sel, A = [], 0.0
    for (e, f, c, r, z, n, L) in faces_b:
        if c == "GAS" and z >= info["throat"] and r <= rt + band:
            i, j, _ = EDGE[f]
            p0, p1 = X[E[e, i]], X[E[e, j]]
            A += abs(math.pi * (p1[0] ** 2 - p0[0] ** 2))     # projected (axial) area of the ring
            sel.append((e, f))
    q = math.pi * rt ** 2 / A if A > 0 else 0.0
    return {k: q for k in sel}, {"band_mm": band, "projected_area_mm2": A, "q_extra_over_P": q}


# =============================================================================================== run + results
def run_ccx(inp, threads=1, timeout=3 * 3600):
    env = dict(os.environ, OMP_NUM_THREADS=str(threads), CCX_NPROC_EQUATION_SOLVER=str(threads))
    t0 = time.time()
    r = subprocess.run(["ccx", "-i", inp.stem], cwd=str(inp.parent), env=env, capture_output=True, text=True, timeout=timeout)
    (inp.parent / f"{inp.stem}.log").write_text(r.stdout[-100000:] + "\n" + r.stderr)
    err = [l for l in r.stdout.splitlines() if "*ERROR" in l]
    warn = [l for l in r.stdout.splitlines() if "*WARNING" in l]
    return {"seconds": round(time.time() - t0, 1), "errors": err[:5], "warnings": warn[:5], "returncode": r.returncode}


def read_frd(frd, n_nodes):
    """[{'U': (N,3), 'S': (N,6)}] per step from a static ccx .frd (ASCII)."""
    steps, cur, blk, vals = [], {}, None, []
    with open(frd) as fh:
        for line in fh:
            if line.startswith(" -4  "):
                blk = line[5:13].strip()
                if blk not in ("DISP", "STRESS"):          # skip ERROR (STR(%) estimator) and any other block
                    blk = None
                vals = []
                continue
            if blk is None:
                continue
            if line.startswith(" -5"):
                continue
            if line.startswith(" -1"):
                vals.append(line)
                continue
            if line.startswith(" -3"):
                ncomp = 3 if blk == "DISP" else 6
                arr = np.zeros((n_nodes, ncomp))
                for l in vals:
                    nid = int(l[3:13])
                    arr[nid - 1] = [float(l[13 + 12 * k:25 + 12 * k]) for k in range(ncomp)]
                if blk == "DISP":
                    cur = {"U": arr}
                elif blk == "STRESS":
                    cur["S"] = arr
                    steps.append(cur)
                blk = None
    return steps


def read_rf(dat):
    """Total reaction forces per step (2 deg segment) from *NODE PRINT TOTALS=ONLY."""
    out, grab = [], False
    for line in open(dat):
        if "total force" in line:
            grab = True
            continue
        if grab and line.strip():
            out.append([float(v) for v in line.split()[:3]])
            grab = False
    return np.array(out)


def vm(S):
    sxx, syy, szz, sxy = S[..., 0], S[..., 1], S[..., 2], S[..., 3]
    return np.sqrt(0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2) + 3.0 * sxy ** 2)


def principal(S):
    """(s_max, s_min) of the axisymmetric tensor (rr, zz, tt, rz)."""
    sxx, syy, szz, sxy = S[..., 0], S[..., 1], S[..., 2], S[..., 3]
    c, rr = 0.5 * (sxx + syy), np.sqrt((0.5 * (sxx - syy)) ** 2 + sxy ** 2)
    p1, p2 = c + rr, c - rr
    return np.maximum(np.maximum(p1, p2), szz), np.minimum(np.minimum(p1, p2), szz)


def singular_points(d, info):
    """Stress singularities of the linear model: re-entrant corners of every part boundary (right turn > 10 deg on the CCW boundary)
    and the ends of tied runs (a tied boundary node next to an untied boundary node of the same part).  Returns (K,2) points (mm)."""
    X, E, pn = d["X"], d["E"], d["pn"]
    tied = set()
    for dof in (1, 2):
        for a_, b_ in d["eqs"][dof]:
            tied.add(int(a_))
            tied.add(int(b_))
    pts = []
    for p in PARTS:
        idx = np.nonzero(pn == p)[0]
        cnt = {}
        for e in idx:
            for f, (i, j, k) in EDGE.items():
                key = (min(E[e, i], E[e, j]), max(E[e, i], E[e, j]))
                cnt.setdefault(key, []).append((e, i, j))
        nb = {}
        for key, lst in cnt.items():
            if len(lst) == 1:
                e, i, j = lst[0]
                a_, b_ = int(E[e, i]), int(E[e, j])
                nb.setdefault(a_, [None, None])[1] = b_
                nb.setdefault(b_, [None, None])[0] = a_
        for n, (pa, pb) in nb.items():
            if pa is None or pb is None:
                continue
            u, w = X[n] - X[pa], X[pb] - X[n]
            ang = math.degrees(math.atan2(u[0] * w[1] - u[1] * w[0], u @ w))
            if ang < -10.0:
                pts.append(X[n])
            elif n in tied and ((pa not in tied) or (pb not in tied)):
                pts.append(X[n])
    return np.array(pts) if pts else np.zeros((0, 2))


# =============================================================================================== thermal states
# v1 rev B: thermal runs of the TC-09 rev B geometry (v13 tag; the v12 runs had the rev A TC-09 and are superseded)
THERMAL = {"B1": THERMAL_RUNS / f"DC-B1v3p99_tg711_hi_SS316L_L2.5_{THERMAL_TAG}",
           "A1": THERMAL_RUNS / f"DC-A1dispp99_tg711_hi_SS316L_L2.5_{THERMAL_TAG}"}
B1_BURN = [0.5, 1.0, 2.0, 4.0, 8.0, 12.0, 16.0, 19.0, 21.65]      # s; B1 burn 0.001-21.651 (thermal meta)
B1_SOAK = [36.7, 71.7, 86.7, 186.7]                                # s; part maxima of the soak (TC-01, TC-09, NZ-04, TC-04; envelope.json, rev B)
if THERMAL_TAG.startswith("v351"):                                 # v3.5.1 thermal runs (TB1 + GlidCop): own part-maximum instants of the soak
    B1_SOAK = [37.7, 68.7, 86.7, 191.7]                            # TC-01 178.1 C, TC-09 729.9 C, NZ-04 733.0 C, TC-04 118.2 C (B1 v351_TB1GC log)
if THERMAL_TAG.startswith("v352"):                                 # v3.5.2: soak instants = the part-maximum instants of its own B1 run
    try:                                                           # (TC-01, TC-09, NZ-04, TC-04 as v351), read from the run's envelope.json
        _env = json.loads((THERMAL_RUNS / f"DC-B1v3p99_tg711_hi_SS316L_L2.5_{THERMAL_TAG}" / "envelope.json").read_text())["parts"]
        B1_SOAK = sorted({round(float(_env[pn]["t_max_s"]), 1) for pn in ("ENG-TC-01", "ENG-TC-09", "ENG-NZ-04", "ENG-TC-04")
                          if float(_env[pn]["t_max_s"]) > 21.7})
    except Exception as _e:                                        # noqa: BLE001  (thermal run not finished: keep the v351 instants)
        B1_SOAK = [37.7, 68.7, 86.7, 191.7]
A1_T = [22.2, 26.78]                                               # s; A1 relight (burn 2 starts 22.211) and end of burn 2
T_CASE_ABORT = 448.15                                              # K; case over-temperature abort (lead) for the stand cases
# (b) package item 2 (lead 05:42Z: 'the abort search with S-AX TB structural solves is fine'): SAX_TB_ABORTS="160,150,..." (C) adds the
# states TB_a<C> = the TB surrogate with the case maximum at that abort temperature instead of 448.15 K
TB_ABORTS_C = [float(x) for x in os.environ.get("SAX_TB_ABORTS", "").split(",") if x.strip()]


def states_all():
    st = {"RT": None}
    for t in B1_BURN + B1_SOAK:
        st[f"B1_{t:g}"] = ("B1", t)
    for t in A1_T:
        st[f"A1_{t:g}"] = ("A1", t)
    st["TB"] = ("B1", 21.65, "case_to_abort")
    for a_ in TB_ABORTS_C:
        st[f"TB_a{a_:g}"] = ("B1", 21.65, "case_to_abort", a_ + 273.15)
    return st


def thermal_dz(run_dir, info):
    meta = json.loads(next(run_dir.glob("*_meta.json")).read_text())
    return float(meta["case"]["monitors"]["head_top_r12"][1]) - info["head_top"]


def state_temperature(name, d, info):
    """Nodal temperature (K) of the structural mesh for a thermal state, with provenance."""
    st = states_all()[name]
    X = d["X"]
    if st is None:
        return np.full(len(X), T_REF), {"state": name, "source": "uniform 20 C (stress-free)"}
    run, t = st[0], st[1]
    rd = THERMAL[run]
    times = (B1_BURN + B1_SOAK) if run == "B1" else A1_T
    fr = extract_frames(rd, times)
    t_act, Tt = fr[min(fr, key=lambda q: abs(q - t))]
    Xt, Et, pnt = thermal_mesh(rd)
    dz = thermal_dz(rd, info)
    node_part, _ = node_maps(d)
    T, stats = map_temperature_parts(X, node_part, Xt, Et, pnt, Tt[:len(Xt)], dz)
    prov = {"state": name, "thermal_run": rd.name, "t_req_s": t, "t_frame_s": t_act, "dz_frame_mm": round(dz, 4),
            "mapping": "part-aware (rev B run 2): each part from its own thermal elements, nearest own-part node outside",
            "nodes_outside_own_part_thermal_mesh": int(sum(s["outside_part_thermal_mesh"] for s in stats.values())),
            "max_nearest_distance_mm": max(s["max_nearest_distance_mm"] for s in stats.values()), "per_part": stats}
    if len(st) > 2 and st[2] == "case_to_abort":
        case = np.unique(d["E"][d["pn"] == "ENG-TC-01"])
        shift = (st[3] if len(st) > 3 else T_CASE_ABORT) - float(T[case].max())
        T = T + shift
        prov["shift_K"] = round(shift, 3)
        prov["note"] = (f"ASSUMED stand surrogate: B1 end-of-burn field shifted uniformly so that the case maximum equals the "
                        f"{(st[3] if len(st) > 3 else T_CASE_ABORT):.2f} K abort limit (longer stand burn); no stand thermal FE exists")
    return T, prov


# =============================================================================================== solve one state
def _load_mesh_file(mf):
    z = np.load(mf, allow_pickle=True)
    d = {k: z[k] for k in ("X", "E", "orig", "pn", "mat")}
    d["eqs"] = {1: [tuple(x) for x in z["eq1"]], 2: [tuple(x) for x in z["eq2"]]}
    d["pairs"] = [tuple(x) for x in z["pairs"].tolist()]
    return d, json.loads(str(z["meta"]))


def get_mesh(level, faces=None, info=None):
    """Mesh of this level for the current tie variant.  A variant re-uses the conforming mesh of another variant of the same level
    (same gmsh mesh; only the tie equations change) instead of re-meshing."""
    if info is None:
        faces, info = geometry()
    wd = run_dir(level)
    wd.mkdir(parents=True, exist_ok=True)
    mf = wd / "mesh.npz"
    if mf.exists():
        d, meta_m = _load_mesh_file(mf)
        return _matov_mesh(d), meta_m
    src = [p for p in sorted(RUNS.glob(f"L{level:g}*/mesh.npz")) + sorted(RUNS.glob(f"revB_run1_evidence/L{level:g}/mesh.npz")) if p != mf]
    # v3.5.1 fix (2026-10-13, Mechanical successor): re-use only a conforming mesh of the SAME CAD version.  The first v3.5.1 run
    # (16:33Z) re-used runs/structural/L1/mesh.npz, i.e. the v3.4.1 rev B section (TC-03 IN718 flange, TC-09 316L) under the v3.5.1
    # thermal states: superseded (run directory and results renamed *_SUPERSEDED_v341mesh).
    src = [p for p in src if (p.parent.name.endswith(CADTAG) if CADTAG else not any(p.parent.name.endswith(t) for t in ("_cad351", "_cad352")))
           and ("_cad352r4" in p.parent.name) == (CADV == "v352r4")]
    if src:
        d0, meta0 = _load_mesh_file(src[0])
        Xc = np.zeros((int(d0["orig"].max()) + 1, 2))
        Xc[d0["orig"]] = d0["X"]
        m = {"X": Xc, "E": d0["orig"][d0["E"]], "pn": d0["pn"], "mat": d0["mat"]}
        d = duplicate(m, info)
        if not np.allclose(d["X"], d0["X"]) or not np.array_equal(d["E"], d0["E"]):
            raise RuntimeError(f"re-duplication of {src[0]} changed the node numbering")
        meta_m = dict(meta0, unknown_pairs=d["unknown_pairs"], conforming_mesh_from=str(src[0]))
    else:
        m = mesh(faces, info, level=level, workdir=wd / "brep")
        d = duplicate(m, info)
        meta_m = {"level": level, "nodes_conforming": int(len(m["X"])), "nodes": int(len(d["X"])), "elements": int(len(d["E"])),
                  "t_mesh_s": m["t_mesh_s"], "overlaps": m["overlaps"], "unknown_pairs": d["unknown_pairs"],
                  "elements_per_part": {p: int((d["pn"] == p).sum()) for p in PARTS}}
        for k_ in ("n_seat_curves_refined", "entry_h_mm", "fragment", "n_gas_curves"):
            meta_m[k_] = m.get(k_)
    meta_m["ties"] = TIES
    meta_m["cad"] = CADV
    d = _matov_mesh(d)
    if MATOV:
        meta_m["material_overrides_screening"] = dict(MATOV)
    meta_m["n_eq_r"], meta_m["n_eq_z"] = len(d["eqs"][1]), len(d["eqs"][2])
    np.savez_compressed(mf, X=d["X"], E=d["E"], orig=d["orig"], pn=d["pn"], mat=d["mat"],
                        eq1=np.array(d["eqs"][1], dtype=np.int64).reshape(-1, 2), eq2=np.array(d["eqs"][2], dtype=np.int64).reshape(-1, 2),
                        pairs=np.array(d["pairs"], dtype=object), meta=json.dumps(meta_m))
    return d, meta_m


def _load_res(path):
    """res.npz -> dict of arrays (float32-stored fields cast to float64, so the post runs in float64 either way) + parsed meta.
    v352r4 output shrink (lead 07:18Z): SAX_RES_F32=1 stores the fields as float32 (checked on the first state that the margin tables
    are unchanged to the reported digits, chain 9); a trimmed state (sax.py trim) keeps res_sub.npz (sub-model region only) instead."""
    z = np.load(path, allow_pickle=True)
    out = {k: (z[k].astype(np.float64) if z[k].dtype == np.float32 else z[k]) for k in z.files if k != "meta"}
    out["meta"] = json.loads(str(z["meta"]))
    return out


def load_res_any(level, st):
    """full fields of a state: res.npz, or the trimmed res_sub.npz expanded to the full node count with NaN outside its region."""
    rd = run_dir(level) / st
    if (rd / "res.npz").exists():
        return _load_res(rd / "res.npz")
    r = _load_res(rd / "res_sub.npz")
    nodes, n_all = r.pop("nodes"), int(r["meta"]["trim"]["n_nodes_full"])
    for k in list(r):
        if k != "meta" and isinstance(r[k], np.ndarray) and r[k].shape[:1] == nodes.shape:
            full = np.full((n_all,) + r[k].shape[1:], np.nan)
            full[nodes] = r[k]
            r[k] = full
    return r


def _guard_before_ccx(tag):
    """lead caps (06:05Z / 07:18Z): no new ccx below the disk floor (SAX_DISK_FLOOR_MB) and at most 2 ccx machine-wide: wait for a
    slot (up to SAX_CCX_WAIT_S), never route around the floor (exit 3 = HOLD)."""
    floor = float(os.environ.get("SAX_DISK_FLOOR_MB", "0"))
    free_mb = shutil.disk_usage("/home/claude").free / 2 ** 20
    if floor and free_mb < floor:
        print(f"HOLD before {tag}: disk {free_mb:.0f} MB free < floor {floor:.0f} MB", flush=True)
        sys.exit(3)
    t0, wmax = time.time(), float(os.environ.get("SAX_CCX_WAIT_S", "1800"))
    while True:
        n = subprocess.run(["pgrep", "-x", "ccx"], capture_output=True, text=True).stdout.split()
        if len(n) < 2:
            return free_mb
        if time.time() - t0 > wmax:
            print(f"HOLD before {tag}: {len(n)} ccx running for {wmax:.0f} s", flush=True)
            sys.exit(3)
        time.sleep(15)


def solve_state(level, name, threads=1, force=False):
    faces, info = geometry()
    wd = run_dir(level)
    d, meta_m = get_mesh(level, faces, info)
    out = wd / name
    res = out / "res.npz"
    if res.exists() and not force:
        return res
    out.mkdir(parents=True, exist_ok=True)
    T, prov = state_temperature(name, d, info)
    fb = boundary_faces(d, info)
    gp, gmeta = gas_profile(info)
    plug, pmeta = plug_band(fb, info, d["X"], d["E"])
    job = out / "sax.inp"
    dk = write_deck(job, d, fb, info, T, gp, plug, f"S-AX {VERSION} L{level:g} state {name} (CAD v3.4.1 J1)")
    r = run_ccx(job, threads=threads)
    if r["errors"] or r["returncode"] != 0:
        (out / "run.json").write_text(json.dumps({"run": r, "deck": dk}, indent=1))
        raise RuntimeError(f"ccx failed {name}: {r}")
    steps = read_frd(out / "sax.frd", len(d["X"]))
    rf = read_rf(out / "sax.dat")
    if len(steps) != 5:
        raise RuntimeError(f"{name}: {len(steps)} steps in frd")
    U = np.array([s["U"] for s in steps])
    S = np.array([s["S"] for s in steps])
    # pressure-integral check: axial force of each unit load on the structure (full ring) vs the support reaction x 180
    F_ax = {}
    for k, kind in ((1, "OP"), (2, "BL"), (3, "PM")):
        f = 0.0
        for (e, fc, c, rr, zz, n, L) in fb:
            if kind == "OP":
                v = 1.0 if c == "PC" else (gp(zz) if c == "GAS" else 0.0)
            elif kind == "BL":
                v = (1.0 if c == "PC" else ((1.0 if zz >= info["throat"] else 0.0) if c == "GAS" else 0.0)) + plug.get((e, fc), 0.0)
            else:
                v = 1.0 if c == "PM" else 0.0
            f += -v * n[1] * 2 * math.pi * rr * L          # pressure pushes along -n (into the solid)
        F_ax[kind] = f
    meta = {"state": name, "level": level, "prov": prov, "run": r, "deck": dk, "gas_profile": gmeta, "plug": pmeta, "mesh": meta_m,
            "F_axial_pressure_integral_N": F_ax, "RF_2deg_per_step": rf.tolist(),
            "RF_check": {k: {"pressure_integral_N": F_ax[k], "support_reaction_x180_N": float((rf[i, 1] - rf[0, 1]) * 180.0)}
                         for i, k in ((1, "OP"), (2, "BL"), (3, "PM"))},
            "RF_gravity_1g_x180_N": float((rf[4, 1] - rf[0, 1]) * 180.0),
            "pressure_faces": {c: int(sum(1 for q in fb if q[2] == c)) for c in ("PC", "GAS", "PM", "AMB")}}
    f32 = os.environ.get("SAX_RES_F32", "0") == "1"      # v352r4 output shrink (lead 07:18Z); differences taken in float64, then cast
    dt_ = np.float32 if f32 else np.float64
    meta["res_dtype"] = "float32" if f32 else "float64"
    fl = {"T": T, "U1": U[0], "S1": S[0], "U_OP": U[1] - U[0], "S_OP": S[1] - S[0], "U_BL": U[2] - U[0], "S_BL": S[2] - S[0],
          "U_PM": U[3] - U[0], "S_PM": S[3] - S[0], "U_G": U[4] - U[0], "S_G": S[4] - S[0]}
    np.savez_compressed(res, **{k: np.asarray(v, dtype=np.float64).astype(dt_) for k, v in fl.items()}, meta=json.dumps(meta, default=float))
    for f_ in ("sax.frd", "sax.12d"):   # raw ccx output (~57 MB/state at L1): the five unit responses are in res.npz, sax.inp is kept
        (out / f_).unlink(missing_ok=True)
    if os.environ.get("SAX_DECK_GZ", "0") == "1":       # v352r4: the deck is kept gzipped (lead 07:18Z 'keep gzipping the decks')
        with open(job, "rb") as fi, gzip.open(str(job) + ".gz", "wb", compresslevel=6) as fo:
            shutil.copyfileobj(fi, fo)
        job.unlink()
    (out / "run.json").write_text(json.dumps(meta, indent=1, default=float))
    return res


def load_mesh(level):
    d, meta_m = _load_mesh_file(run_dir(level) / "mesh.npz")
    return _matov_mesh(d), meta_m


# =============================================================================================== load cases (loadcases v2, S-AX part)
# v3.5.1: lead CHANGELOG 188 (9) (REV-MECH-1 RM1-10) safety factors.  Nominal operating states (LC1-LC4, LC6, TS1, TS2, SEGP, TB70) ENG-10
# 1.5 / 2.0; abnormal / failure states (LC2F, BN, TBS) 1.0 / 1.5; FA-1 keeps its own rule (SF 1.0 yield and ultimate at the lead 194 period-domain
# pressure).  Applied when SAX_CAD=v351 (the v3.5 runs keep the factors they were reported with).
SF_RULE_188 = {"LC1": (1.5, 2.0), "LC2": (1.5, 2.0), "LC4": (1.5, 2.0), "LC6": (1.5, 2.0), "TS1a": (1.5, 2.0), "TS1b": (1.5, 2.0),
               "TS2": (1.5, 2.0), "SEGP": (1.5, 2.0), "TB70": (1.5, 2.0), "BN": (1.0, 1.5), "TBS": (1.0, 1.5)}


def combos(info):
    c = _combos(info)
    if CADV not in ("v351", "v352", "v352r4"):
        return c
    out = []
    for (cid, title, states, coef, sfy, sfu, note) in c:
        if cid in SF_RULE_188:
            sfy, sfu = SF_RULE_188[cid]
            note = f"SF {sfy} yield / {sfu} ultimate at the node temperature (lead 188 (9)); " + note
        out.append((cid, title, states, coef, sfy, sfu, note))
    return out


def _combos(info):
    """[(id, title, states, coefficients {OP, BL, PM, G} in MPa / g, SF_y, SF_u, criterion note)]"""
    p = info["params"]
    Pc, meop, pbn, proof, ptank = p["Pc_max"] / 1e6, p["MEOP_chamber"] / 1e6, p["P_blocked_nozzle"] / 1e6, \
        p["proof_factor"] * p["MEOP_chamber"] / 1e6, p["MEOP_tank"] / 1e6
    burn = [f"B1_{t:g}" for t in B1_BURN]
    g_fl = 35.8 / 9.80665          # peak axial specific force in flight (B1 dispersed max, ICD-AIRFRAME / gnc duty cycles v3)
    return [
        ("LC1", "Max thrust Pc 25.0 bar + manifold 70 bar + 3.65 g axial, B1 transient (9 instants)", burn,
         {"OP": Pc, "PM": ptank, "G": g_fl}, 1.5, 2.0, "SF 1.5 yield / 2.0 ultimate at the node temperature (ENG-09/10)"),
        ("LC2", "Chamber MEOP 45 bar + manifold 70 bar + 3.65 g, B1 transient (also covers LC2F 907.7 N for the pressure structure)", burn,
         {"OP": meop, "PM": ptank, "G": g_fl}, 1.5, 2.0, "SF 1.5 / 2.0 at temperature"),
        ("BN", "Blocked nozzle 63.08 bar (P pi r_bore^2 on the lip) + manifold 70 bar, B1 transient", burn,
         {"BL": pbn, "PM": ptank}, 1.0, None, "no yield at temperature (lead 2026-10-12); ultimate reported"),
        ("LC4", "Hydrostatic proof 67.5 bar chamber (blanked exit) + 105 bar manifold, 20 C", ["RT"],
         {"BL": proof, "PM": 1.5 * ptank}, 1.0, None, "no yield at proof (20 C)"),
        ("TS1a", "A1 relight after the coast: thermal at relight / end of burn 2 + Pc 25 bar + manifold 70 bar", [f"A1_{t:g}" for t in A1_T],
         {"OP": Pc, "PM": ptank, "G": 27.7 / 9.80665}, 1.5, 2.0, "SF 1.5 / 2.0 at temperature"),
        ("TS1b", "A1 relight, MEOP failure case: Pc 45 bar + manifold 70 bar", [f"A1_{t:g}" for t in A1_T],
         {"OP": meop, "PM": ptank, "G": 27.7 / 9.80665}, 1.5, 2.0, "SF 1.5 / 2.0 at temperature"),
        ("TS2", "Post-landing soak peaks, unloaded (thermal stress only)", [f"B1_{t:g}" for t in B1_SOAK],
         {}, 1.0, None, "no yield at temperature; 6061 over-ageing judged separately (time at temperature)"),
        ("SEGP", "SEG-P: manifold 99.75 bar (secondary disc 9.5 MPa + 5 %), trapped segment heated: 20 C, soak peaks, A1 relight",
         ["RT"] + [f"B1_{t:g}" for t in B1_SOAK] + [f"A1_{A1_T[0]:g}"], {"PM": 9.975}, 1.0, None, "no yield at Fty(T) (lead SEG-P)"),
        # S6 is a THROAT BLOCK: the blocked distribution (Pc to the throat + plug) is applied to both stand cases (bounds a partial block)
        ("TB70", "LC-TB70 stand transient 58.1 bar abs (S6 throat block, blocked distribution, DLF from the modal check) + manifold 70 bar, "
                 "case at the 448.15 K abort", ["TB"] + [f"TB_a{a_:g}" for a_ in TB_ABORTS_C],
         {"BL": 5.81, "PM": ptank}, 1.0, None, "no yield at Fty(T), no leak (Mechanical relay-2)"),
        ("TBS", "LC-TB-S stand static 63.1 bar abs (blocked) + manifold 70 bar, case at the 448.15 K abort", ["TB"] + [f"TB_a{a_:g}" for a_ in TB_ABORTS_C],
         {"BL": 6.31, "PM": ptank}, 1.0, None, "no yield at Fty(T), no leak"),
        ("LC6", "Touchdown 10 g axial (inertia toward the nozzle), unpressurised, post-burn soak states (lateral 3 g in S-3D)",
         [f"B1_{t:g}" for t in B1_SOAK[:2]], {"G": 10.0}, 1.5, 2.0, "SF 1.5 / 2.0 at temperature"),
        ("FA1", f"FMEA FA-1 relight fuel-assisted fast part: head-end {FA1['P_head_abs_bar']:.1f} bar abs (<= 3 ms) x DLF {fa1_dlf_value():.3f} "
                "on the operating distribution (vacuum outside), manifold 70 bar, A1 relight thermal state", [f"A1_{A1_T[0]:g}"],
         {"OP": FA1["P_head_abs_bar"] / 10.0 * fa1_dlf_value(), "PM": ptank}, 1.0, 1.0,
         "failure case: yield (Fty(T), SF 1.0) and burst (Ftu(T), SF 1.0) reported; a negative value is reported as a failure"),
        ("FA1S", f"FA-1 sensitivity, step bound: head-end {FA1['P_head_abs_bar']:.1f} bar abs x DLF 2.0 (rise time -> 0), manifold 70 bar, "
                 "A1 relight thermal state", [f"A1_{A1_T[0]:g}"],
         {"OP": FA1["P_head_abs_bar"] / 10.0 * 2.0, "PM": ptank}, 1.0, 1.0,
         "failure case (bound): yield (Fty(T), SF 1.0) and burst (Ftu(T), SF 1.0); a negative value is reported as a failure"),
        # FA-1 INTERIM (lead CHANGELOG line 172 (2), REV-COMB-2 R2-03): 76-88 bar at tf 1 ms, aft 96-97 % of head -> quasi-static
        # 90 bar abs (ENG-09 ultimate design point) at head AND aft until Combustion's O/F 4-12 x tf 1-7 ms envelope lands; the shell
        # breathing period (~0.04 ms) is << the rise time, so the peak governs (DLF 1.0 for the pressure parts)
        ("FA1Q", f"FA-1 INTERIM (lead 172 (2)): quasi-static {FA1Q_BAR:.0f} bar abs at head and aft (operating distribution: uniform chamber, "
                 "nozzle profile; vacuum outside), manifold 70 bar, A1 relight thermal state", [f"A1_{A1_T[0]:g}"],
         {"OP": FA1Q_BAR / 10.0, "PM": ptank}, 1.0, 1.0,
         "failure case: yield (Fty(T), SF 1.0) and ultimate (Ftu(T), SF 1.0) reported per part; negative = failure, never a pass"),
        ("FA1QB", f"FA-1 INTERIM, blocked-distribution bound: {FA1Q_BAR:.0f} bar abs to the throat + plug (like-for-like re-check of the J1 lip "
                  "set at 63.1 bar in BN/TBS), manifold 70 bar, A1 relight thermal state", [f"A1_{A1_T[0]:g}"],
         {"BL": FA1Q_BAR / 10.0, "PM": ptank}, 1.0, 1.0,
         "failure case (bound): yield (Fty(T), SF 1.0) and ultimate (Ftu(T), SF 1.0); negative = failure, never a pass"),
        # FA-1 FINAL load rule (lead CHANGELOG 173, Combustion fa1_envelope_v2p4a 64b328150025fa1e): parts with natural periods of 0.25-1 ms
        # (S-AX modal: mode 1 TC-09 + nozzle stack 0.33-0.47 ms, mode 2 TC-02 head on its screws 0.27-0.38 ms) are also reported at 92 bar
        # (design: baseline with the DLF and +3 % fuel basis) and 102 bar (sensitivity: upper bracket); the shell (~0.05 ms) stays at FA1Q
        ("FA1D", f"FA-1 DESIGN for 0.25-1 ms parts (lead 173): {FA1D_BAR:.0f} bar abs at head and aft (operating distribution), manifold 70 bar, "
                 "A1 relight thermal state", [f"A1_{A1_T[0]:g}"],
         {"OP": FA1D_BAR / 10.0, "PM": ptank}, 1.0, 1.0,
         "failure case: yield (Fty(T), SF 1.0) and ultimate (Ftu(T), SF 1.0); applies to TC-02/TC-09/J1 lip/nozzle stack/closure fasteners"),
        ("FA1DB", f"FA-1 DESIGN, blocked-distribution bound: {FA1D_BAR:.0f} bar abs to the throat + plug (J1 lip like-for-like), manifold 70 bar, "
                  "A1 relight thermal state", [f"A1_{A1_T[0]:g}"],
         {"BL": FA1D_BAR / 10.0, "PM": ptank}, 1.0, 1.0, "failure case (bound): yield and ultimate, SF 1.0"),
        ("FA1U", f"FA-1 SENSITIVITY for 0.25-1 ms parts (lead 173, upper bracket): {FA1U_BAR:.0f} bar abs at head and aft (operating distribution), "
                 "manifold 70 bar, A1 relight thermal state", [f"A1_{A1_T[0]:g}"],
         {"OP": FA1U_BAR / 10.0, "PM": ptank}, 1.0, 1.0, "sensitivity: yield and ultimate, SF 1.0"),
        ("FA1UB", f"FA-1 SENSITIVITY, blocked-distribution bound: {FA1U_BAR:.0f} bar abs to the throat + plug, manifold 70 bar, A1 relight "
                  "thermal state", [f"A1_{A1_T[0]:g}"],
         {"BL": FA1U_BAR / 10.0, "PM": ptank}, 1.0, 1.0, "sensitivity (bound): yield and ultimate, SF 1.0"),
    ]


SCL = [  # (name, part, (r0, z0), (r1, z1)) with z given relative to stations: values are callables of info
    ("case_mid", "ENG-TC-01", lambda i: ((28.575, -60.0), (31.75, -60.0))),
    ("case_collar_groove", "ENG-TC-01", lambda i: ((28.575, 0.0), (i["collar_groove"][0], 0.0))),
    ("case_prechamber_hot", "ENG-TC-01", lambda i: ((28.575, i["inj_face"] - 17.1), (31.75, i["inj_face"] - 17.1))),
    ("case_fwd_gland", "ENG-TC-01", lambda i: ((28.575, i["fwd_glands"][0] + 0.5 * i["fwd_glands"][2]), (31.75, i["fwd_glands"][0] + 0.5 * i["fwd_glands"][2]))),
    ("case_screw_row", "ENG-TC-01", lambda i: ((28.575, i["bolt_z_fwd"]), (31.75, i["bolt_z_fwd"]))),
    ("case_thread", "ENG-TC-01", lambda i: ((28.575, 0.5 * (i["aft_land_top"] + i["aft_thread_top"])), (31.5, 0.5 * (i["aft_land_top"] + i["aft_thread_top"])))),
    ("case_aft_land", "ENG-TC-01", lambda i: ((28.575, i["aft_gland"][0] + 0.5 * i["aft_gland"][1]), (30.5, i["aft_gland"][0] + 0.5 * i["aft_gland"][1]))),
    ("tc09_socket", "ENG-TC-09", lambda i: ((31.5, 0.5 * (i["aft_land_top"] + i["aft_thread_top"])), (36.0, 0.5 * (i["aft_land_top"] + i["aft_thread_top"])))),
    ("tc09_gland_wall", "ENG-TC-09", lambda i: ((i["aft_gland"][2] / 2, i["aft_gland"][0] + 0.5 * i["aft_gland"][1]), (36.0, i["aft_gland"][0] + 0.5 * i["aft_gland"][1]))),
    ("tc09_barrel", "ENG-TC-09", lambda i: ((30.53, 0.5 * (i["tube_aft"] + i["aft_step"])), (33.03, 0.5 * (i["tube_aft"] + i["aft_step"])))),
    ("tc09_holder", "ENG-TC-09", lambda i: ((25.0, 0.5 * (i["aft_step"] + i["lip_top"])), (27.5, 0.5 * (i["aft_step"] + i["lip_top"])))),
    ("tc09_lip_root", "ENG-TC-09", lambda i: ((24.6, i["aft_bottom"]), (24.6, i["lip_top"]))),
    ("tc09_lip_mid", "ENG-TC-09", lambda i: ((20.0, i["aft_bottom"]), (20.0, i["lip_top"]))),
    ("head_r15", "ENG-TC-02", lambda i: ((15.0, i["inj_face"] + 2.0), (15.0, i["head_top"]))),
    ("head_r26_gland_land", "ENG-TC-02", lambda i: ((26.5, i["fwd_glands"][0] + i["fwd_glands"][2]), (26.5, i["fwd_glands"][1]))),
    ("head_bore_wall", "ENG-TC-02", lambda i: ((5.0, 0.5 * (i["z_ins_top"] + i["head_top"])), (28.575, 0.5 * (i["z_ins_top"] + i["head_top"])))),
    ("tc03_body", "ENG-TC-03", lambda i: ((2.75, 0.5 * (i["z_seat"] + i["z_ins_top"])), (6.45, 0.5 * (i["z_seat"] + i["z_ins_top"])))),
    ("bonnet_wall", "ENG-TC-04", lambda i: ((5.0, i["head_top"] + 12.0), (12.0, i["head_top"] + 12.0))),
]


# =============================================================================================== post-processing helpers
def node_maps(d):
    """Part and material of every node (nodes are per part after duplicate())."""
    X, E, pn, mat = d["X"], d["E"], d["pn"], d["mat"]
    node_part = np.empty(len(X), object)
    node_mat = np.empty(len(X), object)
    for p in PARTS:
        node_part[np.unique(E[pn == p])] = p
    for m_ in np.unique(mat):
        node_mat[np.unique(E[mat == m_])] = m_
    return node_part, node_mat


def boundary_edges(d):
    """Part-boundary edges (used once): int array rows (elem, face, n_i, n_j, n_mid)."""
    E = d["E"]
    M = len(E)
    A = np.vstack([np.column_stack([np.arange(M), np.full(M, f), E[:, i], E[:, j], E[:, k]]) for f, (i, j, k) in EDGE.items()])
    lo, hi = np.minimum(A[:, 2], A[:, 3]), np.maximum(A[:, 2], A[:, 3])
    key = lo.astype(np.int64) * (len(d["X"]) + 1) + hi
    _, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    return A[cnt[inv] == 1]


def boundary_normals(d):
    """Outward unit normal at every part-boundary node (mean of the adjacent boundary edges of its own part)."""
    X = d["X"]
    B = boundary_edges(d)
    t = X[B[:, 3]] - X[B[:, 2]]
    L = np.linalg.norm(t, axis=1)
    n = np.column_stack([t[:, 1], -t[:, 0]]) / np.maximum(L, 1e-12)[:, None]
    N = np.zeros((len(X), 2))
    for c in (2, 3, 4):
        np.add.at(N, B[:, c], n)
    nn = np.linalg.norm(N, axis=1)
    N[nn > 0] /= nn[nn > 0][:, None]
    return N


def line_weights(d, part, p0, p1, n=41):
    """Sparse interpolation matrix (n x N) on the linear sub-triangles of `part` at n points of p0 -> p1 (ends pulled 0.5 % inside)."""
    import matplotlib.tri as mtri
    from scipy.sparse import csr_matrix
    X = d["X"]
    E = d["E"][d["pn"] == part]
    sub = np.vstack([E[:, [0, 3, 5]], E[:, [3, 1, 4]], E[:, [5, 4, 2]], E[:, [3, 4, 5]]])
    used = np.unique(sub)
    rm = -np.ones(len(X), np.int64)
    rm[used] = np.arange(len(used))
    tri = mtri.Triangulation(X[used, 0], X[used, 1], rm[sub])
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    s = np.linspace(0.0, 1.0, n)
    P = p0 + s[:, None] * (p1 - p0)
    P[0] = p0 + 0.005 * (p1 - p0)
    P[-1] = p1 - 0.005 * (p1 - p0)
    it = tri.get_trifinder()(P[:, 0], P[:, 1])
    rows, cols, vals = [], [], []
    for q in np.nonzero(it >= 0)[0]:
        t3 = sub[it[q]]
        A = X[t3]
        T = np.array([[A[0, 0] - A[2, 0], A[1, 0] - A[2, 0]], [A[0, 1] - A[2, 1], A[1, 1] - A[2, 1]]])
        l1, l2 = np.linalg.solve(T, P[q] - A[2])
        rows += [q] * 3
        cols += [int(c) for c in t3]
        vals += [l1, l2, 1.0 - l1 - l2]
    W = csr_matrix((vals, (rows, cols)), shape=(n, len(X)))
    return {"W": W, "s": s, "ok": it >= 0, "L": float(np.linalg.norm(p1 - p0)), "P": P, "p0": p0.tolist(), "p1": p1.tolist()}


def _longest_run(ok):
    """Mask of the longest contiguous run of True (an SCL that crosses a void is linearised over its longest solid segment)."""
    best, cur, start, bs = 0, 0, 0, 0
    for i, v in enumerate(ok):
        if v:
            if cur == 0:
                start = i
            cur += 1
            if cur > best:
                best, bs = cur, start
        else:
            cur = 0
    m = np.zeros(len(ok), bool)
    m[bs:bs + best] = True
    return m


def linearise_w(lw, S, T):
    """Membrane / bending (ASME VIII-2 Annex 5-A, straight SCL, no radius correction) of the 4 axisymmetric components."""
    ok = _longest_run(lw["ok"])
    if ok.sum() < 5:
        return None
    v = (lw["W"] @ np.column_stack([S[:, :4], T]))[ok]
    xm = lw["s"][ok] * lw["L"]
    x0 = float(xm[0])
    xm = xm - xm[0]
    t = xm[-1]
    mem = np.trapezoid(v[:, :4], xm, axis=0) / t
    ben = 6.0 / t ** 2 * np.trapezoid(v[:, :4] * (t / 2 - xm)[:, None], xm, axis=0)
    ben[3] = 0.0                                                   # no bending of the shear component
    return {"valid_points": int(ok.sum()), "of_points": int(len(ok)), "segment_mm": [round(x0, 3), round(x0 + float(t), 3)],
            "T_max_K": float(v[:, 4].max()), "T_mean_K": float(v[:, 4].mean()),
            "Pm_vm": float(vm(mem)), "PmPb_vm": max(float(vm(mem + ben)), float(vm(mem - ben))),
            "peak_vm_on_line": float(np.max(vm(v[:, :4]))), "membrane": [round(float(x), 3) for x in mem],
            "bending": [round(float(x), 3) for x in ben]}


def line_force_z(lw, S):
    """Axial force (N, full ring) transmitted across the line: 2 pi int (s_rz n_r + s_zz n_z) r ds, n = unit normal of the line."""
    ok = _longest_run(lw["ok"])
    v = (lw["W"] @ S[:, [1, 3]])[ok]                                 # zz, rz
    P = lw["P"][ok]
    dvec = (np.array(lw["p1"]) - np.array(lw["p0"])) / lw["L"]
    nrm = np.array([dvec[1], -dvec[0]])
    tz = v[:, 1] * nrm[0] + v[:, 0] * nrm[1]
    return float(2.0 * math.pi * np.trapezoid(tz * P[:, 0], lw["s"][ok] * lw["L"]))


def interface_check(pairs, normals, U):
    """Released interfaces: change of the normal gap (mm) between the two copies of every interface node; the model gap is 0 (CAD gaps
    <= 0.10 mm closed), so a negative value is an interpenetration = a contact the linear model does not carry."""
    out = {}
    for (n, pa, pb, ia, ib, rule) in pairs:
        nr = normals[int(ia)]
        if not nr.any():
            continue
        lab = "r" if abs(nr[0]) >= abs(nr[1]) else "z"
        if lab in rule:
            continue
        g = float((U[int(ib), :2] - U[int(ia), :2]) @ nr)
        key = f"{pa}|{pb}|{lab}"
        o = out.setdefault(key, {"pair": [str(pa), str(pb)], "normal": lab, "tied_dofs": rule, "nodes": 0, "min_gap_change_mm": 1e9,
                                 "at_min": None, "max_gap_change_mm": -1e9, "at_max": None})
        o["nodes"] += 1
        if g < o["min_gap_change_mm"]:
            o["min_gap_change_mm"], o["at_min"] = g, int(ia)
        if g > o["max_gap_change_mm"]:
            o["max_gap_change_mm"], o["at_max"] = g, int(ia)
    return out


# =============================================================================================== evaluation
def evaluate(level, states=None, ex_r=1.0, cases=None):
    """All combos x states: nodal MS (regular nodes outside ex_r of singular points, and all nodes), primary-only MS, SCL margins
    (primary Pm / Pm+Pb, and P+Q against the 2 Fty shakedown limit), released-interface gaps, section forces, displacements."""
    from scipy.spatial import cKDTree
    faces, info = geometry()
    d, meta_m = load_mesh(level)
    X = d["X"]
    node_part, node_mat = node_maps(d)
    sp = singular_points(d, info)
    reg = cKDTree(sp).query(X)[0] > ex_r if len(sp) else np.ones(len(X), bool)
    normals = boundary_normals(d)
    LW = {nm: (part, line_weights(d, part, *f_(info))) for (nm, part, f_) in SCL}
    pairs = [(int(a), str(b), str(c), int(e), int(f), str(g)) for (a, b, c, e, f, g) in d["pairs"]]
    rd = run_dir(level)
    res_cache = {}

    def R(st):
        if st not in res_cache:
            res_cache[st] = _load_res(rd / st / "res.npz")
        return res_cache[st]

    rows, scl_rows, ifc_rows, disp_rows, rf_rows = [], [], [], [], {}
    for (cid, title, sts, co, sfy, sfu, crit) in combos(info):
        if cases and cid not in cases:
            continue
        for st in sts:
            if (states is not None and st not in states) or not (rd / st / "res.npz").exists():
                continue
            r = R(st)
            rf_rows[st] = r["meta"].get("RF_check")
            Sm = np.zeros_like(r["S1"])
            Um = np.zeros_like(r["U1"])
            for k, c in co.items():
                Sm += c * r[f"S_{k}"]
                Um += c * r[f"U_{k}"]
            S, U, T = r["S1"] + Sm, r["U1"] + Um, r["T"]
            v, vmech = vm(S), vm(Sm)
            s1, s3 = principal(S)
            s1m, s3m = principal(Sm)
            for p in PARTS:
                nodes = np.nonzero(node_part == p)[0]
                m_ = node_mat[nodes[0]]
                a1, a2 = allowables(m_, T[nodes])
                brittle = m_ in BRITTLE
                Tc = T[nodes] - 273.15
                M_ = engmat.MATERIALS[m_]
                T_char = M_["T_char_C"]["v"] if "T_char_C" in M_ else None
                T_lim = M_["T_max_C"]["v"] if "T_max_C" in M_ else None
                char = (Tc > T_char) if T_char is not None else np.zeros(len(nodes), bool)
                akey = "Fty" if not brittle else ("St" if "St" in M_ else "Sc")
                T_tab = (max(M_[akey]["T_C"]) if len(M_.get(akey, {}).get("T_C", [])) > 1 else None)   # single-point tables: RT value by design
                ms_pq = None
                if brittle:
                    sfu_b = sfu if sfu else 1.5          # flight cases 2.0 on strength, bound / failure / proof cases 1.5
                    big = np.full(len(nodes), np.inf)
                    ms_t = np.where(s1[nodes] > 0, a1 / (sfu_b * np.maximum(s1[nodes], 1e-9)) - 1.0, np.inf) if a1 is not None else big
                    ms_c = np.where(s3[nodes] < 0, a2 / (sfu_b * np.maximum(-s3[nodes], 1e-9)) - 1.0, np.inf) if a2 is not None else big
                    ms = np.minimum(ms_t, ms_c)
                    if char.any():
                        # char zone (T > T_char): the char is not a stress member: no thermal-stress criterion (char shrinkage and
                        # cracking are not modelled); PRIMARY (mechanical-only) compression vs Sc(T) = ASSUMED char band; no tension credit
                        ms_ch = np.where(s3m[nodes] < 0, a2 / (sfu_b * np.maximum(-s3m[nodes], 1e-9)) - 1.0, np.inf) if a2 is not None else big
                        ms = np.where(char, ms_ch, ms)
                    msu, msp = None, None
                    kind = (f"brittle: s1 vs St, s3 vs Sc (strength at temperature), SF {sfu_b:.1f}"
                            + (f"; char zone (T > {T_char:g} C): primary s3 vs Sc(T) (ASSUMED char strength)" if T_char is not None else ""))
                else:
                    ms = a1 / (sfy * np.maximum(v[nodes], 1e-9)) - 1.0
                    msu = (a2 / (sfu * np.maximum(v[nodes], 1e-9)) - 1.0) if sfu else None
                    msp = a1 / (sfy * np.maximum(vmech[nodes], 1e-9)) - 1.0
                    ms_pq = 2.0 * a1 / np.maximum(v[nodes], 1e-9) - 1.0
                    kind = f"von Mises (thermal + mechanical, elastic) vs Fty(T)/{sfy}" + (f", Ftu(T)/{sfu}" if sfu else "")
                for tag, msk in (("regular", reg[nodes]), ("all", np.ones(len(nodes), bool))):
                    if not msk.any():
                        continue
                    i = int(np.argmin(np.where(msk, ms, np.inf)))
                    n = nodes[i]
                    row = {"case": cid, "state": st, "part": p, "material": m_, "set": tag, "MS": float(ms[i]),
                           "role": PART_ROLE[p][0], "role_criterion": PART_ROLE[p][1],
                           "MS_ult": (float(np.min(np.where(msk, msu, np.inf))) if msu is not None else None),
                           "MS_primary_only": (float(np.min(np.where(msk, msp, np.inf))) if msp is not None else None),
                           "MS_PQ_nodal_shakedown": (float(np.min(np.where(msk, ms_pq, np.inf))) if ms_pq is not None else None),
                           "vm_MPa": float(v[n]), "vm_mech_MPa": float(vmech[n]), "vm_thermal_MPa": float(vm(r["S1"][n])),
                           "vm_max_MPa": float(np.max(v[nodes][msk])), "s1_max_MPa": float(np.max(s1[nodes][msk])),
                           "s3_min_MPa": float(np.min(s3[nodes][msk])),
                           "s1_MPa": float(s1[n]), "s3_MPa": float(s3[n]), "s3_mech_MPa": float(s3m[n]), "T_C": float(T[n] - 273.15),
                           "zone": ("char" if char[i] else ("virgin" if T_char is not None else "")),
                           "char_nodes_fraction": (round(float(char.mean()), 4) if T_char is not None else None),
                           "T_char_C": T_char, "T_limit_C": T_lim,
                           "T_limit_exceeded": (bool(Tc.max() > T_lim) if T_lim is not None else None),
                           "allowable_table_max_C": T_tab, "T_above_allowable_table": (bool(Tc[i] > T_tab) if T_tab is not None else None),
                           "allowable_MPa": _allow_at(brittle, a1, a2, i, s1[n], s3[n]),
                           "at_r_z_mm": [round(float(X[n, 0]), 3), round(float(X[n, 1]), 3)], "criterion": kind, "SF_y": sfy, "SF_u": sfu,
                           "T_part_max_C": float(T[nodes].max() - 273.15)}
                    row["status"] = margin_status(row)
                    rows.append(row)
            for nm, (part, lw) in LW.items():
                li_p, li_c = linearise_w(lw, Sm, T), linearise_w(lw, S, T)
                if li_p is None:
                    continue
                mat_p = info["materials"][part]
                fy, fu = allowables(mat_p, np.array([li_c["T_max_K"]]))
                scl_rows.append({"case": cid, "state": st, "scl": nm, "part": part, "material": mat_p, "p0": lw["p0"], "p1": lw["p1"],
                                 "valid_points": li_c["valid_points"], "T_max_C": li_c["T_max_K"] - 273.15, "Fty_MPa": float(fy[0]),
                                 "Ftu_MPa": float(fu[0]) if fu is not None else None, "SF_y": sfy, "SF_u": sfu,
                                 "P_Pm_vm": li_p["Pm_vm"], "P_PmPb_vm": li_p["PmPb_vm"], "PQ_PmPb_vm": li_c["PmPb_vm"],
                                 "peak_vm_on_line": li_c["peak_vm_on_line"],
                                 "MS_Pm_y": float(fy[0] / (sfy * max(li_p["Pm_vm"], 1e-9)) - 1.0),
                                 "MS_PmPb_y": float(fy[0] / (sfy * max(li_p["PmPb_vm"], 1e-9)) - 1.0),
                                 "MS_PmPb_u": (float(fu[0] / (sfu * max(li_p["PmPb_vm"], 1e-9)) - 1.0) if (sfu and fu is not None) else None),
                                 "MS_PQ_shakedown": float(2.0 * fy[0] / max(li_c["PmPb_vm"], 1e-9) - 1.0),
                                 "MS_combined_PmPb_y": float(fy[0] / (sfy * max(li_c["PmPb_vm"], 1e-9)) - 1.0),
                                 "Fz_section_N_mech": line_force_z(lw, Sm), "membrane_combined": li_c["membrane"],
                                 "bending_combined": li_c["bending"]})
            ifc = interface_check(pairs, normals, U)
            for k_, o in ifc.items():
                o.update({"case": cid, "state": st, "at_min_r_z_mm": [round(float(x), 3) for x in X[o["at_min"]]],
                          "at_max_r_z_mm": [round(float(x), 3) for x in X[o["at_max"]]]})
                ifc_rows.append(o)
            um = np.linalg.norm(U[:, :2], axis=1)
            disp_rows.append({"case": cid, "state": st, "max_abs_U_mm": {p: float(um[node_part == p].max()) for p in PARTS},
                              "uz_throat_mm": float(np.interp(info["throat"], *_axis_uz(d, node_part, U, "ENG-NZ-01"))),
                              "uz_head_top_mm": float(U[np.argmin(np.where(node_part == "ENG-TC-02",
                                                                          np.abs(X[:, 1] - info["head_top"]) + 1e-3 * X[:, 0], np.inf)), 1])})
    return {"rows": rows, "scl": scl_rows, "interfaces": ifc_rows, "displacements": disp_rows, "rf_checks": rf_rows,
            "singular_points": int(len(sp)), "ex_r_mm": ex_r, "mesh": meta_m, "level": level}


def margin_status(r):
    """Plain-language assessment of one margin row (lead 2026-10-13: no negative margin is presented as a pass)."""
    role, ms, z = r["role"], r["MS"], r.get("zone") or ""
    hot = " Part above its usable temperature limit (T_limit)." if r.get("T_limit_exceeded") else ""
    if r.get("T_above_allowable_table"):
        hot += f" Node above the end of the allowable table ({r['allowable_table_max_C']:g} C): value held, TO-VERIFY."
    if "BRITTLE" not in r["criterion"].upper():
        if ms >= 0:
            return "MS >= 0 (combined thermal + mechanical vs Fty(T)/SF)." + hot
        if (r.get("MS_primary_only") or 0.0) < 0:
            return "NEGATIVE PRIMARY margin on a load-bearing part: DESIGN CHANGE." + hot
        if (r.get("MS_PQ_nodal_shakedown") or 0.0) < 0:
            return ("P+Q above 2 Fty(T) (no elastic shakedown) on a load-bearing part: DESIGN CHANGE, or an elastic-plastic / low-cycle "
                    "fatigue analysis." + hot)
        return ("NEGATIVE on the combined (thermal + mechanical) / SF screening; primary >= 0 and P+Q <= 2 Fty(T): the excess is "
                "thermal (secondary) stress. NOT a pass: acceptance needs the lead's decision on the criterion for secondary stress." + hot)
    if ms >= 0:
        return ("MS >= 0 (" + ("char zone: primary bearing vs ASSUMED char strength" if z == "char" else "brittle, total stress") + ")." + hot)
    if role.startswith("SEAL"):
        return "NEGATIVE: seal stress above the ASSUMED maximum gasket stress: supplier data or DESIGN CHANGE." + hot
    if role.startswith("ABLATIVE"):
        if z == "char":
            return ("NEGATIVE in the char zone of a non-structural ablative layer (primary compression vs ASSUMED char strength): own "
                    "criterion = char depth + containment; char strength test required. Not a pass." + hot)
        return ("NEGATIVE in the virgin zone of the ablative sleeve (thermal stress vs ASSUMED strength): cracking risk of a non-load-bearing "
                "layer; own criterion = containment + char depth; not a pass." + hot)
    if z == "char":
        return ("NEGATIVE: primary bearing stress in the CHARRED zone of a load-bearing layer vs the ASSUMED char strength: DESIGN CHANGE "
                "or a char compressive-strength test at temperature." + hot)
    return "NEGATIVE on a load-bearing brittle part: DESIGN CHANGE or test-based acceptance (cracked-but-contained). Not a pass." + hot


def _allow_at(brittle, a1, a2, i, s1n, s3n):
    if not brittle:
        return float(a1[i])
    if a1 is not None and s1n > 0 and (a2 is None or s1n / float(a1[i]) >= -s3n / float(a2[i])):
        return float(a1[i])
    return float(a2[i]) if a2 is not None else None


def _axis_uz(d, node_part, U, part):
    """(z, u_z) of the part's nodes on its gas-side contour nearest to the axis, sorted by z (for the throat displacement)."""
    idx = np.nonzero(node_part == part)[0]
    X = d["X"][idx]
    zr = np.round(X[:, 1], 1)
    best = {}
    for k, (z, r) in enumerate(zip(zr, X[:, 0])):
        if z not in best or r < best[z][0]:
            best[z] = (r, k)
    zz = np.array(sorted(best))
    uz = np.array([U[idx[best[z][1]], 1] for z in zz])
    return zz, uz


def governing(ev):
    """Worst state per (case, part) on the regular set (and the all-node value at that state), worst per (case, SCL), worst gap."""
    gov = {}
    for r in ev["rows"]:
        if r["set"] != "regular":
            continue
        k = (r["case"], r["part"])
        if k not in gov or r["MS"] < gov[k]["MS"]:
            gov[k] = r
    allmin = {}
    for r in ev["rows"]:
        if r["set"] == "all":
            k = (r["case"], r["part"])
            if k not in allmin or r["MS"] < allmin[k]["MS"]:
                allmin[k] = r
    table = []
    for k in sorted(gov, key=lambda q: (q[0], PRIO[q[1]])):
        g = dict(gov[k])
        a = allmin.get(k)
        g["MS_all_nodes"] = a["MS"] if a else None
        g["MS_all_nodes_at"] = a["at_r_z_mm"] if a else None
        g["MS_all_nodes_state"] = a["state"] if a else None
        table.append(g)
    sg = {}
    for r in ev["scl"]:
        k = (r["case"], r["scl"])
        m = min(r["MS_PmPb_y"], r["MS_PQ_shakedown"])
        if k not in sg or m < sg[k][0]:
            sg[k] = (m, r)
    ig = {}
    for r in ev["interfaces"]:
        k = (r["case"], r["pair"][0], r["pair"][1], r["normal"])
        if k not in ig or r["min_gap_change_mm"] < ig[k]["min_gap_change_mm"]:
            ig[k] = r
    return table, [v[1] for k, v in sorted(sg.items())], [ig[k] for k in sorted(ig)]


MS_CAP = 99.0     # a margin above 99 means a stress ~ 0 in that criterion (e.g. primary-only in a soak state): CSV prints n/a (RM1-11)


def write_tables(ev, tag):
    """JSON (all rows) + CSV (governing margin table, MS columns capped at MS_CAP for display) in 04-fea/structural/results."""
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    table, scl, ifc = governing(ev)
    js = {"id": "sax_results", "version": VERSION, "tag": tag, "date": "2026-10-13", "owner": "mechanical", "script": "04-fea/structural/sax.py",
          "status": "SIM (linear elastic FE, axisymmetric) on LITERATURE / ASSUMED data; not physical validation",
          "materials": {"engmat_version": engmat.MATERIALS_VERSION, "matov": MATOV, "thermal_tag": THERMAL_TAG},
          "level": ev["level"], "mesh": ev["mesh"], "singular_points": ev["singular_points"], "exclusion_radius_mm": ev["ex_r_mm"],
          "rf_checks": ev["rf_checks"], "governing": table, "scl_governing": scl, "interfaces_governing": ifc,
          "displacements": ev["displacements"], "rows": ev["rows"], "scl_all": ev["scl"]}
    fj = out / f"sax_results_{tag}_{VERSION}.json"
    fj.write_text(json.dumps(js, indent=1, default=float))
    fc = out / f"sax_margin_table_{tag}_{VERSION}.csv"
    cols = ["case", "part", "role", "material", "state", "MS", "MS_ult", "MS_primary_only", "MS_PQ_nodal_shakedown", "MS_all_nodes",
            "status", "zone", "vm_MPa", "vm_mech_MPa", "vm_thermal_MPa", "s1_MPa", "s3_MPa", "s3_mech_MPa", "T_C", "T_part_max_C",
            "T_limit_C", "allowable_MPa", "SF_y", "SF_u", "at_r_z_mm", "MS_all_nodes_at", "criterion", "role_criterion"]
    with open(fc, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in table:
            # v3.5.1 (REV-MECH-1 RM1-11): a margin above MS_CAP means a stress ~ 0 in that criterion: printed 'n/a', not a capped value
            w.writerow([(("n/a" if r[c] > MS_CAP else round(r[c], 4)) if (isinstance(r.get(c), float) and c.startswith("MS")) else
                         (round(r[c], 4) if isinstance(r.get(c), float) else ("n/a" if (r.get(c) is None and c.startswith("MS")) else r.get(c))))
                        for c in cols])
    fs = out / f"sax_scl_table_{tag}_{VERSION}.csv"
    cols2 = ["case", "scl", "part", "material", "state", "T_max_C", "Fty_MPa", "SF_y", "P_Pm_vm", "P_PmPb_vm", "PQ_PmPb_vm", "MS_Pm_y",
             "MS_PmPb_y", "MS_PmPb_u", "MS_PQ_shakedown", "MS_combined_PmPb_y", "Fz_section_N_mech", "valid_points"]
    with open(fs, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols2)
        for r in scl:
            w.writerow([(("n/a" if (c.startswith("MS") and r[c] > MS_CAP) else round(r[c], 4)) if isinstance(r.get(c), float)
                         else ("n/a" if (r.get(c) is None and c.startswith("MS")) else r.get(c))) for c in cols2])
    return fj, fc, fs


# =============================================================================================== VTU + Ansys export
def combo_fields(level, cid, st):
    faces, info = geometry()
    cb = {c[0]: c for c in combos(info)}[cid]
    z = load_res_any(level, st)
    S, U = z["S1"].copy(), z["U1"].copy()
    for k, c in cb[3].items():
        S += c * z[f"S_{k}"]
        U += c * z[f"U_{k}"]
    return S, U, z["T"], cb


def export_vtu(level, picks, path):
    """One VTU (triangle6, x = r, y = z, mm) with point data per (case, state): T_C, U, S (rr, zz, tt, rz), von Mises, s1, s3, MS."""
    import meshio
    d, _ = load_mesh(level)
    node_part, node_mat = node_maps(d)
    pts = np.column_stack([d["X"], np.zeros(len(d["X"]))])
    pdata = {}
    for cid, st in picks:
        S, U, T, cb = combo_fields(level, cid, st)
        v = vm(S)
        s1, s3 = principal(S)
        ms = np.full(len(T), np.nan)
        for m_ in np.unique(node_mat.astype(str)):
            idx = np.nonzero(node_mat.astype(str) == m_)[0]
            a1, a2 = allowables(m_, T[idx])
            if m_ in BRITTLE:
                sf = cb[5] or 1.5
                mt = np.where(s1[idx] > 0, a1 / (sf * np.maximum(s1[idx], 1e-9)) - 1, np.inf) if a1 is not None else np.inf
                mc = np.where(s3[idx] < 0, a2 / (sf * np.maximum(-s3[idx], 1e-9)) - 1, np.inf) if a2 is not None else np.inf
                ms[idx] = np.minimum(mt, mc)
            else:
                ms[idx] = a1 / (cb[4] * np.maximum(v[idx], 1e-9)) - 1
        tg = f"{cid}_{st}"
        pdata[f"{tg}_T_C"] = (T - 273.15).astype(np.float32)
        pdata[f"{tg}_U_mm"] = np.column_stack([U[:, :2], np.zeros(len(U))]).astype(np.float32)
        pdata[f"{tg}_S_rr_zz_tt_rz_MPa"] = S[:, :4].astype(np.float32)
        pdata[f"{tg}_vonMises_MPa"] = v.astype(np.float32)
        pdata[f"{tg}_s1_MPa"] = s1.astype(np.float32)
        pdata[f"{tg}_s3_MPa"] = s3.astype(np.float32)
        pdata[f"{tg}_MS_clip"] = np.clip(ms, -1.0, 10.0).astype(np.float32)
    pid = np.array([PRIO[p] for p in d["pn"]], np.int32)
    m = meshio.Mesh(pts, [("triangle6", d["E"].astype(np.int64))], point_data=pdata, cell_data={"part_index": [pid]})
    meshio.write(str(path), m, file_format="vtu", binary=True, compression="zlib")
    return {"file": str(path), "picks": picks, "part_index": {p: i for i, p in enumerate(PARTS)}, "sha256_16": sha16(path)}


SEAL_GLANDS = {   # (pair parts, radial normal, gland z window from info, extrusion flank z, description)
    "S01": (("ENG-TC-02", "ENG-TC-01"), lambda i: (i["fwd_glands"][0], i["fwd_glands"][0] + i["fwd_glands"][2]),
            lambda i: i["fwd_glands"][0] + i["fwd_glands"][2], "head plug gland, lower (chamber seal): AS568-226 FKM 90A on the case bore 57.25"),
    "S02": (("ENG-TC-02", "ENG-TC-01"), lambda i: (i["fwd_glands"][1], i["fwd_glands"][1] + i["fwd_glands"][2]),
            lambda i: i["fwd_glands"][1] + i["fwd_glands"][2], "head plug gland, upper (back-up): AS568-226 FKM 90A on the case bore 57.25"),
    "S13": (("ENG-TC-01", "ENG-TC-09"), lambda i: (i["aft_gland"][0], i["aft_gland"][0] + i["aft_gland"][1]),
            lambda i: i["aft_gland"][0] + i["aft_gland"][1], "TC-09 rod gland on the case land 61.0: AS568-229 FFKM (lead 2026-10-13)"),
}


def seal_gaps(level, picks):
    """Radial opening (mm, + = the sealing surfaces move apart) of the released TC-01/TC-02 and TC-01/TC-09 interfaces over each gland
    (mean and max over the gland width) and at its extrusion flank (the flank the O-ring is pushed onto by the chamber pressure),
    for (case, state) picks.  The model gap is closed (CAD clearance <= 0.10 mm), so the value is the CHANGE of the gland gap."""
    faces, info = geometry()
    d, _ = load_mesh(level)
    X = d["X"]
    normals = boundary_normals(d)
    pairs = [(int(a), str(b), str(c), int(e), int(f), str(g)) for (a, b, c, e, f, g) in d["pairs"]]
    out = []
    for cid, st in picks:
        S, U, T, cb = combo_fields(level, cid, st)
        row = {"case": cid, "state": st, "seals": {}}
        for sid, ((pa, pb), win, flank, desc) in SEAL_GLANDS.items():
            z0, z1 = win(info)
            zf_ = flank(info)
            g_all, z_all = [], []
            for (n, a_, b_, ia, ib, rule) in pairs:
                if {a_, b_} != {pa, pb}:
                    continue
                nr = normals[ia]
                if not nr.any() or abs(nr[0]) < abs(nr[1]):
                    continue                                  # radial interfaces only
                z = X[ia, 1]
                if not (z0 - 0.3 <= z <= z1 + 0.3):
                    continue
                # opening = relative radial motion of the OUTER surface away from the INNER one
                outer, inner = (ib, ia) if nr[0] > 0 else (ia, ib)
                g_all.append(float(U[outer, 0] - U[inner, 0]))
                z_all.append(float(z))
            if not g_all:
                row["seals"][sid] = {"note": "no interface pairs found in the gland window"}
                continue
            g_all, z_all = np.array(g_all), np.array(z_all)
            kf = int(np.argmin(np.abs(z_all - zf_)))
            row["seals"][sid] = {"description": desc, "gland_z_mm": [round(z0, 3), round(z1, 3)], "flank_z_mm": round(zf_, 3),
                                 "n_pairs": int(len(g_all)), "opening_mean_mm": float(g_all.mean()), "opening_max_mm": float(g_all.max()),
                                 "opening_min_mm": float(g_all.min()), "opening_at_flank_mm": float(g_all[kf])}
        out.append(row)
    return out


def nodal_ms_map(d, node_part, node_mat, S, Sm, T, sfy, sfu):
    """Nodal MS with the criteria of evaluate(): metals Fty(T) / (SF_y vM) - 1 (combined); brittle s1 vs St, s3 vs Sc with SF_u
    (1.5 when the case has none); carbon-phenolic above T_char: primary (mechanical-only) s3 vs Sc(T)."""
    v = vm(S)
    s1, s3 = principal(S)
    _, s3m = principal(Sm)
    ms = np.full(len(T), np.nan)
    for p in PARTS:
        idx = np.nonzero(node_part == p)[0]
        m_ = node_mat[idx[0]]
        a1, a2 = allowables(m_, T[idx])
        if m_ in BRITTLE:
            sf = sfu or 1.5
            mt = np.where(s1[idx] > 0, a1 / (sf * np.maximum(s1[idx], 1e-9)) - 1, np.inf) if a1 is not None else np.full(len(idx), np.inf)
            mc = np.where(s3[idx] < 0, a2 / (sf * np.maximum(-s3[idx], 1e-9)) - 1, np.inf) if a2 is not None else np.full(len(idx), np.inf)
            mm = np.minimum(mt, mc)
            M_ = engmat.MATERIALS[m_]
            if "T_char_C" in M_ and a2 is not None:
                char = (T[idx] - 273.15) > M_["T_char_C"]["v"]
                mch = np.where(s3m[idx] < 0, a2 / (sf * np.maximum(-s3m[idx], 1e-9)) - 1, np.inf)
                mm = np.where(char, mch, mm)
            ms[idx] = mm
        else:
            ms[idx] = a1 / (sfy * np.maximum(v[idx], 1e-9)) - 1
    return ms


def export_png(level, picks, outdir, ex_r=1.0, results_tag=None):
    """PNG field plots of (case, state) picks: von Mises (combined), temperature, |U| on the deformed shape, nodal MS (criteria of the
    margin table), full section + aft and head zooms; the governing node of each part (regular set, margin table) is marked.
    Returns an index with the plotted ranges and the sha256 of each PNG."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.tri as mtri
    from matplotlib.colors import TwoSlopeNorm
    from scipy.spatial import cKDTree
    faces, info = geometry()
    d, _ = load_mesh(level)
    X, E = d["X"], d["E"]
    node_part, node_mat = node_maps(d)
    tri = np.vstack([E[:, [0, 3, 5]], E[:, [3, 1, 4]], E[:, [5, 4, 2]], E[:, [3, 4, 5]]])
    sp = singular_points(d, info)
    reg = cKDTree(sp).query(X)[0] > ex_r if len(sp) else np.ones(len(X), bool)
    tag = results_tag or run_dir(level).name
    jr = HERE / "results" / f"sax_results_{tag}_{VERSION}.json"
    rows = json.loads(jr.read_text())["rows"] if jr.exists() else []
    bnd = {}
    for e in range(len(E)):
        for f, (i, j, _) in EDGE.items():
            key = (min(E[e, i], E[e, j]), max(E[e, i], E[e, j]))
            bnd[key] = bnd.get(key, 0) + 1
    outline = np.array([k for k, c in bnd.items() if c == 1])
    zmin, zmax, rmax = X[:, 1].min(), X[:, 1].max(), X[:, 0].max()
    ZOOMS = {"aft (TC-09 / nozzle stack)": (-246.0, -196.0, 0.0, 37.0), "head (TC-02 / TC-03)": (96.0, 136.0, 0.0, 33.0)}
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    index = []
    for cid, st in picks:
        S, U, T, cb = combo_fields(level, cid, st)
        z_ = load_res_any(level, st)
        Sm = S - z_["S1"]
        v = vm(S)
        Tc = T - 273.15
        um = np.linalg.norm(U[:, :2], axis=1)
        ms = nodal_ms_map(d, node_part, node_mat, S, Sm, T, cb[4], cb[5])
        k_raw = 0.04 * (zmax - zmin) / max(um.max(), 1e-9)
        dec = 10 ** math.floor(math.log10(k_raw))
        k_def = float(dec * (5 if k_raw / dec >= 5 else (2 if k_raw / dec >= 2 else 1)))
        Xd = X + k_def * U[:, :2]
        gov = {}
        for r in rows:
            if r["case"] == cid and r["state"] == st and r["set"] == "regular":
                gov[r["part"]] = r
        vmax = float(np.max(v[reg]))
        fields = [("von Mises, thermal + mechanical (MPa)", v, "viridis", (0.0, vmax), False),
                  ("temperature (C)", Tc, "inferno", (float(Tc.min()), float(Tc.max())), False),
                  (f"|U| (mm) on the deformed shape x{k_def:g}", um, "cividis", (0.0, float(um.max())), True),
                  ("MS (criteria of the margin table; red < 0)", np.clip(ms, -1.0, 3.0), "RdYlBu", (-1.0, 3.0), False)]
        fig = plt.figure(figsize=(17, 29))
        gs = fig.add_gridspec(5, 2, height_ratios=[0.42, 1, 1, 1, 1], hspace=0.22, wspace=0.10, left=0.05, right=0.97,
                              top=0.975, bottom=0.04)
        ax0 = fig.add_subplot(gs[0, :])
        t0 = mtri.Triangulation(X[:, 1], X[:, 0], tri)
        h0 = ax0.tripcolor(t0, v, shading="gouraud", cmap="viridis", vmin=0.0, vmax=vmax)
        for (zl, zh, rl, rh) in ZOOMS.values():
            ax0.add_patch(plt.Rectangle((zl, rl), zh - zl, rh - rl, fill=False, ec="red", lw=1.2))
        ax0.set_aspect("equal")
        ax0.set_xlim(zmin - 2, zmax + 2)
        ax0.set_ylim(0, rmax + 2)
        ax0.set_xlabel("z (mm, engine frame, +Z forward)")
        ax0.set_ylabel("r (mm)")
        ax0.set_title(f"S-AX {VERSION} L{level:g} [{tag}]  {cid} @ {st}: von Mises full section (scale = max over regular nodes "
                      f"{vmax:.0f} MPa); red boxes = zooms below", fontsize=10)
        fig.colorbar(h0, ax=ax0, fraction=0.015, pad=0.01)
        rng = {}
        for row_i, (lab, f, cmap, (lo, hi), deformed) in enumerate(fields):
            for col, (zn, (zl, zh, rl, rh)) in enumerate(ZOOMS.items()):
                ax = fig.add_subplot(gs[row_i + 1, col])
                P_ = Xd if deformed else X
                tt = mtri.Triangulation(P_[:, 1], P_[:, 0], tri)
                if cmap == "RdYlBu":
                    h = ax.tripcolor(tt, f, shading="gouraud", cmap=cmap, norm=TwoSlopeNorm(vmin=lo, vcenter=0.0, vmax=hi))
                    try:
                        ax.tricontour(tt, f, levels=[0.0], colors="k", linewidths=0.8)
                    except Exception:
                        pass
                else:
                    if not deformed:          # von Mises and temperature: colour range of the zoom window (regular nodes)
                        w_ = (X[:, 1] >= zl) & (X[:, 1] <= zh) & (X[:, 0] <= rh) & reg
                        lo, hi = (float(f[w_].min()), float(f[w_].max())) if w_.any() else (lo, hi)
                    h = ax.tripcolor(tt, f, shading="gouraud", cmap=cmap, vmin=lo, vmax=hi)
                if deformed and len(outline):
                    for a_, b_ in outline:
                        if zl - 5 <= X[a_, 1] <= zh + 5:
                            ax.plot(X[[a_, b_], 1], X[[a_, b_], 0], color="0.6", lw=0.4)
                if len(sp):
                    sel = (sp[:, 1] >= zl) & (sp[:, 1] <= zh) & (sp[:, 0] <= rh)
                    ax.plot(sp[sel, 1], sp[sel, 0], ".", ms=2.5, color="k", alpha=0.6)
                k_lab = 0
                for p, r in sorted(gov.items(), key=lambda q: (q[1]["at_r_z_mm"][0], q[1]["at_r_z_mm"][1])):
                    rz = r["at_r_z_mm"]
                    if zl <= rz[1] <= zh and rl <= rz[0] <= rh:
                        ax.plot(rz[1], rz[0], "x", color="magenta", ms=9, mew=2)
                        ax.annotate(f"{p.replace('ENG-', '')} MS {r['MS']:.2f}", (rz[1], rz[0]),
                                    xytext=(8 + 70 * (k_lab % 2), -26 + 13 * k_lab), textcoords="offset points", fontsize=8, color="magenta",
                                    weight="bold", arrowprops=dict(arrowstyle="-", color="magenta", lw=0.6),
                                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))
                        k_lab += 1
                ax.set_xlim(zl, zh)
                ax.set_ylim(rl, rh)
                ax.set_aspect("equal")
                ax.set_title(f"{zn}: {lab}", fontsize=9)
                ax.tick_params(labelsize=7)
                fig.colorbar(h, ax=ax, fraction=0.03, pad=0.01)
                inwin = (X[:, 1] >= zl) & (X[:, 1] <= zh) & (X[:, 0] <= rh)
                fw = f[inwin & reg]
                rng[f"{zn}|{lab}"] = [float(np.nanmin(fw)), float(np.nanmax(fw))] if len(fw) else None
        import textwrap
        fig.text(0.05, 0.012, "\n".join(textwrap.wrap(
            "Linear elastic axisymmetric FE (ccx 2.21 CAX6) on LITERATURE / ASSUMED data: SIM, not physical validation. Black dots: singular "
            "points (re-entrant corners, tie ends; 1.0 mm exclusion in the margin table). Magenta x: governing regular node per part (margin "
            f"table, case {cid}: SF_y {cb[4]}, SF_u {cb[5]}). Thermal state from the 2-D thermal FE (upper-bound heat transfer). "
            f"Coefficients (MPa or g): {cb[3]}.", 190)), fontsize=8.5, va="bottom")
        out = outdir / f"sax_{cid}_{st}_{tag}_{VERSION}.png"
        fig.savefig(out, dpi=110)
        plt.close(fig)
        index.append({"case": cid, "state": st, "file": out.name, "sha256_16": sha16(out), "deformation_scale": k_def,
                      "vm_max_regular_MPa": vmax, "T_range_C": [float(Tc.min()), float(Tc.max())], "U_max_mm": float(um.max()),
                      "ms_min_regular": float(np.nanmin(ms[reg])), "ranges_regular_in_zoom": rng,
                      "governing_regular": {p: {"MS": r["MS"], "at_r_z_mm": r["at_r_z_mm"]} for p, r in gov.items()},
                      "coefficients": cb[3], "SF_y": cb[4], "SF_u": cb[5]})
    return index


def export_ansys(level, cid, st, path):
    """APDL input for Ansys Mechanical APDL (PLANE183 6-node triangle, axisymmetric): mesh, temperature-dependent materials, ties as
    coupled sets, support, nodal temperatures, pressures (face by selected nodes), axial acceleration.  Same units as the ccx model."""
    faces, info = geometry()
    d, meta_m = load_mesh(level)
    X, E, pn, mat = d["X"], d["E"], d["pn"], d["mat"]
    z = load_res_any(level, st)
    meta = z["meta"]
    T = z["T"]
    cb = {c[0]: c for c in combos(info)}[cid]
    co = cb[3]
    fb = boundary_faces(d, info)
    gp, _ = gas_profile(info)
    plug, pmeta = plug_band(fb, info, X, E)
    F_mid = 0.0                         # midpoint-rule axial pressure integral of the ccx run (for comparison)
    for k, c in co.items():
        if k in ("OP", "BL", "PM"):
            F_mid += c * meta["F_axial_pressure_integral_N"][k]
    mass_t = 0.0
    for m_ in MAT_MECH:
        idx = np.nonzero(mat == m_)[0]
        if not len(idx):
            continue
        rho = engmat.MATERIALS[m_]["rho"]["v"] * 1e-12
        P = X[E[idx][:, :3]]
        A = 0.5 * np.abs((P[:, 1, 0] - P[:, 0, 0]) * (P[:, 2, 1] - P[:, 0, 1]) - (P[:, 2, 0] - P[:, 0, 0]) * (P[:, 1, 1] - P[:, 0, 1]))
        rc = P[:, :, 0].mean(axis=1)
        mass_t += float((rho * 2 * math.pi * rc * A).sum())
    F_body = -co.get("G", 0.0) * G * mass_t
    L = ["! ARGOS hopper engine - S-AX %s Ansys APDL export (Mechanical, 2026-10-13); generated by 04-fea/structural/sax.py" % VERSION,
         f"! Case {cid}: {cb[1]}",
         f"! Thermal state {st}: {json.dumps(meta['prov'])}",
         f"! Load coefficients (MPa, or g for ACEL): {json.dumps(co)}; criterion: {cb[6]}",
         "! Units: mm, N, MPa, t (tonne), s, K.  Axisymmetric about Y (X = r, Y = z engine frame of CAD v3.4.1, +Y forward).",
         f"! Mesh level {level:g}: {len(X)} nodes, {len(E)} PLANE183 triangles (Ansys Student limit 128k nodes/elements).",
         "! Ties: coupled sets CP (UX = radial, UY = axial) between the coincident nodes of different parts (see sax.py tie_rule).",
         "! Pressures are applied as consistent nodal forces F (full ring) of the face pressures: no face-number convention needed.",
         "@@CHECK@@",
         "! Results to compare: sax_results_*.json (CalculiX 2.21 CAX6, identical mesh and loads).  SIM only - not physical validation.",
         "/PREP7", "ET,1,PLANE183", "KEYOPT,1,1,1", "KEYOPT,1,3,1", "TREF,293.15"]
    for mi, m_ in enumerate(MAT_MECH, start=1):
        if not (mat == m_).any():
            continue
        M = engmat.MATERIALS[m_]
        L.append(f"! material {mi} = {m_}")
        L.append(f"MP,DENS,{mi},{M['rho']['v'] * 1e-12:.6e}")
        L.append(f"MP,PRXY,{mi},{M['nu']['v']}")
        L.append(f"MP,REFT,{mi},293.15")
        for key, lab, scale in (("E", "EX", 1e-6), ("alpha", "ALPX", 1.0)):
            P_ = M[key]
            if "T_C" in P_:
                Ts = [t + 273.15 for t in P_["T_C"]]
                vs = [v * scale for v in P_["v"]]
                L.append("MPTEMP")
                for k0 in range(0, len(Ts), 6):
                    L.append(f"MPTEMP,{k0 + 1}," + ",".join(f"{t:.2f}" for t in Ts[k0:k0 + 6]))
                for k0 in range(0, len(vs), 6):
                    L.append(f"MPDATA,{lab},{mi},{k0 + 1}," + ",".join(f"{v:.6e}" for v in vs[k0:k0 + 6]))
                L.append("MPTEMP")
            else:
                L.append(f"MP,{lab},{mi},{P_['v'] * scale:.6e}")
    L.append("! nodes")
    L += [f"N,{i + 1},{x[0]:.6f},{x[1]:.6f}" for i, x in enumerate(X)]
    L.append("TYPE,1")
    for mi, m_ in enumerate(MAT_MECH, start=1):
        idx = np.nonzero(mat == m_)[0]
        if not len(idx):
            continue
        L.append(f"MAT,{mi}")
        for e in idx:
            L.append(f"EN,{e + 1}," + ",".join(str(int(n) + 1) for n in E[e]))
    # coupled sets: group dependents by their root
    k_cp = 0
    for dof, lab in ((1, "UX"), (2, "UY")):
        grp = {}
        for a_, b_ in d["eqs"][dof]:
            grp.setdefault(int(b_), []).append(int(a_))
        for root, deps in grp.items():
            nodes_ = [root] + deps
            k_cp += 1
            # CP accepts up to 17 nodes per command; additional nodes are appended with CP,k (same set number)
            L.append(f"CP,{k_cp},{lab}," + ",".join(str(n + 1) for n in nodes_[:16]))
            for k0 in range(16, len(nodes_), 16):
                L.append(f"CP,{k_cp},{lab}," + ",".join(str(n + 1) for n in nodes_[k0:k0 + 16]))
    sup = support_nodes(d, info)
    sup0 = support_node0(d, info, sup)
    U1 = z["U1"]
    L.append("! support (rev B run 2): the collar groove band carries the mechanical load but does not restrain the thermal growth: every")
    L.append("! groove-bottom node is held at its THERMAL-ONLY axial displacement (CalculiX step 1, one node at u_z = 0), radial free")
    L.append("NSEL,NONE")
    for n in sup:
        L.append(f"NSEL,A,NODE,,{int(n) + 1}")
    L += ["CM,NSUP,NODE", "ALLSEL"]
    L += [f"D,{int(n) + 1},UY,{(0.0 if int(n) == sup0 else float(U1[int(n), 1])):.6e}" for n in sup]
    L += ["FINISH", "/SOLU", "ANTYPE,STATIC", "! nodal temperatures (K)"]
    L += [f"BF,{i + 1},TEMP,{t:.3f}" for i, t in enumerate(T)]
    L.append("! pressures: consistent nodal forces of the face pressures (full 360 deg ring, N), quadratic edges, 3-point Gauss")
    Fn = np.zeros((len(X), 2))
    gs, gw = np.array([-math.sqrt(0.6), 0.0, math.sqrt(0.6)]), np.array([5 / 9, 8 / 9, 5 / 9])
    for (e, f, c, rr, zz, n, Lf) in fb:
        v = 0.0
        for k, coef in co.items():
            if k == "OP":
                v += coef * (1.0 if c == "PC" else (gp(zz) if c == "GAS" else 0.0))
            elif k == "BL":
                v += coef * ((1.0 if c == "PC" else ((1.0 if zz >= info["throat"] else 0.0) if c == "GAS" else 0.0)) + plug.get((e, f), 0.0))
            elif k == "PM":
                v += coef * (1.0 if c == "PM" else 0.0)
        if v == 0.0:
            continue
        i, j, k_ = EDGE[f]
        ids = [int(E[e, i]), int(E[e, j]), int(E[e, k_])]            # corner at s = -1, corner at s = +1, midside at s = 0
        xa, xb, xm_ = X[ids[0]], X[ids[1]], X[ids[2]]
        for s_, w_ in zip(gs, gw):
            N = np.array([0.5 * s_ * (s_ - 1.0), 0.5 * s_ * (s_ + 1.0), 1.0 - s_ * s_])
            dN = np.array([s_ - 0.5, s_ + 0.5, -2.0 * s_])
            xs = N[0] * xa + N[1] * xb + N[2] * xm_
            dx = dN[0] * xa + dN[1] * xb + dN[2] * xm_
            q = -v * 2.0 * math.pi * xs[0] * np.array([dx[1], -dx[0]]) * w_      # -p n dA, n dA = (dz, -dr) ds (CCW edge, outward)
            for a_, Na in zip(ids, N):
                Fn[a_] += Na * q
    F_exp = float(Fn[:, 1].sum())
    for nd in np.nonzero(np.abs(Fn).sum(axis=1) > 0)[0]:
        L.append(f"F,{nd + 1},FX,{Fn[nd, 0]:.6e}")
        L.append(f"F,{nd + 1},FY,{Fn[nd, 1]:.6e}")
    L.append("ALLSEL")
    if co.get("G"):
        L.append(f"ACEL,0,{co['G'] * G:.4f},0      ! +Y acceleration of the frame = inertia load toward -Y (nozzle)")
    L += ["OUTRES,ALL,ALL", "SOLVE", "FINISH", "/POST1", "SET,LAST", "CMSEL,S,NSUP", "FSUM", "ALLSEL", "PRNSOL,S,PRIN", "! end"]
    chk = (f"! CHECK after SOLVE: total axial reaction FY on NSUP (full ring) = {(-(F_exp + F_body)):.2f} N expected (consistent pressure forces "
           f"{F_exp:.2f} N [ccx midpoint integral {F_mid:.2f} N] + body force {F_body:.2f} N on the modelled mass {mass_t * 1e3:.4f} kg).")
    L[L.index("@@CHECK@@")] = chk
    Path(path).write_text("\n".join(L) + "\n")
    return {"file": str(path), "case": cid, "state": st, "nodes": int(len(X)), "elements": int(len(E)),
            "expected_support_FY_N": -(F_exp + F_body), "sha256_16": sha16(path)}


# =============================================================================================== modal (DLF of the stand transient)
def modal(level, nmodes=10, threads=1):
    """Axisymmetric (n = 0) natural frequencies of the structural model at 20 C, support as the static model.  Liner, grain, injector
    internals are NOT in the model (non-structural mass): the result is an upper bound; a mass-ratio correction is reported."""
    faces, info = geometry()
    d, meta_m = load_mesh(level)
    wd = run_dir(level) / "MODAL"
    wd.mkdir(parents=True, exist_ok=True)
    job = wd / "modal.inp"
    X, E, mat = d["X"], d["E"], d["mat"]
    lines = [f"*HEADING\nS-AX {VERSION} modal L{level:g}\n", "*NODE, NSET=NALL\n"]
    lines += [f"{i + 1}, {x[0]:.6f}, {x[1]:.6f}\n" for i, x in enumerate(X)]
    for m_ in MAT_MECH:
        idx = np.nonzero(mat == m_)[0]
        if len(idx):
            lines.append(f"*ELEMENT, TYPE=CAX6, ELSET=M_{m_.replace('-', '_')}\n")
            lines += [f"{e + 1}, " + ", ".join(str(int(n) + 1) for n in E[e]) + "\n" for e in idx]
    sup = support_nodes(d, info)
    lines.append("*NSET, NSET=NSUP\n")
    lines += [", ".join(str(int(n) + 1) for n in sup[k:k + 12]) + "\n" for k in range(0, len(sup), 12)]
    for m_ in MAT_MECH:
        if (mat == m_).any():
            lines.append(mat_cards(m_))
            lines.append(f"*SOLID SECTION, ELSET=M_{m_.replace('-', '_')}, MATERIAL={m_.replace('-', '_')}\n")
    for dof in (1, 2):
        for a_, b_ in d["eqs"][dof]:
            lines.append(f"*EQUATION\n2\n{a_ + 1}, {dof}, 1., {b_ + 1}, {dof}, -1.\n")
    lines.append("*BOUNDARY\nNSUP, 2, 2\n")
    lines.append(f"*INITIAL CONDITIONS, TYPE=TEMPERATURE\nNALL, {T_REF}\n")
    # the final temperature must be defined in the step once initial temperatures exist (ccx checktemp; the first FA-1 modal run
    # stopped with "*ERROR in checktemp: no final temperature defined in node 73529", kept in the log of that run)
    lines.append(f"*STEP\n*FREQUENCY\n{nmodes}\n*TEMPERATURE\nNALL, {T_REF}\n*NODE FILE\nU\n*END STEP\n")
    job.write_text("".join(lines))
    r = run_ccx(job, threads=threads)
    freqs = []
    grab = False
    for line in open(wd / "modal.dat"):
        if "E I G E N V A L U E   O U T P U T" in line:
            grab = True
            continue
        if grab:
            p = line.split()
            if len(p) == 5 and p[0].isdigit():
                freqs.append({"mode": int(p[0]), "eigenvalue": float(p[1]), "f_Hz": float(p[3])})
            elif freqs and "P A R T I C I P" in line:
                break
    return {"run": r, "freqs": freqs, "level": level, "nodes": int(len(X))}


def dlf_ramp(f_hz, t_rise_s):
    """Peak dynamic load factor of an undamped SDOF under a linear ramp to a constant load (rise t_r): 1 + |sin(pi t_r/T)| / (pi t_r/T)."""
    x = math.pi * t_rise_s * f_hz
    return 1.0 + abs(math.sin(x)) / x


# =============================================================================================== FMEA FA-1: head-end pulse
def fa1_tau(t_r):
    """Decay time constant of the normalised pulse p(t) = t/t_r (t <= t_r), exp(-(t - t_r)/tau) after, such that the head pressure
    stays above 45 bar abs for FA1['t_above_45bar_s'] (Combustion: 3.0 ms)."""
    q = (45.0 - 1.01325) / (FA1["P_head_abs_bar"] - 1.01325)
    return (FA1["t_above_45bar_s"] - t_r * (1.0 - q)) / (-math.log(q))


def sdof_dlf(f_hz, t_r, tau, zeta=0.0):
    """Peak |x| / x_static(peak) of x'' + 2 zeta w x' + w^2 x = w^2 p(t) for the FA-1 pulse (exact piecewise-linear Duhamel via lsim)."""
    from scipy import signal
    w = 2.0 * math.pi * f_hz
    T = 1.0 / f_hz
    dt = min(T, t_r) / 100.0
    t_end = t_r + 2.0 * tau + 5.0 * T          # undamped: the peak is reached within ~1 period after the ramp; the load then decays
    t = np.arange(0.0, t_end, dt)
    p = np.where(t <= t_r, t / t_r, np.exp(-(t - t_r) / tau))
    sys_ = signal.lti([w * w], [1.0, 2.0 * zeta * w, w * w])
    _, x, _ = signal.lsim(sys_, p, t)
    return float(np.max(np.abs(x)))


def dlf_band(f_hz, mass_factor, t_rs=(0.0005, 0.00075, 0.001), n=25):
    """Max SDOF DLF over the frequency band [f / sqrt(mass_factor), f] (model f is an upper bound) and the rise times t_rs: the ramp
    DLF oscillates with f t_r (1 + |sin(pi f t_r)| / (pi f t_r)), so the end points of the band do not bound it."""
    best = (0.0, None, None)
    for t_r in t_rs:
        tau = fa1_tau(t_r)
        for s in np.linspace(1.0 / math.sqrt(mass_factor), 1.0, n):
            v = sdof_dlf(f_hz * s, t_r, tau)
            if v > best[0]:
                best = (v, f_hz * s, t_r)
    return best


def read_frd_modes(frd, n_nodes):
    """Mode shapes (DISP blocks) of a ccx *FREQUENCY run."""
    modes, blk, vals = [], None, []
    with open(frd) as fh:
        for line in fh:
            if line.startswith(" -4  "):
                blk = line[5:13].strip()
                blk = blk if blk == "DISP" else None
                vals = []
                continue
            if blk is None:
                continue
            if line.startswith(" -1"):
                vals.append(line)
            elif line.startswith(" -3"):
                arr = np.zeros((n_nodes, 3))
                for l in vals:
                    arr[int(l[3:13]) - 1] = [float(l[13 + 12 * k:25 + 12 * k]) for k in range(3)]
                modes.append(arr)
                blk = None
    return modes


def fa1_dlf(level=1.0, threads=1, mass_factor=2.0):
    """DLF of the FA-1 pulse for the axisymmetric modes of the pressure structure (modal of this script), classified by the part with the
    largest share of sum(r |U|^2).  The model lacks the liner, grain and injector internals (non-structural mass), so its frequencies are
    UPPER bounds; the DLF is also evaluated at f / sqrt(mass_factor) (ASSUMED non-structural mass = structural mass) and with a rise
    time of 0.5 ms (bound) besides the nominal 1.0 ms (Combustion tf 1 ms; traces 10-90 % in 0.8 ms).  The governing value is the
    maximum over the first modes in which a pressure-loaded part (case, closures, nozzle stack) dominates."""
    m = modal(level, nmodes=12, threads=threads)
    d, _ = load_mesh(level)
    node_part, _ = node_maps(d)
    wd = run_dir(level) / "MODAL"
    shapes = read_frd_modes(wd / "modal.frd", len(d["X"]))
    r = d["X"][:, 0]
    rows = []
    for k, fr in enumerate(m["freqs"]):
        U = shapes[k] if k < len(shapes) else None
        share = {}
        if U is not None:
            e = r * np.sum(U[:, :2] ** 2, axis=1)
            tot = e.sum()
            share = {p: round(float(e[node_part == p].sum() / tot), 3) for p in PARTS}
        dom = max(share, key=share.get) if share else None
        f = fr["f_Hz"]
        vals = {}
        for t_r in (0.0005, 0.001):
            tau = fa1_tau(t_r)
            vals[f"t_r_{t_r * 1e3:g}ms"] = {"f_model": round(sdof_dlf(f, t_r, tau), 4),
                                            "f_over_sqrt_mass_factor": round(sdof_dlf(f / math.sqrt(mass_factor), t_r, tau), 4)}
        bmax, bf, btr = dlf_band(f, mass_factor)
        vals["band_max"] = {"DLF": round(bmax, 4), "at_f_Hz": round(bf, 1), "at_t_r_ms": btr * 1e3,
                            "band": f"f in [f/sqrt({mass_factor:g}), f], t_r in 0.5/0.75/1.0 ms"}
        rows.append({"mode": fr["mode"], "f_Hz": round(f, 1), "dominant_part": dom, "share": share, "DLF": vals})
    pressure_parts = {"ENG-TC-01", "ENG-TC-02", "ENG-TC-03", "ENG-TC-04", "ENG-TC-09", "ENG-NZ-01", "ENG-NZ-02", "ENG-NZ-03", "ENG-NZ-04", "ENG-NZ-06"}
    gov = max((rw["DLF"]["band_max"]["DLF"], rw["mode"]) for rw in rows if rw["dominant_part"] in pressure_parts)
    out = {"id": "sax_fa1_dlf", "version": VERSION, "date": "2026-10-13", "owner": "mechanical", "script": "04-fea/structural/sax.py fa1dlf",
           "pulse": dict(FA1, shape="linear ramp over t_r, then exponential decay; tau from 3.0 ms above 45 bar abs",
                         tau_s={"t_r_0.5ms": fa1_tau(0.0005), "t_r_0.75ms": fa1_tau(0.00075), "t_r_1ms": fa1_tau(0.001)}),
           "mass_factor_ASSUMED": mass_factor, "modes": rows, "DLF_governing": gov[0], "governing_mode": gov[1],
           "DLF_step_bound": 2.0, "modal_run": m["run"],
           "modal_model": "axisymmetric n = 0, 20 C properties, groove band fixed in z (rigid support), liner/grain/injector internals "
                          "absent (non-structural mass): model frequencies are UPPER bounds; band down to f/sqrt(mass_factor)",
           "note": "undamped SDOF per mode (no damping credit); quasi-static if t_r >> T.  The governing DLF (max of the band over the "
                   "modes dominated by a pressure part) multiplies the pulse peak in combo FA1; combo FA1S uses the step bound 2.0 "
                   "(rise time -> 0) as the sensitivity for a rise faster than 0.5 ms."}
    FA1_DLF_FILE.parent.mkdir(exist_ok=True)
    FA1_DLF_FILE.write_text(json.dumps(out, indent=1, default=float))
    return out


FA1_DLF_FILE = HERE / "results" / ("sax_fa1_dlf_v1.json" if CADV == "v341revB" else f"sax_fa1_dlf{CADTAG}_v1.json")   # v3.5.1 / v3.5.2: own file


def fa1_dlf_value():
    """Governing FA-1 DLF from the modal run (results/sax_fa1_dlf_v1.json); the step bound 2.0 until it exists."""
    try:
        return float(json.loads(FA1_DLF_FILE.read_text())["DLF_governing"])
    except Exception:
        return 2.0


# =============================================================================================== convergence + TS-2 time at temperature
def convergence_table(levels, states, cases=None, ex_r=1.0):
    """Same states and cases at every mesh level (element size ratio 2): peak von Mises (regular / all nodes), min MS (regular), SCL
    primary and P+Q stresses, max displacement.  Observed order p and GCI (Roache, Fs 1.25) where the three values are monotonic."""
    evs = {lv: evaluate(lv, states=states, ex_r=ex_r, cases=cases) for lv in levels}

    def kv(ev):
        q = {}
        for r in ev["rows"]:
            base = (r["case"], r["state"], r["part"], r["set"])
            q[("vm_max",) + base] = r["vm_max_MPa"]
            if r["set"] == "regular":
                q[("MS",) + base] = r["MS"]
                if r["material"] in BRITTLE:
                    q[("s1_max",) + base] = r["s1_max_MPa"]
                    q[("s3_min",) + base] = r["s3_min_MPa"]
        for r in ev["scl"]:
            q[("scl_P_PmPb", r["case"], r["state"], r["scl"])] = r["P_PmPb_vm"]
            q[("scl_PQ_PmPb", r["case"], r["state"], r["scl"])] = r["PQ_PmPb_vm"]
        for r in ev["displacements"]:
            for p_, v_ in r["max_abs_U_mm"].items():
                q[("Umax", r["case"], r["state"], p_)] = v_
        return q
    vals = {lv: kv(ev) for lv, ev in evs.items()}
    keys = sorted(set.intersection(*[set(v) for v in vals.values()]), key=str)
    lv = sorted(levels, reverse=True)                     # coarse -> fine
    rows = []
    for k in keys:
        f = [vals[l][k] for l in lv]
        row = {"quantity": k[0], "key": list(k[1:]), "levels": lv, "values": f}
        if len(f) == 3:
            e21, e32 = f[1] - f[0], f[2] - f[1]
            row["rel_change_last"] = (e32 / f[2]) if abs(f[2]) > 1e-12 else None
            if e21 != 0 and e32 != 0 and (e21 > 0) == (e32 > 0) and abs(e32) < abs(e21):
                pobs = math.log(abs(e21 / e32)) / math.log(2.0)
                row["p_observed"] = pobs
                row["GCI_fine"] = 1.25 * abs(e32 / f[2]) / (2.0 ** pobs - 1.0) if abs(f[2]) > 1e-12 else None
                row["extrapolated"] = f[2] + e32 / (2.0 ** pobs - 1.0)
                row["verdict"] = "converging (monotonic)"
            elif abs(e32) <= 0.02 * max(abs(f[2]), 1e-9):
                row["verdict"] = "within 2 % (non-monotonic)"
            else:
                row["verdict"] = "not converged / singular" if abs(e32) >= abs(e21) else "oscillating"
        rows.append(row)
    return {"levels": lv, "states": states, "cases": cases, "mesh": {l: evs[l]["mesh"] for l in lv}, "rows": rows}


def time_at_temperature(run_dir, parts=("ENG-TC-01", "ENG-TC-02", "ENG-TC-04"), thresholds_C=(120, 150, 175, 200, 250)):
    """Hot-spot time above thresholds per 6061 part over the whole thermal run (part maximum vs time, linear between frames)."""
    z = np.load(run_dir / "envelope_nodes.npz", allow_pickle=True)
    t = np.asarray(z["t_frames"], float)
    names = [str(x) for x in z["parts"]]
    out = {"thermal_run": run_dir.name, "t_end_s": float(t[-1]), "basis": "part maximum temperature (hot spot) per frame", "parts": {}}
    tf = np.linspace(t[0], t[-1], 200001)
    dt = tf[1] - tf[0]
    for p in parts:
        TC = np.interp(tf, t, np.asarray(z["part_series"][names.index(p)], float)) - 273.15
        out["parts"][p] = {"T_peak_C": round(float(TC.max()), 1), "t_peak_s": round(float(tf[TC.argmax()]), 2),
                           "time_above_s": {str(th): round(float((TC > th).sum() * dt), 1) for th in thresholds_C}}
    return out


# =============================================================================================== CLI
def _states(arg):
    if arg in (None, "all"):
        return list(states_all())
    if arg == "all_B1_TB_RT":          # v3.5.2 gap-conductance variant (B1 thermal runs only): every B1 state + TB + RT, no A1
        return [s for s in states_all() if not s.startswith("A1_")]
    return [s.strip() for s in arg.split(",") if s.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["solve", "post", "trim", "modal", "vtu", "ansys", "conv", "fa1dlf", "png", "seals"])
    ap.add_argument("--level", type=float, default=1.0)
    ap.add_argument("--levels", default="2,1,0.5")
    ap.add_argument("--states", default="all")
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--ex", type=float, default=1.0)
    ap.add_argument("--picks", default="")
    a = ap.parse_args()
    t0 = time.time()
    if a.cmd == "solve":
        for st in _states(a.states):
            t1 = time.time()
            if a.force or not (run_dir(a.level) / st / "res.npz").exists():
                _guard_before_ccx(st)
            res = solve_state(a.level, st, threads=a.threads, force=a.force)
            m = json.loads(str(np.load(res, allow_pickle=True)["meta"]))
            print(f"{st}: {time.time() - t1:.1f} s, ccx {m['run']['seconds']} s, RF check "
                  + ", ".join(f"{k} {v['pressure_integral_N']:.1f}/{v['support_reaction_x180_N']:.1f}" for k, v in m["RF_check"].items()),
                  flush=True)
    elif a.cmd == "post":
        ev = evaluate(a.level, states=None if a.states == "all" else _states(a.states), ex_r=a.ex)
        fj, fc, fs = write_tables(ev, run_dir(a.level).name)          # L1 (design ties) or L1_bonded (bound variant)
        print(fj, fc, fs)
        table, scl, ifc = governing(ev)
        for r in table:
            fmt = lambda x: "  -   " if x is None else (f">{MS_CAP:g}  " if x > MS_CAP else f"{x:6.2f}")
            print(f"{r['case']:5s} {r['part']:10s} {r['state']:9s} MS {r['MS']:7.3f} prim {fmt(r.get('MS_primary_only'))} "
                  f"PQ {fmt(r.get('MS_PQ_nodal_shakedown'))} (all {r['MS_all_nodes'] if r['MS_all_nodes'] is None else round(r['MS_all_nodes'], 3)}) "
                  f"vm {r['vm_MPa']:7.1f} T {r['T_C']:7.1f} {r.get('zone') or '':6s} at {r['at_r_z_mm']} | {r['status'][:70]}")
    elif a.cmd == "trim":
        # v352r4 (lead 07:18Z): after the post has written the tables, keep a state (the TB abort trials) as the seat sub-model region
        # only: every node of TC-02 / TC-03 / TC-04 elements and of TC-01 elements with centroid z >= bolt_z_fwd - 32 mm (the T-F2
        # sub-model takes TC-01 above bolt_z_fwd - 30 mm), float32, in res_sub.npz; res.npz is removed (its sha256/16 is kept in meta)
        faces, info = geometry()
        d, _ = load_mesh(a.level)
        cen_z = d["X"][d["E"], 1].mean(axis=1)
        sel = np.isin(d["pn"], ["ENG-TC-02", "ENG-TC-03", "ENG-TC-04"]) | ((d["pn"] == "ENG-TC-01") & (cen_z >= info["bolt_z_fwd"] - 32.0))
        nodes = np.unique(d["E"][sel]).astype(np.int64)
        for st in _states(a.states):
            rp = run_dir(a.level) / st / "res.npz"
            z = np.load(rp, allow_pickle=True)
            meta = json.loads(str(z["meta"]))
            meta["trim"] = {"rule": "TC-02 / TC-03 / TC-04 + TC-01 elements with centroid z >= bolt_z_fwd - 32 mm", "n_nodes_full": int(len(d["X"])),
                            "n_nodes_kept": int(len(nodes)), "full_res_sha256_16": sha16(rp), "full_res_bytes": rp.stat().st_size,
                            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
            arrs = {k: np.asarray(z[k])[nodes].astype(np.float32) for k in z.files if k != "meta"}
            ro = rp.parent / "res_sub.npz"
            np.savez_compressed(ro, nodes=nodes, **arrs, meta=json.dumps(meta, default=float))
            chk = load_res_any(a.level, st)          # reads res.npz while it still exists: verify the subset round-trips
            r2 = _load_res(ro)
            ok = all(np.allclose(r2[k], np.asarray(z[k], np.float64)[nodes], rtol=1e-6, atol=1e-9) for k in arrs)
            if not ok:
                ro.unlink()
                raise RuntimeError(f"trim {st}: subset round-trip failed")
            del chk
            rp.unlink()
            print(f"trim {st}: {meta['trim']['full_res_bytes']} -> {ro.stat().st_size} bytes, {len(nodes)} of {len(d['X'])} nodes", flush=True)
    elif a.cmd == "modal":
        out = modal(a.level, threads=a.threads)
        print(json.dumps(out, indent=1))
    elif a.cmd == "fa1dlf":
        out = fa1_dlf(a.level, threads=a.threads)
        for rw in out["modes"]:
            print(rw["mode"], rw["f_Hz"], rw["dominant_part"], rw["DLF"])
        print("governing DLF", out["DLF_governing"], "mode", out["governing_mode"])
    elif a.cmd == "vtu":
        # --picks "LC2:B1_21.65,BN:B1_21.65,..." (case:state pairs; combos(info) ids)
        picks = [tuple(x.split(":")) for x in a.picks.split(",") if x.strip()]
        out = HERE / "results" / f"sax_fields_L{a.level:g}{CADTAG}_{VERSION}.vtu"
        out.parent.mkdir(exist_ok=True)
        r = export_vtu(a.level, picks, out)
        (out.with_suffix(".json")).write_text(json.dumps(r, indent=1, default=float))
        print(json.dumps(r, indent=1, default=float))
    elif a.cmd == "seals":
        # --picks "FA1:A1_22.2,FA1S:A1_22.2,..." -> results/sax_seal_gaps_<tag>_v1.json
        picks = [tuple(x.split(":")) for x in a.picks.split(",") if x.strip()]
        res = seal_gaps(a.level, picks)
        fo = HERE / "results" / f"sax_seal_gaps_{run_dir(a.level).name}_{VERSION}.json"
        fo.write_text(json.dumps({"id": "sax_seal_gaps", "version": VERSION, "date": "2026-10-13", "owner": "mechanical",
                                  "script": "04-fea/structural/sax.py seals", "status": "SIM (linear elastic FE displacement field)",
                                  "rows": res}, indent=1, default=float))
        for r_ in res:
            print(r_["case"], r_["state"], {k: (round(v.get("opening_mean_mm", float("nan")), 4), round(v.get("opening_max_mm", float("nan")), 4),
                                                round(v.get("opening_at_flank_mm", float("nan")), 4)) for k, v in r_["seals"].items()})
    elif a.cmd == "png":
        # --picks "LC1:B1_21.65,LC1:B1_19,..." -> results/png/sax_<case>_<state>_<tag>_v1.png + index json
        picks = [tuple(x.split(":")) for x in a.picks.split(",") if x.strip()]
        outdir = HERE / "results" / "png"
        idx = export_png(a.level, picks, outdir, ex_r=a.ex)
        fi = outdir / f"sax_png_index_{run_dir(a.level).name}_{VERSION}.json"
        old = json.loads(fi.read_text())["pngs"] if fi.exists() else []
        keep = [o for o in old if (o["case"], o["state"]) not in set(picks)]
        fi.write_text(json.dumps({"id": "sax_png_index", "version": VERSION, "date": "2026-10-13", "owner": "mechanical",
                                  "script": "04-fea/structural/sax.py png", "status": "SIM field plots (linear elastic FE); not validation",
                                  "pngs": keep + idx}, indent=1, default=float))
        for o in idx:
            print(o["file"], o["sha256_16"], "vm_max", round(o["vm_max_regular_MPa"], 1), "T", [round(x) for x in o["T_range_C"]],
                  "Umax", round(o["U_max_mm"], 4), "ms_min_reg", round(o["ms_min_regular"], 3))
    elif a.cmd == "ansys":
        # --picks "BN:B1_21.65" (one or more case:state pairs, one APDL deck each)
        outs = []
        for x in [p_ for p_ in a.picks.split(",") if p_.strip()]:
            cid, st = x.split(":")
            out = HERE / "ansys" / f"sax_{cid}_{st}_L{a.level:g}{CADTAG}_{VERSION}.inp"
            out.parent.mkdir(exist_ok=True)
            outs.append(export_ansys(a.level, cid, st, out))
        (HERE / "ansys" / f"sax_ansys_index_L{a.level:g}{CADTAG}_{VERSION}.json").write_text(json.dumps(outs, indent=1, default=float))
        print(json.dumps(outs, indent=1, default=float))
    elif a.cmd == "conv":
        levels = [float(x) for x in a.levels.split(",")]
        sts = _states(a.states)
        for lv in levels:
            for st in sts:
                solve_state(lv, st, threads=a.threads)
        ct = convergence_table(levels, sts, ex_r=a.ex)
        out = HERE / "results" / f"sax_convergence{CADTAG}_{VERSION}.json"
        out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps({"id": "sax_convergence", "version": VERSION, "date": "2026-10-13", "owner": "mechanical",
                                   "script": "04-fea/structural/sax.py conv", **ct}, indent=1, default=float))
        print(out)
    print(f"done {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
