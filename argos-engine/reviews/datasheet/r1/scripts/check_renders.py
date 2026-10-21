#!/opt/engine-venv/bin/python -I
"""REV-DS-1 criterion (f): every v3.5.2 render's inputs against the FINAL CAD v3.5.2 manifest rows.

Checks, per view: the GLB and BOM sha in the view meta and in render_manifest.json against the
03-cad/v3.5.2/MANIFEST_v3.5.2.sha256 rows (and the files on disk today); the PNG sha in the render
manifest against the file; the part numbers the view meta lists against the GLB node names and the
BOM; and (optionally) the datasheet assets that are derived from the renders (jpg/png of the same
view name). Read-only. A hash match is provenance, not a check of the picture's content.

usage: check_renders.py <renders_dir> <cad_dir> <out_json> [<assets_dir>]
"""
import hashlib
import json
import os
import re
import sys


def sha(p, n=16):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()[:n]


def main():
    rdir, cad, outp = sys.argv[1], sys.argv[2], sys.argv[3]
    assets = sys.argv[4] if len(sys.argv) > 4 else None
    man = {}
    for ln in open(os.path.join(cad, 'MANIFEST_v3.5.2.sha256'), encoding='utf-8'):
        if ln.strip():
            h, rel = ln.split(None, 1)
            man[rel.strip().lstrip('*')] = h
    rm = json.load(open(os.path.join(rdir, 'render_manifest.json'), encoding='utf-8'))
    res = {'renders_dir': rdir, 'cad_dir': cad, 'cad_manifest_sha16': sha(os.path.join(cad, 'MANIFEST_v3.5.2.sha256')),
           'cad_manifest_rows': len(man), 'render_manifest_sha16': sha(os.path.join(rdir, 'render_manifest.json')),
           'checks': [], 'views': []}

    def chk(name, ok, detail):
        res['checks'].append({'check': name, 'ok': bool(ok), 'detail': detail})

    glb_rel = os.path.relpath(rm['glb'], cad)
    bom_rel = os.path.relpath(rm['bom'], cad)
    chk('render_manifest cad_version', rm.get('cad_version') == 'v3.5.2', rm.get('cad_version'))
    chk('GLB path is inside the FINAL v3.5.2 CAD dir', not glb_rel.startswith('..'), rm['glb'])
    chk('GLB row in CAD manifest', glb_rel in man, glb_rel)
    chk('GLB sha (render manifest) = CAD manifest row', man.get(glb_rel, '')[:16] == rm.get('glb_sha256_16'),
        f"{rm.get('glb_sha256_16')} vs {man.get(glb_rel, '')[:16]}")
    chk('GLB file on disk = CAD manifest row', sha(rm['glb'], 64) == man.get(glb_rel), sha(rm['glb']))
    chk('BOM row in CAD manifest', bom_rel in man, bom_rel)
    chk('BOM sha (render manifest) = CAD manifest row', man.get(bom_rel, '')[:16] == rm.get('bom_sha256_16'),
        f"{rm.get('bom_sha256_16')} vs {man.get(bom_rel, '')[:16]}")
    scr = os.path.join(os.path.dirname(os.path.dirname(rdir.rstrip('/'))), '..', 'gen', 'render_views_blender.py')
    scr = os.path.normpath(os.path.join(rdir, '..', '..', '..', 'gen', 'render_views_blender.py'))
    if os.path.isfile(scr):
        chk('render script sha now = render manifest', sha(scr) == rm.get('script_sha256_16'), f'{sha(scr)} vs {rm.get("script_sha256_16")}')

    # GLB node names (part numbers present in the display geometry)
    glb_pns = set()
    try:
        import pygltflib
        g = pygltflib.GLTF2().load(rm['glb'])
        for nd in g.nodes:
            nm = nd.name or ''
            m = re.match(r'(ENG-[A-Z]{2}-[0-9A-Z\-]+?)(?:#\d+|_\d+|$)', nm)
            if m:
                glb_pns.add(m.group(1))
        res['glb_nodes'] = len(g.nodes)
        res['glb_pn_count'] = len(glb_pns)
    except Exception as e:  # noqa
        res['glb_error'] = repr(e)
    bom = json.load(open(rm['bom'], encoding='utf-8'))
    bom_pns = set(l.get('pn') for l in bom.get('lines', []) if l.get('pn'))
    res['bom_pn_count'] = len(bom_pns)
    res['bom_pns_not_in_glb'] = sorted(p for p in bom_pns if p not in glb_pns) if glb_pns else None

    views = {v['png']: v for v in rm.get('views', [])}
    for fn in sorted(os.listdir(rdir)):
        if not fn.endswith('_meta.json'):
            continue
        meta = json.load(open(os.path.join(rdir, fn), encoding='utf-8'))
        png = meta.get('png') or fn.replace('_meta.json', '.png')
        v = {'meta': fn, 'meta_sha16': sha(os.path.join(rdir, fn)), 'view': meta.get('view'), 'png': png}
        pth = os.path.join(rdir, png)
        v['png_exists'] = os.path.isfile(pth)
        v['png_sha16'] = sha(pth) if v['png_exists'] else None
        rv = views.get(png)
        v['in_render_manifest'] = rv is not None
        v['png_sha_matches_manifest'] = (rv or {}).get('png_sha256_16') == v['png_sha16']
        v['meta_glb_sha'] = meta.get('glb_sha256_16')
        v['meta_bom_sha'] = meta.get('bom_sha256_16')
        v['glb_ok'] = meta.get('glb_sha256_16') == man.get(glb_rel, '')[:16]
        v['bom_ok'] = (meta.get('bom_sha256_16') in (None, man.get(bom_rel, '')[:16]))
        pns = meta.get('pns') or []
        v['n_pns'] = len(pns)
        v['pns_not_in_glb'] = sorted(p for p in pns if glb_pns and p not in glb_pns)
        v['pns_not_in_bom'] = sorted(p for p in pns if p not in bom_pns)
        v['unknown_material_pns'] = meta.get('unknown_material_pns')
        v['blender'] = meta.get('blender')
        v['samples'] = meta.get('samples')
        if assets:
            base = png[:-4]
            cand = [f for f in os.listdir(assets) if f.startswith('render_' + base)]
            v['assets'] = cand
        res['views'].append(v)
    res['n_views'] = len(res['views'])
    res['all_views_glb_ok'] = all(v['glb_ok'] for v in res['views'])
    res['all_views_png_ok'] = all(v['png_sha_matches_manifest'] for v in res['views'])
    json.dump(res, open(outp, 'w', encoding='utf-8'), indent=1)
    for c in res['checks']:
        print(('OK  ' if c['ok'] else 'FAIL') + ' ' + c['check'] + ' :: ' + str(c['detail']))
    print('views', res['n_views'], 'all glb ok', res['all_views_glb_ok'], 'all png ok', res['all_views_png_ok'])
    print('GLB part numbers', res.get('glb_pn_count'), 'BOM part numbers', res['bom_pn_count'])
    print('BOM pns not in GLB:', res.get('bom_pns_not_in_glb'))
    for v in res['views']:
        print(f"{v['view']:<12} {v['png']:<16} png={v['png_sha16']} man={v['png_sha_matches_manifest']} glb={v['glb_ok']} "
              f"bom={v['bom_ok']} pns={v['n_pns']} not_in_glb={v['pns_not_in_glb'][:5]} not_in_bom={v['pns_not_in_bom'][:5]} "
              f"unk_mat={v['unknown_material_pns']} assets={v.get('assets')}")
    print('wrote', outp)


if __name__ == '__main__':
    main()
