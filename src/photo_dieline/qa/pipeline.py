"""QA 管线: 十道门 → JSON 报告 (机器可判定; 硬门全过 = VALIDATED; G01 照片门不计入整体状态 —
batch 模板验证没有照片, 单独报告)。

G01 照片证据 | G02 IR Schema | G03 拓扑闭合 | G04 折叠闭合(跨链顶点重合)
G05 golden 尺寸 | G06 面板穿插 | G07 SVG 1:1+分层+在页内+校验条 | G08 PDF 独立解析+图层挂载+在页内+校验条
G09 报告自检 (门齐全/状态合法/整体状态与各门一致) | G10 core 隔离(无 bpy/trellis/torch)
"""
from __future__ import annotations

import math
import re
from pathlib import Path
from dataclasses import dataclass, field

import numpy as np
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from ..core.ir import MIN_PHOTO_PX, GeometryIR
from ..export import layout as lay
from ..export import pdf as pdfx
from ..folding.engine import fold_all
from ..parametric import base as templates
TOL_MM = 0.2          # 折叠闭合残差门
GOLDEN_TOL_MM = 0.5   # golden 尺寸门
ALLOWED_OVERLAP = {   # 模板契约: 允许叠层 (真实工艺)
    frozenset({"flapF", "flapB"}), frozenset({"flapL", "flapR"}),
    frozenset({"glue", "front"}), frozenset({"finB", "finF"}),
}


@dataclass
class Gate:
    id: str
    name: str
    status: str = "FAIL"
    metrics: dict = field(default_factory=dict)
    detail: str = ""

    def ok(self, metrics: dict | None = None, detail: str = ""):
        self.status, self.metrics, self.detail = "PASS", metrics or {}, detail
        return self

    def fail(self, detail: str, metrics: dict | None = None):
        self.status, self.detail = "FAIL", detail
        self.metrics = metrics or {}
        return self

    def as_dict(self):
        return {"id": self.id, "name": self.name, "status": self.status,
                "metrics": self.metrics, "detail": self.detail}


def _vdist(a, b) -> float:
    return float(np.linalg.norm(np.asarray(a) - np.asarray(b)))


def _vertex(world, pid: str, idx: int):
    return world[pid][idx]


def _poly_pts(ir: GeometryIR, pid: str):
    return ir.panel(pid)["polygon_2d"]


def _svg_geometry(svg_text: str) -> dict:
    """独立解析 SVG (XML) → 画布尺寸、各图层形状坐标、变换属性。QA 只信解析结果。"""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(svg_text)
    ns = "{http://www.w3.org/2000/svg}"
    W = float(root.get("width").removesuffix("mm"))
    H = float(root.get("height").removesuffix("mm"))
    vb = [float(v) for v in root.get("viewBox", "").split()]
    layers: dict[str, dict] = {}
    for grp in root.iter(ns + "g"):
        shapes = []
        for el in grp:
            tag = el.tag.replace(ns, "")
            if tag in ("polygon", "polyline"):
                v = [float(x) for x in el.get("points", "").replace(",", " ").split()]
                shapes.append((list(zip(v[0::2], v[1::2])), tag == "polygon"))
            elif tag == "line":
                shapes.append(([(float(el.get("x1")), float(el.get("y1"))),
                                (float(el.get("x2")), float(el.get("y2")))], False))
        layers[grp.get("id")] = {"shapes": shapes,
                                 "text": "".join(t.text or "" for t in grp.iter(ns + "text"))}
    transforms = [el.get("transform") for el in root.iter() if el.get("transform")]
    return {"W": W, "H": H, "viewBox": vb, "layers": layers, "transforms": transforms}


def _pdf_geometry(pdf_bytes: bytes) -> dict:
    """独立解析 PDF (pypdf 严格模式) → MediaBox、图层属性表、内容流图层块。语法错误直接抛出。"""
    import io
    import pypdf
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes), strict=True)
    if len(reader.pages) != 1:
        raise ValueError(f"页数 {len(reader.pages)} ≠ 1")
    page = reader.pages[0]
    box = page.mediabox
    props = page["/Resources"].get("/Properties")
    ocg = {str(key): str(props[key].get("/Name")) for key in props.keys()}
    raw = page.get_contents().get_data().decode("latin-1")
    blocks = [(m.group(1), m.group(2), m.group(3))
              for m in re.finditer(r"/(\w+) (/P\d+) BDC\n(.*?)\nEMC", raw, re.S)]
    return {"W": float(box.width), "H": float(box.height), "ocg": ocg, "blocks": blocks, "raw": raw}


