"""sundry_family: 杂项结构家族 (6 类) — 杯套/蛋托/提手盒/陈列台/方信封/扣夹盒.

类ID:
  cup_sleeve       杯套: n=12 多边形近似圆台侧带(上宽下窄扇形链), 顶/底缘各 12 片
                   缘折入内弯, 双端成环形成卡槽唇(插套槽口) + 搭接粘缝
  egg_tray_2x4     蛋托: 共享底盘 + 2×4 分格 — 中隔板(底盘中线铰链) + 前后墙
                   score 折链横隔半片×6(端缘于中线互抵), 共 8 格
  handle_box       提手盒: tuck 链 + 底全叠封 + 防尘翼 + 顶插盖(舌入前墙内面)
                   + 前墙顶缘直立提手孔板(顶缘 U 形凹口为提手孔)
  display_counter  陈列台: 高背板 + 低前板 + 两侧斜顶板 + 45° 斜前托板
                   (托板远缘精确抵背板顶缘: H = Hf + D 锁定)
  envelope_square  方信封: 正方形背面 + 四边折翼风车折合(全平折共面),
                   三角翻盖尖精确抵底翼远缘中线 (dt = S - flap_d)
  envelope_square 使用翼深 flap_d ≤ S/2; clamp_shell 两半壳铰链相连(共用背墙
  wAb 顶缘翻盖) + 对侧扣舌互扣(前缘双唇远缘相抵)

几何约定: 条带/板类根面板 net(x,y)→world(x,0,y) 或 identity; 杯套扇形链根框架
由 _fan_root 数值求解 (net 射线基 → 墙面基). closure 全部为折叠后世界坐标残差
(远缘重合/抵中线/共面贴合/到位深度), 无构造恒等量。
"""
from __future__ import annotations

import math

import numpy as np

from . import base as _base

# ---------------------------------------------------------------- 公共工具


def _unit(v) -> np.ndarray:
    n = float(np.linalg.norm(v))
    if n < 1e-12:
        raise ValueError("零向量")
    return np.asarray(v, float) / n


def _proj_perp(v, axis) -> np.ndarray:
    axis = _unit(axis)
    return np.asarray(v, float) - float(np.asarray(v, float) @ axis) * axis


def _pts(arr) -> list:
    return [[float(x), float(y)] for x, y in arr]


def _fold(eid, a2, b2, parent, child, tdir, mt="VALLEY") -> dict:
    return {"id": eid, "kind": "FOLD",
            "seg_2d": [[float(a2[0]), float(a2[1])], [float(b2[0]), float(b2[1])]],
            "fold": {"mt_va": mt, "parent": parent, "child": child,
                     "target_dir_3d": [round(float(v), 9) for v in tdir]}}


def _rect(pid, role, xa, ya, xb, yb) -> dict:
    """矩形板 CCW: [左下,右下,右上,左上] (顶点索引契约见 closure_checks)."""
    return {"id": pid, "role": role,
            "polygon_2d": [[float(xa), float(ya)], [float(xb), float(ya)],
                           [float(xb), float(yb)], [float(xa), float(yb)]]}


def _poly(pid, role, pts) -> dict:
    return {"id": pid, "role": role, "polygon_2d": _pts(pts)}


def _rect_split(pid, role, xa, ya, xb, yb, splits_x=(), splits_y=()) -> dict:
    """带铰链分点矩形 (CCW): splits_x 底/顶边 x 分点, splits_y 右/左边 y 分点.
    分点保证 G03 最近顶点匹配逐位一致 (window_box 先例).
    环序: 有 splits_x 时自右下角起 (右缘上行→顶缘右行→左缘下行→底缘右行),
    首三元组必非共线 (G06 检查器以 verts[0..2] 求面法线);
    无 splits_x 保持 [左下,右下,右上,左上] 契约."""
    sxs = sorted({float(s) for s in splits_x if xa < float(s) < xb})
    sys_ = sorted({float(s) for s in splits_y if ya < float(s) < yb})
    if sxs:
        pts: list = [[xb, ya], [xb, yb]]
        pts += [[s, yb] for s in reversed(sxs)] + [[xa, yb], [xa, ya]]
        pts += [[s, ya] for s in sxs]
    else:
        pts = [[xa, ya], [xb, ya]] + [[xb, s] for s in sys_] + \
              [[xb, yb], [xa, yb]] + [[xa, s] for s in reversed(sys_)]
    return {"id": pid, "role": role, "polygon_2d": _pts(pts)}


def _features(*glue_panels) -> list:
    fs = [{"id": f"f_g{i}", "kind": "GLUE_TAB", "panel_id": g}
          for i, g in enumerate(glue_panels)]
    fs += [{"id": "f_bleed", "kind": "BLEED", "offset_mm": 3.0},
           {"id": "f_check", "kind": "CHECK_BAR", "length_mm": 50.0},
           {"id": "f_reg", "kind": "REGISTRATION"}]
    return fs


def _fm(world, pid, i, j):
    return (np.asarray(world[pid][i], float) + np.asarray(world[pid][j], float)) / 2.0


def _d(a, b) -> float:
    return float(np.linalg.norm(np.asarray(a, float) - np.asarray(b, float)))


# ---------------------------------------------------------------- ① cup_sleeve

_CUP_N = 12
CUP_DEFAULTS = {"side_b": 16.0, "side_t": 18.5, "H": 60.0, "hem_d": 5.0,
                "glue_w": 8.0, "board_t": 0.42}


def _cup_geom(sb: float, st: float, h: float) -> dict:
    """恢复锥 (杯套上宽下窄 → 锥顶在下) → 扇形展开参数."""
    n = _CUP_N
    a_b = sb / (2.0 * math.tan(math.pi / n))
    a_t = st / (2.0 * math.tan(math.pi / n))
    Rb = sb / (2.0 * math.sin(math.pi / n))
    Rt = st / (2.0 * math.sin(math.pi / n))
    if st <= sb:
        raise ValueError("杯套须 side_t > side_b (杯口宽于杯底)")
    H_p = h * a_b / (a_b - a_t)                 # 锥顶 z (负 → 锥顶在底面之下)
    lb = math.hypot(H_p, Rb)                    # 锥顶→底角
    Le = math.hypot(h, Rb - Rt)                 # 侧棱长
    lt = lb + Le                                # 锥顶→顶角 (顶环比底环更远)
    beta = 2.0 * math.asin(sb / (2.0 * lb))     # 每墙面顶角
    return {"a_b": a_b, "a_t": a_t, "Rb": Rb, "Rt": Rt, "H_p": H_p,
            "lb": lb, "lt": lt, "Le": Le, "beta": beta}


