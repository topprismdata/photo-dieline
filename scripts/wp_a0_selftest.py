"""WP-A0: 合成真值 + 负向测试 — 审计器本身验收."""
import sys, numpy as np
sys.path.insert(0, "/tmp")
from auditor_core import audit_stage
from pxr import Usd, UsdGeom, UsdGeom as UG, Sdf, Gf, Vt

def make_stage(meshes):
    stage = Usd.Stage.CreateInMemory()
    for name, pts, tris, stv in meshes:
        mesh = UsdGeom.Mesh.Define(stage, f"/{name}")
        mesh.GetPointsAttr().Set(pts)
        mesh.GetFaceVertexCountsAttr().Set([3]*len(tris))
        mesh.GetFaceVertexIndicesAttr().Set([i for t in tris for i in t])
        mesh.GetSubdivisionSchemeAttr().Set("none")
        if stv is not None:
            attr = mesh.GetPrim().CreateAttribute("primvars:st", Sdf.ValueTypeNames.TexCoord2fArray)
            attr.Set(Vt.Vec2fArray([Gf.Vec2f(*p) for p in stv]))
            pv = UsdGeom.Primvar(attr)
            pv.SetInterpolation(UsdGeom.Tokens.faceVarying)
    return stage

def cube(s=1.0, inward=False, uv="planar"):
    v = np.array([[x,y,z] for z in (0,s) for y in (0,s) for x in (0,s)], float)
    quads = [[0,2,3,1],[5,7,6,4],[1,5,4,0],[6,7,3,2],[4,6,2,0],[3,7,5,1]]  # outward
    tris = []
    for q in quads:
        a,b,c,d = q
        tris += [[a,b,c],[a,c,d]]
    if inward: tris = [t[::-1] for t in tris]
    stv = []
    for fi, q in enumerate(quads):
        ox = (fi % 3) * 1.5; oy = (fi // 3) * 1.5
        stv += [[ox,oy],[ox+1,oy],[ox+1,oy+1]] + [[ox,oy],[ox+1,oy+1],[ox,oy+1]]
    stv = np.array(stv, float)
    return v, tris, stv

cases = []
v,t,st = cube(); cases.append(("P1 cube OK", make_stage([("B", v, t, st)]), {"G01":True,"G02":True,"G03":True,"cracks_ge":0}))
v2,t2,st2 = cube(); cases.append(("N1 inward", make_stage([("B", v2, [x[::-1] for x in t2], st2)]), {"G01":True,"G02":False}))
v3,t3,st3 = cube(); t3d = t3 + [t3[0]]; cases.append(("N2 dup face", make_stage([("B", v3, t3d, np.vstack([st3, st3[:3]]))]), {"G01":False}))
v4,t4,st4 = cube(); cases.append(("N3 missing face", make_stage([("B", v4, t4[:-2], st4[:-6])]), {"G01":True,"G02":True}))
v5,t5,st5 = cube()
st5b = st5.copy(); st5b[4][0] += 0.5  # crack: 对角边 tri1 侧端点错位 (ua 连续, uc 断开)
cases.append(("N4 uv crack", make_stage([("B", v5, t5, st5b)]), {"cracks_ge":1}))
v6,t6,st6 = cube(); st6b = st6.copy(); st6b[1][1] = st6b[1][0]  # degenerate UV face
cases.append(("N5 degenerate uv", make_stage([("B", v6, t6, st6b)]), {"G03":False}))
# N6 合法开壳: 单面两三角 (FLAT_PATTERN 合法)
cases.append(("P2 legal open quad", make_stage([("F", np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0]],float), [[0,1,2],[0,2,3]], np.array([[0,0],[1,0],[1,1],[0,0],[1,1],[0,1]],float))]), {"G01":True,"G02":True,"G03":True}))

fails = 0
for name, stage, expect in cases:
    r = audit_stage(stage)
    ok = True
    for k, want in expect.items():
        got = r["G04_cracks"] if k == "cracks_ge" else r.get(k)
        if k == "cracks_ge": ok = ok and got >= want
        else: ok = ok and (got == want)
    print(("PASS " if ok else "FAIL "), name, "| G01", r["G01"], "G02", r["G02"], "G03", r["G03"], "cracks", r["G04_cracks"], "|", r["issues"][:2])
    fails += 0 if ok else 1
print("SELFTEST", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
