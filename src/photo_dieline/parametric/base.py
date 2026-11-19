"""模板注册表与契约 (批量验证 M2-A).

模板模块契约 (模块级, 无类):
  DEFAULTS: dict                     参数默认值
  PARAM_ORDER: list[str]             参数序 (G02 必备键)
  build_ir(params) -> raw IR dict    展开 IR (meta.template.id = 类ID)
  analytic_bbox(params) -> dict      G05 期望 bbox {"W","D","H"} mm
  closure_checks(ir, world) -> dict  G04 闭合残差 {name: mm}
  allowed_overlap() -> set[frozenset] G06 允许叠层对 (真实工艺契约)
  solid_roles() -> tuple[str,...]    G05 量尺寸的角色集
"""
from __future__ import annotations

from importlib import import_module

REGISTRY: dict[str, str] = {}  # class_id -> module name (parametric.<mod>)
_CACHE: dict[str, object] = {}


def register(cls_id: str, mod_name: str) -> None:
    REGISTRY[cls_id] = mod_name


def get(cls_id: str):
    if cls_id not in _CACHE:
        if cls_id not in REGISTRY:
            raise KeyError(f"未注册模板类: {cls_id}")
        _CACHE[cls_id] = import_module(f".{REGISTRY[cls_id]}", __package__)
    return _CACHE[cls_id]


def all_classes() -> list[str]:
    return sorted(REGISTRY)


# --- 自动发现: 包内每个模块导入即自行 register() (零编辑冲突扩展) ---
import pkgutil  # noqa: E402
from pathlib import Path as _P

for _m in pkgutil.iter_modules([str(_P(__file__).parent)]):
    if _m.name in ("base",):
        continue
    try:
        import_module(f".{_m.name}", __package__)
    except Exception as _exc:  # noqa: BLE001
        import sys
        print(f"[parametric] 跳过 {_m.name}: {_exc}", file=sys.stderr)
