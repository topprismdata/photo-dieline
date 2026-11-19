"""brick_family: 砖形无菌包 + 屋顶包变体 (4 类, 批量验证家族).

类ID:
  aseptic_brick       砖形无菌包: 4 矩形墙 + 顶/底斜肩链
                      (每端 2 平行四边形斜板(净高 s=sqrt((D/2)^2+hr^2), 斜边与端三角
                       逐位共边) + 2 三角端板; 顶脊偏 -x D/2, 底脊偏 +x D/2, 顶底反折;
                       脊线/端缘/环缝逐位重合, 折后完全封合)
  brick_250ml         小砖形 (250ml 级参数缩尺, 独立类参数表, 拓扑同 aseptic_brick)
  gable_screw_cap     旋盖屋顶包: gable 拓扑 + 脊上双平鳍座板(半圆缺口对合 16 边形圆孔)
                      + 孔缘 16 片竖立盖裙(多边形近似圆座, 裙缝逐位重合)
  gable_fin_gap_wide  宽鳍缝隙屋顶包: V 形张开双立鳍 (鳍距加大/鳍更高, 独立类)

几何约定: 条带类根面板, 缺省 gable 映射 net(x,y)→world(x,0,y);
砖盒 x∈[-W/2,W/2], y∈[0,D], 墙 z∈[0,Hb]。
所有 fold 的 target_dir_3d 由解析世界像自动导出 (铰链轴 + 子板质心目标方向 ⊥ 分量),
closure 全部为折叠后世界坐标残差 (远缘重合/环缝重合/鳍距自洽), 无构造恒等量。
"""
from __future__ import annotations

import math

import numpy as np

from . import base as _base

_base.register("aseptic_brick", "brick_family")
_base.register("brick_250ml", "brick_family")
_base.register("gable_screw_cap", "brick_family")
_base.register("gable_fin_gap_wide", "brick_family")

PARAM_ORDER = ["W", "D", "Hb", "Hr", "hr", "Ef", "fin_gap", "cap_r", "cap_h",
               "glue_w", "board_t"]
DEFAULTS = {"W": 60.0, "D": 40.0, "Hb": 120.0, "Hr": 0.0, "hr": 12.0, "Ef": 0.0,
            "fin_gap": 0.0, "cap_r": 0.0, "cap_h": 0.0, "glue_w": 12.0,
            "board_t": 0.42}

_NSK = 8  # 半圆缺口弦片数 (全孔 16 边形近似)


# ---------------------------------------------------------------- 公共工具

def _unit(v) -> np.ndarray:
    n = float(np.linalg.norm(v))
    if n < 1e-12:
        raise ValueError("零向量")
    return np.asarray(v, float) / n


def _proj_perp(v: np.ndarray, axis: np.ndarray) -> np.ndarray:
    axis = _unit(axis)
    return np.asarray(v, float) - float(np.asarray(v, float) @ axis) * axis


def _pts(arr) -> list:
    return [[float(x), float(y)] for x, y in arr]


def _circ_intersect(c1, r1, c2, r2, side_x: float) -> tuple:
    """两圆交点中取 x 侧别符合 side_x 方向的那个 (端三角 net 第三顶点)."""
    c1, c2 = np.asarray(c1, float), np.asarray(c2, float)
    d = float(np.linalg.norm(c2 - c1))
    a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
    h2 = r1 * r1 - a * a
    h = math.sqrt(max(0.0, h2))
    mid = c1 + a * (c2 - c1) / d
    perp = np.array([-(c2 - c1)[1], (c2 - c1)[0]]) / d
    p1, p2 = mid + h * perp, mid - h * perp
    return tuple(p1 if (p1[0] - mid[0]) * side_x >= 0 else p2)


def _mean3(poly) -> np.ndarray:
    return np.mean(np.asarray(poly, float), axis=0)


def _directed_edges(specs: list, world: dict) -> list:
    """fold 规格 → 显式 target_dir_3d 边.

    每条规格: {"id","seg":[a,b](net),"parent","child","mt","wa","wb"(世界铰链端点)}.
    tgt = 子板世界质心相对铰链中点的 ⊥ 铰链轴分量 (真实折叠目标方向).
    """
    edges = []
    for sp in specs:
        wa, wb = np.asarray(sp["wa"], float), np.asarray(sp["wb"], float)
        axis = _unit(wb - wa)
        tgt = _unit(_proj_perp(_mean3(world[sp["child"]]) - (wa + wb) / 2.0, axis))
        edges.append({"id": sp["id"], "kind": "FOLD",
                      "seg_2d": [list(map(float, sp["seg"][0])), list(map(float, sp["seg"][1]))],
                      "fold": {"mt_va": sp["mt"], "parent": sp["parent"],
                               "child": sp["child"],
                               "target_dir_3d": [round(float(v), 9) for v in tgt]}})
    return edges


def _features(glue_panel: str) -> list:
    return [{"id": "f_glue", "kind": "GLUE_TAB", "panel_id": glue_panel},
            {"id": "f_bleed", "kind": "BLEED", "offset_mm": 3.0},
            {"id": "f_check", "kind": "CHECK_BAR", "length_mm": 50.0},
            {"id": "f_reg", "kind": "REGISTRATION"}]


def _package(cls_id: str, p: dict) -> dict:
    return {"type": cls_id,
            "template": {"id": cls_id, "version": "0.1"},
            "params": {k: float(p.get(k, 0)) for k in PARAM_ORDER},
            "photo": None}


def _ir(cls_id: str, p: dict, panels: list, edges: list, notes: str) -> dict:
    return {"meta": {"ir_version": "0.1", "units": "mm",
                     "generator": "photo_dieline.parametric.brick_family 0.1",
                     "root_panel": "wallL", "notes": notes},
            "package": _package(cls_id, p),
            "panels": panels, "edges": edges,
            "features": _features("glue")}


# ------------------------------------------------- 砖形无菌包 (aseptic_brick)

BRICK_DEFAULTS = {"W": 60.0, "D": 40.0, "Hb": 120.0, "hr": 12.0,
                  "glue_w": 12.0, "board_t": 0.42}
BRICK250_DEFAULTS = {"W": 40.0, "D": 28.0, "Hb": 95.0, "hr": 8.0,
                     "glue_w": 10.0, "board_t": 0.35}


