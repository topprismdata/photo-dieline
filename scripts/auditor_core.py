"""审计器 v2.1 — R09/WP-A0.1 (契约: docs/research/auditor_contract.md)
三层: L1 观测 → L2 契约(逐 prim) → L3 裁决 (PASS/FAIL/CONTRACT_UNKNOWN/NOT_APPLICABLE)"""
import numpy as np
from pxr import Usd, UsdGeom, Sdf, Gf, Vt

ATOL = 1e-6
DEG = 1e-9

def _face_components(tri):
    n = len(tri)
    adj = [[] for _ in range(n)]
    emap = {}
    for fi, (x, y, z) in enumerate(tri):
        for u, v in ((x, y), (y, z), (z, x)):
            key = (min(int(u), int(v)), max(int(u), int(v)))
            if key in emap: adj[fi].append(emap[key]); adj[emap[key]].append(fi)
            else: emap[key] = fi
    comp = [-1] * n; comps = []
    for i in range(n):
        if comp[i] >= 0: continue
        stack = [i]; comp[i] = len(comps); members = []
        while stack:
            f = stack.pop(); members.append(f)
            for g in adj[f]:
                if comp[g] < 0: comp[g] = len(comps); stack.append(g)
        comps.append(members)
    return comps

def _vertex_manifold_breaks(tri):
    """O6: 逐顶点扇形连通 — 闭壳=单环; 开壳=单链; >2 面共边=非流形"""
    inc_f = {}
    inc_e = {}
    for fi, (x, y, z) in enumerate(tri):
        xs = [int(x), int(y), int(z)]
        for i, v in enumerate(xs):
            w = xs[(i + 1) % 3]
            inc_f.setdefault(v, set()).add(fi)
            inc_e.setdefault(v, {}).setdefault(w, set()).add(fi)
            inc_e.setdefault(w, {}).setdefault(v, set()).add(fi)
    bad = 0
    for v, faces in inc_f.items():
        if len(faces) < 3: continue
        E = inc_e.get(v, {})
        if any(len(fs) > 2 for fs in E.values()):
            bad += 1; continue
        start = sorted(faces)[0]
        cur = start; prev_w = None; visited = {cur}
        while True:
            ws = sorted(emap := [w for w in {w for w, fs in E.items() if cur in fs} if w != prev_w])
            moved = False
            for w in ws:
                others = [f for f in E[w] if f != cur]
                if len(others) == 1 and others[0] not in visited:
                    prev_w = w; cur = others[0]; visited.add(cur); moved = True; break
            if not moved: break
            if cur == start: break
        if visited != faces: bad += 1
    return bad

def _edge_covered(u, v, pts, tri_edges, atol=1e-6):
    """原始多边形边 (u,v) 是否被三角边覆盖 (共线子边)."""
    U, V = pts[u], pts[v]
    d = V - U; L = np.linalg.norm(d)
    if L < atol: return True
    dn = d / L
    for (a, b) in tri_edges:
        A, B = pts[a], pts[b]
        if (np.allclose(A, U, atol=atol) and np.allclose(B, V, atol=atol)) or \
           (np.allclose(A, V, atol=atol) and np.allclose(B, U, atol=atol)): return True
        ta, tb = np.dot(A - U, dn), np.dot(B - U, dn)
        ra = np.linalg.norm(A - (U + ta * dn)); rb = np.linalg.norm(B - (U + tb * dn))
        if ra < atol and rb < atol and -atol <= min(ta, tb) and max(ta, tb) <= L + atol: return True
    return False

