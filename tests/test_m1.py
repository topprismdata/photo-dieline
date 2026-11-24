"""M1 验收测试: 16 项合同中可机器判定部分的自动化 (pytest)."""
from __future__ import annotations

import copy
import json
import math
import re
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from photo_dieline.core.ir import (ARError, build, class_defaults, photo_evidence, resolve_params,
                                   from_raw, validate_dict)
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
    """全动物园回归: 每个注册类要么导出成功且 G07/G08/G09 通过 (几何在页内、PDF 可被独立解析器打开),
要么导出被拒 —— 而拒绝必须对应拓扑门 (G03) 的真实缺陷, 不允许"拒了但说不出为什么"。"""
    from photo_dieline.batch import _build_class
    from photo_dieline.core.ir import from_raw
    bad, refused = {}, {}
    for cls_id in templates.all_classes():
        _mod, _params, raw = _build_class(cls_id)
        ir = from_raw(raw)
        x0, y0, x1, y1 = svgx.net_bbox(ir)
        try:
            rep = run_qa(ir, svgx.render(ir, x1 - x0, y1 - y0), pdfx.build_pdf(ir, x1 - x0, y1 - y0))
        except ARError as exc:
            refused[cls_id] = str(exc)
            if _gate(run_qa(ir, "", b""), "G03")["status"] != "PASS":
                continue
            bad[cls_id] = f"导出被拒但 G03 没有报出原因: {exc}"
            continue
        fails = [g["id"] for g in rep["gates"] if g["id"] in ("G07", "G08", "G09") and g["status"] != "PASS"]
        if fails:
            bad[cls_id] = fails
    assert not bad, {"bad": bad, "refused": refused}


def _split_edge_at_fold(raw):
    """把 front|flapF 折线所在的 front 面板边从中点一分为二 (折线仍是整段, 面板边被细分). 返回折线端点."""
    fold = next(e for e in raw["edges"] if e["fold"]["parent"] == "front" and e["fold"]["child"] == "flapF")
    (ax, ay), (bx, by) = fold["seg_2d"]
    pts = next(p for p in raw["panels"] if p["id"] == "front")["polygon_2d"]
    for i in range(len(pts)):
        p, q = pts[i], pts[(i + 1) % len(pts)]
        if ([p, q] == [[ax, ay], [bx, by]]) or ([p, q] == [[bx, by], [ax, ay]]):
            pts.insert(i + 1, [(ax + bx) / 2, (ay + by) / 2])
            return (ax, ay), (bx, by)
    raise AssertionError("front|flapF 折线不是 front 的一条完整边")


def test_qa_rejects_overlapping_panels(env):
    """展开图面板两两重叠 (正面积) → G03 必须 FAIL (14 类曾带着面板重叠的刀版判 GREEN)。"""
    import copy
    from photo_dieline.core.ir import from_raw
    assert _gate(env[3], "G03")["metrics"]["n_overlap_pairs"] == 0
    dup = copy.deepcopy(env[0].raw)
    ghost = copy.deepcopy(next(p for p in dup["panels"] if p["id"] == "glue"))
    ghost["id"] = "glue_dup"
    ghost["polygon_2d"] = [[x + 20.0, y] for x, y in ghost["polygon_2d"]]  # 压在 wallL 上
    dup["panels"].append(ghost)
    g03 = _gate(run_qa(from_raw(dup), "", b""), "G03")
    assert g03["status"] == "FAIL" and "展开图面板重叠" in g03["detail"]


def test_subdivided_hinge_stays_a_fold(env):
    """折线一侧的顶点细分与折线端点不对应, 本身不是模板错误: 导出须做共线归一 —
    铰链仍是折线, 不得画成裁切 (rsc_handhole 顶翼-前墙的全部实际连接 130mm、egg_tray_2x4 的 860mm 曾被画成 CUT)。"""
    import copy
    from shapely.geometry import LineString
    from photo_dieline.core.ir import from_raw
    from photo_dieline.export import layout as lay
    split = copy.deepcopy(env[0].raw)
    a, b = _split_edge_at_fold(split)
    ir = from_raw(split)
    x0, y0, x1, y1 = svgx.net_bbox(ir)
    report = run_qa(ir, svgx.render(ir, x1 - x0, y1 - y0), pdfx.build_pdf(ir, x1 - x0, y1 - y0))
    g03 = _gate(report, "G03")
    assert g03["status"] == "PASS" and g03["metrics"]["cut_on_fold_mm"] == 0.0
    fold_line = LineString([a, b])

    def to_net(shape):
        return LineString([(x + x0 - lay.MARGIN, y + y0 - lay.MARGIN) for x, y in shape.pts])  # 页面 → 模板坐标

    shapes = lay.page_shapes(ir)
    for s in shapes["CUT"]:
        assert to_net(s).intersection(fold_line).length < 1e-6   # CUT 层没有任何一段落在铰链上
    creases = [s for k in ("CREASE-MOUNTAIN", "CREASE-VALLEY") for s in shapes[k]]
    assert any(to_net(s).covers(fold_line) for s in creases)     # 铰链完整地留在折线层


