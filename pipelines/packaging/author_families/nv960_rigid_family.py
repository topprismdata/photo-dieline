# nv960_rigid_family.py
# Pack10K Author Contract v1 — NV960 战役 B 组: 零售刚体容器 12 类 (旋转体)
#
# Units: mm, Z-up, ground z=0.
# 每类: 主体 (封闭旋转壳, 壁厚≥0.8mm) + 可选盖/泵/喷头零件。
# 材质: 库内 glass_clear/metal_alu/metal_steel/plastic_pp/plastic_hdpe/plastic_pet_clear/ceramic_gloss。
# H 含盖; D 含最宽外表面。容量口径为类命名, 非标定容积。

import math

FAMILY = "nv960_rigid"

CLASSES = [
    "spice_jar_flip_top",
    "swing_top_bottle",
    "insulated_water_bottle",
    "mason_jar",
    "glass_jar_clamp_lid",
    "food_tin_can",
    "cookie_jar",
    "soap_dispenser",
    "spray_bottle",
    "milk_can",
    "wine_decanter",
    "detergent_bottle",
]

DEFAULTS = {
    "spice_jar_flip_top": {"H": 110.0, "D": 45.0},
    "swing_top_bottle": {"H": 300.0, "D": 82.0},
    "insulated_water_bottle": {"H": 250.0, "D": 70.0},
    "mason_jar": {"H": 130.0, "D": 80.0},
    "glass_jar_clamp_lid": {"H": 145.0, "D": 82.0},
    "food_tin_can": {"H": 110.0, "D": 85.0},
    "cookie_jar": {"H": 180.0, "D": 110.0},
    "soap_dispenser": {"H": 190.0, "D": 70.0},
    "spray_bottle": {"H": 260.0, "D": 90.0},
    "milk_can": {"H": 400.0, "D": 220.0},
    "wine_decanter": {"H": 250.0, "D": 240.0},
    "detergent_bottle": {"H": 300.0, "D": 120.0},
}

_SEGMENTS = 96

_BODY_MAT = {
    "spice_jar_flip_top": "glass_clear",
    "swing_top_bottle": "glass_clear",
    "insulated_water_bottle": "metal_steel",
    "mason_jar": "glass_clear",
    "glass_jar_clamp_lid": "glass_clear",
    "food_tin_can": "metal_alu",
    "cookie_jar": "glass_clear",
    "soap_dispenser": "plastic_pp",
    "spray_bottle": "plastic_pet_clear",
    "milk_can": "metal_steel",
    "wine_decanter": "glass_clear",
    "detergent_bottle": "plastic_hdpe",
}


def _smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _append(profile, samples):
    for z, r in samples:
        p = (float(z), float(r))
        if profile:
            q = profile[-1]
            if abs(p[0] - q[0]) < 1e-9 and abs(p[1] - q[1]) < 1e-9:
                continue
        profile.append(p)


def _revolve(profile):
    """轮廓 (z, r) 旋转成封闭流形三角网格。轮廓必须起止于轴 (r=0),
    路径: 底面 → 外壁 → 顶 → 内壁 (封闭实体壳)。"""
    n = _SEGMENTS
    if profile[0][1] != 0.0 or profile[-1][1] != 0.0:
        raise ValueError("Profile must terminate on axis")
    verts, tris, rings = [], [], []
    cs = [(math.cos(2.0 * math.pi * i / n), math.sin(2.0 * math.pi * i / n))
          for i in range(n)]
    for k, (z, r) in enumerate(profile):
        if not math.isfinite(z) or not math.isfinite(r):
            raise ValueError("Non-finite profile")
        if r < 0.0:
            raise ValueError("Negative radius")
        if r == 0.0:
            if k not in (0, len(profile) - 1):
                raise ValueError("Unexpected interior pole")
            rings.append([len(verts)])
            verts.append([0.0, 0.0, z])
        else:
            ring = []
            for c, s in cs:
                ring.append(len(verts))
                verts.append([r * c, r * s, z])
            rings.append(ring)
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            if len(a) == 1:
                tris.append([a[0], b[j], b[i]])
            elif len(b) == 1:
                tris.append([a[i], a[j], b[0]])
            else:
                tris.append([a[i], a[j], b[j]])
                tris.append([a[i], b[j], b[i]])
    return verts, tris


