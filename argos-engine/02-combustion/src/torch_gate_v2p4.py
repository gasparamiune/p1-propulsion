"""Torch-confirmation gate kTorchConfirmBy_s (Combustion v2.4; LEAD 2026-10-13: Electronics v2.8 proposes 0.16 s, provisional
until Combustion confirms and publishes it).

E0 -> E1 = solenoid opening U(0.005, 0.020) s + torch light U(0.02, 0.10) s + flame detection U(0.005, 0.030) s, the ASSUMED
distributions of start_latency_v2p4 (no ignition data; IGN-1 replaces them). The sum is bounded at 0.150 s by construction,
so the gate is set at that bound plus a 10 ms allowance for the ECU sampling and debounce (Electronics: 10 ms persistence
is inside E1's detection term; the allowance covers scheduling). 1e6 samples, seed 2024.
usage: python -I torch_gate_v2p4.py OUTDIR
"""
from __future__ import annotations
import json, os, sys
sys.dont_write_bytecode = True
import numpy as np


def main(outdir):
    rng = np.random.default_rng(2024); N = 1_000_000
    e1 = rng.uniform(0.005, 0.020, N) + rng.uniform(0.02, 0.10, N) + rng.uniform(0.005, 0.030, N)
    ex = {f'{g:.3f}': float(np.mean(e1 > g)) for g in (0.090, 0.100, 0.110, 0.120, 0.130, 0.140, 0.145, 0.150, 0.160)}
    q = {p: float(np.percentile(e1, p)) for p in (50, 95, 99, 99.9)}
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/torch_gate_v2p4.py',
               distributions='ASSUMED (start_latency_v2p4): solenoid U(5,20) ms + torch light U(20,100) ms + detection U(5,30) ms',
               samples=N, seed=2024, E0_E1_s=dict(median=q[50], p95=q[95], p99=q[99], p999=q[99.9], max=float(e1.max()), bound=0.150),
               P_exceed=ex, gate_s=0.16, gate_basis='bound 0.150 s + 10 ms ECU allowance (DERIVED); conditional on IGN-1 measuring the three delays',
               tag='SIM on ASSUMED distributions')
    fn = os.path.join(outdir, 'torch_gate_v2p4.json')
    json.dump(out, open(fn, 'w'), indent=1)
    print(json.dumps(out['E0_E1_s']), json.dumps(ex)); print('wrote', fn)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
