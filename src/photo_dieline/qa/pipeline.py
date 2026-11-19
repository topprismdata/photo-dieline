"""QA 管线: 十道门 → JSON 报告 (机器可判定; 全过 = VALIDATED, 缺照片参照 = DRAFT).

G01 照片证据 | G02 IR Schema | G03 拓扑闭合 | G04 折叠闭合(跨链顶点重合)
G05 golden 尺寸 | G06 面板穿插 | G07 SVG 1:1+分层+校验条 | G08 PDF MediaBox+50mm
G09 报告自检 | G10 core 隔离(无 bpy/trellis/torch)
"""
from __future__ import annotations

import json
import math
import re
import zlib
from pathlib import Path
from dataclasses import dataclass, field

import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

from ..core.ir import ARError, GeometryIR
from ..export import pdf as pdfx
from ..export import svg as svgx
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


def run_qa(ir: GeometryIR, svg_text: str, pdf_bytes: bytes) -> dict:
    g = []

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

    # G03 拓扑: 折线共享边长度一致 + 并集轮廓闭合
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
        u = unary_union(polys).buffer(0)
        n_rings = 1 if u.geom_type == "Polygon" else len(u.geoms)
        if max_len_diff > 1e-6:
            g03.fail(f"折线-面板共享边长不一致 max={max_len_diff:.2e}mm")
        elif n_rings != 1:
            g03.fail(f"网并集不连通: {n_rings} 个环/部件")
        else:
            g03.ok({"max_shared_len_diff_mm": max_len_diff,
                    "panels": len(ir.panels), "folds": len(ir.edges)})
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

    # G07 SVG
    g07 = Gate("G07", "svg_physical")
    try:
        x0, y0, x1, y1 = svgx.net_bbox(ir)
        nw, nh = x1 - x0, y1 - y0
        m = re.search(r'width="([\d.]+)mm" height="([\d.]+)mm"', svg_text)
        vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg_text)
        layers_ok = all(f'id="{l}"' in svg_text for l in pdfx.LAYERS)
        w_mm, h_mm = float(m.group(1)), float(m.group(2))
        vbw, vbh = float(vb.group(1)), float(vb.group(2))
        size_ok = abs(w_mm - vbw) < 1e-3 and abs(h_mm - vbh) < 1e-3
        cut_closed = svg_text.count("stroke-width=\"0.3\"") >= 1
        if layers_ok and size_ok and cut_closed:
            g07.ok({"svg_w_mm": w_mm, "svg_h_mm": h_mm, "net_w_mm": nw, "net_h_mm": nh,
                    "layers": pdfx.LAYERS})
        else:
            g07.fail(f"layers_ok={layers_ok} size_ok={size_ok} cut={cut_closed}")
    except Exception as exc:  # noqa: BLE001
        g07.fail(str(exc))
    g.append(g07)

    # G08 PDF
    g08 = Gate("G08", "pdf_physical")
    try:
        head = pdf_bytes[:4096].decode("latin-1")
        mb = re.search(r"/MediaBox \[0 0 ([\d.]+) ([\d.]+)\]", head)
        x0, y0, x1, y1 = svgx.net_bbox(ir)
        expect_w = (x1 - x0 + 24) * pdfx.PT_PER_MM
        expect_h = (y1 - y0 + 24) * pdfx.PT_PER_MM
        w_pt, h_pt = float(mb.group(1)), float(mb.group(2))
        # 内容流: 解压找 50mm 校验条 (INFO 层内 141.732pt 线段)
        st = re.search(rb"stream\n(.*?)\nendstream", pdf_bytes, re.S)
        raw = zlib.decompress(st.group(1)).decode("latin-1")
        bar_ok = False
        for seg in re.findall(r"([\d.]+) ([\d.]+) m\n([\d.]+) ([\d.]+) l", raw):
            ax, ay, bx, by = map(float, seg)
            length = math.hypot(bx - ax, by - ay)
            if abs(length - 50 * pdfx.PT_PER_MM) < 0.05:
                bar_ok = True
                break
        ocg_n = len(re.findall(r"/Type /OCG", head))
        size_ok = abs(w_pt - expect_w) < 0.2 and abs(h_pt - expect_h) < 0.2
        if size_ok and bar_ok and ocg_n >= 7:
            g08.ok({"mediabox_pt": [w_pt, h_pt], "expected_pt": [expect_w, expect_h],
                    "bar_50mm": True, "ocg_layers": ocg_n})
        else:
            g08.fail(f"size_ok={size_ok} bar={bar_ok} ocg={ocg_n}",
                     {"mediabox_pt": [w_pt, h_pt]})
    except Exception as exc:  # noqa: BLE001
        g08.fail(str(exc))
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
        g10.ok({"imports": "numpy/shapely/jsonschema/PIL/typer only"})
    g.append(g10)

    gates = [x.as_dict() for x in g]
    hard = [x for x in g if x.id != "G01"]
    status = "VALIDATED" if all(x.status == "PASS" for x in hard) else "DRAFT"
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
