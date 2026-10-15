"""Tank-side trades (Combustion v2, brief task 2.3-2.4): N2 supercharge options and propellant settling for relight.

Supercharge options evaluated on the DC-A1 tank (2.059 L, 1.30 kg N2O, gnc.json v1) with the equilibrium model
(tank.EquilibriumTank; N2 pad = ideal gas sharing the ullage at the common temperature, insoluble - ASSUMED; N2
solubility in liquid N2O is NOT negligible in reality and degasses in the injector -> flagged), draining at the DC-A1
oxidiser flow history from the q1d run:
  SP0  self-pressurised, 20 C (baseline)                       SP1 self-pressurised, heated to 25 C / 28 C
  SP2  N2 pad topped to 60 bar at fill (blow-down supercharge)  SP3 regulated N2 at 55 bar from an HPA bottle
Settling: from the DC acceleration histories (a_axial_specific, + = toward the nose acting on the vehicle -> liquid
pushed aft), Bond number Bo = rho_l a R^2 / sigma, settling time ~ sqrt(2 L_free / a) and the liquid column height vs
the outlet; relight-window statistics.
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from tank import EquilibriumTank
import CoolProp.CoolProp as CP

INP = os.path.join(HERE, '..', 'inputs', 'snap_20261012')
R_N2 = 296.8


def supercharge(outdir, dcfile):
    r = pd.read_csv(dcfile)
    t = r.t.values; mdot = r.mox.values
    V = 2.059e-3; m = 1.3
    cases = {}
    def run(name, tk, regulated=None):
        P = []; Tt = []
        for k in range(1, len(t)):
            dt = t[k] - t[k - 1]
            if regulated and tk.liquid:
                tk.step(mdot[k], dt)
                # regulator keeps ullage at P_reg by adding N2 (ideal gas) at tank temperature
                need = regulated - tk.Pv
                tk.m_n2 = max(need, 0.0) * tk.V_ull / (R_N2 * tk.T)
                tk.update_state()
            elif tk.liquid:
                tk.step(mdot[k], dt)
            P.append(tk.P); Tt.append(tk.T)
        return np.array(P), np.array(Tt)
    tk = EquilibriumTank(V, m, 293.15); P0, T0 = run('SP0', tk)
    cases['SP0_self_20C'] = dict(P=P0, note='baseline')
    for TC in (298.15, 301.15):
        mm = m
        # keep the same fill rule at the higher temperature (liquid fraction <= 0.85 at 25 C -> fixed V, same m)
        tk = EquilibriumTank(V, mm, TC); P1, _ = run('SP1', tk)
        cases[f'SP1_self_{TC-273.15:.0f}C'] = dict(P=P1, note='tank heated before launch (ground heater, removed at liftoff)')
    # N2 pad: N2 added at 20 C until total P = 60 bar
    tk = EquilibriumTank(V, m, 293.15)
    pv = tk.Pv; Vu = tk.V_ull
    mN2 = (60e5 - pv) * Vu / (R_N2 * 293.15)
    tk = EquilibriumTank(V, m, 293.15, m_n2=mN2); P2, _ = run('SP2', tk)
    cases['SP2_N2pad_60bar'] = dict(P=P2, note=f'N2 pad {mN2*1e3:.1f} g, insoluble ideal-gas assumption')
    tk = EquilibriumTank(V, m, 293.15); P3, _ = run('SP3', tk, regulated=55e5)
    n2_used = tk.m_n2
    cases['SP3_regulated_55bar'] = dict(P=P3, note=f'N2 consumed {n2_used*1e3:.1f} g (insoluble assumption)')
    # HPA sizing for SP3: N2 needed at end = n2_used; bottle 0.2 L (12 ci) at 300 bar -> mass
    rho_hpa = CP.PropsSI('D', 'P', 300e5, 'T', 293.15, 'Nitrogen')
    rho_min = CP.PropsSI('D', 'P', 60e5, 'T', 250.0, 'Nitrogen')
    V_bottle_needed = n2_used / (rho_hpa - rho_min)
    out = {}
    tt = t[1:]
    i_relight = np.argmax(r.state.values[1:] == 'start') if (r.state == 'start').any() else None
    for k, v in cases.items():
        P = v['P']
        out[k] = dict(P_start_bar=round(P[0] / 1e5, 2), P_at_MECO_bar=round(float(np.interp(2.47, tt, P)) / 1e5, 2),
                      P_at_relight_bar=round(float(np.interp(24.64, tt, P)) / 1e5, 2),
                      P_end_bar=round(P[-1] / 1e5, 2), note=v['note'])
    out['SP3_regulated_55bar']['HPA_bottle_volume_needed_L_at_300bar'] = round(V_bottle_needed * 1e3, 3)
    json.dump(out, open(os.path.join(outdir, 'supercharge_trade_v2.json'), 'w'), indent=1)
    pd.DataFrame({'t': tt, **{k: v['P'] for k, v in cases.items()}}).iloc[::10].to_csv(
        os.path.join(outdir, 'supercharge_trade_P_v2.csv'), index=False, float_format='%.6g')
    return out


def settling(outdir, inp=INP, names=('DC-A1_full_flight_drogue_300m_v1', 'DC-A2_full_flight_freefall_300m_v1'),
             outname='settling_v2.json'):
    """inp/names/outname added 2026-10-12 (v2 working-copy preview); defaults reproduce settling_v2.json (gnc.json v1)."""
    rho_l = CP.PropsSI('D', 'T', 288.15, 'Q', 0, 'NitrousOxide'); sigma = CP.PropsSI('I', 'T', 288.15, 'Q', 0, 'NitrousOxide')
    R = 0.0476   # tank inner radius [m] (mechanical.json v1: 101.6 x 3.175 tube)
    res = {}
    for name in names:
        d = pd.read_csv(os.path.join(inp, name + '.csv'), comment='#')
        a = d.a_axial_specific_mps2.values; t = d.t_s.values; Fc = d.F_cmd_N.values
        off = (Fc <= 0)
        i_meco = int(np.argmax(off))
        # last off sample before relight = end of the FIRST off window (v2 working-copy files also have an off window
        # after touchdown; the v1 rule 'last off sample in the file' picked that one: fixed 2026-10-12, v1 unchanged)
        on_after = np.where(~off[i_meco:])[0]
        i_rel = i_meco + int(on_after[0]) - 1 if len(on_after) else len(t) - 1
        seg = slice(i_meco, i_rel + 1)
        aa = a[seg]; ts = t[seg]
        neg = aa < 0
        t_neg = float(np.sum(neg) * 0.01)
        # longest continuous positive (settling) interval ending at relight
        k = len(aa) - 1; dur = 0.0
        while k >= 0 and aa[k] > 0.05 * 9.80665:
            dur += 0.01; k -= 1
        a_rel = float(aa[-50:].mean())
        Bo = rho_l * max(a_rel, 1e-6) * R ** 2 / sigma
        L_free = 0.3
        t_settle = math.sqrt(2 * L_free / max(a_rel, 1e-6))
        res[name] = dict(coast_s=round(float(ts[-1] - ts[0]), 2), a_min_mps2=round(float(aa.min()), 3),
                         time_negative_s=round(t_neg, 2), settled_interval_before_relight_s=round(dur, 2),
                         a_mean_last_0p5s_mps2=round(a_rel, 3), Bond=round(Bo, 0), t_settle_estimate_s=round(t_settle, 2),
                         rho_l=rho_l, sigma_N_m=sigma)
    json.dump(res, open(os.path.join(outdir, outname), 'w'), indent=1)
    return res


if __name__ == '__main__':
    out = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == '--settling-v2wip':
        # python tank_trades.py OUTDIR --settling-v2wip SNAPDIR : GNC duty_cycles v2 working copy (PREVIEW)
        print(json.dumps(settling(out, sys.argv[3], ('DC-A1_full_flight_drogue_fins_300m_v2', 'DC-A2_full_flight_freefall_300m_v2'),
                                  'settling_v2wip_preview.json'), indent=1))
    else:
        print(json.dumps(settling(out), indent=1))
        print(json.dumps(supercharge(out, sys.argv[2]), indent=1))
