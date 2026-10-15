"""Hard-start bound for the Electronics firmware v2.7 SIL no-light inventories (Combustion v2.4, RC-02 follow-up;
2026-10-13).

Input (SIM, Electronics plant model, firmware v2.7 SIL, CHANGELOG 2026-10-13, relayed by the lead): unignited N2O per
no-light event
  normal start 4.4-4.7 g; stand dead-torch start, abort at 0.35 s 7.81 g; cold relight 11.11 g;
  C7 +0.30 s extension (gate TC 380 K), main never lights, abort at 0.65 s: 26.59 g liquid line,
  18.38 g vapour line (3.38 g of it vapour). SIL vapour-delayed light at 0.499 s.
Questions (lead): (1) vented hard-start peak for each inventory; (2) maximum allowable unignited inventory against
MEOP 45 bar / proof 67.5 bar with margin; (3) if 18.38 g is not acceptable, a shorter extension or a reduced extension
lift that Electronics can implement.
Method: the models of hard_start_v2p4 (0-D vented chamber, Cantera products, Dyer cold flow, HEM flash), no new physics:
  1. envelope: the inventory reacting as a whole with reaction time tau (top-hat, exponential), decomposition at the
     event's tank state and fuel at O/F 8; peaks against tau and the tau below which 40.5 / 45 / 67.5 bar is exceeded;
     on two bases: all admitted mass retained (review convention) and retained = liquid fraction of the liquid admitted
     (flash quality) + the chamber vapour content (mass balance; admitted and flashed vapour leave through the throat);
  2. allowable inventory against reaction time m_allow(tau) for 40.5 bar (MEOP - 10 %), 45 bar and 67.5 bar;
  3. credible two-component case per event (fast part = chamber vapour + spray in transit 20-60 ms; slow pool
     evaporation-limited at 0.5 / 2 / 5 MW/m2), with the author's cold flow and with the cold flow implied by the SIL;
  4. fuel-assisted fast part (O/F 8) per event;
  5. reduced extension lift: lit Pc (E2 3.0 bar check), cold flow, fast part and the extension inventory against lift;
  6. stand burst-disc effect on the envelope for the SIL inventories.
Tags: SIL inventories SIM (Electronics); everything computed here DERIVED/SIM from ASSUMED inputs as hard_start_v2p4.
usage: python -I sil_inventory_bound_v2p4.py DATA_V2P4_DIR
"""
from __future__ import annotations
import json, math, os, sys, time
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import hard_start_v2p4 as HS
import grain_q1d as Q

P_LIMS = {'40.5bar_MEOP_minus_10pct': 40.5e5, '45bar_MEOP': 45e5, '67.5bar_proof': 67.5e5}
TAUS = (1e-3, 2e-3, 5e-3, 1e-2, 2e-2, 3e-2, 5e-2, 1e-1)
SIL = [dict(key='normal_start_4p4g', m_g=4.4, vap_g=0.0, state='20C', desc='normal start, lower'),
       dict(key='normal_start_4p7g', m_g=4.7, vap_g=0.0, state='20C', desc='normal start, upper'),
       dict(key='stand_dead_torch_abort_0p35s', m_g=7.81, vap_g=0.0, state='20C', desc='stand dead-torch start, abort at 0.35 s'),
       dict(key='cold_relight', m_g=11.11, vap_g=0.0, state='A1_relight', desc='cold relight'),
       dict(key='ext_vapour_line_abort_0p65s', m_g=18.38, vap_g=3.38, state='A1_relight',
            desc='C7 +0.30 s extension, main never lights, abort at 0.65 s, vapour line (3.38 g vapour)'),
       dict(key='ext_liquid_line_abort_0p65s', m_g=26.59, vap_g=0.0, state='A1_relight',
            desc='C7 +0.30 s extension, main never lights, abort at 0.65 s, liquid line (sensor invalid)')]
SIL_TAG = 'SIM Electronics firmware v2.7 SIL plant model (CHANGELOG 2026-10-13), relayed by the lead'
# SIL-implied hold flow during the extension: (26.59 - 11.11) g over 0.30 s, assuming the hot relight shares the cold
# relight's base-window inventory (DERIVED from the SIL numbers; the SIL flow history was not supplied)
SIL_EXT_FLOW = (26.59 - 11.11) * 1e-3 / 0.30
A_WET = math.pi * 0.025 * 0.230 + math.pi / 4 * 0.054 ** 2      # port + head area as hard_start_v2p4 section 5
H_EV = 375e3


def peak(m_kg, tau, shape, V, prod, **kw):
    return HS.vented_peak1(m_kg * prod['mass_per_kg_N2O'], tau, shape, V, prod, **kw)


