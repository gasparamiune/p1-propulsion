"""Pintle actuator linkage trade, v2 (Electronics, 2026-10-11).

Reads interfaces/combustion.json (v1+) and its throttle-map CSV; compares crank geometries for the
Savox SB-2292SG pintle servo. Every input is tagged; outputs go to results/pintle_linkage_v2.{json,txt,png}.

Kinematics
  SYM  symmetric crank (v1 proposal):  x = r (sin(th) + sin(h)),   th in [-h, +h]
  TOG  spring-follower crank ("toggle-biased"): crank-pin roller lifts a flat follower plate on the
       needle stem against a closing spring (scotch-yoke law):
           x = r (cos(phi_c) - cos(phi))   for phi >= phi_c ;  x = 0 (needle seated by spring) below phi_c
       phi = crank angle from the dead-centre line; phi_c = contact angle at seat; 'lost motion' below
       phi_c guarantees seating whatever the angle tolerance.
Loads on the actuator (+ = resisting opening): pressure force on the needle (Combustion sign convention:
+ closing), closing spring (TOG only), seal friction (Coulomb, opposes motion).
Servo: linear torque-speed line between DATASHEET stall torque and no-load speed (shape ASSUMED).
Resolution: one servo deadband step (ASSUMED 1 us = 0.1 deg; range 0.5-3 us) mapped through dx/dangle
and the local thrust slope dF/dx of Combustion's 20 C throttle map.
"""
from __future__ import annotations
import csv, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE_ROOT = os.environ.get('ENGINE_ROOT', '/mnt/project-files/engine')
sys.path.insert(0, HERE)
import parts_db as pdb

OUT = os.path.join(HERE, '..', 'results')
COMB = os.path.join(ENGINE_ROOT, 'interfaces', 'combustion.json')

def load_comb():
    c = json.load(open(COMB))
    pa = c['valves_and_actuators']['pintle_actuator_requirements']
    inj = c['gas_path']['injector']
    tp = c['operating_points']['throttle_points_20C_initial_port']
    return c, pa, inj, tp

def map_csv(c):
    fn = c['operating_points']['throttle_map_csv']
    rows = list(csv.DictReader(l for l in open(fn) if not l.startswith('#')))
    out = {}
    for r in rows:
        T = float(r['T_tank']); out.setdefault(T, []).append((float(r['h']), float(r['F']), float(r['Pc']), float(r['frac'])))
    for T in out:
        out[T].sort()
    return out

# ------------------------------------------------------------------------------------------- servo
SV = pdb.SB2292SG
def servo_at(V):
    vs = [6.0, 7.4, 8.4]
    T = [SV['torque_kgcm']['v'][f'{v:.1f}'] * pdb.KGCM_TO_NM for v in vs]
    s60 = [SV['speed_s_per_60deg']['v'][f'{v:.1f}'] for v in vs]
    Ts = float(np.interp(V, vs, T)); w = math.radians(60) / float(np.interp(V, vs, s60))
    return Ts, w
DB_US = pdb.SB2292SG['deadband_us']['v']; DB_RANGE = pdb.SB2292SG['deadband_us']['range']
US_PER_DEG = 10.0         # DATASHEET 1000 us / 100 deg
LAT = 0.003003 + 0.0010   # DATASHEET frame + ASSUMED internal latency [s]
ETA = 0.90                # ASSUMED crank/roller efficiency

# ------------------------------------------------------------------------------------------- kinematics
class Sym:
    def __init__(s, stroke, half_deg):
        s.h = math.radians(half_deg); s.r = stroke / (2 * math.sin(s.h)); s.name = f"SYM r={s.r*1e3:.2f}mm +/-{half_deg:.0f}deg"
        s.spring = None; s.lost = 0.0
    def ang(s, x):  # crank angle [rad] for lift x
        return math.asin(max(-1, min(1, x / s.r - math.sin(s.h))))
    def dxda(s, x):
        return s.r * math.cos(s.ang(x))
    def travel(s, stroke):
        return math.degrees(s.ang(stroke) - s.ang(0.0))

class Tog:
    def __init__(s, r, phic_deg, lost_deg=5.0):
        s.r = r; s.pc = math.radians(phic_deg); s.lost = math.radians(lost_deg)
        s.name = f"TOG r={r*1e3:.1f}mm phi_c={phic_deg:.0f}deg"
    def ang(s, x):
        return math.acos(max(-1, min(1, math.cos(s.pc) - x / s.r)))
    def dxda(s, x):
        return s.r * math.sin(s.ang(x))
    def travel(s, stroke):
        return math.degrees(s.ang(stroke) - s.pc + s.lost)

