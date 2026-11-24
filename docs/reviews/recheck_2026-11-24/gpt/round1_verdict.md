# GPT 从头复查评审 · 第 1 轮判决 (2026-11-24)

- 会话: chatgpt.com/c/6b04e20e-6b54-83ea-9404-cce4e946424f ("优化审计裁决", 新建会话, 无历史锚定)
- 注入: browser relay 新聊天 + insertText 分块; 投递以后端消息表为准 (用户消息 3578 字在册)
- 抓取: backend-api Bearer + 消息表时间序; 助手消息 11 条, 其中 3 条完成 (60 + 32126 + 9303 字)
- 证据边界 (GPT 自述): 远端仓与指定提交 54b81ca 已核对; 本地未推送修复与全部探针/实验**未独立复现** (其运行环境无法克隆仓库)
- 被审输入: `gpt_r1_prompt.txt` (本目录上一级); 证据账 `findings.md`; 清单草案 `OPTIMIZATION_PLAN.md`

## 裁决汇总 (GPT 原文第 9 节)

| 裁决项 | 最终决定 |
|---|---|
| 参数化制造几何主干 | 保留，继续加强 |
| 现有 100/100 制造验收声明 | 撤回，重新分级验证 |
| 几何覆盖稀疏是误差主因 | **不予确认** (接受现象, 拒绝归因) |
| CNN 直接回归 | 暂停资源扩张，保留对照 |
| 零训练解析几何 | 提升为 P0 (升级为参数化逆向拟合) |
| 参数化逆向拟合 | 新增主研究路线 |
| 多视角前馈基础模型 | 降级为研究候选 |
| 合成数据引擎全面升级 | 暂缓，先确定有效变量 |
| 真实物理数据集 | P0，不可再延后 |
| 模板数量扩张 | 暂停 |
| 货架孪生 / ESR | 迁出主仓 |
| PRINT-READY 人工签核原则 | 保留，禁止自动升级 |

---

# GPT 答复主文 (第 0–5 节, 原文)

# PD-RECHECK-R1｜PhotoDieline 优化空间独立评审

**评审裁决：现有技术主干保留，制造交付能力重新验收，学习路线重新排序，货架孪生线拆分。**

我认为这次复查最有价值的发现，不是找出了多少代码缺陷，而是暴露了三个不同层次的问题：

- **制造几何问题**：系统生成的结果不一定是物理上成立的包装结构。
- **验证体系问题**：系统无法有效区分正确结果和错误结果，导致大量绿色门禁失去证明力。
- **研究方法问题**：学习实验虽然取得了数值进展，但尚未证明模型真正获得了几何测量能力。

这三个问题的修复顺序不能颠倒。否则，越强的合成数据引擎、越大的模板动物园、越复杂的视觉模型，都有可能进一步放大错误。

## 0. 评审证据边界

<box border radius="lg" padding={3} gap={2}>
  <row align="center">
    <text color="secondary" size="sm">被审版本</text>
    <spacer/>
    **54b81ca**
  </row>
  <divider/>
  <row align="center">
    <text size="sm">远端仓库及指定提交</text>
    <spacer/>
    <badge color="success">已核对</badge>
  </row>
  <row align="center">
    <text size="sm">README 对外交付声明</text>
    <spacer/>
    <badge color="success">已核对</badge>
  </row>
  <row align="center">
    <text size="sm">本地未推送修复</text>
    <spacer/>
    <badge color="warning">未独立验收</badge>
  </row>
  <row align="center">
    <text size="sm">全部代码探针及四组实验</text>
    <spacer/>
    <badge color="warning">未独立复现</badge>
  </row>
</box>

已经核实，公开仓库 README 确实宣称 100 类模板、十门全绿、折叠闭合残差达标，并将手机照片到印刷级刀版作为项目定位。指定提交 `54b81ca` 的实际变更则集中在货架构建脚本和货架收敛日志。<Cite refs={["turn920635view0","turn282524view0"]}/>

本次尝试直接克隆仓库时遇到运行环境网络限制。因此，下文对具体缺陷数量的裁决属于**证据充分性和设计层审查**，不冒充已经执行过全部代码的独立复现结论。

## 1. 逐条裁决：攻击现有证据

以下「同意」指我认可发现所支持的技术判断及处置方向，不代表相关数量已经由我独立复跑确认。

### A. 核心交付物

| 编号 | 裁决 | 理由与补充要求 |
|---|---|---|
| A1 导出越界 | 同意 | P0。制造几何正确不代表导出几何正确。必须对全部导出元素做物理坐标对账，而非仅检查画布范围。 |
| A2 PDF 错误 | 同意 | P0。严格解析通过仍不代表可渲染，更不代表符合印前标准。至少增加两个独立渲染后端及 PDF/X-4 专用预检。 |
| A3 门禁失效 | 同意 | P0。15/27 个破坏逃逸，说明原 VALIDATED 不具备充分证据。新增门禁后必须用原来的破坏样本重新攻击，而不仅仅是重跑正例。 |
| A4 照片无效、实测冲突 | 修改 | 照片不影响输出只能证明被测入口没有消费照片信息，不能据此证明整个仓库没有视觉能力。实测覆盖参数后还必须重新求解派生约束，不能简单覆盖字典。 |
| A1–4 修复结果 | 暂不签署 | 35 个测试和 100/100 全绿不是充分证据。尤其 B 类缺陷尚未修复，说明当前新门禁仍存在明显覆盖缺口。 |

这里我特别挑战你的一项修复：**新增导出几何单源模块有可能制造新的共因失效。**

如果 SVG、PDF 和验证器都使用同一个错误的坐标变换函数，三者可以完全一致，同时全部错误。

因此需要三个独立层次：

<box border radius="lg" padding={3} gap={2}>
  <svg viewBox="0 0 340 226" width="100%">
    <rect x="95" y="5" width="150" height="35" rx="6" fill="#64748b" fillOpacity=".13" stroke="#64748b"/>
    <text x="170" y="27" fontSize="12" textAnchor="middle" fill="currentColor">Geometry IR</text>
    <path d="M170 40 V54 H80 V66 M170 54 H260 V66" fill="none" stroke="currentColor" strokeOpacity=".5"/>
    <rect x="10" y="66" width="140" height="40" rx="5" fill="#64748b" fillOpacity=".1" stroke="#64748b"/>
    <text x="80" y="82" textAnchor="middle" fill="currentColor" fontSize="11">导出器</text>
    <text x="80" y="96" textAnchor="middle" fill="currentColor" fontSize="10">SVG / PDF</text>
    <rect x="190" y="66" width="140" height="40" rx="5" fill="#16a34a" fillOpacity=".09" stroke="#16a34a"/>
    <text x="260" y="82" textAnchor="middle" fill="currentColor" fontSize="11">独立期望值计算</text>
    <text x="260" y="96" textAnchor="middle" fill="currentColor" fontSize="10">Oracle</text>
    <path d="M80 106 V128 M260 106 V157 H170" fill="none" stroke="currentColor" strokeOpacity=".5"/>
    <rect x="10" y="128" width="140" height="35" rx="5" fill="#64748b" fillOpacity=".1" stroke="#64748b"/>
    <text x="80" y="149" textAnchor="middle" fill="currentColor" fontSize="11">独立解析实际文件</text>
    <path d="M80 163 V174 H170 V183 M260 157 V174 H170" fill="none" stroke="currentColor" strokeOpacity=".5"/>
    <rect x="75" y="183" width="190" height="35" rx="5" stroke="#16a34a" fill="#16a34a" fillOpacity=".09"/>
    <text x="170" y="204" textAnchor="middle" fill="currentColor" fontSize="11">物理坐标、尺寸、拓扑、图层对账</text>
  </svg>
  <caption>导出实现可以共享代码，但验证期望值不得直接复用被验证的变换实现。</caption>
</box>

另外，新增一份手工计算的非零原点金标：包含负坐标、不对称几何、已知长度和不同线型。它比 100 个同源生成的正例更能发现系统性错误。

### B. 模板动物园

| 编号 | 裁决 | 理由与补充要求 |
|---|---|---|
| B5 15 类切穿结构 | 修改 | 必须区分正面积重叠、合法共边和数值容差内接触。折线两侧顶点细分不同，本身不一定构成几何错误；应先做共线分段归一化。 |
| B6 37 类粘口反折 | 同意 | 高优先级。但需要基于有向折线、目标面及允许接触区域裁决，不能只检查法向或角度符号。 |
| B6 145 条翻折逃逸 | 修改 | 这是门禁灵敏度问题，但不是 145 条真实折线错误。部分折线可能存在角度等价性或合法替代折叠路径。应逐类定义有效破坏。 |
| B6 两类无底板 | 修改 | 必须依据结构用途判断。例如套筒、展示架、开口容器可能合法无底。不能全局强制有底板。 |
| B7 39 类参数变体 | 同意 | 应把参数实例、结构族、行业标准编码三者分开统计。但棱数改变也可能导致拓扑改变，不应简单认定全部重复。 |
| B7 ECMA 缺失 | 修改 | 对齐行业标准有价值，但源码中关键词出现次数不是标准符合性的检测方法，也不意味着必须覆盖全部 206 个编码。 |