# ---- 独立金标: 页面坐标手算, 不经过任何被验证的模块 ----
def _page_lines(svg_text, gid):
    """SVG 某图层的线段, 换算成页面坐标 (y 向上, mm)."""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(svg_text)
    h = float(root.get("height")[:-2])
    grp = next(x for x in root.iter("{http://www.w3.org/2000/svg}g") if x.get("id") == gid)
    return [(float(e.get("x1")), h - float(e.get("y1")), float(e.get("x2")), h - float(e.get("y2")))
            for e in grp.iter("{http://www.w3.org/2000/svg}line")]


def test_hand_computed_golden_page(env):
    """独立金标: 页面坐标由 spec 参数手算 (勾股求坡面长; 粘口 + 四面墙; 底折页 + 墙 + 坡面 + 立鳍)。
    导出器与 QA 共用坐标变换时三者可以一致地错 — 这条对账是外部基准 (GPT R1 A1–4 签署条件)。"""
    W, D, Hb, Hr, Ef, gw = (SPEC["params"][k] for k in ("W", "D", "Hb", "Hr", "Ef", "glue_w"))
    m = 12.0
    s = math.hypot(D / 2, Hr)
    page_w, page_h = gw + 4 * W + 2 * m, D + Hb + s + Ef + 2 * m
    crease_x = [m + gw, m + gw + W, m + gw + 2 * W, m + gw + 3 * W]
    crease_y = [m + D, m + D + Hb, m + D + Hb + s]
    cut_x, cut_y = [m, m + gw + 4 * W], [m, m + D + Hb + s + Ef]

    svg = env[1]
    root_h = float(__import__("re").search(r'height="([\d.]+)mm"', svg).group(1))
    root_w = float(__import__("re").search(r'width="([\d.]+)mm"', svg).group(1))
    assert (root_w, root_h) == pytest.approx((page_w, page_h), abs=1e-3)
    creases = _page_lines(svg, "CREASE-MOUNTAIN") + _page_lines(svg, "CREASE-VALLEY")
    assert sorted({a for a, _b, c, _d in creases if abs(a - c) < 1e-9}) == pytest.approx(crease_x, abs=1e-3)
    assert sorted({b for _a, b, _c, d in creases if abs(b - d) < 1e-9}) == pytest.approx(crease_y, abs=1e-3)
    import xml.etree.ElementTree as ET
    grp = next(x for x in ET.fromstring(svg).iter("{http://www.w3.org/2000/svg}g") if x.get("id") == "CUT")
    pts = []
    for e in grp.iter("{http://www.w3.org/2000/svg}polygon"):
        v = [float(t) for t in e.get("points").replace(",", " ").split()]
        pts += list(zip(v[0::2], v[1::2]))
    assert [min(p[0] for p in pts), max(p[0] for p in pts)] == pytest.approx(cut_x, abs=1e-3)
    assert [page_h - max(p[1] for p in pts), page_h - min(p[1] for p in pts)] == pytest.approx(cut_y, abs=1e-3)
    bar = max(_page_lines(svg, "INFO"), key=lambda t: abs(t[2] - t[0]))
    assert (bar[0], bar[1], bar[3]) == pytest.approx((m, page_h - 8, page_h - 8), abs=1e-3)
    assert bar[2] - bar[0] == pytest.approx(50.0, abs=1e-3)

    import io
    import re
    import pypdf
    page = pypdf.PdfReader(io.BytesIO(env[2]), strict=True).pages[0]
    k = 72 / 25.4
    assert (float(page.mediabox.width), float(page.mediabox.height)) == pytest.approx((page_w * k, page_h * k), abs=0.05)
    blocks = dict(re.findall(r"/OC (/P\d+) BDC\n(.*?)\nEMC", page.get_contents().get_data().decode("latin-1"), re.S))

    def segs(ops):
        return [tuple(float(v) / k for v in s) for s in re.findall(r"([\d.]+) ([\d.]+) m\n([\d.]+) ([\d.]+) l", ops)]

    crease = segs(blocks["/P1"]) + segs(blocks["/P2"])
    assert sorted({a for a, _b, c, _d in crease if abs(a - c) < 1e-9}) == pytest.approx(crease_x, abs=1e-3)
    assert sorted({b for _a, b, _c, d in crease if abs(b - d) < 1e-9}) == pytest.approx(crease_y, abs=1e-3)
    bar = max(segs(blocks["/P6"]), key=lambda t: abs(t[2] - t[0]))
    assert (bar[0], bar[1], bar[3]) == pytest.approx((m, page_h - 8, page_h - 8), abs=1e-3)
    assert bar[2] - bar[0] == pytest.approx(50.0, abs=1e-3)


