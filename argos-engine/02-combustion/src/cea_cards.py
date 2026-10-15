"""Fuel thermochemical cards for N2O hybrid analysis (Combustion, v1, 2026-10-11).

Every enthalpy of formation below is DERIVED from a cited primary quantity (monomer
enthalpy of formation + enthalpy of polymerisation, or a bomb-calorimetry heat of
combustion). Nothing is invented; where sources disagree, the spread is kept as a range
and its c* effect is computed by thermo_tables.py (sensitivity table).

Constants (LITERATURE, CODATA/NIST standard values, 298.15 K):
  hf CO2(g) = -393.52 kJ/mol, hf H2O(l) = -285.83 kJ/mol
  (same reference values used by Wilkey, Thibaudeau & Whitmore, Appl. Sci. 16(16) 8063, 2026, Eq. 15)

ABS:
  * Composition range (molar, LITERATURE): acrylonitrile 21-27 %, butadiene 12-25 %, styrene 54-63 %
    as quoted by Walker (USU MS thesis 2015, Sec. 1.4) and Wilkey et al. 2026 (Sec. 1).
  * Reduced formula per mole of monomer units (Wilkey et al. 2026, Eqs. 6-8):
        C = 3 xA + 4 xB + 8 xS ; H = 3 xA + 6 xB + 8 xS ; N = xA
  * Polymer enthalpies of formation (solid, per repeat unit) built from monomer liquid hf
    (NIST Chemistry WebBook) + enthalpy of polymerisation dHp(lc) (Polymer Handbook, Dainton-Ivin
    compilation). Values recalled from those references, NOT re-verified online in this session
    -> tag LITERATURE-UNVERIFIED, uncertainty +/-5 kJ/mol each:
        styrene(l) +103.8 ; dHp -69.9  -> PS  +33.9 kJ/mol
        1,3-butadiene(l) +88.5 ; dHp -72.8 -> PB +15.7 kJ/mol
        acrylonitrile(l) +147.2 ; dHp -76.5 -> PAN +70.7 kJ/mol
  * Bomb calorimetry: Walters, Hackett & Lyon, "Heats of Combustion of High Temperature Polymers",
    FAA W.J. Hughes Technical Center (fire.tc.faa.gov/pdf/chemlab/hoc.pdf), Table 1:
        ABS (C15H17N) Qc,gross = 39.84 kJ/g (single test); group-contribution 39.43 kJ/g
        PET (C10H8O4) Qc,gross = 24.13 +/- 0.39 kJ/g; literature value quoted there 22.2 kJ/g
  * Lead v0 card: C15H17N, hf = +62.6 kJ/mol (ENGINE-BASELINE v0, ASSUMED, to verify).

PETG:
  * PETG = PET in which part of ethylene glycol is replaced by 1,4-cyclohexanedimethanol (CHDM).
    Repeat units: PET C10H8O4 (192.17 g/mol); PCT C16H18O4 (274.31 g/mol).
    CHDM fraction of the diol: ASSUMED 0.31 (range 0.25-0.35, typical copolyester grades; vendor
    composition is not published for most filaments -> UNVERIFIED).
  * hf(PET): DERIVED three ways (spread kept):
        (i) terephthalic acid(s) -816.1 + ethylene glycol(l) -460.0 - 2 H2O(l) (-285.83) with a
            near-zero esterification enthalpy -> -704 kJ/mol (LITERATURE-UNVERIFIED inputs, NIST)
        (ii) FAA bomb Qc 24.13 kJ/g -> -441 kJ/mol ; (iii) Qc 22.2 kJ/g -> -812 kJ/mol
  * hf(PCT unit) = hf(PET) + increment for -C6H10- (cyclohexylene) ~ -120 +/- 40 kJ/mol
    (group-additivity estimate, DERIVED, UNVERIFIED).

Paraffin (for the optional paraffin-ABS composite): C32H66 surrogate, hf = -968 kJ/mol
  (n-dotriacontane-class solid; LITERATURE-UNVERIFIED, range -1000..-900). Composite cards mix by mass.
"""
from __future__ import annotations
import math

