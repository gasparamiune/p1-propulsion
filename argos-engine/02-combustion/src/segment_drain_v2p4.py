"""Segment state after a shutdown, by shutdown order (Combustion v2.4; zone-top MV-P, LEAD 2026-10-13 option A).

Question: with the main valve at the zone top, the valve-to-seat segment (about 44 cm3) keeps feeding the pintle after the
valve has closed (throat_block_v2p4 tail-off: 19.3 g after the decision with the segment, 6.6 g with the valve at the pintle).
How much of the segment empties during a shutdown, how large is the vapour pocket left for the next relight, and does a
pintle-first order (valve closed only once the pintle is seated) keep the segment primed?

Model: throat_block_v2p4 (grain_q1d v2 engine + series valve + flashing segment, homogeneous equilibrium, CoolProp HEOS),
RC-01 tail-off from steady thrust: decision at 0.05 s, pintle command 6.5 ms later (servo 16.7 mm/s, 10 ms lag).
Orders:
  MV_first_30ms   valve de-energised at the decision, 30 ms MV-P close (A4 / abort order, v2.4 sequence);
  MV_first_100ms  the same with the 0.10 s bounding close;
  pintle_first    valve de-energised when the pintle reaches the seat (position feedback) or at decision + 0.20 s,
                  whichever comes first (PROPOSAL for planned cut-offs only).
Outputs per case: N2O and impulse after the decision, segment liquid mass and vapour volume at 0.6 s, and the purge time of
that pocket at the 0.2039 mm ignition lift (SIM C7 0.31 s per 21.42 cm3 at 0.219 mm, scaled with volume and with the lift
ratio, DERIVED). The pocket left after the shutdown adds to any coast boil-off (segment_recheck_v2p4).
usage: python -I segment_drain_v2p4.py OUTDIR
"""
from __future__ import annotations
import json, os, sys
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import throat_block_v2p4 as TB

LIFT_RATIO = 0.2191572e-3 / 0.2039e-3     # SIM C7 purge basis lift (A1 relight, 12.5 %) over the v2.8 default lift
PURGE_PER_CM3 = 0.31 / 21.42 * LIFT_RATIO  # s per cm3 of vapour (DERIVED)
E1E2_LIQUID_MAX = 0.357                    # s, valve at E0, liquid line, K15 loop (relight_latency_sup_seg44_v2p4)


def run(T, F0, segV, order, t_end=0.6, dt=2e-4, Cd=0.70):
    t_close = 0.10 if order == 'MV_first_100ms' else 0.030
    e, s0 = TB.make(T, Cd, 0.0, t_close, segV, 1.0, F0, 3.6)
    e.At_hist = None
    t_dec = 0.05; t = 0.0; rec = []; t_seat = None
    while t < t_end:
        e.t = t
        if t >= t_dec + 0.0065:
            e.state = 'shutdown'
        if e.t_valve is None and t >= t_dec:
            if order.startswith('MV_first'):
                e.t_valve = t_dec
            else:
                if e.h <= 1e-7 and t_seat is None:
                    t_seat = t
                if t_seat is not None or t >= t_dec + 0.20:
                    e.t_valve = t
        F = e.step(dt)
        rec.append((t, F, e.Pc, e.mox))
        t += dt
    r = np.array(rec); tt, FF, PP, MM = r.T
    k = tt >= t_dec
    tr = np.trapezoid if hasattr(np, 'trapezoid') else np.trapz
    s = e.seg
    v_vap = segV * (1.0 - s.liq_vol_frac) * 1e6
    purge = PURGE_PER_CM3 * v_vap
    return dict(T_tank_C=T - 273.15, F0_N=float(s0['F']), h0_mm=float(s0['h']) * 1e3, segment_cm3=segV * 1e6, order=order,
                valve_close_start_after_decision_s=(e.t_valve - t_dec) if e.t_valve is not None else None,
                pintle_seated_after_decision_s=(t_seat - t_dec) if t_seat is not None else None,
                N2O_after_decision_g=1e3 * float(tr(MM[k], tt[k])), impulse_after_decision_Ns=float(tr(FF[k], tt[k])),
                segment_end=dict(P_bar=s.P / 1e5, T_K=s.T, mass_g=s.m * 1e3, quality=s.x, liquid_volume_fraction=s.liq_vol_frac,
                                 vapour_volume_cm3=v_vap),
                purge_of_pocket_at_0p2039mm_s=purge, E1E2_max_estimate_s=E1E2_LIQUID_MAX + purge,
                segment_fail_updates=s.fail)


def main(outdir):
    res = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/segment_drain_v2p4.py',
               tags=dict(model='SIM throat_block_v2p4 (grain_q1d v2, HEM segment, Cd 0.70 ASSUMED)', segment='LEAD relay 44 cm3 (ESTIMATE), Mechanical 32.6 cm3',
                         purge='DERIVED from SIM C7 (0.31 s per 21.42 cm3 at 0.219 mm) x lift ratio', order='pintle_first = PROPOSAL'),
               cases={})
    for segV in (44.0e-6, 32.6e-6):
        for T in (287.0, 293.15, 303.15):
            for F0 in (500.0, 300.0):
                for order in ('MV_first_30ms', 'MV_first_100ms', 'pintle_first'):
                    if F0 == 300.0 and order == 'MV_first_100ms':
                        continue
                    r = run(T, F0, segV, order)
                    key = f"seg{segV*1e6:g}|T{T-273.15:.1f}C|F{F0:.0f}|{order}"
                    res['cases'][key] = r
                    se = r['segment_end']
                    print(f"{key:40s} N2O {r['N2O_after_decision_g']:.1f} g I {r['impulse_after_decision_Ns']:.1f} Ns | seat {r['pintle_seated_after_decision_s']} "
                          f"| seg end {se['mass_g']:.1f} g, liq vol {se['liquid_volume_fraction']:.3f}, vapour {se['vapour_volume_cm3']:.1f} cm3, P {se['P_bar']:.1f} bar "
                          f"| purge {r['purge_of_pocket_at_0p2039mm_s']:.3f} s, E1E2max ~{r['E1E2_max_estimate_s']:.3f} s", flush=True)
    fn = os.path.join(outdir, 'segment_drain_v2p4.json')
    json.dump(res, open(fn, 'w'), indent=1, default=float)
    print('wrote', fn)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
