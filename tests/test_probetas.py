"""Probetas P1.x (04_diseno/probetas/) y perfiles PrusaSlicer (prusaslicer/).

- Construye las probetas con build_probetas.py si sus salidas faltan o están desactualizadas respecto de
  los módulos, params, cadlib, piezas, inputs.yaml o los JSON de resultados (o si P1_REBUILD_PROBETAS=1);
  si no, usa las salidas existentes.
- Verifica malla cerrada (trimesh), 1 cuerpo, apoyo en z = 0 y envolvente ≤ printer.envelope_mm de todas
  las probetas; que estén los 8 ensayos de PENDIENTES_GASPAR §P1 y que sus cotas lean el diseño.
- Verifica que los .ini existen, tienen formato clave = valor y las claves críticas: temperature ≤ 260,
  bed_temperature ≤ 100, perimeters ≥ 6 en estructural, etc. (límites leídos de inputs.yaml).
- Con PrusaSlicer en el PATH: carga y lamina un cubo con cada familia (si no, se saltea).
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import trimesh

ROOT = Path(__file__).resolve().parents[1]
PRB = ROOT / "04_diseno" / "probetas"
PS = ROOT / "prusaslicer"
MAN = PRB / "probetas_manifest.json"
TESTS = [f"P1.{i}" for i in range(1, 9)]
INIS = {"impresora": "P1_impresora_Ender3S1.ini", "filamento": "P1_filamento_PETG.ini",
        "estructural": "P1_impresion_estructural_0.20.ini", "sellado": "P1_impresion_sellado_0.15.ini",
        "fusible": "P1_impresion_fusible_0.20.ini", "cubiertas": "P1_impresion_cubiertas_0.20.ini"}


def _deps():
    d = list(PRB.glob("PRB-*.py")) + list((ROOT / "04_diseno" / "piezas").glob("*.py"))
    d += [PRB / "_probelib.py", PRB / "build_probetas.py", ROOT / "04_diseno" / "params.py",
          ROOT / "04_diseno" / "cadlib.py", ROOT / "inputs.yaml", ROOT / "resultados" / "sizing.json",
          ROOT / "resultados" / "estructural.json"]
    return [x for x in d if x.exists()]


def _stale():
    if not MAN.exists():
        return True
    t = MAN.stat().st_mtime
    data = json.loads(MAN.read_text(encoding="utf-8"))
    if any(not (ROOT / f).exists() for r in data.get("probetas", []) for f in r["files"]):
        return True
    return any(x.stat().st_mtime > t for x in _deps())


@pytest.fixture(scope="session")
def pm():
    if os.environ.get("P1_REBUILD_PROBETAS") == "1" or _stale():
        r = subprocess.run([sys.executable, str(PRB / "build_probetas.py")], cwd=ROOT, capture_output=True,
                           text=True, timeout=3600)
        assert r.returncode == 0, r.stdout[-4000:] + r.stderr[-4000:]
    return json.loads(MAN.read_text(encoding="utf-8"))


def parse_ini(path):
    keys = {}
    for i, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        s = raw.rstrip()
        if not s.strip() or s.lstrip().startswith(("#", ";")):
            continue
        m = re.match(r"^([a-z0-9_]+) = ?(.*)$", s)
        assert m, f"{Path(path).name}:{i} no es «clave = valor»: {s[:60]}"
        assert m.group(1) not in keys, f"{Path(path).name}:{i} clave duplicada {m.group(1)}"
        keys[m.group(1)] = m.group(2)
    return keys


@pytest.fixture(scope="session")
def ini():
    return {k: parse_ini(PS / f) for k, f in INIS.items()}


# ---------------------------------------------------------------------------
# Probetas
# ---------------------------------------------------------------------------
def test_todos_los_ensayos_presentes(pm):
    assert set(TESTS) <= set(pm["tests"]), set(TESTS) - set(pm["tests"])
    ids = {r["id"] for r in pm["probetas"]}
    for must in ("P1.1A", "P1.1H", "P1.2", "P1.3", "P1.4", "P1.5A", "P1.5B", "P1.6A", "P1.6B", "P1.7A", "P1.8"):
        assert must in ids, must
    assert not pm["fails"], pm["fails"]


def test_manifold_envolvente_y_apoyo(pm, inp):
    env = inp["printer"]["envelope_mm"]
    for r in pm["probetas"]:
        for f in r["files"]:
            assert (ROOT / f).exists(), f
        m = trimesh.load(ROOT / r["files"][1], force="mesh")
        assert m.is_watertight and m.is_winding_consistent and m.volume > 0, r["id"]
        assert len(m.split(only_watertight=False)) == 1, (r["id"], "más de un cuerpo")
        ext = m.bounds[1] - m.bounds[0]
        assert ext[0] <= env[0] + 1e-6 and ext[1] <= env[1] + 1e-6 and ext[2] <= env[2] + 1e-6, (r["id"], ext)
        assert abs(m.bounds[0][2]) < 1e-3, (r["id"], "no apoya en z = 0")
        assert r["profile"] in ("estructural", "sellado", "fusible", "cubiertas")


def test_cotas_de_cada_modulo_ok(pm):
    bad = [(t, c["name"]) for t, v in pm["tests"].items() for c in v["checks"] if not c["ok"]]
    assert not bad, bad
    for t in TESTS:
        assert pm["tests"][t]["criterios"], t


def test_probetas_leen_el_diseno(pm):
    import params as P
    p = P.load()
    T = pm["tests"]
    c8 = T["P1.8"]["criterios"]
    assert abs(c8["seccion_mm"][0] - round(p.skeg_neck_len, 2)) < 0.01 and c8["seccion_mm"][1] == p.skeg_t
    assert abs(c8["brazo_ref_mm"] - round(p.skeg_neck_lever, 1)) < 0.05
    assert c8["banda_N"] == [round(2 * p.skeg_fuse_force / 3), round(4 * p.skeg_fuse_force / 3)]
    c2 = T["P1.2"]["criterios"]
    assert c2["D_mm"] == p.brg_D and round(float(p.press), 3) in c2["asientos_presion_mm"]
    c3 = T["P1.3"]["criterios"]
    assert c3["h_mm"] == 18.0 and c3["umbral_N"] >= 3 * c3["F_perno_N"] - 1
    d, w = T["P1.6"]["criterios"]["ranura_mm"]
    assert 2.57 <= d <= 2.72 and 4.50 <= w <= 4.75                 # research/R05 B3 (Parker 4-3), cordón 3,53
    c1 = T["P1.1"]["criterios"]
    for dn in (p.tilt_pin_d, p.shaft_d, p.tube_od):
        assert float(dn) in c1["nominales_mm"]
    assert float(p.clr) in c1["holguras_mm"]


# ---------------------------------------------------------------------------
# Perfiles PrusaSlicer
# ---------------------------------------------------------------------------
def test_ini_existen_y_claves_criticas(ini, inp):
    pr = inp["printer"]
    fil, prn = ini["filamento"], ini["impresora"]
    for k in ("temperature", "first_layer_temperature"):
        assert k in fil and float(fil[k]) <= pr["hotend_max_c"], k
    for k in ("bed_temperature", "first_layer_bed_temperature"):
        assert k in fil and float(fil[k]) <= pr["bed_max_c"], k
    assert fil["filament_type"] == "PETG"
    assert float(prn["nozzle_diameter"]) == pr["nozzle_mm"]
    pts = [tuple(float(c) for c in q.split("x")) for q in prn["bed_shape"].split(",")]
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    assert max(xs) - min(xs) == pr["envelope_mm"][0] and max(ys) - min(ys) == pr["envelope_mm"][1]
    assert max(xs) <= 220 and max(ys) <= 220 and min(xs) >= 0 and min(ys) >= 0
    assert float(prn["max_print_height"]) == pr["envelope_mm"][2]
    if prn.get("use_relative_e_distances") == "1":
        assert "G92 E0" in prn["layer_gcode"]                     # PrusaSlicer lo exige con E relativo
    est = ini["estructural"]
    assert int(est["perimeters"]) >= 6
    assert int(est["top_solid_layers"]) >= 4 and int(est["bottom_solid_layers"]) >= 4
    assert est["fill_pattern"] == "gyroid" and float(est["fill_density"].rstrip("%")) >= 60
    assert float(est["layer_height"]) == 0.2 and est["seam_position"] in ("aligned", "rear")
    sel = ini["sellado"]
    assert 0.12 <= float(sel["layer_height"]) <= 0.15
    assert float(sel["fill_density"].rstrip("%")) >= 100 or int(sel["perimeters"]) >= 4
    fus = ini["fusible"]
    for k in ("perimeters", "fill_density", "fill_pattern", "fill_angle", "perimeter_generator"):
        assert k in fus, k
    cub = ini["cubiertas"]
    assert int(cub["perimeters"]) >= 2
    for name in ("estructural", "sellado", "fusible", "cubiertas"):                # caudal ≤ límite del filamento
        v = max(float(ini[name][k]) for k in ("perimeter_speed", "infill_speed", "solid_infill_speed"))
        assert v * float(ini[name]["infill_extrusion_width"]) * float(ini[name]["layer_height"]) \
            <= float(fil["filament_max_volumetric_speed"]), name


def test_familias_coinciden_con_ini(ini):
    sys.path.insert(0, str(PRB))
    import familias as FAM
    for fam, fn in FAM.PERFILES.items():
        assert (PS / fn).exists(), fn
        assert float(ini[fam]["fill_density"].rstrip("%")) == FAM.INFILL_BASE[fam], fam


def test_validador_formato_y_limites(tmp_path):
    rep = tmp_path / "rep.json"
    r = subprocess.run([sys.executable, str(PS / "validar_perfiles.py"), "--sin-laminar", "--sin-completo",
                        "--informe", str(rep)], cwd=ROOT, capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stdout + r.stderr
    data = json.loads(rep.read_text(encoding="utf-8"))
    assert data["formato_y_limites_ok"] and not data["errores"]


@pytest.mark.skipif(shutil.which("prusa-slicer") is None, reason="PrusaSlicer CLI no instalado")
def test_prusaslicer_lamina_cada_familia(pm, tmp_path):
    cube = ROOT / [r for r in pm["probetas"] if r["id"] == "P1.7A"][0]["files"][1]
    for fam in ("estructural", "sellado", "fusible", "cubiertas"):
        out = tmp_path / f"{fam}.gcode"
        r = subprocess.run(["prusa-slicer", "--load", str(PS / INIS["impresora"]), "--load", str(PS / INIS["filamento"]),
                            "--load", str(PS / INIS[fam]), "--export-gcode", str(cube), "-o", str(out)],
                           capture_output=True, text=True, timeout=300)
        assert r.returncode == 0 and out.exists(), (fam, r.stdout[-800:])
        tail = out.read_text(errors="ignore")[-60000:]
        want = parse_ini(PS / INIS[fam])
        for k in ("perimeters", "fill_density", "layer_height"):
            assert f"; {k} = {want[k]}" in tail, (fam, k)
        assert "; temperature = " + parse_ini(PS / INIS["filamento"])["temperature"] in tail


def test_informe_de_laminado_si_existe():
    rep = PS / "slice_report.json"
    if not rep.exists():
        pytest.skip("sin slice_report.json")
    data = json.loads(rep.read_text(encoding="utf-8"))
    assert data["formato_y_limites_ok"]
    lam = data.get("laminado")
    if lam:
        assert all(it.get("ok") for it in lam["items"]), [it["id"] for it in lam["items"] if not it.get("ok")]
        assert all(it.get("config_ok", True) for it in lam["items"])


def test_tabla_fabricacion_regenera_bloques():
    r = subprocess.run([sys.executable, str(PRB / "tabla_fabricacion.py")], cwd=ROOT, capture_output=True, text=True,
                       timeout=300)
    assert r.returncode == 0, r.stdout + r.stderr
    doc = (ROOT / "05_fabricacion.md").read_text(encoding="utf-8")
    for b in ("perfiles", "orientacion", "probetas", "criterios", "ajustes", "roscas", "totales"):
        m = re.search(rf"<!-- FAB:{b} -->(.*?)<!-- /FAB:{b} -->", doc, re.S)
        assert m and m.group(1).count("|") > 10, b
    assert "<!-- AUTO:" not in doc                                  # docgen exige bloques conocidos
