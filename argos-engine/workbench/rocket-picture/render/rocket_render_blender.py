# ARGOS H1 vehicle concept render: the REAL engine CAD v3.5.1 (GLB) placed in the ASSUMED GNC
# reference airframe RV-1c. Blender 4.0 Cycles (CPU). Visualisation only: not a drawing, not a
# tolerance or fabrication source, not a physical approval.
#
# Status of every element (also written to the meta JSON):
#   engine            real CAD v3.5.1 (frozen GLB, BOM material per part; display tessellation)
#   N2O tank          concept: 6061 tube 101.6 x 3.175 mm, internal 0.445 m; overall 0.50 m ESTIMATE;
#                     placed z 0.58-1.08 m (moved up: v3d had 0.55-0.995 m, overlapping the CAD
#                     engine top at z 0.558 m)
#   airframe, nose, fins, legs, bays, bulkheads, tank centering rings
#                     ASSUMED (GNC reference vehicle RV-1c, interfaces/gnc.json + gncsim/vehicle.py);
#                     not Lauty's airframe design
#
# Frames: GLB metres +Y up; the glTF importer gives Blender +Z up = the CAD engine frame (+Z toward
# the injector, origin at the gimbal pivot). Vehicle frame = Blender world: +Z toward the nose,
# z = 0 at the aft datum (body tube aft end); the engine is translated by +Z_PIVOT. Engine clocking
# about the axis is CAD X = vehicle X (ASSUMED, the airframe clocking is not defined). Azimuth is
# measured from +X toward +Y (BOM convention: ENG-BL-06 "at az 112").
#
# Usage (one Blender process at a time; caller sets nice and threads):
#   blender -b -t 2 -P rocket_render_blender.py -- --glb GLB --bom BOM --view exterior|cutaway
#           --out RAW.png --meta META.json [--w 1000 --h 1800 --ss 1.0 --spp 64]
# Engine import and BOM material mapping are copied from engine/07-datasheet/gen/render_views_blender.py.
import bpy, bmesh, sys, json, math, time, hashlib, argparse
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv[sys.argv.index('--') + 1:]
ap = argparse.ArgumentParser()
ap.add_argument('--glb', required=True)
ap.add_argument('--bom', required=True)
ap.add_argument('--view', required=True, choices=['exterior', 'cutaway'])
ap.add_argument('--out', required=True)
ap.add_argument('--meta', required=True)
ap.add_argument('--w', type=int, default=1000)
ap.add_argument('--h', type=int, default=1800)
ap.add_argument('--ss', type=float, default=1.0, help='render at ss x (w, h); post-script downsamples')
ap.add_argument('--spp', type=int, default=64)
ap.add_argument('--exposure', type=float, default=0.0)
ap.add_argument('--no-render', action='store_true', help='rebuild the scene and write the meta (anchors) only')
args = ap.parse_args(argv)
T0 = time.time()

# ------------------------------------------------------------------ inputs and constants (SI, m)
Z_PIVOT = 0.203          # gnc.json reference_vehicle.gimballed_subassembly.v.z_pivot_m
R_OUT, R_IN = 0.073, 0.070   # body 146 mm OD, 140 mm bay ID (2 x 3 mm PETG wall ASSUMED)
Z_BODY = (0.0, 1.70)     # body tube from the aft datum
NOSE_L = 0.30            # tangent ogive, tip at z 2.00
NOSE_T = 0.003           # nose wall drawn as the body wall (ASSUMED)
# fins: gncsim/vehicle.py fin_cr 0.20, fin_ct 0.10, fin_span 0.12, fin_sweep 0.10 (LE), fin_z_le 0.20; 3 mm
FIN_CR, FIN_CT, FIN_SPAN, FIN_SWEEP, FIN_ZLE, FIN_T = 0.20, 0.10, 0.12, 0.10, 0.20, 0.003
FIN_AZ = (0.0, 90.0, 180.0, 270.0)            # ASSUMED clocking (not defined)
# legs: gncsim/vehicle.py n_legs 4, leg_d 0.020, leg_L 0.52, r_foot 0.40, z_foot -0.25 (foot plane)
LEG_D, LEG_L, R_FOOT, Z_FOOT = 0.020, 0.52, 0.40, -0.25
LEG_AZ = (45.0, 135.0, 225.0, 315.0)          # between the fins, ASSUMED
R_HINGE = 0.080                               # hinge axis just outside the wall (drawing choice)
Z_HINGE = Z_FOOT + math.sqrt(LEG_L ** 2 - (R_FOOT - R_HINGE) ** 2)   # = 0.160 m (DERIVED from leg_L)
Z_DAMP, DAMP_FRAC = 0.40, 0.55                # damper strut top mount / attach fraction: drawing choice
# N2O tank concept (lead): 6061 tube 101.6 OD x 3.175 wall, internal length 0.445 m, flat bulkheads
TANK_RO, TANK_T, TANK_Z0, TANK_Z1, TANK_LINT = 0.0508, 0.003175, 0.58, 1.08, 0.445
TANK_BH = (TANK_Z1 - TANK_Z0 - TANK_LINT) / 2.0    # 0.0275 m each: ESTIMATE (thickness not designed)
# camera (same for both views)
CAM_AZ, CAM_EL, LENS_MM, SENSOR_MM = 90.0, 12.0, 85.0, 36.0
CUT_HALF = 37.0          # cutaway: shell removed for az in CAM_AZ +/- CUT_HALF below Z_STEP
CUT_HALF_UP = 70.0       # ... and CAM_AZ +/- CUT_HALF_UP above Z_STEP (stepped cut)
Z_STEP = 0.44            # above the leg damper brackets (z 0.385-0.415)
BG_SRGB = (0x15, 0x18, 0x1c)


