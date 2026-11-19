"""closure_variants: 单式盖型七类 — 4 矩形墙链 + glue + 底全叠封, 盖型互异即独立拓扑.

几何约定: 同 box_essentials — 链式网根墙 w0 占 y=0 平面, net(x,y)→world(x,0,y),
root_frame off=[-gw,0,0]; 墙环 w0(front,y=0)→w1(right,x=W)→w2(back,y=D)→w3(left,x=0),
w3 自由缘回 w0 左缘; 底 4 折翼全到中线; 全部单件拓扑 (无 web/第二件)。

七类盖型 (世界折叠落位):
  ① clv_tuck_insert  插舌入槽: 主盖深 D 自 w2, 远缘中央插舌 (宽=slot_w) 穿前墙
     w0 顶缘槽口凹多边形 (slot_w × slot_d), 舌尖越过槽底 tuck_d - slot_d 入盒内。
  ② clv_double_tuck  双端插舌: w2/w0 各出全深 D 插舌盖, 顶面共面叠合, 两舌分别
     折入对面墙 (w0/w2) 内面 — 双向锁合。
  ③ clv_snap_lock    卡扣锁盖: w0 顶缘 T 形凹口 (口部宽槽 pk_w×pk_d + 喉部窄槽
     slot_w×slot_d); 盖舌 T 形 (柄宽=slot_w, 端部凸卡点宽=pk_w 深=bd), 卡点落座
     喉口肩线 z=H-pk_d。板厚未建模, 保持以 T 槽腔座位证据表达 (座位线+双侧对位)。
  ④ clv_hinged_flap  铰链翻盖: w2 顶缘 → 活页窄条 (hs, 直立) → 主盖, 双折链,
     盖面抬升到 z=H+hs, 远缘插舌入前墙。
  ⑤ clv_partial_lid  半盖: w2 出盖深 D/2 内折, 远缘落 y=D/2 中线, 不封顶无舌。
  ⑥ clv_double_cover 双层盖: w2 出主盖全深 D, 远缘续链回折内衬盖 (深 lw_d,
     两侧缩进 lin_in), 内衬反折 +y 覆盖主盖前段 z=H。
  ⑦ clv_glue_seal    胶封盖: w2 出盖全深 D, 远缘全宽胶条 (gs_d) 下折贴前墙封口,
     胶条下续撕拉手 (ts_w×ts_d) 越出胶条下缘供撕开。

closure 判据全部为折叠后世界坐标跨链真实闭合证据 (远缘中点落位/槽口对位/座位线
重合/跨链展向配准); 负探针 probe() 绕真实世界铰链轴 Rodrigues 扰动 tdir。
"""
from __future__ import annotations

import copy
import math

import numpy as np

from . import base as _base

DEFAULTS = {"W": 110.0, "D": 70.0, "H": 60.0, "glue_w": 12.0, "board_t": 0.45,
            "tuck_d": 12.0, "ins": 12.0,
            "slot_w": 24.0, "slot_d": 6.0, "pk_w": 40.0, "pk_d": 10.0, "bd": 5.0,
            "hs": 8.0, "lw_d": 30.0, "lin_in": 10.0,
            "gs_d": 12.0, "ts_w": 30.0, "ts_d": 8.0,
            "kind": 0}
PARAM_ORDER = ["kind", "W", "D", "H", "glue_w", "board_t", "tuck_d", "ins",
               "slot_w", "slot_d", "pk_w", "pk_d", "bd",
               "hs", "lw_d", "lin_in", "gs_d", "ts_w", "ts_d"]

_CLS = ("clv_tuck_insert", "clv_double_tuck", "clv_snap_lock",
        "clv_hinged_flap", "clv_partial_lid", "clv_double_cover", "clv_glue_seal")
_KIND = {c: i for i, c in enumerate(_CLS)}

for _cid in _CLS:
    _base.register(_cid, "closure_variants")

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
def _chain(p, W, D, H):
    """[glue][w0..w3] 墙链: 返回 (panels, edges, xs)."""
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


def _set_wall(panels, pid, poly):
    """替换链中某墙的多边形 (凹口墙: 槽口/T 形凹口只裁顶缘, 底/侧棱完整)."""
    for i, pl in enumerate(panels):
        if pl["id"] == pid:
            panels[i] = poly
            return


def _bottom_full(p, xs):
    """底全叠封 4 折翼: 大翼(墙0/墙2)深 D/2, 小翼(墙1/墙3)深 W/2, 全到中线."""
    x1, x2, x3, x4, x5 = xs
    W, D = x2 - x1, x3 - x2
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


