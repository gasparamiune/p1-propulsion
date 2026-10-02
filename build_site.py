#!/usr/bin/env python3
"""build_site.py — Sitio web estático del proyecto (GitHub Pages, carpeta docs/).

Genera, desde los mismos archivos que usa el resto del pipeline (resultados/*.json,
04_diseno/fea/resultados_fea.json, bom.csv, los .md, los planos SVG y el visor 3D):

    index.html        portada: qué es, números clave (con etiqueta), estado honesto, recomendación,
                      próximos pasos físicos y accesos
    documentos.html   índice de documentos + figuras
    doc/<ruta>.html   cada .md renderizado (python-markdown) con índice por página
    planos.html       galería de planos SVG por subsistema (planos/*.svg)
    bom.html          bom.csv como tabla con búsqueda y los totales de resultados/bom_resumen.json
    fea.html          FS por pieza crítica desde 04_diseno/fea/resultados_fea.json
    visor/            el visor 3D (copia; solo se le agrega cabecera <head> y un enlace «← Inicio»)
    og.png, .nojekyll, assets/site.css

Determinista (sin fechas de compilación, sin red, sin git). Los valores se resuelven con el mismo
resolvedor que usan los marcadores <!--V:fuente.ruta:formato--> de docgen.py.

Uso: python build_site.py [--out DIR]     (por defecto DIR = docs/ junto a este archivo)
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import posixpath
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote, unquote

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import docgen  # noqa: E402  (resolvedor de rutas «fuente.ruta» de los marcadores V)

SITE_URL = "https://gasparamiune.github.io/p1-propulsion/"
REPO_URL = "https://github.com/gasparamiune/p1-propulsion"
BLOB = REPO_URL + "/blob/main/"
TREE = REPO_URL + "/tree/main/"
SITE_NAME = "P1-J · Strålen"
SITE_TITLE = "P1-J · Strålen — waterjet eléctrico inboard para un jet boat de 2,30 m"

# Documentos que se publican como páginas (ruta en el repo). El resto de los .md se enlaza a GitHub.
DOCS_MAIN = ["README.md", "01_investigacion.md", "02_calculos.md", "03_arquitectura.md", "04_diseno/README.md",
             "04_diseno/fea/README.md", "04_diseno/electronica/README.md", "05_fabricacion.md",
             "06_ensamblaje_y_pruebas.md", "07_roadmap_P2.md", "decisiones.md", "auditoria.md",
             "PENDIENTES_GASPAR.md", "checklist_salida.md"]
DOC_GROUPS = [
    ("Empezar aquí", ["README.md", "PENDIENTES_GASPAR.md", "checklist_salida.md"]),
    ("Memoria técnica", ["01_investigacion.md", "02_calculos.md", "03_arquitectura.md", "05_fabricacion.md",
                         "06_ensamblaje_y_pruebas.md", "07_roadmap_P2.md"]),
    ("Diseño, FEA y electrónica", ["04_diseno/README.md", "04_diseno/fea/README.md", "04_diseno/electronica/README.md"]),
    ("Decisiones y auditoría", ["decisiones.md", "auditoria.md"]),
]
VISOR_FILES = ["index.html", "datos.json", "mallas.txt", "corte_lateral.png", "plano_waterjet_jorge.png"]
IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}
SUBSYS = {  # prefijo de ID → subsistema (orden de la galería; nombres de 04_diseno/README.md)
    "INT": "Toma de agua", "PMP": "Bomba", "DRV": "Tren (eje, sello, rodamientos, acople)", "MOT": "Motor",
    "STE": "Dirección (boquilla)", "REV": "Reversa (bucket)", "CTL": "Mandos de la consola",
    "ELE": "Electrónica y refrigeración", "BAT": "Batería", "REF": "Casco de referencia",
}
MD_EXT = ["tables", "fenced_code", "toc", "sane_lists", "attr_list", "md_in_html"]

FAVICON = ("data:image/svg+xml," + quote(
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='14' fill='#0f242b'/>"
    "<path d='M10 40c8-6 14-6 22 0s14 6 22 0' fill='none' stroke='#4fb0c2' stroke-width='5' stroke-linecap='round'/>"
    "<path d='M12 26h26l14-8v20l-14-8H12z' fill='#e2601a'/></svg>", safe=":/=' "))

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;800;900'
         '&amp;family=Public+Sans:ital,wght@0,400;0,600;0,700;1,400&amp;family=JetBrains+Mono:wght@400;600&amp;display=swap">')

E = html.escape


# ───────────────────────────── datos ─────────────────────────────

def sources():
    """Las mismas fuentes que docgen.main() expone a los marcadores V (cargadas con docgen.load)."""
    fp = ROOT / "04_diseno" / "fea" / "resultados_fea.json"
    srcs = {"sizing": docgen.load("sizing.json"), "bom": docgen.load("bom_resumen.json"),
            "manifest": docgen.load("manifest.json"), "est": docgen.load("estructural.json"),
            "verify": docgen.load("verify.json"), "arch": docgen.load("arquitectura.json"),
            "cmp": docgen.load("comparacion.json"),
            "fea": json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else {}}
    srcs["_auto"] = auto_blocks(srcs)
    return srcs


def inp(path, default=None):
    """Un valor de inputs.yaml (docgen.sz_inputs), o `default` si falta."""
    try:
        return docgen.sz_inputs(path)
    except Exception:
        return default


class Values:
    def __init__(self, srcs):
        self.srcs = srcs

    def raw(self, path, default=None):
        src, _, rest = path.partition(".")
        try:
            return docgen.getpath(self.srcs[src], rest)
        except Exception:
            return default

    def __call__(self, path, fmt=".0f", es=True):
        """Valor formateado (estilo español: coma decimal, espacio fino de miles); «—» si falta."""
        v = self.raw(path)
        return fnum(v, fmt, es)


def fnum(v, fmt=".0f", es=True):
    if v is None:
        return "—"
    try:
        if isinstance(v, float) and (v == float("inf") or v > 1e12):
            return "∞"
        if fmt.endswith("%"):
            s = format(v * 100, "." + (fmt[1:-1] or "0") + "f")
            s = s.replace(".", ",") if es else s
            return s + "\u00a0%"
        if fmt and fmt[-1] in "fgd" and not isinstance(v, str):
            s = format(v, "," + fmt) if fmt[-1] != "g" else format(v, fmt)
            if es:
                s = s.replace(",", "\u202f").replace(".", ",")
            return s
        return format(v, fmt) if fmt else str(v)
    except (TypeError, ValueError):
        return str(v)


# ───────────────────────────── utilidades de rutas y HTML ─────────────────────────────

def rel(page, target):
    """Ruta relativa desde la página `page` (ruta en el sitio) hasta `target` (ruta en el sitio)."""
    d = posixpath.dirname(page) or "."
    return posixpath.relpath(target, d)


def doc_out(src):
    return "doc/" + src[:-3] + ".html"


def all_docs():
    research = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "research").glob("*.md"))
    return [d for d in DOCS_MAIN if (ROOT / d).exists()] + research


MARK_V_OPEN = re.compile(r"<!--V:[\w.\-]+:[^>]*?-->")
MARK_V_CLOSE = re.compile(r"<!--/V-->")
MARK_AUTO = re.compile(r"^[ \t]*<!-- /?[A-Z]+:[\w\-]+ -->[ \t]*$", re.M)


PAT_V = re.compile(r"<!--V:([\w.\-]+):([^>]*?)-->(.*?)<!--/V-->", re.S)
PAT_AUTO = re.compile(r"(<!-- AUTO:(\w+) -->)(.*?)(<!-- /AUTO:\2 -->)", re.S)


def auto_blocks(srcs):
    """Los bloques AUTO de docgen recalculados con los datos actuales (docgen.blocks, sin escribir nada)."""
    B = docgen.blocks(srcs["sizing"], srcs["bom"], srcs["manifest"], srcs["est"], srcs["verify"])
    if (docgen.RES / "arquitectura_tabla.md").exists():
        B["arch"] = (docgen.RES / "arquitectura_tabla.md").read_text(encoding="utf-8").strip()
    return B


def resolve_markers(txt, srcs, es=False):
    """Como docgen.main: los bloques AUTO y el texto entre marcadores V se recalculan con los datos actuales
    (si algo no resuelve, queda el texto que ya tenía el documento). Después se quitan los comentarios.
    es=True formatea los valores V en estilo español (coma decimal), para los extractos de la portada."""
    blocks = srcs.get("_auto") or {}

    def rb(m):
        name = m.group(2)
        return f"{m.group(1)}\n{blocks[name]}\n{m.group(4)}" if name in blocks else m.group(0)

    def rv(m):
        path, fmt, old = m.group(1), m.group(2), m.group(3)
        src, _, rest = path.partition(".")
        try:
            val = docgen.getpath(srcs[src], rest)
            if es and not isinstance(val, str):
                return fnum(val, fmt, es=True)
            return format(val, fmt) if fmt else str(val)
        except Exception:
            return old
    return strip_markers(PAT_V.sub(rv, PAT_AUTO.sub(rb, txt)))


def strip_markers(txt):
    """Quita los comentarios de los marcadores (los valores entre ellos ya son texto plano)."""
    txt = MARK_V_OPEN.sub("", txt)
    txt = MARK_V_CLOSE.sub("", txt)
    return MARK_AUTO.sub("", txt)


def md_title(txt, fallback):
    m = re.search(r"^#\s+(.+?)\s*#*\s*$", txt, re.M)
    return plain(m.group(1)) if m else fallback


def plain(s):
    """Texto plano de un fragmento Markdown: se renderiza y se quitan las etiquetas (así los «_» dentro de
    palabras —run_all.py, PENDIENTES_GASPAR— quedan, y solo se van los marcadores de énfasis y código)."""
    import markdown
    s = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    h = markdown.markdown(s)
    s = html.unescape(re.sub(r"<[^>]+>", "", h))
    return re.sub(r"\s+", " ", s).strip()


META_PARA = re.compile(r"^(Fecha|Consulta|Autor|Autora|Estado|Versión|Fuente|Fuentes)\b", re.I)


def md_description(txt, n=180):
    """Primer párrafo de texto después del título (sin tablas, código ni encabezados); se saltean los párrafos
    de metadatos («Fecha: …», «Consulta: …», «Autor: …») y los muy cortos."""
    paras, para, in_code = [], [], False

    def flush():
        if para:
            paras.append(plain(" ".join(para)))
            para.clear()

    for ln in txt.splitlines():
        s = ln.strip()
        if s.startswith("```"):
            in_code = not in_code
            flush()
            continue
        if in_code:
            continue
        if not s or s.startswith(("#", "|", "<", "---", "![")):
            flush()
            continue
        para.append(re.sub(r"^(?:>\s*)*(?:[-*+]\s+|\d+\.\s+)?", "", s).strip())
        if len(paras) > 6:
            break
    flush()
    good = [p for p in paras if p and not META_PARA.match(p) and len(p) >= 60]
    d = good[0] if good else (paras[0] if paras else "")
    return d if len(d) <= n else d[: n - 1].rsplit(" ", 1)[0] + "…"


DIA = '<span class="dia">Ø</span>'
PID = re.compile(r"\bP1-[A-Z]{2,4}-\d{2}\b")


def _text_nodes(h, fn):
    """Aplica fn al texto (no a las etiquetas ni atributos) de un fragmento HTML."""
    return re.sub(r"(^|>)([^<]+)", lambda t: t.group(1) + fn(t.group(2)), h)


def display_glyphs(h):
    """En la fuente display (Big Shoulders) la «Ø» es igual a un cero tachado: «Ø132» se lee «0132». Dentro de
    h1–h3 y de los números grandes (.num) la «Ø» va en la fuente del texto (span.dia)."""
    fix = lambda m: _text_nodes(m.group(0), lambda t: t.replace("Ø", DIA))
    h = re.sub(r"<(h[1-3])\b[^>]*>.*?</\1>", fix, h, flags=re.S)
    return re.sub(r'<span class="num">[^<]*</span>', fix, h)


def nowrap_pids(h):
    """Los códigos de pieza (P1-STE-01) no se cortan en el guion."""
    return _text_nodes(h, lambda t: PID.sub(lambda m: f'<span class="pid">{m.group(0)}</span>', t))


def wrap_tables(h):
    h = re.sub(r"<table(\s[^>]*)?>", lambda m: f'<div class="table-wrap"><table{m.group(1) or ""}>', h)
    return h.replace("</table>", "</table></div>")


class Ctx:
    """Estado de una compilación: carpeta de salida, documentos publicados, archivos a copiar."""

    def __init__(self, out):
        self.out = out
        self.docs = all_docs()
        self.doc_set = set(self.docs)
        self.copied = set()

    def copy(self, src_rel, dst_rel):
        if dst_rel in self.copied:
            return
        dst = self.out / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / src_rel, dst)
        self.copied.add(dst_rel)

    def rewrite_links(self, h, src_dir, page):
        """href/src de un HTML renderizado desde un .md de `src_dir` (repo), publicado en `page` (sitio)."""

        def fix(m):
            attr, q, url = m.group(1), m.group(2), html.unescape(m.group(3))
            if not url or url.startswith(("#", "mailto:", "data:", "tel:")) or re.match(r"^[a-z][a-z0-9+.\-]*://", url, re.I):
                return m.group(0)
            path, _, frag = url.partition("#")
            path = unquote(path)
            if path.startswith("/"):
                target = posixpath.normpath(path.lstrip("/")) if path.strip("/") else ""
            else:
                target = posixpath.normpath(posixpath.join(src_dir, path)) if path else ""
            if target in ("", "."):
                new = TREE.rstrip("/")
            elif target.startswith(".."):
                return m.group(0)
            elif target in self.doc_set:
                new = rel(page, doc_out(target)) + (("#" + frag) if frag else "")
            elif target.rstrip("/") == "04_diseno/visor" or (
                    target.startswith("04_diseno/visor/") and posixpath.basename(target) in VISOR_FILES):
                new = rel(page, "visor/" + (posixpath.basename(target) if target.endswith(tuple(VISOR_FILES)) else "index.html"))
            elif attr == "src" and posixpath.splitext(target)[1].lower() in IMG_EXT and (ROOT / target).is_file():
                site_path = "doc/" + target
                self.copy(target, site_path)
                new = rel(page, site_path)
            elif (ROOT / target).is_dir() or path.endswith("/"):
                new = TREE + quote(target.rstrip("/")) + "/"
            else:
                new = BLOB + quote(target) + (("#" + frag) if frag else "")
            return f"{attr}={q}{E(new)}{q}"

        return re.sub(r"\b(href|src)=([\"'])(.*?)\2", fix, h)


LIST_ITEM = re.compile(r"^( *)([-*+]|\d+\.)\s+\S")


def fix_lists(txt):
    """Listas al estilo GitHub → python-markdown: (1) una línea en blanco antes de una lista que viene pegada a
    un párrafo (si no, python-markdown la funde en el párrafo con los «- » a la vista); (2) sangría de las
    sublistas a 4 espacios por nivel (GitHub acepta 2 o 3); (3) casillas «- [ ]» / «- [x]» → ☐ / ☑.
    No toca los bloques ``` ."""
    out, stack, prev, prev_blank, fence = [], None, "", True, False
    for ln in txt.splitlines():
        s = ln.lstrip(" ")
        k = len(ln) - len(s)
        if s.startswith(">") and not fence:       # lista dentro de una cita: línea «>» vacía antes
            q = s[1:].lstrip(" ")
            pq = prev.lstrip(" ")[1:].lstrip(" ") if prev.lstrip(" ").startswith(">") else ""
            if LIST_ITEM.match(q) and pq and not LIST_ITEM.match(pq):
                out.append(" " * k + ">")
            out.append(ln)
            prev, prev_blank, stack = ln, False, None
            continue
        if s.startswith(("```", "~~~")):
            fence = not fence
            if k == 0:
                stack = None
            out.append(ln)
            prev, prev_blank = ln, False
            continue
        if fence:
            out.append(ln)
            continue
        m = LIST_ITEM.match(ln)
        if m:
            if stack is None:
                if k >= 4:          # bloque de código indentado, no una lista
                    out.append(ln)
                    prev, prev_blank = ln, False
                    continue
                stack = [k]
            else:
                while len(stack) > 1 and k < stack[-1]:
                    stack.pop()
                if k > stack[-1]:
                    stack.append(k)
                elif k < stack[-1]:
                    stack[-1] = k
            if not prev_blank and not LIST_ITEM.match(prev):
                out.append("")
            s = re.sub(r"^([-*+])\s+\[ \]\s+", "\\1 ☐ ", s)
            s = re.sub(r"^([-*+])\s+\[[xX]\]\s+", "\\1 ☑ ", s)
            ln = " " * (4 * (len(stack) - 1)) + s
        elif not s:
            pass
        elif stack is not None:
            if k == 0 and (prev_blank or s.startswith(("#", "|", ">"))):
                stack = None
            elif k > 0:      # continuación: pertenece al ítem más profundo cuyo marcador está a la izquierda
                lvl = max(i for i, mk in enumerate(stack) if mk < k) if k > stack[0] else 0
                del stack[lvl + 1:]
                ln = " " * max(4 * (lvl + 1), k) + s
        out.append(ln)
        prev, prev_blank = ln, not s
    return "\n".join(out) + ("\n" if txt.endswith("\n") else "")


