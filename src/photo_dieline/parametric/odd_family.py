"""odd_family: 异形家族 (7 族 8 类) — 棱台/锥管/直管/枕形/书封/楔形信封.

类ID:
  pyramid_frustum_n4/n6/n8  正 n 棱台: 梯形墙扇形链 + 顶盖 n 三角片内折
                            (折入深 = 上底 apothem, 各片远点互抵顶面中心)
  cone_wrap                 锥管: 16 边形近似, 梯形墙扇形链 + 搭接粘缝(贴 w0)
                            + 底 16 边形盘(附 w8 底弦, 盘心精确落轴)
  tube_glue                 直管: 16 边形近似圆管, 环形墙链 + 全重叠粘缝
                            (粘片宽度 = 墙宽, 远缘与 w0 远缘重合)
  pillow_box                枕形盒: 双大面 + 上下各 k 片折线近似半圆弧
                            + 四端折入(端片深 = D/2, 对片远缘中点重合)
  mailer_bookwrap           书封邮寄盒: 中板 + 两侧 90° 翻盖 + 插舌(180° 反贴)
  envelope_wedge            楔形信封: 大面 + 楔形侧翼 + 底折翼 + 三角翻盖
                            (翻盖深 = H - bot_d, 盖尖精确落在底翼远缘中点)

几何约定: 条带类根面板 net(x,y)→world(x,0,y); 扇形类根框架由 _root_frame_fan
数值求解 (net 射线基 → 墙面基); 多面体底/顶多边形中心在原点轴上, z 向上。
closure 全部为折叠后世界坐标残差 (远缘重合/抵中线/共面贴合), 无构造恒等量。
"""
from __future__ import annotations

import math

import numpy as np

from . import base as _base

# ---------------------------------------------------------------- 公共工具


def _unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    if n < 1e-12:
        raise ValueError("零向量")
    return np.asarray(v, float) / n


def _proj_perp(v: np.ndarray, axis: np.ndarray) -> np.ndarray:
    axis = _unit(axis)
    return np.asarray(v, float) - float(np.asarray(v, float) @ axis) * axis


def _pts(arr) -> list:
    return [[float(x), float(y)] for x, y in arr]


def _fold(eid, a2, b2, parent, child, tdir, mt="VALLEY"):
    return {"id": eid, "kind": "FOLD",
            "seg_2d": [[float(a2[0]), float(a2[1])], [float(b2[0]), float(b2[1])]],
            "fold": {"mt_va": mt, "parent": parent, "child": child,
                     "target_dir_3d": [round(float(v), 9) for v in tdir]}}


_STRIP_R = [[1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0]]  # net(x,y)→world(x,0,y)


def _features(glue_panel: str | None) -> list:
    fs = [{"id": "f_bleed", "kind": "BLEED", "offset_mm": 3.0},
          {"id": "f_check", "kind": "CHECK_BAR", "length_mm": 50.0},
          {"id": "f_reg", "kind": "REGISTRATION"}]
    if glue_panel:
        fs.insert(0, {"id": "f_glue", "kind": "GLUE_TAB", "panel_id": glue_panel})
    return fs


def _package(cls_id: str, params: dict) -> dict:
    """package.params = 全 PARAM_ORDER 键 (家族不适用键置 0, 数值契约)."""
    return {"type": cls_id,
            "template": {"id": cls_id, "version": "0.1"},
            "params": {k: params.get(k, 0) for k in PARAM_ORDER},
            "photo": None}


# ------------------------------------------------ 正 n 棱台 (pyramid_frustum)

_N_CLASSES = (4, 6, 8)
FRUSTUM_DEFAULTS = {"n": 4, "side_b": 60.0, "side_t": 36.0, "h": 80.0, "board_t": 0.42}


def _frustum_geom(n: int, sb: float, st: float, h: float) -> dict:
    """恢复全锥 → 扇形展开参数: 墙面顶角 β, 底/顶角锥距 lb/lt, 侧棱 Le."""
    a_b = sb / (2.0 * math.tan(math.pi / n))
    a_t = st / (2.0 * math.tan(math.pi / n))
    Rb = sb / (2.0 * math.sin(math.pi / n))
    Rt = st / (2.0 * math.sin(math.pi / n))
    if a_b - a_t <= 1e-9:
        raise ValueError("棱台须 side_b > side_t (正锥度)")
    H_p = h * a_b / (a_b - a_t)                 # 全锥高(恢复锥顶)
    lb = math.hypot(H_p, Rb)                    # 锥顶→底角
    Le = math.hypot(h, Rb - Rt)                 # 侧棱长 = 底角→顶角
    lt = lb - Le                                # 锥顶→顶角
    beta = 2.0 * math.asin(sb / (2.0 * lb))     # 每墙面顶角
    return {"a_b": a_b, "a_t": a_t, "Rb": Rb, "Rt": Rt, "H_p": H_p,
            "lb": lb, "lt": lt, "Le": Le, "beta": beta}


def _frustum_refs(n, sb, st, h):
    """世界参考: 底/顶多边形顶点环 (底 z=0, 顶 z=h, 中心在原点轴)."""
    g = _frustum_geom(n, sb, st, h)
    omega = lambda k: -math.pi / 2 - math.pi / n + 2.0 * math.pi * k / n
    vb = [np.array([g["Rb"] * math.cos(omega(k)), g["Rb"] * math.sin(omega(k)), 0.0])
          for k in range(n)]
    vt = [np.array([g["Rt"] * math.cos(omega(k)), g["Rt"] * math.sin(omega(k)), float(h)])
          for k in range(n)]
    apex = np.array([0.0, 0.0, g["H_p"]])
    return g, vb, vt, apex