# ---------------------------------------------------------- ① clv_tuck_insert
def _build_tuck_insert(p):
    W, D, H = float(p["W"]), float(p["D"]), float(p["H"])
    sw, sd, td = float(p["slot_w"]), float(p["slot_d"]), float(p["tuck_d"])
    panels, edges, xs = _chain(p, W, D, H)
    x1, x2, x3, x4 = xs[0], xs[1], xs[2], xs[3]
    bp, be = _bottom_full(p, xs)
    xcw = x1 + W / 2.0  # 前墙 w0 净坐标中心 (槽口)
    xcl = x3 + W / 2.0  # w2 净坐标中心 (主盖远缘分点/插舌)
    sw2 = sw / 2.0
    # 前墙 w0 顶缘槽口凹多边形 (slot_w × slot_d, 居中)
    _set_wall(panels, "w0", _poly("w0", "wall",
             [(x1, 0), (x2, 0), (x2, H), (xcw + sw2, H), (xcw + sw2, H - sd),
              (xcw - sw2, H - sd), (xcw - sw2, H), (x1, H)]))
    # 主盖深 D 自背墙 w2, 远缘带分点 (插舌铰链)
    lid = _poly("t2", "flap", [(x3, H), (x4, H), (x4, H + D),
                               (xcl + sw2, H + D), (xcl - sw2, H + D), (x3, H + D)])
    tongue = _rect("tongue", "flap", xcl - sw2, H + D, xcl + sw2, H + D + td)
    edges += [_fold("e_t2", (x3, H), (x4, H), "w2", "t2", (0.0, -1.0, 0.0), "MOUNTAIN"),
              _fold("e_tongue", (xcl - sw2, H + D), (xcl + sw2, H + D),
                    "t2", "tongue", (0.0, 0.0, -1.0), "MOUNTAIN")]
    notes = (f"clv_tuck_insert: 插舌入槽式 — 主盖深 D 自背墙 w2, 远缘中央插舌 "
             f"(宽 {sw:g} = 槽宽, 深 {td:g}) 穿前墙 w0 顶缘槽口凹多边形 "
             f"({sw:g}×{sd:g}), 舌尖越过槽底 {td - sd:g} 入盒内; "
             "4 墙链 + glue + 底全叠封")
    return panels + bp + [lid, tongue], edges + be, notes, _features("glue")


# ---------------------------------------------------------- ② clv_double_tuck
def _build_double_tuck(p):
    W, D, H = float(p["W"]), float(p["D"]), float(p["H"])
    ins, td = float(p["ins"]), float(p["tuck_d"])
    panels, edges, xs = _chain(p, W, D, H)
    x1, x2, x3, x4 = xs[0], xs[1], xs[2], xs[3]
    bp, be = _bottom_full(p, xs)
    # 背盖: w2 出全深 D, 舌折入前墙 y=0
    lt2 = _poly("lt2", "flap", [(x3, H), (x4, H), (x4, H + D),
                                (x4 - ins, H + D), (x3 + ins, H + D), (x3, H)])
    ta = _rect("ta", "flap", x3 + ins, H + D, x4 - ins, H + D + td)
    # 前盖: w0 出全深 D, 舌折入背墙 y=D (与背盖顶面共面叠合)
    lt0 = _poly("lt0", "flap", [(x1, H), (x2, H), (x2 - ins, H + D),
                                (x1 + ins, H + D), (x1, H)])
    tb = _rect("tb", "flap", x1 + ins, H + D, x2 - ins, H + D + td)
    edges += [_fold("e_lt2", (x3, H), (x4, H), "w2", "lt2", (0.0, -1.0, 0.0), "MOUNTAIN"),
              _fold("e_ta", (x3 + ins, H + D), (x4 - ins, H + D),
                    "lt2", "ta", (0.0, 0.0, -1.0), "MOUNTAIN"),
              _fold("e_lt0", (x1, H), (x2, H), "w0", "lt0", (0.0, 1.0, 0.0), "MOUNTAIN"),
              _fold("e_tb", (x1 + ins, H + D), (x2 - ins, H + D),
                    "lt0", "tb", (0.0, 0.0, -1.0), "MOUNTAIN")]
    notes = (f"clv_double_tuck: 双端插舌 — 前后墙各出全深 D 插舌盖 (舌宽 W-2*ins="
             f"{W - 2 * ins:g}, 深 {td:g}), 顶面共面叠合, 两舌分别折入对面墙内面 "
             "(ta→w0, tb→w2) 双向锁合; 4 墙链 + glue + 底全叠封")
    return panels + bp + [lt2, ta, lt0, tb], edges + be, notes, _features("glue")


