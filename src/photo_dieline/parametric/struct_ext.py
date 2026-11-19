"""struct_ext: 结构扩展七类 (动物园收官波 87..93).

类ID:
  prism_tuck_window   插盖开窗正六棱柱: generic_prism tuck 变体 (n=6), 墙链首墙拆窗框
                      4 条绕折共面 (窗洞 → 网并集=带孔单环) + 星形底板/星形插盖
  gable_window_front  开窗前墙屋顶包: gable_top 同构, 前墙拆窗框 4 条绕折共面
                      (坡面改挂窗框顶条 wt, 环缝 = wallL 近棱 ↔ fb/wt 远棱)
  rsc_handhole        提手孔 RSC: FEFCO 0201 前墙顶缘下方 U 形凹口 (顶缘缺口模式,
                      参照 hanger_box 挂孔; 网并集 = 带孔单环, 顶折翼全宽越过缺口)
  crashlock_divider   带隔板顺央底盒: crashlock 互锁底 (tray_family 同款) + 盒内
                      十字隔板 (纵隔全宽 × 横隔全深 T 字相贯, 自底板铰链立起)
  tube_cap_end        卷轴端盖管: tube_glue 16 边形直管 + 一端 8 片内折星盘 (交替墙位
                      三角片, 片尖互抵轴线) + 另一端外翻缘环带 (16 片窄带外折 90°)
  mailer_rigid_pad    硬衬邮寄盒: mailer_bookwrap 三件 + 内衬硬垫片 (180° 反贴左盖
                      内面, 面内共面第二层) + 插舌封盖 (可决式)
  tray_domelid        拱盖托盘: tray_4corner 四角粘合盘 + 后墙铰链 k 段弧折拱盖
                      (半圆弧弦线近似, 参照 pillow_box) + 前墙内扣唇 (前扣)

世界系/铰链/tdir 语义与 box_essentials / generic_prism / gable_top / tray_family /
odd_family / special_shapes 一致; closure 全部为折叠后世界坐标残差 (远缘重合/抵轴线/
共面贴合), 无构造恒等量; 负探针绕真实世界铰链轴 Rodrigues 扰动 tdir。
"""
from __future__ import annotations

import copy
import math

import numpy as np

from . import base as _base

PARAM_ORDER = ["kind", "W", "D", "H", "Hb", "Hr", "Ef", "fin_gap_mm", "glue_w",
               "board_t", "side", "h", "bw", "tw_s", "lw", "flap_ratio", "hw",
               "hh", "dv_x", "dv_h", "rf", "spine_w", "cover_w", "tuck_t",
               "pad_d", "dome_k", "lip_d"]

DEFAULTS = {k: 0.0 for k in PARAM_ORDER}
DEFAULTS.update({"board_t": 0.45, "dome_k": 4})

_CLS = ("prism_tuck_window", "gable_window_front", "rsc_handhole",
        "crashlock_divider", "tube_cap_end", "mailer_rigid_pad", "tray_domelid")
_KIND = {c: i for i, c in enumerate(_CLS)}

for _cid in _CLS:
    _base.register(_cid, "struct_ext")

_R_CHAIN = [[1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0]]   # net(x,y)→world(x,0,y)
_R_GABLE = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]   # net(x,y)→world(0,x,y)
_R_STAR = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]    # net(x,y)→world(x,y,0)


# ---------------------------------------------------------------- helpers
def _rect(pid: str, role: str, xa, ya, xb, yb) -> dict:
    """矩形板 CCW: [左下,右下,右上,左上]."""
    return {"id": pid, "role": role,
            "polygon_2d": [[float(xa), float(ya)], [float(xb), float(ya)],
                           [float(xb), float(yb)], [float(xa), float(yb)]]}


def _poly(pid: str, role: str, pts) -> dict:
    return {"id": pid, "role": role,
            "polygon_2d": [[float(x), float(y)] for x, y in pts]}


def _fold(eid, a2, b2, parent, child, tdir, mt="VALLEY") -> dict:
    return {"id": eid, "kind": "FOLD",
            "seg_2d": [[float(a2[0]), float(a2[1])], [float(b2[0]), float(b2[1])]],
            "fold": {"mt_va": mt, "parent": parent, "child": child,
                     "target_dir_3d": [round(float(v), 9) for v in tdir]}}


def _features(*glue_panels) -> list:
    fs = [{"id": f"f_g{i}", "kind": "GLUE_TAB", "panel_id": g}
          for i, g in enumerate(glue_panels)]
    fs += [{"id": "f_bleed", "kind": "BLEED", "offset_mm": 3.0},
           {"id": "f_check", "kind": "CHECK_BAR", "length_mm": 50.0},
           {"id": "f_reg", "kind": "REGISTRATION"}]
    return fs


def _poly_ring(n: int, side: float, cx: float, cy: float):
    """正 n 边形顶点 (edge0 落 y=0, x∈[0,side]); 返回顶点/外法线/切向/内切半径."""
    R = side / (2.0 * math.sin(math.pi / n))
    a = side / (2.0 * math.tan(math.pi / n))
    ctr = np.array([cx, cy])
    vs = [ctr + R * np.array([math.cos(-math.pi / 2 - math.pi / n + 2.0 * math.pi * k / n),
                              math.sin(-math.pi / 2 - math.pi / n + 2.0 * math.pi * k / n)])
          for k in range(n)]
    outward, tangent = [], []
    for k in range(n):
        em = (vs[k] + vs[(k + 1) % n]) / 2.0
        o = em - ctr
        o = o / np.linalg.norm(o)
        outward.append(o)
        tangent.append(np.array([-o[1], o[0]]))
    return vs, outward, tangent, a


def _ring_bbox(n: int, side: float, h: float) -> dict:
    vs, _, _, _ = _poly_ring(n, side, side / 2.0, side / (2.0 * math.tan(math.pi / n)))
    xs = [v[0] for v in vs]
    ys = [v[1] for v in vs]
    return {"W": float(max(xs) - min(xs)), "D": float(max(ys) - min(ys)), "H": float(h)}


def _frame_parts(xa, xb, h, bw, tw, lw_):
    """窗框 4 条几何 (box_essentials window_box 同款, 挂 [xa,xb]×[0,h] 墙位):
    返回 (fb, wl, wt, wr) 面板 + (e_wl, e_wt, e_wr) 共面绕折链 (tdir 零转平折)."""
    win_h = h - bw - tw
    fb = _poly("fb", "wall", [(xa, 0), (xb, 0), (xb, bw), (xa + lw_, bw), (xa, bw)])
    wl = _rect("wl", "wall", xa, bw, xa + lw_, bw + win_h)
    wt = _poly("wt", "wall", [(xa, h), (xa, bw + win_h), (xa + lw_, bw + win_h),
                              (xb - lw_, bw + win_h), (xb, bw + win_h), (xb, h)])
    wr = _rect("wr", "wall", xb - lw_, bw, xb, bw + win_h)
    e_wl = _fold("e_wl", (xa, bw), (xa + lw_, bw), "fb", "wl", (0.0, 0.0, 1.0), "MOUNTAIN")
    e_wt = _fold("e_wt", (xa, bw + win_h), (xa + lw_, bw + win_h), "wl", "wt",
                 (0.0, 0.0, 1.0), "MOUNTAIN")
    e_wr = _fold("e_wr", (xb - lw_, bw + win_h), (xb, bw + win_h), "wt", "wr",
                 (0.0, 0.0, -1.0), "MOUNTAIN")
    return [fb, wl, wt, wr], [e_wl, e_wt, e_wr], win_h


