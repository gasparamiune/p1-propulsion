// ARGOS engine ECU - small numeric helpers (header-only, no allocation; v2.8.3: RateAccelTracker)
#pragma once
#include <cmath>
#include <cstdint>

namespace ecu {

inline float clampf(float x, float lo, float hi) { return x < lo ? lo : (x > hi ? hi : x); }

// Symmetric slew-rate limiter
struct RateLimiter {
  float y = 0;
  bool init = false;
  float step(float x, float rate_per_s, float dt) {
    if (!init) { y = x; init = true; return y; }
    const float d = rate_per_s * dt;
    y += clampf(x - y, -d, d);
    return y;
  }
  void reset(float x) { y = x; init = true; }
};

// v2.8.3: rate- and acceleration-limited command tracker (GNC gnc.json v3 flight_software.gimbal_command_tracker, as GNC sim6
// v2.6 l.1224-1243): time-optimal braking toward the target, v_d = sign(e) min(sqrt(2 a |e|), |e| / dt, v_max), then
// |dv| <= a dt; the velocity is updated first and the position integrates the NEW velocity (semi-implicit, as sim6).
struct RateAccelTracker {
  float y = 0, v = 0;
  bool init = false;
  float step(float x, float v_max, float a_max, float dt) {
    if (!init) { y = x; v = 0; init = true; return y; }
    const float e = x - y, ae = std::fabs(e);
    float vd = std::sqrt(2.0f * a_max * ae);
    if (vd > ae / dt) vd = ae / dt;
    if (vd > v_max) vd = v_max;
    if (e < 0.0f) vd = -vd;
    v += clampf(vd - v, -a_max * dt, a_max * dt);
    y += v * dt;
    return y;
  }
  void reset(float x) { y = x; v = 0; init = true; }
};

// First-order low-pass, bilinear-free exact discretisation alpha = 1 - exp(-2 pi fc dt)
struct LowPass1 {
  float y = 0;
  bool init = false;
  float a = 1.0f;
  void setup(float fc_Hz, float dt) { a = 1.0f - std::exp(-2.0f * 3.14159265f * fc_Hz * dt); }
  float step(float x) {
    if (!init) { y = x; init = true; return y; }
    y += a * (x - y);
    return y;
  }
  void reset(float x) { y = x; init = true; }
};

// Second-order Butterworth low-pass (bilinear transform with pre-warping), transposed direct form II (v2.2:
// Pc path at 50 Hz against the 144-188 Hz, zeta < 0.03 sense-line resonance reported by Combustion v2)
struct LowPass2 {
  float b0 = 1, b1 = 0, b2 = 0, a1 = 0, a2 = 0, z1 = 0, z2 = 0, y = 0;
  bool init = false;
  void setup(float fc_Hz, float dt, float q = 0.70710678f) {
    const float k = std::tan(3.14159265f * fc_Hz * dt);
    const float n = 1.0f / (1.0f + k / q + k * k);
    b0 = k * k * n; b1 = 2.0f * b0; b2 = b0;
    a1 = 2.0f * (k * k - 1.0f) * n; a2 = (1.0f - k / q + k * k) * n;
  }
  float step(float x) {
    if (!init) reset(x);
    y = b0 * x + z1;
    z1 = b1 * x - a1 * y + z2;
    z2 = b2 * x - a2 * y;
    return y;
  }
  void reset(float x) { y = x; z1 = x * (1.0f - b0); z2 = x * (b2 - a2); init = true; }   // steady state at x
};

// Second-order command low-pass (v2.4, GNC gnc.json v2 requirements.gimbal.command_shaping_in_ecu, MANDATORY): the same
// difference equations as GNC sim6 v2.5 (semi-implicit Euler, rate state first) so the ECU reproduces the validated chain;
// at w dt = 0.05 (50 rad/s, 1 kHz) the discretisation error against the continuous filter is < 1 %.
struct Lpf2Cmd {
  float y = 0, yd = 0;
  bool init = false;
  float step(float x, float w, float zeta, float dt) {
    if (!init) reset(x);
    yd += (w * w * (x - y) - 2.0f * zeta * w * yd) * dt;
    y += yd * dt;
    return y;
  }
  void reset(float x) { y = x; yd = 0; init = true; }
};

// Second-order notch of finite depth (v2.4, ENG-07d): RBJ "peaking EQ" with negative gain, bilinear transform with the
// centre placed exactly at f0; unity gain at DC and Nyquist, gain 10^(depth_dB/20) at f0. Transposed direct form II.
struct Notch2 {
  float b0 = 1, b1 = 0, b2 = 0, a1 = 0, a2 = 0, z1 = 0, z2 = 0;
  bool init = false;
  void setup(float f0_Hz, float q, float depth_dB, float dt) {
    const float w0 = 2.0f * 3.14159265f * f0_Hz * dt;
    const float A = std::pow(10.0f, depth_dB / 40.0f);
    const float al = std::sin(w0) / (2.0f * q), c = std::cos(w0);
    const float a0 = 1.0f + al / A;
    b0 = (1.0f + al * A) / a0; b1 = -2.0f * c / a0; b2 = (1.0f - al * A) / a0;
    a1 = b1; a2 = (1.0f - al / A) / a0;
  }
  float step(float x) {
    if (!init) reset(x);
    const float y = b0 * x + z1;
    z1 = b1 * x - a1 * y + z2;
    z2 = b2 * x - a2 * y;
    return y;
  }
  void reset(float x) { z1 = x * (1.0f - b0); z2 = x * (b2 - a2); init = true; }   // steady state at a constant input x
};

// Episode statistics (v2.4 ENG-07b): duration of the episode in progress, longest episode, completed episodes, and episodes
// longer than t_long (counted once, when they pass t_long). resetStats() keeps an episode in progress running.
struct EpisodeTimer {
  float t = 0, t_max = 0;
  uint16_t count = 0;
  uint8_t n_long = 0;
  bool long_now = false;
  void step(bool on, float dt, float t_long) {
    if (on) {
      t += dt;
      if (t > t_max) t_max = t;
      if (!long_now && t > t_long) { long_now = true; if (n_long < 255) ++n_long; }
    } else {
      if (t > 0 && count < 65535) ++count;
      t = 0; long_now = false;
    }
  }
  void reset() { t = 0; t_max = 0; count = 0; n_long = 0; long_now = false; }
  void resetStats() { t_max = t; count = 0; n_long = 0; long_now = false; }
};

// Persistence timer: true once 'cond' has held continuously for >= t_req
struct Persist {
  float t = 0;
  bool step(bool cond, float t_req, float dt) {
    t = cond ? t + dt : 0.0f;
    return t >= t_req;
  }
  void reset() { t = 0; }
};

// N:1 boxcar decimator for the 4 kHz ADC stream -> 1 kHz (combined with sinc3 in the ADC this
// gives > 40 dB rejection near 4 kHz +/- 0.5 kHz; see REPORT anti-aliasing section)
template <int N>
struct Decimator {
  float acc = 0;
  int k = 0;
  bool push(float x, float& out) {
    acc += x;
    if (++k == N) { out = acc / N; acc = 0; k = 0; return true; }
    return false;
  }
};

}  // namespace ecu
