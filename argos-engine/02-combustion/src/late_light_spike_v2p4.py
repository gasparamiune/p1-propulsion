"""Late-light spike over the ignition-delay band and the A5 ignition-hold monitor (Combustion v2.4; coordinator item
OI-A5-LATE, 2026-10-13).

Question (coordinator, relaying Electronics SIL v2.9 S6: lights 0.20 and 0.25 s after the lift, inside W, abort HARD_START
because A5 (8.0 bar abs for 5 ms, E1 to the ramp start) fires before the 10 ms light confirmation; plant peaks 26.9 and
28.6 bar abs):
  1. peak Pc and the time above 8 bar abs for a light anywhere in the ignition-delay band, at flight W 0.65 s and stand
     W 0.35 s, pad states 15 / 20 / 25 C (fresh 25 mm port) and the A1 relight state (32.2 mm port) (max and p99);
  2. what A5 protects, and a re-specified A5 (answered in the report text from these numbers);
  3. whether the accepted-inventory peak stays below MEOP 45 bar.
Model (SIM on ASSUMED inputs: the RC-02 credible-case construct of hard_start_v2p4 section 5 and hard_start_multivolume_v2p4
section 3, here with time histories):
  * light at t_L = t_lift + ig after the ignition-lift command (0.2039 mm, the v2.8 default; t_lift 28.7 ms); ig = main
    ignition delay after liquid arrival, band U(0.05, 0.30) s (start_latency_v2p4; ASSUMED, the review's band). A vapour pocket
    ahead of the liquid (PURGE residual 4.8-8.2 cm3) delays t_L but not the liquid inventory at light, so a primed line bounds
    the inventory for a given ig. Bounding rows beyond the band: the latest light whose E2 still falls inside W
    (t_L = W - 18 ms, the SIL light-to-E2 maximum), primed line: flight 0.632 s, stand 0.332 s.
  * inventory at light: Dyer cold flow (Cd 0.70 ASSUMED) over the servo history up to t_L (hard_start_v2p4 functions).
  * at light, three sources into the three-node network (hard_start_multivolume_v2p4.Net, no disc; the stand aft DN32 disc
    opens at 55 bar, above every decomposition peak here (asserted), so flight and stand histories coincide and differ only in
    the admissible t_L):
      fast part: chamber vapour at the cold-flow state (by node volume) + spray in transit (liquid flow x t_res 20 or 60 ms,
      at the head), capped by the inventory, reacting top-hat over tf = 1, 2, 5, 10 or 20 ms;
      pool: the rest of the inventory times a retained fraction f_ret (1 = every admitted gram retained, the RC-02 convention;
      0 = the cold-flow steady state in which the throat passes the admitted two-phase flow: no pool), evaporation-limited at
      q 0.5, 1.0, 1.5 or 2.0 MW/m2 over the port + head wetted area (latent heat 375 kJ/kg), released by node volume;
      the continuing injector flow at the ignition lift, as decomposition products at the head.
    Products: N2O decomposition at the tank temperature (hard_start_multivolume_v2p4.json, Cantera GRI-3.0). Sensitivity: the
    whole network with N2O/ABS products at O/F 8 (fuel-assisted fast part, relight state).
  * measured channel: head node delayed by the 2.3 ms sensor latency (start_latency_v2p4.PC_LAT). E2: rise >= 0.8 bar over the
    pre-light pressure for 10 ms (raw only; the SIL's filtered channel adds 6-8 ms). A5: measured Pc > 8.0 bar abs for 5 ms.
    Hardware comparator: measured gauge Pc through RC 5.28 ms against 31.47 bar g (band 30.90-34.06 bar abs). Firmware abort
    30 bar abs: its persistence is not set, so the continuous time above 30 bar abs is given.
  * the pintle stays at the ignition lift (the A5 phase); the ramp after E2 is not modelled.
Not modelled: combustion roughness, flame spread (a deflagrative light over 10-30 ms is represented only by the tf 10 and 20 ms rows),
heat loss, the torch contribution before light (the baseline is the cold-flow pressure).
usage: python -I late_light_spike_v2p4.py DATA_V2P4_DIR OUT_JSON
"""
from __future__ import annotations
import hashlib, itertools, json, math, os, sys, time
sys.dont_write_bytecode = True
import numpy as np
from scipy.integrate import solve_ivp
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import hard_start_v2p4 as HS
import hard_start_multivolume_v2p4 as MV
import start_latency_v2p4 as SL

