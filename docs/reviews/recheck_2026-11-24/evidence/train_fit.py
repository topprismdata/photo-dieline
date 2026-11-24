"""分解: 训练几何拟合误差 vs 留出几何误差 (只读)."""
import json, glob, numpy as np, torch
from PIL import Image
from torchvision.models import resnet18
ROOT = "/Users/guohongbin/photo-dieline"
REL = [("W","Hb"),("D","Hb"),("Hr","Hb"),("Ef","Hb")]
labels = [json.loads(open(p).read()) for p in sorted(glob.glob(f"{ROOT}/output/tde_mve/labels/s_*.json")) if "_probe" not in p]
val_v = set(np.random.default_rng(7).choice(30, 6, replace=False).tolist())
dev = "mps" if torch.backends.mps.is_available() else "cpu"
ck = torch.load(f"{ROOT}/runs/e1_seed42/best.pt", map_location="cpu", weights_only=False)
net = resnet18(weights=None); net.fc = torch.nn.Linear(net.fc.in_features, 12); net.load_state_dict(ck["model"]); net.to(dev).eval()
def run(pool):
    P, Y = [], []
    with torch.no_grad():
        for l in pool:
            im = Image.open(f"{ROOT}/output/tde_mve/images/{l['sample_id']}.png").convert("RGB").resize((384,384), Image.BILINEAR)
            x = torch.from_numpy(np.asarray(im).transpose(2,0,1).copy()).float()/255.0
            x = ((x - torch.tensor([0.485,0.456,0.406])[:,None,None]) / torch.tensor([0.229,0.224,0.225])[:,None,None])[None].to(dev)
            P.append(net(x)[0].view(3,4)[1].cpu().numpy()); Y.append([l["params_gt"][a]/l["params_gt"][b] for a,b in REL])
    return np.array(P), np.array(Y), np.array([l["variant"] for l in pool])
tr = [l for l in labels if l["variant"] not in val_v]; rng = np.random.default_rng(1); tr = [tr[i] for i in rng.choice(len(tr), 1200, replace=False)]
Ptr, Ytr, Vtr = run(tr)
e_tr = np.abs(Ptr - Ytr); print("训练集(见过几何) raw MAE %s mean=%.4f" % (e_tr.mean(0).round(4), e_tr.mean()))
pv = np.load("/tmp/pd_recheck/e1_seed42_val_pred.npy")
val = [l for l in labels if l["variant"] in val_v]; Yv = np.array([[l["params_gt"][a]/l["params_gt"][b] for a,b in REL] for l in val])
e_va = np.abs(pv - Yv); print("验证集(留出几何) raw MAE %s mean=%.4f" % (e_va.mean(0).round(4), e_va.mean()))
# 训练集上: 每个训练变体的预测均值 vs 真值 (几何记忆程度)
print("训练变体: 预测中位误差(跨视角平均后) =", end=" ")
res = []
for v in sorted(set(Vtr.tolist())):
    m = Vtr == v; res.append(np.abs(np.median(Ptr[m],0) - Ytr[m][0]))
res = np.array(res); print(res.mean(0).round(4), "mean=%.4f" % res.mean(), "(n变体=%d)" % len(res))
resv = []
for v in sorted(val_v):
    m = np.array([l["variant"] == v for l in val]); resv.append(np.abs(np.median(pv[m],0) - Yv[m][0]))
resv = np.array(resv); print("留出变体: 预测中位误差(跨视角平均后) =", resv.mean(0).round(4), "mean=%.4f" % resv.mean())
# 最近训练几何距离 vs 留出误差
G = {v: Ytr[Vtr == v][0] for v in sorted(set(Vtr.tolist()))}
Gk = np.array(list(G.values()))
for v, r in zip(sorted(val_v), resv):
    g = Yv[[l["variant"] == v for l in val]][0]
    dd = np.sqrt((((Gk - g)/Gk.std(0))**2).sum(1))
    print("  留出 v%-2d 真值 %s → 最近训练几何归一化距离 %.2f | 逐视角MAE %.4f | 跨视角平均后 %.4f" % (v, g.round(3), dd.min(), e_va[np.array([l["variant"] == v for l in val])].mean(), r.mean()))
