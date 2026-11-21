#!/usr/bin/env python3
"""make_planogram_det: SKU-110K 检测实证 → planogram 分组精化 (ESR Step A v2).

证据升级: facings_evidence vlm_est → sku110k_det
- 每层检测按 x 排序, x-gap > 0.5×中位袋宽 → 分簇 = SKU 组
- 组边界 = 簇内首末检测框的 x 范围 (x0_frac/width_frac)
- color/form/design_id: 与 VLM 组按 x 重叠≥40% 继承; 新组继承最近组
- VLM 原组保留在 vlm_ref (审计)
用法: python3 scripts/make_planogram_det.py [--render-check]
"""
import glob
import json
import sys

import numpy as np
from pathlib import Path

ROOT = Path(__file__).parent.parent
PLANO = ROOT / "data/shelf_twin/planogram.json"
DET = Path("/Users/guohongbin/gate-spatial/evidence/m31/hxl_sku110k_detect.json")
W_IMG = 800.0


def clusters(layer_dets, med_w=None):
    """x 排序 → 间隙膝点分簇: 组内小间隙 vs 组界大间隙 双峰, 最大相对跌落为断点."""
    ds = sorted(layer_dets, key=lambda d: d["x"])
    if len(ds) < 3:
        return [ds]
    gaps = []
    for a, b in zip(ds, ds[1:]):
        gaps.append(max(0.0, b["x"] - (a["x"] + a.get("w", 30))))
    order = np.argsort(gaps)[::-1]
    gsorted = [gaps[i] for i in order]
    # 膝点: 相邻排序间隙的最大比值跌落 (限制组数 3..10)
    kmin, kmax = 2, min(9, len(gsorted) - 1)
    best_k, best_ratio = kmin, 0.0
    for k in range(kmin, kmax):
        r = gsorted[k - 1] / max(gsorted[k], 1e-6)
        if r > best_ratio:
            best_ratio, best_k = r, k
    thr = gsorted[best_k]
    groups, cur = [], [ds[0]]
    for a, b in zip(ds, ds[1:]):
        gap = max(0.0, b["x"] - (a["x"] + a.get("w", 30)))
        if gap >= thr:
            groups.append(cur)
            cur = [b]
        else:
            cur.append(b)
    groups.append(cur)
    return groups


def main():
    det = json.loads(DET.read_text())
    pj = json.loads(PLANO.read_text())
    W = W_IMG
    for lv in pj["levels"]:
        i = lv["level"]
        dets = det["per_layer_detections"].get(f"L{i+1}", [])
        if len(dets) < 2:
            lv.setdefault("detection_note", "检测过少, 组保留 VLM")
            continue
        cls = clusters(dets)
        vlm_old = lv["groups"]
        UNIT_W = {"bag": 0.12, "barrel": 0.11, "box": 0.10}  # 品类单位宽 m (同 make_planogram)

        # 按簇序比例映射 VLM 组序列 (保行内颜色多样性; 检测簇<VLM组时避免重复继承同一灰设计)
        def inherit_for(gi, g):
            m = len(vlm_old)
            idx = min(m - 1, round(gi * (m - 1) / max(1, len(cls) - 1)))
            return vlm_old[idx]

        # 密排满墙: 排面×单位宽平铺全幅 (检测间隙=漏检≠空位, A 实证袋贴袋)
        new_groups = []
        for ci, g in enumerate(cls):
            inh = inherit_for(ci, g)
            new_groups.append({
                "color": inh["color"], "design_id": inh["design_id"], "form": inh["form"],
                "facings": len(g), "facings_evidence": "sku110k_det",
                "avg_conf": round(float(np.mean([d.get("conf", 0.5) for d in g])), 3),
            })
        tw = sum(UNIT_W[g["form"]] * g["facings"] for g in new_groups) or 1.0
        acc = 0.0
        for g in new_groups:
            wf = UNIT_W[g["form"]] * g["facings"] / tw
            g["x0_frac"] = round(acc, 4)
            g["width_frac"] = round(wf, 4)
            acc += wf
        lv["vlm_ref"] = vlm_old
        lv["groups"] = sorted(new_groups, key=lambda g: g["x0_frac"])
        lv["detection_note"] = f"sku110k_det: {len(dets)} 检测 → {len(new_groups)} 组"
    json.dump(pj, PLANO.open("w"), indent=1, ensure_ascii=False)
    n_det = sum(1 for lv in pj["levels"] if any(
        g.get("facings_evidence") == "sku110k_det" for g in lv["groups"]))
    print(f"精化完成: {n_det}/7 层接入检测证据")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
