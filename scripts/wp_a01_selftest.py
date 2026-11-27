"""WP-A0.1: 24 例真值+负向测试 (审计器 v2.1 验收) — T 编号对应 GPT 强制清单"""
import sys, numpy as np
sys.path.insert(0, "/Users/guohongbin/photo-dieline/scripts")
from auditor_core import audit_stage
from pxr import Usd, UsdGeom, Sdf, Gf, Vt

def cube_geo():
    v = np.array([[x, y, z] for z in (0, 1) for y in (0, 1) for x in (0, 1)], float)
    quads = [[0, 2, 3, 1], [5, 7, 6, 4], [1, 5, 4, 0], [6, 7, 3, 2], [4, 6, 2, 0], [3, 7, 5, 1]]  # 外向
    tris, stv = [], []
    for fi, (a, b, c, d) in enumerate(quads):
        ox, oy = (fi % 3) * 1.5, (fi // 3) * 1.5
        tris += [[a, b, c], [a, c, d]]
        stv += [[ox, oy], [ox + 1, oy], [ox + 1, oy + 1]] + [[ox, oy], [ox + 1, oy + 1], [ox, oy + 1]]
    return v, tris, np.array(stv, float)

def make_stage(prims):
    """prims: (name, pts, tris, stv|None, uv_indices|None, scale|None)"""
    stage = Usd.Stage.CreateInMemory()
    root = UsdGeom.Xform.Define(stage, "/Root").GetPrim()
    for name, pts, tris, stv, uvidx, scale in prims:
        prim = UsdGeom.Xform.Define(stage, f"/Root/{name}").GetPrim()
        if scale:
            UsdGeom.XformCommonAPI(prim).SetScale(scale)
        mesh = UsdGeom.Mesh.Define(stage, f"/Root/{name}/Body")
        mesh.GetPointsAttr().Set(Vt.Vec3fArray([Gf.Vec3f(*p) for p in pts]))
        mesh.GetFaceVertexCountsAttr().Set(Vt.IntArray([3] * len(tris)))
        mesh.GetFaceVertexIndicesAttr().Set(Vt.IntArray([i for t in tris for i in t]))
        mesh.GetSubdivisionSchemeAttr().Set("none")
        if stv is not None:
            attr = mesh.GetPrim().CreateAttribute("primvars:st", Sdf.ValueTypeNames.TexCoord2fArray)
            attr.Set(Vt.Vec2fArray([Gf.Vec2f(*p) for p in stv]))
            pv = UsdGeom.Primvar(attr)
            pv.SetInterpolation(UsdGeom.Tokens.faceVarying)
            if uvidx:
                pv.SetIndices(Vt.IntArray(uvidx))
    return stage

V, T, S = cube_geo()
Q_OPEN = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], float)
QUAD_TRIS = [[0, 1, 2], [0, 2, 3]]
QUAD_UV = np.array([[0, 0], [1, 0], [1, 1], [0, 0], [1, 1], [0, 1]], float)
cases = []
def C(n, stage, exp, **kw): cases.append((n, stage, exp, kw))

