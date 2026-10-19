"""FEA3D F1 datasheet figures (pyvista offscreen; fea3d successor 2026-10-15).

Each figure: half-section (y > 0 removed unless stated) of the posed assembly, nodal field on the C3D10 corner-node surface, colour bar
with units, title with the case, the criterion and the field; governing nodes marked with their part MS.  mm, MPa.
usage: fig_f1.py SPEC_JSON   (list of figure specs, see main())
"""
from __future__ import annotations
import sys, json, math
from pathlib import Path
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import post_f1 as PF        # noqa: E402
import asm3d as A3          # noqa: E402
import pyvista as pv        # noqa: E402

pv.OFF_SCREEN = True
FIG = Path("/home/claude/work/fea3d/figs")
FOOT = "ARGOS H1 engine | FEA3D (CalculiX 2.21, C3D10) on CAD v3.5.1 (STEP 4ca22820c796b670) | SIM - not physical approval | asm v1.2 | fea3d 2026-10-19"


def nodal_fields(M, names, T, F, subs, sfy, sfu):
    """Node-wise envelope over the sub-cases: von Mises max, MS (yield, part_margins rules) min.  Arrays over mesh node ids."""
    nn = M.n_mesh + 1
    vmx = np.zeros(nn)
    ms = np.full(nn, np.inf)
    Sl = [PF.combine(F, "S", co) for co in subs]
    for nm in names:
        b = M.bodies[nm]
        nodes = b.noff + np.arange(len(b.X0))
        mat = b.mat
        Mt = A3.engmat.MATERIALS[mat]
        a1, a2 = PF.allowables(mat, T[nodes])
        brittle = mat in PF.BRITTLE
        T_char = Mt["T_char_C"]["v"] if "T_char_C" in Mt else None
        char = ((T[nodes] - 273.15) > T_char) if T_char is not None else np.zeros(len(nodes), bool)
        for S, Sm in Sl:
            v = PF.vm(S[nodes])
            vmx[nodes] = np.maximum(vmx[nodes], v)
            if brittle:
                s1, s3 = PF.principal(S[nodes])
                s3m = PF.principal(Sm[nodes])[1]
                sf = sfu if sfu else 1.5
                big = np.full(len(nodes), np.inf)
                mt = np.where(s1 > 0, a1 / (sf * np.maximum(s1, 1e-9)) - 1.0, np.inf) if a1 is not None else big
                mc = np.where(s3 < 0, a2 / (sf * np.maximum(-s3, 1e-9)) - 1.0, np.inf) if a2 is not None else big
                m_ = np.minimum(mt, mc)
                if char.any() and a2 is not None:
                    m_ = np.where(char, np.where(s3m < 0, a2 / (sf * np.maximum(-s3m, 1e-9)) - 1.0, np.inf), m_)
            else:
                m_ = a1 / (sfy * np.maximum(v, 1e-9)) - 1.0
            ms[nodes] = np.minimum(ms[nodes], m_)
    return vmx, ms


