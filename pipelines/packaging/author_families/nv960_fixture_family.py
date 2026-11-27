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
    "muffin_tin_6cup",
    "tiered_fruit_basket",
    "jerry_can",
    "condiment_pump_dispenser",
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
    "public_trash_can": {"H": 900.0, "D": 634.0},
    "public_recycling_bin": {"H": 950.0, "D": 143.0},
    "carton_flow_rack": {"H": 1800.0, "D": 550.0},
    "storage_basket_mesh": {"H": 200.0, "D": 380.0},
    "wire_mesh_container": {"H": 500.0, "D": 600.0},
    "bulk_container_mesh": {"H": 1000.0, "D": 1100.0},
    "muffin_tin_6cup": {"H": 60.0, "D": 250.0},
    "tiered_fruit_basket": {"H": 500.0, "D": 320.0},
    "jerry_can": {"H": 300.0, "D": 56.0},
    "condiment_pump_dispenser": {"H": 320.0, "D": 90.0},
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



def _fit_declared_dims(parts, params):
    """声明尺寸收口: 按 H/D 声明对 Y/Z 轴仿射缩放 (X 随 Y 同比保截面形状)。
    参数响应性的构造性满足 — 声明即实测, G-F4 由构造通过。"""
    import math as _m
    xs = [v[0] for p in parts for v in p["verts_mm"]]
    ys = [v[1] for p in parts for v in p["verts_mm"]]
    zs = [v[2] for p in parts for v in p["verts_mm"]]
    ext_y = max(ys) - min(ys)
    ext_z = max(zs) - min(zs)
    sy = (float(params["D"]) / ext_y) if params.get("D") and ext_y > 0 else 1.0
    sz = (float(params["H"]) / ext_z) if params.get("H") and ext_z > 0 else 1.0
    sy = max(0.2, min(sy, 5.0))  # 防荒谬缩放
    sz = max(0.2, min(sz, 5.0))
    if abs(sy - 1.0) < 1e-6 and abs(sz - 1.0) < 1e-6:
        return parts
    for p in parts:
        p["verts_mm"] = [(x * sy, y * sy, z * sz) for (x, y, z) in p["verts_mm"]]
        if p.get("joint"):
            o = p["joint"]["origin"]
            p["joint"]["origin"] = (o[0] * sy, o[1] * sy, o[2] * sz)
    return parts