def sha256_16(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()[:16]


def srgb_to_lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


GLB_SHA, BOM_SHA = sha256_16(args.glb), sha256_16(args.bom)
bom = json.load(open(args.bom))
PN_MAT = {r['pn']: r['material'] for r in bom['lines']}

# (base RGB linear, metallic, roughness) per BOM material code (copied from render_views_blender.py)
LOOK = {
    'AL6061-T6': ((0.78, 0.79, 0.81), 1.0, 0.42),
    'AL7075-T6': ((0.72, 0.73, 0.76), 1.0, 0.40),
    'SS316L': ((0.62, 0.62, 0.64), 1.0, 0.25),
    'SS304': ((0.62, 0.62, 0.64), 1.0, 0.25),
    'SS17-4PH-H1150': ((0.58, 0.58, 0.60), 1.0, 0.30),
    'SS17-4PH-H900': ((0.58, 0.58, 0.60), 1.0, 0.30),
    'SS-SPRING': ((0.50, 0.50, 0.52), 1.0, 0.35),
    'STEEL': ((0.45, 0.46, 0.48), 1.0, 0.38),
    'IN718': ((0.56, 0.52, 0.46), 1.0, 0.30),
    'NDFEB': ((0.70, 0.70, 0.72), 1.0, 0.25),
    'PHENOLIC': ((0.36, 0.20, 0.09), 0.0, 0.55),
    'CARBON-PHENOLIC': ((0.07, 0.07, 0.07), 0.0, 0.50),
    'GRAPHITE-ISO': ((0.13, 0.13, 0.14), 0.0, 0.70),
    'FLEX-GRAPHITE-OI': ((0.20, 0.20, 0.21), 0.3, 0.60),
    'G11': ((0.55, 0.60, 0.35), 0.0, 0.50),
    'ABS': ((0.86, 0.84, 0.76), 0.0, 0.55),
    'PETG': ((0.20, 0.45, 0.75), 0.0, 0.30),
    'PTFE': ((0.93, 0.93, 0.91), 0.0, 0.45),
    'PCTFE': ((0.90, 0.92, 0.93), 0.0, 0.35),
    'ELASTOMER-PU': ((0.12, 0.12, 0.12), 0.0, 0.70),
    'MICA': ((0.55, 0.45, 0.30), 0.0, 0.50),
    'COTS-MIXED': ((0.10, 0.11, 0.14), 0.0, 0.55),
}


def pn_of(name):
    return name.split('#')[0].split('.')[0]


def mat_code(pn):
    return PN_MAT.get(pn) or PN_MAT.get(pn.rstrip('ABF')) or PN_MAT.get(pn.rsplit('-', 1)[0]) or 'UNKNOWN'


def wbb(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]


MATS = {}


def pmat(name, col, metallic=0.0, rough=0.5, **inputs):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1.0)
    b.inputs['Metallic'].default_value = metallic
    b.inputs['Roughness'].default_value = rough
    for k, v in inputs.items():
        b.inputs[k.replace('_', ' ')].default_value = v
    MATS[name] = m
    return m


# ------------------------------------------------------------------ engine (real CAD)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=args.glb)
ENGINE = [o for o in scene.objects if o.type == 'MESH']
unknown = set()
for o in ENGINE:
    code = mat_code(pn_of(o.name))
    if code == 'UNKNOWN':
        unknown.add(pn_of(o.name))
    col, met, rough = LOOK.get(code, ((0.7, 0.7, 0.7), 0.5, 0.4))
    o.data.materials.clear()
    o.data.materials.append(pmat('ENG_' + code, col, met, rough))
for o in scene.objects:
    if o.parent is None:
        o.location.z += Z_PIVOT          # pivot at vehicle station z = 0.203 m
bpy.context.view_layer.update()
eng_lo = [min(wbb(o)[0][i] for o in ENGINE) for i in range(3)]
eng_hi = [max(wbb(o)[1][i] for o in ENGINE) for i in range(3)]
vent = [o for o in ENGINE if pn_of(o.name) == 'ENG-BL-06']
vlo, vhi = wbb(vent[0])
VENT_C = Vector([(vlo[i] + vhi[i]) / 2 for i in range(3)])
VENT_AZ = math.degrees(math.atan2(VENT_C.y, VENT_C.x)) % 360.0
VENT_RMAX = max(math.hypot(x, y) for x in (vlo[0], vhi[0]) for y in (vlo[1], vhi[1]))

# ------------------------------------------------------------------ airframe materials
PETG_BODY = pmat('PETG_body_lightgrey', (0.60, 0.61, 0.62), 0.0, 0.40)
PETG_FIN = pmat('GF_PETG_fin_charcoal', (0.035, 0.037, 0.040), 0.0, 0.45)
PETG_DARK = pmat('PETG_internal_darkgrey', (0.06, 0.062, 0.066), 0.0, 0.55)
CARBON = pmat('CFRP_leg', (0.018, 0.018, 0.020), 0.0, 0.28)
ALU = pmat('AL_fitting', (0.80, 0.80, 0.82), 1.0, 0.32)
RUBBER = pmat('foot_rubber', (0.012, 0.012, 0.012), 0.0, 0.85)
PCB = pmat('PCB_green', (0.015, 0.10, 0.04), 0.0, 0.35)
BLACK = pmat('black_module', (0.01, 0.01, 0.012), 0.0, 0.40)
BATT = pmat('battery_wrap', (0.02, 0.05, 0.13), 0.0, 0.38)
CHUTE_R = pmat('nylon_red', (0.42, 0.025, 0.02), 0.0, 0.80, Sheen_Weight=0.6)
CHUTE_O = pmat('nylon_orange', (0.80, 0.22, 0.015), 0.0, 0.80, Sheen_Weight=0.6)
TANK_M = pmat('AL6061_tank_brushed', (0.82, 0.83, 0.85), 1.0, 0.26, Anisotropic=0.75)
_nt = TANK_M.node_tree
_tg = _nt.nodes.new('ShaderNodeTangent')
_tg.direction_type = 'RADIAL'
_tg.axis = 'Z'
_nt.links.new(_tg.outputs['Tangent'], _nt.nodes['Principled BSDF'].inputs['Tangent'])
TANK_BH_M = pmat('AL6061_bulkhead_machined', (0.76, 0.77, 0.79), 1.0, 0.36)

