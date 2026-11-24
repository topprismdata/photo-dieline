"""E5: 导出物独立核验 (不用本仓 QA 代码): SVG/PDF 一致性、重复实体、图层内容、校验条、PDF 有效性."""
import re, zlib, io, json
import numpy as np
from photo_dieline.core.ir import from_raw
from photo_dieline.export import svg as svgx, pdf as pdfx
from photo_dieline.parametric import gable_top
from photo_dieline.cli import _layer_geo

raw = gable_top.build_ir({"W": 57.15, "D": 57.15, "Hb": 75.0, "Hr": 20.25, "Ef": 12.0, "board_t": 0.42})
ir = from_raw(raw); x0, y0, x1, y1 = svgx.net_bbox(ir); nw, nh = x1 - x0, y1 - y0
svg = svgx.render(ir, nw, nh); pdf = pdfx.build_pdf(ir, nw, nh, _layer_geo(ir))

# ---------- SVG ----------
print("== SVG ==")
m = re.search(r'width="([\d.]+)mm" height="([\d.]+)mm"\s+viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
print(f" width/height = {m.group(1)}x{m.group(2)} mm ; viewBox = {m.group(3)}x{m.group(4)} ; net = {nw:.3f}x{nh:.3f} mm ; net+24 = {nw+24:.3f}x{nh+24:.3f}")
layers = dict(re.findall(r'<g id="([\w-]+)">(.*?)</g>', svg, re.S))
print(" layer -> element counts:", {k: {t: len(re.findall(f"<{t}[ >]", v)) for t in ("polygon", "line", "path", "text") if re.findall(f"<{t}[ >]", v)} for k, v in layers.items()})
# 重复 CUT 实体
cut = layers["CUT"]
outline_pts = [tuple(map(float, p.split(","))) for p in re.search(r'<polygon points="([^"]+)"', cut).group(1).split()]
lines = [tuple(map(float, g)) for g in re.findall(r'<line x1="(-?[\d.]+)" y1="(-?[\d.]+)" x2="(-?[\d.]+)" y2="(-?[\d.]+)"', cut)]
def key(a, b): return tuple(sorted((tuple(round(c, 3) for c in a), tuple(round(c, 3) for c in b))))
outline_segs = {key(outline_pts[i], outline_pts[(i + 1) % len(outline_pts)]) for i in range(len(outline_pts) - 1)}
line_keys = [key(l[:2], l[2:]) for l in lines]
from collections import Counter
c = Counter(line_keys)
dup_lines = {k: v for k, v in c.items() if v > 1}
on_outline = [k for k in c if k in outline_segs]
L = lambda k: np.hypot(k[0][0] - k[1][0], k[0][1] - k[1][1])
print(f" CUT layer: 1 outline polygon ({len(outline_segs)} segs) + {len(lines)} <line> elems; distinct={len(c)}")
print(f"   <line> duplicating the outline polygon : {len(on_outline)} segs, total length {sum(L(k) for k in on_outline):.1f} mm")
print(f"   <line> duplicated twice (panel-pair shared cut seams): {len(dup_lines)} keys, {sorted(set(dup_lines.values()))}x")
print(f"   => every mm of the CUT outline is emitted twice: {abs(sum(L(k) for k in on_outline) - sum(L(k) for k in outline_segs)) < 1e-6}")
# 校验条
info = layers["INFO"]
bar = re.search(r'<line x1="([\d.]+)" y1="([\d.]+)" x2="([\d.]+)" y2="([\d.]+)"\s+stroke="#111" stroke-width="0.5"', info)
bx = [float(bar.group(i)) for i in range(1, 5)]
print(f" INFO check bar: ({bx[0]},{bx[1]})->({bx[2]},{bx[3]}) length={np.hypot(bx[2]-bx[0], bx[3]-bx[1]):.3f} user-units (=mm)")
# y 镜像: 找 finB (net y 最大) 在 SVG 中的位置
finB = ir.panel("finB")["polygon_2d"]; finy = [p[1] for p in finB]
print(f" net y-up: finB occupies net y in [{min(finy):.1f},{max(finy):.1f}] (top of net). SVG y-down: finB at SVG y in [{min(finy)+12:.1f},{max(finy)+12:.1f}] of {nh+24:.1f} => drawn at BOTTOM (mirrored vs PDF)")
# 折线图层
mv = {k: len(re.findall(r"<line", layers[k])) for k in ("CREASE-MOUNTAIN", "CREASE-VALLEY")}
print(" crease layers (line count):", mv, " IR mt_va:", {t: sum(1 for e in ir.edges if e.mt_va == t) for t in ("MOUNTAIN", "VALLEY")})

# ---------- PDF ----------
print("\n== PDF ==")
head = pdf[:4096].decode("latin-1")
mb = re.search(r"/MediaBox \[0 0 ([\d.]+) ([\d.]+)\]", head)
PT = 72 / 25.4
print(f" MediaBox = {float(mb.group(1)):.4f} x {float(mb.group(2)):.4f} pt = {float(mb.group(1))/PT:.3f} x {float(mb.group(2))/PT:.3f} mm")
print(" Boxes present:", [b for b in ("MediaBox", "CropBox", "BleedBox", "TrimBox", "ArtBox") if f"/{b}" in pdf.decode("latin-1")])
st = re.search(rb"stream\n(.*?)\nendstream", pdf, re.S); content = zlib.decompress(st.group(1)).decode("latin-1")
tagged = re.findall(r"/P(\d) BDC\n(.*?)\nEMC", content, re.S)
ocg_names = re.findall(r"/Type /OCG /Name \(([^)]+)\)", pdf.decode("latin-1"))
print(" OCG dictionaries:", ocg_names)
for i, body in tagged:
    n_m = len(re.findall(r" m\n", body)); print(f"   /P{i} BDC -> '{ocg_names[int(i)]}': {n_m} subpaths, {body.count(' l\n')} segments, has color op (rg/RG): {'rg' in body or 'RG' in body}")
untagged = content[content.rfind("EMC") + 3:]
print(f" content outside any OCG tag: {untagged.strip()[:70]!r}")
print(f" color operators in whole content stream: {re.findall(r'[\d.]+ [\d.]+ [\d.]+ (?:rg|RG)', content)[:3] or 'NONE (all strokes default black)'}")
dashes = sorted(set(re.findall(r"\[([^\]]+)\] 0 d", content)))
print(f" dash ops: {dashes}")
# PDF 中各层的线段端点与 SVG 比较 (同一 net 点)
seg = re.findall(r"([\d.]+) ([\d.]+) m\n([\d.]+) ([\d.]+) l", content)
ax, ay, bx2, by2 = map(float, seg[0])
print(f" first PDF segment: ({ax/PT:.3f},{ay/PT:.3f})->({bx2/PT:.3f},{by2/PT:.3f}) mm  (PDF y-up => same net point drawn at TOP)")
# 用 PyMuPDF 独立解析
try:
    import fitz
    doc = fitz.open(stream=pdf, filetype="pdf"); pg = doc[0]
    print(f" PyMuPDF: pages={doc.page_count} rect={pg.rect} (pt) ; is_pdf={doc.is_pdf}; needs_pass={doc.needs_pass}")
    dr = pg.get_drawings()
    lens = sorted({round(np.hypot(it[2].x - it[1].x, it[2].y - it[1].y) / PT, 3) for d in dr for it in d["items"] if it[0] == "l"}, reverse=False)
    print(f"   vector line items: {sum(1 for d in dr for it in d['items'] if it[0]=='l')} ; distinct lengths(mm): {lens[:6]} ... max {lens[-1]}")
    print(f"   check bar measured by independent parser: {[l for l in lens if abs(l-50) < 0.01]} mm ; stroke widths(pt): {sorted({round(d.get('width') or 0, 3) for d in dr})}")
    print(f"   stroke colors seen: {sorted({tuple(round(c,2) for c in (d.get('color') or ())) for d in dr})}")
    print(f"   text: {pg.get_text().strip()!r}")
    # OCG
    print("   optional content (OCGs) per PyMuPDF:", doc.get_ocgs())
except Exception as e:
    print(" PyMuPDF failed:", type(e).__name__, e)

# ---------- PDF 校验条篡改 (修正数值) ----------
bar_pt = re.search(r"(-?[\d.]+) (-?[\d.]+) m\n(-?[\d.]+) (-?[\d.]+) l", content)
print(f"\n check bar raw pdf ops: {bar_pt.group(0)!r}  => {np.hypot(float(bar_pt.group(3))-float(bar_pt.group(1)), float(bar_pt.group(4))-float(bar_pt.group(2))):.4f} pt")

print("\n== PDF 校验条/图层经独立解析器 (PyMuPDF) ==")
draws = pg.get_drawings()
ocg_doc = doc.get_ocgs()
import collections
per_layer = collections.defaultdict(lambda: {"subpaths": 0, "segs": 0})
for d in draws:
    lid = d.get("layer") or "(no layer)"
    per_layer[lid]["subpaths"] += 1; per_layer[lid]["segs"] += sum(1 for it in d["items"] if it[0] == "l")
for k, v in per_layer.items(): print(f"   {k:<22s} subpaths={v['subpaths']:>3} segs={v['segs']:>3}")
print("   OCGs:", {v.get("name"): v.get("on") for v in ocg_doc.values()})
neg = sum(1 for d in draws for it in d["items"] if it[0] == "l" and (it[1].y < 0 or it[2].y < 0))
print(f"   line items with an endpoint below the page (y<0pt): {neg} / {sum(1 for d in draws for it in d['items'] if it[0]=='l')}")

print("\n== 重复 CUT 实体 (含负坐标) ==")
from collections import Counter
c = Counter(line_keys)
on_outline = [k for k in c if k in outline_segs]
L = lambda k: float(np.hypot(k[0][0]-k[1][0], k[0][1]-k[1][1]))
print(f" CUT <line> count={len(lines)} distinct={len(c)} ; on outline polygon: {len(on_outline)} ; duplicated <line> keys: {sum(1 for v in c.values() if v>1)}")
outline_len = sum(L(k) for k in outline_segs)
print(f" outline perimeter={outline_len:.2f} mm ; re-emitted as <line> in CUT layer: {sum(L(k) for k in on_outline):.2f} mm")