def test_golden_template_is_fold_valid():
    """金标模板: 折线语义已声明且自洽; 每条折线的 ±35°/180° 扰动都被闭合判据检出 (修复前 4/12 漏检)。"""
    from photo_dieline.qa.pipeline import closure_sensitivity, fold_semantics
    from photo_dieline.core.ir import from_raw
    ir = from_raw(gable_top.build_ir(SPEC["params"]))
    world = fold_all(ir)
    sem = fold_semantics(ir, world)
    assert sem["declared"] and sem["n_mismatch"] == 0 and sem["n_undetermined"] == 0
    sens = closure_sensitivity(ir)
    assert sens["n_probed"] == len(ir.edges) and sens["n_undetected"] == 0 and sens["n_uncovered"] == 0
    assert min(sens["min_worst_residual_mm_by_angle"].values()) > 0.2


def _set_tdir(eid, v):
    return lambda raw: next(e for e in raw["edges"] if e["id"] == eid)["fold"].update(target_dir_3d=list(v))


def _mutate(raw, fn):
    fn(raw)
    return raw


def _finB_like_finF(raw):
    ff = next(e for e in raw["edges"] if e["id"] == "e_sl_ff")["fold"]["target_dir_3d"]
    next(e for e in raw["edges"] if e["id"] == "e_sl_fb")["fold"]["target_dir_3d"] = list(ff)


def _flip_all_mt_va(raw):
    for e in raw["edges"]:
        e["fold"]["mt_va"] = {"MOUNTAIN": "VALLEY", "VALLEY": "MOUNTAIN"}[e["fold"]["mt_va"]]


def _third_panel_shares_fold(raw):
    ghost = copy.deepcopy(next(p for p in raw["panels"] if p["id"] == "back"))
    ghost["id"] = "back_dup"
    raw["panels"].append(ghost)


def _self_intersect_front(raw):
    pts = next(p for p in raw["panels"] if p["id"] == "front")["polygon_2d"]
    pts[0], pts[1] = pts[1], pts[0]   # 矩形顶点 0/1 对调 → 自交 (蝶形)


def _score_one_edge(raw):
    next(e for e in raw["edges"] if e["id"] == "e_wl_bk")["fold"]["mt_va"] = "SCORE"


MUTATIONS = [
    ("粘口折向盒外", _set_tdir("e_glue", (-1, 0, 0)), "G04"),
    ("背底板下垂未折", _set_tdir("e_bk_fl", (0, 0, -1)), "G04"),
    ("左底板折到墙外", _set_tdir("e_wl_fl", (-1, 0, 0)), "G04"),
    ("右底板折到墙外", _set_tdir("e_wr_fl", (1, 0, 0)), "G04"),
    ("两鳍重合", _finB_like_finF, "G04"),
    ("折线 M/V 全部互换", _flip_all_mt_va, "G04"),
    ("第三块板共享折线 (非流形)", _third_panel_shares_fold, "G03"),
    ("面板多边形自交", _self_intersect_front, "G03"),
    ("折线语义改成 SCORE (无对应图层)", _score_one_edge, "G07"),
    ("参考面翻到另一侧但标签不翻", lambda raw: raw["package"]["template"].update(mt_va_reference="polygon_2d_cw"), "G04"),
    ("折向带铰链轴分量 (不垂直铰链, 闭合判据不敏感)", _set_tdir("e_bk_sl", (0.3, -0.88, 0.47)), "G04"),
]