def _brick_world(p: dict) -> dict:
    """砖盒解析世界像 (顶点序与 net 面板一一对应)."""
    W, D, Hb, hr = float(p["W"]), float(p["D"]), float(p["Hb"]), float(p["hr"])
    gw = float(p["glue_w"])
    s = math.hypot(D / 2.0, hr)
    x1, x2, x3, x4, x5 = gw, gw + D, gw + D + W, gw + D + W + D, gw + 2 * D + 2 * W
    hx, tx = -W / 2.0, W / 2.0  # 盒左/右面
    return {
        "glue": [[hx + gw, 0, 0], [hx, 0, 0], [hx, 0, Hb], [hx + gw, 0, Hb]],
        "wallL": [[hx, 0, 0], [hx, D, 0], [hx, D, Hb], [hx, 0, Hb]],
        "back": [[hx, D, 0], [tx, D, 0], [tx, D, Hb], [hx, D, Hb]],
        "wallR": [[tx, D, 0], [tx, 0, 0], [tx, 0, Hb], [tx, D, Hb]],
        "front": [[tx, 0, 0], [hx, 0, 0], [hx, 0, Hb], [tx, 0, Hb]],
        # 顶斜肩链: 脊偏 -x D/2
        "slopeB": [[hx, D, Hb], [tx, D, Hb], [tx - D / 2, D / 2, Hb + hr],
                   [hx - D / 2, D / 2, Hb + hr]],
        "triL": [[hx, D, Hb], [hx - D / 2, D / 2, Hb + hr], [hx, 0, Hb]],
        "triR": [[tx, D, Hb], [tx - D / 2, D / 2, Hb + hr], [tx, 0, Hb]],
        "slopeF": [[tx, 0, Hb], [hx, 0, Hb], [hx - D / 2, D / 2, Hb + hr],
                   [tx - D / 2, D / 2, Hb + hr]],
        # 底斜底链: 脊偏 +x D/2 (顶底反折)
        "slopeB2": [[hx, D, 0], [tx, D, 0], [tx + D / 2, D / 2, -hr],
                    [hx + D / 2, D / 2, -hr]],
        "triLB": [[hx, 0, 0], [hx, D, 0], [hx + D / 2, D / 2, -hr]],
        "triRB": [[tx, D, 0], [tx, 0, 0], [tx + D / 2, D / 2, -hr]],
        "slopeF2": [[tx, 0, 0], [hx, 0, 0], [hx + D / 2, D / 2, -hr],
                    [tx + D / 2, D / 2, -hr]],
    }


def _brick_net(p: dict) -> list:
    W, D, Hb, hr = float(p["W"]), float(p["D"]), float(p["Hb"]), float(p["hr"])
    gw = float(p["glue_w"])
    s = math.hypot(D / 2.0, hr)
    x1 = gw
    x2 = x1 + D
    x3 = x2 + W
    x4 = x3 + D
    x5 = x4 + W
    return [
        ("glue", "glue", [(0, 0), (gw, 0), (gw, Hb), (0, Hb)]),
        ("wallL", "wall", [(x1, 0), (x2, 0), (x2, Hb), (x1, Hb)]),
        ("back", "wall", [(x2, 0), (x3, 0), (x3, Hb), (x2, Hb)]),
        ("wallR", "wall", [(x3, 0), (x4, 0), (x4, Hb), (x3, Hb)]),
        ("front", "wall", [(x4, 0), (x5, 0), (x5, Hb), (x4, Hb)]),
        ("slopeB", "slope", [(x2, Hb), (x3, Hb), (x3 - D / 2, Hb + s), (x2 - D / 2, Hb + s)]),
        ("triL", "slope", [(x2, Hb), (x2 - D / 2, Hb + s), (x1, Hb)]),
        ("triR", "slope", [(x3, Hb), (x3 - D / 2, Hb + s),
                           _circ_intersect((x3, Hb), D, (x3 - D / 2, Hb + s),
                                           math.hypot(D / 2, s), 1.0)]),
        ("slopeF", "slope", [(x4, Hb), (x5, Hb), (x5 + D / 2, Hb + s), (x4 + D / 2, Hb + s)]),
        ("slopeB2", "slope", [(x2, 0), (x3, 0), (x3 + D / 2, -s), (x2 + D / 2, -s)]),
        ("triLB", "slope", [(x1, 0), (x2, 0), (x1 + D / 2, -s)]),
        ("triRB", "slope", [(x3, 0), (x4, 0), (x3 + D / 2, -s)]),
        ("slopeF2", "slope", [(x4, 0), (x5, 0), (x5 - D / 2, -s), (x4 - D / 2, -s)]),
    ]


