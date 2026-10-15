"""Reference vehicle RV-1: mass ledger, geometry and mass properties vs propellant state.

Frames and stations: body z_b along the vehicle axis toward the nose; station z [m] measured
from the airframe aft datum (base plane of the body tube), +z forward. The nozzle exit
protrudes below the datum. This matches the team CAD convention (+Z engine axis forward).

Every ledger item carries (nominal, min, max) mass, a station, a shape for inertia, an owner
and a tag. Airframe items are ASSUMED (Lauty has not designed the airframe). Propulsion items
are DERIVED from the ENGINE-BASELINE-v0 placeholder dimensions or ASSUMED, until
interfaces/mechanical.json publishes CAD mass properties (read by params.load_interfaces()).

Mass properties:
 * fixed items: point / tube / solid cylinder / thin cone / leg-ring inertia about own CG,
   moved to the vehicle CG with the parallel-axis theorem;
 * N2O liquid: settled solid cylinder from the tank bottom (positive axial acceleration),
   rigid for pitch/yaw (slosh handled separately), excluded from roll inertia (inviscid);
 * N2O vapour: uniform in the ullage;
 * fuel grain: hollow cylinder, port grows as fuel burns (part of the gimballed engine).
"""
import json
import numpy as np
from numba import njit

LEDGER_VERSION = "mass_ledger_v3c (2026-10-12; v3b + P00b engine v2 growth from the combustion relay; v1/v2/v3/v3b kept)"


def reference_geometry(pivot="forward", legs="deployable"):
    """Airframe and engine layout of RV-1 (all ASSUMED unless noted)."""
    g = dict(
        d=0.126,                 # body OD [m] (ID 0.120 m per ENGINE-BASELINE airframe_ID_m, + 3 mm wall)
        z_base=0.0, z_body_top=1.70, z_tip=2.00, L_nose=0.30,   # 2.0 m overall (REQUIREMENTS ref vehicle)
        z_nozzle_exit=-0.03,     # nozzle exit 30 mm below the datum (ENG-08 allows protrusion)
        z_injector=0.42,         # injector face; engine length 0.45 m (grain 0.354 m placeholder)
        z_eng_cg_dry=None,       # computed
        tank_z_bot_inner=0.625, tank_D_in=0.09525, tank_wall=0.003175,   # 101.6 x 3.175 mm (baseline)
        tank_V=2.5e-3,           # m3 baseline; resized by params when needed
        grain_z0=0.04, grain_L=0.354, grain_Do=0.052, grain_Dp0=0.030, rho_f=1050.0,
        n_legs=4, leg_d=0.020, leg_L=0.52, r_foot=0.40, z_foot=-0.25, z_leg_aero=-0.05,
        CA0_nf=0.45, CA0_tf=1.05, CA_legs=1.5, CA_engon_nf=-0.07,
        n_fins=0,
    )
    g["z_pivot"] = {"forward": 0.40, "mid": 0.23}[pivot]
    g["pivot"] = pivot
    g["legs"] = legs
    return g


def reference_geometry_v2(pivot="mid", legs="deployable", comb=None, fins=False):
    """RV-1b: RV-1 airframe with the engine laid out from combustion.json (gas path, grain).
    Engine stations: nozzle exit at z = -0.03 m (as RV-1), injector face = exit + gas-path length.
    Pivot 'mid' = gimballed CG (computed from ledger v2), 'forward' = 0.02 m above the injector face."""
    from .engine_v2 import load_combustion
    comb = comb or load_combustion()
    gp = comb["gas_path"]
    g = reference_geometry(pivot="mid", legs=legs)
    z_exit = g["z_nozzle_exit"]
    z_face = z_exit + gp["overall"]["gas_path_length_injector_face_to_exit_m"]["v"]
    gr = gp["grain"]
    g.update(z_injector=z_face, grain_z0=z_face - gr["x_face_end_m"]["v"], grain_L=gr["length_m"]["v"],
             grain_Do=gr["outer_diameter_m"]["v"], grain_Dp0=gr["port"]["initial_diameter_m"]["v"],
             rho_f=gr["density_kg_m3"]["v"], tank_z_bot_inner=0.55, comb_version=comb.get("version", "?"),
             z_throat=z_exit + (gp["nozzle"]["x_face_exit_m"]["v"] - gp["nozzle"]["x_face_throat_m"]["v"]))
    g["z_pivot"] = None
    g["pivot"] = pivot
    g["n_fins"] = 4 if fins else 0
    if fins:
        # aft fins / leg-fin panels (ASSUMED planform, sized in REPORT for coast stability):
        # root chord 0.20 m along the body from z = 0.20 (LE, nose-first) to z = 0.00, tip chord 0.10 m,
        # span 0.12 m, LE sweep 0.10 m (Barrowman CNa ~ 8 /rad incl. body interference)
        g.update(fin_cr=0.20, fin_ct=0.10, fin_span=0.12, fin_sweep=0.10, fin_z_le=0.20)
    led = mass_ledger_v2(dict(g, z_pivot=0.18))
    mg = sum(i["m"] for i in led if i["gimballed"])
    zg = sum(i["m"] * i["z"] for i in led if i["gimballed"])
    m_f = g["rho_f"] * np.pi / 4 * (g["grain_Do"] ** 2 - g["grain_Dp0"] ** 2) * g["grain_L"]
    zg = (zg + m_f * (g["grain_z0"] + g["grain_L"] / 2)) / (mg + m_f)
    g["z_pivot"] = round(zg, 3) if pivot == "mid" else round(z_face + 0.02, 3)
    return g


