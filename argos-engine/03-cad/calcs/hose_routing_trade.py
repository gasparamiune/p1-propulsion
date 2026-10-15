"""Feed-hose routing trade across the gimbal (lead request 2026-10-12, after mechanical.json v2): v1, Mechanical.

Question: is there a routing more compact than the adopted radial straight hose (L >= 0.40 m along the pivot radial line,
valve end ~0.6 m above the pivot) that still meets K_hose <= 20 N m/rad per axis, without a rotating seal in liquid N2O?
Report per option: vehicle length effect, K, hinge moment at 7 deg, mass, risk.

Method: hose_frame.solve (linear 3-D Euler-Bernoulli frame, engine end on a rigid arm from the pivot, fixed end clamped) for
each candidate centreline; deformed shape at the 8 deg stop by linear superposition of the alpha / beta solutions in 16 tilt
directions; clearance of the hose surface (OD ASSUMED 15 mm) to (a) the engine-bay wall (r 70 mm, 3 mm required, as for the
engine) and (b) the posed engine envelope (axisymmetric profile from CAD v3.3 incl. the torch envelope, 3 mm required);
bend radius = installed + 8 deg change (hose_frame.evaluate rule).  Frame: CAD v3.3 pivot frame, mm in the text, m in the
model.  EI 0.05-0.5 N m2 ASSUMED (pressurised EI unknown, bench test B-FD-1).  Hose minimum bend radius: maker datasheet
TO-VERIFY (not assumed here; each option reports what it needs).  Linear theory: rotations up to 8 deg and engine-end
motions up to ~35 mm are extrapolated from the small-rotation solution (adequate for ranking, not for final sizing).
"""
from __future__ import annotations
import sys, json, math
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hose_frame as hf

OUT = HERE / "hose_routing_trade_v1.json"
OD = 0.015                   # m hose OD ASSUMED (-6 PTFE/SS braid 12-15 mm class; TO-VERIFY)
R_WALL = 0.070               # m engine-bay radius (140 mm ID, founder decision)
CLR = 0.003                  # m required clearance (same rule as the engine sweep)
EI_SET = (0.05, 0.25, 0.5)   # N m2 ASSUMED range
TH_STOP, TH_RANGE = math.radians(8.0), math.radians(7.0)
K_REQ = 20.0                 # N m/rad per axis (lead 2026-10-12)
RHO_HOSE = 0.13              # kg/m ASSUMED (as M1; TO-VERIFY)
RHO_TUBE = 0.189             # kg/m 3/8 x 0.035 in 316 tube (DERIVED: pi/4 (9.525^2 - 7.747^2) mm2 x 7.85 g/cm3)
M_FITTING = 0.025            # kg per JIC -6 end/elbow ASSUMED
Z_ENG_END = 0.215            # m bonnet -6 ORB inlet elbow (CAD v3.3 frame, as hose_frame.py)
X_RISER = -0.022             # m (hose_frame.py engine end x)


def R_eng(z):
    """Engine outer radius (m) at height z (m), CAD v3.3 neutral, axisymmetric envelope incl. the torch envelope (conservative)."""
    zm = z * 1e3
    if zm < -147.4 or zm > 262.0:
        return 0.0
    if zm <= 149.6:
        return 0.03175          # case OD 63.5
    if zm <= 178.6:
        return 0.0325           # head
    if zm <= 225.0:
        return 0.036            # bonnet flange 35 / torch envelope 36 (az 0, taken axisymmetric: conservative)
    return 0.026                # v3.4 HV69 in-line stack (crank housing / servo body envelope, ESTIMATE)


def helix(p_start_r, phi0_deg, z0, r1, z1, dphi_deg, lead_out=0.0, n=90, sense=+1):
    """Helix/spiral about the engine axis from (r0, phi0, z0) to (r1, phi0 + sense*dphi, z1), then a vertical lead-out."""
    pts = []
    for i in range(n + 1):
        s = i / n
        r = p_start_r + (r1 - p_start_r) * s
        ph = math.radians(phi0_deg + sense * dphi_deg * s)
        pts.append([r * math.cos(ph), r * math.sin(ph), z0 + (z1 - z0) * s])
    pts = np.array(pts)
    if lead_out > 0:
        m = max(2, int(lead_out / 0.01))
        last = pts[-1]
        pts = np.vstack([pts, [last + np.array([0, 0, lead_out * k / m]) for k in range(1, m + 1)]])
    return pts


