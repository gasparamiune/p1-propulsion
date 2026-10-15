"""Ignition trade, torch specification and start/shutdown sequences (Combustion v2, brief task 6).
Writes data/v2/ignition_v2.json.  Torch sizing: RocketCEA N2O/C3H8 (CEA thermo library), CoolProp propane and N2O;
orifice sizing with the Dyer model (liquid N2O) and ideal-gas choking (propane vapour).  usage: python ignition_v2.py OUTDIR
"""
from __future__ import annotations
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import CoolProp.CoolProp as CP
import numpy as np


def torch_sizing():
    from rocketcea.cea_obj_w_units import CEA_Obj
    import injector as INJ
    c = CEA_Obj(oxName='N2O', fuelName='C3H8', pressure_units='bar', cstar_units='m/s', temperature_units='K')
    Pt, OF, dt = 3.0, 5.5, 2.0e-3            # torch chamber pressure [bar abs], mixture ratio, throat diameter [m]
    cs = c.get_Cstar(Pc=Pt, MR=OF); Tc = c.get_Tcomb(Pc=Pt, MR=OF)
    At = math.pi * dt ** 2 / 4
    m = Pt * 1e5 * At / cs
    mf, mo = m / (1 + OF), m * OF / (1 + OF)
    # N2O: liquid from the injector manifold (P1 = Pv - 0.5 bar) through a sharp orifice into the torch at 3 bar
    rows_n2o = []
    for Tc_ in (10.0, 20.0, 25.0):
        T1 = Tc_ + 273.15; pv = INJ.psat(T1)
        spi, hem, dyer, k = INJ.g_models(pv - 0.5e5, T1, np.array([Pt * 1e5]))
        A = mo / (0.65 * dyer[0])
        rows_n2o.append(dict(T_C=Tc_, G_dyer=float(dyer[0]), d_orifice_mm=2e3 * math.sqrt(A / math.pi)))
    # propane vapour from a small cylinder at Psat(T) through a choked orifice (gamma 1.13, R 188.5)
    rows_c3 = []
    g, R = 1.13, 8.314462 / 0.0440956
    crit = (2 / (g + 1)) ** (g / (g - 1))
    for Tc_ in (0.0, 10.0, 20.0, 25.0):
        T = Tc_ + 273.15; p0 = CP.PropsSI('P', 'T', T, 'Q', 1, 'Propane')
        choked = Pt * 1e5 / p0 < crit
        if choked:
            G = p0 * math.sqrt(g / (R * T)) * (2 / (g + 1)) ** ((g + 1) / (2 * (g - 1)))
        else:
            pr = Pt * 1e5 / p0
            G = p0 * math.sqrt(2 * g / ((g - 1) * R * T) * (pr ** (2 / g) - pr ** ((g + 1) / g)))
        rows_c3.append(dict(T_C=Tc_, Psat_bar=p0 / 1e5, choked=bool(choked), G=G,
                            mdot_through_0p30mm_gps=0.8 * G * math.pi * 0.30e-3 ** 2 / 4 * 1e3))
    A_c3 = mf / (0.8 * rows_c3[2]['G'])
    return dict(Pc_torch_bar=Pt, OF=OF, throat_d_m=dt, cstar_m_s=cs, Tc_K=Tc, mdot_total_kg_s=m, mdot_propane_kg_s=mf,
                mdot_n2o_kg_s=mo, enthalpy_flux_W=m * 2000 * (Tc - 300), per_start_0p6s_propane_g=mf * 0.6e3,
                per_start_0p6s_n2o_g=mo * 0.6e3, n2o_orifice=rows_n2o, propane=rows_c3,
                propane_orifice_d_mm_at_20C=2e3 * math.sqrt(A_c3 / math.pi),
                note='Cd 0.65 (N2O sharp orifice) and 0.80 (propane) ASSUMED; torch Pc 3 bar abs keeps the torch outlet '
                     'choked into the cold chamber (~1 bar) and stays below the propane vapour pressure down to ~0 C '
                     '(4.7 bar); calibrate both orifices by cold flow (weighing) before hot torch tests')


