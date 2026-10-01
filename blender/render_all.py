#!/usr/bin/env python3
"""render_all.py — Renders de P1 con Blender como módulo Python (bpy), solo visual.

Construye la escena desde los mismos módulos de piezas y ubicaciones del CAD:
  • un objeto por pieza/instancia, nombrado P1-<SUB>-<NN>_<nombre>[#k]
  • una colección por subsistema (P1-MNT, P1-HSG, P1-DRV, P1-PRP, P1-STR, P1-ELE, P1-SAF)
  • materiales: PETG (color por subsistema), inox, aluminio, POM; espejo y agua de referencia
Salidas (blender/renders/): render_lateral.png, render_planta.png, render_frontal.png
(ortográficas), render_perspectiva.png, render_explosionada.png, render_basculada.png,
anim_montaje_####.png (animación de montaje) y blender/P1_ensamblaje.blend.
Uso: python blender/render_all.py [--samples 24] [--res 1280 720] [--anim-frames 24]
Requiere: pip install -r requirements-render.txt (bpy). Blender 5.1 de escritorio puede abrir el .blend.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "04_diseno"))
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent / "renders"

import bpy  # noqa: E402
import trimesh  # noqa: E402

SUB_COLOR = {"MNT": (0.23, 0.43, 0.66), "HSG": (0.88, 0.54, 0.12), "DRV": (0.55, 0.55, 0.58),
             "PRP": (0.75, 0.22, 0.17), "STR": (0.56, 0.27, 0.68), "ELE": (0.15, 0.68, 0.38),
             "SAF": (0.95, 0.77, 0.06)}
METAL = {"AISI 316": (0.80, 0.80, 0.82), "AISI 440C": (0.75, 0.75, 0.78), "Al 6061-T6": (0.85, 0.86, 0.88),
         "Al": (0.85, 0.86, 0.88), "Al 5052/6082": (0.85, 0.86, 0.88)}


def mat(name, color, metallic=0.0, rough=0.5, alpha=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    b.inputs["Alpha"].default_value = alpha
    return m


def add_mesh(name, tm, collection, material):
    me = bpy.data.meshes.new(name)
    me.from_pydata(tm.vertices.tolist(), [], tm.faces.tolist())
    me.update()
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    ob.data.materials.append(material)
    for poly in me.polygons:
        poly.use_smooth = False
    return ob


def build_scene(steer=0.0, tilt=0.0):
    import params as P
    from build_all import load_parts, loc_matrix
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    p = P.load()
    cols = {}
    objs = []
    for m in load_parts():
        meta = m.META
        sub = meta["id"].split("-")[1]
        cname = f"P1-{sub}"
        if cname not in cols:
            cols[cname] = bpy.data.collections.new(cname)
            sc.collection.children.link(cols[cname])
        if meta["material"] in METAL:
            mt = mat(meta["material"], METAL[meta["material"]], 1.0, 0.3)
        elif meta["material"] == "POM-C":
            mt = mat("POM-C", (0.95, 0.95, 0.92), 0.0, 0.4)
        else:
            mt = mat(f"PETG_{sub}", SUB_COLOR[sub], 0.0, 0.45)
        mesh = trimesh.load(ROOT / "04_diseno" / "stl" / "asm" / f"{meta['id']}.stl", force="mesh")
        mesh.apply_scale(0.001)                                   # mm → m
        for k, L in enumerate(m.placements(p, steer, tilt)):
            mm = mesh.copy()
            M = np.array(loc_matrix(L))
            M[:3, 3] *= 0.001
            mm.apply_transform(M)
            name = f"{meta['id']}_{meta['name']}" + (f"#{k}" if k else "")
            ob = add_mesh(name, mm, cols[cname], mt)
            ob["frame"] = meta["frame"]
            objs.append(ob)
    # referencia: espejo y agua
    ref = bpy.data.collections.new("Referencia")
    sc.collection.children.link(ref)
    t, H, W = p.tr_t / 1000, p.tr_H / 1000, p.inp["boat"]["transom"]["top_width_mm"] / 1000
    tr = trimesh.creation.box(extents=(t, W, H)); tr.apply_translation((-t / 2, 0, -H / 2))
    add_mesh("Espejo_referencia", tr, ref, mat("Aluminio_casco", (0.6, 0.62, 0.65), 0.8, 0.5))
    zwl = p.layout["z_wl_mm"] / 1000
    wp = trimesh.creation.box(extents=(3.0, 2.0, 0.002)); wp.apply_translation((0.5, 0, zwl))
    wat = mat("Agua", (0.2, 0.45, 0.7), 0.0, 0.1, 0.35)
    wat.blend_method = "BLEND" if hasattr(wat, "blend_method") else None
    add_mesh("Agua_flotacion", wp, ref, wat)
    # luces
    sun = bpy.data.lights.new("Sol", "SUN"); sun.energy = 3.0
    so = bpy.data.objects.new("Sol", sun); sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(50), math.radians(-20), math.radians(30))
    world = bpy.data.worlds.new("Mundo"); sc.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.92, 0.94, 0.97, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
    return p, objs


def camera(name, loc, rot, ortho=None, lens=35):
    cam = bpy.data.cameras.new(name)
    if ortho:
        cam.type = "ORTHO"; cam.ortho_scale = ortho
    else:
        cam.lens = lens
    ob = bpy.data.objects.new(name, cam)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot]
    return ob


def render(path, cam, samples, res):
    sc = bpy.context.scene
    sc.camera = cam
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=24)
    ap.add_argument("--res", type=int, nargs=2, default=[1280, 720])
    ap.add_argument("--anim-frames", type=int, default=16)
    a = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    res = tuple(a.res)
    p, objs = build_scene(0.0, 0.0)
    cx = 0.45
    cams = {
        "lateral": camera("Cam_lateral", (cx, -4.0, -0.1), (90, 0, 0), ortho=1.9),
        "planta": camera("Cam_planta", (cx, 0, 4.0), (0, 0, 0), ortho=1.9),
        "frontal": camera("Cam_frontal", (4.0, 0, -0.1), (90, 0, 90), ortho=1.2),
        "perspectiva": camera("Cam_persp", (2.2, -1.9, 0.9), (68, 0, 48), lens=30),
    }
    for k, c in cams.items():
        render(OUT / f"render_{k}.png", c, a.samples, res)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "blender" / "P1_ensamblaje.blend"))
    # explosionada: desplaza cada pieza de la unidad a lo largo de su dirección desde el pivote
    piv = np.array([p.pivot_x, 0, p.pivot_z]) / 1000
    base = {ob.name: ob.location.copy() for ob in objs}
    for ob in objs:
        c = np.mean(np.array([v.co for v in ob.data.vertices]), axis=0)
        d = c - piv
        n = np.linalg.norm(d)
        off = (d / n * 0.12) if n > 1e-6 else np.zeros(3)
        if ob["frame"] in ("unit", "yoke"):
            ob.location = tuple(np.array(base[ob.name]) + off)
    render(OUT / "render_explosionada.png", cams["perspectiva"], a.samples, res)
    # animación de montaje: de explosionada (frame 1) a montada (frame N)
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, max(2, a.anim_frames)
    for ob in objs:
        ob.keyframe_insert("location", frame=1)
        ob.location = base[ob.name]
        ob.keyframe_insert("location", frame=sc.frame_end)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "blender" / "P1_ensamblaje.blend"))
    for f in range(1, sc.frame_end + 1, max(1, sc.frame_end // 8)):
        sc.frame_set(f)
        render(OUT / f"anim_montaje_{f:04d}.png", cams["perspectiva"], max(8, a.samples // 3), (640, 360))
    # basculada
    p, objs = build_scene(0.0, p.tilt_range)
    cam = camera("Cam_lateral", (cx, -4.0, -0.1), (90, 0, 0), ortho=1.9)
    render(OUT / "render_basculada.png", cam, a.samples, res)
    print("renders Blender OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] if "--" not in sys.argv else sys.argv[sys.argv.index("--") + 1:]))
