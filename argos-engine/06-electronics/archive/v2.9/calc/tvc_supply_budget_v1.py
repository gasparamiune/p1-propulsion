"""TVC servo supply budget and the degraded-supply fault mode FM-PWR-01. ARGOS H1, 06-electronics.

v1 2026-10-12. Lead 2026-10-12, accepting the ENG-07 v2 slew proposal (n 4.8, 2S direct, >= 7.6 V at the servo, ARM permit
8.1 V): "keep two things visible as open items in electronics.json: the pack IR (<= 15 mOhm) and servo branch (<= 20 mOhm)
are ASSUMED - list them as measurements for the bench test plan; the degraded-supply case gives 97 deg/s at 6.6 V - make it
a documented fault mode, with the ECU behaviour defined (for example, the ARM inhibit level)."

What this script does (every input carries a tag; nothing is taken from another team's file except mechanical.json, read):
 A. Resistance chains from the battery to the TVC servo plug, element by element, for
      * the design basis the lead accepted (SIL v2.2: source 15 mOhm, branch 20 mOhm per servo, no shared path),
      * the v2.2 schematic as drawn (hardware/kicad_gen/ecu_design.py: F101, shunt, F401 15 A, one AOD4185, Micro-Fit,
        AWG20 extension, servo JR plug kept through an adapter lead),
      * the v2.3 proposal (two AOD4185 in parallel, F401 deleted, JR plug cut off and Micro-Fit crimped on the servo lead,
        AWG18 extension, AWG12 battery leads),
    each with "typ" and "max" columns. Shared elements (the TVC switch path) carry both servo currents.
 B. Servo plug voltage for two design loads:
      HOLD = both TVC servos at stall (sets the holding moment, the thin margin: 15.9 vs GNC p99 15.6 N m);
             I_stall(V) linear through the DATASHEET points 7.5 A @ 6.0 V and 9.2 A @ 7.4 V (fixed point solved);
      SLEW = both servos on the loaded operating point of the worst ENG-07 slew (I = I_run + (I_stall - I_run) T/Ts).
    The servo data (torque, speed, stall current) are assumed to be specified at the servo plug with the stock 300 mm lead
    (ASSUMED: vendor test conditions are not published), so the servo's own lead is not counted again.
 C. Plug voltage -> n 4.8 holding moment and worst loaded slew with the same models as calc/tvc_slew_check_v1.py.
 D. ECU constants for the fault mode (firmware/src/core/config.h) and bench pass criteria.
Usage: python3 tvc_supply_budget_v1.py [--engine-root DIR]
Outputs: ../results/tvc_supply_budget_v1.json and .txt
"""
import argparse
import datetime
import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parts_db as PDB  # noqa: E402
import tvc_slew_check_v1 as SC  # noqa: E402

D2R = math.pi / 180.0
R_H_N48 = 10.0e-3          # LEAD 2026-10-12 provisional: n 4.8 (horn 10 mm on r_e 48 mm), Mechanical owns the geometry
V_DESIGN = 7.6             # LEAD 2026-10-12: >= 7.6 V at the servo under peak load
V_ARM = 8.1                # LEAD 2026-10-12: ARM permit (resting pack voltage at the ECU)
V_BATT_LOW = 6.6           # DESIGN (config.h kBattLow_V, 3.3 V/cell under load)
HINGE_P99 = SC.HINGE_P99_FLIGHT
I_OTHER_A = 1.0            # ASSUMED other loads during the landing burn: avionics 0.35 A + MV latch 0.20 A + pintle servo
                           #   holding/slow throttle ~0.45 A (no roll RCS; with the RCS provision fitted add up to 2.8 A)
I_RCS_A = 2 * 0.75 * 12.0 / 0.85 / 7.6   # DERIVED: 2 coils x 0.75 A (LEAD ASSUMED) at 12 V through the U3V70F12 (eta 0.85 ASSUMED)

