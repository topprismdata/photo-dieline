import sys, math, json
sys.path.insert(0, "/Users/guohongbin/photo-dieline/src")
import bpy
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

# 重建 bottle 场景 (同 render_assembly_v3 前半, 无渲染)
import os
ALL = json.loads(open(os.environ.get("RENDER_PARTS", "/tmp/author/bottle_parts.json")).read())
rec = ALL
parts = [(p["name"], np.array(p["verts"], float), np.array(p["tris"], int), p["material_id"]) for p in rec["parts"]]
# 出厂三件套清除 (Cube/Light/Camera): 后台启动场景自带 — Cube 即白墙角本体
for _d in ("Cube", "Light", "Camera"):
    _o = bpy.data.objects.get(_d)
    if _o:
        bpy.data.objects.remove(_o, do_unlink=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.world = bpy.data.worlds.new("W")
sc.world.use_nodes = True

allv = np.vstack([p[1] for p in parts])
mn, mx = allv.min(0), allv.max(0)
c = (mn + mx) / 2.0
gz = (float(mn[2]) - float(c[2])) * 1e-3 - 0.002

for pid, verts, tris, mid in parts:
    Pm = (verts - c) * 1e-3
    me = bpy.data.meshes.new(pid)
    me.from_pydata([tuple(p) for p in Pm], [], [tuple(t) for t in tris])
    me.validate()
    ob = bpy.data.objects.new(pid, me)
    sc.collection.objects.link(ob)

# 影棚弧形幕 (cyc): 地板 4m 前伸 + 四分之一圆弧过渡 + 4m 竖墙 — 无地平线
import bmesh
cyc_me = bpy.data.meshes.new("cyc")
bm = bmesh.new()
SEGS = 32
R = 2.5
XW = 7.0
rows = []
rows.append([(-XW, 5.0, gz)])   # 地板前缘 (相机侧)
for i in range(SEGS + 1):
    a = math.radians(90.0 * i / SEGS)
    y = -(R + 1.5) + R * math.sin(a)
    z = gz + R * (1.0 - math.cos(a))
    rows.append([(-XW, y, z)])
rows.append([(-XW, -(R + 1.5), gz + R + 2.0)])  # 顶部
verts = []
quads = []
for r in rows:
    verts.append(bm.verts.new((r[0][0], r[0][1], r[0][2])))
    verts.append(bm.verts.new((r[0][0] + 2 * XW, r[0][1], r[0][2])))
for i in range(len(rows) - 1):
    a0, b0 = verts[2 * i], verts[2 * i + 1]
    a1, b1 = verts[2 * i + 2], verts[2 * i + 3]
    quads.append((a0, b0, b1, a1))
bm.faces.new(quads[0]) if False else None
for i, q in enumerate(quads):
    try:
        bm.faces.new(q)
    except ValueError:
        pass
bm.normal_update()
bm.to_mesh(cyc_me)
bm.free()
cyc_me.validate()
gm_cyc = bpy.data.materials.new("cyc_gray"); gm_cyc.use_nodes = True
gb_c = gm_cyc.node_tree.nodes["Principled BSDF"]
gb_c.inputs["Base Color"].default_value = (0.10, 0.105, 0.11, 1)
gb_c.inputs["Roughness"].default_value = 0.9
cyc_me.materials.append(gm_cyc)
cyc_ob = bpy.data.objects.new("cyc", cyc_me)
sc.collection.objects.link(cyc_ob)

gme = bpy.data.meshes.new("ground")
gme.from_pydata([(-3, -3, gz), (3, -3, gz), (3, 3, gz), (-3, 3, gz)], [], [(0, 1, 2, 3)])  # 60×60 无角线
gme.validate()
gob = bpy.data.objects.new("ground", gme)
sc.collection.objects.link(gob)

az, el = math.radians(35.0), math.radians(20.0)
dd = 0.6
eye = Vector((math.sin(az) * math.cos(el) * dd, -math.cos(az) * math.cos(el) * dd, math.sin(el) * dd))
cd = bpy.data.cameras.new("c"); cd.lens = 75
cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam)
cam.location = eye
tgt = Vector((0, 0, 0))
cam.rotation_euler = (tgt - eye).to_track_quat("-Z", "Y").to_euler()
sc.camera = cam
bpy.context.view_layer.update()

# === 库材质 (render_materials 同源) ===
sys.path.insert(0, "/tmp")
import importlib
rm = importlib.import_module("render_materials")

def lib_mat(mid, corrugated=False):
    rgb, rough, metallic, transmission, ior = rm.MATERIALS[mid]
    m = bpy.data.materials.new(mid)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    b.inputs["IOR"].default_value = ior
    if transmission:
        for key in ("Transmission Weight", "Transmission"):
            if key in b.inputs:
                b.inputs[key].default_value = 1.0
                break
    return m

for pid, verts, tris, mid in parts:
    me = bpy.data.meshes.get(pid)
    if me:
        me.materials.append(lib_mat(mid))
gm2 = bpy.data.materials.new("ground_dark"); gm2.use_nodes = True
gb2 = gm2.node_tree.nodes["Principled BSDF"]
gb2.inputs["Base Color"].default_value = (0.10, 0.105, 0.11, 1)
gb2.inputs["Roughness"].default_value = 0.9
gme.materials.append(gm2)

