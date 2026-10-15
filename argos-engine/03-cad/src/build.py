"""Build the full part registry from the interface-driven parameters, iterate the pivot onto the mid-burn CG,
and pose the assembly (CAD v3, 2026-10-12).

Pivot placement (gimbal_trade.py v1 decision, lead 2026-10-12): the gimbal pivot is the origin; z_head_mid
(head mid-plane above the pivot) is iterated so that the mid-burn CG of the 'engine' group (everything that
moves with Rx(alpha)Ry(beta), incl. the collar, pins, levers and the engine half of the feed hose) lies on
z = 0.  The engine body moves rigidly with z_head_mid while the collar/levers stay on the pivot plane, so a
mass-weighted Newton step converges in one or two rebuilds; the residual is logged.
"""
from __future__ import annotations
import sys, math, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "04-fea" / "src"))
import config
import layout
import engmat
from partlib import Registry
from geom import apply, T_rot, T_trans, mass_props, bbox
import tvc_kinematics as tk


def _one_build(P, include):
    S = layout.stations(P)
    reg = Registry()
    import parts_engine, parts_gimbal
    info = parts_engine.build_engine_parts(P, S, reg, engmat)
    S = parts_gimbal.build_gimbal_parts(P, S, reg, info)
    if "feed" in include:
        import parts_feed
        parts_feed.build_feed_parts(P, S, reg)
        if (P.get("v35_bleed") or {}).get("v"):            # v3.5 (run 6): A1 head-end bleed modelled (parts_bleed.py)
            import parts_bleed
            S = parts_bleed.build_bleed_parts(P, S, reg)
    if "misc" in include:
        import parts_misc
        parts_misc.build_misc_parts(P, S, reg)
    return S, reg


_MP_CACHE = {}


def part_mass(p):
    """(mass kg, CG local mm, I about CG kg m2, tag) of one instance of part p (local frame)."""
    key = (p.pn, id(p.shape))
    if key in _MP_CACHE:
        return _MP_CACHE[key]
    if p.mass_each_kg is not None:
        bb = bbox(p.shape)
        cg = np.array([(bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2, (bb[2] + bb[5]) / 2])
        ext = np.array([bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]]) * 1e-3
        m = p.mass_each_kg
        I = m / 12.0 * np.diag([ext[1] ** 2 + ext[2] ** 2, ext[0] ** 2 + ext[2] ** 2, ext[0] ** 2 + ext[1] ** 2])  # uniform box
        res = (m, cg, I, "COTS mass (" + (p.mass_tag or "untagged") + "); CG and inertia of a uniform bounding box")
    else:
        mp = mass_props(p.shape, engmat.rho(p.material))
        res = (mp["m"], np.array(mp["cg"]) * 1e3, np.array(mp["I_cg"]), f"CAD volume x rho({p.material})")
    _MP_CACHE[key] = res
    return res


_ENGINE_ITEMS = ("stud", "hi_ir", "w_hi")              # lever-joint items fixed to the engine lever
_HORN_ITEMS = ("lo_ir", "w_lo1", "w_lo2", "screw")     # horn-joint items fixed to the horn


def group_of(g):
    """Mass/colour group of a placement tag: engine / ring / fixed / horn / pushrod / hose / line / lock."""
    if g.startswith("engine"):
        return "engine"
    if g.startswith("pushrod:"):
        item = g.split(":")[2]
        if item in _ENGINE_ITEMS:
            return "engine"
        if item in _HORN_ITEMS:
            return "horn"
        return "pushrod"
    return g.split(":")[0]


def body_of(g, idx=0, pn=""):
    """Rigid-body identity of a placement (instances of the same body never move relative to each other):
    engine, ring, fixed, horn:i, rod:i; flexible items are their own body."""
    if g.startswith("engine"):
        return "engine"
    if g in ("fixed", "lock"):
        return "fixed"
    if g == "ring":
        return "ring"
    if g.startswith("horn:"):
        return g
    if g.startswith("pushrod:"):
        _, k, item = g.split(":")
        if item in _ENGINE_ITEMS:
            return "engine"
        if item in _HORN_ITEMS:
            return f"horn:{k}"
        return f"rod:{k}"
    return f"{g}:{pn}#{idx}"


