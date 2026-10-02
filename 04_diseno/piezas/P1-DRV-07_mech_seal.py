"""P1-DRV-07 — Sello mecánico ST-MG1 Ø20 (tipo MG1, EN 12756), caras carbón/SiC, fuelle NBR — comprado
(research/R11 §5, desde 29 €). Pedir CARBÓN/SiC (tolera arranques cortos en seco; SiC/SiC no).
Montaje interior en P1-DRV-02: la cabeza rotante (fuelle + resorte) en la cámara mojada, apoyada hacia
popa en su anillo DIN 471 del eje; el asiento fijo con copa de NBR en el alojamiento Ø seat_od.
Modelo simplificado: cabeza Ø33 + asiento Ø35 (un sólido, caras en contacto)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _drv_geom import tube_s  # noqa: E402
from params import loc_jet  # noqa: E402

META = dict(id="P1-DRV-07", name="mech_seal_MG1_20", desc="Sello mecánico MG1 Ø20 carbón/SiC (comprado)",
            material="referencia", process="comprada", qty=1, frame="jet", group="drive",
            load_case="Presión del conducto, 5 m/s", print_rot=(0, 0, 0), solid_frac=1.0,
            orientation="—", mass_g=60.0,   # [ESTIMADO: params_tren.SEAL]
            allow={"P1-DRV-01": 5.0, "P1-DRV-02": 5.0})


def build(p):
    s = p.drv_seal
    head = tube_s(s["head_od"] / 2, s["d"] / 2, p.drv_S_head_back, p.drv_S_seat_face)
    seat = tube_s(s["seat_od"] / 2, s["seat_id"] / 2, p.drv_S_seat_face, p.drv_S_seat_back)
    return head + seat


def placements(p, steer=0.0, bucket=0):
    return [loc_jet(p)]


def checks(p, part):
    s = p.drv_seal
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("Ø interior del asiento − Ø eje (no roza) [mm]", s["seat_id"] - s["d"], 1.0, ">=")]
