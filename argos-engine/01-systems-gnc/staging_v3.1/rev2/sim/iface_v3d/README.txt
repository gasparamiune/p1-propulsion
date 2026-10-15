iface_v3d (GNC rev2, 2026-10-13): pinned GNC_IFACE for the RG-01 re-fly.
combustion.json   = hub interfaces/combustion.json v2.4 (469727032124329f), copied 2026-10-13 (coordinator: Combustion v2.4 published).
mechanical.json   = hub v2 (4f024ed4ccb4618c, identical to iface_v3c).
ENGINE-BASELINE   = hub v0 (508faa652ccbd539, identical).
electronics.json  = v1 pin (42fe12e15baa6e3e) from iface_v3c, NOT the hub v2 (da067408c1594814): run6.build needs
                    dynamics_for_GNC, absent in v2 (KeyError) -> REV-GNC-2 N5 dependency on the electronics v1 TVC dynamics.
throttle_map_v2.csv, actuator_rate_check_v2.json = iface_v3c pins.
