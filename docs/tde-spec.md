# TDE 冻结规范 V0.1（Twins Data Engine Synthetic Data Spec）

> GPT 第四轮架构评审冻结版（2026-11-18，判决 APPROVE WITH EXPERIMENTAL VALIDATION）。
> 原文见 `reviews/gpt_design_all_rounds.md` 第四轮。数值为冻结的首版工程采样范围，
> 非宣称已由真实手机照片统计校准的分布（后续用真实 EXIF/标注校准）。

## 0. 三条总原则

1. 六维随机化必须**分层+相关性约束**采样，不许各维独立乱随；手机拍摄分布是基准（非单反棚拍）。
2. **先结构多样性，再渲染数量**：100 万张同一盒型不如 100 个独立结构变体。
3. T2 成功标准不是合成集 MAE，而是**未见真实包装上预测参数能否过 Geometry IR 与制造 QA**。

TDE 三大长期指标：Structural Coverage / Sim2Real Transfer / **Manufacturing Yield**（最终贡献）。

## 1. 六维随机化 V0.1（REALISTIC / MODERATE / STRESS）

三档比例冻结 **70 / 25 / 5**，每样本必须记录档位标签。

### 1.1 Camera（最高优先级，手机等效）

| 参数 | REALISTIC | MODERATE | STRESS | 分布 |
|---|---|---|---|---|
| 等效焦距 | 24–70mm | 20–85mm | 16–100mm | 分段混合（主摄广角 24-28 / 裁切 35-50 / 长焦 65-70 三区间） |
| 俯角 | -15°–35° | -30°–45° | -50°–60° | 三角分布 |
| 水平偏航 | ±35° | ±60° | ±85° | 均匀 |
| 滚转 | ±5° | ±12° | ±25° | 截断正态 |
| 拍摄距离 | 25–100cm | 15–150cm | 10–250cm | 对数均匀 |
| 光轴偏移 | 0–10° | 0–20° | 0–35° | 截断正态 |
| 主体画面占比 | 45–85% | 30–90% | 15–95% | 分段均匀 |
| 镜头畸变 | 0–1% | 0–2% | 0–4% | 分段 |
| 景深 | f/1.7–f/4 | f/1.4–f/5.6 | f/1.2–f/8 | 按模糊半径 |

等效焦距≠Blender 实际焦距，须按传感器换算；俯角正负号代码内统一。

### 1.2 Lighting

| 参数 | REALISTIC | MODERATE | STRESS |
|---|---|---|---|
| 色温 | 3000–7500K | 2500–9000K | 2000–12000K |
| 曝光 | ±1.5EV | ±2.5EV | -4~+3EV |
| 主光强度 | 0.5–2× | 0.25–3× | 0.1–5× |
| 环境光比例 | 0.2–0.8 | 0.1–0.9 | 0.02–1.0 |
| 色偏 ΔE | 0–5 | 0–10 | 0–20 |

光照组合约束（联合分布，禁独立组合出无意义样本）：室内暖光 3000-4500K / 混合 3500-6500K / 窗边 4500-7500K / 阴天 5500-8000K。

### 1.3 Material

粗糙度 0.25–0.75（MODERATE 0.15–0.9，STRESS 0.05–1.0，截断 Beta）；微凹凸 0–0.15mm；压痕深度 0–0.3mm（零膨胀）；折痕宽 0.3–2mm。
**纸板厚度属结构真值**：改厚度必须重算折叠补偿/面板偏移/折痕位置，否则 IR 标签错。

### 1.4 Print（APPROVE WITH EVIDENCE LIMIT）

分两子系统：外观图案随机化（虚构品牌图案，避免模型依赖品牌 logo 学尺寸）与印刷缺陷随机化（ΔE/网点 60-175LPI/套印 0-0.2mm/磨损/模糊）。
**诚实边界**：无直接文献支撑"纸包装印刷随机化→几何回归"，Print 数值为工程先验。

### 1.5 Environment

七类场景：白底棚拍 / 厨房 / 办公桌 / 超市货架 / 仓储 / 手持 / 室内桌面。**白底棚拍 ≤15%**。
遮挡 0–5%（STRESS 0–30%，关键结构区加权）；主体偏心 0–10%。

### 1.6 Image Quality（ISP 近似链）

分辨率 720–4032px；JPEG Q75–95；高斯 σ0–0.6px；运动模糊 0–2px；ISO 条件化噪声；锐化 halo；白平衡 ±300K。
**JPEG≠完整退化模型**：须实现可配置 ISP 近似链 `LinearRGB → WB/CC → 降噪/锐化 → 局部色调映射 → 缩放/JPEG`。

