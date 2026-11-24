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
DEFAULTS = {"W": 45.0, "D": 45.0, "Hb": 100.0, "Hr": 12.0, "Ef": 14.0, "H": 100.0, "fin_gap_mm": 3.0}


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
try:  # R3-A4 约束传播: 拟合参数违反模板声明域 → 不得交付确定尺寸 (parametric 不反向依赖 measurement, 无环)
    from ..parametric.gable_top import DEFAULTS as _gable_defaults
    from ..parametric.gable_top import param_domain_violations as _gable_param_domain_violations

    def _gable_domain_violations(q):
        # 测量层只携带几何子集 (无 glue_w/board_t) — 以模板默认值补全后再过域检查
        return _gable_param_domain_violations({**_gable_defaults, **q})

    MODELS["gable_top"]["domain"] = _gable_domain_violations
except ImportError:
    pass


def _gable_measurement_domain(q):
    """D1 测量有效域 (R4 咨询 DOM-02: 三层域契约 D2⊆D1⊆D0)。
    D0 = param_domain_violations (数学声明域, 不动); D1 = 测量可辨识性边界; D2 = 自动交付门 (delivery_policy)。
    V1.0 保守运行边界: lean = asin(gap/(2Ef)) ≤ 75° ⇔ gap ≤ 2·sin75°·Ef = 1.9319·Ef (DOM-01 核对的等价阈值)。
    依据: lean→90° 鳍高→0 退化形体触发其他门 (probe13 近边界发现); 75° 是运行边界而非普适物理边界
    (灵敏度曲线待 R5 真实数据补充后修订)。"""
    out = []
    gap, Ef = q.get("fin_gap_mm"), q.get("Ef")
    if isinstance(gap, (int, float)) and isinstance(Ef, (int, float)) and gap > 0 and Ef > 0:
        lean = math.degrees(math.asin(min(1.0, (gap / 2.0) / Ef)))
        if lean > 75.0:
            out.append(f"lean={lean:.1f}° > 75° (D1 测量有效域 V1.0 保守边界, gap ≤ 1.9319·Ef): 鳍近退化, 测量转人工")
    return out


MODELS["gable_top"]["meas_domain"] = _gable_measurement_domain


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


