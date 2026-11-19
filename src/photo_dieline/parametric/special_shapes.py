"""special_shapes: 特形七类 (第四波动物园).

类ID:
  gable_rect_base     矩形基底屋顶包: W≠D, 山墙三角位于 D 宽墙 (apex 随脊偏移),
                      双坡为矩形板: 前坡斜长 hypot(a,Hr), 后坡 hypot(D-a,Hr),
                      a = D/2 + ridge_off (脊偏移量参数化, ridge_off=0 即对称 gable),
                      过脊双鳍 (顶缘距 fin_gap_mm) + 4 底板到中线
  rsc_display_panel   展示面板箱: RSC 墙环 (前墙矮 Hf, 背/侧墙高 H) + 前墙顶缘 45°
                      外折展示板 (净深 D*sqrt2, 远缘精确抵背墙顶缘, 锁定 H=Hf+D)
                      + 顶 3 折翼 (大翼自背墙到中线, 小翼自侧墙) + 底 4 RSC 折翼
  tray_lid_overfit    连体翻盖托盘: 星形托盘 (底盘+4墙+4角片全高粘邻墙内面,
                      tray_4corner 同款) + 一体盖绕背墙顶缘铰链前翻扣合
                      (盖深 D 覆口缘 + 前裙深 H 外贴前墙)
  hexagonal_flip      六角翻盖盒: 6 墙环形链 + 3 组对折盖 (对位墙 w_k/w_{k+3} 各一片,
                      深 = apothem, 远缘中点全落中心轴 z=H) + 全重叠粘缝
  tube_double_seam    双缝管: 8 边形近似直管 (环形墙链+全重叠粘缝, 粘宽=墙宽)
                      + 两端各 8 片内折盘 (深 = apothem, 远缘中点落轴);
                      反向缝位: 底端短盘 (深 a-g) 在 w7, 顶端短盘在对位墙 w3
  mailer_diecut       镂空邮寄盒: 书封式 (书脊 + 左右 90° 翻盖 + 插舌 180° 反贴)
                      + 左盖面内镂空窗口: 窗框 4 条绕窗共面平折链 (底/左/顶/右条),
                      网并集 = 带孔单环 (窗洞 x∈[-C+wl,-wl], y∈[bw,h-tw])
  divided_tray_3comp  三分格托盘: 共享底盘 + 4 围墙 + 隔板十字 (纵隔板全宽 y=D/2 +
                      横隔板全深 x=xt, 正交 T 字相贯) — 三区: 左上/左下/右区
                      (egg_tray 分隔模式: 隔板自底盘铰链立起)

拓扑声明 (meta.notes 逐类): tray_lid_overfit 为连体单件 (盖绕背墙铰链不可分离,
非两件分离拓扑); 本家族全部为单件连体, 无两件分离拓扑, 网并集皆单环 (无需 web 条)。

几何约定: 链式类 root=首墙 net(x,y)→world(x,0,y), off=[-gw,0,0];
星形类 root=底盘 net(x,y)→world(x,y,0)。所有折线显式 target_dir_3d。
closure 全部为折叠后世界坐标跨链残差; 负探针 probe() 见模块底部。
"""
from __future__ import annotations

import copy
import math

import numpy as np

from . import base as _base

PARAM_ORDER = ["kind", "W", "D", "H", "glue_w", "board_t", "Hb", "Hr", "ridge_off",
               "Ef", "fin_gap_mm", "Hf", "flap_ratio", "side", "h", "g",
               "S", "C", "t", "bw", "tw", "wl", "xt"]
DEFAULTS = {k: 0.0 for k in PARAM_ORDER}
DEFAULTS.update({"board_t": 0.45})

_CLS = ("gable_rect_base", "rsc_display_panel", "tray_lid_overfit",
        "hexagonal_flip", "tube_double_seam", "mailer_diecut",
        "divided_tray_3comp")
_KIND = {c: i for i, c in enumerate(_CLS)}

for _cid in _CLS:
    _base.register(_cid, "special_shapes")

_R_CHAIN = [[1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0]]  # net(x,y)→world(x,0,y)
_R_STAR = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]   # net(x,y)→world(x,y,0)


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


def _poly_ring(n, side, cx, cy):
    """正 n 边形 (edge0 落 y=0, x∈[0,side]); 返回顶点/外法线/切向 (net 2D = 世界 xy)."""
    R = side / (2.0 * math.sin(math.pi / n))
    a = side / (2.0 * math.tan(math.pi / n))
    ctr = np.array([cx, cy])
    vs = [ctr + R * np.array([math.cos(-math.pi / 2 - math.pi / n + 2.0 * math.pi * k / n),
                              math.sin(-math.pi / 2 - math.pi / n + 2.0 * math.pi * k / n)])
          for k in range(n)]
    outward, tangent = [], []
    for k in range(n):
        em = (np.asarray(vs[k], float) + np.asarray(vs[(k + 1) % n], float)) / 2.0
        o = _unit(em - ctr)
        outward.append(o)
        tangent.append(np.array([-o[1], o[0]]))
    return vs, outward, tangent, a


