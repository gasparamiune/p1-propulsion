"""FA-1 envelope at the A1 relight (Combustion v2.4a; REV-COMB-2 R2-03 and R2-11; LEAD CHANGELOG line 172 (2)).

Extends late_light_spike_v2p4.py (v2.4: fuel-assisted sensitivity at O/F 8 only, tf 1/5/10 ms) with an O/F x tf loop on the
same three-node vented construct (its Light class, admitted() and t_lift() are imported unchanged):
  * O/F 4, 5, 6, 8, 10, 12 (the lead's grid) plus O/F 3 and 3.5 (beyond the grid: the closed-volume pressure of the fast part
    peaks at O/F 3.5-4, so these rows show whether a fast part richer than the grid raises the peak);
  * tf 1..7 ms in 1 ms steps (top-hat reaction of the fast part);
  * t_res 0.02 / 0.06 s (spray in transit);
  * pool none (f_ret 0) / f_ret 1 at q 2 MW/m2;
  * A1 relight state (32.2 mm port; hard_start_v2p4 'A1_relight|0.125' tank state; ignition lift 0.2039 mm; light at
    t_lift + 0.30 s, the v2.4 FA-1 basis; inventory checks at t_lift + 0.05 s and at the flight-latest light 0.632 s);
  * port entrance rounded Cd 1.0 (DESIGN, REQUIRED by CHANGELOG line 160 (4)) and sharp Cd 0.65 (bracket);
  * initial node gas: 'vapour_once' = 5 % of the v2.4 inert gas (BASELINE, R2-11: the chamber vapour reacts in the fast part
    and is no longer also present as inert gas; 5 % is the reviewer's reading and a numerical floor) and 'as_written' = the
    v2.4 construct (upper bracket of this model).
Construct changes from v2.4, each stated and tested:
  (1) R2-11 initial gas as above;
  (2) pool with fuel: products rate (q A_wet / h_ev) x (1 + 1/OF) over the N2O evaporation time m_pool h_ev / (q A_wet)
      (v2.4 FA-1 passed m_pool (1 + 1/OF) at q, i.e. rate q A_wet / h_ev over a time x (1 + 1/OF); the new form is the
      reviewer's and adds the fuel to the evaporated N2O);
  (3) products at the A1 tank temperature 286.70 K (v2.4 FA-1: 293.15 K).
  Regression check: the v2.4 FA-1 rows (O/F 8 products from hard_start_multivolume_v2p4.json, v2.4 pool form, initial gas
  x 1.0) are re-run through this script and must reproduce late_light_spike_v2p4.json to 1e-6 bar (asserted).
Per case: head and aft pressure histories (0.1 ms grid, 0-25 ms) and metrics: peak, time to peak, 10-90 % rise time, total
and longest continuous time above 45 / 67.5 / 90 bar abs, impulse above P0 over 25 ms (positive part), thrust and SDOF
equivalent loads.
Thrust: F = Cf x P_aft x A_t with (a) Cf 1.25 / 1.35 (ASSUMED band, REV-COMB-2 section 4 2b and the interim 1.8 kN of line
172 (2)) and (b) the quasi-steady ideal nozzle (eps 2.0, frozen gamma of the products, pa 101.325 kPa) x eta_cf 0.95 /
0.975 (DERIVED on the quasi-steady assumption; eta_cf band of CHANGELOG line 170).
SDOF: undamped single-degree-of-freedom equivalent static load k x_max for natural periods 0.5-5 ms on the thrust history and
the dynamic load factor of the head pressure for periods 0.04-1 ms; exact piecewise-linear recurrence. For comparing load
histories with the interim load (1.8 kN rectangle for 4 ms); not a structural result.
Fuel-vapour inventory at light: MISSING datum (not modelled, not measured). Section 'fuel_vapour_inventory' gives a
first-order bound from the coast thermal state and the closed-volume pressure of the fast part against O/F (Cantera
GRI-3.0, ABS-solid basis as in the construct, and pre-vaporised styrene as a sensitivity).
Tags: SIM (three-node vented network on ASSUMED inputs: fast part, t_res, tf, f_ret, q, O/F); products DERIVED (Cantera
GRI-3.0); thrust DERIVED/ASSUMED as stated; fuel bound DERIVED on ASSUMED and LITERATURE (as recalled, TO-VERIFY) inputs.
None of it is physical evidence.
usage: python -I fa1_envelope_v2p4a.py DATA_V2P4_DIR OUT_JSON OUT_CSV
"""
from __future__ import annotations
import csv, hashlib, itertools, json, math, os, sys, time
sys.dont_write_bytecode = True
import numpy as np
from scipy.optimize import brentq
from scipy.special import erfcx
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import late_light_spike_v2p4 as LL
HS, MV, SL = LL.HS, LL.MV, LL.SL


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


EXPECT_DATA = {'hard_start_v2p4.json': '1bdcf295ce6f7413', 'hard_start_multivolume_v2p4.json': 'a804970397b24857',
               'late_light_spike_v2p4.json': '57fce738164fd571'}
EXPECT_SRC = {'late_light_spike_v2p4.py': 'e8aad73cb6972cb3', 'hard_start_v2p4.py': '00a966bb1572d075',
              'hard_start_multivolume_v2p4.py': 'dd8aadf76f59113e', 'start_latency_v2p4.py': '989ccd9a004b2cb9'}

OFS_GRID = (4.0, 5.0, 6.0, 8.0, 10.0, 12.0)          # LEAD line 172 (2)
OFS_EXT = (3.0, 3.5)                                 # beyond the grid (closed-volume maximum at O/F 3.5-4)
TFS = tuple(i * 1e-3 for i in range(1, 8))
TRES = (0.02, 0.06)
POOLS = (('none', 0.0, None), ('q2.0', 1.0, 2.0e6))
INITS = (('vapour_once', 0.05), ('as_written', 1.0))
ENTR = LL.ENTR                                        # (('rounded_Cd1.0', 1.0), ('sharp_Cd0.65', 0.65))
IG = 0.30
D_PORT = 0.032213
P_LEVELS = (('45', 45e5), ('67p5', 67.5e5), ('90', 90e5))
T_IMP = 0.025
DT_HIST = 1e-4
CF_BAND = (1.25, 1.35)                                # ASSUMED (REV-COMB-2 section 4 2b; interim load line 172 (2))
ETA_CF = (0.95, 0.975)                                # CHANGELOG line 170 (1) band
EPS = 2.0                                             # combustion.json decisions.expansion_ratio
PA = 101325.0
T_SDOF_F = (0.5e-3, 1e-3, 2e-3, 3e-3, 4e-3, 5e-3)     # thrust-path parts (gimbal, mount, linkage: 1-5 ms per REV-COMB-2)
T_SDOF_P = (0.04e-3, 0.1e-3, 0.25e-3, 0.5e-3, 1e-3)   # shell breathing mode ~0.04 ms (REV-COMB-2), closures, bolts
T_SDOF_WIN = 0.030
INTERIM_F, INTERIM_TD = 1800.0, 0.004                 # LEAD line 172 (2): 1.8 kN for 4 ms
INTERIM_P = 90e5                                      # LEAD line 172 (2): quasi-static 90 bar abs at head and aft