def surface(M, names, X, field, clip=True, bodies=None, deform=None, scale=0.0, clip_normal=(0, 1, 0)):
    pts, cells, vals = [], [], []
    off = 0
    for nm in names:
        if bodies and nm not in bodies:
            continue
        b = M.bodies[nm]
        g = b.noff + np.arange(len(b.X0))
        P = X[g].copy()
        if deform is not None and scale:
            P += scale * deform[g]
        T4 = b.T10[:, :4]
        c = np.hstack([np.full((len(T4), 1), 4), T4 + off]).ravel()
        pts.append(P)
        cells.append(c)
        vals.append(field[g])
        off += len(P)
    grid = pv.UnstructuredGrid(np.concatenate(cells), np.full(sum(len(c) // 5 for c in cells), pv.CellType.TETRA, np.uint8), np.vstack(pts))
    grid.point_data["f"] = np.concatenate(vals)
    if clip:
        grid = grid.clip(normal=tuple(clip_normal), origin=(0, 0, 0), invert=True)
    return grid.extract_surface(algorithm="dataset_surface")


def render(surf, title, cbar, out, clim, cmap="turbo", focus=None, dist=None, marks=(), size=(1400, 1700), view=(0, -1, 0), up=(0, 0, 1),
           below=None, above=None, n_colors=16):
    p = pv.Plotter(off_screen=True, window_size=size)
    p.set_background("white")
    sargs = dict(title=cbar, color="black", title_font_size=20, label_font_size=16, n_labels=6, fmt="%.3g", vertical=True,
                 position_x=0.86, position_y=0.12, height=0.7, width=0.06)
    p.add_mesh(surf, scalars="f", cmap=cmap, clim=clim, show_edges=False, scalar_bar_args=sargs, n_colors=n_colors,
               below_color=below, above_color=above, smooth_shading=False)
    p.add_mesh(surf.extract_feature_edges(feature_angle=35, boundary_edges=False, non_manifold_edges=False, manifold_edges=False),
               color="black", line_width=0.6, opacity=0.35)
    for x, lab in marks:
        p.add_point_labels(np.asarray([x]), [lab], point_size=14, point_color="magenta", font_size=18, text_color="black",
                           shape_color="white", shape_opacity=0.8, always_visible=True, render_points_as_spheres=True)
    p.add_text(title, position="upper_left", font_size=11, color="black")
    p.add_text(FOOT, position="lower_left", font_size=8, color="dimgray")
    if focus is not None:
        f = np.asarray(focus, float)
        d = dist or 40.0
        p.camera.focal_point = f
        p.camera.position = f - d * np.asarray(view, float) / np.linalg.norm(view)
        p.camera.up = up
    else:
        p.view_vector(tuple(-np.asarray(view, float)), viewup=up)
        p.camera.zoom(1.15)
    p.add_axes(line_width=2, labels_off=False, color="black")
    p.screenshot(str(out))
    p.close()
    return out


def main(spec_path):
    specs = json.loads(Path(spec_path).read_text())
    cache = {}
    for sp in specs:
        run, state = sp["run"], sp["state"]
        if run not in cache:
            cache.clear()
            M, meta = PF.load_model(run)
            cache[run] = (M, meta)
        M, meta = cache[run]
        names, body, T, X = PF.node_arrays(M, run, state)
        F = PF.load_fields(run, state)
        if sp.get("extra"):
            RF = PF.reactions(run, state, meta["steps"] or PF.STEPS_DEFAULT)
            PF.merge_extra(F, RF, sp["extra"], state)
        if sp["kind"] in ("vm", "ms"):
            if sp.get("lc3env"):
                env = dict(np.load(PF.RES / f"lc3_env_{run}.npz"))
                nn = M.n_mesh + 1
                vmx = env["vm"][:nn].astype(np.float64)
                ms = np.full(nn, np.inf)
                for nm in names:
                    b = M.bodies[nm]
                    g = b.noff + np.arange(len(b.X0))
                    a1, a2 = PF.allowables(b.mat, T[g])
                    if b.mat in PF.BRITTLE:
                        s1, s3 = env["s1"][g].astype(float), env["s3"][g].astype(float)
                        big = np.full(len(g), np.inf)
                        mt = np.where(s1 > 0, a1 / (2.0 * np.maximum(s1, 1e-9)) - 1, np.inf) if a1 is not None else big
                        mc = np.where(s3 < 0, a2 / (2.0 * np.maximum(-s3, 1e-9)) - 1, np.inf) if a2 is not None else big
                        ms[g] = np.minimum(mt, mc)
                    else:
                        ms[g] = a1 / (1.5 * np.maximum(vmx[g], 1e-9)) - 1.0
            else:
                cs = [c for c in PF.combos(state, [k[2:] for k in F if k.startswith("U_")]) if c[0] == sp["case"]][0]
                subs = cs[2] if "subcase" not in sp else [cs[2][sp["subcase"]]]
                vmx, ms = nodal_fields(M, names, T, F, subs, cs[3], cs[4])
            fld = vmx if sp["kind"] == "vm" else np.clip(ms, -1.0, 9.0)
        elif sp["kind"] == "u":
            cs = [c for c in PF.combos(state, [k[2:] for k in F if k.startswith("U_")]) if c[0] == sp["case"]][0]
            U, _ = PF.combine(F, "U", cs[2][0])
            fld = np.linalg.norm(U[:M.n_mesh + 1], axis=1) * 1e3          # micrometres
        else:
            raise ValueError(sp["kind"])
        dfm = None
        if sp.get("deform"):
            cs = [c for c in PF.combos(state, [k[2:] for k in F if k.startswith("U_")]) if c[0] == sp["case"]][0]
            dfm, _ = PF.combine(F, "U", cs[2][0])
        th = math.radians(sp.get("clip_theta", 90.0))          # cut plane through the engine axis at azimuth theta (deg)
        cn = (-math.sin(th), math.cos(th), 0.0)
        surf = surface(M, names, X, fld, clip=sp.get("clip", True), bodies=sp.get("bodies"), deform=dfm, scale=sp.get("scale", 0.0), clip_normal=cn)
        marks = [(np.asarray(m[0], float), m[1]) for m in sp.get("marks", [])]
        clim = sp.get("clim")
        if clim is None:
            v = surf.point_data["f"]
            clim = [float(np.nanmin(v)), float(np.nanpercentile(v, 99.7))]
        out = FIG / sp["out"]
        render(surf, sp["title"], sp["cbar"], out, clim, cmap=sp.get("cmap", "turbo"), focus=sp.get("focus"), dist=sp.get("dist"),
               marks=marks, size=tuple(sp.get("size", (1400, 1700))), view=tuple(sp.get("view", tuple(-c for c in cn))), up=tuple(sp.get("up", (0, 0, 1))),
               below=sp.get("below"), above=sp.get("above"), n_colors=sp.get("n_colors", 16))
        print("wrote", out, flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
