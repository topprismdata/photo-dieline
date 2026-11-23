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
import os
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
ROW_CHAINS = {}  # V37-B2: (lv, r_i, design_id) -> [bag objs] 行内链式打包
ROW_SPANS = {}   # V37-B2: (lv, r_i, design_id) -> (x0, gw) 组原span
ORIG36 = {}      # V38: 打包前 V36 位置快照 (name -> (x, y))
BOX_FRONT_CACHE = {}  # V46: 盒面合成缓存 (design path -> composed png)
BOX_BODY_COLOR = {}  # V47: 盒体色 = 设计边色均值 (消贴纸感)
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
    LIP = _pj["calibration"].get("bottom_lip_mm", 450) / 1000.0  # M31 标定底唇 450mm (FTC 拟合同基准)
    print(f"[planogram] LEVEL_H={LEVEL_H:.3f} SHELVES={SHELVES} LIP={LIP:.3f} (标定驱动)")
else:
    SHELVES, LEVEL_H, SHELF_W, DEPTH, LIP = 7, 0.38, 2.4, 0.40, 0.45
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
    """V59: 价签轨贴图 — 对齐参照实拍电子价签: 条码块 + 大整数位红价 + 上标小数角标 (2⁹), 组间细分隔.
    画布宽高比 = 轨平面 2.36m/52mm ≈ 45.4 (文字不拉伸); 原灰码行删除 (成片尺度不可读, 只添噪)."""
    import random
    from PIL import Image, ImageDraw, ImageFont
    W, H = 8192, 180
    im = Image.new("RGB", (W, H), (253, 253, 251))
    d = ImageDraw.Draw(im)
    try:
        f_i = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", int(H * 0.62), index=0)
        f_d = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", int(H * 0.36), index=0)
    except Exception:
        f_i = f_d = ImageFont.load_default()
    rng = random.Random(seed_lv * 17 + 3)
    x = 0.0
    for gi, (fr, pr) in enumerate(zip(fracs, prices)):
        w = int(fr * W)
        if rng.random() < 0.10:
            x += w  # 空洞段 (轨上无签, 补货语义)
            continue
        w = int(w * (0.82 + rng.random() * 0.18))
        # 条码块 (随机宽度黑白竖线)
        cx = x + w * 0.06
        while cx < x + w * 0.20:
            lw = rng.choice((5, 8, 12))
            d.rectangle([cx, H * 0.16, cx + lw, H * 0.84], fill=(22, 22, 24))
            cx += lw + rng.choice((7, 10, 14))
        # 红价: 整数位大字 + 上标小数角标
        ip, _, dp = pr.partition(".")
        tx = x + w * 0.30
        d.text((tx, H * 0.80), ip, font=f_i, fill=(172, 8, 14), anchor="ls")
        if dp:
            d.text((tx + d.textlength(ip, font=f_i) + H * 0.03, H * 0.46), dp, font=f_d, fill=(172, 8, 14), anchor="ls")
        # 组间分隔
        if gi < len(fracs) - 1:
            d.line([x + w, 0, x + w, H], fill=(150, 152, 156), width=4)
        x += w
    # 顶部装卡阴影线 + 轨底沿
    d.rectangle([0, 0, W, 5], fill=(214, 215, 218))
    d.rectangle([0, H - 4, W, H], fill=(196, 197, 200))
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
    bsdf.inputs["Coat Weight"].default_value = 0.10
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
    r = rng if rng is not None else np.random.default_rng(__import__('zlib').crc32(name.encode()) % (2**32))  # V28修: hash()跨进程随机→crc32定种
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
        tex.image = bpy.data.images.load(str(can_label(Path(tex_path), math.pi * dia / hgt)))
        nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
        b.inputs["Roughness"].default_value = 0.34
    o.data.materials.append(m)
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


def box_placeholder(name, x, y, z_bot, rgb, bw_=0.12, hgt=0.19, front_tex=None):
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
    if front_tex:
        # V45: 盒装正面印刷 (TOPPRISM 设计族 — 同组设计, 品牌一致非虚构)
        fm = bpy.data.materials.new(name + "_front")
        fm.use_nodes = True
        fnt = fm.node_tree
        fb = fnt.nodes["Principled BSDF"]
        fb.inputs["Roughness"].default_value = 0.35
        ftex = fnt.nodes.new("ShaderNodeTexImage")
        ftex.image = bpy.data.images.load(str(front_tex))
        fhs = fnt.nodes.new("ShaderNodeHueSaturation")
        fhs.inputs["Saturation"].default_value = 1.15
        fnt.links.new(ftex.outputs["Color"], fhs.inputs["Color"])
        fnt.links.new(fhs.outputs["Color"], fb.inputs["Base Color"])
        front.data.materials.append(fm)
    else:
        mm = bpy.data.materials.new(name + "_front")
        mm.use_nodes = True
        mm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.94, 0.93, 0.90, 1)
        front.data.materials.append(mm)


def _legacy_tray_rng(rng, lean):
    """V60 冻结种子纪律: 只回放 V30 托盘填充对层级 rng 的抽取序列 (不建对象).
    层级 rng 跨组顺序消费 — 抽取次数一变, 同层其余商品的随机态全部重排; 回放后与 V59 逐位一致."""
    if lean:
        nb_back = int(rng.integers(3, 6))
        nb_front = int(rng.integers(2, 5))
        slots = [(1, k) for k in range(nb_back)] + [(0, k) for k in range(nb_front)]
        if rng.random() < 0.4 and len(slots) > 4:
            slots.pop(int(rng.integers(0, len(slots))))
        for back, k in slots:
            if not back:
                rng.random()  # zz
            rng.random()      # bh3
            if not back:
                rng.random()  # 前探判定
            rng.random(); rng.random()  # rot
    else:
        for st in range(2):
            n = int(rng.integers(3, 7))
            for k in range(n):
                rng.random(); rng.random()  # rz, ox


def tray_carton(name, cx, y, z_bot, bw_, dep=0.26, hgt=0.055, front_tex=None):
    """开箱陈列纸托 (V60): 浅口牛皮箱体 + 浅色切口沿 + 印花前裙, 箱内立式袋 (参照实拍下层开箱直立陈列).
    替 V30 藤编篮: primitive_cube_add(size=1)+半长 scale 致篮体半尺寸、沿口板悬空 37mm、平叠煎饼埋在篮体内;
    size=2 恢复设计尺寸后 150mm 篮体会把填充全埋住 → 改 55mm 浅口."""
    kraft = bpy.data.materials.new(name + "_k")
    kraft.use_nodes = True
    kb = kraft.node_tree.nodes["Principled BSDF"]
    kb.inputs["Base Color"].default_value = (0.66, 0.51, 0.32, 1)
    kb.inputs["Roughness"].default_value = 0.8
    edge = bpy.data.materials.new(name + "_e")
    edge.use_nodes = True
    eb = edge.node_tree.nodes["Principled BSDF"]
    eb.inputs["Base Color"].default_value = (0.84, 0.74, 0.58, 1)
    eb.inputs["Roughness"].default_value = 0.85
    bpy.ops.mesh.primitive_cube_add(size=2, location=(cx, y, z_bot + hgt / 2))
    body = bpy.context.active_object
    body.name = name
    body.scale = (bw_ / 2, dep / 2, hgt / 2)
    body.data.materials.append(kraft)
    # 沿口条顶面须高出箱体顶面 1mm: 完全共面的两个面在 Cycles 里互相自遮挡 → 顶面整片发黑 (单箱探针实证)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(cx, y, z_bot + hgt - 0.0035))
    rim = bpy.context.active_object
    rim.name = name + "_rim"
    rim.scale = (bw_ / 2 + 0.003, dep / 2 + 0.003, 0.0045)
    rim.data.materials.append(edge)
    if front_tex:
        fh = hgt - 0.010  # 印花前裙: 上留切口沿 8mm, 下留 2mm
        img_plane(name + "_front", front_tex, bw_ - 0.006, fh, (cx, y - dep / 2 - 0.002, z_bot + fh / 2 + 0.001),
                  emissive=0.10, rough=0.55)


def tray_upright_fill(name, cx, y_in, z_bot, bw_, dpath, rng, back, full):
    """箱内单排立式袋 (V60): 槽数由箱宽定; full=False 随机缺位 1-2 (lean 组, V31 拿货语义); 后排更后仰、前排微仰;
    逐袋高低差 (V31 语义保留). 袋底落在箱体内, 自箱口露出."""
    bw2 = min(0.10, bw_ / 4.4)
    bh2 = bw2 * 1.55
    nb = max(1, int((bw_ - 0.03) / (bw2 + 0.012)))
    miss = set()
    if not full and nb > 2:
        miss = set(int(i) for i in rng.choice(nb, size=int(rng.integers(1, min(3, nb))), replace=False))
    for k in range(nb):
        if k in miss:
            continue
        xx = cx + (k - (nb - 1) / 2) * (bw2 + 0.012)
        bh3 = bh2 * (0.84 + rng.random() * 0.30)  # V31: 逐袋高低差
        lean = (14 + rng.random() * 8) if back else (5 + rng.random() * 7)
        yy = y_in + (0.065 if back else -0.028) + (rng.random() - 0.5) * 0.008
        zb = z_bot + 0.012 + rng.random() * 0.008
        img_plane(f"{name}_l{int(back)}{k}", dpath, bw2, bh3,
                  (xx, yy, zb + bh3 * 0.5 * math.cos(math.radians(lean))),
                  rot=(-lean, 0, (rng.random() - 0.5) * 16), emissive=0.10, rough=0.5)


TIGHT_CACHE = {}  # V52: 设计紧裁缓存 (stem -> Path)


def _tight_box(a):
    """V54: 自适应紧裁框 — packshot 边缘阴影梯度会骗过单一阈值致紧裁 no-op (白翼残留);
    th 阶梯 60→90→120, 边界离开画布边即接受 (封顶 120: 保住近白袋身 vs 米色背景 dist≈129)."""
    e = np.concatenate([a[:, :24], a[:, -24:]], axis=1)
    bg = np.median(e.reshape(-1, 3)[::7], axis=0)
    d = np.abs(a - bg[None, None, :]).sum(-1)
    H, W = d.shape
    box = (0, 0, W, H)
    for th in (60, 90, 120):
        ys, xs = np.where(d > th)
        if len(xs) <= 100:
            continue
        x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
        box = (max(x0 - 6, 0), max(y0 - 6, 0), min(x1 + 7, W), min(y1 + 7, H))
        if not (x0 <= 2 or y0 <= 2 or x1 >= W - 3 or y1 >= H - 3):
            break
    return box