# ---------------------------------------------------------- ① gable_rect_base
def _build_gable_rect(p):
    W, D, Hb, Hr = float(p["W"]), float(p["D"]), float(p["Hb"]), float(p["Hr"])
    a = D / 2.0 + float(p["ridge_off"])          # 脊世界 y = a
    Ef, gap, gw = float(p["Ef"]), float(p["fin_gap_mm"]), float(p["glue_w"])
    sF = math.hypot(a, Hr)                       # 前坡斜长 (水平 run = a)
    sB = math.hypot(D - a, Hr)                   # 后坡斜长 (水平 run = D-a)
    lean = math.asin(min(1.0, (gap / 2.0) / Ef))
    x1, x2, x3, x4, x5 = gw, gw + W, gw + W + D, gw + 2 * W + D, gw + 2 * W + 2 * D

    panels = [
        _rect("glue", "glue", 0.0, 0.0, x1, Hb),
        _rect("w0", "wall", x1, 0.0, x2, Hb),
        _poly("w1", "wall", [(x2, 0), (x3, 0), (x3, Hb), (x2 + a, Hb + Hr), (x2, Hb)]),
        _rect("w2", "wall", x3, 0.0, x4, Hb),
        _poly("w3", "wall", [(x4, 0), (x5, 0), (x5, Hb), (x4 + (D - a), Hb + Hr), (x4, Hb)]),
        _rect("slopeF", "slope", x1, Hb, x2, Hb + sF),
        _rect("finF", "fin", x1, Hb + sF, x2, Hb + sF + Ef),
        _rect("slopeB", "slope", x3, Hb, x4, Hb + sB),
        _rect("finB", "fin", x3, Hb + sB, x4, Hb + sB + Ef),
        _rect("bF", "flap", x1, -D / 2.0, x2, 0.0),
        _rect("bB", "flap", x3, -D / 2.0, x4, 0.0),
        _rect("bR", "flap", x2, -W / 2.0, x3, 0.0),
        _rect("bL", "flap", x4, -W / 2.0, x5, 0.0),
    ]
    edges = [
        _fold("e_glue", (x1, 0), (x1, Hb), "w0", "glue", (0.0, 1.0, 0.0), "MOUNTAIN"),
        _fold("e_w01", (x2, 0), (x2, Hb), "w0", "w1", (0.0, 1.0, 0.0)),
        _fold("e_w12", (x3, 0), (x3, Hb), "w1", "w2", (-1.0, 0.0, 0.0)),
        _fold("e_w23", (x4, 0), (x4, Hb), "w2", "w3", (0.0, -1.0, 0.0)),
        _fold("e_slF", (x1, Hb), (x2, Hb), "w0", "slopeF", (0.0, a / sF, Hr / sF)),
        _fold("e_finF", (x1, Hb + sF), (x2, Hb + sF), "slopeF", "finF",
              (0.0, math.sin(lean), math.cos(lean)), "MOUNTAIN"),
        _fold("e_slB", (x3, Hb), (x4, Hb), "w2", "slopeB",
              (0.0, -(D - a) / sB, Hr / sB)),
        _fold("e_finB", (x3, Hb + sB), (x4, Hb + sB), "slopeB", "finB",
              (0.0, -math.sin(lean), math.cos(lean)), "MOUNTAIN"),
        _fold("e_bF", (x1, 0), (x2, 0), "w0", "bF", (0.0, 1.0, 0.0), "MOUNTAIN"),
        _fold("e_bB", (x3, 0), (x4, 0), "w2", "bB", (0.0, -1.0, 0.0), "MOUNTAIN"),
        _fold("e_bR", (x2, 0), (x3, 0), "w1", "bR", (-1.0, 0.0, 0.0), "MOUNTAIN"),
        _fold("e_bL", (x4, 0), (x5, 0), "w3", "bL", (1.0, 0.0, 0.0), "MOUNTAIN"),
    ]
    notes = (f"gable_rect_base: 矩形基底屋顶包 (单件连体拓扑) — 4墙 (山墙三角在 w1/w3, "
             f"apex 随脊偏移) + 双坡矩形板 (前坡 run=a={a:g}, 后坡 run={D - a:g}, "
             f"坡面梯形不对称, sF={sF:.2f}/sB={sB:.2f}) + 过脊双鳍 (顶缘距 {gap:g}) "
             f"+ 4 底板到中线; W≠D 矩形化, ridge_off=0 即对称 gable_top 拓扑")
    return panels, edges, notes, _features("glue")