def render_md(txt, toc=True):
    import markdown
    from markdown.extensions.toc import slugify_unicode
    md = markdown.Markdown(extensions=MD_EXT, extension_configs={
        "toc": {"slugify": slugify_unicode, "toc_depth": "2-3", "permalink": False}})
    body = md.convert(fix_lists(txt))
    return wrap_tables(body), (md.toc if toc else ""), getattr(md, "toc_tokens", [])


# ───────────────────────────── plantilla ─────────────────────────────

NAV = [("index.html", "Inicio"), ("visor/index.html", "Visor 3D"), ("documentos.html", "Documentos"),
       ("planos.html", "Planos"), ("bom.html", "Materiales"), ("fea.html", "FEA")]


def head(page, title, description, extra=""):
    url = SITE_URL + ("" if page == "index.html" else page)
    css = rel(page, "assets/site.css")
    t, d = E(title), E(description)
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<meta name="description" content="{d}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{E(SITE_NAME)}">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{E(url)}">
<meta property="og:image" content="{SITE_URL}og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="es_ES">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{SITE_URL}og.png">
<meta name="theme-color" content="#0f242b">
<link rel="icon" href="{FAVICON}">
<link rel="canonical" href="{E(url)}">
{FONTS}
<link rel="stylesheet" href="{css}">{extra}
</head>"""


def page_html(page, title, description, body, active=None, wide=False):
    cur = ' aria-current="page"'
    nav = "".join(
        f'<a href="{rel(page, href)}"{cur if href == active else ""}>{E(lbl)}</a>' for href, lbl in NAV)
    nav += f'<a href="{REPO_URL}" class="ext">GitHub&nbsp;↗</a>'
    return f"""{head(page, title, description)}
<body>
<a class="skip" href="#main">Saltar al contenido</a>
<header class="site-header">
  <div class="bar{' wide' if wide else ''}">
    <a class="brand" href="{rel(page, 'index.html')}"><span class="mark" aria-hidden="true"></span>P1-J <b>Strålen</b></a>
    <nav class="site-nav" aria-label="Secciones">{nav}</nav>
  </div>
</header>
<main id="main" class="main{' wide' if wide else ''}">
{display_glyphs(body)}
</main>
<footer class="site-footer">
  <div class="bar{' wide' if wide else ''}">
    <span>{E(SITE_NAME)} · paquete de ingeniería abierto · todo se regenera desde <code>inputs.yaml</code></span>
    <a href="{REPO_URL}">Repositorio en GitHub ↗</a>
  </div>
