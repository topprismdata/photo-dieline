"""pizza_box: 经典 Baked 一体式披萨盒家族 (新家族完整对标实测 — agent 按契约从零到量产).

拓扑: 底板 + 四墙 (自底四缘上折) + 平盖 (背墙顶缘铰链内折 90°)
     + 前唇压线条 (前墙顶缘铰链内折, 贴盖内面) + 左右内贴翼 (侧墙顶缘铰链内折, 垫盖下).
闭合证据 (closure_checks): 环角密合 (四墙角棱重合) + 盖前缘落在唇面 (平面+跨度) +
左右翼远缘贴盖面 + 唇远缘贴盖面 — 五重真实接触残差.
坐标系: root=bottom 平铺 z=0, net x→world x (宽 W), net y→world y (深 D), 上折=+z.
"""
from __future__ import annotations

import math

import numpy as np

from . import base as _base

DEFAULTS = {"W": 330.0, "D": 330.0, "H": 50.0, "lip_w": 12.0, "flap_w": 25.0,
            "board_t": 0.42}
PARAM_ORDER = ["W", "D", "H", "lip_w", "flap_w", "board_t"]


def _classes():
    yield "pizza_box_330", dict(W=330.0, D=330.0, H=50.0)


def validate_params(params: dict) -> None:
    for k in ("W", "D", "H", "lip_w", "flap_w", "board_t"):
        v = float(params.get(k, DEFAULTS[k]))
        if not (0.0 < v < 5000.0):
            raise ValueError(f"非法参数 {k}={v!r} (须 (0, 5000))")
    if float(params.get("lip_w", 12.0)) >= float(params.get("D", 330.0)) / 2:
        raise ValueError("lip_w 须 < D/2")
    if float(params.get("flap_w", 25.0)) >= float(params.get("W", 330.0)) / 2:
        raise ValueError("flap_w 须 < W/2")


def class_params(cls_id: str) -> dict:
    for cid, ov in _classes():
        if cid == cls_id:
            return dict(ov)
    raise KeyError(cls_id)


for _cid, _ov in _classes():
    _base.register(_cid, "pizza_box")


def build_ir(params: dict | None = None) -> dict:
    p = dict(DEFAULTS)
    p.update(params or {})
    W, D, H = float(p["W"]), float(p["D"]), float(p["H"])
    lw, fw = float(p["lip_w"]), float(p["flap_w"])

    panels, edges = [], []

    def rect(pid, role, x0, y0, x1, y1):
        panels.append({"id": pid, "role": role,
                       "polygon_2d": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]})

    rect("bottom", "wall", 0, 0, W, D)
    rect("wall_bk", "wall", 0, D, W, D + H)          # 背墙 (net y>D)
    rect("wall_ft", "wall", 0, -H, W, 0)             # 前墙 (net y<0)
    rect("wall_l", "wall", -H, 0, 0, D)              # 左墙
    rect("wall_r", "wall", W, 0, W + H, D)           # 右墙
    rect("lid", "wall", 0, D + H, W, D + H + D)       # 平盖 (背墙顶缘续接)
    rect("lip", "flap", 0, -H - lw, W, -H)            # 前唇 (前墙顶缘续接)
    rect("flap_l", "flap", -H - fw, 0, -H, D)        # 左翼 (左墙顶缘续接)
    rect("flap_r", "flap", W + H, 0, W + H + fw, D)  # 右翼

    def fold(eid, a2, b2, parent, child, tdir, mt_va="MOUNTAIN"):
        edges.append({"id": eid, "kind": "FOLD", "seg_2d": [list(a2), list(b2)],
                      "fold": {"mt_va": mt_va, "parent": parent, "child": child,
                               "target_dir_3d": [round(float(v), 9) for v in tdir]}})

    UP = (0.0, 0.0, 1.0)
    fold("e_bk", (0, D), (W, D), "bottom", "wall_bk", UP)                # 背墙上折
    fold("e_ft", (0, 0), (W, 0), "bottom", "wall_ft", UP)                # 前墙上折
    fold("e_l", (0, 0), (0, D), "bottom", "wall_l", UP)                  # 左墙上折
    fold("e_r", (W, 0), (W, D), "bottom", "wall_r", UP)                  # 右墙上折
    fold("e_lid", (0, D + H), (W, D + H), "wall_bk", "lid", (0.0, -1.0, 0.0))  # 盖内折 (-y)
    fold("e_lip", (0, -H), (W, -H), "wall_ft", "lip", (0.0, 1.0, 0.0))         # 唇内折 (+y)
    fold("e_fl", (-H, 0), (-H, D), "wall_l", "flap_l", (1.0, 0.0, 0.0))        # 左翼内折 (+x)
    fold("e_fr", (W + H, 0), (W + H, D), "wall_r", "flap_r", (-1.0, 0.0, 0.0))  # 右翼内折 (-x)

    ir = {
        "meta": {"ir_version": "0.1", "units": "mm", "generator": "pizza_box",
                 "root_panel": "bottom",
                 "root_frame": {"R": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                                "off": [0.0, 0.0, 0.0]}},
        "package": {"type": "pizza_box", "template": {"id": "pizza_box_330", "version": "0.1"},
                    "params": {k: p[k] for k in PARAM_ORDER if k in p}, "photo": None},
        "panels": panels,
        "edges": edges,
        "features": [{"id": "f_lip", "kind": "GLUE_TAB", "panel_id": "lip"}],
    }
    return ir


