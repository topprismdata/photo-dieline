"""T1 多类分类训练: 100 类包装模板家族, zoo_t1 合成集.

评估协议 (规范冻结):
  - 留出: 每类最后 1 个 variant (5 变体轮转留出 → 变体级泛化)
  - 指标: top-1 / top-5 / 混淆矩阵家族级 (family 聚合)
  - 类平衡: 每类恰好 30 张, 无需重加权
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

ROOT = Path("/Users/guohongbin/photo-dieline")
DATA = ROOT / "output" / "zoo_t1"


class T1Dataset(Dataset):
    def __init__(self, rows, classes):
        self.rows = rows
        self.classes = classes
        self.mean = [0.485, 0.456, 0.406]
        self.std = [0.229, 0.224, 0.225]

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        img_path, cid = self.rows[i]
        im = Image.open(img_path).convert("RGB").resize((384, 384), Image.BILINEAR)
        x = torch.from_numpy(np.asarray(im).transpose(2, 0, 1).copy()).float() / 255.0
        mean = torch.tensor(self.mean, dtype=torch.float32)[:, None, None]
        std = torch.tensor(self.std, dtype=torch.float32)[:, None, None]
        return (x - mean) / std, self.classes.index(cid)


def load_rows(holdout_variant: int):
    """每类 5 变体; 留出 variant==holdout_variant 的样本做验证."""
    tr, va = [], []
    classes = sorted({p.name for p in DATA.iterdir() if p.is_dir()})
    for cid in classes:
        for lp in sorted((DATA / cid / "labels").glob("s_*.json")):
            lab = json.loads(lp.read_text())
            if lab.get("class_id") != cid:
                continue  # 旧标签无 class_id → 跳过 (生成器已回写)
            img = ROOT / lab["render_payload"]["out_png"]
            (va if lab["variant"] == holdout_variant else tr).append((img, cid))
    return tr, va, classes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=24)
    ap.add_argument("--holdout-variant", type=int, default=4)
    ap.add_argument("--out", default="runs/t1")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    tr_rows, va_rows, classes = load_rows(args.holdout_variant)
    print(f"train={len(tr_rows)} val={len(va_rows)} classes={len(classes)}", flush=True)
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    from torchvision.models import resnet18
    try:
        net = resnet18(weights="IMAGENET1K_V1")
    except Exception:
        net = resnet18(weights=None)
    net.fc = nn.Linear(net.fc.in_features, len(classes))
    net = net.to(dev)
    tl = DataLoader(T1Dataset(tr_rows, classes), batch_size=64, shuffle=True,
                    num_workers=6, persistent_workers=True)
    vl = DataLoader(T1Dataset(va_rows, classes), batch_size=64, num_workers=4)
    opt = torch.optim.AdamW(net.parameters(), lr=3e-4, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, args.epochs)

    log = {"config": vars(args) | {"device": dev, "n_classes": len(classes),
                                    "n_train": len(tr_rows), "n_val": len(va_rows)},
           "epochs": []}
    best = 0.0
    fam_of = defaultdict(str)
    report = json.loads((ROOT / "output/zoo100/batch_report.json").read_text())
    for r in report["rows"]:
        fam_of[r["class_id"]] = r["family"]
    fam_ids = {c: fam_of.get(c, "?") for c in classes}
    for ep in range(args.epochs):
        net.train()
        t0, tr_loss = time.time(), 0.0
        for x, y in tl:
            x, y = x.to(dev), y.to(dev)
            opt.zero_grad()
            loss = nn.functional.cross_entropy(net(x), y)
            loss.backward()
            opt.step()
            tr_loss += float(loss.detach()) * len(x)
        sched.step()
        net.eval()
        hits, top5, fam_hits, n = 0, 0, 0, 0
        with torch.no_grad():
            for x, y in vl:
                p = net(x.to(dev))
                k = p.topk(5, dim=1).indices.cpu()
                hits += (k[:, 0] == y).sum().item()
                top5 += (k == y[:, None]).any(1).sum().item()
                for ki, yi in zip(k[:, 0].tolist(), y.tolist()):
                    n += 1
                    if fam_ids[classes[ki]] == fam_ids[classes[yi]]:
                        fam_hits += 1
        rec = {"epoch": ep, "train_loss": round(tr_loss / len(tr_rows), 4),
               "val_top1": round(hits / n, 4), "val_top5": round(top5 / n, 4),
               "family_top1": round(fam_hits / n, 4),
               "sec": round(time.time() - t0, 1)}
        log["epochs"].append(rec)
        if rec["val_top1"] > best:
            best = rec["val_top1"]
            torch.save({"model": net.state_dict(), "classes": classes}, out / "best.pt")
        print(f"ep{ep}: loss={rec['train_loss']} top1={rec['val_top1']} "
              f"top5={rec['val_top5']} fam={rec['family_top1']}", flush=True)
        (out / "train_log.json").write_text(json.dumps(log, indent=1))
    print(f"BEST top1={best}", flush=True)


if __name__ == "__main__":
    main()