</footer>
</body>
</html>
"""


def tag_chip(tag):
    t = tag.strip("[]")
    k = t.split(":")[0].split(";")[0].split(" ")[0].upper()
    cls = {"CALCULADO": "calc", "ESTIMADO": "est", "VERIFICADO": "ver", "SUPUESTO": "sup",
           "NO": "no", "PENDIENTE": "no"}.get(k, "calc")
    return f'<span class="tag {cls}">[{E(t)}]</span>'


# ───────────────────────────── páginas ─────────────────────────────

def readme_parts(srcs):
    """Del README: el ítem «Recomendación» del resumen y la lista de próximos pasos físicos."""
    txt = resolve_markers((ROOT / "README.md").read_text(encoding="utf-8"), srcs, es=True)
    rec = None
    m = re.search(r"^\d+\.\s+\*\*Recomendación:\*\*\s*(.+)$", txt, re.M)
    if m:
        rec = m.group(1).strip()
        rec = rec[:1].upper() + rec[1:]
    steps = None
    m = re.search(r"^##\s+Próximos pasos físicos[^\n]*\n(.*?)(?=^##\s|\Z)", txt, re.M | re.S)
    if m:
        steps = m.group(1).strip()
    return rec, steps


def build_index(ctx, V, srcs):
    page = "index.html"
    fea, est = srcs["fea"], srcs["est"]
    req = V.raw("sizing.verdict.plane_margin_required", 0.10)
    margin_nom = V.raw("sizing.verdict.hump_margin_min_nominal")
    hump_ok = V.raw("sizing.verdict.hump_ok")
    verify_ok = V.raw("verify.ok")
    vd = V.raw("sizing.verdict", {}) or {}
    planes_nom, planes_high = vd.get("planes_nominal_band"), vd.get("planes_high_band")
    # datos de entrada (inputs.yaml), no literales
    loa, beam = inp("boat.loa_m"), inp("boat.beam_m")
    steer = inp("waterjet.steering.max_deflection_deg")
    target_kmh = inp("operation.top_speed_target_kmh")
    legal_kn = (inp("operation.legal_speed_limit_kmh") or 0) / 1.852 or None
    env = inp("printer.envelope_mm") or []
    pilot_kg = next((it.get("kg") for it in (V.raw("sizing.masses.items") or []) if it.get("id") == "pilot"), None)
    cap_kg = V.raw("sizing.capacity.persons_gear_kg")
    ok_target = V.raw("sizing.checks.ok_vmax_target")
    s_loa, s_beam, s_steer = fnum(loa, ".2f"), fnum(beam, ".2f"), fnum(steer, ".0f")

    # FEA
    fea_rows = [(pid, p) for pid, p in (fea.get("piezas") or {}).items() if p.get("FS_min") is not None]
    fea_min = min(fea_rows, key=lambda r: r[1]["FS_min"] / (r[1].get("FS_objetivo") or 1)) if fea_rows else None
    n_fea_ok = sum(1 for _, p in fea_rows if p.get("cumple"))

    if planes_high:
        high_note, high_cls = "también planea con la estimación pesimista", ""
    elif vd.get("reaches_planing_high"):
        high_note, high_cls = "con esta estimación no llega a planeo pleno", "warn"
    else:
        high_note, high_cls = "con esta estimación no planea", "bad"
    tgt_txt = ""
    if target_kmh is not None:
        tgt_txt = f"objetivo de Jorge ≥ {fnum(target_kmh, '.0f')} km/h — {'cumple' if ok_target else 'NO cumple'} · "
    cards = [
        ("Impulsor", f"Ø{V('sizing.selection.D_imp_mm', '.0f')}", "mm",
         f"{V('manifest.params.blades', 'd')} álabes, inox, directo al motor", "[CALCULADO]", ""),
        ("Tobera", f"Ø{V('sizing.selection.D_noz_mm', '.0f')}", "mm",
         f"boquilla orientable ±{s_steer}° + bucket de reversa (la cuchara que da marcha atrás)", "[CALCULADO]", ""),
        ("V. máx. sostenida — resistencia nominal", V("sizing.verdict.vmax_cont_kmh.nominal", ".1f"), "km/h",
         f"{tgt_txt}~{V('sizing.verdict.vmax_peak_kmh.nominal', '.0f')} km/h por ratos · modelo sin validar en agua",
         "[CALCULADO]", "" if ok_target or target_kmh is None else "bad"),
        ("V. máx. sostenida — resistencia alta (pesimista)", V("sizing.verdict.vmax_cont_kmh.high", ".1f"), "km/h",
         high_note, "[CALCULADO]", high_cls),
        ("Margen para pasar a planeo (nominal)", fnum(margin_nom, ".0%"), "",
         f"empuje que sobra en la «joroba» antes de planear; objetivo ≥ {fnum(req, '.0%')} — "
         f"{'cumple' if hump_ok else 'NO cumple'}", "[CALCULADO]", "" if hump_ok else "bad"),
        ("Autonomía", V("sizing.energy.t_top_min", ".0f"), "min a fondo",
         f"{V('sizing.energy.t_legal_h', '.1f')} h a {fnum(legal_kn, '.0f')} nudos (límite legal cerca de la costa)",
         "[CALCULADO]", ""),
        ("Empuje con el bote amarrado", V("sizing.performance.bollard_N", ".0f"), "N",
         "a punto fijo («bollard pull»), a potencia pico", "[CALCULADO]", ""),
        ("Piezas en el CAD", V("manifest.totals.n_parts", "d"), "",
         "STEP + STL, sólidos válidos; las piezas a imprimir caben en la impresora"
         + (f" ({'×'.join(fnum(x, '.0f') for x in env)} mm)" if env else ""), "[VERIFICADO en software]", ""),
        ("Costo A — construir la bomba", V("bom.total_eur", ".0f"), "€",
         f"≈ {V('bom.total_dkk', '.0f')} DKK; {V('bom.verified_frac_of_subtotal', '.0%')} del subtotal con precio verificado, "
         f"servicios de taller {V('bom.services_eur', '.0f')} € sin cotizar", "[CALCULADO: bom.py; servicios ESTIMADO]", "span2"),
        ("Costo B — AWT JT132 + este tren", f"{V('cmp.B_total_eur_min', '.0f')}–{V('cmp.B_total_eur_max', '.0f')}", "€",
         "la bomba comercial de la foto con el mismo motor, controlador y batería", "[CALCULADO; precio JT132 ESTIMADO]", "good span2"),
        ("Chequeos de choque entre piezas", V("verify.n_pair_checks", "d"), "combinaciones",
         ("sin interferencias" if verify_ok else "CON FALLAS")
         + f" · pares de piezas × posiciones: boquilla −{s_steer}/0/+{s_steer}° × bucket arriba/abajo",
         "[VERIFICADO en software]", "" if verify_ok else "bad"),
    ]
    if fea_min:
        pid, p = fea_min
        cards.append(("FEA — factor de seguridad mínimo", fnum(p["FS_min"], ".2f"), "",
                      f"{pid} (objetivo {fnum(p.get('FS_objetivo'), 'g')}; FS 2 = aguanta el doble de la carga); "
                      f"{n_fea_ok} de {len(fea_rows)} piezas cumplen",
                      "[CALCULADO: FEA 04_diseno/fea]", "" if p.get("cumple") else "bad"))
    cards_html = "".join(
        f'<article class="kcard {cls}"><h3>{E(lbl)}</h3><p class="kv"><span class="num">{E(v)}</span>'
        f'{f" <small>{E(u)}</small>" if u else ""}</p><p class="kl">{nowrap_pids(E(note))}</p>{tag_chip(tag)}</article>'
        for lbl, v, u, note, tag, cls in cards)

    # Estado honesto: puntos abiertos declarados (el n.º 1 es la estabilidad: bloquea las pruebas en agua)
    items = []
    tips = cap_kg is not None and pilot_kg is not None and cap_kg < pilot_kg
    gm = V("sizing.hydrostatics.GM_m", ".3f")
    if tips:
        items.append(("bad", f"Estabilidad del casco: puede volcar (GM ≈ {gm} m)",
                      f"Con {s_beam} m de manga y el piloto sentado alto, la estabilidad (altura metacéntrica, GM) es casi "
                      f"nula. La capacidad de carga por la regla de EE. UU. 33 CFR 183.33 da "
                      f"{E(fnum(cap_kg, '.0f'))} kg, y un piloto pesa ~{E(fnum(pilot_kg, '.0f'))} kg: <b>puede volcar</b>. "
                      f"<b>Bloquea las pruebas en agua hasta resolverlo</b>: ensayo de escora con carga desplazada antes de "
                      f"motorizar; probablemente haya que ensanchar el casco o bajar el asiento."))
    else:
        items.append(("ok", f"Estabilidad del casco: GM ≈ {gm} m",
                      f"La capacidad de carga por la regla 33 CFR 183.33 da {E(fnum(cap_kg, '.0f'))} kg, más que el piloto "
                      f"(~{E(fnum(pilot_kg, '.0f'))} kg). Igual se hace el ensayo de escora antes de motorizar."))
    vmass, vlwl = V.raw("sizing.verdict.recovery_mass_text", "menos masa"), V.raw("sizing.verdict.recovery_lwl_text", "más eslora")
    vlwl = str(vlwl).replace("L_wl", "eslora mojada")
    no_motor = (V.raw("sizing.verdict.optimizer_status") == "sin_solucion_dura")
    if planes_high and hump_ok:
        p_title, p_cls = "Planeo: planea con las dos estimaciones de resistencia", "ok"
    elif planes_nom:
        p_title, p_cls = "Planeo: con la resistencia alta no llega a planeo pleno", "bad"
    else:
        p_title, p_cls = "Planeo: no llega a planeo pleno ni con la resistencia nominal", "bad"
    nom_txt = (f"Con la resistencia <b>nominal</b> {'planea' if planes_nom else 'no planea'}"
               + (f", pero con margen {E(fnum(margin_nom, '.0%'))} contra el ≥ {E(fnum(req, '.0%'))} que se pide"
                  if planes_nom and not hump_ok else "")
               + (f" (tarda {E(V('sizing.verdict.t_to_plane_nominal_s', '.0f'))} s)" if planes_nom else "") + ". ")
    high_txt = ("" if planes_high else
                f"Con la resistencia <b>alta</b> (método sin validar para un casco tan corto) se queda en "
                f"{E(V('sizing.verdict.V_eq_peak_high_kmh', '.0f'))} km/h a fondo y "
                f"{E(V('sizing.verdict.vmax_cont_kmh.high', '.0f'))} km/h con potencia continua. ")
    fix_txt = ("" if (planes_high and hump_ok) else
               ("Ninguna combinación de motor y batería &lt; 50 V cumple el objetivo: " if no_motor else "")
               + f"lo arregla el casco — <b>{E(vmass)}</b> o <b>{E(vlwl)}</b>. ")
    items.append((p_cls, p_title, nom_txt + high_txt + fix_txt
                  + f"Lo decide la prueba en el agua {E(str(V.raw('sizing.verdict.validated_by', 'T4')))}."))
    for pid_k, row in sorted((est.get("min_by_part") or {}).items()):
        if pid_k != "P1-DRV-08":
            continue
        just = next((r.get("justification") for r in est.get("rows", [])
                     if r.get("part") == pid_k and r.get("load_case") == row.get("load_case")), "")
        below = row["FS"] < row["target"]
        items.append(("bad" if below else "ok",
                      f"Chaveta del eje del motor: factor de seguridad (FS) {fnum(row['FS'], '.2f')} "
                      f"{'&lt;' if below else '≥'} {fnum(row['target'], 'g')}",
                      f"{E(row['load_case'])}. El encastre lo fija el eje del motor y no se puede alargar. "
                      f"Mitigación: <b>medir el chavetero del motor al recibirlo</b>, cubo del acople <b>de acero</b> "
                      f"y <b>Loctite 648</b> en el asiento además de la chaveta."
                      + (f'<details><summary>Justificación completa (estructural.json)</summary><p>{E(just)}</p></details>' if just else "")))
    for pid, p in fea_rows:
        if not p.get("cumple"):
            items.append(("bad", f"FEA: {pid} con FS {fnum(p['FS_min'], '.2f')} &lt; {fnum(p.get('FS_objetivo'), 'g')}",
                          f"{E(p.get('descripcion', ''))}. Caso de carga {E(str(p.get('caso_gobernante', '')))}"
                          f" de la corrida FEA del {E(str((fea.get('meta') or {}).get('fecha', '')))}; "
                          f'detalle en <a href="fea.html#{E(pid)}">Resultados FEA</a>.'))
    open_html = "".join(f'<li class="{c}"><h3>{nowrap_pids(t)}</h3><p>{nowrap_pids(d)}</p></li>' for c, t, d in items)

    rec, steps = readme_parts(srcs)
    rec_html = ""
    if rec:
        b, _, _ = render_md(rec, toc=False)
        rec_html = ctx.rewrite_links(b, "", page)
    steps_html = ""
    if steps:
        b, _, _ = render_md(steps, toc=False)
        steps_html = ctx.rewrite_links(b, "", page)

    lead = ("Un motor eléctrico dentro del bote chupa agua por el fondo y la tira con fuerza por atrás: empuja sin "
            "hélice a la vista. Esto es el diseño completo en computadora; todavía no se construyó nada.")
    qe = (f"Para el jet boat de Jorge ({s_loa} × {s_beam} m, Als Fjord, Dinamarca): toma enrasada en el fondo "
          f"<b>delante</b> del impulsor, impulsor inox de Ø{E(V('sizing.selection.D_imp_mm', '.0f'))} mm directo a un "
          f"motor refrigerado por agua, tobera de Ø{E(V('sizing.selection.D_noz_mm', '.0f'))} mm con boquilla orientable "
          f"y bucket de reversa, batería por debajo de 50 V. Acá está todo el paquete de ingeniería — cálculo, CAD de "
          f"{E(V('manifest.totals.n_parts', 'd'))} piezas, planos, materiales, FEA y plan de pruebas — regenerable desde "
          f"un solo archivo de entrada.")

    buttons = [("visor/index.html", "Visor 3D", "ensamblado, explotado y pieza por pieza", "cube"),
               ("documentos.html", "Documentos", f"{len(ctx.docs)} documentos: cálculo, diseño, pruebas", "doc"),
               ("planos.html", "Planos", "piezas mecanizadas y soldadas, acotadas", "plan"),
               ("bom.html", "Lista de materiales", "precios, proveedores y etiquetas", "list"),
               ("fea.html", "Resultados FEA", "factores de seguridad de las piezas críticas", "fea"),
               (REPO_URL, "Repositorio (GitHub)", "código, CAD STEP/STL y datos", "git")]
    btn_html = "".join(
        f'<a class="bigbtn" href="{href}"><span class="ico ico-{ico}" aria-hidden="true"></span>'
        f'<span><b>{E(t)}</b><small>{E(s)}</small></span></a>' for href, t, s, ico in buttons)

    # criterio de FS a mano y sus excepciones declaradas (estructural.json), no un «FS ≥ 2» sin matices
    man = {p["id"]: p for p in (srcs["manifest"].get("parts") or [])}
    exc = [(pid, r) for pid, r in sorted((est.get("min_by_part") or {}).items()) if r.get("FS", 9) < r.get("target", 0)]
    exc_txt = "; ".join(
        f'<span class="pid">{E(pid)}</span> {E((man.get(pid, {}).get("desc") or "").split(" (")[0])} '
        f'FS {E(fnum(r["FS"], ".2f"))}' for pid, r in exc)
    fs_txt = ("criterio de factor de seguridad (FS) ≥ 2 en metal y ≥ 3 en PETG por cálculo a mano: "
              + (f"lo cumplen todas las piezas salvo {len(exc)} excepciones declaradas ({exc_txt})" if exc
                 else "lo cumplen todas las piezas"))
    verified = (f"CAD de {E(V('manifest.totals.n_parts', 'd'))} piezas "
                + ("sin choques entre piezas" if verify_ok else "<b>con choques entre piezas sin resolver</b>")
                + f" en {E(V('verify.n_pair_checks', 'd'))} combinaciones; {fs_txt}; FEA de las {len(fea_rows)} piezas críticas "
                f"y tests automáticos.")
    fea_list = "".join(
        f'<li><a class="mono" href="fea.html#{E(pid)}">{E(pid)}</a> FS {E(fnum(p["FS_min"], ".2f"))} / '
        f'{E(fnum(p.get("FS_objetivo"), "g"))} '
        f'<span class="pill {"ok" if p.get("cumple") else "bad"}">{"cumple" if p.get("cumple") else "no cumple"}</span></li>'
        for pid, p in fea_rows)

    date = (fea.get("meta") or {}).get("fecha")
    body = f"""
