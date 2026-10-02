"""fea_model.py — Modelo FEA sobre fea_core: interfaces (Winkler / cuerpo rígido, unilaterales),
cuerpos rígidos, iteración de contacto (conjunto activo) y post-proceso de tensiones."""
from __future__ import annotations

import time

import numpy as np
import scipy.sparse as sp
from scipy.spatial import cKDTree

import fea_core as fc

# ---------------------------------------------------------------------------
# Consultas de geometría CAD (build123d / OCP) y selección de facetas
# ---------------------------------------------------------------------------


def cad_cylinders(part):
    """Caras cilíndricas del sólido: lista de dict(r, axis (3,), point (3,))."""
    from build123d import GeomType
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    out = []
    for f in part.faces():
        if f.geom_type != GeomType.CYLINDER:
            continue
        c = BRepAdaptor_Surface(f.wrapped).Cylinder()
        ax = c.Axis()
        d, l = ax.Direction(), ax.Location()
        out.append({"r": c.Radius(), "axis": np.array([d.X(), d.Y(), d.Z()]),
                    "point": np.array([l.X(), l.Y(), l.Z()])})
    return out


def find_cyl(cyls, r, axis, near=None, tol_r=0.02, max_dist=None):
    """Cilindros de radio r (±tol) con eje paralelo a `axis`; agrupa coaxiales. Devuelve
    lista de (point, axis) únicos; si `near` se da, ordena por distancia al eje."""
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    hits = []
    for c in cyls:
        if abs(c["r"] - r) > tol_r or abs(abs(c["axis"] @ axis) - 1) > 1e-6:
            continue
        pt = c["point"] - (c["point"] @ axis) * axis           # proyección ⟂ eje
        if not any(np.linalg.norm(pt - h) < 1e-3 for h in hits):
            hits.append(pt)
    if near is not None:
        near = np.asarray(near, float)
        dist = [np.linalg.norm((near - h) - ((near - h) @ axis) * axis) for h in hits]
        hits = [h for _, h in sorted(zip(dist, hits), key=lambda t: t[0])]
        if max_dist is not None:
            hits = [h for h, d_ in zip(hits, sorted(dist)) if d_ <= max_dist]
    return [(h, axis) for h in hits]


def sel_plane(S, normal, offset, tol=0.05, region=None, body=None, cos_tol=0.995):
    """Facetas sobre el plano n·x = offset con normal saliente ≈ n."""
    n = np.asarray(normal, float) / np.linalg.norm(normal)
    m = (S.fnormal @ n > cos_tol) & (np.abs(S.fcent @ n - offset) < tol)
    if body is not None and S.fbody is not None:
        m &= S.fbody == body
    if region is not None:
        m &= region(S.fcent)
    return np.flatnonzero(m)


def radial(Xc, point, axis):
    v = Xc - point
    v = v - np.outer(v @ axis, axis)
    return np.linalg.norm(v, axis=1), v


def sel_cyl(S, point, axis, r, tol=None, hole=True, region=None, body=None):
    """Facetas sobre el cilindro (radio r alrededor del eje) — agujero: normal hacia el eje."""
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    tol = tol if tol is not None else 0.06 * r + 0.15
    d, v = radial(S.fcent, np.asarray(point, float), axis)
    rad = v / np.maximum(d, 1e-12)[:, None]
    cosn = np.einsum("ij,ij->i", S.fnormal, rad)
    m = (np.abs(d - r) < tol) & ((cosn < -0.6) if hole else (cosn > 0.6))
    if body is not None and S.fbody is not None:
        m &= S.fbody == body
    if region is not None:
        m &= region(S.fcent)
    return np.flatnonzero(m)


def sel_annulus(S, normal, offset, center, r0, r1, tol=0.05, body=None):
    n = np.asarray(normal, float) / np.linalg.norm(normal)
    c = np.asarray(center, float)

    def reg(Xc):
        d, _ = radial(Xc, c, n)
        return (d >= r0 - 1e-6) & (d <= r1 + 1e-6)
    return sel_plane(S, n, offset, tol=tol, region=reg, body=body)


def cos_bearing(direction):
    """Tracción de apoyo cosenoidal (perno que empuja la pared del agujero en `direction`):
    t = p0·max(0, −n·d)·(−n) con p0 = 1 (se escala después)."""
    d = np.asarray(direction, float) / np.linalg.norm(direction)

    def t(Xq, n):
        c = np.maximum(0.0, -(n @ d))
        tt = -n * c[:, None]
        return np.broadcast_to(tt[:, None, :], Xq.shape).copy()
    return t


