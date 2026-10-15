"""Thermochemistry deliverable tables (Combustion v1, brief task 1).

For each fuel card (ABS_TYP_v1 baseline, PETG_NOM_v1 backup, PARABS50_v1 paraffin-ABS option) and each mode
(shifting equilibrium, frozen at the chamber), over Pc = 3..30 bar and O/F = 2..10:
  c*, Tc, gamma_c, MW_c (chamber); transport (cp, mu, k, Pr) in chamber and throat (CEA: equilibrium transport
  properties include reaction contributions in shifting mode, frozen values in frozen mode);
  for eps in EPS: Isp_vac, Isp_SL (Schmucker separation-aware, ideal), pe, Me, separation flag;
  exit composition at eps = 2 (mole fractions >= 1e-4; condensed species flagged).
Oxidizer card: CEA 'N2O' = ideal gas at 298.15 K (hf ~ +82 kJ/mol). The liquid-injection correction
(saturated liquid N2O at 20 C; enthalpy from CoolProp relative to the ideal gas at 298.15 K) is evaluated
separately as card N2O_L20 and reported as a c*/Tc sensitivity (see liquid_n2o_correction()).
Outputs (CSV + JSON, SI): data/thermo/<fuel>_<mode>_v1.{csv,json}; data/thermo/hf_sensitivity_v1.csv;
data/thermo/n2o_liquid_correction_v1.json.
"""
from __future__ import annotations
import csv, json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cea_cards

G0 = 9.80665
PA = 101325.0
PC_BAR = [3.0, 4.0, 5.0, 7.5, 10.0, 12.5, 15.0, 20.0, 25.0, 30.0]
OF = [round(x, 2) for x in np.arange(2.0, 10.01, 0.5)]
EPS = [1.5, 2.0, 2.5, 3.0, 4.0]
SPECIES = ['CO', 'CO2', 'H2O', 'H2', 'N2', 'O2', 'OH', 'NO', 'H', 'O', 'C(gr)', 'CH4', 'HCN', 'NH3']


def cea_obj(fuel, ox='N2O'):
    from rocketcea.cea_obj_w_units import CEA_Obj
    return CEA_Obj(oxName=ox, fuelName=fuel, pressure_units='bar', cstar_units='m/s', temperature_units='K',
                   sonic_velocity_units='m/s', enthalpy_units='J/kg', density_units='kg/m^3',
                   specific_heat_units='J/kg-K', viscosity_units='poise', thermal_cond_units='W/cm-degC', isp_units='sec')


def schmucker_isp_sl(c, pc, of, eps, frozen):
    """Ideal sea-level Isp with Schmucker separation (nozzle cut at eps_sep, no recovery credit)."""
    def pe_ratio(e):
        return 1.0 / c.get_PcOvPe(Pc=pc, MR=of, eps=e, frozen=frozen)
    def psep(e):
        M = c.get_MachNumber(Pc=pc, MR=of, eps=e, frozen=frozen)
        return (1.88 * M - 1.0) ** -0.64
    cstar = c.get_Cstar(Pc=pc, MR=of)
    def isp_amb(e):
        ispv = c.get_Isp(Pc=pc, MR=of, eps=e, frozen=frozen)
        cfv = ispv * G0 / cstar
        return (cfv - e * PA / (pc * 1e5)) * cstar / G0
    pe = pe_ratio(eps) * pc * 1e5
    if pe / PA >= psep(eps):
        return isp_amb(eps), None, pe
    lo, hi = 1.01, eps
    for _ in range(30):
        mid = (lo * hi) ** 0.5
        if pe_ratio(mid) * pc * 1e5 / PA >= psep(mid):
            lo = mid
        else:
            hi = mid
    return isp_amb(lo), lo, pe