# ------------------------------------------------------------------ geometry helpers
AIRFRAME = []     # (object, element key)


def add(ob, key):
    AIRFRAME.append((ob, key))
    return ob


def mesh_obj(name, bm, mat, smooth=False, angle=35.0):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
        me.use_auto_smooth = True
        me.auto_smooth_angle = math.radians(angle)
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


def revolve(name, prof, mat, az0=0.0, az1=360.0, seg=160, angle=35.0):
    """Revolve a closed (r, z) polygon about +Z over [az0, az1] deg; capped when partial."""
    span = az1 - az0
    full = span >= 359.999
    nseg = max(3, int(math.ceil(seg * span / 360.0)))
    nring = nseg if full else nseg + 1
    bm = bmesh.new()
    rings = []
    for k in range(nring):
        a = math.radians(az0 + span * k / nseg)
        ca, sa = math.cos(a), math.sin(a)
        rings.append([bm.verts.new((r * ca, r * sa, z)) for (r, z) in prof])
    n = len(prof)
    for k in range(nseg):
        A, B = rings[k], rings[(k + 1) % nring]
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new([A[i], A[j], B[j], B[i]])
    if not full:
        bm.faces.new(rings[0])
        bm.faces.new(rings[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-9, edges=bm.edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, mat, smooth=True, angle=angle)


def box(name, center, size, mat, az=0.0, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    ob = mesh_obj(name, bm, mat)
    ob.rotation_euler = (0.0, 0.0, math.radians(az))
    ob.location = Vector(center)
    if bevel > 0:
        md = ob.modifiers.new('bevel', 'BEVEL')
        md.width = bevel
        md.segments = 2
        md.limit_method = 'ANGLE'
    return ob


def cyl(name, p0, p1, r, mat, seg=32, bevel=0.0):
    p0, p1 = Vector(p0), Vector(p1)
    v = p1 - p0
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r, radius2=r,
                          depth=v.length)
    ob = mesh_obj(name, bm, mat, smooth=True, angle=40.0)
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = v.normalized().to_track_quat('Z', 'Y')
    ob.location = (p0 + p1) / 2
    if bevel > 0:
        md = ob.modifiers.new('bevel', 'BEVEL')
        md.width = bevel
        md.segments = 4
        md.limit_method = 'ANGLE'
    return ob


def radial(az, r, z):
    a = math.radians(az)
    return Vector((r * math.cos(a), r * math.sin(a), z))


CUT = args.view == 'cutaway'
SHELL_AZ = (CAM_AZ + CUT_HALF_UP, CAM_AZ - CUT_HALF_UP + 360.0) if CUT else (0.0, 360.0)
LOW_AZ = (CAM_AZ + CUT_HALF, CAM_AZ - CUT_HALF + 360.0)

# body tube (ASSUMED RV-1c): 146 OD x 3 mm, z 0-1.70
hole_r = max(vhi[2] - vlo[2], 0.010) / 2 + 0.0015
if CUT:
    add(revolve('AF_body_tube_low', [(R_IN, Z_BODY[0]), (R_OUT, Z_BODY[0]), (R_OUT, Z_STEP), (R_IN, Z_STEP)],
                PETG_BODY, *LOW_AZ, seg=192), 'body_tube')
    add(revolve('AF_body_tube_up', [(R_IN, Z_STEP), (R_OUT, Z_STEP), (R_OUT, Z_BODY[1]), (R_IN, Z_BODY[1])],
                PETG_BODY, *SHELL_AZ, seg=192), 'body_tube')
else:
    tube = add(revolve('AF_body_tube', [(R_IN, Z_BODY[0]), (R_OUT, Z_BODY[0]), (R_OUT, Z_BODY[1]),
                                        (R_IN, Z_BODY[1])], PETG_BODY, seg=192), 'body_tube')
    # vent clearance cut for the real CAD stub ENG-BL-06 (visual clearance only; hole spec TO-DEFINE)
    cutter = cyl('AF_vent_cutter', radial(VENT_AZ, 0.060, VENT_C.z), radial(VENT_AZ, 0.085, VENT_C.z), hole_r,
                 PETG_BODY, seg=32)
    cutter.hide_render = True
    cutter.display_type = 'WIRE'
    bmod = tube.modifiers.new('vent_hole', 'BOOLEAN')
    bmod.operation = 'DIFFERENCE'
    bmod.solver = 'EXACT'
    bmod.object = cutter

# tangent ogive nose (ASSUMED RV-1c): L 0.30, base r 0.073, 3 mm wall
rho = (R_OUT ** 2 + NOSE_L ** 2) / (2 * R_OUT)
outer, inner = [], []
N = 72
for i in range(N + 1):
    x = NOSE_L * i / N
    r = math.sqrt(max(rho * rho - x * x, 0.0)) - (rho - R_OUT)
    r = max(r, 0.0)
    outer.append((r, Z_BODY[1] + x))
    drdx = -x / math.sqrt(max(rho * rho - x * x, 1e-12))
    nn = math.sqrt(1 + drdx * drdx)
    ri, zi = r - NOSE_T / nn, Z_BODY[1] + x + NOSE_T * drdx / nn
    if ri > 0.002:
        inner.append((ri, zi))
nose = add(revolve('AF_nose_ogive', outer + inner[::-1], PETG_BODY, *SHELL_AZ, seg=192), 'nose')

# fins x4 (ASSUMED RV-1c), trailing edge at z 0; in the cutaway the camera-side fin is omitted
for az in FIN_AZ:
    if CUT and abs(((az - CAM_AZ) + 180) % 360 - 180) < CUT_HALF + 1e-6:
        continue
    a = math.radians(az)
    e, tvec = Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a), math.cos(a), 0))
    prof = [(R_OUT - 0.0015, 0.0), (R_OUT - 0.0015, FIN_ZLE), (R_OUT + FIN_SPAN, FIN_ZLE - FIN_SWEEP),
            (R_OUT + FIN_SPAN, FIN_ZLE - FIN_SWEEP - FIN_CT)]
    bm = bmesh.new()
    vs = [bm.verts.new(e * r + Vector((0, 0, z)) + tvec * s * FIN_T / 2) for s in (-1, 1) for (r, z) in prof]
    bm.faces.new(vs[0:4])
    bm.faces.new(vs[4:8][::-1])
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new([vs[i], vs[4 + i], vs[4 + j], vs[j]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    f = mesh_obj('AF_fin_%03d' % az, bm, PETG_FIN)
    md = f.modifiers.new('bevel', 'BEVEL')
    md.width = 0.0012
    md.segments = 2
    md.limit_method = 'ANGLE'
    add(f, 'fins')

# landing legs x4, deployed (ASSUMED RV-1c): main strut leg_d 20 mm from the hinge to the foot
# contact point (r 0.40, z -0.25); damper strut from a wall mount at z 0.40 to 55 % of the leg.
for az in LEG_AZ:
    tag = 'LEG_%03d' % az
    H, F = radial(az, R_HINGE, Z_HINGE), radial(az, R_FOOT, Z_FOOT)
    u = (F - H).normalized()
    add(cyl(tag + '_tube', H, F, LEG_D / 2, CARBON, seg=28), 'legs')
    add(cyl(tag + '_hinge_fitting', H - u * 0.012, H + u * 0.030, 0.0125, ALU, seg=28, bevel=0.002), 'legs')
    add(box(tag + '_hinge_bracket', radial(az, 0.0805, Z_HINGE), (0.016, 0.024, 0.036), ALU, az=az,
            bevel=0.0015), 'legs')
    add(cyl(tag + '_hinge_pin', H - Vector((-math.sin(math.radians(az)), math.cos(math.radians(az)), 0)) * 0.015,
            H + Vector((-math.sin(math.radians(az)), math.cos(math.radians(az)), 0)) * 0.015, 0.004, ALU, seg=16),
        'legs')
    add(cyl(tag + '_foot_fitting', F - u * 0.050, F - u * 0.012, 0.0125, ALU, seg=28, bevel=0.002), 'legs')
    add(cyl(tag + '_foot_pad', Vector((F.x, F.y, Z_FOOT + 0.0001)), Vector((F.x, F.y, Z_FOOT + 0.013)), 0.035,
            RUBBER, seg=40, bevel=0.003), 'legs')
    B = radial(az, 0.0835, Z_DAMP)
    P = H + (F - H) * DAMP_FRAC
    w = (P - B)
    add(box(tag + '_damper_bracket', radial(az, 0.0795, Z_DAMP), (0.014, 0.022, 0.030), ALU, az=az,
            bevel=0.0015), 'legs')
    add(cyl(tag + '_damper_body', B, B + w * 0.56, 0.0085, BLACK, seg=24, bevel=0.0015), 'legs')
    add(cyl(tag + '_damper_rod', B + w * 0.52, P, 0.0040, ALU, seg=16), 'legs')
    add(cyl(tag + '_damper_eye', P - u.cross(Vector((0, 0, 1))).normalized() * 0.013,
            P + u.cross(Vector((0, 0, 1))).normalized() * 0.013, 0.0075, ALU, seg=20), 'legs')

# N2O tank concept (never cut): tube + two flat bulkhead plugs, z 0.58-1.08
TANK_RI = TANK_RO - TANK_T
add(revolve('TANK_tube', [(TANK_RI, TANK_Z0), (TANK_RO, TANK_Z0), (TANK_RO, TANK_Z1), (TANK_RI, TANK_Z1)],
            TANK_M, seg=160), 'tank')
add(revolve('TANK_bulkhead_aft', [(0.0, TANK_Z0), (TANK_RI, TANK_Z0), (TANK_RI, TANK_Z0 + TANK_BH),
                                  (0.0, TANK_Z0 + TANK_BH)], TANK_BH_M, seg=128), 'tank')
add(revolve('TANK_bulkhead_fwd', [(0.0, TANK_Z1 - TANK_BH), (TANK_RI, TANK_Z1 - TANK_BH), (TANK_RI, TANK_Z1),
                                  (0.0, TANK_Z1)], TANK_BH_M, seg=128), 'tank')
# tank centering rings: placeholder for the tank mounts (TO-DEFINE), 6 mm, ASSUMED
for nm, z0 in (('AF_tank_ring_aft', 0.600), ('AF_tank_ring_fwd', 1.054)):
    add(revolve(nm, [(TANK_RO, z0), (R_IN - 0.0002, z0), (R_IN - 0.0002, z0 + 0.006), (TANK_RO, z0 + 0.006)],
                PETG_DARK, *SHELL_AZ, seg=160), 'tank_rings')
# bay bulkheads (ledger A03b, stations ASSUMED for this drawing), 6 mm
for nm, z0 in (('AF_bulkhead_tank_fwd', 1.090), ('AF_bulkhead_avionics_fwd', 1.364),
               ('AF_bulkhead_recovery_fwd', 1.600)):
    add(revolve(nm, [(0.0, z0), (R_IN - 0.0002, z0), (R_IN - 0.0002, z0 + 0.006), (0.0, z0 + 0.006)],
                PETG_DARK, *SHELL_AZ, seg=160), 'bulkheads')
# avionics + battery bay (ledger A05/A06 ASSUMED; shifted forward to clear the tank): z 1.096-1.364
add(box('AV_sled', (0.0, -0.0045, 1.2295), (0.110, 0.003, 0.255), PETG_DARK, bevel=0.001), 'avionics')
add(box('AV_battery', (0.0, 0.0145, 1.158), (0.070, 0.035, 0.090), BATT, bevel=0.003), 'battery')
add(box('AV_fc_imu_board', (0.0, 0.0085, 1.258), (0.085, 0.0016, 0.068), PCB, bevel=0.0004), 'avionics')
for dx in (-0.036, 0.036):
    for dz in (-0.028, 0.028):
        add(cyl('AV_standoff', (dx, -0.003, 1.258 + dz), (dx, 0.0077, 1.258 + dz), 0.0022, ALU, seg=12), 'avionics')
add(box('AV_fc_mcu', (-0.012, 0.0108, 1.262), (0.022, 0.003, 0.022), BLACK, bevel=0.0005), 'avionics')
add(box('AV_imu', (0.020, 0.0104, 1.246), (0.014, 0.0025, 0.014), BLACK, bevel=0.0005), 'avionics')
add(box('AV_radio', (-0.026, 0.0060, 1.325), (0.036, 0.018, 0.034), ALU, bevel=0.001), 'avionics')
add(box('AV_gnss_rx', (0.024, 0.0040, 1.325), (0.030, 0.014, 0.030), BLACK, bevel=0.001), 'avionics')
add(box('AV_lidar', (0.0, 0.0050, 1.205), (0.030, 0.016, 0.020), BLACK, bevel=0.001), 'avionics')
# backup parachute in its bag (ledger A07 ASSUMED) z 1.38-1.58
add(cyl('CHUTE_backup', (0, 0, 1.376), (0, 0, 1.585), 0.054, CHUTE_R, seg=48, bevel=0.014), 'backup_chute')
# nose drogue + ejection (ledger A09 ASSUMED) around z 1.70
add(cyl('EJ_charge_canister', (0.030, 0.0, 1.606), (0.030, 0.0, 1.630), 0.011, BLACK, seg=20, bevel=0.002),
    'drogue')
add(cyl('CHUTE_drogue', (0, 0, 1.628), (0, 0, 1.775), 0.043, CHUTE_O, seg=48, bevel=0.012), 'drogue')

# ------------------------------------------------------------------ floor, world, lights
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=20.0)
floor = mesh_obj('FLOOR', bm, pmat('floor_tmp', (0, 0, 0)))
floor.location = (0, 0, Z_FOOT)
fm = bpy.data.materials.new('FLOOR')
fm.use_nodes = True
nt = fm.node_tree
fb = nt.nodes['Principled BSDF']
fb.inputs['Base Color'].default_value = (0.020, 0.022, 0.026, 1)
fb.inputs['Roughness'].default_value = 0.50
fb.inputs['Specular IOR Level'].default_value = 0.20
tr = nt.nodes.new('ShaderNodeBsdfTransparent')
mix = nt.nodes.new('ShaderNodeMixShader')
tc = nt.nodes.new('ShaderNodeTexCoord')
vm = nt.nodes.new('ShaderNodeVectorMath')
vm.operation = 'MULTIPLY'
vm.inputs[1].default_value = (1.0, 1.0, 0.0)
ln = nt.nodes.new('ShaderNodeVectorMath')
ln.operation = 'LENGTH'
mr = nt.nodes.new('ShaderNodeMapRange')
mr.interpolation_type = 'SMOOTHSTEP'
mr.inputs['From Min'].default_value = 0.6
mr.inputs['From Max'].default_value = 7.0
nt.links.new(tc.outputs['Object'], vm.inputs[0])
nt.links.new(vm.outputs['Vector'], ln.inputs[0])
nt.links.new(ln.outputs['Value'], mr.inputs['Value'])
nt.links.new(mr.outputs['Result'], mix.inputs['Fac'])
nt.links.new(fb.outputs['BSDF'], mix.inputs[1])
nt.links.new(tr.outputs['BSDF'], mix.inputs[2])
nt.links.new(mix.outputs['Shader'], nt.nodes['Material Output'].inputs['Surface'])
floor.data.materials.clear()
floor.data.materials.append(fm)

world = bpy.data.worlds.new('w')
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (*[srgb_to_lin(c) for c in BG_SRGB], 1.0)
bg.inputs['Strength'].default_value = 1.5

TARGET = Vector((0.0, 0.0, 0.85))
LIGHTS = []


def area(name, az, el, dist, sx, sy, energy, aim=TARGET):
    l = bpy.data.lights.new(name, 'AREA')
    l.shape = 'RECTANGLE'
    l.size, l.size_y = sx, sy
    l.energy = energy
    ob = bpy.data.objects.new(name, l)
    a, e = math.radians(az), math.radians(el)
    ob.location = aim + Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e))) * dist
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = (aim - ob.location).to_track_quat('-Z', 'Y')
    ob.visible_camera = False
    scene.collection.objects.link(ob)
    LIGHTS.append({'name': name, 'az_deg': az, 'el_deg': el, 'dist_m': dist, 'size_m': [sx, sy], 'W': energy})
    return ob


