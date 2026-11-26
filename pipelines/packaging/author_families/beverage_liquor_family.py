# beverage_liquor_family.py
# Pack10K Author Contract v1 — 零售类目补全: 酒类/即饮 (通用几何, 零品牌)
#
# 铁律 (用户 2026-11-26 冻结):
# - 零品牌: 无商标/无文字/无标识/无水印, 素材质 + 通用形制
# - 对标 NVIDIA SimReady 交付结构: 每类 → USD + payloads + Textures + metadata (v2 接)
# - mm, Z-up, ground z=0; 每零件封闭流形; 一致外向绕序; 无退化极点三角
#
# 几何方法: 闭合轮廓回转体 (_lathe_closed) — profile 为 (r,z) 闭环,
# 环向闭合 + 闭环轮廓 → 亏格0闭曲面, 流形性由构造保证; 体积符号自动定向。
#
# 类目 (通用形制, 行业公称规格):
#   beer_bottle_330 / beer_bottle_500  长颈啤酒瓶 (皇冠盖)
#   beer_can_500                        铝罐 500mL (顶盖+拉环凸环)
#   baijiu_bottle_500                   白酒鼓腹短颈磨砂瓶 (旋盖)
#   wine_bottle_750                     波尔多直肩 (精版走 bottle_family.bottle_wine)
#   whisky_bottle_700 / vodka_bottle_700 洋酒瓶 (旋盖)
#   liquor_gift_dual                    双瓶位瓦楞礼盒 (素面)

import math

FAMILY = "beverage_liquor"

CLASSES = [
    "beer_bottle_330",
    "beer_bottle_500",
    "beer_can_500",
    "baijiu_bottle_500",
    "wine_bottle_750",
    "whisky_bottle_700",
    "vodka_bottle_700",
    "liquor_gift_dual",
]

DEFAULTS = {
    "beer_bottle_330":   {"H": 235.0, "D": 62.0},
    "beer_bottle_500":   {"H": 265.0, "D": 66.0},
    "beer_can_500":      {"H": 168.0, "D": 66.0},
    "baijiu_bottle_500": {"H": 245.0, "D": 78.0},
    "wine_bottle_750":   {"H": 300.0, "D": 76.0},
    "whisky_bottle_700": {"H": 240.0, "D": 88.0},
    "vodka_bottle_700":  {"H": 290.0, "D": 72.0},
    "liquor_gift_dual":  {"H": 340.0, "D": 200.0},
}

MAT_GLASS_CLEAR = "glass_clear"
MAT_GLASS_AMBER = "glass_amber"
MAT_GLASS_GREEN = "glass_green"
MAT_GLASS_FROST = "glass_frosted"
MAT_ALU = "metal_alu"
MAT_STEEL = "metal_steel"
MAT_CROWN = "metal_steel"
MAT_PAPER_KRAFT = "paper_kraft"


def _lathe_closed(name, loop, mat, n=96):
    """闭合轮廓回转体。loop: [(r,z)] 闭合 (首尾可不相接, 函数自动闭合)。
    流形由构造保证; 体积符号为负时自动翻转绕序 (保证外向法线)。"""
    pts = list(loop)
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    m = len(pts) - 1
    v = []
    for (r, z) in pts[:-1]:
        for i in range(n):
            a = 2 * math.pi * i / n
            v.append((r * math.cos(a), r * math.sin(a), z))
    tris = []
    for k in range(m):
        k2 = (k + 1) % m
        for i in range(n):
            j = (i + 1) % n
            a = k * n + i
            b = k * n + j
            c = k2 * n + j
            d = k2 * n + i
            tris.append([a, b, c])
            tris.append([a, c, d])
    # 体积符号定向 (外向法线 → 正体积)
    vol = 0.0
    for a, b, c in tris:
        ax, ay, az = v[a]
        bx, by, bz = v[b]
        cx, cy, cz = v[c]
        vol += (ax * (by * cz - bz * cy) - ay * (bx * cz - bz * cx) + az * (bx * cy - by * cx)) / 6.0
    if vol < 0:
        tris = [[a, c, b] for a, b, c in tris]
    return {"name": name, "verts_mm": v, "tris": tris, "material_id": mat}


def _annulus(name, r_in, r_out, z0, z1, mat, n=48):
    """闭合环形垫圈 (拉环占位/垫圈类)。"""
    loop = [
        (r_in, z0), (r_out, z0), (r_out, z1), (r_in, z1),
    ]
    return _lathe_closed(name, loop, mat, n=n)


