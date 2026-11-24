"""R5 真实数据试验 — 棋盘格内参标定 (协议 §2) 与合成正控制自检。

纪律 (real-photo-camera-calibration-identifiability 技能): 正控制先行 — 标定器先过合成自检
(已知 GT 内参 + 注入噪声 + 回收, 机器验证恢复正确盆), 再碰真实数据。自检是机器验证,
不是精度承诺; 单帧绝对 f/距离不可辨性结论见 docs/reviews/recheck_2026-11-24/。

单位约定: 物理坐标 mm (与 solve.py 一致); 像素坐标/焦距 px (cv2 口径)。
"""

import math

import numpy as np

PATTERN = (9, 6)  # 内角点数 (cv2 口径), 方格边长见 square_mm 参数


def _object_points(pattern=PATTERN, square_mm=10.0):
    cols, rows = pattern
    pts = np.zeros((cols * rows, 3), np.float64)
    uv = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2)
    pts[:, :2] = ((uv - np.array([(cols - 1) / 2.0, (rows - 1) / 2.0])) * square_mm)
    return pts


def selfcheck(pattern=PATTERN, square_mm=10.0, n_poses=8, noise_px=0.15, seed=0):
    """合成正控制: 已知 K + 平面位姿 → 投影角点 + N(0,noise) → calibrateCamera 回收。
    返回机器验证字段; ok 判据 = fx/fy 相对误差 <1%, |cx/cy 误差| <2px, rms <1px (噪声级)。"""
    import cv2

    rng = np.random.default_rng(seed)
    image_size = (3000, 2000)
    K_gt = np.array([[3000.0, 0, 1500.0], [0, 3000.0, 1000.0], [0, 0, 1.0]])
    objp = _object_points(pattern, square_mm)
    imgps, objps = [], []
    for i in range(n_poses):
        rx, ry = rng.uniform(-0.25, 0.25, 2)
        R, _ = cv2.Rodrigues(np.array([rx, ry, rng.uniform(-0.3, 0.3)]))
        t = np.array([rng.uniform(-40, 40), rng.uniform(-30, 30), rng.uniform(180, 260)])
        uv, _ = cv2.projectPoints(objp, cv2.Rodrigues(R)[0], t, K_gt, None)
        uv = uv.reshape(-1, 2) + rng.normal(0, noise_px, uv.reshape(-1, 2).shape)
        if uv.min() < 0 or uv[:, 0].max() > image_size[0] or uv[:, 1].max() > image_size[1]:
            return {"ok": False, "reason": f"pose {i} projected outside image"}
        imgps.append(uv.astype(np.float32))
        objps.append(objp.astype(np.float32))
    rms, K, _, _, _ = cv2.calibrateCamera(objps, imgps, image_size, None, None)
    fx_rel = abs(K[0, 0] - K_gt[0, 0]) / K_gt[0, 0]
    fy_rel = abs(K[1, 1] - K_gt[1, 1]) / K_gt[1, 1]
    c_err = max(abs(K[0, 2] - K_gt[0, 2]), abs(K[1, 2] - K_gt[1, 2]))
    ok = fx_rel < 0.01 and fy_rel < 0.01 and c_err < 2.0 and rms < 1.0
    return {"ok": ok, "fx_rel_err": float(fx_rel), "fy_rel_err": float(fy_rel),
            "c_err_px": float(c_err), "rms_px": float(rms), "noise_px": noise_px,
            "n_poses": n_poses}


def calibrate(image_paths, pattern=PATTERN, square_mm=10.0):
    """真实棋盘格图序列 → 内参。objectPoints 用 mm (square_mm), K 单位 px。
    先试 SB 检测器, 失败回退标准检测 + 亚像素精化。任意图失败即整体 FAIL (协议: 每 session 一次)。"""
    import cv2

    objp = _object_points(pattern, square_mm).astype(np.float32)
    objps, imgps, size = [], [], None
    for p in image_paths:
        im = cv2.imread(str(p))
        if im is None:
            return {"ok": False, "reason": f"unreadable image: {p}"}
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        size = (gray.shape[1], gray.shape[0])
        found, corners = cv2.findChessboardCornersSB(gray, pattern, flags=0)
        if not found:
            found, corners = cv2.findChessboardCorners(gray, pattern, None)
            if not found:
                return {"ok": False, "reason": f"pattern not found: {p}"}
            crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.001)
            corners = cv2.cornerSubPix(gray, corners, (5, 5), (-1, -1), crit)
        objps.append(objp)
        imgps.append(corners)
    rms, K, dist, _, _ = cv2.calibrateCamera(objps, imgps, size, None, None)
    return {"ok": True, "K": K.tolist(), "dist": dist.ravel().tolist(),
            "rms_px": float(rms), "n_images": len(objps), "image_size": list(size),
            "fx_px": float(K[0, 0]), "fy_px": float(K[1, 1]),
            "note": "solve.py 的 fx 以 px 计 — 传 fx=K[0,0] 前核对 observe/project 的 res 约定"}
