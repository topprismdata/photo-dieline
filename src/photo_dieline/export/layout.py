"""页面几何单源: IR → 各图层的形状 (页面坐标 mm, 原点在左下, y 向上).

SVG 与 PDF 两个交付物共用这一份几何, 保证图层内容、颜色、出血、校验条逐项一致。
坐标约定: 净图 (模板 polygon_2d) 的包围盒左下角平移到 (MARGIN, MARGIN); 模板的净图原点
可以不在 (0,0) — 本模块负责归一, 导出器不再各自假设。
"""
from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from ..core.ir import ARError

MARGIN = 12.0          # 净图到页边的留白 (mm)
BLEED_MM = 3.0         # 出血外扩 (mm)
CHECK_BAR_MM = 50.0    # 物理校验条长度 (mm)
LAYERS = ["CUT", "CREASE-MOUNTAIN", "CREASE-VALLEY", "GLUE", "BLEED", "REGISTRATION", "INFO"]

RGB = {   # 图层色 (0-1); SVG 的 hex 与 PDF 的 RG 都由这一份派生
    "CUT": (0.80, 0.13, 0.13),
    "CREASE-MOUNTAIN": (0.13, 0.27, 0.80),
    "CREASE-VALLEY": (0.12, 0.54, 0.23),
    "GLUE": (0.50, 0.66, 0.56),
    "BLEED": (0.80, 0.13, 0.67),
    "REGISTRATION": (0.07, 0.07, 0.07),
    "INFO": (0.07, 0.07, 0.07),
}
COLORS = {k: "#%02X%02X%02X" % tuple(round(c * 255) for c in v) for k, v in RGB.items()}
DASH = {"CREASE-MOUNTAIN": (4.0, 3.0), "CREASE-VALLEY": (10.0, 3.0, 2.0, 3.0),
        "BLEED": (3.0, 3.0)}   # mm
CREASE_LAYER = {"MOUNTAIN": "CREASE-MOUNTAIN", "VALLEY": "CREASE-VALLEY"}
GLUE_FILL_RGB = tuple(0.45 * c + 0.55 for c in RGB["GLUE"])   # 45% 不透明度的等效实色 (PDF 无透明度)


@dataclass(frozen=True)
class Shape:
    """一条折线或多边形 (页面坐标 mm)."""
    pts: tuple[tuple[float, float], ...]
    layer: str
    width: float = 0.25   # 线宽 mm
    closed: bool = False  # True = 闭合多边形 (GLUE 层同时填充)


def net_bbox(ir) -> tuple[float, float, float, float]:
    """净图包围盒 (模板坐标): (x0, y0, x1, y1)."""
    xs, ys = [], []
    for p in ir.panels:
        for x, y in p["polygon_2d"]:
            xs.append(x)
            ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def page_size(ir) -> tuple[float, float]:
    x0, y0, x1, y1 = net_bbox(ir)
    return x1 - x0 + 2 * MARGIN, y1 - y0 + 2 * MARGIN


def cut_segments(ir) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """全部裁切缝 (模板坐标): 面板边减去被折线共线覆盖的部分.

    面板边与折线的端点不必逐点对应 — 模板可以在面板里插入共线分点 (例如提手缺口把顶缘断开)。
    只要面板边 (或其一段) 被某条折线共线覆盖, 这一段就是铰链材料而不是裁切;
    只有落在全部折线之外的部分才成为裁切缝 (相邻底板分界/粘口自由边必须裁开)。
    含净图外轮廓边; 页面几何里落在并集边界上的段由外轮廓多边形承担, 不重复输出。
    """
    folds = [LineString([tuple(e.seg_2d[0]), tuple(e.seg_2d[1])]) for e in ir.edges]
    folds = [f for f in folds if f.length > 1e-12]
    fold_union = unary_union(folds) if folds else None
    out = []
    for p in ir.panels:
        poly = p["polygon_2d"]
        n = len(poly)
        for i in range(n):
            seg = LineString([tuple(poly[i]), tuple(poly[(i + 1) % n])])
            rest = seg.difference(fold_union) if fold_union is not None else seg
            for piece in (rest.geoms if hasattr(rest, "geoms") else [rest]):
                if piece.length > 1e-9:
                    cs = list(piece.coords)
                    out.append((tuple(cs[0]), tuple(cs[-1])))
    return out


