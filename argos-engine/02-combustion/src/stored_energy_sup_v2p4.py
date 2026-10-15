"""Stored-energy rows added for REPORT v2.4 §9.2 (Combustion v2.4, 2026-10-13; RC-05).

The first v2.4 pass (`safing_relief_v2p4.py`, part D) computed the segment row on the 21.42 cm3 valve-to-seat volume and
the chamber gas on the 284.6 cm3 v2.3 free volume. The adopted layout has a 44 cm3 segment (LEAD 2026-10-13, Mechanical
ESTIMATE) and the free volume is 300.9 cm3 with the convergent (RC-16). This script adds those rows and the unignited
inventories now used in §7.6 and §2.8, with the same method and constants (imported, not copied):
  - decomposition energy: liquid basis for liquid, gas basis for vapour (Cantera GRI-3.0 dH at 298 K, as part D);
  - isentropic expansion of each phase to 1 atm (CoolProp), Brode energy for the chamber gas (gamma 1.25 ASSUMED);
  - TNT 4.184 MJ/kg; 6.9 kPa side-on distance R = 17.9 m kg^-1/3 x W^(1/3) (LITERATURE as recalled, TO-VERIFY).
Fragments are not computed. Order-of-magnitude input to the founders' exclusion distance only.
usage: python -I stored_energy_sup_v2p4.py DATA_V2P4_DIR
"""
from __future__ import annotations
import hashlib, json, os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import safing_relief_v2p4 as S   # noqa: E402  (rho_l, psat, expansion_energy, PA)


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def main(d):
    base_fn = os.path.join(d, 'safing_relief_v2p4.json')
    base = json.load(open(base_fn))['D_stored_energy']
    dH_gas, dH_liq = base['dH_decomposition_gas_J_kg'], base['dH_decomposition_liquid_J_kg']
    TNT, Z = base['TNT_J_kg'], base['scaled_distance_m_kg13']
    rows = {}

    def add(lab, m, T, note, liquid=True):
        if liquid:
            E_x, ml, mv = S.expansion_energy(m, T)
        else:
            E_x, ml, mv = 0.0, 0.0, m
            # saturated vapour expanded isentropically to 1 atm
            u1 = S.CP.PropsSI('U', 'T', T, 'Q', 1, S.FL); s1 = S.CP.PropsSI('S', 'T', T, 'Q', 1, S.FL)
            E_x = m * (u1 - S.CP.PropsSI('U', 'P', S.PA, 'S', s1, S.FL))
        E_dec = ml * dH_liq + mv * dH_gas
        rows[lab] = dict(m_kg=m, T_K=T, liquid_kg=ml, vapour_kg=mv, decomposition_J=E_dec, decomposition_TNT_kg=E_dec / TNT,
                         R_6p9kPa_m_decomposition=Z * (E_dec / TNT) ** (1 / 3), expansion_J=E_x, expansion_TNT_kg=E_x / TNT,
                         R_6p9kPa_m_expansion=Z * (E_x / TNT) ** (1 / 3), note=note)

    T20, TA1 = 293.15, 286.7
    V44 = 44.0e-6
    add('segment_44cm3_liquid_20C', V44 * S.rho_l(T20), T20, 'valve-to-seat segment liquid-full, 20 C (LEAD layout, Mechanical ESTIMATE volume)')
    add('segment_44cm3_liquid_A1_relight_state', V44 * S.rho_l(TA1), TA1, 'same at the A1 relight state 286.7 K')
    add('segment_44cm3_vapour_20C', V44 * S.CP.PropsSI('D', 'T', T20, 'Q', 1, S.FL), T20, 'segment vapour-full, 20 C', liquid=False)
    for lab, m, note in (('stand_allowable_13p84g', 13.84e-3, 'stand allowable, aft DN32 disc, rounded entrance (§7.6)'),
                         ('flight_inventory_accepted_26p6g', 26.6e-3, 'flight unignited inventory accepted by the lead'),
                         ('wide_window_1p05s_liquid_24C_40p0g', 40.0e-3, 'W 1.05 s, liquid line at the 24 C interlock (§2.8)'),
                         ('prep_path_0p88s_bleed_24C_41p4g', 41.4e-3, 'prep path W 0.88 s with the PREPRESS bleed, 24 C (§2.8)')):
        add(lab, m, T20, note + '; liquid at 20 C')
    Vc = 300.9e-6
    Eb = (45e5 - S.PA) * Vc / (1.25 - 1.0)
    rows['chamber_gas_at_MEOP_Brode_300p9cm3'] = dict(V_m3=Vc, P_Pa=45e5, gamma=1.25, expansion_J=Eb, expansion_TNT_kg=Eb / TNT,
                                                      R_6p9kPa_m_expansion=Z * (Eb / TNT) ** (1 / 3),
                                                      note='supersedes the 284.6 cm3 row of safing_relief_v2p4 part D (RC-16)')
    res = dict(version='v2.4', date='2026-10-13', script=os.path.basename(__file__),
               inputs={os.path.basename(base_fn): sha16(base_fn)},
               constants=dict(dH_decomposition_gas_J_kg=dH_gas, dH_decomposition_liquid_J_kg=dH_liq, TNT_J_kg=TNT, scaled_distance_m_kg13=Z),
               rows=rows,
               tag='DERIVED (same method as safing_relief_v2p4 part D); scaled distance LITERATURE as recalled, TO-VERIFY; '
                   'FRAGMENTS NOT COMPUTED; order of magnitude for the founders, not an exclusion distance')
    fn = os.path.join(d, 'stored_energy_sup_v2p4.json')
    json.dump(res, open(fn, 'w'), indent=1, default=float)
    for k, v in rows.items():
        print(f"{k:42s} m {v.get('m_kg', float('nan'))*1e3:7.2f} g  E_dec {v.get('decomposition_J', float('nan'))/1e3:8.2f} kJ  "
              f"TNT {v.get('decomposition_TNT_kg', float('nan'))*1e3:7.2f} g  R_dec {v.get('R_6p9kPa_m_decomposition', float('nan')):5.2f} m  "
              f"E_x {v['expansion_J']/1e3:7.3f} kJ  R_x {v['R_6p9kPa_m_expansion']:5.2f} m")
    print('wrote', fn, sha16(fn))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/work/combustion/data/v2/v2p4')
