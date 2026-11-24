# Pack10K-R1 评审判决 — 6b05e5e5-b328-83ea-9f7e-0b9d6384a512

- 会话: chatgpt.com/c/6b05e5e5-b328-83ea-9f7e-0b9d6384a512
- 抓取: backend, 2026-11-25, parts=2 字符=31174

---

# 两项独立设计评审：U1 诊断知识图谱 / Pack10K R1

两个项目虽然属于不同领域，但有一个共同的研究命题：**工程过程能否把 AI 从生成看似合理的答案，提升为生成具有可验证证据、明确适用边界、允许反证的工程成果。**

我的初步裁决如下：

| 项目 | 裁决 | 核心问题 |
|---|---|---|
| U1 诊断知识图谱 | 有条件 APPROVE | 本体方向正确，但因果裁决与知识失效机制尚未形成完整契约 |
| Pack10K 生产架构 | 有条件 APPROVE | 几何生产能力初步成立，数据集研究价值尚未充分证明 |
| Pack10K 正式发表 | HOLD | 外观、覆盖度、物理真实性与下游任务验证不足 |
| GLM+过程 vs OpenAI 裸模型 | APPROVE EXPERIMENT | 可以立项，但不能直接以跨模型比较证明过程价值 |

# 一、U1 混色打印诊断知识图谱

## 1. SEPIO + PROV-O 不重，但不要把标准本身变成建设目标

我支持采用这两个标准的语义子集，不支持完整实现其本体体系。

你真正需要管理的不是几千个实体，而是同一项知识在不同证据、不同机器状态、不同版本下的可信性变化。

普通知识库记录的是「我知道什么」，而你的系统必须记录「我为什么认为自己知道，以及什么情况下我不再有资格这样认为」。

