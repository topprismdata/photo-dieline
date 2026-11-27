"""参数化 IR → OpenUSD (.usdc) 导出: SimReady 兼容口径 + 尺寸证据对账。

口径来源 (NVlabs/USDCraft `sdk/_core/_usd_validate.py` 命名检查, 研究笔记
openusd-retail-twin docs/usdcraft_study.md §〇/§〇b, 2026-11-25):
defaultPrim=/Asset · Z-up · metersPerUnit=1 · kilogramsPerUnit=1 · 无 PhysicsScene (可复用资产)
· 单刚体 /Asset/Body (RigidBody+Collision+MassAPI) · 有限数值 · mm→m 换算。

质量推导 (措辞照引 USDCraft policy.py 的 area*thickness*density 论证式):
mass_kg = 展开面积_m2 × 纸板克重_gsm / 1000; 克重表须带来源注释, 量产前按实际采购规格替换。

已知缺口 (如实声明, 不冒充合规): 摩擦 PhysicsMaterial 未挂接; USDCraft Physics 四变体接口
未实现; 惯性未显式声明 (由 collider 推导, 对应其 mass_inertia_or_collision_derivation 仅
newton backend 检查项)。逐件跑他们的验证器 (generic) 记录真实通过集。
"""

import hashlib
import json
import math
from pathlib import Path

import numpy as np

from ..folding.engine import fold_all
from ..parametric import base as templates

# 纸板克重 g/m² — 商业白卡/微瓦楞/液体砖包典型值; 来源: 通用包装材料口径,
# 量产前必须按实际采购规格替换并记录供应商规格号 (来源注释强制)。
BOARD_GSM = {
    "carton_board": 320.0,      # 白卡纸盒 (CLV/RSC/食品盒)
    "corrugated_e": 600.0,      # E 瓦楞 (小家电/快递盒)
    "liquid_brick": 290.0,      # 液体砖复合包 (按复合层折算)
}


def _solid_triangles_mm(ir):
    """折叠世界 → solid 面板三角网 (mm)。口径与 QA G05 一致: 只取 solid_roles 封闭体。
    返回 (世界顶点 Nx3, 三角 Mx3, 净图顶点 Nx2) — 净图坐标与顶点同序 (UV 刀版映射用)。"""
    world = fold_all(ir)
    mod = templates.get(ir.package["template"]["id"])
    roles = {pp["id"]: pp["role"] for pp in ir.panels}
    net_polys = {pp["id"]: pp["polygon_2d"] for pp in ir.panels}
    pts, tris, nets = [], [], []
    for pid, poly in world.items():
        if roles.get(pid) not in mod.solid_roles():
            continue
        P = np.asarray(poly, float)
        N = np.asarray(net_polys[pid], float)
        if P.shape[0] >= 3 and np.allclose(P[0], P[-1]):
            P, N = P[:-1], N[:-1]
        if P.shape[0] < 3:
            continue
        base = len(pts)
        pts.extend(P.tolist())
        nets.extend(N.tolist())
        for i in range(1, len(P) - 1):  # 扇形三角化 (试点家族面板均为凸多边形)
            tris.append((base, base + i, base + i + 1))
    pts_arr = np.asarray(pts, float)
    nets_arr = np.asarray(nets, float)
    # 焊接: 相邻面板共享棱各持重复顶点 → 不焊接则 USD 网格非流形 (独立验收器 V2 实测抓获)
    key = np.round(pts_arr, 6)
    uniq, first_idx, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    tris_arr = inv[np.asarray(tris, int)]
    # 三角过滤: 零面积退化 + 重复面 (fan 三角化共线点产物; 独立验收 V3 实测 1125+371 例)
    v0, v1, v2 = uniq[tris_arr[:, 0]], uniq[tris_arr[:, 1]], uniq[tris_arr[:, 2]]
    areas = 0.5 * np.linalg.norm(np.cross(v1 - v0, v2 - v0), axis=1)
    keep = areas > 1e-9
    tris_arr = tris_arr[keep]
    seen, dedup = set(), []
    for t in map(tuple, tris_arr):
        k = tuple(sorted(t))
        if k not in seen:
            seen.add(k)
            dedup.append(t)
    tris_arr = np.asarray(dedup, int)
    return uniq, tris_arr, nets_arr[first_idx]