# ---------------------------------------------------------------------------------------------------------- part data
CU_RHO_20C = 1.7241e-8     # LITERATURE: annealed copper (IACS) resistivity at 20 C [ohm m]
CU_ALPHA = 0.00393         # LITERATURE: copper temperature coefficient [1/K]


def awg_ohm_per_m(awg, T_C=20.0):
    """LITERATURE: AWG diameter d = 0.127 mm x 92^((36 - n)/39) (ASTM B258), solid-equivalent copper."""
    d = 0.127e-3 * 92 ** ((36 - awg) / 39.0)
    return CU_RHO_20C * (1 + CU_ALPHA * (T_C - 20.0)) / (math.pi * d * d / 4.0)


def pcb_ohm(length_m, width_m, oz=2.0, T_C=40.0):
    """DERIVED: copper pour resistance, 1 oz = 35 um."""
    return CU_RHO_20C * (1 + CU_ALPHA * (T_C - 20.0)) * length_m / (width_m * 35e-6 * oz)


# AOS AOD4185 Rev 4.2 (June 2024), read 2026-10-12: RDS(on) typ/max 12.5/15 mOhm @ VGS -10 V (ID -20 A), 16/20 mOhm @ -4.5 V
# (ID -15 A), 19/23 mOhm @ -10 V and TJ 125 C. Gate drive in ecu_design.py: R401 47k (gate-source) / R402 4.7k to the 2N7002
# -> VGS = -VBAT x 47/51.7.
AOD4185 = {'typ': {-10.0: 12.5e-3, -4.5: 16.0e-3}, 'max': {-10.0: 15.0e-3, -4.5: 20.0e-3}, 'tc_per_K': (23.0 / 15.0 - 1.0) / 100.0,
           'src': 'DATASHEET AOS AOD4185 Rev 4.2 (2024-06): RDS(on) 12.5/15 mOhm @ -10 V, 16/20 mOhm @ -4.5 V, 19/23 @ 125 C'}


def aod4185(vbat, col, Tj_C=40.0):
    vgs = -vbat * 47.0 / 51.7
    t = AOD4185[col]
    f = (vgs - (-4.5)) / (-10.0 - (-4.5))     # ASSUMED linear in VGS between the two datasheet points
    f = min(max(f, 0.0), 1.0)
    r25 = t[-4.5] + (t[-10.0] - t[-4.5]) * f
    return r25 * (1 + AOD4185['tc_per_K'] * (Tj_C - 25.0)), vgs


def el(name, typ, mx, tag, src, n_current='single'):
    return {'name': name, 'typ_mohm': round(typ * 1e3, 3), 'max_mohm': round(mx * 1e3, 3), 'tag': tag, 'src': src,
            'carries': n_current}


