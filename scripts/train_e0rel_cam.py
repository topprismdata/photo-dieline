"""E3-B: Oracle Camera 条件化比例回归 — 照片+已知相机内外参输入 (误差来源分解对照组).

A组(现有 E0rel): 仅照片 → 4-9% 经验误差带
B组(本脚本): 照片 + (focal, pitch, yaw, distance/radius) → 若显著优于 A, 相机不确定性为主要误差源
C组(解析): B 比例 × 真值 Hb → 绝对误差下限
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_e0rel import REL, quantile_loss, QUANTILES  # noqa: E402

CAM_DIMS = 4  # focal/50, pitch/35, yaw/30, dist_norm


class CamDataset(Dataset):
    def __init__(self, root: Path, variant_split: set[int], tier: str = "all",
                 use_cam: bool = True):
        self.rows = []
        self.use_cam = use_cam
        self.rng_norm = 18.0
        for lp in sorted(root.glob("labels/s_*.json")):
            if "_probe" in lp.name:
                continue
            lab = json.loads(lp.read_text())
            if lab["variant"] not in variant_split:
                continue
            if tier != "all" and lab.get("capture", {}).get("tier") != tier:
                continue
            self.rows.append((lab, root / "images" / f"{lab['sample_id']}.png"))

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        lab, img_path = self.rows[i]
        im = Image.open(img_path).convert("RGB").resize((384, 384), Image.BILINEAR)
        x = torch.from_numpy(np.asarray(im).transpose(2, 0, 1).copy()).float() / 255.0
        mean = torch.tensor([0.485, 0.456, 0.406], dtype=torch.float32)[:, None, None]
        std = torch.tensor([0.229, 0.224, 0.225], dtype=torch.float32)[:, None, None]
        x = (x - mean) / std
        cam = lab["render_payload"]["camera"]
        cap = lab["capture"]
        r_mm = max(lab["params_gt"].get("W", 60), lab["params_gt"].get("Hb", 105)) * 0.9
        camv = (torch.tensor([
            cam["equiv_focal_mm"] / 50.0,
            cam["pitch_deg"] / 35.0,
            cam["yaw_deg"] / 30.0,
            cam["distance_m"] * 1000.0 / max(r_mm, 1.0),
        ], dtype=torch.float32) if self.use_cam else torch.zeros(4))
        p = lab["params_gt"]
        y = torch.tensor([p[a] / p[b] for a, b in REL], dtype=torch.float32)
        return x, camv, y


class CamNet(nn.Module):
    def __init__(self, n_out: int):
        super().__init__()
        from torchvision.models import resnet18
        try:
            self.backbone = resnet18(weights="IMAGENET1K_V1")
        except Exception:
            self.backbone = resnet18(weights=None)
        feat = self.backbone.fc.in_features
        self.backbone.fc = nn.Identity()
        self.head = nn.Sequential(
            nn.Linear(feat + CAM_DIMS, 256), nn.ReLU(), nn.Linear(256, n_out))

    def forward(self, x, camv):
        f = self.backbone(x)
        return self.head(torch.cat([f, camv], dim=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="output/tde_mve")
    ap.add_argument("--epochs", type=int, default=32)
    ap.add_argument("--tier", default="all")
    ap.add_argument("--out", default="runs/e0rel_cam")
    ap.add_argument("--no-cam", action="store_true",
                    help="E3干净对照: 同架构去掉相机输入 (误差来源分解)")
    args = ap.parse_args()
    root = Path(args.data)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    labels = [json.loads(p.read_text()) for p in sorted(root.glob("labels/s_*.json"))
              if "_probe" not in p.name]
    if args.tier != "all":
        labels = [l for l in labels if l.get("capture", {}).get("tier") == args.tier]
    val_v = set(np.random.default_rng(7).choice(30, 6, replace=False).tolist())
    pre = np.array([[l["params_gt"][a] / l["params_gt"][b] for a, b in REL]
                    for l in labels if l["variant"] not in val_v], float)
    rstd_l = [float(pre[:, i].std()) for i in range(len(REL))]
    ds_tr = CamDataset(root, set(range(30)) - val_v, args.tier, use_cam=not args.no_cam)
    ds_va = CamDataset(root, val_v, args.tier, use_cam=not args.no_cam)
    tl = DataLoader(ds_tr, batch_size=32, shuffle=True, num_workers=0)
    vl = DataLoader(ds_va, batch_size=32, num_workers=0)
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    net = CamNet(len(REL) * 3).to(dev)
    opt = torch.optim.AdamW(net.parameters(), lr=3e-4, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, args.epochs)
    log = {"config": vars(args) | {"device": dev}, "epochs": []}
    names = [f"{a}/{b}" for a, b in REL]
    best = 1e9
    for ep in range(args.epochs):
        net.train()
        t0, tr = time.time(), 0.0
        for x, c, y in tl:
            x, c, y = x.to(dev), c.to(dev), y.to(dev)
            opt.zero_grad()
            loss = quantile_loss(net(x, c), y)
            loss.backward()
            opt.step()
            tr += float(loss.detach()) * len(x)
        sched.step()
        net.eval()
        errs = [[] for _ in REL]
        with torch.no_grad():
            for x, c, y in vl:
                pred = net(x.to(dev), c.to(dev)).view(-1, 3, len(REL))
                med = pred[:, 1, :].cpu()
                for i in range(len(REL)):
                    # raw 单位 (勘误纪律: 不乘 rstd)
                    errs[i] += (med[:, i] - y[:, i]).abs().tolist()
        raw_mae = {k: round(float(np.mean(e)), 4) for k, e in zip(names, errs)}
        mean_raw = float(np.mean(list(raw_mae.values())))
        rec = {"epoch": ep, "train_loss": round(tr / len(ds_tr), 4),
               "raw_ratio_mae": raw_mae, "mean_raw": round(mean_raw, 4),
               "sec": round(time.time() - t0, 1)}
        log["epochs"].append(rec)
        if mean_raw < best:
            best = mean_raw
            torch.save({"model": net.state_dict(), "rel": REL}, out / "best.pt")
        print(f"ep{ep}: loss={rec['train_loss']} rawMAE={raw_mae} mean={mean_raw:.4f}",
              flush=True)
        (out / "train_log.json").write_text(json.dumps(log, indent=1))
    print(f"BEST mean raw ratio MAE: {best}", flush=True)


if __name__ == "__main__":
    main()
