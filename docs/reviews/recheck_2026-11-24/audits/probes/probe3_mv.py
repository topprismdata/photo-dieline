"""E2: gable_top 的 mt_va 标注 vs 实际折向 (tdir 折叠结果) — 修正 away 方向."""
import numpy as np
from photo_dieline.core.ir import from_raw
from photo_dieline.folding.engine import fold_all
from photo_dieline.parametric import gable_top, base as T

def unit(v):
    return v / np.linalg.norm(v)

def A_normal(w):
    P = np.asarray(w, float)
    for i in range(1, len(P) - 1):
        c = np.cross(P[i] - P[0], P[i + 1] - P[0])
        if np.linalg.norm(c) > 1e-9:
            return unit(c)

def analyze(mod, params, label):
    raw = mod.build_ir(params); ir = from_raw(raw); w = fold_all(ir)
    rows = []
    for e in ir.edges:
        if e.target_dir_3d is None:
            continue
        C = np.asarray(w[e.child], float); net2 = ir.panel(e.child)["polygon_2d"]
        ia = next(i for i, p in enumerate(net2) if np.allclose(p, e.seg_2d[0]))
        ib = next(i for i, p in enumerate(net2) if np.allclose(p, e.seg_2d[1]))
        a_w, b_w = C[ia], C[ib]
        v = C.mean(0) - (a_w + b_w) / 2; ax = unit(b_w - a_w)
        away = unit(v - (v @ ax) * ax)
        n_A = A_normal(w[e.parent])
        s = float(away @ n_A)
        # 二面角 (两面板 away 方向夹角): 偏转角
        Pp = np.asarray(w[e.parent], float); pn = ir.panel(e.parent)["polygon_2d"]
        ja = next(i for i, p in enumerate(pn) if np.allclose(p, e.seg_2d[0]))
        jb = next(i for i, p in enumerate(pn) if np.allclose(p, e.seg_2d[1]))
        vp = Pp.mean(0) - (Pp[ja] + Pp[jb]) / 2; away_p = unit(vp - (vp @ ax) * ax)
        dev = np.degrees(np.arccos(float(np.clip(away @ away_p, -1, 1))))
        actA = "VALLEY" if s > 1e-9 else "MOUNTAIN"
        rows.append((e.id, e.parent, e.child, e.mt_va, actA, s, dev))
    print(f"\n[{label}]  A 面 = polygon_2d 逆时针法线 (net +z) = 盒内面")
    badA = badB = 0
    for eid, pa, ch, tag, actA, s, dev in rows:
        okA = tag == actA; okB = tag == ("MOUNTAIN" if actA == "VALLEY" else "VALLEY")
        badA += not okA; badB += not okB
        print(f"  {eid:8s} {pa:7s}->{ch:6s} 标注={tag:8s} 实际(A面看)={actA:8s} 偏转角={dev:6.1f}° d·n={s:+.3f}"
              f"{'  <-- A基准不一致' if not okA else ''}{'  <-- B基准不一致' if not okB else ''}")
    n = len(rows)
    print(f"  以 A 面(盒内) 为基准错标: {badA}/{n};  以 B 面(盒外/印刷面) 为基准错标: {badB}/{n}")

analyze(gable_top, None, "gable_top DEFAULTS")
analyze(gable_top, {"W": 57.15, "D": 57.15, "Hb": 75.0, "Hr": 20.25}, "gable_top halfpint")

raw = gable_top.build_ir(None); ir = from_raw(raw); w = fold_all(ir)
P = np.asarray(w["wallL"]); n = unit(np.cross(P[1]-P[0], P[2]-P[0])); center = np.vstack(list(w.values())).mean(0)
print("\n wallL A-面法线 =", n.round(3).tolist(), " wallL质心->盒中心 =", unit(center - P.mean(0)).round(3).tolist(),
      " => A 面朝盒内:", bool(n @ (center - P.mean(0)) > 0))

print("\n== E2b: 其它 gable 家族模板的标注基准 (只读对比) ==")
for cid in T.all_classes():
    if not cid.startswith("gable"):
        continue
    m = T.get(cid); params = dict(m.DEFAULTS)
    if hasattr(m, "class_params"): params.update(m.class_params(cid))
    analyze(m, params, cid)
