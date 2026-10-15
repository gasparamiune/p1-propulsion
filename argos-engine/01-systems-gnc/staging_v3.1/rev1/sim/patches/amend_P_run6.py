"""Apply run6 amendment P (parameters of the sim6 A-relight forced purge and stuck-open bleed fault) to a run6.py file (path
argument). Requires amendments M, W and F already applied. v1.1 (GNC, 2026-10-13): prg_prio, blf_fmax."""
import sys

p = sys.argv[1]
s = open(p).read()


def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (old[:80], n)
    s = s.replace(old, new)


rep("abort abt_*, geofence proposal geo_dh): parameters passed to sim6, off by default;",
    "abort abt_*, geofence proposal geo_dh) and P (A-relight forced purge prg_*, stuck-open bleed fault blf_*, bleed jet "
    "bl_vj / bl_az): parameters passed to sim6, off by default;")
rep("abt_sdto=0.30, abt_sdenc=0.08, abt_imp=38.2, gim_notch_f=0.0,",
    "abt_sdto=0.30, abt_sdenc=0.08, abt_imp=38.2, prg_on=0, prg_T=2.5, prg_lead=0.5, prg_mdot=0.0200, prg_mdot_hat=None, "
    "prg_book=1, prg_jet=1, prg_prio=1, blf_on=0, blf_ph=4, blf_mdot=0.0194, blf_mode=0, blf_n=0.5, blf_fmax=0.14, bl_vj=105.8, "
    "bl_az=0.0, "
    "gim_notch_f=0.0,")
rep("""    S("test_mode", cfg["test_mode"], "VERIFICATION")
""", """    # v2.8-dev amendment P (coordinator relay 2026-10-13, RG-01 re-fly model): A-relight forced purge and stuck-open bleed
    S("prg_on", float(cfg["prg_on"]), "CONFIG 1 = forced purge before the A relight lift (sim6 v2.8-dev amendment P)")
    S("prg_T", float(cfg["prg_T"]), "DESIGN LEAD relay 2026-10-13: bleed open 2-3 s ending at the lift [s] (Combustion "
                                    "purge_sizing_v2p4 P_abort 0 needs 1.0-2.0 s)")
    S("prg_lead", float(cfg["prg_lead"]), "PROPOSAL GNC extra anticipation of the purge-start trigger [s]")
    S("prg_mdot", float(cfg["prg_mdot"]), "DERIVED Combustion purge_sizing_v2p4 (workdir, hub pending): liquid through the "
                                          "bleed 11.25 g/s (0.6 mm) / 20.0 g/s (0.8 mm) at the coast state, Cd 0.70 ASSUMED; "
                                          "the whole purge taken as liquid (upper bound) [kg/s]")
    pmh_ = cfg["prg_mdot_hat"] if cfg["prg_mdot_hat"] is not None else cfg["prg_mdot"]
    S("prg_mdot_hat", float(pmh_), "DESIGN flight-software purge flow booked into m_hat [kg/s] (nominal = truth unless set; "
                                   "CF-4 cold flow calibrates it)")
    S("prg_book", float(cfg["prg_book"]), "DESIGN 1 = the flight software books the commanded purge into m_hat")
    S("prg_jet", float(cfg["prg_jet"]), "CONFIG 1 = the purge jet acts as a radial force (vent direction TO-DEFINE)")
    S("prg_prio", float(cfg["prg_prio"]), "PROPOSAL GNC 1 = the lift keeps the plain relight trigger and a late purge is "
                                          "truncated; 0 = the lift waits for prg_T (a 2 s wait at the drogue descent rate "
                                          "crashes: test_P smoke run)")
    S("blf_on", float(cfg["blf_on"]), "CONFIG 1 = stuck-open head-end bleed fault flown (amendment P)")
    S("blf_ph", float(cfg["blf_ph"]), "CONFIG bleed fault onset: 0 = first ignition, 4 = the A relight lift (fails to close)")
    S("blf_mdot", float(cfg["blf_mdot"]), "DERIVED coordinator relay of Combustion 2026-10-13: stuck-open bleed during a burn "
                                          "6.3-19.4 g/s (3-8 % of the engine flow at 0.6 mm, up to 14 % at 0.8 mm) [kg/s]")
    S("blf_mode", float(cfg["blf_mode"]), "CONFIG 0 = additive bracket (engine flow kept, tank loses more); 1 = subtractive "
                                          "bracket (bleed taken from the injector flow, thrust drops)")
    S("blf_n", float(cfg["blf_n"]), "ASSUMED fuel-flow exponent on the oxidiser flux for the subtractive bracket")
    S("blf_fmax", float(cfg["blf_fmax"]), "DERIVED coordinator relay: bleed share of the engine flow up to 14 % (0.8 mm); cap of "
                                          "the subtractive bracket")
    S("bl_vj", float(cfg["bl_vj"]), "DERIVED Combustion purge_sizing_v2p4 jet thrust / liquid flow = 1.190 N / 11.25 g/s = "
                                    "2.116 N / 20.0 g/s = 105.8 m/s; 0 = balanced or axial vent [m/s]")
    S("bl_az", float(cfg["bl_az"]), "ASSUMED radial vent azimuth in the body frame [rad] (T4 port cross-drilling; direction "
                                    "TO-DEFINE by Mechanical)")
    S("test_mode", cfg["test_mode"], "VERIFICATION")
""")
open(p, "w").write(s)
print("amendment P applied to", p)
