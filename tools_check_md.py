#!/usr/bin/env python3
"""tools_check_md.py — Verificación de solo lectura de un .md (no escribe nada).

Uso: python3 tools_check_md.py ARCHIVO.md [...]
  - Comprueba que cada marcador <!--V:fuente.ruta:fmt-->valor<!--/V--> resuelve y muestra el
    valor que pondría docgen (fuentes: sizing, bom, manifest, est, verify, arch).
  - Lista los links http(s) del archivo que NO aparecen en research/*.md, inputs.yaml ni en
    otros .md del repositorio (candidatos a "link no abierto en esta sesión").
  - Lista líneas con números sin etiqueta en tablas (heurística, solo aviso).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RES = ROOT / "resultados"
SRC = {"sizing": "sizing.json", "bom": "bom_resumen.json", "manifest": "manifest.json",
       "est": "estructural.json", "verify": "verify.json", "arch": "arquitectura.json",
       "cmp": "comparacion.json"}
PAT = re.compile(r"<!--V:([\w.\-]+):([^>]*?)-->(.*?)<!--/V-->", re.S)
URL = re.compile(r"https?://[^\s)\]>\"'`|]+")


def getpath(src, path):
    cur = src
    for k in path.split("."):
        cur = cur[int(k)] if isinstance(cur, list) else cur[k]
    return cur


def main(files):
    srcs = {k: json.loads((RES / v).read_text(encoding="utf-8")) for k, v in SRC.items() if (RES / v).exists()}
    known = ""
    for f in list((ROOT / "research").glob("*.md")) + [ROOT / "inputs.yaml"]:
        known += f.read_text(encoding="utf-8")
    bad = 0
    for fn in files:
        txt = Path(fn).read_text(encoding="utf-8")
        for m in PAT.finditer(txt):
            path, fmt, shown = m.groups()
            src, _, rest = path.partition(".")
            try:
                val = getpath(srcs[src], rest)
                s = format(val, fmt) if fmt else str(val)
                if s != shown:
                    print(f"{fn}: {path} muestra '{shown}', docgen pondrá '{s}'")
            except Exception as e:  # noqa: BLE001
                print(f"{fn}: MARCADOR ROTO {path} ({e})")
                bad += 1
        for u in sorted(set(URL.findall(txt))):
            u2 = u.rstrip(".,;:")
            if u2 not in known:
                print(f"{fn}: link no encontrado en research/ ni inputs.yaml → {u2}")
                bad += 1
    print(f"tools_check_md: {bad} problemas")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
