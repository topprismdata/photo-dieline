# nv960_fixture_family.py
# Pack10K Author Contract v1 — NV960 战役 C 组: 零售设备 13+3 类 (盒/栅/框架积木)
# Units: mm, Z-up, ground z=0. 每零件封闭流形; 材质库内。

import math

FAMILY = "nv960_fixture"

CLASSES = [
    "shopping_cart",
    "shopping_basket",
    "barcode_scanner",
    "rotating_display_stand",
    "soda_fountain",
    "napkin_dispenser",
    "queue_ticket_dispenser",
    "juice_dispenser",
    "cereal_dispenser",
    "paper_towel_dispenser",
    "public_trash_can",
    "public_recycling_bin",
    "carton_flow_rack",
    "storage_basket_mesh",
    "wire_mesh_container",
    "bulk_container_mesh",
]

DEFAULTS = {
    "shopping_cart": {"H": 775.0, "D": 501.0},
    "shopping_basket": {"H": 292.0, "D": 392.0},
    "barcode_scanner": {"H": 90.0, "D": 40.0},
    "rotating_display_stand": {"H": 1600.0, "D": 500.0},
    "soda_fountain": {"H": 500.0, "D": 260.0},
    "napkin_dispenser": {"H": 220.0, "D": 122.0},
    "queue_ticket_dispenser": {"H": 350.0, "D": 122.0},
    "juice_dispenser": {"H": 600.0, "D": 210.0},
    "cereal_dispenser": {"H": 700.0, "D": 220.0},
    "paper_towel_dispenser": {"H": 350.0, "D": 122.0},
    "public_trash_can": {"H": 900.0, "D": 548.0},
    "public_recycling_bin": {"H": 950.0, "D": 143.0},
    "carton_flow_rack": {"H": 1800.0, "D": 550.0},
    "storage_basket_mesh": {"H": 200.0, "D": 380.0},
    "wire_mesh_container": {"H": 500.0, "D": 600.0},
    "bulk_container_mesh": {"H": 1000.0, "D": 1100.0},
}


def _box(name, x0, y0, z0, x1, y1, z1, mat):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    q = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    tris = []
    for a, b, c, dd in q:
        tris.append([a, b, c])
        tris.append([a, c, dd])
    return {"name": name, "verts_mm": v, "tris": tris, "material_id": mat}


def _cyl(name, r, z0, z1, mat, cx=0.0, cy=0.0, n=64):
    v, tris = [], []
    for k, z in ((0, z0), (1, z1)):
        base = len(v)
        v.append((cx, cy, z))
        for i in range(n):
            a = 2 * math.pi * i / n
            v.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
        if k == 0:
            for i in range(n):
                tris.append([base, base + 1 + (i + 1) % n, base + 1 + i])
        else:
            for i in range(n):
                tris.append([base, base + 1 + i, base + 1 + (i + 1) % n])
    low, top = 1, 2 + n  # top ring 起点 (1+n 是顶心)
    for i in range(n):
        j = (i + 1) % n
        tris.append([low + i, low + j, top + j])
        tris.append([low + i, top + j, top + i])
    return {"name": name, "verts_mm": v, "tris": tris, "material_id": mat}


def _grid_bars(name, x0, y0, z, x1, y1, pitch, r, mat, axis="x"):
    """细栅条组: axis=x → 沿 x 向条, y 向排布。"""
    parts = []
    if axis == "x":
        k = int((y1 - y0) / pitch)
        for i in range(1, k):
            y = y0 + i * pitch
            parts.append(_box(f"{name}_{i}", x0, y - r, z - r, x1, y + r, z + r, mat))
    else:
        k = int((x1 - x0) / pitch)
        for i in range(1, k):
            x = x0 + i * pitch
            parts.append(_box(f"{name}_{i}", x - r, y0, z - r, x + r, y1, z + r, mat))
    return parts


