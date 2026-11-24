"""独立投影对账 (在 Blender 内运行): 用驱动自己的 main() 复现场景与相机,
再用 bpy_extras.world_to_camera_view 把 B0 求解器的三维关键点投到像素坐标,
与求解器手写的 numpy 投影逐点比较。两套独立实现 (Blender vs numpy) 必须一致, 求解器才可信。
用法: blender -b -noaudio --factory-startup --python b0_verify_camera.py
"""
import json
import math
import sys
import types

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sys.path.insert(0, "/tmp/pd_recheck")
sys.modules.setdefault("jsonschema", types.SimpleNamespace(
    ValidationError=type("ValidationError", (Exception,), {}), validate=lambda *a, **k: None))
from b0_solver import gable_keypoints, to_world, project, eye_pos, RES  # noqa: E402

ROOT = "/Users/guohongbin/photo-dieline"
B0 = "/tmp/pd_recheck/b0"
_src = open(ROOT + "/blender/tde_driver.py").read().rsplit("\nmain()", 1)[0]
_ns = {"__name__": "tde_driver"}
exec(compile(_src, "tde_driver.py", "exec"), _ns)

views = json.load(open(f"{B0}/views.json"))
out = []
for v in views[::10][:12] + views[5::37][:4]:
    p, cam = v["params"], v["camera"]
    payload = {"obj_path": f"{B0}/variants/v_{v['variant']}.obj", "center_mm": v["center_mm"], "bbox_min_mm": [0, 0, -0.5],
               "camera": dict(cam), "lighting": {"kelvin": 5200, "exposure_ev": 0.0, "key_intensity_x": 1.0, "ambient_ratio": 0.5},
               "material": {"roughness": 0.5, "base_color": [0.6, 0.5, 0.4]}, "panel_roles": {}, "scene": "STUDIO",
               "res": 64, "samples": 1, "out_png": f"{B0}/images/_verify.png"}
    path = f"{B0}/_verify_payload.json"
    json.dump(payload, open(path, "w"))
    old = sys.argv
    sys.argv = ["blender", "--", path]
    try:
        _ns["main"]()
    finally:
        sys.argv = old
    sc = bpy.context.scene
    cam_obj = next(o for o in sc.objects if o.type == "CAMERA")
    d_eff = cam["distance_m"]
    d_fit = payload.get("_r_meas_m", 0.0) / (18.0 / cam["equiv_focal_mm"]) * 1.30
    if d_eff * 1.35 < d_fit:
        d_eff = d_fit / 1.35
    P, ctr = gable_keypoints(p)
    Pw = to_world(P, ctr)
    fx = cam["equiv_focal_mm"] / 36.0 * RES
    az, el, roll = math.radians(cam["yaw_deg"]), math.radians(cam["pitch_deg"]), math.radians(cam["roll_deg"])
    eye_np = eye_pos(ctr / 1000.0, az, el, d_eff * 1.35)
    uv_np = project(Pw, eye_np, az, el, roll, fx)
    uv_bl = np.array([[c.x * RES, (1.0 - c.y) * RES] for c in (world_to_camera_view(sc, cam_obj, Vector(tuple(q))) for q in Pw)])
    eye_bl = np.array(cam_obj.matrix_world.translation)
    diff = np.linalg.norm(uv_np - uv_bl, axis=1)
    out.append({"sid": v["sid"], "max_px": float(diff.max()), "mean_px": float(diff.mean()),
                "eye_diff_mm": float(np.linalg.norm(eye_bl - eye_np) * 1000.0)})
    print("B0V %s max=%.4fpx mean=%.4fpx 眼位差=%.5fmm" % (v["sid"], diff.max(), diff.mean(), out[-1]["eye_diff_mm"]), flush=True)
json.dump(out, open(f"{B0}/camera_verify.json", "w"), indent=1)
print("B0V_DONE n=%d max_over_all=%.5fpx" % (len(out), max(o["max_px"] for o in out)), flush=True)
