"""Write interfaces/combustion.json v2 from the Combustion v2 data products (2026-10-12).

usage: python write_interface_v2.py DATA_V2_DIR OUT_JSON HUB_02_DIR [--mount-root /mnt/project-files/engine/02-combustion]
Every number is read from a v2 data file (path given in its tag) or is a lead decision / requirement quoted with its
source. File paths in the JSON point at the hub copy (HUB_02_DIR); 'files.canonical_root' gives the mount path the lead
syncs back to when /mnt/project-files recovers.
"""
from __future__ import annotations
import json, math, os, sys, hashlib
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import grain_q1d as Q

DV, OUT, HUB = sys.argv[1], sys.argv[2], sys.argv[3]
MOUNT = sys.argv[sys.argv.index('--mount-root') + 1] if '--mount-root' in sys.argv else '/mnt/project-files/engine/02-combustion'
IFDIR = os.path.dirname(os.path.abspath(OUT))
V, C = Q.V, Q.CFG


def T(v, tag, **kw):
    d = {'v': v, 'tag': tag}; d.update(kw); return d


def J(p):
    return json.load(open(os.path.join(DV, p)))


def H(p):                                   # hub path of a data file
    return os.path.join(HUB, 'data', 'v2', p)


def r(x, n=4):
    return None if x is None or (isinstance(x, float) and not math.isfinite(x)) else round(float(x), n)


def _ver(fn):
    """'<version> <date>' read from an interface file (added 2026-10-12 after gnc.json v2 appeared during the v2.1 write)."""
    try:
        d = json.load(open(fn))
        return f"{d.get('version', '?')} {d.get('date', '?')}"
    except Exception:
        return 'unreadable'


def sha(fn):
    try:
        return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]
    except OSError:
        return 'absent'


# ---------------------------------------------------------------- inputs
noz = J('nozzle_perf_v2.json'); ops = noz['grains']['v2_S230_straight_L230']['ops']
mp = pd.read_csv(os.path.join(DV, 'engine_S230/throttle_map_v2.csv'), comment='#')
m50 = mp[(mp.P_tank_Pa == 5.0e6) & (mp.D_port_m == 0.025)].set_index('frac')
plant = J('engine_S230/plant_valve_to_pc_v2.json')
ceilA = pd.read_csv(os.path.join(DV, 'ceiling_vs_time_v2.csv'), comment='#')
ceilB = pd.read_csv(os.path.join(DV, 'ceiling_vs_time_BLtank_v2.csv'), comment='#')
fsf = J('full_stroke_failure_case_v2.json')
tbc = J('thermal_bc_summary_v2.json')
ero = J('erosion_S230/erosion_dc_v2.json')
soak = J('soakback_v2.json'); wall = J('soakback_wall_v2.json')
sens = J('soakback_sens_v2.json') if os.path.exists(os.path.join(DV, 'soakback_sens_v2.json')) else None
feed = J('feed_line_checks_v2.json'); ign = J('ignition_v2.json'); stab = J('stability_v2.json')
settle = J('settling_v2.json'); sup = J('supercharge_trade_v2.json'); injc = J('injector_compare_v2.json')
n2ov = J('n2o_validation_v2.json'); port = J('chamber_port_state_v2.json')
wip = J('dc_gncv2wip/summary_v2.json'); gsum = J('engine_S230/summary_v2.json')
# v2.2 (2026-10-12, lead request on the HV69 in-line pintle drive): actuator speed checks and head-end thermal BC
act = J('actuator_rate_check_v2.json') if os.path.exists(os.path.join(DV, 'actuator_rate_check_v2.json')) else None
hed = J('headend_thermal_v2.json') if os.path.exists(os.path.join(DV, 'headend_thermal_v2.json')) else None


def dc_shutdowns(rel):
    """Thrust just before each run->shutdown transition of a duty-cycle result CSV (mean over the last 0.05 s)."""
    d = pd.read_csv(os.path.join(DV, rel), comment='#'); st = d.state.values; out = []
    for i in range(1, len(st)):
        if st[i - 1] == 'run' and st[i] != 'run':
            w = d[(d.t > d.t[i] - 0.05) & (d.t <= d.t[i - 1])]
            out.append(dict(t_s=r(d.t[i], 3), F_before_N=r(w.F.mean(), 1), Pc_before_Pa=r(d.Pc[i - 1], -3)))
    return out
gt = pd.read_csv(os.path.join(DV, 'grain_trade_v2.csv'), comment='#'); gt = gt[gt.variant == 'S230 (v2)']
cont = pd.read_csv(os.path.join(DV, 'nozzle_contour_v2.csv'), comment='#')
i_t = int(cont.r_m.idxmin()); x_t = float(cont.x_face_m[i_t]); x_e = float(cont.x_face_m.iloc[-1])
Rt = float(cont.r_m[i_t]); Re_ = float(cont.r_m.iloc[-1]); At = math.pi * Rt ** 2

SIM = 'SIM grain_q1d.py v2 (quasi-1D port, S230, nominal ASSUMED law, Dyer pintle Cd 0.70, eta_c* 0.92, eta_cf 0.975)'
mx = ops[0]; st100 = port['states']['1.0']

# geometry derived
L_g, D_g, D_p0 = V['L_grain'], V['D_grain'], V['D_port0']
web0 = (D_g - D_p0) / 2
V_free = math.pi / 4 * V['D_ch'] ** 2 * (V['L_pre'] + V['L_post']) + V['V_conv'] + math.pi / 4 * D_p0 ** 2 * L_g
Lstar = V_free / At
m_grain = lambda rho: rho * math.pi / 4 * (D_g ** 2 - D_p0 ** 2) * L_g
g_tc = st100['gamma']; Gam = math.sqrt(g_tc) * (2 / (g_tc + 1)) ** ((g_tc + 1) / (2 * (g_tc - 1)))
tau_fill = Lstar / (st100['cstar_delivered_m_s'] * Gam ** 2)

# operating points table
tp = []
for o in ops:
    fr = o['frac']; row = m50.loc[fr] if fr in m50.index else None
    st = port['states'].get(f'{fr}', port['states'].get(str(fr)))
    tp.append(dict(fraction=fr, F_N=r(o['F'], 1), Pc_Pa=r(o['Pc'], 0), mdot_ox_kg_s=r(o['mox'], 5), mdot_fuel_kg_s=r(o['mf'], 5),
                   OF=r(o['OF'], 3), Isp_SL_s=r(o['Isp'], 1),
                   pintle_lift_m=r(row['lift_m'], 6) if row is not None else None,
                   dP_inj_over_Pc=r(row['dP_over_Pc'], 3) if row is not None else None,
                   G_ox_head_kg_m2s=r(st['G_ox_head_kg_m2s'], 1) if st else None,
                   T0_delivered_K=r(st['T0_delivered_K'], 0) if st else None))

# full-stroke failure rows for S230
fs = [x for x in fsf['rows'] if 'S230' in x['grain']]
fs_max = max(fs, key=lambda x: x['Pc_full_stroke_bar']) if fs else None
fs20 = [x for x in fs if x['T_tank_C'] == 20.0 and x['Cd'] == 0.7][0]

# thermal summary
pts = tbc['points']

# erosion summary (S230 x v1 duty cycles)
er = {}
for k, v in ero.items():
    er[k.replace('.csv', '')] = dict(recession_nominal_mm=v['nominal']['recession_mm'], dAt_nominal_pct=v['nominal']['dAt_over_At_pct'],
                                     recession_conservative_mm=v['conservative']['recession_mm'],
                                     dAt_conservative_pct=v['conservative']['dAt_over_At_pct'],
                                     literature_scaled_mm=v['literature_scaled_mm'],
                                     q_in_max_MW_m2=[v['nominal']['q_in_max_MW_m2'], v['conservative']['q_in_max_MW_m2']],
                                     Tw_max_K=[v['nominal']['Tw_max_K'], v['conservative']['Tw_max_K']])
a1 = ero['DC-A1-S230_neqE1e+03_reg1.csv']
sep = pd.read_csv(os.path.join(DV, 'nozzle_perf_v2.csv'), comment='#')
sep = sep[(sep.grain == 'v2_S230_straight_L230') & (sep.eps == 2.0)].set_index('frac')
pe_pa_max = float(sep.loc[1.0, 'pe_over_pa'])
cvc = [x for x in injc['ceiling_vs_Cd'] if x['T_tank_C'] == 20.0]
cw = [x for x in injc['ceiling_worst_model']['rows'] if math.isfinite(x['F_ceiling_N'])]
cw_min = min(cw, key=lambda x: x['F_ceiling_N'])
hb = feed['hose_and_budget']; v_hose = [hb[k]['v_m_s'] for k in hb]
v_nom = feed['hose_and_budget_nominal_0p241']['v_m_s']
dpf = [x['dp_hose_Pa'] for k in hb for x in hb[k]['hose_friction'].values()]
surge = [x['dp_rhoLdvdt_Pa'] for x in feed['surge']['rows']]
bud = feed['budget_verdict']
lag50 = max(x['phase_lag_deg_at_50Hz'] for x in feed['sense_line'] if x['L_m'] <= 0.3 + 1e-9)
fl = [p_ for p_ in plant if p_['frac'] == 0.125][0]
dh_2pct_FS = 0.02 * 500.0 / fl['dF_dh_N_per_m']; dh_2pct_floor = 0.02 * fl['F0_N'] / fl['dF_dh_N_per_m']
# gnc.json v2 throttle requirements (deadband <= 0.5 % F_max, resolution 2 % F_max, closed Pc loop): lift and Pc equivalents
p100 = [p_ for p_ in plant if p_['frac'] == 1.0][0]
DB_N = 0.005 * 500.0
db_100_um, db_floor_um = DB_N / p100['dF_dh_N_per_m'] * 1e6, DB_N / fl['dF_dh_N_per_m'] * 1e6
_op = {round(o['frac'], 3): o for o in ops}
dFdPc_100, dFdPc_floor = _op[1.0]['F'] / _op[1.0]['Pc'], _op[0.125]['F'] / _op[0.125]['Pc']      # N/Pa (F ~ Cf At Pc)
db_Pc_100_bar, db_Pc_floor_bar = DB_N / dFdPc_100 / 1e5, DB_N / dFdPc_floor / 1e5
gap_floor = float(m50.loc[0.125, 'lift_m']) * math.sin(math.radians(15.0))
flights_nom = 5.0 / a1['nominal']['dAt_over_At_pct']; flights_cons = 5.0 / a1['conservative']['dAt_over_At_pct']

