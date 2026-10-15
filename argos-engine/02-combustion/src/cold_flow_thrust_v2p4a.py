"""Cold-flow apparent thrust after an undetected flame-out under the drogue (Combustion v2.4a, 2026-10-13).

Asked by the coordinator after REV-GNC-3 / LEAD CHANGELOG line 181 (4): "Combustion bounds cold-flow apparent thrust under the drogue
after a flame-out" for 0-0.8 s after E2: N2O still flowing through the pintle and the nozzle with no combustion, at the relight tank
states; GNC's R2 release rule (Pc invalid) triggers at 37.16 N of accelerometer thrust and the flame-out case peaks at 33.0 N without
any cold-flow term (sim6 V, pcf_fo: truth thrust decays with t_off, no cold-flow model).

Setting (REPORT v2.4a 7.4 A7, electronics.json "Pc sensor fault"): with Pc invalid in flight the ECU runs the pintle OPEN LOOP on the
feed-forward map at P_feed; nothing closes the pintle on a flame-out (A3 needs a valid Pc).  The lift therefore follows the thrust
command.  Profiles (ASSUMED; GNC's own command trace replaces them): hold at the start level 62.5 N; the start ramp 2500 N/s to
200 N or 500 N; and an envelope valid for ANY command: the pintle moving at the drive's rate limit to the 4.0 mm stroke.

Two numbers per lift (SI):
  BOUND    F <= mdot_max * v_iso,eq.  mdot_max: Dyer flux at P1 = P_tank (no line loss), saturated liquid at T_tank, downstream at
           ambient, Cd 0.80 (line 172 (4) CF acceptance upper limit).  v_iso,eq: isentropic EQUILIBRIUM expansion of the tank liquid
           to ambient (CoolProp).  For steady adiabatic quasi-1D flow dF = (P_e - P_a) dA_e along an isentrope, so the thrust is
           largest at P_e = P_a; irreversibility (injector throttling, slip, non-equilibrium, friction) only raises the entropy and
           h(P_a, s) rises with s, so no adiabatic flow from the tank state exceeds mdot * v_iso,eq.  Heat added to the stream is
           EXCLUDED from the bound and reported as a sensitivity (heat added at tank pressure: the largest work potential per J).
  NOMINAL  quasi-steady HEM estimate: Dyer injector (Cd 0.70, line loss 2.5 bar at 0.25 kg/s ~ mdot^2, grain_q1d v2 plant, injector
           table v2), adiabatic chamber at the stagnation enthalpy of the tank liquid, HEM isentropic nozzle (A_t 147.9 mm2 x Cd_t
           0.98, eps 2.0) choked or venturi; thrust at optimum expansion (upper) and full-flowing at eps 2 (lower, when evaluable).
Not covered: heat pick-up from the hot chamber, grain and nozzle (MISSING thermal state at the relight; sensitivity given),
N2O decomposition or re-ignition on the hot grain (then the engine is not dead), hot-gas blowdown at the flame-out (GNC's t_off
decay, separate), vapour in the line (lower thrust: vapour HEM flux 15 450 vs liquid Dyer 56 843 kg/m2s), phase slip (lowers).
usage: python -I cold_flow_thrust_v2p4a.py THROTTLE_MAP_S230 OUT_JSON OUT_CSV
"""
from __future__ import annotations
import csv, hashlib, json, math, os, sys
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import CoolProp.CoolProp as CP
from scipy.optimize import brentq
import injector as INJ
import grain_q1d as Q
import start_latency_v2p4 as SL

EXPECT_SRC = {'injector.py': '4ee8e0a1b4825a09', 'grain_q1d.py': 'e00f692489ec5234', 'start_latency_v2p4.py': '989ccd9a004b2cb9'}
EXPECT_TAB = '3741ae82a81bb637'                       # data/v2/injector_G_table_v2.npz
EXPECT_MAP = '4f2e6d846f7253da'                       # throttle_map_v2.csv (S230)
GNC_SRC = {'REVIEW-GNC-R2.md': 'fabfc81fa1d70327', 'REPORT-GNC-rev2.md': '2edf0360cbc975e5'}
# GNC numbers (SIM, sim6 V): R2 threshold and the largest flame-out estimates without a cold-flow term
R2 = dict(F_threshold_N=37.16, flameout_max_all_winds_0p5s_N=33.0, flameout_max_W_lt6_0p5s_N=20.85,
          flameout_max_all_winds_0p8s_probe_N=35.20, flameout_max_W_lt6_0p8s_A1none_N=20.06,
          source='REPORT-GNC-rev2 6 (33.0 N, 37.16 N); REVIEW-GNC-R2 4.5 (29.92 / 32.98 N; W<6: 18.75 / 20.85 N; 0.8 s probe 35.20 N, '
                 'W<6 20.06 N on A1_none)')
