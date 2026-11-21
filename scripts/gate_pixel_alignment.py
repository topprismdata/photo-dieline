#!/usr/bin/env python3
"""gate_pixel_alignment: 像素级参照对齐门 (ESR 渲染门的客观量化臂).

与 GPT 排序协议互补: 分布级像素指标 (对取景差异鲁棒), 全 CPU 可复现.
指标: 亮度直方图距离 / 饱和度直方图距离 / 边缘密度 / 高光份额 / 暗部份额 / RMS 对比.
判据: 各指标相对参照的归一化偏差 → 加权合成分 (越低越对齐), >=阈值 ALIGNED.
用法: python3 scripts/gate_pixel_alignment.py --ref <真实照片> --renders <png...>
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

W = {"lum_hist": 0.30, "sat_hist": 0.15, "edge": 0.20,
     "highlight": 0.10, "dark": 0.10, "contrast": 0.15}
THR_ALIGNED = 0.25   # 合成偏差 < 0.25 → ALIGNED
THR_NEAR = 0.40      # < 0.40 → NEAR, 否则 DEVIANT


def stats(img):
    """单图分布级指标."""
    rgb = np.asarray(img.convert("RGB"), dtype=float) / 255.0
    lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    mx = rgb.max(-1)
    mn = rgb.min(-1)
    sat = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0)
    # 边缘密度 (梯度幅度, Sobel 近似)
    gy, gx = np.gradient(lum)
    mag = np.hypot(gx, gy)
    return {
        "lum_hist": np.histogram(lum, bins=64, range=(0, 1), density=True)[0],
        "sat_hist": np.histogram(sat, bins=32, range=(0, 1), density=True)[0],
        "edge": float((mag > 0.06).mean()),
        "highlight": float((lum > 0.92).mean()),
        "dark": float((lum < 0.16).mean()),
        "contrast": float(lum.std()),
    }


def wdist(ha, hb):
    """1D Wasserstein (EMD): CDF 差的积分, [0,1]."""
    return float(np.abs(np.cumsum(ha) / ha.sum() - np.cumsum(hb) / hb.sum()).mean())


def dev(a, b):
    """归一化偏差 [0,1]: 直方图=EMD, 标量=绝对差 (微份额不饱和)."""
    return {
        "lum_hist": wdist(a["lum_hist"], b["lum_hist"]),
        "sat_hist": wdist(a["sat_hist"], b["sat_hist"]),
        "edge": abs(a["edge"] - b["edge"]),
        "highlight": abs(a["highlight"] - b["highlight"]) * 10,
        "dark": abs(a["dark"] - b["dark"]) * 10,
        "contrast": abs(a["contrast"] - b["contrast"]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--renders", nargs="+", required=True)
    ap.add_argument("--labels", nargs="+", required=True)
    ap.add_argument("--out", default=str(Path(__file__).parent.parent /
                                         "data/shelf_twin/pixel_alignment.json"))
    args = ap.parse_args()
    ref = stats(Image.open(args.ref))
    rows = []
    for p, lab in zip(args.renders, args.labels):
        st = stats(Image.open(p))
        d = dev(st, ref)
        score = sum(W[k] * d[k] for k in W)
        verdict = "ALIGNED" if score < THR_ALIGNED else ("NEAR" if score < THR_NEAR else "DEVIANT")
        rows.append({"label": lab, "render": p, "dev": {k: round(v, 4) for k, v in d.items()},
                     "score": round(score, 4), "verdict": verdict})
        print(f"{lab:>6}: dev={score:.3f} [{verdict}]  " +
              " ".join(f"{k}={d[k]:.2f}" for k in ("lum_hist", "edge", "highlight", "contrast")))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"schema": "pixel-alignment-gate/1.0", "ref": args.ref,
                               "weights": W, "thresholds": [THR_ALIGNED, THR_NEAR],
                               "rows": rows}, ensure_ascii=False, indent=1))
    print(f"PIXEL_ALIGNMENT_DONE -> {out}")


if __name__ == "__main__":
    main()
