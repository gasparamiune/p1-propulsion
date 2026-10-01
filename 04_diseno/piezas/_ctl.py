"""_ctl.py — geometría compartida de la unidad de palancas de la consola (no es una pieza).

Marco local U: origen en el eje de las palancas (p.CTL_axis en el BOTE), ejes paralelos al BOTE
(x a proa, y a babor, z arriba); el eje de las palancas es paralelo a y. Giro θ alrededor de +y:
θ > 0 lleva la parte de arriba de la palanca hacia proa (avance). Ángulos φ de los elementos en el
plano XZ medidos desde +x hacia +z (un giro θ resta θ a φ).

Orden en y: cabeza del eje + imán (−22…−16) | palanca del acelerador (−13…−5) | placa central Al
(−3…3) | palanca del bucket (5…13) | anillo E (14…16). Enclavamiento por 2 pernos deslizantes en la
placa central (φ = 90° y 270°, r = CTL_ilock_r):
  acelerador: ranura2 φ∈[60,90] (reversa), ranura3 φ∈[270,310] (avance);
  bucket:     muesca2 en φ = 90 (ARRIBA), muesca3 en φ = 210 (ABAJO, θ_B = −60°).
→ bucket solo se mueve con el acelerador en neutro; avance solo con bucket arriba; reversa solo con
bucket abajo (la lógica se verifica en los checks de P1-CTL-08)."""
import math

Y_THR = (-13.0, -5.0)
Y_MID = (-3.0, 3.0)
Y_BKT = (5.0, 13.0)
Y_HEAD = (-22.0, -16.0)
HUB_R = 30.0
CONSOLE_TOP_LOCAL = None      # se calcula con p
CRANK_R = 46.0                # [CALCULADO: carrera = 2·r·sin30° = carrera del Mach5 en la boquilla]
CRANK_PHI_UP = -30.0          # manivela hacia proa; ARRIBA → φ = −30°, ABAJO → +30° (sube: tira la varilla)
ROD_Y = 17.0
SLEEVE_TOP_Z = -38.0          # fin de la vaina del Mach5 de la consola (sale la varilla hacia arriba)
GROOVES_T = {2: (60.0, 90.0), 3: (270.0, 310.0)}
NOTCHES_B = {2: 90.0, 3: 210.0}
PIN_PHI = {2: 90.0, 3: 270.0}


def unit_loc(p, theta=0.0):
    from build123d import Pos, Rot
    x, y, z = p.CTL_axis
    return Pos(x, y, z) * Rot(0, theta, 0)


def top_local(p):
    """z local de la cara superior de la tapa de la consola."""
    return p.CTL_console_top + p.CTL_ply_t - p.CTL_axis[2]


def crank_pin(phi):
    return (CRANK_R * math.cos(math.radians(phi)), CRANK_R * math.sin(math.radians(phi)))


def interlock_ok(p, th_t, th_b):
    """True si los dos pernos pueden alojarse (estado alcanzable)."""
    def in_arc(a, arc):
        a = a % 360
        lo, hi = arc[0] % 360, arc[1] % 360
        return lo - 1e-6 <= a <= hi + 1e-6 if lo <= hi else (a >= lo - 1e-6 or a <= hi + 1e-6)
    for k in (2, 3):
        lt = PIN_PHI[k] + th_t                       # posición del perno en el marco del acelerador
        lb = PIN_PHI[k] + th_b                       # … en el marco de la palanca del bucket
        t_ok = in_arc(lt, GROOVES_T[k])
        b_ok = abs(((lb - NOTCHES_B[k]) + 180) % 360 - 180) < 1e-6
        if not (t_ok or b_ok):
            return False
    return True
