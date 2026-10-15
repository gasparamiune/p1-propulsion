"""REV-COMB-3 reviewer script: unpurged relight start, outcome classes (independent re-derivation of REPORT v2.4a §2.8,
Tables 2.16 / 2.17, data/v2p4a/unpurged_outcomes_v2p4a.json 18a639d61b58ce8a).

Not a copy of the author's code.  Same stated model (author: SIM on ASSUMED delays + DERIVED line states), different numerics:
  * deterministic quadrature instead of Monte Carlo.  n_run = ig + tc, with tc one of the 54 pool confirmation times of
    start_latency_v2p4 (equal weight) and ig ~ U(0.05, 0.30); the exact CDF of n_run is integrated on a midpoint grid of NK cells;
  * own parse of the PURGE NOT RUN records ("nopurge|...") from the raw trade file, streamed;
  * own flow integral G(t) = int_0^t phi(F(t')) dt' on a 1e-5 s grid, phi(F) = mdot_ox(F) / mdot_ox(62.5 N) of the S230 map;
  * a light is followed through ALL later voids of its sequence (C1, then S2 and C2), not only the first one;
  * adds the drogue-release hold H (release at E2 + H instead of the first 10 ms frame) and reports P(released, then A3 | H) and
    the latest A3 trip time in the population.
Model as stated by the author (REPORT §2.8):
  t_lift = T_cmd + h_ign / V_pintle + 0.010 s; base (E1 -> E2 with liquid at the pintle) = t_lift + ig + tc; n_run = ig + tc is the
  liquid-flow time needed for light + confirmation.  Sequence P1 / S1 / C1 / S2 / C2 [cm3] (vapour / liquid / vapour / liquid /
  vapour); vapour passes at PURGE s/cm3, liquid at DEAD s/cm3 (lift flow).  paused: the ignition clock pauses in a void; restart:
  it restarts after a void (the liquid already spent is lost).  Light iff E1 -> E2 <= W = 0.65 s.  After E2 the flow follows the
  2500 N/s ramp from 62.5 N to F_cmd (volumetric flow x phi(F)) or stays at the lift.  A void that lasts >= 22 ms trips A3 at
  arrival + 22 ms.  Release at the first frame (10 ms) after E2: A3_BEFORE_RELEASE if the tripping void arrives before 10 ms,
  RELEASED_THEN_A3 otherwise; SUCCESS if no void after the light trips A3.
usage: python -I r3_unpurged_classes.py DATA_V2_V2P4 DATA_V2P4 THROTTLE_MAP_S230 AUTHOR_OUTCOMES_JSON OUT_JSON
"""
import gzip, hashlib, json, math, os, re, sys
import numpy as np

d1, d2, fmap, faut, out = sys.argv[1:6]
H16 = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
EXP = {os.path.join(d1, 'start_latency_v2p4.json'): '809491fd86b91439',
       os.path.join(d1, 'relight_vapour_order_v2p4.json'): '78120ff97c0ac8dc',
       os.path.join(d2, 'rg01_line_states_v2p4.json'): '2939549811d4c381',
       os.path.join(d2, 'purge_duration_v2p4_trade.json.raw.json.gz'): '02c30eb2e6569e8d',
       fmap: '4f2e6d846f7253da', faut: '18a639d61b58ce8a'}
for p, h in EXP.items():
    assert H16(p) == h, (p, H16(p))
SLJ = json.load(open(os.path.join(d1, 'start_latency_v2p4.json')))
VO = json.load(open(os.path.join(d1, 'relight_vapour_order_v2p4.json')))
RG = json.load(open(os.path.join(d2, 'rg01_line_states_v2p4.json')))
AU = json.load(open(faut))