def solve(model, obs_idx, obs_uv, fx, anchors, d0, n_az=6, free_fin_gap=False, noise_px=1.0, extra_views=None, free_fx=False, point_clusters=None):
    """联合拟合: 未锚定的包装参数 + 相机 (注视点 3, 方位, 俯仰, 滚转, 眼距)。
    anchors: {参数名: 实测值 mm} (尺度锚定, 与待估参数严格分开)。多起点 (方位 × 俯仰), 取代价最低解。
    free_fin_gap: gable 的 fin_gap_mm 改为自由参数 (先验消融; 无锚点时应重新暴露绝对尺度自由度)。
    noise_px: 关键点噪声假设 (参数级误差棒的 σ 缩放)。
 extra_views: [(obs_idx, obs_uv, fx), ...] 附加视角; 参数跨视角共享, 位姿逐视角独立。
 free_fx: 附加一个共享焦距乘数 s (B0-B"部分未知内参"; s 与眼距耦合, 会进入 Schur 位姿块被边缘化)。
 point_clusters: {关键点索引: 聚类 id} (如逐面分组) → 启用 sandwich 稳健协方差 sigma_mm_robust
 (Liang-Zeger 聚类三明治 + HC1 校正; 相关噪声下 i.i.d. 误差棒过于乐观, R3 B03/B06 实证)。

    R3 WP1 合同 (round3_verdict.md §2):
    - scale_source: MEASURED_ANCHOR (有实测边) / TEMPLATE_PRIOR_ANCHOR (gable 隐含 fin_gap=3mm 绝对先验,
      "无锚点"其实不是无尺度约束) / NO_METRIC_ANCHOR (真·无绝对长度)。
    - identifiability: IDENTIFIABLE / WEAK / UNIDENTIFIABLE (参数子空间 Schur 补, 无量纲归一化;
      阈值 1e4/1e6 是数值诊断, 不是精度标准)。
    - sigma_mm: 参数级 1σ 误差棒 (C ≈ S⁻¹ 局部线性近似; 秩亏方向显式 inf, 不给虚假精度)。
      交付决策应对比 sigma_mm 与特征容差, 而不是只看条件数。
    - delivery: MANUFACTURING_DIMENSIONS (实测锚 + 满秩良态) / INSUFFICIENT_PRECISION (实测锚但 WEAK,
      误差棒可能超容差) / PRIOR_DEPENDENT_ESTIMATE (仅模板先验, 只可作研究估计) / REFUSED
      (NO_METRIC_ANCHOR 或 UNIDENTIFIABLE, 禁止交付确定尺寸)。
      R3-A4 增补: OUT_OF_DOMAIN (拟合参数违反模板声明域) / 失配门 rms_px > 2*noise_px+0.2px → INSUFFICIENT_PRECISION
      (域外真值会跑飞到域内高置信错误解, probe14-b); 无效锚键名直接拒绝 (unknown_anchor_keys)。"""
    try:
        from scipy.optimize import least_squares
    except ImportError as exc:  # 可选依赖: pip install photo-dieline[measure]
        raise ImportError("measurement.solve 需要 scipy: pip install photo-dieline[measure]") from exc
    pnames = model["params"]
    unknown = sorted(k for k in anchors if k not in pnames and k != "fin_gap_mm")
    if unknown:  # R3-A4: 无效锚 (键名拼错/模型不消费的参数) 必须拒绝, 不得静默接受
        return {"ok": False, "reason": f"unknown_anchor_keys: {unknown}",
                "delivery": "NO_GO", "sigma_mm": {}, "sigma_mm_robust": {}}
    names = [n for n in pnames if n not in anchors]
    if free_fin_gap and model is MODELS["gable_top"] and "fin_gap_mm" not in names:
        names = names + ["fin_gap_mm"]
    views = [(obs_idx, obs_uv, fx)] + [tuple(v) for v in (extra_views or [])]
    nv = len(views)

    def params(theta):
        q = {k: DEFAULTS[k] for k in ("W", "D", "Hb", "Hr", "Ef", "H")}
        q.update(anchors)
        if "fin_gap_mm" not in names:
            q["fin_gap_mm"] = 3.0
        q.update(zip(names, theta))
        return q

    def resid(x):
        s = x[-1] if free_fx else 1.0
        P, c = model["kp"](params(x[:len(names)]))
        Pw = to_world(P, c)
        out = []
        for v, (idx, uv, f) in enumerate(views):
            o = len(names) + 7 * v
            eye = eye_pos(x[o:o + 3], x[o + 3], x[o + 4], x[o + 6])
            out.append((project(Pw[idx], eye, x[o + 3], x[o + 4], x[o + 5], f * s) - uv).ravel())
        return np.concatenate(out)

    pose_lo = [-0.6, -0.6, -0.6, 0.0, -0.35, -0.8, 0.03]
    pose_hi = [0.6, 0.6, 0.6, 2 * math.pi, 1.35, 0.8, 6.0]
    lo = np.array([0.5 if n == "fin_gap_mm" else 8.0 for n in names] + pose_lo * nv + ([0.5] if free_fx else []))
    hi = np.array([10.0 if n == "fin_gap_mm" else 500.0 for n in names] + pose_hi * nv + ([2.0] if free_fx else []))
    th0 = np.array([DEFAULTS[n] for n in names])
    c0 = model["kp"](params(th0))[1] / 1000.0
    sols = []
    for k in range(n_az):
        for el0 in (0.15, 0.55):
            x0 = list(th0)
            for v in range(nv):
                x0 += [c0[0], c0[1], c0[2], 2 * math.pi * k / n_az + 0.9 * v, el0, 0.0, d0]
            if free_fx:
                x0 += [1.0]
            x0 = np.array(x0)
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
    scale = np.abs(best.x) + np.array([10.0] * n + [0.1, 0.1, 0.1, 1.0, 1.0, 1.0, 0.1] * nv + ([1.0] if free_fx else []))
    Jn = best.jac / scale
    H = Jn.T @ Jn
    Htt, Htp, Hpp = H[:n, :n], H[:n, n:], H[n:, n:]
    S = Htt - Htp @ np.linalg.pinv(Hpp, rcond=1e-10) @ Htp.T
    ev = np.linalg.eigvalsh((S + S.T) / 2)
    kept = ev[ev > 1e-12 * max(float(ev.max()), 1e-300)]
    full_rank = len(kept) == n
    cond_theta = float(kept.max() / kept.min()) if full_rank else float("inf")
    level = "UNIDENTIFIABLE" if (not full_rank or cond_theta >= 1e6) else ("WEAK" if cond_theta > 1e4 else "IDENTIFIABLE")
    # 参数级 1σ (mm): 无量纲 S⁻¹ 对角 → 物理单位 = sqrt(inv(S)_ii)/scale_i × noise_px; 秩亏方向显式 inf
    Sinv = np.linalg.inv(S) if full_rank else None
    sigma = {nm: (float(math.sqrt(max(Sinv[i, i], 0.0)) / scale[i] * noise_px) if full_rank else float("inf"))
             for i, nm in enumerate(names)}
    # Sandwich 稳健协方差 (聚类三明治): 假定逐聚类相关+异方差, 不依赖 i.i.d.; 残差自带真实噪声尺度。
    # 必须在 θ 边缘空间做: 全空间 H 含冗余位姿方向 (cond ~1e18), pinv 截断会毁掉 θθ 块;
    # 投影得分 w_k = [I | −H_tp·H_pp⁺]·u_k, 则 i.i.d. 下 E[Σw_k w_kᵀ] = S·σ² 精确还原 S 路线。
    sigma_r = None
    if point_clusters and full_rank:
        rows = int(best.fun.shape[0])
        p_tot = int(best.jac.shape[1])
        if rows > p_tot:
            cid = np.full(rows, -1, dtype=int)
            off = 0
            for idx, _u, _f in views:
                for i, kp in enumerate(idx):
                    cid[off + 2 * i] = cid[off + 2 * i + 1] = int(point_clusters.get(int(kp), -1))
                off += 2 * len(idx)
            A = np.concatenate([np.eye(n), -Htp @ np.linalg.pinv(Hpp, rcond=1e-10)], axis=1)  # n×p_tot
            # soft_l1 的 best.jac 已被 ρ′ 加权 → 数值重算原始 J (三明治要求未加权得分)
            J_raw = np.empty((rows, p_tot))
            for j in range(p_tot):
                h = 1e-6 * max(1.0, abs(best.x[j]))
                xp, xm = best.x.copy(), best.x.copy()
                xp[j] += h
                xm[j] -= h
                J_raw[:, j] = (resid(xp) - resid(xm)) / (2 * h)
            scores_raw = (J_raw / scale) * best.fun[:, None]
            # HC3 杠杆校正 (小样本 m=2·关键点, 平均杠杆 ~p/m 大): 逐行 ψ_i/(1−h_i)
            U_, S_, Vt_ = np.linalg.svd(J_raw / scale, full_matrices=False)
            keep_ = S_ > 1e-12 * max(float(S_.max()), 1e-300)
            hat_diag = np.sum(U_[:, keep_] ** 2, axis=1)
            scores = scores_raw / np.clip(1.0 - hat_diag, 1e-3, None)[:, None]
            W = np.zeros((n, n))
            for c in np.unique(cid):
                if c < 0:
                    continue
                w = A @ scores[cid == c].sum(axis=0)
                W += np.outer(w, w)
            V = (Sinv @ W @ Sinv)                                 # HC3 已含杠杆校正, 不再叠 HC1
            sigma_r = {nm: float(math.sqrt(max(V[i, i], 0.0)) / scale[i]) for i, nm in enumerate(names)}
    if anchors:
        scale_source = "MEASURED_ANCHOR"
    elif model is MODELS["gable_top"] and not free_fin_gap:
        scale_source = "TEMPLATE_PRIOR_ANCHOR"      # fin_gap=3mm 是绝对长度先验, "无锚点"并非无尺度约束
    else:
        scale_source = "NO_METRIC_ANCHOR"
    rms_px = float(math.sqrt(np.mean(best.fun ** 2) / 2))
    # R3-A4 约束传播: ① 拟合参数违反模板声明域 (参数界内通常不可达, 挂检查作不变量);
    # ② 残差超过声明噪声 2σ+0.2px → 系统性失配 (域外真值会跑飞到域内高置信错误解, probe14-b 实证)。
    dom_fn = model.get("domain")
    violations = list(dom_fn(params([best.x[i] for i in range(len(names))]))) if dom_fn else []
    misfit_px = rms_px > 2.0 * noise_px + 0.2
    md_fn = model.get("meas_domain")
    meas_violations = list(md_fn(params([best.x[i] for i in range(len(names))]))) if md_fn else []
    if level == "UNIDENTIFIABLE" or scale_source == "NO_METRIC_ANCHOR":
        delivery = "REFUSED"
    elif scale_source == "TEMPLATE_PRIOR_ANCHOR":
        delivery = "PRIOR_DEPENDENT_ESTIMATE"
    elif violations:
        delivery = "OUT_OF_DOMAIN"
    elif meas_violations:
        delivery = "INSUFFICIENT_PRECISION"          # D1 测量有效域外 (近退化): 转人工, 不自动交付
    elif misfit_px:
        delivery = "INSUFFICIENT_PRECISION"          # 实测锚在但几何失配, 误差棒无意义 → 人工复核
    elif level == "WEAK":
        delivery = "INSUFFICIENT_PRECISION"          # 实测锚在, 但误差棒可能超特征容差 → 交付决策看 sigma_mm
    else:
        delivery = "MANUFACTURING_DIMENSIONS"
    sv = np.linalg.svd(Jn, compute_uv=False)
    return {"ok": True, "theta": theta, "anchors": dict(anchors),
            "cam": {"T": best.x[n:n + 3].tolist(), "az": float(best.x[n + 3]), "el": float(best.x[n + 4]),
                    "roll": float(best.x[n + 5]), "d_eye": float(best.x[n + 6]),
                    "fx_scale": float(best.x[-1]) if free_fx else 1.0},
            "cams": [{"T": best.x[n + 7 * v:n + 7 * v + 3].tolist(), "az": float(best.x[n + 7 * v + 3]),
                      "el": float(best.x[n + 7 * v + 4]), "roll": float(best.x[n + 7 * v + 5]),
                      "d_eye": float(best.x[n + 7 * v + 6])} for v in range(nv)],
            "rms_px": float(math.sqrt(np.mean(best.fun ** 2) / 2)), "cost": float(best.cost),
            "cond": float(sv[0] / sv[-1]) if sv[-1] > 0 else float("inf"),
            "cond_theta": cond_theta, "identifiable": level != "UNIDENTIFIABLE",
            "identifiability": level, "scale_source": scale_source, "delivery": delivery,
            "domain_violations": violations, "misfit_px": misfit_px,
            "measurement_violations": meas_violations,
            "sigma_mm": sigma, "sigma_mm_robust": sigma_r,
            "sigma_inflation": (float(np.median([sigma_r[k] / max(sigma[k], 1e-9) for k in names
                                                 if sigma_r and math.isfinite(sigma_r[k]) and math.isfinite(sigma[k])]))
                                if sigma_r else None),
            "n_distinct_minima": int(distinct)}


