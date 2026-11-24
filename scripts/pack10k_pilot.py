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


GATE_IDS = ("G02", "G03", "G04", "G05", "G06", "G07", "G08", "G09", "G10")
# 几何调节率先验 (如实: 这不是可辨识性证明 — 自观测=inverse crime 被禁;
# 真交付标签须测量层在真实观测上判, 数据集只发布几何先验供消费方求解器自证)
DEGENERATE_MAX_RATIO = 6.0   # max/min 尺寸比 ≥6 → LOW (近退化扁平/细长)
DEGENERATE_MIN_RATIO = 0.12


def degeneracy_prior(dims_mm):
    vals = [max(dims_mm[k], 1e-6) for k in ("W", "D", "H")]
    ratio = max(vals) / min(vals)
    prior = "LOW" if (ratio >= DEGENERATE_MAX_RATIO or min(vals) / max(vals) <= DEGENERATE_MIN_RATIO) else "NORMAL"
    return {"dim_ratio": round(ratio, 2), "identifiability_prior": prior}


# 拒收集退化算子: 按家族显式 z 向键集合 (同比缩 0.12 — 比例约束如 Hb>Hf, Hl<H 天然保持;
# 只缩 H 不缩耦合键会被 validate_params 正确拒绝 — 首版实证 12 例)
DEGENERATE_KEYS = {
    "gable": ("Hb", "Hr"),
    "clv": ("H", "tuck_d", "gs_d", "ts_d", "pk_d", "slot_d", "hs", "bd"),
    "cone": ("h",),
    "food": ("H", "Hf", "Hb", "Hl", "lip_d", "glue_w"),
}