# sense line: lowest natural frequency per line length
sl = {}
for x in feed['sense_line']:
    k = f"L{x['L_m']:.2f}m"
    sl.setdefault(k, []).append(x['f_n_Hz'])
sl = {k: [r(min(v), 0), r(max(v), 0)] for k, v in sl.items()}

# stability rows at the initial port
stab0 = {f"{x['frac']}": x for x in stab if abs(x['D_port_m'] - 0.025) < 1e-6}

# wip duty cycles
wrows = []
for k, d in wip.items():
    wrows.append(dict(case=k, burn_s=d['burn_s'], impulse_Ns=d['impulse_Ns'], gnc_impulse_Ns=r(d.get('gnc_impulse_Ns'), 1),
                      ox_used_kg=d['ox_used_kg'], fuel_used_kg=d['fuel_used_kg'], OF_mean=d['OF_mean'], Isp_mean_s=d['Isp_mean_s'],
                      web_end_mm=d['w_min_end_mm'], liquid_left_kg=d['m_liq_end_kg'],
                      liquid_left_over_used=r(d['m_liq_end_kg'] / d['ox_used_kg'], 3), min_dP_over_Pc=d['dpc_min'],
                      min_ceiling_N=d['min_F_ceiling_N'], ceiling_limited_s=d['ceiling_limited_s'], tank=d['tank'],
                      regression_scale=d['regression_scale']))

dc_v1 = [dict(duty_cycle=row.duty_cycle, regression_scale=row.regression_scale, burn_s=row.burn_s, impulse_Ns=row.impulse_Ns,
              N2O_used_kg=row.N2O_used_kg, fuel_used_kg=row.fuel_used_kg, OF_mean=row.OF_mean, Isp_mean_s=row.Isp_mean_s,
              web_end_mm=row.web_end_mm, burnthrough_s=None if not np.isfinite(row.burnthrough_s) else row.burnthrough_s,
              liquid_left_kg=row.liquid_N2O_left_kg, min_ceiling_N=row.min_ceiling_N, min_dP_over_Pc=row.min_dP_over_Pc)
         for row in gt.itertuples()]

# soak-back extracts
ins = soak['insert']
al_pk = {k.split('|')[0]: [] for k in ins}
for k, v in ins.items():
    al_pk[k.split('|')[0]].append((k.split('|')[1] + '|' + k.split('|')[2], r(v['T_retainer_peak_K'], 0)))
ws = wall['cases']
relight_block = 'pending'
if os.path.exists(os.path.join(DV, 'soakback_relight_v2.json')):
    rl = J('soakback_relight_v2.json'); rr_ = pd.DataFrame(rl['rows'])
    _rk = ('T_at_relight_K', 'T_at_Pcmax_landing_burn_K', 'T_max_landing_burn_K', 'Pc_at_Tmax_landing_burn_Pa', 'T_post_landing_peak_K',
           't_post_peak_after_shutdown_s', 'T_900s_K', 'T_3600s_K', 't_above_150C_s', 't_above_200C_s', 't_above_240C_s', 't_above_300C_s')
    relight_block = dict(governing_cases=rl.get('governing_cases'), soak_window_s=rl.get('soak_window_s'),
                         duty_cycles={k: {kk: v[kk] for kk in ('source', 'burns_s', 't_MECO_s', 't_relight_s', 'coast_s', 'Pc_relight_plus_0p5s_Pa',
                                                               'Pc_max_landing_burn_Pa', 't_Pc_max_landing_burn_s', 't_last_shutdown_s', 'note') if kk in v}
                                      for k, v in rl['duty_cycles'].items()},
                         csv=H('soakback_relight_v2.csv'),
                         summary={(f"{d}|{p_}|{b}" + (f"|hc{h:.0f}" if h > 0 else "")): {kk: r(g[kk].iloc[0], 0) for kk in _rk if kk in g}
                                  for (d, p_, b, h), g in rr_.fillna({'hc_W_m2K': -1}).groupby(['duty_cycle', 'part', 'bracket', 'hc_W_m2K'])},
                         note=('coast and relight time are explicit in each DC CSV (burn segments from the mox and Pc columns); coasts adiabatic '
                               '(upper bound at relight); times above thresholds counted over the soak window; no allowable applied '
                               '(240 C = Al lip at 51 MPa, 192 C = Al aft land, steel = own allowable; reuse judgement = Mechanical)'))
def _rng(s, fmt='{:.0f}'):
    s = pd.Series(s).dropna()
    return (fmt.format(s.min()) + '-' + fmt.format(s.max())) if len(s) else 'n/a'


_ins = pd.DataFrame([dict(dc=k.split('|')[0].split('-S230')[0], hc=k.split('|')[1], mat=k.split('|')[2], **v) for k, v in ins.items()])
soak_concl = ("240 C (513 K) is the Mechanical v3.1 allowable of the ALUMINIUM lip at 51 MPa. With the 0.15 kg retainer of soakback.py on "
              f"the gnc.json v1 cycles aluminium peaks at {_rng(_ins[_ins.mat == 'Al'].T_retainer_peak_K)} K (above it)")
if sens:
    _s6 = pd.DataFrame(sens['rows']); _s6 = _s6[(_s6.retainer_material == 'Al') & (_s6.retainer_mass_kg == 0.60)]
    soak_concl += f"; about 0.6 kg of aluminium (~540 J/K) in good thermal contact gives {_rng(_s6.T_retainer_peak_K)} K (sensitivity_summary)"
soak_concl += (f". Steel results ({_rng(_ins[_ins.mat == 'steel'].T_retainer_peak_K)} K at 0.15 kg) are for comparison with a steel "
               "temperature-dependent allowable, which is not defined here (lead note 2026-10-12)")
rl_txt = ''
if relight_block != 'pending':
    _ret = rr_[rr_.part == 'retainer_lip']; _case = rr_[rr_.part == 'case_post_chamber']
    _A = _ret[_ret.coast_s.notna()]; _c5 = _case[_case.bracket.str.startswith('phenolic 5.0')]
    _c5A = _c5[_c5.coast_s.notna()]
    _dcA = [v for v in rl['duty_cycles'].values() if v.get('coast_s')]
    _AlA = _A[_A.bracket.str.startswith('Al')]
    rl_txt = (f" TS-1 (relight after the MECO coast; A cycles, coast {_rng(_A.coast_s, '{:.1f}')} s, coasts adiabatic): retainer at relight "
              f"{_rng(_AlA.T_at_relight_K)} K (Al brackets), {_rng(_A[_A.bracket.str.startswith('steel')].T_at_relight_K)} K "
              f"(steel 0.30 kg); at the landing-burn Pc maximum ({_rng([v['Pc_max_landing_burn_Pa'] / 1e5 for v in _dcA], '{:.1f}')} bar) "
              f"{_rng(_AlA.T_at_Pcmax_landing_burn_K)} K (Al); the in-burn maximum {_rng(_AlA.T_max_landing_burn_K)} K (Al) occurs at the end of "
              f"the landing burn at Pc {_rng(_AlA.Pc_at_Tmax_landing_burn_Pa / 1e5, '{:.1f}')} bar. "
              f"Aft land behind 5 mm phenolic at relight {_rng(_c5A.T_at_relight_K)} K. TS-2 (post-landing soak, {rl.get('soak_window_s', 0):.0f} s window, "
              f"A and B cycles): retainer peak {_rng(_ret.T_post_landing_peak_K)} K, time above 150 C {_rng(_ret.t_above_150C_s)} s; aft land "
              f"(5 mm phenolic) peak {_rng(_c5.T_post_landing_peak_K)} K, time above 150 C {_rng(_c5.t_above_150C_s)} s (soakback_relight_v2.csv).")
sens_txt = 'pending'
if sens:
    sr = pd.DataFrame(sens['rows'])
    parts = []
    for (dc, mat, ms), g in sr.groupby(['duty_cycle', 'retainer_material', 'retainer_mass_kg']):
        parts.append(f"{dc.split('-S230')[0]} {mat} {ms:.2f} kg: {g.T_retainer_peak_K.min():.0f}-{g.T_retainer_peak_K.max():.0f} K")
    ok = sr[sr.T_retainer_peak_K < 513.15]
    sens_txt = ('retainer peak over hc 150-2000 W/m2K -> ' + '; '.join(parts) +
                f". Cases below 513 K (240 C): {len(ok)} of {len(sr)}, all aluminium "
                f"({', '.join(sorted(set(f'{a} kg' for a in ok.retainer_mass_kg.map(lambda x: f'{x:.2f}'))))}); "
                "steel rows are for comparison with a steel temperature-dependent allowable (240 C applies to the aluminium lip at 51 MPa).")

# ---------------------------------------------------------------- v2.2: pintle drive speed checks (lead request 2026-10-12)
DCS_V2 = (('DC-A1 gnc v2', 'dc_gncv2wip/DC-A1-S230v2wip_neqE1e+03_reg1.csv'), ('DC-A2 gnc v2', 'dc_gncv2wip/DC-A2-S230v2wip_neqE1e+03_reg1.csv'),
          ('DC-B1 gnc v2', 'dc_gncv2wip/DC-B1-S230v2wip_neqE1e+03_reg1.csv'), ('DC-B2 gnc v2', 'dc_gncv2wip/DC-B2-S230v2wip_neqE1e+03_reg1.csv'),
          ('DC-A1 gnc v1', 'dc_g3/DC-A1-S230_neqE1e+03_reg1.csv'), ('DC-A2 gnc v1', 'dc_g3/DC-A2-S230_neqE1e+03_reg1.csv'))
