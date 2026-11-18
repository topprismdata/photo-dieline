# GPT 架构设计评审 (会话 6afda74e-a9fc-83ea-9e58-1144b40273fd, 2026-11-18)
# 抓取方式: backend-api Bearer + mapping 时间序

# 第三轮架构评审：Twins Data Engine（TDE）

<row align="center" gap={2}>
  <badge color="success">方向 APPROVE</badge>
  <badge color="success">不推翻 M1</badge>
  <badge color="info">建议纳入 M2 主轨</badge>
</row>

**我的核心裁决：TDE 应成为参数化主干的训练数据基础设施，而不是另一条独立的刀版生成路线。**

这次新方向实际上补上了原架构中一个重要缺口：此前我们有参数化模板、几何内核和 QA，但缺少规模化的视觉识别与参数恢复能力。

现在可以形成一个更完整的闭环：

**参数化生成 → 合成孪生数据 → 模型学习 → 真实照片识别 → 参数化几何重建 → 制造 QA。**

这与母仓货架 SDG → YOLO 微调的经验具有很强的方法论一致性。

但有一个重要区别：货架检测主要学习视觉目标识别；包装重建还必须学习结构参数之间的几何约束。不能只追求分类准确率。

---

## 1. TDE 插入位置：M2 主轨，并行建设，不设独立 M2.5

<badge color="success">裁决：M2 并行主轨</badge>

不建议单独设 M2.5。

原因是 TDE 与模板扩展存在强依赖：

- 没有模板，就没有可信的参数真值。
- 没有 Geometry IR，就没有统一标签协议。
- 没有折叠验证，就不能判断合成样本的结构是否有效。
- 没有模板扩展，训练数据会不断重复同一种结构。

因此，M2 应拆成两个并行工作流：

| 工作流 A | 工作流 B |
|---|---|
| 模板库扩展 | Twins Data Engine |
| FEFCO 0201 | 参数域采样 |
| Gable-top 完善 | 自动生成配对数据 |
| 结构约束完善 | Blender 域随机化 |
| Manufacturing Profile | 数据集版本与质量审计 |

两条工作流共享 Geometry IR 和 QA，但不互相阻塞所有工作。

### TDE 的位置

<box border radius="lg" padding={3} gap={2}>
  <box background="rgba(22,163,74,0.08)" radius="md" padding={3}>
    **Parametric Template Engine**

    生成已知结构和参数真值
  </box>
  <box align="center"><icon name="arrow-down" color="secondary"/></box>
  <box background="rgba(59,130,246,0.08)" radius="md" padding={3}>
    **Twins Data Engine**

    参数采样 → 3D → Blender 渲染 → 数据集
  </box>
  <box align="center"><icon name="arrow-down" color="secondary"/></box>
  <box background="rgba(59,130,246,0.08)" radius="md" padding={3}>
    **Learning Pipeline**

    T1 分类 → T2 参数回归
  </box>
  <box align="center"><icon name="arrow-down" color="secondary"/></box>
  <box background="rgba(22,163,74,0.08)" radius="md" padding={3}>
    **Existing Manufacturing Pipeline**

    用户确认 / 参数约束 → Geometry IR → SVG/PDF → QA
  </box>
</box>

### TDE 与用户手输三尺寸的关系

这里我建议明确一个原则：

**模型预测值永远不能覆盖 MEASURED 实测值。**

把参数来源分为五级：

| 来源 | Evidence Status | 优先级 |
|---|---|---:|
| 卡尺/可靠实测 | MEASURED | 最高 |
| 已知 CAD 或可信规格文件 | VERIFIED_SOURCE | 高 |
| 几何约束计算 | DERIVED | 中高 |
| 模型回归 | INFERRED | 中低 |
| 系统默认 | DEFAULTED | 最低 |

举例：

用户实测长度 68.3mm，模型预测 67.6mm。

系统不能自动选择 67.6mm，而应该：

1. 保留 MEASURED 68.3mm。
2. 记录 INFERRED 67.6mm。
3. 计算 0.7mm 差异。
4. 检查是否存在透视、结构识别或测量错误。
5. 超出阈值时要求复核。

