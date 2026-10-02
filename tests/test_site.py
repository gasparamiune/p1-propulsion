"""Sitio estático (build_site.py → docs/ para GitHub Pages): páginas, enlaces locales, Open Graph."""
from __future__ import annotations

import json
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
    # --allow-stale: la frescura de las fuentes la controla test_sources_fresh; acá se prueba el sitio en sí
    r = subprocess.run([sys.executable, str(ROOT / "build_site.py"), "--allow-stale", "--out", str(out)], cwd=ROOT,
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
    """Enlace dentro del sitio (incluye «#fragmento» de la misma página y las URL absolutas del propio sitio)."""
    s = urlsplit(url)
    return (not (s.scheme or url.startswith("//")) and url != "#") or url.startswith(SITE_URL)


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
    # cada plano tiene su página (cabecera, «← Planos», ampliar, descargar) y la galería enlaza a ella, no al SVG crudo
    assert all((site / "planos" / (s.stem + ".html")).is_file() for s in svgs)
    gal = (site / "planos.html").read_text(encoding="utf-8")
    assert not re.search(r'<a href="planos/[^"]+\.svg"', gal)
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
            absolute = url.startswith(SITE_URL)      # 404.html, canonical, og:url: https://…/p1-propulsion/<ruta>
            sp = urlsplit(url[len(SITE_URL):] if absolute else url)
            path, frag = unquote(sp.path), unquote(sp.fragment)
            if absolute and path in ("", "/"):
                path = "index.html"
            if path.endswith(".md"):
                bad.append(f"{rp}: enlace a .md {url}")
            if path:
                target = ((site.resolve() if absolute else p.parent) / path).resolve()
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
    # y que estén en git (un archivo nuevo sin «git add» da 404 en GitHub): archivo versionado o carpeta que tiene alguno
    r = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, text=True)
    tracked = set(r.stdout.split("\0")) - {""}
    dirs = {"/".join(f.split("/")[:i]) for f in tracked for i in range(1, f.count("/") + 1)}
    untracked = sorted(x for x in paths if x not in tracked and x not in dirs)
    assert not untracked, f"enlaces a GitHub de archivos que git no versiona (falta git add): {untracked[:20]}"


