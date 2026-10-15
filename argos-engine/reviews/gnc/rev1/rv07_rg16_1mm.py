"""rv07_rg16_1mm v1.0 (REV-GNC-R1, independent reviewer, 2026-10-13).

RG-16 closure was flown at the 0.8 mm bleed (purge booked at 20.0 g/s; stuck bleed 19.4 g/s). The lead set the bleed path at
~31 g/s total (CHANGELOG l.160 (5)). This script scales GNC's published RG-16 held maxima to the decided flow, to first order
(DERIVED, linear in the constant mass offset, as in GNC's own method: a constant m_hat offset from ARM), using only published
values: rev1 results/rg16_terms/rg16_fct_terms.json (offsets and held maxima per case, 200 runs per case) and the 1.0 mm arms
of results/purge_bleed_1mm/purge_bleed.json and results/purge_cost (purge mass at 31.3 g/s).
It does NOT replace a re-run of m2_rg16_fct_terms at the decided path; it shows which side needs it.
Output: rv07_rg16_1mm.json. Reads only.
"""
import json
import os

HUB = "/home/claude/work/shared-fallback/engine"
R = f"{HUB}/01-systems-gnc/staging_v3.1/rev1/results"
HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    t = json.load(open(f"{R}/rg16_terms/rg16_fct_terms.json"))
    pc = json.load(open(f"{R}/purge_cost/purge_cost.json"))
    off = t["offsets_kg"]
    cases = t["cases"]
    # sensitivity of the held maximum to a constant over-read (N per g) from GNC's own pairs (case vs its base case)
    sens = {}
    for k, c in cases.items():
        w = c["w_bias_kg"]
        if w > 0:
            sens[k] = (c["held_max_N"] - c["base_held_max_N"]) / (1e3 * w)
    flow_ratio = 31.3 / 19.4                      # stuck bleed: Electronics DERIVED 1.0 mm vs the 19.4 g/s bracket flown
    pnb_1mm_g = max(pc["cases"][f"{b}|PS10"]["purge"]["mass_g"]["max"] for b in ("A1_none", "A1J_pc"))
    scaled = {}
    for k, c in cases.items():
        w_g = 1e3 * c["w_bias_kg"]
        if k.endswith("_pnb"):
            w1 = pnb_1mm_g
        elif k.endswith("_blf"):
            w1 = w_g * flow_ratio
        else:
            continue
        s = sens[k]
        scaled[k] = dict(offset_0p8_g=w_g, offset_1p0_g=w1, sens_N_per_g=s,
                         held_max_0p8_N=c["held_max_N"], held_max_1p0_N_derived=c["base_held_max_N"] + s * w1,
                         margin_to_650_N_derived=650.0 - (c["base_held_max_N"] + s * w1))
    out = dict(version="rv07_rg16_1mm v1.0", offsets_flown_kg=off, flow_ratio_stuck=flow_ratio, purge_mass_1mm_max_g=pnb_1mm_g,
               false_alarm_side=scaled,
               missed_detection_side=dict(
                   booking_residual_0p8_g=-1e3 * off["pbk"],
                   booking_residual_1p0_g_gnc_derived=45.0,
                   flown_at_0p8=dict((k, dict(misses_670=c["stuck"]["670"]["misses"], held_max=c["held_max_N"]))
                                     for k, c in cases.items() if k.endswith("_pbk")),
                   note="the under-read side (booking residual) was flown only at 29.1 g; GNC scales it to ~45 g at 1.0 mm "
                        "without a re-run; the non-adopted Llo_cmd variant already misses 1/1000 at 29.1 g"))
    with open(os.path.join(HERE, "rv07_rg16_1mm.json"), "w") as f:
        json.dump(out, f, indent=1)
    for k, v in scaled.items():
        print(f"{k:22s} offset {v['offset_0p8_g']:6.1f} -> {v['offset_1p0_g']:6.1f} g  held max {v['held_max_0p8_N']:.1f} -> "
              f"{v['held_max_1p0_N_derived']:.1f} N (margin {v['margin_to_650_N_derived']:.1f} N)  sens {v['sens_N_per_g']:.4f} N/g")
    print(json.dumps(out["missed_detection_side"], indent=1))


if __name__ == "__main__":
    main()
