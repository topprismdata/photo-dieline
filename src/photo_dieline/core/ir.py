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


def build(spec: dict, photo_path: str | Path, template_ir: dict) -> GeometryIR:
    """spec(用户输入+证据) + 模板产出的几何 → 完整 IR dict → 校验 → GeometryIR."""
    ir = json.loads(json.dumps(template_ir))  # deep copy
    ir.pop("_derived", None)  # 模板内部派生量, 不进 IR 协议
    ev = photo_evidence(photo_path)
    ir["package"]["photo"] = {
        "path": ev.path,
        "sha256": ev.sha256,
        "width_px": ev.width_px,
        "height_px": ev.height_px,
    }
    # 尺寸证据状态记录: spec.measurements[{name,value_mm,status,source?}]
    status_map = {m["name"]: m["status"].upper() for m in spec.get("measurements", [])}
    ir["package"]["params_evidence"] = {
        k: status_map.get(k, "DEFAULTED") for k in ir["package"]["params"]
    }
    for k, st in ir["package"]["params_evidence"].items():
        if st not in {"MEASURED", "VERIFIED_SOURCE", "DERIVED", "INFERRED", "DEFAULTED"}:
            raise ARError(f"非法证据状态 {k}={st}")
    validate_dict(ir)
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


def to_dict(ir: GeometryIR) -> dict:
    d = json.loads(json.dumps(ir.raw))
    return d


def save(ir: GeometryIR, path: str | Path) -> None:
    Path(path).write_text(json.dumps(to_dict(ir), indent=2, ensure_ascii=False))
