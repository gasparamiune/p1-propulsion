"""TVC slew-rate and torque check for ENG-07 v2 (gimbal slew >= 100 deg/s across the full range). ARGOS H1, 06-electronics.

v1 2026-10-12. Lead decisions 2026-10-12 (hub CHANGELOG): ENG-07 slew raised 60 -> >= 100 deg/s (GNC sim6 v2.3: P(landing)
0.716 at 60 deg/s, 0.966 at 80, 0.984 at 100); "slew stays >= 100 deg/s across the full +/-7 deg range (margin at full
deflection)"; gimbal/mount parts designed to the actuator stall load 26.5 N m (6-DOF hinge torque p99 15.6, max 19.5 N m).

Independent analytic model (the SIL scenario S7 is the time-domain cross-check):
  * servo: Savox SB-2292SG, linear torque-speed line per supply voltage from the DATASHEET points in parts_db.py
    (stall torque, no-load time per 60 deg; the lower of two published torque sets). The published s/60 deg includes the
    acceleration from rest, so using it as the no-load speed is conservative.
  * kinematics: exact Cardan gimbal + vertical pushrods + clamp horns from interfaces/mechanical.json (read, not copied);
    horn angle psi_i = asin(dz_i / r_h); horn moment arm r_h cos(psi_i).
  * two servos share any engine motion through the kinematic Jacobian J (rows dz_i/d(alpha, beta)); along a direction u
    the available hinge moment at engine rate w is m(w) = min_i Ts (1 - s_i w / w_nl) / tau_i with s_i = |J_i u| / (r_h cos
    psi_i) (servo rad per engine rad) and tau_i = |(J^-T u)_i| r_h cos psi_i (servo torque per unit engine moment).
  * load opposing the slew: Mechanical's non-inertial hinge terms at their maxima, summed (conservative concurrency).
  * 1-DOF slews along u with the engine inertia plus the reflected servo inertia J_int (ASSUMED, as in the SIL).
Tags: DATASHEET, MECH (mechanical.json), LEAD (lead decision/relay), ASSUMED, DERIVED (computed here).
Usage: python3 tvc_slew_check_v1.py [--engine-root DIR] [--out ../results/tvc_slew_check_v1.json]
"""
import argparse
import datetime
import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parts_db as PDB  # noqa: E402

D2R = math.pi / 180.0
REQ_RATE_DPS = 100.0          # LEAD ENG-07 v2 (2026-10-12)
REQ_MARGIN = 1.20             # DESIGN: rate margin asked at full deflection ("margin at full deflection", LEAD)
REQ_RANGE_DEG = 7.0           # MECH/GNC commanded vector-norm limit
HINGE_P99_FLIGHT = 15.6       # LEAD relay of GNC sim6 v2.3 (6-DOF p99 hinge torque in flight)
HINGE_MAX = 19.5              # LEAD relay of GNC sim6 v2.3 (6-DOF maximum, incl. touchdown)
STRUCT_DESIGN = 26.5          # LEAD/MECH: parts designed to this actuator stall load at the engine [N m]
ROCK_MIN_HZ = 25.0            # gnc.json v1 engine rocking-mode requirement
PB_RAD = 2.0 * D2R            # ASSUMED servo proportional band (SIL ServoParams.pb_rad)
K_LINK = 2.0e6                # ASSUMED pushrod + ball links + bracket stiffness [N/m] (SIL Gimbal2Params.k_link)
J_INT = (1.0e-3, 2.0e-3, 4.0e-3)   # ASSUMED servo output-referred inertia [kg m2]; 2e-3 is the SIL value; bench-measure
DEADBAND_US = 1.0             # ASSUMED servo deadband (parts_db)
US_PER_DEG = 10.0             # DATASHEET 1000 us / 100 deg


def v(node):
    return node['v'] if isinstance(node, dict) and 'v' in node else node


def servo(V, conflict_set=False):
    """Stall torque [N m] and no-load speed [rad/s] at supply V, linear interpolation between the DATASHEET points."""
    tq = v(PDB.SB2292SG['torque_kgcm_conflict' if conflict_set else 'torque_kgcm'])
    sp = v(PDB.SB2292SG['speed_s_per_60deg'])
    pts = sorted(float(k) for k in tq)

    def lin(tab):
        if V <= pts[0]:
            a, b = pts[0], pts[1]
        elif V >= pts[-1]:
            a, b = pts[-2], pts[-1]
        else:
            a = max(p for p in pts if p <= V)
            b = min(p for p in pts if p > V)
        fa, fb = tab['%.1f' % a], tab['%.1f' % b]
        return fa + (fb - fa) * (V - a) / (b - a)
    Ts = lin(tq) * PDB.KGCM_TO_NM
    wnl = (math.pi / 3.0) / lin(sp)
    return Ts, wnl