**你低估了折叠过程本身的难度。**

当前关注的是折叠终态闭合，我要求补一个独立层次：**折叠可达性**。

<grid columns={3} gap={2}>
  <grid-item>
    <box gap={1}>
      <svg viewBox="0 0 110 100" width="100%">
        <g stroke="#64748b" fill="#94a3b8" fillOpacity=".17" strokeWidth="1.4">
          <rect x="35" y="28" width="35" height="38"/>
          <rect x="0" y="28" width="35" height="38"/>
          <rect x="70" y="28" width="35" height="38"/>
          <rect x="35" y="3" width="35" height="25"/>
          <rect x="35" y="66" width="35" height="25"/>
        </g>
        <g stroke="#2563eb" strokeDasharray="3 2">
          <path d="M35 28V66 M70 28V66 M35 28H70 M35 66H70"/>
        </g>
      </svg>
      **展开合法**
      <caption>无重叠、无非法裁切</caption>
    </box>
  </grid-item>
  <grid-item>
    <box gap={1}>
      <svg viewBox="0 0 110 100" width="100%">
        <path d="M12 65L50 84L98 62L60 43Z" fill="#94a3b8" fillOpacity=".3" stroke="#64748b"/>
        <path d="M12 65L12 23L50 42L50 84Z M50 84L98 62L98 20L50 42Z" fill="#94a3b8" fillOpacity=".22" stroke="#64748b"/>
        <path d="M12 23L72 48L72 78L12 53Z" fill="#dc2626" fillOpacity=".3" stroke="#dc2626"/>
        <path d="M98 20L38 47L38 76L98 49Z" fill="#dc2626" fillOpacity=".25" stroke="#dc2626"/>
        <circle cx="55" cy="51" r="8" fill="#dc2626"/>
        <path d="M51 47L59 55M59 47L51 55" stroke="white" strokeWidth="1.8"/>
      </svg>
      **过程可达**
      <caption>检查折叠过程中的干涉</caption>
    </box>
  </grid-item>
  <grid-item>
    <box gap={1}>
      <svg viewBox="0 0 110 100" width="100%">
        <path d="M15 29L55 9L95 29L55 49Z" fill="#94a3b8" fillOpacity=".13" stroke="#64748b"/>
        <path d="M15 29L55 49L55 92L15 72Z" fill="#94a3b8" fillOpacity=".3" stroke="#64748b"/>
        <path d="M55 49L95 29L95 72L55 92Z" fill="#94a3b8" fillOpacity=".48" stroke="#64748b"/>
        <path d="M55 49V92" stroke="#16a34a" strokeWidth="2.5"/>
      </svg>
      **终态成立**
      <caption>接缝、尺寸、粘合关系正确</caption>
    </box>
  </grid-item>
</grid>

即使最终面板位置完全正确，也可能没有一条无干涉的折叠路径能够到达该位置。

因此，我反对仅凭 G04/G06 的终态残差宣布「可制造」。

---

### C. 学习线

| 编号 | 裁决 | 理由与补充要求 |
|---|---|---|
| C8 比例误差修正 | 同意 | 比例绝对误差乘 100 不是相对百分比误差。必须区分 ratio MAE、relative MAE 和 mm MAE。 |
| C8 超常数基线 | 同意 | 误差下降约 68%，有真实研究价值。但常数基线过弱，不足以证明路线具有竞争力。 |
| C9 几何覆盖主因 | **反对** | 当前只证明了几何留出泛化存在缺口，不能确认其主因。 |
| C10 合成引擎偏离规范 | 同意 | 但规范偏离不等于已证明每个偏离都导致性能下降。不能未经消融就全面重建引擎。 |
| C11 分类真实集失败 | 同意 | 尤其 11/12 高置信错误，说明置信度拒识机制失效。 |
| C11 DINOv2 路线 | 修改 | 真实集 35.1% 优于 CNN 21.6%，值得保留为候选基线，但尚不能裁定检索路线胜出。 |
| C12 VGGT PoC | 同意 | 状态应为 NOT_ESTABLISHED（未证实），不是技术不可行。脏基准不能用于淘汰模型家族。 |

### D. 货架孪生 / ESR

| 编号 | 裁决 | 理由与补充要求 |
|---|---|---|
| D13 旧合规报告 | 同意 | 历史通过不代表 HEAD 通过。报告必须绑定资产哈希、校验规则版本及代码提交。 |
| D13 三门无否决力 | 同意 | 必须撤销当前有效的合规声明。SimReady 官方校验器是补充，不是项目自身几何真实性的替代品。 |
| D14 商业摄影素材 | 同意 | P0 治理风险。删除当前工作树不等于删除 Git 历史，需要核查历史、许可证范围和再分发权限。 |
| D15 工程范围膨胀 | 同意 | 不只是代码质量问题，而是两个不同北极星的项目共享了一个发布边界。 |

货架视觉真实感研究可以有自己的独立价值。指定提交也确实记录了单变量改动与全帧差分控制。但这种证据只能支持特定渲染改动的局部效果，不能替代制造几何或 ESR 合规证据。<Cite refs={["turn282524view0"]}/>

## 2. Q1 裁决：几何覆盖稀疏是不是误差主因？

**不成立。接受现象，拒绝因果归因。**

你发现的反例解释是成立的，而且我认为它应该成为下一阶段学习研究的核心竞争假设。

### 2.1 现有实验究竟证明了什么？

<card gap={3}>
  <title size="md">已见几何与留出几何的误差差异</title>
  <row align="center">
    <caption>已见几何</caption>
    <spacer/>
    **0.0032**
  </row>
  <box height={18} background="surface-tertiary" radius="sm">
    <box width="20.4%" height="100%" background="#16a34a" radius="sm"/>
  </box>
  <row align="center">
    <caption>留出几何</caption>
    <spacer/>
    **0.0157**
  </row>
  <box height={18} background="surface-tertiary" radius="sm">
    <box width="100%" height="100%" background="#dc2626" radius="sm"/>
  </box>
  <divider/>
  <grid columns={2}>
    <grid-item>
      <caption>泛化误差倍数</caption>
      <title size="2xl" color="danger" tabularNums={true}>4.91×</title>
    </grid-item>
    <grid-item>
      <caption>绝对 MAE 差值</caption>
      <title size="2xl" tabularNums={true}>0.0125</title>
    </grid-item>
  </grid>
  <caption>数据来自本轮提交的实验结果，未独立复跑。</caption>
</card>

<card gap={2}>
  <title size="md">几何数量学习曲线</title>
  <Chart content={{"chartType":"line","xKey":"k","xAxisLabel":"训练几何数量","xAxisScale":"linear","series":[{"dataKey":"error","label":"比例 MAE"}],"data":[{"k":6,"error":0.0334},{"k":12,"error":0.024},{"k":24,"error":0.0157}]}}/>
  <caption>现有三个观测点呈下降趋势，但种子与对照不足，不能用于可靠的规模外推。</caption>
</card>

我还发现一个数值表述问题：

- 6→12 的局部幂律指数约为 0.48。
- 12→24 的局部幂律指数约为 0.61。
- 6→24 的整体端点指数约为 0.54。

因此，`err ∝ k^-0.6` 可以作为粗略描述，但不能作为已经确定的缩放规律，更不能据此承诺增加十倍几何数量就能达到毫米级要求。

### 2.2 至少存在五种竞争解释

| 假设 | 模型实际学到了什么 | 现有证据能否排除 |
|---|---|---|
| H1 几何覆盖不足 | 连续几何映射，但训练采样太稀疏 | 不能 |
| H2 变体记忆 | 识别已见模板变体，查找隐含尺寸 | 不能 |
| H3 渲染捷径 | 固定角色颜色、面板纹理、取景尺度等代理变量 | 不能 |
| H4 像素分辨率瓶颈 | 图像中缺少足够的可测量边缘信息 | 不能 |
| H5 数据划分混杂 | 已见组和留出组的参数范围、位姿或可见性难度不同 | 不能 |

Geirhos 等人在 2020 年的 *Shortcut Learning in Deep Neural Networks* 中系统讨论了这种现象：模型可以通过训练分布内有效、但分布外失效的捷径获得良好结果。你的实验恰好需要排查此类机制。<Cite refs={["turn282524search0","turn282524search3"]}/>

### 2.3 我要求新增四组对照实验

