"""NV960 设备正典棚拍批量渲染 (Cycles + Metal GPU, AgX Punchy, 800px).

棚拍合同: 渐变天穹(上亮下暗)+双 Area 灯(主 900W/补 350W)。
坑位备忘: ① 几何必须 mm→m 换算后再入 Blender — 毫米数值当 Blender 单位用时,
按米摆的灯会全部陷进物体内部 (外表面只吃到黑暗天穹 = 全黑渲染的根因);
② 逐部件"体心-面心点积"外向法线校正 (USD/from_pydata 绕向不可靠, Cycles 严格
背向剔除, 反向件渲染纯黑); ③ build_parts 必须显式注入 class_id。
用法: blender -b --factory-startup -P scripts/render_fixtures_studio.py
输出: output/fixture_studio_renders/<class>.png (已有则 SKIP, 断点续跑)
"""
import bpy, sys, math
from pathlib import Path
import numpy as np
from mathutils import Vector

REPO = Path("/Users/guohongbin/photo-dieline")
sys.path.insert(0, str(REPO / "src"))
sys.path.append("/opt/homebrew/Caskroom/miniconda/base/lib/python3.13/site-packages")

from photo_dieline.authoring.validate_parts import load_family

OUT = REPO / "output" / "fixture_studio_renders"
OUT.mkdir(parents=True, exist_ok=True)

_MATS = {
    "steel": ((0.77, 0.78, 0.78), 0.28, 1.0), "alu": ((0.91, 0.92, 0.92), 0.25, 1.0),
    "pp": ((0.85, 0.86, 0.84), 0.38, 0.0), "paper": ((0.9, 0.9, 0.88), 0.7, 0.0),
    "kraft": ((0.44, 0.315, 0.198), 0.84, 0.0), "white": ((0.9, 0.9, 0.88), 0.7, 0.0),
}

def enable_gpu():
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for dt in ("METAL", "OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = dt
            prefs.get_devices()
            for d in prefs.devices: d.use = True
            bpy.context.scene.cycles.device = "GPU"
            return True
        except Exception:
            continue
    return False

def studio(scene):
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    enable_gpu()
    scene.render.resolution_x = scene.render.resolution_y = 640
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Punchy"
    if scene.world is None:
        scene.world = bpy.data.worlds.new("W")
    scene.world.use_nodes = True
    nt = scene.world.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    bg = nt.nodes.new("ShaderNodeBackground")
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.10, 0.11, 0.12, 1.0); ramp.color_ramp.elements[0].position = 0.08
    ramp.color_ramp.elements[1].color = (0.78, 0.79, 0.80, 1.0); ramp.color_ramp.elements[1].position = 0.55
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], ramp.inputs[0])
    nt.links.new(ramp.outputs["Color"], bg.inputs[0])
    bg.inputs[1].default_value = 1.0
    # 双灯
    sd = bpy.data.lights.new("K", 'AREA'); sd.size = 2.5; sd.energy = 900
    key = bpy.data.objects.new("K", sd); bpy.context.collection.objects.link(key)
    fl = bpy.data.lights.new("F", 'AREA'); fl.size = 3.5; fl.energy = 350
    fill = bpy.data.objects.new("F", fl); bpy.context.collection.objects.link(fill)
    return key, fill

def mat_for(mid):
    base, rough, metal = None, 0.4, 0.0
    for k, v in _MATS.items():
        if k in mid: base, rough, metal = v; break
    if base is None: base, rough, metal = (0.8, 0.8, 0.8), 0.5, 0.0
    m = bpy.data.materials.new(mid); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1.0)
    b.inputs["Roughness"].default_value = rough
    try: b.inputs["Metallic"].default_value = metal
    except Exception: pass
    return m

def add_part(p, coll):
    verts = [tuple(v) for v in np.asarray(p["verts_mm"], float) * 1e-3]  # mm→m
    faces = [tuple(t) for t in np.asarray(p["tris"], int)]
    me = bpy.data.meshes.new(p["name"])
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    # 外向法线: 体心-面心点积判定后翻转
    cen = sum((Vector(v) for v in verts), Vector((0,0,0))) / max(1, len(verts))
    out_sum = 0.0
    for poly in me.polygons:
        out_sum += poly.normal.dot(poly.center - cen)
    if out_sum < 0:
        for poly in me.polygons: poly.flip()
        me.update()
    ob = bpy.data.objects.new(p["name"], me)
    coll.objects.link(ob)
    ob.data.materials.append(mat_for(p["material_id"]))
    return ob

def render_class(mod, cid):
    for o in list(bpy.context.scene.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for blk in (bpy.data.meshes, bpy.data.materials):
        for x in list(blk):
            if x.users == 0: blk.remove(x)
    p = dict(mod.DEFAULTS[cid]); p["class_id"] = cid
    parts = mod.build_parts(p)
    coll = bpy.context.scene.collection
    xs=[];ys=[];zs=[]
    for part in parts:
        ob = add_part(part, coll)
        for v in ob.bound_box:
            w = ob.matrix_world @ Vector(v); xs.append(w.x); ys.append(w.y); zs.append(w.z)
    mn = Vector((min(xs),min(ys),min(zs))); mx = Vector((max(xs),max(ys),max(zs)))
    size = max(mx-mn); center = (mn+mx)/2; r = size/2
    key, fill = studio(bpy.context.scene)
    key.location = center + Vector((2.2, -2.6, 2.8))
    key.rotation_euler = (center - Vector(tuple(key.location))).to_track_quat('-Z','Y').to_euler()
    fill.location = center + Vector((-3.0, 2.0, 1.2))
    fill.rotation_euler = (center - Vector(tuple(fill.location))).to_track_quat('-Z','Y').to_euler()
    lens = 50; fov = 2*math.atan(18.0/lens)
    d = (r / math.sin(fov/2)) * 1.3
    az, el = math.radians(35), math.radians(24)
    cd = bpy.data.cameras.new("C"); cd.lens = lens
    cam = bpy.data.objects.new("C", cd); coll.objects.link(cam)
    cam.location = center + Vector((math.sin(az)*math.cos(el)*d, -math.cos(az)*math.cos(el)*d, math.sin(el)*d))
    cam.rotation_euler = (center - Vector(tuple(cam.location))).to_track_quat('-Z','Y').to_euler()
    bpy.context.scene.camera = cam
    sc = bpy.context.scene
    sc.render.filepath = str(OUT / f"{cid}.png")
    bpy.ops.render.render(write_still=True)
    print("DONE", cid, flush=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
mod = load_family(str(REPO / "pipelines/packaging/author_families/nv960_fixture_family.py"))
classes = sorted(mod.DEFAULTS.keys())
for i, cid in enumerate(classes):
    outp = OUT / f"{cid}.png"
    if outp.exists():
        print("SKIP", cid, flush=True); continue
    try: render_class(mod, cid)
    except Exception as e: print("FAIL", cid, str(e)[:100], flush=True)
print("ALL_DONE", flush=True)