def _brick_build(p: dict, cls_id: str) -> dict:
    world = _brick_world(p)
    panels = [{"id": pid, "role": role, "polygon_2d": _pts(poly)}
              for pid, role, poly in _brick_net(p)]
    nw = {q["id"]: q["polygon_2d"] for q in panels}

    def W3(pid, i):
        return world[pid][i]

    specs = [
        {"id": "e_glue", "seg": (nw["wallL"][0], nw["wallL"][3]), "parent": "wallL",
         "child": "glue", "mt": "MOUNTAIN", "wa": W3("wallL", 0), "wb": W3("wallL", 3)},
        {"id": "e_wl_bk", "seg": (nw["wallL"][1], nw["wallL"][2]), "parent": "wallL",
         "child": "back", "mt": "VALLEY", "wa": W3("wallL", 1), "wb": W3("wallL", 2)},
        {"id": "e_bk_wr", "seg": (nw["back"][1], nw["back"][2]), "parent": "back",
         "child": "wallR", "mt": "VALLEY", "wa": W3("back", 1), "wb": W3("back", 2)},
        {"id": "e_wr_ft", "seg": (nw["wallR"][1], nw["wallR"][2]), "parent": "wallR",
         "child": "front", "mt": "VALLEY", "wa": W3("wallR", 1), "wb": W3("wallR", 2)},
        {"id": "e_bk_sl", "seg": (nw["back"][3], nw["back"][2]), "parent": "back",
         "child": "slopeB", "mt": "VALLEY", "wa": W3("back", 3), "wb": W3("back", 2)},
        {"id": "e_sl_tl", "seg": (nw["slopeB"][0], nw["slopeB"][3]), "parent": "slopeB",
         "child": "triL", "mt": "VALLEY", "wa": W3("slopeB", 0), "wb": W3("slopeB", 3)},
        {"id": "e_sl_tr", "seg": (nw["slopeB"][1], nw["slopeB"][2]), "parent": "slopeB",
         "child": "triR", "mt": "VALLEY", "wa": W3("slopeB", 1), "wb": W3("slopeB", 2)},
        {"id": "e_ft_sl", "seg": (nw["front"][3], nw["front"][2]), "parent": "front",
         "child": "slopeF", "mt": "VALLEY", "wa": W3("front", 3), "wb": W3("front", 2)},
        {"id": "e_bk_sb2", "seg": (nw["back"][0], nw["back"][1]), "parent": "back",
         "child": "slopeB2", "mt": "VALLEY", "wa": W3("back", 0), "wb": W3("back", 1)},
        {"id": "e_wl_tlb", "seg": (nw["wallL"][0], nw["wallL"][1]), "parent": "wallL",
         "child": "triLB", "mt": "MOUNTAIN", "wa": W3("wallL", 0), "wb": W3("wallL", 1)},
        {"id": "e_wr_trb", "seg": (nw["wallR"][0], nw["wallR"][1]), "parent": "wallR",
         "child": "triRB", "mt": "MOUNTAIN", "wa": W3("wallR", 0), "wb": W3("wallR", 1)},
        {"id": "e_ft_sf2", "seg": (nw["front"][0], nw["front"][1]), "parent": "front",
         "child": "slopeF2", "mt": "VALLEY", "wa": W3("front", 0), "wb": W3("front", 1)},
    ]
    edges = _directed_edges(specs, world)
    return _ir(cls_id, p, panels, edges,
               "砖形无菌包: 4 矩形墙 + 顶/底斜肩链 (每端 2 平行四边形斜板净高 "
               f"{math.hypot(float(p['D']) / 2, float(p['hr'])):.2f}mm + 2 三角端板, "
               "斜边与端板逐位共边; 顶脊偏 -x D/2, 底脊偏 +x D/2 反折; 全封合)")


def _brick_closure(ir, world) -> dict:
    """斜肩链远缘重合 + 端板尖点落脊 + 环闭合缝 + 粘口贴合 (跨链强判据)."""
    res: dict[str, float] = {}

    def d(name, pa, ia, pb, ib):
        res[name] = float(np.linalg.norm(np.asarray(world[pa][ia], float)
                                         - np.asarray(world[pb][ib], float)))

    # 顶链远缘重合: 两平行四边形脊线逐位 + 端三角尖点落脊 + 自由边落对坡
    d("top.ridge.far_meet", "slopeB", 3, "slopeF", 2)
    d("top.ridge.far_meet2", "slopeB", 2, "slopeF", 3)
    d("top.triL.apex_on_ridge", "triL", 1, "slopeB", 3)
    d("top.triL.free_meets_slopeF", "triL", 2, "slopeF", 1)
    d("top.triR.apex_on_ridge", "triR", 1, "slopeB", 2)
    d("top.triR.free_meets_slopeF", "triR", 2, "slopeF", 0)
    # 底链
    d("bot.ridge.far_meet", "slopeB2", 2, "slopeF2", 3)
    d("bot.ridge.far_meet2", "slopeB2", 3, "slopeF2", 2)
    d("bot.triLB.apex_on_ridge", "triLB", 2, "slopeB2", 3)
    d("bot.triLB.free_meets_slopeF2", "triLB", 0, "slopeF2", 1)
    d("bot.triRB.apex_on_ridge", "triRB", 2, "slopeB2", 2)
    d("bot.triRB.free_meets_slopeF2", "triRB", 1, "slopeF2", 0)
    # 墙环闭合缝: front 自由竖棱 ↔ wallL 竖棱 (3 折链累积)
    d("seam.loop.front_wallL", "front", 1, "wallL", 0)
    d("seam.loop.front_wallL2", "front", 2, "wallL", 3)
    # 粘口 180° 反贴 front 内面: 平贴 + 远缘落贴合位 (翻转/偏折均爆)
    res["glue.flush_y0"] = float(abs(float(np.mean(np.asarray(world["glue"])[:, 1]))))
    gw = float(ir.param("glue_w"))
    far_mid = np.mean(np.asarray(world["glue"], float)[[0, 3]], axis=0)
    res["glue.far_on_front"] = float(abs(far_mid[0]
                                         - (-float(ir.param("W")) / 2.0 + gw)))
    return res


def _brick_overlap() -> set:
    return {frozenset(x) for x in (
        ("glue", "front"), ("front", "wallL"),          # 共面叠合 / 环闭合共享棱
        ("slopeB", "slopeF"), ("slopeB2", "slopeF2"),   # 脊线共边密封
        ("triL", "wallL"), ("triL", "slopeF"),
        ("triR", "wallR"), ("triR", "slopeF"),
        ("triLB", "wallL"), ("triLB", "slopeB2"),
        ("triRB", "wallR"), ("triRB", "slopeF2"),
        ("triRB", "slopeB2"))}  # 共斜边斜接, 投影保守判重叠放行


# ------------------------------------------------ 旋盖屋顶包 (gable_screw_cap)

SCREW_DEFAULTS = {"W": 45.0, "D": 45.0, "Hb": 100.0, "Hr": 12.0, "Ef": 16.0,
                  "cap_r": 13.0, "cap_h": 9.0, "glue_w": 12.0, "board_t": 0.45}


def _screw_geom(p: dict) -> dict:
    W, D, Hb, Hr = float(p["W"]), float(p["D"]), float(p["Hb"]), float(p["Hr"])
    gw, Ef, Rc, Hc = float(p["glue_w"]), float(p["Ef"]), float(p["cap_r"]), float(p["cap_h"])
    s = math.hypot(D / 2.0, Hr)
    x1, x2, x3, x4, x5 = gw, gw + D, gw + D + W, gw + D + W + D, gw + 2 * D + 2 * W
    return {"W": W, "D": D, "Hb": Hb, "Hr": Hr, "Ef": Ef, "Rc": Rc, "Hc": Hc,
            "s": s, "x1": x1, "x2": x2, "x3": x3, "x4": x4, "x5": x5,
            "zr": Hb + Hr}  # zr = 脊/座板高度


def _arc_pts_net(xc: float, yb: float, Rc: float) -> list:
    """半圆缺口弧点 net (θ_j = π − jπ/8, j=0..8; 端点落缺口缘)."""
    return [(xc + Rc * math.cos(math.pi - j * math.pi / _NSK),
             yb + Rc * math.sin(math.pi - j * math.pi / _NSK)) for j in range(_NSK + 1)]


