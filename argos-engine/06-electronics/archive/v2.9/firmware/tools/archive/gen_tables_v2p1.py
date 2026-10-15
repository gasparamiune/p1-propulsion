"""Generate firmware constants and SIL plant tables from the published interfaces (Electronics v2).

Reads (never hard-codes other owners' numbers):
  interfaces/combustion.json          gas path, pintle, operating points, torch timing, plant-model ranges
  interfaces/ENGINE-BASELINE-v0.json  tank placeholder (V, load) - used only if gnc.json is absent
  interfaces/gnc.json                 RV-1 tank load/volume, gimbal range, mid-pivot hinge-moment terms, link-loss hold
  02-combustion/data/perf_table_*.json  CEA shifting-equilibrium c*, gamma, Cf_vac (referenced by combustion.json)
  06-electronics results/pintle_linkage_v2.json (this team's linkage choice)
  CoolProp 'NitrousOxide' (Lemmon & Span 2006 EOS) for saturation and two-phase injector flux tables
Writes:
  src/core/engine_params.h   (firmware: engine constants + pintle linkage + ignition timing)
  sil/plant_tables.h         (SIL plant: N2O saturation, Dyer flux G(T, Pc), CEA c*/gamma/Cf_vac grids)
  sil/gnc_tables.h           (SIL gimbal-axis load model from gnc.json)
  ../results/gen_tables_v2.json (provenance + fitted values)
Dyer model implemented independently here (not imported from Combustion code) so that agreement with
Combustion's throttle map is a cross-check of both: J. Dyer et al., AIAA 2007-5702.
Convention matched to Combustion m1_design.py v1: saturated inlet at the tank temperature (line loss does
not reduce the injector flux in that model; see REPORT open issue).
Usage: /opt/engine-venv/bin/python gen_tables.py [--engine-root /mnt/project-files/engine]
"""
from __future__ import annotations
import argparse, csv, datetime, hashlib, json, math, os, re, sys
import numpy as np
import CoolProp.CoolProp as CP

HERE = os.path.dirname(os.path.abspath(__file__))
FW = os.path.dirname(HERE)
RES = os.path.join(FW, '..', 'results')
FL = 'NitrousOxide'
AS = CP.AbstractState('HEOS', FL)
PA = 101325.0

def sha(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]

# ------------------------------------------------------------------------------------ N2O
def sat(T):
    AS.update(CP.QT_INPUTS, 0.0, T); p = AS.p(); rl = AS.rhomass(); ul = AS.umass(); hl = AS.hmass(); sl = AS.smass()
    AS.update(CP.QT_INPUTS, 1.0, T); rv = AS.rhomass(); uv = AS.umass(); hv = AS.hmass()
    return p, rl, rv, ul, uv, hl, hv, sl

def g_spi(rho, P1, P2):
    return math.sqrt(max(2 * rho * (P1 - P2), 0.0))

def g_hem(P1, h1, s1, P2, n=80):
    """Isentropic homogeneous-equilibrium flux, maximised over the throat pressure (choking)."""
    if P2 >= P1 * 0.9999:
        return 0.0
    ps = np.linspace(max(P2, 0.3e5), P1 * 0.9999, n)
    best, bp = 0.0, ps[0]
    for p in ps:
        AS.update(CP.PSmass_INPUTS, float(p), s1); dh = h1 - AS.hmass()
        if dh > 0:
            g = AS.rhomass() * math.sqrt(2 * dh)
            if g > best: best, bp = g, p
    # local parabolic refinement
    d = ps[1] - ps[0]
    for _ in range(25):
        cand = [max(P2, bp - d), bp, min(P1 * 0.9999, bp + d)]
        vals = []
        for p in cand:
            AS.update(CP.PSmass_INPUTS, float(p), s1); dh = h1 - AS.hmass()
            vals.append(AS.rhomass() * math.sqrt(2 * dh) if dh > 0 else 0.0)
        i = int(np.argmax(vals)); bp = cand[i]; best = max(best, vals[i]); d *= 0.5
    return best

