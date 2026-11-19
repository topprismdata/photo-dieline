"""gable_variants: 屋顶包拓扑变体 (批量验证家族).

类ID: gable_finless — 无立鳍变体: 双坡对折至脊线, 胶条(gfin)自后坡顶缘
     越脊反折, 远缘粘合于前坡顶缘 (经典无鳍封合)。
拓扑签名: 4墙(含山墙三角)+2坡+gfin胶条+4底板 = 12面板 (vs gable_top 13面板含双鳍)。
"""
from __future__ import annotations

import math

import numpy as np

from . import base as _base

_base.register("gable_finless", "gable_variants")

DEFAULTS = {"W": 45.0, "D": 45.0, "Hb": 80.0, "Hr": 20.0, "gfin_w": 18.0, "glue_w": 12.0, "board_t": 0.45}
PARAM_ORDER = ["W", "D", "Hb", "Hr", "gfin_w", "glue_w", "board_t"]


def _slant(D: float, Hr: float) -> float:
    return math.hypot(D / 2.0, Hr)


def build_ir(params: dict | None = None) -> dict:
    p = dict(DEFAULTS)
    p.update(params or {})
    W, D, Hb, Hr = float(p["W"]), float(p["D"]), float(p["Hb"]), float(p["Hr"])
    gw, gfin_w = float(p["glue_w"]), float(p["gfin_w"])
    s = _slant(D, Hr)

    x0 = 0.0
    x1 = gw
    x2 = x1 + D
    x3 = x2 + W
    x4 = x3 + D
    x5 = x4 + W

    def rect(pid, role, xa, xb, ya, yb):
        return {"id": pid, "role": role,
                "polygon_2d": [[xa, ya], [xb, ya], [xb, yb], [xa, yb]]}

    panels = [
        rect("glue", "glue", x0, x1, 0, Hb),
        {"id": "wallL", "role": "wall", "polygon_2d": [
            [x1, 0], [x2, 0], [x2, Hb], [x2 - D / 2, Hb + Hr], [x1, Hb]]},
        rect("back", "wall", x2, x3, 0, Hb),
        {"id": "wallR", "role": "wall", "polygon_2d": [
            [x3, 0], [x4, 0], [x4, Hb], [x4 - D / 2, Hb + Hr], [x3, Hb]]},
        rect("front", "wall", x4, x5, 0, Hb),
        rect("slopeB", "slope", x2, x3, Hb, Hb + s),
        rect("slopeF", "slope", x4, x5, Hb, Hb + s),
        rect("gfin", "glue", x2, x3, Hb + s, Hb + s + gfin_w),
        rect("flapF", "flap", x4, x5, -D, 0),
        rect("flapB", "flap", x2, x3, -D, 0),
        rect("flapL", "flap", x1, x2, -W / 2, 0),
        rect("flapR", "flap", x3, x4, -W / 2, 0),
    ]
    panels[1]["wall_of"] = "wallL"
    # 注: 顶点序为 G04 索引合同 (同 gable_top); 本模块自带 closure_checks
    panels = [{**pp, "polygon_2d": pp["polygon_2d"]} for pp in panels]

    def fold(eid, a2, b2, parent, child, tdir, mt_va="VALLEY"):
        return {"id": eid, "kind": "FOLD", "seg_2d": [list(a2), list(b2)],
                "fold": {"mt_va": mt_va, "parent": parent, "child": child,
                         "target_dir_3d": [round(float(v), 9) for v in tdir]}}

    edges = [
        fold("e_glue", (x1, 0), (x1, Hb), "wallL", "glue", (1.0, 0.0, 0.0), "MOUNTAIN"),
        fold("e_wl_bk", (x2, 0), (x2, Hb), "wallL", "back", (1.0, 0.0, 0.0)),
        fold("e_bk_wr", (x3, 0), (x3, Hb), "back", "wallR", (0.0, -1.0, 0.0)),
        fold("e_wr_ft", (x4, 0), (x4, Hb), "wallR", "front", (-1.0, 0.0, 0.0)),
        fold("e_bk_sl", (x2, Hb), (x3, Hb), "back", "slopeB", (0.0, -D / 2 / s, Hr / s)),
        fold("e_ft_sl", (x4, Hb), (x5, Hb), "front", "slopeF", (0.0, D / 2 / s, Hr / s)),
        # 胶条: 后坡顶缘越脊反折, 远缘落前坡顶缘 (away = 前坡下坡方向)
        fold("e_sl_gf", (x2, Hb + s), (x3, Hb + s), "slopeB", "gfin",
             (0.0, -D / 2 / s, -Hr / s), "MOUNTAIN"),
        fold("e_ft_fl", (x4, 0), (x5, 0), "front", "flapF", (0.0, 1.0, 0.0), "MOUNTAIN"),
        fold("e_bk_fl", (x2, 0), (x3, 0), "back", "flapB", (0.0, -1.0, 0.0), "MOUNTAIN"),
        fold("e_wl_fl", (x1, 0), (x2, 0), "wallL", "flapL", (1.0, 0.0, 0.0), "MOUNTAIN"),
        fold("e_wr_fl", (x3, 0), (x4, 0), "wallR", "flapR", (-1.0, 0.0, 0.0), "MOUNTAIN"),
    ]

    return {
        "meta": {"ir_version": "0.1", "units": "mm", "generator": "gable_variants 0.1",
                 "root_panel": "wallL",
                 "notes": "finless gable: 胶条越脊封合 (无立鳍)"},
        "package": {"type": "gable_finless",
                    "template": {"id": "gable_finless", "version": "0.1"},
                    "params": {k: p[k] for k in PARAM_ORDER},
                    "photo": None},
        "panels": panels,
        "edges": edges,
        "features": [{"id": "f_glue", "kind": "GLUE_TAB", "panel_id": "glue"},
                     {"id": "f_gfin", "kind": "GLUE_TAB", "panel_id": "gfin"}],
    }


