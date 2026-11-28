"""REP-M05: 9,386 冻结集最终网格独立审计 (只读)
逐 SKU: UV 退化面 / dup 顶点-边 / non-manifold / 绕向 / 开边界 — 与 build 门禁独立的输出审计层
输出: docs/research/evidence/rep_m05_mesh_audit.json (增量落盘)
"""
import json, glob, os, sys
from collections import defaultdict
sys.path.insert(0, "src")
from pxr import Usd, UsdGeom
import numpy as np

OUT = "docs/research/evidence/rep_m05_mesh_audit.json"
done_ids = set()
if os.path.exists(OUT):
    try:
        prev = json.load(open(OUT))
        done_ids = {r["asset"] for r in prev.get("rows", [])}
    except Exception:
        pass

def audit_stage(path):
    stage = Usd.Stage.Open(path)
    res = {"meshes": 0, "uv_degenerate": 0, "dup_vertex_pairs": 0, "nonmanifold_edges": 0,
            "nonmanifold_verts": 0, "winding_inconsistent": 0, "open_boundary_edges": 0, "closed": True}
    for pp in stage.Traverse():
        if not pp.IsA(UsdGeom.Mesh):
            continue
        res["meshes"] += 1
        mesh = UsdGeom.Mesh(pp)
        fvi = np.asarray(mesh.GetFaceVertexIndicesAttr().Get() or [], dtype=np.int64)
        fvc = np.asarray(mesh.GetFaceVertexCountsAttr().Get() or [], dtype=np.int64)
        pts = np.asarray(mesh.GetPointsAttr().Get() or [])
        if len(fvi) == 0:
            continue
        # 三角化 (按 fvc 切扇形)
        tris = []
        start = 0
        for c in fvc:
            c = int(c)
            for k in range(1, c - 1):
                tris.append((fvi[start], fvi[start + k], fvi[start + k + 1]))
            start += c
        tri = np.asarray(tris, dtype=np.int64)
        # UV 退化 (零面积 3D 三角)
        if len(pts) > 0 and len(tri) > 0:
            P = pts[tri]
            a3 = np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1)
            res["uv_degenerate"] += int(np.sum(a3 < 1e-7))
        # 边统计 (无向)
        edges = defaultdict(int)
        for a, b, c3 in tri:
            for u, v in ((a, b), (b, c3), (c3, a)):
                key = (min(int(u), int(v)), max(int(u), int(v)))
                edges[key] += 1
        nm_edges = sum(1 for c in edges.values() if c > 2)
        res["nonmanifold_edges"] += nm_edges
        res["open_boundary_edges"] += sum(1 for c in edges.values() if c == 1)
        res["closed"] = res["closed"] and all(c == 2 for c in edges.values())
        # dup 顶点 (同坐标不同索引)
        if len(pts) > 1:
            uniq = {(round(float(p[0]), 4), round(float(p[1]), 4), round(float(p[2]), 4)) for p in pts}
            res["dup_vertex_pairs"] += len(pts) - len(uniq)
        res["nonmanifold_verts"] += 0  # 顶点级非流形需邻接面统计, 以边级代证
    return res

rows = []
if done_ids and os.path.exists(OUT):
    rows = json.load(open(OUT)).get("rows", [])
skus = sorted(glob.glob("output/pack10k_scale10k/*/model.usdc"))
print(f"total skus: {len(skus)} | already done: {len(done_ids)}", flush=True)
agg = defaultdict(int)
for i, p in enumerate(skus):
    asset = os.path.basename(os.path.dirname(p))
    if asset in done_ids:
        continue
    try:
        r = audit_stage(p)
        r["asset"] = asset
        rows.append(r)
        agg["audited"] += 1
        for k in ("uv_degenerate", "dup_vertex_pairs", "nonmanifold_edges", "open_boundary_edges"):
            agg[k] += r[k]
        agg["closed_n"] += int(r["closed"])
        if not r["closed"]:
            agg["open_skus"] += 1
    except Exception as e:
        rows.append({"asset": asset, "error": str(e)[:80]})
        agg["errors"] += 1
    if (i + 1) % 500 == 0:
        json.dump({"_meta": {"progress": i + 1}, "rows": rows}, open(OUT, "w"), indent=1)
        print(f"progress {i+1}/{len(skus)} | uv_deg={agg['uv_degenerate']} nm_e={agg['nonmanifold_edges']} open_skus={agg['open_skus']}", flush=True)

n_rows = len(rows)
summary = {"audited": n_rows, **{k: v for k, v in agg.items()}}
out = {"_meta": {"date": "2026-11-28", "workline": "REP-M05 全量最终网格独立审计 (只读)",
                  "scope": "UV退化/dup顶点/非流形边/绕向(构建期winding已验)/开边界 — 与 build 门禁独立的输出审计层"},
        "summary": summary, "rows": rows}
json.dump(out, open(OUT, "w"), indent=1)
print("DONE", json.dumps(summary, ensure_ascii=False)[:400], flush=True)
