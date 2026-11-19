"""TDE Blender 渲染驱动 (在 bpy 内运行: blender --background --python driver.py -- payload.json).

职责: 载入折叠 OBJ → 建材质/灯/相机 (采样配置) → Cycles 渲染 PNG。
随机化数值全部来自 payload (sampler 产物), 本脚本不含采样逻辑。
遵循 blender-headless-agent-scene: 幂等清理 / view_layer.update / AgX 曝光纪律 / pixel-stat。
"""
import hashlib
import json
import math
import sys

import bpy
import mathutils

CLEAN_TYPES = (bpy.data.objects, bpy.data.meshes, bpy.data.materials,
               bpy.data.cameras, bpy.data.lights, bpy.data.images)


def clean_scene():
    for coll in CLEAN_TYPES:
        for item in list(coll):
            coll.remove(item, do_unlink=True)


ROLE_PRINT = {
    "wall": (0.36, 0.49, 0.70),   # 品牌蓝 (主展示面语义)
    "slope": (0.78, 0.42, 0.30),  # 坡面图案橙红 (人字顶辨识核心)
    "fin": (0.55, 0.55, 0.58),    # 立鳍中性
    "flap": (0.45, 0.45, 0.48),   # 底/盖深灰
    "glue": (0.62, 0.62, 0.60),   # 粘口纸本色
    "gable_end": (0.36, 0.49, 0.70),
}


def build_material(roughness: float, base_color, tint_seed: float, role: str = "wall"):
    mat = bpy.data.materials.new("card")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    # 印刷语义色: 角色基准色 × 基色亮度调制 ±12% 面板抖动 (印刷面板边界可读)
    base = ROLE_PRINT.get(role, tuple(base_color))
    k = 0.88 + (tint_seed % 1.0) * 0.24
    lum = sum(base_color) / 3.0
    col = [min(1.0, b * k * (0.42 + 0.40 * lum) * 0.82) for b in base]
    bsdf.inputs["Base Color"].default_value = (*col, 1.0)
    bsdf.inputs["Roughness"].default_value = min(roughness, 0.42)
    return mat


def kelvin_rgb(k: float):
    """近似黑体色温 → RGB (Tanner Helland 拟合, 归一化)."""
    t = k / 100.0
    if t <= 66:
        r, g = 255.0, 99.47 * math.log(t) - 161.12
    else:
        r = 329.7 * (t - 60) ** -0.1332
        g = 288.12 * (t - 60) ** -0.0755
    b = 255.0 if t >= 66 else (0.0 if t <= 19 else 138.52 * math.log(t - 10) - 305.04)
    c = [max(0.0, min(255.0, v)) / 255.0 for v in (r, g, b)]
    m = max(c)
    return [v / m for v in c]