PA = 101325.0
PA_LOW = 95000.0                                      # ASSUMED site/altitude bracket for the ambient pressure (site elevation MISSING)
CD_BOUND = 0.80                                       # line 172 (4): CF-1/CF-3 accept Cd <= 0.80
CD_NOM = Q.CFG['Cd'][0]                               # 0.70 ASSUMED (grain_q1d v2, the throttle map basis)
CD_T = 0.98                                           # throat discharge coefficient (as ignition_detect_v2p4 unlit bound)
A_T = math.pi / 4 * Q.CFG['Dt0'][0] ** 2
EPS = Q.CFG['eps0'][0]
A_E = A_T * EPS
DP_REF = Q.CFG['dp_line_ref'][0]
STROKE = INJ.STROKE
V_DRIVE = SL.V_PINTLE                                 # 16.7 mm/s HV69 at MEOP (DERIVED); faster at lower load (envelope timing only)
LAG = 0.010                                           # ASSUMED servo lag (start_latency t_lift term; grain_q1d tau_act 0.010)
F_START = 62.5; RAMP = 2500.0
P_TRIPLE = 87850.0                                    # N2O triple-point pressure (~0.8785 bar, LITERATURE); isentropes stop above it
T_STATES = {'cold_283.15K': 283.15, 'A1_relight_286.7K': 286.70, 'coast_289.5K': 289.50}
AS = CP.AbstractState('HEOS', 'NitrousOxide')


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def sat_liq(T):
    AS.update(CP.QT_INPUTS, 0.0, T)
    return dict(P=AS.p(), h=AS.hmass(), s=AS.smass(), rho=AS.rhomass())


def v_iso(h0, s0, p):
    AS.update(CP.PSmass_INPUTS, p, s0)
    return math.sqrt(max(2.0 * (h0 - AS.hmass()), 0.0)), AS.Q()


def v_heated(T, dh, p_exit):
    """Velocity bound with dh added to the tank liquid at tank pressure (largest work potential per J of heat)."""
    st = sat_liq(T)
    AS.update(CP.HmassP_INPUTS, st['h'] + dh, st['P'])
    s1 = AS.smass()
    return v_iso(st['h'] + dh, s1, p_exit)[0]


def load_map(fn):
    rows = [r for r in csv.reader(open(fn)) if r and not r[0].startswith('#')]
    h = rows[0]
    out = {}
    for P in (4.0e6, 4.5e6, 5.0e6):
        sel = [r for r in rows[1:] if abs(float(r[h.index('P_tank_Pa')]) - P) < 1.0 and abs(float(r[h.index('D_port_m')]) - 0.030) < 1e-6]
        sel.sort(key=lambda r: float(r[h.index('F_N')]))
        out[P] = dict(F=np.array([float(r[h.index('F_N')]) for r in sel]), lift=np.array([float(r[h.index('lift_m')]) for r in sel]),
                      mox=np.array([float(r[h.index('mdot_ox')]) for r in sel]), Fceil=float(sel[0][h.index('F_ceiling_N')]),
                      ceil_lim=sel[0][h.index('ceiling_limit')])
    return out


def map_lift(M, F, P):
    """Open-loop map lift for thrust F at tank pressure P (linear in P between the 4.0/4.5/5.0 MPa rows)."""
    Ps = sorted(M)
    P = min(max(P, Ps[0]), Ps[-1])
    for a, b in zip(Ps[:-1], Ps[1:]):
        if a <= P <= b:
            w = (P - a) / (b - a)
            la = np.interp(F, M[a]['F'], M[a]['lift']); lb = np.interp(F, M[b]['F'], M[b]['lift'])
            return float((1 - w) * la + w * lb)
    raise ValueError(P)


