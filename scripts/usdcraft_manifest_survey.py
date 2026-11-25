#!/usr/bin/env python3
"""USDCraft-10K 零售相关资产/图片对账 (manifest.csv 权威口径).
用法: curl -sL https://huggingface.co/datasets/nvidia/USDCraft-10K/resolve/main/manifest.csv -o /tmp/usdcraft_manifest.csv && python3 scripts/usdcraft_manifest_survey.py
"""
import csv
from collections import Counter

CORE_PACKAGING = {
    'R026','R034','R035','R036','R037','R038','R039','R040','R041','R043','R066',
    'R091','R092','R094','R528','R569','R619','R642','R650','R797','R973','R929',
    'R203','R204','R232','R252','R119'}
SHOPPING_RETAIL = {'R331','R332','R341','R345','R355','R358','R752','R766','R767','R788','R506','R497','R514'}
LOGISTICS = {'R415','R416','R422','R423','R886','R887','R888','R436'}

def main(path='/tmp/usdcraft_manifest.csv'):
    rows = list(csv.DictReader(open(path)))
    by_cat = {}
    for r in rows:
        by_cat.setdefault((r['category_id'], r['category'], r['group']), []).append(r)
    def n(ids):
        return sum(len(v) for k, v in by_cat.items() if k[0] in ids)
    print(f"总资产: {len(rows)} ({len(by_cat)} 类 × 10 变体)")
    for name, ids in [('核心 包装+食品容器', CORE_PACKAGING),
                      ('零售设备', SHOPPING_RETAIL),
                      ('物流容器', LOGISTICS)]:
        a = n(ids)
        print(f"{name}: {len(ids)} 类 / {a} 资产 / {a*2} 缩略图")
    all_ids = CORE_PACKAGING | SHOPPING_RETAIL | LOGISTICS
    a = n(all_ids)
    print(f"合计: {len(all_ids)} 类 / {a} 资产 / {a*2} 缩略图")
    for cid in ('R422', 'R091', 'R043', 'R037'):
        for k, v in by_cat.items():
            if k[0] == cid:
                print(f"战役族 {cid} {k[1]} ({k[2]}): {len(v)} 资产 → {len(v)*2} 缩略图")

if __name__ == '__main__':
    main()