# ---------------------------------------------------------- ③ clv_snap_lock
def _build_snap_lock(p):
    W, D, H = float(p["W"]), float(p["D"]), float(p["H"])
    sw, sd = float(p["slot_w"]), float(p["slot_d"])
    pw, pd, bd = float(p["pk_w"]), float(p["pk_d"]), float(p["bd"])
    panels, edges, xs = _chain(p, W, D, H)
    x1, x2, x3, x4 = xs[0], xs[1], xs[2], xs[3]
    bp, be = _bottom_full(p, xs)
    xcw, xcl = x1 + W / 2.0, x3 + W / 2.0
    sw2, pw2 = sw / 2.0, pw / 2.0
    # 前墙 w0 顶缘 T 形凹口: 口部宽槽 (pk_w × pk_d) + 喉部窄槽 (slot_w × slot_d)
    _set_wall(panels, "w0", _poly("w0", "wall",
             [(x1, 0), (x2, 0), (x2, H),
              (xcw + pw2, H), (xcw + pw2, H - pd),
              (xcw + sw2, H - pd), (xcw + sw2, H - pd - sd),
              (xcw - sw2, H - pd - sd), (xcw - sw2, H - pd),
              (xcw - pw2, H - pd), (xcw - pw2, H), (x1, H)]))
    # 主盖深 D 自背墙, 远缘分点 (T 舌柄铰链)
    lid = _poly("t2", "flap", [(x3, H), (x4, H), (x4, H + D),
                               (xcl + sw2, H + D), (xcl - sw2, H + D), (x3, H + D)])
    # T 形盖舌: 柄宽 slot_w, 端部凸卡点宽 pk_w 深 bd, 舌总深 = pk_d (卡点底落在喉口肩线)
    y0, yst, ytip = H + D, H + D + pd - bd, H + D + pd
    tongue = _poly("tongue", "flap",
                   [(xcl - sw2, y0), (xcl + sw2, y0), (xcl + sw2, yst),
                    (xcl + pw2, yst), (xcl + pw2, ytip), (xcl - pw2, ytip),
                    (xcl - pw2, yst), (xcl - sw2, yst)])
    edges += [_fold("e_t2", (x3, H), (x4, H), "w2", "t2", (0.0, -1.0, 0.0), "MOUNTAIN"),
              _fold("e_tongue", (xcl - sw2, y0), (xcl + sw2, y0),
                    "t2", "tongue", (0.0, 0.0, -1.0), "MOUNTAIN")]
    notes = (f"clv_snap_lock: 卡扣锁盖 — 前墙顶缘 T 形凹口 (口部宽槽 {pw:g}×{pd:g} "
             f"+ 喉部窄槽 {sw:g}×{sd:g}), 盖舌 T 形 (柄 {sw:g}, 凸卡点 {pw:g}×{bd:g}) "
             f"入槽腔, 卡点底缘落座喉口肩线 z=H-pk_d (板厚未建模, 保持以 T 槽腔座位"
             "证据表达); 4 墙链 + glue + 底全叠封")
    return panels + bp + [lid, tongue], edges + be, notes, _features("glue")


# ---------------------------------------------------------- ④ clv_hinged_flap
def _build_hinged_flap(p):
    W, D, H = float(p["W"]), float(p["D"]), float(p["H"])
    hs, ins, td = float(p["hs"]), float(p["ins"]), float(p["tuck_d"])
    panels, edges, xs = _chain(p, W, D, H)
    x1, x3, x4 = xs[0], xs[2], xs[3]
    bp, be = _bottom_full(p, xs)
    # 活页窄条: w2 顶缘直立窄条 (双折链第一折)
    strip = _rect("strip", "flap", x3, H, x4, H + hs)
    # 主盖: strip 远缘折平, 盖面抬升到 z=H+hs (第二折)
    lid = _poly("lid", "flap", [(x3, H + hs), (x4, H + hs), (x4, H + hs + D),
                                (x4 - ins, H + hs + D), (x3 + ins, H + hs + D),
                                (x3, H + hs)])
    tongue = _rect("tongue", "flap", x3 + ins, H + hs + D, x4 - ins, H + hs + D + td)
    edges += [_fold("e_strip", (x3, H), (x4, H), "w2", "strip", (0.0, 0.0, 1.0), "MOUNTAIN"),
              _fold("e_lid", (x3, H + hs), (x4, H + hs),
                    "strip", "lid", (0.0, -1.0, 0.0), "MOUNTAIN"),
              _fold("e_tongue", (x3 + ins, H + hs + D), (x4 - ins, H + hs + D),
                    "lid", "tongue", (0.0, 0.0, -1.0), "MOUNTAIN")]
    notes = (f"clv_hinged_flap: 铰链翻盖 — w2 顶缘活页窄条 (宽 {hs:g}) 直立 + 主盖 "
             f"折平的双折链, 盖面抬升至 z=H+hs 覆全顶 (深 D), 远缘插舌 (宽 "
             f"W-2*ins={W - 2 * ins:g}, 深 {td:g}) 入前墙内面; 4 墙链 + glue + 底全叠封")
    return panels + bp + [strip, lid, tongue], edges + be, notes, _features("glue")


