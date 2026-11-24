"""probe16 — B06-P4 对抗性可辨识性分析 (GPT 咨询裁决: P4 完成后允许 CLOSED)。

P4-A 扩展雅可比谱: A = [Jθ, Jpose, Jfx, Jb(逐面共享偏移)], 尺度归一 SVD → 近零空间与 b 子空间的对齐度。
P4-B 对抗解对: 两组解 (θ,pose,b) 重投影差异 < 标注噪声, 但关键尺寸差 > 交付容差 → 信息条件不足的构造性证明。
P4-C 视角信息增量: 同一对抗噪声下 单视角/近重复三视角/互补三视角 的 ΔW 收缩。
P4-D 双率对账: 门禁关/开下的 自动交付率 与 错误自动交付率 (AUTO ∧ |ΔW|>1mm) — 不许只报错误减少量。
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))
from photo_dieline.measurement import (  # noqa: E402
    MODELS, eye_pos, observe, project, solve, to_world, capture_protocol_check, delivery_policy,
)

FX = 50.0 / 36.0 * 768.0
TRUTH = {"W": 45.0, "D": 45.0, "Hb": 100.0, "Hr": 12.0, "Ef": 14.0, "fin_gap_mm": 3.0}
GAB = MODELS["gable_top"]
TOL = 1.0
GROUPS = ([0, 1, 4, 5], [2, 3, 6, 7], [8, 9], [10, 11, 12, 13])   # B03 冻结逐面分组
CAM_S = {"az": math.radians(35), "el": math.radians(18), "roll": math.radians(-4), "d_eye": 0.81}
VIEWS_DUP = [(30, 16, -3, 0.80), (40, 20, -5, 0.82), (35, 14, -2, 0.79)]
VIEWS_COMP = [(35, 18, -4, 0.81), (140, 10, 3, 0.75), (270, 30, 0, 0.90)]


def ccam(t):
    return {"az": math.radians(t[0]), "el": math.radians(t[1]), "roll": math.radians(t[2]), "d_eye": t[3]}


def corr_obs(cam, seed, sigma_iso=0.5, sigma_face=2.0):
    """B03 冻结相关噪声: 各面共享 2px 偏移 + 0.5px i.i.d.。"""
    idx, uv, _ = observe(GAB, TRUTH, cam, FX)
    rng = np.random.default_rng(seed)
    u = uv + rng.normal(0, sigma_iso, uv.shape)
    pos = {int(k): i for i, k in enumerate(idx)}
    for g in GROUPS:
        rows = [pos[k] for k in g if k in pos]
        u[rows] += rng.normal(0, sigma_face, 2)
    return idx, u


def preds(res, idx):
    """解的位姿 + 真值几何? 不 — 用解自身 θ 重投影到该视角的观测关键点 (预测位置)。"""
    th = {**TRUTH, **res["anchors"], **res["theta"]}
    P, c = GAB["kp"](th)
    Pw = to_world(P, c)
    cam = res["cam"]
    eye = eye_pos(np.array(cam["T"]), cam["az"], cam["el"], cam["d_eye"])
    return project(Pw[idx], eye, cam["az"], cam["el"], cam["roll"], FX * cam["fx_scale"])


print("=== P4-A 扩展雅可比谱: b 子空间与近零空间对齐度 (干净解处线性化) ===")
idx, uv0, _ = observe(GAB, TRUTH, CAM_S, FX)
r0 = solve(GAB, idx, uv0, FX, {"Hb": 100.0}, 0.85)
th0 = {**TRUTH, **r0["theta"]}
P, c = GAB["kp"](th0)
Pw = to_world(P, c)
cam0 = r0["cam"]
eye0 = eye_pos(np.array(cam0["T"]), cam0["az"], cam0["el"], cam0["d_eye"])

PN = ["W", "D", "Hr", "Ef"]
x0 = np.array([th0[k] for k in PN] + [cam0["T"][0], cam0["T"][1], cam0["T"][2],
                                      cam0["az"], cam0["el"], cam0["roll"], cam0["d_eye"], 1.0])


def resid_x(xx):
    th = dict(zip(PN, xx[:4]))
    q = {**TRUTH, **th}
    Pq, cq = GAB["kp"](q)
    Pwq = to_world(Pq, cq)
    e = eye_pos(xx[4:7], xx[7], xx[8], xx[10])
    return (project(Pwq[idx], e, xx[7], xx[8], xx[9], FX * xx[11]) - uv0).ravel()


def resid_b(bb):
    u = uv0.copy()
    pos = {int(k): i for i, k in enumerate(idx)}
    for gi, g in enumerate(GROUPS):
        rows = [pos[k] for k in g if k in pos]
        u[rows] += bb[gi]
    return (project(Pw[idx], eye0, cam0["az"], cam0["el"], cam0["roll"], FX) - u).ravel()


eps = 1e-5
n_r = len(resid_x(x0))
Jx = np.zeros((n_r, len(x0)))
for j in range(len(x0)):
    dx = np.zeros_like(x0)
    dx[j] = eps * max(1.0, abs(x0[j]))
    Jx[:, j] = (resid_x(x0 + dx) - resid_x(x0 - dx)) / (2 * dx[j])
Jb = np.zeros((n_r, len(GROUPS)))
for j in range(len(GROUPS)):
    bb = np.zeros(len(GROUPS))
    bb[j] = eps
    Jb[:, j] = (resid_b(bb) - resid_b(-bb)) / (2 * eps)
A = np.hstack([Jx, Jb])
sc = np.abs(A).max(axis=0) + 1e-9
sv = np.linalg.svd(A / sc, compute_uv=False)
null_dirs = np.linalg.svd(A / sc, compute_uv=True)[2][-4:]        # 最右 4 个奇异方向
b_rows = []
pos = {int(k): i for i, k in enumerate(idx)}
for g in GROUPS:
    for k in g:
        if k in pos:
            b_rows += [2 * pos[k], 2 * pos[k] + 1]
B_mask = np.zeros(n_r, bool)
B_mask[b_rows] = True
align = []
U1 = np.linalg.svd(Jx / np.abs(Jx).max(), compute_uv=True)[0]     # 残差空间: 参数化子空间的一组正交基
for j in range(len(GROUPS)):
    jb = Jb[:, j]
    coef = U1.T @ jb
    align.append(float(np.linalg.norm(coef) / max(np.linalg.norm(jb), 1e-12)))
print(f" 奇异值谱 (归一): σ = {np.round(sv, 4).tolist()}")
print(f" 各面偏移列 b_j 落在参数化子空间内的能量占比: {np.round(align, 4).tolist()} "
      f"(占比≈1 ⇒ 该面偏移可被参数+位姿几乎完全吸收, 残差不可见)")

print("\n=== P4-B 对抗解对: 同一组观测, 两组解均拟合良好, 尺寸差 > 容差 ===")
idx_b, uv_b = corr_obs(CAM_S, seed=7)
rA = solve(GAB, idx_b, uv_b, FX, {"Hb": 100.0}, 0.85)             # 解 A: 锚 Hb=100
rB = solve(GAB, idx_b, uv_b, FX, {"Hb": 105.0}, 0.85)             # 解 B: 锚 Hb=105 (锚即真值假设, 无第三方仲裁)
thA = {**TRUTH, **rA["theta"]}
thB = {**TRUTH, **rB["theta"]}
pA = preds(rA, idx_b)
pB = preds(rB, idx_b)
rp_diff = float(np.abs(pA - pB).max())
print(f" 同一观测集上: 解A rms={rA['rms_px']:.3f}px W={thA['W']:.2f} | 解B rms={rB['rms_px']:.3f}px W={thB['W']:.2f}")
print(f" 两解预测的最大重投影差: {rp_diff:.3f}px | ΔW={abs(thA['W']-thB['W']):.2f}mm (容差 {TOL}mm)")
ok_b = rp_diff < 1.0 and abs(thA["W"] - thB["W"]) > TOL
print(f" → {'构造成功: 信息条件不足以区分两解, 差异超出交付容差' if ok_b else '本组未构造出'}")

print("\n=== P4-C 视角信息增量: 对抗噪声下 ΔW 收缩 (6 种子) ===")
for tag, cams in (("单视角", None), ("近重复三视角", VIEWS_DUP), ("互补三视角", VIEWS_COMP)):
    dws, autos = [], 0
    for s in range(6):
        c0 = ccam(cams[0]) if cams else CAM_S
        i1, u1 = corr_obs(c0, seed=100 + s)
        extra = []
        if cams:
            for t in cams[1:]:
                i2, u2 = corr_obs(ccam(t), seed=200 + s)
                extra.append((i2, u2, FX))
        r = solve(GAB, i1, u1, FX, {"Hb": 100.0}, 0.85, extra_views=extra or None)
        th = {**TRUTH, **r["theta"]}
        dws.append(abs(th["W"] - TRUTH["W"]))
        autos += delivery_policy(r, tol_mm=TOL, k=2.0,
                                 protocol=capture_protocol_check([ccam(t) for t in cams] if cams else [CAM_S])) == "AUTO"
    print(f" {tag:<8}: ΔW 中位={np.median(dws):.2f}mm 最大={max(dws):.2f}mm | AUTO {autos}/6")

print("\n=== P4-D 双率对账: 门禁关/开 (24 格 = 12 解 × 2) ===")
n_auto_off = n_wrong_off = n_auto_on = n_wrong_on = n = 0
for s in range(6):
    for noise in ("iid", "corr"):
        for cams in (None, VIEWS_DUP, VIEWS_COMP):
            cam0_ = ccam((35, 18, -4, 0.81))
            if noise == "iid":
                i1, u1, _ = observe(GAB, TRUTH, cam0_, FX)
                u1 = u1 + np.random.default_rng(300 + s).normal(0, 1.0, u1.shape)
                extra = []
                for t in (cams[1:] if cams else []):
                    i2, u2, _ = observe(GAB, TRUTH, ccam(t), FX)
                    extra.append((i2, u2 + np.random.default_rng(400 + s).normal(0, 1.0, u2.shape), FX))
            else:
                i1, u1 = corr_obs(ccam((35, 18, -4, 0.81)), seed=500 + s)
                extra = []
                for t in (cams[1:] if cams else []):
                    i2, u2 = corr_obs(ccam(t), seed=600 + s)
                    extra.append((i2, u2, FX))
            r = solve(GAB, i1, u1, FX, {"Hb": 100.0}, 0.85, extra_views=extra or None)
            th = {**TRUTH, **r["theta"]}
            wrong = abs(th["W"] - TRUTH["W"]) > TOL or abs(th["D"] - TRUTH["D"]) > TOL
            proto = capture_protocol_check([ccam((35, 18, -4, 0.81))] + ([ccam(t) for t in cams[1:]] if cams else []))
            n += 1
            if r["delivery"] == "MANUFACTURING_DIMENSIONS":       # 门禁关: 求解器说能交付就自动
                n_auto_off += 1
                n_wrong_off += wrong
            pol = delivery_policy(r, tol_mm=TOL, k=2.0, protocol=proto)
            if pol == "AUTO":                                     # 门禁开
                n_auto_on += 1
                n_wrong_on += wrong
print(f" 门禁关: AUTO {n_auto_off}/{n}, 其中错误 {n_wrong_off}")
print(f" 门禁开: AUTO {n_auto_on}/{n}, 其中错误 {n_wrong_on}")
print("PROBE16_DONE")