def _edge_extend(arr, th=90):
    """V57: 背景连通泛洪 + 行/列最近邻延展 — packshot 袋型有腰身/收窄, bbox 内剪影凹陷处仍为米色,
    袋侧/背面采样到即成白板. 只有与画布边缘连通的背景状像素才算背景 (袋内浅色薯片/白带不动 —
    V52b/V57 两次逐行条纹事故的根因正是把袋内浅色当背景); 背景像素用同行 (无则同列) 最近袋身像素填充."""
    a = arr.copy()
    H, W, _ = a.shape
    e = np.concatenate([arr[:, :24], arr[:, -24:]], axis=1)
    bg = np.median(e.reshape(-1, 3)[::7], axis=0)
    bglike = np.abs(arr - bg[None, None, :]).sum(-1) <= th
    B = np.zeros((H, W), bool)
    B[0, :] = bglike[0, :]; B[-1, :] = bglike[-1, :]
    B[:, 0] |= bglike[:, 0]; B[:, -1] |= bglike[:, -1]
    for _ in range(max(H, W)):
        D = B.copy()
        D[1:, :] |= B[:-1, :]; D[:-1, :] |= B[1:, :]
        D[:, 1:] |= B[:, :-1]; D[:, :-1] |= B[:, 1:]
        D &= bglike
        if (D == B).all():
            break
        B = D
    rr = np.broadcast_to(np.arange(H)[:, None], (H, W))
    cc = np.broadcast_to(np.arange(W)[None, :], (H, W))
    xs = np.arange(W)
    lidx = np.maximum.accumulate(np.where(~B, xs[None, :], -1), axis=1)
    ridx = np.minimum.accumulate(np.where(~B, xs[None, :], W)[:, ::-1], axis=1)[:, ::-1]
    has_row = (lidx >= 0) | (ridx < W)
    src = np.where((lidx >= 0) & ((ridx >= W) | (xs[None, :] - lidx <= ridx - xs[None, :])), lidx, ridx)
    m1 = B & has_row
    a[m1] = a[rr[m1], np.clip(src, 0, W - 1)[m1]]
    m2 = B & ~has_row          # 整行无袋身 (顶/底边距行): 同列最近袋身像素
    if m2.any():
        ys = np.arange(H)
        uidx = np.maximum.accumulate(np.where(~B, ys[:, None], -1), axis=0)
        didx = np.minimum.accumulate(np.where(~B, ys[:, None], H)[::-1, :], axis=0)[::-1, :]
        pick = np.where((uidx >= 0) & ((didx >= H) | (ys[:, None] - uidx <= didx - ys[:, None])), uidx, didx)
        a[m2] = a[np.clip(pick, 0, H - 1)[m2], cc[m2]]
    # 填充区纵向平滑 (窗 41): 逐行取边缘色受阴影影响成横带, 侧面采样会显条纹
    k = 20
    cs = np.cumsum(np.pad(a, ((k + 1, k), (0, 0), (0, 0))), axis=0)
    sm = (cs[2 * k + 1:] - cs[:-2 * k - 1]) / (2 * k + 1)
    a[B] = sm[B]
    return a


def tight_crop(png: Path) -> Path:
    """V52: 紧裁 packshot 到剪影 — 摄影米色边距直接卷上 barrel/托盘/瓶面成"白翼" (根因修).
    bag 路径经 sat 后用 _tight_box 内联紧裁; 此 helper 服务直用 dpath0 的分支."""
    out = png.with_suffix(".tight.png")
    if out.exists():
        return out
    im = Image.open(png).convert("RGB")
    cropped = im.crop(_tight_box(np.asarray(im, float)))
    Image.fromarray(np.clip(_edge_extend(np.asarray(cropped, float)), 0, 255).astype("uint8")).save(out)
    return out

CAN_CACHE = {}  # V58: 罐标合成缓存 ((紧裁 packshot, 周高比) -> Path)