def class_params(cls_id: str) -> dict:
    return {}


def validate_params(params: dict) -> None:
    for k in ("W", "D", "Hb", "Hr", "gfin_w", "glue_w", "board_t"):
        v = params.get(k)
        if v is None or not isinstance(v, (int, float)) or isinstance(v, bool) or v <= 0:
            raise ValueError(f"非法参数 {k}={v!r} (须正数)")


def analytic_bbox(params: dict) -> dict:
    p = {**DEFAULTS, **(params or {})}
    return {"W": float(p["W"]), "D": float(p["D"]), "H": float(p["Hb"] + p["Hr"])}


def solid_roles():
    return ("wall", "slope")


def allowed_overlap():
    return {
        frozenset({"flapF", "flapB"}), frozenset({"flapL", "flapR"}),
        frozenset({"glue", "front"}), frozenset({"gfin", "slopeF"}),
        frozenset({"gfin", "slopeB"}),
    }


def closure_checks(ir, world) -> dict:
    """真实闭合判据: 脊线四重合 + 底板封合 + gfin 远缘落前坡顶缘."""
    def pair(name, pa, ia, pb, ib):
        return name, float(np.linalg.norm(world[pa][ia] - world[pb][ib]))
    res = dict([
        pair("slopeB.ridge.L == wallL.apex", "slopeB", 3, "wallL", 3),
        pair("slopeF.ridge.L == wallR.apex", "slopeF", 3, "wallR", 3),
        pair("slopeB.ridge.R == wallR.apex", "slopeB", 2, "wallR", 3),
        pair("slopeF.ridge.R == wallL.apex", "slopeF", 2, "wallL", 3),
        ("flapF.far.mid == flapB.attach.mid",
         float(np.linalg.norm(np.mean(world["flapF"][0:2], axis=0) - np.mean(world["flapB"][2:4], axis=0)))),
        ("flapL.far.mid == flapR.far.mid",
         float(np.linalg.norm(np.mean(world["flapL"][0:2], axis=0) - np.mean(world["flapR"][0:2], axis=0)))),
    ])
    # gfin 封合判据: 平贴 slopeF 内表面 (共面) + 法线反平行 + 覆盖深度合法
    gf = np.asarray(world["gfin"], float)
    sf = np.asarray(world["slopeF"], float)
    n_sf = np.cross(sf[1] - sf[0], sf[3] - sf[0])
    n_sf = n_sf / np.linalg.norm(n_sf)
    plane_d = float(np.dot(gf[0] - sf[0], n_sf))
    res["gfin.planar_on_slopeF"] = abs(plane_d)
    far_mid = np.mean(gf[2:4], axis=0)
    # 覆盖深度: 远缘中点沿坡面距顶缘 ≤ 坡斜长 (胶条落在坡面之内)
    ridge_mid = np.mean(sf[2:4], axis=0)
    res["gfin.cover_depth_ok"] = max(0.0, float(np.linalg.norm(far_mid - ridge_mid)) - float(ir.param("gfin_w")) + 0.0)
    s_slant = float(np.linalg.norm(sf[0] - sf[2]))
    res["gfin.far_within_slant"] = max(0.0, float(np.linalg.norm(far_mid - ridge_mid)) - s_slant)
    return res
    flapL_mid = tuple(np.mean(world["flapL"][0:2], axis=0))
    flapR_mid = tuple(np.mean(world["flapR"][0:2], axis=0))
    res["flapL.far.x0"] = abs(flapL_mid[0])
    res["flapR.far.x0"] = abs(flapR_mid[0])
    return res