def mass_ledger(reg, P, state="mid", S=None):
    """Per-instance rows (pn, idx, group, m, cg_mm (engine frame, neutral), I_cg (rotated)).  Grain mass scaled
    for the burn state: 'wet' (fresh grain), 'mid' (half the max-thrust fuel burnt), 'burnout', 'nograin'.
    Flexible feed items (group hose/line) are split engine/fixed by the 'split' attribute set in parts_feed."""
    m_burnt = P["fuel_burnt_max"]["v"] or 0.0
    m_grain0 = sum(part_mass(p)[0] * p.qty for p in reg if p.pn.startswith("ENG-GR-"))
    f = {"wet": 1.0, "mid": (m_grain0 - 0.5 * m_burnt) / m_grain0 if m_grain0 else 1.0,
         "burnout": (m_grain0 - m_burnt) / m_grain0 if m_grain0 else 1.0, "nograin": 0.0}[state]
    rows = []
    fr = None
    if S is not None and "tvc" in S:
        import parts_gimbal
        fr = parts_gimbal.tvc_pose_frames(S, 0.0, 0.0)
    for p in reg:
        m, cg_l, I_l, tag = part_mass(p)
        if p.pn.startswith("ENG-GR-"):
            m, I_l = m * f, I_l * f
            tag += f"; burn state '{state}' factor {f:.3f} (port growth assumed axisymmetric, CG fixed)"
        for i, (T, gname) in enumerate(p.placements):
            if gname == "lock":
                continue
            if fr is not None and gname.startswith("horn:"):
                T = fr[int(gname.split(":")[1])]["horn"]
            elif fr is not None and gname.startswith("pushrod:"):
                _, k, item = gname.split(":")
                T = fr[int(k)][item]
            R = T[:3, :3]
            cg = (T @ np.append(cg_l, 1.0))[:3]
            grp = group_of(gname)
            if grp in ("hose", "line"):           # flexible: split between the moving and the fixed end
                fe = getattr(p, "split_engine", 0.5)
                rows.append(dict(pn=p.pn, idx=i, group="engine", group_raw=gname, m=m * fe, cg=cg, I=R @ I_l @ R.T * fe, tag=tag + f"; {fe:.2f} to engine"))
                rows.append(dict(pn=p.pn, idx=i, group="fixed", group_raw=gname, m=m * (1 - fe), cg=cg, I=R @ I_l @ R.T * (1 - fe), tag=tag + f"; {1-fe:.2f} to fixed"))
                continue
            rows.append(dict(pn=p.pn, idx=i, group=grp, group_raw=gname, m=m, cg=cg, I=R @ I_l @ R.T, tag=tag))
    return rows, m_grain0


def group_props(rows, groups, about=(0, 0, 0)):
    sel = [r for r in rows if r["group"] in groups]
    M = sum(r["m"] for r in sel)
    if M == 0:
        return dict(m=0.0, cg_mm=[0.0, 0.0, 0.0], I_cg=np.zeros((3, 3)), I_about=np.zeros((3, 3)), n=0)
    cg = sum(r["m"] * r["cg"] for r in sel) / M
    I = np.zeros((3, 3))
    for r in sel:
        d = (r["cg"] - cg) * 1e-3
        I += r["I"] + r["m"] * (d @ d * np.eye(3) - np.outer(d, d))
    d0 = (cg - np.array(about, float)) * 1e-3
    I_about = I + M * (d0 @ d0 * np.eye(3) - np.outer(d0, d0))
    return dict(m=M, cg_mm=cg.tolist(), I_cg=I, I_about=I_about, n=len(sel))


