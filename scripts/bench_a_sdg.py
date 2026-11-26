#!/usr/bin/env python3
"""Benchmark A 场景合成器 — 通用零品牌商品类目检测语料 (协议: docs/bench_a_perception_protocol.md).

继承 openusd 02 SDG 骨架 (project_bbox/异常状态机思想), 差异:
 - 类目 = 12 个通用包装结构类 (零品牌), 非货架状态类
 - 资产 = photo-dieline usdc (酒类8 + can330/wine/food_container/rsc)
 - 无状态异常注入 (v0 纯检测)

用法:
  Blender -b -P bench_a_sdg.py -- --num-images 300 --seed 42
输出: output/bench_a/{images,labels}/{train,val} + dataset.yaml + annotations/*.json
"""
import bpy, bmesh
import os, sys, math, json, random, argparse
import numpy as np
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

# ---- 类目注册 (与 retail_categories.json 双轴一致; 顺序=class_id) ----
CLASSES = [
    "beer_bottle_330", "beer_bottle_500", "beer_can_500", "baijiu_bottle_500",
    "wine_bottle_750", "whisky_bottle_700", "vodka_bottle_700", "liquor_gift_dual",
    "beverage_can_330", "bottle_wine", "food_container_1l", "rsc_rsc_closed",
]
ASSET_DIR = "/Users/guohongbin/photo-dieline/output/liquor_usd"
LEGACY_USDC = {
    "beverage_can_330": "/Users/guohongbin/photo-dieline/hfpackage/families/beverage_can_330.usdc",
    "bottle_wine": "/Users/guohongbin/photo-dieline/hfpackage/families/bottle_wine.usdc",
    "food_container_1l": "/Users/guohongbin/photo-dieline/hfpackage/families/food_container_1l.usdc",
    "rsc_rsc_closed": "/Users/guohongbin/photo-dieline/hfpackage/families/rsc_rsc_closed.usdc",
}
# 真实世界公称尺寸 (m): 摆放与相机用
REAL = {
    "beer_bottle_330": (0.062, 0.233), "beer_bottle_500": (0.066, 0.263),
    "beer_can_500": (0.066, 0.167), "baijiu_bottle_500": (0.083, 0.245),
    "wine_bottle_750": (0.076, 0.298), "whisky_bottle_700": (0.088, 0.240),
    "vodka_bottle_700": (0.072, 0.289), "liquor_gift_dual": (0.200, 0.340),
    "beverage_can_330": (0.066, 0.115), "bottle_wine": (0.076, 0.300),
    "food_container_1l": (0.120, 0.100), "rsc_rsc_closed": (0.300, 0.220),
}
MAT_OVERRIDE = {}  # usdc 自带素材质

ap = argparse.ArgumentParser()
ap.add_argument("--num-images", type=int, default=300)
ap.add_argument("--seed", type=int, default=42)
ap.add_argument("--res", type=int, default=960)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
args = ap.parse_args(argv)

OUT = "/Users/guohongbin/photo-dieline/output/bench_a"
for sub in ("images/train", "images/val", "labels/train", "labels/val", "annotations"):
    os.makedirs(os.path.join(OUT, sub), exist_ok=True)
rng = random.Random(args.seed)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.view_settings.exposure = -1.35
scene.render.resolution_x = scene.render.resolution_y = args.res
scene.render.film_transparent = False

# 清场
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# ---- 灯光与世界 ----
try:
    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.72, 0.73, 0.75, 1)
    bg.inputs[1].default_value = 0.5
except Exception:
    world = bpy.data.worlds.new("W"); scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.72, 0.73, 0.75, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.5

def add_light(name, loc, energy, size):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.size = size
    lo = bpy.data.objects.new(name, ld); lo.location = loc
    bpy.context.collection.objects.link(lo)
    return lo

# ---- 资产导入与归一化 ----
def import_asset(cid):
    """导入 usdc, 归一化: 真实尺寸+落地 z=0+质心居中。返回 (collection, (W_m, H_m))"""
    src = LEGACY_USDC.get(cid, f"{ASSET_DIR}/{cid}/simready_usd/{cid}.usdc")
    before = set(bpy.data.objects)
    bpy.ops.wm.usd_import(filepath=src)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    col = bpy.data.collections.new(cid)
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
    root = bpy.data.objects.new(f"root_{cid}", None)
    col.objects.link(root)
    for o in new:
        o.parent = root
    # 包围盒
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    dims = mx - mn
    W, H = REAL.get(cid, (float(dims.x), float(dims.z)))
    s = H / max(float(dims.z), 1e-6)
    root.scale = (s, s, s)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    ctr = (mn + mx) / 2
    root.location = Vector((-ctr.x, -ctr.y, -mn.z - 50.0))
    bpy.context.view_layer.update()
    locals_ = []
    for o in meshes:
        o.data.transform(root.matrix_world.copy())   # 变换烘进顶点
        o.parent = None
        o.matrix_world = Matrix.Identity(4)
        locals_.append((o, Matrix.Identity(4)))
    return col, root, locals_, (W, H)

