"""Apply run6 amendment F (parameters of the sim6 stuck-pintle fault, detectors and abort) to a run6.py file (path argument)."""
import sys

p = sys.argv[1]
s = open(p).read()


def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (old[:80], n)
    s = s.replace(old, new)


rep('"""run6 v2.8-dev (v2.8-dev amendments M (flown mass estimator mest_*, kest_comp) and W (fuel-web state web_*, burn-limit action web_act, B apex predictor on Pc bpred_pc): parameters passed to sim6, off by default;',
    '"""run6 v2.8-dev (v2.8-dev amendments M (flown mass estimator mest_*, kest_comp), W (fuel-web state web_*, burn-limit action web_act, B apex predictor on Pc bpred_pc) and F (stuck-pintle fault flt_*, in-loop detectors det_* / fct_*, abort abt_*, geofence proposal geo_dh): parameters passed to sim6, off by default;')
rep("web_act=0, bpred_pc=0, gim_notch_f=0.0,",
    "web_act=0, bpred_pc=0, flt_on=0, flt_ph=1, flt_t=0.5, flt_F=670.0, flt_rate=2500.0, flt_enc=0, flt_pcl=0, flt_persist=1, "
    "det_fct=1, det_op=1, det_pf=1, det_geo=0, fct_thr=650.0, fct_n=3, fct_tau=0.020, fct_hz=100.0, fct_ph=0.005, fct_comp=0, "
    "det_op_Pabs=3.0e6, det_op_t=0.003, det_pf_t=0.100, det_pf_err_m=0.15e-3, geo_dh=15.0, abt_lat=0.00168, abt_seat=0.0394, "
    "abt_sdto=0.30, abt_sdenc=0.08, abt_imp=38.2, gim_notch_f=0.0,")
