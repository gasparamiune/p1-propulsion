"""Estructural (FS), BOM y coherencia documentos ↔ código."""
import csv
import json
import re
import subprocess
import sys


def test_structural_all_ok(root, manifest):
    r = subprocess.run([sys.executable, str(root / "04_diseno" / "structural.py")], cwd=root, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    est = json.load(open(root / "resultados" / "estructural.json", encoding="utf-8"))
    assert est["n_fail"] == 0
    text = " ".join(row["part"] for row in est["rows"])
    # toda pieza impresa o mecanizada que lleva carga tiene al menos un FS calculado
    for pid in ("P1-INT-01", "P1-INT-02", "P1-INT-03", "P1-INT-04", "P1-PMP-01", "P1-PMP-03", "P1-PMP-06",
                "P1-PMP-08", "P1-PMP-09", "P1-DRV-01", "P1-DRV-03", "P1-MOT-02", "P1-STE-01", "P1-REV-01",
                "P1-CTL-02", "P1-CTL-03", "P1-ELE-01"):
        assert pid in text, pid


def test_load_cases_covered(root):
    sz = json.load(open(root / "resultados" / "sizing.json", encoding="utf-8"))
    for k in ("T_bollard_N", "T_top_N", "p_pump_max_Pa", "F_steer_side_N", "F_bucket_N", "torque_max_Nm"):
        assert sz["loads"][k] > 0, k
    est = json.load(open(root / "resultados" / "estructural.json", encoding="utf-8"))
    lcs = " ".join(r["load_case"].lower() for r in est["rows"])
    for kw in ("empuje", "presión", "bucket", "par", "fatiga"):
        assert kw in lcs, kw


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
            "est": load("estructural.json"), "verify": load("verify.json"), "arch": load("arquitectura.json"),
            "cmp": load("comparacion.json")}
    pat = re.compile(r"<!--V:([\w.]+):([^>]*?)-->(.*?)<!--/V-->", re.S)
    n = 0
    for md in list(root.glob("*.md")):
        for m in pat.finditer(md.read_text(encoding="utf-8")):
            src, _, rest = m.group(1).partition(".")
            assert format(getpath(srcs[src], rest), m.group(2)) == m.group(3), (md.name, m.group(1))
            n += 1
    assert n >= 10