# ---------------------------------------------------------- ① prism_tuck_window
def _build_prism_win(p):
    n, side, h, gw = 6, float(p["side"]), float(p["h"]), float(p["glue_w"])
    bw, tw, lw_ = float(p["bw"]), float(p["tw_s"]), float(p["lw"])
    a = side / (2.0 * math.tan(math.pi / n))
    xs = [gw + i * side for i in range(n + 1)]
    vs, outward, tangent, _ = _poly_ring(n, side, side / 2.0, a)
    face5 = (vs[5] - vs[0]) / side      # w5 面宽方向 (自角缝 verts[0] 指向 verts[5])

    panels = [_poly("glue", "glue", [(0, 0), (xs[0], 0), (xs[0], bw), (xs[0], h), (0, h)])]
    fpan, fed, win_h = _frame_parts(xs[0], xs[1], h, bw, tw, lw_)
    panels += fpan
    edges = [_fold("e_g", (xs[0], 0), (xs[0], bw), "fb", "glue",
                   (float(face5[0]), float(face5[1]), 0.0), "MOUNTAIN"),
             _fold("e_w01", (xs[1], 0), (xs[1], bw), "fb", "w1", (*tangent[1], 0.0))]
    edges += fed
    # w1 近棱带 bw 分点 (窗框底条仅占下段); w2..w5 全高
    panels.append(_poly("w1", "wall", [(xs[1], 0), (xs[2], 0), (xs[2], h),
                                       (xs[1], h), (xs[1], bw)]))
    for i in range(2, n):
        panels.append(_rect(f"w{i}", "wall", xs[i], 0.0, xs[i + 1], h))
    for i in range(1, n - 1):
        edges.append(_fold(f"e_w{i}", (xs[i + 1], 0), (xs[i + 1], h), f"w{i}",
                           f"w{i + 1}", (*tangent[i + 1], 0.0)))
    # 星形底板 + 星形插盖 (generic_prism tuck 同款, 折入深 = apothem)
    for i in range(n):
        panels.append(_rect(f"b{i}", "flap", xs[i], -a, xs[i + 1], 0.0))
        panels.append(_rect(f"t{i}", "flap", xs[i], h, xs[i + 1], h + a))
        edges.append(_fold(f"e_b{i}", (xs[i], 0), (xs[i + 1], 0),
                           "fb" if i == 0 else f"w{i}", f"b{i}",
                           (*(-outward[i]), 0.0), "MOUNTAIN"))
        edges.append(_fold(f"e_t{i}", (xs[i], h), (xs[i + 1], h),
                           "wt" if i == 0 else f"w{i}", f"t{i}",
                           (*(-outward[i]), 0.0), "MOUNTAIN"))
    notes = (f"prism_tuck_window: 正{n}棱柱插盖开窗盒 — 墙链首墙拆窗框 4 条 "
             f"(底 {bw:g}/左 {lw_:g}/顶 {tw:g}/右 {lw_:g}) 绕线平折共面, 窗洞 "
             f"{side - 2 * lw_:g}×{win_h:g} (网并集=带孔单环); 星形底板/星形插盖各 {n} 片 "
             f"折入深 apothem={a:.2f}mm, 片远缘中线互抵轴线")
    return panels, edges, notes, _features("glue"), "fb", _R_CHAIN, [-gw, 0.0, 0.0]


def _closure_prism(ir, world) -> dict:
    n, side, h = 6, float(ir.param("side")), float(ir.param("h"))
    bw = float(ir.param("bw"))
    a = side / (2.0 * math.tan(math.pi / n))
    ctr = np.array([side / 2.0, a, 0.0])
    top = np.array([side / 2.0, a, h])
    _, outward, _, _ = _poly_ring(n, side, side / 2.0, a)
    res: dict[str, float] = {}
    for i in range(n):
        res[f"b{i}.far_to_axis"] = float(np.linalg.norm(
            np.mean(world[f"b{i}"][0:2], axis=0) - ctr))
        res[f"t{i}.far_to_axis"] = float(np.linalg.norm(
            np.mean(world[f"t{i}"][2:4], axis=0) - top))
    for pid in ("fb", "wl", "wt", "wr"):
        res[f"frame.{pid}.plane"] = abs(float(np.mean(np.asarray(world[pid]), axis=0)[1]))
    # 环缝 (跨链): 末墙自由棱 (net 远棱 idx1/idx2) ↔ 窗框底条/顶条左缘
    res["seam.bot"] = float(np.linalg.norm(np.asarray(world["w5"][1], float)
                                           - world["fb"][0]))
    res["seam.top"] = float(np.linalg.norm(np.asarray(world["w5"][2], float)
                                           - world["wt"][0]))
    res["frame.right_bot"] = abs(float(world["wr"][0][2]) - bw)
    # glue 落 w5 内面 (平面过原点, 法向 = edge5 外法线)
    n5 = np.array([*outward[5], 0.0])
    res["glue.flush_w5"] = float(np.max(np.abs(
        np.asarray(world["glue"], float) @ n5)))
    return res


# ---------------------------------------------------------- ② gable_window_front
def _build_gable_win(p):
    W, D, Hb, Hr = float(p["W"]), float(p["D"]), float(p["Hb"]), float(p["Hr"])
    Ef, gap, gw = float(p["Ef"]), float(p["fin_gap_mm"]), float(p["glue_w"])
    bw, tw, lw_ = float(p["bw"]), float(p["tw_s"]), float(p["lw"])
    s = math.hypot(D / 2.0, Hr)
    win_h = Hb - bw - tw
    x1 = gw
    x2, x3, x4, x5 = x1 + D, x1 + D + W, x1 + D + W + D, x1 + 2 * D + 2 * W

    lean = math.asin(min(1.0, (gap / 2) / Ef)) if Ef > 0 else 0.0

    def rect(pid, role, xa, xb, ya, yb):
        return {"id": pid, "role": role,
                "polygon_2d": [[xa, ya], [xb, ya], [xb, yb], [xa, yb]]}

    panels = [
        rect("glue", "glue", 0.0, x1, 0.0, Hb),
        {"id": "wallL", "role": "wall", "polygon_2d": [
            [x1, 0], [x2, 0], [x2, Hb], [x2 - D / 2, Hb + Hr], [x1, Hb]]},
        rect("back", "wall", x2, x3, 0.0, Hb),
        # wallR 近棱带 bw 分点 (窗框底条仅占下段); 首三元组非共线
        {"id": "wallR", "role": "wall", "polygon_2d": [
            [x3, 0], [x4, 0], [x4, bw], [x4, Hb], [x4 - D / 2, Hb + Hr], [x3, Hb]]},
    ]
    fpan, fed, _ = _frame_parts(x4, x5, Hb, bw, tw, lw_)
    panels += fpan
    panels += [
        rect("slopeB", "slope", x2, x3, Hb, Hb + s),
        rect("finB", "fin", x2, x3, Hb + s, Hb + s + Ef),
        rect("slopeF", "slope", x4, x5, Hb, Hb + s),
        rect("finF", "fin", x4, x5, Hb + s, Hb + s + Ef),
        rect("flapF", "flap", x4, x5, -D, 0.0),
        rect("flapB", "flap", x2, x3, -D, 0.0),
        rect("flapL", "flap", x1, x2, -W / 2.0, 0.0),
        rect("flapR", "flap", x3, x4, -W / 2.0, 0.0),
    ]
    edges = [
        _fold("e_glue", (x1, 0), (x1, Hb), "wallL", "glue", (1.0, 0.0, 0.0), "MOUNTAIN"),
        _fold("e_wl_bk", (x2, 0), (x2, Hb), "wallL", "back", (1.0, 0.0, 0.0)),
        _fold("e_bk_wr", (x3, 0), (x3, Hb), "back", "wallR", (0.0, -1.0, 0.0)),
        # wallR → 窗框底条 fb (仅下段 bw; 原前墙全高折线改分段)
        _fold("e_wr_fb", (x4, 0), (x4, bw), "wallR", "fb", (-1.0, 0.0, 0.0)),
    ]
    edges += fed
    edges += [
        # 坡面: 背坡挂 back 顶缘; 前坡改挂窗框顶条 wt (顶条全宽越过框)
        _fold("e_bk_sl", (x2, Hb), (x3, Hb), "back", "slopeB",
              (0.0, -D / 2 / s, Hr / s)),
        _fold("e_ft_sl", (x4, Hb), (x5, Hb), "wt", "slopeF",
              (0.0, D / 2 / s, Hr / s)),
        _fold("e_sl_fb", (x2, Hb + s), (x3, Hb + s), "slopeB", "finB",
              (0.0, -math.sin(lean), math.cos(lean)), "MOUNTAIN"),
        _fold("e_sl_ff", (x4, Hb + s), (x5, Hb + s), "slopeF", "finF",
              (0.0, math.sin(lean), math.cos(lean)), "MOUNTAIN"),
        _fold("e_fb_fl", (x4, 0), (x5, 0), "fb", "flapF", (0.0, 1.0, 0.0), "MOUNTAIN"),
        _fold("e_bk_fl", (x2, 0), (x3, 0), "back", "flapB", (0.0, -1.0, 0.0), "MOUNTAIN"),
        _fold("e_wl_fl", (x1, 0), (x2, 0), "wallL", "flapL", (1.0, 0.0, 0.0), "MOUNTAIN"),
        _fold("e_wr_fl", (x3, 0), (x4, 0), "wallR", "flapR", (-1.0, 0.0, 0.0), "MOUNTAIN"),
    ]
    notes = (f"gable_window_front: 开窗前墙屋顶包 — gable_top 同构, 前墙拆窗框 4 条 "
             f"(底 {bw:g}/左 {lw_:g}/顶 {tw:g}/右 {lw_:g}) 绕折共面, 窗洞 "
             f"{W - 2 * lw_:g}×{win_h:g} (网并集=带孔单环); 前坡改挂窗框顶条全宽, "
             f"环缝 = wallL 近棱 ↔ fb/wt 远棱; 过脊鳍距 {gap:g}mm")
    return panels, edges, notes, _features("glue"), "wallL", _R_GABLE, [-W / 2.0, -gw, 0.0]


