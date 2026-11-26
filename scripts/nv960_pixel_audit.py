#!/usr/bin/env python3
"""960 逐对像素级审计 — 用仓内 pixel_framework 六指标阶梯 + 新增 S1/F1, 对 99.84% 裁决做独立复查.

口径: 与裁决器 e1 相同 (中心 62% 裁切, 比产品区). 每图 7 指标, 逐对双面对比:
  E1 边缘密度 (Sobel |>24| 占比)      — 裁决器现役轴
  E2 边缘方向熵 (结构复杂度)
  S1 Laplacian 方差 (锐度)
  F1 高频 FFT 能量比 (r>0.25 归一频域) — 细纹理有限性
  H2 亮度标准差 (对比度)
  B1 背景均匀度 (四角+上带 std 中位, 越低越无缝)
  T1 纹理熵 (灰度 64-bin 共现粗粒度 → 用 16-bin 灰度熵代理, 冻结参数)
裁决: 每指标 my>their=win / <0.85*their=loss / 其余 tie (与 E1 判负线同容差);
      复合 = win 数 - loss 数. 输出逐类胜率矩阵 + 与 E1-only 裁决的一致性复查.
用法: python3 scripts/nv960_pixel_audit.py --ours manifests/nv960_ours_map.json --out docs/nv960/pixel_audit.json
"""
import argparse, csv, json, glob, os, sys
from pathlib import Path
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from pixel_framework import load_gray, sobel_edges, bg_uniformity
from nv960_verdict import their_assets, ALL_IDS

METRICS = ["E1", "E2", "S1", "F1", "H2", "B1", "T1"]
LOSS_TOL = 0.85  # 与裁决器 0.8 同族容差 (略紧, 独立审计口径)

def crop62(path):
    im = Image.open(path).convert('L')
    w, h = im.size
    cw, ch = int(w * 0.62), int(h * 0.62)
    return np.asarray(im.crop(((w - cw) // 2, (h - ch) // 2,
                               (w + cw) // 2, (h + ch) // 2)), float)

def pixstats(g):
    mag, ang = sobel_edges(g)
    strong = mag > 24
    e1 = float(strong.mean())
    if strong.sum() > 50:
        hist, _ = np.histogram(ang[strong], bins=18, range=(0, 180))
        p = hist / max(1, hist.sum()); p = p[p > 0]
        e2 = float(-(p * np.log(p)).sum() / np.log(18))
    else:
        e2 = 0.0
    lap = g[2:-2, 2:-2] * 4 - g[:-4, 2:-2] - g[4:, 2:-2] - g[2:-2, :-4] - g[2:-2, 4:]
    s1 = float(lap.var())
    f = np.fft.rfft2(g * np.hanning(g.shape[0])[:, None])
    pw = np.abs(f) ** 2
    cy, cx = np.array(pw.shape) // 2
    yy, xx = np.mgrid[0:pw.shape[0], 0:pw.shape[1]]
    r = np.sqrt(((yy - cy) / cy) ** 2 + ((xx - cx) / max(cx, 1)) ** 2)
    tot = pw.sum()
    f1 = float(pw[r > 0.25].sum() / tot) if tot > 0 else 0.0
    h2 = float(g.std())
    b1 = bg_uniformity(g)
    hq, _ = np.histogram(g, bins=16, range=(0, 255))
    pq = hq / max(1, hq.sum()); pq = pq[pq > 0]
    t1 = float(-(pq * np.log(pq)).sum() / np.log(16))
    return {"E1": round(e1, 4), "E2": round(e2, 3), "S1": round(s1, 1),
            "F1": round(f1, 4), "H2": round(h2, 1), "B1": round(b1, 2), "T1": round(t1, 3)}

def cmp_pair(o, t):
    out = {}
    wins = losses = 0
    for m in METRICS:
        a, b = o[m], t[m]
        if m == "B1":  # 越低越好
            a, b = -a, -b
        if a > b:
            out[m] = "win"; wins += 1
        elif a < b * LOSS_TOL:
            out[m] = "loss"; losses += 1
        else:
            out[m] = "tie"
    out["composite"] = wins - losses
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ours', required=True)
    ap.add_argument('--thumbs', default='/tmp/nv960')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    ours_map = json.load(open(args.ours))
    rows = [r for r in their_assets() if r['category_id'] in ALL_IDS]
    board = {"pairs": [], "per_metric": {m: {"W": 0, "T": 0, "L": 0} for m in METRICS},
             "classes": {}}
    n = 0
    for r in rows:
        cid = r['category_id']
        our = ours_map.get(cid)
        if not our or not os.path.exists(our):
            continue
        base = r['path'].replace('rigid/', '').replace('/', '_')
        thumbs = sorted(glob.glob(f"{args.thumbs}/{base}*.png"))
        if not thumbs:
            continue
        o = pixstats(crop62(our))
        cw = cl = 0
        for t in thumbs:
            tm = pixstats(crop62(t))
            c = cmp_pair(o, tm)
            n += 1
            for m in METRICS:
                board["per_metric"][m][c[m][0].upper()] += 1
            if c["composite"] > 0: cw += 1
            elif c["composite"] < 0: cl += 1
            board["pairs"].append({"category": cid, "their": os.path.basename(t),
                                   "our": o, "their": tm, "cmp": c})
        board["classes"].setdefault(cid, {"win": 0, "loss": 0, "total": 0})
        board["classes"][cid]["win"] += cw
        board["classes"][cid]["loss"] += cl
        board["classes"][cid]["total"] += len(thumbs)
    board["summary"] = {"pairs": n, "composite_win": sum(1 for p in board["pairs"] if p["cmp"]["composite"] > 0),
                        "composite_tie": sum(1 for p in board["pairs"] if p["cmp"]["composite"] == 0),
                        "composite_loss": sum(1 for p in board["pairs"] if p["cmp"]["composite"] < 0)}
    json.dump(board, open(args.out, 'w'), ensure_ascii=False)
    s = board["summary"]
    print(json.dumps(s, ensure_ascii=False))
    for m in METRICS:
        w = board["per_metric"][m]
        print(f"{m}: W{w['W']} T{w['T']} L{w['L']}  胜率 {w['W']/max(n,1)*100:.1f}%")

if __name__ == '__main__':
    main()
