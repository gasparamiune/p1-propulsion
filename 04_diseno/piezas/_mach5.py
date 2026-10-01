"""_mach5.py — geometría compartida del cable Mach5 del bucket (no es una pieza)."""
import math


def stud_xz(p, down=False):
    a = math.radians(p.REV_stud_up_ang - (p.bucket_down_deg if down else 0.0))
    return (p.X_bucket_pivot + p.REV_stud_r * math.cos(a), p.Z_bucket_pivot + p.REV_stud_r * math.sin(a))


def rod_y(p):
    return p.REV_y_in + p.REV_t + 1.0 + p.REV_eye_w / 2


def dz(p):
    return stud_xz(p, True)[1] - stud_xz(p)[1]


SLEEVE_D = 12.7      # [ESTIMADO: vaina rígida 33C 1/2"; buscar ficha Ultraflex Mach5]
SLEEVE_L = 120.0     # [ESTIMADO]
HUB_D, HUB_L = 22.0, 20.0   # [ESTIMADO: cabeza con ranura de grapa]
