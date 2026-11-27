# NVIDIA 原版验证器合规台账 (2026-11-27)

验证器: NVIDIA USDCraft SDK `_validate_usd_asset(backend='physx')`
(`~/usdcraft_study/code/sdk/_core/_usd_validate.py`, arXiv 2610.11322 官方仓)
15 项结构检查: default_prim=/Asset / Z-up / 米 / 千克 / 无场景 / 有限值 / 依赖闭包 /
相对路径 / vendor 命名空间 / 物理图无环 / articulation 绑定 / PhysX schema 一致性等。

| 域 | 位置 | 件数 | 判决 |
|---|---|---|---|
| 酒饮包装 (simready_usd) | hfpackage/assets_liquor | 11 | **11/11 PASS** |
| 刚体 legacy | hfpackage/families | 4 | **4/4 PASS** |
| 零售设备正典 | output/nv960_usd | 20 | **20/20 PASS** |
| 设备参数变体 | output/nv960_variants | 35 | **35/35 PASS** |
| TDE 纸包装试点 (gable/clv/cone/food) | output/pack10k_pilot | 100 | **100/100 PASS** |
| **总计** | | **170** | **170/170 PASS** |

## 方言模型 (对照实验裁决)

NVIDIA 发行 = 按后端分目录 (physx/model.usdc), 单文件单方言; 其自家带关节件同样
generic/newton FAIL / physx PASS (R168 shelf 对照实验, 见 usdcraft_study.md §〇e)。
我方全部 170 件 = PhysX 方言, 验证后端与方言匹配。

## 关键对标点

- shopping_cart (293 部件钢丝网格) = NVIDIA 论文自报 Reconstruction 失败案例类型
  ("细网格购物车钢丝重建失真") — 我方参数化 authoring 一次过其全量校验, 且已真参数化
  (H 驱动框/柄/载货, 620/775/969mm 三档全绿)
- G-F4 尺寸对账门禁 (声明 mm vs 实测 bbox, 容差 max(1mm, 1%)) 逐件仲裁参数真实性 —
  变体扫实截 25 个假参数变体; NVIDIA 10K 无逐件对账 (bench 抽检 60+40 件)
- 参数族产能: 1 次 authoring → N 件验证背书实例, 编译+门禁+导出 ~2.0s/件

## 打包契约对齐 (2026-11-27)

对齐 NVIDIA USDCraft-10K per-asset 打包 schema (8 文件契约):
meta.json / com.nvidia.simready.packaging.json / .metadata/{root_usds, packaging.bom,
conformance.Package@1.0.0, conformance.Package-Candidate@1.3.0}.json。
发射器: `scripts/emit_nvidia_package.py` (hfpackage 11 资产)。

- **conformance fail-closed**: FET_031/033 pass 标志来自发射时 NVIDIA 原版验证器实跑判决,
  非缓存声明; 验证失败则 passed=false 并带错误串
- 哈希语义 (我方显式定义, 其内部链序未公开):
  content_hash = BOM 文件集按 relative_path 排序的 sha256 摘要链;
  package_hash = 去除 package_hash 键的 canonical packaging.json 的 sha256 (自指排除)
- 独立复核器同口径复验: BOM 抽样哈希/content_hash/package_hash 11/11 OK
- 证据: docs/nvidia_package_emit_results.json

## 打包契约全域覆盖 (2026-11-27 补)

发射器扩展至全部五域 (hfpackage 11 / nv960 正典 20 / 设备变体 35 / TDE 试点 100 / legacy 4):
**170/170 conformance PASS** (conformance = 发射时原版验证器实跑判决, fail-closed)。
每域 meta 源: liquor=metadata.json / nv9正典=family重算 / 变体=文件名解码参数 / TDE=既有model.json / legacy=stage内省。
证据: docs/nvidia_package_emit_results.json (170 条判决)。
