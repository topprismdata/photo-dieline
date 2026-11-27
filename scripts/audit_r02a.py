"""R02-A v2: 区分闭壳/开壳. 闭壳: 体积绕向; 开壳: 有向一致性+合法边界."""
import json, glob, os, random
import numpy as np
from pxr import Usd, UsdGeom

def analyze(path):
    r = {"file": os.path.basename(os.path.dirname(path))}
    stage = Usd.Stage.Open(path)
    meshes = [(p, UsdGeom.Mesh(p)) for p in stage.Traverse() if p.IsA(UsdGeom.Mesh)]
    issues = []
    g01 = g02 = g03 = True
    seams = cracks = 0; faces_total = 0
    for prim, mesh in meshes:
        nm = prim.GetPath().name
        fv  = np.asarray(mesh.GetFaceVertexCountsAttr().Get() or [])
        fvi = np.asarray(mesh.GetFaceVertexIndicesAttr().Get() or [])
        pts = np.asarray(mesh.GetPointsAttr().Get() or [])
        if len(fv) == 0: continue
        tri = fvi.reshape(-1, 3); faces_total += len(tri)
        if set(fv.tolist()) != {3}:
            g01 = False; issues.append(f"{nm}:G01 non-tri {sorted(set(fv.tolist()))[:4]}"); continue
        # 有向边统计
        de = {}
        for fi, (x,y,z) in enumerate(tri):
            for u,v2 in ((x,y),(y,z),(z,x)):
                de[(int(u),int(v2))] = de.get((int(u),int(v2)), 0) + 1
        dup = [e for e,c in de.items() if c > 1]
        if dup:
            g01 = False; issues.append(f"{nm}:G01 duplicate directed edges {len(dup)}")
        boundary = [e for e in de if (e[1],e[0]) not in de]
        interior_bad = [e for e in de if (e[1],e[0]) in de and any(c>1 for c in [de[e]])]
        closed = len(boundary) == 0
        r.setdefault("shells", []).append({"closed": closed, "tris": len(tri), "boundary_edges": len(boundary)})
        if not closed and len(boundary) % 2 != 0:
            g01 = False; issues.append(f"{nm}:G01 odd boundary edges {len(boundary)} (crack)")
        # G02: 闭壳→符号体积; 开壳→跨共享边法向一致性
        if closed:
            P = pts[tri]
            vol = np.einsum('ij,ij->i', P[:,0], np.cross(P[:,1], P[:,2])).sum() / 6.0
            if vol <= 1e-9:
                g02 = False; issues.append(f"{nm}:G02 closed shell vol {vol:.2f} <= 0 (inward)")
        else:
            bad = 0
            for e in de:
                if (e[1],e[0]) in de:  # interior
                    pass
            # 方向一致性: 每条 interior 边在两个三角中方向相反 → 已由 de 定义保证; 检查法向翻转: 相邻三角共享边端点顺序
            owner = {}
            for fi, (x,y,z) in enumerate(tri):
                for u,v2 in ((x,y),(y,z),(z,x)):
                    owner.setdefault(tuple(sorted((int(u),int(v2)))), []).append((fi, int(u)))
            flip = 0
            for key, occ in owner.items():
                if len(occ) == 2 and occ[0][1] == occ[1][1]:
                    flip += 1  # 同端点作为起点出现两次 = 绕向翻转
            if flip > 0:
                g02 = False; issues.append(f"{nm}:G02 open-shell flipped adjacent tris {flip}")
        # G03
        pvapi = UsdGeom.PrimvarsAPI(mesh.GetPrim())
        st = pvapi.GetPrimvar("primvars:st")
        if st is None or st.Get() is None:
            g03 = False; issues.append(f"{nm}:G03 no st")
        else:
            stv = np.asarray(st.Get())
            if st.GetInterpolation() != "faceVarying" or len(stv) != len(fvi):
                g03 = False; issues.append(f"{nm}:G03 st interp {st.GetInterpolation()} len {len(stv)} != {len(fvi)}")
            else:
                uvf = stv.reshape(-1, 3, 2)
                a,b,c = uvf[:,0], uvf[:,1], uvf[:,2]
                area2 = (b[:,0]-a[:,0])*(c[:,1]-a[:,1]) - (c[:,0]-a[:,0])*(b[:,1]-a[:,1])
                deg = int(np.sum(np.abs(area2) < 1e-9))
                if deg: g03 = False; issues.append(f"{nm}:G03 degenerate UV faces {deg}")
                # G04 crack 检测: interior 边一端UV连续另一端断
                owner_uv = {}
                for fi, (x,y,z) in enumerate(tri):
                    for wi,(u,v2) in enumerate(((x,y),(y,z),(z,x))):
                        owner_uv.setdefault(tuple(sorted((int(u),int(v2)))), []).append((fi, wi))
                for key, occ in owner_uv.items():
                    if len(occ) != 2: continue
                    (f1,w1),(f2,w2) = occ
                    p1,p2 = uvf[f1][w1], uvf[f1][(w1+1)%3]
                    q1,q2 = uvf[f2][w2], uvf[f2][(w2+1)%3]
                    if np.allclose(p1,q2,atol=1e-6) and np.allclose(p2,q1,atol=1e-6): continue
                    if np.allclose(p1,q1,atol=1e-6) and np.allclose(p2,q2,atol=1e-6):
                        seams += 1; continue
                    seams += 1
                    if np.allclose(p1,q2,atol=1e-6) or np.allclose(p1,q1,atol=1e-6):
                        cracks += 1
    r.update({"G01":g01,"G02":g02,"G03":g03,"seams":seams,"cracks":cracks,"faces":faces_total,"issues":issues[:6]})
    # G05
    stage2 = Usd.Stage.Open(path)
    m2 = [(p, UsdGeom.Mesh(p)) for p in stage2.Traverse() if p.IsA(UsdGeom.Mesh)]
    same = len(m2) == len(meshes)
    for (p1,mm1),(p2,mm2) in zip(meshes,m2):
        if (np.asarray(mm1.GetPointsAttr().Get()).tobytes() != np.asarray(mm2.GetPointsAttr().Get()).tobytes()): same = False
    r["G05"] = same
    return r

skus = sorted(glob.glob("output/pack10k_scale10k/*/model.usdc"))
fam_first, seen = [], set()
for p in skus:
    fam = os.path.basename(os.path.dirname(p)).split("_v")[0]
    if fam not in seen: seen.add(fam); fam_first.append(p)
random.seed(42)
sample = fam_first + random.sample([p for p in skus if p not in set(fam_first)], 30)
out = []
for i,p in enumerate(sample):
    try: out.append(analyze(p))
    except Exception as e: out.append({"file": p, "error": str(e)[:80]})
    if (i+1) % 20 == 0: print(f"... {i+1}/{len(sample)}", flush=True)
json.dump(out, open("/tmp/r02a_results.json","w"), ensure_ascii=False, indent=1)
g1 = sum(1 for r in out if r.get("G01")); g2 = sum(1 for r in out if r.get("G02")); g3 = sum(1 for r in out if r.get("G03")); g5 = sum(1 for r in out if r.get("G05"))
print(f"audited {len(out)} | G01 {g1} | G02 {g2} | G03 {g3} | G05 {g5} | seams {sum(r.get('seams',0) for r in out)} | cracks {sum(r.get('cracks',0) for r in out)}")
for r in out:
    if r.get("issues") or r.get("error"): print(r["file"], "|", "; ".join(r.get("issues", [])) or r.get("error"))