class Geometry:
    def __init__(self, mech, r_h=None):
        tvc = mech['tvc_actuation']
        self.az = [math.radians(a) for a in v(tvc['lever_azimuth_deg'])]
        self.r_e = v(tvc['lever_radius_m'])
        self.z_b = v(tvc['lever_ball_z_m'])
        self.r_h = r_h if r_h else v(tvc['horn_radius_m'])
        mp = mech['gimballed_mass_properties']
        I = v(mp['wet_full_grain']['I_pivot_kgm2'])
        self.I = [I[0][0] + v(mp['ring_alpha_axis_only']['I_xx_kgm2']), I[1][1]]   # ring moves with alpha only
        hm = mech['tvc_actuation']['hinge_moment_terms_Nm']
        self.terms = {k: v(x) for k, x in hm.items()}

    def dz(self, a, b, i):
        x0, y0, z0 = self.r_e * math.cos(self.az[i]), self.r_e * math.sin(self.az[i]), self.z_b
        z1 = -x0 * math.sin(b) + z0 * math.cos(b)
        z2 = y0 * math.sin(a) + z1 * math.cos(a)
        return z2 - z0

    def jac(self, a, b):
        h = 1e-6
        return [[(self.dz(a + h, b, i) - self.dz(a - h, b, i)) / (2 * h), (self.dz(a, b + h, i) - self.dz(a, b - h, i)) / (2 * h)]
                for i in range(2)]

    def point(self, a, b, u):
        """Per-servo horn angle, speed ratio s_i and torque per unit engine moment tau_i along unit direction u."""
        J = self.jac(a, b)
        det = J[0][0] * J[1][1] - J[0][1] * J[1][0]
        # g = J^-T u : rod forces per unit generalised moment along u
        g = [(J[1][1] * u[0] - J[1][0] * u[1]) / det, (-J[0][1] * u[0] + J[0][0] * u[1]) / det]
        out = []
        for i in range(2):
            s = self.dz(a, b, i) / self.r_h
            if abs(s) >= 1.0:
                return None
            psi = math.asin(s)
            c = self.r_h * math.cos(psi)
            ju = J[i][0] * u[0] + J[i][1] * u[1]
            out.append({'psi': psi, 'c': c, 's': abs(ju) / c, 'tau': abs(g[i]) * c, 'ju': ju})
        return out

    def inertia(self, u):
        return self.I[0] * u[0] ** 2 + self.I[1] * u[1] ** 2


def worst_psi_deg(geo, deg, n_dir=360):
    """Largest horn angle anywhere on the circle of vector norm deg (inf if the rod would pass the horn tip)."""
    w = 0.0
    for k in range(n_dir):
        th = 2 * math.pi * k / n_dir
        for i in range(2):
            s = abs(geo.dz(deg * D2R * math.cos(th), deg * D2R * math.sin(th), i)) / geo.r_h
            if s >= 1.0:
                return float('inf')
            w = max(w, math.degrees(math.asin(s)))
    return w


def rate_max(pt, Ts, wnl, TL):
    """Steady engine rate [rad/s] along u with the load moment TL opposing the motion (min over the two servos)."""
    w = float('inf')
    for p in pt:
        if p['s'] < 1e-9:
            continue
        w = min(w, (wnl / p['s']) * (1.0 - TL * p['tau'] / Ts))
    return max(w, 0.0)


def m_avail(pt, Ts, wnl, w):
    m = float('inf')
    for p in pt:
        if p['tau'] < 1e-12:
            continue
        m = min(m, Ts * (1.0 - p['s'] * w / wnl) / p['tau'])
    return m


def stall_moment(pt, Ts):
    return min(Ts / p['tau'] for p in pt if p['tau'] > 1e-12)


