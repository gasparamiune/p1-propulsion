"""Regeneración de punta a punta: copia el proyecto a un directorio temporal, cambia dos
entradas en inputs.yaml (espesor del fondo del casco y masa del piloto), corre
`run_all.py --fast --skip-render` en la copia y verifica que cambian cálculos, CAD, BOM y
documentos. Tarda varios minutos (optimizador + CAD); se puede saltar con P1_SKIP_SLOW=1."""
import json
import os
import re
import shutil
import subprocess
import sys

import pytest
import yaml

SKIP = os.environ.get("P1_SKIP_SLOW") == "1"


def _item(sz, iid):
    return [i for i in sz["masses"]["items"] if i["id"] == iid][0]


def _part(man, pid):
    return [p for p in man["parts"] if p["id"].startswith(pid)][0]


@pytest.mark.skipif(SKIP, reason="P1_SKIP_SLOW=1")
def test_full_regeneration(root, tmp_path):
    dst = tmp_path / "p1"
    ignore = shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "*.stl", "*.step", "*.step.gz",
                                    "*.blend", "renders", "*.png", "mallas.txt")
    shutil.copytree(root, dst, ignore=ignore)
    before = {
        "sizing": json.loads((root / "resultados" / "sizing.json").read_text(encoding="utf-8")),
        "manifest": json.loads((root / "resultados" / "manifest.json").read_text(encoding="utf-8")),
    }
    d = yaml.safe_load((dst / "inputs.yaml").read_text(encoding="utf-8"))
    d["boat"]["bottom_thickness_mm"] = d["boat"]["bottom_thickness_mm"] + 4.0
    d["masses"]["items"]["pilot"]["kg"] = d["masses"]["items"]["pilot"]["kg"] - 15.0
    (dst / "inputs.yaml").write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
    r = subprocess.run([sys.executable, "run_all.py", "--fast", "--skip-render"], cwd=dst,
                       capture_output=True, text=True, timeout=3600)
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-3000:]
    sz = json.loads((dst / "resultados" / "sizing.json").read_text(encoding="utf-8"))
    man = json.loads((dst / "resultados" / "manifest.json").read_text(encoding="utf-8"))
    bom = json.loads((dst / "resultados" / "bom_resumen.json").read_text(encoding="utf-8"))
    # cálculos: piloto 15 kg más liviano → menos masa y más margen en la joroba
    assert abs(_item(sz, "pilot")["kg"] - (_item(before["sizing"], "pilot")["kg"] - 15.0)) < 1e-9
    assert sz["masses"]["total_kg"] < before["sizing"]["masses"]["total_kg"]
    assert sz["performance"]["hump_margin_min"] >= before["sizing"]["performance"]["hump_margin_min"] - 1e-6
    # CAD: el fondo más grueso cambia la placa base de la toma (cuerpo enrasado)
    assert _part(man, "P1-INT-02")["volume_mm3"] != pytest.approx(_part(before["manifest"], "P1-INT-02")["volume_mm3"])
    # BOM regenerada y documentos actualizados con los valores nuevos
    assert "total_eur" in bom
    readme = (dst / "README.md").read_text(encoding="utf-8")
    m = re.search(r"<!--V:sizing\.performance\.hump_margin_min:\.0%-->(\d+)%<!--/V-->", readme)
    assert m and int(m.group(1)) == round(100 * sz["performance"]["hump_margin_min"])
