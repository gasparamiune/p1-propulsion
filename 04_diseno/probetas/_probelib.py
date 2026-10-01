"""_probelib.py — utilidades comunes de las probetas P1.x (04_diseno/probetas/PRB-*.py).

Las probetas NO copian cotas a mano: leen params.load(), los módulos de 04_diseno/piezas/
(geometría real, recortes de la pieza) y resultados/estructural.json (cargas). Este módulo
da el contexto (Ctx), rótulos en relieve, escaneo geométrico de sólidos y lectura de cargas.
"""
from __future__ import annotations

import json
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent          # 04_diseno/probetas
D4 = HERE.parent                                 # 04_diseno
ROOT = D4.parent
for _p in (str(D4), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from build123d import (Align, FontStyle, GeomType, Part, Plane, Pos, Rot, Text,  # noqa: E402
                       Vector, extrude)

import params as P  # noqa: E402

CEN = Align.CENTER
FONT = "DejaVu Sans"           # [SUPUESTO: fuente libre del sistema; si falta, OCCT usa la suya]
LABEL_DEPTH = 0.6              # relieve = 3 capas de 0,2 mm [SUPUESTO]


@dataclass
class Ctx:
    """Contexto compartido: parámetros, módulos de piezas, resultados."""
    p: object
    parts: dict = field(default_factory=dict)    # id → módulo de pieza
    est: dict = field(default_factory=dict)      # resultados/estructural.json
    man: dict = field(default_factory=dict)      # resultados/manifest.json (si existe)
    notes: list = field(default_factory=list)    # avisos (fallbacks usados)

    @property
    def inp(self):
        return self.p.inp

    def part(self, pid):
        return self.parts[pid]

    def built(self, pid, _cache={}):
        key = (id(self), pid)
        if key not in _cache:
            _cache[key] = self.parts[pid].build(self.p)
        return _cache[key]


def load_ctx() -> Ctx:
    import build_all                                   # 04_diseno/build_all.py (load_parts)
    p = P.load()
    mods = {m.META["id"]: m for m in build_all.load_parts()}
    est = _json(ROOT / "resultados" / "estructural.json")
    man = _json(ROOT / "resultados" / "manifest.json")
    return Ctx(p=p, parts=mods, est=est, man=man)


def _json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# ---------------------------------------------------------------------------
# Rótulos en relieve
# ---------------------------------------------------------------------------
def label(text, x, y, z, size=5.0, depth=LABEL_DEPTH, rot=0.0) -> Part:
    """Texto en relieve sobre una cara superior plana a la altura z (lectura desde +Z)."""
    t = Text(text, font_size=size, font=FONT, font_style=FontStyle.BOLD, align=(CEN, CEN))
    s = extrude(t, amount=depth + 0.05)
    return Pos(x, y, z - 0.05) * Rot(0, 0, rot) * s


def label_on_plane(text, plane: Plane, size=5.0, depth=LABEL_DEPTH) -> Part:
    """Texto en relieve sobre una cara plana cualquiera (plane.z_dir = normal saliente)."""
    t = Text(text, font_size=size, font=FONT, font_style=FontStyle.BOLD, align=(CEN, CEN))
    pl = plane.offset(-0.05)
    return extrude(pl * t, amount=depth + 0.05)


def fmt_mm(v, nd=2):
    """'+.15' / '-.05' (rótulo corto de holgura en mm)."""
    s = f"{v:+.{nd}f}"
    return s.replace("0.", ".", 1)


# ---------------------------------------------------------------------------
# Geometría: escaneo y caras cilíndricas
# ---------------------------------------------------------------------------
def inside(part, x, y, z, tol=1e-3) -> bool:
    return bool(part.is_inside(Vector(x, y, z), tol))


def scan(part, start, direction, length, step=0.1):
    """Recorre un rayo y devuelve las transiciones [(s, dentro_después)], s en mm desde start."""
    sx, sy, sz = start
    d = Vector(*direction).normalized()
    out = []
    prev = inside(part, sx, sy, sz)
    n = int(round(length / step))
    for i in range(1, n + 1):
        s = i * step
        cur = inside(part, sx + d.X * s, sy + d.Y * s, sz + d.Z * s)
        if cur != prev:
            # refinar por bisección
            a, b = s - step, s
            for _ in range(12):
                m = 0.5 * (a + b)
                if inside(part, sx + d.X * m, sy + d.Y * m, sz + d.Z * m) == prev:
                    a = m
                else:
                    b = m
            out.append((round(0.5 * (a + b), 3), cur))
            prev = cur
    return out


def cyl_faces(part):
    """Caras cilíndricas: [{r, d (eje unitario), loc, hole}] (hole = superficie cóncava = agujero)."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    res = []
    for f in part.faces():
        if f.geom_type != GeomType.CYLINDER:
            continue
        s = BRepAdaptor_Surface(f.wrapped)
        c = s.Cylinder()
        ax = c.Axis()
        d = Vector(ax.Direction().X(), ax.Direction().Y(), ax.Direction().Z())
        loc = Vector(ax.Location().X(), ax.Location().Y(), ax.Location().Z())
        try:
            pt = f.position_at(0.5, 0.5)
            n = f.normal_at(pt)
            rel = pt - loc
            radial = rel - d * rel.dot(d)
            hole = n.dot(radial) < 0
        except Exception:                                  # pragma: no cover
            hole = None
        res.append({"r": c.Radius(), "d": d, "loc": loc, "hole": hole})
    return res


# ---------------------------------------------------------------------------
# Cargas desde resultados/estructural.json
# ---------------------------------------------------------------------------
def est_row(ctx: Ctx, part_prefix: str, lc_substr: str):
    for r in ctx.est.get("rows", []):
        if r["part"].startswith(part_prefix) and lc_substr.lower() in r["load_case"].lower():
            return r
    return None


def rx_float(pattern, text, default=None):
    m = re.search(pattern, text or "")
    if not m:
        return default
    return float(m.group(1).replace(",", "."))


def fs_target(ctx: Ctx) -> float:
    return float(ctx.inp["materials"]["fs_target_printed"])


def petg(ctx: Ctx):
    return ctx.inp["materials"]["PETG"], ctx.inp["materials"]["design_factors"]


def r3(v):
    return None if v is None else round(float(v), 3)


def deg(a):
    return math.degrees(a)
