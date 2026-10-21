"""ARGOS H1 - to-scale side view of the whole rocket concept (SVG) and its layout ledger (JSON).

Reads (read only):
  work/engine_projection.json         true 2-D projection of the frozen engine CAD v3.5.1 GLB, made by
                                      engine_projection.py (its source hashes are re-checked here before use)
  03-cad/v3.5.1/massprops_v3.5.1.json engine wet mass and CG
  01-systems-gnc/vehicle/mass_ledger_v3d.csv, vehicle_v3d.json   GNC reference vehicle RV-1c (ASSUMED airframe)
  interfaces/gnc.json                 reference_vehicle, icd_inputs_for_airframe (keep-out cone, legs, CG band)
Writes: rocket_side_view.svg, rocket_layout.json; with --qa-narrow also work/qa_narrow.svg (phone rules forced on).
QA: every text box is measured with the Inter font metrics; overlaps between labels, leaders crossing labels and
text outside the canvas are reported for the wide (desktop) and narrow (phone, <= 640 px) states.

Frames: station z [m] from the airframe aft datum (base plane), +z toward the nose; r [m] lateral.
Drawing: X = XL + (z - ZL) * S, Y = Y0 - r * S  (S drawing units per metre; nose to the right).
Every element carries a status: real CAD v3.5.1, concept / ESTIMATE, or ASSUMED GNC reference airframe RV-1c
(not Lauty's design). Missing values are written MISSING / TO-DEFINE, never filled in.
"""
import csv, hashlib, json, math, os, sys
from PIL import ImageFont

HERE = '/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rocket/verify_drawing/rerun_inter'
WORK = '/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rocket/drawing/work'
ENG = '/home/claude/work/shared-fallback/engine'
CAD = f'{ENG}/03-cad/v3.5.1'
SRC = dict(
    projection=os.path.join(WORK, 'engine_projection.json'),
    projection_script='/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rocket/drawing/engine_projection.py',
    glb=f'{CAD}/assembly/ENGINE_v3.5.1_neutral.glb',
    manifest=f'{CAD}/assembly/assembly_manifest_v3.5.1.json',
    bom=f'{CAD}/BOM_v3.5.1.json',
    massprops=f'{CAD}/massprops_v3.5.1.json',
    ledger=f'{ENG}/01-systems-gnc/vehicle/mass_ledger_v3d.csv',
    vehicle=f'{ENG}/01-systems-gnc/vehicle/vehicle_v3d.json',
    gnc=f'{ENG}/interfaces/gnc.json',
    gnc_vehicle_py=f'{ENG}/01-systems-gnc/sim/gncsim/vehicle.py',
    changelog=f'{ENG}/interfaces/CHANGELOG.md',
)


