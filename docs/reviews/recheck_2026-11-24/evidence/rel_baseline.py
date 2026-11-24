"""独立复算: gable 比例回归 vs 常数基线 + 门禁FAIL样本占比 (只读)."""
import json, glob, sys
import numpy as np, torch
from PIL import Image
from torchvision.models import resnet18
ROOT = "/Users/guohongbin/photo-dieline"
REL = [("W","Hb"),("D","Hb"),("Hr","Hb"),("Ef","Hb")]
labels = [json.loads(open(p).read()) for p in sorted(glob.glob(f"{ROOT}/output/tde_mve/labels/s_*.json")) if "_probe" not in p]
val_v = set(np.random.default_rng(7).choice(30, 6, replace=False).tolist())
Y = np.array([[l["params_gt"][a]/l["params_gt"][b] for a,b in REL] for l in labels])
V = np.array([l["variant"] for l in labels]); val = np.isin(V, list(val_v))
tg = np.array([bool(l["topology_gate"]["pass"]) for l in labels])
lg = np.array([bool(l["learnability_gate"]["pass"]) for l in labels])
area = np.array([l["learnability_gate"]["subject_area_frac"] for l in labels])
print("n=%d train=%d val=%d  val_variants=%s" % (len(Y), (~val).sum(), val.sum(), sorted(val_v)))
print("gate PASS rates: train topo %.1f%% learn %.1f%% both %.1f%% | val topo %.1f%% learn %.1f%% both %.1f%%" % (
    100*tg[~val].mean(), 100*lg[~val].mean(), 100*(tg&lg)[~val].mean(), 100*tg[val].mean(), 100*lg[val].mean(), 100*(tg&lg)[val].mean()))
print("subject_area_frac: train median %.3f  val median %.3f  frac<0.10: train %.1f%% val %.1f%%" % (
    np.median(area[~val]), np.median(area[val]), 100*(area[~val]<0.10).mean(), 100*(area[val]<0.10).mean()))
# 变体级参数
vp = {}
for l in labels: vp[l["variant"]] = [l["params_gt"][k] for k in ["W","D","Hb","Hr","Ef"]]
P = np.array([vp[k] for k in sorted(vp)])
print("variants (W,D,Hb,Hr,Ef mm):"); 
for i,(k,r) in enumerate(zip(sorted(vp), P)): print("  v%-2d %-28s %s  %s" % (k, np.round(r,1), "VAL" if k in val_v else "", np.round([r[0]/r[2], r[1]/r[2], r[3]/r[2], r[4]/r[2]],3)))
def report(name, pred):
    mae = np.abs(pred - Y[val]).mean(0); rel = mae / Y[val].mean(0) * 100
    print("%-22s raw MAE %s  mean=%.4f | 相对(÷val均值)%% %s  mean=%.2f%%" % (name, np.round(mae,4), mae.mean(), np.round(rel,2), rel.mean()))
    return mae.mean()
med = np.median(Y[~val],0); mean = Y[~val].mean(0)
b1 = report("常数=训练中位数", np.tile(med,(val.sum(),1)))
b2 = report("常数=训练均值", np.tile(mean,(val.sum(),1)))
print("val target mean %s std %s | train std %s" % (np.round(Y[val].mean(0),3), np.round(Y[val].std(0),4), np.round(Y[~val].std(0),4)))
dev = "mps" if torch.backends.mps.is_available() else "cpu"
for run in sys.argv[1:]:
    ck = torch.load(f"{ROOT}/runs/{run}/best.pt", map_location="cpu", weights_only=False)
    net = resnet18(weights=None); net.fc = torch.nn.Linear(net.fc.in_features, 12); net.load_state_dict(ck["model"]); net.to(dev).eval()
    out = []
    with torch.no_grad():
        for i in np.where(val)[0]:
            im = Image.open(f"{ROOT}/output/tde_mve/images/{labels[i]['sample_id']}.png").convert("RGB").resize((384,384), Image.BILINEAR)
            x = torch.from_numpy(np.asarray(im).transpose(2,0,1).copy()).float()/255.0
            x = ((x - torch.tensor([0.485,0.456,0.406])[:,None,None]) / torch.tensor([0.229,0.224,0.225])[:,None,None])[None].to(dev)
            out.append(net(x)[0].view(3,4)[1].cpu().numpy())
    pred = np.array(out); report(f"model:{run}(seed={ck.get('seed')})", pred)
    # 只看双门通过的子集
    ok = (tg&lg)[val]
    mae = np.abs(pred[ok]-Y[val][ok]).mean(0); print("    └ 仅双门PASS子集(n=%d): raw MAE %s mean=%.4f" % (ok.sum(), np.round(mae,4), mae.mean()))
    # 逐变体
    print("    └ 逐变体raw MAE:", {int(v): round(float(np.abs(pred[V[val]==v]-Y[val][V[val]==v]).mean()),4) for v in sorted(val_v)})
