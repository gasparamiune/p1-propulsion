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
SITE_TITLE_FMT = "P1-J · Strålen — waterjet eléctrico inboard para un jet boat de {loa} m"
OG_VERSION = ""     # hash corto de og.png (lo fija build_og): WhatsApp guarda la vista previa por URL de imagen
STALE_BANNER = ""   # aviso rojo en las páginas cuando se compila con --allow-stale y hay fuentes desactualizadas
OG_ALT = "P1-J Strålen: waterjet eléctrico inboard, diseño en computadora, nada construido ni probado todavía"

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
    srcs = docgen.sources()
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
        if not fmt and es and isinstance(v, float):
            return str(v).replace(".", ",")
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
        if name not in blocks:
            return m.group(0)
        return f"{m.group(1)}\n{es_decimals_md(blocks[name]) if es else blocks[name]}\n{m.group(4)}"

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


def es_decimals_md(t):
    """Coma decimal en un bloque AUTO (Markdown) para que coincida con los valores V del mismo documento: «27.1» →
    «27,1». No toca `código`, enlaces/rutas, secciones («§3.2»), versiones ni números de material EN («1.4404»)."""
    parts = re.split(r"(`[^`]*`|\]\([^)]*\))", t)
    rx = re.compile(r"(?<![\w.§/])(?!1\.4\d{3}\b)(\d+)\.(\d+)(?![\w./])")
    return "".join(x if i % 2 else rx.sub(r"\1,\2", x) for i, x in enumerate(parts))


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


META_PARA = re.compile(r"^(Fecha|Consulta|Autor|Autora|Estado|Versión|Fuente|Fuentes|Etiquetas|Convenciones|"
                       r"Las tablas entre|Todo se regenera)\b|run_all\.py", re.I)
# descripción (og:description y la ficha de documentos.html) escrita a mano cuando el primer párrafo no sirve
DOC_DESCRIPTIONS = {
    "04_diseno/README.md": "Diseño CAD del waterjet P1-J: lista de piezas, verificación de interferencias y "
                           "exportes STEP/STL.",
}


def short_desc(d, n=180):
    return d if len(d) <= n else d[: n - 1].rsplit(" ", 1)[0].rstrip(" ,;:—-") + "…"


def short_title(t, n=70):
    """Título para <title>/og:title: hasta el primer « (» o «: » (si queda algo con sentido), y ≤ n caracteres
    cortando en un espacio. El H1 completo queda en el cuerpo de la página."""
    for sep in (" (", ": "):
        i = t.find(sep)
        if i >= 12:
            t = t[:i]
    t = t.strip(" —-:")
    return t if len(t) <= n else t[: n - 1].rsplit(" ", 1)[0].rstrip(" ,;:—-") + "…"


def md_description(txt, n=180):
    """Primer párrafo de texto después del título (sin tablas, código ni encabezados); se saltean los párrafos
    de metadatos («Fecha: …», «Consulta: …», «Autor: …») y los muy cortos."""
    paras, para, in_code = [], [], False

    def flush():
        if para:
            raw = " ".join(para)
            # párrafos sobre el propio archivo (marcadores <!-- … -->, convenciones del generador): no sirven de resumen
            paras.append("" if "<!--" in raw else plain(raw))
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
PID = re.compile(r"\bP1-(?:[A-Z]{2,4}-\d{2}|J)\b")


def _text_nodes(h, fn):
    """Aplica fn al texto (no a las etiquetas ni atributos, ni a <script>/<style>) de un fragmento HTML."""
    parts = re.split(r"(<(script|style)\b.*?</\2>)", h, flags=re.S)
    out = []
    for i in range(0, len(parts), 3):
        out.append(re.sub(r"(^|>)([^<]+)", lambda t: t.group(1) + fn(t.group(2)), parts[i]))
        if i + 1 < len(parts):
            out.append(parts[i + 1])
    return "".join(out)


def display_glyphs(h):
    """En la fuente display (Big Shoulders) la «Ø» es igual a un cero tachado: «Ø132» se lee «0132». Dentro de
    h1–h3 y de los números grandes (.num) la «Ø» va en la fuente del texto (span.dia)."""
    fix = lambda m: _text_nodes(m.group(0), lambda t: t.replace("Ø", DIA))
    h = re.sub(r"<(h[1-3])\b[^>]*>.*?</\1>", fix, h, flags=re.S)
    return re.sub(r'<span class="num">[^<]*</span>', fix, h)


def nowrap_pids(h):
    """Los códigos de pieza (P1-STE-01) y del proyecto (P1-J) no se cortan en el guion (lo aplica page_html a
    todo el cuerpo de cada página)."""
    return _text_nodes(h, lambda t: PID.sub(lambda m: f'<span class="pid">{m.group(0)}</span>', t))


def _short_first_col(t, n=16):
    """¿La primera columna de la tabla HTML `t` es corta (IDs, códigos)? Entonces no se corta en el teléfono."""
    cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip()
             for c in re.findall(r"<tr[^>]*>\s*<t[dh][^>]*>(.*?)</t[dh]>", t, re.S)]
    return bool(cells) and max(len(c) for c in cells) <= n


