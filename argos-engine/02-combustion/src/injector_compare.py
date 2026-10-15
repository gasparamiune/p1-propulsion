"""Injector model comparison and Cd uncertainty (Combustion v2, brief task 2: Dyer vs SPI vs HEM, Cd uncertainty).

1. Mass flux G(P2) for SPI / HEM / Dyer at T1 = 15 / 20 / 25 C (saturated tank, P1 = Pv - feed-line loss).
2. At the throttle operating points (initial port, saturated tank at 15/20/25 C) the oxidiser flow is fixed by the
   thrust command; the pintle lift each model needs (Cd 0.70) shows how much the model choice moves the
   feed-forward map. The closed Pc loop absorbs the difference; the stroke ceiling and the feed-forward error do not.
3. Cd uncertainty: lift and flow sensitivity for Cd 0.60 / 0.70 / 0.80 (LITERATURE range for pintle and
   annular-gap elements; no ARGOS measurement exists).
Outputs: data/v2/injector_compare_v2.{csv,json}; figs/v2/injector_models_v2.png.  Tags: SIM (CoolProp HEOS N2O,
Dyer et al. AIAA 2007-5702 blending), ASSUMED (Cd, line loss).
usage: python injector_compare.py OUTDIR FIGDIR
"""
from __future__ import annotations
import csv, json, math, os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import injector as INJ
import grain_q1d as Q
from run_dc import _FixedTank

TEMPS_C = (15.0, 20.0, 25.0)
FRACS = (1.0, 0.75, 0.5, 0.25, 0.20, 0.125)


def curves():
    out = {}
    for Tc in TEMPS_C:
        T1 = Tc + 273.15
        pv = INJ.psat(T1)
        for dp_line, tag in ((2.5e5, 'full'), (0.05e5, 'floor')):
            P1 = pv - dp_line
            P2 = np.linspace(2e5, min(P1 - 0.2e5, 32e5), 160)
            spi, hem, dyer, k = INJ.g_models(P1, T1, P2)
            out[(Tc, tag)] = dict(P1=P1, pv=pv, P2=P2, spi=spi, hem=hem, dyer=dyer)
    return out


def operating_points():
    rows = []
    gt = INJ.GTable()
    for Tc in TEMPS_C:
        T = Tc + 273.15
        pv = INJ.psat(T)
        e = Q.Engine(_FixedTank(pv, T))
        cei = e.ceiling()
        for fr in FRACS:
            F = 500 * fr
            if F > cei['F'] + 0.1:
                rows.append(dict(T_tank_C=Tc, frac=fr, note='above ceiling', F_ceiling_N=cei['F']))
                continue
            h, _ = e.lift_for_thrust(F, cei=cei); s = e.steady(h)
            P1 = s['P1'] if 'P1' in s else pv - e.dp_line(s['mox'])
            Pc = s['Pc']; mox = s['mox']
            r = dict(T_tank_C=Tc, frac=fr, F_N=s['F'], Pc_Pa=Pc, P1_Pa=P1, Pv_Pa=pv, mdot_ox=mox, OF=s['OF'],
                     dP_over_Pc=s['dpc'], F_ceiling_N=cei['F'], ceiling_limit=cei['limit'])
            for m in ('spi', 'hem', 'dyer'):
                G = gt.G(P1, T, Pc, m)
                r[f'G_{m}'] = G
                A = mox / (0.70 * G)
                r[f'lift_{m}_mm'] = INJ.pintle_lift(A) * 1e3 if A < INJ.pintle_area(INJ.STROKE) else float('nan')
            r['G_spi_over_dyer'] = r['G_spi'] / r['G_dyer']; r['G_hem_over_dyer'] = r['G_hem'] / r['G_dyer']
            k = math.sqrt(max(P1 - Pc, 0) / max(pv - Pc, 1e-9)) if pv > Pc else float('inf')
            r['dyer_k'] = k
            Gd = r['G_dyer']
            for cd in (0.60, 0.80):
                A = mox / (cd * Gd)
                r[f'lift_dyer_Cd{cd:.2f}_mm'] = INJ.pintle_lift(A) * 1e3 if A < INJ.pintle_area(INJ.STROKE) else float('nan')
            # flow error if the feed-forward assumes Cd 0.70 but the true Cd is 0.60/0.80 (lift fixed, Pc held by loop)
            r['flow_err_Cd_pm0p1_pct'] = 100 * 0.10 / 0.70
            rows.append(r)
        print(f'T {Tc} C ceiling {cei["F"]:.1f} N ({cei["limit"]})', flush=True)
    return rows


