"""photo-dieline CLI: spec + 照片 → IR / SVG / PDF / QA 报告."""
from __future__ import annotations

import json
from pathlib import Path

import typer

from .core.ir import ARError, build, save
from .export import pdf as pdfx
from .export import svg as svgx
from .parametric import gable_top
from .qa.pipeline import run_qa

app = typer.Typer(help="photo-dieline: 实物包装照片 → 1:1 刀版", add_completion=False)

MM = {"CUT": ((204, 34, 34), 0.3, None),
      "GLUE": ((127, 168, 143), 0.25, None)}


@app.command("build")
def build_cmd(
    spec: Path = typer.Option(..., "--spec", help="包装 spec JSON"),
    photo: Path = typer.Option(..., "--photo", help="实物参照照片"),
    out: Path = typer.Option(..., "--out", help="artifacts 输出目录"),
) -> None:
    """垂直切片: spec+photo → geometry-ir.json / dieline.svg / dieline.pdf / qa-report.json"""
    spec_d = json.loads(spec.read_text())
    params = {k: float(v) for k, v in spec_d.get("params", {}).items()}
    ir_tpl = gable_top.build_ir(params)
    ir = build(spec_d, photo, ir_tpl)

    out.mkdir(parents=True, exist_ok=True)
    ir_path = out / "geometry-ir.json"
    save(ir, ir_path)

    svg_text = svgx.render(ir, *_net_size(ir))
    (out / "dieline.svg").write_text(svg_text)

    layer_geo = _layer_geo(ir)
    pdf_bytes = pdfx.build_pdf(ir, *_net_size(ir), layer_geo)
    (out / "dieline.pdf").write_bytes(pdf_bytes)

    report = run_qa(ir, svg_text, pdf_bytes)
    (out / "qa-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    typer.echo(f"QA status: {report['status']}")
    for gate in report["gates"]:
        typer.echo(f"  {gate['id']} {gate['status']:4s} {gate['name']}"
                   + (f"  {gate['detail']}" if gate["status"] == "FAIL" else ""))
    if report["status"] != "VALIDATED":
        raise typer.Exit(1)


@app.command()
def params() -> None:
    """列出 gable_top 模板参数与默认值."""
    for k, v in gable_top.DEFAULTS.items():
        typer.echo(f"{k} = {v} mm")


def _net_size(ir):
    x0, y0, x1, y1 = svgx.net_bbox(ir)
    return x1 - x0, y1 - y0


def _layer_geo(ir):
    """净图坐标(mm) → PDF 图层几何."""
    geo: dict[str, list] = {}
    for name, (rgb, w, dash) in {
        "CUT": ((0.8, 0.13, 0.13), 0.3, None),
        "CREASE-MOUNTAIN": ((0.13, 0.27, 0.8), 0.25, (4, 3)),
        "CREASE-VALLEY": ((0.12, 0.54, 0.23), 0.25, (10, 3, 2, 3)),
        "BLEED": ((0.8, 0.13, 0.67), 0.25, (3, 3)),
    }.items():
        geo[name] = []
    # CUT 外轮廓
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    outline = unary_union([Polygon(p["polygon_2d"]) for p in ir.panels]).buffer(0)
    ring = outline.exterior if outline.geom_type == "Polygon" else max(
        (g.exterior for g in outline.geoms), key=lambda g: g.area)
    geo["CUT"].append((list(ring.coords), (0.8, 0.13, 0.13), 0.3, None))
    for a, b in svgx.cut_segments(ir):
        geo["CUT"].append(([a, b], (0.8, 0.13, 0.13), 0.3, None))
    bleed = outline.buffer(3.0)
    bring = bleed.exterior if bleed.geom_type == "Polygon" else max(
        (g.exterior for g in bleed.geoms), key=lambda g: g.area)
    geo["BLEED"].append((list(bring.coords), (0.8, 0.13, 0.67), 0.25, (3, 3)))
    for e in ir.edges:
        layer = "CREASE-MOUNTAIN" if e.mt_va == "MOUNTAIN" else "CREASE-VALLEY"
        geo[layer].append(([tuple(e.seg_2d[0]), tuple(e.seg_2d[1])],
                           (0.13, 0.27, 0.8) if e.mt_va == "MOUNTAIN" else (0.12, 0.54, 0.23),
                           0.25, (4, 3) if e.mt_va == "MOUNTAIN" else (10, 3, 2, 3)))
    # 50mm 校验条 (INFO)
    geo["INFO"] = [([(12.0, 8.0), (62.0, 8.0)], (0.07, 0.07, 0.07), 0.5, None)]
    return geo


@app.command("render")
def render_cmd(
    ir_path: str = typer.Option(..., "--ir", help="geometry-ir.json"),
    photo: str = typer.Option(..., "--photo", help="实拍参照照"),
    out: str = typer.Option(..., "--out", help="对比图输出 PNG"),
    az: float = typer.Option(-22.0, help="相机方位角(度)"),
    el: float = typer.Option(16.0, help="相机仰角(度)"),
    debug_ids: bool = typer.Option(False, "--debug-ids", help="面板ID调试渲染(异色+背面剔除+图例)"),
) -> None:
    """逆向孪生折叠渲染 + 与实拍并排对比 (photo-alignment 人工确认件)."""
    from .core.ir import from_raw
    from .render.twin import compare_side_by_side, render_twin

    ir = from_raw(json.loads(Path(ir_path).read_text()))
    twin = render_twin(ir, az_deg=az, el_deg=el, debug_ids=debug_ids)
    twin_path = Path(out).with_name(Path(out).stem + "_twin.png")
    twin.save(twin_path)
    compare_side_by_side(photo, twin, out)
    typer.echo(f"twin: {twin_path}")
    typer.echo(f"compare: {out}")


def main():
    app()


if __name__ == "__main__":
    main()