def mdot_bound(h, T, p2=PA):
    st = sat_liq(T)
    spi, hem, dyer, k = INJ.g_models(st['P'], T, np.array([p2]))
    return CD_BOUND * INJ.pintle_area(h) * float(dyer[0]), dict(G_dyer=float(dyer[0]), G_spi=float(spi[0]), G_hem=float(hem[0]))


def nozzle(Pc, h0, n=70):
    """HEM capacity of the nozzle and the exit states for chamber (Pc, h0); isentrope sampled down to just above the triple point."""
    AS.update(CP.HmassP_INPUTS, h0, Pc); s = AS.smass(); xc = AS.Q()
    p_lo = P_TRIPLE * 1.005
    ps = np.geomspace(Pc * 0.9999, p_lo, n)
    hh = np.empty(n); rr = np.empty(n)
    for i, p in enumerate(ps):
        AS.update(CP.PSmass_INPUTS, float(p), s); hh[i] = AS.hmass(); rr[i] = AS.rhomass()
    v = np.sqrt(np.clip(2.0 * (h0 - hh), 0.0, None)); G = rr * v
    i_s = int(np.argmax(G)); G_star = float(G[i_s]); star_at_floor = (i_s == n - 1)
    vPa = float(np.interp(math.log(PA), np.log(ps[::-1]), v[::-1])); GPa = float(np.interp(math.log(PA), np.log(ps[::-1]), G[::-1]))
    m_choked = CD_T * A_T * G_star; m_venturi = A_E * GPa
    return dict(s=s, x_chamber=xc, ps=ps, v=v, G=G, i_star=i_s, G_star=G_star, star_at_floor=star_at_floor, v_Pa=vPa, G_Pa=GPa,
                m_cap=min(m_choked, m_venturi), choked=m_choked <= m_venturi, p_star=float(ps[i_s]))


def nominal(h, T, GT, Cd=CD_NOM, dh=0.0):
    """dh: heat added to the stream in the chamber (sensitivity; 0 = adiabatic)."""
    st = sat_liq(T)
    h0 = st['h'] + dh
    CdA = Cd * INJ.pintle_area(h)

    def m_inj(Pc):
        m = 0.0
        for _ in range(6):
            P1 = st['P'] - DP_REF * (m / 0.25) ** 2
            if P1 <= Pc * 1.001:
                return 0.0
            m = CdA * GT.G(P1, T, Pc)
        return m

    f = lambda Pc: m_inj(Pc) - nozzle(Pc, h0)['m_cap']
    lo, hi = PA * 1.002, st['P'] * 0.95
    if f(lo) <= 0:
        return None
    Pc = brentq(f, lo, hi, xtol=50.0)
    nz = nozzle(Pc, h0); m = m_inj(Pc)
    F_opt = m * nz['v_Pa']
    F_eps = None; p_e = None
    if nz['choked']:
        Ge = m / A_E
        sup_G = nz['G'][nz['i_star']:]; sup_p = nz['ps'][nz['i_star']:]; sup_v = nz['v'][nz['i_star']:]
        j = np.where(sup_G <= Ge)[0]
        if len(j):
            j0 = int(j[0]); j1 = max(j0 - 1, 0)
            w = 0.0 if j0 == j1 else (Ge - sup_G[j1]) / (sup_G[j0] - sup_G[j1])
            p_e = float(sup_p[j1] + w * (sup_p[j0] - sup_p[j1])); v_e = float(sup_v[j1] + w * (sup_v[j0] - sup_v[j1]))
            F_eps = m * v_e + (p_e - PA) * A_E
    else:
        F_eps = F_opt; p_e = PA
    return dict(Pc_bar=Pc / 1e5, mdot=m, x_chamber=nz['x_chamber'], choked=nz['choked'], p_star_bar=nz['p_star'] / 1e5,
                star_at_isentrope_floor=nz['star_at_floor'], v_Pa=nz['v_Pa'], F_opt=F_opt, F_eps2=F_eps,
                p_exit_eps2_bar=None if p_e is None else p_e / 1e5)


