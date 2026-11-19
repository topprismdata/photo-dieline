"""box_essentials: 盒装基础六类.

类ID:
  tuck_top_box   4 墙矩形盒 + 顶插盖(主盖深 D, 自背墙 w2, 插舌深 tuck_d 入前墙内面)
                 + 2 防尘翼(侧墙顶缘, 深 dust_r*W 远缘中线相抵) + 底全叠封(4 折翼全到中线)
  hanger_box     同 tuck_top 但盖自前墙 w0 (插舌入背墙内面), 背墙顶缘带挂片:
                 挂片(高 tab_h)与背墙共面直立延伸, 顶缘中央凹口槽(slot_w×slot_d)为挂孔
  window_box     同 tuck_top 但前墙为窗框: 底条(wb, 主链) → 左条(wl) → 顶条(wt) →
                 右条(wr) 绕窗口平折共面链, 前墙中央留矩形窗洞(网并集=带孔单环)
  two_piece      天地盖两件独立管: 内盒(4 墙+glue+底全叠封+顶缘外翻缘) 与
                 盖(4 墙+glue+顶全叠封+口缘外翻缘), 盖内空 = 内盒 + 2*clear,
                 盖深 = H + friction; 两件世界系分离摆放, 网内以窄 web 工艺条相连
                 (分离拓扑: 成型后两件不折接, 见 meta.notes)
  dispenser_top  同 tuck_top 但主盖深 D/2 + 前墙顶翼 f0(深 D/2, 远缘中央缺角多边形)
                 平折成顶面前半, 缺角即抽取口; 主盖远缘中央带下折舌(抽取口内推片)
  slide_box      抽屉盒两件: 外套筒(4 墙+glue, 两端开放) + 内抽屉(4 墙+glue+
                 底全叠封+前墙内面挡板 baffle), 套筒内空 = 抽屉 + 2*cs, 套筒高 H,
                 抽屉高 H-drop; 两件分离摆放, 网内 web 条相连 (分离拓扑)

几何约定: 链式网根墙 w0 占 y=0 平面, net(x,y)→world(x,0,y), root_frame off=[-gw,0,0];
墙环 w0(front,y=0)→w1(right,x=W)→w2(back,y=D)→w3(left,x=0), w3 自由缘回 w0 左缘。
④/⑥ 第二件经 web 条续链: web 铰链于 w3 自由缘 (世界 x=0, y=0 竖线), 平折至
y=0 平面 x∈[-web_w,0], 第二件墙链向 -x 世界向展开 (分离摆放, 间距 = web_w)。
closure 全部为折叠后世界坐标跨链远缘残差; 负探针 probe() 见模块底部。
"""
from __future__ import annotations

import copy
import math

import numpy as np

from . import base as _base

DEFAULTS = {"W": 110.0, "D": 70.0, "H": 60.0, "glue_w": 12.0, "board_t": 0.45,
            "tuck_d": 12.0, "dust_r": 0.5, "ins": 12.0,
            "tab_h": 32.0, "slot_w": 10.0, "slot_d": 12.0,
            "bw": 20.0, "tw_s": 14.0, "lw": 18.0,
            "clear": 1.5, "friction": 2.0, "rf": 5.0, "web_w": 6.0,
            "hw": 18.0, "ad": 8.0, "cs": 1.5, "drop": 6.0, "bs": 25.0,
            "kind": 0}
PARAM_ORDER = ["kind", "W", "D", "H", "glue_w", "board_t", "tuck_d", "dust_r", "ins",
               "tab_h", "slot_w", "slot_d", "bw", "tw_s", "lw",
               "clear", "friction", "rf", "web_w", "hw", "ad", "cs", "drop", "bs"]

_CLS = ("tuck_top_box", "hanger_box", "window_box",
        "two_piece", "dispenser_top", "slide_box")
_KIND = {c: i for i, c in enumerate(_CLS)}

for _cid in _CLS:
    _base.register(_cid, "box_essentials")

_R_CHAIN = [[1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0]]  # net(x,y)→world(x,0,y)


# ---------------------------------------------------------------- helpers
def _rect(pid: str, role: str, xa, ya, xb, yb) -> dict:
    """矩形板 CCW: [左下,右下,右上,左上] (顶点索引契约见 closure_checks)."""
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


# ---------------------------------------------------------- 公共子结构
def _chain(p, W, D, H, pfx=""):
    """[{pfx}glue][{pfx}w0..w3] 墙链: 返回 (panels, edges, xs)."""
    gw = float(p["glue_w"])
    x1, x2, x3, x4, x5 = gw, gw + W, gw + W + D, gw + 2 * W + D, gw + 2 * W + 2 * D
    g, w0, w1, w2, w3 = (f"{pfx}glue", f"{pfx}w0", f"{pfx}w1", f"{pfx}w2", f"{pfx}w3")
    panels = [_rect(g, "glue", 0.0, 0.0, x1, H),
              _rect(w0, "wall", x1, 0.0, x2, H),
              _rect(w1, "wall", x2, 0.0, x3, H),
              _rect(w2, "wall", x3, 0.0, x4, H),
              _rect(w3, "wall", x4, 0.0, x5, H)]
    edges = [_fold(f"e_g{pfx}", (x1, 0), (x1, H), w0, g, (0.0, 1.0, 0.0), "MOUNTAIN"),
             _fold(f"e_w01{pfx}", (x2, 0), (x2, H), w0, w1, (0.0, 1.0, 0.0)),
             _fold(f"e_w12{pfx}", (x3, 0), (x3, H), w1, w2, (-1.0, 0.0, 0.0)),
             _fold(f"e_w23{pfx}", (x4, 0), (x4, H), w2, w3, (0.0, -1.0, 0.0))]
    return panels, edges, (x1, x2, x3, x4, x5)


