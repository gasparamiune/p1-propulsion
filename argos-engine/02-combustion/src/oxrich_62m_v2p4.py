"""Oxidiser-rich operation in the regression band (Combustion v2.4; REV-GNC-1 RG-03 item 1 relayed by the lead, 2026-10-13).

RG-03: in GNC's 62 m band population the mean O/F reaches 11.6 (p50 8.0 in the a 0.6-0.9 tercile) against <= 6.6 in GNC's
85 m sizing populations; fuel burned reaches 0.344 kg. Assess throat and wall oxidation, c* and Isp at O/F 8-11.6, and
combustion stability.
Part A (SIM histories, grain_q1d v2.4): every 62 m history (GNC v3.1 records p99 / max, with and without throat growth; a x0.6-1.65,
  n 0.35-0.68) and, for comparison, the 85 m band (dc_gncv3_band) and the A1 / B1 sizing histories (dc_gncv3): burn time,
  oxidiser and fuel, cumulative O/F, time-weighted instantaneous O/F (median, p95, max), time at O/F >= 7 / 8.17 / 10 / 14
  (14 = the c* table clamp of grain_q1d), Pc mean, end web, and the literature-scaled throat recession of erosion_v2p4
  (onset per flight, and the pessimistic reading with no repeat onset) with flights per insert at dAt/At = 5 %.
Part B (CEA through rocketcea, card ABS_TYP_v1): c*, Tc, sea-level Isp at eps 2 and the chamber mole fractions of the
  oxidising species against O/F 4-16 at Pc 5 / 7.5 / 10 / 25 bar; O/F of maximum c*.
Part C (stability.py model, unchanged): feed-coupled gain margins and the solid thermal-lag frequency at low-a, high-O/F
  operating points (a x0.6, n 0.5 and 0.68; port 30-45 mm; 30-70 % thrust; 46 bar tank).
usage: python -I oxrich_62m_v2p4.py DATA_V2_DIR OUT_JSON
"""
from __future__ import annotations
import glob, json, math, os, re, sys, hashlib
sys.dont_write_bytecode = True
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import erosion_dc as ED
import erosion_v2p4 as EV
import grain_q1d as Q
import stability as STB
from run_dc import _FixedTank

PAT = re.compile(r'(?P<rec>DC-[A-Za-z0-9_]+)-S230_neqE1e\+03_reg(?P<a>[0-9.]+)(_n(?P<n>[0-9.]+))?(_law(?P<law>ox|total))?\.csv$')
SP = ['O2', 'O', 'OH', 'H2O', 'CO2', 'CO', 'H2', 'NO']


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def wq(x, w, q):
    o = np.argsort(x); x = x[o]; w = w[o]; c = np.cumsum(w) / np.sum(w)
    return float(np.interp(q, c, x))


def part_a(d):
    files = sorted(glob.glob(os.path.join(d, 'dc_gncv31_62m', 'lane*', '*.csv')) + glob.glob(os.path.join(d, 'dc_gncv3_band', '*.csv'))
                   + glob.glob(os.path.join(d, 'dc_gncv3', '*.csv')))
    rows = {}
    for f in files:
        m = PAT.search(os.path.basename(f))
        if not m or (m.group('law') == 'total'):
            continue
        r = pd.read_csv(f); t = r.t.values; Pc = r.Pc.values; OF = r.OF.values; mox = r.mox.values; mf = r.mf.values
        on = (mox > 1e-4) & (Pc > 1.5e5)
        dt = np.diff(t, prepend=t[0])
        tb = float(np.sum(dt[on])); ox = float(np.sum((mox * dt)[on])); fu = float(np.sum((mf * dt)[on]))
        of = OF[on]; w = dt[on]; ok = np.isfinite(of)
        lo, hi = ED.literature(t, Pc, OF, on); lo2, hi2 = EV.literature_no_onset_repeat(t, Pc, OF, on)
        key = os.path.relpath(f, d)
        rows[key] = dict(record=m.group('rec'), a_band=float(m.group('a')), n=float(m.group('n') or 0.5), burn_on_s=tb, ox_kg=ox, fuel_kg=fu,
                         OF_cumulative=ox / fu if fu > 0 else None,
                         OF_inst_median=wq(of[ok], w[ok], 0.5), OF_inst_p95=wq(of[ok], w[ok], 0.95), OF_inst_max=float(np.max(of[ok])),
                         t_OF_ge7_s=float(np.sum(w[ok][of[ok] >= 7.0])), t_OF_ge_stoich_s=float(np.sum(w[ok][of[ok] >= 8.17])),
                         t_OF_ge10_s=float(np.sum(w[ok][of[ok] >= 10.0])), t_OF_ge14_clamp_s=float(np.sum(w[ok][of[ok] >= 14.0])),
                         Pc_mean_on_bar=float(np.sum(Pc[on] * dt[on]) / tb / 1e5) if tb > 0 else None,
                         w_end_mm=float(1e3 * r.w_min.values[-1]),
                         lit_recession_mm=[1e3 * lo, 1e3 * hi], lit_recession_no_onset_repeat_mm=[1e3 * lo2, 1e3 * hi2],
                         flights_per_insert_lit=[EV.DELTA_LIM / hi if hi > 0 else None, EV.DELTA_LIM / lo if lo > 0 else None],
                         flights_per_insert_lit_no_onset_repeat=[EV.DELTA_LIM / hi2 if hi2 > 0 else None, EV.DELTA_LIM / lo2 if lo2 > 0 else None],
                         history_sha256_16=sha16(f))
    return rows


