"""REV-COMB-2 reviewer model (independent implementation; the author's code is not imported).

Purpose: first-order check of the Combustion v2.4 late-light peaks (pad 15/20/25 C, A1 relight) and of the fuel-assisted
relight case FA-1 (peak, time above MEOP 45 bar, time above proof 67.5 bar), with an O/F and burn-time sweep.

Construct (kept identical to the author's ASSUMED construct so the numbers are comparable; the construct itself is not
validated here): fast part = chamber vapour (by node volume) + spray in transit (liquid flow x t_res, at the head), top-hat
over tf; pool = (inventory - fast part) x f_ret, evaporation-limited at q over the port + head wetted area (375 kJ/kg),
by node volume; continuing injector flow at the 0.2039 mm ignition lift reacting at the head; initial node gas inert at the
cold-flow chamber pressure.  Three nodes (head, port, aft); head->port orifice Cd x A_port; port->aft orifice either
50 x A_port (the author's 'entrance' network) or 1.0 x A_port (reviewer variant); aft->ambient throat 147.9 mm2, Cd 1.0.

Independent parts: (1) thermochemistry: each node is a gas in chemical equilibrium at its own (u, rho), from Cantera
TV-equilibrium tables (GRI-3.0 species set, elemental composition per propellant mix), instead of a calorically perfect
product gas with a kappa fitted at 40 kg/m3; (2) reactant enthalpy from CoolProp (phase-specific) mapped onto the Cantera
ideal-gas reference; (3) own ODE network and metrics.
Enthalpy bases: 'author' = every source as saturated liquid at the tank temperature (the author's basis);
'phase' = chamber vapour and pool as saturated vapour at the chamber temperature (the pool's latent heat is supplied by the
wall), spray as saturated liquid at the chamber temperature, continuing flow as tank liquid (isenthalpic throttling).
ABS: the project's ABS_TYP card (C6.06 H6.43 N0.24 per 82.63 g, hf +476.4 kJ/kg, solid 298 K) by elemental surrogate.
Tag: SIM on ASSUMED inputs.  Agreement with the author shows only that the construct repeats; it is not physical evidence.
usage: python -I r2_late_light.py HARD_START_V2P4_JSON LATE_LIGHT_V2P4_JSON OUT_JSON
"""
import hashlib, json, math, sys, time
import numpy as np
import cantera as ct
import CoolProp.CoolProp as CP
from scipy.integrate import solve_ivp


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


HSJ, LLJ, OUT = sys.argv[1:4]
assert sha16(HSJ) == '1bdcf295ce6f7413', sha16(HSJ)
assert sha16(LLJ) == '57fce738164fd571', sha16(LLJ)
t0 = time.time()
L_PRE, L_GRAIN, L_POST, D_CH, V_CONV, D_PRE = 0.030, 0.230, 0.040, 0.0539, 28.26e-6, 0.0499
AT = math.pi / 4 * 0.013724 ** 2
PAMB = 101325.0
H_EV = 375e3
MEOP, PROOF = 45e5, 67.5e5
W_N2O = 44.0128e-3
ABS = dict(C=6.06, H=6.43, N=0.24, M=82.63e-3, hf=476.4e3)
gas = ct.Solution('gri30.yaml')


def vols(D_port):
    return np.array([math.pi / 4 * D_PRE ** 2 * L_PRE, math.pi / 4 * D_port ** 2 * L_GRAIN, math.pi / 4 * D_CH ** 2 * L_POST + V_CONV])


def elem_X(OF):
    nC = nH = 0.0
    nN, nO = 2 / W_N2O, 1 / W_N2O
    if OF:
        u = (1.0 / OF) / ABS['M']
        nC, nH, nN = ABS['C'] * u, ABS['H'] * u, nN + ABS['N'] * u
    X = {'N2': nN / 2}
    o1 = nO - nC
    w = min(nH / 2, o1); h2 = nH / 2 - w; o2 = o1 - w
    c2 = min(nC, max(o2, 0.0))
    if nC > 0:
        X['CO'] = nC - c2
        X['CO2'] = c2
    if w > 0:
        X['H2O'] = w
    if h2 > 0:
        X['H2'] = h2
    if o2 - c2 > 0:
        X['O2'] = (o2 - c2) / 2
    return {k: v for k, v in X.items() if v > 0}


TG = np.arange(200.0, 5201.0, 40.0)
LRG = np.linspace(math.log(0.15), math.log(120.0), 34)


