"""Estructural (FS), BOM y coherencia documentos ↔ código."""
import csv
import json
import re
import subprocess
import sys


def test_structural_all_ok(root):
    r = subprocess.run([sys.executable, str(root / "04_diseno" / "structural.py")], cwd=root, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    est = json.load(open(root / "resultados" / "estructural.json", encoding="utf-8"))
    assert est["n_fail"] == 0
    parts = {row["part"].split(" ")[0] for row in est["rows"]}
    # toda pieza impresa estructural tiene al menos un FS calculado
    for pid in ("P1-MNT-01", "P1-MNT-03", "P1-MNT-04", "P1-MNT-05", "P1-MNT-06", "P1-HSG-01", "P1-HSG-02",
                "P1-HSG-04", "P1-STR-01", "P1-PRP-01", "P1-PRP-02"):
        assert any(pp.startswith(pid) for pp in parts), pid


def test_load_cases_covered(root):
    est = json.load(open(root / "resultados" / "estructural.json", encoding="utf-8"))
    lcs = " ".join(r["load_case"] for r in est["rows"])
    for lc in ("LC1", "LC3", "LC4", "LC5", "LC6", "LC7"):
        assert lc in lcs, lc
    sz = json.load(open(root / "resultados" / "sizing.json", encoding="utf-8"))
    assert "LC2_marcha_atras" in sz["loadcases"]


def test_bom(root):
    rows = list(csv.DictReader(open(root / "bom.csv", encoding="utf-8")))
    ids = {r["ID"] for r in rows}
    for must in ("B-MOT", "B-ESC", "B-BAT", "B-CHG", "B-FUSE", "B-CONT", "B-KILL", "B-SEAL", "B-BRG", "B-CPL",
                 "B-PETG", "S-CNC-IMP", "S-CNC-STAT", "R-PIN", "B-BILGE", "B-FOAM", "B-PFD"):
        assert must in ids, must
    for r in rows:
        if r["ID"].startswith(("B-", "S-", "R-", "H-", "MP-")):
            assert r["link_o_busqueda"].startswith(("http", "buscar:")), r["ID"]
            assert r["fecha"]
            assert r["etiqueta"].startswith(("[VERIFICADO", "[ESTIMADO", "[CALCULADO")), r["ID"]
            assert (r["verificado"] == "sí") == r["etiqueta"].startswith("[VERIFICADO"), r["ID"]
    tot = [r for r in rows if r["descripcion"] == "TOTAL SISTEMA EUR"][0]
    assert float(tot["precio_total_EUR"]) > 300
    # cobertura del CAD: compradas con precio; mecanizadas con materia prima o servicio
    man = json.load(open(root / "resultados" / "manifest.json", encoding="utf-8"))
    cov = {pid for r in rows for pid in (r.get("cubre") or "").split()}
    for p in man["parts"]:
        if p["process"] in ("comprada", "torneada", "impresa"):
            assert p["id"] in cov, p["id"]
    summ = json.load(open(root / "resultados" / "bom_resumen.json", encoding="utf-8"))
    for k in ("subtotal_eur", "shipping_eur", "contingency_eur", "total_eur", "total_dkk", "by_category",
              "verified_frac_of_subtotal", "operation_gear_eur", "fixed_excl_battery_eur", "hull_changes_eur"):
        assert k in summ, k
    assert not summ["unpriced_bought_parts"] and not summ["machined_without_service"]


def test_docs_in_sync(root):
    r = subprocess.run([sys.executable, str(root / "docgen.py")], cwd=root, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
    # tras docgen, cada valor marcado coincide con su fuente
    from docgen import getpath, load
    srcs = {"sizing": load("sizing.json"), "bom": load("bom_resumen.json"), "manifest": load("manifest.json"),
            "est": load("estructural.json"), "verify": load("verify.json"), "arch": load("arquitectura.json")}
    pat = re.compile(r"<!--V:([\w.]+):([^>]*?)-->(.*?)<!--/V-->", re.S)
    n = 0
    for md in list(root.glob("*.md")):
        for m in pat.finditer(md.read_text(encoding="utf-8")):
            src, _, rest = m.group(1).partition(".")
            assert format(getpath(srcs[src], rest), m.group(2)) == m.group(3), (md.name, m.group(1))
            n += 1
    assert n >= 10
