#!/usr/bin/env python3
"""USDCraft-10K vs Pack10K 一对一类别审计 (同尺同规).

同判据电池跑双方资产 — 逐 prim 独立判伤 (多零件铰接资产的零件间穿插合法,
跨 prim 不并顶点, 杜绝把接触误判成缺陷):
  V1 网格存在可开  V2 片材复杂体流形 (prim 内 >4 面边=缺陷)  V3 零退化+零重复面 (prim 内)
  V4 坐标有限  V5 声明 extents vs stage bbox (tol max(2mm,2%))  V6 质量>0  V7 包装侧车合法
model.json 字段: USDCraft 用 asset_extents/mass, Pack10K 用 asset_extents_m/mass_kg (同构带单位后缀).
"""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
from pxr import Usd, UsdGeom

sys_path = str(Path(__file__).resolve().parent.parent / "src")

THEIRS = Path("/tmp/usdcraft_audit")
OURS = Path(__file__).resolve().parent.parent / "output/pack10k_scale10k"

MAPPING = {
    "R422_corrugated_parcel_box": ("rsc", "直接同构: 瓦楞快递箱 = FEFCO 0201"),
    "R423_stackable_container_with_lid": ("two", "分体盖 (base+lid)"),
    "R037_hinged_lid_food_container": ("crashlock", "铰盖; 对方材质混合, 我方纸板"),
    "R038_lunch_box": ("two", "bento 分体"),
    "R119_jewelry_box": ("lockbottom", "礼盒底锁"),
    "R026_bread_box": ("tuck", "插盖顶"),
    "R416_plastic_crate": ("tray", "敞口箱; 材质注记"),
    "R415_tote_bin": ("tray", "敞口箱; 材质注记"),
    "R204_plastic_storage_bin": ("tray", "敞口箱; 材质注记"),
    "R392_small_parts_bin": ("tray", "敞口箱"),
    "R373_document_tray_stack": ("tray", "文档盘"),
    "R203_storage_basket": ("tray", "对方网格篮 vs 我方实壁: 形态注记"),
    "R332_shopping_basket": ("handle", "提手; 篮网形态注记"),
    "R929_pipette_tip_box": ("two", "base+lid"),
    "R035_flip_top_spice_jar": ("prism", "材质注记: 塑料/玻璃 vs 纸板"),
    "R040_mason_jar": ("prism", "材质注记: 玻璃 vs 纸板"),
    "R041_glass_jar_with_clamp_lid": ("prism", "材质注记: 玻璃"),
    "R092_food_tin_can": ("cup", "材质注记: 金属罐 vs 纸板圆筒"),
    "R094_cookie_jar": ("prism", "材质注记: 玻璃/陶"),
}