def mass_ledger_v2(geo, descent_option="none", tank_V=None, fins=None):
    """Ledger for RV-1b (engine from combustion.json v1; airframe as RV-1). All engine items ASSUMED
    until mechanical.json; stations follow reference_geometry_v2."""
    V = geo["tank_V"] if tank_V is None else tank_V
    A_in = np.pi * geo["tank_D_in"] ** 2 / 4
    L_in = V / A_in
    Do = geo["tank_D_in"] + 2 * geo["tank_wall"]
    A_wall = np.pi / 4 * (Do ** 2 - geo["tank_D_in"] ** 2)
    L_tube = L_in + 0.05
    m_tank = A_wall * L_tube * 2700.0 + 0.30 + 0.15
    z_tank_c = geo["tank_z_bot_inner"] + L_in / 2
    zf = geo["z_injector"]
    case_L = zf + 0.012 - (-0.01)
    m_case = np.pi / 4 * (0.0635 ** 2 - 0.05715 ** 2) * case_L * 2700.0
    zp = geo["z_pivot"]
    it = []

    def add(name, owner, m, mmin, mmax, z, shape, dims, gimb, tag):
        it.append(dict(name=name, owner=owner, m=m, m_min=mmin, m_max=mmax, z=z, shape=shape,
                       dims=dims, gimballed=gimb, tag=tag))
    add("P01 aft closure + nozzle holder + graphite throat insert (44x32 mm)", "propulsion", 0.30, 0.20, 0.45,
        -0.005, "cyl", [0.032, 0.06], True, "ASSUMED (combustion.json v1 insert envelope; Mechanical to replace)")
    add(f"P02 combustion case 6061-T6 63.5x3.175 mm, L {case_L:.3f} m", "propulsion", round(m_case, 3), 0.40, 0.65,
        round((zf + 0.012 - 0.01) / 2, 4), "tube", [0.03175, 0.02858, case_L], True,
        "DERIVED case length from combustion.json v1 gas path (face-to-exit 0.309 m) x 2700 kg/m3")
    add("P03 phenolic liner 1.6 mm + pre/post-chamber insulators", "propulsion", 0.14, 0.08, 0.22,
        round(zf / 2, 4), "tube", [0.02858, 0.02698, zf], True, "DERIVED/ASSUMED (combustion.json v1 liner)")
    add("P04 injector bulkhead + pintle body + manifold (316L/17-4PH)", "propulsion", 0.35, 0.25, 0.50,
        zf + 0.012, "cyl", [0.032, 0.025], True, "ASSUMED")
    add("P05 pintle throttle actuator (Savox SB-2292SG class + crank + encoder + bracket)", "propulsion", 0.15,
        0.10, 0.25, zf + 0.06, "point", [], True, "ASSUMED (electronics.json v1 servo 0.081 kg + hardware)")
    add("P05b torch igniter + 2 solenoids + spark plug", "propulsion", 0.15, 0.08, 0.25, zf - 0.015, "point", [],
        True, "ASSUMED (combustion.json v1 torch envelope)")
    add("P05c Pc + feed transducers + standoffs (gimballed side)", "propulsion", 0.10, 0.08, 0.15, zf + 0.03,
        "point", [], True, "ASSUMED (electronics.json v1 2 x 0.05 kg)")
    add("P06 gimbal ring, pins, bearings", "propulsion", 0.25, 0.15, 0.40, zp, "ring", [0.055], False, "ASSUMED")
    add("P07 thrust plate (airframe interface)", "propulsion", 0.25, 0.15, 0.40, zf + 0.09, "cyl", [0.06, 0.02],
        False, "ASSUMED")
    add("P08 TVC actuators x2 + pushrods + brackets", "propulsion", 0.30, 0.20, 0.45, zf + 0.02, "ring",
        [0.05], False, "ASSUMED (electronics.json v1: 2 x 0.081 kg servos + hardware)")
    add("P09 NC main isolation valve + spring/latch actuator", "propulsion", 0.35, 0.20, 0.60, zf + 0.17, "point",
        [], False, "ASSUMED")
    add("P10 flex hose, fittings, feed line", "propulsion", 0.20, 0.12, 0.35, zf + 0.12, "point", [], False,
        "ASSUMED")
    add("P11 N2O tank (tube, 2 bulkheads, fittings, relief, sensors)", "propulsion", round(m_tank, 3),
        round(0.85 * m_tank, 3), round(1.25 * m_tank, 3), z_tank_c, "tube", [Do / 2, geo["tank_D_in"] / 2, L_tube],
        False, "DERIVED baseline tank_v0 tube (101.6x3.175, 6061) + 0.45 kg closures/fittings ASSUMED")
    add("P12 engine ECU + battery share + tank sensors", "propulsion", 0.25, 0.16, 0.40, zf + 0.20, "point", [],
        False, "ASSUMED (electronics.json v1 ECU 0.16 kg)")
    add("A01 body tube 126 mm OD, PETG 2.5 mm wall, 1.70 m", "airframe", 2.09, 1.00, 2.80, 0.85, "tube",
        [0.063, 0.0605, 1.70], False, "ASSUMED (printed PETG 1270 kg/m3; CF/GF tube at min)")
    add("A02 nose cone + GNSS antenna", "airframe", 0.35, 0.25, 0.50, 1.80, "cone", [0.063, 0.30], False,
        "ASSUMED")
    add("A03a aft thrust ring + leg mounts", "airframe", 0.35, 0.20, 0.60, 0.20, "ring", [0.06], False, "ASSUMED")
    add("A03b bulkheads and couplers", "airframe", 0.35, 0.20, 0.50, 1.05, "cyl", [0.06, 0.02], False, "ASSUMED")
    if geo["legs"] == "deployable":
        add("A04 landing legs x4 (deployable)", "airframe", 1.20, 0.80, 2.00, -0.05, "legring", [0.22], False,
            "ASSUMED (r_foot 0.40 m, stroke >= 0.10 m)")
    add("A05 avionics (FC, IMU, GNSS, LiDAR, radio)", "airframe", 0.40, 0.25, 0.60, 1.15, "point", [], False,
        "ASSUMED")
    add("A06 battery", "airframe", 0.35, 0.20, 0.50, 1.10, "point", [], False, "ASSUMED")
    add("A07 backup recovery parachute + deployment", "airframe", 0.75, 0.50, 1.00, 1.45, "cyl", [0.055, 0.3],
        False, "ASSUMED")
    add("A08 harness, fasteners, misc", "airframe", 0.50, 0.30, 0.80, 0.85, "tube", [0.06, 0.055, 1.6], False,
        "ASSUMED")
    if (fins if fins is not None else geo.get("n_fins", 0) > 0):
        add("A10 aft fins x4 (span 0.12 m, chords 0.20/0.10 m, 3 mm GF/PETG) or leg-fin panels", "airframe", 0.30,
            0.15, 0.50, 0.12, "ring", [0.10], False, "ASSUMED (coast stability, see REPORT)")
    if descent_option == "drogue":
        add("A09 nose drogue + ejection + release + swivel", "airframe", 0.35, 0.25, 0.50, 1.70, "point", [],
            False, "ASSUMED (0.9 m drogue class)")
    elif descent_option == "rcs":
        add("P13 N2O vapour RCS: 6 valves, lines, nozzles", "propulsion", 0.60, 0.40, 0.90, 1.20, "ring", [0.05],
            False, "ASSUMED (6 x 30-60 g solenoid valves + lines)")
    elif descent_option == "flaps":
        add("A09 nose drag flaps (4) + actuators", "airframe", 0.80, 0.50, 1.20, 1.62, "ring", [0.07], False,
            "ASSUMED")
    return it