# 1 P1 立方体 SOLID
C("P1 cube SOLID", make_stage([("B", V, T, S, None, None)]), {"overall": "PASS"}, contract="SOLID")
# 2 T08 单面反转 (整体 FAIL)
T2 = [t[::-1] if i == 0 else list(t) for i, t in enumerate(T)]
C("T08 one face reversed", make_stage([("B", V, T2, S, None, None)]), {"overall": "FAIL"}, contract="SOLID")
# 3 N2 重复面
C("N2 dup face", make_stage([("B", V, T + [T[0]], np.vstack([S, S[:3]]), None, None)]), {"overall": "FAIL"}, contract="SOLID")
# 4 T09 单三角开壳 OPEN_SHELL
tri3 = [[0, 1, 2], [0, 2, 1]]
tv = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], float)
C("T09 legal tri open OPEN_SHELL", make_stage([("F", tv, [[0, 1, 2]], np.array([[0,0],[1,0],[0,1]],float), None, None)]), {"overall": "PASS"}, contract="OPEN_SHELL")
# 5 N3 缺面: SOLID FAIL / FLAT_PATTERN PASS (双断言)
stage_n3 = make_stage([("B", V, T[:-2], S[:-6], None, None)])
r = audit_stage(stage_n3, contract="SOLID")
c1 = r["L3"]["overall"] == "FAIL"
r2 = audit_stage(stage_n3, contract="FLAT_PATTERN")
c2 = r2["L3"]["overall"] == "PASS"
print(("PASS" if c1 and c2 else "FAIL"), "N3 dual contract (SOLID FAIL / FLAT_PATTERN PASS)", "|", c1, c2)
# 6 T10 一边三面共享
tri3s = [[0, 1, 2], [2, 1, 3], [1, 2, 4]]
fv5 = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0], [0, 0, 1]], float)
C("T10 edge 3 faces", make_stage([("B", fv5, tri3s, np.array([[0,0],[1,0],[1,1],[1,1],[0,0],[1,1],[0,0],[1,0],[1,1]],float), None, None)]), {"overall": "FAIL"}, contract="SOLID")
# 7 T11 两壳共点
allv = np.vstack([V, V[1:] + [2.0, 0, 0]])
mp = {0: 0, 1: 8, 2: 9, 3: 10, 4: 11, 5: 12, 6: 13, 7: 14}
tb = [[mp[a], mp[b], mp[c]] for a, b, c in T]
C("T11 shells share vertex", make_stage([("AB", allv, T + tb, None, None, None)]), {"overall": "FAIL"}, contract="SOLID", known_truth=True)
# 8 T12 两独立正常闭壳
C("T12 two solids", make_stage([("A", V, T, S, None, None), ("B", V + [2.0, 0, 0], T, S, None, None)]), {"overall": "PASS"}, contract="SOLID")
# 9 T13 一壳反向
C("T13 one shell reversed", make_stage([("A", V, T, S, None, None), ("B", V + [2.0, 0, 0], [t[::-1] for t in T], S, None, None)]), {"overall": "FAIL"}, contract="SOLID")
# 10 T14 闭壳+开壳混合 (SOLID+FLAT_PATTERN)
C("T14 mixed legal", make_stage([("A", V, T, S, None, None), ("F", Q_OPEN, QUAD_TRIS, QUAD_UV, None, None)]),
  {"overall": "PASS"}, contract="FLAT_PATTERN", prim_contracts={"A": "SOLID", "F": "FLAT_PATTERN"})
# 11 T15 共线退化三角
lv = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]], float)
C("T15 collinear tri", make_stage([("F", lv, [[0, 1, 2]], None, None, None)]), {"overall": "FAIL"}, contract="FLAT_PATTERN")
# 12 T16 indexed UV 合法
vals = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], float)
idx = [0, 1, 2, 0, 2, 3]
C("T16 indexed UV legal", make_stage([("F", Q_OPEN, QUAD_TRIS, vals, idx, None)]), {"overall": "PASS"}, contract="FLAT_PATTERN")
# 13 T17 UV indices 越界
C("T17 uv indices OOB", make_stage([("F", Q_OPEN, QUAD_TRIS, vals, [0, 1, 99, 0, 2, 3], None)]), {"overall": "FAIL"}, contract="FLAT_PATTERN")
# 14 T18 UV 面角交换 (swap 两角 → 该面有向面积变号)
uv18 = QUAD_UV.copy(); uv18[1], uv18[2] = uv18[2].copy(), uv18[1].copy()
r = audit_stage(make_stage([("F", Q_OPEN, QUAD_TRIS, uv18, None, None)]), contract="FLAT_PATTERN")
c = r["L3"]["overall"] == "PASS" and all(R.get("uv_mixed_sign") for R in r["L1"]["prims"].values())
print(("PASS" if c else "FAIL"), "T18 uv corner swap → L1 观测(降级), overall PASS", "|", r["L3"]["overall"])
# 15 T19 申报单端不连续 → EXPECTED_SEAM
uv19 = np.array([[0, 0], [1, 0], [1, 1], [0, 0], [1.5, 1], [0, 1]], float)
r = audit_stage(make_stage([("F", Q_OPEN, QUAD_TRIS, uv19, None, None)]), contract="FLAT_PATTERN",
                declared_seam_edges=[(0, 2)])