另外，模型应该支持缺失参数补全，而不是强制要求用户永远输入三个尺寸。

当模型有足够置信度时，可以减少问答；但关键尺寸仍必须满足测量证据或经过验证的约束条件。

**TDE 的产品价值不是取消用户测量，而是减少用户需要测量的次数。**

## 2. T1 + T2 是否取代 M3 的手工识别与问答？

<badge color="success">裁决：同意学习实现，但保留人工兜底</badge>

我建议调整原来的 M3 计划。

原来 M3 中的：
- 自动包装类型推荐；
- 关键尺寸问答；
- 视觉辅助参数识别；

应当改为以 T1+T2 学习模型为核心，人工问答只处理不确定和冲突情况。

但不能把这理解成完全取消问答。

### T1：Package Classification

输入照片，输出包装结构类别及概率分布。

例如：

| 类别 | 预测概率 |
|---|---:|
| Gable-top | 0.94 |
| Folding Carton | 0.03 |
| RSC Carton | 0.02 |
| Other | 0.01 |

分类模型必须支持 UNKNOWN / OUT_OF_SCOPE，而不是强制从已有模板中选一个。

建议验收指标：

- Macro-F1。
- 各类别 Recall。
- UNKNOWN 拒识能力。
- 不同拍摄条件下的分类稳定性。

### T2：Parametric Regression

输入照片及 T1 输出的结构类别，预测模板参数。

例如：

```text
package_type: gable_top

predicted_parameters:
  length_mm: 68.1
  width_mm: 68.5
  body_height_mm: 104.8
  roof_height_mm: 24.2

confidence:
  length: ...
  width: ...
  body_height: ...
  roof_height: ...
```

这里我建议使用**结构条件化的多任务回归**，而不是一个模型直接回归所有包装的所有参数。

例如 Gable-top 和 FEFCO 0201 的参数空间完全不同。

更重要的是，回归结果必须经过模板约束检查：

- 参数范围是否合法？
- 面板尺寸是否闭合？
- 是否满足结构比例约束？
- 是否与照片证据矛盾？
- 是否存在多个可能的结构解释？

模型预测的参数不能直接无条件进入制造输出。

### 建议的智能化工作流

<box border radius="lg" padding={3} gap={2}>
  **真实照片输入**
  <box align="center"><icon name="arrow-down" color="secondary"/></box>
  <box background="rgba(59,130,246,0.08)" radius="md" padding={3}>
    **T1 分类**

    识别包装类型，给出置信度和候选类别。
  </box>
  <box align="center"><icon name="arrow-down" color="secondary"/></box>
  <box background="rgba(59,130,246,0.08)" radius="md" padding={3}>
    **T2 参数回归**

    预测长度、宽度、高度及类型专属参数。
  </box>
  <box align="center"><icon name="arrow-down" color="secondary"/></box>
  <box background="rgba(189,150,80,0.09)" radius="md" padding={3}>
    **Evidence Reconciliation**

    MEASURED 优先，模型补全缺失参数，冲突触发人工确认。
  </box>
  <box align="center"><icon name="arrow-down" color="secondary"/></box>
  <box background="rgba(22,163,74,0.08)" radius="md" padding={3}>
    **Parametric Template**

    输出 Geometry IR，进入原有制造 QA。
  </box>
</box>

我的进一步建议：模型输出不应该只有一个预测数字，还应该输出预测不确定性。

对于参数回归，可以采用分位数回归或经过校准的预测区间。比如：

```text
length:
  estimate: 68.1 mm
  interval_90: [67.4, 68.8]
  evidence: INFERRED
```

这比单纯给出一个 0.95 的模型置信度更有工程价值。

---

## 3. Sim2Real：必须先冻结真实照片 Golden Test Set

<badge color="warning">最高风险：必须设独立验证门</badge>

我认为这次新方向最大的风险不是合成数据量不够，而是：

**模型学会了 Blender 的世界，却没有学会真实包装的世界。**

尤其是包装照片有一些合成渲染很难自然覆盖的现象：

- 纸板微小凹凸和压痕。
- 封口变形。
- 纸张纤维与涂层差异。
- 真实印刷偏色和网点。
- 手机镜头畸变与自动锐化。
- 手持遮挡、反光和不均匀光照。
- 真实包装制造误差。