# ---------------------------------------------------------- ② rsc_display_panel
def _build_rsc_display(p):
    W, D = float(p["W"]), float(p["D"])
    Hf, H = float(p["Hf"]), float(p["H"])
    gw = float(p["glue_w"])
    Ls = D * math.sqrt(2.0)                      # 45° 展示板净深
    s2 = math.sqrt(2.0) / 2.0
    dm, dn = D / 2.0, W / 2.0                    # 顶翼: 大翼深 D/2 (背墙), 小翼 W/2 (侧墙)
    x1, x2, x3, x4, x5 = gw, gw + W, gw + W + D, gw + 2 * W + D, gw + 2 * W + 2 * D

    panels = [
        _rect("glue", "glue", 0.0, 0.0, x1, Hf),
        _rect("w0", "wall", x1, 0.0, x2, Hf),
        _poly("w1", "wall", [(x2, 0), (x3, 0), (x3, H), (x2, H), (x2, Hf)]),
        _rect("w2", "wall", x3, 0.0, x4, H),
        _rect("w3", "wall", x4, 0.0, x5, H),
        _rect("slant", "slope", x1, Hf, x2, Hf + Ls),
        _rect("t2", "flap", x3, H, x4, H + dm),
        _rect("t1", "flap", x2, H, x3, H + dn),
        _rect("t3", "flap", x4, H, x5, H + dn),
        _rect("b0", "flap", x1, -dm, x2, 0.0),
        _rect("b1", "flap", x2, -dn, x3, 0.0),
        _rect("b2", "flap", x3, -dm, x4, 0.0),
        _rect("b3", "flap", x4, -dn, x5, 0.0),
    ]
    edges = [
        _fold("e_glue", (x1, 0), (x1, Hf), "w0", "glue", (0.0, 1.0, 0.0), "MOUNTAIN"),
        _fold("e_w01", (x2, 0), (x2, Hf), "w0", "w1", (0.0, 1.0, 0.0)),
        _fold("e_w12", (x3, 0), (x3, H), "w1", "w2", (-1.0, 0.0, 0.0)),
        _fold("e_w23", (x4, 0), (x4, H), "w2", "w3", (0.0, -1.0, 0.0)),
        _fold("e_slant", (x1, Hf), (x2, Hf), "w0", "slant", (0.0, s2, s2), "MOUNTAIN"),
        _fold("e_t2", (x3, H), (x4, H), "w2", "t2", (0.0, -1.0, 0.0), "MOUNTAIN"),
        _fold("e_t1", (x2, H), (x3, H), "w1", "t1", (-1.0, 0.0, 0.0), "MOUNTAIN"),
        _fold("e_t3", (x4, H), (x5, H), "w3", "t3", (1.0, 0.0, 0.0), "MOUNTAIN"),
        _fold("e_b0", (x1, 0), (x2, 0), "w0", "b0", (0.0, 1.0, 0.0), "MOUNTAIN"),
        _fold("e_b1", (x2, 0), (x3, 0), "w1", "b1", (-1.0, 0.0, 0.0), "MOUNTAIN"),
        _fold("e_b2", (x3, 0), (x4, 0), "w2", "b2", (0.0, -1.0, 0.0), "MOUNTAIN"),
        _fold("e_b3", (x4, 0), (x5, 0), "w3", "b3", (1.0, 0.0, 0.0), "MOUNTAIN"),
    ]
    notes = (f"rsc_display_panel: 展示面板箱 (单件连体拓扑) — RSC 墙环 (前墙矮 {Hf:g}, "
             f"背/侧墙高 {H:g}) + 前墙顶缘 45° 展示板 (净深 {Ls:.2f}, 远缘精确抵背墙顶缘, "
             f"锁定 H=Hf+D) + 顶 3 翼 (大翼自背墙到中线, 小翼自侧墙) + 底 4 翼 "
             "(flap_ratio=0.5 到中线)")
    return panels, edges, notes, _features("glue")


# ---------------------------------------------------------- ③ tray_lid_overfit
def _build_tray_lid(p):
    W, D, H, gw = float(p["W"]), float(p["D"]), float(p["H"]), float(p["glue_w"])
    y0, y1, y2, y3 = D, D + H, D + H + D, D + H + D + H
    panels = [
        _rect("base", "wall", 0.0, 0.0, W, D),
        _rect("wF", "wall", 0.0, -H, W, 0.0),
        _rect("wR", "wall", W, 0.0, W + H, D),
        _rect("wB", "wall", 0.0, y0, W, y1),
        _rect("wL", "wall", -H, 0.0, 0.0, D),
        _poly("cFR", "flap", [(W, 0), (W, -H), (W + gw, -H)]),
        _poly("cRB", "flap", [(W + H, D), (W, D), (W, D + gw)]),
        _poly("cBL", "flap", [(0, D), (0, D + H), (-gw, D + H)]),
        _poly("cLF", "flap", [(-H, 0), (0, 0), (0, -gw)]),
        _rect("lid", "flap", 0.0, y1, W, y2),
        _rect("skirt", "flap", 0.0, y2, W, y3),
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
        _fold("e_lid", (0, y1), (W, y1), "wB", "lid", (0.0, -1.0, 0.0), "MOUNTAIN"),
        _fold("e_skirt", (0, y2), (W, y2), "lid", "skirt", (0.0, 0.0, -1.0), "MOUNTAIN"),
    ]
    notes = (f"tray_lid_overfit: 连体翻盖托盘 (拓扑声明: 连体单件 — 盖绕背墙顶缘铰链"
             f"前翻扣合, 不可分离, 非两件分离拓扑) — 星形盘 (底盘 {W:g}×{D:g} + 4墙 {H:g} "
             "+ 4 角片全高粘邻墙内面, tray_4corner 同款) + 一体盖 (深 D 覆口缘) "
             "+ 前裙 (深 H, 扣合后外贴前墙, 远缘与前墙底缘互抵)")
    return panels, edges, notes, _features("cFR", "cRB", "cBL", "cLF")


# ---------------------------------------------------------- ④ hexagonal_flip
def _build_hex_flip(p):
    side, H, gw = float(p["side"]), float(p["H"]), float(p["glue_w"])
    n = 6
    a = side / (2.0 * math.tan(math.pi / n))     # apothem = 对折盖深
    _, outward, tangent, _ = _poly_ring(n, side, side / 2.0, a)
    panels = [_rect("glue", "glue", 0.0, 0.0, gw, H)]
    for i in range(n):
        x0 = gw + i * side
        panels.append(_rect(f"w{i}", "wall", x0, 0.0, x0 + side, H))
        panels.append(_rect(f"f{i}", "flap", x0, H, x0 + side, H + a))
    edges = [_fold("e_glue", (gw, 0), (gw, H), "w0", "glue", (1.0, 0.0, 0.0), "MOUNTAIN")]
    for i in range(n - 1):
        x = gw + (i + 1) * side
        edges.append(_fold(f"e_w{i}", (x, 0), (x, H), f"w{i}", f"w{i + 1}",
                           (float(tangent[i + 1][0]), float(tangent[i + 1][1]), 0.0)))
    for i in range(n):
        x0 = gw + i * side
        edges.append(_fold(f"e_f{i}", (x0, H), (x0 + side, H), f"w{i}", f"f{i}",
                           (float(-outward[i][0]), float(-outward[i][1]), 0.0),
                           "MOUNTAIN"))
    notes = (f"hexagonal_flip: 六角翻盖盒 (单件连体拓扑) — 6 墙环形链 (边长 {side:g}, "
             f"高 {H:g}) + 3 组对折盖 (对位墙 w_k/w_{{k+3}} 各一片, 深 = apothem "
             f"{a:.2f}, 远缘中点全落中心轴 z=H) + 全重叠粘缝 (宽 {gw:g} 贴 w0)")
    return panels, edges, notes, _features("glue")


