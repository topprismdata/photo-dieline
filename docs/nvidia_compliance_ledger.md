# NVIDIA 原版验证器合规台账 (2026-11-27)

验证器: NVIDIA USDCraft SDK `_validate_usd_asset(backend='physx')`
(`~/usdcraft_study/code/sdk/_core/_usd_validate.py`, arXiv 2610.11322 官方仓)
15 项结构检查: default_prim=/Asset / Z-up / 米 / 千克 / 无场景 / 有限值 / 依赖闭包 /
相对路径 / vendor 命名空间 / 物理图无环 / articulation 绑定 / PhysX schema 一致性等。

| 域 | 位置 | 件数 | 判决 |
|---|---|---|---|
| 酒饮包装 (simready_usd) | hfpackage/assets_liquor | 16 (M3 结构轴扩容 + M4: vodka×belly / baijiu×straight / whisky×bordeaux / wine×straight / **whisky×shouldered**) | **16/16 PASS** |
| 刚体 legacy | hfpackage/families | 4 | **4/4 PASS** |
| 零售设备正典 | output/nv960_usd | 20 | **20/20 PASS** |
| 设备参数变体 | output/nv960_variants | 35 | **35/35 PASS** |
| TDE 纸包装试点 (gable/clv/cone/food) | output/pack10k_pilot | 100 | **100/100 PASS** |
| **总计** | | **175** | **175/175 PASS** |

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

## usdc 伴生 model.json 快照 (2026-11-27 补)

发行约定补齐: 每个 usdc 旁伴生 model.json (schema 逐字段照抄 NVIDIA 样本:
author/asset_name/asset_license/category/source_file/rigid_body_count/mass/asset_extents)。
170 usdc 全覆盖零缺失; 发射顺序 = 快照先于 BOM/契约 (哈希链含 model.json,
hfpackage 11 资产独立复算 ALL OK)。

## 双缩略图约定 (2026-11-27 补)

对齐 NVIDIA .thumbs 惯例 (256x256, 暗底+亮底双图, 相机契约同 USDCraft 45°/30°):
170 usdc × 2 = **340 png 全覆盖零失败** (批量 Blender 单进程 ~15min, 断点续传清单)。
发射器重跑后 BOM 纳入 thumbs, hfpackage 11 资产哈希链复算 ALL OK。
脚本: scripts/render_thumbs_batch.py (manifest 驱动, 可断点重放)。

## 一体化审计 (2026-11-27)

`scripts/nvidia_audit_all.py` 单命令: 170 件 × {原版验证器实跑 + BOM/content/package 三哈希复算 +
meta 完整性 + 双缩略图齐备} → `docs/nvidia_full_audit_2026-11-27.json` (时间戳证据, fail-closed)。
结果 **170/170 overall PASS**。

## 审计自纠闭环 (2026-11-27 补)

一体化审计首跑抓出 meta_com=0/170 (meta.json 缺 center_of_mass_m — 他们 meta 的
物理消费字段): emitter 补质量加权 COM (来自 MassAPI authored 属性, 即 COM 修复会话
写入的有限值), 修 emitter 静默 except 吞 NameError (模块级缺 UsdPhysics 导入)。
复审计: **meta_com 170/170, overall 170/170 PASS**。

## 10K 规模抽检 (2026-11-27)

10K 生产构建 (9,386 件 GREEN, 我方门禁) 的 NVIDIA 原版验证器随机抽检
(seed=42, 分层覆盖各家族): n=60 → 60/60, **n=300 → 300/300 PASS** (3.06s)。
产能叙事升级: 10K 级产线获工具链背书 (此前仅我方门禁绿)。
证据脚本可复现: 抽样 seed 固定, 验证器实跑。

## 10K 全量普查 (2026-11-27)

9,386 件生产构建资产**全量**过 NVIDIA 原版验证器 (physx): **9,386/9,386 PASS, 52.4 秒**
(非抽检 — 全数普查, docs/scale10k_full_validation.json)。
叙事终态: 10,000 尝试 → 9,386 GREEN (我方 G-F 门禁, 产率 93.9%, 16.4 分钟)
→ 9,386/9,386 NVIDIA 工具链全量背书 (52.4s)。
产能: 我方全量验证吞吐 ~179 件/秒, NVIDIA 单件 $0.851/4.9min。

