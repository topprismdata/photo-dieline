---
license: apache-2.0
task_categories:
- robotics
- image-to-3d
tags:
- retail
- digital-twin
- usd
- simulation-ready
- physx
- nvidia-usdcraft
- packaging
size_categories:
- n<1K
---

# Pack10K Retail Twin — 对标子集 v0.1 (4 families)

对标 NVIDIA USDCraft-10K 的零售数字孪生资产管线首个公开发布子集。
每件资产 = 参数化 IR → 折叠/装配 → **逐刚体 usdc (Physx 方言)** → **NVIDIA USDCraft 官方验证器 physx 后端 PASS 15 项** → 合同棚拍渲染。

## 与 USDCraft 的关系

- 结构逐位同构: `/Asset/Links/{carton_body,flap_*}/Visuals|Collisions/Geom` + `UsdPhysics` RigidBody/Mass/RevoluteJoint + `PhysxArticulationAPI` (与 ds_R422 实测结构一致)
- 独立复验: NVlabs/USDCraft `sdk/_core/_usd_validate.py` backend=physx → **PASS 15 checks** (与其自家资产同判)
- 对抗性视觉评审 (GPT 四轮): R422 瓦楞箱 **7.4 vs 7.8 打平**, R043 拉环罐 **7.3 vs 7.5 打平** (docs/reviews)

## Families

| family | class | parts | joints | mass | dims mm | 验证 |
|---|---|---|---|---|---|---|
| bottle_wine | bottle_wine | 2 (双层玻璃壳+软木塞) | 0 | 0.4008 kg | 76×76×300 | generic 10 + physx 15 PASS |
| beverage_can_330 | beverage_can_330 | 4 (body/lid/拉环/铆钉) | 1 revolute 绕Z (0-165°) | 0.0121 kg | 66×66×115 | physx 15 PASS |
| food_container_1l | food_container_1l | 5 (base/lid/铰链带/双扣件) | 1 revolute 绕X (0-180°) | 0.0882 kg | 130×100×90 | physx 15 PASS |
| rsc_rsc_closed | rsc_rsc (RSC 0201) | 5 (墙环体+4顶翼) | 4 revolute (0-180°) | 0.0938 kg | 193.9×121.2×97.4 | physx 15 PASS |

## 结构

```
families/*.usdc        # 逐刚体 USD (Crate), physx 方言, closed 态
renders/*.png          # 渲染合同 v3 棚拍 (确定性取景 fill=0.78, 三点灯 100/30/45, AgX)
docs/                  # 作者合同 + 渲染合同 + GPT 对抗评审四轮全文 + 对照板
```

## 生成管线 (GitHub: topprismdata/photo-dieline)

LLM Author 循环 (合同约束程序合成, 对齐 USDCraft 单文件 Author 模式):

```
作者合同 G-F1..F7 (有限性/封闭流形/落地/尺寸/材质/关节/家族语义)
→ GPT Author 产出家族模块 → author_compile.py 编译期门禁
→ export_parts_usdc (physx 方言 usdc) → NVlabs USDCraft 验证器复验
→ 渲染合同 v3 棚拍 → GPT 对抗性视觉评审循环
```

失质资产打回作者修复 (实测: bottle 一次过, hinged 1 轮回注修复后过)。

## 已知边界 (如实声明)

- R091/R037 视觉评分未打平 NVIDIA 参照 (差 1.1/2.3), 路径已明确 (玻璃光学/细节可读性)
- 渲染为合同棚拍白模口径, 非照片级材质扫描
- 印刷层未挂接 (articulation 模式 plain kraft)

## 引用

```bibtex
@misc{pack10k2026,
  title={Pack10K Retail Twin: Contract-Gated LLM Author Pipeline for Simulation-Ready Retail Assets},
  author={topprismdata},
  year={2026},
  url={https://github.com/topprismdata/photo-dieline}
}
```

## NV960 逐对比战役 (2026-11-26 诚实终版)

NVIDIA USDCraft-10K 零售子集全量逐对比: 严格零售口径 48 类 × 20 缩略图 = **960 对**。

- 像素级审计 (七指标阶梯) 发现并撤回背景颗粒混杂 → 诚实双口径:
  - **严格四轴: 90.94%** (873W/87L, 任一轴负即判负)
  - **像素复合: 82.0%** 对净胜 (S1 锐度 98.1% / E1 88.4% / E2 70.2% 真三轴)
- 混杂量化: 影棚背景 TexNoise 细噪贡献 E1 胜率 8.4pp (96.8→88.4), 其 256² 压缩丢颗粒对比不对等
- NVIDIA 480 资产独立 V-gate 审计: 仅 **20.8%** 全过 (我方 100%) — 图像密度 ≠ 资产质量
- 诚实管线: 净背景棚拍 + 产品侧 UnsharpMask + pitch 谱参数化 + 族名贴花 + 高频印刷货箱
- 撤回的 99.84% 版本留 git (509f71c) 作单一指标可被无意识刷高的教材案例
- 全套管线: `docs/nv960/` + 主仓 `scripts/nv960_*.py` (verdict/render/labels/sharpen/pixel_audit)
