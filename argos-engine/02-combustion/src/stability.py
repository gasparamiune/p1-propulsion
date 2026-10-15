"""Combustion stability screening across the throttle range (Combustion v2, brief task 7).

(1) Feed-coupled low-frequency (chug) - linear double-time-lag model (Crocco/Summerfield class), extended with the
    hybrid fuel-flow path:
      chamber  : theta_g dpsi/dt + psi = mu_ox w_ox + mu_f w_f + k_c (w_ox - w_f)
      injector : w_ox = -a psi(t - tau)              a = -dln(mdot_ox)/dln(Pc) from the Dyer table (0 if choked)
      fuel     : w_f  = n w_ox / (tau_f s + 1)       (thermal-lag first-order response, n = flux exponent)
    psi = dPc/Pc, w = dmdot/mdot, mu = mass-flow shares, k_c = dln c*/dln(O/F) (CEA), theta_g = L*/(c* Gamma^2).
    Stability: Nyquist of L(s) = a e^{-s tau} [mu_ox + mu_f n/(tau_f s+1) + k_c (1 - n/(tau_f s+1))] / (theta_g s + 1).
    Reported: gain margin GM = 1/|L(j w180)| over tau in {1, 2, 5, 10} ms and the critical delay tau_crit.
(2) Hybrid-specific low-frequency modes: time scales (solid thermal lag kappa/r^2, gas residence theta_g, port transit
    L/u) - orders of magnitude only; the thermal-lag/boundary-layer coupled instabilities of Karabeyoglu et al.
    (JPP 21(6) 2005) need a solid-phase response model that is NOT included -> mitigation + test requirement.
(3) Chamber acoustics: 1L (injector face -> throat, closed-closed approx.), pre/post-chamber Helmholtz pair coupled
    by the port, 1T of chamber and port.  Sound speed from CEA (delivered T0 = eta_c*^2 Tc).
Outputs data/v2/stability_v2.json and .csv
"""
from __future__ import annotations
import csv, json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import grain_q1d as Q
from run_dc import _FixedTank


def injector_sensitivity(e, h, Pc):
    m0, _ = e.mox_inj(h, Pc); m1, _ = e.mox_inj(h, Pc * 1.01)
    return -(math.log(m1) - math.log(m0)) / math.log(1.01)


def kc(e, Pc, OF):
    c0 = e.P.cstar(Pc, OF); c1 = e.P.cstar(Pc, OF * 1.02)
    return (math.log(c1) - math.log(c0)) / math.log(1.02)


def loop(s, a, mu_ox, mu_f, n, tf, k_c, theta, tau):
    fuel = n / (tf * s + 1)
    return a * np.exp(-s * tau) * (mu_ox + mu_f * fuel + k_c * (1 - fuel)) / (theta * s + 1)


def margins(a, mu_ox, mu_f, n, tf, k_c, theta, taus=(1e-3, 2e-3, 5e-3, 10e-3)):
    w = np.logspace(0, 5.5, 20000)
    out = {}
    for tau in taus:
        L = loop(1j * w, a, mu_ox, mu_f, n, tf, k_c, theta, tau)
        ph = np.unwrap(np.angle(L))
        # phase crossover at -180 deg (L has + sign convention: closed loop 1 + L = 0)
        idx = np.where(np.diff(np.sign(ph + np.pi)))[0]
        gm = min((1.0 / abs(L[i]) for i in idx), default=float('inf'))
        out[f'GM_tau{tau*1e3:g}ms'] = gm
    # critical delay: smallest tau making GM = 1 (scan)
    tc = float('inf')
    for tau in np.linspace(0.2e-3, 60e-3, 300):
        L = loop(1j * w, a, mu_ox, mu_f, n, tf, k_c, theta, tau)
        ph = np.unwrap(np.angle(L)); idx = np.where(np.diff(np.sign(ph + np.pi)))[0]
        if any(abs(L[i]) >= 1 for i in idx):
            tc = tau; break
    out['tau_crit_s'] = tc
    return out


