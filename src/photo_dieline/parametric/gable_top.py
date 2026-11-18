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
DEFAULTS = {"W": 45.0, "D": 45.0, "Hb": 100.0, "Hr": 12.0,
            "Ef": 14.0, "fin_gap_mm": 3.0, "glue_w": 12.0, "board_t": 0.45}

TEMPLATE = {"id": "gable_top", "version": "0.1"}


def slant(D: float, Hr: float) -> float:
    """坡面板斜高 s = sqrt((D/2)^2 + Hr^2)."""
    return math.hypot(D / 2.0, Hr)


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
        fold("e_glue", (x1, 0), (x1, Hb), "wallL", "glue", "MOUNTAIN",
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
        # 底封板: 全宽前后板内折成底 (水平 z=0 平面), 侧插板内折至中线
        fold("e_ft_fl", (x4, 0), (x5, 0), "front", "flapF", "MOUNTAIN",
             tdir=(0.0, 1.0, 0.0)),
        fold("e_bk_fl", (x2, 0), (x3, 0), "back", "flapB", "MOUNTAIN",
             tdir=(0.0, -1.0, 0.0)),
        fold("e_wl_fl", (x1, 0), (x2, 0), "wallL", "flapL", "MOUNTAIN",
             tdir=(1.0, 0.0, 0.0)),
        fold("e_wr_fl", (x3, 0), (x4, 0), "wallR", "flapR", "MOUNTAIN",
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
            "notes": "M1 golden sample; 板厚补偿 P1; 鳍双层顶缘距=fin_gap_mm",
        },
        "package": {
            "type": "gable_top",
            "params": {k: float(p[k]) for k in PARAM_ORDER},
            "template": dict(TEMPLATE),
            "photo": {},  # build() 注入
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