RV1_D_OD = 0.126   # RV-1/RV-1b body OD [m] (ASSUMED 120 mm ID + 3 mm wall), reference for airframe scaling


def reference_geometry_v3(legs="deployable", comb=None, mech=None, fins=False, d_id=None, wall=0.003):
    """RV-1c: RV-1b with the gimballed-engine module of mechanical.json (pivot station, engine stations)
    and the engine-bay ID of the founder decision 2026-10-12 (>= 140 mm, final), applied as a single
    body diameter over the full length (simplest airframe; a stepped 140/126 mm body is Lauty's option).
    Returns the geometry dict; every value that is not read from an interface file is ASSUMED."""
    g = reference_geometry_v2(pivot="mid", legs=legs, comb=comb, fins=fins)
    bay = None
    g["mech_version"] = None
    if mech is not None:
        g["mech_version"] = mech.get("version")
        g["z_pivot"] = mech["frames"]["rv1_station_of_pivot_m"]["v"]
        g["pivot"] = "CG (mechanical.json)"
        env = mech["envelope"]["stations_from_pivot_m"]
        g["z_injector_mech"] = g["z_pivot"] + env["inj_face"]["v"]
        g["z_exit_mech"] = g["z_pivot"] + env["exit"]["v"]
        g["z_grain_top_mech"] = g["z_pivot"] + env["grain_top"]["v"]
        g["z_head_top"] = g["z_pivot"] + mech["envelope"]["head_stack_top_m"]["v"]
        g["bay_zone"] = [g["z_pivot"] + z for z in mech["envelope"]["engine_bay_zone_m"]["v"]]
        bay = mech["envelope"]["required_engine_bay_ID_m"]["v"]
    d_id = d_id or bay or (RV1_D_OD - 2 * wall)
    g["d_id"] = d_id
    g["wall"] = wall
    g["d"] = d_id + 2.0 * wall
    g["vehicle"] = "RV-1c"
    return g