@pytest.mark.parametrize("label,mutate,gate", MUTATIONS, ids=[m[0] for m in MUTATIONS])
def test_golden_mutations_are_rejected(label, mutate, gate):
    """审计变异矩阵回放: 每种单点破坏必须被指定门拒绝 (修复前 27 个里 15 个仍判 VALIDATED)。"""
    import copy
    from photo_dieline.core.ir import from_raw
    raw = copy.deepcopy(gable_top.build_ir(SPEC["params"]))
    mutate(raw)
    ir = from_raw(raw)
    x0, y0, x1, y1 = svgx.net_bbox(ir)
    try:
        svg_text, pdf_bytes = svgx.render(ir, x1 - x0, y1 - y0), pdfx.build_pdf(ir, x1 - x0, y1 - y0)
    except ARError:   # 导出器直接拒绝 (如 SCORE 无对应图层)
        svg_text, pdf_bytes = "", b""
    report = run_qa(ir, svg_text, pdf_bytes)
    assert _gate(report, gate)["status"] == "FAIL", label
    assert report["status"] == "DRAFT", label


def _hr_for_slope(deg):
    """使屋脊坡角 atan(2*Hr/D) = deg 的 Hr。"""
    return SPEC["params"]["D"] / 2.0 * math.tan(math.radians(deg))


@pytest.mark.parametrize("label,params,domain_ok", [
    ("鳍顶距 = 2*Ef (鳍倾角 90°, 鳍高为 0)", {"fin_gap_mm": 2 * SPEC["params"]["Ef"]}, False),
    ("屋脊坡角 4.5° (低于下限, 与平顶盒不可区分)", {"Hr": _hr_for_slope(4.5)}, False),
    ("屋脊坡角 5.5° (域内下沿, 不得过拒)", {"Hr": _hr_for_slope(5.5)}, True),
], ids=["fin_gap=2Ef", "slope_4.5deg", "slope_5.5deg"])
def test_param_domain_boundary(label, params, domain_ok):
    """模板适用域 (G02): 几何自洽但超出模板假设的参数不得出 VALIDATED (修复前 Hr=0.001 判 VALIDATED);
    域内下沿必须仍通过 — 域是对模板假设的声明, 不是越严越好。"""
    from photo_dieline.core.ir import from_raw
    raw = gable_top.build_ir({**SPEC["params"], **params})
    ir = from_raw(raw)
    x0, y0, x1, y1 = svgx.net_bbox(ir)
    report = run_qa(ir, svgx.render(ir, x1 - x0, y1 - y0), pdfx.build_pdf(ir, x1 - x0, y1 - y0))
    assert (_gate(report, "G02")["status"] == "PASS") is domain_ok, label
    assert (report["status"] == "VALIDATED") is domain_ok, label


def test_maturity_level_requires_semantics_and_sensitivity():
    from photo_dieline.batch import FOLD_GATES, GEOMETRY_GATES, maturity_level
    ok = {g: "PASS" for g in GEOMETRY_GATES + FOLD_GATES}
    good = {"n_probed": 12, "n_undetected": 0, "n_uncovered": 0}
    sem = {"declared": True, "n_mismatch": 0}
    assert maturity_level(ok, sem, good) == "L2_KINEMATIC"
    assert maturity_level(ok, {**sem, "declared": False}, good) == "L1_GEOMETRY_VALID"
    assert maturity_level(ok, {**sem, "n_mismatch": 1}, good) == "L1_GEOMETRY_VALID"
    assert maturity_level(ok, sem, {**good, "n_undetected": 1}) == "L1_GEOMETRY_VALID"
    assert maturity_level(ok, sem, {**good, "n_probed": 0}) == "L1_GEOMETRY_VALID"
    assert maturity_level({**ok, "G04": "FAIL"}, sem, good) == "L1_GEOMETRY_VALID"
    assert maturity_level({**ok, "G03": "FAIL"}, sem, good) == "L0_REGISTERED"


# ---- A4 专项 (GPT R2: 实测覆盖、冲突实测、类分发、无照片模式 须各有专项证据) ----
def _photo(tmp_path):
    p = tmp_path / "p.png"
    Image.new("RGB", (1200, 1600), (235, 235, 235)).save(p)
    return p


