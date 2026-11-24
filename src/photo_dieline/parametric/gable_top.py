"""gable_top 模板 V0.1 — 参数 → Geometry IR (展开网 + 折线图 + 解析封闭盒).

结构来源(知识级参照, 代码独立实现): 利乐式屋顶包(gable-top)公开几何规则;
母仓 R40 定案拓扑: 低坡(Hr) + 过脊立鳍(Ef, 双层鳍顶缘距 fin_gap).

展开布局(2D, mm, y 向上, 原点=网左下):
    [glue][wallL+gable三角][back][wallR+gable三角][front]
    back 上方: slopeB(W×s) → 上缘接 finB(W×Ef)
    front 上方: slopeF(W×s) → 上缘接 finF(W×Ef)
    墙底接 4 底封板(front/back 全宽翻板, wallL/wallR 侧插板)

封闭盒(解析): 前墙 y=-D/2 面外向 -y; 背墙 +D/2; wallL x=-W/2; wallR +W/2;
脊线沿 x 轴 y=0, z=Hb+Hr; 鳍自脊上立向对面倾 fin_gap/2。

假设(模板契约 ASSUMED): 板厚补偿 P1 不做(几何取名义尺寸); 侧插板与前后翻板
的叠层接触为 ALLOWED_OVERLAP(真实工艺插板外层)。
"""
from __future__ import annotations

import math

PARAM_ORDER = ["W", "D", "Hb", "Hr", "Ef", "fin_gap_mm", "glue_w", "board_t"]

from . import base as _base
_base.register("gable_top", "gable_top")


def class_params(cls_id: str) -> dict:
    return {}


def validate_params(params: dict) -> None:
    """参数语义: 正尺寸; n/枚举由模板自检."""
    for k in ("W", "D", "Hb", "Hr", "Ef", "fin_gap_mm", "glue_w", "board_t"):
        v = params.get(k)
        # isfinite: nan/inf 能同时躲过 v<=0 与 isinstance 检查, 会在几何内核深处才崩 (R3 §4.4)
        if v is None or not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) or v <= 0:
            raise ValueError(f"非法参数 {k}={v!r} (须正的有限数)")


if __name__ != "__main__":
    pass


def analytic_bbox(params: dict) -> dict:
    """G05 期望 bbox {W,D,H} (统一契约; 复用 analytic_box)."""
    b = analytic_box(params)["bbox"]
    return {"W": float(b["W"]), "D": float(b["D"]), "H": float(b["H"])}


def allowed_overlap():
    """G06 允许叠层 (真实工艺): 前后/左右底板互叠, 粘口贴前墙, 过脊鳍对叠."""
    return {
        frozenset({"flapF", "flapB"}), frozenset({"flapL", "flapR"}),
        frozenset({"glue", "front"}), frozenset({"finB", "finF"}),
    }


def solid_roles():
    return ("wall", "slope")


def _vertex_at(ir, pid, xy):
    """面板在展开图坐标 xy 处的顶点下标 — 按坐标而不是按下标取点:
    使用者插入共线分点或轮换起始顶点时, 判据不受影响 (GPT R2 正向挑战集 POS-04/05)。"""
    import numpy as np
    pts = np.asarray(ir.panel(pid)["polygon_2d"], float)
    d = np.linalg.norm(pts - np.asarray(xy, float), axis=1)
    i = int(d.argmin())
    if d[i] > 1e-6:
        raise ValueError(f"{pid} 没有坐标为 {tuple(xy)} 的顶点 (最近 {d[i]:.3g}mm)")
    return i


