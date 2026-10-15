// ARGOS engine ECU - Pc controller, valve map, pintle linkage, thrust model, TVC shaping (v2)
#include "control.h"
#include <cmath>
#include "valve_map_table.h"

namespace ecu {

// ------------------------------------------------------------------------------------ linkage
// v3 (2026-10-12): MKS HV69 on an in-line crank-slider (pintle_mini_servo_v1 TOG r 3.0 mm, phi_c 15 deg, link L 28 mm):
// s(phi) = r cos(phi) + sqrt(L^2 - r^2 sin^2 phi), lift x = s(phi_c) - s(phi) (tension link; lost motion below phi_c).
// v2.1 (SB-2292SG crank-pin roller on a flat follower, x = r (cos phi_c - cos phi)) is in tools/archive.
namespace linkage {
static float sOf(float phi) {
  using namespace eng;
  const float rs = kCrankR_m * std::sin(phi);
  return kCrankR_m * std::cos(phi) + std::sqrt(kLinkL_m * kLinkL_m - rs * rs);
}
float liftToCrank(float x) {
  using namespace eng;
  if (x <= 0.0f) return kCrankPhiContact_rad - kCrankLostMotion_rad;
  // closed form of s(phi) = S: cos(phi) = (S^2 + r^2 - L^2) / (2 S r), S = s(phi_c) - x
  const float S = sOf(kCrankPhiContact_rad) - x;
  const float c = clampf((S * S + kCrankR_m * kCrankR_m - kLinkL_m * kLinkL_m) / (2.0f * S * kCrankR_m), -1.0f, 1.0f);
  return std::acos(c);
}
float crankToLift(float phi) {
  using namespace eng;
  if (phi <= kCrankPhiContact_rad) return 0.0f;
  return std::fmax(0.0f, sOf(kCrankPhiContact_rad) - sOf(phi));
}
float dLiftDCrank(float x) {
  using namespace eng;
  const float phi = liftToCrank(x > 1e-6f ? x : 1e-6f);
  const float rs = kCrankR_m * std::sin(phi);
  return rs * (1.0f + kCrankR_m * std::cos(phi) / std::sqrt(kLinkL_m * kLinkL_m - rs * rs));
}
float liftToUs(float x, const PintleCal& c) {
  const float psi = liftToCrank(x) - eng::kCrankPhiNeutral_rad;   // servo angle from neutral
  return clampf(c.center_us + c.trim_us + c.dir * psi * 57.29578f * c.us_per_deg, c.min_us, c.max_us);
}
float liftToUs(float x, float trim, float dir) {
  PintleCal c; c.trim_us = trim; c.dir = dir;
  return liftToUs(x, c);
}
}  // namespace linkage

// ------------------------------------------------------------------------------------ thrust model
namespace thrust {
// piecewise-linear in (Pc_abs, Fvac = F + pa*Ae), linear extrapolation from the end segments; the two directions
// are exact inverses of each other (Fvac strictly increasing in Pc, checked by test_core)
static float interp(const float* xs, const float* ys, int n, float x) {
  int i = 0;
  if (x >= xs[n - 1]) i = n - 2;
  else while (i < n - 2 && x > xs[i + 1]) ++i;
  return ys[i] + (ys[i + 1] - ys[i]) * (x - xs[i]) / (xs[i + 1] - xs[i]);
}
float pcAbsFromThrust(float F, float pa) { return interp(eng::kThrFvac_N, eng::kThrPcAbs_Pa, eng::kNThr, F + pa * eng::kAe_m2); }
float thrustFromPcAbs(float pc, float pa) { return interp(eng::kThrPcAbs_Pa, eng::kThrFvac_N, eng::kNThr, pc) - pa * eng::kAe_m2; }
}  // namespace thrust

// ------------------------------------------------------------------------------------ ValveMap
static int bracket(const float* g, int n, float v, float* frac) {
  if (v <= g[0]) { *frac = 0; return 0; }
  if (v >= g[n - 1]) { *frac = 1; return n - 2; }
  int i = 0;
  while (i < n - 2 && v > g[i + 1]) ++i;
  *frac = (v - g[i]) / (g[i + 1] - g[i]);
  return i;
}

float ValveMap::lift(float pc_sp, float ptank, float* gain) {
  // (gain may be nullptr)
  float fp, fq;
  const int i = bracket(vmap::kPcGrid_Pa, vmap::kNPc, pc_sp, &fp);
  const int j = bracket(vmap::kPtGrid_Pa, vmap::kNPt, ptank, &fq);
  auto bil = [&](const float (*t)[vmap::kNPc]) {
    const float a = t[j][i] + fp * (t[j][i + 1] - t[j][i]);
    const float b = t[j + 1][i] + fp * (t[j + 1][i + 1] - t[j + 1][i]);
    return a + fq * (b - a);
  };
  if (gain) *gain = bil(vmap::kGain_Pa_per_m);
  return bil(vmap::kLift_m);
}

float ValveMap::pcForLift(float x, float ptank) {
  float fq;
  const int j = bracket(vmap::kPtGrid_Pa, vmap::kNPt, ptank, &fq);
  float prev = 0.0f;
  for (int i = 0; i < vmap::kNPc; ++i) {
    const float Li = vmap::kLift_m[j][i] + fq * (vmap::kLift_m[j + 1][i] - vmap::kLift_m[j][i]);
    if (x <= Li) {
      if (i == 0) return vmap::kPcGrid_Pa[0];
      const float f = (x - prev) / (Li - prev);
      return vmap::kPcGrid_Pa[i - 1] + f * (vmap::kPcGrid_Pa[i] - vmap::kPcGrid_Pa[i - 1]);
    }
    prev = Li;
  }
  return vmap::kPcGrid_Pa[vmap::kNPc - 1];
}

// ------------------------------------------------------------------------------------ PcController
void PcController::reset(float x_now, float ptank) {
  const float pc0 = ValveMap::pcForLift(x_now, ptank);
  sp_rl_.reset(pc0);
  x_rl_.reset(x_now);
  ref_lpf_.setup(1.0f / (6.2831853f * cfg::kRefModelTau_s), cfg::kDt_s);
  ref_lpf_.reset(pc0);
  for (int i = 0; i < kRefN; ++i) ref_buf_[i] = pc0;
  ref_idx_ = 0; ref_ = pc0;
  float g = 1e9f;
  x_ff_ = ValveMap::lift(pc0, ptank, &g);
  // the multiplicative trim learned in earlier burns of this flight is kept (same engine, same injector);
  // only its rate of change is reset by the RUN-entry hold
}

void PcController::clearTrim() { trim_ = 0.0f; }

float PcController::step(float pc_sp, float pc_meas, float ptank, float dt, bool closed_loop, bool integrate) {
  using namespace cfg;
  const float sp = sp_rl_.step(clampf(pc_sp, kPcSpMinAbs_Pa, kPcSpMaxAbs_Pa), kPcSpRateLimit_Paps, dt);
  // reference model: dead time (ring buffer, whole ticks) then first-order lag
  int nd = static_cast<int>(kRefModelDelay_s / dt + 0.5f);
  if (nd > kRefN - 1) nd = kRefN - 1;
  if (nd < 0) nd = 0;
  ref_buf_[ref_idx_] = sp;
  const float delayed = ref_buf_[(ref_idx_ - nd + kRefN) % kRefN];
  ref_idx_ = (ref_idx_ + 1) % kRefN;
  ref_ = ref_lpf_.step(delayed);
  float g = 1.0e9f;
  x_ff_ = ValveMap::lift(sp, ptank, &g);
  if (g < 1.0e8f) g = 1.0e8f;                 // guard: 1 bar/mm minimum assumed plant gain
  // multiplicative trim: the integrator learns the ratio between the lift the engine needs and the map lift
  // (Cd, regression-law and c* efficiency errors scale the flow, so a ratio learned at one thrust is valid at
  // another; an additive lift offset learned at 500 N drove the lift to the floor clamp after a step to 100 N)
  const float scale = 1.0f + trim_;
  const float x_min = scale * ValveMap::lift(kLiftMinRunFrac * kPcSpMinAbs_Pa, ptank, nullptr);
  if (!closed_loop) {   // Pc sensor fault: map x learned trim (trim frozen)
    return x_rl_.step(clampf(scale * x_ff_, x_min, kPintleLiftMaxCmd_m), kPintleRateCmd_mps, dt);
  }
  const float kp = kKpNorm / g;              // [m/Pa]
  const float xr = std::fmax(x_ff_, 1.0e-4f);
  const float ki = kKiNorm_ps / (g * xr);    // [1/(Pa s)] trim rate per Pa of error: integral loop gain = kKiNorm
  const float e = ref_ - pc_meas;
  const float u_unsat = scale * x_ff_ + kp * e;
  const float u_sat = clampf(u_unsat, x_min, kPintleLiftMaxCmd_m);
  const float u = x_rl_.step(u_sat, kPintleRateCmd_mps, dt);
  // freeze band = fraction of the Pc change produced by one servo deadband step at this operating point
  const float dx_db = linkage::dLiftDCrank(u) * (kPintleDeadband_us / kPintleUsPerDeg) * 0.01745329f;
  band_ = std::fmax(kFreezeBandMin_Pa, kFreezeBandFrac * g * dx_db);
  // conditional integration: stop integrating in the direction that deepens saturation/rate limiting
  const bool pushing_high = (u_unsat > u + 1e-7f) && e > 0;
  const bool pushing_low = (u_unsat < u - 1e-7f) && e < 0;
  // transient hold: while the reference model is still travelling toward the setpoint the error is dominated by
  // actuator/chamber dynamics the map already covers (and, at low O/F, by the c*(O/F) lead): do not integrate it
  const bool ref_settled = std::fabs(sp - ref_) < std::fmax(band_, kIntegRefTolFrac * sp);
  if (integrate && ref_settled && !pushing_high && !pushing_low && std::fabs(e) > band_) trim_ += ki * e * dt;
  trim_ = clampf(trim_, -kTrimLimit, kTrimLimit);
  return u;
}

// ------------------------------------------------------------------------------------ TvcShaper
float TvcShaper::leverDz(float alpha, float beta, int i) {
  // ball at (r cos az, r sin az, z_b) in the engine frame; R = Rx(alpha) Ry(beta); return z' - z_b
  const float x0 = mech::kLeverR_m * std::cos(mech::kLeverAz_rad[i]);
  const float y0 = mech::kLeverR_m * std::sin(mech::kLeverAz_rad[i]);
  const float z0 = mech::kLeverBallZ_m;
  const float z1 = -x0 * std::sin(beta) + z0 * std::cos(beta);
  const float z2 = y0 * std::sin(alpha) + z1 * std::cos(alpha);
  return z2 - z0;
}
float TvcShaper::servoAngle(float alpha, float beta, int i, float horn_r) {
  // lever eye P = Rx(alpha) Ry(beta) P0; horn eye H(psi) = C + r_h (-cos(psi) u + sin(psi) z); |P - H| = L
  // -> -du cos(psi) + dz sin(psi) = K, K = (|d|^2 + r_h^2 - L^2) / (2 r_h), d = P - C, du = d.u, dz = d.z (Mechanical's
  // tvc_kinematics.py formulation); of the two solutions the one nearest 0 is the assembled branch.
  const float* p0 = mech::kLeverEye0_m[i & 1];
  const float ca = std::cos(alpha), sa = std::sin(alpha), cb = std::cos(beta), sb = std::sin(beta);
  const float x1 = p0[0] * cb + p0[2] * sb, z1 = -p0[0] * sb + p0[2] * cb;
  const float* C = mech::kShaftC_m[i & 1];
  const float* u = mech::kHornU[i & 1];
  const float d0 = x1 - C[0], d1 = (p0[1] * ca - z1 * sa) - C[1], d2 = (p0[1] * sa + z1 * ca) - C[2];
  const float du = d0 * u[0] + d1 * u[1];
  const float L = mech::kPushrod_m;
  const float K = (d0 * d0 + d1 * d1 + d2 * d2 + horn_r * horn_r - L * L) / (2.0f * horn_r);
  const float rho = std::sqrt(d2 * d2 + du * du), phi0 = std::atan2(-du, d2);
  const float base = std::asin(clampf(K / rho, -1.0f, 1.0f));
  auto wrap = [](float x) { return std::remainder(x, 6.2831853f); };
  const float c1 = wrap(base - phi0), c2 = wrap(3.14159265f - base - phi0);
  return std::fabs(c1) <= std::fabs(c2) ? c1 : c2;
}

void TvcShaper::reset(const float now[2]) {
  for (int k = 0; k < 2; ++k) { rl_[k].reset(now[k]); lpf_[k].reset(now[k]); notch_[k].f.reset(now[k]); }
  lim_ = 0;
}

bool TvcShaper::setNotch(bool enabled, float f0_Hz, float q, float depth_dB, float dt) {
  NotchAxis n; n.enabled = enabled; n.f0_Hz = f0_Hz; n.q = q; n.depth_dB = depth_dB;
  if (!n.valid(dt)) return false;            // all-or-nothing: both axes keep their setting
  setNotchAxis(0, n, dt);
  setNotchAxis(1, n, dt);
  return true;
}

bool TvcShaper::setNotchAxis(int axis, const NotchAxis& n, float dt) {
  AxisNotch& a = notch_[axis & 1];
  NotchAxis on = n; on.enabled = true;
  const bool vals_ok = on.valid(dt);
  if (!n.enabled) { a.en = false; if (vals_ok) a.cfg = on; return true; }   // disabling always works; valid values are kept
  if (!vals_ok) return false;
  a.cfg = on; a.en = true;
  const int k = axis & 1;
  const float y = lpf_w_radps > 0 ? lpf_[k].y : rl_[k].y;   // start at the notch input (low-pass output): no kick on enable
  a.f.setup(n.f0_Hz, n.q, n.depth_dB, dt); a.f.reset(y);
  return true;
}

void TvcShaper::step(const float cmd[2], float dt, float out_e[2], float out_us[2]) {
  using namespace cfg;
  lim_ = 0;
  // (1) pre-limit the raw command vector at 2 x range so the shaping states stay bounded (GNC sim6 v2.5)
  float c[2] = {std::isfinite(cmd[0]) ? cmd[0] : 0.0f, std::isfinite(cmd[1]) ? cmd[1] : 0.0f};
  const float pre = kGimbalPreLimitFactor * kGimbalRadialLimit_rad, r0 = std::sqrt(c[0] * c[0] + c[1] * c[1]);
  if (r0 > pre) { c[0] *= pre / r0; c[1] *= pre / r0; }
  for (int k = 0; k < 2; ++k) {
    // (2) per-axis slew limit 100 deg/s, (3) 2nd-order structural low-pass 50 rad/s zeta 0.5, (4) optional notch
    const float rl = rl_[k].step(c[k], rate_limit_radps, dt);
    if (std::fabs(rl - c[k]) > 1e-6f) lim_ |= 2u;
    float y = lpf_w_radps > 0 ? lpf_[k].step(rl, lpf_w_radps, lpf_zeta, dt) : rl;
    if (notch_[k].en) y = notch_[k].f.step(y);
    out_e[k] = bypass_filters ? rl : y;
  }
  // (5) hard limits last (the zeta 0.5 low-pass overshoot is clipped here): 7 deg per axis and on the vector norm
  float a = clampf(out_e[0], -kGimbalSoftLimit_rad, kGimbalSoftLimit_rad);
  float b = clampf(out_e[1], -kGimbalSoftLimit_rad, kGimbalSoftLimit_rad);
  if (a != out_e[0] || b != out_e[1]) lim_ |= 1u;
  const float r = std::sqrt(a * a + b * b);
  if (r > kGimbalRadialLimit_rad) { a *= kGimbalRadialLimit_rad / r; b *= kGimbalRadialLimit_rad / r; lim_ |= 1u; }
  out_e[0] = a; out_e[1] = b;
  // v2.6: exact pushrod solve (as-built linkage), relative to the neutral solution (zero for the nominal horn; with a
  // bench-measured horn radius the neutral offset belongs to the centre trim), then the per-sense horn clamp between the 7 deg
  // need and the 8 deg stop
  for (int i = 0; i < 2; ++i) {
    const float psi = clampf(servoAngle(out_e[0], out_e[1], i, horn_r_m) - servoAngle(0.0f, 0.0f, i, horn_r_m),
                             kTvcPsiMin_rad, kTvcPsiMax_rad);
    const float us = kServoCenter_us + trim_us[i] + dir[i] * psi * 57.29578f * kServoUsPerDeg;
    out_us[i] = clampf(us, kServoMin_us, kServoMax_us);
  }
}

}  // namespace ecu
