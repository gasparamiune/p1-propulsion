"""REV-COMB-3 reviewer script: tank-outlet coverage arithmetic (independent re-computation of REPORT v2.4a §2.4 "tank outlet coverage
during PURGE" and its line-181 (10) liquid basis; author's numbers in data/v2p4a/unpurged_start_check_v2p4a.json part D, 4c745dcfbf09aef7).

Own code; the same stated inputs and correlations, so a match shows only that the arithmetic repeats:
  * tank: 6061-T6 tube 101.6 x 3.175 mm (ID 95.25 mm), flat aft bulkhead (mechanical.json v1 concept; not in CAD);
  * GNC purge_outlet_inputs.json (47b4deb96ea22043): liquid mass at the end of the PURGE flow, axial specific force, angles, roll rate;
  * CoolProp saturated N2O densities at 283.15 / 286.7 / 289.5 K;
  * dip (gas pull-through) height in the form the author states for Lubin & Springer (1967):
      h_c = 0.69 (Q^2 / g' * rho_l / (rho_l - rho_v))^0.2,  g' = axial specific force   (LITERATURE as cited; coefficient and form
      not re-checked against the paper here: no access);
  * free-surface drop at the wall R tan(theta); Ekman spin-up h / sqrt(nu Omega); first slosh mode of a flat-bottom cylinder.
Extension (reviewer, NOTE only): the same correlation at landing-burn flows (S230 map mdot_ox at 125 / 250 / 500 N, P_tank 4.5 MPa,
D_port 30 mm) with the axial specific force bounded below by F / 13.6706 kg (GNC ledger v3d, CHANGELOG line 189; the landing mass is
lower, so the true g' is higher and h_c lower), against GNC rev1's ASSUMED 3 % unusable residual (60 g of the 2.0 kg load).
usage: python -I r3_tank_outlet.py GNC_PURGE_OUTLET_INPUTS THROTTLE_MAP_S230 AUTHOR_UNPURGED_CHECK_JSON OUT_JSON
"""
import csv, hashlib, json, math, sys
import CoolProp.CoolProp as CP

fg, fmap, fa, out = sys.argv[1:5]
H16 = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
assert H16(fg) == '47b4deb96ea22043', H16(fg)
assert H16(fmap) == '4f2e6d846f7253da', H16(fmap)
assert H16(fa) == '4c745dcfbf09aef7', H16(fa)
G = json.load(open(fg)); AU = json.load(open(fa))['partD_tank_outlet']
FL, g0 = 'NitrousOxide', 9.80665
ID = 0.1016 - 2 * 0.003175; R = ID / 2; A = math.pi * R * R
TS = (283.15, 286.7, 289.5)
rho = {T: (CP.PropsSI('D', 'T', T, 'Q', 0, FL), CP.PropsSI('D', 'T', T, 'Q', 1, FL)) for T in TS}
recs = G['records']
m_end = min(min(r['m_liq_g']) for r in recs.values()); m_max = max(max(r['m_liq_g']) for r in recs.values())
fax_min = min(r['fax_g']['min'] for r in recs.values())
sf_raw = max(r['sf_axis_angle_deg_raw']['max'] for r in recs.values())
tilt_max = max(v['tilt_max_in_flow_deg']['max'] for v in G['distributions'].values())
roll = max(r['roll_rate_deg_s']['max'] for r in recs.values())
res = dict(script='r3_tank_outlet.py', inputs=dict(gnc_purge_outlet_inputs=H16(fg), throttle_map_v2=H16(fmap), author_unpurged_check=H16(fa)),
           ID_m=ID, A_m2=A, m_liq_end_min_g=m_end, m_liq_max_g=m_max, fax_min_g=fax_min, sf_raw_max_deg=sf_raw, tilt_max_deg=tilt_max,
           roll_max_deg_s=roll)
res['depth_mm'] = {f'{T}': dict(at_min=1e3 * m_end / 1e3 / rho[T][0] / A, at_max=1e3 * m_max / 1e3 / rho[T][0] / A) for T in TS}
hmin = min(v['at_min'] for v in res['depth_mm'].values()) * 1e-3
res['wall_drop_mm'] = {k: 1e3 * R * math.tan(math.radians(a)) for k, a in (('sf_raw', sf_raw), ('tilt_max', tilt_max), ('45deg', 45.0))}
res['wall_uncover_deg'] = math.degrees(math.atan(hmin / R))


def h_c(Q_m, gfac, T):
    rl, rv = rho[T]
    Q = Q_m / rl
    return 0.69 * (Q * Q / (gfac * g0) * rl / (rl - rv)) ** 0.2


