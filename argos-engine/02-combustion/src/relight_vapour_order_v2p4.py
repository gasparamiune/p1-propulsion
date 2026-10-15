"""Vapour next to the pintle at the A1 RELIGHT, in flow order (Combustion v2.4; LEAD relay 2026-10-13, new analysis item 2).

Question (LEAD): what governs ignition is the vapour between the liquid and the pintle, in flow order, at RELIGHT. GNC shows
f_z > 0 (apparent gravity toward the engine) for >= 11.4 s at about +8 m/s2 before the relight command; Mechanical gives the
coast heat input to the MV-to-seat segment (875 J LO to 5.0 kJ HI over the 18.67 s A1 coast). Result wanted: the vapour
volume next to the pintle at RELIGHT (LO and HI), whether W 0.65 s lights it, and if not a comparison of the fixes
(a) head-end prime bleed, (d) MV opened early in the steady descent with the pintle seated, (b) every relight planned as a
vapour start with W 1.05 s.

Inputs (read only; sha256/16 recorded): Mechanical 04-fea/thermal/segment_heat_budget_v1.json and segment_heat_coast_v1.json
(heat by element, LO/HI, and the FE manifold-bore Q(t)); Mechanical 03-cad/src/calcs/inlet_e1m_v1.json (valve-to-seat volumes
and head stations, DESIGN/ESTIMATE) and hose_routing_trade_v2.json (O3b coil ends); GNC staging_v3.1 coast_accel_a1_v1.json
(A1 specific force MECO -> RELIGHT); Combustion post_abort_pocket_v2p4.json (purge rate, abort table) and
start_latency_v2p4.json (to rebuild the 200 000-sample E1 -> E2 liquid-line distribution exactly as post_abort_pocket_v2p4).

Method (each step tagged in the output):
 1. Properties at Mechanical's coast saturation state T_sat 289.48 K (CoolProp; N2O viscosity bound 1e-3 Pa s, CoolProp has
    no N2O viscosity model).
 2. Segment in flow order MV -> seat with volume, elevation (engine frame, z above the pivot, +Z forward; 'up' while f_z > 0)
    and coast heat per element (Mechanical's split; one coil hose end assigned to each side of the U-bottom).
 3. Elevations make an inverted U: the wall line falls from the zone-top module (~z 255) to the coil fixed end (z 45, the
    U-bottom), the coil rises to its engine end (z 62), the riser and head drillings rise to the bonnet crest (bore top,
    z 204.6), and the 10 mm manifold bore (dead-end leg, closed by the seat) falls from the crest to the seat (z 110.6).
    Vapour formed between the U-bottom and the seat cannot reach the MV/S1 by buoyancy in either coast phase; vapour formed
    upstream of the U-bottom rises to the module and leaves through S1 (it is behind the liquid in flow order).
 4. Bubble mobility per passage (Eotvos number; Taylor-bubble drift in the Wallis / White-Beardmore form of
    retained_vapour_check_v2p4; inclined coil bracketed between Fr 0.10 and Bendiksen's large-Eo inclined form) at the
    coast-up and descent specific forces; time to clear each leg; filter-mesh bubble point against the buoyancy head.
 5. Vapour generated in the U = heat in the U x v_fg/h_fg (all generated vapour retained; no condensation sink; the S1-crack
    subcooling credit shown separately), scaled from Mechanical's 18.67 s coast to GNC's window (p50 / max) with the FE
    bore Q(t) shape (linear extrapolation of the last 5 samples, ASSUMED shape for every element).
 6. Pocket ahead of the first sustained liquid = min(vapour in the U, U volume - liquid kept in the dead-end bore leg); a
    liquid plug at the seat is counted as dead time (V_plug / Q_liquid at the ignition lift, converted to an equivalent
    pocket with the purge rate) - conservative. Every case whose U overflows also counts the quasi-steady wall-line and
    module void of the overflow (drift-flux estimate, an upper bound; the first v2.4 run counted it for HI only).
 7. P(abort of a would-be light) at W 0.65 / 0.85 / 1.05 s with the post_abort_pocket_v2p4 model (liquid-line E1 -> E2
    distribution + purge 0.015555 s/cm3 at the 0.2039 mm lift; SIM C7 basis scaled linearly with volume).
 8. Options (a), (d), (b): residual pocket, P_abort, N2O cost, bleed size (choked-vapour estimate), inventory at W.
usage: python -I relight_vapour_order_v2p4.py MECH_BUDGET MECH_COAST MECH_INLET MECH_HOSE GNC_COAST DATA_V2P4_DIR OUT_JSON
"""
from __future__ import annotations
import json, math, os, sys, hashlib
sys.dont_write_bytecode = True
import numpy as np
import CoolProp.CoolProp as CP
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import start_latency_v2p4 as SL

