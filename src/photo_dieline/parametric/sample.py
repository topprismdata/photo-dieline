"""P0-③ 变体采样器: 显式尺寸键缩放 + validate_params 守门 + 种子纪律。

纪律: 尺寸键**显式声明** (禁启发式猜键 — 采错键=静默产废件); 工艺参数 (克重/胶宽/板厚) 不动;
非法组合 validate_params 拒绝 → 换因子重采 (8 次全非法 = 大声失败, 不静默产废)。
种子 = sha256(class_id + variant_index) 派生, 资产可 bit 级再生。
"""

import hashlib

import numpy as np

from ..core.ir import class_defaults, class_module

# 试点家族的可缩放尺寸键 (显式声明; 值须 >0 才缩放, 缩放键 <2 = 大声失败)
SCALABLE_KEYS = {
    "gable": ("W", "D", "Hb", "Hr", "Ef"),
    "clv": ("W", "D", "H"),
    "cone": ("side_b", "side_t", "h"),
    "food": ("W", "D", "H", "Hl"),
    # 2026-11-25 全家族覆盖 (逐族 class_defaults 实测枚举; 保守取主尺寸, 耦合工艺键不动)
    "aseptic": ("W", "D", "Hb"),
    "brick": ("W", "D", "Hb"),
    "clamp": ("W", "D", "H"),
    "crashlock": ("W", "D", "H", "Hf", "Hb"),
    "cup": ("H", "side_b", "side_t"),
    "dispenser": ("W", "D", "H"),
    "display": ("W", "D", "H", "Hf"),
    "envelope": ("S", "flap_d"),
    "handle": ("W", "D", "H"),
    "hanger": ("W", "D", "H"),
    "hexagonal": ("H", "side"),
    "lockbottom": ("W", "D", "H", "Hf", "Hb", "side"),
    "mailer": ("h", "spine_w", "cover_w", "tuck_t"),
    "pillow": ("W", "H", "D"),
    "prism": ("side", "h"),
    "pyramid": ("side_b", "side_t", "h"),
    "rsc": ("W", "D", "H"),
    "slide": ("W", "D", "H"),
    "tray": ("W", "D", "H", "Hf", "Hb", "side"),
    "tube": ("side", "h"),
    "tuck": ("W", "D", "H"),
    "two": ("W", "D", "H"),
    "window": ("W", "D", "H"),
}


def seed_from(cls_id: str, variant_index: int) -> int:
    tag = f"{cls_id}-v{variant_index:04d}".encode()
    return int(hashlib.sha256(tag).hexdigest()[:16], 16)


def sample_variant(cls_id: str, variant_index: int, scale_range=(0.8, 1.25), allow_identity=False):
    """类默认参数 × 尺寸缩放因子 s~U(range)。返回 (params, derivation)。
    allow_identity: 家族未声明 SCALABLE_KEYS 时回退恒等参数 (derivation 标 no_scaling_coverage
    — 规模干跑用, 多样性口径须扣除; 生产 10K 前须显式补键)。"""
    fam = cls_id.split("_")[0]
    keys = SCALABLE_KEYS.get(fam)
    if not keys:
        if allow_identity:
            base = class_defaults(cls_id)
            mod = class_module(cls_id)
            mod.validate_params(base)
            return dict(base), {"scale": 1.0, "scaled_keys": [], "seed": seed_from(cls_id, variant_index),
                                "no_scaling_coverage": True}
        raise ValueError(f"家族 {fam} 未声明 SCALABLE_KEYS — 禁止启发式采键")
    mod = class_module(cls_id)
    base = class_defaults(cls_id)
    rng = np.random.default_rng(seed_from(cls_id, variant_index))
    last_err = None
    for _ in range(8):
        s = float(rng.uniform(*scale_range))
        p = dict(base)
        scaled = []
        for k in keys:
            v = base.get(k, 0)
            if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0:
                p[k] = round(v * s, 3)
                scaled.append(k)
        if len(scaled) < 2:
            if allow_identity:
                mod.validate_params(base)
                return dict(base), {"scale": 1.0, "scaled_keys": [], "seed": seed_from(cls_id, variant_index),
                                    "no_scaling_coverage": True}
            raise ValueError(f"{cls_id}: 可缩放键不足 ({scaled}) — 检查 SCALABLE_KEYS")
        try:
            mod.validate_params(p)
        except ValueError as e:
            last_err = e
            continue
        return p, {"scale": round(s, 4), "scaled_keys": scaled, "seed": seed_from(cls_id, variant_index)}
    if allow_identity:
        mod.validate_params(base)
        return dict(base), {"scale": 1.0, "scaled_keys": [], "seed": seed_from(cls_id, variant_index),
                            "no_scaling_coverage": True, "resample_exhausted": True}
    raise ValueError(f"{cls_id}: 8 次采样均被 validate_params 拒绝 (last: {last_err})")