def scan(geo, Ts, wnl, TL, rng_deg=REQ_RANGE_DEG, n_dir=72, n_mag=29):
    """Worst steady rate over the commanded disc (vector norm <= range) for motion along each radial direction, and
    along the per-axis paths (alpha with beta = 0, beta with alpha = 0)."""
    worst = {'rate_dps': 1e9}
    for k in range(n_dir):
        th = 2 * math.pi * k / n_dir
        u = (math.cos(th), math.sin(th))
        for j in range(n_mag):
            d = -rng_deg + 2 * rng_deg * j / (n_mag - 1)
            a, b = d * D2R * u[0], d * D2R * u[1]
            pt = geo.point(a, b, u)
            if pt is None:
                return {'rate_dps': 0.0, 'note': 'horn beyond 90 deg'}
            r = rate_max(pt, Ts, wnl, TL) / D2R
            if r < worst['rate_dps']:
                worst = {'rate_dps': r, 'dir_deg': math.degrees(th), 'at_deg': d,
                         'psi_deg': [math.degrees(p['psi']) for p in pt]}
    return worst


def axis_profile(geo, Ts, wnl, TL, ax, rng_deg=REQ_RANGE_DEG, n=57):
    u = (1.0, 0.0) if ax == 0 else (0.0, 1.0)
    prof = []
    for j in range(n):
        d = -rng_deg + 2 * rng_deg * j / (n - 1)
        a, b = (d * D2R, 0.0) if ax == 0 else (0.0, d * D2R)
        pt = geo.point(a, b, u)
        prof.append((d, rate_max(pt, Ts, wnl, TL) / D2R))
    return prof


def slew_time(geo, Ts, wnl, TL, J_int, u, d0=-REQ_RANGE_DEG, d1=REQ_RANGE_DEG, dt=2e-5):
    """1-DOF bang-coast slew along u from d0 to d1 [deg]: full drive on the torque-speed line until the steady rate,
    no deceleration phase (servo decelerates in its last few degrees; S7 measures the full step). Returns the time to
    cover |d1 - d0| and the mean rate over the middle 80 %."""
    d, w, t = d0 * D2R, 0.0, 0.0
    end = d1 * D2R
    t10 = t90 = None
    span = end - d
    while d < end and t < 2.0:
        a, b = d * u[0], d * u[1]
        pt = geo.point(a, b, u)
        Ieff = geo.inertia(u) + sum(J_int * p['s'] ** 2 for p in pt)
        m = m_avail(pt, Ts, wnl, w) - TL
        w = min(w + max(m, 0.0) / Ieff * dt, rate_max(pt, Ts, wnl, TL))
        d += w * dt
        t += dt
        f = (d - d0 * D2R) / span
        if t10 is None and f >= 0.1:
            t10 = t
        if t90 is None and f >= 0.9:
            t90 = t
    return t, (0.8 * span / (t90 - t10)) / D2R if (t10 and t90) else float('nan')


def rocking(geo, Ts, u=(1.0, 0.0)):
    pt = geo.point(0.0, 0.0, u)
    k_s = Ts / PB_RAD
    K = 0.0
    for p in pt:
        k_chain = 1.0 / (p['c'] ** 2 / k_s + 1.0 / K_LINK)   # servo + horn in series with the rod [N/m at the ball]
        K += k_chain * p['ju'] ** 2
    return math.sqrt(K / geo.inertia(u)) / (2 * math.pi), K


def rod_force_at_stall(geo, Ts):
    """Pushrod force [N] with the servo at stall: centre, worst point of the 7 deg range, and at the 8 deg conical stop
    (servo runaway into the stop). F = Ts / (r_h cos psi)."""
    out = {'centre_N': Ts / geo.r_h}
    for key, deg in (('range_7deg_N', REQ_RANGE_DEG), ('stop_8deg_N', 8.0)):
        p = worst_psi_deg(geo, deg)
        out[key] = Ts / (geo.r_h * math.cos(math.radians(p))) if p < 89.9 else float('inf')
    return {k: round(x, 0) for k, x in out.items()}


def rate_at(geo, Ts, wnl, TL, u, deg):
    """Worst of the two slew senses at +/-deg along u (steady loaded rate)."""
    r = []
    for sgn in (1, -1):
        d = sgn * deg * D2R
        pt = geo.point(d * u[0], d * u[1], u)
        r.append(rate_max(pt, Ts, wnl, TL) / D2R)
    return min(r)


