"""Add the mandatory ARTISTIC label to a Blender render (Combustion / 05-plume-cfd v2).
usage: python blender_caption.py IN.png OUT.png "title"
"""
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

img = mpimg.imread(sys.argv[1]); title = sys.argv[3] if len(sys.argv) > 3 else ''
h, w = img.shape[:2]
# caption band 0.80 in: title + the ARTISTIC label on two lines (v1 single line was cut at the right edge of the
# 1600 px final renders, found on visual check 2026-10-12)
band = 0.80; H = h / 150 + band
fig = plt.figure(figsize=(w / 150, H), dpi=150, facecolor='black')
ax = fig.add_axes([0, band / H, 1, (h / 150) / H]); ax.imshow(img); ax.axis('off')
fig.text(0.01, (band - 0.24) / H, title, color='0.9', fontsize=8)
fig.text(0.01, (band - 0.48) / H, 'ARTISTIC RENDER (Blender Cycles): appearance only. Colours, brightness, exposure and the '
         'soot-proxy emitter are chosen for illustration;', color='#ffb347', fontsize=6.5)
fig.text(0.01, (band - 0.68) / H, 'NOT a measurement or a validated radiation result. Traceable synthetic image: '
         'synth_photo (forward Abel, qualitative).', color='#ffb347', fontsize=6.5)
fig.savefig(sys.argv[2], dpi=150, facecolor='black'); plt.close(fig)
print('captioned', sys.argv[2])
