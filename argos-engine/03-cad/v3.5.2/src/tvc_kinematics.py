"""TVC packaging geometry and exact linkage kinematics (CAD v3, 2026-10-12).  Units: mm, deg unless noted.

One module feeds the CAD (parts_gimbal.py), the posed assembly (build.py), the checks and the calcs, so the
servo frames, lever points and pushrod length exist in exactly one place.

Layout (engine frame: origin = gimbal pivot, +Z forward, +X outer axis, +Y inner axis):
  * Each TVC servo (electronics.json body L x W x H, H reserved 40.3) stands below the gimbal ring with its body
    length L vertical, its width W radial and its output shaft TANGENTIAL; the box is centred on its own radial
    line at azimuth theta_c so that its outer corners touch the radius R_lim (= bay radius - static wall gap).
    The body inner face is then u_in = sqrt(R_lim^2 - (H/2)^2) - W.
  * The aluminium horn points radially inward (r_h) at neutral; a fixed-length dog-bone pushrod (spherical
    plain bearings both ends) runs vertically from the horn eye up to the lever eye on the engine collar.
  * Lever azimuths phi = 135 / 225 deg: 90 deg apart (orthogonal, equal authority), clear of the yoke posts
    (0/180 deg) and of the inner-axis ring bosses; servo 1 has its horn on its +t side, servo 2 is the mirror
    image (horn on -t), so the two brackets and collar halves are mirror pairs.
Kinematics: the lever eye moves with the engine pose R = Rx(alpha) Ry(beta); the horn angle psi that keeps the
pushrod length is solved in closed form (|P_h(psi) - P_l| = L).  psi > 0 lifts the horn eye.
"""
from __future__ import annotations
import math
import numpy as np


def _mm(P, k):
    return P[k]["v"] * 1000.0


def geometry(P):
    """All TVC packaging numbers from the parameter set.  Returns a dict (mm, deg)."""
    L, W, H = [x * 1000.0 for x in P["tvc_servo_box"]["v"]]      # 40.3 x 20.2 x 40.3 (H reserved)
    R_bay = _mm(P, "engine_bay_ID") / 2.0
    c_wall = P["tvc_wall_gap_mm"]["v"]
    R_lim = R_bay - c_wall
    hH = H / 2.0
    u_out = math.sqrt(R_lim ** 2 - hH ** 2)
    u_in = u_out - W
    u_sh = u_in + W / 2.0
    r_h = _mm(P, "tvc_horn_r")
    z_s = _mm(P, "tvc_shaft_z")
    z_lb = _mm(P, "tvc_lever_z")
    t_eye = hH + P["tvc_eye_offset_mm"]["v"]            # eye mid-plane beyond the spline face
    u_eye = u_sh - r_h
    r_e = math.hypot(u_eye, t_eye)
    off = math.degrees(math.atan2(t_eye, u_eye))
    phis = list(P["tvc_lever_phi_deg"]["v"])
    sides = [+1, -1]
    servos = []
    for i, (phi, s) in enumerate(zip(phis, sides)):
        th = phi - s * off
        a = math.radians(th)
        eu = np.array([math.cos(a), math.sin(a), 0.0])
        et = np.array([-math.sin(a), math.cos(a), 0.0])
        ez = np.array([0.0, 0.0, 1.0])
        sd = s * et                                            # shaft direction (out of the spline face)
        O = u_sh * eu + s * hH * et + z_s * ez                 # servo local origin: shaft axis at the spline face
        C = u_sh * eu + s * t_eye * et + z_s * ez              # shaft axis at the eye mid-plane
        P_h0 = C - r_h * eu                                    # horn eye centre at neutral
        P_l0 = P_h0 + np.array([0.0, 0.0, z_lb - z_s])          # lever eye centre at neutral (vertical pushrod)
        servos.append(dict(i=i + 1, phi=phi, s=s, theta_c=th, eu=eu, et=et, ez=ez, sd=sd, O=O, C=C,
                           P_h0=P_h0, P_l0=P_l0))
    g = dict(L=L, W=W, H=H, R_bay=R_bay, c_wall=c_wall, R_lim=R_lim, u_out=u_out, u_in=u_in, u_sh=u_sh,
             r_h=r_h, z_s=z_s, z_lb=z_lb, t_eye=t_eye, u_eye=u_eye, r_e=r_e, off_deg=off, L_pr=z_lb - z_s,
             n=r_e / r_h, servos=servos)
    return g


def T_servo(sv):
    """4x4: servo_shape local frame (X_s along L, Y_s across W, Z_s = shaft) -> engine frame.  X_s -> +Z
    (body above the shaft: shaft 10 mm from the bottom end), Z_s -> shaft direction, Y_s = Z_s x X_s."""
    ex = sv["ez"]
    ez = sv["sd"]
    ey = np.cross(ez, ex)
    T = np.eye(4)
    T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = ex, ey, ez, sv["O"]
    return T