speed_block, act_txt, eng05_txt, eng04_txt = 'pending', 'pending', 'pending', 'pending'
if act:
    _sd = pd.DataFrame([{k: v for k, v in x.items() if k != 'trace'} for x in act['shutdown']])
    _st = pd.DataFrame([{k: v for k, v in x.items() if k != 'trace'} for x in act['start']])
    _sr = {f"{x['full_stroke_s']:.3f}": {k: (r(v, 4) if isinstance(v, float) else v) for k, v in x.items()} for x in act['start_rule']}
    _hs = {f"{x['full_stroke_s']:.3f}": r(x['N2O_admitted_g'], 2) for x in act['hard_start']}
    _lim = act['max_full_stroke_time_for_ENG05_from_100pct_s']
    _sdn = {k: dc_shutdowns(v) for k, v in DCS_V2 if os.path.exists(os.path.join(DV, v))}
    _s100 = _sd[_sd.frac == 1.0].set_index('full_stroke_s'); _s75 = _sd[_sd.frac == 0.75].set_index('full_stroke_s')
    _st100 = _st[_st.frac == 1.0].set_index('full_stroke_s'); _stf = _st[_st.frac == 0.125].set_index('full_stroke_s')
    _st20 = _st[_st.frac == 0.2].set_index('full_stroke_s')
    _tfs = sorted(_s100.index)
    _surge = feed['surge']['rows']; _tc100 = 0.25 * 1.9176e-3 / 4e-3     # closure time from the 100 % lift at a 0.25 s full stroke
    _dp_tc = max(x['dp_rhoLdvdt_Pa'] * x['t_close_s'] / _tc100 for x in _surge)
    _meco = [s['F_before_N'] for k, v in _sdn.items() for s in v[:1] if s['F_before_N'] > 400]
    _land = [v[-1]['F_before_N'] for k, v in _sdn.items() if 'gnc v2' in k and v[-1]['F_before_N'] < 400]
    _sd_land = _sd[(_sd.full_stroke_s == 0.25) & (_sd.frac.isin([0.25, 0.5]))]
    speed_block = dict(
        model=act['model'],
        origin_of_0p08s=act['origin_of_0p08s'],
        start_transient=T({f"{tf:.3f}": dict(Pc_overshoot_max_pct=r(g.Pc_overshoot_pct.max(), 3),
                                              dPc_dt_max_start_to_100pct_bar_s=r(_st100.loc[tf, 'dPc_dt_max_bar_s'], 0),
                                              t10_t90_start_to_100pct_s=[r(_st100.loc[tf, 't10_s'], 3), r(_st100.loc[tf, 't90_s'], 3)],
                                              t90_start_to_20pct_s=r(_st20.loc[tf, 't90_s'], 3), t90_start_to_12p5pct_s=r(_stf.loc[tf, 't90_s'], 3))
                           for tf, g in _st.groupby('full_stroke_s')},
                          "SIM step start (model: 0.10 s torch-to-main delay ASSUMED, then straight to the commanded lift); t from the start command"),
        start_rule=T(_sr, "DERIVED: travel time = lift / (stroke / full-stroke time) + 10 ms lag (ASSUMED) against the ignition_v2.json "
                          "slots; ramp capability = dF/dh at 100 % (159 kN/m, plant fit) x speed"),
        hard_start_N2O_admitted_g=T(_hs, "DERIVED: N2O into an unlit chamber between the ignition-lift command (0.12 s) and the ignition "
                                         "check/abort (0.35 s) incl. the opening/closing travel, 0.038 kg/s cold flow at the 12.5 % lift (ASSUMED)"),
        eng05_tailoff=T(dict(requirement="gnc.json v2 requirements.ignition.shutdown_tail_off: < 10 % thrust within 0.10 s (REQ ENG-05; GNC note: simulated tau_off 35 ms)",
                             t_to_10pct_of_F_before_s=act['eng05_tailoff_table'],
                             tailoff_impulse_from_100pct_Ns={f"{tf:.3f}": r(_s100.loc[tf, 'tailoff_impulse_Ns'], 1) for tf in _tfs},
                             max_full_stroke_time_meeting_ENG05_from_100pct_s={k: r(v, 3) for k, v in _lim.items()},
                             duty_cycle_shutdowns=_sdn),
                        "SIM shutdown from steady thrust (rate-limited closure + 10 ms lag; cold blowdown and fuel decay as grain_q1d v2); "
                        "duty-cycle shutdown thrust = mean over the last 0.05 s before the shutdown state (data/v2/dc_gncv2wip, dc_g3)"),
        feed_surge_on_closure=T(f"rho L dv/dt surge falls as 1/t_close: <= {_dp_tc/1e3:.0f} kPa for the 0.4-0.8 m line at the {_tc100:.2f} s closure "
                                "from the 100 % lift with a 0.25 s full stroke (feed_line_checks_v2.json rows at 0.04-0.15 s); a slower drive lowers it",
                                "DERIVED"))
    act_txt = (f"No combustion basis for 0.08 s. Start transient: Pc overshoot <= {_st.Pc_overshoot_pct.max():.2f} % for full-stroke times "
               f"{min(_tfs):.2f}-{max(_tfs):.2f} s and starts to 12.5-100 % (chamber fill ~4 ms: the start is quasi-static behind the pintle); "
               f"max dPc/dt on a start to 100 % falls from {_st100.dPc_dt_max_bar_s.loc[min(_tfs)]:.0f} bar/s ({min(_tfs):.2f} s) to "
               f"{_st100.dPc_dt_max_bar_s.loc[0.25]:.0f} bar/s (0.25 s). Hard start: N2O admitted to an unlit chamber before the 0.35 s ignition "
               f"check {min(_hs.values()):.1f} g at every speed (set by the ignition-lift dwell and the abort, not the speed). "
               "Stability: the chug/acoustic margins (stability_v2.json) do not contain the drive; a rate limit only bites on large Pc-loop "
               f"commands (at 0.25 s full stroke, 16 mm/s is reached by a 2.3 Hz sine of {16 / (2 * math.pi * 2.3):.1f} mm amplitude). Feed surge on "
               f"closure falls with slower closure (<= {_dp_tc/1e3:.0f} kPa). Start rule at 0.25 s full stroke: 0.10 mm bleed lift in "
               f"{_sr['0.250']['bleed_lift_0p10mm_s']:.3f} s (slot 0.5 s, then the >= 0.3 s valve ramp), return to the seat {_sr['0.250']['return_to_seat_s']:.3f} s, "
               f"ignition lift 0.207/0.301 mm in {_sr['0.250']['ignition_lift_s'][0]:.3f}/{_sr['0.250']['ignition_lift_s'][1]:.3f} s (slot 0.23 s), "
               f"ramp capability {_sr['0.250']['ramp_capability_at_100pct_N_s']:.0f} N/s at 100 % (more at lower thrust) vs the sequence cap <= 2500 N/s "
               "and the gnc.json v2 minimum 2 F_max/s = 1000 N/s: acceptable.")
    eng05_txt = (f"ENG-05 (< 10 % thrust within 0.10 s) at MECO ({min(_meco):.0f}-{max(_meco):.0f} N on the A cycles) needs a full-stroke time <= "
                 f"{_lim['t_to_10pct_of_F_before_s']:.3f} s in the model; time to < 10 % of the pre-shutdown thrust from 100 %: "
                 + ', '.join(f"{_s100.loc[tf, 't_to_10pct_of_F_before_s']:.3f} s at {tf:.3f} s" for tf in _tfs) +
                 f"; tail-off impulse {_s100.loc[min(_tfs), 'tailoff_impulse_Ns']:.1f} N s (0.08 s) vs {_s100.loc[0.25, 'tailoff_impulse_Ns']:.1f} N s (0.25 s). "
                 f"From 75 % a 0.25 s drive meets it ({_s75.loc[0.25, 't_to_10pct_of_F_before_s']:.3f} s); the landing-burn shutdowns "
                 f"({min(_land):.0f}-{max(_land):.0f} N, gnc.json v2) meet it at every speed ({_sd_land.t_to_10pct_of_F_before_s.min():.3f}-"
                 f"{_sd_land.t_to_10pct_of_F_before_s.max():.3f} s from 25-50 % at 0.25 s).")
    eng04_txt = (f"Step start to the 12.5 % floor reaches 90 % at {_stf.t90_s.min():.2f}-{_stf.t90_s.max():.2f} s and to 20 % at "
                 f"{_st20.t90_s.min():.2f}-{_st20.t90_s.max():.2f} s for every drive speed (set by the ASSUMED 0.10 s torch-to-main delay and the "
                 "slow fuel/thermal-lag mode, not the drive) vs ENG-04 <= 0.5 s with 'ignition at the floor' (gnc.json v2): marginal at 12.5 % in the model, "
                 "inside the 0.6 s planning value.")