TRADE = {
    'criteria_weights': {'restart_count_ge3': 3, 'ignition_reliability_with_N2O': 3, 'hard_start_risk': 2,
                         'mass_on_gimbal': 1, 'electrical_energy_and_HV': 1, 'extra_fluids_or_hazmat': 2,
                         'buildability_cost': 2, 'evidence_base': 2},
    'scale': '1 (poor) .. 5 (good); scores are engineering judgement (DERIVED), stated with their reason',
    'options': {
        'arc_ABS': dict(desc='HV arc across electrodes embedded in the printed ABS at the head end pyrolyses fuel; N2O flow then ignites (USU / Whitmore type)',
                        scores=dict(restart_count_ge3=5, ignition_reliability_with_N2O=2, hard_start_risk=3, mass_on_gimbal=5,
                                    electrical_energy_and_HV=2, extra_fluids_or_hazmat=5, buildability_cost=3, evidence_base=2),
                        reasons='no extra fluid, many relights shown with GOX; with N2O the published work (as recalled, '
                                'LITERATURE-UNVERIFIED here) needed higher arc power or an O2 assist; electrodes must be printed '
                                'into every grain; 200-1000 V class supply near the avionics; restart surface is charred'),
        'torch_N2O_propane': dict(desc='spark-ignited N2O/propane torch firing radially into the pre-chamber (v1 baseline)',
                                  scores=dict(restart_count_ge3=5, ignition_reliability_with_N2O=4, hard_start_risk=4, mass_on_gimbal=3,
                                              electrical_energy_and_HV=4, extra_fluids_or_hazmat=3, buildability_cost=4, evidence_base=4),
                                  reasons='independent of grain state; ~3 kW hot jet for 0.3-0.6 s per start; restarts limited only by '
                                          'propane (0.05 g/start); needs a propane cylinder, 2 NC solenoids, 2 check valves and a spark '
                                          'plug; widely used on amateur and university hybrids; orifice sizes are small (0.15-0.3 mm)'),
        'pyrotechnic': dict(desc='electric match + pyrogen pellet per start (one cartridge per start, 3+ ports or a revolver)',
                            scores=dict(restart_count_ge3=1, ignition_reliability_with_N2O=5, hard_start_risk=4, mass_on_gimbal=4,
                                        electrical_energy_and_HV=5, extra_fluids_or_hazmat=1, buildability_cost=2, evidence_base=5),
                            reasons='excellent first start; each restart needs its own cartridge, port and seal; debris into the '
                                    'injector region; explosives handling and storage rules in Denmark (TO-VERIFY with the '
                                    'authorities and ACEMA rules)'),
        'catalytic_N2O': dict(desc='pre-heated N2O decomposition catalyst (Rh/Ir class on alumina) feeding hot O2/N2 to the grain',
                              scores=dict(restart_count_ge3=4, ignition_reliability_with_N2O=3, hard_start_risk=2, mass_on_gimbal=2,
                                          electrical_energy_and_HV=1, extra_fluids_or_hazmat=4, buildability_cost=1, evidence_base=2),
                              reasons='needs 50-200 W preheat for minutes and a catalyst bed (cost TO-QUOTE); bed poisoning and '
                                      'decomposition propagating upstream into the feed is the N2O hazard this design must avoid'),
    },
}


def scores():
    w = TRADE['criteria_weights']; out = {}
    for k, o in TRADE['options'].items():
        out[k] = sum(w[c] * o['scores'][c] for c in w) / (5 * sum(w.values()))
    return out


SEQUENCE = {
    'arm_preconditions': ['tank 15-25 C (heater blanket for cold days; supercharge not baselined)', 'pintle seated, position '
                          'encoder healthy, isolation valve closed', 'igniter continuity checked (spark coil primary, both '
                          'solenoids)', 'Pc, P_feed, P_tank sensors healthy; Pc reads ambient +/- 0.1 bar'],
    'start': [
        dict(t_s=-0.80, action='ONLY if the line is not primed (P_feed < 0.5 P_tank, e.g. first start after a purge): pintle to '
                               'a 0.10 mm bleed lift BEFORE the isolation valve moves, so the line vents through the injector '
                               '(no dead-ended adiabatic compression of trapped gas: N2 isentropic 847-913 K, N2O vapour '
                               '614-646 K at 45-60 bar, feed_line_checks_v2.json); isolation valve opening ramp >= 0.3 s'),
        dict(t_s=-0.30, action='primed line (relight, P_feed >= 0.5 P_tank): open the NC isolation valve with the pintle seated; '
                               'unprimed line: isolation valve fully open by now and the pintle returns to seated; '
                               'vapour-first (warm line flashes)'),
        dict(t_s=0.00, action='open torch solenoids (N2O SOL1, propane SOL2)'),
        dict(t_s=0.02, action='spark train 50 Hz, 50 mJ, up to 0.5 s'),
        dict(t_s=0.10, action='torch-flame confirmation (photodiode or 0.25 mm thermocouple at the torch outlet, Electronics to '
                              'select; fallback = timing only)'),
        dict(t_s=0.12, action='pintle to the ignition lift (12.5-20 % flow, ~0.2-0.3 mm at 20 C)'),
        dict(t_s=0.35, action='ignition check: Pc > 3.0 bar abs (combustion 4.4-6.2 bar vs cold N2O flow ~1.5 bar); '
                              'if not, ABORT'),
        dict(t_s=0.35, action='ramp to the commanded thrust at <= 2500 N/s (gnc.json engine model slew; a cap: the drive must '
                              'give >= 2 F_max/s, gnc.json v2 ENG-03)'),
        dict(t_s=0.40, action='propane solenoid closed before Pc exceeds 5 bar (propane vapour pressure 6.4 bar at 10 C)'),
        dict(t_s=0.60, action='N2O torch solenoid closed; spark off'),
    ],
    'abort_if_no_ignition': ['pintle closed', 'torch solenoids closed', 'isolation valve closed', 'wait >= 5 s for the chamber '
                             'to vent N2O (no re-try into a pooled chamber)', 'one automatic retry allowed in flight only if '
                             'GNC margin permits; ground: safe the stand and investigate'],
    'shutdown': ['pintle closes to the seat at the drive\'s full speed (v2.2: the v1 "<= 50 mm/s (80 ms full stroke)" is retired; '
                 'no combustion limit on the closing time; the ENG-05 tail-off sets the closing speed: combustion.json '
                 'valves_and_actuators.pintle_actuator.speed_checks)', 'isolation valve closes after the pintle is seated '
                 '(<= 0.15 s)', 'trapped liquid between the isolation valve and the pintle is relieved to the tank side (v1 '
                 'requirement)', 'post-burn: chamber vents through the nozzle; the grain smoulders briefly in air'],
    'relight': ['same as start from t = 0 (the isolation valve may stay open between burns in flight)',
                'settling: liquid at the tank outlet must be confirmed by the acceleration history (A1 has 15 s at ~1 g '
                'before relight; settling_v2.json)', 'torch fires into a hot, fuel-rich chamber: lower ignition energy expected'],
    'flashback_and_backflow': ['check valve on each torch line at the torch inlet (cracking <= 0.3 bar), rated to chamber MEOP 45 bar '
                               'and hot gas', 'torch lines dead-ended during the main burn: the torch body sees Pc and soak '
                               'heat; it is sized for MEOP 45 bar and checked for 30 s exposure (Mechanical)',
                               'no N2O purge through the torch during the main burn (a hot N2O-filled cavity is a '
                               'decomposition site)', 'N2O decomposition in the feed: no heat source upstream of the '
                               'injector, no adiabatic compression of vapour pockets (valves open slowly when lines contain '
                               'vapour), clean Krytox-lubricated hardware only'],
    'purge': ['ground tests: N2 purge of the chamber after shutdown (stand-side valve, 5-10 s) and before a re-start attempt',
              'flight: no purge gas carried (no N2 system baselined); the chamber vents through the nozzle'],
}