def _sliver_quads(arc: list, ctr2: tuple, Hc: float) -> tuple[list, list]:
    """孔缘裙片: 弦 [A_j,A_j+1] + 内向 ⊥ 弦偏移 Hc (世界竖立后侧缝逐位重合)."""
    chords, quads = [], []
    for j in range(_NSK):
        a, b = arc[j], arc[j + 1]
        mid = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        nh = _unit(np.array([ctr2[0] - mid[0], ctr2[1] - mid[1]]))
        chords.append((a, b))
        quads.append([a, b, (b[0] + Hc * nh[0], b[1] + Hc * nh[1]),
                      (a[0] + Hc * nh[0], a[1] + Hc * nh[1])])
    return chords, quads


def _screw_build(p: dict, cls_id: str) -> dict:
    g = _screw_geom(p)
    W, D, Hb, Hr, Ef, Rc, Hc, s = (g["W"], g["D"], g["Hb"], g["Hr"], g["Ef"],
                                   g["Rc"], g["Hc"], g["s"])
    x1, x2, x3, x4, x5, zr = g["x1"], g["x2"], g["x3"], g["x4"], g["x5"], g["zr"]
    hx, tx = -W / 2.0, W / 2.0

    arcB = _arc_pts_net(x2 + W / 2.0, Hb + s, Rc)
    arcF = _arc_pts_net(x4 + W / 2.0, Hb + s, Rc)
    chB, qB = _sliver_quads(arcB, (x2 + W / 2.0, Hb + s), Hc)
    chF, qF = _sliver_quads(arcF, (x4 + W / 2.0, Hb + s), Hc)

    finB_net = ([(x2, Hb + s)] + arcB + [(x3, Hb + s), (x3, Hb + s + Ef), (x2, Hb + s + Ef)])
    finF_net = ([(x4, Hb + s)] + arcF + [(x5, Hb + s), (x5, Hb + s + Ef), (x4, Hb + s + Ef)])
    # 顶点序旋转: 起点移到弧顶 (脱开脊线; 引擎 fan 自 v0, 凹多边形共线三元组会退化)
    finB_net = finB_net[5:] + finB_net[:5]
    finF_net = finF_net[5:] + finF_net[:5]

    # 世界像: 座板平鳍 z=zr; finB 体伸 -y, finF 体伸 +y; 缺口对合 16 边形圆孔
    arcB_w = [[Rc * math.cos(math.pi - j * math.pi / _NSK),
               D / 2 - Rc * math.sin(math.pi - j * math.pi / _NSK), zr]
              for j in range(_NSK + 1)]
    arcF_w = [[-Rc * math.cos(math.pi - j * math.pi / _NSK),
               D / 2 + Rc * math.sin(math.pi - j * math.pi / _NSK), zr]
              for j in range(_NSK + 1)]

    def lift(v, h):
        return [v[0], v[1], v[2] + h]

    sb_w = [[arcB_w[j], arcB_w[j + 1], lift(arcB_w[j + 1], Hc), lift(arcB_w[j], Hc)]
            for j in range(_NSK)]
    sf_w = [[arcF_w[j], arcF_w[j + 1], lift(arcF_w[j + 1], Hc), lift(arcF_w[j], Hc)]
            for j in range(_NSK)]

    finB_w_full = [[hx, D / 2, zr]] + arcB_w + [[tx, D / 2, zr], [tx, D / 2 - Ef, zr],
                                                [hx, D / 2 - Ef, zr]]
    finF_w_full = [[tx, D / 2, zr]] + arcF_w + [[hx, D / 2, zr], [hx, D / 2 + Ef, zr],
                                                [tx, D / 2 + Ef, zr]]
    world = {
        "glue": [[hx + float(p["glue_w"]), 0, 0], [hx, 0, 0],
                 [hx, 0, Hb], [hx + float(p["glue_w"]), 0, Hb]],
        "wallL": [[hx, 0, 0], [hx, D, 0], [hx, D, Hb], [hx, D / 2, zr], [hx, 0, Hb]],
        "back": [[hx, D, 0], [tx, D, 0], [tx, D, Hb], [hx, D, Hb]],
        "wallR": [[tx, D, 0], [tx, 0, 0], [tx, 0, Hb], [tx, D / 2, zr], [tx, D, Hb]],
        "front": [[tx, 0, 0], [hx, 0, 0], [hx, 0, Hb], [tx, 0, Hb]],
        "slopeB": [[hx, D, Hb], [tx, D, Hb], [tx, D / 2, zr], [hx, D / 2, zr]],
        "slopeF": [[tx, 0, Hb], [hx, 0, Hb], [hx, D / 2, zr], [tx, D / 2, zr]],
        "finB": finB_w_full[5:] + finB_w_full[:5],
        "finF": finF_w_full[5:] + finF_w_full[:5],
        "flapF": [[tx, D, 0], [hx, D, 0], [hx, 0, 0], [tx, 0, 0]],
        "flapB": [[hx, 0, 0], [tx, 0, 0], [tx, D, 0], [hx, D, 0]],
        "flapL": [[0, 0, 0], [0, D, 0], [hx, D, 0], [hx, 0, 0]],
        "flapR": [[0, D, 0], [0, 0, 0], [tx, 0, 0], [tx, D, 0]],
    }
    for j in range(_NSK):
        world[f"sb{j}"] = sb_w[j]
        world[f"sf{j}"] = sf_w[j]

    panels = [
        {"id": "glue", "role": "glue", "polygon_2d": _pts([(0, 0), (float(p["glue_w"]), 0),
                                                           (float(p["glue_w"]), Hb), (0, Hb)])},
        {"id": "wallL", "role": "wall", "polygon_2d": _pts(
            [(x1, 0), (x2, 0), (x2, Hb), (x2 - D / 2, Hb + Hr), (x1, Hb)])},
        {"id": "back", "role": "wall", "polygon_2d": _pts(
            [(x2, 0), (x3, 0), (x3, Hb), (x2, Hb)])},
        {"id": "wallR", "role": "wall", "polygon_2d": _pts(
            [(x3, 0), (x4, 0), (x4, Hb), (x4 - D / 2, Hb + Hr), (x3, Hb)])},
        {"id": "front", "role": "wall", "polygon_2d": _pts(
            [(x4, 0), (x5, 0), (x5, Hb), (x4, Hb)])},
        {"id": "slopeB", "role": "slope", "polygon_2d": _pts(
            [(x2, Hb), (x3, Hb), (x3, Hb + s), (x2, Hb + s)])},
        {"id": "finB", "role": "fin", "polygon_2d": _pts(finB_net)},
        {"id": "slopeF", "role": "slope", "polygon_2d": _pts(
            [(x4, Hb), (x5, Hb), (x5, Hb + s), (x4, Hb + s)])},
        {"id": "finF", "role": "fin", "polygon_2d": _pts(finF_net)},
        {"id": "flapF", "role": "flap", "polygon_2d": _pts(
            [(x4, -D), (x5, -D), (x5, 0), (x4, 0)])},
        {"id": "flapB", "role": "flap", "polygon_2d": _pts(
            [(x2, -D), (x3, -D), (x3, 0), (x2, 0)])},
        {"id": "flapL", "role": "flap", "polygon_2d": _pts(
            [(x1, -W / 2), (x2, -W / 2), (x2, 0), (x1, 0)])},
        {"id": "flapR", "role": "flap", "polygon_2d": _pts(
            [(x3, -W / 2), (x4, -W / 2), (x4, 0), (x3, 0)])},
    ]
    for j in range(_NSK):
        panels.append({"id": f"sb{j}", "role": "flap", "polygon_2d": _pts(qB[j])})
    for j in range(_NSK):
        panels.append({"id": f"sf{j}", "role": "flap", "polygon_2d": _pts(qF[j])})

    specs = [
        {"id": "e_glue", "seg": ((x1, 0), (x1, Hb)), "parent": "wallL", "child": "glue",
         "mt": "MOUNTAIN", "wa": [hx, 0, 0], "wb": [hx, 0, Hb]},
        {"id": "e_wl_bk", "seg": ((x2, 0), (x2, Hb)), "parent": "wallL", "child": "back",
         "mt": "VALLEY", "wa": [hx, D, 0], "wb": [hx, D, Hb]},
        {"id": "e_bk_wr", "seg": ((x3, 0), (x3, Hb)), "parent": "back", "child": "wallR",
         "mt": "VALLEY", "wa": [tx, D, 0], "wb": [tx, D, Hb]},
        {"id": "e_wr_ft", "seg": ((x4, 0), (x4, Hb)), "parent": "wallR", "child": "front",
         "mt": "VALLEY", "wa": [tx, 0, 0], "wb": [tx, 0, Hb]},
        {"id": "e_bk_sl", "seg": ((x2, Hb), (x3, Hb)), "parent": "back", "child": "slopeB",
         "mt": "VALLEY", "wa": [hx, D, Hb], "wb": [tx, D, Hb]},
        {"id": "e_ft_sl", "seg": ((x4, Hb), (x5, Hb)), "parent": "front", "child": "slopeF",
         "mt": "VALLEY", "wa": [tx, 0, Hb], "wb": [hx, 0, Hb]},
        {"id": "e_sl_fb", "seg": ((x2, Hb + s), (x3, Hb + s)), "parent": "slopeB",
         "child": "finB", "mt": "MOUNTAIN", "wa": [hx, D / 2, zr], "wb": [tx, D / 2, zr]},
        {"id": "e_sl_ff", "seg": ((x4, Hb + s), (x5, Hb + s)), "parent": "slopeF",
         "child": "finF", "mt": "MOUNTAIN", "wa": [tx, D / 2, zr], "wb": [hx, D / 2, zr]},
        {"id": "e_ft_fl", "seg": ((x4, 0), (x5, 0)), "parent": "front", "child": "flapF",
         "mt": "MOUNTAIN", "wa": [tx, 0, 0], "wb": [hx, 0, 0]},
        {"id": "e_bk_fl", "seg": ((x2, 0), (x3, 0)), "parent": "back", "child": "flapB",
         "mt": "MOUNTAIN", "wa": [hx, D, 0], "wb": [tx, D, 0]},
        {"id": "e_wl_fl", "seg": ((x1, 0), (x2, 0)), "parent": "wallL", "child": "flapL",
         "mt": "MOUNTAIN", "wa": [hx, 0, 0], "wb": [hx, D, 0]},
        {"id": "e_wr_fl", "seg": ((x3, 0), (x4, 0)), "parent": "wallR", "child": "flapR",
         "mt": "MOUNTAIN", "wa": [tx, D, 0], "wb": [tx, 0, 0]},
    ]
    for j in range(_NSK):
        specs.append({"id": f"e_sb{j}", "seg": chB[j], "parent": "finB", "child": f"sb{j}",
                      "mt": "MOUNTAIN", "wa": arcB_w[j], "wb": arcB_w[j + 1]})
        specs.append({"id": f"e_sf{j}", "seg": chF[j], "parent": "finF", "child": f"sf{j}",
                      "mt": "MOUNTAIN", "wa": arcF_w[j], "wb": arcF_w[j + 1]})
    edges = _directed_edges(specs, world)
    return _ir(cls_id, p, panels, edges,
               "旋盖屋顶包: gable 拓扑 + 脊上双平鳍座板(深 "
               f"{Ef:.0f}mm, 半圆缺口对合 {2 * _NSK} 边形圆孔 R={Rc:.1f}mm) + 孔缘 "
               f"{2 * _NSK} 片竖立盖裙(高 {Hc:.1f}mm, 裙缝逐位重合)")


