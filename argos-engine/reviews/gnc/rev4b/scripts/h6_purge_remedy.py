"""REV-GNC-7 (h)(ii): check of the lead's remedy (CHANGELOG 257 (2) as relayed 2026-10-21): after CF-4 / B-BLEED-1 the both-open cap
is re-set from the measured Cd x A (ratio r to the Cd 0.70 value) so that the 297.15 K vent is <= 76 g:
  cap = floor((76 g / mdot_297(r) - 0.05 s) / 10 ms) x 10 ms, never above 2.39 s; flow = cap + 0.05 s (never above 2.43 s)
  mdot_297(r) = r x 31.06 g/s (256 (2), Cd 0.70); needed flow at 283.15 K = 2.2 s / r (need scaling 1/(Cd x A) ASSUMED, as 256 (2)(b)).
Reports the vent at the cap, the 283.15 K margin and the r at which the margin falls below the FD-01 bounds 0.18 / 0.12 s;
and the vent if the cap is set from a measured r while the true ratio is r (1 + u)."""
import json, math, sys
def cap_flow(r):
    m = 31.06 * r
    cap = min(2.39, math.floor(round((76.0 / m - 0.05) / 0.01, 9)) * 0.01)
    flow = min(2.43, cap + 0.05)
    return cap, flow, m
rows = []
for r in [0.91, 0.95, 1.0, 1.05, 1.08, 1.1326, 1.2, 1.3, 1.4, 1.6, 1.9, 2.0]:
    cap, flow, m = cap_flow(r)
    rows.append(dict(r=r, cap_s=round(cap, 2), flow_s=round(flow, 2), vent_297_g=round(m * flow, 2), need_283_s=round(2.2 / r, 3), margin_283_s=round(flow - 2.2 / r, 3)))
def first_r_below(th):
    r = 1.0
    while r < 3.0:
        cap, flow, m = cap_flow(r)
        if flow - 2.2 / r < th: return round(r, 3)
        r += 0.001
    return None
err = []
for u in (0.03, 0.05, 0.079, 0.10):
    cap, flow, m = cap_flow(1.1326)
    err.append(dict(u=u, true_vent_g=round(31.06 * 1.1326 * (1 + u) * flow, 2)))
out = dict(method=__doc__, rows=rows, r_margin_below_0p18=first_r_below(0.18), r_margin_below_0p12=first_r_below(0.12), measurement_error=err)
json.dump(out, open(sys.argv[1], "w"), indent=1)
for x in rows: print(x)
print("margin < 0.18 s from r =", out["r_margin_below_0p18"], "; < 0.12 s from r =", out["r_margin_below_0p12"]); print(err)
