"""WP2 印刷层 v0: 刀版净图即 UV — PIL 在净图栅格上绘制印刷层, 无 Blender 烘焙依赖。

原理: 展开图 (net) 本来就是印刷面 — 每个面板顶点的净图坐标 = UV 坐标。
纹理绘制 (PIL, 纯 CPU): 基材底色 (按纸板类型) + 品类色场 (墙面板) + TOPPRISM 字标
(最大墙面板居中) + 信息条 (材质/克重声明, 数据集溯源要素)。
诚实边界: v0 是**程序化占位印刷**, 非真实品牌版面复刻 — 真实版面属 WP2 后续 (许可与来源审计)。
"""

import math

import numpy as np

from PIL import Image, ImageDraw, ImageFont

from ..folding.engine import fold_all

# 基材底色 (sRGB) — 白卡/液体砖白面/瓦楞牛皮
BASE_COLOR = {"carton_board": (247, 245, 240), "corrugated_e": (196, 164, 118),
              "liquid_brick": (242, 240, 236)}
# 品类色场 (墙面板填充) — 数据集视觉多样性的第一轴 (家族色系)
FAMILY_COLORS = {
    "gable": (66, 133, 244), "clv": (52, 168, 83), "cone": (251, 188, 4),
    "food": (234, 88, 12), "brick": (234, 67, 53), "rsc": (120, 120, 130),
    "tray": (0, 150, 136), "sundry": (156, 100, 210),
}


def draw_print_texture(ir, family, px_per_mm=4.0, net_bbox_mm=None):
    """净图 → RGBA 纹理。返回 (PIL.Image, (x0, y0, w_mm, h_mm))。
    uv 映射 (导出器侧): u = (x_mm - x0)/w_mm, v = 1 - (y_mm - y0)/h_mm (PIL y 向下)。"""
    polys = []
    for pp in ir.panels:
        polys.append((pp["id"], pp["role"], [tuple(p) for p in pp["polygon_2d"]]))
    allpts = [p for _, _, poly in polys for p in poly]
    x0 = min(p[0] for p in allpts); y0 = min(p[1] for p in allpts)
    x1 = max(p[0] for p in allpts); y1 = max(p[1] for p in allpts)
    w_mm, h_mm = x1 - x0, y1 - y0
    W, H = max(256, int(w_mm * px_per_mm)), max(256, int(h_mm * px_per_mm))
    img = Image.new("RGB", (W, H), BASE_COLOR.get("carton_board", (247, 245, 240)))
    d = ImageDraw.Draw(img)

    def px(pt):
        return ((pt[0] - x0) * W / w_mm, (pt[1] - y0) * H / h_mm)

    # 1. 墙面板品类色场 (role=wall 全填; 顶盖/翼保持基材色)
    fam_color = FAMILY_COLORS.get(family, (120, 120, 130))
    wall_polys = [(pid, poly) for pid, role, poly in polys if role == "wall"]
    for _, poly in wall_polys:
        d.polygon([px(p) for p in poly], fill=fam_color, outline=(30, 30, 34))
    # 2. TOPPRISM 字标: 逐墙定向绘制 — up = 净图内"世界最高边"方向 (折叠后墙面正上方),
    #    多边形掩膜裁剪 (防标签溢进邻墙净图区)。净图与世界顶点同序 (fold_all 约定)。
    world = fold_all(ir)
    if wall_polys:
        box_center = np.mean([np.asarray(world[pid], float).mean(0)
                              for pid, _ in wall_polys], axis=0)
        for pid, wpoly in wall_polys:
            w3 = np.asarray(world[pid], float)
            N = np.asarray(wpoly, float)
            if w3.shape[0] >= 3 and np.allclose(w3[0], w3[-1]):
                w3, N = w3[:-1], N[:-1]
            if w3.shape[0] != N.shape[0]:
                continue
            nrm = np.cross(w3[1] - w3[0], w3[2] - w3[0])
            nn = float(np.linalg.norm(nrm)) or 1.0
            nrm = nrm / nn
            if float(np.dot(nrm, np.asarray(w3, float).mean(0) - box_center)) < 0:
                nrm = -nrm  # 外向法线
            r = np.cross(np.array([0.0, 0.0, 1.0]), nrm)
            rn = float(np.linalg.norm(r)) or 1.0
            r = r / rn
            ext = [(float(np.dot(v, r)), float(v[2])) for v in w3]  # 外侧视平面坐标
            ext_sign = _signed_area(ext)
            net_sign = _signed_area([tuple(p) for p in N])
            mirror = (ext_sign * net_sign) < 0  # 外侧视绕向与净图相反 → 印刷镜像
            tip = int(np.argmax(N[:, 1]))                       # 净图最上顶点 (墙顶沿, 坡尖在下方)
            nb = [N[(tip - 1) % len(N)], N[(tip + 1) % len(N)]] # 墙顶沿两点
            base = [N[int(i)] for i in np.argsort(N[:, 1])[:2]]  # 底边两角 (净图最下 = 坡尖侧)
            up = (nb[0] + nb[1]) / 2.0 - (base[0] + base[1]) / 2.0
            n = float(np.hypot(up[0], up[1])) or 1.0
            up = up / n
            base_mid = (base[0] + base[1]) / 2.0
            top_mid = (nb[0] + nb[1]) / 2.0
            wall_h = float(np.linalg.norm(top_mid - base_mid)) or 1.0
            label_c = base_mid + up * wall_h * 0.35  # 墙身带 (底边中点 + 35% 墙高)
            cx = float(label_c[0]); cy = float(label_c[1])
            _draw_wordmark(img, d, px((cx, cy)), math.atan2(up[1], up[0]), wpoly, px,
                           fam_color, mirror)
    # 3. 信息条: 净图右上角, 数据集溯源要素
    d.text((W - 8, 8), "TOPPRISM · PACK10K-RETAIL · SYNTHETIC PRINT v0",
           fill=(90, 90, 96), anchor="ra", font=_font(int(H * 0.018)))
    return img, (x0, y0, w_mm, h_mm)


