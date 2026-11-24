"""E6-E8 + 杂项探针 (只读; CLI 输出写到 /tmp/pd_recheck/cli_out)."""
import copy, json, os, subprocess, sys, hashlib, tempfile, warnings
from pathlib import Path
import numpy as np
from PIL import Image
from photo_dieline.core.ir import from_raw, build, validate_dict, ARError, GeometryIR
from photo_dieline.export import svg as svgx, pdf as pdfx
from photo_dieline.qa.pipeline import run_qa, _intersect3d
from photo_dieline.qa import pipeline as Q
from photo_dieline.parametric import gable_top
from photo_dieline.cli import _layer_geo

REPO = "/Users/guohongbin/photo-dieline"; OUT = Path("/tmp/pd_recheck/cli_out"); OUT.mkdir(parents=True, exist_ok=True)
def art(raw):
    ir = from_raw(raw); x0,y0,x1,y1 = svgx.net_bbox(ir)
    return ir, svgx.render(ir, x1-x0, y1-y0), pdfx.build_pdf(ir, x1-x0, y1-y0, _layer_geo(ir))

print("== E6: IR features 是否驱动导出 ==")
base = art(gable_top.build_ir(None))
m = copy.deepcopy(gable_top.build_ir(None))
for f in m["features"]:
    if f["id"] == "f_bleed": f["offset_mm"] = 10.0
    if f["id"] == "f_check": f["length_mm"] = 30.0
    if f["id"] == "f_glue": f["panel_id"] = "front"
m2 = copy.deepcopy(gable_top.build_ir(None)); m2["features"] = []      # 整个 features 数组删空
a2 = art(m); a3 = art(m2)
print(" 改 f_bleed.offset_mm=10 / f_check.length_mm=30 / f_glue.panel_id=front  => SVG unchanged:", a2[1] == base[1], " PDF unchanged:", a2[2] == base[2])
print(" features = [] (空数组)                                              => SVG unchanged:", a3[1] == base[1], " PDF unchanged:", a3[2] == base[2],
      " schema valid:", (validate_dict({k:v for k,v in m2.items() if k != '_derived'}) is None))

print("\n== E7: 照片内容对输出的影响 (两张不同的 ≥1000px 图) ==")
spec = json.load(open(f"{REPO}/examples/gable_top/spec.json"))
d1, d2 = OUT / "p1.png", OUT / "p2.png"
Image.new("RGB", (1200, 1600), (10, 200, 30)).save(d1)
Image.effect_noise((1600, 1200), 80).convert("RGB").save(d2)
res = []
for tag, ph, sp in (("blank-green", d1, spec), ("noise", d2, spec), ("real-photo", Path(f"{REPO}/examples/gable_top/reference_photo.jpg"), spec)):
    o = OUT / tag; r = subprocess.run([sys.executable, "-m", "photo_dieline.cli", "build", "--spec", f"{REPO}/examples/gable_top/spec.json", "--photo", str(ph), "--out", str(o)], capture_output=True, text=True)
    rep = json.load(open(o / "qa-report.json")); irj = json.load(open(o / "geometry-ir.json"))
    res.append((tag, r.returncode, rep["status"], hashlib.sha256((o/"dieline.svg").read_bytes()).hexdigest()[:16], hashlib.sha256((o/"dieline.pdf").read_bytes()).hexdigest()[:16],
                hashlib.sha256(json.dumps({k:v for k,v in irj.items() if k!='package'}).encode()).hexdigest()[:16], irj["package"]["photo"]["path"]))
    print(f"  photo={tag:<11} rc={r.returncode} status={rep['status']}  svg.sha={res[-1][3]}  pdf.sha={res[-1][4]}  IR(non-package).sha={res[-1][5]}  photo.path={irj['package']['photo']['path']!r}")
print("  => 3 张完全不同的照片, 输出 SVG/PDF/IR(除 package.photo) 逐字节相同:", len({r[3] for r in res}) == 1 and len({r[4] for r in res}) == 1 and len({r[5] for r in res}) == 1)

print("\n== E7b: 照片格式门 (非照片格式/非包装内容) ==")
for name, mk in (("gif", lambda p: Image.new("P", (1200, 1600)).save(p, "GIF")), ("16px-wide-tall", lambda p: Image.new("RGB", (1000, 3)).save(p)), ("1000x1000", lambda p: Image.new("RGB", (1000, 1000)).save(p))):
    p = OUT / f"fmt_{name}.{'gif' if name=='gif' else 'png'}"; mk(p)
    try: build({}, p, gable_top.build_ir(None)); print(f"  {name}: ACCEPTED")
    except Exception as e: print(f"  {name}: rejected ({type(e).__name__}: {str(e)[:60]})")