<box border radius="lg" padding={3} gap={2}>
  <svg viewBox="0 0 340 232" width="100%">
    {#each [{x:8,y:8,w:154,h:43,t:"文档 / 配置 / 源码",s:"知识来源"},{x:178,y:8,w:154,h:43,t:"G-code / 实机 / 照片",s:"执行与观测"},{x:83,y:70,w:174,h:42,t:"Evidence Line",s:"证据组合与对照有效性"},{x:83,y:131,w:174,h:40,t:"Claim + Scope",s:"有适用边界的主张"},{x:83,y:190,w:174,h:34,t:"Adjudication",s:"裁决 / 反证 / 失效"}] as n}
      <rect x={n.x} y={n.y} width={n.w} height={n.h} rx="6" fill="#64748b" fillOpacity=".09" stroke="#64748b" strokeOpacity=".7"/>
      <text x={n.x+n.w/2} y={n.y+16} fontSize="11" fill="currentColor" fontWeight="600" textAnchor="middle">{n.t}</text>
      <text x={n.x+n.w/2} y={n.y+29} fontSize="9" fill="currentColor" opacity=".7" textAnchor="middle">{n.s}</text>
    {/each}
    <g stroke="#64748b" fill="none" strokeWidth="1.3"><path d="M85 51 V60 H170 V70 M255 51 V60 H170 M170 112 V131 M170 171 V190"/><path d="M166 65 L170 70 L174 65 M166 126 L170 131 L174 126 M166 185 L170 190 L174 185"/><path d="M257 207 H320 V151 H257" strokeDasharray="4 3"/><path d="M262 147 L257 151 L262 155"/></g>
    <text x="289" y="182" fontSize="9" fill="currentColor" textAnchor="middle">反证更新</text>
  </svg>
  <caption>诊断知识的最小认知闭环：来源不是结论，证据不是裁决，裁决可以被推翻。</caption>
</box>

13 张表本身完全不过度。SQLite 管理这个规模的数据几乎不存在性能压力。真正的过度设计风险是：建立了大量实体类型，却没有任何机制阻止错误推理。

另外，你声称有 13 张表，但需求书实际只列出了 9 张命名表。正式冻结前必须对齐。

SEPIO 本身就是为了表达科学主张及其证据而设计的，PROV-O 则是 W3C 的来源追溯标准。你选择的方向有成熟理论依据，不需要重新发明一套认知本体。<Cite refs={["turn280025search7","turn280025search18","turn280025search25"]}/>

### MVP：建议冻结为 10 张核心表

| 表 | 职责 | 裁决 |
|---|---|---|
| kg_entity | 设备、耗材、配置、缺陷、运行实例 | 保留 |
| kg_claim | 原子主张与认知类型 | 保留 |
| kg_scope | 主张成立的条件 | 保留 |
| kg_evidence | 原始证据及定位、哈希 | 保留 |
| kg_evidence_line | 证据组合、立场、有效性 | 必须保留 |
| kg_evidence_line_item | 证据组合成员 | 必须保留 |
| kg_activity | 切片、打印、实验、抽取活动 | 替代 kg_experiment |
| kg_adjudication | 追加式认知裁决 | 必须保留 |
| kg_dependency | 依赖关系及版本失效传播 | 保留 |
| kg_claim_member | 多因组合、竞争假设成员 | 新增 |

Printer、Toolhead、Filament、Preset、Document 不需要分别建表。首版可以通过 `kg_entity.entity_type + 类型化 JSON Schema` 管理。

FTS5 虚拟表、索引和 SQLite 内部表不计入领域核心表数量。

暂时不做 OWL 推理器、SPARQL、向量检索、贝叶斯网络。也不必为了图谱的名称引入 Neo4j。

## 2. 因果模型必须重构：禁止裸因果边

这是 U1 方案最大的 P0 风险。

`Defect → caused_by → RootCause` 这个结构天然诱导系统寻找一个原因，而不是理解一个机制。

建议废除作为直接事实写入的 `caused_by` 边。所有因果关系必须通过带 Scope 和 Evidence Line 的 Claim 表达。

<box border radius="lg" padding={3} gap={2}>
  <svg viewBox="0 0 340 245" width="100%">
    <rect x="95" y="5" width="150" height="29" rx="5" fill="#dc2626" fillOpacity=".09" stroke="#dc2626"/>
    <text x="170" y="23" textAnchor="middle" fontSize="11" fill="currentColor">Tesla 打印失败（观测）</text>
    <path d="M170 34 V52 M170 52 H82 V65 M170 52 H258 V65" stroke="#888" fill="none"/>
    <rect x="5" y="65" width="154" height="36" rx="5" stroke="#888" fill="#888" fillOpacity=".07"/>
    <rect x="181" y="65" width="154" height="36" rx="5" stroke="#888" fill="#888" fillOpacity=".07"/>
    <text x="82" y="80" fontSize="10" textAnchor="middle" fill="currentColor">H1：单一 Local-Z 原因</text>
    <text x="82" y="94" fontSize="9" textAnchor="middle" fill="#d97706">未建立单独因果</text>
    <text x="258" y="80" fontSize="10" textAnchor="middle" fill="currentColor">H2：多因素组合机制</text>
    <text x="258" y="94" fontSize="9" textAnchor="middle" fill="#d97706">候选 / 待验证</text>
    <path d="M258 101 V113 H170 V127" stroke="#888" fill="none"/>
    <rect x="14" y="127" width="312" height="85" rx="6" stroke="#888" strokeDasharray="4 3" fill="#888" fillOpacity=".04"/>
    {#each ["Local-Z 子层模式","Purge 不足","塔超界","无 ooze prevention","高加速度"] as t,i}
      <rect x={24+(i%2)*147} y={137+Math.floor(i/2)*23} width="137" height="19" rx="4" fill="#64748b" fillOpacity=".13"/>
      <text x={92+(i%2)*147} y={150+Math.floor(i/2)*23} fontSize="9" textAnchor="middle" fill="currentColor">{t}</text>
    {/each}
    <text x="170" y="232" fontSize="10" textAnchor="middle" fill="currentColor">组合成员不自动获得独立因果资格</text>
  </svg>
  <caption>根据你提供的案例构造竞争假设，而不是预先认定五个因素均已被证实。</caption>
</box>

### 因果关系建议采用六级语义

| 关系 | 含义 |
|---|---|
| associated_with | 观察到共同出现 |
| suspected_contributor | 疑似贡献因素 |
| contributes_to | 有证据支持贡献作用 |
| interacts_with | 与另一因素存在交互作用 |
| necessary_for | 在限定条件下为必要条件 |
| sufficient_for | 在限定条件下为充分条件 |

组合假设额外记录逻辑关系：`AND / OR / INTERACTION / UNRESOLVED`。

其中 `UNRESOLVED` 非常重要。五个因素同时出现，不意味着五个因素必须同时存在，更不意味着已经证明存在五因素交互。

### 不要给 contributes_to 设置主观百分比权重

建议把以下维度分开：

| 维度 | 示例 |
|---|---|
| 证据来源 | DEVICE / SOURCE / DOCUMENT |
| 对照有效性 | CONTROLLED / PARTIAL / CONFOUNDED |
| 证据直接性 | DIRECT / INDIRECT |
| 证据立场 | SUPPORT / REFUTE / INCONCLUSIVE |
| 复现情况 | SINGLE / REPLICATED / INCONSISTENT |
| 效应量 | 脱附率、色差、质量差、失败次数等实测值 |

E0–E5 可以保留为内部证据等级，但它只是序数，不是概率。禁止将 E4 解释为 80% 可信，也禁止将多个 E2 自动加成 E4。

同一次打印产生的照片、日志、视频和 Markdown 报告，原则上属于同一个独立性组，不能算四份独立证据。

## 3. Scope 必须采用双层结构

答案不是差异键集或完整快照二选一，而是：

**完整快照负责复现，最小条件谓词负责知识适用性。**

<box border radius="lg" padding={3} gap={3}>
  <row align="start">
    <box flex={1} gap={1}>
      **运行快照**
      <caption>完整 200+ 配置键</caption>
      <box background="surface-tertiary" radius="md" padding={2}>
        <text size="sm">Preset hash</text>
        <text size="sm">Resolved config</text>
        <text size="sm">Slicer build</text>
        <text size="sm">Firmware / G-code</text>
      </box>
    </box>
    <box flex={1} gap={1}>
      **知识 Scope**
      <caption>与主张相关的最小条件</caption>
      <box background="surface-tertiary" radius="md" padding={2}>
        <text size="sm">Printer = U1</text>
        <text size="sm">Mixing mode = Local-Z</text>
        <text size="sm">Toolchange mode = X</text>
        <text size="sm">Slicer version = Y</text>
      </box>
    </box>
  </row>
  <divider/>
  <text textAlign="center" weight="medium" size="sm">Scope 匹配结果</text>
  <grid columns={3}>
    <grid-item><text textAlign="center" color="success" weight="medium">MATCH</text><caption textAlign="center">适用</caption></grid-item>
    <grid-item><text textAlign="center" color="danger" weight="medium">MISMATCH</text><caption textAlign="center">不适用</caption></grid-item>
    <grid-item><text textAlign="center" color="warning" weight="medium">UNKNOWN</text><caption textAlign="center">条件不足</caption></grid-item>
  </grid>
</box>

必须注意三个问题：

- 差异键集不是完整因果边界。A/B 两件只差三个键，不意味着其他 197 个键不会影响结论。
- Scope 未声明某个键，不代表该键任意变化都不影响结论。
- 相同配置快照不代表相同实机状态。耗材湿度、工具头污染、热床状态、喷嘴磨损仍然可能不同。

另建议在配置知识中强制建立四个阶段：

| 阶段 | 示例 |
|---|---|
| DECLARED | 配置声明速度 105 mm/s |
| RESOLVED | 继承解析后的速度 |
| COMMANDED | G-code 指令速度 30 mm/s |
| OBSERVED | 实机运动或遥测实测速度 |

这四个阶段禁止互相替代。即使 G-code 写了 30 mm/s，也不意味着实际运动全过程都是 30 mm/s。

### 版本失效不能只看预设哈希

Claim 依赖至少需要区分：

- 配置键及有效值依赖；
- 切片引擎和规则实现依赖；
- 固件与硬件能力依赖；
- 原始证据与上游 Claim 依赖。

预设哈希改变但有效值不变时，不应无差别废弃所有知识。无法判定影响范围时，才进入保守的待复核状态。

同时，失效的是知识的**现行适用资格**，不是历史事实。历史打印失败、历史裁决和原始照片不能被覆盖删除。

## 4. 通用 FDM 知识污染：Scope 隔离不够

Simplify3D 的缺陷诊断资料适合生成候选假设，但不能直接成为 U1 的诊断结论。

建议增加一条知识迁移门禁：

<box border radius="lg" padding={3} gap={1}>
  {#each [{n:"L0",t:"DOCUMENTARY",d:"外部资料声称某因素可能导致缺陷"},{n:"L1",t:"TRANSFER_CANDIDATE",d:"机制可能适用于 U1，尚未验证"},{n:"L2",t:"PIPELINE_VERIFIED",d:"在 U1 切片、源码或 G-code 层得到验证"},{n:"L3",t:"DEVICE_SUPPORTED",d:"得到 U1 实机证据支持"},{n:"L4",t:"CAUSALLY_SUPPORTED",d:"在有效对照及适用边界内支持因果结论"}] as item,i}
    <row align="center" gap={3}>
      <box background="surface-tertiary" radius="md" size="34px" align="center" justify="center"><text weight="medium">{item.n}</text></box>
      <box flex={1} gap=0><text weight="medium" size="sm">{item.t}</text><caption>{item.d}</caption></box>
    </row>
    {#if i<4}<box padding={{left:"9px"}}><icon name="arrow-down" color="secondary" size="sm"/></box>{/if}
  {/each}
</box>

这不是规定所有知识都必须经历五级线性晋升，而是规定**每种结论必须满足对应证据资格**。

尤其要调整你的来源枚举：OFFICIAL、PRESET、DEVICE、SOURCE、EXTERNAL 不在同一个分类维度上。官方源码既是 OFFICIAL，也是 SOURCE。

应拆为 `source_kind`、`publisher_authority`、`verification_stage` 三个独立字段。

## 5. 五条负向测试远远不够

你已有的五条都是历史事故回归测试，还缺少对系统本身的攻击测试。

建议扩充到 20 条，作为 V1.0 的冻结门禁。

| ID | 负向测试 | 必须阻断的错误 |
|---|---|---|
| N01 | CLI 全 PASS，实机失败 | 将局部门禁升级为打印成功 |
| N02 | 成败件存在 20+ 差异 | 单因素因果认定 |
| N03 | 塔宽缩小 | 推断 purge 质量同比下降 |
| N04 | 配置 105，指令 30 | 混淆声明与执行 |
| N05 | 全图 Vision 判色 | 将未经校准的感知当测量 |
| N06 | 多篇文章引用同一实验 | 重复累计证据 |
| N07 | 失败记录没有照片 | 将缺失证据当否定证据 |
| N08 | 单头 FDM 指南 | 自动晋升 U1 特有结论 |
| N09 | 旧固件验证通过 | 默认新固件仍适用 |
| N10 | Scope 缺少必要条件 | 默认 MATCH |
| N11 | 预设继承覆盖 | 使用父预设值代替有效值 |
| N12 | 哈希改变但有效值不变 | 无依据全面失效 |
| N13 | 上游 Claim 被反证 | 下游 Claim 仍有效 |
| N14 | 两项控制实验相互矛盾 | 只保留支持性结果 |
| N15 | 未受控条件下打印成功一次 | 宣称已彻底解决 |
| N16 | 切片测试通过，未实机 | 宣称实机通过 |
| N17 | 组合假设得到支持 | 每个成员自动获得因果资格 |
| N18 | 已推翻的旧 Markdown | FTS5 检索时复活旧结论 |
| N19 | 删除或损坏原始证据 | 无证据 Claim 继续有效 |
| N20 | 找不到候选根因 | 自动生成确定性答案 |

注意，N03 不应把「换头次数 × 单次 purge」冻结为所有切片器、所有配置下的普适定律。它需要限定换头序列、排料路径和 purge 策略，塔的支撑、底座及结构耗材也需要单独计量。

### 原验收 A/B/C 建议扩展为七项

| 实验 | 验收内容 |
|---|---|
| A | 历史错误回放 |
| B | 竞争根因与证据检索 |
| C | 版本变更与依赖失效 |
| D | 反证传播及历史保留 |
| E | 跨设备、跨版本知识污染攻击 |
| F | 从答案反查原始证据并独立复算 |
| G | 证据不足时正确拒绝确定性归因 |

B 实验的要求也要修正：系统只能保证列出**已登记且检索到的候选根因**，不能保证列出物理世界全部可能的根因。

## 6. MVP 建设顺序

建议用四个阶段完成首版，而不是先把 145 页 Wiki、27 篇缺陷指南和 377 色耗材全部录入。

<list connector="solid" marker="number" gap={2}>
  <list-item>**M0：认知契约与反向测试**

    冻结 10 表、枚举、20 条负向测试；实现 Scope 三态匹配、认知晋升门禁与证据独立性约束。
  </list-item>
  <list-item>**M1：只录五个历史错误**

    Tesla 炒面、塔料误判、105/30 速度差异、Vision 判色与门禁覆盖错误。保留最初错误判断、后续证据与修订过程。
  </list-item>
  <list-item>**M2：接入确定性证据**

    预设继承、G-code 解析、purge 统计、工具头状态和运行记录；加入实际设备与模拟设备隔离。
  </list-item>
  <list-item>**M3：扩展外部知识**

    Simplify3D、官方 Wiki、社区指南及 TD 数据库。所有自动抽取默认不具备实机因果资格。
  </list-item>
</list>

**U1 最终裁决：CONDITIONAL APPROVE。**

允许进入 M0/M1，不建议立即批量导入外部知识。首版成功标准不是图谱中有多少实体，而是你曾经犯过的五类归因错误能否被机器门禁拦截，以及旧结论被反证后是否还能污染新答案。

---

# 二、Pack10K 数据集设计评审 R1

## 1. 先纠正对标定位：不要做一个缩小版的 USDCraft-10K

我核查了 NVIDIA 的论文和 Hugging Face 数据集说明。USDCraft 的核心研究方向是几何证据驱动的程序化建模，以及面向机器人操作的可动资产重建。其公开数据集则由 DeepSeek-V4.1-Flash 根据文本提示生成。<Cite refs={["turn555271view0","turn555271view2"]}/>

<row align="start">
  <box flex={1}>
    <AsyncImage query="NVIDIA USDCraft-10K articulated 3D assets simulation dataset gallery microwave furniture" aspectRatio="5:3" fit="contain"/>
    **USDCraft-10K**
    <caption>通用刚体与可动资产</caption>
    <title size="2xl" tabularNums={true}>10,000</title>
    <caption>1,000 个类别</caption>
  </box>
  <box flex={1}>
    <AsyncImage query="untextured parametric retail packaging 3d CAD models cartons bottles pouches cans white background" aspectRatio="5:3" fit="contain"/>
    **Pack10K**
    <caption>零售包装专用参数化资产（方向示意，非项目实物）</caption>
    <title size="2xl" tabularNums={true}>10,000</title>
    <caption>100 个计划类别 / 16 个模板族</caption>
  </box>
</row>

NVIDIA 数据集中有 8,222 件带运动关节的资产和 1,778 件静态刚体资产。这说明其主要价值并不在包装几何，而在物体的结构与交互功能。<Cite ref="turn555271view2"/>

因此，我建议 Pack10K 的研究定位为：

> 面向零售包装领域的、具备工程契约、参数可追溯、物理属性可验证、非 CUDA 可生产的 OpenUSD 合成数字孪生数据集。

不要声称全面超过 USDCraft。你应该证明在**一个有真实产业需求的垂直领域**，领域知识与确定性工程过程能够产生更一致、更可复现、更经济的资产。

### 两者的差异化竞争维度

| 维度 | USDCraft-10K | Pack10K 设计方向 |
|---|---|---|
| 主要目标 | 通用物体与机器人交互 | 零售包装与零售仿真 |
| 生成方式 | LLM 编写资产程序 | 工程模板与参数采样 |
| 结构广度 | 强 | 领域限定 |
| 参数与尺寸可追溯 | 需实测对比 | 潜在优势 |
| 印刷与刀版拓扑 | 非主要研究目标 | 可形成独特优势 |
| 生产效率 | 包含模型生成过程 | 模板复用潜在优势 |
| 物理真实性 | 有公开仿真相关验证 | 尚待补证 |
| 非 CUDA 生产 | 未在本次评审中核验 | 用户报告已实现，待独立复现 |
| 下游零售价值 | 非主要研究目标 | 必须用实验建立 |

---

## 2. 发表前最大软肋排序

我不同意你将外观/纹理多样性为零列为唯一最大软肋。

**第一大软肋是缺乏独立的外部正确性基准。** 外观问题排在第二。

| 优先级 | 软肋 | 严重程度 |
|---|---|---|
| 1 | 内部一致性被误当作外部正确性 | P0 |
| 2 | 印刷、纹理、材质多样性为零 | P0 |
| 3 | 缺乏真实包装分布与结构覆盖证据 | P0 |
| 4 | SimReady 合规范围与实际仿真能力混淆 | P0 |
| 5 | 质量、重心、惯量与碰撞真实性不足 | P0 |
| 6 | 缺乏下游任务价值验证 | P0 |
| 7 | 10K 样本间有效多样性不足 | P1 |
| 8 | 生产耗时统计口径不完整 | P1 |
| 9 | 无活动部件、无软体包装行为 | P1，取决于声明范围 |
| 10 | 100 类少于 1000 类 | P2 |

### P0-01：三方尺寸对账 0.0 mm 不足以证明几何正确

如果三个测量对象均来自同一个参数源，即使全部对账为零，也可能是同源错误。

<box border radius="lg" padding={3} gap={2}>
  <svg viewBox="0 0 340 187" width="100%">
    <rect x="107" y="5" width="126" height="29" rx="5" fill="#64748b" fillOpacity=".12" stroke="#64748b"/>
    <text x="170" y="23" fontSize="11" textAnchor="middle" fill="currentColor">同一参数母本</text>
    <path d="M170 34 V48 H58 V61 M170 48 V61 M170 48 H282 V61" stroke="#888" fill="none"/>
    {#each ["声明尺寸","折叠尺寸","USD 尺寸"] as t,i}
      <rect x={5+i*112} y="61" width="106" height="32" rx="5" stroke="#888" fill="#888" fillOpacity=".06"/>
      <text x={58+i*112} y="81" textAnchor="middle" fill="currentColor" fontSize="10">{t}</text>
    {/each}
    <path d="M58 93 V109 H282 V93 M170 93 V109 V120" stroke="#888" fill="none"/>
    <text x="170" y="134" textAnchor="middle" fill="#16a34a" fontSize="12" fontWeight="600">内部一致性 Δ = 0 mm</text>
    <rect x="4" y="149" width="332" height="30" rx="5" fill="#dc2626" fillOpacity=".06" stroke="#dc2626" strokeDasharray="4 3"/>
    <text x="170" y="168" textAnchor="middle" fill="currentColor" fontSize="10">仍需要独立实物 / CAD / 制造规范作为外部真值</text>
  </svg>
</box>

建议建立 **Pack-Real100** 外部参考集：每个类别至少一个独立真实参照，有条件的重点类别增加重复样本。

证据包括实物卡尺测量、称重、实拍、公开且许可明确的刀版、制造规范或 CAD 数据。

没有外部真值的样本仍可以发布为合成资产，但不得宣称已完成真实数字孪生精度验证。

### P0-02：外观不是简单贴图问题

<grid columns={2} gap={3}>
  <grid-item>
    <AsyncImage query="retail product packaging untextured white clay 3d render carton bottles mockup" aspectRatio="4:3"/>
    **几何层**
    <caption>尺寸、结构、轮廓</caption>
  </grid-item>
  <grid-item>
    <AsyncImage query="professional colorful grocery product packaging printed carton bottle packaging designs" aspectRatio="4:3"/>
    **印刷层**
    <caption>版面、标签、颜色、文字</caption>
  </grid-item>
  <grid-item>
    <AsyncImage query="packaging material samples matte cardboard glossy plastic aluminum foil transparent PET close up" aspectRatio="4:3"/>
    **材质层**
    <caption>粗糙度、金属度、透光与反射</caption>
  </grid-item>
  <grid-item>
    <AsyncImage query="real supermarket grocery shelf densely packed products different brands colors packaging" aspectRatio="4:3"/>
    **场景层**
    <caption>遮挡、排列、光照及真实分布</caption>
  </grid-item>
</grid>

以上为四层能力的外部示意图，不是 Pack10K 当前产物。

建议你把已经完成的包装印刷程序化、刀版 UV 映射、酸奶杯 OpenUSD 资产和货架 SDG 研究复用进 Pack10K，而不是另建一套生成体系。

零售包装的细粒度差异往往来自印刷，而非形状。SKU-110K 相关研究也指出了这一特点；NVIDIA 的零售检测合成数据则专门考虑了仿真环境变化。<Cite refs={["turn555271search25","turn555271search3"]}/>

建议把数据集拆成三个可独立使用的子集：

| 子集 | 计划规模 | 用途 |
|---|---:|---|
| Pack10K-Geometry | 10,000 | 几何、尺寸、碰撞、堆叠 |
| Pack10K-Visual | 逐步覆盖 10,000 | 感知、检测、材质和印刷 |
| Pack-Real100 | 至少 100 个真实参照 | 外部精度与迁移验证 |

首版不必为了凑够 10K 高质量贴图而延迟所有研究，但正式发布时必须明确各子集的成熟度。

### P0-03：16 族 / 100 类的覆盖率不能自我证明

类别数量至少有四种含义：

- 包装结构类别；
- 制造工艺类别；
- 商品语义类别；
- 独立拓扑类别。

例如牛奶盒、果汁盒、茶饮盒可能属于三个商品类别，却共享同一种包装拓扑。

因此，100 个商品类别不能自动等于 100 个结构类别。

必须新增 Coverage Matrix，以真实包装需求作为分母，测量模板族覆盖了多少真实结构、工艺及业务场景。ESR 标签如果属于设计先验，也必须和实验得到的验证标签分开。

### P0-04：10/10 命名检查不等于 SimReady 完整合规

这是 Pack10K 中与 U1 事故完全同构的问题。

NVIDIA 官方资料明确区分 Package、目标 Profile、几何能力、物理能力及完整资产验证；公开 USDCraft 数据集记录了具体 Package Profile 的合规结果。<Cite refs={["turn280025search21","turn280025search13","turn555271view2"]}/>

建议拆成以下独立门禁：

| 门禁 | 验证对象 |
|---|---|
| P-GATE-01 | 文件与包命名 |
| P-GATE-02 | USD 结构及依赖完整 |
| P-GATE-03 | 指定 Package Profile |
| P-GATE-04 | 指定资产能力 Profile |
| P-GATE-05 | 碰撞、质量、重心、惯量 |
| P-GATE-06 | 实际运行时加载 |
| P-GATE-07 | 堆叠、跌落、接触与稳定性 |
| P-GATE-08 | 跨运行时行为一致性 |

只有哪一项实测通过，就报告哪一项通过。

禁止使用模糊的 `GREEN = SimReady verified` 作为所有门禁的统称。

### P0-05：面积 × 克重不等于完整商品质量

你的计算方法比 LLM 直接猜质量更可追溯，但它通常只能估算相应包装材料的质量。

\[
m_{\mathrm{gross}} =
m_{\mathrm{shell}} +
m_{\mathrm{closure}} +
m_{\mathrm{label}} +
m_{\mathrm{contents}}
\]

必须区分：

| 物理状态 | 质量模型 |
|---|---|
| 空包装 | 壳体、封口、标签 |
| 满载商品 | 包装质量 + 内容物 |
| 部分填充 | 另建填充状态 |
| 多层复合材料 | 分层密度或面积质量模型 |

如果没有内容物、真实重心和合理惯量，仿真中的倾倒、抓取和堆叠稳定性可能失真。

对于零售场景，这不是次要属性。

## 3. 过程模型实验：必须采用 2×2 因子设计

你的研究假设有价值，但「GLM+过程超过 OpenAI 裸模型」不是一个足够严谨的科学命题。

这里同时改变了两个变量：基础模型和工程过程。

更重要的是，我查看了 USDCraft 论文全文，其第 4.3 节已经研究了建模 harness 的有效性，第 4.6 节还进行了组件消融实验。因此，证明工程过程能够提升模型表现，并不是一个全新的研究方向。<Cite ref="turn500702view0"/>

你的创新点应当是**包装领域的工程契约、负向门禁与证据驱动的资产生成及修复机制**。

### EXP-01：基础模型 × 工程过程

<box border radius="lg" padding={3} gap={2}>
  <grid columns={2} gap={2}>
    <grid-item>
      <box border radius="md" padding={3}>
        <caption>A 组</caption>
        **GLM**
        基础工具 + 无结构化过程
      </box>
    </grid-item>
    <grid-item>
      <box border radius="md" padding={3}>
        <caption>B 组</caption>
        **GLM**
        基础工具 + 完整工程过程
      </box>
    </grid-item>
    <grid-item>
      <box border radius="md" padding={3}>
        <caption>C 组</caption>
        **OpenAI**
        基础工具 + 无结构化过程
      </box>
    </grid-item>
    <grid-item>
      <box border radius="md" padding={3}>
        <caption>D 组</caption>
        **OpenAI**
        基础工具 + 完整工程过程
      </box>
    </grid-item>
  </grid>
  <divider/>
  | 比较 | 能回答的问题 |
  |---|---|
  | B − A | 过程对 GLM 的增益 |
  | D − C | 过程对 OpenAI 的增益 |
  | A − C | 基础模型差异 |
  | B − C | 不同系统组合的实际竞争力 |
  | B − D | 相同过程下的模型差异 |
</box>

另加一个 **E 组：纯确定性模板引擎，无 LLM**。

E 组极其重要，因为在 16 个已经冻结的模板族内，很多任务可能根本不需要 LLM。如果 GLM+过程无法超过纯确定性方法，那么正确结论就是该类任务不需要语言模型。

这同样是有价值的研究结果。

### EXP-02：过程组件消融

完整过程拆成四部分：

| 组件 | 能力 |
|---|---|
| C1 | 领域知识与工程契约 |
| C2 | 正向几何及物理门禁 |
| C3 | 负向探针、异常挑战 |
| C4 | 证据台账与失败修复闭环 |

先验证完整过程是否有效，再分别移除 C1、C2、C3、C4，观察哪一项真正贡献了性能。

不能仅用完整系统与裸模型比较，就声称四个组件都有效。

## 4. 实验任务集设计

建议冻结 **PackBench-200**，作为独立于 Pack10K 生产集的研究基准。

| 任务 | 数量建议 | 验证目标 |
|---|---:|---|
| T1 已知模板参数生成 | 40 | 基本工程执行能力 |
| T2 未见参数组合 | 40 | 参数泛化 |
| T3 未见结构或新模板需求 | 40 | 结构泛化 |
| T4 缺陷资产修复 | 40 | 诊断与修复能力 |
| T5 约束矛盾、信息不足 | 40 | 拒绝错误生成及不确定性表达 |

这里最容易被操纵的是 T1。如果实验主要由已有模板能够直接覆盖的任务组成，过程组的高分可能仅来自模板复用，而不是更好的推理或工程能力。

所以必须分别公布五类结果，不能只公布平均分。

首轮建议 200 任务、5 组、每任务重复 3 次，即 3,000 次运行。这是建议规模，不是已通过统计功效分析得出的最终样本量。可以先用小规模预实验估计方差，再冻结正式规模。

### 公平对照条件

所有模型组必须共享相同的模板访问权限、基础 SDK、输入信息、任务定义和外部验收器。过程组与无过程组可以区别于是否强制执行结构化门禁、负向探针及证据闭环。

还应固定模型版本、推理设置、最大时间、工具调用和 token 预算，隔离会话，随机化任务顺序，并记录全部失败。

建议分别报告等预算实验与实际部署成本实验，因为两者回答的问题不同。

## 5. 禁止用 LLM-as-judge 作为主评分依据

评测必须由独立于生产管线的验收器执行。

| 指标 | 测量方法 |
|---|---|
| 任务完成率 | 独立契约验收 |
| 尺寸误差 | 独立几何解析及外部真值 |
| 拓扑正确性 | 连通性、闭合性、相交检查 |
| 物理正确性 | 独立仿真和实物参照 |
| 修复成功率 | 缺陷消除且未引入新缺陷 |
| 错误放行率 | 隐藏负向测试 |
| 正确拒绝率 | 不可行或不可辨识任务 |
| 可复现性 | 重复运行 |
| 成本 | API、计算、人工与失败重试 |
| 外观质量 | 匿名随机排序的人类盲评 |

LLM 可以辅助定位异常、解释失败，但不能成为最终正确性的唯一裁判。

建议定义主指标：

\[
\text{Verified Success Rate}
=\frac{\text{独立验收成功的可行任务数}}
{\text{全部可行任务数}}
\]

同时单独统计不可行任务的正确拒绝率，防止模型通过全部拒答来规避风险。

正式报告使用配对置信区间，并对不同任务族分层统计。超时、失败及异常退出不得从分母剔除。

**最大的实验门禁：生产验证器与论文评测验证器不能完全同源。**

如果过程模型使用 G03–G06 修复资产，最后仍只用 G03–G06 给它打分，那只能证明它学会满足自己的门禁，不能证明资产质量真正提高。

## 6. USDCraft 作者最可能提出的八项质疑

以下是我站在外部论文评审人的角度构造的质疑，不代表 NVIDIA 作者实际发表过这些意见。

| 潜在质疑 | 是否成立 | 应对策略 |
|---|---|---|
| 你们只是重复采样参数化模板 | 部分成立 | 公布独立拓扑数、形态覆盖率和有效多样性 |
| 你们没有证明对未知结构的泛化 | 成立 | 增加模板族留出实验 |
| 你们的几何真值和生成器同源 | 成立 | 建立 Pack-Real100 |
| 你们没有可动部件 | 取决于定位 | 明确静态包装边界，后续增加瓶盖、翻盖等 |
| 你们不具备真实商品外观 | 成立 | 增加印刷与 PBR 材质生成管线 |
| 你们的物理属性只是理论推导 | 部分成立 | 补充实物称重、重心和动力学验证 |
| 你们的速度对比不公平 | 成立 | 拆分模板开发与完整生产成本 |
| 你们没有证明数据集能解决任何真实任务 | 当前成立 | 增加零售检测与物理操作实验 |

其中最危险的质疑不是「你们不够 agentic」，而是：

> 你们是否只是将 16 个程序模板重复运行了一万次，却把它描述为拥有一万个独立资产的数据集？

这个问题必须用有效多样性实验回答，不能用更多样本数量回答。

### 有效多样性应当分五个维度度量

| 多样性维度 | 建议指标 |
|---|---|
| 几何拓扑 | 独立拓扑签名数量 |
| 几何形态 | 归一化形状距离及尺寸分布 |
| 结构工艺 | 刀版、封口、连接及装配方式 |
| 视觉外观 | 印刷版面、材质、颜色及视觉特征距离 |
| 物理行为 | 质量、重心、稳定性、抓取与接触行为分布 |

不建议现在为了对标 NVIDIA 强行把 100 类增加到 1000 类。先证明现有 100 类具有真实覆盖价值。

## 7. 非 CUDA 应该成为特色，但不能成为未经验证的性能结论

你报告的 500 件试点结果：

<grid columns={2} gap={3}>
  <grid-item>
    <caption>候选资产</caption>
    <title size="2xl" tabularNums={true}>500</title>
  </grid-item>
  <grid-item>
    <caption>生产门禁通过率</caption>
    <title size="2xl" color="success" tabularNums={true}>99.6%</title>
  </grid-item>
  <grid-item>
    <caption>本轮生产耗时</caption>
    <title size="2xl" tabularNums={true}>36.6 s</title>
  </grid-item>
  <grid-item>
    <caption>平均每候选资产</caption>
    <title size="2xl" tabularNums={true}>73 ms</title>
  </grid-item>
</grid>

<caption>以上均来自你的试点报告，尚未进行独立复现，不代表完整纹理与渲染生产耗时。</caption>

这个结果值得保留，但我反对直接拿 73ms 与 USDCraft 的 4.9min 计算加速倍数。

我核对了原论文：4.9 分钟是其 Table 5 中 USDCraft–Astra 生成实验的中位耗时，平均耗时为 5.6 分钟。它不是当前 Hugging Face 数据集每件资产的统一生产耗时。原论文与目前发布的数据集在生成模型及类别口径上也存在差异。你提供的 $0.851 单件成本，本次尚未独立确认。<Cite refs={["turn539348view1","turn555271view2"]}/>

建议采用如下计量合同。

| 成本阶段 | 单独计量 |
|---|---|
| 模板研发 | 人工、模型调用、开发及验证 |
| 参数生成 | CPU 时间 |
| 几何生成 | CPU 时间 |
| USD 导出 | CPU 时间 |
| 印刷版面 | CPU/GPU 时间 |
| 纹理烘焙 | CPU/GPU 时间 |
| 双缩略图 | Metal 渲染时间 |
| 验证与失败重试 | 完整耗时 |
| 打包发布 | I/O、存储与传输 |

同时公布冷启动、热启动、串行、并行、峰值内存、P50/P95 耗时和每个合格资产的实际成本。

基于你的 M1 Max 64GB 环境，我建议将 Apple Silicon 作为第一条完整可复现实验路线，再增加 Linux x86 CPU 路线。

非 CUDA 生产、非 CUDA 验证和非 CUDA 运行是三个不同的主张，必须分别证明。

## 8. 下游任务：这是 Pack10K 发表价值的决定因素

不必从头建设下游研究体系。你此前已经做过 OpenUSD → 货架 SDG → YOLO → SKU-110K 的闭环实验，可以直接复用。

<box border radius="lg" padding={3} gap={2}>
  <row align="center">
    <AsyncImage query="3d retail packaging models bottles boxes cartons cans assortment" aspectRatio="4:3" maxWidth="100px"/>
    <box flex={1}>
      **Pack10K 资产库**
      <caption>几何、印刷、材质、物理属性</caption>
    </box>
  </row>
  <icon name="arrow-down" color="secondary"/>
  <row align="center">
    <AsyncImage query="Blender synthetic supermarket shelves grocery product domain randomization rendered scene" aspectRatio="4:3" maxWidth="100px"/>
    <box flex={1}>
      **合成数据引擎**
      <caption>货架排列、遮挡、相机、光照</caption>
    </box>
  </row>
  <icon name="arrow-down" color="secondary"/>
  <grid columns={2}>
    <grid-item>
      **视觉实验**

      <AsyncImage query="SKU110K densely packed supermarket product detection bounding boxes benchmark" aspectRatio="4:3"/>
      <caption>真实货架检测、计数、识别</caption>
    </grid-item>
    <grid-item>
      **物理实验**

      <AsyncImage query="robot gripper grocery carton pick and place supermarket warehouse packaging manipulation" aspectRatio="4:3"/>
      <caption>堆叠、抓取、倾倒、碰撞</caption>
    </grid-item>
  </grid>
</box>

<caption>研究路线示意，图片为外部参考，不是本轮实验结果。</caption>

建议优先验证三个命题：

| 实验 | 研究命题 |
|---|---|
| D1 | 增加独立几何多样性是否提高真实货架检测效果 |
| D2 | 增加印刷与材质多样性是否缩小 Sim-to-Real 差距 |
| D3 | 引入真实质量与重心是否提高堆叠、抓取预测准确性 |

SKU-110K 适合通用商品检测与计数，但不能单独验证具体 SKU 身份识别能力。后者需要具备商品级身份标签的独立测试集。

---

# 三、Pack10K R1 整改任务书

建议按照你既有的单轮迭代不超过八周的纪律，划分为六个工作包。

| 工作包 | 主要任务 | 退出门禁 | 优先级 |
|---|---|---|---|
| WP0 | 冻结研究定位、术语和对外声明 | 明确合成资产与真实孪生边界 | P0 |
| WP1 | 外部真值与覆盖矩阵 | Pack-Real100 及独立测量报告 | P0 |
| WP2 | 印刷、UV、PBR 材质 | 视觉子集与多样性报告 | P0 |
| WP3 | SimReady 与物理验证 | Profile 合规及运行时证据 | P0 |
| WP4 | PackBench 与过程消融 | 2×2 对照及确定性基线 | P0 |
| WP5 | 下游任务、成本与发表 | 数据卡、复现脚本、实验结果 | P0 |

<box border radius="lg" padding={3} gap={2}>
  <title size="md">建议八周研究路线</title>
  <svg viewBox="0 0 340 217" width="100%">
    {#each Array.from({length:8},(_,i)=>i) as w}
      <text x={111+w*29} y="15" fontSize="9" textAnchor="middle" fill="currentColor">W{w+1}</text>
      <line x1={96+w*29} x2={96+w*29} y1="23" y2="197" stroke="currentColor" strokeOpacity=".1"/>
    {/each}
    {#each [{n:"WP0 定义冻结",s:0,d:1},{n:"WP1 外部真值",s:0,d:3},{n:"WP2 视觉资产",s:1,d:4},{n:"WP3 物理验证",s:1,d:4},{n:"WP4 对照实验",s:2,d:5},{n:"WP5 下游发表",s:4,d:4}] as p,i}
      <text x="3" y={42+i*27} fontSize="10" fill="currentColor">{p.n}</text>
      <rect x={98+p.s*29} y={29+i*27} width={p.d*29-4} height="18" rx="3" fill={i===0?"#64748b":i===4?"#2563eb":i===5?"#0d9488":"#64748b"} fillOpacity={i===4||i===5?".85":".55"}/>
    {/each}
    <line x1="96" x2="328" y1="198" y2="198" stroke="currentColor" strokeOpacity=".2"/>
  </svg>
  <caption>建议安排，允许并行；未通过门禁不得因时间到期而自动验收。</caption>
</box>

## 最终裁决

| 裁决项 | 状态 |
|---|---|
| 16 族参数化生产架构 | <text color="success" weight="medium">APPROVE</text> |
| 扩大到 10K 正式生产 | <text color="warning" weight="medium">HOLD</text> |
| 500 件几何预览集 | <text color="success" weight="medium">CONDITIONAL APPROVE</text> |
| 非 CUDA 研究主线 | <text color="success" weight="medium">APPROVE</text> |
| 全面超过 USDCraft 的主张 | <text color="danger" weight="medium">REJECT</text> |
| 工程过程增益实验 | <text color="success" weight="medium">APPROVE</text> |
| 正式数据集及论文发表 | <text color="warning" weight="medium">HOLD</text> |

本轮属于设计评审，不是独立代码审计。我尚未取得 500 件资产、G03–G06 实现、ESR 标签定义、原始性能日志和实际验证器输出，因此不签署工程实测 PASS。上述样本数量、八周排期及新增门禁是本轮提出的设计建议，并非已经冻结的合同。

---

# 四、两个项目值得共同沉淀的研究资产

我建议不要分别为 U1 和 Pack10K 重造认知治理基础设施。

你此前在个人知识智能、Snapmaker 数字孪生、PhotoDieline 和 OpenUSD 项目中，已经反复遇到相同的问题：

| 错误认知模式 | U1 | Pack10K |
|---|---|---|
| 局部通过冒充整体通过 | CLI CLEAR | 命名检查 GREEN |
| 同源证据冒充独立证据 | 同一次打印多份记录 | 三方尺寸同源 |
| 声明冒充实际 | 配置速度 | 声明物理质量 |
| 候选解释冒充因果 | Local-Z 炒面 | 过程提升模型能力 |
| 无边界泛化 | 通用 FDM 到 U1 | 16 族覆盖零售包装 |
| 不完整成本冒充完整成本 | 塔宽与 purge | 73ms 资产生产 |

这六类问题与具体业务领域无关。

建议将 U1 的十表认知核心进一步抽象成一个跨项目复用的 **Evidence & Adjudication Kernel（证据与裁决内核）**，但首轮不要单独立项做通用平台。先在两个真实项目中分别验证，再提取共同部分。

最终真正具有研究价值的，可能不只是一个打印知识图谱或者一个万件包装数据集，而是一套能够实证回答以下问题的工程方法：

**如何利用领域知识、确定性工具、独立证据和反向门禁，使 AI 工程系统不仅能够完成任务，而且能够识别自己何时没有完成任务、何时判断错误，以及何时必须撤回已有结论。**

<MemoryCite />

## 6. USDCraft 作者最可能提出的八项质疑

以下是我站在外部论文评审人的角度构造的质疑，不代表 NVIDIA 作者实际发表过这些意见。

| 潜在质疑 | 是否成立 | 应对策略 |
|---|---|---|
| 你们只是重复采样参数化模板 | 部分成立 | 公布独立拓扑数、形态覆盖率和有效多样性 |
| 你们没有证明对未知结构的泛化 | 成立 | 增加模板族留出实验 |
| 你们的几何真值和生成器同源 | 成立 | 建立 Pack-Real100 |
| 你们没有可动部件 | 取决于定位 | 明确静态包装边界，后续增加瓶盖、翻盖等 |
| 你们不具备真实商品外观 | 成立 | 增加印刷与 PBR 材质生成管线 |
| 你们的物理属性只是理论推导 | 部分成立 | 补充实物称重、重心和动力学验证 |
| 你们的速度对比不公平 | 成立 | 拆分模板开发与完整生产成本 |
| 你们没有证明数据集能解决任何真实任务 | 当前成立 | 增加零售检测与物理操作实验 |

其中最危险的质疑不是「你们不够 agentic」，而是：

> 你们是否只是将 16 个程序模板重复运行了一万次，却把它描述为拥有一万个独立资产的数据集？

这个问题必须用有效多样性实验回答，不能用更多样本数量回答。

### 有效多样性应当分五个维度度量

| 多样性维度 | 建议指标 |
|---|---|
| 几何拓扑 | 独立拓扑签名数量 |
| 几何形态 | 归一化形状距离及尺寸分布 |
| 结构工艺 | 刀版、封口、连接及装配方式 |
| 视觉外观 | 印刷版面、材质、颜色及视觉特征距离 |
| 物理行为 | 质量、重心、稳定性、抓取与接触行为分布 |

不建议现在为了对标 NVIDIA 强行把 100 类增加到 1000 类。先证明现有 100 类具有真实覆盖价值。

## 7. 非 CUDA 应该成为特色，但不能成为未经验证的性能结论

你报告的 500 件试点结果：

<grid columns={2} gap={3}>
  <grid-item>
    <caption>候选资产</caption>
    <title size="2xl" tabularNums={true}>500</title>
  </grid-item>
  <grid-item>
    <caption>生产门禁通过率</caption>
    <title size="2xl" color="success" tabularNums={true}>99.6%</title>
  </grid-item>
  <grid-item>
    <caption>本轮生产耗时</caption>
    <title size="2xl" tabularNums={true}>36.6 s</title>
  </grid-item>
  <grid-item>
    <caption>平均每候选资产</caption>
    <title size="2xl" tabularNums={true}>73 ms</title>
  </grid-item>
</grid>

<caption>以上均来自你的试点报告，尚未进行独立复现，不代表完整纹理与渲染生产耗时。</caption>

这个结果值得保留，但我反对直接拿 73ms 与 USDCraft 的 4.9min 计算加速倍数。

我核对了原论文：4.9 分钟是其 Table 5 中 USDCraft–Astra 生成实验的中位耗时，平均耗时为 5.6 分钟。它不是当前 Hugging Face 数据集每件资产的统一生产耗时。原论文与目前发布的数据集在生成模型及类别口径上也存在差异。你提供的 $0.851 单件成本，本次尚未独立确认。<Cite refs={["turn539348view1","turn555271view2"]}/>

建议采用如下计量合同。

| 成本阶段 | 单独计量 |
|---|---|
| 模板研发 | 人工、模型调用、开发及验证 |
| 参数生成 | CPU 时间 |
| 几何生成 | CPU 时间 |
| USD 导出 | CPU 时间 |
| 印刷版面 | CPU/GPU 时间 |
| 纹理烘焙 | CPU/GPU 时间 |
| 双缩略图 | Metal 渲染时间 |
| 验证与失败重试 | 完整耗时 |
| 打包发布 | I/O、存储与传输 |

同时公布冷启动、热启动、串行、并行、峰值内存、P50/P95 耗时和每个合格资产的实际成本。

基于你的 M1 Max 64GB 环境，我建议将 Apple Silicon 作为第一条完整可复现实验路线，再增加 Linux x86 CPU 路线。

非 CUDA 生产、非 CUDA 验证和非 CUDA 运行是三个不同的主张，必须分别证明。

## 8. 下游任务：这是 Pack10K 发表价值的决定因素

不必从头建设下游研究体系。你此前已经做过 OpenUSD → 货架 SDG → YOLO → SKU-110K 的闭环实验，可以直接复用。

<box border radius="lg" padding={3} gap={2}>
  <row align="center">
    <AsyncImage query="3d retail packaging models bottles boxes cartons cans assortment" aspectRatio="4:3" maxWidth="100px"/>
    <box flex={1}>
      **Pack10K 资产库**
      <caption>几何、印刷、材质、物理属性</caption>
    </box>
  </row>
  <icon name="arrow-down" color="secondary"/>
  <row align="center">
    <AsyncImage query="Blender synthetic supermarket shelves grocery product domain randomization rendered scene" aspectRatio="4:3" maxWidth="100px"/>
    <box flex={1}>
      **合成数据引擎**
      <caption>货架排列、遮挡、相机、光照</caption>
    </box>
  </row>
  <icon name="arrow-down" color="secondary"/>
  <grid columns={2}>
    <grid-item>
      **视觉实验**

      <AsyncImage query="SKU110K densely packed supermarket product detection bounding boxes benchmark" aspectRatio="4:3"/>
      <caption>真实货架检测、计数、识别</caption>
    </grid-item>
    <grid-item>
      **物理实验**

      <AsyncImage query="robot gripper grocery carton pick and place supermarket warehouse packaging manipulation" aspectRatio="4:3"/>
      <caption>堆叠、抓取、倾倒、碰撞</caption>
    </grid-item>
  </grid>
</box>

<caption>研究路线示意，图片为外部参考，不是本轮实验结果。</caption>

建议优先验证三个命题：

| 实验 | 研究命题 |
|---|---|
| D1 | 增加独立几何多样性是否提高真实货架检测效果 |
| D2 | 增加印刷与材质多样性是否缩小 Sim-to-Real 差距 |
| D3 | 引入真实质量与重心是否提高堆叠、抓取预测准确性 |

SKU-110K 适合通用商品检测与计数，但不能单独验证具体 SKU 身份识别能力。后者需要具备商品级身份标签的独立测试集。

---

# 三、Pack10K R1 整改任务书

建议按照你既有的单轮迭代不超过八周的纪律，划分为六个工作包。

| 工作包 | 主要任务 | 退出门禁 | 优先级 |
|---|---|---|---|
| WP0 | 冻结研究定位、术语和对外声明 | 明确合成资产与真实孪生边界 | P0 |
| WP1 | 外部真值与覆盖矩阵 | Pack-Real100 及独立测量报告 | P0 |
| WP2 | 印刷、UV、PBR 材质 | 视觉子集与多样性报告 | P0 |
| WP3 | SimReady 与物理验证 | Profile 合规及运行时证据 | P0 |
| WP4 | PackBench 与过程消融 | 2×2 对照及确定性基线 | P0 |
| WP5 | 下游任务、成本与发表 | 数据卡、复现脚本、实验结果 | P0 |

<box border radius="lg" padding={3} gap={2}>
  <title size="md">建议八周研究路线</title>
  <svg viewBox="0 0 340 217" width="100%">
    {#each Array.from({length:8},(_,i)=>i) as w}
      <text x={111+w*29} y="15" fontSize="9" textAnchor="middle" fill="currentColor">W{w+1}</text>
      <line x1={96+w*29} x2={96+w*29} y1="23" y2="197" stroke="currentColor" strokeOpacity=".1"/>
    {/each}
    {#each [{n:"WP0 定义冻结",s:0,d:1},{n:"WP1 外部真值",s:0,d:3},{n:"WP2 视觉资产",s:1,d:4},{n:"WP3 物理验证",s:1,d:4},{n:"WP4 对照实验",s:2,d:5},{n:"WP5 下游发表",s:4,d:4}] as p,i}
      <text x="3" y={42+i*27} fontSize="10" fill="currentColor">{p.n}</text>
      <rect x={98+p.s*29} y={29+i*27} width={p.d*29-4} height="18" rx="3" fill={i===0?"#64748b":i===4?"#2563eb":i===5?"#0d9488":"#64748b"} fillOpacity={i===4||i===5?".85":".55"}/>
    {/each}
    <line x1="96" x2="328" y1="198" y2="198" stroke="currentColor" strokeOpacity=".2"/>
  </svg>
  <caption>建议安排，允许并行；未通过门禁不得因时间到期而自动验收。</caption>
</box>

## 最终裁决

| 裁决项 | 状态 |
|---|---|
| 16 族参数化生产架构 | <text color="success" weight="medium">APPROVE</text> |
| 扩大到 10K 正式生产 | <text color="warning" weight="medium">HOLD</text> |
| 500 件几何预览集 | <text color="success" weight="medium">CONDITIONAL APPROVE</text> |
| 非 CUDA 研究主线 | <text color="success" weight="medium">APPROVE</text> |
| 全面超过 USDCraft 的主张 | <text color="danger" weight="medium">REJECT</text> |
| 工程过程增益实验 | <text color="success" weight="medium">APPROVE</text> |
| 正式数据集及论文发表 | <text color="warning" weight="medium">HOLD</text> |

本轮属于设计评审，不是独立代码审计。我尚未取得 500 件资产、G03–G06 实现、ESR 标签定义、原始性能日志和实际验证器输出，因此不签署工程实测 PASS。上述样本数量、八周排期及新增门禁是本轮提出的设计建议，并非已经冻结的合同。

---

# 四、两个项目值得共同沉淀的研究资产

我建议不要分别为 U1 和 Pack10K 重造认知治理基础设施。

你此前在个人知识智能、Snapmaker 数字孪生、PhotoDieline 和 OpenUSD 项目中，已经反复遇到相同的问题：

| 错误认知模式 | U1 | Pack10K |
|---|---|---|
| 局部通过冒充整体通过 | CLI CLEAR | 命名检查 GREEN |
| 同源证据冒充独立证据 | 同一次打印多份记录 | 三方尺寸同源 |
| 声明冒充实际 | 配置速度 | 声明物理质量 |
| 候选解释冒充因果 | Local-Z 炒面 | 过程提升模型能力 |
| 无边界泛化 | 通用 FDM 到 U1 | 16 族覆盖零售包装 |
| 不完整成本冒充完整成本 | 塔宽与 purge | 73ms 资产生产 |

这六类问题与具体业务领域无关。

建议将 U1 的十表认知核心进一步抽象成一个跨项目复用的 **Evidence & Adjudication Kernel（证据与裁决内核）**，但首轮不要单独立项做通用平台。先在两个真实项目中分别验证，再提取共同部分。

最终真正具有研究价值的，可能不只是一个打印知识图谱或者一个万件包装数据集，而是一套能够实证回答以下问题的工程方法：

**如何利用领域知识、确定性工具、独立证据和反向门禁，使 AI 工程系统不仅能够完成任务，而且能够识别自己何时没有完成任务、何时判断错误，以及何时必须撤回已有结论。**

<MemoryCite />