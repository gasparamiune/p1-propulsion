#!/usr/bin/env python3
"""arquitectura.py — Matriz ponderada de arquitecturas + sensibilidad de pesos.
Lee inputs.yaml → architecture_matrix. Escribe resultados/arquitectura.json y la tabla
resultados/arquitectura_tabla.md (bloque AUTO:arch en 03_arquitectura.md)."""
from __future__ import annotations

import json
import sys

import numpy as np

from p1calc.io import RESULTS_DIR, load_inputs


def main():
    inp = load_inputs()
    am = inp["architecture_matrix"]
    crit = list(am["criteria"])
    w = np.array([am["criteria"][c]["w"] for c in crit])
    w = w / w.sum()
    opts = list(am["options"])
    S = np.array([[am["options"][o]["scores"][c] for c in crit] for o in opts], dtype=float)
    tot = S @ w
    rank = np.argsort(-tot)
    # sensibilidad: cada peso ±Δ (renormalizado) → ¿cambia el ganador?
    d = am["weight_perturbation"]
    flips = []
    for i, c in enumerate(crit):
        for sgn in (-1, 1):
            w2 = w.copy(); w2[i] *= (1 + sgn * d); w2 /= w2.sum()
            win = opts[int(np.argmax(S @ w2))]
            flips.append({"criterio": c, "cambio": f"{'+' if sgn > 0 else '−'}{d*100:.0f} %", "ganador": win})
    # Monte Carlo de pesos (Dirichlet centrado en w)
    rng = np.random.default_rng(1)
    W = rng.dirichlet(w * 20, size=am["monte_carlo_n"])
    wins = np.bincount(np.argmax(W @ S.T, axis=1), minlength=len(opts)) / am["monte_carlo_n"]
    # sin criterio de seguridad (¿depende el resultado de un solo criterio?)
    out = {"criteria": crit, "weights": w.tolist(), "options": opts,
           "names": {o: am["options"][o]["name"] for o in opts}, "scores": S.tolist(),
           "totals": dict(zip(opts, tot.round(3).tolist())), "ranking": [opts[i] for i in rank],
           "weight_flips": flips, "mc_win_frac": dict(zip(opts, wins.round(3).tolist()))}
    with open(RESULTS_DIR / "arquitectura.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    hdr = "| Opción | " + " | ".join(f"{c} ({w[i]*100:.0f} %)" for i, c in enumerate(crit)) + " | **Total** | Gana en MC |"
    L = [hdr, "|" + "---|" * (len(crit) + 3)]
    for i in rank:
        o = opts[i]
        L.append(f"| **{o}** {am['options'][o]['name']} | " + " | ".join(f"{int(x)}" for x in S[i]) +
                 f" | **{tot[i]:.2f}** | {wins[i]*100:.0f} % |")
    changed = [f for f in flips if f["ganador"] != opts[rank[0]]]
    L.append("")
    L.append(f"Sensibilidad: variando cada peso ±{d*100:.0f} % (renormalizado), el ganador "
             + ("**no cambia** en ninguno de los " + str(len(flips)) + " casos." if not changed else
                "cambia en: " + "; ".join(f"{f['criterio']} {f['cambio']} → {f['ganador']}" for f in changed) + "."))
    L.append(f"Monte Carlo ({am['monte_carlo_n']} juegos de pesos Dirichlet alrededor de los nominales): "
             + ", ".join(f"{o} {wins[i]*100:.0f} %" for i, o in enumerate(opts) if wins[i] > 0.005) + ".")
    with open(RESULTS_DIR / "arquitectura_tabla.md", "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("arquitectura: ranking", out["ranking"][:3], "MC", {k: v for k, v in out["mc_win_frac"].items() if v > 0})
    return 0


if __name__ == "__main__":
    sys.exit(main())