这四组的价值远高于直接扩大十倍训练集。

<box border radius="lg" padding={3} gap={3}>
  <title size="md">E4｜模型是否真正学会几何测量</title>
  <row align="start" gap={3}>
    <svg viewBox="0 0 100 75" width="100px">
      {#each [0,1,2] as n}
      <g transform={`translate(${n*33},10)`}>
        <rect x="3" y="16" width="23" height="40" fill={["#3b82f6","#dc2626","#16a34a"][n]} fillOpacity=".55" stroke="currentColor" strokeOpacity=".5"/>
        <path d="M3 16L10 9H33L26 16M26 16L33 9V49L26 56" fill="none" stroke="currentColor" strokeOpacity=".5"/>
      </g>
      {/each}
    </svg>
    <box flex={1} gap={1}>
      **E4-A：同几何，异外观**

      固定尺寸和相机，只替换纹理、颜色、印刷与背景。预测应基本不变。
    </box>
  </row>
  <divider/>
  <row align="start" gap={3}>
    <svg viewBox="0 0 100 75" width="100px">
      {#each [0,1,2] as n}
      <g transform={`translate(${n*33},0)`}>
        <rect x="3" y={31-n*10} width="22" height={30+n*10} fill="#64748b" fillOpacity=".35" stroke="#64748b"/>
        <path d={`M3 ${31-n*10} l7 -6 h22 l-7 6 M25 ${31-n*10} l7 -6 V55 l-7 6`} fill="none" stroke="#64748b"/>
      </g>
      {/each}
    </svg>
    <box flex={1} gap={1}>
      **E4-B：同外观，异几何**

      固定纹理生成规则和相机，连续改变 W、D、H。预测应连续响应，而非跳向已知变体。
    </box>
  </row>
  <divider/>
  <row align="start" gap={3}>
    <svg viewBox="0 0 100 75" width="100px">
      {#each [0,1,2,3,4] as n}
        {#each [0,1,2,3] as m}
          <circle cx={13+n*18} cy={12+m*17} r="4" fill={(n+m)%3===0?"#dc2626":"#2563eb"}/>
        {/each}
      {/each}
    </svg>
    <box flex={1} gap={1}>
      **E4-C：参数插值与外推**

      区分训练网格内未见组合、网格外参数、独立留出结构族。观察是哪种泛化首先失败。
    </box>
  </row>
  <divider/>
  <row align="start" gap={3}>
    <svg viewBox="0 0 100 75" width="100px">
      <rect x="6" y="14" width="35" height="48" fill="#94a3b8" fillOpacity=".35" stroke="#64748b"/>
      {#each [0,1,2,3,4,5] as n}
      <path d={`M9 ${20+n*6} H38`} stroke="#64748b" strokeOpacity=".7"/>
      {/each}
      <path d="M44 38 H56 M52 34L56 38L52 42" stroke="currentColor" fill="none"/>
      <rect x="61" y="14" width="32" height="48" fill="none" stroke="#16a34a" strokeWidth="2"/>
      <circle cx="61" cy="14" r="3" fill="#16a34a"/><circle cx="93" cy="14" r="3" fill="#16a34a"/><circle cx="61" cy="62" r="3" fill="#16a34a"/><circle cx="93" cy="62" r="3" fill="#16a34a"/>
    </svg>
    <box flex={1} gap={1}>
      **E4-D：信息通道消融**

      原始 RGB、去纹理白模、轮廓图、精确关键点分别作为输入，对比几何信息贡献。
    </box>
  </row>
</box>

所有实验保持独立测试集不变、至少三个种子，并区分固定总图像数与固定每几何图像数两种预算口径。否则，增加几何数量同时增加训练样本量，就无法确定是哪一个变量带来的改善。

### 2.4 还要加入一个你遗漏的基线

不是另一个 CNN，而是：

**已见几何最近邻检索 + 尺寸查表。**

假如简单查表可以接近现有 CNN 的表现，那么「模型正在测量」这个解释将受到实质挑战。

Q1 最终裁决建议写入研究档案：

> 已证实训练几何数量与留出几何误差之间存在初步关联；几何覆盖稀疏是候选原因之一，尚未排除变体记忆、视觉捷径及成像信息不足，不得登记为已确认主因。

---

## 3. Q2 裁决：暂停 CNN，转向实测和解析几何

**同意暂停 CNN 直接回归；反对现在淘汰 CNN；同意降级多视角前馈几何。**

但我认为你的新路线还差一个关键步骤。

你提出关键点 + 消点闭式解，我建议进一步升级为：

**基于参数化 CAD 的逆向几何拟合（Inverse Parametric Geometry Fitting）。**

消点法仅仅是其中一个初始化或求解手段。

<box border radius="lg" padding={3} gap={2}>
  <title size="md">建议的新主干架构</title>
  <svg viewBox="0 0 340 405" width="100%">
    <rect x="20" y="5" width="142" height="45" rx="6" fill="#64748b" fillOpacity=".12" stroke="#64748b"/>
    <text x="91" y="23" textAnchor="middle" fontSize="12" fill="currentColor">手机照片</text>
    <text x="91" y="39" textAnchor="middle" fontSize="10" fill="currentColor">轮廓 / 边线 / 关键点</text>
    <rect x="178" y="5" width="142" height="45" rx="6" fill="#16a34a" fillOpacity=".1" stroke="#16a34a"/>
    <text x="249" y="23" textAnchor="middle" fontSize="12" fill="currentColor">少量实测尺寸</text>
    <text x="249" y="39" textAnchor="middle" fontSize="10" fill="currentColor">尺度锚定 / 硬约束</text>
    <path d="M91 50V66 M249 50V147H222" fill="none" stroke="currentColor" strokeOpacity=".5"/>
    <rect x="20" y="66" width="142" height="45" rx="6" fill="#64748b" fillOpacity=".1" stroke="#64748b"/>
    <text x="91" y="84" textAnchor="middle" fontSize="12" fill="currentColor">候选结构识别</text>
    <text x="91" y="100" textAnchor="middle" fontSize="10" fill="currentColor">人工 / 检索 / 分类</text>
    <path d="M91 111V130" stroke="currentColor" strokeOpacity=".5"/>
    <rect x="20" y="130" width="202" height="60" rx="6" fill="#2563eb" fillOpacity=".1" stroke="#2563eb"/>
    <text x="121" y="150" textAnchor="middle" fontSize="13" fill="currentColor">参数化几何拟合</text>
    <text x="121" y="165" textAnchor="middle" fontSize="10" fill="currentColor">消点初始化 + 投影优化</text>
    <text x="121" y="180" textAnchor="middle" fontSize="10" fill="currentColor">单视角 / 多视角联合约束</text>
    <path d="M121 190V208" stroke="currentColor" strokeOpacity=".5"/>
    <rect x="20" y="208" width="202" height="40" rx="6" fill="#64748b" fillOpacity=".1" stroke="#64748b"/>
    <text x="121" y="225" textAnchor="middle" fontSize="12" fill="currentColor">参数证据与不确定性</text>
    <text x="121" y="239" textAnchor="middle" fontSize="10" fill="currentColor">无法辨识 → 请求补测</text>
    <path d="M121 248V266" stroke="currentColor" strokeOpacity=".5"/>
    <rect x="20" y="266" width="202" height="35" rx="6" fill="#64748b" fillOpacity=".12" stroke="#64748b"/>
    <text x="121" y="288" textAnchor="middle" fontSize="12" fill="currentColor">Geometry IR / 制造模板</text>
    <path d="M121 301V318 M121 318H87V333 M121 318H253V333" fill="none" stroke="currentColor" strokeOpacity=".5"/>
    <rect x="20" y="333" width="134" height="40" rx="6" fill="#16a34a" fillOpacity=".09" stroke="#16a34a"/>
    <text x="87" y="357" textAnchor="middle" fontSize="12" fill="currentColor">1:1 SVG / PDF</text>
    <rect x="178" y="333" width="150" height="40" rx="6" fill="#16a34a" fillOpacity=".09" stroke="#16a34a"/>
    <text x="253" y="350" textAnchor="middle" fontSize="12" fill="currentColor">折叠与制造门禁</text>
    <text x="253" y="364" textAnchor="middle" fontSize="10" fill="currentColor">独立数值验证</text>
    <text x="280" y="205" textAnchor="middle" fontSize="10" fill="currentColor" opacity=".7">AI 负责</text>
    <text x="280" y="220" textAnchor="middle" fontSize="10" fill="currentColor" opacity=".7">识别与观测</text>
    <text x="280" y="270" textAnchor="middle" fontSize="10" fill="currentColor" opacity=".7">数学内核负责</text>
    <text x="280" y="285" textAnchor="middle" fontSize="10" fill="currentColor" opacity=".7">尺寸与制造</text>
  </svg>
</box>

基本目标函数可以直接表达为：

\[
\min_{\theta,K,R,t}
\sum_i w_i\rho\left(
\|\pi(K,R,t,X_i(\theta))-u_i\|^2
\right)
\]

其中：

- \(\theta\)：包装参数，例如 W、D、H、屋顶高度。
- \(X_i(\theta)\)：参数化模板计算出的三维关键点。
- \(u_i\)：图像中观测到的二维关键点。
- \(K,R,t\)：相机内参及位姿。
- 实测尺寸作为硬约束；存在测量容差时，则以其可信区间约束求解。

这样做的最大优势，是不用先恢复一个任意三维网格，再艰难地把它转换成可制造结构。

**已知包装属于参数化几何族，就直接在这个低维参数空间里求解。**

### 3.1 不能过度神化消点闭式解

你说长方体存在解析解，这个方向正确，但成立需要前提：

| 条件 | 风险 |
|---|---|
| 三组方向确实正交 | 变形纸盒可能不满足 |
| 主点等内参已知或可合理约束 | 手机裁切、变焦可能改变内参 |
| 边线可准确提取 | 圆角、图案、反光会引入误检 |
| 透视条件良好 | 消点很远时数值不稳定 |
| 存在尺度参考 | 单张图像不能凭空恢复绝对尺寸 |

Criminisi 的工作不仅讨论几何测量，还讨论了测量误差传播；Pears 等人的长方体研究使用了参考目标。二者都不支持「任意手机照片必然能解析恢复精确尺寸」这一更强声明。<Cite refs={["turn920635search0","turn920635search3"]}/>

所以我要求把 2.1 拆成三个层次：

| 基线 | 输入 | 验证目的 |
|---|---|---|
| B0 | 人工标注关键点 + 已知尺度 | 测试数学求解器能力上限 |
| B1 | 自动关键点或边线 + 已知尺度 | 测试完整视觉测量能力 |
| B2 | 多视角 + 参数化联合拟合 | 测试额外视角的实际收益 |

如果 B0 都达不到要求，不应该继续投资自动识别或训练 CNN。

### 3.2 更大的遗漏：逆问题不一定有唯一解

<grid columns={2} gap={3}>
  <grid-item>
    <AsyncImage query="straight tuck end folding carton unfolded dieline top bottom flaps technical drawing" aspectRatio="4:3" fit="contain"/>
    **直插式纸盒结构**
  </grid-item>
  <grid-item>
    <AsyncImage query="reverse tuck end folding carton unfolded dieline opposite direction flaps technical drawing" aspectRatio="4:3" fit="contain"/>
    **反插式纸盒结构**
  </grid-item>
</grid>

两种内部结构不同的纸盒，封闭后外观可能高度相似。

照片即使足够清晰，也不一定能确定内部粘口、插舌、封底方式、压线偏置及隐藏搭接关系。更多视角甚至也未必能解决不可见的内部结构。

因此必须区分：

| 产品模式 | 承诺 |
|---|---|
| 原版复原 | 尽可能恢复原包装的真实刀版，需要打开或拆解等额外证据 |
| 功能等价再设计 | 依据外形尺寸及结构要求，生成可制造的等价包装 |

这是我认为本轮最重要的设计层遗漏之一。两种任务可以共享 Geometry IR，但不能共享同一个验收定义。

### 3.3 真实数据采集必须升级

同意 2.0 提升为 P0，但不能仅仅采集 20–30 件包装的多角度照片和长宽高。

我要求建立三层真值：

| 真值层 | 采集内容 | 用途 |
|---|---|---|
| GT-A 成品几何 | W/D/H、屋顶高度、关键边长、材料厚度、重复测量 | 几何回归 |
| GT-B 结构拓扑 | 开盖、底部、粘口、搭接、内部结构照片 | 模板识别 |
| GT-C 展开刀版 | 拆解后的带尺度平铺扫描、裁切轮廓、压线坐标 | 端到端刀版验收 |

建议第一批 24 件，集中在六个主力结构族，每族四件，而不是从 100 类中随意抽取 24 件。

每件至少六张重叠视角图像，并增加一套带标定板的受控照片。尺寸真值建议重复测量三次，记录测量基准及重复性。

同时模拟三种真实使用模式：

- 用户只拍一张照片，提供一个实测尺寸。
- 用户拍三张照片，提供一个或两个实测尺寸。
- 用户拍六张以上照片，允许补测及开盖观察。

必须保证用于评价的实测尺寸不是全部作为算法输入，否则最终精度没有测量意义。

这 24 件适合路线选择与工程 PoC，不足以证明广泛生产环境下的泛化能力。后续还需要独立留出实物。

### 3.4 多视角前馈模型如何处置？

降级为 L2 研究候选，而非项目主干。

我建议对比顺序如下：

| 顺序 | 方法 | 当前处置 |
|---|---|---|
| 1 | 人工关键点 + 解析几何 | 立即实施 |
| 2 | 自动边线/关键点 + 参数化拟合 | 主路线 |
| 3 | 标定相机 + 多视角联合优化 | 高精度基线 |
| 4 | COLMAP 等传统 SfM | 对照路线 |
| 5 | VGGT / π³ / MapAnything 等 | 有干净真值后再测 |
| 6 | CNN 端到端尺寸回归 | 冻结训练扩张，保留实验资产 |

传统 SfM 的价值不在于一定能够重建低纹理纸盒，而在于它提供了与前馈基础模型不同的技术基线。COLMAP 的增量重建、三角化、Bundle Adjustment 都可以作为对照。<Cite refs={["turn877058search8","turn877058search22"]}/>

---

## 4. Q3 裁决：货架孪生迁出，100 类保质量

### 4.1 货架孪生线：迁出

我明确选择迁出，而不是继续在 PhotoDieline 仓库里维护货架孪生子系统。

你已经有 `openusd-retail-twin` 这一独立研究方向，两个项目之间完全可以形成上下游关系。公开 README 本身也已将其定位为独立姊妹仓。<Cite refs={["turn920635view0"]}/>

<box border radius="lg" padding={3} gap={2}>
  <svg viewBox="0 0 340 236" width="100%">
    <rect x="10" y="8" width="320" height="80" rx="7" stroke="#2563eb" fill="#2563eb" fillOpacity=".07"/>
    <text x="170" y="28" textAnchor="middle" fontSize="14" fontWeight="600" fill="currentColor">photo-dieline</text>
    <text x="170" y="47" textAnchor="middle" fontSize="11" fill="currentColor">照片测量 · 参数化几何 · 刀版</text>
    <text x="170" y="65" textAnchor="middle" fontSize="11" fill="currentColor">制造 QA · 折叠验证</text>
    <path d="M170 88V144" stroke="#64748b" strokeWidth="1.5"/>
    <path d="M165 138L170 145L175 138" stroke="#64748b" fill="none"/>
    <rect x="83" y="101" width="174" height="29" rx="4" fill="#64748b" fillOpacity=".17"/>
    <text x="170" y="119" textAnchor="middle" fontSize="11" fill="currentColor">版本化 Geometry IR / 资产接口</text>
    <rect x="10" y="145" width="320" height="80" rx="7" stroke="#16a34a" fill="#16a34a" fillOpacity=".07"/>
    <text x="170" y="165" textAnchor="middle" fontSize="14" fontWeight="600" fill="currentColor">openusd-retail-twin</text>
    <text x="170" y="184" textAnchor="middle" fontSize="11" fill="currentColor">OpenUSD · ESR · 货架布置</text>
    <text x="170" y="202" textAnchor="middle" fontSize="11" fill="currentColor">视觉渲染 · SDG · 下游 AI</text>
  </svg>
  <caption>制造几何作为上游资产，零售数字孪生作为下游消费者；共享协议，不共享发布门禁。</caption>
</box>

PhotoDieline 可以保留少量 USD 转换示例和跨仓接口契约测试，但不应继续保留完整货架构建与摄影优化管线。

原因不是这部分研究失败，而是两者的优化目标天然不同。

| 维度 | PhotoDieline | 货架孪生 |
|---|---|---|
| 主要目标 | 物理尺寸与制造正确性 | 场景和资产真实性 |
| 核心数据 | 参数、边、面、折线 | USD、材质、纹理、场景 |
| 验收方法 | 毫米误差、拓扑、折叠 | 语义、物理、视觉、下游任务 |
| 典型用户 | 包装设计、印前人员 | 零售研究、视觉 AI 人员 |
| 主要技术债 | 几何与制造约束 | 渲染与资产工程 |

另外，迁移前先清理第三方素材及其授权问题，不要把合规风险原样复制到另一个仓库。

### 4.2 100 类：保留研究覆盖，取消制造数量承诺

我反对为了提高真实可制造比例而直接删除已有模板，也反对继续用 100 类全绿作为项目核心宣传。

正确做法是分级发布。

<box border radius="lg" padding={3} gap={2}>
  <title size="md">模板能力成熟度体系</title>
  {#each [
    ["L0","REGISTERED","结构已注册","存在参数化生成实现","#94a3b8"],
    ["L1","GEOMETRY_VALID","展开几何有效","拓扑、裁切、折线合法","#64748b"],
    ["L2","FOLD_VALID","数值折叠有效","可达性、干涉与接缝通过","#2563eb"],
    ["L3","PROTOTYPE_VERIFIED","实物样件验证","裁切、压线、折叠、粘合实测","#0d9488"],
    ["L4","PRODUCTION_APPROVED","指定工艺人工签核","材料、设备、印前要求确认","#16a34a"]
  ] as s,i}
    <row align="start" gap={3}>
      <box background={s[4]} width="6px" height="52px" radius="sm"/>
      <box flex={1} gap=0>
        <row>
          **{s[0]} · {s[2]}**
          <spacer/>
          <caption>{s[1]}</caption>
        </row>
        <text size="sm" color="secondary">{s[3]}</text>
      </box>
    </row>
    {#if i!==4}<divider/>{/if}
  {/each}
</box>

原来的 100 类可以继续作为 L0 研究资产存在，但不能默认获得 L1–L4。

成熟度必须同时绑定模板版本、经过验证的参数域及材料条件。一个默认尺寸通过的模板，不代表所有尺寸都能通过。

建议第一阶段先做透五个结构：

| 核心结构 | 验证价值 |
|---|---|
| RSC 瓦楞箱 | 基础墙板、箱盖、搭接 |
| 直插式纸盒 | 插舌、槽口、折叠顺序 |
| 反插式纸盒 | 相似外观下的不同结构 |
| 自锁底纸盒 | 多面耦合、折叠可达性 |
| 屋顶包 | 非长方体几何、封口及复杂折线 |

**五种真正经过物理裁切、折叠与尺寸实测的模板，比 100 种仅通过自有数值门禁的模板更有技术说服力。**

---

## 5. 优化清单逐条审议

总体上，我认为你的 T0–T3 分类合理，但不能作为严格串行的四个阶段执行。真实数据采集需要和制造内核修复并行启动。

### T0：让仓说实话

| 事项 | 裁决 | 调整后的要求 |
|---|---|---|
| 0.1 导出与门修复 | 同意 | 本地实现完成不等于验收完成，补独立 oracle、原负探针回放 |
| 0.2 G03 重叠和裁切 | 同意 | 补合法共边、槽孔、共线细分、容差处理 |
| 0.3 负探针及水密性 | 修改 | 禁止恒真判据；水密性必须按结构语义启用，不能对所有包装强制 |
| 0.4 素材出库与台账 | 同意 | 提升至最先执行的 P0，检查 Git 历史及许可传播 |
| 0.5 ESR | 修改 | 立即撤销未经现行验证的声明；重修工作放入下游独立仓 |
| 0.6 文档对齐 | 同意 | 不等所有缺陷修复才更新 README，先撤回过度声明 |
| **0.7 新增** | **必做** | 冻结旧版证据和负探针，避免修复过程中丢失问题来源 |
| **0.8 新增** | **必做** | 禁止关键字段静默默认、静默忽略、验证失败后继续升级交付状态 |

注意，不能把「水密性」直接等同于纸盒制造有效性。多数折叠纸盒不是密封容器，合法搭接、开放口和间隙都可能破坏数学水密条件。

### T1：模板可制造性

| 事项 | 裁决 | 调整后的要求 |
|---|---|---|
| 37 类粘口修正 | 修改 | 优先修通用有向折线与接缝关系，不要逐模板打补丁 |
| 15 类重叠结构 | 同意 | 尝试先归类为布局内核缺陷、模板缺陷和拓扑归一化缺陷 |
| G04/G06 | 同意 | 加折叠路径干涉、目标接缝配对和插舌槽口约束 |
| ECMA/FEFCO | 同意 | 建立标准编码与内部参数族映射，禁止为凑覆盖率扩张 |
| 板厚补偿 | 同意 | 必须定义内尺寸、外尺寸、中性层和压线基准 |
| DXF | 延后 | SVG/PDF 尚未完成独立验收前，不增加导出格式 |
| **实物试制** | **新增 P0** | 对核心五类进行 1:1 裁切、压线、折叠及尺寸回测 |
| **参数域验证** | **新增 P0** | 默认值、最小值、最大值、极端比例、边界失效样本 |

我不同意现在直接承诺 1–2 周完成 37 类修复和全部可制造验证。修正数学几何可能很快，但在材料、压线和实物工艺条件未确定时，无法证明完整的制造闭环。

### T2：学习线

| 事项 | 裁决 | 调整后的要求 |
|---|---|---|
| 2.0 真实实物采集 | 同意，提升 | 与 T0 并行，不等待模板修复结束 |
| 2.1 解析几何 | 同意，扩展 | 先人工关键点 oracle，再自动关键点和参数化拟合 |
| 2.2 训练几何 ×10 | **反对当前执行** | 完成 E4 因果对照及真实测试后才决定 |
| 2.3 检索式分类 | 修改 | 检索、规则、人工确认并列比较，不预设检索最终胜出 |
| 2.4 多视角前馈模型 | 同意降级 | 基准冻结之后，按同一实物、同一输入条件比较 |
| **2.5 新增** | **必做** | 参数不确定性、不可辨识检测及主动补测 |
| **2.6 新增** | **必做** | 原版复原与功能等价再设计分开评价 |

### T3：货架孪生线

| 事项 | 裁决 | 调整后的要求 |
|---|---|---|
| 独立仓迁移 | 同意 | 优先迁入现有零售数字孪生研究体系 |
| 保留 ESR 验证样例 | 部分同意 | 只保留少量接口级示例，不保留货架主干 |
| 三门否决力 | 同意 | 迁移后重新建立独立验证体系 |
| 2105 行脚本拆分 | 降级 | 模块拆分不是当前 PhotoDieline P0 |
| SimReady Foundation | 同意 | 固定校验器、tier、profile 及规则版本，保留实际验证产物 |

NVIDIA 的 SimReady Foundation 已提供可测试的内容要求与官方校验机制。不过它解决的是资产是否满足指定用途的内容约束，不代表包装实际尺寸、印刷或商品身份已经正确。<Cite refs={["turn877058search21","turn877058search23","turn877058search26"]}/>

## 6. Q4 裁决：遗漏的文献、方法与风险

我不建议继续无差别增加文献检索数量。现阶段最值得补的是能够改变技术决策的研究。

### 6.1 建议补充的文献

| 文献或技术体系 | 年份 | 对项目的直接价值 | 优先级 |
|---|---:|---|---|
| Zhang — A Flexible New Technique for Camera Calibration | 2000 | 手机相机内参标定，区分成像误差与几何误差 | P0 |
| Hartley & Zisserman — Multiple View Geometry | 2004 | 投影几何、三角化、退化条件、不确定性 | P0 |
| Geirhos — Shortcut Learning in Deep Neural Networks | 2020 | 排查 CNN 是否只是在识别变体 | P0 |
| Beex & Peerlings — An Experimental and Computational Study of Laminated Paperboard Creasing and Folding | 2009 | 解释板厚、压线、分层与折叠力学 | P0 |
| JCGM 100 — Guide to the Expression of Uncertainty in Measurement | 2008 | 建立毫米级真值的测量不确定性体系 | P0 |
| Guo 等 — On Calibration of Modern Neural Networks | 2017 | 解释分类置信度失真，建立概率校准基线 | P1 |
| Geifman & El-Yaniv — Selective Classification / SelectiveNet | 2017/2019 | 按风险—覆盖率建立拒识策略 | P1 |
| Schönberger & Frahm — Structure-from-Motion Revisited | 2016 | 建立独立于 VGGT 的多视角基线 | P1 |
| Demaine & O'Rourke — Geometric Folding Algorithms | 2007 | 理解折叠可达性和展开几何的计算问题 | P1 |
| ECMA / FEFCO Recommendation 101 | 行业规范 | 结构分类、压线补偿、尺寸定义 | P0 |

其中已重点核对的资料：

<box gap={3}>
  <row align="start">
    <icon name="book-open" color="secondary" size="lg"/>
    <box flex={1} gap=1>
      **[Zhang：相机标定](https://ieeexplore.ieee.org/abstract/document/888718/authors)**

      <text size="sm">2000 年。不要直接让学习模型承担相机畸变和尺度恢复问题。</text>
      <caption>IEEE TPAMI <Cite refs={["turn877058search1"]}/></caption>
    </box>
  </row>
  <divider/>
  <row align="start">
    <icon name="book-open" color="secondary" size="lg"/>
    <box flex={1} gap=1>
      **[Beex & Peerlings：纸板压线与折叠](https://www.sciencedirect.com/science/article/pii/S0020768309003084)**

      <text size="sm">2009 年。板厚补偿不是简单地把全部面板长度加减一个厚度；真实压线区域存在更复杂的材料力学行为。</text>
      <caption>International Journal of Solids and Structures <Cite refs={["turn282524search1","turn282524search4"]}/></caption>
    </box>
  </row>
  <divider/>
  <row align="start">
    <icon name="book-open" color="secondary" size="lg"/>
    <box flex={1} gap=1>
      **[SelectiveNet：带拒识能力的预测模型](https://proceedings.mlr.press/v97/geifman19a)**

      <text size="sm">2019 年。不要再单独优化分类准确率，应评价系统在不同自动接受比例下的错误风险。</text>
      <caption>ICML <Cite refs={["turn877058search7"]}/></caption>
    </box>
  </row>
  <divider/>
  <row align="start">
    <icon name="book-open" color="secondary" size="lg"/>
    <box flex={1} gap=1>
      **[FEFCO 国际包装结构编码](https://www.fefco.org/technical-information/fefco-code)**

      <text size="sm">适合建立瓦楞包装的独立结构目录，但标准编码不是制造合规认证。</text>
      <caption>FEFCO 官方资料 <Cite refs={["turn877058search2","turn877058search37"]}/></caption>
    </box>
  </row>
</box>

### 6.2 你最值得尝试的三个替代方案

我认为这三个方案比再引入一个大型视觉模型更有可能迅速推进北极星。

<row align="start" gap={3}>
  <AsyncImage query="AprilTag fiducial markers calibration board next to cardboard box computer vision measurement" aspectRatio="1:1" maxWidth="112px"/>
  <box flex={1} gap={1}>
    **方案 A：标定卡 + 手机照片**

    在包装旁边放置已知尺寸的标定卡，约束尺度和相机位姿。成本低、可重复性强，适合作为第一阶段受控测量工具。

    <text color="secondary" size="sm">优先级：P0</text>
  </box>
</row>
<divider/>
<row align="start" gap={3}>
  <AsyncImage query="3d cuboid wireframe projected over object image pose estimation model fitting computer vision" aspectRatio="1:1" maxWidth="112px"/>
  <box flex={1} gap={1}>
    **方案 B：参数化模板投影拟合**

    将可调节的三维模板投影到照片上，用真实轮廓和边缘不断修正尺寸及位姿。直接求制造参数，避免任意网格重建带来的转换误差。

    <text color="secondary" size="sm">优先级：P0</text>
  </box>
</row>
<divider/>
<row align="start" gap={3}>
  <AsyncImage query="disassembled cardboard carton packaging unfolded flat on cutting mat measuring ruler dieline" aspectRatio="1:1" maxWidth="112px"/>
  <box flex={1} gap={1}>
    **方案 C：拆解平铺扫描**

    对允许拆解的包装，直接从平铺扫描获取裁切与压线信息。它既是独立的低成本技术路线，也是照片逆向重建的实物真值来源。

    <text color="secondary" size="sm">优先级：P0</text>
  </box>
</row>

尤其是方案 C。你目前在研究如何从三维照片恢复二维刀版，但在可以破坏性拆解的业务场景中，直接获取二维刀版本身就是很有竞争力的方案。

不应该因为它不够 AI，而把它排除在基线之外。

### 6.3 遗漏的八项关键风险

| 风险 | 后果 | 推荐控制 |
|---|---|---|
| 隐藏结构不可辨识 | 外观正确但刀版错误 | 明确复原/再设计模式 |
| 测量真值不够准确 | 模型误差和测量误差混淆 | 重复测量及不确定性记录 |
| 几何算法共享错误 | 导出和验证同时出错 | 独立 oracle |
| 默认参数偏差 | 默认尺寸正确，其他尺寸失败 | 参数域属性测试 |
| 内外尺寸混用 | 成品不能正确装入商品 | 统一尺寸基准 |
| 印前工艺不完整 | 文件可打开但无法生产 | PDF/X-4、专色、叠印、线型预检 |
| 锁底等结构不可折叠 | 数值闭合但实物无法组装 | 折叠过程检查及物理试制 |
| 验证集被反复使用 | 多轮优化后产生验证集过拟合 | 封存独立实物盲测集 |

还有一个贯穿整个项目的指标问题：**全局 MAE ≤0.5mm 本身不足以作为制造验收标准。**

同样的 0.5mm 误差，对于 200mm 的墙板与 3mm 的插槽，制造后果完全不同。

应按特征定义容差，包括主尺寸、接缝位置、插舌、槽口、压线、出血和套准，而不是所有几何要素共享一个阈值。

---

## 7. 我认为最值得执行的 Top 5 行动

按照风险降低、研究信息增益和执行成本排序，而不是按照代码工作量排序。

<box border radius="lg" padding={3} gap={3}>
  <row align="start">
    <title size="xl" color="secondary">01</title>
    <box flex={1} gap={1}>
      **冻结旧证据，恢复门禁真实性**

      <caption>建议投入：2–3 人日</caption>
      撤销过度声明，完成独立导出验证，回放 27 个破坏探针，补充重叠和折线门禁，优先处理无许可素材。

      <row>
        <text color="secondary" size="sm">性价比</text>
        <spacer/>
        **极高**
      </row>
      <box height={6} radius="full" background="surface-tertiary"><box height="100%" width="100%" radius="full" background="#16a34a"/></box>
    </box>
  </row>
  <divider/>
  <row align="start">
    <title size="xl" color="secondary">02</title>
    <box flex={1} gap={1}>
      **建立 24 件真实包装黄金数据集**

      <caption>建议投入：2–4 人日，与第一项并行</caption>
      包括成品照片、尺寸真值、结构证据、拆解刀版。封存独立测试对象，不允许模型训练使用。

      <row>
        <text color="secondary" size="sm">性价比</text>
        <spacer/>
        **极高**
      </row>
      <box height={6} radius="full" background="surface-tertiary"><box height="100%" width="100%" radius="full" background="#16a34a"/></box>
    </box>
  </row>
  <divider/>
  <row align="start">
    <title size="xl" color="secondary">03</title>
    <box flex={1} gap={1}>
      **实现零训练参数化测量基线**

      <caption>建议投入：3–5 人日</caption>
      人工关键点 + 尺度锚点 + 投影几何拟合，与常数、最近邻查表、现有 CNN 同标尺盲测。

      <row>
        <text color="secondary" size="sm">性价比</text>
        <spacer/>
        **极高**
      </row>
      <box height={6} radius="full" background="surface-tertiary"><box height="100%" width="95%" radius="full" background="#16a34a"/></box>
    </box>
  </row>
  <divider/>
  <row align="start">
    <title size="xl" color="secondary">04</title>
    <box flex={1} gap={1}>
      **建立五类包装真实制造闭环**

      <caption>建议投入：5–10 人日的首轮试制与修正预算</caption>
      先验证少量代表结构，覆盖真实板厚、折叠干涉、裁切压线、样件回测，再以通用修复扩展模板族。

      <row>
        <text color="secondary" size="sm">性价比</text>
        <spacer/>
        **高**
      </row>
      <box height={6} radius="full" background="surface-tertiary"><box height="100%" width="90%" radius="full" background="#16a34a"/></box>
    </box>
  </row>
  <divider/>
  <row align="start">
    <title size="xl" color="secondary">05</title>
    <box flex={1} gap={1}>
      **货架研究拆仓，冻结无证据的学习扩张**

      <caption>建议投入：1–2 人日完成范围隔离</caption>
      固定跨仓资产接口，货架独立发布；暂缓 CNN ×10、基础模型升级及新增模板数量目标。

      <row>
        <text color="secondary" size="sm">性价比</text>
        <spacer/>
        **高**
      </row>
      <box height={6} radius="full" background="surface-tertiary"><box height="100%" width="85%" radius="full" background="#16a34a"/></box>
    </box>
  </row>
  <caption>投入为评审建议预算，非实测工期；性价比为定性判断。</caption>
</box>

## 8. 下一阶段执行边界

按照你此前设定的单次研究迭代不超过八周的治理原则，我建议本轮设置一个更短的四周裁决窗口，不允许无限扩张研究范围。

<box border radius="lg" padding={3} gap={2}>
  <title size="md">四周研究与验收计划</title>
  <svg viewBox="0 0 350 204" width="100%">
    {#each [0,1,2,3] as w}
      <text x={157+w*54} y="15" fontSize="11" textAnchor="middle" fill="currentColor">W{w+1}</text>
      <path d={`M${130+w*54} 25V194`} stroke="currentColor" strokeOpacity=".1"/>
    {/each}
    {#each [
      ["门禁与声明修复",0,1,"#64748b"],
      ["真实数据采集",0,1.5,"#2563eb"],
      ["解析几何基线",0.6,1.6,"#2563eb"],
      ["五类实物制造",0.8,2.9,"#0d9488"],
      ["独立盲测与裁决",2.8,1.2,"#16a34a"],
      ["货架范围隔离",0,0.7,"#64748b"]
    ] as t,i}
      <text x="3" y={42+i*27} fontSize="11" fill="currentColor">{t[0]}</text>
      <rect x={131+t[1]*54} y={30+i*27} width={t[2]*54-2} height="16" rx="3" fill={t[3]}/>
    {/each}
  </svg>
  <caption>并行工作包设计。第四周做路线裁决，不以所有模板修复完成作为结束条件。</caption>
</box>

{@body const checks=["原负探针全部重新执行并有明确预期","SVG/PDF 独立解析与物理尺寸验证","24 件真实实物及刀版真值完成冻结","解析几何与 CNN 同测试集盲测","五类实物裁切折叠与尺寸回测","货架孪生独立发布边界建立"]}
{@body const [done,setDone]=DIL.useState([false,false,false,false,false,false])}
<card gap={3}>
  <row align="center">
    <title size="md">R2 准入验收清单</title>
    <spacer/>
    <caption>{done.filter(Boolean).length}/6</caption>
  </row>
  <box height={6} background="surface-tertiary" radius="full">
    <box height="100%" background="#16a34a" radius="full" width={`${done.filter(Boolean).length/6*100}%`}/>
  </box>
  {#each checks as item,i}
    <checkbox key={i} checked={done[i]} onChange={v=>setDone(old=>old.map((x,j)=>j===i?v:x))}>{item}</checkbox>
  {/each}
  <button block variant="outline" onClick={()=>GenUI.copy(checks.map((x,i)=>(done[i]?"[x] ":"[ ] ")+x).join("\n"))}><icon name="copy" size="sm"/> 复制验收清单</button>
</card>

## 9. 最终路线裁决汇总

| 裁决项 | 最终决定 |
|---|---|
| 参数化制造几何主干 | 保留，继续加强 |
| 现有 100/100 制造验收声明 | 撤回，重新分级验证 |
| 几何覆盖稀疏是误差主因 | 不予确认 |
| CNN 直接回归 | 暂停资源扩张，保留对照 |
| 零训练解析几何 | 提升为 P0 |
| 参数化逆向拟合 | 新增主研究路线 |
| 多视角前馈基础模型 | 降级为研究候选 |
| 合成数据引擎全面升级 | 暂缓，先确定有效变量 |
| 真实物理数据集 | P0，不可再延后 |
| 模板数量扩张 | 暂停 |
| 货架孪生 / ESR | 迁出主仓 |
| PRINT-READY 人工签核原则 | 保留，禁止自动升级 |

---

**一句总评：PhotoDieline 下一阶段不应该继续证明 AI 能生成多少种包装，而应该证明它能从有限的真实观测中，恢复可辨识的制造参数，并让每一份宣称正确的刀版经得起独立数值验证和真实物理折叠。**

<MemoryCite />

---

# GPT 答复终稿 (第 6–9 节详版, 原文)

## 6. Q4 裁决：遗漏的文献、方法与风险

我不建议继续无差别增加文献检索数量。现阶段最值得补的是能够改变技术决策的研究。

### 6.1 建议补充的文献

| 文献或技术体系 | 年份 | 对项目的直接价值 | 优先级 |
|---|---:|---|---|
| Zhang — A Flexible New Technique for Camera Calibration | 2000 | 手机相机内参标定，区分成像误差与几何误差 | P0 |
| Hartley & Zisserman — Multiple View Geometry | 2004 | 投影几何、三角化、退化条件、不确定性 | P0 |
| Geirhos — Shortcut Learning in Deep Neural Networks | 2020 | 排查 CNN 是否只是在识别变体 | P0 |
| Beex & Peerlings — An Experimental and Computational Study of Laminated Paperboard Creasing and Folding | 2009 | 解释板厚、压线、分层与折叠力学 | P0 |
| JCGM 100 — Guide to the Expression of Uncertainty in Measurement | 2008 | 建立毫米级真值的测量不确定性体系 | P0 |
| Guo 等 — On Calibration of Modern Neural Networks | 2017 | 解释分类置信度失真，建立概率校准基线 | P1 |
| Geifman & El-Yaniv — Selective Classification / SelectiveNet | 2017/2019 | 按风险—覆盖率建立拒识策略 | P1 |
| Schönberger & Frahm — Structure-from-Motion Revisited | 2016 | 建立独立于 VGGT 的多视角基线 | P1 |
| Demaine & O'Rourke — Geometric Folding Algorithms | 2007 | 理解折叠可达性和展开几何的计算问题 | P1 |
| ECMA / FEFCO Recommendation 101 | 行业规范 | 结构分类、压线补偿、尺寸定义 | P0 |

其中已重点核对的资料：

<box gap={3}>
  <row align="start">
    <icon name="book-open" color="secondary" size="lg"/>
    <box flex={1} gap=1>
      **[Zhang：相机标定](https://ieeexplore.ieee.org/abstract/document/888718/authors)**

      <text size="sm">2000 年。不要直接让学习模型承担相机畸变和尺度恢复问题。</text>
      <caption>IEEE TPAMI <Cite refs={["turn877058search1"]}/></caption>
    </box>
  </row>
  <divider/>
  <row align="start">
    <icon name="book-open" color="secondary" size="lg"/>
    <box flex={1} gap=1>
      **[Beex & Peerlings：纸板压线与折叠](https://www.sciencedirect.com/science/article/pii/S0020768309003084)**

      <text size="sm">2009 年。板厚补偿不是简单地把全部面板长度加减一个厚度；真实压线区域存在更复杂的材料力学行为。</text>
      <caption>International Journal of Solids and Structures <Cite refs={["turn282524search1","turn282524search4"]}/></caption>
    </box>
  </row>
  <divider/>
  <row align="start">
    <icon name="book-open" color="secondary" size="lg"/>
    <box flex={1} gap=1>
      **[SelectiveNet：带拒识能力的预测模型](https://proceedings.mlr.press/v97/geifman19a)**

      <text size="sm">2019 年。不要再单独优化分类准确率，应评价系统在不同自动接受比例下的错误风险。</text>
      <caption>ICML <Cite refs={["turn877058search7"]}/></caption>
    </box>
  </row>
  <divider/>
  <row align="start">
    <icon name="book-open" color="secondary" size="lg"/>
    <box flex={1} gap=1>
      **[FEFCO 国际包装结构编码](https://www.fefco.org/technical-information/fefco-code)**

      <text size="sm">适合建立瓦楞包装的独立结构目录，但标准编码不是制造合规认证。</text>
      <caption>FEFCO 官方资料 <Cite refs={["turn877058search2","turn877058search37"]}/></caption>
    </box>
  </row>
</box>

### 6.2 你最值得尝试的三个替代方案

我认为这三个方案比再引入一个大型视觉模型更有可能迅速推进北极星。

<row align="start" gap={3}>
  <AsyncImage query="AprilTag fiducial markers calibration board next to cardboard box computer vision measurement" aspectRatio="1:1" maxWidth="112px"/>
  <box flex={1} gap={1}>
    **方案 A：标定卡 + 手机照片**

    在包装旁边放置已知尺寸的标定卡，约束尺度和相机位姿。成本低、可重复性强，适合作为第一阶段受控测量工具。

    <text color="secondary" size="sm">优先级：P0</text>
  </box>
</row>
<divider/>
<row align="start" gap={3}>
  <AsyncImage query="3d cuboid wireframe projected over object image pose estimation model fitting computer vision" aspectRatio="1:1" maxWidth="112px"/>
  <box flex={1} gap={1}>
    **方案 B：参数化模板投影拟合**

    将可调节的三维模板投影到照片上，用真实轮廓和边缘不断修正尺寸及位姿。直接求制造参数，避免任意网格重建带来的转换误差。

    <text color="secondary" size="sm">优先级：P0</text>
  </box>
</row>
<divider/>
<row align="start" gap={3}>
  <AsyncImage query="disassembled cardboard carton packaging unfolded flat on cutting mat measuring ruler dieline" aspectRatio="1:1" maxWidth="112px"/>
  <box flex={1} gap={1}>
    **方案 C：拆解平铺扫描**

    对允许拆解的包装，直接从平铺扫描获取裁切与压线信息。它既是独立的低成本技术路线，也是照片逆向重建的实物真值来源。

    <text color="secondary" size="sm">优先级：P0</text>
  </box>
</row>

尤其是方案 C。你目前在研究如何从三维照片恢复二维刀版，但在可以破坏性拆解的业务场景中，直接获取二维刀版本身就是很有竞争力的方案。

不应该因为它不够 AI，而把它排除在基线之外。

### 6.3 遗漏的八项关键风险

| 风险 | 后果 | 推荐控制 |
|---|---|---|
| 隐藏结构不可辨识 | 外观正确但刀版错误 | 明确复原/再设计模式 |
| 测量真值不够准确 | 模型误差和测量误差混淆 | 重复测量及不确定性记录 |
| 几何算法共享错误 | 导出和验证同时出错 | 独立 oracle |
| 默认参数偏差 | 默认尺寸正确，其他尺寸失败 | 参数域属性测试 |
| 内外尺寸混用 | 成品不能正确装入商品 | 统一尺寸基准 |
| 印前工艺不完整 | 文件可打开但无法生产 | PDF/X-4、专色、叠印、线型预检 |
| 锁底等结构不可折叠 | 数值闭合但实物无法组装 | 折叠过程检查及物理试制 |
| 验证集被反复使用 | 多轮优化后产生验证集过拟合 | 封存独立实物盲测集 |

还有一个贯穿整个项目的指标问题：**全局 MAE ≤0.5mm 本身不足以作为制造验收标准。**

同样的 0.5mm 误差，对于 200mm 的墙板与 3mm 的插槽，制造后果完全不同。

应按特征定义容差，包括主尺寸、接缝位置、插舌、槽口、压线、出血和套准，而不是所有几何要素共享一个阈值。

---

## 7. 我认为最值得执行的 Top 5 行动

按照风险降低、研究信息增益和执行成本排序，而不是按照代码工作量排序。

<box border radius="lg" padding={3} gap={3}>
  <row align="start">
    <title size="xl" color="secondary">01</title>
    <box flex={1} gap={1}>
      **冻结旧证据，恢复门禁真实性**

      <caption>建议投入：2–3 人日</caption>
      撤销过度声明，完成独立导出验证，回放 27 个破坏探针，补充重叠和折线门禁，优先处理无许可素材。

      <row>
        <text color="secondary" size="sm">性价比</text>
        <spacer/>
        **极高**
      </row>
      <box height={6} radius="full" background="surface-tertiary"><box height="100%" width="100%" radius="full" background="#16a34a"/></box>
    </box>
  </row>
  <divider/>
  <row align="start">
    <title size="xl" color="secondary">02</title>
    <box flex={1} gap={1}>
      **建立 24 件真实包装黄金数据集**

      <caption>建议投入：2–4 人日，与第一项并行</caption>
      包括成品照片、尺寸真值、结构证据、拆解刀版。封存独立测试对象，不允许模型训练使用。

      <row>
        <text color="secondary" size="sm">性价比</text>
        <spacer/>
        **极高**
      </row>
      <box height={6} radius="full" background="surface-tertiary"><box height="100%" width="100%" radius="full" background="#16a34a"/></box>
    </box>
  </row>
  <divider/>
  <row align="start">
    <title size="xl" color="secondary">03</title>
    <box flex={1} gap={1}>
      **实现零训练参数化测量基线**

      <caption>建议投入：3–5 人日</caption>
      人工关键点 + 尺度锚点 + 投影几何拟合，与常数、最近邻查表、现有 CNN 同标尺盲测。

      <row>
        <text color="secondary" size="sm">性价比</text>
        <spacer/>
        **极高**
      </row>
      <box height={6} radius="full" background="surface-tertiary"><box height="100%" width="95%" radius="full" background="#16a34a"/></box>
    </box>
  </row>
  <divider/>
  <row align="start">
    <title size="xl" color="secondary">04</title>
    <box flex={1} gap={1}>
      **建立五类包装真实制造闭环**

      <caption>建议投入：5–10 人日的首轮试制与修正预算</caption>
      先验证少量代表结构，覆盖真实板厚、折叠干涉、裁切压线、样件回测，再以通用修复扩展模板族。

      <row>
        <text color="secondary" size="sm">性价比</text>
        <spacer/>
        **高**
      </row>
      <box height={6} radius="full" background="surface-tertiary"><box height="100%" width="90%" radius="full" background="#16a34a"/></box>
    </box>
  </row>
  <divider/>
  <row align="start">
    <title size="xl" color="secondary">05</title>
    <box flex={1} gap={1}>
      **货架研究拆仓，冻结无证据的学习扩张**

      <caption>建议投入：1–2 人日完成范围隔离</caption>
      固定跨仓资产接口，货架独立发布；暂缓 CNN ×10、基础模型升级及新增模板数量目标。

      <row>
        <text color="secondary" size="sm">性价比</text>
        <spacer/>
        **高**
      </row>
      <box height={6} radius="full" background="surface-tertiary"><box height="100%" width="85%" radius="full" background="#16a34a"/></box>
    </box>
  </row>
  <caption>投入为评审建议预算，非实测工期；性价比为定性判断。</caption>
</box>

## 8. 下一阶段执行边界

按照你此前设定的单次研究迭代不超过八周的治理原则，我建议本轮设置一个更短的四周裁决窗口，不允许无限扩张研究范围。

<box border radius="lg" padding={3} gap={2}>
  <title size="md">四周研究与验收计划</title>
  <svg viewBox="0 0 350 204" width="100%">
    {#each [0,1,2,3] as w}
      <text x={157+w*54} y="15" fontSize="11" textAnchor="middle" fill="currentColor">W{w+1}</text>
      <path d={`M${130+w*54} 25V194`} stroke="currentColor" strokeOpacity=".1"/>
    {/each}
    {#each [
      ["门禁与声明修复",0,1,"#64748b"],
      ["真实数据采集",0,1.5,"#2563eb"],
      ["解析几何基线",0.6,1.6,"#2563eb"],
      ["五类实物制造",0.8,2.9,"#0d9488"],
      ["独立盲测与裁决",2.8,1.2,"#16a34a"],
      ["货架范围隔离",0,0.7,"#64748b"]
    ] as t,i}
      <text x="3" y={42+i*27} fontSize="11" fill="currentColor">{t[0]}</text>
      <rect x={131+t[1]*54} y={30+i*27} width={t[2]*54-2} height="16" rx="3" fill={t[3]}/>
    {/each}
  </svg>
  <caption>并行工作包设计。第四周做路线裁决，不以所有模板修复完成作为结束条件。</caption>
</box>

{@body const checks=["原负探针全部重新执行并有明确预期","SVG/PDF 独立解析与物理尺寸验证","24 件真实实物及刀版真值完成冻结","解析几何与 CNN 同测试集盲测","五类实物裁切折叠与尺寸回测","货架孪生独立发布边界建立"]}
{@body const [done,setDone]=DIL.useState([false,false,false,false,false,false])}
<card gap={3}>
  <row align="center">
    <title size="md">R2 准入验收清单</title>
    <spacer/>
    <caption>{done.filter(Boolean).length}/6</caption>
  </row>
  <box height={6} background="surface-tertiary" radius="full">
    <box height="100%" background="#16a34a" radius="full" width={`${done.filter(Boolean).length/6*100}%`}/>
  </box>
  {#each checks as item,i}
    <checkbox key={i} checked={done[i]} onChange={v=>setDone(old=>old.map((x,j)=>j===i?v:x))}>{item}</checkbox>
  {/each}
  <button block variant="outline" onClick={()=>GenUI.copy(checks.map((x,i)=>(done[i]?"[x] ":"[ ] ")+x).join("\n"))}><icon name="copy" size="sm"/> 复制验收清单</button>
</card>

## 9. 最终路线裁决汇总

| 裁决项 | 最终决定 |
|---|---|
| 参数化制造几何主干 | 保留，继续加强 |
| 现有 100/100 制造验收声明 | 撤回，重新分级验证 |
| 几何覆盖稀疏是误差主因 | 不予确认 |
| CNN 直接回归 | 暂停资源扩张，保留对照 |
| 零训练解析几何 | 提升为 P0 |
| 参数化逆向拟合 | 新增主研究路线 |
| 多视角前馈基础模型 | 降级为研究候选 |
| 合成数据引擎全面升级 | 暂缓，先确定有效变量 |
| 真实物理数据集 | P0，不可再延后 |
| 模板数量扩张 | 暂停 |
| 货架孪生 / ESR | 迁出主仓 |
| PRINT-READY 人工签核原则 | 保留，禁止自动升级 |

---

**一句总评：PhotoDieline 下一阶段不应该继续证明 AI 能生成多少种包装，而应该证明它能从有限的真实观测中，恢复可辨识的制造参数，并让每一份宣称正确的刀版经得起独立数值验证和真实物理折叠。**

<MemoryCite />
