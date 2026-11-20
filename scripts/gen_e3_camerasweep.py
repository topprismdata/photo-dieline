"""E3-A: 固定几何 × 相机参数扫描 — 测量"同几何跨视角预测方差"(相机敏感性).

6 个 gable 变体 × 27 相机格点 (焦距3 × 俯仰3 × 偏航3, 距离按填充率自适应)
输出: output/e3_camsweep/{<variant>/images,labels} + e3_manifest.json
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
from photo_dieline.folding.engine import fold_all  # noqa: F401 (引擎注册副作用)
from photo_dieline.render.mesh import export_obj
from photo_dieline.tde.engine import BLENDER, DRIVER, _center_radius

ROOT = Path("/Users/guohongbin/photo-dieline")
OUT = ROOT / "output" / "e3_camsweep"
MVE = ROOT / "output" / "tde_mve"
RES, SAMPLES = 384, 32
FOCALS = [28.0, 50.0, 85.0]
PITCHES = [5.0, 20.0, 35.0]
YAWS = [-30.0, 0.0, 30.0]


def render(payload_path: Path) -> None:
    pr = subprocess.run([BLENDER, "--background", "--python", str(DRIVER), "--",
                         str(payload_path)], capture_output=True, timeout=240)
    rp = json.loads(payload_path.read_text())["render_payload"]
    if not Path(rp["out_png"]).exists():
        raise RuntimeError(f"render fail: {pr.stderr.decode()[-400:]}")


def main() -> None:
    # 固定几何: 从 MVE 取 6 个变体的冻结参数 (与训练分布同源)
    labs = [json.loads(p.read_text()) for p in sorted(MVE.glob("labels/v_*.json"))] \
        if list(MVE.glob("labels/v_*.json")) else None
    # 变体参数存于 dataset_manifest.json
    man = json.loads((MVE / "dataset_manifest.json").read_text())
    variants = man["variants"][:6]
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    sid = 0
    rows = []
    rng = np.random.default_rng(11)
    for vi, vinfo in enumerate(variants):
        vdir = OUT / f"v{vi}"
        (vdir / "images").mkdir(parents=True, exist_ok=True)
        (vdir / "labels").mkdir(exist_ok=True)
        ir = from_raw({k: v for k, v in
                       templates.get("gable_top").build_ir(dict(vinfo["params"])).items()
                       if k != "_derived"})
        obj = vdir / "geo.obj"
        info = export_obj(ir, obj)
        center, radius = _center_radius(info["bbox_min"], info["bbox_max"])
        horiz = max(info["bbox_max"][0] - info["bbox_min"][0],
                    info["bbox_max"][1] - info["bbox_min"][1])
        for f in FOCALS:
            tan_h = 18.0 / f
            d_fill = horiz / (0.38 * 2.0 * tan_h * 1.35) * 1000.0  # mm
            d_fill = max(d_fill, radius * 2.2)  # 防相机入盒: 眼距1.35d须>>半径
            for pitch in PITCHES:
                for yaw in YAWS:
                    png = vdir / "images" / f"s_{sid:04d}.png"
                    payload = {"obj_path": str(obj), "out_png": str(png),
                               "center_mm": center, "bbox_min_mm": [0, 0, -0.5],
                               "camera": {"equiv_focal_mm": f, "pitch_deg": pitch,
                                           "yaw_deg": yaw, "roll_deg": 0.0,
                                           "aperture_fstop": 4.0,
                                           "distance_m": round(d_fill / 1000.0, 4)},
                               "lighting": {"kelvin": 5200, "exposure_ev": 0.0,
                                             "key_intensity_x": 1.0, "ambient_ratio": 0.35},
                               "material": {"roughness": 0.55,
                                             "base_color": [0.88, 0.86, 0.83]},
                               "panel_roles": {p["id"]: p["role"] for p in ir.panels},
                               "scene": "studio", "res": RES, "samples": SAMPLES}
                    # 自动曝光探针
                    probe = vdir / "images" / f"_probe.png"
                    pp = dict(payload)
                    pp.update({"res": 160, "samples": 12, "out_png": str(probe)})
                    plp = vdir / "labels" / "_probe.json"
                    plp.write_text(json.dumps({"render_payload": pp}))
                    render(plp)
                    from PIL import Image
                    pmean = float(np.asarray(Image.open(probe).convert("L"), float).mean())
                    ev = float(np.clip(math.log2(135.0 / max(pmean, 1.0)), -2.2, 2.2))
                    payload["lighting"]["exposure_ev"] = round(ev, 2)
                    probe.unlink()
                    plp.unlink()
                    pl = vdir / "labels" / f"s_{sid:04d}.json"
                    pl.write_text(json.dumps({"render_payload": payload}))
                    render(pl)
                    rows.append({"sid": sid, "variant": vi, "focal": f, "pitch": pitch,
                                  "yaw": yaw, "distance_m": payload["camera"]["distance_m"],
                                  "ev": payload["lighting"]["exposure_ev"]})
                    sid += 1
        print(f"v{vi} done ({sid} imgs, {round(time.time() - t0)}s)", flush=True)
    (OUT / "e3_manifest.json").write_text(json.dumps({
        "experiment": "E3-A camera sweep, fixed geometry",
        "variants": variants, "grid": {"focals": FOCALS, "pitches": PITCHES,
                                        "yaws": YAWS, "n": sid},
        "rows": rows}, indent=1))
    print(f"DONE: {sid} images in {round(time.time() - t0)}s", flush=True)


if __name__ == "__main__":
    main()
