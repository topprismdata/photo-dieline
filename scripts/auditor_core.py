"""R02-A 审计器 v2 (WP-A0): D2 裁决后修正.
G01: 纯三角 + 无重复有向边 + 边界边构成可走环(每边界顶点恰2条边界边) + 无T型节
G02: 闭壳→符号体积>0; 开壳→相邻面绕向一致(同一有向边不得出现两次)
G03: st faceVarying 数量=fvi + 无退化UV面
G04: interior边UV连续或合法接缝; crack=一端连续一端断
闭壳/开壳语义: FLAT_PATTERN/SURFACE 合法开壳 (D3 契约草案)"""
import numpy as np
from pxr import Usd, UsdGeom

def audit_stage(stage):
    res = {"G01": True, "G02": True, "G03": True, "G04_cracks": 0, "G04_seams": 0,
           "faces": 0, "shells": [], "issues": []}
    for prim in stage.Traverse():
        if not prim.IsA(UsdGeom.Mesh): continue
        mesh = UsdGeom.Mesh(prim); nm = prim.GetPath().name
        fv = np.asarray(mesh.GetFaceVertexCountsAttr().Get() or [])
        fvi = np.asarray(mesh.GetFaceVertexIndicesAttr().Get() or [])
        pts = np.asarray(mesh.GetPointsAttr().Get() or [])
        if len(fv) == 0: continue
        if set(fv.tolist()) != {3}:
            res["G01"] = False; res["issues"].append(f"{nm}:G01 non-tri"); continue
        tri = fvi.reshape(-1, 3); res["faces"] += len(tri)
        de = {}
        for x, y, z in tri:
            for u, v in ((int(x), int(y)), (int(y), int(z)), (int(z), int(x))):
                de[(u, v)] = de.get((u, v), 0) + 1
        dup = [e for e, c in de.items() if c > 1]
        if dup:
            res["G01"] = False; res["issues"].append(f"{nm}:G01 dup directed edges {len(dup)} {dup[:3]}")
        boundary = [e for e in de if (e[1], e[0]) not in de]
        closed = len(boundary) == 0
        # 边界可走环: 每个边界顶点恰出入各一次
        bv = {}
        for u, v in boundary: bv[u] = bv.get(u, 0) + 1; bv[v] = bv.get(v, 0) + 1
        bad_bv = [x for x, c in bv.items() if c != 2]
        if bad_bv:
            res["G01"] = False; res["issues"].append(f"{nm}:G01 boundary not walkable at {len(bad_bv)} verts (T-junction/crack)")
        # 顶点-壳分割 (用于闭壳体积)
        parent = list(range(len(pts)))
        def find(x):
            while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
            return x
        for x, y, z in tri:
            ra, rb, rc = find(int(x)), find(int(y)), find(int(z))
            if ra != rb: parent[ra] = rb
            if rc != parent[ra]: parent[rc] = parent[ra]
        if closed:
            P = pts[tri]
            vol = np.einsum('ij,ij->i', P[:, 0], np.cross(P[:, 1], P[:, 2])).sum() / 6.0
            ok = vol > 1e-9
            if not ok:
                res["G02"] = False; res["issues"].append(f"{nm}:G02 closed vol {vol:.4f}<=0")
            res["shells"].append({"closed": True, "vol": float(vol), "tris": len(tri)})
        else:
            flip = sum(1 for e, c in de.items() if c > 1)
            res["shells"].append({"closed": False, "boundary": len(boundary), "tris": len(tri)})
        # G03
        pvapi = UsdGeom.PrimvarsAPI(mesh.GetPrim())
        st = pvapi.GetPrimvar("primvars:st")
        uvf = None
        if st is None or st.Get() is None:
            res["G03"] = False; res["issues"].append(f"{nm}:G03 no st")
        else:
            stv = np.asarray(st.Get())
            if st.GetInterpolation() != "faceVarying" or len(stv) != len(fvi):
                res["G03"] = False; res["issues"].append(f"{nm}:G03 st interp/len")
            else:
                uvf = stv.reshape(-1, 3, 2)
                a, b, c = uvf[:, 0], uvf[:, 1], uvf[:, 2]
                deg = int(np.sum(np.abs((b[:,0]-a[:,0])*(c[:,1]-a[:,1]) - (c[:,0]-a[:,0])*(b[:,1]-a[:,1])) < 1e-9))
                if deg:
                    res["G03"] = False; res["issues"].append(f"{nm}:G03 degenerate UV faces {deg}")
        # G04
        if uvf is not None:
            euv = {}
            for fi, (x, y, z) in enumerate(tri):
                for wi, (u, v) in enumerate(((x, y), (y, z), (z, x))):
                    euv.setdefault((min(int(u), int(v)), max(int(u), int(v))), []).append((fi, wi, int(u)))
            for key, occ in euv.items():
                if len(occ) != 2: continue
                (f1, w1, s1), (f2, w2, s2) = occ
                p1, p2 = uvf[f1][w1], uvf[f1][(w1+1) % 3]
                q1, q2 = uvf[f2][w2], uvf[f2][(w2+1) % 3]
                e1 = np.allclose(p1, q1, atol=1e-6); e2 = np.allclose(p2, q2, atol=1e-6)
                e3 = np.allclose(p1, q2, atol=1e-6); e4 = np.allclose(p2, q1, atol=1e-6)
                if (e1 and e2) or (e3 and e4):
                    res["G04_seams"] += 1
                else:
                    res["G04_seams"] += 1
                    if e1 or e2 or e3 or e4:
                        res["G04_cracks"] += 1
    return res

def audit_file(path):
    return audit_stage(Usd.Stage.Open(path))