G0 = 9.80665
MU_BOUND = 1.0e-3            # Pa s, upper bound (CoolProp has no N2O viscosity); N_f stays large
_trap = getattr(np, "trapezoid", None) or getattr(np, "trapz")
PURGE = 0.31 / 21.42 * 0.2191572 / 0.2039   # s per cm3 at the v2.8 lift (post_abort_pocket_v2p4, DERIVED)


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def props(T):
    P = CP.PropsSI('P', 'T', T, 'Q', 0, 'N2O')
    rl = CP.PropsSI('D', 'T', T, 'Q', 0, 'N2O'); rv = CP.PropsSI('D', 'T', T, 'Q', 1, 'N2O')
    hfg = CP.PropsSI('H', 'T', T, 'Q', 1, 'N2O') - CP.PropsSI('H', 'T', T, 'Q', 0, 'N2O')
    sig = CP.PropsSI('surface_tension', 'T', T, 'Q', 0, 'N2O')
    cpl = CP.PropsSI('C', 'T', T, 'Q', 0, 'N2O')
    dPdT = (CP.PropsSI('P', 'T', T + 0.05, 'Q', 0, 'N2O') - CP.PropsSI('P', 'T', T - 0.05, 'Q', 0, 'N2O')) / 0.1
    return dict(T_K=T, P_Pa=P, rho_l=rl, rho_v=rv, h_fg=hfg, sigma=sig, cp_l=cpl, dPdT_sat_Pa_K=dPdT,
                vap_cm3_per_J=1e6 / (rv * hfg), liq_cm3_per_J=1e6 / (rl * hfg))


def drift(D, g, p):
    """Taylor-bubble drift velocity [m/s] in a vertical tube of diameter D at specific force g (Wallis / White-Beardmore form)."""
    if g <= 0:
        return 0.0, 0.0
    dr = p['rho_l'] - p['rho_v']
    Eo = dr * g * D * D / p['sigma']
    Nf = p['rho_l'] / MU_BOUND * math.sqrt(g * D ** 3 * dr / p['rho_l'])
    if Eo <= 3.37:
        return 0.0, Eo
    Fr = 0.345 * (1 - math.exp(-0.01 * Nf / 0.345)) * (1 - math.exp((3.37 - Eo) / 10.0))
    return Fr * math.sqrt(g * D * dr / p['rho_l']), Eo


