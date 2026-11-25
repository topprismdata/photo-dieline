"""NV960 刚体零件渲染: parts.json → Cycles 影棚 1024² (Blender 内运行).
用法: blender --background --python scripts/nv960_render_parts.py -- <rigid输出目录>
"""
import json
import math
import sys
from pathlib import Path

import bpy
import mathutils

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ROOT = Path(argv[0]) if argv else Path("/tmp/nv960_rigid")

sys.path.append("/opt/homebrew/Caskroom/miniconda/base/lib/python3.13/site-packages")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src/photo_dieline/authoring"))

from render_materials import MATERIALS  # noqa: E402


def add_label_band(parts, label_png):
    """圆柱标签带 (150° 弧段朝 az−45° 相机, 贴身最大半径段), 酒标配方泛化。"""
    import math as _m
    body = max(parts, key=lambda p: len(p["verts"]))
    vs = body["verts"]
    zs = [v[2] for v in vs]
    rs = [_m.hypot(v[0], v[1]) for v in vs]
    r_body = sorted(rs)[int(len(rs) * 0.7)]  # 70 分位半径 (避开盖/头)
    z_min, z_max = min(zs), max(zs)
    z0 = z_min + (z_max - z_min) * 0.22
    z1 = z_min + (z_max - z_min) * 0.62
    r_band = r_body + 0.35
    CENTER_A = _m.radians(-45.0)
    HALF_ARC = _m.radians(75.0)
    SEGS = 96
    verts, faces = [], []
    for i in range(SEGS + 1):
        a = CENTER_A - HALF_ARC + (2 * HALF_ARC) * i / SEGS
        verts.append((r_band * _m.cos(a), r_band * _m.sin(a), z0))
        verts.append((r_band * _m.cos(a), r_band * _m.sin(a), z1))
    for i in range(SEGS):
        a0, b0 = 2 * i, 2 * i + 1
        a1, b1 = 2 * (i + 1), 2 * (i + 1) + 1
        faces.append((a0, b0, b1, a1))
    tris = []
    for f in faces:
        tris.append([f[0], f[1], f[2]])
        tris.append([f[0], f[2], f[3]])
    return {"name": "label_band", "verts": verts, "tris": tris,
            "material_id": "label_paper", "label_png": str(label_png),
            "u_span": (CENTER_A - HALF_ARC, CENTER_A + HALF_ARC),
            "z_span": (z0, z1)}


def _label_uv(me, part):
    """标签带 UV: u=角度展开, v=z 展开 (无翻转=正向文字)。"""
    import math as _m
    a0, a1 = part["u_span"]
    z0, z1 = part["z_span"]
    uv = me.uv_layers.new(name="st")
    for loop in me.loops:
        v = me.vertices[loop.vertex_index]
        ang = _m.atan2(v.co.y, v.co.x)
        u = (ang - a0) / (a1 - a0)
        w = (v.co.z - z0) / (z1 - z0)
        uv.data[loop.index].uv = (min(max(u, 0.0), 1.0), min(max(w, 0.0), 1.0))


def studio(scene):
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 192
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


def render_parts(parts_json: Path, out_png: Path):
    rec = json.loads(parts_json.read_text())
    parts = rec["parts"]
    label_png = None
    cid = rec.get("class_id", parts_json.stem.replace("_parts", ""))
    lp = Path("/tmp/nv960_labels") / f"{cid}.png"
    if lp.exists():
        parts = parts + [add_label_band(parts, lp)]
        label_png = str(lp)
    allz = [v[2] for p in parts for v in p["verts"]]
    gz = min(allz) - 0.001

    sc = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    for ma in list(bpy.data.materials):
        bpy.data.materials.remove(ma)

    gme = bpy.data.meshes.new("ground")
    gz_m = min(allz) / 1000.0 - 0.001
    gme.from_pydata([(-150, -150, gz_m), (150, -150, gz_m), (150, 150, gz_m), (-150, 150, gz_m)],
                    [], [(0, 1, 2, 3)])
    gme.validate()
    gm2 = bpy.data.materials.new("ground_dark")
    gm2.use_nodes = True
    gb2 = gm2.node_tree.nodes["Principled BSDF"]
    gb2.inputs["Base Color"].default_value = (0.055, 0.058, 0.06, 1)
    gb2.inputs["Roughness"].default_value = 0.9
    gme.materials.append(gm2)
    sc.collection.objects.link(bpy.data.objects.new("ground", gme))

    xs, ys, zs = [], [], []
    for p in parts:
        me = bpy.data.meshes.new(p["name"])
        me.from_pydata([tuple(v) for v in p["verts"]], [], [tuple(t) for t in p["tris"]])
        me.validate()
        me.transform(mathutils.Matrix.Scale(0.001, 4))  # mm→m 统一
        if p.get("name") == "label_band" and label_png:
            _label_uv(me, p)
            m = bpy.data.materials.new("label")
            m.use_nodes = True
            tex = m.node_tree.nodes.new("ShaderNodeTexImage")
            tex.image = bpy.data.images.load(label_png)
            b = m.node_tree.nodes["Principled BSDF"]
            b.inputs["Roughness"].default_value = 0.5
            m.node_tree.links.new(tex.outputs["Color"], b.inputs["Base Color"])
        else:
            rgb, rough, metallic, transmission, ior = MATERIALS[p["material_id"]]
            m = bpy.data.materials.new(p["material_id"])
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
        me.materials.append(m)
        ob = bpy.data.objects.new(p["name"], me)
        sc.collection.objects.link(ob)
        xs.append(min(v.co.x for v in me.vertices)); xs.append(max(v.co.x for v in me.vertices))
        ys.append(min(v.co.y for v in me.vertices)); ys.append(max(v.co.y for v in me.vertices))
        zs.append(min(v.co.z for v in me.vertices)); zs.append(max(v.co.z for v in me.vertices))
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    r = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)) * 0.5

    az, el = math.radians(45.0), math.radians(30.0)
    d = r / math.sin(math.atan(18.0 / 60.0)) * 1.12
    eye = mathutils.Vector((cx + math.sin(az) * math.cos(el) * d,
                            cy - math.cos(az) * math.cos(el) * d,
                            min(zs) + math.sin(el) * d))
    cam_data = bpy.data.cameras.new("c")
    cam_data.lens = 60
    cam = bpy.data.objects.new("c", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.location = eye
    cam.rotation_euler = (-eye).to_track_quat("-Z", "Y").to_euler()

    studio(sc)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    sc.render.filepath = str(out_png)
    bpy.ops.render.render(write_still=True)


def main():
    fails = []
    pjs = sorted(ROOT.glob("*_parts.json"))
    print(f"nv960 rigid render: {len(pjs)} 类", flush=True)
    for i, pj in enumerate(pjs):
        out = ROOT / (pj.stem.replace("_parts", "") + ".png")
        try:
            render_parts(pj, out)
            print(f"[{i+1}/{len(pjs)}] {pj.stem} OK", flush=True)
        except Exception as e:  # noqa: BLE001
            fails.append((pj.stem, f"{type(e).__name__} {str(e)[:120]}"))
            print(f"[{i+1}/{len(pjs)}] {pj.stem} FAIL {type(e).__name__}", flush=True)
    print("fails:", fails, flush=True)


main()
