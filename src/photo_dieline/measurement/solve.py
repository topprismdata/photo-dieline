"""B0 零训练参数化测量求解器: 单视角标注关键点 (2D) + 已知内参 + 可选实测尺寸 → 包装参数与相机位姿联合拟合。

三条设计合同 (审查后的修订版, 实验证据见 docs/reviews/recheck_2026-11-24/evidence/b0/):
1. 生成与求解两套独立投影实现: 生成端 = TDE Blender 驱动 + bpy world_to_camera_view; 求解端 = 本文件
   手写 numpy 针孔模型。两者逐点对账通过 (16 帧 × 14 点最大差 0.004px) 后求解器才可信。
2. 尺度锚定 (已知实测尺寸) 与待估参数严格分开; 无锚点时单视角整体尺度 ↔ 眼距简并, 求解会以近完美
   重投影给出整体偏移的尺寸 (实验中 −15%~−29%)。identifiable=False 必须如实上报, 不许静默交付。
3. 可辨识性判据: 归一化雅可比 → 信息矩阵; 位姿用 (注视点 3, 角度 3, 距离) 7 参数描述 6 自由度, 对包装
   参数子空间做 Schur 补 (消去位姿, 伪逆丢冗余方向) 后, 出现零特征值 = 存在数据约束不到的参数方向。

坐标约定 (与 TDE 驱动实测一致): OBJ 导入使几何绕 z 转 180° (x→−x, y→−y) 再平移到包围盒中心;
相机位于 注视点 + back·d_eye, back = (cos el·sin az, −cos el·cos az, sin el)。
"""
from __future__ import annotations

import math

import numpy as np

RES = 768                       # 求解内部归一分辨率 (与 TDE 渲染一致; project 的 res 参数可覆盖)
REL = [("W", "Hb"), ("D", "Hb"), ("Hr", "Hb"), ("Ef", "Hb")]   # gable 目标比例, 与 CNN 同口径
R_IMPORT = np.diag([-1.0, -1.0, 1.0])   # 驱动 obj_import(forward_axis=NEGATIVE_Y, up_axis=Z) 的实际旋转
DEFAULTS = {"W": 45.0, "D": 45.0, "Hb": 100.0, "Hr": 12.0, "Ef": 14.0, "H": 100.0}


def gable_keypoints(p):
    """gable_top 的 14 个关键点 (折叠坐标, mm): 盒体 8 角 + 两山墙尖 + 双鳍顶缘 4 角; 以及包围盒中心."""
    W, D, Hb, Hr, Ef, gap = (p[k] for k in ("W", "D", "Hb", "Hr", "Ef", "fin_gap_mm"))
    lean = math.asin(min(1.0, (gap / 2) / Ef)) if Ef > 0 else 0.0
    top = Hb + Hr + Ef * math.cos(lean)
    pts = [(sx * W / 2, y, z) for sx in (-1, 1) for y in (0.0, D) for z in (0.0, Hb)]
    pts += [(-W / 2, D / 2, Hb + Hr), (W / 2, D / 2, Hb + Hr)]
    pts += [(sx * W / 2, D / 2 + sy * Ef * math.sin(lean), top) for sx in (-1, 1) for sy in (-1, 1)]
    return np.array(pts), np.array([0.0, D / 2, top / 2])


def gable_faces(p):
    """gable_top 的可见性网格 (9 个面: 墙×4, 底, 双坡, 双鳍)."""
    W, D, Hb, Hr, Ef, gap = (p[k] for k in ("W", "D", "Hb", "Hr", "Ef", "fin_gap_mm"))
    lean = math.asin(min(1.0, (gap / 2) / Ef)) if Ef > 0 else 0.0
    top = Hb + Hr + Ef * math.cos(lean)
    r = Hb + Hr
    quads = [[(-W/2, 0, 0), (W/2, 0, 0), (W/2, 0, Hb), (-W/2, 0, Hb)],
             [(-W/2, D, 0), (W/2, D, 0), (W/2, D, Hb), (-W/2, D, Hb)],
             [(-W/2, 0, 0), (W/2, 0, 0), (W/2, D, 0), (-W/2, D, 0)],
             [(-W/2, 0, 0), (-W/2, D, 0), (-W/2, D, Hb), (-W/2, 0, Hb), (-W/2, D/2, r)],
             [(W/2, 0, 0), (W/2, D, 0), (W/2, D, Hb), (W/2, 0, Hb), (W/2, D/2, r)],
             [(-W/2, D, Hb), (W/2, D, Hb), (W/2, D/2, r), (-W/2, D/2, r)],
             [(-W/2, 0, Hb), (W/2, 0, Hb), (W/2, D/2, r), (-W/2, D/2, r)],
             [(-W/2, D/2, r), (W/2, D/2, r), (W/2, D/2 + Ef*math.sin(lean), top), (-W/2, D/2 + Ef*math.sin(lean), top)],
             [(-W/2, D/2, r), (W/2, D/2, r), (W/2, D/2 - Ef*math.sin(lean), top), (-W/2, D/2 - Ef*math.sin(lean), top)]]
    return _mesh(quads)


