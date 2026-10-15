"""Generate TVC geometry constants (firmware) and the 2-axis gimbal plant tables (SIL) from interfaces/mechanical.json.

Electronics v2 (2026-10-12, mechanical.json v2). Supersedes v1 (archive/gen_mech_params_v1.py: mechanical.json v1 levers at
64.5/154.5 deg, r_e 48 mm, horn 8 mm and the vertical-rod servo map psi = asin(dz / r_h)).
Reads (never hard-codes Mechanical's numbers; every value below comes from the file named):
  interfaces/mechanical.json v2
    tvc_actuation   lever azimuths, lever-eye and horn-eye positions at neutral, horn radius, pushrod length, servo shaft height,
                    the published servo-angle extremes and rod tilt (7 deg command cone, 8 deg stop) and the neutral mixing
                    matrix (fit and checks below), slew table (check against the SIL), design loads, hinge-moment terms,
                    axis-stiffness table (FEA, 9 poses)
    gimbal          range, stop, ring inertia (alpha axis only), hinge friction
    gimballed_mass_properties   inertia about the pivot (wet, mid-burn, dry)
    feed_across_gimbal          hose hinge-stiffness range
Horn plane (why there is a fit): mechanical.json v2 publishes the horn-eye position at neutral but not the servo shaft centre,
i.e. the azimuth of the plane the horn turns in. The exact pushrod-length solve needs it. Against Mechanical's exact model the
v1 vertical-rod map is off by up to 2.1 deg of servo angle (about 0.45 deg of engine angle along that servo's direction) at
7 deg, and a horn plane on the lever radial line by 0.34-0.42 deg of servo angle. This generator therefore FITS one number,
the signed horn-plane offset (servo 2 = mirror image of
servo 1, as published), to the published servo-angle extremes and rod tilt, and refuses to write when the residual exceeds
0.05 deg. When Mechanical publishes tvc_actuation.servo_shaft_xyz_m (Electronics request, open interface issue) that value is
used and the fit becomes a check.
Writes:
  src/core/mech_params.h       firmware: exact Cardan TVC kinematics constants (servo mixing, horn clamps)
  sil/mech_tables.h            SIL: 2-axis gimbal plant (geometry, inertia, hinge terms, FEA structure stiffness per axis)
  ../results/gen_mech_params_v2.json   provenance (sha of mechanical.json, values, fit, checks)
Usage: /opt/engine-venv/bin/python gen_mech_params.py [--engine-root <engine dir with interfaces/>]
"""
import argparse
import datetime
import hashlib
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FW = os.path.dirname(HERE)
RES = os.path.join(FW, '..', 'results')
GEN = 'firmware/tools/gen_mech_params.py v2'
FIT_TOL_DEG = 0.05


def v(node):
    return node['v'] if isinstance(node, dict) and 'v' in node else node


def rot(alpha, beta):
    """R = Rx(alpha) Ry(beta), arrays broadcast (returns [..., 3, 3])"""
    alpha, beta = np.asarray(alpha, float), np.asarray(beta, float)
    ca, sa, cb, sb = np.cos(alpha), np.sin(alpha), np.cos(beta), np.sin(beta)
    z, o = np.zeros_like(ca), np.ones_like(ca)
    rx = np.stack([np.stack([o, z, z], -1), np.stack([z, ca, -sa], -1), np.stack([z, sa, ca], -1)], -2)
    ry = np.stack([np.stack([cb, z, sb], -1), np.stack([z, o, z], -1), np.stack([-sb, z, cb], -1)], -2)
    return rx @ ry