def can_label(src: Path, wrap_ar: float, panels: int = 2, rims: bool = True, tile_h: int = 0, band: float = 0.0) -> Path:
    """V58: 设计条带合成 — packshot 裁掉两侧条纹边距后以原生像素宽高比多联平铺, 余宽用袋身色缝填满.
    整张 packshot 绕圆柱一圈会把文字横向拉 2 倍+ (周长/高 0.93-1.10 vs 贴图 0.446; V57 左下罐 TOPPRISM 摊成巨幅环带).
    边距: 紧裁框按最宽行 (封口鳍) 定, 袋身两侧留 V57 逐行延展的条纹带 → 按水平梯度裁到核心列.
    缝色: 每行中央 50% 列的中位色 (袋身真印刷, 不含剪影阴影) 再纵向平滑 → [P][缝]×n, 首尾同为 P 左缘 → 全周无接缝、无镜像文字.
    罐身 (默认): 双联 + 顶/底各 2.5% 金属缘 (参照实拍 primary.jpg: 真罐满印 flavor 色, 无白环带, 设计绕罐重复).
    V60: panels=0 按宽高比自动定联数, rims=False 去金属缘, tile_h 降输出高, band>0 只取顶部品牌带作面板 — 供纸托前裙等宽幅载体
    (整幅 packshot 密铺成 44 联微型图 = 噪点墙; 品牌带宽高比≈1.6, 69cm 裙约 10 联, 字可读)."""
    key = (str(src), round(wrap_ar, 4), panels, rims, tile_h, band)
    if key in CAN_CACHE:
        return CAN_CACHE[key]
    a = np.asarray(Image.open(src).convert("RGB"), dtype=float)
    th, tw = a.shape[:2]
    # 条纹边距裁切: 紧裁框含剪影外软阴影带 (延展后逐行平色 = 横条纹, 右侧宽 19-27%), 按水平梯度找袋身核心列区间
    body = a[int(th * 0.10):int(th * 0.90)].mean(axis=2)
    g = np.convolve(np.abs(np.diff(body, axis=1)).mean(axis=0), np.ones(31) / 31, mode="same")
    d = np.diff(np.concatenate([[0], (g > 1.2).astype(int), [0]]))
    runs = [(s, e) for s, e in zip(np.where(d == 1)[0], np.where(d == -1)[0]) if e - s >= max(9, tw // 30)]
    cx0, cx1 = (int(runs[0][0]), int(runs[-1][1]) + 1) if runs else (0, tw)
    if cx1 - cx0 < tw * 0.45:
        cx0, cx1 = 0, tw
    a = a[:, cx0:cx1]
    oh = tile_h if tile_h > 0 else th  # 输出高
    rim = int(round(oh * 0.025)) if (rims and band <= 0) else 0
    ih = oh - 2 * rim
    tile = np.asarray(Image.fromarray(a.astype("uint8")).resize(
        (max(2, int(round(a.shape[1] * ih / th))), ih), Image.LANCZOS), dtype=float)
    if band > 0:  # V60 纸托前裙: 只取顶部品牌带 (TOPPRISM+口味名) 作面板, 输出高随之取面板高
        tile = tile[:max(8, int(round(ih * band)))]
        oh = tile.shape[0]
    n = panels if panels > 0 else max(2, int(round(wrap_ar / (tile.shape[1] / tile.shape[0]))))
    W = max(n * tile.shape[1] + n, int(round(wrap_ar * oh)))
    gap = W - n * tile.shape[1]
    rowcol = np.median(tile[:, tile.shape[1] // 4:tile.shape[1] * 3 // 4], axis=1)[:, None, :]
    k = max(1, tile.shape[0] // 6)
    cs = np.cumsum(np.pad(rowcol, ((k + 1, k), (0, 0), (0, 0))), axis=0)
    seam = (cs[2 * k + 1:] - cs[:-2 * k - 1]) / (2 * k + 1)  # 缝色纵向平滑 (窗 2k+1)
    parts = []
    for i in range(n):
        parts += [tile, np.repeat(seam, gap // n + (1 if i >= n - gap % n else 0), axis=1)]  # 余数给末几缝
    mid = np.concatenate(parts, axis=1)
    if rim:
        out = np.empty((oh, W, 3))
        out[rim:rim + ih] = mid
        metal = np.linspace(168.0, 205.0, rim)[:, None, None] * np.ones((1, W, 1))  # 顶/底金属缘竖向微渐变
        out[:rim] = metal
        out[rim + ih:] = metal[::-1]
    else:
        out = mid
    dst = src.with_name(src.stem.replace(".tight", "") + f".can{wrap_ar:.3f}"
                        + ("" if (panels == 2 and rims and not tile_h and band <= 0)
                           else f".p{panels}r{int(rims)}h{tile_h}b{band:.2f}") + ".png")
    Image.fromarray(np.clip(out, 0, 255).astype("uint8")).save(dst)
    CAN_CACHE[key] = dst
    return dst


def bag_material(name, tex_path, rough=0.4, emissive=0.06, uv_rot=0.0, uv_scale=1.0, uv_tr=(0.0, 0.0), warp=0.0,
                 coat_w=0.10, coat_r=0.28, bump_s=0.0):
    """D30: 印刷材质 (从 img_bag_curved 抽出, 供布料库实例 OBJECT-link 复用).
    V41: 印刷重复感去重 — 逐袋 UV 微旋转/缩放/平移 + 噪声非刚性微变形 (同 SKU 官方设计不变)."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Coat Weight"].default_value = coat_w    # V42: 逐袋膜面反射微差异
    bsdf.inputs["Coat Roughness"].default_value = coat_r
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 620.0
    nz.inputs["Detail"].default_value = 4.0
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["To Min"].default_value = 0.93
    ramp.inputs["To Max"].default_value = 1.0
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(tex_path))
    if abs(uv_rot) > 1e-6 or abs(uv_scale - 1.0) > 1e-6 or abs(uv_tr[0]) > 1e-6 or abs(uv_tr[1]) > 1e-6 or warp > 1e-6:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(uv_rot))
        mp.inputs["Scale"].default_value = (uv_scale, uv_scale, 1.0)
        mp.inputs["Location"].default_value = (uv_tr[0], uv_tr[1], 0.0)
        nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
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
    if bump_s > 1e-4:
        bp = nt.nodes.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = bump_s   # V42: 逐袋微起伏强度差异
        nt.links.new(nz.outputs["Fac"], bp.inputs["Height"])
        nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
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
            # V55: 侧条面 UV 内缩 — 袋身鼓胀时圆润侧面只采样纹理边缘列 (u=0/1),
            #     packshot 剪影边列多为米色 → "白翼"第二来源 (barrel 连续环绕 UV 无此问题)
            side = all(abs(abs(l.vert.co.x) - BW / 2) < 1e-9 for l in f.loops)
            for l in f.loops:
                u, v = (l.vert.co.x + BW/2) / BW, l.vert.co.z / BH
                if side:
                    u = 0.04 if l.vert.co.x < 0 else 0.96
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


def drop_to_surface(co, z_target):
    """V28 陈列物理: 旋转/缩放后世界包围盒最低点沉降到 z_target (倾角袋底角悬浮修)."""
    bpy.context.view_layer.update()
    zmin = min((co.matrix_world @ Vector(c)).z for c in co.bound_box)
    co.location.z += z_target - zmin


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
    _res = float(os.environ.get("HXL_RES", "1"))  # V51: 分辨率倍率 (逐SKU印刷优化底座)
    sc.render.resolution_x, sc.render.resolution_y = int(720 * _res), int(1044 * _res)
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
              (0, DEPTH - 0.05, LIP + SHELVES * LEVEL_H / 2), emissive=1.1)

    # 招牌横带 (货架顶沿连体; 0.50m 薄条 — v19 实证 0.62 过高致顶裁切, A 实拍 ~0.5m)
    img_plane("sign", pil_tex_sign(), SHELF_W, 0.50,
              (0, DEPTH - 0.04, LIP + SHELVES * LEVEL_H + 0.25), emissive=1.2)
    # V28: 灯箱体 (横幅非卡片 — 12cm 深盒, 侧/背面深红哑光; context 实拍结构)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, DEPTH + 0.04, LIP + SHELVES * LEVEL_H + 0.25))  # V28修: y+侧=架后(相机y=-1.2, 小y=前), 盒在印刷面/背墙后
    sbx = bpy.context.active_object
    sbx.name = "signbox"
    sbx.scale = (SHELF_W / 2 + 0.01, 0.05, 0.25)  # 前面 DEPTH-0.07, 距印刷面 3cm 防 z-fight
    msx = bpy.data.materials.new("signbox_m"); msx.use_nodes = True
    _sb = msx.node_tree.nodes["Principled BSDF"]
    _sb.inputs["Base Color"].default_value = (0.45, 0.07, 0.06, 1)
    _sb.inputs["Roughness"].default_value = 0.35
    sbx.data.materials.append(msx)
    # 吊装杆 ×3 (饰带→灯箱顶; context 实拍横幅吊装结构)
    for hx in (-SHELF_W / 3, 0.0, SHELF_W / 3):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.006, depth=0.16,
                                            location=(hx, DEPTH + 0.04, LIP + SHELVES * LEVEL_H + 0.58))
        rod = bpy.context.active_object
        rod.name = f"signrod_{hx:.2f}"
        mr = bpy.data.materials.new("rod_m"); mr.use_nodes = True
        _rb = mr.node_tree.nodes["Principled BSDF"]
        _rb.inputs["Base Color"].default_value = (0.10, 0.10, 0.11, 1)
        _rb.inputs["Metallic"].default_value = 0.6
        _rb.inputs["Roughness"].default_value = 0.4
        rod.data.materials.append(mr)
    # 饰带 (红色灯箱长带, 横幅吊其下; 帧上缘仅露下沿 — 同 A 原图顶部裁切)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, DEPTH + 0.04, LIP + SHELVES * LEVEL_H + 0.80))
    fasc = bpy.context.active_object
    fasc.name = "fascia"
    fasc.scale = (SHELF_W / 2 + 0.01, 0.055, 0.16)
    mf = bpy.data.materials.new("fascia_m"); mf.use_nodes = True
    _fb = mf.node_tree.nodes["Principled BSDF"]
    _fb.inputs["Base Color"].default_value = (0.55, 0.09, 0.07, 1)
    _fb.inputs["Roughness"].default_value = 0.3
    _fb.inputs["Emission Color"].default_value = (0.55, 0.09, 0.07, 1)
    _fb.inputs["Emission Strength"].default_value = 0.55
    fasc.data.materials.append(mf)

    # 层板 + 前唇 + 排面 + 价签
    tag_texts = ["2.9", "4.9", "5.8", "5.9", "7.2", "1.7", "3.5"]
    bag_names = [a.stem for a in ASSETS]
    # ESR Step C: 加载陈列表 (数据驱动布局; 场景只留夹具/灯光/相机)
    PLAN = json.loads((ROOT / "data/shelf_twin/planogram.json").read_text())
    # D30: 布料压力袋变体库 (48 网格 × 逐实例 OBJECT 印刷 = 无重复组合)
    build_cloth_library(n_per=6)  # D35: 48→72变体

    for lv in range(SHELVES):
        z0 = LIP + lv * LEVEL_H  # P0#2 修: 底唇 450mm (v19 前层板从地面起排致相机瞄过架顶)
        # 层板 (白板)
        # V59: size=2 — size=1 立方体半边长 0.5, 而下一行 scale 是半长语义: 宽/深/厚曾全部只有一半
        #     (探针实测 1.2×0.2×11mm, 前排商品全悬在板前缘 y=0.1 之外, 底悬空 7.5mm)
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, DEPTH / 2, z0))
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
        norm = min(1.0, 34.0 / fac_sum)  # P0#2 密度: A 实拍满排 ~34 排面/层, 24 槽上限偏疏 (v20 实证)
        plan_lv = {**plan_lv, "groups": [{**g, "facings": max(1, round(g["facings"] * norm))}
                                         for g in plan_lv["groups"]]}
        # P0#2 漏检补偿: SKU-110K 臂对底层 (照片裁切区) facings 偏少, A 实拍底排满排 → 归一后 <14 槽按比例补足
        fac2 = sum(g["facings"] for g in plan_lv["groups"])
        if fac2 < 14:
            k2 = 14.0 / fac2
            plan_lv = {**plan_lv, "groups": [{**g, "facings": max(1, round(g["facings"] * k2))}
                                             for g in plan_lv["groups"]]}
        # D28: 连续轨内嵌逐组大数字 (轨底连续+段内大红价+空洞段)
        fracs = [g["width_frac"] for g in plan_lv["groups"]]
        fs = sum(fracs) or 1.0
        prices = [tag_texts[(lv + gi) % len(tag_texts)] for gi in range(len(fracs))]
        # V59: 价签轨贴层板前缘立面 (板沿 22mm + 板下唇 30mm = 52mm, 全层全视角最前). 原平面 0.15m 高悬在
        #     y=0.303 (板后沿), 被层板前立面从正中劈开 — 红价画在贴图 46% 高 = 层板高度 (ray_cast 竖线扫描实证)
        #     相机在 y=-1.2: 越负越靠前. 板前立面 y=0 → 轨须 y=-0.003 (写 +0.003 即塞进板体, 上 42% 被板面盖成灰带)
        img_plane(f"tagrail{lv}", pil_tag_rail([f / fs for f in fracs], prices, seed_lv=lv),
                  SHELF_W - 0.04, 0.052, (0, -0.003, z0 - 0.014), emissive=0.30)
        for r_i, (y_off, s0, sh) in enumerate(((DEPTH / 2 - 0.06, 1.0, 0.0),
                                               (DEPTH / 2 - 0.17, 0.92, 0.5))):
            for g in plan_lv["groups"]:
                j = int(g["design_id"].split("_")[1])
                rgb = FAMILY_RGB[g["color"]]
                gw = g["width_frac"] * SHELF_W
                x0 = g["x0_frac"] * SHELF_W - SHELF_W / 2 + (rng.random() - 0.5) * 0.02  # H10 组界横移
                n_g = max(1, g["facings"] + (1 if sh and g["facings"] > 2 else 0))
                ar_g = (0.40, 0.58)[(j * 7 + lv * 3) % 2]  # P0-3: 组级袋形 (细长/中宽; 0.95 档已证塌陷弃用)
                if g.get("form", "bag") == "bag":
                    if ar_g >= 0.58:
                        n_g = max(2, int(gw / (LEVEL_H * 0.62 * ar_g)))  # 宽袋: 槽数由袋形推导 (少而大; 检出 facings 不可靠)
                    else:
                        n_g = max(n_g, int(g["width_frac"] * SHELF_W / 0.072))  # 窄袋: 密度饥饿校正 (A L6/L7 满排 ~28)
                bgw = gw / n_g
                z_bot = z0 + 0.013  # 坐落层板唇 (2mm 过盈=承重接触)
                # V26: 设计索引前置 (托盘分支也需印刷贴图; 组级一次)
                gidx0 = LV_GIDX.setdefault((lv, g["design_id"]), len(LV_GIDX))
                style0 = gidx0 % 3
                dpath0 = DESIGN_DIR / f"design_{gidx0:02d}_{style0}.png"
                if g["form"].startswith("tray"):
                    # V60: 开箱陈列纸托 — 箱体只建一次 (r_i=0), 两次行循环各填一排 (后排/前排).
                    #     (V30 藤编篮在两次行循环里同名同位各建一遍 = 每托叠两只篮 + 两套卡片)
                    #     冻结种子纪律: 层级 rng 跨组顺序消费, 托盘只回放旧填充的抽取序列, 自身用独立种子
                    #     → 同层其余商品随机态与 V59 逐位一致.
                    nb = max(1, int(gw / 0.37))
                    bw_ = gw / nb - 0.025
                    y_c = 0.14
                    _lean = g["form"] == "tray_lean"
                    _tp = tight_crop(dpath0) if dpath0.exists() else None
                    for b in range(nb):
                        _legacy_tray_rng(rng, _lean)  # 逐箱回放 (与 V30 逐箱填充的抽取次序一致)
                        bx = x0 + gw * (b + 0.5) / nb
                        if r_i == 0:
                            tray_carton(f"tray{lv}_0_{b}", bx, y_c, z_bot, bw_,
                                        front_tex=can_label(_tp, (bw_ - 0.006) / 0.045, panels=0, tile_h=400, rims=False, band=0.22) if _tp else None)
                        tray_upright_fill(f"tray{lv}_0_{b}", bx, y_c, z_bot, bw_, _tp,
                                          np.random.default_rng(lv * 977 + b * 131 + 7), back=(r_i == 0), full=not _lean)
                    continue
                # V31: 拿货缺口段 (九审 P0 非均匀补货节奏; 中下层 30% 组触发)
                gap_at = set()
                if lv >= 3 and rng.random() < 0.30:
                    g0 = int(rng.integers(0, n_g))
                    gap_at = ({g0, (g0 + 1) % n_g} if rng.random() < 0.4 else {g0})
                for i in range(n_g):
                    if i in gap_at or rng.random() < 0.03:
                        continue  # H9: 3% 缺位 + V31 缺口段 (真实货架有人拿货后的空隙)
                    dist = abs((i + 0.5) / max(n_g, 1) - 0.5) * 2.0  # D33: 0=组心 1=组缘
                    irreg = 0.45 + 1.1 * dist ** 1.5  # 渐进不规则系数
                    # 真实 planogram 软件语义: 数据管结构(组/段/色), SKU 实宽管装箱
                    # 袋宽由高宽比定 (高=层高 0.62-0.72), 邻袋相触允许微溢 (参照: 满排相触)
                    x_bag = x0 + gw * (i + 0.5 + sh * 0.5) / max(n_g, 1) + (rng.random() - 0.5) * 0.008  # V28: 邻袋接触 (±1cm→±4mm)
                    _vj = 0.055 if lv >= 3 else 0.035  # V31: 前缘不齐 (中下层加强)
                    y_bag = y_off + (rng.random() - 0.5) * _vj * irreg + (0.014 if rng.random() < 0.12 * irreg else 0.0)
                    if rng.random() < ((0.45 if lv >= 3 else 0.30) * irreg):
                        # V34: 前拉封顶 0.038 (原 0.050 — BVH 实测前后排行间 11mm 深叠根因)
                        y_bag -= (0.020 + rng.random() * 0.018)  # D31/D33: 前拉加深 (V31 深度随机化)
                    # V33: 簇内中位件前探 (十一审 P0 可见面朝向) — 35% 概率前探 15-24mm,
                    #     局部遮挡后排同款正面, 破 5+ 连排同面积图案 (密度不减, 交叠不算穿插:
                    #     前探件在前, 转角扫掠从邻袋前方通过)
                    if lv >= 3 and g.get("form", "bag") == "bag" and i % 3 == 1 and rng.random() < 0.35:
                        y_bag -= 0.015 + rng.random() * 0.009
                    # V37-B2: 行带硬分离 (路线B R37-B02) — 前排终位 ≤0.070, 后排 ≥0.135
                    #     (袋鼓半深 ~27mm: 带间净距 ≥11mm → 跨排物理不可能相交; y 随机收带, 高度/倾角随机保留)
                    if lv >= 3:
                        if r_i == 1:
                            y_bag = max(0.028, min(0.048, y_bag))
                        else:
                            y_bag = max(0.135, min(0.140, y_bag))
                    y_bag = max(y_bag, 0.012)  # V59: 层板恢复全深 (前缘 y=0) — 前拉件重心须留在板上 (袋半深 ~27mm)
                    ROW_SPANS.setdefault((lv, r_i, g["design_id"]), (x0, gw))
                    if g["form"] == "barrel":
                        barrel_placeholder(f"barrel{lv}_{r_i}_{i}", x_bag, y_bag, z_bot, rgb,
                                           dia=min(0.085, bgw * 0.92), hgt=LEVEL_H * 0.78,
                                           rng=rng, tex_path=tight_crop(dpath0) if dpath0.exists() else None)
                        continue
                    if g["form"] == "box":
                        # V29: 盒组陈列姿态 (六审 P0) — 前排退让 3cm 消前突 + 前排 88% 高
                        #     → 二排露头形成可信前后排遮挡 (几何探针已证盒底坐板 7.5mm)
                        y_box = y_bag + (0.03 if r_i == 1 else 0.0)
                        h_box = 0.19 * (0.88 if r_i == 1 else 1.0)
                        # 盒面设计 (用户裁决简化版): 软粉底+TOPPRISM红顶带+主设计窗, 无次级信息 (拍摄友好)
                        bfp = None
                        if dpath0.exists():
                            _ck = str(dpath0)
                            bfp = BOX_FRONT_CACHE.get(_ck)
                            if bfp is None:
                                from PIL import Image as _I2, ImageDraw as _D3
                                base = _I2.open(dpath0).convert("RGB")
                                W2, H2 = 600, 1180
                                # V48: 粉色主体整体印刷 — 背景盒色软粉 (随 rgb), 元素直接印上, 无白贴纸
                                _soft = tuple(int(c * 255 * 0.30 + 245 * 0.70) for c in rgb)
                                comp = _I2.new("RGB", (W2, H2), _soft)
                                ins = base.resize((int(W2 * 0.78), int(H2 * 0.58)))
                                comp.paste(ins, ((W2 - ins.width) // 2, int(H2 * 0.115)))
                                d3 = _D3.Draw(comp)
                                ftop = _load_font_cn(int(H2 * 0.045))
                                fbot = _load_font_cn(int(H2 * 0.032))
                                d3.rectangle([0, 0, W2, int(H2 * 0.07)], fill=(200, 30, 30))
                                d3.text((W2 // 2, int(H2 * 0.035)), "TOPPRISM", font=ftop, fill=(255, 255, 255), anchor="mm")
                                d3.rectangle([int(W2 * 0.10), int(H2 * 0.83), int(W2 * 0.42), int(H2 * 0.91)], fill=(255, 255, 255), outline=(40, 40, 40), width=3)
                                _bx = int(W2 * 0.115)
                                while _bx < int(W2 * 0.405):
                                    d3.line([(_bx, int(H2 * 0.842)), (_bx, int(H2 * 0.898))], fill=(30, 30, 30), width=2)
                                    _bx += 7

                                bfp = DESIGN_DIR / f"boxfront_{Path(dpath0).stem}.png"
                                comp.save(bfp)
                                BOX_FRONT_CACHE[_ck] = bfp
                            _softf = tuple(c / 255.0 for c in _soft)
                            BOX_BODY_COLOR[_ck] = _softf
                        box_placeholder(f"box{lv}_{r_i}_{i}", x_bag, y_box, z_bot,
                                        rgb, bw_=min(0.12, bgw * 0.92), hgt=h_box,
                                        front_tex=bfp)
                        continue
                    if g["form"] == "bottle":
                        # P0-3: 瓶装 (A L7 深色瓶罐块): 细径高瓶, 复用圆柱占位 (盖=瓶盖)
                        barrel_placeholder(f"bottle{lv}_{r_i}_{i}", x_bag, y_bag, z_bot, rgb,
                                           dia=min(0.05, bgw * 0.9), hgt=LEVEL_H * 0.88,
                                           rng=rng, tex_path=tight_crop(dpath0) if dpath0.exists() else None)
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
                    # V52/V54: 紧裁到袋剪影 — packshot 米色边距映上袋面成"白翼"; 自适应 th 阶梯防 no-op
                    _tg = Image.open(_satp).convert("RGB")
                    _tg = _tg.crop(_tight_box(np.asarray(_tg, float)))
                    _tg = Image.fromarray(np.clip(_edge_extend(np.asarray(_tg, float)), 0, 255).astype("uint8"))
                    _tg.save(_satp)
                    ar_g2 = (0.40, 0.58)[(j * 7 + lv * 3) % 2]  # 与槽宽推导同源
                    _im = Image.open(a)
                    if _im.width / _im.height < ar_g2 - 0.04:
                        _hc = min(int(_im.width / ar_g2), _im.height)
                        _ar_p = dpath.with_suffix(".ar.png")
                        _im.crop((0, 0, _im.width, _hc)).save(_ar_p)
                        a = _ar_p
                    ar = Image.open(a).width / Image.open(a).height
                    # P0-4: 密度-形状协同 (v26 教训: 槽宽钳制反压高度→半高排大空洞;
                    # A 实测 ~34件/层 × 6-8cm 宽 × 0.5-0.65LH 高, 槽宽即袋宽, 高度钳制防塌)
                    w_bag = bgw * 0.985  # V28: 邻袋相触 (0.97→0.985, 缝隙≤2mm)
                    _hm = (0.84 + rng.random() * 0.42) if lv >= 3 else (0.90 + rng.random() * 0.25)  # V31: 高低差 (中下层加强)
                    h_bag = min(max(w_bag / ar * _hm, LEVEL_H * 0.50), LEVEL_H * 0.75)
                    clump = (i // 3) % 2 * 3.4 - 1.7  # D31: 受压簇加强 (1.1→1.7度)
                    _lb = (rng.random() - 0.5) * ((6.5 if lv >= 3 else 3.2) * irreg)  # V31: 角度差 (中下层翻倍)
                    # V33: 簇级侧转 (十一审 P0) — 3件簇共享偏角 -7.5/0/+7.5° + 逐袋 ±1.5°,
                    #     同款正面可见面积逐簇差异化 (几何冻结: 只改朝向)
                    _cl_yaw = ((((i // 3) % 3) - 1) * 5.0 + (rng.random() - 0.5) * 3.0) \
                        if (lv >= 3 and g.get("form", "bag") == "bag") else 0.0
                    lean = 6.5 if rng.random() < 0.05 else (11.0 if rng.random() < 0.05 else (2.6 if i in (2, 9) else _lb + clump * irreg + _cl_yaw))  # D33: 倾角随组缘增强  # H11: 4% 强侧转
                    # D30: 布料库实例 (变体网格共享 + OBJECT 材质逐袋独立印刷)
                    vmesh = CLOTH_LIB[(gidx * 131 + i * 17 + r_i * 53 + lv * 29) % len(CLOTH_LIB)]  # D35: 素数扰动破阵列感
                    co = bpy.data.objects.new(f"bag{lv}_{r_i}_{g['design_id']}_{i}", vmesh)
                    co.location = (max(x0 + w_bag / 2, min(x0 + gw - w_bag / 2, x_bag)),
                                   y_bag, z_bot + h_bag / 2)
                    pitch_x = (rng.random() - 0.5) * 2.4 + (4.0 + rng.random() * 3.0 if r_i == 1 else 0.0)  # D34: 二排前倾 (V34: 7-13→4-7°, 顶后摆≤12mm 防顶进后排)
                    co.rotation_euler = (math.radians(pitch_x), 0, math.radians(lean))
                    if r_i == 1:
                        co.location.y += 0.012  # D34: 整排前移 (V34: 22→12mm)
                    _xc = w_bag / 0.095 * (0.98 + rng.random() * 0.04)
                    if lv >= 3 and g.get("form", "bag") == "bag":
                        # V34: 转角足迹收缩 (十一审 P0) — 侧转袋 x 按 cos(yaw) 收缩,
                        #     转角扫掠钳回槽缝内 (解析防穿, 碰撞探针实测验证)
                        _xc *= math.cos(math.radians(min(abs(lean), 20.0)))
                    co.scale = (_xc,
                               1.0, h_bag / 0.19 * (0.97 + rng.random() * 0.06))  # D35: 逐袋轮廓微差
                    bpy.context.scene.collection.objects.link(co)  # V28修: 先入场景(depsgraph), 后算世界bbox
                    ROW_CHAINS.setdefault((lv, r_i, g["design_id"]), []).append(co)  # V37-B2 行内链式打包登记
                    # V32: 簇相关形变 (十审 P0) — 单用户化+顶点扰动:
                    #     相邻 3 件簇共享挤压方向, 逐袋肩部塌陷幅度/褶皱相位独立 (破复制模板)
                    #     禁穿插: 幅度 ≤1cm; 沉降在后 (drop 需最终 bbox)
                    if lv >= 3 and g.get("form", "bag") == "bag":
                        co.data = co.data.copy()
                        _me = co.data
                        _cl_dir = ((i // 3) % 2) - 0.5  # 簇级挤压方向 (簇内同向, 簇间反向)
                        _sh_amp = 0.003 + rng.random() * 0.005  # V34: 肩塌 3-8mm (原 5-14, BVH 实测同簇对压深叠缩减)
                        _ph = i * 13.7 + lv * 2.3  # 逐袋褶皱相位 (破模板)
                        for _v in _me.vertices:
                            _t = max(0.0, (_v.co.z + 0.095) / 0.19)  # 高度归一 0底→1顶
                            _v.co.x += _cl_dir * _sh_amp * _t * _t  # 肩部内收 (顶满底零)
                            _v.co.y += math.sin(_v.co.x * 210.0 + _ph) * 0.0018 * _t  # 前后向微褶 (V34: 2.2→1.8mm)
                        _me.update()
                    drop_to_surface(co, z_bot)  # V28: 倾角袋底角沉降到板面 (禁悬浮)
                    sl = co.material_slots[0]
                    sl.link = 'OBJECT'
                    # V41: 印刷重复感去重 (十九审 P0) — 逐袋 UV 微旋转±2.5°/缩放 0.96-1.04/平移±0.015
                    #     + 非刚性噪声微变形 0.02 (同 SKU 官方设计不变, 禁改 Logo/文字/配色)
                    _uvr = (rng.random() - 0.5) * 5.0
                    _uvs = 0.96 + rng.random() * 0.08
                    _uvt = ((rng.random() - 0.5) * 0.03, (rng.random() - 0.5) * 0.03)
                    import zlib as _z
                    _sd = _z.crc32(f"bagm_{lv}_{r_i}_{i}".encode())
                    _cw = 0.08 + (_sd % 997) / 997 * 0.06          # V42: clearcoat 0.08-0.14
                    _cr = 0.10 + ((_sd >> 10) % 997) / 997 * 0.16  # clearcoat rough 0.10-0.26
                    _bs = 0.02 + ((_sd >> 20) % 997) / 997 * 0.06  # bump 0.02-0.08
                    sl.material = bag_material(f"bagm_{lv}_{r_i}_{i}", Path(a),
                                               (0.10 if rng.random() < 0.22 else 0.28) + rng.random() * 0.30, 0.02,
                                               uv_rot=_uvr, uv_scale=_uvs, uv_tr=_uvt, warp=0.0,
                                               coat_w=_cw, coat_r=_cr, bump_s=_bs)
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
                            bpy.context.scene.collection.objects.link(ce)  # V28修: 先入场景后沉降
                            drop_to_surface(ce, z_bot - 0.001)  # V28: 簇袋微过盈沉降
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
        _sy = 0.05 * float(os.environ.get("HXL_STRIP", "1.0"))  # V43: 单灯变量 — 灯带宽度倍率 (高光带结构实验)
        lt.size = SHELF_W * 0.9; lt.size_y = _sy
        lt.energy = 24 * (0.48 + 1.20 * ((lv * 0.37 + 0.11) % 1.0))  # D38: 层间光差 ±60% (明暗层次加深)
        if lv % 3 == 1:
            lt.color = (1.0, 0.96, 0.90)  # D38: 冷暖混光 (隔层偏中性)
        strip_x = ((lv * 0.53 + 0.29) % 1.0 - 0.5) * 0.34  # H7: 灯位横移加大 (不均匀光带)
        lo = bpy.data.objects.new(f"strip{lv}", lt)
        lo.location = (strip_x, DEPTH - 0.10, z0 + 0.05)
        lo.rotation_euler = (math.radians(-70), 0, 0)
        sc.collection.objects.link(lo)

    # 环境组 (Lowe's 实证: 立体感=环境完整度 天花板+可见灯具+洞洞板端墙+金属立柱)
    top_z = LIP + SHELVES * LEVEL_H  # 结构顶 (层板顶 2.31 + 板厚近似)
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
    for ux in (-SHELF_W / 2 - 0.015, SHELF_W / 2 + 0.015):  # P0#2 结构修: 立柱移段界两端 (v19 前景三柱横穿画面=GPT结构FAIL项)
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
            lt.energy = 920; lt.spot_size = math.radians(38)
            lt.shadow_soft_size = float(os.environ.get("HXL_SPOT_SOFT", "0.14"))  # V43: 单灯变量 — 主光软影半径 (膜面高光带结构)
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
    fl.size = 2.2; fl.size_y = 1.2
    fl.energy = 7 * float(os.environ.get("HXL_FILL", "1.0"))  # V44: 单灯变量 — 填充光强度 (接触阴影可读性)
    flo = bpy.data.objects.new("frontfill", fl)
    flo.location = (0, -1.1, 1.5)
    flo.rotation_euler = (math.radians(65), 0, 0)
    sc.collection.objects.link(flo)

    # 人位相机 (primary.jpg 对齐: 站右端向左纵深看, 左远右近, 广角手机视场, 微滚转)
    if os.environ.get("HXL_CAM") == "M31":
        # M31 满幅约束拟合 (FTC 层线+横向满幅, 2026-11-22): 层线rms16.1px, 层位avg0.0126H/max0.0306H, 左缘u≈0右缘出画
        # 相机 (0.181,-1.200,2.300) 瞄 (-0.014, DEPTH/2, 2.037), f25.7mm — 实拍摄高≈2.3m (垂直张角自洽)
        cam = bpy.data.cameras.new("c"); cam.lens = 25.7
        co = bpy.data.objects.new("c", cam)
        co.location = (0.181, -1.200, 2.300)
        aim = Vector((-0.014, DEPTH / 2, 2.037)) - co.location
        rot = aim.to_track_quat('-Z', 'Y').to_euler()
        co.rotation_euler = rot
    else:
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
    # V29 几何探针: 盒/袋底 vs 板顶 (mm 级对账)
    bpy.context.view_layer.update()
    boards = {int(o.name[5:]): (o.location.z + o.scale[2]*0.5 if False else o.matrix_world.translation.z + o.dimensions.z/2)
              for o in bpy.data.objects if o.name.startswith("shelf")}
    for o in sorted(bpy.data.objects, key=lambda x: x.name):
        if o.type != 'MESH':
            continue
        zmin = min((o.matrix_world @ Vector(c)).z for c in o.bound_box)
        if o.name.startswith(("box", "bag", "shelf")):
            lv = o.name[3] if o.name.startswith(("box", "bag")) else o.name[5:]
            print(f"PROBE {o.name[:28]:28s} zmin={zmin:.4f} board_top={boards.get(int(lv.rstrip('.0')) if str(lv).rstrip('.0').isdigit() else -1, -1):.4f}")
    if "--heal" in argv:
        # V35: 局部非穿透修正 (十三审 P0) — 深叠对接触区顶点回缩压平, 保留接触外观
        #     只动相交袋对局部几何; 摆放/姿态/种子全冻结; 回缩仅水平向 (板接触保持)
        from mathutils.bvhtree import BVHTree

        def _wbvh(o):
            vs = [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
            ps = [list(p.vertices) for p in o.data.polygons]
            return BVHTree.FromPolygons(vs, ps)

        bags = [o for o in bpy.data.objects
                if o.type == 'MESH' and o.name.startswith("bag") and o.name[3].isdigit()
                and int(o.name.split("_")[0][3:]) >= 3]
        lv_of = lambda n: int(n.split("_")[0][3:])
        cw = lambda o: o.matrix_world.translation
        R, PULL, PASSES = 0.035, 0.004, 5
        healed_ids = {}
        for p_i in range(PASSES):
            trees = {o.name: _wbvh(o) for o in bags}
            deep = []
            for a in bags:
                for b in bags:
                    if b.name <= a.name or lv_of(b.name) != lv_of(a.name):
                        continue
                    dv = cw(b) - cw(a)
                    if abs(dv.x) > 0.16 or abs(dv.y) > 0.09:
                        continue
                    ov = trees[a.name].overlap(trees[b.name])
                    if len(ov) > 60:
                        deep.append((a, b, ov))
            if not deep:
                print(f"HEAL_PASS {p_i} clear")
                break
            for a, b, ov in deep:
                key = f"{a.name} x {b.name}"
                for o in (a, b):
                    if o.data.users > 1:
                        o.data = o.data.copy()  # 单用户化 (护共享布料库)
                if key not in healed_ids:
                    # 首遍: 实测最大穿透深度 (重叠区顶点到对方表面距离)
                    maxpen = 0.0
                    for ia, ib in ov[:120]:
                        for o, t_o, idx in ((a, trees[b.name], ia), (b, trees[a.name], ib)):
                            if idx < len(o.data.polygons):
                                vw = o.matrix_world @ o.data.polygons[idx].center
                                d = t_o.find_nearest(vw)[3]
                                if d is not None:
                                    maxpen = max(maxpen, d)
                    healed_ids[key] = {"lv": lv_of(a.name), "tris0": len(ov),
                                       "pen_mm": round(maxpen * 1000, 1)}
                # 接触区质心 (世界) → 邻域顶点水平回缩
                cent = [(a.matrix_world @ a.data.polygons[ia].center) for ia, ib in ov[:150] if ia < len(a.data.polygons)]
                cent += [(b.matrix_world @ b.data.polygons[ib].center) for ia, ib in ov[:150] if ib < len(b.data.polygons)]
                sep = cw(a) - cw(b)
                sep.z = 0.0
                if sep.length < 1e-6:
                    sep = Vector((1.0, 0.0, 0.0))
                sep.normalize()
                inv_a, inv_b = a.matrix_world.inverted().to_3x3(), b.matrix_world.inverted().to_3x3()
                for o, inv, d in ((a, inv_a, sep), (b, inv_b, -sep)):
                    for v in o.data.vertices:
                        vw = o.matrix_world @ v.co
                        f = 0.0
                        for c in cent:
                            dd = (vw - c).length
                            if dd < R:
                                f = max(f, 1.0 - dd / R)
                        if f > 0.0:
                            v.co += inv @ (d * (PULL * f))
                    o.data.update()
        # 终账: 逐对 tris 终值
        trees = {o.name: _wbvh(o) for o in bags}
        res = []
        for a in bags:
            for b in bags:
                if b.name <= a.name or lv_of(b.name) != lv_of(a.name):
                    continue
                dv = cw(b) - cw(a)
                if abs(dv.x) > 0.16 or abs(dv.y) > 0.09:
                    continue
                ov = trees[a.name].overlap(trees[b.name])
                if len(ov) > 4:
                    res.append((f"{a.name} x {b.name}", len(ov)))
        for k, t in res:
            h = healed_ids.get(k)
            if h and t <= 60 and h["tris0"] > 60:
                print(f"HEAL_OK {k} lv={h['lv']} tris {h['tris0']}->{t} pen={h['pen_mm']}mm")
        for k, t in res:
            h = healed_ids.get(k)
            if t > 60:
                st0 = h["tris0"] if h else "?"
                print(f"HEAL_RESIDUAL {k} tris {st0}->{t}")
        print(f"HEAL_SUMMARY deep0={len([1 for _, t in res if t <= 60])} residual={len([1 for _, t in res if t > 60])}")
    if "--side" in argv:
        # V29: 侧视正交白模 (粉盒接触关系证明 — 六审 P0 要求)
        # V34: env 参数化 (HXL_ORTHO/HXL_AIMZ/HXL_AIMX) — 转袋/前探碰撞证据可调视野
        cam = bpy.data.cameras.new("side"); cam.type = 'ORTHO'
        cam.ortho_scale = float(os.environ.get("HXL_ORTHO", "0.75"))
        co = bpy.data.objects.new("side", cam)
        _ax = float(os.environ.get("HXL_AIMX", "-0.12"))
        _az = float(os.environ.get("HXL_AIMZ", "1.47"))
        co.location = (_ax - 0.43, -1.5, _az - 0.07)  # 侧前 25° (原 L4 盒组偏移保持)
        aim = Vector((_ax, 0.2, _az)) - co.location
        co.rotation_euler = aim.to_track_quat('-Z', 'Y').to_euler()
        sc.camera = co
        sc.render.resolution_x, sc.render.resolution_y = 900, 700
    if "--v37b" in argv:
        # V37-B: 摆放级避碰 (十五审批准路线B, R37-B01~03) — 刚体位置微调, 袋网格完全不变
        # 主轴分离: 跨排对推 y, 同排对推 x; 4 遍全量重检 (新碰撞对显形), 共用袋位移累加=联合求解
        from mathutils.bvhtree import BVHTree

        def _wt(o):
            vs = [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
            ps = [list(p.vertices) for p in o.data.polygons]
            return BVHTree.FromPolygons(vs, ps)

        bags = [o for o in bpy.data.objects
                if o.type == 'MESH' and o.name.startswith("bag") and o.name[3].isdigit()
                and int(o.name.split("_")[0][3:]) >= 3]
        lv_of = lambda n: int(n.split("_")[0][3:])
        ri_of = lambda n: int(n.split("_")[1])
        cw = lambda o: o.matrix_world.translation
        ORIG36.clear()
        ORIG36.update({o.name: (cw(o).x, cw(o).y) for o in bags})
        orig = ORIG36

        # R37-B03: 法线一致性 (符号体积) — 负=法线内向
        inconsistent = 0
        for o in bags:
            if o.data.users > 1:
                continue
            tot = 0.0
            mw = o.matrix_world
            for pg in o.data.polygons:
                vs = [mw @ o.data.vertices[i].co for i in pg.vertices]
                tot += vs[0].dot(vs[1].cross(vs[2]))
            if tot / 6.0 < 0:
                inconsistent += 1
        print(f"V37B_TOPO bags={len(bags)} normal_inverted={inconsistent}")

        for p_i in range(4):
            trees = {o.name: _wt(o) for o in bags}
            pairs = []
            for a in bags:
                for b in bags:
                    if b.name <= a.name or lv_of(b.name) != lv_of(a.name):
                        continue
                    dv = cw(b) - cw(a)
                    if abs(dv.x) > 0.16 or abs(dv.y) > 0.09:
                        continue
                    ov = trees[a.name].overlap(trees[b.name])
                    if len(ov) > 4:
                        pairs.append((a, b, len(ov)))
            deep = len([p for p in pairs if p[2] > 60])
            print(f"V37B_PASS {p_i} colliding={len(pairs)} deep={deep}")
            if not pairs:
                break
            # 位移级联已证失败 (V37-B 首轮: colliding 36→32 但 deep 13→26) — 纯测量, 零位移
        # 终账
        trees = {o.name: _wt(o) for o in bags}
        rem = 0
        moved = len([o for o in bags if abs(cw(o).x - orig[o.name][0]) > 1e-6 or abs(cw(o).y - orig[o.name][1]) > 1e-6])
        for a in bags:
            for b in bags:
                if b.name <= a.name or lv_of(b.name) != lv_of(a.name):
                    continue
                dv = cw(b) - cw(a)
                if abs(dv.x) > 0.16 or abs(dv.y) > 0.09:
                    continue
                ov = trees[a.name].overlap(trees[b.name])
                if len(ov) > 4:
                    rem += 1
                    print(f"V37B_RESIDUAL {a.name} x {b.name} tris={len(ov)}")
        print(f"V37B_SUMMARY residual_pairs={rem} moved_bags={moved} "
              f"max_dx={max(abs(cw(o).x - orig[o.name][0]) for o in bags):.4f} "
              f"max_dy={max(abs(cw(o).y - orig[o.name][1]) for o in bags):.4f}")
    # V37-B2 v3: 整行链式打包 (跨组统一) — 组界对根因: 各组锚自身 x0, 组A末袋撞组B首袋
    #   整行一条链左包 (0.2mm 间隙), 行 span = 各组 [min(x0), max(x0+gw)]; 溢出→行级 yaw 收足 (|lean|>2° 减半×3/轮, ≤6 轮)
    def _xext(o):
        xs = [(o.matrix_world @ Vector(c)).x for c in o.bound_box]
        return min(xs), max(xs)
    row_keys = sorted({(k[0], k[1]) for k in ROW_CHAINS.keys()})
    yaw_shrunk_total = 0
    for (lv_c, ri_c) in row_keys:
        if lv_c < 3:
            continue
        chain = []
        span_lo, span_hi = None, None
        for k, ch in ROW_CHAINS.items():
            if (k[0], k[1]) != (lv_c, ri_c):
                continue
            chain.extend(ch)
            x0g, gw = ROW_SPANS.get(k, (None, None))
            if x0g is not None:
                span_lo = x0g if span_lo is None else min(span_lo, x0g)
                span_hi = (x0g + gw) if span_hi is None else max(span_hi, x0g + gw)
        if len(chain) < 2 or span_lo is None:
            continue
        span = span_hi - span_lo
        for _round in range(6):
            chain = sorted(chain, key=lambda o: o.matrix_world.translation.x)
            widths = []
            for o in chain:
                mn_x, mx_x = _xext(o)
                widths.append(mx_x - mn_x)
            need = sum(widths) + 0.0002 * (len(chain) - 1)
            if need <= span:
                break
            rot = sorted(chain, key=lambda o: -abs(math.degrees(o.rotation_euler.z)))
            hit = 0
            for o in rot:
                if hit >= 3:
                    break
                lz = math.degrees(o.rotation_euler.z)
                if abs(lz) > 2.0:
                    o.rotation_euler.z = math.radians(2.0 if lz > 0 else -2.0)
                    hit += 1
            if hit == 0:
                break
            yaw_shrunk_total += hit
            bpy.context.view_layer.update()
        chain = sorted(chain, key=lambda o: o.matrix_world.translation.x)
        mn0, _ = _xext(chain[0])
        cur = span_lo + (mn0 - span_lo)
        for o in chain:
            mn_x, mx_x = _xext(o)
            o.location.x += (cur - mn_x)
            cur = cur + (mx_x - mn_x) + 0.0002
        bpy.context.view_layer.update()
    print(f"V37B2_ROWCHAIN rows={len(row_keys)} yaw_shrunk={yaw_shrunk_total}")
    if "--topo" in argv:
        # R37-01: 袋体拓扑审计 — 定碰撞壳表示 (闭合流形/开放壳/非流形)
        from collections import defaultdict
        audited = set()
        print("TOPO_BEGIN")
        for o in sorted(bpy.data.objects, key=lambda x: x.name):
            if o.type != 'MESH' or not o.name.startswith("bag"):
                continue
            me = o.data
            if me.name in audited:
                continue
            audited.add(me.name)
            edges = defaultdict(int)
            for pgn in me.polygons:
                vs = list(pgn.vertices)
                for k in range(len(vs)):
                    e = tuple(sorted((vs[k], vs[(k + 1) % len(vs)])))
                    edges[e] += 1
            n_b = len([e for e, c in edges.items() if c == 1])
            n_nm = len([e for e, c in edges.items() if c > 2])
            print(f"TOPO_MESH {me.name} V={len(me.vertices)} F={len(me.polygons)} "
                  f"E={len(edges)} boundary={n_b} nonmanifold={n_nm} "
                  f"closed={'YES' if n_b == 0 and n_nm == 0 else 'NO'}")
        print("TOPO_END")
    if "--v37a" in argv:
        # V37-A: Top5 独立接触判定+局部形变验证 (R37-01~05)
        # 壳表示 (R37-01 已审计): 全部闭合亏格0流形 (V-E+F=2, 零边界零非流形)
        #   → 广义绕数内外判定严格成立, 实体壳表示冻结
        # R37-03 (评审修正): 弃全局平面投影 (平面穿对方鼓包=越推越深, 实测 tris 全升)
        #   → L3 collisionDeformer 正解: 侵入顶点推到对方实际表面外侧 2mm (沿对方表面法线)
        #   + 移动区拉普拉斯平滑 (λ=0.4 防 12mm 单步尖峰); 双方迭代 2 遍
        from mathutils.bvhtree import BVHTree

        def _wt(o):
            vs = [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
            ps = [list(p.vertices) for p in o.data.polygons]
            return BVHTree.FromPolygons(vs, ps)

        def _winding(o, q):
            """广义绕数 (闭合网格严格): q 世界坐标 → +1 内 / 0 外"""
            mwi = o.matrix_world.inverted()
            ql = mwi @ q
            tot = 0.0
            co = o.data.vertices
            for pg in o.data.polygons:
                vs = [co[i].co for i in pg.vertices]
                a, b, c = vs[0] - ql, vs[1] - ql, vs[2] - ql
                la, lb, lc = a.length, b.length, c.length
                if min(la, lb, lc) < 1e-9:
                    continue
                den = la * lb * lc + a.dot(b) * lb + b.dot(c) * lc + c.dot(a) * la
                if abs(den) < 1e-12:
                    continue
                tot += 2.0 * math.atan2(a.cross(b).dot(c), den)
            return tot / (4.0 * math.pi)

        bags = [o for o in bpy.data.objects
                if o.type == 'MESH' and o.name.startswith("bag") and o.name[3].isdigit()
                and int(o.name.split("_")[0][3:]) >= 3]
        lv_of = lambda n: int(n.split("_")[0][3:])
        cw = lambda o: o.matrix_world.translation
        trees = {o.name: _wt(o) for o in bags}
        cands = []
        for a in bags:
            for b in bags:
                if b.name <= a.name or lv_of(b.name) != lv_of(a.name):
                    continue
                dv = cw(b) - cw(a)
                if abs(dv.x) > 0.16 or abs(dv.y) > 0.09:
                    continue
                ov = trees[a.name].overlap(trees[b.name])
                if len(ov) > 4:
                    cands.append((len(ov), a, b, ov))
        cands.sort(key=lambda c: -c[0])
        top5 = cands[:5]
        print(f"V37A_TOPO bags={len(bags)} closed=ALL candidates={len(cands)} "
              f"top5={[(c[1].name, c[2].name, c[0]) for c in top5]}")
        report = []
        for rank, (_, a, b, ov) in enumerate(top5):
            if a.data.users > 1:
                a.data = a.data.copy()
            if b.data.users > 1:
                b.data = b.data.copy()
            cand_a = set()
            cand_b = set()
            for ia, ib in ov[:400]:
                if ia < len(a.data.polygons):
                    cand_a.update(a.data.polygons[ia].vertices)
                if ib < len(b.data.polygons):
                    cand_b.update(b.data.polygons[ib].vertices)

            def _push(o, other, cand_v):
                t_o = _wt(other)
                inv_o = o.matrix_world.inverted().to_3x3()
                mw_o = o.matrix_world
                moved = []
                for vi in cand_v:
                    vw = mw_o @ o.data.vertices[vi].co
                    if _winding(other, vw) < 0.5:
                        continue
                    loc, nrm, _idx, _d = t_o.find_nearest(vw)
                    if loc is None:
                        continue
                    o.data.vertices[vi].co = inv_o @ (Vector(loc) + Vector(nrm) * 0.002)
                    moved.append(vi)
                o.data.update()
                return moved

            for _pi in range(2):
                ma = _push(a, b, cand_a)
                mb = _push(b, a, cand_b)
                if not ma and not mb:
                    break
            # 移动区拉普拉斯平滑 (λ=0.4, 1 遍)
            for o, cand_v in ((a, cand_a), (b, cand_b)):
                if not cand_v:
                    continue
                nbrs = {vi: set() for vi in range(len(o.data.vertices))}  # bpy .keys() 返回字符串名, 禁用
                for pg in o.data.polygons:
                    vs = list(pg.vertices)
                    for k in range(len(vs)):
                        nbrs[vs[k]].add(vs[(k + 1) % len(vs)])
                        nbrs[vs[(k + 1) % len(vs)]].add(vs[k])
                inv_o = o.matrix_world.inverted().to_3x3()
                mw_o = o.matrix_world
                delta = {}
                for vi in cand_v:
                    vw = mw_o @ o.data.vertices[vi].co
                    nb = [mw_o @ o.data.vertices[j].co for j in nbrs[vi]]
                    if nb:
                        avg = Vector((sum(p.x for p in nb) / len(nb),
                                      sum(p.y for p in nb) / len(nb),
                                      sum(p.z for p in nb) / len(nb)))
                        delta[vi] = inv_o @ ((avg - vw) * 0.4)
                for vi, d in delta.items():
                    o.data.vertices[vi].co += d
                o.data.update()
            ta, tb = _wt(a), _wt(b)
            tris_after = len(ta.overlap(tb))
            report.append((rank, a.name, b.name, len(ov), tris_after))
            print(f"V37A_PAIR {rank} {a.name} x {b.name} "
                  f"tris_before={len(ov)} tris_after={tris_after}")
        print(f"V37A_SUMMARY pairs={len(report)} "
              f"cleared={len([r for r in report if r[4] <= 60])}")
    if "--v38" in argv:
        # V38: 恢复 V35 陈列构图 (十七审 P0) — 零相交约束下向 V36 位置二分回推
        #   只动刚体位置; x 全量回推 (构图/节奏), y 保持行带 (跨排零相交依赖); yaw 减足保留
        from bpy_extras.object_utils import world_to_camera_view as _w2c
        bags = [o for o in bpy.data.objects
                if o.type == 'MESH' and o.name.startswith("bag") and o.name[3].isdigit()
                and int(o.name.split("_")[0][3:]) >= 3]
        lv_of = lambda n: int(n.split("_")[0][3:])
        ri_of = lambda n: int(n.split("_")[1])
        cw = lambda o: o.matrix_world.translation

        def _wt(o):
            vs = [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
            ps = [list(p.vertices) for p in o.data.polygons]
            return BVHTree.FromPolygons(vs, ps)

        trees = {o.name: _wt(o) for o in bags}
        v37pos = {o.name: (cw(o).x, cw(o).y) for o in bags}
        joint = [o for o in bags
                 if o.name in ORIG36 and (abs(cw(o).x - ORIG36[o.name][0]) > 5e-4
                                          or abs(cw(o).y - ORIG36[o.name][1]) > 5e-4)]

        def _xext(o):
            xs = [(o.matrix_world @ Vector(c)).x for c in o.bound_box]
            return min(xs), max(xs)

        # V39 修正: 保序单调回拉 (按 V36 x 序, 左界=前袋右缘+0.2mm, 永不穿越; 替代二分 —
        #   二分被中间袋挡住全败, 465mm 残余 = L3 行左压实后右侧袋回不去)
        from collections import defaultdict as _dd
        row_j = _dd(list)
        for o in joint:
            row_j[(lv_of(o.name), ri_of(o.name))].append(o)
        restored = 0
        for (lvr, rir), objs in row_j.items():
            all_row = objs + [o for o in bags
                              if (lv_of(o.name), ri_of(o.name)) == (lvr, rir) and o not in objs]
            all_row = sorted(all_row, key=lambda o: ORIG36.get(o.name, (cw(o).x,))[0])
            prev_right = None
            for o in all_row:
                if o.name in ORIG36:
                    tx, ty = ORIG36[o.name]
                else:
                    tx, ty = cw(o).x, cw(o).y
                if rir == 1:
                    ty = max(0.050, min(0.070, ty))
                else:
                    ty = max(0.135, min(0.140, ty))
                mn_x, mx_x = _xext(o)
                half = (mx_x - mn_x) / 2.0
                lo_lim = (prev_right + 0.0002 + half) if prev_right is not None else -1e9
                gx = max(tx, lo_lim)
                cc = (mn_x + mx_x) / 2.0
                if abs(gx - cc) > 5e-4:
                    o.location.x += (gx - cc)
                    restored += 1
                bpy.context.view_layer.update()
                _mn2, mx2 = _xext(o)
                prev_right = mx2
        bpy.context.view_layer.update()
        # 账: 剩余位移 + 屏幕空间偏差 + 碰撞
        trees = {o.name: _wt(o) for o in bags}
        coll = 0
        for a in bags:
            for b in bags:
                if b.name <= a.name or lv_of(b.name) != lv_of(a.name):
                    continue
                dv = cw(b) - cw(a)
                if abs(dv.x) > 0.16 or abs(dv.y) > 0.09:
                    continue
                if len(trees[a.name].overlap(trees[b.name])) > 4:
                    coll += 1
        cam = sc.camera
        res = (sc.render.resolution_x, sc.render.resolution_y)
        devs = []
        for o in joint:
            if o.name not in v37pos:
                continue
            p37 = _w2c(sc, cam, Vector((v37pos[o.name][0], v37pos[o.name][1], cw(o).z)))
            p38 = _w2c(sc, cam, cw(o))
            dx = (p38.x - p37.x) * res[0]
            dy = (p38.y - p37.y) * res[1]
            devs.append((dx * dx + dy * dy) ** 0.5)
        devs.sort()
        mean_d = sum(devs) / len(devs) if devs else 0.0
        max_d = devs[-1] if devs else 0.0
        rem_disp = [abs(cw(o).x - ORIG36[o.name][0]) for o in joint if o.name in ORIG36]
        print(f"V38_SUMMARY joint={len(joint)} restored={restored} collisions={coll} "
              f"silhouette_mean_px={mean_d:.1f} silhouette_max_px={max_d:.1f} "
              f"residual_disp_max_mm={max(rem_disp) * 1000 if rem_disp else 0:.1f}")
        top_out = sorted(joint, key=lambda o: -abs(cw(o).x - ORIG36[o.name][0]))[:5]
        for o in top_out:
            ox, oy = ORIG36[o.name]
            px, py = cw(o).x, cw(o).y
            p37 = _w2c(sc, cam, Vector((v37pos[o.name][0], v37pos[o.name][1], cw(o).z)))
            p38 = _w2c(sc, cam, cw(o))
            p35 = _w2c(sc, cam, Vector((ox, oy, cw(o).z)))
            print(f"V38_OUTLIER {o.name} lv={lv_of(o.name)} ri={ri_of(o.name)} "
                  f"v36=({ox:.3f},{oy:.3f}) v38=({px:.3f},{py:.3f}) "
                  f"px35=({p35.x * res[0]:.0f},{p35.y * res[1]:.0f}) "
                  f"px38=({p38.x * res[0]:.0f},{p38.y * res[1]:.0f}) "
                  f"disp_mm={(abs(px - ox) ** 2 + abs(py - oy) ** 2) ** 0.5 * 1000:.0f}")
    if "--v40" in argv:
        # V40: 法线一致性修复 (十九审 P0) — 59 内向网格面绕序统一, 不移动顶点
        #   bmesh reverse_faces: loop-vert 关联保留 → UV 不镜像; 符号体积翻正; BVH 拓扑不变
        import bmesh
        fixed, uv_ok = 0, True
        for o in sorted(bags, key=lambda x: x.name):
            tot = 0.0
            mw = o.matrix_world
            for pg in o.data.polygons:
                vs = [mw @ o.data.vertices[i].co for i in pg.vertices]
                tot += vs[0].dot(vs[1].cross(vs[2]))
            if tot / 6.0 >= 0:
                continue
            def _uv_assoc(m):
                """逐面逐顶点 uv 关联 (face_idx, vert_idx) -> uv; 翻绕序不改变角点关联"""
                out = {}
                uvl = m.uv_layers.active
                if uvl is None:
                    return None
                for pg in m.polygons:
                    for li in pg.loop_indices:
                        vi = m.loops[li].vertex_index
                        out[(pg.index, vi)] = tuple(uvl.data[li].uv)
                return out
            uv_before = _uv_assoc(o.data)
            bm = bmesh.new()
            bm.from_mesh(o.data)
            bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
            bm.to_mesh(o.data)
            bm.free()
            uv_after = _uv_assoc(o.data)
            if uv_before is None or uv_before != uv_after:
                uv_ok = False
                print(f"V40_UV_DRIFT {o.name}")
            tot2 = 0.0
            mw = o.matrix_world
            for pg in o.data.polygons:
                vs = [mw @ o.data.vertices[i].co for i in pg.vertices]
                tot2 += vs[0].dot(vs[1].cross(vs[2]))
            fixed += 1
            print(f"V40_FLIP {o.name} svol {tot / 6.0:.6f} -> {tot2 / 6.0:.6f}")
            if (tot2 / 6.0) < 0:
                print(f"V40_STILL_NEG {o.name}")
        # 全场符号体积终检
        neg_after = 0
        for o in bags:
            tot = 0.0
            mw = o.matrix_world
            for pg in o.data.polygons:
                vs = [mw @ o.data.vertices[i].co for i in pg.vertices]
                tot += vs[0].dot(vs[1].cross(vs[2]))
            if tot / 6.0 < 0:
                neg_after += 1
        print(f"V40_SUMMARY fixed={fixed} neg_after={neg_after} uv_preserved={uv_ok}")
    if "--collide" in argv:
        # V34: 三维碰撞验证 (十一审 P0) — BVH 网格相交 + 板接触 + 前后排序
        from mathutils.bvhtree import BVHTree
        dg = bpy.context.evaluated_depsgraph_get()
        bags = [o for o in bpy.data.objects
                if o.type == 'MESH' and o.name.startswith("bag") and o.name[3].isdigit()
                and int(o.name.split("_")[0][3:]) >= 3]
        trees = {}
        for o in bags:
            # V34修: FromObject 是局部空间 (同源网格全重合=全误报) — 世界空间多边形重建
            _vs = [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
            _ps = [list(p.vertices) for p in o.data.polygons]
            trees[o.name] = BVHTree.FromPolygons(_vs, _ps)
        lv_of = lambda n: int(n.split("_")[0][3:])
        x_of = lambda o: o.matrix_world.translation.x
        y_of = lambda o: o.matrix_world.translation.y
        zmin_of = lambda o: min((o.matrix_world @ Vector(c)).z for c in o.bound_box)
        flags, touch, deep, pairs_checked = 0, 0, 0, 0
        for o in bags:
            for p in bags:
                if p.name <= o.name or lv_of(p.name) != lv_of(o.name):
                    continue
                if abs(x_of(p) - x_of(o)) > 0.16 or abs(y_of(p) - y_of(o)) > 0.09:
                    continue
                pairs_checked += 1
                ov = trees[o.name].overlap(trees[p.name])
                if len(ov) > 4:
                    flags += 1
                    if len(ov) > 60:
                        deep += 1
                        print(f"COLLIDE_DEEP {o.name} x {p.name} tris={len(ov)} "
                              f"dx={abs(x_of(p)-x_of(o)):.3f} dy={abs(y_of(p)-y_of(o)):.3f} "
                              f"y=({y_of(o):.3f},{y_of(p):.3f}) "
                              f"zc=({o.matrix_world.translation.z:.3f},{p.matrix_world.translation.z:.3f})")
                    else:
                        touch += 1
                        print(f"COLLIDE_TOUCH {o.name} x {p.name} tris={len(ov)}")
        # 板接触: 袋世界 zmin 距板顶 >3mm = 悬浮
        floats = 0
        for o in bags:
            lv = lv_of(o.name)
            z0 = LIP + lv * LEVEL_H + 0.011
            if zmin_of(o) > z0 + 0.003:
                floats += 1
                print(f"FLOAT_FLAG {o.name} zmin={zmin_of(o):.4f} board_top={z0:.4f}")
        print(f"COLLIDE_SUMMARY pairs={pairs_checked} touch={touch} deep={deep} float_flags={floats} bags={len(bags)}")
    if "--depthtable" in argv:
        # V36: 纯测量轮 (十四审 P0) — 全部相交对逐对穿透深度账 (零几何修改)
        from mathutils.bvhtree import BVHTree

        def _wt(o):
            vs = [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
            ps = [list(p.vertices) for p in o.data.polygons]
            return BVHTree.FromPolygons(vs, ps)

        bags = [o for o in bpy.data.objects
                if o.type == 'MESH' and o.name.startswith("bag") and o.name[3].isdigit()
                and int(o.name.split("_")[0][3:]) >= 3]
        lv_of = lambda n: int(n.split("_")[0][3:])
        cw = lambda o: o.matrix_world.translation
        trees = {o.name: _wt(o) for o in bags}
        rows = []
        for a in bags:
            for b in bags:
                if b.name <= a.name or lv_of(b.name) != lv_of(a.name):
                    continue
                dv = cw(b) - cw(a)
                if abs(dv.x) > 0.16 or abs(dv.y) > 0.09:
                    continue
                ov = trees[a.name].overlap(trees[b.name])
                if len(ov) < 4:
                    continue
                maxpen = 0.0
                for ia, ib in ov[:150]:
                    for o, t_o, idx in ((a, trees[b.name], ia), (b, trees[a.name], ib)):
                        if idx < len(o.data.polygons):
                            vw = o.matrix_world @ o.data.polygons[idx].center
                            d = t_o.find_nearest(vw)[3]
                            if d is not None:
                                maxpen = max(maxpen, d)
                cls = "SURFACE" if maxpen < 0.0005 else ("SLIGHT" if maxpen < 0.002 else "OBVIOUS")
                rows.append((lv_of(a.name), f"{a.name} x {b.name}", len(ov),
                             round(maxpen * 1000, 2), cls))
        rows.sort(key=lambda r: -r[3])
        for lv, k, t, p, c in rows:
            print(f"DEPTH_ROW lv={lv} {k} tris={t} maxpen={p}mm class={c}")
        n_s = len([r for r in rows if r[4] == "SURFACE"])
        n_l = len([r for r in rows if r[4] == "SLIGHT"])
        n_o = len([r for r in rows if r[4] == "OBVIOUS"])
        print(f"DEPTH_SUMMARY pairs={len(rows)} surface={n_s} slight={n_l} obvious={n_o} "
              f"maxpen={rows[0][3] if rows else 0}mm")
    sc.render.filepath = str(OUT)
    if os.environ.get("HXL_NORENDER") != "1":
        bpy.ops.render.render(write_still=True)
    print("HXL_SHELF_OK", OUT)


if __name__ == "__main__":
    main()
