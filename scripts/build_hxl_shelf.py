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
import sys
from pathlib import Path

import numpy as np
import PIL.Image as Image
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = Path(argv[0]) if argv else Path("/tmp/hxl_v1.png")
ROOT = Path("/Users/guohongbin/photo-dieline")

# ---- 场景参数 (对账 v2) ----
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


def barrel_placeholder(name, x, y, z_bot, rgb, dia=0.075, hgt=0.26, rng=None):
    """桶装罐 (H2 几何真实性: 内壁凹腔+缘/盖逐罐抖动, D8 评审罐顶过于整齐)."""
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


def img_bag_curved(name, tex_path, w, h, loc, emissive=0.06, rough=0.4, lean=0.0, amp=0.006, pitch=0.0, phi1=0.0, phi2=0.0, phi3=0.0, phi4=0.0):
    """微鼓曲面前板 (6mm): crop 纹理不变, 剪影+镜面变化 — D4 教训的保守中间路径."""
    import bmesh
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rough
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(tex_path))
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
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
            wr = 0.0006 * math.sin(9 * math.pi * v) * (1 - math.sin(math.pi * u)) ** 2
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
    sc.view_settings.exposure = 0.0
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
    img_plane("sign", pil_tex_sign(), SHELF_W, 0.42,
              (0, DEPTH - 0.04, SHELVES * LEVEL_H + 0.30), emissive=1.2)

    # 层板 + 前唇 + 排面 + 价签
    tag_texts = ["2.9", "4.9", "5.8", "5.9", "7.2", "1.7", "3.5"]
    bag_names = [a.stem for a in ASSETS]
    # ESR Step C: 加载陈列表 (数据驱动布局; 场景只留夹具/灯光/相机)
    PLAN = json.loads((ROOT / "data/shelf_twin/planogram.json").read_text())

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
        # ESR Step C: 排面 = planogram.json 消费者 (facings×单位宽 → 宽度分配)
        rng = np.random.default_rng(lv * 31 + 7)
        plan_lv = PLAN["levels"][lv]
        # 排面归一化: VLM 计数含二排露头会超墙容量, 按比例归一到 ≤24 槽
        fac_sum = sum(g["facings"] for g in plan_lv["groups"])
        norm = min(1.0, 24.0 / fac_sum)
        plan_lv = {**plan_lv, "groups": [{**g, "facings": max(1, round(g["facings"] * norm))}
                                         for g in plan_lv["groups"]]}
        for r_i, (y_off, s0, sh) in enumerate(((DEPTH / 2 - 0.06, 1.0, 0.0),
                                               (DEPTH / 2 - 0.17, 0.92, 0.5))):
            for g in plan_lv["groups"]:
                j = int(g["design_id"].split("_")[1])
                rgb = FAMILY_RGB[g["color"]]
                gw = g["width_frac"] * SHELF_W
                x0 = g["x0_frac"] * SHELF_W - SHELF_W / 2
                n_g = max(1, g["facings"] + (1 if sh and g["facings"] > 2 else 0))
                bgw = gw / n_g
                z_bot = z0 + 0.013  # 坐落层板唇 (2mm 过盈=承重接触)
                for i in range(n_g):
                    # 真实 planogram 软件语义: 数据管结构(组/段/色), SKU 实宽管装箱
                    # 袋宽由高宽比定 (高=层高 0.62-0.72), 邻袋相触允许微溢 (参照: 满排相触)
                    x_bag = x0 + gw * (i + 0.5 + sh * 0.5) / max(n_g, 1) + (rng.random() - 0.5) * 0.015
                    y_bag = y_off + (0.012 if rng.random() < 0.10 else 0.0)
                    if g["form"] == "barrel":
                        barrel_placeholder(f"barrel{lv}_{r_i}_{i}", x_bag, y_bag, z_bot, rgb,
                                           dia=min(0.075, bgw * 0.92), rng=rng)
                        continue
                    if g["form"] == "box":
                        box_placeholder(f"box{lv}_{r_i}_{i}", x_bag, y_bag, z_bot, rgb,
                                        bw_=min(0.12, bgw * 0.92))
                        continue
                    a = crop_bag(ASSETS[j], seed=lv * 31 + r_i * 17 + i)
                    ar = Image.open(a).width / Image.open(a).height
                    # 组内同 SKU=同尺寸定宽平铺 (v29b 教训: 随机尺寸破坏平铺 → 邻字叠印)
                    w_bag = bgw * (0.98 + rng.random() * 0.04)
                    h_bag = min(w_bag / ar, LEVEL_H * 0.8)
                    lean = 1.8 if i in (2, 9) else (rng.random() - 0.5) * 1.8  # v29 教训: 3° 倾角袋角压邻袋文字区(叠印乱码)
                    img_bag_curved(f"bag{lv}_{r_i}_{g['design_id']}_{i}", a, w_bag, h_bag,
                                   (max(x0 + w_bag / 2, min(x0 + gw - w_bag / 2, x_bag)),
                                    y_bag, z_bot + h_bag / 2),
                                   emissive=0.02, rough=0.18 + rng.random() * 0.32, lean=lean,
                                   amp=0.004 + rng.random() * 0.007,
                                   pitch=(rng.random() - 0.5) * 2.4,
                                   phi1=rng.random() * 6.28, phi2=rng.random() * 6.28,
                                   phi3=rng.random() * 6.28, phi4=rng.random() * 6.28)
        # 层间背光带 (EEVEE 自发光不照明 → 需真光源; 朝袋背面)
        bl = bpy.data.lights.new(f"back{lv}", "AREA")
        bl.size = SHELF_W * 0.95; bl.size_y = LEVEL_H * 0.7; bl.energy = 8
        blo = bpy.data.objects.new(f"back{lv}", bl)
        blo.location = (0, DEPTH - 0.10, z0 + LEVEL_H / 2)
        blo.rotation_euler = (math.radians(-90), 0, 0)
        sc.collection.objects.link(blo)
        # 层板下沿灯带 (补层板唇高光)
        lt = bpy.data.lights.new(f"strip{lv}", "AREA")
        lt.size = SHELF_W * 0.9; lt.size_y = 0.05
        lt.energy = 24 * (0.8 + 0.4 * ((lv * 0.37) % 1.0))  # 层间光差 ±20%
        strip_x = ((lv * 0.53) % 1.0 - 0.5) * 0.12  # 灯位微差 (非严格居中)
        lo = bpy.data.objects.new(f"strip{lv}", lt)
        lo.location = (strip_x, DEPTH - 0.10, z0 + 0.05)
        lo.rotation_euler = (math.radians(-70), 0, 0)
        sc.collection.objects.link(lo)

    # 顶部射灯 ×4: 一主三辅 (H1: 定向主光替代平光, 杠杆#2)
    for i, x in enumerate((-0.9, -0.3, 0.3, 0.9)):
        lt = bpy.data.lights.new(f"spot{i}", "SPOT")
        if i == 1:
            lt.energy = 520; lt.spot_size = math.radians(42)   # H6 主光加硬: 高光份额对靶
        else:
            lt.energy = 110; lt.spot_size = math.radians(55)
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

    # 人位相机 (对账 v2: 站位偏右, 平视微仰, 透视向左收敛, 微滚转)
    cam = bpy.data.cameras.new("c"); cam.lens = 32
    co = bpy.data.objects.new("c", cam)
    co.location = (0.85, -1.55, 1.28)
    aim = Vector((-0.30, DEPTH / 2, 1.22)) - co.location
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

    sc.render.filepath = str(OUT)
    bpy.ops.render.render(write_still=True)
    print("HXL_SHELF_OK", OUT)


if __name__ == "__main__":
    main()