print("\n== E8: CLI spec 字段的处理 ==")
spec2 = copy.deepcopy(spec); spec2["package"] = "FEFCO_0201_not_supported"; spec2["measurements"] = [
    {"name": "W", "value_mm": 45.0, "status": "MEASURED"}, {"name": "Widht", "value_mm": 45.0, "status": "MEASURED"}]
spec2["params"]["W"] = 50.0
p = OUT / "spec_mismatch.json"; p.write_text(json.dumps(spec2))
r = subprocess.run([sys.executable, "-m", "photo_dieline.cli", "build", "--spec", str(p), "--photo", str(d1), "--out", str(OUT / "mismatch")], capture_output=True, text=True)
irj = json.load(open(OUT / "mismatch" / "geometry-ir.json")); rep = json.load(open(OUT / "mismatch" / "qa-report.json"))
print(f"  package='FEFCO_0201_not_supported' + params.W=50 vs measurements W=45 MEASURED (+ typo 'Widht')  => rc={r.returncode} status={rep['status']}")
print(f"     IR package.type={irj['package']['type']!r} template={irj['package']['template']['id']!r} params.W={irj['package']['params']['W']} params_evidence={irj['package']['params_evidence']}")
print("     stderr mentions mismatch/unknown package:", any(k in (r.stdout + r.stderr).lower() for k in ("mismatch", "unknown", "fecco", "不一致")))

print("\n== 杂项 ==")
ir = base[0]
try: ir.folds_from("wallL")
except Exception as e: print(f" ir.folds_from('wallL') -> {type(e).__name__}: {e}")
# G06 实际检查对数
world_ids = [p["id"] for p in ir.panels]; allowed = gable_top.allowed_overlap() | Q.ALLOWED_OVERLAP
from photo_dieline.qa.pipeline import _panels_share_fold
roles = {p["id"]: p["role"] for p in ir.panels}
pairs = [(a, b) for i, a in enumerate(world_ids) for b in world_ids[i+1:]]
skipped_allowed = [p for p in pairs if frozenset(p) in allowed]; skipped_adj = [p for p in pairs if frozenset(p) not in allowed and _panels_share_fold(ir, *p)]
skipped_flap = [p for p in pairs if frozenset(p) not in allowed and not _panels_share_fold(ir, *p) and roles[p[0]] == "flap" and roles[p[1]] == "flap"]
print(f" G06: reported checked_pairs={len(pairs)}; actually skipped: allowed={len(skipped_allowed)} adjacent={len(skipped_adj)} flap-flap={len(skipped_flap)} => really tested {len(pairs)-len(skipped_allowed)-len(skipped_adj)-len(skipped_flap)}")
# _intersect3d 探针
sq = lambda c, n: np.array([[c[0]-n, c[1]-n, c[2]], [c[0]+n, c[1]-n, c[2]], [c[0]+n, c[1]+n, c[2]], [c[0]-n, c[1]+n, c[2]]], float)
A = sq((0, 0, 0), 10)
print(" _intersect3d: 小面板A(20x20@z=0) vs 倾斜大板B 穿过 z=0 于 x∈[100,110] (不相交):", _intersect3d(A, np.array([[80,0,-50],[140,0,50],[140,40,50],[80,40,-50]], float)), " <- 假阳性(投影放大)")
print(" _intersect3d: A vs 近平行板B (最近 5mm, 不相交):", _intersect3d(A, np.array([[-10,0,5.0],[10,0,5.3],[10,20,5.3],[-10,20,5.0]], float)), " <- 正确 False")
print(" _intersect3d: A vs 近平行板B 1° 且在 A 范围内穿插 (d0=0.05):", _intersect3d(A, np.array([[-10,0,0.05],[10,0,0.4],[10,20,0.4],[-10,20,0.05]], float)), " <- 真穿插(两板交叉)")
# G03: 点接触
from shapely.geometry import Polygon
from shapely.ops import unary_union
u = unary_union([Polygon([[0,0],[10,0],[10,10],[0,10]]), Polygon([[10,10],[20,10],[20,20],[10,20]])]).buffer(0)
print(f" G03 union of two panels touching at ONE vertex: geom_type={u.geom_type} -> n_rings={1 if u.geom_type=='Polygon' else len(u.geoms)} (gate wants ==1)")
u2 = unary_union([Polygon([[0,0],[10,0],[10,10],[0,10]]), Polygon([[12,0],[22,0],[22,10],[12,10]])]).buffer(0)
print(f" G03 union of two panels 2mm apart: geom_type={u2.geom_type} -> n_rings={len(u2.geoms)}")
u3 = unary_union([Polygon([[0,0],[10,0],[10,10],[0,10]]), Polygon([[5,0],[15,0],[15,10],[5,10]])]).buffer(0)
print(f" G03 union of two panels overlapping 5mm: geom_type={u3.geom_type}, area={u3.area:.0f} (10x10+10x10-5x10=150; overlap silently merged)")
