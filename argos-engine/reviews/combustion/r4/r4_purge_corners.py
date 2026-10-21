"""REV-COMB-4 reviewer sensitivity: needed purge flow time of the decided path (2 x 0.707 mm, both taps) at the 283.15 / 289.5 /
297.15 K tank states (CHANGELOG 253 (7)(ii): is a 2.43 s flow adequate at the three temperature corners?).

Method (DERIVED by the reviewer; NOT a Combustion record): runs an unmodified COPY of the author's retained_vapour_v341_v2p4.main
(02-combustion/src, copy sha16s asserted equal to the originals) on the author's v2.4 inputs, reduced exactly as purge_duration_v2p4
(robust Tp = smallest grid Tp from which every longer grid Tp gives P_abort <= 1e-3 over every heat case, reading, element model and
azimuth at 0 and 2 deg, max of the 'paused' and 'restart' conventions, worst of the five GNC coast series).  Only the tank-state
quantities are changed, through module constants and a modified copy of relight_vapour_order_v2p4.json in a scratch data dir:
  tap fluxes G_L (Dyer liquid) and G_V (HEM vapour) scaled by the author's own two-tap rates r_liq / r_vap at each state
    (purge_basis_line216_v2p4b.json uncertainty.tank_state; 289.5 K law 31.2416 / 8.4916 g/s);
  rho_l, rho_v, h_fg, vapour and liquid cm3 per J: CoolProp HEOS saturated N2O at the state;
  pintle vapour purge s/cm3 scaled by the inverse vapour volumetric flux ratio, liquid-plug dead time s/cm3 by the inverse liquid
    volumetric flux ratio (ASSUMED: the C7 SIM basis and the 35.0 g/s ignition-lift flow scale with the Dyer / HEM flux);
  NOT changed (ASSUMED, stated): the coast heat (segment_heat), the coast migration timings, the E1 -> E2 liquid-line latency sample
    (start_latency at the A1 state), the GNC 300 m era coast series (the 210 m relight state is MISSING, OI-49).
The 289.5 K run uses the author's original files and constants and must reproduce purge_duration_v2p4.json (asserted).
Tags: DERIVED sensitivity on the author's SIM/DERIVED model; a repeat of a computation, not physical evidence.
usage: python -B -I r4_purge_corners.py SRC_DIR SRC_COPY_DIR DATA_V2P4_DIR SCRATCH_DIR OUT_JSON
"""
import gzip, hashlib, json, math, os, sys, time
sys.dont_write_bytecode = True
src_dir, copy_dir, data_dir, scratch, out_f = sys.argv[1:6]
H16 = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
for fn in sorted(os.listdir(src_dir)):
    if fn.endswith('.py'):
        assert H16(os.path.join(src_dir, fn)) == H16(os.path.join(copy_dir, fn)), fn
sys.path.insert(0, copy_dir)
import numpy as np
import CoolProp.CoolProp as CP
import retained_vapour_v341_v2p4 as RV

t0 = time.time()
base = json.load(open(os.path.join(data_dir, 'retained_vapour_v341_v2p4.json')))
bi = base['inputs']
for k in ('segment_heat_v341_v2p4.json', 'relight_vapour_order_v2p4.json', 'coast_migration_v2p4.json', 'start_latency_v2p4.json',
          'post_abort_pocket_v2p4.json'):
    assert H16(os.path.join(data_dir, k)) == bi[k], k
files = [bi['mech_budget'], bi['mech_traps_v341'], bi['mech_drain_pose_v341 (workdir)'], bi['mech_bleed_taps_v341 (workdir)'],
         bi['gnc_series'], bi['gnc_relight_attitude_v1']]
for f in files:
    assert H16(f['file']) == f['sha256_16'], f['file']