# ---------------------------------------------------------- ⑤ clv_partial_lid
def _build_partial_lid(p):
    W, D, H = float(p["W"]), float(p["D"]), float(p["H"])
    panels, edges, xs = _chain(p, W, D, H)
    x3, x4 = xs[2], xs[3]
    bp, be = _bottom_full(p, xs)
    # 半盖: w2 出盖深 D/2 内折, 远缘落 y=D/2 中线, 不封顶无舌
    lid = _rect("lid", "flap", x3, H, x4, H + D / 2.0)
    edges.append(_fold("e_plid", (x3, H), (x4, H), "w2", "lid",
                       (0.0, -1.0, 0.0), "MOUNTAIN"))
    notes = (f"clv_partial_lid: 半盖 — w2 出盖深 D/2 内折, 远缘落 y=D/2 中线 "
             "(不封顶、无插舌, 供搭扣/开窗观察位); 4 墙链 + glue + 底全叠封")
    return panels + bp + [lid], edges + be, notes, _features("glue")


# ---------------------------------------------------------- ⑥ clv_double_cover
def _build_double_cover(p):
    W, D, H = float(p["W"]), float(p["D"]), float(p["H"])
    lwd, lin = float(p["lw_d"]), float(p["lin_in"])
    panels, edges, xs = _chain(p, W, D, H)
    x1, x3, x4 = xs[0], xs[2], xs[3]
    bp, be = _bottom_full(p, xs)
    xcl, lw2 = x3 + W / 2.0, W / 2.0 - lin
    # 主盖: w2 出全深 D, 远缘分点 (内衬盖铰链)
    lmain = _poly("lmain", "flap", [(x3, H), (x4, H), (x4, H + D),
                                    (xcl + lw2, H + D), (xcl - lw2, H + D), (x3, H)])
    # 内衬盖: 主盖远缘续链反折 +y (两片同链序), 覆主盖前段 z=H
    lliner = _rect("lliner", "flap", xcl - lw2, H + D, xcl + lw2, H + D + lwd)
    edges += [_fold("e_lmain", (x3, H), (x4, H), "w2", "lmain",
                    (0.0, -1.0, 0.0), "MOUNTAIN"),
              _fold("e_lliner", (xcl - lw2, H + D), (xcl + lw2, H + D),
                    "lmain", "lliner", (0.0, 1.0, 0.0), "MOUNTAIN")]
    notes = (f"clv_double_cover: 双层盖 — 主盖全深 D 自背墙覆全顶, 远缘续链反折 "
             f"内衬盖 (深 {lwd:g}, 两侧缩进 {lin:g}) 覆主盖前段, 两片同链序叠合增刚; "
             "4 墙链 + glue + 底全叠封")
    return panels + bp + [lmain, lliner], edges + be, notes, _features("glue")


# ---------------------------------------------------------- ⑦ clv_glue_seal
def _build_glue_seal(p):
    W, D, H = float(p["W"]), float(p["D"]), float(p["H"])
    gsd, tsw, tsd = float(p["gs_d"]), float(p["ts_w"]), float(p["ts_d"])
    panels, edges, xs = _chain(p, W, D, H)
    x1, x3, x4 = xs[0], xs[2], xs[3]
    bp, be = _bottom_full(p, xs)
    xcl, ts2 = x3 + W / 2.0, tsw / 2.0
    # 主盖全深 D (全宽, 无分点: 胶条全宽铰链)
    lid = _rect("lid", "flap", x3, H, x4, H + D)
    # 全宽胶条: 盖远缘下折贴前墙封口 (远缘带分点: 撕拉手铰链)
    gstrip = _poly("gstrip", "flap", [(x3, H + D), (x4, H + D), (x4, H + D + gsd),
                                      (xcl + ts2, H + D + gsd),
                                      (xcl - ts2, H + D + gsd), (x3, H + D + gsd)])
    # 撕拉手: 胶条下缘中央续链, 越出胶条下缘供撕开
    gtab = _rect("gtab", "flap", xcl - ts2, H + D + gsd, xcl + ts2, H + D + gsd + tsd)
    edges += [_fold("e_lid", (x3, H), (x4, H), "w2", "lid", (0.0, -1.0, 0.0), "MOUNTAIN"),
              _fold("e_gstrip", (x3, H + D), (x4, H + D),
                    "lid", "gstrip", (0.0, 0.0, -1.0), "MOUNTAIN"),
              _fold("e_gtab", (xcl - ts2, H + D + gsd), (xcl + ts2, H + D + gsd),
                    "gstrip", "gtab", (0.0, 0.0, -1.0), "MOUNTAIN")]
    notes = (f"clv_glue_seal: 胶封盖 — 主盖全深 D, 远缘全宽胶条 (深 {gsd:g}) 下折"
             f"贴前墙封口, 胶条下中央撕拉手 ({tsw:g}×{tsd:g}) 越出胶条下缘 "
             f"{tsd:g} 供撕开; 4 墙链 + glue + 底全叠封")
    return panels + bp + [lid, gstrip, gtab], edges + be, notes, _features("glue")