def mass_ledger_v3(geo, mech=None, el=None, descent_option="none", tank_V=None, fins=None, roll_rcs=True,
                   eng_growth=None):
    """Ledger for RV-1c. Gimballed engine from mechanical.json (dry, grain burnt; the grain is added by
    massprops from combustion.json); gimbal ring from mechanical.json; fixed propulsion-module items
    ASSUMED (mechanical.json v1 lists them without masses); airframe items of RV-1 scaled to the body
    diameter (tube by wall area, rings/nose by perimeter, bulkheads by area: ASSUMED scaling)."""
    if mech is None:
        return mass_ledger_v2(geo, descent_option=descent_option, tank_V=tank_V, fins=fins)
    V = geo["tank_V"] if tank_V is None else tank_V
    A_in = np.pi * geo["tank_D_in"] ** 2 / 4
    L_in = V / A_in
    Do = geo["tank_D_in"] + 2 * geo["tank_wall"]
    A_wall = np.pi / 4 * (Do ** 2 - geo["tank_D_in"] ** 2)
    L_tube = L_in + 0.05
    m_tank = A_wall * L_tube * 2700.0 + 0.30 + 0.15
    z_tank_c = geo["tank_z_bot_inner"] + L_in / 2
    zp = geo["z_pivot"]
    kd = geo["d"] / RV1_D_OD            # perimeter scaling
    kA = kd * kd                        # area scaling
    it = []

    def add(name, owner, m, mmin, mmax, z, shape, dims, gimb, tag):
        it.append(dict(name=name, owner=owner, m=m, m_min=mmin, m_max=mmax, z=z, shape=shape,
                       dims=dims, gimballed=gimb, tag=tag))
    gm = mech["gimballed_mass_properties"]
    dry = gm["dry_grain_burnt"]
    m_g = dry["m_kg"]["v"]
    cx, cy, cz = dry["cg_m"]["v"]
    Ip = np.array(dry["I_pivot_kgm2"]["v"])
    Ixx = Ip[0][0] - m_g * (cy * cy + cz * cz)
    Iyy = Ip[1][1] - m_g * (cx * cx + cz * cz)
    Izz = Ip[2][2] - m_g * (cx * cx + cy * cy)
    unc = 0.10   # mechanical.json v1: added items +/-30 % (about +/-0.10 kg)
    add("P00 gimballed engine dry: thrust chamber, head, pintle + actuator, collar + levers, inner pins, half "
        "pushrods, hose/line shares", "propulsion", m_g, m_g - unc, m_g + unc, zp + cz, "given",
        [0.5 * (Ixx + Iyy), Izz], True,
        f"mechanical.json {mech.get('version')} dry_grain_burnt (CAD v2 solids + itemised estimates, DERIVED+ASSUMED)")
    if eng_growth:
        # ledger v3c: combustion v2 engine growth relayed by the lead (gas path +30 mm, dry mass +0.11 kg); placed at
        # the engine CG (the pivot is kept at the engine CG by the lead decision) until mechanical.json v2
        add("P00b engine v2 growth (S230 gas path +30 mm): case, liner, nozzle shift", "propulsion",
            eng_growth["m"], 0.5 * eng_growth["m"], 1.5 * eng_growth["m"], zp + cz, "point", [], True, eng_growth["tag"])
    ring = gm["ring_alpha_axis_only"]
    m_r = ring["m_kg"]["v"]
    r_r = np.sqrt(2.0 * ring["I_xx_kgm2"]["v"] / m_r)
    add("P06 gimbal ring + outer pins (rotates about the outer axis only)", "propulsion", m_r, 0.7 * m_r, 1.3 * m_r,
        zp, "ring", [r_r], False, f"mechanical.json {mech.get('version')} ring_alpha_axis_only (ASSUMED there)")
    add("P07 thrust frame: 6061 annular plate, yoke lugs, servo cheeks, stop bumper, 8 x M5", "propulsion", 0.35,
        0.25, 0.50, zp - 0.09, "cyl", [0.065, 0.01], False,
        "ASSUMED mass (mechanical.json v1 gives the part, station ~ pivot - 0.09 m, no mass)")
    m_servo = el["actuators"]["tvc_A"]["mass_kg"]["v"] if el is not None else 0.081
    add("P08 TVC servos x2 + clamp horns + half pushrods (fixed side)", "propulsion", round(2 * m_servo + 0.06, 3),
        round(2 * m_servo + 0.03, 3), round(2 * m_servo + 0.12, 3), zp - 0.05, "ring", [0.056], False,
        "electronics.json servo mass x 2 (DATASHEET) + 0.06 kg hardware ASSUMED; r 46-66 mm beside the case (mechanical.json)")
    add("P09 NC isolation valve + spring/latch actuator (tank aft outlet)", "propulsion", 0.35, 0.20, 0.60,
        geo["tank_z_bot_inner"] - 0.05, "point", [], False, "ASSUMED (mechanical.json v1: part named, no mass)")
    add("P10 feed hose fixed share, fittings, tee, filter, torch/sense lines", "propulsion", 0.20, 0.12, 0.35,
        zp + 0.20, "point", [], False, "ASSUMED")
    add("P11 N2O tank (tube, 2 bulkheads, fittings, relief, sensors)", "propulsion", round(m_tank, 3),
        round(0.85 * m_tank, 3), round(1.25 * m_tank, 3), z_tank_c, "tube", [Do / 2, geo["tank_D_in"] / 2, L_tube],
        False, "DERIVED tank tube 101.6x3.175 6061 (mechanical.json v1 tank material) + 0.45 kg closures ASSUMED")
    add("P12 engine ECU + battery share + tank sensors", "propulsion", 0.25, 0.16, 0.40, geo["tank_z_bot_inner"] - 0.02,
        "point", [], False, "ASSUMED (electronics.json v1 ECU 0.16 kg)")
    ro, ri = geo["d"] / 2, geo["d"] / 2 - geo["wall"]
    L_t = geo["z_body_top"] - geo["z_base"]
    m_tube = 1270.0 * np.pi * (ro * ro - ri * ri) * L_t
    add(f"A01 body tube {geo['d']*1e3:.0f} mm OD, PETG {geo['wall']*1e3:.1f} mm wall, {L_t:.2f} m", "airframe",
        round(m_tube, 3), round(0.48 * m_tube, 3), round(1.34 * m_tube, 3), 0.5 * (geo["z_base"] + geo["z_body_top"]),
        "tube", [ro, ri, L_t], False,
        "DERIVED from ASSUMED wall/density (PETG 1270 kg/m3); bay ID from mechanical.json + founder decision 2026-10-12 (final); "
        "min = CF/GF tube, ratios as RV-1")
    add("A02 nose cone + GNSS antenna", "airframe", round(0.35 * kd, 3), round(0.25 * kd, 3), round(0.50 * kd, 3),
        1.80, "cone", [ro, geo["L_nose"]], False, "ASSUMED RV-1 value x d ratio")
    add("A03a aft thrust ring + leg mounts", "airframe", round(0.35 * kd, 3), round(0.20 * kd, 3), round(0.60 * kd, 3),
        0.20, "ring", [ri], False, "ASSUMED RV-1 value x d ratio")
    add("A03b bulkheads and couplers", "airframe", round(0.35 * kA, 3), round(0.20 * kA, 3), round(0.50 * kA, 3), 1.05,
        "cyl", [ri, 0.02], False, "ASSUMED RV-1 value x d^2 ratio")
    if geo["legs"] == "deployable":
        add("A04 landing legs x4 (deployable)", "airframe", 1.20, 0.80, 2.00, -0.05, "legring", [0.22], False,
            "ASSUMED (r_foot 0.40 m, stroke >= 0.10 m)")
    add("A05 avionics (FC, IMU, GNSS, LiDAR, radio)", "airframe", 0.40, 0.25, 0.60, 1.15, "point", [], False,
        "ASSUMED")
    add("A06 battery", "airframe", 0.35, 0.20, 0.50, 1.10, "point", [], False, "ASSUMED")
    add("A07 backup recovery parachute + deployment", "airframe", 0.75, 0.50, 1.00, 1.45, "cyl", [0.055, 0.3],
        False, "ASSUMED")
    add("A08 harness, fasteners, misc", "airframe", 0.50, 0.30, 0.80, 0.85, "tube", [ri, ri - 0.005, 1.6], False,
        "ASSUMED")
    if (fins if fins is not None else geo.get("n_fins", 0) > 0):
        add("A10 aft fins x4 (span 0.12 m, chords 0.20/0.10 m, 3 mm GF/PETG) or leg-fin panels", "airframe", 0.30,
            0.15, 0.50, 0.12, "ring", [0.10], False, "ASSUMED (coast stability, see REPORT)")
    if descent_option == "drogue":
        add("A09 nose drogue + ejection + release + swivel", "airframe", 0.35, 0.25, 0.50, 1.70, "point", [],
            False, "ASSUMED (0.9 m drogue class)")
    elif descent_option == "rcs":
        add("P13 N2O vapour RCS: 6 valves, lines, nozzles", "propulsion", 0.60, 0.40, 0.90, 1.20, "ring", [0.05],
            False, "ASSUMED (6 x 30-60 g solenoid valves + lines)")
    if roll_rcs and descent_option != "rcs":
        add("P14 roll RCS: 2 NC solenoids, 4 nozzles (2 couples), tee, lines from the tank ullage", "propulsion",
            0.25, 0.15, 0.40, geo["tank_z_bot_inner"] + L_in + 0.03, "ring", [geo["d"] / 2 - geo["wall"]], False,
            "ASSUMED (gnc.json v1 roll-RCS estimate ~0.25 kg; valve masses TO-QUOTE; added in ledger v3 rev b)")
    return it


