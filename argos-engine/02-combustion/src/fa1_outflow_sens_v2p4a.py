"""Combustion v2.4a (REV-COMB-2 R2-11 note): sensitivity of the FA-1 peak to the frozen-gamma throat outflow.
The construct vents through the throat with frozen gamma; equilibrium flow would vent more slowly (REV-COMB-2: c* 1511
frozen against 1569 m/s equilibrium, about 4 %). First-order emulation: scale the throat area used by the network
(hard_start_multivolume_v2p4.AT) by 1511/1569 = 0.963, and by 0.92 as an allowance for more dissociation at O/F 4.
Runs only the governing cases of fa1_envelope_v2p4a (same code path; the reference run must reproduce the published
peaks to 1e-6 bar). SIM on the ASSUMED construct.
usage: python -I fa1_outflow_sens_v2p4a.py DATA_V2P4_DIR FA1_JSON OUT_JSON
"""
import hashlib, json, os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fa1_envelope_v2p4a as FE
LL, HS, MV = FE.LL, FE.HS, FE.MV
d, fa1, out = sys.argv[1:4]
h16 = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
assert h16(fa1) == '64b328150025fa1e'
assert h16(os.path.join(HERE, 'fa1_envelope_v2p4a.py')) == 'a6b71cb487c9642e'
for f, h in FE.EXPECT_DATA.items():
    assert h16(os.path.join(d, f)) == h, f
PUB = json.load(open(fa1))['cases']
J = json.load(open(os.path.join(d, 'hard_start_v2p4.json')))
cold = J['cold_flow_at_ignition_lift']['v']['A1_relight|0.125']; L = J['ignition_lifts']['v']['A1_relight|0.125']
P1, T1, P2 = L['P_tank_Pa'], L['T_tank_K'], cold['P2_Pa']
r_inj = HS.mdot_cold(LL.H_IGN, P1, T1, P2)
x_liq = cold['liquid_flow_kg_s'] / cold['mdot_cold_kg_s']
tl = LL.t_lift()
V3 = MV.volumes(0.0499, FE.D_PORT); Vs = sum(V3)
m_vap = cold['vapour_in_chamber_g']['reviewer_300.9cm3'] * 1e-3 * Vs / 300.9e-6
m_inv = LL.admitted(P1, T1, P2, tl + FE.IG)[0]
def fast(tres):
    m_s = r_inj * x_liq * tres; m_f = min(m_vap + m_s, m_inv)
    sp = [(m_vap * V3[0] / Vs + m_s) / (m_vap + m_s), m_vap * V3[1] / Vs / (m_vap + m_s), m_vap * V3[2] / Vs / (m_vap + m_s)]
    return m_f, sp
AT0 = MV.AT
CASES = [('vapour_once', 0.05, 'rounded_Cd1.0', 1.0), ('vapour_once', 0.05, 'sharp_Cd0.65', 0.65), ('as_written', 1.0, 'sharp_Cd0.65', 0.65)]
res = dict(version='v2.4a', date='2026-10-13', script='02-combustion/src/fa1_outflow_sens_v2p4a.py',
           inputs={'fa1_envelope_v2p4a.json': '64b328150025fa1e', 'fa1_envelope_v2p4a.py': 'a6b71cb487c9642e'},
           method='network throat area scaled (MV.AT x s); s 1.0 reproduces the published case', rows={})
for OF in (4.0, 8.0):
    prod = HS.products('comb', T1, OF=OF); mpk = prod['mass_per_kg_N2O']
    for lab_i, fi, lab_e, cd in CASES:
        for tf in (1e-3, 3e-3):
            key = f'{lab_i}|{lab_e}|OF{OF:g}|tf{tf*1e3:.0f}ms|tres0.06|pool_q2.0'
            row = {}
            for s in (1.0, 1511.0 / 1569.0, 0.92):
                MV.AT = AT0 * s
                lt = LL.Light(prod, FE.D_PORT, cd, fi * P2)
                m_f, sp = fast(0.06)
                m_pool = max(m_inv - m_f, 0.0) * 1.0
                t, P, _ = lt.run(r_inj * mpk, m_f * mpk, sp, tf, m_pool * mpk, 2.0e6 * mpk)
                mt, _ = FE.metrics(t, P, P2, prod, AT0)
                row[f's{s:.3f}'] = dict(peak_head_bar=round(mt['peak_head_bar'], 3), peak_aft_bar=round(mt['peak_aft_bar'], 3),
                                        above45_head_total_ms=round(mt['above45_head_total_ms'], 2),
                                        above67p5_head_total_ms=round(mt['above67p5_head_total_ms'], 2),
                                        impulse_head_bar_ms=round(mt['impulse_above_P0_25ms_head_bar_ms'], 1))
                if s == 1.0:
                    assert abs(mt['peak_head_bar'] - PUB[key]['peak_head_bar']) < 1e-6, (key, mt['peak_head_bar'], PUB[key]['peak_head_bar'])
            MV.AT = AT0
            for s in ('s0.963', 's0.920'):
                row[s]['peak_ratio_to_s1'] = round(row[s]['peak_head_bar'] / row['s1.000']['peak_head_bar'], 4)
            res['rows'][key] = row
            print(key, {k: (v['peak_head_bar'], v['above45_head_total_ms'], v['above67p5_head_total_ms'], v.get('peak_ratio_to_s1')) for k, v in row.items()}, flush=True)
res['tags'] = 'SIM on the ASSUMED construct; the area scaling is a first-order emulation of equilibrium outflow (ASSUMED), not an equilibrium nozzle model'
json.dump(res, open(out, 'w'), indent=1)