# ---------------------------------------------------------- ⑤ tube_double_seam
_TN = 8                                        # 八边形近似圆管


def _build_tube_seam(p):
    side, h, g = float(p["side"]), float(p["h"]), float(p["g"])
    n = _TN
    a = side / (2.0 * math.tan(math.pi / n))   # apothem = 内折盘深
    _, outward, tangent, _ = _poly_ring(n, side, side / 2.0, a)
    panels = [_rect("glue", "glue", 0.0, 0.0, side, h)]   # 全重叠粘缝: 宽 = 墙宽
    for i in range(n):
        x0 = side + i * side
        panels.append(_rect(f"w{i}", "wall", x0, 0.0, x0 + side, h))
        db = (a - g) if i == n - 1 else a          # 底端缝位: 末片 w7 短盘
        dt = (a - g) if i == (n // 2 - 1) else a   # 顶端缝位: 对位墙 w3 短盘
        panels.append(_rect(f"b{i}", "flap", x0, -db, x0 + side, 0.0))
        panels.append(_rect(f"t{i}", "flap", x0, h, x0 + side, h + dt))
    edges = [_fold("e_glue", (side, 0), (side, h), "w0", "glue",
                   (1.0, 0.0, 0.0), "MOUNTAIN")]
    for i in range(n - 1):
        x = side + (i + 1) * side
        edges.append(_fold(f"e_w{i}", (x, 0), (x, h), f"w{i}", f"w{i + 1}",
                           (float(tangent[i + 1][0]), float(tangent[i + 1][1]), 0.0)))
    for i in range(n):
        x0 = side + i * side
        oi = outward[i]
        edges.append(_fold(f"e_b{i}", (x0, 0), (x0 + side, 0), f"w{i}", f"b{i}",
                           (float(-oi[0]), float(-oi[1]), 0.0), "MOUNTAIN"))
        edges.append(_fold(f"e_t{i}", (x0, h), (x0 + side, h), f"w{i}", f"t{i}",
                           (float(-oi[0]), float(-oi[1]), 0.0), "MOUNTAIN"))
    notes = (f"tube_double_seam: 双缝管 (单件连体拓扑) — {_TN} 边形直管环形墙链 "
             f"(边长 {side:g}, 长 {h:g}) + 全重叠粘缝 (宽=墙宽, 贴 w0) + 两端各 {_TN} 片"
             f"内折盘 (深 = apothem {a:.2f}, 远缘中点落轴); 反向缝位: 底端短盘 "
             f"(深 a-{g:g}) 在 w7, 顶端短盘在对位墙 w3 (相隔 180°, 封盘搭接应力错位)")
    return panels, edges, notes, _features("glue")


# ---------------------------------------------------------- ⑥ mailer_diecut
def _build_mailer(p):
    S, C, h, t = float(p["S"]), float(p["C"]), float(p["h"]), float(p["t"])
    bw, tw, wl = float(p["bw"]), float(p["tw"]), float(p["wl"])
    panels = [
        _poly("spine", "wall", [(0, 0), (S, 0), (S, h), (0, h), (0, bw)]),
        # 左盖窗框链: 底条(主链) → 左条 → 顶条(带窗角分点) → 右条 绕窗共面平折,
        # 网并集 = 带孔单环 (窗洞 x∈[-C+wl,-wl], y∈[bw,h-tw])
        _poly("clb", "wall", [(-C, 0), (0, 0), (0, bw), (-C + wl, bw), (-C, bw)]),
        _rect("cll", "wall", -C, bw, -C + wl, h - tw),
        _poly("clt", "wall", [(0, h), (-C, h), (-C, h - tw), (-C + wl, h - tw),
                              (-wl, h - tw), (0, h - tw)]),
        _rect("clr", "wall", -wl, bw, 0.0, h - tw),
        _rect("coverR", "wall", S, 0.0, S + C, h),
        _rect("tuck", "flap", S + C, 0.0, S + C + t, h),
    ]
    edges = [
        _fold("e_cl", (0, 0), (0, bw), "spine", "clb", (0.0, 1.0, 0.0)),
        _fold("e_wl", (-C, bw), (-C + wl, bw), "clb", "cll", (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_wt", (-C, h - tw), (-C + wl, h - tw), "cll", "clt",
              (0.0, 0.0, 1.0), "MOUNTAIN"),
        _fold("e_clr", (-wl, h - tw), (0, h - tw), "clt", "clr",
              (0.0, 0.0, -1.0), "MOUNTAIN"),
        _fold("e_cr", (S, 0), (S, h), "spine", "coverR", (0.0, 1.0, 0.0)),
        _fold("e_tk", (S + C, 0), (S + C, h), "coverR", "tuck",
              (0.0, -1.0, 0.0), "MOUNTAIN"),
    ]
    notes = (f"mailer_diecut: 镂空邮寄盒 (单件连体拓扑, 书封式) — 书脊 {S:g} + 左盖 "
             f"窗框 4 条绕窗共面平折 (网并集=带孔单环, 窗洞 "
             f"{C - 2 * wl:g}×{h - bw - tw:g}) + 右盖 {C:g} (90° 立起, 间距=书脊宽) "
             f"+ 插舌 {t:g} 180° 反贴右盖内面 (reach y=C-t)")
    return panels, edges, notes, _features("tuck")


# ---------------------------------------------------------- ⑦ divided_tray_3comp
def _build_divided3(p):
    W, D, H, xt = float(p["W"]), float(p["D"]), float(p["H"]), float(p["xt"])
    panels = [
        _poly("floor", "wall", [(W, D), (0, D), (0, 0), (xt, 0), (W, 0), (xt, D)]),
        _rect("wF", "wall", 0.0, -H, W, 0.0),
        _rect("wB", "wall", 0.0, D, W, D + H),
        _rect("wL", "wall", -H, 0.0, 0.0, D),
        _rect("wR", "wall", W, 0.0, W + H, D),
        _rect("dvl", "wall", 0.0, D / 2.0, W, D / 2.0 + H),   # 纵隔板 (全宽)
        _rect("dvt", "wall", xt, 0.0, xt + H, D),             # 横隔板 (全深)
    ]
    edges = [
        _fold("e_wf", (0, 0), (W, 0), "floor", "wF", (0.0, 0.0, 1.0)),
        _fold("e_wb", (0, D), (W, D), "floor", "wB", (0.0, 0.0, 1.0)),
        _fold("e_wl", (0, 0), (0, D), "floor", "wL", (0.0, 0.0, 1.0)),
        _fold("e_wr", (W, 0), (W, D), "floor", "wR", (0.0, 0.0, 1.0)),
        _fold("e_dvl", (0, D / 2.0), (W, D / 2.0), "floor", "dvl", (0.0, 0.0, 1.0)),
        _fold("e_dvt", (xt, 0), (xt, D), "floor", "dvt", (0.0, 0.0, 1.0)),
    ]
    notes = (f"divided_tray_3comp: 三分格托盘 (单件连体拓扑) — 共享底盘 {W:g}×{D:g} "
             f"+ 4 围墙 {H:g} + 隔板十字 (纵隔板全宽 y=D/2 + 横隔板全深 x={xt:g}, "
             "正交 T 字相贯) — 三区独立围合: 左上/左下/右区 "
             "(egg_tray 分隔模式: 隔板自底盘铰链立起)")
    return panels, edges, notes, _features()


# ------------------------------------------------------------ 契约
_CLASS_PARAMS = {
    "gable_rect_base": {"kind": 0, "W": 60.0, "D": 45.0, "Hb": 90.0, "Hr": 15.0,
                        "ridge_off": 6.0, "Ef": 12.0, "fin_gap_mm": 3.0,
                        "glue_w": 12.0},
    "rsc_display_panel": {"kind": 1, "W": 120.0, "D": 60.0, "Hf": 40.0, "H": 100.0,
                          "flap_ratio": 0.5, "glue_w": 12.0},
    "tray_lid_overfit": {"kind": 2, "W": 90.0, "D": 60.0, "H": 25.0, "glue_w": 12.0},
    "hexagonal_flip": {"kind": 3, "side": 30.0, "H": 80.0, "glue_w": 15.0},
    "tube_double_seam": {"kind": 4, "side": 25.0, "h": 120.0, "g": 6.0},
    "mailer_diecut": {"kind": 5, "S": 40.0, "C": 120.0, "h": 160.0, "t": 30.0,
                      "bw": 30.0, "tw": 30.0, "wl": 30.0},
    "divided_tray_3comp": {"kind": 6, "W": 180.0, "D": 90.0, "H": 35.0, "xt": 60.0},
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
    p = params or {}
    kind = int(p.get("kind", 0))
    if kind == 0:
        _pos(p, "W", "D", "Hb", "Hr", "Ef", "fin_gap_mm", "glue_w")
        ro = float(p.get("ridge_off", 0.0))
        if not (0.0 <= ro < float(p["D"]) / 2.0):
            raise ValueError(f"脊偏移 ridge_off={ro} 须 [0, D/2)")
        if float(p["fin_gap_mm"]) >= 2.0 * float(p["Ef"]):
            raise ValueError("鳍顶缘距 fin_gap_mm 须 < 2*Ef")
        if float(p["glue_w"]) >= min(float(p["W"]), float(p["D"])):
            raise ValueError("粘口 glue_w 须窄于最短墙")
    elif kind == 1:
        _pos(p, "W", "D", "Hf", "H", "flap_ratio", "glue_w")
        if abs(float(p["H"]) - float(p["Hf"]) - float(p["D"])) > 1e-6:
            raise ValueError("45° 展示板远缘抵背墙顶缘须 H = Hf + D (锁定条件)")
        if abs(float(p["flap_ratio"]) - 0.5) > 1e-9:
            raise ValueError("展示箱底大翼须到中线: flap_ratio = 0.5")
        if float(p["glue_w"]) >= min(float(p["W"]), float(p["D"])):
            raise ValueError("粘口 glue_w 须窄于最短墙")
    elif kind == 2:
        _pos(p, "W", "D", "H", "glue_w")
        if float(p["glue_w"]) >= min(float(p["W"]), float(p["D"])) / 2.0:
            raise ValueError("角片搭接宽 glue_w 须窄于半最短墙")
    elif kind == 3:
        _pos(p, "side", "H", "glue_w")
        if float(p["glue_w"]) > float(p["side"]):
            raise ValueError("粘缝宽 glue_w 须不超过墙宽 side")
    elif kind == 4:
        _pos(p, "side", "h", "g")
        a = float(p["side"]) / (2.0 * math.tan(math.pi / _TN))
        if not (0.0 < float(p["g"]) < a / 2.0):
            raise ValueError(f"缝位缺口 g 须 (0, apothem/2={a / 2:.2f})")
    elif kind == 5:
        _pos(p, "S", "C", "h", "t", "bw", "tw", "wl")
        if 2.0 * float(p["wl"]) >= float(p["C"]):
            raise ValueError("窗框侧条 2*wl 须窄于盖宽 C")
        if float(p["bw"]) + float(p["tw"]) >= float(p["h"]):
            raise ValueError("窗框 bw+tw 须小于盖高 h (窗洞 > 0)")
        if float(p["t"]) >= float(p["C"]):
            raise ValueError("插舌深 t 须小于盖宽 C")
    else:
        _pos(p, "W", "D", "H", "xt")
        if not (0.0 < float(p["xt"]) < float(p["W"])):
            raise ValueError("横隔位 xt 须 (0, W)")
        if float(p["H"]) >= float(p["D"]) / 2.0:
            raise ValueError("格深 H 须小于 D/2 (纵隔板网面不越背墙)")


_BUILDERS = (_build_gable_rect, _build_rsc_display, _build_tray_lid,
             _build_hex_flip, _build_tube_seam, _build_mailer, _build_divided3)
_ROOTS = (("w0", _R_CHAIN), ("w0", _R_CHAIN), ("base", _R_STAR), ("w0", _R_CHAIN),
          ("w0", _R_CHAIN), ("spine", _R_CHAIN), ("floor", _R_STAR))


def build_ir(params: dict | None = None) -> dict:
    p = {**DEFAULTS, **(params or {})}
    kind = int(p.get("kind", 0))
    if not 0 <= kind < len(_BUILDERS):
        raise ValueError(f"非法 kind={kind!r} (须 0..{len(_BUILDERS) - 1})")
    cls_id = _CLS[kind]
    validate_params(p)
    panels, edges, notes, feats = _BUILDERS[kind](p)
    root, R = _ROOTS[kind]
    off_x = {"gable_rect_base": -float(p["glue_w"]), "rsc_display_panel": -float(p["glue_w"]),
             "tray_lid_overfit": 0.0, "hexagonal_flip": -float(p["glue_w"]),
             "tube_double_seam": -float(p["side"]), "mailer_diecut": 0.0,
             "divided_tray_3comp": 0.0}[cls_id]
    return {
        "meta": {"ir_version": "0.1", "units": "mm",
                 "generator": "photo_dieline.parametric.special_shapes 0.1",
                 "notes": notes, "root_panel": root,
                 "root_frame": {"R": R, "off": [off_x, 0.0, 0.0]}},
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
                "H": float(p["Hb"]) + float(p["Hr"])}
    if kind == 3:
        side, H = float(p["side"]), float(p["H"])
        return {"W": 2.0 * side, "D": math.sqrt(3.0) * side, "H": H}
    if kind == 4:
        side = float(p["side"])
        a = side / (2.0 * math.tan(math.pi / _TN))
        vs, _, _, _ = _poly_ring(_TN, side, side / 2.0, a)
        xs = [v[0] for v in vs]
        ys = [v[1] for v in vs]
        return {"W": float(max(xs) - min(xs)), "D": float(max(ys) - min(ys)),
                "H": float(p["h"])}
    if kind == 5:
        return {"W": float(p["S"]), "D": float(p["C"]), "H": float(p["h"])}
    return {"W": float(p["W"]), "D": float(p["D"]), "H": float(p["H"])}


def solid_roles():
    return ("wall", "slope")


def allowed_overlap():
    """G06 允许叠层 (真实工艺契约, 全家族并集):
    粘口贴末墙/首墙内面 (全重叠), 过脊双鳍脊线交汇, 45° 展示板缘触侧/背墙与顶翼,
    翻盖托盘前裙外贴前墙 + 角片贴邻墙内面, 插舌反贴右盖内面."""
    return {
        frozenset({"glue", "w3"}),           # ①② 粘口贴末墙内面
        frozenset({"glue", "w0"}),           # ④⑤ 全重叠粘缝贴首墙
        frozenset({"finB", "finF"}),         # ① 过脊双鳍脊线交汇
        frozenset({"slant", "w1"}), frozenset({"slant", "w2"}),
        frozenset({"slant", "w3"}),          # ② 展示板远缘抵背墙/侧缘抵侧墙
        frozenset({"slant", "t1"}), frozenset({"slant", "t2"}),
        frozenset({"slant", "t3"}),          # ② 展示板与顶翼同平面层区
        frozenset({"skirt", "wF"}),          # ③ 前裙外贴前墙 (扣合层压)
        frozenset({"cFR", "wR"}), frozenset({"cRB", "wB"}),
        frozenset({"cBL", "wL"}), frozenset({"cLF", "wF"}),  # ③ 角片贴邻墙内面
        frozenset({"tuck", "coverR"}),       # ⑥ 插舌 180° 反贴右盖内面
    }


# ------------------------------------------------------------ closure (逐类)
def _c_gable(ir, world):
    """① 山墙 apex 四重合 (坡↔三角跨链) + 环缝 + 底板中心相抵 + 鳍距/鳍顶 + 粘缝."""
    Hb, Hr = float(ir.param("Hb")), float(ir.param("Hr"))
    Ef, gap = float(ir.param("Ef")), float(ir.param("fin_gap_mm"))
    lean = math.asin(min(1.0, (gap / 2.0) / Ef))
    res: dict[str, float] = {}
    res["apex.L"] = max(_d(world["slopeF"][3], world["w3"][3]),
                        _d(world["slopeB"][2], world["w3"][3]))
    res["apex.R"] = max(_d(world["slopeF"][2], world["w1"][3]),
                        _d(world["slopeB"][3], world["w1"][3]))
    res["seam.LF.bot"] = _d(world["w3"][1], world["w0"][0])
    res["seam.LF.top"] = _d(world["w3"][2], world["w0"][3])
    res["b.center"] = _d(_fm(world, "bF", 0, 1), _fm(world, "bB", 0, 1))
    res["b.center2"] = _d(_fm(world, "bR", 0, 1), _fm(world, "bL", 0, 1))
    res["b.z0"] = max(abs(float(_fm(world, "bF", 0, 1)[2])),
                      abs(float(_fm(world, "bR", 0, 1)[2])))
    fF, fB = _fm(world, "finF", 2, 3), _fm(world, "finB", 2, 3)
    res["fin.gap"] = abs(float(np.linalg.norm(fF - fB)) - gap)
    z_fin = Hb + Hr + Ef * math.cos(lean)
    res["fin.z"] = max(abs(float(fF[2]) - z_fin), abs(float(fB[2]) - z_fin))
    g = np.asarray(world["glue"], float)
    res["glue.plane_x0"] = abs(float(np.mean(g[:, 0])))
    res["glue.seat_y"] = abs(float(np.mean(g[:, 1])) - float(ir.param("glue_w")) / 2.0)
    return res


def _c_rscdisp(ir, world):
    """② 展示板远缘抵背墙顶缘 (跨链) + 环缝 + 底/顶翼中线相抵 + 粘缝."""
    res: dict[str, float] = {}
    res["seam.LF"] = _d(world["w3"][1], world["w0"][0])
    res["slant.meet_back"] = max(_d(world["slant"][2], world["w2"][3]),
                                 _d(world["slant"][3], world["w2"][2]))
    res["slant.seat_w1"] = _d(world["slant"][2], world["w1"][2])
    g = np.asarray(world["glue"], float)
    res["glue.plane_x0"] = abs(float(np.mean(g[:, 0])))
    res["glue.seat_y"] = abs(float(np.mean(g[:, 1])) - float(ir.param("glue_w")) / 2.0)
    res["b.major.meet"] = _d(_fm(world, "b0", 0, 1), _fm(world, "b2", 0, 1))
    res["b.minor.meet"] = _d(_fm(world, "b1", 0, 1), _fm(world, "b3", 0, 1))
    res["b.z0"] = max(abs(float(_fm(world, "b0", 0, 1)[2])),
                      abs(float(_fm(world, "b2", 0, 1)[2])))
    res["t.meet_FB"] = _d(_fm(world, "t2", 2, 3), _fm(world, "t1", 2, 3))
    res["t.meet_LR"] = _d(_fm(world, "t1", 2, 3), _fm(world, "t3", 2, 3))
    res["t.zH"] = max(abs(float(_fm(world, "t2", 2, 3)[2]) - float(ir.param("H"))),
                      abs(float(_fm(world, "t1", 2, 3)[2]) - float(ir.param("H"))))
    return res


def _c_traylid(ir, world):
    """③ 四角缝 + 角片贴合 + 一体盖远缘抵前墙顶缘 + 前裙远缘抵前墙底缘."""
    res: dict[str, float] = {}
    f, r, b, l = world["wF"], world["wR"], world["wB"], world["wL"]
    res["corner.fr"] = float(max(_d(f[1], r[1]), _d(f[2], r[0])))
    res["corner.rb"] = float(max(_d(r[2], b[2]), _d(r[3], b[1])))
    res["corner.bl"] = float(max(_d(b[3], l[3]), _d(b[0], l[2])))
    res["corner.lf"] = float(max(_d(l[0], f[0]), _d(l[1], f[3])))
    for cid, ax, tgt in (("cFR", 0, float(ir.param("W"))), ("cRB", 1, float(ir.param("D"))),
                         ("cBL", 0, 0.0), ("cLF", 1, 0.0)):
        res[f"{cid}.on_host"] = float(np.max(np.abs(world[cid][:, ax] - tgt)))
    res["lid.meet"] = max(_d(world["lid"][2], world["wF"][1]),
                          _d(world["lid"][3], world["wF"][0]))
    res["skirt.seat"] = max(_d(world["skirt"][2], world["wF"][2]),
                            _d(world["skirt"][3], world["wF"][3]))
    return res


def _c_hexflip(ir, world):
    """④ 六片对折盖远缘中点全落中心轴 (z=H) + 环缝 + 粘缝."""
    side, H = float(ir.param("side")), float(ir.param("H"))
    a = side / (2.0 * math.tan(math.pi / 6))
    res: dict[str, float] = {}
    for i in range(6):
        res[f"f{i}.axis"] = _d(_fm(world, f"f{i}", 2, 3), (side / 2.0, a, H))
    res["seam.w5_w0.bot"] = _d(world["w5"][1], world["w0"][0])
    res["seam.w5_w0.top"] = _d(world["w5"][2], world["w0"][3])
    g = np.asarray(world["glue"], float)
    res["glue.plane_y0"] = abs(float(np.mean(g[:, 1])))
    res["glue.seat_x"] = abs(float(np.mean(g[:, 0])) - float(ir.param("glue_w")) / 2.0)
    return res


def _c_tube(ir, world):
    """⑤ 两端内折盘远缘中点落轴 (短盘落 C+g·outward, 反向缝位) + 环缝 + 粘缝."""
    side, h, g = float(ir.param("side")), float(ir.param("h")), float(ir.param("g"))
    n = _TN
    a = side / (2.0 * math.tan(math.pi / n))
    _, outward, _, _ = _poly_ring(n, side, side / 2.0, a)
    res: dict[str, float] = {}
    for i in range(n):
        cx, cy = side / 2.0, a
        eb = (a - g) if i == n - 1 else a          # 底端缝位: w7 短盘
        et = (a - g) if i == (n // 2 - 1) else a   # 顶端缝位: 对位墙 w3 短盘
        pb = (cx + (a - eb) * float(outward[i][0]), cy + (a - eb) * float(outward[i][1]), 0.0)
        pt = (cx + (a - et) * float(outward[i][0]), cy + (a - et) * float(outward[i][1]), h)
        res[f"b{i}.axis"] = _d(_fm(world, f"b{i}", 0, 1), pb)   # b 远缘 = idx0/1
        res[f"t{i}.axis"] = _d(_fm(world, f"t{i}", 2, 3), pt)
    wn = world[f"w{n - 1}"]
    res["seam.w7_w0.bot"] = _d(wn[1], world["w0"][0])
    res["seam.w7_w0.top"] = _d(wn[2], world["w0"][3])
    gl = np.asarray(world["glue"], float)
    res["glue.plane_y0"] = abs(float(np.mean(gl[:, 1])))
    res["glue.far_w0"] = max(abs(float(gl[0][0]) - side), abs(float(gl[3][0]) - side))
    return res


def _c_mailer(ir, world):
    """⑥ 左盖窗框全片共面前平面 (x=0) + 窗洞角位 + 右盖 90° + 插舌反贴."""
    C, h = float(ir.param("C")), float(ir.param("h"))
    bw, tw, wl = float(ir.param("bw")), float(ir.param("tw")), float(ir.param("wl"))
    res: dict[str, float] = {}
    for pid in ("clb", "cll", "clt", "clr"):
        res[f"cvL.{pid}.plane"] = abs(float(np.mean(np.asarray(world[pid], float)[:, 0])))
    res["coverR.perp_xS"] = abs(float(np.mean(np.asarray(world["coverR"], float)[:, 0]))
                                - float(ir.param("S")))
    res["hole.corner_ll"] = _d(world["cll"][1], (0.0, C - wl, bw))
    res["hole.corner_tr"] = _d(world["clr"][3], (0.0, wl, h - tw))
    res["cvL.reach"] = _d(world["clb"][0], (0.0, C, 0.0))
    tv = np.asarray(world["tuck"], float)
    res["tuck.flush_xS"] = float(np.max(np.abs(tv[:, 0] - float(ir.param("S")))))
    res["tuck.reach"] = abs(float(_fm(world, "tuck", 1, 2)[1]) - (C - float(ir.param("t"))))
    return res


def _c_divided(ir, world):
    """⑦ 四角缝 + 隔板十字平面/顶高 (横隔 x=xt 竖直面, 纵隔 y=D/2 竖直面)."""
    xt, H = float(ir.param("xt")), float(ir.param("H"))
    res: dict[str, float] = {}
    f, r, b, l = world["wF"], world["wR"], world["wB"], world["wL"]
    res["corner.fr"] = float(max(_d(f[1], r[1]), _d(f[2], r[0])))
    res["corner.rb"] = float(max(_d(r[2], b[2]), _d(r[3], b[1])))
    res["corner.bl"] = float(max(_d(b[3], l[3]), _d(b[0], l[2])))
    res["corner.fl"] = float(max(_d(l[0], f[0]), _d(l[1], f[3])))
    dv = np.asarray(world["dvt"], float)
    res["dvt.plane_x"] = abs(float(np.mean(dv[:, 0])) - xt)
    res["dvt.top_z"] = abs(float(np.mean(dv[1:3], axis=0)[2]) - H)
    dl = np.asarray(world["dvl"], float)
    res["dvl.plane_y"] = abs(float(np.mean(dl[:, 1])) - float(ir.param("D")) / 2.0)
    res["dvl.top_z"] = abs(float(np.mean(dl[2:4], axis=0)[2]) - H)
    return res


_CLOSURES = (_c_gable, _c_rscdisp, _c_traylid, _c_hexflip, _c_tube, _c_mailer,
             _c_divided)


def closure_checks(ir, world) -> dict:
    return _CLOSURES[_CLS.index(ir.package["template"]["id"])](ir, world)


# ------------------------------------------------------------ 负探针
def _rodrigues(v, axis, ang):
    a = _unit(axis)
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
    kind = _CLS.index(ir.package["template"]["id"])
    return {0: [("e_slF", (1, 0, 0)), ("e_bF", (1, 0, 0))],
            1: [("e_slant", (1, 0, 0)), ("e_t2", (1, 0, 0))],
            2: [("e_lid", (1, 0, 0)), ("e_skirt", (1, 0, 0))],
            3: [("e_f0", (1, 0, 0)), ("e_w2", (0, 0, 1))],
            4: [("e_b0", (1, 0, 0)), ("e_w4", (0, 0, 1))],
            5: [("e_cl", (0, 0, 1)), ("e_tk", (0, 0, 1))],
            6: [("e_dvt", (0, 1, 0)), ("e_wf", (1, 0, 0))]}[kind]


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
