"""probe15 — R3「独立 PDF 实际渲染」(A2 有条件通过 → 补证): 第三方引擎栅格化 + 像素几何实测。

证据链: 库字节 → PyMuPDF (第三方) 栅格化 → 像素域实测
  ① MediaBox 尺寸 (mm) vs SVG 页面尺寸 (同源对照)
  ② 50mm 校验条: clip 高倍渲染直取 (v3: 全页行映射有 ~10px 探针偏差, clip 直取绕开) → 水平暗列跨度
  ③ 栅格墨迹包围盒 ⊇ 矢量并集包围盒 (第三方渲染完整性; INFO 标题文字可超出净图上缘, 只报告不设门)
  ④ OCProperties /D /ON 全图层默认开启 (印刷可见性) + 油墨覆盖
判据: MediaBox Δ<0.05mm; 校验条偏差 ≤0.3mm (含描边半宽+抗锯齿); 墨迹对矢量并集的外向超出 ≤0.3mm。
"""
import io
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))
import fitz  # noqa: E402
from PIL import Image  # noqa: E402

from photo_dieline.core.ir import from_raw  # noqa: E402
from photo_dieline.export import svg as svgx  # noqa: E402
from photo_dieline.export.pdf import build_pdf  # noqa: E402
from photo_dieline.parametric import gable_top  # noqa: E402

DPI = 300.0
PT2MM = 25.4 / 72.0
BAR_MM = 50.0

ir = from_raw(gable_top.build_ir(dict(gable_top.DEFAULTS)))
x0, y0, x1, y1 = svgx.net_bbox(ir)
net_w, net_h = x1 - x0, y1 - y0
svg_text = svgx.render(ir, net_w, net_h)
pdf_bytes = build_pdf(ir, net_w, net_h)
ev = Path(__file__).resolve().parents[2] / "evidence"
ev.mkdir(exist_ok=True)
(ev / "probe15_independent.pdf").write_bytes(pdf_bytes)

svg_w = float(svg_text.split('width="')[1].split('"')[0].replace("mm", ""))
svg_h = float(svg_text.split('height="')[1].split('"')[0].replace("mm", ""))

doc = fitz.open(stream=pdf_bytes, filetype="pdf")
page = doc[0]
mb_w, mb_h = page.rect.width * PT2MM, page.rect.height * PT2MM
print(f"① MediaBox: {mb_w:.3f} × {mb_h:.3f} mm | SVG 页面: {svg_w:.3f} × {svg_h:.3f} mm "
      f"| Δ=({abs(mb_w-svg_w):.4f}, {abs(mb_h-svg_h):.4f}) mm")

# ---- ② 校验条: 矢量定位 + clip 高倍渲染直取 ----
bar_rect = None
for d in page.get_drawings():
    for item in d["items"]:
        if item[0] == "l" and abs(item[1].y - item[2].y) < 0.01 \
                and abs(abs(item[2].x - item[1].x) - BAR_MM / PT2MM) < 0.5:
            p1, p2 = item[1], item[2]
            bar_rect = fitz.Rect(min(p1.x, p2.x), p1.y, max(p1.x, p2.x), p1.y)
if bar_rect is None:
    print(" ✗ 矢量域未定位到 50mm 校验条")
ZOOM_BAR = 24.0
pad = 6.0
clip = fitz.Rect(bar_rect.x0 - pad, bar_rect.y0 - pad, bar_rect.x1 + pad, bar_rect.y1 + pad)
pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM_BAR, ZOOM_BAR), clip=clip, colorspace=fitz.csRGB)
img_bar = np.asarray(Image.open(io.BytesIO(pix.tobytes("png"))).convert("L"))
# 只取校验条描边带 (中心线 ±0.75mm) 内的暗列 — clip 窗更大时会扫进相邻 caption 文字顶 (取证: pad 6pt 时 +0.3mm)
rc = int(round((clip.y1 - bar_rect.y0) * ZOOM_BAR))                # 中心线所在行 (clip 顶 = clip.y1)
half = int(round(0.75 / PT2MM * ZOOM_BAR))
inner = int(round(0.32 / PT2MM * ZOOM_BAR))                        # 横线半宽 0.25mm+AA; 外圈行只剩竖刻线墨迹
outer = np.vstack([
    img_bar[max(0, rc - half):max(0, rc - inner), :],
    img_bar[rc + inner:rc + half + 1, :],
]) < 160
cols_t = np.where(outer.any(axis=0))[0]
# 校验条是工字标 (横线+两端竖刻线): 墨迹学正确读数 = 两端刻线簇中心距 (如同读游标刻线), 不是墨迹总宽
gaps = np.where(np.diff(cols_t) > 10)[0]
clusters = np.split(cols_t, gaps + 1)
if len(clusters) < 2:
    bar_mm, bar_px = 0.0, 0
    left_c = right_c = float("nan")