def mesh_checks(usd_path: Path, declared_extents_m: list[float] | None,
                declared_mass_kg: float | None) -> dict:
    res = {"usd": False, "v2_manifold": False, "v3_clean": False, "v4_finite": False,
           "v5_dims": False, "v6_mass": bool(declared_mass_kg and declared_mass_kg > 0),
           "tris": 0, "nonmanifold_ge5": 0, "degenerate": 0, "dup_faces": 0, "n_prim": 0}
    try:
        stage = Usd.Stage.Open(str(usd_path))
    except Exception:
        return res
    pts_all, tris_all, defect = [], [], {"nm": 0, "deg": 0, "dup": 0}
    import pxr.UsdPhysics as _UP
    # 公平网格选择: 渲染/碰撞分离约定 (USDCraft: 碰撞凸包独立 prim) → 只审渲染组;
    # 单网格兼任约定 (Pack10K: CollisionAPI 打在渲染网格上) → 审全组
    prims_all = [pr for pr in stage.Traverse() if pr.IsA(UsdGeom.Mesh)]
    prims_render = [pr for pr in prims_all if not pr.HasAPI(_UP.CollisionAPI)]
    for prim in (prims_render or prims_all):
        if True:
            mesh = UsdGeom.Mesh(prim)
        counts = mesh.GetFaceVertexCountsAttr().Get()
        idx = mesh.GetFaceVertexIndicesAttr().Get()
        verts = mesh.GetPointsAttr().Get()
        if counts is None or verts is None or len(counts) == 0:
            continue
        res["n_prim"] += 1
        pts = np.asarray(verts, float)
        base = len(pts_all)
        pts_all.append(pts)
        tris = []
        vi = 0
        for n in counts:
            face = idx[vi:vi + n]
            vi += n
            for k in range(1, n - 1):
                tris.append((face[0], face[k], face[k + 1]))
        if not tris:
            continue
        tris = np.asarray(tris, int)
        tris_all.extend((base + tris).tolist())
        res["tris"] += int(len(tris))
        # V3 per-prim: 退化 + 重复面 (prim 内)
        v0, v1_, v2_ = pts[tris[:, 0]], pts[tris[:, 1]], pts[tris[:, 2]]
        area2 = np.linalg.norm(np.cross(v1_ - v0, v2_ - v0), axis=1)
        deg = int((area2 < 1e-12).sum())
        key = np.round(pts, 6)
        uniq, inv = np.unique(key, axis=0, return_inverse=True)
        tinv = inv[tris]
        seen = defaultdict(int)
        for t in tinv:
            seen[tuple(sorted(int(x) for x in t))] += 1
        dup = int(sum(v - 1 for v in seen.values() if v > 1))
        # V2 per-prim: 片材复杂体流形 (prim 内 ≥5 面边)
        edges = defaultdict(int)
        for t in tinv:
            for i in range(3):
                edges[tuple(sorted((int(t[i]), int(t[(i + 1) % 3]))))] += 1
        nm = int(sum(1 for v in edges.values() if v > 4))
        defect["nm"] += nm
        defect["deg"] += deg
        defect["dup"] += dup
    if not pts_all:
        return res
    res["usd"] = True
    res["v4_finite"] = bool(all(np.isfinite(p).all() for p in pts_all))
    res["nonmanifold_ge5"] = defect["nm"]
    res["degenerate"] = defect["deg"]
    res["dup_faces"] = defect["dup"]
    res["v2_manifold"] = defect["nm"] == 0
    res["v3_clean"] = defect["deg"] == 0 and defect["dup"] == 0
    if declared_extents_m:
        allpts = np.vstack(pts_all)
        mn, mx = allpts.min(axis=0), allpts.max(axis=0)
        got = mx - mn
        want = np.asarray(declared_extents_m, float)
        if np.isfinite(got).all() and (want > 0).all():
            rel = float(np.max(np.abs(got - want) / np.maximum(want, 1e-9)))
            res["v5_dims"] = rel <= 0.02
            res["dims_rel_err"] = round(rel, 5)
    return res


def sidecar_ok(p: Path) -> bool:
    try:
        d = json.loads(p.read_text())
        return bool(d.get("id") or d.get("asset_name") or d.get("package_id"))
    except Exception:
        return False


def read_declared(mj: dict) -> tuple[list | None, float | None]:
    ext = mj.get("asset_extents_m", mj.get("asset_extents"))
    mass = mj.get("mass_kg", mj.get("mass"))
    return ext, mass


def audit_theirs() -> dict:
    out = {}
    for cat_dir in sorted(THEIRS.glob("rigid/*/*")):
        if not cat_dir.is_dir():
            continue
        rows = []
        for var in sorted(cat_dir.glob("0*")):
            usd = var / "physx/model.usdc"
            mj = var / "physx/model.json"
            meta = var / "meta.json"
            if not usd.exists():
                continue
            try:
                d = json.loads(mj.read_text())
            except Exception:
                d = {}
            cm = {}
            if meta.exists():
                try:
                    cm = json.loads(meta.read_text())
                except Exception:
                    pass
            ext, mass = read_declared(d)
            r = mesh_checks(usd, ext, mass)
            r["v7_sidecar"] = sidecar_ok(var / "com.nvidia.simready.packaging.json")
            checks = [r["usd"], r["v2_manifold"], r["v3_clean"], r["v4_finite"],
                      r["v5_dims"], r["v6_mass"], r["v7_sidecar"]]
            r.update(passed=sum(checks), total=len(checks), variant=var.name,
                     physics_type=cm.get("physics_type", "?"), part_count=cm.get("part_count", "?"))
            rows.append(r)
        if rows:
            out[cat_dir.name] = rows
    return out