def _closure_gable(ir, world) -> dict:
    W, D = float(ir.param("W")), float(ir.param("D"))
    bw = float(ir.param("bw"))
    res: dict[str, float] = {}

    def pair(name, pa, ia, pb, ib):
        res[name] = float(np.linalg.norm(np.asarray(world[pa][ia], float)
                                         - np.asarray(world[pb][ib], float)))

    # 屋顶闭合 (wallR 带 bw 分点 → 脊顶/前顶角索引 +1)
    pair("slopeB.ridge.L", "slopeB", 3, "wallL", 3)
    pair("slopeF.ridge.R", "slopeF", 3, "wallR", 4)
    pair("slopeB.ridge.R", "slopeB", 2, "wallR", 4)
    pair("slopeF.ridge.L", "slopeF", 2, "wallL", 3)
    pair("wallL.top.B", "wallL", 2, "slopeB", 0)
    pair("wallR.top.F", "wallR", 3, "slopeF", 0)
    res["flapF.far.mid"] = float(np.linalg.norm(
        np.mean(world["flapF"][0:2], axis=0) - np.mean(world["flapB"][2:4], axis=0)))
    res["flapL.far.mid"] = float(np.linalg.norm(
        np.mean(world["flapL"][0:2], axis=0) - np.mean(world["flapR"][0:2], axis=0)))
    res["flapL.far.x0"] = abs(float(np.mean(world["flapL"][0:2], axis=0)[0]))
    res["flapR.far.x0"] = abs(float(np.mean(world["flapR"][0:2], axis=0)[0]))
    # 窗框: 全框共面前墙平面 (y=0) + 环缝 (wallL 近棱 ↔ fb/wt 远棱)
    for pid in ("fb", "wl", "wt", "wr"):
        res[f"frame.{pid}.plane"] = abs(float(np.mean(np.asarray(world[pid]), axis=0)[1]))
    res["seam.bot"] = float(np.linalg.norm(np.asarray(world["wallL"][0], float)
                                           - world["fb"][1]))
    res["seam.top"] = float(np.linalg.norm(np.asarray(world["wallL"][4], float)
                                           - world["wt"][5]))
    res["frame.left_bot"] = abs(float(world["wr"][0][2]) - bw)
    return res


# ---------------------------------------------------------- ③ rsc_handhole
def _build_rsc_hand(p):
    W, D, H = float(p["W"]), float(p["D"]), float(p["H"])
    r, gw = float(p["flap_ratio"]), float(p["glue_w"])
    hw, hh = float(p["hw"]), float(p["hh"])
    dm, dn = r * D, r * W
    x1, x2, x3, x4, x5 = gw, gw + W, gw + W + D, gw + 2 * W + D, gw + 2 * W + 2 * D
    xc0, xc2 = gw + W / 2.0, x3 + W / 2.0

    def rect(pid, role, xa, xb, ya, yb):
        return {"id": pid, "role": role,
                "polygon_2d": [[xa, ya], [xb, ya], [xb, yb], [xa, yb]]}

    # 前墙 w0: 顶缘下方 U 形凹口 (提手孔, 顶缘缺口多边形, 顶点序含缺口 8 顶点)
    panels = [
        rect("glue", "glue", 0.0, gw, 0.0, H),
        {"id": "w0", "role": "wall", "polygon_2d": [
            [x1, 0], [x2, 0], [x2, H], [xc0 + hw, H], [xc0 + hw, H - hh],
            [xc0 - hw, H - hh], [xc0 - hw, H], [x1, H]]},
        rect("w1", "wall", x2, x3, 0.0, H),
        rect("w2", "wall", x3, x4, 0.0, H),
        rect("w3", "wall", x4, x5, 0.0, H),
        rect("t0", "flap", x1, x2, H, H + dm),
        rect("t1", "flap", x2, x3, H, H + dn),
        rect("t2", "flap", x3, x4, H, H + dm),
        rect("t3", "flap", x4, x5, H, H + dn),
        rect("b0", "flap", x1, x2, -dm, 0.0),
        rect("b1", "flap", x2, x3, -dn, 0.0),
        rect("b2", "flap", x3, x4, -dm, 0.0),
        rect("b3", "flap", x4, x5, -dn, 0.0),
    ]

    def fold(eid, a2, b2, parent, child, tdir):
        return {"id": eid, "kind": "FOLD", "seg_2d": [list(a2), list(b2)],
                "fold": {"mt_va": "MOUNTAIN", "parent": parent, "child": child,
                         "target_dir_3d": [float(v) for v in tdir]}}

    edges = [
        _fold("e_glue", (gw, 0), (gw, H), "w0", "glue", (0.0, 1.0, 0.0), "MOUNTAIN"),
        _fold("e_w01", (x2, 0), (x2, H), "w0", "w1", (0.0, 1.0, 0.0)),
        _fold("e_w12", (x3, 0), (x3, H), "w1", "w2", (-1.0, 0.0, 0.0)),
        _fold("e_w23", (x4, 0), (x4, H), "w2", "w3", (0.0, -1.0, 0.0)),
        fold("e_b0", (x1, 0), (x2, 0), "w0", "b0", (0.0, 1.0, 0.0)),
        fold("e_b1", (x2, 0), (x3, 0), "w1", "b1", (-1.0, 0.0, 0.0)),
        fold("e_b2", (x3, 0), (x4, 0), "w2", "b2", (0.0, -1.0, 0.0)),
        fold("e_b3", (x4, 0), (x5, 0), "w3", "b3", (1.0, 0.0, 0.0)),
        fold("e_t0", (x1, H), (x2, H), "w0", "t0", (0.0, 1.0, 0.0)),
        fold("e_t1", (x2, H), (x3, H), "w1", "t1", (-1.0, 0.0, 0.0)),
        fold("e_t2", (x3, H), (x4, H), "w2", "t2", (0.0, -1.0, 0.0)),
        fold("e_t3", (x4, H), (x5, H), "w3", "t3", (1.0, 0.0, 0.0)),
    ]
    notes = (f"rsc_handhole: 提手孔 RSC (FEFCO 0201) — 4 墙环 + 顶/底折翼各 4 片 "
             f"(大翼深 {dm:g}=ratio*D, 小翼深 {dn:g}=ratio*W); 前墙顶缘下方 U 形凹口 "
             f"{2 * hw:g}×{hh:g} 为提手孔 (顶缘缺口多边形, 顶折翼 t0 全宽越过缺口)")
    return panels, edges, notes, _features("glue"), "w0", _R_CHAIN, [-gw, 0.0, 0.0]


