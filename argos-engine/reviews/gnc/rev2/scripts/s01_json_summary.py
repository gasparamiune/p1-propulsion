import json,sys
p=sys.argv[1]
d=json.load(open(p))
print("keys:",list(d.keys()))
print("version",d.get("version"),"sim",d.get("sim"))
print("sources",json.dumps(d.get("sources"),indent=0)[:800])
print("states:")
for k,v in d["states"].items(): print(" ",k,v["key"],"Pab",v["P_abort"],"maxgl",v["E0_E2_given_light_max_s"],"all",v["E0_E2_all"])
print("plan_check",json.dumps(d["plan_check"]))
print("continuity",json.dumps(d["continuity"])[:1500])
print("n cases",len(d["cases"]))
for k,e in d["cases"].items():
    ps=e.get("purge_sequence") or {}
    print(f"{k:32s} P {e['P']:.3f} W[{e['P_wilson'][0]:.3f},{e['P_wilson'][1]:.3f}] ex {e['exhausted']} res_min {e['usable_reserve_g']['min']:.1f} r14/108 {[round(x,1) for x in e['usable_reserve_runs_14_108'].values()]} fm {e['fail_modes']} Pab {e['P_abort']} apo50 {e['apogee_m']['p50']:.1f} pm {None if not e['purge_mass_g'] else (round(e['purge_mass_g']['min'],1),round(e['purge_mass_g']['max'],1))}")
