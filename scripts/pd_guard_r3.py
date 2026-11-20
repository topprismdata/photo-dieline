"""pd-guard-r3: 全链路治理门禁 (I 摄影测量/J 制造/L 多视角/M 许可) + Release Gate.

子命令:
  pairs    --render-dir DIR        每张渲染必须有绑定相机JSON+坐标系声明 (I1/I2)
  dieline  --spec spec.json        CUT/CREASE语义全覆盖+闭合轮廓+物理尺寸+校验条 (J1/J2)
  license  --manifest manifest.json --zoo-dir DIR  逐资产许可/来源/存证 (M1)
  release  --render-dir --spec --manifest --zoo-dir --index --expect  串联全门禁
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

CAMERA_FIELDS = {"equiv_focal_mm", "pitch_deg", "yaw_deg", "distance_m"}


def cmd_pairs(args):
    rd = Path(args.render_dir)
    missing_frame, missing_json, missing_cam = [], [], []
    frames = set()
    pngs = sorted(rd.glob("*.png"))
    for p in pngs:
        j = p.with_suffix(".json")
        if not j.exists():
            missing_json.append(p.name)
            continue
        lab = json.loads(j.read_text())
        cam = lab.get("camera", lab.get("render", {}).get("camera", {}))
        if not CAMERA_FIELDS <= set(cam):
            missing_cam.append(p.name)
        frame = lab.get("frame") or lab.get("coordinate_frame")
        if frame:
            frames.add(frame)
        else:
            missing_frame.append(p.name)
    ok = not (missing_json or missing_cam or missing_frame) and len(frames) == 1
    print(json.dumps({"check": "pairs", "render_dir": str(rd), "n_images": len(pngs),
                      "missing_label": len(missing_json), "missing_camera_fields": len(missing_cam),
                      "missing_frame_decl": len(missing_frame), "frames_declared": sorted(frames),
                      "examples": (missing_json + missing_cam + missing_frame)[:3],
                      "pass": ok, "note": "内外参绑定图像版本+坐标系显式 (I1/I2)"}, indent=1))
    return 0 if ok else 1


def cmd_dieline(args):
    spec = json.loads(Path(args.spec).read_text())
    errs = []
    exemptions = []
    mats = {"CUT", "CREASE", "PERFORATE"}
    if "polygons" in spec:
        for i, poly in enumerate(spec["polygons"]):
            m = poly.get("material")
            if m not in mats:
                errs.append(f"poly[{i}] material='{m}' not in {sorted(mats)}")
            pts = poly.get("points", [])
            if len(pts) >= 2 and tuple(pts[0]) != tuple(pts[-1]):
                errs.append(f"poly[{i}] contour not closed")
    params = spec.get("params", {})
    meas = {m["name"]: m["value_mm"] for m in spec.get("measurements", [])}
    dims = {**params, **meas}
    # 锁定约束: gable 家族 H=Hb+Hr; 通用 H=Hf+D (字段齐才验, E3)
    if all(k in dims for k in ("H", "Hb", "Hr")) and abs(dims["H"] - (dims["Hb"] + dims["Hr"])) > 0.5:
        errs.append("H != Hb + Hr (gable 锁定约束)")
    if all(k in dims for k in ("H", "Hf", "D")) and abs(dims["H"] - (dims["Hf"] + dims["D"])) > 0.5:
        errs.append("H != Hf + D (锁定约束)")
    if not any(k in dims for k in ("H", "Hb")):
        errs.append("missing physical dims (H/Hb)")
    strip = spec.get("calibration_strip_mm", params.get("calibration_strip_mm"))
    if strip != 50:
        if args.allow_missing_strip:
            exemptions.append("calibration_strip_mm: 渲染器未实现校验条, 豁免待补 (审计留痕)")
        else:
            errs.append(f"calibration_strip_mm={strip} (需 50mm 物理校验条)")
    print(json.dumps({"check": "dieline", "spec": args.spec,
                      "n_polygons": len(spec.get("polygons", [])),
                      "errors": errs[:5], "exemptions": exemptions,
                      "pass": not errs, "note": "网格合法≠结构合法 (J1/J2)"}, indent=1))
    return 0 if not errs else 1


def cmd_license(args):
    man = json.loads(Path(args.manifest).read_text())
    rows = man["assets"] if isinstance(man, dict) and "assets" in man else man
    errs = []
    zd = Path(args.zoo_dir)
    for r in rows:
        k = r.get("key", "?")
        if not r.get("license") or r.get("license") in ("", "unknown"):
            errs.append(f"{k}: license missing")
        if not r.get("source_url"):
            errs.append(f"{k}: source_url missing")
        if not (zd / f"lic_{k}.txt").exists():
            errs.append(f"{k}: notice file lic_{k}.txt missing")
    print(json.dumps({"check": "license", "manifest": args.manifest, "n_assets": len(rows),
                      "errors": errs[:5], "pass": not errs, "note": "来源/许可/审查状态逐资产登记 (M1)"}, indent=1))
    return 0 if not errs else 1


def cmd_release(args):
    steps = [("pairs", ["--render-dir", args.render_dir]),
             ("dieline", ["--spec", args.spec]),
             ("license", ["--manifest", args.manifest, "--zoo-dir", args.zoo_dir]),
             ("numeric", ["--input", args.numeric_input])]
    failures = []
    for name, extra in steps:
        if not all(extra[1::2]):
            continue
        r = subprocess.run([sys.executable, str(Path(__file__).resolve().parent /
                          ("pd_guard_r3.py" if name in ("pairs", "dieline", "license") else "pd_guard.py")),
                          name] + extra, capture_output=True, text=True)
        if r.returncode != 0:
            failures.append(name)
    print(json.dumps({"check": "release_gate", "failures": failures,
                      "pass": not failures, "note": "CI Release Gate: 任一失败即阻断发布"}, indent=1))
    return 0 if not failures else 1


ap = argparse.ArgumentParser(prog="pd-guard-r3")
sp = ap.add_subparsers(dest="cmd", required=True)
p = sp.add_parser("pairs"); p.add_argument("--render-dir", required=True); p.set_defaults(fn=cmd_pairs)
d = sp.add_parser("dieline"); d.add_argument("--spec", required=True); d.add_argument("--allow-missing-strip", action="store_true"); d.set_defaults(fn=cmd_dieline)
m = sp.add_parser("license"); m.add_argument("--manifest", required=True); m.add_argument("--zoo-dir", required=True); m.set_defaults(fn=cmd_license)
r = sp.add_parser("release")
for flag in ("--render-dir", "--spec", "--manifest", "--zoo-dir", "--numeric-input"):
    r.add_argument(flag)
r.set_defaults(fn=cmd_release)
args = ap.parse_args()
sys.exit(args.fn(args))
