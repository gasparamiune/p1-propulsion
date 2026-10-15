"""Animation of plume2s frames: top half Mach number, bottom half numerical schlieren (or T).
(Combustion / 05-plume-cfd v1)   usage: python make_anim.py RUNDIR OUTSTEM [--bottom schlieren|T] [--xmax 30] [--rmax 4]
       [--label 'text'] [--fps 12]
Writes OUTSTEM.mp4 (H.264) and OUTSTEM.gif via ffmpeg; frame PNGs go to RUNDIR/anim_png/.
"""
from __future__ import annotations
import glob, json, os, subprocess, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plume2s as P
from post_plume import gradient_xr


def main():
    run = sys.argv[1]; stem = sys.argv[2]
    opt = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    bottom = opt('--bottom', 'schlieren'); xmax = float(opt('--xmax', 30)); rmax = float(opt('--rmax', 4))
    label = opt('--label', ''); fps = int(opt('--fps', 12))
    info = json.load(open(os.path.join(run, 'run.json')))
    J, pts, Rbody = P.load_geometry()
    g = P.Grid(pts, Rbody, level=info['args']['level'])
    De = g.De; X = g.X / De; R = g.R / De
    solid = g.region == 3
    frames = sorted(glob.glob(os.path.join(run, 'frame_*.npz')))
    pdir = os.path.join(run, 'anim_png'); os.makedirs(pdir, exist_ok=True)
    for k, fn in enumerate(frames):
        d = np.load(fn)
        M = np.ma.masked_where(solid, d['M']); T = np.ma.masked_where(solid, d['T'])
        fig, ax = plt.subplots(figsize=(12, 12 * 2 * rmax / (xmax + 2) + 0.8))
        ax.pcolormesh(X, R, M, cmap='turbo', norm=colors.Normalize(0, 4), shading='flat', rasterized=True)
        if bottom == 'T':
            ax.pcolormesh(X, -R, T, cmap='inferno', norm=colors.Normalize(250, 3000), shading='flat', rasterized=True)
        else:
            gx, gr = gradient_xr(g.xc, g.rc, d['rho'].astype(float))
            s = np.hypot(gx, gr); s[solid] = 0
            sch = np.exp(-12.0 * s / max(np.percentile(s[~solid], 99.7), 1e-9))
            ax.pcolormesh(X, -R, np.ma.masked_where(solid, sch), cmap='gray', norm=colors.Normalize(0, 1), shading='flat',
                          rasterized=True)
        xw = g.X[:g.Nn + 1, g.jc] / De; rw = g.R[:g.Nn + 1, g.jc] / De
        xb = g.X[:g.Nn + 1, g.js] / De; rb = g.R[:g.Nn + 1, g.js] / De
        for sgn in (1, -1):
            ax.fill(np.concatenate([xw, xb[::-1]]), sgn * np.concatenate([rw, rb[::-1]]), color='0.55', ec='k', lw=0.4)
        ax.set_xlim(-2, xmax); ax.set_ylim(-rmax, rmax); ax.set_aspect('equal')
        ax.set_xlabel('x / De'); ax.set_ylabel('r / De')
        fr = float(d['frac']) if 'frac' in d.files else float('nan')
        ax.set_title(f"{label}   t = {float(d['t'])*1e3:6.3f} ms   throttle {fr*100:5.1f} %   "
                     f"top: Mach (0-4)   bottom: {'T 250-3000 K' if bottom == 'T' else 'numerical schlieren'}",
                     loc='left', fontsize=8)
        fig.savefig(os.path.join(pdir, f'f_{k:04d}.png'), dpi=110, bbox_inches='tight'); plt.close(fig)
    mp4 = stem + '.mp4'; gif = stem + '.gif'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(fps), '-i', os.path.join(pdir, 'f_%04d.png'),
                    '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', mp4],
                   check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', mp4, '-vf',
                    f'fps={fps},scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=160[p];[s1][p]paletteuse=dither=bayer',
                    gif], check=True)
    print(json.dumps(dict(frames=len(frames), mp4=mp4, gif=gif, mp4_MB=os.path.getsize(mp4) / 1e6,
                          gif_MB=os.path.getsize(gif) / 1e6)))


if __name__ == '__main__':
    main()
