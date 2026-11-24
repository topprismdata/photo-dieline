"""photo-dieline CLI: spec + 照片 → IR / SVG / PDF / QA 报告."""
from __future__ import annotations

import json
from pathlib import Path

import typer

from .core.ir import ARError, build, class_defaults, class_module, resolve_params, save
from .export import pdf as pdfx
from .export import svg as svgx
from .qa.pipeline import run_qa

app = typer.Typer(help="photo-dieline: 实物包装照片 → 1:1 刀版", add_completion=False)


@app.command("build")
def build_cmd(
    spec: Path = typer.Option(..., "--spec", help="包装 spec JSON"),
    photo: Path = typer.Option(..., "--photo", help="实物参照照片"),
    out: Path = typer.Option(..., "--out", help="artifacts 输出目录"),
) -> None:
    """spec + photo → geometry-ir.json / dieline.svg / dieline.pdf / qa-report.json.

    按 spec.package 经模板注册表分发 (未注册的类显式报错, 不回退默认模板);
    几何参数由 resolve_params 给出: 实测/可信来源值优先于 spec.params 与模板默认值 (ADR-003)。
    """
    spec_d = json.loads(spec.read_text())
    try:
        params, overrides = resolve_params(spec_d)
        ir_tpl = class_module(spec_d["package"]).build_ir(params)
        ir = build(spec_d, photo, ir_tpl)
    except ARError as exc:
        typer.echo(f"输入错误: {exc}", err=True)
        raise typer.Exit(2) from exc
    for name, ov in overrides.items():
        typer.echo(f"实测优先: {name} 参数 {ov['from']:g} → 实测 {ov['to']:g} mm ({ov['status']})")

    out.mkdir(parents=True, exist_ok=True)
    ir_path = out / "geometry-ir.json"
    save(ir, ir_path)

    svg_text = svgx.render(ir, *_net_size(ir))
    (out / "dieline.svg").write_text(svg_text)

    pdf_bytes = pdfx.build_pdf(ir, *_net_size(ir))
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
def params(package: str = typer.Option("gable_top", "--package", help="模板类 ID")) -> None:
    """列出模板类的参数默认值 (mm)."""
    try:
        defaults = class_defaults(package)
    except ARError as exc:
        typer.echo(f"{exc}", err=True)
        raise typer.Exit(2) from exc
    for k, v in defaults.items():
        typer.echo(f"{k} = {v} mm")


def _net_size(ir):
    x0, y0, x1, y1 = svgx.net_bbox(ir)
    return x1 - x0, y1 - y0


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


@app.command("batch")
def batch_cmd(
    out: str = typer.Option("output/zoo100", "--out", help="批量输出目录"),
    prefix: str = typer.Option(None, "--prefix", help="只跑类ID前缀"),
) -> None:
    """注册表全类批量验证 (build→QA→fold→渲染→contact sheet)."""
    from .batch import main_cli
    main_cli(out, prefix)


def main():
    app()


if __name__ == "__main__":
    main()