area('key', CAM_AZ - 50, 32, 3.4, 1.8, 1.8, 170)      # camera-left, above
area('fill', CAM_AZ + 62, 12, 4.0, 2.4, 2.4, 55)      # camera-right, low
area('rim_left', CAM_AZ + 180 + 50, 28, 3.0, 0.6, 3.0, 110)
area('rim_right', CAM_AZ + 180 - 50, 28, 3.0, 0.6, 3.0, 110)
area('top', 0, 90, 3.6, 2.5, 2.5, 60, aim=Vector((0, 0, 0.9)))
if CUT:   # strip softbox in front of the opening (invisible to the camera): lights the bays, streak on metals
    area('front_strip', CAM_AZ, 4, 0.65, 0.22, 1.7, 7, aim=Vector((0, 0, 0.75)))

# ------------------------------------------------------------------ camera (fit the exterior envelope)
W, H = int(round(args.w * args.ss)), int(round(args.h * args.ss))
scene.render.resolution_x, scene.render.resolution_y = W, H
scene.render.resolution_percentage = 100
cd = bpy.data.cameras.new('cam')
cd.type = 'PERSP'
cd.lens = LENS_MM
cd.sensor_fit = 'VERTICAL'
cd.sensor_height = SENSOR_MM
cd.clip_start, cd.clip_end = 0.05, 100.0
cam = bpy.data.objects.new('cam', cd)
scene.collection.objects.link(cam)
scene.camera = cam
bpy.context.view_layer.update()

