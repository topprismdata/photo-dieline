"""WP-A0.1 独立参考实现交叉对照: trimesh vs auditor_core (合成+真实样本)"""
import sys, json, numpy as np
sys.path.insert(0, "/Users/guohongbin/photo-dieline/scripts")
from auditor_core import audit_stage
from pxr import Usd, UsdGeom, Sdf, Gf, Vt
import trimesh

def cube_trimesh(inward=False):
    m = trimesh.creation.box(extents=[1, 1, 1])
    if inward: m.invert()
    return m

def stage_from_trimesh(m, name="B"):
    stage = Usd.Stage.CreateInMemory()
    mesh = UsdGeom.Mesh.Define(stage, f"/{name}")
    mesh.GetPointsAttr().Set(Vt.Vec3fArray([Gf.Vec3f(*p) for p in m.vertices]))
    faces = m.faces
    mesh.GetFaceVertexCountsAttr().Set(Vt.IntArray([3] * len(faces)))
    mesh.GetFaceVertexIndicesAttr().Set(Vt.IntArray([int(i) for f in faces for i in f]))
    mesh.GetSubdivisionSchemeAttr().Set("none")
    return stage

results = []
# 合成对照
for name, m, expect_watertight, expect_wind in [
    ("synth_cube", cube_trimesh(), True, True),
    ("synth_cube_inward", cube_trimesh(True), True, False),
]:
    stage = stage_from_trimesh(m)
    r = audit_stage(stage, contract="SOLID")
    tm = {"is_watertight": bool(m.is_watertight), "is_winding_consistent": bool(m.is_winding_consistent),
          "volume": float(m.volume)}
    shells = [sh for R in r["L1"]["prims"].values() for sh in R.get("shells", [])]
    a = {"closed_shells": all(sh["closed"] for sh in shells) if shells else None,
         "winding_ok": not any(f.startswith("winding") for R in r["L1"]["prims"].values() for f in R["findings"])}
    results.append({"case": name, "trimesh": tm, "auditor": a,
                    "match": (tm["is_watertight"] == a["closed_shells"]) and (tm["is_winding_consistent"] == a["winding_ok"]) if a["closed_shells"] is not None else None})
# 真实样本对照: 3 个 SKU (usdc → trimesh 侧从同一数据构建)
from pxr import Usd as U2
def load_usdc_mesh(path):
    stage = U2.Stage.Open(path)
    out = []
    for p in stage.Traverse():
        if p.IsA(UsdGeom.Mesh):
            mesh = UsdGeom.Mesh(p)
            pts = np.asarray(mesh.GetPointsAttr().Get() or [])
            fvi = np.asarray(mesh.GetFaceVertexIndicesAttr().Get() or [])
            fv = np.asarray(mesh.GetFaceVertexCountsAttr().Get() or [])
            if len(fv) == 0: continue
            out.append((str(p.GetPath()), pts, fvi.reshape(-1, 3)))
    return out

for sku in ["rsc_rsc_rsc_v6959", "aseptic_aseptic_brick_v0000", "tray_tray_4corner_v0130"]:
    path = f"output/pack10k_scale10k/{sku}/model.usdc"
    rec = {"case": sku, "prim_results": []}
    agree_all = True
    for pp, pts, tri in load_usdc_mesh(path):
        m = trimesh.Trimesh(vertices=pts, faces=tri, process=False)
        tm = {"is_watertight": bool(m.is_watertight), "is_winding_consistent": bool(m.is_winding_consistent), "volume": float(m.volume)}
        stage = U2.Stage.Open(path)  # 用完整 stage 审计同一文件
        r = audit_stage(stage, contract="UNKNOWN")
        # 找该 prim 的壳观测
        shells = []
        for R in r["L1"]["prims"].values():
            shells += R.get("shells", [])
        a_closed = any(s["closed"] for s in shells) if shells else None
        a_wind_bad = any("winding" in f for R in r["L1"]["prims"].values() for f in R["findings"])
        agree = (tm["is_watertight"] == a_closed) if a_closed is not None else None
        if agree is False: agree_all = False
        rec["prim_results"].append({"prim": pp.split("/")[-1], "trimesh": tm, "auditor_closed_shell_exists": a_closed})
    rec["agree_watertight"] = agree_all
    results.append(rec)
json.dump(results, open("/Users/guohongbin/photo-dieline/docs/research/evidence/wp_a0_crosscheck.json", "w"), indent=1, ensure_ascii=False)
for r in results: print(json.dumps(r, ensure_ascii=False)[:200])