def _cup_refs(sb, st, h):
    g = _cup_geom(sb, st, h)
    omega = lambda k: -math.pi / 2 - math.pi / _CUP_N + 2.0 * math.pi * k / _CUP_N
    vb = [np.array([g["Rb"] * math.cos(omega(k)), g["Rb"] * math.sin(omega(k)), 0.0])
          for k in range(_CUP_N)]
    vt = [np.array([g["Rt"] * math.cos(omega(k)), g["Rt"] * math.sin(omega(k)), float(h)])
          for k in range(_CUP_N)]
    apex = np.array([0.0, 0.0, g["H_p"]])
    return g, vb, vt, apex


def _cup_root_frame(vb0, vb1, vt0, apex, u0, u1):
    """net 射线基 (u0,u1,u0×u1) → 墙0 面内锥顶射线基 (odd_family 同款三元组对齐)."""
    dL = _unit(vb0 - apex)
    dR = _unit(vb1 - apex)
    u03 = np.array([float(u0[0]), float(u0[1]), 0.0])
    u13 = np.array([float(u1[0]), float(u1[1]), 0.0])
    U = np.column_stack([u03, u13, np.cross(u03, u13)])
    D = np.column_stack([dL, dR, np.cross(dL, dR)])
    return D @ np.linalg.inv(U), np.asarray(apex, float)


def _build_cup(p):
    n = _CUP_N
    sb, st, h = float(p["side_b"]), float(p["side_t"]), float(p["H"])
    gw, hd = float(p["glue_w"]), float(p["hem_d"])
    g, vb, vt, apex = _cup_refs(sb, st, h)
    beta, lb, lt = g["beta"], g["lb"], g["lt"]
    phi = lambda k: -math.pi / 2 - beta / 2.0 + k * beta
    u = lambda k: np.array([math.cos(phi(k)), math.sin(phi(k))])
    B = [lb * u(k) for k in range(n + 1)]
    T = [lt * u(k) for k in range(n + 1)]

    panels = [{"id": f"w{k}", "role": "wall",
               "polygon_2d": _pts([B[k], B[k + 1], T[k + 1], T[k]])} for k in range(n)]
    # 双端卡槽唇: 顶/底弦外缘各 n 片梯形缘折 (net 沿弦中径向内凹深 hem_d)
    for k in range(n):
        um = u(k + 0.5)
        panels.append({"id": f"hemT{k}", "role": "flap",
                       "polygon_2d": _pts([T[k], T[k + 1],
                                           T[k + 1] + hd * um, T[k] + hd * um])})
        panels.append({"id": f"hemB{k}", "role": "flap",
                       "polygon_2d": _pts([B[k], B[k + 1],
                                           B[k + 1] + hd * um, B[k] + hd * um])})
    # 搭接粘缝: 附末墙自由侧棱, 180° 反贴 w0 内侧
    q = np.array([-math.sin(phi(n)), math.cos(phi(n))])
    panels.append({"id": "glue", "role": "glue",
                   "polygon_2d": _pts([T[n], B[n], B[n] + gw * q, T[n] + gw * q])})

    edges = []
    for k in range(n - 1):
        i1, i2 = (k + 1) % n, (k + 2) % n
        cen = (vb[i1] + vb[i2] + vt[i2] + vt[i1]) / 4.0
        tdir = _unit(_proj_perp(cen - (vb[i1] + vt[i1]) / 2.0, vb[i1] - vt[i1]))
        edges.append(_fold(f"e_w{k}", T[k + 1], B[k + 1], f"w{k}", f"w{k+1}", tdir))
    axis0 = vb[0] - vt[0]
    in_w0 = (vb[0] + vb[1] + vt[1] + vt[0]) / 4.0 - (vb[0] + vt[0]) / 2.0
    edges.append(_fold("e_glue", T[n], B[n], f"w{n-1}", "glue",
                       _unit(_proj_perp(in_w0, axis0)), "MOUNTAIN"))
    # 缘折: tdir = 弦中点水平内向 (落 z=h / z=0 平面, 卡槽唇环)
    for k in range(n):
        rim_t = (vt[k] + vt[(k + 1) % n]) / 2.0
        rim_b = (vb[k] + vb[(k + 1) % n]) / 2.0
        edges.append(_fold(f"e_hemT{k}", T[k], T[k + 1], f"w{k}", f"hemT{k}",
                           _unit(-np.array([rim_t[0], rim_t[1], 0.0])), "MOUNTAIN"))
        edges.append(_fold(f"e_hemB{k}", B[k], B[k + 1], f"w{k}", f"hemB{k}",
                           _unit(-np.array([rim_b[0], rim_b[1], 0.0])), "MOUNTAIN"))

    R0, off0 = _cup_root_frame(vb[0], vb[1], vt[0], apex, u(0), u(1))
    ir = {
        "meta": {"ir_version": "0.1", "units": "mm",
                 "generator": "photo_dieline.parametric.sundry_family 0.1",
                 "notes": f"杯套: {_CUP_N} 边形近似圆台侧带 (上宽下窄, 每片墙面顶角 "
                          f"{math.degrees(beta):.3f}°), 顶/底缘各 {_CUP_N} 片缘折入 "
                          f"{hd:g}mm 内弯成环 → 双端卡槽唇 (插套槽口), 搭接粘缝贴 w0",
                 "root_panel": "w0",
                 "root_frame": {"R": [[float(x) for x in row] for row in R0],
                                "off": [float(x) for x in off0]}},
        "package": {"type": "cup_sleeve",
                    "template": {"id": "cup_sleeve", "version": "0.1"},
                    "params": {}, "photo": None},
        "panels": panels, "edges": edges,
        "features": _features("glue"),
    }
    return ir