def _poly_area(poly):
    s = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % len(poly)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def _font(px_h):
    for name in ("/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/HelveticaNeue.ttc"):
        try:
            return ImageFont.truetype(name, max(9, int(px_h)), index=0)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_wordmark(img, d, center_px, angle_rad, wpoly, px, fam_color, mirror=False):
    """逐墙定向字标: 独立 RGBA tile 渲染 → 按 up 角旋转 → 多边形掩膜贴入净图。
    mirror=True 时水平翻转 tile (该墙外侧视绕向与净图相反)。"""
    # 字号: 以面板净图 px 尺寸估计 (px 函数给出 mm→px 比例); 文本宽须 ≤ 0.8 面板宽
    p0, p1 = px((0, 0)), px((1, 1))
    ppx = math.hypot(p1[0] - p0[0], p1[1] - p0[1])  # px per mm
    net_xs = [px(p)[0] for p in wpoly]; net_ys = [px(p)[1] for p in wpoly]
    panel_w_px = min(max(net_xs) - min(net_xs), max(net_ys) - min(net_ys))  # 窄边 (净图 bbox 长边含坡顶)
    wall_px = math.sqrt(_poly_area_px(wpoly, px))
    fs = max(10, int(wall_px * 0.16))
    f = _font(fs)
    text = "TOPPRISM"
    while fs > 10 and d.textlength(text, font=_font(fs)) > panel_w_px * 0.8:
        fs = max(10, int(fs * 0.9))
    f = _font(fs)
    tw = int(d.textlength(text, font=f))
    th = int(fs * 1.8)
    tile = Image.new("RGBA", (tw + fs, th + fs), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    td.rounded_rectangle([0, 0, tile.width - 1, tile.height - 1], radius=int(fs * 0.28),
                         fill=(250, 250, 252, 235),
                         outline=tuple([int(c * 0.6) for c in fam_color] + [255]),
                         width=max(1, fs // 14))
    td.text((tile.width / 2, tile.height / 2), text, font=f, fill=(24, 28, 38, 255), anchor="mm")
    if mirror:
        tile = tile.transpose(Image.FLIP_LEFT_RIGHT)
    rot = tile.rotate(-math.degrees(angle_rad) - 90.0, expand=True, resample=Image.BICUBIC)
    cx, cy = center_px
    # 多边形掩膜: 全图 L 掩膜上墙内区域 = 255, 只允许字标落在本墙内
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).polygon([px(p) for p in wpoly], fill=255)
    img.paste(rot, (int(cx - rot.width / 2), int(cy - rot.height / 2)), Image.composite(rot.split()[3], Image.new("L", rot.size, 0), mask.crop((int(cx - rot.width / 2), int(cy - rot.height / 2), int(cx - rot.width / 2) + rot.width, int(cy - rot.height / 2) + rot.height))))


def _signed_area(pts):
    s = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % len(pts)]
        s += x1 * y2 - x2 * y1
    return s / 2.0


def _poly_area_px(wpoly, px):
    ppx_pts = [px(p) for p in wpoly]
    s = 0.0
    for i in range(len(ppx_pts)):
        x1, y1 = ppx_pts[i]; x2, y2 = ppx_pts[(i + 1) % len(ppx_pts)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0
