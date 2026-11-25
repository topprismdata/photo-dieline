"""NV960 战役: 我方产品渲染批量出图 (Blender 内运行; Cycles 合同 v3 观感).
几何+净图UV+印刷贴图 = pack10k_thumbs 管线; 影棚 = render_final 合同 (渐变天穹/暗地/双灯/AgX Punchy).
用法: blender --background --python scripts/nv960_render_ours.py -- <映射json> <输出目录>
映射json: {"R026": "output/pack10k_scale10k/tray_tray_domelid_v0130", ...} (变体目录, 含 build.json+print.png)
"""
import json
import math
import sys
from pathlib import Path

import bpy
import mathutils

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MAP_PATH = Path(argv[0]) if len(argv) > 0 else None
OUT_DIR = Path(argv[1]) if len(argv) > 1 else None

sys.path.append("/opt/homebrew/Caskroom/miniconda/base/lib/python3.13/site-packages")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from photo_dieline.core.ir import from_raw  # noqa: E402
from photo_dieline.export.usd import _solid_triangles_mm  # noqa: E402
from photo_dieline.core.ir import class_module  # noqa: E402
from photo_dieline.export.print_layer import draw_print_texture  # noqa: E402


def enable_gpu():
    """Metal GPU (M 系列 10-50× 于 CPU; 之前一直 CPU 渲染 = 慢根因)"""
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for dev_type in ("METAL", "OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = dev_type
            prefs.get_devices()
            for d in prefs.devices:
                d.use = True
            bpy.context.scene.cycles.device = "GPU"
            print(f"GPU: {dev_type}", flush=True)
            return True
        except Exception:
            continue
    print("GPU: 不可用, 回退 CPU", flush=True)
    return False

def studio(scene):
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 192
    enable_gpu()
    scene.render.resolution_x = scene.render.resolution_y = 1024
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Punchy"
    scene.world.use_nodes = True
    nt = scene.world.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    bg = nt.nodes.new("ShaderNodeBackground")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.50, 0.51, 0.52, 1.0)
    ramp.color_ramp.elements[0].position = 0.02
    ramp.color_ramp.elements[1].color = (0.30, 0.325, 0.36, 1.0)
    ramp.color_ramp.elements[1].position = 0.55
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs[1].default_value = 0.0

    def area(name, loc, size, power, rot):
        L = bpy.data.lights.new(name, "AREA")
        L.size = size
        L.energy = power
        lo = bpy.data.objects.new(name, L)
        lo.location = loc
        lo.rotation_euler = [math.radians(a) for a in rot]
        lo.visible_transmission = False
        lo.visible_glossy = False
        lo.visible_camera = False
        scene.collection.objects.link(lo)

    area("Key", (0.6, -0.9, 2.2), 6.0, 750, (35, 25, 0))
    area("Fill", (-1.2, -0.5, 1.2), 7.0, 260, (50, -35, 0))


def render_one(variant_dir: Path, out_png: Path):
    build_path = variant_dir / "build.json"
    meta = json.loads(build_path.read_text())
    mod = class_module(meta["class_id"])
    ir = from_raw({k: v for k, v in mod.build_ir(meta["params"]).items() if k != "_derived"})
    pts_mm, tris, nets_mm = _solid_triangles_mm(ir)
    mn, mx = pts_mm.min(0), pts_mm.max(0)
    c = (mn + mx) / 2.0
    r = float(max(mx - mn).max()) * 0.5 * 1e-3
    Pm = (pts_mm - c) * 1e-3

    sc = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    for ma in list(bpy.data.materials):
        bpy.data.materials.remove(ma)

    # 地面 (campaign: ±150m 远边出框 G-F8)
    gz = float(mn[2]) * 1e-3 - 0.001
    gme = bpy.data.meshes.new("ground")
    gme.from_pydata([(-150, -150, gz), (150, -150, gz), (150, 150, gz), (-150, 150, gz)],
                    [], [(0, 1, 2, 3)])
    gme.validate()
    gm2 = bpy.data.materials.new("ground_dark")
    gm2.use_nodes = True
    gb2 = gm2.node_tree.nodes["Principled BSDF"]
    gb2.inputs["Base Color"].default_value = (0.055, 0.058, 0.06, 1)
    gb2.inputs["Roughness"].default_value = 0.9
    gme.materials.append(gm2)
    gobj = bpy.data.objects.new("ground", gme)
    sc.collection.objects.link(gobj)

    # 主体 + 净图 UV + 印刷材质
    me = bpy.data.meshes.new("body")
    me.from_pydata([tuple(p) for p in Pm], [], [tuple(t) for t in tris])
    me.validate()
    # 法线重算 (Cycles 反转法线 = 假开盖透视内壁; Workbench 不暴露)
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob_tmp = bpy.data.objects.new("body", me)
    sc.collection.objects.link(ob_tmp)
    _, (nx0, ny0, nw_mm, nh_mm) = draw_print_texture(ir, meta.get("family", "sundry"))
    uv = me.uv_layers.new(name="st")
    for loop in me.loops:
        nx, ny = nets_mm[loop.vertex_index]
        uv.data[loop.index].uv = (1.0 - (nx - nx0) / nw_mm, 1.0 - (ny - ny0) / nh_mm)
    png = variant_dir / "print.png"
    mat = bpy.data.materials.new("print")
    mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.55
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(png))
    mat.node_tree.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    me.materials.append(mat)
    ob = ob_tmp  # 法线重算时已建 — 复用防双对象 z-fighting

    # 相机 (USDCraft 口径: az45/el30, 焦距感知取景)
    az, el = math.radians(45.0), math.radians(30.0)
    d = r / math.sin(math.atan(18.0 / 60.0)) * 1.12
    eye = mathutils.Vector((math.sin(az) * math.cos(el) * d,
                            -math.cos(az) * math.cos(el) * d,
                            math.sin(el) * d))
    cam_data = bpy.data.cameras.new("c")
    cam_data.lens = 60
    cam = bpy.data.objects.new("c", cam_data)
    sc.collection.objects.link(cam)
    cam.location = eye
    cam.rotation_euler = (-eye).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam

    studio(sc)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    sc.render.filepath = str(out_png)
    bpy.ops.render.render(write_still=True)


def main():
    if not MAP_PATH or not OUT_DIR:
        print("用法: blender --background --python nv960_render_ours.py -- <映射json> <输出目录>")
        return
    mapping = json.loads(MAP_PATH.read_text())
    print(f"nv960 render: {len(mapping)} 类", flush=True)
    fails = []
    for i, (cid, var) in enumerate(sorted(mapping.items())):
        try:
            render_one(Path(var), OUT_DIR / f"{cid}.png")
            print(f"[{i+1}/{len(mapping)}] {cid} OK", flush=True)
        except Exception as e:  # noqa: BLE001
            fails.append((cid, f"{type(e).__name__} {str(e)[:120]}"))
            print(f"[{i+1}/{len(mapping)}] {cid} FAIL {type(e).__name__}", flush=True)
    print("fails:", fails, flush=True)


main()
