"""E2b 冻结实物测试 harness (数据到达即评估; 现在用 E3 合成图干跑验证).

用法:
  python3 scripts/eval_frozen10.py --data data/frozen10          # 真实数据
  python3 --dry-run --render-dir output/e3_camsweep/v0/images    # 干跑(harness 自检)

输入契约 (docs/CAPTURE_PROTOCOL.md):
  data/frozen10/{photos,specs,manifest.json}
  photos/<id>_cam<k>.jpg + 同名 .json (camera 4元组 + frame 声明)
  specs/<id>_measurements.json
输出:
  data/frozen10/sim2real_report.json  (pd-guard pairs 预检 + 逐件 raw 比例 MAE + 缺口汇总)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

REL = ["W/Hb", "D/Hb", "Hr/Hb", "Ef/Hb"]
STATS = {"mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]}
REQUIRED_CAM = {"equiv_focal_mm", "pitch_deg", "yaw_deg", "distance_m"}


def load_model(ckpt: Path, device: str):
    from torchvision.models import resnet18
    ck = torch.load(ckpt, map_location=device, weights_only=False)
    net = resnet18(weights=None)
    net.fc = torch.nn.Linear(net.fc.in_features, 12)
    net.load_state_dict(ck["model"])
    net = net.to(device).eval()
    return net


def predict_ratios(net, image: Path, device: str, head_ratios: int = 4) -> np.ndarray:
    """单张照片 → 4 个比例预测 (中心裁剪+resize 384, 与训练口径一致)."""
    im = Image.open(image).convert("RGB")
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2)).resize((384, 384), Image.BILINEAR)
    x = torch.from_numpy(np.asarray(im).transpose(2, 0, 1).copy()).float() / 255.0
    x = (x - torch.tensor(STATS["mean"])[:, None, None]) / torch.tensor(STATS["std"])[:, None, None]
    with torch.no_grad():
        p = net(x[None].to(device)).view(-1, 3, head_ratios)[:, 1, :].cpu().numpy()[0]
    return p


def true_ratios(meas: dict) -> dict:
    d = {m["name"]: float(m["value_mm"]) for m in meas["measurements"]}
    if "H" in d and "Hb" not in d:
        d["Hb"] = d["H"]  # 盒型键别名 (RSC=H, web specs=Hb)
    out = {}
    for r in REL:
        num, den = r.split("/")
        if num in d and den in d and d[den] != 0:
            out[r] = d[num] / d[den]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/frozen10")
    ap.add_argument("--ckpt", default="runs/e1_seed42/best.pt")
    ap.add_argument("--dry-run", action="store_true", help="用 E3 合成图验证 harness 本身")
    ap.add_argument("--render-dir", default="output/e3_camsweep/v0/images")
    ap.add_argument("--expect", type=int, default=10)
    ap.add_argument("--web", action="store_true", help="web采购模式: 单图/品, 相机契约豁免留痕")
    args = ap.parse_args()
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    report = {"mode": "dry-run" if args.dry_run else "real", "per_item": [], "notes": []}

    if args.dry_run:
        # 干跑: E3 合成图有相机 JSON+frame, GT 用合成真值(v0 specs); 验证 harness 管道而非精度
        rd = Path(args.render_dir)
        pairs_gate = subprocess.run([sys.executable, str(ROOT / "scripts/pd_guard_r3.py"),
                                     "pairs", "--render-dir", str(rd)], capture_output=True, text=True)
        pairs = json.loads(pairs_gate.stdout)
        report["pairs_gate"] = {"pass": pairs["pass"], "n_images": pairs["n_images"],
                                "frames": pairs.get("frames_declared", [])}
        net = load_model(ROOT / args.ckpt, dev)
        errs = [[] for _ in REL]
        n_used = 0
        man = json.loads((rd.parent.parent / "e3_manifest.json").read_text())
        vid = int(rd.parent.name.lstrip("v"))
        params = man["variants"][vid]["params"]
        gt = {r: params[r.split("/")[0]] / params["Hb"] for r in REL}
        for p in sorted(rd.glob("s_*.png"))[:20]:
            if not (rd.parent / "labels" / (p.stem + ".json")).exists():
                continue
            pred = predict_ratios(net, p, dev)
            for i, r in enumerate(REL):
                errs[i].append(abs(float(pred[i]) - gt[r]))
            n_used += 1
        if n_used == 0:
            print("DRY-RUN FAILED: 0 images usable — harness 管道断裂, 不得报告 ok")
            return 1
        report["dry_run"] = {"n_predicted": n_used,
                             "harness_ok": True,
                             "dry_raw_MAE": {r: round(float(np.mean(e)), 4) for r, e in zip(REL, errs)},
                             "note": "管道自检: E3 合成图+variant 真值全链执行; 数值仅验管道非精度结论"}
    else:
        data = Path(args.data)
        photos = data / "photos"
        web_mode = not list(photos.glob("*_cam*.json")) and args.web
        # 预检: pd-guard pairs — 真实采集要求相机契约; web模式 I1/I2 豁免留痕
        pairs_gate = subprocess.run([sys.executable, str(ROOT / "scripts/pd_guard_r3.py"),
                                     "pairs", "--render-dir", str(photos)], capture_output=True, text=True)
        try:
            pairs = json.loads(pairs_gate.stdout)
        except json.JSONDecodeError:
            pairs = {"pass": False, "n_images": 0}
        report["pairs_gate"] = {k: pairs.get(k) for k in ("pass", "n_images",
                                 "missing_label", "missing_camera_fields", "missing_frame_decl")}
        if web_mode:
            report["pairs_gate"]["exemption"] = ("WEB-SOURCED: 相机参数不可追溯(I1/I2豁免留痕); "
                                                 "照片=供应商按品渲染图(非实拍), 无ECXIF契约")
        man = json.loads((data / "manifest.json").read_text())
        items = man["items"] if isinstance(man, dict) else man
        report["denom"] = {"expected": args.expect, "actual": len(items),
                           "pass": len(items) == args.expect}
        net = load_model(ROOT / args.ckpt, dev)
        head_ratios = net.fc.out_features // 3  # 3 quantiles × R ratios (gable=4, box=2)
        rels = REL[:head_ratios]
        report["rel_used"] = rels
        all_errs = [[] for _ in rels]
        for it in items:
            iid = it["id"]
            meas_p = data / "specs" / f"{iid}_measurements.json"
            if not meas_p.exists():
                report["per_item"].append({"id": iid, "status": "INVALID", "reason": "no measurements"})
                continue
            gt = true_ratios(json.loads(meas_p.read_text()))
            per = {r: [] for r in REL}
            n_cam = 0
            if web_mode:
                img = photos / f"{iid}.jpg"
                if img.exists() and gt:
                    pred = predict_ratios(net, img, dev, head_ratios)
                    for i, r in enumerate(rels):
                        if r in gt:
                            per[r].append(abs(float(pred[i]) - gt[r]))
                    n_cam = 1
            else:
                for cj in sorted(photos.glob(f"{iid}_cam*.json")):
                    lab = json.loads(cj.read_text())
                    if not REQUIRED_CAM <= set(lab.get("camera", {})):
                        continue
                    img = cj.with_suffix(".jpg")
                    if not img.exists():
                        img = cj.with_suffix(".png")
                    if not img.exists():
                        continue
                    pred = predict_ratios(net, img, dev)
                    for i, r in enumerate(REL):
                        if r in gt:
                            per[r].append(abs(float(pred[i]) - gt[r]))
                    n_cam += 1
            raws = {r: (float(np.mean(v)) if v else None) for r, v in per.items()}
            avail = [r for r in rels if raws[r] is not None]
            need = 1 if web_mode else 6
            ok = n_cam >= need and len(avail) >= 2   # web盒型无 Hr/Ef, 比例子集即可
            report["per_item"].append({"id": iid, "status": "OK" if ok else "INVALID",
                                       "n_cam": n_cam, "raw_MAE": raws,
                                       "ratios_available": avail})
            if ok:
                for i, r in enumerate(REL):
                    if raws[r] is not None:
                        all_errs[i].append(raws[r])
        report["summary"] = {"overall_raw_MAE": {r: (round(float(np.mean(e)), 4) if e else None)
                                                 for r, e in zip(rels, all_errs)},
                             "n_valid_items": sum(1 for x in report["per_item"] if x["status"] == "OK"),
                             "baseline_synthetic": 0.0166,
                             "sim2real_gap_pp": None}
        ov = [v for v in report["summary"]["overall_raw_MAE"].values() if v is not None]
        report["summary"]["note_head"] = f"模型头 {head_ratios} 比例 (按 ckpt 自适应)"
        if ov:
            report["summary"]["sim2real_gap_pp"] = round((float(np.mean(ov)) - 0.0166) * 100, 1)

    out = Path(args.data) if not args.dry_run else ROOT / "output"
    out.mkdir(parents=True, exist_ok=True)
    (out / "sim2real_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(json.dumps(report.get("summary", report.get("dry_run", {})), indent=1, ensure_ascii=False))
    print(f"saved: {out / 'sim2real_report.json'}")


if __name__ == "__main__":
    main()
