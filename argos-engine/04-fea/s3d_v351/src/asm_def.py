"""FEA3D assembly definition (CAD v3.5 neutral STEP 0dd8064359c6aa26, engine frame mm, +Z forward, origin = gimbal pivot).

Bodies that are meshed (C3D10), their material (engmat key), pose group, temperature rule and mesh sizes per level.
Everything else in the massprops ledger is a MASS item (point mass on a distributing coupling) or outside the engine-module
load path (airframe-wall equipment: F4 hand calculations).
"""
from __future__ import annotations
import os
from pathlib import Path

ROOT = Path("/home/claude/work/fea3d")
# CAD version (environment FEA3D_CAD): 'v35' = ENGINE_v3.5_neutral.step (first pipeline run), 'v351' = frozen v3.5.1 (lead relay,
# hub 03-cad/v3.5.1, MANIFEST b62c0e0ac8555fb8): TC-02 TB1 recess + J-FWD taps, TC-03 TB1 flange in GlidCop AL-15, GM-01/02 root sector,
# GM-03 / GM-08 HK0808 cup seats, GM-04/05 440C raceway pins, GM-06/07 thrust washers, FD-01 spot face.
CAD = os.environ.get("FEA3D_CAD", "v351")
assert CAD in ("v35", "v351"), CAD
GEOM = ROOT / "geom" / f"{CAD}_neutral"
STEP_SHA16 = {"v35": "0dd8064359c6aa26", "v351": "4ca22820c796b670"}[CAD]
MESH_DIR = ROOT / "mesh" if CAD == "v35" else ROOT / "mesh" / CAD

# name: (instance brep stem, solid index or None, group, material, temperature rule, role)
BODIES = {
    "TC-01": ("ENG-TC-01_0", None, "engine", "AL6061-T6", "SAX", "case: pressure vessel + thrust path"),
    "TC-02": ("ENG-TC-02_0", None, "engine", "AL6061-T6", "SAX", "injector head / forward closure"),
    "TC-03": ("ENG-TC-03_0", None, "engine", "IN718" if CAD == "v35" else "GLIDCOP-AL15", "SAX", "pintle seat insert"),
    "TC-04": ("ENG-TC-04_0", None, "engine", "AL6061-T6", "SAX", "bonnet (manifold pressure)"),
    "TC-09": ("ENG-TC-09_0", None, "engine", "IN718", "SAX", "aft section + nozzle holder (J1 lip)"),
    "NZ-01": ("ENG-NZ-01_0", None, "engine", "GRAPHITE-ISO", "SAX", "graphite throat insert (brittle, load-bearing)"),
    "NZ-02": ("ENG-NZ-02_0", None, "engine", "CARBON-PHENOLIC", "SAX", "insert sleeve (ablative / insulating)"),
    "NZ-03": ("ENG-NZ-03_0", None, "engine", "CARBON-PHENOLIC", "SAX", "J1 hot-layer washer (load-bearing + ablative)"),
    "NZ-04": ("ENG-NZ-04_0", None, "engine", "FLEX-GRAPHITE-OI", "SAX", "J1 lip-face seal (bearing)"),
    "GM-01": ("ENG-GM-01_0", None, "engine", "AL7075-T6", "COLLAR", "collar half +Y (servo 1 lever)"),
    "GM-02": ("ENG-GM-02_0", None, "engine", "AL7075-T6", "COLLAR", "collar half -Y (servo 2 lever)"),
    "PD-01R": ("ENG-PD-01_0", 0, "engine", "AL6061-T6", "HEADTOP", "pintle drive frame, +Y piece (BOM 'B': foot + rail plate + shelf)"),
    "PD-01S": ("ENG-PD-01_0", 1, "engine", "AL6061-T6", "HEADTOP", "pintle drive frame, -Y piece (BOM 'A': foot + bridge + servo plate + cap)"),
    "FD-01": ("ENG-FD-01_0", None, "engine", "SS316L", "HEADFLAT", "oxidiser inlet block E1-M (feed bracket)"),
    "GM-03": ("ENG-GM-03_0", None, "ring", "AL6061-T6", "BAY", "gimbal ring"),
    "GM-08a": ("ENG-GM-08_0", None, "fixed", "AL6061-T6", "BAY", "yoke post +X"),
    "GM-08b": ("ENG-GM-08_1", None, "fixed", "AL6061-T6", "BAY", "yoke post -X"),
    "GM-09": ("ENG-GM-09_0", None, "fixed", "AL6061-T6", "BAY", "upper thrust ring (airframe interface, 8 x M5)"),
    "GM-10": ("ENG-GM-10_0", None, "fixed", "AL6061-T6", "BAY", "lower ring (airframe 8 x M5, servo base, stop)"),
    "GM-13": ("ENG-GM-13_0", None, "fixed", "AL6061-T6", "BAY", "TVC servo 1 bracket"),
    "GM-14": ("ENG-GM-14_0", None, "fixed", "AL6061-T6", "BAY", "TVC servo 2 bracket"),
    "GM-16a": ("ENG-GM-16_0", None, "horn1", "AL7075-T6", "BAY", "TVC horn servo 1"),
    "GM-16b": ("ENG-GM-16_1", None, "horn2", "AL7075-T6", "BAY", "TVC horn servo 2"),
}

