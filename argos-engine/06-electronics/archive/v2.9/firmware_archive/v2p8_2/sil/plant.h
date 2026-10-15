// ARGOS engine SIL - plant models (v2.8, 2026-10-13: MV-P poppet main valve; v2.6, 2026-10-12). NOT flight code. Predictions, not
// measurements.
//
// EnginePlant  self-pressurised N2O equilibrium tank (m, U) -> main valve (v2.8: MV-P poppet, cam opener, latch release delay,
//              dashpot close; v2.2-v2.7 spring-return ball valve kept as mv_type 0) -> feed line (priming /
//              trapped liquid, line loss dp_line ~ mdot^2) -> variable-area pintle (needle-in-seat frustum area, Dyer
//              flux, v2.5: Combustion v2 inlet convention P1 = injector-inlet (feed) pressure, saturated-liquid
//              properties at the tank temperature) -> combustion delay -> hybrid fuel (r = helix a G^n, first-order
//              thermal lag tau = alpha/rdot^2) -> chamber filling with CEA c*(Pc, O/F), gamma -> sea-level thrust.
//              Torch igniter (2 solenoids + spark) and main-chamber ignition delay; hard-start and flameout hooks.
// HobbyServo   333 Hz frame latch, 12-bit quantisation, deadband, internal P-D loop saturating at full drive,
//              linear torque-speed line interpolated in supply voltage (v2.5: SB-2292SG or MKS HV69 data), friction.
// GimbalAxis   servo + horn + pushrod (stiffness, damping, backlash) + engine on its pivot (inertia, hose
//              stiffness, acceleration moment, misalignment, friction).
// PintleDrive  v2.5: MKS HV69 in-line on the toggle crank-slider (LEAD 2026-10-12: r 3.0 mm, link 28 mm, contact at
//              15 deg, 5 deg lost motion, stop at 4.2 mm), closing spring, pressure force on the needle (seat/stem
//              areas), seal friction; the crank sits on its own bearings (the link side load does not reach the servo).
// GimbalPlant2 (v2.6) two servos on the as-built Cardan gimbal (mechanical.json v2): 3-D pushrods between the horn eyes
//              and the lever eyes (exact eye kinematics, rod forces along the rod through the virtual-work Jacobians),
//              per-axis structure compliance (FEA) between the lever frame and the engine, per-axis inertia (ring on
//              alpha), hose stiffness, acceleration moment, misalignment + side load, bearing friction, conical stop.
//              v2.1-v2.5: v1 geometry, vertical rods, rigid structure.
// SenseLine    (v2.1) Pc sense line (transducer on the fixed side, mechanical.json v1): lumped acoustic line
//              (N inertance/compliance/Poiseuille-resistance sections) closed by the transducer dead volume.
// Every number is tagged here or in plant_tables.h (generated from combustion.json).
#pragma once
#include <cmath>
#include <cstdint>
#include <random>
#include <vector>
#include "gnc_tables.h"
#include "mech_tables.h"
#include "plant_tables.h"

