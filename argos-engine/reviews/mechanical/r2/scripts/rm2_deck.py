"""REV-MECH-2 (independent reviewer): CalculiX deck parser for the FEA3D decks (own code, no FEA3D module imported).

Parses one f1.inp(.gz): nodes, C3D10 elements per ELSET (= body), section -> material, SPRINGA elements + stiffness, *RIGID BODY
node sets + REF nodes, *BOUNDARY node set, *EQUATION (number of terms, nodes, coefficients), the TH-step *TEMPERATURE field, and per
step the *DLOAD (element, face, value | GRAV) and *CLOAD (node, dof, value) lists.  Writes a compact npz + json cache.

usage: python -I rm2_deck.py <deck.inp.gz> <cache_stem>
"""
from __future__ import annotations
import sys, gzip, json, re
from pathlib import Path
import numpy as np


def open_any(p):
    p = Path(p)
    return gzip.open(p, "rt") if p.suffix == ".gz" else open(p, "rt")


def kw_params(line):
    parts = [s.strip() for s in line.split(",")]
    kw = parts[0].upper()
    prm = {}
    for s in parts[1:]:
        if "=" in s:
            k, v = s.split("=", 1)
            prm[k.strip().upper()] = v.strip()
        elif s:
            prm[s.strip().upper()] = True
    return kw, prm


def parse(path):
    nodes_id, nodes_x = [], []
    elem = {}            # elset -> list of rows (id + 10 nodes)
    springs = []         # (eid, n1, n2, elset)
    spring_k = {}        # elset -> k
    sections = {}        # elset -> material
    nsets = {}           # name -> list of nodes
    rigid = []           # (nset, ref, rot)
    boundary = []        # (nset or node, dof1, dof2)
    eqs = []             # list of (nodes array, dofs array, coefs array)
    steps = []           # list of dict(name, dload, cload, temp)
    temp = None
    cur = None
    step = None
    eq_pending = None
    lines = open_any(path)
    buf = []
    for raw in lines:
        line = raw.strip()
        if not line:
            if cur == ("SPRING",):
                continue
            continue
        if line.startswith("**"):
            m = re.match(r"\*\* step (\S+)", line)
            if m:
                pending_step_name = m.group(1)
                globals()["_pending_name"] = pending_step_name
            continue
        if line.startswith("*"):
            kw, prm = kw_params(line)
            if kw == "*NODE":
                cur = ("NODE", prm.get("NSET"))
            elif kw == "*ELEMENT":
                typ = prm.get("TYPE", "").upper()
                es = prm.get("ELSET")
                cur = ("ELEMENT", typ, es)
                if typ == "C3D10":
                    elem.setdefault(es, [])
            elif kw == "*SPRING":
                cur = ("SPRING", prm.get("ELSET"))
            elif kw == "*SOLID SECTION":
                sections[prm["ELSET"]] = prm["MATERIAL"]
                cur = None
            elif kw == "*NSET":
                cur = ("NSET", prm["NSET"])
                nsets.setdefault(prm["NSET"], [])
            elif kw == "*RIGID BODY":
                rigid.append((prm["NSET"], int(prm["REF NODE"]), int(prm.get("ROT NODE", -1))))
                cur = None
            elif kw == "*BOUNDARY":
                cur = ("BOUNDARY",)
            elif kw == "*EQUATION":
                cur = ("EQUATION",)
                eq_pending = None
            elif kw == "*STEP":
                step = {"name": globals().get("_pending_name", f"step{len(steps) + 1}"), "dload": [], "cload": [], "grav": [], "temp": None}
                steps.append(step)
                cur = None
            elif kw == "*TEMPERATURE":
                cur = ("TEMPERATURE",)
                if step is not None:
                    step["temp"] = []
            elif kw == "*DLOAD":
                cur = ("DLOAD",)
            elif kw == "*CLOAD":
                cur = ("CLOAD",)
            elif kw == "*END STEP":
                cur = None
                step = None
            else:
                cur = None
            continue
        if cur is None:
            continue
        t = cur[0]
        if t == "NODE":
            a = line.split(",")
            nodes_id.append(int(a[0]))
            nodes_x.append((float(a[1]), float(a[2]), float(a[3])))
        elif t == "ELEMENT":
            a = [int(x) for x in line.rstrip(",").split(",") if x.strip()]
            if cur[1] == "C3D10":
                buf += a
                if len(buf) >= 11:
                    elem[cur[2]].append(buf[:11])
                    buf = buf[11:]
            elif cur[1] == "SPRINGA":
                springs.append((a[0], a[1], a[2], cur[2]))
        elif t == "SPRING":
            try:
                spring_k[cur[1]] = float(line.split(",")[0])
            except ValueError:
                pass
        elif t == "NSET":
            nsets[cur[1]] += [int(x) for x in line.rstrip(",").split(",") if x.strip()]
        elif t == "BOUNDARY":
            a = [x.strip() for x in line.split(",")]
            boundary.append(a)
        elif t == "EQUATION":
            a = [x.strip() for x in line.rstrip(",").split(",") if x.strip()]
            if eq_pending is None:
                eq_pending = {"n": int(a[0]), "terms": []}
                continue
            for i in range(0, len(a), 3):
                eq_pending["terms"].append((int(a[i]), int(a[i + 1]), float(a[i + 2])))
            if len(eq_pending["terms"]) >= eq_pending["n"]:
                tt = np.array(eq_pending["terms"], dtype=float)
                eqs.append(tt)
                eq_pending = None
        elif t == "TEMPERATURE":
            a = line.split(",")
            if step is not None:
                try:
                    step["temp"].append((int(a[0]), float(a[1])))
                except ValueError:
                    step.setdefault("temp_sets", []).append((a[0].strip(), float(a[1])))
        elif t == "DLOAD":
            a = [x.strip() for x in line.split(",")]
            if a[1].upper() == "GRAV":
                step["grav"].append([float(a[2]), float(a[3]), float(a[4]), float(a[5])])
            else:
                step["dload"].append((int(a[0]), int(a[1].upper().lstrip("P")), float(a[2])))
        elif t == "CLOAD":
            a = [x.strip() for x in line.split(",")]
            step["cload"].append((int(a[0]), int(a[1]), float(a[2])))
    return dict(nodes_id=np.array(nodes_id), nodes_x=np.array(nodes_x), elem=elem, springs=springs, spring_k=spring_k,
                sections=sections, nsets=nsets, rigid=rigid, boundary=boundary, eqs=eqs, steps=steps)