<section class="hero">
  <div class="hero-text">
    <p class="eyebrow">P1-J · «Strålen» = «el chorro» en danés</p>
    <h1>Waterjet eléctrico inboard para un jet boat de {s_loa}&nbsp;m</h1>
    <p class="lead">{lead}</p>
    <p class="status-line"><span class="pill ok">Diseño completo, verificado en software</span>
      <span class="pill bad">Nada probado físicamente todavía</span></p>
    <div class="cta"><a class="btn primary" href="visor/index.html">Abrir el visor 3D</a>
      <a class="btn" href="#estado">Estado honesto</a>
      <a class="btn" href="#h-ir">Todo el proyecto ↓</a></div>
    <p class="more">{qe}</p>
  </div>
  <figure class="hero-fig">
    <a href="visor/corte_lateral.png"><img src="visor/corte_lateral.png" alt="Corte longitudinal del CAD: casco, toma con rejilla, bomba, tren y motor, con la línea de flotación calculada" width="1600" height="560"></a>
    <figcaption>Corte por crujía del CAD: toma con rejilla delante del impulsor, bomba, tren y motor. Tocá para ampliar.</figcaption>
  </figure>
</section>

<section aria-labelledby="h-num">
  <p class="eyebrow">Números clave</p>
  <h2 id="h-num">Lo que dice el modelo</h2>
  <p class="sub">Cada número sale de <code>resultados/*.json</code> al generar este sitio; la etiqueta dice de dónde viene.
  «Resistencia nominal» y «alta» son dos estimaciones de cuánto frena el agua al casco: la de referencia y una
  pesimista. La real se mide en la prueba en el agua (T4).</p>
  <div class="kgrid">{cards_html}</div>
</section>

<section id="estado" aria-labelledby="h-estado" class="honest">
  <p class="eyebrow">Estado honesto</p>
  <h2 id="h-estado">Verificado en software. Nada probado en el agua.</h2>
  <p>{verified} <b>Ninguna pieza se fabricó ni se probó todavía</b>: los modelos se calibran con las pruebas T0–T4
  (del banco de taller al agua, en <a href="{rel(page, doc_out('06_ensamblaje_y_pruebas.md'))}">06</a>).</p>
  <h3 class="h-open">Puntos abiertos declarados</h3>
  <ol class="open">{open_html}</ol>
  <details class="fea-mini"><summary>FEA de las piezas críticas</summary><ul>{fea_list}</ul>
    <p><a href="fea.html">Ver la tabla completa →</a></p></details>
</section>

<section aria-labelledby="h-rec" class="rec">
  <p class="eyebrow">Recomendación</p>
  <h2 id="h-rec">Comprar la bomba o construirla</h2>
  <div class="ab">
    <div class="opt"><h3>A — bomba propia</h3><p class="kv"><span class="num">{E(V('bom.total_eur', '.0f'))}</span> <small>€</small></p>
      <p>{E(V('cmp.A_vmax_kmh', '.1f'))} km/h sostenidos · piezas que reemplazaría la JT132: {E(V('cmp.A_jet_mass_kg', '.1f'))} kg · impulsor y estator CNC 5 ejes</p>
      <p>{tag_chip('[CALCULADO: bom.py]')}</p></div>
    <div class="opt good"><h3>B — AWT JT132 + este tren</h3><p class="kv"><span class="num">{E(V('cmp.B_total_eur_min', '.0f'))}–{E(V('cmp.B_total_eur_max', '.0f'))}</span> <small>€</small></p>
      <p>{E(V('cmp.B_vmax_kmh', '.1f'))} km/h (≈ A ± la curva de AWT, no publicada) · JT132: {E(V('cmp.B_jet_mass_kg', '.0f'))} kg con dirección y reversa</p>
      <p>{tag_chip('[CALCULADO; precio de la JT132 ESTIMADO]')} {tag_chip('[VERIFICADO: masa, R11 §4]')}</p></div>
  </div>
  <div class="prose">{rec_html}</div>
  <p><a href="{rel(page, doc_out('03_arquitectura.md'))}">Matriz de arquitectura y comparación completa →</a></p>
</section>

<section aria-labelledby="h-pasos" class="steps">
  <p class="eyebrow">Próximos pasos físicos</p>
  <h2 id="h-pasos">Los cinco primeros</h2>
  <div class="prose">{steps_html}</div>
  <p><a href="{rel(page, doc_out('PENDIENTES_GASPAR.md'))}">Todas las acciones pendientes →</a></p>
</section>

<section aria-labelledby="h-ir" class="go">
  <p class="eyebrow">Explorar</p>
  <h2 id="h-ir">Todo el proyecto</h2>
  <div class="btngrid">{btn_html}</div>
  {f'<p class="sub">Datos de la última corrida FEA: {E(str(date))}.</p>' if date else ''}
</section>
"""
    desc = (f"Waterjet eléctrico inboard para un jet boat de {s_loa} m: impulsor "
            f"Ø{V('sizing.selection.D_imp_mm', '.0f')} mm, {V('sizing.verdict.vmax_cont_kmh.nominal', '.1f')} km/h "
            f"sostenidos (modelo), {V('manifest.totals.n_parts', 'd')} piezas de CAD verificadas en software. Cálculo, "
            f"planos, BOM, FEA y visor 3D. Nada construido ni probado todavía.")
    write(ctx, page, page_html(page, SITE_TITLE, desc, body, active="index.html"))


def build_docs(ctx, srcs):
    meta = {}
    for src in ctx.docs:
        page = doc_out(src)
        raw = (ROOT / src).read_text(encoding="utf-8")
        txt = resolve_markers(raw, srcs)
        # el README apunta al visor «en la descripción del PR»: en el sitio, el visor está acá mismo
        txt = txt.replace("(link en la descripción del PR)", "([abrir el visor](04_diseno/visor/index.html))")
        title = md_title(txt, src)
        desc = md_description(txt) or title
        meta[src] = (title, desc)
        body, toc, tokens = render_md(txt)
        body = ctx.rewrite_links(body, posixpath.dirname(src), page)
        has_toc = bool(tokens) and "<li" in toc
        toc_html = ""
        if has_toc:
            toc_html = (f'<details class="toc-m"><summary>Contenido de esta página</summary>{toc}</details>'
                        f'<aside class="toc-d" aria-label="Contenido"><p class="eyebrow">Contenido</p>{toc}</aside>')
        gh = BLOB + quote(src)
        crumbs = (f'<nav class="crumbs" aria-label="Ruta"><a href="{rel(page, "documentos.html")}">Documentos</a> / '
                  f'<span class="mono">{E(src)}</span></nav>')
        html_body = f"""
<div class="doc-layout{' has-toc' if has_toc else ''}">
  <div class="doc-top">{crumbs}<a class="btn small" href="{gh}">Ver en GitHub ↗</a></div>
  {toc_html}
  <article class="prose doc">{body}</article>
</div>"""
        write(ctx, page, page_html(page, f"{title} — {SITE_NAME}", desc, html_body, active="documentos.html", wide=True))
    return meta


def build_documentos(ctx, meta):
    page = "documentos.html"
    research = [d for d in ctx.docs if d.startswith("research/")]
    groups = [(g, [d for d in ds if d in ctx.doc_set]) for g, ds in DOC_GROUPS] + [("Investigación (research/)", research)]
    out = []
    for g, ds in groups:
        if not ds:
            continue
        lis = "".join(
            f'<li><a href="{rel(page, doc_out(d))}"><b>{E(meta[d][0])}</b><span class="mono">{E(d)}</span>'
            f'<small>{E(meta[d][1])}</small></a></li>' for d in ds)
        out.append(f'<section><h2>{E(g)}</h2><ul class="doclist">{lis}</ul></section>')
    figs = sorted(p.name for p in (ROOT / "figuras").glob("*.png")) if (ROOT / "figuras").is_dir() else []
    fig_html = ""
    if figs:
        cards = []
        for f in figs:
            ctx.copy("figuras/" + f, "figuras/" + f)
            lbl = f[:-4].replace("_", " ").capitalize()
            cards.append(f'<figure><a href="figuras/{f}"><img src="figuras/{f}" alt="{E(lbl)}" loading="lazy"></a>'
                         f'<figcaption>{E(lbl)}</figcaption></figure>')
        fig_html = (f'<section><h2>Figuras del cálculo</h2><p class="sub">Generadas por <code>sizing.py</code> y '
                    f'<code>bom.py</code>; explicadas en <a href="{rel(page, doc_out("02_calculos.md"))}">02 — cálculos</a>.</p>'
                    f'<div class="figgrid">{"".join(cards)}</div></section>')
    body = f"""
<p class="eyebrow">Documentos</p>
<h1>Documentación del proyecto</h1>
<p class="sub">Los mismos archivos Markdown del repositorio, renderizados. Los números entre marcadores se regeneran desde los resultados.</p>
{''.join(out)}
{fig_html}
"""
    write(ctx, page, page_html(page, f"Documentos — {SITE_NAME}", "Índice de la documentación de P1-J Strålen: "
                               "investigación, cálculo, arquitectura, diseño, fabricación, pruebas, auditoría.",
                               body, active="documentos.html"))


def build_planos(ctx, srcs):
    page = "planos.html"
    man = {p["id"]: p for p in (srcs["manifest"].get("parts") or [])}
    svgs = sorted(p.name for p in (ROOT / "04_diseno" / "planos").glob("*.svg"))
    groups = {}
    for f in svgs:
        m = re.match(r"^(P1-([A-Z]+)-\d+)_(.+)\.svg$", f)
        pid, sub, name = (m.group(1), m.group(2), m.group(3)) if m else (f[:-4], "OTRO", f[:-4])
        groups.setdefault(sub, []).append((pid, name, f))
        ctx.copy("04_diseno/planos/" + f, "planos/" + f)
    order = list(SUBSYS) + sorted(k for k in groups if k not in SUBSYS)
    secs = []
    for sub in order:
        if sub not in groups:
            continue
        cards = []
        for pid, name, f in groups[sub]:
            p = man.get(pid, {})
            desc = p.get("desc", "")
            mat = p.get("material", "")
            cards.append(
                f'<figure class="plano"><a href="planos/{f}" aria-label="Abrir el plano {E(pid)} {E(name)}">'
                f'<img src="planos/{f}" alt="Plano {E(pid)} {E(name)}" loading="lazy"></a>'
                f'<figcaption><b class="mono">{E(pid)}</b> {E(name.replace("_", " "))}'
                f'{f"<small>{E(desc)}</small>" if desc else ""}{f"<small class=mono>{E(mat)}</small>" if mat else ""}'
                f'</figcaption></figure>')
        secs.append(f'<section><h2><span class="mono">{E(sub)}</span> {E(SUBSYS.get(sub, sub))}</h2>'
                    f'<div class="planogrid">{"".join(cards)}</div></section>')
    body = f"""
<p class="eyebrow">Planos</p>
<h1>Planos acotados</h1>
<p class="sub">{len(svgs)} planos SVG de las piezas mecanizadas, torneadas y soldadas, generados desde el CAD paramétrico
(<code>04_diseno/planos*.py</code>). Tocá un plano para abrirlo a tamaño completo. Los STEP y STL están en el
<a href="{TREE}04_diseno">repositorio ↗</a>.</p>
{''.join(secs)}
"""
    write(ctx, page, page_html(page, f"Planos — {SITE_NAME}", f"{len(svgs)} planos acotados del waterjet P1-J por subsistema: "
                               "toma, bomba, tren, motor, dirección, reversa y mandos.", body, active="planos.html", wide=True))


ALCANCE = {"casco": "casco (aparte)", "operacion": "operación (aparte)"}


def build_bom(ctx, srcs, V):
    page = "bom.html"
    b = srcs["bom"]
    with open(ROOT / "bom.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    # renglones con ID = ítems; sin ID = subtotales y totales de bom.py (van en su propia tabla, con su moneda)
    items = [r for r in rows if (r.get("ID") or "").strip()]
    totals = [r for r in rows if not (r.get("ID") or "").strip() and (r.get("descripcion") or "").strip()]
    cats, cat_scope = [], {}
    for r in items:
        if r.get("categoria") and r["categoria"] not in cats:
            cats.append(r["categoria"])
        cat_scope.setdefault(r.get("categoria", ""), (r.get("alcance") or "sistema").strip())
    L = ["ID", "Descripción", "Cant.", "EUR total", "Proveedor / link", "Etiqueta", "Fecha"]
    trs = []
    for r in items:
        link = (r.get("link_o_busqueda") or "").strip()
        if re.match(r"^https?://", link):
            dom = re.sub(r"^https?://(www\.)?", "", link).split("/")[0]
            link_html = f'<a href="{E(link)}" rel="noopener">{E(dom)}&nbsp;↗</a>'
        else:
            link_html = f'<span class="muted">{E(link)}</span>'
        spec = (r.get("especificacion_minima") or "").strip()
        ver = (r.get("verificado") or "").strip()
        try:
            tot = float(r.get("precio_total_EUR") or 0)
        except ValueError:
            tot = None
        etiqueta = (r.get("etiqueta") or "").strip()
        scope = (r.get("alcance") or "sistema").strip()
        scope_html = f' <span class="pill warn scope">{E(ALCANCE.get(scope, scope))}</span>' if scope != "sistema" else ""
        trs.append(
            f'<tr data-cat="{E(r.get("categoria", ""))}">'
            f'<td class="mono nowrap idc" data-label="{L[0]}">{E(r.get("ID", ""))}</td>'
            f'<td class="desc" data-label="{L[1]}"><b>{E(r.get("descripcion", ""))}</b>{scope_html}'
            + (f'<details><summary>especificación</summary><p>{E(spec)}</p></details>' if spec else "")
            + f'<small class="muted">{E(r.get("categoria", ""))}{" · cubre " + E(r["cubre"]) if r.get("cubre") else ""}</small></td>'
            f'<td class="num nowrap qty" data-label="{L[2]}">{E(fnum(_flt(r.get("cantidad")), "g"))} {E(r.get("unidad", ""))}</td>'
            f'<td class="num nowrap tot" data-label="{L[3]}">{E(fnum(tot, ".2f")) if tot is not None else "—"}</td>'
            f'<td class="prov" data-label="{L[4]}">{E(r.get("proveedor_envio_DK", ""))}<br>{link_html}</td>'
            f'<td class="tagcell" data-label="{L[5]}"><span class="pill {"ok" if ver.lower().startswith("s") else "warn"}">'
            f'{"verificado" if ver.lower().startswith("s") else "no verificado"}</span><small>{E(etiqueta)}</small></td>'
            f'<td class="nowrap mono fecha" data-label="{L[6]}">{E(r.get("fecha", ""))}</td></tr>')
    tot_rows = []
    for r in totals:
        d = r.get("descripcion", "")
        cur = "DKK" if re.search(r"\bDKK\b", d) else "€"
        strong = d.upper().startswith(("TOTAL", "SUBTOTAL"))
        v = _flt(r.get("precio_total_EUR"))
        val = E(fnum(v, ".2f")) if isinstance(v, float) else "—"
        tot_rows.append(f'<tr{" class=strong" if strong else ""}><td data-label="Concepto">{E(d)}</td>'
                        f'<td class="num nowrap" data-label="Importe">{val} {cur}</td></tr>')
    by_cat = sorted((b.get("by_category") or {}).items(), key=lambda kv: -kv[1])
    apart = ' <span class="pill warn">aparte, no entra en el total del sistema</span>'
    cat_rows = "".join(
        f"<tr><td>{E(k)}{apart if cat_scope.get(k, 'sistema') != 'sistema' else ''}"
        f"</td><td class='num'>{E(fnum(v, '.0f'))}</td></tr>" for k, v in by_cat if v > 0)
    opts = "".join(f'<option value="{E(c)}">{E(c)}</option>' for c in cats)
    n_items = b.get("n_rows") or len(items)
    body = f"""
<p class="eyebrow">Lista de materiales</p>
<h1>BOM — {len(items)} renglones</h1>
<div class="kgrid small">
  <article class="kcard"><h3>Total del sistema</h3><p class="kv"><span class="num">{E(V('bom.total_eur', '.0f'))}</span> <small>€</small></p>
    <p class="kl">≈ {E(V('bom.total_dkk', '.0f'))} DKK, con envío, importación e imprevistos</p>{tag_chip('[CALCULADO: bom.py]')}</article>
  <article class="kcard"><h3>Subtotal</h3><p class="kv"><span class="num">{E(V('bom.subtotal_eur', '.0f'))}</span> <small>€</small></p>
    <p class="kl">envío {E(V('bom.shipping_eur', '.0f'))} € · importación CN {E(V('bom.import_cn_eur', '.0f'))} € · imprevistos {E(V('bom.contingency_eur', '.0f'))} €</p>{tag_chip('[CALCULADO]')}</article>
  <article class="kcard"><h3>Precio verificado</h3><p class="kv"><span class="num">{E(V('bom.verified_frac_of_subtotal', '.0%'))}</span></p>
    <p class="kl">del subtotal ({E(V('bom.verified_rows', 'd'))} renglones con precio leído en la página del proveedor)</p>{tag_chip('[VERIFICADO]')}</article>
  <article class="kcard warn"><h3>Servicios de taller</h3><p class="kv"><span class="num">{E(V('bom.services_eur', '.0f'))}</span> <small>€</small></p>
    <p class="kl">CNC 5 ejes, soldadura, anodizado: a cotizar</p>{tag_chip('[ESTIMADO]')}</article>
</div>
<details class="bycat"><summary>Totales de bom.py</summary><div class="table-wrap"><table class="totals stack">
<thead><tr><th>Concepto</th><th>Importe</th></tr></thead><tbody>{''.join(tot_rows)}</tbody></table></div>
<p class="sub">Los cambios de casco (los hace Jorge) y el equipo de seguridad de operación van aparte del total del sistema.</p></details>
<details class="bycat"><summary>Por categoría (EUR, sin envío ni imprevistos)</summary><div class="table-wrap"><table><thead><tr><th>Categoría</th><th>EUR</th></tr></thead>
<tbody>{cat_rows}</tbody></table></div></details>
<div class="filters">
  <label>Buscar <input type="search" id="q" placeholder="motor, M8, Maytech…" autocomplete="off"></label>
  <label>Categoría <select id="cat"><option value="">Todas</option>{opts}</select></label>
  <span id="count" class="muted" aria-live="polite"></span>
</div>
<div class="table-wrap"><table class="bom stack" id="bom">
<thead><tr>{''.join(f'<th>{h}</th>' for h in L)}</tr></thead>
<tbody>{''.join(trs)}</tbody></table></div>
<p class="sub">Fuente: <a href="{BLOB}bom.csv">bom.csv ↗</a> (generado por <code>bom.py</code> desde <code>inputs.yaml</code>);
totales de <a href="{BLOB}resultados/bom_resumen.json">resultados/bom_resumen.json ↗</a>.</p>
<script>
(function () {{
  var q = document.getElementById("q"), c = document.getElementById("cat"), n = document.getElementById("count");
  var rows = Array.prototype.slice.call(document.querySelectorAll("#bom tbody tr"));
  function f() {{
    var t = q.value.trim().toLowerCase(), k = c.value, shown = 0;
    rows.forEach(function (r) {{
      var ok = (!k || r.getAttribute("data-cat") === k) && (!t || r.textContent.toLowerCase().indexOf(t) !== -1);
      r.hidden = !ok; if (ok) shown++;
    }});
    n.textContent = shown + " de " + rows.length + " renglones";
  }}
  q.addEventListener("input", f); c.addEventListener("change", f); f();
}})();
</script>
"""
    if n_items != len(items):
        print(f"build_site: AVISO bom.csv tiene {len(items)} renglones con ID y bom_resumen.n_rows = {n_items}")
    write(ctx, page, page_html(page, f"Lista de materiales — {SITE_NAME}",
                               f"BOM del waterjet P1-J: {len(items)} renglones, total {V('bom.total_eur', '.0f')} €, "
                               f"{V('bom.verified_frac_of_subtotal', '.0%')} del subtotal con precio verificado.",
                               body, active="bom.html", wide=True))


def _flt(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return x


def _fea_image(ctx, src_rel, max_w=960):
    """Copia (reducida a ≤ max_w px de ancho) una imagen de FEA al sitio; devuelve su ruta en el sitio."""
    from PIL import Image
    src = ROOT / src_rel
    if not src.is_file():
        return None
    dst_rel = "fea/" + src.name
    dst = ctx.out / dst_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        if im.width > max_w:
            im = im.convert("RGB").resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
            im.save(dst, "PNG", optimize=True)
        else:
            shutil.copyfile(src, dst)
    ctx.copied.add(dst_rel)
    return dst_rel


FEA_CAPTIONS = {"vm": "Tensión de von Mises", "deformada": "Deformada (exagerada)",
                "sZ": "Tracción entre capas de impresión (σZ)"}


def build_fea(ctx, srcs):
    page = "fea.html"
    fea = srcs["fea"]
    piezas = fea.get("piezas") or {}
    notes, cur = {}, None
    for h in fea.get("hallazgos") or []:
        m = re.match(r"^- \*\*(P1-[A-Z]+-\d+)\b", h)
        if m:
            cur = m.group(1)
        notes.setdefault(cur or "_", []).append(h)
    rows, secs = [], []
    for pid, p in piezas.items():
        caso = str(p.get("caso_gobernante", ""))
        cname = ((p.get("casos") or {}).get(caso) or {}).get("nombre", "")
        mat = (p.get("admisibles") or {}).get("material") or p.get("material", "")
        ok = bool(p.get("cumple"))
        rows.append(
            f'<tr><td data-label="Pieza"><a href="#{E(pid)}" class="mono nowrap">{E(pid)}</a><small>{E(p.get("descripcion", ""))}</small></td>'
            f'<td class="num nowrap" data-label="FS mín. / objetivo"><b>{E(fnum(p.get("FS_min"), ".2f"))}</b> / {E(fnum(p.get("FS_objetivo"), "g"))}</td>'
            f'<td data-label="Cumple"><span class="pill {"ok" if ok else "bad"}">{"sí" if ok else "no"}</span></td>'
            f'<td data-label="Caso gobernante"><b>{E(caso)}</b> <small>{E(cname)}</small></td>'
            f'<td data-label="Material">{E(mat)}</td></tr>')
        imgs = ""
        ims = list(p.get("imagenes") or [])
        order = {"vm": 0, "deformada": 1}
        ims.sort(key=lambda i: order.get(Path(i).stem.split("_", 1)[-1], 2))
        for i in ims:
            sp = _fea_image(ctx, i)
            if sp:
                kind = Path(i).stem.split("_", 1)[-1]
                cap = FEA_CAPTIONS.get(kind, kind)
                imgs += (f'<figure><a href="{sp}"><img src="{sp}" alt="{E(pid)}: {E(cap)}" '
                         f'loading="lazy"></a><figcaption>{E(cap)}</figcaption></figure>')
        nb = ""
        if notes.get(pid):
            b, _, _ = render_md("\n".join(notes[pid]), toc=False)
            nb = ctx.rewrite_links(b, "04_diseno/fea", page)
        secs.append(f'<section id="{E(pid)}" class="feapart"><h2><span class="mono">{E(pid)}</span> {E(p.get("descripcion", ""))}</h2>'
                    f'<p><span class="pill {"ok" if ok else "bad"}">FS {E(fnum(p.get("FS_min"), ".2f"))} '
                    f'(objetivo {E(fnum(p.get("FS_objetivo"), "g"))}) — {"cumple" if ok else "NO cumple"}</span> '
                    f'criterio {E(str(p.get("criterio_gobernante", "")))} · malla {E(str(p.get("nivel_reportado", "")))}</p>'
                    f'<div class="prose">{nb}</div><div class="figgrid">{imgs}</div></section>')
    gen = ""
    if notes.get("_"):
        b, _, _ = render_md("\n".join(notes["_"]), toc=False)
        gen = f'<section><h2>Notas generales</h2><div class="prose">{b}</div></section>'
    meta = fea.get("meta") or {}
    readme = "04_diseno/fea/README.md"
    rlink = rel(page, doc_out(readme)) if readme in ctx.doc_set else BLOB + readme
    body = f"""
<p class="eyebrow">Resultados FEA</p>
<h1>Elementos finitos de las piezas críticas</h1>
<p class="sub">{E(meta.get('metodo', ''))}. {f"Corrida del {E(str(meta['fecha']))}." if meta.get('fecha') else ''}
Método, cargas, admisibles y comparación con el cálculo a mano: <a href="{rlink}">04_diseno/fea/README</a>. {tag_chip('[CALCULADO]')}</p>
<div class="table-wrap"><table class="fea stack">
<thead><tr><th>Pieza</th><th>FS mín. / objetivo</th><th>Cumple</th><th>Caso gobernante</th><th>Material</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
{''.join(secs)}
{gen}
"""
    nok = sum(1 for p in piezas.values() if p.get("cumple"))
    write(ctx, page, page_html(page, f"Resultados FEA — {SITE_NAME}",
                               f"FEA 3D de {len(piezas)} piezas críticas del waterjet P1-J: {nok} de {len(piezas)} cumplen el FS objetivo.",
                               body, active="fea.html", wide=True))


VISOR_CSS = """<style id="p1-site">
/* agregado por build_site.py: en el teléfono la barra y los controles salen de encima del modelo 3D */
@media (max-width: 600px) {
  .p1-out.toolbar, .p1-out.controls { position: static; margin: 0; }
  .p1-out.toolbar { padding: 0 0 2px; }
}
@media (prefers-color-scheme: light) {
  :root:not([data-theme="dark"]) .tbtn.demo:not([aria-pressed="true"]) { background: #b8490b; border-color: #b8490b; color: #fff; }
}
:root[data-theme="light"] .tbtn.demo:not([aria-pressed="true"]) { background: #b8490b; border-color: #b8490b; color: #fff; }
</style>"""
VISOR_JS = """<script>
/* agregado por build_site.py: en pantallas angostas la barra va arriba del lienzo y los controles abajo */
(function () {
  var st = document.getElementById("stage"); if (!st || !window.matchMedia) return;
  var tb = st.querySelector(".toolbar"), ct = st.querySelector(".controls"), ld = document.getElementById("loading");
  var mq = window.matchMedia("(max-width: 600px)");
  function place() {
    if (mq.matches) {
      if (tb) { st.parentNode.insertBefore(tb, st); tb.classList.add("p1-out"); }
      if (ct) { st.parentNode.insertBefore(ct, st.nextSibling); ct.classList.add("p1-out"); }
    } else {
      if (tb) { tb.classList.remove("p1-out"); st.insertBefore(tb, ld ? ld.nextSibling : st.firstChild); }
      if (ct) { ct.classList.remove("p1-out"); st.appendChild(ct); }
    }
    window.dispatchEvent(new Event("resize"));
  }
  place();
  if (mq.addEventListener) mq.addEventListener("change", place); else if (mq.addListener) mq.addListener(place);
})();
</script>"""


def _site_image(ctx, src_rel, dst_rel, max_w):
    """Copia una imagen al sitio, reducida a ≤ max_w px de ancho (PNG optimizado; paleta si sigue pesada)."""
    from PIL import Image
    src, dst = ROOT / src_rel, ctx.out / dst_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        if im.width <= max_w and src.stat().st_size < 400_000:
            shutil.copyfile(src, dst)
        else:
            im = im.convert("RGB")
            if im.width > max_w:
                im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
            im.save(dst, "PNG", optimize=True)
            if dst.stat().st_size > 400_000:
                im.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(dst, "PNG", optimize=True)
    ctx.copied.add(dst_rel)


def build_visor(ctx):
    vdir = ROOT / "04_diseno" / "visor"
    for f in VISOR_FILES:
        if (vdir / f).exists() and f != "index.html":
            if f == "plano_waterjet_jorge.png":
                _site_image(ctx, f"04_diseno/visor/{f}", f"visor/{f}", 1000)
            else:
                ctx.copy(f"04_diseno/visor/{f}", f"visor/{f}")
    src = (vdir / "index.html").read_text(encoding="utf-8")
    # el visor saluda a Jorge; el título de la pestaña y del enlace compartido es el del sitio
    src = src.replace("<h1>Hola Jorge!", "<h1>¡Hola Jorge!")
    page = "visor/index.html"
    if not src.lstrip().lower().startswith("<!doctype"):
        # El visor es un fragmento (sin <html>/<head>): se le antepone una cabecera con charset, viewport,
        # Open Graph y favicon; su propio <title> y <style> quedan tal cual dentro del <head>.
        h = head(page, "Visor 3D — " + SITE_NAME, "Visor 3D del waterjet P1-J: ensamblado, explotado, pieza por pieza "
                 "y demo de dirección y reversa.")
        h = h.replace("</head>", "")
        src = re.sub(r"<title>.*?</title>\n?", "", src, count=1)
        h = h.replace(FONTS + "\n", "")
        h = re.sub(r'<link rel="stylesheet" href="[^"]*site\.css">', "", h)
        src = h + "\n" + src
    back = ('<a href="../index.html" class="p1-home" style="justify-self:start;margin-bottom:-14px;'
            'font:600 14px/1 var(--font-body,system-ui,sans-serif);background:var(--ink,#0f242b);color:var(--bg,#eef2f1);'
            'padding:10px 14px;border-radius:999px;text-decoration:none">← Inicio · P1-J</a>')
    src, n = re.subn(r'(<div class="wrap">)', lambda m: back + "\n" + m.group(1), src, count=1)
    if not n:
        src += "\n" + back
    src = src.replace("</style>", "</style>\n" + VISOR_CSS, 1) if "</style>" in src else VISOR_CSS + "\n" + src
    write(ctx, page, src.rstrip("\n") + "\n" + VISOR_JS + "\n")


# ───────────────────────────── og.png, css ─────────────────────────────

def _font(size, bold=True):
    from PIL import ImageFont
    names = (["LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf", "FreeSansBold.ttf"] if bold
             else ["LiberationSans-Regular.ttf", "DejaVuSans.ttf", "FreeSans.ttf"])
    dirs = [Path("/usr/share/fonts/truetype/liberation"), Path("/usr/share/fonts/truetype/dejavu"),
            Path("/usr/share/fonts/truetype/freefont"), Path("/Library/Fonts"), Path("C:/Windows/Fonts")]
    for n in names:
        for d in dirs:
            if (d / n).exists():
                return ImageFont.truetype(str(d / n), size)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def build_og(ctx, V):
    from PIL import Image, ImageDraw
    W, H = 1200, 630
    ink, paper, accent, sea = (15, 36, 43), (238, 242, 241), (226, 96, 26), (79, 176, 194)
    im = Image.new("RGB", (W, H), ink)
    d = ImageDraw.Draw(im)
    src = ROOT / "04_diseno" / "visor" / "corte_lateral.png"
    if src.exists():
        with Image.open(src) as c:
            c = c.convert("RGB")
            tw = W - 80
            th = round(c.height * tw / c.width)
            if th > 330:
                th, tw = 330, round(c.width * 330 / c.height)
            c = c.resize((tw, th), Image.LANCZOS)
            panel = Image.new("RGB", (W - 48, th + 24), (255, 255, 255))
            im.paste(panel, (24, H - th - 48))
            im.paste(c, ((W - tw) // 2, H - th - 36))
    d.rectangle([0, 0, W, 10], fill=accent)
    d.text((48, 40), "P1-J · STRÅLEN", font=_font(30), fill=sea)
    d.text((48, 82), "Waterjet eléctrico inboard", font=_font(60), fill=paper)
    d.text((48, 150), "para un jet boat de 2,30 m", font=_font(44, bold=False), fill=paper)
    sub = (f"Ø{V('sizing.selection.D_imp_mm', '.0f')} mm · {V('sizing.verdict.vmax_cont_kmh.nominal', '.1f')} km/h (modelo) · "
           f"{V('manifest.totals.n_parts', 'd')} piezas · verificado en software")
    d.text((48, 206), sub, font=_font(26, bold=False), fill=(147, 167, 171))
    dst = ctx.out / "og.png"
    im.save(dst, "PNG", optimize=True)
    if dst.stat().st_size > 300_000:
        im.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(dst, "PNG", optimize=True)


CSS = r"""/* P1-J · sitio — tokens del visor 3D (04_diseno/visor/index.html) */
:root {
  --bg: #eef2f1; --surface: #ffffff; --ink: #0f242b; --muted: #4f6166; --line: #cfd9d8;
  --accent: #c4510f; --accent-bg: #b8490b; --accent-ink: #ffffff; --sea: #17687a; --ok: #23753f; --warn: #8f5d12; --bad: #b0302a;
  --ok-bg: #e3f1e7; --warn-bg: #f8eedb; --bad-bg: #f8e3e0; --sea-bg: #e0eef0;
  --font-display: "Big Shoulders Display", "Arial Narrow", "Helvetica Neue", Arial, sans-serif;
  --font-body: "Public Sans", "Segoe UI", Helvetica, Arial, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
  --radius: 10px; --gutter: 16px;
  /* cabecera y bloques de código: oscuros en los dos temas (no se invierten con --ink) */
  --chrome: #0f242b; --chrome-ink: #eef2f1; --chrome-accent: #ff7a33;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #0b181d; --surface: #11232a; --ink: #e4eded; --muted: #9db0b4; --line: #22383f;
    --accent: #ff8a4c; --accent-bg: #ff7a33; --accent-ink: #1a0c04; --sea: #5fbccd; --ok: #67cc88; --warn: #e8b259; --bad: #f27a6b;
    --ok-bg: #12301f; --warn-bg: #33270f; --bad-bg: #3a1714; --sea-bg: #0f2c33; --chrome: #071216; color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #0b181d; --surface: #11232a; --ink: #e4eded; --muted: #9db0b4; --line: #22383f;
  --accent: #ff8a4c; --accent-bg: #ff7a33; --accent-ink: #1a0c04; --sea: #5fbccd; --ok: #67cc88; --warn: #e8b259; --bad: #f27a6b;
  --ok-bg: #12301f; --warn-bg: #33270f; --bad-bg: #3a1714; --sea-bg: #0f2c33; --chrome: #071216; color-scheme: dark;
}
@media (min-width: 720px) { :root { --gutter: 28px; } }
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; background: var(--bg); color: var(--ink); font-family: var(--font-body); font-size: 16px; line-height: 1.6; overflow-x: hidden; }
img, svg { max-width: 100%; height: auto; }
a { color: var(--sea); text-underline-offset: 2px; }
a:hover { color: var(--accent); }
:focus-visible { outline: 3px solid var(--accent-bg); outline-offset: 2px; }
code, .mono { font-family: var(--font-mono); font-size: 0.86em; }
code, pre, kbd, .mono, .eyebrow, .tag { font-variant-ligatures: none; font-feature-settings: "liga" 0, "calt" 0; }
.dia { font-family: var(--font-body); font-weight: 700; }
.pid { white-space: nowrap; }
code { background: color-mix(in srgb, var(--line) 45%, transparent); padding: 0.1em 0.3em; border-radius: 4px; overflow-wrap: anywhere; }
h1, h2, h3 { font-family: var(--font-display); line-height: 1.05; text-wrap: balance; margin: 0 0 0.4em; }
h1 { font-size: clamp(2.1rem, 8vw, 3.8rem); font-weight: 900; letter-spacing: -0.005em; }
h2 { font-size: clamp(1.7rem, 5.5vw, 2.5rem); font-weight: 800; }
h3 { font-size: 1.3rem; font-weight: 800; }
.skip { position: absolute; left: -999px; top: 0; background: var(--ink); color: var(--bg); padding: 8px 12px; z-index: 10; }
.skip:focus { left: 8px; }
.eyebrow { font-family: var(--font-mono); font-size: 0.8125rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--sea); margin: 0 0 6px; }
.sub { color: var(--muted); max-width: 72ch; }
.muted { color: var(--muted); }
.nowrap { white-space: nowrap; }

