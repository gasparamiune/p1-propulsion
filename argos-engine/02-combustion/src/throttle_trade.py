"""Throttle-architecture trade (Combustion v2, brief task 3): numbers behind the qualitative criteria.
(a) characterised (V-port) ball valve close-coupled to a fixed showerhead injector
(b) variable-area pintle injector (baseline, lead decision 2026-10-11) + NC isolation valve
(c) needle/control valve upstream of a fixed showerhead (feed line + manifold between them)
For each throttle point of the v2 map (quasi-1D model, 20 C tank, initial port):
  - (b): injector dP/Pc, injector sensitivity a = -dln(mdot)/dln(Pc) (Dyer table), lift, flow gain dF/dh
  - (a)/(c): showerhead CdA fixed at the max-thrust point (same P1 as (b)); valve throttles to P_mid; fluid after the
    valve = isenthalpic flash of the tank liquid; injector flow HEM from the two-phase state (P_mid, h) to Pc;
    reported: P_mid, vapour quality x_mid, injector dP/Pc, sensitivity a, manifold compliance and feed-system mode.
    Valve law: (a) equal-percentage V-ball, rangeability 50 (ASSUMED), 90 deg; (c) linear needle (ASSUMED).
Outputs data/v2/throttle_trade_v2.json/.csv
"""
from __future__ import annotations
import csv, json, math, os, sys
import numpy as np
import CoolProp.CoolProp as CP
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import grain_q1d as Q
from run_dc import _FixedTank
F = 'NitrousOxide'
AS = CP.AbstractState('HEOS', F)


def flash_h(p, h):
    AS.update(CP.HmassP_INPUTS, h, p)
    return AS.rhomass(), AS.smass(), AS.Q(), AS.T()


def G_hem_from(p1, h1, p2, n=80):
    rho1, s1, q1, T1 = flash_h(p1, h1)
    best = 0.0; pc = p2
    for p in np.linspace(p2, p1 * 0.9999, n):
        AS.update(CP.PSmass_INPUTS, p, s1)
        dh = h1 - AS.hmass()
        if dh <= 0:
            continue
        g = AS.rhomass() * math.sqrt(2 * dh)
        if g > best:
            best, pc = g, p
    return best, pc


def two_phase_sound_speed(p, h):
    """HEM (equilibrium) sound speed from finite differences of rho(p, s)."""
    rho, s, q, T = flash_h(p, h)
    AS.update(CP.PSmass_INPUTS, p * 1.002, s); r1 = AS.rhomass()
    AS.update(CP.PSmass_INPUTS, p * 0.998, s); r0 = AS.rhomass()
    return math.sqrt((0.004 * p) / (r1 - r0)), rho


def main(outdir):
    T_tank = 293.15
    P_tank = CP.PropsSI('P', 'T', T_tank, 'Q', 0, F)
    AS.update(CP.QT_INPUTS, 0.0, T_tank); h_l = AS.hmass()
    e = Q.Engine(_FixedTank(P_tank, T_tank))
    rows = []
    # showerhead sized at max thrust: same P1 (after line loss) as the pintle case, liquid inlet
    s100 = e.steady(e.lift_for_thrust(500.0)[0])
    CdA_sh = s100['mox'] / e.GT.G(s100['P1'], T_tank, s100['Pc'])
    V_man = {'a': 3e-6, 'c': 3e-6 + math.pi / 4 * 0.0079 ** 2 * 0.30}     # close-coupled vs 0.30 m -6 line + manifold
    for fr in (1.0, 0.75, 0.5, 0.25, 0.2, 0.125):
        h, _ = e.lift_for_thrust(500 * fr); s = e.steady(h)
        Pc, mox = s['Pc'], s['mox']
        m0, _ = e.mox_inj(h, Pc); m1, _ = e.mox_inj(h, Pc * 1.01)
        a_b = -(math.log(m1) - math.log(m0)) / math.log(1.01)
        dh = 2e-6; sF = e.steady(h + dh)
        row = dict(frac=fr, Pc_Pa=Pc, mdot_ox=mox, b_lift_m=h, b_dP_over_Pc=s['dpc'], b_a=a_b,
                   b_dF_dh_N_per_mm=(sF['F'] - s['F']) / dh * 1e-3)
        # (a)/(c): find P_mid giving mox through the fixed showerhead (two-phase HEM from flashed state)
        lo, hi = Pc * 1.0005, s100['P1']
        for _ in range(60):
            pm = 0.5 * (lo + hi)
            G, _ = G_hem_from(pm, h_l, Pc) if pm < P_tank * 0.999 else (e.GT.G(pm, T_tank, Pc), 0)
            if CdA_sh * G > mox:
                hi = pm
            else:
                lo = pm
        pm = 0.5 * (lo + hi)
        rho_m, _, x_m, T_m = flash_h(pm, h_l)
        G0_, _ = G_hem_from(pm, h_l, Pc); G1_, _ = G_hem_from(pm, h_l, Pc * 1.01)
        a_sh = -(math.log(G1_) - math.log(G0_)) / math.log(1.01) if G1_ > 0 and G0_ > 0 else float('nan')
        c2p, _ = two_phase_sound_speed(pm, h_l)
        row.update(ac_P_mid_Pa=pm, ac_quality_x=max(x_m, 0.0), ac_rho_mid=rho_m, ac_dP_over_Pc=(pm - Pc) / Pc, ac_a=a_sh,
                   ac_sound_speed_m_s=c2p)
        for k in ('a', 'c'):
            Cm = V_man[k] / (rho_m * c2p ** 2)          # compliance dm/dp [kg/Pa]
            # injector resistance R = dP/dmdot (linearised), feed-volume time constant tau = R*C
            G2_, _ = G_hem_from(pm * 1.01, h_l, Pc)
            dmdP = CdA_sh * (G2_ - G0_) / (0.01 * pm)
            tau = Cm / max(dmdP, 1e-12)
            row[f'{k}_manifold_tau_s'] = tau
        # valve characteristics: required Cv fraction for the throttling dP (liquid-equivalent, ignores flashing)
        dPv = P_tank - pm
        rows.append(row)
        print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()}, flush=True)
    fn = os.path.join(outdir, 'throttle_trade_v2.csv')
    with open(fn, 'w', newline='') as f:
        f.write('# Throttle architecture trade v2 (throttle_trade.py). b_ = pintle; ac_ = valve + fixed showerhead (sized at '
                'max thrust). a = -dln(mdot)/dln(Pc). SIM/DERIVED; two-phase states CoolProp HEM.\n')
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    json.dump(dict(CdA_showerhead_m2=CdA_sh, P_tank=P_tank, rows=rows), open(os.path.join(outdir, 'throttle_trade_v2.json'), 'w'),
              indent=1, default=float)


if __name__ == '__main__':
    main(sys.argv[1])