def _shell(h_body, r_max, r_neck, wall, shoulder_frac=0.75, base_r=None):
    """通用容器封闭壳: 底 → 外壁 → 颈口 → 内壁回落 → 内底 → 轴闭合。"""
    base_r = base_r if base_r is not None else r_max * 0.92
    z_neck = h_body
    z_sh = h_body * shoulder_frac
    p = []
    _append(p, [(0.0, 0.0)])
    _append(p, [(0.0, base_r)])
    _append(p, [(h_body * 0.04, r_max)])
    # 外壁: 基部到底肩 (直线) + 肩部收颈 (smoothstep)
    steps = 10
    for i in range(1, steps + 1):
        t = i / steps
        z = h_body * 0.04 + (z_sh - h_body * 0.04) * t
        _append(p, [(z, r_max)])
    for i in range(1, steps + 1):
        t = i / steps
        z = z_sh + (z_neck - z_sh) * t
        rr = r_max + (r_neck - r_max) * _smoothstep(t)
        _append(p, [(z, rr)])
    # 颈口翻边 → 内壁
    _append(p, [(z_neck, r_neck - wall)])
    for i in range(steps, -1, -1):
        t = i / steps
        z = z_sh + (z_neck - z_sh) * t
        rr = r_max + (r_neck - wall - r_max) * _smoothstep(t)
        _append(p, [(z, rr)])
    for i in range(steps, -1, -1):
        t = i / steps
        z = h_body * 0.04 + (z_sh - h_body * 0.04) * t
        _append(p, [(z, r_max - wall)])
    _append(p, [(h_body * 0.04 + wall, r_max - wall)])
    _append(p, [(wall * 1.5, base_r - wall)])
    _append(p, [(wall * 1.5, 0.0)])
    return p


def _lid_disc(r_lid, h_lid, mat, z0=0.0):
    """浅盘盖: 顶面微拱, 底置于 z0 (落在瓶口上)。"""
    p = []
    _append(p, [(z0, 0.0)])
    _append(p, [(z0 + 0.6, r_lid * 0.92)])
    _append(p, [(z0 + h_lid - 0.8, r_lid * 0.98)])
    _append(p, [(z0 + h_lid, r_lid)])
    _append(p, [(z0 + h_lid, r_lid - 0.8)])
    _append(p, [(z0 + h_lid - 0.8, r_lid * 0.98 - 0.8)])
    _append(p, [(z0 + 0.6, r_lid * 0.92 - 0.8)])
    _append(p, [(z0 + 1.4, 0.0)])
    verts, tris = _revolve(p)
    return {"name": "lid", "verts_mm": verts, "tris": tris, "material_id": mat}


def _pump_head(r_neck, h_total, mat):
    """泵头: 颈套 + 锥头 (合并单零件, 封闭)。"""
    p = []
    _append(p, [(0.0, 0.0)])
    _append(p, [(0.0, r_neck * 0.72)])
    _append(p, [(h_total * 0.10, r_neck * 0.72)])
    _append(p, [(h_total * 0.42, r_neck * 0.34)])
    _append(p, [(h_total * 0.52, r_neck * 0.40)])
    _append(p, [(h_total * 0.70, r_neck * 0.22)])
    _append(p, [(h_total * 0.82, r_neck * 0.16)])
    _append(p, [(h_total, r_neck * 0.10)])
    _append(p, [(h_total, 0.0)])
    verts, tris = _revolve(p)
    return {"name": "pump", "verts_mm": verts, "tris": tris, "material_id": mat}