def stroke_ceiling_vs_cd():
    """Thrust ceiling at 20 C and 15 C for Cd 0.60/0.70/0.80: stroke vs stiffness limit."""
    out = []
    for Tc in (15.0, 20.0, 25.0):
        T = Tc + 273.15; pv = INJ.psat(T)
        for cd in (0.50, 0.60, 0.70, 0.80):
            e = Q.Engine(_FixedTank(pv, T), cfg=dict(Q.V, Cd=cd))
            c = e.ceiling()
            out.append(dict(T_tank_C=Tc, Cd=cd, F_ceiling_N=c['F'], limit=c['limit'], lift_mm=c['h'] * 1e3,
                            Pc_Pa=c['Pc'], dP_over_Pc=c['dpc']))
    return out


def ceiling_worst_model(rows):
    """Stroke ceiling if the real element follows HEM (or SPI) instead of Dyer: effective Cd relative to the Dyer model
    Cd_eff = Cd x G_model/G_Dyer at the max-thrust point of that temperature; plus the minimum Cd_eff (vs Dyer) that keeps a
    500 N ceiling at each temperature (bisection) = the cold-flow acceptance gate for the 5.5 mm seat."""
    out = dict(rows=[], min_Cd_eff_for_500N={})
    for Tc in TEMPS_C:
        T = Tc + 273.15; pv = INJ.psat(T)
        r_max = [r for r in rows if r['T_tank_C'] == Tc and r['frac'] == 1.0 and 'G_dyer' in r]
        if not r_max:
            continue
        rm = r_max[0]
        for model, ratio in (('HEM', rm['G_hem_over_dyer']), ('SPI', rm['G_spi_over_dyer'])):
            for cd in (0.60, 0.70, 0.80):
                cde = cd * ratio
                e = Q.Engine(_FixedTank(pv, T), cfg=dict(Q.V, Cd=cde))
                c = e.ceiling()
                if c is None:   # e.g. SPI x Cd 0.8 -> Cd_eff > 1: outside the steady solver's range (not physical)
                    out['rows'].append(dict(T_tank_C=Tc, model=model, Cd_nominal=cd, G_ratio_to_Dyer=ratio,
                                            Cd_eff_vs_Dyer=cde, F_ceiling_N=float('nan'),
                                            limit='no steady solution (Cd_eff outside model range)', dP_over_Pc=float('nan')))
                    continue
                out['rows'].append(dict(T_tank_C=Tc, model=model, Cd_nominal=cd, G_ratio_to_Dyer=ratio, Cd_eff_vs_Dyer=cde,
                                        F_ceiling_N=c['F'], limit=c['limit'], dP_over_Pc=c['dpc']))
        lo, hi = 0.2, 0.9
        for _ in range(14):
            mid = 0.5 * (lo + hi)
            c = Q.Engine(_FixedTank(pv, T), cfg=dict(Q.V, Cd=mid)).ceiling()
            if c['F'] >= 500.0:
                hi = mid
            else:
                lo = mid
        out['min_Cd_eff_for_500N'][f'{Tc:.0f}C'] = hi
        print(f'T {Tc} C: min Cd_eff (vs Dyer) for a 500 N ceiling = {hi:.3f}', flush=True)
    return out


