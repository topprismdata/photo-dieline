"""T1 Top-5 候选路由原型 (GPT 判决: 候选识别器而非硬路由 + KNOWN/AMBIGUOUS/UNKNOWN 拒绝机制).

决策规则 (v1, 依据 docs/T1_multiclass.md 实证):
  - top-5 家族并集覆盖真实家族 99.0% → 输出候选集交下游折叠拟合残差裁决
  - margin (top1-top2 logit 差) 过小 → AMBIGUOUS_TYPE (交给残差裁决, 不硬判)
  - top-5 概率质量过低 → UNKNOWN_TYPE (拒绝)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image

ROOT = Path("/Users/guohongbin/photo-dieline")
sys.path.insert(0, str(ROOT / "src"))

MARGIN_AMBIGUOUS = 1.0   # top1-top2 logit 差 < 此值 → AMBIGUOUS
CONF_UNKNOWN = 0.30      # top5 softmax 质量 < 此值 → UNKNOWN


def load_router(checkpoint: Path = ROOT / "runs/t1/best.pt"):
    from torchvision.models import resnet18
    ck = torch.load(checkpoint, map_location="cpu", weights_only=False)
    net = resnet18(weights=None)
    net.fc = torch.nn.Linear(net.fc.in_features, len(ck["classes"]))
    net.load_state_dict(ck["model"])
    net.eval()
    rows = json.loads((ROOT / "output/zoo100/batch_report.json").read_text())["rows"]
    fam = {r["class_id"]: r["family"] for r in rows}
    return net, ck["classes"], fam


def route(net, classes, fam, image_path: Path, device: str = "cpu"):
    im = Image.open(image_path).convert("RGB").resize((384, 384), Image.BILINEAR)
    x = torch.from_numpy(np.asarray(im).transpose(2, 0, 1).copy()).float() / 255.0
    x = (x - torch.tensor([0.485, 0.456, 0.406])[:, None, None]) / \
        torch.tensor([0.229, 0.224, 0.225])[:, None, None]
    with torch.no_grad():
        logits = net(x[None].to(device))[0].cpu()
    probs = torch.softmax(logits, 0)
    top5 = probs.topk(5)
    margin = float(logits[top5.indices[0]] - logits[top5.indices[1]])
    conf = float(top5.values.sum())
    cand = [{"class_id": classes[int(i)], "family": fam.get(classes[int(i)], "?"),
             "p": round(float(p), 4)} for p, i in zip(top5.values, top5.indices)]
    families = sorted({c["family"] for c in cand})
    if conf < CONF_UNKNOWN:
        decision = "UNKNOWN_TYPE"
    elif margin < MARGIN_AMBIGUOUS:
        decision = "AMBIGUOUS_TYPE"
    else:
        decision = "KNOWN_TYPE"
    return {"decision": decision, "margin": round(margin, 3), "top5_conf": round(conf, 3),
            "candidates": cand, "candidate_families": families,
            "note": "候选集交折叠拟合残差裁决; 本模块不做最终结构裁决 (T1_multiclass.md)"}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+")
    args = ap.parse_args()
    net, classes, fam = load_router()
    for p in args.images:
        r = route(net, classes, fam, Path(p))
        print(json.dumps({"image": p, **r}, ensure_ascii=False))


if __name__ == "__main__":
    main()
