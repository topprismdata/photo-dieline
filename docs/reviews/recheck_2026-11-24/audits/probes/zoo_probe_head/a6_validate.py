import json, sys
import numpy as np
from shapely.geometry import Polygon, LineString
sys.path.insert(0, "/tmp/pd_recheck/probe_head")
from common import *

SKIP = {"kind", "fam", "variant", "n", "k", "lid", "dome_k"}

def flags(ir, world):
    polys = {p["id"]: np.array(p["polygon_2d"], float) for p in ir.panels}
    roles = {p["id"]: p["role"] for p in ir.panels}
    f = set()
    for pid, v in polys.items():
        P = Polygon(v)
        if abs(P.area) < 1e-3 or (not P.is_valid and P.buffer(0).area < 0.999 * abs(P.area)):
            f.add("degenerate_panel:" + pid)
    norms = {pid: plane_normal(v)[0] for pid, v in world.items()}
    parent = {e.child: e.parent for e in ir.edges}
    share = {frozenset((e.parent, e.child)) for e in ir.edges}
    for g in [p for p in polys if roles[p] == "glue"]:
        n = norms[g]
        if n is None:
            continue
        A = Polygon(to2d(world[g], n))
        hosts = []; self_ov = 0.0
        for q in polys:
            if q == g or norms[q] is None or not coplanar(world[g], n, world[q], norms[q]):
                continue
            ar = A.intersection(Polygon(to2d(world[q], n))).area
            if frozenset((g, q)) in share:
                self_ov += ar
            elif ar > 1e-3:
                hosts.append(ar)
        if not hosts and self_ov > 0.5 * A.area:
            f.add("glue_on_own_panel")
        elif hosts:
            inside = 0.0
            for q in polys:
                if q == g or norms[q] is None or not coplanar(world[g], n, world[q], norms[q]) or frozenset((g, q)) in share:
                    continue
                inside = max(inside, A.intersection(Polygon(to2d(world[q], n))).area)
            if inside < 0.95 * A.area:
                f.add("glue_overhang")
    tot = 0.0
    P2 = {k: Polygon(v).buffer(0) for k, v in polys.items()}
    own = {}
    for pid, poly in polys.items():
        for i in range(len(poly)):
            own.setdefault(tuple(sorted((tuple(poly[i]), tuple(poly[(i + 1) % len(poly)])))), []).append(pid)
    for (a, b) in cut_segments(ir):
        seg = LineString([a, b])
        o = set(own.get(tuple(sorted((tuple(a), tuple(b)))), []))
        for q, pq in P2.items():
            if q in o:
                continue
            x = seg.intersection(pq.buffer(-1e-6))
            if not x.is_empty:
                tot += x.length
    f.add(f"cut_foreign={tot:.1f}")
    return f

res = {}
for cid in T.all_classes():
    mod, params, ir0, world0 = load(cid)
    base_flags = flags(ir0, world0)
    base_cut = [x for x in base_flags if x.startswith("cut_foreign")][0]
    rec = {"base_flags": sorted(x for x in base_flags if not x.startswith("cut_foreign")), "base_cut": base_cut, "trials": []}
    for k, v in params.items():
        if k in SKIP or not isinstance(v, (int, float)) or isinstance(v, bool) or abs(float(v)) < 1e-12:
            continue
        for fac in (0.25, 0.5, 2.0, 4.0):
            nv = float(v) * fac
            if isinstance(v, int) and k in ("n",):
                continue
            p2 = dict(params); p2[k] = nv
            try:
                raw = mod.build_ir(p2); raw.pop("_derived", None)
                ir = from_raw(raw)
                st = "accepted"
            except Exception as exc:
                rec["trials"].append((k, fac, "REJECT", type(exc).__name__ + ":" + str(exc)[:60].replace("\n", " ")))
                continue
            try:
                world = fold_all(ir)
                st, rep = qa_status(ir)
            except Exception as exc:
                rec["trials"].append((k, fac, "FOLD_ERR", repr(exc)[:60])); continue
            if st != "GREEN":
                rec["trials"].append((k, fac, "QA_FAIL", st)); continue
            fl = flags(ir, world)
            cut = [x for x in fl if x.startswith("cut_foreign")][0]
            fl2 = sorted(x for x in fl if not x.startswith("cut_foreign"))
            try:
                lk = leak(world, N=10)
                lkv = round(lk["leak_any"], 2) if lk and lk.get("n_interior") else None
            except Exception:
                lkv = None
            rec["trials"].append((k, fac, "GREEN", {"flags": fl2, "cut": cut, "leak_any": lkv}))
    res[cid] = rec
json.dump(res, open("/tmp/pd_recheck/probe_head/a6.json", "w"), ensure_ascii=False, indent=1, default=str)
for cid, rec in res.items():
    from collections import Counter
    c = Counter(t[2] for t in rec["trials"])
    greens = [t for t in rec["trials"] if t[2] == "GREEN"]
    newfl = [t for t in greens if any(f not in rec["base_flags"] for f in t[3]["flags"])]
    base_leak = None
    print(f"{cid}: base_flags={rec['base_flags']} trials={dict(c)} GREEN_with_new_flags={len(newfl)}/{len(greens)}")