def _shell_with_cap(name, outer, wall, mat, cap_profile=None, cap_mat=None, n=96):
    """玻璃闭壳: 外壁上行 → 口部 → 内壁下行 → 底 → 自动闭环。"""
    inner = [(max(r - wall, 1.0), z) for r, z in reversed(outer)]
    loop = list(outer) + inner
    P = [_lathe_closed(name, loop, mat, n=n)]
    if cap_profile:
        P.append(_lathe_closed("cap", cap_profile, cap_mat or MAT_STEEL, n=64))
    return P


def _beer_bottle(H, D, mat):
    """长颈啤酒瓶: 闭壳玻璃 + 皇冠盖。"""
    R = D / 2.0
    wall = 1.8
    lip_r = R * 0.52
    z_lip = H - 12.0
    outer = [
        (R * 0.82, 0.0), (R, 5.0), (R, H * 0.34), (R, H * 0.62),
        (R * 0.96, H * 0.66), (R * 0.78, H * 0.72),
        (lip_r + 1.8, H * 0.80), (lip_r + 1.8, z_lip),
        (lip_r, z_lip), (lip_r, z_lip - wall), (lip_r + 1.8, z_lip - wall),
    ]
    inner = [(max(r - wall, 1.0), z) for r, z in reversed(outer[1:-1])]
    loop = outer + inner + [outer[0]]
    P = [_lathe_closed("glass_shell", loop, mat, n=96)]
    cr = lip_r + 3.2
    cz = z_lip - wall
    crown = [
        (cr * 0.55, cz + 1.0), (cr * 0.92, cz + 1.5), (cr * 0.92, cz + 2.5),
        (cr, cz + 4.0), (cr, cz + 10.0), (cr * 0.97, cz + 11.5), (cr * 0.55, cz + 12.0),
    ]
    P.append(_lathe_closed("crown_cap", crown, MAT_CROWN, n=64))
    return P


def _baijiu_500(H, D):
    R = D / 2.0
    wall = 2.2
    belly = R * 1.06
    nr = R * 0.44
    outer = [
        (R * 0.78, 0.0), (R * 0.97, 7.0), (belly, H * 0.34), (belly * 0.99, H * 0.52),
        (R * 0.72, H * 0.72), (nr + wall, H * 0.84), (nr + wall, H - 12.0),
        (nr, H - 12.0), (nr, H - 12.0 - wall), (nr + wall, H - 12.0 - wall),
    ]
    inner = [(max(r - wall, 1.0), z) for r, z in reversed(outer[1:-1])]
    loop = outer + inner + [outer[0]]
    P = [_lathe_closed("glass_shell", loop, MAT_GLASS_FROST, n=96)]
    cr = nr + 2.5
    cz = H - 12.0 - wall
    cap = [
        (cr * 0.8, cz + 0.5), (cr, cz + 1.5), (cr, cz + 12.0), (cr * 0.88, cz + 14.0),
        (cr * 0.5, cz + 14.5),
    ]
    P.append(_lathe_closed("screw_cap", cap, MAT_STEEL, n=64))
    return P


def _whisky_700(H, D):
    R = D / 2.0
    wall = 2.4
    nr = R * 0.50
    outer = [
        (R * 0.85, 0.0), (R, 8.0), (R, H * 0.48), (R * 0.93, H * 0.58),
        (R * 0.62, H * 0.70), (nr + wall, H * 0.78), (nr + wall, H - 11.0),
        (nr, H - 11.0), (nr, H - 11.0 - wall), (nr + wall, H - 11.0 - wall),
    ]
    inner = [(max(r - wall, 1.0), z) for r, z in reversed(outer[1:-1])]
    loop = outer + inner + [outer[0]]
    P = [_lathe_closed("glass_shell", loop, MAT_GLASS_AMBER, n=96)]
    cr = nr + 2.8
    cz = H - 11.0 - wall
    cap = [
        (cr * 0.8, cz + 0.5), (cr, cz + 1.5), (cr, cz + 10.0), (cr * 0.9, cz + 12.5),
        (cr * 0.5, cz + 13.0),
    ]
    P.append(_lathe_closed("screw_cap", cap, MAT_STEEL, n=64))
    return P