# --------------------------------------------------------------------------------------------- helpers
def cf_ideal(Pc, g, eps=EPS, pa=PA):
    """Quasi-steady ideal nozzle thrust coefficient (frozen gamma), vectorised in Pc [Pa]."""
    Me = brentq(lambda M: (1 / M) * ((2 / (g + 1)) * (1 + (g - 1) / 2 * M * M)) ** ((g + 1) / (2 * (g - 1))) - eps, 1.0001, 10.0)
    pe = (1 + (g - 1) / 2 * Me * Me) ** (-g / (g - 1))
    gam = math.sqrt(g) * (2 / (g + 1)) ** ((g + 1) / (2 * (g - 1)))
    cmom = gam * math.sqrt(2 * g / (g - 1) * (1 - pe ** ((g - 1) / g)))
    return cmom + (pe - pa / np.asarray(Pc)) * eps, pe, cmom


def sdof_max(F, dt, periods):
    """Max of k*x(t) of undamped SDOF oscillators at rest under the piecewise-linear history F (exact recurrence)."""
    w = 2 * math.pi / np.asarray(periods); c, s = np.cos(w * dt), np.sin(w * dt)
    u = np.zeros_like(w); v = np.zeros_like(w); umax = np.zeros_like(w)
    for i in range(len(F) - 1):
        sl = (F[i + 1] - F[i]) / dt
        A = u - F[i]; B = (v - sl) / w
        u, v = A * c + B * s + F[i + 1], -A * w * s + B * w * c + sl
        umax = np.maximum(umax, u)
    return umax


def above(t, x, thr):
    m_ = x > thr
    if not m_.any():
        return 0.0, 0.0
    dt = t[1] - t[0]
    best = run = 0
    for b in m_:
        run = run + 1 if b else 0
        best = max(best, run)
    return float(m_.sum() * dt), float(best * dt)


def rise(t, x, P0):
    k = int(np.argmax(x)); pk = x[k]
    lo, hi = P0 + 0.1 * (pk - P0), P0 + 0.9 * (pk - P0)
    i10 = int(np.argmax(x[:k + 1] >= lo)); i90 = int(np.argmax(x[:k + 1] >= hi))
    return float(t[k]), float(t[i90] - t[i10])


def metrics(t, P, P0, prod, A_t):
    out = {}
    w = t <= T_IMP + 1e-12
    trap = getattr(np, 'trapezoid', None) or getattr(np, 'trapz')
    for lab, i in (('head', 0), ('aft', 2)):
        x = P[i]
        out[f'peak_{lab}_bar'] = float(x.max()) / 1e5
        tp, tr = rise(t, x, P0)
        out[f't_peak_{lab}_ms'] = 1e3 * tp
        out[f'rise_10_90_{lab}_ms'] = 1e3 * tr
        for nm, thr in P_LEVELS:
            tot, cont = above(t, x, thr)
            out[f'above{nm}_{lab}_total_ms'] = 1e3 * tot
            out[f'above{nm}_{lab}_cont_ms'] = 1e3 * cont
        out[f'impulse_above_P0_25ms_{lab}_bar_ms'] = float(trap(np.maximum(x[w] - P0, 0.0), t[w])) / 1e5 * 1e3
        out[f'P_at_25ms_{lab}_bar'] = float(np.interp(T_IMP, t, x)) / 1e5
    out['aft_over_head_peak'] = out['peak_aft_bar'] / out['peak_head_bar']
    out['P_end_bar'] = float(P[0][-1]) / 1e5
    out['t_end_ms'] = 1e3 * float(t[-1])
    # thrust
    pa = P[2]
    cfq, _, _ = cf_ideal(np.maximum(pa, 1.2e5), prod['gamma_frozen'])
    F = {f'Cf{cf:.2f}': cf * pa * A_t for cf in CF_BAND}
    F.update({f'QSx{e:.3f}': np.maximum(e * cfq * pa * A_t, 0.0) for e in ETA_CF})
    for k, f in F.items():
        out[f'F_peak_{k}_N'] = float(f.max())
        out[f'F_impulse_25ms_{k}_Ns'] = float(trap(f[w], t[w]))
        out[f'F_above1kN_{k}_ms'] = 1e3 * above(t, f, 1000.0)[0]
    out['Cf_QS_at_peak'] = float(cf_ideal(pa.max(), prod['gamma_frozen'])[0])
    ws = t <= T_SDOF_WIN + 1e-12; dt = float(t[1] - t[0])
    for k in ('Cf1.35', 'QSx0.975'):
        f0 = float(F[k][0])                              # pre-light static thrust; dynamic part from rest
        out[f'F_sdof_{k}_N'] = [f0 + float(x) for x in sdof_max(F[k][ws] - f0, dt, T_SDOF_F)]
    pg = np.maximum(P[0][ws] - PA, 0.0)
    out['P_head_DLF'] = [float(x) for x in sdof_max(pg, dt, T_SDOF_P) / pg.max()]
    pg = np.maximum(P[2][ws] - PA, 0.0)
    out['P_aft_DLF'] = [float(x) for x in sdof_max(pg, dt, T_SDOF_P) / pg.max()]
    return out, F


def hist(t, x, scale=1e5, nd=3):
    g = np.arange(0.0, T_IMP + 1e-9, DT_HIST)
    return [round(float(v), nd) for v in np.interp(g, t, x) / scale]