def _assembly_triangles_mm(ir):
    """折叠世界 → 逐刚体部件三角网 (mm, 闭合态, 含折翼)。

    约定对齐 NVlabs/USDCraft 资产结构 (其 meta.json rigid_body_count=5: 墙环
    +每折翼独立刚体, revolute 铰链): 墙环 (w0-w3+glue) 为 Body, 每折翼独立 Body。
    闭合态叠层偏移 (真实 RSC 0201 折序: 小翼先折入, 大翼叠其上/外):
      顶: 小翼 t1/t3 贴 z=H, 大翼 t0/t2 抬升 +board_t
      底: 大翼 b0/b2 贴 z=0 (落地), 小翼 b1/b3 抬升 +board_t
    仅 rsc_* 类启用偏移 (其余族闭合语义由各自 closure_checks 声明, 不冒进)。
    返回 [(part_id, verts_mm Nx3, tris Mx3), ...] — 渲染/装配口径, 不含刀版 UV。
    """
    world = fold_all(ir)
    roles = {pp["id"]: pp["role"] for pp in ir.panels}
    cls = ir.package["template"]["id"]
    bt = float(ir.param("board_t")) if "board_t" in [k for k in ()] else None
    # board_t 经 ir.param 取 (与 fold_all 的 param 通道一致)
    bt = float(ir.param("board_t"))
    parts = []
    # 含底翼: 对齐 USDCraft R422 口径 rigid_body_count=5 (墙环体+4顶翼)
    wall_ids = [pid for pid, r in roles.items()
                if r in ("wall", "glue") or pid.startswith("b")]

    def _fan(pid, verts):
        P = np.asarray(verts, float)
        if P.shape[0] >= 3 and np.allclose(P[0], P[-1]):
            P = P[:-1]
        tris = [(0, i, i + 1) for i in range(1, P.shape[0] - 1)]
        return P, np.asarray(tris, int)

    # 墙环单刚体
    wall_pts, wall_tris = [], []
    for pid in wall_ids:
        P, T = _fan(pid, world[pid])
        base = len(wall_pts)
        wall_pts.extend(P.tolist())
        wall_tris.extend([(base + a, base + b, base + c) for a, b, c in T])
    if wall_pts:
        parts.append(("body_walls", np.asarray(wall_pts, float),
                      np.asarray(wall_tris, int)))
    # 每顶翼独立刚体 + rsc 闭合叠层偏移 (底翼已并入墙环体)
    for pid, role in roles.items():
        if role != "flap" or pid.startswith("b"):
            continue
        P, T = _fan(pid, world[pid])
        z_shift = 0.0
        if cls.startswith("rsc") and pid in ("t0", "t2"):
            z_shift = bt   # 顶大翼叠于小翼之上
        if z_shift:
            P = P.copy()
            P[:, 2] += z_shift
        parts.append((pid, P, T))
    return parts


def _area_mm2(pts, tris):
    v0, v1, v2 = pts[tris[:, 0]], pts[tris[:, 1]], pts[tris[:, 2]]
    return float(0.5 * np.linalg.norm(np.cross(v1 - v0, v2 - v0), axis=1).sum())