def build_one(fam, cls_id, idx, out_dir, degenerate=False):
    params, deriv = sample_variant(cls_id, idx)
    if degenerate:  # R03 类拒收样本: 近扁平化 (z 向键同比 ×0.12), 几何仍合法可折叠
        keys = [k for k in DEGENERATE_KEYS.get(fam, ()) if params.get(k, 0) > 0]
        if not keys:
            return {"status": "QA_FAIL", "gates": {}, "fail": "无 z 向键可退化"}, params, deriv
        for k in keys:
            params[k] = round(params[k] * 0.12, 3)
        deriv["degenerate"] = f"{','.join(keys)}×0.12"
        deriv["identifiability_prior"] = "LOW"
    mod = class_module(cls_id)
    try:
        ir_raw = mod.build_ir(params)
    except ValueError as e:
        return {"status": "CONTRACT_REJECTED", "gates": {}, "fail": f"合同拒绝: {e}"}, params, deriv
    ir_raw.pop("_derived", None)
    ir = from_raw(ir_raw)

    import time as _t
    t0 = _t.perf_counter()
    x0, y0, x1, y1 = net_bbox(ir)
    svg = svg_render(ir, x1 - x0, y1 - y0)
    pdf = build_pdf(ir, x1 - x0, y1 - y0)
    report = run_qa(ir, svg, pdf)
    t_qa = _t.perf_counter() - t0
    gates = {g["id"]: g["status"] for g in report["gates"] if g["id"] != "G01"}
    gate_fail = [k for k, v in gates.items() if v != "PASS"]
    if gate_fail:
        return {"status": "QA_FAIL", "gates": gates, "fail": f"gate {gate_fail} FAIL"}, params, deriv

    t1 = _t.perf_counter()
    world = fold_all(ir)
    roles = {pp["id"]: pp["role"] for pp in ir.panels}
    solid = np.vstack([v for pid, v in world.items() if roles[pid] in mod.solid_roles()])
    folded = {k: float(solid[:, i].max() - solid[:, i].min()) for i, k in enumerate("WDH")}
    analytic = mod.analytic_bbox(params)
    t_fold = _t.perf_counter() - t1

    asset_id = f"{fam}_{cls_id}_v{idx:04d}" + ("_dg" if degenerate else "")
    a_dir = Path(out_dir) / asset_id
    t2 = _t.perf_counter()
    ev = export_usdc(ir, a_dir / "model.usdc", kind="carton_board", family=fam)
    sdims = stage_dims_m(a_dir / "model.usdc")
    rec = reconcile_dims(analytic, folded, sdims)
    t_exp = _t.perf_counter() - t2
    t3 = _t.perf_counter()
    val = validate_usdc(a_dir / "model.usdc")
    t_val = _t.perf_counter() - t3

    ev["stage_dims_m"] = sdims
    ev["date"] = datetime.date.today().isoformat()
    write_sidecars(a_dir, asset_id, cls_id, ev, rec, val["checks"])
    (a_dir / "build.json").write_text(json.dumps({
        "asset_id": asset_id, "family": fam, "class_id": cls_id,
        "params": params, "derivation": deriv, "gates": gates,
        "folded_mm": {k: round(v, 3) for k, v in folded.items()},
        "board_kind": ev["kind"]}, ensure_ascii=False, indent=2))
    return {"status": "GREEN" if (rec["ok"] and val["ok"]) else "EVID_FAIL",
            "gates": gates, "reconcile": rec, "validator": val,
            "stage_ms": {"qa": round(t_qa * 1000, 1), "fold": round(t_fold * 1000, 1),
                         "export": round(t_exp * 1000, 1), "validate": round(t_val * 1000, 1)},
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
    refusal_per_family = max(1, args.per_family // 12)  # ~8% 拒收先验样本
    for fam, classes in FAMILIES.items():
        n_normal = args.per_family - refusal_per_family
        plan = [(i, False) for i in range(n_normal)] + [(args.per_family + j, True) for j in range(refusal_per_family)]
        for i, degenerate in plan:
            cls_id = classes[i % len(classes)]
            asset_id = f"{fam}_{cls_id}_v{i:04d}" + ("_dg" if degenerate else "")
            row = {"asset_id": asset_id, "family": fam, "class_id": cls_id, "variant": i,
                   "sample_set": "REFUSAL_PRIOR" if degenerate else "MAIN"}
            try:
                res, params, deriv = build_one(fam, cls_id, i, out, degenerate=degenerate)
                row.update({"status": res["status"], "params": params, "derivation": deriv,
                            "stage_ms": res.get("stage_ms"),
                            "fail": res.get("fail") or res.get("validator", {}).get("reason"),
                            "gates": res.get("gates", {}),
                            "reconcile_ok": (res.get("reconcile") or {}).get("ok"),
                            "reconcile_worst_mm": (res.get("reconcile") or {}).get("worst_diff_mm"),
                            "validator_ok": (res.get("validator") or {}).get("ok"),
                            "validator_checks": len((res.get("validator") or {}).get("checks", []))})
                if res.get("status") == "GREEN":
                    dims = res["analytic"]
                    row["degeneracy"] = degeneracy_prior(dims)
                    row["dims_mm"] = {"analytic": dims, "folded": res["folded"]}
                    row["reconcile"] = res["reconcile"]["axes"]
                    # P-GATE 拆分 (R1 P0-04: 禁止 GREEN=SimReady verified 混称; 只报实测)
                    for gk, gv in {"01_naming": "PASS",
                                   "02_structure": "PASS" if row.get("validator_ok") else "FAIL",
                                   "03_package_profile": "UNTESTED",
                                   "04_asset_profile": "UNTESTED",
                                   "05_physics": "PARTIAL",
                                   "06_runtime_load": "UNTESTED",
                                   "07_stability": "UNTESTED",
                                   "08_cross_runtime": "UNTESTED"}.items():
                        row["p_gate_" + gk.split("_")[0]] = gv
            except Exception as e:
                row.update({"status": "ERROR", "fail": f"{type(e).__name__}: {str(e)[:220]}",
                            "trace": traceback.format_exc()[-600:]})
            rows.append(row)
            print(f"[{len(rows):3d}] {row['status']:8s} {asset_id}"
                  + (f"  <- {row['fail'][:80]}" if row.get("fail") else ""), flush=True)

    # manifest (CSV) + summary
    import csv
    cols = ["asset_id", "family", "class_id", "variant", "sample_set", "status", "reconcile_ok",
            "reconcile_worst_mm", "validator_ok", "validator_checks", "identifiability_prior", "dim_ratio",
        "qa_ms", "fold_ms", "export_ms", "validate_ms",
        "p_gate_01", "p_gate_02", "p_gate_03", "p_gate_04", "p_gate_05", "p_gate_06", "p_gate_07", "p_gate_08", "fail"]
    for r in rows:
            dg = r.get("degeneracy") or {}
            r["identifiability_prior"] = dg.get("identifiability_prior", "")
            r["dim_ratio"] = dg.get("dim_ratio", "")
    with open(out / "manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
        st = {}
    for r in rows:
        st[r["status"]] = st.get(r["status"], 0) + 1
    stage_ok = [r.get("stage_ms") for r in rows if r.get("stage_ms")]
    stage_avg = {k: round(sum(x[k] for x in stage_ok) / max(len(stage_ok), 1), 1)
                 for k in ("qa", "fold", "export", "validate")} if stage_ok else {}
    summary = {"total": len(rows), "statuses": st, "stage_avg_ms": stage_avg,
               "thumbs_render_s": None,
               "reconcile_ok": sum(1 for r in rows if r.get("reconcile_ok")),
               "validator_ok": sum(1 for r in rows if r.get("validator_ok")),
               "validator_available": HAVE_UDV}
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