# --------------------------------------------------------------------------------------------- fuel-vapour bound
def fuel_bound(V3, cold, m_fast_by_tres, T_tank):
    """First-order bound of the fuel available to the fast part at an A1 relight light (DERIVED on ASSUMED/LITERATURE)."""
    Vs = sum(V3)
    A_port = math.pi * D_PORT * LL.L_GRAIN
    A_wet = A_port + math.pi / 4 * 0.054 ** 2
    kap, rho, cf = 1.2e-7, 1000.0, 1500.0               # grain_q1d kappa_s (LITERATURE-UNVERIFIED), rho_f (ASSUMED); soakback_v2 c
    dT_burn = 350.0                                      # soakback_v2 grain_zone surface-to-bulk (ASSUMED)
    r_band = {'0.50': 0.5e-3, '0.70': 0.70e-3, '1.00': 1.0e-3}   # 0.70 DERIVED from DC-A1dispp99 grain run at MECO
    t_coast = 18.67                                      # A1 MECO->relight coast (CHANGELOG line 106)
    T0s = (288.15, 308.15)                               # grain bulk at relight (ASSUMED band)
    tau_dec = 0.05                                       # grain_q1d post-shutdown pyrolysis decay (ASSUMED)
    Lg = (1.5e6, 3.5e6)                                  # ABS heat of gasification (LITERATURE as recalled, TO-VERIFY)
    sty = dict(A=7.14016, B=1574.51, C=224.09, M=0.10415, Lv=0.421e6, cp_l=1750.0, hf_gas=1.4153e6, hf_liq=0.9966e6)  # as recalled, TO-VERIFY
    q = 2.0e6
    m_torch = 0.0548e-3                                  # combustion.json igniter.torch_sizing per 0.6 s start (DERIVED)
    Qv = cold['mdot_cold_kg_s'] * cold['quality'] / cold['rho_vapour']   # cold-flow vapour volume flow (DERIVED)
    tau_f = Vs / Qv
    T_p = 290.0 + dT_burn                                # pyrolysis surface temperature consistent with soakback_v2 (ASSUMED)
    out = dict(status='MISSING: the fuel-vapour (and aerosol/film) inventory in the warm 32.2 mm port at the moment of light '
                      'after the 18.67 s A1 coast is not modelled and not measured. Below: first-order bounds only.',
               inputs=dict(A_port_m2=A_port, A_wet_m2=A_wet, V_chamber_m3=Vs, kappa_m2_s=kap, rho_kg_m3=rho, c_J_kgK=cf,
                           dT_surface_at_MECO_K=dT_burn, r_MECO_mm_s=list(r_band), t_coast_s=t_coast, T_bulk_K=list(T0s),
                           tau_decay_s=tau_dec, L_g_ABS_J_kg=list(Lg), styrene=sty, q_W_m2=q, m_torch_propane_per_start_kg=m_torch,
                           cold_flow_vapour_m3_s=Qv, flush_tau_s=tau_f, T_pyrolysis_K=T_p),
               tags=dict(r_MECO='DERIVED: DC-A1dispp99-S230 grain run, mf 16.7 g/s at D 33.2 mm -> 0.70 mm/s; band 0.5-1.0 ASSUMED',
                         kappa='LITERATURE-UNVERIFIED (grain_q1d)', rho_c_dT='ASSUMED (soakback_v2 grain_zone: 1000 x 1500, 350 K)',
                         t_coast='CHANGELOG line 106 (A1 coast 18.67 s)', T_bulk='ASSUMED 15-35 C', tau_decay='ASSUMED (grain_q1d)',
                         L_g='LITERATURE as recalled, TO-VERIFY', styrene='LITERATURE as recalled (Antoine mmHg/C; hf gas 147.4 kJ/mol, '
                         'liquid 103.8 kJ/mol; Lv 43.9 kJ/mol), TO-VERIFY; styrene used as the volatile proxy of ABS pyrolysate (ASSUMED)',
                         q='ASSUMED (the construct pool flux, upper value)', torch='DERIVED combustion.json igniter.torch_sizing',
                         flush='DERIVED hard_start_v2p4 cold flow at the A1 ignition lift; well-mixed dilution (conservative vs plug flow); '
                               'the head-end purge vents overboard (no chamber flush credited)'))
    terms = {}
    for rl, r in r_band.items():
        dl = kap / r
        Q2 = rho * cf * dT_burn * dl                     # stored heat in the thermal layer at MECO [J/m2]
        m_dec = rho * A_port * r * tau_dec               # post-MECO pyrolysis by the decay construct
        m_en = Q2 * A_port / Lg[0]                       # energy bound (all stored heat gasifies at the low L_g)
        a = math.sqrt(kap * t_coast) / dl
        dTs = dT_burn * float(erfcx(a))                  # adiabatic surface, exact for an exponential initial profile
        Tw = [T0 + dTs for T0 in T0s]
        msat = []
        for T in Tw:
            p = 133.322 * 10 ** (sty['A'] - sty['B'] / (T - 273.15 + sty['C']))
            msat.append(p * sty['M'] * Vs / (8.314462 * T))
        terms[rl] = dict(thermal_layer_mm=1e3 * dl, stored_heat_kJ_m2=Q2 / 1e3, m_post_MECO_decay_g=1e3 * m_dec,
                         m_post_MECO_energy_bound_g=1e3 * m_en, m_post_MECO_bound_g=1e3 * max(m_dec, m_en),
                         T_wall_at_relight_K=Tw, m_sat_styrene_in_chamber_g=[1e3 * x for x in msat])
    flash = q * A_wet / (sty['Lv'] + sty['cp_l'] * 100.0)              # condensed-film flash rate [kg/s]
    gas_solid = q * A_wet / Lg[0]                                       # solid ABS gasification after heat-up [kg/s]
    T_w_max = max(max(v['T_wall_at_relight_K']) for v in terms.values())
    T_w_min = min(min(v['T_wall_at_relight_K']) for v in terms.values())
    # t_heat = (pi/4) k rho c (dT/q)^2 with k = kappa rho c
    t_heat = [math.pi / 4 * (kap * rho * cf) * (rho * cf) * ((T_p - Tw_) / q) ** 2 for Tw_ in (T_w_max, T_w_min)]
    m_post_hi = max(v['m_post_MECO_bound_g'] for v in terms.values()) * 1e-3
    m_post_70 = terms['0.70']['m_post_MECO_bound_g'] * 1e-3
    rows = {}
    for tres, m_n in m_fast_by_tres.items():
        for ig in (0.05, 0.10, 0.20, 0.30):
            Rf = math.exp(-ig / tau_f)
            for tf in TFS:
                for lab, mp in (('r0.70', m_post_70), ('r_band_max', m_post_hi)):
                    susp = mp * Rf                                   # all post-MECO pyrolysate suspended (vapour/aerosol), flushed
                    film = min(mp, flash * tf)                       # all of it as a wall film (not flushed), flash-limited
                    solid = gas_solid * max(tf - t_heat[0], 0.0)     # solid grain after its heat-up time (hottest wall)
                    mfu = m_torch + max(susp, film) + solid
                    rows[f'tres{tres}|ig{ig:.2f}|tf{tf*1e3:.0f}ms|{lab}'] = dict(
                        m_N2O_fast_g=1e3 * m_n, R_flush=Rf, fuel_suspended_g=1e3 * susp, fuel_film_flash_g=1e3 * film,
                        fuel_solid_g=1e3 * solid, fuel_torch_g=1e3 * m_torch, fuel_upper_g=1e3 * mfu, OF_min=m_n / mfu)
    of_min = min(r['OF_min'] for r in rows.values())
    late = [r['OF_min'] for k, r in rows.items() if '|ig0.30|' in k]
    early = [r['OF_min'] for k, r in rows.items() if '|ig0.05|' in k]
    tf1 = [r['OF_min'] for k, r in rows.items() if '|tf1ms|' in k]
    out.update(terms_by_r_MECO=terms, film_flash_rate_g_ms=flash, solid_gasification_rate_after_heatup_g_ms=gas_solid,
               solid_heat_up_time_s=dict(hottest_wall=t_heat[0], coldest_wall=t_heat[1]), rows=rows,
               summary=dict(OF_min_all=of_min, OF_min_light_at_ig0p30=min(late), OF_min_light_at_ig0p05=min(early),
                            OF_min_tf1ms=min(tf1)))
    return out