def closure_checks(ir, world):
    """G04 折叠闭合残差。每条判据须对至少一种已知折叠破坏敏感
    (qa.pipeline.closure_sensitivity 逐条折线扰动回放); 顶点一律按展开图坐标定位
    (对共线分点、起始顶点轮换、整体平移不变):

    - 脊线端点落在山墙尖; 前后底板远缘互达对侧墙底; 左右底板远缘在中线汇合
    - 粘口远缘落在前脸闭合缝外表面、内移 glue_w (粘口折向盒外或未折即偏离)
    - 过脊双鳍顶缘中点距 = fin_gap_mm (超域时倾角钳位 → 2*Ef)

    原 "wallL.top.B == slopeB.bottom.L" 两条比较的是铰链上的点, 残差恒为 0, 已删。
    """
    import numpy as np
    p = ir.package["params"]
    W, D, Hb, Hr, Ef, gw = (float(p[k]) for k in ("W", "D", "Hb", "Hr", "Ef", "glue_w"))
    gap = float(p["fin_gap_mm"])
    s = slant(D, Hr)
    x1, x2, x3, x4, x5 = gw, gw + D, gw + D + W, gw + D + W + D, gw + D + W + D + W
    glue_pts = np.asarray(ir.panel("glue")["polygon_2d"], float)
    ox, oy = float(glue_pts[:, 0].min()), float(glue_pts[:, 1].min())   # 以粘口左下角为原点 → 整体平移不变

    def P(pid, xy):
        return np.asarray(world[pid][_vertex_at(ir, pid, (xy[0] + ox, xy[1] + oy))], float)

    def mid(pid, a, b):
        return (P(pid, a) + P(pid, b)) / 2.0

    def pair(name, a, b):
        return name, float(np.linalg.norm(a - b))

    apex_l, apex_r = (x2 - D / 2, Hb + Hr), (x4 - D / 2, Hb + Hr)
    top = Hb + s + Ef
    flap_l_far = mid("flapL", (x1, -W / 2), (x2, -W / 2))
    flap_r_far = mid("flapR", (x3, -W / 2), (x4, -W / 2))
    off = np.array([gw, 0.0, 0.0])
    checks = [
        pair("slopeB.ridge.L == wallL.apex", P("slopeB", (x2, Hb + s)), P("wallL", apex_l)),
        pair("slopeF.ridge.L == wallR.apex", P("slopeF", (x4, Hb + s)), P("wallR", apex_r)),
        pair("slopeB.ridge.R == wallR.apex", P("slopeB", (x3, Hb + s)), P("wallR", apex_r)),
        pair("slopeF.ridge.R == wallL.apex", P("slopeF", (x5, Hb + s)), P("wallL", apex_l)),
        ("glue.far.on_front",
         float(np.linalg.norm((P("glue", (0.0, 0.0)) - P("front", (x5, 0.0))) - off)
               + np.linalg.norm((P("glue", (0.0, Hb)) - P("front", (x5, Hb))) - off))),
        ("flapF.far.mid == flapB.attach.mid",
         float(np.linalg.norm(mid("flapF", (x4, -D), (x5, -D)) - mid("flapB", (x2, 0.0), (x3, 0.0))))),
        ("flapB.far.mid == flapF.attach.mid",
         float(np.linalg.norm(mid("flapB", (x2, -D), (x3, -D)) - mid("flapF", (x4, 0.0), (x5, 0.0))))),
        ("flapL.far.mid == flapR.far.mid", float(np.linalg.norm(flap_l_far - flap_r_far))),
        ("fin.top_gap",
         abs(float(np.linalg.norm(mid("finB", (x2, top), (x3, top)) - mid("finF", (x4, top), (x5, top))))
             - min(gap, 2.0 * Ef))),
    ]
    res = dict(checks)
    res["flapL.far.x0"] = abs(float(flap_l_far[0]))
    res["flapR.far.x0"] = abs(float(flap_r_far[0]))
    return res
DEFAULTS = {"W": 45.0, "D": 45.0, "Hb": 100.0, "Hr": 12.0,
            "Ef": 14.0, "fin_gap_mm": 3.0, "glue_w": 12.0, "board_t": 0.45}

# mt_va_reference: 折线 MOUNTAIN/VALLEY 的观察面约定 = 父面板 polygon_2d 逆时针法线一侧
# (qa.pipeline.fold_semantics 据此核对; 本模板墙体该侧为盒内面)
TEMPLATE = {"id": "gable_top", "version": "0.1", "mt_va_reference": "polygon_2d_ccw"}


def slant(D: float, Hr: float) -> float:
    """坡面板斜高 s = sqrt((D/2)^2 + Hr^2)."""
    return math.hypot(D / 2.0, Hr)


SLOPE_ANGLE_MIN_DEG = 5.0   # 屋脊坡角 atan(2*Hr/D) 下限, 依据见 param_domain_violations