PD = json.load(open(os.path.join(data_dir, 'purge_duration_v2p4.json')))
assert H16(os.path.join(data_dir, 'purge_duration_v2p4.json')) == '1ff6bfcd7d2f454c'
VO0 = json.load(open(os.path.join(data_dir, 'relight_vapour_order_v2p4.json')))
G_V0, G_L0 = RV.G_V, RV.G_L
assert (G_V0, G_L0) == (15450.0, 56843.0)
LIM = 1e-3
CASES = ['isothermal|LO', 'hw+5K|LO', 'ARM_bay45C_liq24C|LO', 'isothermal|HI', 'hw+5K|HI', 'ARM_bay45C_liq24C|HI']
TP = tuple(sorted(set([round(1.0 + 0.1 * i, 2) for i in range(23)] + [2.43, 2.44])))      # 1.0-3.2 s plus 2.43 / 2.44
RV.TP = TP; RV.ORIF = (0.707, 0.8); RV.TILTS = (0.0, 2.0); RV.TAPS = ("2tap",)   # 0.8 kept only for the author's built-in sanity check
# author's two-tap rates per state (purge_basis_line216_v2p4b.json uncertainty.tank_state; 289.5 K: the law values)
RATES = {283.15: (29.40, 7.31), 289.5: (31.2416, 8.4916), 297.15: (33.20, 10.10)}
p0 = VO0['properties']


def state(T):
    rl = CP.PropsSI('D', 'T', T, 'Q', 0, 'NitrousOxide'); rv = CP.PropsSI('D', 'T', T, 'Q', 1, 'NitrousOxide')
    hfg = CP.PropsSI('H', 'T', T, 'Q', 1, 'NitrousOxide') - CP.PropsSI('H', 'T', T, 'Q', 0, 'NitrousOxide')
    P = CP.PropsSI('P', 'T', T, 'Q', 0, 'NitrousOxide')
    return rl, rv, hfg, P


def run(T):
    tag = f'T{T:.2f}'
    if T == 289.5:
        d = data_dir; RV.G_V, RV.G_L = G_V0, G_L0; mod = None
    else:
        d = os.path.join(scratch, 'data_' + tag); os.makedirs(d, exist_ok=True)
        for fn in os.listdir(data_dir):
            dst = os.path.join(d, fn)
            if fn != 'relight_vapour_order_v2p4.json' and not os.path.exists(dst):
                os.symlink(os.path.join(data_dir, fn), dst)
        rl, rv, hfg, P = state(T)
        fl = RATES[T][0] / RATES[289.5][0]; fv = RATES[T][1] / RATES[289.5][1]
        RV.G_L, RV.G_V = G_L0 * fl, G_V0 * fv
        ratio_l = (fl / rl) / (1.0 / p0['rho_l']); ratio_v = (fv / rv) / (1.0 / p0['rho_v'])
        VO = json.loads(json.dumps(VO0))
        pp = VO['properties']
        pp.update(T_K=T, P_Pa=P, rho_l=rl, rho_v=rv, h_fg=hfg, vap_cm3_per_J=1e6 / (hfg * rv), liq_cm3_per_J=1e6 / (hfg * rl))
        VO['purge_s_per_cm3'] = VO0['purge_s_per_cm3'] / ratio_v
        VO['liquid_plug_dead_time_s_per_cm3'] = VO0['liquid_plug_dead_time_s_per_cm3'] / ratio_l
        json.dump(VO, open(os.path.join(d, 'relight_vapour_order_v2p4.json'), 'w'))
        mod = dict(G_L=RV.G_L, G_V=RV.G_V, rho_l=rl, rho_v=rv, h_fg=hfg, P_sat_bar=P / 1e5, vap_cm3_per_J=pp['vap_cm3_per_J'],
                   liq_cm3_per_J=pp['liq_cm3_per_J'], purge_s_per_cm3=VO['purge_s_per_cm3'],
                   liquid_plug_dead_time_s_per_cm3=VO['liquid_plug_dead_time_s_per_cm3'], liquid_volumetric_flux_ratio=ratio_l,
                   vapour_volumetric_flux_ratio=ratio_v)
    raw_f = os.path.join(scratch, f'purge_{tag}.json')
    RV.main(d, *[f['file'] for f in files], raw_f)
    R = json.load(open(raw_f))
    with gzip.open(raw_f.replace('.json', '_summary.json.gz'), 'rt') as fh:
        S = json.load(fh)['summary']
    P_ = lambda k: max(S[k]['P_paused'], S[k]['P_restart'])
    fk = '0.707|2tap'; sp = R['s_phys'][fk]
    out = {}
    for lin in ('0.0', '1.0'):
        for s_lab in ('scons', 'swall', 's1.0', 's0.5'):
            worst = {}; n2 = {}; tco = 0.0
            for Tp in TP:
                w = 0.0; lo, hi = 1e9, 0.0
                for m in ('barrier', 'open'):
                    for c in CASES:
                        for tg in ('wet', 'dry'):
                            for th, azs in ((0.0, (0.0,)), (2.0, RV.AZS)):
                                for az in azs:
                                    k = f'purge0.707|2tap|{s_lab}|Tp{Tp}|lin{lin}|{m}|{c}|{tg}|{th}|{az}'
                                    w = max(w, P_(k)); lo = min(lo, S[k]['N2O_g'][0]); hi = max(hi, S[k]['N2O_g'][1])
                                    tco = max(tco, S[k]['t_cap_out'][1])
                worst[f'{Tp}'] = w; n2[f'{Tp}'] = [lo, hi]
            Tp_r = None
            for i, Tp in enumerate(TP):
                if all(worst[f'{x}'] <= LIM for x in TP[i:]):
                    Tp_r = Tp; break
            out[f'lin{lin}|{s_lab}'] = dict(s=(sp['scons'] if s_lab == 'scons' else sp['swall'] if s_lab == 'swall' else float(s_lab[1:])),
                                            Tp_robust_s=Tp_r, worst_P_by_Tp=worst, N2O_g_by_Tp=n2, t_cap_out_max_s=tco)
    unl = [out[f'lin0.0|{s}']['Tp_robust_s'] for s in ('scons', 'swall', 's1.0', 's0.5')]
    res = dict(state_K=T, modified=mod, s_phys=sp, flows=R['flows'][fk], robust=out,
               needed_Tp_unlined_worst_bracket_s=(None if None in unl else max(unl)),
               V_zero_abort_cm3=R['constants']['V_zero_abort_cm3'], runtime_s=round(time.time() - t0, 1))
    return res