所以我不接受只用合成测试集报告 T1/T2 成绩。

### 3.1 先冻结真实照片基准集

建议在 TDE 训练之前建立 Real Golden Set。

第一阶段不需要很大，但必须有代表性。

建议首批：

| 数据集 | 数量 | 用途 |
|---|---:|---|
| Synthetic Train | 20,000+ | 初始训练 |
| Synthetic Validation | 3,000+ | 超参数选择 |
| Real Development | 100–200 | 真实域调试 |
| Real Golden Test | 200–300 | 独立最终评估 |

这里的数字是首期建议规模，不是统计学保证。

Real Golden Test 必须：

1. 真实包装实物拍摄。
2. 有真实尺寸或可靠 CAD 基准。
3. 包含不同手机、拍摄距离、角度和光照。
4. 包含不同包装材料和表面状态。
5. 测试样本与训练样本按物理产品和拍摄会话隔离。
6. 在首次模型训练前冻结，并保存数据集版本及校验哈希。

特别强调：不能将同一实物的不同角度照片随机分到训练集和测试集，否则会产生严重的数据泄漏。

### 3.2 三阶段 Sim2Real 验证协议

<box border radius="lg" padding={3} gap={3}>
  <box gap={1}>
    <badge color="info">Experiment A</badge>
    **Synthetic-only Baseline**

    只用合成数据训练，在真实 Golden Test 上测试。

    目的：测量纯合成数据的迁移能力。
  </box>
  <divider color="subtle"/>
  <box gap={1}>
    <badge color="info">Experiment B</badge>
    **Domain Randomization Ablation**

    分别调整光照、背景、相机、材质、印刷、遮挡和图像退化强度。

    目的：确定哪些随机化因素真正改善真实域表现。
  </box>
  <divider color="subtle"/>
  <box gap={1}>
    <badge color="info">Experiment C</badge>
    **Synthetic + Real Fine-tuning**

    使用训练集中的少量真实标注数据进行混合训练或微调。

    目的：判断真实数据是否能显著改善性能，以及改善是否具有跨产品泛化能力。
  </box>
</box>

注意：Real Development 可以参与训练迭代，但 Real Golden Test 永远不能参与训练、阈值选择和模型选择。

### 3.3 域随机化不能只追求随机程度

建议建立六组可控变量：

| 随机化维度 | 主要变化 |
|---|---|
| Camera | 焦距、透视、畸变、拍摄距离 |
| Lighting | 色温、方向、强度、阴影 |
| Material | 纸板粗糙度、反射、折痕 |
| Print | 色偏、纹理、印刷图案、网点 |
| Environment | 背景、桌面、场景、遮挡 |
| Image Quality | 模糊、噪声、压缩、曝光 |

但是必须避免一个错误：随机化越强，不代表真实域泛化越好。

例如把包装变成严重扭曲、不可见的状态，虽然增加了数据多样性，却可能让模型学习到真实业务中不存在的分布。

我建议保留三档：

- REALISTIC：符合真实拍摄分布。
- MODERATE：扩大正常拍摄变化范围。
- STRESS：极端情况，仅用于鲁棒性测试。

三档分别报告，不能混成一个总成绩。

### 3.4 设立明确的 Sim2Real 放行门

建议 T1/T2 都必须分别通过以下测试：

| 指标 | 首期建议门槛 |
|---|---:|
| T1 Real Macro-F1 | ≥0.90 |
| T1 各主要类别 Recall | ≥0.85 |
| T2 关键尺寸 MAE | ≤1.0mm |
| T2 关键尺寸误差 P90 | ≤2.0mm |
| 模板约束合法率 | ≥99% |
| UNKNOWN 拒识 | 单独报告 Precision / Recall |

这些是首期研究目标，不是已经证明可达到的性能承诺。

还要增加一项特别重要的指标：

**参数进入制造主干后的最终几何通过率。**

因为模型预测 68.3mm 并不代表它生成的整张刀版正确。

我建议单独统计：

