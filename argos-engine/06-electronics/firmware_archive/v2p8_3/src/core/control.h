// ARGOS engine ECU - Pc controller, feed-forward valve map, pintle linkage, thrust model, TVC shaping (v2; v2.8.3: gnc.json v3 tracker)
#pragma once
#include <cmath>
#include "config.h"
#include "filters.h"

namespace ecu {

// Pintle in-line crank-slider (v3, MKS HV69, pintle_mini_servo_v1): x = s(phi_c) - s(phi),
// s(phi) = r cos(phi) + sqrt(L^2 - r^2 sin^2 phi), phi from top dead centre (eng::kCrankR_m, kLinkL_m, kCrankPhiContact_rad).
namespace linkage {
float liftToCrank(float x_m);          // closed (x <= 0) -> contact angle minus lost motion
float crankToLift(float phi_rad);      // 0 below contact (needle seated by its spring)
float dLiftDCrank(float x_m);          // [m/rad]
float liftToUs(float x_m, float trim_us, float dir);   // default calibration (config.h) plus trim and direction
// v2.6 (LEAD 2026-10-12): HV69 pulse calibration is a run-time parameter, set from the B-PNT-1 travel sweep (800-2200 us,
// 10 us steps, 1 A limit); defaults = config.h (1520 us neutral, 10 us/deg ASSUMED, clamps 900-2100 us).
struct PintleCal {
  float center_us = cfg::kPintleCenter_us;    // pulse at the neutral crank angle eng::kCrankPhiNeutral_rad
  float us_per_deg = cfg::kPintleUsPerDeg;    // pulse per degree of servo output
  float min_us = cfg::kPintleMin_us;          // clamps (the sweep's usable range less a margin)
  float max_us = cfg::kPintleMax_us;
  float trim_us = 0.0f;                       // fine trim at the seat
  float dir = 1.0f;                           // +1 / -1 (servo mounting)
  bool valid() const {                        // a calibration outside these bounds is refused (setPintleCal)
    return us_per_deg > 5.0f && us_per_deg < 20.0f && min_us >= cfg::kPintleCalMin_us && max_us <= cfg::kPintleCalMax_us &&
           min_us < center_us && center_us < max_us && (dir == 1.0f || dir == -1.0f) && trim_us > -100.0f && trim_us < 100.0f;
  }
};
float liftToUs(float x_m, const PintleCal& c);
}  // namespace linkage

// Sea-level thrust model F = CfE*At*Pc_abs - pa*Ae (CfE fitted to Combustion's map; replace with static-fire fit)
namespace thrust {
float pcAbsFromThrust(float F_N, float pa_Pa);
float thrustFromPcAbs(float pc_abs_Pa, float pa_Pa);
}  // namespace thrust

// Feed-forward map: lift needed for an absolute Pc setpoint at a given absolute tank pressure, plus the
// local plant gain g = dPc/dx [Pa/m] used for gain scheduling. Table generated offline (sil/gen_valve_map)
// from the SIL plant that reproduces Combustion's lumped model; replace with cold-flow / hot-fire data.
struct ValveMap {
  static float lift(float pc_sp_abs_Pa, float ptank_abs_Pa, float* gain_Pa_per_m);
  static float pcForLift(float lift_m, float ptank_abs_Pa);   // inverse along Pc (monotonic rows)
};

// Two-degree-of-freedom Pc control: the feed-forward map makes the fast response; a gain-scheduled PI acts
// (integral part = multiplicative trim on the map lift, v2.1)
// on the error between a reference model of the expected Pc response (dead time + lag applied to the
// rate-limited setpoint) and the measured Pc, so transport delay does not wind up the integrator.
// Conditional-integration anti-windup, command rate limit (matched to the pintle servo), lower lift clamp
// against controller-induced flameout, and an integrator freeze band sized to one servo deadband step at
// the current operating point (prevents deadband hunting).
class PcController {
 public:
  // Bumpless start: setpoint ramp starts from the map Pc of the current lift, integrator cleared, so the
  // first command equals the current lift and the ignition transient (fuel thermal lag) is not integrated.
  void reset(float x_now_m, float ptank_abs_Pa);
  // Returns pintle lift command [m]. closed_loop=false -> pure feed-forward (Pc sensor fault).
  float step(float pc_sp_abs_Pa, float pc_meas_abs_Pa, float ptank_abs_Pa, float dt, bool closed_loop, bool integrate = true);
  float setpointActive() const { return sp_rl_.y; }
  float integrator() const { return trim_ * x_ff_; }   // equivalent lift correction [m] (telemetry)
  float trim() const { return trim_; }                  // learned lift ratio - 1 [-]
  void clearTrim();                                     // new engine/injector or ground reset
  float ff() const { return x_ff_; }
  float freezeBand() const { return band_; }
  float refModel() const { return ref_; }
 private:
  RateLimiter sp_rl_, x_rl_;
  LowPass1 ref_lpf_;
  static constexpr int kRefN = 16;
  float ref_buf_[kRefN] = {0};
  int ref_idx_ = 0;
  float trim_ = 0, x_ff_ = 0, band_ = 0, ref_ = 0;
};

// v2.4 ENG-07b actuator-saturation proxy for one axis: the encoder is off the first-order expected response of the shaped
// command (model, time constant cfg::kGimbalModelTau_s) by more than kGimbalSatErr_rad plus kGimbalSatRateWin_s x the model
// rate (the healthy actuator's own lag, 9-22 ms for 10-25 Hz, differs from the 20 ms model during slews). Shared by the
// firmware and the SIL so both count the same episodes. Calibrate against servo current at B-TVC-1.
inline bool satProxyAxis(float model_rad, float model_rate_radps, float meas_rad) {
  return std::fabs(model_rad - meas_rad) > cfg::kGimbalSatErr_rad + cfg::kGimbalSatRateWin_s * std::fabs(model_rate_radps);
}

// v2.6 (LEAD 2026-10-12, GNC csi_v3): the ENG-07d notch is REQUIRED and set PER AXIS - the alpha and beta rocking modes differ by
// 8-15 %. One record per axis (B-TVC-1 measurement), settable in SAFE, stored non-volatile by the HAL (protocol.h NvGimbalCal)
// and applied at boot, so the notch stays enabled once B-TVC-1 has set it.
struct NotchAxis {
  bool enabled = false;
  float f0_Hz = cfg::kGimbalNotchHz;
  float q = cfg::kGimbalNotchQ;
  float depth_dB = cfg::kGimbalNotchDepth_dB;     // negative = attenuation at f0
  bool valid(float dt) const {                    // a disabled axis is always valid; an enabled one must be inside the ranges
    return !enabled || (std::isfinite(f0_Hz) && f0_Hz >= cfg::kGimbalNotchMinHz && f0_Hz <= cfg::kGimbalNotchMaxHz &&
                        f0_Hz < 0.45f / dt && q >= cfg::kGimbalNotchQMin && q <= cfg::kGimbalNotchQMax &&
                        depth_dB >= cfg::kGimbalNotchDepthMin_dB && depth_dB <= cfg::kGimbalNotchDepthMax_dB);
  }
};
struct GimbalNotchCal {
  NotchAxis ax[2];                                // [0] alpha (outer axis), [1] beta (inner axis)
  bool valid(float dt) const { return ax[0].valid(dt) && ax[1].valid(dt); }
  bool complete() const { return ax[0].enabled && ax[1].enabled; }   // flight requirement: both axes notched
};

// TVC command shaping (GNC command_shaping_in_ecu, per axis at 1 kHz): pre-limit 2 x range on the vector norm, v2.8.3
// (gnc.json v3) rate- and acceleration-limited tracker 100 deg/s, 2000 deg/s2 (v2.4-v2.8.2 plain 100 deg/s slew limit),
// 2nd-order low-pass 50 rad/s zeta 0.5, optional ENG-07d notch, then the hard 7 deg axis and
// vector-norm limits; then the pushrod linkage inverse, servo calibration (centre trim, direction), pulse-width clamp.
// TVC servo mixing (v2.1). Commands are engine angles (alpha = outer axis, beta = inner axis,
// Cardan R = Rx(alpha) Ry(beta)); each servo drives a vertical pushrod to a lever ball on the engine collar
// (mechanical.json v1: azimuths 64.5/154.5 deg, r_e 48 mm, ball 22 mm below the pivot, horn 8 mm).
class TvcShaper {
 public:
  void reset(const float engine_now_rad[2]);
  // cmd_rad/out_engine_rad: [alpha, beta]; out_us: [servo A, servo B]
  void step(const float cmd_rad[2], float dt, float out_engine_rad[2], float out_us[2]);
  float trim_us[2] = {0, 0};      // per-servo centre trim (bench calibration)
  float dir[2] = {1, 1};          // +1/-1 mounting direction
  float horn_r_m = mech::kHornR_m;                     // v2.2: bench-measured horn radius (default mechanical.json)
  float rate_limit_radps = cfg::kGimbalRateLimit_radps;   // v2.2: per-axis command slew limit (SIL capability tests)
  float accel_limit_radps2 = cfg::kGimbalAccelLimit_radps2;   // v2.8.3: tracker acceleration limit (0 = plain slew limiter;
                                                               //   SIL actuator-capability tests only)
  float lpf_w_radps = cfg::kGimbalCmdLpfW_radps;          // v2.4: GNC structural low-pass (0 = off, SIL capability tests only)
  float lpf_zeta = cfg::kGimbalCmdLpfZeta;
  bool bypass_filters = false;    // v2.6 B-TVC-1 frequency response: low-pass and notch outputs bypassed (their states keep
                                  //   running); slew and angle limits stay. Set by the ECU in SAFE TVC-test mode 2 only.
                                  //   v2.8.3: in this mode the output is the plain 100 deg/s slew limiter, not the tracker
                                  //   (a 0.3 deg sine needs > 2000 deg/s2 above ~13 Hz; the mode identification runs to 50 Hz)
  static float leverDz(float alpha, float beta, int servo);      // exact Cardan vertical lever-eye displacement [m]
  // v2.6 horn angle [rad], psi > 0 lifts the horn eye: exact pushrod-length solve on the as-built linkage (mechanical.json v2,
  // horn plane per gen_mech_params v2); the v2.1-v2.5 vertical-rod map asin(dz/r_h) was 2.1 deg of servo angle off at 7 deg.
  // horn_r: bench-measured horn radius; the shaft position (bracket) and the pushrod length stay as built.
  static float servoAngle(float alpha, float beta, int servo, float horn_r = mech::kHornR_m);
  // v2.4 ENG-07d: notch on the engine-angle commands, after the low-pass and ahead of the hard limits; off until calibrated.
  // v2.4 API: the same notch on both axes. Disabling always succeeds; an enable request outside the accepted range is ignored
  // (previous setting kept), returns false.
  bool setNotch(bool enabled, float f0_Hz, float q, float depth_dB, float dt);
  // v2.6: per-axis notch (axis 0 alpha, 1 beta); same semantics, the other axis is untouched
  bool setNotchAxis(int axis, const NotchAxis& n, float dt);
  bool notchEnabled() const { return notch_[0].en || notch_[1].en; }        // any axis
  bool notchEnabled(int axis) const { return notch_[axis & 1].en; }
  float notchHz() const { return notch_[0].cfg.f0_Hz; }                      // v2.4 accessor (alpha)
  NotchAxis notchAxis(int axis) const { NotchAxis n = notch_[axis & 1].cfg; n.enabled = notch_[axis & 1].en; return n; }
  // v2.4: command limiting applied in the last step: b0 7 deg axis or vector limit clipped, b1 rate / acceleration shaping
  // active (v2.8.3: the tracker output differs from the pre-limited command)
  uint8_t limitFlags() const { return lim_; }
  float trackerRate(int axis) const { return tr_[axis & 1].v; }   // v2.8.3 tracker velocity [rad/s] (tests, log context)
 private:
  RateLimiter rl_[2];             // plain slew limiter: runs always; output in B-TVC-1 bypass mode and when accel limit = 0
  RateAccelTracker tr_[2];        // v2.8.3 flight shaping (gnc.json v3)
  float pre_[2] = {0, 0};         // last shaping output ahead of the low-pass (notch enable start value)
  Lpf2Cmd lpf_[2];
  struct AxisNotch { Notch2 f; NotchAxis cfg; bool en = false; };
  AxisNotch notch_[2];
  uint8_t lim_ = 0;
};

}  // namespace ecu