def _cup_closure(ir, world) -> dict:
    p = ir.package["params"]
    sb, st, h = float(p["side_b"]), float(p["side_t"]), float(p["H"])
    n = _CUP_N
    _, vb, vt, _ = _cup_refs(sb, st, h)
    res: dict[str, float] = {}
    wn = world[f"w{n-1}"]
    res["seam.far_edge"] = float(max(np.linalg.norm(wn[1] - vb[0]),
                                     np.linalg.norm(wn[2] - vt[0])))
    e0 = _unit(vb[1] - vb[0])
    up0 = _unit(vt[0] - vb[0])
    nrm0 = np.cross(e0, up0)
    res["glue.flush_w0"] = float(np.max(np.abs(
        (np.asarray(world["glue"]) - vb[0]) @ nrm0)))
    for k in range(n):
        for tag, ring, z in (("hemT", vt, h), ("hemB", vb, 0.0)):
            pid = f"{tag}{k}"
            rim = (ring[k] + ring[(k + 1) % n]) / 2.0
            nh = _unit(np.array([rim[0], rim[1], 0.0]))
            expect = rim - nh * float(p["hem_d"])
            res[f"{pid}.far"] = float(np.linalg.norm(
                np.mean(np.asarray(world[pid][2:4]), axis=0) - expect))
    return res


def _cup_analytic(params) -> dict:
    sb, st, h = float(params["side_b"]), float(params["side_t"]), float(params["H"])
    _, vb, vt, _ = _cup_refs(sb, st, h)
    xs = [v[0] for v in vb] + [v[0] for v in vt]
    ys = [v[1] for v in vb] + [v[1] for v in vt]
    return {"W": float(max(xs) - min(xs)), "D": float(max(ys) - min(ys)), "H": float(h)}


def _cup_overlap() -> set:
    n = _CUP_N
    s = {frozenset({"glue", "w0"}), frozenset({"w0", f"w{n-1}"})}
    # 卡槽唇环与邻墙/远墙斜面仅缘线接触, 检查器投影保守 → 契约放行
    for k in range(n):
        for tag in ("hemT", "hemB"):
            for j in range(n):
                if j != k:
                    s.add(frozenset({f"{tag}{k}", f"w{j}"}))
            s.add(frozenset({f"{tag}{k}", "glue"}))
    return s


# ---------------------------------------------------------------- ② egg_tray_2x4

EGG_DEFAULTS = {"W": 160.0, "D": 80.0, "H": 28.0, "board_t": 0.45}


def _build_egg(p):
    W, D, H = float(p["W"]), float(p["D"]), float(p["H"])
    xs4 = (W / 4.0, W / 2.0, 3.0 * W / 4.0)
    floor = _rect_split("floor", "wall", 0.0, 0.0, W, D, splits_y=(D / 2.0,))
    waf = _rect_split("wAf", "wall", 0.0, 0.0, W, H, splits_x=xs4)
    wab = _rect_split("wAb", "wall", 0.0, D, W, D + H, splits_x=xs4)
    wal = _rect("wAl", "wall", -H, 0.0, 0.0, D)
    war = _rect("wAr", "wall", W, 0.0, W + H, D)
    dvm = _rect("dvm", "wall", 0.0, D / 2.0, W, D / 2.0 + H)
    panels = [floor, waf, wab, wal, war, dvm]
    for j, xj in enumerate(xs4, start=1):
        # 前后墙 score 折链横隔半片: 铰链 = 墙内竖直score线, 折出成正交横隔,
        # 净图与母墙共位 (score 翻出, 成型后无共面重叠)
        panels.append(_rect(f"cs{j}", "wall", xj, 0.0, xj + D / 2.0, H))
        panels.append(_rect(f"cn{j}", "wall", xj, D, xj + D / 2.0, D + H))
    edges = [
        _fold("e_wf", (0, 0), (W, 0), "floor", "wAf", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_wb", (0, D), (W, D), "floor", "wAb", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_wl", (0, 0), (0, D), "floor", "wAl", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_wr", (W, 0), (W, D), "floor", "wAr", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_dvm", (0, D / 2.0), (W, D / 2.0), "floor", "dvm",
              (0.0, 0.0, 1.0), "MOUNTAIN"),
    ]
    for j, xj in enumerate(xs4, start=1):
        edges.append(_fold(f"e_cs{j}", (xj, 0), (xj, H), "wAf", f"cs{j}",
                           (0.0, 1.0, 0.0), "MOUNTAIN"))
        edges.append(_fold(f"e_cn{j}", (xj, D), (xj, D + H), "wAb", f"cn{j}",
                           (0.0, -1.0, 0.0), "MOUNTAIN"))
    ir = {
        "meta": {"ir_version": "0.1", "units": "mm",
                 "generator": "photo_dieline.parametric.sundry_family 0.1",
                 "notes": f"蛋托 2×4: 共享底盘 + 四周围墙 (前/后墙带 3 条竖 score 折链 "
                          f"翻出横隔半片) + 中隔板 (底盘中线铰链) — 8 格, 横隔端缘于 "
                          f"y=D/2 中线互抵并贴中隔板, 格口 {W / 4:.0f}×{D / 2:.0f}×{H:g}",
                 "root_panel": "floor",
                 "root_frame": {"R": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0],
                                      [0.0, 0.0, 1.0]], "off": [0.0, 0.0, 0.0]}},
        "package": {"type": "egg_tray_2x4",
                    "template": {"id": "egg_tray_2x4", "version": "0.1"},
                    "params": {}, "photo": None},
        "panels": panels, "edges": edges,
        "features": _features(),
    }
    return ir


def _egg_closure(ir, world) -> dict:
    W, D, H = ir.param("W"), ir.param("D"), ir.param("H")
    res: dict[str, float] = {}
    f, b, l, r = world["wAf"], world["wAb"], world["wAl"], world["wAr"]
    # wAf/wAb 环序旋转后自 (W,·) 起: [0]=(W,·,0) [1]=(W,·,H) [5]=(0,·,H) [6]=(0,·,0)
    res["corner.fr"] = float(max(_d(f[0], r[0]), _d(f[1], r[1])))
    res["corner.rb"] = float(max(_d(r[2], b[1]), _d(r[3], b[0])))
    res["corner.bl"] = float(max(_d(b[5], l[3]), _d(b[6], l[2])))
    res["corner.fl"] = float(max(_d(f[6], l[1]), _d(f[5], l[0])))
    dv = world["dvm"]
    res["dvm.top_zH"] = float(abs(float(np.mean(dv[2:4], axis=0)[2]) - H))
    res["dvm.end_flush"] = float(abs(float(np.mean(dv[[0, 3]], axis=0)[0])))
    for j in (1, 2, 3):
        cs, cn = world[f"cs{j}"], world[f"cn{j}"]
        res[f"butt.{j}"] = float(_d(np.mean(cs[1:3], axis=0), np.mean(cn[1:3], axis=0)))
        seat = max(abs(float(np.mean(cs[2:4], axis=0)[2]) - H),
                   abs(float(np.mean(cs[1:3], axis=0)[1]) - D / 2.0),
                   abs(float(np.mean(cn[2:4], axis=0)[2]) - H),
                   abs(float(np.mean(cn[1:3], axis=0)[1]) - D / 2.0))
        res[f"seat.{j}"] = float(seat)
    return res