def test_measured_override_recomputes_derived_panels(tmp_path):
    """参数 W=50、实测 W=45 → 结果为 45, 且派生面板尺寸同步重算 (不是只改一个数字)."""
    spec = dict(SPEC, params=dict(SPEC["params"], W=50.0))
    params, _overrides = resolve_params(spec)
    ir = build(spec, _photo(tmp_path), gable_top.build_ir(params))
    assert ir.package["params"]["W"] == 45.0
    for pid in ("front", "back", "flapF", "flapB"):     # 宽 = W 的面板全部重算
        assert np.ptp(np.asarray(ir.panel(pid)["polygon_2d"], float)[:, 0]) == pytest.approx(45.0), pid
    glue = np.asarray(ir.panel("glue")["polygon_2d"], float)
    assert np.ptp(glue[:, 0]) == pytest.approx(SPEC["params"]["glue_w"])   # 粘口宽不受影响


def test_conflicting_measurements_are_refused():
    """同一参数两条互相矛盾的实测值 → 必须拒绝, 不允许按输入顺序后者覆盖前者."""
    spec = {"package": "gable_top", "params": SPEC["params"],
            "measurements": [{"name": "W", "value_mm": 45.0, "status": "MEASURED"},
                             {"name": "W", "value_mm": 46.0, "status": "MEASURED"}]}
    with pytest.raises(ARError, match="矛盾"):
        resolve_params(spec)
    same = {"package": "gable_top", "params": SPEC["params"],
            "measurements": [{"name": "W", "value_mm": 45.0, "status": "MEASURED"},
                             {"name": "W", "value_mm": 45.0, "status": "VERIFIED_SOURCE"}]}
    assert resolve_params(same)[0]["W"] == 45.0          # 两条一致的不算冲突


def test_cli_dispatch_uses_the_named_generator(tmp_path):
    """指定非 gable_top 模板 → IR 的模板 id 与面板都必须来自该族."""
    from typer.testing import CliRunner
    from photo_dieline.cli import app
    spec = tmp_path / "ok.json"
    spec.write_text(json.dumps({"package": "rsc_rsc", "params": class_defaults("rsc_rsc")}))
    r = CliRunner().invoke(app, ["build", "--spec", str(spec), "--photo", str(_photo(tmp_path)),
                                 "--out", str(tmp_path / "o")])
    assert r.exit_code == 0, r.output
    ir = json.loads((tmp_path / "o" / "geometry-ir.json").read_text())
    assert ir["package"]["template"]["id"] == "rsc_rsc"
    assert not {"slopeB", "finF", "flapF"} & {p["id"] for p in ir["panels"]}


def test_parametric_mode_without_photo_declares_size_source(tmp_path):
    """未提供照片的参数化模式: 输出必须写明尺寸来源, 并声明照片未参与尺寸恢复 (GPT R2-15)."""
    from typer.testing import CliRunner
    from photo_dieline.cli import app
    spec = tmp_path / "s.json"
    spec.write_text(json.dumps(SPEC))
    r = CliRunner().invoke(app, ["build", "--spec", str(spec), "--out", str(tmp_path / "o")])
    assert r.exit_code == 0, r.output
    report = json.loads((tmp_path / "o" / "qa-report.json").read_text())
    usage = report["input_usage"]
    assert usage["photo_provided"] is False
    assert usage["photo_used_for_dimensions"] is False
    assert "measurements" in usage["dimension_source"]
    assert _gate(report, "G01")["status"] == "FAIL"         # 无照片如实报告, 不冒充有照片证据


def test_photo_is_never_claimed_to_measure(env):
    """即便提供了照片, 报告也须声明: 当前尺寸全部来自 spec, 照片只作证据存档."""
    usage = env[3]["input_usage"]
    assert usage["photo_provided"] is True and usage["photo_used_for_dimensions"] is False


# ---- 正向挑战集 (GPT R2-4: 防止门禁从过松走向过严 — 合法变化必须仍然通过) ----
def _qa_raw(raw):
    ir = from_raw(raw)
    x0, y0, x1, y1 = svgx.net_bbox(ir)
    return run_qa(ir, svgx.render(ir, x1 - x0, y1 - y0), pdfx.build_pdf(ir, x1 - x0, y1 - y0))


