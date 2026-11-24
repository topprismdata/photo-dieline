"""假设检验: gable 比例回归误差 vs 主体在画面中的大小 (只读, 复算)."""
import json, glob, math, sys
import numpy as np, torch
from PIL import Image
from torchvision.models import resnet18
ROOT = "/Users/guohongbin/photo-dieline"
REL = [("W","Hb"),("D","Hb"),("Hr","Hb"),("Ef","Hb")]
man = json.load(open(f"{ROOT}/output/tde_mve/dataset_manifest.json"))
rad = {v["vid"]: v["radius_mm"] for v in man["variants"]}
labels = [json.loads(open(p).read()) for p in sorted(glob.glob(f"{ROOT}/output/tde_mve/labels/s_*.json")) if "_probe" not in p]
val_v = set(np.random.default_rng(7).choice(30, 6, replace=False).tolist())
val = [l for l in labels if l["variant"] in val_v]
Y = np.array([[l["params_gt"][a]/l["params_gt"][b] for a,b in REL] for l in val])
fill, dist, fe, pitch = [], [], [], []
for l in val:
    cp = l["capture"]; r = rad[l["variant"]]
    tan_half = 18.0/cp["equiv_focal_mm"]; d = cp["distance_mm"]/1000.0
    rm = l["render_payload"].get("_r_meas_m", 0.0)
    if rm > 0:
        d_fit = rm/tan_half*1.30
        if d*1.35 < d_fit: d = d_fit/1.35
    d_eye = d*1.35*1000.0
    fill.append(r/(d_eye*tan_half)); dist.append(d_eye); fe.append(cp["equiv_focal_mm"]); pitch.append(cp["pitch_deg"])
fill = np.array(fill)
q = lambda v: np.round(np.percentile(v, [5, 25, 50, 75, 95]), 3)
print("主体包围球半径/半画幅 (1.0=球刚好内切画幅):", q(fill), " <0.25: %.0f%%  <0.20: %.0f%%  <0.15: %.0f%%" % (100*(fill<0.25).mean(), 100*(fill<0.20).mean(), 100*(fill<0.15).mean()))
print("等效应素: 盒高≈2·fill·192·(盒高/2R) — 盒高像素估计 p5/50/95:", end=" ")
hpx = np.array([2*fill[i]*192*(labels_val_h := (val[i]["params_gt"]["Hb"]+val[i]["params_gt"]["Hr"])/(2*rad[val[i]["variant"]])) for i in range(len(val))])
print(q(hpx))
dev = "mps" if torch.backends.mps.is_available() else "cpu"
ck = torch.load(f"{ROOT}/runs/e1_seed42/best.pt", map_location="cpu", weights_only=False)
net = resnet18(weights=None); net.fc = torch.nn.Linear(net.fc.in_features, 12); net.load_state_dict(ck["model"]); net.to(dev).eval()
pred = []
with torch.no_grad():
    for l in val:
        im = Image.open(f"{ROOT}/output/tde_mve/images/{l['sample_id']}.png").convert("RGB").resize((384,384), Image.BILINEAR)
        x = torch.from_numpy(np.asarray(im).transpose(2,0,1).copy()).float()/255.0
        x = ((x - torch.tensor([0.485,0.456,0.406])[:,None,None]) / torch.tensor([0.229,0.224,0.225])[:,None,None])[None].to(dev)
        pred.append(net(x)[0].view(3,4)[1].cpu().numpy())
pred = np.array(pred); err = np.abs(pred - Y)
med = np.median(np.array([[l["params_gt"][a]/l["params_gt"][b] for a,b in REL] for l in labels if l["variant"] not in val_v]),0)
base = np.abs(np.tile(med,(len(val),1)) - Y)
print("\n按主体大小分箱: raw MAE(模型) | raw MAE(常数基线) | 相对误差(÷val均值) | n")
for lo, hi in [(0,0.15),(0.15,0.20),(0.20,0.25),(0.25,0.30),(0.30,0.40),(0.40,9)]:
    m = (fill>=lo)&(fill<hi)
    if m.sum() < 10: continue
    e = err[m].mean(0); b = base[m].mean(0)
    print(f"  fill[{lo:.2f},{hi if hi<9 else 9:.2f}) n={m.sum():4d} | 模型 {e.round(4)} mean={e.mean():.4f} | 常数 {b.round(4)} mean={b.mean():.4f} | 相对 {(e/Y[m].mean(0)*100).round(1)} mean={(e/Y[m].mean(0)).mean()*100:.2f}%")
print("\n误差与 fill 的 Spearman 相关 (逐比例):", [round(float(np.corrcoef(np.argsort(np.argsort(fill)), np.argsort(np.argsort(err[:,i])))[0,1]),3) for i in range(4)])
np.save("/tmp/pd_recheck/e1_seed42_val_pred.npy", pred); np.save("/tmp/pd_recheck/val_fill.npy", fill)
