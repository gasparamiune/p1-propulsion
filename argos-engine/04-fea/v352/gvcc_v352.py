"""GVCC: closure-coupled J1 gap-conductance thermal variant (lead 2026-10-20 03:10Z, TC-02 option (a) APPROVED).  Mechanical, 2026-10-20, v1.

Basis (lead): J1 = the TC-01 / TC-02 fit (three lands) at the MAXIMUM designed clearance: bore 57.25 H8 at its upper limit 57.296 with the
plug 57.20 f7 at its lower limit 57.140, cold radial clearance c0 = 0.078 mm (DERIVED from the drawing callouts in 03-cad/src/parts_engine.py:
TC-01 'fwd bore 57.25 H8 (+0.046/0) Ra 0.8', TC-02 'plug 57.20 f7 (-0.030/-0.060)').  The J1 conductance follows the computed plug-to-bore
closure at every step:
  g_L(t) = c0 + r_m (eps_TC01,L(t) - eps_TC02,L(t))      per land L (z windows from the GVLO strip segments),
  eps = area x r weighted mean secant thermal strain alpha(T) (T - 20 C) of the part's section elements whose centroid lies within the land's
  z range +/- 1 mm (the free-ring rule of v352/checks/closure_sweep.py; plane-stress free annulus: ID and OD grow by this mean strain),
  alpha = engmat AL6061-T6 mean CTE from 20 C (ASM Handbook Vol. 2, LITERATURE), r_m = 28.6125 mm.
  open (g > 0):  h = k_air(T) / g + 4 sigma eps_eff T^3   (k_air Incropera & DeWitt Table A.4 as GVLO, kmul 1.0, eps_eff from the GVLO record),
                 capped at h_c (a gas gap thinner than k_air / h_c ~ 9 um is not credited above the contact value);
  closed (g <= 0): h = h_c, the contact conductance; range and source in H_C; the LOW end is used (conservative for the TC-02-hot margin).
J2 / J3 stay at their GVLO strips (0.110 / 0.240 mm).  Mesh = the GVLO mesh (same strips); only the J1 strip conductivity changes.
Implementation: the GVLO deck with the J1 strip split into its three lands (own element sets) and every step split into sub-steps at the
output instants (0.5 s in the burn, 1 s / 2 s early soak, 20 s / 200 s late soak); each sub-step carries *CHANGE SOLID SECTION to the land's
strip material for that sub-step (CalculiX 2.21; checked on a 3-layer CAX6 strip, v352/gvcc/css_test: 399.02 -> 391.67 -> 399.02 K exact).
The gap schedule comes from the previous pass (fixed-point iteration): pass 0 = GVLO (J1 0.090 mm), pass 1 = 0.5 relaxation of the GVLO
closure, later passes a per-land, per-instant secant on (applied, computed) gap; converged when the computed and the applied gaps differ
by < 2 um at every sub-step and the TC-02 maximum changes by < 0.3 K.  Evidence: SIM (ccx) + CALC (closure rule) on LITERATURE / ASSUMED
inputs; nothing here is physical validation.
Usage: gvcc_v352.py run [--threads 2] [--max_pass 4] | deck --pass k (write only) | probe (deck of COAST + 2 burn sub-steps, ccx check)"""
import sys, os, json, math, gzip, time, hashlib, shutil, subprocess, argparse
from pathlib import Path
import numpy as np

TH = Path("/home/claude/work/mechanical/v352/engine/04-fea/thermal")
sys.path.insert(0, str(TH))
import ax_thermal as at          # noqa: E402
import engmat                    # noqa: E402
import run_thermal as rt         # noqa: E402  (postprocess)