def _egg_analytic(params) -> dict:
    return {"W": float(params["W"]), "D": float(params["D"]), "H": float(params["H"])}


def _egg_overlap() -> set:
    s = set()
    for j in (1, 2, 3):
        # 横隔底缘坐于底盘 / 端缘抵中隔板 (真实线接触, 投影保守放行)
        s.add(frozenset({f"cs{j}", "floor"}))
        s.add(frozenset({f"cn{j}", "floor"}))
        s.add(frozenset({f"cs{j}", "dvm"}))
        s.add(frozenset({f"cn{j}", "dvm"}))
    return s


# ---------------------------------------------------------------- ③ handle_box

HB_DEFAULTS = {"W": 90.0, "D": 55.0, "H": 130.0, "glue_w": 12.0, "board_t": 0.45,
               "tuck_d": 12.0, "dust_r": 0.5, "ins": 12.0,
               "tab_h": 30.0, "slot_w": 16.0, "slot_d": 11.0}


def _hb_chain(p, W, D, H):
    """[glue][w0..w3] 墙链 (box_essentials 同款): 返回 (panels, edges, xs)."""
    gw = float(p["glue_w"])
    x1, x2, x3, x4, x5 = gw, gw + W, gw + W + D, gw + 2 * W + D, gw + 2 * W + 2 * D
    panels = [_rect("glue", "glue", 0.0, 0.0, x1, H),
              _rect("w0", "wall", x1, 0.0, x2, H),
              _rect("w1", "wall", x2, 0.0, x3, H),
              _rect("w2", "wall", x3, 0.0, x4, H),
              _rect("w3", "wall", x4, 0.0, x5, H)]
    edges = [_fold("e_g", (x1, 0), (x1, H), "w0", "glue", (0.0, 1.0, 0.0), "MOUNTAIN"),
             _fold("e_w01", (x2, 0), (x2, H), "w0", "w1", (0.0, 1.0, 0.0)),
             _fold("e_w12", (x3, 0), (x3, H), "w1", "w2", (-1.0, 0.0, 0.0)),
             _fold("e_w23", (x4, 0), (x4, H), "w2", "w3", (0.0, -1.0, 0.0))]
    return panels, edges, (x1, x2, x3, x4, x5)


def _hb_bottom(p, xs, W, D):
    x1, x2, x3, x4, x5 = xs
    dm, dn = D / 2.0, W / 2.0
    panels = [_rect("b0", "flap", x1, -dm, x2, 0.0),
              _rect("b1", "flap", x2, -dn, x3, 0.0),
              _rect("b2", "flap", x3, -dm, x4, 0.0),
              _rect("b3", "flap", x4, -dn, x5, 0.0)]
    edges = [_fold("e_b0", (x1, 0), (x2, 0), "w0", "b0", (0.0, 1.0, 0.0), "MOUNTAIN"),
             _fold("e_b1", (x2, 0), (x3, 0), "w1", "b1", (-1.0, 0.0, 0.0), "MOUNTAIN"),
             _fold("e_b2", (x3, 0), (x4, 0), "w2", "b2", (0.0, -1.0, 0.0), "MOUNTAIN"),
             _fold("e_b3", (x4, 0), (x5, 0), "w3", "b3", (1.0, 0.0, 0.0), "MOUNTAIN")]
    return panels, edges


def _hb_dust(p, xs, W, H):
    x1, x2, x3, x4, x5 = xs
    dd = float(p["dust_r"]) * W
    panels = [_rect("t1", "flap", x2, H, x3, H + dd),
              _rect("t3", "flap", x4, H, x5, H + dd)]
    edges = [_fold("e_t1", (x2, H), (x3, H), "w1", "t1", (-1.0, 0.0, 0.0), "MOUNTAIN"),
             _fold("e_t3", (x4, H), (x5, H), "w3", "t3", (1.0, 0.0, 0.0), "MOUNTAIN")]
    return panels, edges


def _build_handle(p):
    W, D, H = float(p["W"]), float(p["D"]), float(p["H"])
    td, ins = float(p["tuck_d"]), float(p["ins"])
    th, sw, sd = float(p["tab_h"]), float(p["slot_w"]), float(p["slot_d"])
    panels, edges, xs = _hb_chain(p, W, D, H)
    x1, x2, x3, x4, x5 = xs
    bp, be = _hb_bottom(p, xs, W, D)
    dp, de = _hb_dust(p, xs, W, H)
    # 顶插盖: 主盖深 D 自背墙 w2, 远缘插舌入前墙内面
    lid = _poly("t2", "flap", [(x3, H), (x4, H), (x4, H + D),
                               (x4 - ins, H + D), (x3 + ins, H + D), (x3, H + D)])
    tongue = _rect("tongue", "flap", x3 + ins, H + D, x4 - ins, H + D + td)
    edges += [_fold("e_t2", (x3, H), (x4, H), "w2", "t2", (0.0, -1.0, 0.0), "MOUNTAIN"),
              _fold("e_tongue", (x3 + ins, H + D), (x4 - ins, H + D),
                    "t2", "tongue", (0.0, 0.0, -1.0), "MOUNTAIN")]
    # 提手孔板: 前墙 w0 顶缘直立延伸, 顶缘中央 U 形凹口为提手孔 (hanger 凹口模式)
    xc, hs = x1 + W / 2.0, sw / 2.0
    tab = _poly("tab", "flap",
                [(x1, H), (x2, H), (x2, H + th),
                 (xc + hs, H + th), (xc + hs, H + th - sd),
                 (xc - hs, H + th - sd), (xc - hs, H + th), (x1, H + th)])
    edges.append(_fold("e_tab", (x1, H), (x2, H), "w0", "tab", (0.0, 0.0, 1.0),
                       "MOUNTAIN"))
    notes = (f"handle_box: 4 墙链 + 底全叠封 + 2 防尘翼 + 顶插盖 (主盖深 D 自背墙, "
             f"插舌深 {td:g} 入前墙内面) + 前墙顶缘提手孔板 (高 {th:g}, 顶缘 U 形凹口 "
             f"{sw:g}×{sd:g} 为提手孔, 凹口多边形)")
    ir = {
        "meta": {"ir_version": "0.1", "units": "mm",
                 "generator": "photo_dieline.parametric.sundry_family 0.1",
                 "notes": notes,
                 "root_panel": "w0",
                 "root_frame": {"R": [[1.0, 0.0, 0.0], [0.0, 0.0, 0.0],
                                      [0.0, 1.0, 0.0]],
                                "off": [-float(p["glue_w"]), 0.0, 0.0]}},
        "package": {"type": "handle_box",
                    "template": {"id": "handle_box", "version": "0.1"},
                    "params": {}, "photo": None},
        "panels": panels + bp + dp + [lid, tongue, tab],
        "edges": edges + be + de,
        "features": _features("glue"),
    }
    return ir