def add_scene(payload):
    sc = bpy.context.scene
    cam = payload["camera"]
    light = payload["lighting"]
    mat = payload["material"]

    # 材质: 每面板独立印刷色 (角色基准+面板抖动, 种子=对象名 hash)
    obj_to_role = payload.get("panel_roles", {})
    for ob in bpy.data.objects:
        if ob.type == "MESH":
            seed = float(int(hashlib.md5(ob.name.encode()).hexdigest()[:8], 16) % 997) / 997
            m = build_material(mat["roughness"], mat["base_color"], seed,
                               obj_to_role.get(ob.name, "wall"))
            ob.data.materials.clear()
            ob.data.materials.append(m)

    # 包围盒中心 (payload 毫米 → 米制场景 ×0.001, 与 OBJ 导入缩放一致)
    ctr = mathutils.Vector(payload["center_mm"]) * 0.001

    # 相机: 等效焦距 (sensor 36mm) → lens mm; 球坐标眼位; roll 绕视线轴
    # 场景米制: OBJ 已按 0.001 缩放导入, payload 距离/中心均为米
    lens = cam["equiv_focal_mm"]
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = lens
    cam_data.sensor_width = 36.0
    cam_data.dof.use_dof = True
    cam_data.dof.aperture_fstop = cam["aperture_fstop"]
    az = math.radians(cam["yaw_deg"])
    el = math.radians(cam["pitch_deg"])
    d = cam["distance_m"]
    fwd = mathutils.Vector((math.cos(el) * math.sin(az), -math.cos(el) * math.cos(az),
                            math.sin(el)))
    eye = ctr + fwd * d * 1.35
    cam_obj = bpy.data.objects.new("cam", cam_data)
    cam_obj.location = eye
    # 朝向: -Z 对准目标, 再加 roll
    direction = ctr - eye
    rot = direction.to_track_quat("-Z", "Y").to_euler()
    rot.rotate_axis("Z", math.radians(cam["roll_deg"]))
    cam_obj.rotation_euler = rot
    bpy.context.collection.objects.link(cam_obj)
    sc.camera = cam_obj
    cam_data.dof.focus_distance = d * 1.35  # 眼距= d*1.35 (margin同上), 焦平面须在主体上

    # 渲染输出
    sc.render.engine = "CYCLES"
    sc.cycles.samples = payload.get("samples", 48)
    sc.cycles.use_denoising = True
    sc.render.resolution_x = payload.get("res", 384)
    sc.render.resolution_y = payload.get("res", 384)
    sc.render.film_transparent = False
    sc.view_settings.exposure = max(-0.7, min(0.7, light["exposure_ev"]))
    try:
        sc.view_settings.look = "AgX - Punchy"
    except Exception:
        pass
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.get_devices()
    for dev in prefs.devices:
        dev.use = True

    # 灯光: Key SUN 方向光 (色温, 无距离衰减, 曝光稳定) + 环境世界 + 小面积补光
    kd = bpy.data.lights.new("key", "SUN")
    kd.energy = 5.0 * light["key_intensity_x"]
    kd.angle = math.radians(9.0)
    kd.color = kelvin_rgb(light["kelvin"])
    key = bpy.data.objects.new("key", kd)
    key.location = (ctr.x + d * 0.5, ctr.y - d * 0.8, ctr.z + d * 0.9)
    kd_dir = mathutils.Vector((ctr.x - key.location.x, ctr.y - key.location.y,
                               ctr.z - key.location.z)).normalized()
    key.rotation_euler = kd_dir.to_track_quat("-Z", "Y").to_euler()
    bpy.context.collection.objects.link(key)
    kd2 = bpy.data.lights.new("fill", "AREA")
    kd2.energy = 2.0 * light["key_intensity_x"] * light["ambient_ratio"] * 2
    kd2.size = max(0.5, d * 0.8)
    kd2.color = kelvin_rgb(light["kelvin"] + 400)
    fill = bpy.data.objects.new("fill", kd2)
    fill.location = (ctr.x - d * 0.7, ctr.y + d * 0.3, ctr.z + d * 0.4)
    bpy.context.collection.objects.link(fill)
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    amb_col = kelvin_rgb(light["kelvin"] + 200)
    bg.inputs[0].default_value = (*amb_col, 1.0)
    bg.inputs[1].default_value = (0.35 + 0.5 * light["ambient_ratio"]) * 0.40
    sc.world = w

    # 环境: 地面 + 背景板 (场景类简化程序化; 白底棚拍提亮)
    scene = payload["scene"]
    ground_col = {"STUDIO": (0.55, 0.55, 0.56), "PHONE_DESKTOP": (0.42, 0.32, 0.24),
                  "PHONE_INDOOR": (0.45, 0.42, 0.38), "PHONE_WINDOW_LIGHT": (0.50, 0.48, 0.45),
                  "PHONE_SUPERMARKET": (0.55, 0.55, 0.57), "PHONE_HANDHELD": (0.40, 0.38, 0.36)}.get(scene, (0.5, 0.5, 0.5))
    gmesh = bpy.data.meshes.new("ground")
    s = max(d * 2.5, 1.0)
    g_z = payload["bbox_min_mm"][2] * 0.001 - 0.002
    gmesh.from_pydata([(-s, -s, g_z), (s, -s, g_z), (s, s, g_z), (-s, s, g_z)],
                      [], [(0, 1, 2), (0, 2, 3)])
    gm = bpy.data.materials.new("ground")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*ground_col, 1.0)
    gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
    gobj = bpy.data.objects.new("ground", gmesh)
    gobj.data.materials.append(gm)
    bpy.context.collection.objects.link(gobj)

    bpy.context.view_layer.update()  # matrix 惰性坑
    sc.render.filepath = payload["out_png"]
    bpy.ops.render.render(write_still=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    label = json.load(open(argv[0]))
    payload = label["render_payload"] if "render_payload" in label else label
    clean_scene()
    bpy.ops.wm.obj_import(filepath=payload["obj_path"], global_scale=0.001,
                          forward_axis="NEGATIVE_Y", up_axis="Z")
    add_scene(payload)


main()
