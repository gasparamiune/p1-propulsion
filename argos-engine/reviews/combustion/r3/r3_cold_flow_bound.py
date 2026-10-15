"""REV-COMB-3 reviewer script: cold-flow apparent-thrust bound (independent re-derivation of REPORT v2.4a §7.3 Table 7.3a,
data/v2p4a/cold_flow_thrust_v2p4a.csv e094c4be80d12f66).

Own code (CoolProp HEOS N2O; not the author's injector.py / grain_q1d.py).  The bound as stated by the author:
  F <= mdot_max * v_iso,eq;  mdot_max = Cd 0.80 * A(lift) * G_Dyer(P1 = P_sat(T), P2 = 1 atm, saturated liquid, kappa = 1);
  G_Dyer = kappa/(1+kappa) G_SPI + 1/(1+kappa) G_HEM, G_SPI = sqrt(2 rho_l (P1 - P2)), G_HEM = max over P of rho(P, s_l) sqrt(2 (h_l - h(P, s_l)));
  v_iso,eq = sqrt(2 (h_l - h(1 atm, s_l)));  A(h) = pi s (Ds - s cos a), s = h sin a, Ds 5.5 mm, a 15 deg.
  The lift of a command comes from the S230 open-loop map (Cd 0.70), interpolated linearly in P_tank at P_sat(T).
Checks against the author's CSV at every (state, lift) row, and at the Table 7.3a command points (62.5 / 200 / 500 N, 4 mm).
Extensions: (1) heat added at tank pressure (author's sensitivity) and the heat needed to reach the 16.31 N margin;
(2) heat added after the throttling, at a chamber pressure Pc (the work per joule there), to show where heat matters;
(3) the margin ratio 16.31 / F_bound at the start level, as a tolerance on Cd x A x G (the Cd <= 0.80 acceptance is a full-stroke one).
usage: python -I r3_cold_flow_bound.py AUTHOR_CSV THROTTLE_MAP_S230 OUT_JSON
"""
import csv, hashlib, json, math, sys
import numpy as np
import CoolProp.CoolProp as CP

fcsv, fmap, out = sys.argv[1:4]
H16 = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
assert H16(fcsv) == 'e094c4be80d12f66', H16(fcsv)
assert H16(fmap) == '4f2e6d846f7253da', H16(fmap)
FL = 'NitrousOxide'; PA = 101325.0
DS, ALPHA, CD = 5.5e-3, math.radians(15.0), 0.80
F_THR, M_ALL, M_W6 = 37.16, 4.16, 16.31


def area(h):
    s = h * math.sin(ALPHA)
    return math.pi * s * (DS - s * math.cos(ALPHA))


def sat(T):
    return dict(T=T, P=CP.PropsSI('P', 'T', T, 'Q', 0, FL), rho=CP.PropsSI('D', 'T', T, 'Q', 0, FL),
                h=CP.PropsSI('H', 'T', T, 'Q', 0, FL), s=CP.PropsSI('S', 'T', T, 'Q', 0, FL))


def g_hem(P1, h0, s0):
    best = (0.0, None)
    for P in np.linspace(P1 * 0.999, PA, 1500):
        rho = CP.PropsSI('D', 'P', P, 'S', s0, FL); h = CP.PropsSI('H', 'P', P, 'S', s0, FL)
        G = rho * math.sqrt(max(2.0 * (h0 - h), 0.0))
        if G > best[0]:
            best = (G, P)
    return best


def v_iso(P0, h0, s0, Pe=PA):
    return math.sqrt(2.0 * (h0 - CP.PropsSI('H', 'P', Pe, 'S', s0, FL)))


# ---- open-loop map lift at a command, interpolated in P_tank (map rows at D_port 0.030 m)
rows = [r for r in csv.reader(open(fmap)) if r and not r[0].startswith('#')]
hd = rows[0]; ix = {k: hd.index(k) for k in ('P_tank_Pa', 'D_port_m', 'F_N', 'lift_m')}
tab = {}
for r in rows[1:]:
    if abs(float(r[ix['D_port_m']]) - 0.030) < 1e-9:
        tab.setdefault(float(r[ix['P_tank_Pa']]), []).append((float(r[ix['F_N']]), float(r[ix['lift_m']])))
Pt = sorted(tab)


def map_lift(F, P):
    L = [np.interp(F, *zip(*sorted(tab[p]))) for p in Pt]
    return float(np.interp(P, Pt, L))


# ---- author's CSV rows
A = [r for r in csv.DictReader(l for l in open(fcsv) if not l.startswith('"#') and not l.startswith('#'))]
res = dict(script='r3_cold_flow_bound.py', inputs=dict(cold_flow_thrust_v2p4a_csv=H16(fcsv), throttle_map_v2_csv=H16(fmap)),
           states={}, csv_compare=[], table_points=[])