# === 渲染设置 (合同 v3) ===
sc.render.engine = "CYCLES"
sc.cycles.samples = 192
sc.render.resolution_x = sc.render.resolution_y = 1024
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Punchy"
sc.world.use_nodes = True
bg = sc.world.node_tree.nodes["Background"]
# 渐变天穹 (无缝 cyc): 地平色=地面远端色, 上方渐亮 — 消灭墙角读感
nt = sc.world.node_tree
tc = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (0.145, 0.152, 0.16, 1.0)   # 地平: 地面远端色
ramp.color_ramp.elements[0].position = 0.02
ramp.color_ramp.elements[1].color = (0.30, 0.325, 0.36, 1.0)   # 天顶
ramp.color_ramp.elements[1].position = 0.55
nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
bg.inputs[1].default_value = 0.0  # 世界全黑: 一切亮度来自灯+幕 (世界彻底退出画面)

def area(name, loc, size, power, rot):
    L = bpy.data.lights.new(name, "AREA"); L.size = size; L.energy = power
    lo = bpy.data.objects.new(name, L); lo.location = loc
    lo.rotation_euler = [math.radians(a) for a in rot]
    lo.visible_transmission = False  # 面光经玻璃折射显形 = 假墙角线根因
    lo.visible_glossy = False
    lo.visible_camera = False        # 灯本体对相机可见 = 白墙角真根因 (发光不受影响)
    sc.collection.objects.link(lo)

area("Key", (0.6, -0.9, 1.1), 1.2, 300, (35, 25, 0))
area("Fill", (-0.9, -0.4, 0.7), 1.6, 90, (50, -35, 0))
area("Rim", (0.2, 0.9, 0.9), 0.9, 135, (60, 160, 0))

# === 确定性取景 ===
az, el = math.radians(35.0), math.radians(20.0)
dd = float(mx[2] - mn[2]) * 1e-3
eye = Vector((math.sin(az) * math.cos(el) * dd, -math.cos(az) * math.cos(el) * dd, math.sin(el) * dd))
cd = bpy.data.cameras.new("c"); cd.lens = 75
cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam)
cam.location = eye
tgt = Vector((0, 0, 0))
cam.rotation_euler = (tgt - eye).to_track_quat("-Z", "Y").to_euler()
sc.camera = cam
# 迭代拟合: world_to_camera_view (探针已验证的可靠原语) 采样实测填充率, 5 轮收敛
d = dd
for it in range(5):
    cam.location = Vector((math.sin(az) * math.cos(el) * d, -math.cos(az) * math.cos(el) * d, math.sin(el) * d))
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    fill = 0.0
    n_out = 0
    n_tot = 0
    for pid, verts, tris, mid in parts:
        Pm = (verts - c) * 1e-3
        step = max(1, len(Pm) // 400)
        for p in Pm[::step]:
            uv = world_to_camera_view(sc, cam, Vector(tuple(p)))
            n_tot += 1
            if not (0 <= uv.x <= 1 and 0 <= uv.y <= 1):
                n_out += 1
                fill = max(fill, max(abs(uv.x - 0.5), abs(uv.y - 0.5)) * 2.0)
    print("FIT", it, "d", round(d, 4), "fill", round(fill, 3), "out", n_out, "/", n_tot)
    if abs(fill - 0.78) < 0.06 or fill < 0.05:
        break
    d *= max(0.5, min(2.0, fill / 0.78))
cam.location = Vector((math.sin(az) * math.cos(el) * d, -math.cos(az) * math.cos(el) * d, math.sin(el) * d))
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.view_layer.update()

if "cyc" in bpy.data.objects:
    bpy.data.objects["cyc"].hide_render = True  # 弧幕试验件退出渲染
# 背幕: 瓶后 2.2m 竖板 4×3 暗灰 — 上框全被实体墙占据 (白背景根因隔离)
bme = bpy.data.meshes.new("backdrop")
bme.from_pydata([(2.2, 2.2, gz), (-2.2, 2.2, gz), (-2.2, 2.2, gz + 3.0), (2.2, 2.2, gz + 3.0)], [], [(0, 1, 2, 3)])
bme.validate()
bob = bpy.data.objects.new("backdrop", bme)
sc.collection.objects.link(bob)
bm2 = bpy.data.materials.new("backdrop_gray"); bm2.use_nodes = True
bb2 = bm2.node_tree.nodes["Principled BSDF"]
bb2.inputs["Base Color"].default_value = (0.13, 0.135, 0.14, 1)
bb2.inputs["Roughness"].default_value = 0.85
bme.materials.append(bm2)
import os
out = os.environ.get("RENDER_OUT", "/tmp/author/render.png")
for o in sc.collection.objects:
    if o.type == 'MESH':
        co = [o.matrix_world @ v.co for v in o.data.vertices]
        mn = tuple(round(float(min(p[i] for p in co)), 2) for i in range(3))
        mx = tuple(round(float(max(p[i] for p in co)), 2) for i in range(3))
        print('MESH', o.name, 'verts', len(o.data.vertices), 'bbox', mn, '->', mx)
print('DBG cam loc:', tuple(round(x,3) for x in cam.location))
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("FINAL OK", out)
