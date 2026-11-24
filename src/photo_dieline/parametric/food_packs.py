"""food_packs: 食品包装七类 (第五波动物园).

类ID:
  food_clamshell_burger  铰链汉堡盒: 星形底盘 + 4 矮墙 + 连体拱盖 (k 段折线近似弧拱,
                         参照 pillow_box 弧近似) 绕背墙顶缘铰链前扣, 远缘抵前墙顶缘
                         (拱升高 ra, 弦片逐段 tdir = 参考圆弧弦向)
  food_noodle_pail       外卖粉盒: 八棱台全锥扇形链 (梯形墙, odd_family 恢复锥同款)
                         + 收顶 8 梯形片 (刚体展开 congruence 反折成小八边开口, gd 深)
                         + 双翼对折盖 (对位两翼远缘中线互抵于开口中心)
                         + 顶缘 U 形提线缺口 (w0/w4 顶缘 U 凹口替代金属提线)
  food_fries_sleeve      薯条套: 前矮后高斜套筒 (前墙 Hf / 后墙 Hb / 侧墙梯形)
                         + 后缘内折唇 (水平内折 lip_d) + 粘口缝 (贴前墙)
  food_bento_lid_box     便当双层: 底盒 (4 墙星形) + 浅盘式盖 (铰链于背墙顶缘前扣,
                         盖盘 = 底盒 + clearance 2c, 3 矮墙外包缘包口)
                         双唇: 外唇 (深 c) 远缘抵盖盘前缘, 内唇 (深 c) 贴前墙外面
  food_wrap_pocket       卷饼纸袋: 侧折纸袋式 (前板 + 两侧内折梯形翼 + 高背后板,
                         环闭远缘缝) + 顶斜封盖 (深 = sqrt(gs^2+hb^2), 深角精确抵
                         前板顶角, 远缘斜切 sd)
  food_sushi_tray        寿司托: 长圆角托 (切角八边形近似) + 分离式透明盖 (缘包口
                         浅盘: 盘底 = 托底外偏置 c 的八边形, web 工艺条续链,
                         two_piece 分离拓扑, 世界系盖倒扣悬置)
  food_tray_liner        托盘内衬: 六角浅盘 (tray_6corner 同款角片 + 粘口) + 防尘
                         翻缘 (6 片沿棱折链内折, 对角平分斜缘拼接成环, 角点互抵)

几何约定: 星形网根面板 net(x,y)->world(x,y,0) (_R_STAR); 链式网 _R_CHAIN;
粉盒扇形链根框架三元组对齐数值求解 (odd_family 同款)。closure 全部为折叠后
世界坐标跨链残差 (远缘重合/抵缘/落平面/配合展向差), 无构造恒等量。
负探针 probe(): 每类扰动 2 条关键折线 (绕真实世界铰链轴 Rodrigues 转开 tdir)。
"""
from __future__ import annotations

import copy
import math

import numpy as np

from . import base as _base

PARAM_ORDER = ["kind", "W", "D", "H", "ra", "k",
               "side_b", "side_t", "h", "s_p", "gd", "nw", "nd",
               "Hf", "Hb", "lip_d",
               "Hl", "c",
               "hb", "gs", "sd",
               "ch", "web_w",
               "side", "hem_d",
               "glue_w", "board_t"]

DEFAULTS = {k: 0.0 for k in PARAM_ORDER}
DEFAULTS.update({"k": 6.0, "board_t": 0.45})

_CLS = ("food_clamshell_burger", "food_noodle_pail", "food_fries_sleeve",
        "food_bento_lid_box", "food_wrap_pocket", "food_sushi_tray",
        "food_tray_liner")
_KIND = {c: i for i, c in enumerate(_CLS)}

for _cid in _CLS:
    _base.register(_cid, "food_packs")

_R_CHAIN = [[1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0]]  # net(x,y)->world(x,0,y)
_R_STAR = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]   # net(x,y)->world(x,y,0)


# ---------------------------------------------------------------- helpers
def _rect(pid, role, xa, ya, xb, yb):
    """矩形板 CCW: [左下,右下,右上,左上] (顶点索引契约见 closure_checks)."""
    return {"id": pid, "role": role,
            "polygon_2d": [[float(xa), float(ya)], [float(xb), float(ya)],
                           [float(xb), float(yb)], [float(xa), float(yb)]]}


def _poly(pid, role, pts):
    return {"id": pid, "role": role,
            "polygon_2d": [[float(x), float(y)] for x, y in pts]}


def _fold(eid, a2, b2, parent, child, tdir, mt="VALLEY"):
    return {"id": eid, "kind": "FOLD",
            "seg_2d": [[float(a2[0]), float(a2[1])], [float(b2[0]), float(b2[1])]],
            "fold": {"mt_va": mt, "parent": parent, "child": child,
                     "target_dir_3d": [round(float(v), 9) for v in tdir]}}


def _features(*glue_panels):
    fs = [{"id": f"f_g{i}", "kind": "GLUE_TAB", "panel_id": g}
          for i, g in enumerate(glue_panels)]
    fs += [{"id": "f_bleed", "kind": "BLEED", "offset_mm": 3.0},
           {"id": "f_check", "kind": "CHECK_BAR", "length_mm": 50.0},
           {"id": "f_reg", "kind": "REGISTRATION"}]
    return fs


def _unit(v):
    v = np.asarray(v, float)
    return v / float(np.linalg.norm(v))


def _d(a, b) -> float:
    return float(np.linalg.norm(np.asarray(a, float) - np.asarray(b, float)))


def _fm(world, pid, i, j):
    return (np.asarray(world[pid][i], float) + np.asarray(world[pid][j], float)) / 2.0


def _hex_geom(side):
    """正六边形 (edge0 落 y=0, x in [0,side], 中心 (side/2, apothem) 上方)."""
    n = 6
    R = side / (2.0 * math.sin(math.pi / n))
    a = side / (2.0 * math.tan(math.pi / n))
    ctr = np.array([side / 2.0, a])
    vs = [ctr + R * np.array([math.cos(-math.pi / 2 - math.pi / n + 2.0 * math.pi * k / n),
                              math.sin(-math.pi / 2 - math.pi / n + 2.0 * math.pi * k / n)])
          for k in range(n)]
    outward, tangent = [], []
    for k in range(n):
        em = (np.asarray(vs[k], float) + np.asarray(vs[(k + 1) % n], float)) / 2.0
        o = _unit(em - ctr)
        outward.append(o)
        tangent.append(np.array([-o[1], o[0]]))
    return [np.asarray(v, float) for v in vs], outward, tangent, a


def _offset_poly(vs, c):
    """凸多边形外偏置 c (逐边外移后相邻偏置线求交; CCW 保持)."""
    n = len(vs)
    ns, ds = [], []
    for i in range(n):
        t = _unit(np.asarray(vs[(i + 1) % n], float) - np.asarray(vs[i], float))
        nrm = np.array([t[1], -t[0]])
        ns.append(nrm)
        ds.append(float(nrm @ np.asarray(vs[i], float)) + c)
    out = []
    for i in range(n):
        n1, d1 = ns[(i - 1) % n], ds[(i - 1) % n]
        n2, d2 = ns[i], ds[i]
        A = np.array([[n1[0], n1[1]], [n2[0], n2[1]]])
        q = np.linalg.solve(A, np.array([d1, d2]))
        out.append(q)
    return out


# ---------------------------------------------------------- ① food_clamshell_burger
def _arch_refs(D, H, ra, k):
    """弧拱参考: 过 (D,H)/(0,H) 顶点、顶点在 (D/2, H+ra) 的圆弧, k 等弦分段.
    返回 (chord 深度列表, 世界弦向 tdir 列表, 顶点序列 P_j (y,z))."""
    s = ((D / 2.0) ** 2 - ra ** 2) / (2.0 * ra)      # 圆心低于弦口距离
    R0 = s + ra
    zc = H - s
    th0 = math.atan2(s, D / 2.0)
    sweep = math.pi - 2.0 * th0
    pts = []
    for j in range(k + 1):
        th = th0 + j * sweep / k
        pts.append(np.array([D / 2.0 + R0 * math.cos(th), zc + R0 * math.sin(th)]))
    chords, tdirs = [], []
    for j in range(k):
        dv = pts[j + 1] - pts[j]
        chords.append(float(np.linalg.norm(dv)))
        tdirs.append((0.0, float(dv[0] / chords[j]), float(dv[1] / chords[j])))
    return chords, tdirs, pts


