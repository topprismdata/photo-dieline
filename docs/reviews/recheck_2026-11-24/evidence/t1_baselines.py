"""T1 对照: 训练过的 ResNet18 (现役) vs 零训练 DINOv2 kNN — 合成验证集 + ABO 真实棚拍."""
import sys, glob, json, collections, numpy as np, torch, timm
from PIL import Image
sys.path.insert(0, "/Users/guohongbin/photo-dieline/scripts")
import route_t1
ROOT = "/Users/guohongbin/photo-dieline"
net18, classes, fam = route_t1.load_router()
fams = sorted(set(fam.values())); print("families(%d): %s" % (len(fams), fams))
def grp(f):
    if f in ("rsc", "crashlock", "lockbottom"): return "corrugated_box"
    if f in ("gable", "brick", "window_front"): return "gable_or_carton"
    if f in ("tube", "cone"): return "bottle_jug"
    if f in ("egg", "cup", "sushi", "pyramid", "pillow", "pyramid_ext", "display"): return "other_package"
    return "folding_box"
# ---- 数据
tr, va = [], []
for cid in classes:
    for lp in sorted(glob.glob(f"{ROOT}/output/zoo_t1/{cid}/labels/s_*.json")):
        lab = json.loads(open(lp).read())
        if lab.get("class_id") != cid: continue
        (va if lab["variant"] == 4 else tr).append((lab["render_payload"]["out_png"], cid))
print("train %d val %d" % (len(tr), len(va)))
real = [(p, p.split("/")[-1].split("_")[1]) for p in sorted(glob.glob(f"{ROOT}/output/datasets/abo_pack/*.jpg"))]
# ---- DINOv2
dev = "mps" if torch.backends.mps.is_available() else "cpu"
m = timm.create_model("vit_small_patch14_dinov2.lvd142m", pretrained=True, num_classes=0, img_size=336).to(dev).eval()
mean = torch.tensor([0.485,0.456,0.406])[:,None,None]; std = torch.tensor([0.229,0.224,0.225])[:,None,None]
def embed(paths, bs=16, S=336):
    out = []
    with torch.no_grad():
        for i in range(0, len(paths), bs):
            xs = []
            for p in paths[i:i+bs]:
                im = Image.open(p).convert("RGB").resize((S, S), Image.BICUBIC)
                xs.append(torch.from_numpy(np.asarray(im).transpose(2,0,1).copy()).float()/255.0)
            f = m(((torch.stack(xs) - mean)/std).to(dev)).float().cpu()
            out.append(torch.nn.functional.normalize(f, dim=1))
    return torch.cat(out)
Etr = embed([p for p,_ in tr]); Eta = embed([p for p,_ in va]); Ere = embed([p for p,_ in real])
ltr = [c for _, c in tr]; lta = [c for _, c in va]
def knn_topk(E, k=5):
    s = E @ Etr.T; return s.topk(k, dim=1)
def metrics(topv, topi, labels, name):
    pred = [[ltr[int(j)] for j in row] for row in topi]
    t1 = np.mean([p[0] == y for p, y in zip(pred, labels)])
    t5 = np.mean([y in p for p, y in zip(pred, labels)])
    ft1 = np.mean([fam[p[0]] == fam[y] for p, y in zip(pred, labels)])
    print(f"{name}: top1={t1*100:.1f}% top5={t5*100:.1f}% 家族级top1={ft1*100:.1f}% (n={len(labels)})")
    return pred
v, i = knn_topk(Eta); pred_va = metrics(v, i, lta, "DINOv2 kNN  | 合成验证集(留出变体4)")
# 现役 ResNet18 在同一验证集
ok1 = ok5 = okf = 0; confs = []
with torch.no_grad():
    for (p, y) in va:
        x = route_t1.Image.open(p).convert("RGB").resize((384,384), route_t1.Image.BILINEAR)
        x = torch.from_numpy(np.asarray(x).transpose(2,0,1).copy()).float()/255.0
        x = ((x - torch.tensor([0.485,0.456,0.406])[:,None,None]) / torch.tensor([0.229,0.224,0.225])[:,None,None])[None]
        pr = torch.softmax(net18(x)[0], 0).topk(5)
        c = [classes[int(j)] for j in pr.indices]; ok1 += c[0] == y; ok5 += y in c; okf += fam[c[0]] == fam[y]; confs.append(float(pr.values.sum()))
print(f"ResNet18(现役) | 合成验证集(留出变体4): top1={ok1/len(va)*100:.1f}% top5={ok5/len(va)*100:.1f}% 家族级top1={okf/len(va)*100:.1f}%  (top5概率质量 mean={np.mean(confs):.2f})")
# ---- 真实照片 (ABO): 粗类口径 (真值=文件名关键词, 自身有噪声)
v2, i2 = knn_topk(Ere); pred_re = [[ltr[int(j)] for j in row] for row in i2]
ylab = [g for _, g in real]
def coarse_report(preds, name, decisions=None):
    hit1 = np.mean([grp(fam[p[0]]) == y for p, y in zip(preds, ylab)])
    hit5 = np.mean([y in [grp(fam[c]) for c in p] for p, y in zip(preds, ylab)])
    print(f"{name}: 粗类top1={hit1*100:.1f}% 粗类top5={hit5*100:.1f}% (n={len(ylab)}, 真值噪声: 关键词标)")
    for g in sorted(set(ylab)):
        idx = [k for k, y in enumerate(ylab) if y == g]
        print(f"    {g:16s} n={len(idx):2d} top1命中 {sum(grp(fam[preds[k][0]])==g for k in idx)}  top5命中 {sum(g in [grp(fam[c]) for c in preds[k]] for k in idx)}")
coarse_report(pred_re, "DINOv2 kNN | ABO真实棚拍")
rp = []
for p, _ in real:
    r = route_t1.route(net18, classes, fam, p); rp.append([c["class_id"] for c in r["candidates"]])
coarse_report(rp, "ResNet18(现役)| ABO真实棚拍")
dec = [route_t1.route(net18, classes, fam, p)["decision"] for p, _ in real]
kn = [k for k, d in enumerate(dec) if d == "KNOWN_TYPE"]
print("ResNet18 判为 KNOWN_TYPE 的 %d 张里: 粗类top1命中 %d 张 (即 %d 张是高置信错判)" % (len(kn), sum(grp(fam[rp[k][0]]) == ylab[k] for k in kn), sum(grp(fam[rp[k][0]]) != ylab[k] for k in kn)))
json.dump({"dino_val_top1": float(np.mean([p[0]==y for p,y in zip(pred_va,lta)])), "resnet_val_top1": ok1/len(va), "abo_dino": pred_re, "abo_resnet": rp, "abo_true": ylab, "decisions": dec}, open("/tmp/pd_recheck/t1_baselines.json","w"))