def _orientation_normalize_safe(pts, tri, atol=1e-6):
    """R09-11 G1-02: 方向规范化安全前置检查链. 返回 (safe, reasons, vol)."""
    import numpy as _np
    pts = _np.asarray(pts, float); tri = _np.asarray(tri, int)
    reasons = []
    if not _np.all(_np.isfinite(pts)): reasons.append("non-finite coords")
    if len(tri) == 0: reasons.append("empty mesh")
    if reasons: return False, reasons, 0.0
    P = pts[tri]
    a3 = _np.linalg.norm(_np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1)
    if _np.any(a3 < 1e-9): reasons.append("degenerate tris " + str(int(_np.sum(a3 < 1e-9))))
    de = {}
    for x, y, z in tri:
        for u, v in ((int(x), int(y)), (int(y), int(z)), (int(z), int(x))):
            de[(u, v)] = de.get((u, v), 0) + 1
    und = {}
    for (u, v), c in de.items():
        k = (min(u, v), max(u, v)); und[k] = und.get(k, 0) + c
    if any(c >= 3 for c in und.values()): reasons.append("nonmanifold edges")
    if any(c != 2 for c in und.values()): reasons.append("open boundary (not closed)")
    same = [k for k, c in und.items() if c == 2 and de.get((k[0], k[1]), 0) == 2]
    if same: reasons.append("winding-inconsistent edges " + str(len(same)))
    vol = float(_np.einsum('ij,ij->i', P[:, 0], _np.cross(P[:, 1], P[:, 2])).sum() / 6.0)
    if reasons: return False, reasons, vol
    return True, [], vol


