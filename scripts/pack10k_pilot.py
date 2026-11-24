#!/usr/bin/env python3
"""pack10k 试点: 4 GREEN 家族 × N 变体 → IR → QA 十门 → USD 导出 → 尺寸三方对账 →
他们的验证器逐件 → SimReady 侧车 → manifest。

用法: python3 scripts/pack10k_pilot.py --out output/pack10k_pilot [--per-family 25]
判据: 全链路无静默失败; manifest 记录每件真实状态 (含失败)。
"""

import argparse
import datetime
import json
import sys
import traceback
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from photo_dieline.core.ir import class_defaults, class_module, from_raw  # noqa: E402
from photo_dieline.export.pdf import build_pdf  # noqa: E402
from photo_dieline.export.svg import net_bbox, render as svg_render  # noqa: E402
from photo_dieline.export.usd import export_usdc, reconcile_dims, stage_dims_m, write_sidecars  # noqa: E402
from photo_dieline.folding.engine import fold_all  # noqa: E402
from photo_dieline.parametric import base as templates  # noqa: E402
from photo_dieline.parametric.sample import sample_variant  # noqa: E402
from photo_dieline.qa.pipeline import run_qa  # noqa: E402

FAMILIES = {
    "gable": ["gable_top", "gable_finless", "gable_fin_gap_wide", "gable_rect_base"],
    "clv": ["clv_double_cover", "clv_double_tuck", "clv_glue_seal", "clv_hinged_flap",
            "clv_partial_lid", "clv_snap_lock", "clv_tuck_insert"],
    "cone": ["cone_wrap", "cone_wrap_n12", "cone_wrap_n20"],
    "food": ["food_bento_lid_box", "food_clamshell_burger", "food_fries_sleeve", "food_wrap_pocket"],
}
GATE_IDS = ("G02", "G03", "G04", "G05", "G06", "G07", "G08", "G09", "G10")

try:  # 他们的验证器 (Apache-2.0; 本机研究副本)
    sys.path.insert(0, "/Users/guohongbin/usdcraft_study/code")
    from sdk._core._usd_validate import _validate_usd_asset
    HAVE_UDV = True
except Exception:
    HAVE_UDV = False


def validate_usdc(path):
    if not HAVE_UDV:
        return {"ok": None, "reason": "validator 不可用", "checks": []}
    try:
        checks = _validate_usd_asset(Path(path), backend="generic")
        return {"ok": True, "checks": list(checks)}
    except Exception as e:
        return {"ok": False, "reason": str(e)[:300], "checks": []}


def build_one(fam, cls_id, idx, out_dir):
    params, deriv = sample_variant(cls_id, idx)
    mod = class_module(cls_id)
    ir_raw = mod.build_ir(params)
    ir_raw.pop("_derived", None)
    ir = from_raw(ir_raw)

    x0, y0, x1, y1 = net_bbox(ir)
    svg = svg_render(ir, x1 - x0, y1 - y0)
    pdf = build_pdf(ir, x1 - x0, y1 - y0)
    report = run_qa(ir, svg, pdf)
    gates = {g["id"]: g["status"] for g in report["gates"] if g["id"] != "G01"}
    gate_fail = [k for k, v in gates.items() if v != "PASS"]
    if gate_fail:
        return {"status": "QA_FAIL", "gates": gates, "fail": f"gate {gate_fail} FAIL"}, params, deriv

    world = fold_all(ir)
    roles = {pp["id"]: pp["role"] for pp in ir.panels}
    solid = np.vstack([v for pid, v in world.items() if roles[pid] in mod.solid_roles()])
    folded = {k: float(solid[:, i].max() - solid[:, i].min()) for i, k in enumerate("WDH")}
    analytic = mod.analytic_bbox(params)

    asset_id = f"{fam}_{cls_id}_v{idx:04d}"
    a_dir = Path(out_dir) / asset_id
    ev = export_usdc(ir, a_dir / "model.usdc", kind="carton_board")
    sdims = stage_dims_m(a_dir / "model.usdc")
    rec = reconcile_dims(analytic, folded, sdims)
    val = validate_usdc(a_dir / "model.usdc")

    ev["stage_dims_m"] = sdims
    ev["date"] = datetime.date.today().isoformat()
    write_sidecars(a_dir, asset_id, cls_id, ev, rec, val["checks"])
    return {"status": "GREEN" if (rec["ok"] and val["ok"]) else "EVID_FAIL",
            "gates": gates, "reconcile": rec, "validator": val,
            "folded": {k: round(v, 3) for k, v in folded.items()},
            "analytic": {k: round(v, 3) for k, v in analytic.items()}}, params, deriv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "output" / "pack10k_pilot"))
    ap.add_argument("--per-family", type=int, default=25)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for fam, classes in FAMILIES.items():
        for i in range(args.per_family):
            cls_id = classes[i % len(classes)]
            asset_id = f"{fam}_{cls_id}_v{i:04d}"
            row = {"asset_id": asset_id, "family": fam, "class_id": cls_id, "variant": i}
            try:
                res, params, deriv = build_one(fam, cls_id, i, out)
                row.update({"status": res["status"], "params": params, "derivation": deriv,
                            "fail": res.get("fail") or res.get("validator", {}).get("reason"),
                            "gates": res.get("gates", {}),
                            "reconcile_ok": (res.get("reconcile") or {}).get("ok"),
                            "reconcile_worst_mm": (res.get("reconcile") or {}).get("worst_diff_mm"),
                            "validator_ok": (res.get("validator") or {}).get("ok"),
                            "validator_checks": len((res.get("validator") or {}).get("checks", []))})
                if res.get("status") == "GREEN":
                    row["dims_mm"] = {"analytic": res["analytic"], "folded": res["folded"]}
                    row["reconcile"] = res["reconcile"]["axes"]
            except Exception as e:
                row.update({"status": "ERROR", "fail": f"{type(e).__name__}: {str(e)[:220]}",
                            "trace": traceback.format_exc()[-600:]})
            rows.append(row)
            print(f"[{len(rows):3d}] {row['status']:8s} {asset_id}"
                  + (f"  <- {row['fail'][:80]}" if row.get("fail") else ""), flush=True)

    # manifest (CSV) + summary
    import csv
    cols = ["asset_id", "family", "class_id", "variant", "status", "reconcile_ok",
            "reconcile_worst_mm", "validator_ok", "validator_checks", "fail"]
    with open(out / "manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    st = {}
    for r in rows:
        st[r["status"]] = st.get(r["status"], 0) + 1
    summary = {"total": len(rows), "statuses": st,
               "reconcile_ok": sum(1 for r in rows if r.get("reconcile_ok")),
               "validator_ok": sum(1 for r in rows if r.get("validator_ok")),
               "validator_available": HAVE_UDV}
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