def main(budget_f, coast_f, inlet_f, hose_f, gnc_f, d2p4, out_f):
    B = json.load(open(budget_f)); C = json.load(open(coast_f)); IN = json.load(open(inlet_f))
    HO = json.load(open(hose_f)); GN = json.load(open(gnc_f))
    T_sat = float(B['T_sat_coast_K'])
    p = props(T_sat)
    vpj, lpj = p['vap_cm3_per_J'], p['liq_cm3_per_J']
    # ---------------------------------------------------------------- 2-3. segment in flow order (MV -> seat)
    vol = IN['valve_to_seat_volume_cm3']['items']
    st = IN['stations_derived_mm']
    coil = HO['O3_coils'][0]
    z_coil_engine = 1e3 * coil['engine_end_m'][2]; z_coil_fixed = 1e3 * coil['fixed_end_m'][2]
    z_seat = 1e3 * GN['stations']['z_seat_from_pivot_m']
    el = {e['name']: e for e in B['elements']}
    E = lambda name, case: float(el[name]['E_coast_J'][f'isothermal|{case}'])
    ID_wall = 9.525 - 2 * 0.889
    A_wall = math.pi / 4 * ID_wall ** 2
    L_wall = float(el['fixed wall line 3/8 x 0.035 316L, module -> coil (~250 mm)']['A_mm2']) / (math.pi * ID_wall)
    V_wall = A_wall * L_wall / 1e3
    V_U = float(IN['valve_to_seat_volume_cm3']['total'])
    V_seg = 44.0                                                     # LEAD/Mechanical ESTIMATE (v2.8 segment)
    V_mod = V_seg - V_U - V_wall
    nd = B['needle']['E_J']
    fe = B['fe_head_bore']
    hose_end = lambda c: 0.5 * E('coil hose ends 2x -6 JIC swivel + nipple (316)', c)
    rows = [  # name, V cm3, z_from, z_to, D_h mm, side, heat LO, heat HI, note
        ('MV/FS-01 module outlet side', V_mod, 255.0, 240.0, 8.0, 'route', E('MV/FS-01 module, outlet side (316L body)', 'LO'),
         E('MV/FS-01 module, outlet side (316L body)', 'HI'), 'V = 44 - U - wall line (ESTIMATE); zone top ~0.26 m above the pivot (Mechanical)'),
        ('fixed wall line 3/8 x 0.035', V_wall, 240.0, z_coil_fixed, ID_wall, 'route', E('fixed wall line 3/8 x 0.035 316L, module -> coil (~250 mm)', 'LO'),
         E('fixed wall line 3/8 x 0.035 316L, module -> coil (~250 mm)', 'HI'), f'L {L_wall:.0f} mm from Mechanical wetted area'),
        ('union/elbow + fixed-end hose fitting (U-bottom)', 0.0, z_coil_fixed, z_coil_fixed, 8.0, 'route',
         E('line-coil union / 90 deg elbow (316)', 'LO') + hose_end('LO'), E('line-coil union / 90 deg elbow (316)', 'HI') + hose_end('HI'),
         'volume inside the fittings item of the U list; heat counted on the route side (rises up the wall line)'),
        ('coil hose O3b (300 deg, r 54->42)', vol['hose_O3b'], z_coil_fixed, z_coil_engine, 7.9, 'U',
         E('coil hose O3b 0.252 m, PTFE liner 1.0 + SS braid 0.5 (equivalent)', 'LO'), E('coil hose O3b 0.252 m, PTFE liner 1.0 + SS braid 0.5 (equivalent)', 'HI'),
         f'rises {z_coil_engine - z_coil_fixed:.0f} mm over {1e3*coil["hose_length_m"]:.0f} mm (hose_routing_trade_v2 option 1)'),
        ('coil-end fittings, FD-05 TEE + MSS-1', vol['fittings_coil_end'], z_coil_engine, 80.0, 7.75, 'U',
         hose_end('LO') + E('FD-05 TEE + MSS-1 port (316L)', 'LO'), hose_end('HI') + E('FD-05 TEE + MSS-1 port (316L)', 'HI'), ''),
        ('FD-03 riser 3/8 x 0.035', vol['riser'], 80.0, 151.1, ID_wall, 'U', E('FD-03 riser 3/8 x 0.035 316L (~130 mm)', 'LO'),
         E('FD-03 riser 3/8 x 0.035 316L (~130 mm)', 'HI'), ''),
        ('FD-01 block passages (8 mm)', vol['block_passages'], 151.1, st['z_filter_axis'], 8.0, 'U', E('FD-01 inlet block (316L, ~52 g)', 'LO'),
         E('FD-01 inlet block (316L, ~52 g)', 'HI'), 'socket + vertical + radial'),
        ('filter bore 14 mm (radial) + cartridge', vol['filter_bore_open'], st['z_filter_axis'], st['z_filter_axis'], 14.0, 'U',
         E('TC-02 head cap: filter bore 14 x 21 + axial 8 x 7 (6061)', 'LO') * 0.75, E('TC-02 head cap: filter bore 14 x 21 + axial 8 x 7 (6061)', 'HI') * 0.75,
         '15 um mesh between core (inlet) and collecting annulus; TC-02 heat split 0.75 / 0.25 by wetted area (ASSUMED)'),
        ('head axial 8 mm', vol['head_axial'], st['z_filter_axis'] + 7.0, 178.59, 8.0, 'U',
         E('TC-02 head cap: filter bore 14 x 21 + axial 8 x 7 (6061)', 'LO') * 0.25, E('TC-02 head cap: filter bore 14 x 21 + axial 8 x 7 (6061)', 'HI') * 0.25, ''),
        ('bonnet axial 8 mm', vol['bonnet_axial'], 178.59, st['bore_top'], 8.0, 'U',
         E('TC-04 bonnet: axial 8 x 26 + cross 8 x 14 + T4 port (6061)', 'LO') * 0.6, E('TC-04 bonnet: axial 8 x 26 + cross 8 x 14 + T4 port (6061)', 'HI') * 0.6,
         'TC-04 heat split 0.6 / 0.4 by wetted area (ASSUMED)'),
        ('bonnet cross 8 mm + tap stub (CREST)', vol['cross_and_tap_stub'], st['z_cross_axis'], st['z_cross_axis'], 8.0, 'U',
         E('TC-04 bonnet: axial 8 x 26 + cross 8 x 14 + T4 port (6061)', 'LO') * 0.4, E('TC-04 bonnet: axial 8 x 26 + cross 8 x 14 + T4 port (6061)', 'HI') * 0.4,
         'highest point of the U; T4 / P_manifold port at its outer end (stand only)'),
        ('manifold 10 mm bore annulus (dead-end leg to the seat)', vol['manifold_10mm_bore_annulus'], st['bore_top'], z_seat, 2.0, 'U',
         fe['LO']['E_coast_J'] + nd[0], fe['HI']['E_coast_J'] + nd[1], 'FE manifold bore (TC-02/03/04 bore walls) + needle ESTIMATE; gap 2 mm (10/6)'),
    ]
    seg = []
    for r in rows:
        seg.append(dict(name=r[0], V_cm3=r[1], z_from_mm=r[2], z_to_mm=r[3], D_h_mm=r[4], side=r[5], Q_LO_J=r[6], Q_HI_J=r[7], note=r[8]))
    Q = {c: dict(U=sum(s[f'Q_{c}_J'] for s in seg if s['side'] == 'U'), route=sum(s[f'Q_{c}_J'] for s in seg if s['side'] == 'route'))
         for c in ('LO', 'HI')}
    for c in Q:
        Q[c]['total'] = Q[c]['U'] + Q[c]['route']
        Q[c]['mechanical_total_J'] = B['totals'][f'isothermal|{c}']['E_total_J']
    crest = st['bore_top']
    geometry = dict(U_volume_cm3=V_U, segment_cm3=V_seg, module_cm3=V_mod, wall_line_cm3=V_wall, z_U_bottom_mm=z_coil_fixed,
                    z_crest_mm=crest, z_seat_mm=z_seat, z_module_mm=255.0, crest_above_U_bottom_mm=crest - z_coil_fixed,
                    bore_leg_cm3=vol['manifold_10mm_bore_annulus'],
                    upper_trap_above_mesh_cm3=vol['cross_and_tap_stub'] + vol['bonnet_axial'] + vol['head_axial'] + 0.5 * vol['filter_bore_open'],
                    lower_trap_below_mesh_cm3=0.5 * vol['filter_bore_open'] + vol['block_passages'] + vol['riser'] + vol['fittings_coil_end'] + vol['hose_O3b'],
                    tag='DESIGN/ESTIMATE (Mechanical inlet_e1m_v1 + hose_routing_trade_v2); filter split 50/50 core/annulus ASSUMED')
    # ---------------------------------------------------------------- 4. mobility
    gnc_d = GN['dispersed']
    def gpick(key, q):
        v = gnc_d.get(key, {})
        return float(v.get(q)) if isinstance(v, dict) and v.get(q) is not None else None
    g_desc = dict(p01=7.74, p50=8.18)                     # GNC descent mean f_z at the seat (coordinator relay; JSON dispersed block)
    g_up = dict(mean=0.39, min=1.47)                      # |f_z| coast-up mean and p01 minimum (toward the nose)
    mob = {}
    for name, D in (('3 mm drilling', 3.0), ('8 mm drillings / block', 8.0), ('7.75 mm riser / wall line', ID_wall), ('7.9 mm hose', 7.9),
                    ('14 mm filter bore', 14.0), ('2 mm annular gap (10/6 bore)', 2.0)):
        rowm = {}
        for lab, g in list(g_desc.items()) + [('coast_up_mean', g_up['mean']), ('coast_up_p01_min', g_up['min'])]:
            U, Eo = drift(D / 1e3, g, p)
            rowm[lab] = dict(Eo=Eo, U_m_s=U)
        mob[name] = rowm
    lam_c = math.sqrt(p['sigma'] / ((p['rho_l'] - p['rho_v']) * g_desc['p01'])) * 1e3
    # leg clearing times in the descent (p01 specific force)
    gd = g_desc['p01']
    U_riser = drift(ID_wall / 1e3, gd, p)[0]; U_8 = drift(8e-3, gd, p)[0]
    th = math.atan((z_coil_engine - z_coil_fixed) / (1e3 * coil['hose_length_m']))
    sgD = math.sqrt(gd * 7.9e-3 * (p['rho_l'] - p['rho_v']) / p['rho_l'])
    U_coil = dict(low=0.10 * sgD, high=(0.54 * math.cos(th) + 0.35 * math.sin(th)) * sgD)
    U_gap = dict(low=drift(2e-3, gd, p)[0], high=0.345 * math.sqrt(gd * 10e-3 * (p['rho_l'] - p['rho_v']) / p['rho_l']) * (1 + 0.1 * 0.6))
    L_bore = (crest - z_seat) / 1e3
    legs = {'coil 252 mm at %.1f deg' % math.degrees(th): [1e3 * coil['hose_length_m'] / 1e3 / U_coil['high'], 1e3 * coil['hose_length_m'] / 1e3 / U_coil['low']],
            'riser + fittings ~89 mm vertical': [(151.1 - z_coil_engine) / 1e3 / U_riser] * 2,
            'block + head + bonnet drillings ~54 mm': [(crest - 151.1) / 1e3 / U_8] * 2,
            'bore leg %.0f mm (2 mm gap)' % (1e3 * L_bore): [L_bore / U_gap['high'], L_bore / U_gap['low']],
            'wall line %.0f mm vertical' % (240.0 - z_coil_fixed): [(240.0 - z_coil_fixed) / 1e3 / U_riser] * 2}
    mesh = dict(pore_m=15e-6, bubble_point_Pa=4 * p['sigma'] / 15e-6,
                head_upper_trap_Pa=(p['rho_l'] - p['rho_v']) * gd * (crest - (st['z_filter_axis'] + 7.0)) / 1e3,
                head_lower_trap_full_Pa=(p['rho_l'] - p['rho_v']) * gd * ((st['z_filter_axis'] + 7.0) - z_coil_fixed) / 1e3,
                tag='ASSUMED fully wetted 15 um Dutch-twill mesh, pore ~ rating; bubble point 4 sigma / d')
    # ---------------------------------------------------------------- 5. vapour generated (window scaling with the FE bore shape)
    win = dict(mech=float(B['coast_s']), p50=gpick('window_s', 'p50'), p99=gpick('window_s', 'p99'), max=gpick('window_s', 'max'),
               min=gpick('window_s', 'min'))
    scale = {}
    for c, lab in (('LO', 'DC-A1dispp99_tg711_hi_SS316L_L2.5_v11pre36IN'), ('HI', 'DC-A1dispp99_tg711_hi_SS316L_L2.5_v11pre36ING10')):
        s = C['runs'][lab]['series']; t = np.array(s['t_s']) - s['t_s'][0]; q = np.array(s['Q_W'])
        k = np.polyfit(t[-5:], q[-5:], 1)
        def E_to(T, t=t, q=q, k=k):
            if T <= t[-1]:
                tt = np.linspace(0, T, 400); return float(_trap(np.interp(tt, t, q), tt))
            tt = np.linspace(t[-1], T, 200)
            return float(_trap(q, t) + _trap(np.polyval(k, tt), tt))
        E_m = E_to(win['mech'])
        scale[c] = {w: E_to(v) / E_m for w, v in win.items() if v is not None}
        scale[c]['q_end_over_mean'] = float(q[-1] / (_trap(q, t) / t[-1]))
        scale[c]['coast_up_share'] = E_to(6.4) / E_m
    sub_J = V_U * p['rho_l'] / 1e6 * p['cp_l'] * 0.05e6 / p['dPdT_sat_Pa_K']   # S1 crack 0.05 MPa mid -> subcooling credit (U liquid)
    # ---------------------------------------------------------------- 6-7. pocket and P_abort
    J = json.load(open(os.path.join(d2p4, 'start_latency_v2p4.json')))
    rws = J['part1_runs']['v']; lifts = J['ignition_lifts']
    pool = [r for r in rws if r['ramp'] == 2500.0 and r['F_cmd'] in (200.0, 500.0) and r['state'] == 'A1_relight'
            and r['frac'] == 0.125 and r.get('loop_K', 0.0) == 15.0]
    N = 200000; rng = np.random.default_rng(2024)
    h = lifts['A1_relight|0.125']['lift_m']; t_lift = SL.T_CMD + h / SL.V_PINTLE + 0.010
    idx = rng.integers(0, len(pool), N)
    tc = np.array([np.nan if q_['t_conf_s'] is None else q_['t_conf_s'] for q_ in pool])[idx]
    _ = rng.uniform(0.005, 0.020, N) + rng.uniform(0.02, 0.10, N) + rng.uniform(0.005, 0.030, N)   # stream parity
    ig = rng.uniform(0.05, 0.30, N)
    base = (t_lift + ig + tc); base = base[np.isfinite(base)]
    PA = json.load(open(os.path.join(d2p4, 'post_abort_pocket_v2p4.json')))
    check = dict(base_max_s=float(base.max()), post_abort_pocket_base_max_s=PA['E1_E2_liquid_s']['max'],
                 reproduces=bool(abs(float(base.max()) - PA['E1_E2_liquid_s']['max']) < 1e-9))
    def pab(Veff, W):
        return float(np.mean(base + PURGE * Veff > W))
    Ws = (0.65, 0.85, 1.05)
    allow = {f'W{W:.2f}': (W - float(base.max())) / PURGE for W in Ws}
    Ql_cm3_s = 37.1e-3 / p['rho_l'] * 1e6 * (35.0 / 37.1)       # A1-state flow at the 0.2039 mm lift (35.0 g/s, v2.8) as liquid volume
    res = {}
    for c in ('LO', 'HI'):
        for w in ('min', 'mech', 'p50', 'max'):
            if w not in scale[c]:
                continue
            QU = Q[c]['U'] * scale[c][w]; QR = Q[c]['route'] * scale[c][w]
            Vgen = QU * vpj
            Vgen_sub = max(0.0, QU - sub_J) * vpj
            # dead-end bore leg: refilled at the descent onset only if the crest still holds liquid then (no mesh barrier),
            # then loses its own evaporation in the descent; with the mesh barrier it is not refilled (bounding: plug 0)
            Q_L1 = seg[-1][f'Q_{c}_J'] * scale[c][w]
            share_desc = 1.0 - scale[c]['coast_up_share'] / scale[c][w]
            plug_refill = max(0.0, seg[-1]['V_cm3'] - Q_L1 * share_desc * lpj)
            out = {}
            for lab, plug in (('bore_leg_refilled', plug_refill), ('bore_leg_dry', 0.0)):
                V_vap_U = min(Vgen, V_U - plug)
                over = max(0.0, Vgen - (V_U - plug))
                wall_void = 0.0
                if over > 0:
                    rate = (Q[c]['U'] + Q[c]['route']) * scale[c]['q_end_over_mean'] / win['mech'] * vpj * 1e-6   # m3/s at the end
                    jv = rate / (A_wall * 1e-6); Ud = drift(ID_wall / 1e3, gd, p)[0]
                    wall_void = jv / (1.2 * jv + Ud) if jv > 0 else 0.0
                V_eff = V_vap_U + plug * PURGE ** -1 * (1.0 / Ql_cm3_s) if plug > 0 else V_vap_U
                # v2.4 correction (2026-10-13): the wall-line void of the overflow counts whenever the U overflows (LO as well;
                # the first run added it for HI only, so its LO V_eff was low by up to the void x 16.1 cm3; kept as evidence)
                V_eff_HIwall = V_eff + wall_void * (V_wall + V_mod)
                out[lab] = dict(plug_cm3=plug, vapour_in_U_cm3=V_vap_U, overflow_cm3=over, wall_line_void=wall_void,
                                V_eff_cm3=V_eff_HIwall,
                                P_abort={f'W{W:.2f}': pab(V_eff_HIwall, W) for W in Ws})
            res[f'{c}|{w}'] = dict(window_s=win[w], Q_U_J=QU, Q_route_J=QR, V_generated_in_U_cm3=Vgen, V_generated_with_S1_subcooling_cm3=Vgen_sub,
                                   U_fill_fraction=min(1.0, Vgen / V_U), Q_bore_leg_J=Q_L1, **out)
    # ---------------------------------------------------------------- 8. options
    # (a) prime bleed at the crest with the MV open (pintle seated): choked-vapour bleed, then liquid; residual = bore leg + boiling after the bleed
    Cd = 0.8; P0 = p['P_Pa']
    mdot_v_per_A = Cd * 0.667 * math.sqrt(p['rho_v'] * P0)
    mdot_l_per_A = 0.6 * math.sqrt(2 * p['rho_l'] * P0)
    t_purge = 0.30
    A_b = (V_U * 1e-6 * p['rho_v'] / t_purge) / mdot_v_per_A
    d_b = math.sqrt(4 * A_b / math.pi) * 1e3
    opt_a = {}
    for c in ('LO', 'HI'):
        rate_end = (Q[c]['U'] / win['mech']) * scale[c]['q_end_over_mean'] * vpj      # cm3/s generated in the U at the end
        for gap in (0.5, 1.0):
            resid = rate_end * gap + seg[-1]['V_cm3']                                   # bore leg not swept + boiling after the bleed
            opt_a[f'{c}|bleed_end_{gap:.1f}s_before_E0'] = dict(U_boil_rate_cm3_s=rate_end, residual_pocket_cm3=resid,
                                                                P_abort={f'W{W:.2f}': pab(resid, W) for W in Ws})
    opt_a['bleed'] = dict(orifice_d_mm_for_U_in_0p30s=d_b, vapour_g=V_U * p['rho_v'] / 1e3, liquid_g_if_closed_0p10s_after_liquid=mdot_l_per_A * A_b * 0.10 * 1e3,
                          tag='DERIVED estimate: choked vapour (ideal-gas coefficient, gamma 1.3, Cd 0.8 ASSUMED), liquid 0.6 sqrt(2 rho dP) (ASSUMED)',
                          location='crest (bonnet cross-drilling outer port, today the stand-only T4 / P_manifold port; a radial fitting there leaves the 8 deg sweep cone - Mechanical)',
                          does_not_sweep='the dead-end bore leg (4.51 cm3) between the crest and the seat')
    opt_d = dict(effect_on_U='none: the crest is %.0f mm above the U-bottom; an open MV adds no buoyant path out of the U and the seated pintle gives no flow' % (crest - z_coil_fixed),
                 effect_on_route='the wall line and module vent to the tank instead of through S1 (they already vent)',
                 pocket_change_cm3=0.0)
    inv = json.load(open(os.path.join(d2p4, 'hard_start_multivolume_v2p4.json')))['inventory_vs_W_v2p8_lift']['v']
    def inv_at(Tlab, W):
        r = inv[Tlab]; s0 = r['W0.25_g']; slope = (r['W0.65_g'] - r['W0.25_g']) / 0.40
        return s0 + slope * (W - 0.25)
    opt_b = dict(W_s=1.05, pocket_allowance_cm3=allow['W1.05'], planning_primed_s=0.16 + 1.05, planning_unprimed_s=0.56 + 0.16 + 1.05,
                 planning_v2p8_s=dict(primed=0.81, unprimed=1.37, fc_unprimed=1.41),
                 max_unignited_liquid_line_g={T: inv_at(T, 1.05) for T in inv}, max_unignited_liquid_line_g_W0p65={T: inv_at(T, 0.65) for T in inv},
                 flight_inventory_accepted_g=26.6,
                 note='liquid-line inventories by linear extension of inventory_vs_W_v2p8_lift (W 0.25-0.65 rows); credible and fuel-assisted hard-start peaks in hard_start_multivolume_v2p4 do not depend on the inventory (fast fraction 1.88 g)')
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/relight_vapour_order_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               inputs={k: dict(file=f, sha256_16=sha16(f)) for k, f in (('mech_budget', budget_f), ('mech_coast', coast_f), ('mech_inlet', inlet_f),
                                                                         ('mech_hose', hose_f), ('gnc_coast_accel', gnc_f))},
               properties=p, geometry=geometry, segment_flow_order=seg, heat_J=Q, window_scale=scale, window_s=win,
               mobility=dict(per_passage=mob, capillary_length_mm_descent=lam_c, coil_incline_deg=math.degrees(th), U_coil_m_s=U_coil,
                             U_gap_m_s=U_gap, leg_clear_time_s=legs, filter_mesh=mesh, g_desc_m_s2=g_desc, g_coast_up_abs_m_s2=g_up,
                             tag='LITERATURE forms as recalled (Wallis; White & Beardmore; Bendiksen 1984 inclined; Das et al. annulus) - TO-VERIFY'),
               subcooling_credit_J=sub_J, distribution_check=check, purge_s_per_cm3=PURGE, pocket_allowance_cm3=allow,
               liquid_plug_dead_time_s_per_cm3=1.0 / Ql_cm3_s, results=res, option_a=opt_a, option_d=opt_d, option_b=opt_b,
               tags=dict(heat='Mechanical FEA + ESTIMATE (isothermal LO = h 376 W/m2K; HI = Cooper nucleate boiling, unlimited far field)',
                         geometry='Mechanical DESIGN/ESTIMATE', model='DERIVED + SIM (K15 pool)', acceleration='GNC SIM'))
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    brief = dict(U=geometry, heat=Q, results={k: {kk: (vv if not isinstance(vv, dict) else {a: b for a, b in vv.items()})
                                                  for kk, vv in v.items()} for k, v in res.items()}, allow=allow, check=check,
                 option_a=opt_a, option_b={k: v for k, v in opt_b.items() if k != 'note'}, legs=legs, mesh=mesh, mob=mob, props=p)
    print(json.dumps(brief, indent=1, default=float))


if __name__ == '__main__':
    main(*sys.argv[1:8])