def _closure_rsc(ir, world) -> dict:
    W, D, H = float(ir.param("W")), float(ir.param("D")), float(ir.param("H"))
    gw = float(ir.param("glue_w"))
    hw, hh = float(ir.param("hw")), float(ir.param("hh"))

    def fm(pid, i, j):
        return (np.asarray(world[pid][i], float) + np.asarray(world[pid][j], float)) / 2.0

    def d(a, b) -> float:
        return float(np.linalg.norm(np.asarray(a, float) - np.asarray(b, float)))

    res: dict[str, float] = {}
    res["ring.w3_to_w0"] = d(fm("w3", 1, 2), fm("w0", 0, 7))  # w0 顶点序含缺口
    res["glue.seat_x0"] = abs(float(fm("glue", 0, 3)[0]))
    res["glue.far_y"] = abs(float(fm("glue", 0, 3)[1]) - gw)
    for pre in ("t", "b"):
        maj, mnr = f"{pre}0", f"{pre}2"
        fmaj = fm(maj, 2, 3) if pre == "t" else fm(maj, 0, 1)
        zmaj = H if pre == "t" else 0.0
        res[f"{pre}_major.z"] = max(abs(float(fmaj[2]) - zmaj),
                                    abs(float(fm(mnr, 2, 3)[2] if pre == "t"
                                             else fm(mnr, 0, 1)[2]) - zmaj))
        res[f"{pre}_major.level"] = abs(float(fmaj[2])
                                        - float(fm(mnr, 2, 3)[2] if pre == "t"
                                                else fm(mnr, 0, 1)[2]))
    # 提手孔: 缺口底缘高度 / 居中 / 落前墙平面
    w0 = np.asarray(world["w0"], float)
    res["hole.bottom_z"] = abs(float((w0[4] + w0[5])[2] / 2.0) - (H - hh))
    res["hole.center_x"] = abs(float((w0[3][0] + w0[6][0]) / 2.0) - W / 2.0)
    res["hole.plane_y0"] = abs(float(np.mean(w0[:, 1])))
    return res


# ------------------------------------------------- ④ crashlock_divider
def _crashlock_ratios(W, D):
    """互锁翼折线比例 (tray_family 同款): hd(翼深), ya/yb(折线两端高度)."""
    hd = W / 2.0
    s = 0.5333 * D
    c = s * s / (hd * hd + s * s)
    ya = max(0.4 * D, ((1 - 2 * c) / (2 - 2 * c) + 0.02) * D)
    return hd, ya, ya + s


def _build_crashlock_div(p):
    W, D, H, gw = float(p["W"]), float(p["D"]), float(p["H"]), float(p["glue_w"])
    dv_x, dv_h = float(p["dv_x"]), float(p["dv_h"])
    hd, ya, yb = _crashlock_ratios(W, D)

    def _mirror_ok():
        d = np.array([hd, yb - ya])
        for q in (np.array([0.0, D]), np.array([hd, D])):
            v = q - np.array([0.0, ya])
            t = float(v @ d) / float(d @ d)
            m = 2 * (np.array([0.0, ya]) + t * d) - q
            if not (-1e-6 <= m[0] <= W + 1e-6 and -1e-6 <= m[1] <= D + 1e-6):
                return False
        return True

    if not _mirror_ok():
        raise ValueError(f"crashlock 镜像翼越界: W={W} D={D} (需 W/D ∈ [1.1, 2.4] 左右)")

    def _poly(pid, role, pts):
        return {"id": pid, "role": role,
                "polygon_2d": [[float(x), float(y)] for x, y in pts]}

    def _refl2(pt, a, b):
        pt, a, b = (np.asarray(v, float) for v in (pt, a, b))
        d = b[:2] - a[:2]
        v = pt[:2] - a[:2]
        r = a[:2] + 2.0 * float(v @ d) / float(d @ d) * d - v
        return np.array([r[0], r[1], 0.0])

    def _perp3(v, axis):
        v = np.asarray(v, float)
        a = np.asarray(axis, float)
        a = a / np.linalg.norm(a)
        w = v - float(v @ a) * a
        return w / np.linalg.norm(w)

    panels = [
        _poly("glue", "glue", [(-gw, 0), (0, 0), (0, H), (-gw, H)]),
        _poly("wF", "wall", [(0, 0), (W, 0), (W, H), (0, H)]),
        _poly("wR", "wall", [(W + ya, 0), (W + D, 0), (W + D, H), (W, H), (W, 0)]),
        _poly("wB", "wall", [(W + D, 0), (2 * W + D, 0), (2 * W + D, H), (W + D, H)]),
        _poly("wL", "wall", [(2 * W + D + (D - ya), 0), (2 * W + 2 * D, 0),
                             (2 * W + 2 * D, H), (2 * W + D, H), (2 * W + D, 0)]),
        # bF: 底板带隔板铰链分点 (dvl: 两侧棱中点 / dvt: 上下棱 dv_x 分点); 首三元组非共线
        _poly("bF", "flap", [(W, -D / 2.0), (W, 0), (dv_x, 0), (0, 0), (0, -D / 2.0),
                             (0, -D), (dv_x, -D), (W, -D)]),
        _poly("bB", "flap", [(W + D, -D), (2 * W + D, -D), (2 * W + D, 0), (W + D, 0)]),
        _poly("gL0", "flap", [(2 * W + 2 * D, 0), (2 * W + D + (D - ya), 0),
                              (2 * W + D + (D - yb), -hd), (2 * W + 2 * D, -hd)]),
        _poly("gR0", "flap", [(W, 0), (W + ya, 0), (W + yb, -hd), (W, -hd)]),
    ]
    edges = [
        _fold("e_glue", (0, 0), (0, H), "wF", "glue", (1.0, 0.0, 0.0), "MOUNTAIN"),
        _fold("e_wR", (W, 0), (W, H), "wF", "wR", (0.0, 1.0, 0.0)),
        _fold("e_wB", (W + D, 0), (W + D, H), "wR", "wB", (-1.0, 0.0, 0.0)),
        _fold("e_wL", (2 * W + D, 0), (2 * W + D, H), "wB", "wL", (0.0, -1.0, 0.0)),
        _fold("e_bF", (0, 0), (W, 0), "wF", "bF", (0.0, 1.0, 0.0), "MOUNTAIN"),
        _fold("e_bB", (W + D, 0), (2 * W + D, 0), "wB", "bB", (0.0, -1.0, 0.0), "MOUNTAIN"),
        _fold("e_gL0", (2 * W + 2 * D, 0), (2 * W + D + (D - ya), 0), "wL", "gL0",
              (1.0, 0.0, 0.0), "MOUNTAIN"),
        _fold("e_gR0", (W, 0), (W + ya, 0), "wR", "gR0", (-1.0, 0.0, 0.0), "MOUNTAIN"),
        # 十字隔板: 自 bF 铰链立起 (dvl 纵隔全宽 @y=D/2 / dvt 横隔全深 @x=dv_x)
        _fold("e_dvl", (0, -D / 2.0), (W, -D / 2.0), "bF", "dvl", (0.0, 0.0, 1.0),
              "MOUNTAIN"),
        _fold("e_dvt", (dv_x, 0), (dv_x, -D), "bF", "dvt", (0.0, 0.0, 1.0), "MOUNTAIN"),
    ]

    def _net_to_world(parent, q):
        q = np.asarray(q, float)
        if parent == "gL0":
            return np.array([-q[1], D - (q[0] - (2 * W + D)), 0.0])
        return np.array([W + q[1], q[0] - W, 0.0])

    def _lock_fold(pid, pts, seg_a, seg_b, crease_a, crease_b, parent):
        panels.append(_poly(pid, "flap", pts))
        cen_net = np.mean(pts, axis=0)
        cen_pre = _net_to_world(parent, cen_net)
        cen_ref = _refl2(cen_pre, crease_a, crease_b)
        axis3 = np.array([crease_b[0] - crease_a[0], crease_b[1] - crease_a[1], 0.0])
        mid = np.array([(crease_a[0] + crease_b[0]) / 2.0,
                        (crease_a[1] + crease_b[1]) / 2.0, 0.0])
        tdir = _perp3(cen_ref - mid, axis3)
        edges.append(_fold(f"e_{pid}", seg_a, seg_b, parent, pid, tdir, "MOUNTAIN"))

    _lock_fold("gL1",
               [(2 * W + D + (D - ya), 0), (2 * W + D, 0),
                (2 * W + D, -hd), (2 * W + D + (D - yb), -hd)],
               (2 * W + D + (D - yb), -hd), (2 * W + D + (D - ya), 0),
               (hd, yb), (0.0, ya), "gL0")
    _lock_fold("gR1",
               [(W + ya, 0), (W + D, 0), (W + D, -hd), (W + yb, -hd)],
               (W + yb, -hd), (W + ya, 0),
               (W - hd, yb), (float(W), ya), "gR0")

    panels.append(_poly("dvl", "wall", [(0, -D / 2.0 - dv_h), (W, -D / 2.0 - dv_h),
                                        (W, -D / 2.0), (0, -D / 2.0)]))
    panels.append(_poly("dvt", "wall", [(dv_x, 0), (dv_x, -D),
                                        (dv_x + dv_h, -D), (dv_x + dv_h, 0)]))
    notes = (f"crashlock_divider: 带隔板顺央底盒 — 4 墙链 + 全深底板 bF/bB + 菱形互锁 "
             f"斜折片×4 (90°下折+180°斜折平铺互锁) + 盒内十字隔板 (纵隔全宽 @y=D/2 × "
             f"横隔全深 @x={dv_x:g}, T 字相贯, 高 {dv_h:g}, 自底板铰链立起)")
    return panels, edges, notes, _features("glue", "gL0", "gR0"), "wF", _R_CHAIN, [0.0, 0.0, 0.0]


