"""REV-GNC-7 (h)(ii) v2: the lead's condition (d) (CHANGELOG 257 (2); combustion.json v2.4c purge_decision_v2p4c.condition_d_LEAD_257_2)
on the decided structure: the both-open cap is re-set from the measured Cd x A ratio r (to the Cd 0.70 value) so that the 297.15 K
vent at the cap is <= 76 g, and the scheduled overlap sits 10 ms under the cap (as the decided 2.38 s under 2.39 s):
  cap = floor((76 g / mdot_297(r) - 0.05 s) / 10 ms) x 10 ms, never above 2.39 s; flow at the cap = cap + 0.05 s;
  scheduled flow = (cap - 0.01 s) + 0.05 s, never above 2.43 s;  mdot_297(r) = r x 31.06 g/s (Cd 0.70, 230 (3) / 256 (2));
  needed flow at 283.15 K = 2.2 s / r; with the FD-01 element bounds 2.25 / 2.30 s / r (margins 0.18 / 0.13 s at r = 1 and 2.43 s,
  purge_decision_v2p4c); need scaling 1 / (Cd x A) ASSUMED (256 (2)(b)).
v1 (h6) took the flow at the cap for r > 1 (10 ms more than scheduled); v2 reproduces the lead's 0.23 / 0.21 / 0.21 / 0.19 s.
Also: the 297.15 K vent at the cap when the cap is set from a measured r while the true ratio is r (1 + u)."""
import json, math, sys
def cap_of(r):
    m = 31.06 * r
    cap = min(2.39, math.floor(round((76.0 / m - 0.05) / 0.01, 9)) * 0.01)
    return cap, m
rows = []
for r in [0.91, 0.95, 1.0, 1.05, 1.08, 1.1326, 1.2, 1.3, 1.5, 2.0]:
    cap, m = cap_of(r)
    sched = min(2.43, cap - 0.01 + 0.05)
    rows.append(dict(r=r, cap_s=round(cap, 2), scheduled_flow_s=round(sched, 2), flow_at_cap_s=round(cap + 0.05, 2),
                     vent_297_at_cap_g=round(m * (cap + 0.05), 2), vent_297_scheduled_g=round(m * sched, 2),
                     margin_283_s=round(sched - 2.2 / r, 3), margin_283_FD01_s=[round(sched - 2.25 / r, 3), round(sched - 2.30 / r, 3)]))
err = []
for u in (0.03, 0.05, 0.079, 0.10):
    cap, m = cap_of(1.1326)
    err.append(dict(r_measured=1.1326, u=u, true_vent_297_at_cap_g=round(m * (1 + u) * (cap + 0.05), 2)))
for r in (1.0, 1.08):
    pass
out = dict(method=__doc__, rows=rows, measurement_error=err,
           range_r_1_to_1p3=dict(margin_283_s=[min(x["margin_283_s"] for x in rows if 1.0 <= x["r"] <= 1.3), max(x["margin_283_s"] for x in rows if 1.0 <= x["r"] <= 1.3)],
                                 margin_283_FD01_s=[min(min(x["margin_283_FD01_s"]) for x in rows if 1.0 <= x["r"] <= 1.3), max(max(x["margin_283_FD01_s"]) for x in rows if 1.0 <= x["r"] <= 1.3)],
                                 vent_297_at_cap_max_g=max(x["vent_297_at_cap_g"] for x in rows if x["r"] >= 1.0)),
           tag="DERIVED (arithmetic on the Combustion / lead figures; need scaling ASSUMED); REV-GNC-7")
json.dump(out, open(sys.argv[1], "w"), indent=1)
for x in rows: print(x)
print(out["range_r_1_to_1p3"]); print(err)
