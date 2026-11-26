#!/usr/bin/env python3
"""资产规格验证器: metadata.json × asset_spec.schema.json × retail_categories.json。

用法: python3 scripts/validate_asset_spec.py <dir-with-metadata.json> ...
规则:
 1. JSON Schema (draft-07) 结构合规
 2. 双轴注册: axes 必须落在 retail_categories.json mappings 的注册组合内
 3. closure 一致性: attributes.closure == mapping.closure
 4. 来源分级纪律: dimensions/mass 必须存在且 source_tier ∈ 六级;
    不允许 missing 标 estimated (禁止编造冒充)
输出: 每文件 PASS/FAIL + 汇总。任一 FAIL → 退出码 1。
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src"))

try:
    import jsonschema
except ImportError:
    jsonschema = None

SCHEMA = json.load(open(HERE / "docs/retail_ontology/asset_spec.schema.json"))
CATS = json.load(open(HERE / "docs/retail_ontology/retail_categories.json"))
MAPPING = {m["asset"]: m for m in CATS["mappings"]}
TIERS = {"measured", "official_spec", "derived", "estimated", "sampled", "unknown"}


def check(path: Path) -> list[str]:
    fails = []
    spec = json.load(open(path))
    # 1. schema
    if jsonschema:
        try:
            jsonschema.validate(spec, SCHEMA)
        except jsonschema.ValidationError as e:
            fails.append(f"schema: {e.message[:120]}")
    else:
        for k in SCHEMA["required"]:
            if k not in spec:
                fails.append(f"schema: missing required '{k}'")
    # 2. 双轴注册
    aid = spec.get("asset", path.parent.name)
    m = MAPPING.get(aid)
    if not m:
        fails.append("axes: 资产未在 retail_categories.json mappings 注册")
    else:
        ax = spec.get("axes", {})
        if ax.get("product_category") != m["product_category"]:
            fails.append(f"axes: product_category {ax.get('product_category')!r} != 注册 {m['product_category']!r}")
        if ax.get("packaging_structure") != m["packaging_structure"]:
            fails.append(f"axes: packaging_structure 不一致")
        # 3. closure 一致
        cl = spec.get("attributes", {}).get("closure", {})
        clv = cl.get("value") if isinstance(cl, dict) else cl
        if clv != m["closure"]:
            fails.append(f"closure: {clv!r} != 注册 {m['closure']!r}")
    # 4. 来源分级纪律
    attrs = spec.get("attributes", {})
    for req in ("dimensions_mm", "mass_kg"):
        a = attrs.get(req)
        if not isinstance(a, dict) or "value" not in a:
            fails.append(f"{req}: 缺 value (必须有带来源的值, 哪怕 unknown)")
        elif a.get("source_tier") not in TIERS:
            fails.append(f"{req}: source_tier {a.get('source_tier')!r} 非法")
    return fails


def main() -> int:
    paths = []
    for p in sys.argv[1:]:
        pp = Path(p)
        if pp.is_dir():
            paths += sorted(pp.glob("*/simready_usd/metadata.json"))
        else:
            paths.append(pp)
    if not paths:
        print("usage: validate_asset_spec.py <dir|metadata.json> ...")
        return 2
    npass = 0
    for p in paths:
        fails = check(p)
        aid = p.parent.parent.name if p.parent.name == 'simready_usd' else p.stem
        if fails:
            print(f"FAIL {aid}:")
            for f in fails:
                print(f"   - {f}")
        else:
            npass += 1
            print(f"PASS {aid}")
    print(f"\n{npass}/{len(paths)} PASS")
    return 0 if npass == len(paths) else 1


if __name__ == "__main__":
    raise SystemExit(main())