def save(d, stem):
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    arr = {"nodes_id": d["nodes_id"], "nodes_x": d["nodes_x"]}
    bodies = []
    for es, rows in d["elem"].items():
        a = np.array(rows, dtype=np.int64)
        arr[f"E_{es}"] = a
        bodies.append(es)
    # equations: flattened
    nterm = np.array([len(e) for e in d["eqs"]], dtype=np.int64)
    arr["eq_nterm"] = nterm
    arr["eq_terms"] = np.vstack(d["eqs"]) if d["eqs"] else np.zeros((0, 3))
    for i, st in enumerate(d["steps"]):
        if st["dload"]:
            arr[f"DL_{i}"] = np.array(st["dload"], dtype=float)
        if st["cload"]:
            arr[f"CL_{i}"] = np.array(st["cload"], dtype=float)
        if st["temp"]:
            arr[f"T_{i}"] = np.array(st["temp"], dtype=float)
    np.savez_compressed(str(stem) + ".npz", **arr)
    meta = {"bodies": bodies, "sections": d["sections"], "springs": d["springs"], "spring_k": d["spring_k"],
            "nsets": {k: v for k, v in d["nsets"].items()}, "rigid": d["rigid"], "boundary": d["boundary"],
            "steps": [{"i": i, "name": s["name"], "n_dload": len(s["dload"]), "n_cload": len(s["cload"]), "grav": s["grav"],
                       "has_temp": bool(s["temp"])} for i, s in enumerate(d["steps"])],
            "n_nodes": int(len(d["nodes_id"])), "n_eq": int(len(d["eqs"]))}
    Path(str(stem) + ".json").write_text(json.dumps(meta))
    return meta


if __name__ == "__main__":
    d = parse(sys.argv[1])
    meta = save(d, sys.argv[2])
    print(json.dumps({k: (v if k in ("n_nodes", "n_eq", "bodies", "sections", "spring_k") else None) for k, v in meta.items()}, indent=0)[:3000])
    print("steps:", [(s["name"], s["n_dload"], s["n_cload"], s["grav"], s["has_temp"]) for s in meta["steps"]])