def ratio_mae(model, theta, truth):
    """与 CNN 同口径的指标: 目标比例向量的 raw MAE."""
    rel = REL if model is MODELS["gable_top"] else [("W", "H"), ("D", "H")]
    return float(np.mean([abs(theta[a] / theta[b] - truth[a] / truth[b]) for a, b in rel]))


def capture_protocol_check(cams, min_az_spread_deg=25.0):
    """采集协议层 B06 对策 (R4): 近重复视角下逐面吸收偏移不可检 (B05/B06 实证: 近重复超容差 0.37 vs 互补 0.07)。
    方位角圆跨度 < min_az_spread_deg 的多视角集判 NEAR_DUP → 须降级人工; 单视角 SINGLE_VIEW。"""
    azs = sorted(math.degrees(c["az"]) % 360.0 for c in cams)
    if len(azs) <= 1:
        return {"status": "SINGLE_VIEW", "az_spread_deg": 0.0}
    gaps = [b - a for a, b in zip(azs, azs[1:])] + [360.0 - azs[-1] + azs[0]]
    spread = 360.0 - max(gaps)
    return {"status": "NEAR_DUP" if spread < min_az_spread_deg else "OK", "az_spread_deg": float(spread)}


def cross_view_closure(model, obs_list, anchors, d0):
    """测站闭合差 (摄影测量 multi-station QC): 逐视角独立解 (同锚), 维度估计跨站分歧 (mm)。
    互补视角下相关偏移吸收方向不同 → 分歧暴露系统误差; 近重复视角分歧天然小 (先过 capture_protocol_check)。"""
    per_view = []
    for idx, uv, fx in obs_list:
        r = solve(model, idx, uv, fx, anchors, d0)
        if not r.get("ok"):
            continue
        th = {**r["anchors"], **r["theta"]}
        per_view.append({"dims": {k: float(th[k]) for k in ("W", "D") if k in th},
                         "sigma": {k: r["sigma_mm"][k] for k in ("W", "D") if k in r["sigma_mm"] and math.isfinite(r["sigma_mm"][k])}})
    out = {"n_views_solved": len(per_view), "W_spread_mm": None, "D_spread_mm": None,
           "W_closure_over_sigma": None, "D_closure_over_sigma": None}
    for k in ("W", "D"):
        vals = [d["dims"][k] for d in per_view if k in d["dims"]]
        sig = [d["sigma"][k] for d in per_view if k in d["sigma"]]
        if len(vals) >= 2:
            out[f"{k}_spread_mm"] = float(max(vals) - min(vals))
            out[f"{k}_per_view"] = [round(v, 2) for v in vals]
        if len(vals) >= 2 and len(sig) == len(vals):
            denom = math.sqrt(sum(s * s for s in sig))     # 跨站合成精度: 闭合差/√Σσ² (深度退化站归一)
            out[f"{k}_closure_over_sigma"] = float(out[f"{k}_spread_mm"] / denom) if denom > 0 else None
    return out


