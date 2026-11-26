#!/usr/bin/env python3
"""NV960 parity 锐化后处理 (管线级, 确定性零漂移)。

用法: python3 nv960_sharpen.py <img> [<img>...]
配方: UnsharpMask(radius=2, percent=280, threshold=1) — 实测 E1 +53%。
"""
import sys

from PIL import Image, ImageFilter


def main() -> int:
    for p in sys.argv[1:]:
        im = Image.open(p)
        im.filter(ImageFilter.UnsharpMask(radius=2, percent=280, threshold=1)).save(p)
        print(f"锐化完成: {p}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