/* cabecera y pie */
.bar { max-width: 1120px; margin: 0 auto; padding: 0 var(--gutter); }
.bar.wide, .main.wide { max-width: 1320px; }
.site-header { background: var(--chrome); color: var(--chrome-ink); position: sticky; top: 0; z-index: 20; }
.site-header .bar { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 16px; padding-block: 8px; }
.brand { color: var(--chrome-ink); text-decoration: none; font-family: var(--font-display); font-size: 1.35rem; font-weight: 800; letter-spacing: 0.02em; display: inline-flex; align-items: center; gap: 8px; }
.brand b { color: var(--chrome-accent); }
.brand:hover { color: var(--chrome-ink); }
.mark { width: 14px; height: 14px; border-radius: 50%; background: var(--chrome-accent); box-shadow: 0 0 0 3px color-mix(in srgb, var(--chrome-accent) 35%, transparent); }
.site-nav { display: flex; flex-wrap: wrap; gap: 2px 4px; margin-left: auto; }
.site-nav a { color: var(--chrome-ink); text-decoration: none; font-size: 0.9rem; font-weight: 600; padding: 6px 8px; border-radius: 6px; }
.site-nav a:hover, .site-nav a[aria-current="page"] { background: color-mix(in srgb, var(--chrome-ink) 16%, transparent); color: var(--chrome-ink); }
.site-nav a.ext { opacity: 0.85; }
@media (max-width: 600px) {
  .site-header { position: static; }
  .site-nav { margin-left: 0; width: calc(100% + 2 * var(--gutter)); margin-inline: calc(-1 * var(--gutter)); padding-inline: calc(var(--gutter) - 8px);
    flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; -webkit-mask-image: linear-gradient(90deg, #000 88%, transparent); mask-image: linear-gradient(90deg, #000 88%, transparent); }
  .site-nav::-webkit-scrollbar { display: none; }
  .site-nav a { flex: none; min-height: 44px; display: inline-flex; align-items: center; padding: 0 10px; font-size: 0.9rem; }
  .site-header .bar { padding-block: 6px 2px; }
}
.main { max-width: 1120px; margin: 0 auto; padding: 24px var(--gutter) 56px; min-width: 0; }
.main > * { min-width: 0; }
.main > * + section, .main > section + * { margin-top: 44px; }
.main > p:first-child { margin-top: 0; }
.site-footer { border-top: 1px solid var(--line); color: var(--muted); font-size: 0.875rem; }
.site-footer .bar { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px 20px; padding-block: 18px 28px; }

/* botones y pastillas */
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 11px 18px; border-radius: 999px; border: 1.5px solid var(--ink); color: var(--ink); text-decoration: none; font-weight: 700; min-height: 44px; }
.btn.primary { background: var(--accent-bg); border-color: var(--accent-bg); color: var(--accent-ink); }
.btn.primary:hover { color: var(--accent-ink); filter: brightness(1.05); }
.btn.small { padding: 6px 12px; min-height: 36px; font-size: 0.875rem; }
.pill { display: inline-block; font-size: 0.8125rem; font-weight: 700; padding: 3px 10px; border-radius: 999px; background: var(--sea-bg); color: var(--sea); }
.pill.ok { background: var(--ok-bg); color: var(--ok); }
.pill.warn { background: var(--warn-bg); color: var(--warn); }
.pill.bad { background: var(--bad-bg); color: var(--bad); }
.tag { display: inline-block; font-family: var(--font-mono); font-size: 0.72rem; letter-spacing: 0.02em; padding: 2px 7px; border-radius: 5px; border: 1px solid currentColor; color: var(--sea); overflow-wrap: anywhere; }
.tag.est, .tag.sup { color: var(--warn); }
.tag.ver { color: var(--ok); }
.tag.no { color: var(--bad); }

/* portada */
.hero { display: grid; gap: 22px; align-items: center; }
.hero .lead { font-size: 1.12rem; max-width: 60ch; margin: 0 0 14px; }
.hero .more { color: var(--muted); font-size: 0.95rem; max-width: 70ch; margin: 18px 0 0; }
.status-line { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 16px; }
.cta { display: flex; flex-wrap: wrap; gap: 10px; }
.hero-fig { margin: 0; background: #fff; border: 1px solid var(--line); border-radius: var(--radius); padding: 10px; }
.hero-fig > a { display: block; }
.hero-fig figcaption { font-size: 0.8125rem; color: #4f6166; margin-top: 6px; }
@media (min-width: 980px) { .hero { grid-template-columns: 1.05fr 1fr; } }
.kgrid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 240px), 1fr)); gap: 12px; margin-top: 16px; }
@media (max-width: 639px) {
  .kgrid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
  .kgrid .kcard { padding: 12px; }
  .kgrid .span2 { grid-column: span 2; }
  .kgrid { grid-auto-flow: row dense; }
  .kv .num { font-size: 2rem; }
  .kl { font-size: 0.84rem; }
}
.kgrid.small { grid-template-columns: repeat(auto-fill, minmax(min(100%, 220px), 1fr)); }
.kcard { background: var(--surface); border: 1px solid var(--line); border-top: 4px solid var(--sea); border-radius: var(--radius); padding: 14px 16px; display: grid; gap: 6px; align-content: start; }
.kcard.warn { border-top-color: var(--warn); }
.kcard.bad { border-top-color: var(--bad); }
.kcard.good { border-top-color: var(--ok); }
.kcard h3 { font-family: var(--font-body); font-size: 0.875rem; font-weight: 700; color: var(--muted); margin: 0; text-transform: none; }
.kv { margin: 0; line-height: 1; }
.kv .num { font-family: var(--font-display); font-size: 2.6rem; font-weight: 800; }
.kv small { font-size: 0.95rem; color: var(--muted); font-weight: 600; }
.kl { margin: 0; font-size: 0.9rem; color: var(--muted); }
.kcard .tag { justify-self: start; }
.honest { background: var(--surface); border: 1px solid var(--line); border-left: 6px solid var(--bad); border-radius: var(--radius); padding: 20px 18px; }
.honest > p { max-width: 75ch; }
.h-open { margin-top: 18px; }
ol.open { list-style: none; margin: 0; padding: 0; display: grid; gap: 12px; counter-reset: o; }
ol.open li { counter-increment: o; position: relative; padding: 12px 14px 12px 50px; border-radius: 8px; background: var(--bad-bg); }
ol.open li.ok { background: var(--ok-bg); }
ol.open li::before { content: counter(o, lower-alpha); position: absolute; left: 14px; top: 11px; width: 26px; height: 26px; border-radius: 50%; background: var(--bad); color: #fff; font-weight: 800; display: grid; place-items: center; font-size: 0.9rem; }
ol.open li.ok::before { background: var(--ok); }
ol.open h3 { font-family: var(--font-body); font-size: 1.02rem; font-weight: 800; margin: 0 0 4px; line-height: 1.3; }
ol.open p { margin: 0; }
ol.open details { margin-top: 6px; font-size: 0.9rem; }
.fea-mini { margin-top: 16px; }
.fea-mini ul { padding-left: 18px; }
summary { cursor: pointer; font-weight: 700; color: var(--sea); min-height: 32px; }
.ab { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr)); gap: 12px; margin: 10px 0 14px; }
.opt { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); padding: 14px 16px; }
.opt.good { border: 2px solid var(--ok); }
.opt h3 { font-size: 1.25rem; }
.opt p { margin: 6px 0 0; }
.btngrid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 300px), 1fr)); gap: 12px; margin-top: 12px; }
.bigbtn { display: flex; align-items: center; gap: 14px; padding: 16px 18px; min-height: 76px; background: var(--surface); border: 1.5px solid var(--line); border-radius: 14px; text-decoration: none; color: var(--ink); }
.bigbtn:hover { border-color: var(--accent-bg); color: var(--ink); }
.bigbtn b { display: block; font-family: var(--font-display); font-size: 1.45rem; font-weight: 800; line-height: 1.1; }
.bigbtn small { color: var(--muted); font-size: 0.875rem; }
.ico { flex: 0 0 42px; height: 42px; border-radius: 10px; background: var(--accent-bg); position: relative; }
.ico::after { content: ""; position: absolute; inset: 11px; border: 3px solid var(--accent-ink); border-radius: 3px; }
.ico-doc::after { inset: 10px 13px; border-radius: 2px; }
.ico-plan { background: var(--sea); } .ico-plan::after { border-style: dashed; }
.ico-list::after { border-left: 0; border-right: 0; }
.ico-fea { background: var(--ok); } .ico-fea::after { border-radius: 50%; }
.ico-git { background: var(--ink); } .ico-git::after { border-color: var(--bg); border-radius: 50%; }

