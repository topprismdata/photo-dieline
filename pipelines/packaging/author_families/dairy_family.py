"""Dairy 家族 (M5): 酸奶杯 160g — 锥度杯身 + 铝箔拱顶盖 (压合卷边)。
零品牌: 通用几何, 零商标零文字零贴图。质量 = 材质密度×闭壳体积 (门禁推导)。
"""
import math

FAMILY = "dairy"

CLASSES = [
    "yogurt_cup_160",
]

DEFAULTS = {
    "yogurt_cup_160": {"H": 92.0, "D": 58.0},
}

MAT_PP_CUP = "plastic_pp"
MAT_ALU_FOIL = "metal_alu"


def _lathe_closed(name, loop, mat, n=96):
    """闭合轮廓回转体 (极点焊接 + 绕序翻转): 流形由构造保证。"""
    pts = list(loop)
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    m = len(pts) - 1
    verts = []
    row_idx = []
    for (r, z) in pts[:m]:
        if r < 1e-6:  # 极点行: 单顶点焊接
            row_idx.append([len(verts)] * n)
            verts.append((0.0, 0.0, z))
        else:
            idxs = []
            for k in range(n):
                a = 2.0 * math.pi * k / n
                idxs.append(len(verts))
                verts.append((r * math.cos(a), r * math.sin(a), z))
            row_idx.append(idxs)
    tris = []
    for i in range(m):
        A, B = row_idx[i], row_idx[(i + 1) % m]
        for k in range(n):
            k1 = (k + 1) % n
            q = [A[k], A[k1], B[k1], B[k]]
            uniq = []
            for vidx in q:
                if vidx not in uniq:
                    uniq.append(vidx)
            if len(uniq) == 3:
                tris.append([uniq[0], uniq[1], uniq[2]])
            elif len(uniq) == 4:
                tris.append([uniq[0], uniq[1], uniq[2]])
                tris.append([uniq[0], uniq[2], uniq[3]])
    # 绕序翻转 (signed volume < 0 → 外向法线保证)
    vol = 0.0
    for t in tris:
        a, b, c = (verts[i] for i in t)
        vol += (a[0] * (b[1] * c[2] - b[2] * c[1])
                - a[1] * (b[0] * c[2] - b[2] * c[0])
                + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.0
    if vol < 0:
        for t in tris:
            t[0], t[1] = t[1], t[0]
    return {"name": name, "verts_mm": verts, "tris": tris, "material_id": mat}


def _yogurt_cup(H, D):
    """锥度杯: 顶宽底窄 (拔模 ~6°), 底缘圆角台阶; 铝箔拱顶盖压合卷边。"""
    R_top = D / 2.0
    R_bot = R_top * 0.78
    wall = 0.9
    rim_z = H - 6.0
    outer = [
        (R_bot * 0.80, 0.0), (R_bot, 2.5), (R_bot, 5.0),
        (R_top - 0.2, rim_z), (R_top, rim_z), (R_top, rim_z + 1.2),
        (R_top - 1.2, rim_z + 1.2), (R_top - 1.2, rim_z),
    ]
    inner = [(max(r - wall, 0.8), z) for r, z in reversed(outer[1:-1])]
    loop = outer + inner + [outer[0]]
    P = [_lathe_closed("cup_shell", loop, MAT_PP_CUP, n=96)]
    # 铝箔拱顶盖: 卷边扣在杯口外缘, 中央上拱 4mm
    foil_seal = R_top + 1.5
    rim_in = R_top - 1.2
    foil = [
        (rim_in, rim_z + 1.0), (foil_seal, rim_z + 1.2), (foil_seal, rim_z + 3.0),
        (foil_seal - 1.0, rim_z + 3.6), (R_top * 0.55, rim_z + 6.5),
        (0.0, rim_z + 7.5),
    ]
    foil_closed = foil + [(0.0, rim_z + 3.2)]
    P.append(_lathe_closed("foil_lid", foil_closed, MAT_ALU_FOIL, n=96))
    return P


def build_parts(params: dict) -> list[dict]:
    cid = CLASSES[0]
    if isinstance(params, dict) and params.get("class_id") in DEFAULTS:
        cid = params["class_id"]
    D0 = DEFAULTS[cid]
    if cid == "yogurt_cup_160":
        return _yogurt_cup(D0["H"], D0["D"])
    raise KeyError(f"unknown class {cid}")