def _fan_root_frame(vb0, vb1, vt0, apex, u0, u1, lb):
    """根框架: 3D 三元组对齐 — net 射线基 (u0,u1,u0×u1) → 墙0 面内锥顶射线基.
    R@u0 = (v0−apex)/lb, R@u1 = (v1−apex)/lb (两射线夹角同为 β, 旋转存在且唯一);
    off = 锥顶世界坐标 (net 原点映像)."""
    dL = _unit(vb0 - apex)
    dR = _unit(vb1 - apex)
    u03 = np.array([float(u0[0]), float(u0[1]), 0.0])
    u13 = np.array([float(u1[0]), float(u1[1]), 0.0])
    U = np.column_stack([u03, u13, np.cross(u03, u13)])
    D = np.column_stack([dL, dR, np.cross(dL, dR)])
    R = D @ np.linalg.inv(U)
    return R, np.asarray(apex, float)


def _frustum_build(params: dict, cls_id: str) -> dict:
    p = {**FRUSTUM_DEFAULTS, **(params or {})}
    n, sb, st, h = int(p["n"]), float(p["side_b"]), float(p["side_t"]), float(p["h"])
    g, vb, vt, apex = _frustum_refs(n, sb, st, h)
    beta, lb, lt, a_t = g["beta"], g["lb"], g["lt"], g["a_t"]
    phi = lambda k: -math.pi / 2 - beta / 2.0 + k * beta
    u = lambda k: np.array([math.cos(phi(k)), math.sin(phi(k))])
    B = [lb * u(k) for k in range(n + 1)]
    T = [lt * u(k) for k in range(n + 1)]

    panels = [{"id": f"w{k}", "role": "wall",
               "polygon_2d": _pts([B[k], B[k + 1], T[k + 1], T[k]])} for k in range(n)]
    # 顶盖三角片: 底边 = 顶弦(长 st), 尖点折入深 = a_t → 世界尖点 = 顶面中心。
    # 净图放置: 墙体占据顶弦外侧 (扇形 lt→lb), tf 必须内放 (朝顶心) 否则 G03 自压
    # (同款修: fan_net_ext.py line 142, 2026-11-25)
    for k in range(n):
        Fk = (T[k] + T[k + 1]) / 2.0 - a_t * u(k + 0.5)
        panels.append({"id": f"tf{k}", "role": "flap",
                       "polygon_2d": _pts([T[k], T[k + 1], Fk])})

    edges = []
    # 墙链: 铰链 = 侧棱 [T_{k+1}, B_{k+1}]; tdir = 邻墙面内指向面质心方向
    for k in range(n - 1):
        i1, i2 = (k + 1) % n, (k + 2) % n
        cen = (vb[i1] + vb[i2] + vt[i2] + vt[i1]) / 4.0
        axis = vb[i1] - vt[i1]
        tdir = _unit(_proj_perp(cen - (vb[i1] + vt[i1]) / 2.0, axis))
        edges.append(_fold(f"e_w{k}", T[k + 1], B[k + 1], f"w{k}", f"w{k+1}", tdir, "VALLEY"))
    # 顶盖片: 铰链 = 顶弦; tdir = 弦中点水平内向 (仅取水平分量, 弦中点含 z=h)
    for k in range(n):
        rim = (vt[k] + vt[(k + 1) % n]) / 2.0
        tdir = _unit(-np.array([rim[0], rim[1], 0.0]))
        edges.append(_fold(f"e_tf{k}", T[k], T[k + 1], f"w{k}", f"tf{k}", tdir, "MOUNTAIN"))

    u0, u1 = u(0), u(1)
    R0, off0 = _fan_root_frame(vb[0], vb[1], vt[0], apex, u0, u1, lb)
    ir = {
        "meta": {"ir_version": "0.1", "units": "mm",
                 "generator": "photo_dieline.parametric.odd_family 0.1",
                 "notes": f"正{n}棱台: 梯形墙扇形链(墙面顶角 {math.degrees(beta):.2f}°); "
                          f"顶盖 {n} 三角片折入深=上底 apothem={a_t:.3f}mm, 尖点互抵顶面中心",
                 "root_panel": "w0",
                 "root_frame": {"R": [[float(x) for x in row] for row in R0],
                                "off": [float(x) for x in off0]}},
        "package": _package(cls_id, p),
        "panels": panels, "edges": edges,
        "features": _features(None),
    }
    return ir


def _frustum_analytic(params: dict) -> dict:
    p = {**FRUSTUM_DEFAULTS, **(params or {})}
    n, sb, st, h = int(p["n"]), float(p["side_b"]), float(p["side_t"]), float(p["h"])
    g, vb, vt, _ = _frustum_refs(n, sb, st, h)
    xs = [v[0] for v in vb] + [v[0] for v in vt]
    ys = [v[1] for v in vb] + [v[1] for v in vt]
    return {"W": float(max(xs) - min(xs)), "D": float(max(ys) - min(ys)), "H": float(h)}


def _frustum_closure(ir, world) -> dict:
    p = ir.package["params"]
    n, sb, st, h = int(p["n"]), float(p["side_b"]), float(p["side_t"]), float(p["h"])
    _, vb, vt, _ = _frustum_refs(n, sb, st, h)
    res: dict[str, float] = {}
    # 顶盖片尖点互抵顶面中心 (远缘过轴线)
    for k in range(n):
        res[f"tf{k}.apex_to_axis"] = float(
            np.linalg.norm(world[f"tf{k}"][2] - np.array([0.0, 0.0, h])))
    # 环闭合缝: 末墙自由侧棱 ↔ 首墙左棱 (非铰链共享远缘)
    wn = world[f"w{n-1}"]
    res["seam.far_edge"] = float(max(np.linalg.norm(wn[1] - vb[0]),
                                     np.linalg.norm(wn[2] - vt[0])))
    return res


