"""ARGOS H1 rocket side view: true 2-D projection of the frozen engine CAD v3.5.1 (GLB).

Reads (read only):  ENGINE_v3.5.1_neutral.glb, assembly_manifest_v3.5.1.json, BOM_v3.5.1.json
Writes:             work/engine_projection.json  (outlines in the VEHICLE frame, millimetres)

Frames
  GLB:      metres, +Y up (= engine axis toward the injector), origin = gimbal pivot.
  Engine:   mm, +Z forward (toward the injector / nose), origin = pivot   (STEP frame).
            engine (x, y, z) = 1000 * (X_glb, -Z_glb, Y_glb)   (checked against the manifest bounds)
  Vehicle:  station s [mm] = z_engine + 203.0 (pivot station 0.203 m, gnc.json v3.1 / vehicle_v3d)
            lateral l [mm] = component of (x, y) along the drawing 'up' direction, azimuth AZ_UP
            (azimuth measured from engine +X toward +Y, the BOM convention: ENG-BL-06 'at az 112').
  The view is an orthographic projection seen from azimuth AZ_UP + 90 deg, so page-right = +s
  (toward the nose), page-up = azimuth AZ_UP. This is a true (not mirrored) view.

Method: every triangle of every instance is projected onto the (s, l) plane and rasterised
(RES mm per pixel); the union mask is traced with marching squares (contourpy) and simplified
(Ramer-Douglas-Peucker, tolerance TOL). Outlines are display geometry from the tessellated GLB:
not a fabrication or tolerance source.
"""
import hashlib, json, math, sys, time
import numpy as np
import trimesh
import contourpy
from PIL import Image, ImageDraw

CAD = '/home/claude/work/shared-fallback/engine/03-cad/v3.5.1'
GLB = f'{CAD}/assembly/ENGINE_v3.5.1_neutral.glb'
MAN = f'{CAD}/assembly/assembly_manifest_v3.5.1.json'
BOM = f'{CAD}/BOM_v3.5.1.json'
MASSPROPS = f'{CAD}/massprops_v3.5.1.json'
OUT = sys.argv[1] if len(sys.argv) > 1 else 'work/engine_projection.json'

PIVOT_STATION_MM = 203.0      # gnc.json v3.1 conventions.stations; vehicle_v3d.json z_pivot_m
AZ_UP = 112.0                 # deg; BOM ENG-BL-06 'V2 vent bulkhead fitting ... through the bay wall at az 112'
RES = 0.1                     # mm per pixel
TOL_UNION = 0.12              # mm, RDP tolerance for the union outlines
TOL_PART = 0.20               # mm, RDP tolerance for per-part outlines
GIMBAL_STOP_DEG = 8.0         # gimbal stop (brief / mechanical); used only for the swept-outline check