def chains(vbat):
    """Element lists for the three configurations. 'source' carries I_total, 'common' carries both TVC servo currents,
    'branch' carries one servo's current."""
    q_typ, vgs = aod4185(vbat, 'typ')
    q_max, _ = aod4185(vbat, 'max', Tj_C=60.0)
    awg = {n: awg_ohm_per_m(n, 30.0) for n in (12, 14, 16, 18, 20)}
    ATM_UNK = 'TO-CONFIRM Littelfuse 297 (MINI/ATM) datasheet cold-resistance column (not retrievable through the proxy on 2026-10-12)'
    MF_UNK = 'TO-CONFIRM Molex Micro-Fit 3.0 product specification PS-43045 (low-level contact resistance; not retrievable 2026-10-12)'
    src_common = [
        el('pack leads AWG14 2 x 0.10 m (stock pack leads)', 0.2 * awg[14], 0.2 * awg[14], 'LITERATURE+ASSUMED', 'AWG table at 30 C; length ASSUMED'),
        el('XT60 mated pair (2 contacts)', 1.0e-3, 2.0e-3, 'ASSUMED', 'TO-CONFIRM AMASS XT60 contact resistance; bench B-PWR-1 includes it'),
        el('F101 ATM 25 A + Keystone 3568 holder', 3.0e-3, 4.5e-3, 'ASSUMED', ATM_UNK),
        el('current shunt (INA181 sense)', 2.0e-3, 2.02e-3, 'DESIGN', 'ecu_design.py: INA181A1 x20 on 2 mOhm (1 % part)'),
        el('PCB VBAT_IN -> VBAT, 2 oz, 8 mm x 40 mm', pcb_ohm(0.04, 0.008), pcb_ohm(0.04, 0.005, T_C=60.0), 'DERIVED', 'copper pour; layout not routed'),
    ]
    out = {}
    # --- design basis accepted by the lead (SIL v2.2 sim.h: R_batt 0.015 for the whole source path, R_lead 0.020 per servo)
    out['basis_SIL_v2.2'] = {
        'source': [el('pack + source path (lumped)', 15e-3, 15e-3, 'ASSUMED', 'LEAD 2026-10-12 accepted value, open item B-PWR-1')],
        'common': [],
        'branch': [el('servo branch (lumped)', 20e-3, 20e-3, 'ASSUMED', 'LEAD 2026-10-12 accepted value, open item B-PWR-2')],
        'pack_mohm': None}
    # --- v2.2 as drawn
    out['v2.2_as_drawn'] = {
        'source': [el('battery leads to the ECU AWG16 2 x 0.30 m (first_pass_v1 harness)', 0.6 * awg[16], 0.6 * awg[16], 'LITERATURE+DESIGN',
                      'calc/first_pass_v1.py battery->ECU run')] + src_common,
        'common': [el('F401 ATM 15 A + Keystone 3568 holder', 5.0e-3, 7.0e-3, 'ASSUMED', ATM_UNK),
                   el('Q401 AOD4185 at VGS %.1f V (typ 40 C / max 60 C junction)' % vgs, q_typ, q_max, 'DATASHEET+DERIVED', AOD4185['src']),
                   el('PCB VBAT -> TVC_PWR, 2 oz, 6 mm x 40 mm', pcb_ohm(0.04, 0.006), pcb_ohm(0.04, 0.004, T_C=60.0), 'DERIVED', 'copper pour; layout not routed')],
        'branch': [el('PCB TVC_PWR -> J401 and GND return', pcb_ohm(0.03, 0.004), pcb_ohm(0.03, 0.003, T_C=60.0), 'DERIVED', 'copper pour'),
                   el('Micro-Fit 3.0 mated pair (V+ and GND contacts)', 2 * 5e-3, 2 * 10e-3, 'ASSUMED', MF_UNK),
                   el('extension AWG20 2 x 0.15 m', 0.3 * awg[20], 0.3 * awg[20], 'LITERATURE+ASSUMED', 'first_pass_v1 TVC lead gauge; length ASSUMED'),
                   el('servo JR/universal plug mated pair (adapter lead)', 2 * 5e-3, 2 * 10e-3, 'ASSUMED', 'TO-CONFIRM; not published for JR-type servo plugs')],
        'pack_mohm': 15.0}
    # --- v2.3 proposal (Electronics: two AOD4185 in parallel, F401 deleted, plug cut, AWG18 extension, AWG12 battery leads)
    q2t, q2m = q_typ / 2 * 1.10, q_max / 2 * 1.20      # ASSUMED 10/20 % current-sharing allowance for paralleled MOSFETs
    out['v2.3_proposal'] = {
        'source': [el('battery leads to the ECU AWG12 2 x 0.30 m', 0.6 * awg[12], 0.6 * awg[12], 'LITERATURE+DESIGN', 'v2.3 harness')] + src_common,
        'common': [el('F401 deleted (hard-short protection by F101 25 A; firmware e-fuse on the pad)', 0.0, 0.0, 'DESIGN', 'v2.3 proposal'),
                   el('Q401 + Q403 AOD4185 in parallel at VGS %.1f V (+10/20 %% sharing)' % vgs, q2t, q2m, 'DATASHEET+DERIVED', AOD4185['src']),
                   el('PCB VBAT -> TVC_PWR, 2 oz, 10 mm x 30 mm', pcb_ohm(0.03, 0.010), pcb_ohm(0.03, 0.007, T_C=60.0), 'DERIVED', 'copper pour')],
        'branch': [el('PCB TVC_PWR -> J401 and GND return', pcb_ohm(0.02, 0.005), pcb_ohm(0.02, 0.004, T_C=60.0), 'DERIVED', 'copper pour'),
                   el('Micro-Fit 3.0 mated pair (V+ and GND contacts)', 2 * 5e-3, 2 * 10e-3, 'ASSUMED', MF_UNK),
                   el('extension AWG18 2 x 0.15 m, crimped onto the cut servo lead', 0.3 * awg[18], 0.3 * awg[18], 'LITERATURE+ASSUMED', 'v2.3 harness'),
                   el('servo plug removed (lead cut, butt-spliced or crimped)', 0.5e-3, 1.0e-3, 'ASSUMED', 'splice/crimp joint pair')],
        'pack_mohm': 15.0}
    return out


