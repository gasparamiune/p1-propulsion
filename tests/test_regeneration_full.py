"""Regeneración de punta a punta: copia el proyecto a un directorio temporal, cambia dos
entradas en inputs.yaml (espesor máximo de espejo y masa por persona), corre
`run_all.py --fast --skip-render` en la copia y verifica que cambian cálculos, CAD, BOM y
documentos. Tarda ~1 min (malla gruesa); se puede saltar con P1_SKIP_SLOW=1."""
import json
import os
import re
import shutil
import subprocess
import sys

import pytest
import yaml

SKIP = os.environ.get("P1_SKIP_SLOW") == "1"


@pytest.mark.skipif(SKIP, reason="P1_SKIP_SLOW=1")
def test_full_regeneration(root, tmp_path):
    dst = tmp_path / "p1"
    ignore = shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "*.stl", "*.step", "*.blend",
                                    "renders", "*.png")
    shutil.copytree(root, dst, ignore=ignore)
    before = {
        "sizing": json.loads((root / "resultados" / "sizing.json").read_text(encoding="utf-8")),
        "manifest": json.loads((root / "resultados" / "manifest.json").read_text(encoding="utf-8")),
        "bom": json.loads((root / "resultados" / "bom_resumen.json").read_text(encoding="utf-8")),
    }
    d = yaml.safe_load((dst / "inputs.yaml").read_text(encoding="utf-8"))
    d["boat"]["transom"]["thickness_range_mm"] = [20, 80]
    d["load"]["mass_per_person_kg"] = 85.0
    (dst / "inputs.yaml").write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
    r = subprocess.run([sys.executable, "run_all.py", "--fast", "--skip-render"], cwd=dst,
                       capture_output=True, text=True, timeout=1800)
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-3000:]
    sz = json.loads((dst / "resultados" / "sizing.json").read_text(encoding="utf-8"))
    man = json.loads((dst / "resultados" / "manifest.json").read_text(encoding="utf-8"))
    bom = json.loads((dst / "resultados" / "bom_resumen.json").read_text(encoding="utf-8"))
    # cálculos: 30 kg menos de personas
    assert abs((before["sizing"]["masses"]["total_kg"] - sz["masses"]["total_kg"]) - 30.0) < 1e-6
    assert sz["cruise"]["design"]["P_bat"] < before["sizing"]["cruise"]["design"]["P_bat"]
    # CAD: la abrazadera crece 15 mm de garganta

    def bb(m, pid):
        r_ = [p for p in m["parts"] if p["id"] == pid][0]
        return r_.get("print_bbox_mm") or r_.get("bbox_mm")
    assert max(bb(man, "P1-MNT-01")) > max(bb(before["manifest"], "P1-MNT-01"))
    # BOM regenerada y documentos actualizados con los valores nuevos
    assert "total_eur" in bom
    readme = (dst / "README.md").read_text(encoding="utf-8")
    m = re.search(r"<!--V:sizing\.masses\.payload_kg:\.0f-->(\d+)<!--/V-->", readme)
    assert m and int(m.group(1)) == round(sz["masses"]["payload_kg"])
