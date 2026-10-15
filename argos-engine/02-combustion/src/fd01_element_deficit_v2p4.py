"""FD-01 leg flow deficit from Mechanical's F2 inline element (Combustion v2.4, 2026-10-13; coordinator after CHANGELOG 162-164).

Mechanical (line 162): F3 equal 0.707 mm restrictors; F2 an inline <= 15 um element on the FD-01 leg, between the tap and the
tee, with Cd.A >= 1.57 mm2 (4x the restrictor's geometric area).  Coordinator: check the FD-01 leg deficit; run the two-flow
purge grid only if the margin at 2.5 s drops below 0.3 s, otherwise state the bound.

Restrictor: 0.707 mm, Cd 0.70 ASSUMED (Cd.A 0.2748 mm2), discharging to ambient; the coast state is saturated liquid at 289.5 K
(46.45 bar) or saturated vapour.  Three readings of the element in series (element Cd.A 1.57 mm2 and, for the coordinator's
estimate, 4 x 0.2748 = 1.10 mm2):
  (i)   incompressible series (both resistances single-phase): Cd.A_eff = 1 / sqrt(1/a_r^2 + 1/a_e^2);
  (ii)  liquid, metastable through the element (no flashing), restrictor by Dyer at the reduced inlet pressure (kappa < 1);
  (iii) liquid flashing to equilibrium in the element (isenthalpic), restrictor inlet two-phase: Dyer form with kappa = 1, the
        SPI term on the homogeneous inlet density and the HEM term from the two-phase inlet (lower bound: HEM ignores
        non-equilibrium in a short orifice); the element dP on the homogeneous density at its outlet.
Vapour: element dP on the vapour density; choked HEM restrictor flux proportional to its inlet pressure (DERIVED).
usage: python -I fd01_element_deficit_v2p4.py OUT_JSON
"""
from __future__ import annotations
import hashlib, json, math, os, sys
sys.dont_write_bytecode = True
import numpy as np
import CoolProp.CoolProp as CP
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import n2o as N

T0 = 289.5
P_AMB = 1.0e5
A_R = 0.70 * math.pi / 4 * (0.707e-3) ** 2
AS = CP.AbstractState('HEOS', 'NitrousOxide')


def state_ph(p, h):
    AS.update(CP.HmassP_INPUTS, float(h), float(p))
    return AS.rhomass(), AS.smass(), AS.Q()


def hem_from(p1, h1, p2=P_AMB, n=80):
    _, s1, _ = state_ph(p1, h1)
    best = 0.0
    for p in np.linspace(max(p2, 2e5), p1 * 0.9999, n):
        AS.update(CP.PSmass_INPUTS, float(p), float(s1))
        dh = h1 - AS.hmass()
        if dh > 0:
            best = max(best, AS.rhomass() * math.sqrt(2 * dh))
    return best


def main(out_f):
    sp = N.sat_props(T0)
    P0, rho_l, h_l, rho_v, h_v = sp['P'], sp['rho_l'], sp['h_l'], sp['rho_v'], sp['h_v']
    G0 = N.G_dyer(P0, T0, P_AMB)          # saturated liquid, no element (the purge model's 56 843 kg/m2s)
    m0 = A_R * G0
    res = dict(P0_bar=P0 / 1e5, rho_l=rho_l, rho_v=rho_v, G0_liquid_kg_m2s=G0, mdot0_liquid_g_s=m0 * 1e3, readings={})
    for lab, a_e in (('Mechanical_CdA_1.57mm2', 1.57e-6), ('coordinator_4x_CdA_1.10mm2', 4 * A_R)):
        r = {}
        # (i) incompressible series
        r['i_incompressible_ratio'] = 1.0 / math.sqrt(1.0 + (A_R / a_e) ** 2)
        # (ii) metastable liquid through the element, Dyer at the reduced inlet pressure (kappa < 1, T1 = T0)
        m = m0
        for _ in range(60):
            dpe = (m / a_e) ** 2 / (2 * rho_l)
            P1 = P0 - dpe
            k = math.sqrt((P1 - P_AMB) / (P0 - P_AMB))
            gs = math.sqrt(2 * rho_l * (P1 - P_AMB)); gh = hem_from(P0 - 1.0, h_l)   # HEM from the saturated state (metastable)
            m_new = A_R * ((k / (1 + k)) * gs + (1 / (1 + k)) * gh)
            if abs(m_new - m) < 1e-9:
                break
            m = 0.5 * (m + m_new)
        r['ii_metastable'] = dict(mdot_g_s=m * 1e3, ratio=m / m0, element_dP_bar=dpe / 1e5)
        # (iii) equilibrium flashing in the element
        m = m0
        for _ in range(80):
            # element outlet state at P1, h_l: homogeneous density; dP on that density (conservative)
            dpe = (m / a_e) ** 2 / (2 * rho_l)
            for _ in range(20):
                P1 = P0 - dpe
                rho1, _, x1 = state_ph(P1, h_l)
                dpe_new = (m / a_e) ** 2 / (2 * rho1)
                if abs(dpe_new - dpe) < 1.0:
                    break
                dpe = dpe_new
            P1 = P0 - dpe
            rho1, _, x1 = state_ph(P1, h_l)
            gs = math.sqrt(2 * rho1 * (P1 - P_AMB)); gh = hem_from(P1, h_l)
            m_new = A_R * (0.5 * gs + 0.5 * gh)
            if abs(m_new - m) < 1e-9:
                break
            m = 0.5 * (m + m_new)
        r['iii_flashing'] = dict(mdot_g_s=m * 1e3, ratio=m / m0, element_dP_bar=dpe / 1e5, inlet_quality=x1)
        # vapour
        mv0 = A_R * 15450.0
        dpv = (mv0 / a_e) ** 2 / (2 * rho_v)
        r['vapour'] = dict(mdot0_g_s=mv0 * 1e3, element_dP_bar=dpv / 1e5, ratio=(P0 - dpv) / P0)
        worst = min(r['i_incompressible_ratio'], r['ii_metastable']['ratio'], r['iii_flashing']['ratio'], r['vapour']['ratio'])
        r['worst_ratio'] = worst
        # effect on the needed purge time: bound = all of the needed time limited by the FD-01 leg
        r['needed_Tp_bound_s'] = 1.9 / worst
        r['margin_at_2p5_bound_s'] = 2.5 - 1.9 / worst
        res['readings'][lab] = r
    res.update(version='v2.4', date='2026-10-13', script='02-combustion/src/fd01_element_deficit_v2p4.py',
               script_sha256_16=hashlib.sha256(open(os.path.abspath(__file__), 'rb').read()).hexdigest()[:16],
               bound_method=('Needed time bound = 1.9 s / (worst FD-01 leg flow ratio): conservative, since T4 carries half of the column flow '
                             'unchanged and, with the open element, also draws the upstream queue; the s 0.5 bracket that governs is fixed and does not '
                             'depend on the column speed'),
               tags='DERIVED (CoolProp HEOS; Dyer / HEM; Cd 0.70 and the element Cd.A from Mechanical line 162; flashing readings bracket the unknown element nucleation)')
    json.dump(res, open(out_f, 'w'), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    main(sys.argv[1])