# ------------------------------------------------------------------------------------------- loads
def loads(c, pa, inj):
    Ds = inj['seat_diameter_m']['v']; ds = inj['stem_diameter_through_seal_m']['v']
    As = math.pi * ds ** 2 / 4; Aseat = math.pi * Ds ** 2 / 4
    P_meop = c['operating_points']['tank_MEOP_Pa']['v']
    P_op = c['operating_points']['tank_pressure_range_Pa']['v'][1]
    F_seal = pa['seal_friction_N']['v']
    return dict(As=As, Aseat=Aseat, P_meop=P_meop, P_op=P_op, F_seal=F_seal,
                F_open_meop=-(P_meop - 101325) * As, F_open_op=-(P_op - 101325) * As,
                F_seat_meop=(P_meop - 101325) * Aseat - (P_meop - 101325) * As)

def spring_design(L, stroke, margin=10.0, k=5000.0):
    """Closing spring so that the net load on the follower never changes sign at tank MEOP
    (pressure opening force + seal friction + margin) over the whole stroke."""
    F0 = -L['F_open_meop'] + L['F_seal'] + margin
    return dict(F0=F0, k=k, F_full=F0 + k * stroke, margin=margin,
                tag="DERIVED: F0 >= |stem pressure force at tank MEOP| + seal friction + 10 N; k ASSUMED 5 N/mm")

def act_force(geo, L, x, P_tank, opening=True):
    """Force the actuator must deliver at lift x (+ = opening direction needed)."""
    # pressure force (+ closing) - seated vs open blend over the first 0.1 mm
    f_open = -(P_tank - 101325) * L['As']
    f_seat = (P_tank - 101325) * (L['Aseat'] - L['As'])
    w = min(1.0, x / 1e-4)
    Fp = (1 - w) * f_seat + w * f_open
    Fs = geo.spring['F0'] + geo.spring['k'] * x if getattr(geo, 'spring', None) else 0.0
    Ff = L['F_seal'] if opening else -L['F_seal']
    return Fp + Fs + Ff

def stroke_time(geo, L, x0, x1, V, P_tank, n=400):
    Ts, w = servo_at(V)
    a0 = geo.ang(x0); a1 = geo.ang(x1)
    if isinstance(geo, Tog) and x0 <= 0: a0 = geo.pc - geo.lost
    t = 0.0; Tpk = 0.0
    for a in np.linspace(a0, a1, n)[:-1]:
        da = (a1 - a0) / (n - 1)
        if isinstance(geo, Tog):
            x = max(0.0, geo.r * (math.cos(geo.pc) - math.cos(a))); dxda = geo.r * math.sin(a) if a > geo.pc else 0.0
        else:
            x = geo.r * (math.sin(a) + math.sin(geo.h)); dxda = geo.r * math.cos(a)
        F = act_force(geo, L, x, P_tank, opening=(x1 > x0))
        T = max(0.0, F * dxda / ETA) if x1 > x0 else max(0.0, -F * dxda / ETA)
        Tpk = max(Tpk, abs(F * dxda / ETA))
        om = w * max(0.05, 1 - T / Ts)
        t += abs(da) / om
    return t + LAT, Tpk

def dFdx_at(mp, x):
    hs = np.array([r[0] for r in mp]); F = np.array([r[1] for r in mp])
    i = int(np.clip(np.searchsorted(hs, x) - 1, 0, len(hs) - 2))
    return (F[i + 1] - F[i]) / (hs[i + 1] - hs[i])

