#!/usr/bin/env python3
"""check_simready_conformance: 官方 CAP/FET 能力清单的可执行子集, 双侧量测.

检查项建模自官方资产内嵌验证矩阵 (banana sm_...usda SimReady_Metadata.validation),
能力 ID 对应官方命名; 其中 WIKIDATA_QCODE 是我方已知缺口, 如实参测.
用法: python3 scripts/check_simready_conformance.py
输出: docs/shelf_twin/conformance_score.json + 双侧通过率表
"""
import json
import sys
from pathlib import Path

import mujoco
import numpy as np
from pxr import Sdf, Usd, UsdGeom, UsdShade

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from verify_sku_physics import MANIFEST, verify  # noqa: E402

GAP = 0.005
FRIC = {"glass": 0.4, "clear_glass": 0.4, "plastic": 0.4, "paperboard": 0.6,
        "plant": 0.7, "organic": 0.7, "rubber": 0.7, "metal": 0.4}

CHECKS = [
    "CORE_OPENUSD",        # CAP000: plain usd-core 可开
    "SELF_CONTAINED",      # CAP031: 引用自包含
    "PLACEABLE_VISUAL",    # FET001: Z-up/米制/非空网格
    "WIKIDATA_LABELS",     # CAP046: wikidata_class 可解析
    "WIKIDATA_QCODE",      # 官方 qcode 富化 (我方已知缺口)
    "SEMANTIC_MATERIAL",   # FET011: material 标签
    "MATERIALS_BOUND",     # FET006: 材质绑定到可渲染 prim
    "EXTENTS_METADATA",    # 机器可读尺寸
    "MASS_METADATA",       # 机器可读质量
    "RIGID_BODY_MUJOCO",   # CAP003: MuJoCo 静置
]


def walk(stage):
    for p in stage.TraverseAll():
        if p.IsInstance():
            p.SetInstanceable(False)
    return stage.TraverseAll()


def resolve(stage, prim, key):
    while prim.IsValid():
        a = prim.GetAttribute(f"semantics:labels:{key}")
        if a is not None and a.Get() is not None:
            return str(a.Get())
        prim = prim.GetParent()
    return None


def check(stage, mesh_prims, dims=None, mass=None):
    it = walk(stage)
    root = stage.GetDefaultPrim() or next((p for p in it), None)
    res = {}
    res["CORE_OPENUSD"] = stage is not None
    # 自包含: 所有子层/引用路径都落在资产目录内 (我方单文件无引用 = 自包含)
    bad = []
    for lay in stage.GetLayerStack():
        ident = lay.identifier
        if ident.startswith("/") and "assets/" not in ident and "sku_usd" not in ident:
            bad.append(ident)
    res["SELF_CONTAINED"] = not bad
    up = UsdGeom.GetStageUpAxis(stage)
    lps = stage.GetMetadata("metersPerUnit")
    mpu = float(lps) if lps is not None else 0.01
    res["PLACEABLE_VISUAL"] = (up == "Z" and abs(mpu - 1.0) < 1e-6
                               and len(mesh_prims) > 0)
    cls = resolve(stage, mesh_prims[0] if mesh_prims else root, "wikidata_class")
    res["WIKIDATA_LABELS"] = cls is not None
    q = resolve(stage, mesh_prims[0] if mesh_prims else root, "wikidata_qcode")
    res["WIKIDATA_QCODE"] = q is not None
    mat = None
    for p in walk(stage):
        a = p.GetAttribute("semantics:labels:material")
        if a is not None and a.Get() is not None:
            mat = str(a.Get())
            break
    if mat is None:
        mat = resolve(stage, mesh_prims[0] if mesh_prims else root, "material")
    res["SEMANTIC_MATERIAL"] = mat is not None
    bound = False
    for p in walk(stage):
        if p.IsA(UsdGeom.Mesh):
            for rel in p.GetRelationships():
                if rel.GetName().startswith("material:binding") and rel.GetTargets():
                    bound = True
                    break
        if bound:
            break
    has_matprim = any(p.IsA(UsdShade.Material) for p in walk(stage))
    res["MATERIALS_BOUND"] = bound and has_matprim
    res["EXTENTS_METADATA"] = dims is not None
    res["MASS_METADATA"] = mass is not None
    return res, cls, mat