def mass_ledger(geo, descent_option="none", tank_V=None):
    """Return list of item dicts: name, owner, m, m_min, m_max, z, shape, dims, gimballed, tag."""
    V = geo["tank_V"] if tank_V is None else tank_V
    A_in = np.pi * geo["tank_D_in"] ** 2 / 4
    L_in = V / A_in
    Do = geo["tank_D_in"] + 2 * geo["tank_wall"]
    A_wall = np.pi / 4 * (Do ** 2 - geo["tank_D_in"] ** 2)
    L_tube = L_in + 0.05
    m_tube = A_wall * L_tube * 2700.0
    m_tank = m_tube + 0.30 + 0.15
    z_tank_c = geo["tank_z_bot_inner"] + L_in / 2
    case_L = 0.37
    m_case = np.pi / 4 * (0.0635 ** 2 - 0.05715 ** 2) * case_L * 2700.0
    zp = geo["z_pivot"]
    it = []

    def add(name, owner, m, mmin, mmax, z, shape, dims, gimb, tag):
        it.append(dict(name=name, owner=owner, m=m, m_min=mmin, m_max=mmax, z=z, shape=shape,
                       dims=dims, gimballed=gimb, tag=tag))
    # ---- propulsion (engine team) ----
    add("P01 aft closure + nozzle holder + graphite throat insert", "propulsion", 0.35, 0.25, 0.50,
        0.005, "cyl", [0.032, 0.07], True, "ASSUMED (no CAD yet; Mechanical to replace)")
    add("P02 combustion case 6061-T6 63.5x3.175 mm, L 0.37 m", "propulsion", round(m_case, 3), 0.45, 0.75,
        0.215, "tube", [0.03175, 0.02858, case_L], True,
        "DERIVED baseline case_v0 tube x 0.37 m x 2700 kg/m3")
    add("P03 liner and insulators", "propulsion", 0.14, 0.08, 0.22, 0.215, "tube",
        [0.0286, 0.026, 0.35], True, "ASSUMED")
    add("P04 injector bulkhead + pintle body", "propulsion", 0.35, 0.25, 0.50, 0.42, "cyl",
        [0.032, 0.05], True, "ASSUMED")
    add("P05 pintle throttle actuator (on engine head)", "propulsion", 0.15, 0.10, 0.30, 0.47, "point",
        [], True, "ASSUMED (pintle actuator rides on the gimballed head)")
    add("P06 gimbal ring, pins, bearings", "propulsion", 0.25, 0.15, 0.40, zp, "ring",
        [0.055], False, "ASSUMED")
    add("P07 thrust mount / thrust plate (airframe interface)", "propulsion", 0.25, 0.15, 0.40, 0.47,
        "cyl", [0.06, 0.02], False, "ASSUMED")
    add("P08 TVC actuators x2 + pushrods + brackets", "propulsion", 0.30, 0.15, 0.45, 0.36, "ring",
        [0.045], False, "ASSUMED (2 HV hobby servos class)")
    add("P09 NC main isolation valve + actuator", "propulsion", 0.35, 0.20, 0.60, 0.55, "point", [],
        False, "ASSUMED")
    add("P10 flex hose, fittings, feed line", "propulsion", 0.20, 0.12, 0.35, 0.51, "point", [], False,
        "ASSUMED")
    add("P11 N2O tank (tube, 2 bulkheads, fittings, relief, sensors)", "propulsion", round(m_tank, 3),
        round(0.85 * m_tank, 3), round(1.25 * m_tank, 3), z_tank_c, "tube",
        [Do / 2, geo["tank_D_in"] / 2, L_tube], False,
        "DERIVED baseline tank_v0 tube (101.6x3.175, 6061) + 0.45 kg closures/fittings ASSUMED")
    add("P12 engine ECU, Pc/Ptank/Ttank sensors, igniter electronics", "propulsion", 0.25, 0.15, 0.40,
        0.58, "point", [], False, "ASSUMED")
    # ---- airframe (Lauty) ----
    add("A01 body tube 126 mm OD, PETG 2.5 mm wall, 1.70 m", "airframe", 2.09, 1.00, 2.80, 0.85, "tube",
        [0.063, 0.0605, 1.70], False, "ASSUMED (printed PETG 1270 kg/m3; CF/GF tube at min)")
    add("A02 nose cone + GNSS antenna", "airframe", 0.35, 0.25, 0.50, 1.80, "cone", [0.063, 0.30],
        False, "ASSUMED")
    add("A03a aft thrust ring + leg mounts", "airframe", 0.35, 0.20, 0.60, 0.20, "ring", [0.06], False,
        "ASSUMED")
    add("A03b bulkheads and couplers", "airframe", 0.35, 0.20, 0.50, 1.05, "cyl", [0.06, 0.02], False,
        "ASSUMED")
    if geo["legs"] == "deployable":
        add("A04 landing legs x4 (deployable)", "airframe", 1.20, 0.80, 2.00, -0.05, "legring",
            [0.22], False, "ASSUMED (r_foot 0.40 m, stroke >= 0.10 m)")
    add("A05 avionics (FC, IMU, GNSS, LiDAR, radio)", "airframe", 0.40, 0.25, 0.60, 1.15, "point", [],
        False, "ASSUMED")
    add("A06 battery", "airframe", 0.35, 0.20, 0.50, 1.10, "point", [], False, "ASSUMED")
    add("A07 backup recovery parachute + deployment", "airframe", 0.75, 0.50, 1.00, 1.45, "cyl",
        [0.055, 0.3], False, "ASSUMED")
    add("A08 harness, fasteners, misc", "airframe", 0.50, 0.30, 0.80, 0.85, "tube", [0.06, 0.055, 1.6],
        False, "ASSUMED")
    if descent_option == "drogue":
        add("A09 nose drogue + ejection + release", "airframe", 0.35, 0.25, 0.50, 1.70, "point", [], False,
            "ASSUMED (0.9 m drogue class)")
    elif descent_option == "rcs":
        add("P13 N2O vapour RCS: 6 valves, lines, nozzles", "propulsion", 0.60, 0.40, 0.90, 1.20, "ring",
            [0.05], False, "ASSUMED (6 x 30-60 g solenoid valves + lines)")
    elif descent_option == "flaps":
        add("A09 nose drag flaps (4) + actuators", "airframe", 0.80, 0.50, 1.20, 1.62, "ring", [0.07],
            False, "ASSUMED")
    return it