def _screw_closure(ir, world) -> dict:
    """座板环缝 + 圆孔多边形心/半径 + 脊-山墙尖 + 座板平贴 (跨链强判据)."""
    p = ir.package["params"]
    Rc, Hc, Ef = float(p["cap_r"]), float(p["cap_h"]), float(p["Ef"])
    zr = float(p["Hb"]) + float(p["Hr"])
    ctr = np.array([0.0, float(p["D"]) / 2.0, zr])
    res: dict[str, float] = {}

    def d(name, pa, ia, pb, ib):
        res[name] = float(np.linalg.norm(np.asarray(world[pa][ia], float)
                                         - np.asarray(world[pb][ib], float)))

    # 圆孔: 16 弧端点世界像质心落孔心 + 各点落圆 (座板环缝证据)
    ring = [np.asarray(world[f"sb{j}"][0], float) for j in range(_NSK)] + \
           [np.asarray(world[f"sf{j}"][0], float) for j in range(_NSK)]
    res["hole.center_on_axis"] = float(np.linalg.norm(np.mean(ring, axis=0) - ctr))
    res["hole.radius_uniform"] = float(max(abs(float(np.linalg.norm(v - ctr)) - Rc)
                                           for v in ring))
    # 裙缝: 同鳍相邻裙片顶缝逐位 (8 缝) + 跨鳍合拢缝 (2 处)
    seam = [float(np.linalg.norm(np.asarray(world[f"sb{j}"][2], float)
                                 - np.asarray(world[f"sb{j + 1}"][3], float)))
            for j in range(_NSK - 1)]
    seam += [float(np.linalg.norm(np.asarray(world[f"sf{j}"][2], float)
                                  - np.asarray(world[f"sf{j + 1}"][3], float)))
             for j in range(_NSK - 1)]
    seam.append(float(np.linalg.norm(np.asarray(world["sb7"][2], float)
                                     - np.asarray(world["sf0"][3], float))))
    seam.append(float(np.linalg.norm(np.asarray(world["sb0"][3], float)
                                     - np.asarray(world["sf7"][2], float))))
    res["ring.seam_meet"] = float(max(seam))
    # 脊线四重合 (坡-山墙尖)
    d("ridge.gableL", "slopeB", 3, "wallL", 3)
    d("ridge.gableR", "slopeF", 3, "wallR", 3)
    d("ridge.gableL2", "slopeF", 2, "wallL", 3)
    d("ridge.gableR2", "slopeB", 2, "wallR", 3)
    # 座板平鳍: 落 zr 平面 + 远缘深度 (远缘 = y 最小的两顶点, 顶点序旋转无关)
    flat = [abs(float(np.mean(np.asarray(world[q], float)[:, 2])) - zr)
            for q in ("finB", "finF")]
    res["seat.flat_zr"] = float(max(flat))
    fb = np.asarray(world["finB"], float)
    far = fb[fb[:, 1] <= fb[:, 1].min() + 1e-6]
    res["seat.reach"] = float(abs(float(np.mean(far, axis=0)[1])
                                  - (float(p["D"]) / 2 - Ef)))
    # 底封板
    res["flapF.far.mid == flapB.attach.mid"] = float(np.linalg.norm(
        np.mean(world["flapF"][0:2], axis=0) - np.mean(world["flapB"][2:4], axis=0)))
    res["flapL.far.mid == flapR.far.mid"] = float(np.linalg.norm(
        np.mean(world["flapL"][0:2], axis=0) - np.mean(world["flapR"][0:2], axis=0)))
    return res