results = {}
for T in (289.5, 283.15, 297.15):
    results[f'{T}'] = run(T)
    print('state', T, 'needed unlined', results[f'{T}']['needed_Tp_unlined_worst_bracket_s'],
          {k: v['Tp_robust_s'] for k, v in results[f'{T}']['robust'].items()}, round(time.time() - t0, 1), 's', flush=True)
    if T == 289.5:
        # reproduction of purge_duration_v2p4.json on the common grid points
        rep = {}
        for lab, v in results['289.5']['robust'].items():
            a = PD['robust'][f'0.707|2tap|{lab}']
            com = [k for k in a['worst_P_by_Tp'] if k in v['worst_P_by_Tp']]
            rep[lab] = dict(n_common=len(com), max_abs_dP=max(abs(a['worst_P_by_Tp'][k] - v['worst_P_by_Tp'][k]) for k in com),
                            author_Tp_robust=a['Tp_robust_s'], reviewer_Tp_robust=v['Tp_robust_s'])
            assert rep[lab]['max_abs_dP'] < 1e-9, (lab, rep[lab])
        results['reproduction_289.5_vs_purge_duration_v2p4'] = rep
        print('reproduction', json.dumps(rep), flush=True)
results['script'] = 'r4_purge_corners.py'; results['script_sha16'] = H16(sys.argv[0])
results['inputs'] = dict(src_copy_equal_to_author_src=True, data_dir=data_dir, purge_duration_v2p4='1ff6bfcd7d2f454c',
                         relight_vapour_order_v2p4=H16(os.path.join(data_dir, 'relight_vapour_order_v2p4.json')),
                         retained_vapour_v341_v2p4_py=H16(os.path.join(src_dir, 'retained_vapour_v341_v2p4.py')))
results['grid_Tp_s'] = list(TP)
results['runtime_s'] = round(time.time() - t0, 1)
json.dump(results, open(out_f, 'w'), indent=1, default=float)
print('done', results['runtime_s'], flush=True)