def param_domain_violations(params: dict) -> list[str]:
    """模板适用域 (G02 核对)。域外不是"算错了", 而是本模板的假设不成立 — 不得出 VALIDATED。
    - 各参数须为正的有限数 (与 validate_params 同口径, 入口已拒; 这里兜底);
    - fin_gap_mm < 2*Ef: 鳍倾角 lean = asin(fin_gap_mm / (2*Ef)) 须 < 90° (等于 90° 时鳍高为 0);
    - 屋脊坡角 atan(2*Hr/D) >= SLOPE_ANGLE_MIN_DEG: 再低时屋脊抬高量落在闭合容差与关键点噪声的量级内,
      山墙三角退化, 与平顶盒不可区分 — "屋顶包"模板不描述这种形体。"""
    out = []
    for k in PARAM_ORDER:
        v = params.get(k)
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) or v <= 0.0:
            out.append(f"{k}={v!r} 须为正的有限数")
    if out:
        return out
    gap, Ef, D, Hr = (float(params[k]) for k in ("fin_gap_mm", "Ef", "D", "Hr"))
    if gap >= 2.0 * Ef:
        out.append(f"fin_gap_mm={gap:g} >= 2*Ef={2.0 * Ef:g} (鳍倾角 >= 90°, 鳍高为 0)")
    slope = math.degrees(math.atan2(2.0 * Hr, D))
    if slope < SLOPE_ANGLE_MIN_DEG:
        out.append(f"屋脊坡角 {slope:.2f}° < {SLOPE_ANGLE_MIN_DEG:g}° (Hr={Hr:g}, D={D:g}: 山墙三角退化, 与平顶盒不可区分)")
    return out


