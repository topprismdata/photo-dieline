"""pd-guard: PD-Guardrails R1 硬门禁最小集 (L0, 违规退出码非0).

子命令:
  units    --payload render_payload.json        单位/物理范围 (A1, 历史事故: d_fill×1000)
  artifact --image render.png [--min-fill 0.03] 产物主体有效性 (B3, 历史事故: 有图无盒)
  numeric  --input predictions.npz             NaN/Inf/退化扫描 (K)
  family   --spec spec.json --rule "H=Hf+D"    家族不变量 (E3, 历史事故: 锁定约束破坏)

所有检查输出机器可读 JSON 到 stdout, PASS=0 / FAIL=1 (UNKNOWN 不当 PASS).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def cmd_units(args):
    payload = json.loads(Path(args.payload).read_text())
    cam = payload["camera"]
    checks = []
    d = cam["distance_m"]
    checks.append(("camera_distance_m", d, 0.01 <= d <= 10.0,
                   "历史事故 d_fill×1000 → 85m"))
    f = cam["equiv_focal_mm"]
    checks.append(("equiv_focal_mm", f, 10.0 <= f <= 200.0, ""))
    pit = abs(cam["pitch_deg"])
    checks.append(("pitch_deg_abs", pit, pit <= 89.0, ""))
    p = payload.get("params_gt") or {}
    hbs = [v for k, v in p.items() if k in ("Hb", "H", "h") and v]
    if hbs:
        checks.append(("carton_height_mm", max(hbs), 10.0 <= max(hbs) <= 1000.0, ""))
    fr = payload.get("fill_ratio")
    if fr is not None:
        checks.append(("fill_ratio", fr, 0.0 < fr <= 1.0, ""))
    report = {"check": "units", "payload": args.payload,
              "items": [{"name": n, "value": round(v, 4), "pass": ok, "note": note}
                        for n, v, ok, note in checks],
              "pass": all(c[2] for c in checks)}
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0 if report["pass"] else 1


def cmd_artifact(args):
    import numpy as np
    from PIL import Image
    im = np.asarray(Image.open(args.image).convert("RGB"), float)
    h, w = im.shape[:2]
    # 背景模型: 行局部背景 (每行左右边缘 20px 中位数) — 平滑渐变场景归零 (B1: 分割非单一 std)
    edge = np.concatenate([im[:, :20], im[:, -20:]], axis=1)  # h×40×3
    bg_rows = np.median(edge, axis=1)  # h×3
    dist = np.abs(im - bg_rows[:, None, :]).sum(-1)
    thr = 45.0
    mask = dist > thr
    area_frac = float(mask.mean())
    ys, xs = np.where(mask)
    if len(xs):
        bbox_frac = (xs.max() - xs.min()) / w * (ys.max() - ys.min()) / h
        cx_ok = 0.05 < (xs.min() + xs.max()) / (2 * w) < 0.95
    else:
        bbox_frac, cx_ok = 0.0, False
    # 可分离度: 前景像素与背景色的平均距离
    sep = float(dist[mask].mean()) if mask.any() else 0.0
    ok = area_frac >= args.min_fill and bbox_frac >= 0.02 and sep > 50.0 and cx_ok
    report = {"check": "artifact", "image": args.image,
              "subject_area_frac": round(area_frac, 4),
              "subject_bbox_frac": round(bbox_frac, 4),
              "separation": round(sep, 1), "centered_ok": bool(cx_ok),
              "pass": bool(ok),
              "note": "单一像素统计不构成主体判据 (B1): 本检查=角背景模型分割+面积+bbox+可分离度"}
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0 if ok else 1


def cmd_numeric(args):
    import numpy as np
    path = Path(args.input)
    bad = []
    if path.suffix == ".npz":
        data = np.load(path, allow_pickle=False)
        for k in data.files:
            arr = data[k]
            if arr.dtype.kind in "fc":
                n_nan = int(np.isnan(arr).sum()) if arr.dtype.kind == "f" else 0
                n_inf = int(np.isinf(arr).sum())
                if n_nan or n_inf:
                    bad.append({"key": k, "nan": n_nan, "inf": n_inf})
    else:
        obj = json.loads(path.read_text())
        def walk(o, path_):
            if isinstance(o, float):
                if math.isnan(o) or math.isinf(o):
                    bad.append({"key": path_, "nan": math.isnan(o), "inf": math.isinf(o)})
            elif isinstance(o, dict):
                for k, v in o.items():
                    walk(v, f"{path_}.{k}")
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    walk(v, f"{path_}[{i}]")
        walk(obj, path.name)
    print(json.dumps({"check": "numeric", "input": args.input,
                      "violations": bad, "pass": not bad}, indent=1))
    return 0 if not bad else 1


def cmd_family(args):
    spec = json.loads(Path(args.spec).read_text())
    g = spec.get("params", spec)
    violations = []
    for rule in args.rule:
        lhs, rhs = rule.split("=")
        lv = g.get(lhs.strip())
        rv = sum(g.get(t.strip(), 0) for t in rhs.split("+"))
        if lv is None:
            violations.append({"rule": rule, "reason": f"missing key {lhs.strip()}"})
        elif abs(lv - rv) > 1e-6:
            violations.append({"rule": rule, "lhs": lv, "rhs": rv,
                               "reason": "不变量破坏 (E3)"})
    print(json.dumps({"check": "family", "spec": args.spec, "rules": args.rule,
                      "violations": violations, "pass": not violations}, indent=1))
    return 0 if not violations else 1


def main():
    ap = argparse.ArgumentParser(prog="pd-guard")
    sub = ap.add_subparsers(dest="cmd", required=True)
    u = sub.add_parser("units")
    u.add_argument("--payload", required=True)
    u.set_defaults(fn=cmd_units)
    a = sub.add_parser("artifact")
    a.add_argument("--image", required=True)
    a.add_argument("--min-fill", type=float, default=0.03)
    a.set_defaults(fn=cmd_artifact)
    n = sub.add_parser("numeric")
    n.add_argument("--input", required=True)
    n.set_defaults(fn=cmd_numeric)
    fam = sub.add_parser("family")
    fam.add_argument("--spec", required=True)
    fam.add_argument("--rule", action="append", required=True)
    fam.set_defaults(fn=cmd_family)
    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