RUNS = Path("/home/claude/work/mechanical/runs/thermal")
PRE = "DC-B1v3p99_tg711_hi_SS316L_L2.5_"
BASE_TAG = "v352_NF2b_GVLO"
BASE = RUNS / (PRE + BASE_TAG)
TAG = "v352_NF2b_GVCC"
LABEL = PRE + TAG
OUT = RUNS / LABEL
WD = Path("/home/claude/work/mechanical/v352/gvcc")
LOG = Path("/home/claude/work/mechanical/v352/logs/gvcc.log")
C0_MM = round((57.296 - 57.140) / 2, 4)          # 0.078
R_M = 28.6125
W_MM = 0.30
SIG = 5.670374e-8
TS = [293.15, 350.0, 400.0, 500.0, 600.0, 800.0, 1000.0, 1200.0, 1400.0, 1800.0, 2400.0]
H_C = {"low_W_m2K": 2000.0, "air_W_m2K": 3640.0, "high_W_m2K": 6700.0, "used": "low",
       "source": "LITERATURE, AS RECALLED (TO-VERIFY page): Incropera & DeWitt, Fundamentals of Heat and Mass Transfer 6th ed., Table 3.1 "
                 "(metallic interfaces under vacuum, aluminium, 100 kN/m2: R''tc 1.5-5.0 e-4 m2K/W -> 2000-6700 W/m2K) and Table 3.2 "
                 "(aluminium-aluminium, air, 10 um roughness, 1e5 N/m2: 2.75 e-4 -> 3640 W/m2K); a fit closing by free-ring overlap starts at "
                 "near-zero contact pressure, so the low end applies to the TC-02-hot margin"}
DZ_WIN = 1.0
TOL_DONE_MM = 0.002
TOL_TC02_K = 0.3


def log(msg):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}\n")
    print(msg, flush=True)


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


# ------------------------------------------------------------------------------------------------ base deck + mesh
def read_base():
    inp = BASE / f"{PRE}{BASE_TAG}.inp"
    lines = inp.read_text().splitlines()
    meta = json.loads((BASE / f"{PRE}{BASE_TAG}_meta.json").read_text())
    nodes, elems, elsets = {}, {}, {}
    cur, cur_set = None, None
    for ln in lines:
        if ln.startswith("*"):
            u = ln.upper()
            cur, cur_set = None, None
            if u.startswith("*NODE") and not u.startswith("*NODE PRINT") and not u.startswith("*NODE FILE"):
                cur = "node"
            elif u.startswith("*ELEMENT"):
                cur = "elem"
                cur_set = [p.split("=")[1].strip() for p in ln.split(",") if p.strip().upper().startswith("ELSET=")][0]
                elsets.setdefault(cur_set, [])
            elif u.startswith("*ELSET"):
                cur = "elset"
                cur_set = [p.split("=")[1].strip() for p in ln.split(",") if p.strip().upper().startswith("ELSET=")][0]
                elsets.setdefault(cur_set, [])
            continue
        if ln.startswith("**") or not ln.strip():
            continue
        if cur == "node":
            p = ln.split(",")
            nodes[int(p[0])] = (float(p[1]), float(p[2]))
        elif cur == "elem":
            p = [int(x) for x in ln.split(",") if x.strip()]
            elems[p[0]] = p[1:7]
            elsets[cur_set].append(p[0])
        elif cur == "elset":
            elsets[cur_set].extend(int(x) for x in ln.split(",") if x.strip())
    return lines, meta, nodes, elems, elsets


def lands_and_windows(meta, nodes, elems, elsets):
    j1 = meta["gap_variant"]["joints"]["J1"]
    segs = j1["segments"]
    strip = elsets["M_GAP_J1"]
    lands = []
    for k, s in enumerate(segs):
        z0, z1 = s["z_mm"]
        zo0, zo1 = s["z_overlap_mm"]
        lands.append({"name": f"L{k + 1}", "z_strip_mm": [z0, z1], "z_overlap_mm": [zo0, zo1], "elems": [], "win": {}})
    for e in strip:
        zc = np.mean([nodes[n][1] for n in elems[e][:3]])
        hit = [L for L in lands if L["z_strip_mm"][0] - 1e-6 <= zc <= L["z_strip_mm"][1] + 1e-6]
        if len(hit) != 1:
            raise RuntimeError(f"J1 strip element {e} at z {zc:.3f} in {len(hit)} lands")
        hit[0]["elems"].append(e)
    for L in lands:
        zlo, zhi = L["z_overlap_mm"][0] - DZ_WIN, L["z_overlap_mm"][1] + DZ_WIN
        for pn, es in (("ENG-TC-01", elsets["P_ENG_TC_01"]), ("ENG-TC-02", elsets["P_ENG_TC_02"])):
            sel = [e for e in es if zlo <= np.mean([nodes[n][1] for n in elems[e][:3]]) <= zhi]
            L["win"][pn] = sel
    return lands, j1


