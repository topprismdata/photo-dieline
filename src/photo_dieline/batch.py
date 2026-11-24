"""批量验证: 注册表全类 → build → QA 十门 → 折线语义/闭合灵敏度 → 成熟度分级 → 对账 JSON + contact sheet.

用法: photo-dieline batch --out output/zoo100 [--prefix prism]
成熟度 (机器可判定的前三档; L3 样件验证 / L4 生产签核须实物, 不在此判定):
  L0_REGISTERED    模板能构建
  L1_GEOMETRY_VALID  schema + 展开拓扑 + 两个导出件独立解析 全过
  L2_KINEMATIC     L1 + 折叠终态闭合/尺寸/穿插 全过 + 折线语义已声明且与参考面自洽 + 每条折线的 ±35°/180° 扰动都被闭合判据检出
                    (只证明终态运动学; 折叠路径可达性、印刷面/压线工艺面映射、制造特征约束均未评估 — GPT R2 §4.4)
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from .core.ir import class_defaults, class_module, from_raw
from .folding.engine import fold_all
from .parametric import base as templates
from .qa.pipeline import closure_sensitivity, run_qa
from .export.svg import render as svg_render, net_bbox
from .export.pdf import build_pdf
from .render.twin import render_twin


def _build_class(cls_id: str):
    """类默认参数 (家族模块按 class_params 派生) → 模板 IR; 与 CLI 的类分发同源."""
    params = class_defaults(cls_id)
    mod = class_module(cls_id)
    return mod, params, mod.build_ir(params)


GEOMETRY_GATES = ("G02", "G03", "G07", "G08", "G09", "G10")
FOLD_GATES = ("G04", "G05", "G06")
LEVELS = ("L0_REGISTERED", "L1_GEOMETRY_VALID", "L2_KINEMATIC")


def maturity_level(gates: dict, semantics: dict, sensitivity: dict) -> str:
    if not all(gates.get(g) == "PASS" for g in GEOMETRY_GATES):
        return "L0_REGISTERED"
    if not all(gates.get(g) == "PASS" for g in FOLD_GATES):
        return "L1_GEOMETRY_VALID"
    if not (semantics.get("declared") and semantics.get("n_mismatch", 1) == 0):
        return "L1_GEOMETRY_VALID"
    if not sensitivity.get("n_probed") or sensitivity.get("n_undetected", 1) or sensitivity.get("n_uncovered", 1):
        return "L1_GEOMETRY_VALID"
    return "L2_KINEMATIC"


def run_batch(out_dir: str, prefix: str | None = None, thumb: int = 320) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "thumbs").mkdir(exist_ok=True)
    classes = [c for c in templates.all_classes() if not prefix or c.startswith(prefix)]
    rows = []
    t0 = time.time()
    for cls_id in classes:
        row: dict = {"class_id": cls_id, "family": None, "status": "FAIL", "level": "L0_REGISTERED", "gates": {}}
        try:
            mod, params, ir_raw = _build_class(cls_id)
            ir_raw.pop("_derived", None)  # 模板内部派生量不进 IR 协议 (build 同款清理)
            row["family"] = cls_id.split("_")[0]
            row["params"] = params
            ir = from_raw(ir_raw)
            x0, y0, x1, y1 = net_bbox(ir)
            svg_text = svg_render(ir, x1 - x0, y1 - y0)
            pdf_bytes = build_pdf(ir, x1 - x0, y1 - y0)
            report = run_qa(ir, svg_text, pdf_bytes)
            row["gates"] = {g["id"]: g["status"] for g in report["gates"] if g["id"] != "G01"}
            g04 = next((g for g in report["gates"] if g["id"] == "G04"), {})
            row["qa_worst_closure_mm"] = (g04.get("metrics", {}).get("worst_residual_mm")
                                          if g04.get("status") == "PASS" else None)
            row["fold_semantics"] = g04.get("metrics", {}).get("fold_semantics", {})
            try:
                sens = closure_sensitivity(ir)
            except Exception as exc:  # noqa: BLE001  (灵敏度探针自身失败 = 未验证, 不冒充通过)
                sens = {"n_probed": 0, "n_undetected": 0, "n_uncovered": 0, "error": str(exc)[:120]}
            row["closure_sensitivity"] = {**sens, "undetected": list(sens.get("undetected", []))[:8]}
            row["level"] = maturity_level(row["gates"], row["fold_semantics"], sens)
            fold_all(ir)
            twin = render_twin(ir, size=thumb)
            twin.save(out / "thumbs" / f"{cls_id}.png")
            row["status"] = "GREEN" if all(v == "PASS" for v in row["gates"].values()) else "QA_FAIL"
        except Exception as exc:  # noqa: BLE001
            row["status"] = "ERROR"
            row["error"] = str(exc)[:200]
        rows.append(row)

    green = sum(1 for r in rows if r["status"] == "GREEN")
    by_level = {lv: sum(1 for r in rows if r["level"] == lv) for lv in LEVELS}
    report = {
        "batch_version": "0.2",
        "total_classes": len(rows),
        "green": green,
        "gate_green_ratio": round(green / max(1, len(rows)), 4),
        "maturity": by_level,
        "fold_edges_mislabeled": sum(r.get("fold_semantics", {}).get("n_mismatch", 0) for r in rows),
        "fold_edges_total": sum(r.get("fold_semantics", {}).get("n_edges", 0) for r in rows),
        "elapsed_s": round(time.time() - t0, 1),
        "rows": rows,
    }
    (out / "batch_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    _contact_sheet(rows, out / "contact_sheet.png", thumb)
    return report


def _contact_sheet(rows: list[dict], path: Path, thumb: int, cols: int = 6) -> None:
    show = [r for r in rows if r["status"] in ("GREEN", "QA_FAIL")]
    cell_w, cell_h = thumb + 8, thumb + 30
    n = max(1, len(show))
    rows_n = (n + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w + 8, rows_n * cell_h + 8), (250, 250, 250))
    d = ImageDraw.Draw(sheet)
    for i, r in enumerate(show):
        cx, cy = (i % cols) * cell_w + 8, (i // cols) * cell_h + 8
        try:
            im = Image.open(path.parent / "thumbs" / f"{r['class_id']}.png")
            sheet.paste(im, (cx, cy))
        except Exception:  # noqa: BLE001
            pass
        level = r.get("level", "L0_REGISTERED")[:2]
        color = {"L2": (30, 130, 60), "L1": (190, 130, 10)}.get(level, (200, 70, 50))
        d.text((cx, cy + thumb + 2), f"{r['class_id']} [{level}{'✓' if r['status'] == 'GREEN' else ''}]", fill=color)
    sheet.save(path)


def main_cli(out_dir: str, prefix: str | None) -> dict:
    rep = run_batch(out_dir, prefix)
    print(f"batch: {rep['green']}/{rep['total_classes']} green "
          f"({rep['elapsed_s']}s) -> {out_dir}/batch_report.json")
    bad = [r["class_id"] for r in rep["rows"] if r["status"] != "GREEN"]
    if bad:
        print("non-green:", ", ".join(bad))
    return rep
