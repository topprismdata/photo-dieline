"""rsc_family: FEFCO 0201 瓦楞开槽箱家族 (RSC/HSC/CSS/lock 底).

类ID:
  rsc_rsc  标准开槽箱: 4 墙 + 上下各 2 大折翼(从 W 墙, 深 flap_ratio*D) + 2 小折翼(从 D 墙, 深 flap_ratio*W) + glue 接缝
  rsc_hsc  半槽 (HSC): 只有底折翼, 顶全开
  rsc_css  中心特封 (CSSA): 全部折翼等宽 flap_ratio*D, 大折翼对远缘中心相抵 (class_params 锁 flap_ratio=0.5)
  rsc_lock 锁底: 顶同 RSC, 底大折翼带锁合 — 前翼带插舌, 后翼开插槽, 插舌入槽

几何约定: 根墙 w0 占 y=0 平面, net(x,y)→world(x-?, 0, y) 由 root_frame 映射;
墙环 w0(front,y=0)→w1(right,x=W)→w2(back,y=D)→w3(left,x=0) 逆时针闭合,
w3 自由缘回到 w0 左缘 (环闭合缝)。折翼全部折到水平面 (顶 z=H / 底 z=0) 内折。
lock 底: b0 深 dm+tw 远缘中央带矩形插舌 (W/2±sl/2); b2 深 D-dm 远缘中央开同宽
插槽深 tw — 折平后插舌恰好填入插槽 (tip 边 == slot 底边, 自适应任意 flap_ratio)。

模块内参数 variant (0=rsc,1=hsc,2=css,3=lock) 是类身份路由, 非用户尺寸,
不进 PARAM_ORDER / package.params (schema additionalProperties=false)。
"""
from __future__ import annotations

import numpy as np

from . import base as _base

DEFAULTS = {"W": 160.0, "D": 100.0, "H": 80.0, "flap_ratio": 0.5,
            "glue_w": 12.0, "board_t": 0.45, "variant": 0}
PARAM_ORDER = ["W", "D", "H", "flap_ratio", "glue_w", "board_t"]

_CLS_IDS = ("rsc_rsc", "rsc_hsc", "rsc_css", "rsc_lock")

for _cid in _CLS_IDS:
    _base.register(_cid, "rsc_family")


def class_params(cls_id: str) -> dict:
    """类ID → 参数覆盖: css/lock 的大折翼必须到中线 (锁合/中心相抵), 锁 flap_ratio=0.5."""
    if cls_id == "rsc_css":
        return {"variant": 2, "flap_ratio": 0.5}
    if cls_id == "rsc_lock":
        return {"variant": 3, "flap_ratio": 0.5}
    if cls_id == "rsc_hsc":
        return {"variant": 1}
    return {"variant": 0}


def validate_params(params: dict) -> None:
    """参数语义: 正尺寸, flap_ratio∈(0,1], 粘口须窄于最短墙 (否则粘缝超端墙)."""
    for k in ("W", "D", "H", "glue_w", "board_t"):
        v = params.get(k)
        if v is None or not isinstance(v, (int, float)) or isinstance(v, bool) or v <= 0:
            raise ValueError(f"非法参数 {k}={v!r} (须正数)")
    r = params.get("flap_ratio")
    if not isinstance(r, (int, float)) or isinstance(r, bool) or not (0.0 < float(r) <= 1.0):
        raise ValueError(f"非法参数 flap_ratio={r!r} (须 (0,1])")
    if float(params["glue_w"]) >= min(float(params["W"]), float(params["D"])):
        raise ValueError(f"粘口 glue_w={params['glue_w']} 须窄于最短墙 min(W,D)={min(params['W'], params['D'])}")


def _rect(pid: str, role: str, xa: float, xb: float, ya: float, yb: float) -> dict:
    """矩形板: 顶点序 [[xa,ya],[xb,ya],[xb,yb],[xa,yb]] (索引契约见 closure_checks)."""
    return {"id": pid, "role": role,
            "polygon_2d": [[xa, ya], [xb, ya], [xb, yb], [xa, yb]]}