# envelope points: exterior airframe vertices (cutaway geometry is a subset) + engine bbox corners
dg = bpy.context.evaluated_depsgraph_get()
pts = []
for ob, key in AIRFRAME:
    if key == 'legs':
        pts += [ob.matrix_world @ v.co for v in ob.data.vertices]
for z in (Z_BODY[0], Z_BODY[1]):
    pts += [radial(a, R_OUT, z) for a in range(0, 360, 5)]
for x in (eng_lo[0], eng_hi[0]):
    for y in (eng_lo[1], eng_hi[1]):
        for z in (eng_lo[2], eng_hi[2]):
            pts.append(Vector((x, y, z)))
# exterior fins (the cutaway omits one; keep the framing identical for both views)
for az in FIN_AZ:
    pts += [radial(az, R_OUT + FIN_SPAN, 0.0), radial(az, R_OUT + FIN_SPAN, FIN_ZLE - FIN_SWEEP)]
pts += [Vector((0, 0, Z_BODY[1] + NOSE_L))]

V_BAND = (0.085, 0.905)        # content band in normalised height (bottom 0 -> top 1)
U_BAND = (0.06, 0.94)
dvec = Vector((math.cos(math.radians(CAM_EL)) * math.cos(math.radians(CAM_AZ)),
               math.cos(math.radians(CAM_EL)) * math.sin(math.radians(CAM_AZ)),
               math.sin(math.radians(CAM_EL))))