ASSETS = {}
for cid in CLASSES:
    ASSETS[cid] = import_asset(cid)

SCENE_OBJS = []

# 玻璃透射钳制: 语料可读性优先 (透射>0.5 压到 0.4, 底色加深)
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    for n in m.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            tw = n.inputs.get('Transmission Weight')
            if tw and tw.default_value > 0.3:
                tw.default_value = 0.25
                bc = n.inputs.get('Base Color')
                bc.default_value = tuple(max(v * 0.30, 0.05) for v in bc.default_value[:3]) + (1.0,)
print("assets imported:", len(ASSETS))

def spawn(cid, loc, yaw_deg, scale_jitter=0.04):
    """链接复制模板对象 (共享 mesh 数据) 到货架位。返回 (obs, W, H)。"""
    col, root, locals_, (W, H) = ASSETS[cid]
    s = 1.0 + rng.uniform(-scale_jitter, scale_jitter)
    M_place = (Matrix.Translation(Vector(loc)) @ Matrix.Rotation(math.radians(yaw_deg), 4, 'Z')
               @ Matrix.Diagonal(Vector((s, s, s, 1.0))))
    obs = []
    for src, lmat in locals_:
        d = src.copy()  # 链接 mesh 数据, 低开销
        d.matrix_world = M_place @ lmat
        bpy.context.scene.collection.objects.link(d)
        obs.append(d)
        SCENE_OBJS.append(d)
    return obs, W * s, H * s

# ---- 货架搭建 ----
def build_shelf(broads=3, width=1.6, depth=0.42, gap=0.42):
    board_mat = bpy.data.materials.new("board")
    board_mat.use_nodes = True
    bn = board_mat.node_tree.nodes["Principled BSDF"]
    bn.inputs["Base Color"].default_value = (0.42, 0.40, 0.38, 1)
    bn.inputs["Roughness"].default_value = 0.55
    ys = []
    for i in range(broads):
        z = 0.9 + i * gap
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -depth/2, z - 0.02))
        b = bpy.context.object
        b.scale = (width, depth, 0.04)
        b.data.materials.append(board_mat)
        b.name = f"board{i}"
        ys.append(z)
    # 背板
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.16, 1.2))
    bp = bpy.context.object
    bp.scale = (width + 0.1, 0.03, 1.6)
    bp.data.materials.append(board_mat)
    bp.name = "backplate"
    return ys

def visible_frac(obs, cam, res):
    """近似可见比例: 物件包围盒中心+角点投影在画内的比例"""
    cnt = 0; tot = 0
    mn = Vector((min(o.matrix_world @ Vector(c) for c in o.bound_box) for o in obs)) if False else None
    pts = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box]
    if not pts: return 0.0
    mnv = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mxv = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    for sx in (0.1, 0.5, 0.9):
        for sy in (0.1, 0.9):
            for sz in (0.1, 0.5, 0.9):
                pt = Vector((mnv.x + (mxv.x-mnv.x)*sx, mnv.y + (mxv.y-mnv.y)*sy, mnv.z + (mxv.z-mnv.z)*sz))
                co = world_to_camera_view(scene, cam, pt)
                tot += 1
                if 0.02 < co.x < 0.98 and 0.02 < co.y < 0.98 and co.z > 0:
                    cnt += 1
    return cnt / max(tot, 1)

def project_bbox(obs, cam, w, h):
    xs, ys_, zs = [], [], []
    for o in obs:
        for c in o.bound_box:
            wpt = o.matrix_world @ Vector(c)
            co = world_to_camera_view(scene, cam, wpt)
            xs.append(co.x); ys_.append(co.y); zs.append(co.z)
    x1, x2 = min(xs), max(xs)
    y1, y2 = min(ys_), max(ys_)
    if max(zs) <= 0 or x2 < 0 or x1 > 1 or y2 < 0 or y1 > 1:
        return None
    u1, u2 = max(0, x1), min(1, x2)
    v1, v2 = max(0, 1 - y2), min(1, 1 - y1)
    if (u2 - u1) * (v2 - v1) < 0.005:
        return None
    return (u1 * w, v1 * h, u2 * w, v2 * h)

