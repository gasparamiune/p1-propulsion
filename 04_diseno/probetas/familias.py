"""familias.py — Familia de perfil PrusaSlicer por pieza impresa y ajustes por objeto.

Lo usan tabla_fabricacion.py (tabla de 05_fabricacion.md) y prusaslicer/validar_perfiles.py (laminado
de prueba). Toda pieza impresa no listada cae en «estructural» (el perfil más exigente) [SUPUESTO:
conservador]. Los perfiles están en prusaslicer/P1_impresion_<familia>_*.ini.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PS = ROOT / "prusaslicer"

PERFILES = {
    "estructural": "P1_impresion_estructural_0.20.ini",
    "sellado": "P1_impresion_sellado_0.15.ini",
    "fusible": "P1_impresion_fusible_0.20.ini",
    "cubiertas": "P1_impresion_cubiertas_0.20.ini",
}
IMPRESORA = "P1_impresora_Ender3S1.ini"
FILAMENTO = "P1_filamento_PETG.ini"

# Excepciones a «estructural», justificadas por la función de la pieza (ver 05_fabricacion.md §3)
FAMILIA = {
    "P1-ELE-01": ("sellado", "caja estanca: O-ring de cara y prensaestopas (research/R05 B3–B4)"),
    "P1-PRP-02": ("fusible", "patín: la cintura debe romper a skeg_fuse_force (P1.8)"),
    "P1-PRP-01": ("fusible", "protector: consumible, paredes llenas (research/R05 A6/A8)"),
    "P1-HSG-03": ("cubiertas", "cubrecorrea: salpicaduras, sin carga, drena"),
    "P1-HSG-05": ("cubiertas", "capó: salpicaduras, sin carga, ventilado"),
}
INFILL_BASE = {"estructural": 85, "sellado": 100, "fusible": 100, "cubiertas": 25}   # = los .ini


def familia(rec) -> tuple[str, str]:
    pid = rec["id"]
    if pid in FAMILIA:
        return FAMILIA[pid]
    return "estructural", "en la ruta de carga o con FS calculado (structural.py)"


def relleno(rec, fam=None) -> int:
    """Relleno [%] por objeto: en «estructural», ≥ solid_frac del manifest (redondeado a 5 %)."""
    fam = fam or familia(rec)[0]
    base = INFILL_BASE[fam]
    if fam != "estructural":
        return base
    sf = float(rec.get("solid_frac", 1.0))
    return int(max(base, min(100, 5 * round(sf * 100 / 5))))


def overrides(rec, fam=None) -> dict:
    """Claves a sobrescribir por objeto (PrusaSlicer: «Agregar ajustes» del objeto, o CLI)."""
    fam = fam or familia(rec)[0]
    o = {}
    inf = relleno(rec, fam)
    if inf != INFILL_BASE[fam]:
        o["fill_density"] = f"{inf}%"
        if inf >= 100:
            o["fill_pattern"] = "rectilinear"            # gyroid no trabaja al 100 %
    b = brim(rec)
    if b:
        o["brim_width"] = str(b)
    return o


def brim(rec) -> int:
    """Borde [mm] si la pieza es alta respecto de su huella (alto/lado menor > 2) [SUPUESTO: regla práctica]."""
    bb = rec.get("print_bbox_mm")
    if not bb:
        return 0
    r = bb[2] / max(1e-6, min(bb[0], bb[1]))
    return 8 if r > 5 else (5 if r > 2 else 0)