_BUILDERS = {0: _build_tuck_insert, 1: _build_double_tuck, 2: _build_snap_lock,
             3: _build_hinged_flap, 4: _build_partial_lid, 5: _build_double_cover,
             6: _build_glue_seal}


# ---------------------------------------------------------------- 契约
def class_params(cls_id: str) -> dict:
    """类ID → 全键参数表 (批量 build_ir 判型与取值的唯一权威)."""
    k = _KIND[cls_id]
    p = {key: 0.0 for key in PARAM_ORDER}
    p["kind"] = k
    if cls_id == "clv_tuck_insert":
        p.update({"W": 110.0, "D": 70.0, "H": 60.0, "glue_w": 12.0, "board_t": 0.45,
                  "tuck_d": 12.0, "slot_w": 24.0, "slot_d": 6.0})
    elif cls_id == "clv_double_tuck":
        p.update({"W": 100.0, "D": 60.0, "H": 50.0, "glue_w": 12.0, "board_t": 0.45,
                  "tuck_d": 10.0, "ins": 12.0})
    elif cls_id == "clv_snap_lock":
        p.update({"W": 100.0, "D": 60.0, "H": 50.0, "glue_w": 12.0, "board_t": 0.45,
                  "slot_w": 20.0, "slot_d": 5.0, "pk_w": 36.0, "pk_d": 9.0, "bd": 5.0})
    elif cls_id == "clv_hinged_flap":
        p.update({"W": 100.0, "D": 60.0, "H": 50.0, "glue_w": 12.0, "board_t": 0.45,
                  "hs": 8.0, "tuck_d": 10.0, "ins": 12.0})
    elif cls_id == "clv_partial_lid":
        p.update({"W": 110.0, "D": 70.0, "H": 60.0, "glue_w": 12.0, "board_t": 0.45})
    elif cls_id == "clv_double_cover":
        p.update({"W": 100.0, "D": 60.0, "H": 50.0, "glue_w": 12.0, "board_t": 0.45,
                  "lw_d": 32.0, "lin_in": 10.0})
    elif cls_id == "clv_glue_seal":
        p.update({"W": 100.0, "D": 60.0, "H": 50.0, "glue_w": 12.0, "board_t": 0.45,
                  "gs_d": 12.0, "ts_w": 30.0, "ts_d": 8.0})
    return p


def validate_params(params: dict) -> None:
    """参数语义: 相关键非零才校验 (家族不适用键置 0)."""
    pos = lambda k: isinstance(params.get(k), (int, float)) and \
        not isinstance(params.get(k), bool) and float(params.get(k)) > 0

    if pos("glue_w") and pos("W") and pos("D") and \
            float(params["glue_w"]) >= min(float(params["W"]), float(params["D"])):
        raise ValueError(f"粘口 glue_w={params['glue_w']} 须窄于最短墙 "
                         f"min(W,D)={min(params['W'], params['D'])}")
    if pos("tuck_d") and pos("H") and pos("hs") and \
            float(params["tuck_d"]) >= float(params["H"]) + float(params["hs"]):
        raise ValueError("铰链盖插舌深 tuck_d 须小于 H+hs (舌尖 z>0)")
    elif pos("tuck_d") and pos("H") and float(params["tuck_d"]) >= float(params["H"]):
        raise ValueError("插舌深 tuck_d 须小于盒高 H")
    if pos("slot_d") and pos("tuck_d") and \
            float(params["slot_d"]) >= float(params["tuck_d"]):
        raise ValueError("槽深 slot_d 须小于插舌深 tuck_d (舌尖须越过槽底)")
    if pos("slot_w") and pos("W") and float(params["slot_w"]) + 16.0 > float(params["W"]):
        raise ValueError("槽宽 slot_w 须窄于墙 W (两侧留 ≥8mm)")
    if pos("slot_w") and pos("pk_w") and \
            float(params["slot_w"]) >= float(params["pk_w"]):
        raise ValueError("喉部窄槽 slot_w 须窄于口部宽槽 pk_w")
    if pos("bd") and pos("pk_d") and float(params["bd"]) >= float(params["pk_d"]):
        raise ValueError("凸卡点深 bd 须小于口部宽槽深 pk_d (舌柄深 pk_d-bd>0)")
    if pos("pk_w") and pos("W") and float(params["pk_w"]) + 16.0 > float(params["W"]):
        raise ValueError("口部宽槽 pk_w 须窄于墙 W (两侧留 ≥8mm)")
    if pos("pk_d") and pos("slot_d") and pos("H") and \
            float(params["pk_d"]) + float(params["slot_d"]) >= float(params["H"]):
        raise ValueError("T 形凹口总深 pk_d+slot_d 须小于墙高 H")
    if pos("hs") and pos("H") and float(params["hs"]) >= float(params["H"]):
        raise ValueError("活页窄条宽 hs 须小于墙高 H")
    if pos("lw_d") and pos("D") and float(params["lw_d"]) >= float(params["D"]):
        raise ValueError("内衬盖深 lw_d 须小于盖深 D")
    if pos("lin_in") and pos("W") and 2 * float(params["lin_in"]) >= float(params["W"]):
        raise ValueError("内衬盖两侧缩进 2*lin_in 须窄于 W")
    if pos("gs_d") and pos("ts_d") and pos("H") and \
            float(params["gs_d"]) + float(params["ts_d"]) >= float(params["H"]):
        raise ValueError("胶条+撕拉手 gs_d+ts_d 须小于墙高 H (拉手尖 z>0)")
    if pos("ts_w") and pos("W") and float(params["ts_w"]) + 16.0 > float(params["W"]):
        raise ValueError("撕拉手宽 ts_w 须窄于墙 W (两侧留 ≥8mm)")


