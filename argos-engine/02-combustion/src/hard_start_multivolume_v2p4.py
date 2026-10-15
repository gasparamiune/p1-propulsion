"""Hard-start relief with the stand burst disc at the AFT end: three-node vented model (Combustion v2.4, RC-02;
lead request 2026-10-13 relaying Mechanical's finding (CHANGELOG 2026-10-13, Mechanical item 8) that the initial
25 mm grain port (491 mm2) is smaller than A_t + A_bd (148 + 491 mm2) and chokes the head-end relief path).

Question: with the disc only at the aft end (stand-only section TC-09S), what unignited inventory keeps the HEAD-end
pressure at or below proof 67.5 bar (and MEOP 45 bar) for a top-hat reaction over tau_r = 5 ms (the criterion behind the
LEAD 20 g cap), for a fresh grain; and does a certified disc of MNFA >= 792 mm2 at K_D 0.62 (DN32) or a DN40 disc change
it. Also: the credible (two-component) case in the same network, and the inventory at the Electronics v2.8 default
ignition lift (0.2039 mm) so that the R1/R2/R3 windows can be re-set against the allowable.

Model (SIM, same thermodynamics as hard_start_v2p4.vented_peak1):
  * nodes H (pre-chamber, L 30 mm, D 53.9 mm or 49.9 mm with TC-06 3.6 mm), P (port, D_port x 230 mm), A (post-chamber
    D 53.9 x 40 mm + convergent 28.26 cm3 from nozzle_contour_v2.csv); each node a perfectly-stirred volume of reacting
    products (constant R, frozen gamma, cv_eff = cp / kappa so that an instantaneous release reproduces the Cantera UV
    temperature and a slow one the HP temperature, as in hard_start_v2p4);
  * links: the port is ONE restriction Cd x A_port (Cd 1.0 rounded edge, 0.65 sharp-edged contraction, ASSUMED band),
    placed either at the port entrance (port volume downstream: 'entrance') or at the port exit (port volume upstream:
    'exit'); the other link is opened (50 x A_port). 'double' (Cd x A_port at the entrance and 1.0 x A_port at the exit)
    over-counts the loss of a straight duct and is kept as a conservative reference. A->ambient: throat A_t (Cd 1.0)
    plus the burst disc K_D x MNFA once P_A >= 55 bar (stays open); as a PROPOSAL (not in CAD) the same disc at the head
    node (stand-only head-end port), alone or with the aft disc. Isentropic orifice flow, choked or subsonic, either
    direction (upstream stagnation = upstream node);
  * release: top-hat m/tau into the nodes with a stated split ('head': all in H; 'volume': by node volume; 'aft': all
    in A); initial gas 1.1 bar, 190 K in every node; every admitted gram retained (as hard_start_v2p4);
  * the port is lumped (acoustic transit 0.23 ms << tau_r); friction and heat addition along the port are not modelled.
Validation: with the port links opened to 0.02 m2 (40 x A_port) the network reproduces hard_start_v2p4.vented_peak1 for the
summed volume (section 0).
usage: python -I hard_start_multivolume_v2p4.py DATA_V2P4_DIR
"""
from __future__ import annotations
import json, math, os, sys
sys.dont_write_bytecode = True
import numpy as np
from scipy.integrate import solve_ivp
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import hard_start_v2p4 as HS

PAMB = 101325.0
AT = HS.AT
MEOP, PROOF, P_BD = 45e5, 67.5e5, 55e5
EPS_LIN = 2e-3
L_PRE, L_GRAIN, L_POST, D_CH, V_CONV = 0.030, 0.230, 0.040, 0.0539, 28.26e-6
A_DN32 = 792e-6 * 0.62          # certified DN32 disc, MNFA 792 mm2 x K_D 0.62 (Mechanical) = 491 mm2, the same as the ideal 25 mm Cd 1 basis
A_DN40 = math.pi / 4 * 0.040 ** 2 * 0.62   # DN40, MNFA ASSUMED equal to the 40 mm bore
# disc sets: list of (node, effective area); node 2 = aft (TC-09S, Mechanical), node 0 = head (proposal, not in CAD)
DISCS = {'none': [],
         'DN32_cert_MNFA792_KD0.62_aft (= ideal 25 mm Cd 1, v2.4 first basis)': [(2, A_DN32)],
         'DN40_MNFA1257_KD0.62_aft (ASSUMED MNFA = bore)': [(2, A_DN40)],
         'DN32_cert_at_HEAD (proposal)': [(0, A_DN32)],
         'DN32_aft+DN32_head (proposal)': [(2, A_DN32), (0, A_DN32)]}