def _handle_closure(ir, world) -> dict:
    W, D, H = ir.param("W"), ir.param("D"), ir.param("H")
    td = ir.param("tuck_d")
    res: dict[str, float] = {}
    res["ring.w3_w0"] = _d(_fm(world, "w3", 1, 2), _fm(world, "w0", 0, 3))
    res["glue.seat"] = abs(float(np.mean(np.asarray(world["glue"]), axis=0)[0]))
    res["b.major.meet"] = _d(_fm(world, "b0", 0, 1), _fm(world, "b2", 0, 1))
    res["b.minor.meet"] = _d(_fm(world, "b1", 0, 1), _fm(world, "b3", 0, 1))
    res["b.major.z0"] = max(abs(float(_fm(world, "b0", 0, 1)[2])),
                            abs(float(_fm(world, "b2", 0, 1)[2])))
    res["dust.meet"] = _d(_fm(world, "t1", 2, 3), _fm(world, "t3", 2, 3))
    res["dust.zH"] = max(abs(float(_fm(world, "t1", 2, 3)[2]) - H),
                         abs(float(_fm(world, "t3", 2, 3)[2]) - H))
    lid_far = _fm(world, "t2", 2, 3)
    res["lid.far_y"] = abs(float(lid_far[1]))
    res["lid.zH"] = abs(float(lid_far[2]) - H)
    tm = np.mean(np.asarray(world["tongue"]), axis=0)
    res["tongue.flush"] = abs(float(tm[1]))
    res["tongue.depth"] = abs(float(_fm(world, "tongue", 2, 3)[2]) - (H - td))
    tb = np.asarray(world["tab"], float)
    th, sd = ir.param("tab_h"), ir.param("slot_d")
    res["tab.plane_y0"] = abs(float(np.mean(tb[:, 1])))
    res["tab.top_z"] = abs(float(tb[:, 2].max()) - (H + th))
    res["tab.slot_bottom"] = abs(float((tb[4] + tb[5])[2] / 2.0) - (H + th - sd))
    res["tab.slot_center"] = abs(float((tb[3][0] + tb[6][0]) / 2.0) - W / 2.0)
    return res


def _handle_analytic(params) -> dict:
    return {"W": float(params["W"]), "D": float(params["D"]), "H": float(params["H"])}


def _handle_overlap() -> set:
    return {frozenset({"glue", "w3"}), frozenset({"tongue", "w0"}),
            frozenset({"tab", "tongue"})}  # tab/舌同面前后段, 零厚模型缘触


# ---------------------------------------------------------------- ④ display_counter

DC_DEFAULTS = {"W": 120.0, "D": 60.0, "Hf": 40.0, "H": 100.0, "board_t": 0.45}


def _build_display(p):
    W, D, Hf, H = float(p["W"]), float(p["D"]), float(p["Hf"]), float(p["H"])
    Ls = D * math.sqrt(2.0)  # 45° 托板净深
    panels = [
        _rect("floor", "wall", 0.0, 0.0, W, D),
        _rect("waf", "wall", 0.0, -Hf, W, 0.0),
        _rect("wab", "wall", 0.0, D, W, D + H),
        _poly("wal", "wall", [(0.0, 0.0), (0.0, D), (-H, D), (-Hf, 0.0)]),
        _poly("war", "wall", [(W, 0.0), (W + Hf, 0.0), (W + H, D), (W, D)]),
        _rect("slant", "slope", 0.0, -Hf - Ls, W, -Hf),
    ]
    s2 = math.sqrt(2.0) / 2.0
    edges = [
        _fold("e_wf", (0, 0), (W, 0), "floor", "waf", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_wb", (0, D), (W, D), "floor", "wab", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_wl", (0, 0), (0, D), "floor", "wal", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_wr", (W, 0), (W, D), "floor", "war", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_sl", (0, -Hf), (W, -Hf), "waf", "slant", (0.0, s2, s2), "MOUNTAIN"),
    ]
    ir = {
        "meta": {"ir_version": "0.1", "units": "mm",
                 "generator": "photo_dieline.parametric.sundry_family 0.1",
                 "notes": f"陈列台: 共享底盘 + 低前板 {Hf:g} + 高背板 {H:g} + 两侧斜顶板 "
                          f"(前 {Hf:g} → 后 {H:g} 斜肩) + 45° 斜前托板 (净深 "
                          f"{Ls:.3f}mm, 远缘精确抵背板顶缘, 锁定 H=Hf+D)",
                 "root_panel": "floor",
                 "root_frame": {"R": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0],
                                      [0.0, 0.0, 1.0]], "off": [0.0, 0.0, 0.0]}},
        "package": {"type": "display_counter",
                    "template": {"id": "display_counter", "version": "0.1"},
                    "params": {}, "photo": None},
        "panels": panels, "edges": edges,
        "features": _features(),
    }
    return ir