def T_ut(sv, origin=None):
    """Right-handed frame (e_u, e_t, e_z) at the servo centre line (used to store brackets in a drawing frame)."""
    T = np.eye(4)
    T[:3, 0], T[:3, 1], T[:3, 2] = sv["eu"], sv["et"], sv["ez"]
    T[:3, 3] = np.zeros(3) if origin is None else origin
    return T


def R_pose(alpha, beta):
    a, b = math.radians(alpha), math.radians(beta)
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    return Rx @ Ry


def horn_eye(g, sv, psi_deg):
    p = math.radians(psi_deg)
    return sv["C"] + g["r_h"] * (-math.cos(p) * sv["eu"] + math.sin(p) * sv["ez"])


def solve_psi(g, sv, alpha, beta):
    """Horn angle (deg) that keeps |P_h - P_l| = L_pr for the engine pose (alpha, beta); branch nearest 0."""
    Pl = R_pose(alpha, beta) @ sv["P_l0"]
    d = Pl - sv["C"]
    du, dz, dt = float(d @ sv["eu"]), float(d @ sv["ez"]), float(d @ sv["et"])
    L, rh = g["L_pr"], g["r_h"]
    K = (du * du + dz * dz + dt * dt + rh * rh - L * L) / (2.0 * rh)
    # -du cos(psi) + dz sin(psi) = K   ->   rho sin(psi + phi0) = K
    rho = math.hypot(dz, du)
    phi0 = math.atan2(-du, dz)
    if abs(K) > rho:
        return float("nan"), Pl
    base = math.asin(K / rho)
    cands = [base - phi0, math.pi - base - phi0]
    cands = [((c + math.pi) % (2 * math.pi)) - math.pi for c in cands]
    psi = min(cands, key=abs)
    return math.degrees(psi), Pl


def pose_all(g, alpha, beta):
    out = []
    for sv in g["servos"]:
        psi, Pl = solve_psi(g, sv, alpha, beta)
        Ph = horn_eye(g, sv, psi)
        rod = Pl - Ph
        tilt = math.degrees(math.acos(max(-1.0, min(1.0, rod[2] / np.linalg.norm(rod)))))
        out.append(dict(i=sv["i"], psi=psi, P_h=Ph, P_l=Pl, rod_tilt_deg=tilt, rod_len=float(np.linalg.norm(rod))))
    return out


def mixing_linear(g):
    """d(psi_i)/d(alpha, beta) at neutral (deg/deg), by central differences of the exact solve."""
    h = 0.01
    M = np.zeros((2, 2))
    for j, (da, db) in enumerate([(h, 0.0), (0.0, h)]):
        p1 = [r["psi"] for r in pose_all(g, da, db)]
        p0 = [r["psi"] for r in pose_all(g, -da, -db)]
        M[:, j] = (np.array(p1) - np.array(p0)) / (2 * h)
    return M


def travel_table(g, stop_deg=8.0, cmd_deg=7.0, n=72):
    """Servo angle extremes for commanded vector norms (cmd) and the conical stop, plus inverse-kinematics
    (alpha, beta) -> psi over the circle.  Returns a dict for the calcs/README."""
    res = {}
    for name, amp in (("cmd", cmd_deg), ("stop", stop_deg)):
        psis = [[], []]
        tilts = [[], []]
        for k in range(n):
            ang = 2 * math.pi * k / n
            # a conical tilt of 'amp' in direction ang: rotation axis in the XY plane
            a, b = _cone_to_ab(amp, ang)
            for r in pose_all(g, a, b):
                psis[r["i"] - 1].append(r["psi"])
                tilts[r["i"] - 1].append(r["rod_tilt_deg"])
        res[name] = {"amp_deg": amp,
                     "psi_min_deg": [round(min(p), 2) for p in psis], "psi_max_deg": [round(max(p), 2) for p in psis],
                     "rod_tilt_max_deg": [round(max(t), 2) for t in tilts]}
    return res


def _cone_to_ab(amp_deg, dir_rad):
    """(alpha, beta) of R = Rx(alpha)Ry(beta) whose engine axis makes angle amp with +Z, tilted toward azimuth
    dir (the nozzle exit swings the opposite way).  Exact: the axis z' = R e_z."""
    th = math.radians(amp_deg)
    v = np.array([math.sin(th) * math.cos(dir_rad), math.sin(th) * math.sin(dir_rad), math.cos(th)])
    # R e_z = (sin b, -sin a cos b, cos a cos b)
    b = math.asin(max(-1.0, min(1.0, v[0])))
    a = math.atan2(-v[1], v[2])
    return math.degrees(a), math.degrees(b)


def cone_to_ab(amp_deg, dir_deg):
    return _cone_to_ab(amp_deg, math.radians(dir_deg))


if __name__ == "__main__":
    import sys, json
    sys.path.insert(0, ".")
    import config
    P, _ = config.build()
    g = geometry(P)
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in g.items() if k != "servos"})
    for sv in g["servos"]:
        print(sv["i"], round(sv["theta_c"], 2), np.round(sv["P_h0"], 2), np.round(sv["P_l0"], 2))
    print(mixing_linear(g))
    print(json.dumps(travel_table(g), indent=1))
