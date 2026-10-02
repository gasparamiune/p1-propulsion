"""Sitio estático (build_site.py → docs/ para GitHub Pages): páginas, enlaces locales, Open Graph."""
from __future__ import annotations

import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://gasparamiune.github.io/p1-propulsion/"


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    out = tmp_path_factory.mktemp("site") / "docs"
    r = subprocess.run([sys.executable, str(ROOT / "build_site.py"), "--out", str(out)], cwd=ROOT,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return out


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.meta, self.title, self.lang, self._t = [], {}, None, None, False
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for k in ("id", "name"):
            if a.get(k) and tag != "meta":
                self.ids.add(a[k])
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "title":
            self._t = True
        if tag == "meta":
            k = a.get("property") or a.get("name")
            if k:
                self.meta[k] = a.get("content", "")
        for att in ("href", "src"):
            if a.get(att) is not None:
                self.links.append((tag, att, a[att]))

    def handle_data(self, data):
        if self._t:
            self.title = (self.title or "") + data

    def handle_endtag(self, tag):
        if tag == "title":
            self._t = False


def parse(p):
    h = Links()
    h.feed(p.read_text(encoding="utf-8"))
    return h


def local(url):
    s = urlsplit(url)
    return not (s.scheme or url.startswith(("#", "//")))


def test_pages_exist(site):
    import build_site
    for p in ["index.html", "documentos.html", "planos.html", "bom.html", "fea.html", "visor/index.html",
              "visor/datos.json", "visor/mallas.txt", "visor/corte_lateral.png", "assets/site.css", ".nojekyll"]:
        assert (site / p).is_file(), p
    docs = build_site.all_docs()
    assert "README.md" in docs and "04_diseno/fea/README.md" in docs
    assert any(d.startswith("research/") for d in docs)
    for d in docs:
        assert (site / build_site.doc_out(d)).is_file(), d
    svgs = sorted((ROOT / "04_diseno" / "planos").glob("*.svg"))
    assert svgs and all((site / "planos" / s.name).is_file() for s in svgs)
    assert not list(site.rglob("*.step")) and not list(site.rglob("*.stl")) and not list(site.rglob("*.md"))


REPO = "https://github.com/gasparamiune/p1-propulsion/"


def test_local_links_resolve(site):
    """Enlaces locales: el archivo existe dentro del sitio y el #fragmento existe en la página de destino."""
    pages = sorted(site.rglob("*.html"))
    assert len(pages) > 20
    parsed = {p.resolve(): parse(p) for p in pages}
    bad = []
    for p, h in parsed.items():
        rp = p.relative_to(site.resolve())
        for tag, att, url in h.links:
            if url.startswith("/") and not url.startswith("//"):
                bad.append(f"{rp}: enlace absoluto a la raíz {url}")
                continue
            if not local(url):
                continue
            sp = urlsplit(url)
            path, frag = unquote(sp.path), unquote(sp.fragment)
            if path.endswith(".md"):
                bad.append(f"{rp}: enlace a .md {url}")
            if path:
                target = (p.parent / path).resolve()
                if path.endswith("/"):
                    target = target / "index.html"
                if not target.is_file() or site.resolve() not in target.parents:
                    bad.append(f"{rp}: {att}={url} no existe")
                    continue
            else:
                target = p
            if frag and target.suffix == ".html":
                ids = parsed[target].ids if target in parsed else parse(target).ids
                if frag not in ids:
                    bad.append(f"{rp}: {att}={url}: no hay id «{frag}» en {target.name}")
    assert not bad, "\n".join(bad[:40])


def test_github_links_point_to_tracked_paths(site):
    """Los enlaces blob/tree/main del repo apuntan a archivos que existen y que git no ignora."""
    paths = set()
    for p in site.rglob("*.html"):
        for _, _, url in parse(p).links:
            for kind in ("blob/main/", "tree/main/"):
                if url.startswith(REPO + kind):
                    rest = unquote(urlsplit(url).path.split("/" + kind, 1)[1]).rstrip("/")
                    if rest:
                        paths.add(rest)
    assert paths
    missing = sorted(x for x in paths if not (ROOT / x).exists())
    assert not missing, missing[:20]
    r = subprocess.run(["git", "check-ignore", "--stdin"], cwd=ROOT, input="\n".join(sorted(paths)),
                       capture_output=True, text=True)
    ignored = [x for x in r.stdout.splitlines() if x.strip()]
    assert not ignored, f"enlaces a archivos ignorados por git: {ignored[:20]}"


def test_open_graph_and_head(site):
    for p in sorted(site.rglob("*.html")):
        h = parse(p)
        rp = p.relative_to(site)
        assert h.lang == "es", rp
        assert h.title and h.title.strip(), rp
        for k in ("description", "og:title", "og:description", "og:type", "og:url", "og:image", "twitter:card", "viewport"):
            assert h.meta.get(k), f"{rp}: falta {k}"
        assert h.meta["og:image"] == SITE_URL + "og.png", rp
        assert h.meta["og:url"].startswith(SITE_URL), rp
        assert h.meta["twitter:card"] == "summary_large_image", rp
        assert any(t == "link" and u.startswith("data:image/svg+xml") for t, a, u in h.links), f"{rp}: favicon"


def test_og_image(site):
    from PIL import Image
    p = site / "og.png"
    with Image.open(p) as im:
        assert im.size == (1200, 630)
    assert p.stat().st_size < 300_000


def test_index_content(site):
    txt = (site / "index.html").read_text(encoding="utf-8")
    for s in ("Estado honesto", "Próximos pasos físicos", "GM", "Loctite 648", "T4", "visor/index.html",
              "documentos.html", "planos.html", "bom.html", "fea.html", "github.com/gasparamiune/p1-propulsion"):
        assert s in txt, s
    assert "[CALCULADO" in txt and "[VERIFICADO" in txt
    assert not re.search(r"\b(href|src)=\"/(?!/)", txt)


def test_markers_hidden_and_tables_wrapped(site):
    readme = (site / "doc" / "README.html").read_text(encoding="utf-8")
    assert "<!--V:" not in readme and "&lt;!--V:sizing" not in readme
    assert "<table" in readme and '<div class="table-wrap"><table' in readme
    assert readme.count("<table") == readme.count('<div class="table-wrap"><table')


def test_deterministic(site, tmp_path):
    out2 = tmp_path / "docs2"
    r = subprocess.run([sys.executable, str(ROOT / "build_site.py"), "--out", str(out2)], cwd=ROOT,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    a = sorted(p.relative_to(site).as_posix() for p in site.rglob("*") if p.is_file())
    b = sorted(p.relative_to(out2).as_posix() for p in out2.rglob("*") if p.is_file())
    assert a == b
    diff = [f for f in a if (site / f).read_bytes() != (out2 / f).read_bytes()]
    assert not diff, diff[:10]


def test_titles_keep_underscores(site):
    docs = (site / "documentos.html").read_text(encoding="utf-8")
    assert "PENDIENTES_GASPAR" in docs and "run_all.py" in docs
    h = parse(site / "doc" / "PENDIENTES_GASPAR.html")
    assert "PENDIENTES_GASPAR" in h.meta["og:title"] and "PENDIENTES_GASPAR" in h.title


def _md_list_items(src):
    n, fence = 0, False
    for ln in (ROOT / src).read_text(encoding="utf-8").splitlines():
        if ln.lstrip().startswith("```"):
            fence = not fence
            continue
        if not fence and re.match(r"^\s*(?:>\s*)*([-*+]|\d+\.)\s+\S", ln):
            n += 1
    return n


def test_lists_render_as_lists(site):
    """python-markdown funde en un párrafo la lista pegada a una línea de texto: build_site lo corrige."""
    import build_site
    for src in ("decisiones.md", "checklist_salida.md", "06_ensamblaje_y_pruebas.md", "05_fabricacion.md"):
        html_txt = (site / build_site.doc_out(src)).read_text(encoding="utf-8")
        art = html_txt.split('<article class="prose doc">', 1)[1].split("</article>", 1)[0]
        assert art.count("<li") >= _md_list_items(src), src
        assert not re.search(r"\n\s*- \[[ x]\]", art), src


def test_bom_totals_apart(site):
    import build_site
    txt = (site / "bom.html").read_text(encoding="utf-8")
    items = txt.split('id="bom"', 1)[1].split("</table>", 1)[0]
    assert "TOTAL SISTEMA" not in items and "SUBTOTAL" not in items
    assert "TOTAL SISTEMA DKK" in txt
    bom = build_site.docgen.load("bom_resumen.json")
    if bom.get("n_rows"):
        assert f"BOM — {bom['n_rows']} renglones" in txt


def test_sources_fresh():
    """El visor y los hallazgos FEA que se copian tal cual coinciden con resultados/*.json (si falla: run_all.py)."""
    import build_site
    probs = build_site.freshness(build_site.sources())
    assert not probs, "\n".join(probs)


def test_committed_docs_up_to_date(site):
    """docs/ (lo que publica GitHub Pages) es idéntico a una compilación nueva: si no, correr build_site.py."""
    docs = ROOT / "docs"
    if not (docs / "index.html").exists():
        pytest.skip("docs/ no generado")
    a = sorted(p.relative_to(site).as_posix() for p in site.rglob("*") if p.is_file())
    b = sorted(p.relative_to(docs).as_posix() for p in docs.rglob("*") if p.is_file())
    assert a == b, sorted(set(a) ^ set(b))[:20]
    diff = [f for f in a if (site / f).read_bytes() != (docs / f).read_bytes()]
    assert not diff, f"docs/ desactualizado (correr python build_site.py): {diff[:10]}"