def build_ir(params: dict | None = None) -> dict:
    p = {**DEFAULTS, **(params or {})}
    kind = int(p.get("kind", 0))
    if kind not in _BUILDERS:
        raise ValueError(f"非法 kind={kind!r} (须 0..6)")
    cls_id = _CLS[kind]
    panels, edges, notes, feats = _BUILDERS[kind](p)
    return {
        "meta": {"ir_version": "0.1", "units": "mm",
                 "generator": "photo_dieline.parametric.closure_variants 0.1",
                 "notes": notes,
                 "root_panel": "w0",
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
    """G05 期望: solid (wall 角色) 折叠 bbox — 全家族单件墙环 W×D×H."""
    p = {**DEFAULTS, **(params or {})}
    return {"W": float(p["W"]), "D": float(p["D"]), "H": float(p["H"])}


def solid_roles():
    return ("wall",)


def allowed_overlap():
    """G06 允许叠层 (真实工艺契约, 全家族并集):
    粘口贴 w3 内面; 环闭合末墙↔首墙; 插舌/胶条/拉手贴前墙 (①穿槽/②④入内面/
    ⑦胶封); ③ T 舌与墙零面积相交仍按契约申报."""
    return {
        frozenset({"glue", "w3"}), frozenset({"w0", "w3"}),
        frozenset({"tongue", "w0"}),        # ①④ 插舌过槽/入前墙
        frozenset({"ta", "w0"}), frozenset({"tb", "w2"}),  # ② 双端插舌
        frozenset({"gstrip", "w0"}), frozenset({"gtab", "w0"}),  # ⑦ 胶封+撕拉手
    }


# ---------------------------------------------------------------- closure
def _fm(world, pid, i, j):
    return (np.asarray(world[pid][i], float) + np.asarray(world[pid][j], float)) / 2.0


def _d(a, b) -> float:
    return float(np.linalg.norm(np.asarray(a, float) - np.asarray(b, float)))


def _closure_base(ir, world, w0_lt=3) -> dict:
    """全家族公共封合证据: 墙环缝 + 粘缝平面 + 底全叠封 (远缘中线相抵).
    w0_lt: w0 左上角顶点索引 (矩形墙=3; 凹口墙=末点)."""
    res: dict[str, float] = {}
    res["ring.w3_w0"] = _d(_fm(world, "w3", 1, 2), _fm(world, "w0", 0, w0_lt))
    res["glue.seat"] = abs(float(np.mean(np.asarray(world["glue"]), axis=0)[0]))
    res["b.major.meet"] = _d(_fm(world, "b0", 0, 1), _fm(world, "b2", 0, 1))
    res["b.minor.meet"] = _d(_fm(world, "b1", 0, 1), _fm(world, "b3", 0, 1))
    res["b.major.z0"] = max(abs(float(_fm(world, "b0", 0, 1)[2])),
                            abs(float(_fm(world, "b2", 0, 1)[2])))
    return res


def _closure_tuck_insert(ir, world) -> dict:
    """① 插舌入槽: 盖远缘落前墙面 + 舌尖越槽底 + 舌-槽双侧对位 (跨链配准)."""
    H, td = ir.param("H"), ir.param("tuck_d")
    res = _closure_base(ir, world, w0_lt=7)  # 凹口 w0: 8 顶点, 左上角=末点
    lid_far = _fm(world, "t2", 2, 3)
    res["lid.far_y"] = abs(float(lid_far[1]))
    res["lid.zH"] = abs(float(lid_far[2]) - H)
    tip = _fm(world, "tongue", 2, 3)
    res["tongue.tip_z"] = abs(float(tip[2]) - (H - td))
    res["tongue.plane_y"] = abs(float(np.mean(np.asarray(world["tongue"]), axis=0)[1]))
    # 舌尖双侧 vs 墙槽口双侧 (跨链: 舌经 w2→t2→tongue 旋转链, 槽在根墙 w0)
    sl = sorted((float(world["tongue"][2][0]), float(world["tongue"][3][0])))
    wl = sorted((float(world["w0"][4][0]), float(world["w0"][5][0])))
    res["slot.align"] = abs(sl[0] - wl[0]) + abs(sl[1] - wl[1])
    return res


def _closure_double_tuck(ir, world) -> dict:
    """② 双端插舌: 两盖各自远缘落到对面墙平面 + 两舌入墙深度 + 顶面共面."""
    H, D, td = ir.param("H"), ir.param("D"), ir.param("tuck_d")
    res = _closure_base(ir, world)
    res["lt2.far_y"] = abs(float(_fm(world, "lt2", 2, 3)[1]))
    res["lt0.far_y"] = abs(float(_fm(world, "lt0", 2, 3)[1]) - D)
    res["lids.zH"] = max(abs(float(_fm(world, "lt2", 2, 3)[2]) - H),
                         abs(float(_fm(world, "lt0", 2, 3)[2]) - H))
    res["ta.tip_z"] = abs(float(_fm(world, "ta", 2, 3)[2]) - (H - td))
    res["tb.tip_z"] = abs(float(_fm(world, "tb", 2, 3)[2]) - (H - td))
    res["ta.plane_y"] = abs(float(np.mean(np.asarray(world["ta"]), axis=0)[1]))
    res["tb.plane_y"] = abs(float(np.mean(np.asarray(world["tb"]), axis=0)[1]) - D)
    return res


def _closure_snap_lock(ir, world) -> dict:
    """③ 卡扣锁盖: 卡点底缘落座喉口肩线 (跨链 z) + 卡点/柄与宽槽/窄槽双侧配准."""
    H, pw = ir.param("H"), ir.param("pk_w")
    res = _closure_base(ir, world, w0_lt=11)  # T 形凹口 w0: 12 顶点, 左上角=末点
    lid_far = _fm(world, "t2", 2, 3)
    res["lid.far_y"] = abs(float(lid_far[1]))
    res["lid.zH"] = abs(float(lid_far[2]) - H)
    w0 = np.asarray(world["w0"], float)
    # 墙 T 凹口: 口部宽槽右缘 v3/v4, 左缘 v9/v10; 喉部窄槽右缘 v5/v6, 左缘 v7/v8
    pocket_r, pocket_l = float(w0[3][0]), float(w0[9][0])
    throat_r, throat_l = float(w0[5][0]), float(w0[8][0])
    shoulder_z = float(w0[4][2])  # 喉口肩线 z = H - pk_d (槽底)
    tg = np.asarray(world["tongue"], float)
    res["snap.seat"] = abs(float(_fm(world, "tongue", 4, 5)[2]) - shoulder_z)
    bump_cx, bump_w = float((tg[4][0] + tg[5][0]) / 2.0), abs(float(tg[4][0] - tg[5][0]))
    res["snap.bump.cx"] = abs(bump_cx - (pocket_r + pocket_l) / 2.0)
    res["snap.bump.w"] = abs(bump_w - pw)
    stem_cx, stem_w = float((tg[0][0] + tg[1][0]) / 2.0), abs(float(tg[0][0] - tg[1][0]))
    res["snap.stem.cx"] = abs(stem_cx - (throat_r + throat_l) / 2.0)
    res["snap.stem.w"] = abs(stem_w - (throat_r - throat_l))
    res["tongue.plane_y"] = abs(float(np.mean(tg, axis=0)[1]))
    return res


def _closure_hinged_flap(ir, world) -> dict:
    """④ 铰链翻盖: 活页窄条直立 (共面背墙+顶到位) + 盖面抬升 H+hs + 远缘落前墙."""
    H, hs, td = ir.param("H"), ir.param("hs"), ir.param("tuck_d")
    res = _closure_base(ir, world)
    res["strip.plane"] = abs(float(np.mean(np.asarray(world["strip"]), axis=0)[1])
                             - ir.param("D"))
    res["strip.top_z"] = abs(float(_fm(world, "strip", 2, 3)[2]) - (H + hs))
    lid_far = _fm(world, "lid", 2, 3)
    res["lid.far_y"] = abs(float(lid_far[1]))
    res["lid.zH"] = abs(float(lid_far[2]) - (H + hs))
    res["tongue.tip_z"] = abs(float(_fm(world, "tongue", 2, 3)[2]) - (H + hs - td))
    res["tongue.plane_y"] = abs(float(np.mean(np.asarray(world["tongue"]), axis=0)[1]))
    return res


def _closure_partial_lid(ir, world) -> dict:
    """⑤ 半盖: 远缘落 y=D/2 中线 (内折不封顶) + 盖面共平面 z=H."""
    H = ir.param("H")
    res = _closure_base(ir, world)
    far = _fm(world, "lid", 2, 3)
    res["lid.far_y"] = abs(float(far[1]) - ir.param("D") / 2.0)
    res["lid.zH"] = abs(float(far[2]) - H)
    return res


def _closure_double_cover(ir, world) -> dict:
    """⑥ 双层盖: 主盖远缘落前墙 + 内衬反折远缘落 y=lw_d + 两片共面 z=H."""
    H, lwd = ir.param("H"), ir.param("lw_d")
    res = _closure_base(ir, world)
    main_far = _fm(world, "lmain", 2, 3)
    res["main.far_y"] = abs(float(main_far[1]))
    res["main.zH"] = abs(float(main_far[2]) - H)
    lin_far = _fm(world, "lliner", 2, 3)
    res["liner.far_y"] = abs(float(lin_far[1]) - lwd)
    res["liner.zH"] = abs(float(lin_far[2]) - H)
    res["liner.cx"] = abs(float((world["lliner"][2][0] + world["lliner"][3][0]) / 2.0)
                          - ir.param("W") / 2.0)
    return res


def _closure_glue_seal(ir, world) -> dict:
    """⑦ 胶封盖: 盖远缘落前墙 + 全宽胶条贴墙 (平面/深度/跨链全宽配准) + 拉手越出."""
    H, gsd, tsd = ir.param("H"), ir.param("gs_d"), ir.param("ts_d")
    res = _closure_base(ir, world)
    lid_far = _fm(world, "lid", 2, 3)
    res["lid.far_y"] = abs(float(lid_far[1]))
    res["lid.zH"] = abs(float(lid_far[2]) - H)
    res["seal.plane_y"] = abs(float(np.mean(np.asarray(world["gstrip"]), axis=0)[1]))
    res["seal.depth"] = abs(float(_fm(world, "gstrip", 2, 3)[2]) - (H - gsd))
    # 胶条全宽 vs 前墙展向配准 (跨链: 胶条经 w2→lid→gstrip, 墙为根)
    w0x = np.asarray(world["w0"], float)[:, 0]
    gsx = np.asarray(world["gstrip"], float)[:, 0]
    res["seal.width"] = (abs(float(gsx.min()) - float(w0x.min()))
                         + abs(float(gsx.max()) - float(w0x.max())))
    res["tab.tip_z"] = abs(float(_fm(world, "gtab", 2, 3)[2]) - (H - gsd - tsd))
    res["tab.cx"] = abs(float((world["gtab"][2][0] + world["gtab"][3][0]) / 2.0)
                        - float(w0x.max() + w0x.min()) / 2.0)
    res["tab.plane_y"] = abs(float(np.mean(np.asarray(world["gtab"]), axis=0)[1]))
    return res


_CLOSURES = {0: _closure_tuck_insert, 1: _closure_double_tuck, 2: _closure_snap_lock,
             3: _closure_hinged_flap, 4: _closure_partial_lid, 5: _closure_double_cover,
             6: _closure_glue_seal}


def closure_checks(ir, world) -> dict:
    return _CLOSURES[_KIND[ir.package["template"]["id"]]](ir, world)


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
    """负探针: 每类扰动 2 条关键折线 (edge, 世界铰链轴) → closure 最大残差
    须从 ~1e-13 爆到 mm 级. 返回 {edge_id: (baseline_max, perturbed_max)}."""
    raw = ir.raw
    base = max(float(v) for v in closure_checks(ir, fold_all(ir)).values())
    kind = _KIND[ir.package["template"]["id"]]
    targets = {0: [("e_t2", (1, 0, 0)), ("e_tongue", (1, 0, 0))],
               1: [("e_lt2", (1, 0, 0)), ("e_lt0", (1, 0, 0))],
               2: [("e_t2", (1, 0, 0)), ("e_tongue", (1, 0, 0))],
               3: [("e_strip", (1, 0, 0)), ("e_lid", (1, 0, 0))],
               4: [("e_plid", (1, 0, 0)), ("e_b0", (1, 0, 0))],
               5: [("e_lmain", (1, 0, 0)), ("e_lliner", (1, 0, 0))],
               6: [("e_lid", (1, 0, 0)), ("e_gstrip", (1, 0, 0))]}[kind]
    out = {}
    for eid, ax in targets:
        irp = from_raw(_perturb(raw, eid, ax))
        worst = max(float(v) for v in closure_checks(irp, fold_all(irp)).values())
        out[eid] = (base, worst)
    return out
