"""TDE 生成器编排: 变体 × 捕获配置 → Blender 串行渲染 (Metal 单实例纪律) + 标签.

产出结构:
  out/tde_mve/
    variants/v_{id}.obj            折叠孪生网格 (mm, 1:1)
    images/{sample_id}.png         渲染图
    labels/{sample_id}.json        捕获配置+真值参数+相机 (标签单一来源=采样器)
    dataset_manifest.json          数据治理 (spec §3)
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

from ..parametric import base as templates
from ..core.ir import from_raw
from ..folding.engine import fold_all
from ..render.mesh import export_obj
from .sampler import sample_batch

BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
DRIVER = Path(__file__).resolve().parents[3] / "blender" / "tde_driver.py"


def _center_radius(bbox_min, bbox_max):
    import numpy as np
    lo, hi = np.array(bbox_min), np.array(bbox_max)
    c = (lo + hi) / 2
    r = float(np.linalg.norm(hi - lo)) / 2
    return c.round(3).tolist(), round(r, 3)


def run_tde(out_dir: str, template_id: str = "gable_top",
            variants: int = 30, captures_per: int = 10, seed: int = 7,
            res: int = 384, samples: int = 48, blender: str = BLENDER) -> dict:
    out = Path(out_dir)
    (out / "variants").mkdir(parents=True, exist_ok=True)
    (out / "images").mkdir(exist_ok=True)
    (out / "labels").mkdir(exist_ok=True)
    mod = templates.get(template_id)
    manifest = {"dataset_version": "mve-0.1", "generator_version": "tde-0.1",
                "template_version": "0.1", "template_id": template_id,
                "variants": [], "samples": [], "license_manifest": {
                    "synthetic": "generated (parametric templates, MIT repo)",
                    "no_real_images": True}}

    # 变体: 参数扰动需保持结构 (拓扑同型, 尺寸/比例独立变体; Ds 距离后续按 spec §2 计算)
    base_params = dict(mod.DEFAULTS)
    rng = __import__("numpy").random.default_rng(seed)
    vid_list = []
    for vi in range(variants):
        vp = dict(base_params)
        for k in PARAM_JITTER.get(template_id, PARAM_JITTER["default"]):
            vp[k] = round(float(base_params[k] * rng.uniform(0.8, 1.3)), 2)
        ir_raw = mod.build_ir(vp)
        ir_raw.pop("_derived", None)
        ir = from_raw(ir_raw)
        obj_path = out / "variants" / f"v_{vi}.obj"
        info = export_obj(ir, obj_path)
        center, radius = _center_radius(info["bbox_min"], info["bbox_max"])
        vid_list.append({"vid": vi, "params": vp, "obj": str(obj_path),
                         "center_mm": center, "radius_mm": radius,
                         "sha256": hashlib.sha256(obj_path.read_bytes()).hexdigest()[:16]})
        manifest["variants"].append(vid_list[-1])

    # 捕获渲染 (串行; Metal 单实例)
    sid = 0
    t0 = time.time()
    for vi, vinfo in enumerate(vid_list):
        caps = sample_batch(radius_mm=vinfo["radius_mm"], n=captures_per, seed=seed * 100 + vi)
        for ci, cap in enumerate(caps):
            payload = {"obj_path": str(vinfo["obj"]), "out_png": str(out / "images" / f"s_{sid:05d}.png"),
                       "center_mm": vinfo["center_mm"], "bbox_min_mm": None,  # driver 只用 z (米制×0.001 后)
                       "camera": {**{k: cap[k] for k in ("equiv_focal_mm", "pitch_deg", "yaw_deg",
                                                          "roll_deg", "aperture_fstop")},
                                  "distance_m": round(cap["distance_mm"] / 1000.0, 4)},
                       "lighting": {k: cap[k] for k in ("kelvin", "exposure_ev", "key_intensity_x", "ambient_ratio")},
                       "material": {"roughness": cap["roughness"], "base_color": cap["base_color"]},
                       "panel_roles": {p["id"]: p["role"] for p in ir.panels},
                       "scene": cap["scene"], "res": res, "samples": samples}
            payload["bbox_min_mm"] = [0, 0, -0.5]
            pl = out / "labels" / f"s_{sid:05d}.json"
            payload["out_png"] = str(out / "images" / f"s_{sid:05d}.png")
            gate = _topology_gate(ir, cap, vinfo, res)
            png = out / "images" / f"s_{sid:05d}.png"
            pl.write_text(json.dumps({"sample_id": f"s_{sid:05d}", "variant": vi,
                                      "capture": cap, "params_gt": vinfo["params"],
                                      "topology_gate": gate,
                                      "render_payload": payload}, ensure_ascii=False, indent=1))
            pr = subprocess.run([blender, "--background", "--python", str(DRIVER), "--",
                                 str(pl)], capture_output=True, timeout=240)
            if not png.exists():  # blender 脚本异常也可能 exit 0 → 以产物为准
                raise RuntimeError(f"render {sid} 无产物: {pr.stderr.decode()[-600:]}")
            manifest["samples"].append({"sample_id": f"s_{sid:05d}", "variant": vi,
                                        "tier": cap["tier"], "scene": cap["scene"],
                                        "g0": bool(gate["pass"]), "label": str(pl)})
            sid += 1

    manifest["sample_count"] = sid
    manifest["structure_count"] = variants
    manifest["randomization_profile"] = "70/25/5 + 4 CaptureProfile + STUDIO<=15%"
    (out / "dataset_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    return {"samples": sid, "variants": variants, "elapsed_s": round(time.time() - t0, 1),
            "out": str(out)}


def _topology_gate(ir, cap, vinfo, res: int) -> dict:
    """拓扑保真门禁 (GPT v0.3 处方): 屋脊投影在帧内、高于肩线、跨度达标.

    纯几何投影判据 (不依赖渲染像素): 相机模型与 blender/tde_driver.py 同构
    (eye=ctr+fwd·d·1.15, 等效焦距 36mm sensor, roll 绕视线轴)。
    """
    import math
    import numpy as np
    world = fold_all(ir)
    ridges, shoulders = [], []
    for pid, verts in world.items():
        if not pid.startswith("slope"):
            continue
        v = np.asarray(verts, float)
        rs = v[np.argsort(v[:, 2])[-2:]]  # 坡顶缘两点 = 脊线端点
        ridges.append((pid, rs))
        sh = v[np.argsort(v[:, 2])[:2]]
        shoulders.append((pid, sh))
    ctr = np.array(vinfo["center_mm"]) * 0.001
    radius = vinfo["radius_mm"] / 1000.0
    az, el = math.radians(cap["yaw_deg"]), math.radians(cap["pitch_deg"])
    d = cap["distance_mm"] / 1000.0 * 1.15
    eye = ctr + np.array([d * math.sin(az) * math.cos(el), -d * math.cos(az) * math.cos(el),
                          d * math.sin(el)])
    fwd = ctr - eye
    fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, np.array([0.0, 0.0, 1.0]))
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    f = 1.0 / math.tan(math.radians(18.0) / math.radians(1) if False else math.atan(18.0 / cap["equiv_focal_mm"]))
    roll = math.radians(cap["roll_deg"])

    def proj(pts):
        rel = pts - eye
        z = rel @ fwd
        x = (rel @ right) / z * f
        y = (rel @ up) / z * f
        px, py = 160 + x * 160, 160 - y * 160
        c, sn = math.cos(roll), math.sin(roll)
        dx, dy = px - 192, py - 192
        return np.array([192 + dx * c - dy * sn, 192 + dx * sn + dy * c])

    ridge_pts = np.vstack([r for _, r in ridges]) * 0.001
    sh_pts = np.vstack([s for _, s in shoulders]) * 0.001
    rp = proj(ridge_pts)
    sp = proj(sh_pts)
    in_frame = bool(np.all(rp[:, 0] > 8) and np.all(rp[:, 0] < res - 8)
                    and np.all(rp[:, 1] > 8) and np.all(rp[:, 1] < res - 8))
    above = bool(rp[:, 1].mean() < sp[:, 1].mean() - 6)
    span = float(rp[:, 0].max() - rp[:, 0].min())
    span_ok = bool(span > res * 0.15)
    box_all = np.vstack([ridge_pts, sh_pts])
    bp = proj(box_all)
    fully_in = bool(np.all(bp[:, 0] > 4) and np.all(bp[:, 0] < res - 4)
                    and np.all(bp[:, 1] > 4) and np.all(bp[:, 1] < res - 4))
    return {"ridge_in_frame": in_frame, "ridge_above_shoulder": above,
            "ridge_span_px": round(span, 1), "span_ok": span_ok,
            "box_fully_in_frame": fully_in,
            "pass": bool(in_frame and above and span_ok)}


PARAM_JITTER = {
    "gable_top": ["W", "D", "Hb", "Hr", "Ef"],
    "default": [],
}