def u_loop(p0, up1, Rb, down, plane_dir_deg, n_bend=24):
    """Up 'up1' along +z from p0, 180 deg bend of radius Rb toward plane_dir (in the XY plane), down 'down'."""
    p0 = np.asarray(p0, float)
    d = np.array([math.cos(math.radians(plane_dir_deg)), math.sin(math.radians(plane_dir_deg)), 0.0])
    pts = [p0 + np.array([0, 0, up1 * k / max(2, int(up1 / 0.01))]) for k in range(0, max(2, int(up1 / 0.01)) + 1)]
    top = pts[-1]
    c = top + d * Rb
    for k in range(1, n_bend + 1):
        a = math.pi * k / n_bend
        pts.append(c - d * Rb * math.cos(a) + np.array([0, 0, Rb * math.sin(a)]))
    last = pts[-1]
    m = max(2, int(down / 0.01))
    for k in range(1, m + 1):
        pts.append(last - np.array([0, 0, down * k / m]))
    return np.array(pts)


def rodrigues(a, th):
    a = np.asarray(a, float) / np.linalg.norm(a)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * K @ K


def clearance(nodes, Ux, Uy, theta_unit, s_skip=0.02):
    """Min clearance (m) of the hose surface to the wall and to the posed engine over 16 tilt directions at the 8 deg stop."""
    N = len(nodes)
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(nodes, axis=0), axis=1))])
    sc = TH_STOP / theta_unit
    wall_min, eng_min, worst = 1.0, 1.0, {}
    for k in range(16):
        psi = 2 * math.pi * k / 16
        a = np.array([math.cos(psi), math.sin(psi), 0.0])
        U = (math.cos(psi) * Ux + math.sin(psi) * Uy) * sc
        R = rodrigues(a, TH_STOP)
        for i in range(N):
            p = nodes[i] + U[6 * i:6 * i + 3]
            cw = R_WALL - (math.hypot(p[0], p[1]) + OD / 2)
            if cw < wall_min:
                wall_min, worst["wall"] = cw, {"node_s_m": round(float(s[i]), 3), "z_m": round(float(p[2]), 3), "tilt_dir_deg": round(math.degrees(psi), 1)}
            if s[i] < s_skip:
                continue
            pe = R.T @ p
            re_ = math.hypot(pe[0], pe[1]) - OD / 2 - R_eng(pe[2])
            if R_eng(pe[2]) > 0 and re_ < eng_min:
                eng_min, worst["engine"] = re_, {"node_s_m": round(float(s[i]), 3), "z_m": round(float(pe[2]), 3), "tilt_dir_deg": round(math.degrees(psi), 1)}
    # static (neutral) clearances
    w0 = min(R_WALL - (math.hypot(p[0], p[1]) + OD / 2) for p in nodes)
    e0 = min((math.hypot(p[0], p[1]) - OD / 2 - R_eng(p[2])) for i, p in enumerate(nodes) if s[i] >= s_skip and R_eng(p[2]) > 0) if any(
        R_eng(p[2]) > 0 for i, p in enumerate(nodes) if s[i] >= s_skip) else 1.0
    return {"wall_min_mm_at_stop": round(wall_min * 1e3, 1), "engine_min_mm_at_stop": round(eng_min * 1e3, 1) if eng_min < 1 else None,
            "wall_min_mm_neutral": round(w0 * 1e3, 1), "engine_min_mm_neutral": round(e0 * 1e3, 1) if e0 < 1 else None, "worst": worst,
            "pass": bool(wall_min >= CLR and eng_min >= CLR)}


