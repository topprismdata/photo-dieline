#!/usr/bin/env python3
"""NV960 通用产品标签生成 (PIL): TOPPRISM 品牌带 + 品名 + 假条码块, 2048x616.
用法: python3 nv960_labels.py <输出目录>  (每类一张 <class>.png)
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONT_BOLD = "/System/Library/Fonts/Helvetica.ttc"
FONT_REG = "/System/Library/Fonts/Helvetica.ttc"

LABELS = {
    "spice_jar_flip_top": ("TOPPRISM", "SPICE JAR · 120 mL"),
    "swing_top_bottle": ("TOPPRISM", "SWING TOP · 500 mL"),
    "insulated_water_bottle": ("TOPPRISM", "INSULATED · 750 mL"),
    "mason_jar": ("TOPPRISM", "MASON JAR · 16 oz"),
    "glass_jar_clamp_lid": ("TOPPRISM", "CLAMP LID · 1 L"),
    "food_tin_can": ("TOPPRISM", "TIN CAN · 400 g"),
    "cookie_jar": ("TOPPRISM", "COOKIE JAR · 2 L"),
    "soap_dispenser": ("TOPPRISM", "SOAP · 400 mL"),
    "spray_bottle": ("TOPPRISM", "SPRAY · 500 mL"),
    "milk_can": ("TOPPRISM", "MILK CAN · 10 L"),
    "wine_decanter": ("TOPPRISM", "DECANTER · 1.5 L"),
    "detergent_bottle": ("TOPPRISM", "DETERGENT · 2 L"),
    "R422": ("TOPPRISM", "CORRUGATED PARCEL · RSC 0201"),
    "R436": ("TOPPRISM", "JOBSITE BOX · HEAVY DUTY"),
    "R886": ("TOPPRISM", "BULK CONTAINER · COLLAPSIBLE"),
    "R929": ("TOPPRISM", "PIPETTE TIPS · 96"),
    "R038": ("TOPPRISM", "LUNCH BOX · BENTO"),
    "R949": ("TOPPRISM", "TOPPRISM"),
    "shopping_cart": ("TOPPRISM", "SHOPPING CART · 180 L"),
    "shopping_basket": ("TOPPRISM", "SHOPPING BASKET · 32 L"),
    "barcode_scanner": ("TOPPRISM", "SCAN · 1D/2D"),
    "rotating_display_stand": ("TOPPRISM", "DISPLAY · 4 TIER"),
    "soda_fountain": ("TOPPRISM", "SODA FOUNTAIN · DUAL"),
    "napkin_dispenser": ("TOPPRISM", "NAPKIN · 600"),
    "queue_ticket_dispenser": ("TOPPRISM", "TICKETS · A-Z"),
    "juice_dispenser": ("TOPPRISM", "JUICE · 18 L"),
    "cereal_dispenser": ("TOPPRISM", "CEREAL · 35 L"),
    "paper_towel_dispenser": ("TOPPRISM", "TOWEL · CENTER-PULL"),
    "public_recycling_bin": ("TOPPRISM", "RECYCLE · 2-STREAM"),
    "carton_flow_rack": ("TOPPRISM", "CARTON FLOW · 3 LANE"),
    "muffin_tin_6cup": ("TOPPRISM", "MUFFIN TIN · 6"),
    "tiered_fruit_basket": ("TOPPRISM", "FRUIT · 2 TIER"),
    "jerry_can": ("TOPPRISM", "JERRY CAN · 20 L"),
    "R034": ("TOPPRISM", "CONDIMENT PUMP · 300 mL"),
    "R066": ("TOPPRISM", "WIRE BASKET · STEEL"),
    "R331": ("TOPPRISM", "SHOPPING CART · 180 L"),
    "R332": ("TOPPRISM", "SHOPPING BASKET · 32 L"),
    "R341": ("TOPPRISM", "DISPLAY RACK · 4 TIER"),
    "R345": ("TOPPRISM", "MAGAZINE RACK · STEEL"),
    "R355": ("TOPPRISM", "SODA FOUNTAIN · DUAL"),
    "R358": ("TOPPRISM", "NAPKIN DISPENSER · 600"),
    "R514": ("TOPPRISM", "COOLING RACK · GRID"),
    "R642": ("TOPPRISM", "WINE RACK · 24"),
    "R752": ("TOPPRISM", "PAPER TOWEL · ROLL"),
    "R766": ("TOPPRISM", "TOWEL DISPENSER · M"),
    "R767": ("TOPPRISM", "TISSUE DISPENSER · L"),
    "R788": ("TOPPRISM", "TOWEL CENTER-PULL"),
    "R888": ("TOPPRISM", "CARTON FLOW · 3 LANE"),
    "R973": ("TOPPRISM", "JERRY CAN · 20 L"),
}


def f(sz, index=0):
    return ImageFont.truetype(FONT_BOLD, sz, index=index)


def barcode(d, x, y, w, h, seed=7):
    import random
    rnd = random.Random(seed)
    cx = x
    while cx < x + w:
        bw = rnd.choice([2, 3, 2, 4, 2])
        if rnd.random() < 0.62:
            d.rectangle([cx, y, min(cx + bw, x + w), y + h], fill=(28, 30, 36))
        cx += bw + rnd.choice([2, 3])


def make(cls, brand, line):
    W, H = 2048, 616
    im = Image.new("RGB", (W, H), (246, 245, 241))
    d = ImageDraw.Draw(im)
    # 双金框
    d.rectangle([14, 14, W - 14, H - 14], outline=(176, 141, 66), width=6)
    d.rectangle([34, 34, W - 34, H - 34], outline=(204, 176, 106), width=2)
    # 品牌字
    d.text((W // 2, 150), brand, font=f(150), fill=(30, 32, 40), anchor="mm")
    # 品名行
    d.text((W // 2, 300), line, font=f(72, 1), fill=(70, 74, 84), anchor="mm")
    # 渐变三角徽章 (右下)
    bx, by, bs = W - 300, H - 210, 150
    d.rounded_rectangle([bx, by, bx + bs * 2.1, by + bs], radius=int(bs * 0.14),
                        fill=(255, 255, 255), outline=(210, 213, 218), width=2)
    tri = [(bx + 40, by + bs * 0.78), (bx + 40 + bs * 0.62, by + bs * 0.22), (bx + 40 + bs * 1.24, by + bs * 0.78)]
    pts = [tri[0], tri[1], tri[2]]
    for i in range(3):
        d.line([pts[i], pts[(i + 1) % 3]], fill=[(47, 107, 240), (139, 60, 240), (0, 144, 240)][i],
               width=max(4, bs // 12))
    # 条码 (左下)
    barcode(d, 80, H - 190, 420, 120, seed=len(cls))
    d.text((80, H - 210), cls.upper().replace("_", " ")[:28], font=f(34, 1), fill=(90, 94, 104), anchor="la")
    return im


def main(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for cls, (brand, line) in LABELS.items():
        make(cls, brand, line).save(out / f"{cls}.png")
    print(f"labels: {len(LABELS)} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/nv960_labels")