def delivery_policy(res, tol_mm=1.0, k=2.0, protocol=None):
    """R4 WP1 第 III 层: σ 对比特征容差的自动交付门槛 (优先用稳健 σ, 缺则退 i.i.d. σ)。
    AUTO: 实测锚 + 可辨识 + max(σ_W,σ_D) ≤ tol/k (k=2 安全系数), 可自动交付;
    MANUAL: 实测锚可辨识但误差棒超容差 → 转人工复核; NO_GO: 拒绝/仅先验/不可辨识。
    注意 B0-B 冻结结论: TOL=1mm 时单视角固有精度 1–4mm → 大量 MANUAL 是正确行为 (精度不足即不自动)。
    protocol: capture_protocol_check 的返回; NEAR_DUP → 封顶 MANUAL (B06 类沉默错误在近重复视角下不可检)。"""
    if protocol is not None and protocol.get("status") == "NEAR_DUP":
        return "MANUAL"
    if not res.get("ok"):
        return "NO_GO"
    if res.get("delivery") in ("REFUSED", "PRIOR_DEPENDENT_ESTIMATE"):
        return "NO_GO"
    if res.get("delivery") == "INSUFFICIENT_PRECISION":
        return "MANUAL"
    s = res.get("sigma_mm_robust") or res.get("sigma_mm") or {}
    dims = [s[k] for k in ("W", "D") if k in s and math.isfinite(s.get(k, float("inf")))]
    if res.get("delivery") != "MANUFACTURING_DIMENSIONS" or not dims:
        return "NO_GO"
    return "AUTO" if max(dims) <= tol_mm / k else "MANUAL"