else:
    left_c, right_c = clusters[0].mean(), clusters[-1].mean()
    bar_px = right_c - left_c
    bar_mm = bar_px / ZOOM_BAR * PT2MM
bar_err = abs(bar_mm - BAR_MM)
print(f"② 校验条 (工字标): 端刻线中心距实测 {bar_mm:.3f} mm ({len(clusters)} 刻线簇, 中心 {left_c:.0f}/{right_c:.0f}px) | 偏差 {bar_err:.3f} mm")

# ---- ③ 墨迹包围盒 ⊇ 矢量并集 (300 dpi, 剔 MediaBox 边界 1pt 渲染伪影带) ----
zoom = DPI / 72.0
pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), colorspace=fitz.csRGB)
img = np.asarray(Image.open(io.BytesIO(pix.tobytes("png"))).convert("L"))
GUARD = 6  # ≈1.4pt: 取证见 evidence (clip 1pt 后页边暗像素归零, 矢量域无页边元素)
core = img.copy()
core[:GUARD, :] = 255
core[-GUARD:, :] = 255
core[:, :GUARD] = 255
core[:, -GUARD:] = 255
ink = core < 128
rows = np.where(ink.any(axis=1))[0]
cols = np.where(ink.any(axis=0))[0]
mm_px = 25.4 / DPI
ink_x0, ink_x1 = cols.min() * mm_px, (cols.max() + 1) * mm_px
ink_y1 = ink_x1 * 0  # 占位避免误用; y 由下行计算
ink_y0 = (page.rect.height * zoom - rows.max() - 1) * mm_px      # 底边 (mm, 自页面底)
ink_y1 = (page.rect.height * zoom - rows.min()) * mm_px          # 顶边

vu = fitz.Rect()
n_vec = 0
for d in page.get_drawings():
    vu |= d["rect"]
    n_vec += 1
vu_x0, vu_x1 = vu.x0 * PT2MM, vu.x1 * PT2MM
vu_y0, vu_y1 = (page.rect.height - vu.y1) * PT2MM, (page.rect.height - vu.y0) * PT2MM
print(f"③ 矢量并集 ({n_vec} 条): x[{vu_x0:.2f},{vu_x1:.2f}] y[{vu_y0:.2f},{vu_y1:.2f}] mm | "
      f"栅格墨迹: x[{ink_x0:.2f},{ink_x1:.2f}] y[{ink_y0:.2f},{ink_y1:.2f}] mm")
cover_ok = (ink_x0 <= vu_x0 + 0.3 and ink_x1 >= vu_x1 - 0.3 and ink_y0 <= vu_y0 + 0.3)
over_out = max(0.0, vu_x0 - ink_x0, vu_x1 - ink_x1, vu_y0 - ink_y0)
top_text_mm = max(0.0, ink_y1 - vu_y1)                          # 上缘超出 = INFO 标题文字 (合法)
print(f"   完整性: 墨迹须包住矢量并集 (外向缺欠 {over_out:.2f} mm, 上缘文字超出 {top_text_mm:.2f} mm 只记录)")

# ---- ④ 图层默认开启 + 油墨覆盖 ----
ocp = b"/OCProperties" in pdf_bytes and b"/ON" in pdf_bytes
ink_ratio = float(ink.mean())
print(f"④ OCProperties /D /ON 存在: {ocp} | 油墨占比 {ink_ratio*100:.2f}%")

fails = []
if abs(mb_w - svg_w) > 0.05 or abs(mb_h - svg_h) > 0.05:
    fails.append("MediaBox≠SVG")
if bar_rect is None or bar_err > 0.3:
    fails.append("校验条像素实测>0.3mm")
if over_out > 0.3:
    fails.append("墨迹未包住矢量并集")
if not ocp or ink_ratio < 0.001:
    fails.append("图层配置/油墨异常")
print("\n判定:", "ALL PASS" if not fails else f"FAIL: {fails}")
print("PROBE15_DONE")
