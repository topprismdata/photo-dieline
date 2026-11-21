"""build_hxl_shelf: 好想来式背光墙货架段 — 场景/排面/灯光/人位相机一体化.

对账依据: docs/shelf_twin/RECONCILIATION.md v2 (primary.jpg 7 维真值).
用法: blender --background --python scripts/build_hxl_shelf.py -- out.png

构件 z/y 台账 (技能: blender-coldcase-shelf-scene — 落位前查冲突):
  地板 slab   z=-0.02 (顶面低于最低构件)      y 0..8
  层板 lv     z0=lv*0.38 .. z0+0.025 (板厚)   y 0..DEPTH
  层板唇+价签 z0-0.05..z0+0.025 前立面          y=DEPTH/2
  袋(坐落)    底=z0+0.015, 高 0.75*LEVEL_H    y 前=0.14 后=0.03
  背光带      z0+LEVEL_H*0.35 层板后 0.10     y=DEPTH-0.10
  层下灯带    z0+0.05                          y=DEPTH-0.10
  射灯×4      z=顶+0.55 悬挂                   y=-0.7
  相机        (0.85,-1.55,1.28) → (-0.3,D/2,1.22) roll-2°
"""
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np
import PIL.Image as Image
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).parent))
from bag_print import render_print
from PIL import ImageFont

def _load_font_cn(sz):
    try:
        return ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", sz, index=0)
    except Exception:
        return ImageFont.load_default()
FLAVORS = ["经典原味", "黄瓜味", "青柠味", "麻辣小龙虾味", "番茄味", "海苔味",
           "芝士味", "焦糖黄油味", "劲爆辣味", "烧烤鸡味", "黑松露味", "藤椒味"]

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = Path(argv[0]) if argv else Path("/tmp/hxl_v1.png")
ROOT = Path("/Users/guohongbin/photo-dieline")
DESIGN_DIR = ROOT / "assets/pillow_designs"
AI_FLAVOR_KEY = {"经典原味": "yuwei", "黄瓜味": "huanggua", "青柠味": "qingning", "麻辣小龙虾味": "xiaolongxia",
                 "番茄味": "fanqie", "海苔味": "haitai", "芝士味": "zhishi", "焦糖黄油味": "jiaotang",
                 "劲爆辣味": "jinbaoLa", "烧烤鸡味": "shaokaoJi", "黑松露味": "heisonglu", "藤椒味": "tengjiao"}
LV_GIDX = {}
FOOD_PATCHES = [Image.open(pp) for pp in sorted((ROOT / "assets/food_patches").glob("*.png"))]
FLAVOR_TINT = {"黄瓜味": (0.82, 1.10, 0.85), "青柠味": (0.85, 1.08, 0.82),
               "番茄味": (1.10, 0.92, 0.85), "麻辣小龙虾味": (1.10, 0.90, 0.82),
               "劲爆辣味": (1.12, 0.88, 0.80), "芝士味": (1.08, 1.04, 0.80)}

# ---- 场景参数 (ESR Step A: planogram.json 驱动; 缺省回退对账 v2) ----
_PLANO = ROOT / "docs/shelf_twin/planogram.json"
if _PLANO.exists():
    _pj = json.loads(_PLANO.read_text())
    SHELVES = _pj["shelf"]["layers"]
    LEVEL_H = _pj["shelf"]["layer_pitch_mm"] / 1000.0
    SHELF_W = _pj["shelf"]["shelf_width_mm"] / 1000.0
    DEPTH = _pj["shelf"]["board_depth_mm"] / 1000.0
    print(f"[planogram] LEVEL_H={LEVEL_H:.3f} SHELVES={SHELVES} (标定驱动)")
else:
    SHELVES, LEVEL_H, SHELF_W, DEPTH = 7, 0.38, 2.4, 0.40
ASSETS = sorted((ROOT / "assets/pillow_bags").glob("*.png"))
FAMILY_RGB = {  # 12 设计族基色 (与 make_planogram.FAMILY_IDX 同序)
    "red": (0.82, 0.22, 0.10), "orange": (0.92, 0.45, 0.10), "yellow": (0.95, 0.72, 0.12),
    "green": (0.30, 0.62, 0.28), "blue": (0.18, 0.42, 0.72), "purple": (0.48, 0.25, 0.60),
    "brown": (0.42, 0.26, 0.16), "pink": (0.90, 0.50, 0.58), "teal": (0.15, 0.58, 0.58),
    "gold": (0.85, 0.62, 0.20), "white": (0.88, 0.86, 0.82), "dark": (0.22, 0.24, 0.30),
}


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
    im = Image.new("RGB", (2048, 512), (196, 30, 38))
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 190, index=0)
        f2 = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 120, index=0)
        f3 = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 88, index=0)
    except Exception:
        f = f2 = f3 = ImageFont.load_default()
    d.text((70, 150), "来来来 好想来", font=f, fill=(255, 255, 255), anchor="lm")
    d.text((70, 360), "又便宜 又好吃", font=f2, fill=(255, 230, 90), anchor="lm")
    d.rounded_rectangle([1470, 90, 1990, 430], radius=36, fill=(252, 250, 244))
    d.text((1730, 200), "好想来", font=f3, fill=(196, 30, 38), anchor="mm")
    d.text((1730, 330), "品牌零食", font=f3, fill=(196, 30, 38), anchor="mm")
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


def pil_tag_rail(fracs, prices, seed_lv=0):
    """H16: 逐组价签轨 — 沿唇贯通白条, 每组一段: 条码块+红价+灰码, 组间细分隔 (真实货架语义)."""
    import random
    from PIL import Image, ImageDraw, ImageFont
    W, H = 3072, 210
    im = Image.new("RGB", (W, H), (253, 253, 251))
    d = ImageDraw.Draw(im)
    try:
        f_p = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 150, index=0)
    except Exception:
        f_p = ImageFont.load_default()
    rng = random.Random(seed_lv * 17 + 3)
    x = 0.0
    for gi, (fr, pr) in enumerate(zip(fracs, prices)):
        w = int(fr * W)
        if rng.random() < 0.10:
            x += w  # 空洞段 (轨上无签, 补货语义)
            continue
        w = int(w * (0.82 + rng.random() * 0.18))
        # 条码块 (随机宽度黑白竖线)
        bx = x + w * 0.05
        bw = w * 0.15
        cx = bx
        while cx < bx + bw:
            lw = rng.choice((3, 5, 8))
            d.rectangle([cx, H * 0.22, cx + lw, H * 0.72], fill=(22, 22, 24))
            cx += lw + rng.choice((4, 6, 9))
        # 红价 + 灰码
        d.text((x + w * 0.58, H * 0.46 + rng.randint(-8, 8)), pr, font=f_p, fill=(172, 8, 14), anchor="mm")
        d.text((x + w * 0.58, H * 0.87), f"69{rng.randint(10000000, 99999999)}",
               fill=(24, 26, 30), anchor="mm")
        # 组间分隔
        if gi < len(fracs) - 1:
            d.line([x + w, 0, x + w, H], fill=(150, 152, 156), width=4)
        x += w
    # 顶部装卡阴影线
    d.rectangle([0, 0, W, 6], fill=(214, 215, 218))
    p = Path(f"/tmp/hxl_tagrail_{seed_lv}.png"); im.save(p); return p