def _display_closure(ir, world) -> dict:
    res: dict[str, float] = {}
    f, b, l, r, sl = (world["waf"], world["wab"], world["wal"], world["war"],
                      world["slant"])
    res["corner.fl"] = float(max(_d(f[3], l[0]), _d(f[0], l[3])))
    res["corner.fr"] = float(max(_d(f[2], r[0]), _d(f[1], r[1])))
    res["corner.br"] = float(max(_d(r[2], b[2]), _d(r[3], b[1])))
    res["corner.bl"] = float(max(_d(l[2], b[3]), _d(l[1], b[0])))
    res["slant.meets_back_top"] = float(max(_d(sl[0], b[3]), _d(sl[1], b[2])))
    res["slant.side_seats"] = float(max(_d(sl[2], r[1]), _d(sl[3], l[3])))
    return res


def _display_analytic(params) -> dict:
    return {"W": float(params["W"]), "D": float(params["D"]), "H": float(params["H"])}


def _display_overlap() -> set:
    # 托板远缘抵背板顶缘 / 侧缘抵侧板斜肩 (线接触, 检查器投影保守放行)
    return {frozenset({"slant", "wab"}), frozenset({"slant", "wal"}),
            frozenset({"slant", "war"})}


# ---------------------------------------------------------------- ⑤ envelope_square

ENV_DEFAULTS = {"S": 140.0, "flap_d": 70.0, "board_t": 0.42}


def _build_env(p):
    S, fd = float(p["S"]), float(p["flap_d"])
    dt = S - fd  # 三角翻盖净深: 盖尖精确抵底翼远缘中线
    panels = [
        _rect("body", "wall", 0.0, 0.0, S, S),
        _rect("flapL", "flap", -fd, 0.0, 0.0, S),
        _rect("flapR", "flap", S, 0.0, S + fd, S),
        _rect("flapB", "flap", 0.0, -fd, S, 0.0),
        _poly("flapT", "flap", [(0.0, S), (S, S), (S / 2.0, S + dt)]),
    ]
    edges = [
        _fold("e_fl", (0, 0), (0, S), "body", "flapL", (1.0, 0.0, 0.0), "MOUNTAIN"),
        _fold("e_fr", (S, 0), (S, S), "body", "flapR", (-1.0, 0.0, 0.0), "MOUNTAIN"),
        _fold("e_fb", (0, 0), (S, 0), "body", "flapB", (0.0, 1.0, 0.0), "MOUNTAIN"),
        _fold("e_ft", (0, S), (S, S), "body", "flapT", (0.0, -1.0, 0.0), "MOUNTAIN"),
    ]
    ir = {
        "meta": {"ir_version": "0.1", "units": "mm",
                 "generator": "photo_dieline.parametric.sundry_family 0.1",
                 "notes": f"方信封: 正方形背面 {S:g}×{S:g} + 四边折翼风车顺序折合 "
                          f"(左右底翼深 {fd:g} → 远缘抵中线, 三角翻盖净深 {dt:g} → "
                          "盖尖精确抵底翼远缘中线), 全片 180° 平折共面封闭",
                 "root_panel": "body",
                 "root_frame": {"R": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0],
                                      [0.0, 0.0, 1.0]], "off": [0.0, 0.0, 0.0]}},
        "package": {"type": "envelope_square",
                    "template": {"id": "envelope_square", "version": "0.1"},
                    "params": {}, "photo": None},
        "panels": panels, "edges": edges,
        "features": _features(),
    }
    return ir


def _env_closure(ir, world) -> dict:
    S, fd = ir.param("S"), ir.param("flap_d")
    res: dict[str, float] = {}
    res["flapL.far_x"] = abs(float(np.mean(np.asarray(world["flapL"][[0, 3]]), axis=0)[0]) - fd)
    res["flapR.far_x"] = abs(float(np.mean(np.asarray(world["flapR"][[1, 2]]), axis=0)[0]) - (S - fd))
    res["flapB.far_y"] = abs(float(np.mean(np.asarray(world["flapB"][[0, 1]]), axis=0)[1]) - fd)
    res["flapT.apex_meets_bot_far"] = float(
        np.linalg.norm(world["flapT"][2] - np.array([S / 2.0, fd, 0.0])))
    for pid in ("flapL", "flapR", "flapB", "flapT"):
        res[f"{pid}.flush_z0"] = float(abs(float(np.mean(np.asarray(world[pid])[:, 2]))))
    return res


def _env_analytic(params) -> dict:
    return {"W": float(params["S"]), "D": float(params["S"]), "H": 0.0}


def _env_overlap() -> set:
    """封闭信封全片平折共面: 5 片两两共面叠合 → 全对放行 (真实工艺契约)."""
    ids = ["body", "flapL", "flapR", "flapB", "flapT"]
    return {frozenset({ids[i], ids[j]})
            for i in range(len(ids)) for j in range(i + 1, len(ids))}


# ---------------------------------------------------------------- ⑥ clamp_shell

CL_DEFAULTS = {"W": 90.0, "D": 60.0, "H": 25.0, "lip_d": 10.0, "board_t": 0.45}


def _build_clamp(p):
    W, D, H, lip = float(p["W"]), float(p["D"]), float(p["H"]), float(p["lip_d"])
    y0, y1, y2 = D, D + H, D + H + D  # 半壳 A 底盘 / 背墙(铰链) / 半壳 B 底盘
    panels = [
        _rect("bA", "wall", 0.0, 0.0, W, y0),
        _rect("wAf", "wall", 0.0, -H, W, 0.0),
        _rect("wAl", "wall", -H, 0.0, 0.0, y0),
        _rect("wAr", "wall", W, 0.0, W + H, y0),
        _rect("wAb", "wall", 0.0, y0, W, y1),          # A 背墙 = 铰链墙
        _rect("bB", "wall", 0.0, y1, W, y2),           # 自 wAb 顶缘翻下的半壳 B 底盘
        _rect("wBl", "wall", -H, y1, 0.0, y2),
        _rect("wBr", "wall", W, y1, W + H, y2),
        _rect("tA", "flap", 0.0, -H - lip, W, -H),     # A 前墙顶缘外折唇
        _rect("tB", "flap", 0.0, y2, W, y2 + lip),     # B 底盘前缘外折唇
    ]
    edges = [
        _fold("e_wf", (0, 0), (W, 0), "bA", "wAf", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_wl", (0, 0), (0, y0), "bA", "wAl", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_wr", (W, 0), (W, y0), "bA", "wAr", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_wb", (0, y0), (W, y0), "bA", "wAb", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_bB", (0, y1), (W, y1), "wAb", "bB", (0.0, -1.0, 0.0), "MOUNTAIN"),
        _fold("e_wBl", (0, y1), (0, y2), "bB", "wBl", (0.0, 0.0, -1.0), "MOUNTAIN"),
        _fold("e_wBr", (W, y1), (W, y2), "bB", "wBr", (0.0, 0.0, -1.0), "MOUNTAIN"),
        _fold("e_tA", (0, -H), (W, -H), "wAf", "tA", (0.0, -1.0, 0.0), "MOUNTAIN"),
        _fold("e_tB", (0, y2), (W, y2), "bB", "tB", (0.0, -1.0, 0.0), "MOUNTAIN"),
    ]
    ir = {
        "meta": {"ir_version": "0.1", "units": "mm",
                 "generator": "photo_dieline.parametric.sundry_family 0.1",
                 "notes": f"扣夹盒: 半壳 A (底盘+前/左/右/背墙 {H:g}) 与半壳 B (底盘+"
                          f"左右墙) 经共用背墙 wAb 顶缘铰链相连, 扣合后 B 贴合 A 口缘 "
                          f"(侧壁共面对位) — 对侧前缘扣舌互扣: 双唇外折深 {lip:g} 于口缘 "
                          "平面远缘相抵 (平面互扣)",
                 "root_panel": "bA",
                 "root_frame": {"R": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0],
                                      [0.0, 0.0, 1.0]], "off": [0.0, 0.0, 0.0]}},
        "package": {"type": "clamp_shell",
                    "template": {"id": "clamp_shell", "version": "0.1"},
                    "params": {}, "photo": None},
        "panels": panels, "edges": edges,
        "features": _features(),
    }
    return ir


