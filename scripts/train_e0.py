"""TDE MVE E0 基线训练: ResNet18 + 384² + 分位数回归 (Q10/Q50/Q90).

规范: docs/tde-spec.md §4 (标签三分离; 辅助任务后续; 按 variant 分割防泄漏).
用法: python3 scripts/train_e0.py --data output/tde_mve --epochs 8 --out runs/e0
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

PARAMS = ["W", "D", "Hb", "Hr", "Ef"]
QUANTILES = (0.1, 0.5, 0.9)


class TDEDataset(Dataset):
    def __init__(self, root: Path, variant_split: set[int], stats, pstd):
        self.pstd = pstd
        self.rows = []
        for lp in sorted(root.glob("labels/s_*.json")):
            if "_probe" in lp.name:
                continue
            lab = json.loads(lp.read_text())
            if lab["variant"] not in variant_split:
                continue
            self.rows.append((lab, root / "images" / f"{lab['sample_id']}.png"))
        self.stats = stats

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        lab, img_path = self.rows[i]
        im = Image.open(img_path).convert("RGB")
        # v1: 直接 resize 384 (真实域随机化含分辨率维度; RandAugment 留 E1)
        im = im.resize((384, 384), Image.BILINEAR)
        x = torch.from_numpy(np.asarray(im).transpose(2, 0, 1).copy()).float() / 255.0
        mean = torch.tensor(self.stats["mean"], dtype=torch.float32)[:, None, None]
        std = torch.tensor(self.stats["std"], dtype=torch.float32)[:, None, None]
        x = (x - mean) / std
        p = lab["params_gt"]
        y = torch.tensor([p[k] / self.pstd[i] for i, k in enumerate(PARAMS)], dtype=torch.float32)
        return x, y


def quantile_loss(pred, target):
    """pred: (B, P*3) 按 Q10/Q50/Q90 排列; pinball loss."""
    losses = []
    for qi, q in enumerate(QUANTILES):
        p = pred[:, qi * len(PARAMS):(qi + 1) * len(PARAMS)]
        d = target - p
        losses.append(torch.maximum(q * d, (q - 1) * d))
    return torch.stack(losses, dim=1).mean()


def norm_stats(root: Path, variant_split, n=64):
    rng = np.random.default_rng(0)
    files = sorted(root.glob("images/s_*.png"))
    files = [f for f in files if "_probe" not in f.name]
    pick = rng.choice(len(files), min(n, len(files)), replace=False)
    acc = []
    for i in pick:
        im = np.asarray(Image.open(files[int(i)]).convert("RGB"), float) / 255.0
        acc.append(im.reshape(-1, 3)[::17])
    acc = np.concatenate(acc)
    return {"mean": acc.mean(0).tolist(), "std": (acc.std(0) + 1e-6).tolist()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="output/tde_mve")
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--out", default="runs/e0")
    ap.add_argument("--backbone", default="resnet18", choices=["resnet18", "vit_tiny"])
    args = ap.parse_args()
    root = Path(args.data)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # 按 variant 分割 (24 训练 / 6 验证) — 防结构泄漏
    all_v = set(range(30))
    val_v = set(rng for rng in sorted(np.random.default_rng(7).choice(30, 6, replace=False)))
    train_v = all_v - val_v
    stats = norm_stats(root, train_v)

    # 先算参数归一化尺度 (训练集真值 std), 注入数据集 (loss 在归一化域, 报告回 mm)
    pre_rows = []
    for lp in sorted(root.glob("labels/s_*.json")):
        if "_probe" in lp.name:
            continue
        lab = json.loads(lp.read_text())
        if lab["variant"] in train_v:
            pre_rows.append(lab["params_gt"])
    ys = np.array([[pr[k] for k in PARAMS] for pr in pre_rows], float)
    pstd = {k: float(ys[:, i].std()) for i, k in enumerate(PARAMS)}
    pstd_l = [pstd[k] for k in PARAMS]
    ds_tr = TDEDataset(root, train_v, stats, pstd_l)
    ds_va = TDEDataset(root, val_v, stats, pstd_l)
    tl = DataLoader(ds_tr, batch_size=args.batch, shuffle=True, num_workers=4)
    vl = DataLoader(ds_va, batch_size=args.batch, num_workers=2)

    if args.backbone == "resnet18":
        from torchvision.models import resnet18
        try:
            net = resnet18(weights="IMAGENET1K_V1")
        except Exception:
            net = resnet18(weights=None)
        net.fc = nn.Linear(net.fc.in_features, len(PARAMS) * 3)
    else:
        raise SystemExit("vit_tiny 留 E1 (规范: MVE 先 ResNet18 立基线)")

    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    net = net.to(dev)
    opt = torch.optim.AdamW(net.parameters(), lr=3e-4, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, args.epochs)

    ds_tr.pstd, ds_va.pstd = pstd_l, pstd_l

    log = {"config": vars(args) | {"device": dev, "train_v": len(train_v), "val_v": len(val_v)},
           "param_std_mm": pstd, "epochs": []}
    best = 1e9
    for ep in range(args.epochs):
        net.train()
        t0, tr_loss = time.time(), 0.0
        for x, y in tl:
            x, y = x.to(dev), y.to(dev)
            opt.zero_grad()
            loss = quantile_loss(net(x), y)
            loss.backward()
            opt.step()
            tr_loss += float(loss) * len(x)
        sched.step()
        net.eval()
        errs = [[] for _ in PARAMS]
        with torch.no_grad():
            for x, y in vl:
                pred = net(x.to(dev)).view(-1, 3, len(PARAMS))
                pstd_t = torch.tensor([pstd[k] for k in PARAMS])
                med = pred[:, 1, :].cpu() * pstd_t
                yy = y.cpu() * pstd_t
                for i in range(len(PARAMS)):
                    errs[i] += (med[:, i] - yy[:, i]).abs().tolist()
        mae = {k: round(float(np.mean(e)), 3) for k, e in zip(PARAMS, errs)}
        p90 = {k: round(float(np.percentile(e, 90)), 3) for k, e in zip(PARAMS, errs)}
        rec = {"epoch": ep, "train_loss": round(tr_loss / len(ds_tr), 4),
               "val_mae_mm": mae, "val_p90_mm": p90,
               "val_mae_norm": round(float(np.mean([mae[k] / pstd[k] for k in PARAMS])), 4),
               "sec": round(time.time() - t0, 1)}
        log["epochs"].append(rec)
        total_mae = float(np.mean(list(mae.values())))
        if total_mae < best:
            best = total_mae
            torch.save({"model": net.state_dict(), "params": PARAMS,
                        "stats": stats, "pstd": pstd}, out / "best.pt")
        print(f"ep{ep}: loss={rec['train_loss']} MAE(mm)={mae} P90={p90['Hr'] if 'Hr' in p90 else ''}", flush=True)
        (out / "train_log.json").write_text(json.dumps(log, indent=1))
    print(f"BEST mean MAE(mm): {round(best, 3)} | 通过门: 合成验证 MAE ≤0.5mm → {'PASS' if best <= 0.5 else 'FAIL'}")


if __name__ == "__main__":
    main()
