"""Selected duty-cycle cases (Combustion v2) after the batch was cut to respect the 2-process compute cap.
usage: python run_dc_extra.py OUTDIR job [job ...]
jobs: b2band (DC-B2 x1.5, v1 grain) | maxthrust (A1 tank, 15/20/25 C x eq/E1e3/E1e2, v2 grain) | maps (throttle map + plant, v2 grain) |
      ground_g2 (DC-C and DC-D, straight port L200, nominal) | ground_<tag> with tag S230/S260 (straight port, nominal)
"""
from __future__ import annotations
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_dc as RD

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
fn = os.path.join(out, 'summary_v2.json')
S = json.load(open(fn)) if os.path.exists(fn) else {}
def save():
    json.dump(S, open(fn, 'w'), indent=1, default=float)
for job in sys.argv[2:]:
    if job == 'b2band':
        s, _, _ = RD.run_case('DC-B2', RD.FLIGHT['DC-B2'], 'neq', 1e3, band=1.5, outdir=out, cfg=RD.Q.VARIANTS['v1_helix_L200']); S[s['case']] = s; save()
    elif job == 'maxthrust':
        for T0 in (288.15, 293.15, 298.15):
            for tk, E in (('eq', 0), ('neq', 1e3), ('neq', 1e2)):
                s = RD.run_maxthrust(T0, tk, E, 2.059e-3, 1.3, out, 'A1tank'); S[s['case']] = s; save()
    elif job == 'maps':
        S['throttle_map_csv'] = RD.throttle_map(out); save()
        S['plant'] = RD.plant(out); save()
    elif job.startswith('ground_'):
        tag = job.split('_', 1)[1]
        L = {'g2': 0.20, 'S230': 0.23, 'S260': 0.26}[tag]
        cfg = dict(r_helix=0.0, F_helix=1.0, L_grain=L)
        for k, f in RD.GROUND.items():
            s, _, _ = RD.run_case(k + '-' + ('G2' if tag == 'g2' else tag), f, ground=True, outdir=out, cfg=cfg); S[s['case']] = s; save()
    elif job == 'maxthrust_BL':
        # baseline tank (lead decision 2026-10-12, CHANGELOG): 2.00 kg N2O in 3.17 L (85 % fill); V, m as in the GNC
        # duty_cycles v2 DC-A1 entry (0.0031700 m3, 2.0018 kg)
        for T0 in (288.15, 293.15, 298.15):
            for tk, E in (('eq', 0), ('neq', 1e3), ('neq', 1e2)):
                s = RD.run_maxthrust(T0, tk, E, 3.169952601830201e-3, 2.0018029785156246, out, 'BLtank'); S[s['case']] = s; save()
    elif job.startswith('gncv2wip'):
        # GNC duty_cycles v2 WORKING COPY (unpublished, snapshot 2026-10-12 19:15Z): S230 grain, each DC with its own tank
        inp = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'inputs', 'snap_gnc_v2wip_20261012T1915')
        names = {'DC-A1': 'DC-A1_full_flight_drogue_fins_300m_v2', 'DC-A2': 'DC-A2_full_flight_freefall_300m_v2',
                 'DC-B1': 'DC-B1_hop_100m_floor20_v2', 'DC-B2': 'DC-B2_hop_50m_floor20_v2'}
        plan = {'gncv2wip': [(k, 1.0) for k in names] + [('DC-B1', 1.5), ('DC-A1', 1.5), ('DC-A1', 0.6)],
                'gncv2wip_ground': []}[job]
        for k, band in plan:
            s, _, _ = RD.run_case(k + '-S230v2wip', names[k], 'neq', 1e3, band=band, outdir=out, inp=inp)
            S[s['case']] = s; save()
        if job == 'gncv2wip_ground':
            gn = {'DC-C': 'DC-C_tethered_hover_v2', 'DC-D': 'DC-D_static_fire_qualification_v2'}
            for k, f in gn.items():
                s, _, _ = RD.run_case(k + '-S230v2wip', f, ground=True, outdir=out, inp=inp); S[s['case']] = s; save()