def _path_pts(ops: str) -> list[tuple[float, float]]:
    """内容流片段里的路径顶点 (pt): `x y m` / `x y l`。"""
    return [(float(x), float(y)) for x, y in re.findall(r"(-?[\d.]+) (-?[\d.]+) [ml]\b", ops)]


def run_qa(ir: GeometryIR, svg_text: str, pdf_bytes: bytes) -> dict:
    g = []

    # G01 照片证据门: 照片在册且分辨率达标 (batch 模板验证无照片 → FAIL, 不计入整体状态)
    g01 = Gate("G01", "photo_evidence")
    ph = ir.package.get("photo") or {}
    if ph.get("sha256") and min(ph.get("width_px", 0), ph.get("height_px", 0)) >= MIN_PHOTO_PX:
        g01.ok({"width_px": ph.get("width_px"), "height_px": ph.get("height_px"), "sha256": ph.get("sha256")})
    else:
        g01.fail("无照片证据或分辨率不足")
    g.append(g01)
    # G02 IR Schema (已在 build 校验, 双重保险: 存在五顶层)
    g02 = Gate("G02", "ir_schema")
    try:
        from ..core.ir import validate_dict
        validate_dict(ir.raw)
        missing = []
        try:
            mod = templates.get(ir.package["template"]["id"])
            missing = [k for k in mod.PARAM_ORDER if k not in ir.package["params"]]
        except KeyError:
            missing = ["<未注册模板>"]
        if missing:
            g02.fail(f"模板参数缺失: {missing}")
        else:
            g02.ok({"top_level": ["meta", "package", "panels", "edges", "features"],
                    "template": ir.package["template"]["id"]})
    except Exception as exc:  # noqa: BLE001
        g02.fail(str(exc))
    g.append(g02)

    # G03 拓扑: 折线共享边长度一致 + 并集为单部件 + 面板自有效 + 展开图面板两两不重叠 + 裁切缝不切穿结构
    g03 = Gate("G03", "topology")
    try:
        max_len_diff = 0.0
        for e in ir.edges:
            (a, b) = e.seg_2d
            fold_len = math.dist(a, b)
            plen = _seg_len_in_panel(_poly_pts(ir, e.parent), a, b)
            clen = _seg_len_in_panel(_poly_pts(ir, e.child), a, b)
            max_len_diff = max(max_len_diff, abs(fold_len - plen), abs(fold_len - clen))
        polys = [Polygon(p["polygon_2d"]) for p in ir.panels]
        invalid = [ir.panels[i]["id"] for i, pg in enumerate(polys) if not pg.is_valid]
        polys_clean = [pg.buffer(0) for pg in polys]
        u = unary_union(polys_clean).buffer(0)
        n_parts = 1 if u.geom_type == "Polygon" else len(u.geoms)
        # 展开图里一块材料只能属于一块面板: 两两交集面积须为 0
        overlaps = []
        for i in range(len(polys_clean)):
            for j in range(i + 1, len(polys_clean)):
                area_ij = polys_clean[i].intersection(polys_clean[j]).area
                if area_ij > 1e-6:
                    overlaps.append((f"{ir.panels[i]['id']}|{ir.panels[j]['id']}", round(area_ij, 3)))
        # 裁切缝落点: 并集边界之外的非折线面板边 (内部裁切缝) 不得与折线共线重叠, 不得落入任何面板内部
        bnd = u.boundary
        fold_lines = [LineString([e.seg_2d[0], e.seg_2d[1]]) for e in ir.edges]
        shrunk = [pg.buffer(-1e-6) for pg in polys_clean]
        cut_on_fold = 0.0
        cut_in_panel = 0.0
        for a, b in lay.cut_segments(ir):
            seg = LineString([a, b])
            if bnd.distance(seg) < 1e-6:
                continue   # 落在并集边界上 = 正常外轮廓
            cut_on_fold = max(cut_on_fold, max((seg.intersection(fl).length for fl in fold_lines), default=0.0))
            cut_in_panel = max(cut_in_panel, max((seg.intersection(sp).length for sp in shrunk), default=0.0))
        metrics = {"max_shared_len_diff_mm": max_len_diff, "panels": len(ir.panels), "folds": len(ir.edges),
                   "n_overlap_pairs": len(overlaps), "cut_on_fold_mm": round(cut_on_fold, 3),
                   "cut_in_panel_mm": round(cut_in_panel, 3)}
        if invalid:
            g03.fail(f"面板多边形自交: {invalid}", metrics)
        elif max_len_diff > 1e-6:
            g03.fail(f"折线-面板共享边长不一致 max={max_len_diff:.2e}mm", metrics)
        elif n_parts != 1:
            g03.fail(f"网并集不连通: {n_parts} 个部件", metrics)
        elif overlaps:
            g03.fail(f"展开图面板重叠 {len(overlaps)} 对 (面板对, mm²): {overlaps[:4]}", metrics)
        elif cut_on_fold > 1e-6 or cut_in_panel > 1e-6:
            g03.fail(f"裁切缝切穿结构: 与折线重叠 {cut_on_fold:.1f}mm, 落入面板内部 {cut_in_panel:.1f}mm", metrics)
        else:
            g03.ok(metrics)
    except Exception as exc:  # noqa: BLE001
        g03.fail(str(exc))
    g.append(g03)

    # G04 折叠闭合 (跨链顶点重合)
    g04 = Gate("G04", "fold_closure")
    try:
        world = fold_all(ir)
        mod = templates.get(ir.package["template"]["id"])
        residual = {k: round(float(v), 6) for k, v in mod.closure_checks(ir, world).items()}
        worst = max(residual.values())
        if worst <= TOL_MM:
            g04.ok({"worst_residual_mm": worst, **residual})
        else:
            g04.fail(f"最大闭合残差 {worst:.3f}mm > {TOL_MM}mm", residual)
    except Exception as exc:  # noqa: BLE001
        g04.fail(str(exc))
    g.append(g04)

    # G05 golden 尺寸 (解析盒 vs 折叠结果 bbox; 只量封闭体: wall+slope, 排除开板/鳍耳)
    g05 = Gate("G05", "golden_dimensions")
    try:
        world = fold_all(ir)
        mod = templates.get(ir.package["template"]["id"])
        roles = {pp["id"]: pp["role"] for pp in ir.panels}
        solid = [v for pid, v in world.items() if roles[pid] in mod.solid_roles()]
        allpts = np.vstack(solid)
        dims = {
            "W": float(allpts[:, 0].max() - allpts[:, 0].min()),
            "D": float(allpts[:, 1].max() - allpts[:, 1].min()),
            "H": float(allpts[:, 2].max() - allpts[:, 2].min()),
        }
        ana = mod.analytic_bbox(ir.package["params"])
        diffs = {k: abs(dims[k] - ana[k]) for k in ("W", "D", "H")}
        worst = max(diffs.values())
        if worst <= GOLDEN_TOL_MM:
            g05.ok({"dims_mm": dims, "expected_mm": ana, "worst_diff_mm": worst})
        else:
            g05.fail(f"bbox 偏差 {worst:.3f}mm > {GOLDEN_TOL_MM}mm",
                     {"dims_mm": dims, "expected_mm": ana})
    except Exception as exc:  # noqa: BLE001
        g05.fail(str(exc))
    g.append(g05)

    # G06 穿插 (非相邻面板 3D 平面投影相交检测)
    g06 = Gate("G06", "no_interpenetration")
    try:
        world = fold_all(ir)
        mod = templates.get(ir.package["template"]["id"])
        allowed = mod.allowed_overlap()
        roles = {pp["id"]: pp["role"] for pp in ir.panels}
        bad = []
        ids = list(world)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = ids[i], ids[j]
                key = frozenset({a, b})
                if key in allowed or key in ALLOWED_OVERLAP:
                    continue
                if _panels_share_fold(ir, a, b):
                    continue
                if roles.get(a) == "flap" and roles.get(b) == "flap":
                    continue  # 底板层间接触契约
                if _intersect3d(world[a], world[b]):
                    bad.append((a, b))
        if bad:
            g06.fail(f"穿插对: {bad}")
        else:
            g06.ok({"checked_pairs": len(ids) * (len(ids) - 1) // 2})
    except Exception as exc:  # noqa: BLE001
        g06.fail(str(exc))
    g.append(g06)

    # 图层内容对账基准: 折线按语义计数, 粘口按角色计数
    n_mtn = sum(1 for e in ir.edges if e.mt_va == "MOUNTAIN")
    n_val = sum(1 for e in ir.edges if e.mt_va == "VALLEY")
    n_glue = sum(1 for p in ir.panels if p["role"] == "glue")
    need_layers = {"CUT", "BLEED", "REGISTRATION", "INFO"}
    if n_mtn:
        need_layers.add("CREASE-MOUNTAIN")
    if n_val:
        need_layers.add("CREASE-VALLEY")
    if n_glue:
        need_layers.add("GLUE")
    x0, y0, x1, y1 = lay.net_bbox(ir)
    nw, nh = x1 - x0, y1 - y0

    # G07 SVG: 1:1 物理页 + 分层内容 + 全部几何在页内 + 外轮廓落位 + 50mm 校验条 (独立 XML 解析)
    g07 = Gate("G07", "svg_physical")
    try:
        geo = _svg_geometry(svg_text)
        W, H, vb = geo["W"], geo["H"], geo["viewBox"]
        size_ok = (len(vb) == 4 and abs(vb[0]) < 1e-6 and abs(vb[1]) < 1e-6
                   and abs(W - vb[2]) < 1e-3 and abs(H - vb[3]) < 1e-3
                   and abs(W - (nw + 2 * lay.MARGIN)) < 1e-3 and abs(H - (nh + 2 * lay.MARGIN)) < 1e-3)
        scale_ok = not geo["transforms"]
        L = geo["layers"]
        layers_ok = all(k in L for k in pdfx.LAYERS)
        n_closed = lambda k: sum(1 for _pts, is_poly in L[k]["shapes"] if is_poly)  # noqa: E731
        n_open = lambda k: sum(1 for _pts, is_poly in L[k]["shapes"] if not is_poly)  # noqa: E731
        content_ok = (layers_ok and n_closed("CUT") >= 1 and n_open("CREASE-MOUNTAIN") == n_mtn
                      and n_open("CREASE-VALLEY") == n_val and n_closed("GLUE") == n_glue
                      and n_closed("BLEED") >= 1 and n_open("REGISTRATION") == 8)
        xs, ys = [], []
        for k in pdfx.LAYERS:
            if k in L:
                for pts, _is_poly in L[k]["shapes"]:
                    xs += [p[0] for p in pts]
                    ys += [p[1] for p in pts]
        out_of_page = sum(1 for x, y in zip(xs, ys)
                          if x < -1e-3 or y < -1e-3 or x > W + 1e-3 or y > H + 1e-3)
        in_page_ok = bool(xs) and out_of_page == 0
        # CUT 闭合外轮廓的包围盒 = 净图平移到页边距 (证明 1:1 且未平移出页); SVG y 向下
        cx = [p[0] for pts, is_poly in L["CUT"]["shapes"] if is_poly for p in pts]
        cy = [p[1] for pts, is_poly in L["CUT"]["shapes"] if is_poly for p in pts]
        place_ok = (bool(cx) and abs(min(cx) - lay.MARGIN) < 1e-3 and abs(max(cx) - (lay.MARGIN + nw)) < 1e-3
                    and abs(min(cy) - (H - lay.MARGIN - nh)) < 1e-3 and abs(max(cy) - (H - lay.MARGIN)) < 1e-3)
        bars = [math.hypot(b[0] - a[0], b[1] - a[1])
                for pts, is_poly in L["INFO"]["shapes"] if not is_poly and len(pts) == 2 for a, b in [pts]]
        bar_ok = any(abs(b - lay.CHECK_BAR_MM) < 0.01 for b in bars) and "CHECK BAR" in L["INFO"]["text"]
        checks = {"size_ok": size_ok, "scale_ok": scale_ok, "layers_ok": layers_ok, "content_ok": content_ok,
                  "in_page_ok": in_page_ok, "place_ok": place_ok, "bar_ok": bar_ok}
        if all(checks.values()):
            g07.ok({"svg_w_mm": W, "svg_h_mm": H, "net_w_mm": nw, "net_h_mm": nh, "layers": pdfx.LAYERS,
                    "n_points": len(xs), "out_of_page_points": out_of_page, "bar_mm": lay.CHECK_BAR_MM})
        else:
            g07.fail("未通过: " + ", ".join(k for k, v in checks.items() if not v),
                     {"svg_w_mm": W, "svg_h_mm": H, "out_of_page_points": out_of_page})
    except Exception as exc:  # noqa: BLE001
        g07.fail(f"SVG 解析失败: {exc}")
    g.append(g07)

    # G08 PDF: 独立解析器 (pypdf 严格模式) 打开 + MediaBox + 图层挂载 + 全部几何在页内 + 50mm 校验条
    g08 = Gate("G08", "pdf_physical")
    try:
        expect_w = (nw + 2 * lay.MARGIN) * pdfx.PT_PER_MM
        expect_h = (nh + 2 * lay.MARGIN) * pdfx.PT_PER_MM
        geo = _pdf_geometry(pdf_bytes)
        W, H = geo["W"], geo["H"]
        size_ok = abs(W - expect_w) < 0.05 and abs(H - expect_h) < 0.05
        keys = [f"/P{i}" for i in range(len(pdfx.LAYERS))]
        ocg_ok = list(geo["ocg"].keys()) == keys and [geo["ocg"][k] for k in keys] == list(pdfx.LAYERS)
        scale_ok = not re.search(r"\bcm\b", geo["raw"])
        tags_ok = all(tag == "OC" and prop in geo["ocg"] for tag, prop, _ops in geo["blocks"])
        used = [prop for _tag, prop, _ops in geo["blocks"]]
        mount_ok = bool(used) and len(used) == len(set(used))
        have = {pdfx.LAYERS[int(prop[2:])] for prop in used if prop in geo["ocg"]}
        xs, ys = [], []
        for _tag, _prop, ops in geo["blocks"]:
            for x, y in _path_pts(ops):
                xs.append(x)
                ys.append(y)
        out_of_page = sum(1 for x, y in zip(xs, ys)
                          if x < -0.05 or y < -0.05 or x > W + 0.05 or y > H + 0.05)
        in_page_ok = bool(xs) and out_of_page == 0
        info_prop = f"/P{pdfx.LAYERS.index('INFO')}"
        bar_ok = False
        for _tag, prop, ops in geo["blocks"]:
            if prop == info_prop:
                pts = _path_pts(ops)
                bar_ok = any(abs(math.hypot(b[0] - a[0], b[1] - a[1]) - lay.CHECK_BAR_MM * pdfx.PT_PER_MM) < 0.05
                             for a, b in zip(pts[0::2], pts[1::2]))
        checks = {"size_ok": size_ok, "ocg_ok": ocg_ok, "scale_ok": scale_ok, "tags_ok": tags_ok,
                  "mount_ok": mount_ok, "layers_ok": need_layers <= have, "in_page_ok": in_page_ok, "bar_ok": bar_ok}
        if all(checks.values()):
            g08.ok({"mediabox_pt": [W, H], "expected_pt": [expect_w, expect_h], "bar_50mm": True,
                    "ocg_layers": len(keys), "mounted_layers": sorted(have), "n_points": len(xs),
                    "out_of_page_points": out_of_page, "parser": "pypdf"})
        else:
            g08.fail("未通过: " + ", ".join(k for k, v in checks.items() if not v),
                     {"mediabox_pt": [W, H], "out_of_page_points": out_of_page})
    except Exception as exc:  # noqa: BLE001
        g08.fail(f"PDF 解析失败: {exc}")
    g.append(g08)

    # G10 core 隔离
    g10 = Gate("G10", "core_isolation")
    banned = []
    root = Path(__file__).resolve().parents[2]
    for py in root.rglob("*.py"):
        src = py.read_text(errors="replace")
        for mod in ("bpy", "trellis", "torch", "blenderproc"):
            if re.search(rf"^\s*(import {mod}|from {mod})", src, re.M):
                banned.append(f"{py.name}:{mod}")
    if banned:
        g10.fail(f"core 不应硬依赖: {banned}")
    else:
        g10.ok({"imports": "numpy/shapely/jsonschema/PIL/typer/pypdf only"})
    g.append(g10)

    # G09 报告自检: 其余九道门齐全、状态合法、整体状态与各门一致
    g09 = Gate("G09", "report_selfcheck")
    expect_ids = [f"G{i:02d}" for i in range(1, 11) if i != 9]
    ids = [x.id for x in g]
    hard = [x for x in g if x.id != "G01"]
    status = "VALIDATED" if all(x.status == "PASS" for x in hard) else "DRAFT"
    # 每道门状态合法, 且每道 FAIL 必须带说明 (无说明的 FAIL 等于没检查)
    explained = all(x.status in ("PASS", "FAIL") and (x.status == "PASS" or bool(x.detail)) for x in g)
    if ids == expect_ids and explained:
        g09.ok({"gates": ids + ["G09"], "n_gates": 10, "status": status})
    else:
        g09.fail(f"门不齐或 FAIL 无说明: ids={ids}")
    g.append(g09)

    gates = sorted((x.as_dict() for x in g), key=lambda d: d["id"])
    return {
        "qa_version": "0.1",
        "status": status,
        "package": {"type": ir.package["type"],
                    "template": ir.package["template"],
                    "params": ir.package["params"],
                    "params_evidence": ir.package.get("params_evidence", {})},
        "photo": ir.package["photo"],
        "gates": gates,
        "tolerances": {"fold_closure_mm": TOL_MM, "golden_mm": GOLDEN_TOL_MM},
    }


def _seg_len_in_panel(poly, a, b) -> float:
    pts = [np.array(p, float) for p in poly]
    ia = int(np.argmin([np.linalg.norm(p - np.array(a)) for p in pts]))
    ib = int(np.argmin([np.linalg.norm(p - np.array(b)) for p in pts]))
    return float(np.linalg.norm(pts[ia] - pts[ib]))


def _panels_share_fold(ir: GeometryIR, a: str, b: str) -> bool:
    for e in ir.edges:
        if {e.parent, e.child} == {a, b}:
            return True
    return False


def _intersect3d(pa: np.ndarray, pb: np.ndarray) -> bool:
    """保守近似: 两面板三角形扇在公共平面投影相交 → 视为穿插候选."""
    na = np.cross(pa[1] - pa[0], pa[2] - pa[0])
    nb = np.cross(pb[1] - pb[0], pb[2] - pb[0])
    na, nb = na / (np.linalg.norm(na) + 1e-12), nb / (np.linalg.norm(nb) + 1e-12)
    if abs(float(na @ nb)) > 0.999:  #近平行面: 距离检查
        d = float(np.dot(pa[0] - pb[0], na))
        return abs(d) < 1e-6 and _proj_overlap(pa, pb, na)
    # 取 b 投到 a 平面
    n = na
    dist = np.dot(pb - pa[0], n)
    if (dist > 0).all() or (dist < 0).all():
        return False  # 完全同侧 → 无穿插
    return _proj_overlap(pa, pb, n)


def _proj_overlap(pa: np.ndarray, pb: np.ndarray, n: np.ndarray) -> bool:
    def frame(nvec):
        t = np.array([1.0, 0, 0]) if abs(nvec[0]) < 0.9 else np.array([0, 1.0, 0])
        u = np.cross(nvec, t)
        u /= np.linalg.norm(u)
        v = np.cross(nvec, u)
        return u, v

    u, v = frame(n)

    def poly2(p):
        return [(float(q @ u), float(q @ v)) for q in p]

    A = Polygon(poly2(pa)).buffer(0)
    B = Polygon(poly2(pb)).buffer(0)
    return A.intersects(B) and A.intersection(B).area > 1e-6