def main(map_fn, out_json, out_csv):
    for k, v in EXPECT_SRC.items():
        assert sha16(os.path.join(HERE, k)) == v, (k, sha16(os.path.join(HERE, k)))
    assert sha16(INJ.TAB_FN) == EXPECT_TAB, sha16(INJ.TAB_FN)
    assert sha16(map_fn) == EXPECT_MAP, sha16(map_fn)
    assert abs(V_DRIVE - 0.004 / 0.24) < 1e-12 and abs(A_T * 1e6 - 147.93) < 0.05 and EPS == 2.0 and CD_NOM == 0.70
    GT = INJ.GTable()
    M = load_map(map_fn)
    # map check: lift at 62.5 N / 200 N / 500 N at 4.5 MPa (REPORT throttle map) reproduced
    assert abs(map_lift(M, 500.0, 4.5e6) - 2.11917e-3) < 1e-8 and abs(map_lift(M, 200.0, 4.5e6) - 0.620402e-3) < 1e-9
    lift_grid = np.array([0.15, 0.2039, 0.22, 0.25, 0.30, 0.40, 0.50, 0.62, 0.80, 1.00, 1.30, 1.60, 2.00, 2.20, 2.50, 3.00, 3.50, 4.00]) * 1e-3
    res_states = {}
    csv_rows = []
    for lab, T in T_STATES.items():
        st = sat_liq(T)
        v_eq, x_e = v_iso(st['h'], st['s'], PA)
        v_eq_low = v_iso(st['h'], st['s'], PA_LOW)[0]
        heat = {f'{int(dh / 1e3)}kJ_kg': dict(v_bound=v_heated(T, dh, PA)) for dh in (0.0, 25e3, 50e3, 100e3, 200e3)}
        tab = []
        for h in lift_grid:
            mb, gb = mdot_bound(h, T)
            mb_low = mdot_bound(h, T, PA_LOW)[0]
            nm = nominal(h, T, GT); nm_hi = nominal(h, T, GT, Cd=CD_BOUND)
            row = dict(lift_mm=h * 1e3, area_mm2=INJ.pintle_area(h) * 1e6, mdot_bound_kg_s=mb, F_bound_N=mb * v_eq,
                       F_bound_Pa95kPa_N=mb_low * v_eq_low, G_bound=gb, nominal_Cd070=nm, nominal_Cd080=nm_hi)
            tab.append(row)
            csv_rows.append([lab, T, st['P'], h * 1e3, mb, mb * v_eq, nm['mdot'], nm['Pc_bar'], nm['F_opt'],
                             '' if nm['F_eps2'] is None else nm['F_eps2'], nm_hi['mdot'], nm_hi['F_opt']])
        Lb = np.array([r['lift_mm'] for r in tab]) * 1e-3
        Fb = np.array([r['F_bound_N'] for r in tab]); Fn = np.array([r['nominal_Cd070']['F_opt'] for r in tab])
        Fn8 = np.array([r['nominal_Cd080']['F_opt'] for r in tab])
        Fb_of = lambda h: np.interp(h, Lb, Fb)
        Fn_of = lambda h: np.interp(h, Lb, Fn)
        Fn8_of = lambda h: np.interp(h, Lb, Fn8)
        # per commanded thrust (open-loop map lift at this tank pressure)
        per_F = []
        for Fc in (62.5, 75.0, 100.0, 125.0, 150.0, 200.0, 250.0, 375.0, 500.0):
            h = map_lift(M, Fc, st['P'])
            per_F.append(dict(F_cmd_N=Fc, lift_mm=h * 1e3, F_bound_N=float(Fb_of(h)), F_nom_N=float(Fn_of(h)), F_nom_Cd080_N=float(Fn8_of(h)),
                              bound_over_cmd=float(Fb_of(h) / Fc)))
        per_F.append(dict(F_cmd_N='stroke 4.0 mm', lift_mm=STROKE * 1e3, F_bound_N=float(Fb_of(STROKE)), F_nom_N=float(Fn_of(STROKE)),
                          F_nom_Cd080_N=float(Fn8_of(STROKE))))
        # commanded thrust at which the bound / nominal alone reach given levels
        Fgrid = np.linspace(62.5, 500.0, 1751)
        hF = np.array([map_lift(M, f, st['P']) for f in Fgrid])
        def first_F(curve, level):
            v = curve(hF); i = np.where(v >= level)[0]
            return None if len(i) == 0 else float(Fgrid[i[0]])
        levels = {'4.16N_margin_all_winds': R2['F_threshold_N'] - R2['flameout_max_all_winds_0p5s_N'],
                  '16.31N_margin_W_lt6': R2['F_threshold_N'] - R2['flameout_max_W_lt6_0p5s_N'],
                  '37.16N_threshold_alone': R2['F_threshold_N']}
        F_cmd_reaching = {k: dict(bound=first_F(Fb_of, lv), nominal=first_F(Fn_of, lv), nominal_Cd080=first_F(Fn8_of, lv)) for k, lv in levels.items()}
        # time profiles 0-0.8 s after E2
        t = np.arange(0.0, 0.8 + 1e-9, 0.0025)
        h_start = map_lift(M, F_START, st['P'])
        prof = {}
        for plab, Fc in (('hold_start_level_62p5N', None), ('ramp_to_200N', 200.0), ('ramp_to_500N', 500.0), ('envelope_any_command', 'env')):
            if Fc == 'env':
                hh = np.minimum(STROKE, h_start + V_DRIVE * np.clip(t - LAG, 0.0, None))
            else:
                Fcmd = np.full_like(t, F_START) if Fc is None else np.minimum(F_START + RAMP * t, Fc)
                hcmd = np.array([map_lift(M, f, st['P']) for f in Fcmd])
                hh = np.empty_like(t); hh[0] = h_start
                for i in range(1, len(t)):
                    tgt = h_start if t[i] < LAG else float(np.interp(t[i] - LAG, t, hcmd))
                    dmax = V_DRIVE * (t[i] - t[i - 1])
                    hh[i] = hh[i - 1] + min(max(tgt - hh[i - 1], -dmax), dmax)
            fb = Fb_of(hh); fn = Fn_of(hh); fn8 = Fn8_of(hh)
            w5 = t <= 0.5 + 1e-9
            def t_first(v, lv):
                i = np.where(v >= lv)[0]
                return None if len(i) == 0 else float(t[i[0]])
            prof[plab] = dict(lift_mm_at=dict(t0=float(hh[0] * 1e3), t0p1=float(np.interp(0.1, t, hh) * 1e3), t0p5=float(np.interp(0.5, t, hh) * 1e3),
                                              t0p8=float(hh[-1] * 1e3)),
                              F_bound_N=dict(t0=float(fb[0]), max_0_0p5s=float(fb[w5].max()), max_0_0p8s=float(fb.max())),
                              F_nom_N=dict(t0=float(fn[0]), max_0_0p5s=float(fn[w5].max()), max_0_0p8s=float(fn.max())),
                              F_nom_Cd080_N=dict(max_0_0p8s=float(fn8.max())),
                              t_first_s={k: dict(bound=t_first(fb, lv), nominal=t_first(fn, lv)) for k, lv in levels.items()},
                              series_t_s_every_25ms=[float(x) for x in t[::10]],
                              series_F_bound_N=[float(x) for x in fb[::10]], series_F_nom_N=[float(x) for x in fn[::10]])
        heat_nom = {}
        for Fc in (62.5, 200.0):
            hF_ = map_lift(M, Fc, st['P'])
            heat_nom[f'F_cmd_{Fc:g}N'] = {f'{int(dh / 1e3)}kJ_kg': dict(F_nom_opt_N=nominal(hF_, T, GT, dh=dh)['F_opt'],
                                                                        F_bound_N=float(mdot_bound(hF_, T)[0] * v_heated(T, dh, PA)))
                                          for dh in (0.0, 50e3, 100e3, 200e3)}
        mb_s = mdot_bound(h_start, T)[0]
        dh_lo, dh_hi = 0.0, 400e3
        for _ in range(40):
            dm = 0.5 * (dh_lo + dh_hi)
            if mb_s * v_heated(T, dm, PA) >= levels['16.31N_margin_W_lt6']:
                dh_hi = dm
            else:
                dh_lo = dm
        ign_check = dict(lift_mm=0.2039, mdot_Cd070_noLineLoss_Pa_kg_s=float(mdot_bound(0.2039e-3, T)[0] * CD_NOM / CD_BOUND),
                         mdot_Cd070_nominal_model_kg_s=nominal(0.2039e-3, T, GT)['mdot'],
                         report_value='REPORT v2.4: 35.0 g/s at the A1 state, 37.1 g/s at 20 C (CF-3 table <= 37.4 g/s)')
        res_states[lab] = dict(T_tank_K=T, heat_pickup_nominal_sensitivity=heat_nom,
                               dh_for_start_level_bound_to_reach_W_lt6_margin_J_kg=dh_hi, heat_rate_for_that_W=dh_hi * mb_s,
                               ignition_lift_flow_check=ign_check, P_tank_bar=st['P'] / 1e5, rho_liq=st['rho'], v_iso_eq_m_s=v_eq, exit_quality_eq=x_e,
                               v_iso_eq_at_95kPa_m_s=v_eq_low, heat_pickup_sensitivity=heat, h_start_level_mm=h_start * 1e3,
                               per_lift=tab, per_F_cmd=per_F, F_cmd_at_which_cold_flow_reaches=F_cmd_reaching, profiles=prof)
    # chamber hot-gas energy at the flame-out, for scale (FA-1 closed volume; Pc at E2 3-4.4 bar; gamma 1.2) - DERIVED order of magnitude
    E_gas = [P * 365.65e-6 / 0.2 for P in (3.0e5, 4.4e5)]
    out = dict(version='v2.4a', date='2026-10-13', script=os.path.basename(__file__), script_sha256_16=sha16(os.path.abspath(__file__)),
               request='coordinator after REV-GNC-3 / LEAD CHANGELOG line 181 (4): cold-flow apparent thrust under the drogue after an undetected flame-out at E2, 0-0.8 s',
               inputs={**EXPECT_SRC, 'injector_G_table_v2.npz': EXPECT_TAB, os.path.basename(map_fn): EXPECT_MAP, **GNC_SRC},
               constants=dict(P_ambient_Pa=PA, P_ambient_low_Pa=PA_LOW, Cd_bound=CD_BOUND, Cd_nominal=CD_NOM, Cd_throat=CD_T, A_t_m2=A_T, eps=EPS,
                              dp_line_ref_Pa_at_0p25kg_s=DP_REF, stroke_m=STROKE, drive_rate_m_s=V_DRIVE, lag_s=LAG, F_start_N=F_START,
                              ramp_N_s=RAMP, P_triple_Pa=P_TRIPLE),
               R2_numbers=R2, states=res_states,
               hot_gas_energy_at_flameout_J=E_gas,
               tags=dict(bound='DERIVED thermodynamic bound (CoolProp HEOS N2O; Dyer flux) on ASSUMED Cd <= 0.80 (CF acceptance limit), no line loss, '
                               'adiabatic; open-loop map lift (SIM throttle map S230, Cd 0.70)',
                         nominal='DERIVED quasi-steady HEM model on ASSUMED Cd 0.70 (0.80 variant), ASSUMED line loss, Cd_t 0.98; no measurement exists',
                         profiles='ASSUMED command profiles (hold 62.5 N; 2500 N/s ramps to 200/500 N) and DERIVED drive envelope (HV69 16.7 mm/s, lag 10 ms '
                                  'ASSUMED); GNC replaces them with the sim6 command trace',
                         tank_states='A1 relight 286.7 K / 43.5 bar (SIM, Combustion A1 v2 run at the relight command); coast state 289.5 K / 46.45 bar '
                                     '(REPORT); 283.15 K / 40.0 bar ASSUMED cold bracket; saturated (no supercharge in flight)',
                         R2='GNC SIM numbers (sim6 V), quoted', heat='sensitivity only; the chamber/nozzle thermal state at the relight is MISSING'),
               excluded=['heat pick-up from the hot chamber, grain and nozzle (sensitivity table)', 'N2O decomposition or re-ignition on the hot grain',
                         'hot-gas blowdown at the flame-out (GNC t_off decay; add, do not replace)', 'vapour in the feed line (lowers the thrust)',
                         'phase slip and non-equilibrium (lower the thrust)', 'nozzle flow separation (between the eps-2 and optimum values)'])
    json.dump(out, open(out_json, 'w'), indent=1, default=float)
    with open(out_csv, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['# cold_flow_thrust_v2p4a (Combustion v2.4a, 2026-10-13). F_bound DERIVED upper bound (Cd 0.80, no line loss, isentropic '
                    'equilibrium to 1 atm, adiabatic); F_nom DERIVED HEM estimate (Cd 0.70 / 0.80, optimum expansion). SI except lift mm, P bar.'])
        w.writerow(['state', 'T_tank_K', 'P_tank_Pa', 'lift_mm', 'mdot_bound_kg_s', 'F_bound_N', 'mdot_nom_kg_s', 'Pc_nom_bar', 'F_nom_opt_N',
                    'F_nom_eps2_N', 'mdot_nom_Cd080_kg_s', 'F_nom_Cd080_opt_N'])
        for r in csv_rows:
            w.writerow(r)
    # summary
    for lab, s in res_states.items():
        print(f"{lab}: P {s['P_tank_bar']:.2f} bar v_eq {s['v_iso_eq_m_s']:.1f} m/s (x_e {s['exit_quality_eq']:.3f}; 95 kPa {s['v_iso_eq_at_95kPa_m_s']:.1f}) "
              f"heat {[round(v['v_bound'], 1) for v in s['heat_pickup_sensitivity'].values()]} h_start {s['h_start_level_mm']:.4f} mm")
        for r in s['per_F_cmd']:
            pass
        print('   heat nominal', json.dumps({k: {a: round(b['F_nom_opt_N'], 2) for a, b in v.items()} for k, v in s['heat_pickup_nominal_sensitivity'].items()}),
              'bound', json.dumps({k: {a: round(b['F_bound_N'], 2) for a, b in v.items()} for k, v in s['heat_pickup_nominal_sensitivity'].items()}))
        print('   dh to reach the W<6 margin at the start level %.1f kJ/kg (%.2f kW); ign check %s' % (s['dh_for_start_level_bound_to_reach_W_lt6_margin_J_kg'] / 1e3,
              s['heat_rate_for_that_W'] / 1e3, json.dumps(s['ignition_lift_flow_check'])))
        for r in s['per_F_cmd']:
            print('   Fcmd', r['F_cmd_N'], 'lift %.3f mm  bound %.1f N  nom %.1f N  nom(Cd0.80) %.1f N' % (r['lift_mm'], r['F_bound_N'], r['F_nom_N'], r['F_nom_Cd080_N']))
        for r in s['per_lift'][::3]:
            n_ = r['nominal_Cd070']
            print('   lift %.3f mm A %.2f mm2 m_b %.4f F_b %.1f | nom m %.4f Pc %.2f bar x %.3f choked %s p* %.2f F_opt %.1f F_eps2 %s pe %s'
                  % (r['lift_mm'], r['area_mm2'], r['mdot_bound_kg_s'], r['F_bound_N'], n_['mdot'], n_['Pc_bar'], n_['x_chamber'], n_['choked'],
                     n_['p_star_bar'], n_['F_opt'], None if n_['F_eps2'] is None else round(n_['F_eps2'], 1),
                     None if n_['p_exit_eps2_bar'] is None else round(n_['p_exit_eps2_bar'], 3)))
        print('   F_cmd reaching:', json.dumps(s['F_cmd_at_which_cold_flow_reaches']))
        for p, v in s['profiles'].items():
            print('   ', p, 'lift', {k: round(x, 3) for k, x in v['lift_mm_at'].items()}, 'bound', {k: round(x, 1) for k, x in v['F_bound_N'].items()},
                  'nom', {k: round(x, 1) for k, x in v['F_nom_N'].items()}, 'nomCd0.8', round(v['F_nom_Cd080_N']['max_0_0p8s'], 1), 't_first', json.dumps(v['t_first_s']))
    print('hot gas energy at flame-out J', [round(e) for e in E_gas])
    print('wrote', out_json, sha16(out_json), out_csv, sha16(out_csv))


if __name__ == '__main__':
    main(*sys.argv[1:4])
