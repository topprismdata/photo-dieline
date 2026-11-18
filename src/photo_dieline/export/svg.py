"""分层 1:1 SVG 导出 (user units = mm; width/height 带物理单位; 图层=印前语义).

图层: CUT(红实线) / CREASE-MOUNTAIN(蓝虚) / CREASE-VALLEY(绿点划) /
GLUE(灰绿填充) / BLEED(品红虚, 外扩3mm) / REGISTRATION(黑角标) / INFO(黑: 50mm 校验条+图签)
"""
from __future__ import annotations

import math

from shapely.geometry import Polygon
from shapely.ops import unary_union

MARGIN = 12.0
COLORS = {
    "CUT": "#CC2222",
    "CREASE-MOUNTAIN": "#2244CC",
    "CREASE-VALLEY": "#1F8A3B",
    "GLUE": "#7FA88F",
    "BLEED": "#CC22AA",
    "REGISTRATION": "#111111",
    "INFO": "#111111",
}
DASH = {
    "CREASE-MOUNTAIN": "4,3",
    "CREASE-VALLEY": "10,3,2,3",
    "BLEED": "3,3",
}


def _poly_svg(pts) -> str:
    return " ".join(f"{x:.3f},{y:.3f}" for x, y in pts)


def render(ir, net_w: float, net_h: float) -> str:
    W, H = net_w + 2 * MARGIN, net_h + 2 * MARGIN

    def T(x, y):
        return x + MARGIN, y + MARGIN  # 净图坐标 → 画布

    # 面板并集外轮廓 = CUT 边界
    polys = [Polygon(p["polygon_2d"]) for p in ir.panels]
    outline = unary_union(polys).buffer(0)
    boundary = outline.exterior if outline.geom_type == "Polygon" else max(
        (g.exterior for g in outline.geoms), key=lambda g: g.area)

    parts: dict[str, list[str]] = {k: [] for k in COLORS}
    # CUT: 外轮廓 + 内部裁切段 (非折线面板边)
    ring = list(boundary.coords)
    parts["CUT"].append(f'<polygon points="{_poly_svg([(T(x, y)) for x, y in ring])}" '
                        f'fill="none" stroke="{COLORS["CUT"]}" stroke-width="0.3"/>')
    for a, b in cut_segments(ir):
        (xa, ya), (xb, yb) = T(*a), T(*b)
        parts["CUT"].append(
            f'<line x1="{xa:.3f}" y1="{ya:.3f}" x2="{xb:.3f}" y2="{yb:.3f}" '
            f'stroke="{COLORS["CUT"]}" stroke-width="0.3"/>')
    # 折线
    for e in ir.edges:
        (a, b) = e.seg_2d
        layer = "CREASE-MOUNTAIN" if e.mt_va == "MOUNTAIN" else "CREASE-VALLEY"
        (xa, ya), (xb, yb) = T(*a), T(*b)
        parts[layer].append(
            f'<line x1="{xa:.3f}" y1="{ya:.3f}" x2="{xb:.3f}" y2="{yb:.3f}" '
            f'stroke="{COLORS[layer]}" stroke-width="0.25" stroke-dasharray="{DASH[layer]}"/>')
    # GLUE 填充
    for p in ir.panels:
        if p["role"] == "glue":
            pts = [T(x, y) for x, y in p["polygon_2d"]]
            parts["GLUE"].append(f'<polygon points="{_poly_svg(pts)}" '
                                 f'fill="{COLORS["GLUE"]}" fill-opacity="0.45" stroke="none"/>')
    # BLEED: 外轮廓外扩
    bleed = outline.buffer(3.0)
    bring = bleed.exterior if bleed.geom_type == "Polygon" else max(
        (g.exterior for g in bleed.geoms), key=lambda g: g.area)
    parts["BLEED"].append(f'<polygon points="{_poly_svg([(T(x, y)) for x, y in bring.coords])}" '
                          f'fill="none" stroke="{COLORS["BLEED"]}" stroke-width="0.25" '
                          f'stroke-dasharray="{DASH["BLEED"]}"/>')
    # REGISTRATION: 四角 crop marks
    cm, off = 6.0, 4.0
    for cx, cy in [(0, 0), (W, 0), (0, H), (W, H)]:
        sx = 1 if cx == 0 else -1
        sy = 1 if cy == 0 else -1
        parts["REGISTRATION"].append(
            f'<path d="M {cx+sx*off} {cy} L {cx+sx*(off+cm)} {cy} '
            f'M {cx} {cy+sy*off} L {cx} {cy+sy*(off+cm)}" '
            f'stroke="{COLORS["REGISTRATION"]}" stroke-width="0.25" fill="none"/>')
    # INFO: 50mm 校验条 + 图签
    bx, by = MARGIN, 8.0
    parts["INFO"].append(
        f'<line x1="{bx:.3f}" y1="{by:.3f}" x2="{bx+50.0:.3f}" y2="{by:.3f}" '
        f'stroke="#111" stroke-width="0.5"/>')
    parts["INFO"].append(
        f'<line x1="{bx:.3f}" y1="{by-2:.3f}" x2="{bx:.3f}" y2="{by+2:.3f}" stroke="#111" stroke-width="0.3"/>')
    parts["INFO"].append(
        f'<line x1="{bx+50:.3f}" y1="{by-2:.3f}" x2="{bx+50:.3f}" y2="{by+2:.3f}" stroke="#111" stroke-width="0.3"/>')
    title = (f"{ir.package['type']} {ir.package['template']['id']} v{ir.package['template']['version']} "
             f"| IR v{ir.meta['ir_version']} | units=mm | scale 1:1")
    parts["INFO"].append(
        f'<text x="{MARGIN}" y="{H - 4}" font-size="3.5" fill="#111" '
        f'font-family="Helvetica">{title} | CHECK BAR = 50 mm</text>')

    layers = "\n".join(
        f'<g id="{name}">' + "\n".join(items) + "</g>" for name, items in parts.items())
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W:.3f}mm" height="{H:.3f}mm"
 viewBox="0 0 {W:.3f} {H:.3f}">
<title>PhotoDieline dieline 1:1</title>
{layers}
</svg>'''


def net_bbox(ir) -> tuple[float, float, float, float]:
    xs, ys = [], []
    for p in ir.panels:
        for x, y in p["polygon_2d"]:
            xs.append(x)
            ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def cut_segments(ir) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """内部+边界裁切段: 所有面板边减去折线边 (相邻底板分界/粘口自由边必须裁开)."""
    fold_keys = {tuple(sorted((tuple(e.seg_2d[0]), tuple(e.seg_2d[1])))) for e in ir.edges}
    out = []
    for p in ir.panels:
        poly = p["polygon_2d"]
        n = len(poly)
        for i in range(n):
            a, b = tuple(poly[i]), tuple(poly[(i + 1) % n])
            if tuple(sorted((a, b))) in fold_keys:
                continue
            out.append((a, b))
    return out
