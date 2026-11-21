#!/usr/bin/env python3
"""measure_planogram: 从参照实拍照量测陈列表 → planogram.json (ESR Step A).

取证方法 (像素证据, 不用美术直觉):
- 层带: 参照对账 v2 量测的 7 层 (docs/shelf_twin/RECONCILIATION.md), 层带按货架
  可见区等分 (透视未校正, 注记 perspective_uncorrected)
- 段界: 层带中线上逐列主色 (HSV hue 量化) 变化点 = 色块段边界
- 排面数: 段内竖直边缘梯度峰周期计数 (亚像素不 annotation=est)
- 设计映射: 段主色 hue → Topprism 12 设计族 (公开轨品牌替换)
"""
import json
import colorsys
from pathlib import Path

import numpy as np
from PIL import Image

REF = Path(__file__).parent.parent / "data/shelf_twin_ref/primary.jpg"
OUT = Path(__file__).parent.parent / "data/shelf_twin/planogram.json"
LEVELS = 7
# Topprism 12 设计族 (与 build_hxl_shelf.FAMILIES 同源; hue 中心 0-360)
FAMILIES = [
    ("red", 8), ("orange", 26), ("yellow", 50), ("green", 115),
    ("blue", 210), ("purple", 275), ("brown", 22), ("pink", 345),
    ("teal", 180), ("gold", 42), ("white", -1), ("dark", -1),
]


def hue_name(h_deg, sat, val):
    if sat < 0.22 and val > 0.75:
        return "white"
    if val < 0.18:
        return "dark"
    for name, c in FAMILIES[:-2]:
        d = min(abs(h_deg - c), 360 - abs(h_deg - c))
        if name in ("brown", "gold") and not (18 <= h_deg <= 50):
            continue
        if d < 22:
            return name
    return "white" if sat < 0.3 else "dark"


def main():
    im = Image.open(REF).convert("RGB")
    a = np.asarray(im).astype(float)
    h_img, w_img = a.shape[:2]
    r, g, b = a[..., 0] / 255, a[..., 1] / 255, a[..., 2] / 255
    mx, mn = np.max(a / 255, -1), np.min(a / 255, -1)
    v = mx
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    # hue 向量化
    hue = np.zeros_like(v)
    dz = mx - mn
    m = dz > 1e-6
    rr, gg, bb = r, g, b
    idx = (mx == rr) & m
    hue[idx] = (60 * ((gg[idx] - bb[idx]) / dz[idx]) + 360) % 360
    idx = (mx == gg) & m
    hue[idx] = (60 * ((bb[idx] - rr[idx]) / dz[idx]) + 120) % 360
    idx = (mx == bb) & m
    hue[idx] = (60 * ((rr[idx] - gg[idx]) / dz[idx]) + 240) % 360

    # 货架可见区 (参照: 顶部招牌下沿~底部地面), 取竖直 8%-92%
    y0, y1 = int(h_img * 0.08), int(h_img * 0.92)
    band_h = (y1 - y0) / LEVELS

    levels_out = []
    for lv in range(LEVELS):
        ly0 = int(y0 + lv * band_h)
        ly1 = int(y0 + (lv + 1) * band_h)
        # 中线带 (层带中部 30-70%) 逐列主色
        my0, my1 = int(ly0 + band_h * 0.30), int(ly0 + band_h * 0.70)
        col_hue = np.median(hue[my0:my1], axis=0)
        col_s = np.median(s[my0:my1], axis=0)
        col_v = np.median(v[my0:my1], axis=0)
        def coarse(hd, sa, va):
            if sa < 0.25 and va > 0.7:
                return "neutral"
            if va < 0.18:
                return "neutral"
            if hd < 18 or hd >= 330:
                return "red"
            if 18 <= hd < 55:
                return "yellow"
            if 55 <= hd < 165:
                return "green"
            if 165 <= hd < 255:
                return "blue"
            return "purple"
        names = [coarse(col_hue[x], col_s[x], col_v[x]) for x in range(w_img)]
        # 段界: 粗主色变化 且 持续 >=45px 才算段 (滤袋印刷细节噪声)
        segs = []
        cur = names[0]
        start = 0
        for x in range(1, w_img):
            if names[x] != cur:
                nxt = names[min(x + 45, w_img - 1)]
                if nxt != cur:
                    if x - start >= 45:
                        segs.append([start, x, cur])
                    cur = nxt
                    start = x
        if w_img - start >= 45:
            segs.append([start, w_img, cur])
        # 合并同名相邻段 (间隔<60px) + 吸收 <40px 小段进邻段
        merged = []
        for sg in segs:
            if merged and merged[-1][2] == sg[2] and sg[0] - merged[-1][1] < 60:
                merged[-1][1] = sg[1]
            else:
                merged.append(sg)
        stable = []
        for sg in merged:
            if sg[1] - sg[0] < 40 and stable:
                stable[-1][1] = sg[1]
            else:
                stable.append(sg)
        merged = stable
        # 排面数: 段内竖直梯度峰 (|dI/dx| 阈值) 计周期
        gray = a.mean(-1)
        seg_out = []
        for (sx0, sx1, fam) in merged:
            fam = hue_name(float(np.median(col_hue[sx0:sx1])),
                           float(np.median(col_s[sx0:sx1])),
                           float(np.median(col_v[sx0:sx1])))
            strip = gray[my0:my1, sx0:sx1]
            gx = np.abs(np.diff(strip, axis=1)).mean(0)
            thr = gx.mean() + 1.2 * gx.std()
            peaks = (gx[1:-1] > thr) & (gx[1:-1] >= gx[:-2]) & (gx[1:-1] >= gx[2:])
            # 峰间距取中位数 → 排面宽 → facings
            idxs = np.where(peaks)[0] + 1
            if len(idxs) >= 2:
                gaps = np.diff(idxs)
                gaps = gaps[(gaps > 12) & (gaps < 200)]
                period = float(np.median(gaps)) if len(gaps) else 0
            else:
                period = 0
            facings = max(1, round((sx1 - sx0) / period)) if period > 0 else max(1, round((sx1 - sx0) / 90))
            seg_out.append({
                "family_color": fam,
                "design_id": f"tp_{[f[0] for f in FAMILIES].index(fam):02d}",
                "x0_frac": round(sx0 / w_img, 4),
                "x1_frac": round(sx1 / w_img, 4),
                "facings": int(facings),
                "facings_evidence": "edge_periodicity" if period > 0 else "width_est",
            })
        levels_out.append({
            "level": lv,
            "y_band_px": [ly0, ly1],
            "segments": seg_out,
        })

    plan = {
        "schema": "shelf-planogram/1.0",
        "source": {
            "reference": "data/shelf_twin_ref/primary.jpg",
            "method": "pixel_measured",
            "notes": "perspective_uncorrected; 层带按对账v2的7层等分",
        },
        "fixture": {
            "type": "backlit_wall",
            "width_m": 2.4,
            "levels": LEVELS,
            "level_height_m": 0.38,
            "depth_m": 0.4,
            "evidence": "RECONCILIATION.md v2 量测",
        },
        "levels": levels_out,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(plan, ensure_ascii=False, indent=1))
    n_seg = sum(len(l["segments"]) for l in levels_out)
    print(f"planogram.json: {LEVELS} levels, {n_seg} segments")
    for l in levels_out:
        segs = " | ".join(f"{sg['family_color']}({sg['facings']}f)" for sg in l["segments"])
        print(f"  L{l['level']}: {segs}")


if __name__ == "__main__":
    main()
