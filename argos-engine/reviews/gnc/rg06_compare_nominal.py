"""rg06_compare_nominal v1 (independent GNC review, 2026-10-13): reviewer 1-DOF model (rg03) vs the author's 6-DOF nominal
flights (recorded by rg05 part 'nominal' with the author's own PC.nominal configuration), phase by phase.

Compares, for A1 (plan 0.81 s, liquid-line median delay 0.315 s), B1 85 m and B1 62 m (no band, no growth, k_est_asc 2):
  N2O burned / fuel burned / impulse / liquid left / reserve, and the split between the ascent (to MECO or to the end of the
  full-thrust phase) and the rest; tank pressure and temperature at fixed times; delivered N2O per unit impulse.
Output: rg06_compare_nominal.json
"""
import json
import os

import numpy as np

import rg03_vertical as V

HERE = os.path.dirname(os.path.abspath(__file__))


def author(nm):
    d = json.load(open(os.path.join(HERE, "rg05_sens.json")))["nominal"][nm]
    h = np.array(d["hist"])
    c = {k: h[:, i] for i, k in enumerate(d["hist_cols"])}
    return d, c


def integ(t, y, t0=-1.0, t1=1e9):
    s = (t >= t0) & (t <= t1)
    return float(np.trapezoid(y[s], t[s])) if s.sum() > 1 else 0.0


def main():
    A_dry = 16.0746 - 2.0
    B_dry = 15.4246 - 2.0
    mine = {"A1_plan0.81_liq_med": V.fly("A", 300.0, A_dry, False, d_ign=0.3152, t_est=0.81),
            "B1_85m": V.fly("B", 85.0, B_dry, True),
            "B1_62m": V.fly("B", 62.0, B_dry, True)}
    out = {}
    for nm, r in mine.items():
        d, c = author(nm)
        hm = np.array(r["hist"])
        mc = {k: hm[:, i] for i, k in enumerate(r["hist_cols"])}
        tme_a = d["t_meco"]
        tme_m = r.get("t_meco", np.nan)
        row = dict(
            author=dict(n2o_burned=d["closure"]["n2o_burned"], fuel_burned=d["closure"]["fuel_burned"], impulse=d["closure"]["impulse_Ns"],
                        liquid_left=d["closure"]["liquid_left"], reserve=d["closure"]["reserve_frac"], h_max=d["closure"]["h_max"],
                        burn_counter=d["closure"]["burn_time_s"], t_meco=tme_a, h_meco=d["h_meco"], v_meco=d["v_meco"],
                        n2o_to_meco=integ(c["t"], c["mox"], t1=tme_a + 0.6), impulse_to_meco=integ(c["t"], c["F"], t1=tme_a + 0.6),
                        n2o_after=integ(c["t"], c["mox"], t0=tme_a + 0.6), impulse_after=integ(c["t"], c["F"], t0=tme_a + 0.6),
                        P_tank_at=[float(np.interp(x, c["t"], c["Ptank"])) for x in (0.0, 2.0, 5.0, 10.0, 15.0)],
                        T_tank_at=[float(np.interp(x, c["t"], c["Ttank"])) for x in (0.0, 2.0, 5.0, 10.0, 15.0)]),
            reviewer=dict(n2o_burned=r["n2o_burned"], fuel_burned=r["fuel_burned"], impulse=r["impulse_Ns"], liquid_left=r["liquid_left"],
                          reserve=r["reserve"], h_max=r.get("h_apo"), thrust_on=r["thrust_on_s"], t_meco=tme_m, h_meco=r.get("h_meco"),
                          v_meco=r.get("v_meco"),
                          n2o_to_meco=integ(mc["t"], mc["mox"], t1=tme_m + 0.6), impulse_to_meco=integ(mc["t"], mc["F"], t1=tme_m + 0.6),
                          n2o_after=integ(mc["t"], mc["mox"], t0=tme_m + 0.6), impulse_after=integ(mc["t"], mc["F"], t0=tme_m + 0.6),
                          P_tank_at=[float(np.interp(x, mc["t"], mc["P_tank"])) for x in (0.0, 2.0, 5.0, 10.0, 15.0)]))
        a, m = row["author"], row["reviewer"]
        row["n2o_per_impulse_g_per_kNs"] = dict(author_after=1e6 * a["n2o_after"] / max(a["impulse_after"], 1e-9),
                                                reviewer_after=1e6 * m["n2o_after"] / max(m["impulse_after"], 1e-9),
                                                author_to_meco=1e6 * a["n2o_to_meco"] / max(a["impulse_to_meco"], 1e-9),
                                                reviewer_to_meco=1e6 * m["n2o_to_meco"] / max(m["impulse_to_meco"], 1e-9))
        out[nm] = row
        print(nm)
        for k in ("n2o_burned", "fuel_burned", "impulse", "liquid_left", "reserve", "h_max", "t_meco", "n2o_to_meco", "impulse_to_meco",
                  "n2o_after", "impulse_after", "P_tank_at"):
            print(f"   {k:16s} author {a.get(k)} | reviewer {m.get(k)}")
        print("   N2O per impulse [g/kNs]", {k: round(v, 2) for k, v in row["n2o_per_impulse_g_per_kNs"].items()})
    json.dump(out, open(os.path.join(HERE, "rg06_compare_nominal.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