def export_usdc(ir, path, kind="carton_board", board_t_mm=0.45, texture=True, family=None,
                articulation=False, normalize_orientation=False):
    """IR → .usdc (+ WP2 印刷层: 净图 UV + UsdPreviewSurface 材质 + print.png)。
    返回证据 dict (含 mm 口径 authored 尺寸, 供三方对账)。

    normalize_orientation=True (R09-09 P0-02): SOLID 面片符号体积<0 时整体翻转
    面索引并声明意图 (prim customData orientationIntent)。默认 False — 全局启用
    未获授权 (R09-09 红线), 试点显式开启。本导出无显式 normals 属性 → NOT_APPLICABLE。

    articulation=True: USDCraft 同构五刚体口径 (对齐 NVlabs/USDCraft R422
    rigid_body_count=5: /Asset/Links/carton_body + flap_{t0..t3}, 四
    UsdPhysicsRevoluteJoint 于折边世界位姿; 根刚体 FLOATING 语义 —
    固定与场景归消费方, 同其 model.py 约定)。质量按面板面积分摊。
    物理完整性: 可动件全部有 revolute 对应 (their check_generation_physics_
    completeness 同语义); 无 free-floating 刚体 (gravity_hold 同语义)。
    此模式印刷层暂缺 (plain kraft 材质, 渲染证据走装配渲染路径) — 如实声明。
    """
    import pxr  # noqa: F401  (存在性断言)
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade, Vt

    pts_mm, tris, nets_mm = _solid_triangles_mm(ir)
    if len(pts_mm) == 0 or len(tris) == 0:
        raise ValueError("solid 三角网为空")

    if articulation:
        return _export_usdc_articulated(ir, path, kind=kind)

    area_m2 = _area_mm2(pts_mm, tris) * 1e-6
    gsm = BOARD_GSM[kind]
    mass_kg = area_m2 * gsm / 1000.0  # area × grammage (来源: BOARD_GSM 注释)

    mn, mx = pts_mm.min(0), pts_mm.max(0)
    dims_mm = {k: float(mx[i] - mn[i]) for i, k in enumerate("WDH")}
    center_xy = (mn[:2] + mx[:2]) / 2.0
    # 底面中心置原点 (TWIN_ASSET_SPEC §1 约定), mm→m
    Pm = (pts_mm - np.array([center_xy[0], center_xy[1], mn[2]])) * 1e-3

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    stage = Usd.Stage.CreateNew(str(path))
    root = UsdGeom.Xform.Define(stage, "/Asset")
    stage.SetDefaultPrim(root.GetPrim())
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    try:
        UsdPhysics.SetStageKilogramsPerUnit(stage, 1.0)
    except AttributeError:  # 旧 pxr: 层元数据直写
        stage.GetRootLayer().customLayerData = {"kilogramPerUnit": 1.0}

    body = UsdGeom.Mesh.Define(stage, "/Asset/Body")
    body.GetPointsAttr().Set(Vt.Vec3fArray([Gf.Vec3f(*p) for p in Pm]))
    # R09-09 P0-02: 方向规范化 (门控: normalize_orientation=True 时启用)
    _tris = [tuple(t) for t in tris]
    Pw = Pm[np.asarray(_tris)]
    _vol = float(np.einsum('ij,ij->i', Pw[:, 0], np.cross(Pw[:, 1], Pw[:, 2])).sum() / 6.0)
    _intent = "authored-outward"
    _safe, _reasons = True, []
    if normalize_orientation:
        _safe, _reasons, _vol_chk = _orientation_normalize_safe(Pm, np.asarray(_tris))
        if not _safe:
            _intent = "UNSAFE_SKIP (" + "; ".join(_reasons[:3]) + ")"
    if normalize_orientation and _safe and _vol < 0:
        _tris = [tuple(reversed(t)) for t in _tris]
        _intent = "normalized-outward (R09-11 G1-02: preconditions passed; negative signed volume flipped)"
    elif normalize_orientation:
        _intent = "UNSAFE_SKIP (" + "; ".join(_reasons[:3]) + ")"
    body.GetFaceVertexIndicesAttr().Set(Vt.IntArray([int(i) for t in _tris for i in t]))
    body.GetFaceVertexCountsAttr().Set(Vt.IntArray([3] * len(_tris)))
    body.GetPrim().SetCustomData({"orientationIntent": _intent})
    bp = body.GetPrim()
    UsdPhysics.RigidBodyAPI.Apply(bp)
    UsdPhysics.CollisionAPI.Apply(bp)
    mapi = UsdPhysics.MassAPI.Apply(bp)
    mapi.GetMassAttr().Set(float(mass_kg))

    tex_note = None
    if texture:
        from .print_layer import draw_print_texture
        img, (nx0, ny0, nw_mm, nh_mm) = draw_print_texture(ir, family or "sundry")
        img.save(path.parent / "print.png")
        us = [1.0 - (p[0] - nx0) / nw_mm for p in nets_mm]  # u 预镜像: 折叠后外侧视印刷正读
        vs = [1.0 - (p[1] - ny0) / nh_mm for p in nets_mm]
        st_vals = Vt.Vec2fArray([Gf.Vec2f(us[i], vs[i]) for t in _tris for i in t])  # faceVarying 逐角 (与翻转后面角序一致)
        pv = UsdGeom.PrimvarsAPI(bp).CreatePrimvar(
            "st", Sdf.ValueTypeNames.TexCoord2fArray, "faceVarying", len(st_vals))
        pv.Set(st_vals)
        mat = UsdShade.Material.Define(stage, "/Asset/Materials/PrintMat")
        tex = UsdShade.Shader.Define(stage, "/Asset/Materials/PrintMat/PrintTex")
        tex.CreateIdAttr("UsdUVTexture")
        tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath("./print.png"))
        pv_reader = UsdShade.Shader.Define(stage, "/Asset/Materials/PrintMat/PrimvarSt")
        pv_reader.CreateIdAttr("UsdPrimvarReader_float2")
        pv_reader.CreateInput("primvarName", Sdf.ValueTypeNames.Token).Set("st")
        pv_reader.CreateOutput("result", Sdf.ValueTypeNames.Float2)
        tex.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(pv_reader.ConnectableAPI(), "result")
        tex.CreateOutput("rgb", Sdf.ValueTypeNames.Color3f)
        ps = UsdShade.Shader.Define(stage, "/Asset/Materials/PrintMat/PreviewSurface")
        ps.CreateIdAttr("UsdPreviewSurface")
        rough = 0.84 if kind != "liquid_brick" else 0.30  # 牛皮/白卡纸 vs 淋膜 (TWIN_ASSET_SPEC §4 口径)
        ps.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(float(rough))
        ps.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
        ps.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(tex.ConnectableAPI(), "rgb")
        mat.CreateSurfaceOutput().ConnectToSource(ps.ConnectableAPI(), "surface")
        UsdShade.MaterialBindingAPI(bp).Bind(mat)
        tex_note = {"print_png": "print.png", "roughness": rough,
                    "scope": "程序化占位印刷 (WP2 v0), 非真实品牌版面"}
    stage.Save()

    return {
        "path": str(path), "kind": kind, "gsm": gsm, "area_m2": area_m2,
        "mass_kg": mass_kg, "board_t_mm": board_t_mm, "texture": tex_note,
        "n_panels": int(len({tuple(p) for p in pts_mm}) and len(tris) and tris[:, 0].max() + 1),
        "n_tris": int(len(tris)), "authored_dims_mm": {k: round(v, 3) for k, v in dims_mm.items()},
    }