if __name__ == '__main__':
    out = sys.argv[1]
    ts = torch_sizing()
    sc = scores()
    act_fn = os.path.join(out, 'actuator_rate_check_v2.json'); floor_txt = ''
    if os.path.exists(act_fn):
        st = [x for x in json.load(open(act_fn))['start']]
        t90 = {f: [x['t90_s'] for x in st if x['frac'] == f] for f in (0.125, 0.2)}
        floor_txt = (f' Step starts to the 12.5 % / 20 % floor reach 90 % at {min(t90[0.125]):.2f}-{max(t90[0.125]):.2f} s / '
                     f'{min(t90[0.2]):.2f}-{max(t90[0.2]):.2f} s for every drive speed 0.08-0.40 s full stroke (actuator_rate_check_v2.json).')
    J = dict(version='v2.2', date='2026-10-12', revision_note='v2.2 (2026-10-12): shutdown wording - the v1 pintle closing speed '
             '"<= 50 mm/s (80 ms full stroke)" is retired (no combustion basis; lead request on the HV69 drive); start ramp marked as a cap; '
             'floor-start t90 added to model_transients. Torch sizing unchanged (recomputed, same inputs).', decision='spark-ignited N2O/propane torch (baseline kept); arc-ABS kept as a '
             'research option for bench tests (would remove the propane system)', weighted_scores=sc, trade=TRADE,
             torch=dict(sizing=ts, envelope=dict(body_max_length_m=0.045, body_max_diameter_m=0.020, mount='radial boss on the '
                        'head section at x_face 0.015 m, axis inclined 30 deg inward/aft so the plug end stays inside the 120 mm '
                        'head sweep (answers Mechanical REQUEST 2026-10-12)', outlet_bore_m=0.003),
                        materials='316L body, PTFE/FKM seals, nickel-electrode micro spark plug (model-engine class, TO-QUOTE)',
                        electrical=dict(spark_supply_V=12.0, coil_primary_peak_A=4.0, spark_energy_J=0.05, rate_Hz=50.0, train_s=0.5,
                                        solenoid_V=12.0, solenoid_A_each=0.8, solenoid_on_s=0.6, energy_per_start_J=15.0),
                        mass_estimate_kg=dict(v=[0.20, 0.30], tag='ASSUMED: body 50 g, plug 10 g, two micro solenoids 60-120 g, '
                                              'propane cylinder 50 g, lines/fittings 50 g')),
             sequence=SEQUENCE,
             model_transients='SIM grain_q1d v2 (ASSUMED torch-to-main delay 0.10 s, 30 % preheated regression at main-flow '
                              'arrival): relights in A1/A2 reach 10 % thrust 0.10-0.11 s and 90 % 0.28-0.29 s after the command; '
                              'DC-D first start t10-90 0.04 s. Ignition delay is the least certain input: static fire measures it.' + floor_txt)
    json.dump(J, open(os.path.join(out, 'ignition_v2.json'), 'w'), indent=1, default=float)
    print(json.dumps(sc, indent=1)); print(json.dumps(ts, indent=1, default=float))
