# ARGOS H1 engine datasheet: Blender 4.0 Cycles renders of the real CAD assembly (GLB).
#
# Derived from scratchpad/renders/render_engine.py (materials by BOM material code, half-section
# bisect at y = 0, projected part anchors). Extended for the datasheet: several views per run,
# camera-relative lighting, orthographic projection metadata for dimension overlays, cut-face
# centroids for section callouts, a laid-out thrust-chamber view and per-family renders.
#
# Usage (one Blender process at a time; the caller sets nice/threads):
#   blender -b -t 2 -P render_views_blender.py -- --glb GLB --bom BOM_JSON --out-dir DIR
#           --views iso,section,front,side,layout,family:GM,... [--px 1600] [--spp 64]
#
# Visualisation only: tessellated display geometry from the GLB. Not a drawing, tolerance or
# fabrication source. Frames: the glTF importer converts +Y up (glTF, metres) to Blender +Z up,
# which reproduces the CAD engine frame (+Z forward toward the injector, origin at the pivot).
import bpy, sys, json, math, time, hashlib, argparse, mathutils
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv[sys.argv.index('--') + 1:]
ap = argparse.ArgumentParser()
ap.add_argument('--glb', required=True)
ap.add_argument('--bom', required=True)
ap.add_argument('--out-dir', required=True)
ap.add_argument('--views', required=True)
ap.add_argument('--px', type=int, default=1600, help='long side of the render in pixels')
ap.add_argument('--spp', type=int, default=64)
ap.add_argument('--family-px', type=int, default=900)
ap.add_argument('--family-spp', type=int, default=48)
args = ap.parse_args(argv)


def sha256_16(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()[:16]


GLB_SHA = sha256_16(args.glb)
BOM_SHA = sha256_16(args.bom)
bom = json.load(open(args.bom))
PN_MAT = {r['pn']: r['material'] for r in bom['lines']}

# (base RGB, metallic, roughness) per BOM material code; unknown codes fall back to grey.
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
    # v0.3.0 (CAD v3.5.2 codes)
    'SS440C-HT': ((0.55, 0.55, 0.57), 1.0, 0.28),
    'GLIDCOP-AL15': ((0.80, 0.45, 0.30), 1.0, 0.30),
    'FLEX-GRAPHITE-TH': ((0.20, 0.20, 0.21), 0.3, 0.60),
}

# Thrust-chamber laid-out view: ordered groups (head -> nozzle), matched by PN prefix.
LAYOUT_GROUPS = [
    ('pintle drive', ['ENG-PD-', 'ENG-EL-05']),
    ('injector head assembly', ['ENG-TC-02', 'ENG-TC-03', 'ENG-TC-04', 'ENG-TC-05', 'ENG-TC-10',
                                'ENG-TC-11', 'ENG-IG-', 'ENG-FD-01', 'ENG-FD-02']),
    ('pre-chamber insulator', ['ENG-TC-06']),
    ('combustion case', ['ENG-TC-01']),
    ('grain liner', ['ENG-TC-07']),
    ('grain segment 1', ['ENG-GR-01']),
    ('grain segment 2', ['ENG-GR-02']),
    ('post-chamber insulator', ['ENG-TC-08']),
    ('aft section', ['ENG-TC-09']),
    ('throat insert and sleeve', ['ENG-NZ-01', 'ENG-NZ-02']),
    ('nozzle joint J1', ['ENG-NZ-03', 'ENG-NZ-04', 'ENG-NZ-06']),
]


def pn_of(name):
    return name.split('#')[0].split('.')[0]


def family_of(pn):
    p = pn.split('-')
    return p[1] if len(p) > 2 else p[0]


def mat_code(pn):
    return PN_MAT.get(pn) or PN_MAT.get(pn.rstrip('ABF')) or PN_MAT.get(pn.rsplit('-', 1)[0]) or 'UNKNOWN'


def wbb(o):
    pts = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
    return [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]