aim = Vector((0.0, 0.0, 0.875))
D = 6.5
for it in range(8):
    cam.location = aim + dvec * D
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = (-dvec).to_track_quat('-Z', 'Y')
    cd.shift_x = cd.shift_y = 0.0
    bpy.context.view_layer.update()
    uv = [world_to_camera_view(scene, cam, p) for p in pts]
    us, vs = [q.x for q in uv], [q.y for q in uv]
    s = max((max(vs) - min(vs)) / (V_BAND[1] - V_BAND[0]), (max(us) - min(us)) / (U_BAND[1] - U_BAND[0]))
    D *= s
    if abs(s - 1) < 1e-4:
        break
cam.location = aim + dvec * D
bpy.context.view_layer.update()
uv = [world_to_camera_view(scene, cam, p) for p in pts]
us, vs = [q.x for q in uv], [q.y for q in uv]
L = max(W, H)
cd.shift_x = ((max(us) + min(us)) / 2 - 0.5) * W / L
cd.shift_y = ((max(vs) + min(vs)) / 2 - sum(V_BAND) / 2) * H / L
bpy.context.view_layer.update()
uv = [world_to_camera_view(scene, cam, p) for p in pts]
fit = {'u': [min(q.x for q in uv), max(q.x for q in uv)], 'v': [min(q.y for q in uv), max(q.y for q in uv)]}

# ------------------------------------------------------------------ render settings
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = args.spp
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.01
scene.cycles.use_denoising = False   # this Blender 4.0.2 build has no OpenImageDenoise
scene.cycles.max_bounces = 8
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 4
scene.cycles.transparent_max_bounces = 8
scene.cycles.sample_clamp_indirect = 3.0
scene.cycles.blur_glossy = 1.0
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.image_settings.color_depth = '8'
scene.view_settings.view_transform = 'Filmic'
looks = [i.identifier for i in scene.view_settings.bl_rna.properties['look'].enum_items]
scene.view_settings.look = 'Filmic - Medium High Contrast' if 'Filmic - Medium High Contrast' in looks else 'None'
scene.view_settings.exposure = args.exposure
scene.render.filepath = args.out

