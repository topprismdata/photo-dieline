"""分层 1:1 SVG 导出 (user units = mm; width/height 带物理单位; 图层=印前语义).

图层: CUT(红实线) / CREASE-MOUNTAIN(蓝虚) / CREASE-VALLEY(绿点划) /
GLUE(灰绿填充) / BLEED(品红虚, 外扩3mm) / REGISTRATION(黑角标) / INFO(黑: 50mm 校验条+图签)

几何与颜色来自 export.layout (与 PDF 共用的单源); 本模块只做 SVG 序列化。
页面坐标 y 向上, SVG y 向下 → 翻转 y, 使 SVG 与 PDF 呈现同一个面。
"""
from __future__ import annotations

from ..core.ir import ARError
from .layout import (BLEED_MM, CHECK_BAR_MM, COLORS, DASH, LAYERS, MARGIN, RGB,
                     cut_segments, net_bbox, page_shapes, title)

__all__ = ["render", "net_bbox", "cut_segments", "MARGIN", "BLEED_MM", "CHECK_BAR_MM",
           "COLORS", "DASH", "LAYERS", "RGB"]


def _n(v: float) -> str:
    return f"{v:.3f}"


def render(ir, net_w: float, net_h: float) -> str:
    """IR → 分层 SVG 字符串。net_w/net_h = 净图宽高 (须与 IR 包围盒一致)。"""
    nx0, ny0, nx1, ny1 = net_bbox(ir)
    pw, ph = nx1 - nx0, ny1 - ny0
    if abs(pw - net_w) > 1e-6 or abs(ph - net_h) > 1e-6:
        raise ARError(f"net_w/net_h ({net_w:.3f},{net_h:.3f}) 与 IR 净图包围盒 ({pw:.3f},{ph:.3f}) 不一致")
    W, H = net_w + 2 * MARGIN, net_h + 2 * MARGIN
    shapes = page_shapes(ir)

    def P(pts) -> str:
        return " ".join(f"{_n(x)},{_n(H - y)}" for x, y in pts)

    parts: dict[str, list[str]] = {k: [] for k in LAYERS}
    for layer in LAYERS:
        dash = f' stroke-dasharray="{",".join(f"{d:g}" for d in DASH[layer])}"' if layer in DASH else ""
        for s in shapes[layer]:
            if s.closed and layer == "GLUE":
                parts[layer].append(f'<polygon points="{P(s.pts)}" fill="{COLORS["GLUE"]}" '
                                    f'fill-opacity="0.45" stroke="none"/>')
            elif s.closed:
                parts[layer].append(f'<polygon points="{P(s.pts)}" fill="none" stroke="{COLORS[layer]}" '
                                    f'stroke-width="{s.width:g}"{dash}/>')
            elif len(s.pts) == 2:
                (x1, y1), (x2, y2) = s.pts
                parts[layer].append(f'<line x1="{_n(x1)}" y1="{_n(H - y1)}" x2="{_n(x2)}" y2="{_n(H - y2)}" '
                                    f'stroke="{COLORS[layer]}" stroke-width="{s.width:g}"{dash}/>')
            else:
                parts[layer].append(f'<polyline points="{P(s.pts)}" fill="none" stroke="{COLORS[layer]}" '
                                    f'stroke-width="{s.width:g}"{dash}/>')
    parts["INFO"].append(f'<text x="{_n(MARGIN)}" y="{_n(H - 4.0)}" font-size="3.5" fill="#111111" '
                         f'font-family="Helvetica">{title(ir)} | CHECK BAR = {CHECK_BAR_MM:g} mm</text>')

    layers = "\n".join(f'<g id="{name}">' + "\n".join(items) + "</g>" for name, items in parts.items())
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W:.3f}mm" height="{H:.3f}mm"
 viewBox="0 0 {W:.3f} {H:.3f}">
<title>PhotoDieline dieline 1:1</title>
{layers}
</svg>'''
