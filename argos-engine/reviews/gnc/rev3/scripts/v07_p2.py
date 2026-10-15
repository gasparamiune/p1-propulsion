"""REV-GNC-5 v07: independent recomputation of P2 (v3.5-class landing mass at 285 m and the apogee / gain options) from the
staged rev3 SIM tables.  For every P2 arm: P per main base, pooled exact McNemar against the same-state ledger-v3d arm
(liq|G73|h285 or pw|G73|h285), first on the flown 60 g residual basis and then with the R3-17 dip onset (62 / 69 / 80 g)
applied to BOTH arms (a landed run with liquid left below the onset counts as lost).  Also: the band sets with no
significant pooled loss per family and onset, monotonicity of the loss pattern over the 5 m bands, kd70 / ht5 against the
same-mass h285 arm, a one-sided 95 % upper bound on the pooled P deficit (non-inferiority view), and the minimum usable
reserve.  SIM tables -> DERIVED.  Usage: python -I v07_p2.py <out.json>"""
import json, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rv5lib as L

ONS = {"60g_flown": None, "125N_62g": 62.0, "250N_69g": 69.0, "500N_80g": 80.0}
BANDS = ("h285", "h275", "h265", "h255", "h245")
FAM = [(s, v) for s in ("liq", "pw") for v in ("v35a", "v35t")]


def okon(rows, onset):
    o = L.ok(rows)
    if onset is None:
        return o
    return [a and (1e3 * float(r["liq_left"]) - onset >= 0.0) for a, r in zip(o, rows)]


def pool(ref_nm, case_nm, onset):
    prs = []
    for b in L.MAIN:
        ra = L.load3(b, ref_nm); rb = L.load3(b, case_nm)
        prs.append(L.paired(ra, rb, okon(ra, onset), okon(rb, onset)))
    d = L.pooled(prs)
    # one-sided 95 % upper bound on the paired P deficit (normal approx. for paired proportions; DERIVED, for the
    # non-inferiority view only)
    n = d["n"]; b_, c_ = d["lost"], d["gained"]
    diff = (b_ - c_) / n
    se = math.sqrt(max(b_ + c_ - (b_ - c_) ** 2 / n, 0.0)) / n
    d["deficit_pp"] = round(100 * diff, 2); d["deficit_ub95_pp"] = round(100 * (diff + 1.645 * se), 2)
    d["per_base_P_case"] = [round(x["P_case"], 4) for x in prs]
    return d


out = dict(script="v07_p2 (REV-GNC-5)", tag="SIM tables; DERIVED statistics (dip onset re-count)", arms={}, sets={}, monotone={}, extra={})
arms = []
for s, v in FAM:
    for h in BANDS:
        arms.append((f"{s}|G73|h285", f"{s}|G73|{v}|{h}"))
    for x in ("kd70", "ht5"):
        arms.append((f"{s}|G73|h285", f"{s}|G73|{v}|{x}|h285"))
for s in ("liq", "pw"):
    for dm in ("dm100g", "dm200g", "dm300g", "dm450g"):
        arms.append((f"{s}|G73|h285", f"{s}|G73|{dm}|h285"))
arms.append(("liq|G73|h285", "liq|G73|v35g|h285"))
for ref, nm in arms:
    if L.load3("A1_none", nm) is None:
        out["arms"][nm] = "MISSING TABLE"; continue
    e = {}
    for k, on in ONS.items():
        e[k] = pool(ref, nm, on)
    rows = L.load3("A1_none", nm) + L.load3("A1J_pc", nm)
    okk = L.ok(rows)
    u = [1e3 * float(r["liq_left"]) for r, o in zip(rows, okk) if o]
    e["liq_left_landed_g_min_p01"] = [round(min(u), 1), round(L.q(u, (1,))[0], 1)] if u else None
    e["exhausted"] = sum(float(r["exhausted"]) > 0.5 for r in rows)
    e["sha16"] = [L.sha16(L.path3(b, nm)) for b in L.MAIN]
    out["arms"][nm] = e
# band sets with no significant pooled loss, per family and onset; monotonicity
for s, v in FAM:
    for k in ONS:
        ok_b = [h for h in BANDS if not out["arms"][f"{s}|G73|{v}|{h}"][k]["loses"]]
        lose_b = [h for h in BANDS if out["arms"][f"{s}|G73|{v}|{h}"][k]["loses"]]
        out["sets"][f"{s}|{v}|{k}"] = dict(no_sig_loss=ok_b, loses=lose_b,
                                          kd70_no_sig_loss=not out["arms"][f"{s}|G73|{v}|kd70|h285"][k]["loses"],
                                          ht5_no_sig_loss=not out["arms"][f"{s}|G73|{v}|ht5|h285"][k]["loses"])
        # monotone if, ordered from 245 up, once a band loses all higher bands lose
        seq = [out["arms"][f"{s}|G73|{v}|{h}"][k]["loses"] for h in reversed(BANDS)]
        first = seq.index(True) if True in seq else None
        out["monotone"][f"{s}|{v}|{k}"] = dict(pattern_245_to_285=["L" if x else "-" for x in seq],
                                              monotone=(first is None or all(seq[first:])),
                                              highest_no_sig_loss=next((h for h in BANDS if not out["arms"][f"{s}|G73|{v}|{h}"][k]["loses"]), None),
                                              highest_below_first_loss=(None if first == 0 else (list(reversed(BANDS))[first - 1] if first else "h285")))
# kd70 / ht5 against the same-mass h285 arm
for s, v in FAM:
    for x in ("kd70", "ht5"):
        for k, on in ONS.items():
            out["extra"][f"{s}|{v}|{x} vs {s}|G73|{v}|h285|{k}"] = pool(f"{s}|G73|{v}|h285", f"{s}|G73|{v}|{x}|h285", on)
json.dump(out, open(sys.argv[1], "w"), indent=1)
print("pooled vs same-state v3d (P_case vs P_ref -lost/+gained p; deficit pp [ub95]):")
for nm, e in out["arms"].items():
    if isinstance(e, str):
        print(" ", nm, e); continue
    print(f"  {nm:26s} " + " | ".join(f"{k}: {L.fmt(e[k])} [{e[k]['deficit_pp']}/{e[k]['deficit_ub95_pp']}]" for k in ONS)
          + f" | landed liq min/p01 {e['liq_left_landed_g_min_p01']} exh {e['exhausted']}")
print("sets:")
for k, d in out["sets"].items():
    m = out["monotone"][k]
    print(f"  {k:24s} no-loss {d['no_sig_loss']} loses {d['loses']} kd70 ok {d['kd70_no_sig_loss']} ht5 ok {d['ht5_no_sig_loss']} | 245->285 {''.join(m['pattern_245_to_285'])} monotone {m['monotone']} highest_no_loss {m['highest_no_sig_loss']} highest_below_first_loss {m['highest_below_first_loss']}")
print("kd70/ht5 vs same-mass h285:")
for k, d in out["extra"].items():
    print(f"  {k:44s} {L.fmt(d)}")
