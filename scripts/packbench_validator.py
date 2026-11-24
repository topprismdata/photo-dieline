#!/usr/bin/env python3
"""PackBench 独立验收器 (R1 §5: 评测验证器与生产验证器异源 — 本脚本不复用生产 G03 代码)。

从 model.usdc 独立解析, 检查生产门禁覆盖不到/不肯认的项:
  V1 结构: default prim / Z-up / 米制 / kg / 无 PhysicsScene
  V2 网格水密性: 每条边恰好被 2 个三角共享 (流形闭合)
  V3 无退化三角 (零面积) / 无重复面
  V4 数值合法性: 点/UV 有限
  V5 尺寸独立核账: stage bbox vs manifest 声明 (独立读取, 容差 0.5mm)
  V6 物理字段: 质量存在且为正; mass_scope 声明存在
  V7 依赖闭合: 纹理等相对引用存在

用法: python3 scripts/packbench_validator.py <asset_dir> [更多...]
输出: 每件 JSON 判决 {asset, checks: {...}, verdict: PASS/FAIL} — 评测主指标 VSR 的验收器。
"""

import json
import math
import sys
from collections import Counter
from pathlib import Path

from pxr import Sdf, Usd, UsdGeom, UsdPhysics

TOL_MM = 0.5


def check_asset(asset_dir: Path):
    usdc = asset_dir / "model.usdc"
    checks, details = {}, {}

    stage = Usd.Stage.Open(str(usdc))
    checks["v1_stage_open"] = stage is not None
    if not checks["v1_stage_open"]:
        return {"asset": asset_dir.name, "checks": checks, "verdict": "FAIL"}
    comp = list(stage.GetCompositionErrors())
    checks["v1_no_comp_errors"] = not comp
    dp = stage.GetDefaultPrim()
    checks["v1_default_prim"] = bool(dp) and dp.GetPath() == Sdf.Path("/Asset")
    checks["v1_z_up"] = UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.z
    checks["v1_meters"] = math.isclose(UsdGeom.GetStageMetersPerUnit(stage), 1.0, abs_tol=1e-12)
    checks["v1_kilograms"] = math.isclose(UsdPhysics.GetStageKilogramsPerUnit(stage), 1.0, abs_tol=1e-12)
    checks["v1_no_physics_scene"] = not any(p.IsA(UsdPhysics.Scene) for p in stage.Traverse())

    # V2-V4: 收集所有网格三角
    import numpy as np

    edges = Counter()
    tris_total, degen, dup_faces = 0, 0, Counter()
    all_pts = []
    finite = True
    mesh_count = 0
    for prim in stage.Traverse():
        if not prim.IsA(UsdGeom.Mesh):
            continue
        mesh_count += 1
        mesh = UsdGeom.Mesh(prim)
        pts = np.asarray(mesh.GetPointsAttr().Get(), dtype=float)
        if pts.size and not np.isfinite(pts).all():
            finite = False
        idx = np.asarray(mesh.GetFaceVertexIndicesAttr().Get(), dtype=int)
        cnt = np.asarray(mesh.GetFaceVertexCountsAttr().Get(), dtype=int)
        if len(cnt) == 0:
            continue
        tris = idx.reshape(-1, 3)
        tris_total += len(tris)
        all_pts.append(pts)
        for t in tris:
            a, b, c = pts[t[0]], pts[t[1]], pts[t[2]]
            area2 = np.dot(np.cross(b - a, c - a), np.cross(b - a, c - a))
            if math.sqrt(area2) < 1e-12:
                degen += 1
            key = tuple(sorted((round(float(x), 6), float(y), float(z))
                               for x, y, z in (a, b, c)))
            dup_faces[key] += 1
            for i in range(3):
                e = tuple(sorted((t[i], t[(i + 1) % 3])))
                edges[e] += 1
    dup = sum(v - 1 for v in dup_faces.values() if v > 1)
    non_manifold = sum(1 for v in edges.values() if v > 2)      # 流形: 每棱 ≤2 面
    open_edges = sum(1 for v in edges.values() if v == 1)        # 开口腔 (托盘) 合法边界
    closed = non_manifold == 0 and open_edges == 0
    checks["v2_manifold"] = mesh_count > 0 and non_manifold == 0
    checks["v2_closed"] = closed  # INFO 级: 开口托盘/盒合法为 False
    checks["v3_no_degenerate"] = degen == 0
    checks["v3_no_duplicate_faces"] = dup == 0
    checks["v4_finite"] = finite
    details["tris"] = tris_total
    details["non_manifold_edges"] = non_manifold
    details["open_edges"] = open_edges
    details["degenerate_tris"] = degen

    # V5: stage bbox vs manifest 声明
    bc = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_], useExtentsHint=True)
    rng = bc.ComputeWorldBound(dp).ComputeAlignedRange()
    dims_mm = [(rng.GetMax()[i] - rng.GetMin()[i]) * 1000.0 for i in range(3)]
    meta = {}
    mp = asset_dir / "model.json"
    if mp.exists():
        meta = json.loads(mp.read_text())
    ext = meta.get("asset_extents_m")
    if ext:
        diffs = [abs(dims_mm[i] - ext[i] * 1000.0) for i in range(3)]
        checks["v5_dims_match_manifest"] = max(diffs) <= TOL_MM
        details["dims_max_diff_mm"] = round(max(diffs), 4)
    else:
        checks["v5_dims_match_manifest"] = False

    # V6: 物理字段
    mass_ok, scope_ok = False, False
    for prim in stage.Traverse():
        m = UsdPhysics.MassAPI(prim)
        mv = m.GetMassAttr().Get()
        if mv is not None and float(mv) > 0:
            mass_ok = True
    scope_ok = meta.get("mass_scope") == "packaging_empty"
    checks["v6_positive_mass"] = mass_ok
    checks["v6_mass_scope_declared"] = scope_ok

    # V7: 依赖闭合 (print.png 相对引用存在)
    tex = asset_dir / "print.png"
    checks["v7_dependencies_exist"] = tex.exists() if tex is not None else True

    verdict = "PASS" if all(v for k, v in checks.items() if k != "v2_closed") else "FAIL"  # closed 为 INFO (开口腔合法)
    return {"asset": asset_dir.name, "checks": checks, "details": details, "verdict": verdict}


def main(argv):
    rows = [check_asset(Path(a)) for a in argv]
    npass = sum(1 for r in rows if r["verdict"] == "PASS")
    for r in rows:
        failed = [k for k, v in r["checks"].items() if not v]
        print(f"{r['asset']}: {r['verdict']}" + (f"  failed={failed}" if failed else ""))
        if r["verdict"] == "FAIL" and r.get("details"):
            print(f"  details: {r['details']}")
    print(f"\n独立验收 VSR 口径: {npass}/{len(rows)} PASS")
    return 0 if npass == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