def build_parts(params: dict) -> list[dict]:
    parts = []
    wall = 1.0
    # 每类: (H, D, 颈比, 肩位, 附加零件钩)
    spec = {
        "spice_jar_flip_top": (110.0, 45.0, 0.55, 0.86, "flip"),
        "swing_top_bottle": (300.0, 82.0, 0.42, 0.80, "stopper"),
        "insulated_water_bottle": (250.0, 70.0, 0.52, 0.86, "cap"),
        "mason_jar": (130.0, 80.0, 0.84, 0.90, "lid"),
        "glass_jar_clamp_lid": (145.0, 82.0, 0.82, 0.90, "clamp_lid"),
        "food_tin_can": (110.0, 85.0, 0.95, 0.97, "tin_lid"),
        "cookie_jar": (180.0, 110.0, 0.80, 0.88, "lid"),
        "soap_dispenser": (190.0, 70.0, 0.42, 0.84, "pump"),
        "spray_bottle": (260.0, 90.0, 0.36, 0.80, "trigger"),
        "milk_can": (400.0, 220.0, 0.50, 0.78, "milk_lid"),
        "wine_decanter": (250.0, 240.0, 0.16, 0.30, None),
        "detergent_bottle": (300.0, 120.0, 0.30, 0.82, "cap"),
    }
    # 显式类选择 (编译驱动传 class_id); 兼容 H/D 值匹配
    cid = CLASSES[0]
    if isinstance(params, dict):
        if params.get("class_id") in DEFAULTS:
            cid = params["class_id"]
        else:
            for c in CLASSES:
                if params.get("H") == DEFAULTS[c]["H"] and params.get("D") == DEFAULTS[c]["D"]:
                    cid = c
                    break
    H, D, neck_f, sh_f, extra = spec[cid]
    r_max = D / 2.0
    r_neck = r_max * neck_f
    mat = _BODY_MAT[cid]

    if cid == "wine_decanter":
        # 球 bowl + 长颈: 定制轮廓
        p = []
        _append(p, [(0.0, 0.0)])
        _append(p, [(6.0, r_max * 0.55)])
        _append(p, [(30.0, r_max * 0.85)])
        _append(p, [(70.0, r_max)])
        _append(p, [(110.0, r_max * 0.80)])
        _append(p, [(140.0, r_max * 0.42)])
        _append(p, [(160.0, r_max * 0.22)])
        _append(p, [(215.0, r_max * 0.14)])
        _append(p, [(235.0, r_max * 0.16)])
        _append(p, [(250.0, r_max * 0.10)])
        _append(p, [(250.0, r_max * 0.10 - wall)])
        _append(p, [(235.0, r_max * 0.16 - wall)])
        _append(p, [(215.0, r_max * 0.14 - wall)])
        _append(p, [(160.0, r_max * 0.22 - wall)])
        _append(p, [(140.0, r_max * 0.42 - wall)])
        _append(p, [(110.0, r_max * 0.80 - wall)])
        _append(p, [(70.0, r_max - wall)])
        _append(p, [(30.0, r_max * 0.85 - wall)])
        _append(p, [(6.0, r_max * 0.55 - wall)])
        _append(p, [(7.5, 0.0)])
        verts, tris = _revolve(p)
        parts.append({"name": "body", "verts_mm": verts, "tris": tris, "material_id": mat})
        return parts

    # z_body: 使 body+零件 总高精确 = H (G-F4)
    _EXTRA_TOP = {"flip": 9.0, "stopper": 36.0, "cap": 14.0, "trigger": 42.0,
                  "pump": 0.0, "lid": 8.8, "tin_lid": 5.8, "milk_lid": 12.8, "clamp_lid": 8.8}
    h_body = H - _EXTRA_TOP.get(extra, 0.0) if extra else H
    body = _shell(h_body, r_max, r_neck, wall, sh_f)
    verts, tris = _revolve(body)
    parts.append({"name": "body", "verts_mm": verts, "tris": tris, "material_id": mat})

    z_body = h_body

    if extra == "flip":
        p = []
        r_t = r_neck + 2.0
        _append(p, [(z_body - 1.0, 0.0)])
        _append(p, [(z_body - 1.0, r_neck * 0.7)])
        _append(p, [(z_body + 1.0, r_t * 0.8)])
        _append(p, [(z_body + 9.0, r_t)])
        _append(p, [(z_body + 9.0, r_t - 1.2)])
        _append(p, [(z_body + 1.5, r_t * 0.8 - 1.2)])
        _append(p, [(z_body + 1.0, 0.6)])
        _append(p, [(z_body + 1.0, 0.0)])
        v, t = _revolve(p)
        parts.append({"name": "flip_top", "verts_mm": v, "tris": t,
                      "material_id": "plastic_pp"})
    elif extra == "stopper":
        p = []
        r_t = r_neck + 1.5
        _append(p, [(z_body - 1.0, 0.0)])
        _append(p, [(z_body - 1.0, r_neck * 0.7)])
        _append(p, [(z_body + 2.0, r_t)])
        _append(p, [(z_body + 6.0, r_t * 0.9)])
        _append(p, [(z_body + 22.0, r_t * 0.55)])
        _append(p, [(z_body + 34.0, r_t * 0.85)])
        _append(p, [(z_body + 36.0, r_t * 0.7)])
        _append(p, [(z_body + 30.0, 1.0)])
        _append(p, [(z_body + 8.0, 1.0)])
        _append(p, [(z_body + 2.0, 0.5)])
        _append(p, [(z_body + 2.0, 0.0)])
        v, t = _revolve(p)
        parts.append({"name": "stopper", "verts_mm": v, "tris": t,
                      "material_id": "ceramic_gloss"})
    elif extra in ("lid", "tin_lid", "milk_lid", "clamp_lid"):
        r_lid = min(r_neck + (6.0 if cid in ("mason_jar", "glass_jar_clamp_lid", "milk_can") else 1.5), r_max - 0.2)
        z0 = z_body - 2.0
        h_lid = H - z0  # 盖顶精确 = H (G-F4)
        lmat = "metal_alu" if cid in ("mason_jar", "food_tin_can", "insulated_water_bottle") else "metal_steel" if cid == "milk_can" else "glass_clear"
        parts.append(_lid_disc(r_lid, h_lid, lmat, z0=z0))
    elif extra == "pump":
        parts.append(_pump_head(r_neck, H - z_body, "plastic_pp"))
    elif extra == "trigger":
        p = []
        r_t = r_neck + 1.0
        _append(p, [(z_body - 1.0, 0.0)])
        _append(p, [(z_body - 1.0, r_neck * 0.7)])
        _append(p, [(z_body + 4.0, r_t)])
        _append(p, [(z_body + 12.0, r_t * 0.8)])
        _append(p, [(z_body + 26.0, r_t * 0.5)])
        _append(p, [(z_body + 40.0, r_t * 0.9)])
        _append(p, [(z_body + 42.0, r_t * 0.6)])
        _append(p, [(z_body + 30.0, 1.2)])
        _append(p, [(z_body + 6.0, 1.0)])
        _append(p, [(z_body + 1.0, 0.4)])
        _append(p, [(z_body + 1.0, 0.0)])
        v, t = _revolve(p)
        parts.append({"name": "trigger", "verts_mm": v, "tris": t,
                      "material_id": "plastic_pp"})
    elif extra == "cap":
        p = []
        r_t = r_neck + 1.0
        _append(p, [(z_body - 1.0, 0.0)])
        _append(p, [(z_body - 1.0, r_t)])
        _append(p, [(z_body + 14.0, r_t)])
        _append(p, [(z_body + 14.0, r_t - 1.2)])
        _append(p, [(z_body + 1.5, r_t - 1.2)])
        _append(p, [(z_body + 1.0, 0.5)])
        _append(p, [(z_body + 1.0, 0.0)])
        v, t = _revolve(p)
        parts.append({"name": "cap", "verts_mm": v, "tris": t,
                      "material_id": "plastic_hdpe"})
    return parts