def part_b():
    from rocketcea.cea_obj_w_units import CEA_Obj
    import cea_cards
    cea_cards.register_all()
    c = CEA_Obj(oxName='N2O', fuelName='ABS_TYP_v1', pressure_units='bar', cstar_units='m/s', temperature_units='K')
    out = {}
    for pc in (5.0, 7.5, 10.0, 25.0):
        rows = {}
        for of in (4.0, 5.0, 6.0, 7.0, 8.0, 8.17, 9.0, 10.0, 11.6, 13.0, 14.0, 16.0):
            cs = c.get_Cstar(Pc=pc, MR=of); tc = c.get_Tcomb(Pc=pc, MR=of)
            isp, mode = c.estimate_Ambient_Isp(Pc=pc, MR=of, eps=2.0, Pamb=1.01325, frozen=0, frozenAtThroat=0)
            _, mf = c.get_SpeciesMoleFractions(Pc=pc, MR=of, eps=2.0, frozen=0, frozenAtThroat=0, min_fraction=1e-6)
            X = {}
            for s in SP:
                v = mf.get(s, mf.get('*' + s, [0.0, 0.0, 0.0]))
                X[s] = float(v[0]) if len(v) else 0.0
            rows[f'{of:g}'] = dict(cstar_m_s=cs, Tc_K=tc, Isp_SL_eps2_s=isp, Isp_mode=mode, X_chamber=X)
        best = max(rows.items(), key=lambda kv: kv[1]['cstar_m_s'])
        out[f'{pc:g}bar'] = dict(rows=rows, OF_at_max_cstar=float(best[0]), cstar_max_m_s=best[1]['cstar_m_s'])
    return out


def part_c():
    rows = []
    for band, n in ((0.6, 0.5), (0.6, 0.68), (1.0, 0.5)):
        e = Q.Engine(_FixedTank(46.0e5, 290.15), dict(a=band * 1.0e-3 / 300.0 ** n, n=n))
        c = e.c
        for D in (0.030, 0.040, 0.045):
            e.D[:] = D
            for fr in (0.7, 0.5, 0.3):
                try:
                    h, cei = e.lift_for_thrust(500 * fr); s = e.steady(h)
                except Exception as ex:                                   # keep failures as evidence
                    rows.append(dict(a_band=band, n=n, D_port_m=D, frac=fr, error=repr(ex))); continue
                Pc, OF = s['Pc'], s['OF']
                a = STB.injector_sensitivity(e, h, Pc)
                mu_ox = s['mox'] / (s['mox'] + s['mf']); mu_f = 1 - mu_ox
                r, _ = e.regression(s['mox']); rbar = float(np.mean(r))
                tf = c['kappa_s'] / rbar ** 2
                g = e.P.gamma(Pc, min(OF, 14.0)); cs = e.cstar(Pc, OF)
                Gam = math.sqrt(g) * (2 / (g + 1)) ** ((g + 1) / (2 * (g - 1)))
                theta = e.Vc() / e.At / (cs * Gam ** 2)
                k_c = STB.kc(e, Pc, OF) if OF < 13.7 else None
                mg = STB.margins(a, mu_ox, mu_f, c['n'], tf, k_c if k_c is not None else 0.0, theta)
                rows.append(dict(a_band=band, n=n, D_port_m=D, frac=fr, Pc_bar=Pc / 1e5, OF=OF, dP_over_Pc=s['dpc'], inj_sensitivity_a=a,
                                 r_mean_mm_s=1e3 * rbar, tau_thermal_lag_s=tf, f_thermal_lag_Hz=1 / (2 * math.pi * tf), k_c=k_c,
                                 k_c_note=None if k_c is not None else 'O/F at the c* table clamp (14): k_c unknown, margin computed with k_c = 0',
                                 G_ox_kg_m2s=4 * s['mox'] / (math.pi * D * D), GM_tau1ms=mg['GM_tau1ms'], GM_tau10ms=mg['GM_tau10ms'], tau_crit_s=mg['tau_crit_s']))
                print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in rows[-1].items()}, flush=True)
    return rows


def main(d, out_f):
    A = part_a(d); B = part_b(); C = part_c()
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/oxrich_62m_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               part_a_histories=A, part_b_cea=B, part_c_stability=C,
               tags=dict(A='SIM (grain_q1d v2.4 on GNC SIM records; ASSUMED regression band) + LITERATURE-scaled erosion',
                         B='CEA (rocketcea, ABS_TYP_v1 card)', C='DERIVED (stability.py v2 model; Karabeyoglu-type modes not modelled)'))
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    print('wrote', out_f)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
