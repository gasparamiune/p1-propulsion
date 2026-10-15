#!/usr/bin/env python3
"""Low-inlet check v2.3 (Combustion, 2026-10-12): judgement on Mechanical's LOW INLET for CAD v3.4.

Input under review (read only): 03-cad/calcs/hose_routing_trade_v2.json, sha256/16 bf183b936852be36, section
O3b_riser_to_low_inlet: 316L block on the case OD at the head plug (2 of the 8 radial M5 head screws), O-ring face seal
around a 4-5 mm case-wall hole, annulus 1.5 x 4 mm at r 27.8 mm on the plug OD, ONE 3 mm x 23 mm radial passage into the
10 mm manifold bore, riser 3/8 x 0.035 316 (z 62-129.3 mm), -6 hose coil 0.252 m; manifold 3.3 -> ~4.5 cm3 (ESTIMATE).

Checks (1-D / lumped models, no CFD; every input tagged):
 1. inlet-path pressure loss by the handbook-K method of feed_line_checks_v2 (K ASSUMED) at 0.26 kg/s / 25 C and
    0.241 kg/s / 20 C; total line vs the 2.70 bar budget (0.26 kg/s) used by every v2 simulation; equilibrium flash
    state of the manifold (CoolProp, isenthalpic); pintle area needed at the 100 % point (Dyer table) vs the 4.2 mm stop.
 2. distribution: feed velocity head / injector dP at the throttle points (throttle_trade_v2 + stability_v2 rows);
    first-harmonic flux bound 0.5 q/dP_inj; lateral jet momentum on the needle (mdot v); guide-reaction friction on
    CAD v3.3 stations; pintle-gap sensitivity to a needle lateral offset e: d(flux)/flux = e cos(a) / (h sin(a)).
 3. volumes: manifold dead leg above the feed entry (CAD v3.3 primitives, DERIVED reading of Mechanical's
    parts_engine.py), valve->seat volume for two valve positions, trapped-liquid mass, isochoric heating to the 7.5 MPa
    relief (CoolProp).
 4. priming: bleed area at 0.10 mm, choked vent capacity, vent time constants (isentropic bound is volume-independent).
 5. relight: choked purge of a vapour-filled valve->seat volume through the ignition lift vs the 0.23 s between the
    ignition lift (t 0.12 s) and the ignition check (t 0.35 s) of combustion.json v2.3 igniter.sequence.
 6. chug: manifold mass compliance V/a^2, injector R*C time constant, feed-mode frequency with / without a vapour pocket.
usage: python low_inlet_check.py OUTDIR
"""
from __future__ import annotations
import hashlib, json, math, os, sys
import numpy as np
import CoolProp.CoolProp as CP
from scipy.optimize import brentq

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from injector import GTable, pintle_area, pintle_lift   # noqa: E402

F = 'NitrousOxide'
DATA = os.path.join(HERE, '..', 'data', 'v2')
MECH = '/home/claude/work/shared-fallback/engine/03-cad/calcs/hose_routing_trade_v2.json'
MECH_SHA16 = 'bf183b936852be36'
CD = 0.70                      # pintle Cd, ASSUMED (combustion.json v2.3)
ALPHA = math.radians(15.0)     # needle cone half-angle (combustion.json)
MU_GUIDE = 0.20                # guide friction, baseline S3 design (Mechanical pintle_inline_v34_v2p2, ASSUMED)
BUDGET_PA = 2.5e5 * (0.26 / 0.25) ** 2     # grain_q1d dp_line 2.5 bar at 0.25 kg/s ~ mdot^2 (ASSUMED in every v2 sim)
TEMPS = {'15C': 288.15, '20C': 293.15, '25C': 298.15}


def T(v, tag, src=''):
    return {'v': v, 'tag': tag, 'src': src} if src else {'v': v, 'tag': tag}


