#!/usr/bin/env python3
"""货架渲染后置: CMOS 噪声 (暗部加权) + 全局爆白像素门.

用法: python3 scripts/post_shelf_photo.py <render.png> [--jpg out.jpg]
负结果存证 (D3e, 2026-11-21): 边缘色差(1px通道移位)+暗角使排序 7.5->7.2 反输,
被 GPT 判为"数字锐化感/重影/色边"渲染痕迹 — 严禁加入本管线。
"""
import sys
import numpy as np
from PIL import Image


def main():
    src = sys.argv[1]
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    pct252 = (a.max(axis=2) >= 252).mean() * 100
    print(f"PIXEL_GATE pct>=252: {pct252:.1f}%  mean: {a.mean():.1f}  -> "
          f"{'PASS' if pct252 < 10 else 'FAIL'}")
    h, w = a.shape[:2]
    lum = a.mean(axis=2, keepdims=True)
    dark_w = np.clip(1.0 - lum / 200.0, 0.15, 1.0)  # 暗部加权
    rng = np.random.default_rng(7)
    ln = rng.normal(0, 2.0, lum.shape).astype(np.float32) * dark_w   # 亮度噪 σ2.0
    cn = rng.normal(0, 1.0, a.shape).astype(np.float32)              # 色噪 σ1.0
    out = np.clip(a + ln + cn, 0, 255).astype(np.uint8)
    Image.fromarray(out).save(src)
    if "--jpg" in sys.argv:
        jpg = sys.argv[sys.argv.index("--jpg") + 1]
        Image.fromarray(out).convert("RGB").save(jpg, quality=88)
        print(f"jpg -> {jpg}")


if __name__ == "__main__":
    main()
