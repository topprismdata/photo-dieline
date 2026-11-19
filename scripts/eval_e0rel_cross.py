"""E1 消融交叉评估: {all-tier, REALISTIC-only} × {REALISTIC, MODERATE, STRESS} val 矩阵."""
import json, sys
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_e0rel import REL, RelDataset

root = Path("/Users/guohongbin/photo-dieline/output/tde_mve")
dev = "mps" if torch.backends.mps.is_available() else "cpu"
labels = [json.loads(p.read_text()) for p in sorted(root.glob("labels/s_*.json"))
          if "_probe" not in p.name]
val_v = set(np.random.default_rng(7).choice(30, 6, replace=False).tolist())
stats = {"mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]}

print(f"{'model':<18}{'REALISTIC':>12}{'MODERATE':>12}{'STRESS':>12}")
for name, ck in (("all-tier", "/Users/guohongbin/photo-dieline/runs/e0rel/best.pt"),
                 ("REALISTIC-only", "/Users/guohongbin/photo-dieline/runs/e0rel_R/best.pt")):
    net = torch.load(ck, map_location=dev, weights_only=False)["model"]
    from torchvision.models import resnet18
    m = resnet18(weights=None)
    m.fc = torch.nn.Linear(m.fc.in_features, len(REL) * 3)
    m.load_state_dict(net)
    m = m.to(dev).eval()
    row = []
    for tier in ("REALISTIC", "MODERATE", "STRESS"):
        ds = RelDataset(root, val_v, stats, tier=tier)
        # RelDataset 构造已按 variant 留出过滤; 此处再按 capture.tier 精滤
        ds.rows = [(lab, ip) for lab, ip in ds.rows
                   if lab.get("capture", {}).get("tier") == tier]
        errs = []
        with torch.no_grad():
            for x, y in DataLoader(ds, batch_size=32):
                p = m(x.to(dev)).view(-1, 3, len(REL))[:, 1, :].cpu()
                errs += (p - y).abs().mean(1).tolist()
        row.append(f"{100 * float(np.mean(errs)):.2f}%")
    print(f"{name:<18}{row[0]:>12}{row[1]:>12}{row[2]:>12}")