def _vodka_700(H, D):
    R = D / 2.0
    wall = 2.2
    nr = R * 0.46
    outer = [
        (R * 0.82, 0.0), (R, 7.0), (R, H * 0.56), (R * 0.80, H * 0.66),
        (nr + wall, H * 0.74), (nr + wall, H - 10.0),
        (nr, H - 10.0), (nr, H - 10.0 - wall), (nr + wall, H - 10.0 - wall),
    ]
    inner = [(max(r - wall, 1.0), z) for r, z in reversed(outer[1:-1])]
    loop = outer + inner + [outer[0]]
    P = [_lathe_closed("glass_shell", loop, MAT_GLASS_CLEAR, n=96)]
    cr = nr + 2.5
    cz = H - 10.0 - wall
    cap = [
        (cr * 0.8, cz + 0.5), (cr, cz + 1.5), (cr, cz + 9.0), (cr * 0.9, cz + 11.0),
        (cr * 0.5, cz + 11.5),
    ]
    P.append(_lathe_closed("screw_cap", cap, MAT_STEEL, n=64))
    return P


def _beer_can_500(H, D):
    R = D / 2.0
    wall = 0.25
    dome = 5.0
    z_rim = H - 2.0
    outer = [
        (R * 0.86, 0.0), (R, dome), (R, z_rim - 2.0), (R * 0.965, z_rim),
        (R * 0.965, H - 0.8), (R * 0.62, H - 0.8),
        (R * 0.62, H - 1.6), (R * 0.965, H - 1.6), (R * 0.965 - wall, z_rim),
        (R * 0.965 - wall, H - 2.2),
    ]
    inner = [(max(r - wall, 0.5), max(z - 0.5, 0.3)) for r, z in reversed(outer[1:-1])]
    loop = outer + inner + [outer[0]]
    P = [_lathe_closed("can_shell", loop, MAT_ALU, n=96)]
    # 顶盖 (下凹盘, 闭合)
    lid = [
        (R * 0.30, H - 2.6), (R * 0.86, H - 2.6), (R * 0.93, H - 2.0),
        (R * 0.93, H - 1.2), (R * 0.86, H - 1.8), (R * 0.30, H - 1.8),
    ]
    P.append(_lathe_closed("lid", lid, MAT_ALU, n=64))
    # 拉环 (环形凸起占位)
    P.append(_annulus("pull_tab", R * 0.06, R * 0.30, H - 2.4, H - 2.0, MAT_ALU, n=32))
    return P


def _gift_dual(H, D):
    """双瓶位瓦楞礼盒: 底+四壁 (每零件独立闭合箱体)。素面零印刷。"""
    W = D
    t = 3.0

    def _box6(name, x0, y0, z0, x1, y1, z1):
        v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        q = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        tris = []
        for a, b, c, d in q:
            tris.append([a, b, c])
            tris.append([a, c, d])
        return {"name": name, "verts_mm": v, "tris": tris, "material_id": MAT_PAPER_KRAFT}

    P = [_box6("floor", -W / 2, -W / 2, 0, W / 2, W / 2, t),
         _box6("wall_w", -W / 2, -W / 2, 0, -W / 2 + t, W / 2, H),
         _box6("wall_e", W / 2 - t, -W / 2, 0, W / 2, W / 2, H),
         _box6("wall_s", -W / 2, -W / 2, 0, W / 2, -W / 2 + t, H),
         _box6("wall_n", -W / 2, W / 2 - t, 0, W / 2, W / 2, H)]
    return P


def build_parts(params: dict) -> list[dict]:
    cid = CLASSES[0]
    if isinstance(params, dict) and params.get("class_id") in DEFAULTS:
        cid = params["class_id"]
    D0 = DEFAULTS[cid]
    H, D = D0["H"], D0["D"]
    if cid == "beer_bottle_330":
        return _beer_bottle(H, D, MAT_GLASS_GREEN)
    if cid == "beer_bottle_500":
        return _beer_bottle(H, D, MAT_GLASS_AMBER)
    if cid == "beer_can_500":
        return _beer_can_500(H, D)
    if cid == "baijiu_bottle_500":
        return _baijiu_500(H, D)
    if cid == "wine_bottle_750":
        return _beer_bottle(H, D, MAT_GLASS_CLEAR)
    if cid == "whisky_bottle_700":
        return _whisky_700(H, D)
    if cid == "vodka_bottle_700":
        return _vodka_700(H, D)
    if cid == "liquor_gift_dual":
        return _gift_dual(H, D)
    raise ValueError(cid)
