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


PALETTE = [(94, 129, 244), (240, 96, 106), (72, 187, 120), (244, 180, 64), (155, 107, 244),
           (64, 192, 220), (228, 120, 200), (140, 160, 90), (244, 130, 64), (90, 140, 200),
           (200, 90, 90), (120, 190, 170), (180, 170, 80), (110, 110, 130), (220, 200, 120),
           (90, 210, 140), (170, 110, 220), (230, 160, 110), (100, 120, 170), (160, 200, 90)]


ROLE_RANK = {"wall": 0, "slope": 0, "gable_end": 0, "fin": 1, "flap": 1, "glue": 2}


def render_twin(ir: GeometryIR, size: int = 640, az_deg: float = -22.0,
                el_deg: float = 16.0, debug_ids: bool = False) -> Image.Image:
    world = fold_all(ir)
    roles = {p["id"]: p["role"] for p in ir.panels}
    pids = [p["id"] for p in ir.panels]
    pid_color = {pid: PALETTE[i % len(PALETTE)] for i, pid in enumerate(pids)}
    # 实体优先着色, 开板(鳍/底板/粘口)半透明逻辑: 简化 = 全部不透明按深度排序
    tris: list[tuple[np.ndarray, np.ndarray, np.ndarray, str]] = []
    allpts = np.vstack(list(world.values()))
    lo, hi = allpts.min(0), allpts.max(0)
    center = (lo + hi) / 2
    radius = float(np.linalg.norm(hi - lo)) / 2

    for pid, verts in world.items():
        for (ia, ib, ic) in _tri_faces(verts):
            tris.append((verts[ia], verts[ib], verts[ic], pid, roles.get(pid, "wall")))

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
    img = np.full((size, size, 3), 248, dtype=np.uint8)
    zbuf = np.full((size, size), np.inf)
    rbuf = np.full((size, size), 9, dtype=np.int8)

    def outward_normal(a, b, c):
        n = _norm(np.cross(b - a, c - a))
        if n @ (0.5 * (a + b + c) - center) < 0:  # 模板绕序内翻 → 背离盒中心定向
            n = -n
        return n

    for (a, b, c, pid, role) in tris:
        nrm = outward_normal(a, b, c)
        if debug_ids and nrm @ (eye - a) < 0:
            continue  # 背面剔除 (仅调试图; 法线已外向归一)
        p2a, za = project(a); p2b, zb = project(b); p2c, zc = project(c)
        if debug_ids:
            base = tuple(v / 255.0 for v in pid_color.get(pid, (128, 128, 128)))
            col = np.array(base) * 235
        else:
            base = {"wall": (0.90, 0.90, 0.92), "slope": (0.88, 0.88, 0.91),
                    "fin": (0.82, 0.82, 0.86), "flap": (0.80, 0.80, 0.84),
                    "glue": (0.78, 0.78, 0.81), "gable_end": (0.90, 0.90, 0.92)}.get(role, (0.88, 0.88, 0.9))
            lam = max(0.0, float(nrm @ light))
            shade = 0.38 + 0.62 * lam
            col = np.array([base[0] * shade, base[1] * shade, base[2] * shade]) * 255
        fill_tri_z(img, zbuf, rbuf, ROLE_RANK.get(role, 1), p2a, za, p2b, zb, p2c, zc, col)

    # 结构棱线: 重投影所有折线邻接边(近似=面板轮廓)
    im = Image.fromarray(img)
    from PIL import ImageDraw
    dr = ImageDraw.Draw(im)
    for pid, verts in world.items():
        pts = []
        for v in verts:
            p2, _ = project(v)
            pts.append(tuple(p2))
        dr.line(pts + [pts[0]], fill=(30, 32, 38) if debug_ids else (70, 74, 84), width=1)
    if debug_ids:
        gl = Image.new("RGB", (168, 24 * len(pids) + 8), (250, 250, 250))
        dg = ImageDraw.Draw(gl)
        for i, pid in enumerate(pids):
            y = 4 + i * 24
            dg.rectangle([4, y, 20, y + 16], fill=pid_color[pid], outline=(40, 40, 44))
            dg.text((26, y + 2), f"{pid} ({roles.get(pid, '?')})", fill=(30, 30, 34))
        canvas = Image.new("RGB", (im.width + gl.width, im.height), (250, 250, 250))
        canvas.paste(im, (0, 0))
        canvas.paste(gl, (im.width, 0))
        return canvas
    return im


def fill_tri_z(img: np.ndarray, zbuf: np.ndarray, rbuf: np.ndarray, rank: int,
               p2a, za, p2b, zb, p2c, zc, col) -> None:
    size = img.shape[0]
    xs = [p2a[0], p2b[0], p2c[0]]
    ys = [p2a[1], p2b[1], p2c[1]]
    x0, x1 = max(0, int(min(xs))), min(size - 1, int(max(xs)) + 1)
    y0, y1 = max(0, int(min(ys))), min(size - 1, int(max(ys)) + 1)
    if x1 < x0 or y1 < y0:
        return
    v0 = p2b - p2a
    v1 = p2c - p2a
    den = v0[0] * v1[1] - v1[0] * v0[1]
    if abs(den) < 1e-9:
        return
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    px_x = gx - p2a[0]
    px_y = gy - p2a[1]
    u = (px_x * v1[1] - v1[0] * px_y) / den
    v = (v0[0] * px_y - px_x * v0[1]) / den
    mask = (u >= -1e-6) & (v >= -1e-6) & (u + v <= 1 + 1e-6)
    # 透视正确深度: 1/z 屏幕仿射 → 同平面三角形逐像素深度精确相等 (共面仲裁才可靠)
    inv_z = (1.0 - u - v) / za + u / zb + v / zc
    zz = 1.0 / np.maximum(inv_z, 1e-9)
    sub_z = zbuf[y0:y1 + 1, x0:x1 + 1]
    sub_r = rbuf[y0:y1 + 1, x0:x1 + 1]
    # 同面仲裁: |Δz| < 0.6mm 视为共面(零板厚), 高优先级(低rank)面板胜出
    coplanar = mask & (np.abs(zz - sub_z) < 0.6) & (rank < sub_r)
    nearer = mask & (zz < sub_z - 0.6)
    upd = nearer | coplanar
    sub_z[upd] = zz[upd]
    sub_r[upd] = rank
    sub_img = img[y0:y1 + 1, x0:x1 + 1]
    sub_img[upd] = np.clip(col, 0, 255)


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