def pil_tag_single(seed, price):
    """D27: 独立价签卡 — 白底黑条码+大红价+灰码, 每签独立随机."""
    import random
    from PIL import Image, ImageDraw, ImageFont
    W, H = 512, 256
    im = Image.new("RGB", (W, H), (253, 253, 251))
    d = ImageDraw.Draw(im)
    try:
        f_p = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 128, index=0)
    except Exception:
        f_p = ImageFont.load_default()
    rng = random.Random(seed * 29 + 5)
    bx, bw = W * 0.07, W * 0.34
    cx = bx
    while cx < bx + bw:
        lw = rng.choice((4, 7, 11))
        d.rectangle([cx, H * 0.24, cx + lw, H * 0.70], fill=(20, 20, 22))
        cx += lw + rng.choice((5, 8, 12))
    d.text((W * 0.62, H * 0.40), price, font=f_p, fill=(186, 16, 22), anchor="mm")
    d.text((W * 0.62, H * 0.82), f"69{rng.randint(10000000, 99999999)}", fill=(40, 42, 46), anchor="mm")
    d.rectangle([0, 0, W, 8], fill=(210, 211, 214))
    p = Path(f"/tmp/hxl_tag1_{seed}.png"); im.save(p); return p


def crop_bag(png: Path, seed: int = 0) -> Path:
    """裁掉资产渲染的烤入背景 + 变体抖动 (翻转/饱和/亮度 ±15%): 12 资产 → 48 设计, 杀克隆感."""
    import numpy as np
    from PIL import Image, ImageEnhance
    out = Path("/tmp") / f"crop_{png.stem}_{seed}.png"
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
    rng = np.random.default_rng(seed)
    # 严禁水平翻转: 翻转会镜像印刷文字 (v13-v19 镜像字真根因)
    im = ImageEnhance.Color(im).enhance(0.85 + rng.random() * 0.4)
    im = ImageEnhance.Brightness(im).enhance(0.9 + rng.random() * 0.25)
    im.save(out)
    return out


def img_plane(name, tex_path, w, h, loc, rot=(0, 0, 0), emissive=0.0, rough=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = True  # 背脸剔除: 第二排不再漏镜像字
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Coat Weight"].default_value = 0.10      # 镀铝亮面袋 (0.28 洗白印刷, 再平衡实证)
    bsdf.inputs["Coat Roughness"].default_value = 0.16
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
    # CCW(自 -y 视角)顶点序 + 恒等 UV — 法线朝相机, 文字正读
    # (事故: normal_flip 反转环序 → UV 转置 90°, 文字竖排)
    v = [b.verts.new((-w/2, 0, -h/2)), b.verts.new((w/2, 0, -h/2)),
         b.verts.new((w/2, 0, h/2)), b.verts.new((-w/2, 0, h/2))]
    f = b.faces.new(v)
    uv = b.loops.layers.uv.verify()
    for loop, (uu, vv) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv].uv = (uu, vv)
    b.to_mesh(mesh); b.free()
    o.data.materials.append(mat)
    return o


def img_bag_thin(name, tex_path, w, h, loc, emissive=0.06, rough=0.4, lean=0.0):
    """10mm 薄盒软袋: 正面贴图, 侧面/背面压暗纯色 — 实体厚度消'平面卡片'感 (GPT D3c P1)."""
    import bmesh
    t = 0.01
    avg = Image.open(tex_path).resize((1, 1)).getpixel((0, 0))
    mfront = bpy.data.materials.new(name + "_f")
    mfront.use_nodes = True
    mfront.use_backface_culling = True
    nt = mfront.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Coat Weight"].default_value = 0.10      # 镀铝亮面袋 (0.28 洗白印刷, 再平衡实证)
    bsdf.inputs["Coat Roughness"].default_value = 0.16
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
    msolid = bpy.data.materials.new(name + "_s")
    msolid.use_nodes = True
    sb = msolid.node_tree.nodes["Principled BSDF"]
    sb.inputs["Base Color"].default_value = (avg[0]/255*0.55, avg[1]/255*0.55, avg[2]/255*0.55, 1)
    sb.inputs["Roughness"].default_value = 0.5
    mesh = bpy.data.meshes.new(name)
    o = bpy.data.objects.new(name, mesh)
    o.location = loc
    o.rotation_euler = (math.radians(pitch), 0, math.radians(lean))
    bpy.context.scene.collection.objects.link(o)
    b = bmesh.new()
    V = [b.verts.new(v) for v in ((-w/2,-t/2,-h/2),(w/2,-t/2,-h/2),(w/2,-t/2,h/2),(-w/2,-t/2,h/2),
                                  (-w/2,t/2,-h/2),(w/2,t/2,-h/2),(w/2,t/2,h/2),(-w/2,t/2,h/2))]
    f0 = b.faces.new((V[0], V[1], V[2], V[3]))
    uv = b.loops.layers.uv.verify()
    for loop, (uu, vv) in zip(f0.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv].uv = (uu, vv)
    for fv in ((V[5],V[4],V[7],V[6]), (V[4],V[0],V[3],V[7]), (V[1],V[5],V[6],V[2]),
               (V[3],V[2],V[6],V[7]), (V[4],V[5],V[1],V[0])):
        b.faces.new(fv)
    b.to_mesh(mesh); b.free()
    mesh.materials.append(mfront)
    mesh.materials.append(msolid)
    mesh.polygons[0].material_index = 0
    for poly in mesh.polygons[1:]:
        poly.material_index = 1
    return o