def evaluate(geo, V, TL, conflict_set=False):
    Ts, wnl = servo(V, conflict_set)
    res = {'V': V, 'Ts_Nm': round(Ts, 3), 'w_nl_servo_dps': round(wnl / D2R, 1)}
    res['rod_force_at_stall'] = rod_force_at_stall(geo, Ts)
    rv = {}
    for nm, th in (('alpha', 0.0), ('beta', 90.0), ('dir65', 65.0)):
        u = (math.cos(math.radians(th)), math.sin(math.radians(th)))
        rv[nm] = {'%gdeg' % d: round(rate_at(geo, Ts, wnl, TL, u, d), 1) for d in (0.0, 4.0, 5.0, 6.0, 7.0)}
    res['loaded_rate_vs_angle_dps'] = rv
    res['noload_worst'] = scan(geo, Ts, wnl, 0.0)
    res['loaded_worst'] = scan(geo, Ts, wnl, TL)
    for ax, nm in ((0, 'alpha'), (1, 'beta')):
        prof = axis_profile(geo, Ts, wnl, TL, ax)
        res['loaded_axis_min_' + nm] = round(min(r for _, r in prof), 1)
        res['loaded_axis_centre_' + nm] = round(prof[len(prof) // 2][1], 1)
        res['loaded_axis_at7_' + nm] = round(min(prof[0][1], prof[-1][1]), 1)
        res['loaded_axis_within5_' + nm] = round(min(r for d, r in prof if abs(d) <= 5.0 + 1e-9), 1)
    st = []
    for k in range(72):
        th = 2 * math.pi * k / 72
        u = (math.cos(th), math.sin(th))
        for d in (0.0, REQ_RANGE_DEG):
            pt = geo.point(d * D2R * u[0], d * D2R * u[1], u)
            st.append(stall_moment(pt, Ts))
    res['stall_moment_min_Nm'] = round(min(st), 2)    # weakest holding direction anywhere in the range
    res['stall_moment_max_Nm'] = round(max(st), 2)    # largest moment the actuators can put on the structure
    f, K = rocking(geo, Ts)
    res['rocking_alpha_Hz'] = round(f, 1)
    res['K_alpha_Nm_per_rad'] = round(K, 0)
    res['slew_14deg'] = {}
    for J in J_INT:
        ta, ma = slew_time(geo, Ts, wnl, TL, J, (1.0, 0.0))
        tb, mb = slew_time(geo, Ts, wnl, TL, J, (0.0, 1.0))
        res['slew_14deg']['J_int_%.0e' % J] = {'alpha_s': round(ta, 4), 'alpha_mean_mid80_dps': round(ma, 1),
                                               'beta_s': round(tb, 4), 'beta_mean_mid80_dps': round(mb, 1)}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine-root', default=os.environ.get('ENGINE_ROOT', '/home/claude/work/shared-fallback/engine'))
    ap.add_argument('--out', default=os.path.join(HERE, '..', 'results', 'tvc_slew_check_v1.json'))
    args = ap.parse_args()
    fn = os.path.join(args.engine_root, 'interfaces', 'mechanical.json')
    raw = open(fn, 'rb').read()
    mech = json.loads(raw)
    geo0 = Geometry(mech)
    terms = geo0.terms
    # non-inertial hinge terms (the gimbal's own acceleration term is excluded: at the steady slew rate it is zero)
    TL_keys = [k for k in terms if not k.startswith('inertia_')]
    TL = sum(abs(terms[k]) for k in TL_keys)
    out = {'tool': 'calc/tvc_slew_check_v1.py', 'date': datetime.date.today().isoformat(),
           'inputs': {'mechanical_json': {'version': mech.get('version'), 'sha256_16': hashlib.sha256(raw).hexdigest()[:16]},
                      'servo': 'Savox SB-2292SG, ' + PDB.SB2292SG['torque_kgcm']['src'] + ' (lower torque set)',
                      'req_rate_dps': {'v': REQ_RATE_DPS, 'tag': 'LEAD', 'src': 'ENG-07 v2, hub CHANGELOG 2026-10-12'},
                      'req_margin': {'v': REQ_MARGIN, 'tag': 'DESIGN', 'note': 'LEAD asks for margin at full deflection'},
                      'hinge_p99_flight_Nm': {'v': HINGE_P99_FLIGHT, 'tag': 'LEAD', 'src': 'GNC sim6 v2.3 relay'},
                      'hinge_max_Nm': {'v': HINGE_MAX, 'tag': 'LEAD', 'src': 'GNC sim6 v2.3 relay (incl. touchdown)'},
                      'structure_design_Nm': {'v': STRUCT_DESIGN, 'tag': 'LEAD/MECH'},
                      'slew_load_Nm': {'v': round(TL, 3), 'tag': 'DERIVED', 'src': 'sum of mechanical.json non-inertial hinge terms: ' + ', '.join(TL_keys)},
                      'pb_deg': {'v': PB_RAD / D2R, 'tag': 'ASSUMED'}, 'k_link_N_per_m': {'v': K_LINK, 'tag': 'ASSUMED'},
                      'J_int_kgm2': {'v': list(J_INT), 'tag': 'ASSUMED', 'note': 'servo output-referred inertia; bench step test'},
                      'r_e_m': geo0.r_e, 'r_h_mech_m': geo0.r_h, 'I_axes_kgm2': geo0.I}}
    # A. baseline geometry (mechanical.json) at the three supply voltages
    base = {}
    for V in (6.6, 7.4, 7.8, 8.0, 8.4):
        base['%.1fV' % V] = evaluate(geo0, V, TL)
    base['7.4V_conflict_torque_set'] = evaluate(geo0, 7.4, TL, conflict_set=True)
    out['A_baseline_mech_v1'] = base
    # B. horn-radius trade (lever radius fixed by the collar; only n = r_e / r_h matters for angles, rates and moments, while
    #    rod forces scale with 1 / r_h and the linkage stiffness at the engine with r_e^2)
    VOLTS = (6.6, 7.4, 7.6, 7.8, 8.4)
    trade = []
    for r_h_mm in (6.0, 7.0, 8.0, 9.0, 9.6, 10.0, 10.5, 11.0, 12.0):
        geo = Geometry(mech, r_h_mm * 1e-3)
        row = {'r_h_mm': r_h_mm, 'n_small_angle': round(geo.r_e / geo.r_h, 2),
               'psi_worst_at_7deg': round(worst_psi_deg(geo, REQ_RANGE_DEG), 1),
               'psi_worst_at_8deg_stop': round(worst_psi_deg(geo, 8.0), 1)}
        if row['psi_worst_at_7deg'] > 50.0 or row['psi_worst_at_8deg_stop'] > 65.0:
            row['infeasible'] = ('horn angle beyond the servo operating half-travel 50 deg at 7 deg or the 65 deg maximum at '
                                 'the 8 deg stop (DATASHEET pulse range)')
            trade.append(row)
            continue
        row['struct_load_8V4_stall_Nm'] = evaluate(geo, 8.4, TL)['stall_moment_max_Nm']
        for V in VOLTS:
            e = evaluate(geo, V, TL)
            noload = e['noload_worst']['rate_dps']
            loaded = e['loaded_worst']['rate_dps']
            x = {'noload_worst_dps': round(noload, 1), 'loaded_worst_dps': round(loaded, 1),
                 'loaded_worst_at': {k: (round(y, 1) if isinstance(y, float) else [round(z, 1) for z in y])
                                     for k, y in e['loaded_worst'].items() if k != 'rate_dps'},
                 'loaded_axis_min_dps': [e['loaded_axis_min_alpha'], e['loaded_axis_min_beta']],
                 'loaded_axis_within5_dps': [e['loaded_axis_within5_alpha'], e['loaded_axis_within5_beta']],
                 'margin_vs_100': round(loaded / REQ_RATE_DPS, 3),
                 'stall_moment_min_Nm': e['stall_moment_min_Nm'], 'stall_moment_max_Nm': e['stall_moment_max_Nm'],
                 'rocking_alpha_Hz': e['rocking_alpha_Hz'], 'slew_14deg_Jint2e-3': e['slew_14deg']['J_int_2e-03'],
                 'resolution_deg_centre': round(DEADBAND_US / US_PER_DEG * geo.r_h / geo.r_e, 4),
                 'rod_force_at_stall_N': e['rod_force_at_stall'], 'loaded_rate_vs_angle_dps': e['loaded_rate_vs_angle_dps']}
            x['checks'] = {'rate_ge_100x1.2': loaded >= REQ_RATE_DPS * REQ_MARGIN, 'rate_ge_100': loaded >= REQ_RATE_DPS,
                           'hold_p99_15.6': e['stall_moment_min_Nm'] >= HINGE_P99_FLIGHT,
                           'rocking_ge_25Hz': e['rocking_alpha_Hz'] >= ROCK_MIN_HZ,
                           'struct_le_26.5': row['struct_load_8V4_stall_Nm'] <= STRUCT_DESIGN + 1e-6}
            row['%.1fV' % V] = x
        trade.append(row)
    out['B_horn_radius_trade'] = trade
    # C. verdict and recommendation
    b74, b84, b66 = base['7.4V'], base['8.4V'], base['6.6V']

    def meets(V, skip=()):
        return [r['r_h_mm'] for r in trade if 'infeasible' not in r and all(ok for k, ok in r['%.1fV' % V]['checks'].items() if k not in skip)]
    REC_RH, REC_V = 10.0, 7.6
    rec = next(r for r in trade if r['r_h_mm'] == REC_RH)
    out['C_verdict'] = {
        'baseline_n6_2S': ('FAILS ENG-07 v2 at full deflection: loaded worst-case %.1f deg/s at 7.4 V (%.1f at 6.6 V, %.1f at '
                           '8.4 V); no-load worst %.1f deg/s at 7.4 V; per-axis at 7 deg %.1f/%.1f deg/s at 7.4 V' %
                           (b74['loaded_worst']['rate_dps'], b66['loaded_worst']['rate_dps'], b84['loaded_worst']['rate_dps'],
                            b74['noload_worst']['rate_dps'], b74['loaded_axis_min_alpha'], b74['loaded_axis_min_beta'])),
        'horn_radii_meeting_all_checks': {'%.1fV' % V: meets(V) for V in VOLTS},
        'horn_radii_meeting_rate_hold_rocking (structure re-rated by Mechanical)': {'%.1fV' % V: meets(V, ('struct_le_26.5',)) for V in VOLTS},
        'recommendation': {
            'tag': 'DESIGN (Electronics proposal; Mechanical owns the linkage)',
            'n': rec['n_small_angle'], 'r_h_mm_with_r_e_48mm': REC_RH,
            'rail': '2S LiPo direct through the watchdog-gated TVC switch (no regulator); design point >= %.1f V at the servo under '
                    'peak load: ARM permit raised 7.8 -> 8.1 V, pack DC IR <= 15 mOhm, servo branch <= 20 mOhm (ASSUMED until measured)' % REC_V,
            'at_design_point': {k: rec['%.1fV' % REC_V][k] for k in ('loaded_worst_dps', 'margin_vs_100', 'stall_moment_min_Nm', 'rocking_alpha_Hz',
                                                                      'loaded_rate_vs_angle_dps', 'checks')},
            'degraded_7V4': {k: rec['7.4V'][k] for k in ('loaded_worst_dps', 'margin_vs_100', 'stall_moment_min_Nm')},
            'degraded_6V6': {k: rec['6.6V'][k] for k in ('loaded_worst_dps', 'margin_vs_100', 'stall_moment_min_Nm')},
            'structure_at_8V4_stall': {'max_engine_moment_Nm': rec['struct_load_8V4_stall_Nm'], 'rod_force_N': rec['8.4V']['rod_force_at_stall_N'],
                                       'mech_v1_n6_max_engine_moment_Nm': b84['stall_moment_max_Nm'], 'mech_v1_n6_rod_force_N': b84['rod_force_at_stall'],
                                       'note': 'parts are designed to 26.5 N m = centre value of the 8.4 V stall x n 6; the stall moment grows with '
                                               'the horn angle (n_eff = n / cos psi) and both servos can push together; the 8 deg stop case is a '
                                               'servo runaway into the conical stop'}},
        'note': ('rate checks use the steady torque-speed line with the summed non-inertial hinge load; holding uses the '
                 'weakest direction anywhere in the range; rocking uses an ASSUMED 2 deg proportional band and 2e6 N/m linkage; '
                 'all to be replaced by bench data (servo torque-speed at 7.4/8.4 V, step response, stiffness)')}
    # rate-vs-angle table for Mechanical (CSV)
    import csv
    csvp = os.path.join(os.path.dirname(os.path.abspath(args.out)), 'tvc_rate_vs_angle_v1.csv')
    with open(csvp, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['r_h_mm', 'r_e_mm', 'n', 'V_servo', 'direction', 'engine_angle_deg', 'loaded_rate_dps', 'noload_rate_dps', 'load_Nm',
                    'note'])
        for r_h_mm in (8.0, REC_RH):
            geo = Geometry(mech, r_h_mm * 1e-3)
            for V in VOLTS:
                Ts, wnl = servo(V)
                for nm, th in (('alpha', 0.0), ('beta', 90.0), ('worst_65deg', 65.0)):
                    u = (math.cos(math.radians(th)), math.sin(math.radians(th)))
                    for d in (0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0):
                        w.writerow([r_h_mm, round(geo.r_e * 1e3, 1), round(geo.r_e / geo.r_h, 2), V, nm, d,
                                    round(rate_at(geo, Ts, wnl, TL, u, d), 1), round(rate_at(geo, Ts, wnl, 0.0, u, d), 1), round(TL, 2),
                                    'MECH v1' if r_h_mm == 8.0 else 'Electronics proposal'])
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    json.dump(out, open(args.out, 'w'), indent=1)
    # text summary
    L = []
    L.append('TVC slew check v1 (%s), mechanical.json %s sha %s, slew load %.2f N m (non-inertial terms summed)' %
             (out['date'], mech.get('version'), out['inputs']['mechanical_json']['sha256_16'], TL))
    for k, e in base.items():
        L.append('A %-26s Ts %.2f N m, w_nl %.0f deg/s | worst no-load %.1f, loaded %.1f deg/s (dir %.0f, at %.1f deg, psi %s) | '
                 'axis min a/b %.1f/%.1f, within 5 deg %.1f/%.1f | hold min %.1f, struct max %.1f N m | rock %.1f Hz | '
                 'slew14 a %.3f s (J 2e-3)' % (k, e['Ts_Nm'], e['w_nl_servo_dps'], e['noload_worst']['rate_dps'], e['loaded_worst']['rate_dps'],
                                                e['loaded_worst'].get('dir_deg', 0), e['loaded_worst'].get('at_deg', 0),
                                                [round(x, 1) for x in e['loaded_worst'].get('psi_deg', [])],
                                                e['loaded_axis_min_alpha'], e['loaded_axis_min_beta'], e['loaded_axis_within5_alpha'],
                                                e['loaded_axis_within5_beta'], e['stall_moment_min_Nm'], e['stall_moment_max_Nm'],
                                                e['rocking_alpha_Hz'], e['slew_14deg']['J_int_2e-03']['alpha_s']))
    for k, e in base.items():
        L.append('A %-26s loaded rate vs angle (deg/s, worst sense): %s | rod at stall %s' % (k, json.dumps(e['loaded_rate_vs_angle_dps']), json.dumps(e['rod_force_at_stall'])))
    L.append('B horn radius trade (r_e %.0f mm):' % (geo0.r_e * 1e3))
    for r in trade:
        if 'infeasible' in r:
            L.append('  r_h %4.1f mm n %.2f: INFEASIBLE (psi %.1f deg at 7 deg, %.1f at the stop)' % (r['r_h_mm'], r['n_small_angle'],
                                                                                                 r['psi_worst_at_7deg'], r['psi_worst_at_8deg_stop']))
            continue
        for V in VOLTS:
            x = r['%.1fV' % V]
            L.append('  r_h %4.1f mm n %.2f psi7 %.1f %.1fV: worst loaded %.1f (no-load %.1f) deg/s, margin %.2f | hold %.1f N m | rock %.1f Hz | '
                     'struct(8.4V stall) %.1f N m | rod %s | %s' % (r['r_h_mm'], r['n_small_angle'], r['psi_worst_at_7deg'], V, x['loaded_worst_dps'],
                                                                     x['noload_worst_dps'], x['margin_vs_100'], x['stall_moment_min_Nm'], x['rocking_alpha_Hz'],
                                                                     r['struct_load_8V4_stall_Nm'], json.dumps(x['rod_force_at_stall_N']),
                                                                     ' '.join(k + '=' + ('Y' if ok else 'N') for k, ok in x['checks'].items())))
    L.append('C ' + json.dumps(out['C_verdict']))
    txt = '\n'.join(L)
    open(os.path.splitext(args.out)[0] + '.txt', 'w').write(txt + '\n')
    print(txt)


if __name__ == '__main__':
    main()
