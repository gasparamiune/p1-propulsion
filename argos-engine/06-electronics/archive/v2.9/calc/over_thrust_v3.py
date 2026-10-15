#!/usr/bin/env python3
"""Over-thrust abort v3: v2 content (ADOPTED rule, latency chain from FC_THRUST receipt to valve action, IMU delay status) plus the
REV-GNC-1 RG-19 end-to-end budget for HIL (Electronics, 2026-10-13, v3; v2 and v1 kept).

RG-19 (reviews/REVIEW-GNC.md, MINOR, gate HIL): "An end-to-end budget with each term sourced, verified in HIL. T1-T4 log F_acc against
the load cell, including the low-frequency content." v3 adds: the term list from the thrust onset to the MV seated (IMU, FC, CAN, ECU,
latch, MV-P, tail-off), each with value, tag, source, owner and the HIL / bench measurement that verifies it; the step and stuck-pintle
exposure (GNC detection-from-onset p99 read from fc_thrust.json); the HIL set-up, stimulus, timestamps and pass rule; the common time
base the T1-T4 F_acc-vs-load-cell logging needs. SIL evidence from results/sil_v2p8_2 (firmware v2.8.2).

LEAD 2026-10-13 (CHANGELOG; GNC staging_v3.1 m2_fc_thrust v1.1): over-thrust abort ADOPTED: 650 N on 3 consecutive frames (20 ms) of a
first-order tau 20 ms accelerometer estimate, valid only airborne + engine lit + drogue released; stale or invalid -> flag only; the
FC-side abort decision comes 38.5 / 43 ms (mean / max) after a step. The lead asked Electronics for: (1) CAN transport + ECU scheduling
latency from FC_THRUST receipt to the abort action, (2) the IMU internal filter and sample delay (ADIS16470 datasheet), (3) whether the
check also runs with a valid Pc, (4) the valid-flag semantics.

Method (no other team's number typed in here):
  (1) CAN 2.0A worst-case frame time with stuff bits (Davis, Burns, Bril, Lukkien 2007, Real-Time Systems 35: C = (g + 8 s + 13 +
      floor((g + 8 s - 1) / 4)) bit times, g = 34 for 11-bit identifiers, interframe space included) for the frame lengths parsed from
      firmware/src/core/protocol.cpp; worst response of FC_THRUST (ID 0x024) = blocking by the longest frame in progress + one instance of
      each higher-priority FC frame that can be queued (CMD_FAST 0x020 at 500 Hz; ABORT 0x010 listed separately) + its own frame;
      ECU: RX drained at the next 1 kHz tick (config.h kDt_s) + core step (ASSUMED bound, not measured: HAL not written) and the MV
      latch gate written at the end of that tick (test_core group 6: abort and latch drop on the tick of the 3rd frame);
      valve: latch release (results/mv_latch_magnet_v1.json, worst 8.4 V / -10 C) + MV-P closing with dashpot (Mechanical
      mv_actuator_v1.json, ESTIMATE); SIL S6 v2.8.1 cases read from the run folder.
  (2) ADIS16470 values from the repository record public/engineering/vehicle/electronics-candidates.json (data sheet Rev. C read by
      the repo team 2026-10-03); the internal filter group delay / bandwidth are not in that record and the datasheet host was refused
      by the egress proxy in this session (2026-10-13): reported as UNKNOWN with the closure path.
Inputs: firmware/src/core/config.h, protocol.h, protocol.cpp; <engine-root>/01-systems-gnc/staging_v3.1/results/fc_thrust/fc_thrust.json;
<engine-root>/03-cad/calcs/mv_actuator_v1.json; results/mv_latch_magnet_v1.json; <repo>/public/engineering/vehicle/
electronics-candidates.json; results/<sil>/S6_aborts.json. Outputs: results/over_thrust_v2.json / .txt. Analysis, not validation.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FW = os.path.join(HERE, '..', 'firmware', 'src', 'core')
RES = os.path.join(HERE, '..', 'results')

CORE_STEP_MAX_S = 0.0002   # [ASSUMED] core step + output write on the i.MX RT1062 (to be measured: B-ECU-1 tick timing; HAL not written)


def cfg(name: str, kind: str = 'float') -> float:
    txt = open(os.path.join(FW, 'config.h'), encoding='utf-8').read()
    pat = (r'constexpr\s+(?:float|double)\s+' if kind == 'float' else r'constexpr\s+int\s+') + re.escape(name) + r'\s*=\s*([0-9.eE+-]+)f?\s*;'
    m = re.search(pat, txt)
    if not m:
        raise SystemExit(f'{name} not found in config.h')
    return float(m.group(1))


def frame_lengths() -> dict:
    h = open(os.path.join(FW, 'protocol.h'), encoding='utf-8').read()
    ids = {k: int(v, 16) for k, v in re.findall(r'(ID_[A-Z_]+)\s*=\s*(0x[0-9A-Fa-f]+)', h)}
    cpp = open(os.path.join(FW, 'protocol.cpp'), encoding='utf-8').read()
    lens = {k: int(v) for k, v in re.findall(r'f\.id\s*=\s*(ID_[A-Z_]+);\s*f\.len\s*=\s*(\d+);', cpp)}
    m = re.search(r'CAN 2\.0B\s+([0-9.]+)\s*Mbit/s', h)
    bitrate = float(m.group(1)) * 1e6 if m else float('nan')
    return {'ids': ids, 'lens': lens, 'bitrate_bps': bitrate}


def can_bits_worst(s: int, g: int = 34) -> int:
    return g + 8 * s + 13 + (g + 8 * s - 1) // 4


def can_bits_nominal(s: int, g: int = 34) -> int:
    return g + 8 * s + 13


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine-root', default=os.environ.get('ENGINE_ROOT', '/home/claude/work/shared-fallback/engine'))
    ap.add_argument('--repo', default='/home/claude/ARGOS-H1')
    ap.add_argument('--sil', default=os.path.join(RES, 'sil_v2p8_2'))
    a = ap.parse_args()

    thr = cfg('kOverThrust_N'); nfr = int(cfg('kOverThrustFrames', 'int')); rate = cfg('kFcThrustRate_Hz')
    stale = cfg('kFcThrustStale_s'); hold = cfg('kOverThrustTime_s'); dt = cfg('kDt_s'); t_sd = cfg('kShutdownTimeout_s')
    fl = frame_lengths(); ids, lens, br = fl['ids'], fl['lens'], fl['bitrate_bps']
    tb = 1.0 / br
    fct = 'ID_FC_THRUST'
    higher = sorted([k for k in ids if ids[k] < ids[fct] and k in lens], key=lambda k: ids[k])   # FC frames that win arbitration
    longest = max(lens.values())
    C = {k: can_bits_worst(lens[k]) * tb for k in lens}
    C_nom_fct = can_bits_nominal(lens[fct]) * tb
    blocking = can_bits_worst(longest) * tb
    interf_no_abort = sum(C[k] for k in higher if k != 'ID_ABORT')
    interf_abort = C.get('ID_ABORT', 0.0)
    can_worst = blocking + interf_no_abort + C[fct]
    can_worst_with_abort = can_worst + interf_abort
    ecu_worst = dt + CORE_STEP_MAX_S
    ecu_mean = 0.5 * dt + 0.5 * CORE_STEP_MAX_S

    gnc = json.load(open(os.path.join(a.engine_root, '01-systems-gnc', 'staging_v3.1', 'results', 'fc_thrust', 'fc_thrust.json'), encoding='utf-8'))
    lat = gnc['latency']['tau20ms']
    dec_mean, dec_max = lat['abort_decision_delay_step_to_2T_mean_max_s']
    mag = json.load(open(os.path.join(RES, 'mv_latch_magnet_v1.json'), encoding='utf-8'))
    t_rel = mag['selected']['release']['cold_8V4']['t_release_s']
    mv = json.load(open(os.path.join(a.engine_root, '03-cad', 'calcs', 'mv_actuator_v1.json'), encoding='utf-8'))
    t_close = mv['B_balanced_poppet_MVP']['closing_with_dashpot_s']

    # (2) IMU record (repository, read-only)
    imu = {'part': 'ADIS16470AMLZ', 'source': 'repo public/engineering/vehicle/electronics-candidates.json (data sheet Rev. C 2019-04 read by the repo team 2026-10-03)'}
    try:
        rec = json.load(open(os.path.join(a.repo, 'public', 'engineering', 'vehicle', 'electronics-candidates.json'), encoding='utf-8'))
        c = next(x for x in rec['candidates'] if 'ADIS16470' in x['identity']['partNumber'])
        tm = c['timing']
        imu.update({'status_in_repo': c['candidateStatus'], 'output_rate_Hz': [tm['outputRateHz']['value'], 'DATASHEET via repo record: ' + tm['outputRateHz']['condition']],
                    'sample_period_s': [1.0 / tm['outputRateHz']['value'], 'DERIVED 1 / output rate'],
                    'timestamp_quantum_s': [tm['timestampQuantumS']['value'], 'DATASHEET via repo record (TIME_STAMP LSB, scaled sync mode)'],
                    'system_latency_s': [tm['systemLatencyS']['value'], 'repo record: ' + tm['systemLatencyS'].get('reason', '')]})
    except (OSError, StopIteration, KeyError) as e:
        imu['error'] = f'record not readable: {e}'
    imu['internal_filter_group_delay_s'] = [None, 'UNKNOWN: not in the repo record; analog.com refused by the egress proxy on 2026-10-13 (not retried, '
                                            'not routed around). The FC owner fixes the filter / decimation setting; its group delay comes from data sheet '
                                            'Rev. C (or a measurement, bench plan B-FC-1) and adds to the GNC 38.5 / 43 ms']
    imu['sample_age_s'] = [[0.0, 1.0 / imu['output_rate_Hz'][0]] if 'output_rate_Hz' in imu else None,
                           'DERIVED: 0 if the FC reads on data-ready, up to one sample period if it polls asynchronously']

    # SIL v2.8.1 S6 over-thrust cases
    sil = {}
    p6 = os.path.join(a.sil, 'S6_aborts.json')
    if os.path.exists(p6):
        s6 = json.load(open(p6, encoding='utf-8'))
        for cse in s6['cases']:
            if any(k in cse['case'] for k in ('over_thrust', 'fc_bias', 'pc_reads_low', 'fc_estimate_stale')):
                sil[cse['case']] = {k: cse.get(k) for k in ('cause_name', 'inj_to_abort_s', 'inj_to_MV_latch_hw_off_s', 'inj_to_MV_closed_s',
                                                             'inj_to_ARM_bus_off_s', 'inj_to_pintle_closed_s', 'Pc_max_abs_Pa', 't_Pc_above_30bar_s',
                                                             'F_at_inj_N', 'F_max_after_inj_N', 'pass')}
    chain_mean = dec_mean + C_nom_fct + ecu_mean
    chain_max = dec_max + can_worst_with_abort + ecu_worst

    # ------------------------------------------------------------------ RG-19 end-to-end budget (v3)
    det = gnc.get('stuck_pintle_detection', {}).get('by_case', {})
    thr_i = int(round(thr))

    def det_case(F0, Ff, rate_):
        k = f'tau20ms|T{thr_i}|F0 {F0}|Ff {Ff}|rate {rate_}'
        return k, det.get(k)
    chl = os.path.join(a.engine_root, 'interfaces', 'CHANGELOG.md')
    comb_line = next((l for l in open(chl, encoding='utf-8') if '| combustion |' in l and 'v2.4 ANSWERS' in l), '')
    mt = re.search(r'tail-off\s+([0-9.]+)-([0-9.]+)\s*N s', comb_line)
    tail_Ns = [float(mt.group(1)), float(mt.group(2))] if mt else None
    mb = re.search(r'B-MV-1 close <=\s*([0-9.]+)\s*s', comb_line)
    mv_req = float(mb.group(1)) if mb else None
    T_ecu_can_max = can_worst_with_abort + ecu_worst
    T_ecu_can_mean = C_nom_fct + ecu_mean
    known_max = dec_max + T_ecu_can_max + t_rel + t_close
    known_mean = dec_mean + T_ecu_can_mean + t_rel + t_close
    sample_T = imu.get('sample_period_s', [None])[0]
    terms = [
        {'id': 'E0', 'term': 'IMU sample age at the FC read', 'mean_s': (0.5 * sample_T) if sample_T else None, 'max_s': sample_T,
         'tag': 'DERIVED (1 / output rate, repo record)', 'owner': 'FC owner (read on data-ready -> 0)',
         'verify': 'B-FC-1: IMU DR pin vs FC read GPIO on the logic analyser'},
        {'id': 'E1', 'term': 'IMU internal digital filter / decimation group delay', 'mean_s': None, 'max_s': None,
         'tag': 'UNKNOWN (ADIS16470 data sheet Rev. C not read: analog.com refused by the egress proxy; FC owner sets the filter)',
         'owner': 'FC owner + Electronics', 'verify': 'B-FC-1: step input (drop / pneumatic step fixture) on the flight IMU, DR edges vs a reference '
                                                         'accelerometer (or the data sheet value once read)'},
        {'id': 'E2', 'term': 'IMU SPI burst read + FC driver to the estimator', 'mean_s': None, 'max_s': None, 'tag': 'TO-DEFINE (FC software not written)',
         'owner': 'FC owner', 'verify': 'HIL-OT-1: FC GPIO toggles at read start / estimator input'},
        {'id': 'E3', 'term': 'FC estimator (tau 20 ms) + 650 N on 3 frames decision, from a thrust step', 'mean_s': dec_mean, 'max_s': dec_max,
         'tag': 'SIM (GNC m2_fc_thrust v1.1, rigid airframe)', 'owner': 'GNC', 'verify': 'HIL-OT-1: SPI-replayed sim6 F_acc step / ramp, FC decision GPIO'},
        {'id': 'E4', 'term': 'FC task scheduling (decision -> FC_THRUST in the CAN TX mailbox)', 'mean_s': None, 'max_s': None, 'tag': 'TO-DEFINE',
         'owner': 'FC owner', 'verify': 'HIL-OT-1: FC decision GPIO vs CAN analyser start-of-frame'},
        {'id': 'E5', 'term': 'CAN FC_THRUST worst response (incl. one ABORT frame)', 'mean_s': C_nom_fct, 'max_s': can_worst_with_abort,
         'tag': 'DERIVED (Davis et al. 2007, frame lengths parsed from protocol.cpp)', 'owner': 'Electronics', 'verify': 'B-ECU-1 / HIL-OT-1: CAN analyser timestamps'},
        {'id': 'E6', 'term': 'ECU receipt -> MV latch gate off (RX at the next 1 kHz tick + core step)', 'mean_s': ecu_mean, 'max_s': ecu_worst,
         'tag': 'DERIVED (tick, DESIGN) + ASSUMED core step (HAL not written)', 'owner': 'Electronics',
         'verify': 'B-ECU-1: CAN analyser end-of-frame vs scope on MVL_G (gate) over >= 1000 frames'},
        {'id': 'E7', 'term': 'MV latch release (8.4 V / -10 C worst)', 'mean_s': t_rel, 'max_s': t_rel, 'tag': 'DERIVED calc/mv_latch_magnet_v1 (estimate)',
         'owner': 'Electronics', 'verify': 'B-MV-1: latch coil current + poppet position switch on the scope'},
        {'id': 'E8', 'term': 'MV-P closing with dashpot', 'mean_s': t_close, 'max_s': t_close, 'tag': 'MECH mv_actuator_v1 ESTIMATE; COMB B-MV-1 bound '
         + (f'{mv_req:.2f} s' if mv_req else 'not parsed'), 'owner': 'Mechanical', 'verify': 'B-MV-1 (flowing, 0.05-0.26 kg/s per COMB)'},
        {'id': 'E9', 'term': 'tail-off after the MV seats (impulse)', 'impulse_Ns': tail_Ns, 'tag': 'COMB v2.4 (CHANGELOG combustion v2.4 ANSWERS, parsed)',
         'owner': 'Combustion', 'verify': 'T1-T4 hot fires: load cell'},
        {'id': 'E10', 'term': 'airframe axial modes between the engine and the IMU; low-frequency combustion oscillation', 'mean_s': None, 'max_s': None,
         'tag': 'UNKNOWN (rigid airframe in sim6; outside the vibration model)', 'owner': 'GNC / Mechanical / Combustion',
         'verify': 'T1-T4: F_acc vs load cell with the low-frequency content (5-200 Hz) on a common time base'}]
    stuck = {}
    for F0 in (500, 150):
        k, v = det_case(F0, 876, 2500)
        if v:
            p99 = v['t_detect_from_onset_p50_p99_max_s'][1]
            stuck[f'F0_{F0}N_to_876N_2500Nps'] = {
                'gnc_case': k, 'detect_from_onset_p99_s': p99, 'detect_from_true_crossing_p99_s': v['t_detect_from_true_crossing_p50_p99_max_s'][1],
                'onset_to_mv_seated_estimate_s': round(p99 + T_ecu_can_max + t_rel + t_close, 4),
                'onset_to_mv_seated_at_B_MV_1_bound_s': round(p99 + T_ecu_can_max + t_rel + mv_req, 4) if mv_req else None,
                'then_tail_off_Ns': tail_Ns,
                'excludes': 'E0-E2, E4, E10 (UNKNOWN / TO-DEFINE)'}
    rg19 = {
        'requirement': 'REV-GNC-1 RG-19 (MINOR, gate HIL): end-to-end budget, each term sourced, verified in HIL; T1-T4 log F_acc against the load cell incl. '
                       'low-frequency content',
        'terms': terms,
        'step_onset_to_mv_seated_known_terms_s': {'mean': round(known_mean, 5), 'max': round(known_max, 5),
                                                  'unknown_terms': ['E1 IMU filter', 'E2 SPI/driver', 'E4 FC scheduling', 'E10 airframe / oscillation'],
                                                  'tag': 'DERIVED sum of E3 + E5 + E6 + E7 + E8 (E0 sample age adds up to one IMU sample)'},
        'stuck_pintle_exposure': stuck,
        'allocation_proposed': {'E0+E1+E2_IMU_to_estimator_max_s': [0.005, 'DESIGN proposal (Electronics): to be accepted by the FC owner / GNC'],
                                'E4_FC_scheduling_max_s': [0.002, 'DESIGN proposal (Electronics)'],
                                'E5+E6_CAN_ECU_max_s': [round(T_ecu_can_max, 5), 'DERIVED (above)'],
                                'note': 'with these allocations the step onset -> MV seated budget is the known max + 7 ms; GNC adds the allocated '
                                        'terms to its decision delay when it re-evaluates the exposure'},
        'hil_plan': {
            'id': 'HIL-OT-1 (with B-ECU-1, B-FC-1, B-MV-1)',
            'setup': 'flight FC and flight ECU (Teensy 4.1 build) on the bench harness, flight CAN at 1 Mbit/s with the flight stub lengths and terminations; '
                     'CAN analyser with hardware timestamps (<= 1 us); 8-channel logic analyser / scope on IMU DR, FC read GPIO, FC decision GPIO, ECU MVL_G, '
                     'latch coil current, MV-P position switch; MV-P on its bench rig (B-MV-1, flowing water or N2 per Mechanical)',
            'stimulus': ['(a) SPI replay of sim6 F_acc traces into the FC estimator input (FC test hook): steps 500 -> 876 N, ramps 2500 / 3600 N/s from '
                         '150 and 500 N, healthy 571.5 N maxima for the no-trip check', '(b) flight IMU on a step fixture for E0/E1 (B-FC-1)',
                         '(c) FC_THRUST frames injected by the analyser directly to the ECU for E5/E6 alone (B-ECU-1)'],
            'measure': 'each term as an edge-to-edge time; 1000 repetitions per stimulus; report mean, p99, max',
            'pass': 'every measured term <= its budget max (or its allocation); end-to-end p99 <= the sum; no trip on the healthy replay; '
                    'a term over budget is reported with its measured value and goes back to the owner',
            'not_covered': 'airframe axial modes and combustion oscillation (E10): T1-T4 hot fires'},
        'common_time_base': {
            'need': 'T1-T4 compare F_acc (FC) with the load cell (stand DAQ) and the ECU log; today the FC, ECU and DAQ clocks are independent (open issue)',
            'proposal': 'the stand DAQ records the CAN bus through the analyser on the DAQ clock (FC_THRUST and TLM frames timestamped on the same clock as '
                        'the load cell) and one ECU GPIO sync pulse (1 Hz, edge logged by the ECU tick counter and by the DAQ); the FC logs its CAN TX '
                        'timestamps; residual alignment <= 1 ms [DESIGN]',
            'logging': 'load cell >= 1 kHz anti-aliased, F_acc at the FC frame rate plus its raw IMU samples, low-frequency content 5-200 Hz retained '
                       '(no high-pass) for RG-19 second action',
            'owner': 'Electronics (stand DAQ, ECU sync) + FC owner (FC log) + GNC (analysis)', 'tag': 'DESIGN, TO-AGREE'},
        'tags': 'terms tagged individually; nothing here is a measurement'}
    out = {
        'id': 'over_thrust', 'version': 'v3', 'date': '2026-10-13', 'script': 'calc/over_thrust_v3.py', 'supersedes': 'over_thrust_v2 (kept; v3 adds the RG-19 budget, SIL v2.8.2)',
        'rule_implemented_v2p8_1_unchanged_v2p8_2': {
            'v': f'abort OVER_THRUST when {nfr} consecutive fresh FC_THRUST frames carry the valid flag and a value > {thr:.0f} N while the ECU is in '
                 f'RUN in FLIGHT mode; fresh = received within {stale * 1e3:.0f} ms of the previous one (+1 us slack); the count restarts on a frame '
                 f'<= threshold, a frame with the flag clear, a gap > {stale * 1e3:.0f} ms or leaving RUN; the abort is taken on the tick that '
                 f'receives the {nfr}rd frame and drops the MV latch drive on that tick',
            'tag': 'LEAD 2026-10-13 ADOPTED (GNC m2_fc_thrust v1.1); firmware config.h kOverThrust_N / kOverThrustFrames / kFcThrustStale_s',
            'frame_rate_Hz': [rate, 'LEAD / GNC interface requirement (static_assert: (frames - 1) / rate = 20 ms)'], 'hold_s': [hold, 'LEAD'],
        },
        'item1_latency': {
            'can': {'bitrate_bps': [br, 'DESIGN (protocol.h)'], 'frame_bits_worst': {k: can_bits_worst(lens[k]) for k in lens},
                    'fc_thrust_frame_s': [C[fct], 'DERIVED worst stuffing'], 'fc_thrust_frame_nominal_s': [C_nom_fct, 'DERIVED no stuff bits'],
                    'blocking_longest_frame_s': [blocking, f'DERIVED {longest}-byte frame in progress (non-pre-emptive)'],
                    'higher_priority_fc_frames': {k: [hex(ids[k]), lens[k], C[k]] for k in higher},
                    'worst_response_s': [can_worst, 'DERIVED blocking + one CMD_FAST + own frame'],
                    'worst_response_with_abort_frame_s': [can_worst_with_abort, 'DERIVED + one ABORT frame queued (then the burn is ending anyway)']},
            'ecu': {'tick_s': [dt, 'DESIGN config.h kDt_s'], 'core_step_max_s': [CORE_STEP_MAX_S, 'ASSUMED (B-ECU-1 measures it on the Teensy)'],
                    'receipt_to_latch_gate_off_worst_s': [ecu_worst, 'DERIVED: RX drained at the next tick + core step; latch gate written at the end of that tick'],
                    'receipt_to_latch_gate_off_mean_s': [ecu_mean, 'DERIVED'],
                    'note': 'HAL not written: the RX-at-tick design and the core step time are requirements on the HAL until B-ECU-1 measures them'},
            'fc_thrust_receipt_to_latch_drive_off_worst_s': [can_worst_with_abort + ecu_worst, 'DERIVED (CAN worst incl. ABORT + ECU worst)'],
            'latch_release_s': [t_rel, 'DERIVED calc/mv_latch_magnet_v1 worst (8.4 V, -10 C), estimate'],
            'mv_p_closing_s': [t_close, 'MECH mv_actuator_v1 closing_with_dashpot_s, ESTIMATE (B-MV-1 gates it)'],
            'latch_off_to_mv_closed_s': [t_rel + t_close, 'DERIVED (SIL plant uses the same two values)'],
            'arm_bus': ('not dropped by the over-thrust decision (abort law: the pintle is driven closed on the ARM bus, the NC valve closes on the '
                        f'latch); the ARM bus drops at ABORT->SAFE: with a valid Pc when Pc < 3 bar abs (>= 50 ms), with an invalid Pc only at the '
                        f'{t_sd:.1f} s timeout (v2.8.1), earlier by the pintle monitor (no closing progress 0.1 s), the 60 ms Pc > 30 bar check (valid Pc) '
                        'or the hardware comparator; SIL numbers in sil_v2p8_1'),
            'chain_step_to_latch_drive_off_s': {'mean': [chain_mean, 'DERIVED GNC mean 38.5 ms + nominal CAN + mean ECU'],
                                                'max': [chain_max, 'DERIVED GNC max 43 ms + worst CAN incl. ABORT + worst ECU'],
                                                'excludes': 'IMU internal filter / sample delay (item 2, UNKNOWN) and FC task scheduling (FC owner)'},
            'chain_step_to_mv_closed_s': {'mean': [chain_mean + t_rel + t_close, 'DERIVED'], 'max': [chain_max + t_rel + t_close, 'DERIVED'],
                                          'excludes': 'same; the true thrust keeps flowing until the MV-P seats (the pintle is the failed part in a runaway)'},
            'gnc_inputs': {'decision_step_to_2T_mean_max_s': [[dec_mean, dec_max], 'GNC m2_fc_thrust v1.1 tau20ms (staging v3.1)'],
                           'frame_staleness_s': [lat['frame_staleness_s'], 'GNC'], 'gnc_latency_note': gnc.get('latency_note')},
        },
        'item2_imu': imu,
        'item3_pc_valid': {'v': 'IMPLEMENTED with a valid Pc as well (v2.8.1): covers an in-range wrong Pc, which the firmware over-pressure check and the '
                                'hardware comparator (same PC_SIG) cannot see; FLIGHT RUN only, never on the stand (strap STAND latched at ARM)',
                           'tag': 'DESIGN (LEAD: either choice acceptable; GNC 0/1000 healthy false aborts at >= 610 N)'},
        'item4_valid_flag': {'v': 'FC sets b0 only while airborne, engine lit (ECU RUN) and drogue released; the ECU additionally requires RUN, the FLIGHT '
                                  f'strap, freshness <= {stale * 1e3:.0f} ms and {nfr} consecutive frames; a stale stream or b0 = 0 never aborts: it clears '
                                  'the count, raises the log flag (seq2_flags b4 clear, fc_thr_dN 0xFFFF) and TLM fault bit only',
                             'tag': 'LEAD 2026-10-13 / firmware v2.8.1'},
        'sil_S6': {'run': os.path.relpath(a.sil, os.path.join(HERE, '..')), 'cases': sil},
        'rg19_end_to_end_budget': rg19,
        'sil_fc_model': 'v2.8.1 SIL: first-order tau 20 ms on the plant thrust (adopted estimate), 5 N rms noise [ASSUMED], 100 Hz; extra delay 0 '
                        '(IMU / FC scheduling unknown) except the 10 ms [ASSUMED] sensitivity case; v2.8 used a pure 20 ms delay',
        'limitations': ['CAN analysis assumes the FC queues frames in ID order with no FC-side transmit-buffer priority inversion (FC owner to confirm)',
                        'ECU core step time ASSUMED; HAL not written', 'IMU internal delay UNKNOWN', 'valve closing times are estimates (B-MV-1)',
                        'SIL plant and FC model are models, not hardware'],
    }
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, 'over_thrust_v3.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1)
    L = [f'over_thrust_v3 (2026-10-13): ADOPTED {thr:.0f} N on {nfr} consecutive fresh valid FC_THRUST frames ({hold * 1e3:.0f} ms at {rate:.0f} Hz), flight RUN, '
         'with or without a valid Pc',
         f'  CAN {br / 1e6:.0f} Mbit/s: FC_THRUST {lens[fct]} B = {can_bits_worst(lens[fct])} bits worst ({C[fct] * 1e6:.0f} us; nominal {C_nom_fct * 1e6:.0f} us); '
         f'worst response {can_worst * 1e6:.0f} us ({can_worst_with_abort * 1e6:.0f} us with an ABORT frame queued)',
         f'  ECU: receipt -> MV latch drive off <= {ecu_worst * 1e3:.2f} ms (mean {ecu_mean * 1e3:.2f} ms; core step {CORE_STEP_MAX_S * 1e3:.1f} ms ASSUMED)',
         f'  latch release {t_rel * 1e3:.1f} ms + MV-P closing {t_close * 1e3:.0f} ms (ESTIMATE) = {(t_rel + t_close) * 1e3:.1f} ms',
         f'  step -> latch drive off: mean {chain_mean * 1e3:.1f} ms, max {chain_max * 1e3:.1f} ms; step -> MV closed: mean {(chain_mean + t_rel + t_close) * 1e3:.1f} ms, '
         f'max {(chain_max + t_rel + t_close) * 1e3:.1f} ms (+ IMU filter UNKNOWN + FC scheduling)',
         f"  IMU {imu['part']}: output {imu.get('output_rate_Hz', ['?'])[0]} Hz (sample {imu.get('sample_period_s', [float('nan')])[0] * 1e3:.2f} ms); internal filter delay UNKNOWN"]
    L.append(f"  RG-19 step onset -> MV seated, known terms: mean {known_mean * 1e3:.1f} ms, max {known_max * 1e3:.1f} ms (+ UNKNOWN IMU filter, SPI/driver, FC scheduling, "
             f"airframe); tail-off {tail_Ns} N s")
    for k, v in stuck.items():
        L.append(f"  RG-19 stuck pintle {k}: detection p99 {v['detect_from_onset_p99_s']:.3f} s from onset -> MV seated {v['onset_to_mv_seated_estimate_s']:.3f} s "
                 f"(estimate), {v['onset_to_mv_seated_at_B_MV_1_bound_s']} s at the B-MV-1 bound")
    for k, v in sil.items():
        L.append(f"  SIL {k}: {v['cause_name']} abort +{(v['inj_to_abort_s'] or float('nan')) * 1e3:.0f} ms, latch off +{(v['inj_to_MV_latch_hw_off_s'] or float('nan')) * 1e3:.0f} ms, "
                 f"MV closed +{(v['inj_to_MV_closed_s'] or float('nan')) * 1e3:.0f} ms, ARM off +{(v['inj_to_ARM_bus_off_s'] or float('nan')) * 1e3:.0f} ms, "
                 f"F max {v['F_max_after_inj_N'] or float('nan'):.0f} N, Pc max {v['Pc_max_abs_Pa'] / 1e5:.1f} bar, >30 bar {(v['t_Pc_above_30bar_s'] or 0) * 1e3:.0f} ms, "
                 f"{'PASS' if v['pass'] else 'FAIL'}")
    txt = '\n'.join(L)
    with open(os.path.join(RES, 'over_thrust_v3.txt'), 'w', encoding='utf-8') as f:
        f.write(txt + '\n')
    print(txt)


if __name__ == '__main__':
    main()
