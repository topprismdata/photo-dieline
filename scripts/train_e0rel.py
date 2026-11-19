"""E0-rel: 相对参数化实验 (选型③) — 学比例向量, 绝对尺度交给配准仪器 (职责分离).

目标: y = [W/Hb, D/Hb, Hr/Hb, Ef/Hb] 4 维比例 (Hb 锚=1)
假设: 单视图尺度歧义下绝对 mm 病态 (E0' 实证 7-9% 齐平), 比例可学性 ≥ 绝对
评估: 比例 MAE (%) + 派生绝对 MAE 下限 (给定真 Hb 时)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_e0 import QUANTILES  # noqa: E402

PARAMS = ["W", "D", "Hb", "Hr", "Ef"]
REL = [("W", "Hb"), ("D", "Hb"), ("Hr", "Hb"), ("Ef", "Hb")]


class RelDataset(Dataset):
    def __init__(self, root: Path, variant_split: set[int], stats, tier: str = "all"):
        self.stats = stats
        self.tier = tier
        self.rows = []
        for lp in sorted(root.glob("labels/s_*.json")):
            if "_probe" in lp.name:
                continue
            lab = json.loads(lp.read_text())
            if lab["variant"] not in variant_split:
                continue
            if self.tier != "all" and lab.get("capture", {}).get("tier") != self.tier:
                continue
            self.rows.append((lab, root / "images" / f"{lab['sample_id']}.png"))

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        lab, img_path = self.rows[i]
        im = Image.open(img_path).convert("RGB").resize((384, 384), Image.BILINEAR)
        x = torch.from_numpy(np.asarray(im).transpose(2, 0, 1).copy()).float() / 255.0
        mean = torch.tensor(self.stats["mean"], dtype=torch.float32)[:, None, None]
        std = torch.tensor(self.stats["std"], dtype=torch.float32)[:, None, None]
        x = (x - mean) / std
        p = lab["params_gt"]
        y = torch.tensor([p[a] / p[b] for a, b in REL], dtype=torch.float32)
        return x, y


def quantile_loss(pred, target):
    losses = []
    for qi, q in enumerate(QUANTILES):
        p = pred[:, qi * len(REL):(qi + 1) * len(REL)]
        d = target - p
        losses.append(torch.maximum(q * d, (q - 1) * d))
    return torch.stack(losses, dim=1).mean()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="output/tde_mve")
    ap.add_argument("--epochs", type=int, default=32)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--out", default="runs/e0rel")
    ap.add_argument("--tier", default="all",
                    help="E1消融: all | REALISTIC | MODERATE | MAX (按capture.tier过滤)")
    args = ap.parse_args()
    root = Path(args.data)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    labels = [json.loads(p.read_text()) for p in sorted(root.glob("labels/s_*.json"))
              if "_probe" not in p.name]
    if args.tier != "all":
        labels = [l for l in labels
                  if l.get("capture", {}).get("tier") == args.tier]
        print(f"tier filter {args.tier}: {len(labels)} samples")
    all_v = set(range(30))
    val_v = set(np.random.default_rng(7).choice(30, 6, replace=False).tolist())
    pre = np.array([[l["params_gt"][a] / l["params_gt"][b] for a, b in REL]
                    for l in labels if l["variant"] not in val_v], float)
    rstd = {f"{a}/{b}": float(pre[:, i].std()) for i, (a, b) in enumerate(REL)}
    rstd_l = [rstd[f"{a}/{b}"] for a, b in REL]

    ds_tr = RelDataset(root, set(range(30)) - val_v,
                       {"mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]},
                       tier=args.tier)
    ds_va = RelDataset(root, val_v, ds_tr.stats, tier=args.tier)
    tl = DataLoader(ds_tr, batch_size=32, shuffle=True, num_workers=4)
    vl = DataLoader(ds_va, batch_size=32, num_workers=2)

    from torchvision.models import resnet18
    try:
        net = resnet18(weights="IMAGENET1K_V1")
    except Exception:
        net = resnet18(weights=None)
    net.fc = nn.Linear(net.fc.in_features, len(REL) * 3)
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    net = net.to(dev)
    opt = torch.optim.AdamW(net.parameters(), lr=3e-4, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, args.epochs)

    log = {"mode": "relative_parametrization", "config": vars(args) | {"device": dev},
           "rel_ratio_std": rstd, "epochs": []}
    best = 1e9
    names = [f"{a}/{b}" for a, b in REL]
    for ep in range(args.epochs):
        net.train()
        t0, tr = time.time(), 0.0
        for x, y in tl:
            x, y = x.to(dev), y.to(dev)
            opt.zero_grad()
            loss = quantile_loss(net(x), y)
            loss.backward()
            opt.step()
            tr += float(loss.detach()) * len(x)
        sched.step()
        net.eval()
        errs = [[] for _ in REL]
        with torch.no_grad():
            for x, y in vl:
                pred = net(x.to(dev)).view(-1, 3, len(REL))
                med = pred[:, 1, :].cpu() * torch.tensor(rstd_l)
                yy = y.cpu() * torch.tensor(rstd_l)
                for i in range(len(REL)):
                    errs[i] += (med[:, i] - yy[:, i]).abs().tolist()
        mae = {k: round(float(np.mean(e)), 4) for k, e in zip(names, errs)}
        rel_pct = {k: round(100 * float(np.mean(e)), 2) for k, e in zip(names, errs)}
        rec = {"epoch": ep, "train_loss": round(tr / len(ds_tr), 4),
               "val_ratio_mae": mae, "val_ratio_mae_pct": rel_pct,
               "mean_pct": round(float(np.mean(list(rel_pct.values()))), 2),
               "sec": round(time.time() - t0, 1)}
        log["epochs"].append(rec)
        if rec["mean_pct"] < best:
            best = rec["mean_pct"]
            torch.save({"model": net.state_dict(), "rel": REL}, out / "best.pt")
        print(f"ep{ep}: loss={rec['train_loss']} ratioMAE%={rel_pct} mean%={rec['mean_pct']}", flush=True)
        (out / "train_log.json").write_text(json.dumps(log, indent=1))
    print(f"BEST mean ratio MAE: {best}% (比例误差 → 绝对尺度由配准仪器 P0-2 提供)")


if __name__ == "__main__":
    main()