def _clamp_closure(ir, world) -> dict:
    W, D, H, lip = ir.param("W"), ir.param("D"), ir.param("H"), ir.param("lip_d")
    res: dict[str, float] = {}
    f, b, l, r = world["wAf"], world["wAb"], world["wAl"], world["wAr"]
    bl, br, bB, tA, tB = world["wBl"], world["wBr"], world["bB"], world["tA"], world["tB"]
    res["corner.fa_r"] = float(max(_d(f[2], r[0]), _d(f[1], r[1])))
    res["corner.fa_l"] = float(max(_d(f[3], l[1]), _d(f[0], l[0])))
    res["corner.ab_r"] = float(max(_d(r[2], b[2]), _d(r[3], b[1])))
    res["corner.ab_l"] = float(max(_d(l[3], b[3]), _d(l[2], b[0])))
    res["lid.fit_front"] = float(max(_d(bB[2], f[1]), _d(bB[3], f[0])))
    res["lid.zRim"] = float(abs(float(np.mean(bB[:, 2])) - H))
    res["side.seat_l"] = float(max(_d(bl[0], l[2]), _d(bl[1], l[3]),
                                   _d(bl[2], l[0]), _d(bl[3], l[1])))
    res["side.seat_r"] = float(max(_d(br[0], r[2]), _d(br[1], r[3]),
                                   _d(br[2], r[0]), _d(br[3], r[1])))
    res["snap.far_meet"] = float(_d(np.mean(tA[0:2], axis=0), np.mean(tB[2:4], axis=0)))
    res["snap.zRim"] = float(max(abs(float(np.mean(tA[0:2], axis=0)[2]) - H),
                                 abs(float(np.mean(tB[2:4], axis=0)[2]) - H)))
    res["snap.reach"] = float(abs(float(np.mean(tA[0:2], axis=0)[1])) - lip)
    return res


def _clamp_analytic(params) -> dict:
    return {"W": float(params["W"]), "D": float(params["D"]), "H": float(params["H"])}


def _clamp_overlap() -> set:
    """扣合态: B 侧壁与 A 侧壁共面贴合, 双扣舌口缘平面互扣重叠 (零厚层压契约)."""
    return {frozenset({"wBf", "wAf"}), frozenset({"wBl", "wAl"}),
            frozenset({"wBr", "wAr"}), frozenset({"tA", "tB"}),
            frozenset({"tA", "bB"}), frozenset({"tB", "wAf"})}


# ------------------------------------------------------------ 注册与分发

for _cid in ("cup_sleeve", "egg_tray_2x4", "handle_box", "display_counter",
             "envelope_square", "clamp_shell"):
    _base.register(_cid, "sundry_family")

# 模块契约: 多类异构模块 → PARAM_ORDER = 全家族键并集; 家族不适用键置 0.
PARAM_ORDER = ["W", "D", "H", "Hf", "S", "side_b", "side_t", "hem_d", "glue_w",
               "board_t", "tuck_d", "dust_r", "ins", "tab_h", "slot_w", "slot_d",
               "flap_d", "lip_d"]
DEFAULTS = {"W": 0.0, "D": 0.0, "H": 0.0, "Hf": 0.0, "S": 0.0, "side_b": 0.0,
            "side_t": 0.0, "hem_d": 0.0, "glue_w": 0.0, "board_t": 0.42,
            "tuck_d": 0.0, "dust_r": 0.0, "ins": 0.0, "tab_h": 0.0, "slot_w": 0.0,
            "slot_d": 0.0, "flap_d": 0.0, "lip_d": 0.0}

_CLASS_PARAMS = {
    "cup_sleeve": CUP_DEFAULTS,
    "egg_tray_2x4": EGG_DEFAULTS,
    "handle_box": HB_DEFAULTS,
    "display_counter": DC_DEFAULTS,
    "envelope_square": ENV_DEFAULTS,
    "clamp_shell": CL_DEFAULTS}


def class_params(cls_id: str) -> dict:
    """类ID → 该类全键参数表 (批量 build_ir 判型与取值的唯一权威)."""
    if cls_id not in _CLASS_PARAMS:
        raise KeyError(f"未知类ID: {cls_id}")
    p = {k: 0.0 for k in PARAM_ORDER}
    p.update(_CLASS_PARAMS[cls_id])
    return p


def _family_of(p: dict) -> str:
    """合并参数 → 类ID (家族判别键 > 0 优先)."""
    if p.get("S", 0) > 0:
        return "envelope_square"
    if p.get("side_b", 0) > 0:
        return "cup_sleeve"
    if p.get("Hf", 0) > 0:
        return "display_counter"
    if p.get("lip_d", 0) > 0:
        return "clamp_shell"
    if p.get("tab_h", 0) > 0:
        return "handle_box"
    return "egg_tray_2x4"


