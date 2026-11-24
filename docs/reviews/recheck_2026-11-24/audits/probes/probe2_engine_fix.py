import math, numpy as np
from photo_dieline.core.ir import from_raw
from photo_dieline.folding.engine import fold_all
def simple_ir(mt_va, angle=90.0):
    return {
        "meta": {"ir_version": "0.1", "units": "mm", "generator": "probe",
                 "root_panel": "parent", "root_frame": {"R": [[1,0,0],[0,1,0],[0,0,1]], "off": [0,0,0]}},
        "package": {"type": "probe", "params": {}, "template": {"id": "probe", "version": "0.1"}, "photo": None},
        "panels": [
            {"id": "parent", "role": "wall", "polygon_2d": [[0,0],[10,0],[10,10],[0,10]]},
            {"id": "child", "role": "wall", "polygon_2d": [[0,-10],[10,-10],[10,0],[0,0]]},
        ],
        "edges": [{"id": "e1", "kind": "FOLD", "seg_2d": [[0,0],[10,0]],
                   "fold": {"mt_va": mt_va, "parent": "parent", "child": "child", "target_angle_deg": angle}}],
        "features": [],
    }
def away_dir(w):
    w = np.asarray(w); d = (w[0]+w[1])/2 - (w[2]+w[3])/2; return d/np.linalg.norm(d)
print("== E1c (修正): target_dir_3d 含铰链轴分量 ==")
ir = simple_ir("VALLEY", 90.0); ir["edges"][0]["fold"]["target_dir_3d"] = [0.7, -0.7, 0.7]
w = fold_all(from_raw(ir)); d = away_dir(w["child"]); tgt = np.array([0.7,-0.7,0.7]); tgt/=np.linalg.norm(tgt)
print(" no error; achieved=", d.round(4).tolist(), " requested=", tgt.round(4).tolist(),
      " angle_err_deg=", round(math.degrees(math.acos(float(np.clip(d@tgt,-1,1)))),2))
print("== E1e (修正): child 已放置后, 第二条入边被丢弃且无残差 ==")
ir = simple_ir("VALLEY", 90.0)
ir["panels"].append({"id": "p2", "role": "wall", "polygon_2d": [[10,0],[20,0],[20,10],[10,10]]})
ir["edges"].append({"id": "e2", "kind": "FOLD", "seg_2d": [[10,0],[20,0]],
                    "fold": {"mt_va": "VALLEY", "parent": "p2", "child": "child",
                             "target_dir_3d": [0,0,1]}})   # 与 e1 的折向矛盾
try:
    w = fold_all(from_raw(ir)); print(" no error. panels placed:", sorted(w), "| e2 (p2->child) silently dropped:", True)
except Exception as e:
    print(" ->", type(e).__name__, e)

print("== E1f: 无 tdir 的边在注册模板中的占比 (影响面, 只读统计) ==")
from photo_dieline.parametric import base as T
tot = notd = ncls = 0; per = {}
for c in T.all_classes():
    try:
        m = T.get(c); raw = m.build_ir(dict(m.DEFAULTS))
    except Exception as e:
        per[c] = f"build-error {type(e).__name__}"; continue
    es = raw.get("edges", [])
    k = sum(1 for e in es if not e.get("fold", {}).get("target_dir_3d"))
    tot += len(es); notd += k; ncls += 1
    if k: per[c] = f"{k}/{len(es)}"
print(f" classes built={ncls} edges={tot} edges_without_tdir={notd} classes_with_such_edges={len(per)}")
print(" ", dict(list(per.items())[:40]))
