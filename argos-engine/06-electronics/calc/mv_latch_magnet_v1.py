#!/usr/bin/env python3
"""MV-P holding magnet and coil sizing (Electronics, 2026-10-13, v1).

Lead request 2026-10-13 (MV concept change to Mechanical's MV-P balanced poppet): "Size the latch magnet and coil for 30.5 N within
your power budget." The over-centre latch (10:1) holds the poppet open against the spring (107 N open) plus the closing pressure bias
(45.7 N at 6.5 MPa); Mechanical's 30.5 N already includes the 2x latch factor of the Electronics MV spec v1.

Concept (DESIGN): DC pot-core holding magnet (inner pole + outer ring of equal area, coil in the annular window, flat armature on the
latch lever). The armature is brought into contact by the opener cam (no pull-in requirement): the magnet only HOLDS at a closed
armature, so a small coil suffices. A non-magnetic layer on the pole faces (0.05 mm, DESIGN: hard-chrome or austenitic foil) fixes the
working gap and prevents remanent sticking (release must not depend on residual magnetism).

Model (analytic magnetic circuit, every input tagged; a SIZING, not a validation - B-MV-1 measures the pull-off force, the drop-out
voltage and the release time):
  - reluctances: two gaps in series (pole faces), steel paths (inner pole, outer ring, back plate and armature as radial discs) with
    a linear relative permeability mu_r [ASSUMED 500, conservative for annealed low-carbon steel / pure iron at <= 1.3 T];
  - leakage across the coil window in parallel with the gap path: P_leak = mu0 * 2 pi r_m h / (2 w) [DERIVED, the 1/2 factor gives
    more leakage than the 1/3 energy-equivalent of a distributed MMF -> conservative];
  - force: Maxwell stress on both pole faces, uniform field, no fringing (conservative): F = Phi_g^2 / (2 mu0) (1/A1 + 1/A2);
  - coil: round enamelled copper, layer fill 0.55 [ASSUMED] in the window less a 0.5 mm bobbin wall each side [DESIGN], overall
    wire diameter 1.10 x bare [ASSUMED grade 2]; rho_Cu 1.724e-8 ohm m at 20 C, alpha 0.00393 /K [LITERATURE];
  - drive: DMN6075S low side [DATASHEET DS37023 Rev6-2: RDS(on) <= 120 mOhm at 4.5 V] from the ARM bus (2S); release through
    SS14 + SMAJ24A [DATASHEET Littelfuse SMAJ series: V_BR 26.7-29.5 V; slowest release at 26.7 V];
  - release time: coil current decay into the clamp to the current at which F falls to the true load (30.5 / 2 = 15.25 N), plus the
    eddy-current lag of the solid steel (single equivalent shorted turn per solid cylinder, 8 pi / (sigma l), x3 for the other solid
    parts [ASSUMED]); sigma 1.0e7 S/m [LITERATURE, pure iron = slowest].

Inputs read: Mechanical 03-cad/calcs/mv_actuator_v1.json (sha256 checked against the prefix the lead quoted), the Electronics power
budget limits below. Outputs: ../results/mv_latch_magnet_v1.json / .txt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, '..', 'results')
MU0 = 4e-7 * math.pi

# ---------------------------------------------------------------- inputs (tagged)
MV_JSON_CANDIDATES = ('03-cad/calcs/mv_actuator_v1.json', '03-cad/src/calcs/mv_actuator_v1.json')
MV_SHA_PREFIX = 'a2d8cdd3ef4ca6c0'            # [LEAD 2026-10-13] quoted id of Mechanical's MV actuator data
F_MODEL_FACTOR = 1.0                         # [DESIGN] no extra factor on MECH's 30.5 N (it already holds the 2x latch factor); the
                                             #   model uncertainty is carried by the worst-case inputs (mu_r 500, worst gap, 100 C, 6.0 V)
                                             #   and shown by the sensitivity cases; B-MV-1 measures the pull-off force
V_MIN_BUS = 6.0                              # [DESIGN] lowest ARM-bus voltage the latch must hold at (battery-low flag 6.6 V
                                             #   under load, cfg::kBattLow_V; v1 budget DERIVED 6.11 V at 3.5 V/cell) less margin
V_MAX_BUS = 8.4                              # [DATASHEET 2S LiPo full charge 4.2 V/cell]
R_FET = 0.120                                # [DATASHEET DMN6075S RDS(on) max at VGS 4.5 V]
R_HARNESS = 0.10                             # [ASSUMED] connector J506 + 2 x 0.5 m AWG24 (2 x 0.042 ohm) + crimps
T_COIL_HOT_C = 100.0                         # [ASSUMED bound] bay <= ~45 C at ARM (LEAD launch constraint) + engine-bay heating
                                             #   + self-heating; 100 C coil (class 180 wire)
T_COIL_COLD_C = -10.0                        # [DATASHEET SB-2292SG lower rating, used as the cold bound of the bay]
G_SHIM = 0.05e-3                             # [DESIGN] non-magnetic layer per pole face (sets the gap, prevents sticking)
G_ROUGH_NOM, G_ROUGH_WORST = 0.01e-3, 0.02e-3   # [ASSUMED] ground faces, flatness, wear, dirt per face, with a SELF-ALIGNING armature
                                                #   (DESIGN requirement: armature floats on the lever so both faces seat; a rigid tilt
                                                #   would add gap - sensitivity case 0.10 mm/face below)
MU_R = 500.0                                 # [ASSUMED conservative] low-carbon steel / pure iron, B <= 1.3 T
B_STEEL_MAX = 1.3                            # [DESIGN] limit for the linear model (saturation ~2.0 T LITERATURE)
SIGMA_FE = 1.0e7                             # [LITERATURE] pure iron conductivity (low-carbon steel ~7e6)
EDDY_OTHER_FACTOR = 3.0                      # [ASSUMED] ring, back plate and armature add 3x the inner-pole eddy time constant
ROBUST = 1.25                                # [DESIGN] at mu_r 250 (half) OR at 0.10 mm/face (each alone, 6.0 V, 100 C) the force stays
                                             #   >= 1.25 x the true load (the lightest design at exactly 30.5 N falls to 1.0x)
FILL = 0.55                                  # [ASSUMED] layer-wound round wire
BOBBIN = 0.5e-3                              # [DESIGN] bobbin wall each side of the window
WIRE_BUILD = 1.10                            # [ASSUMED] overall / bare diameter (grade 2)
RHO_CU20, ALPHA_CU = 1.724e-8, 0.00393       # [LITERATURE]
RHO_FE, RHO_CU_D = 7870.0, 8960.0            # [LITERATURE] densities [kg/m3]
C_FE, C_CU = 450.0, 385.0                    # [LITERATURE] specific heats [J/kg/K]
V_CLAMP_MIN = 26.7 + 0.4                     # [DATASHEET SMAJ24A V_BR min + SS14 forward ~0.4 V]
P_MAX_BUDGET = 4.0                           # [Electronics electronics.json v1 latch_coil power_W_max, ASSUMED requirement]
P_TARGET = 4.0                               # [DESIGN] = the latch budget (LEAD: 'within your power budget'); 2.0 W needs a regulated
                                             #   drive or a heavier magnet (options table)
T_ON_MAX_S = 120.0                           # [ASSUMED] longest continuous latch-on per sequence (pad PREPRESS + 60 s flight + margin)
T_RELEASE_REQ = 0.010                        # [Electronics MV spec v1 -> B-MV-1] latch release <= 10 ms


def awg_d(awg: int) -> float:
    return 0.127e-3 * 92.0 ** ((36 - awg) / 39.0)


def rho_cu(T_C: float) -> float:
    return RHO_CU20 * (1.0 + ALPHA_CU * (T_C - 20.0))


def load_mv(engine_root: str):
    for rel in MV_JSON_CANDIDATES:
        p = os.path.join(engine_root, rel)
        if os.path.exists(p):
            raw = open(p, 'rb').read()
            sha = hashlib.sha256(raw).hexdigest()
            return p, sha, json.loads(raw)
    return None, None, None


def design(r1, w, h, awg, g_face, T_C, V_bus, mu_r=MU_R):
    """Magnetic circuit of one candidate. Returns a dict with geometry, coil, flux and force."""
    A1 = math.pi * r1 ** 2
    r2 = r1 + w
    r3 = math.sqrt(r2 ** 2 + A1 / math.pi)          # outer ring area = inner pole area (balanced faces)
    A2 = math.pi * (r3 ** 2 - r2 ** 2)
    t_b = max(1.5e-3, 0.55 * r1)                     # [DESIGN] back plate / armature thickness (radial flux at r1 <= 0.91 B1)
    t_a = t_b
    mu = mu_r * MU0
    l_pole = h + 0.5 * (t_b + t_a)
    R_inner = l_pole / (mu * A1)
    R_outer = l_pole / (mu * A2)
    rm_ring = 0.5 * (r2 + r3)
    R_back = math.log(rm_ring / (0.5 * r1)) / (2 * math.pi * mu * t_b)
    R_arm = math.log(rm_ring / (0.5 * r1)) / (2 * math.pi * mu * t_a)
    R_steel = R_inner + R_outer + R_back + R_arm
    R_gap = g_face / (MU0 * A1) + g_face / (MU0 * A2)
    r_m = r1 + 0.5 * w
    P_leak = MU0 * 2 * math.pi * r_m * h / (2.0 * w)
    R_leak = 1.0 / P_leak
    R_par = R_gap * R_leak / (R_gap + R_leak)
    R_tot = R_steel + R_par
    # coil
    wc, hc = w - 2 * BOBBIN, h - 2 * BOBBIN
    if wc <= 0 or hc <= 0:
        return None
    d = awg_d(awg)
    d_o = WIRE_BUILD * d
    N = int(FILL * wc * hc / (d_o ** 2))             # square-packing count x fill
    if N < 10:
        return None
    l_turn = 2 * math.pi * r_m
    R_coil = rho_cu(T_C) * N * l_turn / (math.pi * d ** 2 / 4)
    I = V_bus / (R_coil + R_FET + R_HARNESS)
    NI = N * I
    Phi = NI / R_tot
    Phi_g = Phi * R_leak / (R_gap + R_leak)
    F = Phi_g ** 2 / (2 * MU0) * (1.0 / A1 + 1.0 / A2)
    B1 = Phi / A1
    B_back = Phi / (2 * math.pi * r1 * t_b)
    L = N ** 2 / R_tot
    m_fe = RHO_FE * (A1 * h + A2 * h + math.pi * r3 ** 2 * (t_b + t_a))
    m_cu = RHO_CU_D * N * l_turn * math.pi * d ** 2 / 4
    return dict(r1=r1, w=w, h=h, r3=r3, t_b=t_b, A1=A1, A2=A2, awg=awg, d=d, N=N, R_coil=R_coil, I=I, NI=NI, Phi=Phi,
                Phi_g=Phi_g, F=F, B1=B1, B_back=B_back, L=L, R_tot=R_tot, R_gap=R_gap, R_steel=R_steel, R_leak=R_leak,
                m_fe=m_fe, m_cu=m_cu, P=I ** 2 * R_coil, P_bus=I * V_bus, l_pole=l_pole)


def release_time(dc, F_true):
    """Coil decay into the clamp to the current where F = F_true, plus the eddy lag (single shorted turns, ASSUMED factor)."""
    I0, R, L = dc['I'], dc['R_coil'] + R_FET + R_HARNESS, dc['L']
    I_rel = I0 * math.sqrt(F_true / dc['F'])         # linear circuit: F ~ I^2
    tau = L / R
    Vc = V_CLAMP_MIN
    t_coil = tau * math.log((I0 + Vc / R) / (I_rel + Vc / R))
    R_eq_inner = 8 * math.pi / (SIGMA_FE * dc['l_pole'])
    tau_e = (1.0 / dc['R_tot']) / R_eq_inner * EDDY_OTHER_FACTOR
    # first-order lag of the flux behind the coil MMF: the flux reaches the release level about tau_e after the MMF does
    return dict(t_coil_s=t_coil, tau_eddy_s=tau_e, t_release_s=t_coil + tau_e, I_release_A=I_rel, tau_LR_s=tau,
                V_drain_peak_V=V_MAX_BUS + Vc + 29.5 - 26.7)


def dropout_voltage(dc_fn, F_true):
    lo, hi = 0.1, V_MAX_BUS
    for _ in range(60):
        m = 0.5 * (lo + hi)
        if dc_fn(m)['F'] >= F_true: hi = m
        else: lo = m
    return hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine-root', default='/mnt/project-files/engine')
    ap.add_argument('--mech-root', default='', help='fallback root holding 03-cad/src/calcs/mv_actuator_v1.json (Mechanical workdir)')
    a = ap.parse_args()
    path, sha, mv = load_mv(a.engine_root)
    if mv is None and a.mech_root:
        path, sha, mv = load_mv(a.mech_root)
    if mv is None:
        raise SystemExit('mv_actuator_v1.json not found (hub 03-cad/calcs or --mech-root)')
    if not sha.startswith(MV_SHA_PREFIX):
        raise SystemExit('mv_actuator_v1.json sha256 %s does not match the quoted %s: re-read the lead message' % (sha[:16], MV_SHA_PREFIX))
    B = mv['B_balanced_poppet_MVP']
    F_req = float(B['latch_hold_force_N_incl_2x'])                 # [MECH] incl. 2x
    lever = float(B['spec']['latch_lever_ratio']['v'])
    F_true = (float(B['spring_open_N']) + float(B['F_bias_closed_N'])) / lever   # load without the 2x factor
    F_need_model = F_REQ_MODEL = F_req * F_MODEL_FACTOR

    g_nom, g_worst = G_SHIM + G_ROUGH_NOM, G_SHIM + G_ROUGH_WORST
    V_min_coil = V_MIN_BUS
    cands = []
    for r1 in [x * 0.5e-3 for x in range(4, 15)]:
        for w in [x * 0.5e-3 for x in range(4, 17)]:
            for h in [x * 1e-3 for x in range(4, 21)]:
                for awg in range(24, 41):
                    worst = design(r1, w, h, awg, g_worst, T_COIL_HOT_C, V_min_coil)
                    if worst is None:
                        continue
                    hot_max = design(r1, w, h, awg, g_nom, T_COIL_COLD_C, V_MAX_BUS)
                    ok = (worst['F'] >= F_need_model and hot_max['P_bus'] <= P_TARGET and worst['B1'] <= B_STEEL_MAX and
                          worst['B_back'] <= B_STEEL_MAX)
                    if ok:   # robustness: each sensitivity corner alone keeps ROBUST x the true load
                        f_mu = design(r1, w, h, awg, g_worst, T_COIL_HOT_C, V_min_coil, mu_r=MU_R / 2)['F']
                        f_gap = design(r1, w, h, awg, 0.10e-3, T_COIL_HOT_C, V_min_coil)['F']
                        ok = min(f_mu, f_gap) >= ROBUST * F_true
                    if ok:
                        cands.append((worst['m_fe'] + worst['m_cu'], worst, hot_max))
    cands.sort(key=lambda c: c[0])
    if not cands:
        raise SystemExit('no candidate meets the requirements')
    m, worst, cold = cands[0]
    r1, w, h, awg = worst['r1'], worst['w'], worst['h'], worst['awg']
    nom = design(r1, w, h, awg, g_nom, 20.0, 7.4)
    rel_nom = release_time(nom, F_true)
    rel_cold = release_time(cold, F_true)            # highest current -> longest decay
    vdo_hot = dropout_voltage(lambda V: design(r1, w, h, awg, g_worst, T_COIL_HOT_C, V), F_true)
    vdo_hot_2x = dropout_voltage(lambda V: design(r1, w, h, awg, g_worst, T_COIL_HOT_C, V), F_req)
    # adiabatic self-heating over the longest latch-on period at the highest power
    dT = cold['P'] * T_ON_MAX_S / (cold['m_fe'] * C_FE + cold['m_cu'] * C_CU)
    E_flight_J = nom['P_bus'] * 60.0
    # sensitivity: mu_r 250 (half), gap 0.15 mm
    sens = {
        'mu_r_250_worst_gap_hot_6V_F_N': design(r1, w, h, awg, g_worst, T_COIL_HOT_C, V_min_coil, mu_r=MU_R / 2)['F'],
        'gap_0p10mm_hot_6V_F_N': design(r1, w, h, awg, 0.10e-3, T_COIL_HOT_C, V_min_coil)['F'],
        'gap_0p15mm_hot_6V_F_N': design(r1, w, h, awg, 0.15e-3, T_COIL_HOT_C, V_min_coil)['F'],
        'gap_0p20mm_hot_6V_F_N': design(r1, w, h, awg, 0.20e-3, T_COIL_HOT_C, V_min_coil)['F'],
    }
    top = [dict(mass_g=round(1e3 * c[0], 2), r1_mm=round(c[1]['r1'] * 1e3, 2), w_mm=round(c[1]['w'] * 1e3, 2), h_mm=round(c[1]['h'] * 1e3, 2),
                awg=c[1]['awg'], N=c[1]['N'], F_worst_N=round(c[1]['F'], 1), P_max_W=round(c[2]['P'], 2)) for c in cands[:8]]

    # drive options (trade evidence): lightest magnet per drive and bus-power limit, at the worst gap and at 0.10 mm/face
    def search(mode, gw, P_lim):
        best = None
        for r1_ in [x * 0.5e-3 for x in range(4, 15)]:
            for w_ in [x * 0.5e-3 for x in range(4, 17)]:
                for h_ in [x * 1e-3 for x in range(4, 21)]:
                    for awg_ in range(24, 41):
                        d = design(r1_, w_, h_, awg_, gw, T_COIL_HOT_C, V_MIN_BUS)
                        if d is None:
                            continue
                        R_hot = d['R_coil']
                        R_cold = R_hot * (1 + ALPHA_CU * (T_COIL_COLD_C - 20)) / (1 + ALPHA_CU * (T_COIL_HOT_C - 20))
                        I_req = d['I'] * math.sqrt(F_need_model / d['F'])
                        if mode == 'direct_bus':
                            if d['F'] < F_need_model: continue
                            I_ = d['I']; P_bus = V_MAX_BUS ** 2 / (R_cold + R_FET + R_HARNESS)
                        elif mode == 'buck_5V':      # [ASSUMED] 5.0 V +/- 2 %, efficiency 0.85
                            I_ = 4.9 / (R_hot + R_FET + R_HARNESS)
                            if I_ < I_req: continue
                            P_bus = (5.1 / (R_cold + R_FET + R_HARNESS)) ** 2 * (R_cold + R_FET + R_HARNESS) / 0.85
                        else:                        # linear constant current, 0.15 V sense, 0.3 V headroom, <= 1 W pass element
                            I_ = I_req; Rs = 0.15 / I_
                            if I_ * (R_hot + R_HARNESS + R_FET + Rs) + 0.3 > V_MIN_BUS: continue
                            P_bus = V_MAX_BUS * I_
                            if (V_MAX_BUS - I_ * (R_cold + R_HARNESS + R_FET + Rs)) * I_ > 1.0: continue
                        if P_bus > P_lim or d['B1'] * I_ / d['I'] > B_STEEL_MAX:
                            continue
                        mass = d['m_fe'] + d['m_cu']
                        if best is None or mass < best[0]:
                            best = (mass, d, I_, P_bus)
        if best is None:
            return {'mode': mode, 'gap_mm': round(gw * 1e3, 3), 'P_bus_limit_W': P_lim, 'result': 'none in the search range'}
        mass, d, I_, P_bus = best
        return {'mode': mode, 'gap_mm': round(gw * 1e3, 3), 'P_bus_limit_W': P_lim, 'mass_g': round(mass * 1e3, 1),
                'outer_d_mm': round(2e3 * d['r3'], 1), 'pole_d_mm': round(2e3 * d['r1'], 1), 'window_mm': round(d['w'] * 1e3, 1),
                'coil_h_mm': round(d['h'] * 1e3, 1), 'awg': d['awg'], 'turns': d['N'], 'I_hold_A': round(I_, 3), 'P_bus_max_W': round(P_bus, 2)}
    options = [search(md, gw_, pl) for gw_ in (g_worst, 0.10e-3) for md in ('direct_bus', 'buck_5V', 'cc_linear') for pl in (2.0, 4.0)]

    def mm(x): return round(x * 1e3, 3)
    res = {
        'id': 'mv_latch_magnet', 'version': 'v1', 'date': '2026-10-13', 'owner': 'electronics',
        'script': '06-electronics/calc/mv_latch_magnet_v1.py',
        'status': 'SIZING (analytic magnetic circuit). Not a validation: B-MV-1 measures pull-off force, drop-out voltage and release time',
        'inputs': {
            'mv_actuator_json': {'path': path, 'sha256': sha, 'tag': 'MECH mv_actuator_v1 (LEAD 2026-10-13 quoted a2d8cdd3ef4ca6c0)'},
            'F_hold_req_incl_2x_N': {'v': F_req, 'tag': 'MECH latch_hold_force_N_incl_2x'},
            'F_true_load_N': {'v': round(F_true, 2), 'tag': 'DERIVED (spring_open_N + F_bias_closed_N) / latch_lever_ratio (MECH)'},
            'F_model_factor': {'v': F_MODEL_FACTOR, 'tag': 'DESIGN'},
            'V_min_bus_V': {'v': V_MIN_BUS, 'tag': 'DESIGN'}, 'V_max_bus_V': {'v': V_MAX_BUS, 'tag': 'DATASHEET 2S'},
            'R_fet_ohm': {'v': R_FET, 'tag': 'DATASHEET DMN6075S'}, 'R_harness_ohm': {'v': R_HARNESS, 'tag': 'ASSUMED'},
            'T_coil_hot_C': {'v': T_COIL_HOT_C, 'tag': 'ASSUMED bound'}, 'T_coil_cold_C': {'v': T_COIL_COLD_C, 'tag': 'DATASHEET SB-2292SG lower rating'},
            'gap_per_face_nom_mm': {'v': mm(g_nom), 'tag': 'DESIGN shim 0.05 + ASSUMED 0.01'},
            'gap_per_face_worst_mm': {'v': mm(g_worst), 'tag': 'DESIGN shim 0.05 + ASSUMED 0.05'},
            'mu_r': {'v': MU_R, 'tag': 'ASSUMED'}, 'B_steel_max_T': {'v': B_STEEL_MAX, 'tag': 'DESIGN'},
            'sigma_Fe_S_m': {'v': SIGMA_FE, 'tag': 'LITERATURE'}, 'fill': {'v': FILL, 'tag': 'ASSUMED'},
            'V_clamp_min_V': {'v': V_CLAMP_MIN, 'tag': 'DATASHEET SMAJ24A V_BR min + SS14'},
            'P_budget_W': {'v': P_MAX_BUDGET, 'tag': 'electronics.json v1 latch_coil power_W_max (ASSUMED requirement)'},
            'P_target_W': {'v': P_TARGET, 'tag': 'DESIGN'},
        },
        'selected': {
            'tag': 'DERIVED (lightest candidate meeting F >= 30.5 N at 6.0 V / 100 C / 0.07 mm per face / mu_r 500, >= 1.25 x the true load at mu_r 250 or at 0.10 mm per face, bus power <= 4.0 W at 8.4 V / -10 C, steel <= 1.3 T; direct ARM-bus drive)',
            'geometry_mm': {'inner_pole_d': mm(2 * r1), 'window_w': mm(w), 'coil_h': mm(h), 'outer_d': mm(2 * worst['r3']),
                            'back_plate_t': mm(worst['t_b']), 'armature_t': mm(worst['t_b']),
                            'pole_area_mm2': round(worst['A1'] * 1e6, 1)},
            'coil': {'awg': awg, 'bare_d_mm': mm(worst['d']), 'turns': worst['N'],
                     'R_20C_ohm': round(nom['R_coil'], 2), 'R_100C_ohm': round(worst['R_coil'], 2), 'R_m10C_ohm': round(cold['R_coil'], 2)},
            'mass_g': {'steel': round(worst['m_fe'] * 1e3, 1), 'copper': round(worst['m_cu'] * 1e3, 2),
                       'tag': 'DERIVED, excl. bobbin, leads, housing'},
            'worst_hold': {'condition': '6.0 V bus, coil 100 C, gap 0.07 mm/face, mu_r 500',
                           'I_A': round(worst['I'], 3), 'NI_At': round(worst['NI'], 1), 'B_pole_T': round(worst['B1'], 3),
                           'F_N': round(worst['F'], 1), 'margin_vs_30p5N': round(worst['F'] / F_req, 2),
                           'margin_vs_true_load': round(worst['F'] / F_true, 2)},
            'nominal': {'condition': '7.4 V, 20 C, gap 0.06 mm/face', 'I_A': round(nom['I'], 3), 'F_N': round(nom['F'], 1),
                        'P_coil_W': round(nom['P'], 3), 'P_bus_W': round(nom['P_bus'], 3), 'L_H': round(nom['L'], 4),
                        'B_pole_T': round(nom['B1'], 3)},
            'max_power': {'condition': '8.4 V, -10 C, gap 0.06 mm/face', 'I_A': round(cold['I'], 3), 'P_coil_W': round(cold['P'], 3),
                          'P_bus_W': round(cold['P_bus'], 3), 'B_pole_T_linear_model': round(cold['B1'], 3),
                          'within_budget_4W': cold['P_bus'] <= P_MAX_BUDGET,
                          'note': 'B above ~1.3 T means the linear model overestimates the force here (saturation): irrelevant, the '
                                  'worst hold case sets the design'},
            'dropout_V': {'hot_worst_gap_true_load': round(vdo_hot, 2), 'hot_worst_gap_30p5N': round(vdo_hot_2x, 2),
                          'tag': 'DERIVED: bus voltage at which the force falls to the load (releases below it)'},
            'release': {'nominal_7V4': {k: (round(v, 5) if isinstance(v, float) else v) for k, v in rel_nom.items()},
                        'cold_8V4': {k: (round(v, 5) if isinstance(v, float) else v) for k, v in rel_cold.items()},
                        'req_s': T_RELEASE_REQ, 'meets_req': rel_cold['t_release_s'] <= T_RELEASE_REQ,
                        'tag': 'DERIVED estimate (clamp decay + ASSUMED eddy factor); B-MV-1 measures it'},
            'self_heating_K': {'v': round(dT, 2), 'tag': 'DERIVED adiabatic, %.0f s at the 8.4 V / -10 C power' % T_ON_MAX_S},
            'energy_per_60s_burn_J': {'v': round(E_flight_J, 1), 'tag': 'DERIVED at 7.4 V (flight-day budget 13 Wh usable: negligible)'},
            'sensitivity_F_N': {k: round(v, 1) for k, v in sens.items()},
        },
        'candidates_lightest': top,
        'drive_options': {'v': options, 'tag': 'DERIVED trade (same magnetic model): a regulated coil supply removes the (8.4/6.0)^2 '
                                                 'bus factor; baseline keeps the direct ARM-bus drive (existing MVL channel, no new parts)'},
        'driver': {'switch': 'DMN6075S low side (existing solenoid_channel, fast release SS14 + SMAJ24A), ARM bus, AND /FAULT (LTC4365) and the '
                             'HAL dynamic gate (v2.7)', 'peak_drain_V': round(rel_cold['V_drain_peak_V'], 1),
                   'tag': 'DATASHEET DMN6075S 60 V / 2.0 A'},
        'notes': [
            'The armature is pushed onto the poles by the cam (over-centre lever): no pull-in force is required, only holding at a closed armature.',
            'Self-aligning armature (floats on the latch lever) is part of the design: the 0.07 mm/face worst gap assumes both faces seat.',
            'Non-magnetic layer 0.05 mm per face is part of the design: it fixes the working gap and removes remanent sticking (release '
            'must never rely on demagnetisation). Without it the force rises but release becomes unpredictable.',
            'COTS alternative: a DC holding electromagnet of the ~22 mm class with a 6 V coil can replace the custom pot core if its '
            'datasheet gives the force at a 0.07 mm gap: requirement F >= 30.5 N at 6.0 V and 100 C coil, bus power <= 4.0 W at 8.4 V. TO-QUOTE.',
            'Vibration: the 2x factor in the 30.5 N covers the armature/lever inertial load only if Mechanical confirms the lever mass '
            'and the flight acceleration spectrum (TO-VERIFY).',
        ],
        'open': ['mu_r and the gap allowance are ASSUMED: B-MV-1 pull-off force vs bus voltage at 20 C and hot (oven 100 C coil)',
                 'release time: B-MV-1 latch-drop to CLOSED switch with the SMAJ24A clamp (<= 10 ms latch release required)',
                 'steel grade and annealing: Mechanical drawing (pure iron or 1010, stress-relief anneal after machining)'],
    }
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, 'mv_latch_magnet_v1.json'), 'w') as f:
        json.dump(res, f, indent=1)
    s = res['selected']
    lines = [
        'MV-P holding magnet sizing v1 (2026-10-13)  - SIZING, not validation',
        'input %s sha256 %s' % (path, sha[:16]),
        'requirement %.1f N (MECH incl. 2x), true load %.2f N, model factor %.2f -> design %.1f N at 6.0 V, 100 C, %.2f mm/face, mu_r %.0f; '
        'robust >= %.2f x true load at mu_r %.0f or 0.10 mm/face' % (F_req, F_true, F_MODEL_FACTOR, F_need_model, 1e3 * g_worst, MU_R, ROBUST, MU_R / 2),
        'selected: inner pole d %.1f mm, window %.1f mm, coil h %.1f mm, outer d %.2f mm, plates %.2f mm; AWG %d, %d turns' %
        (2e3 * r1, 1e3 * w, 1e3 * h, 2e3 * worst['r3'], 1e3 * worst['t_b'], awg, worst['N']),
        'R coil 20 C %.2f ohm, 100 C %.2f ohm; mass steel %.1f g + copper %.2f g' % (nom['R_coil'], worst['R_coil'], 1e3 * worst['m_fe'], 1e3 * worst['m_cu']),
        'worst hold: I %.3f A, NI %.1f At, B %.3f T, F %.1f N (x%.2f of 30.5 N, x%.2f of the true load)' %
        (worst['I'], worst['NI'], worst['B1'], worst['F'], worst['F'] / F_req, worst['F'] / F_true),
        'nominal 7.4 V 20 C: I %.3f A, P coil %.3f W, F %.1f N, L %.4f H' % (nom['I'], nom['P'], nom['F'], nom['L']),
        'max power 8.4 V -10 C: I %.3f A, P coil %.3f W (bus %.3f W; budget 4.0 W)' % (cold['I'], cold['P'], cold['P_bus']),
        'drop-out (hot, worst gap): true load %.2f V, 30.5 N %.2f V' % (vdo_hot, vdo_hot_2x),
        'release (8.4 V cold): coil decay %.2f ms + eddy %.2f ms = %.2f ms (req <= 10 ms); 7.4 V: %.2f ms' %
        (1e3 * rel_cold['t_coil_s'], 1e3 * rel_cold['tau_eddy_s'], 1e3 * rel_cold['t_release_s'], 1e3 * rel_nom['t_release_s']),
        'self-heating %.2f K over %.0f s; energy per 60 s burn %.1f J' % (dT, T_ON_MAX_S, E_flight_J),
        'sensitivity (6.0 V, 100 C): mu_r 250 -> %.1f N; gap 0.10 mm -> %.1f N; gap 0.15 mm -> %.1f N; gap 0.20 mm -> %.1f N (true load %.2f N)' %
        (sens['mu_r_250_worst_gap_hot_6V_F_N'], sens['gap_0p10mm_hot_6V_F_N'], sens['gap_0p15mm_hot_6V_F_N'], sens['gap_0p20mm_hot_6V_F_N'], F_true),
        'drive options: ' + '; '.join('%s gap %.2f P<=%.0f W: %s' % (o['mode'], o['gap_mm'], o['P_bus_limit_W'], ('%.1f g OD %.1f mm' % (o['mass_g'], o['outer_d_mm'])) if 'mass_g' in o else 'none') for o in options),
        'lightest candidates: ' + '; '.join('%s g d%.1f/w%.1f/h%.1f AWG%d F%.1f P%.2f' % (c['mass_g'], 2 * c['r1_mm'], c['w_mm'], c['h_mm'], c['awg'], c['F_worst_N'], c['P_max_W']) for c in top[:5]),
    ]
    with open(os.path.join(RES, 'mv_latch_magnet_v1.txt'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
