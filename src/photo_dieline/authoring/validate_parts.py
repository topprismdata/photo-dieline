"""Author 合同 compile 期门禁 (G-F1..G-F7) + 部件→usdc 导出。

对齐 NVlabs/USDCraft 作者模式: Author (外部 LLM) 产 mesh-path 家族模块,
本模块做 compile 期验证, 失败回注。2026-11-25。
"""
from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np

MATERIALS = {
    "paper_kraft", "paper_white", "glass_clear", "metal_alu", "metal_steel",
    "plastic_pp", "plastic_pet_clear", "plastic_hdpe", "wood_pine",
    "ceramic_gloss", "tape_craft", "label_paper", "foil_lid",
}
# kg/m³ (通用工程口径, 量产按实测替换)
DENSITY = {
    "paper_kraft": 700.0, "paper_white": 800.0, "glass_clear": 2500.0,
    "metal_alu": 2700.0, "metal_steel": 7850.0, "plastic_pp": 905.0,
    "plastic_pet_clear": 1380.0, "plastic_hdpe": 960.0, "wood_pine": 500.0,
    "ceramic_gloss": 2400.0, "tape_craft": 800.0, "label_paper": 80.0,
    "foil_lid": 150.0,
}


def load_family(path: str | Path):
    spec = importlib.util.spec_from_file_location("author_family", str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["author_family"] = mod
    spec.loader.exec_module(mod)
    return mod


def _volume_mm3(pts: np.ndarray, tris: np.ndarray) -> float:
    """有向体积 (封闭网格 → 正值; 顶点顺序任意时取 abs)。"""
    v0, v1, v2 = pts[tris[:, 0]], pts[tris[:, 1]], pts[tris[:, 2]]
    return float(np.abs(np.einsum("ij,ij->i", v0, np.cross(v1, v2)).sum()) / 6.0)


def validate_parts(parts: list[dict], params: dict, family: str) -> dict:
    """G-F1..G-F7。返回 {ok, fails: [(gate, detail)], mass_kg, dims_mm}。"""
    fails: list[tuple[str, str]] = []
    names = set()
    all_pts = []
    for part in parts:
        pts = np.asarray(part["verts_mm"], float)
        tris = np.asarray(part["tris"], int)
        name = part["name"]
        names.add(name)
        all_pts.append(pts)
        # G-F1 finite
        if not np.all(np.isfinite(pts)):
            fails.append(("G-F1", f"{name}: 非有限顶点"))
            continue
        # G-F2 manifold (有向边计数)
        if len(tris) == 0 or tris.max() >= len(pts) or tris.min() < 0:
            fails.append(("G-F2", f"{name}: 三角索引越界"))
            continue
        edges: dict[tuple[int, int], int] = {}
        for a, b, c in tris:
            for e in ((a, b), (b, c), (c, a)):
                key = tuple(sorted(e))
                edges[key] = edges.get(key, 0) + 1
        bad = sum(1 for v in edges.values() if v != 2)
        if bad:
            fails.append(("G-F2", f"{name}: {bad} 条边非两次共享 (开放/重复面)"))
        # G-F5 material
        if part.get("material_id") not in MATERIALS:
            fails.append(("G-F5", f"{name}: material_id {part.get('material_id')!r} 不在库"))
    allp = np.vstack(all_pts)
    # G-F3 grounded
    zmin = float(allp[:, 2].min())
    if abs(zmin) > 0.5:
        fails.append(("G-F3", f"底面 z={zmin:.3f}mm ≠ 0"))
    dims = {k: float(v) for k, v in zip("XYZ", allp.max(0) - allp.min(0))}
    # G-F4 dims (参数声明 H/D 时)
    for key, idx in (("H", 2), ("D", 1)):
        if key in params and params[key] and abs(dims["XYZ"[idx]] - float(params[key])) > max(1.0, 0.01 * float(params[key])):
            fails.append(("G-F4", f"{key}: 实测 {dims['XYZ'[idx]]:.1f}mm vs 声明 {params[key]}mm"))
    # G-F6 joints
    for part in parts:
        j = part.get("joint")
        if j is None:
            continue
        if j.get("parent") not in names:
            fails.append(("G-F6", f"{part['name']}: joint.parent {j.get('parent')!r} 不存在"))
            continue
        ax = np.asarray(j["axis"], float)
        n = float(np.linalg.norm(ax))
        if abs(n - 1.0) > 1e-6:
            fails.append(("G-F6", f"{part['name']}: joint.axis 非单位向量 {ax.tolist()}"))
            continue
        if abs(ax[int(np.argmax(np.abs(ax)))]) < 0.999:
            fails.append(("G-F6", f"{part['name']}: joint.axis 非主轴对齐 {ax.tolist()}"))
        ppts = np.asarray(next(p["verts_mm"] for p in parts if p["name"] == j["parent"]), float)
        o = np.asarray(j["origin"], float)
        lo, hi = ppts.min(0), ppts.max(0)
        if np.any(o < lo - 1.0) or np.any(o > hi + 1.0):
            fails.append(("G-F6", f"{part['name']}: joint.origin 不在 parent bbox 内"))
    # G-F7 家族语义
    fails.extend(_family_semantics(parts, family))

    mass_kg = 0.0
    for part in parts:
        pts = np.asarray(part["verts_mm"], float)
        tris = np.asarray(part["tris"], int)
        vol_m3 = _volume_mm3(pts, tris) * 1e-9
        mass_kg += vol_m3 * DENSITY.get(part.get("material_id", ""), 700.0)

    return {
        "ok": not fails,
        "fails": fails,
        "mass_kg": round(mass_kg, 6),
        "dims_mm": {k: round(v, 2) for k, v in dims.items()},
        "n_parts": len(parts),
        "n_tris": int(sum(len(p["tris"]) for p in parts)),
    }


def _family_semantics(parts: list[dict], family: str) -> list[tuple[str, str]]:
    fails: list[tuple[str, str]] = []
    if family == "bottle":
        # 轴对称: 所有部件质心轴 ≈ Z (x,y 质心 ~0)
        for part in parts:
            pts = np.asarray(part["verts_mm"], float)
            c = pts.mean(0)
            if math.hypot(c[0], c[1]) > 8.0:
                fails.append(("G-F7", f"bottle/{part['name']}: 质心偏轴 {math.hypot(c[0], c[1]):.1f}mm (须回转体)"))
        # 有 cork/塞类部件
        if not any("cork" in p["name"] or "stopper" in p["name"] or "cap" in p["name"] for p in parts):
            fails.append(("G-F7", "bottle: 缺瓶塞/瓶盖部件"))
    elif family == "can":
        tab = [p for p in parts if "tab" in p["name"] or "pull" in p["name"]]
        if not tab:
            fails.append(("G-F7", "can: 缺拉环部件"))
        else:
            j = tab[0].get("joint")
            if j is None or int(np.argmax(np.abs(j["axis"]))) != 2:
                fails.append(("G-F7", "can: 拉环 joint 须绕 Z 轴"))
    elif family == "hinged_box":
        lid = [p for p in parts if "lid" in p["name"]]
        if not lid:
            fails.append(("G-F7", "hinged_box: 缺 lid 部件"))
        elif lid[0].get("joint") is None:
            fails.append(("G-F7", "hinged_box: lid 须带 revolute joint"))
        else:
            ax = np.asarray(lid[0]["joint"]["axis"], float)
            if int(np.argmax(np.abs(ax))) != 0:
                fails.append(("G-F7", "hinged_box: 铰链轴须沿 X (背缘)"))
    return fails


def export_parts_usdc(parts: list[dict], path: str | Path, mass_kg: float,
                      family: str) -> dict:
    """部件 → usdc (physx 方言, 与 USDCraft R422 同构): Links/Visuals+Collisions,
    PhysicsMaterial per material_id, joints 按部件 joint spec。"""
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade, Vt

    allp = np.vstack([np.asarray(p["verts_mm"], float) for p in parts])
    mn, mx = allp.min(0), allp.max(0)
    origin = np.array([(mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2]])

    stage = Usd.Stage.CreateNew(str(Path(path)))
    root = UsdGeom.Xform.Define(stage, "/Asset")
    stage.SetDefaultPrim(root.GetPrim())
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdPhysics.SetStageKilogramsPerUnit(stage, 1.0)

    # 材质: 渲染 (UsdPreviewSurface 按库) + 物理 (MaterialAPI 按 density)
    mat_paths = {}
    _USD_PARAMS = {
        "glass_clear": ((0.62, 0.74, 0.68), 0.02, 0.0, 0.92),
        "metal_alu": ((0.91, 0.92, 0.92), 0.25, 1.0, 0.0),
        "metal_steel": ((0.77, 0.78, 0.78), 0.3, 1.0, 0.0),
        "plastic_pp": ((0.85, 0.86, 0.84), 0.38, 0.0, 0.0),
        "plastic_pet_clear": ((0.9, 0.94, 0.95), 0.08, 0.0, 1.0),
        "plastic_hdpe": ((0.86, 0.86, 0.84), 0.45, 0.0, 0.0),
        "wood_pine": ((0.72, 0.56, 0.36), 0.6, 0.0, 0.0),
        "ceramic_gloss": ((0.92, 0.92, 0.9), 0.1, 0.0, 0.0),
        "paper_kraft": ((0.44, 0.315, 0.198), 0.84, 0.0, 0.0),
        "paper_white": ((0.9, 0.9, 0.88), 0.8, 0.0, 0.0),
        "tape_craft": ((0.62, 0.52, 0.38), 0.5, 0.0, 0.0),
        "label_paper": ((0.92, 0.92, 0.9), 0.7, 0.0, 0.0),
        "foil_lid": ((0.85, 0.86, 0.88), 0.2, 1.0, 0.0),
    }
    for mid, (rgb, rough, metallic, transmission) in _USD_PARAMS.items():
        m = UsdShade.Material.Define(stage, f"/Asset/Materials/{mid}")
        s = UsdShade.Shader.Define(stage, f"/Asset/Materials/{mid}/PreviewSurface")
        s.CreateIdAttr("UsdPreviewSurface")
        s.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*rgb))
        s.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(rough)
        s.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(metallic)
        if transmission:
            s.CreateInput("transmission", Sdf.ValueTypeNames.Float).Set(transmission)
            s.CreateInput("ior", Sdf.ValueTypeNames.Float).Set(1.5)
            s.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(0.35)
        m.CreateSurfaceOutput().ConnectToSource(s.ConnectableAPI(), "surface")
        mat_paths[mid] = f"/Asset/Materials/{mid}"
        pm = stage.DefinePrim(f"/Asset/PhysicsMaterials/{mid}")
        UsdPhysics.MaterialAPI.Apply(pm)
        UsdPhysics.MaterialAPI(pm).CreateDensityAttr().Set(float(DENSITY[mid]))
        UsdPhysics.MaterialAPI(pm).CreateStaticFrictionAttr().Set(0.6)
        UsdPhysics.MaterialAPI(pm).CreateDynamicFrictionAttr().Set(0.45)
        UsdPhysics.MaterialAPI(pm).CreateRestitutionAttr().Set(0.03)

    body_paths = {}
    total_vol = sum(_volume_mm3(np.asarray(p["verts_mm"], float),
                                np.asarray(p["tris"], int)) * 1e-9 for p in parts)
    root_prim = None
    for part in parts:
        pts = (np.asarray(part["verts_mm"], float) - origin) * 1e-3
        tris = np.asarray(part["tris"], int)
        link = part["name"]
        vol_m3 = _volume_mm3(np.asarray(part["verts_mm"], float), tris) * 1e-9
        share = vol_m3 / total_vol if total_vol else 1.0 / len(parts)
        vis = UsdGeom.Mesh.Define(stage, f"/Asset/Links/{link}/Visuals/panel/Geom")
        vis.GetPointsAttr().Set(Vt.Vec3fArray([Gf.Vec3f(*p) for p in pts]))
        vis.GetFaceVertexIndicesAttr().Set(Vt.IntArray([int(i) for t in tris for i in t]))
        vis.GetFaceVertexCountsAttr().Set(Vt.IntArray([3] * len(tris)))
        vm = UsdShade.Material(stage.GetPrimAtPath(mat_paths[part["material_id"]]))
        UsdShade.MaterialBindingAPI(vis).Bind(vm)
        col = UsdGeom.Mesh.Define(stage, f"/Asset/Links/{link}/Collisions/panel/Geom")
        col.GetPointsAttr().Set(Vt.Vec3fArray([Gf.Vec3f(*p) for p in pts]))
        col.GetFaceVertexIndicesAttr().Set(Vt.IntArray([int(i) for t in tris for i in t]))
        col.GetFaceVertexCountsAttr().Set(Vt.IntArray([3] * len(tris)))
        UsdPhysics.CollisionAPI.Apply(col.GetPrim())
        pm_mat = UsdShade.Material(stage.GetPrimAtPath(
            f"/Asset/PhysicsMaterials/{part['material_id']}"))
        UsdShade.MaterialBindingAPI(col).Bind(pm_mat, materialPurpose="physics")
        bp = stage.GetPrimAtPath(f"/Asset/Links/{link}")
        UsdPhysics.RigidBodyAPI.Apply(bp)
        mapi = UsdPhysics.MassAPI.Apply(bp)
        mapi.GetMassAttr().Set(round(float(mass_kg * share), 6))
        body_paths[link] = f"/Asset/Links/{link}"

    n_joints = 0
    for part in parts:
        j = part.get("joint")
        if j is None:
            continue
        axis = np.asarray(j["axis"], float)
        tok = ("X", "Y", "Z")[int(np.argmax(np.abs(axis)))]
        jt = UsdPhysics.RevoluteJoint.Define(stage, f"/Asset/Joints/{part['name']}_j")
        jt.CreateBody0Rel().SetTargets([Sdf.Path(body_paths[j["parent"]])])
        jt.CreateBody1Rel().SetTargets([Sdf.Path(body_paths[part["name"]])])
        o_m = (np.asarray(j["origin"], float) - origin) * 1e-3
        jt.CreateLocalPos0Attr().Set(Gf.Vec3f(*o_m))
        jt.CreateLocalPos1Attr().Set(Gf.Vec3f(0.0, 0.0, 0.0))
        jt.CreateLocalRot0Attr().Set(Gf.Quatf(1.0, 0, 0, 0))
        jt.CreateLocalRot1Attr().Set(Gf.Quatf(1.0, 0, 0, 0))
        jt.CreateAxisAttr().Set(tok)
        jt.CreateCollisionEnabledAttr().Set(False)
        jt.CreateLowerLimitAttr().Set(float(j["limits_deg"][0]))
        jt.CreateUpperLimitAttr().Set(float(j["limits_deg"][1]))
        UsdPhysics.DriveAPI.Apply(jt.GetPrim(), "angular")
        dapi = UsdPhysics.DriveAPI(jt.GetPrim(), "angular")
        dapi.CreateDampingAttr().Set(0.03 * math.pi / 180.0)
        dapi.CreateStiffnessAttr().Set(0.0)
        dapi.CreateMaxForceAttr().Set(1.0)
        dapi.CreateTypeAttr().Set("force")
        n_joints += 1

    # 根: 关节连通分量的根 (parent 集合 − 子集合); 无关节 → 不挂 root
    # (静态刚体对齐其 static_rigid 类; 铰接体对齐其 articulated 类)
    joint_children = {part["name"] for part in parts if part.get("joint")}
    root_name = next((p["name"] for p in parts
                      if p["name"] in {j.get("parent") for j in (q.get("joint") for q in parts) if j}
                      and p["name"] not in joint_children), None)
    if root_name is not None and n_joints > 0:
        root_prim = stage.GetPrimAtPath(body_paths[root_name])
        UsdPhysics.ArticulationRootAPI.Apply(root_prim)
        schemas = list(root_prim.GetAppliedSchemas())
        if "PhysxArticulationAPI" not in schemas:
            schemas.append("PhysxArticulationAPI")
        root_prim.ClearMetadata("apiSchemas")
        root_prim.SetMetadata("apiSchemas", Sdf.TokenListOp.CreateExplicit(schemas))

    stage.Save()
    return {
        "path": str(path), "n_parts": len(parts), "n_joints": n_joints,
        "mass_kg": round(mass_kg, 6),
        "dims_m": [round(float(v), 6) for v in (mx - mn) * 1e-3],
        "root": str(root_prim.GetPath()) if root_prim is not None else None,
    }
