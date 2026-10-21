#!/opt/engine-venv/bin/python -I
"""REV-DS-1: mean absolute RGB difference (0-255) between each datasheet render asset and its
v3.5.2 render PNG, both composited on white, trimmed to content, resized to the asset size.
Provenance of the picture only, not a check of what it shows. usage: asset_diff.py <assets> <renders> <out.json>"""
import json, sys
from PIL import Image, ImageChops
A, R, O = sys.argv[1], sys.argv[2], sys.argv[3]
def load(p):
    im = Image.open(p)
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA'); bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); im = bg
    im = im.convert('RGB')
    diff = ImageChops.difference(im, Image.new('RGB', im.size, (255, 255, 255)))
    bb = diff.convert('L').point(lambda v: 255 if v > 12 else 0).getbbox()
    return im.crop(bb) if bb else im
res = {}
import os
for f in sorted(os.listdir(A)):
    if not f.startswith('render_'):
        continue
    base = f[len('render_'):].rsplit('.', 1)[0]
    rp = os.path.join(R, base + '.png')
    if not os.path.isfile(rp):
        res[f] = 'no render png'; continue
    a = load(os.path.join(A, f)); r = load(rp).resize(a.size, Image.LANCZOS)
    d = ImageChops.difference(a, r)
    h = d.histogram(); n = a.size[0] * a.size[1] * 3
    s = sum((i % 256) * h[i] for i in range(len(h)))
    res[f] = round(s / n, 2)
json.dump({'method': __doc__.split('\n')[1].strip(), 'results': res}, open(O, 'w'), indent=1)
print(json.dumps(res))
