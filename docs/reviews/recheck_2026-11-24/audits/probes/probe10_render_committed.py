"""E10: 用独立渲染器渲染仓内已提交的 golden 产物 (只读). 证明 SVG 底板在画布外, PDF 在 poppler/Quartz 下打不开或全白."""
import io, re, shutil, subprocess
from pathlib import Path
import numpy as np
from PIL import Image
REPO = Path("/Users/guohongbin/photo-dieline"); A = Path("/tmp/pd_recheck/render_out"); A.mkdir(parents=True, exist_ok=True)
svg = (REPO / "examples/gable_top/artifacts/dieline.svg").read_text(); H = 203.173; NUM = r"-?[\d.]+"
def ys_of(s): return np.array([float(v) for v in re.findall(rf'y[12]="({NUM})"', s)] + [float(b) for a, b in re.findall(rf"({NUM}),({NUM})", s)]
                              + [float(y) for _, y in re.findall(rf"[ML] ({NUM}) ({NUM})", s)])
print("== committed examples/gable_top/artifacts/dieline.svg ==")
for name in ("CUT", "CREASE-MOUNTAIN", "CREASE-VALLEY", "GLUE", "BLEED", "REGISTRATION", "INFO"):
    yy = ys_of(re.search(rf'<g id="{name}">(.*?)</g>', svg, re.S).group(1))
    print(f"  layer {name:<15} y∈[{yy.min():7.2f},{yy.max():7.2f}] mm  (viewBox y∈[0,{H}])  off-canvas share={100*(yy<0).mean():3.0f}%")
try:
    import fitz
    pix = fitz.open(stream=svg.encode(), filetype="svg")[0].get_pixmap(dpi=254)
    a = np.array(Image.open(io.BytesIO(pix.tobytes("png"))).convert("L")); ink = a < 200; h = a.shape[0]; r = np.where(ink.any(axis=1))[0]
    print(f"  MuPDF raster: ink y∈[{r.min()/h*H:.1f},{r.max()/h*H:.1f}] mm from top ; empty band at bottom = {(h-1-r.max())/h*H:.1f} mm")
    print(f"  ink pixels in band y∈[135,200]mm (where the 57mm-tall bottom flaps would sit if on canvas): {int(ink[int(135/H*h):int(200/H*h)].sum())}")
except Exception as e:
    print("  SVG rasterization failed:", type(e).__name__, e)
print("\n== committed examples/gable_top/artifacts/dieline.pdf under independent engines ==")
pdf = REPO / "examples/gable_top/artifacts/dieline.pdf"; f = A / "golden_committed.pdf"; shutil.copy(pdf, f)
p = subprocess.run(["pdftoppm", "-r", "254", "-gray", "-png", str(f), str(A / "gc")], capture_output=True, text=True)
a = np.array(Image.open(sorted(A.glob("gc-*.png"))[0]).convert("L"))
print(f"  poppler pdftoppm : rc={p.returncode} raster={a.shape[1]}x{a.shape[0]} min_pixel={a.min()} -> {'ALL WHITE' if a.min() == 255 else 'has content'} ; syntax errors={len([l for l in p.stderr.splitlines() if 'Error' in l])}")
p = subprocess.run(["sips", "-s", "format", "png", str(f), "--out", str(A / "gc_sips.png")], capture_output=True, text=True)
print(f"  Apple Quartz sips: rc={p.returncode} ; {'renders' if p.returncode == 0 else 'FAILS: ' + ' / '.join(l.strip() for l in p.stderr.splitlines() if 'Error' in l)[:110]}")
try:
    import Quartz
    b = str(f).encode(); doc = Quartz.CGPDFDocumentCreateWithURL(Quartz.CFURLCreateFromFileSystemRepresentation(None, b, len(b), False))
    print(f"  Apple CoreGraphics CGPDFDocumentCreate: {'opens, pages=' + str(Quartz.CGPDFDocumentGetNumberOfPages(doc)) if doc else 'returns None (cannot open)'}")
except ImportError:
    print("  (PyObjC Quartz unavailable)")
try:
    import pypdf
    r = pypdf.PdfReader(str(f), strict=False); print(f"  pypdf lenient    : pages={len(r.pages)} mediabox={tuple(float(v) for v in r.pages[0].mediabox)} ; properties keys parsed: {list(r.pages[0]['/Resources'].get('/Properties', {}).keys()) if '/Properties' in r.pages[0]['/Resources'] else 'NONE'}")
except Exception as e:
    print("  pypdf:", type(e).__name__, str(e)[:100])
