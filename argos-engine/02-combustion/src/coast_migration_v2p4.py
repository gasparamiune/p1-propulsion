"""Buoyant bubble migration along the A1 coast specific-force history (Combustion v2.4; REV-GNC-1 RG-20, 2026-10-13).

RG-20: use GNC's time history, not the shorthand "at least 11.4 s at +8 m/s2" (11.4 s is the minimum duration of positive f_z
before the relight command; 8.18 m/s2 is the descent mean; the history has a -1.90 m/s2 dip at the drogue turnover).
For each GNC series (nominal and the four listed runs, including the minimum-acceleration run 264) and for the p01 / p50 /
p99 envelope aligned at the relight command, integrate the Taylor-bubble drift of relight_vapour_order_v2p4 (Wallis /
White-Beardmore form; no drift for Eo <= 3.37) with the instantaneous seat specific force:
    dx/dt = sign(f_z) U_drift(|f_z|, D)        x > 0 toward +z (the zone-top MV), x < 0 toward the seat / U-bottom.
Reported per passage: displacement in the coast-up (MECO to the first instant of the final positive interval), in the final
positive interval, the largest backward excursion after the drogue load (turnover dip); the coast-up displacement runs from the first instant with
f_z < 0 (after the tail-off) to the drogue load (first f_z > 0.5 g after that), and the time needed in the final
interval to move each leg's length. The inclined coil (3.9 deg) is bracketed as in relight_vapour_order_v2p4 (Fr 0.10 low,
Bendiksen high, on the axial component). Lateral specific force (flat_seat up to 3.1 m/s2) is not integrated (no coil-plane
geometry); it is listed against the trap height.
usage: python -I coast_migration_v2p4.py SERIES_CSV ENVELOPE_RELIGHT_CSV VAPOUR_ORDER_JSON OUT_JSON
"""
from __future__ import annotations
import json, math, os, sys, hashlib
sys.dont_write_bytecode = True
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import relight_vapour_order_v2p4 as RV

PASSAGES = {'2 mm annular gap (bore leg)': 2.0e-3, '3 mm drilling': 3.0e-3, '7.75 mm riser / wall line': 7.747e-3,
            '8 mm drillings / block': 8.0e-3, '14 mm filter bore': 14.0e-3}
LEGS_M = {'wall line (module -> U-bottom), 7.75 mm': ('7.75 mm riser / wall line', 0.195),
          'riser + fittings, 7.75 mm': ('7.75 mm riser / wall line', 0.089),
          'block + head + bonnet drillings, 8 mm': ('8 mm drillings / block', 0.054),
          'bore leg (crest -> seat), 2 mm gap': ('2 mm annular gap (bore leg)', 0.094)}


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def integrate(t, fz, D, p):
    u = np.array([math.copysign(RV.drift(D, abs(f), p)[0], f) if f != 0 else 0.0 for f in fz])
    dt = np.diff(t, prepend=t[0])
    return np.cumsum(u * dt), u


def coil_u(f, p, incl, low):
    if f == 0:
        return 0.0
    g = abs(f); sgD = math.sqrt(g * 7.9e-3 * (p['rho_l'] - p['rho_v']) / p['rho_l'])
    U = 0.10 * sgD if low else (0.54 * math.cos(incl) + 0.35 * math.sin(incl)) * sgD
    return math.copysign(U, f)