def _parts(geom):
    """Polygon / MultiPolygon → Polygon 列表."""
    if geom.geom_type == "Polygon":
        return [geom]
    return [g for g in geom.geoms if g.geom_type == "Polygon"]


def page_shapes(ir) -> dict[str, list[Shape]]:
    """IR → 各图层形状 (页面坐标). 单一来源: 导出器与 QA 门都读这里."""
    x0, y0, _x1, _y1 = net_bbox(ir)
    W, H = page_size(ir)

    def T(x, y):
        return x - x0 + MARGIN, y - y0 + MARGIN

    out: dict[str, list[Shape]] = {k: [] for k in LAYERS}
    outline = unary_union([Polygon(p["polygon_2d"]) for p in ir.panels]).buffer(0)
    parts = _parts(outline)
    if not parts:
        raise ARError("面板并集为空")
    # CUT: 每个独立坯件的外轮廓 (+ 内孔) 各画一次
    for part in parts:
        out["CUT"].append(Shape(tuple(T(x, y) for x, y in part.exterior.coords), "CUT", 0.3, True))
        for ring in part.interiors:
            out["CUT"].append(Shape(tuple(T(x, y) for x, y in ring.coords), "CUT", 0.3, True))
    # CUT: 内部裁切缝 (不落在并集边界上的非折线面板边)
    bnd = outline.boundary
    for a, b in cut_segments(ir):
        if bnd.distance(LineString([a, b])) < 1e-6:
            continue
        out["CUT"].append(Shape((T(*a), T(*b)), "CUT", 0.3))
    # 折线: M/V 语义原样分图层; 未知语义报错 (不静默归类)
    for e in ir.edges:
        layer = CREASE_LAYER.get(e.mt_va)
        if layer is None:
            raise ARError(f"折线 {e.id} 语义非法: {e.mt_va!r} (须 MOUNTAIN/VALLEY)")
        out[layer].append(Shape((T(*e.seg_2d[0]), T(*e.seg_2d[1])), layer, 0.25))
    # GLUE: 粘口填充
    for p in ir.panels:
        if p["role"] == "glue":
            out["GLUE"].append(Shape(tuple(T(x, y) for x, y in p["polygon_2d"]), "GLUE", 0.0, True))
    # BLEED: 外轮廓外扩 (圆角分段数固定, SVG/PDF 同一条曲线)
    bleed = outline.buffer(BLEED_MM, quad_segs=8)
    for part in _parts(bleed):
        out["BLEED"].append(Shape(tuple(T(x, y) for x, y in part.exterior.coords), "BLEED", 0.25, True))
    # REGISTRATION: 四角套准标
    cm, off = 6.0, 4.0
    for cx, cy in ((0.0, 0.0), (W, 0.0), (0.0, H), (W, H)):
        sx = 1.0 if cx == 0 else -1.0
        sy = 1.0 if cy == 0 else -1.0
        out["REGISTRATION"].append(Shape(((cx + sx * off, cy), (cx + sx * (off + cm), cy)), "REGISTRATION"))
        out["REGISTRATION"].append(Shape(((cx, cy + sy * off), (cx, cy + sy * (off + cm))), "REGISTRATION"))
    # INFO: 50mm 物理校验条 + 两端刻度
    by = H - 8.0
    bx = MARGIN
    out["INFO"].append(Shape(((bx, by), (bx + CHECK_BAR_MM, by)), "INFO", 0.5))
    for x in (bx, bx + CHECK_BAR_MM):
        out["INFO"].append(Shape(((x, by - 2.0), (x, by + 2.0)), "INFO", 0.3))
    return out


def title(ir) -> str:
    return (f"{ir.package['type']} {ir.package['template']['id']} v{ir.package['template']['version']} "
            f"| IR v{ir.meta['ir_version']} | units=mm | scale 1:1")
