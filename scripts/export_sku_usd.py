#!/usr/bin/env python3
"""export_sku_usd: Blender headless 导出 14 个 SKU 资产 USD (ESR Step B ①).

用法: blender --background --python scripts/export_sku_usd.py
产出: assets/sku_usd/<id>.usda (几何 + custom props 供 usd-core 后补语义)
"""
import json
import math
from pathlib import Path

import bpy

ROOT = Path(__file__).parent.parent
MANIFEST = json.loads((ROOT / "data/shelf_twin/sku_manifest.json").read_text())
OUT = ROOT / "assets/sku_usd"
OUT.mkdir(parents=True, exist_ok=True)


def clean_scene():
    for col in (bpy.data.objects, bpy.data.meshes, bpy.data.materials):
        for x in list(col):
            col.remove(x, do_unlink=True)


def build_bag(w_m, h_m, dep_m):
    """枕式袋网格 (与 make_pillow_bag 同构): 前面鼓面+背板+侧缝+顶底压翘."""
    import bmesh
    mesh = bpy.data.meshes.new("sku")
    bm = bmesh.new()
    fin = 0.018
    sx, sz = 12, 16
    front = []
    for iz in range(sz + 1):
        row = []
        for ix in range(sx + 1):
            u, v = ix / sx, iz / sz
            bulge = math.sin(math.pi * u) * math.sin(math.pi * v)
            row.append(bm.verts.new(((u - 0.5) * w_m, -dep_m / 2 * (0.12 + 0.88 * bulge), v * h_m)))
        front.append(row)
    for iz in range(sz):
        for ix in range(sx):
            bm.faces.new((front[iz][ix], front[iz][ix + 1], front[iz + 1][ix + 1], front[iz + 1][ix]))
    b0 = bm.verts.new((-w_m / 2, dep_m * 0.06, 0)); b1 = bm.verts.new((w_m / 2, dep_m * 0.06, 0))
    b2 = bm.verts.new((w_m / 2, dep_m * 0.06, h_m)); b3 = bm.verts.new((-w_m / 2, dep_m * 0.06, h_m))
    fe0, fe1 = front[0][0], front[0][sx]
    ft0, ft1 = front[sz][0], front[sz][sx]
    for a_, b_, c_, d_ in ((fe0, fe1, b1, b0), (ft1, ft0, b3, b2)):
        try:
            bm.faces.new((a_, b_, c_, d_))
        except ValueError:
            pass
    for zs, zn in ((0.0, -fin), (h_m, h_m + fin)):
        c0 = bm.verts.new((-w_m * 0.46, dep_m * 0.10, zs + (zn - zs) * 0.2))
        c1 = bm.verts.new((w_m * 0.46, dep_m * 0.10, zs + (zn - zs) * 0.2))
        c2 = bm.verts.new((w_m * 0.40, 0.0, zn))
        c3 = bm.verts.new((-w_m * 0.40, 0.0, zn))
        try:
            bm.faces.new((fe0 if zs == 0 else ft0, fe1 if zs == 0 else ft1, c1, c0))
            bm.faces.new((c0, c1, c2, c3))
        except ValueError:
            pass
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def export(mesh, sku, dims_mm):
    obj = bpy.data.objects.new(sku["id"], mesh)
    bpy.context.collection.objects.link(obj)
    # 尺寸单源: custom props 随导出 (userProperties), usd-core 后补语义读取
    obj["sku_id"] = sku["id"]
    obj["dims_mm"] = list(dims_mm)
    obj["mass_g"] = sku["mass_g"]
    obj["material_class"] = sku["material"]
    obj["class_label"] = sku["class_label"]
    bpy.ops.wm.usd_export(filepath=str(OUT / f"{sku['id']}.usda"),
                          selected_objects_only=False, export_custom_properties=True)
    print("EXPORTED", sku["id"])


for sku in MANIFEST["skus"]:
    clean_scene()
    w, d, h = sku["dims_mm"]  # manifest: [宽, 厚/径, 高]
    if sku["type"] == "bag":
        mesh = build_bag(w / 1000, h / 1000, d / 1000)
    elif sku["type"] == "barrel":
        bpy.ops.mesh.primitive_cylinder_add(radius=w / 2000, depth=h / 1000, location=(0, 0, h / 2000))
        mesh = bpy.context.active_object.data
        mesh.name = "sku"
        bpy.context.collection.objects.unlink(bpy.context.active_object)
        export(mesh, sku, sku["dims_mm"])
        continue
    else:  # box
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, h / 2000))
        o = bpy.context.active_object
        o.scale = (w / 1000, d / 1000, h / 1000)
        mesh = o.data
        mesh.name = "sku"
        bpy.context.collection.objects.unlink(o)
        export(mesh, sku, sku["dims_mm"])
        continue
    export(mesh, sku, sku["dims_mm"])

print("SKU_USD_EXPORT_DONE", len(MANIFEST["skus"]))
