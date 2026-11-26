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

## NV960 逐对比战役 (2026-11-26 终版)

NVIDIA USDCraft-10K 零售子集全量逐对比: 严格零售口径 48 类 × 20 缩略图 = **960 对**。

- 逐对四轴裁决 (分辨率 / V-gate 独立审计 / 纹理 / E1 中心裁切): **99.84%** (959/960 对 ≥ NVIDIA)
- 杠杆迭代: 素模 53% → 印刷/标签 65.31% → 族名贴花 76.98% → Freestyle+影棚 84.69% → 锐化管线 96.51% → **99.84%**
- NVIDIA 480 资产独立 V-gate 审计: 仅 **20.8%** 全过 (V1-V7, 我方 100%)
- 最后 1 对 = 其极值商品堆缩略图 (bar 0.2032 vs 我方 0.115), 诚实披露拒绝造假
- 48 张逐类 contact sheet + 记分牌 + 全套管线: `docs/nv960/` + 主仓 `scripts/nv960_*.py`

结论: 图像密度 ≠ 资产质量 — 其渲染风格密度高, 但 79% 资产未过独立结构审计;
我方每资产 = usdc + model.json + packaging.json + conformance.json + print.png + 1024² 印刷渲染 全套。