def _build_clamshell(p):
    W, D, H, ra = float(p["W"]), float(p["D"]), float(p["H"]), float(p["ra"])
    k = int(p["k"])
    chords, tdirs, pts = _arch_refs(D, H, ra, k)

    panels = [
        _rect("base", "wall", 0.0, 0.0, W, D),
        _rect("wF", "wall", 0.0, -H, W, 0.0),
        _rect("wR", "wall", W, 0.0, W + H, D),
        _rect("wB", "wall", 0.0, D, W, D + H),
        _rect("wL", "wall", -H, 0.0, 0.0, D),
    ]
    edges = [
        _fold("e_wF", (0, 0), (W, 0), "base", "wF", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_wR", (W, 0), (W, D), "base", "wR", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_wB", (0, D), (W, D), "base", "wB", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_wL", (0, 0), (0, D), "base", "wL", (0.0, 0.0, 1.0), "MOUNTAIN"),
    ]
    # 拱盖弦片链: s1 铰链于 wB 顶缘 (世界 (y=D,z=H)), 逐段弦向 tdir 前扣
    y = D + H
    for j in range(k):
        pid = f"s{j + 1}"
        panels.append(_rect(pid, "slope", 0.0, y, W, y + chords[j]))
        parent = "wB" if j == 0 else f"s{j}"
        edges.append(_fold(f"e_s{j + 1}", (0, y), (W, y), parent, pid,
                           tdirs[j], "MOUNTAIN"))
        y += chords[j]
    notes = (f"clamshell_burger: 铰链汉堡盒 (单件连体拓扑) — 星形底盘 {W:g}x{D:g} + "
             f"4 矮墙 {H:g} + 连体拱盖 {k} 段折线近似弧拱 (拱升高 {ra:g}, 圆弧半径 "
             f"{(ra + ((D / 2.0) ** 2 - ra ** 2) / (2.0 * ra)):.2f}, 每段弦向 tdir = "
             "参考弧弦向, pillow_box 弧近似同款) 绕背墙顶缘铰链前扣, 末段远缘精确抵"
             "前墙顶缘 (y=0,z=H)")
    return panels, edges, notes, _features()


def _c_clamshell(ir, world):
    W, D, H, ra = (float(ir.param("W")), float(ir.param("D")),
                   float(ir.param("H")), float(ir.param("ra")))
    k = int(ir.param("k"))
    chords, tdirs, pts = _arch_refs(D, H, ra, k)
    f, r, b, l = world["wF"], world["wR"], world["wB"], world["wL"]
    res: dict[str, float] = {}
    res["corner.fr"] = float(max(_d(f[1], r[1]), _d(f[2], r[0])))
    res["corner.rb"] = float(max(_d(r[2], b[2]), _d(r[3], b[1])))
    res["corner.bl"] = float(max(_d(b[3], l[3]), _d(b[0], l[2])))
    res["corner.lf"] = float(max(_d(l[0], f[0]), _d(l[1], f[3])))
    # 拱盖落位: s1 远缘中点 ↔ 参考弧 P1; 拱顶折线中点 ↔ (W/2, D/2, H+ra);
    # 末段远缘中点 ↔ 前墙顶缘中点 (跨链扣合)
    res["s1.seat"] = _d(_fm(world, "s1", 2, 3),
                        (W / 2.0, float(pts[1][0]), float(pts[1][1])))
    res["apex.seat"] = _d(_fm(world, f"s{k // 2}", 2, 3), (W / 2.0, D / 2.0, H + ra))
    res["lid.front"] = _d(_fm(world, f"s{k}", 2, 3), (W / 2.0, 0.0, H))
    return res


# ---------------------------------------------------------- ② food_noodle_pail
_PN = 8                                        # 八棱台边数


def _pail_geom(sb, st, hh):
    """恢复全锥扇形参数 (odd_family _frustum_geom 同款, n=8)."""
    n = _PN
    a_b = sb / (2.0 * math.tan(math.pi / n))
    a_t = st / (2.0 * math.tan(math.pi / n))
    Rb = sb / (2.0 * math.sin(math.pi / n))
    Rt = st / (2.0 * math.sin(math.pi / n))
    if a_b - a_t <= 1e-9:
        raise ValueError("粉盒须 side_b > side_t (八棱台锥度)")
    H_p = hh * a_b / (a_b - a_t)
    lb = math.hypot(H_p, Rb)
    Le = math.hypot(hh, Rb - Rt)
    lt = lb - Le
    beta = 2.0 * math.asin(sb / (2.0 * lb))
    return {"a_b": a_b, "a_t": a_t, "Rb": Rb, "Rt": Rt, "H_p": H_p,
            "lb": lb, "lt": lt, "Le": Le, "beta": beta}


def _pail_refs(sb, st, hh):
    """世界参考环: 底/顶八边形顶点 (底 z=0, 顶 z=hh, 轴上中心)."""
    n = _PN
    g = _pail_geom(sb, st, hh)
    omega = lambda k: -math.pi / 2 - math.pi / n + 2.0 * math.pi * k / n
    vb = [np.array([g["Rb"] * math.cos(omega(k)), g["Rb"] * math.sin(omega(k)), 0.0])
          for k in range(n)]
    vt = [np.array([g["Rt"] * math.cos(omega(k)), g["Rt"] * math.sin(omega(k)), float(hh)])
          for k in range(n)]
    return g, vb, vt, np.array([0.0, 0.0, g["H_p"]])


def _fan_root(vb0, vb1, vt0, apex, u0, u1):
    """扇形根框架: net 射线基 -> 墙0 面内锥顶射线基 三元组对齐 (odd_family 同款)."""
    dL = _unit(vb0 - apex)
    dR = _unit(vb1 - apex)
    u03 = np.array([float(u0[0]), float(u0[1]), 0.0])
    u13 = np.array([float(u1[0]), float(u1[1]), 0.0])
    U = np.column_stack([u03, u13, np.cross(u03, u13)])
    Dm = np.column_stack([dL, dR, np.cross(dL, dR)])
    R0 = Dm @ np.linalg.inv(U)
    return R0, np.asarray(apex, float)


def _pail_notch_poly(Bk, Bk1, Tk, Tk1, u_out, nw, nd, side_t):
    """带顶缘 U 形缺口墙多边形: [B_k,B_k+1,T_k+1,foot_r,dip_r,dip_l,foot_l,T_k]."""
    chord = Tk1 - Tk
    s_r = 0.5 + nw / (2.0 * side_t)
    s_l = 0.5 - nw / (2.0 * side_t)
    foot_r = Tk + s_r * chord
    foot_l = Tk + s_l * chord
    dip_r = foot_r + nd * u_out
    dip_l = foot_l + nd * u_out
    return [Bk, Bk1, Tk1, foot_r, dip_r, dip_l, foot_l, Tk], (foot_r, foot_l)


def _build_pail(p):
    n = _PN
    sb, st, hh = float(p["side_b"]), float(p["side_t"]), float(p["h"])
    s_p, gd = float(p["s_p"]), float(p["gd"])
    nw, nd, gw = float(p["nw"]), float(p["nd"]), float(p["glue_w"])
    g, vb, vt, apex = _pail_refs(sb, st, hh)
    beta, lb, lt = g["beta"], g["lb"], g["lt"]
    phi = lambda k: -math.pi / 2 - beta / 2.0 + k * beta
    u = lambda k: np.array([math.cos(phi(k)), math.sin(phi(k))])
    B = [lb * u(k) for k in range(n + 1)]
    T = [lt * u(k) for k in range(n + 1)]
    u_mid = lambda k: u(k + 0.5)

    # --- 收顶小八边环 (z=h-gd, 边长 s_p, 与顶环同取向)
    R_p = s_p / (2.0 * math.sin(math.pi / n))
    omega = lambda k: -math.pi / 2 - math.pi / n + 2.0 * math.pi * k / n
    vs = [np.array([R_p * math.cos(omega(k)), R_p * math.sin(omega(k)), hh - gd])
          for k in range(n)]

    panels, edges = [], []
    for k in range(n):
        if k in (0, n // 2):                   # w0/w4 顶缘带 U 形提线缺口
            verts, _ = _pail_notch_poly(B[k], B[k + 1], T[k], T[k + 1],
                                        u_mid(k), nw, nd, st)
            panels.append(_poly(f"w{k}", "wall", verts))
        else:
            panels.append(_poly(f"w{k}", "wall", [B[k], B[k + 1], T[k + 1], T[k]]))
    # 墙链: 铰链 = 侧棱, tdir = 邻墙面内指向面质心 (odd_family 同款);
    # e_w3 子面板 w4 带 U 形缺口 → 质心偏移使引擎 away 倾斜, 需按三点对齐真框架
    # 计算 tgt_true = R4_true @ away_net (仅此边, 其余子面板为对称素四边形)
    Um = np.eye(3)
    Um[:, 0] = np.array([*(B[5] - B[4]), 0.0])
    Um[:, 1] = np.array([*(T[4] - B[4]), 0.0])
    Um[:, 2] = np.cross(Um[:, 0], Um[:, 1])
    Dm = np.eye(3)
    Dm[:, 0] = vb[5] - vb[4]
    Dm[:, 1] = vt[4] - vb[4]
    Dm[:, 2] = np.cross(Dm[:, 0], Dm[:, 1])
    R4t = Dm @ np.linalg.inv(Um)
    for k in range(n - 1):
        i1, i2 = (k + 1) % n, (k + 2) % n
        cen = (vb[i1] + vb[i2] + vt[i2] + vt[i1]) / 4.0
        axis = _unit(vb[i1] - vt[i1])
        r = cen - (vb[i1] + vt[i1]) / 2.0
        tdir = _unit(r - float(r @ axis) * axis)
        if k == 3:      # 子面板 w4 带缺口: away 倾斜补偿 (真框架映 away)
            poly4 = np.asarray(panels[4]["polygon_2d"], float)
            a_seg, b_seg = np.asarray(T[4], float), np.asarray(B[4], float)
            cen4 = poly4.mean(axis=0)
            ab = b_seg - a_seg
            tt = float(np.dot(cen4 - a_seg, ab)) / float(np.dot(ab, ab))
            away3 = np.array([*(cen4 - (a_seg + tt * ab)), 0.0])
            tdir = _unit(R4t @ away3)
        edges.append(_fold(f"e_w{k}", T[k + 1], B[k + 1], f"w{k}", f"w{k+1}",
                           tdir, "VALLEY"))

    # --- 收顶梯形片 tf_k: 刚体展开 congruence (铰链=顶弦; 远弦落小八边环 vs)
    # 注意: 各片远弦网位独立 (每片自己的展开坐标), 不能共用字典键
    F_far = {}
    for k in range(n):
        c3 = _unit(vt[(k + 1) % n] - vt[k])           # 顶弦世界向 (= 铰链轴向)
        a_k = float(np.dot(vs[k] - vt[k], c3))        # 沿轴分量 (旋转不变)
        w = vs[k] - vt[k]
        d_f = float(np.linalg.norm(w - float(np.dot(w, c3)) * c3))  # 到铰线距离
        c2 = _unit(T[k + 1] - T[k])                   # 网弦向
        uo = u_mid(k)                                 # 网径向 (锥顶->外)
        # 净图放置: 墙体占据顶弦外侧 (扇形 lt→lb), tf 必须内放 (朝锥顶) 否则 G03 自压
        # (同款修: fan_net_ext.py line 142 / odd_family.py line 139, 2026-11-25)
        Fk0 = T[k] + a_k * c2 - d_f * uo
        Fk1 = T[k + 1] + (float(np.dot(vs[(k + 1) % n] - vt[(k + 1) % n],
                                              c3)) * c2 - d_f * uo)
        F_far[k] = (Fk0, Fk1)
        panels.append(_poly(f"tf{k}", "slope", [T[k], T[k + 1], Fk1, Fk0]))
        hm3 = (vt[k] + vt[(k + 1) % n]) / 2.0
        fm3 = (vs[k] + vs[(k + 1) % n]) / 2.0
        edges.append(_fold(f"e_tf{k}", T[k], T[k + 1], f"w{k}", f"tf{k}",
                           _unit(fm3 - hm3), "MOUNTAIN"))

    # --- 双翼对折盖 wg0/wg4: 铰链 = tf 远弦, 远缘 = 过开口中心的平行弦 (中线互抵)
    ctr3 = np.array([0.0, 0.0, hh - gd])
    wg_ids = (0, n // 2)
    for k in wg_ids:
        c3 = _unit(vt[k + 1] - vt[k])
        far3 = [ctr3 - (s_p / 2.0) * c3, ctr3 + (s_p / 2.0) * c3]  # [k 端, k+1 端]
        c2 = _unit(T[k + 1] - T[k])
        uo = u_mid(k)
        Wn = {}
        for j, vj in ((k, vs[k]), (k + 1, vs[k + 1])):
            fj = far3[0] if j == k else far3[1]
            wj = fj - vj
            aj = float(np.dot(wj, c3))
            dj = float(np.linalg.norm(wj - aj * c3))
            base = F_far[k][0] if j == k else F_far[k][1]
            Wn[j] = base + aj * c2 - dj * uo           # 随 tf 内放, 翼体续向锥顶侧
        panels.append(_poly(f"wg{k}", "flap",
                            [F_far[k][0], F_far[k][1], Wn[k + 1], Wn[k]]))
        vsm = (vs[k] + vs[k + 1]) / 2.0
        edges.append(_fold(f"e_wg{k}", F_far[k][0], F_far[k][1], f"tf{k}", f"wg{k}",
                           _unit(ctr3 - vsm), "MOUNTAIN"))

    # --- 粘口: 附 w7 自由侧棱, 180° 反贴 w0 内面 (cone_wrap 同款)
    q = np.array([-math.sin(phi(n)), math.cos(phi(n))])
    panels.append(_poly("glue", "glue",
                        [T[n], B[n], B[n] + gw * q, T[n] + gw * q]))
    axis0 = vb[0] - vt[0]
    in_w0 = (vb[0] + vb[1] + vt[1] + vt[0]) / 4.0 - (vb[0] + vt[0]) / 2.0
    in_w0 = in_w0 - float(np.dot(in_w0, axis0) / float(np.dot(axis0, axis0))) * axis0
    edges.append(_fold("e_glue", T[n], B[n], f"w{n-1}", "glue", _unit(in_w0),
                       "MOUNTAIN"))

    R0, off0 = _fan_root(vb[0], vb[1], vt[0], apex, u(0), u(1))
    notes = (f"noodle_pail: 外卖粉盒 (单件连体拓扑) — 八棱台扇形墙链 (墙面顶角 "
             f"{math.degrees(beta):.2f}, 底 {sb:g}/顶 {st:g}, 高 {hh:g}) + 收顶 8 梯形片 "
             f"(刚体展开 congruence 反折, 开口边长 {s_p:g} @ z={hh - gd:g}, 收顶深 {gd:g}) "
             f"+ 双翼对折盖 (对位翼远缘中线互抵开口中心) + 顶缘 U 形提线缺口 "
             f"{nw:g}x{nd:g} (w0/w4, 替代金属提线) + 搭接粘口贴 w0")
    return panels, edges, notes, R0, off0, vb, vt, vs


def _c_pail(ir, world):
    n = _PN
    sb, st, hh = (float(ir.param("side_b")), float(ir.param("side_t")),
                  float(ir.param("h")))
    s_p, gd, nd = (float(ir.param("s_p")), float(ir.param("gd")),
                   float(ir.param("nd")))
    gw = float(ir.param("glue_w"))
    _, vb, vt, _ = _pail_refs(sb, st, hh)
    R_p = s_p / (2.0 * math.sin(math.pi / n))
    omega = lambda k: -math.pi / 2 - math.pi / n + 2.0 * math.pi * k / n
    vs = [np.array([R_p * math.cos(omega(k)), R_p * math.sin(omega(k)), hh - gd])
          for k in range(n)]
    ctr3 = np.array([0.0, 0.0, hh - gd])
    res: dict[str, float] = {}
    # 环闭合缝: 末墙自由侧棱 ↔ 首墙左棱 (跨链)
    wn = world[f"w{n-1}"]
    res["seam.far_edge"] = float(max(_d(wn[1], vb[0]), _d(wn[2], vt[0])))
    # 收顶片远弦中点 ↔ 小八边弦中点 (逐片, 折角落位)
    for k in range(n):
        tgt = (vs[k] + vs[(k + 1) % n]) / 2.0
        res[f"tf{k}.rim"] = _d(_fm(world, f"tf{k}", 2, 3), tgt)
    # 双翼对折: 两翼远缘中线均落开口中心 + 平面 z=h-gd
    for k in (0, n // 2):
        res[f"wg{k}.axis"] = _d(_fm(world, f"wg{k}", 2, 3), ctr3)
    res["wg.planar"] = float(max(abs(float(v[2]) - (hh - gd))
                                 for k in (0, n // 2) for v in world[f"wg{k}"]))
    # U 形缺口底中点: 世界位 = 顶弦中点 + nd·(墙面下滑向)
    for k in (0, n // 2):
        vm = (vt[k] + vt[k + 1]) / 2.0
        bm = (vb[k] + vb[k + 1]) / 2.0
        tgt = vm + nd * _unit(bm - vm)
        res[f"w{k}.notch"] = _d((world[f"w{k}"][4] + world[f"w{k}"][5]) / 2.0, tgt)
    # 粘口贴合: 落 w0 平面 (全部顶点到平面距离)
    nrm = np.cross(vb[1] - vb[0], vt[0] - vb[0])
    nrm = _unit(nrm if float(np.dot(nrm, (vb[0] + vt[0]) / 2.0)) > 0 else -nrm)
    gv = np.asarray(world["glue"], float)
    res["glue.seat"] = float(np.max(np.abs((gv - vb[0]) @ nrm)))
    # 粘口远缘中点到铰线 (w0 左棱直线) 距离 ≈ gw (反贴宽度落位)
    a0, b0 = vt[0], vb[0]
    fmid = (gv[2] + gv[3]) / 2.0
    ab = b0 - a0
    res["glue.width"] = abs(float(np.linalg.norm(
        fmid - a0 - float(np.dot(fmid - a0, ab)) / float(np.dot(ab, ab)) * ab)) - gw)
    return res


# ---------------------------------------------------------- ③ food_fries_sleeve
def _build_fries(p):
    W, D = float(p["W"]), float(p["D"])
    Hf, Hb, lp, gw = (float(p["Hf"]), float(p["Hb"]), float(p["lip_d"]),
                      float(p["glue_w"]))
    panels = [
        _rect("floor", "wall", 0.0, 0.0, W, D),
        _rect("wF", "wall", 0.0, -Hf, W, 0.0),
        _poly("wR", "wall", [(W, 0), (W + Hf, 0), (W + Hb, D), (W, D)]),
        _rect("wB", "wall", 0.0, D, W, D + Hb),
        _poly("wL", "wall", [(-Hf, 0), (0, 0), (0, D), (-Hb, D)]),
        _rect("lip", "flap", 0.0, D + Hb, W, D + Hb + lp),
        _rect("glue", "glue", -Hf, -gw, 0.0, 0.0),
    ]
    edges = [
        _fold("e_wF", (0, 0), (W, 0), "floor", "wF", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_wR", (W, 0), (W, D), "floor", "wR", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_wB", (0, D), (W, D), "floor", "wB", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_wL", (0, 0), (0, D), "floor", "wL", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_lip", (0, D + Hb), (W, D + Hb), "wB", "lip", (0.0, -1.0, 0.0),
              "MOUNTAIN"),
        _fold("e_glue", (-Hf, 0), (0, 0), "wL", "glue", (1.0, 0.0, 0.0), "MOUNTAIN"),
    ]
    notes = (f"fries_sleeve: 薯条套 (单件连体拓扑) — 斜套筒: 底板 {W:g}x{D:g} + 前墙 "
             f"{Hf:g} / 后墙 {Hb:g} / 侧墙梯形 (前 Hf 后 Hb 斜顶缘) + 后缘内折唇 "
             f"(深 {lp:g}, z=Hb 水平内折) + 粘口缝 (wL 前棱贴 wF, tray_wedge 同款)")
    return panels, edges, notes, _features("glue")


def _c_fries(ir, world):
    D, Hb, lp = (float(ir.param("D")), float(ir.param("Hb")),
                 float(ir.param("lip_d")))
    f, r, b, l = world["wF"], world["wR"], world["wB"], world["wL"]
    res: dict[str, float] = {}
    res["corner.fr"] = float(max(_d(f[1], r[1]), _d(f[2], r[0])))
    res["corner.rb"] = float(max(_d(r[2], b[2]), _d(r[3], b[1])))
    res["corner.bl"] = float(max(_d(b[3], l[3]), _d(b[0], l[2])))
    res["corner.lf"] = float(max(_d(l[0], f[0]), _d(l[1], f[3])))
    res["glue.planar"] = float(np.max(np.abs(np.asarray(world["glue"], float)[:, 1])))
    # 内折唇: 远缘中点落 (W/2, D-lip, Hb) + 全片平面 z=Hb (平面性+覆盖深度双判据)
    res["lip.far"] = _d(_fm(world, "lip", 2, 3),
                        (float(ir.param("W")) / 2.0, D - lp, Hb))
    res["lip.planar"] = float(np.max(np.abs(np.asarray(world["lip"], float)[:, 2] - Hb)))
    return res


# ---------------------------------------------------------- ④ food_bento_lid_box
def _build_bento(p):
    W, D, H, Hl, c = (float(p["W"]), float(p["D"]), float(p["H"]),
                      float(p["Hl"]), float(p["c"]))
    y1, Db = D + H, D + c
    yf = y1 + Db                      # 盘前缘网 y
    panels = [
        _rect("bA", "wall", 0.0, 0.0, W, D),
        _rect("wF", "wall", 0.0, -H, W, 0.0),
        _rect("wR", "wall", W, 0.0, W + H, D),
        _rect("wB", "wall", 0.0, D, W, y1),
        _rect("wL", "wall", -H, 0.0, 0.0, D),
        # 浅盘盖: 盘底 (顶点序保证扇形三角化无退化: 首点取前缘角)
        _poly("bB", "wall", [(W + c, yf), (-c, yf), (-c, y1),
                             (0, y1), (W, y1), (W + c, y1)]),
        _rect("wBl", "wall", -c - Hl, y1, -c, yf),
        _rect("wBr", "wall", W + c, y1, W + c + Hl, yf),
        _rect("wBf", "wall", -c, yf, W + c, yf + Hl),
        # 双唇: 外唇 (深 c, 抵盖盘前缘) / 内唇 (深 c, 贴前墙外面)
        _rect("tA", "flap", 0.0, -H - c, W, -H),
        _rect("tBi", "flap", -c, yf + Hl, W + c, yf + Hl + c),
    ]
    edges = [
        _fold("e_wF", (0, 0), (W, 0), "bA", "wF", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_wR", (W, 0), (W, D), "bA", "wR", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_wB", (0, D), (W, D), "bA", "wB", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_wL", (0, 0), (0, D), "bA", "wL", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_bB", (0, y1), (W, y1), "wB", "bB", (0.0, -1.0, 0.0), "MOUNTAIN"),
        _fold("e_wBl", (-c, y1), (-c, yf), "bB", "wBl", (0.0, 0.0, -1.0), "MOUNTAIN"),
        _fold("e_wBr", (W + c, y1), (W + c, yf), "bB", "wBr", (0.0, 0.0, -1.0),
              "MOUNTAIN"),
        _fold("e_wBf", (-c, yf), (W + c, yf), "bB", "wBf", (0.0, 0.0, -1.0),
              "MOUNTAIN"),
        _fold("e_tA", (0, -H), (W, -H), "wF", "tA", (0.0, -1.0, 0.0), "MOUNTAIN"),
        _fold("e_tBi", (-c, yf + Hl), (W + c, yf + Hl), "wBf", "tBi", (0.0, 1.0, 0.0),
              "MOUNTAIN"),
    ]
    notes = (f"bento_lid_box: 便当双层 (单件连体拓扑) — 底盒 4 墙 {H:g} + 浅盘盖 "
             f"(盘底 = 底盒外扩 clearance c={c:g} 两侧, 铰链于背墙顶缘前扣, 3 矮墙 "
             f"{Hl:g} 外包缘包口) 双唇: 外唇 (深 c) 远缘抵盖盘前缘 (z=H 平面互扣), "
             "内唇 (深 c) 贴前墙外面 (z=H-Hl 水平贴合), clamp_shell 双唇同款")
    return panels, edges, notes, _features()


def _c_bento(ir, world):
    W, D, H, Hl, c = (float(ir.param("W")), float(ir.param("D")),
                      float(ir.param("H")), float(ir.param("Hl")),
                      float(ir.param("c")))
    f, r, b, l = world["wF"], world["wR"], world["wB"], world["wL"]
    bl, br, bf, bb = world["wBl"], world["wBr"], world["wBf"], world["bB"]
    res: dict[str, float] = {}
    res["corner.fr"] = float(max(_d(f[1], r[1]), _d(f[2], r[0])))
    res["corner.rb"] = float(max(_d(r[2], b[2]), _d(r[3], b[1])))
    res["corner.bl"] = float(max(_d(b[3], l[3]), _d(b[0], l[2])))
    res["corner.lf"] = float(max(_d(l[0], f[0]), _d(l[1], f[3])))
    res["bB.zH"] = float(np.max(np.abs(np.asarray(bb, float)[:, 2] - H)))
    # 缘包口配合: 盖盘+B墙 x/y 外跨 - 底盒外跨 = 2c / c (展向差)
    xs = np.vstack([bb, bl, br, bf])
    res["fit.x"] = abs(float(xs[:, 0].max() - xs[:, 0].min()) - (W + 2 * c))
    res["fit.y"] = abs(float(xs[:, 1].max() - xs[:, 1].min()) - (D + c))
    # B 角缝 + 唇
    res["corner.B.bl"] = _d(bl[3], bf[3])
    res["corner.B.br"] = _d(br[2], bf[2])
    res["tA.meet"] = _d(_fm(world, "tA", 0, 1), _fm(world, "bB", 0, 1))
    res["tBi.seat_y"] = abs(float(_fm(world, "tBi", 2, 3)[1]))
    res["tBi.seat_z"] = abs(float(np.mean(np.asarray(world["tBi"], float)[:, 2]))
                            - (H - Hl))
    return res


# ---------------------------------------------------------- ⑤ food_wrap_pocket
def _build_wrap(p):
    W, H, hb, gs, gw, sd = (float(p["W"]), float(p["H"]), float(p["hb"]),
                            float(p["gs"]), float(p["glue_w"]), float(p["sd"]))
    dep = math.hypot(gs, hb)                     # 顶斜封盖深: 深角抵前板顶角
    x1, x2, x3 = W, W + gs, W + gs + W           # gL 右缘 / wB 右缘
    panels = [
        _rect("wF", "wall", 0.0, 0.0, W, H),
        _poly("gL", "wall", [(W, 0), (x1 + gs, 0), (x1 + gs, H + hb), (W, H)]),
        _rect("wB", "wall", x1 + gs, 0.0, x2 + W, H + hb),
        _poly("gR", "wall", [(x2 + W, 0), (x2 + W + gs, 0),
                             (x2 + W + gs, H), (x2 + W, H + hb)]),
        _rect("glue", "glue", x2 + W + gs, 0.0, x2 + W + gs + gw, H),
        # 顶斜封盖: 铰链 = 背墙顶缘, 远缘斜切 (右端浅 sd)
        _poly("t2", "flap", [(x1 + gs, H + hb), (x2 + W, H + hb),
                             (x2 + W, H + hb + dep - sd), (x1 + gs, H + hb + dep)]),
    ]
    edges = [
        _fold("e_gL", (W, 0), (W, H), "wF", "gL", (0.0, 1.0, 0.0), "VALLEY"),
        _fold("e_wB", (x1 + gs, 0), (x1 + gs, H + hb), "gL", "wB", (-1.0, 0.0, 0.0),
              "VALLEY"),
        _fold("e_gR", (x2 + W, 0), (x2 + W, H + hb), "wB", "gR", (0.0, -1.0, 0.0),
              "VALLEY"),
        _fold("e_glue", (x2 + W + gs, 0), (x2 + W + gs, H), "gR", "glue",
              (1.0, 0.0, 0.0), "MOUNTAIN"),
        _fold("e_t2", (x1 + gs, H + hb), (x2 + W, H + hb), "wB", "t2",
              (0.0, -gs / dep, -hb / dep), "MOUNTAIN"),
    ]
    notes = (f"wrap_pocket: 卷饼纸袋 (单件连体拓扑) — 侧折纸袋式: 前板 {W:g}x{H:g} + "
             f"两侧内折梯形翼 (深 {gs:g}, 前缘 H / 后缘 H+hb) + 高背后板 (H+{hb:g}) "
             "环闭远缘缝 (gR 远棱 ↔ wF 左棱) + 顶斜封盖 (深 = sqrt(gs^2+hb^2) = "
             f"{dep:.2f}, 深角精确抵前板顶角 (W,0,H), 远缘斜切 {sd:g}) + 粘口贴 wF")
    return panels, edges, notes, _features("glue")


def _c_wrap(ir, world):
    W, H, hb, gs, gw, sd = (float(ir.param("W")), float(ir.param("H")),
                            float(ir.param("hb")), float(ir.param("gs")),
                            float(ir.param("glue_w")), float(ir.param("sd")))
    dep = math.hypot(gs, hb)
    f, gl, b, gr = world["wF"], world["gL"], world["wB"], world["gR"]
    res: dict[str, float] = {}
    # 环闭: 3 铰结顶角重合 + gR 远棱 ↔ wF 左棱 (跨链)
    res["jn.FL"] = _d(f[2], gl[3])
    res["jn.LB"] = _d(gl[2], b[3])
    res["jn.BR"] = _d(b[2], gr[3])
    res["seam.RF"] = float(max(_d(gr[1], f[0]), _d(gr[2], f[3])))
    # 粘口: 落前板平面 y=0 + 反贴宽度
    g = np.asarray(world["glue"], float)
    res["glue.planar"] = float(np.max(np.abs(g[:, 1])))
    res["glue.width"] = abs(float(np.max(g[:, 0])) - gw)
    # 顶斜封盖: 深角 ↔ 前板右上顶角 (wF idx2); 浅角解析落位; 斜缘两重判据
    res["t2.deep"] = _d(world["t2"][3], f[2])
    tgt = (0.0, gs - (dep - sd) * gs / dep, H + hb - (dep - sd) * hb / dep)
    res["t2.shallow"] = _d(world["t2"][2], tgt)
    return res


# ---------------------------------------------------------- ⑥ food_sushi_tray
def _sushi_octo(W, D, ch):
    """切角八边形顶点 CCW (edge0 = 前长缘)."""
    return [np.array([ch, 0.0]), np.array([W - ch, 0.0]), np.array([W, ch]),
            np.array([W, D - ch]), np.array([W - ch, D]), np.array([ch, D]),
            np.array([0.0, D - ch]), np.array([0.0, ch])]


def _octo_normals(vs):
    ns = []
    n = len(vs)
    for i in range(n):
        t = _unit(np.asarray(vs[(i + 1) % n], float) - np.asarray(vs[i], float))
        ns.append(np.array([t[1], -t[0]]))
    return ns


def _build_sushi(p):
    W, D, H, Hl, c = (float(p["W"]), float(p["D"]), float(p["H"]),
                      float(p["Hl"]), float(p["c"]))
    ch, gw, webw = float(p["ch"]), float(p["glue_w"]), float(p["web_w"])
    vs = _sushi_octo(W, D, ch)
    ns = _octo_normals(vs)
    panels = [_poly("floor", "wall", vs)]
    edges = []
    for i in range(8):
        if i == 7:      # 末片带半高分点 (粘口铰链端点须顶点)
            panels.append(_poly("w7", "wall",
                                [vs[7], vs[0], vs[0] + (H / 2.0) * ns[7],
                                 vs[0] + H * ns[7], vs[7] + H * ns[7]]))
        else:
            panels.append(_poly(f"w{i}", "wall",
                                [vs[i], vs[i + 1], vs[i + 1] + H * ns[i],
                                 vs[i] + H * ns[i]]))
        edges.append(_fold(f"e_w{i}", vs[i], vs[(i + 1) % 8], "floor",
                           f"w{i}" if i < 7 else "w7", (0.0, 0.0, 1.0), "MOUNTAIN"))
    # 粘口: w7 端棱上半段, 折合于 w0 内面 (tray_6corner 同款)
    A = vs[0] + (H / 2.0) * ns[7]
    Bp = vs[0] + H * ns[7]
    t0 = _unit(vs[1] - vs[0])
    panels.append(_poly("glue", "glue", [A, Bp, Bp + gw * t0, A + gw * t0]))
    edges.append(_fold("e_glue", A, Bp, "w7", "glue", (float(t0[0]), float(t0[1]), 0.0),
                       "MOUNTAIN"))
    # --- web 工艺条: 铰链于 w4 (背墙) 顶缘, 平折向后 (分离拓扑, two_piece 同款)
    uvs = _offset_poly(vs, c)
    x4e, x5e = W / 2.0 - (W - 2 * ch) / 2.0, W / 2.0 + (W - 2 * ch) / 2.0
    yw = D + H
    yf2 = yw + webw                       # 盖后墙 L0 底缘网 y
    yfl = yf2 + Hl                        # 盖盘底背缘网 y (LB 远缘铰链线)
    panels.append(_rect("web", "flap", x4e, yw, x5e, yf2))
    edges.append(_fold("e_web", (vs[4][0], yw), (vs[5][0], yw), "w4", "web",
                       (0.0, 1.0, 0.0), "MOUNTAIN"))
    # 盖盘底 = 托底外偏置 c, 背缘铰链于 LB 远缘 (网 y = yfl), 盘体向后镜像展开。
    # 平移放置会把盘体压回托网 (G03 自压); LB 面片全等锁定背缘位置, 铰链边不动
    # 唯一的自由放置 = 沿铰线镜像 (引擎对镜像不敏感, 3D 落位不变)
    shift = yfl - float(uvs[4][1])
    uv = [np.array([q[0], 2.0 * yfl - (q[1] + shift)]) for q in uvs]
    panels.append(_poly("lfloor", "wall", uv))
    # uv 镜像后绕序反转 (CW), 外法线 = 内法线取反
    uns = [np.array([-n[0], -n[1]]) for n in _octo_normals(uv)]
    # 盖后墙 LB (梯形: 底缘 = web 远缘, 顶缘 = 盘底背缘), 上升
    panels.append(_poly("LB", "wall", [(x4e, yf2), (x5e, yf2), uv[4], uv[5]]))
    edges += [
        _fold("e_LBw", (x4e, yf2), (x5e, yf2), "web", "LB", (0.0, 0.0, 1.0),
              "MOUNTAIN"),
        _fold("e_LBf", uv[4], uv[5], "LB", "lfloor", (0.0, -1.0, 0.0), "MOUNTAIN"),
    ]
    # 盖墙 (挂下): 除背缘 (L0) 外 7 片; 末片 (edge7) 带半高分点 + 盖粘口
    for i in range(8):
        if i == 4:
            continue
        if i == 7:
            panels.append(_poly("L7", "wall",
                                [uv[7], uv[0], uv[0] + (Hl / 2.0) * uns[7],
                                 uv[0] + Hl * uns[7], uv[7] + Hl * uns[7]]))
            edges.append(_fold("e_L7", uv[7], uv[0], "lfloor", "L7",
                               (0.0, 0.0, -1.0), "MOUNTAIN"))
        else:
            panels.append(_poly(f"L{i}", "wall",
                                [uv[i], uv[i + 1], uv[i + 1] + Hl * uns[i],
                                 uv[i] + Hl * uns[i]]))
            edges.append(_fold(f"e_L{i}", uv[i], uv[i + 1], "lfloor", f"L{i}",
                               (0.0, 0.0, -1.0), "MOUNTAIN"))
    A2 = uv[0] + (Hl / 2.0) * uns[7]
    B2 = uv[0] + Hl * uns[7]
    t02 = _unit(uv[1] - uv[0])
    # 伸入 L7/L0 端棱间空楔 (外法线角平分向; ±t02 均会压邻墙净图带,
    # tray_6corner 粘口空楔同款思路)
    wgt = _unit(uns[7] + uns[0])
    panels.append(_poly("lglue", "glue",
                        [A2, B2, B2 + gw * wgt, A2 + gw * wgt]))
    edges.append(_fold("e_lglue", A2, B2, "L7", "lglue",
                       (float(t02[0]), float(t02[1]), 0.0), "MOUNTAIN"))
    notes = (f"sushi_tray: 寿司托 (分离式两件拓扑, 网内 web 条 {webw:g}mm 相连供整版) "
             f"— 长圆角托: 切角八边形底 {W:g}x{D:g} (角切 {ch:g}) + 8 墙 {H:g} + 粘口; "
             f"分离式透明盖: 盘底 = 托底外偏置 c={c:g} 的八边形 (缘包口), 8 矮墙 {Hl:g} "
             "(世界系倒扣悬置于 web 后方, 成型后两件分离) + 盖粘口")
    return panels, edges, notes, _features("glue", "lglue")


def _c_sushi(ir, world):
    W, D, H, Hl, c, ch, webw = (float(ir.param("W")), float(ir.param("D")),
                                float(ir.param("H")), float(ir.param("Hl")),
                                float(ir.param("c")), float(ir.param("ch")),
                                float(ir.param("web_w")))
    res: dict[str, float] = {}
    # 托环缝: 8 顶结顶点重合 (w7 带半高分点特殊索引)
    for k in range(8):
        if k == 7:
            res["seam.v0"] = _d(world["w7"][3], world["w0"][3])
        elif k == 6:
            res["seam.v7"] = _d(world["w6"][2], world["w7"][4])
        else:
            res[f"seam.v{k + 1}"] = _d(world[f"w{k}"][2], world[f"w{k + 1}"][3])
    g = np.asarray(world["glue"], float)
    res["glue.seat"] = float(np.max(np.abs(g[:, 1])))
    # 盖环缝 (挂下墙: idx2/idx3 = 悬挂远端; LB 上升梯形斜腿跨角 v4/v5 跳过)
    res["lseam.v0"] = _d(world["L7"][3], world["L0"][3])
    res["lseam.v1"] = _d(world["L0"][2], world["L1"][3])
    res["lseam.v2"] = _d(world["L1"][2], world["L2"][3])
    res["lseam.v3"] = _d(world["L2"][2], world["L3"][3])
    res["lseam.v6"] = _d(world["L5"][2], world["L6"][3])
    res["lseam.v7"] = _d(world["L6"][2], world["L7"][4])
    lg = np.asarray(world["lglue"], float)
    res["lglue.seat"] = float(np.max(np.abs(lg[:, 1] - (webw - 2 * c))))
    # web 工艺条落位: 远缘抵 y=D+webw + 全片平面 z=H (折叠正确性)
    res["web.far"] = abs(float(_fm(world, "web", 2, 3)[1]) - (float(ir.param("D")) + webw))
    res["web.planar"] = float(np.max(np.abs(np.asarray(world["web"], float)[:, 2] - H)))
    # 盖盘底倒扣悬置平面 z=H+Hl (跨件装配落位)
    lf = np.asarray(world["lfloor"], float)
    res["lid.plane"] = float(np.max(np.abs(lf[:, 2] - (H + Hl))))
    # 配合证据 (跨件展向差, two_piece 同款): 盘底跨 = 托底跨 + 2c; 盖深 Hl
    xs = np.vstack([world["floor"]] + [world[f"w{i}"] for i in range(8)])
    lids = [world["lfloor"], world["LB"]] + [world[f"L{i}"] for i in range(8)
                                             if i != 4]
    xl = np.vstack(lids)
    res["fit.x"] = abs(float(xl[:, 0].max() - xl[:, 0].min())
                       - (float(xs[:, 0].max() - xs[:, 0].min()) + 2 * c))
    res["fit.y"] = abs(float(xl[:, 1].max() - xl[:, 1].min()) - (D + 2 * c))
    res["fit.z"] = abs(float(xs[:, 2].max() - xs[:, 2].min())
                       - (float(xl[:, 2].max() - xl[:, 2].min())) - (H - Hl))
    return res


# ---------------------------------------------------------- ⑦ food_tray_liner
def _build_liner(p):
    side, H, hem, gw = (float(p["side"]), float(p["H"]), float(p["hem_d"]),
                        float(p["glue_w"]))
    vs, outward, tangent, _ = _hex_geom(side)
    panels = [_poly("base", "wall", vs)]
    edges = []
    for i in range(6):
        j = (i + 1) % 6
        vi, vj, oi = vs[i], vs[j], outward[i]
        if i == 5:      # 末墙带半高分点 (粘口铰链端点须顶点)
            panels.append(_poly("w5", "wall",
                                [vi, vj, vj + (H / 2.0) * oi, vj + H * oi,
                                 vi + H * oi]))
        else:
            panels.append(_poly(f"w{i}", "wall",
                                [vi, vj, vj + H * oi, vi + H * oi]))
        edges.append(_fold(f"e_w{i}", vi, vj, "base", f"w{i}" if i < 5 else "w5",
                           (0.0, 0.0, 1.0), "MOUNTAIN"))
    # 角片 c0..c4: 挂 w_i 端棱, 钝角楔区折合 w_{i+1} 内面 (tray_6corner 同款)
    for i in range(5):
        j = (i + 1) % 6
        m = np.array([outward[i][0] * math.cos(math.pi / 6)
                      - outward[i][1] * math.sin(math.pi / 6),
                      outward[i][0] * math.sin(math.pi / 6)
                      + outward[i][1] * math.cos(math.pi / 6)])
        A, Bp = vs[j], vs[j] + H * outward[i]
        panels.append(_poly(f"c{i}", "flap", [A, Bp, Bp + gw * m, A + gw * m]))
        edges.append(_fold(f"e_c{i}", A, Bp, f"w{i}", f"c{i}",
                           (*tangent[j], 0.0), "MOUNTAIN"))
    # 粘口: w5 端棱上半段, 折合 w0 内面; 净图伸 +t5 空楔 (避开 w0 净图带,
    # tray_6corner 同款 — 伸 +t0 会切进 w0 带 ~0.3mm²)
    A = vs[0] + (H / 2.0) * outward[5]
    Bp = vs[0] + H * outward[5]
    panels.append(_poly("glue", "glue",
                        [A, Bp, Bp + gw * tangent[5], A + gw * tangent[5]]))
    edges.append(_fold("e_glue", A, Bp, "w5", "glue",
                       (*tangent[0], 0.0), "MOUNTAIN"))
    # 防尘翻缘 f0..f5: 铰链 = 墙顶缘, 对角平分斜缘 (刚体展开 congruence),
    # 折合后 6 片内翻缘拼接成环, 角点互抵 (沿棱折链)
    bis = []                                   # 角 k 内向平分线 (世界 2D)
    for k in range(6):
        bis.append(_unit(-(outward[(k - 1) % 6] + outward[k])))
    for i in range(6):
        j = (i + 1) % 6
        ti = tangent[i]
        oi = outward[i]
        hl = vs[i] + H * oi
        hr = vs[j] + H * oi

        def _net_off(corner):                  # 镜像 ⊥ 分量 → 网偏移
            d = hem * bis[corner]
            return (float(np.dot(d, ti)) * ti - float(np.dot(d, oi)) * oi)

        panels.append(_poly(f"f{i}", "flap",
                            [hl, hr, hr + _net_off(j), hl + _net_off(i)]))
        fl = vs[i] + hem * bis[i]
        fr = vs[j] + hem * bis[j]
        fmid = (fl + fr) / 2.0
        hmid = (hl + hr) / 2.0
        # 折向声明合同: tdir 须为单位向量且 ⊥ 世界铰链轴 (轴 = 墙顶缘方向,
        # R_STAR 星形网下 = 净图铰线方向); 引擎本就投影, 显式化后 G04 折向门可核
        d3 = np.array([float((fmid - hmid)[0]), float((fmid - hmid)[1]), 0.0])
        ax3 = _unit(np.array([float((hr - hl)[0]), float((hr - hl)[1]), 0.0]))
        d3 = d3 - float(d3 @ ax3) * ax3
        edges.append(_fold(f"e_f{i}", hl, hr, f"w{i}" if i < 5 else "w5", f"f{i}",
                           _unit(d3), "MOUNTAIN"))
    notes = (f"tray_liner: 托盘内衬 (单件连体拓扑) — 六角浅盘 (边长 {side:g}, 浅深 "
             f"{H:g}) + 5 角片 + 粘口 (tray_6corner 同款) + 防尘翻缘 6 片沿棱折链 "
             f"(内折深 {hem:g}, 对角平分斜缘拼接成环, 相邻翻缘角点互抵)")
    return panels, edges, notes, _features("glue")


def _c_liner(ir, world):
    side, H, hem = (float(ir.param("side")), float(ir.param("H")),
                    float(ir.param("hem_d")))
    vs, outward, _, _ = _hex_geom(side)
    bis = [_unit(-(outward[(k - 1) % 6] + outward[k])) for k in range(6)]
    res: dict[str, float] = {}
    # 六角环缝: 墙顶结重合 (w5 带分点特殊索引)
    for i in range(4):
        j = (i + 1) % 6
        res[f"seam.v{j}"] = _d(world[f"w{i}"][2], world[f"w{j}"][3])
    res["seam.v5"] = _d(world["w4"][2], world["w5"][4])
    res["seam.v0"] = _d(world["w5"][3], world["w0"][3])
    # 角片贴合 (贴邻墙内面)
    for cid, i in (("c0", 0), ("c1", 1), ("c2", 2), ("c3", 3), ("c4", 4)):
        j = (i + 1) % 6
        oj = np.array([*outward[j], 0.0])
        vj = np.array([*vs[j], 0.0])
        res[f"{cid}.on_plane"] = float(np.max(
            np.abs((np.asarray(world[cid], float) - vj) @ oj)))
    g = np.asarray(world["glue"], float)
    o0 = np.array([*outward[0], 0.0])
    res["glue.on_plane"] = float(np.max(np.abs(
        (g - np.array([*vs[0], 0.0])) @ o0)))
    # 翻缘环: 相邻片角点互抵 (角 k: f_k 远左 ↔ f_{k-1} 远右) + 平面 z=H + 落位
    for k in range(6):
        prev = f"f{(k - 1) % 6}"
        res[f"rim.meet.v{k}"] = _d(world[f"f{k}"][3], world[prev][2])
    zr = np.vstack([world[f"f{i}"] for i in range(6)])[:, 2]
    res["rim.planar"] = float(np.max(np.abs(zr - H)))
    for i in range(6):
        j = (i + 1) % 6
        tgt = (vs[i] + hem * bis[i] + vs[j] + hem * bis[j]) / 2.0
        res[f"f{i}.seat"] = _d(_fm(world, f"f{i}", 2, 3), (float(tgt[0]),
                                                           float(tgt[1]), H))
    return res


# ------------------------------------------------------------ 契约
_CLASS_PARAMS = {
    "food_clamshell_burger": {"kind": 0, "W": 100.0, "D": 100.0, "H": 28.0,
                              "ra": 20.0, "k": 6.0, "board_t": 0.45},
    "food_noodle_pail": {"kind": 1, "side_b": 40.0, "side_t": 32.0, "h": 70.0,
                         "s_p": 20.0, "gd": 10.0, "nw": 14.0, "nd": 7.0,
                         "glue_w": 10.0, "board_t": 0.42},
    "food_fries_sleeve": {"kind": 2, "W": 75.0, "D": 32.0, "Hf": 70.0, "Hb": 95.0,
                          "lip_d": 10.0, "glue_w": 12.0, "board_t": 0.45},
    "food_bento_lid_box": {"kind": 3, "W": 120.0, "D": 80.0, "H": 40.0, "Hl": 12.0,
                           "c": 2.5, "board_t": 0.45},
    "food_wrap_pocket": {"kind": 4, "W": 150.0, "H": 95.0, "hb": 25.0, "gs": 45.0,
                         "sd": 15.0, "glue_w": 12.0, "board_t": 0.45},
    "food_sushi_tray": {"kind": 5, "W": 190.0, "D": 120.0, "H": 35.0, "Hl": 12.0,
                        "c": 3.0, "ch": 18.0, "glue_w": 10.0, "web_w": 8.0,
                        "board_t": 0.45},
    "food_tray_liner": {"kind": 6, "side": 45.0, "H": 16.0, "hem_d": 10.0,
                        "glue_w": 8.0, "board_t": 0.45},
}


def class_params(cls_id: str) -> dict:
    """类ID → 全键参数表 (批量 build_ir 判型与取值的唯一权威)."""
    if cls_id not in _CLASS_PARAMS:
        raise KeyError(f"未知类ID: {cls_id}")
    p = {k: 0.0 for k in PARAM_ORDER}
    p.update(_CLASS_PARAMS[cls_id])
    return p


def _pos(p, *keys):
    for k in keys:
        v = p.get(k)
        if v is None or not isinstance(v, (int, float)) or isinstance(v, bool) \
                or float(v) <= 0:
            raise ValueError(f"非法参数 {k}={v!r} (须正数)")


def validate_params(params: dict) -> None:
    kind = int(params.get("kind", 0))
    _pos(params, "board_t")
    if kind == 0:
        _pos(params, "W", "D", "H", "ra")
        k = int(params.get("k", 6))
        if k % 2 != 0 or not 4 <= k <= 12:
            raise ValueError(f"拱盖弦片数 k={k} 须偶数且 4..12")
        if float(params["ra"]) >= float(params["D"]) / 2.0:
            raise ValueError("拱升高 ra 须小于 D/2 (弧圆心须低于弦口)")
        _, _, pts = _arch_refs(float(params["D"]), float(params["H"]),
                               float(params["ra"]), k)
        sweep = math.pi - 2.0 * math.atan2(
            ((float(params["D"]) / 2.0) ** 2 - float(params["ra"]) ** 2)
            / (2.0 * float(params["ra"])), float(params["D"]) / 2.0)
        if sweep < 0.35:
            raise ValueError(f"弧拱总转角过小 ({math.degrees(sweep):.1f}°), 弦片退化")
    elif kind == 1:
        _pos(params, "side_b", "side_t", "h", "s_p", "gd", "nw", "nd", "glue_w")
        g, _, _, _ = _pail_refs(float(params["side_b"]), float(params["side_t"]),
                                float(params["h"]))
        if not float(params["s_p"]) < float(params["side_t"]):
            raise ValueError("开口边长 s_p 须小于顶边 side_t (收顶)")
        if float(params["nw"]) >= float(params["side_t"]) * 0.6:
            raise ValueError("缺口宽 nw 须小于 0.6*side_t")
        if float(params["nd"]) >= 0.6 * (g["lb"] - g["lt"]):
            raise ValueError("缺口深 nd 须小于 0.6*(lb-lt) (墙净深)")
        if float(params["glue_w"]) >= g["Le"]:
            raise ValueError("粘口 glue_w 须窄于侧棱长 Le")
    elif kind == 2:
        _pos(params, "W", "D", "Hf", "Hb", "lip_d", "glue_w")
        if float(params["Hb"]) <= float(params["Hf"]):
            raise ValueError("薯条套须 Hb > Hf (前矮后高)")
        if float(params["lip_d"]) >= float(params["D"]):
            raise ValueError("内折唇深 lip_d 须小于 D")
        if float(params["glue_w"]) >= float(params["Hf"]):
            raise ValueError("粘口 glue_w 须窄于前墙高 Hf")
    elif kind == 3:
        _pos(params, "W", "D", "H", "Hl", "c")
        if float(params["Hl"]) >= float(params["H"]):
            raise ValueError("盖为浅盘: 须 Hl < H")
    elif kind == 4:
        _pos(params, "W", "H", "hb", "gs", "sd", "glue_w")
        dep = math.hypot(float(params["gs"]), float(params["hb"]))
        if float(params["sd"]) >= 0.6 * dep:
            raise ValueError(f"斜切 sd 须小于 0.6*dep={0.6 * dep:.2f}")
        if float(params["glue_w"]) >= float(params["W"]) / 2.0:
            raise ValueError("粘口 glue_w 须窄于半前板宽")
    elif kind == 5:
        _pos(params, "W", "D", "H", "Hl", "c", "ch", "glue_w", "web_w")
        if not float(params["ch"]) < min(float(params["W"]), float(params["D"])) / 2.0:
            raise ValueError("角切 ch 须小于半最短边 (八边形退化)")
        if float(params["Hl"]) >= float(params["H"]):
            raise ValueError("盖为浅盘: 须 Hl < H")
    else:
        _pos(params, "side", "H", "hem_d", "glue_w")
        a = float(params["side"]) / (2.0 * math.tan(math.pi / 6))
        if float(params["H"]) >= a:
            raise ValueError("浅盘: 格深 H 须小于 apothem")
        if float(params["hem_d"]) >= 0.8 * a:
            raise ValueError(f"翻缘深 hem_d 须小于 0.8*apothem={0.8 * a:.2f}")
        if float(params["glue_w"]) > float(params["H"]) / 2.0:
            raise ValueError("粘口 glue_w 须不超过 H/2 (铰链段置于端棱上半段)")


_BUILDERS = (_build_clamshell, _build_pail, _build_fries, _build_bento,
             _build_wrap, _build_sushi, _build_liner)
_CLOSURES = (_c_clamshell, _c_pail, _c_fries, _c_bento, _c_wrap, _c_sushi,
             _c_liner)
_ROOTS = (("base", _R_STAR), ("w0", None), ("floor", _R_STAR),
          ("bA", _R_STAR), ("wF", _R_CHAIN), ("floor", _R_STAR),
          ("base", _R_STAR))


def build_ir(params: dict | None = None) -> dict:
    p = {**DEFAULTS, **(params or {})}
    kind = int(p.get("kind", 0))
    if not 0 <= kind < len(_BUILDERS):
        raise ValueError(f"非法 kind={kind!r} (须 0..{len(_BUILDERS) - 1})")
    cls_id = _CLS[kind]
    validate_params(p)
    built = _BUILDERS[kind](p)
    if kind == 1:
        panels, edges, notes = built[0], built[1], built[2]
        Rf = [[float(x) for x in row] for row in built[3]]
        off_x = [float(x) for x in built[4]]
        feats = _features("glue")
        root = "w0"
    else:
        panels, edges, notes, feats = built
        root, Rf = _ROOTS[kind]
        off_x = [0.0, 0.0, 0.0]
    return {
        "meta": {"ir_version": "0.1", "units": "mm",
                 "generator": "photo_dieline.parametric.food_packs 0.1",
                 "notes": notes, "root_panel": root,
                 "root_frame": {"R": Rf, "off": off_x}},
        "package": {"type": cls_id,
                    "template": {"id": cls_id, "version": "0.1"},
                    "params": {k: float(p[k]) for k in PARAM_ORDER},
                    "photo": None},
        "panels": panels,
        "edges": edges,
        "features": feats,
    }


def analytic_bbox(params: dict) -> dict:
    """G05 期望: solid (wall+slope 角色) 折叠 bbox."""
    p = {**DEFAULTS, **(params or {})}
    kind = int(p.get("kind", 0))
    if kind == 0:
        return {"W": float(p["W"]), "D": float(p["D"]),
                "H": float(p["H"]) + float(p["ra"])}
    if kind == 1:
        _, vb, vt, _ = _pail_refs(float(p["side_b"]), float(p["side_t"]),
                                  float(p["h"]))
        pts = np.vstack(vb + vt)
        return {"W": float(pts[:, 0].max() - pts[:, 0].min()),
                "D": float(pts[:, 1].max() - pts[:, 1].min()),
                "H": float(p["h"])}
    if kind == 4:
        return {"W": float(p["W"]), "D": float(p["gs"]), "H": float(p["H"])
                + float(p["hb"])}
    if kind == 5:
        c, webw, Hl = float(p["c"]), float(p["web_w"]), float(p["Hl"])
        return {"W": float(p["W"]) + 2 * c, "D": float(p["D"]) + webw,
                "H": float(p["H"]) + Hl}
    if kind == 6:
        side, H = float(p["side"]), float(p["H"])
        return {"W": 2.0 * side, "D": math.sqrt(3.0) * side, "H": H}
    if kind == 3:
        W, D, H, Hl, c = (float(p["W"]), float(p["D"]), float(p["H"]),
                          float(p["Hl"]), float(p["c"]))
        xs = [0.0, W, -c, W + c]          # A 墙平面 0..W; 盖盘+B墙外包 ±c
        ys = [0.0, D, -c]                 # 盖盘前缘越前板 c (包口)
        return {"W": max(xs) - min(xs), "D": max(ys) - min(ys), "H": H}
    return {"W": float(p["W"]), "D": float(p["D"]), "H": float(p["Hb"])}


def solid_roles():
    return ("wall", "slope")


def allowed_overlap():
    """G06 允许叠层 (真实工艺契约, 全家族并集):
    粘口贴邻墙/前墙内面, 环闭合末墙↔首墙, 拱盖末段抵前墙顶缘, 便当盖缘包口
    共面贴合+双唇互扣/层压, 卷饼顶斜封盖跨翼口缘接触, 六角翻缘对角拼接层区."""
    s = {
        # ① 拱盖末段远缘抵前墙顶缘 (扣合接触; 默认类 k=6 → s6)
        frozenset({"s6", "wF"}),
        # ② 粉盒: 粘口贴 w0, 环闭合末墙↔首墙, 收顶片互相逼近, 双翼对折对合
        frozenset({"glue", "w0"}), frozenset({"w0", "w7"}),
    }
    tf = [f"tf{i}" for i in range(_PN)]
    for i in range(_PN):
        for j in range(i + 1, _PN):
            s.add(frozenset({tf[i], tf[j]}))
    # 收顶片侧缘沿邻墙内面折入 (工艺折入顺序: 片缘贴邻墙内面) + 片缘角触粘口
    for i in range(_PN):
        s.add(frozenset({f"tf{i}", f"w{(i + 1) % _PN}"}))
        s.add(frozenset({f"tf{i}", f"w{(i - 1) % _PN}"}))
    s.add(frozenset({"tf0", "glue"}))
    s.add(frozenset({"wg0", "wg4"}))
    # ③ 薯条套粘口贴前墙
    s.add(frozenset({"glue", "wF"}))
    # ④ 便当: 双唇 (外唇/盖盘 z=H 层压, 外唇/盖前墙缘触, 内唇贴前墙外面)
    s |= {frozenset({"tA", "bB"}),
          frozenset({"tA", "wBf"}), frozenset({"tBi", "wF"})}
    # ⑤ 卷饼: 粘口贴前墙 + 顶斜封盖跨两翼口缘
    s |= {frozenset({"glue", "wF"}), frozenset({"t2", "gL"}),
          frozenset({"t2", "gR"})}
    # ⑥ 寿司托: 托/盖各自粘口贴首墙
    s |= {frozenset({"glue", "w0"}), frozenset({"lglue", "L0"})}
    # ⑦ 内衬: 粘口贴 w0, 角片贴宿墙内面 (tray_6corner 同款),
    #     翻缘相邻对角拼接共面区, 翻缘与角片线触
    s.add(frozenset({"glue", "w0"}))
    for i in range(5):
        s.add(frozenset({f"c{i}", f"w{(i + 1) % 6}"}))
    for i in range(6):
        s.add(frozenset({f"f{i}", f"f{(i + 1) % 6}"}))
        s.add(frozenset({f"f{i}", f"c{i}"}))
        s.add(frozenset({f"f{(i + 1) % 6}", f"c{i}"}))
    return s


def closure_checks(ir, world) -> dict:
    return _CLOSURES[_CLS.index(ir.package["template"]["id"])](ir, world)


# ------------------------------------------------------------ 负探针
def _rodrigues(v, axis, ang):
    a = _unit(axis)
    k = np.asarray(v, float)
    return (k * math.cos(ang) + np.cross(a, k) * math.sin(ang)
            + a * float(a @ k) * (1.0 - math.cos(ang)))


def _perturb(raw_ir, edge_id, axis, ang=0.35):
    """绕真实世界铰链轴把 tdir 转开 ang 弧度 (引擎把 tdir 投影到轴垂直面 —
    只有绕轴的分量才改变折叠落位; 沿轴扰动为恒等操作)."""
    ir = copy.deepcopy(raw_ir)
    for e in ir["edges"]:
        if e["id"] == edge_id:
            t = np.asarray(e["fold"]["target_dir_3d"], float)
            tp = _rodrigues(t, axis, ang)
            e["fold"]["target_dir_3d"] = [float(v) for v in tp / np.linalg.norm(tp)]
            return ir
    raise KeyError(edge_id)


def _probe_targets(ir) -> list:
    """每类 2 条关键折线 → (edge_id, 铰链轴世界向)."""
    kind = _CLS.index(ir.package["template"]["id"])
    if kind == 1:
        _, vb, vt, _ = _pail_refs(_CP1["side_b"], _CP1["side_t"], _CP1["h"])
        return [("e_w3", _unit(vb[4] - vt[4])), ("e_tf0", _unit(vt[1] - vt[0]))]
    if kind == 6:
        _, _, tangent, _ = _hex_geom(_CP6["side"])
        return [("e_f0", (1.0, 0.0, 0.0)),
                ("e_w3", (float(tangent[3][0]), float(tangent[3][1]), 0.0))]
    return {0: [("e_s1", (1, 0, 0)), ("e_wF", (1, 0, 0))],
            2: [("e_wB", (1, 0, 0)), ("e_lip", (1, 0, 0))],
            3: [("e_bB", (1, 0, 0)), ("e_wBf", (1, 0, 0))],
            4: [("e_t2", (1, 0, 0)), ("e_gL", (0, 0, 1))],
            5: [("e_web", (1, 0, 0)), ("e_w2", (0, 1, 0))]}[kind]


_CP1 = _CLASS_PARAMS["food_noodle_pail"]
_CP6 = _CLASS_PARAMS["food_tray_liner"]


def probe(ir, fold_all, from_raw) -> dict:
    """负探针: 每类扰动 2 条关键折线 → closure 最大残差须爆到 mm 级.
    返回 {edge_id: (baseline_max, perturbed_max)}."""
    raw = ir.raw
    base = max(float(v) for v in closure_checks(ir, fold_all(ir)).values())
    out = {}
    for eid, ax in _probe_targets(ir):
        irp = from_raw(_perturb(raw, eid, ax))
        worst = max(float(v) for v in closure_checks(irp, fold_all(irp)).values())
        out[eid] = (base, worst)
    return out