def sums(c, col, pack_mohm=None):
    key = col + '_mohm'
    rs = sum(e[key] for e in c['source']) * 1e-3
    if pack_mohm is not None:
        rs += pack_mohm * 1e-3
    rc = sum(e[key] for e in c['common']) * 1e-3
    rb = sum(e[key] for e in c['branch']) * 1e-3
    return rs, rc, rb


def i_stall(V):
    """DATASHEET 7.5 A @ 6.0 V, 9.2 A @ 7.4 V (Savox SB-2292SG listing), linear (motor + driver resistance constant)."""
    p = PDB.SB2292SG['stall_current_A']['v']
    a, b = p['6.0'], p['7.4']
    return a + (b - a) / 1.4 * (V - 6.0)


def plug_voltage_hold(voc, rs, rc, rb, i_other=I_OTHER_A):
    """Both servos at stall: V = voc - (2 I + Io) rs - 2 I rc - I rb with I = a + k (V - 6). Closed form."""
    p = PDB.SB2292SG['stall_current_A']['v']
    k = (p['7.4'] - p['6.0']) / 1.4
    a = p['6.0'] - 6.0 * k                       # I = a + k V
    req = 2 * rs + 2 * rc + rb                   # per-servo equivalent including the source shared by both
    V = (voc - i_other * rs - a * req) / (1 + k * req)
    return V, a + k * V


