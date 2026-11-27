"""WP-A3 v1.1: ledger 驱动语义封合编译 — closure_relations 台账 + UV 前后诊断"""
import sys, json, numpy as np
sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from photo_dieline.core.ir import class_module, from_raw
from photo_dieline.folding.engine import fold_all
from photo_dieline.parametric.sample import sample_variant
from pxr import Usd, UsdGeom, Sdf, Gf, Vt
sys.path.insert(0, "scripts")
from auditor_core import audit_stage

params, _ = sample_variant("aseptic_brick", 0, allow_identity=True)
mod = class_module("aseptic_brick")
ir_raw = mod.build_ir(params); ir_raw.pop("_derived", None)
ir = from_raw(ir_raw)
world = fold_all(ir)
roles = {pp["id"]: pp["role"] for pp in ir_raw["panels"]}
netpoly = {pp["id"]: np.asarray(pp["polygon_2d"], float) for pp in ir_raw["panels"]}
solid_ids = set(mod.solid_roles()) - {"glue"}
OUT = "output/candidates/aseptic_brick_v0000/wp_a3"

# ---- 1) fold 树焊接 (同 v1.0, 已 ACCEPTED) ----
vmap = {}; pts = []
panel_net_idx = {}
for pid in world:
    ids = []
    for i, p2 in enumerate(netpoly[pid]):
        k2 = ("n", pid, round(float(p2[0]), 5), round(float(p2[1]), 5))
        if k2 not in vmap: vmap[k2] = len(pts); pts.append((0.0, 0.0, 0.0))
        ids.append(vmap[k2])
    panel_net_idx[pid] = ids
for pid, ids in panel_net_idx.items():
    wv = np.asarray(world[pid], float) * 1e-3
    for li, gi in enumerate(ids): pts[gi] = tuple(wv[li])