def sha16(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()[:16]


def rdp(pts, tol):
    """Ramer-Douglas-Peucker on an open polyline (N,2); iterative stack, numpy distances."""
    n = len(pts)
    if n < 3:
        return pts
    keep = np.zeros(n, bool)
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        a, b = pts[i], pts[j]
        seg = pts[i + 1:j]
        d = b - a
        L = math.hypot(d[0], d[1])
        if L < 1e-12:
            dist = np.hypot(seg[:, 0] - a[0], seg[:, 1] - a[1])
        else:
            dist = np.abs(d[0] * (seg[:, 1] - a[1]) - d[1] * (seg[:, 0] - a[0])) / L
        k = int(np.argmax(dist))
        if dist[k] > tol:
            m = i + 1 + k
            keep[m] = True
            stack.append((i, m))
            stack.append((m, j))
    return pts[keep]


def simplify_closed(loop, tol):
    """RDP on a closed loop: split at the point farthest from the first point."""
    if np.allclose(loop[0], loop[-1]):
        loop = loop[:-1]
    if len(loop) < 4:
        return loop
    d = np.hypot(loop[:, 0] - loop[0, 0], loop[:, 1] - loop[0, 1])
    k = int(np.argmax(d))
    a = rdp(loop[:k + 1], tol)
    b = rdp(np.vstack([loop[k:], loop[:1]]), tol)
    return np.vstack([a[:-1], b[:-1]])


def loop_area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def trace(mask, s0, l_top, tol, min_area=0.4):
    """Closed outlines of a binary mask -> list of (N,2) arrays in (s, l) mm."""
    m = np.pad(mask.astype(np.float32), 2)
    gen = contourpy.contour_generator(z=m, line_type='Separate')
    loops = []
    for ln in gen.lines(0.5):
        if len(ln) < 4:
            continue
        col = ln[:, 0] - 2.0
        row = ln[:, 1] - 2.0
        s = s0 + (col + 0.5) * RES
        l = l_top - (row + 0.5) * RES
        p = np.c_[s, l]
        if abs(loop_area(p)) < min_area:
            continue
        loops.append(simplify_closed(p, tol))
    return loops


def main():
    t0 = time.time()
    sc = trimesh.load(GLB)
    man = {i['inst']: i for i in json.load(open(MAN))['instances']}
    bom = json.load(open(BOM))
    names = {l['pn']: l['name'] for l in bom['lines']}
    mp = json.load(open(MASSPROPS))
    ca, sa = math.cos(math.radians(AZ_UP)), math.sin(math.radians(AZ_UP))

    parts = {}
    allv = []
    for inst in sc.graph.nodes_geometry:
        T, g = sc.graph[inst]
        m = sc.geometry[g]
        V = trimesh.transformations.transform_points(m.vertices, T) * 1000.0
        e = np.c_[V[:, 0], -V[:, 2], V[:, 1]]           # engine frame, mm
        parts[inst] = (e, np.asarray(m.faces))
        allv.append(e)
    allv = np.vstack(allv)

    # axis mapping check against the manifest bounds (tessellation tolerance)
    max_err = 0.0
    for inst, (e, f) in parts.items():
        b = np.r_[e.min(0), e.max(0)]
        max_err = max(max_err, float(np.abs(b - np.array(man[inst]['bounds_mm'])).max()))

    # projected coordinates
    proj = {}
    for inst, (e, f) in parts.items():
        s = e[:, 2] + PIVOT_STATION_MM
        l = e[:, 0] * ca + e[:, 1] * sa
        proj[inst] = np.c_[s, l]
    P = np.vstack(list(proj.values()))
    s_min, s_max = float(P[:, 0].min()), float(P[:, 0].max())
    l_min, l_max = float(P[:, 1].min()), float(P[:, 1].max())
    S0 = math.floor(s_min) - 1.0
    LT = math.ceil(l_max) + 1.0
    W = int(math.ceil((math.ceil(s_max) + 1.0 - S0) / RES)) + 1
    H = int(math.ceil((LT - (math.floor(l_min) - 1.0)) / RES)) + 1

    union = np.zeros((H, W), bool)
    gimb = np.zeros((H, W), bool)
    out_parts = {}
    for inst, (e, f) in parts.items():
        pp = proj[inst]
        cx = (pp[:, 0] - S0) / RES
        cy = (LT - pp[:, 1]) / RES
        c0, c1 = int(math.floor(cx.min())) - 2, int(math.ceil(cx.max())) + 3
        r0, r1 = int(math.floor(cy.min())) - 2, int(math.ceil(cy.max())) + 3
        img = Image.new('1', (c1 - c0, r1 - r0), 0)
        dr = ImageDraw.Draw(img)
        X = cx - c0
        Y = cy - r0
        for a, b, c in f:
            dr.polygon([(X[a], Y[a]), (X[b], Y[b]), (X[c], Y[c])], fill=1, outline=1)
        loc = np.array(img, dtype=bool)
        union[r0:r1, c0:c1] |= loc
        grp = man[inst]['group']
        if grp == 'engine':
            gimb[r0:r1, c0:c1] |= loc
        loops = trace(loc, S0 + c0 * RES, LT - r0 * RES, TOL_PART)
        pn = inst.split('#')[0]
        out_parts[inst] = dict(group=grp, pn=pn, name=names.get(pn, ''), loops=[np.round(p, 2).tolist() for p in loops])

    u_loops = trace(union, S0, LT, TOL_UNION)
    g_loops = trace(gimb, S0, LT, TOL_UNION)

    # ---- metrics from the vertices (exact, not raster) ------------------------------------------
    r_all = np.hypot(allv[:, 0], allv[:, 1])
    bl6 = parts['ENG-BL-06#0'][0]
    r6 = np.hypot(bl6[:, 0], bl6[:, 1])
    i6 = int(np.argmax(r6))
    p6 = proj['ENG-BL-06#0']
    fd12 = proj['ENG-FD-12F#0']

    # radial envelope over all azimuths, per 2 mm station band (swept / rotated envelope)
    band = 2.0
    st_all = allv[:, 2] + PIVOT_STATION_MM
    edges = np.arange(math.floor(st_all.min() / band) * band, st_all.max() + band, band)
    idx = np.clip(np.digitize(st_all, edges) - 1, 0, len(edges) - 2)
    rmax_band = np.zeros(len(edges) - 1)
    np.maximum.at(rmax_band, idx, r_all)
    env = [[round(float(edges[i]), 1), round(float(edges[i + 1]), 1), round(float(rmax_band[i]), 2)]
           for i in range(len(edges) - 1) if rmax_band[i] > 0]

    # gimbal-stop sweep: tilt the gimballed group ('engine') by 8 deg about an axis through the pivot,
    # perpendicular to the engine axis, for every tilt direction; max radius of the aft end.
    eg = np.vstack([parts[i][0] for i in parts if man[i]['group'] == 'engine'])
    th = math.radians(GIMBAL_STOP_DEG)
    sweep = {}
    for label, zcut in (('below_GM10_aft_face_z_lt_-99.8mm', -99.8), ('aft_of_pivot_z_lt_0', 0.0),
                        ('below_body_aft_datum_z_lt_-203mm', -PIVOT_STATION_MM)):
        q = eg[eg[:, 2] < zcut]
        best = (0.0, None)
        for phi in np.radians(np.arange(0.0, 360.0, 1.0)):
            # rotation about axis a = (-sin phi, cos phi, 0): tilts +z toward direction phi
            ax = np.array([-math.sin(phi), math.cos(phi), 0.0])
            K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
            R = np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * K @ K
            qr = q @ R.T
            rr = np.hypot(qr[:, 0], qr[:, 1])
            k = int(np.argmax(rr))
            if rr[k] > best[0]:
                best = (float(rr[k]), dict(phi_deg=round(math.degrees(phi), 1), z_mm=round(float(qr[k, 2]), 2)))
        sweep[label] = dict(r_max_mm=round(best[0], 2), **best[1], n_vertices=int(len(q)))

    # swept outline in the drawing plane: in-plane tilt (+/- 8 deg about the view axis) of the
    # gimballed group, aft of the GM-10 ring (z < -99.8 mm): outlines for the drawing
    sw_loops = {}
    for sgn in (+1, -1):
        a = sgn * th
        img = Image.new('1', (W, H), 0)
        dr = ImageDraw.Draw(img)
        for inst, (e, f) in parts.items():
            if man[inst]['group'] != 'engine':
                continue
            s = e[:, 2]
            l = e[:, 0] * ca + e[:, 1] * sa
            # in-plane rotation about the pivot (s along the axis, l lateral)
            s2 = s * math.cos(a) - l * math.sin(a)
            l2 = s * math.sin(a) + l * math.cos(a)
            cx = (s2 + PIVOT_STATION_MM - S0) / RES
            cy = (LT - l2) / RES
            sel = np.all(e[f][:, :, 2] < -99.8, axis=1)       # faces entirely aft of the GM-10 aft face
            for a_, b_, c_ in f[sel]:
                dr.polygon([(cx[a_], cy[a_]), (cx[b_], cy[b_]), (cx[c_], cy[c_])], fill=1, outline=1)
        msk = np.array(img, dtype=bool)
        sw_loops['+8' if sgn > 0 else '-8'] = [np.round(p, 2).tolist() for p in trace(msk, S0, LT, TOL_UNION)]

    # in-plane lateral extent of the swept aft section (drawing check)
    sw_extent = {k: [round(min(min(pt[1] for pt in lp) for lp in v), 2), round(max(max(pt[1] for pt in lp) for lp in v), 2)]
                 for k, v in sw_loops.items() if v}

    wet = mp['states']['wet']['all']
    res = dict(
        about='True orthographic projection of the frozen engine CAD v3.5.1 GLB onto the vehicle side plane. '
              'Display geometry (tessellated GLB); not a fabrication or tolerance source.',
        sources=dict(glb=GLB, glb_sha256_16=sha16(GLB), manifest=MAN, manifest_sha256_16=sha16(MAN),
                     bom=BOM, bom_sha256_16=sha16(BOM), massprops=MASSPROPS, massprops_sha256_16=sha16(MASSPROPS)),
        frames=dict(engine='mm, +Z forward toward the injector, origin = gimbal pivot (= STEP frame); '
                           'engine (x,y,z) = 1000 * (X_glb, -Z_glb, Y_glb)',
                    vehicle_station='s [mm] = z_engine + 203.0 (pivot station 0.203 m)',
                    lateral='l [mm] along azimuth AZ_UP (az from engine +X toward +Y)',
                    az_up_deg=AZ_UP, viewed_from_az_deg=(AZ_UP + 90.0) % 360.0,
                    axis_mapping_max_bound_error_mm=round(max_err, 3)),
        raster=dict(res_mm=RES, rdp_tol_union_mm=TOL_UNION, rdp_tol_part_mm=TOL_PART, image_px=[W, H]),
        envelope=dict(
            station_min_mm=round(s_min, 2), station_max_mm=round(s_max, 2),
            axial_extent_engine_frame_mm=[round(float(allv[:, 2].min()), 2), round(float(allv[:, 2].max()), 2)],
            bbox_x_mm=[round(float(allv[:, 0].min()), 2), round(float(allv[:, 0].max()), 2)],
            bbox_y_mm=[round(float(allv[:, 1].min()), 2), round(float(allv[:, 1].max()), 2)],
            projected_lateral_mm=[round(l_min, 2), round(l_max, 2)],
            r_max_all_az_mm=round(float(r_all.max()), 2)),
        features=dict(
            pivot_station_mm=PIVOT_STATION_MM,
            nozzle_exit_station_mm=round(s_min, 2),
            engine_top_station_mm=round(s_max, 2),
            BL06_vent_stub=dict(r_max_mm=round(float(r6[i6]), 2),
                                az_of_r_max_deg=round(math.degrees(math.atan2(bl6[i6, 1], bl6[i6, 0])), 1),
                                station_mm=[round(float(p6[:, 0].min()), 2), round(float(p6[:, 0].max()), 2)],
                                projected_lateral_mm=[round(float(p6[:, 1].min()), 2), round(float(p6[:, 1].max()), 2)]),
            FD12F_tank_line_flange=dict(station_mm=[round(float(fd12[:, 0].min()), 2), round(float(fd12[:, 0].max()), 2)],
                                        projected_lateral_mm=[round(float(fd12[:, 1].min()), 2), round(float(fd12[:, 1].max()), 2)]),
            GM09_upper_thrust_ring_station_mm=[round(man['ENG-GM-09#0']['bounds_mm'][2] + PIVOT_STATION_MM, 2),
                                               round(man['ENG-GM-09#0']['bounds_mm'][5] + PIVOT_STATION_MM, 2)],
            GM10_lower_ring_station_mm=[round(man['ENG-GM-10#0']['bounds_mm'][2] + PIVOT_STATION_MM, 2),
                                        round(man['ENG-GM-10#0']['bounds_mm'][5] + PIVOT_STATION_MM, 2)],
            thrust_ring_outer_r_mm=round(float(np.hypot(parts['ENG-GM-09#0'][0][:, 0], parts['ENG-GM-09#0'][0][:, 1]).max()), 2),
            engine_cg_wet_station_mm=round(PIVOT_STATION_MM + wet['cg_mm'][2], 2),
            engine_mass_wet_kg=wet['m_kg']),
        gimbal_stop_sweep=dict(stop_deg=GIMBAL_STOP_DEG, group='engine (gimballed)', cases=sweep,
                               in_plane_swept_lateral_extent_mm=sw_extent),
        radial_envelope_2mm_bands=env,
        outline_union=[np.round(p, 2).tolist() for p in u_loops],
        outline_gimballed=[np.round(p, 2).tolist() for p in g_loops],
        outline_swept_aft=sw_loops,
        parts=out_parts,
        runtime_s=round(time.time() - t0, 1),
    )
    with open(OUT, 'w') as fh:
        json.dump(res, fh, separators=(',', ':'))
    print(json.dumps({k: res[k] for k in ('frames', 'raster', 'envelope', 'features', 'gimbal_stop_sweep', 'runtime_s')}, indent=1))
    print('union loops', len(u_loops), [len(p) for p in u_loops][:12], 'gimballed loops', len(g_loops))
    print('part loops total pts', sum(len(lp) for v in out_parts.values() for lp in v['loops']))


if __name__ == '__main__':
    main()