for T in (283.15, 286.7, 289.5):
    S = sat(T)
    Gs = math.sqrt(2.0 * S['rho'] * (S['P'] - PA))
    Gh, Pch = g_hem(S['P'], S['h'], S['s'])
    Gd = 0.5 * Gs + 0.5 * Gh
    v = v_iso(S['P'], S['h'], S['s'])
    st = dict(P_sat_bar=S['P'] / 1e5, rho_l=S['rho'], G_SPI=Gs, G_HEM=Gh, P_HEM_choke_bar=Pch / 1e5, G_Dyer=Gd, v_iso_eq=v)
    # heat at tank pressure (author's sensitivity): v_iso from (P_sat, h_l + q)
    st['v_iso_heat_at_tank_P'] = {}
    for q in (25e3, 50e3, 100e3, 200e3):
        h0 = S['h'] + q; s0 = CP.PropsSI('S', 'P', S['P'], 'H', h0, FL)
        st['v_iso_heat_at_tank_P'][f'{q/1e3:.0f}kJ_kg'] = v_iso(S['P'], h0, s0)
    # heat after the throttling, at a chamber pressure Pc: extra isentropic enthalpy drop to 1 atm per joule
    st['work_per_joule_after_throttling'] = {}
    for Pc in (1.03e5, 1.3e5, 2.0e5, 4.0e5):
        s1 = CP.PropsSI('S', 'P', Pc, 'H', S['h'], FL)
        dh0 = S['h'] - CP.PropsSI('H', 'P', PA, 'S', s1, FL)
        eta = {}
        for q in (100e3, 300e3, 600e3):
            s2 = CP.PropsSI('S', 'P', Pc, 'H', S['h'] + q, FL)
            dh = S['h'] + q - CP.PropsSI('H', 'P', PA, 'S', s2, FL)
            eta[f'{q/1e3:.0f}kJ_kg'] = (dh - dh0) / q
        st['work_per_joule_after_throttling'][f'{Pc/1e5:.2f}bar'] = dict(dh_iso_throttled_no_heat_J_kg=dh0, eta=eta)
    res['states'][f'{T:.2f}'] = st
    # CSV rows of this state
    for r in A:
        if abs(float(r['T_tank_K']) - T) > 1e-6:
            continue
        h = float(r['lift_mm']) * 1e-3
        md = CD * area(h) * Gd
        res['csv_compare'].append(dict(T=T, lift_mm=h * 1e3, mdot_mine=md, mdot_author=float(r['mdot_bound_kg_s']),
                                       F_mine=md * v, F_author=float(r['F_bound_N']),
                                       rel_F=md * v / float(r['F_bound_N']) - 1.0))
    # Table 7.3a command points
    for Fc in (62.5, 200.0, 500.0, 'stroke'):
        h = 4.0e-3 if Fc == 'stroke' else map_lift(Fc, S['P'])
        md = CD * area(h) * Gd
        F = md * v
        pt = dict(T=T, command=Fc, lift_mm=h * 1e3, area_mm2=area(h) * 1e6, mdot_bound=md, F_bound=F)
        if Fc == 62.5:
            pt['margin_ratio_W6'] = M_W6 / F
            pt['v_needed_for_W6_margin'] = M_W6 / md
            # heat at tank pressure needed to reach the 16.31 N margin (bisection on q)
            lo_, hi_ = 0.0, 300e3
            for _ in range(60):
                q = 0.5 * (lo_ + hi_); s0 = CP.PropsSI('S', 'P', S['P'], 'H', S['h'] + q, FL)
                (lo_, hi_) = (q, hi_) if md * v_iso(S['P'], S['h'] + q, s0) < M_W6 else (lo_, q)
            pt['q_tank_P_for_W6_margin_J_kg'] = q; pt['heat_rate_W'] = q * md
            # Cd*A*G factor and lift offset that alone reach the margin
            pt['lift_offset_for_W6_margin_mm'] = None
            for dh in np.linspace(0.0, 0.2e-3, 2001):
                if CD * area(h + dh) * Gd * v >= M_W6:
                    pt['lift_offset_for_W6_margin_mm'] = dh * 1e3
                    break
        res['table_points'].append(pt)
    # 37.16 N crossing: command at which F_bound reaches the threshold (map lift)
    Fs = np.arange(62.5, 500.01, 0.25)
    FB = np.array([CD * area(map_lift(f, S['P'])) * Gd * v for f in Fs])
    res['states'][f'{T:.2f}']['command_at_threshold_N'] = dict(
        all_winds_4p16=float(Fs[np.argmax(FB >= M_ALL)]) if (FB >= M_ALL).any() else None,
        W6_16p31=float(Fs[np.argmax(FB >= M_W6)]) if (FB >= M_W6).any() else None,
        thr_37p16=float(Fs[np.argmax(FB >= F_THR)]) if (FB >= F_THR).any() else None)
json.dump(res, open(out, 'w'), indent=1)
for k, st in res['states'].items():
    print(k, json.dumps({a: (round(b, 4) if isinstance(b, float) else b) for a, b in st.items() if a not in ('work_per_joule_after_throttling',)}))
    for pc, x in st['work_per_joule_after_throttling'].items():
        print('    heat after throttling at', pc, 'dh_iso(no heat) %.0f J/kg' % x['dh_iso_throttled_no_heat_J_kg'], json.dumps({a: round(b, 4) for a, b in x['eta'].items()}))
print('CSV compare: max |rel F| %.2e over %d rows' % (max(abs(x['rel_F']) for x in res['csv_compare']), len(res['csv_compare'])))
for x in res['csv_compare']:
    if abs(x['lift_mm'] - 0.22) < 1e-9 or abs(x['lift_mm'] - 4.0) < 1e-9 or abs(x['lift_mm'] - 0.62) < 1e-9 or abs(x['lift_mm'] - 2.2) < 1e-9:
        print('   T %.2f lift %.3f mdot %.5f/%.5f F %.3f/%.3f' % (x['T'], x['lift_mm'], x['mdot_mine'], x['mdot_author'], x['F_mine'], x['F_author']))
for p in res['table_points']:
    print('  ', json.dumps({a: (round(b, 5) if isinstance(b, float) else b) for a, b in p.items()}))
print('wrote', out, H16(out))