A_BD = {k: sum(a for _, a in v) for k, v in DISCS.items()}


def volumes(D_pre=D_CH, D_port=0.025):
    return [math.pi / 4 * D_pre ** 2 * L_PRE, math.pi / 4 * D_port ** 2 * L_GRAIN, math.pi / 4 * D_CH ** 2 * L_POST + V_CONV]


class Net:
    def __init__(self, prod, V, A_in, A_out, discs=(), P_bd=P_BD):
        self.R = prod['R']; self.g = prod['gamma_frozen']; self.Thp = prod['T_HP_K']; kap = prod['kappa']
        self.cp = self.g * self.R / (self.g - 1); self.cv = self.cp / kap
        self.Gc = math.sqrt(self.g) * (2 / (self.g + 1)) ** ((self.g + 1) / (2 * (self.g - 1)))
        self.crit = (2 / (self.g + 1)) ** (self.g / (self.g - 1))
        self.V = list(V); self.A_in = A_in; self.A_out = A_out; self.P_bd = P_bd
        self.discs = [(n, a) for n, a in discs if a > 0]
        self.opened = [False] * len(self.discs)

    def orifice(self, Pu, Tu, Pd, A):
        if Pu <= Pd or A <= 0:
            return 0.0
        pr = Pd / Pu
        if pr < self.crit:
            return A * Pu * self.Gc / math.sqrt(self.R * Tu)
        x = 1.0 - pr
        if x < EPS_LIN:
            # near-equal pressures: linear in (1 - pr) below EPS_LIN, matched at EPS_LIN (removes the infinite slope of the
            # isentropic law at pr -> 1 that made the stiff solver crawl; effect on the peaks < 0.1 % in the checks)
            pe = 1.0 - EPS_LIN
            fe = A * Pu * math.sqrt(max(2 * self.g / ((self.g - 1) * self.R * Tu) * (pe ** (2 / self.g) - pe ** ((self.g + 1) / self.g)), 0.0))
            return fe * x / EPS_LIN
        return A * Pu * math.sqrt(max(2 * self.g / ((self.g - 1) * self.R * Tu) * (pr ** (2 / self.g) - pr ** ((self.g + 1) / self.g)), 0.0))

    def link(self, Pi, Ti, Pj, Tj, A):
        """Mass flow i -> j (negative if j -> i) and the enthalpy it carries."""
        if Pi >= Pj:
            w = self.orifice(Pi, Ti, Pj, A); return w, w * self.cp * Ti
        w = self.orifice(Pj, Tj, Pi, A); return -w, -w * self.cp * Tj

    def rhs(self, y, r, split):
        m = y[0::2]; E = y[1::2]
        T = [E[i] / (m[i] * self.cv) for i in range(3)]
        P = [m[i] * self.R * T[i] / self.V[i] for i in range(3)]
        w01, h01 = self.link(P[0], T[0], P[1], T[1], self.A_in)
        w12, h12 = self.link(P[1], T[1], P[2], T[2], self.A_out)
        A_ex = AT + sum(a for (n, a), o in zip(self.discs, self.opened) if o and n == 2)
        A_hd = sum(a for (n, a), o in zip(self.discs, self.opened) if o and n == 0)
        w2a = self.orifice(P[2], T[2], PAMB, A_ex); h2a = w2a * self.cp * T[2]
        w0a = self.orifice(P[0], T[0], PAMB, A_hd) if A_hd > 0 else 0.0; h0a = w0a * self.cp * T[0]
        src = [r * s for s in split]; hs = self.cp * self.Thp
        d = np.empty(6)
        d[0] = src[0] - w01 - w0a; d[1] = src[0] * hs - h01 - h0a
        d[2] = src[1] + w01 - w12; d[3] = src[1] * hs + h01 - h12
        d[4] = src[2] + w12 - w2a; d[5] = src[2] * hs + h12 - h2a
        return d, P

    def peak(self, m0, tau, split, m_fast=0.0, tau_fast=1e-3, split_fast=None, P0=1.1e5, T0=190.0):
        """Peak pressure per node [Pa] for a top-hat slow release m0 over tau (split) plus an optional top-hat fast part."""
        split_fast = split_fast or split
        y = np.empty(6)
        for i in range(3):
            mi = P0 * self.V[i] / (self.R * T0); y[2 * i] = mi; y[2 * i + 1] = mi * self.cv * T0
        self.opened = [False] * len(self.discs)
        sq = math.sqrt(self.R * self.Thp) * self.Gc
        tv_slow = self.V[2] / (AT * sq) + self.V[1] / (self.A_out * sq)
        t_rel = max(tau if m0 > 0 else 0.0, tau_fast if m_fast > 0 else 0.0)
        t_max = t_rel + 25 * tv_slow
        Pk = [P0] * 3
        hs = self.cp * self.Thp
        atol = np.array([1e-10, 1e-4] * 3)
        # piecewise-constant sources: integrate segment by segment (stiff solver; the burst-disc opening is an event)
        ends = sorted({b for b in ((tau if m0 > 0 else None), (tau_fast if m_fast > 0 else None)) if b is not None and b < t_max})
        segs = []; a = 0.0
        for b in ends + [t_max]:
            if b > a:
                segs.append((a, b)); a = b
        t0 = 0.0
        for (a, b) in segs:
            tm = 0.5 * (a + b)
            r = m0 / tau if (m0 > 0 and tm < tau) else 0.0
            rf = m_fast / tau_fast if (m_fast > 0 and tm < tau_fast) else 0.0

            def fun(tt, yy, r=r, rf=rf):
                d1, _ = self.rhs(yy, r, split)
                if rf > 0:
                    for i in range(3):
                        d1[2 * i] += rf * split_fast[i]; d1[2 * i + 1] += rf * split_fast[i] * hs
                return d1

            def mk_burst(node):
                def burst(tt, yy):
                    return yy[2 * node] * self.R * (yy[2 * node + 1] / (yy[2 * node] * self.cv)) / self.V[node] - self.P_bd
                burst.terminal = True; burst.direction = 1
                return burst
            ms = max(min([x for x in (tau, tau_fast, tv_slow) if x > 0]) / 30.0, 1e-7)
            t0 = a
            while t0 < b - 1e-12:
                idx = [k for k in range(len(self.discs)) if not self.opened[k]]
                ev = [mk_burst(self.discs[k][0]) for k in idx] or None
                tb = b if (a < t_rel or b - t0 < 2 * tv_slow) else min(b, t0 + 2 * tv_slow)
                sol = solve_ivp(fun, (t0, tb), y, method='LSODA', events=ev, max_step=ms, rtol=1e-6, atol=atol)
                Y = sol.y
                for j in range(Y.shape[1]):
                    for i in range(3):
                        Pi = Y[2 * i, j] * self.R * (Y[2 * i + 1, j] / (Y[2 * i, j] * self.cv)) / self.V[i]
                        if Pi > Pk[i]:
                            Pk[i] = Pi
                y = Y[:, -1].copy(); t0 = sol.t[-1]
                if sol.status == 1:
                    for j, k in enumerate(idx):
                        if len(sol.t_events[j]) > 0:
                            self.opened[k] = True
                if t0 >= t_rel:
                    Pn = [y[2 * i] * self.R * (y[2 * i + 1] / (y[2 * i] * self.cv)) / self.V[i] for i in range(3)]
                    if max(Pn) < 0.5 * max(Pk):
                        return Pk
        return Pk


