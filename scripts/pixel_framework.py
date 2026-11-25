#!/usr/bin/env python3
"""像素级客观对比框架 — Pack10K vs NVIDIA USDCraft 参照渲染。

与 GPT 视觉打分并行的第二支柱 (主观+客观双框架)。
指标 (每行 6 项, 每项给出我方值/参照值/对齐度):
  H1 灰度直方图分布   32-bin 归一化直方图 L1 距离 (越小越近)
  H2 亮度均值/方差    整体曝光水平对齐
  E1 边缘密度         Sobel |>24| 像素占比 (细节丰富度)
  E2 边缘方向熵       边缘方向分布均匀度 (结构复杂度)
  C1 主色             KMeans(k=5) 主色质心与占比
  B1 背景均匀度       四角+上带区域局部标准差中位数 (无缝度, 低=好)
用法: python pixel_framework.py <ours.png> <theirs.png> [--json OUT]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def load_gray(p):
    return np.asarray(Image.open(p).convert("L"), float)


def load_rgb(p):
    return np.asarray(Image.open(p).convert("RGB"), float)


def hist_l1(a, b, bins=32):
    ha, _ = np.histogram(a, bins=bins, range=(0, 255))
    hb, _ = np.histogram(b, bins=bins, range=(0, 255))
    ha = ha / max(1, ha.sum())
    hb = hb / max(1, hb.sum())
    return float(np.abs(ha - hb).sum())


def ssim_simple(a, b):
    """全局 SSIM (均匀窗近似, C1/C2 标准)。"""
    a = a[: min(a.shape[0], b.shape[0]), : min(a.shape[1], b.shape[1])]
    b = b[: a.shape[0], : a.shape[1]]
    ma, mb = a.mean(), b.mean()
    va, vb = a.var(), b.var()
    cov = ((a - ma) * (b - mb)).mean()
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    return float(((2 * ma * mb + c1) * (2 * cov + c2)) / ((ma**2 + mb**2 + c1) * (va + vb + c2)))


def sobel_edges(img):
    gx = np.zeros_like(img)
    gy = np.zeros_like(img)
    gx[1:-1, 1:-1] = (
        -img[:-2, :-2] - 2 * img[1:-1, :-2] - img[2:, :-2]
        + img[:-2, 2:] + 2 * img[1:-1, 2:] + img[2:, 2:]
    )
    gy[1:-1, 1:-1] = (
        -img[:-2, :-2] - 2 * img[:-2, 1:-1] - img[:-2, 2:]
        + img[2:, :-2] + 2 * img[2:, 1:-1] + img[2:, 2:]
    )
    mag = np.hypot(gx, gy) / 4.0
    ang = np.degrees(np.arctan2(gy, gx)) % 180.0
    return mag, ang


def edge_stats(img):
    mag, ang = sobel_edges(img)
    strong = mag > 24
    density = float(strong.mean())
    if strong.sum() > 50:
        hist, _ = np.histogram(ang[strong], bins=18, range=(0, 180))
        p = hist / max(1, hist.sum())
        p = p[p > 0]
        entropy = float(-(p * np.log(p)).sum() / np.log(18))
    else:
        entropy = 0.0
    return density, entropy


def kmeans5(rgb, iters=8, seed=0):
    px = rgb.reshape(-1, 3)[:: max(1, rgb.shape[0] * rgb.shape[1] // 20000)]
    rng = np.random.default_rng(seed)
    centers = px[rng.choice(len(px), 5, replace=False)]
    for _ in range(iters):
        d = ((px[:, None, :] - centers[None, :, :]) ** 2).sum(2)
        lab = d.argmin(1)
        for k in range(5):
            sel = px[lab == k]
            if len(sel):
                centers[k] = sel.mean(0)
    d = ((px[:, None, :] - centers[None, :, :]) ** 2).sum(2)
    lab = d.argmin(1)
    counts = np.bincount(lab, minlength=5)
    order = counts.argsort()[::-1]
    return [(centers[k].round(1).tolist(), round(float(counts[k] / len(px)), 3)) for k in order]


def bg_uniformity(img):
    """四角+上带的局部标准差中位数 (无缝度)。"""
    h, w = img.shape
    m = max(8, w // 10)
    zones = [
        img[: h // 6, :m], img[: h // 6, w - m :],
        img[h // 6: h // 3, :m], img[h // 6: h // 3, w - m :],
        img[: h // 8, w // 2 - m // 2: w // 2 + m // 2],
    ]
    stds = [float(z.std()) for z in zones if z.size > 50]
    return float(np.median(stds)) if stds else 0.0


def metrics(png_path):
    g = load_gray(png_path)
    rgb = load_rgb(png_path)
    density, entropy = edge_stats(g)
    return {
        "brightness_mean": round(float(g.mean()), 1),
        "brightness_std": round(float(g.std()), 1),
        "edge_density": round(density, 4),
        "edge_dir_entropy": round(entropy, 3),
        "bg_uniformity": round(bg_uniformity(g), 2),
        "dom_colors": kmeans5(rgb),
    }


def main() -> int:
    ours_p, theirs_p = sys.argv[1], sys.argv[2]
    out = sys.argv[4] if len(sys.argv) > 4 else None
    mo, mt = metrics(ours_p), metrics(theirs_p)
    go, gt = load_gray(ours_p), load_gray(theirs_p)
    h1 = hist_l1(go, gt)
    s = ssim_simple(go, gt)
    result = {
        "ours": ours_p, "theirs": theirs_p,
        "H1_hist_l1": round(h1, 3),
        "H2_ssim_global": round(s, 3),
        "E1_edge_density": {"ours": mo["edge_density"], "theirs": mt["edge_density"]},
        "E2_edge_dir_entropy": {"ours": mo["edge_dir_entropy"], "theirs": mt["edge_dir_entropy"]},
        "B1_bg_uniformity": {"ours": mo["bg_uniformity"], "theirs": mt["bg_uniformity"]},
        "brightness": {"ours": mo["brightness_mean"], "theirs": mt["brightness_mean"]},
        "dom_colors": {"ours": mo["dom_colors"], "theirs": mt["dom_colors"]},
    }
    print(f"== {Path(ours_p).name} vs {Path(theirs_p).name}")
    print(f"  H1 直方图L1 {result['H1_hist_l1']}  H2 SSIM {result['H2_ssim_global']}")
    print(f"  E1 边缘密度 我{result['E1_edge_density']['ours']} vs 参{result['E1_edge_density']['theirs']}")
    print(f"  E2 方向熵   我{result['E2_edge_dir_entropy']['ours']} vs 参{result['E2_edge_dir_entropy']['theirs']}")
    print(f"  B1 背景均匀 我{result['B1_bg_uniformity']['ours']} vs 参{result['B1_bg_uniformity']['theirs']}")
    print(f"  亮度        我{result['brightness']['ours']} vs 参{result['brightness']['theirs']}")
    if out:
        import json
        Path(out).write_text(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
