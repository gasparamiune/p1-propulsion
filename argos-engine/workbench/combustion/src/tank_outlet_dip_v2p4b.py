"""Landing-burn tank-outlet dip onset (Combustion v2.4b, 2026-10-13; REV-COMB-3 R3-17; LEAD CHANGELOG line 194 (6)).

The liquid left in the N2O tank when gas is first pulled into the outlet by the drain dip (no swirl), by thrust level, for GNC's landing
usable reserve and for Mechanical's OI-32 outlet geometry.  Same correlation and tank geometry as the v2.4a PURGE coverage screening
(unpurged_start_check_v2p4a.py part D, 41fad4500f472bd4):
  Lubin & Springer (1967), non-swirling drain from a flat bottom: h_c = 0.69 (Q^2 / g' x rho_l / (rho_l - rho_v))^0.2, independent of
  the outlet diameter in this form (LITERATURE as recalled; applicability to near-saturated N2O TO-VERIFY);
  Q = mdot_ox(F) / rho_l, mdot_ox from the S230 throttle map (SIM grain_q1d v2 nominal law, Cd 0.70, eta_c* 0.92), the largest value over
  the map's port diameters and tank pressures 3.5-5.0 MPa (conservative: a larger Q raises h_c);
  g' = F / m: the axial specific force of the vehicle at thrust F, m from GNC's ledger v3d dry mass 13.6706 kg (gnc.json v3.1,
  4f3209323b0e0ed4) to 13.6706 + 0.6 kg (ASSUMED end-of-burn residual N2O and grain); a larger m lowers g' and raises h_c;
  liquid mass at onset m_c = rho_l x A_tank x h_c with a centre outlet on a flat aft bulkhead, no tilt (a planar tilted surface keeps
  the mean depth over a centre outlet), A_tank from the tank tube of mechanical.json (fixed_module.tank, v1 concept, not in CAD);
  rho_l, rho_v saturated (CoolProp) at the tank temperature 270-289.5 K (the end-of-flight tank temperature is GNC's; 270 K is an
  ASSUMED cold bound after the blow-down).
Not modelled: swirl (vortexing raises h_c; the roll spin-up time of the liquid is >= 359 s, v2.4a part D), slosh, the outlet position
and shape, a sump, dip tube or anti-vortex baffle (all MISSING: the tank is not in CAD), and the liquid held in the outlet line.
Tags: DERIVED on LITERATURE correlation, SIM map flows and DESIGN-concept geometry; not physical evidence.
usage: python -I tank_outlet_dip_v2p4b.py THROTTLE_MAP_S230 GNC_JSON MECHANICAL_JSON OUT_JSON
"""
from __future__ import annotations
import csv, hashlib, json, math, os, sys
sys.dont_write_bytecode = True
import numpy as np
import CoolProp.CoolProp as CP