class Linkage:
    """Servo i: shaft (horizontal) through C_i; horn eye H(psi) = C + r_h (-cos psi u + sin psi z), u = horizontal unit vector
    from the horn eye to the shaft at neutral; lever eye P = R(alpha, beta) P0_i; pushrod |P - H| = L; psi > 0 lifts the eye."""

    def __init__(self, P0, Ph0, r_h, L, phi_deg, off_deg=None, C=None):
        self.P0 = np.asarray(P0, float)
        self.Ph0 = np.asarray(Ph0, float)
        self.r_h, self.L = float(r_h), float(L)
        if C is not None:
            self.C = np.asarray(C, float)
            u = self.C - self.Ph0
            u[:, 2] = 0.0
            self.u = u / np.linalg.norm(u, axis=1)[:, None]
        else:
            s = np.array([1.0, -1.0])          # servo 2 = mirror image of servo 1 (mechanical.json lever_azimuth_deg src)
            th = np.radians(np.asarray(phi_deg) - s * off_deg)
            self.u = np.stack([np.cos(th), np.sin(th), np.zeros(2)], -1)
            self.C = self.Ph0 + self.r_h * self.u

    def psi(self, i, alpha, beta):
        P = rot(alpha, beta) @ self.P0[i]
        d = P - self.C[i]
        du = d @ self.u[i]
        dz = d[..., 2]
        K = ((d * d).sum(-1) + self.r_h ** 2 - self.L ** 2) / (2.0 * self.r_h)
        rho = np.hypot(dz, du)
        phi0 = np.arctan2(-du, dz)
        base = np.arcsin(np.clip(K / rho, -1.0, 1.0))
        c1 = (base - phi0 + np.pi) % (2 * np.pi) - np.pi
        c2 = (np.pi - base - phi0 + np.pi) % (2 * np.pi) - np.pi
        ps = np.where(np.abs(c1) <= np.abs(c2), c1, c2)
        H = self.C[i] + self.r_h * (-np.cos(ps)[..., None] * self.u[i] + np.sin(ps)[..., None] * np.array([0, 0, 1.0]))
        rod = P - H
        tilt = np.degrees(np.arccos(np.clip(np.abs(rod[..., 2]) / np.linalg.norm(rod, axis=-1), -1, 1)))
        return ps, tilt

    def extremes(self, amp_rad, n=1440):
        th = np.linspace(0, 2 * np.pi, n, endpoint=False)
        a, b = amp_rad * np.cos(th), amp_rad * np.sin(th)
        out = []
        for i in range(2):
            p, t = self.psi(i, a, b)
            out.append((float(np.degrees(p.min())), float(np.degrees(p.max())), float(t.max())))
        return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine-root', default=os.environ.get('ENGINE_ROOT', '/home/claude/work/shared-fallback/engine'))
    args = ap.parse_args()
    fn = os.path.join(args.engine_root, 'interfaces', 'mechanical.json')
    raw = open(fn, 'rb').read()
    sha = hashlib.sha256(raw).hexdigest()[:16]
    m = json.loads(raw)
    ver = m.get('version', '?')
    if not str(ver).startswith('v2'):
        raise SystemExit('gen_mech_params v2 needs mechanical.json v2 (horn/lever eye positions); v1 -> archive/gen_mech_params_v1.py')
    tvc, gim, mp = m['tvc_actuation'], m['gimbal'], m['gimballed_mass_properties']
    hm = tvc['hinge_moment_terms_Nm']
    phi = list(v(tvc['lever_azimuth_deg']))
    r_e, z_b, r_h, L = v(tvc['lever_radius_m']), v(tvc['lever_ball_z_m']), v(tvc['horn_radius_m']), v(tvc['pushrod_length_m'])
    z_s, n_gear = v(tvc['servo_shaft_z_m']), v(tvc['gear_ratio_n'])
    P0, Ph0 = np.array(v(tvc['lever_eye_xyz_m'])), np.array(v(tvc['horn_eye_xyz_m']))
    rng, stop = math.radians(v(gim['range_deg'])), math.radians(v(gim['mechanical_stop_deg']))
    # consistency of the published geometry (fails loudly rather than generating a wrong map)
    chk = {}
    for i in range(2):
        a = math.radians(phi[i])
        chk[f'lever_eye_{i + 1}_vs_r_e_phi_z_mm'] = round(1e3 * float(np.linalg.norm(P0[i] - [r_e * math.cos(a), r_e * math.sin(a), z_b])), 4)
        chk[f'horn_eye_{i + 1}_vs_lever_xy_shaft_z_mm'] = round(1e3 * float(np.linalg.norm(Ph0[i] - [P0[i][0], P0[i][1], z_s])), 4)
    chk['pushrod_vs_eye_heights_mm'] = round(1e3 * abs(L - (z_b - z_s)), 4)
    for k_, val in chk.items():
        if val > 0.2:
            raise SystemExit(f'mechanical.json geometry inconsistent: {k_} = {val} mm')
    pub = v(tvc['servo_angle_range_deg'])
    tgt = []
    for key in ('cmd_7deg', 'stop_8deg'):
        e = pub[key]
        tgt.append((math.radians(e['amp_deg']), e['psi_min_deg'], e['psi_max_deg'], e['rod_tilt_max_deg']))

    def resid(lk):
        r = 0.0
        for amp, pmin, pmax, tilt in tgt:
            ex = lk.extremes(amp)
            for i in range(2):
                r = max(r, abs(ex[i][0] - pmin[i]), abs(ex[i][1] - pmax[i]), abs(ex[i][2] - tilt[i]))
        return r

    shaft_pub = tvc.get('servo_shaft_xyz_m')
    if shaft_pub is not None:
        lk = Linkage(P0, Ph0, r_h, L, phi, C=v(shaft_pub))
        off, fit_src = float('nan'), 'mechanical.json tvc_actuation.servo_shaft_xyz_m'
    else:
        grid = np.arange(-89.5, 89.6, 0.5)
        rs = [resid(Linkage(P0, Ph0, r_h, L, phi, off_deg=o)) for o in grid]
        o0 = float(grid[int(np.argmin(rs))])
        lo, hi = o0 - 0.5, o0 + 0.5               # golden-section refinement
        g = (math.sqrt(5) - 1) / 2
        for _ in range(40):
            x1, x2 = hi - g * (hi - lo), lo + g * (hi - lo)
            if resid(Linkage(P0, Ph0, r_h, L, phi, off_deg=x1)) <= resid(Linkage(P0, Ph0, r_h, L, phi, off_deg=x2)):
                hi = x2
            else:
                lo = x1
        off = 0.5 * (lo + hi)
        lk = Linkage(P0, Ph0, r_h, L, phi, off_deg=off)
        fit_src = 'FIT of the signed horn-plane offset to tvc_actuation.servo_angle_range_deg (psi extremes and rod tilt, 7 and 8 deg)'
        # the opposite sign and the radial plane, as evidence that the fit is identifiable
        chk['fit_residual_opposite_sign_deg'] = round(resid(Linkage(P0, Ph0, r_h, L, phi, off_deg=-off)), 3)
        chk['fit_residual_radial_plane_deg'] = round(resid(Linkage(P0, Ph0, r_h, L, phi, off_deg=0.0)), 3)
    res_fit = resid(lk)
    chk['fit_residual_deg'] = round(res_fit, 4)
    if res_fit > FIT_TOL_DEG:
        raise SystemExit(f'horn-plane fit residual {res_fit:.3f} deg > {FIT_TOL_DEG} deg: geometry not reproduced, not writing')
    ex_rng, ex_stop = lk.extremes(rng), lk.extremes(stop)
    ex_mid = lk.extremes(0.5 * (rng + stop))
    psi_rng = [min(e[0] for e in ex_rng), max(e[1] for e in ex_rng)]
    psi_stop = [max(e[0] for e in ex_stop), min(e[1] for e in ex_stop)]      # the stop is reached first by the nearer servo
    psi_clamp = [min(e[0] for e in ex_mid), max(e[1] for e in ex_mid)]
    if not (psi_stop[0] < psi_clamp[0] < psi_rng[0] and psi_rng[1] < psi_clamp[1] < psi_stop[1]):
        raise SystemExit('horn clamp does not lie between the range and the stop')
    # neutral mixing (central difference) vs the published matrix
    h = math.radians(0.01)
    mix = np.zeros((2, 2))
    for i in range(2):
        mix[i, 0] = float(lk.psi(i, h, 0.0)[0] - lk.psi(i, -h, 0.0)[0]) / (2 * h)
        mix[i, 1] = float(lk.psi(i, 0.0, h)[0] - lk.psi(i, 0.0, -h)[0]) / (2 * h)
    mix_pub = np.array(v(tvc['mixing_servo_deg_per_engine_deg']))
    chk['mixing_neutral_max_diff'] = round(float(np.abs(mix - mix_pub).max()), 4)
    if chk['mixing_neutral_max_diff'] > 0.01:
        raise SystemExit('neutral mixing differs from mechanical.json')
    # v1 vertical-rod map error on the range cone (evidence for the change)
    th = np.linspace(0, 2 * np.pi, 1440, endpoint=False)
    a, b = rng * np.cos(th), rng * np.sin(th)
    err_v1 = 0.0
    for i in range(2):
        p, _ = lk.psi(i, a, b)
        dz = (rot(a, b) @ lk.P0[i])[..., 2] - lk.P0[i][2]
        err_v1 = max(err_v1, float(np.degrees(np.abs(p - np.arcsin(np.clip(dz / r_h, -1, 1)))).max()))
    chk['v1_vertical_rod_map_err_servo_deg'] = round(err_v1, 3)
    chk['v1_vertical_rod_map_err_engine_deg'] = round(err_v1 / n_gear, 3)
    # ---------------------------------------------------------------------------------------------- SIL inputs
    I_wet = v(mp['wet_full_grain']['I_pivot_kgm2'])
    I_mid = v(mp['mid_burn']['I_pivot_kgm2'])
    I_dry = v(mp['dry_grain_burnt']['I_pivot_kgm2'])
    I_ring = v(gim['ring_alpha_axis_only']['I_xx_pivot_kgm2'])
    k_hose = v(m['feed_across_gimbal']['hinge_stiffness_Nm_per_rad'])
    axacc_per_rad = v(hm['axial_accel_m_a_le_sin7']) / math.sin(rng)
    tab = v(tvc['axis_stiffness_table'])
    cen = tab['centre']
    K_struct_c = cen['mech_rigidchain']
    K_mechT_c = cen['mech_T']
    K_chain_ax = [1.0 / (1.0 / K_mechT_c[k] - 1.0 / K_struct_c[k]) for k in range(2)]
    # generalized rod Jacobian at neutral: d(rod length)/d(alpha, beta) = vertical lever-eye velocity = (y0, -x0)
    J2 = [sum(lk.P0[i][1] ** 2 for i in range(2)), sum(lk.P0[i][0] ** 2 for i in range(2))]
    k_rod = [K_chain_ax[k] / J2[k] for k in range(2)]
    poses_min = []
    for k in range(2):
        nm, rec = min(((nm, rec) for nm, rec in tab.items()), key=lambda it: it[1]['mech_rigidchain'][k])
        poses_min.append((nm, rec['mech_rigidchain'][k], rec['mech_T'][k]))
    slew = v(tvc['rate_engine_dps_under_3.19Nm'])
    slew_V = sorted(slew.keys(), key=float)
    f_rock = v(tvc['rocking_mode_Hz'])
    date = datetime.date.today().isoformat()
    src = 'mechanical.json %s sha %s' % (ver, sha)
    tag_c = 'MECH' if shaft_pub is not None else 'FIT'

    def arr3(x, fmt='%.6f', suf='f'):
        return '{' + ', '.join('{' + ', '.join((fmt % c) + suf for c in row) + '}' for row in x) + '}'

    fwh = f'''// GENERATED by {GEN} - DO NOT EDIT. Regenerate when mechanical.json changes.
// Source: {src}, date {date}. Units SI. [MECH] = mechanical.json value, [DERIVED] = computed here,
// [FIT] = fitted here to mechanical.json values (generator header: horn plane not published, residual {res_fit:.3f} deg).
#pragma once
namespace ecu {{
namespace mech {{
// Cardan gimbal R = Rx(alpha) Ry(beta); alpha = outer axis (ring pins, +X), beta = inner axis (collar pins, +Y).
// Each TVC servo drives a pushrod (spherical bearings both ends) from its horn eye to a lever eye on the engine collar.
constexpr float kLeverAz_rad[2] = {{{math.radians(phi[0]):.6f}f, {math.radians(phi[1]):.6f}f}};   // [MECH] {phi} deg
constexpr float kLeverR_m = {r_e:.6f}f;        // [MECH] lever-eye radius from the engine axis
constexpr float kLeverBallZ_m = {z_b:.6f}f;    // [MECH] lever-eye height in the engine frame (pivot = 0)
constexpr float kHornR_m = {r_h:.6f}f;         // [MECH] servo horn radius
constexpr float kPushrod_m = {L:.6f}f;       // [MECH] eye to eye
constexpr float kGearRatio = {n_gear:.4f}f;          // [MECH] r_e / r_h at neutral
constexpr float kRangeVec_rad = {rng:.6f}f;    // [MECH/GNC] commanded limit on the VECTOR norm
constexpr float kStopCone_rad = {stop:.6f}f;   // [MECH] conical mechanical stop
// v2 exact pushrod-length kinematics: horn eye H(psi) = C + r_h (-cos(psi) u + sin(psi) z) (u horizontal, from the horn eye
// to the shaft at neutral), lever eye P = R(alpha, beta) P0; |P - H| = kPushrod_m; psi > 0 lifts the horn eye.
constexpr float kLeverEye0_m[2][3] = {arr3(lk.P0)};   // [MECH] lever_eye_xyz_m
constexpr float kShaftC_m[2][3] = {arr3(lk.C)};   // [{tag_c}] point on the horn rotation axis
constexpr float kHornU[2][2] = {{{{{lk.u[0][0]:.6f}f, {lk.u[0][1]:.6f}f}}, {{{lk.u[1][0]:.6f}f, {lk.u[1][1]:.6f}f}}}};   // [{tag_c}] horn plane direction
constexpr float kHornPlaneOff_deg = {0.0 if shaft_pub is not None else off:.3f}f;   // [{tag_c}] servo 1 horn plane = lever azimuth minus this (servo 2 mirrored)
constexpr float kPsiRange_deg[2] = {{{psi_rng[0]:.3f}f, {psi_rng[1]:.3f}f}};   // [DERIVED] servo angle min/max on the 7 deg cone (MECH {pub['cmd_7deg']['psi_min_deg'][0]} / {pub['cmd_7deg']['psi_max_deg'][0]})
constexpr float kPsiStop_deg[2] = {{{psi_stop[0]:.3f}f, {psi_stop[1]:.3f}f}};    // [DERIVED] first stop contact, each sense (MECH {pub['stop_8deg']['psi_min_deg'][0]} / {pub['stop_8deg']['psi_max_deg'][0]})
constexpr float kPsiClamp_rad[2] = {{{math.radians(psi_clamp[0]):.6f}f, {math.radians(psi_clamp[1]):.6f}f}};   // [DERIVED] horn clamp = extremes on the {math.degrees(0.5 * (rng + stop)):.1f} deg cone ({psi_clamp[0]:.2f} / {psi_clamp[1]:.2f} deg)
constexpr float kServoAtRange_deg = {max(-psi_rng[0], psi_rng[1]):.3f}f;   // [DERIVED] largest |psi| on the 7 deg cone
constexpr float kMixNeutral[2][2] = {arr3(mix, '%.4f')};   // [MECH check] d psi / d(alpha, beta) at neutral
}}  // namespace mech
}}  // namespace ecu
'''
    open(os.path.join(FW, 'src', 'core', 'mech_params.h'), 'w').write(fwh)
    silh = f'''// GENERATED by {GEN} - DO NOT EDIT. SIL 2-axis gimbal plant from {src}.
#pragma once
namespace sil {{
namespace mech {{
constexpr double k_I_wet_kgm2[2] = {{{I_wet[0][0]:.6e}, {I_wet[1][1]:.6e}}};   // [MECH] Ixx, Iyy about the pivot, full grain (engine group)
constexpr double k_I_mid_kgm2[2] = {{{I_mid[0][0]:.6e}, {I_mid[1][1]:.6e}}};   // [MECH] mid-burn
constexpr double k_I_dry_kgm2[2] = {{{I_dry[0][0]:.6e}, {I_dry[1][1]:.6e}}};   // [MECH] no grain
constexpr double k_I_ring_alpha_kgm2 = {I_ring:.6e};   // [MECH] ring group, alpha (outer) axis only
constexpr double k_K_hose_Nm_per_rad[2] = {{{k_hose[0]:.4f}, {k_hose[1]:.4f}}};   // [MECH DERIVED+ASSUMED range] radial routing 0.40 m
constexpr double k_M_fric_bearing_Nm = {v(hm['bearing_seal_friction_per_axis']):.4f};   // [MECH ASSUMED] 2 x 608-2RS seal drag per axis
constexpr double k_M_mis_full_Nm = {v(hm['thrust_misalignment']):.4f};         // [MECH] thrust misalignment at 500 N
constexpr double k_M_side_floor_Nm = {v(hm['nozzle_side_load_floor']):.4f};    // [MECH] separation side load (floor)
constexpr double k_M_lat_Nm = {v(hm['lateral_accel_m_alat_le']):.4f};          // [MECH] lateral acceleration x l_e
constexpr double k_M_vehacc_Nm = {v(hm['vehicle_angular_accel_Ipivot_x_omegadot']):.4f};   // [MECH] vehicle angular accel
constexpr double k_K_axacc_Nm_per_rad = {axacc_per_rad:.4f};   // [DERIVED] MECH axial-accel term / sin(range)
constexpr double k_hinge_linear_sum_Nm = {v(tvc['hinge_moment_linear_sum_Nm']):.4f};   // [MECH] operating linear sum
constexpr double k_hinge_struct_design_Nm = {v(tvc['hinge_moment_design_Nm']):.4f};   // [MECH] structural design load (servo stall)
constexpr double k_lever_r_m = {r_e:.6f}, k_lever_z_m = {z_b:.6f}, k_horn_r_m = {r_h:.6f}, k_pushrod_m = {L:.6f};   // [MECH]
constexpr double k_lever_az_rad[2] = {{{math.radians(phi[0]):.6f}, {math.radians(phi[1]):.6f}}};   // [MECH]
constexpr double k_lever_eye0_m[2][3] = {arr3(lk.P0, '%.7f', '')};   // [MECH]
constexpr double k_shaft_c_m[2][3] = {arr3(lk.C, '%.7f', '')};   // [{tag_c}]
constexpr double k_horn_u[2][2] = {{{{{lk.u[0][0]:.7f}, {lk.u[0][1]:.7f}}}, {{{lk.u[1][0]:.7f}, {lk.u[1][1]:.7f}}}}};   // [{tag_c}]
constexpr double k_stop_rad = {stop:.6f};   // [MECH] conical stop
// Structure (CalculiX FEA, axis_stiffness_table): K_struct = structure only (servo and rod chain rigid, 'mech_rigidchain');
// the rod chain per rod is DERIVED from mech_T (structure + chain) and mech_rigidchain at the centre pose.
constexpr double k_K_struct_centre_Nm_per_rad[2] = {{{K_struct_c[0]:.1f}, {K_struct_c[1]:.1f}}};   // [MECH FEA] alpha, beta
constexpr double k_K_struct_min_Nm_per_rad[2] = {{{poses_min[0][1]:.1f}, {poses_min[1][1]:.1f}}};   // [MECH FEA] lowest pose: {poses_min[0][0]} / {poses_min[1][0]}
constexpr double k_K_mechT_centre_Nm_per_rad[2] = {{{K_mechT_c[0]:.1f}, {K_mechT_c[1]:.1f}}};   // [MECH FEA] structure + chain
constexpr double k_k_chain_rod_N_per_m = {0.5 * (k_rod[0] + k_rod[1]):.4e};   // [DERIVED] per rod ({k_rod[0]:.4e} from alpha, {k_rod[1]:.4e} from beta)
constexpr double k_f_rock_mech_centre_Hz[2] = {{{cen['f_rock_Hz_smin_smax_mech']['mech_T'][0]:.1f}, {cen['f_rock_Hz_smin_smax_mech']['mech_T'][1]:.1f}}};   // [MECH] sqrt(K/I)/2pi, servo rigid
constexpr double k_slew_V[{len(slew_V)}] = {{{', '.join(slew_V)}}};   // [MECH] plug voltages of the slew table
constexpr double k_slew_worst_dps[{len(slew_V)}] = {{{', '.join('%.1f' % slew[x]['worst_dps'] for x in slew_V)}}};   // [MECH] worst direction at 7 deg
constexpr double k_slew_worst_dir_deg = {slew[slew_V[0]]['worst_dir_deg']:.1f};   // [MECH]
}}  // namespace mech
}}  // namespace sil
'''
    open(os.path.join(FW, 'sil', 'mech_tables.h'), 'w').write(silh)
    prov = {'generator': GEN, 'date': date, 'mechanical_json': {'version': ver, 'sha256_16': sha},
            'firmware': {'lever_az_deg': phi, 'lever_r_m': r_e, 'lever_eye_z_m': z_b, 'horn_r_m': r_h, 'pushrod_m': L,
                         'servo_shaft_z_m': z_s, 'gear_ratio': n_gear, 'range_vec_deg': v(gim['range_deg']),
                         'stop_deg': v(gim['mechanical_stop_deg']), 'shaft_C_m': lk.C.round(7).tolist(),
                         'horn_u': lk.u.round(7).tolist(), 'horn_plane_offset_deg': None if shaft_pub is not None else round(off, 3),
                         'horn_plane_source': fit_src, 'psi_range_deg': [round(x, 3) for x in psi_rng],
                         'psi_stop_deg': [round(x, 3) for x in psi_stop], 'psi_clamp_deg': [round(x, 3) for x in psi_clamp],
                         'mixing_neutral': mix.round(4).tolist()},
            'published_targets': pub, 'reproduced': {'cmd_7deg': ex_rng, 'stop_8deg': ex_stop},
            'checks': chk,
            'sil': {'I_wet': [I_wet[0][0], I_wet[1][1]], 'I_mid': [I_mid[0][0], I_mid[1][1]], 'I_dry': [I_dry[0][0], I_dry[1][1]],
                    'I_ring_alpha': I_ring, 'K_hose_range': k_hose, 'K_axacc_per_rad': axacc_per_rad,
                    'K_struct_centre': K_struct_c, 'K_mechT_centre': K_mechT_c, 'K_chain_axis': K_chain_ax, 'k_chain_rod': k_rod,
                    'K_struct_min_pose': poses_min, 'f_rock_mech_published_Hz': f_rock,
                    'slew_worst_dps': {x: slew[x]['worst_dps'] for x in slew_V}}}
    os.makedirs(RES, exist_ok=True)
    json.dump(prov, open(os.path.join(RES, 'gen_mech_params_v2.json'), 'w'), indent=1)
    print(json.dumps({'checks': chk, 'psi_range': psi_rng, 'psi_stop': psi_stop, 'psi_clamp': psi_clamp, 'off': off,
                      'k_rod': k_rod, 'K_struct_min': poses_min}, indent=1))


if __name__ == '__main__':
    main()
