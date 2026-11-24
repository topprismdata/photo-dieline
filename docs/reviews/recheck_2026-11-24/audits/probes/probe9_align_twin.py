"""E9: align.py 与 render/twin.py 投影一致性 + 拟合边界; twin NaN 来源; BLEED SVG vs PDF."""
import math, warnings, copy
import numpy as np
from PIL import Image
from photo_dieline.core.ir import from_raw
from photo_dieline.folding.engine import fold_all
from photo_dieline import align
from photo_dieline.render import twin
from photo_dieline.parametric import gable_top, base as T
from photo_dieline.export import svg as svgx
from photo_dieline.cli import _layer_geo

ir = from_raw(gable_top.build_ir(None)); world = fold_all(ir)
allp = np.vstack(list(world.values())); lo, hi = allp.min(0), allp.max(0)
center, radius = (lo + hi) / 2, float(np.linalg.norm(hi - lo)) / 2

print("== E9a: 默认相机下 align.project 与 twin.render_twin 投影是否逐像素一致 ==")
# twin 的 project 是闭包, 用图像重投影反推: 取 wallL 顶点, 在 render_twin 的输出图里找轮廓线? 更直接: 复刻 twin.project 公式 (逐字抄自 twin.py L70-77) 与 align.project 比较
def twin_project(p, az_deg=-22.0, el_deg=16.0, size=640):
    az, el = np.radians(az_deg), np.radians(el_deg); d = radius * 3.0
    eye = center + np.array([d*np.sin(az)*np.cos(el), -d*np.cos(az)*np.cos(el), d*np.sin(el)])
    fwd = (center - eye) / np.linalg.norm(center - eye)
    right = np.cross(fwd, np.array([0.0, 0.0, 1.0])); right /= np.linalg.norm(right)
    up = np.cross(right, fwd); f = 1.0 / np.tan(np.radians(28.0))
    rel = p - eye; z = rel @ fwd; x = rel @ right / z * f; y = rel @ up / z * f
    return np.array([(x + 1) * size / 2, (1 - y) * size / 2]), z
p_align = align.P0.copy()
d = np.linalg.norm(align.project(world["front"], p_align, center, radius) - np.array([twin_project(v)[0] for v in world["front"]]), axis=1)
print(f" size=640: max |align.project - twin.project| = {d.max():.2e} px  (same default az/el/d_factor/fov)")
for size in (320, 900, 1280):
    d = np.linalg.norm(align.project(world["front"], p_align, center, radius) - np.array([twin_project(v, size=size)[0] for v in world["front"]]), axis=1)
    print(f" size={size}: max diff with align P0 (cx=cy=320, scale=1) = {d.max():.1f} px  <- align 'half=320' hard-coded; equivalent params would be cx=cy=size/2")
print(f" render_twin signature exposes d_factor / fov? {twin.render_twin.__code__.co_varnames[:twin.render_twin.__code__.co_argcount]}  (hard-coded 3.0 and 28°)")

print("\n== E9b: 合成拟合 (真值已知) — 可辨识性与参数边界 ==")
rng = np.random.default_rng(0)
def synth(true_p, px_sigma=3.0, n=None):
    pts = np.vstack([world[k] for k in ("front", "wallR", "slopeF", "flapF", "wallL", "finB")])
    idx = rng.choice(len(pts), size=n or 14, replace=False)
    wp = pts[idx]; ip = align.project(wp, np.array(true_p, float), center, radius) + rng.normal(0, px_sigma, (len(idx), 2))
    return wp, ip
for true_p, label in (([-22, 16, 3, 28, 320, 320, 1.0], "真值=P0 (640 画布)"), ([-35, 22, 2.4, 34, 1050, 750, 3.2], "2100x1500 照片 (中心 1050,750)"),
                      ([20, 8, 4.0, 20, 1500, 2000, 4.0], "3000x4000 照片 (中心 1500,2000, 超出 HI cx/cy=1040)")):
    wp, ip = synth(true_p)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore"); p, err, _ = align.fit_camera(wp, ip, center, radius)
    print(f" [{label}] 真值={true_p}\n     拟合={np.round(p, 2).tolist()}\n     mean_px={err.mean():.2f} worst_px={err.max():.2f}  at_bound={[align.P_NAMES[i] for i in range(7) if abs(p[i]-align.LO[i])<1e-6 or abs(p[i]-align.HI[i])<1e-6]}")
# 距离/焦距/尺度三参数简并: 不同 (d,fov,scale) 给出几乎相同的投影?
A = align.project(world["front"], np.array([-22,16,3.0,28,320,320,1.0]), center, radius)
for (dd, ff, ss) in ((2.0, 20.0, 1.0), (4.5, 36.0, 1.0), (6.0, 55.0, 1.0)):
    B = align.project(world["front"], np.array([-22,16,dd,ff,320,320,ss]), center, radius)
    print(f"   (d_factor,fov,scale)=({dd},{ff},{ss}) vs (3,28,1): max |Δpx| = {np.linalg.norm(A-B,axis=1).max():.1f}px  mean={np.linalg.norm(A-B,axis=1).mean():.1f}px  (无噪声; 仅透视畸变提供 d/fov 可辨识信息)")

print("\n== twin.py RuntimeWarning (NaN) 来源 ==")
for c in T.all_classes():
    m = T.get(c); params = dict(m.DEFAULTS)
    if hasattr(m, "class_params"): params.update(m.class_params(c))
    try: raw = m.build_ir(params); raw.pop("_derived", None); i = from_raw(raw)
    except Exception: continue
    w = fold_all(i); bad = []
    for pid, v in w.items():
        if len(v) < 3: bad.append((pid, "n<3")); continue
        cr = np.cross(v[1]-v[0], v[2]-v[0])
        if np.linalg.norm(cr) < 1e-9: bad.append((pid, "fan-degenerate(first 3 collinear)"))
        if not np.all(np.isfinite(v)): bad.append((pid, "non-finite"))
    if bad: print(f"  {c}: {bad}")

print("\n== BLEED: SVG (quad_segs 默认8) vs PDF (quad_segs=2) 几何差 ==")
import re
raw = gable_top.build_ir(None); i = from_raw(raw); x0,y0,x1,y1 = svgx.net_bbox(i)
svg = svgx.render(i, x1-x0, y1-y0); pdf = __import__("photo_dieline.export.pdf", fromlist=["x"]).build_pdf(i, x1-x0, y1-y0, _layer_geo(i))
from shapely.geometry import Polygon
bleed_svg = re.search(r'<g id="BLEED">.*?<polygon points="([^"]+)"', svg, re.S).group(1)
pts_svg = np.array([[float(a), float(b)] for a, b in re.findall(r"(-?[\d.]+),(-?[\d.]+)", bleed_svg)])
outline = __import__("shapely.ops", fromlist=["x"]).unary_union([Polygon(p["polygon_2d"]) for p in i.panels]).buffer(0)
b8 = outline.buffer(3.0); b2 = outline.buffer(3.0, quad_segs=2)
print(f" BLEED polygon vertices: SVG={len(pts_svg)} (quad_segs=8) ; PDF={len(b2.exterior.coords)} (quad_segs=2) ; max deviation b2 vs b8 = {b2.boundary.hausdorff_distance(b8.boundary):.3f} mm")