class Closure:
    """Free-ring gap of each land from a nodal temperature field (K, indexed by node id)."""

    def __init__(self, lands, nodes, elems):
        self.lands = lands
        Ta = np.arange(250.0, 900.0, 1.0)
        self.Ta = Ta
        self.al = np.array([engmat.prop("AL6061-T6", "alpha", T - 273.15) for T in Ta])
        self.geo = {}
        ids = set()
        for L in lands:
            for pn, es in L["win"].items():
                con = np.array([elems[e] for e in es])
                xy = np.array([[nodes[n] for n in elems[e][:3]] for e in es])
                A = 0.5 * np.abs((xy[:, 1, 0] - xy[:, 0, 0]) * (xy[:, 2, 1] - xy[:, 0, 1]) - (xy[:, 2, 0] - xy[:, 0, 0]) * (xy[:, 1, 1] - xy[:, 0, 1]))
                rc = xy[:, :, 0].mean(axis=1)
                self.geo[(L["name"], pn)] = (con, A * rc)
                ids.update(con.ravel().tolist())
        self.node_ids = sorted(ids)

    def gaps(self, Tn):
        out = {}
        for L in self.lands:
            eps = {}
            for pn in ("ENG-TC-01", "ENG-TC-02"):
                con, w = self.geo[(L["name"], pn)]
                Te = np.array([[Tn[n] for n in row] for row in con]).mean(axis=1)
                al = np.interp(Te, self.Ta, self.al)
                eps[pn] = float(np.sum(al * (Te - 293.15) * w) / np.sum(w))
            out[L["name"]] = {"dgap_mm": (eps["ENG-TC-01"] - eps["ENG-TC-02"]) * R_M, "eps_TC01": eps["ENG-TC-01"], "eps_TC02": eps["ENG-TC-02"]}
        return out


def frd_frames(path, keep):
    """(t, {node: T}) for the kept node ids, from an ASCII or gzipped .frd."""
    op = (lambda: gzip.open(path, "rt")) if str(path).endswith(".gz") else (lambda: open(path))
    keep = set(keep)
    t, inblk, vals = None, False, None
    with op() as fh:
        for line in fh:
            if line.startswith("  100CL"):
                t = float(line[12:24])
                inblk, vals = False, {}
                continue
            if line.startswith(" -4  NDTEMP"):
                inblk = True
                continue
            if inblk:
                if line.startswith(" -1"):
                    n = int(line[3:13])
                    if n in keep:
                        vals[n] = float(line[13:25])
                elif line.startswith(" -3"):
                    inblk = False
                    yield t, vals


def history(frd, clo):
    H = {"t": [], **{L["name"]: [] for L in clo.lands}}
    for t, vals in frd_frames(frd, clo.node_ids):
        g = clo.gaps(vals)
        H["t"].append(t)
        for L in clo.lands:
            H[L["name"]].append(C0_MM + g[L["name"]]["dgap_mm"])
    return {k: np.array(v) for k, v in H.items()}


# ------------------------------------------------------------------------------------------------ sub-steps and deck
def substeps():
    S = [("COAST", 0.0, 0.001, 1, 1000)]
    t0 = 0.001
    for i in range(43):
        S.append(("BURN", t0 + 0.5 * i, 0.05, 10, 10))
    S.append(("BURN", t0 + 21.5, 0.05, 3, 10))
    tb = 21.651
    for i in range(20):
        S.append(("SOAK0.5", tb + 1.0 * i, 0.5, 2, 2))
    for i in range(20):
        S.append(("SOAK0.5", tb + 20.0 + 2.0 * i, 0.5, 4, 2))
    ts5 = 81.651
    for i in range(27):
        S.append(("SOAK5", ts5 + 20.0 * i, 5.0, 4, 1))
    ts20 = 621.651
    for i in range(15):
        S.append(("SOAK20", ts20 + 200.0 * i, 20.0, 10, 1))
    return [{"k": k, "step": s, "t0": round(a, 4), "dt": dt, "n": n, "freq": f, "t1": round(a + dt * n, 4), "t_mid": round(a + 0.5 * dt * n, 4)}
            for k, (s, a, dt, n, f) in enumerate(S)]


def base_steps(lines):
    """{name: (load lines, n_inc_orig)} from the base deck (the lines between the time line and *NODE PRINT of each step)."""
    out, i = {}, 0
    while i < len(lines):
        if lines[i].startswith("** ") and any(lines[i][3:].startswith(s) for s in ("COAST", "BURN", "SOAK0.5", "SOAK5", "SOAK20")):
            name = lines[i][3:].split()[0]
            assert lines[i + 1].startswith("*STEP") and lines[i + 2].startswith("*HEAT TRANSFER"), lines[i:i + 3]
            j = i + 4
            loads = []
            while not lines[j].startswith("*NODE PRINT"):
                loads.append(lines[j])
                j += 1
            out[name] = loads
            i = j
        i += 1
    return out