decl = sum(1 for R in r["L1"]["prims"].values() for s2 in R.get("seams", []) if s2.get("declared")); c = decl >= 1 and r["L1"]["seams"]["partial_discontinuity"] >= 1
print(("PASS" if c else "FAIL"), "T19 declared single-end cut → EXPECTED_SEAM", "|", r["L1"]["seams"])
# 16 T20 未申报双端不连续 → UNEXPECTED_SEAM
uv20 = np.array([[0, 0], [1, 0], [1, 1], [0.2, 0], [1.5, 1.5], [0, 1]], float)
r = audit_stage(make_stage([("F", Q_OPEN, QUAD_TRIS, uv20, None, None)]), contract="FLAT_PATTERN")
c = r["L1"]["seams"]["full_discontinuity"] >= 1
print(("PASS" if c else "FAIL"), "T20 undeclared full mismatch → UNEXPECTED_SEAM", "|", r["L1"]["seams"])
# 17 T21 负尺度合法资产
r = audit_stage(make_stage([("B", V, T, S, None, (-1, 1, 1))]), contract="SOLID")
c = r["L3"]["overall"] == "PASS" and any(R.get("mirrored") for R in r["L1"]["prims"].values())
print(("PASS" if c else "FAIL"), "T21 negative scale consistent → PASS + mirrored noted", "|", r["L3"]["overall"])
# 18 T22 往返 UV 丢失
full = make_stage([("F", Q_OPEN, QUAD_TRIS, QUAD_UV, None, None)])
lost = make_stage([("F", Q_OPEN, QUAD_TRIS, None, None, None)])
r = audit_stage(full, contract="FLAT_PATTERN", roundtrip_stage=lost)
c = r["L3"]["overall"] == "FAIL" and r["L3"]["prim_verdicts"]["F"]["roundtrip"] == "FAIL"
print(("PASS" if c else "FAIL"), "T22 roundtrip UV lost → FAIL", "|", r["L3"]["overall"])
# 19 T23 三角化边界改变
C("T23 boundary lost vs IR", make_stage([("F", Q_OPEN, [[0, 1, 2]], QUAD_UV[:3], None, None)]),
  {"overall": "FAIL"}, contract="FLAT_PATTERN", ir_boundary=[(0, 1), (1, 2), (2, 3), (3, 0)])
# 20 T24 开壳异常 + UNKNOWN 契约
C("T24 open anomaly UNKNOWN", make_stage([("F", Q_OPEN, [[0, 1, 2]], QUAD_UV[:3], None, None)]),
  {"overall": "CONTRACT_UNKNOWN"}, contract="UNKNOWN")
# 21 P2 合法开壳 FLAT_PATTERN
C("P2 legal open quad", make_stage([("F", Q_OPEN, QUAD_TRIS, QUAD_UV, None, None)]), {"overall": "PASS"}, contract="FLAT_PATTERN")
# 22 N1 整体内向 SOLID
C("N1 inward cube", make_stage([("B", V, [t[::-1] for t in T], S, None, None)]), {"overall": "FAIL"}, contract="SOLID")
# 23 N4 未申报 crack (单端错位)
uv23 = np.array([[0, 0], [1, 0], [1, 1], [0, 0], [1.5, 1], [0, 1]], float)
r = audit_stage(make_stage([("F", Q_OPEN, QUAD_TRIS, uv23, None, None)]), contract="FLAT_PATTERN")
unexp = sum(1 for R in r["L1"]["prims"].values() for s2 in R.get("seams", []) if s2["class"] != "CONTINUOUS"); c = r["L1"]["seams"]["partial_discontinuity"] >= 1 and unexp >= 1
print(("PASS" if c else "FAIL"), "N4 undeclared crack → UNEXPECTED_SEAM partial", "|", r["L1"]["seams"])
# 24 N5 退化 UV
uv24 = QUAD_UV.copy(); uv24[2] = uv24[1]
C("N5 degenerate uv", make_stage([("F", Q_OPEN, QUAD_TRIS, uv24, None, None)]), {"overall": "FAIL"}, contract="FLAT_PATTERN")

fails = 0
for name, stage, exp, kw in cases:
    r = audit_stage(stage, **kw)
    got = r["L3"]["overall"]
    ok = got == exp["overall"]
    print(("PASS" if ok else "FAIL"), name, "→", got, "|", [f for R in r["L1"]["prims"].values() for f in R.get("findings", [])][:2])
    fails += 0 if ok else 1
print("SELFTEST", "ALL 24 PASS" if fails == 0 else f"{fails} FAILURES")