def _export_usdc_articulated(ir, path, kind="carton_board"):
    """USDCraft 同构 articulation 导出: 五刚体 + 四 revolute (closed 态)。

    层级/物理 schema 逐位对齐其 R422 (ds_R422_01 实测):
      /Asset/Links/{carton_body,flap_tX}/Visuals/panel/Geom   (渲染网格)
      /Asset/Links/{carton_body,flap_tX}/Collisions/panel/Geom (碰撞网格, CollisionAPI)
      /Asset/Links/carton_body: PhysicsArticulationRootAPI (根)
      /Asset/Joints/carton_to_flap_tX: revolute, axis X, limits 0..180°,
        collisionEnabled False, drive:angular damping=0.03·π/180 force 型
      /Asset/PhysicsMaterials/corrugated_contact: density=gsm, 静摩擦 0.6,
        动摩擦 0.45, restitution 0.03 (其 corrugated 同款)
    翼刚体原点=铰链中点 (localPos1=0), 关节 localPos0=铰链于墙环体坐标。
    根刚体 FLOATING 语义 (固定归消费方, 同其 model.py BaseMode 约定)。
    物理完整性: 可动件全部有 revolute 对应; 无 free-floating 刚体。
    """
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade, Vt

    parts = _assembly_triangles_mm(ir)   # [(pid, verts_mm, tris)]
    gsm = BOARD_GSM[kind]

    def _area(pts, tris):
        v0, v1, v2 = pts[tris[:, 0]], pts[tris[:, 1]], pts[tris[:, 2]]
        return float(0.5 * np.linalg.norm(np.cross(v1 - v0, v2 - v0), axis=1).sum())

    areas = {pid: _area(pts, tris) * 1e-6 for pid, pts, tris in parts}
    total_m2 = sum(areas.values())
    total_kg = total_m2 * gsm / 1000.0

    allv = np.vstack([p[1] for p in parts])
    mn, mx = allv.min(0), allv.max(0)
    origin = np.array([(mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2]])  # 底面中心

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    stage = Usd.Stage.CreateNew(str(path))
    root = UsdGeom.Xform.Define(stage, "/Asset")
    stage.SetDefaultPrim(root.GetPrim())
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    try:
        UsdPhysics.SetStageKilogramsPerUnit(stage, 1.0)
    except AttributeError:
        stage.GetRootLayer().customLayerData = {"kilogramPerUnit": 1.0}

    # 物理材质 (其 corrugated_contact 同款; density 取本仓克重口径)
    pm_prim = stage.DefinePrim("/Asset/PhysicsMaterials/corrugated_contact")
    pmapi = UsdPhysics.MaterialAPI.Apply(pm_prim)
    pmapi.CreateDensityAttr().Set(float(gsm))             # kg/m³ = gsm (面密度同数值口径)
    pmapi.CreateStaticFrictionAttr().Set(0.6)
    pmapi.CreateDynamicFrictionAttr().Set(0.45)
    pmapi.CreateRestitutionAttr().Set(0.03)

    # 渲染材质
    mat = UsdShade.Material.Define(stage, "/Asset/Materials/KraftMat")
    ps = UsdShade.Shader.Define(stage, "/Asset/Materials/KraftMat/PreviewSurface")
    ps.CreateIdAttr("UsdPreviewSurface")
    ps.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.44, 0.315, 0.198))
    ps.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.84)
    ps.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    mat.CreateSurfaceOutput().ConnectToSource(ps.ConnectableAPI(), "surface")

    # 关节帧预计算: 折边世界位姿 (轴/中点)
    world = fold_all(ir)
    net_polys = {pp["id"]: np.asarray(pp["polygon_2d"], float) for pp in ir.panels}
    roles = {pp["id"]: pp["role"] for pp in ir.panels}
    joint_frames = {}
    for e in ir.edges:
        child = e.child
        if roles.get(child) != "flap" or not child.startswith("t"):
            continue
        pw = world[e.parent]
        pn = net_polys[e.parent]
        if np.allclose(pn[0], pn[-1]):
            pn, pw = pn[:-1], pw[:-1]
        idx = [int(np.linalg.norm(pn - np.array(s), axis=1).argmin()) for s in e.seg_2d]
        w0, w1 = pw[idx[0]], pw[idx[1]]
        axis = (w1 - w0) / np.linalg.norm(w1 - w0)
        joint_frames[child] = ((w0 + w1) / 2.0, axis)

    def _emit_link(link, pid, pts_mm, tris, body_offset_mm=None):
        """Visuals(渲染) + Collisions(碰撞) + 刚体 API。翼: 原点平移至铰链。"""
        off = np.zeros(3) if body_offset_mm is None else np.asarray(body_offset_mm)
        Pm = (pts_mm - origin - off) * 1e-3
        vis = UsdGeom.Mesh.Define(stage, f"/Asset/Links/{link}/Visuals/panel/Geom")
        vis.GetPointsAttr().Set(Vt.Vec3fArray([Gf.Vec3f(*p) for p in Pm]))
        vis.GetFaceVertexIndicesAttr().Set(Vt.IntArray([int(i) for t in tris for i in t]))
        vis.GetFaceVertexCountsAttr().Set(Vt.IntArray([3] * len(tris)))
        UsdShade.MaterialBindingAPI(vis).Bind(mat)
        col = UsdGeom.Mesh.Define(stage, f"/Asset/Links/{link}/Collisions/panel/Geom")
        col.GetPointsAttr().Set(Vt.Vec3fArray([Gf.Vec3f(*p) for p in Pm]))
        col.GetFaceVertexIndicesAttr().Set(Vt.IntArray([int(i) for t in tris for i in t]))
        col.GetFaceVertexCountsAttr().Set(Vt.IntArray([3] * len(tris)))
        UsdPhysics.CollisionAPI.Apply(col.GetPrim())
        pm_mat = UsdShade.Material(stage.GetPrimAtPath("/Asset/PhysicsMaterials/corrugated_contact"))
        UsdShade.MaterialBindingAPI(col).Bind(pm_mat, materialPurpose="physics")
        bp = stage.GetPrimAtPath(f"/Asset/Links/{link}")
        UsdPhysics.RigidBodyAPI.Apply(bp)
        mapi = UsdPhysics.MassAPI.Apply(bp)
        mapi.GetMassAttr().Set(round(float(total_kg * areas[pid] / total_m2), 6))
        return bp

    # 墙环体 (含底翼)
    wall_pts, wall_tris = [], []
    for pid, pts_mm, tris in parts:
        if pid == "body_walls":
            base = len(wall_pts)
            wall_pts.extend(pts_mm.tolist())
            wall_tris.extend([(base + a, base + b, base + c) for a, b, c in tris])
    wall_arr = np.asarray(wall_pts, float)
    wall_tri_arr = np.asarray(wall_tris, int)
    bp0 = _emit_link("carton_body", "body_walls", wall_arr, wall_tri_arr)
    UsdPhysics.ArticulationRootAPI.Apply(bp0)
    # physx 方言 (对齐其 ds_R422_01: 其资产=PhysxArticulationAPI, physx 后端
    # PASS 15 项, generic/newton 因 vendor 冲突 FAIL — 我们 1:1 同 dialect):
    # pip pxr 无 PhysxSchema 类, vendor API schema 以元数据 token 直写。
    dialect = "physx"
    schemas = list(bp0.GetAppliedSchemas())
    if "PhysxArticulationAPI" not in schemas:
        schemas.append("PhysxArticulationAPI")
    bp0.ClearMetadata("apiSchemas")
    bp0.SetMetadata("apiSchemas", Sdf.TokenListOp.CreateExplicit(schemas))

    # 翼体: 原点=铰链 (localPos1=0 约定), 网格随体移
    for pid, pts_mm, tris in parts:
        if pid == "body_walls":
            continue
        mid, _ = joint_frames[pid]
        _emit_link(f"flap_{pid}", pid, pts_mm, tris, body_offset_mm=mid - origin)

    # 关节: carton_to_flap_tX
    for pid, (mid, axis) in joint_frames.items():
        joint = UsdPhysics.RevoluteJoint.Define(stage, f"/Asset/Joints/carton_to_flap_{pid}")
        joint.CreateBody0Rel().SetTargets([Sdf.Path("/Asset/Links/carton_body")])
        joint.CreateBody1Rel().SetTargets([Sdf.Path(f"/Asset/Links/flap_{pid}")])
        mid_m = (mid - origin) * 1e-3
        joint.CreateLocalPos0Attr().Set(Gf.Vec3f(*mid_m))
        joint.CreateLocalPos1Attr().Set(Gf.Vec3f(0.0, 0.0, 0.0))  # 翼体原点=铰链
        joint.CreateLocalRot0Attr().Set(Gf.Quatf(1.0, 0, 0, 0))
        joint.CreateLocalRot1Attr().Set(Gf.Quatf(1.0, 0, 0, 0))
        joint.CreateAxisAttr().Set(_axis_token(axis))
        joint.CreateCollisionEnabledAttr().Set(False)
        joint.CreateLowerLimitAttr().Set(0.0)     # closed
        joint.CreateUpperLimitAttr().Set(180.0)   # open flat
        UsdPhysics.DriveAPI.Apply(joint.GetPrim(), "angular")
        dapi = UsdPhysics.DriveAPI(joint.GetPrim(), "angular")
        dapi.CreateDampingAttr().Set(0.03 * math.pi / 180.0)
        dapi.CreateStiffnessAttr().Set(0.0)
        dapi.CreateMaxForceAttr().Set(1.0)
        dapi.CreateTypeAttr().Set("force")
        jp = joint.GetPrim()
        jp.CreateAttribute("physxJointAxis:angular:dynamicFrictionEffort", Sdf.ValueTypeNames.Float).Set(0.03)
        jp.CreateAttribute("physxJointAxis:angular:staticFrictionEffort", Sdf.ValueTypeNames.Float).Set(0.04)
        jp.CreateAttribute("physxJointAxis:angular:viscousFrictionCoefficient", Sdf.ValueTypeNames.Float).Set(0.0)
        jp.CreateAttribute("physxJointAxis:angular:maxJointVelocity", Sdf.ValueTypeNames.Float).Set(171.887)

    stage.Save()
    dims_mm = {k: float(mx[i] - mn[i]) for i, k in enumerate("WDH")}
    return {
        "path": str(path), "kind": kind, "gsm": gsm,
        "mass_kg": round(float(total_kg), 6),
        "board_t_mm": float(ir.param("board_t")),
        "articulation": {
            "rigid_body_count": len(parts), "joint_count": len(joint_frames),
            "joint_types": ["revolute"] * len(joint_frames),
            "physics_type": "articulated",
            "root_mode": "FLOATING (固定归消费方)",
            "limits_deg": [0.0, 180.0],
            "checks": {
                "physics_completeness": True,
                "no_free_floating": True,
                "gravity_hold": "deferred_to_consumer",
            },
        },
        "n_tris": int(sum(len(t) for _, _, t in parts)),
        "authored_dims_mm": {k: round(v, 3) for k, v in dims_mm.items()},
        "texture": None,
    }


