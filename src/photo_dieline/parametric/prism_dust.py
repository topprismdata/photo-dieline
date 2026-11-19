"""prism_dust: 正 n 棱柱防尘翼插盖家族 (prism_dust_n{n}, n=4..12, 9 类).

拓扑: generic_prism tuck 变体 + 每条墙-墙转角缝一片**防尘翼** (dust flap):
     n 墙板链 + glue 搭接缝 + n 底板星形内折 + n 盖片内折 + n 防尘翼 = 4n+1 面板.
     防尘翼在每墙顶缘左右两端**共享** (真实插盖盒做法): 转角缝两侧墙共用一片,
     附着于一侧墙顶缘侧边竖折线, 先于盖片折入盒内, 折后平贴邻墙内面 (竖直翼面),
     盖片随后内折压于其上缘, 封住顶开口转角漏缝.

几何约定 (同 generic_prism): 根墙 w0 占 y=0 平面, net(x,y)→world(x,0,y);
     n 边形中心 (side/2, apothem), 顶点 v_k: φk = -π/2 - π/n + 2πk/n;
     edge_k = v_k→v_{k+1} 为 w_k 足迹, 外法线 outward_k, 切向 tangent_k = outward CCW90°.

net 布局 (密排墙带, 防尘翼嵌缺口不占带宽):
     [glue][w0][w1]...[w_{n-1}][d0]
     - w_i (i≤n-2) 右上角开 df×df 缺口, 容纳 d_{i+1} (附着 w_{i+1} 左缘顶段);
     - w_{n-1} 保持全宽矩形 (右上角不开缺口), 环缝翼 d0 附着其右缘顶段、
       折后贴 w0 内面 (与 glue 同面, allowed_overlap 契约对);
     - t_i (i≤n-2) 为梯形盖: 铰链=墙顶缘未缺口段 (side-df), 远缘全宽 side
       (远缘中点仍过中心轴 → 过轴判据与全宽盖一致); t_{n-1} 全宽矩形盖;
     - 折线段端点必须同为 parent/child 多边形顶点 (G03 顶点吸附),
       故缺口墙左缘、w_{n-1} 两竖缘插入共线顶点。

tdir 链式推理 (防尘翼): d_i 铰链 = w_i 左缘顶段竖线 (net 竖线 = 世界 ẑ),
     net 平铺时 away = -tangent_i (w_i 帧), 折到贴 w_{i-1} 内面 → tgt = -tangent_{i-1},
     即绕转角竖轴 inward 旋 2π/n; d0: away = +tangent_{n-1}, tgt = +tangent_0.

参数: n/side/h/tuck_depth/glue_w/board_t. tuck_depth=盖片折深 (G04 过轴判据
     要求 = apothem(n, side), class_params 按默认 side=60 逐类给出; 用户自定义
     side 时须同步给出一致的 tuck_depth, 否则 G04 如实 FAIL).
"""
from __future__ import annotations

import math

import numpy as np

from . import base as _base

DEFAULTS = {"n": 4, "side": 60.0, "h": 100.0, "tuck_depth": 30.0,
            "glue_w": 12.0, "board_t": 0.42}
PARAM_ORDER = ["n", "side", "h", "tuck_depth", "glue_w", "board_t"]

_APOTHEM_TOL = 0.2


def _apothem(n: int, side: float) -> float:
    return side / (2.0 * math.tan(math.pi / n))


def _circumradius(n: int, side: float) -> float:
    return side / (2.0 * math.sin(math.pi / n))


def _dust_depth(side: float) -> float:
    """防尘翼深: min(15, 0.3*side)."""
    return min(15.0, 0.3 * side)


def _classes():
    for n in range(4, 13):
        yield f"prism_dust_n{n}", n


def validate_params(params: dict) -> None:
    for k in ("side", "h", "tuck_depth", "glue_w", "board_t"):
        v = params.get(k)
        if v is None or not isinstance(v, (int, float)) or isinstance(v, bool) or v <= 0:
            raise ValueError(f"非法参数 {k}={v!r} (须正数)")
    n = params.get("n")
    if not isinstance(n, int) or isinstance(n, bool) or not (3 <= n <= 24):
        raise ValueError(f"非法参数 n={n!r} (须 3..24 整数)")