## 2. 采样策略

- **分层 40% + Latin Hypercube 40% + Active Sampling 20%**（每轮生成预算比）；类别变量分层、连续变量 LHS、错误集中区主动补。
- 禁全参数网格（6 维 5-7 档即 3 万组合，大量无意义样本）。
- **CaptureProfile 先选档再采样**：`PHONE_INDOOR / PHONE_WINDOW_LIGHT / PHONE_SUPERMARKET / PHONE_HANDHELD / PHONE_DESKTOP / PHONE_LOW_LIGHT`，档内联动（近距↔焦距/畸变/景深；暗光↔ISO/降噪；手持↔运动模糊/偏心）。

### 结构多样性

| 级别 | 独立结构变体 |
|---|---|
| MVE | 30 |
| TDE 首期 | 60 |
| M2 稳定 | 100 |

结构距离 Ds=Σwᵢ·|pᵢ-pᵢ'|/rᵢ：Ds<0.05 近重复；≥0.15 独立变体候选。**仅改颜色/印刷不计独立变体；结构变化必须改变 Geometry IR。** 每变体跨多 CaptureProfile，禁结构-背景绑定。

## 3. 数据治理

每样本：`source_type/source_uri/source_license/derivative_status/redistribution_allowed/dataset_split/generator_version` + 可反查参数真值/IR/渲染配置。
`dataset_manifest.json`：dataset_version / generator_version / template_version / ir_schema_version / randomization_profile / sample_count / structure_count / split / license_manifest / content_hash。
同一实物照片必须同分区（防泄漏）；真实 Golden Set 训练前冻结+哈希。

## 4. T2 学习基线

- 首期单箱型：**ResNet18 + 384² + Quantile Regression（Q10/Q50/Q90，区间须真实验证集校准）**。
- 辅助任务只留两个：**面板分割 + 折线/边界检测**（不做品牌识别/OCR）。
- 多箱型：Shared Backbone + **Per-type Heads**（2-5 类）；MoE 类多且专家头互补时再引入。
- 输入：MVE 单照片（先证明单照片可观测性）；多照片（正+侧+顶）为后续高精度模式。
- 标签三分离：`nominal_geometry / observed_geometry / manufacturing_deviation`。

## 5. MVE 两周实验（gable-top）

| 项 | 数值 |
|---|---|
| 合成 | 5,000 张（30 变体 × ~167 拍摄实例，70/25/5） |
| 真实 | 30 个不同实物 × 3 视角 = 90 张（20 训练/开发 + **10 冻结测试**） |
| 实验 | E0 纯 REALISTIC / E1 三档随机化 / E2 E1+真实微调；**E-BASE 参数中位数非学习基线** |

通过门槛：合成验证 MAE ≤0.5mm；真实 Golden 参数 MAE ≤1.0mm、P90 ≤2.0mm；参数合法率 ≥99%；IR 生成成功率 100%；超中位数基线 ≥20%；E1 比 E0 至少两个主要参数方向改善；制造 QA 无结构性失败。
10 个测试实物仅为初步证据，不宣称跨品牌/材料/手机泛化。

## 6. 参考文献（按精读优先级）

1. **Tobin et al. 2017**, Domain Randomization for Transferring Deep Neural Networks from Simulation to the Real World — 理论基础；不支持"越真实越好"，随机化目标是让真实落入合成分布覆盖。
2. **Denninger et al. 2020**, BlenderProc — 工程实现蓝本（程序化场景/渲染/标签）。
3. **Mishra et al. 2022**, Task2Sim (CVPR) — 任务导向采样：随机化参数按下游任务表现调，非越多越好。
4. **Kamo & Ishizaka 2023**, Product object detection using pseudo-generated product shelf images — 零售特化（货架先验/促销遮挡/拍摄质量）。
5. **Geng et al. 2025**, One View, Many Worlds (单图 6D 位姿 × 生成式域随机化) — 与"单照片→参数+尺度"最接近的任务范式。
6. Roberts et al. 2021 Hypersim（场景级真值管理）；Borrego et al. 2018（随机化消融）；Zhu et al. 2025 工业域随机化综合研究（逐因素消融）；Abdul Hay et al. 2025/2026（Fibonacci 视点采样）。

## 7. 边界

Blender headless 留在 TDE 数据生成，不进 M1 CI；本轮后冻结设计，下一步直接进 TDE 生成器实现与 MVE 实验，不再扩随机化维度。