def _closure_crashlock_div(ir, world) -> dict:
    W, D, H = float(ir.param("W")), float(ir.param("D")), float(ir.param("H"))
    dv_x, dv_h = float(ir.param("dv_x")), float(ir.param("dv_h"))
    hd, ya, yb = _crashlock_ratios(W, D)
    res: dict[str, float] = {}
    res["seam.LF.bot"] = float(np.linalg.norm(world["wL"][1] - world["wF"][0]))
    res["seam.LF.top"] = float(np.linalg.norm(world["wL"][2] - world["wF"][3]))
    res["bF.tucks_wB"] = float(np.linalg.norm(np.mean(world["bF"][5:8], axis=0)
                                              - np.mean(world["wB"][0:2], axis=0)))
    res["bB.tucks_wF"] = float(np.linalg.norm(np.mean(world["bB"][0:2], axis=0)
                                              - np.mean(world["wF"][0:2], axis=0)))
    ca = np.array([hd, yb])
    cb = np.array([0.0, ya])
    dd = cb - ca
    t_star = float((np.array([hd, D]) - ca) @ dd) / float(dd @ dd)
    mirror = 2 * (ca + t_star * dd) - np.array([hd, D])
    mxL, mxR = float(world["gL1"][2][0]), float(world["gR1"][2][0])
    res["lock.mirror_x"] = abs(mxL - mirror[0]) + abs((W - mxR) - mirror[0])
    res["lock.sym_x"] = abs(mxL + mxR - W)
    res["lock.iso"] = abs(float(np.linalg.norm(world["gL1"][2] - world["gL1"][1])) - hd)
    res["lock.flat"] = abs(float(world["gL1"][2][2])) + abs(float(world["gR1"][2][2]))
    res["glue.planar_y0"] = float(np.max(np.abs(world["glue"][:, 1])))
    # 十字隔板: 立面落位 + 全高 + 横隔足线居中
    dv = np.asarray(world["dvl"], float)
    dt = np.asarray(world["dvt"], float)
    res["dvl.plane"] = abs(float(np.mean(dv[:, 1])) - D / 2.0)
    res["dvl.top"] = abs(float(np.mean(dv[0:2], axis=0)[2]) - dv_h)
    res["dvl.seat"] = abs(float(np.mean(dv[2:4], axis=0)[2]))
    res["dvt.plane"] = abs(float(np.mean(dt[:, 0])) - dv_x)
    res["dvt.top"] = abs(float(np.mean(dt[2:4], axis=0)[2]) - dv_h)
    res["dvt.seat"] = abs(float(np.mean(dt[0:2], axis=0)[2]))
    res["dvt.foot_y"] = abs(float(np.mean(dt[0:2], axis=0)[1]) - D / 2.0)
    return res


# ---------------------------------------------------------- ⑤ tube_cap_end
_TN = 16


def _build_tube_cap(p):
    n, side, h, gw = _TN, float(p["side"]), float(p["h"]), float(p["glue_w"])
    rf = float(p["rf"])
    a = side / (2.0 * math.tan(math.pi / n))
    _, outward, tangent, _ = _poly_ring(n, side, side / 2.0, a)

    panels = [_rect("glue", "glue", 0.0, 0.0, gw, h)]
    for i in range(n):
        panels.append(_rect(f"w{i}", "wall", gw + i * side, 0.0, gw + (i + 1) * side, h))
    # 星盘: 交替墙位 8 三角片 (片尖折入抵轴线, 深 = apothem)
    for k in range(8):
        x0 = gw + 2 * k * side
        panels.append(_poly(f"cap{k}", "flap",
                            [(x0, 0), (x0 + side, 0), (x0 + side / 2.0, -a)]))
    # 外翻缘环带: 每墙顶缘外折 90° 窄带 (tdir 向外)
    for i in range(n):
        panels.append(_rect(f"f{i}", "flap", gw + i * side, h,
                            gw + (i + 1) * side, h + rf))
    edges = []
    for i in range(n - 1):
        x = gw + (i + 1) * side
        edges.append(_fold(f"e_w{i}", (x, 0), (x, h), f"w{i}", f"w{i + 1}",
                           (*tangent[i + 1], 0.0)))
    edges.append(_fold("e_glue", (gw, 0), (gw, h), "w0", "glue", (1.0, 0.0, 0.0),
                       "MOUNTAIN"))
    for k in range(8):
        x0 = gw + 2 * k * side
        edges.append(_fold(f"e_cap{k}", (x0, 0), (x0 + side, 0), f"w{2 * k}",
                           f"cap{k}", (*(-outward[2 * k]), 0.0), "MOUNTAIN"))
    for i in range(n):
        edges.append(_fold(f"e_f{i}", (gw + i * side, h), (gw + (i + 1) * side, h),
                           f"w{i}", f"f{i}", (*outward[i], 0.0), "MOUNTAIN"))
    notes = (f"tube_cap_end: 卷轴端盖管 — 直管曲面 {n} 边形近似 (墙 {n} 片矩形, 全重叠"
             f"粘缝 1 片宽=墙宽) + 底端 8 片内折星盘 (交替墙位三角片, 深 apothem="
             f"{a:.2f}mm, 片尖互抵轴线, 交替墙位留 V 形缺口为已知边界) + 顶端外翻缘"
             f"环带 {n} 片 (深 {rf:g}, 外折 90°)")
    return panels, edges, notes, _features("glue"), "w0", _R_CHAIN, [-gw, 0.0, 0.0]


def _closure_tube_cap(ir, world) -> dict:
    n, side, h = _TN, float(ir.param("side")), float(ir.param("h"))
    rf = float(ir.param("rf"))
    a = side / (2.0 * math.tan(math.pi / n))
    ctr0 = np.array([side / 2.0, a, 0.0])
    ctrh = np.array([side / 2.0, a, h])
    res: dict[str, float] = {}
    wn = world[f"w{n - 1}"]
    res["seam.far_edge"] = float(max(np.linalg.norm(wn[1] - world["w0"][0]),
                                     np.linalg.norm(wn[2] - world["w0"][3])))
    res["glue.flush_w0"] = float(abs(float(np.mean(np.asarray(world["glue"])[:, 1]))))
    res["glue.far_meets_w0_far"] = float(max(
        np.linalg.norm(world["glue"][3] - world["w0"][2]),
        np.linalg.norm(world["glue"][0] - world["w0"][1])))
    for k in range(8):
        res[f"cap{k}.axis"] = float(np.linalg.norm(np.asarray(world[f"cap{k}"][2], float)
                                                   - ctr0))
    for i in range(n):
        far = np.mean(world[f"f{i}"][2:4], axis=0)
        res[f"f{i}.far"] = float(abs(np.linalg.norm(far - ctrh) - (a + rf)))
        res[f"f{i}.plane"] = float(abs(float(far[2]) - h))
    return res