# ---------------------------------------------------------------- v2.2: head-end thermal BC (lead request 2026-10-12)
head_block, head_txt, head_impl = 'pending', 'pending', 'pending'
if hed:
    _hrows = []
    for dc, c in hed['cases'].items():
        for key, s_ in c['variants'].items():
            band, cons, mh = key.split('|')
            th = s_['T_head']; en = s_['energy_into_head_J']
            _hrows.append(dict(dc=dc, band=band, cons=cons, mass=mh, T_relight=th['at_relight_K'], T_meco=th['at_MECO_K'],
                               T_flight=th['max_in_flight_K'], T_last=th['at_last_shutdown_K'], T_soak=th['soak_peak_K'],
                               t_soak=th['soak_peak_after_shutdown_s'], T_3600=th['at_3600s_K'],
                               a50f=s_['T_head_time_above_50C_in_flight_s'], a50s=s_['T_head_time_above_50C_soak_s'],
                               a60f=s_['T_head_time_above_60C_in_flight_s'], a60s=s_['T_head_time_above_60C_soak_s'],
                               Tcase=s_['T_case_fwd']['max_in_flight_K'], Tcase_soak=s_['T_case_fwd']['soak_peak_K'],
                               Tins=s_['T_ins']['max_in_flight_K'], Ef=en['face_flight'], Ej=en['joint_flight'], En=en['n2o_flight'],
                               Efs=en['face_soak'], Ejs=en['joint_soak'], Ebs=en['bay_soak']))
    _hd = pd.DataFrame(_hrows)
    _cols = ['T_at_MECO_K', 'T_at_relight_K', 'T_max_in_flight_K', 'T_at_last_shutdown_K', 'T_soak_peak_K', 't_soak_peak_after_last_shutdown_s',
             'T_at_3600s_K', 't_above_50C_flight_s', 't_above_50C_soak_s', 't_above_60C_flight_s', 't_above_60C_soak_s',
             'T_case_fwd_max_flight_K', 'T_case_fwd_soak_peak_K', 'E_face_flight_J', 'E_joint_flight_J', 'E_N2O_flight_J']
    _tab = {f"{x.dc}|{x.band}|{x.cons}|{x.mass}": [r(x.T_meco, 1), r(x.T_relight, 1), r(x.T_flight, 1), r(x.T_last, 1), r(x.T_soak, 1),
                                                    r(x.t_soak, 0), r(x.T_3600, 1), r(x.a50f, 2), r(x.a50s, 0), r(x.a60f, 2), r(x.a60s, 0),
                                                    r(x.Tcase, 1), r(x.Tcase_soak, 1), r(x.Ef, 0), r(x.Ej, 0), r(x.En, 0)]
            for x in _hd.itertuples()}
    _fl = _hd[_hd.dc.str.contains('gnc')]
    def _rk(df, col):
        return f"{df[col].min() - 273.15:.0f}-{df[col].max() - 273.15:.0f} C"
    def _rs(df, col, f=1.0, fmt='{:.0f}'):
        a_, b_ = sorted((df[col].min() * f, df[col].max() * f))
        return fmt.format(a_) + '-' + fmt.format(b_)
    _cad = _fl[_fl.cons == 'disc2mm']; _c44 = _cad[_cad.mass == 'head_0.44kg']; _c20 = _cad[_cad.mass == 'head_0.20kg']
    _c44x1 = _c44[_c44.band == 'hg_x1']; _bare44 = _fl[(_fl.cons == 'bare') & (_fl.mass == 'head_0.44kg')]
    _d4 = _fl[(_fl.cons == 'disc4mm') & (_fl.mass == 'head_0.44kg')]
    _relA = _c44[_c44.T_relight.notna()]
    _gr = _hd[_hd.dc.str.contains('DC-C')]
    _gr44 = _gr[(_gr.cons == 'disc2mm') & (_gr.mass == 'head_0.44kg')]
    head_block = dict(
        purpose=hed['purpose'], version=hed['version'], supersedes=hed.get('supersedes'),
        geometry=T(hed['geometry'], "Mechanical CAD v3.2 dimensions (parts_engine.py read only; Mechanical confirms); head mass 0.44 kg DERIVED from the CAD dimensions"),
        surfaces="injector face (r 2.75-26.95 mm at x_face 0: TC-10 2 mm phenolic disc over r 10.2-26.85 mm, TC-03 17-4PH seat-insert flange r 2.75-10.1 mm), pre-chamber wall (x_face 0-0.030 m, TC-06 1.6 mm phenolic over the 3.175 mm 6061 case), pintle needle (17-4PH, 4 mm stem, 6 mm body in the 10 mm manifold bore)",
        bc_csv={k: H(v['bc_csv']) for k, v in hed['cases'].items()},
        bc_by_phase=T(dict(
            burn=("gas side h_g(Pc), T_aw(Pc), q_rad band from the thermal_bc_*_v2.csv rows at x_face 0 (Bartz at the pre-chamber diameter, wall 600 K), "
                  "log-Pc interpolation, h_g ~ Pc^0.8 below the 12.5 % point; T_aw = delivered T0 = UPPER BOUND for the spray-cooled head; apply x0.5-2 to h_g, "
                  "q_rad lo/mid/hi with the band (incident gas term); radiative exchange eps 0.8: face <-> pre-chamber insulator F 0.65, face <-> grain end F 0.35 "
                  "(grain 750 K ASSUMED); N2O side h_c(mdot, T_liq) on the CAD manifold annulus 10/6 mm (columns of headend_bc_*_v2.csv)"),
            MECO_coast=("pintle seated, isolation valve open, chamber vented: gas side natural convection 10 W/m2K (x0.5-2) to cavity gas at the insulator "
                        "surface temperature (upper bound) + the same radiative exchange (grain 700 K at shutdown, 1 s decay ASSUMED); N2O side static liquid "
                        "at the tank temperature, hA 1 W/K (ASSUMED)"),
            relight="as burn from the relight ignition; the coast duration and the relight time are explicit in each DC CSV (burn segments from mox and Pc)",
            post_landing_soak=("as coast for 3600 s after the last shutdown; isolation valve closed, trapped liquid relieved: N2O side vapour only "
                               "(hA 0.01 W/K, no evaporative credit); bay 10 W/m2K at 288 K"),
            pintle_stem=("the needle tip takes the face BC and sits in the N2O flow (h_c); stem conductance to the bonnet 2.3e-3 W/K (17-4PH 4 mm x 0.10 m): "
                         "not a heat path to the servo")),
            "DERIVED headend_thermal_v2.py v2.2b (headend_thermal_v2.json)"),
        bc_points_x_face0=T([{k: (r(v, 1) if isinstance(v, float) else v) for k, v in x.items()} for x in hed['bc_points_x_face0']],
                            "SIM Bartz, thermal_bc_*_v2.csv first row (Pc Pa, h W/m2K, Taw K, qlo/qhi W/m2)"),
        n2o_side=T({k: (r(v, 1) if isinstance(v, float) else ({kk: r(vv, 6) for kk, vv in v.items()} if isinstance(v, dict) else v))
                    for k, v in hed['n2o_side'].items()}, "DERIVED Dittus-Boelter; CoolProp liquid rho/cp, CO2 corresponding-states mu/k"),
        pintle_needle=hed['pintle_needle'],
        first_cut_bound=T(dict(model=("1-D pre-chamber wall stack (1.6 mm phenolic + 3.175 mm 6061; re-radiation while burning, adiabatic gas side otherwise; "
                                      "back side bay 10 W/m2K + two-way 4 W/K joint to the head) + lumped 6061 head 0.2 / 0.44 kg (c 900 J/kg K) with the face "
                                      "bare / 2 mm disc (CAD) / 4 mm disc (2000 W/m2K contact), N2O cooling h_c x 16.3 cm2 in flow, 1 W/K coast, 0.01 W/K soak, "
                                      "bay 10 W/m2K x 0.01 m2, start 293.15 K; energies = heat into the head per path (J)"),
                               columns=_cols, rows=_tab),
                          "DERIVED (bounding: T_aw = T0, no char credit; Mechanical thermal FEA with the real head/bonnet/bracket supersedes)"),
        not_modelled=hed['not_modelled'])
    head_txt = (f"Lumped head bound (T_aw = T0, no char credit; gnc.json v1/v2 A1/A2/B1, h_g x0.5-2). CAD v3.2 (2 mm face disc), 0.44 kg head: at relight "
                f"{_rk(_relA, 'T_relight')} (x1 {_rk(_relA[_relA.band == 'hg_x1'], 'T_relight')}), max in flight {_rk(_c44, 'T_flight')} (x1 {_rk(_c44x1, 'T_flight')}), "
                f"post-landing soak peak {_rk(_c44, 'T_soak')} at {_rs(_c44, 't_soak')} s after the last shutdown; time above 50 C in flight "
                f"{_rs(_c44, 'a50f', fmt='{:.1f}')} s. 0.2 kg head: max in flight {_rk(_c20, 'T_flight')}, soak peak {_rk(_c20, 'T_soak')}. Face disc lost (bare, 0.44 kg): "
                f"max in flight {_rk(_bare44, 'T_flight')}; 4 mm disc: {_rk(_d4, 'T_flight')}. Heat into the 0.44 kg head in flight (CAD disc, x1): face "
                f"{_rs(_c44x1, 'Ef', 1e-3, '{:.1f}')} kJ, pre-chamber case joint {_rs(_c44x1, 'Ej', 1e-3, '{:.1f}')} kJ, N2O removes {_rs(_c44x1, 'En', -1e-3, '{:.1f}')} kJ: "
                f"the case path is as large as the face path; forward case node (1.6 mm phenolic) {_rk(_cad, 'Tcase')} in flight, soak peak {_rk(_cad, 'Tcase_soak')}. "
                f"Ground cycle DC-C (46 s burns, CAD, 0.44 kg): head max {_rk(_gr44, 'T_flight')}, soak peak {_rk(_gr44, 'T_soak')}.")
    head_impl = ("Servo mount (HV69 -10..60 C; mount limit 50 C in flight incl. relight): under this bound the head itself is above 50 C at relight in the x1-x2 "
                 "cases and through the post-landing soak, so the mount must not rely on the head staying cool. The HV69 does not sit at the head temperature "
                 "(bracket TC-12 on 2x M4, servo heat capacity): Mechanical FEA with these BCs decides. Measures that hold whatever the true head-end gas "
                 "temperature: keep the 2 mm face disc (a lost disc adds the bare-face rows), a low-conductance bracket foot (G10/PEEK washers, stainless or "
                 "titanium screws), consider a thicker pre-chamber insulator (the case joint carries ~half of the heat), and instrument T1: thermocouples on "
                 "the face-disc back, head top, bracket foot and servo case to replace the T0 bound. The same bound puts the pre-chamber case behind "
                 f"the 1.6 mm TC-06 insulator at {_rk(_cad, 'Tcase')} in flight (B1 highest; A cycles {_rk(_cad[_cad.T_relight.notna()], 'Tcase')}): this joins "
                 "OI-4 (insulator thickness from the FEA).")