HF_CO2 = -393.52     # kJ/mol
HF_H2O_L = -285.83   # kJ/mol
R_KJ = 8.314462618e-3
T0 = 298.15
M_C, M_H, M_N, M_O = 12.011, 1.008, 14.007, 15.999

HF_PS, HF_PB, HF_PAN = 33.9, 15.7, 70.7          # kJ/mol per repeat unit, LITERATURE-UNVERIFIED +/-5
HF_PET_NOM, HF_PET_LO, HF_PET_HI = -704.0, -812.0, -441.0
DHF_CYCLOHEXYLENE = -120.0                        # kJ/mol, DERIVED estimate +/-40
HF_PARAFFIN = -968.0                              # kJ/mol C32H66, LITERATURE-UNVERIFIED


def molar_mass(C=0.0, H=0.0, N=0.0, O=0.0):
    return C * M_C + H * M_H + N * M_N + O * M_O


def hf_from_gross_heat_of_combustion(Qc_kJ_per_g, C, H, N=0.0, O=0.0):
    """Enthalpy of formation (kJ/mol formula) from a bomb (constant-volume) gross heat of
    combustion. Corrects dU -> dH with the gas mole change (products: CO2(g), H2O(l), N2(g))."""
    M = molar_mass(C, H, N, O)
    dU = -Qc_kJ_per_g * M
    n_O2 = C + H / 4.0 - O / 2.0
    dn_gas = (C + N / 2.0) - n_O2
    dH = dU + dn_gas * R_KJ * T0
    return C * HF_CO2 + (H / 2.0) * HF_H2O_L - dH


def abs_formula(xA, xB, xS):
    s = xA + xB + xS
    xA, xB, xS = xA / s, xB / s, xS / s
    C = 3 * xA + 4 * xB + 8 * xS
    H = 3 * xA + 6 * xB + 8 * xS
    N = xA
    hf = xA * HF_PAN + xB * HF_PB + xS * HF_PS
    return C, H, N, hf


def petg_formula(chi=0.31, hf_pet=HF_PET_NOM, dhf_chx=DHF_CYCLOHEXYLENE):
    C = 10 + 6 * chi
    H = 8 + 10 * chi
    O = 4.0
    hf = hf_pet + chi * dhf_chx
    return C, H, O, hf


def card(name, C, H, hf_kJ_mol, N=0.0, O=0.0, rho_gcc=1.0, wt=100.0):
    parts = f"C {C:.5f} H {H:.5f}"
    if N > 0:
        parts += f" N {N:.5f}"
    if O > 0:
        parts += f" O {O:.5f}"
    return f"fuel {name}  {parts}  wt%={wt:.2f}  h,kj/mol={hf_kJ_mol:.3f}  t(k)=298.15  rho={rho_gcc:.3f}\n"


# Design cards (v1). Typical-ABS composition = mid-points of the literature molar ranges, renormalised.
ABS_TYP = dict(xA=0.24, xB=0.185, xS=0.575)