namespace sil {

double satP(double T);                        // N2O saturation pressure [Pa]
double ghemSat(double T, double P2);          // HEM flux from saturated liquid at T into P2 [kg/m2/s] (table)
double dyerG2(double T1, double P1, double P2);   // v2.5 Dyer flux, Combustion v2 convention (inlet P1, liquid at T1)
double dyerG(double T, double Pc_abs);        // saturated inlet (P1 = Pv(T), no line loss): dyerG2(T, Pv(T), Pc)
double ceaCstar(double Pc_abs, double of);    // ideal c* [m/s]
double ceaGamma(double Pc_abs, double of);
double ceaCfVac(double Pc_abs, double of);    // at combustion.json eps
double GammaFn(double g);                     // Vandenkerckhove function
double pintleArea(double x);                  // geometric flow area at lift x [m2]

struct EngineParams {
  // MC multipliers / scenario knobs (1.0 = nominal combustion.json values)
  double Cd_scale = 1.0;            // pintle Cd (combustion: 0.70, band 0.6-0.8)
  double reg_scale = 1.0;           // regression coefficient a (combustion band x0.6-1.5)
  double tl_scale = 1.0;            // thermal-lag time multiplier
  double eta_scale = 1.0;           // c* efficiency multiplier
  double comb_delay = 0.005;        // [s] ASSUMED, combustion.json tau_d range 3-10 ms
  double alpha_fuel = 1.0e-7;       // [m2/s] combustion.json "ABS diffusivity ~1e-7 (LITERATURE-UNVERIFIED)"
  double tau_f_fixed = 0.0;         // >0 overrides the thermal-lag law with a constant (scenario)
  double T_tank0 = 293.15;          // [K] REQ ENG-12 conditioning 20 +/- 3 C
  double dp_line_ref = tab::k_dp_line_ref, mdot_ref = 0.25;   // [COMB feed_line_checks_v2.json] line loss at 0.25 kg/s (~mdot^2)
  double V_line = 19.0e-6;          // [m3] ASSUMED MV -> pintle liquid volume (3/8 in hose ~0.3 m + fittings)
  double t_mv_open = 0.05, t_mv_close = 0.10;    // [s] ASSUMED fastest valve opening (servo-limited, v2.1: 0.15 after cock) / spring close
  double theta_full_open = 40.0 * M_PI / 180;    // [ASSUMED] v2.2 opener angle at which the one-way dog has pushed the MV fully open
  double CdA_mv = 3.0 * 1.699e-5;   // [DERIVED] v2.2 Cv 3 (COMB v2 minimum via lead) -> Cd*A = Cv x 1.699e-5 m2 (water, 1 psi, 1 gpm)
  double T_gas0 = 293.15, R_gas = 287.0, gamma_gas = 1.40;   // [ASSUMED] v2.2 gas in an unprimed line: air at ambient
  double line_vent_at = -1.0;       // scenario v2.2: line vented to ambient at this time (drained, gas at 1 bar)
  double t_cock_needed = 0.20;      // [s] ASSUMED opener-servo dwell needed to cock the valve
  double tau_prime = 0.060;         // [s] unused since v2.2 (priming now from the valve area and the gas pocket)
  double tau_feed = 0.004;          // [s] ASSUMED primed-line pressure response
  double cstar_cold = 400.0;        // [m/s] ASSUMED unlit N2O cold-flow c*
  double gamma_cold = 1.27;         // ASSUMED
  double torch_delay = 0.030;       // [s] ASSUMED: torch lights this long after both solenoids open + first spark
  double ign_delay = 0.100;         // [s] COMB v2.2 speed_checks ASSUMED torch-to-main delay 0.10 s (v2.4 SIL: 0.04 s)
  double hard_start_gain = 0.0;     // scenario: fraction of unburnt ox accumulated before ignition released in 5 ms
  double flameout_at = -1.0;        // scenario: time [s] at which the flame is forced out (-1 = never)
  double mdot_extinguish = 2.0e-3;  // [kg/s] ASSUMED: below this ox flow for 50 ms the flame goes out
  double At_block_at = -1.0;        // v2.2 scenario: time [s] at which part of the throat is blocked (-1 = never)
  double At_block_frac = 0.0;       // v2.2 scenario: blocked fraction of the throat area (thrust then approximate)
  // v2.7 torch chamber pressure P_torch (the RC-01 flame-confirmation signal, M3200 on the torch body port). ESTIMATES until
  // IGN-1 measures them: lit ~3 bar abs, unlit N2O + propane cold flow ~0.15 bar above the chamber; first-order lag
  double torch_p_lit = 3.0e5;       // [Pa abs] ESTIMATE
  double torch_dp_cold = 0.15e5;    // [Pa] ESTIMATE
  double torch_tau = 0.003;         // [s] ASSUMED
  bool torch_fail = false;          // scenario: the torch never lights (igniter, valve or propane failure)
  // v2.7 C7 scenario: from vapour_fill_at the valve-to-seat volume (tab::k_V_valve_to_seat, Combustion low_inlet_check_v2p3) holds
  // N2O vapour (sat. vapour 20 C state); at the next opening it is pushed through the pintle lift (choked vapour flux) before
  // liquid reaches the seat. The vapour does not light the main here (conservative for the check timing: with a hot grain it may
  // light, but Pc stays low until the liquid arrives either way)
  double vapour_fill_at = -1.0;
  double V_vap = -1.0;              // v2.8 final scenario: vapour volume placed by vapour_fill_at [m3] (< 0: tab::k_V_valve_to_seat, COMB v2.3
                                    //   21.42 cm3; S11 sweeps it, e.g. MECH option A ~44 cm3 read from seat_leak_drain_v1.json)
  // v2.8 main valve type (LEAD 2026-10-13 MV concept change; MECH 03-cad/calcs/mv_actuator_v1, sha256 a2d8cdd3):
  // 1 = MV-P balanced poppet: constant-rise cam (lift proportional to the opener angle up to theta_full_open), curtain area proportional
  //     to lift up to d/4 (linear area law), Cv 3.64 (Cd 0.65 ASSUMED), dashpot-damped closing t_mv_close_poppet after the holding
  //     magnet releases, release delay t_latch_release (flux decay); the switches sit on the cam follower (same thresholds)
  // 0 = v2.2-v2.7 spring-return ball valve (t_mv_close 0.10 s spring close, ball overlap area law, Cv 3, no release delay): comparison
  int mv_type = 1;
  double t_mv_close_poppet = 0.030;   // [MECH mv_actuator_v1 closing_with_dashpot_s, ESTIMATE] latch release -> seated
  double t_latch_release = 0.0094;    // [DERIVED calc/mv_latch_magnet_v1: clamp decay 2.4 ms + eddy lag 7.0 ms at 8.4 V / -10 C, estimate]
  double Cv_poppet = 3.64;            // [MECH mv_actuator_v1 B_balanced_poppet_MVP.Cv, ESTIMATE]
};

class EnginePlant {
 public:
  explicit EnginePlant(const EngineParams& p);
  // dt [s]; x pintle lift [m]; mv_latch; opener_theta = MV opener servo output angle [rad] (v2.2); torch solenoids; spark
  void step(double dt, double x, bool mv_latch, double opener_theta, bool sol_n2o, bool sol_prop, bool spark);
  // lit steady state at tank temperature T for lift x with current port (map generator / checks)
  void steadyState(double T, double x, double* Pc_abs, double* mox, double* mf, double* F) const;
  double thrustOf(double Pc_abs, double of) const;