def figure(cv, rows, figdir):
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.6))
    ax = axs[0]
    cols = {15.0: 'tab:blue', 20.0: 'tab:green', 25.0: 'tab:red'}
    for (Tc, tag), d in cv.items():
        if tag != 'full':
            continue
        c = cols[Tc]
        ax.plot(d['P2'] / 1e5, d['spi'] / 1e3, ':', color=c, lw=1.2)
        ax.plot(d['P2'] / 1e5, d['hem'] / 1e3, '--', color=c, lw=1.2)
        ax.plot(d['P2'] / 1e5, d['dyer'] / 1e3, '-', color=c, lw=1.8, label=f'{Tc:.0f} C (Pv {d["pv"]/1e5:.1f} bar)')
    ax.axvspan(4.36, 25.0, color='0.9', zorder=0)
    ax.text(5, 1.0, 'engine Pc range 4.4-25 bar', fontsize=8)
    ax.set_xlabel('chamber pressure P2 [bar]'); ax.set_ylabel('G = mdot/(Cd A) [kg/m2/s x1e3]')
    ax.set_title('N2O mass flux, P1 = Pv - 2.5 bar\nSPI dotted, HEM dashed, Dyer solid', fontsize=9)
    ax.legend(fontsize=8); ax.grid(alpha=0.3); ax.set_ylim(0, None)
    ax = axs[1]
    for Tc in TEMPS_C:
        rr = [r for r in rows if r['T_tank_C'] == Tc and 'G_dyer' in r]
        fr = [r['frac'] * 100 for r in rr]
        ax.plot(fr, [r['G_spi_over_dyer'] for r in rr], 'o:', color=cols[Tc], label=f'SPI/Dyer {Tc:.0f} C')
        ax.plot(fr, [r['G_hem_over_dyer'] for r in rr], 's--', color=cols[Tc], label=f'HEM/Dyer {Tc:.0f} C')
    ax.axhline(1, color='k', lw=0.6)
    ax.set_xlabel('thrust [% of 500 N]'); ax.set_ylabel('G_model / G_Dyer at the operating point')
    ax.set_title('Model spread at the operating points\n(initial port, saturated tank)', fontsize=9)
    ax.grid(alpha=0.3); ax.legend(fontsize=7, ncol=2)
    ax = axs[2]
    rr = [r for r in rows if r['T_tank_C'] == 20.0 and 'G_dyer' in r]
    fr = np.array([r['frac'] * 100 for r in rr])
    for m, st in (('spi', 'o:'), ('hem', 's--'), ('dyer', 'D-')):
        ax.plot(fr, [r[f'lift_{m}_mm'] for r in rr], st, label=f'{m.upper()} (Cd 0.70)')
    lo = [r['lift_dyer_Cd0.80_mm'] for r in rr]; hi = [r['lift_dyer_Cd0.60_mm'] for r in rr]
    ax.fill_between(fr, lo, hi, color='tab:green', alpha=0.2, label='Dyer, Cd 0.60-0.80')
    ax.axhline(INJ.STROKE * 1e3, color='k', lw=0.8); ax.text(15, INJ.STROKE * 1e3 - 0.25, 'stroke 4 mm', fontsize=8)
    ax.set_xlabel('thrust [% of 500 N]'); ax.set_ylabel('pintle lift [mm]')
    ax.set_title('Lift needed at 20 C: model and Cd uncertainty', fontsize=9)
    ax.grid(alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout()
    fn = os.path.join(figdir, 'injector_models_v2.png'); fig.savefig(fn, dpi=130); plt.close(fig)
    return fn


if __name__ == '__main__':
    outdir, figdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True); os.makedirs(figdir, exist_ok=True)
    cv = curves()
    rows = operating_points()
    cc = stroke_ceiling_vs_cd()
    wm = ceiling_worst_model(rows)
    fn = os.path.join(outdir, 'injector_compare_v2.csv')
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(fn, 'w', newline='') as f:
        f.write('# Injector model comparison at throttle operating points (initial port, saturated tank at T). G in '
                'kg/m2/s; lifts in mm for pintle seat 5.5 mm / 15 deg cone. SIM (CoolProp HEOS, Dyer 2007 blending); '
                'Cd ASSUMED 0.70 (0.60-0.80 band). SI.\n')
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    json.dump(dict(version='v2', date='2026-10-12', grain=Q.V.get('L_grain'), operating_points=rows, ceiling_vs_Cd=cc,
                   ceiling_worst_model=wm,
                   notes=['Cd 0.70 is ASSUMED: no ARGOS flow measurement; the measurement plan is in REPORT.md section 3.6',
                          'The closed Pc loop removes steady Cd/model error from the thrust; it remains in the feed-forward '
                          '(transient tracking) and in the stroke-limited ceiling.']),
              open(os.path.join(outdir, 'injector_compare_v2.json'), 'w'), indent=1, default=float)
    print(figure(cv, rows, figdir))
    for r in cc:
        print(r)
    for r in rows:
        if 'G_dyer' in r:
            print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k in (
                'T_tank_C', 'frac', 'Pc_Pa', 'P1_Pa', 'mdot_ox', 'G_spi_over_dyer', 'G_hem_over_dyer', 'lift_spi_mm',
                'lift_hem_mm', 'lift_dyer_mm', 'lift_dyer_Cd0.60_mm', 'lift_dyer_Cd0.80_mm', 'dyer_k')})