## M3 结构轴扩容 (2026-11-27 补)

本体映射 11→15 条: 新增 4 组合 = 已注册结构轴的空白填充 (vodka×belly / baijiu×straight /
whisky×bordeaux / wine×straight, 每类独立 lathe profile)。全链: G-F 门禁 → simready 结构化
(pxr 实测 dims/mass 回填) → NVIDIA 原版验证器 4/4 PASS → hfpackage 并入 (spec 15/15) →
打包契约发射 (总 174/174)。

## M4 结构轴收口 (2026-11-27 补)

whisky×shouldered 补齐 — **本体 9 结构轴 9/9 全有资产** (longneck/belly/shouldered/straight/
bordeaux/can_alu/pet_bottle/gable_carton/gift_box_carton)。全链: G-F → 结构化 → NVIDIA
验证器 PASS → spec 16/16 → 契约发射 175/175。

## M5 乳品域 (2026-11-27 补)

dairy 家族 (yogurt_cup_160: 锥度 PP 杯 + 铝箔拱顶膜封, 极点焊接 lathe + 绕序翻转):
G-F → simready (61×61×87.2mm, 0.0402kg) → spec 1/1 → NVIDIA 原版验证器 PASS →
打包契约 176/176。本体结构轴 +1 (cup), 商品轴 yogurt 获首个资产。

## 侧车契约双轨事实 (2026-11-27 补)

10K 构建每件自带 5 文件生产契约侧车 (model.usdc / model.json / packaging.json /
conformance.json / build.json / print.png — 我方 schema, 产线再生凭证)。
NVIDIA 8 文件契约 (meta/root_usds/BOM/双 conformance) 已发射于 175 件精选域;
9386 件构建的 NVIDIA-schema 重发射为可选后处理 (emitter ~0.5s/件), 未执行 —
两套 schema 并存事实记录在案, 消费端按需选择。

## M6 参数收口与审计竞态复盘 (2026-11-27 补)

- 变体产能收口: `_fit_declared_dims` 构造性收口 (声明 H/D 对 Y/Z 仿射缩放, X 随 Y 同比
  保截面) → 变体扫 **60/60 全绿零拦** (原 35/60, 25 个 D 不响应类由构造满足)。
- 审计竞态复盘: 变体重生成后审计 0/60 — 根因 = 变体目录残留**重生成前的陈旧契约**
  (BOM 哈希对旧 usdc)。发射器重跑刷新后复审计 **202/202** (liquor16/dairy2/legacy4/
  canonical20/variants60/tde100)。教训: **资产重生成必须重跑契约发射**, 审计的
  BOM 抽验通道正是此类陈旧的探测器。

## M7 铰接资产与下游物理评测 (2026-11-27 补)

回应外部评审攻击点①(无下游仿真证据)/③(293部件无关节):

- shopping_cart 铰接化: 4 真滚动轮 (Y 轴圆盘, revolute ±360°) + 4 叉架
  (锁定 revolute 焊接底盘) = 8 关节, root=frame_lo 挂 ArticulationRootAPI。
  NVIDIA 原版验证器 PASS (铰接资产类), 全审计仍 202/202。
- **pivot 约定修正**: 发射器 localPos1 原为 (0,0,0), 而部件顶点在资产坐标系
  → 离原点铰点全部错位 (静态验证器不可见)。修正为 localPos0=localPos1=铰点
  资产系坐标。教训: 关节正确性需要下游仿真才能暴露, 静态 Linter 盲区实证。
- MuJoCo 下游评测 (scripts/mujoco_downstream_eval.py): 部件→MJCF (frame 合并
  刚体, 轮=解析圆柱+hinge), 落地+四轮驱动 1200 步: **100% 四轮触地, 净位移
  0.812 m, 轮速 21.2 rad/s, 最大穿透 1.198 mm, 零爆炸 → PASS**。
- 评测器取证: mesh-hull 轮接触扛 111kg 车架时约束力失效整体脱离 (nefc 64→0),
  解析圆柱+implicitfast 修复; MJCF 单位 bug (轮在 -186m 空转 300rad/s) 被
  位移≈自由落体距离的量级对照当场抓出。下游评测即探测器, 与审计同哲学。
- _fit_declared_dims 同步缩放 joint origin (G-F6 由构造满足的必要补丁)。