J2 = {
    "id": "combustion", "version": "v2.2", "date": "2026-10-12", "owner": "combustion",
    "revision_note": ("v2.2 (2026-10-12, lead request on the HV69 in-line pintle drive): valves_and_actuators.pintle_actuator.full_stroke_time_s 0.08 s RETIRED (no combustion basis; it was derived from the v1 ENG-03 throttle-response target) and replaced by speed_checks (actuator_rate_check_v2.json: start transient, start rule, hard-start inventory, ENG-05 tail-off vs drive speed); lead decision logged: pre-MECO throttle-down to <= 75 %, spring-assisted closing, closing time at 25 bar in B-PNT-1, ENG-05 wording unchanged (OI-14); ignition_v2.json v2.2 shutdown wording (the 50 mm/s closing cap retired) and ramp marked as a cap; ENG-04 floor-start t90 added (OI-2); thermal_and_loads.head_end_bc added (injector face, forward closure, pintle stem; burn, MECO coast, relight, post-landing soak; x0.5-2 band; headend_thermal_v2.py v2.2b with CAD v3.2 geometry; first-cut run without re-radiation superseded and kept as evidence) with OI-15 for the servo-mount check. Everything else unchanged from v2.1."),
    "revision_history": ["v2.1 (2026-10-12, same day as v2): soak-back wording corrected per lead (240 C is the aluminium lip allowable at 51 MPa; steel judged against its own allowable); lip/case temperatures for the lead's governing cases added (thermal_and_loads.relight_after_coast: TS-1 at relight after the MECO coast with the pressure at that time, TS-2 post-landing soak over 3600 s with times above 150/200/240/300 C); soak-back numbers in the text now read from the data files; gnc.json v2 (published 20:34:31Z, during the first v2.1 write) read: the duty-cycle results apply unchanged (identical F/F_cmd histories), settling recomputed on the v2 cycles, OI-1/2/9/10/11 updated, OI-12 (relight 'purged' wording) and OI-13 (deadband / Pc resolution) added", "v2 (2026-10-12): M2 second pass (supersedes v1)"],
    "status": ("SECOND PASS (M2). Quasi-1D port model with an ASSUMED regression law (band x0.6-1.5), two-CV non-equilibrium "
               "tank, Dyer pintle model with ASSUMED Cd, CEA (RocketCEA) thermochemistry, Bartz BCs, coupled throat "
               "erosion/conduction, 2-D axisymmetric plume CFD. Nothing here is hot-fire validated: the first cold-flow and "
               "static-fire tests (REPORT test plan) measure Cd, regression, eta_c*, ignition delay and erosion."),
    "supersedes": "combustion.json v1 (2026-10-11): v1 numbers for the helical L200 grain are kept in 02-combustion/data/ (v1 files)",
    "units": "SI (m, kg, s, N, Pa, K, J, W) unless the key says otherwise",
    "conventions": ("x_face = axial distance from the injector face toward the nozzle exit [m]. CAD +Z points forward "
                    "(nozzle -> injector), so z_CAD = x_exit_face - x_face. Contour CSV radii are gas-side wall radii. "
                    "Mechanical CAD v3.1: engine aft-most face = insert bottom = exit plane - 3 mm."),
    "inputs_read": {
        "ENGINE-BASELINE-v0.json": "v0",
        "REQUIREMENTS.md": "rev 1 (ENG-02 pintle baseline, 12.5 % stretch) + lead decisions in interfaces/CHANGELOG.md to 2026-10-12",
        "gnc.json": (f"{_ver(os.path.join(IFDIR, 'gnc.json'))} (sha256 {sha(os.path.join(IFDIR, 'gnc.json'))}): requirements (floor, t10-90, slew, "
                     "resolution, deadband, ignition latency, roll threshold, tank), duty cycles v2 (01-systems-gnc/duty_cycles/*_v2.csv); "
                     "gnc.json v1 cycles kept as the comparison set"),
        "gnc_duty_cycles_v2": ("published with gnc.json v2 (hub mtime 2026-10-12 20:34:31Z); the Combustion runs used the 19:15Z working-copy "
                               "snapshot, whose F_N and F_cmd_N histories are identical (max difference 0 N; "
                               "02-combustion/inputs/gnc_v2_published_20261012T2034/MANIFEST.txt)"),
        "mechanical.json": f"{_ver(os.path.join(IFDIR, 'mechanical.json'))} (sha256 {sha(os.path.join(IFDIR, 'mechanical.json'))}) + CHANGELOG notes CAD v3.1/v3.2 / hand calcs v2",
        "electronics.json": f"{_ver(os.path.join(IFDIR, 'electronics.json'))} (sha256 {sha(os.path.join(IFDIR, 'electronics.json'))})",
    },
    "decisions": {
        "chamber_MEOP_Pa": T(4.5e6, "LEAD decision 2026-10-12 (CHANGELOG): basis = pintle full-stroke failure, 30 C tank, Cd 0.8 (data/v2/full_stroke_failure_case_v2.json)"),
        "proof_pressure_Pa": T(6.75e6, "LEAD decision 2026-10-12: 1.5 x MEOP; also covers the blocked-nozzle bound (tank pressure, 63.1 bar at 30 C) below yield"),
        "normal_software_Pc_cap_Pa": T(2.5e6, "LEAD decision 2026-10-12"),
        "ecu_overpressure_abort_Pa": T(3.0e6, "LEAD decision 2026-10-12 (~30 bar, Electronics implements; value approximate until Electronics fixes filter/latency)"),
        "grain_v2": T("centred straight round port, L 0.230 m (S230)", "LEAD decision 2026-10-12 (CHANGELOG): removes the helical-port roll-torque source; grain trade data/v2/grain_trade_v2.csv"),
        "throttle_architecture": T("Servo-driven variable-area pintle (needle-in-seat) at the head end + separate NC main isolation valve upstream (tank side, off-gimbal)",
                                   "LEAD decision 2026-10-11; v2 trade (data/v2/throttle_trade_v2.json) finds no showstopper"),
        "expansion_ratio": T(2.0, "DERIVED v2 re-check with S230 (data/v2/nozzle_perf_v2.csv): attached to 15 % thrust, incipient lip separation at 12.5 % (Schmucker eps_sep 1.94; Summerfield attached), side-load bound < 0.01 N; eps 2.5/3.0 separate at <= 15 %/20 % (bounds 3-11 N)"),
        "fuel": T("ABS (FDM printed, 100 % infill); PETG backup", "REQ founder/LEAD; ABS card c* within +/-0.3 % across compositions/hf sources (cea_cards.py)"),
        "igniter": T(ign['decision'], "DERIVED weighted trade data/v2/ignition_v2.json (torch 0.80, arc-ABS 0.675, pyro 0.64, catalytic 0.525)"),
        "tank_pressurisation": T("Self-pressurised N2O conditioned 15-25 C (heater blanket for cold days, removed at liftoff); N2 supercharge NOT baselined",
                                 "DERIVED data/v2/supercharge_trade_v2.json: N2 pad 60 bar gives +3.4 bar at MECO vs heating to 25 C +4.3 bar; regulated N2 (0.21 L at 300 bar) adds a pressure system for +13 bar"),
        "N2O_load_and_tank": T({"m_N2O_kg": 2.0018, "V_tank_m3": 0.0031700}, "LEAD decision 2026-10-12 (CHANGELOG): 2.00 kg / 3.17 L (85 % fill)"),
    },
    "gas_path": {
        "case": {"material": T("6061-T6 tube", "mechanical.json v1 (Mechanical owns)"), "OD_m": T(0.0635, "mechanical.json v1"), "wall_m": T(0.003175, "mechanical.json v1")},
        "liner_grain_zone": {"thickness_m": T(0.0016, "v1 (grain zone only: the residual web >= 1 mm shields the case)"), "ID_m": T(0.05395, "v1")},
        "post_chamber_insulator": T("phenolic, thickness set by thermal FEA; 1-D bound needs >= 5 mm and still exceeds the 192 C aft-land allowable (open issue OI-4)",
                                    "DERIVED data/v2/soakback_wall_v2.json"),
        "chamber_gas_diameter_m": T(V['D_ch'], "v1 (pre/post-chamber gas-side diameter); changes if the post-chamber insulator thickens (OI-4)"),
        "grain": {
            "material": T("ABS, FDM printed, 100 % infill", "REQ"),
            "outer_diameter_m": T(D_g, C['D_grain'][1]),
            "length_m": T(L_g, C['L_grain'][1]),
            "port": {"type": T("single centred straight round port", "LEAD decision 2026-10-12"),
                     "initial_diameter_m": T(D_p0, C['D_port0'][1]),
                     "initial_web_m": T(r(web0, 5), "DERIVED (OD - port)/2")},
            "density_kg_m3": T(V['rho_f'], C['rho_f'][1] + "; filament 1040"),
            "mass_kg": T(r(m_grain(V['rho_f']), 3), "DERIVED geometry x 1000 kg/m3", range_kg=[r(m_grain(975.0), 3), r(m_grain(1040.0), 3)],
                         range_note="975-1040 kg/m3 (printed parts .. filament); weigh every grain"),
            "regression_law": {"form": "r = a * G_ox^n (oxidiser-flux law, local G_ox along the port)",
                               "a": T(V['a'], C['a'][1]), "n": T(V['n'], C['n'][1]),
                               "note": "No verified N2O/ABS law in accessible literature; every result is checked at x0.6 and x1.5 on a. Static fires T1-T2 measure it."},
            "x_face_start_m": T(V['L_pre'], "DERIVED"), "x_face_end_m": T(V['L_pre'] + L_g, "DERIVED"),
            "residual_web_rule": T("web >= 1 mm at the x1.5 regression bound for every flight duty cycle", "DERIVED: ABS thermal layer kappa/r 0.1-0.3 mm (soakback_v2.json grain_zone); >= 1 mm shields the case"),
            "retention": "forward face on the pre-chamber insulator shoulder, aft face on the post-chamber insulator; anti-rotation key (Mechanical)",
        },
        "pre_chamber": {"length_m": T(V['L_pre'], C['L_pre'][1]), "diameter_m": T(V['D_ch'], "v1")},
        "post_chamber": {"length_m": T(V['L_post'], C['L_post'][1]), "diameter_m": T(V['D_ch'], "v1")},
        "injector": {
            "type": T("pintle (needle-in-seat), unchanged from v1", "LEAD 2026-10-11"),
            "seat_diameter_m": T(0.0055, "v1"), "stroke_m": T(0.004, "v1"), "Cd": T(V['Cd'], C['Cd'][1]),
            "Cd_acceptance": T("Cd_eff (vs Dyer) >= 0.41 measured in N2O cold flow keeps the 15 C ceiling >= 500 N (HEM-like worst case, data/v2/injector_compare_v2.json)", "DERIVED"),
            "flow_model": "Dyer et al. AIAA 2007-5702 (SPI/HEM blend); HEM and SPI bound it (G ratio 0.55-0.68 and 1.34-1.45 at 15 C)",
            "filter": T("sintered <= 15 um, Cv >= 2.2", f"DERIVED: seat gap at the 12.5 % floor = lift {m50.loc[0.125, 'lift_m']*1e3:.3f} mm x sin 15 deg = {gap_floor*1e6:.0f} um; filter <= 1/3 of the smallest gap; Cv from the line budget (feed_line_checks_v2.json); v1 said 40 um"),
        },
        "nozzle": {
            "throat_diameter_m": T(r(2 * Rt, 6), "v1 geometry (data/v2/nozzle_contour_v2.csv)"),
            "exit_diameter_m": T(r(2 * Re_, 6), "v1 geometry"), "expansion_ratio": T(2.0, "see decisions"),
            "throat_area_m2": T(r(At, 9), "DERIVED"),
            "contour_csv": H('nozzle_contour_v2.csv'),
            "x_face_throat_m": T(r(x_t, 5), "DERIVED (contour v2: +30 mm vs v1)"), "x_face_exit_m": T(r(x_e, 5), "DERIVED"),
            "pe_over_pa_at_max": T(r(pe_pa_max, 3), "CEA shifting, S230 max point (nozzle_perf_v2.csv)"),
            "graphite": T("isomolded/extruded fine-grain graphite, bulk density >= 1.80-1.85 g/cm3, ash <= 0.1 %; grade TO-QUOTE (Sønderborg DK-6400)", "DERIVED (erosion model sensitivity to density/porosity)"),
            "insert_envelope_note": "Mechanical CAD v3.1: 44 mm OD + 30 x 6.5 mm aft spigot through a 6 mm lip; gas side unchanged (erosion/soak models used the 44 x 32 mm v3.0 slice)",
        },
        "pc_tap": {"location": T("head top (Mechanical 2026-10-12) via sense line to the fixed side", "mechanical CHANGELOG"),
                   "sense_line": T("1/8 in OD (1.6 mm ID) SS, length <= 0.3 m, transducer dead volume <= 0.3 cm3",
                                   "DERIVED data/v2/feed_line_checks_v2.json: lowest f_n per length (dead volume 0.1-0.5 cm3) " + json.dumps(sl) + f" Hz; phase lag <= {lag50:.2f} deg at 50 Hz")},
        "overall": {
            "gas_path_length_injector_face_to_exit_m": T(r(x_e, 4), "DERIVED"),
            "free_chamber_volume_initial_m3": T(r(V_free, 7), "DERIVED (pre + post + convergent + initial port)"),
            "L_star_initial_m": T(r(Lstar, 3), "DERIVED V_free / A_t"),
        },
    },
    "operating_points": {
        "basis": "20 C saturated tank (P_tank 50 bar row of the map for lift and dP/Pc), initial port 25 mm, nominal law. " + SIM,
        "max_thrust": {"F_N": T(r(mx['F'], 1), SIM), "Pc_Pa": T(r(mx['Pc'], 0), SIM), "mdot_ox_kg_s": T(r(mx['mox'], 5), SIM),
                       "mdot_fuel_kg_s": T(r(mx['mf'], 5), SIM), "mdot_total_kg_s": T(r(mx['mox'] + mx['mf'], 5), SIM),
                       "OF": T(r(mx['OF'], 3), SIM + " (v1 helical 7.76: the straight port burns less fuel)"),
                       "Isp_SL_s": T(r(mx['Isp'], 1), SIM),
                       "cstar_delivered_m_s": T(r(st100['cstar_delivered_m_s'], 1), "CEA x eta_c* 0.92 (chamber_port_state_v2.json)"),
                       "Tc_ideal_K": T(r(st100['Tc_K'], 0), "CEA"), "T0_delivered_K": T(r(st100['T0_delivered_K'], 0), "CEA x eta_c*^2"),
                       "gamma_chamber": T(r(st100['gamma'], 4), "CEA"), "MW_chamber": T(r(st100['MW'], 2), "CEA"),
                       "G_ox_initial_kg_m2s": T(r(st100['G_ox_head_kg_m2s'], 0), SIM),
                       "pintle_lift_m": T(r(m50.loc[1.0, 'lift_m'], 6), SIM), "dP_inj_over_Pc": T(r(m50.loc[1.0, 'dP_over_Pc'], 3), SIM)},
        "throttle_points_20C_initial_port": tp,
        "throttle_map_csv": H('engine_S230/throttle_map_v2.csv'),
        "throttle_map_note": "map axes: P_tank 35-55 bar x D_port 25-45 mm x fraction 0.125-1; ceiling column = min(stroke 4 mm, dP/Pc >= 0.25)",
        "floor_requirement_25pct": {"F_N": T(125.0, "REQ"), "Pc_Pa": T(r(ops[4]['Pc'], 0), SIM), "OF": T(r(ops[4]['OF'], 2), SIM), "status": "met (dP/Pc 5.8)"},
        "floor_target_20pct": {"F_N": T(100.0, "REQ"), "Pc_Pa": T(r(ops[5]['Pc'], 0), SIM), "OF": T(r(ops[5]['OF'], 2), SIM), "status": "met (dP/Pc 7.1)"},
        "floor_stretch_12p5pct": {"F_N": T(62.5, "REQ stretch"), "Pc_Pa": T(r(ops[7]['Pc'], 0), SIM), "OF": T(r(ops[7]['OF'], 2), SIM),
                                  "status": ("model meets it: dP/Pc 10.4, chug gain margin 38.6 at 10 ms delay, attached nozzle except incipient lip "
                                             "separation (Schmucker); G_ox 74 -> ~25 kg/m2s as the port opens: low-flux combustion efficiency/"
                                             "stability is UNVERIFIED (static fire T3)")},
        "pressure_limits": {"chamber_MEOP_Pa": T(4.5e6, "LEAD 2026-10-12"), "proof_Pa": T(6.75e6, "LEAD 2026-10-12"),
                            "normal_cap_Pa": T(2.5e6, "LEAD 2026-10-12"), "abort_Pa": T(3.0e6, "LEAD 2026-10-12 (~30 bar)"),
                            "blocked_nozzle_bound_Pa": T(6.308e6, "CoolProp Psat at 30 C (full_stroke_failure_case_v2.json)"),
                            "full_stroke_failure_S230": T([dict(T_tank_C=x['T_tank_C'], Cd=x['Cd'], Pc_bar=x['Pc_full_stroke_bar'], F_N=x['F_N']) for x in fs],
                                                          "SIM grain_q1d v2 steady, initial port (full_stroke_failure_case_v2.json)"),
                            "full_stroke_failure_S230_max_bar": T(fs_max['Pc_full_stroke_bar'] if fs_max else None, "SIM (30 C, Cd 0.8)")},
        "thrust_ceiling_rule": T("F_ceiling = F at min(stroke 4 mm, injector dP/Pc >= 0.25)", "DERIVED stiffness rule (stability section)"),
        "ceiling_vs_Cd_20C_and_models": T(f"ceiling {min(x['F_ceiling_N'] for x in cvc):.0f}-{max(x['F_ceiling_N'] for x in cvc):.0f} N for Cd 0.5-0.8 at 20 C (Dyer); worst model case {cw_min['model']} at {cw_min['T_tank_C']:.0f} C, Cd {cw_min['Cd_nominal']}: {cw_min['F_ceiling_N']:.0f} N (Cd_eff {cw_min['Cd_eff_vs_Dyer']:.3f})", "SIM injector_compare_v2.json"),
        "max_thrust_hold_baseline_tank": {
            "csv": H('ceiling_vs_time_BLtank_v2.csv'),
            "t_500N_held_s": T([r(ceilB.t_500N_held_s.min(), 2), r(ceilB.t_500N_held_s.max(), 2)], "SIM 15-25 C, eq/neq E 100/1000 tank (min, max)"),
            "t_liquid_depletion_s": T([r(ceilB.t_liquid_depletion_s.min(), 2), r(ceilB.t_liquid_depletion_s.max(), 2)], "SIM (non-eq tank keeps a 0.011 kg residual)"),
            "F_ceiling_at_0s_N": T({f"{int(t)}C": r(ceilB[ceilB.T0_C == t].F_ceiling_at_0s_N.iloc[0], 1) for t in (15, 20, 25)}, "SIM"),
            "F_ceiling_at_liquid_end_N": T([r(ceilB.F_ceiling_at_liquid_end_N.min(), 1), r(ceilB.F_ceiling_at_liquid_end_N.max(), 1)], "SIM"),
            "impulse_to_liquid_end_Ns": T([r(ceilB.impulse_to_liquid_depletion_Ns.min(), 0), r(ceilB.impulse_to_liquid_depletion_Ns.max(), 0)], "SIM"),
            "ox_to_liquid_end_kg": T([r(ceilB.ox_used_to_liquid_end_kg.min(), 3), r(ceilB.ox_used_to_liquid_end_kg.max(), 3)], "SIM")},
        "max_thrust_hold_gnc_v1_tank_1p30kg": {"csv": H('ceiling_vs_time_v2.csv'),
                                               "t_500N_held_s": T([r(ceilA.t_500N_held_s.min(), 2), r(ceilA.t_500N_held_s.max(), 2)], "SIM")},
        "tank_pressure_range_Pa": T([4.50e6, 5.65e6], "CoolProp Psat 15-25 C (n2o_validation_v2.json: CoolProp vs ESDU <= 0.98 % to 300 K)"),
        "tank_MEOP_Pa": T(7.0e6, "LEAD v0"),
        "chamber_fill_time_constant_s": T(r(tau_fill, 4), "DERIVED L*/(c*_del Gamma^2); step-response fit 0.004 s (1 ms sampling)"),
    },
    "valves_and_actuators": {
        "architecture": "tank -> NC main isolation valve (off-gimbal) -> -6 PTFE-lined braided hose across the gimbal -> <= 15 um filter -> pintle injector (on gimbal)",
        "isolation_valve": {"Cv_min": T(3.0, f"DERIVED feed budget (feed_line_checks_v2.json): valve Cv 3 + filter Cv 2.2 give {bud['total_dp_Cv3_valve_Cv2p2_filter_Pa']/1e5:.2f} bar total at 0.26 kg/s vs the {bud['budget_at_0p26_Pa']/1e5:.2f} bar budget; Cv 1.5 + Cv 1.0 give {bud['total_dp_Cv1p5_valve_Cv1_filter_Pa']/1e5:.2f} bar"),
                            "MEOP_Pa": T(7.0e6, "LEAD"), "close_time_max_s": T(0.15, "DERIVED"),
                            "trapped_liquid_relief": T("required (<= 7.5 MPa) between the isolation valve and the pintle", "v1 / mechanical.json v1")},
        "hose": T(f"-6 accepted: {v_nom:.1f} m/s at 0.241 kg/s nominal, {min(v_hose):.1f}-{max(v_hose):.1f} m/s at 0.26 kg/s (15-25 C); hose friction {min(dpf)/1e3:.0f}-{max(dpf)/1e3:.0f} kPa; slow-closure surge (40-150 ms, 0.4-0.8 m line) {min(surge)/1e3:.0f}-{max(surge)/1e3:.0f} kPa",
                  "DERIVED feed_line_checks_v2.json (answers Mechanical REQUEST 2026-10-12)"),
        "priming_rule": T(feed['priming']['requirement'], "DERIVED: isentropic compression bound N2 847-913 K, N2O vapour 614-646 K at 45-60 bar (feed_line_checks_v2.json)"),
        "pintle_actuator": {"stroke_m": T(0.004, "v1"),
                            "full_stroke_time_s": T(None, "RETIRED v2.2 (2026-10-12): the v1 value 0.08 s (50 mm/s) was DERIVED from the v1 ENG-03 throttle-response target (10-90 % <= 100 ms), not from combustion physics. The drive is sized by gnc.json v2 requirements.throttle (t10-90 <= 0.15 s, slew >= 2 F_max/s) and ENG-05 with the lead resolution of 2026-10-12 (pre-MECO throttle-down to <= 75 %); see speed_checks", retired_value_s=0.08),
                            "speed_checks": T(speed_block, "SIM grain_q1d v2 + DERIVED (actuator_rate_check_v2.json, src/actuator_rate_check.py, figs/v2/actuator_rate_check_v2.png)",
                                              file=H('actuator_rate_check_v2.json'), conclusion=act_txt, eng05=eng05_txt, eng04_floor_start=eng04_txt,
                                              lead_resolution="2026-10-12 (CHANGELOG): 0.08 s retired, Combustion condition for the HV69 closed; ENG-05 met by a GNC pre-MECO throttle-down to <= 75 % (0.25 s full stroke then gives 0.082 s), torsion spring sized to assist closing, closing time at 25 bar measured in B-PNT-1; ENG-05 wording unchanged"),
                            "position_resolution_m": T(1e-5, f"v1; v2 check: at the 12.5 % floor dF/dh = {fl['dF_dh_N_per_m']/1e3:.0f} N/mm (plant fit), so 2 % of 500 N needs {dh_2pct_FS*1e6:.0f} um and 2 % of the floor thrust {dh_2pct_floor*1e6:.1f} um (the closed Pc loop then rests on Pc resolution); gnc.json v2: resolution 2 % F_max (ENG-03), deadband <= 0.5 % F_max = {db_100_um:.0f} um at 100 % and {db_floor_um:.1f} um at 12.5 % open-loop, closed Pc loop required"),
                            "force_basis_note": "v1 force envelope was computed at the v1 MEOP (31 bar chamber); the needle force depends on feed pressure (tank MEOP 70 bar unchanged) and Pc: re-check with the 45 bar chamber MEOP in the pintle CAD (open item)"},
        "plant_model_valve_to_Pc": {
            "form": "Pc(s)/h(s) = K_h [ (1 - phi)/(tau_c s + 1) + phi/(tau_f s + 1) ]   (h = pintle lift; fast chamber filling + slow fuel/thermal-lag mode)",
            "fit": T([dict(fraction=x['frac'], h0_m=r(x['h0_m'], 6), K_h_Pa_per_m=r(x['K_h_Pa_per_m'], -3), phi=r(x['phi'], 3), tau_c_s=x['tau_c_s'],
                           tau_f_s=x['tau_f_s'], dF_dh_N_per_m=r(x['dF_dh_N_per_m'], 0)) for x in plant],
                     "SIM grain_q1d v2 +3 % lift step, tank frozen at 50.5 bar (engine_S230/plant_valve_to_pc_v2.json)"),
            "tau_d_s": T([0.003, 0.010], "ASSUMED injection/vaporisation delay (v1)"),
            "note": "K_h grows 2.7x from 100 % to 12.5 % (gain scheduling or a closed Pc loop needed); the slow mode is 5-9 % of the static gain"},
    },
    "igniter": {
        "type": T("spark-ignited N2O/propane torch, radial into the pre-chamber", "ignition_v2.json"),
        "torch_sizing": T({k: (r(v, 6) if isinstance(v, float) else v) for k, v in ign['torch']['sizing'].items() if not isinstance(v, (list, dict))}, "DERIVED/CEA ignition_v2.json"),
        "N2O_orifice_d_m": T(1.31e-4, "DERIVED Dyer at 20 C, Cd 0.65 ASSUMED (0.128-0.137 mm for 10-25 C)"),
        "propane_orifice_d_m": T(2.54e-4, "DERIVED at 20 C, Cd 0.80 ASSUMED; calibrate both by weighing"),
        "envelope": T(ign['torch']['envelope'], "DERIVED (answers Mechanical REQUEST 2026-10-12)"),
        "electrical": T(ign['torch']['electrical'], "DERIVED; electronics.json v1 IGN_HV coil mode + SOL1/SOL2"),
        "mass_kg": ign['torch']['mass_estimate_kg'],
        "sequence": T(ign['sequence'], "DERIVED ignition_v2.json; verify by torch and static-fire tests"),
        "model_transients": T(ign['model_transients'], "SIM"),
        "starts_per_flight": T(">= 3; limited by propane (0.055 g/start) and N2O torch flow (0.30 g/start)", "DERIVED"),
    },
    "thermal_and_loads": {
        "thermal_bc_csv": {k: H(v['file']) for k, v in pts.items()},
        "thermal_bc_columns_note": "Bartz h_g (cold wall 600 K) with T_aw, plus q_rad_band (0.10-0.65 MW/m2, gas radiation band) and h_g_eqprops (equilibrium-property variant, ~x3, UPPER bound); use the x0.5-2 band for FEA sensitivity",
        "peak_convective_heat_flux_W_m2": T(pts['max']['peak_q_conv_Tw600_W_m2'], "SIM Bartz at the throat, wall 600 K, max thrust, S230 (thermal_bc_summary_v2.json)"),
        "peak_h_g_W_m2K": T(pts['max']['peak_h_g_Tw600_W_m2K'], "SIM"),
        "T_aw_throat_K": T(pts['max']['T_aw_at_peak_K'], "SIM"),
        "peak_flux_by_point_W_m2": T({k: v['peak_q_conv_Tw600_W_m2'] for k, v in pts.items()}, "SIM"),
        "peak_incident_flux_cold_wall_transient_W_m2": T([27.12e6, 31.55e6], "SIM coupled insert model at start (wall near ambient), nominal/conservative (erosion_S230/erosion_dc_v2.json)"),
        "throat_erosion_per_flight": T(er, "SIM coupled erosion model (nominal/conservative kinetics) + literature-scaled band; S230 over gnc.json v1 duty cycles"),
        "throat_replacement_rule": T("replace the insert when dA_t/A_t reaches 5 % (measured pin gauge / bore scan after each firing)", "DERIVED"),
        "flights_per_insert_A1": T([r(flights_cons, 1), r(flights_nom, 1)], "DERIVED 5 % / (dAt per A1 flight): conservative, nominal kinetics"),
        "insert_soakback": T({"retainer_0p15kg_peak_K": al_pk, "conclusion": soak_concl,
                              "sensitivity_csv": H('soakback_sens_v2.csv') if sens else "pending",
                              "sensitivity_summary": sens_txt},
                             "SIM lumped/1-D (soakback.py, soakback_sens.py); Mechanical thermal FEA supersedes"),
        "wall_soakback_post_chamber": T({k: dict(T_case_peak_K=r(v['T_case_peak_K'], 0), t_peak_s=r(v['t_peak_s'], 0)) for k, v in ws.items()},
                                        "SIM 1-D slab, no char credit, h_g x1/x2 (soakback_wall_v2.json)"),
        "relight_after_coast": T(relight_block, "SIM soakback_relight.py (lumped insert/retainer + 1-D wall, coasts adiabatic = conservative); Mechanical FEA supersedes"),
        "head_end_bc": T(head_block, "DERIVED headend_thermal_v2.py v2.2b (BC time series per DC + lumped/1-D first-cut bound); Mechanical thermal FEA supersedes the bound",
                         summary=head_txt, servo_mount_implication=head_impl, json=H('headend_thermal_v2.json'), figure=os.path.join(HUB, 'figs', 'v2', 'headend_thermal_v2.png')),
        "grain_mass_kg": T(r(m_grain(V['rho_f']), 3), "DERIVED"),
        "roll_torque": T("helical-port swirl source removed by the straight port; residual roll torque (injector/print asymmetry) is UNKNOWN: measure at static fire T1 (lead rule: RCS deleted only if |roll torque| <= 0.02 N m)", "LEAD/DERIVED"),
        "thrust_misalignment": T("not quantified (asymmetric regression of a printed grain); measure at T1 with a 6-axis stand or two load cells", "UNKNOWN"),
        "max_thrust_case_csv": H('engine_S230_BL/maxthrust_BLtank_neqE1e+03_T20C.csv'),
    },
    "stability": {
        "criteria": "injector dP/Pc >= 0.25 everywhere (ceiling rule); chug gain margin from the lumped feed/chamber model; acoustic modes far above the actuator band",
        "points_initial_port": T({k: dict(dP_over_Pc=r(v['dP_over_Pc'], 2), GM_tau5ms=r(v['GM_tau5ms'], 1), GM_tau10ms=r(v['GM_tau10ms'], 1),
                                       f_1L_Hz=r(v['f_1L_Hz'], 0), f_Helmholtz_Hz=r(v['f_Helmholtz_pre_post_Hz'], 0), f_1T_chamber_Hz=r(v['f_1T_chamber_Hz'], 0),
                                       f_thermal_lag_Hz=r(v['f_thermal_lag_Hz'], 2)) for k, v in stab0.items()},
                                 "SIM stability.py v2 (stability_v2.json)"),
        "hybrid_LF_note": "classical hybrid low-frequency (thermal-lag/boundary-layer) instability 0.3-2 Hz band is identified but its amplitude is NOT predicted; static fire T2/T3 with 1 kHz Pc logging",
    },
    "duty_cycle_results": {
        "gnc_v1_cycles_S230": T(dc_v1, "SIM grain_q1d v2 over gnc.json v1 duty cycles (grain_trade_v2.csv); A1 x0.6: cumulative O/F 15.9 exceeds the CEA table range (instantaneous O/F clamped at 14)"),
        "gnc_v2_cycles_S230": T(wrows, "SIM grain_q1d v2 over the gnc.json v2 duty cycles (published 2026-10-12 20:34Z; run on the 19:15Z working-copy snapshot with identical F/F_cmd histories, inputs/gnc_v2_published_20261012T2034/MANIFEST.txt)"),
        "ground_grain_counts": T({"DC-C": 2, "DC-D": 3}, "SIM one S230 grain burns through at 46.4 s (C) and 24.1 s (D) of sim time (engine_S230/summary_v2.json)"),
        "reserve_check": T(f"liquid left / ox used {min(w['liquid_left_over_used'] for w in wrows):.2f}-{max(w['liquid_left_over_used'] for w in wrows):.2f} (gnc.json v2 cycles, incl. x0.6/x1.5) vs the gnc.json usable-liquid reserve rule >= 0.20 x used (+0.03 residual fraction): met", "DERIVED"),
    },
    "settling_and_relight": T({k: dict(coast_s=v['coast_s'], settled_interval_before_relight_s=v['settled_interval_before_relight_s'],
                                        t_settle_estimate_s=v['t_settle_estimate_s'], Bond=v['Bond'])
                               for k, v in {**settle, **(J('settling_v2wip_preview.json') if os.path.exists(os.path.join(DV, 'settling_v2wip_preview.json')) else {})}.items()},
                              "DERIVED settling_v2.json (gnc.json v1 cycles) + settling_v2wip_preview.json (gnc.json v2 cycles; computed on the 19:15Z snapshot, acceleration "
                              "differences to the published files <= 1e-4 m/s2): the shortest settled interval before relight is A2 (3.1 s v1, 2.2 s v2) vs a "
                              "0.5-0.6 s settle estimate"),
    "open_interface_issues": [],
    "unknowns_and_open_items": [
        "N2O/ABS regression law (a, n) and its band: static fires T1-T2.",
        "Pintle Cd (N2O two-phase) at all lifts: water then N2O cold flow; acceptance Cd_eff >= 0.41.",
        "eta_c* of the straight port at O/F 4-10 (assumed 0.92, band 0.85-0.96).",
        "Low-flux combustion at the 12.5 % stretch floor (G_ox ~25-74 kg/m2s).",
        "Ignition delay with the torch (assumed 0.10 s torch-to-main + 30 % preheat).",
        "Graphite grade, density and erosion kinetics: post-fire bore measurement.",
        "Residual roll torque and thrust misalignment of the straight port: T1.",
        "Plume afterburning and radiation: CFD gives fast-chemistry bounds only (05-plume-cfd).",
        "Head-end gas temperature and heat transfer (the bound uses T_aw = delivered T0 and Bartz outside its validity): face-disc, head-top, bracket and servo-case thermocouples at T1.",
        "Pintle closing time under load at 25 bar and MEOP (HV69 + torsion spring): bench test B-PNT-1.",
    ],
    "files": {
        "hub_root": HUB, "canonical_root": MOUNT,
        "src": os.path.join(HUB, 'src'), "data_v2": os.path.join(HUB, 'data', 'v2'), "data_v1": os.path.join(HUB, 'data'),
        "figs_v2": os.path.join(HUB, 'figs', 'v2'), "plume_cfd": os.path.join(os.path.dirname(HUB), '05-plume-cfd'),
        "report": "02-combustion/REPORT.md (text delivered to the lead in the handback; the harness blocks subagent report files)",
    },
}