def test_open_graph_and_head(site):
    for p in sorted(site.rglob("*.html")):
        h = parse(p)
        rp = p.relative_to(site)
        assert h.lang == "es", rp
        assert h.title and h.title.strip(), rp
        for k in ("description", "og:title", "og:description", "og:type", "og:url", "og:image", "twitter:card", "viewport"):
            assert h.meta.get(k), f"{rp}: falta {k}"
        assert re.fullmatch(re.escape(SITE_URL) + r"og\.png\?v=[0-9a-f]{8}", h.meta["og:image"]), rp
        assert h.meta.get("twitter:image") == h.meta["og:image"] and h.meta.get("og:image:alt"), rp
        assert h.meta["og:url"] == SITE_URL + ("" if rp.as_posix() == "index.html" else rp.as_posix()), rp
        assert len(h.title) <= 110, f"{rp}: <title> demasiado largo ({len(h.title)})"
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
    r = subprocess.run([sys.executable, str(ROOT / "build_site.py"), "--allow-stale", "--out", str(out2)], cwd=ROOT,
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


def _check_status_claims(root):
    import build_site
    srcs = build_site.sources()
    V = build_site.Values(srcs)
    txt = (root / "index.html").read_text(encoding="utf-8")
    n_open = build_site.open_points(V, srcs)
    all_ok = build_site.all_checks_ok(srcs)
    green = re.findall(r'<(?:span|a)[^>]*class="pill ok"[^>]*>([^<]*)<', txt)
    if not all_ok or n_open:
        assert not any("verificado" in g.lower() or "completo" in g.lower() for g in green), green
        assert "Verificado en software. Nada probado" not in txt
        assert "Diseño en revisión" in txt and build_site.open_points_phrase(n_open) in txt
        # la pastilla cuenta lo mismo que la lista «Puntos abiertos declarados» (los ítems en rojo)
        ol = txt.split('<ol class="open">', 1)[1].split("</ol>", 1)[0]
        assert ol.count('<li class="bad">') == n_open
        _, other, _ = build_site.verify_summary(srcs)
        for kind, t in other:      # las fallas que no son choques (cotas críticas) también se nombran
            assert t.split(" ")[0] in txt, t
    if not all_ok:
        # los documentos publicados no dicen «sin interferencias» / «todo está verificado» con fallas abiertas
        ok_verify = bool((srcs["verify"] or {}).get("ok"))
        for p in (root / "doc").rglob("*.html"):
            art = p.read_text(encoding="utf-8")
            assert "todo está verificado" not in art and "CAD paramétrico verificado" not in art, p
            if not ok_verify:
                assert "sin interferencias" not in art, p
    desc = parse(root / "index.html").meta["og:description"]
    assert len(desc) <= 200 and "sin construir" in desc[:60], desc
    tgt, ok_t = build_site.inp("operation.top_speed_target_kmh"), V.raw("sizing.checks.ok_vmax_target")
    if tgt is not None and not ok_t:
        assert "no cumple" in desc, desc


def test_status_claims_follow_data(site):
    """La portada no dice «verificado / completo» (pastilla verde, título) si hay puntos abiertos, verify.json o el
    FEA tienen fallas; los documentos tampoco dicen «sin interferencias» con choques abiertos."""
    _check_status_claims(site)


def test_committed_docs_publishable():
    """docs/ (lo que sirve GitHub Pages) no es una vista previa con aviso rojo (--allow-stale) y no exagera el estado."""
    docs = ROOT / "docs"
    if not (docs / "index.html").exists():
        pytest.skip("docs/ no generado")
    stale = sorted(p.relative_to(docs).as_posix() for p in docs.rglob("*.html")
                   if 'class="stale"' in p.read_text(encoding="utf-8"))
    assert not stale, f"docs/ compilado con --allow-stale (fuentes desactualizadas): {stale[:5]}"
    _check_status_claims(docs)


def _strict_json(path):
    def bad(const):
        raise ValueError(f"{path}: {const} no es JSON válido")
    json.loads(path.read_text(encoding="utf-8"), parse_constant=bad)


def test_json_strict_for_browsers(site):
    """Todo .json que baja el navegador es JSON estricto: un Infinity/NaN (Python los escribe por defecto) hace que
    `response.json()` rechace el archivo entero y el visor muestra «No se pudo cargar el modelo» (pasó con
    `t_to_plane_high_s` = inf cuando la banda alta no planea). Incluye el visor fuente, que se publica como artifact."""
    files = (sorted(site.rglob("*.json")) + sorted((ROOT / "docs").rglob("*.json"))
             + sorted((ROOT / "04_diseno" / "visor").glob("*.json")))
    assert sum(f.name == "datos.json" for f in files) >= 2
    for f in files:
        _strict_json(f)


def test_stale_sources_block_build(tmp_path, monkeypatch):
    """Con fuentes desactualizadas build_site sale con código ≠ 0 y no toca la carpeta de salida (salvo --allow-stale)."""
    import build_site
    monkeypatch.setattr(build_site, "freshness", lambda srcs: ["prueba: fuente vieja"])
    out = tmp_path / "out"
    assert build_site.main(["--out", str(out)]) == 2
    assert not out.exists()


def test_404_absolute_links(site):
    """404.html se sirve en cualquier ruta: enlaces absolutos al sitio (que test_local_links_resolve comprueba)."""
    h = parse(site / "404.html")
    rel = [u for t, a, u in h.links if not (u.startswith(("https://", "data:", "#")))]
    assert not rel, rel
    assert any(u == SITE_URL for _, _, u in h.links)
    own = [u for _, _, u in h.links if u.startswith(SITE_URL)]
    assert len(own) >= 5, own


def test_mobile_css_guards(site):
    """Reglas que evitan desbordes en teléfonos de 320 px y textos pegados en las tarjetas de la BOM."""
    css = (site / "assets" / "site.css").read_text(encoding="utf-8")
    assert re.search(r"\.doclist \.mono \{[^}]*overflow-wrap: anywhere", css)
    assert re.search(r"\.doclist a \{[^}]*min-width: 0", css)
    assert "table.bom td.prov > .muted" in css
    fea = (site / "fea.html").read_text(encoding="utf-8")
    # en table.stack (grid) ningún texto suelto: cada celda lleva un solo elemento
    for td in re.findall(r'<td[^>]*data-label="FS mín\. / objetivo"[^>]*>(.*?)</td>', fea):
        assert td.startswith("<span>") and td.endswith("</span>"), td