H_IGN = 0.2039e-3
DT_OUT = 5e-5
A5_P, A5_T = 8.0e5, 0.005
E2_RISE, E2_T = 0.8e5, 0.010
RC_TAU = 5.28e-3
OVP_G = 31.47e5                       # bar g -> Pa g; abs band below
OVP_ABS_BAND = (30.90e5, 34.06e5)
FW_ABS = 30.0e5
MEOP = 45e5
H_EV = 375e3
L_GRAIN = 0.230
SIL_E2_MAX = 0.018                    # Electronics sil_a1_relight_mc E2 - light max 18 ms
IG_BAND = (0.05, 0.075, 0.10, 0.125, 0.15, 0.175, 0.20, 0.225, 0.25, 0.275, 0.30)
TFS = (1e-3, 2e-3, 5e-3, 10e-3, 20e-3)
TRES = (0.02, 0.06)
POOLS = (('fret0', 0.0, None), ('fret1_q0.5', 1.0, 0.5e6), ('fret1_q1.0', 1.0, 1.0e6), ('fret1_q1.5', 1.0, 1.5e6), ('fret1_q2.0', 1.0, 2.0e6))
ENTR = (('rounded_Cd1.0', 1.0), ('sharp_Cd0.65', 0.65))


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def t_lift():
    return SL.T_CMD + H_IGN / SL.V_PINTLE + 0.010


def admitted(P1, T1, P2, t_L, dt=2e-4):
    """N2O admitted from the lift command to t_L with the pintle held at the ignition lift (kg)."""
    t, H = HS.servo_history(H_IGN, 10.0, dt=dt, t_end=t_L + dt)
    m = np.array([HS.mdot_cold(hh, P1, T1, P2) if hh > 1e-8 else 0.0 for hh in H])
    k = t <= t_L + 1e-12
    trap = getattr(np, 'trapezoid', None) or getattr(np, 'trapz')
    return float(trap(m[k], t[k])), float(m[-1])


class Light:
    def __init__(self, prod, D_port, cd, P0):
        self.V3 = MV.volumes(0.0499, D_port); self.Vs = sum(self.V3)
        self.net = MV.make_net(prod, self.V3, D_port, cd, 'entrance', 'none')
        self.P0 = P0
        self.cp = self.net.cp; self.Thp = self.net.Thp
        self.A_wet = math.pi * D_port * L_GRAIN + math.pi / 4 * 0.054 ** 2

    def run(self, r_inj, m_f, split_f, tf, m_pool, q, t_tail=0.06, t_cap=1.2):
        net = self.net; hs = self.cp * self.Thp
        vs = [v / self.Vs for v in self.V3]
        tau_p = (m_pool * H_EV / (q * self.A_wet)) if (m_pool > 0 and q) else 0.0
        t_end = min(max(tf, tau_p) + t_tail, t_cap)
        y = np.empty(6)
        for i in range(3):
            mi = self.P0 * self.V3[i] / (net.R * 190.0); y[2 * i] = mi; y[2 * i + 1] = mi * net.cv * 190.0
        bounds = sorted({b for b in (tf, tau_p) if 0 < b < t_end} | {t_end})
        T = []; P = []
        a = 0.0
        for b in bounds:
            tm = 0.5 * (a + b)
            rf = m_f / tf if tm < tf else 0.0
            rp = m_pool / tau_p if (tau_p > 0 and tm < tau_p) else 0.0

            def fun(tt, yy, rf=rf, rp=rp):
                d, _ = net.rhs(yy, 0.0, vs)
                src = [r_inj + rf * split_f[0] + rp * vs[0], rf * split_f[1] + rp * vs[1], rf * split_f[2] + rp * vs[2]]
                for i in range(3):
                    d[2 * i] += src[i]; d[2 * i + 1] += src[i] * hs
                return d
            n_out = max(int(round((b - a) / DT_OUT)), 1)
            te = np.linspace(a, b, n_out + 1)
            ms = (min(tf, 1e-3) / 8.0) if a < tf else 1e-3
            sol = solve_ivp(fun, (a, b), y, method='LSODA', t_eval=te, max_step=ms, rtol=1e-6, atol=np.array([1e-10, 1e-4] * 3))
            assert sol.status == 0, sol.message
            Y = sol.y
            Pn = np.array([Y[2 * i] * net.R * (Y[2 * i + 1] / (Y[2 * i] * net.cv)) / self.V3[i] for i in range(3)])
            sl = slice(0 if not T else 1, None)
            T.append(sol.t[sl]); P.append(Pn[:, sl])
            y = Y[:, -1].copy(); a = b
        return np.concatenate(T), np.concatenate(P, axis=1), tau_p


