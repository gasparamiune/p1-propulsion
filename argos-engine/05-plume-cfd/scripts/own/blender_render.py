"""ARTISTIC Blender Cycles render of the ARGOS H1 plume (Combustion / 05-plume-cfd v2).

Runs inside Blender (tested with Blender 4.0.2, headless):
  blender -b --factory-startup -P blender_render.py -- INDIR OUT.png [samples] [resx] [resy] [K_E] [K_D] [view]
                                                        [exposure] [emis] [q_min] [x_fade]
INDIR holds dens.png, temp.png and fields.json from blender_prep.py. The axisymmetric CFD fields are revolved in the
shader: r = sqrt(y^2 + z^2) from object coordinates (1 Blender unit = 1 De), u = x / xmax, v = r / rmax.
Volume: Principled Volume with scattering density K_D q and blackbody emission (temperature from the CFD T + fast-
chemistry afterburning increment) of strength
  emis 't4'   : K_E q (T / 2400 K)^4                      (test renders 2026-10-12: far plume too uniform)
  emis 'wien' : K_E q exp(c2/lambda (1/2400 K - 1/T)), c2/lambda = 14388 um K / 0.6 um  (default: Wien-weighted
                visible emission of a grey soot proxy, so the luminous plume follows the hot core and afterburning)
q = soot-proxy density (Z rho), ASSUMED.
ARTISTIC: exposure, colour transform, K_E, K_D, the emission weighting and the camera are chosen for appearance; nothing
in this image is a measurement or a validated radiation result. The traceable image is synth_photo.py (qualitative).
"""
import bpy, json, math, os, sys

argv = sys.argv[sys.argv.index('--') + 1:]
indir, out_png = argv[0], argv[1]
samples = int(argv[2]) if len(argv) > 2 else 64
resx = int(argv[3]) if len(argv) > 3 else 1600
resy = int(argv[4]) if len(argv) > 4 else 560
K_E = float(argv[5]) if len(argv) > 5 else 4.0
K_D = float(argv[6]) if len(argv) > 6 else 0.3
view = argv[7] if len(argv) > 7 else 'threequarter'
exposure = float(argv[8]) if len(argv) > 8 else 0.0
emis = argv[9] if len(argv) > 9 else 'wien'
QMIN = float(argv[10]) if len(argv) > 10 else 0.002          # q threshold (fraction of q_max), cosmetic
XFADE = float(argv[11]) if len(argv) > 11 else 5.0           # fade length before x = xmax [De], cosmetic
info = json.load(open(os.path.join(indir, 'fields.json')))
xmax, rmax = info['xmax_De'], info['rmax_De']

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = samples
sc.cycles.use_adaptive_sampling = True
sc.cycles.volume_step_rate = 1.0
sc.cycles.volume_max_steps = 1024
sc.cycles.sample_clamp_indirect = 2.0                       # suppress volume fireflies (test renders 2026-10-12)
try:
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception:
    sc.cycles.use_denoising = False
print('DENOISE', sc.cycles.use_denoising, getattr(sc.cycles, 'denoiser', None))
sc.render.threads_mode = 'FIXED'; sc.render.threads = 2
sc.render.resolution_x = resx; sc.render.resolution_y = resy; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '8'
for vt in ('AgX', 'Filmic', 'Standard'):
    try:
        sc.view_settings.view_transform = vt
        break
    except Exception:
        continue
sc.view_settings.exposure = exposure

world = bpy.data.worlds.new('world'); sc.world = world; world.use_nodes = True
bg = world.node_tree.nodes.get('Background')
bg.inputs[0].default_value = (0.004, 0.005, 0.009, 1.0); bg.inputs[1].default_value = 1.0

# ---------------- plume volume domain ----------------
bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=rmax, depth=xmax, location=(xmax / 2, 0, 0),
                                    rotation=(0, math.pi / 2, 0))
dom = bpy.context.active_object; dom.name = 'plume_domain'
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
mat = bpy.data.materials.new('plume'); mat.use_nodes = True
nt = mat.node_tree; N = nt.nodes; L = nt.links
for n in list(N):
    N.remove(n)
out = N.new('ShaderNodeOutputMaterial')
tc = N.new('ShaderNodeTexCoord')
sep = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sep.inputs[0])


def m(op, a=None, b=None, va=None, vb=None):
    node = N.new('ShaderNodeMath'); node.operation = op
    if a is not None:
        L.new(a, node.inputs[0])
    elif va is not None:
        node.inputs[0].default_value = va
    if b is not None:
        L.new(b, node.inputs[1])
    elif vb is not None:
        node.inputs[1].default_value = vb
    return node.outputs[0]


r = m('SQRT', m('ADD', m('MULTIPLY', sep.outputs['Y'], sep.outputs['Y']), m('MULTIPLY', sep.outputs['Z'], sep.outputs['Z'])))
comb = N.new('ShaderNodeCombineXYZ')
L.new(m('DIVIDE', sep.outputs['X'], vb=xmax), comb.inputs[0]); L.new(m('DIVIDE', r, vb=rmax), comb.inputs[1])