def _lock_dims(dm: float, W: float) -> tuple[float, float]:
    """插舌长 tw / 插槽宽 sl (几何自适应: tw<dm, sl<W)."""
    tw = min(10.0, 0.25 * dm)
    sl = min(24.0, 0.25 * W)
    return tw, sl


def build_ir(params: dict | None = None) -> dict:
    p = {**DEFAULTS, **(params or {})}
    variant = int(p.get("variant", 0))
    if variant not in (0, 1, 2, 3):
        raise ValueError(f"非法 variant={variant!r} (须 0..3)")
    cls_id = _CLS_IDS[variant]
    W, D, H = float(p["W"]), float(p["D"]), float(p["H"])
    r, gw = float(p["flap_ratio"]), float(p["glue_w"])
    has_top = variant in (0, 2, 3)   # hsc 半槽: 顶全开
    css = variant == 2
    lock = variant == 3

    dm = r * D                       # 大折翼折入深 (w0/w2 墙)
    dn = (r * D) if css else (r * W)  # 小折翼折入深 (w1/w3 墙; css 全翼等宽 D 比)
    dm2 = (D - dm) if lock else dm   # lock 后底翼深 (自适应使插槽底 == 插舌尖)
    tw, sl = _lock_dims(dm, W) if lock else (0.0, 0.0)
    hs = sl / 2.0

    x1, x2, x3, x4, x5 = gw, gw + W, gw + W + D, gw + 2 * W + D, gw + 2 * W + 2 * D
    xc0, xc2 = gw + W / 2.0, x3 + W / 2.0  # b0/b2 墙宽中线 (net x)

    panels = [_rect("glue", "glue", 0.0, gw, 0.0, H),
              _rect("w0", "wall", x1, x2, 0.0, H),
              _rect("w1", "wall", x2, x3, 0.0, H),
              _rect("w2", "wall", x3, x4, 0.0, H),
              _rect("w3", "wall", x4, x5, 0.0, H)]

    # 顶折翼 (rsc/css/lock): 大翼从 w0/w2 全宽折出, 小翼从 w1/w3
    if has_top:
        panels += [_rect("t0", "flap", x1, x2, H, H + dm),
                   _rect("t1", "flap", x2, x3, H, H + dn),
                   _rect("t2", "flap", x3, x4, H, H + dm),
                   _rect("t3", "flap", x4, x5, H, H + dn)]

    # 底折翼: b1/b3 小翼; lock 时 b0 带插舌 / b2 开插槽 (远缘中央缺口)
    if lock:
        panels += [
            {"id": "b0", "role": "flap", "polygon_2d": [
                [x1, 0], [x2, 0], [x2, -dm],
                [xc0 + hs, -dm], [xc0 + hs, -dm - tw],
                [xc0 - hs, -dm - tw], [xc0 - hs, -dm], [x1, -dm]]},
            _rect("b1", "flap", x2, x3, -dn, 0.0),
            {"id": "b2", "role": "flap", "polygon_2d": [
                [x3, 0], [x4, 0], [x4, -dm2],
                [xc2 + hs, -dm2], [xc2 + hs, -dm2 + tw],
                [xc2 - hs, -dm2 + tw], [xc2 - hs, -dm2], [x3, -dm2]]},
            _rect("b3", "flap", x4, x5, -dn, 0.0),
        ]
    else:
        panels += [_rect("b0", "flap", x1, x2, -dm, 0.0),
                   _rect("b1", "flap", x2, x3, -dn, 0.0),
                   _rect("b2", "flap", x3, x4, -dm, 0.0),
                   _rect("b3", "flap", x4, x5, -dn, 0.0)]

    def fold(eid, a2, b2, parent, child, mt_va, tdir):
        return {"id": eid, "kind": "FOLD", "seg_2d": [list(a2), list(b2)],
                "fold": {"mt_va": mt_va, "parent": parent, "child": child,
                         "target_dir_3d": [float(v) for v in tdir]}}

    edges = [
        # 墙环: w0(y=0)→w1(x=W)→w2(y=D)→w3(x=0), 自由缘回 w0 左缘
        fold("e_glue", (gw, 0), (gw, H), "w0", "glue", "MOUNTAIN", (0.0, 1.0, 0.0)),
        fold("e_w01", (x2, 0), (x2, H), "w0", "w1", "VALLEY", (0.0, 1.0, 0.0)),
        fold("e_w12", (x3, 0), (x3, H), "w1", "w2", "VALLEY", (-1.0, 0.0, 0.0)),
        fold("e_w23", (x4, 0), (x4, H), "w2", "w3", "VALLEY", (0.0, -1.0, 0.0)),
        # 底折翼: 全部内折至 z=0 水平面 (lock: 含插舌翼/插槽翼)
        fold("e_b0", (x1, 0), (x2, 0), "w0", "b0", "MOUNTAIN", (0.0, 1.0, 0.0)),
        fold("e_b1", (x2, 0), (x3, 0), "w1", "b1", "MOUNTAIN", (-1.0, 0.0, 0.0)),
        fold("e_b2", (x3, 0), (x4, 0), "w2", "b2", "MOUNTAIN", (0.0, -1.0, 0.0)),
        fold("e_b3", (x4, 0), (x5, 0), "w3", "b3", "MOUNTAIN", (1.0, 0.0, 0.0)),
    ]
    if has_top:
        edges += [
            fold("e_t0", (x1, H), (x2, H), "w0", "t0", "MOUNTAIN", (0.0, 1.0, 0.0)),
            fold("e_t1", (x2, H), (x3, H), "w1", "t1", "MOUNTAIN", (-1.0, 0.0, 0.0)),
            fold("e_t2", (x3, H), (x4, H), "w2", "t2", "MOUNTAIN", (0.0, -1.0, 0.0)),
            fold("e_t3", (x4, H), (x5, H), "w3", "t3", "MOUNTAIN", (1.0, 0.0, 0.0)),
        ]

    ir = {
        "meta": {"ir_version": "0.1", "units": "mm",
                 "generator": "photo_dieline.parametric.rsc_family 0.1",
                 "root_panel": "w0",
                 "root_frame": {"R": [[1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                                "off": [-gw, 0.0, 0.0]}},
        "package": {"type": cls_id,
                    "template": {"id": cls_id, "version": "0.1"},
                    "params": {k: float(p[k]) for k in PARAM_ORDER},
                    "photo": None},
        "panels": panels,
        "edges": edges,
        "features": [{"id": "f_glue", "kind": "GLUE_TAB", "panel_id": "glue"}],
    }
    return ir


def analytic_bbox(params: dict) -> dict:
    """G05 期望: 墙环实体 (wall 角色) 封闭盒 W×D×H."""
    p = {**DEFAULTS, **(params or {})}
    return {"W": float(p["W"]), "D": float(p["D"]), "H": float(p["H"])}


def solid_roles():
    return ("wall",)


def allowed_overlap():
    """G06 允许叠层 (真实工艺契约):
    同面折翼全对 (顶 6 对 / 底 6 对: 对翼中线相抵或大小翼角部叠层)
    + glue 端缘贴末墙 w3 + 环闭合末墙 w3↔首墙 w0 工艺粘缝."""
    s = set()
    for pre in ("t", "b"):
        f = [f"{pre}{i}" for i in range(4)]
        for i in range(4):
            for j in range(i + 1, 4):
                s.add(frozenset({f[i], f[j]}))
    s.add(frozenset({"glue", "w3"}))
    s.add(frozenset({"w0", "w3"}))
    return s


def closure_checks(ir, world) -> dict:
    """G04 折叠闭合残差 (全部为跨链远缘几何证据, 非构造恒等):

    ring.w3_to_w0   环闭合: w3 自由缘经 3 次折返回 w0 左缘 (墙链闭合)
    glue.seat/far   粘缝: glue 远缘贴 w3 外面 (x=0 平面) 且距铰链 gw
    *_z0 / *_zH     折翼远缘落底/顶平面 (经墙链定位, 验墙环立姿正确)
    *_level         对翼远缘同高 (RSC/HSC/lock 平封语义)
    css.*_meet      CSS 大翼对远缘重合于中心线 (D/2 相抵, 最强闭合)
    lock.*          插舌尖边 == 插槽底边 (入槽到位) + 插槽居中 + 插舌落平面

    面板顶点索引契约: _rect 环 [[xa,ya],[xb,ya],[xb,yb],[xa,yb]];
    b0(lock) 8 顶点: far 角=2,7 / 舌尖=4,5; b2(lock): far 角=2,7 / 槽底=4,5.
    """
    cls_id = ir.package["template"]["id"]
    variant = _CLS_IDS.index(cls_id)
    W, D, H = ir.param("W"), ir.param("D"), ir.param("H")
    gw = ir.param("glue_w")
    has_top, css, lock = variant in (0, 2, 3), variant == 2, variant == 3

    def fm(pid, i, j) -> np.ndarray:
        return (np.asarray(world[pid][i], float) + np.asarray(world[pid][j], float)) / 2.0

    def d(a, b) -> float:
        return float(np.linalg.norm(np.asarray(a, float) - np.asarray(b, float)))

    res: dict[str, float] = {}
    # 墙环闭合 + 粘缝贴末墙外面
    res["ring.w3_to_w0"] = d(fm("w3", 1, 2), fm("w0", 0, 3))
    g = fm("glue", 0, 3)
    res["glue.seat_x0"] = abs(float(g[0]))
    res["glue.far_y"] = abs(float(g[1]) - gw)

    # 底折翼 (far 中线: lock 翼用不含舌/槽的 far 角 2,7)
    b0f = fm("b0", 2, 7) if lock else fm("b0", 0, 1)
    b2f = fm("b2", 2, 7) if lock else fm("b2", 0, 1)
    res["b_major.z0"] = max(abs(float(b0f[2])), abs(float(b2f[2])))
    res["b_major.level"] = abs(float(b0f[2]) - float(b2f[2]))
    b1f, b3f = fm("b1", 0, 1), fm("b3", 0, 1)
    res["b_minor.z0"] = max(abs(float(b1f[2])), abs(float(b3f[2])))
    res["b_minor.level"] = abs(float(b1f[2]) - float(b3f[2]))
    if css:
        res["css.b_major_meet"] = d(b0f, b2f)  # 两翼远缘重合于中心线 y=D/2
    if lock:
        tip, slot = fm("b0", 4, 5), fm("b2", 4, 5)
        res["lock.tongue_in_slot"] = d(tip, slot)      # 舌尖边 == 槽底边 (入槽)
        res["lock.slot_centered"] = abs(float(slot[0]) - W / 2.0)
        res["lock.tongue_z0"] = abs(float(tip[2]))

    # 顶折翼 (hsc 无)
    if has_top:
        t0f, t2f = fm("t0", 2, 3), fm("t2", 2, 3)
        res["t_major.zH"] = max(abs(float(t0f[2]) - H), abs(float(t2f[2]) - H))
        res["t_major.level"] = abs(float(t0f[2]) - float(t2f[2]))
        t1f, t3f = fm("t1", 2, 3), fm("t3", 2, 3)
        res["t_minor.zH"] = max(abs(float(t1f[2]) - H), abs(float(t3f[2]) - H))
        res["t_minor.level"] = abs(float(t1f[2]) - float(t3f[2]))
        if css:
            res["css.t_major_meet"] = d(t0f, t2f)
    return res