def build_cards():
    """Return {card_name: (card_text, meta)}; register with rocketcea.add_new_fuel by caller."""
    cards = {}
    C, H, N, hf = abs_formula(**ABS_TYP)
    M = molar_mass(C, H, N)
    cards['ABS_TYP_v1'] = (card('ABS_TYP', C, H, hf, N=N, rho_gcc=1.04),
                           dict(C=C, H=H, N=N, hf_kJ_mol=hf, M=M, hf_kJ_kg=hf / M * 1e3,
                                tag='DERIVED from LITERATURE monomer ranges + polymer hf (see module doc)'))
    # Lead v0 card
    cards['ABS_LEAD_v0'] = (card('ABS_LEAD', 15, 17, 62.6, N=1, rho_gcc=1.05),
                            dict(C=15, H=17, N=1, hf_kJ_mol=62.6, M=molar_mass(15, 17, 1),
                                 hf_kJ_kg=62.6 / molar_mass(15, 17, 1) * 1e3, tag='ASSUMED lead v0'))
    # FAA bomb calorimetry, C15H17N basis
    hf_faa = hf_from_gross_heat_of_combustion(39.84, 15, 17, 1)
    hf_gc = hf_from_gross_heat_of_combustion(39.43, 15, 17, 1)
    for nm, h, tg in [('ABS_FAA_v1', hf_faa, 'DERIVED from FAA bomb Qc 39.84 kJ/g'),
                      ('ABS_FAAGC_v1', hf_gc, 'DERIVED from FAA group-contribution Qc 39.43 kJ/g')]:
        cards[nm] = (card(nm.split('_v')[0], 15, 17, h, N=1, rho_gcc=1.04),
                     dict(C=15, H=17, N=1, hf_kJ_mol=h, M=molar_mass(15, 17, 1),
                          hf_kJ_kg=h / molar_mass(15, 17, 1) * 1e3, tag=tg))
    # Composition extremes (styrene-rich / butadiene-rich / acrylonitrile-rich corners of the range)
    for nm, comp in [('ABS_SRICH_v1', dict(xA=0.21, xB=0.12, xS=0.63)),
                     ('ABS_BRICH_v1', dict(xA=0.21, xB=0.25, xS=0.54)),
                     ('ABS_ARICH_v1', dict(xA=0.27, xB=0.12, xS=0.61)),
                     ('ABS_USU5043_v1', dict(xA=0.43, xB=0.50, xS=0.07))]:
        C, H, N, hf = abs_formula(**comp)
        M = molar_mass(C, H, N)
        cards[nm] = (card(nm.split('_v')[0], C, H, hf, N=N, rho_gcc=1.04),
                     dict(C=C, H=H, N=N, hf_kJ_mol=hf, M=M, hf_kJ_kg=hf / M * 1e3, comp=comp,
                          tag='DERIVED composition corner (USU5043 = 50:43:7 B:A:S quoted on the withdrawn '
                              'Whitmore-Petersen-Eilers USU record)' if 'USU' in nm else 'DERIVED composition corner'))
    # PETG nominal and extremes
    for nm, hpet, chi in [('PETG_NOM_v1', HF_PET_NOM, 0.31), ('PETG_LO_v1', HF_PET_LO, 0.31),
                          ('PETG_HI_v1', HF_PET_HI, 0.31), ('PET_LEAD_v0', -476.0, 0.0)]:
        C, H, O, hf = petg_formula(chi, hpet)
        M = molar_mass(C, H, 0, O)
        cards[nm] = (card(nm.split('_v')[0], C, H, hf, O=O, rho_gcc=1.27),
                     dict(C=C, H=H, O=O, hf_kJ_mol=hf, M=M, hf_kJ_kg=hf / M * 1e3,
                          tag='ASSUMED lead v0 (PET only)' if 'LEAD' in nm else
                          f'DERIVED (hf_PET={hpet}, CHDM fraction {chi})'))
    # Paraffin and 50/50 paraffin-ABS composite by mass (two-line card)
    Mp = molar_mass(32, 66)
    cards['PARAFFIN_v1'] = (card('PARAFFIN', 32, 66, HF_PARAFFIN, rho_gcc=0.92),
                            dict(C=32, H=66, hf_kJ_mol=HF_PARAFFIN, M=Mp, hf_kJ_kg=HF_PARAFFIN / Mp * 1e3,
                                 tag='LITERATURE-UNVERIFIED C32H66 surrogate'))
    C, H, N, hf = abs_formula(**ABS_TYP)
    comp_card = (card('PARW', 32, 66, HF_PARAFFIN, rho_gcc=0.92, wt=50.0) +
                 card('ABSW', C, H, hf, N=N, rho_gcc=1.04, wt=50.0))
    cards['PARABS50_v1'] = (comp_card, dict(tag='DERIVED 50/50 wt paraffin-ABS (USU McCulley et al. 2012 concept)'))
    return cards


_REGISTERED = set()


def register_all():
    from rocketcea.cea_obj import add_new_fuel
    cards = build_cards()
    for k, (txt, _) in cards.items():
        if k not in _REGISTERED:
            add_new_fuel(k, txt)
            _REGISTERED.add(k)
    return cards


if __name__ == '__main__':
    for k, (txt, meta) in build_cards().items():
        print(k, '|', txt.strip().replace('\n', ' || '), '|', {kk: (round(v, 3) if isinstance(v, float) else v) for kk, v in meta.items() if kk != 'tag'})
