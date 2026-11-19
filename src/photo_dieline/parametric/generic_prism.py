"""generic_prism: 正 n 棱柱家族 (批量验证主力).

类ID: prism_n{n}_{lid}  lid ∈ {"open" 开口托盘, "tuck" 内折插盖}
拓扑: n 墙板链 + glue 搭接缝 + n 底板星形内折 (n>=4 中心闭合)
     tuck lid = 顶缘再折同深度的内折板 (拓扑翻倍)

几何约定: 根墙 wall0 占 y=0 平面, net(x,y)→world(x,0,y);
         n 边形中心 (side/2, apothem); 顶点角 θk 从 edge0 起算。
"""
from __future__ import annotations

import math

import numpy as np

from . import base as _base

DEFAULTS = {"n": 4, "side": 60.0, "h": 100.0, "glue_w": 12.0, "board_t": 0.42}
PARAM_ORDER = ["n", "side", "h", "glue_w", "board_t"]

_APOTHEM_TOL = 0.2


def _apothem(n: int, side: float) -> float:
    return side / (2.0 * math.tan(math.pi / n))


def _circumradius(n: int, side: float) -> float:
    return side / (2.0 * math.sin(math.pi / n))


def _classes():
    for n in range(4, 13):
        for lid in ("open", "tuck"):
            yield f"prism_n{n}_{lid}", n, lid


def validate_params(params: dict) -> None:
    for k in ("side", "h", "glue_w", "board_t"):
        v = params.get(k)
        if v is None or not isinstance(v, (int, float)) or isinstance(v, bool) or v <= 0:
            raise ValueError(f"非法参数 {k}={v!r} (须正数)")
    n = params.get("n")
    if not isinstance(n, int) or isinstance(n, bool) or not (3 <= n <= 24):
        raise ValueError(f"非法参数 n={n!r} (须 3..24 整数)")


def class_params(cls_id: str) -> dict:
    """类ID → 参数覆盖: prism_n10_tuck → {"n":10, "lid":"tuck"}."""
    body = cls_id.removeprefix("prism_n")
    n_str, lid = body.rsplit("_", 1)
    return {"n": int(n_str), "lid": lid}


for _cid, _n, _lid in _classes():
    _base.register(_cid, "generic_prism")