# mesh sizes (hmax, hmin, curvature elements per 2 pi) at level 1.0; a level factor f scales hmax and hmin (f < 1 = finer)
MESH = {
    "TC-01": (6.0, 2.0, 8), "TC-02": (6.0, 1.2, 6), "TC-03": (2.0, 0.6, 8), "TC-04": (4.0, 1.0, 8), "TC-09": (5.0, 1.2, 8),
    "NZ-01": (5.0, 1.2, 8), "NZ-02": (4.0, 1.2, 8), "NZ-03": (3.0, 1.0, 8), "NZ-04": (2.5, 1.0, 8),
    "GM-01": (3.5, 1.0, 8), "GM-02": (3.5, 1.0, 8), "PD-01R": (4.0, 1.0, 8), "PD-01S": (4.0, 1.0, 8),
    "FD-01": (3.0, 1.0, 8), "GM-03": (5.0, 1.2, 8), "GM-08a": (8.0, 2.0, 6), "GM-08b": (8.0, 2.0, 6), "GM-09": (8.0, 2.0, 6),
    "GM-10": (8.0, 2.0, 6), "GM-13": (8.0, 2.0, 6), "GM-14": (8.0, 2.0, 6), "GM-16a": (2.5, 0.6, 8), "GM-16b": (2.5, 0.6, 8),
}

GROUP_OF_LEDGER = {"engine": "engine", "ring": "ring", "fixed": "fixed", "horn": "horn", "pushrod": "pushrod"}

DEFEAT = ROOT / "geom" / f"{CAD}_neutral_defeat"   # sliver-face defeatured BREPs (defeature.py log in PROGRESS.md)


def brep_of(name):
    stem = BODIES[name][0]
    p = DEFEAT / f"{stem}.brep"
    return p if p.exists() else GEOM / f"{stem}.brep"

# PD-02 (crank housing) is NOT meshable as drawn: the R 11.0 spring cavity (axis Y at z 237.4) is tangent to the housing top and
# bottom faces (z 248.4 / 226.4), a zero-thickness wall over y 19.5-25.5 at x = 0 (every gmsh 2D/3D algorithm and the STL route
# fail with intersecting PLC segments there).  CAD finding for Mechanical.  In the FE it is a RIGID connector between PD-01A and
# PD-01B over their PD-02 contact faces (upper bound on that joint stiffness), carrying its mass and the drive loads.
RIGID_CONNECTORS = {"PD-02": {"bodies": ("PD-01R", "PD-01S"), "instance": "ENG-PD-02_0"}}