def cuboid_keypoints(p):
    """长方体: 8 个角 (W × D × H), 原点在底面中心下方."""
    W, D, H = p["W"], p["D"], p["H"]
    pts = [(sx * W / 2, y, z) for sx in (-1, 1) for y in (0.0, D) for z in (0.0, H)]
    return np.array(pts), np.array([0.0, D / 2, H / 2])


def cuboid_faces(p):
    """长方体的可见性网格 (6 个面)."""
    W, D, H = p["W"], p["D"], p["H"]
    return _mesh([[(-W/2, 0, 0), (W/2, 0, 0), (W/2, 0, H), (-W/2, 0, H)],
                  [(-W/2, D, 0), (W/2, D, 0), (W/2, D, H), (-W/2, D, H)],
                  [(-W/2, 0, 0), (W/2, 0, 0), (W/2, D, 0), (-W/2, D, 0)],
                  [(-W/2, 0, H), (W/2, 0, H), (W/2, D, H), (-W/2, D, H)],
                  [(-W/2, 0, 0), (-W/2, D, 0), (-W/2, D, H), (-W/2, 0, H)],
                  [(W/2, 0, 0), (W/2, D, 0), (W/2, D, H), (W/2, 0, H)]])


def _mesh(quads):
    V, F = [], []
    for q in quads:
        n = len(V)
        V += [(x / 1000, y / 1000, z / 1000) for x, y, z in q]
        F += [(n, n + 1, n + 2)] + [(n, n + 2, n + i) for i in range(3, len(q))]
    return np.array(V), np.array(F)


MODELS = {"gable_top": {"kp": gable_keypoints, "faces": gable_faces, "params": ("W", "D", "Hb", "Hr", "Ef"), "target": ("W", "D", "Hr", "Ef")},
          "cuboid": {"kp": cuboid_keypoints, "faces": cuboid_faces, "params": ("W", "D", "H"), "target": ("W", "D", "H")}}


def to_world(P, c):
    """折叠坐标 (mm) → 世界 (m): 绕 z 转 180° (导入器) + 平移到包围盒中心."""
    return (R_IMPORT @ (P - c).T).T / 1000.0 + c / 1000.0


def back_dir(az, el):
    """注视点 → 相机的单位方向 (与 TDE 驱动同式: eye = 注视点 + back·d)."""
    return np.array([math.cos(el) * math.sin(az), -math.cos(el) * math.cos(az), math.sin(el)])


def eye_pos(center, az, el, d_eye):
    return np.asarray(center, float) + back_dir(az, el) * d_eye