EXPECT = {'map': '4f2e6d846f7253da', 'gnc': '4f3209323b0e0ed4', 'mech': 'e4d3e7c9df529171'}
F_LEVELS = (62.5, 125.0, 250.0, 375.0, 500.0)
T_LIST = (270.0, 283.15, 286.7, 289.5)
M_DRY = 13.6706
M_EXTRA = 0.6
G0 = 9.80665


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def main(map_fn, gnc_fn, mech_fn, out_f):
    for k, f in (('map', map_fn), ('gnc', gnc_fn), ('mech', mech_fn)):
        assert sha16(f) == EXPECT[k], (k, sha16(f))
    G = json.load(open(gnc_fn))
    # the ledger dry mass (GNC v3.1 mass ledger v3d) is asserted where the file carries it
    s = json.dumps(G)
    assert '"dry_mass_kg": 13.6706' in s, 'ledger dry mass not found in gnc.json'
    M = json.load(open(mech_fn))
    tank = M['fixed_module']['tank']
    ID = 0.1016 - 2 * 0.003175                       # tube 4.0 in x 0.125 in wall (v2.4a part D basis)
    A = math.pi * ID * ID / 4.0
    rows = [r for r in csv.reader(open(map_fn)) if r and not r[0].startswith('#')]
    h = rows[0]; rows = rows[1:]
    col = lambda r, k: float(r[h.index(k)])
    mox = {}
    for F in F_LEVELS:
        best = None
        for P in sorted({col(r, 'P_tank_Pa') for r in rows}):
            for D in sorted({col(r, 'D_port_m') for r in rows}):
                sel = sorted([r for r in rows if abs(col(r, 'P_tank_Pa') - P) < 1 and abs(col(r, 'D_port_m') - D) < 1e-9], key=lambda r: col(r, 'F_N'))
                Fs = np.array([col(r, 'F_N') for r in sel]); ms = np.array([col(r, 'mdot_ox') for r in sel])
                if len(Fs) < 2 or F < Fs.min() - 1e-9 or F > Fs.max() + 1e-9:
                    continue
                v = float(np.interp(F, Fs, ms))
                if best is None or v > best[0]:
                    best = (v, P, D)
        mox[F] = best
    out_rows = []
    for F in F_LEVELS:
        if mox[F] is None:
            continue
        md, P, D = mox[F]
        for T in T_LIST:
            rl = CP.PropsSI('D', 'T', T, 'Q', 0, 'NitrousOxide'); rv = CP.PropsSI('D', 'T', T, 'Q', 1, 'NitrousOxide')
            Q = md / rl
            for m in (M_DRY, M_DRY + M_EXTRA):
                gp = F / m
                hc = 0.69 * (Q * Q / gp * rl / (rl - rv)) ** 0.2
                out_rows.append(dict(F_N=F, T_K=T, vehicle_mass_kg=m, mdot_ox_kg_s=md, map_P_tank_Pa=P, map_D_port_m=D, rho_l=rl, rho_v=rv,
                                     g_axial_m_s2=gp, g_axial_g=gp / G0, h_c_mm=1e3 * hc, liquid_at_onset_g=1e3 * rl * A * hc))
    summ = {}
    for F in F_LEVELS:
        r = [x for x in out_rows if x['F_N'] == F]
        if r:
            summ[f'{F:g}N'] = dict(liquid_at_onset_g=[min(x['liquid_at_onset_g'] for x in r), max(x['liquid_at_onset_g'] for x in r)],
                                   liquid_at_onset_g_283_to_289p5K=[min(x['liquid_at_onset_g'] for x in r if x['T_K'] >= 283.0),
                                                                    max(x['liquid_at_onset_g'] for x in r if x['T_K'] >= 283.0)],
                                   h_c_mm=[min(x['h_c_mm'] for x in r), max(x['h_c_mm'] for x in r)], mdot_ox_kg_s=r[0]['mdot_ox_kg_s'])
    out = dict(version='v2.4b', date='2026-10-13', script='02-combustion/src/tank_outlet_dip_v2p4b.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               request='REV-COMB-3 R3-17; LEAD CHANGELOG line 194 (6): landing-burn outlet dip onset by thrust level for GNC and OI-32',
               inputs={os.path.basename(map_fn): sha16(map_fn), 'gnc.json v3.1': sha16(gnc_fn), 'mechanical.json v2.1': sha16(mech_fn)},
               tank=dict(ID_m=ID, area_m2=A, source='mechanical.json fixed_module.tank (v1 concept; tank not in CAD): ' + json.dumps(tank)[:300]),
               correlation='Lubin & Springer (1967) non-swirling drain: h_c = 0.69 (Q^2/g x rho_l/(rho_l - rho_v))^0.2 (LITERATURE as recalled; '
                           'N2O applicability TO-VERIFY)',
               rows=out_rows, summary=summ,
               comparison=dict(GNC_rev1_unusable_residual='3 % = 60 g (ASSUMED, REPORT-GNC-rev1; REV-COMB-3 R3-17)',
                               reviewer_r3_tank_outlet='60-62 g at 125 N, 68-69 g at 250 N, 78-80 g at 500 N (REV-COMB-3 R3-17; comparator only)'),
               missing=['outlet position, diameter and shape on the aft bulkhead; sump, dip tube or anti-vortex baffle (OI-32, Mechanical)',
                        'end-of-flight tank temperature and vehicle mass at the landing burn (GNC)', 'swirl and slosh during the landing burn'],
               tags=dict(flows='SIM S230 map', correlation='LITERATURE (as recalled)', geometry='DESIGN concept', result='DERIVED; not physical evidence'))
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    print(json.dumps(summ, indent=1))
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:5])