def plug_voltage_slew(voc, rs, rc, rb, frac, i_other=I_OTHER_A):
    """Both servos on the loaded operating point: I = I_run + (I_stall(V) - I_run) * frac (frac = T_load/T_stall of the
    limiting servo, from the slew model). Fixed point (frac itself depends weakly on V; one outer iteration is enough)."""
    i_run = PDB.SB2292SG['running_current_A']['v']['7.4']
    V = voc
    for _ in range(30):
        I = i_run + (i_stall(V) - i_run) * frac
        V = voc - (2 * I + i_other) * rs - 2 * I * rc - I * rb
    return V, I


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine-root', default=os.environ.get('ENGINE_ROOT', '/home/claude/work/shared-fallback/engine'))
    args = ap.parse_args()
    fn = os.path.join(args.engine_root, 'interfaces', 'mechanical.json')
    raw = open(fn, 'rb').read()
    mech = json.loads(raw)
    geo = SC.Geometry(mech, R_H_N48)
    terms = geo.terms
    TL = sum(abs(terms[k]) for k in terms if not k.startswith('inertia_'))

    # capability vs plug voltage (n 4.8), the same functions as tvc_slew_check_v1
    grid = [6.4 + 0.1 * k for k in range(21)]
    cap = []
    for V in grid:
        Ts, wnl = SC.servo(V)
        sc = SC.scan(geo, Ts, wnl, TL)
        st = []
        for kd in range(72):
            th = 2 * math.pi * kd / 72
            u = (math.cos(th), math.sin(th))
            for d in (0.0, SC.REQ_RANGE_DEG):
                st.append(SC.stall_moment(geo.point(d * D2R * u[0], d * D2R * u[1], u), Ts))
        u = (math.cos(math.radians(sc['dir_deg'])), math.sin(math.radians(sc['dir_deg'])))
        a, b = sc['at_deg'] * D2R * u[0], sc['at_deg'] * D2R * u[1]
        pt = geo.point(a, b, u)
        frac = max(TL * p['tau'] / Ts for p in pt)          # load fraction of the limiting servo at the worst point
        cap.append({'V_plug': round(V, 2), 'Ts_Nm': round(Ts, 3), 'slew_worst_dps': round(sc['rate_dps'], 1),
                    'hold_min_Nm': round(min(st), 2), 'load_frac_worst': round(frac, 3)})

    def interp(V, key):
        if V <= cap[0]['V_plug']:
            c0, c1 = cap[0], cap[1]
        elif V >= cap[-1]['V_plug']:
            c0, c1 = cap[-2], cap[-1]
        else:
            j = max(i for i in range(len(cap)) if cap[i]['V_plug'] <= V + 1e-9)
            j = min(j, len(cap) - 2)
            c0, c1 = cap[j], cap[j + 1]
        return c0[key] + (c1[key] - c0[key]) * (V - c0['V_plug']) / (c1['V_plug'] - c0['V_plug'])

    # plug voltage at which the holding moment equals GNC's p99 hinge moment
    v_hold_p99 = next(round(c0['V_plug'] + (HINGE_P99 - c0['hold_min_Nm']) * (c1['V_plug'] - c0['V_plug']) / (c1['hold_min_Nm'] - c0['hold_min_Nm']), 3)
                      for c0, c1 in zip(cap, cap[1:]) if c0['hold_min_Nm'] <= HINGE_P99 <= c1['hold_min_Nm'])
    v_slew_100 = next(round(c0['V_plug'] + (100.0 - c0['slew_worst_dps']) * (c1['V_plug'] - c0['V_plug']) / (c1['slew_worst_dps'] - c0['slew_worst_dps']), 3)
                      for c0, c1 in zip(cap, cap[1:]) if c0['slew_worst_dps'] <= 100.0 <= c1['slew_worst_dps'])
    v_slew_120 = next(round(c0['V_plug'] + (120.0 - c0['slew_worst_dps']) * (c1['V_plug'] - c0['V_plug']) / (c1['slew_worst_dps'] - c0['slew_worst_dps']), 3)
                      for c0, c1 in zip(cap, cap[1:]) if c0['slew_worst_dps'] <= 120.0 <= c1['slew_worst_dps'])

    VOCS = (8.4, 8.3, 8.2, 8.1, 7.8, 7.6, 7.4, 7.0, 6.6)
    ch = chains(V_ARM)
    cases = []
    configs = [('basis_SIL_v2.2', 'typ', None), ('v2.2_as_drawn', 'typ', 15.0), ('v2.2_as_drawn', 'max', 15.0),
               ('v2.3_proposal', 'typ', 15.0), ('v2.3_proposal', 'max', 15.0), ('v2.3_proposal', 'typ', 6.0), ('v2.3_proposal', 'typ', 24.0)]
    for name, col, pack in configs:
        c = ch[name]
        rs, rc, rb = sums(c, col, pack)
        req = 2 * rs + 2 * rc + rb
        row = {'config': name, 'column': col, 'pack_mohm': pack, 'R_source_mohm': round(rs * 1e3, 2), 'R_common_mohm': round(rc * 1e3, 2),
               'R_branch_mohm': round(rb * 1e3, 2),
               'R_branch_equivalent_mohm': round((2 * rc + rb) * 1e3, 2),
               'note_equivalent': 'per servo with both servos at equal current: 2 x common + branch (what the ECU constant kRBranchEqCal_ohm holds)',
               'by_rest_voltage': []}
        for voc in VOCS:
            vh, ih = plug_voltage_hold(voc, rs, rc, rb)
            frac = interp(min(max(vh, cap[0]['V_plug']), cap[-1]['V_plug']), 'load_frac_worst')
            vs, is_ = plug_voltage_slew(voc, rs, rc, rb, frac)
            row['by_rest_voltage'].append({
                'V_rest': voc, 'HOLD_V_plug': round(vh, 3), 'HOLD_I_servo_A': round(ih, 2), 'HOLD_sag_V': round(voc - vh, 3),
                'hold_min_Nm': round(interp(vh, 'hold_min_Nm'), 2), 'hold_ge_p99': interp(vh, 'hold_min_Nm') >= HINGE_P99,
                'SLEW_V_plug': round(vs, 3), 'SLEW_I_servo_A': round(is_, 2), 'slew_worst_dps': round(interp(vs, 'slew_worst_dps'), 1)})
        # rest voltage needed for 7.6 V at the plug under HOLD (bisection)
        lo, hi = 7.0, 10.0
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if plug_voltage_hold(mid, rs, rc, rb)[0] < V_DESIGN:
                lo = mid
            else:
                hi = mid
        row['V_rest_needed_for_7.6V_hold'] = round(hi, 3)
        lo, hi = 7.0, 10.0
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if interp(plug_voltage_hold(mid, rs, rc, rb)[0], 'hold_min_Nm') < HINGE_P99:
                lo = mid
            else:
                hi = mid
        row['V_rest_needed_for_hold_p99'] = round(hi, 3)
        cases.append(row)

    # sensitivity of the holding moment at the ARM permit to each element of the v2.3 typical chain
    k_hold = (interp(7.7, 'hold_min_Nm') - interp(7.5, 'hold_min_Nm')) / 0.2     # N m per V near the design point
    i_d = i_stall(V_DESIGN)
    sens = {'dHold_dV_Nm_per_V': round(k_hold, 2), 'I_stall_at_7.6V_A': round(i_d, 2),
            'per_mohm_source_V': round((2 * i_d + I_OTHER_A) * 1e-3, 4), 'per_mohm_common_V': round(2 * i_d * 1e-3, 4),
            'per_mohm_branch_V': round(i_d * 1e-3, 4)}

    # ECU constants (firmware/src/core/config.h) - design basis until the bench values exist
    rs0, rc0, rb0 = sums(ch['basis_SIL_v2.2'], 'typ')
    vh_arm, _ = plug_voltage_hold(V_ARM, rs0, rc0, rb0)
    ecu = {
        'kTvcSupplyMin_V': {'v': V_DESIGN, 'tag': 'LEAD', 'src': 'design point >= 7.6 V at the servo under peak (stall) load'},
        'kTvcSupplyHyst_V': {'v': 0.10, 'tag': 'DESIGN'},
        'kTvcSupplyTime_s': {'v': 0.10, 'tag': 'DESIGN', 'note': 'set persistence; clear after 0.5 s above min + hysteresis'},
        'kTvcServoDesign_A': {'v': round(i_d, 2), 'tag': 'DERIVED', 'src': 'DATASHEET stall current 7.5 A @ 6.0 V, 9.2 A @ 7.4 V, linear to 7.6 V'},
        'kAuxDesign_A': {'v': I_OTHER_A, 'tag': 'ASSUMED', 'note': 'landing-burn other loads; roll RCS adds up to %.1f A' % I_RCS_A},
        'kRSrcCal_ohm': {'v': rs0, 'tag': 'ASSUMED (LEAD-accepted basis)', 'replace_with': 'bench B-PWR-1 (and the in-situ estimate every flight)'},
        'kRBranchEqCal_ohm': {'v': 2 * rc0 + rb0, 'tag': 'ASSUMED (LEAD-accepted basis)', 'replace_with': 'bench B-PWR-2'},
        'predicted_hold_plug_V_at_ARM_permit_with_basis': round(vh_arm, 3),
        'note': ('with the accepted basis, the 8.1 V rest permit and the 7.6 V predicted-voltage check coincide; with bench values '
                 'worse than the basis the predicted-voltage check refuses ARM first (Abort TVC_SUPPLY = 19)')}
    out = {'tool': 'calc/tvc_supply_budget_v1.py', 'date': datetime.date.today().isoformat(),
           'inputs': {'mechanical_json': {'version': mech.get('version'), 'sha256_16': hashlib.sha256(raw).hexdigest()[:16]},
                      'geometry': {'r_h_m': R_H_N48, 'r_e_m': geo.r_e, 'n': round(geo.r_e / R_H_N48, 2), 'tag': 'LEAD provisional n 4.8'},
                      'slew_load_Nm': {'v': round(TL, 3), 'tag': 'DERIVED (mechanical.json non-inertial hinge terms summed)'},
                      'servo': {'stall_current_A': PDB.SB2292SG['stall_current_A'], 'running_current_A': PDB.SB2292SG['running_current_A'],
                                'reference_plane': {'v': 'servo plug, stock 300 mm lead included', 'tag': 'ASSUMED (vendor test conditions unpublished)'}},
                      'I_other_A': {'v': I_OTHER_A, 'tag': 'ASSUMED'}, 'I_roll_rcs_A': {'v': round(I_RCS_A, 2), 'tag': 'DERIVED from LEAD ASSUMED 0.75 A/coil'},
                      'hinge_p99_Nm': {'v': HINGE_P99, 'tag': 'LEAD (GNC sim6 v2.3)'},
                      'aod4185': AOD4185['src'], 'copper': 'LITERATURE: IACS 1.7241e-8 ohm m at 20 C, alpha 0.00393/K, ASTM B258 AWG diameters'},
           'A_chains_at_8.1V': ch,
           'C_capability_vs_plug_voltage_n4.8': cap,
           'plug_voltage_thresholds': {'hold_equals_GNC_p99_15.6Nm_V': v_hold_p99, 'slew_worst_100dps_V': v_slew_100,
                                       'slew_worst_120dps_V': v_slew_120},
           'B_cases': cases, 'sensitivity_at_design_point': sens, 'D_ecu_constants': ecu}
    # verdicts
    def row(name, col, pack):
        return next(r for r in cases if r['config'] == name and r['column'] == col and r['pack_mohm'] == pack)
    v22, v23, v23lo = row('v2.2_as_drawn', 'typ', 15.0), row('v2.3_proposal', 'typ', 15.0), row('v2.3_proposal', 'typ', 6.0)
    at = lambda r, voc: next(x for x in r['by_rest_voltage'] if abs(x['V_rest'] - voc) < 1e-9)
    out['verdict'] = {
        'basis': 'The accepted basis (source 15 + branch 20 mOhm, nothing shared) gives %.2f V at the plug with both servos stalled from the 8.1 V permit.'
                 % at(row('basis_SIL_v2.2', 'typ', None), 8.1)['HOLD_V_plug'],
        'v2.2_as_drawn_typ': ('equivalent branch %.1f mOhm (vs 20 assumed) and source %.1f mOhm: %.2f V at the plug, holding %.1f N m '
                              '(p99 %.1f) at the 8.1 V permit; slew is not the issue (%.2f V, %.0f deg/s)'
                              % (v22['R_branch_equivalent_mohm'], v22['R_source_mohm'], at(v22, 8.1)['HOLD_V_plug'], at(v22, 8.1)['hold_min_Nm'], HINGE_P99,
                                 at(v22, 8.1)['SLEW_V_plug'], at(v22, 8.1)['slew_worst_dps'])),
        'v2.3_proposal_typ': ('equivalent branch %.1f mOhm: %.2f V at the plug, holding %.1f N m at 8.1 V; rest voltage for 7.6 V: %.2f V'
                              % (v23['R_branch_equivalent_mohm'], at(v23, 8.1)['HOLD_V_plug'], at(v23, 8.1)['hold_min_Nm'], v23['V_rest_needed_for_7.6V_hold'])),
        'v2.3_low_IR_pack_typ': ('with a 6 mOhm pack: %.2f V at the plug, holding %.1f N m at 8.1 V; rest voltage for 7.6 V: %.2f V'
                                 % (at(v23lo, 8.1)['HOLD_V_plug'], at(v23lo, 8.1)['hold_min_Nm'], v23lo['V_rest_needed_for_7.6V_hold'])),
        'reading': ('The holding case (both servos at stall, ~9.4 A each) sets the supply requirement, not the slew (~1-2 A per servo). '
                    'Every 1 mOhm in the shared source costs %.3f V, in the TVC common path %.3f V and in one servo branch %.3f V; '
                    'near the design point the holding moment moves %.2f N m per volt.' % (sens['per_mohm_source_V'], sens['per_mohm_common_V'],
                                                                                       sens['per_mohm_branch_V'], sens['dHold_dV_Nm_per_V']))}
    res = os.path.join(HERE, '..', 'results')
    os.makedirs(res, exist_ok=True)
    json.dump(out, open(os.path.join(res, 'tvc_supply_budget_v1.json'), 'w'), indent=1)
    L = ['TVC supply budget v1 (%s), mechanical.json %s sha %s, n %.2f, slew load %.2f N m' %
         (out['date'], mech.get('version'), out['inputs']['mechanical_json']['sha256_16'], geo.r_e / R_H_N48, TL)]
    L.append('Capability vs plug voltage (n 4.8): ' + ', '.join('%.1f V: %.1f deg/s / %.1f N m' % (c['V_plug'], c['slew_worst_dps'], c['hold_min_Nm'])
                                                              for c in cap if abs(c['V_plug'] * 10 - round(c['V_plug'] * 10)) < 1e-6 and round(c['V_plug'] * 10) % 2 == 0))
    L.append('Plug voltage for holding = p99 15.6 N m: %.3f V; worst slew 100 deg/s: %.3f V; 120 deg/s: %.3f V' % (v_hold_p99, v_slew_100, v_slew_120))
    for name in ('basis_SIL_v2.2', 'v2.2_as_drawn', 'v2.3_proposal'):
        L.append('Chain %s at 8.1 V:' % name)
        for part in ('source', 'common', 'branch'):
            for e in ch[name][part]:
                L.append('   %-7s %-86s typ %6.2f max %6.2f mOhm [%s]' % (part, e['name'], e['typ_mohm'], e['max_mohm'], e['tag']))
    for r in cases:
        L.append('Case %-15s %-3s pack %-4s: R_src %.1f, common %.1f, branch %.1f, equivalent branch %.1f mOhm | rest for 7.6 V hold %.2f V, for p99 hold %.2f V'
                 % (r['config'], r['column'], r['pack_mohm'], r['R_source_mohm'], r['R_common_mohm'], r['R_branch_mohm'], r['R_branch_equivalent_mohm'],
                    r['V_rest_needed_for_7.6V_hold'], r['V_rest_needed_for_hold_p99']))
        for x in r['by_rest_voltage']:
            if x['V_rest'] in (8.4, 8.1, 7.4, 6.6):
                L.append('     rest %.1f V: HOLD plug %.2f V (%.2f A/servo, sag %.2f V) -> hold %.1f N m %s | SLEW plug %.2f V (%.2f A) -> %.1f deg/s'
                         % (x['V_rest'], x['HOLD_V_plug'], x['HOLD_I_servo_A'], x['HOLD_sag_V'], x['hold_min_Nm'], '>= p99' if x['hold_ge_p99'] else '< p99',
                            x['SLEW_V_plug'], x['SLEW_I_servo_A'], x['slew_worst_dps']))
    L.append('Sensitivity: ' + json.dumps(sens))
    L.append('ECU constants: ' + json.dumps({k: (x['v'] if isinstance(x, dict) else x) for k, x in ecu.items() if k != 'note'}))
    for k, x in out['verdict'].items():
        L.append('VERDICT %s: %s' % (k, x))
    open(os.path.join(res, 'tvc_supply_budget_v1.txt'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
