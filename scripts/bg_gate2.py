#!/usr/bin/env python3
"""G-F8b 背景长直线门禁 v2 — 旋转扫描式 (round5b 假阴性修正)。

原理: 地平线/墙角/斜向分界 = 图像中的长直线。将图像旋转 ±25/±45/±60°,
每次都做「连续阶跃行」检测 (行内 ≥55% 宽度的像素发生 ≥5/255 同向阶跃);
任何旋转下存在这样的长直线 = FAIL。产品棱线 (短/弯曲) 与平滑渐变不触发。
用法: python bg_gate2.py <render.png> [run_frac=0.55] [step=5.0]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def long_line_rows(g, run_frac=0.55, step=5.0):
    """返回最强长直线行: (row, run_len_frac)。无长线返回 (None, 0)。g=灰度图。"""
    d = np.abs(np.diff(g, axis=0))  # 相邻行差
    run = d >= step
    best_frac, best_row = 0.0, -1
    for r in range(run.shape[0]):
        row = run[r]
        # 最长连续 True 段 (含 1px 容差断点)
        best, cur, gap = 0, 0, 0
        for v in row:
            if v:
                cur += 1 + (gap if gap <= 2 else 0)
                gap = 0
                best = max(best, cur)
            elif cur > 0 and gap <= 2:
                gap += 1
            else:
                cur, gap = 0, 0
        frac = best / row.size
        if frac > best_frac:
            best_frac, best_row = frac, r
    return best_row, best_frac


def main() -> int:
    p = Path(sys.argv[1])
    run_frac = float(sys.argv[2]) if len(sys.argv) > 2 else 0.55
    step = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
    im0 = Image.open(p).convert("RGB")
    worst = ("base", 0.0)
    for ang in (0, 25, -25, 45, -45, 60, -60):
        im = im0 if ang == 0 else im0.rotate(ang, expand=True, fillcolor=(128, 128, 128))
        a = np.asarray(im.convert("L"), float)
        row, frac = long_line_rows(a, run_frac, step)
        if frac > worst[1]:
            worst = (f"rot{ang}", frac)
    ok = worst[1] < run_frac
    print(f"G-F8b {'PASS' if ok else 'FAIL'}: longest line run {worst[1]:.2%} "
          f"(at {worst[0]}, thresh {run_frac:.0%}) — {p.name}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
