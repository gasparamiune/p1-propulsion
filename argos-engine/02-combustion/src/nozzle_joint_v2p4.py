"""Nozzle insert shoulder joint (S14, NZ-03): leak consequence and requirement set for a replacement joint
(Combustion v2.4; coordinator relay 2026-10-13 item 4: "NZ-03 mica/vermiculite gasket reaches 1595 C against a 900 C class,
so it FAILS. Propose a nozzle joint or material that survives that temperature in N2O/ABS exhaust, and agree it with Mechanical").

Inputs (read, not copied): Mechanical seal_table_v1 (S14 row), the FE envelope of DC-B1v3p99_tg711_hi_SS316L_L2.5_v11pre36IN
(NZ-01/02/03, TC-09 maxima), CAD config (spigot 30 h9, lip bore 30.5 H11, insert OD 44 h9 with 4 axial vent grooves 1.0 x 0.5,
sleeve 3 mm, gasket 1 mm, lip 6 mm), combustion.json v2.3 (throat, 100 % mass flow, T0).
Leak path if the shoulder seal fails: chamber -> 4 vent grooves on the insert OD (the annulus is at Pc by design) -> gasket face
-> spigot/lip radial clearance -> ambient at the exit plane. Choked flow through the narrowest section (the grooves) scales with
area at the same Pc as the throat. Heating of the 316L lip bore by the leak jet: deposited fraction 5-20 % (ASSUMED bracket).
usage: python -I nozzle_joint_v2p4.py SEAL_TABLE_JSON FE_SUMMARY_JSON COMBUSTION_JSON OUT_JSON
"""
from __future__ import annotations
import hashlib, json, math, os, sys
sys.dont_write_bytecode = True


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def main(seal_f, fe_f, comb_f, out_f):
    ST = json.load(open(seal_f)); FE = json.load(open(fe_f)); CO = json.load(open(comb_f))
    s14 = [r for r in ST['table'] if r['id'] == 'S14'][0]
    env = FE['envelope']
    # geometry (CAD config.py v3.2-v3.4 values; DERIVED in Mechanical's config)
    d_sp_max, d_sp_min = 30.000, 30.000 - 0.052          # 30 h9
    d_lb_min, d_lb_max = 30.500, 30.500 + 0.160          # 30.5 H11
    c_min, c_max = (d_lb_min - d_sp_max) / 2, (d_lb_max - d_sp_min) / 2
    A_gap_min = math.pi * (d_lb_min + d_sp_max) / 2 * c_min
    A_gap_max = math.pi * (d_lb_max + d_sp_min) / 2 * c_max
    A_grooves = 4 * 1.0 * 0.5
    Dt = 2 * CO['gas_path']['nozzle']['throat_radius_m']['v'] * 1e3 if 'gas_path' in CO and 'nozzle' in CO['gas_path'] and 'throat_radius_m' in CO['gas_path']['nozzle'] else 13.724
    At = math.pi / 4 * Dt ** 2
    mdot = CO['operating_points']['max_thrust']['mdot_total_kg_s']['v']
    Cd_t, Cd_g = 0.98, (0.6, 0.8)
    leak_frac = [c * A_grooves / (Cd_t * At) for c in Cd_g]
    m_leak = [f * mdot for f in leak_frac]
    T0, Tw, cp_f = 2852.4, 900.0, 2000.0                  # delivered T0 (combustion.json v2.3), wall ~900 K, frozen cp ASSUMED
    H_leak = [m * cp_f * (T0 - Tw) for m in m_leak]
    A_bore = math.pi * d_lb_min * 6.0                     # lip bore wetted area, mm2 (6 mm lip)
    rho_c = 8000 * 500.0                                  # 316L J/m3K (ASSUMED room-temperature class)
    t_melt = {}
    for frac in (0.05, 0.20):
        for H in H_leak:
            q = frac * H / (A_bore * 1e-6)
            t_melt[f'dep{frac:.2f}_H{H/1e3:.1f}kW'] = dict(q_MW_m2=q / 1e6, t_1mm_layer_to_1400C_s=rho_c * 1e-3 * (1400 - 250) / q)
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/nozzle_joint_v2p4.py',
               inputs={os.path.basename(seal_f): sha16(seal_f), os.path.basename(fe_f): sha16(fe_f), os.path.basename(comb_f): sha16(comb_f)},
               S14=dict(item=s14['item'], rating_cont_C=s14['rating_cont_C'], T_max_all_runs_C=s14['T_max_all_runs_C'], margin_K=s14['margin_to_cont_K'],
                        per_run_inburn_postburn=s14['per_run_inburn_postburn_s175']),
               FE_B1p99=dict(NZ01=env['ENG-NZ-01'], NZ02=env['ENG-NZ-02'], NZ03=env['ENG-NZ-03'], TC09=env['ENG-TC-09']),
               leak_path=dict(grooves_mm2=A_grooves, grooves_over_At=A_grooves / At, spigot_lip_radial_clearance_mm=[c_min, c_max],
                              spigot_lip_gap_mm2=[A_gap_min, A_gap_max], gap_over_At=[A_gap_min / At, A_gap_max / At], At_mm2=At,
                              leak_fraction_of_engine_flow=leak_frac, leak_kg_s_at_100pct=m_leak, enthalpy_flow_W=H_leak,
                              lip_bore_area_mm2=A_bore, lip_heating=t_melt),
               requirement=dict(
                   hot_layer=dict(T_service_C='>= 1700 (FE 1595 + 100 K)', atmosphere='N2O/ABS exhaust: CO, H2, H2O, CO2, N2; free O2 up to 12 % at O/F 8-11.6 (§4.6)',
                                  bearing_MPa='10.6 at BN 63.1 bar; strength >= 2x at temperature', k_through_W_mK='<= ~1 (keeps the lip at or below the present 250 C in-burn)',
                                  compatibility='no SiO2 in contact with graphite above ~1400-1500 C (SiO2 + 3C -> SiC + 2CO, as recalled, TO-VERIFY)',
                                  sealing='none required'),
                   seal_layer=dict(location='lip face (cold side)', T_service='in-burn face temperature from the FE re-run + 100 K; today 250.6 C in-burn, 653.5 C soak at the lip (FE)',
                                   tightness='gas-tight at MEOP 45 bar; seated by the insert at BN 63.1 bar', life='replaced at every insert change (one per flight)')),
               candidates=[
                   dict(id='J1 (preferred)', hot_layer='carbon-phenolic flange 2.0 mm, integral with NZ-02 (top-hat sleeve) or a separate washer',
                        seal='0.5 mm flexible graphite ring (oxidation-inhibited grade) or the present 1 mm mica/vermiculite ring at the lip face',
                        why='same ablative family as NZ-02; carbon char is compatible with graphite; low virgin k; tolerates the 1593 C hot face by charring',
                        risks='char depth and shrinkage (preload is pressure-energised); pyrolysis gas into the annulus (vents to the chamber via the grooves)',
                        tags='LITERATURE as recalled, TO-VERIFY (char rate, k, char strength)'),
                   dict(id='J2', hot_layer='dense fully stabilised zirconia washer 1.5-2.0 mm, lapped faces',
                        seal='0.5 mm flexible graphite ring at the lip face', why='survives > 2000 C, inert in oxidising gas, strong in compression',
                        risks='thermal-shock cracking (acceptable only while confined and in compression); k ~2-2.5 W/mK raises the seal-face and lip temperature: FE to show',
                        tags='LITERATURE as recalled, TO-VERIFY'),
                   dict(id='J3', hot_layer='J1 or J2', seal='metal C-ring (Inconel 718 / X-750, silver plated) in a lip groove', why='seal independent of oxidation',
                        risks='groove in a 6 mm lip; separate bearing path; rated ~700 C class as recalled', tags='TO-VERIFY'),
                   dict(id='rejected', items=['flexible graphite on the hot face (oxidises in O2-bearing gas at 1600 C)',
                                              'silica- or glass-bearing layers against graphite above ~1500 C',
                                              'alumina-silica or alumina fibre paper as the bearing layer (crushes far below 10.6 MPa, as recalled)'])],
               side_finding=dict(NZ02='NZ-02 peaks at 1551 C (r 22, soak). A glass-phenolic sleeve would melt its glass (E-glass softens far below that, as recalled); '
                                      'silica-phenolic reacts with the graphite above ~1500 C. Carbon-phenolic is the conventional backing for graphite inserts. Mechanical to confirm the NZ-02 material in the same FE re-run.'),
               verification=['Mechanical FE re-run with the two-layer stack and contact conductances (hot-layer peak, seal-face peak in-burn and soak, lip peak)',
                             'T1: thermocouple well in the lip at r 21 (planned) plus one at the lip bore edge',
                             'pressure-decay leak check of the assembled joint with N2 at 67.5 bar before and after every firing (criterion TO-DEFINE with Mechanical)',
                             'post-test: section the hot layer (char depth or cracks), inspect the lip bore and the spigot OD for leak tracks, measure stack height loss'],
               prices='TO-QUOTE (Sønderborg DK-6400): carbon-phenolic tube/plate, zirconia washers, flexible graphite sheet, C-rings',
               tags='DERIVED arithmetic on DESIGN dimensions; material data LITERATURE as recalled, TO-VERIFY; proposal pending agreement with Mechanical via the lead')
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    lp = out['leak_path']
    print('At %.2f mm2; grooves %.2f mm2 (%.2f %% At); gap %.1f-%.1f mm2 (%.1f-%.1f %% At); radial clearance %.3f-%.3f mm' % (
        At, A_grooves, 100 * A_grooves / At, A_gap_min, A_gap_max, 100 * A_gap_min / At, 100 * A_gap_max / At, c_min, c_max))
    print('leak %.2f-%.2f %% of engine flow = %.2f-%.2f g/s at 100 %%; enthalpy %.1f-%.1f kW' % (
        100 * leak_frac[0], 100 * leak_frac[1], 1e3 * m_leak[0], 1e3 * m_leak[1], H_leak[0] / 1e3, H_leak[1] / 1e3))
    for k, v in t_melt.items():
        print(k, '%.2f MW/m2, 1 mm layer to 1400 C in %.1f s' % (v['q_MW_m2'], v['t_1mm_layer_to_1400C_s']))
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:5])