W, A3D, FRAME, RAMP, FL = 0.65, 0.022, 0.010, 2500.0, 62.5
PURGE, DEAD = VO['purge_s_per_cm3'], VO['liquid_plug_dead_time_s_per_cm3']
C = SLJ['constants']
h_ign = SLJ['ignition_lifts']['A1_relight|0.125']['lift_m']
t_lift = C['T_cmd_s'] + h_ign / C['V_pintle_m_s'] + 0.010
assert abs(t_lift - RG['t_lift_s']) < 1e-12 and abs(PURGE - RG['PURGE_s_per_cm3']) < 1e-15, (t_lift, RG['t_lift_s'])
pool = [r for r in SLJ['part1_runs']['v'] if r['state'] == 'A1_relight' and r['frac'] == 0.125 and r['ramp'] == 2500.0
        and r['F_cmd'] in (200.0, 500.0) and r.get('loop_K', 0.0) == 15.0]
TC = np.array([r['t_conf_s'] for r in pool if r['t_conf_s'] is not None], float)
FC = sorted({r['F_cmd'] for r in pool if r['t_conf_s'] is not None})

# ---- exact n_run distribution on a midpoint grid
NK = 40000
lo, hi = TC.min() + 0.05, TC.max() + 0.30
edges = np.linspace(lo, hi, NK + 1)
cdf = lambda x: np.clip((x[:, None] - TC[None, :] - 0.05) / 0.25, 0.0, 1.0).mean(axis=1)
WGT = np.diff(cdf(edges)); NR = 0.5 * (edges[1:] + edges[:-1])
assert abs(WGT.sum() - 1.0) < 1e-12

# ---- flow integral from the S230 map (mdot_ox depends on F only in this map; checked)
rows = [l.strip().split(',') for l in open(fmap) if l.strip() and not l.startswith('#')]
hd = rows[0]; ix = {k: hd.index(k) for k in ('P_tank_Pa', 'D_port_m', 'frac', 'F_N', 'mdot_ox')}
byfrac = {}
for r in rows[1:]:
    byfrac.setdefault(float(r[ix['frac']]), []).append(float(r[ix['mdot_ox']]))
MAP_SPREAD = max((max(v) - min(v)) / min(v) for v in byfrac.values())     # mdot_ox at one frac across P_tank and D_port
sel = sorted((float(r[ix['F_N']]), float(r[ix['mdot_ox']])) for r in rows[1:]
             if abs(float(r[ix['P_tank_Pa']]) - 4.5e6) < 1 and abs(float(r[ix['D_port_m']]) - 0.030) < 1e-9)
Fm = np.array([a for a, _ in sel]); Mm = np.array([b for _, b in sel])
phi = lambda F: np.interp(F, Fm, Mm) / np.interp(FL, Fm, Mm)
DT = 1e-5; tg = np.arange(0.0, 4.0 + DT / 2, DT)
G = {None: tg.copy()}
for Fc in (200.0, 500.0):
    ph = phi(np.minimum(FL + RAMP * tg, Fc))
    G[Fc] = np.concatenate([[0.0], np.cumsum(0.5 * (ph[1:] + ph[:-1]) * DT)])
Ginv = lambda Fc, g: np.interp(g, G[Fc], tg)
MODES = {'lift_flow_held': None, 'ramp_to_200N': 200.0, 'ramp_to_500N': 500.0}


def light(seq, conv, nr):
    """E1->E2 and the position of the light: slug index (1, 2, 3 = continuous) and rem = lift-seconds of liquid left in it."""
    P1, S1, C1, S2, C2 = seq
    if C1 <= 0.0 and C2 > 0.0:              # S1 and S2 contiguous
        S1, S2, C1, C2 = S1 + S2, 0.0, C2, 0.0
    t1, t2 = S1 * DEAD, S2 * DEAD
    if C1 <= 0.0 and C2 <= 0.0:
        return t_lift + nr + PURGE * P1, np.full(nr.shape, 3), np.zeros_like(nr)
    if conv == 'paused':
        e = t_lift + nr + PURGE * P1 + (nr > t1) * PURGE * C1 + (nr > t1 + t2) * PURGE * C2
        slug = np.where(nr <= t1, 1, np.where(nr <= t1 + t2, 2, 3))
        rem = np.where(slug == 1, t1 - nr, np.where(slug == 2, t1 + t2 - nr, 0.0))
    else:
        e = t_lift + nr + PURGE * P1 + (nr > t1) * (t1 + PURGE * C1 + (nr > t2) * (t2 + PURGE * C2))
        slug = np.where(nr <= t1, 1, np.where(nr <= t2, 2, 3))
        rem = np.where(slug == 1, t1 - nr, np.where(slug == 2, t2 - nr, 0.0))
    if C2 <= 0.0:                             # nothing follows slug 2
        slug = np.where(slug == 2, 3, slug)
    return e, slug, rem


