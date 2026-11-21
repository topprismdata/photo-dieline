#!/usr/bin/env python3
"""bag_print: 软袋印刷设计 v2 (共享模块, make_pillow_bag 与 build_hxl_shelf 共用).

P3 印刷保真 + P2 微观质感 (资产栈级, 2026-11-21 立项):
- 多区排版: 顶品牌带/图案带/食品窗/风味横幅 — 参照真袋的 busy print 结构
- 图案带: 斜纹/圆点网格 (种子确定性, 同设计同版)
- 食品窗: 暖色椭圆簇 (薯片堆意象) + 高光点
- 吉祥物圆徽 (右上) + 品牌字错版 1px (印刷套准缺陷, 微量)
- 纸纹: 垂直渐变 + 亮度颗粒 (D4a 负结果教训: 纯平色场=CG 塑料感)
"""
import colorsys
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/STHeiti Medium.ttc"


def render_print(S: int, col, sub: str, seed: int = 0, label: str = "TOPPRISM") -> Image.Image:
    """col: RGB 0-1 floats; 返回 S×S 印刷面."""
    h, l, sv = colorsys.rgb_to_hsv(*[c for c in col[:3]])
    sv = min(1.0, sv * 0.95)
    r, g, b = colorsys.hsv_to_rgb(h, sv, l)
    base = tuple(int(c * 255) for c in (r, g, b))
    lite = tuple(min(255, int(c * 255 + 38)) for c in (r, g, b))
    dark = tuple(max(0, int(c * 255 - 52)) for c in (r, g, b))
    im = Image.new("RGB", (S, S), base)
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)

    # 1) 顶品牌带 (更亮)
    d.rectangle([0, 0, S, S // 6], fill=lite)
    # 2) 图案带 (上中, 斜纹或圆点 — 奇偶种子二选一)
    band_y0, band_y1 = S // 6, int(S * 0.42)
    if seed % 2 == 0:
        step = S // 16
        for x0 in range(-S, S * 2, step * 2):
            d.polygon([(x0, band_y1), (x0 + step, band_y1), (x0 + step + S // 14, band_y0),
                       (x0 + S // 14, band_y0)], fill=dark)
    else:
        step = S // 14
        for yy in range(band_y0 + step // 2, band_y1, step):
            for xx in range(step // 2, S, step):
                rad = S // 34
                d.ellipse([xx - rad, yy - rad, xx + rad, yy + rad], fill=dark)
    # 食品窗背景 (中下, 更亮收口; 版式: 品牌字 0.37-0.57, 窗 0.60-0.82 不相撞)
    win = [S * 0.14, int(S * 0.60), S * 0.86, int(S * 0.82)]
    d.rounded_rectangle(win, radius=S // 22, fill=(250, 248, 242), outline=dark, width=max(2, S // 240))
    # 3) 食品窗内容: 暖色椭圆簇 (薯片堆意象, 充满窗) + 高光点
    cx, cy = (win[0] + win[2]) / 2, (win[1] + win[3]) / 2 + S * 0.01
    warm = [(243, 196, 80), (238, 160, 66), (214, 120, 52), (245, 214, 120)]
    for k in range(22):
        ang = rng.random() * math.pi * 2
        rad = rng.random() * S * 0.145
        ex, ey = cx + math.cos(ang) * rad, cy + math.sin(ang) * rad * 0.62
        ew = S * (0.06 + rng.random() * 0.05)
        c = warm[k % len(warm)]
        d.ellipse([ex - ew, ey - ew * 0.62, ex + ew, ey + ew * 0.62], fill=c)
    for k in range(8):
        hx = cx + (rng.random() - 0.5) * S * 0.3
        hy = cy + (rng.random() - 0.5) * S * 0.16
        hr = S * 0.014
        d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=(255, 250, 235))
    # 4) 风味横幅 (底部深色带 + 品名小注)
    d.rectangle([0, int(S * 0.84), S, S], fill=dark)
    f2 = ImageFont.truetype(FONT, int(S * 0.075), index=0)
    d.text((S // 2, int(S * 0.92)), sub, font=f2, fill=(255, 255, 255), anchor="mm")
    # 5) 吉祥物圆徽 (右上)
    mx, my, mr = S * 0.84, S * 0.10, S * 0.07
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(250, 248, 242), outline=dark, width=S // 90)
    d.ellipse([mx - mr * 0.45, my - mr * 0.3, mx - mr * 0.15, my + mr * 0.05], fill=(40, 40, 46))
    d.ellipse([mx + mr * 0.15, my - mr * 0.3, mx + mr * 0.45, my + mr * 0.05], fill=(40, 40, 46))
    d.arc([mx - mr * 0.45, my - mr * 0.1, mx + mr * 0.45, my + mr * 0.55],
          20, 160, fill=(40, 40, 46), width=max(2, S // 110))
    # 6) 品牌字 (宽度自适应) + 1px 错版 (套准缺陷)
    f = ImageFont.truetype(FONT, int(S * 0.34), index=0)
    size = int(S * 0.34)
    while size > 40:
        bb = d.textbbox((0, 0), label, font=f)
        if bb[2] - bb[0] <= 0.82 * S:
            break
        size -= 16
        f = ImageFont.truetype(FONT, size, index=0)
    ty = int(S * 0.47)
    d.text((S // 2 + S // 512, ty + S // 512), label, font=f, fill=dark, anchor="mm")
    d.text((S // 2, ty), label, font=f, fill=(30, 30, 34), anchor="mm")
    # 7) 纸纹: 垂直渐变 + 亮度颗粒 (D4a: 纯平色场=塑料感根因)
    arr = np.asarray(im).astype(np.float32)
    arr *= np.linspace(1.0, 0.9, S)[:, None, None]
    arr += np.random.default_rng(seed + 100).normal(0, 4.5, arr.shape)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
