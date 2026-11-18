"""M1 验收测试: 16 项合同中可机器判定部分的自动化 (pytest)."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from photo_dieline.core.ir import ARError, build, photo_evidence, validate_dict
from photo_dieline.export import pdf as pdfx
from photo_dieline.export import svg as svgx
from photo_dieline.folding.engine import fold_all
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
    from photo_dieline.cli import _layer_geo
    pdf_bytes = pdfx.build_pdf(ir, x1 - x0, y1 - y0, _layer_geo(ir))
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
