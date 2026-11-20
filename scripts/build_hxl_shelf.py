"""build_hxl_shelf: 好想来式背光墙货架段 v1 — 场景/排面/灯光/人位相机一体化.

对账依据: docs/shelf_twin/RECONCILIATION.md v2 (primary.jpg 7 维真值).
用法: blender --background --python scripts/build_hxl_shelf.py -- out.png
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = Path(argv[0]) if argv else Path("/tmp/hxl_v1.png")
ROOT = Path("/Users/guohongbin/photo-dieline")

# ---- 场景参数 (对账 v2) ----
SHELVES, LEVEL_H, SHELF_W, DEPTH = 7, 0.38, 2.4, 0.40
BAGS_PER_LEVEL = 10
ASSETS = sorted((ROOT / "assets/pillow_bags").glob("*.png"))
# 每层色系主块 (对账: 逐层色系分块) — 索引进 ASSETS 排序
LEVEL_PLAN = [
    ["yellow", "gold"],                 # L1 黄系
    ["brown", "gold", "white"],         # L2 棕金
    ["blue", "teal", "white"],          # L3 蓝青
    ["green", "teal"],                  # L4 绿系
    ["red", "orange", "pink"],          # L5 红橙
    ["purple", "pink", "dark"],         # L6 紫粉
    ["yellow", "orange", "red"],        # L7 顶混暖
]


def pil_tex_backwall():
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (512, 512), (248, 246, 240))
    d = ImageDraw.Draw(im)
    for y in range(7):
        d.rectangle([0, y*73, 511, y*73+6], fill=(225, 222, 214))
    p = Path("/tmp/hxl_backwall.png"); im.save(p); return p


def pil_tex_floor():
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (1024, 1024), (176, 178, 182))
    d = ImageDraw.Draw(im)
    for y in range(8):
        for x in range(8):
            if (x + y) % 2 == 0:
                d.rectangle([x*128, y*128, (x+1)*128-2, (y+1)*128-2], fill=(196, 198, 202))
    p = Path("/tmp/hxl_floor.png"); im.save(p); return p


def pil_tex_sign():
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (2048, 320), (196, 30, 38))
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 150, index=0)
        f2 = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 70, index=0)
    except Exception:
        f = f2 = ImageFont.load_default()
    d.text((80, 160), "好想来", font=f, fill=(255, 255, 255), anchor="lm")
    d.text((760, 160), "品牌零食", font=f, fill=(255, 220, 80), anchor="lm")
    d.text((1340, 160), "一件也是批发价", font=f2, fill=(255, 255, 255), anchor="lm")
    p = Path("/tmp/hxl_sign.png"); im.save(p); return p


def pil_price_tag(text):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (256, 160), (252, 250, 244))
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 78, index=0)
    except Exception:
        f = ImageFont.load_default()
    d.text((128, 70), text, font=f, fill=(200, 30, 34), anchor="mm")
    p = Path(f"/tmp/hxl_tag_{text.replace('.', '_')}.png"); im.save(p); return p


def crop_bag(png: Path) -> Path:
    """裁掉资产渲染的烤入背景, 只留袋体 (排面平面用; 否则灰背景占 50% = 白卡)."""
    import numpy as np
    from PIL import Image
    out = Path("/tmp") / f"crop_{png.stem}.png"
    if out.exists():
        return out
    im = Image.open(png).convert("RGB")
    a = np.asarray(im, float)
    edge = np.concatenate([a[:, :24], a[:, -24:]], axis=1)
    bg = np.median(np.concatenate([edge.reshape(-1, 3)[::7]]), axis=0)
    dist = np.abs(a - bg[None, None, :]).sum(-1)
    ys, xs = np.where(dist > 60)
    if len(xs) > 100:
        x0, x1 = max(xs.min()-8, 0), min(xs.max()+8, a.shape[1])
        y0, y1 = max(ys.min()-8, 0), min(ys.max()+8, a.shape[0])
        im = im.crop((x0, y0, x1, y1))
    im.save(out)
    return out


def img_plane(name, tex_path, w, h, loc, rot=(0, 0, 0), emissive=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(tex_path))
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if emissive > 0:
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = emissive
        nt.links.new(tex.outputs["Color"], em.inputs["Color"])
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(bsdf.outputs["BSDF"], mix.inputs[1])
        nt.links.new(em.outputs["Emission"], mix.inputs[2])
        nt.links.new(mix.outputs["Shader"], nt.nodes["Material Output"].inputs["Surface"])
    mesh = bpy.data.meshes.new(name)
    o = bpy.data.objects.new(name, mesh)
    o.location = loc
    o.rotation_euler = [math.radians(a) for a in rot]
    sc = bpy.context.scene.collection
    sc.objects.link(o)
    import bmesh
    b = bmesh.new()
    v = [b.verts.new((-w/2, 0, -h/2)), b.verts.new((-w/2, 0, h/2)),
         b.verts.new((w/2, 0, h/2)), b.verts.new((w/2, 0, -h/2))]
    f = b.faces.new(v)
    f.normal_flip()
    uv = b.loops.layers.uv.verify()
    for loop, (uu, vv) in zip(f.loops, ((1, 0), (1, 1), (0, 1), (0, 0))):
        loop[uv].uv = (uu, vv)
    b.to_mesh(mesh); b.free()
    o.data.materials.append(mat)
    return o


def main():
    # 清启动场景 (事故 2026-11-21: 默认 Cube 2m 卡在相机与货架间 = 全程白雾元凶;
    # tde_driver 有 clean_scene, 此脚本没有 → 八轮"洗白"误诊为灯光/曝光/atlas)
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials,
                 bpy.data.cameras, bpy.data.lights, bpy.data.images, bpy.data.worlds):
        for item in list(coll):
            coll.remove(item, do_unlink=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"   # 默认 look 强去饱和 (冷柜线已知坑)
    sc.view_settings.exposure = -0.4
    sc.render.resolution_x, sc.render.resolution_y = 720, 1044
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.06, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.3

    # 地面 (棋盘, y=0 平面)
    img_plane("floor", pil_tex_floor(), 8.0, 8.0, (0, 4.0, 0), rot=(90, 0, 0))
    img_plane("sideL", pil_tex_backwall(), 0.1, SHELVES * LEVEL_H + 0.5,
              (-SHELF_W / 2 - 0.35, 1.6, SHELVES * LEVEL_H / 2), rot=(0, 0, 90), emissive=0.5)

    # 背光板 (发光背墙, 位于货架后)
    img_plane("backwall", pil_tex_backwall(), SHELF_W, SHELVES * LEVEL_H + 0.5,
              (0, DEPTH - 0.05, SHELVES * LEVEL_H / 2), emissive=1.1)

    # 招牌横带 (货架顶沿连体)
    img_plane("sign", pil_tex_sign(), SHELF_W, 0.42,
              (0, DEPTH - 0.04, SHELVES * LEVEL_H + 0.30), emissive=1.2)

    # 层板 + 前唇 + 排面 + 价签
    tag_texts = ["2.9", "4.9", "5.8", "5.9", "7.2", "1.7", "3.5"]
    bag_names = [a.stem for a in ASSETS]
    for lv in range(SHELVES):
        z0 = lv * LEVEL_H
        # 层板 (白板)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, DEPTH / 2, z0))
        sh = bpy.context.active_object
        sh.scale = (SHELF_W / 2, DEPTH / 2, 0.018)
        sh.name = f"shelf{lv}"
        m = bpy.data.materials.new(f"shm{lv}"); m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.92, 0.92, 0.94, 1)
        m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.3
        sh.data.materials.append(m)
        # 前唇亮边
        img_plane(f"lip{lv}", pil_price_tag(tag_texts[lv % len(tag_texts)]),
                  0.16, 0.10, (-SHELF_W / 2 + 0.25, DEPTH / 2 + 0.21, z0 + 0.005), emissive=0.35)
        # 排面: 两排软袋卡 (第一排贴唇, 第二排垫高出缝)
        fam = LEVEL_PLAN[lv % len(LEVEL_PLAN)]
        picks = [a for a in ASSETS if a.stem in fam] or ASSETS
        n = BAGS_PER_LEVEL
        bw = SHELF_W / n
        for r_i, (y_off, z_off, scale) in enumerate(((DEPTH / 2 - 0.06, 0.015, 0.93),
                                                     (DEPTH / 2 - 0.15, 0.09, 0.86))):
            for i in range(n):
                a = crop_bag(picks[(i * 5 + lv + r_i * 2) % len(picks)])  # 层内多样设计, 杀克隆感
                img_plane(f"bag{lv}_{r_i}_{i}", a, bw * 0.94 * scale, LEVEL_H * 0.72 * scale,
                          (-SHELF_W / 2 + bw * (i + 0.5), y_off, z0 + 0.02 + z_off * (1 if r_i else 0)),
                          emissive=0.25)
        # 层间背光带 (EEVEE 自发光不照明 → 需真光源; 朝袋背面)
        bl = bpy.data.lights.new(f"back{lv}", "AREA")
        bl.size = SHELF_W * 0.95; bl.size_y = LEVEL_H * 0.7; bl.energy = 8
        blo = bpy.data.objects.new(f"back{lv}", bl)
        blo.location = (0, DEPTH - 0.10, z0 + LEVEL_H / 2)
        blo.rotation_euler = (math.radians(-90), 0, 0)
        sc.collection.objects.link(blo)
        # 层板下沿灯带 (补层板唇高光)
        lt = bpy.data.lights.new(f"strip{lv}", "AREA")
        lt.size = SHELF_W * 0.9; lt.size_y = 0.05; lt.energy = 12
        lo = bpy.data.objects.new(f"strip{lv}", lt)
        lo.location = (0, DEPTH - 0.10, z0 + 0.05)
        lo.rotation_euler = (math.radians(-70), 0, 0)
        sc.collection.objects.link(lo)

    # 顶部射灯 ×4 (黑轨道语义简化为灯本体)
    for i, x in enumerate((-0.9, -0.3, 0.3, 0.9)):
        lt = bpy.data.lights.new(f"spot{i}", "SPOT")
        lt.energy = 120; lt.spot_size = math.radians(55)
        lo = bpy.data.objects.new(f"spot{i}", lt)
        lo.location = (x, -0.7, SHELVES * LEVEL_H + 0.55)
        aim = Vector((x * 0.6, DEPTH / 2, 1.0)) - lo.location
        lo.rotation_euler = aim.to_track_quat('-Z', 'Y').to_euler()
        sc.collection.objects.link(lo)

    # 前置柔光 (袋面受光底座)
    fl = bpy.data.lights.new("frontfill", "AREA")
    fl.size = 3.0; fl.size_y = 1.6; fl.energy = 40
    flo = bpy.data.objects.new("frontfill", fl)
    flo.location = (0, -1.1, 1.5)
    flo.rotation_euler = (math.radians(65), 0, 0)
    sc.collection.objects.link(flo)

    # 人位相机 (对账 v2: 站位偏右, 平视微仰, 透视向左收敛, 微滚转)
    cam = bpy.data.cameras.new("c"); cam.lens = 32
    co = bpy.data.objects.new("c", cam)
    co.location = (0.85, -1.55, 1.28)
    aim = Vector((-0.30, DEPTH / 2, 1.22)) - co.location
    rot = aim.to_track_quat('-Z', 'Y').to_euler()
    rot.rotate_axis('Y', math.radians(-2.0))  # 微滚转
    co.rotation_euler = rot
    sc.collection.objects.link(co); sc.camera = co

    sc.render.filepath = str(OUT)
    bpy.ops.render.render(write_still=True)
    print("HXL_SHELF_OK", OUT)


if __name__ == "__main__":
    main()
