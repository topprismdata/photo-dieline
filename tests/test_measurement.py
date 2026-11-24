"""B0 参数化测量求解器合同测试 (GPT 复查 5.3-2: 参数化逆向拟合基线)。"""
import math

import numpy as np
import pytest

from photo_dieline.measurement import MODELS, delivery_policy, observe, ratio_mae, solve

# 与 experiments 一致的相机口径: equiv_focal → fx, 眼距 = 距离 × 1.35 (ADJ_FOV)
FX = 50.0 / 36.0 * 768.0
CUBOID_CAM = {"az": 0.6, "el": 0.4, "roll": 0.0, "d_eye": 0.5}
GABLE_PARAMS = {"W": 45.0, "D": 45.0, "Hb": 100.0, "Hr": 12.0, "Ef": 14.0, "fin_gap_mm": 3.0}


def _gable_cam():
    return {"az": math.radians(28.0), "el": math.radians(18.0), "roll": math.radians(-4.0), "d_eye": 0.6 * 1.35}


def test_noise_free_recovery_exact():
    """无噪声 + 一条实测边: 参数恢复须精确 (验收判据: 参数误差 <= 0.01mm, 重投影 <= 0.001px)。"""
    cub = MODELS["cuboid"]
    pc = {"W": 80.0, "D": 50.0, "H": 120.0}
    idx, uv, _ = observe(cub, pc, CUBOID_CAM, FX)
    assert len(idx) >= 6
    r = solve(cub, idx, uv, FX, {"H": pc["H"]}, 0.6)
    assert r["ok"] and r["identifiable"]
    assert abs(r["theta"]["W"] - pc["W"]) <= 0.01 and abs(r["theta"]["D"] - pc["D"]) <= 0.01
    assert r["rms_px"] <= 0.001 and r["n_distinct_minima"] == 0

    gab = MODELS["gable_top"]
    idx, uv, _ = observe(gab, GABLE_PARAMS, _gable_cam(), FX)
    assert len(idx) >= 6
    r = solve(gab, idx, uv, FX, {"Hb": GABLE_PARAMS["Hb"]}, 0.8)
    assert r["ok"] and r["identifiable"]
    for k in ("W", "D", "Hr", "Ef"):
        assert abs(r["theta"][k] - GABLE_PARAMS[k]) <= 0.01, k
    assert r["rms_px"] <= 0.001


def test_unanchored_scale_flagged_not_silent():
    """无尺度锚点: 单视角整体尺度不可辨识, 求解器必须如实标记 (低重投影 ≠ 尺寸正确)。"""
    cub = MODELS["cuboid"]
    pc = {"W": 80.0, "D": 50.0, "H": 120.0}
    idx, uv, _ = observe(cub, pc, CUBOID_CAM, FX)
    r = solve(cub, idx, uv, FX, {}, 0.6)
    assert r["ok"] and not r["identifiable"]   # 尺度方向无数据约束 → 拒绝交付确定解
    assert abs(r["rms_px"]) < 1e-6             # 重投影近完美 — 恰是必须上报的陷阱


def test_measured_edge_beats_cnn_tolerance_at_realistic_noise():
    """σ=1px 关键点噪声 (现实点选精度): 一条实测边的比例 MAE 须显著优于现役 CNN (同帧 0.0314)。"""
    rng = np.random.default_rng(7)
    gab = MODELS["gable_top"]
    idx, uv, _ = observe(gab, GABLE_PARAMS, _gable_cam(), FX)
    r = solve(gab, idx, uv + rng.normal(0, 1.0, uv.shape), FX, {"Hb": GABLE_PARAMS["Hb"]}, 0.8)
    assert r["ok"] and r["identifiable"]
    th = {**r["anchors"], **r["theta"]}
    mae = ratio_mae(gab, th, GABLE_PARAMS)
    assert mae < 0.0314 / 2, mae
    for k in ("W", "D", "Hr", "Ef"):
        assert abs(th[k] - GABLE_PARAMS[k]) < 3.0, (k, th[k])


def test_scale_source_and_delivery_contract():
    """R3 WP1 合同: 尺度来源分级 + 交付处置 (无绝对长度 → REFUSED; 仅模板先验 → 只作研究估计)。"""
    cub, gab = MODELS["cuboid"], MODELS["gable_top"]
    pc = {"W": 80.0, "D": 50.0, "H": 120.0}
    idx, uv, _ = observe(cub, pc, CUBOID_CAM, FX)
    r = solve(cub, idx, uv, FX, {}, 0.6)
    assert r["scale_source"] == "NO_METRIC_ANCHOR" and r["delivery"] == "REFUSED"
    assert r["identifiability"] == "UNIDENTIFIABLE" and all(math.isinf(v) for v in r["sigma_mm"].values())

    idx, uv, _ = observe(gab, GABLE_PARAMS, _gable_cam(), FX)
    r = solve(gab, idx, uv, FX, {}, 0.8)
    assert r["scale_source"] == "TEMPLATE_PRIOR_ANCHOR" and r["delivery"] == "PRIOR_DEPENDENT_ESTIMATE"

    r = solve(gab, idx, uv, FX, {"Hb": GABLE_PARAMS["Hb"]}, 0.8)
    assert r["scale_source"] == "MEASURED_ANCHOR" and r["delivery"] == "MANUFACTURING_DIMENSIONS"

    # fin_gap 转自由参数: 模板先验消失, 无锚点须重新暴露不可辨识 (R3 §2.2 第三组条件)
    r = solve(gab, idx, uv, FX, {}, 0.8, free_fin_gap=True)
    assert r["scale_source"] == "NO_METRIC_ANCHOR" and r["delivery"] == "REFUSED"
    assert r["identifiability"] == "UNIDENTIFIABLE"


