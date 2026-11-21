#!/usr/bin/env python3
"""enrich_sku_usd: SKU USD 富化到官方能力清单 (对标缺口修复).

① 材质入 USD: UsdPreviewSurface + crop 贴图(assetpath 相对) + material:binding
② wikidata_qcode: Q749316 (snack, wikidata.org/wiki/Q749316 实证)
用法: python3 scripts/enrich_sku_usd.py
"""
import json
import shutil
from pathlib import Path

from pxr import Sdf, Usd, UsdGeom, UsdShade

ROOT = Path(__file__).parent.parent
USD = ROOT / "assets/sku_usd"
TEX = USD / "textures"
MANIFEST = json.loads((ROOT / "data/shelf_twin/sku_manifest.json").read_text())
QCODE = "Q749316"  # snack (Wikidata 实证)


def crop_of(sku, fams):
    """从 /tmp crop 缓存挑该 SKU 的 crop; 家族色字段在 build_hxl 场景侧,
    manifest 无 design_id → 用 family 色词匹配."""
    color = sku["family"]
    hits = sorted(Path("/tmp").glob(f"crop_{color}_*.png"))
    return hits[0] if hits else None


def enrich(f, sku):
    stage = Usd.Stage.Open(str(f))
    root = stage.GetDefaultPrim()
    # qcode (官方同款裸属性)
    a = root.CreateAttribute("semantics:labels:wikidata_qcode", Sdf.ValueTypeNames.Token)
    a.Set(QCODE)
    # 材质: UsdPreviewSurface + 贴图
    tex_src = crop_of(sku, MANIFEST.get("families", []))
    mats = UsdGeom.Scope.Define(stage, root.GetPath().AppendChild("Materials"))
    mat_path = mats.GetPath().AppendChild(f"m_{sku['id']}")
    mat = UsdShade.Material.Define(stage, mat_path)
    shader = UsdShade.Shader.Define(stage, mat_path.AppendChild("surface"))
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.55)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    surf = mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    if tex_src is not None:
        TEX.mkdir(exist_ok=True)
        dst = TEX / f"{sku['id']}.png"
        if not dst.exists():
            shutil.copy(tex_src, dst)
        texsh = UsdShade.Shader.Define(stage, mat_path.AppendChild("diffuse"))
        texsh.CreateIdAttr("UsdUVTexture")
        texsh.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(
            str(dst.relative_to(USD)))
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(
            texsh.ConnectableAPI(), "rgb")
    else:
        # barrel/box 无 crop 源: 家族色常量材质 (贴图欠账如实, 场景侧标签是程序化)
        color = {"red": (0.75, 0.15, 0.15), "orange": (0.9, 0.5, 0.1),
                 "yellow": (0.9, 0.8, 0.2), "green": (0.2, 0.65, 0.3),
                 "blue": (0.15, 0.35, 0.8), "purple": (0.5, 0.2, 0.7),
                 "gold": (0.85, 0.65, 0.2), "pink": (0.9, 0.5, 0.6),
                 "teal": (0.1, 0.6, 0.6), "white": (0.9, 0.9, 0.9),
                 "brown": (0.45, 0.3, 0.15), "dark": (0.2, 0.2, 0.25)}.get(
            sku["family"], (0.8, 0.8, 0.8))
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(color)
    # 绑定: 每个 mesh
    n = 0
    for prim in stage.TraverseAll():
        if prim.IsA(UsdGeom.Mesh):
            rel = prim.CreateRelationship("material:binding")
            rel.SetTargets([mat_path])
            n += 1
    stage.GetRootLayer().Save()
    return n, tex_src is not None


def main():
    ok, fail = 0, 0
    for f in sorted(USD.glob("*.usda")):
        sku = next(s for s in MANIFEST["skus"] if s["id"] == f.stem)
        n_mesh, has_tex = enrich(f, sku)
        ok += 1
        print(f"ENRICHED {f.stem}: meshes_bound={n_mesh} tex={'y' if has_tex else 'MISSING'}")
    print(f"ENRICH_DONE ok={ok} fail={fail}")


if __name__ == "__main__":
    main()