def item_inertia(item, legs_deployed=True):
    """(I_transverse about own CG, I_roll about the vehicle axis) for one item."""
    m, s, d = item["m"], item["shape"], item["dims"]
    if s == "point":
        return 0.0, 0.0
    if s == "cyl":
        r, L = d
        return m * (3 * r * r + L * L) / 12.0, 0.5 * m * r * r
    if s == "tube":
        ro, ri, L = d
        return m * (3 * (ro * ro + ri * ri) + L * L) / 12.0, 0.5 * m * (ro * ro + ri * ri)
    if s == "ring":
        r = d[0]
        return 0.5 * m * r * r, m * r * r
    if s == "cone":
        r, L = d   # thin conical shell about its own CG (approx.)
        return m * (r * r / 4.0 + L * L / 18.0), 0.5 * m * r * r
    if s == "given":
        # inertia supplied by the owner (e.g. mechanical.json): dims = [I_transverse about own CG, I_roll]
        return d[0], d[1]
    if s == "legring":
        r = d[0] if legs_deployed else 0.07
        return 0.5 * m * r * r + m * 0.3 ** 2 / 12.0, m * r * r
    raise ValueError(s)


def fixed_sums(ledger, legs_deployed=True):
    """Return dict with non-gimballed (S_*) and gimballed dry (G_*) sums about the datum."""
    out = {}
    for key, sel in (("S", False), ("G", True)):
        m = sum(i["m"] for i in ledger if i["gimballed"] == sel)
        s1 = sum(i["m"] * i["z"] for i in ledger if i["gimballed"] == sel)
        s2 = sum(i["m"] * i["z"] ** 2 + item_inertia(i, legs_deployed)[0] for i in ledger
                 if i["gimballed"] == sel)
        sr = sum(item_inertia(i, legs_deployed)[1] for i in ledger if i["gimballed"] == sel)
        out[key] = (m, s1, s2, sr)
    return out


