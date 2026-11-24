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
    return uniq, tris_arr, nets_arr[first_idx]


def _area_mm2(pts, tris):
    v0, v1, v2 = pts[tris[:, 0]], pts[tris[:, 1]], pts[tris[:, 2]]
    return float(0.5 * np.linalg.norm(np.cross(v1 - v0, v2 - v0), axis=1).sum())


def export_usdc(ir, path, kind="carton_board", board_t_mm=0.45, texture=True, family=None):
    """IR → .usdc (+ WP2 印刷层: 净图 UV + UsdPreviewSurface 材质 + print.png)。
    返回证据 dict (含 mm 口径 authored 尺寸, 供三方对账)。"""
    import pxr  # noqa: F401  (存在性断言)
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade, Vt

    pts_mm, tris, nets_mm = _solid_triangles_mm(ir)
    if len(pts_mm) == 0 or len(tris) == 0:
        raise ValueError("solid 三角网为空")
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
    body.GetFaceVertexIndicesAttr().Set(Vt.IntArray([int(i) for t in tris for i in t]))
    body.GetFaceVertexCountsAttr().Set(Vt.IntArray([3] * len(tris)))
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
        st_vals = Vt.Vec2fArray([Gf.Vec2f(us[i], vs[i]) for t in tris for i in t])  # faceVarying 逐角
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