def evaluate(name, nodes, extra_mass, fixed_end_note, needs, risk):
    L = float(np.sum(np.linalg.norm(np.diff(nodes, axis=0), axis=1)))
    k0 = hf.curvature_installed(nodes)
    rec = {"option": name, "hose_length_m": round(L, 3), "engine_end_m": [round(float(c), 4) for c in nodes[0]],
           "fixed_end_m": [round(float(c), 4) for c in nodes[-1]], "fixed_end_height_above_pivot_m": round(float(nodes[-1][2]), 3),
           "installed_min_bend_radius_m": round(1.0 / k0.max(), 4) if k0.max() > 0 else None, "per_EI": {}}
    th = 1e-3
    for EI in EI_SET:
        kx, _, bx, Ux = hf.solve(nodes, EI, axis=(1, 0, 0), theta=th)
        ky, _, by, Uy = hf.solve(nodes, EI, axis=(0, 1, 0), theta=th)
        dk = np.maximum(bx, by) / EI * TH_STOP / th * th      # bend moment for theta = th -> curvature change at the stop
        dk = np.maximum(bx, by) / EI * (TH_STOP / th)
        kk = np.maximum(k0[:-1], k0[1:]) + dk
        rec["per_EI"][f"EI={EI}"] = {"K_alpha_Nm_rad": round(kx, 2), "K_beta_Nm_rad": round(ky, 2), "M_7deg_Nm": [round(kx * TH_RANGE, 2), round(ky * TH_RANGE, 2)],
                                     "K_rule_pass": bool(max(kx, ky) <= K_REQ), "min_bend_radius_at_stop_m": round(1.0 / kk.max(), 4)}
        if EI == EI_SET[-1]:
            rec["clearance_8deg"] = clearance(nodes, Ux, Uy, th)
    rec["mass_kg"] = round(L * RHO_HOSE + extra_mass, 3)
    rec["fixed_end"] = fixed_end_note
    rec["needs"] = needs
    rec["risk"] = risk
    return rec


def L_min_radial(EI, h=Z_ENG_END, k_req=K_REQ):
    """Shortest straight radial hose meeting K <= k_req: closed form K = 4EI/L (1 + 3x + 3x^2), x = h/L (bisection)."""
    lo, hi = 0.05, 2.0
    f = lambda L: 4 * EI / L * (1 + 3 * h / L + 3 * (h / L) ** 2) - k_req
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if f(mid) > 0:
            lo = mid
        else:
            hi = mid
    return hi