def audit_stage(stage, contract="UNKNOWN", prim_contracts=None, declared_seam_edges=None,
                ir_boundary=None, roundtrip_stage=None):
    de_seam = {(min(e), max(e)) for e in (declared_seam_edges or [])}
    pc = prim_contracts or {}
    out = {"L1": {"prims": {}}, "L3": {}, "issues": []}
    faces_total = 0
    prims = [(p, UsdGeom.Mesh(p)) for p in stage.Traverse() if p.IsA(UsdGeom.Mesh)]
    xf = UsdGeom.XformCache(Usd.TimeCode.Default())
    for prim, mesh in prims:
        nm = prim.GetPath().GetParentPath().name or prim.GetPath().name
        c = pc.get(nm, contract)
        R = {"contract": c, "findings": [], "normals": "NOT_APPLICABLE"}
        fv = np.asarray(mesh.GetFaceVertexCountsAttr().Get() or [])
        fvi = np.asarray(mesh.GetFaceVertexIndicesAttr().Get() or [])
        pts = np.asarray(mesh.GetPointsAttr().Get() or [])
        if len(fv) == 0: continue
        det = 1.0
        try:
            m = np.asarray(xf.GetLocalToWorldTransform(prim)).reshape(4, 4)
            det = float(np.linalg.det(m[:3, :3]))
        except Exception:
            pass
        if abs(det - 1.0) > 1e-6 and det < 0: R["mirrored"] = True
        if set(fv.tolist()) != {3}:
            R["findings"].append("topology:non-tri"); faces_total += 0; continue
        tri = fvi.reshape(-1, 3); faces_total += len(tri)
        # O12 3D 退化
        P = pts[tri]
        a3 = np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1)
        if np.any(a3 < 1e-7): R["findings"].append("geometry:degenerate-3d")
        # 有向边
        de = {}
        for x, y, z in tri:
            for u, v in ((int(x), int(y)), (int(y), int(z)), (int(z), int(x))):
                de[(u, v)] = de.get((u, v), 0) + 1
        dup = [e for e, cc in de.items() if cc > 1]
        if dup: R["findings"].append(f"topology:dup-directed-edges:{len(dup)}")
        boundary = [e for e in de if (e[1], e[0]) not in de]
        # 顶点流形
        vmb = _vertex_manifold_breaks(tri)
        if vmb > 0: R["findings"].append(f"vertex_manifold:nonfan:{vmb}")
        # 逐面连通分量壳
        comps = _face_components(tri)
        shells = []
        for members in comps:
            sub = tri[members]
            des, bnd = {}, []
            for x, y, z in sub:
                for u, v in ((int(x), int(y)), (int(y), int(z)), (int(z), int(x))):
                    des[(u, v)] = des.get((u, v), 0) + 1
            bnd = [e for e in des if (e[1], e[0]) not in des]
            closed = len(bnd) == 0
            shells.append({"closed": closed, "tris": len(sub), "boundary": len(bnd)})
            if closed:
                Pc = pts[sub]
                vol = np.einsum('ij,ij->i', Pc[:, 0], np.cross(Pc[:, 1], Pc[:, 2])).sum() / 6.0
                if vol <= 1e-9: R["findings"].append(f"winding:closed-vol:{vol:.4f}")
            else:
                bv = {}
                for u, v in bnd: bv[u] = bv.get(u, 0) + 1; bv[v] = bv.get(v, 0) + 1
                if any(cc != 2 for cc in bv.values()):
                    R["findings"].append("topology:boundary-not-walkable")
        R["shells"] = shells
        # IR 边界保持 (T23)
        if ir_boundary is not None:
            te = list(de.keys())
            for (u, v) in ir_boundary:
                if not _edge_covered(int(u), int(v), pts, te):
                    R["findings"].append(f"boundary_preserved:lost:{(int(u), int(v))}"); break
        # UV
        st = UsdGeom.PrimvarsAPI(mesh.GetPrim()).GetPrimvar("primvars:st")
        try:
            has_st = st is not None and st.GetAttr().IsDefined()
        except RuntimeError:
            has_st = False
        if not has_st:
            R["findings"].append("uv:no-st")
        else:
            stv = np.asarray(st.Get())
            idx = st.GetIndices()
            if idx is not None and len(idx) > 0:
                if len(stv) == 0 or int(np.max(idx)) >= len(stv) or len(idx) != len(fvi):
                    R["findings"].append("uv:indices-bad")
                    stv = None
                else:
                    stv = stv[np.asarray(idx)]
            if stv is not None:
                if st.GetInterpolation() != "faceVarying" or len(stv) != len(fvi):
                    R["findings"].append(f"uv:interp/len:{st.GetInterpolation()}:{len(stv)}!={len(fvi)}")
                else:
                    uvf = stv.reshape(-1, 3, 2)
                    a, b, cc = uvf[:, 0], uvf[:, 1], uvf[:, 2]
                    a2 = (b[:, 0] - a[:, 0]) * (cc[:, 1] - a[:, 1]) - (cc[:, 0] - a[:, 0]) * (b[:, 1] - a[:, 1])
                    if np.any(np.abs(a2) < DEG):
                        R["findings"].append(f"uv:degenerate-faces:{int(np.sum(np.abs(a2) < DEG))}")
                    elif np.any(a2 > 0) and np.any(a2 < 0):
                        R["findings"].append("uv:corner-swap-mixed-sign")
                    # L1 接缝分层
                    euv = {}
                    for fi, (x, y, z) in enumerate(tri):
                        for wi, (u, v) in enumerate(((x, y), (y, z), (z, x))):
                            euv.setdefault((min(int(u), int(v)), max(int(u), int(v))), []).append((fi, wi))
                    for key, occ in euv.items():
                        if len(occ) != 2: continue
                        (f1, w1), (f2, w2) = occ
                        p1, p2 = uvf[f1][w1], uvf[f1][(w1 + 1) % 3]
                        q1, q2 = uvf[f2][w2], uvf[f2][(w2 + 1) % 3]
                        e1 = np.allclose(p1, q1, atol=ATOL); e2 = np.allclose(p2, q2, atol=ATOL)
                        e3 = np.allclose(p1, q2, atol=ATOL); e4 = np.allclose(p2, q1, atol=ATOL)
                        if (e1 and e2) or (e3 and e4): continue  # 连续
                        declared = key in de_seam
                        R.setdefault("seams", []).append(
                            {"edge": list(key), "class": "EXPECTED_SEAM" if declared else
                             ("UNEXPECTED_SEAM" if (e1 or e2 or e3 or e4) else "UNEXPECTED_SEAM:full-mismatch"),
                             "partial": bool(e1 or e2 or e3 or e4)})
        # 法线
        if mesh.GetNormalsAttr().Get() is not None: R["normals"] = "present"
        out["L1"]["prims"][nm] = R
    # G05 往返
    rt = "NOT_RUN"
    if roundtrip_stage is not None:
        m2 = [(p, UsdGeom.Mesh(p)) for p in roundtrip_stage.Traverse() if p.IsA(UsdGeom.Mesh)]
        ok = len(prims) == len(m2)
        if ok:
            for (p1, x1), (p2, x2) in zip(prims, m2):
                def sig(x):
                    u = UsdGeom.PrimvarsAPI(x.GetPrim()).GetPrimvar("primvars:st")
                    return (np.asarray(x.GetPointsAttr().Get() or []).tobytes(),
                            np.asarray(x.GetFaceVertexIndicesAttr().Get() or []).tobytes(),
                            (np.asarray(u.Get() or []).tobytes() if u else b"<lost>"),
                            (u.GetInterpolation() if u else "<lost>"))
                if sig(x1) != sig(x2): ok = False
        rt = "PASS" if ok else "FAIL"
        for R in out["L1"]["prims"].values(): R["roundtrip"] = rt
    # L3 逐 prim 裁决
    overall = "PASS"
    for nm, R in out["L1"]["prims"].items():
        f = R.get("findings", [])
        if not f:
            R["verdict"] = "PASS" if R["contract"] != "UNKNOWN" else "CONTRACT_UNKNOWN:UNVERIFIED"
        else:
            R["verdict"] = "CONTRACT_UNKNOWN:FAIL" if R["contract"] == "UNKNOWN" else "FAIL"
        R["roundtrip"] = R.get("roundtrip", rt if rt != "NOT_RUN" else "NOT_RUN")
        if R["verdict"].startswith("FAIL"): overall = "FAIL"
        elif R["verdict"].startswith("CONTRACT_UNKNOWN") and overall == "PASS": overall = "CONTRACT_UNKNOWN"
        if R.get("roundtrip") == "FAIL": overall = "FAIL"
    L1 = out["L1"]
    L1["faces"] = faces_total
    L1["seams"] = {"declared": sum(1 for R in L1["prims"].values() for s in R.get("seams", []) if s["class"] == "EXPECTED_SEAM"),
                    "unexpected": sum(1 for R in L1["prims"].values() for s in R.get("seams", []) if s["class"] != "EXPECTED_SEAM"),
                    "partial_cracks": sum(1 for R in L1["prims"].values() for s in R.get("seams", []) if s["class"] == "UNEXPECTED_SEAM" and s["partial"])}
    out["L3"]["overall"] = overall
    out["L3"]["normals"] = "NOT_APPLICABLE (no explicit attr; derived)" if all(
        R["normals"] == "NOT_APPLICABLE" for R in out["L1"]["prims"].values()) and prims else "mixed/present"
    out["L3"]["prim_verdicts"] = {nm: {"verdict": R["verdict"], "contract": R["contract"],
                                        "findings": R.get("findings", []),
                                        "roundtrip": R.get("roundtrip", "NOT_RUN"),
                                        "mirrored": R.get("mirrored", False)} for nm, R in L1["prims"].items()}
    return out

def audit_file(path, **kw):
    return audit_stage(Usd.Stage.Open(path), **kw)
