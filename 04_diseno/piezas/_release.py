"""_release.py — geometría de las trabas del bucket y de su desbloqueo (no es una pieza).

Fuente ÚNICA de la posición de los émbolos P1-REV-04 (la usan P1-REV-01/04/09/10, P1-STE-01, planos y FEA):
traba del brazo +Y a REV_lock_ang y del brazo −Y a REV_lock_ang_m, las dos a REV_lock_r del pivote del bucket
(marco de la boquilla, bucket ABAJO = posición en la que el émbolo entra en el agujero "abajo")."""
import math


def lock_ang(p, side=1):
    """Ángulo (°, desde +X hacia +Z) de la traba del brazo +Y (side > 0) o −Y (side < 0)."""
    return p.REV_lock_ang if side > 0 else p.REV_lock_ang_m


def lock_xz(p, side=1):
    """(X, Z) del eje del émbolo de la traba del brazo +Y (side > 0) o −Y (side < 0), marco de la boquilla."""
    a = math.radians(lock_ang(p, side))
    return (p.X_bucket_pivot + p.REV_lock_r * math.cos(a), p.Z_bucket_pivot + p.REV_lock_r * math.sin(a))


def lock_sides(p):
    """Brazos con traba: (+1,) o (+1, −1) según REV_n_locks."""
    return (1, -1) if p.REV_n_locks > 1 else (1,)


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
