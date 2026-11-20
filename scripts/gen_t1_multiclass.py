"""T1 多类分类数据集生成: 100 类动物园 × 5 变体 × 6 捕获 = 3000 张.

复用:
  - output/zoo100/batch_report.json 冻结参数 (审计 GREEN 的 100 类真值)
  - tde.engine 内核 (sample_batch / DRIVER / 自动曝光探针 / learnability 门)
差异 vs run_tde:
  - build_ir 显式传 cls_id (brick/fan/odd 多类模块必需)
  - 类别标签入 label (class_id 字段) + 顶层 index.json
  - 跳过拓扑门 (分类任务不需要投影门)
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from photo_dieline.parametric import base as templates
from photo_dieline.core.ir import from_raw
from photo_dieline.folding.engine import fold_all
from photo_dieline.render.mesh import export_obj
from photo_dieline.tde.engine import (
    BLENDER, DRIVER, PARAM_JITTER, _center_radius, _image_learnability_gate)
from photo_dieline.tde.sampler import sample_batch

ROOT = Path("/Users/guohongbin/photo-dieline")
OUT = ROOT / "output" / "zoo_t1"
REPORT = ROOT / "output" / "zoo100" / "batch_report.json"
VARIANTS, CAPS, RES, SAMPLES = 5, 6, 384, 32
JITTER_KEYS = ["W", "D", "Hb", "Hr", "Ef", "hr"]


def render_one(payload_path: Path) -> None:
    pr = subprocess.run([BLENDER, "--background", "--python", str(DRIVER), "--",
                         str(payload_path)], capture_output=True, timeout=240)
    rp = json.loads(payload_path.read_text())["render_payload"]
    if not Path(rp["out_png"]).exists():
        raise RuntimeError(f"render 无产物: {pr.stderr.decode()[-500:]}")


def gen_class(cls_id: str, params: dict, sid0: int) -> int:
    cdir = OUT / cls_id
    (cdir / "variants").mkdir(parents=True, exist_ok=True)
    (cdir / "images").mkdir(exist_ok=True)
    (cdir / "labels").mkdir(exist_ok=True)
    rng = np.random.default_rng(abs(hash(cls_id)) % (2**32))
    jk = [k for k in PARAM_JITTER.get(cls_id, PARAM_JITTER["default"]) or JITTER_KEYS
          if k in params] or [k for k in JITTER_KEYS if params.get(k, 0) > 0]
    sid = sid0
    for vi in range(VARIANTS):
        vp = dict(params)
        for k in jk:
            if vp.get(k, 0) > 0:
                vp[k] = round(float(vp[k] * rng.uniform(0.85, 1.15)), 2)
        mod = templates.get(cls_id)
        try:
            raw = mod.build_ir(dict(vp), cls_id=cls_id)
        except TypeError:
            raw = mod.build_ir(dict(vp))
        except ValueError:
            # 参数抖动破坏锁定约束(如 H=Hf+D) → 回退注册表原参数
            vp = dict(params)
            try:
                raw = mod.build_ir(dict(vp), cls_id=cls_id)
            except TypeError:
                raw = mod.build_ir(dict(vp))
        ir = from_raw({k: v for k, v in raw.items() if k != "_derived"})
        obj = cdir / "variants" / f"v_{vi}.obj"
        info = export_obj(ir, obj)
        center, radius = _center_radius(info["bbox_min"], info["bbox_max"])
        caps = sample_batch(radius_mm=radius, n=CAPS, seed=1000 + sid)
        # 填充率重定位: 驱动眼距= d×1.35 (margin硬编码) → 按水平投影宽反算
        horiz = max(info["bbox_max"][0] - info["bbox_min"][0],
                    info["bbox_max"][1] - info["bbox_min"][1])
        for cap in caps:
            tan_h = 18.0 / cap["equiv_focal_mm"]
            d_fill = horiz / (0.38 * 2.0 * tan_h * 1.35)
            cap["distance_mm"] = round(float(d_fill * rng.uniform(0.85, 1.2)), 1)
        ir_panels = {p["id"]: p["role"] for p in ir.panels}
        for cap in caps:
            png = cdir / "images" / f"s_{sid:05d}.png"
            payload = {"obj_path": str(obj), "out_png": str(png),
                       "center_mm": center, "bbox_min_mm": [0, 0, -0.5],
                       "camera": {**{k: cap[k] for k in ("equiv_focal_mm", "pitch_deg",
                                                          "yaw_deg", "roll_deg",
                                                          "aperture_fstop")},
                                  "distance_m": round(cap["distance_mm"] / 1000.0, 4)},
                       "lighting": {k: cap[k] for k in ("kelvin", "exposure_ev",
                                                         "key_intensity_x", "ambient_ratio")},
                       "material": {"roughness": cap["roughness"],
                                     "base_color": cap["base_color"]},
                       "panel_roles": ir_panels, "scene": cap["scene"],
                       "res": RES, "samples": SAMPLES}
            # 自动曝光探针 (160res/12spp → EV 修正目标 mean≈135)
            probe = cdir / "images" / f"s_{sid:05d}_probe.png"
            pp = dict(payload)
            pp.update({"res": 160, "samples": 12, "out_png": str(probe),
                       "lighting": {**payload["lighting"], "exposure_ev": 0.0}})
            plp = cdir / "labels" / f"_probe.json"
            plp.write_text(json.dumps({"render_payload": pp}))
            render_one.__wrapped_probe = None
            pr = subprocess.run([BLENDER, "--background", "--python", str(DRIVER), "--",
                                 str(plp)], capture_output=True, timeout=240)
            if probe.exists():
                from PIL import Image
                pmean = float(np.asarray(Image.open(probe).convert("L"), float).mean())
                ev = float(np.clip(math.log2(135.0 / max(pmean, 1.0)), -2.2, 2.2))
                payload["lighting"]["exposure_ev"] = round(
                    max(-2.5, min(2.5, payload["lighting"]["exposure_ev"] + ev)), 2)
                probe.unlink()
            plp.unlink()
            pl = cdir / "labels" / f"s_{sid:05d}.json"
            pl.write_text(json.dumps({"render_payload": payload}))
            render_one(pl)
            iq = _image_learnability_gate(png)
            lab = json.loads(pl.read_text())
            lab.update({"sample_id": f"s_{sid:05d}", "class_id": cls_id,
                        "variant": vi, "params_gt": vp, "capture": cap,
                        "learnability_gate": iq})
            pl.write_text(json.dumps(lab, ensure_ascii=False, indent=1))
            sid += 1
    return sid


def main() -> None:
    classes = {r["class_id"]: r["params"] for r in
               json.loads(REPORT.read_text())["rows"] if r["status"] == "GREEN"}
    only = sys.argv[1].split(",") if len(sys.argv) > 1 else None
    ids = [c for c in sorted(classes) if not only or c in only]
    OUT.mkdir(parents=True, exist_ok=True)
    index_path = OUT / "index.jsonl"
    t0, sid0 = time.time(), 0
    if index_path.exists():
        done = {json.loads(l)["class_id"] for l in index_path.read_text().splitlines()}
        ids = [c for c in ids if c not in done]
        print(f"resuming: {len(done)} classes done, {len(ids)} left", flush=True)
    failed = []
    for i, cid in enumerate(ids):
        n0 = sid0
        try:
            sid0 = gen_class(cid, classes[cid], sid0)
        except Exception as e:  # 单类失败不杀批 (记录后续跑)
            failed.append((cid, repr(e)[:200]))
            print(f"[{i + 1}/{len(ids)}] {cid}: FAILED {repr(e)[:120]}", flush=True)
            continue
        with index_path.open("a") as f:
            f.write(json.dumps({"class_id": cid, "n": sid0 - n0,
                                "sec": round(time.time() - t0, 1)}) + "\n")
        print(f"[{i + 1}/{len(ids)}] {cid}: {sid0 - n0} imgs "
              f"(total {sid0}, {round((time.time() - t0) / 60, 1)}min)", flush=True)
    if failed:
        (OUT / "failed.json").write_text(json.dumps(failed, indent=1))
        print(f"FAILED classes: {[f[0] for f in failed]}", flush=True)
    print(f"DONE: {sid0} images, {round(time.time() - t0, 1)}s", flush=True)


if __name__ == "__main__":
    main()
