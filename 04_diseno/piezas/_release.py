"""_release.py — geometría del desbloqueo del émbolo del bucket (no es una pieza)."""
import math


def lock_xz(p, side=1):
    a = math.radians(p.REV_lock_ang if side > 0 else p.raw.get("REV_lock_ang_m", p.REV_lock_ang))
    return (p.X_bucket_pivot + p.REV_lock_r * math.cos(a), p.Z_bucket_pivot + p.REV_lock_r * math.sin(a))


def mirror_loc(p):
    """Lleva la geometría construida alrededor de la traba +Y a la traba −Y (y → −y)."""
    from build123d import Pos, Rot
    x1, z1 = lock_xz(p, 1)
    x2, z2 = lock_xz(p, -1)
    return Pos(x2, 0, z2) * Rot(180, 0, 0) * Pos(-x1, 0, -z1)


def knob_end_y(p):
    return p.STE_ear_y0 - 24.0          # cara del pomo (P1-REV-04)


def plate_y(p):
    """Cara de la placa de tope de la vaina (lado del pomo)."""
    return knob_end_y(p) - (p.REV_release_need + 6.0)


def pin_tip_y(p):
    return p.REV_y_in + p.REV_t + 1.0


def need(p):
    """Recorrido del pomo para sacar el perno del brazo del bucket (+0,5 de luz)."""
    return pin_tip_y(p) - (p.REV_y_in - 0.5)