def load_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=args.glb)
    scene = bpy.context.scene
    mats = {}

    def mat_for(code):
        if code not in mats:
            col, met, rough = LOOK.get(code, ((0.7, 0.7, 0.7), 0.5, 0.4))
            m = bpy.data.materials.new(code)
            m.use_nodes = True
            b = m.node_tree.nodes['Principled BSDF']
            b.inputs['Base Color'].default_value = (*col, 1.0)
            b.inputs['Metallic'].default_value = met
            b.inputs['Roughness'].default_value = rough
            mats[code] = m
        return mats[code]

    meshes = [o for o in scene.objects if o.type == 'MESH']
    unknown = set()
    for o in meshes:
        code = mat_code(pn_of(o.name))
        if code == 'UNKNOWN':
            unknown.add(pn_of(o.name))
        o.data.materials.clear()
        o.data.materials.append(mat_for(code))
        for p in o.data.polygons:
            p.use_smooth = False
    return scene, meshes, sorted(unknown)


def section_cut(meshes):
    """Remove the y < 0 half, cap the cut and give cut faces a darker material. Returns
    {object name: area-weighted centroid of its cut faces in world metres}."""
    import bmesh
    keep = []
    for o in list(meshes):
        lo, hi = wbb(o)
        if hi[1] <= 0.0:
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        keep.append(o)
        if lo[1] >= 0.0:
            continue
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.transform(o.matrix_world)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                                     plane_co=(0, 0, 0), plane_no=(0, 1, 0),
                                     clear_inner=True, clear_outer=False, dist=1e-7)
        cut_edges = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
        if cut_edges:
            try:
                bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=cut_edges,
                                        normal=(0, -1, 0))
            except Exception as e:
                print('FILL-FAIL', o.name, e)
        bm.transform(o.matrix_world.inverted())
        bm.to_mesh(o.data)
        bm.free()
        o.data.update()
    centroids = {}
    for o in keep:
        if not o.data.materials:
            continue
        base = o.data.materials[0]
        cutname = base.name + '_cut'
        if cutname not in bpy.data.materials:
            m = base.copy()
            m.name = cutname
            b = m.node_tree.nodes['Principled BSDF']
            c = b.inputs['Base Color'].default_value
            b.inputs['Base Color'].default_value = (c[0] * 0.16, c[1] * 0.16, c[2] * 0.16, 1.0)
            b.inputs['Metallic'].default_value = min(b.inputs['Metallic'].default_value, 0.3)
            b.inputs['Roughness'].default_value = 0.75
        mcut = bpy.data.materials[cutname]
        if mcut.name not in [mm.name for mm in o.data.materials]:
            o.data.materials.append(mcut)
        idx = [mm.name for mm in o.data.materials].index(cutname)
        mw = o.matrix_world
        n3 = mw.to_3x3()
        # area-weighted centroid of the cut faces, split by side of the axis (x < 0: 'L',
        # x >= 0: 'R'), so an axisymmetric part gets one anchor on material on each side
        # instead of a single centroid on the axis (inside the bore)
        accs = {'L': [mathutils.Vector((0.0, 0.0, 0.0)), 0.0], 'R': [mathutils.Vector((0.0, 0.0, 0.0)), 0.0]}
        for poly in o.data.polygons:
            nrm = (n3 @ poly.normal).normalized()
            if abs(nrm.y) > 0.98 and all(abs((mw @ o.data.vertices[v].co).y) < 2e-5 for v in poly.vertices):
                poly.material_index = idx
                a = poly.area
                c = mw @ poly.center
                s = 'L' if c.x < 0.0 else 'R'
                accs[s][0] += c * a
                accs[s][1] += a
        res = {s: {'p': list(acc / area), 'area': area} for s, (acc, area) in accs.items() if area > 0}
        if res:
            centroids[o.name] = res
    return keep, centroids