def products_styrene(T_tank, OF, hf=1.4153e6, P_hp=45e5, rho_uv=40.0):
    """As hard_start_v2p4.products('comb') but with pre-vaporised styrene (C8H8, hf gas +147.4 kJ/mol, LITERATURE as
    recalled, TO-VERIFY) as the fuel: the sensitivity for a fast part fuelled by coast pyrolysate instead of solid ABS."""
    import cantera as ct
    _, h_n2o, _ = HS._reactants('dec', T_tank, None)
    X = {'N2O': OF * 104.15 / 44.013, 'C2H2': 4.0}
    h_mix = (OF * h_n2o + hf) / (1.0 + OF)
    g = HS._eq(X, h_mix, P=P_hp)
    T_hp = g.T; R = ct.gas_constant / g.mean_molecular_weight; gam = g.cp_mass / g.cv_mass
    G = math.sqrt(gam) * (2 / (gam + 1)) ** ((gam + 1) / (2 * (gam - 1)))
    cstar = math.sqrt(R * T_hp) / G; MW = g.mean_molecular_weight
    g = HS._eq(X, h_mix, v=1.0 / rho_uv)
    return dict(kind='comb_styrene_gas', OF=OF, T_tank_K=T_tank, T_HP_K=T_hp, R=R, MW=MW, gamma_frozen=gam, cstar_th_m_s=cstar,
                T_UV_K=g.T, kappa=g.T / T_hp, P_UV_at_rho_Pa=g.P, rho_uv=rho_uv, mass_per_kg_N2O=1.0 + 1.0 / OF)


def closed_volume_vs_OF(T_tank, Vs, m_n2o):
    """Closed-volume (UV) equilibrium pressure of the fast part alone, ABS-solid basis (the construct) and pre-vaporised
    styrene (gas / liquid) as the fuel (sensitivity)."""
    res = {}
    for OF in (1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 8.0, 10.0, 12.0):
        P, T = HS.cantera_cv('comb', m_n2o, Vs, T_tank=T_tank, OF=OF)
        row = dict(ABS_solid_P_bar=P / 1e5, ABS_solid_T_K=T)
        _, h_n2o, _ = HS._reactants('dec', T_tank, None)       # liquid-basis N2O enthalpy (Cantera frame), as the construct
        for lab, hf in (('styrene_gas', 1.4153e6), ('styrene_liq', 0.9966e6)):
            X = {'N2O': OF * 104.15 / 44.013, 'C2H2': 4.0}
            h = (OF * h_n2o + hf) / (1.0 + OF)
            g = HS._eq(X, h, v=Vs / (m_n2o * (1.0 + 1.0 / OF)))
            row[f'{lab}_P_bar'] = g.P / 1e5; row[f'{lab}_T_K'] = g.T
        res[f'{OF:g}'] = row
    return res