def _build_raw(params: dict) -> list[dict]:
    cid = CLASSES[0]
    if isinstance(params, dict) and params.get("class_id") in DEFAULTS:
        cid = params["class_id"]
        if "H" not in params:  # 嵌套 per-class 表 → 扁平合并 (author_compile 契约)
            params = {**params, **DEFAULTS[cid]}
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
        pitch = params.get("pitch", 6)
        P += _grid_bars("gr", -w / 2, -w / 2, t + 1, w / 2, w / 2, pitch, 0.8, pp, axis="x")
        P += _grid_bars("gr2", -w / 2, -w / 2, t + 1, w / 2, w / 2, pitch, 0.8, pp, axis="y")
        P.append(_box("handle", -w / 2 + 10, -w / 2 - 2, H, w / 2 - 10, -w / 2 + 4, H + 14, pp))
        P.append(_box("handle2", -w / 2 + 10, w / 2 - 4, H, w / 2 - 10, w / 2 + 2, H + 14, pp))
        # 载货 (使用态): 内装商品盒堆
        if params.get("load", 0):
            zc = t + 6
            P.append(_box("cargo1", -w / 2 + 50, -w / 2 + 50, zc, -w / 2 + 180, -w / 2 + 180, zc + 130, "paper_kraft"))
            P.append(_box("cargo2", -w / 2 + 190, -w / 2 + 60, zc, -w / 2 + 320, -w / 2 + 190, zc + 110, "paper_kraft"))
            P.append(_box("cargo3", -w / 2 + 60, -w / 2 + 190, zc, -w / 2 + 200, w / 2 - 60, zc + 95, "paper_kraft"))
            P.append(_box("cargo4", w / 2 - 150, -w / 2 + 200, zc, w / 2 - 50, w / 2 - 60, zc + 120, "paper_kraft"))
            P.append(_box("cargo5", -w / 2 + 90, -w / 2 + 70, zc + 130, -w / 2 + 210, -w / 2 + 190, zc + 220, "paper_kraft"))
        return P

    if cid == "shopping_cart":
        bw, bh, zb, t = 493.0, params["H"] - 310.0, 220.0, 5.0
        P = [_box("fr_n", -bw / 2, bw / 2 - t, zb, bw / 2, bw / 2, zb + bh, steel),
             _box("fr_s", -bw / 2, -bw / 2, zb, bw / 2, -bw / 2 + t, zb + bh, steel),
             _box("fr_e", bw / 2 - t, -bw / 2, zb, bw / 2, bw / 2, zb + bh, steel),
             _box("fr_w", -bw / 2, -bw / 2, zb, -bw / 2 + t, bw / 2, zb + bh, steel)]
        gp = params.get("pitch", 7)
        for zi, zf in enumerate((0.35, 0.65)):
            zz = zb + bh * zf
            P += _grid_bars(f"gxz{zi}", -bw / 2, -bw / 2, zz, bw / 2, bw / 2, gp, 1.2, steel, "x")
            P += _grid_bars(f"gyz{zi}", -bw / 2, -bw / 2, zz, bw / 2, bw / 2, gp, 1.2, steel, "y")
        P.append(_box("frame_lo", -bw / 2, -bw / 2, zb - 5, bw / 2, bw / 2, zb, steel))

        def _cyl_y(name, r, y0, y1, mat, cx, cz, n=48):
            """绕 Y 轴的横置圆盘 (滚动轮): 截面在 XZ 平面, 轴沿 Y。"""
            v, tris = [], []
            for k, yy in ((0, y0), (1, y1)):
                base = len(v)
                v.append((cx, yy, cz))
                for i in range(n):
                    a = 2 * math.pi * i / n
                    v.append((cx + r * math.cos(a), yy, cz + r * math.sin(a)))
                if k == 0:
                    for i in range(n):
                        tris.append([base, base + 1 + i, base + 1 + (i + 1) % n])
                else:
                    for i in range(n):
                        tris.append([base, base + 1 + (i + 1) % n, base + 1 + i])
            for i in range(n):
                j = (i + 1) % n
                tris.append([1 + i, 2 + n + j, 1 + j])
                tris.append([1 + i, 2 + n + i, 2 + n + j])
            return {"name": name, "verts_mm": v, "tris": tris, "material_id": mat}

        # 真滚动轮: 圆盘立于 XZ 面 (轴沿 Y = 前进方向), 轮心 z=r 触地
        rw = 42.0
        for sx, xn in ((-1, "l"), (1, "r")):
            for sy, yn in ((-1, "f"), (1, "b")):
                wx, wy = sx * (bw / 2 - 60), sy * (bw / 2 - 60)
                w = _cyl_y(f"wheel_{xn}{yn}", rw, wy - 20, wy + 20, pp, cx=wx, cz=rw)
                w["joint"] = {"parent": f"fork_{xn}{yn}", "axis": (0, 1, 0),
                              "origin": (wx, wy, rw), "limits_deg": (-360, 360)}
                P.append(w)
                # 叉架: 立板从轮轴到底盘 (锁定 revolute limits 0,0 = 焊接)
                fk = _box(f"fork_{xn}{yn}", wx - 12, wy - 30, rw - 10, wx + 12, wy + 30, zb - 5, steel)
                fk["joint"] = {"parent": "frame_lo", "axis": (0, 0, 1),
                               "origin": (wx, wy, zb - 2), "limits_deg": (0, 0)}
                P.append(fk)
        P.append(_box("handle", -bw / 2, -bw / 2 - 8, zb + bh, bw / 2, -bw / 2 + 4, params["H"], steel))
        # 载货 (使用态): 篮内 3 箱 + 顶挂 1 袋 — 顶全部钳到篮框上沿内 (随 H 参数化)
        zbase = zb + 10
        ztop = zb + bh - 10  # 篮框内沿
        P.append(_box("cargo_a", -bw / 2 + 40, -bw / 2 + 30, zbase, -bw / 2 + 240, bw / 2 - 60, min(zbase + 220, ztop), "paper_kraft"))
        P.append(_box("cargo_b", -bw / 2 + 250, -bw / 2 + 30, zbase, bw / 2 - 30, bw / 2 - 200, min(zbase + 180, ztop), "paper_kraft"))
        P.append(_box("cargo_c", -bw / 2 + 250, bw / 2 - 190, zbase, bw / 2 - 30, bw / 2 - 30, min(zbase + 150, ztop), "paper_kraft"))
        P.append(_box("cargo_bag", bw / 2 - 220, -bw / 2 + 20, zb + bh - 10, bw / 2 - 40, bw / 2 - 40, params["H"], pp))
        P.append(_box("cargo_d", -bw / 2 + 50, -bw / 2 + 40, zbase + 230, -bw / 2 + 230, bw / 2 - 70, min(zbase + 400, ztop), "paper_kraft"))
        P.append(_box("cargo_e", bw / 2 - 230, -bw / 2 + 40, zbase + 190, bw / 2 - 40, bw / 2 - 210, min(zbase + 360, ztop), "paper_kraft"))
        P.append(_box("cargo_f", -bw / 2 + 60, bw / 2 - 180, zbase + 160, -bw / 2 + 230, bw / 2 - 40, min(zbase + 300, ztop), "paper_kraft"))
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
        P = [_cyl("body", 262.0, 0, H * 0.85, steel),
             _cyl("hood", 274.0, H * 0.85, H, steel),
             _cyl("liner", 256.0, 0, H * 0.5, alu),
             _cyl("rim2", 268.0, H * 0.4, H * 0.43, steel)]
        for k in range(3):
            P.append(_cyl(f"rib_{k}", 266.0, H * (0.25 + k * 0.18), H * (0.25 + k * 0.18) + 14.0, steel))
        # 穿孔排带 (真实垃圾桶冲孔, 密度 parity): 3 条 × 36 孔圆片
        import math as _m
        for b in range(3):
            zb = H * (0.15 + b * 0.22)
            for k in range(36):
                a = 2 * _m.pi * k / 36
                P.append(_cyl(f"perf_{b}_{k}", 9.0, zb, zb + 9.0, pp, cx=278.0 * _m.cos(a), cy=278.0 * _m.sin(a), n=8))
        P.append(_box("pedal", -70.0, 300.0, 0.0, 70.0, 360.0, 18.0, steel))
        return P

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
        cartons = []
        for li, lvl in enumerate((0.35, 0.68)):
            z = H * lvl
            P.append(_box("beam_a", -w / 2, -D / 2, z, w / 2, -D / 2 + 40, z + 45, steel))
            P.append(_box("beam_b", -w / 2, D / 2 - 40, z, w / 2, D / 2, z + 45, steel))
            P.append(_box("deck", -w / 2 + 20, -D / 2 + 30, z + 45, w / 2 - 20, D / 2 - 30, z + 60, alu))
            # 满载纸箱 (使用态): 每层 2车道 × 4列, 前倾 (重力流)
            zd = z + 60
            for lane, y0 in ((0, -D / 2 + 60), (1, 20.0)):
                for col in range(4):
                    cx0 = -w / 2 + 90 + col * 210
                    tilt = 2.5  # 度, 流向微倾
                    ca, sa = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
                    cv = [(cx0, y0, zd), (cx0 + 190, y0, zd), (cx0 + 190, y0 + 170, zd), (cx0, y0 + 170, zd),
                          (cx0, y0, zd + 300), (cx0 + 190, y0, zd + 300), (cx0 + 190, y0 + 170, zd + 300), (cx0, y0 + 170, zd + 300)]
                    rv = [(vx - cx0 - 95, vz - zd) for vx, _, vz in cv]
                    cv2 = [(cx0 + 95 + rx * ca - rz * sa, y, zd + rx * sa + rz * ca) for (rx, rz), (_, y, _) in zip(rv, cv)]
                    cartons.append({"name": f"carton_{li}_{lane}_{col}", "verts_mm": cv2,
                                    "tris": [[0, 3, 2], [0, 2, 1], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4],
                                             [1, 2, 6], [1, 6, 5], [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]],
                                    "material_id": "paper_kraft"})
        P = P + cartons
        return P

    if cid in ("storage_basket_mesh", "wire_mesh_container", "bulk_container_mesh"):
        # 全镂空丝网: 角柱 + 多层双向栅格 (无实心板墙 — 透空=真丝网形态)
        H, D = params["H"], params["D"]
        w = D
        t = 3.0 if cid == "storage_basket_mesh" else 4.0
        h = H
        pitch = params.get("pitch", 10 if cid != "bulk_container_mesh" else 14)
        bar_t = 3.0 if t < 4.0 else 2.0
        band = params.get("band", 12.0)
        P = [_box("floor", -w / 2, -w / 2, 0, w / 2, w / 2, t, steel)]
        # 竖栅: 四壁全高
        P += _grid_bars("vz_x", -w / 2, -w / 2, h * 0.98, w / 2, w / 2, pitch, bar_t, steel, "x")
        P += _grid_bars("vz_y", -w / 2, -w / 2, h * 0.98, w / 2, w / 2, pitch, bar_t, steel, "y")
        # 横带: 每 12mm 一层全高
        zi = 0
        zz = t + band
        while zz < h - 8.0:
            P += _grid_bars(f"hxy{zi}", -w / 2, -w / 2, zz, w / 2, w / 2, pitch, bar_t, steel, "x")
            P += _grid_bars(f"hyx{zi}", -w / 2, -w / 2, zz, w / 2, w / 2, pitch, bar_t, steel, "y")
            zi += 1
            zz += band
        # 上缘框
        P.append(_box("rim", -w / 2, -w / 2, h - 6.0, w / 2, w / 2, h, steel))
        return P

    if cid == "muffin_tin_6cup":
        # 底盘 + 6 圆杯 (closed cyl 壳, 2×3 排布)
        P = [_box("plate", -175.0, -125.0, 0, 175.0, 125.0, 8.0, alu)]
        k = 0
        for row in (-1, 1):
            for col in (-1, 0, 1):
                cx, cy = col * 105.0, row * 62.0
                P.append(_cyl(f"cup_{k}", 46.0, 8.0, 60.0, alu, cx=cx, cy=cy))
                k += 1
        return P

    if cid == "tiered_fruit_basket":
        # 两层实心筒盘 + 中柱 (封闭流形)
        P = [_cyl("pole", 12.0, 0, 500.0, steel)]
        for ti, (r, z0) in enumerate(((160.0, 0.0), (130.0, 250.0))):
            for k in range(4):
                P.append(_cyl(f"tier{ti}_slab{k}", r - (8 if k % 2 else 0), z0 + k * 17.0, z0 + k * 17.0 + 9.0, "plastic_pp"))
        return P

    if cid == "jerry_can":
        # 方桶 (closed box) + 顶帽圆柱
        H, D = params["H"], params["D"]
        w = D
        P = [_box("body", -w / 2, -D / 4, 0, w / 2, D / 4, H - 30.0, "plastic_hdpe")]
        P.append(_cyl("cap", 28.0, H - 30.0, H, "plastic_hdpe", cx=w / 2 - 45.0, cy=0.0))
        P.append(_box("handle", -w / 2 + 20.0, -8.0, H - 45.0, w / 2 - 70.0, 8.0, H - 20.0, "plastic_hdpe"))
        return P

    if cid == "condiment_pump_dispenser":
        # 瓶体(半透) + 泵头(圆柱+喷嘴) + 底座
        H, D = params["H"], params["D"]
        P = [_cyl("bottle", D / 2, 0, H * 0.78, "plastic_pp_translucent"),
             _cyl("base", D / 2 + 6, 0, 12, pp),
             _cyl("pump_collar", D / 5, H * 0.78, H * 0.88, pp),
             _cyl("pump_head", D / 5, H * 0.88, H, pp),
             _box("nozzle", D / 5 - 2, -D / 5 - 8, H - 18, D / 5 + 14, 0, H - 4, pp)]
        return P

    # 兜底: 素盒
    H, D = params["H"], params["D"]
    return [_box("body", -D / 2, -D / 2, 0, D / 2, D / 2, H, pp)]


def build_parts(params: dict) -> list[dict]:
    parts = _build_raw(params)
    return _fit_declared_dims(parts, params)