def uniform_traction(vec):
    v = np.asarray(vec, float)

    def t(Xq, n):
        return np.broadcast_to(v, Xq.shape).copy()
    return t


def force_of(S, f):
    """Resultante (3,) de un vector de cargas nodales (solo gdl FEM)."""
    return f[:S.ndof_fem].reshape(-1, 3).sum(axis=0)


def moment_of(S, f, about):
    F = f[:S.ndof_fem].reshape(-1, 3)
    return np.cross(S.Xall - np.asarray(about), F).sum(axis=0)


# ---------------------------------------------------------------------------
# Modelo
# ---------------------------------------------------------------------------

class Interface:
    """Resortes de superficie. kind='ground' (contra suelo, opcional desplazamiento de
    referencia) o 'rigid' (contra un cuerpo rígido). unilateral → solo compresión."""

    def __init__(self, name, facets, k, kind="ground", rigid=None, k_t=0.0, unilateral=True, zone=True, axis=None):
        self.name, self.facets, self.k, self.kind = name, np.asarray(facets), float(k), kind
        self.axis = axis
        self.rigid, self.k_t, self.unilateral, self.zone = rigid, k_t, unilateral, zone
        self.active = np.ones(len(self.facets), bool)
        if len(self.facets) == 0:
            raise ValueError(f"interfaz '{name}' sin facetas: revisar la selección geométrica")