def build(fuel, frozen, outdir, ox='N2O'):
    c = cea_obj(fuel, ox)
    mode = 'frozen' if frozen else 'shifting'
    rows = []
    t0 = time.time()
    for pc in PC_BAR:
        for of in OF:
            r = dict(Pc_bar=pc, OF=of)
            r['cstar_m_s'] = c.get_Cstar(Pc=pc, MR=of)
            r['Tc_K'] = c.get_Tcomb(Pc=pc, MR=of)
            mw, g = c.get_Chamber_MolWt_gamma(Pc=pc, MR=of, eps=2.0)
            r['MW_c'] = mw; r['gamma_c'] = g
            for st, fn in (('c', c.get_Chamber_Transport), ('t', c.get_Throat_Transport)):
                cp, mu, k, pr = fn(Pc=pc, MR=of, eps=2.0, frozen=frozen)
                r[f'cp_{st}_J_kgK'] = cp; r[f'mu_{st}_Pa_s'] = mu * 0.1; r[f'k_{st}_W_mK'] = k * 100.0; r[f'Pr_{st}'] = pr
            for e in EPS:
                r[f'Isp_vac_eps{e}_s'] = c.get_Isp(Pc=pc, MR=of, eps=e, frozen=frozen)
                isl, esep, pe = schmucker_isp_sl(c, pc, of, e, frozen)
                r[f'Isp_SL_eps{e}_s'] = isl
                r[f'pe_eps{e}_Pa'] = pe
                r[f'Me_eps{e}'] = c.get_MachNumber(Pc=pc, MR=of, eps=e, frozen=frozen)
                r[f'eps_sep_eps{e}'] = esep if esep is not None else ''
            mwd, mf = c.get_SpeciesMoleFractions(Pc=pc, MR=of, eps=2.0, frozen=frozen, frozenAtThroat=0, min_fraction=1e-5)
            cond = []
            for k, v in mf.items():
                name = k.strip('*')
                val = v[3] if len(v) > 3 else v[-1]
                if name in SPECIES:
                    r[f'X_exit_{name}'] = val
                if '(' in name and val > 0:
                    cond.append(f'{name}:{val:.2e}')
            for s in SPECIES:
                r.setdefault(f'X_exit_{s}', 0.0)
            r['condensed_exit'] = ';'.join(cond)
            rows.append(r)
    os.makedirs(outdir, exist_ok=True)
    stem = os.path.join(outdir, f'{fuel}_{"" if ox == "N2O" else ox + "_"}{mode}_v1')
    keys = list(rows[0].keys())
    with open(stem + '.csv', 'w', newline='') as f:
        f.write(f'# CEA (RocketCEA {__import__("rocketcea").__version__}) {mode} equilibrium, oxidizer {ox}, fuel card {fuel} '
                f'(cards: 02-combustion/src/cea_cards.py). Ideal values (no eta_c*/eta_cf). Isp_SL: Schmucker separation, '
                f'p_a = 101325 Pa. Transport: mu Pa.s, k W/m/K, cp J/kg/K. X_exit: mole fractions at eps = 2. Tag: CEA.\n')
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    json.dump(dict(fuel=fuel, oxidizer=ox, mode=mode, Pc_bar=PC_BAR, OF=OF, eps=EPS, rows=rows, tag='CEA',
                   version='v1', date='2026-10-11'), open(stem + '.json', 'w'), default=float)
    return stem, time.time() - t0


def hf_sensitivity(outdir):
    cards = ['ABS_TYP_v1', 'ABS_LEAD_v0', 'ABS_FAA_v1', 'ABS_FAAGC_v1', 'ABS_SRICH_v1', 'ABS_BRICH_v1', 'ABS_ARICH_v1',
             'ABS_USU5043_v1', 'PETG_NOM_v1', 'PETG_LO_v1', 'PETG_HI_v1', 'PET_LEAD_v0', 'PARAFFIN_v1', 'PARABS50_v1']
    allc = cea_cards.build_cards()
    rows = []
    for cd in cards:
        if cd not in allc:
            continue
        c = cea_obj(cd)
        for pc in (25.0, 4.36):
            best = max(((c.get_Cstar(Pc=pc, MR=of), of) for of in np.arange(2.0, 10.01, 0.25)))
            r = dict(card=cd, Pc_bar=pc, cstar_peak_m_s=best[0], OF_at_peak=best[1])
            for of in (3.0, 4.0, 5.0, 6.0, 7.0, 7.76, 8.0):
                r[f'cstar_OF{of}'] = c.get_Cstar(Pc=pc, MR=of)
            rows.append(r)
    fn = os.path.join(outdir, 'hf_sensitivity_v1.csv')
    with open(fn, 'w', newline='') as f:
        f.write('# c* [m/s] sensitivity to fuel composition/enthalpy-of-formation cards (CEA shifting). Card definitions and '
                'sources: 02-combustion/src/cea_cards.py. Tag: CEA.\n')
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    return fn


