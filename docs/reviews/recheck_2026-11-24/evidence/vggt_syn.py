"""受控 PoC: VGGT-1B × 3 视角合成渲染 (gable 留出几何 v_16) → 三边比例 vs 真值。
只读仓库; 产物写 /tmp/pd_recheck/vggt_syn/。用法: python3 vggt_syn.py"""
import json, math, os, subprocess, sys, time, numpy as np
ROOT = "/Users/guohongbin/photo-dieline"; OUT = "/tmp/pd_recheck/vggt_syn"; os.makedirs(OUT, exist_ok=True)
man = json.load(open(f"{ROOT}/output/tde_mve/dataset_manifest.json"))
V = {v["vid"]: v for v in man["variants"]}
gts = {}
for vid in (16, 23, 25):   # 留出几何各一
    labs = [json.loads(open(f"{ROOT}/output/tde_mve/labels/{f}").read()) for f in sorted(os.listdir(f"{ROOT}/output/tde_mve/labels")) if f.endswith(".json") and "_probe" not in f]
    lab = next(l for l in labs if l["variant"] == vid); p = lab["params_gt"]
    gts[vid] = {"W": p["W"], "D": p["D"], "H": p["Hb"] + p["Hr"]}
views = [(-45, 14), (5, 18), (65, 12)]
paths = []
for vid in gts:
    for k, (yaw, pitch) in enumerate(views):
        pl = json.load(open(json.dumps(0) and "/dev/stdin")) if False else None
    # 模板 payload 取自该变体的既有标签
    tmpl = next(l for l in labs if l["variant"] == vid)["render_payload"]
    r = V[vid]["radius_mm"]; fe = 50.0; tan_half = 18.0 / fe
    d_mm = r / (0.62 * tan_half) / 1.35
    for k, (yaw, pitch) in enumerate(views):
        pl = json.loads(json.dumps(tmpl))
        pl["out_png"] = f"{OUT}/v{vid}_{k}.png"; pl["res"] = 518; pl["samples"] = 64
        pl["camera"] = {**pl["camera"], "equiv_focal_mm": fe, "pitch_deg": pitch, "yaw_deg": yaw, "roll_deg": 0.0, "aperture_fstop": 8.0, "distance_m": round(d_mm / 1000, 4)}
        pl["lighting"] = {**pl["lighting"], "exposure_ev": 0.0, "kelvin": 5200, "key_intensity_x": 1.4, "ambient_ratio": 0.55}
        pl["scene"] = "STUDIO"
        pj = f"{OUT}/v{vid}_{k}.json"; json.dump(pl, open(pj, "w"))
        t0 = time.time()
        subprocess.run(["/Applications/Blender.app/Contents/MacOS/Blender", "--background", "--python", f"{ROOT}/blender/tde_driver.py", "--", pj], capture_output=True, timeout=240)
        assert os.path.exists(pl["out_png"]), f"render missing {pl['out_png']}"
        paths.append(pl["out_png"]); print("rendered", pl["out_png"], "%.0fs" % (time.time() - t0), flush=True)
sys.path.insert(0, "/tmp/pd_recheck/vggt_repo")
import torch
from vggt.models.vggt import VGGT
from vggt.utils.load_fn import load_and_preprocess_images
dev = "mps" if torch.backends.mps.is_available() else "cpu"
model = VGGT.from_pretrained("facebook/VGGT-1B").to(dev).eval()
def estimate(ps):
    imgs = load_and_preprocess_images(ps)
    with torch.no_grad():
        pred = model(imgs[None].to(dev))
    wp = pred["world_points"][0].float().cpu().numpy(); cf = pred["world_points_conf"][0].float().cpu().numpy()
    pts = []
    from PIL import Image
    for k, p in enumerate(ps):
        a = np.asarray(Image.open(p).convert("RGB").resize((518, 518), Image.BICUBIC)).astype(np.float32)
        bg = (a.max(2) - a.min(2)) < 9   # 中性灰 = 地面/背景/阴影; 盒身偏蓝、坡面偏橙 (色度>9)
        m = (~bg) & (cf[k] > np.percentile(cf[k], 30))
        pts.append(wp[k][m])
    P = np.concatenate(pts); c = P.mean(0); Q = P - c
    _, _, vt = np.linalg.svd(Q[::max(1, len(Q)//20000)], full_matrices=False)
    proj = Q @ vt.T; lo, hi = np.percentile(proj, 0.5, 0), np.percentile(proj, 99.5, 0)
    return np.sort(hi - lo)[::-1], float(bg.mean())
res = []
for i, vid in enumerate(gts):
    g = gts[vid]; gt = np.sort([g["W"], g["D"], g["H"]])[::-1]
    for nv in (1, 2, 3):
        ext, bgf = estimate(paths[3*i:3*i+nv])
        r_est, r_gt = ext[1:] / ext[0], gt[1:] / gt[0]
        err = float(np.abs(r_est - r_gt).mean())
        res.append({"variant": vid, "n_views": nv, "ext": [round(float(x), 3) for x in ext], "gt_mm": [round(float(x), 1) for x in gt], "ratio_est": [round(float(x), 3) for x in r_est], "ratio_gt": [round(float(x), 3) for x in r_gt], "ratio_abs_err": round(err, 4)})
        print(json.dumps(res[-1]), flush=True)
json.dump(res, open(f"{OUT}/result.json", "w"), indent=1)
for nv in (1, 2, 3):
    e = [r["ratio_abs_err"] for r in res if r["n_views"] == nv]
    print("n_views=%d: 边比平均绝对相对误差 mean=%.4f  (%s)" % (nv, np.mean(e), np.round(e, 4).tolist()), flush=True)