def build_ir(params: dict | None = None) -> dict:
    p = dict(DEFAULTS)
    p.update(params or {})
    W, D, Hb, Hr = p["W"], p["D"], p["Hb"], p["Hr"]
    Ef, gap, gw = p["Ef"], p["fin_gap_mm"], p["glue_w"]
    s = slant(D, Hr)

    x0 = 0.0          # glue 左缘
    x1 = gw           # wallL 左缘
    x2 = x1 + D       # wallL|back
    x3 = x2 + W       # back|wallR
    x4 = x3 + D       # wallR|front
    x5 = x4 + W       # front 右缘(闭合缝)

    R = math.radians(90.0)  # 统一 90° 墙体折

    def rect(pid, role, xa, xb, ya, yb):
        return {"id": pid, "role": role,
                "polygon_2d": [[xa, ya], [xb, ya], [xb, yb], [xa, yb]]}

    def fold(eid, a2, b2, parent, child, mt_va="VALLEY", angle=None, tdir=None):
        f = {"id": eid, "kind": "FOLD", "seg_2d": [list(a2), list(b2)],
             "fold": {"mt_va": mt_va, "parent": parent, "child": child}}
        if angle is not None:
            f["fold"]["target_angle_deg"] = angle
        if tdir is not None:
            f["fold"]["target_dir_3d"] = list(tdir)
        return f

    panels = [
        # --- 墙体带 (含山墙三角: 墙+三角同一板) ---
        rect("glue", "glue", x0, x1, 0, Hb),
        {"id": "wallL", "role": "wall", "polygon_2d": [
            [x1, 0], [x2, 0], [x2, Hb], [x2 - D / 2, Hb + Hr], [x1, Hb]]},
        rect("back", "wall", x2, x3, 0, Hb),
        {"id": "wallR", "role": "wall", "polygon_2d": [
            [x3, 0], [x4, 0], [x4, Hb], [x4 - D / 2, Hb + Hr], [x3, Hb]]},
        rect("front", "wall", x4, x5, 0, Hb),
        # --- 屋顶坡 + 过脊鳍 ---
        rect("slopeB", "slope", x2, x3, Hb, Hb + s),
        rect("finB", "fin", x2, x3, Hb + s, Hb + s + Ef),
        rect("slopeF", "slope", x4, x5, Hb, Hb + s),
        rect("finF", "fin", x4, x5, Hb + s, Hb + s + Ef),
        # --- 底封板 ---
        rect("flapF", "flap", x4, x5, -D, 0),
        rect("flapB", "flap", x2, x3, -D, 0),
        rect("flapL", "flap", x1, x2, -W / 2, 0),
        rect("flapR", "flap", x3, x4, -W / 2, 0),
    ]
    # 山墙三角归属(拓扑标注): wallL/wallR 顶三角即 gable_end 区, 同板无折线
    panels[1]["wall_of"] = "wallL"
    # 注: polygon_2d 顶点序是 M1 冻结合同 (G04 索引配对依赖), 不改;
    # 法线外向归一由渲染器侧处理 (twin.py)

    lean = math.asin(min(1.0, (gap / 2) / Ef)) if Ef > 0 else 0.0
    # 全部折线显式 target_dir_3d (模板解析已知封闭盒: wallL x=-W/2 平面 y 0..D;
    # back y=D; wallR x=+W/2; front y=0; 脊 y=D/2, z=Hb+Hr; 底 z=0)
    edges = [
        fold("e_glue", (x1, 0), (x1, Hb), "wallL", "glue", "VALLEY",
             tdir=(1.0, 0.0, 0.0)),
        fold("e_wl_bk", (x2, 0), (x2, Hb), "wallL", "back", "VALLEY",
             tdir=(1.0, 0.0, 0.0)),
        fold("e_bk_wr", (x3, 0), (x3, Hb), "back", "wallR", "VALLEY",
             tdir=(0.0, -1.0, 0.0)),
        fold("e_wr_ft", (x4, 0), (x4, Hb), "wallR", "front", "VALLEY",
             tdir=(-1.0, 0.0, 0.0)),
        # 坡面: 自墙顶缘向脊 (y=D/2) 上倾
        fold("e_bk_sl", (x2, Hb), (x3, Hb), "back", "slopeB", "VALLEY",
             tdir=(0.0, -D / 2 / s, Hr / s)),
        fold("e_ft_sl", (x4, Hb), (x5, Hb), "front", "slopeF", "VALLEY",
             tdir=(0.0, +D / 2 / s, Hr / s)),
        # 过脊鳍: 双层顶缘距 gap → 倾角 lean = asin(gap/2 / Ef)
        fold("e_sl_fb", (x2, Hb + s), (x3, Hb + s), "slopeB", "finB", "MOUNTAIN",
             tdir=(0.0, -math.sin(lean), math.cos(lean))),
        fold("e_sl_ff", (x4, Hb + s), (x5, Hb + s), "slopeF", "finF", "MOUNTAIN",
             tdir=(0.0, math.sin(lean), math.cos(lean))),
        # 底封板: 全宽前后板内折成底 (水平 z=0 平面), 侧插板内折至中线。
        # 粘口与底板都朝 polygon_2d 正面一侧折 → 以该面为观察面是 VALLEY (原先误标 MOUNTAIN)
        fold("e_ft_fl", (x4, 0), (x5, 0), "front", "flapF", "VALLEY",
             tdir=(0.0, 1.0, 0.0)),
        fold("e_bk_fl", (x2, 0), (x3, 0), "back", "flapB", "VALLEY",
             tdir=(0.0, -1.0, 0.0)),
        fold("e_wl_fl", (x1, 0), (x2, 0), "wallL", "flapL", "VALLEY",
             tdir=(1.0, 0.0, 0.0)),
        fold("e_wr_fl", (x3, 0), (x4, 0), "wallR", "flapR", "VALLEY",
             tdir=(-1.0, 0.0, 0.0)),
    ]

    features = [
        {"id": "f_glue", "kind": "GLUE_TAB", "panel_id": "glue"},
        {"id": "f_bleed", "kind": "BLEED", "offset_mm": 3.0},
        {"id": "f_check", "kind": "CHECK_BAR", "length_mm": 50.0},
        {"id": "f_reg", "kind": "REGISTRATION"},
    ]

    ir = {
        "meta": {
            "ir_version": "0.1", "units": "mm",
            "generator": "photo_dieline.parametric.gable_top 0.1",
            "notes": "M1 golden sample; 板厚补偿 P1; 鳍双层顶缘距=fin_gap_mm; "
                     "mt_va 观察面 = polygon_2d 正面 (本模板墙体该侧为盒内面)",
        },
        "package": {
            "type": "gable_top",
            "params": {k: float(p[k]) for k in PARAM_ORDER},
            "template": dict(TEMPLATE),
            "photo": None,  # build() 注入 (批量=null)
        },
        "panels": panels,
        "edges": edges,
        "features": features,
    }
    # 供折叠/导出使用的派生量(不进 schema 校验面, 由 ir.raw 透传)
    ir["_derived"] = {
        "slant": s,
        "x": [x0, x1, x2, x3, x4, x5],
        "fin_lean_deg": math.degrees(lean),
        "fin_top_gap": 2 * Ef * math.sin(lean),
    }
    return ir


def analytic_box(p: dict) -> dict:
    """解析封闭盒尺寸与关键闭合点 (QA golden 基准). 盒坐标: x 0..W 居中±W/2,
    wallL x=-W/2 平面, back y=D, front y=0, 脊 y=D/2."""
    p = {**DEFAULTS, **p}
    W, D, Hb, Hr, Ef, gap = p["W"], p["D"], p["Hb"], p["Hr"], p["Ef"], p["fin_gap_mm"]
    lean = math.asin(min(1.0, (gap / 2) / Ef)) if Ef > 0 else 0.0
    return {
        "bbox": {"W": W, "D": D, "H": Hb + Hr},
        "ridge_mid": (0.0, D / 2, Hb + Hr),
        "gable_apex_L": (-W / 2, D / 2, Hb + Hr),
        "gable_apex_R": (W / 2, D / 2, Hb + Hr),
        "fin_top_gap": 2 * Ef * math.sin(lean),
        "fin_lean_deg": math.degrees(lean),
    }