def basis(az, el, roll):
    """相机坐标系 (观察方向, 右, 上): 观察方向 = −back; 右 = 观察方向 × 世界 z; 上 = 右 × 观察方向; 再绕观察方向转 roll."""
    fwd = -back_dir(az, el)
    right = np.cross(fwd, [0.0, 0.0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    c, s = math.cos(roll), math.sin(roll)
    return fwd, right * c + up * s, -right * s + up * c


def project(P, eye, az, el, roll, fx, res=RES):
    """numpy 针孔模型 (图像 y 向下, 主点居中). 与 bpy world_to_camera_view 对账一致 (evidence/b0/camera_verify.json)."""
    fwd, right, up = basis(az, el, roll)
    v = P - eye
    z = v @ fwd
    return np.stack([fx * (v @ right) / z + res / 2, res / 2 - fx * (v @ up) / z], 1)


def visible(Pw, eye, faces_w):
    """被自身网格挡住的关键点不可标注 (trimesh 射线; 容差 1mm). 需要可选依赖 trimesh。"""
    import trimesh
    mesh = trimesh.Trimesh(*faces_w, process=False)
    out = []
    for q in Pw:
        d = q - eye
        dist = np.linalg.norm(d)
        hits = mesh.ray.intersects_location([eye], [d / dist], multiple_hits=True)[0]
        out.append(all(np.linalg.norm(h - eye) >= dist - 1e-3 for h in hits))
    return np.array(out)


def observe(model, p, cam, fx, res=RES):
    """生成端: 真值参数 + 真值相机 → (可见且在画面内的关键点编号, 无噪声图像坐标, 真实眼位)."""
    P, c = model["kp"](p)
    V, F = model["faces"](p)
    faces_w = ((R_IMPORT @ (V * 1000 - c).T).T / 1000.0 + c / 1000.0, F)
    Pw = to_world(P, c)
    eye = eye_pos(c / 1000.0, cam["az"], cam["el"], cam["d_eye"])
    uv = project(Pw, eye, cam["az"], cam["el"], cam["roll"], fx, res)
    idx = np.where(visible(Pw, eye, faces_w) & (uv[:, 0] > 2) & (uv[:, 0] < res - 2) & (uv[:, 1] > 2) & (uv[:, 1] < res - 2))[0]
    return idx, uv[idx], eye


def solve(model, obs_idx, obs_uv, fx, anchors, d0, n_az=6):
    """联合拟合: 未锚定的包装参数 + 相机 (注视点 3, 方位, 俯仰, 滚转, 眼距)。
    anchors: {参数名: 实测值 mm} (尺度锚定, 与待估参数严格分开)。多起点 (方位 × 俯仰), 取代价最低解。
    返回 identifiable=False 表示存在数据约束不到的参数方向 (典型: 无锚点时的整体尺度), 不得采信尺寸。"""
    try:
        from scipy.optimize import least_squares
    except ImportError as exc:  # 可选依赖: pip install photo-dieline[measure]
        raise ImportError("measurement.solve 需要 scipy: pip install photo-dieline[measure]") from exc
    pnames = model["params"]
    names = [n for n in pnames if n not in anchors]

    def params(theta):
        q = {k: DEFAULTS[k] for k in ("W", "D", "Hb", "Hr", "Ef", "H")}
        q.update(anchors)
        q["fin_gap_mm"] = 3.0
        q.update(zip(names, theta))
        return q

    def resid(x):
        P, c = model["kp"](params(x[:len(names)]))
        eye = eye_pos(x[len(names):len(names) + 3], x[-4], x[-3], x[-1])
        uv = project(to_world(P, c)[obs_idx], eye, x[-4], x[-3], x[-2], fx)
        return (uv - obs_uv).ravel()

    lo = np.array([8.0] * len(names) + [-0.6, -0.6, -0.6, 0.0, -0.35, -0.8, 0.03])
    hi = np.array([500.0] * len(names) + [0.6, 0.6, 0.6, 2 * math.pi, 1.35, 0.8, 6.0])
    th0 = np.array([DEFAULTS[n] for n in names])
    c0 = model["kp"](params(th0))[1] / 1000.0
    sols = []
    for k in range(n_az):
        for el0 in (0.15, 0.55):
            x0 = np.concatenate([th0, c0, [2 * math.pi * k / n_az, el0, 0.0, d0]])
            try:
                r = least_squares(resid, np.clip(x0, lo + 1e-6, hi - 1e-6), bounds=(lo, hi), loss="soft_l1", f_scale=2.0, max_nfev=300)
            except Exception:
                continue
            sols.append(r)
    if not sols:
        return {"ok": False, "reason": "no_start_converged"}
    best = min(sols, key=lambda r: r.cost)
    theta = dict(zip(names, (float(v) for v in best.x[:len(names)])))
    distinct = sum(1 for r in sols if r is not best and r.cost <= best.cost + 1e-6
                   and any(abs(r.x[i] - best.x[i]) > 1.0 for i in range(len(names))))
    # 可辨识性: 见模块 docstring 合同 3
    n = len(names)
    scale = np.abs(best.x) + np.array([10.0] * n + [0.1, 0.1, 0.1, 1.0, 1.0, 1.0, 0.1])
    Jn = best.jac / scale
    H = Jn.T @ Jn
    Htt, Htp, Hpp = H[:n, :n], H[:n, n:], H[n:, n:]
    S = Htt - Htp @ np.linalg.pinv(Hpp, rcond=1e-10) @ Htp.T
    ev = np.linalg.eigvalsh((S + S.T) / 2)
    kept = ev[ev > 1e-12 * max(float(ev.max()), 1e-300)]
    cond_theta = float(kept.max() / kept.min()) if len(kept) == n else float("inf")
    sv = np.linalg.svd(Jn, compute_uv=False)
    return {"ok": True, "theta": theta, "anchors": dict(anchors),
            "cam": {"T": best.x[n:n + 3].tolist(), "az": float(best.x[-4]), "el": float(best.x[-3]),
                    "roll": float(best.x[-2]), "d_eye": float(best.x[-1])},
            "rms_px": float(math.sqrt(np.mean(best.fun ** 2) / 2)), "cost": float(best.cost),
            "cond": float(sv[0] / sv[-1]) if sv[-1] > 0 else float("inf"),
            "cond_theta": cond_theta, "identifiable": bool(cond_theta < 1e6), "n_distinct_minima": int(distinct)}


def ratio_mae(model, theta, truth):
    """与 CNN 同口径的指标: 目标比例向量的 raw MAE."""
    rel = REL if model is MODELS["gable_top"] else [("W", "H"), ("D", "H")]
    return float(np.mean([abs(theta[a] / theta[b] - truth[a] / truth[b]) for a, b in rel]))