def _screw_overlap() -> set:
    s = {frozenset({"flapF", "flapB"}), frozenset({"flapL", "flapR"}),
         frozenset({"glue", "front"}), frozenset({"finB", "finF"})}
    ids = [f"sb{j}" for j in range(_NSK)] + [f"sf{j}" for j in range(_NSK)]
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            s.add(frozenset({ids[i], ids[j]}))
    return s


# ----------------------------------------------- 宽鳍缝隙屋顶包 (gable_fin_gap_wide)

WIDE_DEFAULTS = {"W": 45.0, "D": 45.0, "Hb": 100.0, "Hr": 12.0, "Ef": 26.0,
                 "fin_gap": 18.0, "glue_w": 12.0, "board_t": 0.45}


def _wide_geom(p: dict) -> dict:
    W, D, Hb, Hr = float(p["W"]), float(p["D"]), float(p["Hb"]), float(p["Hr"])
    gw, Ef, gap = float(p["glue_w"]), float(p["Ef"]), float(p["fin_gap"])
    s = math.hypot(D / 2.0, Hr)
    x1, x2, x3, x4, x5 = gw, gw + D, gw + D + W, gw + D + W + D, gw + 2 * D + 2 * W
    lean = math.asin(min(0.999, gap / (2.0 * Ef)))  # 鳍自竖直外张角
    return {"W": W, "D": D, "Hb": Hb, "Hr": Hr, "Ef": Ef, "gap": gap, "s": s,
            "lean": lean, "x1": x1, "x2": x2, "x3": x3, "x4": x4, "x5": x5,
            "zr": Hb + Hr, "sln": math.sin(lean), "cls": math.cos(lean)}


