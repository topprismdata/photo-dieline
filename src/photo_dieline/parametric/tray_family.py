"""tray_family: 托盘/锁底家族 (五类六种).

类ID:
  tray_4corner         四角粘合盘: 中央底板+4墙, 4角片全高绕角折合粘于邻墙内面 (角缝即粘缝, 无粘口)
  tray_6corner         六角盘: 六边形中央底板+6墙+6半高角片(绕角折合)+粘口缝(缝上段)
  tray_wedge           楔形盘: 前低后高, 中央底板+梯形侧墙+粘口缝
  crashlock_rect       顺央底盒(开顶): 4墙链+全深底板×2+菱形互锁斜折片×4 (90°下折+180°斜折平铺互锁)
  crashlock_rect_tuck  顺央底盒(插盖): 同上 + 顶缘4内折盖片中心闭合
  lockbottom_123       1-2-3锁底: 4墙链+三段底折片(bL/bR/bF), 三段远缘互抵中心

几何约定: 世界系 x∈[0,W], y∈[0,D], z∈[0,H] (楔形 H=Hb);
  星形网类 (4corner/6corner/wedge) root=base, net(x,y)→world(x,y,0);
  链式网类 (crashlock/lockbottom) root=wF, net(x,y)→world(x,0,y)。
  所有折线显式 target_dir_3d (子面板 away 质心方向折至 tdir);
  互锁三角 180° 平折: tdir 取铰链直线镜像像方向 (数值推导, 非构造恒等)。
fam 参数编码类别 (1..5, schema params 仅数字), lid 由类ID派生不入参数。
"""
from __future__ import annotations

import math

import numpy as np

from . import base as _base

DEFAULTS = {"fam": 1, "W": 120.0, "D": 80.0, "H": 40.0, "Hf": 25.0, "Hb": 60.0,
            "side": 40.0, "glue_w": 12.0, "board_t": 0.45}
PARAM_ORDER = ["fam", "W", "D", "H", "Hf", "Hb", "side", "glue_w", "board_t"]

_FAM_CLS = {1: "tray_4corner", 2: "tray_6corner", 3: "tray_wedge",
            4: "crashlock_rect", 5: "lockbottom_123"}

# root_frame: 链式网 (net x,y → world x,0,y) / 星形网 (net x,y → world x,y,0)
_R_CHAIN = {"R": [[1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0]], "off": [0.0, 0.0, 0.0]}
_R_STAR = {"R": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], "off": [0.0, 0.0, 0.0]}


# ---------------------------------------------------------------- helpers
def _poly(pid, role, pts):
    return {"id": pid, "role": role,
            "polygon_2d": [[round(float(x), 4), round(float(y), 4)] for x, y in pts]}


def _fold(eid, a, b, parent, child, tdir, mt_va="VALLEY"):
    return {"id": eid, "kind": "FOLD",
            "seg_2d": [[round(float(a[0]), 4), round(float(a[1]), 4)],
                       [round(float(b[0]), 4), round(float(b[1]), 4)]],
            "fold": {"mt_va": mt_va, "parent": parent, "child": child,
                     "target_dir_3d": [round(float(v), 9) for v in tdir]}}


def _refl2(p, a, b):
    """点 p (z=0) 关于直线 (a,b) 的镜像; 返回 (3,) 世界向量."""
    p, a, b = (np.asarray(v, float) for v in (p, a, b))
    d = b[:2] - a[:2]
    v = p[:2] - a[:2]
    r = a[:2] + 2.0 * float(v @ d) / float(d @ d) * d - v
    return np.array([r[0], r[1], 0.0])


def _perp3(v, axis):
    """v 去除 axis 分量后归一 (锁定 tdir ⊥ 铰链轴)."""
    v = np.asarray(v, float)
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    w = v - float(v @ a) * a
    return w / np.linalg.norm(w)


def _hex_geom(side):
    """正六边形: edge0 落 y=0、中心在上; 返回 verts(6,2), outward[6], tangent[6]."""
    n = 6
    ctr = np.array([side / 2.0, side / (2.0 * math.tan(math.pi / n))])  # (side/2, apothem)
    R = side / (2.0 * math.sin(math.pi / n))                   # = side
    verts = np.array([ctr + R * np.array([math.cos(-math.pi / 2 - math.pi / n + 2 * math.pi * k / n),
                                          math.sin(-math.pi / 2 - math.pi / n + 2 * math.pi * k / n)])
                      for k in range(n)])
    outward, tangent = [], []
    for k in range(n):
        em = (verts[k] + verts[(k + 1) % n]) / 2.0
        o = em - ctr
        o = o / np.linalg.norm(o)
        outward.append(o)
        tangent.append(np.array([-o[1], o[0]]))  # 外法线 CCW 90° = 行进切向
    return verts, outward, tangent