def k_table(g_mm, eps_eff, hc):
    rows = []
    for T in TS:
        if g_mm <= 0.0:
            h = hc
        else:
            h = min(at.air_k(T) / (g_mm * 1e-3) + 4 * SIG * eps_eff * T ** 3, hc)
        rows.append((h * W_MM * 1e-3, T))
    return rows


def write_deck(path, sched, lines, lands, clo, eps_eff, hc, n_sub=None):
    """sched: {land: array of applied gaps (mm) per sub-step}."""
    SS = substeps()
    if n_sub is not None:
        SS = SS[:n_sub]
    loads = base_steps(lines)
    first_step = next(i for i, l in enumerate(lines) if l.startswith("** COAST"))
    model = lines[:first_step]
    k_ss = next(i for i, l in enumerate(model) if l.startswith("*SOLID SECTION, ELSET=M_GAP_J1"))
    nmon = set()
    k_nm = next(i for i, l in enumerate(model) if l.startswith("*NSET, NSET=NMON"))
    j = k_nm + 1
    while not model[j].startswith("*"):
        nmon.update(int(x) for x in model[j].split(",") if x.strip())
        j += 1
    win = [n for n in clo.node_ids if n not in nmon]
    ins = []
    for L in lands:
        ins.append(f"*ELSET, ELSET=M_GJ1_{L['name']}")
        e = L["elems"]
        ins += [", ".join(map(str, e[i:i + 12])) for i in range(0, len(e), 12)]
    ins.append("*NSET, NSET=NJ1W")
    ins += [", ".join(map(str, win[i:i + 12])) for i in range(0, len(win), 12)]
    for L in lands:
        for s in SS:
            g = float(sched[L["name"]][s["k"]])
            ins += [f"*MATERIAL, NAME=GJ1_{L['name']}_S{s['k']:03d}", "*DENSITY", "1.000000e-12", "*CONDUCTIVITY"]
            ins += [f"{k_:.6e}, {T:.2f}" for k_, T in k_table(g, eps_eff, hc)]
            ins += ["*SPECIFIC HEAT", "1.000000e+09, 293.15"]
    for L in lands:
        ins.append(f"*SOLID SECTION, ELSET=M_GJ1_{L['name']}, MATERIAL=GJ1_{L['name']}_S000")
    out = model[:k_ss] + ins + model[k_ss + 1:]
    for s in SS:
        out.append(f"** GVCC sub-step {s['k']} ({s['step']}) {s['t0']:.3f} -> {s['t1']:.3f} s")
        out.append(f"*STEP, INC={s['n'] + 10}")
        out.append("*HEAT TRANSFER, DIRECT")
        out.append(f"{s['dt']:.6f}, {s['dt'] * s['n']:.6f}")
        if s["k"] > 0:
            for L in lands:
                out.append(f"*CHANGE SOLID SECTION, ELSET=M_GJ1_{L['name']}, MATERIAL=GJ1_{L['name']}_S{s['k']:03d}")
        out += loads[s["step"]]
        # one print frequency per step in CalculiX (the last *NODE PRINT card sets it): no extra print, so the monitor output keeps the
        # GVLO per-increment resolution; the closure history is read from the .frd (all window nodes at every output frame)
        out += ["*NODE PRINT, NSET=NMON, FREQUENCY=1", "NT", f"*NODE FILE, FREQUENCY={s['freq']}", "NT", "*END STEP"]
    path.write_text("\n".join(out) + "\n")
    return len(out), len(win)


# ------------------------------------------------------------------------------------------------ schedule update
def at_mid(H, SS):
    """Computed gap history (frd frames) -> value per sub-step (mean of the sub-step start and end, linear in time)."""
    out = {}
    t = H["t"]
    for L in [k for k in H if k != "t"]:
        g = H[L]
        out[L] = np.array([0.5 * (np.interp(s["t0"], t, g) + np.interp(s["t1"], t, g)) for s in SS])
    return out