def follow(seq, conv, nr, Fc, all_voids=True):
    """Per n_run cell: lit, trip time after E2 (inf if none), arrival of the tripping void, index of that void (1 or 2)."""
    P1, S1, C1, S2, C2 = seq
    if C1 <= 0.0 and C2 > 0.0:
        S1, S2, C1, C2 = S1 + S2, 0.0, C2, 0.0
    e, slug, rem = light(seq, conv, nr)
    lit = e <= W
    ttrip = np.full(nr.shape, np.inf); tarr = np.full(nr.shape, np.inf); which = np.zeros(nr.shape, int)
    first_dip = np.zeros(nr.shape, bool)
    voids = []                                  # (mask, offset lift-seconds, volume, index)
    m1 = lit & (slug == 1); m2 = lit & (slug == 2)
    if C1 > 0.0:
        voids.append((m1, rem, C1, 1))
        if all_voids and C2 > 0.0:
            voids.append((m1, rem + PURGE * C1 + S2 * DEAD, C2, 2))
    if C2 > 0.0:
        voids.append((m2, rem, C2, 2))
    for m, off, V, k in voids:
        ta = Ginv(Fc, off); te = Ginv(Fc, off + PURGE * V); dg = te - ta
        trip = m & (dg >= A3D) & ~np.isfinite(ttrip)
        first_dip |= m & (dg < A3D) & (k == 1)
        ttrip = np.where(trip, ta + A3D, ttrip); tarr = np.where(trip, ta, tarr); which = np.where(trip, k, which)
    return lit, ttrip, tarr, which, first_dip


def classify(fo, hold=FRAME):
    lit, ttrip, tarr, which, dip = fo
    trip = np.isfinite(ttrip)
    rel = trip & (tarr >= hold)                 # the tripping void arrives after the release (Pc still >= 3 bar at release)
    rel_cons = trip & (ttrip > hold)            # conservative: release at E2 + hold whenever A3 has not yet tripped
    w = lambda m: float(WGT[m].sum())
    r = dict(P_no_light=w(~lit), P_A3_before_release=w(trip & ~rel), P_released_then_A3=w(rel), P_success=w(lit & ~trip),
             P_light=w(lit), P_released_then_A3_conservative=w(rel_cons), P_trip_on_second_void=w(trip & (which == 2)))
    assert abs(r['P_no_light'] + r['P_A3_before_release'] + r['P_released_then_A3'] + r['P_success'] - 1.0) < 1e-9
    if trip.any():
        r['A3_trip_after_E2_s'] = dict(min=float(ttrip[trip].min()), max=float(ttrip[trip].max()),
                                       arrival_max=float(tarr[trip].max()))
    return r


def classes(seq, conv, Fc, hold=FRAME, all_voids=True):
    return classify(follow(seq, conv, NR, Fc, all_voids), hold)


res = dict(script='r3_unpurged_classes.py', inputs={os.path.basename(p): h for p, h in EXP.items()},
           constants=dict(W=W, A3_detect=A3D, frame=FRAME, ramp_N_s=RAMP, F_lift=FL, PURGE=PURGE, DEAD=DEAD, t_lift=t_lift,
                          n_pool=len(TC), pool_F_cmd=FC, tc_range=[float(TC.min()), float(TC.max())], NK=NK,
                          phi_200=float(phi(200.0)), phi_500=float(phi(500.0)), map_mdot_spread_rel=MAP_SPREAD))