# --------------------------------------------------------------------------------------------- main
def main(d, out_f, out_csv):
    t0w = time.time()
    for f, h in EXPECT_DATA.items():
        assert sha16(os.path.join(d, f)) == h, (f, sha16(os.path.join(d, f)))
    for f, h in EXPECT_SRC.items():
        assert sha16(os.path.join(HERE, f)) == h, (f, sha16(os.path.join(HERE, f)))
    J = json.load(open(os.path.join(d, 'hard_start_v2p4.json')))
    M = json.load(open(os.path.join(d, 'hard_start_multivolume_v2p4.json')))
    LJ = json.load(open(os.path.join(d, 'late_light_spike_v2p4.json')))
    cold = J['cold_flow_at_ignition_lift']['v']['A1_relight|0.125']; L = J['ignition_lifts']['v']['A1_relight|0.125']
    P1, T1, P2 = L['P_tank_Pa'], L['T_tank_K'], cold['P2_Pa']
    r_inj = HS.mdot_cold(LL.H_IGN, P1, T1, P2)
    x_liq = cold['liquid_flow_kg_s'] / cold['mdot_cold_kg_s']
    tl = LL.t_lift()
    A_t = HS.AT
    V3 = MV.volumes(0.0499, D_PORT); Vs = sum(V3)
    m_vap = cold['vapour_in_chamber_g']['reviewer_300.9cm3'] * 1e-3 * Vs / 300.9e-6
    inv = {lab: LL.admitted(P1, T1, P2, tl + ig)[0] for lab, ig in (('ig0.30', IG), ('ig0.05', 0.05), ('flight_latest', 0.65 - LL.SIL_E2_MAX))}

    def fast(tres, m_inv):
        m_s = r_inj * x_liq * tres
        m_f = min(m_vap + m_s, m_inv)
        sp = [(m_vap * V3[0] / Vs + m_s) / (m_vap + m_s), m_vap * V3[1] / Vs / (m_vap + m_s), m_vap * V3[2] / Vs / (m_vap + m_s)]
        return m_s, m_f, sp

    # ---- (0) regression check against v2.4 (same code path, v2.4 inputs and construct)
    prod8 = M['products']['comb_OF8']; mpk8 = prod8['mass_per_kg_N2O']
    reg = {}
    for lab_e, cd in ENTR:
        lt = LL.Light(prod8, D_PORT, cd, P2)
        for ig, tf, tres, (lab_p, fr, q) in ((0.30, 1e-3, 0.06, LL.POOLS[4]), (0.30, 1e-3, 0.02, LL.POOLS[0]),
                                             (0.20, 5e-3, 0.06, LL.POOLS[4]), (0.20, 10e-3, 0.06, LL.POOLS[0])):
            m_inv, _ = LL.admitted(P1, T1, P2, tl + ig)
            m_s, m_f, sp = fast(tres, m_inv)
            m_pool = max(m_inv - m_f, 0.0) * fr
            t, P, _ = lt.run(r_inj * mpk8, m_f * mpk8, sp, tf, m_pool * mpk8, q)
            mt = LL.metrics(t, P, P2)
            key = f'A1_relight|{lab_e}|{ig:.3f}|tf{tf*1e3:.0f}ms|tres{tres}|{lab_p}'
            ref = LJ['fuel_assisted_relight'][key]
            reg[key] = dict(v2p4_peak_head_bar=ref['peak_head_bar'], rerun_peak_head_bar=mt['peak_head_bar'],
                            v2p4_peak_aft_bar=ref['peak_aft_bar'], rerun_peak_aft_bar=mt['peak_aft_bar'],
                            v2p4_above45_cont_s=ref['above45_cont_s'], rerun_above45_cont_s=mt['above45_cont_s'])
            assert abs(ref['peak_head_bar'] - mt['peak_head_bar']) < 1e-6 and abs(ref['peak_aft_bar'] - mt['peak_aft_bar']) < 1e-6, (key, ref['peak_head_bar'], mt['peak_head_bar'])
    print('regression v2.4 reproduced', round(time.time() - t0w, 1), 's', flush=True)

    # ---- (1) products at the A1 tank temperature
    prods = {OF: HS.products('comb', T1, OF=OF) for OF in OFS_EXT + OFS_GRID}
    print('products', round(time.time() - t0w, 1), 's', flush=True)

    # ---- (2) envelope grid
    cases = {}; Fstore = {}
    m_inv = inv['ig0.30']
    for (lab_i, fi), (lab_e, cd), OF in itertools.product(INITS, ENTR, OFS_EXT + OFS_GRID):
        prod = prods[OF]; mpk = prod['mass_per_kg_N2O']
        lt = LL.Light(prod, D_PORT, cd, fi * P2)
        for tres, tf, (lab_p, fr, q) in itertools.product(TRES, TFS, POOLS):
            m_s, m_f, sp = fast(tres, m_inv)
            m_pool = max(m_inv - m_f, 0.0) * fr
            t, P, tau_p = lt.run(r_inj * mpk, m_f * mpk, sp, tf, m_pool * mpk, (q * mpk) if q else None)
            mt, F = metrics(t, P, P2, prod, A_t)
            key = f'{lab_i}|{lab_e}|OF{OF:g}|tf{tf*1e3:.0f}ms|tres{tres}|pool_{lab_p}'
            cases[key] = dict(OF=OF, tf_ms=tf * 1e3, t_res_s=tres, pool=lab_p, init=lab_i, entrance=lab_e,
                              m_fast_N2O_g=1e3 * m_f, m_fuel_fast_g=1e3 * m_f / OF, m_pool_N2O_g=1e3 * m_pool, tau_pool_s=tau_p,
                              **mt, P_head_hist_bar=hist(t, P[0]), P_aft_hist_bar=hist(t, P[2]))
            Fstore[key] = (t, F)
        print(lab_i, lab_e, OF, 'done', round(time.time() - t0w, 1), 's', flush=True)

    # ---- (3) inventory checks: early light (ig 0.05) and flight-latest light (0.632 s) on the governing rows
    inv_chk = {}
    for lab_inv in ('ig0.05', 'flight_latest'):
        for (lab_i, fi), (lab_e, cd), OF in itertools.product(INITS, ENTR, (3.5, 4.0)):
            prod = prods[OF]; mpk = prod['mass_per_kg_N2O']
            lt = LL.Light(prod, D_PORT, cd, fi * P2)
            for tf in (1e-3, 3e-3):
                m_s, m_f, sp = fast(0.06, inv[lab_inv])
                m_pool = max(inv[lab_inv] - m_f, 0.0)
                t, P, tau_p = lt.run(r_inj * mpk, m_f * mpk, sp, tf, m_pool * mpk, 2.0e6 * mpk if m_pool > 0 else None)
                mt, _ = metrics(t, P, P2, prod, A_t)
                base = cases[f'{lab_i}|{lab_e}|OF{OF:g}|tf{tf*1e3:.0f}ms|tres0.06|pool_q2.0']
                inv_chk[f'{lab_inv}|{lab_i}|{lab_e}|OF{OF:g}|tf{tf*1e3:.0f}ms|tres0.06|pool_q2.0'] = dict(
                    inventory_g=1e3 * inv[lab_inv], m_fast_N2O_g=1e3 * m_f, m_pool_N2O_g=1e3 * m_pool,
                    peak_head_bar=mt['peak_head_bar'], base_ig0p30_peak_head_bar=base['peak_head_bar'],
                    impulse_25ms_head_bar_ms=mt['impulse_above_P0_25ms_head_bar_ms'],
                    base_ig0p30_impulse_25ms_head_bar_ms=base['impulse_above_P0_25ms_head_bar_ms'],
                    above45_head_total_ms=mt['above45_head_total_ms'], base_above45_head_total_ms=base['above45_head_total_ms'])
    print('inventory checks', round(time.time() - t0w, 1), 's', flush=True)

    # ---- (3b) fuel-basis sensitivity: pre-vaporised styrene instead of solid ABS on the governing rows
    fsens = {}
    for OF in (3.5, 4.0, 5.0):
        prs = products_styrene(T1, OF); mpk = prs['mass_per_kg_N2O']
        for (lab_i, fi), (lab_e, cd) in itertools.product(INITS, ENTR):
            lt = LL.Light(prs, D_PORT, cd, fi * P2)
            for tf in (1e-3, 2e-3):
                m_s, m_f, sp = fast(0.06, m_inv)
                m_pool = max(m_inv - m_f, 0.0)
                t, P, tau_p = lt.run(r_inj * mpk, m_f * mpk, sp, tf, m_pool * mpk, 2.0e6 * mpk)
                mt, _ = metrics(t, P, P2, prs, A_t)
                key = f'{lab_i}|{lab_e}|OF{OF:g}|tf{tf*1e3:.0f}ms|tres0.06|pool_q2.0'
                b = cases[key]
                fsens[key] = dict(peak_head_bar=mt['peak_head_bar'], peak_aft_bar=mt['peak_aft_bar'], ABS_peak_head_bar=b['peak_head_bar'],
                                  ratio=mt['peak_head_bar'] / b['peak_head_bar'], above45_head_total_ms=mt['above45_head_total_ms'],
                                  above67p5_head_total_ms=mt['above67p5_head_total_ms'], above90_head_total_ms=mt['above90_head_total_ms'],
                                  F_peak_QS0975_N=mt['F_peak_QSx0.975_N'], P_head_DLF=mt['P_head_DLF'], products=prs)
    print('fuel-basis sensitivity', round(time.time() - t0w, 1), 's', flush=True)

    # ---- (4) envelope summaries
    def env(sel):
        if not sel:
            return None
        o = {}
        for m_ in ('peak_head_bar', 'peak_aft_bar', 'above45_head_total_ms', 'above45_aft_total_ms', 'above67p5_head_total_ms',
                   'above67p5_aft_total_ms', 'above90_head_total_ms', 'above90_aft_total_ms', 'above45_head_cont_ms',
                   'impulse_above_P0_25ms_head_bar_ms', 'impulse_above_P0_25ms_aft_bar_ms', 'F_peak_Cf1.35_N', 'F_peak_QSx0.975_N',
                   'F_impulse_25ms_QSx0.975_Ns', 'F_impulse_25ms_Cf1.35_Ns'):
            k = max(sel, key=lambda kk: cases[kk][m_])
            o[m_] = dict(max=cases[k][m_], case=k)
        ah = [cases[k]['aft_over_head_peak'] for k in sel]
        o['aft_over_head_peak'] = [min(ah), max(ah)]
        kpk = o['peak_head_bar']['case']
        o['at_max_head_peak'] = {m_: cases[kpk][m_] for m_ in ('t_peak_head_ms', 'rise_10_90_head_ms', 'peak_aft_bar',
                                                                'above45_head_total_ms', 'above67p5_head_total_ms',
                                                                'impulse_above_P0_25ms_head_bar_ms')}
        o['F_sdof_QSx0.975_N_max_by_period'] = [max(cases[k]['F_sdof_QSx0.975_N'][j] for k in sel) for j in range(len(T_SDOF_F))]
        o['F_sdof_Cf1.35_N_max_by_period'] = [max(cases[k]['F_sdof_Cf1.35_N'][j] for k in sel) for j in range(len(T_SDOF_F))]
        o['P_head_DLF_max_by_period'] = [max(cases[k]['P_head_DLF'][j] for k in sel) for j in range(len(T_SDOF_P))]
        for nd in ('head', 'aft'):
            eq = []
            for j in range(len(T_SDOF_P)):
                kk = max(sel, key=lambda x: PA / 1e5 + cases[x][f'P_{nd}_DLF'][j] * (cases[x][f'peak_{nd}_bar'] - PA / 1e5))
                eq.append(dict(P_equiv_static_abs_bar=PA / 1e5 + cases[kk][f'P_{nd}_DLF'][j] * (cases[kk][f'peak_{nd}_bar'] - PA / 1e5),
                               DLF=cases[kk][f'P_{nd}_DLF'][j], case=kk))
            o[f'P_{nd}_equiv_static_by_period'] = eq
        o['n'] = len(sel)
        return o
    keys = list(cases)
    S = {}
    for lab_i, _ in INITS:
        sel_i = [k for k in keys if cases[k]['init'] == lab_i]
        S[f'{lab_i}|grid_OF4-12|all'] = env([k for k in sel_i if cases[k]['OF'] in OFS_GRID])
        S[f'{lab_i}|incl_OF3-3.5|all'] = env(sel_i)
        for lab_e, _ in ENTR:
            S[f'{lab_i}|grid_OF4-12|{lab_e}'] = env([k for k in sel_i if cases[k]['OF'] in OFS_GRID and cases[k]['entrance'] == lab_e])
        for OF in OFS_EXT + OFS_GRID:
            S[f'{lab_i}|OF{OF:g}'] = env([k for k in sel_i if cases[k]['OF'] == OF])
            for tf in TFS:
                S[f'{lab_i}|OF{OF:g}|tf{tf*1e3:.0f}ms'] = env([k for k in sel_i if cases[k]['OF'] == OF and abs(cases[k]['tf_ms'] - tf * 1e3) < 1e-9])
    S['both|grid_OF4-12|all'] = env([k for k in keys if cases[k]['OF'] in OFS_GRID])
    S['both|incl_OF3-3.5|all'] = env(keys)
    # interim-load comparison
    tt = np.arange(0.0, T_SDOF_WIN + 1e-12, LL.DT_OUT)
    Frect = np.where(tt < INTERIM_TD, INTERIM_F, 0.0); Frect[0] = 0.0
    rect_sdof = [float(x) for x in sdof_max(Frect, LL.DT_OUT, T_SDOF_F)]
    interim = dict(pressure_quasi_static_bar=INTERIM_P / 1e5, thrust_rect_N=INTERIM_F, thrust_rect_ms=INTERIM_TD * 1e3,
                   thrust_rect_sdof_N=rect_sdof, sdof_periods_ms=[1e3 * x for x in T_SDOF_F])
    for lab in ('both|grid_OF4-12|all', 'both|incl_OF3-3.5|all'):
        e = S[lab]
        interim[f'{lab}|head_peak_vs_90bar'] = e['peak_head_bar']['max'] / 90.0
        interim[f'{lab}|aft_peak_vs_90bar'] = e['peak_aft_bar']['max'] / 90.0
        interim[f'{lab}|sdof_QS0.975_over_rect'] = [a / b for a, b in zip(e['F_sdof_QSx0.975_N_max_by_period'], rect_sdof)]
        interim[f'{lab}|sdof_Cf1.35_over_rect'] = [a / b for a, b in zip(e['F_sdof_Cf1.35_N_max_by_period'], rect_sdof)]
        interim[f'{lab}|F_peak_QS0.975_vs_1.8kN'] = e['F_peak_QSx0.975_N']['max'] / INTERIM_F
        interim[f'{lab}|P_head_equiv_static_over_90bar_by_period'] = [x['P_equiv_static_abs_bar'] / 90.0 for x in e['P_head_equiv_static_by_period']]
        interim[f'{lab}|P_aft_equiv_static_over_90bar_by_period'] = [x['P_equiv_static_abs_bar'] / 90.0 for x in e['P_aft_equiv_static_by_period']]

    # governing thrust histories (0.1 ms, 0-25 ms) for the cases setting a thrust or pressure maximum
    gov = set()
    for lab, e in S.items():
        if e and (lab.endswith('|all') or lab.count('|') == 1):
            for m_ in ('peak_head_bar', 'F_peak_QSx0.975_N', 'F_impulse_25ms_QSx0.975_Ns', 'impulse_above_P0_25ms_head_bar_ms',
                       'above45_head_total_ms'):
                gov.add(e[m_]['case'])
    thrust_hist = {k: {kk: hist(Fstore[k][0], Fstore[k][1][kk], scale=1.0, nd=1) for kk in ('Cf1.25', 'Cf1.35', 'QSx0.950', 'QSx0.975')}
                   for k in sorted(gov)}

    # reviewer comparison (REV-COMB-2 section 4 2b tables; r2_late_light*.json)
    rv = {'4': ((82.2, 84.0), (86.4, 88.0), 3.60, 4.58, 0.96, 1.34), '5': ((79.8, 81.5), (86.5, 88.0), 3.44, 4.54, 0.84, 1.36),
          '6': ((76.0, 77.8), (83.9, 85.4), 3.06, 4.16, 0.62, 1.22), '8': ((69.6, 71.2), (77.1, 78.6), 2.50, 3.46, 0.14, 0.78),
          '10': ((65.0, 66.6), (72.5, 73.9), 2.12, 3.00, 0.0, 0.40), '12': ((61.7, 63.2), (68.9, 70.3), 1.84, 2.70, 0.0, 0.10)}
    comp = {}
    for OF in OFS_GRID:
        r = rv[f'{OF:g}']
        row = dict(reviewer_tf1_vapour_once_bar=list(r[0]), reviewer_tf1_as_written_bar=list(r[1]),
                   reviewer_max_above45_ms_vapour_once=r[2], reviewer_max_above45_ms_as_written=r[3],
                   reviewer_max_above67p5_ms_vapour_once=r[4], reviewer_max_above67p5_ms_as_written=r[5])
        for lab_i, _ in INITS:
            sel1 = [k for k in keys if cases[k]['init'] == lab_i and cases[k]['OF'] == OF and cases[k]['tf_ms'] == 1.0
                    and cases[k]['pool'] == 'q2.0' and cases[k]['t_res_s'] == 0.06]
            row[f'this_tf1_{lab_i}_bar'] = [min(cases[k]['peak_head_bar'] for k in sel1), max(cases[k]['peak_head_bar'] for k in sel1)]
            selA = [k for k in keys if cases[k]['init'] == lab_i and cases[k]['OF'] == OF]
            row[f'this_max_above45_ms_{lab_i}'] = max(cases[k]['above45_head_total_ms'] for k in selA)
            row[f'this_max_above67p5_ms_{lab_i}'] = max(cases[k]['above67p5_head_total_ms'] for k in selA)
            row[f'this_aft_over_head_{lab_i}'] = [min(cases[k]['aft_over_head_peak'] for k in selA), max(cases[k]['aft_over_head_peak'] for k in selA)]
        comp[f'OF{OF:g}'] = row

    # ---- (5) fuel-vapour inventory: first-order bound and closed-volume pressure against O/F
    m_fast_by_tres = {tres: fast(tres, m_inv)[1] for tres in TRES}
    FB = fuel_bound(V3, cold, m_fast_by_tres, T1)
    FB['closed_volume_fast_part_vs_OF'] = dict(m_N2O_g=1e3 * m_fast_by_tres[0.06], V_m3=Vs, T_tank_K=T1,
                                               rows=closed_volume_vs_OF(T1, Vs, m_fast_by_tres[0.06]),
                                               tag='DERIVED Cantera GRI-3.0 UV equilibrium, no venting, no initial gas')
    cv = FB['closed_volume_fast_part_vs_OF']['rows']
    kmax = max(cv, key=lambda k: cv[k]['ABS_solid_P_bar'])
    FB['closed_volume_fast_part_vs_OF']['max_ABS_solid'] = dict(OF=float(kmax), P_bar=cv[kmax]['ABS_solid_P_bar'])
    ks = max(cv, key=lambda k: cv[k]['styrene_gas_P_bar'])
    FB['closed_volume_fast_part_vs_OF']['max_styrene_gas'] = dict(OF=float(ks), P_bar=cv[ks]['styrene_gas_P_bar'],
                                                                   over_ABS_max=cv[ks]['styrene_gas_P_bar'] / cv[kmax]['ABS_solid_P_bar'])
    print('fuel bound', round(time.time() - t0w, 1), 's', flush=True)

    out = dict(version='v2.4a', date='2026-10-13', script='02-combustion/src/fa1_envelope_v2p4a.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               request='REV-COMB-2 R2-03 (FA-1 envelope) and R2-11 (vapour counted once); LEAD CHANGELOG line 172 (2)',
               inputs={f: EXPECT_DATA[f] for f in EXPECT_DATA}, code_dependencies=EXPECT_SRC,
               construct=dict(base='late_light_spike_v2p4 fuel-assisted construct (three-node vented network; Light class imported unchanged)',
                              changes_from_v2p4=['initial node gas x 0.05 (vapour_once, baseline) or x 1.0 (as_written)',
                                                 'pool products rate (q A_wet / h_ev)(1 + 1/OF) over the N2O evaporation time',
                                                 'products at the A1 tank temperature 286.70 K'],
                              every_source_burns_at_OF='injector flow, fast part and pool all react as N2O + ABS at the case O/F (v2.4 convention)',
                              light_at_s=tl + IG, ig_s=IG),
               state=dict(P_tank_Pa=P1, T_tank_K=T1, P0_cold_flow_Pa=P2, r_inj_kg_s=r_inj, x_liquid=x_liq, t_lift_s=tl,
                          inventory_g={k: 1e3 * v for k, v in inv.items()}, m_vap_chamber_g=1e3 * m_vap,
                          m_spray_g={str(tr): 1e3 * fast(tr, m_inv)[0] for tr in TRES}, m_fast_N2O_g={str(tr): 1e3 * fast(tr, m_inv)[1] for tr in TRES},
                          V_nodes_m3=V3, D_port_m=D_PORT, A_t_m2=A_t, A_wet_m2=math.pi * D_PORT * LL.L_GRAIN + math.pi / 4 * 0.054 ** 2),
               products={f'OF{OF:g}': prods[OF] for OF in prods},
               regression_check_v2p4=reg, inventory_checks=inv_chk, fuel_basis_sensitivity_styrene_gas=fsens,
               grid=dict(OF_grid=list(OFS_GRID), OF_extension=list(OFS_EXT), tf_ms=[1e3 * x for x in TFS], t_res_s=list(TRES),
                         pools=[p[0] for p in POOLS], inits={a: b for a, b in INITS}, entrances={a: b for a, b in ENTR}, n_cases=len(cases)),
               metric_definitions=dict(peak='max of the node pressure on the 0.05 ms solver output grid', t_peak='from the light',
                                       rise_10_90='between P0 + 10 % and P0 + 90 % of (peak - P0), before the peak',
                                       above_total='summed time above the level', above_cont='longest continuous time above the level',
                                       impulse='integral of max(P - P0, 0) over 0-25 ms after the light, bar.ms; P0 = cold-flow pressure 1.071 bar',
                                       thrust='F = Cf P_aft A_t; Cf1.25/Cf1.35 ASSUMED band; QSx0.95/QSx0.975 = quasi-steady ideal nozzle (eps 2.0, '
                                              'frozen gamma, pa 101.325 kPa) x eta_cf (DERIVED, quasi-steady assumption)',
                                       sdof='undamped SDOF, at rest, k x_max over 0-30 ms; periods_ms ' + str([1e3 * x for x in T_SDOF_F]) +
                                            ' (thrust) and ' + str([1e3 * x for x in T_SDOF_P]) + ' (pressure DLF = max k x / max gauge P)',
                                       histories='0.1 ms grid from the light to 25 ms (linear interpolation of the 0.05 ms solver output)'),
               history_grid_ms=[round(1e3 * x, 4) for x in np.arange(0.0, T_IMP + 1e-9, DT_HIST)],
               envelope=S, interim_load_comparison=interim, reviewer_comparison=comp, fuel_vapour_inventory=FB,
               thrust_histories_governing_N=thrust_hist, cases=cases,
               not_modelled=['acoustic/wave peaks along the 230 mm port (lumped nodes; transit ~0.3 ms hot, ~1 ms cold)',
                             'equilibrium (variable cv, recombination) thermochemistry: kappa fitted at 40 kg/m3 (REV-COMB-2: +3.7 % at 6.6 kg/m3, conservative)',
                             'frozen-gamma throat outflow (REV-COMB-2: vents ~4 % fast, slightly non-conservative)',
                             'flame spread, heat loss, combustion roughness; the torch contribution before the light',
                             'the fuel-vapour inventory at light (MISSING; first-order bound only)'],
               tags=dict(model='SIM three-node vented network on ASSUMED inputs (fast part, t_res, tf, f_ret, q, O/F): an ESTIMATE, not acceptance evidence',
                         products='DERIVED Cantera GRI-3.0', inventory='DERIVED Dyer, Cd 0.70 ASSUMED',
                         thrust='Cf band ASSUMED; quasi-steady Cf DERIVED', sdof='DERIVED (load-history comparison only)'))
    json.dump(out, open(out_f, 'w'), indent=None, separators=(',', ':'), default=float)
    # CSV: per (init, entrance, OF, tf) maxima over t_res and pool
    with open(out_csv, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['init', 'entrance', 'OF', 'tf_ms', 'peak_head_bar', 'peak_aft_bar', 'aft_over_head', 't_peak_head_ms', 'rise_10_90_head_ms',
                     'above45_head_ms', 'above45_aft_ms', 'above67p5_head_ms', 'above67p5_aft_ms', 'above90_head_ms',
                     'impulse25_head_bar_ms', 'impulse25_aft_bar_ms', 'F_peak_Cf1.35_N', 'F_peak_QS0.975_N', 'F_impulse25_QS0.975_Ns', 'governing_case'])
        for (lab_i, _), (lab_e, _), OF, tf in itertools.product(INITS, ENTR, OFS_EXT + OFS_GRID, TFS):
            sel = [k for k in keys if cases[k]['init'] == lab_i and cases[k]['entrance'] == lab_e and cases[k]['OF'] == OF and abs(cases[k]['tf_ms'] - 1e3 * tf) < 1e-9]
            k = max(sel, key=lambda kk: cases[kk]['peak_head_bar']); c = cases[k]
            w.writerow([lab_i, lab_e, OF, round(1e3 * tf), round(c['peak_head_bar'], 2), round(c['peak_aft_bar'], 2), round(c['aft_over_head_peak'], 4),
                        round(c['t_peak_head_ms'], 2), round(c['rise_10_90_head_ms'], 2),
                        round(max(cases[x]['above45_head_total_ms'] for x in sel), 2), round(max(cases[x]['above45_aft_total_ms'] for x in sel), 2),
                        round(max(cases[x]['above67p5_head_total_ms'] for x in sel), 2), round(max(cases[x]['above67p5_aft_total_ms'] for x in sel), 2),
                        round(max(cases[x]['above90_head_total_ms'] for x in sel), 2),
                        round(max(cases[x]['impulse_above_P0_25ms_head_bar_ms'] for x in sel), 1), round(max(cases[x]['impulse_above_P0_25ms_aft_bar_ms'] for x in sel), 1),
                        round(max(cases[x]['F_peak_Cf1.35_N'] for x in sel), 0), round(max(cases[x]['F_peak_QSx0.975_N'] for x in sel), 0),
                        round(max(cases[x]['F_impulse_25ms_QSx0.975_Ns'] for x in sel), 2), k])
    # console summary
    for lab in ('vapour_once|grid_OF4-12|all', 'as_written|grid_OF4-12|all', 'both|grid_OF4-12|all', 'both|incl_OF3-3.5|all'):
        e = S[lab]
        print(lab, 'head %.2f aft %.2f >45 %.2f ms >67.5 %.2f ms >90 %.2f ms imp %.0f bar.ms F %.0f/%.0f N' % (
            e['peak_head_bar']['max'], e['peak_aft_bar']['max'], e['above45_head_total_ms']['max'], e['above67p5_head_total_ms']['max'],
            e['above90_head_total_ms']['max'], e['impulse_above_P0_25ms_head_bar_ms']['max'], e['F_peak_Cf1.35_N']['max'], e['F_peak_QSx0.975_N']['max']),
            'aft/head', [round(x, 3) for x in e['aft_over_head_peak']], e['peak_head_bar']['case'])
    print('interim', json.dumps(interim, default=float)[:900])
    kf = max(fsens, key=lambda k: fsens[k]['peak_head_bar'])
    print('styrene-gas sensitivity max', kf, round(fsens[kf]['peak_head_bar'], 2), 'ratio', round(fsens[kf]['ratio'], 4), '>90', fsens[kf]['above90_head_total_ms'])
    for lab in ('vapour_once|grid_OF4-12|rounded_Cd1.0', 'vapour_once|grid_OF4-12|all', 'both|grid_OF4-12|all'):
        for nd in ('head', 'aft'):
            print(lab, nd, 'equiv static by period', [round(x['P_equiv_static_abs_bar'], 1) for x in S[lab][f'P_{nd}_equiv_static_by_period']],
                  'DLF', [round(x['DLF'], 3) for x in S[lab][f'P_{nd}_equiv_static_by_period']])
    print('fuel bound summary', FB['summary'], 'CV max', FB['closed_volume_fast_part_vs_OF']['max_ABS_solid'], FB['closed_volume_fast_part_vs_OF']['max_styrene_gas'])
    print('wrote', out_f, sha16(out_f), os.path.getsize(out_f), 'bytes;', out_csv, sha16(out_csv), round(time.time() - t0w, 1), 's')


if __name__ == '__main__':
    main(*sys.argv[1:4])