# ------------------------------------------------------------------ projection + label anchors
M = cam.matrix_world.copy()
R3 = M.to_3x3()
C = M.translation.copy()
f_px = LENS_MM / SENSOR_MM * H


def proj_closed(p):
    q = R3.transposed() @ (Vector(p) - C)
    x, y = q.x / -q.z, q.y / -q.z
    return [W / 2 + f_px * x - cd.shift_x * L, H / 2 - f_px * y + cd.shift_y * L]


def proj_blender(p):
    q = world_to_camera_view(scene, cam, Vector(p))
    return [q.x * W, (1.0 - q.y) * H], [q.x, q.y, q.z]


SKIP_HIT = {'AF_vent_cutter'}


def first_hit(p):
    """First object hit on the camera ray toward p (the hidden vent cutter is skipped)."""
    d = Vector(p) - C
    dist, dn = d.length, d.normalized()
    dgx = bpy.context.evaluated_depsgraph_get()
    travelled = 0.0
    for _ in range(8):
        hit, loc, nrm, idx, ob, mx = scene.ray_cast(dgx, C + dn * travelled, dn, distance=dist + 1.0 - travelled)
        if not hit:
            return None, None, None, dist
        if ob.name in SKIP_HIT:
            travelled = (loc - C).length + 1e-5
            continue
        return ob.name, list(loc), (loc - C).length, dist
    return None, None, None, dist


ANCH_DEF = [
    # key, mode, candidate 3-D points, accepted hit-object prefixes (priority order)
    ('engine', 'surface', [(0, 0, z) for z in (0.37, 0.34, 0.40, 0.31, 0.43)], [('ENG-TC-01',), ('ENG-',)]),
    ('gimbal_pivot', 'point', [(0, 0, Z_PIVOT)], None),
    ('thrust_rings', 'surface', [radial(CAM_AZ + d, 0.0697, 0.2300) for d in (25, 20, 30, 15, 0)],
     [('ENG-GM-09',), ('ENG-GM-10',)]),
    ('vent_stub', 'surface', [tuple(VENT_C), radial(VENT_AZ, VENT_RMAX - 0.002, VENT_C.z)], [('ENG-BL-06',)]),
    ('tank_engine_gap', 'point', [radial(CAM_AZ, 0.045, (eng_hi[2] + TANK_Z0) / 2)], None),
    ('tank', 'surface', [(0, 0, z) for z in (0.86, 0.80, 0.92, 0.74)], [('TANK_tube',)]),
    ('battery', 'surface', [(0, 0, z) for z in (1.158, 1.140, 1.175)], [('AV_battery',)]),
    ('avionics', 'surface', [(-0.02, 0, z) for z in (1.27, 1.28, 1.25)] + [(0, 0, 1.30)],
     [('AV_fc', 'AV_imu'), ('AV_',)]),
    ('backup_chute', 'surface', [(0, 0, z) for z in (1.48, 1.45, 1.51)], [('CHUTE_backup',)]),
    ('drogue', 'surface', [(0, 0, z) for z in (1.70, 1.68, 1.72, 1.74)], [('CHUTE_drogue',)]),
    ('fins', 'surface', [radial(a, R_OUT + 0.055, 0.075) for a in (0.0, 180.0)] +
     [radial(a, R_OUT + 0.09, 0.05) for a in (0.0, 180.0)], [('AF_fin_',)]),
    ('legs', 'surface', [Vector(radial(a, R_HINGE, Z_HINGE)).lerp(radial(a, R_FOOT, Z_FOOT), t)
                         for a in (45.0, 135.0) for t in (0.80, 0.70, 0.88)], [('LEG_',)]),
    ('body_tube', 'surface', [radial(CAM_AZ + d, R_OUT, 0.95) for d in (75, 85, 60, -75, -85, -60)], [('AF_body_tube',)]),
    ('nose', 'surface', [radial(CAM_AZ + d, 0.05, 1.86) for d in (75, 85, 60, -75, -85, -60)], [('AF_nose',)]),
]
anchors = {}
for key, mode, cands, accept in ANCH_DEF:
    rec = None
    if mode == 'point':
        p = Vector(cands[0])
        nm, loc, dhit, dist = first_hit(p)
        px, uvz = proj_blender(p)
        rec = {'mode': 'true projection of the 3-D point', 'p_m': list(p), 'px': px, 'uvz': uvz,
               'first_hit_object': nm, 'occluded': bool(nm and dhit < dist - 1e-4)}
    else:
        for pref in accept:
            for p in cands:
                nm, loc, dhit, dist = first_hit(p)
                if nm and nm.startswith(pref):
                    px, uvz = proj_blender(loc)
                    rec = {'mode': 'visible surface point (camera ray-cast first hit)', 'p_m': loc, 'px': px,
                           'uvz': uvz, 'hit_object': nm, 'aim_point_m': list(Vector(p))}
                    break
            if rec:
                break
        if rec is None:
            p = Vector(cands[0])
            nm, loc, dhit, dist = first_hit(p)
            px, uvz = proj_blender(p)
            rec = {'mode': 'NOT VISIBLE: projected aim point', 'p_m': list(p), 'px': px, 'uvz': uvz,
                   'first_hit_object': nm, 'occluded': True}
    rec['px_closed_form'] = proj_closed(rec['p_m'])
    rec['closed_form_residual_px'] = math.dist(rec['px'], rec['px_closed_form'])
    anchors[key] = rec

