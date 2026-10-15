"""v0 lift capability and landing-closure window for a 500 N throttleable hybrid.
Point-mass, vertical, flat-earth, ISA sea-level density. Seed numbers only; the Space/GNC
specialist replaces this with a 6-DOF + Monte Carlo analysis."""
import numpy as np
g0 = 9.80665
F_MAX = 500.0           # N, max sea-level thrust (founder requirement)
ISP = 205.0             # s, delivered, assumed (CEA 234 s theoretical x ~0.88)
RHO = 1.2
def sim(m_dry, m_prop, apogee_target, d=0.13, cd_up=0.6, cd_down=0.9, landing_tw=2.0, dt=1e-3):
    A = np.pi * d**2 / 4
    m = m_dry + m_prop; h = 0.0; v = 0.0; t = 0.0
    # ascent at full thrust until coast apogee (with drag) reaches target
    def coast_apogee(h, v, m):
        while v > 0:
            a = -g0 - 0.5*RHO*cd_up*A*v*v/m
            v += a*dt; h += v*dt
        return h
    used = 0.0
    while True:
        if coast_apogee(h, v, m) >= apogee_target: break
        mdot = F_MAX/(ISP*g0)
        a = (F_MAX - 0.5*RHO*cd_up*A*v*v)/m - g0
        v += a*dt; h += v*dt; m -= mdot*dt; used += mdot*dt; t += dt
        if used > m_prop: return None
    t_asc = t
    # coast up
    while v > 0:
        v += (-g0 - 0.5*RHO*cd_up*A*v*v/m)*dt; h += v*dt; t += dt
    h_apo = h
    # fall; ignite when constant-thrust (T = landing_tw * W_now) stop distance equals height
    while True:
        dec = landing_tw*g0 - g0     # net decel available (approx, ignoring drag)
        if h <= v*v/(2*dec): break
        v += (-g0 + 0.5*RHO*cd_down*A*v*v/m)*dt; h += v*dt; t += dt
    v_ign, h_ign = v, h
    # landing burn: thrust law that tracks v^2 = 2*a*h (closed-form guidance), clipped to [0, F_MAX]
    used_land = 0.0
    while h > 0.0 and v < -0.05:
        a_req = v*v/(2*max(h, 1e-3))
        T = m*(a_req + g0) - 0.5*RHO*cd_down*A*v*v
        T = min(max(T, 0.0), F_MAX)
        mdot = T/(ISP*g0)
        v += (T + 0.5*RHO*cd_down*A*v*v)/m*dt - g0*dt; h += v*dt
        m -= mdot*dt; used_land += mdot*dt; t += dt
    return dict(t_asc=t_asc, h_apo=h_apo, v_ign=v_ign, h_ign=h_ign, used_asc=used,
                used_land=used_land, m_land=m, total=used+used_land, t_total=t)

print("Lift capability at 500 N (static thrust-to-weight):")
for tw in [1.2, 1.5, 2.0, 2.5, 3.0, 4.0]:
    print(f"  liftoff T/W {tw:3.1f} -> max liftoff mass {F_MAX/(tw*g0):5.1f} kg")
print("\nLanding window: min landing mass to hover at the throttle floor (T_min <= 0.9 W),"
      "\nmax landing mass for T_max/W >= 2:")
for floor in [0.15, 0.20, 0.25, 0.33, 0.40]:
    print(f"  floor {floor*100:4.0f}% ({F_MAX*floor:5.0f} N): hover needs m_land >= {F_MAX*floor/(0.9*g0):5.1f} kg;"
          f" T_max/W>=2 needs m_land <= {F_MAX/(2*g0):4.1f} kg")

print("\nPropellant for the reference flight (full-thrust ascent, MECO, coast, fall, relight,"
      " hoverslam at T/W 2), +25 % reserve:")
print(" m_dry  apogee  prop_used  prop_loaded  m_liftoff  T/W_lo  v_ign  h_ign  t_flight  I_total")
for m_dry in [10.0, 12.0, 14.0, 16.0]:
    for apo in [100.0, 200.0, 300.0]:
        mp = 0.5
        for _ in range(40):
            r = sim(m_dry, mp, apo)
            if r is None: mp *= 1.3; continue
            need = r['total']*1.25
            if abs(need-mp) < 1e-3: break
            mp = need
        lo = m_dry + mp
        print(f" {m_dry:5.1f}  {apo:5.0f}   {r['total']:7.3f}    {mp:7.3f}     {lo:6.2f}    {F_MAX/(lo*g0):4.2f}"
              f"  {-r['v_ign']:5.1f}  {r['h_ign']:5.1f}  {r['t_total']:6.1f}   {mp*ISP*g0:6.0f}")
