#!/usr/bin/env python3
"""NV960 战役: 48 类逐对对比 contact sheet 生成.
输入: docs/nv960/scoreboard.json (逐对裁决) + ours_map + /tmp/nv960 缩略图
输出: docs/images/nv960/contact_sheets/<CID>.png (每类 10 资产 × 2 底 vs 我方渲染 + 判定角标)
"""
import argparse
import json
import glob
import os
from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/Helvetica.ttc"
THUMB_DIR = "/tmp/nv960"

GREEN, RED, GRAY = (55, 178, 108), (224, 82, 82), (128, 134, 148)


def f(sz, index=0):
    return ImageFont.truetype(FONT, sz, index=index)


def thumb_pair(asset_base):
    a = f"{THUMB_DIR}/{asset_base}_physx_.thumbs_256x256_model.usdc.png"
    b = f"{THUMB_DIR}/{asset_base}_physx_.thumbs_256x256_model.usdc_light.png"
    imgs = []
    for p in (a, b):
        if os.path.exists(p):
            im = Image.open(p).convert("RGB")
            im.thumbnail((256, 256))
            imgs.append(im)
    return imgs


def sheet_for(cid, pairs, our_path, out_path):
    """pairs: 该类的逐对记录 (≤10 资产 × 2 底)"""
    cell, pad, head = 256, 8, 46
    theirs = {}
    for p in pairs:
        base = p["their"].replace("_physx_.thumbs_256x256_model.usdc.png", "") \
                          .replace("_physx_.thumbs_256x256_model.usdc_light.png", "")
        theirs.setdefault(base, []).append(p)
    n_assets = len(theirs)
    cols = min(n_assets, 5)
    rows = (n_assets + cols - 1) // cols
    our_img = Image.open(our_path).convert("RGB")
    our_img.thumbnail((cell * 2, cell * 2))
    W = cols * (cell + pad) + pad
    H = head + rows * (cell + 26 + pad) + pad
    canvas = Image.new("RGB", (W, H), (16, 19, 25))
    d = ImageDraw.Draw(canvas)
    d.text((pad, 8), f"{cid}  vs NVIDIA USDCraft-10K", font=f(22), fill=(232, 234, 240))
    # 我方 (左上角大格)
    canvas.paste(our_img, (pad, head))
    d.text((pad, head + our_img.height + 2), "Pack10K (Ours)", font=f(15), fill=GREEN)
    x0, y0 = pad + our_img.width + 12, head
    for i, (base, prs) in enumerate(sorted(theirs.items())):
        cx = x0 + (i % cols) * (cell + pad)
        cy = y0 + (i // cols) * (cell + 26 + pad)
        for k, p in enumerate(prs[:2]):
            im = Image.open(f"{THUMB_DIR}/{p['their']}").convert("RGB")
            im.thumbnail((cell // 2 - 2, cell // 2 - 2))
            canvas.paste(im, (cx + k * (cell // 2), cy))
        verd = "WIN" if all(q["verdict"] == "WIN" for q in prs) else (
            "LOSS" if any(q["verdict"] == "LOSS" for q in prs) else "TIE")
        color = {"WIN": GREEN, "LOSS": RED, "TIE": GRAY}[verd]
        d.rectangle([cx, cy + cell // 2, cx + 46, cy + cell // 2 + 18], fill=color)
        d.text((cx + 4, cy + cell // 2 + 2), verd, font=f(12), fill=(255, 255, 255))
    out = Image.new("RGB", (W, max(H, head + our_img.height + 24)))
    out.paste(canvas, (0, 0))
    out.save(out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--board', default='docs/nv960/scoreboard.json')
    ap.add_argument('--ours', default='manifests/nv960_ours_map.json')
    ap.add_argument('--out', default='docs/images/nv960/contact_sheets')
    args = ap.parse_args()
    board = json.load(open(args.board))
    ours = json.load(open(args.ours))
    by_cat = {}
    for p in board['pairs']:
        by_cat.setdefault(p['category'], []).append(p)
    os.makedirs(args.out, exist_ok=True)
    n = 0
    for cid, prs in sorted(by_cat.items()):
        if cid not in ours:
            continue
        try:
            sheet_for(cid, prs, ours[cid], f"{args.out}/{cid}.png")
            n += 1
        except Exception as e:
            print(f"{cid} FAIL {type(e).__name__} {e}")
    print(f"sheets: {n} -> {args.out}")


if __name__ == "__main__":
    main()
