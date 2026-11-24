"""GPT R1 点名遗漏的基线: 已见几何最近邻检索 + 尺寸查表 (不训练任何回归头)。
(a) 参数空间 oracle 查表: 留出样本直接取"比例真值最近"的训练变体的标签 = 任何查表法的下界。
(b) 图像空间 DINOv2 检索: 留出图 → 最近训练图 → 取其标签。"""
import json, glob, numpy as np, torch, timm
from PIL import Image
ROOT = "/Users/guohongbin/photo-dieline"
REL = [("W","Hb"),("D","Hb"),("Hr","Hb"),("Ef","Hb")]
labels = [json.loads(open(p).read()) for p in sorted(glob.glob(f"{ROOT}/output/tde_mve/labels/s_*.json")) if "_probe" not in p]
val_v = set(np.random.default_rng(7).choice(30, 6, replace=False).tolist())
V = np.array([l["variant"] for l in labels]); val = np.isin(V, list(val_v))
Y = np.array([[l["params_gt"][a]/l["params_gt"][b] for a,b in REL] for l in labels])
tr_var = sorted(set(V[~val].tolist())); Ytr_var = np.array([Y[(V == v).nonzero()[0][0]] for v in tr_var]); sd = Ytr_var.std(0)
def mae(pred): return float(np.abs(pred - Y[val]).mean())
out = {"cnn_e1_3seeds": 0.0166}
# (a) oracle 查表
pred = []
for i in np.where(val)[0]:
    d = np.sqrt((((Ytr_var - Y[i]) / sd) ** 2).sum(1)); pred.append(Ytr_var[d.argmin()])
out["oracle_param_table"] = round(mae(np.array(pred)), 4)
# (b) DINOv2 图像检索
dev = "mps" if torch.backends.mps.is_available() else "cpu"
m = timm.create_model("vit_small_patch14_dinov2.lvd142m", pretrained=True, num_classes=0, img_size=336).to(dev).eval()
mean = torch.tensor([0.485,0.456,0.406])[:,None,None]; std = torch.tensor([0.229,0.224,0.225])[:,None,None]
def embed(idxs):
    fs = []
    with torch.no_grad():
        for k in range(0, len(idxs), 16):
            xs = [torch.from_numpy(np.asarray(Image.open(f"{ROOT}/output/tde_mve/images/{labels[i]['sample_id']}.png").convert("RGB").resize((336, 336), Image.BILINEAR)).transpose(2,0,1).copy()).float()/255.0 for i in idxs[k:k+16]]
            fs.append(torch.nn.functional.normalize(m(((torch.stack(xs) - mean) / std).to(dev)).float().cpu(), dim=1))
    return torch.cat(fs)
tri, vai = np.where(~val)[0], np.where(val)[0]
Etr, Eva = embed(list(tri)), embed(list(vai))
S = Eva @ Etr.T; nn = S.argmax(1).numpy()
# 检索质量: 最近训练图是否来自"比例最近的训练变体"
true_nn_var = [tr_var[int(np.sqrt((((Ytr_var - Y[i]) / sd) ** 2).sum(1)).argmin())] for i in vai]
retr_var = [int(V[tri[j]]) for j in nn]
out["dino_retrieves_param_nearest_variant"] = round(float(np.mean([a == b for a, b in zip(retr_var, true_nn_var)])), 3)
out["dino_image_lookup"] = round(mae(Y[tri[nn]]), 4)
# 检索到的变体里再取该变体的标签中位 (= 变体识别 oracle): 识别对了误差才小
out["median_baseline"] = round(mae(np.tile(np.median(Y[~val], 0), (int(val.sum()), 1))), 4)
# 每个训练变体被多少留出图检索到 (查表是否退化为只认少数变体)
cnt = np.bincount(np.array([tr_var.index(v) for v in retr_var]), minlength=len(tr_var))
out["distinct_training_variants_hit"] = int((cnt > 0).sum()); out["hit_hist"] = cnt.tolist()
json.dump(out, open("/tmp/pd_recheck/knn_lookup.json", "w"), indent=1); print(json.dumps(out))