- 参数预测正确率。
- Geometry IR 生成成功率。
- Geometry QA 通过率。
- 人工修正比例。
- 最终制造验证通过率。

只有最后一项才能真正说明 TDE 给主项目带来了多少价值。

## 4. TDE 是否强化 ADR-001：模型永远不直接生成刀版？

<badge color="success">STRONGLY AGREE — 强化 ADR-001</badge>

我认为这次方向反而让 ADR-001 更有说服力，而且应该把它升级为不可轻易改变的架构原则。

**生成模型负责理解照片，参数化内核负责构造制造几何。**

我建议正式划定三个能力边界：

| 层次 | 技术 | 输出 | 权威性 |
|---|---|---|---|
| Perception | T1 分类模型 | 包装类型 | 识别建议 |
| Parameter Inference | T2 回归模型 | 模板参数及不确定性 | 参数建议 |
| Manufacturing Geometry | Geometry IR + 模板引擎 | 真实制造几何 | 唯一权威 |

T3 也不能改变这个原则。

即使未来训练 photo→Geometry IR 模型，也应当把它定义为候选结构生成器，而不是最终制造文件生成器。

它输出的候选 IR 必须：

1. 通过 JSON Schema。
2. 通过拓扑约束。
3. 通过尺寸闭合。
4. 通过折叠运动学。
5. 通过制造规则。
6. 通过人工或其他独立证据复核。

最终仍由统一的 Geometry Kernel 规范化并导出 SVG/PDF。

### 我建议新增 ADR-009

<box border radius="lg" padding={3} gap={2}>
  <badge color="success">PROPOSED — FREEZE</badge>
  **ADR-009：Learning-to-Parameter, Not Learning-to-Manufacture**

  所有学习模型仅负责包装类型识别、参数推断及候选结构提出。最终制造几何必须由经过验证的参数化模板与 Geometry Kernel 生成。任何学习模型不得绕过制造几何验证直接发布刀版文件。

  **核心理由：**
  - 保持尺寸可追溯。
  - 保持制造规则确定性。
  - 降低生成模型幻觉风险。
  - 维持 SVG/PDF 输出一致性。
  - 允许模型独立升级而不破坏制造内核。
</box>

### 对三条结构数据来源的额外审查

我原则上批准三路来源，但有一个需要补充的治理门。

| 来源 | 裁决 | 处理方式 |
|---|---|---|
| 自有参数化模板 | <badge color="success">GO</badge> | 作为最高可信度的 Ground Truth |
| Sketchfab CC 资产 | <badge color="warning">CONDITIONAL</badge> | 逐资产核验许可证、作者、改编和再分发条件 |
| PackBox / DieCutStudio 输出 | <badge color="warning">CONDITIONAL</badge> | 先核验代码许可、输出版权和使用条款 |

尤其不能认为开源软件输出的刀版就天然可以作为 MIT 项目的训练数据或公开数据集。

我建议 TDE 为每条样本增加：

- `source_type`
- `source_uri`
- `source_license`
- `author`
- `derivative_status`
- `redistribution_allowed`
- `commercial_use_allowed`
- `dataset_split`
- `generator_version`

如果某资产只能用于内部实验，就必须在数据集中隔离，不能混入公开发布的训练数据包。

此外，**自有模板随机生成的数据虽然可以无限增加数量，但不等于无限增加独立信息。** 应该按参数空间、结构变体和真实制造边界衡量覆盖度，而不是用合成图片数量作为项目成绩。

---

## 五、TDE 插入后的 M1/M2/M3 最终重排

我建议不改变 M1，只重构 M2 和 M3。TDE 的数据协议、训练管线和模型评估都进入 M2，T1/T2 从原 M3 提前，T3 保留远期研究。

