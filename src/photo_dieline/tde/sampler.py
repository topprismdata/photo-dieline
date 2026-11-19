"""TDE 六维随机化采样器 (docs/tde-spec.md 冻结版 V0.1).

分档 70/25/5 (REALISTIC/MODERATE/STRESS); 采样 40% 分层 + 40% LHS + 20% 主动(v1 预留)。
CaptureProfile 档内联动: 先选档再采样, 近距↔焦距/景深, 暗光↔ISO, 手持↔运动模糊/滚转。
每样本输出完整捕获配置 (渲染端与标签共享同一来源, 杜绝标签漂移)。
"""
from __future__ import annotations

import math

import numpy as np

TIERS = ("REALISTIC", "MODERATE", "STRESS")
TIER_MIX = (0.70, 0.25, 0.05)
SCENE_PROFILES = ("PHONE_INDOOR", "PHONE_WINDOW_LIGHT", "PHONE_SUPERMARKET",
                  "PHONE_DESKTOP", "PHONE_HANDHELD")
STUDIO_CAP = 0.15  # 白底棚拍 ≤15% (spec 1.5)


def _trunc_normal(rng, lo, hi, mu, sigma, size=None):
    v = rng.normal(mu, sigma, size)
    return np.clip(v, lo, hi)


def _tri(rng, lo, hi, size=None):
    return rng.triangular(lo, lo + (hi - lo) * 0.4, hi, size)


