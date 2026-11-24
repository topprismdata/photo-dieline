"""E5b: 净图原点偏移 — render()/build_pdf() 只收宽高, 假定净图左下角=(0,0). gable_top 净图 y∈[-D, ...] => 底板画到画布外."""
import re, zlib
import numpy as np
from photo_dieline.core.ir import from_raw
from photo_dieline.export import svg as svgx, pdf as pdfx
from photo_dieline.parametric import gable_top, base as T
from photo_dieline.cli import _layer_geo

NUM = r"-?[\d.]+"
def check(raw, label):
    ir = from_raw(raw); x0, y0, x1, y1 = svgx.net_bbox(ir); nw, nh = x1 - x0, y1 - y0
    svg = svgx.render(ir, nw, nh); pdf = pdfx.build_pdf(ir, nw, nh, _layer_geo(ir))
    W, H = nw + 24, nh + 24
    pts = [(float(a), float(b)) for a, b in re.findall(rf'<(?:line|polygon|path)[^>]*?...', "")] if False else None
    xs, ys = [], []
    for tag in re.findall(r"<(?:line|polygon)\b[^>]*>", svg):
        if tag.startswith("<line"):
            g = re.match(rf'<line x1="({NUM})" y1="({NUM})" x2="({NUM})" y2="({NUM})"', tag)
            xs += [float(g.group(1)), float(g.group(3))]; ys += [float(g.group(2)), float(g.group(4))]
        else:
            for a, b in re.findall(rf"({NUM}),({NUM})", tag):
                xs.append(float(a)); ys.append(float(b))
    xs, ys = np.array(xs), np.array(ys)
    out_x = ((xs < 0) | (xs > W)).sum(); out_y = ((ys < 0) | (ys > H)).sum()
    n = len(xs)
    print(f"[{label}] net bbox x∈[{x0:.2f},{x1:.2f}] y∈[{y0:.2f},{y1:.2f}]  canvas={W:.2f}x{H:.2f}")
    print(f"   SVG geometry coords: x∈[{xs.min():.2f},{xs.max():.2f}] y∈[{ys.min():.2f},{ys.max():.2f}]  ; vertices outside viewBox: {out_x+out_y}/{n} "
          f"({100*(out_x+out_y)/n:.0f}%)  ; y<0 by {max(0,-ys.min()):.2f} mm ; empty band at SVG bottom: {H-ys.max():.2f} mm")
    head = pdf[:4096].decode("latin-1")
    content = zlib.decompress(re.search(rb"stream\n(.*?)\nendstream", pdf, re.S).group(1)).decode("latin-1")
    cy = [float(v) for v in re.findall(rf"({NUM}) ({NUM}) m\n", content) for v in (v,)] if False else None
    cy = [float(b) for a, b in re.findall(rf"({NUM}) ({NUM}) m\n", content)]
    PT = 72 / 25.4
    print(f"   PDF path starts y∈[{min(cy)/PT:.2f},{max(cy)/PT:.2f}] mm on a {H:.2f} mm-tall page  ; starts below page (y<0): {sum(1 for v in cy if v < 0)}/{len(cy)}")
    return out_x + out_y, n

raw = gable_top.build_ir({"W": 57.15, "D": 57.15, "Hb": 75.0, "Hr": 20.25, "Ef": 12.0, "board_t": 0.42})
check(raw, "gable_top halfpint (README 示例)")
check(gable_top.build_ir(None), "gable_top DEFAULTS")

print("\n== 仓内已提交的示例产物 (examples/gable_top/artifacts/dieline.svg) ==")
s = open("/Users/guohongbin/photo-dieline/examples/gable_top/artifacts/dieline.svg").read()
print(" ", re.search(r'<svg[^>]*viewBox="[^"]+"', s).group(0).replace("\n", " "))
ys = [float(b) for a, b in re.findall(rf"({NUM}),({NUM})", s)] + [float(v) for v in re.findall(rf'<line [^>]*?y[12]="({NUM})"', s)]
print(f"  y range in file: [{min(ys):.3f}, {max(ys):.3f}]  -> negative-y (off-canvas) coordinates: {(np.array(ys) < 0).sum()} of {len(ys)}")
# 哪些面板落在画布外
ir = from_raw(raw)
for p in ir.panels:
    ymin = min(q[1] for q in p["polygon_2d"]) + 12
    if ymin < 0: print(f"   panel {p['id']:6s} (role={p['role']}) spans SVG y∈[{ymin:.2f},{max(q[1] for q in p['polygon_2d'])+12:.2f}] -> OFF-CANVAS")

print("\n== 影响面: 注册表 100 类中有多少类净图左下角不在原点 (只读统计) ==")
bad = []; tot = 0
for c in T.all_classes():
    m = T.get(c); params = dict(m.DEFAULTS)
    if hasattr(m, "class_params"): params.update(m.class_params(c))
    try:
        r = m.build_ir(params); r.pop("_derived", None); i = from_raw(r)
    except Exception as e:
        continue
    tot += 1; x0, y0, x1, y1 = svgx.net_bbox(i)
    if x0 < -1e-9 or y0 < -1e-9: bad.append((c, round(x0, 2), round(y0, 2)))
print(f" classes={tot}, with net min-x<0 or min-y<0 (geometry drawn off-canvas): {len(bad)}")
print(" ", bad[:50])
