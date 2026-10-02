"""familias.py — Familia de perfil PrusaSlicer por pieza impresa y ajustes por objeto.

Lo usan tabla_fabricacion.py (tablas de 05_fabricacion.md), build_probetas.py (perfil de P1.6/P1.7 = el de
P1-INT-04) y prusaslicer/validar_perfiles.py (laminado). Toda pieza impresa no listada cae en «estructural»
(el perfil más exigente; hoy: soporte del kill switch P1-CTL-03, seguridad) [SUPUESTO: conservador].
Los perfiles están en prusaslicer/P1_impresion_<familia>_*.ini.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PS = ROOT / "prusaslicer"

PERFILES = {
    "estructural": "P1_impresion_estructural_0.20.ini",
    "sellado": "P1_impresion_sellado_0.15.ini",
    "cubiertas": "P1_impresion_cubiertas_0.20.ini",
}
IMPRESORA = "P1_impresora_Ender3S1.ini"
FILAMENTO = "P1_filamento_PETG.ini"

# Excepciones a «estructural», justificadas por la función de la pieza (ver 05_fabricacion.md §2)
FAMILIA = {
    "P1-INT-04": ("sellado", "mojada y a presión: O-ring de cara y purga; sección llena, sin canales entre cordones "
                             "(research/R05 B4) — P1.6/P1.7"),
    "P1-ELE-01": ("cubiertas", "seca, sobre el piso; FS ≥ 16 (estructural.json); insertos M5 en nervios macizos — P1.4"),
    "P1-ELE-02": ("cubiertas", "capota antisalpicaduras, seca; FS ≥ 6 (estructural.json)"),
    "P1-CTL-02": ("cubiertas", "tapa de la unidad de palancas: sin cargas de mando (van a P1-CTL-08); 5 perímetros, "
                               "30 % (orientación del manifest)"),
}
INFILL_BASE = {"estructural": 85, "sellado": 100, "cubiertas": 30}   # = los .ini


def familia(rec) -> tuple[str, str]:
    pid = rec["id"]
    if pid in FAMILIA:
        return FAMILIA[pid]
    return "estructural", "en la ruta de carga de un elemento de seguridad (tirón del cordón, golpe a la seta); FS en structural.py"


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
