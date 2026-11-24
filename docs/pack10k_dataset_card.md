# Pack10K-Retail 数据集卡 (草案 v0.2 — HF 发布口径)

> 对标: nvidia/USDCraft-10K (arXiv 2610.11322)。定位: **零售包装域**的 simulation-ready
> OpenUSD 资产数据集 + **测量有效性证据链** (ESR)。状态: 500 件试点已全绿, 10K 规模化中。

## 数据集一览 (试点口径, 10K 版另行冻结)

| 项 | 值 |
|---|---|
| 资产数 | 500 (4 家族 × 125 变体; 规模化目标 10K+) |
| 家族 | gable_top 系 (屋顶包) / CLV 系 (插舌封盒) / cone_wrap 系 (锥台) / food_packs 系 (食品盒) |
| 格式 | OpenUSD (.usdc, crate), Z-up, metresPerUnit=1, kilogramsPerUnit=1, defaultPrim=/Asset |
| 物理 | PhysX RigidBody+Collision+MassAPI; 质量=展开面积×纸板克重 (解析推导, 非 LLM 拍数) |
| 侧车 | model.json (extents/mass/克重来源) · packaging.json (id/许可/sha256 内容哈希) · conformance.json (逐件验证器检查+已知缺口) · build.json (参数+种子+门禁 = bit 级再生凭证) |
| 缩略图 | .thumbs/256x256/{model.usdc, model.usdc_light}.png 512px, az45°/el30° 朝 −Y (USDCraft 口径) |
| manifest | CSV: asset_id/family/class/seed/状态/三方对账/验证器通过数/调节率先验 |

## 与 USDCraft-10K 的差异 (声明式, 逐条可验证)

| 维度 | USDCraft-10K | Pack10K-Retail |
|---|---|---|
| 单件生产 | LLM 写程序 (4.9min, $0.851) | 家族模板×参数采样 (**0.073s, $0**) |
| 可复现 | LLM 非确定, 产物即凭证 | 种子+参数+模板 SHA → bit 级再生 |
| 尺寸证据 | 记 extents, 无对账 | **声明/折叠/USD 三方对账** (G05 0.5mm 门, 试点 0.0mm) |
| 拒绝样本 | 无 | **REFUSAL_PRIOR 集** (~8%: 近退化参数 + 合同拒绝记录) |
| 制造真值 | 视觉近似 | 刀版可折可印 (SVG/PDF+压线/胶口), 纸板克重物理 |
| 领域 | 1000 类家电家具 | 零售包装拓扑 (他们 1000 类中为零) |
| 外观 | LLM 材质+贴图+贴花 | **无纹理 (已知最大差距, 见"诚实边界")** |
| 关节 | 8222 件带关节 | 少量 (包装拓扑本来少关节, 不对标) |

## 生产链: 全程非 CUDA (实测)

全链在 Apple Silicon (M 系列, 无 NVIDIA GPU) 上运行并计时:

| 段 | 工具 | 后端 | 500 件实测 |
|---|---|---|---|
| 生成+折叠+G03-G10 门禁 | photo_dieline 纯 Python | CPU | 36.6s |
| USD 导出+物理 | pxr (usd-core) + scipy | CPU | (含上) |
| 第三方验证器 | NVlabs/USDCraft _usd_validate | CPU (pxr+numpy) | (含上) |
| 双缩略图 | Blender headless | Metal (Workbench) | 72s |

**合计 ≈109s / 500 件 ≈ 0.22s/件, API 成本 $0**。下游消费同样无 CUDA: MuJoCo CPU 静置
物理验证、任何 USD 查看器。Isaac Sim 不是本数据集的验证依赖 (诚实声明: 未做 Isaac 导入测试,
静态合规+物理作者化不构成运行时行为证明 — 引 USDCraft 同款门禁诚实性措辞)。

## ESR 先验标签 (诚实边界)

manifest 的 `identifiability_prior` 是**几何调节率先验** (尺寸比阈值), 不是可辨识性证明 —
自观测=inverse crime 被禁; 真交付标签 (AUTO/MANUAL/REFUSED) 须由测量层在真实观测上判定
(R5 协议, 冻结于 docs/measurement/r5_real_pilot_protocol*.md)。

## 诚实边界 (发表前必须解决/声明)

1. **外观/纹理为零** — 最大差距 (USDCraft 自评外观也是其最低分项); 印刷版面/材质感缺失;
2. 类别广度: 家族数 vs 他们 1000 类 — 我们走"制造真实模板×深参数空间"路线;
3. 克重为通用材料口径值 — 量产须按采购规格替换 (来源注释已强制);
4. 2 件 gable_top 退化样本 G02 拓扑拒绝 — 保留为拒绝行为记录;
5. 未做 Isaac Sim 导入/运行时测试 (同 USDCraft 门禁诚实性边界)。

## 许可 (待用户确认)

- 代码: Apache-2.0 (与 USDCraft 对齐, 含其验证器引用的署名)
- 数据集: CC-BY-4.0 (默认建议)
- 品牌层: TOPPRISM 徽章化 (无客户资产)