# ---------------------------------------------------------- ⑥ mailer_rigid_pad
def _build_mailer_pad(p):
    S, C, h, t = float(p["spine_w"]), float(p["cover_w"]), float(p["h"]), float(p["tuck_t"])
    pd = float(p["pad_d"])

    def rect(pid, role, x0, x1):
        return {"id": pid, "role": role,
                "polygon_2d": [[x0, 0], [x1, 0], [x1, h], [x0, h]]}

    panels = [rect("spine", "wall", 0.0, S),
              rect("coverL", "wall", -C, 0.0),
              rect("coverR", "wall", S, S + C),
              rect("tuck", "flap", S + C, S + C + t),
              rect("pad", "flap", -C - pd, -C)]
    edges = [
        _fold("e_cl", (0, 0), (0, h), "spine", "coverL", (0.0, 1.0, 0.0)),
        _fold("e_cr", (S, 0), (S, h), "spine", "coverR", (0.0, 1.0, 0.0)),
        _fold("e_tk", (S + C, 0), (S + C, h), "coverR", "tuck", (0.0, -1.0, 0.0),
              "MOUNTAIN"),
        # 内衬硬垫片: 180° 反贴左盖内面 (面内共面第二层)
        _fold("e_pad", (-C, 0), (-C, h), "coverL", "pad", (0.0, -1.0, 0.0), "MOUNTAIN"),
    ]
    notes = (f"mailer_rigid_pad: 硬衬邮寄盒 — 书封三件 (书脊 {S:g} + 左右盖 {C:g}, "
             f"90° 立起) + 插舌 {t:g} 180° 反贴右盖内面 (可决式封盖, reach y=C-t) + "
             f"内衬硬垫片 {pd:g} 180° 反贴左盖内面 (面内共面第二层)")
    return panels, edges, notes, _features("tuck"), "spine", _R_CHAIN, [0.0, 0.0, 0.0]


def _closure_mailer(ir, world) -> dict:
    S, C, t = float(ir.param("spine_w")), float(ir.param("cover_w")), float(ir.param("tuck_t"))
    pd = float(ir.param("pad_d"))
    res: dict[str, float] = {}
    res["coverL.perp_x0"] = abs(float(np.mean(world["coverL"][[0, 3]], axis=0)[0]))
    res["coverR.perp_xS"] = abs(float(np.mean(world["coverR"][[1, 2]], axis=0)[0]) - S)
    tv = np.asarray(world["tuck"], float)
    res["tuck.flush_xS"] = float(np.max(np.abs(tv[:, 0] - S)))
    res["tuck.reach"] = abs(float(np.mean(tv[[1, 2]], axis=0)[1]) - (C - t))
    pv = np.asarray(world["pad"], float)
    res["pad.flush_x0"] = float(np.max(np.abs(pv[:, 0])))
    res["pad.reach"] = abs(float(np.mean(pv[[0, 3]], axis=0)[1]) - (C - pd))
    return res


# ---------------------------------------------------------- ⑦ tray_domelid
def _build_tray_dome(p):
    W, D, H, gw = float(p["W"]), float(p["D"]), float(p["H"]), float(p["glue_w"])
    k, lip_d = int(p["dome_k"]), float(p["lip_d"])
    r = D / 2.0
    c = 2.0 * r * math.sin(math.pi / (2.0 * k))     # 弧弦片深 (等弦)

    def _poly(pid, role, pts):
        return {"id": pid, "role": role,
                "polygon_2d": [[float(x), float(y)] for x, y in pts]}

    panels = [
        _poly("base", "wall", [(0, 0), (W, 0), (W, D), (0, D)]),
        _poly("wF", "wall", [(0, -H), (W, -H), (W, 0), (0, 0)]),
        _poly("wR", "wall", [(W, 0), (W + H, 0), (W + H, D), (W, D)]),
        _poly("wB", "wall", [(0, D), (W, D), (W, D + H), (0, D + H)]),
        _poly("wL", "wall", [(-H, 0), (0, 0), (0, D), (-H, D)]),
        _poly("cFR", "flap", [(W, 0), (W, -H), (W + gw, -H)]),
        _poly("cRB", "flap", [(W + H, D), (W, D), (W, D + gw)]),
        _poly("cBL", "flap", [(0, D), (0, D + H), (-gw, D + H)]),
        _poly("cLF", "flap", [(-H, 0), (0, 0), (0, -gw)]),
    ]
    edges = [
        _fold("e_wF", (0, 0), (W, 0), "base", "wF", (0.0, 0.0, 1.0)),
        _fold("e_wR", (W, 0), (W, D), "base", "wR", (0.0, 0.0, 1.0)),
        _fold("e_wB", (0, D), (W, D), "base", "wB", (0.0, 0.0, 1.0)),
        _fold("e_wL", (0, 0), (0, D), "base", "wL", (0.0, 0.0, 1.0)),
        _fold("e_cFR", (W, 0), (W, -H), "wF", "cFR", (0.0, 1.0, 0.0), "MOUNTAIN"),
        _fold("e_cRB", (W + H, D), (W, D), "wR", "cRB", (-1.0, 0.0, 0.0), "MOUNTAIN"),
        _fold("e_cBL", (0, D), (0, D + H), "wB", "cBL", (0.0, -1.0, 0.0), "MOUNTAIN"),
        _fold("e_cLF", (-H, 0), (0, 0), "wL", "cLF", (1.0, 0.0, 0.0), "MOUNTAIN"),
    ]
    # 拱盖: 后墙铰链 k 段弧折 (半圆弧 P(φ)=(D/2+r cosφ, H+r sinφ), φ: 0→π),
    # 弦线近似 (pillow_box 弧同款); 末段远缘精确落前墙顶缘 (y=0, z=H)
    y0 = D + H
    P = lambda ph: np.array([D / 2.0 + r * math.cos(ph), H + r * math.sin(ph)])
    prev = P(0.0)
    for j in range(1, k + 1):
        cur = P(j * math.pi / k)
        y_lo = y0 + (j - 1) * c     # 累计式: j=1 时 y_lo == y0 逐位精确 (G03 并集连通)
        y_hi = y0 + j * c
        panels.append(_poly(f"dome{j}", "slope",
                            [(0, y_lo), (W, y_lo), (W, y_hi), (0, y_hi)]))
        chord = cur - prev
        tdir = (0.0, float(chord[0]), float(chord[1]))
        nrm = math.hypot(tdir[1], tdir[2])
        tdir = (0.0, tdir[1] / nrm, tdir[2] / nrm)
        edges.append(_fold(f"e_dome{j}", (0, y_lo), (W, y_lo),
                           "wB" if j == 1 else f"dome{j - 1}", f"dome{j}",
                           tdir, "VALLEY"))
        prev = cur
        yk = y_hi
    # 前扣唇: 自拱盖末段远缘 (前墙顶缘线) 内折下扣, 贴前墙内面 (共面第二层)
    panels.append(_poly("lip", "flap", [(0, yk), (W, yk), (W, yk + lip_d), (0, yk + lip_d)]))
    edges.append(_fold("e_lip", (0, yk), (W, yk), f"dome{k}", "lip",
                       (0.0, 0.0, -1.0), "MOUNTAIN"))
    notes = (f"tray_domelid: 拱盖托盘 — 四角粘合盘 (中央底板+4墙+4全高角片绕角折合) "
             f"+ 后墙铰链拱盖 {k} 段弧折 (半圆弧弦线近似, 弦深 {c:.2f}mm, 末段远缘落 "
             f"前墙顶缘) + 前墙内扣唇 {lip_d:g} (前扣)")
    return panels, edges, notes, _features("cFR", "cRB", "cBL", "cLF"), "base", _R_STAR, [0.0, 0.0, 0.0]


