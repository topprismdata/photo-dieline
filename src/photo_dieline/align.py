"""照片-对齐配准 (P0-2): 孪生相机模型 + 关键点最小二乘拟合 + 轮廓叠加.

协议 (2026-11-19 冻结):
  - 关键点由独立 LLM (GPT relay) 在裁切实拍上标注, 逐点带 ±10px 不确定度声明
  - 3D 对应点取自折叠孪生世界坐标 (mm)
  - 相机模型与 render.twin 同构: 绕盒 orbit(az,el,d_factor) + 透视 f + 平面缩放平移
  - scipy least_squares 稳健拟合; 输出逐点重投影误差 (px)
  - 验收: 轮廓叠加图 + 逐点误差表; 阈值须标定实验确定, 不得宣称毫米精度
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from .folding.engine import fold_all
from .core.ir import GeometryIR

# 拟合参数向量: [az_deg, el_deg, d_factor, fov_half_deg, cx, cy, scale]
P_NAMES = ["az_deg", "el_deg", "d_factor", "fov_half_deg", "cx", "cy", "scale"]
P0 = np.array([-22.0, 16.0, 3.0, 28.0, 320.0, 320.0, 1.0])
LO = np.array([-90.0, -5.0, 1.8, 10.0, -400.0, -400.0, 0.2])
HI = np.array([90.0, 45.0, 6.0, 55.0, 1040.0, 1040.0, 4.0])


def _camera(p: np.ndarray, center: np.ndarray, radius: float):
    az, el, d_fac, fov = np.radians(p[0]), np.radians(p[1]), p[2], np.radians(p[3])
    d = d_fac * radius
    eye = center + np.array([d * np.sin(az) * np.cos(el), -d * np.cos(az) * np.cos(el),
                             d * np.sin(el)])
    fwd = center - eye
    fwd = fwd / np.linalg.norm(fwd)
    right = np.cross(fwd, np.array([0.0, 0.0, 1.0]))
    right = right / np.linalg.norm(right)
    up = np.cross(right, fwd)
    f = 1.0 / np.tan(fov)
    return eye, fwd, right, up, f


def project(pts: np.ndarray, p: np.ndarray, center: np.ndarray, radius: float) -> np.ndarray:
    """世界点 (N,3) mm → 像素 (N,2); scale=1 时单位半幅=320px (render_twin 同构)."""
    eye, fwd, right, up, f = _camera(p, center, radius)
    rel = pts - eye
    z = rel @ fwd
    x = (rel @ right) / z * f
    y = (rel @ up) / z * f
    half = 320.0
    return np.column_stack([p[4] + x * half * p[6], p[5] - y * half * p[6]])


def fit_camera(world_pts: np.ndarray, img_pts: np.ndarray,
               center: np.ndarray, radius: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """LSQ 拟合相机参数. 返回 (params, 重投影误差px(逐点), 逐点像素)."""
    from scipy.optimize import least_squares

    def resid(p):
        return (project(world_pts, p, center, radius) - img_pts).ravel()

    r = least_squares(resid, P0, bounds=(LO, HI), loss="soft_l1", f_scale=8.0)
    proj = project(world_pts, r.x, center, radius)
    err = np.linalg.norm(proj - img_pts, axis=1)
    return r.x, err, proj


def fit_for_ir(ir: GeometryIR, correspondences: list[dict]) -> dict:
    """correspondences: [{"panel": "front", "vertex": 0, "px": [x, y]}, ...]"""
    world = fold_all(ir)
    allp = np.vstack(list(world.values()))
    lo, hi = allp.min(0), allp.max(0)
    center, radius = (lo + hi) / 2, float(np.linalg.norm(hi - lo)) / 2
    wp = np.array([world[c["panel"]][c["vertex"]] for c in correspondences], float)
    ip = np.array([c["px"] for c in correspondences], float)
    p, err, proj = fit_camera(wp, ip, center, radius)
    return {"params": dict(zip(P_NAMES, [round(float(v), 3) for v in p])),
            "per_point_px": [round(float(e), 2) for e in err],
            "mean_px": round(float(err.mean()), 2),
            "worst_px": round(float(err.max()), 2),
            "projected": proj.round(1).tolist(),
            "n_points": len(correspondences)}


def overlay(ir: GeometryIR, params: np.ndarray, photo_path: str, out_path: str,
            size: int = 900) -> None:
    """孪生轮廓 (透视正确投影, 含全部面板边) 叠加实拍裁切."""
    world = fold_all(ir)
    allp = np.vstack(list(world.values()))
    lo, hi = allp.min(0), allp.max(0)
    center, radius = (lo + hi) / 2, float(np.linalg.norm(hi - lo)) / 2
    photo = Image.open(photo_path).convert("RGB")
    scale = size / max(photo.width, photo.height)
    photo = photo.resize((int(photo.width * scale), int(photo.height * scale)))
    p = params.copy()
    # 像素重映射: 拟合坐标系 (半幅320, 尺寸任意) → 叠加图尺寸
    p[4] = p[4] * scale
    p[5] = p[5] * scale
    p[6] = p[6] * scale
    canvas = photo.copy()
    d = ImageDraw.Draw(canvas)
    for pid, verts in world.items():
        pts = [tuple(project(v[None, :], p, center, radius)[0]) for v in verts]
        d.line(pts + [pts[0]], fill=(255, 90, 70), width=2)
    canvas.save(out_path, quality=92)
