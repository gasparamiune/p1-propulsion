"""Write interfaces/combustion.json v1 from m1_design results (Combustion, 2026-10-11).
Usage: python write_interface_v1.py <results_json> <out_json> <shared_02_dir>
All file paths in the JSON point at the shared folder copies (02-combustion/data/...)."""
import json, math, sys, os, datetime

res_fn, out_fn, shared = sys.argv[1], sys.argv[2], sys.argv[3]
R = json.load(open(res_fn))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m1_design as M
V, INP = M.V, M.INP
noz = R['noz']; st = R['stations']
D = lambda f: os.path.join(shared, 'data', os.path.basename(f))


def T(v, tag, **kw):
    d = {'v': v, 'tag': tag}
    d.update(kw)
    return d


def inp(k, scale=1.0, nd=6):
    return T(round(V[k] * scale, nd), INP[k][1])


opm = {(round(o['T_tank'], 2), o['frac']): o for o in R['opmap'] if 'F' in o}
def op(fr, Tt=293.15):
    return opm[(Tt, fr)]
mx, h50, f20, f125 = op(1.0), op(0.5), op(0.2), op(0.125)
mt = R['maxrun']
SIM = 'SIM m1_design.py v1 (lumped 0D: equilibrium tank, Dyer injector, lumped helical port, CEA ABS_TYP_v1)'