class CaptureSampler:
    """按冻结表采样一帧捕获配置."""

    def __init__(self, seed: int):
        self.rng = np.random.default_rng(seed)

    def _tier(self) -> str:
        return TIERS[self.rng.choice(3, p=TIER_MIX)]

    def _scene(self, tier: str) -> str:
        if self.rng.random() < STUDIO_CAP:
            return "STUDIO"
        return SCENE_PROFILES[self.rng.choice(len(SCENE_PROFILES))]

    # ---- 1.1 Camera ----
    def camera(self, tier: str, radius_mm: float) -> dict:
        r = self.rng
        # 等效焦距 分段混合: 主摄广角 24-28 / 裁切 35-50 / 长焦 65-70
        seg = r.choice(3)
        lo, hi = [(24, 28), (35, 50), (65, 70)][seg]
        el_min = {"REALISTIC": 8.0, "MODERATE": 5.0, "STRESS": -15.0}[tier]
        if tier == "REALISTIC":
            fe = r.uniform(lo, hi)
            pitch = _tri(r, el_min, 35)
            yaw = r.uniform(-35, 35)
            roll = float(_trunc_normal(r, -5, 5, 0, 2))
            dist_cm = float(np.exp(r.uniform(np.log(25), np.log(100))))
            ratio_lo, ratio_hi = 0.45, 0.85
            dist_pct = r.uniform(0, 0.01)
            fstop = r.uniform(1.7, 4.0)
        elif tier == "MODERATE":
            fe = r.uniform(max(20, lo - 6), min(85, hi + 15))
            pitch = _tri(r, el_min, 45)
            yaw = r.uniform(-60, 60)
            roll = float(_trunc_normal(r, -12, 12, 0, 5))
            dist_cm = float(np.exp(r.uniform(np.log(15), np.log(150))))
            ratio_lo, ratio_hi = 0.30, 0.90
            dist_pct = r.uniform(0, 0.02)
            fstop = r.uniform(1.4, 5.6)
        else:
            fe = r.uniform(16, 100)
            pitch = _tri(r, el_min, 60)
            yaw = r.uniform(-85, 85)
            roll = float(_trunc_normal(r, -25, 25, 0, 10))
            dist_cm = float(np.exp(r.uniform(np.log(10), np.log(250))))
            ratio_lo, ratio_hi = 0.15, 0.95
            dist_pct = r.uniform(0, 0.04)
            fstop = r.uniform(1.2, 8.0)
        # 距离↔景深联动: 近距开大光圈概率升高
        if dist_cm < 35 and r.random() < 0.5:
            fstop = min(fstop, r.uniform(1.7, 2.8))
        # 主体占比 (spec 语义=画面面积占比) → 线性占比 = sqrt(面积占比); 距离解算后夹回档位区间
        ratio = math.sqrt(r.uniform(ratio_lo, ratio_hi))
        fov_half = math.atan(18.0 / fe)
        d_mm = radius_mm / (ratio * math.tan(fov_half))
        d_mm = float(np.clip(d_mm, dist_cm * 10, dist_cm * 10 * 1.6))
        return {"equiv_focal_mm": round(fe, 2), "pitch_deg": round(float(pitch), 2),
                "yaw_deg": round(float(yaw), 2), "roll_deg": round(roll, 2),
                "distance_mm": round(d_mm, 1), "subject_linear_ratio_target": round(ratio, 3),
                "optical_axis_offset_deg": round(dist_pct * 57.3, 2),
                "distortion_frac": round(r.uniform(0, {"REALISTIC": 0.01, "MODERATE": 0.02, "STRESS": 0.04}[tier]), 4),
                "aperture_fstop": round(fstop, 2)}

    # ---- 1.2 Lighting (联合分布约束) ----
    def lighting(self, tier: str, scene: str) -> dict:
        r = self.rng
        if scene == "STUDIO":
            kel_lo, kel_hi, amb_lo, amb_hi = 6200, 6800, 0.55, 0.75
        elif scene == "PHONE_INDOOR":
            kel_lo, kel_hi, amb_lo, amb_hi = 3000, 4500, 0.30, 0.60
        elif scene == "PHONE_WINDOW_LIGHT":
            kel_lo, kel_hi, amb_lo, amb_hi = 4500, 7500, 0.40, 0.80
        elif scene == "PHONE_SUPERMARKET":
            kel_lo, kel_hi, amb_lo, amb_hi = 4000, 6500, 0.35, 0.70
        elif scene == "PHONE_DESKTOP":
            kel_lo, kel_hi, amb_lo, amb_hi = 3500, 5000, 0.30, 0.65
        else:  # PHONE_HANDHELD
            kel_lo, kel_hi, amb_lo, amb_hi = 3000, 7500, 0.20, 0.80
        kel = r.uniform(kel_lo, kel_hi)
        ev = {"REALISTIC": lambda: r.uniform(-1.5, 1.5), "MODERATE": lambda: r.uniform(-2.5, 2.5),
              "STRESS": lambda: r.uniform(-4, 3)}[tier]()
        key = {"REALISTIC": lambda: r.uniform(0.5, 2.0), "MODERATE": lambda: r.uniform(0.25, 3.0),
               "STRESS": lambda: r.uniform(0.1, 5.0)}[tier]()
        amb = r.uniform(amb_lo, amb_hi)
        return {"kelvin": round(kel), "exposure_ev": round(ev, 2),
                "key_intensity_x": round(key, 2), "ambient_ratio": round(amb, 2)}

    # ---- 1.3 Material / 1.5 Environment / 1.6 IQ ----
    def material_env_iq(self, tier: str, scene: str) -> dict:
        r = self.rng
        rough = {"REALISTIC": lambda: r.uniform(0.25, 0.75),
                 "MODERATE": lambda: r.uniform(0.15, 0.90),
                 "STRESS": lambda: r.uniform(0.05, 1.0)}[tier]()
        iq = {"jpeg_q": int(r.integers(75, 96)),
              "gauss_sigma_px": round(r.uniform(0, 0.6), 3),
              "motion_blur_px": round(r.uniform(0, 2.0) * (1.0 if scene == "PHONE_HANDHELD" else 0.35), 2),
              "wb_shift_k": int(r.uniform(-300, 300))}
        occl = {"REALISTIC": lambda: r.uniform(0, 0.05),
                "MODERATE": lambda: r.uniform(0, 0.15),
                "STRESS": lambda: r.uniform(0, 0.30)}[tier]()
        return {"roughness": round(float(rough), 3),
                "base_color": [round(float(x), 3) for x in r.uniform(0.55, 0.92, 3)],
                "occlusion_hint": round(float(occl), 3), **iq}

    def sample(self, radius_mm: float, tier: str | None = None) -> dict:
        tier = tier or self._tier()
        scene = self._scene(tier)
        s = {"tier": tier, "scene": scene}
        s.update(self.camera(tier, radius_mm))
        s.update(self.lighting(tier, scene))
        s.update(self.material_env_iq(tier, scene))
        return s


def lhs_samples(n: int, dim: int, rng: np.random.Generator) -> np.ndarray:
    """Latin Hypercube (0,1]^dim — 连续维用; 类别维走分层."""
    u = (rng.permutation(np.arange(n)).reshape(dim, n).T + rng.uniform(size=(n, dim))) / n
    return u


def sample_batch(radius_mm: float, n: int, seed: int,
                 tier_mix: tuple = TIER_MIX) -> list[dict]:
    """n 帧捕获配置; 档位分层 + 场景分层 (棚拍≤15%)."""
    rng = np.random.default_rng(seed)
    s = CaptureSampler(seed + 1)
    n_tier = [int(round(n * m)) for m in tier_mix]
    while sum(n_tier) < n:
        n_tier[0] += 1
    tiers = sum(([t] * c for t, c in zip(TIERS, n_tier)), [])
    rng.shuffle(tiers)
    out = []
    studio_used = 0
    for i, tier in enumerate(tiers[:n]):
        smp = s.sample(radius_mm, tier=tier)
        if smp["scene"] == "STUDIO" and studio_used >= STUDIO_CAP * n:
            smp["scene"] = "PHONE_INDOOR"
            smp.update(s.lighting(tier, "PHONE_INDOOR"))
        studio_used += smp["scene"] == "STUDIO"
        smp["sample_seed"] = seed * 100003 + i
        out.append(smp)
    return out
