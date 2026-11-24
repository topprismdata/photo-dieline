"""手写分层 PDF: 可选内容组 (Optional Content Groups) = 印前图层.

几何与颜色来自 export.layout (与 SVG 共用的单源); 页面坐标 mm → pt (1mm = 72/25.4 pt)。
QA 门 (G08) 用独立解析器 pypdf 打开本文件, 核对 MediaBox、图层挂载、50mm 校验条与
"全部几何在页内" — 本模块的正确性由外部读取来证明, 不由自己写的字节来证明。

PDF 语法要点 (曾因这两处写错导致独立引擎打不开):
  /Properties 字典的键必须是名字对象 (/P0); BDC 需要 tag 与 properties 两个操作数 (/OC /P0 BDC)。
"""
from __future__ import annotations

import zlib

from ..core.ir import ARError
from .layout import DASH, GLUE_FILL_RGB, LAYERS, MARGIN, RGB, net_bbox, page_shapes, title

PT_PER_MM = 72.0 / 25.4


def _mm(v: float) -> float:
    return v * PT_PER_MM


def _pt(v: float) -> str:
    return f"{v:.4f}"


def _rgb(c: tuple[float, float, float]) -> str:
    return f"{c[0]:.3f} {c[1]:.3f} {c[2]:.3f}"


def _literal(s: str) -> str:
    """PDF 文本串字面量: 只转义反斜杠、圆括号, 非 Latin-1 字符替换."""
    out = []
    for ch in s.encode("latin-1", "replace").decode("latin-1"):
        out.append("\\" + ch if ch in "\\()" else ch)
    return "".join(out)


def _shape_ops(shape) -> list[str]:
    ops = [f"{_mm(shape.width):.3f} w"]
    if shape.layer in DASH:
        ops.append("[" + " ".join(f"{_mm(d):.3f}" for d in DASH[shape.layer]) + "] 0 d")
    else:
        ops.append("[] 0 d")
    ops.append(f"{_pt(_mm(shape.pts[0][0]))} {_pt(_mm(shape.pts[0][1]))} m")
    for x, y in shape.pts[1:]:
        ops.append(f"{_pt(_mm(x))} {_pt(_mm(y))} l")
    if shape.closed and shape.layer == "GLUE":
        ops += [f"{_rgb(GLUE_FILL_RGB)} rg", "h", "f"]
    elif shape.closed:
        ops += [f"{_rgb(RGB[shape.layer])} RG", "h", "S"]
    else:
        ops += [f"{_rgb(RGB[shape.layer])} RG", "S"]
    return ops


def build_pdf(ir, net_w: float, net_h: float) -> bytes:
    """IR → 分层 PDF 字节。net_w/net_h = 净图宽高 (须与 IR 包围盒一致); 几何取 export.layout 单源。"""
    nx0, ny0, nx1, ny1 = net_bbox(ir)
    pw, ph = nx1 - nx0, ny1 - ny0
    if abs(pw - net_w) > 1e-6 or abs(ph - net_h) > 1e-6:
        raise ARError(f"net_w/net_h ({net_w:.3f},{net_h:.3f}) 与 IR 净图包围盒 ({pw:.3f},{ph:.3f}) 不一致")
    W, H = _mm(net_w + 2 * MARGIN), _mm(net_h + 2 * MARGIN)
    shapes = page_shapes(ir)

    streams: list[tuple[int, str]] = []   # (LAYERS 下标, 内容流片段)
    for i, name in enumerate(LAYERS):
        body = "\n".join(op for s in shapes[name] for op in _shape_ops(s))
        if name == "INFO":
            caption = f"{title(ir)} | CHECK BAR = 50 mm"
            text_op = (f"BT /F1 10 Tf {_mm(MARGIN):.2f} {_mm(4.0):.2f} Td "
                       f"({_literal(caption)}) Tj ET")
            body = text_op if not body else body + "\n" + text_op
        if body:
            streams.append((i, body))

    objs: list[bytes] = []  # 1-based

    def add(b: bytes) -> int:
        objs.append(b)
        return len(objs)

    add(b"")  # 1 catalog
    add(b"")  # 2 pages
    add(b"")  # 3 page
    font_id = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    add(b"")  # 5 content
    ocg_ids = [add(f"<< /Type /OCG /Name ({name}) >>".encode()) for name in LAYERS]
    ocprops = " ".join(str(i) for i in ocg_ids)
    props = " ".join(f"/P{i} {oid} 0 R" for i, oid in enumerate(ocg_ids))
    objs[0] = (b"<< /Type /Catalog /Pages 2 0 R /OCProperties << /OCGs ["
               + ocprops.encode() + b"] /D << /ON [" + ocprops.encode()
               + b"] /Order [" + ocprops.encode() + b"] >> >> >>")
    objs[1] = b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"
    objs[2] = (f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W:.4f} {H:.4f}] "
               f"/Resources << /Font << /F1 {font_id} 0 R >> /Properties << {props} >> >> "
               f"/Contents 5 0 R >>").encode()
    chunks = [f"/OC /P{i} BDC\n{body}\nEMC" for i, body in streams]
    comp = zlib.compress("\n".join(chunks).encode("latin-1", "replace"))
    objs[4] = (b"<< /Length " + str(len(comp)).encode() + b" /Filter /FlateDecode >> stream\n"
               + comp + b"\nendstream")
    out = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for o in offsets:
        out += f"{o:010d} 00000 n \n".encode()
    out += (f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF").encode()
    return bytes(out)