Q_PURGE = 0.031241633637819454          # two-tap liquid purge flow used by the author (rg01 stuck_open, upper)
res['h_c_purge_mm'] = {f'{T}': 1e3 * h_c(Q_PURGE, fax_min, T) for T in TS}
need = 1e-3 * res['h_c_purge_mm']['286.7'] + R * math.tan(math.radians(tilt_max))
res['coverage_depth_needed_mm'] = 1e3 * need
res['coverage_mass_g'] = {f'{T}': 1e3 * need * A * rho[T][0] for T in TS}
res['ratio_min_liquid_over_needed'] = [m_end / max(res['coverage_mass_g'].values()), m_end / min(res['coverage_mass_g'].values())]
nu_hi = 2.0e-7
res['ekman_s'] = hmin / math.sqrt(nu_hi * math.radians(roll))
res['slosh_Hz'] = math.sqrt(1.8412 * fax_min * g0 / R * math.tanh(1.8412 * hmin / R)) / (2 * math.pi)
res['author'] = dict(min_depth_mm=1e3 * AU['min_depth_m'], h_c_mm=1e3 * AU['dip_pull_through_LubinSpringer_h_c_m'],
                     ekman_s=AU['roll_spin_up_Ekman_s_min'], slosh_Hz=AU['slosh_first_mode_Hz'], wall_uncover_deg=AU['wall_uncovering_angle_deg'],
                     wall_drop_tilt_max_mm=1e3 * AU['surface_tilt_at_wall']['tilt_max']['surface_drop_at_wall_m'])
# ---- extension: landing-burn flows
rows = [r for r in csv.reader(open(fmap)) if r and not r[0].startswith('#')]
hd = rows[0]; ix = {k: hd.index(k) for k in ('P_tank_Pa', 'D_port_m', 'F_N', 'mdot_ox')}
mp = sorted((float(r[ix['F_N']]), float(r[ix['mdot_ox']])) for r in rows[1:]
            if abs(float(r[ix['P_tank_Pa']]) - 4.5e6) < 1 and abs(float(r[ix['D_port_m']]) - 0.030) < 1e-9)
M_LEDGER = 13.6706
land = []
for F in (125.0, 250.0, 500.0):
    md = min(mp, key=lambda x: abs(x[0] - F))
    gl = F / M_LEDGER / g0
    for T in TS:
        hc = h_c(md[1], gl, T)
        land.append(dict(F_N=md[0], mdot_ox=md[1], g_axial_lower_bound=gl, T_K=T, h_c_mm=1e3 * hc, liquid_at_dip_onset_g=1e3 * hc * A * rho[T][0]))
res['landing_extension'] = dict(rows=land, unusable_residual_GNC_rev1_g=0.03 * 2000.0,
                                note='centre outlet, flat bulkhead, quasi-static, no tilt; outlet geometry MISSING (OI-32)')
json.dump(res, open(out, 'w'), indent=1)
print('depth [mm] at the 766 g minimum / 1170 g:', {k: (round(v['at_min'], 1), round(v['at_max'], 1)) for k, v in res['depth_mm'].items()},
      '| author min %.1f' % res['author']['min_depth_mm'])
print('wall drop [mm]:', {k: round(v, 2) for k, v in res['wall_drop_mm'].items()}, '| uncover %.1f deg (author %.1f)' % (res['wall_uncover_deg'], res['author']['wall_uncover_deg']))
print('h_c purge [mm]:', {k: round(v, 2) for k, v in res['h_c_purge_mm'].items()}, '| author %.2f' % res['author']['h_c_mm'])
print('coverage depth %.2f mm; mass [g] %s; ratio %.2f-%.2f' % (res['coverage_depth_needed_mm'], {k: round(v, 1) for k, v in res['coverage_mass_g'].items()},
                                                              *res['ratio_min_liquid_over_needed']))
print('Ekman %.0f s (author %.0f); slosh %.3f Hz (author %.3f)' % (res['ekman_s'], res['author']['ekman_s'], res['slosh_Hz'], res['author']['slosh_Hz']))
for x in land:
    print('  landing F %5.0f N mdot %.4f g>=%.2f T %.2f: h_c %.1f mm, liquid at dip onset %.0f g (GNC 3 %% = 60 g)'
          % (x['F_N'], x['mdot_ox'], x['g_axial_lower_bound'], x['T_K'], x['h_c_mm'], x['liquid_at_dip_onset_g']))
print('wrote', out, H16(out))