def tex(fn):
    im = bpy.data.images.load(os.path.join(indir, fn)); im.colorspace_settings.name = 'Non-Color'
    t = N.new('ShaderNodeTexImage'); t.image = im; t.interpolation = 'Linear'; t.extension = 'EXTEND'
    L.new(comb.outputs[0], t.inputs['Vector'])
    return t.outputs['Color']


ds = tex('dens.png'); ts = tex('temp.png')
q0 = m('MULTIPLY', ds, ds)                                  # decode sqrt encoding
# cosmetic: drop the faint outer halo (speckle at low sample counts) and fade the cut at the domain end x = xmax
q_thr = m('MAXIMUM', m('SUBTRACT', q0, vb=QMIN), vb=0.0)
fade = m('MINIMUM', m('MAXIMUM', m('DIVIDE', m('SUBTRACT', None, sep.outputs['X'], va=xmax), vb=XFADE), vb=0.0), vb=1.0)
q = m('MULTIPLY', q_thr, fade)
T = m('MULTIPLY', ts, vb=info['T_scale_K'])
bb = N.new('ShaderNodeBlackbody'); L.new(T, bb.inputs['Temperature'])
if emis == 't4':
    wT = m('POWER', m('DIVIDE', T, vb=2400.0), vb=4.0)
else:                                                       # Wien weighting at 0.6 um, normalised at 2400 K
    C2L = 14388.0 / 0.6
    Tc = m('MAXIMUM', T, vb=300.0)
    invT = m('DIVIDE', None, Tc, va=1.0)                    # 1 / T
    wT = m('EXPONENT', m('ADD', m('MULTIPLY', invT, vb=-C2L), vb=C2L / 2400.0))
es = m('MULTIPLY', m('MULTIPLY', q, wT), vb=K_E)
pv = N.new('ShaderNodeVolumePrincipled')
L.new(m('MULTIPLY', q, vb=K_D), pv.inputs['Density'])
L.new(bb.outputs['Color'], pv.inputs['Emission Color'])
L.new(es, pv.inputs['Emission Strength'])
pv.inputs['Color'].default_value = (0.30, 0.27, 0.24, 1.0)
pv.inputs['Absorption Color'].default_value = (0.02, 0.02, 0.02, 1.0)
L.new(pv.outputs[0], out.inputs['Volume'])
dom.data.materials.append(mat)

# ---------------- nozzle + illustrative body (lathe about the x axis) ----------------
inner = info['nozzle_inner_De']                              # (x from exit, r), x <= 0
rb, rc = info['body_outer_radius_De'], info['case_outer_radius_De']
x0 = min(p[0] for p in inner)
prof = [(x, rr) for x, rr in inner]
prof += [(0.0, rb), (-2.0, rb), (-2.3, rc), (-9.0, rc), (-9.0, inner[0][1]), (x0, inner[0][1])]
M = 96
verts, faces = [], []
for (x, rr) in prof:
    for k in range(M):
        ph = 2 * math.pi * k / M
        verts.append((x, rr * math.cos(ph), rr * math.sin(ph)))
n = len(prof)
for i in range(n):
    j = (i + 1) % n
    for k in range(M):
        k2 = (k + 1) % M
        faces.append((i * M + k, i * M + k2, j * M + k2, j * M + k))
me = bpy.data.meshes.new('engine'); me.from_pydata(verts, [], faces); me.update()
eng = bpy.data.objects.new('engine', me); sc.collection.objects.link(eng)
for p in me.polygons:
    p.use_smooth = True
mb = bpy.data.materials.new('metal'); mb.use_nodes = True
bs = mb.node_tree.nodes.get('Principled BSDF')
bs.inputs['Base Color'].default_value = (0.18, 0.18, 0.19, 1.0)
bs.inputs['Metallic'].default_value = 0.7; bs.inputs['Roughness'].default_value = 0.4
eng.data.materials.append(mb)

# ---------------- lights and camera ----------------
# key + fill area lights aimed at the engine (test renders 2026-10-12: the hardware was invisible at 60 W)
for loc, en in (((-10.0, -12.0, 10.0), 400.0), ((-6.0, 12.0, 4.0), 120.0)):
    bpy.ops.object.light_add(type='AREA', location=loc)
    lt = bpy.context.active_object; lt.data.energy = en; lt.data.size = 8.0
    tr = lt.constraints.new(type='TRACK_TO'); tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
    aim = bpy.data.objects.new('aim', None); sc.collection.objects.link(aim); aim.location = (-3.0, 0.0, 0.0); tr.target = aim
tgt = bpy.data.objects.new('target', None); sc.collection.objects.link(tgt)
if view == 'side':
    tgt.location = (12.0, 0.0, 0.0); cam_loc = (12.0, -52.0, 0.0); lens = 50.0       # x ~ -6.7 .. 30.7 De in frame
else:
    tgt.location = (11.0, 0.0, 0.0); cam_loc = (-1.0, -40.0, 11.0); lens = 40.0
bpy.ops.object.camera_add(location=cam_loc)
cam = bpy.context.active_object; cam.data.lens = lens; sc.camera = cam
c = cam.constraints.new(type='TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'

sc.render.filepath = out_png
bpy.ops.render.render(write_still=True)
print('RENDERED', out_png, 'samples', samples, 'K_E', K_E, 'K_D', K_D, 'view', view, 'exposure', exposure, 'emis', emis, 'transform', sc.view_settings.view_transform)