def _shift_net(raw, dx, dy):
    for p in raw["panels"]:
        p["polygon_2d"] = [[x + dx, y + dy] for x, y in p["polygon_2d"]]
    for e in raw["edges"]:
        e["seg_2d"] = [[x + dx, y + dy] for x, y in e["seg_2d"]]
    return raw


def _insert_midpoints(raw):
    for p in raw["panels"]:
        pts = p["polygon_2d"]
        out = []
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            out += [a, [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]]
        p["polygon_2d"] = out
    return raw


def _rotate_polygon_start(raw):
    for p in raw["panels"]:
        pts = p["polygon_2d"]
        k = len(pts) // 2
        p["polygon_2d"] = pts[k:] + pts[:k]
    return raw


def _reverse_records(raw):
    raw["panels"].reverse()
    raw["edges"].reverse()
    return raw


def _legal_params(raw):
    raw.update(gable_top.build_ir({"W": 50.0, "D": 40.0, "Hb": 90.0, "Hr": 15.0, "Ef": 12.0, "glue_w": 15.0}))
    return raw


def _tiny_angle(raw):
    """一条折线的折向偏 0.1° — 远在闭合容差内的合法数值偏差."""
    e = next(x for x in raw["edges"] if x["id"] == "e_bk_sl")
    a = math.radians(0.1)
    x, y, z = e["fold"]["target_dir_3d"]
    e["fold"]["target_dir_3d"] = [x, y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)]
    return raw


def _flip_reference_and_labels(raw):
    """参考面翻到另一侧, M/V 同步翻转 — 物理折法完全不变的等价表示."""
    raw["package"]["template"]["mt_va_reference"] = "polygon_2d_cw"
    for e in raw["edges"]:
        e["fold"]["mt_va"] = {"MOUNTAIN": "VALLEY", "VALLEY": "MOUNTAIN"}[e["fold"]["mt_va"]]
    return raw


POSITIVE = [
    ("POS-01 整体平移", lambda raw: _shift_net(raw, 37.0, -11.0)),
    ("POS-03 合法参数域内改尺寸", _legal_params),
    ("POS-04 每条面板边插入共线中点", _insert_midpoints),
    ("POS-05 面板与折线记录重排", _reverse_records),
    ("POS-05b 多边形起始顶点轮换", _rotate_polygon_start),
    ("POS-07 容差内 0.1° 折向偏差", _tiny_angle),
    ("POS-08 参考面翻转且 M/V 同步翻转", _flip_reference_and_labels),
]


@pytest.mark.parametrize("label,fn", POSITIVE, ids=[p[0] for p in POSITIVE])
def test_legal_transformations_still_pass(label, fn):
    """合法变化必须仍然 VALIDATED, 且导出几何与变化前一致 (平移类除外, 只要求闭合与导出成立)."""
    raw = copy.deepcopy(gable_top.build_ir(SPEC["params"]))
    fn(raw)
    report = _qa_raw(raw)
    failed = [g["id"] for g in report["gates"] if g["id"] != "G01" and g["status"] != "PASS"]
    assert not failed, f"{label} 被误杀: {failed} — " + "; ".join(
        g["detail"] for g in report["gates"] if g["status"] == "FAIL")
    assert report["status"] == "VALIDATED", label


def test_positive_set_keeps_folded_geometry():
    """平移 / 插中点 / 重排 / 翻参考面 都不改变折叠终态: 逐面板逐顶点 (按 net 坐标对齐) 世界坐标一致."""
    base = copy.deepcopy(gable_top.build_ir(SPEC["params"]))
    w0 = fold_all(from_raw(base))
    ref = {pid: np.asarray(v) for pid, v in w0.items()}
    for fn in (_insert_midpoints, _reverse_records, _flip_reference_and_labels):
        raw = copy.deepcopy(gable_top.build_ir(SPEC["params"]))
        fn(raw)
        ir = from_raw(raw)
        w = fold_all(ir)
        for p in ir.panels:
            pts = np.asarray(p["polygon_2d"], float)
            src = np.asarray(next(q for q in base["panels"] if q["id"] == p["id"])["polygon_2d"], float)
            for k, q in enumerate(pts):
                if any(np.allclose(q, s) for s in src):          # 原有顶点仍在 → 折叠后位置必须一致
                    j = int(np.argmin(np.linalg.norm(src - q, axis=1)))
                    assert np.allclose(w[p["id"]][k], ref[p["id"]][j], atol=1e-9), (fn.__name__, p["id"], k)