def liquid_n2o_correction(outdir, T=293.15):
    """Effective enthalpy of formation of saturated-liquid N2O at T relative to CEA's gas reference (298.15 K)."""
    import CoolProp.CoolProp as CP
    from rocketcea.cea_obj import add_new_oxidizer
    M = 44.0128e-3
    h_l = CP.PropsSI('H', 'T', T, 'Q', 0, 'NitrousOxide')
    h_ig = CP.PropsSI('H', 'T', 298.15, 'P', 10.0, 'NitrousOxide')      # ~ideal gas at 10 Pa
    dh = (h_l - h_ig) * M / 1000.0                                       # kJ/mol
    hf_gas = 82.05                                                       # NIST-JANAF / CODATA gas value, kJ/mol (LITERATURE)
    hf_liq = hf_gas + dh
    card = f'oxid N2O_L20  N 2 O 1  wt%=100.\nh,kj/mol={hf_liq:.3f}  t(k)={T:.2f}  rho=0.786\n'
    add_new_oxidizer('N2O_L20', card)
    out = dict(T_K=T, dh_liquid_minus_idealgas298_kJ_mol=dh, hf_gas_kJ_mol=hf_gas, hf_effective_liquid_kJ_mol=hf_liq,
               card=card, source='CoolProp (Lemmon & Span 2006 EOS) for h_l(sat, T) - h_ig(298.15 K); hf_gas 82.05 kJ/mol '
               '(NIST Chemistry WebBook, LITERATURE)')
    pts = []
    for pc, of in ((25.0, 7.76), (13.25, 5.48), (6.18, 3.70), (4.36, 3.11), (25.0, 7.0)):
        cg = cea_obj('ABS_TYP_v1', 'N2O'); cl = cea_obj('ABS_TYP_v1', 'N2O_L20')
        pts.append(dict(Pc_bar=pc, OF=of, cstar_gas=cg.get_Cstar(Pc=pc, MR=of), cstar_liq=cl.get_Cstar(Pc=pc, MR=of),
                        Tc_gas=cg.get_Tcomb(Pc=pc, MR=of), Tc_liq=cl.get_Tcomb(Pc=pc, MR=of),
                        Isp_vac2_gas=cg.get_Isp(Pc=pc, MR=of, eps=2.0), Isp_vac2_liq=cl.get_Isp(Pc=pc, MR=of, eps=2.0)))
        pts[-1]['dcstar_pct'] = 100 * (pts[-1]['cstar_liq'] / pts[-1]['cstar_gas'] - 1)
    out['points'] = pts
    json.dump(out, open(os.path.join(outdir, 'n2o_liquid_correction_v1.json'), 'w'), indent=1, default=float)
    return out


if __name__ == '__main__':
    outdir = sys.argv[1]
    cea_cards.register_all()
    what = sys.argv[2] if len(sys.argv) > 2 else 'all'
    if what in ('all', 'liq'):
        o = liquid_n2o_correction(outdir)
        print(json.dumps({k: v for k, v in o.items() if k != 'card'}, indent=1, default=float))
    if what in ('all', 'hf'):
        print(hf_sensitivity(outdir))
    if what in ('all', 'tables'):
        for fuel in ('ABS_TYP_v1', 'PETG_NOM_v1', 'PARABS50_v1'):
            for fr in (0, 1):
                print(build(fuel, fr, outdir), flush=True)