def main():
    p0 = np.array([X_RISER, 0.0, Z_ENG_END])
    d_rad = p0 / np.linalg.norm(p0)
    opts = []
    # O1 adopted: straight along the pivot radial line
    for L in (0.40, 0.30):
        nodes = hf.centreline_straight(p0, d_rad, L)
        opts.append(evaluate(f"O1 radial straight L {L:.2f} m (lead-adopted rule at 0.40)", nodes, 2 * M_FITTING,
                             "isolation-valve outlet on the vehicle axis above the engine", "hose min bend radius not engaged (straight)",
                             "low: bench EI (B-FD-1); valve end high in the vehicle"))
    # O2 helix around the engine axis at the head-stack top: starts at the bonnet elbow (r 30, az 90), 300 / 360 deg
    for (r0, r1, dphi, z1, lead) in ((0.030, 0.045, 300.0, 0.255, 0.05), (0.030, 0.050, 360.0, 0.265, 0.05), (0.045, 0.050, 300.0, 0.255, 0.05)):
        nodes = helix(r0, 90.0, Z_ENG_END, r1, z1, dphi, lead_out=lead)
        opts.append(evaluate(f"O2 helix about the engine axis at the stack top: r {r0*1e3:.0f}->{r1*1e3:.0f} mm, {dphi:.0f} deg, z {Z_ENG_END:.3f}->{z1:.3f} m + {lead:.2f} m lead-out",
                             nodes, 2 * M_FITTING, "fixed bracket at the bay wall above the stack, then the valve", f"hose bend radius <= {min(r0, r1)*1e3:.0f} mm",
                             "medium-high: bend radius below typical -6 PTFE values (datasheet TO-VERIFY); coil near the engine end swings with the head"))
    # O3 low helix around the case near the pivot plane, fed by an engine-mounted 3/8 riser from the bonnet down to z 0.06 m
    for (r0, r1, dphi) in ((0.042, 0.054, 300.0), (0.045, 0.055, 330.0)):
        nodes = helix(r0, 90.0, 0.062, r1, 0.045, dphi, lead_out=0.0)
        riser_L = (Z_ENG_END - 0.062) + 0.03
        opts.append(evaluate(f"O3 low helix around the case at the pivot plane: r {r0*1e3:.0f}->{r1*1e3:.0f} mm, {dphi:.0f} deg, z 0.062->0.045 m, engine riser {riser_L:.2f} m",
                             nodes, 2 * M_FITTING + riser_L * RHO_TUBE + 0.02, "bulkhead fitting on the upper thrust ring GM-09 (z 0.035 m); fixed 3/8 line up the bay wall",
                             "a fixed 3/8 in line from GM-09 up past the head/stack heights: the engine sweeps to r 57-67 mm at z 0.18-0.25 m, so the line (OD 9.5 + 3 mm clearance) "
                             "needs a local bay radius >= 72.5-79.8 mm (a ~10 mm deep channel in the airframe wall over ~0.15 m, or an external line)",
                             "high: airframe change; N2O riser 6 mm from the pre-chamber case (FEA hi bound case 315 C inner wall, B1) -> trapped-liquid heating and shielding"))
    # O5 inverted-U loop above the stack in the plane of the radial line
    for (up1, Rb, down) in ((0.06, 0.045, 0.05), (0.10, 0.050, 0.08)):
        nodes = u_loop(p0, up1, Rb, down, plane_dir_deg=-90.0)
        opts.append(evaluate(f"O5 inverted-U loop above the stack: up {up1:.2f}, bend R {Rb*1e3:.0f} mm toward -Y, down {down:.2f} m", nodes, 2 * M_FITTING,
                             "fixed bracket beside the stack, then the valve", f"hose bend radius <= {Rb*1e3:.0f} mm", "medium: bend radius; loop swings with the head"))
    Lmin = {f"EI={e}": round(L_min_radial(e), 3) for e in (0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5)}
    swivel = {
        "option": "O4 two-axis rotary unions in the gimbal trunnions (fixed -> outer pin X -> ring passage -> inner pin Y -> collar -> engine riser)",
        "K_Nm_rad": "~0 (no hose); seal friction torque instead: 2 rotary seals per axis on ~10 mm journals at 7 MPa, 0.1-0.5 N m per axis ASSUMED (no datasheet)",
        "M_7deg_Nm": "friction 0.1-0.5 N m per axis (ASSUMED), stick-slip in the TVC loop",
        "mass_kg": "0.10-0.20 ESTIMATE (2 unions, drilled ring/collar passages, engine riser 0.04)",
        "vehicle_length": "same in-bay problem as O3: the fixed feed must reach the outer trunnion at z ~0 from the tank above, past the head/stack sweep (no room inside "
                          "the 140 mm ID) -> no length saving without an airframe channel",
        "risk": "high: rotating seals in liquid N2O at 7 MPa (leak/wear particles next to the engine, oxygen-service qualification), ring and collar become pressure parts, "
                "no qualified part identified (TO-VERIFY / TO-QUOTE)",
        "verdict": "rejected (lead rule: no rotating seal in liquid N2O unless clearly better and qualified; it is neither)"}
    res = {"id": "hose_routing_trade", "version": "v1", "date": "2026-10-12", "script": "03-cad/src/calcs/hose_routing_trade.py",
           "method": __doc__.strip().splitlines()[0], "assumptions": {"OD_m": OD, "EI_Nm2": EI_SET, "hose_kg_per_m": RHO_HOSE, "fitting_kg": M_FITTING,
                                                                    "bay_radius_m": R_WALL, "clearance_m": CLR, "K_req_Nm_rad": K_REQ,
                                                                    "engine_profile": "case 31.75 / head 32.5 / bonnet-torch 36 / v3.4 stack 26 mm (CAD v3.3 frame)"},
           "options": opts, "swivel": swivel, "radial_straight_L_min_m_for_K20": Lmin}
    OUT.write_text(json.dumps(res, indent=1))
    for o in opts:
        e5 = o["per_EI"]["EI=0.5"]; e05 = o["per_EI"]["EI=0.05"]
        c = o["clearance_8deg"]
        print(f"{o['option'][:100]:100s} L {o['hose_length_m']:.3f} top z {o['fixed_end_height_above_pivot_m']:.3f} K(EI .05) {e05['K_alpha_Nm_rad']:.1f}/{e05['K_beta_Nm_rad']:.1f} "
              f"K(EI .5) {e5['K_alpha_Nm_rad']:.1f}/{e5['K_beta_Nm_rad']:.1f} Rmin_inst {o['installed_min_bend_radius_m']} Rstop {e5['min_bend_radius_at_stop_m']} "
              f"wall {c['wall_min_mm_neutral']}/{c['wall_min_mm_at_stop']} eng {c['engine_min_mm_neutral']}/{c['engine_min_mm_at_stop']} pass {c['pass']} m {o['mass_kg']}")
    print("L_min radial for K <= 20:", Lmin)


if __name__ == "__main__":
    main()
