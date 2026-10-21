// ARGOS engine ECU - TVC supply monitor, fault mode FM-PWR-01 (v2.3, 2026-10-12; LEAD decisions 2026-10-12)
//
// Predicts the TVC servo PLUG voltage with both TVC servos at stall (the holding case that sizes the supply,
// calc/tvc_supply_budget_v1.py) from the two board measurements the ECU has:
//   V_board  A0, VBAT node after the main fuse and shunt (divider 10k/3.3k)
//   I_bat    A2, total battery current (INA181A1 x20 on 2 mOhm)
// Model: V_board = V_oc - I_bat R_src;  V_plug = V_oc - (2 I_s + I_o) R_src - I_s R_br,eq
//   V_oc      load-compensated pack voltage, LPF(V_board + I_bat R_src)
//   R_src     source path (pack + leads + XT60 + F101 + shunt + PCB): max(bench calibration, in-situ estimate)
//   R_br,eq   VBAT node -> servo plug per servo, the shared TVC switch path counted twice (both servos at equal current):
//             not observable from V_board/I_bat -> bench calibration only (B-PWR-2)
//   I_s, I_o  design currents: servo stall at the design voltage, other loads
// In-situ R_src: exponentially weighted least-squares slope of V_board against I_bat over a kRsrcWin_s window, accepted when
// the current variance proves excitation (servo slews: pre-flight TVC sweep on the pad, gimbal activity in flight) and the
// slope is physical. The estimate includes pack polarisation on the window time scale (conservative for a 0.1-1 s hold).
// Pure computation, no I/O: the same code runs on the Teensy and in the SIL.
#pragma once
#include <cmath>
#include "config.h"
#include "filters.h"

namespace ecu {

class SupplyMonitor {
 public:
  void reset() { init_ = false; measured_ = false; n_acc_ = 0; }
  void step(float v_board, float i_bat, float dt) {
    using namespace cfg;
    if (!std::isfinite(v_board) || !std::isfinite(i_bat)) return;   // keep the last prediction on a bad sample
    if (!init_) {
      m_i_ = i_bat; m_v_ = v_board; s_ii_ = 0; s_vi_ = 0; init_ = true;
      voc_lpf_.setup(kSupplyVocFc_Hz, dt); voc_lpf_.reset(v_board + i_bat * rsrcUsed());
    }
    const float a = clampf(dt / kRsrcWin_s, 0.0f, 1.0f);
    const float di = i_bat - m_i_, dv = v_board - m_v_;
    m_i_ += a * di; m_v_ += a * dv;
    s_ii_ = (1.0f - a) * (s_ii_ + a * di * di);
    s_vi_ = (1.0f - a) * (s_vi_ + a * di * dv);
    excited_ = s_ii_ > kRsrcMinVar_A2;
    if (excited_) {
      const float r = -s_vi_ / s_ii_;
      if (r > kRsrcMin_ohm && r < kRsrcMax_ohm) {
        r_est_ = measured_ ? r_est_ + clampf(dt / kRsrcAvg_s, 0.0f, 1.0f) * (r - r_est_) : r;
        measured_ = true; ++n_acc_;
      }
    }
    voc_ = voc_lpf_.step(v_board + i_bat * rsrcUsed());
  }
  // source resistance used for the prediction: never below the bench calibration
  float rsrcUsed() const { return measured_ ? std::fmax(r_est_, cfg::kRSrcCal_ohm) : cfg::kRSrcCal_ohm; }
  float rsrcEstimate() const { return measured_ ? r_est_ : NAN; }
  bool measured() const { return measured_; }
  bool excited() const { return excited_; }
  float voc() const { return voc_; }
  float vplugPred() const {   // NAN until the first valid sample (callers treat NAN as "not OK")
    using namespace cfg;
    if (!init_) return NAN;
    return voc_ - (2.0f * kTvcServoDesign_A + kAuxDesign_A) * rsrcUsed() - kTvcServoDesign_A * kRBranchEqCal_ohm;
  }
  unsigned accepted() const { return n_acc_; }

 private:
  bool init_ = false, measured_ = false, excited_ = false;
  float m_i_ = 0, m_v_ = 0, s_ii_ = 0, s_vi_ = 0, r_est_ = 0, voc_ = 0;
  unsigned n_acc_ = 0;
  LowPass1 voc_lpf_;
};

}  // namespace ecu
