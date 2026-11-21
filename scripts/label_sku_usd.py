#!/usr/bin/env python3
"""label_sku_usd: usd-core 补 SemanticsLabelsAPI + phys:dimensionsMM (ESR Step B ②).

规范硬点 (simready-usd-pipeline-mac):
- SL.003 用 SemanticsLabelsAPI (非废弃 SemanticsAPI)
- SL.MAT.001 每个 Material prim 非空 material 标签
- instance name = taxonomy 名 (wikidata_class / material), 值写品类词
用法: python3 scripts/label_sku_usd.py
"""
import json
from pathlib import Path

from pxr import Gf, Kind, Sdf, Usd, UsdShade

ROOT = Path(__file__).parent.parent
USD_DIR = ROOT / "assets/sku_usd"
MANIFEST = {s["id"]: s for s in json.loads((ROOT / "data/shelf_twin/sku_manifest.json").read_text())["skus"]}


def label_stage(usda: Path, sku: dict):
    stage = Usd.Stage.Open(str(usda))
    root = stage.GetDefaultPrim()
    if not root or not root.IsValid():
        root = stage.GetPseudoRoot().GetChildren()[0]
    stage.SetDefaultPrim(root)
    root.SetKind(Kind.Tokens.component)

    # 尺寸单源: 读 Blender userProperties (custom props) → phys: dimensionsMM
    dims = None
    for key in ("dims_mm", "userProperties:dims_mm"):
        if root.HasAttribute(key):
            dims = root.GetAttribute(key).Get()
            break
    if dims is None:
        dims = sku["dims_mm"]
    dims_attr = root.CreateAttribute("phys:dimensionsMM", Sdf.ValueTypeNames.Float3)
    dims_attr.Set(Gf.Vec3f(float(dims[0]), float(dims[1]), float(dims[2])))

    # 语义: 类标签 (SL.003 SemanticsLabelsAPI) — apiSchemas apply + 裸属性双写
    # 官方样例写法: 裸属性 semantics:labels:<taxonomy> (参数化 ApplyAPI 需 SimReady 插件, plain usd-core 无)
    api = "SemanticsLabelsAPI:wikidata_class"
    attr = root.CreateAttribute("semantics:labels:wikidata_class", Sdf.ValueTypeNames.Token)
    attr.Set(sku["class_label"])

    # 材质标签 (SL.MAT.001): 材质 prim (Blender 导出可能无材质 → 打在 root 的材质标签属性)
    # SL.MAT.001: 裸属性 (同上)
    mattr = root.CreateAttribute("semantics:labels:material", Sdf.ValueTypeNames.Token)
    mattr.Set(sku["material"])
    for prim in stage.Traverse():
        if prim.IsA(UsdShade.Material):
            p = prim.CreateAttribute("semantics:labels:material", Sdf.ValueTypeNames.Token)
            if not p.HasAuthoredValue():
                p.Set(sku["material"])

    stage.GetRootLayer().Save()
    return [float(d) for d in dims]


def main():
    ok, fail = [], []
    for f in sorted(USD_DIR.glob("*.usda")):
        sku = MANIFEST.get(f.stem)
        if not sku:
            fail.append((f.name, "no manifest entry"))
            continue
        try:
            dims = label_stage(f, sku)
            ok.append((f.stem, dims))
        except Exception as e:  # noqa: BLE001
            fail.append((f.name, str(e)))
    for sid, dims in ok:
        print("LABELED", sid, dims)
    for name, err in fail:
        print("FAIL", name, err)
    print(f"LABEL_DONE ok={len(ok)} fail={len(fail)}")


if __name__ == "__main__":
    main()