def test_sigma_bars_finite_positive_and_honest():
    """σ=1px + 一条实测边: 误差棒为有限正值且 2σ 区间须覆盖实际误差 (局部线性近似的下限检查)。"""
    rng = np.random.default_rng(2027)
    gab = MODELS["gable_top"]
    covered = total = 0
    for _ in range(3):
        idx, uv, _ = observe(gab, GABLE_PARAMS, _gable_cam(), FX)
        r = solve(gab, idx, uv + rng.normal(0, 1.0, uv.shape), FX, {"Hb": GABLE_PARAMS["Hb"]}, 0.8, noise_px=1.0)
        th = {**r["anchors"], **r["theta"]}
        for k in ("W", "D", "Hr", "Ef"):
            s = r["sigma_mm"][k]
            assert math.isfinite(s) and s > 0, (k, s)
            covered += abs(th[k] - GABLE_PARAMS[k]) <= 2 * s
            total += 1
    assert covered >= 0.8 * total, covered  # 名义 95%, 小样本放宽到 80% 下限


def test_multiview_and_free_fx_contract():
    """B0-B 前置合同: 多视角联合拟合 (参数共享/位姿逐视角) + 共享焦距乘数恢复。"""
    gab = MODELS["gable_top"]
    idx, uv, _ = observe(gab, GABLE_PARAMS, _gable_cam(), FX)
    extra = []
    for az, el, roll, d in ((140, 10, 3, 0.75), (270, 30, 0, 0.90)):
        c = {"az": math.radians(az), "el": math.radians(el), "roll": math.radians(roll), "d_eye": d}
        i2, u2, _ = observe(gab, GABLE_PARAMS, c, FX)
        extra.append((i2, u2, FX))
    r = solve(gab, idx, uv, FX, {"Hb": GABLE_PARAMS["Hb"]}, 0.8, extra_views=extra)
    assert r["ok"] and len(r["cams"]) == 3
    th = {**r["anchors"], **r["theta"]}
    for k in ("W", "D"):
        assert abs(th[k] - GABLE_PARAMS[k]) < 3.0, (k, th[k])

    # 部分未知内参: 渲染 fx×1.05, 求解名义 fx + 共享乘数 → s 须恢复 1.05 且尺寸不歪
    i3, u3, _ = observe(gab, GABLE_PARAMS, _gable_cam(), FX * 1.05)
    r = solve(gab, i3, u3, FX, {"Hb": GABLE_PARAMS["Hb"]}, 0.8, free_fx=True)
    assert abs(r["cam"]["fx_scale"] - 1.05) < 0.05
    th = {**r["anchors"], **r["theta"]}
    assert abs(th["W"] - GABLE_PARAMS["W"]) < 3.0


def test_sandwich_robust_sigma_and_policy_gate():
    """R4 WP1-III + B06 对策: 聚类三明治 σ 与交付门槛合同。"""
    gab = MODELS["gable_top"]
    CL = {0: 0, 1: 0, 4: 0, 5: 0, 2: 1, 3: 1, 6: 1, 7: 1, 8: 2, 9: 2, 10: 3, 11: 3, 12: 3, 13: 3}
    rng = np.random.default_rng(31)
    idx, uv, _ = observe(gab, GABLE_PARAMS, _gable_cam(), FX)
    r = solve(gab, idx, uv + rng.normal(0, 1.0, uv.shape), FX, {"Hb": GABLE_PARAMS["Hb"]}, 0.8, point_clusters=CL)
    assert r["ok"] and r["sigma_mm_robust"] is not None
    # i.i.d. 下三明治不得系统性误伤 (逐帧 4 簇方差大, 只查宽界)
    ratio = r["sigma_mm_robust"]["W"] / r["sigma_mm"]["W"]
    assert 0.25 <= ratio <= 4.0, ratio
    # 交付门槛: REFUSED → NO_GO
    idx2, uv2, _ = observe(MODELS["cuboid"], {"W": 80.0, "D": 50.0, "H": 120.0}, CUBOID_CAM, FX)
    r2 = solve(MODELS["cuboid"], idx2, uv2, FX, {}, 0.6)
    assert delivery_policy(r2) == "NO_GO"
    # MANUFACTURING + 巨大 σ → MANUAL (精度不足禁自动)
    r3 = solve(gab, idx, uv + rng.normal(0, 8.0, uv.shape), FX, {"Hb": GABLE_PARAMS["Hb"]}, 0.8, point_clusters=CL)
    if r3["delivery"] == "MANUFACTURING_DIMENSIONS":
        assert delivery_policy(r3, tol_mm=1.0, k=2.0) == "MANUAL"