def tau_thr(m_kg, P_lim, V, prod, shape, lo=1e-4, hi=0.5):
    if peak(m_kg, lo, shape, V, prod) < P_lim:
        return 0.0
    if peak(m_kg, hi, shape, V, prod) > P_lim:
        return float('inf')
    a, b = math.log(lo), math.log(hi)
    for _ in range(15):
        c = 0.5 * (a + b)
        if peak(m_kg, math.exp(c), shape, V, prod) > P_lim:
            a = c
        else:
            b = c
    return math.exp(0.5 * (a + b))


def m_allow(tau, P_lim, V, prod, shape, lo=1e-5, hi=0.3):
    """Largest N2O mass whose vented peak stays <= P_lim when it reacts with reaction time tau."""
    if peak(hi, tau, shape, V, prod) <= P_lim:
        return float('inf')
    a, b = lo, hi
    for _ in range(18):
        c = 0.5 * (a + b)
        if peak(c, tau, shape, V, prod) > P_lim:
            b = c
        else:
            a = c
    return 0.5 * (a + b)


def main(d):
    t0 = time.time()
    J = json.load(open(os.path.join(d, 'hard_start_v2p4.json')))
    cold = J['cold_flow_at_ignition_lift']['v']; lifts = J['ignition_lifts']['v']
    prods = {'20C': HS.products('dec', 293.15), 'A1_relight': HS.products('dec', 286.70), 'comb_OF8': HS.products('comb', 293.15, 8.0)}
    res = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/sil_inventory_bound_v2p4.py', base='hard_start_v2p4.json',
               closes='REVIEW-COMBUSTION RC-02 follow-up: lead request 2026-10-13 (firmware v2.7 SIL inventories)',
               sil_inputs=dict(v=SIL, tag=SIL_TAG), sil_implied_extension_flow_kg_s=SIL_EXT_FLOW,
               sil_implied_flow_tag='DERIVED from the SIL numbers: (26.59 - 11.11) g / 0.30 s, assuming the hot and cold relights share '
                                    'the base-window inventory; the author model gives 37.4 g/s cold flow at the 12.5 % lift (A1 relight '
                                    'state, Dyer, Cd 0.70 ASSUMED)',
               P_limits_Pa=P_LIMS, products={k: {kk: vv for kk, vv in v.items()} for k, v in prods.items()})
    # ---- 1. envelope per SIL event
    env = {}
    for ev in SIL:
        st = ev['state']; c = cold[f'{st}|0.125']; x = c['quality']
        for pk_ in (st, 'comb_OF8'):
            prod = prods[pk_]
            for vk, V in HS.V_CH.items():
                bases = {'all_admitted': ev['m_g'] * 1e-3,
                         'retained': (ev['m_g'] - ev['vap_g']) * 1e-3 * (1 - x) + c['vapour_in_chamber_g'][vk] * 1e-3}
                for bk, m in bases.items():
                    for shape in ('tophat', 'exp'):
                        row = dict(m_g=1e3 * m, peaks_bar={f'{t*1e3:g}ms': peak(m, t, shape, V, prod) / 1e5 for t in TAUS},
                                   tau_thr_ms={pl: 1e3 * tau_thr(m, P, V, prod, shape) for pl, P in P_LIMS.items()})
                        env[f"{ev['key']}|{'dec' if pk_ != 'comb_OF8' else 'comb_OF8'}|{vk}|{bk}|{shape}"] = row
        print('envelope', ev['key'], round(time.time() - t0, 1), 's', flush=True)
    res['envelope'] = dict(v=env, tag='SIM 0-D vented chamber (hard_start_v2p4.vented_peak1); inventory reacting as a whole over tau; '
                           'all_admitted = review convention; retained = (admitted - admitted vapour) x (1 - flash quality) + chamber vapour '
                           '(DERIVED mass balance, no drainage); tau_thr = reaction time below which the limit is exceeded')
    # ---- 2. allowable inventory against reaction time
    ma = {}
    for pk_ in ('20C', 'A1_relight', 'comb_OF8'):
        prod = prods[pk_]
        for shape in ('tophat', 'exp'):
            for pl, P in P_LIMS.items():
                vals = {}
                for tau in (2e-3, 5e-3, 1e-2, 2e-2, 3e-2, 5e-2, 1e-1):
                    vals[f'{tau*1e3:g}ms'] = min(1e3 * m_allow(tau, P, V, prod, shape) for V in HS.V_CH.values())
                ma[f'{pk_}|{shape}|{pl}'] = vals
        print('m_allow', pk_, round(time.time() - t0, 1), 's', flush=True)
    res['allowable_inventory_vs_tau_g'] = dict(v=ma, tag='SIM: largest admitted N2O mass [g] whose vented peak stays at or below the '
                                               'limit when it reacts as a whole over tau (minimum over 284.6 / 300.9 cm3); tau is unknown')
    # ---- 3. credible two-component case per SIL event
    cr = {}
    for ev in SIL:
        st = ev['state']; c = cold[f'{st}|0.125']; prod = prods[st]
        flows = {'author_cold_flow': c['mdot_cold_kg_s'], 'SIL_implied_flow': SIL_EXT_FLOW}
        for fk, md in flows.items():
            rows = []
            for vk, V in HS.V_CH.items():
                m_vap = c['vapour_in_chamber_g'][vk] * 1e-3
                for t_res in (0.02, 0.06):
                    m_fast = min(m_vap + md * (1 - c['quality']) * t_res, ev['m_g'] * 1e-3)
                    m_pool = max(ev['m_g'] * 1e-3 - m_fast, 0.0)
                    for q in (0.5e6, 2.0e6, 5.0e6):
                        tau_pool = max(m_pool * H_EV / (q * A_WET), 1e-3)
                        for tf in (1e-3, 5e-3):
                            pk = HS.vented_peak1(m_pool, tau_pool, 'tophat', V, prod, m_fast=m_fast, tau_fast=tf)
                            rows.append(dict(V=vk, t_res_s=t_res, q_W_m2=q, tau_fast_s=tf, m_fast_g=1e3 * m_fast, m_pool_g=1e3 * m_pool,
                                             tau_pool_s=tau_pool, P_peak_bar=pk / 1e5))
            core = [r for r in rows if r['q_W_m2'] <= 2.0e6]
            cr[f"{ev['key']}|{fk}"] = dict(liquid_flow_kg_s=md * (1 - c['quality']), rows=rows,
                                            P_peak_range_q_0p5_2_bar=[min(r['P_peak_bar'] for r in core), max(r['P_peak_bar'] for r in core)],
                                            P_peak_max_q_5_bar=max(r['P_peak_bar'] for r in rows if r['q_W_m2'] == 5.0e6),
                                            m_fast_range_g=[min(r['m_fast_g'] for r in rows), max(r['m_fast_g'] for r in rows)])
        print('credible', ev['key'], round(time.time() - t0, 1), 's', flush=True)
    res['credible_case'] = dict(v=cr, tag='ESTIMATE (DERIVED from ASSUMED inputs as hard_start_v2p4 section 5; q 5 MW/m2 added as a '
                                'bounding sensitivity, about 2.5x the upper assumed value); decomposition products at the event tank state')
    # ---- 4. fuel-assisted fast part
    fa = {}
    pc8 = prods['comb_OF8']
    for ev in SIL:
        st = ev['state']; c = cold[f'{st}|0.125']
        for fk, md in (('author_cold_flow', c['mdot_cold_kg_s']), ('SIL_implied_flow', SIL_EXT_FLOW)):
            for vk, V in HS.V_CH.items():
                for t_res in (0.02, 0.06):
                    m_fast = min(c['vapour_in_chamber_g'][vk] * 1e-3 + md * (1 - c['quality']) * t_res, ev['m_g'] * 1e-3)
                    for tf in (1e-3, 2e-3, 3e-3, 5e-3, 1e-2):
                        fa[f"{ev['key']}|{fk}|{vk}|tres{t_res}|tf{tf*1e3:g}ms"] = dict(
                            m_fast_g=1e3 * m_fast, P_peak_bar=peak(m_fast, tf, 'tophat', V, pc8) / 1e5)
    res['fuel_assisted_fast_part'] = dict(v=fa, tag='ESTIMATE: fast part reacting with fuel vapour at O/F 8 (fuel unlimited), top-hat; '
                                          'applies to a relight into a hot chamber with an ignition delay; slow part omitted')
    print('fuel-assisted done', round(time.time() - t0, 1), 's', flush=True)
    # ---- 5. reduced extension lift (A1 relight state, relight port 32.2 mm)
    tk_lab = 'A1_relight'
    L0 = lifts[f'{tk_lab}|0.125']; c0 = cold[f'{tk_lab}|0.125']
    h0 = L0['lift_m']
    red = {}
    for r in (0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00):
        h = r * h0
        out = dict(lift_ratio_to_12p5pct=r, lift_m=h)
        for eta in (0.85, 0.92):
            tk, Dp = HS.tank_state(tk_lab)
            e = Q.Engine(tk, cfg=dict(eta_cstar=eta))
            e.D[:] = Dp
            s = e.steady(h)
            out[f'lit_eta{eta:.2f}'] = None if s is None else dict(Pc_bar=s['Pc'] / 1e5, mox_g_s=1e3 * s['mox'], F_N=s['F'])
        tk, Dp = HS.tank_state(tk_lab)
        P1, T1 = tk.P, tk.T
        m_guess = HS.mdot_cold(h, P1, T1, 1.3e5)
        cc = HS.cold_chamber(m_guess, T1)
        m1 = HS.mdot_cold(h, P1 - 2.5e5 * (m_guess / 0.25) ** 2, T1, cc['P2_Pa'])
        cc = HS.cold_chamber(m1, T1)
        flow_ratio = m1 / c0['mdot_cold_kg_s']
        V = HS.V_CH['author_284.6cm3']
        m_vap = c0['vapour_in_chamber_g']['author_284.6cm3'] * 1e-3 * cc['P2_Pa'] / c0['P2_Pa']
        out.update(cold_mdot_g_s=1e3 * m1, cold_Pc_bar=cc['P2_Pa'] / 1e5, flow_ratio_to_12p5pct=flow_ratio, quality=cc['quality'])
        fp = {}
        for fk, md in (('author', m1), ('SIL_scaled', SIL_EXT_FLOW * flow_ratio)):
            for t_res in (0.02, 0.06):
                m_fast = m_vap + md * (1 - cc['quality']) * t_res
                fp[f'{fk}|tres{t_res}'] = dict(m_fast_g=1e3 * m_fast,
                                               fuel_OF8_peak_bar={f'{tf*1e3:g}ms': peak(m_fast, tf, 'tophat', V, pc8) / 1e5 for tf in (1e-3, 2e-3, 3e-3, 5e-3)},
                                               dec_peak_bar={f'{tf*1e3:g}ms': peak(m_fast, tf, 'tophat', V, prods[tk_lab]) / 1e5 for tf in (1e-3, 5e-3)})
        out['fast_part'] = fp
        # extension inventory with the extension at this lift (SIL scaling: the extension admits 15.0 g (vapour line) and
        # 15.48 g (liquid line) at the SIL ignition lift over 0.30 s)
        out['SIL_scaled_inventory_g'] = dict(vapour_line=3.38 + (18.38 - 3.38) * flow_ratio, liquid_line=11.11 + (26.59 - 11.11) * flow_ratio)
        red[f'{r:.2f}'] = out
        print('lift', r, json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in out.items() if k != 'fast_part'})[:400], flush=True)
    res['reduced_extension_lift'] = dict(v=red, tag='SIM grain_q1d v2 steady (A1 relight tank state, port 32.2 mm; eta_c* 0.85 / 0.92); '
                                         'DERIVED Dyer cold flow (Cd 0.70) and fast part; inventory scaled from the SIL by the cold-flow ratio')
    # ---- 6. extension length (SIL scaling) and the SIL vapour-delayed light
    ext = {}
    for dt in (0.10, 0.15, 0.20, 0.25, 0.30):
        ext[f'{dt:.2f}'] = dict(abort_at_s=0.35 + dt, vapour_line_g=3.38 + (18.38 - 3.38) * dt / 0.30, liquid_line_g=11.11 + (26.59 - 11.11) * dt / 0.30,
                                margin_to_SIL_light_s=0.35 + dt - 0.499)
    res['extension_length_SIL_scaled'] = dict(v=ext, tag='DERIVED linear scaling of the SIL inventories with the extension length '
                                              '(the SIL extension adds 15.0 g (vapour line) and 15.48 g (liquid line) over 0.30 s); '
                                              'margin to the SIL vapour-delayed light at 0.499 s before the Pc-confirmation persistence (10 ms)')
    # ---- 7. stand burst disc against the SIL inventories (envelope, decomposition 20 C, 284.6 cm3, top-hat)
    bd = {}
    prod = prods['20C']
    for ev in SIL:
        for d_mm in (0.0, 16.0, 20.0, 25.0):
            for tau in (2e-3, 5e-3, 1e-2, 2e-2):
                A = math.pi / 4 * (d_mm * 1e-3) ** 2
                bd[f"{ev['key']}|bd{d_mm:g}mm|tau{tau*1e3:g}ms"] = peak(ev['m_g'] * 1e-3, tau, 'tophat', HS.V_CH['author_284.6cm3'], prod,
                                                                         A_bd=A, P_bd=55e5 if d_mm > 0 else None) / 1e5
    res['burst_disc_bar'] = dict(v=bd, tag='SIM: as hard_start_v2p4 burst_disc_effect_bar, for the SIL inventories (all admitted)')
    fn = os.path.join(d, 'sil_inventory_bound_v2p4.json')
    json.dump(res, open(fn, 'w'), indent=1, default=float)
    print('wrote', fn, round(time.time() - t0, 1), 's')


if __name__ == '__main__':
    main(sys.argv[1])