def _on_pivot(pn):
    """Engine-group items that stay on the pivot plane when z_head_mid changes (collar, pins, studs ...)."""
    return pn in ("ENG-GM-01", "ENG-GM-02", "ENG-GM-04", "ENG-GM-06", "ENG-GM-18", "ENG-GM-19", "ENG-HW-22-IR", "ENG-HW-21", "ENG-EL-06")


def build(include=("engine", "gimbal", "feed", "misc"), iterate_cg=True, tol_mm=0.2, overrides=None):
    """overrides: {param: value} applied after config.build() (trade studies; logged in clog['overrides'])."""
    P, clog = config.build()
    for k, val in (overrides or {}).items():
        clog["overrides"].append({"param": k, "from": "build(overrides=...)", "old": P.get(k, {}).get("v"), "new": val,
                                  "why": "v3.4 baseline (config.V34_ON)" if (k in config.V34_ON and config.V34_ON[k] == val) else "trade study"})
        base = k in config.V34_ON and config.V34_ON[k] == val          # v3.4 baseline switch (not a trade study)
        P[k] = {"v": val, "tag": "DESIGN" if base else "TRADE", "src": "config.V34_ON (v3.4 baseline)" if base else "build.py overrides (trade study)"}
    hist = []
    t0 = time.time()
    S, reg = _one_build(P, include)
    for it in range(5):
        rows, mg0 = mass_ledger(reg, P, "mid", S)
        eng = group_props(rows, ("engine",))
        m_mov = sum(r["m"] for r in rows if r["group"] == "engine" and not _on_pivot(r["pn"]))
        hist.append({"iter": it, "z_head_mid_mm": round(P["z_head_mid"]["v"] * 1e3, 3), "cg_mid_mm": [round(c, 3) for c in eng["cg_mm"]],
                     "m_engine_group_kg": round(eng["m"], 4), "m_moving_with_head_kg": round(m_mov, 4), "t_s": round(time.time() - t0, 1)})
        if not iterate_cg or abs(eng["cg_mm"][2]) < tol_mm or (P.get("pivot_frozen") or {}).get("v"):
            break                                # v3.4.1 rev B: config.V34_ON may freeze the pivot (z_head_mid given)
        dz = -eng["cg_mm"][2] * eng["m"] / m_mov
        P["z_head_mid"] = {"v": P["z_head_mid"]["v"] + dz * 1e-3, "tag": "DERIVED",
                           "src": "build.py CG iteration: pivot on the mid-burn CG of the engine group (checks/cg_iteration.json)"}
        S, reg = _one_build(P, include)
    S["cg_iteration"] = hist
    return P, S, reg, clog


# --------------------------------------------------------------------------------------------- posing
def R4(alpha, beta):
    T = np.eye(4)
    T[:3, :3] = tk.R_pose(alpha, beta)
    return T


def group_T(group, alpha=0.0, beta=0.0):
    if group == "engine":
        return R4(alpha, beta)
    if group == "ring":
        return T_rot("x", alpha)
    return np.eye(4)


def posed_instances(reg, S, alpha=0.0, beta=0.0, explode=0.0, groups=None, with_lock=False):
    """[(pn, idx, group, posed shape, rigid body)] for every instance at the engine pose (alpha, beta) in deg."""
    import parts_gimbal
    fr = parts_gimbal.tvc_pose_frames(S, alpha, beta)
    out = []
    for p in reg:
        for i, (T, g) in enumerate(p.placements):
            if g == "lock" and not with_lock:
                continue
            grp = group_of(g)
            if groups is not None and grp not in groups:
                continue
            if g.startswith("horn:"):
                Tp = fr[int(g.split(":")[1])]["horn"]
            elif g.startswith("pushrod:"):
                _, k, item = g.split(":")
                Tp = fr[int(k)][item]
            elif grp in ("hose", "line"):
                import parts_feed
                sh = parts_feed.posed_flex(p, S, alpha, beta, i)
                if sh is not None:
                    out.append((p.pn, i, grp, sh, body_of(g, i, p.pn)))
                continue
            else:
                Tp = group_T(grp if grp != "lock" else "fixed", alpha, beta) @ T
            if explode:
                Tp = _explode(p, Tp, explode)
            out.append((p.pn, i, grp, apply(p.shape, Tp), body_of(g, i, p.pn)))
    return out