def make_net(prod, V3, D_port, cd, restr, disc_label):
    A = math.pi / 4 * D_port ** 2
    a_in, a_out = {'entrance': (cd * A, 50 * A), 'exit': (50 * A, cd * A), 'double': (cd * A, A)}[restr]
    return Net(prod, V3, a_in, a_out, discs=DISCS[disc_label])


def m_allow(net, tau, split, P_lim, node=0, lo=1e-3, hi=0.08):
    """Largest N2O inventory [kg] whose top-hat release over tau keeps the given node <= P_lim (bisection)."""
    if net.peak(lo, tau, split)[node] > P_lim:
        return 0.0
    if net.peak(hi, tau, split)[node] < P_lim:
        return float('inf')
    a, b = lo, hi
    for _ in range(12):
        c = 0.5 * (a + b)
        if net.peak(c, tau, split)[node] > P_lim:
            b = c
        else:
            a = c
    return 0.5 * (a + b)


def main(d):
    J = json.load(open(os.path.join(d, 'hard_start_v2p4.json')))
    res = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/hard_start_multivolume_v2p4.py',
               request='LEAD 2026-10-13 (Mechanical item 8: aft-end disc, port choke; Electronics v2.8 default lift 0.2039 mm)',
               inputs=dict(At_m2=AT, P_bd_Pa=P_BD, discs_node_area_m2=DISCS, L_pre=L_PRE, L_grain=L_GRAIN, L_post=L_POST, D_ch=D_CH,
                           V_conv_m3=V_CONV, tags=dict(geometry='combustion.json v2.3 gas path; convergent from nozzle_contour_v2.csv '
                                                       '(RC-16); D_pre 49.9 mm = Mechanical TC-06 3.6 mm (CHANGELOG 2026-10-13)',
                                                       Cd_in='ASSUMED band (rounded 1.0 / sharp-edged 0.65)',
                                                       disc='K_D x MNFA; DN32 MNFA 792 mm2 K_D 0.62 (Mechanical); DN40 MNFA ASSUMED = bore',
                                                       products='Cantera GRI-3.0 via hard_start_v2p4.products')))
    prods = {'dec_20C': HS.products('dec', 293.15), 'dec_A1': HS.products('dec', 286.70), 'comb_OF8': HS.products('comb', 293.15, OF=8.0)}
    res['products'] = {k: {kk: vv for kk, vv in v.items()} for k, v in prods.items()}
    # ---- 0. validation against the single-volume model
    prod = prods['dec_20C']; V3 = volumes(); Vsum = sum(V3)
    DN32 = 'DN32_cert_MNFA792_KD0.62_aft (= ideal 25 mm Cd 1, v2.4 first basis)'
    DN40 = 'DN40_MNFA1257_KD0.62_aft (ASSUMED MNFA = bore)'
    HEAD = 'DN32_cert_at_HEAD (proposal)'
    BOTH = 'DN32_aft+DN32_head (proposal)'
    val = {}
    for mg, tau in ((12.0, 5e-3), (20.0, 5e-3), (20.0, 2e-3), (8.0, 10e-3)):
        p1 = HS.vented_peak1(mg * 1e-3, tau, 'tophat', Vsum, prod, A_bd=A_DN32, P_bd=P_BD)
        net = Net(prod, V3, 0.02, 0.02, discs=DISCS[DN32])
        p3 = net.peak(mg * 1e-3, tau, [v / Vsum for v in V3])
        val[f'{mg}g|tau{tau*1e3:g}ms'] = dict(single_volume_bar=p1 / 1e5, network_open_port_bar=[p / 1e5 for p in p3])
        print('validation', mg, tau, round(p1 / 1e5, 2), [round(p / 1e5, 2) for p in p3], flush=True)
    res['validation_open_port_vs_single_volume'] = dict(v=val, tag='SIM check: port links 0.02 m2 (40 x A_port), volume-proportional release')
    # ---- 1. allowable inventory, fresh grain (25 mm) and used grain (30 / 35 mm)
    allow = {}

    def grid1():
        for dpre_lab, D_pre in (('Dpre49.9_TC06_3.6mm', 0.0499), ('Dpre53.9', 0.0539)):
            for restr in ('entrance', 'exit', 'double'):
                for cd in (1.0, 0.65):
                    for bd_lab in DISCS:
                        for sp_lab in ('head', 'volume', 'aft'):
                            taus = (2e-3, 5e-3, 10e-3, 20e-3) if (sp_lab == 'head' and restr != 'double' and D_pre == 0.0499) else (5e-3,)
                            for tau in taus:
                                yield dpre_lab, D_pre, 0.025, restr, cd, bd_lab, sp_lab, tau
        for D_port in (0.030, 0.035):
            for restr in ('entrance', 'exit'):
                for cd in (1.0, 0.65):
                    for bd_lab in (DN32, DN40, HEAD):
                        yield 'Dpre49.9_TC06_3.6mm', 0.0499, D_port, restr, cd, bd_lab, 'head', 5e-3
    for dpre_lab, D_pre, D_port, restr, cd, bd_lab, sp_lab, tau in grid1():
        V3 = volumes(D_pre, D_port); Vs = sum(V3)
        sp = {'head': [1.0, 0.0, 0.0], 'volume': [v / Vs for v in V3], 'aft': [0.0, 0.0, 1.0]}[sp_lab]
        net = make_net(prod, V3, D_port, cd, restr, bd_lab)
        row = dict(m_allow_head_proof_g=1e3 * m_allow(net, tau, sp, PROOF, node=0),
                   m_allow_head_MEOP_g=1e3 * m_allow(net, tau, sp, MEOP, node=0),
                   m_allow_aft_proof_g=1e3 * m_allow(net, tau, sp, PROOF, node=2))
        k = f'{dpre_lab}|Dport{D_port*1e3:.0f}mm|{restr}|Cd{cd}|{bd_lab}|{sp_lab}|tau{tau*1e3:g}ms'
        allow[k] = row
        print('allow', k, {kk: round(vv, 2) for kk, vv in row.items()}, flush=True)
    res['allowable_inventory'] = dict(v=allow, tag='SIM three-node vented model, decomposition products at 20 C, top-hat release; '
                                      'm_allow = largest N2O mass keeping the node <= the limit (inf = never exceeded up to 80 g; '
                                      '0 = exceeded at 1 g); bisection resolution 0.02 g')
    # ---- 2. peaks for given inventories (fresh grain, head release)
    pk = {}
    for dpre_lab, D_pre in (('Dpre49.9_TC06_3.6mm', 0.0499), ('Dpre53.9', 0.0539)):
        V3 = volumes(D_pre, 0.025)
        for restr in ('entrance', 'exit'):
            for cd in (1.0, 0.65):
                for bd_lab in ('none', DN32, DN40, HEAD, BOTH):
                    net = make_net(prod, V3, 0.025, cd, restr, bd_lab)
                    for mg in (6.0, 8.0, 10.0, 12.0, 13.0, 14.0, 15.0, 16.0, 18.9, 20.0, 26.6):
                        for tau in (5e-3, 10e-3, 20e-3):
                            p = net.peak(mg * 1e-3, tau, [1.0, 0.0, 0.0])
                            pk[f'{dpre_lab}|{restr}|Cd{cd}|{bd_lab}|{mg}g|tau{tau*1e3:g}ms'] = [x / 1e5 for x in p]
    res['peaks_head_release'] = dict(v=pk, tag='SIM: [head, port, aft] peak bar; fresh grain; release at the head')
    print('peaks done', flush=True)
    # ---- 3. credible case in the network: fast part (chamber vapour by volume + spray in transit at the head) + slow pool
    cred = {}
    cold = J['cold_flow_at_ignition_lift']['v']
    A_wet = math.pi * 0.025 * 0.230 + math.pi / 4 * 0.054 ** 2
    for st, pk_ in (('20C', 'dec_20C'), ('A1_relight', 'dec_A1')):
        c = cold[f'{st}|0.125']; prod_s = prods[pk_]
        D_pre = 0.0499; dpre_lab = 'Dpre49.9_TC06_3.6mm'
        V3 = volumes(D_pre, 0.025); Vs = sum(V3)
        m_vap = c['vapour_in_chamber_g']['reviewer_300.9cm3'] * 1e-3 * Vs / 300.9e-6
        for restr in ('entrance', 'exit'):
            for cd in (1.0, 0.65):
                for bd_lab in ('none', DN32, HEAD):
                    net = make_net(prod_s, V3, 0.025, cd, restr, bd_lab)
                    t_res = 0.06
                    m_s = c['liquid_flow_kg_s'] * t_res
                    m_f = m_vap + m_s
                    split_f = [(m_vap * V3[0] / Vs + m_s) / m_f, m_vap * V3[1] / Vs / m_f, m_vap * V3[2] / Vs / m_f]
                    for m_inv_g in (15.0, 20.0, 26.6):
                        m_pool = max(m_inv_g * 1e-3 - m_f, 0.0)
                        for q in (0.5e6, 2.0e6):
                            tau_pool = max(m_pool * 375e3 / (q * A_wet), 1e-3)
                            for tf in (1e-3, 5e-3):
                                p = net.peak(m_pool, tau_pool, [v / Vs for v in V3], m_fast=m_f, tau_fast=tf, split_fast=split_f)
                                cred[f'{st}|{dpre_lab}|{restr}|Cd{cd}|{bd_lab}|tres{t_res}|{m_inv_g}g|q{q/1e6:.1f}|tf{tf*1e3:.0f}ms'] = dict(
                                    m_fast_g=m_f * 1e3, head_fraction_of_fast=split_f[0], tau_pool_s=tau_pool, peak_bar=[x / 1e5 for x in p])
        print('credible', st, 'done', flush=True)
    res['credible_case_network'] = dict(v=cred, tag='ESTIMATE (ASSUMED inputs as hard_start_v2p4 section 5); fast part = chamber vapour '
                                        '(by node volume) + spray in transit 0.06 s (at the head) reacting top-hat over tf; pool evaporation-limited '
                                        '(375 kJ/kg over the wetted area at q), released by node volume; [head, port, aft] peak bar')
    # ---- 4. fuel-assisted fast part (O/F 8), same split
    fa = {}
    prod_c = prods['comb_OF8']
    for st in ('20C', 'A1_relight'):
        c = cold[f'{st}|0.125']
        V3 = volumes(0.0499, 0.025); Vs = sum(V3)
        m_vap = c['vapour_in_chamber_g']['reviewer_300.9cm3'] * 1e-3 * Vs / 300.9e-6
        for restr in ('entrance', 'exit'):
            for cd in (1.0, 0.65):
                for bd_lab in (DN32, HEAD):
                    net = make_net(prod_c, V3, 0.025, cd, restr, bd_lab)
                    for t_res in (0.02, 0.06):
                        m_s = c['liquid_flow_kg_s'] * t_res; m_f = m_vap + m_s
                        split_f = [(m_vap * V3[0] / Vs + m_s) / m_f, m_vap * V3[1] / Vs / m_f, m_vap * V3[2] / Vs / m_f]
                        for tf in (1e-3, 5e-3, 10e-3):
                            p = net.peak(m_f * prod_c['mass_per_kg_N2O'], tf, split_f)
                            fa[f'{st}|Dpre49.9|{restr}|Cd{cd}|{bd_lab}|tres{t_res}|tf{tf*1e3:.0f}ms'] = [x / 1e5 for x in p]
    res['fuel_assisted_fast_part_network'] = dict(v=fa, tag='ESTIMATE: fast part with fuel at O/F 8 (fuel not limited); [head, port, aft] bar')
    # ---- 5. inventory at the Electronics v2.8 default ignition lift (0.2039 mm) against the window W
    inv = {}
    lifts = J['ignition_lifts']['v']
    for st in ('15C', '20C', '25C', 'A1_relight'):
        L = lifts[f'{st}|0.125']; c = cold[f'{st}|0.125']
        row = {'cold_flow_g_s_at_0.2039mm': 1e3 * HS.mdot_cold(0.2039e-3, L['P_tank_Pa'], L['T_tank_K'], c['P2_Pa'])}
        for W in (0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65):
            row[f'W{W:.2f}_g'] = 1e3 * HS.inventory(0.2039e-3, L['P_tank_Pa'], L['T_tank_K'], c['P2_Pa'], W)[0]
            row[f'W{W:.2f}_g_at_author_lift'] = 1e3 * HS.inventory(L['lift_m'], L['P_tank_Pa'], L['T_tank_K'], c['P2_Pa'], W)[0]
        row['author_lift_mm'] = L['lift_m'] * 1e3
        inv[st] = row
        print('inventory', st, {k: round(v, 2) for k, v in row.items()}, flush=True)
    res['inventory_vs_W_v2p8_lift'] = dict(v=inv, tag='DERIVED hard_start_v2p4.inventory (Dyer, Cd 0.70 ASSUMED, servo history, W from the '
                                         'lift command, close command 6.5 ms later); 0.2039 mm = Electronics v2.8 default (CHANGELOG 2026-10-13)')
    fn = os.path.join(d, 'hard_start_multivolume_v2p4.json')
    json.dump(res, open(fn, 'w'), indent=1, default=float)
    print('wrote', fn)


if __name__ == '__main__':
    main(sys.argv[1])