def _bottom_full(p, xs, pfx="", walls=("w0", "w1", "w2", "w3"), tdirs=None):
    """底全叠封 4 折翼: 大翼(墙0/墙2)深 D/2, 小翼(墙1/墙3)深 W/2, 全到中线.
    tdirs: 链取向镜像时显式传入 (drawer 链: ((-1,0,0),(0,-1,0),(1,0,0),(0,1,0)))."""
    x1, x2, x3, x4, x5 = xs
    W, D = x2 - x1, x3 - x2
    dm, dn = D / 2.0, W / 2.0
    if tdirs is None:
        tdirs = ((0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (1.0, 0.0, 0.0))
    panels = [_rect(f"{pfx}b0", "flap", x1, -dm, x2, 0.0),
              _rect(f"{pfx}b1", "flap", x2, -dn, x3, 0.0),
              _rect(f"{pfx}b2", "flap", x3, -dm, x4, 0.0),
              _rect(f"{pfx}b3", "flap", x4, -dn, x5, 0.0)]
    edges = [_fold(f"e_{pfx}b0", (x1, 0), (x2, 0), walls[0], f"{pfx}b0",
                   tdirs[0], "MOUNTAIN"),
             _fold(f"e_{pfx}b1", (x2, 0), (x3, 0), walls[1], f"{pfx}b1",
                   tdirs[1], "MOUNTAIN"),
             _fold(f"e_{pfx}b2", (x3, 0), (x4, 0), walls[2], f"{pfx}b2",
                   tdirs[2], "MOUNTAIN"),
             _fold(f"e_{pfx}b3", (x4, 0), (x5, 0), walls[3], f"{pfx}b3",
                   tdirs[3], "MOUNTAIN")]
    return panels, edges


def _dust(p, xs, W, H):
    """2 防尘翼: 侧墙顶缘内折, 深 dust_r*W (0.5 → 远缘中线相抵)."""
    x1, x2, x3, x4, x5 = xs
    dd = float(p["dust_r"]) * W
    panels = [_rect("t1", "flap", x2, H, x3, H + dd),
              _rect("t3", "flap", x4, H, x5, H + dd)]
    edges = [_fold("e_t1", (x2, H), (x3, H), "w1", "t1", (-1.0, 0.0, 0.0), "MOUNTAIN"),
             _fold("e_t3", (x4, H), (x5, H), "w3", "t3", (1.0, 0.0, 0.0), "MOUNTAIN")]
    return panels, edges


def _lid(p, xs, D, H, hinge_back=True, dep=None):
    """主盖 + 插舌. hinge_back=True: 盖自 w2 折向 -y 世界 (覆盖 y∈[D-dep, D]),
    舌入前墙 w0 内面 (y=D-dep 竖面); False: 盖自 w0 折向 +y (覆盖 y∈[0, dep]),
    舌入背墙 w2 内面 (y=dep 竖面). 返回 (panels, edges, lid_id, far_y)."""
    x1, x2, x3, x4, x5 = xs
    td, ins = float(p["tuck_d"]), float(p["ins"])
    dep = float(D if dep is None else dep)
    xa, xb = (x3, x4) if hinge_back else (x1, x2)
    lid_id = "t2" if hinge_back else "t0"
    far_y = D - dep if hinge_back else dep
    lid = _poly(lid_id, "flap", [(xa, H), (xb, H), (xb, H + dep),
                                 (xb - ins, H + dep), (xa + ins, H + dep), (xa, H + dep)])
    edges = [_fold(f"e_{lid_id}", (xa, H), (xb, H),
                   "w2" if hinge_back else "w0", lid_id,
                   (0.0, -1.0, 0.0) if hinge_back else (0.0, 1.0, 0.0), "MOUNTAIN")]
    tongue = _rect("tongue", "flap", xa + ins, H + dep, xb - ins, H + dep + td)
    edges.append(_fold("e_tongue", (xa + ins, H + dep), (xb - ins, H + dep),
                       lid_id, "tongue", (0.0, 0.0, -1.0), "MOUNTAIN"))
    return [lid, tongue], edges, lid_id, far_y


# ---------------------------------------------------------- ① tuck_top_box
def _build_tuck(p):
    W, D, H = float(p["W"]), float(p["D"]), float(p["H"])
    panels, edges, xs = _chain(p, W, D, H)
    bp, be = _bottom_full(p, xs)
    dp, de = _dust(p, xs, W, H)
    lp, le, _, _ = _lid(p, xs, D, H)
    notes = ("tuck_top_box: 4 墙链 + 底全叠封(大小翼全到中线) + 2 防尘翼(中线相抵) "
             f"+ 顶插盖(主盖深 D 自背墙 w2, 插舌深 {p['tuck_d']:g} 入前墙内面)")
    return panels + bp + dp + lp, edges + be + de + le, notes, _features("glue")


# ---------------------------------------------------------- ② hanger_box
def _build_hanger(p):
    W, D, H = float(p["W"]), float(p["D"]), float(p["H"])
    th, sw, sd = float(p["tab_h"]), float(p["slot_w"]), float(p["slot_d"])
    panels, edges, xs = _chain(p, W, D, H)
    x3, x4 = xs[2], xs[3]
    bp, be = _bottom_full(p, xs)
    dp, de = _dust(p, xs, W, H)
    lp, le, _, _ = _lid(p, xs, D, H, hinge_back=False)
    # 挂片: 背墙 w2 顶缘同面直立延伸, 顶缘中央凹口槽 = 挂孔 (凹口非凸多边形)
    xc, hs = x3 + W / 2.0, sw / 2.0
    tab = _poly("tab", "flap",
                [(x3, H), (x4, H), (x4, H + th),
                 (xc + hs, H + th), (xc + hs, H + th - sd),
                 (xc - hs, H + th - sd), (xc - hs, H + th), (x3, H + th)])
    edges.append(_fold("e_tab", (x3, H), (x4, H), "w2", "tab", (0.0, 0.0, 1.0), "MOUNTAIN"))
    notes = ("hanger_box: tuck_top 变体 — 盖自前墙 w0 (插舌入背墙内面), 背墙顶缘挂片 "
             f"(高 {th:g}, 与背墙共面直立) 顶缘中央凹口槽 {sw:g}×{sd:g} 为挂孔(凹口多边形)")
    return (panels + bp + dp + lp + [tab], edges + be + de + le,
            notes, _features("glue"))


# ---------------------------------------------------------- ③ window_box
def _build_window(p):
    W, D, H = float(p["W"]), float(p["D"]), float(p["H"])
    bw, tw, lw_ = float(p["bw"]), float(p["tw_s"]), float(p["lw"])
    gw = float(p["glue_w"])
    win_h = H - tw - bw
    x1, x2 = gw, gw + W
    x3, x4, x5 = x2 + D, x2 + D + W, x2 + 2 * D + W
    panels = [_poly("glue", "glue", [(0.0, 0.0), (x1, 0.0), (x1, bw), (x1, H), (0.0, H)]),
              # 前墙 = 窗框 4 条: 底条入主链 (底棱全宽, 顶棱带左铰链分点)
              _poly("wb", "wall", [(x1, 0), (x2, 0), (x2, bw), (x1 + lw_, bw), (x1, bw)]),
              _poly("w1", "wall", [(x2, 0), (x3, 0), (x3, H), (x2, H), (x2, bw)]),
              _rect("w2", "wall", x3, 0.0, x4, H),
              _rect("w3", "wall", x4, 0.0, x5, H),
              # 窗框绕行链: 左条(wb 顶棱左段) → 顶条(wl 顶棱, 底棱带左右分点) → 右条(wt 底棱右段)
              _rect("wl", "wall", x1, bw, x1 + lw_, bw + win_h),
              _poly("wt", "wall", [(x1, bw + win_h + tw), (x1, bw + win_h),
                                   (x1 + lw_, bw + win_h), (x2 - lw_, bw + win_h),
                                   (x2, bw + win_h), (x2, bw + win_h + tw)]),
              _rect("wr", "wall", x2 - lw_, bw, x2, bw + win_h)]
    edges = [
        _fold("e_g", (x1, 0), (x1, bw), "wb", "glue", (0.0, 1.0, 0.0), "MOUNTAIN"),
        _fold("e_w01", (x2, 0), (x2, bw), "wb", "w1", (0.0, 1.0, 0.0)),
        _fold("e_w12", (x3, 0), (x3, H), "w1", "w2", (-1.0, 0.0, 0.0)),
        _fold("e_w23", (x4, 0), (x4, H), "w2", "w3", (0.0, -1.0, 0.0)),
        # 窗框平折共面链 (180° 展平: tdir = away 原向, 零转)
        _fold("e_wl", (x1, bw), (x1 + lw_, bw), "wb", "wl", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_wt", (x1, bw + win_h), (x1 + lw_, bw + win_h), "wl", "wt",
              (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_wr", (x2 - lw_, bw + win_h), (x2, bw + win_h), "wt", "wr",
              (0.0, 0.0, -1.0), "MOUNTAIN"),
    ]
    xs = (x1, x2, x3, x4, x5)
    bp, be = _bottom_full(p, xs, walls=("wb", "w1", "w2", "w3"))
    dp, de = _dust(p, xs, W, H)
    lp, le, _, _ = _lid(p, xs, D, H)
    notes = (f"window_box: 前墙拆窗框 4 条 (底 {bw:g}/左 {lw_:g}/顶 {tw:g}/右 {lw_:g}) "
             f"绕线平折共面, 窗洞 {W - 2 * lw_:g}×{win_h:g} (网并集=带孔单环); "
             "顶插盖 + 防尘翼 + 底全叠封同 tuck_top")
    return panels + bp + dp + lp, edges + be + de + le, notes, _features("glue")


# ---------------------------------------------------------- ④ two_piece
def _flange(p, walls, up=True, pfx=""):
    """外翻缘: walls = [(pid, xa, xb, H, tdir_out)], 顶缘/底缘水平外折深 rf."""
    rf = float(p["rf"])
    panels, edges = [], []
    for i, (pid, xa, xb, hh, tdir) in enumerate(walls):
        y0, y1 = (hh, hh + rf) if up else (-rf, 0.0)
        panels.append(_rect(f"{pfx}e{i}", "flap", xa, y0, xb, y1))
        edges.append(_fold(f"e_{pfx}e{i}", (xa, hh), (xb, hh), pid, f"{pfx}e{i}",
                           tdir, "MOUNTAIN"))
    return panels, edges


def _build_two_piece(p):
    W, D, H = float(p["W"]), float(p["D"]), float(p["H"])
    cl, fr, gw, webw = float(p["clear"]), float(p["friction"]), float(p["glue_w"]), float(p["web_w"])
    rf = float(p["rf"])
    Wl, Dl, Hl = W + 2 * cl, D + 2 * cl, H + fr

    # --- 内盒 (base): [glue_b][bw0..bw3] + 底全叠封 + 顶缘外翻缘
    panels, edges, xs = _chain(p, W, D, H, pfx="b")
    bp, be = _bottom_full(p, xs, pfx="b", walls=("bw0", "bw1", "bw2", "bw3"))
    x1, x2, x3, x4, x5 = xs
    fpan, fed = _flange(p, [("bw0", x1, x2, H, (0.0, -1.0, 0.0)),
                            ("bw1", x2, x3, H, (1.0, 0.0, 0.0)),
                            ("bw2", x3, x4, H, (0.0, 1.0, 0.0)),
                            ("bw3", x4, x5, H, (-1.0, 0.0, 0.0))], up=True, pfx="b")
    panels += bp + fpan
    edges += be + fed

    # --- web 工艺条: 铰链于 bw3 自由缘 (世界 x=0, y=0 竖线), 平折至 y=0 平面 x∈[-webw,0]
    xw0, xw1 = x5, x5 + webw
    panels.append(_rect("web", "flap", xw0, 0.0, xw1, H))
    edges.append(_fold("e_web", (xw0, 0), (xw0, H), "bw3", "web", (-1.0, 0.0, 0.0), "MOUNTAIN"))

    # --- 盖 (lid): 链自 web 远缘向 -x 世界展开; lwF 左棱带 H 分点 (web 高 H < Hl)
    X = xw1
    panels += [
        _poly("lwF", "wall", [(X, 0), (X + Wl, 0), (X + Wl, Hl), (X, Hl), (X, H)]),
        _rect("lwR", "wall", X + Wl, 0.0, X + Wl + Dl, Hl),
        _rect("lwB", "wall", X + Wl + Dl, 0.0, X + 2 * Wl + Dl, Hl),
        _rect("lwL", "wall", X + 2 * Wl + Dl, 0.0, X + 2 * Wl + 2 * Dl, Hl),
        _rect("glue_l", "glue", X + 2 * Wl + 2 * Dl, 0.0, X + 2 * Wl + 2 * Dl + gw, Hl),
    ]
    edges += [
        _fold("e_lwf", (X, 0), (X, H), "web", "lwF", (0.0, 1.0, 0.0), "MOUNTAIN"),
        _fold("e_lwr", (X + Wl, 0), (X + Wl, Hl), "lwF", "lwR", (-1.0, 0.0, 0.0)),
        _fold("e_lwb", (X + Wl + Dl, 0), (X + Wl + Dl, Hl), "lwR", "lwB", (0.0, -1.0, 0.0)),
        _fold("e_lwl", (X + 2 * Wl + Dl, 0), (X + 2 * Wl + Dl, Hl), "lwB", "lwL", (1.0, 0.0, 0.0)),
        _fold("e_gl", (X + 2 * Wl + 2 * Dl, 0), (X + 2 * Wl + 2 * Dl, Hl),
              "lwL", "glue_l", (0.0, 1.0, 0.0), "MOUNTAIN"),
    ]
    # 盖顶全叠封 (z=Hl 平面, 远缘互抵盖中心) + 盖口缘外翻缘 (z=0 平面向外)
    xL1, xL2, xL3, xL4, xL5 = X, X + Wl, X + Wl + Dl, X + 2 * Wl + Dl, X + 2 * Wl + 2 * Dl
    dm, dn = Dl / 2.0, Wl / 2.0
    ltop = [_rect("ltF", "flap", xL1, Hl, xL2, Hl + dm),
            _rect("ltR", "flap", xL2, Hl, xL3, Hl + dn),
            _rect("ltB", "flap", xL3, Hl, xL4, Hl + dm),
            _rect("ltL", "flap", xL4, Hl, xL5, Hl + dn)]
    lte = [_fold("e_ltF", (xL1, Hl), (xL2, Hl), "lwF", "ltF", (-1.0, 0.0, 0.0), "MOUNTAIN"),
           _fold("e_ltR", (xL2, Hl), (xL3, Hl), "lwR", "ltR", (0.0, -1.0, 0.0), "MOUNTAIN"),
           _fold("e_ltB", (xL3, Hl), (xL4, Hl), "lwB", "ltB", (1.0, 0.0, 0.0), "MOUNTAIN"),
           _fold("e_ltL", (xL4, Hl), (xL5, Hl), "lwL", "ltL", (0.0, 1.0, 0.0), "MOUNTAIN")]
    lfpan, lfed = _flange(p, [("lwF", xL1, xL2, 0.0, (1.0, 0.0, 0.0)),
                              ("lwR", xL2, xL3, 0.0, (0.0, 1.0, 0.0)),
                              ("lwB", xL3, xL4, 0.0, (-1.0, 0.0, 0.0)),
                              ("lwL", xL4, xL5, 0.0, (0.0, -1.0, 0.0))], up=False, pfx="l")
    panels += ltop + lfpan
    edges += lte + lfed

    notes = (f"two_piece: 天地盖两件分离拓扑 (网内 web 条 {webw:g}mm 相连供整版, "
             f"成型后不折接) — 内盒 {W:g}×{D:g}×{H:g} (底全叠封+顶缘外翻缘 {rf:g}), "
             f"盖内空 {Wl:g}×{Dl:g}×{Hl:g} (clear {cl:g}, 盖深 = H+friction {fr:g}, "
             "顶全叠封+口缘外翻缘), 世界系两件分离摆放")
    return panels, edges, notes, _features("bglue", "glue_l")


# ---------------------------------------------------------- ⑤ dispenser_top
def _build_dispenser(p):
    W, D, H = float(p["W"]), float(p["D"]), float(p["H"])
    hw, ad = float(p["hw"]), float(p["ad"])
    ins = float(p["ins"])
    dep = D / 2.0
    panels, edges, xs = _chain(p, W, D, H)
    x1, x2, x3, x4, x5 = xs
    xc = x1 + W / 2.0
    bp, be = _bottom_full(p, xs)
    dp, de = _dust(p, xs, W, H)
    # 主盖: 深 D/2 自背墙, 远缘带分点 (中央舌铰链)
    t2 = _poly("t2", "flap", [(x3, H), (x4, H), (x4, H + dep),
                              (x4 - ins, H + dep), (x3 + ins, H + dep), (x3, H + dep)])
    tongue = _rect("tongue", "flap", x3 + ins, H + dep, x4 - ins, H + dep + float(p["tuck_d"]))
    edges += [_fold("e_t2", (x3, H), (x4, H), "w2", "t2", (0.0, -1.0, 0.0), "MOUNTAIN"),
              _fold("e_tongue", (x3 + ins, H + dep), (x4 - ins, H + dep),
                    "t2", "tongue", (0.0, 0.0, -1.0), "MOUNTAIN")]
    # 顶前翼 f0: 前墙顶缘平折成顶面前半 (membrane 直折), 远缘中央缺角 = 抽取口
    f0 = _poly("f0", "flap", [(x1, H), (x2, H), (x2, H + dep),
                              (xc + hw, H + dep), (xc + hw, H + dep - ad),
                              (xc - hw, H + dep - ad), (xc - hw, H + dep), (x1, H + dep)])
    edges.append(_fold("e_f0", (x1, H), (x2, H), "w0", "f0", (0.0, 1.0, 0.0), "MOUNTAIN"))
    notes = (f"dispenser_top: 主盖深 D/2 自背墙 (远缘中央下折舌为抽取口推片), "
             f"前墙顶翼 f0 深 D/2 membrane 直折成顶面前半, 远缘中央缺角 {2 * hw:g}×{ad:g} "
             "即抽取口 (缺角多边形); 防尘翼+底全叠封同 tuck_top")
    return panels + bp + dp + [t2, tongue, f0], edges + be + de, notes, _features("glue")


# ---------------------------------------------------------- ⑥ slide_box
def _build_slide(p):
    W, D, H = float(p["W"]), float(p["D"]), float(p["H"])
    cs, drop, gw, webw = float(p["cs"]), float(p["drop"]), float(p["glue_w"]), float(p["web_w"])
    bs = float(p["bs"])
    Hd, Ws, Ds = H - drop, W + 2 * cs, D + 2 * cs

    # --- 外套筒: [glue_s][sw0..sw3] 两端开放 (无折翼); sw3 自由棱带 Hd 分点 (web 铰链)
    x1, x2 = gw, gw + Ws
    x3, x4, x5 = x2 + Ds, x2 + Ds + Ws, x2 + 2 * Ds + Ws
    panels = [_rect("glue_s", "glue", 0.0, 0.0, x1, H),
              _rect("sw0", "wall", x1, 0.0, x2, H),
              _rect("sw1", "wall", x2, 0.0, x3, H),
              _rect("sw2", "wall", x3, 0.0, x4, H),
              _poly("sw3", "wall", [(x4, 0), (x5, 0), (x5, Hd), (x5, H), (x4, H)])]
    edges = [_fold("e_gs", (x1, 0), (x1, H), "sw0", "glue_s", (0.0, 1.0, 0.0), "MOUNTAIN"),
             _fold("e_sw01", (x2, 0), (x2, H), "sw0", "sw1", (0.0, 1.0, 0.0)),
             _fold("e_sw12", (x3, 0), (x3, H), "sw1", "sw2", (-1.0, 0.0, 0.0)),
             _fold("e_sw23", (x4, 0), (x4, H), "sw2", "sw3", (0.0, -1.0, 0.0))]

    # --- web 条: 铰链于 sw3 自由棱下段 (世界 x=0, y=0, z∈[0,Hd]), 平折 y=0 平面
    xw0, xw1 = x5, x5 + webw
    X = xw1
    panels.append(_rect("web", "flap", xw0, 0.0, xw1, Hd))
    edges.append(_fold("e_web", (xw0, 0), (xw0, Hd), "sw3", "web", (-1.0, 0.0, 0.0), "MOUNTAIN"))

    # --- 内抽屉: 链自 web 远缘 (dwF 左棱全段 = 铰链) 向 -x 世界展开
    panels += [_rect("dwF", "wall", X, 0.0, X + W, Hd),
               _rect("dwR", "wall", X + W, 0.0, X + W + D, Hd),
               _rect("dwB", "wall", X + W + D, 0.0, X + 2 * W + D, Hd),
               _rect("dwL", "wall", X + 2 * W + D, 0.0, X + 2 * W + 2 * D, Hd),
               _rect("glue_d", "glue", X + 2 * W + 2 * D, 0.0, X + 2 * W + 2 * D + gw, Hd)]
    edges += [_fold("e_dwf", (X, 0), (X, Hd), "web", "dwF", (0.0, 1.0, 0.0), "MOUNTAIN"),
              _fold("e_dwr", (X + W, 0), (X + W, Hd), "dwF", "dwR", (-1.0, 0.0, 0.0)),
              _fold("e_dwb", (X + W + D, 0), (X + W + D, Hd), "dwR", "dwB", (0.0, -1.0, 0.0)),
              _fold("e_dwl", (X + 2 * W + D, 0), (X + 2 * W + D, Hd), "dwB", "dwL", (1.0, 0.0, 0.0)),
              _fold("e_gd", (X + 2 * W + 2 * D, 0), (X + 2 * W + 2 * D, Hd),
                    "dwL", "glue_d", (0.0, 1.0, 0.0), "MOUNTAIN")]
    # 抽屉底全叠封 (drawer 链向 -x 世界展开 → tdirs 镜像) + 前墙内面挡板 (顶缘下折内面)
    xD = (X, X + W, X + W + D, X + 2 * W + D, X + 2 * W + 2 * D)
    dbp, dbe = _bottom_full(p, xD, pfx="d", walls=("dwF", "dwR", "dwB", "dwL"),
                            tdirs=((-1.0, 0.0, 0.0), (0.0, -1.0, 0.0),
                                   (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))
    baffle = _rect("baffle", "flap", X, Hd, X + W, Hd + bs)
    edges.append(_fold("e_baffle", (X, Hd), (X + W, Hd), "dwF", "baffle",
                       (0.0, 0.0, -1.0), "MOUNTAIN"))
    panels += dbp + [baffle]
    edges += dbe

    notes = (f"slide_box: 抽屉盒两件分离拓扑 (网内 web 条 {webw:g}mm 相连, 成型后分离) — "
             f"外套筒 {Ws:g}×{Ds:g}×{H:g} 两端开放 (内空 = 抽屉+2*cs, cs={cs:g}), "
             f"内抽屉 {W:g}×{D:g}×{Hd:g} (底全叠封 + 前墙内面挡板深 {bs:g}), "
             "世界系两件分离摆放")
    return panels, edges, notes, _features("glue_s", "glue_d")


_BUILDERS = {0: _build_tuck, 1: _build_hanger, 2: _build_window,
             3: _build_two_piece, 4: _build_dispenser, 5: _build_slide}


# ---------------------------------------------------------------- 契约
def class_params(cls_id: str) -> dict:
    """类ID → 全键参数表 (批量 build_ir 判型与取值的唯一权威)."""
    k = _KIND[cls_id]
    p = {key: 0.0 for key in PARAM_ORDER}
    p["kind"] = k
    if cls_id == "tuck_top_box":
        p.update({"W": 110.0, "D": 70.0, "H": 60.0, "glue_w": 12.0, "board_t": 0.45,
                  "tuck_d": 12.0, "dust_r": 0.5, "ins": 12.0})
    elif cls_id == "hanger_box":
        p.update({"W": 90.0, "D": 55.0, "H": 140.0, "glue_w": 12.0, "board_t": 0.45,
                  "tuck_d": 12.0, "dust_r": 0.5, "ins": 12.0,
                  "tab_h": 32.0, "slot_w": 10.0, "slot_d": 12.0})
    elif cls_id == "window_box":
        p.update({"W": 110.0, "D": 70.0, "H": 60.0, "glue_w": 12.0, "board_t": 0.45,
                  "tuck_d": 12.0, "dust_r": 0.5, "ins": 12.0,
                  "bw": 20.0, "tw_s": 14.0, "lw": 18.0})
    elif cls_id == "two_piece":
        p.update({"W": 80.0, "D": 60.0, "H": 45.0, "glue_w": 12.0, "board_t": 0.45,
                  "clear": 1.5, "friction": 2.0, "rf": 5.0, "web_w": 6.0})
    elif cls_id == "dispenser_top":
        p.update({"W": 110.0, "D": 70.0, "H": 60.0, "glue_w": 12.0, "board_t": 0.45,
                  "tuck_d": 12.0, "dust_r": 0.5, "ins": 12.0, "hw": 18.0, "ad": 8.0})
    elif cls_id == "slide_box":
        p.update({"W": 100.0, "D": 60.0, "H": 40.0, "glue_w": 12.0, "board_t": 0.45,
                  "cs": 1.5, "drop": 6.0, "bs": 25.0, "web_w": 6.0})
    return p


def validate_params(params: dict) -> None:
    """参数语义: 相关键非零才校验 (家族不适用键置 0)."""
    pos = lambda k: isinstance(params.get(k), (int, float)) and \
        not isinstance(params.get(k), bool) and float(params.get(k)) > 0

    def need(*keys):
        for k in keys:
            if not pos(k):
                raise ValueError(f"非法参数 {k}={params.get(k)!r} (须正数)")

    if pos("glue_w") and pos("W") and pos("D") and \
            float(params["glue_w"]) >= min(float(params["W"]), float(params["D"])):
        raise ValueError(f"粘口 glue_w={params['glue_w']} 须窄于最短墙 "
                         f"min(W,D)={min(params['W'], params['D'])}")
    if pos("dust_r") and not (0.0 < float(params["dust_r"]) <= 0.5):
        raise ValueError(f"非法参数 dust_r={params['dust_r']!r} (须 (0, 0.5])")
    if pos("tuck_d") and pos("H") and float(params["tuck_d"]) >= float(params["H"]):
        raise ValueError("插舌深 tuck_d 须小于盒高 H")
    if pos("tab_h") and pos("slot_d") and float(params["slot_d"]) >= float(params["tab_h"]):
        raise ValueError("挂孔深 slot_d 须小于挂片高 tab_h")
    if pos("slot_w") and pos("W") and pos("ins") and \
            float(params["slot_w"]) >= float(params["W"]) - 2 * float(params["ins"]):
        raise ValueError("挂孔宽 slot_w 须窄于挂片 (W - 2*ins)")
    if pos("bw") and pos("tw_s") and pos("H") and \
            float(params["bw"]) + float(params["tw_s"]) >= float(params["H"]):
        raise ValueError("窗框 bw + tw_s 须小于 H (窗洞 win_h > 0)")
    if pos("tw_s") and pos("tuck_d") and float(params["tw_s"]) <= float(params["tuck_d"]):
        raise ValueError("窗框顶条 tw_s 须大于插舌深 tuck_d (插舌不触侧条)")
    if pos("lw") and pos("W") and 2 * float(params["lw"]) >= float(params["W"]):
        raise ValueError("窗框侧条 2*lw 须窄于 W")
    if pos("hw") and pos("W") and pos("ins") and \
            2 * float(params["hw"]) >= float(params["W"]) - 2 * float(params["ins"]):
        raise ValueError("抽取口宽 2*hw 须窄于 (W - 2*ins)")
    if pos("ad") and pos("D") and float(params["ad"]) >= float(params["D"]) / 2.0:
        raise ValueError("抽取口深 ad 须小于 D/2")
    if pos("rf") and pos("W") and pos("D") and \
            float(params["rf"]) >= min(float(params["W"]), float(params["D"])) / 2.0:
        raise ValueError("外翻缘 rf 须窄于半最短墙")
    if pos("drop") and pos("H") and float(params["drop"]) >= float(params["H"]):
        raise ValueError("抽屉落差 drop 须小于套筒高 H")
    if pos("bs") and pos("W") and float(params["bs"]) >= float(params["W"]):
        raise ValueError("挡板深 bs 须小于抽屉宽 W")


def build_ir(params: dict | None = None) -> dict:
    p = {**DEFAULTS, **(params or {})}
    kind = int(p.get("kind", 0))
    if kind not in _BUILDERS:
        raise ValueError(f"非法 kind={kind!r} (须 0..5)")
    cls_id = _CLS[kind]
    panels, edges, notes, feats = _BUILDERS[kind](p)
    root = {0: "w0", 1: "w0", 2: "wb", 3: "bw0", 4: "w0", 5: "sw0"}[kind]
    return {
        "meta": {"ir_version": "0.1", "units": "mm",
                 "generator": "photo_dieline.parametric.box_essentials 0.1",
                 "notes": notes,
                 "root_panel": root,
                 "root_frame": {"R": _R_CHAIN, "off": [-float(p["glue_w"]), 0.0, 0.0]}},
        "package": {"type": cls_id,
                    "template": {"id": cls_id, "version": "0.1"},
                    "params": {k: float(p[k]) for k in PARAM_ORDER},
                    "photo": None},
        "panels": panels,
        "edges": edges,
        "features": feats,
    }


def analytic_bbox(params: dict) -> dict:
    """G05 期望: solid (wall 角色) 折叠 bbox. ④/⑥ 两件分离摆放, 联合 bbox."""
    p = {**DEFAULTS, **(params or {})}
    kind = int(p.get("kind", 0))
    W, D, H = float(p["W"]), float(p["D"]), float(p["H"])
    if kind in (0, 1, 2, 4):
        return {"W": W, "D": D, "H": H}
    webw = float(p["web_w"])
    if kind == 3:  # 内盒 x∈[0,W]; 盒盖 x∈[-webw-Dl, -webw], y∈[0,Wl], z∈[0,Hl]
        cl, fr = float(p["clear"]), float(p["friction"])
        Wl, Dl, Hl = W + 2 * cl, D + 2 * cl, H + fr
        return {"W": W + webw + Dl, "D": max(D, Wl), "H": Hl}
    cs = float(p["cs"])  # 套筒 x∈[0,Ws]; 抽屉 x∈[-webw-D, -webw], y∈[0,W], z∈[0,H-drop]
    return {"W": webw + D + W + 2 * cs, "D": max(D + 2 * cs, W), "H": H}


def solid_roles():
    return ("wall",)


def allowed_overlap():
    """G06 允许叠层 (真实工艺契约, 全家族并集):
    粘口贴末墙/邻墙内面; 插舌入墙内面; 挡板贴前墙内面; 环闭合末墙↔首墙缝."""
    s = {
        frozenset({"glue", "w3"}), frozenset({"bglue", "bw3"}),
        frozenset({"glue_l", "lwF"}), frozenset({"glue_s", "sw3"}),
        frozenset({"glue_d", "dwF"}),
        frozenset({"tongue", "w0"}), frozenset({"tongue", "w2"}),
        frozenset({"tongue", "wt"}),        # 窗框顶条后插舌
        frozenset({"baffle", "dwF"}),       # 挡板贴抽屉前墙内面
        frozenset({"glue_d", "baffle"}),    # 粘缝与挡板同面层压
        frozenset({"bw0", "bw3"}), frozenset({"lwL", "lwF"}),
        frozenset({"sw0", "sw3"}), frozenset({"dwL", "dwF"}),
        frozenset({"web", "lwL"}),          # web 与盖左棱共环缝贴合
    }
    return s


# ---------------------------------------------------------------- closure
def _fm(world, pid, i, j):
    return (np.asarray(world[pid][i], float) + np.asarray(world[pid][j], float)) / 2.0


def _d(a, b) -> float:
    return float(np.linalg.norm(np.asarray(a, float) - np.asarray(b, float)))


def _closure_single(ir, world, kind):
    """单件类 (①②③⑤): 墙环缝 + 粘缝 + 底全叠封 + 防尘翼 + 盖/舌 (+窗框/挂片/抽取口)."""
    W, D, H = ir.param("W"), ir.param("D"), ir.param("H")
    td = ir.param("tuck_d")
    res: dict[str, float] = {}
    if kind != 2:  # 窗框类环缝由 seam.bot/seam.top 分段承担
        res["ring.w3_w0"] = _d(_fm(world, "w3", 1, 2), _fm(world, "w0", 0, 3))
    res["glue.seat"] = abs(float(np.mean(np.asarray(world["glue"]), axis=0)[0]))
    res["b.major.meet"] = _d(_fm(world, "b0", 0, 1), _fm(world, "b2", 0, 1))
    res["b.minor.meet"] = _d(_fm(world, "b1", 0, 1), _fm(world, "b3", 0, 1))
    res["b.major.z0"] = max(abs(float(_fm(world, "b0", 0, 1)[2])),
                            abs(float(_fm(world, "b2", 0, 1)[2])))
    res["dust.meet"] = _d(_fm(world, "t1", 2, 3), _fm(world, "t3", 2, 3))
    res["dust.zH"] = max(abs(float(_fm(world, "t1", 2, 3)[2]) - H),
                         abs(float(_fm(world, "t3", 2, 3)[2]) - H))
    # 盖远缘/插舌: kind1 盖自前墙 (远缘落 y=D, 舌入背墙 y=D); kind4 远缘落 y=D/2; 其余 y=0
    lid_id = "t0" if kind == 1 else "t2"
    lid_far = _fm(world, lid_id, 2, 3)
    far_tgt = D if kind == 1 else (D / 2.0 if kind == 4 else 0.0)
    res["lid.far_y"] = abs(float(lid_far[1]) - far_tgt)
    res["lid.zH"] = abs(float(lid_far[2]) - H)
    tgt_y = D if kind == 1 else (D / 2.0 if kind == 4 else 0.0)
    tm = np.mean(np.asarray(world["tongue"]), axis=0)
    res["tongue.flush"] = abs(float(tm[1]) - tgt_y)
    res["tongue.depth"] = abs(float(_fm(world, "tongue", 2, 3)[2]) - (H - td))
    if kind == 1:  # 挂片: 共面背墙 + 挂孔几何 (凹口槽底/居中)
        tb = np.asarray(world["tab"], float)
        th, sd = ir.param("tab_h"), ir.param("slot_d")
        res["tab.plane_yD"] = abs(float(np.mean(tb[:, 1])) - D)
        res["tab.top_z"] = abs(float(tb[:, 2].max()) - (H + th))
        res["tab.slot_bottom"] = abs(float((tb[4] + tb[5])[2] / 2.0) - (H + th - sd))
        res["tab.slot_center"] = abs(float((tb[3][0] + tb[6][0]) / 2.0) - W / 2.0)
    if kind == 2:  # 窗框: 全框共面前墙平面 + 环缝上下段 (跨链) + 右条落底棱平面
        for pid in ("wb", "wl", "wt", "wr"):
            res[f"frame.{pid}.plane"] = abs(float(np.mean(np.asarray(world[pid]), axis=0)[1]))
        res["seam.bot"] = _d(world["w3"][1], world["wb"][0])
        res["seam.top"] = _d(world["w3"][2], world["wt"][0])
        res["frame.right_bot"] = abs(float(world["wr"][0][2]) - ir.param("bw"))
    if kind == 4:  # 抽取口: f0 缺角几何 + f0/t2 远缘中线相抵
        f0v = np.asarray(world["f0"], float)
        ad = ir.param("ad")
        res["f0.plane_zH"] = abs(float(np.mean(f0v[:, 2])) - H)
        res["f0.far_y"] = abs(float(np.mean(f0v[[2, 7]], axis=0)[1]) - D / 2.0)
        res["f0.notch_bottom_y"] = abs(float((f0v[4] + f0v[5])[1] / 2.0) - (D / 2.0 - ad))
        res["f0.notch_center_x"] = abs(float((f0v[3][0] + f0v[6][0]) / 2.0) - W / 2.0)
        res["t2.far_y"] = abs(float(_fm(world, "t2", 4, 5)[1]) - D / 2.0)
    return res


def _closure_two_piece(ir, world):
    """天地盖: 各自封合 (环缝/粘缝/底·顶全叠封/外翻缘) + 配合证据 (跨件展向差)."""
    H = ir.param("H")
    rf, cl, fr = ir.param("rf"), ir.param("clear"), ir.param("friction")
    res: dict[str, float] = {}
    res["base.ring"] = _d(_fm(world, "bw3", 1, 2), _fm(world, "bw0", 0, 3))
    res["base.glue"] = abs(float(np.mean(np.asarray(world["bglue"]), axis=0)[0]))
    res["base.b.meet"] = _d(_fm(world, "bb0", 0, 1), _fm(world, "bb2", 0, 1))
    res["base.flange.zH"] = abs(float(_fm(world, "be1", 2, 3)[2]) - H)
    res["base.flange.out"] = abs(float(_fm(world, "be1", 2, 3)[0]) - (float(ir.param("W")) + rf))
    res["lid.ring"] = _d(_fm(world, "lwL", 1, 2), _fm(world, "lwF", 0, 3))
    res["lid.glue"] = abs(float(np.mean(np.asarray(world["glue_l"]), axis=0)[0]) + float(ir.param("web_w")))
    res["lid.top.meet"] = _d(_fm(world, "ltF", 2, 3), _fm(world, "ltB", 2, 3))
    res["lid.top.zH"] = abs(float(_fm(world, "ltF", 2, 3)[2]) - (H + fr))
    res["lid.flange.z0"] = abs(float(_fm(world, "le1", 0, 1)[2]))
    xs = np.vstack([world[k] for k in ("bw0", "bw1", "bw2", "bw3")])
    xl = np.vstack([world[k] for k in ("lwF", "lwR", "lwB", "lwL")])
    # 盖链向 -x 展开: 盖 x 向 = 深度 (Dl), y 向 = 宽度 (Wl); 内盒 x 向 = 宽度, y 向 = 深度
    res["fit.depth"] = abs(float(xl[:, 0].max() - xl[:, 0].min())
                           - (float(xs[:, 1].max() - xs[:, 1].min()) + 2 * cl))
    res["fit.width"] = abs(float(xl[:, 1].max() - xl[:, 1].min())
                           - (float(xs[:, 0].max() - xs[:, 0].min()) + 2 * cl))
    zs = np.vstack([world[k] for k in ("bw0", "bw2")])[:, 2]
    zl = np.vstack([world[k] for k in ("lwF", "lwB")])[:, 2]
    res["fit.z_span"] = abs(float(zl.max() - zl.min()) - (float(zs.max() - zs.min()) + fr))
    return res


def _closure_slide(ir, world):
    """套筒/抽屉: 各自封合 + 三向配合证据 (套筒内空 = 抽屉 + 2*cs, 高差 drop)."""
    cs, drop = ir.param("cs"), ir.param("drop")
    res: dict[str, float] = {}
    res["sleeve.ring"] = _d(_fm(world, "sw3", 1, 3), _fm(world, "sw0", 0, 3))
    res["sleeve.glue"] = abs(float(np.mean(np.asarray(world["glue_s"]), axis=0)[0]))
    res["drawer.ring"] = _d(_fm(world, "dwL", 1, 2), _fm(world, "dwF", 0, 3))
    res["drawer.glue"] = abs(float(np.mean(np.asarray(world["glue_d"]), axis=0)[0]) + float(ir.param("web_w")))
    res["drawer.b.meet"] = _d(_fm(world, "db0", 0, 1), _fm(world, "db2", 0, 1))
    res["drawer.b.z0"] = abs(float(_fm(world, "db0", 0, 1)[2]))
    bfv = np.asarray(world["baffle"], float)
    res["baffle.seat"] = abs(float(np.mean(bfv[:, 0])) + float(ir.param("web_w")))
    res["baffle.depth"] = abs(float(bfv[:, 2].max()) - float(ir.param("H") - drop))
    xs = np.vstack([world[k] for k in ("sw0", "sw1", "sw2", "sw3")])
    xd = np.vstack([world[k] for k in ("dwF", "dwR", "dwB", "dwL")])
    # 套筒链沿 +x (x 向 = 套筒宽 Ws); 抽屉链向 -x (x 向 = 抽屉深 D, y 向 = 抽屉宽 W)
    res["fit.width"] = abs(float(xs[:, 0].max() - xs[:, 0].min())
                           - (float(xd[:, 1].max() - xd[:, 1].min()) + 2 * cs))
    res["fit.depth"] = abs(float(xs[:, 1].max() - xs[:, 1].min())
                           - (float(xd[:, 0].max() - xd[:, 0].min()) + 2 * cs))
    zd = np.vstack([world[k] for k in ("dwF", "dwB")])[:, 2]
    res["fit.z_span"] = abs(float(ir.param("H")) - (float(zd.max() - zd.min()) + drop))
    return res


def closure_checks(ir, world) -> dict:
    kind = _KIND[ir.package["template"]["id"]]
    if kind == 3:
        return _closure_two_piece(ir, world)
    if kind == 5:
        return _closure_slide(ir, world)
    return _closure_single(ir, world, kind)


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


def probe(ir, fold_all, from_raw):
    """负探针: 每类扰动 2 条关键折线 (edge, 铰链轴) → closure 最大残差须爆到 mm 级.
    返回 {edge_id: (baseline_max, perturbed_max)}."""
    raw = ir.raw
    base = max(float(v) for v in closure_checks(ir, fold_all(ir)).values())
    kind = _KIND[ir.package["template"]["id"]]
    targets = {0: [("e_t2", (1, 0, 0)), ("e_b0", (1, 0, 0))],
               1: [("e_t0", (1, 0, 0)), ("e_tab", (1, 0, 0))],
               2: [("e_wt", (1, 0, 0)), ("e_tongue", (1, 0, 0))],
               3: [("e_ltB", (0, -1, 0)), ("e_bb0", (1, 0, 0))],
               4: [("e_f0", (1, 0, 0)), ("e_t2", (1, 0, 0))],
               5: [("e_dwb", (0, 0, 1)), ("e_baffle", (0, 1, 0))]}[kind]
    out = {}
    for eid, ax in targets:
        irp = from_raw(_perturb(raw, eid, ax))
        worst = max(float(v) for v in closure_checks(irp, fold_all(irp)).values())
        out[eid] = (base, worst)
    return out