# ---- 场景生成 ----
def make_scene(idx, split):
    global SCENE_OBJS
    for o in SCENE_OBJS:
        try:
            bpy.data.objects.remove(o, do_unlink=True)
        except Exception:
            pass
    for o in list(bpy.data.objects):
        if o.name.startswith(("cam_", "sun_", "fill_", "board", "backplate")):
            bpy.data.objects.remove(o, do_unlink=True)
    SCENE_OBJS = []
    boards = build_shelf()
    add_light("sun_", (0.5, -1.2, 2.2), rng.uniform(300, 480), 2.0)
    add_light("fill_", (-0.9, -0.8, 1.6), rng.uniform(120, 220), 1.5)
    cds = bpy.data.cameras.new("cam_")
    cds.lens = rng.choice([38, 40, 42])
    cam = bpy.data.objects.new("cam_", cds)
    bpy.context.collection.objects.link(cam)
    cam.location = (rng.uniform(-0.08, 0.08), -1.72 + rng.uniform(-0.06, 0.06), 1.32 + rng.uniform(-0.05, 0.05))
    target = Vector((0, 0, 1.30))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = cam

    records = []
    n_slots = rng.randint(5, 8)
    slot_w = 1.5 / n_slots
    for bi, zboard in enumerate(boards):
        for si in range(n_slots):
            cid = rng.choice(CLASSES)
            W, H = REAL[cid]
            x0 = -0.75 + si * slot_w
            n_face = rng.randint(1, 3)
            yaw = rng.uniform(-14, 14)
            for fi in range(n_face):
                fx = x0 + slot_w/2 + (fi - (n_face-1)/2) * (W + 0.012)
                if fx > 0.76 or fx < -0.76:
                    continue
                obs, ws, hs = spawn(cid, (fx + rng.uniform(-0.006, 0.006), -0.22 + rng.uniform(-0.02, 0.02), zboard), yaw + rng.uniform(-4, 4))
                records.append((obs, cid))
    bpy.context.view_layer.update()

    labels, ann = [], []
    img_idx = f"img_{idx:04d}"
    kept = 0
    class_count = {}
    dbg_first = None
    for obs, cid in records:
        if dbg_first is None:
            bb0 = project_bbox(obs, cam, args.res, args.res)
            vf0 = visible_frac(obs, cam, args.res)
            dbg_first = (len(obs), obs[0].matrix_world.translation[:] if obs else None,
                         bb0, round(vf0, 2))
        bb = project_bbox(obs, cam, args.res, args.res)
        vf = visible_frac(obs, cam, args.res)
        if bb is None or vf < 0.35:
            continue
        x1, y1, x2, y2 = bb
        cx, cy = (x1+x2)/2/args.res, (y1+y2)/2/args.res
        bw, bh = (x2-x1)/args.res, (y2-y1)/args.res
        labels.append(f"{CLASSES.index(cid)} {cx:.5f} {cy:.5f} {bw:.5f} {bh:.5f}")
        ann.append({"sku": cid, "bbox_xyxy": [round(v,1) for v in bb]})
        kept += 1
        class_count[cid] = class_count.get(cid, 0) + 1
    if kept < 6:
        print(f"   DBG img{idx}: records={len(records)} kept={kept} first={dbg_first}")
        return False  # 太空则弃图
    scene.render.filepath = f"{OUT}/images/{split}/{img_idx}.png"
    bpy.ops.render.render(write_still=True)
    open(f"{OUT}/labels/{split}/{img_idx}.txt", "w").write("\n".join(labels))
    json.dump({"image": img_idx, "split": split, "n": kept, "classes": class_count},
              open(f"{OUT}/annotations/{img_idx}.json", "w"))
    return True

n_val = max(20, args.num_images // 6)
made = 0
for i in range(args.num_images):
    split = "val" if i % 6 == 0 else "train"
    if make_scene(i, split):
        made += 1
    if (i+1) % 25 == 0:
        print(f"[{i+1}/{args.num_images}] made={made}")

yaml = f"path: {OUT}\ntrain: images/train\nval: images/val\nnames:\n" + \
       "".join(f"  {i}: {c}\n" for i, c in enumerate(CLASSES))
open(f"{OUT}/dataset.yaml", "w").write(yaml)
print(f"DONE made={made} yaml={OUT}/dataset.yaml")
