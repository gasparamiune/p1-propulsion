import sys, json
import numpy as np
sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import post_f1 as PF, post_modal as PMd, asm_build as AB
run = sys.argv[1]
M, meta = PF.load_model(run)
Z = np.load(PF.RUNS / run / "B1_21.65" / "fields.npz")
Uf = Z["U_FREQ"].astype(np.float64)
m, grp, items = PMd.lumped_masses(M)
N1 = M.next_n + 1
Uf = Uf[:, :N1]
print("lumped total kg", m.sum() * 1e3, "n with mass", (m > 0).sum())
gm = np.einsum("kij,i->k", Uf ** 2, m)
md = json.load(open(PF.RUNS / run / "B1_21.65" / "modal.json"))
tot = np.zeros(3)
for k in range(min(12, Uf.shape[0])):
    L = np.einsum("ij,i->j", Uf[k], m)          # sum m phi (t)
    me = L ** 2 / gm[k] * 1e3                    # kg
    tot += me
    print(k + 1, round(md["modes"][k]["f_Hz"], 1), "lumped eff kg", np.round(me, 3), "ccx", np.round(np.array(md["effective_mass"][k][1:4]) * 1e3, 3))
allL = np.einsum("kij,i->kj", Uf, m); print("sum 60 modes lumped kg", np.round((allL ** 2 / gm[:, None]).sum(0) * 1e3, 3), "ccx total", np.round(np.array(md["total_effective_mass"][:3]) * 1e3, 3))