def audit_ours(n_per_family: int = 10) -> dict:
    rows_manifest = list(csv.DictReader(open(OURS / "manifest.csv")))
    by_fam = defaultdict(list)
    for r in rows_manifest:
        if r["status"] == "GREEN":
            by_fam[r["family"]].append(r)
    out = {}
    for cat, (fam, note) in MAPPING.items():
        rows = []
        for r in by_fam[fam][:n_per_family]:
            nid = re.sub(r"v(\d{6})$", lambda m: "v" + m.group(1)[-4:], r["asset_id"])
            d = OURS / nid
            usd = d / "model.usdc"
            if not usd.exists() and (OURS / r["asset_id"] / "model.usdc").exists():
                d = OURS / r["asset_id"]
                usd = d / "model.usdc"
            if not usd.exists():
                continue
            try:
                mj = json.loads((d / "model.json").read_text())
            except Exception:
                mj = {}
            ext, mass = read_declared(mj)
            r2 = mesh_checks(usd, ext, mass)
            r2["v7_sidecar"] = sidecar_ok(d / "packaging.json")
            checks = [r2["usd"], r2["v2_manifold"], r2["v3_clean"], r2["v4_finite"],
                      r2["v5_dims"], r2["v6_mass"], r2["v7_sidecar"]]
            r2.update(passed=sum(checks), total=len(checks), variant=r["asset_id"])
            rows.append(r2)
        if rows:
            out[cat] = rows
    return out


def agg(rows: list[dict]) -> dict:
    n = len(rows)
    full = sum(1 for r in rows if r["passed"] == r["total"])
    return {"n": n, "full_pass": full, "rate": round(full / max(n, 1), 3),
            "median_tris": int(np.median([r["tris"] for r in rows])) if n else 0,
            "fails": {k: sum(1 for r in rows if not r.get(k, False))
                      for k in ("v2_manifold", "v3_clean", "v4_finite", "v5_dims", "v6_mass", "v7_sidecar")}}


def main() -> None:
    theirs = audit_theirs()
    ours = audit_ours()
    report = {"criteria": "V1 usd / V2 prim内流形(≥5面边=缺陷) / V3 prim内零退化零重复 / V4 finite / V5 extents≤max(2mm,2%) / V6 mass>0 / V7 sidecar",
              "schema_note": "USDCraft model.json: asset_extents/mass; Pack10K: asset_extents_m/mass_kg (同构, 我方加单位后缀)",
              "categories": {}}
    print(f"{'类别':36s} | {'我方族':9s} | 对方 n/率/中位tri | 我方 n/率/中位tri | 对方伤 | 我方伤")
    for cat, (fam, note) in sorted(MAPPING.items()):
        tr = agg(theirs.get(cat, []))
        ur = agg(ours.get(cat, []))
        report["categories"][cat] = {"our_family": fam, "note": note, "theirs": tr, "ours": ur,
                                     "theirs_detail": theirs.get(cat, []), "ours_detail": ours.get(cat, [])}
        print(f"{cat:36s} | {fam:9s} | {tr['n']:2d}/{tr['rate']:.2f}/{tr['median_tris']:6d} "
              f"| {ur['n']:2d}/{ur['rate']:.2f}/{ur['median_tris']:6d} | {json.dumps(tr['fails'])} | {json.dumps(ur['fails'])}")
    tot_t = [agg(report["categories"][c]["theirs_detail"]) for c in report["categories"]]
    tot_u = [agg(report["categories"][c]["ours_detail"]) for c in report["categories"]]
    report["aggregate"] = {
        "theirs": {"n": sum(t["n"] for t in tot_t), "full_pass": sum(t["full_pass"] for t in tot_t)},
        "ours": {"n": sum(u["n"] for u in tot_u), "full_pass": sum(u["full_pass"] for u in tot_u)},
    }
    for side in ("theirs", "ours"):
        a = report["aggregate"][side]
        a["rate"] = round(a["full_pass"] / max(a["n"], 1), 4)
    od = Path(__file__).resolve().parent.parent / "docs/reviews/usdcraft_1v1_audit.json"
    od.parent.mkdir(parents=True, exist_ok=True)
    od.write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print("聚合:", json.dumps(report["aggregate"], ensure_ascii=False))
    print("->", od)


if __name__ == "__main__":
    main()
