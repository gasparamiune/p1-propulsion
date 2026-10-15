*Spark-ignited N2O/propane torch sizing (data/v2/ignition_v2.json torch.sizing; DERIVED/CEA)*

| torch sizing item | value |
|---|---|
| Pc_torch_bar | 3.000 |
| OF | 5.500 |
| throat_d_m | 0.002000 |
| cstar_m_s | 1586.483 |
| Tc_K | 2852.410 |
| mdot_total_kg_s | 0.000594 |
| mdot_propane_kg_s | 0.000091 |
| mdot_n2o_kg_s | 0.000503 |
| enthalpy_flux_W | 3032.607 |
| per_start_0p6s_propane_g | 0.055 |
| per_start_0p6s_n2o_g | 0.302 |
| n2o_orifice | [{'T_C': 10.0, 'G_dyer': 52093.60862608043, 'd_orifice_mm': 0.1374828874791189}, {'T_C': 20.0, 'G_dyer': 57451.47716898496, 'd_orifice_mm': 0.1309152581605437}, {'T_C': 25.0, 'G_dyer': 59727.56779964869, 'd_orifice_mm': 0.1283965786301386}] |
| propane | [{'T_C': 0.0, 'Psat_bar': 4.744575428060169, 'choked': False, 'G': 1316.8481271788316, 'mdot_through_0p30mm_gps': 0.07446600724029291}, {'T_C': 10.0, 'Psat_bar': 6.366015641814749, 'choked': True, 'G': 1748.327503987894, 'mdot_through_0p30mm_gps': 0.09886559116675224}, {'T_C': 20.0, 'Psat_bar': 8.364609050465276, 'choked': True, 'G': 2257.6887535538576, 'mdot_through_0p30mm_gps': 0.1276692912406277}, {'T_C': 25.0, 'Psat_bar': 9.52074523342492, 'choked': True, 'G': 2548.1025854311315, 'mdot_through_0p30mm_gps': 0.1440918065337048}] |
| propane_orifice_d_mm_at_20C | 0.254 |
| note | Cd 0.65 (N2O sharp orifice) and 0.80 (propane) ASSUMED; torch Pc 3 bar abs keeps the torch outlet choked into the cold chamber (~1 bar) and stays below the propane vapour pressure down to ~0 C (4.7 bar); calibrate both orifices by cold flow (weighing) before hot torch tests |
