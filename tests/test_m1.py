"""M1 验收测试: 16 项合同中可机器判定部分的自动化 (pytest)."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from photo_dieline.core.ir import (ARError, build, class_defaults, photo_evidence, resolve_params,
                                   validate_dict)
from photo_dieline.export import pdf as pdfx
from photo_dieline.export import svg as svgx
from photo_dieline.folding.engine import fold_all
from photo_dieline.parametric import base as templates
from photo_dieline.parametric import gable_top
from photo_dieline.qa.pipeline import run_qa

ROOT = Path(__file__).resolve().parents[1]
SPEC = json.loads((ROOT / "examples" / "gable_top" / "spec.json").read_text())


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    photo = tmp_path_factory.mktemp("in") / "reference_photo.png"
    Image.new("RGB", (1200, 1600), (235, 235, 235)).save(photo)
    ir = build(dict(SPEC, measurements=SPEC["measurements"]), photo,
               gable_top.build_ir(SPEC["params"]))
    x0, y0, x1, y1 = svgx.net_bbox(ir)
    svg_text = svgx.render(ir, x1 - x0, y1 - y0)
    pdf_bytes = pdfx.build_pdf(ir, x1 - x0, y1 - y0)
    report = run_qa(ir, svg_text, pdf_bytes)
    return ir, svg_text, pdf_bytes, report


# ---- 输入 ----
def test_photo_evidence_recorded(env):
    ir, _, _, report = env
    assert report["photo"]["sha256"]
    assert min(report["photo"]["width_px"], report["photo"]["height_px"]) >= 1000


def test_photo_gate_rejects_small(tmp_path):
    small = tmp_path / "small.png"
    Image.new("RGB", (200, 200)).save(small)
    with pytest.raises(ARError):
        photo_evidence(small)


def test_measurements_evidence_status(env):
    ir, _, _, _ = env
    ev = ir.package["params_evidence"]
    assert ev["W"] == "MEASURED" and ev["glue_w"] == "DEFAULTED"


# ---- 几何 ----
def test_ir_schema_valid(env):
    validate_dict(env[0].raw)


def test_panel_fold_counts(env):
    ir, _, _, _ = env
    roles = [p["role"] for p in ir.panels]
    assert roles.count("wall") == 4 and roles.count("slope") == 2
    assert roles.count("fin") == 2 and roles.count("flap") == 4 and roles.count("glue") == 1
    assert len(ir.edges) == 12
    semantics = {e.mt_va for e in ir.edges}
    assert {"MOUNTAIN", "VALLEY"} <= semantics


def test_fold_closure_residuals(env):
    ir, _, _, _ = env
    world = fold_all(ir)
    checks = [
        ("slopeB", 3, "wallL", 3), ("slopeF", 3, "wallR", 3),
        ("slopeB", 2, "wallR", 3), ("slopeF", 2, "wallL", 3),
        ("wallL", 2, "slopeB", 0), ("wallR", 2, "slopeF", 0),
    ]
    for pa, ia, pb, ib in checks:
        d = float(np.linalg.norm(world[pa][ia] - world[pb][ib]))
        assert d <= 0.2, f"{pa}[{ia}] vs {pb}[{ib}] = {d:.3f}mm"


def test_golden_dimensions(env):
    ir, _, _, _ = env
    world = fold_all(ir)
    roles = {p["id"]: p["role"] for p in ir.panels}
    pts = np.vstack([v for pid, v in world.items() if roles[pid] in ("wall", "slope")])
    dims = [float(pts[:, i].max() - pts[:, i].min()) for i in range(3)]
    p = SPEC["params"]
    assert math.isclose(dims[0], p["W"], abs_tol=0.5)
    assert math.isclose(dims[1], p["D"], abs_tol=0.5)
    assert math.isclose(dims[2], p["Hb"] + p["Hr"], abs_tol=0.5)
    # 鳍双层顶缘距
    gap = abs(float(np.mean(world["finF"][2:4], axis=0)[1] - np.mean(world["finB"][2:4], axis=0)[1]))
    assert math.isclose(gap, p["fin_gap_mm"], abs_tol=0.2)


# ---- 刀版 ----
def test_svg_physical_layers(env):
    _, svg_text, _, _ = env
    m = __import__("re").search(r'width="([\d.]+)mm"', svg_text)
    assert m and float(m.group(1)) > 100  # mm 物理单位
    for layer in pdfx.LAYERS:
        assert f'id="{layer}"' in svg_text


def test_pdf_mediabox_and_bar(env):
    import re
    import zlib
    _, _, pdf_bytes, _ = env
    head = pdf_bytes[:4096].decode("latin-1")
    mb = re.search(r"/MediaBox \[0 0 ([\d.]+) ([\d.]+)\]", head)
    assert mb
    st = re.search(rb"stream\n(.*?)\nendstream", pdf_bytes, re.S)
    raw = zlib.decompress(st.group(1)).decode("latin-1")
    bar = any(abs(math.hypot(float(b[2]) - float(b[0]), float(b[3]) - float(b[1]))
                  - 50 * pdfx.PT_PER_MM) < 0.05
              for b in re.findall(r"([\d.]+) ([\d.]+) m\n([\d.]+) ([\d.]+) l", raw))
    assert bar
    assert len(re.findall(r"/Type /OCG", head)) == 7


# ---- QA ----
def test_qa_status_validated(env):
    report = env[3]
    assert report["status"] == "VALIDATED"
    assert all(g["status"] == "PASS" for g in report["gates"])


def test_cut_segments_separate_flaps(env):
    ir, _, _, _ = env
    segs = svgx.cut_segments(ir)
    # 粘口自由边 + 底板相邻分界(4块底板至少 5 条内部分界) 必须存在
    assert len(segs) >= 8
    keys = {tuple(sorted((tuple(a), tuple(b)))) for a, b in segs}
    fold_keys = {tuple(sorted((tuple(e.seg_2d[0]), tuple(e.seg_2d[1])))) for e in ir.edges}
    assert not (keys & fold_keys)  # 裁切段不得含折线


def test_qa_report_serializable(env, tmp_path):
    out = tmp_path / "qa-report.json"
    out.write_text(json.dumps(env[3]))
    assert json.loads(out.read_text())["qa_version"]


# ---- 工程 ----
def test_invalid_spec_rejected(tmp_path):
    photo = tmp_path / "p.png"
    Image.new("RGB", (1200, 1600)).save(photo)
    bad = gable_top.build_ir({"W": -5.0})  # 负宽
    bad.pop("_derived")
    with pytest.raises(Exception):
        validate_dict(bad)


# ---- 导出完整性: 坏交付物必须被 G07/G08 拒绝 (负探针) ----
def _gate(report, gid):
    return next(g for g in report["gates"] if g["id"] == gid)


def _shift_group(svg_text, gid, dx, dy):
    """文本级平移某图层的全部坐标 (模拟导出器丢弃净图原点的事故)。"""
    m = re.search(rf'(<g id="{gid}">)(.*?)(</g>)', svg_text, re.S)
    head, body, tail = m.groups()
    body = re.sub(r"(-?\d+\.\d+),(-?\d+\.\d+)",
                  lambda mm: f"{float(mm.group(1)) + dx:.3f},{float(mm.group(2)) + dy:.3f}", body)
    for ax in ("x1", "x2"):
        body = re.sub(rf'{ax}="(-?\d+\.\d+)"', lambda mm, ax=ax: f'{ax}="{float(mm.group(1)) + dx:.3f}"', body)
    for ay in ("y1", "y2"):
        body = re.sub(rf'{ay}="(-?\d+\.\d+)"', lambda mm, ay=ay: f'{ay}="{float(mm.group(1)) + dy:.3f}"', body)
    return svg_text[:m.start()] + head + body + tail + svg_text[m.end():]


def _rewrite_pdf_stream(pdf_bytes, fn):
    """解压内容流 → 改写 → 重新压缩, 并修正 /Length。"""
    import zlib
    m = re.search(rb"<< /Length (\d+) /Filter /FlateDecode >> stream\n(.*?)\nendstream", pdf_bytes, re.S)
    comp = zlib.compress(fn(zlib.decompress(m.group(2)).decode("latin-1")).encode("latin-1"))
    return (pdf_bytes[:m.start()] + b"<< /Length " + str(len(comp)).encode()
            + b" /Filter /FlateDecode >> stream\n" + comp + b"\nendstream" + pdf_bytes[m.end():])


def test_svg_geometry_stays_on_page(env):
    """导出器曾丢弃净图原点: 95/100 类的几何被平移出画布 (屋顶/底部折页整段丢失)。"""
    ir, _svg_text, _pdf_bytes, report = env
    g07 = _gate(report, "G07")
    assert g07["status"] == "PASS" and g07["metrics"]["out_of_page_points"] == 0
    _x0, y0, _x1, _y1 = svgx.net_bbox(ir)
    assert y0 != 0.0  # gable_top 净图原点不在 (0,0): 这条测试针对的正是这类模板


def test_qa_rejects_scaled_offpage_or_barless_svg(env):
    """SVG 缩半 (非 1:1) / CUT 层平移出页 / 删除 50mm 校验条 → G07 必须 FAIL。"""
    ir, svg_text, pdf_bytes, _ = env
    scaled = re.sub(r'(width|height)="([\d.]+)(mm)"',
                    lambda mm: f'{mm.group(1)}="{float(mm.group(2)) / 2:g}{mm.group(3)}"', svg_text, count=2)
    scaled = re.sub(r'viewBox="0 0 ([\d.]+) ([\d.]+)"',
                    lambda mm: f'viewBox="0 0 {float(mm.group(1)) / 2:g} {float(mm.group(2)) / 2:g}"', scaled)
    offpage = _shift_group(svg_text, "CUT", 0.0, -150.0)
    nobar, n = re.subn(r'<line x1="12\.000" y1="[\d.]+" x2="62\.000" y2="[\d.]+"[^>]*/>', "", svg_text)
    assert n == 1
    for name, bad in (("scaled", scaled), ("offpage", offpage), ("nobar", nobar)):
        assert _gate(run_qa(ir, bad, pdf_bytes), "G07")["status"] == "FAIL", name


def test_pdf_opens_in_independent_parser(env):
    """手写 PDF 曾有两处语法错误: 独立引擎打不开/渲染全白, 图层错挂、无 GLUE/REGISTRATION。"""
    import io
    import pypdf
    page = pypdf.PdfReader(io.BytesIO(env[2]), strict=True).pages[0]
    props = page["/Resources"]["/Properties"]
    assert [str(props[k].get("/Name")) for k in props.keys()] == pdfx.LAYERS
    used = re.findall(r"/OC (/P\d+) BDC", page.get_contents().get_data().decode("latin-1"))
    assert len(used) == len(set(used)) == len(pdfx.LAYERS)
    g08 = _gate(env[3], "G08")
    assert g08["status"] == "PASS" and g08["metrics"]["out_of_page_points"] == 0
    assert set(g08["metrics"]["mounted_layers"]) == set(pdfx.LAYERS)


def test_qa_rejects_broken_pdf(env):
    """键缺 `/`、BDC 缺 tag、图层错挂、内容流缩放 → G08 必须 FAIL。"""
    ir, svg_text, pdf_bytes, _ = env
    cases = {
        "key_not_name": pdf_bytes.replace(b"/Properties << /P0", b"/Properties << P0", 1),
        "bdc_missing_tag": _rewrite_pdf_stream(pdf_bytes, lambda s: s.replace("/OC /P0 BDC", "/P0 BDC", 1)),
        "layer_mismounted": _rewrite_pdf_stream(pdf_bytes, lambda s: s.replace("/OC /P3 BDC", "/OC /P9 BDC", 1)),
        "content_scaled": _rewrite_pdf_stream(pdf_bytes, lambda s: "0.5 0 0 0.5 0 0 cm\n" + s),
    }
    for name, bad in cases.items():
        assert bad != pdf_bytes, name
        assert _gate(run_qa(ir, svg_text, bad), "G08")["status"] == "FAIL", name


def test_measured_value_wins_and_faked_measurement_rejected(tmp_path):
    """ADR-003 实测优先: 实测值覆盖参数; 参数与实测不符却标 MEASURED → ARError。"""
    photo = tmp_path / "p.png"
    Image.new("RGB", (1200, 1600)).save(photo)
    spec = dict(SPEC, params=dict(SPEC["params"], W=50.0))  # 参数写 50, 实测是 45
    params, overrides = resolve_params(spec)
    assert params["W"] == 45.0
    assert overrides["W"] == {"from": 50.0, "to": 45.0, "status": "MEASURED"}
    ir = build(spec, photo, gable_top.build_ir(params))
    assert ir.package["params"]["W"] == 45.0 and ir.package["params_evidence"]["W"] == "MEASURED"
    with pytest.raises(ARError, match="实测值与几何参数不一致"):
        build(spec, photo, gable_top.build_ir({**SPEC["params"], "W": 50.0}))
    with pytest.raises(ARError, match="未定义的参数"):
        resolve_params({"package": "gable_top", "params": {"Widht": 45.0}})
    with pytest.raises(ARError, match="未注册模板类"):
        resolve_params({"package": "FEFCO_0201_not_supported", "params": SPEC["params"]})


def test_build_dispatches_by_package(tmp_path):
    """CLI 曾硬编码 gable_top: 未注册类必须报错, 其他注册类必须按 spec.package 构建。"""
    from typer.testing import CliRunner
    from photo_dieline.cli import app
    photo = tmp_path / "p.png"
    Image.new("RGB", (1200, 1600)).save(photo)
    runner = CliRunner()
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"package": "FEFCO_0201_not_supported", "params": SPEC["params"]}))
    r = runner.invoke(app, ["build", "--spec", str(bad), "--photo", str(photo), "--out", str(tmp_path / "o1")])
    assert r.exit_code == 2 and "未注册模板类" in r.output
    ok = tmp_path / "ok.json"
    ok.write_text(json.dumps({"package": "rsc_rsc", "params": class_defaults("rsc_rsc")}))
    r = runner.invoke(app, ["build", "--spec", str(ok), "--photo", str(photo), "--out", str(tmp_path / "o2")])
    assert r.exit_code == 0, r.output
    ir = json.loads((tmp_path / "o2" / "geometry-ir.json").read_text())
    assert ir["package"]["template"]["id"] == "rsc_rsc"


def test_photo_gate_rejects_non_photo_formats(tmp_path):
    p = tmp_path / "x.gif"
    Image.new("RGB", (1200, 1600), (200, 10, 10)).save(p)
    with pytest.raises(ARError, match="照片格式"):
        photo_evidence(p)


def test_qa_report_has_ten_gates(env):
    ids = [g["id"] for g in env[3]["gates"]]
    assert ids == [f"G{i:02d}" for i in range(1, 11)]  # G01 与 G09 曾根本不存在 ("十门" 实为 8 门)
    assert env[3]["status"] == "VALIDATED"


def test_zoo_exports_stay_on_page_and_parse():
    """全动物园回归: 每个注册类的 SVG/PDF 都须几何在页内、PDF 可被独立解析器打开。"""
    from photo_dieline.batch import _build_class
    from photo_dieline.core.ir import from_raw
    bad = {}
    for cls_id in templates.all_classes():
        _mod, _params, raw = _build_class(cls_id)
        ir = from_raw(raw)
        x0, y0, x1, y1 = svgx.net_bbox(ir)
        rep = run_qa(ir, svgx.render(ir, x1 - x0, y1 - y0), pdfx.build_pdf(ir, x1 - x0, y1 - y0))
        fails = [g["id"] for g in rep["gates"] if g["id"] in ("G07", "G08", "G09") and g["status"] != "PASS"]
        if fails:
            bad[cls_id] = fails
    assert not bad, bad


def test_qa_rejects_overlapping_panels_and_hinge_cut(env):
    """展开图面板重叠 / 折线一侧被细分致铰链被画成裁切 → G03 必须 FAIL (15 类曾带着切穿结构的刀版判 GREEN)。"""
    import copy
    from photo_dieline.core.ir import from_raw
    base = env[0].raw
    assert _gate(env[3], "G03")["metrics"]["n_overlap_pairs"] == 0

    dup = copy.deepcopy(base)
    ghost = copy.deepcopy(next(p for p in dup["panels"] if p["id"] == "glue"))
    ghost["id"] = "glue_dup"
    ghost["polygon_2d"] = [[x + 20.0, y] for x, y in ghost["polygon_2d"]]  # 压在 wallL 上
    dup["panels"].append(ghost)
    g03 = _gate(run_qa(from_raw(dup), "", b""), "G03")
    assert g03["status"] == "FAIL" and "展开图面板重叠" in g03["detail"]

    split = copy.deepcopy(base)
    fold = next(e for e in split["edges"] if e["fold"]["parent"] == "front" and e["fold"]["child"] == "flapF")
    (ax, ay), (bx, by) = fold["seg_2d"]
    pts = next(p for p in split["panels"] if p["id"] == "front")["polygon_2d"]
    for i in range(len(pts)):
        p, q = pts[i], pts[(i + 1) % len(pts)]
        if ([p, q] == [[ax, ay], [bx, by]]) or ([p, q] == [[bx, by], [ax, ay]]):
            pts.insert(i + 1, [(ax + bx) / 2, (ay + by) / 2])  # 折线仍是整段, 面板边被一分为二
            break
    else:
        raise AssertionError("front|flapF 折线不是 front 的一条完整边")
    g03 = _gate(run_qa(from_raw(split), "", b""), "G03")
    assert g03["status"] == "FAIL" and "裁切缝切穿结构" in g03["detail"]
