"""MVE 渲染后处理: 全量重算图像级门(含裁切检测) + 数据集报告.

裁切判据: 主体 mask 触及画面边缘(>15px 连续) → clipped → 不入 G0 (spec: 主体须完整).
"""
import json
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

root = Path("/Users/guohongbin/photo-dieline/output/tde_mve")


def image_gate(img: np.ndarray) -> dict:
    gray = img.mean(axis=2)
    lap = (np.roll(gray, 1, 0) + np.roll(gray, -1, 0) + np.roll(gray, 1, 1)
           + np.roll(gray, -1, 1) - 4 * gray)
    sharp = float(lap.var())
    corners = np.concatenate([img[:40, :40].reshape(-1, 3), img[:40, -40:].reshape(-1, 3),
                              img[-40:, :40].reshape(-1, 3), img[-40:, -40:].reshape(-1, 3)])
    bg = corners.mean(0)
    mask = np.abs(img - bg).sum(2) > 60
    frac = float(mask.mean())
    # 裁切判据由 3D 投影门提供 (box_fully_in_frame), 图像 mask 的 edge 检测被地面像素污染已废
    clipped = False
    h, w = img.shape[:2]
    ys, xs = np.nonzero(mask)
    bbox_frac = (float((ys.max() - ys.min()) / h) if len(ys) else 0.0,
                 float((xs.max() - xs.min()) / w) if len(xs) else 0.0)
    nondegenerate = float(gray.std()) > 5.0
    ok = bool(nondegenerate and 0.06 <= frac <= 0.93 and sharp >= 35.0 and not clipped)
    return {"sharpness_lapvar": round(sharp, 1), "subject_area_frac": round(frac, 3),
            "bbox_frac_hw": [round(bbox_frac[0], 3), round(bbox_frac[1], 3)],
            "clipped": clipped, "nondegenerate": nondegenerate, "pass": ok}


def main():
    labels = sorted(root.glob("labels/s_*.json"))
    labels = [p for p in labels if "_probe" not in p.name]
    stats = Counter()
    g0_rows = []
    for lp in labels:
        lab = json.loads(lp.read_text())
        img = np.asarray(Image.open(root / "images" / f"{lab['sample_id']}.png").convert("RGB"), float)
        iq = image_gate(img)
        lab["learnability_gate"] = iq
        lp.write_text(json.dumps(lab, ensure_ascii=False, indent=1))
        topo = lab["topology_gate"]["pass"]
        fully = lab["topology_gate"].get("box_fully_in_frame", False)
        g0 = bool(topo and iq["pass"] and fully)
        stats["total"] += 1
        stats["topo_pass"] += topo
        stats["learn_pass"] += iq["pass"]
        stats["clipped"] += iq["clipped"]
        stats["g0"] += g0
        if g0:
            g0_rows.append({"sample_id": lab["sample_id"], "variant": lab["variant"],
                            "tier": lab["capture"]["tier"], "scene": lab["capture"]["scene"],
                            "params_gt": lab["params_gt"]})
    print("total:", stats["total"], "| topo:", stats["topo_pass"],
          f"({100*stats['topo_pass']/stats['total']:.1f}%)",
          "| learn:", stats["learn_pass"], f"({100*stats['learn_pass']/stats['total']:.1f}%)",
          "| clipped:", stats["clipped"],
          "| G0 双门:", stats["g0"], f"({100*stats['g0']/stats['total']:.1f}%)")
    out = {"dataset_version": "mve-0.1-fixed-axis", "total": stats["total"],
           "topology_pass": stats["topo_pass"], "learnability_pass": stats["learn_pass"],
           "clipped": stats["clipped"], "g0_count": stats["g0"],
           "g0_ratio": round(stats["g0"] / stats["total"], 4),
           "g0_subset": g0_rows}
    (root / "dataset_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print("report ->", root / "dataset_report.json")


if __name__ == "__main__":
    main()