par = list(range(len(pts)))
def find(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
fold_meet = []
for e in ir_raw["edges"]:
    if e.get("kind") != "FOLD": continue
    p, c2 = e["fold"]["parent"], e["fold"]["child"]
    if p not in solid_ids or c2 not in solid_ids:
        continue
    ip = [int(np.argmin(np.linalg.norm(netpoly[p] - np.array(s), axis=1))) for s in e["seg_2d"]]
    ic = [int(np.argmin(np.linalg.norm(netpoly[c2] - np.array(s), axis=1))) for s in e["seg_2d"]]
    for k1, k2 in zip(ip, ic):
        a, b = find(panel_net_idx[p][k1]), find(panel_net_idx[c2][k2])
        if a != b: par[a] = b
        fold_meet.append({"relation": "FOLD_MEET", "panels": [p, c2],
                          "edge_2d": e["seg_2d"], "source": "ir.edges:FOLD"})
remap = {}; pts2 = []
for i in range(len(pts)):
    r = find(i)
    if r not in remap: remap[r] = len(pts2); pts2.append(pts[i])
loops = {pid: [remap[find(panel_net_idx[pid][i])] for i in range(len(panel_net_idx[pid]))] for pid in panel_net_idx}
uv_of = {}
uv_of_original = {}
net_all = np.vstack(list(netpoly.values())); nmin, nmax = net_all.min(0), net_all.max(0)
span = float((nmax - nmin).max())
for pid, loop in loops.items():
    for i, gi in enumerate(loop):
        p2 = netpoly[pid][i]
        uvv = ((float(p2[0]) - nmin[0]) / span, (float(p2[1]) - nmin[1]) / span)
        uv_of[gi] = uvv
        uv_of_original[(pid, i)] = uvv

# ---- 2) 封合候选发现 (L1 观测): 重合边界边对 ----
def boundary_edges(loops):
    de = {}
    for pid, loop in loops.items():
        n = len(loop)
        for i in range(n):
            u, v = loop[i], loop[(i+1) % n]
            de[(u, v)] = de.get((u, v), 0) + 1
    return [(u, v) for (u, v) in de if (v, u) not in de]
bnd = boundary_edges(loops)
P = {i: np.array(pts2[i]) for i in set(x for e in bnd for x in e)}
pairs = []
used = set()
for i, (u, v) in enumerate(bnd):
    if u in used or v in used: continue
    for (u2, v2) in bnd[i+1:]:
        if u2 in used or v2 in used: continue
        d1 = np.linalg.norm(P[u] - P[u2]); d2 = np.linalg.norm(P[v] - P[v2])
        d3 = np.linalg.norm(P[u] - P[v2]); d4 = np.linalg.norm(P[v] - P[u2])
        if max(d1, d2) < 1e-5: pairs.append((u, v, u2, v2, "fwd"))
        elif max(d3, d4) < 1e-5: pairs.append((u, v, v2, u2, "rev"))

# ---- 3) L2 分类: 面板对语义 → closure_relations 台账 ----
fam_pairs = {(frozenset(e["fold"]["parent"], e["fold"]["child"]) if False else frozenset([e["fold"]["parent"], e["fold"]["child"]])) for e in ir_raw["edges"] if e.get("kind") == "FOLD"}
ledger = []
for (u, v, u2, v2, orient) in pairs:
    # 找该边界边所属面板
    owners = []
    for pid, loop in loops.items():
        n = len(loop)
        for i in range(n):
            a, b = loop[i], loop[(i+1) % n]
            if {min(a, b), max(a, b)} == {min(u, v), max(u, v)}: owners.append(pid)
            if {min(a, b), max(a, b)} == {min(u2, v2), max(u2, v2)}: owners.append(pid)
    pset = frozenset(set(owners))
    if pset == frozenset({"glue", "front"}) or frozenset({"glue", "front"}) <= pset:
        rel, src, cond = "GLUE_BOND", "family_design:glue_flap", "glue_w>0, state=folded"
    elif pset in fam_pairs or any(pset <= fp for fp in fam_pairs):
        rel, src, cond = "FOLD_MEET", "ir.edges:FOLD", "always"
    else:
        rel, src, cond = "SEAL_MEET", "family_design:end_seal", "state=folded"
    ledger.append({"relation": rel, "panels": sorted(pset), "edge_weld": [u, v, u2, v2],
                   "orient": orient, "source": src, "condition": cond,
                   "uv_before": [round(uv_of[u][0], 4), round(uv_of[u][1], 4)],
                   "uv_conflict": None})
print("closure ledger:")
for l in ledger: print(" ", l["relation"], l["panels"], l["source"])

# ---- 4) 仅按台账焊接 + UV 冲突诊断 (封合前后) ----
uv_conflicts = []
for l in ledger:
    u, v, u2, v2 = l["edge_weld"]
    ua, ub = uv_of.get(u), uv_of.get(v)
    ua2, ub2 = uv_of.get(u2), uv_of.get(v2)
    # GLUE_BOND: 胶板与壁面的自由边在 net 上不相邻 → UV 值不同属预期 (跨材料接缝)
    # SEAL_MEET: 相遇边在 net 上亦不相邻 → UV 不同属预期
    l["uv_before"] = [round(ua[0], 4), round(ua[1], 4)] if ua else None
    l["uv_after"] = None
    if ua is not None and ua2 is not None:
        l["uv_conflict"] = bool(not np.allclose(ua, ua2, atol=1e-6) and not np.allclose(ua, ub2, atol=1e-6))
    # 焊接
    a, b = find(u), find(u2)
    if a != b: par[a] = b
    a, b = find(v), find(v2)
    if a != b: par[a] = b
# UV 前后: 焊后每焊接组内 UV 是否一致 (SEAL_MEET 期望不一致=跨接缝, GLUE_BOND 同)
remap = {}; pts2 = []
for i in range(len(pts)):
    r = find(i)
    if r not in remap: remap[r] = len(pts2); pts2.append(pts[i])
loops2 = {pid: [remap[find(panel_net_idx[pid][i])] for i in range(len(panel_net_idx[pid]))] for pid in panel_net_idx}
bnd_after = boundary_edges(loops2)
# ---- 5) 发射 + 审计 ----
face_corners = []
for pid, loop in loops2.items():
    n = len(loop)
    if n == 4: face_corners += [(loop[0], loop[1], loop[2]), (loop[0], loop[2], loop[3])]
    else: face_corners += [(loop[0], loop[i], loop[i+1]) for i in range(1, n-1)]
corner_uv = {}
for pid, loop in loops2.items():
    for i, c in enumerate(loop):
        corner_uv[(pid, i)] = uv_of_original.get((pid, i), (0.0, 0.0))
uv_final = []
for pid, loop in loops2.items():
    n = len(loop)
    if n == 4: tris = [(0, 1, 2), (0, 2, 3)]
    else: tris = [(0, i, i+1) for i in range(1, n-1)]
    for t in tris:
        for ci in t:
            uv_final.append(corner_uv.get((pid, ci), (0.0, 0.0)))
stage = Usd.Stage.CreateInMemory()
mesh = UsdGeom.Mesh.Define(stage, "/Asset/FoldedSolid")
mesh.GetPointsAttr().Set(Vt.Vec3fArray([Gf.Vec3f(*p) for p in pts2]))
mesh.GetFaceVertexCountsAttr().Set(Vt.IntArray([3]*len(face_corners)))
mesh.GetFaceVertexIndicesAttr().Set(Vt.IntArray([int(c) for t in face_corners for c in t]))
mesh.GetSubdivisionSchemeAttr().Set("none")
attr = mesh.GetPrim().CreateAttribute("primvars:st", Sdf.ValueTypeNames.TexCoord2fArray)
attr.Set(Vt.Vec2fArray([Gf.Vec2f(u[0], u[1]) for u in uv_final]))
UsdGeom.Primvar(attr).SetInterpolation(UsdGeom.Tokens.faceVarying)
stage.GetRootLayer().Export(f"{OUT}/folded_solid_ledgerweld.usdc")
r = audit_stage(Usd.Stage.Open(f"{OUT}/folded_solid_ledgerweld.usdc"), contract="SOLID")
key = list(r["L1"]["prims"].keys())[0]
R = r["L1"]["prims"][key]
ext_arr = np.asarray(pts2); ext = ext_arr.max(0) - ext_arr.min(0)
print("ledger 焊接候选: overall", r["L3"]["overall"])
print("findings:", R["findings"])
print("shells:", R["shells"])
print("boundary after ledger:", len(bnd_after))
print("bbox(m):", np.round(ext_arr, 4))
json.dump({"ledger": ledger, "boundary_after": len(bnd_after),
           "audit": {"overall": r["L3"]["overall"], "findings": R["findings"], "shells": R["shells"]},
           "bbox_m": [round(float(x), 4) for x in (ext_arr.max(0) - ext_arr.min(0))]},
          open("docs/research/evidence/wp_a11_closure_relations.json", "w"), indent=1, ensure_ascii=False)
print("closure_relations json saved")
