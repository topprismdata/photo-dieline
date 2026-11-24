"""E1: 折叠引擎非 tdir 分支 VALLEY/MOUNTAIN 判别是否有效 (只读探针)."""
import copy, json, math
import numpy as np
from photo_dieline.core.ir import from_raw
from photo_dieline.folding.engine import fold_all, _away_net, _rot

def simple_ir(mt_va, angle=90.0):
    # net: parent 正方形 (0..10, 0..10), child 在其下方 (0..10, -10..0), 折线 y=0
    return {
        "meta": {"ir_version": "0.1", "units": "mm", "generator": "probe",
                 "root_panel": "parent", "root_frame": {"R": [[1,0,0],[0,1,0],[0,0,1]], "off": [0,0,0]}},
        "package": {"type": "probe", "params": {}, "template": {"id": "probe", "version": "0.1"}, "photo": None},
        "panels": [
            {"id": "parent", "role": "wall", "polygon_2d": [[0,0],[10,0],[10,10],[0,10]]},
            {"id": "child", "role": "wall", "polygon_2d": [[0,-10],[10,-10],[10,0],[0,0]]},
        ],
        "edges": [{"id": "e1", "kind": "FOLD", "seg_2d": [[0,0],[10,0]],
                   "fold": {"mt_va": mt_va, "parent": "parent", "child": "child",
                            "target_angle_deg": angle}}],
        "features": [],
    }

print("== E1: 无 target_dir_3d 时 VALLEY vs MOUNTAIN 的折后位姿 ==")
for angle in (90.0, 60.0, 120.0, 45.0):
    wv = fold_all(from_raw(simple_ir("VALLEY", angle)))
    wm = fold_all(from_raw(simple_ir("MOUNTAIN", angle)))
    nv = np.cross(wv["child"][1]-wv["child"][0], wv["child"][2]-wv["child"][0]); nv /= np.linalg.norm(nv)
    nm = np.cross(wm["child"][1]-wm["child"][0], wm["child"][2]-wm["child"][0]); nm /= np.linalg.norm(nm)
    print(f"interior={angle:>5}  child_normal(VALLEY)={nv.round(4).tolist()}  child_normal(MOUNTAIN)={nm.round(4).tolist()}  "
          f"identical={np.allclose(wv['child'], wm['child'])}")

# 数学根因: pc 与 away 都在父平面内且都垂直折线 => 两候选 d·pc 恒相等
polys = {"parent": np.array([[0,0],[10,0],[10,10],[0,10]], float),
         "child": np.array([[0,-10],[10,-10],[10,0],[0,0]], float)}
seg = ((0.0,0.0),(10.0,0.0))
away = _away_net(polys["child"], seg); pc = _away_net(polys["parent"], seg)
axis = np.array([1.0,0,0])
for interior in (90.0, 60.0, 120.0):
    delta = math.pi - math.radians(interior)
    s = [float((_rot(axis, sg*delta) @ away) @ pc) for sg in (+1.0,-1.0)]
    print(f"  interior={interior}: score(sign=+1)={s[0]:+.6f}  score(sign=-1)={s[1]:+.6f}  -> tie={abs(s[0]-s[1])<1e-12}")

print("\n== E1b: SCORE mt_va 走哪条分支 ==")
try:
    ws = fold_all(from_raw(simple_ir("SCORE", 90.0)))
    wv = fold_all(from_raw(simple_ir("VALLEY", 90.0)))
    print("SCORE folded == VALLEY folded:", np.allclose(ws["child"], wv["child"]))
except Exception as e:
    print("SCORE ->", type(e).__name__, e)

print("\n== E1c: target_dir_3d 不垂直于铰链轴时是否报错 ==")
ir = simple_ir("VALLEY", 90.0)
ir["edges"][0]["fold"]["target_dir_3d"] = [0.0, -0.7, 0.7]   # 含轴(x)分量 0.7
try:
    w = fold_all(from_raw(ir))
    d = w["child"][2] - w["child"][0]
    tgt = np.array([0.0,-0.7,0.7]); tgt/=np.linalg.norm(tgt)
    print("no error. child away dir =", (d/np.linalg.norm(d)).round(4).tolist(),
          " target=", tgt.round(4).tolist(),
          " angle_err_deg=", round(math.degrees(math.acos(float((d/np.linalg.norm(d))@tgt))),2))
except Exception as e:
    print("->", type(e).__name__, e)

print("\n== E1d: mt_va 与 target_dir_3d 矛盾时是否报错 ==")
ir = simple_ir("MOUNTAIN", 90.0); ir["edges"][0]["fold"]["target_dir_3d"] = [0,1,0]
ir2 = simple_ir("VALLEY", 90.0); ir2["edges"][0]["fold"]["target_dir_3d"] = [0,1,0]
print("same tdir, MOUNTAIN vs VALLEY identical:", np.allclose(fold_all(from_raw(ir))["child"], fold_all(from_raw(ir2))["child"]))

print("\n== E1e: 同一 child 多条入边 (第二 parent) 是否被静默丢弃 ==")
ir = simple_ir("VALLEY", 90.0)
ir["panels"].append({"id": "p2", "role": "wall", "polygon_2d": [[20,0],[30,0],[30,10],[20,10]]})
# p2 与 child 不相邻 (悬空声明), 声称 child 同时挂在 p2 上
ir["edges"].append({"id": "e2", "kind": "FOLD", "seg_2d": [[20,0],[30,0]],
                    "fold": {"mt_va": "VALLEY", "parent": "p2", "child": "child", "target_dir_3d": [0,-1,0]}})
try:
    w = fold_all(from_raw(ir)); print("no error; edges consumed:", 2, " p2 placed:", "p2" in w, " p2 in edges tree? (p2 is never a child)")
except Exception as e:
    print("->", type(e).__name__, e)