| 阶段 | 核心任务 | 交付物 | 验收目标 |
|---|---|---|---|
| **M1** | 原定参数化垂直切片 | Gable-top、Geometry IR、SVG/PDF、纯 Python 折叠 QA | 原冻结范围全部通过 |
| **M2-A** | 模板库扩展 | FEFCO 0201、Gable-top 完善、Template Contract | 多模板统一 IR |
| **M2-B** | Twins Data Engine | 参数采样、3D 生成、Blender 渲染、数据集构建 | 孪生数据自动生成和可追溯 |
| **M2-C** | 真实数据基准 | Real Golden Set、标注规范、数据版本管理 | 独立测试集冻结 |
| **M2-D** | T1 分类模型 | 包装类型识别、UNKNOWN 拒识 | 真实域分类验证 |
| **M2-E** | T2 参数回归 | 类型条件化参数预测、置信区间 | 真实域尺寸与几何验证 |
| **M3-A** | 视觉重建增强 | TRELLIS.2、Mesh Analysis、非标结构辅助 | 视觉证据与参数化结构融合 |
| **M3-B** | 智能交互 | 自动补全参数、冲突检测、最少问答 | 降低人工测量与确认成本 |
| **M3-C** | T3 研究 | Photo→Candidate Geometry IR | 探索端到端结构生成，不绕过制造 QA |

### 建议的执行依赖关系

```text
M1: Parametric Manufacturing Core
                |
                v
       +--------+---------+
       |                  |
       v                  v
M2-A Template Engine   M2-B TDE
       |                  |
       +--------+---------+
                |
                v
       M2-C Real Golden Set
                |
                v
          +-----+-----+
          |           |
          v           v
       T1 Class    T2 Regression
          |           |
          +-----+-----+
                |
                v
       Evidence Reconciliation
                |
                v
       Parametric Geometry IR
                |
                v
       Manufacturing QA
                |
                v
            M3 Vision
                |
                v
         T3 Exploratory
```

这里有一个执行顺序上的细节：M2-B 可以先用 M1 的 Gable-top 模板开始开发，不必等待 M2-A 的所有模板完成；M2-C 的真实 Golden Set 应尽早冻结，不能等模型训练完成才开始采集。

## 六、最终架构决议

建议在现有 ADR-001 至 ADR-008 之外，增加以下三项：

| ADR | 新决策 | 裁决 |
|---|---|---|
| ADR-009 | Learning-to-Parameter, Not Learning-to-Manufacture | <badge color="success">APPROVE</badge> |
| ADR-010 | Synthetic-to-Real Evaluation Protocol | <badge color="success">APPROVE</badge> |
| ADR-011 | Dataset Provenance & Licensing | <badge color="success">APPROVE</badge> |

我的最终判断：

**TDE 不是给项目增加一条 AI 功能，而是把项目从一个参数化刀版工具，升级为一个具有持续学习能力的包装几何重建系统。**

但要守住三个边界：

1. **M1 不动。** 先完成确定性的制造几何闭环。
2. **M2 建立数据飞轮。** 模板生成真值，真值训练模型，真实照片验证模型。
3. **M3 扩展视觉智能。** 模型提高输入自动化程度，但不接管制造几何的最终决定权。

我尤其赞成将母仓的货架 SDG → YOLO 微调经验迁移过来，但不要简单复制训练流程。包装项目需要增加结构拓扑、参数约束、折叠闭合和制造可行性这些独有的标签与验证机制。

<box border radius="lg" padding={3} gap={2}>
  <title size="xl" color="success">第三轮评审：APPROVE</title>
  **最终冻结意见**

  - M1：维持原冻结范围。
  - TDE：纳入 M2 主轨，与模板扩展并行。
  - T1/T2：提前到 M2。
  - Sim2Real：独立 Golden Test 硬门。
  - T3：保留 M3 研究，不作为交付承诺。
  - ADR-001：强化，不修改。
  - 新增 ADR-009/010/011。
</box>

**我认为现在已经形成了一个非常清晰的长期技术路线：先有可信的几何真值，再有规模化孪生数据，最后让模型学习如何从真实照片恢复这些几何真值。**

这条路线值得投入，而且比直接训练一个端到端照片生成刀版模型稳健得多。

=====CONT=====

## 五、TDE 插入后的 M1/M2/M3 最终重排

我建议不改变 M1，只重构 M2 和 M3。TDE 的数据协议、训练管线和模型评估都进入 M2，T1/T2 从原 M3 提前，T3 保留远期研究。

