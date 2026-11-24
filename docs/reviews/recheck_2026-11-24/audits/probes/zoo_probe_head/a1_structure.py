import json, sys
import numpy as np
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
sys.path.insert(0, "/tmp/pd_recheck/probe_head")
from common import *
from photo_dieline.qa.pipeline import _intersect3d

out = {}
for cid in T.all_classes():
    try:
        mod, params, ir, world = load(cid)
    except Exception as exc:
        out[cid] = {"error": repr(exc)[:200]}
        continue
    rec = {"n_panels": len(ir.panels), "n_edges": len(ir.edges)}
    polys = {p["id"]: np.array(p["polygon_2d"], float) for p in ir.panels}
    roles = {p["id"]: p["role"] for p in ir.panels}
    P2 = {k: Polygon(v).buffer(0) for k, v in polys.items()}
    share = {frozenset((e.parent, e.child)) for e in ir.edges}
    parent = {e.child: e.parent for e in ir.edges}
    norms = {}
    for pid, v in world.items():
        n, s = plane_normal(v)
        norms[pid] = n
        pa = v
        cr = np.cross(pa[1] - pa[0], pa[2] - pa[0])
        rec.setdefault("degen_first_tri", [])
        if np.linalg.norm(cr) < 1e-7 * max(1e-9, float(np.abs(pa).max())):
            rec["degen_first_tri"].append(pid)
        if Polygon(polys[pid]).is_valid is False or abs(Polygon(polys[pid]).area) < 1e-6:
            rec.setdefault("bad_poly", []).append(pid)

    # ---- B. net overlap
    ov = []
    ids = list(polys)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            ar = P2[a].intersection(P2[b]).area
            if ar > 1e-5:
                ov.append((a, b, round(float(ar), 2)))
    rec["net_overlap"] = ov
    sum_area = float(sum(P2[a].area for a in ids))
    union_area = float(unary_union(list(P2.values())).area)
    rec["net_dup_area"] = round(sum_area - union_area, 2)

    # ---- A. glue hosts
    gl = []
    for g in [p for p in ids if roles[p] == "glue"]:
        n = norms[g]
        hosts = []
        par = parent.get(g)
        for q in ids:
            if q == g:
                continue
            nq = norms[q]
            if nq is None or not coplanar(world[g], n, world[q], nq):
                continue
            A = Polygon(to2d(world[g], n)); B = Polygon(to2d(world[q], n))
            ar = A.intersection(B).area
            if ar > 1e-3:
                hosts.append((q, roles[q], round(float(ar), 2), q == par, frozenset((g, q)) in share))
        garea = float(Polygon(polys[g]).area)
        gl.append({"glue": g, "parent": par, "area": round(garea, 2), "hosts": hosts})
    rec["glue"] = gl

    # ---- E. coplanar overlap groups (folded)
    co = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            na, nb = norms[a], norms[b]
            if na is None or nb is None or not coplanar(world[a], na, world[b], nb):
                continue
            ar = Polygon(to2d(world[a], na)).intersection(Polygon(to2d(world[b], na))).area
            if ar > 1e-3:
                allowed = mod.allowed_overlap() | ALLOWED_OVERLAP
                why = ("share_fold" if frozenset((a, b)) in share else
                       "allowed" if frozenset((a, b)) in allowed else
                       "flap_flap" if roles[a] == "flap" and roles[b] == "flap" else
                       "FLAG")
                co.append((a, roles[a], b, roles[b], round(float(ar), 2), why))
    rec["coplanar_overlap"] = co

    # ---- F. robust non-coplanar crossing
    cr = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            na, nb = norms[a], norms[b]
            if na is None or nb is None or coplanar(world[a], na, world[b], nb):
                continue
            L = cross_len(world[a], na, world[b], nb)
            if L > 1e-3:
                allowed = mod.allowed_overlap() | ALLOWED_OVERLAP
                why = ("share_fold" if frozenset((a, b)) in share else
                       "allowed" if frozenset((a, b)) in allowed else
                       "flap_flap" if roles[a] == "flap" and roles[b] == "flap" else
                       "FLAG" if _intersect3d(world[a], world[b]) or _intersect3d(world[b], world[a]) else
                       "G06_MISS")
                cr.append((a, roles[a], b, roles[b], round(float(L), 2), why))
    rec["crossing"] = cr
    out[cid] = rec

json.dump(out, open("/tmp/pd_recheck/probe_head/a1.json", "w"), ensure_ascii=False, indent=1, default=str)

# ---------- report
print("== A. glue hosts ==")
for cid, r in out.items():
    if "error" in r:
        print(cid, "ERROR", r["error"]); continue
    for g in r["glue"]:
        real = [h for h in g["hosts"] if not h[3] and not h[4]]
        selfh = [h for h in g["hosts"] if h[3] or h[4]]
        tag = "OK" if real else ("SELF" if selfh else "NONE")
        if tag != "OK" or len(real) != 1 or real[0][2] < 0.98 * g["area"]:
            print(f"  [{tag}] {cid}: glue={g['glue']} parent={g['parent']} area={g['area']} hosts={g['hosts']}")
print("== B. net overlap (dup area > 0.01) ==")
for cid, r in out.items():
    if "error" in r: continue
    if r["net_dup_area"] > 0.01:
        print(f"  {cid}: dup={r['net_dup_area']} pairs={r['net_overlap'][:6]}{'...' if len(r['net_overlap'])>6 else ''}")
print("== degen first tri / bad poly ==")
for cid, r in out.items():
    if "error" in r: continue
    if r.get("degen_first_tri") or r.get("bad_poly"):
        print(f"  {cid}: degen={r['degen_first_tri']} bad={r.get('bad_poly')}")
print("== F. crossings ==")
for cid, r in out.items():
    if "error" in r: continue
    for c in r["crossing"]:
        if c[5] in ("G06_MISS", "FLAG", "flap_flap", "allowed"):
            print(f"  {cid}: {c}")
