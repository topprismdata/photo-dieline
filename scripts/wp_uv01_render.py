"""R14-UV-01: 轻量 UV 渲染验证 — brick 系两家族 × S0/S1/S2 × 六正交视角 (36张, Eevee+Emission诊断纹理)"""
import sys, os, math
sys.path.insert(0, "scripts")
import numpy as np
from pxr import Usd, UsdGeom, Sdf, Gf, Vt
import bpy
import mathutils

TEX = "/Users/guohongbin/photo-dieline/output/candidates/aseptic_brick_v0000/wp_a12/diag_texture.png"
OUT = "output/candidates/aseptic_brick_v0000/wp_a12/uv_verify"
os.makedirs(OUT, exist_ok=True)

CASES = [
    ("aseptic_brick", "S0", "output/candidates/aseptic_brick_v0000/wp_fixed/model_S0_frozen.usdc"),
    ("aseptic_brick", "S1", "output/candidates/aseptic_brick_v0000/wp_fixed/model_fixed.usdc"),
    ("aseptic_brick", "S2", "output/candidates/aseptic_brick_v0000/wp_fixed/model_normalized.usdc"),
    ("brick_250ml", "S0", "output/candidates/brick_250ml_v0000/wp_fixed/model_S0_frozen.usdc"),
    ("brick_250ml", "S1", "output/candidates/brick_250ml_v0000/wp_fixed/model_S1_fixed.usdc"),
    ("brick_250ml", "S2", "output/candidates/brick_250ml_v0000/wp_fixed/model_S2_normalized.usdc"),
]
VIEWS = [("px", 0, 0), ("nx", 180, 0), ("py", 90, 0), ("ny", 270, 0), ("pz", 0, 90), ("nz", 0, -90)]


# Emission 诊断材质
mat = bpy.data.materials.new("DiagEmission")
mat.use_nodes = True
nt = mat.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
texnode = nt.nodes.new("ShaderNodeTexImage")
texnode.image = bpy.data.images.load(TEX, check_existing=True)
print("TEX loaded:", texnode.image is not None, texnode.image.size[0] if texnode.image else 0)
em = nt.nodes.new("ShaderNodeEmission")
em.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
em.inputs[1].default_value = 1.0
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(texnode.outputs["Color"], em.inputs[0])
nt.links.new(em.outputs[0], out.inputs[0])

done = 0
for fam, stage_tag, path in CASES:
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = 512; sc.render.resolution_y = 512
    sc.view_settings.view_transform = "Standard"
    bpy.ops.wm.usd_import(filepath=path, import_cameras=False, import_lights=False)
    mesh_prims = [p for p in sc.collection.all_objects if p.type == "MESH"]
    diag = bpy.data.materials.new("DiagEmission_" + stage_tag)
    diag.use_nodes = True
    dnt = diag.node_tree
    for n in list(dnt.nodes): dnt.nodes.remove(n)
    texn = dnt.nodes.new("ShaderNodeTexImage")
    texn.image = bpy.data.images.load(TEX, check_existing=True)
    emn = dnt.nodes.new("ShaderNodeEmission")
    emn.inputs[1].default_value = 1.0
    on = dnt.nodes.new("ShaderNodeOutputMaterial")
    dnt.links.new(texn.outputs["Color"], emn.inputs[0])
    dnt.links.new(emn.outputs[0], on.inputs[0])
    for ob in mesh_prims:
        ob.data.materials.clear()
        ob.data.materials.append(diag)
    # 相机对齐
    mn = np.array([min(ob.matrix_world @ v for v in []) for ob in []]) if False else None
    allpts = []
    for ob in mesh_prims:
        mw = ob.matrix_world
        for corner in ob.bound_box:
            allpts.append(mw @ mathutils.Vector(corner))
    allpts = np.array(allpts)
    mn, mx = allpts.min(0), allpts.max(0)
    ctr = (mn + mx) / 2
    size = float((mx - mn).max())
    cam_data = bpy.data.cameras.new("Ortho")
    cam_data.ortho_scale = size * 1.15
    cam = bpy.data.objects.new("OrthoCam", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    from mathutils import Vector as MV2
    for vname, rotz, rotx in VIEWS:
        d = size * 2
        cam.location = ctr + MV2((
            d * math.cos(math.radians(rotx)) * math.cos(math.radians(rotz)),
            d * math.cos(math.radians(rotx)) * math.sin(math.radians(rotz)),
            d * math.sin(math.radians(rotx))))
        direction = MV2(ctr) - MV2(cam.location)
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        sc.camera = cam
        sc.render.filepath = f"{OUT}/{fam}_{stage_tag}_{vname}.png"
        bpy.ops.render.render(write_still=True)
        done += 1
print(f"RENDERED {done}/36")