liner_ID = R['liner_ID']
x_ig = 0.015
J = {
    "id": "combustion", "version": "v1", "date": "2026-10-11", "owner": "combustion",
    "status": "FIRST PASS (M1). Lumped models, ASSUMED regression law and efficiencies. Geometry is stable to ~+/-10 % "
              "(grain length is the most uncertain dimension: depends on the unverified N2O/ABS helical-port regression law). "
              "v2 will follow with the quasi-1D port model, non-equilibrium tank, gnc.json duty cycles.",
    "units": "SI (m, kg, s, N, Pa, K, J, W) unless the key says otherwise",
    "conventions": "x_face = axial distance from the injector face toward the nozzle exit [m]. CAD +Z points forward "
                   "(nozzle -> injector), so z_CAD = x_exit_face - x_face. Contour CSV radii are gas-side wall radii.",
    "inputs_read": {"ENGINE-BASELINE-v0.json": "v0", "REQUIREMENTS.md": "rev 1 (ENG-02 pintle baseline, 12.5 % stretch)",
                    "gnc.json": "absent at v1 (duty cycles ASSUMED)", "mechanical.json": "absent at v1",
                    "electronics.json": "absent at v1"},
    "decisions": {
        "throttle_architecture": T("Servo-driven variable-area pintle (needle-in-seat) injector at the head end + separate "
                                   "normally-closed main isolation valve upstream (tank side, off-gimbal)",
                                   "LEAD decision 2026-10-11 (REQUIREMENTS rev 1); trade study in 02-combustion/REPORT.md confirms (no showstopper)"),
        "expansion_ratio": T(V['eps'], INP['eps'][1] + "; eps=3 (v0) separates (Schmucker) already at 20 % thrust; eps=2 stays attached to ~14 %, incipient lip separation at 12.5 % (eps_sep 1.89); Isp cost at max -3.5 % vs eps=3"),
        "design_OF_at_max_thrust": T(round(mx['OF'], 2), INP['OF_design'][1] + "; lumped model value at initial port"),
        "fuel": T("ABS (printed, 100 % infill); PETG backup", "REQ founder/LEAD; ABS card verified: c* within +/-0.3 % across literature compositions and hf sources (cea_cards.py)"),
        "igniter": T("Spark-ignited N2O/propane torch (N2O tapped from the injector manifold), radial into the pre-chamber",
                     "DERIVED first-pass choice (trade in progress: arc-ABS needs O2/Nytrox assist with N2O; pyro cartridges limited starts); may change in v2 with a CHANGELOG line"),
        "tank_pressurisation": T("Self-pressurised N2O, conditioned 20 +/- 3 C (N2 supercharge trade pending in v2)", "REQ ENG-12 / LEAD v0"),
    },
    "gas_path": {
        "case": {"material": T("6061-T6 tube", "LEAD v0 placeholder; Mechanical owns"),
                 "OD_m": inp('case_OD'), "wall_m": inp('case_wall')},
        "liner": {"material": T("paper- or glass-phenolic tube (Mechanical selects)", "DERIVED recommendation"),
                  "thickness_m": inp('liner_t'), "ID_m": T(round(liner_ID, 5), "DERIVED = case ID - 2 x liner")},
        "chamber_inner_diameter_m": T(round(liner_ID, 5), "DERIVED (liner ID); pre- and post-chamber gas-side diameter = grain OD + 0.4 mm = %.4f m" % (2 * R['Rc'])),
        "grain": {
            "material": T("ABS, FDM printed, 100 % infill, concentric/helical perimeters", "REQ"),
            "outer_diameter_m": inp('D_grain'),
            "length_m": inp('L_grain'),
            "port": {"type": T("single helical port (round section), helix along the axis", "DERIVED"),
                     "initial_diameter_m": inp('D_port0'),
                     "helix_centreline_radius_m": inp('helix_offset'),
                     "helix_pitch_m": inp('helix_pitch'),
                     "port_envelope_diameter_m": T(round(V['D_port0'] + 2 * V['helix_offset'], 4), "DERIVED"),
                     "min_initial_web_m": T(round((V['D_grain'] - V['D_port0'] - 2 * V['helix_offset']) / 2, 5), "DERIVED")},
            "density_kg_m3": inp('rho_fuel'),
            "mass_kg": T(round(R['grain_mass'], 3), "DERIVED (geometry x density, straight-port volume)"),
            "regression_law": {"form": "r = helix_factor * a * G_ox^n  (r m/s, G_ox kg/m2/s)",
                               "a": inp('reg_a', nd=9), "n": inp('reg_n'), "helix_factor": inp('helix_factor'),
                               "note": "No verified N2O/ABS law found in accessible literature; design is checked across a x0.6..x1.5, n 0.35-0.68, helix 1.0-2.5. First static fires must measure it."},
            "x_face_start_m": T(R['x_grain0'], "DERIVED"), "x_face_end_m": T(R['x_grain1'], "DERIVED"),
            "retention": "forward face seats on the pre-chamber insulator shoulder; aft face on post-chamber insulator; anti-rotation key (Mechanical)",
        },
        "pre_chamber": {"length_m": inp('L_pre'), "diameter_m": T(round(2 * R['Rc'], 5), "DERIVED"),
                        "wall": "phenolic insulator; injector face is the forward wall"},
        "post_chamber": {"length_m": inp('L_post'), "diameter_m": T(round(2 * R['Rc'], 5), "DERIVED"),
                         "wall": "phenolic insulator, graphite or phenolic convergent entry"},
        "injector": {
            "type": T("variable-area pintle: conical needle (metering cone) moving axially in a sharp-edged seat; flow exits as an annular sheet into the pre-chamber",
                      "LEAD decision + DERIVED geometry"),
            "seat_diameter_m": inp('pintle_seat_D'),
            "needle_metering_cone_half_angle_deg": inp('pintle_cone_half'),
            "stroke_m": T(V['pintle_stroke'], INP['pintle_stroke'][1]),
            "lift_range_used_m": T([round(f125['h'], 6), round(max(r['h'] for r in mt), 6)],
                                   SIM + ": 12.5 % thrust at 20 C tank to max thrust at end of max-thrust run (cold tank)"),
            "stem_diameter_through_seal_m": inp('pintle_stem_D'),
            "Cd": inp('pintle_Cd'),
            "flow_area_vs_lift_csv": D(R['fn_pin']),
            "spray_deflection": "downstream of the seat a 35-40 deg half-angle conical injector-face diffuser (or flared needle tip) spreads the sheet; DERIVED, to cold-flow test",
            "manifold_volume_m3": T(3.0e-6, "DERIVED target (annular cavity around needle upstream of seat) - keep <= 5 cm3 to limit dribble/restart vapour"),
            "plate_thickness_m": T(0.012, "DERIVED first estimate at the seat region (Mechanical sizes for MEOP 7 MPa upstream / Pc downstream)"),
            "inlet": "3/8 in tube class, >= 8 mm ID from the flex hose (line velocity <= 5 m/s at max flow)",
            "filter": "sintered 40 um or finer upstream of the pintle (seat gap at the floor ~0.05 mm)",
            "materials": "316L or 17-4PH body and needle; PTFE spring-energised stem seal; FKM static O-rings; Krytox only",
            "flow_model": "Dyer et al. AIAA 2007-5702 (SPI/HEM blend); HEM-critical (choked) whenever Pc/P1 < ~0.72 (saturated N2O at 20 C)",
        },
        "nozzle": {
            "throat_diameter_m": T(round(noz['Dt'], 6), "DERIVED: F=500 N SL at Pc 25 bar, O/F 7, eps 2, eta_c* 0.92, eta_cf 0.975"),
            "exit_diameter_m": T(round(noz['De'], 6), "DERIVED"),
            "expansion_ratio": T(V['eps'], INP['eps'][1]),
            "throat_area_m2": T(noz['At'], "DERIVED"),
            "contour_csv": D(R['contour']),
            "convergent_half_angle_deg": inp('conv_half_angle'),
            "throat_upstream_radius_of_curvature_m": T(round(V['Rtu_over_Rt'] * noz['Dt'] / 2, 6), INP['Rtu_over_Rt'][1]),
            "throat_downstream_radius_of_curvature_m": T(round(V['Rtd_over_Rt'] * noz['Dt'] / 2, 6), INP['Rtd_over_Rt'][1]),
            "divergent_half_angle_deg": inp('div_half_angle'),
            "divergence_loss_factor_lambda": T(round((1 + math.cos(math.radians(V['div_half_angle']))) / 2, 4), "LITERATURE: lambda=(1+cos a)/2 conical nozzle"),
            "convergent_length_m": T(round(st['L_conv'], 5), "DERIVED"), "divergent_length_m": T(round(st['L_div'], 5), "DERIVED"),
            "x_face_throat_m": T(round(st['x_throat_face'], 5), "DERIVED"), "x_face_exit_m": T(round(st['x_exit_face'], 5), "DERIVED"),
            "pe_over_pa_at_max": T(round(noz['pe_pa'], 3), "CEA"),
        },
        "graphite_throat_insert_envelope": {
            "material": T("isomolded fine-grain graphite (grade per REPORT v2; e.g. SGL R6510 / Toyo IG-110 / Mersen 2020 class)", "DERIVED recommendation, allowables to be cited by Mechanical"),
            "outer_diameter_m": T(0.044, "DERIVED first estimate (>= 6 mm wall at the convergent inlet radius 16 mm)"),
            "length_m": T(0.032, "DERIVED: from convergent radius 16 mm to exit plane, +3 mm margin"),
            "gas_side_from_radius_m": T(0.016, "DERIVED: graphite starts where convergent r = 16 mm; upstream convergent in phenolic"),
            "erosion_allowance": "throat erosion estimate and life limit in REPORT v2 (literature-based); design for >= 2 flights (ENG-06)",
        },
        "pc_tap": {"location": T("radial, pre-chamber wall at x_face = 0.015 m, 180 deg from igniter port", "DERIVED"),
                   "port": "1/4-18 NPT female boss (matches electronics.json v1 TE M3234 Pc transducer) feeding a 1/8 in OD SS standoff tube >= 150 mm",
                   "range_Pa": T(3.447e6, "electronics.json v1 0-34.5 bar transducer accepted: covers MEOP 3.1 MPa")},
        "feed_pressure_tap": {"location": T("injector manifold, upstream of the pintle seat (gimballed side)", "DERIVED; matches electronics.json v1 P_feed"),
                              "port": "1/4-18 NPT female boss", "purpose": "injector dP for Cd tracking, feed-forward and chug monitoring"},
        "igniter_port": {"location": T("radial, pre-chamber wall at x_face = %.3f m" % x_ig, "DERIVED"),
                         "port": "M10x1 or 1/4 BSPP boss; torch exit bore 3 mm",
                         "torch_envelope_outside_chamber_m": T([0.020, 0.070], "DERIVED first estimate: diameter, length (body + spark plug), plus two solenoid valves ~0.020 x 0.045 each mounted on the engine"),
                         "propane_supply": "small refillable propane cartridge (~20-50 g) off-gimbal with a 1/8 in flexible line, or on-engine micro-cylinder (Mechanical choice)"},
        "overall": {"gas_path_length_injector_face_to_exit_m": T(round(st['x_exit_face'], 4), "DERIVED"),
                    "free_chamber_volume_initial_m3": T(round(R['Vc'], 7), "DERIVED"),
                    "L_star_initial_m": T(round(R['Lstar'], 3), "DERIVED"),
                    "injector_body_forward_of_face_m": T(0.025, "DERIVED estimate (manifold + seal stack); pintle actuator envelope extra (Electronics/Mechanical)")},
    },
    "operating_points": {
        "max_thrust": {"F_N": T(round(mx['F'], 1), SIM), "Pc_Pa": T(round(mx['Pc'], 0), "REQ/LEAD v0 25 bar"),
                       "mdot_total_kg_s": T(round(mx['mox'] + mx['mf'], 4), SIM), "mdot_ox_kg_s": T(round(mx['mox'], 4), SIM),
                       "mdot_fuel_kg_s": T(round(mx['mf'], 4), SIM), "OF": T(round(mx['OF'], 2), SIM),
                       "Isp_SL_s": T(round(mx['Isp'], 1), SIM), "cstar_delivered_m_s": T(round(noz['cstar_del'], 1), "CEA x eta_c* 0.92"),
                       "G_ox_initial_kg_m2s": T(round(mx['G'], 0), SIM), "dP_inj_over_Pc_20C": T(round(mx['dP_over_Pc'], 2), SIM),
                       "pintle_lift_m": T(round(mx['h'], 6), SIM)},
        "chamber_MEOP_Pa": T(3.1e6, "LEAD v0 (1.25 x Pc max); start-transient overshoot check in v2"),
        "throttle_points_20C_initial_port": [
            {"fraction": o['frac'], "F_N": round(o['F'], 1), "Pc_Pa": round(o['Pc'], 0), "mdot_ox_kg_s": round(o['mox'], 5),
             "OF": round(o['OF'], 2), "Isp_SL_s": round(o['Isp'], 1), "G_ox_kg_m2s": round(o['G'], 0),
             "dP_inj_over_Pc": round(o['dP_over_Pc'], 2), "pintle_lift_m": round(o['h'], 6),
             "nozzle_separation_area_ratio": (round(o['sep'], 3) if o['sep'] else None)}
            for o in [op(f) for f in [1.0, 0.75, 0.5, 0.25, 0.2, 0.125]]],
        "throttle_map_csv": D(R['fn_map']),
        "floor_requirement_25pct": {"F_N": T(round(op(0.25)['F'], 1), SIM), "Pc_Pa": T(round(op(0.25)['Pc'], 0), SIM)},
        "floor_target_20pct": {"F_N": T(round(f20['F'], 1), SIM), "Pc_Pa": T(round(f20['Pc'], 0), SIM), "OF": T(round(f20['OF'], 2), SIM)},
        "floor_stretch_12p5pct": {"F_N": T(round(f125['F'], 1), SIM), "Pc_Pa": T(round(f125['Pc'], 0), SIM), "OF": T(round(f125['OF'], 2), SIM),
                                  "status": "feed stiffness OK (dP/Pc ~7-10); nozzle lip separation incipient (eps_sep 1.89 vs 2.0); hybrid low-flux combustion (G_ox 74 -> ~30 kg/m2/s as port grows) is the main unverified risk - see REPORT stability section"},
        "tank_pressure_range_Pa": T([3.0e6, 5.65e6], "DERIVED: initial 4.78-5.40 MPa for 20 +/- 3 C conditioning (CoolProp Psat), up to 5.65 MPa at 25 C; equilibrium adiabatic blowdown to liquid depletion ends near 3.0-3.3 MPa (max-thrust run: %.2f MPa)" % (mt[-1]['P_tank']/1e6)),
        "tank_MEOP_Pa": T(7.0e6, "LEAD v0"),
        "thrust_ceiling_rule": T("Pc_max(t) = P_injector_inlet(t) / 1.25 (injector dP/Pc >= 0.25)", INP['dp_over_pc_min'][1]),
        "chamber_fill_time_constant_s": T(round(R['tau_fill'], 5), "DERIVED tau = L*/(c* Gamma^2)"),
    },
    "valves_and_actuators": {
        "architecture": "tank -> NC main isolation valve (off-gimbal) -> PTFE-lined braided flex hose across gimbal -> 40 um filter -> pintle injector (on gimbal)",
        "pintle_actuator_requirements": {
            "stroke_m": T(V['pintle_stroke'], "DERIVED (usable 0.2-4.0 mm)"),
            "force_pressure_envelope_N": T([round(R['F_pintle']['open_MEOP'], 1), round(R['F_pintle']['closed_MEOP'], 1)],
                                           "DERIVED: + = toward chamber (closing). Seated at MEOP: pressure holds needle closed with +77 N; wide open at MEOP: -87 N (stem area x P). Reference geometry seat 5.5 / stem 4.0 mm"),
            "seal_friction_N": T(25.0, "ASSUMED upper bound, PTFE spring-energised seal on 4 mm stem at 7 MPa (vendor data to confirm)"),
            "design_force_N": T(115.0, "DERIVED: max |pressure| + friction"),
            "actuator_rated_force_N": T(170.0, "DERIVED: 1.5 x design force"),
            "full_stroke_time_s": T(0.08, "DERIVED from ENG-03 (10-90 % thrust <= 100 ms target with ~3 ms chamber fill + fuel lag)"),
            "speed_at_rated_load_m_s": T(0.05, "DERIVED"),
            "position_resolution_m": T(1.0e-5, "DERIVED: <= 2 % thrust resolution needs <= 0.05 mm; 10 um gives margin at the floor"),
            "backlash_max_m": T(1.0e-5, "DERIVED"),
            "small_signal_bandwidth_Hz": T(8.0, "ASSUMED (match ENG-07 class until gnc.json sets the Pc-loop bandwidth)"),
            "fail_state": "spring-to-close preferred (not safety-critical: the NC isolation valve is the safety barrier)",
            "example_implementation": "hobby/industrial servo (>= 0.7 N m) on a 3.8 mm crank: 60 deg = 4 mm; F = T/r -> 0.65 N m for 170 N (Electronics selects)",
        },
        "isolation_valve_requirements": {
            "type": "normally-closed, fail-closed (spring return or NC solenoid), full port", "bore_min_m": T(0.008, "DERIVED"),
            "Cv_min": T(1.5, "DERIVED: <= 0.5 bar at 0.25 kg/s liquid N2O (rho ~800)"), "MEOP_Pa": T(7.0e6, "LEAD"),
            "close_time_max_s": T(0.15, "DERIVED: thrust shutoff is done by the pintle (<= 50 ms); isolation follows"),
            "materials": "PTFE/PCTFE seats, FKM, oxygen-cleaned, Krytox only",
            "trapped_liquid": "segment between isolation valve and closed pintle must be relieved (vented-ball cavity relief to the tank side, or a thermal relief valve <= 7.5 MPa)",
        },
        "plant_model_valve_to_Pc": {
            "form": "Pc(s)/h(s) = K_h * [(1 - phi) + phi/(tau_f s + 1)] * exp(-tau_d s) / (tau_c s + 1)",
            "K_h_Pa_per_m": T({"floor_12p5_to_25pct": round((op(0.25)['Pc'] - op(0.125)['Pc']) / (op(0.25)['h'] - op(0.125)['h']), -4),
                               "mid_50_to_75pct": round((op(0.75)['Pc'] - op(0.5)['Pc']) / (op(0.75)['h'] - op(0.5)['h']), -4),
                               "max_75_to_100pct": round((op(1.0)['Pc'] - op(0.75)['Pc']) / (op(1.0)['h'] - op(0.75)['h']), -4)},
                              SIM + " secant slopes of the 20 C throttle map (initial port)"),
            "tau_c_s": T(round(R['tau_fill'], 5), "DERIVED chamber filling"),
            "phi": T(0.10, "DERIVED: fraction of the static gain carried by the fuel flow ~ (1-n)/(1+O/F) .. 1/(1+O/F)"),
            "tau_f_s": T([0.1, 0.5], "DERIVED: solid-phase thermal lag kappa_s/r^2 with ABS diffusivity ~1e-7 m2/s (LITERATURE-UNVERIFIED) and r 1.0-0.45 mm/s"),
            "tau_d_s": T([0.003, 0.010], "ASSUMED injection/vaporisation + boundary-layer transport delay"),
            "tank_pressure_sensitivity": "K_h scales ~ with sqrt(P1 - Pc) (SPI part) to G_crit(P1) (HEM part): feed-forward on measured tank/injector-inlet pressure",
        },
    },
    "igniter_electrical": {
        "type": "spark-ignited N2O/propane torch",
        "ecu_channel_mapping": "electronics.json v1: IGN_HV in inductive coil-drive mode (12 V, <= 3 A) for the spark; SOL1/SOL2 for the torch N2O and propane NC solenoids",
        "spark": {"supply_V": T(12.0, "DERIVED"), "peak_current_A": T(4.0, "ASSUMED coil-driver class"),
                  "spark_energy_J": T(0.05, "ASSUMED per spark (>> N2O/propane minimum ignition energy)"),
                  "spark_rate_Hz": T(50.0, "DERIVED"), "spark_train_duration_s": T(0.5, "DERIVED")},
        "solenoids": {"count": 2, "supply_V": T(12.0, "DERIVED"), "current_each_A": T(0.8, "ASSUMED (small NC direct-acting, PTFE/FKM seals)"),
                      "on_time_per_start_s": T(0.6, "DERIVED")},
        "energy_per_start_J": T(15.0, "DERIVED: 2 x 12 V x 0.8 A x 0.6 s + spark ~1-2 J"),
        "timing_per_start_s": {"torch_solenoids_open": 0.0, "spark_train_start": 0.02, "torch_flame_confirmed_by": 0.10,
                               "pintle_to_ignition_lift": 0.12, "main_Pc_90pct_expected": 0.30, "torch_off": 0.60,
                               "tag": "DERIVED target sequence; ENG-04 <= 0.5 s (target 0.3 s); verify by static fire"},
        "starts_per_flight": T(">= 3 (limited only by propane/N2O; propane ~0.2 g per start)", "DERIVED"),
    },
    "thermal_and_loads": {
        "thermal_bc_csv": {"max_thrust": D(R['thermal']['max']['file']), "throttle_50pct": D(R['thermal']['50pct']['file']),
                           "floor_12p5pct": D(R['thermal']['floor12p5']['file'])},
        "peak_convective_heat_flux_W_m2": T(round(R['thermal']['max']['peak']['q_conv_Tw600_W_m2'], -4), "SIM Bartz at throat, cold wall 600 K, max thrust"),
        "peak_h_g_W_m2K": T(round(R['thermal']['max']['peak']['h_g_Tw600_W_m2K'], 0), "SIM Bartz at throat"),
        "T_aw_throat_K": T(round(R['thermal']['max']['peak']['T_aw_K'], 0), "SIM"),
        "max_thrust_case_csv": D(R['fn_mt']),
        "max_thrust_case_summary": {"burn_to_liquid_depletion_s": T(round(R['t_burn'], 2), SIM),
                                    "total_impulse_Ns": T(round(R['impulse'], 0), SIM),
                                    "fuel_burnt_kg": T(round(R['m_fuel_burn'], 3), SIM),
                                    "port_diameter_end_m": T(round(mt[-1]['D_port'], 4), SIM)},
        "duty_assumptions": T("Until gnc.json exists: (A) bounding case = max thrust held to liquid depletion (~6.05 s) for FEA thermal; "
                              "(B) provisional flight duty = 3.5 s at 100 % (ascent) / 8-10 s coast / relight / 6-8 s at 25-60 % (landing) / soak-back >= 300 s. "
                              "Grain web protects the case in the grain zone; pre/post-chamber and nozzle get the CSV BCs.", "ASSUMED"),
        "grain_mass_kg": T(round(R['grain_mass'], 3), "DERIVED"),
        "thrust_misalignment_note": "Helical port is axisymmetric on average; asymmetric regression may produce small side forces - not quantified in v1",
    },
    "unknowns_and_open_items": [
        "N2O/ABS (and PETG) regression law: no verified literature law; static-fire characterisation required (band used: a x0.6-1.5, n 0.35-0.68, helix 1.0-2.5).",
        "Pintle Cd and two-phase flow at small lifts: water then N2O cold flow (REPORT test plan).",
        "Low-flux (G_ox < ~50 kg/m2/s) combustion at the 12.5 % stretch floor: efficiency and stability unverified.",
        "Duty cycles from gnc.json not yet available.",
        "Tank geometry/load from Mechanical/GNC (v0 placeholders 2.5 L / 1.6 kg used).",
        "Igniter choice is first-pass (torch); trade completes in REPORT v2.",
    ],
    "files": {"source": os.path.join(shared, 'src'), "data": os.path.join(shared, 'data')},
}
json.dump(J, open(out_fn, 'w'), indent=1)
print('wrote', out_fn)