def g_dyer_sat(T, P2):
    p, rl, rv, ul, uv, hl, hv, sl = sat(T)
    if P2 >= p:
        return 0.0
    k = 1.0                    # saturated inlet: kappa = sqrt((P1-P2)/(Pv-P2)) = 1
    return k / (1 + k) * g_spi(rl, p, P2) + 1 / (1 + k) * g_hem(p, hl, sl, P2)

# ------------------------------------------------------------------------------------ helpers
def carr(name, a, fmt='{:.6e}'):
    a = np.asarray(a)
    if a.ndim == 1:
        return f"constexpr double {name}[{a.shape[0]}] = {{" + ', '.join(fmt.format(v) for v in a) + "};\n"
    rows = ',\n  '.join('{' + ', '.join(fmt.format(v) for v in r) + '}' for r in a)
    return f"constexpr double {name}[{a.shape[0]}][{a.shape[1]}] = {{\n  {rows}}};\n"

def fcarr(name, a, fmt='{:.6e}f'):
    a = np.asarray(a)
    rows = ',\n  '.join('{' + ', '.join(fmt.format(v) for v in r) + '}' for r in a) if a.ndim == 2 else ', '.join(fmt.format(v) for v in a)
    if a.ndim == 1:
        return f"constexpr float {name}[{a.shape[0]}] = {{{rows}}};\n"
    return f"constexpr float {name}[{a.shape[0]}][{a.shape[1]}] = {{\n  {rows}}};\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine-root', default=os.environ.get('ENGINE_ROOT', '/mnt/project-files/engine'))
    ap.add_argument('--fast', action='store_true', help='coarse Dyer grid (debug)')
    a = ap.parse_args()
    ER = a.engine_root
    f_comb = os.path.join(ER, 'interfaces', 'combustion.json')
    f_base = os.path.join(ER, 'interfaces', 'ENGINE-BASELINE-v0.json')
    f_link = os.path.join(RES, 'pintle_linkage_v2.json')
    C = json.load(open(f_comb)); B = json.load(open(f_base)); LK = json.load(open(f_link))
    f_gnc = os.path.join(ER, 'interfaces', 'gnc.json')
    GN = json.load(open(f_gnc)) if os.path.exists(f_gnc) else None
    gp = C['gas_path']; inj = gp['injector']; noz = gp['nozzle']; gr = gp['grain']; op = C['operating_points']
    va = C['valves_and_actuators']; pm = va['plant_model_valve_to_Pc']; ig = C['igniter_electrical']
    perf_fn = os.path.join(ER, '02-combustion', 'data', 'perf_table_ABS_TYP_v1_shifting_v1.json')
    PT = json.load(open(perf_fn))
    prov = {'combustion.json': [C['version'], sha(f_comb)], 'ENGINE-BASELINE-v0.json': [B.get('version', 'v0'), sha(f_base)],
            'perf_table': [PT['version'], sha(perf_fn), PT['source']], 'pintle_linkage_v2.json': [LK['version'], sha(f_link)],
            'CoolProp': CP.get_global_param_string('version'), 'date': datetime.date.today().isoformat()}
    if GN is not None:
        prov['gnc.json'] = [GN['version'], sha(f_gnc)]
    # ---------------------------------------------------------------- GNC inputs (gimbal, link loss, tank)
    if GN is not None:
        gb = GN['requirements_to_engine']['gimbal'] if 'requirements_to_engine' in GN else None
        if gb is None:   # locate the 'gimbal' block wherever v1 put it
            def find(o, key):
                if isinstance(o, dict):
                    if key in o and isinstance(o[key], dict) and 'range_deg' in o[key]:
                        return o[key]
                    for v in o.values():
                        r = find(v, key)
                        if r is not None:
                            return r
                return None
            gb = find(GN, 'gimbal')
        rng_deg = gb['range_deg']['v']; hm = gb['hinge_moment_design_Nm']['v']; tm = hm['terms_mid']
        def findkey(o, key):
            if isinstance(o, dict):
                if key in o:
                    return o[key]
                for v in o.values():
                    r = findkey(v, key)
                    if r is not None:
                        return r
            return None
        llp = findkey(GN, 'link_loss_policy_in_RUN')['v']
        mm = re.search(r"HOLD[^0-9]*([\d.]+) s", llp)
        if not mm:
            raise SystemExit('gnc.json link_loss_policy_in_RUN: HOLD time not found: ' + llp)
        gnc = dict(range_deg=rng_deg, rate_min_dps=gb['rate_min_dps']['v'], bw_min_Hz=gb['bandwidth_min_Hz']['v'],
                   res_max_deg=gb['resolution_max_deg']['v'], backlash_max_deg=gb['backlash_max_deg']['v'],
                   latency_max_s=gb['latency_cmd_to_motion_max_s']['v'], hinge_mid_Nm=hm['mid_pivot'], hinge_fwd_Nm=hm['forward_pivot'],
                   I_pivot=tm['I_pivot_kgm2'], K_hose=tm['flex_hose_K_delta'] / math.radians(rng_deg), M_fric=tm['pivot_friction'],
                   M_mis=tm['thrust_misalignment_T_e'], M_side_floor=tm['nozzle_side_load_at_floor'],
                   K_axacc=tm['axial_accel_m_e_a_l_e_sin_delta'] / math.sin(math.radians(rng_deg)),
                   accel_min=gb['angular_accel_min_rad_s2']['v'], link_hold_landing_s=float(mm.group(1)),
                   rocking_min_Hz=findkey(GN, 'gimballed_engine_first_mode_min_Hz')['v'],
                   tank_m=findkey(GN, 'n2o_load_kg')['v'], tank_V=findkey(GN, 'tank_volume_L')['v'] * 1e-3)
    else:
        gnc = None

    # ---------------------------------------------------------------- engine constants
    At = noz['throat_area_m2']['v']; eps = noz['expansion_ratio']['v']; Ae = At * eps
    pts = op['throttle_points_20C_initial_port']
    # thrust model used by the ECU estimator: F = CfE * At * Pc - pa * Ae (least squares on Combustion's points)
    X = np.array([p['Pc_Pa'] * At for p in pts]); Y = np.array([p['F_N'] + PA * Ae for p in pts])
    CfE = float((X @ Y) / (X @ X)); fit_err = (CfE * X - PA * Ae) - np.array([p['F_N'] for p in pts])
    # piecewise-linear thrust table (replaces the single CfE in the ECU thrust<->Pc conversion; v2.1):
    # vacuum-equivalent thrust Fvac = F + pa*Ae is monotonic in Pc and makes both directions exact inverses
    srt = sorted(pts, key=lambda p: p['Pc_Pa'])
    thr_pc = [p['Pc_Pa'] for p in srt]; thr_fv = [p['F_N'] + PA * Ae for p in srt]
    lift25 = [p['pintle_lift_m'] for p in pts if abs(p['fraction'] - 0.25) < 1e-6][0]
    pc_floor = op['floor_stretch_12p5pct']['Pc_Pa']['v']
    tim = ig['timing_per_start_s']
    # pintle linkage (this team)
    sel = LK['selected']
    m = re.match(r"TOG r=([\d.]+)mm phi_c=([\d.]+)deg", sel)
    r_c = float(m.group(1)) * 1e-3; phi_c = math.radians(float(m.group(2))); lost = math.radians(5.0)
    stroke = va['pintle_actuator_requirements']['stroke_m']['v']
    phi_max = math.acos(math.cos(phi_c) - stroke / r_c)
    phi_n = 0.5 * ((phi_c - lost) + phi_max)
    spring = LK['spring']
    eng = dict(At=At, eps=eps, Ae=Ae, CfE=CfE, pc_max=op['max_thrust']['Pc_Pa']['v'], pc_meop=op['chamber_MEOP_Pa']['v'],
               tank_meop=op['tank_MEOP_Pa']['v'], dp_over_pc_min=None, lift25=lift25, pc_floor=pc_floor)
    rule = op['thrust_ceiling_rule']['v']
    mm = re.search(r"/ ?([\d.]+)", rule); ceil_div = float(mm.group(1)) if mm else 1.25
    eng['dp_over_pc_min'] = ceil_div - 1.0

    hdr = f"""// GENERATED by firmware/tools/gen_tables.py - DO NOT EDIT. Regenerate when an interface changes.
// Sources: combustion.json {prov['combustion.json'][0]} (sha {prov['combustion.json'][1]}), pintle_linkage_v2.json (Electronics),
//          date {prov['date']}. Units SI. Tags: [COMB] combustion.json, [ELEC] electronics design, [DERIVED] computed here.
#pragma once
namespace ecu {{
namespace eng {{
constexpr float kAt_m2 = {At:.6e}f;             // [COMB] nozzle throat area
constexpr float kEps = {eps:.4f}f;                 // [COMB] expansion ratio
constexpr float kAe_m2 = {Ae:.6e}f;             // [DERIVED] At * eps
constexpr float kCfVacEff = {CfE:.5f}f;           // [DERIVED] LSQ fit F = Cf*At*Pc - pa*Ae over combustion 20 C throttle points (max err {np.max(np.abs(fit_err)):.2f} N)
constexpr float kPamb_Pa = 101325.0f;          // [ELEC] ambient used for thrust<->Pc (FC may update)
// thrust <-> Pc table [DERIVED from combustion throttle_points_20C_initial_port]: Fvac = F + pa*Ae, Pc absolute.
// Linear extrapolation beyond the ends. Replace by the load-cell calibration after static fire (TS-cal).
constexpr int kNThr = {len(thr_pc)};
constexpr float kThrPcAbs_Pa[kNThr] = {{{', '.join(f'{v:.1f}f' for v in thr_pc)}}};
constexpr float kThrFvac_N[kNThr] = {{{', '.join(f'{v:.3f}f' for v in thr_fv)}}};
constexpr float kPcMaxAbs_Pa = {eng['pc_max']:.1f}f;    // [COMB] Pc at 500 N (absolute)
constexpr float kPcMeopAbs_Pa = {eng['pc_meop']:.1f}f;  // [COMB] chamber MEOP
constexpr float kPcFloorAbs_Pa = {pc_floor:.1f}f;  // [COMB] 12.5 % stretch floor at 20 C
constexpr float kTankMeop_Pa = {eng['tank_meop']:.1f}f;   // [COMB/LEAD] tank MEOP
constexpr float kDpOverPcMin = {eng['dp_over_pc_min']:.3f}f;        // [COMB] thrust ceiling rule: Pc <= P_inj_inlet/{ceil_div}
constexpr float kFmax_N = {op['max_thrust']['F_N']['v']:.1f}f;               // [COMB/REQ]
constexpr float kPintleStroke_m = {stroke:.6e}f;  // [COMB] mechanical stroke
constexpr float kPintleIgnitionLift_m = {lift25:.6e}f; // [COMB] lift for 25 % thrust at 20 C (ignition start point, ELEC choice)
// pintle linkage: crank-pin roller on flat follower, closing spring (pintle_linkage_v2: {sel})
constexpr float kCrankR_m = {r_c:.6e}f;          // [ELEC]
constexpr float kCrankPhiContact_rad = {phi_c:.6f}f; // [ELEC] crank angle (from dead centre) at needle contact/seat
constexpr float kCrankLostMotion_rad = {lost:.6f}f;  // [ELEC] commanded overtravel below contact when closed
constexpr float kCrankPhiNeutral_rad = {phi_n:.6f}f; // [DERIVED] crank angle at servo neutral (1500 us), centres the range
constexpr float kCrankPhiMax_rad = {phi_max:.6f}f;   // [DERIVED] crank angle at full stroke
constexpr float kSpringPreload_N = {spring['F0']:.2f}f;   // [ELEC request to COMB/MECH] closing spring preload at seat
constexpr float kSpringRate_Npm = {spring['k']:.1f}f;
// torch igniter sequence [COMB igniter_electrical.timing_per_start_s], times from IGNITION entry
constexpr float kTorchSolOpen_s = {tim['torch_solenoids_open']:.3f}f;
constexpr float kSparkStart_s = {tim['spark_train_start']:.3f}f;
constexpr float kTorchConfirmBy_s = {tim['torch_flame_confirmed_by']:.3f}f;
constexpr float kPintleToIgnitionLift_s = {tim['pintle_to_ignition_lift']:.3f}f;
constexpr float kMainPc90Expected_s = {tim['main_Pc_90pct_expected']:.3f}f;
constexpr float kTorchOff_s = {tim['torch_off']:.3f}f;
constexpr float kSparkRate_Hz = {ig['spark']['spark_rate_Hz']['v']:.1f}f;
constexpr float kSparkTrain_s = {ig['spark']['spark_train_duration_s']['v']:.3f}f;
// GNC requirements to the engine [GNC gnc.json {prov.get('gnc.json', ['absent'])[0]}]
constexpr float kGimbalRange_rad = {math.radians(gnc['range_deg']) if gnc else math.radians(7.0):.6f}f;   // [GNC] per-axis range (mid pivot)
constexpr float kGimbalRateMin_radps = {math.radians(gnc['rate_min_dps']) if gnc else math.radians(60.0):.6f}f;  // [GNC/REQ ENG-07]
constexpr float kLinkHoldLanding_s = {gnc['link_hold_landing_s'] if gnc else 0.3:.3f}f;   // [GNC] landing-burn link-loss HOLD time
}}  // namespace eng
}}  // namespace ecu
"""
    open(os.path.join(FW, 'src', 'core', 'engine_params.h'), 'w').write(hdr)

    # ---------------------------------------------------------------- SIL plant tables
    Ts = np.arange(240.0, 308.01, 1.0)
    S = np.array([sat(T)[:7] for T in Ts])
    if a.fast:
        Tg = np.arange(255.0, 305.01, 5.0); Pg = np.arange(1.0e5, 40.01e5, 1.0e5)
    else:
        Tg = np.arange(255.0, 305.01, 2.5); Pg = np.arange(1.0e5, 40.01e5, 0.5e5)
    G = np.zeros((len(Tg), len(Pg)))
    for i, T in enumerate(Tg):
        for j, P2 in enumerate(Pg):
            G[i, j] = g_dyer_sat(T, P2)
    PcB = np.array(PT['Pc_bar']) * 1e5; OF = np.array(PT['OF']); ie = PT['eps'].index(eps) if eps in PT['eps'] else None
    if ie is None:
        raise SystemExit(f'eps {eps} not on perf grid')
    cstar = np.array(PT['cstar']); gam = np.array(PT['gamma']); cfv = np.array(PT['Cf_vac'])[:, :, ie]
    tank = B['tank_v0']
    P = {
        'At': (At, 'COMB'), 'eps': (eps, 'COMB'), 'eta_cstar': (0.92, 'COMB (m1_design ASSUMED 0.92, band 0.85-0.96)'),
        'eta_cfv': (noz['divergence_loss_factor_lambda']['v'] * 0.992, 'COMB lambda x 0.992 (m1_design eta_cfv 0.975)'),
        'Ds_seat': (inj['seat_diameter_m']['v'], 'COMB'), 'cone_half': (math.radians(inj['needle_metering_cone_half_angle_deg']['v']), 'COMB'),
        'Cd': (inj['Cd']['v'], 'COMB ASSUMED 0.6-0.8'), 'd_stem': (inj['stem_diameter_through_seal_m']['v'], 'COMB'),
        'V_manifold': (inj['manifold_volume_m3']['v'], 'COMB'),
        'a_reg': (gr['regression_law']['a']['v'], 'COMB ASSUMED'), 'n_reg': (gr['regression_law']['n']['v'], 'COMB ASSUMED'),
        'helix': (gr['regression_law']['helix_factor']['v'], 'COMB ASSUMED'), 'rho_f': (gr['density_kg_m3']['v'], 'COMB ASSUMED'),
        'L_grain': (gr['length_m']['v'], 'COMB'), 'D_port0': (gr['port']['initial_diameter_m']['v'], 'COMB'),
        'V_free0': (gp_free := C['gas_path']['overall']['free_chamber_volume_initial_m3']['v'], 'COMB'),
        'tau_d_lo': (pm['tau_d_s']['v'][0], 'COMB ASSUMED'), 'tau_d_hi': (pm['tau_d_s']['v'][1], 'COMB ASSUMED'),
        'tau_f_lo': (pm['tau_f_s']['v'][0], 'COMB DERIVED'), 'tau_f_hi': (pm['tau_f_s']['v'][1], 'COMB DERIVED'),
        'tank_V': ((gnc['tank_V'], 'GNC RV-1 tank_volume_L') if gnc else (tank['volume_m3'], 'LEAD v0 placeholder')),
        'tank_m': ((gnc['tank_m'], 'GNC RV-1 n2o_load_kg') if gnc else (tank['N2O_load_kg'], 'LEAD v0 placeholder')),
        'pc_meop': (op['chamber_MEOP_Pa']['v'], 'COMB'),
    }
    out = [f"// GENERATED by firmware/tools/gen_tables.py - DO NOT EDIT. SIL plant tables (not flight code).\n"
           f"// combustion.json {prov['combustion.json'][0]} sha {prov['combustion.json'][1]}; perf table {prov['perf_table'][0]} sha {prov['perf_table'][1]} ({prov['perf_table'][2]});\n"
           f"// N2O: CoolProp {prov['CoolProp']} NitrousOxide (Lemmon & Span 2006). Dyer flux: saturated inlet at tank T (Combustion v1 convention).\n",
           "#pragma once\nnamespace sil {\nnamespace tab {\n"]
    for k, (v, tag) in P.items():
        out.append(f"constexpr double k_{k} = {v:.8e};   // [{tag}]\n")
    out.append(f"// saturation table, T = {Ts[0]:.1f}..{Ts[-1]:.1f} K step 1 K: P, rho_l, rho_v, u_l, u_v, h_l, h_v\n")
    out.append(f"constexpr int kNsat = {len(Ts)};\nconstexpr double kSatT0 = {Ts[0]:.2f}, kSatDT = 1.0;\n")
    out.append(carr('kSat', S))
    out.append(f"// Dyer mass flux [kg/m2/s] G(T_tank, Pc); T = {Tg[0]:.1f}..{Tg[-1]:.1f} step {Tg[1]-Tg[0]:.2f} K, Pc = {Pg[0]:.0f}..{Pg[-1]:.0f} step {Pg[1]-Pg[0]:.0f} Pa (abs)\n")
    out.append(f"constexpr int kNGT = {len(Tg)}, kNGP = {len(Pg)};\nconstexpr double kGT0 = {Tg[0]:.2f}, kGDT = {Tg[1]-Tg[0]:.3f}, kGP0 = {Pg[0]:.1f}, kGDP = {Pg[1]-Pg[0]:.1f};\n")
    out.append(carr('kG', G, '{:.5e}'))
    out.append(f"// CEA (shifting) on log(Pc) x O/F grid; eps = {eps} for Cf_vac\n")
    out.append(f"constexpr int kNCP = {len(PcB)}, kNOF = {len(OF)};\n")
    out.append(carr('kCeaPc', PcB, '{:.1f}')); out.append(carr('kCeaOF', OF, '{:.3f}'))
    out.append(carr('kCstar', cstar, '{:.3f}')); out.append(carr('kGamma', gam, '{:.5f}')); out.append(carr('kCfVac', cfv, '{:.5f}'))
    out.append("}  // namespace tab\n}  // namespace sil\n")
    open(os.path.join(FW, 'sil', 'plant_tables.h'), 'w').write(''.join(out))

    # ---------------------------------------------------------------- SIL gimbal-axis load model (gnc.json)
    g = gnc or dict(I_pivot=0.1143, K_hose=0.2 * 180 / math.pi, M_fric=0.3, M_mis=0.5, M_side_floor=0.0, K_axacc=2.19 / math.radians(7.0),
                    hinge_mid_Nm=11.7, hinge_fwd_Nm=11.7, range_deg=7.0, rate_min_dps=60.0, bw_min_Hz=8.0, res_max_deg=0.1,
                    backlash_max_deg=0.1, latency_max_s=0.01, accel_min=52.0, rocking_min_Hz=25.0, link_hold_landing_s=0.3)
    src = f"gnc.json {prov['gnc.json'][0]} sha {prov['gnc.json'][1]}" if gnc else "gnc.json ABSENT: electronics first_pass_v1 ASSUMED values"
    gh = [f"// GENERATED by firmware/tools/gen_tables.py - DO NOT EDIT. SIL gimbal-axis load model (mid pivot) from {src}.\n",
          "#pragma once\nnamespace sil {\nnamespace gnc {\n"]
    rows = [('I_pivot_kgm2', g['I_pivot'], 'GNC terms_mid.I_pivot_kgm2 (mass ledger ASSUMED; mechanical.json replaces)'),
            ('K_hose_Nm_per_rad', g['K_hose'], 'GNC flex_hose_K_delta / range (hose stiffness ASSUMED by GNC)'),
            ('M_fric_Nm', g['M_fric'], 'GNC pivot_friction'),
            ('M_mis_full_Nm', g['M_mis'], 'GNC thrust_misalignment_T_e at full thrust'),
            ('M_side_floor_Nm', g['M_side_floor'], 'GNC nozzle_side_load_at_floor (separation side load; disturbance)'),
            ('K_axacc_Nm_per_rad', g['K_axacc'], 'GNC axial_accel term / sin(range)'),
            ('hinge_design_mid_Nm', g['hinge_mid_Nm'], 'GNC hinge_moment_design mid pivot (linear worst-case sum incl. inertia)'),
            ('hinge_design_fwd_Nm', g['hinge_fwd_Nm'], 'GNC hinge_moment_design forward pivot'),
            ('range_deg', g['range_deg'], 'GNC range'), ('rate_min_dps', g['rate_min_dps'], 'GNC/ENG-07'),
            ('bw_min_Hz', g['bw_min_Hz'], 'GNC/ENG-07'), ('res_max_deg', g['res_max_deg'], 'GNC/ENG-07'),
            ('backlash_max_deg', g['backlash_max_deg'], 'GNC'), ('latency_max_s', g['latency_max_s'], 'GNC'),
            ('accel_min_radps2', g['accel_min'], 'GNC'), ('rocking_min_Hz', g['rocking_min_Hz'], 'GNC/ENG-11')]
    for k, v, tag in rows:
        gh.append(f"constexpr double k_{k} = {v:.6e};   // [{tag}]\n")
    gh.append("}  // namespace gnc\n}  // namespace sil\n")
    open(os.path.join(FW, 'sil', 'gnc_tables.h'), 'w').write(''.join(gh))

    # ---------------------------------------------------------------- cross-check: my Dyer vs Combustion's throttle-map flux
    chk = []
    rows = list(csv.DictReader(l for l in open(op['throttle_map_csv']) if not l.startswith('#')))
    for r in rows:
        T = float(r['T_tank']); Pc = float(r['Pc']); h = float(r['h']); mox = float(r['mox'])
        Ds = P['Ds_seat'][0]; al = P['cone_half'][0]
        s = h * math.sin(al); A = math.pi * s * (Ds - s * math.cos(al))
        g = g_dyer_sat(T, Pc)
        chk.append(dict(T=T, frac=float(r['frac']), mox_comb=mox, mox_elec=P['Cd'][0] * A * g, err_pct=100 * (P['Cd'][0] * A * g / mox - 1)))
    res = dict(id='gen_tables', version='v2.1', provenance=prov, CfVacEff=CfE, CfVacEff_fit_err_N=fit_err.tolist(),
               thrust_table=dict(Pc_abs_Pa=thr_pc, Fvac_N=thr_fv, note='ECU thrust<->Pc uses this table from v2.1 (exact at the Combustion points)'),
               gnc_inputs=gnc,
               pintle=dict(r_c=r_c, phi_c_deg=math.degrees(phi_c), lost_deg=5.0, phi_max_deg=math.degrees(phi_max), phi_neutral_deg=math.degrees(phi_n)),
               dyer_crosscheck=chk, max_abs_err_pct=max(abs(c['err_pct']) for c in chk))
    json.dump(res, open(os.path.join(RES, 'gen_tables_v2.json'), 'w'), indent=1)
    print(json.dumps({k: res[k] for k in ('CfVacEff', 'pintle', 'max_abs_err_pct')}, indent=1))
    for c in chk:
        print(f"T={c['T']:.2f} frac={c['frac']:.3f} mox comb={c['mox_comb']:.5f} elec={c['mox_elec']:.5f} err={c['err_pct']:+.2f}%")

if __name__ == '__main__':
    main()
