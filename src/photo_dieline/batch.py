"""批量验证: 注册表全类 → build→QA→fold→渲染 → 对账 JSON + contact sheet.

用法: photo-dieline batch --out output/zoo100 [--prefix prism]
验收口径: gate_green = G02-G10 全 PASS (G01 照片门按证据分级单列)
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
from .qa.pipeline import run_qa
from .export.svg import render as svg_render, net_bbox
from .export.pdf import build_pdf
from .render.twin import render_twin


def _build_class(cls_id: str):
    """类默认参数 (家族模块按 class_params 派生) → 模板 IR; 与 CLI 的类分发同源."""
    params = class_defaults(cls_id)
    mod = class_module(cls_id)
    return mod, params, mod.build_ir(params)


def run_batch(out_dir: str, prefix: str | None = None, thumb: int = 320) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "thumbs").mkdir(exist_ok=True)
    classes = [c for c in templates.all_classes() if not prefix or c.startswith(prefix)]
    rows = []
    t0 = time.time()
    for cls_id in classes:
        row: dict = {"class_id": cls_id, "family": None, "status": "FAIL", "gates": {}}
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
            row["qa_worst_closure_mm"] = next((g["metrics"].get("worst_residual_mm") for g in report["gates"]
                                               if g["id"] == "G04" and g["status"] == "PASS"), None)
            world = fold_all(ir)
            twin = render_twin(ir, size=thumb)
            twin.save(out / "thumbs" / f"{cls_id}.png")
            row["status"] = "GREEN" if all(v == "PASS" for v in row["gates"].values()) else "QA_FAIL"
        except Exception as exc:  # noqa: BLE001
            row["status"] = "ERROR"
            row["error"] = str(exc)[:200]
        rows.append(row)

    green = sum(1 for r in rows if r["status"] == "GREEN")
    report = {
        "batch_version": "0.1",
        "total_classes": len(rows),
        "green": green,
        "gate_green_ratio": round(green / max(1, len(rows)), 4),
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
        color = (30, 130, 60) if r["status"] == "GREEN" else (200, 80, 60)
        d.text((cx, cy + thumb + 2), f"{r['class_id']} [{r['status']}]", fill=color)
    sheet.save(path)


def main_cli(out_dir: str, prefix: str | None) -> dict:
    rep = run_batch(out_dir, prefix)
    print(f"batch: {rep['green']}/{rep['total_classes']} green "
          f"({rep['elapsed_s']}s) -> {out_dir}/batch_report.json")
    bad = [r["class_id"] for r in rep["rows"] if r["status"] != "GREEN"]
    if bad:
        print("non-green:", ", ".join(bad))
    return rep
