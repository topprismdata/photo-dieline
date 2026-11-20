"""E3-A 分析: 同几何跨视角预测方差 (相机敏感性) + 逐因素分解.

GPT 判决的指标: 同一几何跨视角预测方差; Oracle 对照的 A 组基线.
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

import numpy as np
import torch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_e0rel import REL  # noqa: E402

ROOT = Path("/Users/guohongbin/photo-dieline")
OUT = ROOT / "output" / "e3_camsweep"
dev = "mps" if torch.backends.mps.is_available() else "cpu"
ck = torch.load(ROOT / "runs/e0rel/best.pt", map_location=dev, weights_only=False)
from torchvision.models import resnet18  # noqa: E402
net = resnet18(weights=None)
net.fc = torch.nn.Linear(net.fc.in_features, len(REL) * 3)
net.load_state_dict(ck["model"])
net = net.to(dev).eval()
mean = torch.tensor([0.485, 0.456, 0.406])[:, None, None]
std = torch.tensor([0.229, 0.224, 0.225])[:, None, None]

man = json.loads((OUT / "e3_manifest.json").read_text())
by_var = defaultdict(list)
for r in man["rows"]:
    vdir = OUT / f"v{r['variant']}"
    lab = json.loads((vdir / "labels" / f"s_{r['sid']:04d}.json").read_text())
    im = Image.open(vdir / "images" / f"s_{r['sid']:04d}.png").convert("RGB") \
        .resize((384, 384), Image.BILINEAR)
    x = (torch.from_numpy(np.asarray(im).transpose(2, 0, 1).copy()).float() / 255.0 - mean) / std
    with torch.no_grad():
        pred = net(x[None].to(dev)).view(3, len(REL))[1].cpu()
    # 真值比例 (全相机相同)
    p = man["variants"][r["variant"]]["params"]
    y = np.array([p[a] / p[b] for a, b in REL])
    by_var[r["variant"]].append({**r, "pred": pred.numpy(), "true": y})

print("=== E3-A: 同几何跨视角 (27 相机) 预测一致性 ===")
names = [f"{a}/{b}" for a, b in REL]
all_stds = []
for vi, rows in sorted(by_var.items()):
    P = np.array([r["pred"] for r in rows])
    Y = rows[0]["true"]
    pred_mean = P.mean(0)
    pred_std = P.std(0)
    all_stds.append(pred_std)
    err_vs_true = np.abs(pred_mean - Y)
    print(f"v{vi}: pred_mean={np.round(pred_mean, 3)}")
    print(f"     跨视角std={np.round(pred_std, 4)}  |mean_pred-true|={np.round(err_vs_true, 4)}")
S = np.mean(np.array(all_stds), 0)
print("\n=== 平均跨视角 std (raw 比例单位) ===")
for n, s in zip(names, S):
    print(f"  {n}: {s:.4f}")
print(f"  mean: {S.mean():.4f}")

# 逐因素方差分解: 按 focal / pitch / yaw 分组的组内 std 对比
print("\n=== 逐因素组内 std (谁贡献相机敏感性) ===")
for factor in ("focal", "pitch", "yaw"):
    groups = defaultdict(list)
    for rows in by_var.values():
        for r in rows:
            groups[r[factor]].append(r["pred"])
    # 组间均值的离散度 (该因素的效应)
    gm = np.array([np.mean(groups[k], 0) for k in sorted(groups)])
    between = gm.std(0)
    print(f"  {factor}: 组间均值std = {np.round(between, 4)} (mean {between.mean():.4f})")

# 距离效应 (distance 随 focal 变化, 单独列出不重复计)
gd = defaultdict(list)
for rows in by_var.values():
    for r in rows:
        gd[round(r["distance_m"], 2)].append(r["pred"])
gm = np.array([np.mean(gd[k], 0) for k in sorted(gd)])
print(f"  distance: 组间均值std = {np.round(gm.std(0), 4)} (mean {gm.std(0).mean():.4f})")

# 保存
np.save(OUT / "e3a_predictions.npy",
        np.array([[r["pred"] for r in by_var[vi]] for vi in sorted(by_var)]))
print("\nsaved: e3_camsweep/e3a_predictions.npy")