class Table:
    def __init__(self, OF):
        X = elem_X(OF)
        nr, nt = len(LRG), len(TG)
        self.U = np.empty((nr, nt)); self.R = np.empty((nr, nt)); self.G = np.empty((nr, nt))
        for j, lr in enumerate(LRG):
            rho = math.exp(lr)
            gas.TDX = 700.0, rho, X
            gas.equilibrate('TV')
            Y700 = gas.Y.copy()
            for i, T in enumerate(TG):
                if T < 700.0:
                    gas.TDY = T, rho, Y700
                else:
                    gas.TDX = T, rho, X
                    gas.equilibrate('TV')
                self.U[j, i] = gas.int_energy_mass
                self.R[j, i] = ct.gas_constant / gas.mean_molecular_weight
                self.G[j, i] = gas.cp_mass / gas.cv_mass
            assert np.all(np.diff(self.U[j]) > 0)
        self.dT = TG[1] - TG[0]; self.dl = LRG[1] - LRG[0]

    def state(self, u, rho):
        """vectorised over nodes: (u J/kg, rho kg/m3) -> T, P, R, gamma_frozen"""
        x = (np.log(rho) - LRG[0]) / self.dl
        j = np.clip(np.floor(x).astype(int), 0, len(LRG) - 2); w = np.clip(x - j, 0.0, 1.0)
        T = np.empty_like(u)
        for k in range(len(u)):
            Ta = np.interp(u[k], self.U[j[k]], TG); Tb = np.interp(u[k], self.U[j[k] + 1], TG)
            T[k] = (1 - w[k]) * Ta + w[k] * Tb
        y = (T - TG[0]) / self.dT
        i = np.clip(np.floor(y).astype(int), 0, len(TG) - 2); v = np.clip(y - i, 0.0, 1.0)

        def bil(A):
            return ((1 - w) * ((1 - v) * A[j, i] + v * A[j, i + 1]) + w * ((1 - v) * A[j + 1, i] + v * A[j + 1, i + 1]))
        R = bil(self.R); G = bil(self.G)
        return T, rho * R * T, R, G


def h_reactant_n2o(phase, T):
    """N2O enthalpy on the Cantera ideal-gas (formation) reference, J/kg: Cantera ideal gas at T minus CoolProp departure."""
    gas.TPX = T, 1e5, 'N2O:1'
    h_ig = gas.enthalpy_mass
    h_ig_cp = CP.PropsSI('H', 'T', T, 'P', 5.0, 'N2O')
    h_cp = CP.PropsSI('H', 'T', T, 'Q', 0 if phase == 'liq' else 1, 'N2O')
    return h_ig - (h_ig_cp - h_cp)


def h_mix(h_n2o, OF):
    return h_n2o if not OF else (OF * h_n2o + ABS['hf']) / (1.0 + OF)


def orifice(A, Pu, Tu, Ru, Gu, Pd):
    pr = Pd / Pu
    crit = (2 / (Gu + 1)) ** (Gu / (Gu - 1))
    if pr <= crit:
        return A * Pu * math.sqrt(Gu / (Ru * Tu)) * (2 / (Gu + 1)) ** ((Gu + 1) / (2 * (Gu - 1)))
    return A * Pu * math.sqrt(max(2 * Gu / ((Gu - 1) * Ru * Tu) * (pr ** (2 / Gu) - pr ** ((Gu + 1) / Gu)), 0.0))


