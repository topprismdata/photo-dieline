"""Blender 侧材质库 — 与 photo_dieline.authoring.validate_parts._USD_PARAMS 同参数源。

冻结渲染合同的一部分: 部件引用 material_id, 本库给 BSDF; 禁止逐渲调参。
参数 (rgb, roughness, metallic, transmission, ior):
"""
MATERIALS = {
    "paper_kraft": ((0.44, 0.315, 0.198), 0.84, 0.0, 0.0, 1.45),
    "paper_white": ((0.90, 0.90, 0.88), 0.80, 0.0, 0.0, 1.45),
    "glass_clear": ((0.45, 0.60, 0.54), 0.06, 0.0, 0.78, 1.52),  # 透射玻璃 (暗背景承载提亮)
    "metal_alu": ((0.91, 0.92, 0.92), 0.25, 1.0, 0.0, 1.0),
    "metal_steel": ((0.77, 0.78, 0.78), 0.30, 1.0, 0.0, 1.0),
    "plastic_pp": ((0.85, 0.86, 0.84), 0.38, 0.0, 0.0, 1.49),
    "plastic_pet_clear": ((0.90, 0.94, 0.95), 0.08, 0.0, 1.0, 1.54),
    "plastic_hdpe": ((0.86, 0.86, 0.84), 0.45, 0.0, 0.0, 1.52),
    "wood_pine": ((0.72, 0.56, 0.36), 0.60, 0.0, 0.0, 1.45),
    "ceramic_gloss": ((0.92, 0.92, 0.90), 0.10, 0.0, 0.0, 1.45),
    "tape_craft": ((0.62, 0.52, 0.38), 0.50, 0.0, 0.0, 1.45),
    "label_paper": ((0.92, 0.92, 0.90), 0.70, 0.0, 0.0, 1.45),
    "foil_lid": ((0.85, 0.86, 0.88), 0.20, 1.0, 0.0, 1.0),
}
# corrugated 微表面 (bump) 仅用于 paper_kraft 瓦楞件 — 合同内的家族级选项, 非逐渲调参
CORRUGATED = {"scale": 120.0, "distortion": 2.0, "strength": 0.16}


def build_material(bpy_data, node_class, mid, corrugated=False):
    """mid → bpy material (Principled BSDF + 可选瓦楞 bump)。"""
    rgb, rough, metallic, transmission, ior = MATERIALS[mid]
    m = bpy_data.materials.new(mid)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    b.inputs["IOR"].default_value = ior
    if transmission:
        for key in ("Transmission Weight", "Transmission"):
            if key in b.inputs:
                b.inputs[key].default_value = 1.0
                break
    if corrugated and mid == "paper_kraft":
        tex = nt.nodes.new("ShaderNodeTexCoord")
        wave = nt.nodes.new("ShaderNodeTexWave")
        wave.inputs["Scale"].default_value = CORRUGATED["scale"]
        wave.inputs["Distortion"].default_value = CORRUGATED["distortion"]
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = CORRUGATED["strength"]
        nt.links.new(tex.outputs["Object"], wave.inputs["Vector"])
        nt.links.new(wave.outputs["Color"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m