def _explode(p, T, f):
    """Exploded-view offsets (mm x f) by part family: for the exploded render/GLB only."""
    pn = p.pn
    off = np.zeros(3)
    c = T[:3, 3]
    radial = np.array([c[0], c[1], 0.0])
    rn = radial / (np.linalg.norm(radial) + 1e-9)
    fam = pn.split("-")[1]
    tail = pn.split("-")[2]
    num = int(tail) if tail.isdigit() else 0
    if fam == "TC":
        off[2] = {1: 0, 2: 90, 3: 60, 4: 140, 5: 120, 6: 30, 7: -20, 8: -60, 9: -170, 10: 50, 11: 150,
                  12: 210, 13: 230, 14: 220, 15: 200, 16: 180, 17: 165}.get(num, 0)
    elif fam == "NZ":
        off[2] = -120 - 15 * num
    elif fam == "GR":
        off += np.array([110.0, 0.0, 20.0 - 40.0 * num])
    elif fam == "IG":
        off[2] = 140
        off += rn * 40
    elif fam == "GM":
        if num in (1, 2):
            off += np.array([0.0, 30.0 if num == 1 else -30.0, -10.0])
        elif num in (3, 5, 7):
            off += rn * 25
        elif num in (4, 6):
            off += rn * 15
        elif num == 8:
            off += rn * 60
        elif num == 9:
            off[2] = 90
        elif num in (10, 11, 12):
            off[2] = -90
        else:
            off += rn * 50 + np.array([0.0, 0.0, -40.0])
    elif fam in ("HW", "EL"):
        off += rn * 45
    elif fam in ("FD", "GS"):
        off[2] = 80
    return T_trans(*(off * f)) @ T


def pose_list(P, S=None):
    """Gimbal configurations exported and checked: neutral, +/- range per axis, the four combined corners of
    the commanded vector (norm = range), and the conical stop in 8 directions."""
    rng = P["gimbal_range_deg"]["v"]
    stop = P["gimbal_stop_deg"]["v"]
    poses = [("neutral", 0.0, 0.0)]
    for nm, a, b in (("alpha+", rng, 0.0), ("alpha-", -rng, 0.0), ("beta+", 0.0, rng), ("beta-", 0.0, -rng)):
        poses.append((nm, float(a), float(b)))
    for d in (45, 135, 225, 315):
        a, b = tk.cone_to_ab(rng, d)
        poses.append((f"combined{d:03d}", a, b))
    for d in range(0, 360, 45):
        a, b = tk.cone_to_ab(stop, d)
        poses.append((f"stop{d:03d}", a, b))
    if S is not None and "feed" in S:
        # v3.4.1 rev B: the stop toward the fixed hose end (closest point of the FD-07B sleeve axis to the engine axis); the 8 stop
        # directions above miss it by about 22 deg (about 0.8 mm of reach at the sleeve height)
        f = S["feed"]
        Fq, cd = np.asarray(f["Fq"], float), np.asarray(f["cdir"], float)
        s_ = float(np.clip(-(Fq[:2] @ cd[:2]) / (cd[:2] @ cd[:2]), 0.0, 15.0))
        pc = Fq + s_ * cd
        az_t = math.degrees(math.atan2(pc[1], pc[0])) % 360.0
        best = None
        for dd in np.arange(0.0, 360.0, 0.25):
            a, b = tk.cone_to_ab(stop, float(dd))
            v = tk.R_pose(a, b) @ np.array([0.0, 0.0, 1.0])
            err = abs((math.degrees(math.atan2(v[1], v[0])) - az_t + 180.0) % 360.0 - 180.0)
            if best is None or err < best[0]:
                best = (err, float(dd), a, b)
        poses.append(("stopFD07B", best[2], best[3]))
    return poses
