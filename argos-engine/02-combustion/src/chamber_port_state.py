"""Chamber state and port-flame figure (Combustion v2; 05-plume-cfd deliverable 3, item 1).

What is computed (traceable):
  * port state along the S230 grain at the initial port (D 25 mm) for the v2 operating points 100/50/20/12.5 % at
    20 C (nozzle_perf_v2.json, SIM grain_q1d v2): oxidiser flux G_ox(x), total flux G(x), regression r(x) (ASSUMED
    law r = a G_ox^0.5, a 0.0577 mm/s, band x0.6-1.5), cumulative fuel flow and the cumulative (cross-section mean)
    mixture ratio O/F(x) = mdot_ox / mdot_f(0..x), compared with the stoichiometric O/F of the ABS card;
  * chamber state at the same points from CEA (RocketCEA, ABS_TYP_v1 card, equilibrium): Tc, gamma, MW, c*, major
    species; delivered stagnation temperature eta_c*^2 Tc (eta_c* 0.92 ASSUMED).
What is schematic (labelled on the figure): the turbulent boundary-layer thickness uses the flat-plate correlation
  delta = 0.37 x Re_x^-0.2 (LITERATURE, Schlichting; the basis of Marxman's hybrid model) with an ASSUMED gas viscosity
  9e-5 Pa s and NO blowing correction; the diffusion-flame band is drawn at 0.1-0.3 delta (ASSUMED, schematic only:
  the flame position is not computed).
usage: python chamber_port_state.py DATADIR FIGDIR
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import grain_q1d as Q
from tank import EquilibriumTank
import cea_cards

MU_GAS = 9e-5           # Pa s, ASSUMED hot-gas viscosity for the schematic boundary layer
FRACS = (1.0, 0.5, 0.2, 0.125)


def of_stoich():
    C, H, N, hf = cea_cards.abs_formula(**cea_cards.ABS_TYP)
    m_f = C * 12.011 + H * 1.008 + N * 14.007
    n_o = 2 * C + 0.5 * H                       # mol O (= mol N2O) per formula unit: C -> CO2, H -> H2O
    return n_o * 44.013 / m_f


def cea_state(Pc, OF):
    from rocketcea.cea_obj import CEA_Obj
    cea_cards.register_all()
    c = CEA_Obj(oxName='N2O', fuelName='ABS_TYP_v1')
    p = Pc / 6894.757
    Tc = c.get_Tcomb(Pc=p, MR=OF) / 1.8
    cstar = c.get_Cstar(Pc=p, MR=OF) * 0.3048
    mw, gam = c.get_Chamber_MolWt_gamma(Pc=p, MR=OF, eps=2.0)
    _, mf = c.get_SpeciesMoleFractions(Pc=p, MR=OF, eps=2.0, frozen=0, frozenAtThroat=0, min_fraction=5e-3)
    X = {k.strip('*'): round(v[1], 4) for k, v in mf.items() if v[1] >= 5e-3}
    return dict(Tc_K=Tc, cstar_ideal_m_s=cstar, MW=mw, gamma=gam, X_major=dict(sorted(X.items(), key=lambda kv: -kv[1])))


def main(datadir, figdir):
    J = json.load(open(os.path.join(datadir, 'v2', 'nozzle_perf_v2.json')))
    ops = {round(o['frac'], 3): o for o in J['grains']['v2_S230_straight_L230']['ops']}
    E = Q.Engine(EquilibriumTank(3.17e-3, 2.0, 293.15))
    c = E.c
    ofst = of_stoich()
    x = E.x
    Ap = math.pi / 4 * c['D_port0'] ** 2
    prof = {}; states = {}
    for f in FRACS:
        o = ops[f]
        r, mcum = E.regression(o['mox'])
        G_ox = o['mox'] / Ap
        G = (o['mox'] + mcum) / Ap
        OFc = o['mox'] / np.maximum(mcum, 1e-12)
        x_st = float(np.interp(ofst, OFc[::-1], x[::-1])) if OFc[-1] < ofst else None
        Rex = G * (x + c['L_pre']) / MU_GAS                 # boundary layer starts at the grain head (pre-chamber ignored)
        Rex_g = G * x / MU_GAS
        delta = 0.37 * x * np.maximum(Rex_g, 1.0) ** -0.2
        prof[f] = dict(x_m=x.tolist(), G_ox=G_ox, G_total=G.tolist(), r_mm_s=(r * 1e3).tolist(), OF_cum=OFc.tolist(),
                       delta_mm=(delta * 1e3).tolist())
        st = cea_state(o['Pc'], o['OF'])
        st.update(frac=f, F_N=o['F'], Pc_bar=o['Pc'] / 1e5, OF=o['OF'], mdot_ox=o['mox'], mdot_f=o['mf'], Isp_SL_s=o['Isp'],
                  T0_delivered_K=c['eta_cstar'] ** 2 * st['Tc_K'], cstar_delivered_m_s=c['eta_cstar'] * st['cstar_ideal_m_s'],
                  G_ox_head_kg_m2s=G_ox, G_total_aft_kg_m2s=float(G[-1]), r_mean_mm_s=float(np.mean(r) * 1e3),
                  x_where_OF_cum_reaches_stoich_m=x_st, mixture_at_grain_end='fuel-rich' if o['OF'] < ofst else 'oxidiser-rich',
                  delta_aft_mm=float(delta[-1] * 1e3), delta_aft_over_R=float(delta[-1] / (c['D_port0'] / 2)))
        states[f] = st
    # ---------- figure ----------
    fig = plt.figure(figsize=(14, 9.2))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.15, 1, 1])
    ax0 = fig.add_subplot(gs[0, :])
    L_pre, L_g, L_post = c['L_pre'], c['L_grain'], c['L_post']
    Rg = c['D_grain'] / 2; Rp = c['D_port0'] / 2; Rch = c['D_ch'] / 2
    xg0 = L_pre
    # case/grain outline (half-section, mm)
    ax0.fill_between([xg0 * 1e3, (xg0 + L_g) * 1e3], Rp * 1e3, Rg * 1e3, color='#c9b18a', label='ABS grain (S230)')
    ax0.fill_between([0, (xg0 + L_g + L_post) * 1e3], Rg * 1e3, (Rch + 0.0016) * 1e3, color='0.75')
    ax0.plot([0, 0], [0, Rch * 1e3], 'k-', lw=2); ax0.text(1, Rch * 1e3 + 2, 'injector face', fontsize=7)
    d100 = np.array(prof[1.0]['delta_mm']); xm = (xg0 + x) * 1e3
    ax0.plot(xm, Rp * 1e3 - d100, 'b--', lw=1, label='turbulent BL edge, 100 % (flat-plate correlation, no blowing: SCHEMATIC)')
    ax0.fill_between(xm, Rp * 1e3 - 0.3 * d100, Rp * 1e3 - 0.1 * d100, color='tab:orange', alpha=0.8,
                     label='diffusion-flame zone (0.1-0.3 delta, ASSUMED: position NOT computed)')
    ax0.annotate('N2O (liquid/vapour spray, decomposes and vaporises in the pre-chamber)', xy=(5, 4), fontsize=7)
    ax0.annotate('post-chamber: mixing of the oxidiser-rich core with the fuel-rich wall layer', xy=((xg0 + L_g) * 1e3 + 2, 4), fontsize=7)
    ax0.set_xlim(0, (xg0 + L_g + L_post) * 1e3 + 5); ax0.set_ylim(0, Rch * 1e3 + 6)
    ax0.set_xlabel('x from the injector face [mm]'); ax0.set_ylabel('r [mm] (half-section)')
    ax0.legend(fontsize=7, loc='upper right'); ax0.set_title('(a) S230 port at ignition (D 25 mm, L 230 mm), 100 % thrust, 20 C', loc='left', fontsize=9)
    ax1 = fig.add_subplot(gs[1, 0]); ax2 = fig.add_subplot(gs[1, 1]); ax3 = fig.add_subplot(gs[2, 0]); ax4 = fig.add_subplot(gs[2, 1])
    cols = {1.0: 'tab:red', 0.5: 'tab:orange', 0.2: 'tab:green', 0.125: 'tab:blue'}
    for f in FRACS:
        p = prof[f]; xm = np.array(p['x_m']) * 1e3
        ax1.plot(xm, p['G_total'], color=cols[f], lw=1.2, label=f'{f*100:g} %: G total')
        ax1.axhline(p['G_ox'], color=cols[f], lw=0.7, ls=':')
        ax2.plot(xm, p['r_mm_s'], color=cols[f], lw=1.2, label=f'{f*100:g} %')
        ax3.semilogy(xm, p['OF_cum'], color=cols[f], lw=1.2, label=f"{f*100:g} % (exit O/F {states[f]['OF']:.2f})")
        ax4.plot(xm, p['delta_mm'], color=cols[f], lw=1.0)
    ax3.axhline(ofst, color='k', lw=0.8, ls='--'); ax3.text(3, ofst * 1.08, f'stoichiometric O/F {ofst:.2f} (ABS card)', fontsize=7)
    ax1.set_ylabel('mass flux [kg/m2/s]'); ax1.set_title('(b) total flux G(x) (solid) and oxidiser flux G_ox (dotted)', loc='left', fontsize=9)
    ax2.set_ylabel('regression rate [mm/s]'); ax2.set_title('(c) r = a G_ox^0.5 (ASSUMED law, nominal a; band x0.6-1.5)', loc='left', fontsize=9)
    ax3.set_ylabel('cumulative O/F'); ax3.set_title('(d) cross-section mean O/F along the port', loc='left', fontsize=9)
    ax4.set_ylabel('delta [mm]'); ax4.set_title(f'(e) boundary-layer thickness (SCHEMATIC, mu {MU_GAS:g} Pa s ASSUMED)', loc='left', fontsize=9)
    for a in (ax1, ax2, ax3, ax4):
        a.set_xlabel('x along the grain [mm]'); a.grid(alpha=0.3)
    ax1.legend(fontsize=7); ax2.legend(fontsize=7); ax3.legend(fontsize=7)
    txt = 'Chamber state (CEA equilibrium, ABS_TYP_v1 card; delivered T0 = eta_c*^2 Tc, eta_c* 0.92 ASSUMED)\n'
    for f in FRACS:
        s = states[f]
        top = ', '.join(f'{k} {v:.2f}' for k, v in list(s['X_major'].items())[:5])
        txt += (f"{f*100:5.1f} %: Pc {s['Pc_bar']:.2f} bar, O/F {s['OF']:.2f}, Tc {s['Tc_K']:.0f} K, T0 {s['T0_delivered_K']:.0f} K, "
                f"gamma {s['gamma']:.3f}, MW {s['MW']:.2f}; X: {top}\n")
    fig.text(0.01, 0.005, txt, fontsize=6.6, family='monospace', va='bottom')
    fig.suptitle('ARGOS H1 chamber state and port flame, v2 grain S230 at ignition (SIM grain_q1d v2 + CEA; schematic items labelled)',
                 fontsize=10)
    fig.tight_layout(rect=(0, 0.11, 1, 0.97))
    os.makedirs(figdir, exist_ok=True)
    fn = os.path.join(figdir, 'chamber_port_state_v2.png'); fig.savefig(fn, dpi=140); plt.close(fig)
    out = dict(version='v2', date='2026-10-12', OF_stoich=ofst, mu_gas_assumed=MU_GAS, states=states,
               profiles={str(k): v for k, v in prof.items()}, figure=fn,
               notes=['Cumulative O/F is the cross-section mean; the real port has a fuel-rich wall layer and an '
                      'oxidiser-rich core (diffusion flame in the boundary layer).',
                      'At 100 % the mean mixture stays oxidiser-rich along the whole port (exit O/F 10.4 > 8.17): the '
                      'remaining fuel/oxidiser mixing happens in the post-chamber and nozzle; at <= 50 % the mean O/F '
                      'crosses stoichiometric inside the port.'])
    json.dump(out, open(os.path.join(datadir, 'v2', 'chamber_port_state_v2.json'), 'w'), indent=1, default=float)
    for f in FRACS:
        s = states[f]
        print(f, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items() if k != 'X_major'})


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