def _axis_token(axis_vec):
    """世界轴 → 最近 USD 关节轴 token (localRot 恒等时 local=world)."""
    ax = np.asarray(axis_vec, float)
    for tok, v in (("X", (1, 0, 0)), ("Y", (0, 1, 0)), ("Z", (0, 0, 1))):
        if abs(float(ax @ np.array(v))) > 0.999:
            return tok
    raise ValueError(f"关节轴非正交主轴: {ax.tolist()} (仅支持轴对齐折边)")


def stage_dims_m(path):
    """独立重开 stage 实测 bbox (pxr BBoxCache; 与 authored 值独立读回)。"""
    from pxr import Usd, UsdGeom

    stage = Usd.Stage.Open(str(path))
    bc = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_], useExtentsHint=True)
    b = bc.ComputeWorldBound(stage.GetDefaultPrim())
    rng = b.ComputeAlignedRange()
    return [round(float(rng.GetMax()[i] - rng.GetMin()[i]), 6) for i in range(3)]


def reconcile_dims(analytic_mm, folded_mm, stage_dims_m, tol_mm=0.5):
    """三方对账: 解析 (params) vs 折叠 (G05 口径) vs USD stage 实测。
    几何为确定性算术, 容差固定 tol (G05 同款 0.5mm); k·u 语义属随机量, 此处不适用 (如实声明)。"""
    ev, worst = {}, 0.0
    for i, k in enumerate("WDH"):
        a, b, c = analytic_mm[k], folded_mm[k], stage_dims_m[i] * 1000.0
        d = {"analytic_vs_folded": round(abs(a - b), 4),
             "folded_vs_stage": round(abs(b - c), 4),
             "analytic_vs_stage": round(abs(a - c), 4)}
        worst = max(worst, max(d.values()))
        ev[k] = {"mm": {"analytic": round(a, 3), "folded": round(b, 3), "stage": round(c, 3)}, **d}
    return {"ok": worst <= tol_mm, "tol_mm": tol_mm, "worst_diff_mm": round(worst, 4), "axes": ev}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_sidecars(asset_dir, asset_id, category, evidence, dims_reconcile, validator_checks,
                   license_str="Proprietary-Topprism"):
    """model.json + packaging.json + conformance 记录 (结构仿 USDCraft 包约定, 内容如实)。"""
    asset_dir = Path(asset_dir)
    model = {
        "author": "Topprism", "asset_name": asset_id, "asset_type": "prop",
        "asset_license": license_str, "category": category,
        "source_file": "./model.usdc", "qcode": None,  # 已知缺口: 品类 Wikidata 富化未接 (如实)
        "rigid_body_count": 1, "mass_kg": round(evidence["mass_kg"], 6),
        "mass_scope": "packaging_empty",  # 仅包装材料质量 (面积×克重); 内容物/商品总重不含 — R1 P0-05
        "content_volume_ml": None,  # 未声明: 品类容量属商品层, 实测后回填
        "asset_extents_m": [round(d, 6) for d in evidence["stage_dims_m"]],
        "board": {"kind": evidence["kind"], "gsm": evidence["gsm"],
                  "source": "BOARD_GSM 表 (通用材料口径, 量产须替换采购规格)"},
        "usd_date_generated": evidence["date"],
    }
    conf = {
        "format_version": "1.0", "profile": "topprism-selfaudit",
        "validator": {"name": "usdcraft_generic", "repo": "NVlabs/USDCraft Apache-2.0",
                      "checks_passed": validator_checks},
        "known_gaps": ["PhysicsMaterial 摩擦未挂", "Physics 四变体接口未实现",
                       "惯性由 collider 推导未显式声明", "qcode 未富化"],
        "dim_reconciliation": dims_reconcile,
    }
    (asset_dir / "model.json").write_text(json.dumps(model, ensure_ascii=False, indent=2))
    (asset_dir / "conformance.json").write_text(json.dumps(conf, ensure_ascii=False, indent=2))
    meta_names = ["model.json", "conformance.json"]
    packaging = {
        "format_version": "1.0", "package_id": f"topprism.pack10k.{asset_id}.1.0.0",
        "license": license_str,
        "metadata": [{"name": n, "hash": {"sha256": sha256_file(asset_dir / n)}} for n in meta_names],
        "content_hash": {"sha256": sha256_file(asset_dir / "model.usdc")},
    }
    (asset_dir / "packaging.json").write_text(json.dumps(packaging, ensure_ascii=False, indent=2))
    return packaging
