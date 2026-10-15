# REV-GNC-4 spot-check of mass_v35_vs_v3d.json against massprops_v3.5.json, BOM_v3.5.csv, ledger v3d and mechanical.json v2 (reviewer code)
import json, csv, sys, hashlib
H = "/home/claude/work/shared-fallback/engine"
MP = f"{H}/03-cad/massprops_v3.5.json"; BOM = f"{H}/03-cad/BOM_v3.5.csv"; LED = f"{H}/01-systems-gnc/vehicle/mass_ledger_v3d.csv"
MECH = sys.argv[2]; MJ = sys.argv[1]
sh = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
for p in (MP, BOM, LED, MECH, MJ): print(sh(p), p)
mp = json.load(open(MP)); mj = json.load(open(MJ)); me = json.load(open(MECH))
led = list(csv.DictReader(open(LED)))
L = {r["item"].split()[0]: r for r in led}
print("ledger items", len(led), "sum m_kg", round(sum(float(r["m_kg"]) for r in led), 5))
for k in ("P00", "P06", "P07", "P09", "P10", "P12"):
    r = L.get(k); print("  ledger", k, r and (r["m_kg"], r["z_m"], r["gimballed"], r["item"][:90]))
st = mp["states"]
for s in ("wet", "mid", "nograin"):
    e = st[s]["engine"]; print(f"  massprops {s} engine m {e['m_kg']} cg_mm {e['cg_mm']} Ipiv diag {[e['I_pivot_kgm2'][i][i] for i in range(3)]}")
print("  massprops fixed", st["mid"]["fixed"]["m_kg"], "ring", st["mid"]["ring"]["m_kg"], "horn", st["mid"]["horn"]["m_kg"], "pushrod", st["mid"]["pushrod"]["m_kg"], "all nograin", st["nograin"]["all"]["m_kg"])
gm = me["gimballed_mass_properties"]
dry_key = next(k for k in gm if "dry" in k)
for k_v3d, k_v35, lab in ((dry_key, "nograin", "dry"), ("wet_full_grain", "wet", "wet"), ("mid_burn", "mid", "mid")):
    a = gm[k_v3d]["I_pivot_kgm2"]["v"]; b = st[k_v35]["engine"]["I_pivot_kgm2"]
    ch = [100 * (b[i][i] / a[i][i] - 1) for i in (0, 1)]
    print(f"  TVC inertia {lab}: v3d {a[0][0]},{a[1][1]} (m {gm[k_v3d]['m_kg']['v']}) v35 {b[0][0]},{b[1][1]} change % {ch[0]:.2f},{ch[1]:.2f}")
# BOM sums by the author's part-number groups
bom = list(csv.DictReader(open(BOM)))
print("BOM columns", list(bom[0].keys())[:14], "rows", len(bom))