def class_params(cls_id: str) -> dict:
    """类ID → 参数覆盖: prism_dust_n7 → {"n":7, "tuck_depth":apothem(7,60)}."""
    n = int(cls_id.removeprefix("prism_dust_n"))
    return {"n": n,
            "tuck_depth": round(_apothem(n, float(DEFAULTS["side"])), 6)}


for _cid, _n in _classes():
    _base.register(_cid, "prism_dust")


def _outline(n: int, side: float):
    """正 n 边形足迹 (edge0 落 y=0, 中心 +y): 顶点/外法线/切向 (局部坐标)."""
    a = _apothem(n, side)
    ctr = np.array([side / 2.0, a])
    r = _circumradius(n, side)
    verts = [ctr + r * np.array([math.cos(-math.pi / 2 - math.pi / n + 2 * math.pi * k / n),
                                 math.sin(-math.pi / 2 - math.pi / n + 2 * math.pi * k / n)])
             for k in range(n)]
    edge_mid = [(verts[k] + verts[(k + 1) % n]) / 2.0 for k in range(n)]
    outward = [np.array([em[0] - ctr[0], em[1] - ctr[1]]) for em in edge_mid]
    outward = [o / np.linalg.norm(o) for o in outward]
    tangent = [np.array([-o[1], o[0]]) for o in outward]
    return ctr, outward, tangent