def frame_camera(scene, meshes, d, up_hint, px_long, margin=1.06):
    """Orthographic camera looking along -d (from +d side), sized to the projected extents."""
    pts = []
    for o in meshes:
        lo, hi = wbb(o)
        for x in (lo[0], hi[0]):
            for y in (lo[1], hi[1]):
                for z in (lo[2], hi[2]):
                    pts.append(mathutils.Vector((x, y, z)))
    d = mathutils.Vector(d).normalized()
    quat = (-d).to_track_quat('-Z', up_hint)
    rot = quat.to_matrix()
    right, up = rot.col[0], rot.col[1]
    us = [p.dot(right) for p in pts]
    vs = [p.dot(up) for p in pts]
    ex, ey = (max(us) - min(us)) * margin, (max(vs) - min(vs)) * margin
    uc, vc = (max(us) + min(us)) / 2, (max(vs) + min(vs)) / 2
    ctr_all = mathutils.Vector([sum(p[i] for p in pts) / len(pts) for i in range(3)])
    dc = ctr_all.dot(d)
    centre = right * uc + up * vc + d * dc
    if ex >= ey:
        W, H = px_long, max(64, int(round(px_long * ey / ex)))
        scale = ex
    else:
        H, W = px_long, max(64, int(round(px_long * ex / ey)))
        scale = ey
    cam_data = bpy.data.cameras.new('cam')
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = scale
    cam_data.clip_start = 0.001
    cam_data.clip_end = 20.0
    cam = bpy.data.objects.new('cam', cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.location = centre + d * 3.0
    cam.rotation_euler = quat.to_euler()
    scene.render.resolution_x = W
    scene.render.resolution_y = H
    scene.render.resolution_percentage = 100
    bpy.context.view_layer.update()
    m_per_px = scale / max(W, H)
    return cam, W, H, m_per_px, right, up, d, centre


def lights_and_world(scene, cam, centre, d, dist):
    world = bpy.data.worlds.new('w')
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.86, 0.88, 0.91, 1.0)
    bg.inputs['Strength'].default_value = 0.35
    right = cam.matrix_world.to_3x3().col[0]
    up = cam.matrix_world.to_3x3().col[1]
    d = mathutils.Vector(d).normalized()

    def area(name, loc, energy, size):
        l = bpy.data.lights.new(name, 'AREA')
        l.energy = energy
        l.size = size
        ob = bpy.data.objects.new(name, l)
        ob.location = loc
        ob.rotation_euler = (centre - mathutils.Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        scene.collection.objects.link(ob)
    s = max(dist, 0.3)
    area('key', centre + (d * 1.0 - right * 0.9 + up * 0.8).normalized() * 1.6 * s, 95 * s * s, 0.9 * s)
    area('fill', centre + (d * 1.0 + right * 1.1 + up * 0.1).normalized() * 1.8 * s, 30 * s * s, 1.2 * s)
    area('rim', centre + (-d * 0.8 + right * 0.3 + up * 1.0).normalized() * 1.6 * s, 55 * s * s, 0.8 * s)


def render_settings(scene, spp, out_png, exposure):
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = spp
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.use_denoising = False  # this Blender build has no OpenImageDenoise
    scene.cycles.adaptive_threshold = 0.015
    scene.cycles.max_bounces = 6
    scene.cycles.sample_clamp_indirect = 2.0
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.view_settings.view_transform = 'Filmic'
    looks = [i.identifier for i in scene.view_settings.bl_rna.properties['look'].enum_items]
    scene.view_settings.look = 'Filmic - Medium High Contrast' if 'Filmic - Medium High Contrast' in looks else 'None'
    scene.view_settings.exposure = exposure
    scene.render.filepath = out_png


def project(scene, cam, p, W, H):
    uv = world_to_camera_view(scene, cam, mathutils.Vector(p))
    return [uv.x * W, (1.0 - uv.y) * H]


def do_view(view):
    t0 = time.time()
    scene, meshes, unknown = load_scene()
    fam = None
    label = view
    if view.startswith('family:'):
        fam = view.split(':', 1)[1]
        label = 'family_' + fam
        for o in list(meshes):
            if family_of(pn_of(o.name)) != fam:
                bpy.data.objects.remove(o, do_unlink=True)
                meshes.remove(o)
        if not meshes:
            print('EMPTY-FAMILY', fam)
            return None
    centroids = {}
    layout_meta = []
    if view == 'section':
        meshes, centroids = section_cut(meshes)
    if view == 'layout':
        groups = []
        used = set()
        for gname, prefixes in LAYOUT_GROUPS:
            g = [o for o in meshes if o.name not in used and any(pn_of(o.name).startswith(p) for p in prefixes)]
            for o in g:
                used.add(o.name)
            if g:
                groups.append((gname, g))
        for o in list(meshes):
            if o.name not in used:
                bpy.data.objects.remove(o, do_unlink=True)
        meshes = [o for _, g in groups for o in g]
        x = 0.0
        gap = 0.018
        for gname, g in groups:
            # side by side along X at true scale; each group re-centred on z = 0 (axial
            # position is NOT preserved: the CAD z range is recorded in the metadata)
            lo = min(wbb(o)[0][0] for o in g)
            hi = max(wbb(o)[1][0] for o in g)
            zlo = min(wbb(o)[0][2] for o in g)
            zhi = max(wbb(o)[1][2] for o in g)
            dx = x - lo
            dz = -(zlo + zhi) / 2
            for o in g:
                o.location.x += dx
                o.location.z += dz
            bpy.context.view_layer.update()
            layout_meta.append({'group': gname, 'pns': sorted({pn_of(o.name) for o in g}),
                                'x_centre_m': x + (hi - lo) / 2, 'cad_z_range_m': [zlo, zhi],
                                'dx_m': dx, 'dz_m': dz})
            x += (hi - lo) + gap
        bpy.context.view_layer.update()

    if view == 'iso' or view.startswith('family:'):
        d, uph, expo = (-0.80, -1.0, 0.42), 'Y', -0.35
    elif view == 'section':
        d, uph, expo = (0.0, -1.0, 0.0), 'Y', -1.0
    elif view == 'front':
        d, uph, expo = (0.0, -1.0, 0.0), 'Y', -0.6
    elif view == 'side':
        d, uph, expo = (1.0, 0.0, 0.0), 'Y', -0.6
    elif view == 'layout':
        d, uph, expo = (0.0, -1.0, 0.22), 'Y', -0.35
    else:
        raise SystemExit('unknown view ' + view)
    px = args.family_px if fam else args.px
    spp = args.family_spp if fam else args.spp
    cam, W, H, mpp, right, up, dvec, centre = frame_camera(scene, meshes, d, uph, px,
                                                           margin=1.10 if fam else 1.05)
    ext = max(max(wbb(o)[1][i] for o in meshes) - min(wbb(o)[0][i] for o in meshes) for i in range(3))
    lights_and_world(scene, cam, centre, dvec, ext)
    out_png = f"{args.out_dir}/{label}.png"
    render_settings(scene, spp, out_png, expo)
    bpy.context.view_layer.update()

    anchors = {}
    for o in meshes:
        if len(o.data.vertices) == 0:
            continue
        pn = pn_of(o.name)
        a, b = wbb(o)
        if o.name in centroids:
            for s, c in sorted(centroids[o.name].items()):
                anchors.setdefault(pn, []).append({'px': project(scene, cam, c['p'], W, H),
                                                   'kind': 'cut-face centroid', 'side': s,
                                                   'area_m2': c['area'], 'bbox_m': [a, b]})
            continue
        else:
            p = [(a[i] + b[i]) / 2 for i in range(3)]
            if view == 'section':
                p[1] = max(a[1], 0.0)
            kind = 'bbox centre'
        anchors.setdefault(pn, []).append({'px': project(scene, cam, p, W, H), 'kind': kind,
                                           'bbox_m': [a, b]})
    lo = [min(wbb(o)[0][i] for o in meshes) for i in range(3)]
    hi = [max(wbb(o)[1][i] for o in meshes) for i in range(3)]
    probe = {'origin': project(scene, cam, (0, 0, 0), W, H),
             'bbox_lo': project(scene, cam, lo, W, H), 'bbox_hi': project(scene, cam, hi, W, H)}
    meta = {
        'view': view, 'label': label, 'png': f'{label}.png', 'res': [W, H],
        'camera': {'type': 'ORTHO', 'ortho_scale_m': cam.data.ortho_scale,
                   'centre_m': list(centre), 'right': list(right), 'up': list(up),
                   'toward_camera': list(dvec), 'm_per_px': mpp},
        'projection_rule': 'px = W/2 + dot(P - centre, right)/m_per_px ; py = H/2 - dot(P - centre, up)/m_per_px (P in metres, engine frame)',
        'probe_points_px': probe,
        'visible_bbox_m': [lo, hi],
        'n_objects': len(meshes), 'pns': sorted({pn_of(o.name) for o in meshes}),
        'unknown_material_pns': unknown, 'layout_groups': layout_meta,
        'anchors': anchors,
        'glb_sha256_16': GLB_SHA, 'bom_sha256_16': BOM_SHA, 'samples': spp,
        'blender': bpy.app.version_string,
    }
    bpy.ops.render.render(write_still=True)
    meta['render_s'] = round(time.time() - t0, 1)
    json.dump(meta, open(f"{args.out_dir}/{label}_meta.json", 'w'), indent=1)
    print('DONE', label, W, H, meta['render_s'], 's')
    return meta


for v in [s.strip() for s in args.views.split(',') if s.strip()]:
    do_view(v)
