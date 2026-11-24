"""pack10k 双缩略图 (Blender 内运行; Workbench 快速档):
.thumbs/256x256/model.usdc.png (深底) + model.usdc_light.png (浅底), 512px。
相机口径照 USDCraft: 方位 45°/仰角 30°, 从物体前方 (−Y) 观察。

用法: /Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/pack10k_thumbs.py -- <数据集根目录>
"""

import json
import math
import sys
from pathlib import Path

import bpy
import mathutils

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ROOT = Path(argv[0]) if argv else None
# Blender 3.13 内置 Python 无 jsonschema — 挂 miniconda 3.13 站点包 (二进制同版兼容);
# append 不抢占 Blender 自带包
sys.path.append("/opt/homebrew/Caskroom/miniconda/base/lib/python3.13/site-packages")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from photo_dieline.core.ir import from_raw  # noqa: E402
from photo_dieline.export.usd import _solid_triangles_mm  # noqa: E402
from photo_dieline.core.ir import class_module  # noqa: E402


def setup_scene(dark: bool):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.render_aa = "FXAA"
    shading = sc.display.shading
    shading.background_type = "WORLD"  # Workbench 默认 THEME 灰 — 显式切 WORLD
    shading.light = "STUDIO"
    shading.color_type = "TEXTURE"  # WP2: 显示印刷纹理
    shading.show_cavity = True
    shading.cavity_type = "WORLD"
    w = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    sc.world = w
    w.color = (0.075, 0.078, 0.086) if dark else (0.93, 0.93, 0.94)  # RGB 三元 (Blender 5.x)
    sc.render.resolution_x = sc.render.resolution_y = 512
    sc.render.film_transparent = False
    return sc


def render_asset(build_path: Path):
    meta = json.loads(build_path.read_text())
    mod = class_module(meta["class_id"])
    ir = from_raw({k: v for k, v in mod.build_ir(meta["params"]).items() if k != "_derived"})
    pts_mm, tris, nets_mm = _solid_triangles_mm(ir)
    mn, mx = pts_mm.min(0), pts_mm.max(0)
    c = (mn + mx) / 2.0
    r = float(max(mx - mn).max()) * 0.5 * 1e-3  # 米! (mm bbox → m; 之前漏换算致相机 117m 外)
    Pm = (pts_mm - c) * 1e-3  # 中心置原点, mm→m

    sc = bpy.context.scene
    # 逐件清除 (禁用 read_factory_settings(use_empty) — 实证会清出异常场景态: 物体不在 view layer)
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    for ma in list(bpy.data.materials):
        bpy.data.materials.remove(ma)
    me = bpy.data.meshes.new("body")
    me.from_pydata([tuple(p) for p in Pm], [], [tuple(t) for t in tris])
    me.validate()
    # WP2: 净图 UV + 印刷纹理材质 (Workbench TEXTURE 模式显示)
    from photo_dieline.export.print_layer import draw_print_texture
    _, (nx0, ny0, nw_mm, nh_mm) = draw_print_texture(ir, meta.get("family", "sundry"))
    uv = me.uv_layers.new(name="st")
    for loop in me.loops:
        nx, ny = nets_mm[loop.vertex_index]
        uv.data[loop.index].uv = (1.0 - (nx - nx0) / nw_mm, 1.0 - (ny - ny0) / nh_mm)
    png = build_path.parent / "print.png"
    if png.exists():
        mat = bpy.data.materials.new("print")
        mat.use_nodes = True
        nt = mat.node_tree
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(str(png))
        nt.links.new(tex.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
        me.materials.append(mat)
    ob = bpy.data.objects.new("body", me)
    sc.collection.objects.link(ob)

    az, el = math.radians(45.0), math.radians(30.0)
    # 距离: r/sin(atan(sensor_half/lens)) × 1.12 边距 (60mm/36mm → d≈3.73r, 焦距感知取景)
    d = r / math.sin(math.atan(18.0 / 60.0)) * 1.12
    eye = mathutils.Vector((math.sin(az) * math.cos(el) * d,
                            -math.cos(az) * math.cos(el) * d,
                            math.sin(el) * d))
    cam_data = bpy.data.cameras.new("c")
    cam_data.lens = 60
    cam = bpy.data.objects.new("c", cam_data)
    sc.collection.objects.link(cam)
    cam.location = eye
    direction = -eye
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam

    tdir = build_path.parent / ".thumbs" / "256x256"
    tdir.mkdir(parents=True, exist_ok=True)
    for dark, name in ((True, "model.usdc.png"), (False, "model.usdc_light.png")):
        setup_scene(dark)
        sc.render.filepath = str(tdir / name)
        bpy.ops.render.render(write_still=True)


def main():
    if ROOT is None:
        print("用法: blender --background --python pack10k_thumbs.py -- <数据集根目录>")
        return
    builds = sorted(ROOT.glob("**/build.json"))
    print(f"thumbnails: {len(builds)} assets", flush=True)
    for i, bp in enumerate(builds):
        try:
            render_asset(bp)
        except Exception as e:  # noqa: BLE001
            print(f"[{i}] FAIL {bp.parent.name}: {type(e).__name__} {str(e)[:120]}", flush=True)
            continue
        if (i + 1) % 50 == 0:
            print(f"[{i + 1}/{len(builds)}]", flush=True)
    print("thumbnails done", flush=True)


main()
