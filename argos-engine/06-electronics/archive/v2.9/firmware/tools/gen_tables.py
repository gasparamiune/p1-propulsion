"""Generate firmware constants, the ECU feed-forward valve map and the SIL plant tables from the published interfaces.

Electronics v3.3 (2026-10-13, firmware v2.8.3): reads gnc.json v3 (published 2026-10-13, sha 3e97c378cfebee95; the v3.2 generator
failed on it: KeyError hinge_moment.flight_p99_Nm, found by firmware/tools/sil_manifest_v1.py as a STALE gnc.json reference).
New: kGncShapeAccel_radps2 from flight_software.gimbal_command_tracker (rate- and acceleration-limited tracker that replaces the
plain 100 deg/s slew limiter in the ECU TvcShaper; cross-checked against requirements.gimbal.command_shaping_in_ecu
accel_limit_dps2 and the slew limit); gnc.json v2 files still work (accel 0 = plain limiter). SIL documentation constants:
hinge (v3 keys design_load_engine_moment_Nm and the delivered MC p99/max table) and the rocking-mode floor (v3 dict: tuned-notch
value, fixed-notch value carried). Tags name the gnc.json version read. v3.2 archived as archive/gen_tables_v3p2.py (its
engine_params.h / gnc_tables.h as archive/engine_params_v3p2.h / gnc_tables_v3p2.h).
Electronics v3.2 (2026-10-13): adds kPintleIgnitionLiftLow_m = the lift of the LOW end of Combustion's ignition flow range
(12.5 %, read from the same 'pintle to the ignition lift' step and the throttle points) for the firmware v2.7 ground
timing-only start (Combustion review RC-01: timing-only allowed on the ground with a documented reduced inventory); the
kTorchConfirmBy_s comment names the selected sensor (P_torch). Everything else unchanged; v3.1 archived as
archive/gen_tables_v3p1.py (its engine_params.h as archive/engine_params_v3p1.h).
Electronics v3.1 (2026-10-13): adds the relight vapour purge (lead decision C7, 2026-10-12) from Combustion's
02-combustion/data/v2/low_inlet_check_v2p3.json (named in the CHANGELOG lead decision and Combustion's judgement line;
not yet carried in combustion.json) -> engine_params.h kRelightPurge* and the SIL vapour-purge state. v3 archived as
archive/gen_tables_v3.py (its output results/gen_tables_v3.json kept). Supersedes v2.1 (archive/gen_tables_v2p1.py).
Reads (never hard-codes another owner's number; every value below is read from the file named):
  interfaces/combustion.json (v2.1)      gas path, throttle points, pressure limits (lead decisions as recorded by
                                         Combustion), pintle stroke, igniter sequence + electrical data, priming rule,
                                         valve->Pc plant fit, throttle_map_csv (map v2: P_tank x D_port x thrust fraction)
  02-combustion/inputs/combustion_v1.json  v1 injector geometry (metering-cone half angle, stem, manifold volume): v2 states
                                         'pintle (needle-in-seat), unchanged from v1' and does not republish them
  02-combustion/data/perf_table_ABS_TYP_v1_shifting_v1.json  CEA grids (the table Combustion's v2 runs still use)
  interfaces/gnc.json (v3; v2 accepted)  gimbal requirements + mandatory ECU command shaping and tracker, link-loss policy, rocking mode
  ../results/gen_tables_v2.json          gnc.json v1 mid-pivot hinge terms for the single-axis SIL model (gnc.json v2 does
                                         not republish them; their v1 sha is carried along)
  ../results/pintle_mini_servo_v1.json   Electronics pintle drive selection: MKS HV69 on an in-line crank-slider (TOG),
                                         link length and spring from Mechanical's message (tagged there)
  CoolProp 'NitrousOxide' (Lemmon & Span 2006 EOS) for saturation and the HEM flux table
Writes:
  src/core/engine_params.h      engine constants, thrust<->Pc table, crank-slider linkage, torch/priming sequence, GNC values
  src/core/valve_map_table.h    ECU feed-forward lift map + plant gain, from Combustion's throttle_map_v2.csv (initial port).
                                v2.1 generated it from the SIL plant; v3 uses Combustion's published map so that the SIL
                                (Electronics' own plant) runs the controller against a model it was NOT tuned on.
  sil/plant_tables.h            SIL plant: N2O saturation, HEM flux table (the Dyer blend is formed at run time with the
                                combustion v2 inlet convention), CEA grids, combustion constants
  sil/gnc_tables.h              SIL single-axis gimbal load model (gnc v1 terms) + gnc v2 requirements
  ../results/gen_tables_v3p1.json provenance (versions + sha256) and the Dyer cross-check against throttle_map_v2.csv
Injector flux convention (Combustion v2, 02-combustion/src/injector.py): liquid at the tank temperature T1 and the
injector inlet pressure P1 = P_tank - dp_line(mdot); P1 <= Pv(T1) -> saturated-liquid properties at T1;
G = k/(1+k) G_SPI + 1/(1+k) G_HEM, k = sqrt((P1-P2)/(Pv-P2)) (J. Dyer et al., AIAA 2007-5702). Implemented here
independently (not imported) so that agreement with Combustion's map is a cross-check of both.
Usage: /opt/engine-venv/bin/python gen_tables.py [--engine-root DIR] [--fast]
"""
from __future__ import annotations
import argparse, csv, datetime, hashlib, json, math, os, re
import numpy as np
import CoolProp.CoolProp as CP
from scipy.interpolate import PchipInterpolator

HERE = os.path.dirname(os.path.abspath(__file__))
FW = os.path.dirname(HERE)
RES = os.path.join(FW, '..', 'results')
FL = 'NitrousOxide'
AS = CP.AbstractState('HEOS', FL)
PA = 101325.0
GEN_VERSION = 'v3.3'


