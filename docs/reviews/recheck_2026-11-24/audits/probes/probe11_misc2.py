"""E11: _intersect3d 正/负例, SVG CUT 内部缝, fin_gap 钳位 (只读)."""
import re
import numpy as np
from photo_dieline.qa.pipeline import _intersect3d
from photo_dieline.core.ir import from_raw
from photo_dieline.folding.engine import fold_all
from photo_dieline.export import svg as svgx
from photo_dieline.parametric import gable_top

A = np.array([[-10, -10, 0], [10, -10, 0], [10, 10, 0], [-10, 10, 0]], float)
print("== _intersect3d ==")
cases = {
    "正例: B 竖直穿过 A 中心 (真穿插)":            np.array([[-5, -15, -15], [5, -15, 15], [5, 15, 15], [-5, 15, -15]], float),
    "负例: B 平行, 距 A 5mm (不相交)":             np.array([[-10, -10, 5], [10, -10, 5], [10, 10, 5], [-10, 10, 5]], float),
    "负例: B 倾斜, 交线在 x=50 (离 A 40mm)":        np.array([[0, -100, -25], [100, -100, 25], [100, 100, 25], [0, 100, -25]], float),
    "正例: B 夹角 1.1°, 交线 x=5 (在 A 内, 真穿插)": np.array([[-10, -10, -0.30], [10, -10, 0.10], [10, 10, 0.10], [-10, 10, -0.30]], float),
}
for k, B in cases.items():
    na = np.cross(A[1] - A[0], A[2] - A[0]); nb = np.cross(B[1] - B[0], B[2] - B[0])
    ang = np.degrees(np.arccos(abs(float(na @ nb) / np.linalg.norm(na) / np.linalg.norm(nb))))
    truth = ("True" if k.startswith("正例") else "False")
    r = _intersect3d(A, B)
    print(f"  {k:<46} |na·nb|夹角={ang:5.2f}°  _intersect3d={r!s:5}  应为={truth}  {'OK' if str(r) == truth else '<<< 错'}")

print("\n== SVG CUT 层: 不在外轮廓 polygon 上的 <line> ==")
raw = gable_top.build_ir({"W": 57.15, "D": 57.15, "Hb": 75.0, "Hr": 20.25, "Ef": 12.0}); ir = from_raw(raw)
x0, y0, x1, y1 = svgx.net_bbox(ir); svg = svgx.render(ir, x1 - x0, y1 - y0)
cut = re.search(r'<g id="CUT">(.*?)</g>', svg, re.S).group(1)
ring = [tuple(map(float, p.split(","))) for p in re.search(r'<polygon points="([^"]+)"', cut).group(1).split()]
ringset = {tuple(sorted((ring[i], ring[(i + 1) % (len(ring) - 1)]))) for i in range(len(ring) - 1)}
lines = [tuple(map(float, g)) for g in re.findall(r'<line x1="(-?[\d.]+)" y1="(-?[\d.]+)" x2="(-?[\d.]+)" y2="(-?[\d.]+)"', cut)]
inner = [l for l in lines if tuple(sorted(((l[0], l[1]), (l[2], l[3])))) not in ringset]
print(f"  <line> 总数={len(lines)}; 与外轮廓重合={len(lines) - len(inner)}; 内部={len(inner)}")
for l in inner: print(f"    ({l[0]:.3f},{l[1]:.3f}) -> ({l[2]:.3f},{l[3]:.3f})  len={np.hypot(l[2]-l[0], l[3]-l[1]):.3f}")
for x in sorted({l[0] for l in inner}):
    segs = [l for l in inner if l[0] == x]; print(f"    seam x={x:.3f}: {len(segs)} lines cover it, overlap length = {min(abs(l[3]-l[1]) for l in segs):.3f} mm")

print("\n== fin_gap_mm 超域钳位 ==")
for gap in (3.0, 27.9, 28.0, 40.0):
    r = gable_top.build_ir({"Ef": 14.0, "fin_gap_mm": gap}); i = from_raw(r); w = fold_all(i)
    top = np.linalg.norm(np.mean(w["finF"][2:4], axis=0) - np.mean(w["finB"][2:4], axis=0))
    print(f"  fin_gap_mm={gap:>5}  折叠后两鳍顶缘距={top:7.3f} mm  (偏差 {abs(top-gap):6.3f})  fin_lean_deg={r['_derived']['fin_lean_deg']:.2f}")