def main():
    c, pa, inj, tp = load_comb()
    mp = map_csv(c)
    m20 = mp[293.15]; m5 = mp[min(mp.keys())]
    L = loads(c, pa, inj)
    stroke = pa['stroke_m']['v']
    sp = spring_design(L, stroke)
    x_floor20 = [r for r in m20 if abs(r[3] - 0.125) < 1e-6][0][0]
    x_20pct = [r for r in m20 if abs(r[3] - 0.2) < 1e-6][0][0]
    x_max20 = [r for r in m20 if abs(r[3] - 1.0) < 1e-6][0][0]
    x_floor5 = [r for r in m5 if abs(r[3] - 0.125) < 1e-6][0][0]
    x_max5 = [r for r in m5 if abs(r[3] - 1.0) < 1e-6][0][0]
    cands = [Sym(stroke, 25.0), Sym(stroke, 40.0)]
    for r in (4e-3, 5e-3, 6e-3, 7e-3):
        for pc in (5.0, 10.0, 15.0):
            g = Tog(r, pc); 
            if g.travel(stroke) <= 100.0: cands.append(g)
    for g in cands:
        g.spring = sp if isinstance(g, Tog) else None
    res = []
    P20 = 5052509.0; Pcold = 3541606.0
    for g in cands:
        row = dict(name=g.name, travel_deg=g.travel(stroke))
        for lab, x, mm in (('floor12p5_20C', x_floor20, m20), ('pct20_20C', x_20pct, m20), ('max_20C', x_max20, m20),
                           ('floor12p5_5C', x_floor5, m5), ('max_5C', x_max5, m5)):
            dx = g.dxda(x) * math.radians(DB_US / US_PER_DEG)
            row[f'res_um_{lab}'] = dx * 1e6
            row[f'res_N_{lab}'] = dx * dFdx_at(mm, x)
            row[f'res_N_3us_{lab}'] = 3 * dx * dFdx_at(mm, x)
        for V in (7.0, 7.4):
            t_up, T1 = stroke_time(g, L, x_20pct, x_max20, V, P20)
            t_dn, T2 = stroke_time(g, L, x_max20, x_20pct, V, P20)
            t_full, T3 = stroke_time(g, L, 0.0, stroke, V, L['P_meop'])
            t_close, T4 = stroke_time(g, L, stroke, 0.0, V, L['P_meop'])
            Ts, _ = servo_at(V)
            row[f'V{V}'] = dict(t_20to100_s=t_up, t_100to20_s=t_dn, t_full_open_s=t_full, t_full_close_s=t_close,
                                T_peak_Nm=max(T1, T2, T3, T4), T_stall_Nm=Ts, torque_margin=Ts / max(T1, T2, T3, T4))
        res.append(row)
    # selection rule: full open <= combustion full-stroke time at 7.4 V, then best floor resolution
    t_req = pa['full_stroke_time_s']['v']
    ok = [r for r in res if r['V7.4']['t_full_open_s'] <= t_req and r['name'].startswith('TOG')]
    best = min(ok, key=lambda r: r['res_um_floor12p5_20C']) if ok else None
    out = dict(id='pintle_linkage', version='v2', date='2026-10-11',
               inputs=dict(combustion_json=json.load(open(COMB))['version'], stroke_m=stroke,
                           seal_friction_N=L['F_seal'], stem_force_open_meop_N=L['F_open_meop'], seat_force_meop_N=L['F_seat_meop'],
                           full_stroke_time_req_s=t_req, resolution_req_m=pa['position_resolution_m']['v'],
                           deadband_us=dict(v=DB_US, range=DB_RANGE, tag='ASSUMED'), latency_s=dict(v=LAT, tag='DATASHEET frame + ASSUMED 1 ms'),
                           eta_link=dict(v=ETA, tag='ASSUMED')),
               spring=sp, lifts=dict(floor12p5_20C=x_floor20, pct20_20C=x_20pct, max_20C=x_max20, floor12p5_5C=x_floor5, max_5C=x_max5),
               candidates=res, selected=best['name'] if best else None,
               selection_rule='TOG geometries with full 0->4 mm open <= combustion full_stroke_time at 7.4 V; then finest floor resolution')
    json.dump(out, open(os.path.join(OUT, 'pintle_linkage_v2.json'), 'w'), indent=1)
    lines = [f"pintle_linkage_v2  (combustion.json {out['inputs']['combustion_json']})",
             f"spring F0={sp['F0']:.1f} N k={sp['k']/1e3:.1f} N/mm F(4mm)={sp['F_full']:.1f} N; seat force at MEOP {L['F_seat_meop']:.1f} N, stem open force at MEOP {L['F_open_meop']:.1f} N",
             f"{'geometry':28s} {'trav':>5s} | res um (1us) floor/20%/max/floor5C | N(1us) floor | N(3us) floor | 7.0V: 20->100 100->20 full_open close  Tpk margin | 7.4V full_open"]
    for r in res:
        v0 = r['V7.0']; v1 = r['V7.4']
        lines.append(f"{r['name']:28s} {r['travel_deg']:5.1f} | {r['res_um_floor12p5_20C']:5.2f} {r['res_um_pct20_20C']:5.2f} {r['res_um_max_20C']:5.2f} {r['res_um_floor12p5_5C']:5.2f} |"
                     f" {r['res_N_floor12p5_20C']:5.2f} | {r['res_N_3us_floor12p5_20C']:5.2f} | {v0['t_20to100_s']*1e3:5.1f} {v0['t_100to20_s']*1e3:5.1f} {v0['t_full_open_s']*1e3:6.1f} {v0['t_full_close_s']*1e3:5.1f}"
                     f" {v0['T_peak_Nm']:4.2f} {v0['torque_margin']:4.1f} | {v1['t_full_open_s']*1e3:6.1f}")
    lines.append(f"selected: {out['selected']}  ({out['selection_rule']})")
    open(os.path.join(OUT, 'pintle_linkage_v2.txt'), 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))

if __name__ == '__main__':
    main()