# ---------------------------------------------------------------- tray_4corner
def _build_tray4(p):
    """中央底板 + 4墙 + 4全高角片 (角片绕竖直角棱折合, 粘于顺时针邻墙内面)."""
    W, D, H, gw = float(p["W"]), float(p["D"]), float(p["H"]), float(p["glue_w"])
    panels = [
        _poly("base", "wall", [(0, 0), (W, 0), (W, D), (0, D)]),
        _poly("wF", "wall", [(0, -H), (W, -H), (W, 0), (0, 0)]),
        _poly("wR", "wall", [(W, 0), (W + H, 0), (W + H, D), (W, D)]),
        _poly("wB", "wall", [(0, D), (W, D), (W, D + H), (0, D + H)]),
        _poly("wL", "wall", [(-H, 0), (0, 0), (0, D), (-H, D)]),
        # 角片: 全高直角三角形, 直角边 = 角棱 H × 搭接宽 gw (顺时针针轮)
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
    features = [{"id": f"f_{c}", "kind": "GLUE_TAB", "panel_id": c}
                for c in ("cFR", "cRB", "cBL", "cLF")]
    return "tray_4corner", panels, edges, features, _R_STAR, "base"


# ---------------------------------------------------------------- tray_6corner
def _build_tray6(p):
    """六边形中央底板 + 6墙 + 5全高角片 (墙隙 60° 楔区绕角折合) + 粘口缝 (末墙端棱全段,
    折合于 w0 内面; 第 6 角以粘缝合拢). 网面无叠合: 角片楔区恰被墙楔夹持, 粘口伸 +t5 空楔."""
    side, H, gw = float(p["side"]), float(p["H"]), float(p["glue_w"])
    verts, outward, tangent = _hex_geom(side)
    panels = [_poly("base", "wall", [tuple(v) for v in verts])]
    edges = []
    for i in range(6):
        j = (i + 1) % 6
        vi, vj, oi = verts[i], verts[j], outward[i]
        if i == 5:
            # 末墙端棱带半高分点 (粘口铰链端点须顶点: G03 核算); 起始三元组非共线 (G06 法线)
            half_v = vj + (H / 2.0) * oi
            panels.append(_poly(f"w{i}", "wall",
                                [vi + H * oi, vi, vj, half_v, vj + H * oi]))
        else:
            panels.append(_poly(f"w{i}", "wall",
                                [vi, vj, vj + H * oi, vi + H * oi]))
        edges.append(_fold(f"e_w{i}", vi, vj, "base", f"w{i}", (0.0, 0.0, 1.0)))
    # 角片 c_i (i=0..4): 挂 w_i 端棱全段的平行四边形条 (绕角棱折合于 w_{i+1} 内面下段);
    # 钝角外形避免 BLEED buffer 圆角弧密集 (G08 流长); c5 位由粘口承担
    for i in range(5):
        j = (i + 1) % 6
        m = np.array([outward[i][0] * math.cos(math.pi / 6) - outward[i][1] * math.sin(math.pi / 6),
                      outward[i][0] * math.sin(math.pi / 6) + outward[i][1] * math.cos(math.pi / 6)])
        A = verts[j]
        B = verts[j] + H * outward[i]
        C = B + gw * m
        Dp = A + gw * m
        panels.append(_poly(f"c{i}", "flap", [A, B, C, Dp]))
        edges.append(_fold(f"e_c{i}", A, B, f"w{i}", f"c{i}",
                           (*tangent[j], 0.0), "MOUNTAIN"))
    # 粘口: 末墙 w5 端棱上段 (w5 带半高分点), 展开越过端棱伸入墙外空楔 (+t5 向, 避开底板内角),
    # 折合于 w0 内面; 第 6 角由粘缝合拢 (c5 位让位于粘口)
    A = verts[0] + (H / 2.0) * outward[5]
    B = verts[0] + H * outward[5]
    C = B + gw * tangent[5]
    Dp = A + gw * tangent[5]
    panels.append(_poly("glue", "glue", [A, B, C, Dp]))
    edges.append(_fold("e_glue", A, B, "w5", "glue", (*tangent[0], 0.0), "MOUNTAIN"))
    features = [{"id": "f_glue", "kind": "GLUE_TAB", "panel_id": "glue"}]
    features += [{"id": f"f_c{i}", "kind": "GLUE_TAB", "panel_id": f"c{i}"} for i in range(5)]
    return "tray_6corner", panels, edges, features, _R_STAR, "base"


# ---------------------------------------------------------------- tray_wedge
def _build_wedge(p):
    """楔形盘: 中央底板 + 前低(Hf)后高(Hb) 墙带, 侧墙梯形, 粘口缝于左墙前棱."""
    W, D = float(p["W"]), float(p["D"])
    Hf, Hb, gw = float(p["Hf"]), float(p["Hb"]), float(p["glue_w"])
    panels = [
        _poly("base", "wall", [(0, 0), (W, 0), (W, D), (0, D)]),
        _poly("wF", "wall", [(0, -Hf), (W, -Hf), (W, 0), (0, 0)]),
        _poly("wR", "wall", [(W, 0), (W + Hf, 0), (W + Hb, D), (W, D)]),
        _poly("wB", "wall", [(0, D), (W, D), (W, D + Hb), (0, D + Hb)]),
        _poly("wL", "wall", [(-Hf, 0), (0, 0), (0, D), (-Hb, D)]),
        _poly("glue", "glue", [(-Hf, -gw), (0, -gw), (0, 0), (-Hf, 0)]),
    ]
    edges = [
        _fold("e_wF", (0, 0), (W, 0), "base", "wF", (0.0, 0.0, 1.0)),
        _fold("e_wR", (W, 0), (W, D), "base", "wR", (0.0, 0.0, 1.0)),
        _fold("e_wB", (0, D), (W, D), "base", "wB", (0.0, 0.0, 1.0)),
        _fold("e_wL", (0, 0), (0, D), "base", "wL", (0.0, 0.0, 1.0)),
        _fold("e_glue", (-Hf, 0), (0, 0), "wL", "glue", (1.0, 0.0, 0.0), "MOUNTAIN"),
    ]
    features = [{"id": "f_glue", "kind": "GLUE_TAB", "panel_id": "glue"}]
    return "tray_wedge", panels, edges, features, _R_STAR, "base"


def _crashlock_ratios(W, D):
    """互锁翼折线比例: hd(翼深), ya/yb(折线两端高度) — build 与 closure 共用."""
    hd = W / 2.0
    s = 0.5333 * D
    c = s * s / (hd * hd + s * s)
    ya = max(0.4 * D, ((1 - 2 * c) / (2 - 2 * c) + 0.02) * D)  # 保证镜像入盒
    return hd, ya, ya + s


# ---------------------------------------------------------------- crashlock
def _crashlock_common(p):
    """4墙链 + 全深底板 bF/bB + 斜折链互锁翼 gL0/gL1, gR0/gR1.

    斜折链 (逐段 away 链式推理):
      段1 wL→gL0 90° 下折平铺 (gL0=铰链侧梯形, 含翼底棱下段);
      段2 gL0→gL1 180° 斜折 (上升对角折线), 镜像三角越中线与对侧互锁 (菱形互锁).
    折线端点落在墙底棱分点 (墙多边形带共线分点, G03 顶点核算).
    """
    W, D, H, gw = float(p["W"]), float(p["D"]), float(p["H"]), float(p["glue_w"])
    hd, ya, yb = _crashlock_ratios(W, D)          # 翼深 = 半宽 (镜像越中线互锁)

    def _mirror_ok():
        """镜像四边形顶点须全在盒投影内 (数值守门)."""
        d = np.array([hd, yb - ya])
        pts = [np.array([0.0, D]), np.array([hd, D])]
        for q in pts:
            v = q - np.array([0.0, ya])
            t = float(v @ d) / float(d @ d)
            foot = np.array([0.0, ya]) + t * d
            m = 2 * foot - q
            if not (-1e-6 <= m[0] <= W + 1e-6 and -1e-6 <= m[1] <= D + 1e-6):
                return False
        return True

    if not _mirror_ok():
        raise ValueError(f"crashlock 镜像翼越界: W={W} D={D} (需 W/D ∈ [1.1, 2.4] 左右)")

    panels = [
        _poly("glue", "glue", [(-gw, 0), (0, 0), (0, H), (-gw, H)]),
        _poly("wF", "wall", [(0, 0), (W, 0), (W, H), (0, H)]),
        # wR/wL 底棱带分点; 顶点序从非共线三元组起始 (G06 法线核算用首三角)
        _poly("wR", "wall", [(W + ya, 0), (W + D, 0), (W + D, H), (W, H), (W, 0)]),
        _poly("wB", "wall", [(W + D, 0), (2 * W + D, 0), (2 * W + D, H), (W + D, H)]),
        # wL 底棱带分点 (折线端点须顶点: G03 共享边长核算)
        _poly("wL", "wall", [(2 * W + D + (D - ya), 0), (2 * W + 2 * D, 0),
                             (2 * W + 2 * D, H), (2 * W + D, H), (2 * W + D, 0)]),
        _poly("bF", "flap", [(0, -D), (W, -D), (W, 0), (0, 0)]),
        _poly("bB", "flap", [(W + D, -D), (2 * W + D, -D), (2 * W + D, 0), (W + D, 0)]),
        # 左右翼: gL0/gR0=铰链侧梯形 (90° 下折), gL1/gR1=上梯形 (180° 斜折, 由 _lock_fold 追加)
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
    ]

    def _lock_fold(pid, pts, seg_a, seg_b, crease_a, crease_b, parent):
        """互锁片: 多边形 pts (含折线边 seg_a-seg_b), 180° 斜折平铺.

        tdir = 镜像像质心方向 (⊥折线): 折线镜像为对合, 网面质心的像方向即折叠延伸方向.
        """
        panels.append(_poly(pid, "flap", pts))
        cen_net = np.mean(pts, axis=0)
        cen_pre = _net_to_world(parent, cen_net)
        cen_ref = _refl2(cen_pre, crease_a, crease_b)
        axis3 = np.array([crease_b[0] - crease_a[0], crease_b[1] - crease_a[1], 0.0])
        mid = np.array([(crease_a[0] + crease_b[0]) / 2.0,
                        (crease_a[1] + crease_b[1]) / 2.0, 0.0])
        tdir = _perp3(cen_ref - mid, axis3)
        edges.append(_fold(f"e_{pid}", seg_a, seg_b, parent, pid, tdir, "MOUNTAIN"))

    # 网面→底面世界映射: 左系 net(2W+D+s,-t)→(t, D-s, 0); 右系 net(W+s,-t)→(W-t, s, 0)
    def _net_to_world(parent, q):
        q = np.asarray(q, float)
        if parent == "gL0":
            return np.array([-q[1], D - (q[0] - (2 * W + D)), 0.0])
        return np.array([W + q[1], q[0] - W, 0.0])

    # 左互锁片: 网面 [(2W+D+(D-ya),0),(2W+D,0),(2W+D,-hd),(2W+D+(D-yb),-hd)],
    #   世界 {(0,ya),(0,D),(hd,D),(hd,yb)}; 折线 = 闭合边 (hd,yb)-(0,ya)
    _lock_fold("gL1",
               [(2 * W + D + (D - ya), 0), (2 * W + D, 0),
                (2 * W + D, -hd), (2 * W + D + (D - yb), -hd)],
               (2 * W + D + (D - yb), -hd), (2 * W + D + (D - ya), 0),
               (hd, yb), (0.0, ya), "gL0")
    # 右互锁片 (镜像): 世界 {(W,ya),(W,D),(W-hd,D),(W-hd,yb)}; 折线 = (W-hd,yb)-(W,ya)
    _lock_fold("gR1",
               [(W + ya, 0), (W + D, 0), (W + D, -hd), (W + yb, -hd)],
               (W + yb, -hd), (W + ya, 0),
               (W - hd, yb), (float(W), ya), "gR0")
    return panels, edges


def _build_crashlock(p):
    lid = p.get("lid", "open")
    panels, edges = _crashlock_common(p)
    W, D, H = float(p["W"]), float(p["D"]), float(p["H"])
    if lid == "tuck":
        panels += [
            _poly("tF", "flap", [(0, H), (W, H), (W, H + D / 2), (0, H + D / 2)]),
            _poly("tB", "flap", [(W + D, H), (2 * W + D, H), (2 * W + D, H + D / 2), (W + D, H + D / 2)]),
            _poly("tR", "flap", [(W, H), (W + D, H), (W + D, H + W / 2), (W, H + W / 2)]),
            _poly("tL", "flap", [(2 * W + D, H), (2 * W + 2 * D, H), (2 * W + 2 * D, H + W / 2), (2 * W + D, H + W / 2)]),
        ]
        edges += [
            _fold("e_tF", (0, H), (W, H), "wF", "tF", (0.0, 1.0, 0.0), "MOUNTAIN"),
            _fold("e_tB", (W + D, H), (2 * W + D, H), "wB", "tB", (0.0, -1.0, 0.0), "MOUNTAIN"),
            _fold("e_tR", (W, H), (W + D, H), "wR", "tR", (-1.0, 0.0, 0.0), "MOUNTAIN"),
            _fold("e_tL", (2 * W + D, H), (2 * W + 2 * D, H), "wL", "tL", (1.0, 0.0, 0.0), "MOUNTAIN"),
        ]
    features = [{"id": "f_glue", "kind": "GLUE_TAB", "panel_id": "glue"},
                {"id": "f_gL0", "kind": "GLUE_TAB", "panel_id": "gL0"},
                {"id": "f_gR0", "kind": "GLUE_TAB", "panel_id": "gR0"}]
    cls = "crashlock_rect_tuck" if lid == "tuck" else "crashlock_rect"
    return cls, panels, edges, features, _R_CHAIN, "wF"


# ---------------------------------------------------------------- lockbottom_123
def _build_lockbottom(p):
    """1-2-3锁底: 4墙链 + 三段底折片 bL(1)/bR(2)/bF(3 末折锁定), 三段远缘互抵中心."""
    W, D, H, gw = float(p["W"]), float(p["D"]), float(p["H"]), float(p["glue_w"])
    panels = [
        _poly("glue", "glue", [(-gw, 0), (0, 0), (0, H), (-gw, H)]),
        _poly("wF", "wall", [(0, 0), (W, 0), (W, H), (0, H)]),
        _poly("wR", "wall", [(W, 0), (W + D, 0), (W + D, H), (W, H)]),
        _poly("wB", "wall", [(W + D, 0), (2 * W + D, 0), (2 * W + D, H), (W + D, H)]),
        _poly("wL", "wall", [(2 * W + D, 0), (2 * W + 2 * D, 0), (2 * W + 2 * D, H), (2 * W + D, H)]),
        _poly("bF", "flap", [(0, -D / 2), (W, -D / 2), (W, 0), (0, 0)]),
        _poly("bR", "flap", [(W, -W / 2), (W + D, -W / 2), (W + D, 0), (W, 0)]),
        _poly("bL", "flap", [(2 * W + D, -W / 2), (2 * W + 2 * D, -W / 2), (2 * W + 2 * D, 0), (2 * W + D, 0)]),
    ]
    edges = [
        _fold("e_glue", (0, 0), (0, H), "wF", "glue", (1.0, 0.0, 0.0), "MOUNTAIN"),
        _fold("e_wR", (W, 0), (W, H), "wF", "wR", (0.0, 1.0, 0.0)),
        _fold("e_wB", (W + D, 0), (W + D, H), "wR", "wB", (-1.0, 0.0, 0.0)),
        _fold("e_wL", (2 * W + D, 0), (2 * W + D, H), "wB", "wL", (0.0, -1.0, 0.0)),
        _fold("e_bL", (2 * W + D, 0), (2 * W + 2 * D, 0), "wL", "bL", (1.0, 0.0, 0.0), "MOUNTAIN"),
        _fold("e_bR", (W, 0), (W + D, 0), "wR", "bR", (-1.0, 0.0, 0.0), "MOUNTAIN"),
        _fold("e_bF", (0, 0), (W, 0), "wF", "bF", (0.0, 1.0, 0.0), "MOUNTAIN"),
    ]
    features = [{"id": "f_glue", "kind": "GLUE_TAB", "panel_id": "glue"},
                {"id": "f_bF", "kind": "GLUE_TAB", "panel_id": "bF"}]
    return "lockbottom_123", panels, edges, features, _R_CHAIN, "wF"


# ---------------------------------------------------------------- contract
def validate_params(params: dict) -> None:
    p = params or {}
    for k in ("fam", "W", "D", "H", "Hf", "Hb", "side", "glue_w", "board_t"):
        v = p.get(k)
        if v is None:
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
            raise ValueError(f"非法参数 {k}={v!r} (须正数)")
    fam = int(p.get("fam", 1))
    if fam not in _FAM_CLS:
        raise ValueError(f"非法参数 fam={fam!r} (须 1..5)")
    if p.get("Hf") is not None and p.get("Hb") is not None and float(p["Hb"]) <= float(p["Hf"]):
        raise ValueError(f"楔形盘须 Hb > Hf (前低后高), 得 Hf={p['Hf']} Hb={p['Hb']}")
    if fam == 2 and float(p.get("glue_w", 12.0)) >= float(p.get("side", 40.0)):
        raise ValueError("六角盘须 glue_w < side (角片搭接不得越墙长)")
    if fam == 2 and float(p.get("glue_w", 12.0)) > float(p.get("H", 50.0)) / 2.0:
        raise ValueError("六角盘须 glue_w ≤ H/2 (粘口铰链段须在端棱上放下段)")
    if fam in (1, 4, 5) and float(p.get("glue_w", 12.0)) >= float(p.get("D", 1e9)) / 2.0:
        raise ValueError("glue_w/互锁翼过宽 (须 < D/2)")
    if fam in (1, 4, 5) and float(p.get("glue_w", 12.0)) >= float(p.get("W", 1e9)) / 2.0:
        raise ValueError("glue_w/互锁翼过宽 (须 < W/2)")
    lid = p.get("lid")
    if lid is not None and lid not in ("open", "tuck"):
        raise ValueError(f"非法 lid={lid!r} (open|tuck)")


def class_params(cls_id: str) -> dict:
    """类ID → 参数覆盖 (fam/尺寸/lid)."""
    base = {"glue_w": DEFAULTS["glue_w"], "board_t": DEFAULTS["board_t"]}
    if cls_id == "tray_4corner":
        return {**base, "fam": 1, "W": 120.0, "D": 80.0, "H": 40.0}
    if cls_id == "tray_6corner":
        return {**base, "fam": 2, "side": 40.0, "H": 50.0}
    if cls_id == "tray_wedge":
        return {**base, "fam": 3, "W": 100.0, "D": 60.0, "Hf": 25.0, "Hb": 60.0}
    if cls_id in ("crashlock_rect", "crashlock_rect_tuck"):
        return {**base, "fam": 4, "W": 100.0, "D": 60.0, "H": 80.0,
                "lid": "tuck" if cls_id.endswith("_tuck") else "open"}
    if cls_id == "lockbottom_123":
        return {**base, "fam": 5, "W": 90.0, "D": 50.0, "H": 70.0}
    raise KeyError(f"未知托盘类: {cls_id}")


for _cid in ("tray_4corner", "tray_6corner", "tray_wedge",
             "crashlock_rect", "crashlock_rect_tuck", "lockbottom_123"):
    _base.register(_cid, "tray_family")


def build_ir(params: dict | None = None) -> dict:
    p = dict(DEFAULTS)
    p.update(params or {})
    fam = int(p.get("fam", 1))
    lid = p.get("lid", "open")
    if fam == 1:
        cls_id, panels, edges, features, rf, root = _build_tray4(p)
    elif fam == 2:
        cls_id, panels, edges, features, rf, root = _build_tray6(p)
    elif fam == 3:
        cls_id, panels, edges, features, rf, root = _build_wedge(p)
    elif fam == 4:
        cls_id, panels, edges, features, rf, root = _build_crashlock(p)
    elif fam == 5:
        cls_id, panels, edges, features, rf, root = _build_lockbottom(p)
    else:
        raise ValueError(f"非法 fam={fam}")
    validate_params(p)
    return {
        "meta": {"ir_version": "0.1", "units": "mm", "generator": "photo_dieline.parametric.tray_family 0.1",
                 "notes": "托盘/锁底家族; 所有折线显式 target_dir_3d; 互锁片 180° 斜折平铺",
                 "root_panel": root, "root_frame": {"R": rf["R"], "off": rf["off"]}},
        "package": {"type": cls_id,
                    "template": {"id": cls_id, "version": "0.1"},
                    "params": {k: float(p[k]) for k in PARAM_ORDER},
                    "photo": None},
        "panels": panels,
        "edges": edges,
        "features": features,
    }


def analytic_bbox(params: dict) -> dict:
    """G05 期望: solid (wall: 底板+墙) 折叠 bbox."""
    p = {**DEFAULTS, **(params or {})}
    fam = int(p.get("fam", 1))
    if fam == 2:
        side, H = float(p["side"]), float(p["H"])
        return {"W": 2.0 * side, "D": math.sqrt(3.0) * side, "H": H}
    if fam == 3:
        return {"W": float(p["W"]), "D": float(p["D"]), "H": float(p["Hb"])}
    return {"W": float(p["W"]), "D": float(p["D"]), "H": float(p["H"])}


def solid_roles():
    return ("wall",)


def allowed_overlap():
    """允许叠层全集 (共面叠合/工艺粘缝): 角片贴邻墙内面, 底板/互锁片全对, 插盖顶片全对, 粘口贴墙."""
    s = set()
    # tray_4corner: 角片全高贴合顺时针邻墙内面
    for c, w in (("cFR", "wR"), ("cRB", "wB"), ("cBL", "wL"), ("cLF", "wF")):
        s.add(frozenset({c, w}))
    # tray_6corner: 角片贴邻墙内面 + 粘口贴 w0; 相邻墙缝/角片-底板棱触 (星网非链, G06 需显式契约)
    for i in range(5):
        s.add(frozenset({f"c{i}", f"w{(i + 1) % 6}"}))
        s.add(frozenset({"base", f"c{i}"}))
    for i in range(6):
        s.add(frozenset({f"w{i}", f"w{(i + 1) % 6}"}))
    s.add(frozenset({"glue", "w0"}))
    s.add(frozenset({"glue", "base"}))
    # crashlock: z=0 共面底板/主翼/互锁三角全对 + z=H 插盖顶片全对
    bottoms = ("bF", "bB", "gL0", "gR0", "gL1", "gR1")
    for i in range(len(bottoms)):
        for j in range(i + 1, len(bottoms)):
            s.add(frozenset({bottoms[i], bottoms[j]}))
    tops = ("tF", "tB", "tL", "tR")
    for i in range(len(tops)):
        for j in range(i + 1, len(tops)):
            s.add(frozenset({tops[i], tops[j]}))
    # lockbottom_123: 三段底片共面全对
    for a, b in (("bF", "bL"), ("bF", "bR"), ("bL", "bR")):
        s.add(frozenset({a, b}))
    # 链式网粘口缝合
    s.add(frozenset({"glue", "wF"}))
    return s


def _hex_closure_ref(side):
    verts, outward, _ = _hex_geom(side)
    return verts, outward


def closure_checks(ir, world) -> dict:
    """G04: 非铰链远缘真实闭合 — 角缝重合 / 底板抵墙 / 互锁镜像对称 / 远缘抵中心 / 片面贴合."""
    fam = int(ir.param("fam"))
    res: dict[str, float] = {}
    if fam == 1:
        # 四角缝: 相邻墙独立折起后远端顶点重合 (跨链)
        for name, pa, ia, pb, ib in (
                ("seam.FR", "wF", 1, "wR", 1), ("seam.RB", "wR", 2, "wB", 2),
                ("seam.BL", "wB", 3, "wL", 3), ("seam.LF", "wL", 0, "wF", 0)):
            res[name] = float(np.linalg.norm(world[pa][ia] - world[pb][ib]))
        for cid, ax, tgt in (("cFR", 0, None), ("cRB", 1, None), ("cBL", 0, 0.0), ("cLF", 1, 0.0)):
            tgt = float(ir.param("W")) if (cid == "cFR") else (float(ir.param("D")) if cid == "cRB" else tgt)
            res[f"{cid}.on_host"] = float(np.max(np.abs(world[cid][:, ax] - tgt)))
    elif fam == 2:
        side, H = float(ir.param("side")), float(ir.param("H"))
        verts, outward = _hex_closure_ref(side)
        # 墙 i 顶角 ↔ 墙 i+1 起始角重合 (w5 为 5 顶点旋转序: v0 顶=idx4, v5 顶=idx0)
        for i in range(4):
            j = (i + 1) % 6
            res[f"seam.v{j}"] = float(np.linalg.norm(world[f"w{i}"][2] - world[f"w{j}"][3]))
        res["seam.v5"] = float(np.linalg.norm(world["w4"][2] - world["w5"][0]))
        res["seam.v0"] = float(np.linalg.norm(world["w5"][4] - world["w0"][3]))
        for i in range(5):
            j = (i + 1) % 6
            d = world[f"c{i}"] - np.array([*verts[j], 0.0])
            res[f"c{i}.on_plane"] = float(np.max(np.abs(d @ np.array([*outward[j], 0.0]))))
        g = world["glue"] - np.array([*verts[0], 0.0])
        res["glue.on_plane"] = float(np.max(np.abs(g @ np.array([*outward[0], 0.0]))))
    elif fam == 3:
        for name, pa, ia, pb, ib in (
                ("seam.FR", "wF", 1, "wR", 1), ("seam.RB", "wR", 2, "wB", 2),
                ("seam.BL", "wB", 3, "wL", 3), ("seam.LF", "wL", 0, "wF", 0)):
            res[name] = float(np.linalg.norm(world[pa][ia] - world[pb][ib]))
        res["glue.planar_y0"] = float(np.max(np.abs(world["glue"][:, 1])))
    elif fam == 4:
        W, D, H = float(ir.param("W")), float(ir.param("D")), float(ir.param("H"))
        # 环缝 (末墙远缘 ↔ 首墙近缘; wL 顶点旋转序: 远缘=idx1/idx2)
        res["seam.LF.bot"] = float(np.linalg.norm(world["wL"][1] - world["wF"][0]))
        res["seam.LF.top"] = float(np.linalg.norm(world["wL"][2] - world["wF"][3]))
        # 全深底板远缘抵对面墙底缘 (跨链)
        res["bF.tucks_wB"] = float(np.linalg.norm(np.mean(world["bF"][0:2], axis=0)
                                                  - np.mean(world["wB"][0:2], axis=0)))
        res["bB.tucks_wF"] = float(np.linalg.norm(np.mean(world["bB"][0:2], axis=0)
                                                  - np.mean(world["wF"][0:2], axis=0)))
        # 菱形互锁: 180° 斜折链逐段验 — 镜像角位置(解析预期) + 左右对称 + 等距性
        hd, ya, yb = _crashlock_ratios(W, D)
        ca = np.array([hd, yb])           # 折线端 (网 seg_a 侧)
        cb = np.array([0.0, ya])          # 折线端 (网 seg_b 侧)
        dd = cb - ca
        t_star = float((np.array([hd, D]) - ca) @ dd) / float(dd @ dd)
        mirror = 2 * (ca + t_star * dd) - np.array([hd, D])   # 互锁角解析镜像位
        mxL, mxR = float(world["gL1"][2][0]), float(world["gR1"][2][0])
        res["lock.mirror_x"] = abs(mxL - mirror[0]) + abs((W - mxR) - mirror[0])
        res["lock.sym_x"] = abs(mxL + mxR - W)
        res["lock.iso"] = abs(float(np.linalg.norm(world["gL1"][2] - world["gL1"][1])) - hd)
        res["lock.flat"] = abs(float(world["gL1"][2][2])) + abs(float(world["gR1"][2][2]))
        if "tF" in world:
            res["tuck.FB"] = float(np.linalg.norm(np.mean(world["tF"][2:4], axis=0)
                                                  - np.mean(world["tB"][2:4], axis=0)))
            res["tuck.LR"] = float(np.linalg.norm(np.mean(world["tL"][2:4], axis=0)
                                                  - np.mean(world["tR"][2:4], axis=0)))
        res["glue.planar_y0"] = float(np.max(np.abs(world["glue"][:, 1])))
    else:
        W, D = float(ir.param("W")), float(ir.param("D"))
        res["seam.LF.bot"] = float(np.linalg.norm(world["wL"][1] - world["wF"][0]))
        res["seam.LF.top"] = float(np.linalg.norm(world["wL"][2] - world["wF"][3]))
        ctr = np.array([W / 2.0, D / 2.0, 0.0])
        # 1-2-3: 三段远缘互抵中心
        res["bL.bR.center"] = float(np.linalg.norm(np.mean(world["bL"][0:2], axis=0)
                                                   - np.mean(world["bR"][0:2], axis=0)))
        res["bF.center"] = float(np.linalg.norm(np.mean(world["bF"][0:2], axis=0) - ctr))
        res["glue.planar_y0"] = float(np.max(np.abs(world["glue"][:, 1])))
    return res