# mass-property parameter vector (for numba)
(MP_SM, MP_S1, MP_S2, MP_SR, MP_GM, MP_G1, MP_G2, MP_GR, MP_TZB, MP_TAIN, MP_TLIN,
 MP_GZ0, MP_GL, MP_GDO, MP_RHOF, MP_ZP) = range(16)
N_MP = 16


def build_mp(geo, ledger, legs_deployed=True, tank_V=None):
    fs = fixed_sums(ledger, legs_deployed)
    V = geo["tank_V"] if tank_V is None else tank_V
    mp = np.zeros(N_MP)
    mp[MP_SM], mp[MP_S1], mp[MP_S2], mp[MP_SR] = fs["S"]
    mp[MP_GM], mp[MP_G1], mp[MP_G2], mp[MP_GR] = fs["G"]
    mp[MP_TZB] = geo["tank_z_bot_inner"]
    mp[MP_TAIN] = np.pi * geo["tank_D_in"] ** 2 / 4
    mp[MP_TLIN] = V / mp[MP_TAIN]
    mp[MP_GZ0] = geo["grain_z0"]
    mp[MP_GL] = geo["grain_L"]
    mp[MP_GDO] = geo["grain_Do"]
    mp[MP_RHOF] = geo["rho_f"]
    mp[MP_ZP] = geo["z_pivot"]
    return mp


