import bpy, math, os, json
bpy.ops.wm.read_factory_settings(use_empty=True)
M = 0.001
base = "/Users/guohongbin/photo-dieline"
# G0 冻结几何复用: 与 g0_final 相同布局 (砖1 x=0, 砖2 x=0.115, 瓶 x=0.2375)
gray = (0.88, 0.88, 0.90, 1)  # 非印刷面: 白卡纸
def plain_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = gray
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.6
    return m
def print_mat(name, tex_path):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]; bsdf.inputs["Roughness"].default_value = 0.55
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = bpy.data.images.load(tex_path)
    nt.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"])
    return m
def make_box_print(name, w, d, h, x, tex):
    bpy.ops.mesh.primitive_cube_add(location=(x, 0, h/2*M), scale=(w/2*M, d/2*M, h/2*M))
    o = bpy.context.object; o.name = name
    mprint = print_mat(name + "_front", tex)
    mplain = plain_mat(name + "_plain")
    # 顶封棱
    bpy.ops.mesh.primitive_cube_add(location=(x, 0, h*M + 0.0008), scale=(w/2*M*0.96, 0.0012, 0.0008))
    bpy.context.object.data.materials.append(mplain)
    for dx in (-1, 1):
        bpy.ops.mesh.primitive_cube_add(location=(x + dx*(w/2*M)*0.92, d/2*M*0.55, h/2*M),
                                        scale=(0.0008, 0.0012, h/2*M*0.98))
        bpy.context.object.data.materials.append(mplain)
    # 前面 (-Y normal) 贴 print, 其余 5 面 plain
    for poly in o.data.polygons:
        n = poly.normal
        if n.y < -0.9:
            poly.material_index = 0
        else:
            poly.material_index = 1
    o.data.materials.append(mprint)  # slot 0
    o.data.materials.append(mplain)  # slot 1
    # 显式 UV 重写: u=+X (面宽), v=+Z (面高) — 覆盖默认可能旋转的 UV
    uv = o.data.uv_layers.new()
    for loop in o.data.loops:
        co = o.data.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = ((co.x + w/2*M) / (w*M), co.z / (h*M))
make_box_print("JINDIAN", 55, 40, 115, 0.0,
               "/Users/guohongbin/photo-dieline/docs/research/evidence/r32_scene_contract_placeholder.png" if False else
               "/Users/guohongbin/photo-dieline/output/r32_scene/textures_v2/DAIRY-01.png")
make_box_print("ANMUXI", 55, 40, 115, 0.115,
               "/Users/guohongbin/photo-dieline/output/r32_scene/textures_v2/DAIRY-03.png")
# 娟姗瓶: 瓶身环面贴标签带 (圆柱 UV 环向), 瓶颈/盖素色
bx = 0.2375
profile = [(0,0),(33,0),(35,10),(35,110),(28,132),(16,146),(14,152),(15,156),(15,168),(13,171),(0,173)]
verts, edges, faces, uvs = [], [], [], []
n_ring = 48
uv_done = []
for ri, (r, z) in enumerate(profile):
    a0 = ri * n_ring
    for k in range(n_ring):
        a = 2*math.pi*k/n_ring
        verts.append((bx + r*M*math.cos(a), r*M*math.sin(a), z*M))
        uvs.append(((k/n_ring + 0.25) % 1.0, ri/(len(profile)-1)))
    if ri > 0:
        prev = a0 - n_ring
        for k in range(n_ring):
            k2 = (k+1) % n_ring
            faces.append((prev+k, prev+k2, a0+k2, a0+k))
mesh_data = bpy.data.meshes.new("JUANSHAN_BOTTLE")
mesh_data.from_pydata(verts, edges, faces)
uv_layer = mesh_data.uv_layers.new()
for li, loop in enumerate(mesh_data.loops):
    uv_layer.data[li].uv = uvs[loop.vertex_index]
for poly in mesh_data.polygons: poly.use_smooth = True
bottle = bpy.data.objects.new("JUANSHAN_BOTTLE", mesh_data)
bpy.context.collection.objects.link(bottle)
mbody = bpy.data.materials.new("bottle_label"); mbody.use_nodes = True
nt = mbody.node_tree
bsdf = nt.nodes["Principled BSDF"]; bsdf.inputs["Roughness"].default_value = 0.4
tn = nt.nodes.new("ShaderNodeTexImage")
# 瓶标: 生成带状标签 (PIL 已有 DAIRY-09 512×900, 环向映射会有拉伸—可接受首轮)
tn.image = bpy.data.images.load("/Users/guohongbin/photo-dieline/output/r32_scene/textures/DAIRY-09.png")
nt.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"])
bottle.data.materials.append(mbody)
# 瓶盖
bpy.ops.mesh.primitive_cylinder_add(location=(bx, 0, 0.169), radius=0.0155, depth=0.012)
cap = bpy.context.object
cm = bpy.data.materials.new("cap"); cm.use_nodes = True
cm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.18, 0.18, 0.20, 1)
cap.data.materials.append(cm)
# 地面/灯光/相机 — 全部沿用 G0 冻结配置
bpy.ops.mesh.primitive_plane_add(location=(0.12, 0, -0.001), scale=(0.45, 0.35, 1))
g = bpy.context.object
gm = bpy.data.materials.new("ground"); gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.88, 0.88, 0.90, 1)
g.data.materials.append(gm)
bpy.ops.object.light_add(type='SUN', location=(0.12, -0.4, 0.8))
l1 = bpy.context.object; l1.data.energy = 0.9
bpy.ops.object.light_add(type='AREA', location=(0.12, -0.3, 0.45))
l2 = bpy.context.object; l2.data.energy = 10; l2.data.size = 0.4
wld = bpy.data.worlds.new("W"); wld.use_nodes = True
wld.node_tree.nodes["Background"].inputs[0].default_value = (0.75, 0.76, 0.78, 1)
bpy.context.scene.world = wld
bpy.ops.object.empty_add(location=(0.12, 0, 0.09))
target = bpy.context.object
bpy.ops.object.camera_add(location=(0.12, -0.72, 0.16))
cam = bpy.context.object
tc = cam.constraints.new('TRACK_TO'); tc.target = target; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
bpy.context.scene.camera = cam
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Filmic'
sc.render.resolution_x = 1400; sc.render.resolution_y = 700
sc.render.filepath = "/Users/guohongbin/photo-dieline/docs/research/evidence/r38_g1r3_print.png"
bpy.ops.render.render(write_still=True)
bpy.ops.object.camera_add(location=(0.12, -0.6, 0.0875), rotation=(math.radians(90), 0, 0))
cam2 = bpy.context.object; cam2.data.type = 'ORTHO'; cam2.data.ortho_scale = 0.40
bpy.context.scene.camera = cam2
sc.render.filepath = "/Users/guohongbin/photo-dieline/docs/research/evidence/r38_g1r3_print_ortho.png"
bpy.ops.render.render(write_still=True)
print("RENDER_OK_G1")