def build_ir(params: dict | None = None) -> dict:
    p = dict(DEFAULTS)
    p.update(params or {})
    n, side, h = int(p["n"]), float(p["side"]), float(p["h"])
    gw, td = float(p["glue_w"]), float(p["tuck_depth"])
    a = _apothem(n, side)      # 底板折深 = 内切半径 (星形过轴)
    df = _dust_depth(side)     # 防尘翼深 (缺口/翼尺寸同源)
    cls_id = f"prism_dust_n{n}"

    panels, edges = [], []
    X = [gw + i * side for i in range(n)]   # 墙左缘 net x (密排)
    xr = gw + n * side                      # 墙带右缘

    # 粘口 (全高矩形)
    panels.append({"id": "glue", "role": "glue",
                   "polygon_2d": [[0, 0], [gw, 0], [gw, h], [0, h]]})

    # 墙板: w_i (i≤n-2) 右上 df 缺口; i≥1 左缘共线顶点; w_{n-1} 全宽 + 两竖缘共线点
    for i in range(n):
        x = X[i]
        if i <= n - 2:
            poly = [[x, 0], [x + side, 0], [x + side, h - df],
                    [x + side - df, h - df], [x + side - df, h], [x, h]]
            if i >= 1:
                poly.append([x, h - df])   # e_d{i} 铰链下端吸附顶点
        else:
            poly = [[x, 0], [x + side, 0], [x + side, h - df],
                    [x + side, h], [x, h], [x, h - df]]
        panels.append({"id": f"w{i}", "role": "wall", "polygon_2d": poly})

    # 盖片: t_i (i≤n-2) 梯形 (铰链=顶缘未缺口段, 远缘全宽); t_{n-1} 全宽矩形
    for i in range(n):
        x = X[i]
        if i <= n - 2:
            poly = [[x, h], [x + side - df, h], [x + side, h + td], [x, h + td]]
        else:
            poly = [[x, h], [x + side, h], [x + side, h + td], [x, h + td]]
        panels.append({"id": f"t{i}", "role": "flap", "polygon_2d": poly})

    # 底板星形
    for i in range(n):
        x = X[i]
        panels.append({"id": f"b{i}", "role": "flap",
                       "polygon_2d": [[x, -a], [x + side, -a], [x + side, 0], [x, 0]]})

    # 防尘翼: d_i (i≥1) 附 w_i 左缘顶段, 折贴 w_{i-1} 内面; d0 附 w_{n-1} 右缘顶段, 折贴 w0
    for i in range(1, n):
        x = X[i]
        panels.append({"id": f"d{i}", "role": "flap",
                       "polygon_2d": [[x - df, h - df], [x, h - df], [x, h], [x - df, h]]})
    panels.append({"id": "d0", "role": "flap",
                   "polygon_2d": [[xr + df, h - df], [xr, h - df], [xr, h], [xr + df, h]]})

    def fold(eid, a2, b2, parent, child, tdir, mt_va="VALLEY"):
        edges.append({"id": eid, "kind": "FOLD", "seg_2d": [list(a2), list(b2)],
                      "fold": {"mt_va": mt_va, "parent": parent, "child": child,
                               "target_dir_3d": [round(float(v), 9) for v in tdir]}})

    _ctr, outward, tangent = _outline(n, side)

    # 墙链: w_i → w_{i+1}, 铰链 = 转角竖线未缺口段 (0..h-df); tdir = tangent_{i+1}
    for i in range(n - 1):
        x = X[i + 1]
        fold(f"e_w{i}", (x, 0), (x, h - df), f"w{i}", f"w{i + 1}",
             (*tangent[i + 1], 0.0))
    # glue → w0 内面
    fold("e_glue", (gw, 0), (gw, h), "w0", "glue", (1.0, 0.0, 0.0), "MOUNTAIN")
    # 防尘翼: 铰链竖线 = 墙顶缘端部侧边; tdir = -tangent_{i-1} (d0: +tangent_0)
    for i in range(1, n):
        x = X[i]
        fold(f"e_d{i}", (x, h - df), (x, h), f"w{i}", f"d{i}",
             (*(-tangent[i - 1]), 0.0))
    fold("e_d0", (xr, h - df), (xr, h), f"w{n - 1}", "d0",
         (*tangent[0], 0.0))
    # 盖片: 铰链 = 墙顶缘未缺口段; tdir = -outward_i (内折水平)
    for i in range(n - 1):
        x = X[i]
        fold(f"e_t{i}", (x, h), (x + side - df, h), f"w{i}", f"t{i}",
             (*(-outward[i]), 0.0))
    x = X[n - 1]
    fold(f"e_t{n - 1}", (x, h), (x + side, h), f"w{n - 1}", f"t{n - 1}",
         (*(-outward[n - 1]), 0.0))
    # 底板: 铰链 = 墙底缘全宽; tdir = -outward_i
    for i in range(n):
        x = X[i]
        fold(f"e_b{i}", (x, 0), (x + side, 0), f"w{i}", f"b{i}",
             (*(-outward[i]), 0.0))

    ir = {
        "meta": {"ir_version": "0.1", "units": "mm", "generator": "prism_dust",
                 "root_panel": "w0",
                 "root_frame": {"R": [[1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                                "off": [-gw, 0.0, 0.0]}},
        "package": {"type": cls_id,
                    "template": {"id": cls_id, "version": "0.1"},
                    "params": {k: p[k] for k in PARAM_ORDER if k in p},
                    "photo": None},
        "panels": panels,
        "edges": edges,
        "features": [{"id": "f_glue", "kind": "GLUE_TAB", "panel_id": "glue"}],
    }
    return ir


def analytic_bbox(params: dict) -> dict:
    """G05 期望: 墙板实体 n 边形足迹 bbox × h (缺口不改变外墙包络)."""
    p = {**DEFAULTS, **(params or {})}
    n, side, h = int(p["n"]), float(p["side"]), float(p["h"])
    ctr, _o, _t = _outline(n, side)
    r = _circumradius(n, side)
    vs = [ctr + r * np.array([math.cos(-math.pi / 2 - math.pi / n + 2 * math.pi * k / n),
                              math.sin(-math.pi / 2 - math.pi / n + 2 * math.pi * k / n)])
          for k in range(n)]
    xs = [v[0] for v in vs]
    ys = [v[1] for v in vs]
    return {"W": float(max(xs) - min(xs)), "D": float(max(ys) - min(ys)), "H": float(h)}


def solid_roles():
    return ("wall",)


def _dust_host(i: int) -> int:
    """d_i 平贴的宿主墙号: d_i (i≥1) 贴 w_{i-1}; d0 (环缝翼) 贴 w0."""
    return (i - 1) if i >= 1 else 0


def allowed_overlap():
    """真实工艺契约: 共面叠层全列.
    - 底星 z=0 全对 / 盖片 z=h 全对 / 底×盖 (层间接触契约);
    - d_i ↔ 宿主墙内面共面 (贴合); d0 ↔ glue (同贴 w0 内面, 环缝重叠);
    - 环闭合 w0↔w_{n-1} 共棱 + glue 端缘触末墙 + glue 贴 w0.
    """
    s = set()
    for n in range(4, 13):
        bs = [f"b{i}" for i in range(n)]
        ts = [f"t{i}" for i in range(n)]
        ds = [f"d{i}" for i in range(n)]
        for grp in (bs, ts, ds):
            for i in range(len(grp)):
                for j in range(i + 1, len(grp)):
                    s.add(frozenset({grp[i], grp[j]}))
        for b in bs:
            for t in ts:
                s.add(frozenset({b, t}))
        for i in range(n):
            s.add(frozenset({f"d{i}", f"w{_dust_host(i)}"}))
        s.add(frozenset({"d0", "glue"}))
        s.add(frozenset({"w0", f"w{n - 1}"}))
        s.add(frozenset({"glue", f"w{n - 1}"}))
        s.add(frozenset({"glue", "w0"}))
    return s


def closure_checks(ir, world) -> dict:
    """G04 闭合残差 (远缘中点判据):
    - b{i}.far_to_axis: 底星远缘中点 → 中心轴 (z=0);
    - t{i}.far_to_axis: 盖片远缘中点 → 顶中心轴点 (含 z);
    - d{i}.host_planar: 防尘翼远缘中点 → 宿主墙平面距离 (垂直度证据);
    - d{i}.host_inspan: 远缘中点沿宿主墙展向距转角 = df (向内贴靠证据,
      与 planar 联合唯一锁定折叠: 反向外翻/垂直鳍/平铺均爆残差);
    - glue.planar_y0: glue 远缘贴 w0 平面.
    """
    n = int(ir.param("n"))
    side = float(ir.param("side"))
    h = float(ir.param("h"))
    df = _dust_depth(side)
    ctr = np.array([side / 2.0, _apothem(n, side)])
    res: dict[str, float] = {}

    for i in range(n):
        fm = np.mean(world[f"b{i}"][0:2], axis=0)
        res[f"b{i}.far_to_axis"] = float(abs(np.linalg.norm(fm[:2] - ctr[:2])))
    top = np.array([ctr[0], ctr[1], h])
    for i in range(n):
        fm = np.mean(world[f"t{i}"][2:4], axis=0)
        res[f"t{i}.far_to_axis"] = float(np.linalg.norm(fm - top))
    for i in range(n):
        host = world[f"w{_dust_host(i)}"]
        p0, p1 = np.asarray(host[0], float), np.asarray(host[1], float)
        span = p1 - p0
        span = span / np.linalg.norm(span)
        nrm = np.cross(p1 - p0, np.asarray(host[3], float) - p0)
        nrm = nrm / np.linalg.norm(nrm)
        fl = world[f"d{i}"]
        fm = np.mean([np.asarray(fl[0], float), np.asarray(fl[3], float)], axis=0)
        res[f"d{i}.host_planar"] = float(abs(np.dot(fm - p0, nrm)))
        anchor = p1 if i >= 1 else p0   # d_i 转角 = 宿主远端角 v_i (展向负向); d0 = v0
        target = -df if i >= 1 else df  # 由转角向宿主跨内延伸 → 展向投影 ±df
        res[f"d{i}.host_inspan"] = float(abs(np.dot(fm - anchor, span) - target))
    gm = np.mean(world["glue"][0:2], axis=0)
    res["glue.planar_y0"] = float(abs(gm[1]))
    return res
