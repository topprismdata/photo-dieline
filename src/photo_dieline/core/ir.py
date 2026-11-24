"""Geometry IR V0.1: 加载/校验/单位纪律 (浮点 mm, 模块间禁止无单位坐标)."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema
from PIL import Image

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "geometry-ir.schema.json"

MIN_PHOTO_PX = 1000  # 照片证据门: 最短边像素下限
PHOTO_FORMATS = ("JPEG", "PNG")  # 照片证据门: 接受的编码格式
MEASURED_STATUSES = ("MEASURED", "VERIFIED_SOURCE")  # 可覆盖几何参数的证据等级 (ADR-003)
MEASURED_TOL_MM = 0.5  # 实测值与最终几何参数的允许偏差 (DESIGN §5: MVP ≤0.5mm)


class ARError(ValueError):
    """IR 构造/校验错误."""


@dataclass
class PhotoEvidence:
    path: str
    sha256: str
    width_px: int
    height_px: int


def photo_evidence(path: str | Path) -> PhotoEvidence:
    """读取照片 → 像素门 + 哈希存证 (G01). 仅读元数据, 不参与几何."""
    p = Path(path)
    if not p.is_file():
        raise ARError(f"照片不存在: {p}")
    with Image.open(p) as im:
        w, h = im.size
        fmt = im.format
    if fmt not in PHOTO_FORMATS:
        raise ARError(f"照片格式须为 {'/'.join(PHOTO_FORMATS)}, 实为 {fmt}: {p}")
    if min(w, h) < MIN_PHOTO_PX:
        raise ARError(f"照片分辨率不足: {w}x{h} < {MIN_PHOTO_PX}px 最短边")
    return PhotoEvidence(str(p), hashlib.sha256(p.read_bytes()).hexdigest(), w, h)


@dataclass
class FoldEdge:
    id: str
    seg_2d: tuple[tuple[float, float], tuple[float, float]]
    mt_va: str
    parent: str
    child: str
    target_angle_deg: float | None = None
    target_dir_3d: tuple[float, float, float] | None = None


@dataclass
class GeometryIR:
    meta: dict
    package: dict
    panels: list[dict]
    edges: list[FoldEdge]
    features: list[dict]
    raw: dict = field(repr=False, default_factory=dict)

    # ---- 便捷查询 ----
    def panel(self, pid: str) -> dict:
        for p in self.panels:
            if p["id"] == pid:
                return p
        raise ARError(f"面板不存在: {pid}")

    def folds_from(self, pid: str) -> list[FoldEdge]:
        return [e for e in self.edges if e.fold.parent == pid]

    def param(self, key: str) -> float:
        return float(self.package["params"][key])


def validate_dict(ir: dict, schema_path: Path = SCHEMA_PATH) -> None:
    schema = json.loads(schema_path.read_text())
    jsonschema.validate(ir, schema)
    try:  # 模板参数语义 (负值/非法组合): 注册表分发, 未注册类跳过由 G02 拦
        from ..parametric import base as _templates
        mod = _templates.get(ir["package"]["template"]["id"])
        hook = getattr(mod, "validate_params", None)
        if hook:
            hook(ir["package"]["params"])
    except jsonschema.ValidationError:
        raise
    except KeyError:
        pass


def class_module(cls_id: str):
    """按类 ID 取模板模块; 未注册 → ARError (绝不静默回退到任何默认模板)."""
    from ..parametric import base as _templates
    try:
        return _templates.get(cls_id)
    except KeyError as exc:
        raise ARError(str(exc.args[0] if exc.args else exc)) from exc


def class_defaults(cls_id: str) -> dict:
    """模板类的完整默认参数 (家族模块按 class_params(cls_id) 派生具体类)."""
    mod = class_module(cls_id)
    params = dict(mod.DEFAULTS)
    if hasattr(mod, "class_params"):
        params.update(mod.class_params(cls_id))
    return params


def resolve_params(spec: dict) -> tuple[dict, dict]:
    """spec → 几何参数 (浮点 mm)。

    实测优先 (ADR-003 三条铁律之二): MEASURED / VERIFIED_SOURCE 的 value_mm 覆盖同名参数,
    模型或默认值永远不能覆盖实测。其余参数: spec.params > 模板类默认值。
    返回 (params, overrides); overrides = {name: {from, to, status}} 记录被实测值改写的项。
    """
    if not spec.get("package"):
        raise ARError("spec 缺少 package (包装类型/模板类 ID)")
    params = {k: float(v) for k, v in class_defaults(spec["package"]).items()}
    given = spec.get("params", {})
    unknown = sorted(k for k in given if k not in params)
    if unknown:
        raise ARError(f"spec.params 含模板 {spec['package']} 未定义的参数: {unknown}")
    params.update({k: float(v) for k, v in given.items()})
    overrides: dict = {}
    measured: dict = {}   # 同一参数的多条实测/可信来源值必须一致
    for m in spec.get("measurements", []):
        name, st = m.get("name"), str(m.get("status", "")).upper()
        if name not in params:
            raise ARError(f"measurements 含模板 {spec['package']} 未定义的参数: {name!r}")
        if st in MEASURED_STATUSES:
            v = float(m["value_mm"])
            if name in measured and abs(measured[name] - v) > 1e-9:
                raise ARError(f"参数 {name} 的实测值互相矛盾 ({measured[name]:g}mm 与 {v:g}mm): "
                              f"须先解决冲突, 不按输入顺序覆盖")
            measured[name] = v
            if abs(v - params[name]) > 1e-9:
                overrides[name] = {"from": params[name], "to": v, "status": st}
                params[name] = v
    return params, overrides


def _attach_evidence(ir: dict, spec: dict) -> None:
    """把 spec 的证据等级写进 IR, 并执行"实测优先"的入口检查 (原地修改)."""
    # 尺寸证据状态记录: spec.measurements[{name,value_mm,status,source?}]
    status_map = {m["name"]: m["status"].upper() for m in spec.get("measurements", [])}
    ir["package"]["params_evidence"] = {
        k: status_map.get(k, "DEFAULTED") for k in ir["package"]["params"]
    }
    for k, st in ir["package"]["params_evidence"].items():
        if st not in {"MEASURED", "VERIFIED_SOURCE", "DERIVED", "INFERRED", "DEFAULTED"}:
            raise ARError(f"非法证据状态 {k}={st}")
    # 实测优先的执行点: 实测/可信来源值必须就是最终几何参数 (否则这份 IR 冒充实测)
    for m in spec.get("measurements", []):
        if m.get("name") in ir["package"]["params"] and str(m.get("status", "")).upper() in MEASURED_STATUSES:
            diff = abs(float(m["value_mm"]) - float(ir["package"]["params"][m["name"]]))
            if diff > MEASURED_TOL_MM:
                raise ARError(
                    f"实测值与几何参数不一致: {m['name']} 几何={ir['package']['params'][m['name']]:g}mm "
                    f"实测={float(m['value_mm']):g}mm (|Δ|={diff:.3f}mm > {MEASURED_TOL_MM}mm); "
                    f"几何须由 resolve_params(spec) 生成")
    validate_dict(ir)


def _to_ir(ir: dict) -> GeometryIR:
    edges = [FoldEdge(
        id=e["id"],
        seg_2d=((e["seg_2d"][0][0], e["seg_2d"][0][1]), (e["seg_2d"][1][0], e["seg_2d"][1][1])),
        mt_va=e["fold"]["mt_va"],
        parent=e["fold"]["parent"],
        child=e["fold"]["child"],
        target_angle_deg=e["fold"].get("target_angle_deg"),
        target_dir_3d=tuple(e["fold"]["target_dir_3d"]) if e["fold"].get("target_dir_3d") else None,
    ) for e in ir["edges"]]
    return GeometryIR(ir["meta"], ir["package"], ir["panels"], edges, ir["features"], ir)


def build(spec: dict, photo_path: str | Path, template_ir: dict) -> GeometryIR:
    """spec(用户输入+证据) + 照片证据 + 模板产出的几何 → 完整 IR。
    照片在此只作证据存证 (哈希/尺寸), 不参与尺寸恢复。"""
    ir = json.loads(json.dumps(template_ir))  # deep copy
    ir.pop("_derived", None)  # 模板内部派生量, 不进 IR 协议
    ev = photo_evidence(photo_path)
    ir["package"]["photo"] = {
        "path": ev.path,
        "sha256": ev.sha256,
        "width_px": ev.width_px,
        "height_px": ev.height_px,
    }
    _attach_evidence(ir, spec)
    return _to_ir(ir)


def build_parametric(spec: dict, template_ir: dict) -> GeometryIR:
    """无照片的参数化模式: 尺寸全部来自 spec (实测优先)。照片位留空 — QA 的 G01 如实报告无照片证据,
    报告的 input_usage 写明尺寸来源, 不得被读成"照片测量"。"""
    ir = json.loads(json.dumps(template_ir))
    ir.pop("_derived", None)
    ir["package"]["photo"] = None
    _attach_evidence(ir, spec)
    return _to_ir(ir)


def to_dict(ir: GeometryIR) -> dict:
    d = json.loads(json.dumps(ir.raw))
    return d


def from_raw(raw: dict) -> GeometryIR:
    """任意来源 raw IR → GeometryIR (统一协议清理: 剥模板内部派生量, 重校验)."""
    raw = json.loads(json.dumps(raw))  # 深拷贝, 不污染调用方
    raw.pop("_derived", None)
    validate_dict(raw)
    edges = [FoldEdge(
        id=e["id"],
        seg_2d=((e["seg_2d"][0][0], e["seg_2d"][0][1]), (e["seg_2d"][1][0], e["seg_2d"][1][1])),
        mt_va=e["fold"]["mt_va"], parent=e["fold"]["parent"], child=e["fold"]["child"],
        target_angle_deg=e["fold"].get("target_angle_deg"),
        target_dir_3d=tuple(e["fold"]["target_dir_3d"]) if e["fold"].get("target_dir_3d") else None,
    ) for e in raw["edges"]]
    return GeometryIR(raw["meta"], raw["package"], raw["panels"], edges, raw["features"], raw)


def save(ir: GeometryIR, path: str | Path) -> None:
    Path(path).write_text(json.dumps(to_dict(ir), indent=2, ensure_ascii=False))