def build_parts(params: dict) -> list[dict]:
    cid = CLASSES[0]
    if isinstance(params, dict) and params.get("class_id") in DEFAULTS:
        cid = params["class_id"]
    P = []
    steel, pp, alu = "metal_steel", "plastic_pp", "metal_alu"

    if cid == "shopping_basket":
        w, H, t = 388.0, 278.0, 4.0
        P = [_box("wall_n", -w / 2, w / 2 - t, 0, w / 2, w / 2, H, pp),
             _box("wall_s", -w / 2, -w / 2, 0, w / 2, -w / 2 + t, H, pp),
             _box("wall_e", w / 2 - t, -w / 2, 0, w / 2, w / 2, H, pp),
             _box("wall_w", -w / 2, -w / 2, 0, -w / 2 + t, w / 2, H, pp),
             _box("floor", -w / 2, -w / 2, 0, w / 2, w / 2, t, pp)]
        P += _grid_bars("gr", -w / 2, -w / 2, t + 1, w / 2, w / 2, 40, 1.2, pp, axis="x")
        P.append(_box("handle", -w / 2 + 10, -w / 2 - 2, H, w / 2 - 10, -w / 2 + 4, H + 14, pp))
        P.append(_box("handle2", -w / 2 + 10, w / 2 - 4, H, w / 2 - 10, w / 2 + 2, H + 14, pp))
        return P

    if cid == "shopping_cart":
        bw, bh, zb, t = 493.0, 510.0, 220.0, 5.0
        P = [_box("fr_n", -bw / 2, bw / 2 - t, zb, bw / 2, bw / 2, zb + bh, steel),
             _box("fr_s", -bw / 2, -bw / 2, zb, bw / 2, -bw / 2 + t, zb + bh, steel),
             _box("fr_e", bw / 2 - t, -bw / 2, zb, bw / 2, bw / 2, zb + bh, steel),
             _box("fr_w", -bw / 2, -bw / 2, zb, -bw / 2 + t, bw / 2, zb + bh, steel)]
        P += _grid_bars("gx", -bw / 2, -bw / 2, zb + 3, bw / 2, bw / 2, 55, 1.6, steel, "x")
        P += _grid_bars("gy", -bw / 2, -bw / 2, zb + bh - 3, bw / 2, bw / 2, 55, 1.6, steel, "y")
        P.append(_box("frame_lo", -bw / 2, -bw / 2, zb - 5, bw / 2, bw / 2, zb, steel))
        for sx, xn in ((-1, "l"), (1, "r")):
            for sy, yn in ((-1, "f"), (1, "b")):
                P.append(_cyl(f"wheel_{xn}{yn}", 42, 0, 20, pp,
                              cx=sx * (bw / 2 - 60), cy=sy * (bw / 2 - 60)))
        P.append(_box("handle", -bw / 2, -bw / 2 - 8, zb + bh, bw / 2, -bw / 2 + 4, 775.0, steel))
        return P

    if cid == "barcode_scanner":
        return [_box("body", -80.0, -20.0, 0, 80.0, 20.0, 63.0, pp),
                _box("head", -53.0, -16.0, 63.0, 53.0, 16.0, 90.0, pp),
                _box("window", -40.0, -13.0, 84.0, 40.0, 13.0, 90.0, alu)]

    if cid == "rotating_display_stand":
        H, D = params["H"], params["D"]
        P = [_cyl("pole", 14, 40, H, steel),
             _cyl("base", D / 2, 0, 40, steel)]
        lv = 4
        for i in range(lv):
            z = 200 + i * (H - 300) / lv
            P.append(_cyl(f"shelf_{i}", D / 2, z, z + 10, alu))
        return P

    if cid in ("soda_fountain", "juice_dispenser", "cereal_dispenser"):
        H = params["H"]
        D = {"soda_fountain": 230.0, "juice_dispenser": 180.0, "cereal_dispenser": 190.0}[cid]
        P = [_box("tank", -D / 3, -D / 3, H * 0.3, D / 3, D / 3, H, "plastic_pp_translucent"),
             _box("body", -D / 2, -D / 2, 0, D / 2, D / 2, H * 0.3, pp)]
        P.append(_box("tap", -12, -D / 2 - 30, H * 0.18, 12, -D / 2, H * 0.26, alu))
        return P

    if cid in ("napkin_dispenser", "paper_towel_dispenser", "queue_ticket_dispenser"):
        H = params["H"]
        return [_box("body", -59.0, -60.0, 0, 59.0, 60.0, H, pp),
                _box("slot", -30.0, -62.0, H - 50.0, 30.0, -58.0, H - 10.0, alu)]

    if cid == "public_trash_can":
        H = params["H"]
        return [_cyl("body", 262.0, 0, H * 0.85, steel),
                _cyl("hood", 274.0, H * 0.85, H, steel),
                _cyl("liner", 256.0, 0, H * 0.5, alu)]

    if cid == "public_recycling_bin":
        H = params["H"]
        P = []
        for k, cx in enumerate((-65.0, 65.0)):
            P.append(_cyl(f"body_{k}", 61.0, 0, H * 0.85, pp if k == 0 else "plastic_pp_translucent", cx=cx))
            P.append(_cyl(f"hood_{k}", 71.5, H * 0.85, H, steel, cx=cx))
        return P

    if cid == "carton_flow_rack":
        H, w, D = 1800.0, 1000.0, 500.0
        for kx, px in enumerate((-w / 2, w / 2)):
            for ky, py in enumerate((-D / 2, D / 2)):
                P.append(_box(f"post_{kx}_{ky}", px - 25, py - 25, 0, px + 25, py + 25, H, steel))
        for lvl in (0.35, 0.68):
            z = H * lvl
            P.append(_box("beam_a", -w / 2, -D / 2, z, w / 2, -D / 2 + 40, z + 45, steel))
            P.append(_box("beam_b", -w / 2, D / 2 - 40, z, w / 2, D / 2, z + 45, steel))
            P.append(_box("deck", -w / 2 + 20, -D / 2 + 30, z + 45, w / 2 - 20, D / 2 - 30, z + 60, alu))
        return P

    if cid in ("storage_basket_mesh", "wire_mesh_container", "bulk_container_mesh"):
        H, D = params["H"], params["D"]
        w = D
        t = 3.0 if cid == "storage_basket_mesh" else 5.0
        h = H
        P = [_box("fl_n", -w / 2, w / 2 - t, 0, w / 2, w / 2, h, steel),
             _box("fl_s", -w / 2, -w / 2, 0, w / 2, -w / 2 + t, h, steel),
             _box("fl_e", w / 2 - t, -w / 2, 0, w / 2, w / 2, h, steel),
             _box("fl_w", -w / 2, -w / 2, 0, -w / 2 + t, w / 2, h, steel),
             _box("floor", -w / 2, -w / 2, 0, w / 2, w / 2, t, steel)]
        pitch = 45 if cid != "bulk_container_mesh" else 70
        P += _grid_bars("mx", -w / 2, -w / 2, h * 0.55, w / 2, w / 2, pitch, t * 0.5, steel, "x")
        P += _grid_bars("my", -w / 2, -w / 2, h * 0.55, w / 2, w / 2, pitch, t * 0.5, steel, "y")
        P += _grid_bars("mx2", -w / 2, -w / 2, h * 0.85, w / 2, w / 2, pitch, t * 0.5, steel, "x")
        return P

    # 兜底: 素盒
    H, D = params["H"], params["D"]
    return [_box("body", -D / 2, -D / 2, 0, D / 2, D / 2, H, pp)]