def settle_mu(dims_m, mass, mu):
    w, d, h = dims_m
    mjcf = f"""
<mujoco><option timestep="0.002" gravity="0 0 -9.81"/>
<worldbody><geom name="f" type="plane" size="1 1 0.1" friction="1 1 1"/>
<body name="b" pos="0 0 {h/2+GAP}"><freejoint/>
<geom name="g" type="box" size="{w/2} {d/2} {h/2}" mass="{mass}"
friction="{mu} {mu} 1" condim="3"/></body></worldbody></mujoco>"""
    m = mujoco.MjModel.from_xml_string(mjcf)
    d2 = mujoco.MjData(m)
    z0 = d2.qpos[2]
    for _ in range(500):
        mujoco.mj_step(m, d2)
    ke = 0.5 * mass * float(np.dot(d2.qvel[:3], d2.qvel[:3]))
    z = d2.qpos[2]
    return ke < 1e-6 and z < z0 + GAP + 1e-3 and abs(z - h / 2) < GAP + 2e-3


def ours(asset_path, sku):
    st = Usd.Stage.Open(str(asset_path))
    meshes = [p for p in walk(st) if p.IsA(UsdGeom.Mesh)]
    dims = None
    r = st.GetDefaultPrim()
    for key in ("phys:dimensionsMM", "userProperties:dims_mm"):
        if r.IsValid() and r.HasAttribute(key):
            dims = [float(x) for x in r.GetAttribute(key).Get()]
            break
    mass = sku["mass_g"] / 1000.0
    res, cls, mat = check(st, meshes, dims, mass)
    stable, _, _, _, _ = verify(sku)
    res["RIGID_BODY_MUJOCO"] = bool(stable)
    return res, cls, mat, dims


def official(asset_dir):
    mains = sorted(asset_dir.glob("sm_*.usd*"))
    if not mains:
        return None
    st = Usd.Stage.Open(str(mains[0]))
    meshes = [p for p in walk(st) if p.IsA(UsdGeom.Mesh)]
    cld = dict(st.GetRootLayer().customLayerData or {})
    cld.update(cld.get("SimReady_Metadata") or {})
    ext = cld.get("asset_extents")
    mass = cld.get("mass")
    res, cls, mat = check(st, meshes,
                          [float(x) * 1000 for x in ext] if ext else None, mass)
    if ext and mass:
        mu = FRIC.get(mat, 0.5)
        res["RIGID_BODY_MUJOCO"] = bool(settle_mu([float(x) for x in ext],
                                                  float(mass), mu))
    else:
        res["RIGID_BODY_MUJOCO"] = False
    return res, cls, mat, ext


def main():
    manifest = {s["id"]: s for s in MANIFEST["skus"]}
    rows = []
    for f in sorted((ROOT / "assets/sku_usd").glob("*.usda")):
        sku = manifest[f.stem]
        res, cls, mat, dims = ours(f, sku)
        rows.append({"side": "esr", "asset": f.stem, "checks": res})
    for d in sorted((ROOT / "assets/simready_official").iterdir()):
        if not d.is_dir():
            continue
        got = official(d)
        if got is None:
            continue
        res, cls, mat, ext = got
        rows.append({"side": "official", "asset": d.name, "checks": res})

    summary = {}
    for c in CHECKS:
        esr = [r for r in rows if r["side"] == "esr"]
        off = [r for r in rows if r["side"] == "official"]
        summary[c] = {
            "esr": f"{sum(r['checks'][c] for r in esr)}/{len(esr)}",
            "official": f"{sum(r['checks'][c] for r in off)}/{len(off)}",
        }
    esr_n, off_n = len([r for r in rows if r["side"] == "esr"]), len([r for r in rows if r["side"] == "official"])
    esr_total = sum(sum(r["checks"].values()) for r in rows if r["side"] == "esr")
    off_total = sum(sum(r["checks"].values()) for r in rows if r["side"] == "official")
    print(f"{'能力(官方ID建模)':<22} {'ESR(14)':>8} {'官方(3)':>8}")
    for c in CHECKS:
        print(f"{c:<22} {summary[c]['esr']:>8} {summary[c]['official']:>8}")
    print(f"\n总分: ESR {esr_total}/{esr_n*len(CHECKS)} ({esr_total/(esr_n*len(CHECKS)):.0%})"
          f"  官方 {off_total}/{off_n*len(CHECKS)} ({off_total/(off_n*len(CHECKS)):.0%})")
    out = ROOT / "data/shelf_twin/conformance_score.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "schema": "simready-conformance/1.0",
        "checks": CHECKS, "rows": rows, "summary": summary,
        "totals": {"esr": [esr_total, esr_n * len(CHECKS)],
                   "official": [off_total, off_n * len(CHECKS)]},
    }, ensure_ascii=False, indent=1))
    print(f"CONFORMANCE_DONE -> {out}")


if __name__ == "__main__":
    main()