def run(tab, V, A_in, A_out, P0, T0, src_fast, h_fast, tf, r_cont, h_cont, r_pool, h_pool, t_end=0.025, dt_out=2e-5):
    """src_fast: kg per node over tf (top-hat).  Returns t, P (3 x n)."""
    u0 = np.interp(T0, TG, tab.U[0])          # inert initial gas (frozen low-T composition), uniform
    # initial density from P0 = rho R T at T0 (R at the low-density row)
    R0 = tab.R[0, 0]
    rho0 = P0 / (R0 * T0)
    m0 = rho0 * V
    y0 = np.concatenate([[m0[k], m0[k] * u0] for k in range(3)])
    vs = V / V.sum()

    def fun(t, y):
        m = np.maximum(y[0::2], 1e-12); E = y[1::2]
        rho = m / V; u = E / m
        T, P, R, G = tab.state(u, rho)
        h = u + P / rho
        dm = np.zeros(3); dE = np.zeros(3)
        for a, b, A in ((0, 1, A_in), (1, 2, A_out)):
            if P[a] >= P[b]:
                f = orifice(A, P[a], T[a], R[a], G[a], P[b]); hs = h[a]
            else:
                f = -orifice(A, P[b], T[b], R[b], G[b], P[a]); hs = h[b]
            dm[a] -= f; dm[b] += f; dE[a] -= f * hs; dE[b] += f * hs
        if P[2] > PAMB:
            f = orifice(AT, P[2], T[2], R[2], G[2], PAMB); dm[2] -= f; dE[2] -= f * h[2]
        if t < tf:
            s = src_fast / tf
            dm += s; dE += s * h_fast
        dm[0] += r_cont; dE[0] += r_cont * h_cont
        dm += r_pool * vs; dE += r_pool * vs * h_pool
        out = np.empty(6); out[0::2] = dm; out[1::2] = dE
        return out
    T_, P_ = [], []
    y = y0; a = 0.0
    for b, ms in ((tf, tf / 10), (t_end, 2e-4)):
        te = np.arange(a, b, dt_out)
        te = np.append(te[te < b - 1e-12], b)
        sol = solve_ivp(fun, (a, b), y, method='LSODA', t_eval=te, max_step=ms, rtol=1e-6,
                        atol=np.array([1e-9, 1e-3] * 3))
        assert sol.status == 0, sol.message
        m = sol.y[0::2]; E = sol.y[1::2]
        Pn = np.empty_like(m)
        for k in range(m.shape[1]):
            Pn[:, k] = tab.state(E[:, k] / m[:, k], m[:, k] / V)[1]
        sl = slice(1, None) if T_ else slice(None)
        T_.append(sol.t[sl]); P_.append(Pn[:, sl])
        y = sol.y[:, -1]; a = b
    return np.concatenate(T_), np.concatenate(P_, axis=1), y0


def above(t, p, thr):
    mk = p > thr
    if not mk.any():
        return 0.0
    i0 = int(np.argmax(mk)); j = i0
    while j < len(mk) and mk[j]:
        j += 1
    return float(t[min(j, len(t) - 1)] - t[i0])


def metrics(t, P, P0):
    ph = P[0]
    return dict(peak_head_bar=float(ph.max()) / 1e5, peak_aft_bar=float(P[2].max()) / 1e5, t_peak_ms=1e3 * float(t[int(np.argmax(ph))]),
                above30_ms=1e3 * above(t, ph, 30e5), above45_ms=1e3 * above(t, ph, MEOP), above67p5_ms=1e3 * above(t, ph, PROOF),
                impulse_above_P0_bar_ms=float(np.trapezoid(ph - P0, t)) * 1e3 / 1e5, P_end_bar=float(ph[-1]) / 1e5)


# ------------------------------------------------------------------------------------------------- inputs (author data)
HJ = json.load(open(HSJ)); LJ = json.load(open(LLJ))
cold = HJ['cold_flow_at_ignition_lift']['v']; lifts = HJ['ignition_lifts']['v']
STATES = {'15C': 0.025, '20C': 0.025, '25C': 0.025, 'A1_relight': 0.032213}
inp = {}
for st, Dp in STATES.items():
    c = cold[st + '|0.125']; L = lifts[st + '|0.125']
    V = vols(Dp)
    row = LJ['rows'][f'{st}|sharp_Cd0.65|stand_latest|tf1ms|tres0.06|fret1_q2.0']
    inp[st] = dict(D_port=Dp, V=V, P0=c['P2_Pa'], T_ch=c['T_K'], T_tank=L['T_tank_K'],
                   x_liq=c['liquid_flow_kg_s'] / c['mdot_cold_kg_s'],
                   m_vap=c['vapour_in_chamber_g']['reviewer_300.9cm3'] * 1e-3 * V.sum() / 300.9e-6,
                   inventory=row['inventory_g'] * 1e-3, author_m_fast=row['m_fast_g'] * 1e-3)
# r_inj at the 0.2039 mm lift: the author's inventory table value (Dyer, Cd 0.70 ASSUMED) - an input here
# the cold flow at 0.2039 mm is in hard_start_multivolume_v2p4.json; recover it from the author's fast part instead:
# m_fast = m_vap + r_inj * x_liq * 0.06  ->  r_inj = (m_fast - m_vap) / (x_liq * 0.06)  (checked against the table below)
for st, d in inp.items():
    d['r_inj'] = (d['author_m_fast'] - d['m_vap']) / (d['x_liq'] * 0.06)