OI = [
    dict(id="OI-1", with_="Space/GNC + lead", issue="gnc.json v2 duty cycles size A2 at 2.54 kg and B1 at 2.44 kg N2O (B2 1.81 kg), above the lead baseline 2.00 kg / 3.17 L that A1 uses. The engine flies all of them (ceiling never limits, min ceiling 556-598 N, min dP/Pc 0.55-0.80) but the tank is one part.",
         action="GNC re-runs A2/B1 on the 3.17 L tank or the lead re-opens the tank size."),
    dict(id="OI-2", with_="Space/GNC", issue="gnc.json v2 flies the combustion.json v1 map x relay factors (its scripts switch to the v2 map automatically) and shows an open-loop case with phi 0.1 at P 0.982. v2 plant: tau_c 4 ms, slow fuel mode phi 0.05-0.09 with tau_f 0.11-0.53 s (0.3-1.5 Hz, inside the 2.3 Hz Pc-loop bandwidth of gnc.json v2), K_h x2.7 from 100 % to 12.5 %; relight 10/90 % at 0.10/0.29 s in the model vs ENG-04 <= 0.5 s (planning value 0.6 s). v2.2: " + eng04_txt,
         action="GNC re-runs the MC on throttle_map_v2.csv + plant fit (gain-scheduled K_h); ignition latency and repeatability (+/-50 ms) are measured at T1/T3. v2.2 (lead 2026-10-12): GNC confirms the relight start level and that the MC start-delay dispersion covers >= 0.53 s; ENG-04 stays, the 12.5 % floor start is logged as marginal."),
    dict(id="OI-3", with_="Mechanical", issue="Grain is L 0.230 m, 0.404 kg at 1000 kg/m3 (0.394-0.420); CAD v2 shows 0.369 kg (L 0.200). Gas path 0.3386 m (v1 0.3086).",
         action="CAD v3.x carries S230 and the v2 contour; mass budget update."),
    dict(id="OI-4", with_="Mechanical", issue="Post-chamber wall 1-D bound: case peak 220-269 C (A1) and 360-426 C (B1) behind 5 mm phenolic, 287-354 C (A1) behind 3 mm, vs aft-land T_allow 192 C. The model has no char credit and no 2-D heat sink.",
         action="Thermal FEA with thermal_bc_*_v2.csv (x0.5-2 band) and the DC histories; insulator thickness and material from FEA. v2.2: the pre-chamber wall (1.6 mm TC-06) is in the same position, see OI-15 and thermal_and_loads.head_end_bc."),
    dict(id="OI-5", with_="Mechanical", issue=("Insert retention lip vs soak-back. " + soak_concl + "." + rl_txt +
                                              " Governing cases per lead 2026-10-12: TS-1 temperature at relight after the MECO coast with Pc 25 bar "
                                              "(normal) and 45 bar (MEOP); TS-2 post-landing soak, unloaded, over-ageing of 6061-T6 for reuse."),
         action=("Mechanical: retainer material/mass/interlayer choice; TS-1 from T_at_relight_K / T_max_landing_burn_K with Pc_at_Tmax_landing_burn_Pa "
                 "(coast and relight time explicit in the DC CSVs data/v2/dc_g3/*.csv, data/v2/dc_gncv2wip/*.csv); TS-2 from the soak times above "
                 "150/200/240/300 C; thermal FEA of the v3.1/v3.2 insert supersedes these lumped bounds.")),
    dict(id="OI-6", with_="Electronics", issue=f"Pc transducer 0-34.5 bar (electronics.json v1) vs chamber MEOP 45 bar, proof 67.5 bar and full-stroke failure Pc up to {fs_max['Pc_full_stroke_bar']:.1f} bar (S230, 30 C, Cd 0.8; {fs20['Pc_full_stroke_bar']:.1f} bar at 20 C, Cd 0.7): the ~30 bar abort is inside the range, the failure transient saturates.",
         action="Electronics selects 0-69 bar (or confirms the 34.5 bar part survives 67.5 bar proof and accepts saturation); ignition check needs <= 0.1 bar resolution at 3 bar."),
    dict(id="OI-7", with_="Electronics/Mechanical", issue="Isolation valve Cv >= 3 (v1 said 1.5) and filter <= 15 um with Cv >= 2.2 (v1 said 40 um) to stay inside the 2.7 bar line budget used by every v2 simulation.",
         action="Component selection with datasheet Cv; TO-QUOTE (Sønderborg DK-6400)."),
    dict(id="OI-8", with_="Electronics", issue="Torch flame confirmation (photodiode or 0.25 mm TC) and the priming rule (pintle bleed lift 0.10 mm before the isolation valve opens on an unprimed line, valve opening ramp >= 0.3 s).",
         action="ECU sequence implements ignition_v2.json; sensor selection."),
    dict(id="OI-9", with_="Space/GNC + lead", issue="Roll torque: helical source removed; residual unknown. gnc.json v2: RCS-off threshold 0.03 N m (no significant landing loss); the lead rule (delete the RCS provision only if T1 measures <= 0.02 N m) is inside it.",
         action="T1 roll-torque measurement with a stand resolution well below 0.02 N m."),
    dict(id="OI-10", with_="Space/GNC", issue="Residual web at x1.5 regression: B1 is the limiting cycle (1.31 mm on gnc.json v2 B1, 0.94 mm on gnc.json v1 B1) against the >= 1 mm rule.",
         action="Keep B1 within 19 s of burn or accept a longer grain after T1-T2 measure the law."),
    dict(id="OI-11", with_="Mechanical", issue="Pintle needle force envelope was sized at the v1 31 bar chamber MEOP; with 45 bar the closing-direction pressure force at shutdown changes; CAD v3.2 adds a torsion-spring spring-to-close with backlash preload.",
         action="Re-check servo/linkage force with Pc 0-45 bar, feed 0-70 bar and the spring preload; the spring must still close the needle against the opening pressure force at MEOP. v2.2: per the lead ENG-05 resolution the spring is also sized to assist the closing speed (closing time at 25 bar measured in B-PNT-1)."),
    dict(id="OI-12", with_="Space/GNC + Electronics", issue="gnc.json v2 relight conditions say 'chamber purged'; combustion carries no purge gas in flight (ignition_v2.json): the chamber vents passively through the nozzle during the 11-22 s coast with the pintle seated.",
         action="Read 'purged' as 'vented': the ECU checks Pc within 0.1 bar of ambient before the torch fires (arm precondition); N2 purge is a ground-test procedure only."),
    dict(id="OI-13", with_="Electronics + Mechanical", issue=f"gnc.json v2 asks deadband <= 0.5 % F_max (2.5 N), resolution 2 % F_max and a closed Pc loop. Open-loop this is {db_100_um:.0f} um of pintle lift at 100 % and {db_floor_um:.1f} um at the 12.5 % floor (plant dF/dh); closed-loop it is {db_Pc_100_bar:.2f} bar of Pc at 100 % and {db_Pc_floor_bar:.2f} bar at the floor.",
         action="Pc measurement noise/resolution <= 0.1 bar over 0-25 bar (with OI-6 range); pintle drive backlash/hysteresis small against the closed-loop authority (spring preload, CAD v3.2); bench test with the measured plant."),
    dict(id="OI-14", with_="Space/GNC + Electronics + Mechanical (lead decided 2026-10-12)", status="RESOLVED by the lead; implementation open",
         issue="Pintle full-stroke 0.08 s retired (no combustion basis). " + eng05_txt,
         action="Lead decision 2026-10-12: GNC guidance throttles down to <= 75 % before MECO; torsion spring sized to assist closing; closing time at 25 bar measured in B-PNT-1; ENG-05 wording unchanged. Combustion: re-run the tail-off with the measured closing curve when B-PNT-1 reports."),
    dict(id="OI-15", with_="Mechanical (+ Electronics for the servo rating)",
         issue="Head-end thermal BC for the HV69 in-line pintle drive (rated -10..60 C; mount limit 50 C in flight incl. relight): " + head_txt,
         action="Mechanical thermal FEA of the head TC-02, bonnet TC-04, bracket TC-12 and servo with thermal_and_loads.head_end_bc (headend_bc_<DC>_v2.csv, x0.5-2) over burn, MECO coast, relight and the 3600 s soak. " + head_impl),
]
for o in OI:
    o['with'] = o.pop('with_')
J2['open_interface_issues'] = OI

json.dump(J2, open(OUT, 'w'), indent=1, ensure_ascii=False, default=float)
print('wrote', OUT, os.path.getsize(OUT), 'bytes; L* %.3f m, V_free %.3e m3, grain %.3f kg, tau_fill %.4f s' % (Lstar, V_free, m_grain(V['rho_f']), tau_fill))