def main(outdir):
    rows = []
    e = Q.Engine(_FixedTank(50.5e5, 293.15))
    c = e.c
    V_pre = math.pi / 4 * c['D_ch'] ** 2 * c['L_pre']; V_post = math.pi / 4 * c['D_ch'] ** 2 * c['L_post']
    for D in (0.025, 0.038):
        e.D[:] = D
        for fr in (1.0, 0.75, 0.5, 0.25, 0.2, 0.125):
            h, cei = e.lift_for_thrust(500 * fr); s = e.steady(h)
            Pc, OF = s['Pc'], s['OF']
            a = injector_sensitivity(e, h, Pc)
            mu_ox = s['mox'] / (s['mox'] + s['mf']); mu_f = 1 - mu_ox
            r, _ = e.regression(s['mox']); rbar = float(np.mean(r))
            tf = c['kappa_s'] / rbar ** 2
            g = e.P.gamma(Pc, OF); cs = e.cstar(Pc, OF)
            Gam = math.sqrt(g) * (2 / (g + 1)) ** ((g + 1) / (2 * (g - 1)))
            Vc = e.Vc(); Lstar = Vc / e.At; theta = Lstar / (cs * Gam ** 2)
            k_c = kc(e, Pc, OF)
            mg = margins(a, mu_ox, mu_f, c['n'], tf, k_c, theta)
            # acoustics
            T0 = e.P.Tc(Pc, OF) * c['eta_cstar'] ** 2
            R = (cs * Gam) ** 2 / T0                      # R from c* (delivered)
            a_s = math.sqrt(g * R * T0)
            L_ft = c['L_pre'] + c['L_grain'] + c['L_post'] + 0.0277
            f1L = a_s / (2 * L_ft)
            Ap = math.pi / 4 * D ** 2
            fH = a_s / (2 * math.pi) * math.sqrt(Ap / c['L_grain'] * (1 / V_pre + 1 / V_post))
            f1T_ch = 1.8412 * a_s / (math.pi * c['D_ch']); f1T_port = 1.8412 * a_s / (math.pi * D)
            rho_g = Pc / (R * T0); u_port = (s['mox'] + s['mf']) / (rho_g * Ap)
            rows.append(dict(D_port_m=D, frac=fr, Pc_Pa=Pc, OF=OF, dP_over_Pc=s['dpc'], inj_sensitivity_a=a,
                             theta_g_s=theta, tau_thermal_lag_s=tf, r_mean_m_s=rbar, port_transit_s=c['L_grain'] / u_port,
                             k_c=k_c, mu_f=mu_f, GM_tau1ms=mg['GM_tau1ms'], GM_tau2ms=mg['GM_tau2ms'],
                             GM_tau5ms=mg['GM_tau5ms'], GM_tau10ms=mg['GM_tau10ms'], tau_crit_s=mg['tau_crit_s'],
                             a_sound_m_s=a_s, f_1L_Hz=f1L, f_Helmholtz_pre_post_Hz=fH, f_1T_chamber_Hz=f1T_ch,
                             f_1T_port_Hz=f1T_port, f_thermal_lag_Hz=1 / (2 * math.pi * tf), u_port_m_s=u_port))
            print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in rows[-1].items()}, flush=True)
    fn = os.path.join(outdir, 'stability_v2.csv')
    with open(fn, 'w', newline='') as f:
        f.write('# Stability screening v2 (stability.py). Chug: linear double-time-lag + hybrid fuel path; GM = gain margin '
                '(inf = no phase crossover). Acoustic estimates with delivered T0. SIM/DERIVED.\n')
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    json.dump(rows, open(os.path.join(outdir, 'stability_v2.json'), 'w'), indent=1, default=float)


if __name__ == '__main__':
    main(sys.argv[1])
