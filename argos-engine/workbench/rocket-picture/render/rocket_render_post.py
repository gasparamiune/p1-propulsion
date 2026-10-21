#!/usr/bin/env python3
"""ARGOS H1 vehicle concept renders: post-processing.

Reads   work/raw_{exterior,cutaway}.png  (RGBA, straight alpha, film transparent) and
        work/meta_{exterior,cutaway}.json written by rocket_render_blender.py.
Writes  rocket_exterior.jpg, rocket_cutaway.jpg, rocket_cutaway_labelled.jpg, render_meta.json.

Labels: every leader line ends at the camera projection stored by the Blender script (Blender's
world_to_camera_view of a ray-cast visible surface point, or of a true 3-D point for the gimbal pivot
and the tank-engine gap). The 0.5 m scale bar is projected here with the closed-form pinhole model
that the Blender script verified against world_to_camera_view (residual recorded in the meta).
Visualisation only: not a drawing, tolerance or fabrication source; not a physical approval.
"""
import datetime
import hashlib
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont, __version__ as PIL_VERSION

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, 'work')
BG = (0x15, 0x18, 0x1c)
FONT_DIR = '/usr/share/fonts/opentype/inter'
K = 3                                   # overlay supersampling for anti-aliased lines and text
COL = {'CAD': (108, 196, 255), 'CONCEPT': (243, 178, 74), 'ASSUMED': (190, 198, 209),
       'TODEF': (255, 128, 110), 'muted': (150, 159, 171), 'text': (232, 236, 241), 'halo': (11, 13, 16)}
TAG_TEXT = {'CAD': 'real CAD v3.5.1', 'CONCEPT': 'concept / ESTIMATE', 'ASSUMED': 'ASSUMED (GNC RV-1c)',
            'TODEF': 'TO-DEFINE'}
CAD = '/home/claude/work/shared-fallback/engine/03-cad/v3.5.1'
ENG = '/home/claude/work/shared-fallback/engine'
SOURCES = {
    'glb': f'{CAD}/assembly/ENGINE_v3.5.1_neutral.glb',
    'bom': f'{CAD}/BOM_v3.5.1.json',
    'assembly_manifest': f'{CAD}/assembly/assembly_manifest_v3.5.1.json',
    'gnc_json': f'{ENG}/interfaces/gnc.json',
    'gncsim_vehicle_py': f'{ENG}/01-systems-gnc/sim/gncsim/vehicle.py',
    'vehicle_v3d': f'{ENG}/01-systems-gnc/vehicle/vehicle_v3d.json',
    'mass_ledger_v3d': f'{ENG}/01-systems-gnc/vehicle/mass_ledger_v3d.csv',
    'datasheet_render_script': f'{ENG}/07-datasheet/gen/render_views_blender.py',
}