def metrics(t, P, P0):
    ph = P[0]
    k = int(round(SL.PC_LAT / DT_OUT))
    pm = np.concatenate([np.full(k, P0), ph[:-k]])
    out = dict(peak_head_bar=float(ph.max()) / 1e5, peak_aft_bar=float(P[2].max()) / 1e5)

    def first_persist(mask, dur):
        n = int(round(dur / DT_OUT)); run = 0
        for i, m_ in enumerate(mask):
            run = run + 1 if m_ else 0
            if run > n:
                return float(t[i])
        return None

    def above(x, thr):
        m_ = x > thr
        if not m_.any():
            return 0.0, 0.0
        i0 = int(np.argmax(m_)); j = i0
        while j < len(m_) and m_[j]:
            j += 1
        return float(t[min(j, len(t) - 1)] - t[i0]), float(m_.sum() * DT_OUT)
    out['t_E2_s'] = first_persist(pm - P0 >= E2_RISE, E2_T)
    out['t_A5_s'] = first_persist(pm > A5_P, A5_T)
    out['A5_before_E2'] = bool(out['t_A5_s'] is not None and (out['t_E2_s'] is None or out['t_A5_s'] < out['t_E2_s']))
    out['above8_cont_s'], out['above8_total_s'] = above(ph, A5_P)
    out['above8_meas_cont_s'], _ = above(pm, A5_P)
    out['above30_cont_s'], _ = above(ph, FW_ABS)
    out['above45_cont_s'], _ = above(ph, MEOP)
    # hardware comparator: RC on the measured gauge pressure
    a = DT_OUT / (RC_TAU + DT_OUT); f = np.empty_like(pm); acc = P0 - MV.PAMB
    for i, x in enumerate(pm - MV.PAMB):
        acc += a * (x - acc); f[i] = acc
    fpk = float(f.max()) + MV.PAMB
    out['comparator_filtered_peak_abs_bar'] = fpk / 1e5
    out['comparator_trip_nominal'] = bool(fpk - MV.PAMB >= OVP_G)
    out['comparator_trip_low_band'] = bool(fpk >= OVP_ABS_BAND[0])
    out['comparator_trip_high_band'] = bool(fpk >= OVP_ABS_BAND[1])
    out['P_end_bar'] = float(ph[-1]) / 1e5
    return out


