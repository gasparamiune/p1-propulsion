#!/usr/bin/env python3
"""Over-thrust abort v2: the ADOPTED rule, latency chain from FC_THRUST receipt to valve action, IMU delay status (Electronics,
2026-10-13, v2; v1 = provisional basis, kept).

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
    ap.add_argument('--engine-root', default='/mnt/project-files/engine')
    ap.add_argument('--repo', default='/home/claude/ARGOS-H1')
    ap.add_argument('--sil', default=os.path.join(RES, 'sil_v2p8_1'))
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
    out = {
        'id': 'over_thrust', 'version': 'v2', 'date': '2026-10-13', 'script': 'calc/over_thrust_v2.py', 'supersedes': 'over_thrust_v1 (provisional basis, kept)',
        'rule_implemented_v2p8_1': {
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
        'sil_v2p8_1_S6': sil,
        'sil_fc_model': 'v2.8.1 SIL: first-order tau 20 ms on the plant thrust (adopted estimate), 5 N rms noise [ASSUMED], 100 Hz; extra delay 0 '
                        '(IMU / FC scheduling unknown) except the 10 ms [ASSUMED] sensitivity case; v2.8 used a pure 20 ms delay',
        'limitations': ['CAN analysis assumes the FC queues frames in ID order with no FC-side transmit-buffer priority inversion (FC owner to confirm)',
                        'ECU core step time ASSUMED; HAL not written', 'IMU internal delay UNKNOWN', 'valve closing times are estimates (B-MV-1)',
                        'SIL plant and FC model are models, not hardware'],
    }
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, 'over_thrust_v2.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1)
    L = [f'over_thrust_v2 (2026-10-13): ADOPTED {thr:.0f} N on {nfr} consecutive fresh valid FC_THRUST frames ({hold * 1e3:.0f} ms at {rate:.0f} Hz), flight RUN, '
         'with or without a valid Pc',
         f'  CAN {br / 1e6:.0f} Mbit/s: FC_THRUST {lens[fct]} B = {can_bits_worst(lens[fct])} bits worst ({C[fct] * 1e6:.0f} us; nominal {C_nom_fct * 1e6:.0f} us); '
         f'worst response {can_worst * 1e6:.0f} us ({can_worst_with_abort * 1e6:.0f} us with an ABORT frame queued)',
         f'  ECU: receipt -> MV latch drive off <= {ecu_worst * 1e3:.2f} ms (mean {ecu_mean * 1e3:.2f} ms; core step {CORE_STEP_MAX_S * 1e3:.1f} ms ASSUMED)',
         f'  latch release {t_rel * 1e3:.1f} ms + MV-P closing {t_close * 1e3:.0f} ms (ESTIMATE) = {(t_rel + t_close) * 1e3:.1f} ms',
         f'  step -> latch drive off: mean {chain_mean * 1e3:.1f} ms, max {chain_max * 1e3:.1f} ms; step -> MV closed: mean {(chain_mean + t_rel + t_close) * 1e3:.1f} ms, '
         f'max {(chain_max + t_rel + t_close) * 1e3:.1f} ms (+ IMU filter UNKNOWN + FC scheduling)',
         f"  IMU {imu['part']}: output {imu.get('output_rate_Hz', ['?'])[0]} Hz (sample {imu.get('sample_period_s', [float('nan')])[0] * 1e3:.2f} ms); internal filter delay UNKNOWN"]
    for k, v in sil.items():
        L.append(f"  SIL {k}: {v['cause_name']} abort +{(v['inj_to_abort_s'] or float('nan')) * 1e3:.0f} ms, latch off +{(v['inj_to_MV_latch_hw_off_s'] or float('nan')) * 1e3:.0f} ms, "
                 f"MV closed +{(v['inj_to_MV_closed_s'] or float('nan')) * 1e3:.0f} ms, ARM off +{(v['inj_to_ARM_bus_off_s'] or float('nan')) * 1e3:.0f} ms, "
                 f"F max {v['F_max_after_inj_N'] or float('nan'):.0f} N, Pc max {v['Pc_max_abs_Pa'] / 1e5:.1f} bar, >30 bar {(v['t_Pc_above_30bar_s'] or 0) * 1e3:.0f} ms, "
                 f"{'PASS' if v['pass'] else 'FAIL'}")
    txt = '\n'.join(L)
    with open(os.path.join(RES, 'over_thrust_v2.txt'), 'w', encoding='utf-8') as f:
        f.write(txt + '\n')
    print(txt)


if __name__ == '__main__':
    main()