def analytic_bbox(params: dict) -> dict:
    """G05 期望: 闭合盒外壳 W×D×H (盖齐平 z=H)."""
    p = {**DEFAULTS, **(params or {})}
    return {"W": float(p["W"]), "D": float(p["D"]), "H": float(p["H"])}


def solid_roles():
    return ("wall",)


def allowed_overlap():
    """z=H 平面共面叠合契约: 盖↔唇/左右翼 + 唇↔左右翼 (角区) + 环角四墙对."""
    s = set()
    for a in ("lip", "flap_l", "flap_r"):
        s.add(frozenset({"lid", a}))
    s.add(frozenset({"lip", "flap_l"}))
    s.add(frozenset({"lip", "flap_r"}))
    for pair in (("wall_bk", "wall_l"), ("wall_bk", "wall_r"),
                 ("wall_ft", "wall_l"), ("wall_ft", "wall_r")):
        s.add(frozenset(pair))
    return s


def closure_checks(ir, world) -> dict:
    """G04: 环角密合 (四墙共享角棱顶点重合) + 盖前缘落唇面 (平面+跨度)
    + 唇/左右翼远缘贴盖面 (平面+跨度). 判据=真实接触证据, 负探针须全检出."""
    W, D, H = float(ir.param("W")), float(ir.param("D")), float(ir.param("H"))
    lw, fw = float(ir.param("lip_w")), float(ir.param("flap_w"))
    res: dict[str, float] = {}

    def V(pid, i):
        return np.asarray(world[pid], float)[i]

    def EM(pid, i, j):
        return (V(pid, i) + V(pid, j)) / 2.0

    def span_ok(p, x0, x1, y0, y1):
        return 0.0 if (x0 - 0.5 <= p[0] <= x1 + 0.5 and y0 - 0.5 <= p[1] <= y1 + 0.5) else 1e3

    # 环角: 每个盒角处两相邻墙的角点 z 集合对称差 (与引擎顶点序无关;
    # 任一墙折反 → 其 z 集 {0,-H} 对 {0,H} 对称差=H, 立爆 mm 级)
    corners_pts = [(0, 0, "wall_ft", "wall_l"), (W, 0, "wall_ft", "wall_r"),
                   (W, D, "wall_bk", "wall_r"), (0, D, "wall_bk", "wall_l")]
    for cx, cy, a, b in corners_pts:
        def zset(pid):
            vs = np.asarray(world[pid], float)
            near = vs[(np.abs(vs[:, 0] - cx) < 1.0) & (np.abs(vs[:, 1] - cy) < 1.0)]
            return sorted(float(z) for z in near[:, 2])
        za, zb = zset(a), zset(b)
        d1 = max((min(abs(z - y) for y in zb) for z in za), default=1e3)
        d2 = max((min(abs(z - y) for y in za) for z in zb), default=1e3)
        res[f"corner_{a}_{b}"] = float(max(d1, d2))

    # 远缘中点: 取面板顶点中距铰链"线"最远的簇均值 (叉积线距, 非原点距 —
    # 盖宽端顶点躺在铰线上但离原点可达 D, 原点距会误选; 引擎顶点序亦随折叠朝向变)
    def far_mid(pid, origin, axis):
        vs = np.asarray(world[pid], float)
        ax = np.asarray(axis, float) / np.linalg.norm(axis)
        d = np.linalg.norm(np.cross(vs - np.asarray(origin, float), ax), axis=1)
        far = vs[d >= 0.5 * d.max()]
        return far.mean(axis=0)

    # 盖前缘中点落唇面: z=H 平面 + 唇跨度 (铰链=背墙顶棱)
    lf = far_mid("lid", (0, D, H), (1, 0, 0))
    res["lid_front_on_lip"] = float(abs(lf[2] - H) + span_ok(lf, 0, W, 0, lw))

    # 唇远缘贴盖面: z=H + 盖跨度 (铰链=前墙顶棱)
    lm = far_mid("lip", (0, 0, H), (1, 0, 0))
    res["lip_far_on_lid"] = float(abs(lm[2] - H) + span_ok(lm, 0, W, 0, D))

    # 左右翼远缘贴盖面: z=H + 盖跨度 (铰链=侧墙顶棱)
    for pid, ox in (("flap_l", 0.0), ("flap_r", W)):
        fm = far_mid(pid, (ox, 0, H), (0, 1, 0))
        res[f"{pid}_far_on_lid"] = float(abs(fm[2] - H) + span_ok(fm, 0, W, 0, D))
    return res
