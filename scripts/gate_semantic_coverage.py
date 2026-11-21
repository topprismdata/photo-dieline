#!/usr/bin/env python3
"""gate_semantic_coverage: 语义分割覆盖门 — CPU 扫描线光栅化 (ESR Step D).

纪律 (simready-usd-pipeline-mac):
- 矩阵手性配套: view 空间 forward 为正, w = z_view, proj[3,2] = 1.0, 相机基填列
- 验证: 相机自身在 view 空间必须 [0,0,0]; 目标点 ndc 在 [-1,1]
- 取景: padding 1.0 (官方 0.280968 对标系数; 1.2 会偏 31%)
- 覆盖率只对单道具有效: 报告 unlabelled 占比 + dominant id
门: labelled_frac >= 0.98 (SL.001: 每个可渲染像素可解析到 label)
用法: python3 scripts/gate_semantic_coverage.py
"""
import json
from pathlib import Path

import numpy as np
from pxr import Usd, UsdGeom

ROOT = Path(__file__).parent.parent
USD_DIR = ROOT / "assets/sku_usd"
RES = 256


def gather(stage):
    """(verts_world, tri_indices, tri_prim_path) 聚合."""
    # 官方 SimReady 资产 obj 层 instanceable=true; 嵌套实例代理在 pip usd-core
    # TraverseAll 下不可见 (嵌套代理遍历缺口) — 内存解除 instancing, 不落盘
    for prim in stage.TraverseAll():
        if prim.IsInstance():
            prim.SetInstanceable(False)
    verts, tris, paths = [], [], []
    off = 0
    for prim in stage.TraverseAll():
        if not prim.IsA(UsdGeom.Mesh):
            continue
        mesh = UsdGeom.Mesh(prim)
        pts = np.array(mesh.GetPointsAttr().Get(), dtype=float)
        m = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
        M = np.array(m, dtype=float)
        pw = pts @ M[:3, :3].T + M[3, :3]
        counts = np.array(mesh.GetFaceVertexCountsAttr().Get())
        idx = np.array(mesh.GetFaceVertexIndicesAttr().Get())
        i0 = 0
        for c in counts:
            face = idx[i0:i0 + c]
            for k in range(1, c - 1):
                tris.append([off + face[0], off + face[k], off + face[k + 1]])
                paths.append(str(prim.GetPath()))
            i0 += c
        verts.append(pw)
        off += len(pw)
    return np.vstack(verts), np.array(tris), paths


def look_at(eye, target, up=np.array([0.0, 0.0, 1.0])):
    f = target - eye
    f = f / np.linalg.norm(f)          # forward 为正 (手性纪律)
    s = np.cross(f, up)
    s = s / (np.linalg.norm(s) + 1e-12)
    u = np.cross(s, f)
    view = np.eye(4)
    view[:3, :3] = np.stack([s, u, f], axis=1)  # 列赋值 (坑位纪律)
    view[:3, 3] = -view[:3, :3].T @ eye
    return view