# station ruler at the depth of the vehicle axis, on the camera-left side
right = R3.col[0].copy()
right.z = 0.0
right.normalize()
ruler = {}
for z in (0.0, 0.5, 1.0, 1.5, 2.0):
    p = Vector((0, 0, z)) - right * 0.62
    ruler['%.1f' % z] = {'p_m': list(p), 'px': proj_blender(p)[0]}
axis_px = {('%.3f' % z): proj_blender((0, 0, z))[0] for z in
           (Z_FOOT, -0.035, 0.0, Z_PIVOT, eng_hi[2], TANK_Z0, TANK_Z1, Z_BODY[1], 2.0)}

# ------------------------------------------------------------------ render
bpy.context.view_layer.update()
t1 = time.time()
if not args.no_render:
    bpy.ops.render.render(write_still=True)
render_s = None if args.no_render else time.time() - t1

elements = {}
for ob, key in AIRFRAME:
    vv = [ob.matrix_world @ v.co for v in ob.data.vertices]
    e = elements.setdefault(key, {'objects': 0, 'z_m': [1e9, -1e9], 'r_max_m': 0.0})
    e['objects'] += 1
    e['z_m'] = [round(min(e['z_m'][0], min(p.z for p in vv)), 4), round(max(e['z_m'][1], max(p.z for p in vv)), 4)]
    e['r_max_m'] = round(max(e['r_max_m'], max(math.hypot(p.x, p.y) for p in vv)), 4)

meta = {
    'view': args.view, 'raw_png': args.out, 'res_render': [W, H], 'res_final': [args.w, args.h], 'ss': args.ss,
    'blender': bpy.app.version_string, 'samples_max': args.spp, 'adaptive_threshold': 0.01,
    'denoiser': 'none (this Blender 4.0.2 build has no OpenImageDenoise)',
    'view_transform': scene.view_settings.view_transform, 'look': scene.view_settings.look,
    'exposure': args.exposure, 'render_s': None if render_s is None else round(render_s, 1),
    'render_skipped': bool(args.no_render), 'total_s': round(time.time() - T0, 1),
    'glb_sha256_16': GLB_SHA, 'bom_sha256_16': BOM_SHA,
    'engine': {'n_objects': len(ENGINE), 'unknown_material_pns': sorted(unknown),
               'world_bbox_m': [[round(v, 4) for v in eng_lo], [round(v, 4) for v in eng_hi]],
               'translation_m': [0.0, 0.0, Z_PIVOT], 'clocking': 'CAD X = vehicle X (ASSUMED)',
               'vent_stub_ENG-BL-06': {'centre_m': [round(v, 4) for v in VENT_C], 'az_deg': round(VENT_AZ, 2),
                                       'r_max_m': round(VENT_RMAX, 4), 'drawn_wall_cut_radius_m': round(hole_r, 4)}},
    'airframe_elements': elements,
    'derived': {'z_hinge_m': round(Z_HINGE, 4), 'tank_bulkhead_each_m': round(TANK_BH, 4),
                'nose_ogive_radius_m': round(rho, 5)},
    'cutaway': {'shell_removed_az_deg': ({'z < %.2f m' % Z_STEP: [CAM_AZ - CUT_HALF, CAM_AZ + CUT_HALF],
                                      'z > %.2f m (incl. nose, bulkheads, rings)' % Z_STEP: [CAM_AZ - CUT_HALF_UP, CAM_AZ + CUT_HALF_UP]}
                                     if CUT else None),
                'omitted': ['fin at az %g (camera side)' % CAM_AZ] if CUT else [],
                'cut_objects': ['AF_body_tube_low/up', 'AF_nose_ogive', 'AF_tank_ring_*', 'AF_bulkhead_*'] if CUT else [],
                'not_cut': ['engine (real CAD)', 'N2O tank', 'bay contents', 'legs', 'fins (3 of 4 shown)']},
    'camera': {'type': 'PERSP', 'lens_mm': LENS_MM, 'sensor_fit': 'VERTICAL', 'sensor_height_mm': SENSOR_MM,
               'az_deg': CAM_AZ, 'elev_deg': CAM_EL, 'aim_m': list(aim), 'distance_m': round(D, 4),
               'location_m': list(C), 'rotation_quat_wxyz': list(cam.rotation_quaternion),
               'matrix_world': [list(r) for r in M], 'shift_x': cd.shift_x, 'shift_y': cd.shift_y,
               'f_px_render': f_px, 'fit_uv': fit, 'band_v': V_BAND, 'band_u': U_BAND},
    'projection': {
        'primary': 'bpy_extras.object_utils.world_to_camera_view(scene, cam, P) -> (u, v); px = u*W, py = (1-v)*H',
        'closed_form': 'q = R^T (P - C); px = W/2 + f_px*q.x/(-q.z) - shift_x*max(W,H); '
                       'py = H/2 - f_px*q.y/(-q.z) + shift_y*max(W,H); f_px = lens/sensor_height*H',
        'note': 'pixel coordinates at the render resolution; divide by ss for the final image'},
    'anchors': anchors, 'station_ruler': ruler, 'axis_px': axis_px, 'lights': LIGHTS,
    'world': {'srgb_background': '#%02x%02x%02x' % BG_SRGB, 'strength': 1.5},
    'floor': {'z_m': Z_FOOT, 'fade_radius_m': [0.6, 7.0]},
}
json.dump(meta, open(args.meta, 'w'), indent=1)
print('DONE', args.view, W, H, 'render', render_s, 's')