R_INJ_TABLE = {'15C': 35.2741e-3, '20C': 36.8028e-3, '25C': 38.1398e-3, 'A1_relight': 34.8076e-3}   # multivolume JSON (read by the reviewer)
for st, d in inp.items():
    assert abs(d['r_inj'] - R_INJ_TABLE[st]) / R_INJ_TABLE[st] < 2e-3, (st, d['r_inj'])
    d['r_inj'] = R_INJ_TABLE[st]

# ------------------------------------------------------------------------------------------------- tables
tabs = {None: Table(None)}
OFS = (4.0, 5.0, 6.0, 7.0, 8.0, 10.0, 12.0)
for of in OFS:
    tabs[of] = Table(of)
t_tab = time.time() - t0
res = dict(script='reviews/combustion/r2/r2_late_light.py', script_sha16=sha16(__file__), inputs=dict(hard_start_v2p4=sha16(HSJ), late_light_spike_v2p4=sha16(LLJ)),
           construct='author ASSUMED construct (see docstring); reviewer thermochemistry and network', table_build_s=t_tab, decomposition={}, fa1={}, closed_volume={})


# closed-volume bound (no venting, instantaneous fast part, inert initial gas) per state/basis/OF
def closed(tab, V, P0, T0, m_f, h_f):
    u0 = np.interp(T0, TG, tab.U[0]); rho0 = P0 / (tab.R[0, 0] * T0); m0 = rho0 * V.sum()
    m = m0 + m_f; u = (m0 * u0 + m_f * h_f) / m
    T, P, _, _ = tab.state(np.array([u]), np.array([m / V.sum()]))
    return float(P[0]) / 1e5, float(T[0])


# enthalpies
H = {}
for st, d in inp.items():
    H[st] = dict(liq_tank=h_reactant_n2o('liq', d['T_tank']), vap_ch=h_reactant_n2o('vap', d['T_ch']), liq_ch=h_reactant_n2o('liq', d['T_ch']))
res['enthalpy_J_kg'] = H


def case(st, OF, entr_cd, exit_mode, tres, tf, pool, basis):
    d = inp[st]; V = d['V']; Ap = math.pi / 4 * d['D_port'] ** 2
    A_in = entr_cd * Ap; A_out = 50 * Ap if exit_mode == 'author50A' else 1.0 * Ap
    mpk = 1.0 + (1.0 / OF if OF else 0.0)
    m_s = d['r_inj'] * d['x_liq'] * tres
    m_f = min(d['m_vap'] + m_s, d['inventory'])
    hv = H[st]
    if basis == 'author':
        hf_vap = hf_s = h_c = h_p = hv['liq_tank']
    else:
        hf_vap, hf_s, h_c, h_p = hv['vap_ch'], hv['liq_ch'], hv['liq_tank'], hv['vap_ch']
    # fast part per node: vapour by volume, spray at the head; one mixed enthalpy for the fast stream per node
    mv = d['m_vap'] * V / V.sum()
    fast = mv.copy(); fast[0] += m_s
    Efast = mv * h_mix(hf_vap, OF); Efast[0] += m_s * h_mix(hf_s, OF)
    hfast = Efast / fast
    A_wet = math.pi * d['D_port'] * L_GRAIN + math.pi / 4 * 0.054 ** 2
    if pool:
        m_pool = max(d['inventory'] - m_f, 0.0); r_pool = pool * A_wet / H_EV
    else:
        m_pool = 0.0; r_pool = 0.0
    tab = tabs[OF]
    t, P, y0 = run(tab, V, A_in, A_out, d['P0'], max(d['T_ch'], 200.0), fast * mpk, hfast, tf,
                   d['r_inj'] * mpk, h_mix(h_c, OF), r_pool * mpk, h_mix(h_p, OF))
    mt = metrics(t, P, d['P0'])
    mt.update(m_fast_g=1e3 * m_f, fuel_g=1e3 * m_f * (mpk - 1), pool_rate_g_s=1e3 * r_pool * mpk, m_pool_g=1e3 * m_pool)
    pcv, tcv = closed(tab, V, d['P0'], max(d['T_ch'], 200.0), m_f * mpk, float(np.sum(hfast * fast) / np.sum(fast)))
    mt.update(closed_volume_fast_part_bar=pcv, closed_volume_T_K=tcv)
    return mt


