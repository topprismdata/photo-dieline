"""折叠孪生渲染器: 3D 面板 → 平面着色 PNG (纯 numpy, core 隔离).

画家算法 + 兰伯特头灯; 相机绕盒 3/4 视角; 输出折叠孪生单帧,
用于与实拍照片并排对比 (photo-alignment QA 的 P1 前身, 人工确认件)。
"""
from __future__ import annotations

import numpy as np
from PIL import Image

from ..core.ir import GeometryIR
from ..folding.engine import fold_all


def _tri_faces(poly: np.ndarray) -> list[tuple[int, int, int]]:
    return [(0, i, i + 1) for i in range(1, len(poly) - 1)]


def render_twin(ir: GeometryIR, size: int = 640, az_deg: float = -32.0,
                el_deg: float = 12.0) -> Image.Image:
    world = fold_all(ir)
    roles = {p["id"]: p["role"] for p in ir.panels}
    # 实体优先着色, 开板(鳍/底板/粘口)半透明逻辑: 简化 = 全部不透明按深度排序
    tris: list[tuple[np.ndarray, np.ndarray, np.ndarray, str]] = []
    allpts = np.vstack(list(world.values()))
    lo, hi = allpts.min(0), allpts.max(0)
    center = (lo + hi) / 2
    radius = float(np.linalg.norm(hi - lo)) / 2

    for pid, verts in world.items():
        for (ia, ib, ic) in _tri_faces(verts):
            tris.append((verts[ia], verts[ib], verts[ic], roles.get(pid, "wall")))

    az, el = np.radians(az_deg), np.radians(el_deg)
    d = radius * 3.0
    eye = center + np.array([d * np.sin(az) * np.cos(el), -d * np.cos(az) * np.cos(el),
                             d * np.sin(el)])
    fwd = _norm(center - eye)
    right = _norm(np.cross(fwd, np.array([0.0, 0.0, 1.0])))
    up = np.cross(right, fwd)
    f = 1.0 / np.tan(np.radians(28.0))  # 半视场 28°

    def project(p):
        rel = p - eye
        z = float(rel @ fwd)
        x = float(rel @ right) / z * f
        y = float(rel @ up) / z * f
        return np.array([(x + 1) * size / 2, (1 - y) * size / 2]), z

    light = _norm(np.array([-0.35, 0.55, 0.76]))
    order = []
    for t in tris:
        cen = (t[0] + t[1] + t[2]) / 3
        order.append((float((cen - eye) @ fwd), t))
    order.sort(key=lambda x: -x[0])

    img = np.full((size, size, 3), 248, dtype=np.uint8)
    for depth, (a, b, c, role) in order:
        p2a, za = project(a); p2b, zb = project(b); p2c, zc = project(c)
        nrm = _norm(np.cross(b - a, c - a))
        if nrm @ (eye - a) < 0:
            nrm = -nrm
        base = {"wall": (0.90, 0.90, 0.92), "slope": (0.88, 0.88, 0.91),
                "fin": (0.82, 0.82, 0.86), "flap": (0.80, 0.80, 0.84),
                "glue": (0.72, 0.80, 0.74), "gable_end": (0.90, 0.90, 0.92)}.get(role, (0.88, 0.88, 0.9))
        lam = max(0.0, float(nrm @ light))
        shade = 0.38 + 0.62 * lam
        col = np.array([base[0] * shade, base[1] * shade, base[2] * shade]) * 255
        fill_tri(img, p2a, p2b, p2c, col)

    # 结构棱线: 重投影所有折线邻接边(近似=面板轮廓)
    im = Image.fromarray(img)
    from PIL import ImageDraw
    dr = ImageDraw.Draw(im)
    for pid, verts in world.items():
        pts = []
        for v in verts:
            p2, _ = project(v)
            pts.append(tuple(p2))
        dr.line(pts + [pts[0]], fill=(70, 74, 84), width=1)
    return im


def fill_tri(img: np.ndarray, p2a, p2b, p2c, col) -> None:
    size = img.shape[0]
    xs = [p2a[0], p2b[0], p2c[0]]
    ys = [p2a[1], p2b[1], p2c[1]]
    x0, x1 = max(0, int(min(xs))), min(size - 1, int(max(xs)) + 1)
    y0, y1 = max(0, int(min(ys))), min(size - 1, int(max(ys)) + 1)
    if x1 < x0 or y1 < y0:
        return
    ax, ay = p2a
    v0 = p2b - p2a
    v1 = p2c - p2a
    den = v0[0] * v1[1] - v1[0] * v0[1]
    if abs(den) < 1e-9:
        return
    for yy in range(y0, y1 + 1):
        for xx in range(x0, x1 + 1):
            px = np.array([xx + 0.5, yy + 0.5]) - np.array([ax, ay])
            u = (px[0] * v1[1] - v1[0] * px[1]) / den
            v = (v0[0] * px[1] - px[0] * v0[1]) / den
            if u >= -1e-6 and v >= -1e-6 and u + v <= 1 + 1e-6:
                img[yy, xx] = np.clip(col, 0, 255)


def _norm(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v)


def compare_side_by_side(photo_path, twin: Image.Image, out_path, crop=None) -> None:
    """实拍 | 孪生渲染 并排 + 标注 (photo-alignment 人工确认件)."""
    import hashlib
    from pathlib import Path
    photo = Image.open(photo_path).convert("RGB")
    if crop:
        photo = photo.crop(crop)
    h = 720
    photo = photo.resize((int(photo.width * h / photo.height), h))
    twin = twin.resize((int(twin.width * h / twin.height), h))
    gap = 24
    canvas = Image.new("RGB", (photo.width + twin.width + gap * 3, h + 56), (250, 250, 250))
    canvas.paste(photo, (gap, 40))
    canvas.paste(twin, (photo.width + gap * 2, 40))
    d = ImageDraw_of(canvas)
    d.text((gap, 12), "A. 实拍照片 (USDA PD)", fill=(30, 30, 34))
    d.text((photo.width + gap * 2, 12), "B. 逆向孪生折叠渲染 (Geometry IR → 纯Python)", fill=(30, 30, 34))
    sha = hashlib.sha256(Path(photo_path).read_bytes()).hexdigest()[:12]
    d.text((gap, h + 42), f"photo sha256:{sha}… | twin: gable_top IR folded | 人工确认件 (非自动对齐门)",
           fill=(110, 110, 116))
    canvas.save(out_path, quality=92)


def ImageDraw_of(im):
    from PIL import ImageDraw
    return ImageDraw.Draw(im)