  // state / outputs (absolute pressures)
  double t = 0, Pc = 101325.0, p_feed = 101325.0, P_tank = 0, T_tank = 0, m_tank = 0, U_tank = 0;
  double mox = 0, mox_burn = 0, mf = 0, of = 0, thrust = 0, cstar = 0, Dport = 0, Vc = 0;
  double mv_frac = 0, fill = 0, cock_timer = 0;
  // v2.2 priming gas pocket (indicative: adiabatic, no wall heat transfer, no liquid inertia)
  bool gas_active = false;
  double gas_m = 0, gas_T = 293.15, gas_p = 101325.0, gas_T_max = 0, gas_p_max = 0, prime_Q = 0, dpfeed_dt_max = 0;
  bool mv_open_sw = false, mv_closed_sw = true, torch_lit = false, ignited = false, liquid_depleted = false;
  double unburnt = 0, burst_left = 0, ox_used = 0, fuel_used = 0;
  double P_torch = 101325.0;        // v2.7 torch chamber pressure [Pa abs]
  double vap_left = 0.0, mvap = 0.0;   // v2.7 C7 vapour still in the valve-to-seat volume [m3]; vapour flow through the pintle [kg/s]
  EngineParams P;
 private:
  void tankUpdate(double dt);
  std::vector<double> delay_buf_;
  size_t delay_idx_ = 0;
  double delay_dt_ = 0, delay_acc_ = 0;
  double torch_timer_ = 0, ign_timer_ = 0, low_flow_timer_ = 0, sol_timer_ = 0;
  double latch_off_t_ = 1e9;          // v2.8: time since the holding-magnet drive went off [s]
  bool vent_done_ = false, vap_done_ = false;   // v2.7: one-shot scenario events (v2.2-v2.6: a one-sub-step time window, which a
                                                //   float-accumulated t can step over when the event time is a multiple of dt)
  bool spark_seen_ = false;
};

struct ServoParams {
  // model 0: Savox SB-2292SG (DATASHEET 22/31/45 kg-cm, 0.085/0.07/0.055 s per 60 deg at 6.0/7.4/8.4 V) = TVC (+ MV opener)
  // model 1: MKS HV69 (retailer copies of MKS data, pintle_mini_servo_v1: 6.0/7.5/9.2/10.2 kg-cm, 0.17/0.13/0.11/0.10 s
  //          per 60 deg at 4.8/6.0/7.4/8.2 V; stall current NOT published -> 1.5 A at 7.4 V ASSUMED (DERIVED bound 1.2-1.7 A))
  int model = 0;
  double V = 7.4;                        // supply at the servo [V]
  double center_us = 1500.0;             // pulse at the zero output angle [us] (HV69: 1520 us, MKS)
  double deadband_us = 1.0;              // ASSUMED (0.5-3 us)
  double backlash_rad = 0.2 * M_PI / 180;// ASSUMED (0.05-0.5 deg)
  double pb_rad = 2.0 * M_PI / 180;      // ASSUMED proportional band: full drive at 2 deg error
  double zeta = 0.7;                     // ASSUMED internal loop damping target
  double J_int = 1.6e-3;                 // [DERIVED central, servo_jint_estimate_v1: 0.76-2.7e-3] output-referred rotor + gear
                                         //   inertia [kg m2] (v2.0-v2.5: 2.0e-3 ASSUMED); B-TVC-1 measures it
  double latency = 0.0010;               // ASSUMED internal processing latency [s]
  double frame = 0.003003;               // DATASHEET 333 Hz
  double quant_us = 1400.0 / 4096.0;     // DATASHEET 12-bit over 800-2200 us
  double us_per_rad = 10.0 * 180.0 / M_PI;   // DATASHEET 1000 us / 100 deg
  double fric = 0.02;                    // ASSUMED Coulomb friction at output [N m]
  double torque_scale = 1.0;             // MC multiplier on stall torque
  double speed_scale = 1.0;              // MC multiplier on no-load speed
  double tstall() const;                 // [N m] at V
  double wnl() const;                    // [rad/s] at V
  double istall() const;                 // [A] at V
  static ServoParams hv69() {            // v2.5 pintle baseline (LEAD 2026-10-12)
    ServoParams p; p.model = 1; p.V = 7.483; p.center_us = 1520.0;   // v2.6: rail v2 typ (Sim overwrites V each ms)
    p.J_int = 9.5e-4;                    // DERIVED tau_m T_s / w_nl with tau_m 10 ms ASSUMED (coreless motor), 7.4 V data
    p.deadband_us = 1.0;                 // [MKS retailer data] 1 us
    p.us_per_rad = 10.0 * 180.0 / M_PI;  // ASSUMED 10 us/deg (not published; B-PNT-1 measures travel)
    p.fric = 0.01;                       // ASSUMED (smaller gear train than the SB-2292SG)
    return p;
  }
};

class HobbyServo {
 public:
  explicit HobbyServo(const ServoParams& p, uint32_t seed = 1);
  void setPulse(double us) { us_in_ = us; }
  // T_load: external torque on the output shaft, + opposes + motion; J_load: reflected load inertia
  void step(double dt, double t, double T_load, double J_load);
  double theta = 0, omega = 0, T_motor = 0, current = 0, target = 0;
  bool powered = true;
  ServoParams P;
 private:
  double us_in_ = 1500, next_frame_ = 0, kd_ = 0;
  // latched pulses waiting for (pulse end + internal latency); a FIFO because a long pulse plus latency can
  // exceed one 3.003 ms frame (v2 fix: a single pending slot was overwritten and froze the target near 2 ms pulses)
  static constexpr int kQ = 4;
  double q_at_[kQ] = {0}, q_val_[kQ] = {0};
  int q_head_ = 0, q_n_ = 0;
  std::mt19937 rng_;
};

struct GimbalParams {               // one axis, mid pivot; load terms from gnc.json v1 (gnc_tables.h), geometry ELEC v2 proposal
  double I = gnc::k_I_pivot_kgm2;    // kg m2 about pivot [GNC, mass ledger ASSUMED until mechanical.json]
  double k_hose = gnc::k_K_hose_Nm_per_rad;          // N m/rad [GNC ASSUMED hose stiffness]
  double M_acc_per_rad = gnc::k_K_axacc_Nm_per_rad;  // N m/rad axial-acceleration term [GNC]
  double M_mis = gnc::k_M_mis_full_Nm;               // N m thrust misalignment at full thrust [GNC]
  double M_side = gnc::k_M_side_floor_Nm;            // N m constant side-load disturbance [GNC floor value, applied always = conservative]
  double M_fric = gnc::k_M_fric_Nm;                  // N m Coulomb pivot friction [GNC]
  double c_damp = 0.05;              // N m s/rad [ASSUMED]
  double r_h = 0.018, R_e = 0.105;   // m (small-angle lever ratio 5.83) [ELEC v2 proposal; v1 had 15 mm horn = ratio 7]
  double k_link = 2.0e6;             // N/m lumped pushrod/ball-link/bracket stiffness (ASSUMED)
  double c_link = 200.0;             // N s/m
  double play_m = 0.02e-3;           // m total rod-end play (ASSUMED)
  double stop_rad = 8.0 * M_PI / 180;// hard stop
  double thrust_frac = 1.0;          // scales misalignment
};

class GimbalAxis {
 public:
  GimbalAxis(const GimbalParams& g, const ServoParams& s, uint32_t seed);
  void step(double dt, double t, double us_cmd);
  double theta_e = 0, omega_e = 0, F_rod = 0;
  HobbyServo servo;
  GimbalParams G;
};

struct PintleMechParams {                    // v2.5 HV69 toggle crank-slider (LEAD 2026-10-12; pintle_mini_servo_v1)
  double r_c = 3.0e-3;                       // [m] crank radius
  double L = 28.0e-3;                        // [m] link length
  double phi_c = 15.0 * M_PI / 180;          // contact angle (needle leaves the seat)
  double phi_n = 1.037054;                   // crank angle at servo neutral (engine_params.h kCrankPhiNeutral_rad; checked in Sim)
  double eta = 0.90;                         // ASSUMED roller/crank efficiency
  double F0 = 121.69, k_spring = 5000.0;     // closing spring (pintle_linkage_v2)
  double F_seal = 25.0;                      // combustion.json ASSUMED upper bound
  double A_seat = M_PI / 4 * 5.5e-3 * 5.5e-3;// combustion.json seat 5.5 mm
  double A_stem = M_PI / 4 * 4.0e-3 * 4.0e-3;// combustion.json stem 4.0 mm
  double v_eps = 1.0e-3;                     // m/s friction smoothing
  double stroke_max = 4.2e-3;                // mechanical stop (lift) [MECH/LEAD]
  double s(double phi) const { const double rs = r_c * std::sin(phi); return r_c * std::cos(phi) + std::sqrt(L * L - rs * rs); }
  double lift(double phi) const { return phi <= phi_c ? 0.0 : s(phi_c) - s(phi); }
  double dxdphi(double phi) const {
    if (phi <= phi_c) return 0.0;
    const double rs = r_c * std::sin(phi);
    return rs * (1.0 + r_c * std::cos(phi) / std::sqrt(L * L - rs * rs));
  }
};

class PintleDrive {
 public:
  PintleDrive(const PintleMechParams& m, const ServoParams& s, uint32_t seed);
  void step(double dt, double t, double us_cmd, double p_feed_abs, double Pc_abs);
  double crank() const { return M.phi_n + servo.theta + flank_; }   // crank angle from top dead centre
  double x = 0, xdot = 0, F_net = 0, phi_stop = 0;
  bool contact_lost = false;                 // net force < 0: follower would separate (model invalid -> flagged)
  bool at_stop = false;                      // v2.5: crank against the 4.2 mm lift stop (servo stalled)
  HobbyServo servo;
  PintleMechParams M;
 private:
  double flank_ = 0;
};

struct Gimbal2Params {              // v2.6: mechanical.json v2 (mech_tables.h, gen_mech_params v2); [ASSUMED] where marked
  double I[2] = {mech::k_I_wet_kgm2[0] + mech::k_I_ring_alpha_kgm2, mech::k_I_wet_kgm2[1]};   // alpha (outer), beta: engine group
  double k_hose = mech::k_K_hose_Nm_per_rad[1];        // upper end of the radial-routing range (lower end in a case)
  double K_axacc = mech::k_K_axacc_Nm_per_rad;          // N m/rad, applied DESTABILISING
  double M_mis = mech::k_M_mis_full_Nm;                 // at 500 N, scaled by thrust_frac
  double M_side = mech::k_M_side_floor_Nm;              // constant (floor value applied always = conservative)
  double M_fric = mech::k_M_fric_bearing_Nm;            // Coulomb per axis
  double c_damp = 0.05;                                 // N m s/rad [ASSUMED] bearing viscous term
  // as-built linkage (v2.6 exact 3-D pushrods): lever eye P0, horn rotation-axis point C, horn plane direction u (horn eye
  // H = C + r_h (-cos(th) u + sin(th) z)), rod length L; mech_tables.h (C and u FITTED by gen_mech_params v2)
  double r_h = mech::k_horn_r_m, L_rod = mech::k_pushrod_m;
  double P0[2][3], C[2][3], u[2][2];
  double k_link = mech::k_k_chain_rod_N_per_m;          // N/m per rod: rod + 2 x GE 5 E + stud [DERIVED from the MECH FEA]
  double c_link = 200.0;                                // N s/m [ASSUMED]
  double play_m = 0.02e-3;                              // m ball-joint play [ASSUMED, MECH: preloaded GE joints]
  // v2.6 structure compliance per axis (lever frame between the rods and the engine): FEA structure-only stiffness
  bool flex = true;
  double K_struct[2] = {mech::k_K_struct_centre_Nm_per_rad[0], mech::k_K_struct_centre_Nm_per_rad[1]};   // [MECH FEA] centre pose
  double zeta_struct = 0.02;                            // [ASSUMED] structural damping (GNC CSI corner value)
  double I_lev = 4.0e-4;                                // kg m2 [ASSUMED] collar + levers about each axis, taken out of I
  double stop_rad = mech::k_stop_rad;                   // conical stop
  double thrust_frac = 1.0;
  double dist_dir_rad = mech::k_lever_az_rad[0] - M_PI / 2;   // disturbance direction in the (alpha, beta) plane:
                                                       // along servo A's actuation direction = worst case for A
  Gimbal2Params() {
    for (int i = 0; i < 2; ++i) {
      for (int k = 0; k < 3; ++k) { P0[i][k] = mech::k_lever_eye0_m[i][k]; C[i][k] = mech::k_shaft_c_m[i][k]; }
      u[i][0] = mech::k_horn_u[i][0]; u[i][1] = mech::k_horn_u[i][1];
    }
  }
};

class GimbalPlant2 {
 public:
  GimbalPlant2(const Gimbal2Params& g, const ServoParams& sa, const ServoParams& sb, uint32_t seed);
  void step(double dt, double t, const double us_cmd[2]);
  double dz(int i, double a, double b, double* dda, double* ddb) const;   // lever-eye vertical displacement and Jacobian
  // v2.6: lever eye position and its partial derivatives at the pose (al, be) [m, m/rad]
  void leverEye(int i, double al, double be, double P[3], double dPa[3], double dPb[3]) const;
  double rodLength(int i) const;                         // current eye-to-eye length [m]
  double a = 0, b = 0, wa = 0, wb = 0;     // engine alpha, beta [rad], rates [rad/s]
  double al = 0, bl = 0, wal = 0, wbl = 0; // v2.6 lever frame (= engine when flex is off)
  double F_rod[2] = {0, 0};                // pushrod compression [N]
  double M_ext[2] = {0, 0};                // v2.6 external moment on the engine axes [N m] (S7 mode identification)
  bool at_stop = false;
  HobbyServo servo[2];
  Gimbal2Params G;
};

// v2.6: lowest undamped rocking mode [Hz] of one axis of the linearised GimbalPlant2 at neutral: rotor (J_int, servo position-loop
// stiffness T_stall / PB to ground) - pushrods - lever frame - structure - engine, both servos (mixing at neutral). The SIL uses
// it as the "B-TVC-1 measurement" that sets the per-axis ECU notch; S7 checks it against the plant's own frequency response.
double rockingModeHz(const Gimbal2Params& g, const ServoParams& s, int axis);
// v2.6: the same linear chain WITH its damping (servo loop D term + back-EMF on the rotor, rod damping, structural damping, bearing
// viscous term), driven by the servo position command: engine angle / commanded engine angle at f [Hz] (magnitude). The SIL servo
// loop is ASSUMED critically shaped (zeta 0.7), so the rotor is heavily damped and the resonance seen from the command sits ABOVE the
// undamped eigenfrequency; B-TVC-1 measures this response. peakHz: frequency of the largest |gain| in [fmin, fmax] (1 % steps).
double rockingGain(const Gimbal2Params& g, const ServoParams& s, int axis, double f_Hz);
double rockingPeakHz(const Gimbal2Params& g, const ServoParams& s, int axis, double* gain_peak = nullptr, double fmin = 5.0, double fmax = 80.0);

struct SenseLineParams {            // all [ASSUMED] until CAD v3 routing and the transducer adapter are fixed
  double L = 0.30;                  // m  tap (head top) -> transducer (fixed side), across the gimbal [COMB v2 via lead: 0.3 m]
  double ID = 1.59e-3;              // m  1/8 in OD x 1/16 in ID PTFE
  double V_end = 0.5e-6;            // m3 transducer port + 1/8 tube -> 1/4 NPT adapter dead volume
  double T = 350.0;                 // K  gas in the line (cooled combustion products)
  double M = 0.026;                 // kg/mol products molar mass (N2O/ABS, ASSUMED; CEA value from Combustion)
  double mu = 2.2e-5;               // Pa s
  double n_poly = 1.15;             // polytropic exponent in a narrow tube (between 1 and gamma)
  int N = 16;                       // sections
  bool enabled = true;
  bool legacy_v21 = false;          // v2.6: true = the v2.1-v2.5 formulation (volumetric branch flow with a pressure-
                                    //   dependent inertance; NOT mass-conservative: a 1 -> 40 bar step gave a 1695 bar peak)
};

class SenseLine {
 public:
  explicit SenseLine(const SenseLineParams& p);
  void init(double p0);
  double step(double dt, double p_in);   // returns the pressure at the closed (transducer) end
  double c() const;                      // sound speed [m/s]
  SenseLineParams P;
 private:
  std::vector<double> p_, q_;
};

}  // namespace sil