def _wide_build(p: dict, cls_id: str) -> dict:
    g = _wide_geom(p)
    W, D, Hb, Hr, Ef, s = g["W"], g["D"], g["Hb"], g["Hr"], g["Ef"], g["s"]
    sln, cls, zr = g["sln"], g["cls"], g["zr"]
    x1, x2, x3, x4, x5 = g["x1"], g["x2"], g["x3"], g["x4"], g["x5"]
    hx, tx = -W / 2.0, W / 2.0
    dy, dz = Ef * sln, Ef * cls  # 鳍顶缘外张偏移

    world = {
        "glue": [[hx + float(p["glue_w"]), 0, 0], [hx, 0, 0],
                 [hx, 0, Hb], [hx + float(p["glue_w"]), 0, Hb]],
        "wallL": [[hx, 0, 0], [hx, D, 0], [hx, D, Hb], [hx, D / 2, zr], [hx, 0, Hb]],
        "back": [[hx, D, 0], [tx, D, 0], [tx, D, Hb], [hx, D, Hb]],
        "wallR": [[tx, D, 0], [tx, 0, 0], [tx, 0, Hb], [tx, D / 2, zr], [tx, D, Hb]],
        "front": [[tx, 0, 0], [hx, 0, 0], [hx, 0, Hb], [tx, 0, Hb]],
        "slopeB": [[hx, D, Hb], [tx, D, Hb], [tx, D / 2, zr], [hx, D / 2, zr]],
        "slopeF": [[tx, 0, Hb], [hx, 0, Hb], [hx, D / 2, zr], [tx, D / 2, zr]],
        "finB": [[hx, D / 2, zr], [tx, D / 2, zr], [tx, D / 2 - dy, zr + dz],
                 [hx, D / 2 - dy, zr + dz]],
        "finF": [[tx, D / 2, zr], [hx, D / 2, zr], [hx, D / 2 + dy, zr + dz],
                 [tx, D / 2 + dy, zr + dz]],
        "flapF": [[tx, D, 0], [hx, D, 0], [hx, 0, 0], [tx, 0, 0]],
        "flapB": [[hx, 0, 0], [tx, 0, 0], [tx, D, 0], [hx, D, 0]],
        "flapL": [[0, 0, 0], [0, D, 0], [hx, D, 0], [hx, 0, 0]],
        "flapR": [[0, D, 0], [0, 0, 0], [tx, 0, 0], [tx, D, 0]],
    }
    panels = [
        {"id": "glue", "role": "glue", "polygon_2d": _pts([(0, 0), (float(p["glue_w"]), 0),
                                                           (float(p["glue_w"]), Hb), (0, Hb)])},
        {"id": "wallL", "role": "wall", "polygon_2d": _pts(
            [(x1, 0), (x2, 0), (x2, Hb), (x2 - D / 2, Hb + Hr), (x1, Hb)])},
        {"id": "back", "role": "wall", "polygon_2d": _pts(
            [(x2, 0), (x3, 0), (x3, Hb), (x2, Hb)])},
        {"id": "wallR", "role": "wall", "polygon_2d": _pts(
            [(x3, 0), (x4, 0), (x4, Hb), (x4 - D / 2, Hb + Hr), (x3, Hb)])},
        {"id": "front", "role": "wall", "polygon_2d": _pts(
            [(x4, 0), (x5, 0), (x5, Hb), (x4, Hb)])},
        {"id": "slopeB", "role": "slope", "polygon_2d": _pts(
            [(x2, Hb), (x3, Hb), (x3, Hb + s), (x2, Hb + s)])},
        {"id": "finB", "role": "fin", "polygon_2d": _pts(
            [(x2, Hb + s), (x3, Hb + s), (x3, Hb + s + Ef), (x2, Hb + s + Ef)])},
        {"id": "slopeF", "role": "slope", "polygon_2d": _pts(
            [(x4, Hb), (x5, Hb), (x5, Hb + s), (x4, Hb + s)])},
        {"id": "finF", "role": "fin", "polygon_2d": _pts(
            [(x4, Hb + s), (x5, Hb + s), (x5, Hb + s + Ef), (x4, Hb + s + Ef)])},
        {"id": "flapF", "role": "flap", "polygon_2d": _pts(
            [(x4, -D), (x5, -D), (x5, 0), (x4, 0)])},
        {"id": "flapB", "role": "flap", "polygon_2d": _pts(
            [(x2, -D), (x3, -D), (x3, 0), (x2, 0)])},
        {"id": "flapL", "role": "flap", "polygon_2d": _pts(
            [(x1, -W / 2), (x2, -W / 2), (x2, 0), (x1, 0)])},
        {"id": "flapR", "role": "flap", "polygon_2d": _pts(
            [(x3, -W / 2), (x4, -W / 2), (x4, 0), (x3, 0)])},
    ]
    specs = [
        {"id": "e_glue", "seg": ((x1, 0), (x1, Hb)), "parent": "wallL", "child": "glue",
         "mt": "MOUNTAIN", "wa": [hx, 0, 0], "wb": [hx, 0, Hb]},
        {"id": "e_wl_bk", "seg": ((x2, 0), (x2, Hb)), "parent": "wallL", "child": "back",
         "mt": "VALLEY", "wa": [hx, D, 0], "wb": [hx, D, Hb]},
        {"id": "e_bk_wr", "seg": ((x3, 0), (x3, Hb)), "parent": "back", "child": "wallR",
         "mt": "VALLEY", "wa": [tx, D, 0], "wb": [tx, D, Hb]},
        {"id": "e_wr_ft", "seg": ((x4, 0), (x4, Hb)), "parent": "wallR", "child": "front",
         "mt": "VALLEY", "wa": [tx, 0, 0], "wb": [tx, 0, Hb]},
        {"id": "e_bk_sl", "seg": ((x2, Hb), (x3, Hb)), "parent": "back", "child": "slopeB",
         "mt": "VALLEY", "wa": [hx, D, Hb], "wb": [tx, D, Hb]},
        {"id": "e_ft_sl", "seg": ((x4, Hb), (x5, Hb)), "parent": "front", "child": "slopeF",
         "mt": "VALLEY", "wa": [tx, 0, Hb], "wb": [hx, 0, Hb]},
        {"id": "e_sl_fb", "seg": ((x2, Hb + s), (x3, Hb + s)), "parent": "slopeB",
         "child": "finB", "mt": "MOUNTAIN", "wa": [hx, D / 2, zr], "wb": [tx, D / 2, zr]},
        {"id": "e_sl_ff", "seg": ((x4, Hb + s), (x5, Hb + s)), "parent": "slopeF",
         "child": "finF", "mt": "MOUNTAIN", "wa": [tx, D / 2, zr], "wb": [hx, D / 2, zr]},
        {"id": "e_ft_fl", "seg": ((x4, 0), (x5, 0)), "parent": "front", "child": "flapF",
         "mt": "MOUNTAIN", "wa": [tx, 0, 0], "wb": [hx, 0, 0]},
        {"id": "e_bk_fl", "seg": ((x2, 0), (x3, 0)), "parent": "back", "child": "flapB",
         "mt": "MOUNTAIN", "wa": [hx, D, 0], "wb": [tx, D, 0]},
        {"id": "e_wl_fl", "seg": ((x1, 0), (x2, 0)), "parent": "wallL", "child": "flapL",
         "mt": "MOUNTAIN", "wa": [hx, 0, 0], "wb": [hx, D, 0]},
        {"id": "e_wr_fl", "seg": ((x3, 0), (x4, 0)), "parent": "wallR", "child": "flapR",
         "mt": "MOUNTAIN", "wa": [tx, D, 0], "wb": [tx, 0, 0]},
    ]
    edges = _directed_edges(specs, world)
    return _ir(cls_id, p, panels, edges,
               f"宽鳍缝隙屋顶包: V 形张开双立鳍 (高 Ef={Ef:.0f}mm, 外张 "
               f"{math.degrees(g['lean']):.1f}°, 鳍顶距 fin_gap={g['gap']:.0f}mm)")