def sha(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def V(node):
    """value of a tagged node {'v': ..., 'tag': ...} or the node itself"""
    return node['v'] if isinstance(node, dict) and 'v' in node else node


def dig(d, *paths):
    """first existing dotted path (v2 key layout first, v1 fallback after); returns (value, path)"""
    for p in paths:
        cur, ok = d, True
        for k in p.split('.'):
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                ok = False
                break
        if ok:
            return cur, p
    raise KeyError('none of ' + ', '.join(paths))


# ------------------------------------------------------------------------------------ N2O
def sat(T):
    AS.update(CP.QT_INPUTS, 0.0, T); p = AS.p(); rl = AS.rhomass(); ul = AS.umass(); hl = AS.hmass(); sl = AS.smass()
    AS.update(CP.QT_INPUTS, 1.0, T); rv = AS.rhomass(); uv = AS.umass(); hv = AS.hmass()
    return p, rl, rv, ul, uv, hl, hv, sl


def g_hem_sat(T, P2, n=80):
    """isentropic homogeneous-equilibrium flux from saturated liquid at T, maximised over the throat pressure (choking)"""
    p1, rl, rv, ul, uv, h1, hv, s1 = sat(T)
    if P2 >= p1 * 0.9999:
        return 0.0
    ps = np.linspace(max(P2, 0.3e5), p1 * 0.9999, n)
    best, bp = 0.0, ps[0]
    for p in ps:
        AS.update(CP.PSmass_INPUTS, float(p), s1); dh = h1 - AS.hmass()
        if dh > 0:
            g = AS.rhomass() * math.sqrt(2 * dh)
            if g > best:
                best, bp = g, p
    d = ps[1] - ps[0]
    for _ in range(25):   # local refinement of the maximum
        cand = [max(P2, bp - d), bp, min(p1 * 0.9999, bp + d)]
        vals = []
        for p in cand:
            AS.update(CP.PSmass_INPUTS, float(p), s1); dh = h1 - AS.hmass()
            vals.append(AS.rhomass() * math.sqrt(2 * dh) if dh > 0 else 0.0)
        i = int(np.argmax(vals)); bp = cand[i]; best = max(best, vals[i]); d *= 0.5
    return best


def g_dyer_v2(T1, P1, P2, ghem):
    """Dyer blend with the combustion v2 inlet convention (saturated-liquid properties at T1 when P1 <= Pv)"""
    pv, rl = sat(T1)[0], sat(T1)[1]
    if P1 <= P2:
        return 0.0
    spi = math.sqrt(2.0 * rl * (P1 - P2))
    if P2 >= pv:
        return spi
    k = math.sqrt((P1 - P2) / (pv - P2))
    return k / (1 + k) * spi + 1.0 / (1 + k) * ghem


def pintle_area(h, Ds, a):
    """frustum between the sharp seat (Ds) and the metering cone (half angle a), capped at the seat area
    (combustion v1/v2 law, 02-combustion/src/injector.py pintle_area)"""
    s = max(0.0, h) * math.sin(a)
    A_seat = math.pi * Ds * Ds / 4.0
    disc = Ds * Ds - 4.0 * math.cos(a) * A_seat / math.pi
    s_star = (Ds - math.sqrt(max(disc, 0.0))) / (2.0 * math.cos(a))
    return math.pi * s * (Ds - s * math.cos(a)) if s < s_star else A_seat


# ------------------------------------------------------------------------------------ helpers
def carr(name, a, fmt='{:.6e}'):
    a = np.asarray(a)
    if a.ndim == 1:
        return f"constexpr double {name}[{a.shape[0]}] = {{" + ', '.join(fmt.format(v) for v in a) + "};\n"
    rows = ',\n  '.join('{' + ', '.join(fmt.format(v) for v in r) + '}' for r in a)
    return f"constexpr double {name}[{a.shape[0]}][{a.shape[1]}] = {{\n  {rows}}};\n"


def farr2(name, a, dims, fmt='{:.4e}f'):
    rows = ',\n  '.join('{' + ', '.join(fmt.format(v) for v in r) + '}' for r in a)
    return f"constexpr float {name}[{dims[0]}][{dims[1]}] = {{\n  {rows}\n}};\n"


def find_step(seq, pattern):
    for st in seq:
        if re.search(pattern, st['action'], re.I):
            return st
    raise SystemExit('combustion.json igniter.sequence.start: no step matching ' + pattern)


def num(pattern, text, what):
    m = re.search(pattern, text, re.I)
    if not m:
        raise SystemExit(f'cannot parse {what} from: {text[:200]}')
    return float(m.group(1))


class CrankSlider:
    """in-line crank-slider (pintle_mini_servo_v1 'TOG'): s(phi) = r cos phi + sqrt(L^2 - r^2 sin^2 phi), phi from top dead
    centre; lift x = s(phi_c) - s(phi) for phi > phi_c (tension link, lost motion below phi_c)"""

    def __init__(self, r, phi_c, L):
        self.r, self.phi_c, self.L = r, phi_c, L
        self.s0 = self.s(phi_c)

    def s(self, phi):
        return self.r * math.cos(phi) + math.sqrt(self.L ** 2 - (self.r * math.sin(phi)) ** 2)

    def x(self, phi):
        return max(0.0, self.s0 - self.s(phi)) if phi > self.phi_c else 0.0

    def phi(self, x):   # closed form: cos phi = (S^2 + r^2 - L^2) / (2 S r), S = s(phi_c) - x
        if x <= 0:
            return self.phi_c
        S = self.s0 - x
        return math.acos(max(-1.0, min(1.0, (S * S + self.r ** 2 - self.L ** 2) / (2 * S * self.r))))

    def dxdphi(self, phi):
        q = math.sqrt(self.L ** 2 - (self.r * math.sin(phi)) ** 2)
        return self.r * math.sin(phi) * (1.0 + self.r * math.cos(phi) / q)


# ------------------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine-root', default=os.environ.get('ENGINE_ROOT', '/home/claude/work/shared-fallback/engine'))
    ap.add_argument('--fast', action='store_true', help='coarse HEM grid (debug)')
    a = ap.parse_args()
    ER = a.engine_root
    f_comb = os.path.join(ER, 'interfaces', 'combustion.json')
    f_comb1 = os.path.join(ER, '02-combustion', 'inputs', 'combustion_v1.json')
    f_gnc = os.path.join(ER, 'interfaces', 'gnc.json')
    f_gnc1 = os.path.join(RES, 'gen_tables_v2.json')
    f_pint = os.path.join(RES, 'pintle_mini_servo_v1.json')
    C = json.load(open(f_comb)); C1 = json.load(open(f_comb1)); GN = json.load(open(f_gnc))
    G1 = json.load(open(f_gnc1)); PM = json.load(open(f_pint))
    perf_fn = os.path.join(ER, '02-combustion', 'data', 'perf_table_ABS_TYP_v1_shifting_v1.json')
    PT = json.load(open(perf_fn))
    map_fn = V(C['operating_points']['throttle_map_csv'])
    if not os.path.exists(map_fn):   # the path in the JSON may name the canonical mount; resolve it under ER
        map_fn = os.path.join(ER, map_fn.split('/engine/', 1)[1])
    prov = {'combustion.json': [C['version'], sha(f_comb)], 'combustion_v1.json (02-combustion/inputs)': [C1['version'], sha(f_comb1)],
            'gnc.json': [GN['version'], sha(f_gnc)], 'gen_tables_v2.json (gnc v1 terms)': [G1['version'], sha(f_gnc1),
                                                                                           G1['provenance']['gnc.json']],
            'pintle_mini_servo_v1.json': [PM['version'], sha(f_pint)], 'throttle_map_v2.csv': sha(map_fn),
            'perf_table': [PT['version'], sha(perf_fn), PT['source']], 'CoolProp': CP.get_global_param_string('version'),
            'date': datetime.date.today().isoformat(), 'generator': 'firmware/tools/gen_tables.py ' + GEN_VERSION}
    gp = C['gas_path']; noz = gp['nozzle']; gr = gp['grain']; op = C['operating_points']; va = C['valves_and_actuators']
    used = {}   # path log: which key layout was read

    # ---------------------------------------------------------------- combustion values (v2 keys, v1 fallbacks)
    At = V(noz['throat_area_m2']); eps = V(noz['expansion_ratio']); Ae = At * eps
    pts = V(op['throttle_points_20C_initial_port'])
    srt = sorted(pts, key=lambda p: p['Pc_Pa'])
    thr_pc = [p['Pc_Pa'] for p in srt]; thr_fv = [p['F_N'] + PA * Ae for p in srt]
    X = np.array([p['Pc_Pa'] * At for p in pts]); Y = np.array([p['F_N'] + PA * Ae for p in pts])
    CfE = float((X @ Y) / (X @ X)); fit_err = (CfE * X - PA * Ae) - np.array([p['F_N'] for p in pts])
    pc_max = V(op['max_thrust']['Pc_Pa']); F_max = V(op['max_thrust']['F_N'])
    n, used['pc_meop'] = dig(op, 'pressure_limits.chamber_MEOP_Pa', 'chamber_MEOP_Pa'); pc_meop = V(n)
    n, used['pc_cap'] = dig(op, 'pressure_limits.normal_cap_Pa'); pc_cap = V(n)
    n, used['pc_abort'] = dig(op, 'pressure_limits.abort_Pa'); pc_abort = V(n)
    n, used['pc_proof'] = dig(op, 'pressure_limits.proof_Pa'); pc_proof = V(n)
    tank_meop = V(op['tank_MEOP_Pa'])
    pc_floor = V(op['floor_stretch_12p5pct']['Pc_Pa'])
    rule = V(op['thrust_ceiling_rule'])
    m = re.search(r"dP/Pc\s*>=\s*([\d.]+)", rule) or re.search(r"/ ?([\d.]+)", rule)
    dp_over_pc_min = float(m.group(1)) if 'dP/Pc' in rule else float(m.group(1)) - 1.0
    n, used['stroke'] = dig(va, 'pintle_actuator.stroke_m', 'pintle_actuator_requirements.stroke_m'); stroke = V(n)
    # ignition lift: Combustion v2 'pintle to the ignition lift (12.5-20 % flow ...)'. ELEC choice: the 20 % point
    # (lead 2026-10-12 / Combustion actuator_rate_check_v2: 20 % start reaches 90 % in 0.43-0.44 s, 12.5 % in 0.52-0.53 s
    # vs ENG-04 0.5 s; GNC to confirm the relight start level)
    IGN_FRAC = 0.20
    ign = C['igniter']; seq = V(ign['sequence'])['start']; el = V(ign['electrical'])
    s_ign = find_step(seq, r'pintle to the ignition lift')
    lo_pct = num(r'\(([\d.]+)-[\d.]+ % flow', s_ign['action'], 'ignition flow range low')
    hi_pct = num(r'\([\d.]+-([\d.]+) % flow', s_ign['action'], 'ignition flow range high')
    if not (lo_pct / 100 - 1e-9 <= IGN_FRAC <= hi_pct / 100 + 1e-9):
        raise SystemExit(f'ignition fraction {IGN_FRAC} outside Combustion range {lo_pct}-{hi_pct} %')
    lift_ign = [p['pintle_lift_m'] for p in pts if abs(p['fraction'] - IGN_FRAC) < 1e-6][0]
    # v3.2: the low end of Combustion's ignition range (ground timing-only start, firmware v2.7)
    lo_rows = [p for p in pts if abs(p['fraction'] - lo_pct / 100) < 1e-6]
    if not lo_rows:
        raise SystemExit('no throttle point at the low end of the ignition range (%g %%)' % lo_pct)
    lift_ign_lo = lo_rows[0]['pintle_lift_m']; F_ign_lo = lo_rows[0]['F_N']
    F_ign = [p['F_N'] for p in pts if abs(p['fraction'] - IGN_FRAC) < 1e-6][0]
    # torch / start sequence (times from IGNITION entry = Combustion t 0)
    s_torch = find_step(seq, r'open torch solenoids')
    s_spark = find_step(seq, r'spark train')
    s_conf = find_step(seq, r'torch-flame confirmation')
    s_chk = find_step(seq, r'ignition check')
    pc_ign_abs = num(r'Pc > ([\d.]+) bar abs', s_chk['action'], 'ignition check Pc') * 1e5
    s_ramp = find_step(seq, r'ramp to the commanded thrust')
    ramp_Nps = num(r'<= ?([\d.]+) N/s', s_ramp['action'], 'start ramp')
    s_prop = find_step(seq, r'propane solenoid closed')
    pc_prop_abs = num(r'before Pc exceeds ([\d.]+) bar', s_prop['action'], 'propane close Pc') * 1e5
    s_n2o = find_step(seq, r'N2O torch solenoid closed')
    s_bleed = find_step(seq, r'bleed lift')
    bleed_lift = num(r'([\d.]+) mm bleed lift', s_bleed['action'], 'bleed lift') * 1e-3
    mv_ramp_min = num(r'opening ramp >= ?([\d.]+) s', s_bleed['action'], 'MV opening ramp')
    prime_frac = num(r'P_feed < ([\d.]+) P_tank', s_bleed['action'], 'priming threshold')
    spark_rate = V(el)['rate_Hz'] if 'rate_Hz' in V(el) else V(ign['spark']['spark_rate_Hz'])
    spark_train = V(el)['train_s']
    sol_on = V(el)['solenoid_on_s']
    if abs(V(s_n2o)['t_s'] - sol_on) > 1e-6:
        raise SystemExit('torch N2O off time %.3f != electrical solenoid_on_s %.3f' % (s_n2o['t_s'], sol_on))
    iv = va['isolation_valve']
    iv_close_max = V(iv['close_time_max_s'])
    # ---------------------------------------------------------------- v3.1 relight vapour purge (lead C7, Combustion)
    f_li = os.path.join(ER, '02-combustion', 'data', 'v2', 'low_inlet_check_v2p3.json')
    LI = json.load(open(f_li)); prov['low_inlet_check_v2p3.json'] = [LI.get('version', '?'), sha(f_li)]
    rp = LI['5_relight_purge']
    li_states = rp['states']
    purge12 = max(st_['ign_lift_12p5pct']['purge_s']['O3b_valve_at_coil'] for st_ in li_states.values())
    purge20 = max(st_['ign_lift_20pct']['purge_s']['O3b_valve_at_coil'] for st_ in li_states.values())
    purge_window = V(rp['window_s'])
    if abs(purge_window - (s_chk['t_s'] - s_ign['t_s'])) > 1e-6:
        raise SystemExit('low_inlet_check window %.3f != igniter sequence check - lift %.3f' % (purge_window, s_chk['t_s'] - s_ign['t_s']))
    V_vs = LI['3_volumes']['valve_to_seat_cm3']['valve_at_coil_fixed_end'] * 1e-6
    sv20 = li_states['sat_vapour_20C']
    vap_rho, vap_G = sv20['rho1'], sv20['G_choked_kg_m2s']
    # ---------------------------------------------------------------- pintle drive (Electronics pintle_mini_servo_v1)
    hv = [c for c in PM['candidates'] if c['id'] == 'MKS HV69'][0]
    sel = hv['selected_crank']
    mm = re.match(r"TOG r=([\d.]+)mm phi_c=([\d.]+)deg", sel)
    r_c = float(mm.group(1)) * 1e-3; phi_c = math.radians(float(mm.group(2)))
    mech = PM['inputs']['MECH']
    L_link = V(mech['link_m']); x_stop = V(mech['x_stop_m']); F0 = V(mech['F0_N']); k_spr = V(mech['k_N_per_m'])
    lost = math.radians(5.0)   # [DESIGN] pintle_mini_servo_v1 LOST_DEG (tension link in a slot)
    cs = CrankSlider(r_c, phi_c, L_link)
    phi_max = cs.phi(stroke); phi_stop = cs.phi(x_stop)
    phi_closed = phi_c - lost
    phi_n = 0.5 * (phi_closed + phi_max)
    travel_deg = math.degrees(phi_max - phi_closed)
    crank_rows = [{'lift_mm': x * 1e3, 'crank_deg': math.degrees(cs.phi(x)),
                   'link_angle_deg': math.degrees(math.asin(r_c * math.sin(cs.phi(x)) / L_link)),
                   'dxdphi_mm_per_deg': cs.dxdphi(max(cs.phi(x), phi_c + 1e-6)) * 1e3 * math.pi / 180}
                  for x in (0.0, 0.1e-3, 0.301e-3, 1e-3, 2e-3, 3e-3, 4e-3, x_stop)]
    # ---------------------------------------------------------------- GNC v2
    gb = GN['requirements']['gimbal']
    shp = V(gb['command_shaping_in_ecu'])
    llp = V(GN['requirements']['navigation_and_loop_rates']['link_loss_policy_in_RUN'])
    mh = re.search(r"HOLD[^0-9]*([\d.]+) s", llp)
    if not mh:
        raise SystemExit('gnc.json link_loss_policy_in_RUN: HOLD time not found: ' + llp)
    # v3.3: gnc.json v3 rate- and acceleration-limited tracker (ECU TvcShaper); v2 files have none (0 = plain slew limiter)
    trk = GN.get('flight_software', {}).get('gimbal_command_tracker')
    if trk is not None:
        tv = V(trk)
        acc_dps2 = float(tv['accel_limit_dps2'])
        bad = abs(math.radians(acc_dps2) - float(tv['accel_limit_rad_s2'])) > 0.01 or abs(float(tv['rate_limit_dps']) - float(shp['slew_limit_dps'])) > 1e-9
        if 'accel_limit_dps2' in shp:
            bad = bad or abs(float(shp['accel_limit_dps2']) - acc_dps2) > 1e-9
        if bad:
            raise SystemExit('gnc.json: gimbal_command_tracker and command_shaping_in_ecu disagree (rate / accel limits)')
        if 'TvcShaper' not in tv.get('where', ''):
            raise SystemExit('gnc.json: gimbal_command_tracker is not placed in the ECU TvcShaper: ' + tv.get('where', ''))
        trk_law = tv.get('law', '')
    else:
        acc_dps2, trk_law = 0.0, ''
    hng = V(gb['hinge_moment'])
    if 'flight_p99_Nm' in hng:                                          # gnc.json v2 layout
        hinge_rows = [('hinge_flight_p99_Nm', hng['flight_p99_Nm'], 'hinge_moment flight p99'),
                      ('hinge_flight_max_Nm', hng['flight_max_Nm'], 'hinge_moment flight max')]
    else:                                                               # gnc.json v3 layout
        dl = hng['delivered_mech_v2_MC_p99_max_Nm']
        hinge_rows = [('hinge_design_load_Nm', hng['design_load_engine_moment_Nm'], 'hinge_moment design_load_engine_moment_Nm'),
                      ('hinge_delivered_p99_max_over_cases_Nm', max(v[0] for v in dl.values()), 'hinge_moment delivered MC p99, max over cases'),
                      ('hinge_delivered_max_over_cases_Nm', max(v[1] for v in dl.values()), 'hinge_moment delivered MC max, max over cases')]
    rk = V(GN['requirements']['structure']['gimballed_engine_first_mode_min_Hz'])
    rocking_fixed = None
    if isinstance(rk, dict):                                            # gnc.json v3: per notch tuning
        rocking = rk['with_notch_tuned_5pct_Hz']; rocking_fixed = rk.get('with_notch_fixed_15pct_Hz')
    else:
        rocking = rk
    gnc = dict(range_deg=V(gb['range_deg']), stop_deg=V(gb['mechanical_stop_deg']), rate_min_dps=V(gb['rate_min_dps']),
               bw_min_Hz=V(gb['bandwidth_min_Hz']), res_max_deg=V(gb['resolution_max_deg']),
               backlash_max_deg=V(gb['backlash_max_deg']), latency_max_s=V(gb['latency_cmd_to_motion_max_s']),
               accel_min=V(gb['angular_accel_min_rad_s2']), hinge_rows=hinge_rows,
               shaping_slew_dps=shp['slew_limit_dps'], shaping_w=shp['lowpass_2nd_order_w_rad_s'], shaping_zeta=shp['lowpass_zeta'],
               shaping_accel_dps2=acc_dps2, tracker_law=trk_law,
               link_hold_landing_s=float(mh.group(1)),
               rocking_min_Hz=rocking, rocking_fixed_notch_Hz=rocking_fixed,
               t10_90_s=V(GN['requirements']['throttle']['t10_90_s']),
               slew_min_N_s=V(GN['requirements']['throttle']['slew_min_Fmax_per_s']) * F_max)
    g1 = G1['gnc_inputs']   # gnc.json v1 mid-pivot terms (not republished in v2)
    # ---------------------------------------------------------------- headers: engine_params.h
    hdr = f"""// GENERATED by firmware/tools/gen_tables.py {GEN_VERSION} - DO NOT EDIT. Regenerate when an interface changes.
// Sources: combustion.json {C['version']} (sha {prov['combustion.json'][1]}), gnc.json {GN['version']} (sha {prov['gnc.json'][1]}),
//          pintle_mini_servo_v1.json (Electronics, sha {prov['pintle_mini_servo_v1.json'][1]}), date {prov['date']}.
// Units SI. Tags: [COMB] combustion.json, [GNC] gnc.json, [LEAD] lead decision recorded in combustion.json,
//          [ELEC] Electronics design (pintle_mini_servo_v1), [MECH] Mechanical value carried by pintle_mini_servo_v1, [DERIVED].
#pragma once
namespace ecu {{
namespace eng {{
constexpr float kAt_m2 = {At:.6e}f;             // [COMB] nozzle throat area
constexpr float kEps = {eps:.4f}f;                 // [COMB] expansion ratio
constexpr float kAe_m2 = {Ae:.6e}f;             // [DERIVED] At * eps
constexpr float kCfVacEff = {CfE:.5f}f;           // [DERIVED] LSQ F = Cf*At*Pc - pa*Ae over the 20 C points (max err {np.max(np.abs(fit_err)):.2f} N); info only
constexpr float kPamb_Pa = 101325.0f;          // [ELEC] ambient used for thrust<->Pc (FC may update)
// thrust <-> Pc table [DERIVED from combustion throttle_points_20C_initial_port, {len(pts)} points]: Fvac = F + pa*Ae, Pc absolute.
// Linear extrapolation beyond the ends. Replace by the load-cell calibration after static fire (TS-cal).
constexpr int kNThr = {len(thr_pc)};
constexpr float kThrPcAbs_Pa[kNThr] = {{{', '.join(f'{v:.1f}f' for v in thr_pc)}}};
constexpr float kThrFvac_N[kNThr] = {{{', '.join(f'{v:.3f}f' for v in thr_fv)}}};
constexpr float kFmax_N = {F_max:.1f}f;               // [COMB/REQ]
constexpr float kPcMaxAbs_Pa = {pc_max:.1f}f;    // [COMB] Pc at 500 N (absolute)
constexpr float kPcFloorAbs_Pa = {pc_floor:.1f}f;  // [COMB] 12.5 % stretch floor at 20 C
constexpr float kPcMeopAbs_Pa = {pc_meop:.1f}f;  // [LEAD via COMB pressure_limits] chamber MEOP
constexpr float kPcProofAbs_Pa = {pc_proof:.1f}f;  // [LEAD via COMB] proof 1.5 x MEOP
constexpr float kPcNormalCapAbs_Pa = {pc_cap:.1f}f;  // [LEAD via COMB] normal software cap on the Pc command
constexpr float kPcAbortAbs_Pa = {pc_abort:.1f}f;  // [LEAD via COMB] ECU over-pressure abort (~30 bar)
constexpr float kTankMeop_Pa = {tank_meop:.1f}f;   // [COMB/LEAD v0] tank MEOP
constexpr float kDpOverPcMin = {dp_over_pc_min:.3f}f;        // [COMB] thrust ceiling rule: injector dP/Pc >= {dp_over_pc_min}
constexpr float kPintleStroke_m = {stroke:.6e}f;  // [COMB] mechanical stroke
constexpr float kPintleIgnitionFrac = {IGN_FRAC:.3f}f;     // [ELEC choice inside COMB {lo_pct:g}-{hi_pct:g} %] start level ({F_ign:.0f} N)
constexpr float kPintleIgnitionLift_m = {lift_ign:.6e}f; // [COMB] lift for {IGN_FRAC * 100:.0f} % thrust at 20 C
constexpr float kPintleIgnitionLiftLow_m = {lift_ign_lo:.6e}f; // [COMB] lift for {lo_pct:g} % thrust ({F_ign_lo:.1f} N) at 20 C: low end of the ignition range (v3.2)
// pintle linkage: MKS HV69 on an in-line crank-slider (pintle_mini_servo_v1 {sel}, L {L_link * 1e3:.1f} mm):
//   s(phi) = r cos phi + sqrt(L^2 - r^2 sin^2 phi), lift x = s(phi_c) - s(phi), phi from top dead centre; lost motion below phi_c
constexpr float kCrankR_m = {r_c:.6e}f;          // [ELEC] crank radius
constexpr float kLinkL_m = {L_link:.6e}f;          // [MECH] link length (centre to centre)
constexpr float kCrankPhiContact_rad = {phi_c:.6f}f; // [ELEC] crank angle at needle contact/seat
constexpr float kCrankLostMotion_rad = {lost:.6f}f;  // [ELEC] commanded overtravel below contact when closed (slot)
constexpr float kCrankPhiMax_rad = {phi_max:.6f}f;   // [DERIVED] crank angle at full stroke ({math.degrees(phi_max):.2f} deg)
constexpr float kCrankPhiStop_rad = {phi_stop:.6f}f;  // [DERIVED] crank angle at the {x_stop * 1e3:.1f} mm open stop ({math.degrees(phi_stop):.2f} deg)
constexpr float kCrankPhiNeutral_rad = {phi_n:.6f}f; // [DERIVED] crank angle at servo neutral: centre of the {travel_deg:.1f} deg command travel
constexpr float kPintleStopLift_m = {x_stop:.6e}f;  // [ELEC/MECH] open stop beyond the stroke
constexpr float kSpringPreload_N = {F0:.2f}f;   // [MECH] closing spring preload at seat
constexpr float kSpringRate_Npm = {k_spr:.1f}f;     // [MECH ASSUMED]
// crank-slider check vectors from this generator's (Python) implementation, compared with the firmware's in test_core
constexpr int kNCrankChk = {len(crank_rows)};
constexpr float kCrankChkLift_m[kNCrankChk] = {{{', '.join(f"{r_['lift_mm'] * 1e-3:.6e}f" for r_ in crank_rows)}}};
constexpr float kCrankChkPhi_rad[kNCrankChk] = {{{', '.join(f"{math.radians(r_['crank_deg']):.7f}f" for r_ in crank_rows)}}};
// start / torch sequence [COMB igniter.sequence.start], times from IGNITION entry (Combustion t = 0)
constexpr float kTorchSolOpen_s = {s_torch['t_s']:.3f}f;      // [COMB] open N2O + propane torch solenoids
constexpr float kSparkStart_s = {s_spark['t_s']:.3f}f;        // [COMB] spark train start
constexpr float kSparkRate_Hz = {spark_rate:.1f}f;        // [COMB]
constexpr float kSparkTrain_s = {spark_train:.3f}f;        // [COMB] up to 0.5 s
constexpr float kTorchConfirmBy_s = {s_conf['t_s']:.3f}f;    // [COMB] torch flame confirmed by (ELEC v2.7 sensor: torch chamber pressure P_torch; hard gate in flight)
constexpr float kPintleToIgnitionLift_s = {s_ign['t_s']:.3f}f; // [COMB] pintle to the ignition lift
constexpr float kIgnitionCheck_s = {s_chk['t_s']:.3f}f;     // [COMB] ignition check time: Pc above kIgnitionPcAbs_Pa or ABORT
constexpr float kIgnitionPcAbs_Pa = {pc_ign_abs:.1f}f;  // [COMB] combustion 4.4-6.2 bar vs cold N2O flow ~1.5 bar
constexpr float kStartRamp_Nps = {ramp_Nps:.1f}f;     // [COMB/GNC] ramp to the commanded thrust at <= this after ignition
constexpr float kPropaneOff_s = {s_prop['t_s']:.3f}f;        // [COMB] propane solenoid closed ...
constexpr float kPropaneOffPcAbs_Pa = {pc_prop_abs:.1f}f; // [COMB] ... or before Pc exceeds this (propane vapour pressure)
constexpr float kTorchOff_s = {s_n2o['t_s']:.3f}f;          // [COMB] N2O torch solenoid closed, spark off
// line priming [COMB igniter.sequence.start t -0.8 s, valves_and_actuators.priming_rule]
constexpr float kPrimeSlowFrac = {prime_frac:.3f}f;       // [COMB] P_feed / P_tank below this -> unprimed line
constexpr float kBleedLift_m = {bleed_lift:.6e}f;    // [COMB] pintle bleed lift before the isolation valve moves
constexpr float kMvOpenRampMin_s = {mv_ramp_min:.3f}f;     // [COMB] isolation-valve opening ramp (minimum)
constexpr float kMvCloseMax_s = {iv_close_max:.3f}f;        // [COMB] isolation valve close time (maximum)
// relight vapour purge [COMB low_inlet_check_v2p3 5_relight_purge (sha {prov['low_inlet_check_v2p3.json'][1]}), lead C7 2026-10-12]:
// time to push a vapour/supercritical valve->seat volume ({V_vs * 1e6:.2f} cm3, NC valve at the hose-coil end) through the
// ignition lift; worst of the states Combustion lists (sat. vapour 20 C, supercritical 7.5 MPa 330/360 K)
constexpr float kRelightPurge12p5_s = {purge12:.4f}f;   // [COMB] at the 12.5 % ignition lift
constexpr float kRelightPurge20_s = {purge20:.4f}f;     // [COMB] at the 20 % ignition lift (this ECU's start level)
constexpr float kRelightPurgeWindow_s = {purge_window:.3f}f; // [COMB] ignition lift -> ignition check in the start sequence
// GNC requirements to the engine [gnc.json {GN['version']}]
constexpr float kGimbalRange_rad = {math.radians(gnc['range_deg']):.6f}f;   // [GNC] commanded limit on the vector norm
constexpr float kGimbalRateMin_radps = {math.radians(gnc['rate_min_dps']):.6f}f;  // [GNC/REQ ENG-07] {gnc['rate_min_dps']:g} deg/s
constexpr float kGncShapeSlew_radps = {math.radians(gnc['shaping_slew_dps']):.6f}f;  // [GNC] command_shaping_in_ecu slew {gnc['shaping_slew_dps']:g} deg/s
constexpr float kGncShapeW_radps = {gnc['shaping_w']:.3f}f;      // [GNC] command_shaping_in_ecu 2nd-order low-pass
constexpr float kGncShapeZeta = {gnc['shaping_zeta']:.3f}f;
constexpr float kGncShapeAccel_radps2 = {math.radians(gnc['shaping_accel_dps2']):.4f}f;  // [GNC] flight_software.gimbal_command_tracker {gnc['shaping_accel_dps2']:g} deg/s2 (0 = plain slew limiter)
// tracker law [GNC]: {gnc['tracker_law'][:220]}
constexpr float kLinkHoldLanding_s = {gnc['link_hold_landing_s']:.3f}f;   // [GNC] landing-burn link-loss HOLD time
}}  // namespace eng
}}  // namespace ecu
"""
    open(os.path.join(FW, 'src', 'core', 'engine_params.h'), 'w').write(hdr)

    # ---------------------------------------------------------------- ECU feed-forward valve map (Combustion map v2)
    rows = list(csv.DictReader(l for l in open(map_fn) if not l.startswith('#')))
    hdr_line = [l for l in open(map_fn) if l.startswith('#')][0]
    D0 = V(gr['port']['initial_diameter_m'])
    mrows = [r for r in rows if abs(float(r['D_port_m']) - D0) < 1e-6]
    ptanks = sorted(set(float(r['P_tank_Pa']) for r in mrows))
    pc_grid = np.array([4.0, 4.5, 5.0, 5.5, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 25.0, 26.0]) * 1e5
    LIFT = np.zeros((len(ptanks), len(pc_grid))); GAIN = np.zeros_like(LIFT)
    map_rows_used = {}
    for j, ptk in enumerate(ptanks):
        rr = sorted([r for r in mrows if float(r['P_tank_Pa']) == ptk], key=lambda r: float(r['Pc_Pa']))
        pc = np.array([float(r['Pc_Pa']) for r in rr]); h = np.array([float(r['lift_m']) for r in rr])
        if np.any(np.diff(pc) <= 0) or np.any(np.diff(h) <= 0):
            raise SystemExit(f'throttle map row P_tank {ptk} not monotonic')
        f = PchipInterpolator(pc, h, extrapolate=False); df = f.derivative()
        for i, p in enumerate(pc_grid):
            if p < pc[0]:
                d = float(df(pc[0])); LIFT[j, i] = h[0] + d * (p - pc[0]); GAIN[j, i] = 1.0 / d
            elif p > pc[-1]:
                d = float(df(pc[-1])); LIFT[j, i] = h[-1] + d * (p - pc[-1]); GAIN[j, i] = 1.0 / d
            else:
                LIFT[j, i] = float(f(p)); GAIN[j, i] = 1.0 / float(df(p))
        map_rows_used[f'{ptk:.0f}'] = {'Pc_Pa': pc.tolist(), 'lift_m': h.tolist(), 'T_tank_K': float(rr[0]['T_tank_K'])}
    LIFT = np.clip(LIFT, 1.0e-6, x_stop)
    vm = [f"// GENERATED by firmware/tools/gen_tables.py {GEN_VERSION} - DO NOT EDIT.\n"
          f"// ECU feed-forward map: steady pintle lift [m] and plant gain dPc/dx [Pa/m] vs absolute Pc setpoint and absolute tank\n"
          f"// pressure, from Combustion's published throttle map (combustion.json {C['version']} throttle_map_csv, sha {prov['throttle_map_v2.csv']},\n"
          f"// D_port {D0 * 1e3:.0f} mm initial port, {len(ptanks)} tank pressures x {len(mrows) // len(ptanks)} thrust points): monotone cubic (PCHIP) in Pc,\n"
          f"// linear extrapolation outside {min(thr_pc) / 1e5:.2f}-{max(thr_pc) / 1e5:.2f} bar; the ECU clamps outside the tank-pressure grid.\n"
          f"// Map basis: {hdr_line.strip()[2:120]}...\n"
          "// v2.1 used a table generated from the SIL plant; v3 uses Combustion's model, so the SIL plant (Electronics) tests\n"
          "// the controller against a model it was not tuned on. To be replaced by cold-flow + static-fire data (same layout).\n"
          "#pragma once\nnamespace ecu {\nnamespace vmap {\n",
          f"constexpr int kNPc = {len(pc_grid)}, kNPt = {len(ptanks)};\n",
          "constexpr float kPcGrid_Pa[kNPc] = {" + ', '.join(f'{v:.1f}f' for v in pc_grid) + "};\n",
          "constexpr float kPtGrid_Pa[kNPt] = {" + ', '.join(f'{v:.1f}f' for v in ptanks) + "};\n",
          f"constexpr float kMapPortD_m = {D0:.4f}f;   // [COMB] port diameter of the map rows\n",
          farr2('kLift_m', LIFT, ('kNPt', 'kNPc')), farr2('kGain_Pa_per_m', GAIN, ('kNPt', 'kNPc')),
          "}  // namespace vmap\n}  // namespace ecu\n"]
    open(os.path.join(FW, 'src', 'core', 'valve_map_table.h'), 'w').write(''.join(vm))

    # ---------------------------------------------------------------- SIL plant tables
    inj1 = C1['gas_path']['injector']
    Ds = V(gp['injector']['seat_diameter_m']); cone = math.radians(V(inj1['needle_metering_cone_half_angle_deg']))
    Cd = V(gp['injector']['Cd'])
    eta_cs = num(r'eta_c\* ([\d.]+)', op['max_thrust']['F_N']['tag'], 'eta_c*')
    eta_cf = num(r'eta_cf ([\d.]+)', op['max_thrust']['F_N']['tag'], 'eta_cf')
    f_feed = os.path.join(ER, '02-combustion', 'data', 'v2', 'feed_line_checks_v2.json')   # named by combustion.json (OI-7)
    FC = json.load(open(f_feed)); prov['feed_line_checks_v2.json'] = [FC['version'], sha(f_feed)]
    dp_line_ref, dp_line_tag = FC['inputs']['line_loss_budget_Pa']
    pm = va['plant_model_valve_to_Pc']
    fit = V(pm['fit'])
    tau_f = [f_['tau_f_s'] for f_ in fit]
    reg = gr['regression_law']
    helix = V(reg['helix_factor']) if 'helix_factor' in reg else 1.0
    nl = V(C['decisions']['N2O_load_and_tank'])
    Ts = np.arange(240.0, 308.01, 1.0)
    S = np.array([sat(T)[:7] for T in Ts])
    if a.fast:
        Tg = np.arange(255.0, 305.01, 5.0); Pg = np.arange(1.0e5, 40.01e5, 1.0e5)
    else:
        Tg = np.arange(255.0, 305.01, 2.5); Pg = np.arange(1.0e5, 40.01e5, 0.5e5)
    GH = np.zeros((len(Tg), len(Pg)))
    for i, T in enumerate(Tg):
        for j, P2 in enumerate(Pg):
            GH[i, j] = g_hem_sat(T, P2)
    PcB = np.array(PT['Pc_bar']) * 1e5; OF = np.array(PT['OF'])
    if eps not in PT['eps']:
        raise SystemExit(f'eps {eps} not on perf grid')
    ie = PT['eps'].index(eps)
    cstar = np.array(PT['cstar']); gam = np.array(PT['gamma']); cfv = np.array(PT['Cf_vac'])[:, :, ie]
    P = {
        'At': (At, 'COMB'), 'eps': (eps, 'COMB'),
        'eta_cstar': (eta_cs, 'COMB v2 max_thrust tag (ASSUMED 0.92, band 0.85-0.96)'),
        'eta_cfv': (eta_cf, 'COMB v2 max_thrust tag (15 deg cone 0.983 x 0.992)'),
        'Ds_seat': (Ds, 'COMB'), 'cone_half': (cone, 'COMB v1 (v2: injector unchanged from v1)'),
        'Cd': (Cd, 'COMB ASSUMED 0.6-0.8'), 'd_stem': (V(inj1['stem_diameter_through_seal_m']), 'COMB v1 (unchanged)'),
        'V_manifold': (V(inj1['manifold_volume_m3']), 'COMB v1 (unchanged)'),
        'a_reg': (V(reg['a']), 'COMB ASSUMED'), 'n_reg': (V(reg['n']), 'COMB ASSUMED'),
        'helix': (helix, 'COMB v2 straight port (no helix factor)' if 'helix_factor' not in reg else 'COMB'),
        'rho_f': (V(gr['density_kg_m3']), 'COMB'), 'L_grain': (V(gr['length_m']), 'COMB v2 S230'),
        'D_port0': (D0, 'COMB'), 'V_free0': (V(gp['overall']['free_chamber_volume_initial_m3']), 'COMB v2'),
        'tau_d_lo': (V(pm['tau_d_s'])[0], 'COMB ASSUMED'), 'tau_d_hi': (V(pm['tau_d_s'])[1], 'COMB ASSUMED'),
        'tau_f_lo': (min(tau_f), 'COMB v2 plant fit'), 'tau_f_hi': (max(tau_f), 'COMB v2 plant fit'),
        'tank_V': (nl['V_tank_m3'], 'LEAD via COMB decisions.N2O_load_and_tank'),
        'tank_m': (nl['m_N2O_kg'], 'LEAD via COMB decisions.N2O_load_and_tank'),
        'pc_meop': (pc_meop, 'LEAD via COMB'),
        'dp_line_ref': (dp_line_ref, 'COMB feed_line_checks_v2.json: ' + dp_line_tag + ' (~mdot^2)'),
        'V_valve_to_seat': (V_vs, 'COMB low_inlet_check_v2p3 3_volumes valve_at_coil_fixed_end (v3.1, C7)'),
        'vap_rho': (vap_rho, 'COMB low_inlet_check_v2p3 relight purge state sat_vapour_20C rho1 (v3.1, C7)'),
        'vap_G': (vap_G, 'COMB low_inlet_check_v2p3 relight purge state sat_vapour_20C choked flux (v3.1, C7)'),
    }
    out = [f"// GENERATED by firmware/tools/gen_tables.py {GEN_VERSION} - DO NOT EDIT. SIL plant tables (not flight code).\n"
           f"// combustion.json {C['version']} sha {prov['combustion.json'][1]} (+ combustion_v1.json injector geometry sha {prov['combustion_v1.json (02-combustion/inputs)'][1]});\n"
           f"// perf table {PT['version']} sha {prov['perf_table'][1]} ({PT['source']});\n"
           f"// N2O: CoolProp {prov['CoolProp']} NitrousOxide (Lemmon & Span 2006). HEM flux from saturated liquid at T; the Dyer blend\n"
           f"// G = k/(1+k) G_SPI(P1) + 1/(1+k) G_HEM, k = sqrt((P1-P2)/(Pv-P2)) is formed at run time (combustion v2 inlet convention).\n",
           "#pragma once\nnamespace sil {\nnamespace tab {\n"]
    for k, (v, tag) in P.items():
        out.append(f"constexpr double k_{k} = {v:.8e};   // [{tag}]\n")
    out.append(f"// saturation table, T = {Ts[0]:.1f}..{Ts[-1]:.1f} K step 1 K: P, rho_l, rho_v, u_l, u_v, h_l, h_v\n")
    out.append(f"constexpr int kNsat = {len(Ts)};\nconstexpr double kSatT0 = {Ts[0]:.2f}, kSatDT = 1.0;\n")
    out.append(carr('kSat', S))
    out.append(f"// HEM mass flux [kg/m2/s] from saturated liquid at T to P2; T = {Tg[0]:.1f}..{Tg[-1]:.1f} step {Tg[1]-Tg[0]:.2f} K, P2 = {Pg[0]:.0f}..{Pg[-1]:.0f} step {Pg[1]-Pg[0]:.0f} Pa (abs)\n")
    out.append(f"constexpr int kNGT = {len(Tg)}, kNGP = {len(Pg)};\nconstexpr double kGT0 = {Tg[0]:.2f}, kGDT = {Tg[1]-Tg[0]:.3f}, kGP0 = {Pg[0]:.1f}, kGDP = {Pg[1]-Pg[0]:.1f};\n")
    out.append(carr('kGhem', GH, '{:.5e}'))
    out.append(f"// CEA (shifting) on log(Pc) x O/F grid; eps = {eps} for Cf_vac\n")
    out.append(f"constexpr int kNCP = {len(PcB)}, kNOF = {len(OF)};\n")
    out.append(carr('kCeaPc', PcB, '{:.1f}')); out.append(carr('kCeaOF', OF, '{:.3f}'))
    out.append(carr('kCstar', cstar, '{:.3f}')); out.append(carr('kGamma', gam, '{:.5f}')); out.append(carr('kCfVac', cfv, '{:.5f}'))
    out.append("}  // namespace tab\n}  // namespace sil\n")
    open(os.path.join(FW, 'sil', 'plant_tables.h'), 'w').write(''.join(out))

    # ---------------------------------------------------------------- SIL gimbal-axis tables
    gsrc = f"gnc.json {GN['version']} sha {prov['gnc.json'][1]} (requirements); gnc.json {g1 and G1['provenance']['gnc.json'][0]} sha {G1['provenance']['gnc.json'][1]} (mid-pivot terms, not in v2/v3)"
    gh = [f"// GENERATED by firmware/tools/gen_tables.py {GEN_VERSION} - DO NOT EDIT. SIL single-axis gimbal load model from {gsrc}.\n",
          "#pragma once\nnamespace sil {\nnamespace gnc {\n"]
    grow = [('I_pivot_kgm2', g1['I_pivot'], 'GNC v1 terms_mid.I_pivot_kgm2 (2-axis model uses mechanical.json)'),
            ('K_hose_Nm_per_rad', g1['K_hose'], 'GNC v1 flex_hose_K_delta / range'),
            ('M_fric_Nm', g1['M_fric'], 'GNC v1 pivot_friction'),
            ('M_mis_full_Nm', g1['M_mis'], 'GNC v1 thrust_misalignment_T_e'),
            ('M_side_floor_Nm', g1['M_side_floor'], 'GNC v1 nozzle_side_load_at_floor'),
            ('K_axacc_Nm_per_rad', g1['K_axacc'], 'GNC v1 axial_accel term / sin(range)'),
            ('hinge_design_mid_Nm', g1['hinge_mid_Nm'], 'GNC v1 hinge_moment_design mid pivot (superseded: LEAD 35.3 N m design load)'),
            ] + [(k_, v_, f"GNC {GN['version']} {t_}") for k_, v_, t_ in gnc['hinge_rows']] + [
            ('range_deg', gnc['range_deg'], f"GNC {GN['version']} range (vector norm)"), ('rate_min_dps', gnc['rate_min_dps'], f"GNC {GN['version']} / ENG-07"),
            ('bw_min_Hz', gnc['bw_min_Hz'], f"GNC {GN['version']} / ENG-07"), ('res_max_deg', gnc['res_max_deg'], f"GNC {GN['version']} / ENG-07"),
            ('backlash_max_deg', gnc['backlash_max_deg'], f"GNC {GN['version']}"), ('latency_max_s', gnc['latency_max_s'], f"GNC {GN['version']}"),
            ('accel_min_radps2', gnc['accel_min'], f"GNC {GN['version']}"),
            ('rocking_min_Hz', gnc['rocking_min_Hz'], f"GNC {GN['version']} / ENG-11" + (' (notch tuned within 5 %)' if gnc['rocking_fixed_notch_Hz'] else '')),
            ] + ([('rocking_min_fixed_notch_Hz', gnc['rocking_fixed_notch_Hz'], f"GNC {GN['version']} / ENG-11 (fixed notch, 15 %)")]
                 if gnc['rocking_fixed_notch_Hz'] else []) + [
            ('cmd_accel_limit_dps2', gnc['shaping_accel_dps2'], f"GNC {GN['version']} gimbal_command_tracker (0 = none)"),
            ('thrust_t10_90_s', gnc['t10_90_s'], f"GNC {GN['version']} / ENG-03"), ('thrust_slew_min_Nps', gnc['slew_min_N_s'], f"GNC {GN['version']}")]
    for k, v_, tag in grow:
        gh.append(f"constexpr double k_{k} = {v_:.6e};   // [{tag}]\n")
    gh.append("}  // namespace gnc\n}  // namespace sil\n")
    open(os.path.join(FW, 'sil', 'gnc_tables.h'), 'w').write(''.join(gh))

    # ---------------------------------------------------------------- cross-check: my Dyer (v2 convention) vs Combustion's map
    hem_cache = {}
    chk = []
    for r in rows:
        T = float(r['T_tank_K']); Pc = float(r['Pc_Pa']); h = float(r['lift_m']); mox = float(r['mdot_ox']); Ptk = float(r['P_tank_Pa'])
        key = (round(T, 3), round(Pc, 0))
        if key not in hem_cache:
            hem_cache[key] = g_hem_sat(T, Pc)
        A = Cd * pintle_area(h, Ds, cone)
        m_ = mox
        for _ in range(30):   # P1 = P_tank - dp_line(mdot), fixed point on mdot
            P1 = Ptk - P['dp_line_ref'][0] * (m_ / 0.25) ** 2
            m_new = A * g_dyer_v2(T, P1, Pc, hem_cache[key])
            if abs(m_new - m_) < 1e-9:
                break
            m_ = m_new
        m_sat = A * g_dyer_v2(T, sat(T)[0], Pc, hem_cache[key])   # v1 convention (line loss ignored), for reference
        chk.append(dict(P_tank=Ptk, T=T, D_port=float(r['D_port_m']), frac=float(r['frac']), mox_comb=mox, mox_elec=m_,
                        err_pct=100 * (m_ / mox - 1), err_v1conv_pct=100 * (m_sat / mox - 1)))
    res = dict(id='gen_tables', version=GEN_VERSION, provenance=prov, key_paths_read=used, CfVacEff=CfE,
               CfVacEff_fit_err_N=fit_err.tolist(),
               thrust_table=dict(Pc_abs_Pa=thr_pc, Fvac_N=thr_fv, note='ECU thrust<->Pc table (exact at the Combustion points)'),
               pressure_limits=dict(meop=pc_meop, proof=pc_proof, cap=pc_cap, abort=pc_abort, tank_meop=tank_meop),
               start_sequence=dict(torch_open=s_torch['t_s'], spark=s_spark['t_s'], confirm=s_conf['t_s'], pintle=s_ign['t_s'],
                                   check=s_chk['t_s'], check_pc_abs=pc_ign_abs, ramp_Nps=ramp_Nps, propane_off=s_prop['t_s'],
                                   propane_off_pc_abs=pc_prop_abs, torch_off=s_n2o['t_s'], spark_rate=spark_rate,
                                   spark_train=spark_train, ignition_frac=IGN_FRAC, ignition_lift_m=lift_ign, ignition_lift_low_m=lift_ign_lo, ignition_low_pct=lo_pct,
                                   bleed_lift_m=bleed_lift, mv_ramp_min_s=mv_ramp_min, prime_frac=prime_frac),
               gnc_inputs=gnc, gnc_v1_terms=g1,
               pintle=dict(servo='MKS HV69', crank=sel, r_c=r_c, L=L_link, phi_c_deg=math.degrees(phi_c), lost_deg=5.0,
                           phi_closed_deg=math.degrees(phi_closed), phi_max_deg=math.degrees(phi_max),
                           phi_stop_deg=math.degrees(phi_stop), phi_neutral_deg=math.degrees(phi_n), travel_deg=travel_deg,
                           crank_rows=crank_rows, spring_F0_N=F0, spring_k_Npm=k_spr),
               valve_map=dict(source='throttle_map_v2.csv D_port %.3f' % D0, P_tank_Pa=ptanks, Pc_grid_Pa=pc_grid.tolist(),
                              lift_m=LIFT.tolist(), gain_Pa_per_m=GAIN.tolist(), rows=map_rows_used),
               dyer_crosscheck=chk, max_abs_err_pct=max(abs(c['err_pct']) for c in chk),
               max_abs_err_v1conv_pct=max(abs(c['err_v1conv_pct']) for c in chk),
               sil_plant_constants={k: [v_, t_] for k, (v_, t_) in P.items()},
               relight_purge=dict(source='02-combustion/data/v2/low_inlet_check_v2p3.json', purge_12p5_s=purge12, purge_20_s=purge20,
                                  window_s=purge_window, V_valve_to_seat_m3=V_vs, vap_rho=vap_rho, vap_G=vap_G))
    json.dump(res, open(os.path.join(RES, 'gen_tables_%s.json' % GEN_VERSION.replace('.', 'p')), 'w'), indent=1)
    print(json.dumps({k: res[k] for k in ('CfVacEff', 'max_abs_err_pct', 'max_abs_err_v1conv_pct')}, indent=1))
    print(json.dumps(res['pintle'], indent=1)[:1600])
    print(json.dumps(res['start_sequence'], indent=1))
    worst = sorted(chk, key=lambda c: -abs(c['err_pct']))[:5]
    for c in worst:
        print('worst: P_tank %.0f T %.2f D %.3f frac %.3f mox comb %.5f elec %.5f err %+.2f %% (v1 conv %+.2f %%)' % (
            c['P_tank'], c['T'], c['D_port'], c['frac'], c['mox_comb'], c['mox_elec'], c['err_pct'], c['err_v1conv_pct']))


if __name__ == '__main__':
    main()
