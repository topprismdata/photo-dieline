"""pillow_bag: 零食软袋(枕式袋)参数化资产生成器 — 货架孪生缺口工单#1.

产出(Blender headless): 一个袋体网格 + PIL 印刷 atlas + Principled 材质.
用法: blender --background --python scripts/make_pillow_bag.py -- out.png [W_mm H_mm]
设计纪律(冷柜线): 远观排面=低多边形+色块 atlas; hero 近景才上全印刷.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = Path(argv[0]) if argv else Path("/tmp/pillow_bag.png")
W_MM = float(argv[1]) if len(argv) > 1 else 140.0   # 袋宽
H_MM = float(argv[2]) if len(argv) > 2 else 200.0   # 袋高
COL = tuple(float(x) for x in argv[3].split(",")) if len(argv) > 3 else (0.85, 0.30, 0.12, 1.0)
LABEL = argv[4] if len(argv) > 4 else "TOPPRISM"    # 品名字
SUB = argv[5] if len(argv) > 5 else "零食 100g"      # 品名小注
FIN_MM = 18.0                                       # 顶/底封翘 crimp 高
DEPTH = 70.0                                        # 充气后厚度


def build_mesh():
    """枕式袋: 前后鼓面 + 顶底压翘. 细分平面沿厚度方向 inflate 成枕形."""
    import bmesh
    mesh = bpy.data.meshes.new("bag")
    bm = bmesh.new()
    w, h, dep = W_MM / 1000, H_MM / 1000, DEPTH / 1000
    fin = FIN_MM / 1000
    # 前面: 细分网格 12x16, z 向鼓起(枕形=边缘贴背, 中心鼓)
    sx, sz = 12, 16
    front = []
    for iz in range(sz + 1):
        row = []
        for ix in range(sx + 1):
            u, v = ix / sx, iz / sz
            bulge = math.sin(math.pi * u) * math.sin(math.pi * v)  # 边缘0中心1
            x = (u - 0.5) * w
            z = v * h
            y = -dep / 2 * (0.12 + 0.88 * bulge)  # 前面朝 -y 鼓
            row.append(bm.verts.new((x, y, z)))
        front.append(row)
    for iz in range(sz):
        for ix in range(sx):
            bm.faces.new((front[iz][ix], front[iz][ix + 1],
                          front[iz + 1][ix + 1], front[iz + 1][ix]))
    # 背面: 平面(贴陈列背板)
    back = [bm.verts.new(((u - 0.5) * w, dep * 0.06, v * h))
            for v in (0.0, 1.0) for u in (0.0, 1.0)]
    b0, b1, b2, b3 = back  # 左下 右下 左上 右上 顺序重排
    b0 = bm.verts.new((-w / 2, dep * 0.06, 0)); b1 = bm.verts.new((w / 2, dep * 0.06, 0))
    b2 = bm.verts.new((w / 2, dep * 0.06, h)); b3 = bm.verts.new((-w / 2, dep * 0.06, h))
    # 侧缝条(x=±w/2 窄条连前后缘)
    fe0, fe1 = front[0][0], front[0][sx]
    ft0, ft1 = front[sz][0], front[sz][sx]
    for a, bb, c, d, x in ((fe0, fe1, b1, b0, 0), (ft1, ft0, b3, b2, 1)):
        try:
            bm.faces.new((a, bb, c, d))
        except ValueError:
            pass
    # 顶/底压翘 fin: 扁平塌缩条 (crimp 锯齿用 bevel 感近似=斜切)
    for zs, zn in ((0.0, -fin), (h, h + fin)):
        c0 = bm.verts.new((-w * 0.46, dep * 0.10, zs + (0 if zs == 0 else 0) + (zn - zs) * 0.2))
        c1 = bm.verts.new((w * 0.46, dep * 0.10, zs + (zn - zs) * 0.2))
        c2 = bm.verts.new((w * 0.40, 0.0, zn))
        c3 = bm.verts.new((-w * 0.40, 0.0, zn))
        try:
            bm.faces.new((fe0 if zs == 0 else ft0, fe1 if zs == 0 else ft1, c1, c0))
            bm.faces.new((c0, c1, c2, c3))
        except ValueError:
            pass
    # UV: 前面行→atlas 全幅 (印刷主区); 其余面默认 (0,0)→用纯色象限
    uv_layer = bm.loops.layers.uv.verify()
    bm.faces.ensure_lookup_table()
    for iz in range(sz):
        for ix in range(sx):
            f = bm.faces[iz * sx + ix]  # 前面面片按创建顺序即最前
            for loop, du, dv in zip(f.loops, (0, 1, 1, 0), (0, 0, 1, 1)):
                u0 = ix / sx
                v0 = iz / sz
                loop[uv_layer].uv = (u0 + du / sx * 0.98 + 0.01,
                                     v0 + dv / sz * 0.98 + 0.01)
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("bag", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def make_atlas(path: Path):
    from PIL import Image, ImageDraw, ImageFont
    S = 512
    import colorsys
    _h, _l, _sv = colorsys.rgb_to_hsv(*[c for c in COL[:3]])
    _sv = min(1.0, _sv * 1.2)
    _r, _g, _b = colorsys.hsv_to_rgb(_h, _sv, _l)
    _col = (_r, _g, _b, 1.0)  # 局部饱和增强色 (不遮蔽全局 COL)
    im = Image.new("RGB", (S, S), tuple(int(c * 255) for c in _col[:3]))
    d = ImageDraw.Draw(im)
    # 色块主导 (对账: 排面远观读色系): 白窗收窄至 30% 居中, 顶带亮色+品字
    d.rectangle([0, 0, S, S // 5], fill=tuple(min(255, int(c * 255 + 45)) for c in _col[:3]))
    d.rounded_rectangle([S * 4 // 10, S * 9 // 20, S * 6 // 10, S * 13 // 20], radius=14, fill=(250, 248, 242))
    try:
        f = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 64, index=0)
        f2 = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 40, index=0)
    except Exception:
        f = f2 = ImageFont.load_default()
    d.text((S // 2, S * 0.55), LABEL, font=f, fill=(30, 30, 34), anchor="mm")
    d.text((S // 2, S * 0.13), SUB, font=f2, fill=(255, 255, 255), anchor="mm")
    d.text((S // 2, S * 0.12), "NEW", font=f2, fill=(255, 255, 255), anchor="mm")
    im.save(path)


def make_material(obj, atlas: Path):
    mat = bpy.data.materials.new("bagmat")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.38  # 软膜光泽
    bsdf.inputs["Alpha"].default_value = 1.0
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(atlas))
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    obj.data.materials.append(mat)


def render(obj, out: Path):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"  # Blender5.2 枚举无 _NEXT (tde pitfalls)
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"   # 默认 look 去饱和 = 洗白根因 (2026-11-21)
    sc.view_settings.exposure = -0.3
    sc.render.resolution_x = sc.render.resolution_y = 640
    sc.world = bpy.data.worlds.new("w") or sc.world
    if sc.world:
        sc.world.use_nodes = True
        sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.92, 0.92, 0.94, 1)
        sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.55
    light = bpy.data.lights.new("key", "AREA")
    light.size = 1.2; light.energy = 220
    lo = bpy.data.objects.new("key", light)
    lo.location = (0.9, -0.8, 1.0)
    lo.rotation_euler = (math.radians(55), 0, math.radians(45))
    bpy.context.collection.objects.link(lo)
    fill = bpy.data.lights.new("fill", "AREA")
    fill.size = 1.5; fill.energy = 120
    fo = bpy.data.objects.new("fill", fill)
    fo.location = (-1.0, -0.6, 0.4)
    bpy.context.collection.objects.link(fo)
    cam = bpy.data.cameras.new("c"); cam.lens = 60
    co = bpy.data.objects.new("c", cam)
    co.location = (0, -0.55, H_MM / 2000)
    co.rotation_euler = (math.radians(90), 0, 0)
    bpy.context.collection.objects.link(co)
    sc.camera = co
    sc.render.filepath = str(out)
    bpy.ops.render.render(write_still=True)


obj = build_mesh()
atlas = Path("/tmp") / "pb_atlas.png"  # 中间产物不入资产目录
make_atlas(atlas)
make_material(obj, atlas)
render(obj, OUT)
print("PILLOW_BAG_OK", OUT, W_MM, H_MM)