def build_pyramid_rack_v2(loc, h=1.0, w=0.46, dep=0.34):
    """前景挂架 v2 (对齐②最小要素): 细圆管 A 形侧架 + 3 挂杆 + 挂钩 + 垂坠袋位."""
    import bmesh
    x0, y0 = loc
    mmetal = bpy.data.materials.new("rackmetal")
    mmetal.use_nodes = True
    mb = mmetal.node_tree.nodes["Principled BSDF"]
    mb.inputs["Base Color"].default_value = (0.91, 0.91, 0.93, 1)
    mb.inputs["Roughness"].default_value = 0.3
    mb.inputs["Metallic"].default_value = 0.65

    def tube(name, p0, p1, r):
        d = (Vector(p1) - Vector(p0))
        mid = (Vector(p0) + Vector(p1)) / 2
        _bm = bmesh.new()
        bmesh.ops.create_cone(_bm, cap_ends=True, segments=12,
                              radius1=r, radius2=r, depth=d.length)
        mesh = bpy.data.meshes.new(name)
        _bm.to_mesh(mesh)
        _bm.free()
        o = bpy.data.objects.new(name, mesh)
        o.location = mid
        o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        bpy.context.scene.collection.objects.link(o)
        o.data.materials.append(mmetal)
        return o

    tops = []
    for sx in (-1, 1):
        px = x0 + sx * w / 2
        # A 腿 (前后撑开) + 竖杆
        tube(f"lg_f{sx}", (px - sx * 0.04, y0 - dep / 2, 0), (px, y0, h), 0.006)
        tube(f"lg_b{sx}", (px + sx * 0.04, y0 + dep / 2, 0), (px, y0, h), 0.006)
        tube(f"post{sx}", (px, y0, 0), (px, y0, h), 0.005)
        tops.append((px, y0, h))
    tube("topbar", tops[0], tops[1], 0.005)
    # 底横撑 + 接地脚
    tube("base_f", (x0 - w / 2 + 0.02, y0 - dep / 2, 0.012), (x0 + w / 2 - 0.02, y0 - dep / 2, 0.012), 0.005)
    tube("base_b", (x0 - w / 2 + 0.02, y0 + dep / 2, 0.012), (x0 + w / 2 - 0.02, y0 + dep / 2, 0.012), 0.005)
    # 3 层挂杆 (前面, 层间) + 挂钩
    tier_z = [h * t for t in (0.24, 0.5, 0.76)]
    hooks = []
    for k, zt in enumerate(tier_z):
        tube(f"rail{k}", (x0 - w / 2 + 0.03, y0 - dep * 0.36, zt),
             (x0 + w / 2 - 0.03, y0 - dep * 0.36, zt), 0.0045)
        for hi in range(4):
            hx = x0 - w / 2 + 0.08 + (w - 0.16) * hi / 3
            tube(f"hook{k}_{hi}", (hx, y0 - dep * 0.36, zt), (hx, y0 - dep * 0.36, zt - 0.018), 0.002)
            hooks.append((hx, y0 - dep * 0.36, zt - 0.018, k))
    return hooks


def barrel_placeholder(name, x, y, z_bot, rgb, dia=0.075, hgt=0.26, rng=None, tex_path=None):
    """桶装罐 (H2 几何真实性 + 标签环绕: 设计图 UV 环绕侧壁, D8 评审罐顶过于整齐)."""
    r = rng if rng is not None else np.random.default_rng(abs(hash(name)) % (2**32))
    soft = tuple(rgb[c] * 0.78 + 0.14 for c in range(3))
    bpy.ops.mesh.primitive_cylinder_add(radius=dia / 2, depth=hgt, location=(x, y, z_bot + hgt / 2))
    o = bpy.context.active_object
    o.name = name
    o.scale = (0.985 + r.random() * 0.03, 0.985 + r.random() * 0.03, 1.0)  # 逐罐锥度差
    o.rotation_euler = (r.uniform(-0.015, 0.015), r.uniform(-0.015, 0.015),
                        r.uniform(0, math.pi))  # 微倾+随机自转 (印刷面对向差异)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (soft[0], soft[1], soft[2], 1)
    b.inputs["Roughness"].default_value = 0.38
    nt = m.node_tree
    if tex_path and Path(tex_path).exists():
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(str(tex_path))
        nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
        b.inputs["Roughness"].default_value = 0.34
    o.data.materials.append(m)
    bpy.ops.mesh.primitive_cylinder_add(radius=dia / 2 + 0.0008, depth=0.028,
                                        location=(x, y, z_bot + hgt * 0.62))
    band = bpy.context.active_object
    band.name = name + "_band"
    mm = bpy.data.materials.new(name + "_band")
    mm.use_nodes = True
    mm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.95, 0.95, 0.94, 1)
    band.data.materials.append(mm)
    # 内壁凹腔 (开口层次): 半径/深度逐罐不同
    wall_r = dia / 2 - (0.0022 + r.random() * 0.0016)
    wall_d = 0.014 + r.random() * 0.013
    bpy.ops.mesh.primitive_cylinder_add(radius=wall_r, depth=wall_d,
                                        location=(x, y, z_bot + hgt - wall_d / 2 + 0.0035))
    wall = bpy.context.active_object
    wall.name = name + "_wall"
    mw = bpy.data.materials.new(name + "_wall")
    mw.use_nodes = True
    wb = mw.node_tree.nodes["Principled BSDF"]
    wb.inputs["Base Color"].default_value = (0.14 + r.random() * 0.05,
                                             0.13 + r.random() * 0.05,
                                             0.12 + r.random() * 0.05, 1)
    wb.inputs["Roughness"].default_value = 0.6
    wall.data.materials.append(mw)
    # 金属顶缘: 半径/z/倾角/粗糙度逐罐抖动 (不再整齐划一)
    lid_r = dia / 2 - (0.0005 + r.random() * 0.001)
    lid_z = z_bot + hgt - 0.006 + (r.random() - 0.5) * 0.0025
    bpy.ops.mesh.primitive_cylinder_add(radius=lid_r, depth=0.011, location=(x, y, lid_z))
    lid = bpy.context.active_object
    lid.name = name + "_lid"
    lid.rotation_euler = (r.uniform(-0.02, 0.02), r.uniform(-0.02, 0.02),
                          r.uniform(0, math.pi))
    ml = bpy.data.materials.new(name + "_lid")
    ml.use_nodes = True
    lb = ml.node_tree.nodes["Principled BSDF"]
    g = 0.72 + r.random() * 0.08
    lb.inputs["Base Color"].default_value = (g, g + 0.01, g + 0.03, 1)
    lb.inputs["Metallic"].default_value = 0.75 + r.random() * 0.15
    lb.inputs["Roughness"].default_value = 0.28 + r.random() * 0.18
    lid.data.materials.append(ml)


def box_placeholder(name, x, y, z_bot, rgb, bw_=0.12, hgt=0.19):
    """盒装占位 (planogram form=box): 立盒+白窗前板, 填满槽宽."""
    soft = tuple(rgb[c] * 0.75 + 0.16 for c in range(3))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z_bot + hgt / 2))
    o = bpy.context.active_object
    o.name = name
    o.scale = (bw_, 0.045, hgt)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (soft[0], soft[1], soft[2], 1)
    b.inputs["Roughness"].default_value = 0.42
    o.data.materials.append(m)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y - 0.0235, z_bot + hgt / 2))
    front = bpy.context.active_object
    front.name = name + "_front"
    front.rotation_euler = (math.radians(90), 0, 0)
    front.scale = (bw_ * 0.62, hgt * 0.5, 1)
    mm = bpy.data.materials.new(name + "_front")
    mm.use_nodes = True
    mm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.94, 0.93, 0.90, 1)
    front.data.materials.append(mm)