def update(passes, SS):
    """passes: list of (applied {L: arr}, computed {L: arr}); returns the next applied schedule and the update rule used."""
    Ha, Ga = passes[-1]
    if len(passes) == 1:
        return {L: Ha[L] + 0.5 * (Ga[L] - Ha[L]) for L in Ha}, "relaxation 0.5"
    Hb, Gb = passes[-2]
    nxt = {}
    for L in Ha:
        fa, fb = Ga[L] - Ha[L], Gb[L] - Hb[L]
        den = fa - fb
        sec = np.where(np.abs(den) > 1e-6, Ha[L] - fa * (Ha[L] - Hb[L]) / np.where(np.abs(den) > 1e-6, den, 1.0), Ha[L] + 0.5 * fa)
        lo, hi = np.minimum(Ha[L], Ga[L]), np.maximum(Ha[L], Ga[L])
        ok = (sec >= lo - 1e-6) & (sec <= hi + 1e-6)          # keep the secant inside the latest bracket, else relax
        nxt[L] = np.clip(np.where(ok, sec, Ha[L] + 0.5 * fa), -0.02, 0.25)
    return nxt, "secant per land and sub-step (bracketed; else relaxation 0.5)"


# ------------------------------------------------------------------------------------------------ run one pass
def ccx_pass(pdir, threads, label=LABEL):
    env = dict(os.environ, OMP_NUM_THREADS=str(threads), CCX_NPROC_EQUATION_SOLVER=str(threads))
    t0 = time.time()
    with open(pdir / f"{label}.log", "w") as fo:
        p = subprocess.Popen(["nice", "-n", "15", "ccx", "-i", label], cwd=str(pdir), env=env, stdout=fo, stderr=subprocess.STDOUT)
        mx = 0
        while p.poll() is None:
            time.sleep(20)
            try:                      # 'nice' execs ccx: p.pid is the ccx process itself
                rss = int(open(f"/proc/{p.pid}/status").read().split("VmRSS:")[1].split()[0])
                mx = max(mx, rss)
                if rss > 1500000:
                    log(f"RSS WARN {rss} kB ccx")
            except Exception:
                pass
    sta = (pdir / f"{label}.sta").read_text().strip().splitlines()[-1] if (pdir / f"{label}.sta").exists() else ""
    err = [l for l in (pdir / f"{label}.log").read_text().splitlines() if "*ERROR" in l]
    return {"seconds": round(time.time() - t0, 1), "returncode": p.returncode, "max_rss_kB": mx, "sta_last_line": sta, "errors": err[:5]}


def disk_ok(need_kB):
    st = os.statvfs("/home/claude")
    return st.f_bavail * st.f_frsize // 1024 >= need_kB