# A: decomposition, reproduce the author's maxima (tf 1 ms, t_res 0.06) and bases / exit variants
for st in STATES:
    for lab_e, cd in (('rounded_Cd1.0', 1.0), ('sharp_Cd0.65', 0.65)):
        for ex in ('author50A', 'A1.0'):
            for pool, lp in ((2.0e6, 'fret1_q2.0'), (0.0, 'fret0')):
                for basis in ('author', 'phase'):
                    if ex == 'A1.0' and (lp == 'fret0' or basis == 'phase'):
                        continue
                    k = f'{st}|{lab_e}|{ex}|tf1ms|tres0.06|{lp}|{basis}'
                    res['decomposition'][k] = case(st, None, cd, ex, 0.06, 1e-3, pool, basis)
                    a = LJ['rows'].get(f'{st}|{lab_e}|stand_latest|tf1ms|tres0.06|{lp}')
                    res['decomposition'][k]['author_peak_head_bar'] = a['peak_head_bar'] if a else None
    print(st, 'decomposition done', round(time.time() - t0, 1), 's', flush=True)
# B: FA-1 at the A1 relight state, O/F x tf sweep, sharp and rounded entrance, t_res 0.06, pool q 2.0 (and fret0 for O/F 8)
TFS = (0.5e-3, 1e-3, 1.5e-3, 2e-3, 3e-3, 4e-3, 5e-3, 7e-3, 10e-3)
for of in OFS:
    for lab_e, cd in (('rounded_Cd1.0', 1.0), ('sharp_Cd0.65', 0.65)):
        for tf in TFS:
            k = f'A1_relight|OF{of:g}|{lab_e}|author50A|tf{tf * 1e3:g}ms|tres0.06|fret1_q2.0|author'
            res['fa1'][k] = case('A1_relight', of, cd, 'author50A', 0.06, tf, 2.0e6, 'author')
    print('FA OF', of, 'done', round(time.time() - t0, 1), 's', flush=True)
for lab_e, cd in (('rounded_Cd1.0', 1.0), ('sharp_Cd0.65', 0.65)):
    for tres in (0.02, 0.06):
        for tf in (1e-3, 5e-3):
            k = f'A1_relight|OF8|{lab_e}|author50A|tf{tf * 1e3:g}ms|tres{tres}|fret0|author'
            res['fa1'][k] = case('A1_relight', 8.0, cd, 'author50A', tres, tf, 0.0, 'author')
            a = [r for kk, r in LJ['fuel_assisted_relight'].items() if kk.startswith(f'A1_relight|{lab_e}|0.300|tf{tf * 1e3:.0f}ms|tres{tres}|fret0')]
            res['fa1'][k]['author_peak_head_bar'] = a[0]['peak_head_bar'] if a else None
            res['fa1'][k]['author_above45_ms'] = 1e3 * a[0]['above45_cont_s'] if a else None
        k = f'A1_relight|OF8|{lab_e}|A1.0|tf1ms|tres0.06|fret1_q2.0|author'
        res['fa1'][k] = case('A1_relight', 8.0, cd, 'A1.0', 0.06, 1e-3, 2.0e6, 'author')
res['run_s'] = time.time() - t0
json.dump(res, open(OUT, 'w'), indent=1)
print('== decomposition (peak head bar: reviewer / author; closed-volume fast part)')
for k, r in res['decomposition'].items():
    print(f"{k:60s} {r['peak_head_bar']:6.2f} / {r['author_peak_head_bar'] if r['author_peak_head_bar'] else float('nan'):6.2f}  aft {r['peak_aft_bar']:6.2f}"
          f"  >45 {r['above45_ms']:.2f} ms  >30 {r['above30_ms']:.2f} ms  Pcv {r['closed_volume_fast_part_bar']:.1f}")
print('== FA-1')
for k, r in res['fa1'].items():
    print(f"{k:72s} pk {r['peak_head_bar']:6.2f} (auth {r.get('author_peak_head_bar') or float('nan'):5.1f}) >45 {r['above45_ms']:.2f} ms"
          f" (auth {r.get('author_above45_ms') or float('nan'):.2f}) >67.5 {r['above67p5_ms']:.2f} ms  Pcv {r['closed_volume_fast_part_bar']:.1f}"
          f"  fuel {r['fuel_g']:.3f} g  I {r['impulse_above_P0_bar_ms']:.1f} bar ms")
print('wrote', OUT, 'run', round(res['run_s'], 1), 's')