# ---- (1) named states, both conventions, three flow modes; compare with the author
named = {}
ST = RG['part2_line_states_for_gnc']['v']
for key in AU['named_states']:
    s = ST[key]; seq = tuple(s['sequence_P1_S1_C1_S2_C2_cm3'])
    named[key] = dict(sequence=list(seq), published_P_abort=s['P_abort_W0p65'], published_convention=s['convention'])
    for conv in ('paused', 'restart'):
        for mo, Fc in MODES.items():
            mine = classes(seq, conv, Fc)
            mine_first = classes(seq, conv, Fc, all_voids=False)
            au = AU['named_states'][key][conv][mo]
            named[key][f'{conv}|{mo}'] = dict(mine=mine, mine_first_void_only=mine_first,
                                             author={k: au[k] for k in ('P_no_light', 'P_A3_before_release', 'P_released_then_A3', 'P_success')},
                                             max_abs_diff=max(abs(mine_first[k] - au[k]) for k in ('P_no_light', 'P_A3_before_release',
                                                                                                    'P_released_then_A3', 'P_success')))
    pa = named[key][f"{s['convention'].split(' ')[0]}|lift_flow_held"]['mine']['P_no_light']
    named[key]['P_no_light_vs_published'] = pa - s['P_abort_W0p65']
res['named_states'] = named

# ---- analytic margins at the LO worst unlined state (paused): a light after the first void needs W >= this
P1, S1, C1, S2, C2 = ST['purge_not_run_unlined_LO_0-2deg_worst']['sequence_P1_S1_C1_S2_C2_cm3']
res['LO_worst_analytic'] = dict(
    t1_s=S1 * DEAD, W_needed_for_light_after_void_s=t_lift + S1 * DEAD + PURGE * (P1 + C1),
    gap_lift_flow_s=PURGE * C1, gap_at_constant_500N_s=PURGE * C1 / float(phi(500.0)),
    phi_needed_for_gap_below_A3=PURGE * C1 / A3D,
    P_light_exact_n_run_le_t1=float(WGT[NR <= S1 * DEAD].sum()),
    P_no_light_exact=float(WGT[NR > S1 * DEAD].sum()))

# ---- (2) population: all PURGE NOT RUN records at 0 and 2 deg, own streamed parse
rx = re.compile(r'"(nopurge\|[^"]*)":(\{[^{}]*\})')
recs, buf = {}, ''
with gzip.open(os.path.join(d2, 'purge_duration_v2p4_trade.json.raw.json.gz'), 'rt') as fh:
    while True:
        ch = fh.read(1 << 24)
        if not ch:
            break
        buf += ch
        last = 0
        for m in rx.finditer(buf):
            recs[m.group(1)] = json.loads(m.group(2)); last = m.end()
        buf = buf[max(last, len(buf) - 4096):]
for m in rx.finditer(buf):
    recs[m.group(1)] = json.loads(m.group(2))
keys = list(recs)
parts = [k.split('|') for k in keys]
res['population_parse'] = dict(n_nopurge_records=len(recs), field_values={i: sorted({p[i] for p in parts}) for i in range(1, 9)})
groups = {}
for k, p in zip(keys, parts):
    th = float(p[6])
    if th not in (0.0, 2.0):
        continue
    lin = p[1]; fam = p[4]
    r = recs[k]
    seq = tuple(round(float(r[x]), 4) for x in ('P1', 'S1', 'C1', 'S2', 'C2'))
    groups.setdefault(f'{lin}|{fam}', []).append((seq, r['P_paused'], r['P_restart']))
