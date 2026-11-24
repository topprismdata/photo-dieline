import json, sys
import numpy as np
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
sys.path.insert(0, "/tmp/pd_recheck/probe_head")
from common import *

out = {}
for cid in T.all_classes():
    mod, params, ir, world = load(cid)
    polys = {p["id"]: np.array(p["polygon_2d"], float) for p in ir.panels}
    roles = {p["id"]: p["role"] for p in ir.panels}
    P2 = {k: Polygon(v) for k, v in polys.items()}
    fold_keys = {tuple(sorted((tuple(e.seg_2d[0]), tuple(e.seg_2d[1])))) for e in ir.edges}
    cuts = cut_segments(ir)
    # map cut seg -> owner panel(s)
    owner = {}
    for pid, poly in polys.items():
        n = len(poly)
        for i in range(n):
            a, b = tuple(poly[i]), tuple(poly[(i + 1) % n])
            owner.setdefault(tuple(sorted((a, b))), []).append(pid)
    union = unary_union([p.buffer(0) for p in P2.values()])
    bnd = union.boundary
    # C1: cut inside foreign panel interior
    bad = []
    tot = 0.0
    for (a, b) in cuts:
        seg = LineString([a, b])
        L = seg.length
        if L < 1e-9:
            continue
        own = set(owner.get(tuple(sorted((tuple(a), tuple(b)))), []))
        for q, pq in P2.items():
            if q in own:
                continue
            inner = seg.intersection(pq.buffer(-1e-6))
            if not inner.is_empty and inner.length > 1e-6:
                tot += inner.length
                bad.append((tuple(sorted(own)), q, round(float(inner.length), 2)))
    # C2: cut overlapping fold
    cf = []
    for (a, b) in cuts:
        for e in ir.edges:
            L = seg_overlap(np.array(a), np.array(b), np.array(e.seg_2d[0]), np.array(e.seg_2d[1]))
            if L > 1e-6:
                cf.append((tuple(sorted(owner.get(tuple(sorted((tuple(a), tuple(b)))), ['?']))), e.id, round(float(L), 2)))
                break
    # D: fold backing
    fd = []
    for e in ir.edges:
        a, b = np.array(e.seg_2d[0]), np.array(e.seg_2d[1])
        seg = LineString([a, b]); L = seg.length
        for pid in (e.parent, e.child):
            cov = 0.0
            poly = polys[pid]; n = len(poly)
            for i in range(n):
                ov = seg_overlap(a, b, poly[i], poly[(i + 1) % n])
                if ov > 0:
                    cov += ov
            if cov < L - 1e-6:
                fd.append((e.id, pid, round(float(cov) / L, 3)))
    holes = []
    if union.geom_type == "Polygon":
        for r in union.interiors:
            holes.append(round(float(Polygon(r).area), 2))
    else:
        for g in union.geoms:
            for r in g.interiors:
                holes.append(round(float(Polygon(r).area), 2))
    out[cid] = {"cut_in_foreign_total": round(float(tot), 2), "cut_in_foreign": bad,
                "cut_on_fold": cf, "fold_underbacked": fd, "holes": holes,
                "n_cut_segs": len(cuts), "n_parts": 1 if union.geom_type == "Polygon" else len(union.geoms)}
json.dump(out, open("/tmp/pd_recheck/probe_head/a2.json", "w"), ensure_ascii=False, indent=1, default=str)
print("== C1 cut inside foreign panel interior (total mm > 0.5) ==")
for cid, r in out.items():
    if r["cut_in_foreign_total"] > 0.5:
        agg = {}
        for own, q, L in r["cut_in_foreign"]:
            agg[q] = agg.get(q, 0.0) + L
        top = sorted(agg.items(), key=lambda kv: -kv[1])[:5]
        print(f"  {cid}: total={r['cut_in_foreign_total']} by_victim={top} n={len(r['cut_in_foreign'])}")
print("== C2 cut overlapping a fold (crease drawn as cut) ==")
for cid, r in out.items():
    if r["cut_on_fold"]:
        agg = {}
        for own, eid, L in r["cut_on_fold"]:
            agg[eid] = agg.get(eid, 0.0) + L
        print(f"  {cid}: {sorted(agg.items(), key=lambda kv: -kv[1])[:6]}")
print("== D under-backed folds ==")
for cid, r in out.items():
    if r["fold_underbacked"]:
        print(f"  {cid}: {r['fold_underbacked'][:6]}")
print("== holes ==")
for cid, r in out.items():
    if r["holes"]:
        print(f"  {cid}: holes={r['holes']}")
print("== multi-part nets ==", [cid for cid, r in out.items() if r["n_parts"] > 1])
