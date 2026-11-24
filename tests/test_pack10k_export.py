"""pack10k 导出/采样器测试 — 种子确定性、validate 守门、USD 往返、三方对账。"""

import math
from pathlib import Path

import pytest

from photo_dieline.core.ir import class_defaults, class_module, from_raw
from photo_dieline.export.usd import export_usdc, reconcile_dims, stage_dims_m
from photo_dieline.parametric.sample import sample_variant, seed_from

try:
    sys_path_guard = True
except NameError:  # pragma: no cover
    sys_path_guard = False


def _ir(cls="gable_top", params=None):
    mod = class_module(cls)
    p = params or class_defaults(cls)
    return from_raw({k: v for k, v in mod.build_ir(p).items() if k != "_derived"})


def test_seed_deterministic():
    assert sample_variant("gable_top", 7) == sample_variant("gable_top", 7)
    assert sample_variant("gable_top", 7)[1]["seed"] == seed_from("gable_top", 7)
    p7 = sample_variant("gable_top", 7)[0]
    p8 = sample_variant("gable_top", 8)[0]
    assert p7["W"] != p8["W"]  # 不同 index → 不同变体


def test_sampler_explicit_keys_only():
    with pytest.raises(ValueError):
        sample_variant("rsc_regular", 0)  # rsc 未声明 SCALABLE_KEYS → 禁启发式


def test_sampler_scales_and_validates():
    p, d = sample_variant("gable_top", 3)
    base = class_defaults("gable_top")
    assert 0.8 <= d["scale"] <= 1.25
    assert p["W"] == pytest.approx(base["W"] * d["scale"], abs=1.1e-3)  # 采样器圆整 3dp (mm 口径)
    assert p["board_t"] == base["board_t"]  # 工艺参数不动
    mod = class_module("gable_top")
    mod.validate_params(p)  # 不抛 = 合法


def test_export_roundtrip(tmp_path: Path):
    ev = export_usdc(_ir(), tmp_path / "model.usdc", kind="carton_board")
    assert ev["mass_kg"] > 0 and ev["n_tris"] > 0
    # 独立重开: 单位/defaultPrim/实测尺寸
    from pxr import Sdf, Usd, UsdGeom, UsdPhysics

    stage = Usd.Stage.Open(str(tmp_path / "model.usdc"))
    assert stage.GetDefaultPrim().GetPath() == Sdf.Path("/Asset")
    assert UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.z
    assert math.isclose(UsdGeom.GetStageMetersPerUnit(stage), 1.0, abs_tol=1e-12)
    assert math.isclose(UsdPhysics.GetStageKilogramsPerUnit(stage), 1.0, abs_tol=1e-12)
    assert not any(p.IsA(UsdPhysics.Scene) for p in stage.Traverse())
    dims = stage_dims_m(tmp_path / "model.usdc")
    assert all(d > 0 for d in dims)
    m = UsdPhysics.MassAPI(stage.GetPrimAtPath("/Asset/Body"))
    assert m.GetMassAttr().Get() == pytest.approx(ev["mass_kg"], rel=1e-9)


def test_reconcile_exact_and_fail():
    d = {"W": 45.0, "D": 45.0, "H": 112.0}
    r = reconcile_dims(d, dict(d), [0.045, 0.045, 0.112])
    assert r["ok"] and r["worst_diff_mm"] == 0.0
    r2 = reconcile_dims(d, {"W": 45.6, "D": 45.0, "H": 112.0}, [0.045, 0.045, 0.112])
    assert not r2["ok"] and r2["axes"]["W"]["analytic_vs_folded"] == pytest.approx(0.6)


def test_export_mass_from_area(tmp_path: Path):
    ev = export_usdc(_ir("clv_double_tuck"), tmp_path / "m.usdc")
    assert ev["gsm"] == 320.0
    assert ev["mass_kg"] == pytest.approx(ev["area_m2"] * 320.0 / 1000.0, rel=1e-12)