def _closure_tray_dome(ir, world) -> dict:
    W, D, H = float(ir.param("W")), float(ir.param("D")), float(ir.param("H"))
    r, k = D / 2.0, int(ir.param("dome_k"))
    lip_d = float(ir.param("lip_d"))
    res: dict[str, float] = {}
    # 四角缝 (跨链) + 角片贴邻墙内面
    for name, pa, ia, pb, ib in (
            ("seam.FR", "wF", 1, "wR", 1), ("seam.RB", "wR", 2, "wB", 2),
            ("seam.BL", "wB", 3, "wL", 3), ("seam.LF", "wL", 0, "wF", 0)):
        res[name] = float(np.linalg.norm(world[pa][ia] - world[pb][ib]))
    for cid, ax, tgt in (("cFR", 0, W), ("cRB", 1, D), ("cBL", 0, 0.0), ("cLF", 1, 0.0)):
        res[f"{cid}.on_host"] = float(np.max(np.abs(world[cid][:, ax] - tgt)))
    # 拱盖: 末段远缘落前墙顶缘 + 中段远缘过弧顶 (y=D/2, z=H+r)
    dmk = world[f"dome{k}"]
    res["dome.close"] = float(np.linalg.norm(np.mean(dmk[2:4], axis=0)
                                             - np.mean(world["wF"][0:2], axis=0)))
    dmid = world[f"dome{k // 2}"]
    apex = np.mean(dmid[2:4], axis=0)
    res["dome.apex"] = abs(float(apex[1]) - D / 2.0) + abs(float(apex[2]) - (H + r))
    res["dome.hinge"] = float(np.linalg.norm(np.mean(world["dome1"][0:2], axis=0)
                                             - np.mean(world["wB"][2:4], axis=0)))
    # 前扣唇: 贴前墙平面 + 扣深 + 座落前墙顶缘下
    lp = np.asarray(world["lip"], float)
    res["lip.plane_y0"] = float(np.max(np.abs(lp[:, 1])))
    res["lip.depth"] = abs(float(np.mean(lp[2:4], axis=0)[2]) - (H - lip_d))
    res["lip.seat"] = abs(float(np.mean(lp[0:2], axis=0)[2]) - H)
    return res