def wrap_tables(h):
    def one(m):
        t, attrs = m.group(0), m.group(1) or ""
        if _short_first_col(t) and "class=" not in attrs:
            t = t.replace("<table" + attrs + ">", f'<table{attrs} class="idcol">', 1)
        return f'<div class="table-wrap">{t}</div>'
    return re.sub(r"<table(\s[^>]*)?>.*?</table>", one, h, flags=re.S)


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
            elif posixpath.splitext(target)[1].lower() in IMG_EXT and (ROOT / target).is_file():
                # la imagen (o el enlace a ella) va a la copia dentro del sitio, no a GitHub
                if target.startswith("figuras/") or target.startswith("04_diseno/planos/"):
                    site_path = ("figuras/" if target.startswith("figuras/") else "planos/") + posixpath.basename(target)
                else:
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
    sublistas a 4 espacios por nivel (GitHub acepta 2 o 3); (3) casillas «- [ ]» / «- [x]» → ☐ / ☑; (4) línea en blanco
    cuando una lista cambia de numerada a viñetas (o al revés) en el mismo nivel.
    No toca los bloques ``` ."""
    out, stack, prev, prev_blank, fence, kinds, prev_lvl = [], None, "", True, False, {}, None
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
            # (4) cambio de tipo (numerada ↔ viñetas) en el mismo nivel: python-markdown lo funde en el ítem anterior;
            # una línea en blanco abre una lista nueva
            lvl_i, kind = len(stack) - 1, ("ol" if m.group(2)[0].isdigit() else "ul")
            for j in [j for j in kinds if j > lvl_i]:
                del kinds[j]
            if not prev_blank and ((kinds.get(lvl_i) not in (None, kind)) or (prev_lvl is not None and lvl_i < prev_lvl)):
                out.append("")          # también al volver de una sublista: si no, python-markdown la funde
            kinds[lvl_i] = kind
            prev_lvl = lvl_i
            s = re.sub(r"^([-*+])\s+\[ \]\s+", "\\1 ☐ ", s)
            s = re.sub(r"^([-*+])\s+\[[xX]\]\s+", "\\1 ☑ ", s)
            ln = " " * (4 * (len(stack) - 1)) + s
        elif not s:
            pass
        elif stack is not None:
            if k == 0 and (prev_blank or s.startswith(("#", "|", ">"))):
                stack, kinds, prev_lvl = None, {}, None
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

# (destino, etiqueta, etiqueta corta en el teléfono; None = no se muestra en el teléfono: la marca ya va a Inicio)
NAV = [("index.html", "Inicio", None), ("visor/index.html", "Visor 3D", "Visor 3D"),
       ("documentos.html", "Documentos", "Docs"), ("planos.html", "Planos", "Planos"), ("bom.html", "Materiales", "BOM"),
       ("fea.html", "FEA", "FEA")]


def head(page, title, description, extra=""):
    url = SITE_URL + ("" if page == "index.html" else page)
    css = rel(page, "assets/site.css")
    t, d = E(title), E(description)
    og_img = SITE_URL + "og.png" + (f"?v={OG_VERSION}" if OG_VERSION else "")
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
<meta property="og:image" content="{og_img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{E(OG_ALT)}">
<meta property="og:locale" content="es_ES">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{og_img}">
<meta name="theme-color" content="#0f242b">
<link rel="icon" href="{FAVICON}">
<link rel="canonical" href="{E(url)}">
{FONTS}
<link rel="stylesheet" href="{css}">{extra}
</head>"""


def page_html(page, title, description, body, active=None, wide=False):
    cur = ' aria-current="page"'
    def lab(lbl, short):
        if short is None or short == lbl:
            return E(lbl)
        return f'<span class="l-long">{E(lbl)}</span><span class="l-short" aria-hidden="true">{E(short)}</span>'
    nav = "".join(
        f'<a href="{rel(page, href)}"{cur if href == active else ""}{" class=nav-home" if short is None else ""}>'
        f'{lab(lbl, short)}</a>' for href, lbl, short in NAV)
    nav += f'<a href="{REPO_URL}" class="ext">GitHub<span class="l-long">&nbsp;↗</span></a>'
    return f"""{head(page, title, description)}
<body>
<a class="skip" href="#main">Saltar al contenido</a>
<header class="site-header" id="top">
  <div class="bar{' wide' if wide else ''}">
    <a class="brand" href="{rel(page, 'index.html')}"><span class="mark" aria-hidden="true"></span>P1-J <b>Strålen</b></a>
    <nav class="site-nav" aria-label="Secciones">{nav}</nav>
  </div>
</header>
{STALE_BANNER}
<main id="main" class="main{' wide' if wide else ''}">
{display_glyphs(nowrap_pids(body))}
</main>
<a class="totop" href="#top" aria-label="Volver arriba" title="Volver arriba">↑</a>
<footer class="site-footer">
  <div class="bar{' wide' if wide else ''}">
    <span>{E(SITE_NAME)} · paquete de ingeniería abierto · todo se regenera desde <code>inputs.yaml</code></span>
    <a href="{REPO_URL}">Repositorio en GitHub ↗</a>
  </div>
</footer>
<script>(function () {{
  var n = document.querySelector(".site-nav"); if (!n) return;
  function f() {{ n.classList.toggle("at-end", n.scrollLeft + n.clientWidth >= n.scrollWidth - 4); }}
  n.addEventListener("scroll", f, {{ passive: true }}); window.addEventListener("resize", f); f();
}})();
(function () {{
  var b = document.querySelector(".totop"); if (!b) return;
  function g() {{ b.classList.toggle("show", window.scrollY > 2 * window.innerHeight); }}
  window.addEventListener("scroll", g, {{ passive: true }}); g();
}})();</script>
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
    txt = site_rewrites("README.md", resolve_markers((ROOT / "README.md").read_text(encoding="utf-8"), srcs, es=True), srcs)
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


COTA = re.compile(r"^(P1-[A-Z]+-\d+): cota crítica '(.+?)(?: \[([^\]]+)\])?' = (-?[\d.]+) \(ref ([<>]=?) (-?[\d.]+)\)")
CLASH = re.compile(r"^interferencia (P1-[A-Z]+-\d+)(?:#\d+)? ↔ (P1-[A-Z]+-\d+)(?:#\d+)?")


def verify_summary(srcs):
    """verify.json → (pares de piezas que chocan [(a, b, n)], otras fallas [(tipo, texto)], n.º de fallas de choque).
    Las fallas que no son choques (p. ej. una cota crítica fuera de tolerancia) se listan aparte."""
    pairs, other, n_clash = {}, [], 0
    for f in (srcs.get("verify") or {}).get("fails") or []:
        f = str(f)
        m = CLASH.match(f)
        if m:
            n_clash += 1
            k = tuple(sorted((m.group(1), m.group(2))))
            pairs[k] = pairs.get(k, 0) + 1
            continue
        m = COTA.match(f)
        if m:
            pid, what, unit, val, op, ref = m.groups()
            u = f" {unit}" if unit else ""
            op = {">=": "≥", "<=": "≤"}.get(op, op)
            other.append(("cota", f"{pid} {what}: {fnum(float(val), '.1f')}{u}, se pide {op} {fnum(float(ref), 'g')}{u}"))
        else:
            other.append(("otra", f))
    return [(a, b, n) for (a, b), n in pairs.items()], other, n_clash


def verify_phrase(srcs, html_out=True):
    """«24 choques entre piezas (P1-REV-04 ↔ P1-REV-09, …) y 1 cota crítica fuera de tolerancia (…)», desde los datos."""
    pairs, other, n_clash = verify_summary(srcs)
    parts = []
    if n_clash:
        pl = " y ".join(f"{a} ↔ {b}" for a, b, _ in pairs)
        parts.append(f"choques entre {pl} ({n_clash} caso{'s' if n_clash != 1 else ''} entre posiciones de boquilla y "
                     f"bucket)")
    cotas = [t for k, t in other if k == "cota"]
    otras = [t for k, t in other if k != "cota"]
    if cotas:
        parts.append(f"{len(cotas)} cota{'s' if len(cotas) != 1 else ''} crítica{'s' if len(cotas) != 1 else ''} "
                     f"fuera de tolerancia ({'; '.join(cotas)})")
    if otras:
        parts.append(f"{len(otras)} falla{'s' if len(otras) != 1 else ''} más ({'; '.join(otras)})")
    txt = " y ".join(parts) if len(parts) <= 2 else ", ".join(parts[:-1]) + " y " + parts[-1]
    return E(txt) if html_out else txt


def open_failures(srcs):
    """Fallas abiertas del CAD y del FEA: pares que chocan + otras fallas de verify.json + piezas FEA que no cumplen."""
    pairs, other, _ = verify_summary(srcs)
    fea_bad = [pid for pid, p in ((srcs.get("fea") or {}).get("piezas") or {}).items()
               if p.get("FS_min") is not None and not p.get("cumple")]
    return len(pairs) + len(other) + len(fea_bad)


def all_checks_ok(srcs):
    """verify.json sin fallas y todas las piezas FEA cumplen (lo que un documento puede llamar «verificado»)."""
    return bool((srcs.get("verify") or {}).get("ok")) and open_failures(srcs) == 0


def mc_runs():
    """N.º de juegos de pesos del Monte Carlo de la matriz de arquitectura (de resultados/arquitectura_tabla.md)."""
    fp = docgen.RES / "arquitectura_tabla.md"
    m = re.search(r"Monte Carlo \((\d+) juegos", fp.read_text(encoding="utf-8")) if fp.exists() else None
    return int(m.group(1)) if m else None


def fs_exception_note(est, pid):
    """«(fusible intencional: …)» si la justificación de la pieza en estructural.json dice que es un fusible."""
    for r in est.get("rows", []):
        if r.get("part") == pid and str(r.get("justification") or "").lower().startswith("fusible"):
            return " (fusible intencional: se rompe a propósito ante un golpe y se cambia cada temporada)"
    return ""


def status_items(V, srcs, page="index.html"):
    """Puntos abiertos de la portada [(clase, título, texto HTML)]: estabilidad, planeo, verificación del CAD,
    chaveta del motor y piezas FEA que no cumplen. Los que tienen clase «bad» son los «puntos abiertos» que se
    cuentan en la pastilla de la portada y en og.png."""
    fea, est = srcs["fea"], srcs["est"]
    req = V.raw("sizing.verdict.plane_margin_required", 0.10)
    margin_nom = V.raw("sizing.verdict.hump_margin_min_nominal")
    hump_ok = V.raw("sizing.verdict.hump_ok")
    verify_ok = V.raw("verify.ok")
    vd = V.raw("sizing.verdict", {}) or {}
    planes_nom, planes_high = vd.get("planes_nominal_band"), vd.get("planes_high_band")
    beam = inp("boat.beam_m")
    pilot_kg = next((it.get("kg") for it in (V.raw("sizing.masses.items") or []) if it.get("id") == "pilot"), None)
    cap_kg = V.raw("sizing.capacity.persons_gear_kg")
    v_pairs, v_other, _ = verify_summary(srcs)
    fea_rows = [(pid, p) for pid, p in (fea.get("piezas") or {}).items() if p.get("FS_min") is not None]

    items = []
    tips = cap_kg is not None and pilot_kg is not None and cap_kg < pilot_kg
    gm = V("sizing.hydrostatics.GM_m", ".3f")
    if tips:
        items.append(("bad", f"Estabilidad del casco: puede volcar (GM ≈ {gm} m)",
                      f"Con {fnum(beam, '.2f')} m de manga y el piloto sentado alto, la estabilidad (altura metacéntrica, "
                      f"GM) es casi nula. La capacidad de carga por la regla de EE. UU. 33 CFR 183.33 da "
                      f"{E(fnum(cap_kg, '.0f'))} kg, y un piloto pesa ~{E(fnum(pilot_kg, '.0f'))} kg: <b>puede volcar</b>. "
                      f"<b>Bloquea las pruebas en agua hasta resolverlo</b>: ensayo de escora con carga desplazada antes de "
                      f"motorizar; probablemente haya que ensanchar el casco o bajar el asiento."))
    else:
        items.append(("ok", f"Estabilidad del casco: GM ≈ {gm} m",
                      f"La capacidad de carga por la regla 33 CFR 183.33 da {E(fnum(cap_kg, '.0f'))} kg, más que el piloto "
                      f"(~{E(fnum(pilot_kg, '.0f'))} kg). Igual se hace el ensayo de escora antes de motorizar."))
    vmass, vlwl = V.raw("sizing.verdict.recovery_mass_text", "menos masa"), V.raw("sizing.verdict.recovery_lwl_text", "más eslora")
    vlwl = str(vlwl).replace("L_wl", "eslora mojada (largo del casco en el agua)")
    no_motor = (V.raw("sizing.verdict.optimizer_status") == "sin_solucion_dura")
    target_kmh = inp("operation.top_speed_target_kmh")
    ok_target = V.raw("sizing.checks.ok_vmax_target")
    if planes_high and hump_ok:
        p_title, p_cls = "Planeo: planea con las dos estimaciones de resistencia", "ok"
    elif planes_nom:
        p_title, p_cls = "Planeo: justo con la resistencia nominal, no llega con la alta", "bad"
    else:
        p_title, p_cls = "Planeo: no llega a planeo pleno ni con la resistencia nominal", "bad"
    if target_kmh is not None and not ok_target:
        p_title += f"; no llega a los {fnum(target_kmh, '.0f')} km/h que pide Jorge"
    t_nom, t_max = vd.get("t_to_plane_nominal_s"), V.raw("sizing.success.t_plane_max_s")
    t_nom = t_nom if isinstance(t_nom, (int, float)) and t_nom < 1e6 else None
    v_full, full_cont = vd.get("V_full_planing_kmh"), vd.get("sustains_full_planing_cont_nominal")
    if planes_nom:
        nom_txt = ("Con la resistencia <b>nominal</b> (la de referencia), a fondo llega a planear"
                   + (f", pero justo: le sobra {E(fnum(margin_nom, '.0%'))} de empuje contra el ≥ {E(fnum(req, '.0%'))} que "
                      f"se pide" if not hump_ok else "")
                   + (f"; tarda {E(fnum(t_nom, '.0f'))} s" if t_nom is not None else "")
                   + (f" (se pide ≤ {E(fnum(t_max, 'g'))} s)" if t_nom is not None and t_max and t_nom > t_max else "")
                   + ". "
                   + (f"Con potencia continua no se sostiene en planeo pleno: "
                      f"{E(V('sizing.verdict.vmax_cont_kmh.nominal', '.1f'))} km/h contra "
                      f"{E(fnum(v_full, '.0f'))} km/h que hacen falta. " if full_cont is False and v_full else ""))
    else:
        nom_txt = "Con la resistencia <b>nominal</b> (la de referencia) no llega a planear. "
    high_txt = ("" if planes_high else
                f"Con la resistencia <b>alta</b> (pesimista; método sin validar para un casco tan corto) se queda en "
                f"{E(V('sizing.verdict.V_eq_peak_high_kmh', '.0f'))} km/h a fondo y "
                f"{E(V('sizing.verdict.vmax_cont_kmh.high', '.0f'))} km/h con potencia continua, sin planear. ")
    fix_txt = ("" if (planes_high and hump_ok) else
               ("Ninguna combinación de motor y batería &lt; 50 V cumple el objetivo: " if no_motor else "")
               + f"lo arregla el casco — <b>{E(vmass)}</b> o <b>{E(vlwl)}</b>. ")
    items.append((p_cls, p_title, nom_txt + high_txt + fix_txt
                  + f"Lo decide la prueba en el agua {E(str(V.raw('sizing.verdict.validated_by', 'T4')))}."))
    if not verify_ok:
        n_cota = sum(1 for k, _ in v_other if k == "cota")
        bits = ([f"{len(v_pairs)} par{'es' if len(v_pairs) != 1 else ''} de piezas que chocan"] if v_pairs else []) \
            + ([f"{n_cota} cota{'s' if n_cota != 1 else ''} crítica{'s' if n_cota != 1 else ''} fuera de tolerancia"] if n_cota else []) \
            + ([f"{len(v_other) - n_cota} falla{'s' if len(v_other) - n_cota != 1 else ''} más"] if len(v_other) > n_cota else [])
        items.append(("bad", "Verificación del CAD: " + " y ".join(bits or ["con fallas"]),
                      f"La verificación automática del modelo 3D (<code>verify_parts.py</code>) da {verify_phrase(srcs)}. "
                      f"Hay que corregir esas piezas en el CAD y volver a verificar <b>antes de fabricar</b>. Detalle en "
                      f'<a href="{rel(page, doc_out("04_diseno/README.md"))}">04_diseno — Verificación</a>.'))
    for pid_k, row in sorted((est.get("min_by_part") or {}).items()):
        if pid_k != "P1-DRV-08":
            continue
        just = next((r.get("justification") for r in est.get("rows", [])
                     if r.get("part") == pid_k and r.get("load_case") == row.get("load_case")), "")
        below = row["FS"] < row["target"]
        items.append(("bad" if below else "ok",
                      f"Chaveta del eje del motor: factor de seguridad (FS) {fnum(row['FS'], '.2f')} "
                      f"{'&lt;' if below else '≥'} {fnum(row['target'], 'g')}",
                      f"La chaveta (la pieza que traba el eje del motor con el acople de la bomba) puede deformarse con el "
                      f"par máximo del motor. El largo lo fija el eje del motor y no se puede alargar. "
                      f"Mitigación: <b>medir el chavetero del motor al recibirlo</b>, cubo del acople <b>de acero</b> "
                      f"y <b>Loctite 648</b> en el asiento además de la chaveta."
                      f'<details><summary>Detalle técnico (estructural.json)</summary><p>Caso de carga: {E(row["load_case"])}.'
                      + (f" {E(just)}" if just else "") + "</p></details>"))
    for pid, p in fea_rows:
        if not p.get("cumple"):
            items.append(("bad", f"FEA: {pid} con FS {fnum(p['FS_min'], '.2f')} &lt; {fnum(p.get('FS_objetivo'), 'g')}",
                          f"{E(p.get('descripcion', ''))}. Caso de carga {E(str(p.get('caso_gobernante', '')))}"
                          f" de la corrida FEA del {E(str((fea.get('meta') or {}).get('fecha', '')))}; "
                          f'detalle en <a href="{rel(page, "fea.html")}#{E(pid)}">Resultados FEA</a>.'))
    return items


def open_points(V, srcs):
    """N.º de puntos abiertos (clase «bad») de status_items: lo que cuenta la pastilla de la portada y og.png."""
    return sum(1 for c, _, _ in status_items(V, srcs) if c == "bad")


def open_points_phrase(n):
    return f"{n} punto{'s' if n != 1 else ''} abierto{'s' if n != 1 else ''}"


def speed_phrase(V):
    """«24,4 km/h (modelo; objetivo 30, no cumple)» para og:description y og.png."""
    tgt, ok = inp("operation.top_speed_target_kmh"), V.raw("sizing.checks.ok_vmax_target")
    s = f"{V('sizing.verdict.vmax_cont_kmh.nominal', '.1f')} km/h (modelo"
    if tgt is not None:
        s += f"; objetivo {fnum(tgt, '.0f')}, {'cumple' if ok else 'no cumple'}"
    return s + ")"


def index_description(V, srcs, n_open=None):
    """og:description de la portada (WhatsApp muestra ~2 líneas: la advertencia va primero; ≤ 200 caracteres)."""
    n_open = open_points(V, srcs) if n_open is None else n_open
    loa = fnum(inp("boat.loa_m"), ".2f")
    head_ = (f"Diseño (aún sin construir ni probar) de un waterjet eléctrico inboard para un jet boat de {loa} m: "
             f"Ø{V('sizing.selection.D_imp_mm', '.0f')} mm, {speed_phrase(V)}, {V('manifest.totals.n_parts', 'd')} piezas CAD"
             + (f", {open_points_phrase(n_open)}" if n_open else "") + ".")
    for tail in (" Visor 3D, planos, BOM y FEA.", " Visor 3D y planos.", ""):
        if len(head_ + tail) <= 200:
            return head_ + tail
    return head_[:199].rsplit(" ", 1)[0] + "…"


_SVG = '<svg viewBox="0 0 24 24" width="24" height="24" focusable="false">{}</svg>'
ICONS = {   # íconos de los accesos de la portada (trazo con currentColor)
    "cube": _SVG.format('<path d="M12 2.5 3.5 7v10l8.5 4.5 8.5-4.5V7z"/><path d="M3.5 7 12 11.5 20.5 7M12 11.5v10"/>'),
    "doc": _SVG.format('<path d="M6 2.5h8.5l4.5 4.5v14.5H6z"/><path d="M14 2.5V7.5h5M9 12.5h7M9 16.5h7"/>'),
    "plan": _SVG.format('<rect x="2.5" y="8" width="19" height="8" rx="1"/><path d="M6.5 8v3M10.5 8v4.5M14.5 8v3M18.5 8v4.5"/>'),
    "list": _SVG.format('<path d="M9 6h12M9 12h12M9 18h12"/><path d="M4 6h.5M4 12h.5M4 18h.5" stroke-width="3"/>'),
    "fea": _SVG.format('<path d="M3.5 18a8.5 8.5 0 1 1 17 0"/><path d="M12 18l4.5-6.5M6.5 13.5l1.2.7M12 8.5v1.4M17.5 13.5l-1.2.7"/>'),
    "git": _SVG.format('<circle cx="6" cy="5" r="2"/><circle cx="6" cy="19" r="2"/><circle cx="18" cy="7" r="2"/>'
                       '<path d="M6 7v10M18 9c0 5-12 3-12 8"/>'),
}


def build_index(ctx, V, srcs):
    page = "index.html"
    fea, est = srcs["fea"], srcs["est"]
    req = V.raw("sizing.verdict.plane_margin_required", 0.10)
    margin_nom = V.raw("sizing.verdict.hump_margin_min_nominal")
    hump_ok = V.raw("sizing.verdict.hump_ok")
    verify_ok = V.raw("verify.ok")
    vd = V.raw("sizing.verdict", {}) or {}
    planes_high = vd.get("planes_high_band")
    # datos de entrada (inputs.yaml), no literales
    loa, beam = inp("boat.loa_m"), inp("boat.beam_m")
    steer = inp("waterjet.steering.max_deflection_deg")
    target_kmh = inp("operation.top_speed_target_kmh")
    legal_kn = (inp("operation.legal_speed_limit_kmh") or 0) / 1.852 or None
    env = inp("printer.envelope_mm") or []
    ok_target = V.raw("sizing.checks.ok_vmax_target")
    s_loa, s_beam, s_steer = fnum(loa, ".2f"), fnum(beam, ".2f"), fnum(steer, ".0f")
    v_pairs, v_other, n_clash = verify_summary(srcs)
    items = status_items(V, srcs, page)
    n_open = sum(1 for c, _, _ in items if c == "bad")
    all_ok = all_checks_ok(srcs) and n_open == 0

    # FEA
    fea_rows = [(pid, p) for pid, p in (fea.get("piezas") or {}).items() if p.get("FS_min") is not None]
    fea_min = min(fea_rows, key=lambda r: r[1]["FS_min"] / (r[1].get("FS_objetivo") or 1)) if fea_rows else None
    n_fea_ok = sum(1 for _, p in fea_rows if p.get("cumple"))

    v_plane = vd.get("V_planing_start_kmh")
    if planes_high:
        high_note, high_cls = "también planea con la estimación pesimista", ""
    elif vd.get("sustains_planing_cont_high") is False:
        high_note, high_cls = (
            "con potencia continua se cae del planeo"
            + (f" (empieza a planear a {fnum(v_plane, '.0f')} km/h)" if v_plane else "")
            + f"; a fondo llega a {V('sizing.verdict.V_eq_peak_high_kmh', '.0f')} km/h "
            + ("sin planeo pleno" if vd.get("reaches_planing_high") else "sin planear"), "bad")
    elif vd.get("reaches_planing_high"):
        high_note, high_cls = "con esta estimación no llega a planeo pleno", "warn"
    else:
        high_note, high_cls = "con esta estimación no planea", "bad"
    b_planes, b_margin = V.raw("cmp.B_planes"), V.raw("cmp.B_hump_margin")
    b_plane_note = ("" if b_planes or b_planes is None else
                    f"; con la resistencia alta tampoco planea (margen {fnum(b_margin, '.0%')}, "
                    f"A: {fnum(V.raw('cmp.A_hump_margin'), '.0%')})").replace("-", "−")
    tgt_txt = ""
    if target_kmh is not None:
        tgt_txt = f"objetivo de Jorge ≥ {fnum(target_kmh, '.0f')} km/h — {'cumple' if ok_target else 'NO cumple'} · "
    if verify_ok:
        chk = ("Chequeos de choque entre piezas", V("verify.n_pair_checks", "d"), "combinaciones",
               f"sin interferencias · pares de piezas × posiciones: boquilla −{s_steer}/0/+{s_steer}° × bucket arriba/abajo",
               "[VERIFICADO en software]", "")
    else:
        n_cota = sum(1 for k, _ in v_other if k == "cota")
        bits = ([f"{len(v_pairs)} par{'es' if len(v_pairs) != 1 else ''} de piezas que chocan ({n_clash} caso{'s' if n_clash != 1 else ''})"]
                if v_pairs else []) \
            + ([f"{n_cota} cota{'s' if n_cota != 1 else ''} crítica{'s' if n_cota != 1 else ''} fuera de tolerancia"] if n_cota else []) \
            + ([f"{len(v_other) - n_cota} falla{'s' if len(v_other) - n_cota != 1 else ''} más"] if len(v_other) > n_cota else [])
        n_vf = len(v_pairs) + len(v_other)
        chk = ("Verificación del CAD (choques entre piezas y cotas)", str(n_vf),
               "falla abierta" if n_vf == 1 else "fallas abiertas",
               " y ".join(bits) + f", en {V('verify.n_pair_checks', 'd')} combinaciones revisadas"
               f" (boquilla −{s_steer}/0/+{s_steer}° × bucket arriba/abajo) · detalle en «Estado honesto»",
               "[CALCULADO: verify_parts.py; fallas abiertas]", "bad span2")
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
         "la bomba comercial de la foto con el mismo tren eléctrico (motor, controlador y batería)" + b_plane_note,
         "[CALCULADO; precio JT132 ESTIMADO]", "good span2"),
        chk,
    ]
    if fea_min:
        pid, p = fea_min
        cards.append(("FEA (simulación de tensiones) — factor de seguridad mínimo", fnum(p["FS_min"], ".2f"), "",
                      f"{pid} (objetivo {fnum(p.get('FS_objetivo'), 'g')}; FS 2 = aguanta el doble de la carga); "
                      f"{n_fea_ok} de {len(fea_rows)} piezas cumplen",
                      "[CALCULADO: FEA 04_diseno/fea]", "" if p.get("cumple") else "bad span2"))
    cards_html = "".join(
        f'<article class="kcard {cls}"><h3>{E(lbl)}</h3><p class="kv"><span class="num">{E(v)}</span>'
        f'{f" <small>{E(u)}</small>" if u else ""}</p><p class="kl">{E(note)}</p>{tag_chip(tag)}</article>'
        for lbl, v, u, note, tag, cls in cards)

    # Estado honesto: puntos abiertos declarados (el n.º 1 es la estabilidad: bloquea las pruebas en agua)
    open_html = "".join(f'<li class="{c}"><h3>{t}</h3><p>{d}</p></li>' for c, t, d in items)

    rec, steps = readme_parts(srcs)
    rec_html = ""
    if rec:
        # el README dice «el resto son servicios de taller a cotizar»: no es así (servicios ≈ 39 %, el resto ESTIMADO)
        sv, sub = V.raw("bom.services_eur"), V.raw("bom.subtotal_eur")
        if isinstance(sv, (int, float)) and isinstance(sub, (int, float)) and sub > 0:
            rec = re.sub(r";\s*el resto son servicios de taller a cotizar",
                         f"; servicios de taller {fnum(sv, '.0f')} € ({fnum(sv / sub, '.0%')}) y el resto con precio "
                         f"ESTIMADO, todo a cotizar", rec)
        n_mc = mc_runs()
        rec = re.sub(r"\bdel Monte Carlo\b", f"de {fnum(n_mc, '.0f') if n_mc else 'miles de'} sorteos con pesos al azar "
                     f"(Monte Carlo)", rec)
        b, _, _ = render_md(rec, toc=False)
        rec_html = ctx.rewrite_links(b, "", page)
    steps_html = ""
    if steps:
        b, _, _ = render_md(steps, toc=False)
        steps_html = ctx.rewrite_links(b, "", page)

    lead = ("Un motor eléctrico dentro del bote chupa agua por el fondo y la tira con fuerza por atrás: empuja sin "
            "hélice a la vista. Esto es el diseño " + ("completo en computadora" if all_ok else "en computadora, en revisión")
            + "; todavía no se construyó nada.")
    qe = (f"Para el jet boat de Jorge ({s_loa} × {s_beam} m, Als Fjord, Dinamarca): toma enrasada (al ras del fondo) "
          f"<b>delante</b> del impulsor, impulsor inox de Ø{E(V('sizing.selection.D_imp_mm', '.0f'))} mm directo a un "
          f"motor refrigerado por agua, tobera de Ø{E(V('sizing.selection.D_noz_mm', '.0f'))} mm con boquilla orientable "
          f"y bucket de reversa, batería por debajo de 50 V. Acá está todo el paquete de ingeniería — cálculo, modelo 3D (CAD) de "
          f"{E(V('manifest.totals.n_parts', 'd'))} piezas, planos, materiales, FEA y plan de pruebas — regenerable desde "
          f"un solo archivo de entrada.")

    buttons = [("visor/index.html", "Visor 3D", "ensamblado, explotado y pieza por pieza", "cube"),
               ("documentos.html", "Documentos", f"{len(ctx.docs)} documentos: cálculo, diseño, pruebas", "doc"),
               ("planos.html", "Planos", "piezas mecanizadas y soldadas, acotadas", "plan"),
               ("bom.html", "Lista de materiales", "precios, proveedores y etiquetas", "list"),
               ("fea.html", "Resultados FEA", "factores de seguridad de las piezas críticas", "fea"),
               (REPO_URL, "Repositorio (GitHub)", "código, CAD STEP/STL y datos", "git")]
    btn_html = "".join(
        f'<a class="bigbtn" href="{href}"><span class="ico ico-{ico}" aria-hidden="true">{ICONS[ico]}</span>'
        f'<span><b>{E(t)}</b><small>{E(s)}</small></span></a>' for href, t, s, ico in buttons)

    # criterio de FS a mano y sus excepciones declaradas (estructural.json), no un «FS ≥ 2» sin matices
    man = {p["id"]: p for p in (srcs["manifest"].get("parts") or [])}
    exc = [(pid, r) for pid, r in sorted((est.get("min_by_part") or {}).items()) if r.get("FS", 9) < r.get("target", 0)]
    exc_txt = "; ".join(
        f'{E(pid)} {E((man.get(pid, {}).get("desc") or "").split(" (")[0])} '
        f'FS {E(fnum(r["FS"], ".2f"))}{E(fs_exception_note(est, pid))}' for pid, r in exc)
    fs_txt = ("criterio de factor de seguridad (FS) ≥ 2 en metal y ≥ 3 en PETG por cálculo a mano: "
              + (f"lo cumplen todas las piezas salvo {len(exc)} excepciones declaradas ({exc_txt})" if exc
                 else "lo cumplen todas las piezas"))
    n_fea_bad = len(fea_rows) - n_fea_ok
    verified = (f"Modelo 3D (CAD) de {E(V('manifest.totals.n_parts', 'd'))} piezas "
                + ("sin choques entre piezas" if verify_ok else f"<b>con fallas de verificación sin resolver: {verify_phrase(srcs)}</b>")
                + f" en {E(V('verify.n_pair_checks', 'd'))} combinaciones revisadas; {fs_txt}; FEA (simulación de tensiones por "
                f"computadora) de las {len(fea_rows)} piezas críticas"
                + (f", <b>{n_fea_bad} no cumple{'n' if n_fea_bad != 1 else ''}</b>" if n_fea_bad else "")
                + "; y tests automáticos.")
    fea_list = "".join(
        f'<li><a class="mono" href="fea.html#{E(pid)}">{E(pid)}</a> FS {E(fnum(p["FS_min"], ".2f"))} / '
        f'{E(fnum(p.get("FS_objetivo"), "g"))} '
        f'<span class="pill {"ok" if p.get("cumple") else "bad"}">{"cumple" if p.get("cumple") else "no cumple"}</span></li>'
        for pid, p in fea_rows)

    date = (fea.get("meta") or {}).get("fecha")
    b_mass_less = (V.raw("sizing.masses.total_kg") or 0) - (V.raw("cmp.B_mass_total_kg") or 0)
    b_speed_note = (" (se supone la misma eficiencia de bomba que A: AWT no publica la curva de la JT132"
                    + (f"; la diferencia sale de los {fnum(b_mass_less, '.0f')} kg menos" if b_mass_less >= 0.5 else "")
                    + "; no es una ventaja demostrada)")
    if all_ok:
        status_pill = '<span class="pill ok">Diseño completo, revisado por computadora</span>'
        estado_h2 = "Revisado por computadora, sin puntos abiertos. Nada probado en el agua."
    else:
        status_pill = f'<a class="pill warn" href="#estado">Diseño en revisión: {open_points_phrase(n_open)} ↓</a>'
        estado_h2 = f"Revisado por computadora, con {open_points_phrase(n_open)}. Nada probado en el agua."
    body = f"""
<section class="hero">
  <div class="hero-text">
    <p class="eyebrow">P1-J · «Strålen» = «el chorro» en danés</p>
    <h1>Waterjet eléctrico inboard para un jet boat de {s_loa}&nbsp;m</h1>
    <p class="lead">{lead}</p>
    <p class="status-line">{status_pill}
      <span class="pill bad">Nada probado físicamente todavía</span></p>
    <div class="cta"><a class="btn primary" href="visor/index.html">Abrir el visor 3D</a>
      <a class="btn" href="#estado">Estado honesto</a>
      <a class="btn" href="#h-ir">Todo el proyecto ↓</a></div>
    <p class="more">{qe}</p>
  </div>
  <figure class="hero-fig">
    <a href="figuras/corte_crujia.html"><img src="visor/corte_lateral.png" alt="Corte longitudinal del CAD: casco, toma con rejilla, bomba, tren y motor, con la línea de flotación calculada" width="1600" height="560"></a>
    <figcaption>Corte por el centro del bote (crujía) en el CAD: toma con rejilla delante del impulsor, bomba, tren y motor. Tocá para ampliar.</figcaption>
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
  <h2 id="h-estado">{estado_h2}</h2>
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
      <p>{E(V('cmp.B_vmax_kmh', '.1f'))} km/h sostenidos{b_speed_note} · JT132: {E(V('cmp.B_jet_mass_kg', '.0f'))} kg con dirección y reversa</p>
      {f'<p class="warn-txt">{E(b_plane_note[2:3].upper() + b_plane_note[3:])}: el problema de planeo es del casco, no de la bomba.</p>' if b_plane_note else ''}
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
    # WhatsApp muestra ~2 líneas: la advertencia va primero
    desc = index_description(V, srcs, n_open)
    write(ctx, page, page_html(page, SITE_TITLE_FMT.format(loa=s_loa), desc, body, active="index.html"))
    if (ctx.out / "visor" / "corte_lateral.png").is_file():
        image_page(ctx, "figuras/corte_crujia.html", "visor/corte_lateral.png", "Corte por el centro del bote (crujía)",
                   "Corte longitudinal del CAD del waterjet P1-J: casco, toma con rejilla delante del impulsor, bomba, "
                   "tren y motor, con la línea de flotación calculada.", "index.html", "Inicio",
                   caption="Toma con rejilla delante del impulsor, bomba, tren (eje, sello, rodamientos y acople) y "
                           "motor, con la línea de flotación calculada.",
                   natural_w=natural_width(ctx.out / "visor" / "corte_lateral.png"))


def fea_fail_phrase(srcs):
    """«P1-STE-01 FS 1,80 < 2» por cada pieza FEA que no cumple (o "")."""
    return "; ".join(f"{pid} FS {fnum(p['FS_min'], '.2f')} < {fnum(p.get('FS_objetivo'), 'g')}"
                     for pid, p in ((srcs.get("fea") or {}).get("piezas") or {}).items()
                     if p.get("FS_min") is not None and not p.get("cumple"))


def site_rewrites(src, txt, srcs):
    """Correcciones que el sitio aplica al texto ya resuelto de un .md (el .md del repo no se toca): frases escritas
    a mano que dicen «verificado / sin interferencias» se ajustan a verify.json y al FEA cuando hay fallas abiertas
    (lo que no se pueda ajustar lo detecta overclaims() y bloquea la publicación)."""
    ok_verify = bool((srcs.get("verify") or {}).get("ok"))
    ok_all = all_checks_ok(srcs)
    n_fail = open_failures(srcs)
    vph = verify_phrase(srcs, html_out=False)
    fph = fea_fail_phrase(srcs)
    estado = "[Estado honesto](../index.html#estado)" if src.count("/") == 0 else None
    if src == "README.md":
        if not ok_verify:
            txt = txt.replace("CAD paramétrico verificado", "CAD paramétrico (verificación automática con fallas abiertas)")
            txt = re.sub(r"^(\| Interferencias:[^\n]*\| )\[VERIFICADO en software\]",
                         lambda m: m.group(1) + "[CALCULADO: verify_parts.py] **con fallas abiertas** (ver la portada, "
                         "Estado honesto)", txt, flags=re.M)
        if not ok_all:
            def honest(m):
                cad = (f"CAD de {m.group(1)} piezas " + ("sin interferencias" if ok_verify else f"con {vph}")
                       + f" en {m.group(2)} pares×estados")
                return (f"todo está revisado *en software*, **con {n_fail} falla{'s' if n_fail != 1 else ''} "
                        f"abierta{'s' if n_fail != 1 else ''} de CAD/FEA** ({cad}"
                        + (f"; FEA: {fph}" if fph else "")
                        + f"; {m.group(3)} por cálculo a mano, salvo excepciones declaradas; tests"
                        + (f"; detalle en {estado}" if estado else "") + ")")
            txt = re.sub(r"todo está verificado \*en software\* \(CAD de ([^()]*?) piezas sin interferencias en "
                         r"([^()]*?) pares×estados, (FS[^()]*?), tests\)", honest, txt)
    if src == "README.md":
        # «26,8 km/h (≈ A ± la curva de AWT…)» se leía como «igual a A» con 2,4 km/h de diferencia
        txt = re.sub(r"km/h \(≈ A ± la curva de AWT, que no está publicada: no es una ventaja demostrada\)",
                     "km/h sostenidos (parecido a A: se supone la misma eficiencia de bomba porque AWT no publica la "
                     "curva de la JT132; la diferencia sale de su menor masa y no es una ventaja demostrada)", txt)
    if src == "06_ensamblaje_y_pruebas.md" and not ok_verify:
        txt = re.sub(r"\[CALCULADO: `verify\.json` sin interferencias en ([^\]|]*)\]",
                     lambda m: f"[CALCULADO: `verify.json` en {m.group(1)}: hoy **con {n_fail} falla"
                     f"{'s' if n_fail != 1 else ''} abierta{'s' if n_fail != 1 else ''}** (ver Estado honesto "
                     f"en la portada)]", txt)
    if src == "research/R11_componentes_jet.md":
        # sin nombres de personas en el sitio: el contacto de ventas está en las páginas de Maytech
        txt = re.sub(r"\(\w+@maytech\.cn figura en sus páginas\)", "(el contacto de ventas figura en sus páginas)", txt)
    return txt


OVERCLAIM_VERIFY = re.compile(r"sin interferencias", re.I)
OVERCLAIM_ALL = re.compile(r"todo está verificado|CAD paramétrico verificado", re.I)


def overclaims(srcs):
    """Frases de los documentos publicados que dicen «verificado / sin interferencias» mientras verify.json o el FEA
    tienen fallas abiertas (después de site_rewrites). Un sitio así no se publica."""
    ok_verify, ok_all = bool((srcs.get("verify") or {}).get("ok")), all_checks_ok(srcs)
    if ok_all:
        return []
    out = []
    for src in all_docs():
        txt = site_rewrites(src, resolve_markers((ROOT / src).read_text(encoding="utf-8"), srcs, es=True), srcs)
        pats = ([OVERCLAIM_VERIFY] if not ok_verify else []) + [OVERCLAIM_ALL]
        for pat in pats:
            for m in pat.finditer(txt):
                ln = txt.count("\n", 0, m.start()) + 1
                out.append(f"{src}:{ln} dice «{m.group(0)}» pero verify.json/FEA tienen fallas abiertas "
                           f"(corregir el .md o agregar el caso a build_site.site_rewrites)")
    return out


def build_docs(ctx, srcs):
    meta = {}
    for src in ctx.docs:
        page = doc_out(src)
        raw = (ROOT / src).read_text(encoding="utf-8")
        txt = resolve_markers(raw, srcs, es=True)
        # el README apunta al visor «en la descripción del PR»: en el sitio, el visor está acá mismo
        txt = txt.replace("(link en la descripción del PR)", "([abrir el visor](04_diseno/visor/index.html))")
        txt = site_rewrites(src, txt, srcs)
        title = md_title(txt, src)
        desc = DOC_DESCRIPTIONS.get(src) or md_description(txt) or title
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
        write(ctx, page, page_html(page, f"{short_title(title)} — {SITE_NAME}", desc, html_body, active="documentos.html", wide=True))
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
            image_page(ctx, f"figuras/{f[:-4]}.html", f"figuras/{f}", f"Figura: {lbl}",
                       f"Figura del cálculo del waterjet P1-J: {lbl}.", "documentos.html", "Documentos",
                       natural_w=natural_width(ROOT / "figuras" / f), active="documentos.html")
            cards.append(f'<figure><a href="figuras/{f[:-4]}.html"><img src="figuras/{f}" alt="{E(lbl)}" loading="lazy"></a>'
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


def build_404(ctx):
    """404.html: GitHub Pages la sirve en cualquier ruta inexistente (a cualquier profundidad), así que sus enlaces
    son absolutos (https://…/p1-propulsion/…), no relativos."""
    page = "404.html"
    body = """
<p class="eyebrow">Error 404</p>
<h1>Esta página no existe</h1>
<p class="sub">El enlace puede ser de una versión anterior del sitio o tener un error de tipeo. Todo el proyecto
(visor 3D, documentos, planos, materiales y FEA) se recorre desde la portada.</p>
<div class="cta"><a class="btn primary" href="index.html">Ir a la portada</a>
  <a class="btn" href="visor/index.html">Visor 3D</a> <a class="btn" href="documentos.html">Documentos</a></div>
"""
    h = page_html(page, f"Página no encontrada — {SITE_NAME}",
                  "La página no existe. Portada del proyecto P1-J Strålen: waterjet eléctrico inboard.", body)
    h = re.sub(r'\b(href|src)="(?![a-z][a-z0-9+.\-]*:|#|//)([^"]*)"',
               lambda m: f'{m.group(1)}="{SITE_URL}{"" if m.group(2) == "index.html" else m.group(2)}"', h)
    write(ctx, page, h)


def natural_width(src_path):
    """Ancho natural (px) de un SVG (atributo width o viewBox) o de una imagen raster; None si no se sabe."""
    src_path = Path(src_path)
    try:
        if src_path.suffix.lower() == ".svg":
            head_ = src_path.read_text(encoding="utf-8", errors="ignore")[:2000]
            m = re.search(r"<svg\b[^>]*?\swidth=\"([\d.]+)(?:px)?\"", head_) or \
                re.search(r"<svg\b[^>]*?viewBox=\"[-\d.]+[ ,]+[-\d.]+[ ,]+([\d.]+)", head_)
            return round(float(m.group(1))) if m else None
        from PIL import Image
        with Image.open(src_path) as im:
            return im.width
    except Exception:
        return None


def image_page(ctx, page, img, title, desc, back_href, back_label, caption="", natural_w=None, active=None):
    """Página propia para una imagen grande (plano SVG, figura): en el teléfono el archivo crudo se abre diminuto, sin
    navegación y más ancho que la pantalla. Acá va con cabecera, «← volver», botón Ampliar/Ajustar (la imagen a su
    ancho natural, con desplazamiento dentro del recuadro) y enlace de descarga. `img` y `back_href` son rutas del
    sitio."""
    img_rel = rel(page, img)
    ext = posixpath.splitext(img)[1].lstrip(".").upper()
    zw = max(natural_w or 1600, 900)
    body = f"""
<nav class="crumbs" aria-label="Ruta"><a class="btn small" href="{rel(page, back_href)}">← {E(back_label)}</a></nav>
<h1 class="img-title">{E(title)}</h1>
{f'<p class="sub">{caption}</p>' if caption else ''}
<div class="imgtools"><button type="button" class="btn small" id="zoom" aria-pressed="false" aria-controls="iv">Ampliar</button>
  <a class="btn small" href="{img_rel}" download>Descargar {E(ext)}</a></div>
<div class="imgview" id="iv" style="--zoom-w:{zw}px"><img src="{img_rel}" alt="{E(title)}"></div>
<p class="sub">En el teléfono: tocá «Ampliar» y deslizá con el dedo dentro del recuadro, o pellizcá para hacer zoom.</p>
<script>
(function () {{
  var b = document.getElementById("zoom"), v = document.getElementById("iv"); if (!b || !v) return;
  b.addEventListener("click", function () {{
    var on = v.classList.toggle("zoomed"); b.setAttribute("aria-pressed", on ? "true" : "false");
    b.textContent = on ? "Ajustar a la pantalla" : "Ampliar";
  }});
}})();
</script>
"""
    write(ctx, page, page_html(page, f"{title} — {SITE_NAME}", desc, body, active=active, wide=True))


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
        mp = man.get(pid, {})
        image_page(ctx, "planos/" + f[:-4] + ".html", "planos/" + f, f"Plano {pid} {name.replace('_', ' ')}",
                   short_desc(f"Plano acotado {pid} del waterjet P1-J: " + (mp.get("desc") or name.replace("_", " "))
                              + (f" ({mp['material']})" if mp.get("material") else "") + "."),
                   "planos.html", "Planos",
                   caption=E(" · ".join(x for x in (mp.get("desc", ""), mp.get("material", "")) if x)),
                   natural_w=natural_width(ROOT / "04_diseno" / "planos" / f), active="planos.html")
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
                f'<figure class="plano"><a href="planos/{f[:-4]}.html" aria-label="Abrir el plano {E(pid)} {E(name)}">'
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
(<code>04_diseno/planos*.py</code>). Tocá un plano para abrirlo y ampliarlo. Los STEP y STL están en el
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
        tot_rows.append(f'<tr{" class=strong" if strong else ""}><td data-label="Concepto"><span>{E(d)}</span></td>'
                        f'<td class="num nowrap" data-label="Importe"><span>{val} {cur}</span></td></tr>')
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


def es_decimals(h):
    """Coma decimal en el texto de un fragmento HTML (no dentro de <code>/<pre>): «FS = 1.80» → «FS = 1,80».
    Las coordenadas «(590.7, -23.0, 169.5)» pasan a «(590,7; −23,0; 169,5)»; no se tocan los números de material
    EN («1.4404») ni versiones («v1.2»)."""
    parts = re.split(r"(<(?:code|pre)\b.*?</(?:code|pre)>)", h, flags=re.S)
    num = r"-?\d+(?:\.\d+)?"

    def txt(t):
        t = re.sub(rf"\(({num}), ({num}), ({num})\)", lambda m: f"({m.group(1)}; {m.group(2)}; {m.group(3)})", t)
        return re.sub(r"(?<![\w.])(?!1\.4\d{3}\b)(\d+)\.(\d+)(?![\w.])", r"\1,\2", t)
    return "".join(x if i % 2 else _text_nodes(x, txt) for i, x in enumerate(parts))


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
            f'<td class="num nowrap" data-label="FS mín. / objetivo"><span><b>{E(fnum(p.get("FS_min"), ".2f"))}</b> / {E(fnum(p.get("FS_objetivo"), "g"))}</span></td>'
            f'<td data-label="Cumple"><span class="pill {"ok" if ok else "bad"}">{"sí" if ok else "no"}</span></td>'
            f'<td data-label="Caso gobernante"><span><b>{E(caso)}</b> <small>{E(cname)}</small></span></td>'
            f'<td data-label="Material"><span>{E(mat)}</span></td></tr>')
        imgs = ""
        ims = list(p.get("imagenes") or [])
        order = {"vm": 0, "deformada": 1}
        ims.sort(key=lambda i: order.get(Path(i).stem.split("_", 1)[-1], 2))
        for i in ims:
            sp = _fea_image(ctx, i)
            if sp:
                kind = Path(i).stem.split("_", 1)[-1]
                cap = FEA_CAPTIONS.get(kind, kind)
                wp = sp[:-4] + ".html"
                image_page(ctx, wp, sp, f"{pid}: {cap}", f"FEA de {pid} ({p.get('descripcion', '')}): {cap}.",
                           f"fea.html#{pid}", f"FEA {pid}", natural_w=natural_width(ctx.out / sp), active="fea.html")
                imgs += (f'<figure><a href="{wp}"><img src="{sp}" alt="{E(pid)}: {E(cap)}" '
                         f'loading="lazy"></a><figcaption>{E(cap)}</figcaption></figure>')
        nb = ""
        if notes.get(pid):
            b, _, _ = render_md("\n".join(notes[pid]), toc=False)
            nb = es_decimals(ctx.rewrite_links(b, "04_diseno/fea", page))
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
  .hint:not([hidden]) { display: block; top: auto; bottom: 8px; left: 10px; right: auto; text-align: left; font-size: 11px;
    line-height: 1.35; pointer-events: none; text-shadow: 0 0 4px var(--bg, #fff); }
  /* el modelo 3D primero: título → visor → texto de presentación → el resto */
  .wrap { gap: 14px; padding-block-start: 12px; }
  .wrap > * { order: 3; }
  .wrap > .p1-home, .wrap > .stale { order: 0; }
  header.hero { display: contents; }
  header.hero > .eyebrow, header.hero > h1 { order: 0; }
  header.hero > h1 { font-size: clamp(1.6rem, 8vw, 2.2rem); }
  .wrap > section[aria-label="Visor 3D"] { order: 1; }
  header.hero > .lead, header.hero > .meta { order: 2; }
}
@media (prefers-color-scheme: light) {
  :root:not([data-theme="dark"]) .tbtn.demo:not([aria-pressed="true"]) { background: #b8490b; border-color: #b8490b; color: #fff; }
}
:root[data-theme="light"] .tbtn.demo:not([aria-pressed="true"]) { background: #b8490b; border-color: #b8490b; color: #fff; }
</style>"""
def STALE_BANNER_VISOR():
    return ("" if not STALE_BANNER else
            STALE_BANNER.replace('<div class="stale"', '<div class="stale" style="background:#b0302a;color:#fff;'
                                 'padding:10px 14px;border-radius:8px;font:600 14px/1.4 system-ui,sans-serif"'))


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


# El visor del repo le habla a Jorge («tu jet boat», «Hola Jorge!»); el sitio se comparte con cualquiera: en la copia
# publicada el texto va en tercera persona. (La fuente 04_diseno/visor/index.html no se toca.)
VISOR_NEUTRAL = [
    ('<h1>Hola Jorge! Este es tu <span class="name">“Strålen”</span></h1>',
     '<h1><span class="name">“Strålen”</span>: visor 3D del waterjet</h1>'),
    ("waterjet eléctrico para tu jet boat de", "waterjet eléctrico para el jet boat de Jorge,"),
    ("como el de tu plano", "como el del plano de Jorge"),
    ("el bucket te dan dirección", "el bucket dan dirección"),
    ("Tu comentario sobre la rejilla", "El comentario de Jorge sobre la rejilla"),
    ("Tu casco (referencia, transparente)", "Casco de Jorge (referencia, transparente)"),
    ("Medir tu casco", "Medir el casco"),
    ("La bomba de tu foto", "La bomba de la foto de Jorge"),
    ("(la de tu foto)", "(la de la foto de Jorge)"),
    ("Tenías razón:", "Jorge tenía razón:"),
    ('alt="Tu plano preliminar del waterjet"', 'alt="Plano preliminar del waterjet, dibujado por Jorge"'),
    ("Tu plano preliminar del", "Plano preliminar de Jorge del"),
]
# números del visor con la misma regla que el resto del sitio (docgen/fnum): coma decimal y espacio fino de miles
# también con 4 cifras («7 026», no «7026» ni «10.856»)
VISOR_FMT = ('const fmt = (x, d = 0) => (x == null || Number.isNaN(x)) ? "—" : Number(x).toLocaleString("es-ES", '
             '{ minimumFractionDigits: d, maximumFractionDigits: d });',
             'const fmt = (x, d = 0) => { if (x == null || Number.isNaN(Number(x))) return "—"; '
             'const s = Math.abs(Number(x)).toFixed(d).split("."); '
             'const neg = Number(x) < 0 && Number(Number(x).toFixed(d)) !== 0; '
             'return (neg ? "-" : "") + s[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g, "\\u202f") + (s[1] ? "," + s[1] : ""); };')
VISOR_CLAIM = ("que se verificó sin interferencias con la boquilla en ±25° y el bucket arriba y abajo",
               "que se verifica automáticamente con la boquilla en ±25° y el bucket arriba y abajo (hoy con fallas "
               "abiertas: ver «Estado honesto» en la portada)")


def build_visor(ctx, srcs=None):
    vdir = ROOT / "04_diseno" / "visor"
    for f in VISOR_FILES:
        if (vdir / f).exists() and f != "index.html":
            if f == "plano_waterjet_jorge.png":
                _site_image(ctx, f"04_diseno/visor/{f}", f"visor/{f}", 1000)
            else:
                ctx.copy(f"04_diseno/visor/{f}", f"visor/{f}")
    src = (vdir / "index.html").read_text(encoding="utf-8")
    for a, b in VISOR_NEUTRAL:
        src = src.replace(a, b)
    if VISOR_FMT[0] in src:
        src = src.replace(*VISOR_FMT)
    else:
        print("build_site: aviso: no se encontró fmt() en el visor (formato de números sin unificar)")
    if srcs is not None and not (srcs.get("verify") or {}).get("ok", True):
        src = src.replace(*VISOR_CLAIM)
    # el visor en el teléfono: la ayuda de gestos queda visible (abajo a la izquierda del lienzo); en vertical, el
    # encuadre inicial se aleja un poco para que entre el conjunto
    src = src.replace("const dist = rad / Math.sin(Math.min(vf, hf) / 2) * 0.85;",
                      "const dist = rad / Math.sin(Math.min(vf, hf) / 2) * (camera.aspect < 1 ? 1.0 : 0.85);")
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
    back = ('<a href="../index.html" class="p1-home" style="justify-self:start;margin:0 0 -14px;'
            'font:600 14px/1 var(--font-body,system-ui,sans-serif);background:var(--ink,#0f242b);color:var(--bg,#eef2f1);'
            'padding:10px 14px;border-radius:999px;text-decoration:none">← Inicio · P1-J</a>')
    src, n = re.subn(r'(<div class="wrap">)', lambda m: m.group(1) + "\n" + back + STALE_BANNER_VISOR(), src, count=1)
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


def build_og(ctx, V, srcs):
    """og.png (vista previa de WhatsApp): textos desde los datos; siempre dice que no hay nada construido ni probado.
    Devuelve el hash corto del PNG (va como ?v= en og:image para que WhatsApp no reutilice una vista previa vieja)."""
    import hashlib
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
            if th > 300:
                th, tw = 300, round(c.width * 300 / c.height)
            c = c.resize((tw, th), Image.LANCZOS)
            panel = Image.new("RGB", (W - 48, th + 24), (255, 255, 255))
            im.paste(panel, (24, H - th - 48))
            im.paste(c, ((W - tw) // 2, H - th - 36))
    d.rectangle([0, 0, W, 10], fill=accent)
    d.text((48, 40), "P1-J · STRÅLEN", font=_font(30), fill=sea)
    d.text((48, 82), "Waterjet eléctrico inboard", font=_font(60), fill=paper)
    loa = fnum(inp("boat.loa_m"), ".2f")
    d.text((48, 150), f"para un jet boat de {loa} m", font=_font(44, bold=False), fill=paper)
    n_open = open_points(V, srcs)
    sub = (f"Ø{V('sizing.selection.D_imp_mm', '.0f')} mm · {speed_phrase(V)} · "
           f"{V('manifest.totals.n_parts', 'd')} piezas CAD"
           + ("" if n_open == 0 and all_checks_ok(srcs) else f" · en revisión: {open_points_phrase(n_open)}"))
    for size in (26, 24, 22, 20):
        f_sub = _font(size, bold=False)
        if d.textlength(sub, font=f_sub) <= W - 96:
            break
    d.text((48, 206), sub, font=f_sub, fill=(147, 167, 171))
    d.text((48, 242), "Diseño en computadora · nada construido ni probado todavía", font=_font(26), fill=accent)
    dst = ctx.out / "og.png"
    im.save(dst, "PNG", optimize=True)
    if dst.stat().st_size > 300_000:
        im.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(dst, "PNG", optimize=True)
    ctx.copied.add("og.png")
    return hashlib.sha1(dst.read_bytes()).hexdigest()[:8]


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
  --scroll-shadow: rgba(0, 0, 0, 0.28);
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #0b181d; --surface: #11232a; --ink: #e4eded; --muted: #9db0b4; --line: #22383f;
    --accent: #ff8a4c; --accent-bg: #ff7a33; --accent-ink: #1a0c04; --sea: #5fbccd; --ok: #67cc88; --warn: #e8b259; --bad: #f27a6b;
    --ok-bg: #12301f; --warn-bg: #33270f; --bad-bg: #3a1714; --sea-bg: #0f2c33; --chrome: #071216; color-scheme: dark;
    --scroll-shadow: rgba(255, 255, 255, 0.22);
  }
}
:root[data-theme="dark"] {
  --bg: #0b181d; --surface: #11232a; --ink: #e4eded; --muted: #9db0b4; --line: #22383f;
  --accent: #ff8a4c; --accent-bg: #ff7a33; --accent-ink: #1a0c04; --sea: #5fbccd; --ok: #67cc88; --warn: #e8b259; --bad: #f27a6b;
  --ok-bg: #12301f; --warn-bg: #33270f; --bad-bg: #3a1714; --sea-bg: #0f2c33; --chrome: #071216; color-scheme: dark;
  --scroll-shadow: rgba(255, 255, 255, 0.22);
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
.l-short { display: none; }
@media (max-width: 600px) {
  .l-long, .site-nav a.nav-home { display: none; }
  .l-short { display: inline; }
  .site-header { position: static; }
  .site-nav { margin-left: 0; width: calc(100% + 2 * var(--gutter)); margin-inline: calc(-1 * var(--gutter)); padding-inline: calc(var(--gutter) - 8px);
    flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; -webkit-mask-image: linear-gradient(90deg, #000 88%, transparent); mask-image: linear-gradient(90deg, #000 88%, transparent); }
  .site-nav::-webkit-scrollbar { display: none; }
  .site-nav.at-end { -webkit-mask-image: none; mask-image: none; }
  .site-nav a { flex: none; min-height: 44px; min-width: 40px; display: inline-flex; align-items: center; justify-content: center; padding: 0 6px; font-size: 0.9rem; }
  .site-nav a.nav-home { display: none; }
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
a.pill { text-decoration: none; }
a.pill:hover { text-decoration: underline; }
.warn-txt { color: var(--warn); font-weight: 600; font-size: 0.92rem; }
.totop { position: fixed; right: 14px; bottom: calc(14px + env(safe-area-inset-bottom, 0px)); z-index: 30; width: 46px; height: 46px; border-radius: 50%; display: grid; place-items: center; background: var(--chrome); color: var(--chrome-ink); border: 1.5px solid color-mix(in srgb, var(--chrome-ink) 30%, transparent); font-size: 1.35rem; font-weight: 800; text-decoration: none; box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25); opacity: 0; pointer-events: none; transform: translateY(8px); transition: opacity .2s, transform .2s; }
.totop.show { opacity: 1; pointer-events: auto; transform: none; }
.totop:hover { color: var(--chrome-ink); }
@media print { .totop { display: none; } }
.img-title { font-size: clamp(1.6rem, 6vw, 2.6rem); overflow-wrap: anywhere; }
.imgtools { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }
button.btn { background: var(--surface); font: inherit; font-weight: 700; cursor: pointer; }
.imgview { overflow: auto; -webkit-overflow-scrolling: touch; background: #fff; border: 1px solid var(--line); border-radius: var(--radius); padding: 8px; max-height: 82vh; touch-action: pan-x pan-y pinch-zoom; }
.imgview img { display: block; width: 100%; height: auto; }
.imgview.zoomed img { width: var(--zoom-w, 1600px); max-width: none; }
.stale { background: #b0302a; color: #fff; padding: 10px var(--gutter); text-align: center; font-weight: 600; }
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
.ico { flex: 0 0 42px; height: 42px; border-radius: 10px; background: var(--accent-bg); color: var(--accent-ink); display: grid; place-items: center; }
.ico svg { width: 24px; height: 24px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.ico-plan { background: var(--sea); color: #fff; }
.ico-fea { background: var(--ok); color: #fff; }
.ico-git { background: var(--ink); color: var(--bg); }
:root[data-theme="dark"] .ico-plan, :root[data-theme="dark"] .ico-fea { color: #071216; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .ico-plan, :root:not([data-theme="light"]) .ico-fea { color: #071216; } }

/* documentos */
.doclist { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 320px), 1fr)); gap: 10px; }
.doclist li { min-width: 0; }
.doclist a { min-width: 0; display: grid; gap: 3px; height: 100%; padding: 12px 14px; background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); text-decoration: none; color: var(--ink); }
.doclist a:hover { border-color: var(--accent-bg); }
.doclist b { font-size: 1.02rem; line-height: 1.3; }
.doclist .mono { color: var(--sea); font-size: 0.78rem; overflow-wrap: anywhere; }
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
.table-wrap { width: 100%; max-width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 12px 0; border: 1px solid var(--line); border-radius: 8px;
  /* sombra en el borde por el que hay más tabla (las capas «local» la tapan cuando no hay más para desplazar) */
  background: linear-gradient(to right, var(--surface) 30%, transparent) left center / 40px 100% no-repeat local,
    linear-gradient(to left, var(--surface) 30%, transparent) right center / 40px 100% no-repeat local,
    radial-gradient(farthest-side at 0 50%, var(--scroll-shadow), transparent) left center / 14px 100% no-repeat scroll,
    radial-gradient(farthest-side at 100% 50%, var(--scroll-shadow), transparent) right center / 14px 100% no-repeat scroll,
    var(--surface); }
.table-wrap table.idcol td:first-child { white-space: nowrap; }
.table-wrap table { border-collapse: collapse; width: 100%; font-size: 0.9rem; }
.table-wrap th, .table-wrap td { padding: 7px 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; min-width: 7ch; }
.prose .table-wrap td, .prose .table-wrap th { min-width: 9ch; max-width: 46ch; }
.table-wrap td:first-child, .table-wrap th:first-child { min-width: 0; }
.table-wrap th { background: color-mix(in srgb, var(--line) 40%, var(--surface)); font-weight: 700; position: sticky; top: 0; }
.table-wrap tbody tr:last-child td { border-bottom: 0; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
td small { display: block; color: var(--muted); font-size: 0.8125rem; }
/* teléfono: los documentos usan todo el ancho (sin el marco de la tarjeta) y las tablas anchas se desplazan como
   columnas de verdad (no una palabra por renglón) */
@media (max-width: 600px) {
  .prose.doc { padding: 14px var(--gutter); border-inline: 0; border-radius: 0; margin-inline: calc(-1 * var(--gutter)); }
  .prose.doc .table-wrap { width: calc(100% + 2 * var(--gutter)); max-width: none; margin-inline: calc(-1 * var(--gutter)); border-radius: 0; border-inline: 0; }
  .prose .table-wrap td, .prose .table-wrap th { min-width: 14ch; max-width: 34ch; }
  .prose .table-wrap td:first-child, .prose .table-wrap th:first-child { min-width: 7ch; }
}

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
  table.stack td > .pill { justify-self: start; }
  table.stack td.num { text-align: left; }
  /* BOM: tarjeta compacta — ID y precio arriba, descripción, cantidad + verificación, proveedor */
  table.bom tr { display: grid; grid-template-columns: minmax(0, 1fr) auto; grid-auto-flow: row dense; gap: 2px 12px; padding: 10px 12px; }
  table.bom tr[hidden] { display: none; }
  table.bom td { display: block; padding: 0; min-width: 0; max-width: none; }
  table.bom td::before { content: none; }
  table.bom td.idc { grid-column: 1; font-weight: 700; color: var(--sea); }
  table.bom td.tot { grid-column: 2; grid-row: 1; text-align: right; font-weight: 800; }
  table.bom td.tot::after { content: " € total"; font-weight: 600; font-size: 0.8em; color: var(--muted); }
  table.bom td.desc { grid-column: 1 / -1; }
  table.bom td.qty { grid-column: 1; text-align: left; color: var(--muted); font-size: 0.85rem; }
  table.bom td.tagcell { grid-column: 2; text-align: right; }
  table.bom td.tagcell small, table.bom td.fecha { display: none; }
  table.bom td.prov { grid-column: 1 / -1; font-size: 0.85rem; color: var(--muted); }
  table.bom td.prov br { display: none; }
  table.bom td.prov a, table.bom td.prov > .muted { margin-left: 6px; }
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
    # sizing.py (paso 1 de run_all) toma la masa del jet del manifest.json de la corrida ANTERIOR del CAD (paso 2):
    # si el CAD cambió de masa, todas las velocidades y márgenes salen de una masa vieja
    jet = next((it.get("kg") for it in (V.raw("sizing.masses.items") or []) if it.get("id") == "jet"), None)
    cad = V.raw("manifest.totals.jet_unit_mass_kg")
    if isinstance(jet, (int, float)) and isinstance(cad, (int, float)) and abs(jet - cad) > 0.05:
        probs.append(f"sizing.json usa una masa de jet anterior al CAD ({jet:.2f} kg contra "
                     f"manifest.totals.jet_unit_mass_kg = {cad:.2f} kg): correr sizing.py (o run_all.py) otra vez")
    if dp.exists():
        dat = json.loads(dp.read_text(encoding="utf-8"))
        res, cmpv = dat.get("resumen") or {}, dat.get("comparacion") or {}
        gm = V.raw("sizing.hydrostatics.GM_m")
        checks = [("resumen", res, "vmax_kmh", "sizing.performance.vmax_cont_kmh", None, 0.01),
                  ("resumen", res, "vmax_pico_kmh", "sizing.verdict.vmax_peak_kmh.nominal", None, 0.05),
                  ("resumen", res, "t_planeo_s", "sizing.verdict.t_to_plane_nominal_s", None, 0.5),
                  ("resumen", res, "bollard_n", "sizing.performance.bollard_N", None, 0.5),
                  ("resumen", res, "t_fondo_min", "sizing.energy.t_top_min", None, 0.5),
                  ("resumen", res, "t_legal_h", "sizing.energy.t_legal_h", None, 0.05),
                  ("resumen", res, "gm_mm", "sizing.hydrostatics.GM_m×1000", gm * 1000 if isinstance(gm, (int, float)) else None, 0.5),
                  ("resumen", res, "masa_total_kg", "sizing.masses.total_kg", None, 0.05),
                  ("resumen", res, "masa_jet_kg", "manifest.totals.jet_unit_mass_kg", None, 0.05),
                  ("resumen", res, "costo_eur", "bom.total_eur", None, 0.5),
                  ("resumen", res, "n_piezas", "manifest.totals.n_parts", None, 0),
                  ("comparacion", cmpv, "B_vmax_kmh", "cmp.B_vmax_kmh", None, 0.05),
                  ("comparacion", cmpv, "B_total_eur_min", "cmp.B_total_eur_min", None, 0.5),
                  ("comparacion", cmpv, "B_total_eur_max", "cmp.B_total_eur_max", None, 0.5),
                  ("comparacion", cmpv, "A_total_eur", "bom.total_eur", None, 0.5)]
        for sec, d, key, path, b, tol in checks:
            a = d.get(key)
            b = V.raw(path) if b is None else b
            if isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) > tol:
                probs.append(f"visor/datos.json desactualizado: {sec}.{key} = {a:g} y {path} = {b:g} "
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
    probs += overclaims(srcs)
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
    # marcadores V: el texto guardado en el .md (lo que muestra GitHub, p. ej. el README de la raíz) contra el valor actual
    for md in sorted(ROOT / d for d in all_docs()):
        stale = []
        for m in PAT_V.finditer(md.read_text(encoding="utf-8")):
            path, fmt, old_txt = m.group(1), m.group(2), m.group(3)
            src, _, rest = path.partition(".")
            try:
                val = docgen.getpath(srcs[src], rest)
                new = format(val, fmt) if fmt else str(val)
            except Exception:
                continue
            if new != old_txt:
                stale.append(path)
        if stale:
            out.append(f"{md.relative_to(ROOT)}: {len(stale)} marcador(es) V desactualizados en el .md "
                       f"({', '.join(sorted(set(stale))[:4])}{', …' if len(set(stale)) > 4 else ''}): falta docgen.py "
                       f"(GitHub muestra el .md con los valores viejos; el sitio ya usa los actuales)")
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


def build(out, allow_stale=False):
    """Compila el sitio en `out`. Si las fuentes que se copian tal cual están desactualizadas (freshness), no toca
    `out` y devuelve None, salvo con allow_stale=True (vista previa): entonces las páginas llevan un aviso rojo."""
    global OG_VERSION, STALE_BANNER
    srcs = sources()
    V = Values(srcs)
    for w in staleness_warnings(srcs):
        print("build_site: aviso:", w)
    probs = freshness(srcs)
    for pr in probs:
        print("build_site: *** FUENTE DESACTUALIZADA ***", pr)
    if probs and not allow_stale:
        print(f"build_site: *** {len(probs)} problema(s) de frescura: NO se genera el sitio (no se tocó {out}). "
              f"Correr run_all.py completo; para una vista previa: --allow-stale ***")
        return None
    STALE_BANNER = (f'<div class="stale" role="alert"><b>Vista previa con datos desactualizados</b> — '
                    f'{len(probs)} fuente(s) no coinciden con los resultados actuales; no compartir este enlace.</div>'
                    if probs else "")
    out = clean_out(Path(out))
    ctx = Ctx(out)
    OG_VERSION = build_og(ctx, V, srcs)
    write(ctx, ".nojekyll", "")
    write(ctx, "assets/site.css", CSS)
    build_visor(ctx, srcs)
    meta = build_docs(ctx, srcs)
    build_documentos(ctx, meta)
    build_index(ctx, V, srcs)
    build_planos(ctx, srcs)
    build_bom(ctx, srcs, V)
    build_fea(ctx, srcs)
    build_404(ctx)
    n_html = sum(1 for _ in out.rglob("*.html"))
    size = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    print(f"build_site: {n_html} páginas HTML, {size / 1e6:.1f} MB en {out}")
    if probs:
        print(f"build_site: *** {len(probs)} problema(s) de frescura: vista previa (--allow-stale), NO publicar ***")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=str(ROOT / "docs"), help="carpeta de salida (se regenera desde cero)")
    ap.add_argument("--allow-stale", action="store_true",
                    help="compilar aunque las fuentes estén desactualizadas (vista previa con aviso rojo; no publicar)")
    a = ap.parse_args(argv)
    return 0 if build(a.out, allow_stale=a.allow_stale) is not None else 2


if __name__ == "__main__":
    sys.exit(main())