HOLDS = (0.010, 0.10, 0.22, 0.25, 0.30, 0.40, 0.65)
pop = {}
cache = {}
for g, lst in sorted(groups.items()):
    acc = dict(n=len(lst), n_C1zero_C2pos=sum(1 for s, _, _ in lst if s[2] <= 0 < s[4]),
               n_C2pos=sum(1 for s, _, _ in lst if s[4] > 0))
    worst, best, ps_w, plight_dev = [], [], [], []
    hold_rel = {h: [] for h in HOLDS}; hold_rel_c = {h: [] for h in HOLDS}; hold_mode = {}
    trip_max = {mo: 0.0 for mo in MODES}; second = []
    first_only_success = []
    for seq, Pp, Pr in lst:
        if seq not in cache:
            cl, hd_ = {}, {}
            fos = {}
            for conv in ('paused', 'restart'):
                for mo, Fc in MODES.items():
                    fos[(conv, mo)] = follow(seq, conv, NR, Fc)
                    cl[(conv, mo)] = classify(fos[(conv, mo)])
            for h in HOLDS:
                # hold on both conventions, lift flow and 200 N ramp (the pool); the larger hazard is kept; also per mode
                for mo in ('lift_flow_held', 'ramp_to_200N'):
                    cc = [classify(fos[(conv, mo)], hold=h) for conv in ('paused', 'restart')]
                    hd_[(h, mo)] = max(c['P_released_then_A3'] for c in cc)
                    hd_[(h, mo, 'c')] = max(c['P_released_then_A3_conservative'] for c in cc)
                hd_[h] = max(hd_[(h, 'lift_flow_held')], hd_[(h, 'ramp_to_200N')])
                hd_[(h, 'c')] = max(hd_[(h, 'lift_flow_held', 'c')], hd_[(h, 'ramp_to_200N', 'c')])
            fo = min(classes(seq, conv, Fc, all_voids=False)['P_success'] for conv in ('paused', 'restart') for Fc in (None, 200.0))
            cache[seq] = (cl, hd_, fo)
        cl, hd_, fo = cache[seq]
        sub = {k: v for k, v in cl.items() if k[1] in ('lift_flow_held', 'ramp_to_200N')}     # the author's two modes (pool = 200 N)
        wv = min(sub.values(), key=lambda v: v['P_success']); bv = max(sub.values(), key=lambda v: v['P_success'])
        worst.append(wv); best.append(bv); ps_w.append(wv['P_success']); first_only_success.append(fo)
        plight_dev.append(max(abs(cl[('paused', 'lift_flow_held')]['P_no_light'] - Pp), abs(cl[('restart', 'lift_flow_held')]['P_no_light'] - Pr)))
        for h in HOLDS:
            hold_rel[h].append(hd_[h]); hold_rel_c[h].append(hd_[(h, 'c')])
            for mo in ('lift_flow_held', 'ramp_to_200N'):
                hold_mode.setdefault((h, mo), []).append(hd_[(h, mo)]); hold_mode.setdefault((h, mo, 'c'), []).append(hd_[(h, mo, 'c')])
        for mo in MODES:
            for conv in ('paused', 'restart'):
                t = cl[(conv, mo)].get('A3_trip_after_E2_s')
                if t:
                    trip_max[mo] = max(trip_max[mo], t['max'])
        second.append(max(cl[(c, m)]['P_trip_on_second_void'] for c in ('paused', 'restart') for m in ('lift_flow_held', 'ramp_to_200N')))
    mean = lambda L, k: float(np.mean([x[k] for x in L]))
    ps_w = np.array(ps_w)
    acc.update(
        mean_worst=dict((k, mean(worst, k)) for k in ('P_no_light', 'P_A3_before_release', 'P_released_then_A3', 'P_success', 'P_light')),
        mean_best=dict((k, mean(best, k)) for k in ('P_released_then_A3', 'P_success')),
        share_P_success_worst_below_0p05=float((ps_w < 0.05).mean()), share_P_success_worst_above_0p70=float((ps_w > 0.70).mean()),
        mean_P_success_worst_first_void_only=float(np.mean(first_only_success)),
        max_P_trip_on_second_void=float(max(second)), n_records_trip_on_second_void=int(sum(1 for x in second if x > 1e-9)),
        max_abs_P_no_light_vs_record=float(max(plight_dev)),
        hold_P_released_then_A3=dict((f'{h:.2f}', dict(mean=float(np.mean(hold_rel[h])), max=float(np.max(hold_rel[h])),
                                                       n_records_gt_1e3=int(sum(1 for x in hold_rel[h] if x > 1e-3)),
                                                       conservative_mean=float(np.mean(hold_rel_c[h])),
                                                       conservative_max=float(np.max(hold_rel_c[h])))) for h in HOLDS),
        latest_A3_trip_after_E2_s=trip_max,
        hold_by_mode=dict((f'{h:.2f}|{mo}', dict(mean=float(np.mean(hold_mode[(h, mo)])), max=float(np.max(hold_mode[(h, mo)])),
                                                  n_records_gt_1e3=int(sum(1 for x in hold_mode[(h, mo)] if x > 1e-3)),
                                                  conservative_mean=float(np.mean(hold_mode[(h, mo, 'c')])),
                                                  conservative_max=float(np.max(hold_mode[(h, mo, 'c')]))))
                          for h in HOLDS for mo in ('lift_flow_held', 'ramp_to_200N')))
    au = AU['population_0_2deg'].get(g)
    if au:
        acc['author_mean_worst'] = au['mean_over_records_worst_case']
        acc['author_share_below_0p05'] = au['share_of_records_P_success_below_0p05']
    pop[g] = acc