def main(d, out_f):
    t0w = time.time()
    J = json.load(open(os.path.join(d, 'hard_start_v2p4.json')))
    M = json.load(open(os.path.join(d, 'hard_start_multivolume_v2p4.json')))
    cold = J['cold_flow_at_ignition_lift']['v']; lifts = J['ignition_lifts']['v']
    inv_ref = M['inventory_vs_W_v2p8_lift']['v']
    tl = t_lift()
    states = {'15C': dict(prod=None, T=288.15, D_port=0.025), '20C': dict(prod='dec_20C', D_port=0.025),
              '25C': dict(prod=None, T=298.15, D_port=0.025), 'A1_relight': dict(prod='dec_A1', D_port=0.032213)}
    prods_extra = {}
    rows = {}
    traces = {}
    TRACE_KEYS = {('A1_relight', 'sharp_Cd0.65', 'flight_latest', 1e-3, 0.06, 'fret1_q2.0'),
                  ('A1_relight', 'rounded_Cd1.0', 'flight_latest', 1e-3, 0.06, 'fret1_q2.0'),
                  ('20C', 'rounded_Cd1.0', '0.300', 5e-3, 0.06, 'fret1_q2.0'),
                  ('20C', 'rounded_Cd1.0', 'SIL_tL0.200', 5e-3, 0.06, 'fret0'),
                  ('20C', 'rounded_Cd1.0', 'SIL_tL0.250', 5e-3, 0.06, 'fret1_q1.0'),
                  ('A1_relight', 'rounded_Cd1.0', '0.300', 10e-3, 0.02, 'fret1_q1.0')}
    for st, sd in states.items():
        L = lifts[f'{st}|0.125']; c = cold[f'{st}|0.125']
        P1, T1, P2 = L['P_tank_Pa'], L['T_tank_K'], c['P2_Pa']
        if sd['prod']:
            prod = M['products'][sd['prod']]
        else:
            prod = prods_extra[st] = HS.products('dec', sd['T'])          # Cantera GRI-3.0, as hard_start_v2p4
        r_inj = HS.mdot_cold(H_IGN, P1, T1, P2)
        assert abs(1e3 * r_inj - inv_ref[st]['cold_flow_g_s_at_0.2039mm']) < 1e-6
        x_liq = c['liquid_flow_kg_s'] / c['mdot_cold_kg_s']           # liquid fraction after the flash (cold-flow state)
        Vs_ref = 300.9e-6
        cases = [(f'{ig:.3f}', tl + ig) for ig in IG_BAND] + [('flight_latest', 0.65 - SIL_E2_MAX), ('stand_latest', 0.35 - SIL_E2_MAX)]
        if st == '20C':
            cases += [('SIL_tL0.200', 0.200), ('SIL_tL0.250', 0.250)]
        for lab_e, cd in ENTR:
            lt = Light(prod, sd['D_port'], cd, P2)
            m_vap = c['vapour_in_chamber_g']['reviewer_300.9cm3'] * 1e-3 * lt.Vs / Vs_ref
            for lab_t, t_L in cases:
                m_inv, _ = admitted(P1, T1, P2, t_L)
                for tf, tres in itertools.product(TFS, TRES):
                    m_s = r_inj * x_liq * tres
                    m_f = min(m_vap + m_s, m_inv)
                    sp = [(m_vap * lt.V3[0] / lt.Vs + m_s) / (m_vap + m_s), m_vap * lt.V3[1] / lt.Vs / (m_vap + m_s), m_vap * lt.V3[2] / lt.Vs / (m_vap + m_s)]
                    for lab_p, fr, q in POOLS:
                        m_pool = max(m_inv - m_f, 0.0) * fr
                        t, P, tau_p = lt.run(r_inj, m_f, sp, tf, m_pool, q)
                        mt = metrics(t, P, P2)
                        assert mt['peak_head_bar'] < 55.0 and mt['peak_aft_bar'] < 55.0, (st, lab_e, lab_t, tf, tres, lab_p, mt['peak_head_bar'])
                        key = f'{st}|{lab_e}|{lab_t}|tf{tf*1e3:.0f}ms|tres{tres}|{lab_p}'
                        rows[key] = dict(t_L_s=t_L, inventory_g=1e3 * m_inv, m_fast_g=1e3 * m_f, m_pool_g=1e3 * m_pool, tau_pool_s=tau_p, **mt)
                        if (st, lab_e, lab_t, tf, tres, lab_p) in TRACE_KEYS:
                            k = int(round(1e-4 / DT_OUT))
                            traces[key] = dict(t_from_light_s=[round(float(x), 5) for x in t[::k]],
                                               P_head_abs_bar=[round(float(x) / 1e5, 4) for x in P[0][::k]],
                                               P_aft_abs_bar=[round(float(x) / 1e5, 4) for x in P[2][::k]])
            print(st, lab_e, 'done', round(time.time() - t0w, 1), 's', flush=True)
    # ---- fuel-assisted sensitivity (relight): N2O/ABS products at O/F 8 for every source (conservative for the pool)
    fa = {}
    st = 'A1_relight'; L = lifts[f'{st}|0.125']; c = cold[f'{st}|0.125']
    P1, T1, P2 = L['P_tank_Pa'], L['T_tank_K'], c['P2_Pa']
    prod = M['products']['comb_OF8']; mpk = prod['mass_per_kg_N2O']
    r_inj = HS.mdot_cold(H_IGN, P1, T1, P2); x_liq = c['liquid_flow_kg_s'] / c['mdot_cold_kg_s']
    for lab_e, cd in ENTR:
        lt = Light(prod, 0.032213, cd, P2)
        m_vap = c['vapour_in_chamber_g']['reviewer_300.9cm3'] * 1e-3 * lt.Vs / 300.9e-6
        for ig in (0.20, 0.30):
            m_inv, _ = admitted(P1, T1, P2, tl + ig)
            for tf, tres in itertools.product((1e-3, 5e-3, 10e-3), TRES):
                m_s = r_inj * x_liq * tres; m_f = min(m_vap + m_s, m_inv)
                sp = [(m_vap * lt.V3[0] / lt.Vs + m_s) / (m_vap + m_s), m_vap * lt.V3[1] / lt.Vs / (m_vap + m_s), m_vap * lt.V3[2] / lt.Vs / (m_vap + m_s)]
                for lab_p, fr, q in (POOLS[0], POOLS[4]):
                    m_pool = max(m_inv - m_f, 0.0) * fr
                    t, P, tau_p = lt.run(r_inj * mpk, m_f * mpk, sp, tf, m_pool * mpk, q)
                    mt = metrics(t, P, P2)
                    fa[f'{st}|{lab_e}|{ig:.3f}|tf{tf*1e3:.0f}ms|tres{tres}|{lab_p}'] = dict(inventory_g=1e3 * m_inv, m_fast_g=1e3 * m_f, **mt)
    print('fuel-assisted done', round(time.time() - t0w, 1), 's', flush=True)
    # ---- summaries
    def summ(sel):
        out = {}
        for m_ in ('peak_head_bar', 'above8_cont_s', 'above8_meas_cont_s', 'above30_cont_s', 'above45_cont_s', 'comparator_filtered_peak_abs_bar'):
            v = np.array([r[m_] for r in sel])
            out[m_] = dict(min=float(v.min()), p50=float(np.percentile(v, 50)), p99=float(np.percentile(v, 99)), max=float(v.max()))
        out['n'] = len(sel)
        out['A5_before_E2_fraction'] = float(np.mean([r['A5_before_E2'] for r in sel]))
        out['A5_trips_fraction'] = float(np.mean([r['t_A5_s'] is not None for r in sel]))
        out['comparator_trip_nominal_fraction'] = float(np.mean([r['comparator_trip_nominal'] for r in sel]))
        out['comparator_trip_low_band_fraction'] = float(np.mean([r['comparator_trip_low_band'] for r in sel]))
        e2 = [r['t_E2_s'] for r in sel if r['t_E2_s'] is not None]
        out['t_E2_from_light_s'] = [min(e2), max(e2)] if e2 else None
        a5 = [r['t_A5_s'] for r in sel if r['t_A5_s'] is not None]
        out['t_A5_from_light_s'] = [min(a5), max(a5)] if a5 else None
        out['inventory_g'] = [min(r['inventory_g'] for r in sel), max(r['inventory_g'] for r in sel)]
        return out
    band_labs = {f'{ig:.3f}' for ig in IG_BAND}
    S = {}
    for st in states:
        for lab_p, _, _ in POOLS:
            for tf in TFS:
                sel = [r for k, r in rows.items() if k.startswith(st + '|') and k.split('|')[2] in band_labs and f'|tf{tf*1e3:.0f}ms|' in k and k.endswith(lab_p)]
                S[f'band|{st}|tf{tf*1e3:.0f}ms|{lab_p}'] = summ(sel)
                for lat in ('flight_latest', 'stand_latest'):
                    sel = [r for k, r in rows.items() if k.startswith(st + '|') and k.split('|')[2] == lat and f'|tf{tf*1e3:.0f}ms|' in k and k.endswith(lab_p)]
                    S[f'{lat}|{st}|tf{tf*1e3:.0f}ms|{lab_p}'] = summ(sel)
        sel = [r for k, r in rows.items() if k.startswith(st + '|') and k.split('|')[2] in band_labs]
        S[f'band|{st}|all'] = summ(sel)
        sel = [r for k, r in rows.items() if k.startswith(st + '|') and k.split('|')[2] in band_labs | {'flight_latest'}]
        S[f'flight_W0.65|{st}|all'] = summ(sel)
        sel = [r for k, r in rows.items() if k.startswith(st + '|') and k.split('|')[2] in band_labs | {'stand_latest'}]
        S[f'stand_W0.35|{st}|all'] = summ(sel)
    sil = {k: dict(peak_head_bar=r['peak_head_bar'], above8_cont_s=r['above8_cont_s'], t_A5_s=r['t_A5_s'], t_E2_s=r['t_E2_s'])
           for k, r in rows.items() if '|SIL_tL' in k and '|rounded' in k}
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/late_light_spike_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               request='coordinator OI-A5-LATE (Electronics SIL v2.9 S6 late lights inside W abort HARD_START on A5)',
               inputs={'hard_start_v2p4.json': sha16(os.path.join(d, 'hard_start_v2p4.json')),
                       'hard_start_multivolume_v2p4.json': sha16(os.path.join(d, 'hard_start_multivolume_v2p4.json'))},
               constants=dict(h_ign_m=H_IGN, t_lift_s=tl, ig_band_s=list(IG_BAND), tf_s=list(TFS), t_res_s=list(TRES), pools=[p[0] for p in POOLS],
                              A5=dict(P_abs_Pa=A5_P, persist_s=A5_T), E2=dict(rise_Pa=E2_RISE, persist_s=E2_T), Pc_latency_s=SL.PC_LAT,
                              comparator=dict(RC_tau_s=RC_TAU, threshold_Pa_g=OVP_G, abs_band_Pa=list(OVP_ABS_BAND)), firmware_abort_abs_Pa=FW_ABS,
                              SIL_E2_after_light_max_s=SIL_E2_MAX, latent_heat_J_kg=H_EV),
               products_computed_here=prods_extra, summary=S, sil_comparison_20C_rounded=sil, rows=rows, fuel_assisted_relight=fa, traces=traces,
               tags=dict(model='SIM three-node vented network on ASSUMED inputs (ig band, tf, t_res, q, f_ret): an ESTIMATE, not acceptance evidence',
                         inventory='DERIVED Dyer, Cd 0.70 ASSUMED', products='DERIVED Cantera GRI-3.0',
                         latency='DERIVED electronics.json v1 (2.3 ms); comparator RC and band: Electronics v2.8/v2.9 (DESIGN/DERIVED)'))
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    for k, v in S.items():
        if k.startswith('band|') or k.startswith('flight_latest|A1') or k.startswith('stand_latest|20C'):
            print(k, 'peak p99/max %.1f/%.1f' % (v['peak_head_bar']['p99'], v['peak_head_bar']['max']),
                  '>8 bar p99/max %.3f/%.3f' % (v['above8_cont_s']['p99'], v['above8_cont_s']['max']),
                  '>30 max %.4f' % v['above30_cont_s']['max'], 'A5<E2 %.2f' % v['A5_before_E2_fraction'],
                  'cmp nom %.2f lo %.2f' % (v['comparator_trip_nominal_fraction'], v['comparator_trip_low_band_fraction']), 'inv', [round(x, 1) for x in v['inventory_g']])
    print('SIL', json.dumps(sil, default=float)[:1500])
    print('wrote', out_f, sha16(out_f), round(time.time() - t0w, 1), 's')


if __name__ == '__main__':
    main(*sys.argv[1:3])
