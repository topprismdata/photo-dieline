"""审计器 v2.1 — R09/WP-A0.1 (契约: docs/research/auditor_contract.md)
三层: L1 观测 → L2 契约(逐 prim) → L3 裁决 (PASS/FAIL/CONTRACT_UNKNOWN/NOT_APPLICABLE)"""
import numpy as np
from pxr import Usd, UsdGeom, Sdf, Gf, Vt

ATOL = 1e-6
DEG = 1e-9

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
    """O6: 逐顶点边组并查 — 同边-key 面互链; 分量数>1 = 非单扇 (链/环均合法)"""
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
        par = {f: f for f in faces}
        def find(x):
            while par[x] != x: par[x] = par[par[x]]; x = par[x]
            return x
        for w, fs in E.items():
            fs = [f for f in fs if f in par]
            for f in fs[1:]:
                ra, rb = find(fs[0]), find(f)
                if ra != rb: par[ra] = rb
        if len(set(find(f) for f in faces)) > 1: bad += 1
    return bad

def audit_stage(stage, contract="UNKNOWN", prim_contracts=None, declared_seam_edges=None,
                ir_boundary=None, roundtrip_stage=None, known_truth=False):
    de_seam = {(min(e), max(e)) for e in (declared_seam_edges or [])}
    pc = prim_contracts or {}
    out = {"L1": {"prims": {}}, "L3": {}, "issues": []}
    faces_total = 0
    prims = [(p, UsdGeom.Mesh(p)) for p in stage.Traverse() if p.IsA(UsdGeom.Mesh)]
    xf = UsdGeom.XformCache(Usd.TimeCode.Default())
    for prim, mesh in prims:
        own = prim.GetPath().name
        pname = prim.GetPath().GetParentPath().name
        nm = pname if (own == "Body" and pname not in ("", "/")) else own
        if nm in ("", "/"): nm = own
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
            if closed:
                Pc = pts[sub]
                vol = np.einsum('ij,ij->i', Pc[:, 0], np.cross(Pc[:, 1], Pc[:, 2])).sum() / 6.0
                shells.append({"closed": True, "tris": len(sub), "boundary": 0, "vol": float(vol)})
                if vol <= 1e-9: R["findings"].append(f"winding:closed-vol:{vol:.4f}")
            else:
                bv = {}
                for u, v in bnd: bv[u] = bv.get(u, 0) + 1; bv[v] = bv.get(v, 0) + 1
                if any(cc != 2 for cc in bv.values()):
                    R["findings"].append("topology:boundary-not-walkable")
                elif c == "SOLID":
                    R["findings"].append("closure:solid-with-open-boundary")
                shells.append({"closed": False, "tris": len(sub), "boundary": len(bnd)})
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
                        R["uv_mixed_sign"] = True  # L1 观测降级 (R09-02 仲裁 A): 待镜像契约登记后裁决
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
                        cls = "CONTINUOUS" if ((e1 and e2) or (e3 and e4)) else (
                            "PARTIAL_DISCONTINUITY" if (e1 or e2 or e3 or e4) else "FULL_DISCONTINUITY")
                        R.setdefault("seams", []).append(
                            {"edge": list(key), "class": cls, "declared": declared,
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
    # L3 逐 prim 裁决 (v2.2: 客观 FAIL / 契约依赖 / DISPUTED 分离)
    OBJECTIVE = ("topology:dup-directed-edges", "topology:nonmanifold-edges", "winding:same-direction-interior-edges",
                 "uv:degenerate-faces", "geometry:degenerate-3d", "winding:closed-vol",
                 "boundary_preserved", "uv:indices-bad", "uv:interp/len", "uv:no-st")
    overall = "PASS"
    for nm, R in out["L1"]["prims"].items():
        f = R.get("findings", [])
        obj = [x for x in f if any(x.startswith(p) for p in OBJECTIVE)]
        cdep = [x for x in f if x not in obj]
        disp = R.get("disputed", [])
        R["objective_findings"] = obj; R["contract_findings"] = cdep; R["disputed"] = disp
        R["roundtrip"] = R.get("roundtrip", rt if rt != "NOT_RUN" else "NOT_RUN")
        if obj or R["roundtrip"] == "FAIL":
            R["verdict"] = "FAIL"
        elif known_truth and disp:
            R["verdict"] = "FAIL"
        elif disp:
            R["verdict"] = "DISPUTED_FINDING"
        elif cdep:
            R["verdict"] = "CONTRACT_DEPENDENT_FAIL" if R["contract"] != "UNKNOWN" else "UNKNOWN"
        elif R["contract"] == "UNKNOWN":
            R["verdict"] = "CONTRACT_UNKNOWN:UNVERIFIED"
        else:
            R["verdict"] = "PASS"
        if R["verdict"] in ("FAIL", "CONTRACT_DEPENDENT_FAIL"): overall = "FAIL"
        elif R["verdict"] == "DISPUTED_FINDING" and overall == "PASS": overall = "DISPUTED"
        elif R["verdict"] in ("UNKNOWN", "CONTRACT_UNKNOWN:UNVERIFIED") and overall == "PASS": overall = "CONTRACT_UNKNOWN"
    L1 = out["L1"]
    L1["faces"] = faces_total
    L1["uv_mixed_sign_skus"] = sum(1 for R in L1["prims"].values() if R.get("uv_mixed_sign"))
    L1["disputed_prims"] = sum(1 for R in L1["prims"].values() if R.get("disputed"))
    L1["seams"] = {"continuous": sum(1 for R in L1["prims"].values() for s2 in R.get("seams", []) if s2["class"] == "CONTINUOUS"),
                    "partial_discontinuity": sum(1 for R in L1["prims"].values() for s2 in R.get("seams", []) if s2["class"] == "PARTIAL_DISCONTINUITY"),
                    "full_discontinuity": sum(1 for R in L1["prims"].values() for s2 in R.get("seams", []) if s2["class"] == "FULL_DISCONTINUITY")}
    out["L3"]["overall"] = overall
    out["L3"]["normals"] = "NOT_APPLICABLE (no explicit attr; derived)" if all(
        R["normals"] == "NOT_APPLICABLE" for R in out["L1"]["prims"].values()) and prims else "mixed/present"
    out["L3"]["prim_verdicts"] = {nm: {"verdict": R["verdict"], "contract": R["contract"],
                                        "findings": R.get("findings", []), "objective_findings": R.get("objective_findings", []), "contract_findings": R.get("contract_findings", []), "disputed": R.get("disputed", []),
                                        "roundtrip": R.get("roundtrip", "NOT_RUN"),
                                        "mirrored": R.get("mirrored", False)} for nm, R in L1["prims"].items()}
    return out

def audit_file(path, **kw):
    return audit_stage(Usd.Stage.Open(path), **kw)

def orientation_normalize_safe(pts, tri, atol=1e-6):
    """R09-11 G1-02: 方向规范化前置检查链 (五项), 全过才允许翻转.
    返回 (safe, reasons, vol)"""
    reasons = []
    pts = np.asarray(pts, float); tri = np.asarray(tri, int)
    # R1 有限坐标
    if not np.all(np.isfinite(pts)): reasons.append("non-finite coords")
    if len(tri) == 0: reasons.append("empty mesh")
    if reasons: return False, reasons, 0.0
    # R2 有效几何 (无退化三角)
    P = pts[tri]
    a3 = np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1)
    if np.any(a3 < 1e-9): reasons.append(f"degenerate tris {int(np.sum(a3 < 1e-9))}")
    # O2 无向边分类: n>=3 非流形边
    de = {}
    for x, y, z in tri:
        for u, v in ((int(x), int(y)), (int(y), int(z)), (int(z), int(x))):
            de[(u, v)] = de.get((u, v), 0) + 1
    und = {}
    for (u, v), c in de.items():
        k = (min(u, v), max(u, v)); und[k] = und.get(k, 0) + c
    nm = [k for k, c in und.items() if c >= 3]
    if nm: reasons.append(f"nonmanifold edges {len(nm)}")
    # R3 闭合 (全部 n=2)
    if any(c != 2 for c in und.values()): reasons.append("open boundary (not closed)")
    # R4 绕向一致 (n=2 内部边须反向: 同向即冲突)
    same = [k for k, c in und.items() if c == 2 and de.get((k[0], k[1]), 0) == 2]
    if same: reasons.append(f"winding-inconsistent edges {len(same)}")
    vol = float(np.einsum('ij,ij->i', P[:, 0], np.cross(P[:, 1], P[:, 2])).sum() / 6.0)
    if reasons: return False, reasons, vol
    return True, [], vol
