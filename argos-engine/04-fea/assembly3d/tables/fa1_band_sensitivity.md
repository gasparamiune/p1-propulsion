FA-1 column sensitivity at TC-01 (modal_v351ca2b_c71: all bodies at mesh level 2, f_max 5130 Hz). Shares of the static unit-pressure stress (dominant principal direction; tensor projection in brackets) [SIM]; MS [DERIVED] with Peq = slow x 151.04 + (1 - slow) x 93 / 102 bar.

| point (nearest L2 node) | f scale | slow T > 1 ms | 0.1-1 ms | residual (fast) | mode 11 (1010 Hz) | mode 12 (1091 Hz) | mode 13 (1189 Hz) | Peq yield / ult bar | MS_y / MS_u |
|---|---|---|---|---|---|---|---|---|---|
| TC-01 J-FWD (FA-1 governing, L1 node 8314) (node 2785, 0.55 mm) | 1.00 | +0.018 (+0.017) | +0.600 (+0.621) | +0.382 (+0.362) | +0.006 (+0.006) | +0.002 (+0.003) | +0.004 (+0.005) | 94.0 / 102.9 | +0.237 / +0.223 |
| TC-01 J-FWD (FA-1 governing, L1 node 8314) (node 2785, 0.55 mm) | 0.90 | +0.026 (+0.026) | +0.592 (+0.612) | +0.382 (+0.362) | +0.006 (+0.006) | +0.002 (+0.003) | +0.004 (+0.005) | 94.5 / 103.3 | +0.231 / +0.218 |
| TC-01 J-FWD (FA-1 governing, L1 node 8314) (node 2785, 0.55 mm) | 0.85 | +0.026 (+0.026) | +0.592 (+0.612) | +0.382 (+0.362) | +0.006 (+0.006) | +0.002 (+0.003) | +0.004 (+0.005) | 94.5 / 103.3 | +0.231 / +0.218 |
| TC-01 LC1 governing (L1 node 8843, B1_21.65) (node 2800, 0.78 mm) | 1.00 | +0.035 (+0.035) | +0.524 (+0.524) | +0.441 (+0.441) | -0.004 (-0.004) | +0.016 (+0.016) | -0.005 (-0.005) | 95.0 / 103.7 | +0.224 / +0.213 |
| TC-01 LC1 governing (L1 node 8843, B1_21.65) (node 2800, 0.78 mm) | 0.90 | +0.046 (+0.046) | +0.512 (+0.513) | +0.441 (+0.441) | -0.004 (-0.004) | +0.016 (+0.016) | -0.005 (-0.005) | 95.7 / 104.3 | +0.216 / +0.206 |
| TC-01 LC1 governing (L1 node 8843, B1_21.65) (node 2800, 0.78 mm) | 0.85 | +0.046 (+0.046) | +0.512 (+0.513) | +0.441 (+0.441) | -0.004 (-0.004) | +0.016 (+0.016) | -0.005 (-0.005) | 95.7 / 104.3 | +0.216 / +0.206 |

Distance to the break-even (nearest node, principal functional): uniform frequency scale at which modes would carry a slow share of 0.40 / 0.485, and the share carried by all modes below 2 / 3 kHz:

- TC-01 J-FWD (FA-1 governing, L1 node 8314): slow share 0.40 at f x0.464, 0.485 at f x0.464; modes below 2 kHz carry +0.090, below 3 kHz +0.565
- TC-01 LC1 governing (L1 node 8843, B1_21.65): slow share 0.40 at f x0.449, 0.485 at f x0.449; modes below 2 kHz carry +0.006, below 3 kHz +0.628

Neighbour spread (every TC-01 node within 2 mm of the L1 point; principal functional; slow share at f scale 1.00 / 0.90 / 0.85):

- TC-01 J-FWD (FA-1 governing, L1 node 8314): 6 nodes; x1.00: +0.015 .. +0.025; x0.90: +0.024 .. +0.035; x0.85: +0.024 .. +0.035
- TC-01 LC1 governing (L1 node 8843, B1_21.65): 6 nodes; x1.00: +0.035 .. +0.040; x0.90: +0.046 .. +0.053; x0.85: +0.046 .. +0.053

F1 columns at the J-FWD node (L1 node 8314) and the proportionality check (break-even pressure P x (1 + MS)) [SIM / DERIVED]:

| column | P bar abs | MS_y | MS_u | vm MPa | break-even yield bar | break-even ult bar |
|---|---|---|---|---|---|---|
| FA1Q | 90.00 | +0.291 | +0.393 | 182.8 | 116.2 | 125.3 |
| FA1D | 93.00 | +0.251 | +0.349 | 188.7 | 116.3 | 125.5 |
| FA1U | 102.00 | +0.144 | +0.233 | 206.4 | 116.6 | 125.8 |
| FA1S | 151.04 | -0.221 | -0.160 | 303.0 | 117.7 | 126.9 |

Spread of the break-even pressure across the four columns: yield 1.27 %, ultimate 1.27 %. Break-even slow share: yield 0.402 (proportional, from FA1D) / 0.414 (affine fit of the four columns); ultimate 0.485 / 0.499.
