"""Part record and registry.  Every part carries the metadata the BOM, mass ledger, PETG notes and
drawings need, so those outputs are generated, never hand-edited."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import numpy as np


@dataclass
class Part:
    pn: str
    name: str
    material: str                 # key into engmat.MATERIALS
    process: str                  # CNC-lathe / CNC-mill / FDM-PETG / FDM-ABS / COTS / cut-stock
    shape: Any                    # cq.Shape in the part's local frame (mm, +Z = engine axis forward)
    placements: list = field(default_factory=list)   # [(4x4 mm transform engine frame at neutral, group)]
    cots: bool = False
    mass_each_kg: float | None = None   # COTS / not-from-volume mass
    mass_tag: str = ""                  # tag for mass_each_kg
    supplier: str = ""
    supplier_pn: str = ""
    price: str = "TO-QUOTE"             # "12.50 EUR (2026-10-11, source)" or TO-QUOTE
    petg: dict = field(default_factory=dict)  # orientation, infill, compensation, coldflow
    drawing: bool = False
    notes: str = ""
    wetted: str = ""                    # "N2O" if oxidiser-wetted (cleaning/material rule)
    hot: bool = False
    dwg: dict = field(default_factory=dict)   # drawing data: datum, fits, finish, ht, extra notes
    bom_parent: str = ""                # sub-solid of another BOM item (e.g. GE inner ring): no separate BOM line
    split_engine: float = 0.5           # flexible items (group hose/line): mass fraction carried by the engine

    @property
    def sub(self):
        return self.pn.split("-")[1]

    @property
    def qty(self):
        return len(self.placements)

    def place(self, T, group):
        T = np.array(T, float)
        # v3.4 guard: a left-handed placement mirrors the solid and turns it inside out (negative volume, inverted point
        # classification) -- found on ENG-FD-09 (2026-10-13); every placement must be a proper rotation
        assert np.linalg.det(T[:3, :3]) > 0.0, f"{self.pn}: left-handed placement (det {np.linalg.det(T[:3, :3]):.3f})"
        self.placements.append((T, group))
        return self


class Registry:
    def __init__(self):
        self.parts: dict[str, Part] = {}

    def add(self, p: Part):
        assert p.pn not in self.parts, p.pn
        self.parts[p.pn] = p
        return p

    def __iter__(self):
        return iter(sorted(self.parts.values(), key=lambda p: p.pn))

    def get(self, pn):
        return self.parts[pn]
