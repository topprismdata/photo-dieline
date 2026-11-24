#!/usr/bin/env python3
"""pack10k HF 数据集打包器: 试点输出 → HuggingFace 数据集树 (USDCraft 包口径)。

用法: python3 scripts/pack10k_export_hf.py --src output/pack10k_pilot500 --dst output/pack10k_hf
产物: <dst>/
  README.md                # 数据集卡 (frontmatter + 实测数字)
  manifest.csv             # 与生产 manifest 同构 + 布局列
  rigid/<family>/<asset_id>/{physx/model.usdc, physx/print.png, model.json,
                             packaging.json, conformance.json, build.json,
                             .thumbs/256x256/*.png}
上传: hf upload 大文件协议 (hf CLI, 用户 token)。
"""

import argparse
import csv
import datetime
import json
import shutil
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="output/pack10k_pilot500")
    ap.add_argument("--dst", default="output/pack10k_hf")
    args = ap.parse_args()
    src, dst = Path(args.src), Path(args.dst)
    if dst.exists():
        shutil.rmtree(dst)

    rows = list(csv.DictReader(open(src / "manifest.csv")))
    n_main = sum(1 for r in rows if r["sample_set"] == "MAIN")
    n_refusal = sum(1 for r in rows if r["sample_set"] == "REFUSAL_PRIOR")
    vsr = json.loads((src / "independent_vsr.json").read_text())
    today = datetime.date.today().isoformat()

    copied = 0
    for r in rows:
        aid = r["asset_id"]
        sdir = src / aid
        if not (sdir / "model.usdc").exists():
            continue  # 拒绝记录行: 只入 manifest, 无资产
        ddir = dst / "rigid" / r["family"] / aid / "physx"
        ddir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(sdir / "model.usdc", ddir / "model.usdc")
        for f in ("model.json", "packaging.json", "conformance.json", "build.json"):
            if (sdir / f).exists():
                shutil.copy2(sdir / f, ddir.parent / f)
        thumbs = sdir / ".thumbs" / "256x256"
        if thumbs.exists():
            (ddir.parent / ".thumbs" / "256x256").mkdir(parents=True, exist_ok=True)
            for png in thumbs.glob("*.png"):
                shutil.copy2(png, ddir.parent / ".thumbs" / "256x256" / png.name)
        shutil.copy2(sdir / "print.png", ddir / "print.png") if (sdir / "print.png").exists() else None
        copied += 1

    shutil.copy2(src / "manifest.csv", dst / "manifest.csv")
    shutil.copy2(src / "independent_vsr.json", dst / "independent_vsr.json")

    card = f"""---
license: cc-by-4.0
task_categories:
- robotics
- computer-vision
tags:
- openusd
- simready
- retail
- packaging
- synthetic
- digital-twin
size_categories: 100<n<1K
pretty_name: Pack10K-Retail Preview 500
---

# Pack10K-Retail Preview 500

> 零售包装域 simulation-ready OpenUSD 资产预览集。正式 10K 版规模化为 HOLD
> (外部真值 Pack-Real100 与视觉子集成熟度门禁未过, 见 R1 评审)。

- 资产: {copied} (主集 {n_main} + 拒收先验集 {n_refusal}: 其中 {n_refusal - 2} 件带
  几何调节率先验标签资产, 2 件拓扑拒绝仅记录无资产)
- 生产: 参数化模板家族 × 种子化采样, 全链非 CUDA (CPU/Metal), 单件几何段 73ms, API $0
- 独立验收 VSR: {vsr.get('vsr')} ({vsr.get('VSR_pass')}/{vsr.get('assets_validated')};
  验收器异源于生产门禁, 含水密性/退化/尺寸核账/物理字段)
- 逐件: model.usdc (defaultPrim=/Asset, Z-up, m/kg, PhysX 刚体+碰撞+克重推导质量)
  + print.png (程序化占位印刷 v0) + 侧车 (model.json/packaging.json/conformance/build.json)
  + 双缩略图 (az45/el30 朝 −Y)
- 已知边界: 印刷为程序化占位非真实版面; 未做 Isaac 导入运行时测试;
  mass_scope=packaging_empty (不含内容物); qcode 未富化; 2 件拓扑拒绝记录入账

## 布局

```
manifest.csv
independent_vsr.json
rigid/<family>/<asset_id>/
  physx/model.usdc, print.png
  model.json, packaging.json, conformance.json, build.json
  .thumbs/256x256/model.usdc.png, model.usdc_light.png
```

生成于 {today} · 引擎 photo-dieline 参数化模板 (Apache-2.0 候选) · 验证器引用 NVlabs/USDCraft (Apache-2.0)
"""
    (dst / "README.md").write_text(card, encoding="utf-8")
    print(f"HF 树组装完成: {copied} 资产 → {dst}")
    n_refusal_assets = n_refusal - 2
    print(f"  主集 {n_main} + 拒收先验 {n_refusal} ({n_refusal_assets} 带资产 + 2 拓扑拒绝记录) · VSR {vsr.get('vsr')}")
    print(f"  上传: hf upload → hyperion911/pack10k-retail-preview")


if __name__ == "__main__":
    main()