# ------------------------------------------------------------ 契约
_CLASS_PARAMS = {
    "prism_tuck_window": {"kind": 0, "side": 60.0, "h": 100.0, "glue_w": 12.0,
                          "board_t": 0.42, "bw": 20.0, "tw_s": 14.0, "lw": 18.0},
    "gable_window_front": {"kind": 1, "W": 60.0, "D": 45.0, "Hb": 100.0, "Hr": 15.0,
                           "Ef": 14.0, "fin_gap_mm": 3.0, "glue_w": 12.0,
                           "board_t": 0.45, "bw": 20.0, "tw_s": 14.0, "lw": 12.0},
    "rsc_handhole": {"kind": 2, "W": 160.0, "D": 100.0, "H": 80.0, "flap_ratio": 0.5,
                     "glue_w": 12.0, "board_t": 0.45, "hw": 15.0, "hh": 22.0},
    "crashlock_divider": {"kind": 3, "W": 100.0, "D": 60.0, "H": 80.0, "glue_w": 12.0,
                          "board_t": 0.45, "dv_x": 50.0, "dv_h": 36.0},
    "tube_cap_end": {"kind": 4, "side": 20.0, "h": 140.0, "glue_w": 20.0,
                     "board_t": 0.42, "rf": 6.0},
    "mailer_rigid_pad": {"kind": 5, "spine_w": 40.0, "cover_w": 150.0, "h": 220.0,
                         "tuck_t": 35.0, "board_t": 0.42, "pad_d": 70.0},
    "tray_domelid": {"kind": 6, "W": 120.0, "D": 80.0, "H": 40.0, "glue_w": 12.0,
                     "board_t": 0.45, "dome_k": 4, "lip_d": 10.0},
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
    """参数语义: 相关键非零才校验 (家族不适用键置 0)."""
    p = params or {}
    kind = int(p.get("kind", 0))
    if kind == 0:      # prism_tuck_window
        _pos(p, "side", "h", "glue_w", "bw", "tw_s", "lw")
        if float(p["glue_w"]) >= float(p["side"]):
            raise ValueError("粘口 glue_w 须窄于墙宽 side")
        if float(p["bw"]) + float(p["tw_s"]) >= float(p["h"]):
            raise ValueError("窗框 bw + tw_s 须小于 h (窗洞 win_h > 0)")
        if 2.0 * float(p["lw"]) >= float(p["side"]):
            raise ValueError("窗框侧条 2*lw 须窄于 side")
    elif kind == 1:    # gable_window_front
        _pos(p, "W", "D", "Hb", "Hr", "Ef", "fin_gap_mm", "glue_w", "bw", "tw_s", "lw")
        if float(p["fin_gap_mm"]) >= 2.0 * float(p["Ef"]):
            raise ValueError("鳍顶缘距 fin_gap_mm 须 < 2*Ef")
        if float(p["glue_w"]) >= min(float(p["W"]), float(p["D"])):
            raise ValueError("粘口 glue_w 须窄于最短墙")
        if float(p["bw"]) + float(p["tw_s"]) >= float(p["Hb"]):
            raise ValueError("窗框 bw + tw_s 须小于 Hb (窗洞 win_h > 0)")
        if 2.0 * float(p["lw"]) >= float(p["W"]):
            raise ValueError("窗框侧条 2*lw 须窄于 W")
    elif kind == 2:    # rsc_handhole
        _pos(p, "W", "D", "H", "glue_w", "hw", "hh")
        r = p.get("flap_ratio")
        if not isinstance(r, (int, float)) or isinstance(r, bool) \
                or not (0.0 < float(r) <= 1.0):
            raise ValueError(f"非法参数 flap_ratio={r!r} (须 (0,1])")
        if float(p["glue_w"]) >= min(float(p["W"]), float(p["D"])):
            raise ValueError(f"粘口 glue_w={p['glue_w']} 须窄于最短墙 "
                             f"min(W,D)={min(p['W'], p['D'])}")
        if 2.0 * float(p["hw"]) >= float(p["W"]):
            raise ValueError("提手孔宽 2*hw 须窄于 W")
        if float(p["hh"]) >= float(p["H"]) / 2.0:
            raise ValueError("提手孔深 hh 须小于 H/2")
    elif kind == 3:    # crashlock_divider
        _pos(p, "W", "D", "H", "glue_w", "dv_x", "dv_h")
        if float(p["glue_w"]) >= float(p["D"]) / 2.0 \
                or float(p["glue_w"]) >= float(p["W"]) / 2.0:
            raise ValueError("glue_w/互锁翼过宽 (须 < W/2 且 < D/2)")
        if not (2.0 < float(p["dv_x"]) < float(p["W"]) - 2.0):
            raise ValueError("横隔位 dv_x 须落在盒宽内 (留 2mm 边距)")
        if float(p["dv_h"]) >= float(p["H"]):
            raise ValueError("隔板高 dv_h 须小于盒高 H")
    elif kind == 4:    # tube_cap_end
        _pos(p, "side", "h", "glue_w", "rf")
        if float(p["glue_w"]) > float(p["side"]):
            raise ValueError("直管全重叠粘缝: glue_w ≤ side")
        if float(p["rf"]) >= float(p["side"]):
            raise ValueError("外翻缘 rf 须窄于墙宽 side")
    elif kind == 5:    # mailer_rigid_pad
        _pos(p, "spine_w", "cover_w", "h", "tuck_t", "pad_d")
        if float(p["tuck_t"]) >= float(p["cover_w"]):
            raise ValueError("书封须 tuck_t < cover_w")
        if float(p["pad_d"]) >= float(p["cover_w"]):
            raise ValueError("内衬垫深 pad_d 须小于 cover_w")
    elif kind == 6:    # tray_domelid
        _pos(p, "W", "D", "H", "glue_w", "lip_d")
        k = p.get("dome_k")
        if not isinstance(k, (int, float)) or isinstance(k, bool) \
                or int(k) not in (2, 4, 6) or int(k) != k:
            raise ValueError(f"非法参数 dome_k={k!r} (须偶数 2/4/6)")
        if float(p["glue_w"]) >= float(p["H"]):
            raise ValueError("角片搭接宽 glue_w 须窄于墙高 H")
        if float(p["lip_d"]) >= float(p["H"]):
            raise ValueError("前扣唇深 lip_d 须小于墙高 H")
    else:
        raise ValueError(f"非法 kind={kind!r} (须 0..6)")


_BUILDERS = (_build_prism_win, _build_gable_win, _build_rsc_hand, _build_crashlock_div,
             _build_tube_cap, _build_mailer_pad, _build_tray_dome)


def build_ir(params: dict | None = None) -> dict:
    p = {**DEFAULTS, **(params or {})}
    kind = int(p.get("kind", 0))
    if not (0 <= kind <= 6):
        raise ValueError(f"非法 kind={kind!r} (须 0..6)")
    cls_id = _CLS[kind]
    panels, edges, notes, feats, root, R, off = _BUILDERS[kind](p)
    return {
        "meta": {"ir_version": "0.1", "units": "mm",
                 "generator": "photo_dieline.parametric.struct_ext 0.1",
                 "notes": notes,
                 "root_panel": root,
                 "root_frame": {"R": [list(map(float, row)) for row in R],
                                "off": [float(v) for v in off]}},
        "package": {"type": cls_id,
                    "template": {"id": cls_id, "version": "0.1"},
                    "params": {k: float(p[k]) for k in PARAM_ORDER},
                    "photo": None},
        "panels": panels,
        "edges": edges,
        "features": feats,
    }


def analytic_bbox(params: dict) -> dict:
    """G05 期望: solid (wall 角色) 折叠 bbox."""
    p = {**DEFAULTS, **(params or {})}
    kind = int(p.get("kind", 0))
    if kind == 0:
        return _ring_bbox(6, float(p["side"]), float(p["h"]))
    if kind == 1:
        return {"W": float(p["W"]), "D": float(p["D"]),
                "H": float(p["Hb"]) + float(p["Hr"])}
    if kind == 4:
        return _ring_bbox(_TN, float(p["side"]), float(p["h"]))
    if kind == 5:
        return {"W": float(p["spine_w"]), "D": float(p["cover_w"]), "H": float(p["h"])}
    return {"W": float(p["W"]), "D": float(p["D"]), "H": float(p["H"])}


def solid_roles():
    return ("wall",)


def allowed_overlap():
    """G06 允许叠层 (真实工艺契约, 全家族并集):
    星形底板/插盖/星盘全对; 环闭合末墙↔首墙; glue 端缘触邻墙; 窗框环缝跨链对;
    隔板/垫片/扣唇共面贴合对; 拱盖与墙/角片顶缘近邻放行对."""
    s = set()
    # ① prism_tuck_window: 星形底板/插盖全对 (n=6) + 环缝跨链 + glue 触邻
    for pre in ("b", "t"):
        ids = [f"{pre}{i}" for i in range(6)]
        for i in range(6):
            for j in range(i + 1, 6):
                s.add(frozenset({ids[i], ids[j]}))
    for i in range(6):
        for j in range(6):
            s.add(frozenset({f"b{i}", f"t{j}"}))
    for pid in ("fb", "wl", "wt", "wr"):
        s.add(frozenset({pid, "w5"}))
        s.add(frozenset({"glue", pid}))
    s.add(frozenset({"glue", "w5"}))
    s.add(frozenset({"glue", "b0"}))
    # ② gable_window_front: gable 同款 + 窗框环缝/glue 跨框对
    s.add(frozenset({"flapF", "flapB"}))
    s.add(frozenset({"flapL", "flapR"}))
    s.add(frozenset({"finB", "finF"}))
    s.add(frozenset({"glue", "wallL"}))
    for pid in ("fb", "wl", "wt", "wr"):
        s.add(frozenset({pid, "wallL"}))
        s.add(frozenset({"glue", pid}))
    # ③ rsc_handhole: rsc 同面折翼全对 + 环缝 + glue 触末墙
    for pre in ("t", "b"):
        ids = [f"{pre}{i}" for i in range(4)]
        for i in range(4):
            for j in range(i + 1, 4):
                s.add(frozenset({ids[i], ids[j]}))
    s.add(frozenset({"glue", "w3"}))
    s.add(frozenset({"w0", "w3"}))
    # ④ crashlock_divider: z=0 底板/互锁片全对 + 隔板与底板/墙/互锁片贴合对
    bottoms = ("bF", "bB", "gL0", "gL1", "gR0", "gR1")
    for i in range(len(bottoms)):
        for j in range(i + 1, len(bottoms)):
            s.add(frozenset({bottoms[i], bottoms[j]}))
    s.add(frozenset({"glue", "wF"}))
    for dv in ("dvl", "dvt"):
        for host in bottoms + ("wF", "wR", "wB", "wL"):
            s.add(frozenset({dv, host}))
        s.add(frozenset({dv, "glue"}))
    s.add(frozenset({"dvl", "dvt"}))
    # ⑤ tube_cap_end: 星盘全对 + 环缝 + glue 触首墙
    for i in range(8):
        for j in range(i + 1, 8):
            s.add(frozenset({f"cap{i}", f"cap{j}"}))
    s.add(frozenset({"glue", "w0"}))
    s.add(frozenset({"w0", f"w{_TN - 1}"}))
    # ⑥ mailer_rigid_pad: 插舌反贴右盖 / 硬垫反贴左盖 (共面第二层)
    s.add(frozenset({"tuck", "coverR"}))
    s.add(frozenset({"pad", "coverL"}))
    # ⑦ tray_domelid: 角片贴邻墙内面 + 拱盖/扣唇与墙·角片顶缘近邻放行
    for cfd, w in (("cFR", "wR"), ("cRB", "wB"), ("cBL", "wL"), ("cLF", "wF")):
        s.add(frozenset({cfd, w}))
    for j in range(1, 7):
        for w in ("wF", "wR", "wB", "wL"):
            s.add(frozenset({f"dome{j}", w}))
        for cfd in ("cFR", "cRB", "cBL", "cLF"):
            s.add(frozenset({f"dome{j}", cfd}))
    for w in ("wF", "wR", "wB", "wL"):
        s.add(frozenset({"lip", w}))
    for cfd in ("cFR", "cRB", "cBL", "cLF"):
        s.add(frozenset({"lip", cfd}))
    return s


# ---------------------------------------------------------------- closure
def closure_checks(ir, world) -> dict:
    kind = _KIND[ir.package["template"]["id"]]
    return (_closure_prism, _closure_gable, _closure_rsc, _closure_crashlock_div,
            _closure_tube_cap, _closure_mailer, _closure_tray_dome)[kind](ir, world)


# ---------------------------------------------------------------- 负探针
def _rodrigues(v, axis, ang):
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    k = np.asarray(v, float)
    return (k * math.cos(ang) + np.cross(a, k) * math.sin(ang)
            + a * float(a @ k) * (1.0 - math.cos(ang)))


def _perturb(raw_ir, edge_id, axis, ang=0.35):
    """绕铰链轴把 tdir 转开 ang 弧度 (引擎把 tdir 投影到轴垂直面 —
    只有绕轴的分量才改变折叠落位)."""
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
    kind = _KIND[ir.package["template"]["id"]]
    return {0: [("e_wt", (1, 0, 0)), ("e_t0", (1, 0, 0))],
            1: [("e_wt", (1, 0, 0)), ("e_ft_sl", (1, 0, 0))],
            2: [("e_b0", (1, 0, 0)), ("e_t0", (1, 0, 0))],
            3: [("e_dvl", (1, 0, 0)), ("e_gL0", (0, 1, 0))],
            4: [("e_cap0", (1, 0, 0)), ("e_f0", (1, 0, 0))],
            5: [("e_tk", (0, 0, 1)), ("e_pad", (0, 0, 1))],
            6: [("e_dome1", (1, 0, 0)), ("e_cFR", (0, 0, 1))]}[kind]


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