def sha16(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()[:16]


HASH = {k: sha16(v) for k, v in SRC.items()}
PRJ = json.load(open(SRC['projection']))
for k in ('glb', 'manifest', 'bom', 'massprops'):          # the projection must belong to the current frozen CAD
    if PRJ['sources'][f'{k}_sha256_16'] != HASH[k]:
        sys.exit(f'projection is stale: {k} hash {PRJ["sources"][f"{k}_sha256_16"]} != {HASH[k]}')
MP = json.load(open(SRC['massprops']))
VEH = json.load(open(SRC['vehicle']))
GNC = json.load(open(SRC['gnc']))
LEDGER = list(csv.DictReader(open(SRC['ledger'])))

# ------------------------------------------------------------------ data (SI: m, kg)
ICD = GNC['icd_inputs_for_airframe']
PIVOT = VEH['z_pivot_m']                                   # 0.203
R_O = VEH['d_body_m'] / 2.0                                # 0.073
R_I = VEH['d_id_m'] / 2.0                                  # 0.070
Z_BODY_TOP, Z_TIP, L_NOSE = 1.70, 2.00, 0.30               # vehicle.py reference_geometry (ASSUMED RV-1)
FEAT = PRJ['features']
Z_EXIT = FEAT['nozzle_exit_station_mm'] / 1000.0           # -0.0351 (CAD)
Z_ENG_TOP = FEAT['engine_top_station_mm'] / 1000.0         # 0.5582 (CAD)
FIN = dict(n=4, span=0.12, cr=0.20, ct=0.10, sweep=0.10, z_le=0.20, t=0.003)        # vehicle.py v2 fins
LEGV = ICD['leg_design_values']['v']
LEG = dict(n=LEGV['n_legs'], r_foot=LEGV['foot_radius_m'], stroke=LEGV['stroke_min_m'],
           z_foot=-0.25, L=0.52, d=0.020)                  # z_foot, L, d: vehicle.py reference_geometry
Z_HINGE = LEG['z_foot'] + math.sqrt(LEG['L'] ** 2 - (LEG['r_foot'] - R_O) ** 2)    # DERIVED, ~0.154
KO = ICD['plume_line_clearance_rule']['v']['aft_structure_keep_out']
TANK = dict(od=0.1016, wall=0.003175, z0=0.58, z1=1.08, L_int=VEH['tank_internal_length_m'])
V3D_TANK = (0.55, 0.55 + VEH['tank_internal_length_m'])   # vehicle.py v2 tank_z_bot_inner 0.55 + internal length
DZ = 0.085                                                 # tank-top shift 1.080 - 0.9945 = 0.0855, rounded to 5 mm
LED = {r['item'].split(' ')[0]: dict(name=r['item'], m=float(r['m_kg']), z=float(r['z_m']), tag=r['tag'],
                                     owner=r['owner']) for r in LEDGER}
BAYS = [  # ledger id, short name, long name, v3d ledger station, station used here
    ('A06', 'BATTERY', 'battery', LED['A06']['z'], round(LED['A06']['z'] + DZ, 3)),
    ('A05', 'AVIONICS', 'avionics (FC, IMU, GNSS, LiDAR, radio)', LED['A05']['z'], round(LED['A05']['z'] + DZ, 3)),
    ('A07', 'BACKUP CHUTE', 'backup recovery parachute + deployment', LED['A07']['z'], round(LED['A07']['z'] + DZ, 3)),
    ('A09', 'NOSE DROGUE', 'nose drogue + ejection + release + swivel', LED['A09']['z'], LED['A09']['z']),
]
WET = MP['states']['wet']['all']
M_ENG = WET['m_kg']
Z_ENG_CG = PIVOT + WET['cg_mm'][2] / 1000.0
ENGINE_REPLACES = ['P00', 'P06', 'P07', 'P09', 'P10']      # v3d items + grain now inside the CAD engine
GRAIN_V3D = VEH['grain_kg_in_tables']
m_replaced = sum(LED[k]['m'] for k in ENGINE_REPLACES) + GRAIN_V3D
GROWTH = M_ENG - m_replaced
AIRFRAME_IDS = [k for k in LED if k.startswith('A')]
M_AIR = sum(LED[k]['m'] for k in AIRFRAME_IDS)
M_TANK, M_ECU, M_N2O = LED['P11']['m'], LED['P12']['m'], VEH['n2o_load_kg']
M_PROP = M_ENG + M_TANK + M_ECU + M_N2O
M_LIFTOFF = M_PROP + M_AIR
M_LAND = VEH['m_land_nominal_kg'] + GROWTH
Z_TANK_C = 0.5 * (TANK['z0'] + TANK['z1'])

# liftoff CG (ESTIMATE: ledger points, moved items at their new stations, N2O lumped at the tank centre)
new_z = {b[0]: b[4] for b in BAYS}
cg_items = [dict(id='ENG', name='engine v3.5.1 wet (CAD massprops)', m=M_ENG, z=Z_ENG_CG),
            dict(id='P11', name='N2O tank (ledger P11)', m=M_TANK, z=Z_TANK_C),
            dict(id='P12', name='engine ECU (ledger P12, ledger station kept, see finding F4)', m=M_ECU, z=LED['P12']['z']),
            dict(id='N2O', name='N2O load at the tank centre', m=M_N2O, z=Z_TANK_C)]
for k in AIRFRAME_IDS:
    cg_items.append(dict(id=k, name=LED[k]['name'], m=LED[k]['m'], z=new_z.get(k, LED[k]['z'])))
CG = sum(i['m'] * i['z'] for i in cg_items) / sum(i['m'] for i in cg_items)
liq = VEH['events'][0]['liquid_kg']                        # 1.877 kg liquid at liftoff (vehicle_v3d events)
z_int0 = Z_TANK_C - TANK['L_int'] / 2                      # internal cylinder centred in the envelope (ESTIMATE)
A_in = math.pi * (TANK['od'] / 2 - TANK['wall']) ** 2
RHO_LIQ = 786.0                                            # saturated liquid N2O ~20 C, approx. (LITERATURE)
h_liq = (liq / RHO_LIQ) / A_in
CG_SETTLED = (CG * M_LIFTOFF - liq * Z_TANK_C + liq * (z_int0 + h_liq / 2)) / M_LIFTOFF
CG_BAND = ICD['cg_and_length_limits']['v']['axial_cg_band_verified_m']

# ------------------------------------------------------------------ drawing frame, styles, text metrics
S = 400.0                       # drawing units per metre (1 unit = 2.5 mm)
ZL, XL = -0.25, 56.0
Y0 = 300.0
W, H = 1000.0, 872.0


def X(z):
    return XL + (z - ZL) * S


def Y(r):
    return Y0 - r * S


def f(v, d=1):
    s = f'{v:.{d}f}'
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


BG, TXT, TXT2, MUTE = '#15181c', '#e9edf2', '#b3bbc6', '#7d8794'
AIR, ENGC, TNK, TNKF, FIND, DIM = '#c3c9d2', '#f0a04b', '#86b4e3', '#4f86bf', '#ff7d6e', '#8f99a6'
CLS = {  # class: (font size, bold, letter spacing)
    't1': (22, True, 0), 't2': (12.5, False, 0), 'key': (15.5, True, 0), 'fine': (12, False, 0), 'tag': (10, True, 0.5),
    'sm': (11, False, 0), 'hd': (13, True, 0.6), 'tb': (12.5, False, 0), 'tbb': (12.5, True, 0), 'tbs': (11.5, False, 0),
    'big': (27, True, 0)}
FONTDIR = '/usr/share/fonts/opentype/inter'
_F = {False: ImageFont.truetype(f'{FONTDIR}/Inter-Regular.otf', 200), True: ImageFont.truetype(f'{FONTDIR}/Inter-Bold.otf', 200)}


def tw(s, cls, size=None):
    fs, bold, ls = CLS[cls]
    fs = size or fs
    return _F[bold].getlength(s) * fs / 200.0 + ls * len(s)


BOXES, SEGS = [], []    # QA registries: text boxes (x0, y0, x1, y1, state, owner, text), leader segments


def reg(x, y, s, cls, anchor='start', state='b', owner='', size=None, extra_w=0.0):
    fs = size or CLS[cls][0]
    w = tw(s, cls, size) + extra_w
    x0 = x if anchor == 'start' else x - w / 2 if anchor == 'middle' else x - w
    BOXES.append((x0, y - 0.74 * fs, x0 + w, y + 0.22 * fs, state, owner, s))
    return w


out = []


def add(s):
    out.append(s)


def poly(pts, close=True, d=1):
    s = 'M' + ' L'.join(f'{f(x, d)} {f(y, d)}' for x, y in pts)
    return s + (' Z' if close else '')


def line(x1, y1, x2, y2, stroke, w=1.0, extra=''):
    add(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" stroke="{stroke}" stroke-width="{w}" {extra}/>')


def text(x, y, s, cls, anchor='start', extra='', state='b', owner='', size=None, wrap=None):
    """one text line; state b = both views, w = wide only, n = narrow (phone) only."""
    reg(x, y, s, cls, anchor, state, owner, size)
    c = cls + (' wide' if state == 'w' else ' nar' if state == 'n' else '')
    a = '' if anchor == 'start' else f' text-anchor="{anchor}"'
    st = f' style="font-size:{size}px"' if size else ''
    add(f'<text x="{f(x)}" y="{f(y)}" class="{c}"{a}{st} {extra}>{esc(s)}</text>')


def arrow(x, y, ang, color, size=6.0):
    """filled arrowhead with its tip at (x, y), pointing along ang (radians, SVG coordinates)."""
    a1, a2 = ang + math.pi - 0.38, ang + math.pi + 0.38
    p = [(x, y), (x + size * math.cos(a1), y + size * math.sin(a1)), (x + size * math.cos(a2), y + size * math.sin(a2))]
    add(f'<path d="{poly(p, d=2)}" fill="{color}"/>')


def callout(owner, key, fines, short, leader, lx, ly, color=TXT, tag=None, align='left', dot=True):
    """leader + key title (+ status tag) + fine lines (wide view) + short title (phone view).
    align='right': the block is right-aligned at lx (start positions computed from measured widths)."""
    if leader:
        add(f'<path d="{poly(leader, close=False)}" fill="none" stroke="{MUTE}" stroke-width="0.8"/>')
        for a, b in zip(leader[:-1], leader[1:]):
            SEGS.append((a, b, owner))
        if dot:
            add(f'<circle cx="{f(leader[0][0])}" cy="{f(leader[0][1])}" r="2.2" fill="{MUTE}"/>')
    kw = tw(key, 'key') + (6 + tw(tag[0], 'tag') if tag else 0)
    x_key = lx - kw if align == 'right' else lx
    reg(x_key, ly, key, 'key', 'start', 'w', owner, extra_w=kw - tw(key, 'key'))
    k = esc(key) + (f'<tspan class="tag" fill="{tag[1]}" dx="6">{esc(tag[0])}</tspan>' if tag else '')
    add('<g class="wide">')
    add(f'<text x="{f(x_key)}" y="{f(ly)}" class="key" fill="{color}">{k}</text>')
    for i, s in enumerate(fines):
        xs = lx - tw(s, 'fine') if align == 'right' else lx
        reg(xs, ly + 15 + 14 * i, s, 'fine', 'start', 'w', owner)
        add(f'<text x="{f(xs)}" y="{f(ly + 15 + 14 * i)}" class="fine">{esc(s)}</text>')
    add('</g>')
    xs = lx - tw(short, 'big') if align == 'right' else lx
    reg(xs, ly + 4, short, 'big', 'start', 'n', owner)
    add(f'<text x="{f(xs)}" y="{f(ly + 4)}" class="big nar" fill="{color}">{esc(short)}</text>')


# ------------------------------------------------------------------ SVG header
add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {f(W)} {f(H)}" width="{f(W)}" height="{f(H)}" '
    f'role="img" aria-labelledby="ttl dsc">')
add('<title id="ttl">ARGOS H1 rocket concept - side view to scale</title>')
add('<desc id="dsc">To-scale side view, nose to the right, station z in metres from the aft datum. The engine outline is the '
    'true projection of the frozen engine CAD v3.5.1; the N2O tank is a concept with an estimated length; airframe, '
    'fins, legs, nose and bays are the ASSUMED GNC reference vehicle RV-1c, not Lauty\'s design. '
    'Not a fabrication drawing and not a physical approval.</desc>')
add('<style>'
    'text{font-family:Inter,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}'
    f'.t1{{font-size:22px;font-weight:700;fill:{TXT}}}'
    f'.t2{{font-size:12.5px;fill:{TXT2}}}'
    '.key{font-size:15.5px;font-weight:700}'
    f'.fine{{font-size:12px;fill:{TXT2}}}'
    '.tag{font-size:10px;font-weight:700;letter-spacing:0.5px}'
    f'.sm{{font-size:11px;fill:{TXT2}}}'
    f'.hd{{font-size:13px;font-weight:700;fill:{TXT};letter-spacing:0.6px}}'
    f'.tb{{font-size:12.5px;fill:{TXT}}}'
    f'.tbb{{font-size:12.5px;font-weight:700;fill:{TXT}}}'
    f'.tbs{{font-size:11.5px;fill:{TXT2}}}'
    '.big{font-size:27px;font-weight:700}'
    '.nar{display:none}'
    '@media (max-width:640px){.wide{display:none}.nar{display:inline}}'
    '</style>')
add(f'<rect width="{f(W)}" height="{f(H)}" fill="{BG}"/>')

# ------------------------------------------------------------------ title
text(24, 34, 'ARGOS H1 — rocket concept, side view to scale', 't1', state='w', owner='title')
text(24, 54, 'Station z in metres from the airframe aft datum, nose to the right. Engine = real CAD v3.5.1 '
     '(projected silhouette). Tank = concept.', 't2', state='w', owner='title')
text(24, 70, 'Airframe, fins, legs, nose and bays = ASSUMED GNC reference vehicle RV-1c, not Lauty\'s design. '
     'Not a fabrication drawing; no physical approval.', 't2', state='w', owner='title')
text(24, 46, 'ARGOS H1 rocket — to scale', 'big', state='n', owner='title', size=34, extra=f'fill="{TXT}"')

# ------------------------------------------------------------------ centreline
line(X(-0.06), Y0, X(2.03), Y0, '#4f5864', 0.8, 'stroke-dasharray="16 4 3 4"')

# ------------------------------------------------------------------ plume keep-out cone (GNC rule, not validated)
th = math.radians(KO['theta_deg'])
z_ko = Z_EXIT - KO['x_max_m']
r_ko = KO['r_e_m'] + KO['x_max_m'] * math.tan(th)
add(f'<path class="wide" d="{poly([(X(Z_EXIT), Y(KO["r_e_m"])), (X(z_ko), Y(r_ko)), (X(z_ko), Y(-r_ko)), (X(Z_EXIT), Y(-KO["r_e_m"]))], close=False)}" '
    f'fill="{FIND}" fill-opacity="0.06" stroke="{FIND}" stroke-opacity="0.6" stroke-width="0.8" stroke-dasharray="3 3"/>')
text(X(-0.155), Y0 - 3, 'plume', 'sm', 'middle', state='w', owner='ko')
text(X(-0.155), Y0 + 10, 'keep-out', 'sm', 'middle', state='w', owner='ko')

# ------------------------------------------------------------------ legs (deployed, rotated into the drawing plane)
uz, ur = LEG['z_foot'] - Z_HINGE, LEG['r_foot'] - R_O
Lg = math.hypot(uz, ur)
uz, ur = uz / Lg, ur / Lg
nz, nr = -ur, uz
w2 = LEG['d'] / 2
for sg in (1, -1):
    hz, hr = Z_HINGE, sg * R_O
    fz, fr = LEG['z_foot'], sg * LEG['r_foot']
    q = [(hz + w2 * nz, hr + sg * w2 * nr), (fz + w2 * nz, fr + sg * w2 * nr), (fz - w2 * nz, fr - sg * w2 * nr), (hz - w2 * nz, hr - sg * w2 * nr)]
    add(f'<path d="{poly([(X(a), Y(b)) for a, b in q])}" fill="{AIR}" fill-opacity="0.16" stroke="{AIR}" stroke-width="0.9"/>')
    add(f'<circle cx="{f(X(hz))}" cy="{f(Y(hr))}" r="3.2" fill="{BG}" stroke="{AIR}" stroke-width="1"/>')
    add(f'<circle cx="{f(X(fz))}" cy="{f(Y(fr))}" r="4" fill="{AIR}"/>')
line(X(LEG['z_foot']), Y(0.445), X(LEG['z_foot']), Y(-0.445), DIM, 0.9, 'stroke-dasharray="6 4"')
add(f'<text class="sm wide" transform="translate({f(X(LEG["z_foot"]) - 6)} {f(Y0)}) rotate(-90)" text-anchor="middle">'
    f'foot plane z −0.25 m (ground at touchdown)</text>')

# ------------------------------------------------------------------ fins (two of four, in the drawing plane)
for sg in (1, -1):
    q = [(FIN['z_le'], R_O), (FIN['z_le'] - FIN['sweep'], R_O + FIN['span']),
         (FIN['z_le'] - FIN['sweep'] - FIN['ct'], R_O + FIN['span']), (FIN['z_le'] - FIN['cr'], R_O)]
    add(f'<path d="{poly([(X(a), Y(sg * b)) for a, b in q])}" fill="{AIR}" fill-opacity="0.13" stroke="{AIR}" stroke-width="0.9"/>')

# ------------------------------------------------------------------ body tube (section: 3 mm PETG wall) + ogive nose
for sg in (1, -1):
    add(f'<rect x="{f(X(0))}" y="{f(min(Y(sg * R_O), Y(sg * R_I)), 2)}" width="{f(Z_BODY_TOP * S)}" height="{f(abs(R_O - R_I) * S, 2)}" '
        f'fill="{AIR}" fill-opacity="0.35"/>')
    line(X(0), Y(sg * R_O), X(Z_BODY_TOP), Y(sg * R_O), AIR, 1.1)
    line(X(0), Y(sg * R_I), X(Z_BODY_TOP), Y(sg * R_I), AIR, 0.5, 'stroke-opacity="0.75"')
    line(X(0), Y(sg * R_O), X(0), Y(sg * R_I), AIR, 1.1)
line(X(Z_BODY_TOP), Y(R_O), X(Z_BODY_TOP), Y(-R_O), AIR, 0.7, 'stroke-dasharray="4 3"')
rho = (R_O ** 2 + L_NOSE ** 2) / (2 * R_O)                 # tangent ogive radius
og = []
for i in range(41):
    x = L_NOSE * i / 40.0                                   # distance from the tip
    og.append((Z_TIP - x, math.sqrt(max(rho ** 2 - (L_NOSE - x) ** 2, 0.0)) + R_O - rho))
top = [(X(z), Y(r)) for z, r in reversed(og)]
bot = [(X(z), Y(-r)) for z, r in og]
add(f'<path d="{poly(top + bot, close=False, d=2)}" fill="{AIR}" fill-opacity="0.07" stroke="{AIR}" stroke-width="1.1"/>')

# ------------------------------------------------------------------ N2O tank (concept; closures not designed -> dashed ends)
r_to, r_ti = TANK['od'] / 2, TANK['od'] / 2 - TANK['wall']
add(f'<rect x="{f(X(TANK["z0"]))}" y="{f(Y(r_to))}" width="{f((TANK["z1"] - TANK["z0"]) * S)}" height="{f(2 * r_to * S)}" '
    f'fill="{TNKF}" fill-opacity="0.22"/>')
for sg in (1, -1):
    add(f'<rect x="{f(X(TANK["z0"]))}" y="{f(min(Y(sg * r_to), Y(sg * r_ti)), 2)}" width="{f((TANK["z1"] - TANK["z0"]) * S)}" '
        f'height="{f((r_to - r_ti) * S, 2)}" fill="{TNK}" fill-opacity="0.55"/>')
    line(X(TANK['z0']), Y(sg * r_to), X(TANK['z1']), Y(sg * r_to), TNK, 1.1)
for z in (TANK['z0'], TANK['z1']):
    line(X(z), Y(r_to), X(z), Y(-r_to), TNK, 1.1, 'stroke-dasharray="4 3"')


# ------------------------------------------------------------------ engine: true projected silhouette of CAD v3.5.1
def mm2xy(p):
    return (X(p[0] / 1000.0), Y(p[1] / 1000.0))


def union_edge(s_mm, lower=True):
    """lateral of the silhouette edge at station s (mm) on the outer loop (bottom or top)."""
    L, ls = PRJ['outline_union'][0], []
    for i in range(len(L)):
        (s1, l1), (s2, l2) = L[i], L[(i + 1) % len(L)]
        if (s1 - s_mm) * (s2 - s_mm) < 0:
            ls.append(l1 + (l2 - l1) * (s_mm - s1) / (s2 - s1))
    return min(ls) if lower else max(ls)


union_d = ' '.join(poly([mm2xy(p) for p in lp], d=2) for lp in PRJ['outline_union'])
parts_d = ' '.join(poly([mm2xy(p) for p in lp], d=1) for v in PRJ['parts'].values() for lp in v['loops'])
add(f'<path d="{union_d}" fill="{ENGC}" fill-opacity="0.24" fill-rule="evenodd" stroke="none"/>')
add(f'<path class="wide" d="{parts_d}" fill="none" stroke="{ENGC}" stroke-opacity="0.5" stroke-width="0.35" stroke-linejoin="round"/>')
add(f'<path d="{union_d}" fill="none" stroke="{ENGC}" stroke-width="1.1" stroke-linejoin="round"/>')
for k, lps in PRJ['outline_swept_aft'].items():
    d = ' '.join(poly([mm2xy(p) for p in lp], d=2) for lp in lps)
    add(f'<path class="wide" d="{d}" fill="none" stroke="{ENGC}" stroke-opacity="0.85" stroke-width="0.7" stroke-dasharray="3 2.5"/>')
px_, py_ = X(PIVOT), Y0                                    # gimbal pivot marker
add(f'<circle cx="{f(px_)}" cy="{f(py_)}" r="4.5" fill="{BG}" stroke="{TXT}" stroke-width="1.1"/>')
line(px_ - 7.5, py_, px_ + 7.5, py_, TXT, 1.0)
line(px_, py_ - 7.5, px_, py_ + 7.5, TXT, 1.0)
line(X(Z_EXIT), Y(0.05), X(Z_EXIT), Y(-0.05), TXT, 0.9, 'stroke-dasharray="3 2"')   # nozzle exit plane

# ------------------------------------------------------------------ tank line (route TO-DEFINE) + integration finding
fd = FEAT['FD12F_tank_line_flange']
s_fd = 0.5 * (fd['station_mm'][0] + fd['station_mm'][1]) / 1000.0
l_fd = 0.5 * (fd['projected_lateral_mm'][0] + fd['projected_lateral_mm'][1]) / 1000.0
add(f'<path d="{poly([(X(s_fd), Y(l_fd)), (X(TANK["z0"]) - 1, Y(l_fd))], close=False)}" stroke="{TNK}" stroke-width="1.4" '
    f'stroke-dasharray="2.5 2" fill="none"/>')
add(f'<rect x="{f(X(V3D_TANK[0]), 2)}" y="{f(Y(r_to))}" width="{f((Z_ENG_TOP - V3D_TANK[0]) * S, 2)}" height="{f(2 * r_to * S)}" '
    f'fill="{FIND}" fill-opacity="0.6"/>')                 # overlap of GNC v3d tank (0.550) with the engine top (0.558)
yb = Y(0.091)
line(X(V3D_TANK[0]), yb, X(V3D_TANK[1]), yb, FIND, 1.2, 'stroke-dasharray="5 3"')
for z in V3D_TANK:
    line(X(z), yb - 4, X(z), yb + 5, FIND, 1.2)
yg = Y(0.034)                                              # gap dimension, arrows from outside
line(X(Z_ENG_TOP) - 16, yg, X(Z_ENG_TOP), yg, TXT, 0.8)
line(X(TANK['z0']), yg, X(TANK['z0']) + 16, yg, TXT, 0.8)
arrow(X(Z_ENG_TOP), yg, 0.0, TXT, 5)
arrow(X(TANK['z0']), yg, math.pi, TXT, 5)

# ------------------------------------------------------------------ bays (ledger point stations; lengths MISSING)
for bid, short, name, z_old, z_new in BAYS:
    xx = X(z_new)
    add(f'<path d="{poly([(xx, Y0 - 5), (xx + 5, Y0), (xx, Y0 + 5), (xx - 5, Y0)])}" fill="{BG}" stroke="{AIR}" stroke-width="1.1"/>')
ya = Y(-0.054)
x_a0, x_a1 = X(TANK['z1']) + 1, X(Z_BODY_TOP) - 1
line(x_a0, ya, x_a1, ya, DIM, 0.8)
arrow(x_a0, ya, math.pi, DIM, 5)
arrow(x_a1, ya, 0.0, DIM, 5)
s_av = f'{Z_BODY_TOP - TANK["z1"]:.2f} m to nose joint'
text(0.5 * (X(BAYS[0][4]) + X(1.645)), ya - 4, s_av, 'sm', 'middle', state='w', owner='avail')

# ------------------------------------------------------------------ CG estimate marker
cx, cy = X(CG), Y0
add(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="6" fill="{BG}" stroke="{TXT}" stroke-width="1.1"/>')
add(f'<path d="M{f(cx)} {f(cy)} L{f(cx + 6)} {f(cy)} A6 6 0 0 0 {f(cx)} {f(cy - 6)} Z M{f(cx)} {f(cy)} L{f(cx - 6)} {f(cy)} '
    f'A6 6 0 0 0 {f(cx)} {f(cy + 6)} Z" fill="{TXT}"/>')

# ------------------------------------------------------------------ body diameter dimension (inside the body)
xd = X(1.645)
line(xd, Y(R_O), xd, Y(-R_O), TXT, 0.8)
arrow(xd, Y(R_O), -math.pi / 2, TXT, 5)
arrow(xd, Y(-R_O), math.pi / 2, TXT, 5)
add(f'<text class="sm" transform="translate({f(xd - 4)} {f(Y0)}) rotate(-90)" text-anchor="middle" style="fill:{TXT}">Ø146</text>')

# ------------------------------------------------------------------ overall length chain dimension
yd = 484.0
for z, r in ((Z_EXIT, -0.03), (0.0, -R_O), (Z_BODY_TOP, -R_O), (Z_TIP, 0.0)):
    line(X(z), Y(r) + 3, X(z), yd + 5, DIM, 0.6, '' if z in (Z_TIP, Z_EXIT) else 'stroke-dasharray="2 2"')
line(X(Z_EXIT), yd, X(Z_TIP), yd, DIM, 0.8)
for z in (0.0, Z_BODY_TOP):
    line(X(z) - 3, yd + 3, X(z) + 3, yd - 3, DIM, 1.0)
arrow(X(Z_EXIT), yd, math.pi, DIM, 6)
arrow(X(Z_TIP), yd, 0.0, DIM, 6)
text(0.5 * (X(0) + X(Z_BODY_TOP)), yd - 4, '1.700 body tube', 'sm', 'middle', state='w', owner='dim')
text(0.5 * (X(Z_BODY_TOP) + X(Z_TIP)), yd - 4, '0.300 ogive nose', 'sm', 'middle', state='w', owner='dim')
text(X(Z_EXIT) - 9, yd + 4, f'{-Z_EXIT:.3f}', 'sm', 'end', state='w', owner='dim')
text(0.5 * (X(Z_EXIT) + X(Z_TIP)), yd + 17, f'{Z_TIP - Z_EXIT:.3f} m overall: nozzle exit z {Z_EXIT:.3f} → nose tip z {Z_TIP:.3f}'.replace('-', '−'),
     'tbb', 'middle', state='w', owner='dim')
text(0.5 * (X(Z_EXIT) + X(Z_TIP)), yd + 28, f'{Z_TIP - Z_EXIT:.3f} m', 'big', 'middle', state='n', owner='dim', extra=f'fill="{TXT}"')

# ------------------------------------------------------------------ station axis + scale bar
yx = 528.0
line(X(-0.25), yx, X(2.0), yx, DIM, 0.8)
for i in range(-5, 41):
    z = i * 0.05
    line(X(z), yx, X(z), yx + (7 if i % 2 == 0 else 4), DIM, 0.8)
    if i % 2 == 0:
        text(X(z), yx + 19, f'{z:.1f}'.replace('-', '−'), 'sm', 'middle', state='w', owner='axis')
for z in (0.0, 0.5, 1.0, 1.5, 2.0):
    text(X(z), yx + 33, f'{z:.1f}', 'big', 'middle', state='n', owner='axis', extra=f'fill="{TXT2}"')
text(X(-0.25), yx + 36, f'station z (m) from the aft datum, +z toward the nose · seen from engine az {PRJ["frames"]["viewed_from_az_deg"]:.0f}° (vent az 112° up) · 1 unit = 2.5 mm', 'sm', state='w', owner='axis')
xs0 = X(1.66)
line(xs0, yx + 32, xs0 + 0.1 * S, yx + 32, TXT, 3.0)
line(xs0, yx + 27, xs0, yx + 37, TXT, 1.0)
line(xs0 + 0.1 * S, yx + 27, xs0 + 0.1 * S, yx + 37, TXT, 1.0)
text(xs0 + 0.1 * S + 8, yx + 36, '0.1 m scale bar', 'sm', state='w', owner='axis')

# ------------------------------------------------------------------ callouts
U1, U2, U3 = 98.0, 160.0, 220.0
L1, L2 = 362.0, 420.0
CADT, CONT, ASST, FNDT = ('REAL CAD', ENGC), ('CONCEPT', TNK), ('ASSUMED', AIR), ('FINDING', FIND)
t_leg = 0.66
lz, lr = Z_HINGE + t_leg * (LEG['z_foot'] - Z_HINGE), R_O + t_leg * (LEG['r_foot'] - R_O)
callout('legs', 'LANDING LEGS ×4', [f'deployed · foot r {LEG["r_foot"]:.2f} m · feet at z −0.25 m',
                                    f'stroke {LEG["stroke"]:.2f} m · Ø20 mm · hinge z {Z_HINGE:.3f} (derived)',
                                    'GNC RV-1c values; Lauty designs the legs'],
        'LEGS', [(X(lz), Y(lr)), (X(lz), U1 + 48)], 96, U1, tag=ASST)
callout('fins', 'FINS ×4', ['span 0.12 · chords 0.20 / 0.10', 'LE sweep 0.10 · 3 mm GF/PETG'],
        'FINS', [(X(0.12), Y(0.15)), (X(0.12), U2 + 34)], 152, U2, tag=ASST)
xv = X(sum(FEAT['BL06_vent_stub']['station_mm']) / 2000.0)
callout('vent', 'BLEED VENT STUB', ['ENG-BL-06 crosses the bay wall: r 74.2 mm',
                                    'at z 0.458–0.468 · wall hole + tee TO-DEFINE'],
        'VENT STUB', [(xv, Y(FEAT['BL06_vent_stub']['r_max_mm'] / 1000.0)), (xv, U2 - 5), (xv + 6, U2 - 5)], xv + 10, U2, tag=CADT)
callout('moved', 'TANK MOVED UP', [f'GNC v3d tank {V3D_TANK[0]:.3f}–{V3D_TANK[1]:.3f} m (red) overlaps',
                                   f'engine top {Z_ENG_TOP:.3f} → now {TANK["z0"]:.2f}–{TANK["z1"]:.2f}, gap {1000 * (TANK["z0"] - Z_ENG_TOP):.0f} mm'],
        'TANK MOVED UP', [(X(V3D_TANK[0]) + 26, yb), (X(V3D_TANK[0]) + 26, U3 + 35)], xv + 10, U3, color=FIND, tag=FNDT, dot=False)
xav = X(BAYS[1][4])
callout('avio', 'AVIONICS', ['FC, IMU, GNSS, LiDAR, radio · ledger point',
                             f'z {BAYS[1][4]:.3f} (v3d {BAYS[1][3]:.2f} + {DZ:.3f}) · bay length MISSING'],
        'AVIONICS', [(xav, Y0 - 6), (xav, U1 - 5), (xav + 6, U1 - 5)], xav + 10, U1, tag=ASST)
xbk = X(BAYS[2][4])
callout('backup', 'BACKUP CHUTE', [f'z {BAYS[2][4]:.3f} (v3d {BAYS[2][3]:.2f} + {DZ:.3f})', 'length MISSING'],
        'BACKUP CHUTE', [(xbk, Y0 - 6), (xbk, U2 - 5), (xbk + 6, U2 - 5)], xbk + 10, U2, tag=ASST)
xdr = X(BAYS[3][4])
callout('drogue', 'DROGUE', [f'nose bay · z {BAYS[3][4]:.2f}', '+ ejection, swivel'],
        'DROGUE', [(xdr, Y0 - 6), (xdr, U3 - 5), (xdr + 6, U3 - 5)], xdr + 10, U3, tag=ASST)
s_e = 300.0
callout('engine', 'ENGINE v3.5.1', ['projected GLB outline', f'{FEAT["engine_top_station_mm"] - FEAT["nozzle_exit_station_mm"]:.0f} mm · {M_ENG:.2f} kg wet',
                                    f'⊕ pivot {PIVOT:.3f} · exit {Z_EXIT:.3f}'.replace('-', '−'),
                                    'rings r 69.75 = interface', 'dashed: ±8° sweep r ≤ 61.3'],
        'ENGINE', [(X(s_e / 1000.0), Y(union_edge(s_e) / 1000.0 + 0.002)), (X(s_e / 1000.0), L1 - 15)],
        234, L1, tag=CADT)
callout('cg', 'LIFTOFF CG ≈ 0.66 m', ['ESTIMATE: ledger points,', 'N2O at the tank centre;', f'GNC band {CG_BAND[0]:.3f}–{CG_BAND[1]:.3f} m'],
        'CG ≈ 0.66', [(cx, cy + 7), (cx, L2 - 5), (cx + 6, L2 - 5)], cx + 10, L2, dot=False)
xbt = X(BAYS[0][4])
callout('battery', 'BATTERY', [f'ledger point z {BAYS[0][4]:.3f}', f'(v3d {BAYS[0][3]:.2f} + {DZ:.3f}) · length MISSING'],
        'BATTERY', [(xbt, Y0 + 6), (xbt, L1 - 5), (xbt + 6, L1 - 5)], xbt + 10, L1, tag=ASST)
xn = X(1.86)
callout('nose', 'NOSE', ['tangent ogive 0.30 m', 'tip z 2.000'], 'NOSE',
        [(xn, Y(-0.032)), (xn, L2 - 5), (xn - 6, L2 - 5)], xn - 10, L2, tag=ASST, align='right')
# tank label inside the tank
text(X(0.85), Y0 - 3, 'N2O TANK', 'tbb', 'middle', state='w', owner='tank')
text(X(0.85), Y0 + 12, 'concept · 0.50 m (estimate)', 'sm', 'middle', state='w', owner='tank')
text(X(0.85), Y0 + 10, 'TANK', 'big', 'middle', state='n', owner='tank', extra=f'fill="{TNK}"')

# ------------------------------------------------------------------ bottom band: status legend, findings, masses
YB = 572.0
line(24, YB, W - 24, YB, '#2c323a', 1.0)
add('<g class="wide">')
text(24, YB + 22, 'STATUS', 'hd', owner='leg', state='w')
leg_rows = [
    (ENGC, 'fill', 'Real CAD v3.5.1 — frozen engine, projected GLB outline'),
    (TNK, 'fill', 'Concept / ESTIMATE — N2O tank, closures not designed'),
    (AIR, 'fill', 'ASSUMED airframe RV-1c (GNC) — not Lauty\'s design'),
    (FIND, 'dash', 'Integration finding / superseded GNC v3d layout'),
    (DIM, 'dash', 'Dashed = not designed / TO-DEFINE'),
]
for i, (c, kind, s) in enumerate(leg_rows):
    yy = YB + 44 + 20 * i
    if kind == 'fill':
        add(f'<rect x="24" y="{f(yy - 10)}" width="22" height="12" fill="{c}" fill-opacity="0.35" stroke="{c}" stroke-width="1.1"/>')
    else:
        line(24, yy - 4, 46, yy - 4, c, 1.6, 'stroke-dasharray="5 3"')
    text(54, yy, s, 'tb', owner='leg', state='w')
text(24, YB + 166, 'FINDINGS', 'hd', owner='find', state='w')
finds = [
    ('1', f'GNC v3d tank {V3D_TANK[0]:.3f}–{V3D_TANK[1]:.3f} m overlaps the engine top ({Z_ENG_TOP:.3f} m).'),
    ('', f'Moved to {TANK["z0"]:.3f}–{TANK["z1"]:.3f} m: {1000 * (TANK["z0"] - Z_ENG_TOP):.0f} mm gap, tank line route TO-DEFINE.'),
    ('2', f'Battery, avionics, backup chute moved +{DZ:.3f} m; bay lengths MISSING.'),
    ('3', 'Vent stub reaches r 74.2 > 73 mm OD: wall hole + outside tee TO-DEFINE.'),
    ('4', f'ECU ledger point z {LED["P12"]["z"]:.2f} m lies inside the engine envelope: TO-DEFINE.'),
    ('5', f'Liftoff CG ≈ {CG:.3f} m: ESTIMATE in the GNC band, not a GNC run.'),
    ('6', 'Fins and legs drawn rotated into this plane; clocking TO-DEFINE.'),
]
for i, (n, s) in enumerate(finds):
    if n:
        text(24, YB + 188 + 15 * i, n, 'tbs', owner='find', state='w', extra=f'style="fill:{FIND}"')
    text(38, YB + 188 + 15 * i, s, 'tbs', owner='find', state='w')
mx = 500.0
text(mx, YB + 22, 'MASS (kg) — current lead estimate, not frozen', 'hd', owner='mass', state='w')
rows = [
    ('Engine v3.5.1, wet incl. grain', M_ENG, 'CAD massprops v3.5.1', ENGC, False),
    ('N2O tank (ledger P11)', M_TANK, 'ledger, closures ASSUMED', TNK, False),
    ('Engine ECU (ledger P12)', M_ECU, 'ledger ASSUMED', AIR, False),
    ('N2O load', M_N2O, 'REQ lead 2026-10-12', TNK, False),
    ('Propulsion subtotal', M_PROP, 'sum', None, True),
    ('Airframe group A01–A10', M_AIR, 'ledger v3d ASSUMED, 11 items', AIR, False),
    ('Liftoff', M_LIFTOFF, 'ESTIMATE, row sum', None, True),
    ('Landing', M_LAND, 'ESTIMATE, not re-simulated', None, True),
]
yy = YB + 44
text(mx + 10, yy, 'item', 'tbs', owner='mass', state='w')
text(mx + 262, yy, 'kg', 'tbs', 'end', owner='mass', state='w')
text(mx + 276, yy, 'basis / tag', 'tbs', owner='mass', state='w')
line(mx, yy + 6, W - 24, yy + 6, '#2c323a', 1.0)
for i, (name, m, basis, c, bold) in enumerate(rows):
    yy = YB + 66 + 21 * i
    if bold:
        line(mx, yy - 15, W - 24, yy - 15, '#2c323a', 0.8)
    if c:
        add(f'<rect x="{f(mx)}" y="{f(yy - 9)}" width="4" height="10" fill="{c}"/>')
    text(mx + 10, yy, name, 'tbb' if bold else 'tb', owner='mass', state='w')
    text(mx + 262, yy, f'{m:.2f}', 'tbb' if bold else 'tb', 'end', owner='mass', state='w')
    text(mx + 276, yy, basis, 'tbs', owner='mass', state='w')
yy = YB + 66 + 21 * len(rows) + 4
for s in [f'Engine growth vs GNC v3d: {M_ENG:.2f} − (P00, P06, P07, P09, P10 + {GRAIN_V3D:.3f} grain)',
          f'= +{GROWTH:.2f} kg; landing = v3d SIM {VEH["m_land_nominal_kg"]:.2f} + {GROWTH:.2f}. Lead quotes ≈17.4 / ≈16.1 kg.',
          'Max thrust 500 N · first-flight target apogee 210 m (SIM, lead decision).']:
    text(mx, yy, s, 'sm', owner='mass', state='w')
    yy += 14
add('</g>')
nb = [(ENGC, 'Engine — real CAD v3.5.1'), (TNK, 'Tank — concept / estimate'), (AIR, 'Airframe — ASSUMED, not Lauty\'s')]
add('<g class="nar">')
for i, (c, s) in enumerate(nb):
    yy = YB + 46 + 40 * i
    add(f'<rect x="24" y="{f(yy - 20)}" width="34" height="22" fill="{c}" fill-opacity="0.35" stroke="{c}" stroke-width="1.5"/>')
    reg(70, yy, s, 'big', state='n', owner='nleg')
    add(f'<text x="70" y="{f(yy)}" class="big" fill="{TXT}">{esc(s)}</text>')
for i, s in enumerate([f'Liftoff {M_LIFTOFF:.2f} kg · landing {M_LAND:.2f} kg', f'Propulsion {M_PROP:.2f} · airframe {M_AIR:.2f} kg',
                       'Estimates, not frozen · no physical approval']):
    reg(24, YB + 186 + 40 * i, s, 'big', state='n', owner='nmass', size=25)
    add(f'<text x="24" y="{f(YB + 186 + 40 * i)}" class="big" fill="{TXT2}" style="font-size:25px">{esc(s)}</text>')
add('</g>')
add('</svg>')


# ------------------------------------------------------------------ QA: overlaps and canvas bounds per view state
def seg_hits_box(a, b, bx):
    x0, y0, x1, y1 = bx[:4]
    for t in [i / 40.0 for i in range(41)]:
        x, y = a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
        if x0 + 0.5 < x < x1 - 0.5 and y0 + 0.5 < y < y1 - 0.5:
            return True
    return False


problems = []
for st in ('w', 'n'):
    vis = [b for b in BOXES if b[4] in (st, 'b')]
    for i, a in enumerate(vis):
        if a[0] < 2 or a[2] > W - 2 or a[1] < 2 or a[3] > H - 2:
            problems.append(f'[{st}] outside canvas: {a[6]!r} x {a[0]:.0f}-{a[2]:.0f} y {a[1]:.0f}-{a[3]:.0f}')
        for b in vis[i + 1:]:
            if a[0] < b[2] - 0.5 and b[0] < a[2] - 0.5 and a[1] < b[3] - 0.5 and b[1] < a[3] - 0.5:
                problems.append(f'[{st}] overlap: {a[6]!r} <> {b[6]!r}')
    for p, q, own in SEGS:
        for b in vis:
            if b[5] != own and seg_hits_box(p, q, b):
                problems.append(f'[{st}] leader of {own} crosses {b[6]!r}')
print('QA problems:', len(problems))
for p in problems:
    print('  ', p)

svg = '\n'.join(out)
with open(os.path.join(HERE, 'rocket_side_view.svg'), 'w', encoding='utf-8') as fh:
    fh.write(svg)
if '--qa-narrow' in sys.argv:
    q = svg.replace('.nar{display:none}', '.nar{display:inline}.wide{display:none}')
    with open(os.path.join(WORK, 'qa_narrow.svg'), 'w', encoding='utf-8') as fh:
        fh.write(q)

# ------------------------------------------------------------------ layout ledger (JSON)
T = dict(CAD='real CAD v3.5.1', CON='concept / ESTIMATE', ASS="ASSUMED GNC reference airframe RV-1c (not Lauty's design)",
         DER='DERIVED for this drawing from the cited values')
layout = dict(
    id='ARGOS-H1 rocket side view layout', version='1.0', date='2026-10-15',
    status='CONCEPT LAYOUT for visualisation. Not a fabrication drawing, not an ICD, not physical approval.',
    units='SI: m, kg; station z from the airframe aft datum (base plane), +z toward the nose; r lateral',
    files=dict(svg='rocket_side_view.svg', png='rocket_side_view.png', generator='make_side_view.py',
               engine_projection='work/engine_projection.json (engine_projection.py)'),
    frames=dict(vehicle='z [m] from the aft datum, +z to the nose (gnc.json conventions.stations)',
                engine='engine CAD frame mm, +Z toward the injector, origin = gimbal pivot; z_vehicle = 0.203 + Z_engine/1000',
                glb='GLB m, +Y up = engine +Z; engine (x,y,z) = 1000 (X_glb, -Z_glb, Y_glb), checked against the manifest bounds '
                    f'(max error {PRJ["frames"]["axis_mapping_max_bound_error_mm"]} mm)',
                drawing=f'X = {XL} + (z + 0.25) x {S}, Y = {Y0} - r x {S} (SVG units, 1 unit = 2.5 mm); nose to the right',
                view=f'orthographic; drawing up = engine azimuth {PRJ["frames"]["az_up_deg"]} deg (ENG-BL-06 vent side), '
                     f'viewed from azimuth {PRJ["frames"]["viewed_from_az_deg"]} deg (true view, not mirrored)'),
    sources={k: dict(path=v, sha256_16=HASH[k]) for k, v in SRC.items()},
    engine=dict(status=T['CAD'],
                outline='true orthographic projection of every GLB triangle onto the side plane (0.1 mm raster, union traced '
                        'by marching squares, RDP 0.12 mm); display geometry, not a fabrication or tolerance source',
                outline_check='outline within the per-vertex radial envelope to the 0.1 mm raster (4 band-edge points at 0.05 mm)',
                pivot_z_m=PIVOT, nozzle_exit_z_m=round(Z_EXIT, 4), engine_top_z_m=round(Z_ENG_TOP, 4),
                length_mm=round(FEAT['engine_top_station_mm'] - FEAT['nozzle_exit_station_mm'], 1),
                axial_extent_about_pivot_mm=PRJ['envelope']['axial_extent_engine_frame_mm'],
                bbox_x_mm=PRJ['envelope']['bbox_x_mm'], bbox_y_mm=PRJ['envelope']['bbox_y_mm'],
                r_max_all_azimuths_mm=PRJ['envelope']['r_max_all_az_mm'],
                thrust_rings=dict(GM09_z_mm=FEAT['GM09_upper_thrust_ring_station_mm'], GM10_z_mm=FEAT['GM10_lower_ring_station_mm'],
                                  outer_r_mm=FEAT['thrust_ring_outer_r_mm'], role='airframe interface (thrust path)'),
                bleed_vent_stub_ENG_BL_06=dict(z_mm=FEAT['BL06_vent_stub']['station_mm'], r_max_mm=FEAT['BL06_vent_stub']['r_max_mm'],
                                               az_deg=FEAT['BL06_vent_stub']['az_of_r_max_deg'],
                                               airframe='wall hole TO-DEFINE; outside opposed vent tee ENG-BL-06N TO-DEFINE (ICD-14)'),
                tank_line_flange_ENG_FD_12F=dict(z_mm=fd['station_mm'], note='tank line route TO-DEFINE (ICD-5); drawn dashed'),
                gimbal_stop_sweep=dict(stop_deg=8.0,
                                       aft_end_r_max_mm=PRJ['gimbal_stop_sweep']['cases']['below_GM10_aft_face_z_lt_-99.8mm']['r_max_mm'],
                                       bay_inner_r_mm=round(1000 * R_I, 1), drawn='in-plane +/-8 deg outlines aft of the GM-10 face'),
                mass_wet_kg=M_ENG, cg_wet_z_m=round(Z_ENG_CG, 4), grain_mass_wet_kg=MP['grain_mass_wet_kg'],
                hardware_carried_kg=MP['hardware_carried']['carried_kg']),
    tank=dict(status=T['CON'], material='6061 tube', od_m=TANK['od'], wall_m=TANK['wall'], z_m=[TANK['z0'], TANK['z1']],
              overall_length_m=round(TANK['z1'] - TANK['z0'], 3), overall_length_tag='ESTIMATE (plan ~0.50 m)',
              internal_cylinder_length_m=round(TANK['L_int'], 4),
              closures='two flat bolted bulkheads, thickness NOT designed (drawn dashed)',
              placement=f'moved up from GNC v3d {V3D_TANK[0]:.3f}-{V3D_TANK[1]:.4f} m: the v3.5.1 engine top is at {Z_ENG_TOP:.4f} m',
              gap_to_engine_top_mm=round(1000 * (TANK['z0'] - Z_ENG_TOP), 1)),
    airframe=dict(status=T['ASS'],
                  body=dict(od_m=VEH['d_body_m'], id_m=VEH['d_id_m'], wall='2 x 3 mm PETG ASSUMED', z_m=[0.0, Z_BODY_TOP]),
                  nose=dict(shape='tangent ogive', length_m=L_NOSE, base_z_m=Z_BODY_TOP, tip_z_m=Z_TIP, ogive_radius_m=round(rho, 5),
                            wall_and_shoulder='MISSING'),
                  overall_length_m=round(Z_TIP - Z_EXIT, 4),
                  fins=dict(n=FIN['n'], span_m=FIN['span'], root_chord_m=FIN['cr'], tip_chord_m=FIN['ct'], le_sweep_m=FIN['sweep'],
                            root_le_z_m=FIN['z_le'], root_te_z_m=0.0, tip_le_z_m=round(FIN['z_le'] - FIN['sweep'], 3),
                            thickness_m=FIN['t'], material='GF/PETG',
                            source='gnc.json reference_vehicle.fins + vehicle.py reference_geometry_v2 fin planform'),
                  legs=dict(n=LEG['n'], foot_radius_m=LEG['r_foot'], foot_plane_z_m=LEG['z_foot'], leg_length_m=LEG['L'],
                            leg_diameter_m=LEG['d'], stroke_m=LEG['stroke'], state='deployed (landing)',
                            hinge=dict(z_m=round(Z_HINGE, 4), r_m=R_O, tag=T['DER'] + ': z_foot + sqrt(L^2 - (r_foot - r_body)^2); '
                                       'GNC gives no hinge station; check: leg midpoint z -0.048 vs GNC z_leg_aero -0.05'),
                            foot_pad='MISSING (not designed)', source='gnc.json icd_inputs_for_airframe.leg_design_values + vehicle.py'),
                  clocking='fins and legs both drawn rotated into the drawing plane; their relative clocking is TO-DEFINE (Lauty)',
                  plume_keep_out_cone=dict(theta_deg=KO['theta_deg'], r_e_m=KO['r_e_m'], x_max_m=KO['x_max_m'],
                                           end_z_m=round(z_ko, 4), end_r_m=round(r_ko, 4),
                                           tag='DERIVED GNC, not validated (icd_inputs_for_airframe.plume_line_clearance_rule)')),
    bays=[dict(ledger_id=b[0], name=b[2], z_v3d_m=b[3], z_m=b[4], shift_m=round(b[4] - b[3], 3), length_m='MISSING',
               drawn='ledger point marker only', status=T['ASS']) for b in BAYS],
    bay_shift_rule=f'items forward of the tank move with the tank top: DZ = 1.080 - {V3D_TANK[1]:.4f} = '
                   f'{TANK["z1"] - V3D_TANK[1]:.4f} m, used as {DZ} m; the drogue stays at the nose bay station 1.70 m',
    space_tank_top_to_nose_joint_m=round(Z_BODY_TOP - TANK['z1'], 3),
    masses=dict(
        rows=[dict(item='engine v3.5.1 wet incl. grain', kg=M_ENG, tag='CAD massprops v3.5.1 states.wet.all'),
              dict(item='N2O tank (P11)', kg=M_TANK, tag=LED['P11']['tag']),
              dict(item='engine ECU + battery share + tank sensors (P12)', kg=M_ECU, tag=LED['P12']['tag']),
              dict(item='N2O load', kg=M_N2O, tag='REQ lead decision 2026-10-12 (gnc.json reference_vehicle.n2o_load_kg)'),
              dict(item='propulsion subtotal', kg=round(M_PROP, 4), tag='sum'),
              dict(item='airframe group A01-A10 (11 ledger items)', kg=round(M_AIR, 4), tag='ledger v3d ASSUMED'),
              dict(item='liftoff', kg=round(M_LIFTOFF, 4), tag='ESTIMATE (row sum)'),
              dict(item='landing', kg=round(M_LAND, 4),
                   tag=f'ESTIMATE: v3d SIM landing {VEH["m_land_nominal_kg"]:.4f} + engine growth {GROWTH:.4f}; not re-simulated')],
        airframe_items=[dict(id=k, name=LED[k]['name'], kg=LED[k]['m'], z_v3d_m=LED[k]['z'], z_used_m=new_z.get(k, LED[k]['z']),
                             tag=LED[k]['tag']) for k in AIRFRAME_IDS],
        engine_growth_vs_v3d=dict(kg=round(GROWTH, 4), replaced_items=ENGINE_REPLACES, replaced_grain_kg=GRAIN_V3D,
                                  replaced_kg=round(m_replaced, 4),
                                  note=f'lead quotes +1.37 kg (liftoff ~17.4, landing ~16.1 kg); the row sum gives +{GROWTH:.2f} kg. '
                                       'The 0.02 kg difference matches the grain basis (massprops wet grain 0.424 kg vs v3d 0.404 kg); '
                                       'within rounding'),
        v3d_reference=dict(liftoff_kg=VEH['m_liftoff_kg'], landing_kg=VEH['m_land_nominal_kg'], tag='SIM nominal A1 (vehicle_v3d.json)'),
        context=dict(max_thrust_N=500, first_flight_target_apogee_m=210,
                     tag='SIM / lead decision (interfaces/CHANGELOG.md line 214: 210 m A1 value; gnc.json throttle_frac F/500 N)'),
    ),
    cg_estimate=dict(z_m=round(CG, 4), z_liquid_settled_aft_m=round(CG_SETTLED, 4), tag='ESTIMATE (not a GNC run)',
                     method='sum(m z) / sum(m) over the items below; N2O lumped at the tank centre. Variant: the 1.877 kg liftoff '
                            f'liquid settled aft in the centred internal cylinder (rho {RHO_LIQ:.0f} kg/m3, approx.), vapour at the centre',
                     gnc_verified_band_m=CG_BAND, gnc_v3d_liftoff_cg_m=VEH['cg']['liftoff_m'],
                     items=[dict(id=i['id'], name=i['name'], kg=i['m'], z_m=round(i['z'], 4)) for i in cg_items]),
    findings=[
        dict(id='F1', text=f'GNC v3d tank {V3D_TANK[0]:.3f}-{V3D_TANK[1]:.4f} m overlaps the v3.5.1 engine top {Z_ENG_TOP:.4f} m by '
                           f'{1000 * (Z_ENG_TOP - V3D_TANK[0]):.1f} mm (internal cylinder only; closures add to it). Tank moved to '
                           f'{TANK["z0"]}-{TANK["z1"]} m: gap {1000 * (TANK["z0"] - Z_ENG_TOP):.1f} mm; tank line route TO-DEFINE (ICD-5)'),
        dict(id='F2', text=f'battery, avionics and backup chute shifted +{DZ} m with the tank top; as ledger points they fit in the '
                           f'1.70 m tube ({Z_BODY_TOP - TANK["z1"]:.2f} m between the tank top and the nose joint); bay lengths MISSING'),
        dict(id='F3', text='ENG-BL-06 vent stub reaches r 74.2 mm > body outer r 73 mm at z 0.458-0.468 m (az ~108-112 deg): '
                           'wall hole and outside opposed tee TO-DEFINE (airframe, ICD-14)'),
        dict(id='F4', text=f'ECU (P12) ledger station z {LED["P12"]["z"]} m lies inside the v3.5.1 engine envelope (top {Z_ENG_TOP:.3f} m): '
                           'ECU station TO-DEFINE; kept at the ledger value in the CG estimate'),
        dict(id='F5', text=f'liftoff CG estimate {CG:.3f} m ({CG_SETTLED:.3f} m with the liquid settled aft) lies inside the GNC verified '
                           f'band {CG_BAND} m; ESTIMATE only, a GNC re-run on this layout is the check'),
        dict(id='F6', text='thrust rings GM-09/GM-10 outer r 69.75 mm vs bay inner r 70.0 mm: 0.25 mm radial clearance on the '
                           'ASSUMED 140 mm bay ID; fit and tolerance are airframe ICD items'),
        dict(id='F7', text='fins and legs are drawn rotated into the drawing plane (true span and foot radius); the fin/leg clocking '
                           'is TO-DEFINE'),
    ],
    missing=['bay lengths and volumes (battery, avionics, backup chute, drogue)', 'tank closure thickness and design',
             'tank line route (ICD-5)', 'wall hole size and outside vent tee (ICD-14)', 'ECU station',
             'leg hinge station, leg and foot design (Lauty)', 'fin and leg clocking (Lauty)', 'nose wall and shoulder',
             'airframe bulkhead stations (ledger A03b lumped at 1.05 m)'],
    qa=dict(text_overlap_problems=len(problems), method='Inter metrics, wide and phone (<= 640 px) states'),
)
with open(os.path.join(HERE, 'rocket_layout.json'), 'w', encoding='utf-8') as fh:
    json.dump(layout, fh, indent=1, ensure_ascii=False)
print(f'svg {len(svg) / 1024:.1f} KiB; CG {CG:.4f} (settled {CG_SETTLED:.4f}); liftoff {M_LIFTOFF:.4f}; prop {M_PROP:.4f}; '
      f'air {M_AIR:.4f}; land {M_LAND:.4f}; growth {GROWTH:.4f}; hinge {Z_HINGE:.4f}; DZ {DZ}; ko end z {z_ko:.4f} r {r_ko:.4f}')
