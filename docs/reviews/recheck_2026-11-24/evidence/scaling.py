"""学习曲线: 留出几何误差 vs 训练几何数量 (复刻 train_e0rel 配方; 内存数据集). 结果追加写 /tmp/pd_recheck/scaling.json"""
import json, glob, time, sys, numpy as np, torch, torch.nn as nn
from PIL import Image
from torchvision.models import resnet18
torch.backends.mps.manual_seed = lambda s: torch.manual_seed(s)
ROOT = "/Users/guohongbin/photo-dieline"
REL = [("W","Hb"),("D","Hb"),("Hr","Hb"),("Ef","Hb")]; Q = (0.1, 0.5, 0.9)
labels = [json.loads(open(p).read()) for p in sorted(glob.glob(f"{ROOT}/output/tde_mve/labels/s_*.json")) if "_probe" not in p]
val_v = sorted(np.random.default_rng(7).choice(30, 6, replace=False).tolist())
t0 = time.time()
X = torch.stack([torch.from_numpy(np.asarray(Image.open(f"{ROOT}/output/tde_mve/images/{l['sample_id']}.png").convert("RGB")).transpose(2,0,1).copy()) for l in labels])
Y = torch.tensor([[l["params_gt"][a]/l["params_gt"][b] for a,b in REL] for l in labels], dtype=torch.float32)
V = torch.tensor([l["variant"] for l in labels]); valm = torch.isin(V, torch.tensor(val_v))
mean = torch.tensor([0.485,0.456,0.406])[:,None,None]; std = torch.tensor([0.229,0.224,0.225])[:,None,None]
Xv = ((X[valm].float()/255.0) - mean)/std; Yv = Y[valm]; Vv = V[valm]
tr_order = [int(v) for v in np.random.default_rng(0).choice(sorted(set(range(30)) - set(val_v)), 24, replace=False)]
print("preload %.0fs | val n=%d | train variant order=%s" % (time.time()-t0, int(valm.sum()), tr_order), flush=True)
dev = "mps" if torch.backends.mps.is_available() else "cpu"
def qloss(pred, target):
    return torch.stack([torch.maximum(q*(target - pred[:, i*4:(i+1)*4]), (q-1)*(target - pred[:, i*4:(i+1)*4])) for i, q in enumerate(Q)], 1).mean()
def evaluate(net):
    net.eval(); P = []
    with torch.no_grad():
        for i in range(0, len(Xv), 64): P.append(net(Xv[i:i+64].to(dev)).view(-1,3,4)[:,1,:].cpu())
    P = torch.cat(P); e = (P - Yv).abs()
    va = []
    for v in val_v:
        m = Vv == v; va.append((P[m].median(0).values - Yv[m][0]).abs())
    return float(e.mean()), e.mean(0).tolist(), float(torch.stack(va).mean())
out_path = "/tmp/pd_recheck/scaling.json"
try:
    results = json.load(open(out_path))
except Exception:
    results = []
for seed in (11, 23):
    for k in (6, 12, 24):
        use = tr_order[:k]; m = torch.isin(V, torch.tensor(use)) & ~valm
        Xt = ((X[m].float()/255.0) - mean)/std; Yt = Y[m]; n = len(Xt)
        torch.manual_seed(seed)
        net = resnet18(weights="IMAGENET1K_V1"); net.fc = nn.Linear(net.fc.in_features, 12); net = net.to(dev)
        opt = torch.optim.AdamW(net.parameters(), lr=3e-4, weight_decay=1e-4); ep_n = 32
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, ep_n); g = torch.Generator().manual_seed(seed)
        best = (9, None); t1 = time.time(); curve = []
        for ep in range(ep_n):
            net.train(); perm = torch.randperm(n, generator=g); tot = 0.0
            for i in range(0, n, 32):
                idx = perm[i:i+32]; xb = Xt[idx].to(dev); yb = Yt[idx].to(dev)
                opt.zero_grad(); loss = qloss(net(xb), yb); loss.backward(); opt.step(); tot += float(loss.detach())*len(idx)
            sched.step()
            if ep >= 7 and (ep % 4 == 3 or ep == ep_n-1):
                e, per, avg = evaluate(net); curve.append([ep, round(e,4)])
                if e < best[0]: best = (e, per)
                print(f"seed{seed} k={k} ep{ep} loss={tot/n:.4f} val_raw={e:.4f} viewavg={avg:.4f} ({time.time()-t1:.0f}s)", flush=True)
        rec = {"seed": seed, "k_train_variants": k, "n_train": n, "val_raw_mae": round(best[0],4), "per_ratio": [round(x,4) for x in best[1]], "curve": curve, "sec": round(time.time()-t1)}
        results.append(rec); json.dump(results, open(out_path, "w"), indent=1)
        print("DONE", json.dumps({k2: v for k2, v in rec.items() if k2 != "curve"}), flush=True)
        del net, opt; 
        if dev == "mps": torch.mps.empty_cache()