def postprocess(pdir, meta, m):
    meta2 = dict(meta)
    summ, env = rt.postprocess(pdir, LABEL, m, meta2)
    return summ, env


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "deck", "probe"])
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--max_pass", type=int, default=4)
    a = ap.parse_args()
    assert a.threads <= 2, "lead: <= 2 solver threads"
    lines, meta, nodes, elems, elsets = read_base()
    lands, j1 = lands_and_windows(meta, nodes, elems, elsets)
    clo = Closure(lands, nodes, elems)
    eps_eff = float(j1["eps_eff"])
    hc = H_C["low_W_m2K"]
    SS = substeps()
    z = np.load(BASE / "envelope_nodes.npz", allow_pickle=True)
    m = {"X": z["X"], "E": z["E"], "pn": z["pn"], "mat": z["mat"]}
    info = {L["name"]: {"z_strip_mm": L["z_strip_mm"], "z_overlap_mm": L["z_overlap_mm"], "n_strip_elems": len(L["elems"]),
                        "n_window_elems": {k: len(v) for k, v in L["win"].items()}} for L in lands}
    log(f"GVCC setup: c0 {C0_MM} mm, lands {json.dumps(info)}, window nodes {len(clo.node_ids)}, sub-steps {len(SS)}, h_c {hc}")
    if a.cmd == "probe":
        pdir = WD / "probe"
        pdir.mkdir(parents=True, exist_ok=True)
        sched = {L["name"]: np.full(len(SS), C0_MM) for L in lands}
        n, nw = write_deck(pdir / "probe.inp", sched, lines, lands, clo, eps_eff, hc, n_sub=3)
        log(f"probe deck {n} lines, NJ1W {nw} nodes")
        r = ccx_pass(pdir, 1, label="probe")
        log(f"probe ccx {r}")
        return
    # pass 0 = GVLO
    st_path = WD / "gvcc_state.json"
    state = json.loads(st_path.read_text()) if st_path.exists() else {"passes": []}
    passes = [({L: np.array(v) for L, v in p["applied"].items()}, {L: np.array(v) for L, v in p["computed"].items()}) for p in state["passes"]]
    if not passes:
        gz = next(BASE.glob("*.frd.gz"))
        H0 = history(gz, clo)
        applied0 = {L["name"]: np.full(len(SS), float(j1["g_hot_mm"])) for L in lands}
        comp0 = at_mid(H0, SS)
        env0 = json.loads((BASE / "envelope.json").read_text())["parts"]
        state["passes"].append({"pass": 0, "dir": str(BASE), "applied": {k: v.tolist() for k, v in applied0.items()},
                                "computed": {k: v.tolist() for k, v in comp0.items()}, "TC02_max_C": env0["ENG-TC-02"]["T_max_C"],
                                "TC02_t_s": env0["ENG-TC-02"]["t_max_s"], "max_abs_resid_mm": float(max(np.abs(comp0[L] - applied0[L]).max() for L in comp0)),
                                "history": {k: v.tolist() for k, v in H0.items()}})
        st_path.write_text(json.dumps(state))
        passes.append((applied0, comp0))
        log(f"pass 0 (GVLO) TC-02 {env0['ENG-TC-02']['T_max_C']} C; computed gap min " +
            ", ".join(f"{L} {comp0[L].min():.4f}" for L in comp0) + " mm")
    if a.cmd == "deck":
        nxt, rule = update(passes, SS)
        pdir = WD / f"pass{len(passes)}"
        pdir.mkdir(parents=True, exist_ok=True)
        n, nw = write_deck(pdir / f"{LABEL}.inp", nxt, lines, lands, clo, eps_eff, hc)
        log(f"deck pass {len(passes)} ({rule}): {n} lines")
        return
    while len(passes) <= a.max_pass:
        k = len(passes)
        nxt, rule = update(passes, SS)
        pdir = RUNS / f"{LABEL}_p{k}"
        if pdir.exists():
            shutil.rmtree(pdir)
        pdir.mkdir(parents=True)
        n, nw = write_deck(pdir / f"{LABEL}.inp", nxt, lines, lands, clo, eps_eff, hc)
        while not disk_ok(2600000):
            log("disk below 2.6 GB before the GVCC pass: waiting (lead floor 2.0 GB, thermal needs ~0.4 GB transient)")
            time.sleep(120)
        log(f"pass {k} start ({rule}); deck {n} lines; applied gap min " + ", ".join(f"{L} {nxt[L].min():.4f}" for L in nxt))
        r = ccx_pass(pdir, a.threads)
        log(f"pass {k} ccx {r}")
        if r["returncode"] != 0 or r["errors"] or "0.362165E+04" not in r["sta_last_line"]:
            log(f"pass {k} FAILED: stop")
            sys.exit(2)
        H = history(pdir / f"{LABEL}.frd", clo)
        comp = at_mid(H, SS)
        mk = dict(meta)
        mk["inp"] = str(pdir / f"{LABEL}.inp")
        summ, env = postprocess(pdir, mk, m)
        resid = float(max(np.abs(comp[L] - nxt[L]).max() for L in comp))
        rec = {"pass": k, "dir": str(pdir), "rule": rule, "applied": {L: v.tolist() for L, v in nxt.items()}, "computed": {L: v.tolist() for L, v in comp.items()},
               "TC02_max_C": env["ENG-TC-02"]["T_max_C"], "TC02_t_s": env["ENG-TC-02"]["t_max_s"], "TC02_at": env["ENG-TC-02"]["at_r_z_mm"],
               "max_abs_resid_mm": resid, "ccx": r, "history": {kk: v.tolist() for kk, v in H.items()}}
        state["passes"].append(rec)
        st_path.write_text(json.dumps(state))
        passes.append((nxt, comp))
        dT = abs(env["ENG-TC-02"]["T_max_C"] - state["passes"][-2]["TC02_max_C"])
        log(f"pass {k}: TC-02 {env['ENG-TC-02']['T_max_C']} C at {env['ENG-TC-02']['t_max_s']} s {env['ENG-TC-02']['at_r_z_mm']}; "
            f"max |computed - applied| {resid * 1e3:.1f} um; dTC02 vs previous {dT:.2f} K")
        # keep the frd of this pass until the next pass has used it; delete the frd of older passes (own intermediate outputs)
        for p in state["passes"][:-1]:
            if p["pass"] > 0:
                f = Path(p["dir"]) / f"{LABEL}.frd"
                if f.exists():
                    f.unlink()
                    log(f"removed intermediate {f}")
        if resid < TOL_DONE_MM and dT < TOL_TC02_K:
            log(f"CONVERGED at pass {k}")
            finalize(pdir, rec, state, meta, lands, j1, hc)
            log("GVCC_DONE")
            return
    log("max passes reached without convergence: last pass kept as the result, residual reported")
    finalize(Path(state["passes"][-1]["dir"]), state["passes"][-1], state, meta, lands, j1, hc, converged=False)
    log("GVCC_DONE")


