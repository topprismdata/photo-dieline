"""PoC: 前馈多视角几何 (VGGT-1B, 零训练) 从 ABO 实拍估计物体长宽高比例, 对比官方尺寸比例。
只读; 输出 /tmp/pd_recheck/vggt_abo.json + 输入图贴板。"""
import json, os, sys, time, numpy as np, torch
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "/tmp/pd_recheck/vggt_repo")
from vggt.models.vggt import VGGT
from vggt.utils.load_fn import load_and_preprocess_images
ROOT = "/Users/guohongbin/photo-dieline"; D = f"{ROOT}/output/datasets/abo_bench30"
man = json.load(open(f"{ROOT}/docs/abo_bench30_manifest.json"))
items = []
for it in man:
    fs = [it["file"]] + [v["file"] for v in it.get("views", [])]
    fs = [f for f in fs if os.path.exists(os.path.join(D, f))]
    dims = it.get("dims_in") or {}
    if len(fs) >= 2 and all(k in dims for k in ("height", "length", "width")):
        items.append((it, fs))
print("items with >=2 views + dims:", len(items), flush=True)
dev = "mps" if torch.backends.mps.is_available() else "cpu"
model = VGGT.from_pretrained("facebook/VGGT-1B").to(dev).eval()
S = 518
def crop255(path):
    im = Image.open(path).convert("RGB")
    s = S / min(im.size); nw, nh = max(S, round(im.width*s)), max(S, round(im.height*s))
    im = im.resize((nw, nh), Image.BICUBIC)
    l = (nw - S)//2; t = (nh - S)//2
    return np.asarray(im.crop((l, t, l+S, t+S))).astype(np.float32)
res = []; tiles = []
for it, fs in items:
    t0 = time.time()
    try:
        imgs = load_and_preprocess_images([os.path.join(D, f) for f in fs])
        with torch.no_grad():
            pred = model(imgs[None].to(dev))
        wp = pred["world_points"][0].float().cpu().numpy(); cf = pred["world_points_conf"][0].float().cpu().numpy()
        pts = []; whites = []
        for k, f in enumerate(fs):
            a = crop255(os.path.join(D, f)); bg = a.min(2) > 232
            whites.append(float(bg[:8].mean() + bg[-8:].mean() + bg[:, :8].mean() + bg[:, -8:].mean()) / 4)
            m = (~bg) & (cf[k] > np.percentile(cf[k], 40))
            pts.append(wp[k][m])
        P = np.concatenate(pts); P = P[np.isfinite(P).all(1)]
        c = P.mean(0); Q = P - c
        _, _, vt = np.linalg.svd(Q[::max(1, len(Q)//20000)], full_matrices=False)
        proj = Q @ vt.T
        lo, hi = np.percentile(proj, 1.5, 0), np.percentile(proj, 98.5, 0)
        ext = np.sort(hi - lo)[::-1]
        off = np.sort([dims := it["dims_in"], ][0]["height"]*25.4, )[::-1] if False else np.sort([it["dims_in"]["height"]*25.4, it["dims_in"]["length"]*25.4, it["dims_in"]["width"]*25.4])[::-1]
        r_est = ext[1:]/ext[0]; r_off = off[1:]/off[0]
        err = float(np.abs(r_est - r_off).mean())
        res.append({"item": it["item_id"], "structure": it.get("structure"), "n_views": len(fs), "ext_est": [round(float(x), 3) for x in ext],
                    "dims_off_mm": [round(float(x), 1) for x in off], "ratio_est": [round(float(x), 3) for x in r_est], "ratio_off": [round(float(x), 3) for x in r_off],
                    "ratio_abs_err": round(err, 4), "white_border": round(float(np.mean(whites)), 3), "n_pts": int(len(P)), "sec": round(time.time()-t0, 1)})
        print(json.dumps(res[-1]), flush=True)
        row = Image.new("RGB", (S*len(fs)//2, S//2+18), (18,18,18)); d = ImageDraw.Draw(row)
        for k, f in enumerate(fs): row.paste(Image.open(os.path.join(D, f)).convert("RGB").resize((S//2, S//2)), (k*S//2, 18))
        d.text((4, 2), f"{it['item_id']} {it.get('structure')} est={np.round(r_est,2).tolist()} off={np.round(r_off,2).tolist()} err={err:.3f}", fill=(255,230,0))
        tiles.append(row)
    except Exception as e:
        print("ERR", it["item_id"], repr(e)[:200], flush=True)
json.dump(res, open("/tmp/pd_recheck/vggt_abo.json", "w"), indent=1)
if tiles:
    W = max(t.width for t in tiles); sheet = Image.new("RGB", (W, sum(t.height for t in tiles)), (18,18,18)); y = 0
    for t in tiles: sheet.paste(t, (0, y)); y += t.height
    sheet.save("/tmp/pd_recheck/vggt_abo_inputs.png")
good = [r for r in res if r["white_border"] > 0.9]
print("DONE n=%d; 白底件 n=%d: 比例平均绝对相对误差 mean=%.3f median=%.3f (常数基线=官方比例中位数 %.3f)" % (
    len(res), len(good), np.mean([r["ratio_abs_err"] for r in good]) if good else -1, np.median([r["ratio_abs_err"] for r in good]) if good else -1,
    np.mean([np.abs(np.median([x["ratio_off"] for x in good], 0) - x["ratio_off"]).mean() for x in good]) if good else -1), flush=True)