def resolve_label(prim):
    """逐 prim 标签解析: 自身→祖先链找 semantics:labels:* 裸属性 (官方样例写法)."""
    p = prim
    while p.IsValid():
        for attr in p.GetAttributes():
            name = attr.GetName()
            if name.startswith("semantics:labels:") and attr.Get() is not None:
                return name.removeprefix("semantics:labels:"), str(attr.Get())
        p = p.GetParent()
    return None


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--usd-dir", default=str(USD_DIR))
    ap.add_argument("--out", default=str(ROOT / "data/shelf_twin/gate_semantic_coverage.json"))
    args = ap.parse_args()
    results = []
    for f in sorted(Path(args.usd_dir).glob("*.usd*")):
        stage = Usd.Stage.Open(str(f))
        verts, tris, paths = gather(stage)
        uniq = sorted(set(paths))
        pid = {p: i for i, p in enumerate(uniq)}
        tri_pid = np.array([pid[p] for p in paths])
        # SL.001 真解析: 每 prim 走祖先链找标签; 无标签 prim 的像素计 unlabelled
        labels = {}
        for p in uniq:
            prim = stage.GetPrimAtPath(p)
            got = resolve_label(prim) if prim.IsValid() else None
            labels[p] = got
        resolved_ids = {pid[p] for p in uniq if labels[p] is not None}
        tax_seen = sorted({t for t, _ in labels.values() if t})

        # auto-frame: padding 1.0 (取景标定纪律)
        mn, mx = verts.min(0), verts.max(0)
        center = (mn + mx) / 2
        radius = float(np.linalg.norm(mx - mn)) / 2
        fov = 40.0
        dist = radius / np.tan(np.radians(fov / 2)) * 1.0
        eye = center + np.array([0.0, -dist * 0.85, dist * 0.5])
        view = look_at(eye, center)
        # 验证: 相机在 view 空间必须 [0,0,0]
        assert np.allclose((view @ np.hstack([eye, [1]]))[:3], 0, atol=1e-9)

        v_cam = (view @ np.hstack([verts, np.ones((len(verts), 1))]).T).T[:, :3]
        fcl = 1.0 / np.tan(np.radians(fov / 2))
        z = v_cam[:, 2]
        x_ndc = np.where(z > 1e-6, fcl * v_cam[:, 0] / np.maximum(z, 1e-9), 0)
        y_ndc = np.where(z > 1e-6, fcl * v_cam[:, 1] / np.maximum(z, 1e-9), 0)
        px = (x_ndc * 0.5 + 0.5) * RES
        py = (1 - (y_ndc * 0.5 + 0.5)) * RES

        label = np.full((RES, RES), -1, np.int32)
        depth = np.full((RES, RES), 1e9, np.float32)
        for ti, (a, b, c) in enumerate(tris):
            xs = np.array([px[a], px[b], px[c]])
            ys = np.array([py[a], py[b], py[c]])
            zs = np.array([z[a], z[b], z[c]])
            if (zs <= 1e-6).any():
                continue
            x0, x1 = int(max(0, xs.min())), int(min(RES - 1, xs.max()) + 1)
            y0, y1 = int(max(0, ys.min())), int(min(RES - 1, ys.max()) + 1)
            if x1 <= x0 or y1 <= y0:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
            d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
            if abs(d) < 1e-9:
                continue
            w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
            w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d
            w2 = 1 - w0 - w1
            mask = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not mask.any():
                continue
            zi = w0 * zs[0] + w1 * zs[1] + w2 * zs[2]
            sub_d = depth[y0:y1, x0:x1]
            upd = mask & (zi < sub_d)
            sub_d[upd] = zi[upd]
            lab = label[y0:y1, x0:x1]
            lab[upd] = tri_pid[ti]

        covered = label >= 0
        proj_area = np.count_nonzero(covered)
        if proj_area == 0:
            results.append({"sku": f.stem, "pass": False, "err": "no projection"})
            continue
        # SL.001: 每个覆盖像素经 prim→祖先链解析到标签; 未解析 prim 的像素计 unlabelled
        labelled_px = int(np.isin(label[covered], list(resolved_ids)).sum())
        on_coverage = float(covered.mean())
        res_pix = label[covered][np.isin(label[covered], list(resolved_ids))]
        dominant = int(np.bincount(res_pix).argmax()) if len(res_pix) else -1
        unlabelled_prims = sorted(p for p in uniq if labels[p] is None)
        labelled_frac = labelled_px / proj_area
        passed = (labelled_frac >= 0.98) and (0.05 <= on_coverage <= 0.60)
        results.append({"sku": f.stem, "pass": bool(passed),
                        "on_coverage": round(on_coverage, 4),
                        "labelled_frac": round(labelled_frac, 4),
                        "taxonomies": tax_seen,
                        "unlabelled_prims": unlabelled_prims[:5],
                        "dominant_id": dominant,
                        "padding": 1.0})
        print(f"{'PASS' if passed else 'FAIL'} {f.stem}: on_cov={on_coverage:.3f} "
              f"labelled={labelled_frac:.3f} tax={tax_seen} "
              f"unlabelled={len(unlabelled_prims)}")
    n_ok = sum(r["pass"] for r in results)
    report = {"schema": "semantic-coverage-gate/1.1", "res": RES, "padding": 1.0,
              "results": results, "ok": n_ok, "fail": len(results) - n_ok}
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(f"COVERAGE_DONE ok={n_ok} fail={len(results) - n_ok}")


if __name__ == "__main__":
    main()
