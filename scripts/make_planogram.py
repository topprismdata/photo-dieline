#!/usr/bin/env python3
"""make_planogram: 合成 planogram.json (ESR Step A 终版).

证据来源分层:
- 结构/组序列/排面数: VLM 全图结构化读取 (2026-11-21 会话, 参照对齐语境)
- 招牌带: 像素量测 (红色行占比)
- 设计映射: 家族色 → Topprism 12 设计 (公开轨品牌替换)
- 宽度: facings × 品类单位宽 (真实 planogram 分配算法), 输出 width_frac
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

REF = Path(__file__).parent.parent / "data/shelf_twin_ref/primary.jpg"
OUT = Path(__file__).parent.parent / "data/shelf_twin/planogram.json"

# VLM 全图读取 (2026-11-21): 排1..7 (排7 partial)
ROWS = [
    [("green", 4, "box"), ("brown", 7, "box"), ("brown", 3, "bag"), ("purple", 4, "bag"),
     ("yellow", 5, "bag"), ("red", 4, "bag")],
    [("yellow", 6, "box"), ("gold", 4, "box"), ("yellow", 4, "box"), ("red", 3, "bag"),
     ("yellow", 3, "bag"), ("blue", 4, "bag"), ("green", 5, "bag"), ("red", 4, "bag")],
    [("green", 2, "barrel"), ("red", 5, "barrel"), ("green", 4, "barrel"), ("red", 5, "bag"),
     ("blue", 4, "bag"), ("purple", 4, "bag"), ("yellow", 3, "bag")],
    [("yellow", 4, "barrel"), ("blue", 5, "barrel"), ("red", 4, "bag"), ("blue", 4, "bag"),
     ("yellow", 4, "bag"), ("green", 4, "bag")],
    [("pink", 4, "barrel"), ("red", 4, "barrel"), ("yellow", 3, "barrel"), ("purple", 3, "bag"),
     ("orange", 4, "bag"), ("dark", 3, "bag"), ("yellow", 7, "bag")],
    [("dark", 3, "box"), ("pink", 3, "box"), ("red", 5, "box"), ("orange", 3, "bag"),
     ("dark", 3, "bag"), ("yellow", 4, "bag")],
    [("purple", 3, "bag"), ("blue", 5, "bag"), ("red", 5, "bag")],
]
PARTIAL = [False] * 6 + [True]
FAMILY_IDX = {"red": 0, "orange": 1, "yellow": 2, "green": 3, "blue": 4, "purple": 5,
              "brown": 6, "pink": 7, "teal": 8, "gold": 9, "white": 10, "dark": 11}
UNIT_W = {"bag": 0.12, "barrel": 0.11, "box": 0.10}  # m, 品类单位宽 (含间隙)


def sign_band_frac():
    """像素量测: 红色行占比 → 招牌带."""
    a = np.asarray(Image.open(REF).convert("RGB")).astype(float) / 255
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red_rows = ((r > 0.45) & (r - g > 0.18) & (r - b > 0.18)).mean(axis=1)
    rows = np.where(red_rows > 0.5)[0]
    if len(rows):
        return {"top_frac": round(rows.min() / a.shape[0], 3),
                "bottom_frac": round(rows.max() / a.shape[0], 3),
                "method": "pixel_red_band"}
    return {"method": "not_detected"}


def main():
    levels = []
    for lv, groups in enumerate(ROWS):
        # 宽度 ∝ facings × 单位宽 (真实 planogram 分配)
        weights = [f * UNIT_W[form] for (_, f, form) in groups]
        total = sum(weights)
        out_groups = []
        x = 0.0
        for (fam, f, form), wgt in zip(groups, weights):
            wf = wgt / total
            out_groups.append({
                "color": fam,
                "design_id": f"tp_{FAMILY_IDX[fam]:02d}",
                "facings": f,
                "facings_evidence": "vlm_est",
                "form": form,
                "x0_frac": round(x, 4),
                "width_frac": round(wf, 4),
            })
            x += wf
        levels.append({"level": lv, "partial": PARTIAL[lv], "groups": out_groups})

    plan = {
        "schema": "shelf-planogram/1.1",
        "source": {
            "reference": "data/shelf_twin_ref/primary.jpg",
            "structure": "vlm_read_full_photo (2026-11-21, 参照对齐语境)",
            "facings": "vlm_est",
            "brand_replacement": "Topprism 12 设计族 (公开轨)",
        },
        "fixture": {
            "type": "backlit_wall",
            "width_m": 2.4,
            "levels": len(ROWS),
            "level_height_m": 0.38,
            "depth_m": 0.4,
            "evidence": "RECONCILIATION.md v2 量测",
        },
        "sign_band": sign_band_frac(),
        "levels": levels,
    }
    OUT.write_text(json.dumps(plan, ensure_ascii=False, indent=1))
    n_groups = sum(len(l["groups"]) for l in levels)
    print(f"planogram.json: {len(ROWS)} levels, {n_groups} groups")
    for l in levels:
        segs = " | ".join(f"{g['color']}[{g['form'][:2]}{g['facings']}]" for g in l["groups"])
        print(f"  L{l['level']}{'(partial)' if l['partial'] else ''}: {segs}")


if __name__ == "__main__":
    main()
