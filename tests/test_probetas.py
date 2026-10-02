"""Probetas y ensayos de taller del waterjet (04_diseno/probetas/) y perfiles PrusaSlicer (prusaslicer/).

- Construye las probetas con build_probetas.py --sin-tablas si sus salidas faltan o están desactualizadas
  respecto de los módulos, params, cadlib, piezas, inputs.yaml o los JSON de resultados (o si
  P1_REBUILD_PROBETAS=1); si no, usa las salidas existentes.
- Verifica malla cerrada (trimesh), 1 cuerpo, apoyo en z = 0 y envolvente ≤ printer.envelope_mm de las
  probetas impresas; que estén los ensayos del set del waterjet (impresos y de taller) y ninguno de la cola
  larga; que los criterios lean sizing.json / estructural.json / params.
- Verifica que los .ini existen, tienen formato clave = valor y las claves críticas (límites de inputs.yaml).
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
IMPRESAS = ["P1.1", "P1.4", "P1.6", "P1.7"]
TALLER = ["P1.9", "P1.10", "P1.11", "P1.12"]
TESTS = IMPRESAS + TALLER
COLA_LARGA = ["P1.2", "P1.3", "P1.5", "P1.8"]           # rodamiento en PETG, tuerca M6, flexión, patín
FAMILIAS = ("estructural", "sellado", "cubiertas")
INIS = {"impresora": "P1_impresora_Ender3S1.ini", "filamento": "P1_filamento_PETG.ini",
        "estructural": "P1_impresion_estructural_0.20.ini", "sellado": "P1_impresion_sellado_0.15.ini",
        "cubiertas": "P1_impresion_cubiertas_0.20.ini"}


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
        r = subprocess.run([sys.executable, str(PRB / "build_probetas.py"), "--sin-tablas"], cwd=ROOT, capture_output=True,
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
    assert not set(COLA_LARGA) & set(pm["tests"]), set(COLA_LARGA) & set(pm["tests"])
    ids = {r["id"] for r in pm["probetas"]}
    for must in ("P1.1A", "P1.1H", "P1.4", "P1.6A", "P1.6B", "P1.7A", "P1.7B", "P1.7C"):
        assert must in ids, must
    assert not [r["id"] for r in pm["probetas"] if r["test"] in COLA_LARGA]
    for t in IMPRESAS:
        assert pm["tests"][t]["tipo"] == "impresa"
    for t in TALLER:                                              # ensayos de taller: sin CAD
        assert pm["tests"][t]["tipo"] == "taller"
        assert not [r for r in pm["probetas"] if r["test"] == t]
    assert not pm["fails"], pm["fails"]


def test_sin_salidas_viejas(pm):
    files = {f for r in pm["probetas"] for f in r["files"]}
    for d in ("step", "stl"):
        for f in (PRB / d).glob("*"):
            assert str(f.relative_to(ROOT)) in files, f"salida de probeta que ya no existe: {f.name}"


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
        assert r["profile"] in FAMILIAS


def test_cotas_de_cada_modulo_ok(pm):
    bad = [(t, c["name"]) for t, v in pm["tests"].items() for c in v["checks"] if not c["ok"]]
    assert not bad, bad
    for t in TESTS:
        c = pm["tests"][t]["criterios"]
        assert c and c.get("pasa_si") and c.get("ensayo"), t


def test_probetas_impresas_con_perfil_de_su_pieza(pm, manifest):
    sys.path.insert(0, str(PRB))
    import familias as FAM
    fam = {r["id"]: r["profile"] for r in pm["probetas"]}
    assert fam["P1.4"] == FAM.familia({"id": "P1-ELE-01"})[0]
    assert fam["P1.6A"] == fam["P1.6B"] == fam["P1.7A"] == FAM.familia({"id": "P1-INT-04"})[0]
    printed = {r["id"] for r in manifest["parts"] if r["process"] == "impresa"}
    assert set(pm["tests"]["P1.1"]["piezas"]) <= printed | {"P1-INT-01"}


def test_criterios_leen_los_json(pm, sizing):
    import params as P
    p = P.load()
    est = json.loads((ROOT / "resultados" / "estructural.json").read_text(encoding="utf-8"))
    T = pm["tests"]
    sp = sizing["mech"]["shear_pin"]
    c9 = T["P1.9"]["criterios"]
    assert c9["d_pin_mm"] == sp["d_mm"] and abs(c9["T_cut_Nm"] - sp["T_cut_Nm"]) < 0.01
    assert c9["banda"] == [0.8, 1.2]
    assert abs(c9["T_min_Nm"] - round(0.8 * sp["T_cut_Nm"], 1)) < 0.06 and abs(c9["T_max_Nm"] - round(1.2 * sp["T_cut_Nm"], 1)) < 0.06
    assert c9["T_min_Nm"] > c9["T_ctrl_Nm"]                         # no corta en marcha
    assert c9["semipasadores_por_juego"] == p.pmp_pin_n == 2 and c9["largo_semipasador_mm"] == p.pmp_pin_half_len
    assert c9["D_manguito_mm"] == 2 * p.pmp_land_r
    c11 = T["P1.11"]["criterios"]
    pd = est["loads"]["structural_bomba"]["loads_used"]["p_design_Pa"]
    assert abs(c11["p_ensayo_MPa"] - round(1.5 * pd / 1e6, 3)) < 1e-6 and c11["p_ensayo_MPa"] >= 0.3   # R12 §7.2
    assert c11["luz_bridas_mm"] == p.pmp_stack_gap and "radial" in c11["f2"] and c11["D_salida_mm"] == p.D_noz
    c12 = T["P1.12"]["criterios"]
    assert abs(c12["c_diseno_mm"] - round(sizing["pump"]["tip_clearance_mm"], 3)) < 1e-6
    assert c12["c_min_mm"] == 0.30 and 0.39 <= c12["c_max_mm"] <= 0.40 + 1e-9 and c12["c_min_mm"] <= c12["c_diseno_mm"] <= c12["c_max_mm"]
    c10 = {b["id"]: b for b in T["P1.10"]["criterios"]["bujes"]}
    assert abs(c10["P1-PMP-07"]["d"] - p.shaft_d) < 1e-9 and abs(c10["P1-PMP-07"]["D"] - p.pmp_brg_id) < 1e-9
    assert abs(c10["P1-PMP-11"]["d"] - p.steer_pin_d) < 1e-9
    for b in c10.values():
        assert b["d"] < b["D_min_mm"] <= b["D"]
    c6 = T["P1.6"]["criterios"]
    assert abs(c6["p_ensayo_Pa"] - round(sizing["loads"]["p_pump_max_Pa"], 0)) < 1.0
    d, w = c6["ranura_mm"]
    assert 2.57 <= d <= 2.72 and 4.50 <= w <= 4.75                 # research/R05 B3 (Parker 4-3), cordón 3,53
    c4 = T["P1.4"]["criterios"]
    assert c4["F_inserto_N"] and abs(c4["umbral_N"] - round(c4["FS"] * c4["F_inserto_N"], 0)) < 1.0
    c1 = T["P1.1"]["criterios"]
    assert float(p.CTL_kill_hole) in c1["nominales_mm"] and 6.0 in c1["nominales_mm"]
    assert float(p.clr) in c1["holguras_mm"]
    for r in c1["ajustes_en_piezas"]:                               # cada Ø del CAD está en el peine
        assert r["holgura_cad"] in c1["holguras_por_d_mm"][f"{r['d_nom']:g}"]


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
    cub = ini["cubiertas"]
    assert int(cub["perimeters"]) >= 4
    assert not (PS / "P1_impresion_fusible_0.20.ini").exists()      # ninguna pieza impresa del jet es fusible
    for name in FAMILIAS:                                                          # caudal ≤ límite del filamento
        v = max(float(ini[name][k]) for k in ("perimeter_speed", "infill_speed", "solid_infill_speed"))
        assert v * float(ini[name]["infill_extrusion_width"]) * float(ini[name]["layer_height"]) \
            <= float(fil["filament_max_volumetric_speed"]), name


def test_familias_coinciden_con_ini(ini):
    sys.path.insert(0, str(PRB))
    import familias as FAM
    assert tuple(FAM.PERFILES) == FAMILIAS
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
    for fam in FAMILIAS:
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


def test_informe_de_laminado_si_existe(manifest, pm):
    rep = PS / "slice_report.json"
    if not rep.exists():
        pytest.skip("sin slice_report.json")
    data = json.loads(rep.read_text(encoding="utf-8"))
    assert data["formato_y_limites_ok"]
    lam = data.get("laminado")
    if lam:
        assert all(it.get("ok") for it in lam["items"]), [it["id"] for it in lam["items"] if not it.get("ok")]
        assert all(it.get("config_ok", True) for it in lam["items"])
        printed = {r["id"] for r in manifest["parts"] if r["process"] == "impresa"}
        piezas = {it["id"] for it in lam["items"] if it["tipo"] == "pieza"}
        assert piezas == printed, piezas ^ printed                  # solo piezas del waterjet
        probs = {it["id"] for it in lam["items"] if it["tipo"] == "probeta"}
        assert probs == {r["id"] for r in pm["probetas"]}, probs ^ {r["id"] for r in pm["probetas"]}


def test_tabla_fabricacion_regenera_bloques():
    r = subprocess.run([sys.executable, str(PRB / "tabla_fabricacion.py")], cwd=ROOT, capture_output=True, text=True,
                       timeout=300)
    assert r.returncode == 0, r.stdout + r.stderr
    doc = (ROOT / "05_fabricacion.md").read_text(encoding="utf-8")
    for b in ("procesos", "perfiles", "orientacion", "roscas", "totales", "torno", "soldadura", "cnc", "anodizado",
              "probetas", "ensayos", "ajustes"):
        m = re.search(rf"<!-- FAB:{b} -->(.*?)<!-- /FAB:{b} -->", doc, re.S)
        assert m and m.group(1).count("|") > 10, b
    m = re.search(r"<!-- FAB:procedimientos -->(.*?)<!-- /FAB:procedimientos -->", doc, re.S)
    assert m and all(f"**{t} " in m.group(1) for t in TESTS)
    for viejo in ("P1-MNT-", "P1-HSG-", "P1-PRP-", "P1-STR-", "P1-SAF-"):    # nada de la cola larga
        assert viejo not in doc, viejo
    assert "<!-- AUTO:" not in doc                                  # docgen exige bloques conocidos
