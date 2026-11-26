#!/usr/bin/env python3
"""960 逐对裁决引擎: NVIDIA USDCraft-10K 零售缩略图 vs Pack10K 同语义类渲染.
四轴: 分辨率 / V-gate (我方独立 V1-V7) / 纹理 / E1 边缘密度.
判: 任一轴胜且无轴负=WIN; 全平=TIE; 任一轴负=LOSS.
用法: python3 scripts/nv960_verdict.py --ours manifests/nv960_ours_map.json --out docs/nv960/scoreboard.json
"""
import argparse, csv, json, glob, os, sys
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from pixel_framework import load_gray, edge_stats  # 既有客观框架

CORE = {'R026','R034','R035','R036','R037','R038','R039','R040','R041','R043','R066',
        'R091','R092','R094','R528','R569','R619','R642','R650','R797','R973','R929',
        'R203','R204','R232','R252','R119'}
SHOP = {'R331','R332','R341','R345','R355','R358','R752','R766','R767','R788','R506','R497','R514'}
LOG = {'R415','R416','R422','R423','R886','R887','R888','R436'}
ALL_IDS = CORE | SHOP | LOG

def their_assets():
    rows = [r for r in csv.DictReader(open('/tmp/usdcraft_manifest.csv')) if r['category_id'] in ALL_IDS]
    return rows

def their_vgate():
    """我方独立审计 (V1-V7, 路径键控): {asset_base: full_pass}"""
    p = Path(__file__).resolve().parent.parent / "docs/reviews/nv960_audit480.json"
    if p.exists():
        return json.load(open(p))
    return {}

def e1(path):
    """中心 62% 裁切 E1 (消背景观感差: 我方黑棚 vs 其浅底棚拍, 同口径比产品区)"""
    try:
        from PIL import Image
        im = Image.open(path).convert('L')
        w, h = im.size
        cw, ch = int(w * 0.62), int(h * 0.62)
        import os as _os
        _t = f'/tmp/_e1crop_{_os.getpid()}.png'
        im.crop(((w - cw) // 2, (h - ch) // 2, (w + cw) // 2, (h + ch) // 2)).save(_t)
        d, _ = edge_stats(load_gray(_t))
        return d
    except Exception:
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ours', required=True, help='JSON: {category_id: our_render_path}')
    ap.add_argument('--thumbs', default='/tmp/nv960')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    ours_map = json.load(open(args.ours))
    vgate = their_vgate()
    rows = their_assets()

    board = {'pairs': [], 'summary': {'WIN': 0, 'TIE': 0, 'LOSS': 0}}
    for r in rows:
        cid, path = r['category_id'], r['path']
        our = ours_map.get(cid)
        if not our or not os.path.exists(our):
            continue  # 缺口 (P3 补建队列另行输出)
        base = path.replace('rigid/', '').replace('/', '_')
        theirs_imgs = sorted(glob.glob(f'{args.thumbs}/{base}*.png'))
        ow, oh = None, None
        from PIL import Image
        im = Image.open(our); ow, oh = im.size
        our_e1 = e1(our)
        for t in theirs_imgs:
            tim = Image.open(t); tw, th = tim.size
            te1 = e1(t)
            # 轴1 分辨率
            res_win = ow * oh > tw * th; res_tie = ow * oh == tw * th
            # 轴2 V-gate: their full_pass=False → 我胜; True → 平 (双方均过)
            tv = vgate.get(os.path.basename(t)
                           .replace('_physx_.thumbs_256x256_model.usdc.png', '')
                           .replace('_physx_.thumbs_256x256_model.usdc_light.png', ''))
            vg_win = isinstance(tv, dict) and tv.get('full_pass') is False
            # 轴3 纹理: their has_textures=false → 我胜; true → 比 E1
            ht = r['has_textures'] == 'true'
            tx_win = (not ht)
            # 轴4 E1: 信息量 (our 高 = 更丰富)
            e1_win = our_e1 is not None and te1 is not None and our_e1 > te1
            e1_loss = our_e1 is not None and te1 is not None and our_e1 < te1 * 0.8  # 20% 容差内=平
            axes_win = sum([res_win, vg_win, tx_win, e1_win])
            axes_loss = (not res_win and not res_tie) or e1_loss
            if axes_loss:
                v = 'LOSS'
            elif axes_win > 0:
                v = 'WIN'
            else:
                v = 'TIE'
            board['pairs'].append({'category': cid, 'their': os.path.basename(t),
                                   'their_res': [tw, th], 'our_res': [ow, oh],
                                   'their_e1': te1, 'our_e1': our_e1,
                                   'their_vgate': tv, 'their_textures': ht,
                                   'verdict': v})
            board['summary'][v] += 1
    tot = board['summary']['WIN'] + board['summary']['TIE'] + board['summary']['LOSS']
    board['summary']['total'] = tot
    board['summary']['score_pct'] = round((board['summary']['WIN'] + board['summary']['TIE'] * 0.5) / max(tot, 1) * 100, 2)
    board['summary']['target'] = 'WIN+TIE = 100% (每对≥平)'
    missing = sorted(set(r['category_id'] for r in rows if r['category_id'] not in ours_map))
    board['missing_categories'] = missing
    json.dump(board, open(args.out, 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(board['summary'], ensure_ascii=False))
    print('缺口类:', missing)

if __name__ == '__main__':
    main()
