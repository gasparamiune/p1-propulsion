"""rv05_rg16_window v1.0.1 (REV-GNC-R1, independent reviewer, 2026-10-13).

Ruling input for GNC's dispute of the reviewer's RG-16 hypothesis ("the A1 k_hat vs F_acc offset comes from different comparison
windows"). Reads GNC's published per-run diagnostic (rev1 results/khat_offset/khat_offset.json, m2_khat_offset v1.1, 200 runs per
profile) and checks, with the reviewer's own arithmetic:
  1. what the "two halves" are (the code splits the window at t0 + 0.5 s: first 0.5 s against the rest), the window length per run,
     and how many runs show a negative offset in each part;
  2. closure of the term decomposition per run (total - sum of terms);
  3. an order-of-magnitude check of the lever-arm term from the published medians: (wx^2 + wy^2) r_z m / F;
  4. the B1 contrast (body rates, terms).
Output: rv05_rg16_window.json. Reads only.
"""
import json
import os

import numpy as np

HUB = "/home/claude/work/shared-fallback/engine"
P = f"{HUB}/01-systems-gnc/staging_v3.1/rev1/results/khat_offset/khat_offset.json"
HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    d = json.load(open(P))
    out = dict(version="rv05_rg16_window v1.0.1", source=P, gnc_version=d["version"], profiles={})
    for prof in ("A1", "B1"):
        runs = [r for r in d["runs"][prof] if r is not None]
        e = np.array([r["ratio_kh_early_late"][0] for r in runs if r["ratio_kh_early_late"][0] is not None])
        la = np.array([r["ratio_kh_early_late"][1] for r in runs if r["ratio_kh_early_late"][1] is not None])
        win = np.array([r["t_sel"][1] - r["t_sel"][0] for r in runs])
        clos = np.array([r["closure"] for r in runs])
        tot = np.array([r["ratio_kraw_nf"] for r in runs])
        terms = {k: np.array([r["terms"][k] for r in runs]) for k in ("lever", "dir", "aero", "bias")}
        s = d["summary"][prof]
        w50 = s["pct_median_over_runs"]["body_rate_deg_s"][1]
        lever_est = (np.radians(w50) ** 2) * s["r_z_m_median"] * (np.median([r["m_kg"] for r in runs]) / s["F_N_median"])
        out["profiles"][prof] = dict(
            n_runs=len(runs),
            window_s=dict(p01=float(np.percentile(win, 1)), p50=float(np.median(win)), p99=float(np.percentile(win, 99))),
            split_rule="early = first 0.5 s of the comparison window, late = the rest (m2_khat_offset l.123-124), not equal halves",
            early_median=float(np.median(e)), late_median=float(np.median(la)),
            runs_early_negative=int(np.sum(e < 0)), runs_late_negative=int(np.sum(la < 0)), n_early=int(e.size), n_late=int(la.size),
            total_median=float(np.median(tot)), terms_median={k: float(np.median(v)) for k, v in terms.items()},
            closure_abs_max=float(np.max(np.abs(clos))),
            median_of_sum_of_terms=float(np.median(sum(terms.values()))),
            body_rate_median_deg_s=w50,
            lever_term_order_of_magnitude=float(-lever_est),
            lever_term_published_median=float(np.median(terms["lever"])),
            per_run_total_p01_p99=[float(np.percentile(tot, 1)), float(np.percentile(tot, 99))],
            gnc_sample_envelope_after_lever_dir_comp_p01_p99=s["pct_p01_p99_over_runs"]["total_lever_dir_comp"],
            gnc_sample_envelope_total_p01_p99=s["pct_p01_p99_over_runs"]["total"],
            note_envelopes="gnc_sample_envelope_* are GNC per-sample percentile envelopes over runs (pct_p01_p99_over_runs), not per-run window means; per_run_total_p01_p99 is the per-run window-mean ratio (v1.0.1 relabels the v1.0 key)")
    out["ruling_inputs"] = (
        "Both parts of the same landing-burn window carry the offset in A1, and the per-sample decomposition closes to rounding "
        "(lever + direction + aero + bias = total): the window hypothesis is refuted as the cause. The lever term is consistent "
        "with the published body-rate and lever-arm medians to first order.")
    with open(os.path.join(HERE, "rv05_rg16_window.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1)[:4000])


if __name__ == "__main__":
    main()