@njit(cache=True)
def grain_port(mp, m_fuel):
    Do = mp[MP_GDO]
    A = m_fuel / (mp[MP_RHOF] * mp[MP_GL])
    dp2 = Do * Do - 4.0 * A / np.pi
    if dp2 < 1e-6:
        dp2 = 1e-6
    return np.sqrt(dp2)


@njit(cache=True)
def massprops(mp, m_liq, m_vap, rho_l, m_fuel, out):
    """out = [m, z_cg, I_t (about CG), I_roll, m_g, z_g (gimballed CG), I_g (own CG, transverse), D_port]."""
    # liquid column (settled at the tank bottom)
    A = mp[MP_TAIN]
    h = m_liq / (rho_l * A) if rho_l > 1.0 else 0.0
    Lin = mp[MP_TLIN]
    if h > Lin:
        h = Lin
    zb = mp[MP_TZB]
    r_t = np.sqrt(A / np.pi)
    zl = zb + 0.5 * h
    Il = m_liq * (3 * r_t * r_t + h * h) / 12.0
    # vapour in the ullage
    zv = zb + h + 0.5 * (Lin - h)
    Iv = m_vap * (3 * r_t * r_t + (Lin - h) ** 2) / 12.0
    # grain
    Dp = grain_port(mp, m_fuel)
    zg_f = mp[MP_GZ0] + 0.5 * mp[MP_GL]
    Ig_f = m_fuel * (3 * (mp[MP_GDO] ** 2 + Dp * Dp) / 4.0 + mp[MP_GL] ** 2) / 12.0
    Ir_f = 0.5 * m_fuel * (mp[MP_GDO] ** 2 + Dp * Dp) / 4.0
    # gimballed subassembly (dry engine + fuel)
    mg = mp[MP_GM] + m_fuel
    s1g = mp[MP_G1] + m_fuel * zg_f
    s2g = mp[MP_G2] + m_fuel * zg_f * zg_f + Ig_f
    zg = s1g / mg
    Ig = s2g - mg * zg * zg
    # whole vehicle
    m = mp[MP_SM] + mg + m_liq + m_vap
    s1 = mp[MP_S1] + s1g + m_liq * zl + m_vap * zv
    s2 = mp[MP_S2] + s2g + m_liq * zl * zl + Il + m_vap * zv * zv + Iv
    zc = s1 / m
    It = s2 - m * zc * zc
    Ir = mp[MP_SR] + mp[MP_GR] + Ir_f
    out[0] = m; out[1] = zc; out[2] = It; out[3] = Ir
    out[4] = mg; out[5] = zg; out[6] = Ig; out[7] = Dp


def ledger_table(ledger):
    rows = []
    for i in ledger:
        rows.append(dict(item=i["name"], owner=i["owner"], m_kg=i["m"], m_min_kg=i["m_min"],
                         m_max_kg=i["m_max"], z_m=round(i["z"], 4), gimballed=i["gimballed"], tag=i["tag"]))
    return rows