def _wide_closure(ir, world) -> dict:
    """鳍距自洽 (3D 鳍顶距 == fin_gap) + 鳍高 + 脊线四重合 + 底封板."""
    p = ir.package["params"]
    Ef, gap = float(p["Ef"]), float(p["fin_gap"])
    g = _wide_geom(p)
    zr = float(p["Hb"]) + float(p["Hr"])
    res: dict[str, float] = {}

    def d(name, pa, ia, pb, ib):
        res[name] = float(np.linalg.norm(np.asarray(world[pa][ia], float)
                                         - np.asarray(world[pb][ib], float)))

    topB = np.asarray(world["finB"][2:4], float)
    topF = np.asarray(world["finF"][2:4], float)
    res["fin.gap_self"] = float(abs(
        float(np.linalg.norm(np.mean(topB, axis=0) - np.mean(topF, axis=0))) - gap))
    res["fin.heightB"] = float(abs(
        float(np.mean(topB, axis=0)[2]) - (zr + Ef * g["cls"])))
    res["fin.heightF"] = float(abs(
        float(np.mean(topF, axis=0)[2]) - (zr + Ef * g["cls"])))
    d("ridge.gableL", "slopeB", 3, "wallL", 3)
    d("ridge.gableR", "slopeF", 3, "wallR", 3)
    d("ridge.gableL2", "slopeF", 2, "wallL", 3)
    d("ridge.gableR2", "slopeB", 2, "wallR", 3)
    res["ridge.slope_meet"] = float(max(
        float(np.linalg.norm(np.asarray(world["slopeB"][2], float)
                             - np.asarray(world["slopeF"][3], float))),
        float(np.linalg.norm(np.asarray(world["slopeB"][3], float)
                             - np.asarray(world["slopeF"][2], float)))))
    res["flapF.far.mid == flapB.attach.mid"] = float(np.linalg.norm(
        np.mean(world["flapF"][0:2], axis=0) - np.mean(world["flapB"][2:4], axis=0)))
    res["flapL.far.mid == flapR.far.mid"] = float(np.linalg.norm(
        np.mean(world["flapL"][0:2], axis=0) - np.mean(world["flapR"][0:2], axis=0)))
    return res


def _wide_overlap() -> set:
    return {frozenset({"flapF", "flapB"}), frozenset({"flapL", "flapR"}),
            frozenset({"glue", "front"})}


# ------------------------------------------------------------ 注册与分发

_CLASS_DEFAULTS = {
    "aseptic_brick": BRICK_DEFAULTS,
    "brick_250ml": BRICK250_DEFAULTS,
    "gable_screw_cap": SCREW_DEFAULTS,
    "gable_fin_gap_wide": WIDE_DEFAULTS,
}

_BUILDERS = {
    "aseptic_brick": (_brick_build, _brick_closure, _brick_overlap),
    "brick_250ml": (_brick_build, _brick_closure, _brick_overlap),
    "gable_screw_cap": (_screw_build, _screw_closure, _screw_overlap),
    "gable_fin_gap_wide": (_wide_build, _wide_closure, _wide_overlap),
}


def _full_params(cls_id: str) -> dict:
    p = {k: 0.0 for k in PARAM_ORDER}
    p.update({k: float(v) for k, v in _CLASS_DEFAULTS[cls_id].items()})
    return p


def class_params(cls_id: str) -> dict:
    """类ID → 该类全键参数表 (批量 build_ir 判型与取值的唯一权威)."""
    if cls_id not in _CLASS_DEFAULTS:
        raise KeyError(f"未知类ID: {cls_id}")
    return _full_params(cls_id)


def _infer_cls(params: dict) -> str:
    merged = {**DEFAULTS, **(params or {})}
    for cid in _CLASS_DEFAULTS:
        if all(abs(float(merged[k]) - float(_full_params(cid)[k])) < 1e-9
               for k in PARAM_ORDER):
            return cid
    if float(merged.get("cap_r", 0) or 0) > 0:
        return "gable_screw_cap"
    if float(merged.get("fin_gap", 0) or 0) > 0:
        return "gable_fin_gap_wide"
    return "aseptic_brick"


def _pos(params: dict, *keys):
    for k in keys:
        v = params.get(k)
        if v is None or not isinstance(v, (int, float)) or isinstance(v, bool) or v <= 0:
            raise ValueError(f"非法参数 {k}={v!r} (须正数)")


def validate_params(params: dict) -> None:
    merged = {**DEFAULTS, **(params or {})}
    cid = _infer_cls(params)
    _pos(merged, "glue_w", "board_t")
    if cid in ("aseptic_brick", "brick_250ml"):
        _pos(merged, "W", "D", "Hb", "hr")
        if merged["hr"] >= merged["Hb"]:
            raise ValueError("砖盒须 hr < Hb (斜肩高不得超墙高)")
    elif cid == "gable_screw_cap":
        _pos(merged, "W", "D", "Hb", "Hr", "Ef", "cap_r", "cap_h")
        if merged["cap_r"] > min(merged["Ef"], merged["W"] / 2.0):
            raise ValueError("旋盖座孔须 cap_r ≤ min(Ef, W/2) (孔落在座板内)")
        if merged["cap_h"] >= merged["cap_r"]:
            raise ValueError("旋盖须 cap_h < cap_r (盖裙网内不越孔心)")
    else:
        _pos(merged, "W", "D", "Hb", "Hr", "Ef", "fin_gap")
        if merged["fin_gap"] >= 2.0 * merged["Ef"]:
            raise ValueError("宽鳍须 fin_gap < 2*Ef (外张角域 asin)")


def build_ir(params: dict | None = None, cls_id: str | None = None) -> dict:
    """契约入口; 类ID 由参数表精确匹配判型 (缺省 aseptic_brick), 可显式覆盖."""
    p = {**DEFAULTS, **(params or {})}
    cid = cls_id or _infer_cls(p)
    return _BUILDERS[cid][0]({**DEFAULTS, **p}, cid)


def analytic_bbox(params: dict) -> dict:
    p = {**DEFAULTS, **(params or {})}
    cid = _infer_cls(p)
    if cid in ("aseptic_brick", "brick_250ml"):
        W, D, Hb, hr = float(p["W"]), float(p["D"]), float(p["Hb"]), float(p["hr"])
        return {"W": float(W + D), "D": float(D), "H": float(Hb + 2 * hr)}
    return {"W": float(p["W"]), "D": float(p["D"]),
            "H": float(p["Hb"]) + float(p["Hr"])}


def closure_checks(ir, world) -> dict:
    cid = ir.package["template"]["id"]
    return _BUILDERS[cid][1](ir, world)


def allowed_overlap() -> set:
    s: set = set()
    for hooks in _BUILDERS.values():
        s |= hooks[2]()
    return s


def solid_roles() -> tuple:
    return ("wall", "slope")