/* documentos */
.doclist { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 320px), 1fr)); gap: 10px; }
.doclist a { display: grid; gap: 3px; height: 100%; padding: 12px 14px; background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); text-decoration: none; color: var(--ink); }
.doclist a:hover { border-color: var(--accent-bg); }
.doclist b { font-size: 1.02rem; line-height: 1.3; }
.doclist .mono { color: var(--sea); font-size: 0.78rem; }
.doclist small { color: var(--muted); font-size: 0.875rem; line-height: 1.45; }
.figgrid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 320px), 1fr)); gap: 12px; }
.figgrid figure { margin: 0; background: #fff; border: 1px solid var(--line); border-radius: var(--radius); padding: 8px; }
.figgrid figcaption { font-size: 0.8125rem; color: #4f6166; }

/* página de documento */
.doc-layout { display: grid; gap: 16px; min-width: 0; }
.doc-top { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px; }
.crumbs { font-size: 0.875rem; color: var(--muted); overflow-wrap: anywhere; }
.toc-m { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); padding: 8px 14px; }
.toc-d { display: none; }
.toc-m ul, .toc-d ul { list-style: none; padding-left: 12px; margin: 4px 0; font-size: 0.9rem; }
.toc-m > div > ul, .toc-d > div > ul { padding-left: 0; }
.toc-m li, .toc-d li { margin: 3px 0; line-height: 1.35; }
.toc-m a, .toc-d a { text-decoration: none; overflow-wrap: anywhere; }
.prose h1, .prose h2, .prose h3, .prose h4 { overflow-wrap: anywhere; }
@media (min-width: 1040px) {
  .doc-layout.has-toc { grid-template-columns: 260px minmax(0, 1fr); grid-template-areas: "top top" "toc doc"; align-items: start; }
  .doc-layout.has-toc .doc-top { grid-area: top; }
  .doc-layout.has-toc .toc-m { display: none; }
  .doc-layout.has-toc .toc-d { display: block; grid-area: toc; position: sticky; top: 64px; max-height: calc(100vh - 80px); overflow: auto; padding-right: 8px; }
  .doc-layout.has-toc .doc { grid-area: doc; }
}
.prose { min-width: 0; overflow-wrap: break-word; }
.prose.doc { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); padding: 18px 16px; }
@media (min-width: 720px) { .prose.doc { padding: 28px 34px; } }
.prose p, .prose li { max-width: 80ch; }
.prose h1 { font-size: clamp(1.9rem, 6.5vw, 3rem); }
.prose h2 { margin-top: 1.4em; padding-top: 0.3em; border-top: 1px solid var(--line); }
.prose h3 { margin-top: 1.2em; }
.prose h2, .prose h3, .prose h4 { scroll-margin-top: 72px; }
.prose blockquote { margin: 1em 0; padding: 4px 16px; border-left: 4px solid var(--sea); background: var(--sea-bg); border-radius: 0 8px 8px 0; }
.prose pre { overflow-x: auto; background: var(--chrome); color: var(--chrome-ink); padding: 12px 14px; border-radius: 8px; font-size: 0.85rem; line-height: 1.5; }
.prose pre code { background: none; padding: 0; color: inherit; overflow-wrap: normal; }
.prose img { display: block; margin: 12px 0; background: #fff; border-radius: 6px; }
.prose a { overflow-wrap: anywhere; }
.prose hr { border: 0; border-top: 1px solid var(--line); margin: 2em 0; }

/* tablas: el desplazamiento horizontal queda dentro del contenedor, nunca en la página */
.table-wrap { width: 100%; max-width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 12px 0; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); }
.table-wrap table { border-collapse: collapse; width: 100%; font-size: 0.9rem; }
.table-wrap th, .table-wrap td { padding: 7px 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; min-width: 7ch; }
.prose .table-wrap td, .prose .table-wrap th { min-width: 9ch; max-width: 46ch; }
.table-wrap td:first-child, .table-wrap th:first-child { min-width: 0; }
.table-wrap th { background: color-mix(in srgb, var(--line) 40%, var(--surface)); font-weight: 700; position: sticky; top: 0; }
.table-wrap tbody tr:last-child td { border-bottom: 0; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
td small { display: block; color: var(--muted); font-size: 0.8125rem; }

/* BOM / FEA / planos */
.filters { display: flex; flex-wrap: wrap; gap: 10px 16px; align-items: end; }
.filters label { display: grid; gap: 4px; font-size: 0.875rem; font-weight: 700; flex: 1 1 200px; }
.filters input, .filters select { font: inherit; font-size: 16px; padding: 9px 10px; border: 1.5px solid var(--line); border-radius: 8px; background: var(--surface); color: var(--ink); width: 100%; }
table.bom td.desc { min-width: 28ch; max-width: 52ch; }
table.bom td.tagcell { min-width: 22ch; max-width: 40ch; }
table.bom details summary { font-size: 0.8125rem; min-height: 0; }
table.bom details p { font-size: 0.8125rem; margin: 4px 0; }
.bycat { max-width: 640px; }
.bycat + .bycat { margin-top: 8px; }
table.totals tr.strong td { font-weight: 800; }
.desc .scope { margin-left: 6px; font-size: 0.75rem; padding: 1px 8px; }
/* teléfono: las tablas anchas (BOM, FEA, totales) pasan a tarjetas, una fila por tarjeta */
@media (max-width: 640px) {
  table.stack thead { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
  table.stack, table.stack tbody, table.stack tr, table.stack td { display: block; width: 100%; }
  table.stack tr { padding: 8px 12px; border-bottom: 1px solid var(--line); }
  table.stack tr[hidden] { display: none; }
  table.stack tbody tr:last-child { border-bottom: 0; }
  table.stack td { display: grid; grid-template-columns: 7.5em minmax(0, 1fr); gap: 8px; padding: 3px 0; border: 0; min-width: 0; max-width: none; text-align: left; white-space: normal; }
  table.stack td::before { content: attr(data-label); font-size: 0.78rem; font-weight: 700; color: var(--muted); padding-top: 2px; }
  table.stack td > * { grid-column: 2; }
  table.stack td.num { text-align: left; }
  /* BOM: tarjeta compacta — ID y precio arriba, descripción, cantidad + verificación, proveedor */
  table.bom tr { display: grid; grid-template-columns: minmax(0, 1fr) auto; grid-auto-flow: row dense; gap: 2px 12px; padding: 10px 12px; }
  table.bom tr[hidden] { display: none; }
  table.bom td { display: block; padding: 0; min-width: 0; max-width: none; }
  table.bom td::before { content: none; }
  table.bom td.idc { grid-column: 1; font-weight: 700; color: var(--sea); }
  table.bom td.tot { grid-column: 2; grid-row: 1; text-align: right; font-weight: 800; }
  table.bom td.tot::after { content: " €"; }
  table.bom td.desc { grid-column: 1 / -1; }
  table.bom td.qty { grid-column: 1; text-align: left; color: var(--muted); font-size: 0.85rem; }
  table.bom td.tagcell { grid-column: 2; text-align: right; }
  table.bom td.tagcell small, table.bom td.fecha { display: none; }
  table.bom td.prov { grid-column: 1 / -1; font-size: 0.85rem; color: var(--muted); }
  table.bom td.prov br { display: none; }
  table.bom td.prov a { margin-left: 6px; }
  table.bom td.desc details p { max-width: none; }
}
.feapart { border-top: 2px solid var(--ink); padding-top: 14px; }
.feapart h2 { font-size: clamp(1.4rem, 4.5vw, 2rem); }
.feapart .prose ul { padding-left: 18px; }
.planogrid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 340px), 1fr)); gap: 12px; }
.plano { margin: 0; background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); overflow: hidden; }
.plano > a { display: block; background: #fff; padding: 6px; }
.plano img { display: block; width: 100%; aspect-ratio: 1400 / 620; object-fit: contain; }
.plano figcaption { padding: 8px 12px 12px; display: grid; gap: 2px; }
.plano figcaption small { color: var(--muted); font-size: 0.8125rem; }
section > h2 .mono, .feapart h2 .mono { color: var(--sea); font-size: 0.7em; margin-right: 6px; }
@media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto !important; } }
@media print { .site-header, .site-footer, .toc-m, .toc-d { display: none; } body { background: #fff; } }
"""


# ───────────────────────────── frescura de las fuentes ─────────────────────────────

def _part_notes():
    """PART_NOTES de 04_diseno/fea/fea_run.py, leído con ast (sin importar el módulo de FEA)."""
    import ast
    fp = ROOT / "04_diseno" / "fea" / "fea_run.py"
    if not fp.exists():
        return {}
    for node in ast.parse(fp.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "PART_NOTES" for t in node.targets):
            try:
                return ast.literal_eval(node.value)
            except ValueError:
                return {}
    return {}


def freshness(srcs):
    """Contradicciones entre lo que se copia tal cual al sitio y resultados/*.json (por contenido, no por fechas):
    devuelve la lista de problemas. Un sitio con problemas no se debe publicar: correr run_all.py completo."""
    probs = []
    V = Values(srcs)
    dp = ROOT / "04_diseno" / "visor" / "datos.json"
    if dp.exists():
        res = (json.loads(dp.read_text(encoding="utf-8")).get("resumen") or {})
        for key, path, tol in (("vmax_kmh", "sizing.performance.vmax_cont_kmh", 0.01),
                               ("masa_total_kg", "sizing.masses.total_kg", 0.05),
                               ("masa_jet_kg", "manifest.totals.jet_unit_mass_kg", 0.05),
                               ("costo_eur", "bom.total_eur", 0.5),
                               ("n_piezas", "manifest.totals.n_parts", 0)):
            a, b = res.get(key), V.raw(path)
            if isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) > tol:
                probs.append(f"visor/datos.json desactualizado: resumen.{key} = {a:g} y {path} = {b:g} "
                             f"(correr 04_diseno/visor/build_visor.py)")
    notes = _part_notes()
    heads = {}
    for h in (srcs["fea"].get("hallazgos") or []):
        m = re.match(r"^- \*\*(P1-[A-Z]+-\d+)\b", h)
        if m:
            heads[m.group(1)] = h
    for pid in (srcs["fea"].get("piezas") or {}):
        note = notes.get(pid)
        if note and pid in heads and note not in heads[pid]:
            probs.append(f"resultados_fea.json: los hallazgos de {pid} no tienen la nota actual de fea_run.py "
                         f"(PART_NOTES): corrida FEA anterior al último cambio del diseño")
    return probs


def staleness_warnings(srcs):
    """Avisos que no bloquean (dependen de fechas de archivo o solo afectan la vista del repo en GitHub)."""
    out = []
    fr, fs = ROOT / "04_diseno" / "fea" / "resultados_fea.json", ROOT / "04_diseno" / "fea" / "fea_run.py"
    if fr.exists() and fs.exists() and fr.stat().st_mtime + 1 < fs.stat().st_mtime:
        out.append("resultados_fea.json es más viejo que fea_run.py")
    blocks = srcs.get("_auto") or {}
    for md in sorted(list(ROOT.glob("*.md")) + list((ROOT / "04_diseno").rglob("*.md"))):
        old = [m.group(2) for m in PAT_AUTO.finditer(md.read_text(encoding="utf-8"))
               if m.group(2) in blocks and m.group(3).strip() != blocks[m.group(2)].strip()]
        if old:
            out.append(f"{md.relative_to(ROOT)}: {len(old)} bloque(s) AUTO desactualizados en el .md ({', '.join(old)}); "
                       f"falta docgen.py (el sitio ya usa los valores actuales)")
    return out


# ───────────────────────────── principal ─────────────────────────────

def write(ctx, rel_path, text):
    p = ctx.out / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def clean_out(out):
    out = out.resolve()
    if out in (ROOT, Path(out.anchor)) or out in ROOT.parents:
        raise SystemExit(f"build_site: carpeta de salida peligrosa: {out}")
    if out.exists():
        children = list(out.iterdir())
        if children and not ((out / ".nojekyll").exists() or (out / "index.html").exists()):
            raise SystemExit(f"build_site: {out} no está vacía y no parece un sitio generado; no se borra")
        for c in children:
            if c.is_dir() and not c.is_symlink():
                shutil.rmtree(c)
            else:
                c.unlink()
    out.mkdir(parents=True, exist_ok=True)
    return out


def build(out):
    out = clean_out(Path(out))
    ctx = Ctx(out)
    srcs = sources()
    V = Values(srcs)
    for w in staleness_warnings(srcs):
        print("build_site: aviso:", w)
    probs = freshness(srcs)
    for pr in probs:
        print("build_site: *** FUENTE DESACTUALIZADA ***", pr)
    write(ctx, ".nojekyll", "")
    write(ctx, "assets/site.css", CSS)
    build_visor(ctx)
    meta = build_docs(ctx, srcs)
    build_documentos(ctx, meta)
    build_index(ctx, V, srcs)
    build_planos(ctx, srcs)
    build_bom(ctx, srcs, V)
    build_fea(ctx, srcs)
    build_og(ctx, V)
    n_html = sum(1 for _ in out.rglob("*.html"))
    size = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    print(f"build_site: {n_html} páginas HTML, {size / 1e6:.1f} MB en {out}")
    if probs:
        print(f"build_site: *** {len(probs)} problema(s) de frescura: NO publicar este sitio; correr run_all.py completo ***")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=str(ROOT / "docs"), help="carpeta de salida (se regenera desde cero)")
    a = ap.parse_args(argv)
    build(a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