def analyse(t, fz, p, incl, flat=None):
    pos = fz > 0
    # start of the final positive interval (last instant with fz <= 0, then +1 sample)
    nonpos = np.where(~pos)[0]
    i0 = int(nonpos[-1]) + 1 if len(nonpos) else 0
    # coast-up start: first instant with fz < 0 (after the thrust tail-off); descent onset (drogue loaded): first instant
    # after that with fz > 0.5 g0
    neg = np.where(fz < 0)[0]
    i_cu = int(neg[0]) if len(neg) else 0
    later = np.where((np.arange(len(fz)) > i_cu) & (fz > 0.5 * 9.80665))[0]
    i_up_end = int(later[0]) if len(later) else i0
    out = dict(t_final_positive_s=float(t[-1] - t[i0]), t_from_drogue_load_s=float(t[-1] - t[i_up_end]),
               t_coast_up_to_drogue_load_s=float(t[i_up_end] - t[i_cu]), t_coast_up_to_final_positive_s=float(t[i0] - t[i_cu]),
               fz_min_mps2=float(fz.min()), fz_min_after_drogue_load_mps2=float(fz[i_up_end:].min()),
               passages={})
    for name, D in PASSAGES.items():
        x, u = integrate(t, fz, D, p)
        x_up = float(x[i0] - x[i_cu])                      # coast-up start -> start of the final positive interval (net)
        x_toward_seat = float(np.min(x[i_cu:i0 + 1] - x[i_cu])) if i0 >= i_cu else 0.0   # largest excursion toward the seat
        x_fin = float(x[-1] - x[i0])                       # final positive interval
        back = 0.0
        if i_up_end < len(x) - 1:
            seg = x[i_up_end:]
            back = float(np.min(seg - np.maximum.accumulate(seg)))   # largest backward excursion after the drogue load
        out['passages'][name] = dict(x_coast_up_net_mm=1e3 * x_up, x_coast_up_max_toward_seat_mm=1e3 * x_toward_seat,
                                     x_final_positive_interval_mm=1e3 * x_fin,
                                     max_backward_excursion_after_drogue_load_mm=1e3 * back,
                                     Eo_at_fz_min=RV.drift(D, abs(float(fz.min())), p)[1])
    for low in (True, False):
        uc = np.array([coil_u(f, p, incl, low) for f in fz]); dt = np.diff(t, prepend=t[0]); xc = np.cumsum(uc * dt)
        out['passages']['7.9 mm coil hose at 3.9 deg (%s bracket)' % ('Fr 0.10' if low else 'Bendiksen')] = dict(
            x_coast_up_net_mm=1e3 * float(xc[i0] - xc[i_cu]), x_coast_up_max_toward_seat_mm=1e3 * float(np.min(xc[i_cu:i0 + 1] - xc[i_cu])) if i0 >= i_cu else 0.0,
            x_final_positive_interval_mm=1e3 * float(xc[-1] - xc[i0]),
            max_backward_excursion_after_drogue_load_mm=1e3 * float(np.min(xc[i_up_end:] - np.maximum.accumulate(xc[i_up_end:]))))
    legs = {}
    for leg, (pname, L) in LEGS_M.items():
        D = PASSAGES[pname]; x, _ = integrate(t[i0:], fz[i0:], D, p)
        k = np.where(x - x[0] >= L)[0]
        legs[leg] = dict(L_m=L, time_to_traverse_in_final_interval_s=float(t[i0 + k[0]] - t[i0]) if len(k) else None,
                         margin_to_relight_cmd_s=float(t[-1] - t[i0 + k[0]]) if len(k) else None)
    out['legs'] = legs
    if flat is not None:
        th = np.degrees(np.arctan2(flat, fz))               # angle of the specific force from +z
        crit = math.degrees(math.atan2(159.585, 54.0))       # U-bottom level with the crest: coil end ~54 mm off axis (ASSUMED crest on axis)
        dsc = np.arange(len(t)) >= i_up_end
        m = dsc & (fz > 0) & (th > crit)
        longest = 0.0; run = 0.0
        dtt = np.diff(t, prepend=t[0])
        for k in range(len(t)):
            run = run + dtt[k] if m[k] else 0.0
            longest = max(longest, run)
        out['tilt'] = dict(critical_angle_deg=crit, max_angle_after_drogue_load_while_fz_pos_deg=float(th[dsc & (fz > 0)].max()) if np.any(dsc & (fz > 0)) else None,
                           time_beyond_critical_after_drogue_load_s=float(np.sum(dtt[m])), longest_continuous_beyond_critical_s=longest)
    return out


def main(series_f, env_f, vo_f, out_f):
    VO = json.load(open(vo_f)); p = VO['properties']
    incl = math.radians(VO['mobility']['coil_incline_deg'])
    S = pd.read_csv(series_f)
    res = {}
    for name, g in S.groupby('series'):
        g = g[g.t_minus_relight_cmd_s <= 1e-9].sort_values('t_s')
        res[name] = analyse(g.t_s.values, g.fz_seat_mps2.values, p, incl, g.flat_seat_mps2.values)
        res[name]['window_s'] = float(g.t_s.values[-1] - g.t_s.values[0])
        res[name]['flat_seat_max_mps2'] = float(g.flat_seat_mps2.max())
    E = pd.read_csv(env_f).sort_values('t_minus_relight_cmd_s')
    E = E[E.n_runs >= 450]                                 # only instants covered by >= 90 % of the runs
    env = {}
    for q in ('p01', 'p50', 'p99'):
        env[q] = analyse(E.t_minus_relight_cmd_s.values, E[f'fz_seat_{q}_mps2'].values, p, incl)
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/coast_migration_v2p4.py',
               script_sha256_16=sha16(os.path.abspath(__file__)),
               inputs=dict(series=dict(file=series_f, sha256_16=sha16(series_f)), envelope=dict(file=env_f, sha256_16=sha16(env_f)),
                           vapour_order=dict(file=vo_f, sha256_16=sha16(vo_f))),
               sign='x > 0 toward +z (zone-top MV); x < 0 toward the seat and the U-bottom',
               series=res, envelope_aligned_at_relight_cmd=env,
               note='Envelope rows are pointwise percentiles (not a run); only instants covered by >= 450 of 500 runs are used.',
               tag='DERIVED (GNC SIM specific force x LITERATURE drift forms as recalled, TO-VERIFY)')
    json.dump(out, open(out_f, 'w'), indent=1)
    for k, v in list(res.items()) + [('env_' + q, v) for q, v in env.items()]:
        print(k, 'final+ %.2f s, from drogue %.2f s, fz_min %.2f, after drogue %.2f' % (v['t_final_positive_s'], v['t_from_drogue_load_s'],
              v['fz_min_mps2'], v['fz_min_after_drogue_load_mps2']))
        for pn, pv in v['passages'].items():
            print('   %-46s coast-up net %7.1f mm, toward seat %7.1f mm | final %8.1f mm | back %6.1f mm' % (pn, pv['x_coast_up_net_mm'], pv['x_coast_up_max_toward_seat_mm'], pv['x_final_positive_interval_mm'],
                  pv['max_backward_excursion_after_drogue_load_mm']))
        if 'tilt' in v:
            print('   tilt', json.dumps({k: round(x, 3) if isinstance(x, float) else x for k, x in v['tilt'].items()}))
        for ln, lv in v['legs'].items():
            print('   leg %-44s %s s (margin %s s)' % (ln, None if lv['time_to_traverse_in_final_interval_s'] is None else round(lv['time_to_traverse_in_final_interval_s'], 2),
                  None if lv['margin_to_relight_cmd_s'] is None else round(lv['margin_to_relight_cmd_s'], 2)))
    print('wrote', out_f)


if __name__ == '__main__':
    main(*sys.argv[1:5])