| 阶段 | 核心任务 | 交付物 | 验收目标 |
|---|---|---|---|
| **M1** | 原定参数化垂直切片 | Gable-top、Geometry IR、SVG/PDF、纯 Python 折叠 QA | 原冻结范围全部通过 |
| **M2-A** | 模板库扩展 | FEFCO 0201、Gable-top 完善、Template Contract | 多模板统一 IR |
| **M2-B** | Twins Data Engine | 参数采样、3D 生成、Blender 渲染、数据集构建 | 孪生数据自动生成和可追溯 |
| **M2-C** | 真实数据基准 | Real Golden Set、标注规范、数据版本管理 | 独立测试集冻结 |
| **M2-D** | T1 分类模型 | 包装类型识别、UNKNOWN 拒识 | 真实域分类验证 |
| **M2-E** | T2 参数回归 | 类型条件化参数预测、置信区间 | 真实域尺寸与几何验证 |
| **M3-A** | 视觉重建增强 | TRELLIS.2、Mesh Analysis、非标结构辅助 | 视觉证据与参数化结构融合 |
| **M3-B** | 智能交互 | 自动补全参数、冲突检测、最少问答 | 降低人工测量与确认成本 |
| **M3-C** | T3 研究 | Photo→Candidate Geometry IR | 探索端到端结构生成，不绕过制造 QA |

### 建议的执行依赖关系

```text
M1: Parametric Manufacturing Core
                |
                v
       +--------+---------+
       |                  |
       v                  v
M2-A Template Engine   M2-B TDE
       |                  |
       +--------+---------+
                |
                v
       M2-C Real Golden Set
                |
                v
          +-----+-----+
          |           |
          v           v
       T1 Class    T2 Regression
          |           |
          +-----+-----+
                |
                v
       Evidence Reconciliation
                |
                v
       Parametric Geometry IR
                |
                v
       Manufacturing QA
                |
                v
            M3 Vision
                |
                v
         T3 Exploratory
```

这里有一个执行顺序上的细节：M2-B 可以先用 M1 的 Gable-top 模板开始开发，不必等待 M2-A 的所有模板完成；M2-C 的真实 Golden Set 应尽早冻结，不能等模型训练完成才开始采集。

## 六、最终架构决议

建议在现有 ADR-001 至 ADR-008 之外，增加以下三项：

| ADR | 新决策 | 裁决 |
|---|---|---|
| ADR-009 | Learning-to-Parameter, Not Learning-to-Manufacture | <badge color="success">APPROVE</badge> |
| ADR-010 | Synthetic-to-Real Evaluation Protocol | <badge color="success">APPROVE</badge> |
| ADR-011 | Dataset Provenance & Licensing | <badge color="success">APPROVE</badge> |

我的最终判断：

**TDE 不是给项目增加一条 AI 功能，而是把项目从一个参数化刀版工具，升级为一个具有持续学习能力的包装几何重建系统。**

但要守住三个边界：

1. **M1 不动。** 先完成确定性的制造几何闭环。
2. **M2 建立数据飞轮。** 模板生成真值，真值训练模型，真实照片验证模型。
3. **M3 扩展视觉智能。** 模型提高输入自动化程度，但不接管制造几何的最终决定权。

我尤其赞成将母仓的货架 SDG → YOLO 微调经验迁移过来，但不要简单复制训练流程。包装项目需要增加结构拓扑、参数约束、折叠闭合和制造可行性这些独有的标签与验证机制。

<box border radius="lg" padding={3} gap={2}>
  <title size="xl" color="success">第三轮评审：APPROVE</title>
  **最终冻结意见**

  - M1：维持原冻结范围。
  - TDE：纳入 M2 主轨，与模板扩展并行。
  - T1/T2：提前到 M2。
  - Sim2Real：独立 Golden Test 硬门。
  - T3：保留 M3 研究，不作为交付承诺。
  - ADR-001：强化，不修改。
  - 新增 ADR-009/010/011。
</box>

**我认为现在已经形成了一个非常清晰的长期技术路线：先有可信的几何真值，再有规模化孪生数据，最后让模型学习如何从真实照片恢复这些几何真值。**

这条路线值得投入，而且比直接训练一个端到端照片生成刀版模型稳健得多。
