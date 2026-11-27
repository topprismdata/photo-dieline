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
        _CACHE[cls_id] = _wrap_identity_guard(cls_id, import_module(f".{REGISTRY[cls_id]}", __package__))
    return _CACHE[cls_id]


class _IdentityGuard:
    """GOV-IR-01 (R23-A 授权): 输入身份冲突 FAIL-CLOSED。
    调用方经 get(cls_id) 取模块并 build_ir(params) 时, 产物 template.id 必须与
    请求的 cls_id 一致; 共享模块 (如 prism_dust 同服务 n4..n12) 的参数默认值
    静默改写身份 (漏传 n → n4) 由此在编译入口直接拒绝, 不再产出错误身份资产。"""

    def __init__(self, cls_id: str, mod):
        self._cls_id = cls_id
        self._mod = mod
        self.__doc__ = getattr(mod, "__doc__", "")

    def __getattr__(self, name):
        return getattr(self._mod, name)

    def build_ir(self, params: dict | None = None) -> dict:
        ir_raw = self._mod.build_ir(params)
        got = ir_raw.get("package", {}).get("template", {}).get("id")
        # 仅当产物身份是【另一注册类】(兄弟类, 如 prism_dust_n4 vs 请求 n12) 时拒绝;
        # 模块级模板标识 (如 rsc_rsc, 不在注册表) 是该模块自身的合法标记, 放行。
        if got != self._cls_id and got in REGISTRY:
            raise IdentityConflictError(
                f"GOV-IR-01 身份冲突: 请求类 {self._cls_id} 但参数产物为注册类 {got} "
                f"(共享模块默认值静默生效; 请显式传全身份参数, 如 n)")
        return ir_raw


class IdentityConflictError(ValueError):
    pass


def _wrap_identity_guard(cls_id: str, mod):
    if not hasattr(mod, "build_ir"):
        return mod
    return _IdentityGuard(cls_id, mod)


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
