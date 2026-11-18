"""手写分层 PDF (无第三方依赖): 可选内容组(Optional Content Groups) = 印前图层.

几何: 线段/多边形描边; mm→pt (1mm = 72/25.4 pt)。QA 直读 MediaBox 与
内容流校验 1:1 物理尺寸与 50mm 校验条。
"""
from __future__ import annotations

import zlib

PT_PER_MM = 72.0 / 25.4
LAYERS = ["CUT", "CREASE-MOUNTAIN", "CREASE-VALLEY", "GLUE", "BLEED", "REGISTRATION", "INFO"]


def _esc(s: str) -> bytes:
    return s.encode("latin-1", "replace")


def _mm(v: float) -> float:
    return v * PT_PER_MM


def _path_cmds(shapes, close=False) -> str:
    ops = []
    for pts, _color, width, dash in shapes:
        if len(pts) < 2:
            continue
        ops.append(f"{_mm(width):.3f} w")
        if dash:
            ops.append(f"[{_mm(dash[0]):.3f} {_mm(dash[1]):.3f}] 0 d")
        else:
            ops.append("[] 0 d")
        ops.append(f"{_mm(pts[0][0]):.4f} {_mm(pts[0][1]):.4f} m")
        for p in pts[1:]:
            ops.append(f"{_mm(p[0]):.4f} {_mm(p[1]):.4f} l")
        if close:
            ops.append("h")
        ops.append("S")
    return "\n".join(ops)


def build_pdf(ir, net_w: float, net_h: float, layer_geo: dict) -> bytes:
    """layer_geo: {layer: [ (pts, (r,g,b), width_mm, (d1,d2)|None) ]} 坐标=净图mm."""
    W, H = (net_w + 24) * PT_PER_MM, (net_h + 24) * PT_PER_MM  # MARGIN*2=24mm
    shift = 12.0  # 与 SVG MARGIN 一致

    streams = []
    content_parts = []
    for i, name in enumerate(LAYERS):
        shapes = layer_geo.get(name, [])
        if not shapes:
            continue
        body = _path_cmds([([(x + shift, y + shift) for x, y in pts], c, w, d)
                           for pts, c, w, d in shapes])
        if not body:
            continue
        streams.append((name, body))
    # 文本 (INFO 图签)
    info_extra = (
        f"BT /F1 10 Tf 12 {shift:.2f} Td (photo-dieline 1:1 | units mm | "
        f"CHECK BAR 50mm = {50 * PT_PER_MM:.3f}pt) Tj ET"
    )

    objs: list[bytes] = []  # 1-based

    def add(b: bytes) -> int:
        objs.append(b)
        return len(objs)

    # 占位: catalog=1, pages=2, page=3 (稍后回填)
    add(b"")  # 1 catalog
    add(b"")  # 2 pages
    add(b"")  # 3 page
    font_id = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    content_id = add(b"")  # 5 content
    ocg_ids = []
    for name in LAYERS:
        ocg_ids.append(add(f"<< /Type /OCG /Name ({name}) >>".encode()))
    ocprops_ids = " ".join(str(i) for i in ocg_ids)
    objs[0] = (b"<< /Type /Catalog /Pages 2 0 R /OCProperties << /OCGs ["
               + ocprops_ids.encode() + b"] /D << /ON [" + ocprops_ids.encode()
               + b"] /Order [" + ocprops_ids.encode() + b"] >> >> >>")
    objs[1] = b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"
    objs[2] = (f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W:.4f} {H:.4f}] "
               f"/Resources << /Font << /F1 {font_id} 0 R >> /Properties << "
               + " ".join(f"P{i} {oid} 0 R" for i, oid in enumerate(ocg_ids))
               + " >> >> /Contents 5 0 R >>").encode()
    # 内容流: 每图层 BDC/EMC 包裹
    chunks = []
    for i, (name, body) in enumerate(streams):
        chunks.append(f"/P{i} BDC\n{body}\nEMC")
    chunks.append(info_extra)
    raw = ("\n".join(chunks)).encode("latin-1", "replace")
    comp = zlib.compress(raw)
    objs[4] = (b"<< /Length " + str(len(comp)).encode() + b" /Filter /FlateDecode >> stream\n"
               + comp + b"\nendstream")
    out = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs)+1}\n".encode()
    out += b"0000000000 65535 f \n"
    for o in offsets:
        out += f"{o:010d} 00000 n \n".encode()
    out += (f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF").encode()
    return bytes(out)