def finalize(pdir, rec, state, meta, lands, j1, hc, converged=True):
    if OUT.exists():
        shutil.move(str(OUT), str(OUT) + f"_old{int(time.time())}")
    shutil.move(str(pdir), str(OUT))
    SS = substeps()
    t_mid = np.array([s["t_mid"] for s in SS])
    closure = {}
    for L in lands:
        g = np.array(rec["computed"][L["name"]])
        Hh = np.array(rec["history"][L["name"]])
        th = np.array(rec["history"]["t"])
        closed = Hh <= 0.0
        closure[L["name"]] = {"gap_min_mm": round(float(Hh.min()), 4), "t_gap_min_s": round(float(th[int(np.argmin(Hh))]), 3),
                              "closed_any": bool(closed.any()),
                              "t_first_closed_frame_s": (round(float(th[np.argmax(closed)]), 3) if closed.any() else None),
                              "t_last_closed_frame_s": (round(float(th[len(closed) - 1 - np.argmax(closed[::-1])]), 3) if closed.any() else None),
                              "gap_end_of_burn_mm": round(float(np.interp(21.651, th, Hh)), 4),
                              "gap_max_soak_mm": round(float(Hh[th > 21.7].max()), 4)}
    gv = {"name": "GVCC", "basis": __doc__.split("Implementation:")[0].strip(), "c0_mm": C0_MM, "r_m_mm": R_M, "w_strip_mm": W_MM,
          "h_c": H_C, "eps_eff": j1["eps_eff"], "J2_J3": "as GVLO (0.110 / 0.240 mm)", "base_deck": str(BASE), "converged": converged,
          "passes": [{k: p[k] for k in ("pass", "dir", "TC02_max_C", "TC02_t_s", "max_abs_resid_mm") if k in p} for p in state["passes"]],
          "closure": closure, "sub_steps": len(SS),
          "schedule_mm": {L["name"]: rec["applied"][L["name"]] for L in lands}, "t_mid_s": t_mid.tolist()}
    meta2 = dict(meta)
    meta2["inp"] = str(OUT / f"{LABEL}.inp")
    meta2["gap_variant"] = dict(meta["gap_variant"], name="GVCC", note="J1 closure-coupled (see gvcc)", gvcc=gv)
    meta2["case"] = dict(meta["case"], label=LABEL)
    meta2["ccx"] = rec["ccx"]
    env = json.loads((OUT / "envelope.json").read_text())["parts"]
    meta2["envelope"] = env
    (OUT / f"{LABEL}_meta.json").write_text(json.dumps(meta2, indent=1, default=str))
    (OUT / "summary.json").write_text(json.dumps({"label": LABEL, "envelope": env, "ccx": rec["ccx"], "gvcc": {k: gv[k] for k in ("closure", "passes", "converged", "c0_mm", "h_c")}}, indent=1))
    frd = OUT / f"{LABEL}.frd"
    if frd.exists():
        subprocess.run(["nice", "-n", "15", "gzip", "-f", str(frd)], check=True)
    (WD / "gvcc_result_v1.json").write_text(json.dumps({"label": LABEL, "dir": str(OUT), "gvcc": gv,
                                                        "envelope": {p: env[p] for p in env},
                                                        "sha256_16": {f.name: sha16(f) for f in sorted(OUT.iterdir()) if f.is_file() and f.suffix in (".gz", ".json", ".npz", ".csv")}},
                                                       indent=1, default=str))
    log(f"finalized {OUT}; result {WD / 'gvcc_result_v1.json'}")


if __name__ == "__main__":
    main()