def r(x, n=4):
    if isinstance(x, dict):
        return {k: r(v, n) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [r(v, n) for v in x]
    if isinstance(x, (float, np.floating)):
        if not math.isfinite(x):
            return None
        return float(f'{x:.{n}g}')
    return x


def liq(Tk):
    return dict(rho=CP.PropsSI('D', 'T', Tk, 'Q', 0, F), Psat=CP.PropsSI('P', 'T', Tk, 'Q', 0, F),
                a=CP.PropsSI('A', 'T', Tk, 'Q', 0, F), h=CP.PropsSI('H', 'T', Tk, 'Q', 0, F))


def mu_liq_esdu(Tk):
    Tc = 309.57
    th = (Tc - 5.24) / (Tk - 5.24)
    return 0.0293423e-3 * math.exp(1.6089 * (th - 1) ** (1 / 3) + 2.0439 * (th - 1) ** (4 / 3))


def haaland(Re, rr):
    return (-1.8 * math.log10((rr / 3.7) ** 1.11 + 6.9 / Re)) ** -2


def circ(d):
    return math.pi / 4 * d ** 2


# ------------------------------------------------------------------------------------------------ geometry and inputs
HOSE_ID = 0.0079               # -6 PTFE hose ID (feed_line_checks_v2 / mechanical.json v1)
TUBE_ID = 0.009525 - 2 * 0.000889   # 3/8 x 0.035 in tube ID 7.747 mm (DERIVED from the size)
L_FIXED = 0.245                # fixed 3/8 line, valve at the zone top (~0.26 m above the pivot) to the coil fixed end (0.045 m): 0.215 + 0.03 bends, ESTIMATE
L_TANK_VALVE = 0.15            # tank outlet to the NC valve, ASSUMED (not drawn)
V_FITTINGS = 1.0e-6            # 2 hose ends + tube-weld adapter internal volume, ASSUMED
# CAD v3.3 stations (DERIVED reading of Mechanical parts_engine.py v3.3, read only; z in mm, engine frame)
Z = dict(face=112.59, seat=117.59, ins_top=124.59, head_top=178.59, needle_body_top=180.59, bore_top=204.59,
         v33_cross=190.59, guide_bush=(206.59, 210.59), carriage_pin=215.59, g2_top=128.29, bolt_hole_low=133.84)
Z_LOW_ENTRY = 0.5 * (Z['g2_top'] + Z['bolt_hole_low'])   # 131.1 mm: annulus/passage level, ESTIMATE (plug may grow 3-8 mm)
D_BORE, D_BODY, D_STEM = 10.0, 6.0, 3.0                  # mm (v3.4 stem 3 mm, lead decision v2.3)


def dead_leg_mm3(z_entry, d_entry):
    """10 mm bore annulus volume above the top edge of the feed entry (needle closed)."""
    z0 = z_entry + d_entry / 2
    a_body = math.pi / 4 * (D_BORE ** 2 - D_BODY ** 2)
    a_stem = math.pi / 4 * (D_BORE ** 2 - D_STEM ** 2)
    v = a_body * max(0.0, min(Z['needle_body_top'], Z['bore_top']) - z0) if z0 < Z['needle_body_top'] else 0.0
    v += a_stem * (Z['bore_top'] - max(z0, Z['needle_body_top']))
    return v


def bore_volume_mm3():
    a_body = math.pi / 4 * (D_BORE ** 2 - D_BODY ** 2)
    a_stem = math.pi / 4 * (D_BORE ** 2 - D_STEM ** 2)
    return a_body * (Z['needle_body_top'] - Z['ins_top']) + a_stem * (Z['bore_top'] - Z['needle_body_top'])


# ------------------------------------------------------------------------------------------------ K-method losses
def sec(name, d_or_A, K, frac=1.0, L=0.0, is_area=False, n_par=1, rough=10e-6):
    """section: flow area (one channel), K on its own velocity head, flow fraction per channel, length for friction."""
    A = d_or_A if is_area else circ(d_or_A)
    Dh = math.sqrt(4 * A / math.pi) if not is_area else None
    return dict(name=name, A=A, K=K, frac=frac, L=L, Dh=Dh, rough=rough, n_par=n_par)


def path_dp(sections, mdot, Tk):
    p = liq(Tk); mu = mu_liq_esdu(Tk)
    out, tot = [], 0.0
    for s in sections:
        m = mdot * s['frac']
        v = m / (p['rho'] * s['A'])
        q = 0.5 * p['rho'] * v ** 2
        Kf = 0.0
        if s['L'] > 0:
            Dh = s['Dh'] if s['Dh'] else s.get('Dh_override')
            Re = p['rho'] * v * Dh / mu
            Kf = haaland(Re, s['rough'] / Dh) * s['L'] / Dh
        dp = (s['K'] + Kf) * q
        tot += dp
        out.append(dict(name=s['name'], A_mm2=s['A'] * 1e6, v_m_s=v, q_kPa=q / 1e3, K=s['K'], K_fric=Kf, dp_kPa=dp / 1e3))
    return tot, out


def common_line(mdot, Tk):
    """tank -> manifold losses EXCEPT the inlet path (feed_line_checks_v2 method), with the O3b routing."""
    p = liq(Tk); mu = mu_liq_esdu(Tk)
    rho = p['rho']
    items = {}
    # hose 0.252 m (Mechanical O3_coils[0]), smooth PTFE 1.5 um
    A = circ(HOSE_ID); v = mdot / (rho * A); q = 0.5 * rho * v ** 2
    Re = rho * v * HOSE_ID / mu
    items['hose_friction_0p252m'] = haaland(Re, 1.5e-6 / HOSE_ID) * 0.252 / HOSE_ID * q
    # v2 minor losses less the deleted bonnet inlet turn: tank outlet 0.5, tee run 0.3, hose ends 0.6, elbow 1.0 (ASSUMED)
    items['minor_K2p4_on_hose_q'] = 2.4 * q
    # fixed 3/8 line (inside the bay, 0.245 m ESTIMATE) + 2 bends K 0.3 + riser 0.07 m + S-bend K 0.3 (ASSUMED)
    At = circ(TUBE_ID); vt = mdot / (rho * At); qt = 0.5 * rho * vt ** 2
    Ret = rho * vt * TUBE_ID / mu
    ft = haaland(Ret, 1.5e-6 / TUBE_ID)
    items['fixed_line_0p245m_plus_2_bends'] = (ft * L_FIXED / TUBE_ID + 0.6) * qt
    items['riser_0p07m_plus_S_bend'] = (ft * 0.07 / TUBE_ID + 0.3) * qt
    # NC valve Cv 3, filter Cv 2.2 (combustion.json v2.3)
    Q_gpm = mdot / rho * 15850.32; SG = rho / 999.0
    items['valve_Cv3'] = SG * (Q_gpm / 3.0) ** 2 * 6894.76
    items['filter_Cv2p2'] = SG * (Q_gpm / 2.2) ** 2 * 6894.76
    return sum(items.values()), items


def inlet_variants():
    """inlet-path variants, sections in flow order (K ASSUMED, handbook ranges: Idelchik / Crane type)."""
    v = {}
    v['V0_v33_bonnet_reference'] = dict(
        note='CAD v3.3 bonnet inlet: -6 ORB port -> 6 mm riser bore -> 90 deg -> 6 mm cross-drilling (17 mm) -> 10 mm bore '
             '(screen counted as the Cv 2.2 filter). Reference for "no worse than v3.3".',
        sections=[sec('contraction ORB port -> 6 mm bore', 0.006, 0.3), sec('90 deg turn into 6 mm cross-drilling', 0.006, 1.1),
                  sec('6 mm drillings friction (6.6 + 17 mm)', 0.006, 0.0, L=0.0236), sec('exit into the 10 mm bore', 0.006, 1.0)],
        z_entry=Z['v33_cross'], d_entry=6.0, n_feeds=1, entry_note='top of the bore (flow-through to the seat, 73 mm)')
    for dh in (4.0, 5.0):
        v[f'V1_as_drawn_hole{dh:.0f}mm_aligned'] = dict(
            note=f'Mechanical O3b as drawn: block 90 deg turn into a {dh:.0f} mm case-wall hole, across the 1.5 mm annulus gap into '
                 'ONE 3 mm x 23 mm radial passage aligned with the hole, exit against the 6 mm needle body.',
            sections=[sec(f'90 deg turn into the {dh:.0f} mm case hole', dh / 1e3, 1.1),
                      sec('gap transfer + contraction into the 3 mm passage', 0.003, 0.5),
                      sec('3 mm passage friction (23 mm)', 0.003, 0.0, L=0.023), sec('exit into the 10 mm bore', 0.003, 1.0)],
            z_entry=Z_LOW_ENTRY, d_entry=3.0, n_feeds=1, entry_note='low: 13-17 mm above the seat, dead leg above')
    a_ann = 1.5e-3 * 4e-3
    s_ann = sec('annulus 1.5 x 4 mm, half flow each way, half circumference (87.5 mm)', a_ann, 1.0, frac=0.5, L=0.0875, is_area=True)
    s_ann['Dh'] = 4 * a_ann / (2 * (1.5e-3 + 4e-3))
    v['V1b_as_drawn_hole4p5mm_180deg_misaligned'] = dict(
        note='as drawn with the passage 180 deg from the case hole (no clocking feature): the 6 mm2 annulus carries half the flow '
             'each way; split K 1.0 + merge K 1.0 on the annulus velocity head (ASSUMED)',
        sections=[sec('90 deg turn into the 4.5 mm case hole', 0.0045, 1.1), s_ann,
                  sec('annulus merge into the passage', a_ann, 1.0, frac=0.5, is_area=True),
                  sec('contraction into the 3 mm passage', 0.003, 0.5), sec('3 mm passage friction (23 mm)', 0.003, 0.0, L=0.023),
                  sec('exit into the 10 mm bore', 0.003, 1.0)],
        z_entry=Z_LOW_ENTRY, d_entry=3.0, n_feeds=1, entry_note='low')
    v['E1_top_entry_7mm'] = dict(
        note='example compliant layout A (Combustion proposal, Mechanical to judge): 7 mm case hole clocked to a 7 mm radial '
             'drilling, internal axial 7 mm drilling (~60 mm) up the head to a 7 mm cross-drilling at the TOP of the bore '
             '(v3.3 entry level): v3.3 hydraulics, no dead leg, transfer groove minimal',
        sections=[sec('90 deg turn into the 7 mm case hole', 0.007, 1.1), sec('transfer + 90 deg into the axial drilling', 0.007, 1.1),
                  sec('axial + radial drillings friction (60 + 17 mm)', 0.007, 0.0, L=0.077),
                  sec('90 deg into the cross-drilling', 0.007, 1.1), sec('exit into the 10 mm bore', 0.007, 1.0)],
        z_entry=Z['v33_cross'], d_entry=7.0, n_feeds=1, entry_note='top of the bore (flow-through)')
    a_ann2 = 17.5e-6
    s_ann2 = sec('annulus >= 17.5 mm2, half flow each way to the 45 deg feeds (21.9 mm)', a_ann2, 1.0, frac=0.5, L=0.0219, is_area=True)
    s_ann2['Dh'] = 4 * a_ann2 / (2 * (2.5e-3 + 7e-3))
    v['E2_low_4feeds_4p5mm'] = dict(
        note='example compliant layout B: 8 mm case hole, annulus 2.5 x 7 mm (17.5 mm2), 4 radial feeds 4.5 mm at 45/135/225/315 deg '
             'from the hole, PLUS a dead-leg filler sleeve above the entry (volume above the entry <= 0.8 cm3)',
        sections=[sec('90 deg turn into the 8 mm case hole', 0.008, 1.1), s_ann2,
                  sec('branch into a 4.5 mm feed', 0.0045, 1.0, frac=0.25), sec('feed friction (22 mm)', 0.0045, 0.0, frac=0.25, L=0.022),
                  sec('exit into the 10 mm bore', 0.0045, 1.0, frac=0.25)],
        z_entry=Z_LOW_ENTRY, d_entry=4.5, n_feeds=4, entry_note='low, 4 balanced feeds, filler sleeve required')
    return v


# ------------------------------------------------------------------------------------------------ helpers (flash, vapour)
def flash_state(P, h_in):
    hl = CP.PropsSI('H', 'P', P, 'Q', 0, F); hv = CP.PropsSI('H', 'P', P, 'Q', 1, F)
    x = (h_in - hl) / (hv - hl)
    rl = CP.PropsSI('D', 'P', P, 'Q', 0, F); rv = CP.PropsSI('D', 'P', P, 'Q', 1, F)
    alpha = (x / rv) / (x / rv + (1 - x) / rl) if x > 0 else 0.0
    return x, alpha


def choked_flux_isentropic(P1, s1, h1, pmin=1.0e5, n=200):
    """max over p of rho(p,s1) sqrt(2(h1 - h(p,s1))): HEM / real-gas choked mass flux [kg/m2 s]."""
    best = 0.0
    for p in np.geomspace(pmin, P1 * 0.9999, n):
        rho = CP.PropsSI('D', 'P', p, 'S', s1, F); h = CP.PropsSI('H', 'P', p, 'S', s1, F)
        g = rho * math.sqrt(max(2 * (h1 - h), 0.0))
        best = max(best, g)
    return best


def ideal_gas_Qcrit(CdA, gamma, Rgas, Tk):
    """volumetric (at the upstream state) choked flow capacity: Cd A sqrt(g R T) (2/(g+1))^((g+1)/(2(g-1)))."""
    return CdA * math.sqrt(gamma * Rgas * Tk) * (2 / (gamma + 1)) ** ((gamma + 1) / (2 * (gamma - 1)))


# ------------------------------------------------------------------------------------------------ main
def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    raw = open(MECH, 'rb').read()
    sha16 = hashlib.sha256(raw).hexdigest()[:16]
    mech = json.loads(raw)
    o3b = mech['O3b_riser_to_low_inlet']
    coil = mech['O3_coils'][0]
    stab = [s for s in json.load(open(os.path.join(DATA, 'stability_v2.json'))) if abs(s['D_port_m'] - 0.025) < 1e-6]
    tt = json.load(open(os.path.join(DATA, 'throttle_trade_v2.json')))['rows']
    head = json.load(open(os.path.join(DATA, 'headend_thermal_v2.json')))
    res = dict(id='low_inlet_check', version='v2p3', date='2026-10-12', owner='Combustion', script='02-combustion/src/low_inlet_check.py',
               request='lead follow-up 2026-10-12: Combustion judgement on the LOW INLET before Mechanical commits CAD v3.4',
               input_reviewed=dict(file='03-cad/calcs/hose_routing_trade_v2.json', sha256_16=sha16, sha_expected=MECH_SHA16,
                                   sha_ok=(sha16 == MECH_SHA16), concept=o3b['inlet_concept'],
                                   manifold_volume_estimate_cm3=o3b['manifold_volume_estimate_cm3'],
                                   riser_z_mm=o3b['riser_z_mm'], hose_length_m=coil['hose_length_m']),
               basis=dict(budget_Pa=T(BUDGET_PA, 'ASSUMED in every v2 simulation', 'grain_q1d 2.5 bar at 0.25 kg/s ~ mdot^2'),
                          Cd=T(CD, 'ASSUMED'), K_values=T('handbook ranges, Idelchik / Crane type', 'ASSUMED'),
                          cad_stations_mm=T(Z, 'DERIVED', 'reading of Mechanical parts_engine.py v3.3 primitives (read only)'),
                          low_entry_z_mm=T(Z_LOW_ENTRY, 'ESTIMATE', 'mid between g2 top 128.29 and bolt hole 133.84; plug grows 3-8 mm in v3.4')))
    props = {k: liq(t) for k, t in TEMPS.items()}
    res['n2o_liquid_CoolProp'] = r({k: dict(rho_kg_m3=p['rho'], Psat_Pa=p['Psat'], a_m_s=p['a']) for k, p in props.items()})

    # ---------------------------------------------------------------- 1. losses, budget, flash, ceiling
    variants = inlet_variants()
    GT = GTable()
    loss = {}
    for name, vv in variants.items():
        row = dict(note=vv['note'])
        for case, (md, tk) in {'0p26_25C': (0.26, TEMPS['25C']), '0p241_20C': (0.241, TEMPS['20C']), '0p26_15C': (0.26, TEMPS['15C'])}.items():
            dpi, secs = path_dp(vv['sections'], md, tk)
            dpc, items = common_line(md, tk)
            p = props[[k for k, t in TEMPS.items() if t == tk][0]]
            P_man = p['Psat'] - dpc - dpi
            x, alpha = flash_state(P_man, p['h'])
            row[case] = dict(inlet_dp_Pa=dpi, sections=secs, rest_of_line_Pa=dpc, rest_items_Pa=items, total_line_Pa=dpc + dpi,
                             budget_Pa=BUDGET_PA * (md / 0.26) ** 2, within_budget=(dpc + dpi) <= BUDGET_PA * (md / 0.26) ** 2,
                             P_manifold_Pa=P_man, below_Psat_Pa=p['Psat'] - P_man, flash_quality_eq=max(x, 0.0), void_fraction_eq=alpha)
        # pintle area at the 100 % point (Pc 25.0 bar, mdot_ox 0.241 kg/s), Dyer table with metastable-liquid inlet
        ceil = {}
        for k, tk in TEMPS.items():
            dpi, _ = path_dp(vv['sections'], 0.241, tk)
            dpc, _ = common_line(0.241, tk)
            P1 = props[k]['Psat'] - dpc - dpi
            Pc = 25.0e5
            if P1 <= Pc * 1.02:
                ceil[k] = dict(P1_Pa=P1, feasible=False, note='manifold at or below Pc: 100 % point unreachable')
                continue
            G = GT.G(P1, tk, Pc, 'dyer')
            A = 0.241 / (CD * G)
            h = pintle_lift(A) if A < pintle_area(0.0042) else float('nan')
            ceil[k] = dict(P1_Pa=P1, dP_inj_Pa=P1 - Pc, A_req_mm2=A * 1e6, lift_req_mm=h * 1e3 if math.isfinite(h) else None,
                           A_stop_4p2mm_mm2=pintle_area(0.0042) * 1e6, feasible=bool(math.isfinite(h)),
                           note='Dyer with metastable-liquid inlet = OPTIMISTIC when the manifold is below Psat (equilibrium flash ignored)')
        row['pintle_at_100pct'] = ceil
        loss[name] = row
    res['1_losses_budget_flash'] = r(loss)

    # ---------------------------------------------------------------- 2. distribution, side load, offset sensitivity
    pts = []
    for s in stab:
        tr = min(tt, key=lambda q: abs(q['frac'] - s['frac']))
        pts.append(dict(frac=s['frac'], Pc=s['Pc_Pa'], dP_inj=s['dP_over_Pc'] * s['Pc_Pa'], mdot=tr['mdot_ox'], lift=tr['b_lift_m']))
    pts.insert(0, dict(frac='design_max_0p26', Pc=stab[0]['Pc_Pa'], dP_inj=stab[0]['dP_over_Pc'] * stab[0]['Pc_Pa'], mdot=0.26,
                       lift=pintle_lift(0.26 / 0.2266 * pintle_area(tt[0]['b_lift_m']))))
    rho20 = props['20C']['rho']
    feeds = {'as_drawn_1x3mm': (1, circ(0.003)), 'v33_1x6mm': (1, circ(0.006)), 'E1_1x7mm_top': (1, circ(0.007)),
             'single_10mps_1x6p7mm': (1, circ(0.0067)), 'E2_4x4p5mm': (4, circ(0.0045))}
    dist = []
    for pnt in pts:
        row = dict(frac=pnt['frac'], Pc_Pa=pnt['Pc'], dP_inj_Pa=pnt['dP_inj'], mdot_ox=pnt['mdot'], lift_mm=pnt['lift'] * 1e3,
                   seat_gap_um=pnt['lift'] * math.sin(ALPHA) * 1e6,
                   flux_first_harmonic_per_um_offset_pct=100 * math.cos(ALPHA) / (pnt['lift'] * 1e6 * math.sin(ALPHA)))
        for fname, (n, a) in feeds.items():
            m1 = pnt['mdot'] / n
            v = m1 / (rho20 * a)
            q = 0.5 * rho20 * v ** 2
            F1 = m1 * v
            Fnet = F1 if n == 1 else 0.4 * F1          # 4 feeds: opposite pair at +/-10 % flow -> (1.1^2 - 0.9^2) F1
            row[fname] = dict(v_m_s=v, q_over_dPinj=q / pnt['dP_inj'], flux_asym_bound_pct=100 * 0.5 * q / pnt['dP_inj'],
                              lateral_jet_N=Fnet)
        dist.append(row)
    lever = {}
    zg = Z['guide_bush'][0]; s_sup = Z['carriage_pin'] - 0.5 * sum(Z['guide_bush'])
    for nm, ze in (('low_entry', Z_LOW_ENTRY), ('v33_entry', Z['v33_cross'])):
        a_arm = zg - ze
        lever[nm] = dict(arm_to_guide_mm=a_arm, support_spacing_mm=s_sup,
                         friction_per_N_side_load=MU_GUIDE * (2 * a_arm + s_sup) / s_sup)
    res['2_distribution_side_load'] = r(dict(
        rows=dist, guide_lever=lever,
        notes=['q = feed velocity head (20 C liquid); flux bound 0.5 q/dP_inj assumes the whole feed head appears as a '
               'circumferential pressure variation at the seat (upper bound; decay over the 13-17 mm to the seat not credited)',
               'lateral jet = mdot v (full momentum transfer onto the needle body, upper bound); 4 feeds: opposite pair +/-10 % '
               '(ASSUMED imbalance) -> 0.4 x one feed',
               'guide lever: two supports (TC-11 bushing, carriage pin) 7 mm apart on CAD v3.3 stations; friction = mu (R1 + R2), '
               f'mu {MU_GUIDE} (S3 baseline); v3.4 guide layout may differ (Mechanical)',
               'needle lateral offset e changes the local seat gap by e cos(15 deg); the mean gap (total flow) is unchanged to first order']))

    # ---------------------------------------------------------------- 3. volumes, dead leg, trapped liquid
    v_bore_cad = bore_volume_mm3() * 1e-9
    v_man_mech = o3b['manifold_volume_estimate_cm3']['v33_total'] + o3b['manifold_volume_estimate_cm3']['added_annulus'] + \
        o3b['manifold_volume_estimate_cm3']['added_passage']
    v_hose = coil['hose_length_m'] * circ(HOSE_ID)
    v_riser = 0.07 * circ(TUBE_ID)
    v_block = circ(0.0045) * 0.016
    v_fixed = L_FIXED * circ(TUBE_ID)
    V_valve_at_coil = v_hose + v_riser + v_block + V_FITTINGS + v_man_mech * 1e-6
    V_valve_at_top = V_valve_at_coil + v_fixed
    V_ref_v2 = 0.26 * circ(HOSE_ID) + 3.3e-6 + V_FITTINGS
    V_ref_O1 = 0.40 * circ(HOSE_ID) + 3.3e-6 + V_FITTINGS
    trapped = {}
    for k, tk in TEMPS.items():
        p = props[k]
        T_relief = brentq(lambda t: CP.PropsSI('P', 'T', t, 'D', p['rho'], F) - 7.5e6, tk, tk + 40)
        trapped[k] = dict(mass_g_valve_at_coil=p['rho'] * V_valve_at_coil * 1e3, mass_g_valve_at_top=p['rho'] * V_valve_at_top * 1e3,
                          dPdT_isochoric_bar_K=CP.PropsSI('d(P)/d(T)|Dmass', 'T', tk, 'Dmass', p['rho'] * 1.0001, F) / 1e5,
                          dT_liquid_full_to_7p5MPa_K=T_relief - tk)
    hv = {}
    for case, d in head['cases'].items():
        if 'gnc v2' not in case:
            continue
        for var, vd in d['variants'].items():
            hv.setdefault('T_head_max_in_flight_K', []).append(vd['T_head']['max_in_flight_K'])
            hv.setdefault('T_head_at_relight_K', []).append(vd['T_head']['at_relight_K'])
            hv.setdefault('T_case_fwd_at_relight_K', []).append(vd['T_case_fwd']['at_relight_K'])
    res['3_volumes'] = r(dict(
        manifold_mech_estimate_cm3=T(v_man_mech, 'ESTIMATE (Mechanical O3b)'),
        bore_annulus_cad_v33_cm3=T(v_bore_cad * 1e6, 'DERIVED', '10 mm bore 124.59-204.59 mm around the 6 mm body / 3 mm stem; '
                                   'Mechanical 3.3 cm3 matches the v3.2 52 mm wetted bore -> Mechanical to measure the v3.4 solid'),
        dead_leg_above_entry_cm3={'low_entry_3mm': dead_leg_mm3(Z_LOW_ENTRY, 3.0) * 1e-3, 'low_entry_4p5mm': dead_leg_mm3(Z_LOW_ENTRY, 4.5) * 1e-3,
                                  'v33_cross_6mm': dead_leg_mm3(Z['v33_cross'], 6.0) * 1e-3, 'tag': 'DERIVED (CAD v3.3 stations)'},
        valve_to_seat_cm3=dict(valve_at_coil_fixed_end=V_valve_at_coil * 1e6, valve_at_zone_top=V_valve_at_top * 1e6,
                               ref_v2_feed_line_checks=V_ref_v2 * 1e6, ref_O1_0p40m=V_ref_O1 * 1e6,
                               items_cm3=dict(hose=v_hose * 1e6, riser=v_riser * 1e6, block=v_block * 1e6, fittings=V_FITTINGS * 1e6,
                                              manifold=v_man_mech, fixed_line=v_fixed * 1e6),
                               tag='DERIVED from Mechanical O3b/O3_coils + ASSUMED fittings; fixed line ESTIMATE'),
        trapped_liquid=trapped,
        head_thermal_v2=dict(T_crit_K=CP.PropsSI('Tcrit', F),
                             **{k: [min(x for x in v if x is not None), max(x for x in v if x is not None)] for k, v in hv.items()},
                             src='headend_thermal_v2.json (gnc v2 duty cycles, all variants), SIM'),
        n2o_side_cooling_basis='headend_thermal_v2 credits forced N2O cooling over a 52 mm wetted bore; a low entry leaves ~7-10 mm '
                               'of flowing bore below the entry: the dead leg is stagnant (not covered by that model)'))

    # ---------------------------------------------------------------- 4. priming
    A_b = pintle_area(1.0e-4)
    R_N2 = 8.314462618 / 0.0280134; R_N2O = 8.314462618 / 0.0440128
    g_n2o = CP.PropsSI('CPMASS', 'T', 293.15, 'P', 1e5, F) / CP.PropsSI('CVMASS', 'T', 293.15, 'P', 1e5, F)
    Qn2 = ideal_gas_Qcrit(CD * A_b, 1.4, R_N2, 293.15)
    Qno = ideal_gas_Qcrit(CD * A_b, g_n2o, R_N2O, 293.15)
    vols = {'ref_v2': V_ref_v2, 'ref_O1': V_ref_O1, 'O3b_valve_at_coil': V_valve_at_coil, 'O3b_valve_at_top': V_valve_at_top}
    res['4_priming'] = r(dict(
        bleed_area_0p10mm_mm2=A_b * 1e6, Q_crit_N2_293K_cm3_s=Qn2 * 1e6, Q_crit_N2O_vap_293K_cm3_s=Qno * 1e6,
        vent_time_constant_s={k: dict(N2=v / Qn2, N2O_vapour=v / Qno) for k, v in vols.items()},
        liquid_flow_through_bleed_g_s=CD * A_b * math.sqrt(2 * props['20C']['rho'] * (props['20C']['Psat'] - 1e5)) * 1e3,
        isentropic_bound=T('N2 847-913 K, N2O vapour 614-646 K at 45-60 bar: volume-independent', 'DERIVED', 'feed_line_checks_v2.json'),
        note='any valve inflow above Q_crit compresses the line gas whatever the volume (Q_crit ~ Cd A_bleed c*, volume-independent); '
             'a larger volume lengthens the compression (more wall heat loss) but carries more hot gas to the manifold end; '
             'a DEAD LEG above the feed entry is never vented by the bleed: its gas is compressed dead-ended (rule premise fails)'))

    # ---------------------------------------------------------------- 5. relight purge of a vapour-filled line
    purge = {}
    states = {'sat_vapour_20C': ('Q', 1.0, 293.15), 'supercritical_7p5MPa_330K': ('P', 7.5e6, 330.0), 'supercritical_7p5MPa_360K': ('P', 7.5e6, 360.0)}
    for sn, (kind, val, tk) in states.items():
        if kind == 'Q':
            P1 = CP.PropsSI('P', 'T', tk, 'Q', 1, F); s1 = CP.PropsSI('S', 'T', tk, 'Q', 1, F); h1 = CP.PropsSI('H', 'T', tk, 'Q', 1, F)
            rho1 = CP.PropsSI('D', 'T', tk, 'Q', 1, F)
        else:
            P1 = val; s1 = CP.PropsSI('S', 'T', tk, 'P', P1, F); h1 = CP.PropsSI('H', 'T', tk, 'P', P1, F)
            rho1 = CP.PropsSI('D', 'T', tk, 'P', P1, F)
        G = choked_flux_isentropic(P1, s1, h1)
        row = dict(P1_Pa=P1, rho1=rho1, G_choked_kg_m2s=G)
        for lift_name, h in (('ign_lift_12p5pct', tt[-1]['b_lift_m']), ('ign_lift_20pct', tt[-2]['b_lift_m'])):
            A = pintle_area(h)
            Qv = CD * A * G / rho1
            row[lift_name] = dict(lift_mm=h * 1e3, A_mm2=A * 1e6, Q_cm3_s=Qv * 1e6,
                                  purge_s={k: v / Qv for k, v in vols.items()})
        purge[sn] = row
    res['5_relight_purge'] = r(dict(states=purge, window_s=T(0.35 - 0.12, 'REQ/DERIVED', 'combustion.json v2.3 igniter.sequence: '
                                                                                   'ignition lift t 0.12 s, ignition check t 0.35 s'),
                                    note='upper bound of the purge time if the whole valve->seat volume is vapour/supercritical at relight '
                                         '(valve closed in coasts, block on the hot case, riser 3 mm from the pre-chamber case). '
                                         'Pre-existing gap: the v2 reference volume already exceeds the window if fully vapour.'))

    # ---------------------------------------------------------------- 6. chug-related feed quantities
    p20 = props['20C']
    s100 = stab[0]
    dPi = s100['dP_over_Pc'] * s100['Pc_Pa']; m100 = tt[0]['mdot_ox']
    R_inj = 2 * dPi / m100
    rho_v = CP.PropsSI('D', 'T', 293.15, 'Q', 1, F); a_v = CP.PropsSI('A', 'T', 293.15, 'Q', 1, F)
    I_path = {'as_drawn': (L_TANK_VALVE + L_FIXED + 0.07) / circ(TUBE_ID) + 0.252 / circ(HOSE_ID) + 0.023 / circ(0.003),
              'E1_top_entry': (L_TANK_VALVE + L_FIXED + 0.07) / circ(TUBE_ID) + 0.252 / circ(HOSE_ID) + 0.077 / circ(0.007)}
    chug = {}
    for nm, (V_l, V_v) in {'liquid_4p5cm3': (4.5e-6, 0.0), 'liquid_5p8cm3': (5.8e-6, 0.0),
                           'liquid_4p5_plus_vapour_dead_leg_4p1cm3': (4.5e-6 - 4.1e-6, 4.1e-6),
                           'liquid_4p5_plus_vapour_1cm3': (3.5e-6, 1.0e-6)}.items():
        C = V_l / p20['a'] ** 2 + V_v / a_v ** 2
        row = dict(C_kg_per_Pa=C, tau_RC_ms=R_inj * C * 1e3)
        for ip, I in I_path.items():
            row[f'f_feed_Hz_{ip}'] = 1 / (2 * math.pi * math.sqrt(I * C))
        chug[nm] = row
    res['6_chug_feed'] = r(dict(
        rows=chug, theta_g_ms=stab[0]['theta_g_s'] * 1e3, GM_100pct_tau1_10ms=[stab[0]['GM_tau1ms'], stab[0]['GM_tau10ms']],
        dtl_band_Hz=[1 / (2 * (stab[0]['theta_g_s'] + 0.010)), 1 / (2 * (stab[0]['theta_g_s'] + 0.001))],
        R_inj_Pa_s_per_kg=R_inj,
        notes=['double-time-lag chug model (stability_v2) has no feed dynamics: margins unchanged only for a liquid-full manifold',
               'vapour compliance uses the single-phase isentropic sound speed of saturated vapour (LOWER bound on compliance; '
               'condensation/evaporation make it larger)', 'inertance tank->manifold: tank-valve 0.15 m ASSUMED, fixed line, hose, '
               'riser, inlet passage; feed mode f = 1/(2 pi sqrt(I C)), lumped (indicative only)',
               'dtl_band = 1/(2(theta_g + tau)) for tau 1-10 ms (indicative)']))

    # ---------------------------------------------------------------- verdict (text built from the computed values above)
    def rng(vals, fmt='{:.1f}'):
        lo, hi = min(vals), max(vals)
        return fmt.format(lo) if abs(hi - lo) < 1e-9 * max(1.0, abs(hi)) else (fmt + '-' + fmt).format(lo, hi)
    drawn = [loss[k] for k in loss if k.startswith('V1_as_drawn')]
    mis = loss['V1b_as_drawn_hole4p5mm_180deg_misaligned']
    v33, e1, e2 = loss['V0_v33_bonnet_reference'], loss['E1_top_entry_7mm'], loss['E2_low_4feeds_4p5mm']
    pas = [s for s in drawn[0]['0p26_25C']['sections'] if '3 mm passage friction' in s['name'] or 'exit' in s['name']]
    dp_passage_only = sum(s['dp_kPa'] for s in pas) / 100.0
    v_p = [s['v_m_s'] for s in drawn[0]['0p26_25C']['sections'] if s['name'].startswith('3 mm passage')][0]
    lifts_d = [d_['pintle_at_100pct'][k]['lift_req_mm'] for d_ in drawn for k in TEMPS if d_['pintle_at_100pct'][k].get('lift_req_mm')]
    lifts_0 = [v33['pintle_at_100pct'][k]['lift_req_mm'] for k in TEMPS]
    dmax = dist[0]; d100 = dist[1]
    fr_low = lever['low_entry']['friction_per_N_side_load']; fr_v33 = lever['v33_entry']['friction_per_N_side_load']
    dl_low = dead_leg_mm3(Z_LOW_ENTRY, 3.0) * 1e-3; dl_v33 = dead_leg_mm3(Z['v33_cross'], 6.0) * 1e-3
    hmin = min(x for x in hv['T_head_max_in_flight_K'] if x is not None); hmax = max(x for x in hv['T_head_max_in_flight_K'] if x is not None)
    ch = res['6_chug_feed']['rows']; pr = res['4_priming']; pg = res['5_relight_purge']['states']['sat_vapour_20C']
    res['verdict'] = dict(
        overall='ACCEPT WITH CONDITIONS the low inlet ROUTING (block on the case OD at the head plug); REJECT the internal flow path as drawn',
        reject_reasons=[
            f'single 3 mm passage: {v_p:.1f} m/s at 0.26 kg/s, 25 C; inlet path {rng([d_["0p26_25C"]["inlet_dp_Pa"] / 1e5 for d_ in drawn])} bar '
            f'(4-5 mm case hole, aligned; {dp_passage_only:.1f} bar from the passage friction + exit alone; '
            f'{mis["0p26_25C"]["inlet_dp_Pa"] / 1e5:.1f} bar if 180 deg out of clock) vs {BUDGET_PA / 1e5:.2f} bar for the WHOLE line',
            f'manifold {rng([d_["0p26_25C"]["below_Psat_Pa"] / 1e5 for d_ in drawn])} bar below Psat at 25 C: equilibrium flash quality '
            f'{rng([d_["0p26_25C"]["flash_quality_eq"] for d_ in drawn], "{:.2f}")} (void {rng([100 * d_["0p26_25C"]["void_fraction_eq"] for d_ in drawn], "{:.0f}")} %) '
            f'upstream of the metering seat; 100 % lift (Dyer, optimistic) {rng(lifts_d, "{:.2f}")} mm vs {rng(lifts_0, "{:.2f}")} mm (v3.3 path)',
            f'single jet on the needle body: {dmax["as_drawn_1x3mm"]["lateral_jet_N"]:.1f} N at 0.26 kg/s ({d100["as_drawn_1x3mm"]["lateral_jet_N"]:.1f} N at 100 %), '
            f'{lever["low_entry"]["arm_to_guide_mm"]:.0f} mm below the guide -> ~{fr_low * dmax["as_drawn_1x3mm"]["lateral_jet_N"]:.0f} N guide friction (ESTIMATE, mu {MU_GUIDE}); '
            f'feed head / injector dP {100 * dmax["as_drawn_1x3mm"]["q_over_dPinj"]:.0f} % -> first-harmonic flux asymmetry up to '
            f'{dmax["as_drawn_1x3mm"]["flux_asym_bound_pct"]:.0f} %',
            f'low entry leaves {dl_low:.1f} cm3 of the 10 mm bore as a dead leg above it (v3.3 {dl_v33:.1f} cm3); head wall in flight '
            f'{hmin:.0f}-{hmax:.0f} K > T_crit {CP.PropsSI("Tcrit", F):.1f} K -> vapour pocket; bleed cannot vent it (priming dead end)'],
        conditions=[
            f'C1 every flow section >= 35 mm2 (<= 10 m/s at 0.26 kg/s, 25 C); inlet path <= v3.3 ({v33["0p26_15C"]["inlet_dp_Pa"] / 1e5:.2f} bar at '
            f'0.26 kg/s, 15 C), target <= 1.0 bar; line total at 15 C <= {BUDGET_PA / 1e5:.2f} bar (v3.3 {v33["0p26_15C"]["total_line_Pa"] / 1e5:.2f}, '
            f'example E1 {e1["0p26_15C"]["total_line_Pa"] / 1e5:.2f}, E2 {e2["0p26_15C"]["total_line_Pa"] / 1e5:.2f})',
            f'C2 flow-through manifold: entry at the TOP of the bore (v3.3 hydraulics, example E1) or <= {dl_v33:.1f} cm3 above a low entry (filler sleeve)',
            f'C3 a low entry needs >= 4 equal feeds (example E2: net lateral jet {dmax["E2_4x4p5mm"]["lateral_jet_N"]:.2f} N, flux bound '
            f'{dmax["E2_4x4p5mm"]["flux_asym_bound_pct"]:.2f} %) and an annulus >= 17.5 mm2; a single path needs the case hole clocked to the passage (pin)',
            'C4 no single seal between the N2O annulus and chamber gas: two seals + an overboard-vented interspace (reject the +3 mm variant)',
            'C5 the <= 15 um / Cv >= 2.2 filter (OI-7) goes downstream of the hose and the riser weld (bonnet screen seat deleted)',
            f'C6 relief <= 7.5 MPa covers the valve->seat volume (liquid-full: relief after {rng([t["dT_liquid_full_to_7p5MPa_K"] for t in trapped.values()])} K '
            f'of warming); block isolated from the case, riser shielded (Mechanical G5)',
            f'C7 relight with a vapour-filled line: purge at the 12.5 % ignition lift {pg["ign_lift_12p5pct"]["purge_s"]["O3b_valve_at_coil"]:.2f} s '
            f'(valve at the coil end) / {pg["ign_lift_12p5pct"]["purge_s"]["O3b_valve_at_top"]:.2f} s (valve at the zone top) vs the 0.23 s window '
            f'(v2 basis {pg["ign_lift_12p5pct"]["purge_s"]["ref_v2"]:.2f} s, pre-existing) -> sequence owners add a pre-purge or a T-gated check'],
        unchanged=['ENG-05 tail-off and dribble: all added volume is upstream of the metering seat (shutdown: pintle first, valve after seating)',
                   f'priming rule kept for a flow-through manifold: isentropic bound volume-independent; bleed vents {pr["Q_crit_N2_293K_cm3_s"]:.0f} cm3/s N2 '
                   'whatever the volume', f'chug (DTL) margins for a liquid-full manifold: R*C {ch["liquid_4p5cm3"]["tau_RC_ms"]:.2f} ms << theta_g '
                   f'{res["6_chug_feed"]["theta_g_ms"]:.1f} ms; with the vapour dead leg {ch["liquid_4p5_plus_vapour_dead_leg_4p1cm3"]["tau_RC_ms"]:.1f} ms and the feed mode '
                   f'{ch["liquid_4p5cm3"]["f_feed_Hz_as_drawn"]:.0f} -> {ch["liquid_4p5_plus_vapour_dead_leg_4p1cm3"]["f_feed_Hz_as_drawn"]:.0f} Hz '
                   '(not in the DTL model)'],
        verification=['CF-3: line loss with a test-only manifold tap, spray symmetry at 100/25/12.5 % (high-speed imaging), thermocouple at the '
                      'bore top during priming, P_feed and Pc >= 1 kHz', 'B-PNT-1: needle friction under flow', 'T1: thrust misalignment'],
        pre_existing_findings_kept_as_evidence=[
            f'v2 line estimate allotted K 1.0 on the hose head to the bonnet inlet; the CAD v3.3 6 mm drillings give {v33["0p26_25C"]["inlet_dp_Pa"] / 1e5:.2f} bar '
            f'(0.26 kg/s, 25 C) by this K-method: v3.3 line total {v33["0p26_25C"]["total_line_Pa"] / 1e5:.2f} bar at 25 C (> {BUDGET_PA / 1e5:.2f}, non-binding: '
            f'the ceiling binds at 15 C, total {v33["0p26_15C"]["total_line_Pa"] / 1e5:.2f} bar)',
            f'relight purge of a fully vapour line already exceeded the 0.23 s window on the v2 basis ({pg["ign_lift_12p5pct"]["purge_s"]["ref_v2"]:.2f} s at the '
            '12.5 % lift); not checked in v2.3',
            f'manifold volume: CAD v3.3 primitives give {v_bore_cad * 1e6:.2f} cm3 for the 10 mm bore annulus alone (124.59-204.59 mm) vs Mechanical 3.3 cm3 '
            '(matches the v3.2 52 mm wetted bore) -> measure the v3.4 solid',
            f'the v3.3 cross-drilling also leaves a {dl_v33:.1f} cm3 dead leg at the stem seal (not flagged before)'])
    fn = os.path.join(outdir, 'low_inlet_check_v2p3.json')
    with open(fn, 'w') as f:
        json.dump(res, f, indent=1)
    print(fn)
    return res


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else DATA)