rep("""    S("test_mode", cfg["test_mode"], "VERIFICATION")
""", """    # v2.8-dev amendment F (review RG-18): stuck-pintle fault, in-loop detectors, abort (off by default)
    S("flt_on", float(cfg["flt_on"]), "CONFIG 1 = stuck-pintle over-thrust fault flown (sim6 v2.8-dev amendment F)")
    S("flt_ph", float(cfg["flt_ph"]), "CONFIG fault onset phase: 1 boost, 2 B floor phases, 5 landing burn")
    S("flt_t", float(cfg["flt_t"]), "CONFIG/MC onset time: flight time (phases 1-2) or time after the landing-burn start (5) [s]")
    S("flt_F", float(cfg["flt_F"]), "REQ review RG-18 stuck level [N] (670 N = threshold + 20 N; 876 N Combustion full-open "
                                    "MEOP stuck-pintle case)")
    S("flt_rate", float(cfg["flt_rate"]), "ASSUMED excursion ramp [N/s] (m2_fc_thrust v1.1 synthetic ramps 2.5 / 3.6 kN/s)")
    S("flt_enc", float(cfg["flt_enc"]), "CONFIG 1 = the pintle encoder sees the jam (PINTLE_FAULT path); 0 = linkage failure "
                                        "the encoder does not see")
    S("flt_pcl", float(cfg["flt_pcl"]), "CONFIG 1 = Pc invalid (ECU over-pressure check blind)")
    S("flt_persist", float(cfg["flt_persist"]), "CONFIG 1 = the fault persists through a normal close and re-activates at "
                                                "the next start (linkage still broken)")
    S("det_fct", float(cfg["det_fct"]), "CONFIG FC_THRUST over-thrust abort active (firmware v2.8.1: also with a valid Pc)")
    S("det_op", float(cfg["det_op"]), "CONFIG ECU over-pressure abort active (firmware kPcOverPressureAbs_Pa, Pc valid)")
    S("det_pf", float(cfg["det_pf"]), "CONFIG PINTLE_FAULT stall/tracking abort active (firmware v2.6 time path)")
    S("det_geo", float(cfg["det_geo"]), "CONFIG geofence abort (GNC PROPOSAL, research; off in the baseline)")
    S("fct_thr", float(cfg["fct_thr"]), "REQ LEAD 2026-10-13 ADOPTED over-thrust threshold [N] (firmware kOverThrust_N)")
    S("fct_n", float(cfg["fct_n"]), "REQ LEAD 2026-10-13 ADOPTED consecutive frames (firmware kOverThrustFrames)")
    S("fct_tau", float(cfg["fct_tau"]), "REQ LEAD / GNC m2_fc_thrust v1.1 first-order estimate filter [s]")
    S("fct_hz", float(cfg["fct_hz"]), "REQ interface FC_THRUST frame rate [Hz] (firmware kFcThrustRate_Hz)")
    S("fct_ph", float(cfg["fct_ph"]), "MC frame phase [s] (U(0, 1 / fct_hz) per run in the fault Monte Carlo)")
    S("fct_comp", float(cfg["fct_comp"]), "DESIGN 1 = lever-arm / encoder-direction compensation in F_acc (RG-16 proposal)")
    pcm_ = np.asarray(tab["pc"], float)[:, 0]
    Fgm_ = np.asarray(tab["Fg"], float)
    if not (np.all(np.diff(pcm_) > 0) and pcm_[0] < float(cfg["det_op_Pabs"]) < pcm_[-1]):
        raise ValueError("amendment F: the map Pc(F) must be increasing and bracket the over-pressure threshold")
    S("det_op_F", float(np.interp(float(cfg["det_op_Pabs"]), pcm_, Fgm_)),
      f"DERIVED map thrust at the ECU over-pressure abort {cfg['det_op_Pabs'] / 1e5:.1f} bar abs (firmware kPcAbortAbs_Pa via "
      "engine_params.h; combustion map Pc(F), port-independent) [N, Pc-equivalent]")
    S("det_op_t", float(cfg["det_op_t"]), "DESIGN firmware kPcOverPressureTime_s persistence [s] (Pc filter lag not modelled)")
    S("det_pf_t", float(cfg["det_pf_t"]), "DESIGN firmware kPintleStallTime_s, no-progress time path [s] (LEAD approved)")
    if par[s6.P_toff_l5] > par[s6.P_toff_l1] > 0.0:
        tl_ = [par[getattr(s6, f"P_toff_l{i_}")] for i_ in range(6)]
        tf_ = [0.0] + [par[getattr(s6, f"P_toff_f{i_}")] for i_ in range(1, 6)]
        slope_ = max((tf_[i_ + 1] - tf_[i_]) / (tl_[i_ + 1] - tl_[i_]) for i_ in range(5))
        S("det_pf_dF", float(cfg["det_pf_err_m"]) * 1e3 * slope_,
          f"DERIVED firmware kPintleStallErr_m {cfg['det_pf_err_m'] * 1e3:.2f} mm x the steepest slope {slope_:.1f} N/mm of "
          "the lift-thrust table (latest trip) [N, Pc-equivalent]")
    else:
        S("det_pf_dF", 60.0, "ASSUMED tracking band in thrust when the lift table is not loaded [N]")
    S("geo_dh", float(cfg["geo_dh"]), "PROPOSAL GNC geofence margin above h_target [m] (research, RG-18)")
    S("abt_lat", float(cfg["abt_lat"]), "DERIVED Electronics over_thrust_v3.json (770bf284d14b1336): CAN <= 0.48 ms incl. the "
                                        "ABORT frame + ECU <= 1.2 ms [s]")
    S("abt_seat", float(cfg["abt_seat"]), "ESTIMATE Electronics over_thrust_v3: latch release 9.4 ms + MV-P close 30 ms "
                                          "(ESTIMATE; B-MV-1 bound 0.10 s close) [s]")
    S("abt_sdto", float(cfg["abt_sdto"]), "DESIGN firmware kMvSeatTimeout_s (COMB v2.4 / LEAD 2026-10-13) [s]")
    S("abt_sdenc", float(cfg["abt_sdenc"]), "ASSUMED normal pintle closing from <= 75 % in 0.059-0.083 s (ENG-05, MECH "
                                            "pintle_dynamics_v2) + 5 x 1 ms seat confirmation [s]")
    S("abt_imp", float(cfg["abt_imp"]), "SIM Combustion v2.4 tail-off 37.5-38.2 N s after the MV closes (upper value) [N s]")
    S("test_mode", cfg["test_mode"], "VERIFICATION")
""")
open(p, "w").write(s)
print("patched", p)