class Model:
    def __init__(self, S: fc.P2Space, E, nu, n_print, body_names=("pieza",)):
        self.S, self.E, self.nu = S, E, nu
        self.n_print = np.asarray(n_print, float) / np.linalg.norm(n_print)
        self.body_names = list(body_names)
        self.rigids = {}
        self.interfaces = []
        self.fixed = np.zeros(0, int)
        self.zones = []                 # facetas de aplicación de carga / apoyo (zonas excluidas)
        self.K0 = None
        self.pre = None
        self.static_K = None            # resortes bilaterales siempre presentes
        self.n_print_body = None        # dirección Z de impresión por cuerpo (si hay varios)
        self.P = None

    # --- construcción ---
    def add_rigid(self, name, xref, fixed_local=()):
        if self.K0 is not None:
            raise RuntimeError("agregar cuerpos rígidos antes de assemble()")
        dofs = self.S.add_extra(6)
        self.rigids[name] = {"dofs": dofs, "xref": np.asarray(xref, float)}
        self.fixed = np.concatenate([self.fixed, dofs[list(fixed_local)]]).astype(int)
        return dofs

    def assemble(self):
        t0 = time.time()
        self.K0 = self.S.stiffness(self.E, self.nu)
        self.P = self.S.coarse_prolongation()
        self.t_asm = time.time() - t0

    def fix_facets(self, facets, comps=(0, 1, 2), zone=False):
        if len(facets) == 0:
            raise ValueError("fix_facets: selección vacía")
        nodes = self.S.facet_nodes(facets)
        d = (3 * nodes[:, None] + np.asarray(comps)).ravel()
        self.fixed = np.unique(np.concatenate([self.fixed, d])).astype(int)
        if zone:
            self.zones.append(np.asarray(facets))

    def add_static(self, K):
        self.static_K = K if self.static_K is None else self.static_K + K

    def base_matrix(self, extra_K=None):
        K = self.K0.copy()
        if self.static_K is not None:
            K = K + self.static_K
        if extra_K is not None:
            K = K + extra_K
        for itf in self.interfaces:
            K = K + self.interface_matrix(itf)
        return K

    def add_interface(self, itf: Interface):
        self.interfaces.append(itf)
        if itf.zone:
            self.zones.append(itf.facets)
        return itf

    def interface_matrix(self, itf, active=None):
        a = itf.active if active is None else active
        f = itf.facets[a]
        if itf.kind == "rigid":
            r = self.rigids[itf.rigid]
            return self.S.rigid_coupling(f, itf.k, r["dofs"], r["xref"], k_t=itf.k_t, axis=itf.axis)
        return self.S.spring_matrix(f, itf.k, k_t=itf.k_t, axis=itf.axis)

    def itf_normals(self, itf):
        n = self.S.fnormal[itf.facets]
        if itf.axis is None:
            return n
        pt, ax = np.asarray(itf.axis[0], float), np.asarray(itf.axis[1], float)
        ax = ax / np.linalg.norm(ax)
        v = self.S.fcent[itf.facets] - pt
        v = v - np.outer(v @ ax, ax)
        r = -v / np.linalg.norm(v, axis=1, keepdims=True)
        return r if np.einsum("ij,ij->i", r, n).mean() >= 0 else -r

    def gaps(self, itf, u):
        uc = self.S.facet_values(u, itf.facets)
        if itf.kind == "rigid":
            r = self.rigids[itf.rigid]
            q = u[r["dofs"]]
            uc = uc - (q[:3][None, :] + np.cross(q[3:][None, :], self.S.fcent[itf.facets] - r["xref"]))
        return np.einsum("ij,ij->i", uc, self.itf_normals(itf))

    # --- solución con contacto unilateral ---
    def solve(self, f, extra_K=None, extra_f=None, init_active=None, maxit=15, rtol=1e-7, log=None, change_tol=0.002):
        S = self.S
        if init_active:
            for itf in self.interfaces:
                if itf.name in init_active and itf.unilateral:
                    itf.active = init_active[itf.name].copy()
        else:
            for itf in self.interfaces:
                itf.active[:] = True
        rhs = f.copy() if extra_f is None else f + extra_f
        hist, u, info = [], None, {}
        seen = []
        t0 = time.time()
        cg_total = 0
        for it in range(maxit):
            K = self.base_matrix(extra_K)
            rebuild = self.pre is None or getattr(self, "_last_cg", 0) > getattr(self, "cg_rebuild", 60)
            u, info, pre = fc.solve_spd(K, rhs, self.fixed, self.P, x0=u, rtol=rtol,
                                        pre=None if rebuild else self.pre, maxiter=600)
            self._last_cg = info["cg_iters"]
            if info["cg_flag"] != 0:                                 # no convergió: continuar desde u con un precondicionador nuevo
                u, info, pre = fc.solve_spd(K, rhs, self.fixed, self.P, x0=u, rtol=rtol,
                                            pre=None if not rebuild else pre, maxiter=3000)
            self.pre = pre
            cg_total += info["cg_iters"]
            changed = 0
            state, old = [], []
            for itf in self.interfaces:
                if not itf.unilateral:
                    continue
                g = self.gaps(itf, u)
                new = g > 0.0
                changed += int((new != itf.active).sum())
                old.append((itf, itf.active.copy()))
                itf.active = new
                state.append(new.copy())
            hist.append(changed)
            if log:
                log(f"      contacto it {it}: cambios {changed}, CG {info['cg_iters']} it")
            n_uni = sum(len(i.facets) for i in self.interfaces if i.unilateral)
            if changed <= max(2, change_tol * n_uni):
                for itf, a in old:                                   # u es consistente con el conjunto previo
                    itf.active = a
                accepted = changed
                break
            key = np.concatenate(state) if state else np.zeros(0, bool)
            if any(np.array_equal(key, s) for s in seen):          # ciclo → resolver con el último conjunto
                accepted = None
                break
            seen.append(key)
        else:
            accepted = None
        if accepted is None:                                         # solución final con el conjunto activo final
            K = self.base_matrix(extra_K)
            u, info, pre = fc.solve_spd(K, rhs, self.fixed, self.P, x0=u, rtol=rtol, pre=self.pre, maxiter=3000)
            cg_total += info["cg_iters"]
        info.update({"contact_iters": len(hist), "contact_changes": hist, "cg_total": cg_total,
                     "case_s": time.time() - t0, "converged_contact": accepted is not None,
                     "residual_changes_accepted": accepted})
        self._last_extra = (extra_K, extra_f)
        return u, info

    def interface_forces(self, u, extra=None):
        """Resultante sobre la pieza de cada interfaz: dict(name → {F, active_frac, p_max})."""
        out = {}
        S = self.S
        for itf in self.interfaces:
            Ki = self.interface_matrix(itf)
            fi = -(Ki @ u)
            F = fi[:S.ndof_fem].reshape(-1, 3)
            Fsum = F.sum(axis=0)
            g = self.gaps(itf, u)
            p = itf.k * np.where(itf.active, g, 0.0)
            w = np.linalg.norm(F, axis=1)
            cen = (S.Xall * w[:, None]).sum(0) / max(w.sum(), 1e-30)
            out[itf.name] = {"F_N": Fsum.round(2).tolist(), "F_abs_N": float(np.linalg.norm(Fsum)),
                             "active_frac": float(itf.active.mean()), "p_max_MPa": float(p.max()) if len(p) else 0.0,
                             "centroid_mm": cen.round(1).tolist()}
        return out

    # --- post-proceso ---
    def stress_fields(self, u):
        S = self.S
        Sv = S.vertex_stress(u, self.E, self.nu)
        Sn = S.nodal_average(Sv)
        if self.n_print_body is not None and S.body is not None:
            nb = np.zeros(S.N, int)
            nb[S.T.ravel()] = np.repeat(S.body, 4)
            nvec = np.asarray(self.n_print_body, float)[nb]
            sZ = np.einsum("nij,ni,nj->n", Sn, nvec, nvec)
        else:
            sZ = fc.normal_stress(Sn, self.n_print)
        return {"S": Sn, "vm": fc.von_mises(Sn), "s1": fc.principal_max(Sn), "sZ": sZ,
                "u": u[:S.ndof_fem].reshape(-1, 3)[:S.N]}

    def zone_mask(self, r_ex, extra=()):
        """Nodos (vértices) a distancia ≤ r_ex de las facetas de aplicación de carga/apoyo."""
        S = self.S
        zl = list(self.zones) + [np.asarray(z) for z in extra]
        if not zl:
            return np.zeros(S.N, bool)
        zf = np.unique(np.concatenate(zl))
        pts = np.vstack([S.X[S.ftri[zf]].reshape(-1, 3), S.fcent[zf]])
        d, _ = cKDTree(pts).query(S.X, k=1)
        return d <= r_ex

    def summarize(self, fields, r_ex, body=0, extra_zones=()):
        S = self.S
        nb = np.zeros(S.N, int)
        if S.body is not None:
            nb[S.T.ravel()] = np.repeat(S.body, 4)
        sel = nb == body
        w = S.node_volume()
        excl = self.zone_mask(r_ex, extra_zones)
        out = {}
        for key in ("vm", "s1", "sZ"):
            v = fields[key]
            vb, wb = v[sel], w[sel]
            ok = sel & ~excl
            if not ok.any():
                ok = sel
            iarg = np.flatnonzero(sel)[np.argmax(vb)]
            iex = np.flatnonzero(ok)[np.argmax(v[ok])]
            out[key] = {"max": float(vb.max()), "p99": fc.weighted_percentile(vb, wb, 99.0),
                        "max_excl": float(v[iex]), "at_max_mm": S.X[iarg].round(1).tolist(),
                        "at_max_excl_mm": S.X[iex].round(1).tolist()}
        um = np.linalg.norm(fields["u"], axis=1)[sel]
        out["u_max_mm"] = float(um.max())
        out["excl_frac_vol"] = float(w[sel & excl].sum() / w[sel].sum())
        return out

    def region_summary(self, fields, r_ex, regions, extra_zones=()):
        """Por región (nombre → máscara(X (N,3)) → bool): σ máx. global, máx. fuera de zonas de
        carga/apoyo (máx*; None si la región entera cae dentro de r_excl), p99 y promedio de la región
        (ponderados por volumen) y ubicación del máx*."""
        S = self.S
        w = S.node_volume()
        excl = self.zone_mask(r_ex, extra_zones)
        out = {}
        for name, fn in regions.items():
            sel = np.asarray(fn(S.X), bool)
            if not sel.any():
                continue
            ok = sel & ~excl
            rec = {"n_nodos": int(sel.sum()), "frac_excluida": float(w[sel & excl].sum() / w[sel].sum())}
            for key in ("vm", "s1", "sZ"):
                v = fields[key]
                vv = v[ok] if ok.any() else v[sel]
                iex = (np.flatnonzero(ok) if ok.any() else np.flatnonzero(sel))[np.argmax(vv)]
                rec[key] = {"max": float(v[sel].max()), "max_excl": float(v[iex]) if ok.any() else None,
                            "p99": fc.weighted_percentile(v[sel], w[sel], 99.0),
                            "mean": float((v[sel] * w[sel]).sum() / w[sel].sum()),
                            "at_max_excl_mm": S.X[iex].round(1).tolist()}
            out[name] = rec
        return out


def mesh_quality(X, T):
    """Calidad γ = 3·r_in/r_circ (1 = regular) por tetraedro."""
    a, b, c, d = (X[T[:, i]] for i in range(4))
    vol = np.abs(np.einsum("ij,ij->i", np.cross(b - a, c - a), d - a)) / 6
    areas = sum(0.5 * np.linalg.norm(np.cross(q - p, r - p), axis=1)
                for p, q, r in ((a, b, c), (a, b, d), (a, c, d), (b, c, d)))
    r_in = 3 * vol / areas
    # circunradio
    A = np.stack([b - a, c - a, d - a], axis=1)
    rhs = 0.5 * np.stack([(b - a) ** 2, (c - a) ** 2, (d - a) ** 2], axis=1).sum(axis=2)
    cc = np.linalg.solve(A, rhs[..., None])[..., 0]
    r_c = np.linalg.norm(cc, axis=1)
    return 3 * r_in / r_c