def _pos(p, *keys):
    for k in keys:
        v = p.get(k)
        if v is None or not isinstance(v, (int, float)) or isinstance(v, bool) or v <= 0:
            raise ValueError(f"非法参数 {k}={v!r} (须正数)")


def validate_params(params: dict) -> None:
    fam = _family_of(params)
    _pos(params, "board_t")
    if fam == "cup_sleeve":
        _pos(params, "side_b", "side_t", "H", "hem_d", "glue_w")
        if params["side_t"] <= params["side_b"]:
            raise ValueError("杯套须 side_t > side_b (杯口宽于杯底)")
        g = _cup_geom(float(params["side_b"]), float(params["side_t"]), float(params["H"]))
        a_min = min(g["a_b"], g["a_t"])
        if float(params["hem_d"]) * 2.0 >= a_min:
            raise ValueError(f"卡槽唇深 hem_d 须小于最小端面 apothem 之半 ({a_min / 2:.2f})")
        if float(params["glue_w"]) > min(float(params["side_b"]), float(params["side_t"])):
            raise ValueError("杯套粘片宽 glue_w 不得超最窄端弦长")
    elif fam == "egg_tray_2x4":
        _pos(params, "W", "D", "H")
        if float(params["H"]) >= min(float(params["W"]), float(params["D"])):
            raise ValueError("格深 H 须小于最短格距")
    elif fam == "handle_box":
        _pos(params, "W", "D", "H", "glue_w", "tuck_d", "ins", "tab_h", "slot_w", "slot_d")
        if float(params["tuck_d"]) >= float(params["H"]):
            raise ValueError("插舌深 tuck_d 须小于盒高 H")
        if float(params["slot_d"]) >= float(params["tab_h"]):
            raise ValueError("提手孔深 slot_d 须小于孔板高 tab_h")
        if float(params["slot_w"]) >= float(params["W"]) - 2 * float(params["ins"]):
            raise ValueError("提手孔宽 slot_w 须窄于 (W - 2*ins)")
        if float(params["glue_w"]) >= min(float(params["W"]), float(params["D"])):
            raise ValueError("粘口 glue_w 须窄于最短墙")
        if float(params.get("dust_r", 0.5)) and not 0.0 < float(params["dust_r"]) <= 0.5:
            raise ValueError(f"非法参数 dust_r={params['dust_r']!r} (须 (0, 0.5])")
    elif fam == "display_counter":
        _pos(params, "W", "D", "Hf", "H")
        if abs(float(params["H"]) - float(params["Hf"]) - float(params["D"])) > 1e-6:
            raise ValueError("45° 托板远缘抵背板顶缘须 H = Hf + D (锁定条件)")
    elif fam == "envelope_square":
        _pos(params, "S", "flap_d")
        if float(params["flap_d"]) > float(params["S"]) / 2.0:
            raise ValueError("翼深 flap_d 须不超过 S/2 (远缘至中线)")
    else:
        _pos(params, "W", "D", "H", "lip_d")
        if float(params["lip_d"]) > float(params["H"]):
            raise ValueError("扣舌深 lip_d 须不超过墙高 H")


_BUILDERS = {
    "cup_sleeve": (_build_cup, _cup_analytic, _cup_closure, _cup_overlap),
    "egg_tray_2x4": (_build_egg, _egg_analytic, _egg_closure, _egg_overlap),
    "handle_box": (_build_handle, _handle_analytic, _handle_closure, _handle_overlap),
    "display_counter": (_build_display, _display_analytic, _display_closure,
                        _display_overlap),
    "envelope_square": (_build_env, _env_analytic, _env_closure, _env_overlap),
    "clamp_shell": (_build_clamp, _clamp_analytic, _clamp_closure, _clamp_overlap),
}


def build_ir(params: dict | None = None) -> dict:
    """契约入口; 类ID 由参数判型 (缺省 egg_tray_2x4)."""
    p = {**DEFAULTS, **(params or {})}
    cid = _family_of(p)
    ir = _BUILDERS[cid][0]({**DEFAULTS, **p})
    ir["package"]["params"] = {k: float(p[k]) for k in PARAM_ORDER}
    return ir


def analytic_bbox(params: dict) -> dict:
    p = {**DEFAULTS, **(params or {})}
    return _BUILDERS[_family_of(p)][1](p)


def closure_checks(ir, world) -> dict:
    return _BUILDERS[ir.package["template"]["id"]][2](ir, world)


def allowed_overlap() -> set:
    """全家族允许叠层并集 (G06 契约无 ir 入参 → 全家族并集, odd_family 先例)."""
    s: set = set()
    for hooks in _BUILDERS.values():
        s |= hooks[3]()
    return s


def solid_roles() -> tuple:
    return ("wall", "slope")


# ---------------------------------------------------------------- 负探针

def _rodrigues(v, axis, ang):
    a = _unit(axis)
    k = np.asarray(v, float)
    return (k * math.cos(ang) + np.cross(a, k) * math.sin(ang)
            + a * float(a @ k) * (1.0 - math.cos(ang)))


def _perturb(raw_ir, edge_id, axis, ang=0.35):
    """绕铰链轴把 tdir 转开 ang 弧度 (只有绕轴分量才改变折叠落位)."""
    import copy
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
    cid = ir.package["template"]["id"]
    if cid == "cup_sleeve":
        _, vb, vt, _ = _cup_refs(CUP_DEFAULTS["side_b"], CUP_DEFAULTS["side_t"],
                                 CUP_DEFAULTS["H"])
        return [("e_hemT0", _unit(vt[1] - vt[0])),
                ("e_w5", _unit(vb[6] - vt[6]))]
    if cid == "egg_tray_2x4":
        return [("e_dvm", (1.0, 0.0, 0.0)), ("e_cs2", (0.0, 0.0, 1.0))]
    if cid == "handle_box":
        return [("e_tab", (1.0, 0.0, 0.0)), ("e_t2", (1.0, 0.0, 0.0))]
    if cid == "display_counter":
        return [("e_sl", (1.0, 0.0, 0.0)), ("e_wf", (1.0, 0.0, 0.0))]
    if cid == "envelope_square":
        return [("e_ft", (1.0, 0.0, 0.0)), ("e_fl", (0.0, 1.0, 0.0))]
    return [("e_tA", (1.0, 0.0, 0.0)), ("e_bB", (1.0, 0.0, 0.0))]


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
