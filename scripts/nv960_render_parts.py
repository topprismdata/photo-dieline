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
