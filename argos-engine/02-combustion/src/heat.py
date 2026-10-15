"""Gas-side heat transfer along the gas path (Combustion v1).

Bartz (1957) closed form, as given in D.R. Bartz, "A Simple Equation for Rapid Estimation of Rocket
Nozzle Convective Heat Transfer Coefficients", Jet Propulsion 27(1) 1957, 49-51, and in Huzel & Huang,
"Modern Engineering for Design of Liquid-Propellant Rocket Engines", AIAA Prog. Astro. Aero. 147 (1992), Eq. 4-13:

  h_g = [0.026 / Dt^0.2 * (mu^0.2 cp / Pr^0.6)_0 * (Pc / c*)^0.8 * (Dt / Rc)^0.1] * (At/A)^0.9 * sigma
  sigma = 1 / { [0.5 Tw/T0 (1 + (g-1)/2 M^2) + 0.5]^0.68 * [1 + (g-1)/2 M^2]^0.12 }
  T_aw = T0 * [1 + r (g-1)/2 M^2] / [1 + (g-1)/2 M^2],  r = Pr^(1/3) (turbulent recovery factor)

(Pc in Pa and c* in m/s give (Pc/c*) in kg/m2/s, so h in W/m2/K with SI properties; the 'g' factor of
the original English form is 1 in SI.) Bartz is a nozzle correlation; applied to chamber walls (low M,
large A/At) it gives an order-of-magnitude estimate only -> uncertainty factor stated in the CSV.

Gas radiation: grey-gas H2O+CO2 estimate with Leckner-type total emissivity (fitted values quoted in
Modest, "Radiative Heat Transfer", 3rd ed., Ch. 11) is NOT re-implemented here; instead a bounding
emissivity band 0.05-0.20 (gas + soot, small path length L_m = 0.9 D) is used and labelled ASSUMED.
"""
from __future__ import annotations
import numpy as np

SIGMA_SB = 5.670374419e-8


def mach_from_area(Aratio, gamma, supersonic):
    """Isentropic Mach number for A/At = Aratio (>= 1)."""
    from scipy.optimize import brentq
    g = gamma
    f = lambda M: (1 / M) * ((2 / (g + 1)) * (1 + (g - 1) / 2 * M * M)) ** ((g + 1) / (2 * (g - 1))) - Aratio
    if Aratio <= 1.0 + 1e-9:
        return 1.0
    if supersonic:
        return brentq(f, 1.0 + 1e-9, 20.0)
    return brentq(f, 1e-6, 1.0 - 1e-9)


def bartz_h(Pc, cstar, Dt, Rc_throat, mu0, cp0, Pr0, T0, gamma, Aratio, M, Tw):
    base = 0.026 / Dt ** 0.2 * (mu0 ** 0.2 * cp0 / Pr0 ** 0.6) * (Pc / cstar) ** 0.8 * (Dt / Rc_throat) ** 0.1
    f = 1 + (gamma - 1) / 2 * M * M
    sigma = 1.0 / ((0.5 * Tw / T0 * f + 0.5) ** 0.68 * f ** 0.12)
    return base * (1.0 / Aratio) ** 0.9 * sigma


def t_aw(T0, gamma, M, Pr):
    r = Pr ** (1.0 / 3.0)
    f = (gamma - 1) / 2 * M * M
    return T0 * (1 + r * f) / (1 + f)


def radiation_flux(T_gas, T_wall, emissivity):
    return emissivity * SIGMA_SB * (T_gas ** 4 - T_wall ** 4)