def bag_material(name, tex_path, rough=0.4, emissive=0.06):
    """D30: 印刷材质 (从 img_bag_curved 抽出, 供布料库实例 OBJECT-link 复用)."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Coat Weight"].default_value = 0.10      # 镀铝亮面袋 (0.28 洗白印刷, 再平衡实证)
    bsdf.inputs["Coat Roughness"].default_value = 0.16
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 620.0
    nz.inputs["Detail"].default_value = 4.0
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["To Min"].default_value = 0.93
    ramp.inputs["To Max"].default_value = 1.0
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(tex_path))
    hs = nt.nodes.new("ShaderNodeHueSaturation")
    hs.inputs["Saturation"].default_value = 1.18  # D40: 印刷更鲜艳
    nt.links.new(tex.outputs["Color"], hs.inputs["Color"])
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    nt.links.new(hs.outputs["Color"], mul.inputs[6])
    nt.links.new(ramp.outputs["Result"], mul.inputs[7])
    nt.links.new(mul.outputs[2], bsdf.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = max(0.04, rough - 0.05)  # D40: 反光再收敛
    rr.inputs["To Max"].default_value = rough + 0.09
    nt.links.new(nz.outputs["Fac"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], bsdf.inputs["Roughness"])
    try:
        bsdf.inputs["Coat Weight"].default_value = 0.10  # D40: 银灰反射压制
        bsdf.inputs["Coat Roughness"].default_value = 0.28
    except KeyError:
        pass
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = emissive
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(bsdf.outputs["BSDF"], mix.inputs[1])
    nt.links.new(em.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], nt.nodes["Material Output"].inputs["Surface"])
    return mat


CLOTH_LIB = []  # D30: 布料压力袋变体网格库 (base 0.095×0.19, origin 底面中心)


def build_cloth_library(n_per=6):  # D35: 48→72变体
    """D30: 每味4变体布料压力袋 — 封闭枕头网格+cloth pressure+顶底销点 → 静态形变网格.

    实证: 5.2 API (self_collision 在 collision_settings; pressure_factor 单参数),
    2.9s/袋, 中段鼓胀 ~45mm; 调参=绷紧大面+少量大折痕 (tension 45/pressure 1.3)."""
    import bmesh
    from mathutils import Vector as _V
    lib_col = bpy.data.collections.new("clothlib")
    bpy.context.scene.collection.children.link(lib_col)
    for var in range(12 * n_per):  # 72 = 12味×6
        rng = np.random.default_rng(var * 101 + 17)
        BW, BH, W, H = 0.095, 0.19, 24, 34
        bm = bmesh.new()
        vf, vb = {}, {}
        for r in range(H + 1):
            for c in range(W + 1):
                u, v = c / W, r / H
                bow = math.sin(u * math.pi) * 0.006
                y_in = math.sin(v * math.pi) * 0.004
                vf[(r, c)] = bm.verts.new((-BW/2 + u*BW, -0.012 - bow + y_in, v * BH))
                vb[(r, c)] = bm.verts.new((-BW/2 + u*BW, 0.012 + bow - y_in, v * BH))
        for r in range(H):
            for c in range(W):
                bm.faces.new((vf[(r,c)], vf[(r+1,c)], vf[(r+1,c+1)], vf[(r,c+1)]))
                bm.faces.new((vb[(r,c)], vb[(r,c+1)], vb[(r+1,c+1)], vb[(r+1,c)]))
        for c in range(W):
            bm.faces.new((vf[(0,c)], vb[(0,c)], vb[(0,c+1)], vf[(0,c+1)]))
            bm.faces.new((vf[(H,c)], vf[(H,c+1)], vb[(H,c+1)], vb[(H,c)]))
        for r in range(H):
            bm.faces.new((vf[(r,0)], vf[(r+1,0)], vb[(r+1,0)], vb[(r,0)]))
            bm.faces.new((vb[(r,W)], vb[(r+1,W)], vf[(r+1,W)], vf[(r,W)]))
        uv = bm.loops.layers.uv.verify()
        for f in bm.faces:
            f.smooth = True
            cen_y = sum(l.vert.co.y for l in f.loops) / len(f.loops)
            front = cen_y < 0
            for l in f.loops:
                u, v = (l.vert.co.x + BW/2) / BW, l.vert.co.z / BH
                l[uv].uv = (u, v) if front else (1.0 - u, v)
        mesh = bpy.data.meshes.new(f"cloth_{var:02d}")
        mesh.materials.append(None)
        bm.to_mesh(mesh)
        bm.free()
        # 预噪声: 逐变体折叠独特性
        for vtx in mesh.vertices:
            if vtx.co.z > 0.004 and vtx.co.z < BH - 0.004:
                vtx.co.y += float(rng.normal(0, 0.00015))  # G1修: 预噪声收敛
        obj = bpy.data.objects.new(f"clothsrc_{var:02d}", mesh)
        lib_col.objects.link(obj)
        vg = obj.vertex_groups.new(name="pin")
        for vtx in mesh.vertices:
            if vtx.co.z < 0.004 or vtx.co.z > BH - 0.004:
                vg.add([vtx.index], 1.0, 'ADD')
        mod = obj.modifiers.new("cloth", 'CLOTH')
        cl = mod.settings
        cl.vertex_group_mass = "pin"
        cl.quality = 5
        cl.mass = 0.08
        cl.tension_stiffness = 60 * (0.9 + rng.random() * 0.2)  # G1修: 绷紧充气枕
        cl.compression_stiffness = 45 * (0.85 + rng.random() * 0.3)
        cl.shear_stiffness = 22
        cl.bending_stiffness = 3.5 * (0.7 + rng.random() * 0.6)
        cl.air_damping = 2.0
        cl.time_scale = 1.2
        cl.pressure_factor = 2.0 + rng.random() * 0.6  # G1修: 饱满鼓胀 (皱纸片→充气枕)
        cs = mod.collision_settings
        cs.use_self_collision = True
        cs.self_distance_min = 0.0025
        # D36: 接触碰撞体 — 侧壁 (随机窄距=侧缘压扁) + 40%变体加前顶压板 (袋顶弯折)
        gap = 0.010 + rng.random() * 0.006
        for side in (-1, 1):
            cw = bpy.data.meshes.new(f"cw{var}")
            cmb = bmesh.new()
            v1 = cmb.verts.new((side * (BW/2 + gap), -0.03, -0.02))
            v2 = cmb.verts.new((side * (BW/2 + gap), 0.03, -0.02))
            v3 = cmb.verts.new((side * (BW/2 + gap + side * rng.random() * 0.004), 0.03, BH + 0.02))
            v4 = cmb.verts.new((side * (BW/2 + gap + side * rng.random() * 0.004), -0.03, BH + 0.02))
            cmb.faces.new((v1, v2, v3, v4))
            cmb.to_mesh(cw)
            cmb.free()
            cwo = bpy.data.objects.new(f"cwall{var}_{side}", cw)
            lib_col.objects.link(cwo)
        if rng.random() < 0.2:  # G1修: 顶弯折减半
            cf = bpy.data.meshes.new(f"cf{var}")
            cmb = bmesh.new()
            f1 = cmb.verts.new((-BW, -0.028, BH * 0.86))
            f2 = cmb.verts.new((BW, -0.028, BH * 0.86))
            f3 = cmb.verts.new((BW, -0.004, BH * 1.05))
            f4 = cmb.verts.new((-BW, -0.004, BH * 1.05))
            cmb.faces.new((f4, f3, f2, f1))
            cmb.to_mesh(cf)
            cmb.free()
            cfo = bpy.data.objects.new(f"cfront{var}", cf)
            lib_col.objects.link(cfo)
        mod.point_cache.frame_end = 20
        sc2 = bpy.context.scene
        sc2.frame_set(1)
        for fr in range(1, 21):
            sc2.frame_set(fr)
        bpy.context.view_layer.objects.active = obj
        with bpy.context.temp_override(selected_objects=[obj], active_object=obj):
            bpy.ops.object.modifier_apply(modifier="cloth")
        # 原点移到底面中心 (调用方传层板底 z + h/2)
        off = _V((0, 0, -BH / 2))
        for vtx in mesh.vertices:
            vtx.co += off
        CLOTH_LIB.append(mesh)
        lib_col.objects.unlink(obj)  # 网格由实例持有; 源对象退场
    print(f"CLOTHLIB_OK n={len(CLOTH_LIB)}")


def img_bag_curved(name, tex_path, w, h, loc, emissive=0.06, rough=0.4, lean=0.0, amp=0.006, pitch=0.0, phi1=0.0, phi2=0.0, phi3=0.0, phi4=0.0):
    """微鼓曲面前板 (6mm): crop 纹理不变, 剪影+镜面变化 — D4 教训的保守中间路径."""
    import bmesh
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Coat Weight"].default_value = 0.10      # 镀铝亮面袋 (0.28 洗白印刷, 再平衡实证)
    bsdf.inputs["Coat Roughness"].default_value = 0.16
    # H8 表面微真实: 印刷颗粒 (噪声乘色) + 粗糙度微_map + 塑料清漆双层
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 620.0
    nz.inputs["Detail"].default_value = 4.0
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = 0.0
    ramp.inputs["From Max"].default_value = 1.0
    ramp.inputs["To Min"].default_value = 0.93   # 颗粒调暗 7%
    ramp.inputs["To Max"].default_value = 1.0
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(tex_path))
    hs = nt.nodes.new("ShaderNodeHueSaturation")
    hs.inputs["Saturation"].default_value = 1.18  # D40: 印刷更鲜艳
    nt.links.new(tex.outputs["Color"], hs.inputs["Color"])
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    nt.links.new(hs.outputs["Color"], mul.inputs[6])
    nt.links.new(ramp.outputs["Result"], mul.inputs[7])
    nt.links.new(mul.outputs[2], bsdf.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["From Min"].default_value = 0.0
    rr.inputs["From Max"].default_value = 1.0
    rr.inputs["To Min"].default_value = max(0.04, rough - 0.05)  # D40: 反光再收敛
    rr.inputs["To Max"].default_value = rough + 0.09
    nt.links.new(nz.outputs["Fac"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], bsdf.inputs["Roughness"])
    try:
        bsdf.inputs["Coat Weight"].default_value = 0.10  # D40: 银灰反射压制   # 塑料薄膜双层反射
        bsdf.inputs["Coat Roughness"].default_value = 0.28
    except KeyError:
        pass
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
    o.rotation_euler = (math.radians(pitch), 0, math.radians(lean))
    bpy.context.scene.collection.objects.link(o)
    b = bmesh.new()
    sx, sz = 8, 8
    grid = []
    for iz in range(sz + 1):
        row = []
        for ix in range(sx + 1):
            u, v = ix / sx, iz / sz
            # H3 侧缘外弓 + H5 左右不对称弓 (逐侧相位差) + 封口鳍边外展
            bow = 1 + 0.045 * math.sin(math.pi * v)
            if u < 0.5:
                bow += 0.014 * math.sin(2 * math.pi * v + phi3)
            else:
                bow += 0.014 * math.sin(2 * math.pi * v + phi4)
            fin = 0 if (v < 0.045 or v > 0.955) else 1
            bow *= 1.024 if not fin else 1.0
            bulge = math.sin(math.pi * u) * math.sin(math.pi * v)
            # H4: 鼓包非均匀 (低频不规则项, 逐袋相位差) + 封边褶皱 (高频浅纹)
            irr = 1 + 0.32 * math.sin(3 * math.pi * u + phi1) * math.sin(2 * math.pi * v + phi2)
            wr = 0.0016 * math.sin(9 * math.pi * v + phi2 * 0.5) * (1 - math.sin(math.pi * u)) ** 2
            row.append(b.verts.new(((u - 0.5) * w * bow,
                                    -amp * bulge * irr + wr * (u * (1 - u) * 4)
                                    - (0.0 if fin else 0.0035),
                                    (v - 0.5) * h)))
        grid.append(row)
    uv = b.loops.layers.uv.verify()
    for iz in range(sz):
        for ix in range(sx):
            f = b.faces.new((grid[iz][ix], grid[iz][ix + 1], grid[iz + 1][ix + 1], grid[iz + 1][ix]))
            for loop, du, dv in zip(f.loops, (0, 1, 1, 0), (0, 0, 1, 1)):
                loop[uv].uv = (ix / sx + du / sx, 1 - (iz / sz + dv / sz))
    b.normal_update()
    b.to_mesh(mesh)
    b.free()
    o.data.materials.append(mat)
    return o


def apply_clay_override():
    """白模模式: 所有网格覆写单一中性灰材质 (形态验收专用, 逐层验证前禁止看印刷)."""
    clay = bpy.data.materials.new("clay_grey")
    clay.use_nodes = True
    b = clay.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.62, 0.62, 0.63, 1)
    b.inputs["Roughness"].default_value = 0.55
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.data.materials.clear()
            o.data.materials.append(clay)


def main():
    # 清启动场景 (事故 2026-11-21: 默认 Cube 2m 卡在相机与货架间 = 全程白雾元凶;
    # tde_driver 有 clean_scene, 此脚本没有 → 八轮"洗白"误诊为灯光/曝光/atlas)
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials,
                 bpy.data.cameras, bpy.data.lights, bpy.data.images, bpy.data.worlds):
        for item in list(coll):
            coll.remove(item, do_unlink=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    try:
        sc.cycles.device = "GPU"
        sc.cycles.samples = 96
        sc.cycles.use_denoising = True
    except AttributeError:
        pass
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"   # 默认 look 强去饱和 (冷柜线已知坑)
    sc.view_settings.exposure = -0.55
    sc.view_settings.gamma = 1.02
    sc.render.resolution_x, sc.render.resolution_y = 720, 1044
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    # H1 光照重构: HDRI 世界给光泽面反射内容 (黑虚空=塑料感根源, 杠杆#4)
    env = w.node_tree.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(
        str(ROOT / "assets/hdri/studio_small_09_2k.hdr"))
    bg = w.node_tree.nodes["Background"]
    w.node_tree.links.new(env.outputs["Color"], bg.inputs["Color"])
    bg.inputs[1].default_value = 0.3

    # 地面 (棋盘, y=0 平面)
    img_plane("floor", pil_tex_floor(), 8.0, 8.0, (0, 4.0, 0), rot=(90, 0, 0))
    img_plane("sideL", pil_tex_backwall(), DEPTH, SHELVES * LEVEL_H + 0.5,
              (-SHELF_W / 2 - 0.02, DEPTH / 2, SHELVES * LEVEL_H / 2), rot=(0, 0, 90), emissive=0.22)

    # 背光板 (发光背墙, 位于货架后)
    img_plane("backwall", pil_tex_backwall(), SHELF_W, SHELVES * LEVEL_H + 0.5,
              (0, DEPTH - 0.05, SHELVES * LEVEL_H / 2), emissive=1.1)

    # 招牌横带 (货架顶沿连体)
    img_plane("sign", pil_tex_sign(), SHELF_W, 0.62,
              (0, DEPTH - 0.04, SHELVES * LEVEL_H + 0.30), emissive=1.2)

    # 层板 + 前唇 + 排面 + 价签
    tag_texts = ["2.9", "4.9", "5.8", "5.9", "7.2", "1.7", "3.5"]
    bag_names = [a.stem for a in ASSETS]
    # ESR Step C: 加载陈列表 (数据驱动布局; 场景只留夹具/灯光/相机)
    PLAN = json.loads((ROOT / "data/shelf_twin/planogram.json").read_text())
    # D30: 布料压力袋变体库 (48 网格 × 逐实例 OBJECT 印刷 = 无重复组合)
    build_cloth_library(n_per=6)  # D35: 48→72变体

    for lv in range(SHELVES):
        z0 = lv * LEVEL_H
        # 层板 (白板)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, DEPTH / 2, z0))
        sh = bpy.context.active_object
        sh.scale = (SHELF_W / 2, DEPTH / 2, 0.011)  # G1修: 2cm薄板
        sh.name = f"shelf{lv}"
        m = bpy.data.materials.new(f"shm{lv}"); m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.92, 0.92, 0.94, 1)
        m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.3
        sh.data.materials.append(m)
        # 前唇亮边 (H16 价签轨另置, 见排面归一化后)
        # ESR Step C: 排面 = planogram.json 消费者 (facings×单位宽 → 宽度分配)
        rng = np.random.default_rng(lv * 31 + 7)
        plan_lv = PLAN["levels"][lv]
        # 排面归一化: VLM 计数含二排露头会超墙容量, 按比例归一到 ≤24 槽
        fac_sum = sum(g["facings"] for g in plan_lv["groups"])
        norm = min(1.0, 24.0 / fac_sum)
        plan_lv = {**plan_lv, "groups": [{**g, "facings": max(1, round(g["facings"] * norm))}
                                         for g in plan_lv["groups"]]}
        # D28: 连续轨内嵌逐组大数字 (轨底连续+段内大红价+空洞段)
        fracs = [g["width_frac"] for g in plan_lv["groups"]]
        fs = sum(fracs) or 1.0
        prices = [tag_texts[(lv + gi) % len(tag_texts)] for gi in range(len(fracs))]
        img_plane(f"tagrail{lv}", pil_tag_rail([f / fs for f in fracs], prices, seed_lv=lv),
                  SHELF_W - 0.04, 0.15, (0, DEPTH / 2 + DEPTH / 4 + 0.003, z0 + 0.012), emissive=0.30)
        for r_i, (y_off, s0, sh) in enumerate(((DEPTH / 2 - 0.06, 1.0, 0.0),
                                               (DEPTH / 2 - 0.17, 0.92, 0.5))):
            for g in plan_lv["groups"]:
                j = int(g["design_id"].split("_")[1])
                rgb = FAMILY_RGB[g["color"]]
                gw = g["width_frac"] * SHELF_W
                x0 = g["x0_frac"] * SHELF_W - SHELF_W / 2 + (rng.random() - 0.5) * 0.02  # H10 组界横移
                n_g = max(1, g["facings"] + (1 if sh and g["facings"] > 2 else 0))
                bgw = gw / n_g
                z_bot = z0 + 0.013  # 坐落层板唇 (2mm 过盈=承重接触)
                for i in range(n_g):
                    if rng.random() < 0.03:
                        continue  # H9: 3% 缺位 (真实货架有人拿货后的空隙)
                    dist = abs((i + 0.5) / max(n_g, 1) - 0.5) * 2.0  # D33: 0=组心 1=组缘
                    irreg = 0.45 + 1.1 * dist ** 1.5  # 渐进不规则系数
                    # 真实 planogram 软件语义: 数据管结构(组/段/色), SKU 实宽管装箱
                    # 袋宽由高宽比定 (高=层高 0.62-0.72), 邻袋相触允许微溢 (参照: 满排相触)
                    x_bag = x0 + gw * (i + 0.5 + sh * 0.5) / max(n_g, 1) + (rng.random() - 0.5) * 0.02
                    y_bag = y_off + (rng.random() - 0.5) * 0.035 * irreg + (0.014 if rng.random() < 0.12 * irreg else 0.0)
                    if rng.random() < 0.30 * irreg:
                        y_bag -= 0.038  # D31/D33: 前拉加深 (概率随组缘增强)
                    if g["form"] == "barrel":
                        # 设计路径前置 (桶罐标签也需要)
                        gidx0 = LV_GIDX.setdefault((lv, g["design_id"]), len(LV_GIDX))
                        style0 = gidx0 % 3
                        dpath0 = DESIGN_DIR / f"design_{gidx0:02d}_{style0}.png"
                        barrel_placeholder(f"barrel{lv}_{r_i}_{i}", x_bag, y_bag, z_bot, rgb,
                                           dia=min(0.085, bgw * 0.92), hgt=LEVEL_H * 0.78,
                                           rng=rng, tex_path=dpath0 if dpath0.exists() else None)
                        continue
                    if g["form"] == "box":
                        box_placeholder(f"box{lv}_{r_i}_{i}", x_bag, y_bag, z_bot, rgb,
                                        bw_=min(0.12, bgw * 0.92))
                        continue
                    # H12: 组独立印刷设计 (bag_print, 组=SKU 设计一对一)
                    gidx, style, dpath = gidx0, style0, dpath0
                    # H15: H3-Image AI 直出印刷优先 (assets/ai_prints/<味key>.png, 768×1707)
                    if not dpath.exists():
                        dpath.parent.mkdir(parents=True, exist_ok=True)
                        ai_src = ROOT / f"assets/ai_prints/{AI_FLAVOR_KEY.get(FLAVORS[gidx % len(FLAVORS)], '')}.png"
                        if ai_src.exists():
                            shutil.copyfile(ai_src, dpath)
                    if not dpath.exists():
                        dpath.parent.mkdir(parents=True, exist_ok=True)
                        col = FAMILY_RGB[g["color"]]  # 数据层色彩守 planogram
                        patch = FOOD_PATCHES[gidx % len(FOOD_PATCHES)]
                        tint = FLAVOR_TINT.get(FLAVORS[gidx % len(FLAVORS)])
                        base = render_print(768, col, FLAVORS[gidx % len(FLAVORS)],
                                            seed=gidx * 7 + 3, food_img=patch, tint=tint,
                                            H=1707)  # v35 教训: 原生竖版 (ar≈0.45 真实薯片袋)
                        if style == 1:
                            # 极简: 40% 去饱和 + 大色块徽标带 (brand-minimal 体系)
                            from PIL import ImageEnhance
                            base = ImageEnhance.Color(base).enhance(0.72)
                            from PIL import ImageDraw as _D
                            _d = _D.Draw(base)
                            _d.rectangle([0, int(1707 * 0.34), 768, int(1707 * 0.46)],
                                         fill=(38, 41, 46))
                            _f = _load_font_cn(int(768 * 0.085))
                            _d.text((768 / 2, int(1707 * 0.41)), "TOPPRISM",
                                    fill=(245, 245, 242), font=_f, anchor="mm")
                        elif style == 2:
                            # 牛皮纸哑光: 棕调乘色 + 强纸纹 (matte-kraft 体系)
                            from PIL import ImageEnhance
                            base = ImageEnhance.Color(base).enhance(0.4)
                            px = np.asarray(base, dtype=float)
                            kraft = px * np.array([1.06, 0.90, 0.72])
                            grain = np.random.default_rng(gidx).normal(0, 7.0, kraft.shape[:2])[..., None]
                            base = Image.fromarray(np.clip(kraft + grain, 0, 255).astype("uint8"))
                        base.save(dpath)
                    a = dpath
                    from PIL import ImageEnhance as _IE
                    _sat = Image.open(a)
                    _sat = _IE.Color(_sat).enhance(1.40)
                    _sat = _IE.Contrast(_sat).enhance(1.08)
                    _satp = dpath.with_suffix(".sat.png")
                    _sat.save(_satp)
                    a = _satp
                    ar = Image.open(a).width / Image.open(a).height
                    # 组内同 SKU=同尺寸定宽平铺 (v29b 教训: 随机尺寸破坏平铺 → 邻字叠印)
                    # 高度主导 (v35 教训: 宽度主导+窄 ar → 半高袋; 参照袋占层高 ~2/3)
                    h_bag = LEVEL_H * (0.72 + rng.random() * 0.08)  # G1修: 密排充满
                    w_bag = min(h_bag * ar, bgw * 0.99)
                    h_bag = w_bag / ar
                    clump = (i // 3) % 2 * 3.4 - 1.7  # D31: 受压簇加强 (1.1→1.7度)
                    lean = 6.5 if rng.random() < 0.05 else (11.0 if rng.random() < 0.05 else (2.6 if i in (2, 9) else (rng.random() - 0.5) * 3.2 * irreg + clump * irreg))  # D33: 倾角随组缘增强  # H11: 4% 强侧转
                    # D30: 布料库实例 (变体网格共享 + OBJECT 材质逐袋独立印刷)
                    vmesh = CLOTH_LIB[(gidx * 131 + i * 17 + r_i * 53 + lv * 29) % len(CLOTH_LIB)]  # D35: 素数扰动破阵列感
                    co = bpy.data.objects.new(f"bag{lv}_{r_i}_{g['design_id']}_{i}", vmesh)
                    co.location = (max(x0 + w_bag / 2, min(x0 + gw - w_bag / 2, x_bag)),
                                   y_bag, z_bot + h_bag / 2)
                    pitch_x = (rng.random() - 0.5) * 2.4 + (7.0 + rng.random() * 6.0 if r_i == 1 else 0.0)  # D34: 二排前倾压前排
                    co.rotation_euler = (math.radians(pitch_x), 0, math.radians(lean))
                    if r_i == 1:
                        co.location.y += 0.022  # D34: 整排前移 2.2cm (顶靠前排背)
                    co.scale = (w_bag / 0.095 * (0.98 + rng.random() * 0.04),
                               1.0, h_bag / 0.19 * (0.97 + rng.random() * 0.06))  # D35: 逐袋轮廓微差
                    bpy.context.scene.collection.objects.link(co)
                    sl = co.material_slots[0]
                    sl.link = 'OBJECT'
                    sl.material = bag_material(f"bagm_{lv}_{r_i}_{i}", Path(a),
                                               (0.10 if rng.random() < 0.22 else 0.28) + rng.random() * 0.30, 0.02)
                    # D32: 排尾簇 (12% 组触发): 斜靠+前压袋 — 评审"局部成簇不规则堆叠"
                    if i == n_g - 1 and rng.random() < 0.12 and g.get("form", "bag") == "bag":
                        for k, (yaw_k, dy_k, pitch_k) in enumerate(
                                ((16.0 + rng.random() * 14.0, -0.020, 5.0 + rng.random() * 4.0),
                                 (-13.0 - rng.random() * 11.0, -0.038, 9.0 + rng.random() * 5.0))):
                            ce = bpy.data.objects.new(f"bagc{lv}_{r_i}_{g['design_id']}_{i}_{k}", vmesh)
                            ce.location = (min(x0 + gw - w_bag * 0.35, x_bag + (rng.random() - 0.25) * 0.02),
                                           y_bag + dy_k, z_bot + h_bag / 2 - k * 0.004)
                            ce.rotation_euler = (math.radians(pitch_k), 0, math.radians(lean + yaw_k))
                            ce.scale = (w_bag / 0.095, 1.0, h_bag / 0.19)
                            bpy.context.scene.collection.objects.link(ce)
                            sl2 = ce.material_slots[0]
                            sl2.link = 'OBJECT'
                            sl2.material = bag_material(f"bagcm_{lv}_{r_i}_{i}_{k}", Path(a),
                                                        0.30 + rng.random() * 0.25, 0.02)
        # 层间背光带 (EEVEE 自发光不照明 → 需真光源; 朝袋背面)
        bl = bpy.data.lights.new(f"back{lv}", "AREA")
        bl.size = SHELF_W * 0.95; bl.size_y = LEVEL_H * 0.7; bl.energy = 8
        blo = bpy.data.objects.new(f"back{lv}", bl)
        blo.location = (0, DEPTH - 0.10, z0 + LEVEL_H / 2)
        blo.rotation_euler = (math.radians(-90), 0, 0)
        sc.collection.objects.link(blo)
        # 层板下沿灯带 (补层板唇高光)
        lt = bpy.data.lights.new(f"strip{lv}", "AREA")
        lt.color = (1.0, 0.92, 0.82)  # D37: 商店LED暖化 4300K
        lt.size = SHELF_W * 0.9; lt.size_y = 0.05
        lt.energy = 24 * (0.48 + 1.20 * ((lv * 0.37 + 0.11) % 1.0))  # D38: 层间光差 ±60% (明暗层次加深)
        if lv % 3 == 1:
            lt.color = (1.0, 0.96, 0.90)  # D38: 冷暖混光 (隔层偏中性)
        strip_x = ((lv * 0.53 + 0.29) % 1.0 - 0.5) * 0.34  # H7: 灯位横移加大 (不均匀光带)
        lo = bpy.data.objects.new(f"strip{lv}", lt)
        lo.location = (strip_x, DEPTH - 0.10, z0 + 0.05)
        lo.rotation_euler = (math.radians(-70), 0, 0)
        sc.collection.objects.link(lo)

    # 环境组 (Lowe's 实证: 立体感=环境完整度 天花板+可见灯具+洞洞板端墙+金属立柱)
    top_z = SHELVES * LEVEL_H
    # 天花板
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, DEPTH / 2 + 1.2, top_z + 0.62))
    cl = bpy.context.active_object; cl.name = "ceiling"
    cl.scale = (SHELF_W / 2 + 1.2, 2.6, 0.02)
    cm = bpy.data.materials.new("ceil"); cm.use_nodes = True
    cm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.93, 0.93, 0.95, 1)
    cm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.5
    cl.data.materials.append(cm)
    # 荧光灯灯具 ×3 (可见外壳+发光底面) — Lowe's 实证: 灯具模型是第一立体线索
    for fx in (-0.7, 0.0, 0.7):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(fx, 0.5, top_z + 0.48))
        fxo = bpy.context.active_object; fxo.name = f"fixture{fx}"
        fxo.scale = (0.55, 0.09, 0.035)
        fm = bpy.data.materials.new(f"fxf{fx}"); fm.use_nodes = True
        fxb = fm.node_tree.nodes["Principled BSDF"]
        fxb.inputs["Base Color"].default_value = (0.95, 0.95, 0.97, 1)
        fxb.inputs["Emission Color"].default_value = (1.0, 0.98, 0.94, 1)
        fxb.inputs["Emission Strength"].default_value = 6.0
        fxo.data.materials.append(fm)
    # 左端洞洞板墙 (封虚空; Lowe's pegboard 实证)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-SHELF_W / 2 - 0.45, DEPTH / 2 + 0.8, top_z / 2))
    pb = bpy.context.active_object; pb.name = "pegboard"
    pb.rotation_euler = (0, math.radians(90), 0)
    pb.scale = (top_z / 2 + 0.6, 2.6, 1)
    pm = bpy.data.materials.new("pegm"); pm.use_nodes = True
    pmb = pm.node_tree.nodes["Principled BSDF"]
    pmb.inputs["Base Color"].default_value = (0.72, 0.73, 0.75, 1)
    pmb.inputs["Roughness"].default_value = 0.6
    pb.data.materials.append(pm)
    # 金属立柱 ×3 (货架段界, 真实龙门架语义)
    for ux in (-SHELF_W / 2 + 0.02, -SHELF_W / 6, SHELF_W / 6):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(ux, -0.02, top_z / 2))
        up = bpy.context.active_object; up.name = f"upright{ux}"
        up.scale = (0.022, 0.03, top_z / 2 + 0.08)
        um = bpy.data.materials.new(f"upm{ux}"); um.use_nodes = True
        ub = um.node_tree.nodes["Principled BSDF"]
        ub.inputs["Base Color"].default_value = (0.62, 0.64, 0.66, 1)
        ub.inputs["Metallic"].default_value = 0.85
        ub.inputs["Roughness"].default_value = 0.35
        up.data.materials.append(um)

    # 顶部射灯 ×4: 一主三辅 (H1: 定向主光替代平光, 杠杆#2)
    for i, x in enumerate((-0.9, -0.3, 0.3, 0.9)):
        lt = bpy.data.lights.new(f"spot{i}", "SPOT")
        if i == 1:
            lt.energy = 920; lt.spot_size = math.radians(38); lt.shadow_soft_size = 0.14  # D39: 软影保高光
            lt.color = (1.0, 0.96, 0.90)  # D37: 主光微暖
            # 5.2 EEVEE Next: contact_shadow 已移除 (阴影由 RT 阴影覆盖)
        elif i == 2:
            lt.energy = 38; lt.spot_size = math.radians(38)   # H7: 右辅光压暗 (光比不均=局部阴影)
        else:
            lt.energy = 60; lt.spot_size = math.radians(55)  # D38: 辅光再压 (光比加深)
        lo = bpy.data.objects.new(f"spot{i}", lt)
        lo.location = (x, -0.7, SHELVES * LEVEL_H + 0.55)
        aim = Vector((x * 0.6, DEPTH / 2, 1.0)) - lo.location
        lo.rotation_euler = aim.to_track_quat('-Z', 'Y').to_euler()
        sc.collection.objects.link(lo)

    # 前置柔光 (H6: 再杀到 7W, 暗部份额对靶)
    fl = bpy.data.lights.new("frontfill", "AREA")
    fl.size = 2.2; fl.size_y = 1.2; fl.energy = 7
    flo = bpy.data.objects.new("frontfill", fl)
    flo.location = (0, -1.1, 1.5)
    flo.rotation_euler = (math.radians(65), 0, 0)
    sc.collection.objects.link(flo)

    # 人位相机 (primary.jpg 对齐: 站右端向左纵深看, 左远右近, 广角手机视场, 微滚转)
    cam = bpy.data.cameras.new("c"); cam.lens = 26
    co = bpy.data.objects.new("c", cam)
    co.location = (0.55, -1.85, 1.44)
    aim = Vector((-0.15, DEPTH / 2, 1.21)) - co.location
    rot = aim.to_track_quat('-Z', 'Y').to_euler()
    rot.rotate_axis('Y', math.radians(-2.0))  # 微滚转
    co.rotation_euler = rot
    sc.collection.objects.link(co); sc.camera = co

    # 前景挂架 v2 (对齐②清单: 细圆管/挂杆/挂钩/垂坠袋)
    hooks = build_pyramid_rack_v2((-0.05, -1.08))
    rack_bags = [ASSETS[2], ASSETS[5], ASSETS[9]]
    for hi, (hx, hy, hz, k) in enumerate(hooks):
        img_plane(f"rbag{k}_{hi}", crop_bag(rack_bags[(hi + k) % 3], seed=70 + hi),
                  0.062, 0.092, (hx, hy - 0.002, hz - 0.05),
                  rot=(0, 0, (hash((hi, k)) % 7 - 3) * 0.6), emissive=0.12, rough=0.45)

    if "--clay" in argv:
        apply_clay_override()
    sc.render.filepath = str(OUT)
    bpy.ops.render.render(write_still=True)
    print("HXL_SHELF_OK", OUT)


if __name__ == "__main__":
    main()