def build_ir(params: dict | None = None) -> dict:
    p = dict(DEFAULTS)
    p.update(params or {})
    n, side, h, gw = int(p["n"]), float(p["side"]), float(p["h"]), float(p["glue_w"])
    lid = p.get("lid", "open")
    a = _apothem(n, side)          # 底板折入深度 = 内切半径
    cls_id = f"prism_n{n}_{lid}"

    panels, edges = [], []

    # 墙板带: [glue][w0][w1]...[w_{n-1}]  (net 连续横排, 每墙宽 side)
    panels.append({"id": "glue", "role": "glue",
                   "polygon_2d": [[0, 0], [gw, 0], [gw, h], [0, h]]})
    for i in range(n):
        x0 = gw + i * side
        panels.append({"id": f"w{i}", "role": "wall",
                       "polygon_2d": [[x0, 0], [x0 + side, 0], [x0 + side, h], [x0, h]]})
    x_last = gw + n * side

    # 底板: 每墙下折, 深 = apothem (星形闭合)
    for i in range(n):
        x0 = gw + i * side
        panels.append({"id": f"b{i}", "role": "flap",
                       "polygon_2d": [[x0, -a], [x0 + side, -a], [x0 + side, 0], [x0, 0]]})

    # 插盖: 顶缘上折同深度 (tuck only)
    if lid == "tuck":
        for i in range(n):
            x0 = gw + i * side
            panels.append({"id": f"t{i}", "role": "flap",
                           "polygon_2d": [[x0, h], [x0 + side, h], [x0 + side, h + a], [x0, h + a]]})

    # 折线 (全部显式 tdir; 世界系见 docstring)
    # 顶点解析: 中心 (side/2, a), 角 φk = π + 2πk/n (使 edge0 = (0,0)-(side,0))
    ctr = np.array([side / 2.0, a])
    verts = [ctr + _circumradius(n, side) * np.array([math.cos(-math.pi / 2 - math.pi / n + 2 * math.pi * k / n),
                                                      math.sin(-math.pi / 2 - math.pi / n + 2 * math.pi * k / n)]) for k in range(n)]
    edge_mid = [(verts[k] + verts[(k + 1) % n]) / 2.0 for k in range(n)]
    outward = [np.array([em[0] - ctr[0], em[1] - ctr[1]]) for em in edge_mid]
    outward = [o / np.linalg.norm(o) for o in outward]
    # 切向 = 外法线 CCW 90°: edge_k 从 v_k 到 v_{k+1} 的行进方向
    tangent = [np.array([-o[1], o[0]]) for o in outward]

    def fold(eid, a2, b2, parent, child, tdir, mt_va="VALLEY"):
        f = {"id": eid, "kind": "FOLD", "seg_2d": [list(a2), list(b2)],
             "fold": {"mt_va": mt_va, "parent": parent, "child": child,
                      "target_dir_3d": [round(float(v), 9) for v in tdir]}}
        edges.append(f)

    # 墙链: w_i -> w_{i+1}  铰链 = 顶点 i+1 竖线; tdir = 外法线_{i+1}
    for i in range(n - 1):
        x = gw + (i + 1) * side
        fold(f"e_w{i}", (x, 0), (x, h), f"w{i}", f"w{i + 1}", (*tangent[i + 1], 0.0))
    # glue -> w0  (tdir = w0 外法线的反方向? glue 贴内: 同 gable 模式 tdir = +y 世界=内法线 w0 的外法线是 -y... )
    # glue 在 net 最左, 铰链 x=gw 竖线, away = -x(net) → 世界 -x; 折到 w0 内侧贴面 = y=0 平面 → tdir = (1,0,0)
    fold(f"e_glue", (gw, 0), (gw, h), "w0", "glue", (1.0, 0.0, 0.0), "MOUNTAIN")
    # 底板: w_i -> b_i  铰链 = 墙底缘; tdir = 内向水平 = -outward_i
    for i in range(n):
        x0 = gw + i * side
        fold(f"e_b{i}", (x0, 0), (x0 + side, 0), f"w{i}", f"b{i}",
             (*(-outward[i]), 0.0))
    if lid == "tuck":
        for i in range(n):
            x0 = gw + i * side
            fold(f"e_t{i}", (x0, h), (x0 + side, h), f"w{i}", f"t{i}",
                 (*(-outward[i]), 0.0))

    ir = {
        "meta": {"ir_version": "0.1", "units": "mm", "generator": "generic_prism",
                 "root_panel": "w0",
                 "root_frame": {"R": [[1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                                "off": [-gw, 0.0, 0.0]}},
        "package": {"type": f"prism_n{n}_{lid}",
                    "template": {"id": cls_id, "version": "0.1"},
                    "params": {k: p[k] for k in PARAM_ORDER if k in p},
                    "photo": None},
        "panels": panels,
        "edges": edges,
        "features": [{"id": "f_glue", "kind": "GLUE_TAB", "panel_id": "glue"}],
    }
    return ir


def analytic_bbox(params: dict) -> dict:
    """G05 期望: 墙板实体 (wall 角色) 的 n 边形 bbox × h."""
    p = {**DEFAULTS, **(params or {})}
    n, side, h = int(p["n"]), float(p["side"]), float(p["h"])
    ctr = np.array([side / 2.0, _apothem(n, side)])
    R = _circumradius(n, side)
    vs = [ctr + R * np.array([math.cos(-math.pi / 2 - math.pi / n + 2 * math.pi * k / n),
                              math.sin(-math.pi / 2 - math.pi / n + 2 * math.pi * k / n)]) for k in range(n)]
    xs = [v[0] for v in vs]
    ys = [v[1] for v in vs]
    return {"W": float(max(xs) - min(xs)), "D": float(max(ys) - min(ys)), "H": float(h)}


def solid_roles():
    return ("wall",)


def allowed_overlap():
    """星形底板全对允许 (z=0 共面叠层契约) + glue 贴 w0."""
    s = set()
    for n in range(4, 13):
        bs = [f"b{i}" for i in range(n)]
        ts = [f"t{i}" for i in range(n)]
        for i in range(len(bs)):
            for j in range(i + 1, len(bs)):
                s.add(frozenset({bs[i], bs[j]}))
        for i in range(len(ts)):
            for j in range(i + 1, len(ts)):
                s.add(frozenset({ts[i], ts[j]}))
        for i in range(len(bs)):
            for j in range(len(ts)):
                s.add(frozenset({bs[i], ts[j]}))
    # 环闭合: 末墙↔首墙共享棱 (工艺粘缝) + glue 端缘触末墙
    for n in range(4, 13):
        s.add(frozenset({f"w0", f"w{n - 1}"}))
        s.add(frozenset({"glue", f"w{n - 1}"}))
    s.add(frozenset({"glue", "w0"}))
    return s


def closure_checks(ir, world) -> dict:
    """G04: 底板星形闭合 (远缘中点过轴线) + glue 缝合 + tuck 顶闭合."""
    n = int(ir.param("n"))
    side = float(ir.param("side"))
    ctr = np.array([side / 2.0, _apothem(n, side), 0.0])
    res: dict[str, float] = {}
    for i in range(n):
        fm = np.mean(world[f"b{i}"][0:2], axis=0)
        res[f"b{i}.far_to_axis"] = float(abs(np.linalg.norm(fm[:2] - ctr[:2])))
    if f"t{n - 1}" in world:
        for i in range(n):
            fm = np.mean(world[f"t{i}"][2:4], axis=0)
            top = np.array([ctr[0], ctr[1], float(ir.param("h"))])
            res[f"t{i}.far_to_axis"] = float(abs(np.linalg.norm(fm[:2] - top[:2])))
    # glue 远缘 (x=0 net) 贴 w0 内侧: 世界应在 y=0 平面 x∈[0,gw]
    gm = np.mean(world["glue"][0:2], axis=0)
    res["glue.planar_y0"] = float(abs(gm[1]))
    return res