def h16(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()[:16]


def font(weight, px):
    return ImageFont.truetype(f'{FONT_DIR}/Inter-{weight}.otf', int(round(px * K)))


def composite(path, size):
    im = Image.open(path).convert('RGBA')
    out = Image.alpha_composite(Image.new('RGBA', im.size, BG + (255,)), im).convert('RGB')
    return out.resize(size, Image.LANCZOS) if out.size != size else out


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(' '), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if draw.textlength(t, font=fnt) <= max_w * K or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


class Overlay:
    """RGBA overlay drawn at K x resolution, downsampled (premultiplied) onto the base image."""

    def __init__(self, size):
        self.size = size
        self.im = Image.new('RGBA', (size[0] * K, size[1] * K), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def text(self, xy, s, fnt, fill, anchor='la'):
        self.d.text((xy[0] * K, xy[1] * K), s, font=fnt, fill=fill + (255,), anchor=anchor)

    def width(self, s, fnt):
        return self.d.textlength(s, font=fnt) / K

    def line(self, pts, fill, w, alpha=255):
        self.d.line([(x * K, y * K) for x, y in pts], fill=fill + (alpha,), width=max(1, int(round(w * K))),
                    joint='curve')

    def dot(self, xy, r, fill, outline=None, ow=0.0):
        x, y = xy[0] * K, xy[1] * K
        if outline:
            ro = (r + ow) * K
            self.d.ellipse([x - ro, y - ro, x + ro, y + ro], fill=outline + (255,))
        self.d.ellipse([x - r * K, y - r * K, x + r * K, y + r * K], fill=fill + (255,))

    def ring(self, xy, r, fill, w):
        x, y = xy[0] * K, xy[1] * K
        self.d.ellipse([x - r * K, y - r * K, x + r * K, y + r * K], outline=fill + (255,), width=int(round(w * K)))

    def apply(self, base):
        small = self.im.convert('RGBa').resize(self.size, Image.LANCZOS).convert('RGBA')
        return Image.alpha_composite(base.convert('RGBA'), small).convert('RGB')


def caption(img, lines_text):
    """Small provenance caption at the bottom of the unlabelled renders."""
    ov = Overlay(img.size)
    f = font('Regular', 12.5)
    lines = []
    for t in lines_text:
        lines += wrap(ov.d, t, f, img.size[0] - 80)
    y = img.size[1] - 18 - 17 * len(lines)
    for t in lines:
        ov.text((img.size[0] / 2, y), t, f, COL['muted'], anchor='mt')
        y += 17
    return ov.apply(img)


def save_jpeg(img, path, q=90):
    for qq in (q, 86, 82, 78):
        img.save(path, 'JPEG', quality=qq, optimize=True, progressive=True, subsampling=0 if qq >= 86 else 2)
        if os.path.getsize(path) <= 600 * 1024:
            return qq
    return qq


def project_closed(cam, W, H, p):
    """Closed-form pinhole projection (render resolution), as verified in the Blender script."""
    M = cam['matrix_world']
    R = [[M[i][j] for j in range(3)] for i in range(3)]
    C = [M[i][3] for i in range(3)]
    d = [p[i] - C[i] for i in range(3)]
    q = [sum(R[i][j] * d[i] for i in range(3)) for j in range(3)]   # R^T d
    L = max(W, H)
    return [W / 2 + cam['f_px_render'] * q[0] / -q[2] - cam['shift_x'] * L,
            H / 2 - cam['f_px_render'] * q[1] / -q[2] + cam['shift_y'] * L]


def main():
    me = json.load(open(os.path.join(WORK, 'meta_exterior.json')))
    mc = json.load(open(os.path.join(WORK, 'meta_cutaway.json')))
    anchor_rerun = None
    if mc.get('render_skipped'):
        # anchors recomputed with --no-render on the same scene: it must match the run that rendered the image
        mr = json.load(open(os.path.join(WORK, 'meta_cutaway_render.json')))
        for k in ('camera', 'airframe_elements', 'engine', 'cutaway', 'res_render', 'glb_sha256_16', 'bom_sha256_16'):
            assert mc[k] == mr[k], f'anchor re-run differs from the render run: {k}'
        mc['render_s'] = mr['render_s']
        anchor_rerun = ('cutaway anchors recomputed without re-rendering (script --no-render, anchor candidate '
                        'order changed for thrust_rings/body_tube/nose); camera, geometry summary, engine and cutaway '
                        'records asserted identical to the render run')
    for k in ('matrix_world', 'shift_x', 'shift_y', 'lens_mm', 'f_px_render'):
        assert me['camera'][k] == mc['camera'][k], f'camera differs between views: {k}'
    Wf, Hf = mc['res_final']
    Wr, Hr = mc['res_render']
    ss = mc['ss']
    size = (Wf, Hf)
    ext = composite(os.path.join(WORK, 'raw_exterior.png'), size)
    cut = composite(os.path.join(WORK, 'raw_cutaway.png'), size)

    cap_common = ('engine: real CAD v3.5.1 (frozen) · N2O tank: concept, length ESTIMATE · airframe, nose, fins, '
                  'legs and bays: ASSUMED GNC reference vehicle RV-1c, not Lauty\'s airframe design')
    cap_tail = 'Visualisation only: not a drawing, tolerance or fabrication source; not a physical approval.'
    out = {}
    out['rocket_exterior.jpg'] = caption(ext, ['ARGOS H1 vehicle concept, standing on deployed legs · ' + cap_common,
                                               cap_tail])
    out['rocket_cutaway.jpg'] = caption(cut, ['ARGOS H1 vehicle concept, cutaway (shell removed on the camera side, '
                                              'one fin omitted) · ' + cap_common, cap_tail])

    # ---------------------------------------------------------------- labelled cutaway
    A = {k: dict(v, px_final=[v['px'][0] / ss, v['px'][1] / ss]) for k, v in mc['anchors'].items()}
    for k, a in A.items():
        assert 0 <= a['px_final'][0] <= Wf and 0 <= a['px_final'][1] <= Hf, k
        assert not a['mode'].startswith('NOT VISIBLE'), f'anchor {k} not visible'
        px = cut.getpixel((int(a['px_final'][0]), int(a['px_final'][1])))
        a['pixel_rgb_unlabelled'] = list(px)
        a['differs_from_background'] = sum(abs(px[i] - BG[i]) for i in range(3)) > 12

    LBL = [
        # key, side, tag, [title, line, line...]; per-line tag override with (text, tag)
        ('drogue', 'L', 'ASSUMED', ['Nose drogue + ejection', 'ledger A09, z ~1.70 m']),
        ('backup_chute', 'L', 'ASSUMED', ['Backup parachute', 'ledger A07, z ~1.45 m']),
        ('avionics', 'L', 'ASSUMED', ['Avionics bay + battery', 'FC, IMU, GNSS, LiDAR, radio',
                                      'ledger A05/A06, drawn forward', 'of the tank (z 1.10-1.36 m)']),
        ('tank', 'L', 'CONCEPT', ['N2O tank (concept)', '6061 tube 101.6 x 3.175 mm',
                                  'z 0.58-1.08 m, length ESTIMATE']),
        ('engine', 'L', 'CAD', ['Engine v3.5.1 (real CAD)', 'frozen GLB, BOM materials',
                                'z -0.035 to 0.558 m']),
        ('fins', 'L', 'ASSUMED', ['Fins x4 (one cut away)', 'root 0.20, tip 0.10, span 0.12 m']),
        ('legs', 'L', 'ASSUMED', ['Landing legs x4, deployed', 'foot r 0.40 m, foot plane z -0.25 m']),
        ('body_tube', 'R', 'ASSUMED', ['Body tube 146 mm OD', '3 mm PETG, z 0-1.70 m,', 'ogive nose 0.30 m']),
        ('tank_engine_gap', 'R', 'TODEF', ['Engine top 0.558, tank 0.580 m', ('22 mm gap: tank line route', 'TODEF'),
                                           ('TO-DEFINE', 'TODEF')]),
        ('vent_stub', 'R', 'CAD', ['Bleed vent stub ENG-BL-06', 'real CAD, az 112 deg, r 74.2 mm',
                                   ('wall hole + outer tee TO-DEFINE', 'TODEF')]),
        ('thrust_rings', 'R', 'CAD', ['Thrust rings GM-09 / GM-10', 'real CAD, r 69.75 mm:',
                                      'the airframe interface']),
        ('gimbal_pivot', 'R', 'CAD', ['Gimbal pivot, z 0.203 m', 'on the axis, behind ring GM-03']),
    ]
    ov = Overlay(size)
    ft, fb = font('SemiBold', 15.5), font('Regular', 13.0)
    LH_T, LH_B, GAP = 20.0, 16.5, 12.0
    XL, XR = 322.0, 678.0            # left column right edge, right column left edge
    Y_MIN, Y_MAX = 150.0, 1688.0
    blocks = []
    for key, side, tag, lines in LBL:
        a = A[key]['px_final']
        h = LH_T + LH_B * (len(lines) - 1)
        blocks.append({'key': key, 'side': side, 'tag': tag, 'lines': lines, 'h': h, 'a': a,
                       'top': a[1] - LH_T / 2})
    for side in ('L', 'R'):
        col = sorted([b for b in blocks if b['side'] == side], key=lambda b: b['a'][1])
        for _ in range(50):
            for i in range(1, len(col)):
                col[i]['top'] = max(col[i]['top'], col[i - 1]['top'] + col[i - 1]['h'] + GAP)
            if col and col[-1]['top'] + col[-1]['h'] > Y_MAX:
                col[-1]['top'] = Y_MAX - col[-1]['h']
            for i in range(len(col) - 2, -1, -1):
                col[i]['top'] = min(col[i]['top'], col[i + 1]['top'] - col[i]['h'] - GAP)
            if col and col[0]['top'] < Y_MIN:
                col[0]['top'] = Y_MIN
    for b in blocks:
        c = COL[b['tag']]
        x_text = XL if b['side'] == 'L' else XR
        anchor = 'ra' if b['side'] == 'L' else 'la'
        y = b['top']
        title_mid = y + LH_T / 2 + 1
        wmax = 0.0
        for i, ln in enumerate(b['lines']):
            txt, ltag = (ln if isinstance(ln, tuple) else (ln, None))
            f = ft if i == 0 else fb
            fill = c if i == 0 else (COL[ltag] if ltag else COL['muted'])
            ov.text((x_text, y), txt, f, fill, anchor=anchor)
            wmax = max(wmax, ov.width(txt, f))
            y += LH_T if i == 0 else LH_B
        b['text_box'] = [x_text - wmax if b['side'] == 'L' else x_text, b['top'],
                         x_text if b['side'] == 'L' else x_text + wmax, b['top'] + b['h']]
        e0 = (x_text + 7, title_mid) if b['side'] == 'L' else (x_text - 7, title_mid)
        e1 = (e0[0] + 14, title_mid) if b['side'] == 'L' else (e0[0] - 14, title_mid)
        ax, ay = b['a']
        pts = [e0, e1, (ax, ay)]
        ov.line(pts, COL['halo'], 3.4, alpha=210)
        ov.line(pts, c, 1.3)
        if b['key'] == 'gimbal_pivot':
            ov.ring((ax, ay), 5.0, COL['halo'], 3.0)
            ov.ring((ax, ay), 5.0, c, 1.4)
            ov.line([(ax - 8, ay), (ax + 8, ay)], c, 1.2)
            ov.line([(ax, ay - 8), (ax, ay + 8)], c, 1.2)
        elif b['key'] == 'tank_engine_gap':
            ov.line([(ax - 9, ay), (ax + 9, ay)], COL['halo'], 3.6)
            ov.line([(ax - 9, ay), (ax + 9, ay)], c, 1.6)
        else:
            ov.dot((ax, ay), 3.0, c, outline=COL['halo'], ow=1.3)
        b['leader_px'] = [list(p) for p in pts]

    # scale bar: projection of a vertical 0.5 m segment at the depth of the vehicle axis
    cam = mc['camera']
    M = cam['matrix_world']
    rx, ry = M[0][0], M[1][0]
    rn = math.hypot(rx, ry)
    off = 0.50
    P0 = [rx / rn * off, ry / rn * off, 1.45]
    P1 = [rx / rn * off, ry / rn * off, 1.95]
    b0 = [v / ss for v in project_closed(cam, Wr, Hr, P0)]
    b1 = [v / ss for v in project_closed(cam, Wr, Hr, P1)]
    for w_, colr in ((3.6, COL['halo']), (1.6, COL['text'])):
        ov.line([b0, b1], colr, w_)
        ov.line([(b0[0] - 7, b0[1]), (b0[0] + 7, b0[1])], colr, w_)
        ov.line([(b1[0] - 7, b1[1]), (b1[0] + 7, b1[1])], colr, w_)
    ym = (b0[1] + b1[1]) / 2
    ov.text((b0[0] + 14, ym - 12), '0.5 m', font('SemiBold', 15), COL['text'])
    ov.text((b0[0] + 14, ym + 8), 'at the axis depth', fb, COL['muted'])
    ov.text((b0[0] + 14, ym + 24), '(perspective view)', fb, COL['muted'])

    # header and legend
    ov.text((40, 30), 'ARGOS H1 vehicle concept: cutaway', font('SemiBold', 24), COL['text'])
    fh = font('Regular', 13.5)
    yy = 66
    for t in wrap(ov.d, 'Real engine CAD v3.5.1 placed in the ASSUMED GNC reference airframe RV-1c (not Lauty\'s '
                  'airframe design). Leaders end on true camera projections of the labelled parts.', fh, 920):
        ov.text((40, yy), t, fh, COL['muted'])
        yy += 18
    x = 40.0
    yl = Hf - 76
    fl = font('Regular', 13.0)
    for tg in ('CAD', 'CONCEPT', 'ASSUMED', 'TODEF'):
        ov.dot((x + 5, yl + 8), 4.2, COL[tg])
        ov.text((x + 15, yl), TAG_TEXT[tg], fl, COL['text'])
        x += 15 + ov.width(TAG_TEXT[tg], fl) + 26
    yy = Hf - 50
    for t in wrap(ov.d, 'Visualisation only: not a drawing, tolerance or fabrication source; not a physical approval. '
                  'z from the aft datum, +z to the nose.', font('Regular', 12.5), 920):
        ov.text((40, yy), t, font('Regular', 12.5), COL['muted'])
        yy += 17
    out['rocket_cutaway_labelled.jpg'] = ov.apply(cut)

    # ---------------------------------------------------------------- write images
    files = {}
    for name, img in out.items():
        p = os.path.join(HERE, name)
        q = save_jpeg(img, p)
        files[name] = {'res': list(img.size), 'jpeg_quality': q, 'bytes': os.path.getsize(p), 'sha256_16': h16(p)}

    # ---------------------------------------------------------------- render_meta.json
    el = mc['airframe_elements']
    ee = me['airframe_elements']
    eng = mc['engine']
    elements = [
        {'key': 'engine', 'what': 'Engine assembly v3.5.1 (148 GLB instances; groups engine/fixed/ring/horn/'
                                  'pushrod/hose), pivot at the vehicle station of the gimbal pivot',
         'z_m': [eng['world_bbox_m'][0][2], eng['world_bbox_m'][1][2]], 'r_max_m': 0.07417,
         'status': 'REAL CAD v3.5.1 (frozen GLB; display tessellation; BOM material per part)',
         'source': 'ENGINE_v3.5.1_neutral.glb + BOM_v3.5.1.json', 'placement': 'translated +0.203 m in z; '
         'clocking CAD X = vehicle X (ASSUMED: airframe clocking not defined)'},
        {'key': 'gimbal_pivot', 'z_m': [0.203, 0.203], 'status': 'REAL CAD origin at the GNC station',
         'source': 'gnc.json reference_vehicle.gimballed_subassembly.z_pivot_m 0.203'},
        {'key': 'vent_stub ENG-BL-06', 'z_m': [0.458, 0.468], 'r_max_m': 0.07417, 'az_deg': eng['vent_stub_ENG-BL-06']['az_deg'],
         'status': 'REAL CAD; the wall hole (exterior view: visual clearance cut r %.4f m) and the outside opposed '
                   'vent tee (airframe ICD-14) are TO-DEFINE' % eng['vent_stub_ENG-BL-06']['drawn_wall_cut_radius_m'],
         'source': 'BOM ENG-BL-06 "through the bay wall at az 112"; vertex r_max 74.17 mm (trimesh, this task)'},
        {'key': 'n2o_tank', 'what': '6061 tube 101.6 OD x 3.175 wall, two flat plug bulkheads', 'z_m': el['tank']['z_m'],
         'r_max_m': el['tank']['r_max_m'],
         'status': 'CONCEPT (lead): tube size and internal length 0.445 m given; overall 0.50 m ESTIMATE; '
                   'bulkheads drawn 0.0275 m each = (0.50 - 0.445)/2, thickness not designed; closure retention, '
                   'outlet fitting and line route TO-DEFINE', 'source': 'lead brief 2026-10-15; vehicle_v3d '
         'tank_internal_length_m 0.4445'},
        {'key': 'tank_mount_rings', 'z_m': el['tank_rings']['z_m'], 'status': 'ASSUMED placeholder (6 mm rings at '
         'z 0.600 and 1.054 m); tank mounting TO-DEFINE', 'source': 'drawing choice, no source'},
        {'key': 'body_tube', 'what': '146 mm OD x 3 mm PETG', 'z_m': ee['body_tube']['z_m'],
         'r_max_m': ee['body_tube']['r_max_m'], 'status': 'ASSUMED GNC RV-1c', 'source': 'gnc.json reference_vehicle '
         '(body_diameter_m 0.146 = 0.140 ID + 2 x 3 mm PETG ASSUMED); vehicle_v3d d_id_m 0.140'},
        {'key': 'nose', 'what': 'tangent ogive L 0.30 m, 3 mm wall (wall ASSUMED = body)', 'z_m': ee['nose']['z_m'],
         'status': 'ASSUMED GNC RV-1c', 'source': 'gnc.json reference_vehicle.nose'},
        {'key': 'fins', 'what': '4 fins, root 0.20 m (LE z 0.20, TE z 0), tip 0.10 m, span 0.12 m, LE sweep 0.10 m, '
                                '3 mm; az 0/90/180/270 deg (clocking ASSUMED)', 'z_m': ee['fins']['z_m'],
         'r_max_m': ee['fins']['r_max_m'], 'status': 'ASSUMED GNC RV-1c', 'source': 'gncsim/vehicle.py fin_cr/fin_ct/'
         'fin_span/fin_sweep/fin_z_le; gnc.json reference_vehicle.fins'},
        {'key': 'landing_legs', 'what': '4 legs at az 45/135/225/315 deg (clocking ASSUMED), 20 mm main strut of '
                                        'length 0.52 m from a hinge at r 0.080 m, z %.3f m (DERIVED from leg_L) to the '
                                        'foot contact at r 0.40 m, z -0.25 m; damper strut from a wall mount at z 0.40 m '
                                        'to 55 %% of the leg (drawing choice, no source); stroke 0.10 m not drawn as a '
                                        'value' % mc['derived']['z_hinge_m'],
         'z_m': ee['legs']['z_m'], 'r_max_m': ee['legs']['r_max_m'], 'status': 'ASSUMED GNC RV-1c (Lauty to design)',
         'source': 'gncsim/vehicle.py n_legs 4, leg_d 0.020, leg_L 0.52, r_foot 0.40, z_foot -0.25; gnc.json '
         'reference_vehicle.landing_legs (stroke 0.10 m, k 2500 N/m, c 120 N s/m)'},
        {'key': 'bulkheads', 'what': '6 mm discs at z 1.090, 1.364, 1.600 m', 'z_m': el['bulkheads']['z_m'],
         'status': 'ASSUMED (ledger A03b bulkheads and couplers exists; stations are a drawing choice)',
         'source': 'mass_ledger_v3d.csv A03b'},
        {'key': 'avionics', 'what': 'sled with FC/IMU board, radio, GNSS receiver, LiDAR blocks (sizes not designed)',
         'z_m': el['avionics']['z_m'], 'status': 'ASSUMED; ledger A05 z 1.15 m moved forward to clear the tank top '
         '(1.08 m)', 'source': 'mass_ledger_v3d.csv A05'},
        {'key': 'battery', 'z_m': el['battery']['z_m'], 'status': 'ASSUMED; ledger A06 z 1.10 m moved forward '
         '(block size not designed)', 'source': 'mass_ledger_v3d.csv A06'},
        {'key': 'backup_parachute', 'z_m': el['backup_chute']['z_m'], 'status': 'ASSUMED; ledger A07 z 1.45 m '
         '(packed size not designed)', 'source': 'mass_ledger_v3d.csv A07'},
        {'key': 'nose_drogue_and_ejection', 'z_m': el['drogue']['z_m'], 'status': 'ASSUMED; ledger A09 z 1.7 m',
         'source': 'mass_ledger_v3d.csv A09'},
        {'key': 'foot_plane (floor)', 'z_m': [-0.25, -0.25], 'status': 'ASSUMED GNC (z_foot)',
         'source': 'gncsim/vehicle.py z_foot -0.25'},
    ]
    not_drawn = [
        'tank-to-engine line and its route (engine side: tank-line flange ENG-FD-12F on the MV module, ICD-5): TO-DEFINE',
        'ledger P09 NC isolation valve (v3d z 0.5 m): no room between the engine top (0.558 m) and the tank (0.58 m); '
        'whether the CAD MV module (ENG-FS-01A/B, FS-06..11) supersedes it is for the lead to confirm',
        'airframe aft thrust ring and leg mounts (ledger A03a), nose shoulder/coupler, harness, GNSS antenna in the nose '
        '(ledger A02), roll RCS provision, LiDAR ground-view aperture, outside vent tee (ICD-14), MV bracket wall '
        'fasteners at az 219.5 deg (BOM ENG-FS-15, ICD-2)',
    ]
    meta = {
        'title': 'ARGOS H1 vehicle concept renders around the real engine CAD v3.5.1',
        'generated_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'status': 'VISUALISATION ONLY: not a drawing, tolerance or fabrication source; not a physical approval. '
                  'Airframe = ASSUMED GNC reference vehicle RV-1c, not Lauty\'s design.',
        'glb_sha256_16': mc['glb_sha256_16'], 'bom_sha256_16': mc['bom_sha256_16'],
        'inputs': {k: {'path': p, 'sha256_16': h16(p)} for k, p in SOURCES.items() if os.path.exists(p)},
        'scripts': {n: h16(os.path.join(HERE, n)) for n in ('rocket_render_blender.py', 'rocket_render_post.py',
                                                             'run_renders.sh')},
        'frames': {'vehicle': 'metres, +z toward the nose, z = 0 at the aft datum (body tube aft end); Blender world '
                              'frame = vehicle frame', 'engine_glb': 'metres, +Y up = engine axis toward the injector, '
                              'origin at the gimbal pivot; importer gives +Z up = CAD engine frame',
                   'azimuth': 'from +X toward +Y (BOM convention, ENG-BL-06 at az 112)'},
        'elements': elements,
        'not_drawn': not_drawn,
        'integration_finding': {
            'claim': 'The v3d layout tank (z 0.55-0.995 m) overlaps the v3.5.1 engine, whose top is at z 0.558 m. '
                     'Drawn here: tank at z 0.58-1.08 m (22 mm gap for the tank line, route TO-DEFINE); avionics, '
                     'battery and backup chute moved forward accordingly; all still fit in the 1.70 m tube.',
            'numbers': {'engine_top_z_m': eng['world_bbox_m'][1][2], 'nozzle_exit_z_m': eng['world_bbox_m'][0][2],
                        'tank_v3d_z_m': [0.55, 0.995], 'tank_drawn_z_m': [0.58, 1.08], 'gap_m': round(0.58 - eng['world_bbox_m'][1][2], 4)},
            'consequence': 'mass properties change (tank + N2O move forward ~0.058 m); GNC must recompute CG, inertia '
                           'and margins; not done here'},
        'render': {'engine': 'Blender %s Cycles CPU' % mc['blender'], 'threads': 2, 'nice': 10,
                   'samples_max_per_pixel': mc['samples_max'], 'adaptive_threshold': mc['adaptive_threshold'],
                   'denoiser': mc['denoiser'], 'supersampling': '%gx (render %dx%d, Lanczos to %dx%d)' % (ss, Wr, Hr, Wf, Hf),
                   'view_transform': mc['view_transform'], 'look': mc['look'], 'exposure': mc['exposure'],
                   'render_s': {'exterior': me['render_s'], 'cutaway': mc['render_s']},
                   'backdrop': 'film transparent, composited on sRGB #15181c; floor fades to transparent between '
                               'r 0.6 and 7 m', 'lights': {'exterior': me['lights'], 'cutaway': mc['lights']},
                   'pil': PIL_VERSION},
        'camera': mc['camera'],
        'cutaway': mc['cutaway'],
        'anchor_rerun': anchor_rerun,
        'projection': {
            **mc['projection'],
            'labels': 'final px = render px / ss; leaders end at anchors[*].px_final',
            'max_closed_form_residual_px': max(a['closed_form_residual_px'] for a in A.values()),
            'scale_bar': {'p0_m': P0, 'p1_m': P1, 'px_final': [b0, b1],
                          'note': 'vertical 0.5 m segment at the depth of the vehicle axis, offset 0.50 m along the '
                                  'camera right vector; valid at that depth only (perspective)'}},
        'anchors': {k: {kk: a[kk] for kk in ('mode', 'p_m', 'px_final', 'hit_object', 'first_hit_object', 'occluded',
                                             'closed_form_residual_px', 'pixel_rgb_unlabelled',
                                             'differs_from_background') if kk in a} for k, a in A.items()},
        'labels': [{'key': b['key'], 'side': b['side'], 'tag': b['tag'],
                    'text': [ln if isinstance(ln, str) else ln[0] for ln in b['lines']],
                    'text_box_px': [round(v, 1) for v in b['text_box']], 'leader_px': b['leader_px']} for b in blocks],
        'outputs': files,
    }
    json.dump(meta, open(os.path.join(HERE, 'render_meta.json'), 'w'), indent=1)
    print(json.dumps(files, indent=1))
    print('anchors on rocket pixels:', {k: a['differs_from_background'] for k, a in A.items()})


if __name__ == '__main__':
    sys.exit(main())