def _frustum_overlap() -> set:
    s = set()
    for n in _N_CLASSES:
        tf = [f"tf{k}" for k in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                s.add(frozenset({tf[i], tf[j]}))
        s.add(frozenset({"w0", f"w{n-1}"}))  # 环闭合末墙↔首墙共享棱
    return s


# ---------------------------------------------------- 锥管 (cone_wrap, n=16)

_CN = 16
CONE_DEFAULTS = {"side_b": 18.0, "side_t": 10.0, "h": 120.0, "glue_w": 8.0, "board_t": 0.42}


def _cone_build(params: dict, cls_id: str) -> dict:
    p = {**CONE_DEFAULTS, **(params or {})}
    n, sb, st, h = _CN, float(p["side_b"]), float(p["side_t"]), float(p["h"])
    gw = float(p["glue_w"])
    g, vb, vt, apex = _frustum_refs(n, sb, st, h)
    beta, lb, lt = g["beta"], g["lb"], g["lt"]
    phi = lambda k: -math.pi / 2 - beta / 2.0 + k * beta
    u = lambda k: np.array([math.cos(phi(k)), math.sin(phi(k))])
    B = [lb * u(k) for k in range(n + 1)]
    T = [lt * u(k) for k in range(n + 1)]

    panels = [{"id": f"w{k}", "role": "wall",
               "polygon_2d": _pts([B[k], B[k + 1], T[k + 1], T[k]])} for k in range(n)]

    # 粘缝: 附末墙自由侧棱, 折 180° 贴 w0 内侧 (搭接缝)
    q = np.array([-math.sin(phi(n)), math.cos(phi(n))])  # 增角侧法向
    panels.append({"id": "glue", "role": "glue",
                   "polygon_2d": _pts([T[n], B[n], B[n] + gw * q, T[n] + gw * q])})

    # 底盘: 16 边形近似, 附 w_{n/2} 底弦, 折 90° 落 z=0, 盘心精确落轴
    kd = n // 2
    R16 = sb / (2.0 * math.sin(math.pi / n))
    u_out = u(kd + 0.5)
    cd = (B[kd] + B[kd + 1]) / 2.0 + g["a_b"] * u_out      # net 16 边形中心
    # 正 16 边形: 顶点 j 角参数 s_j = δ − jΔ (δ=π/n), 由弦端点序锁定绕向
    cdir = -_unit(u_out)                                    # cd → 弦中点方向
    that = _unit(_proj_perp(B[kd] - cd, cdir))              # B_kd 端的弦向分量
    dl = math.pi / n
    ring = []
    for j in range(n):
        s = dl - j * 2.0 * dl
        v = cd + R16 * (math.cos(s) * cdir + math.sin(s) * that)
        ring.append([float(v[0]), float(v[1])])
    ring[0], ring[1] = _pts([B[kd], B[kd + 1]])            # 共享弦与墙底缘逐位一致
    panels.append({"id": "disk", "role": "flap", "polygon_2d": ring})

    edges = []
    for k in range(n - 1):
        i1, i2 = (k + 1) % n, (k + 2) % n
        cen = (vb[i1] + vb[i2] + vt[i2] + vt[i1]) / 4.0
        tdir = _unit(_proj_perp(cen - (vb[i1] + vt[i1]) / 2.0, vb[i1] - vt[i1]))
        edges.append(_fold(f"e_w{k}", T[k + 1], B[k + 1], f"w{k}", f"w{k+1}", tdir, "VALLEY"))
    # 粘缝 tdir: 沿 w0 面内从左棱指向墙质心 (180° 反贴, 落 w0 平面)
    axis0 = vb[0] - vt[0]
    in_w0 = (vb[0] + vb[1] + vt[1] + vt[0]) / 4.0 - (vb[0] + vt[0]) / 2.0
    edges.append(_fold("e_glue", T[n], B[n], f"w{n-1}", "glue",
                       _unit(_proj_perp(in_w0, axis0)), "MOUNTAIN"))
    # 底盘: 铰链 = w_kd 底弦; tdir = 弦中点 → 轴 (水平内向)
    edges.append(_fold("e_disk", B[kd], B[kd + 1], f"w{kd}", "disk",
                       _unit(-(vb[kd] + vb[kd + 1]) / 2.0), "MOUNTAIN"))

    R0, off0 = _fan_root_frame(vb[0], vb[1], vt[0], apex, u(0), u(1), lb)
    ir = {
        "meta": {"ir_version": "0.1", "units": "mm",
                 "generator": "photo_dieline.parametric.odd_family 0.1",
                 "notes": f"锥管曲面 {_CN} 边形近似: 墙 {_CN} 片梯形(每片4边, 墙面顶角 "
                          f"{math.degrees(beta):.2f}°), 搭接粘缝 1 片, 底盘 1 片 "
                          f"{_CN} 边形({_CN} 顶点/{_CN} 边)折 90° 落底, 盘心落轴",
                 "root_panel": "w0",
                 "root_frame": {"R": [[float(x) for x in row] for row in R0],
                                "off": [float(x) for x in off0]}},
        "package": _package(cls_id, p),
        "panels": panels, "edges": edges,
        "features": _features("glue"),
    }
    return ir


def _cone_analytic(params: dict) -> dict:
    p = {**CONE_DEFAULTS, **(params or {})}
    sb, st, h = float(p["side_b"]), float(p["side_t"]), float(p["h"])
    _, vb, vt, _ = _frustum_refs(_CN, sb, st, h)
    xs = [v[0] for v in vb] + [v[0] for v in vt]
    ys = [v[1] for v in vb] + [v[1] for v in vt]
    return {"W": float(max(xs) - min(xs)), "D": float(max(ys) - min(ys)), "H": float(h)}


def _cone_closure(ir, world) -> dict:
    p = ir.package["params"]
    sb, st, h = float(p["side_b"]), float(p["side_t"]), float(p["h"])
    n = _CN
    g, vb, vt, _ = _frustum_refs(n, sb, st, h)
    res: dict[str, float] = {}
    # 粘缝重合: 末墙自由侧棱 ↔ 首墙左棱 (经 15 折链累积后仍闭合)
    wn = world[f"w{n-1}"]
    res["seam.far_edge"] = float(max(np.linalg.norm(wn[1] - vb[0]),
                                     np.linalg.norm(wn[2] - vt[0])))
    # 粘片贴合: 落 w0 平面 (全部顶点)
    e0 = _unit(vb[1] - vb[0])
    up0 = _unit(vt[0] - vb[0])
    nrm = np.cross(e0, up0)
    res["glue.flush_w0"] = float(np.max(np.abs(
        (np.asarray(world["glue"]) - vb[0]) @ nrm)))
    # 底盘: 盘心(正 16 边形顶点均值)落轴 + 盘面落 z=0 + 远弦中点过轴
    dv = np.asarray(world["disk"], float)
    res["disk.center_to_axis"] = float(np.linalg.norm(dv.mean(axis=0)))
    res["disk.planar_z0"] = float(abs(dv[:, 2].mean()))
    res["disk.far_mid_to_axis"] = float(abs(
        float(np.linalg.norm((dv[8] + dv[9]) / 2.0)) - g["a_b"]))
    return res


def _cone_overlap() -> set:
    s = {frozenset({"glue", "w0"}), frozenset({"w0", f"w{_CN - 1}"})}
    # 盘缘 16 角点与各墙底弦共点(点触), 检查器平面投影保守判重叠 → 契约放行
    for k in range(_CN):
        if k != _CN // 2:  # 父墙 w8 走共享折线豁免
            s.add(frozenset({"disk", f"w{k}"}))
    s.add(frozenset({"disk", "glue"}))
    return s


# ---------------------------------------------------- 直管 (tube_glue, n=16)

_TN = 16
TUBE_DEFAULTS = {"side": 20.0, "h": 140.0, "glue_w": 20.0, "board_t": 0.42}


def _poly_ring(n: int, side: float, cx: float, cy: float):
    """正 n 边形顶点 (edge0 落 y=0, x∈[0,side]); 返回顶点与各边外法线/切向."""
    R = side / (2.0 * math.sin(math.pi / n))
    a = side / (2.0 * math.tan(math.pi / n))
    ctr = np.array([cx, cy])
    vs = [ctr + R * np.array([math.cos(-math.pi / 2 - math.pi / n + 2.0 * math.pi * k / n),
                              math.sin(-math.pi / 2 - math.pi / n + 2.0 * math.pi * k / n)])
          for k in range(n)]
    outward, tangent = [], []
    for k in range(n):
        em = (vs[k] + vs[(k + 1) % n]) / 2.0
        o = _unit(em - ctr)
        outward.append(o)
        tangent.append(np.array([-o[1], o[0]]))
    return vs, outward, tangent, a


def _tube_build(params: dict, cls_id: str) -> dict:
    p = {**TUBE_DEFAULTS, **(params or {})}
    n, side, h, gw = _TN, float(p["side"]), float(p["h"]), float(p["glue_w"])
    a = side / (2.0 * math.tan(math.pi / n))
    vs, outward, tangent, a = _poly_ring(n, side, side / 2.0, a)

    panels = [{"id": "glue", "role": "glue",
               "polygon_2d": _pts([[0, 0], [gw, 0], [gw, h], [0, h]])}]
    for i in range(n):
        x0 = gw + i * side
        panels.append({"id": f"w{i}", "role": "wall",
                       "polygon_2d": _pts([[x0, 0], [x0 + side, 0], [x0 + side, h], [x0, h]])})

    edges = []
    for i in range(n - 1):
        x = gw + (i + 1) * side
        edges.append(_fold(f"e_w{i}", (x, 0), (x, h), f"w{i}", f"w{i + 1}",
                           (float(tangent[i + 1][0]), float(tangent[i + 1][1]), 0.0),
                           "VALLEY"))
    edges.append(_fold("e_glue", (gw, 0), (gw, h), "w0", "glue", (1.0, 0.0, 0.0), "MOUNTAIN"))

    ir = {
        "meta": {"ir_version": "0.1", "units": "mm",
                 "generator": "photo_dieline.parametric.odd_family 0.1",
                 "notes": f"直管曲面 {_TN} 边形近似: 墙 {_TN} 片矩形(每片4边, 单边转角 "
                          f"{360.0 / _TN:.2f}°), 全重叠粘缝 1 片(宽=墙宽, 远缘与 w0 远缘重合)",
                 "root_panel": "w0",
                 "root_frame": {"R": _STRIP_R, "off": [-gw, 0.0, 0.0]}},
        "package": _package(cls_id, p),
        "panels": panels, "edges": edges,
        "features": _features("glue"),
    }
    return ir


def _tube_analytic(params: dict) -> dict:
    p = {**TUBE_DEFAULTS, **(params or {})}
    n, side, h = _TN, float(p["side"]), float(p["h"])
    vs, _, _, _ = _poly_ring(n, side, side / 2.0,
                             side / (2.0 * math.tan(math.pi / n)))
    xs = [v[0] for v in vs]
    ys = [v[1] for v in vs]
    return {"W": float(max(xs) - min(xs)), "D": float(max(ys) - min(ys)), "H": float(h)}


def _tube_closure(ir, world) -> dict:
    n = _TN
    res: dict[str, float] = {}
    # 环闭合缝: 末墙自由竖棱 ↔ w0 左棱
    wn = world[f"w{n-1}"]
    res["seam.far_edge"] = float(max(np.linalg.norm(wn[1] - world["w0"][0]),
                                     np.linalg.norm(wn[2] - world["w0"][3])))
    # 粘缝贴合: 落 w0 平面 (y=0)
    res["glue.flush_w0"] = float(abs(float(np.mean(np.asarray(world["glue"])[:, 1]))))
    # 全重叠: 粘片远缘 ↔ w0 远缘 (粘宽=墙宽时逐位重合; 顶对顶 底对底)
    res["glue.far_meets_w0_far"] = float(max(
        np.linalg.norm(world["glue"][3] - world["w0"][2]),
        np.linalg.norm(world["glue"][0] - world["w0"][1])))
    return res


def _tube_overlap() -> set:
    return {frozenset({"glue", "w0"}), frozenset({"w0", f"w{_TN - 1}"})}


# ---------------------------------------------------- 枕形盒 (pillow_box)

PILLOW_DEFAULTS = {"W": 60.0, "H": 90.0, "D": 28.0, "k": 3, "board_t": 0.42}


def _pillow_build(params: dict, cls_id: str) -> dict:
    p = {**PILLOW_DEFAULTS, **(params or {})}
    W, H, D, k = float(p["W"]), float(p["H"]), float(p["D"]), int(p["k"])
    r = D / 2.0
    dlt = math.pi / k
    c = D * math.sin(dlt / 2.0)          # 弧弦片深
    de = D / 2.0                          # 端片折入深

    def rect(pid, role, x0, x1, y0, y1):
        return {"id": pid, "role": role,
                "polygon_2d": _pts([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])}

    panels = [rect("faceF", "wall", 0, W, 0, H),
              rect("faceB", "wall", 0, W, H + k * c, H + k * c + H)]
    for j in range(1, k + 1):
        panels.append(rect(f"s{j}", "slope", 0, W, H + (j - 1) * c, H + j * c))
        panels.append(rect(f"b{j}", "slope", 0, W, -j * c, -(j - 1) * c))
    panels.append({"id": "endFL", "role": "flap",
                   "polygon_2d": _pts([[-de, 0], [0, 0], [0, H], [-de, H]])})
    panels.append({"id": "endFR", "role": "flap",
                   "polygon_2d": _pts([[W, 0], [W + de, 0], [W + de, H], [W, H]])})
    yb0 = H + k * c
    panels.append({"id": "endBL", "role": "flap",
                   "polygon_2d": _pts([[-de, yb0], [0, yb0], [0, yb0 + H], [-de, yb0 + H]])})
    panels.append({"id": "endBR", "role": "flap",
                   "polygon_2d": _pts([[W, yb0], [W + de, yb0], [W + de, yb0 + H], [W, yb0 + H]])})

    # 弧参考: 顶链 P(φ) = (D/2 + r cosφ, H + r sinφ), φ: π→0 (过顶鼓弧)
    #         底链 P'(φ) = (D/2 + r cosφ, -r sinφ),  φ: π→0 (过底鼓弧)
    Pt = lambda ph: np.array([D / 2.0 + r * math.cos(ph), H + r * math.sin(ph)])
    Pb = lambda ph: np.array([D / 2.0 + r * math.cos(ph), -r * math.sin(ph)])
    t3 = lambda v: (0.0, float(v[0]), float(v[1]))  # 弧参考(y,z) → world (0,y,z)

    edges = []
    edges.append(_fold("e_s1", (0, H), (W, H), "faceF", "s1", t3(_unit(Pt(math.pi - dlt) - Pt(math.pi)))))
    for j in range(2, k + 1):
        y = H + (j - 1) * c
        edges.append(_fold(f"e_s{j}", (0, y), (W, y), f"s{j-1}", f"s{j}",
                           t3(_unit(Pt(math.pi - j * dlt) - Pt(math.pi - (j - 1) * dlt)))))
    edges.append(_fold("e_fb", (0, H + k * c), (W, H + k * c), f"s{k}", "faceB",
                       (0.0, 0.0, -1.0), "MOUNTAIN"))
    edges.append(_fold("e_b1", (0, 0), (W, 0), "faceF", "b1", t3(_unit(Pb(math.pi - dlt) - Pb(math.pi)))))
    for j in range(2, k + 1):
        y = -(j - 1) * c
        edges.append(_fold(f"e_b{j}", (0, y), (W, y), f"b{j-1}", f"b{j}",
                           t3(_unit(Pb(math.pi - j * dlt) - Pb(math.pi - (j - 1) * dlt)))))
    # 端片折入: 左端 −x→+y (贴 x=0 端面, 伸向 +y), 右端镜像; 背面端片 −y 向
    edges.append(_fold("e_efl", (0, 0), (0, H), "faceF", "endFL", (0.0, 1.0, 0.0), "MOUNTAIN"))
    edges.append(_fold("e_efr", (W, 0), (W, H), "faceF", "endFR", (0.0, 1.0, 0.0), "MOUNTAIN"))
    edges.append(_fold("e_ebl", (0, yb0), (0, yb0 + H), "faceB", "endBL", (0.0, -1.0, 0.0), "MOUNTAIN"))
    edges.append(_fold("e_ebr", (W, yb0), (W, yb0 + H), "faceB", "endBR", (0.0, -1.0, 0.0), "MOUNTAIN"))

    ir = {
        "meta": {"ir_version": "0.1", "units": "mm",
                 "generator": "photo_dieline.parametric.odd_family 0.1",
                 "notes": f"枕形盒: 2 大面 + 上下弧链各 {k} 片折线近似半圆"
                          f"(每片转角 {math.degrees(dlt):.2f}°, 弦深 {c:.3f}mm)"
                          f" + 4 端折入片(深 D/2, 对片远缘中点重合)",
                 "root_panel": "faceF",
                 "root_frame": {"R": _STRIP_R, "off": [0.0, 0.0, 0.0]}},
        "package": _package(cls_id, p),
        "panels": panels, "edges": edges,
        "features": _features(None),
    }
    return ir


def _pillow_analytic(params: dict) -> dict:
    p = {**PILLOW_DEFAULTS, **(params or {})}
    return {"W": float(p["W"]), "D": float(p["D"]), "H": float(p["H"])}


def _pillow_closure(ir, world) -> dict:
    p = ir.package["params"]
    D = float(p["D"])
    res: dict[str, float] = {}
    # 环闭合: 底弧链末片远缘 ↔ faceB 底缘 (面网 y=H+kc 缘为铰链侧=世界顶缘, 底缘=verts 2,3)
    bk = world[f"b{int(p['k'])}"]
    fb = world["faceB"]
    res["loop.bottom_far"] = float(max(np.linalg.norm(bk[0] - fb[3]),
                                       np.linalg.norm(bk[1] - fb[2])))
    # 端部重合: 前后端片远缘中点 (深度各 D/2, 于 y=D/2 处对接)
    res["endL.meet"] = float(np.linalg.norm(
        np.mean(world["endFL"][[0, 3]], axis=0) - np.mean(world["endBL"][[0, 3]], axis=0)))
    res["endR.meet"] = float(np.linalg.norm(
        np.mean(world["endFR"][[1, 2]], axis=0) - np.mean(world["endBR"][[1, 2]], axis=0)))
    # 背面大面落位 (y=D 平面)
    res["faceB.plane_yD"] = float(abs(float(np.mean(np.asarray(fb)[:, 1])) - D))
    return res


def _pillow_overlap() -> set:
    # 端片与对面大面无实际接触(端片 y 跨度 D/2, 面在 y=0/D 平面),
    # 检查器非严格同侧判定 + 投影保守 → 契约放行
    return {frozenset({"endFL", "faceB"}), frozenset({"endFR", "faceB"}),
            frozenset({"endBL", "faceF"}), frozenset({"endBR", "faceF"})}


# ------------------------------------------------ 书封邮寄盒 (mailer_bookwrap)

MAILER_DEFAULTS = {"spine_w": 40.0, "cover_w": 150.0, "h": 220.0, "tuck_t": 35.0,
                   "board_t": 0.42}


def _mailer_build(params: dict, cls_id: str) -> dict:
    p = {**MAILER_DEFAULTS, **(params or {})}
    S, C, h, t = float(p["spine_w"]), float(p["cover_w"]), float(p["h"]), float(p["tuck_t"])

    def rect(pid, role, x0, x1):
        return {"id": pid, "role": role,
                "polygon_2d": _pts([[x0, 0], [x1, 0], [x1, h], [x0, h]])}

    panels = [rect("spine", "wall", 0, S),
              rect("coverL", "wall", -C, 0),
              rect("coverR", "wall", S, S + C),
              rect("tuck", "flap", S + C, S + C + t)]
    edges = [
        _fold("e_cl", (0, 0), (0, h), "spine", "coverL", (0.0, 1.0, 0.0), "VALLEY"),
        _fold("e_cr", (S, 0), (S, h), "spine", "coverR", (0.0, 1.0, 0.0), "VALLEY"),
        _fold("e_tk", (S + C, 0), (S + C, h), "coverR", "tuck", (0.0, -1.0, 0.0), "MOUNTAIN"),
    ]
    ir = {
        "meta": {"ir_version": "0.1", "units": "mm",
                 "generator": "photo_dieline.parametric.odd_family 0.1",
                 "notes": "书封邮寄盒: 中板(书脊) + 两侧 90° 翻盖(平行, 间距=书脊宽) "
                          "+ 插舌 180° 反贴于右盖内面",
                 "root_panel": "spine",
                 "root_frame": {"R": _STRIP_R, "off": [0.0, 0.0, 0.0]}},
        "package": _package(cls_id, p),
        "panels": panels, "edges": edges,
        "features": _features("tuck"),
    }
    return ir


def _mailer_analytic(params: dict) -> dict:
    p = {**MAILER_DEFAULTS, **(params or {})}
    return {"W": float(p["spine_w"]), "D": float(p["cover_w"]), "H": float(p["h"])}


def _mailer_closure(ir, world) -> dict:
    p = ir.package["params"]
    S, C, t = float(p["spine_w"]), float(p["cover_w"]), float(p["tuck_t"])
    res: dict[str, float] = {}
    # 两盖 90° 精确立起: 远缘贴 x=0 / x=S 竖面
    res["coverL.perp_x0"] = float(abs(float(np.mean(world["coverL"][[0, 3]], axis=0)[0])))
    res["coverR.perp_xS"] = float(abs(float(np.mean(world["coverR"][[1, 2]], axis=0)[0]) - S))
    # 插舌 180° 反贴: 全片落 x=S 平面, 远缘伸至 y = C - t
    tv = np.asarray(world["tuck"], float)
    res["tuck.flush_xS"] = float(np.max(np.abs(tv[:, 0] - S)))
    res["tuck.reach_yC-t"] = float(abs(float(np.mean(tv[[1, 2]], axis=0)[1]) - (C - t)))
    return res


def _mailer_overlap() -> set:
    return {frozenset({"tuck", "coverR"})}


# ------------------------------------------------- 楔形信封 (envelope_wedge)

ENV_DEFAULTS = {"W": 120.0, "H": 180.0, "side_d": 22.0, "bot_d": 40.0, "corner_e": 14.0,
                "board_t": 0.42}


def _envelope_build(params: dict, cls_id: str) -> dict:
    p = {**ENV_DEFAULTS, **(params or {})}
    W, H = float(p["W"]), float(p["H"])
    ds, db, ce = float(p["side_d"]), float(p["bot_d"]), float(p["corner_e"])
    dt = H - db  # 三角翻盖深: 使盖尖精确落在底翼远缘 (z = db)

    panels = [
        {"id": "body", "role": "wall",
         "polygon_2d": _pts([[0, 0], [W, 0], [W, H], [0, H]])},
        {"id": "sideL", "role": "flap",
         "polygon_2d": _pts([[-ds, ce], [0, 0], [0, H], [-ds, H - ce]])},
        {"id": "sideR", "role": "flap",
         "polygon_2d": _pts([[W, 0], [W + ds, ce], [W + ds, H - ce], [W, H]])},
        {"id": "bot", "role": "flap",
         "polygon_2d": _pts([[0, -db], [W, -db], [W, 0], [0, 0]])},
        {"id": "top", "role": "flap",
         "polygon_2d": _pts([[0, H], [W, H], [W / 2.0, H + dt]])},
    ]
    edges = [
        _fold("e_sl", (0, 0), (0, H), "body", "sideL", (1.0, 0.0, 0.0), "MOUNTAIN"),
        _fold("e_sr", (W, 0), (W, H), "body", "sideR", (-1.0, 0.0, 0.0), "MOUNTAIN"),
        _fold("e_bt", (0, 0), (W, 0), "body", "bot", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_tp", (0, H), (W, H), "body", "top", (0.0, 0.0, -1.0), "MOUNTAIN"),
    ]
    ir = {
        "meta": {"ir_version": "0.1", "units": "mm",
                 "generator": "photo_dieline.parametric.odd_family 0.1",
                 "notes": f"楔形信封: 大面 + 2 楔形侧翼(角部斜切 {ce}mm) + 底折翼 "
                          f"+ 三角翻盖(深 {dt:.3f}mm = H-bot_d, 盖尖抵底翼远缘); "
                          "全片 180° 平折封闭",
                 "root_panel": "body",
                 "root_frame": {"R": _STRIP_R, "off": [0.0, 0.0, 0.0]}},
        "package": _package(cls_id, p),
        "panels": panels, "edges": edges,
        "features": _features(None),
    }
    return ir


def _envelope_analytic(params: dict) -> dict:
    p = {**ENV_DEFAULTS, **(params or {})}
    return {"W": float(p["W"]), "D": 0.0, "H": float(p["H"])}


def _envelope_closure(ir, world) -> dict:
    p = ir.package["params"]
    W, db = float(p["W"]), float(p["bot_d"])
    res: dict[str, float] = {}
    # 翻盖远缘重合: 三角盖尖 ↔ 底翼远缘中点 (W/2, 0, bot_d)
    res["top.apex_meets_bot_far"] = float(
        np.linalg.norm(world["top"][2] - np.array([W / 2.0, 0.0, db])))
    # 各翼 180° 平折贴合: 落大面平面 (y=0)
    for pid in ("sideL", "sideR", "bot"):
        res[f"{pid}.flush_y0"] = float(abs(float(np.mean(np.asarray(world[pid])[:, 1]))))
    return res


def _envelope_overlap() -> set:
    """封闭信封全片平折共面: 5 片两两共面叠合 → 全对放行 (真实工艺契约)."""
    ids = ["body", "sideL", "sideR", "bot", "top"]
    return {frozenset({ids[i], ids[j]})
            for i in range(len(ids)) for j in range(i + 1, len(ids))}


# ------------------------------------------------------------ 注册与分发

for _cid in (f"pyramid_frustum_n{n}" for n in _N_CLASSES):
    _base.register(_cid, "odd_family")
for _cid in ("cone_wrap", "tube_glue", "pillow_box", "mailer_bookwrap", "envelope_wedge"):
    _base.register(_cid, "odd_family")

# 模块契约: 多类异构模块 → PARAM_ORDER = 全家族键并集; 家族不适用键置 0.
# 批量契约 params = dict(DEFAULTS) + class_params(cls_id) → build_ir(params) 由参数判型.
PARAM_ORDER = ["n", "side_b", "side_t", "h", "board_t", "glue_w", "side", "W", "H",
               "D", "k", "spine_w", "cover_w", "tuck_t", "side_d", "bot_d", "corner_e"]
DEFAULTS = {"n": 4, "side_b": 60.0, "side_t": 36.0, "h": 80.0, "board_t": 0.42,
            "glue_w": 0.0, "side": 0.0, "W": 0.0, "H": 0.0, "D": 0.0, "k": 0,
            "spine_w": 0.0, "cover_w": 0.0, "tuck_t": 0.0, "side_d": 0.0,
            "bot_d": 0.0, "corner_e": 0.0}


def _cls_params(real: dict) -> dict:
    """家族真实参数 + 不适用键置 0 → 全键类参数表."""
    p = {k: 0 for k in PARAM_ORDER}
    p.update(real)
    return p


def class_params(cls_id: str) -> dict:
    """类ID → 该类全键参数表 (批量 build_ir 判型与取值的唯一权威)."""
    if cls_id.startswith("pyramid_frustum_n"):
        return _cls_params({"n": int(cls_id.rsplit("_n", 1)[1]),
                            "side_b": 60.0, "side_t": 36.0, "h": 80.0, "board_t": 0.42})
    if cls_id == "cone_wrap":
        return _cls_params({"side_b": 18.0, "side_t": 10.0, "h": 120.0,
                            "glue_w": 8.0, "board_t": 0.42})
    if cls_id == "tube_glue":
        return _cls_params({"side": 20.0, "h": 140.0, "glue_w": 20.0, "board_t": 0.42})
    if cls_id == "pillow_box":
        return _cls_params({"W": 60.0, "H": 90.0, "D": 28.0, "k": 3, "board_t": 0.42})
    if cls_id == "mailer_bookwrap":
        return _cls_params({"spine_w": 40.0, "cover_w": 150.0, "h": 220.0,
                            "tuck_t": 35.0, "board_t": 0.42})
    if cls_id == "envelope_wedge":
        return _cls_params({"W": 120.0, "H": 180.0, "side_d": 22.0, "bot_d": 40.0,
                            "corner_e": 14.0, "board_t": 0.42})
    raise KeyError(f"未知类ID: {cls_id}")


def _family_of(p: dict) -> str:
    """合并参数 → 类ID (家族判别键 > 0 优先)."""
    if p.get("spine_w", 0) > 0:
        return "mailer_bookwrap"
    if p.get("side_d", 0) > 0:
        return "envelope_wedge"
    if p.get("k", 0) > 0:
        return "pillow_box"
    if p.get("side", 0) > 0:
        return "tube_glue"
    if p.get("side_b", 0) > 0:
        n = int(p.get("n") or 0)
        return f"pyramid_frustum_n{n}" if n >= 3 else "cone_wrap"
    return "pyramid_frustum_n4"


def _pos(p, *keys):
    for k in keys:
        v = p.get(k)
        if v is None or not isinstance(v, (int, float)) or isinstance(v, bool) or v <= 0:
            raise ValueError(f"非法参数 {k}={v!r} (须正数)")


def validate_params(params: dict) -> None:
    fam = _family_of(params)
    if fam.startswith("pyramid_frustum"):
        _pos(params, "side_b", "side_t", "h", "board_t")
        n = params.get("n")
        if not isinstance(n, int) or isinstance(n, bool) or not (3 <= n <= 24):
            raise ValueError(f"非法参数 n={n!r} (须 3..24 整数)")
        if params["side_t"] >= params["side_b"]:
            raise ValueError("棱台须 side_b > side_t (正锥度)")
    elif fam == "cone_wrap":
        _pos(params, "side_b", "side_t", "h", "glue_w", "board_t")
        if params["side_t"] >= params["side_b"]:
            raise ValueError("锥管须 side_b > side_t (正锥度)")
        if params["glue_w"] > params["side_t"]:
            raise ValueError("锥管粘片宽不得超上底弦 (侧墙向顶收窄, glue_w ≤ side_t)")
    elif fam == "tube_glue":
        _pos(params, "side", "h", "glue_w", "board_t")
        if params["glue_w"] > params["side"]:
            raise ValueError("直管全重叠粘缝: glue_w ≤ side")
    elif fam == "pillow_box":
        _pos(params, "W", "H", "D", "board_t")
        k = params.get("k")
        if not isinstance(k, int) or isinstance(k, bool) or not (2 <= k <= 8):
            raise ValueError(f"非法参数 k={k!r} (须 2..8 整数)")
    elif fam == "mailer_bookwrap":
        _pos(params, "spine_w", "cover_w", "h", "tuck_t", "board_t")
        if params["tuck_t"] >= params["cover_w"]:
            raise ValueError("书封须 tuck_t < cover_w")
    else:
        _pos(params, "W", "H", "side_d", "bot_d", "corner_e", "board_t")
        if 2.0 * params["side_d"] >= params["W"]:
            raise ValueError("信封侧翼须 2*side_d < W")
        if params["bot_d"] >= params["H"]:
            raise ValueError("信封须 bot_d < H (三角翻盖深 H-bot_d > 0)")
        if 2.0 * params["corner_e"] >= params["H"]:
            raise ValueError("信封须 2*corner_e < H")


_BUILDERS = {
    "pyramid_frustum": (_frustum_build, _frustum_analytic, _frustum_closure,
                        _frustum_overlap, ("wall",)),
    "cone_wrap": (_cone_build, _cone_analytic, _cone_closure, _cone_overlap, ("wall",)),
    "tube_glue": (_tube_build, _tube_analytic, _tube_closure, _tube_overlap, ("wall",)),
    "pillow_box": (_pillow_build, _pillow_analytic, _pillow_closure, _pillow_overlap,
                   ("wall",)),
    "mailer_bookwrap": (_mailer_build, _mailer_analytic, _mailer_closure, _mailer_overlap,
                        ("wall",)),
    "envelope_wedge": (_envelope_build, _envelope_analytic, _envelope_closure,
                       _envelope_overlap, ("wall",)),
}


def _dispatch(cls_id: str):
    for pref, hooks in _BUILDERS.items():
        if cls_id.startswith(pref):
            return hooks
    raise KeyError(f"未知类ID: {cls_id}")


def build_ir(params: dict | None = None, cls_id: str | None = None) -> dict:
    """契约入口; 类ID 由参数判型 (缺省 n=4 棱台), 或显式 cls_id 覆盖."""
    p = {**DEFAULTS, **(params or {})}
    cid = cls_id or _family_of(p)
    family = "pyramid_frustum" if cid.startswith("pyramid_frustum_n") else cid
    hooks = _dispatch(family)
    return hooks[0]({**DEFAULTS, **p}, cid)


def analytic_bbox(params: dict) -> dict:
    p = {**DEFAULTS, **(params or {})}
    cid = _family_of(p)
    family = "pyramid_frustum" if cid.startswith("pyramid_frustum_n") else cid
    return _dispatch(family)[1](p)


def closure_checks(ir, world) -> dict:
    cid = ir.package["template"]["id"]
    family = "pyramid_frustum" if cid.startswith("pyramid_frustum_n") else cid
    return _dispatch(family)[2](ir, world)


def allowed_overlap() -> set:
    """全家族允许叠层并集 (G06 按模板 id 分发不可行 → 契约为全家族并集)."""
    s: set = set()
    for hooks in _BUILDERS.values():
        s |= hooks[3]()
    return s


def solid_roles() -> tuple:
    return ("wall",)