res['population_0_2deg'] = pop
json.dump(res, open(out, 'w'), indent=1, default=float)

# ---- print
for key, v in named.items():
    print('==', key, v['sequence'], 'pubPabort %.5f (mine-pub %+.5f)' % (v['published_P_abort'], v['P_no_light_vs_published']))
    for cm in [k for k in v if '|' in k]:
        x = v[cm]; m = x['mine']
        print('   %-24s noL %.4f A3pre %.4f relA3 %.4f succ %.4f | 2nd-void trips %.4f | first-void-only vs author max|d| %.5f | trip %s'
              % (cm, m['P_no_light'], m['P_A3_before_release'], m['P_released_then_A3'], m['P_success'], m['P_trip_on_second_void'],
                 x['max_abs_diff'], json.dumps(m.get('A3_trip_after_E2_s'))))
print('LO worst analytic', json.dumps(res['LO_worst_analytic']))
print('parse', json.dumps(res['population_parse'])[:600])
for g, a in pop.items():
    print('##', g, 'n', a['n'], 'C1=0<C2', a['n_C1zero_C2pos'], 'C2>0', a['n_C2pos'])
    print('   worst', json.dumps(a['mean_worst']))
    print('   author', json.dumps(a.get('author_mean_worst')))
    print('   best', json.dumps(a['mean_best']), 'share<0.05 %.4f (author %s) >0.70 %.4f' % (a['share_P_success_worst_below_0p05'],
          a.get('author_share_below_0p05'), a['share_P_success_worst_above_0p70']))
    print('   first-void-only mean P_success worst %.4f; second-void trips: max %.4f in %d records; P_nolight vs record max|d| %.5f'
          % (a['mean_P_success_worst_first_void_only'], a['max_P_trip_on_second_void'], a['n_records_trip_on_second_void'],
             a['max_abs_P_no_light_vs_record']))
    print('   latest A3 trip after E2 [s]', json.dumps(a['latest_A3_trip_after_E2_s']))
    for k, x in a['hold_by_mode'].items():
        print('     mode-hold %-22s: P(rel then A3) mean %.4f max %.4f n>1e-3 %3d | conservative mean %.4f max %.4f' % (
            k, x['mean'], x['max'], x['n_records_gt_1e3'], x['conservative_mean'], x['conservative_max']))
    for h, x in a['hold_P_released_then_A3'].items():
        print('     hold %s: P(rel then A3) mean %.4f max %.4f n>1e-3 %d | conservative mean %.4f max %.4f' % (
            h, x['mean'], x['max'], x['n_records_gt_1e3'], x['conservative_mean'], x['conservative_max']))
print('wrote', out, H16(out))
