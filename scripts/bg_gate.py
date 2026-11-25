#!/usr/bin/env python3
"""背景分界图像级门禁 (G-F8) — GPT round4b 建议: 不能只看场景对象清空, 要测渲染像素。

判据: 上半帧 (背景区) 内最强水平边缘的梯度强度。无缝棚的上半帧只允许
缓变 (天穹渐变), 任何 ≥6.0/255 的水平阶跃 = 地平/墙角/板边 → FAIL。
用法: python bg_gate.py <render.png> [thresh=6.0]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def main() -> int:
    p = Path(sys.argv[1])
    thresh = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
    im = np.asarray(Image.open(p).convert("RGB"), float).mean(2)
    h, w = im.shape
    # 只测左右边距列 (主体外的真背景区); 全宽会把主体棱线误判为背景分界
    margin = max(8, w // 12)
    top = np.hstack([im[: h // 2, :margin], im[: h // 2, w - margin:]])
    dy = np.abs(np.diff(top, axis=0)).mean(1)
    peak_row = int(dy.argmax())
    peak = float(dy.max())
    ok = peak < thresh
    print(f"BG-GATE {'PASS' if ok else 'FAIL'}: peak_horizontal_edge "
          f"{peak:.2f}/255 at row {peak_row} (thresh {thresh}) — {p.name}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
