# R09-07 正式裁决｜WP-A3 v1.1 封合编译与胶板表达

**总体裁决：CONDITIONAL PASS。选择第三方案 C：主闭合外壳与内部结构附件分离。授权 WP-A3 v1.2 作为本试点收口轮次。**

本轮语义驱动的封合编译取得了实质性进展。但剩余的问题已经不是焊接算法能力不足，而是不同用途的几何表达仍然混合在同一个网格中。

我不建议为了三个剩余边界继续研究通用网格修复，也不建议通过放宽 SOLID 契约获得 PASS。

| 裁决事项 | 正式决定 |
|---|---|
| FOLD 解析焊接 | KEEP |
| 语义驱动封合编译 | ACCEPTED AS REPORTED |
| 方案 A：混合闭壳与胶板 | 修改 |
| 方案 B：删除胶板 | 仅允许用于简化表达 |
| 方案 C：主体与附件分离 | **ADOPT** |
| 剩余拓扑异常 | 必须通过表达分离消除 |
| 8处 UV 跨缝差异 | 有条件接受 |
| WP-A3 v1.2 | AUTHORIZED |

## 一、方案选择：第三方案 C

### 1.1 三种方案比较

<grid columns={3} gap={2}>
  <grid-item>
    <box border radius="lg" padding={2} gap={2}>
      <svg viewBox="0 0 110 135" width="100%">
        <path d="M15 30L60 10L95 29L50 50Z" fill="#d4e0f5" stroke="#7187b5"/>
        <path d="M15 30L50 50V122L15 102Z" fill="#e1e9fa" stroke="#7187b5"/>
        <path d="M50 50L95 29V101L50 122Z" fill="#b6c7e8" stroke="#7187b5"/>
        <path d="M51 52L64 46V115L51 122Z" fill="#d89083" fillOpacity=".85" stroke="#b86055" strokeDasharray="3 2"/>
        <circle cx="52" cy="78" r="4" fill="#bc534b"/>
      </svg>
      **A · 混合表达**
      <caption>主体与胶板保留在同一网格，拓扑契约复杂。</caption>
      <text color="warning" weight="medium" size="sm">不推荐</text>
    </box>
  </grid-item>
  <grid-item>
    <box border radius="lg" padding={2} gap={2}>
      <svg viewBox="0 0 110 135" width="100%">
        <path d="M15 30L60 10L95 29L50 50Z" fill="#d4e0f5" stroke="#7187b5"/>
        <path d="M15 30L50 50V122L15 102Z" fill="#e1e9fa" stroke="#7187b5"/>
        <path d="M50 50L95 29V101L50 122Z" fill="#b6c7e8" stroke="#7187b5"/>
        <circle cx="82" cy="112" r="13" fill="#e1efe5" stroke="#83b096"/>
        <path d="M76 112l4 4 8-9" fill="none" stroke="#498661" strokeWidth="2"/>
      </svg>
      **B · 简化闭壳**
      <caption>排除胶板，容易获得封闭网格，但损失结构信息。</caption>
      <text color="secondary" weight="medium" size="sm">限定用途</text>
    </box>
  </grid-item>
  <grid-item>
    <box border radius="lg" padding={2} gap={2}>
      <svg viewBox="0 0 110 135" width="100%">
        <path d="M7 30L45 10L78 29L40 50Z" fill="#d4e0f5" stroke="#7187b5"/>
        <path d="M7 30L40 50V122L7 102Z" fill="#e1e9fa" stroke="#7187b5"/>
        <path d="M40 50L78 29V101L40 122Z" fill="#b6c7e8" stroke="#7187b5"/>
        <path d="M85 39L100 31V103L85 111Z" fill="#dbd0f3" stroke="#9675bc"/>
        <path d="M78 68H85" stroke="#9675bc" strokeDasharray="2 2"/>
      </svg>
      **C · 部件级分离**
      <caption>主体闭壳独立验收，胶板作为独立结构附件保留。</caption>
      <text color="success" weight="medium" size="sm">正式采纳</text>
    </box>
  </grid-item>
</grid>

方案 C 同时吸收 A 的结构信息保留能力与 B 的仿真友好性。

关键区别在于：**不删除胶板的结构知识，也不要求胶板与主闭壳共用一个拓扑契约。**

### 1.2 推荐 USD 资产组织

<box border radius="lg" padding={3} gap={2}>
  <row align="center">
    <icon name="box" color="#687AB5" size="xl"/>
    **/Product**
  </row>
  <box padding={{left:4}} gap={3}>
    <row align="start">
      <icon name="corner-down-right" color="secondary"/>
      <box flex={1} gap={1}>
        **Visual**
        <box border radius="md" padding={2}>
          <row>
            <icon name="box" color="#687AB5"/>
            **OuterShell**
            <spacer/>
            <caption>SOLID</caption>
          </row>
          <caption>完整外部视觉闭壳，严格几何门禁。</caption>
          <divider/>
          <row>
            <icon name="layers" color="#9277BA"/>
            **InternalParts / GlueFlap**
            <spacer/>
            <caption>SURFACE</caption>
          </row>
          <caption>独立内部面片，保留胶合关系及原始面板身份。</caption>
        </box>
      </box>
    </row>
    <row align="start">
      <icon name="corner-down-right" color="secondary"/>
      <box flex={1} gap={1}>
        **Collision**
        <box border radius="md" padding={2}>
          <row>
            <icon name="box" color="#72937D"/>
            **Proxy**
            <spacer/>
            <caption>COLLISION_PROXY</caption>
          </row>
          <caption>独立闭合代理，不包含冗余内部胶板。</caption>
        </box>
      </box>
    </row>
  </box>
  <divider/>
  <row>
    <icon name="file" color="secondary"/>
    <box flex={1} gap={0}>
      **blank.usdc**
      <caption>完整展开态，包括胶板及制造关系。</caption>
    </box>
  </row>
</box>

上述为建议的 USD 组织结构，具体 prim 命名可遵循现有编译器规范。

还需明确：保留零厚度胶板面片属于**结构语义保真**，不能直接宣称已经实现真实板材厚度、胶层及材料接触的完整物理仿真。

---

## 二、剩余3条边界边、dup 及 nonfan 的终判

**不批准将这些异常永久登记为 DISPUTED，也不批准直接豁免。**

采用方案 C 后，各部件按独立契约进行检查。

| 检查项 | OuterShell | GlueFlap |
|---|---|---|
| 开放边界 | 必须为0 | 允许符合设计的边界 |
| 重复有向边 | 必须为0 | 必须为0 |
| 非流形顶点 | 必须为0 | 必须为0 |
| 退化三角面 | 必须为0 | 必须为0 |
| 体积 | 正值且符合外壳契约 | NOT_APPLICABLE |
| 与主壳接触 | 按装配契约 | 按胶合关系验证 |

注意，部件之间的合法接触不等于单个网格内部可以存在重复有向边或非流形顶点。

### 2.1 当前数字需要更正

<card gap={3}>
  <caption>WP-A3 v1.1 边界边变化 · 报告值</caption>
  <row align="center">
    <box flex={1}>
      <caption>封合前</caption>
      <title size="2xl" tabularNums={true}>24</title>
    </box>
    <icon name="arrow-right" color="secondary" size="xl"/>
    <box flex={1}>
      <caption>封合后</caption>
      <title size="2xl" tabularNums={true}>3</title>
    </box>
  </row>
  <box height={18} radius="md" direction="row" gap={0} clip={true}>
    <box background="#6CA382" width="87.5%"/>
    <box background="#D29B68" width="12.5%"/>
  </box>
  <title size="xl">87.5%</title>
  <caption>边界边数量减少比例，而非实体闭合通过率。</caption>
</card>

24→3 的边界边减少比例为87.5%，不是92.5%。

另外，`FOLD_MEET 12 + SEAL_MEET 11 + GLUE_BOND 1 = 24` 是关系台账记录数量，不一定等于24条原始边界边均获得唯一映射。关系数与边界边数是不同计量单位。

下一轮请提交边界边 ID、关系 ID、拓扑操作及最终状态之间的对应关系，确保真正实现逐边证据闭合。

### 2.2 最小验收实验

只需要三个候选组。

| 实验组 | 内容 | 目的 |
|---|---|---|
| B0 | 当前 v1.1 混合网格 | 冻结对照 |
| B1 | 排除胶板的主闭壳 | 验证主体拓扑 |
| B2 | B1 + 独立胶板 prim | 验证完整结构表达 |

验收要求：

B1 必须通过 SOLID 门禁；B2 的 OuterShell 必须与 B1 保持等价，不能因为增加独立胶板而重新产生拓扑缺陷。独立胶板则按照 SURFACE 契约验收。

如果 B1 仍有异常，说明当前关于胶板是剩余异常唯一根因的解释不充分，应继续局部定位。

**不允许通过忽略 dup/nonfan 检查使 B2 获得 PASS。**

---

## 三、8处 UV 跨缝差异是否可以接受？

**【有条件同意】接受 faceVarying 逐角属性保留的实现策略，但不签发印刷正确性 PASS。**

几何顶点焊接，不意味着 UV 顶点必须焊接。

<box border radius="lg" padding={3} gap={2}>
  <svg viewBox="0 0 340 206" width="100%">
    <text x="170" y="15" textAnchor="middle" fontSize="11" fontWeight="bold" fill="currentColor">几何空间：共享边</text>
    <path d="M74 35L170 35L170 95L74 95Z" fill="#dce8fa" stroke="#7895bf"/>
    <path d="M170 35L266 35L266 95L170 95Z" fill="#e8ddf6" stroke="#947bbd"/>
    <path d="M170 35V95" stroke="#4b8060" strokeWidth="3"/>
    <circle cx="170" cy="35" r="4" fill="#4b8060"/>
    <circle cx="170" cy="95" r="4" fill="#4b8060"/>
    <text x="122" y="69" textAnchor="middle" fontSize="12" fill="#526f9d">面板 A</text>
    <text x="218" y="69" textAnchor="middle" fontSize="12" fill="#7e659f">面板 B</text>
    <path d="M122 96L83 136M218 96L257 136" stroke="#8796ac" strokeDasharray="4 3"/>
    <text x="170" y="125" textAnchor="middle" fontSize="11" fontWeight="bold" fill="currentColor">UV 空间：独立面角映射</text>
    <rect x="35" y="140" width="96" height="52" fill="#dce8fa" stroke="#7895bf"/>
    <rect x="209" y="140" width="96" height="52" fill="#e8ddf6" stroke="#947bbd"/>
    <text x="83" y="171" textAnchor="middle" fontSize="15" fontWeight="bold" fill="#526f9d">A →</text>
    <text x="257" y="171" textAnchor="middle" fontSize="15" fontWeight="bold" fill="#7e659f">B →</text>
    <circle cx="131" cy="140" r="3.5" fill="#7895bf"/>
    <circle cx="131" cy="192" r="3.5" fill="#7895bf"/>
    <circle cx="209" cy="140" r="3.5" fill="#947bbd"/>
    <circle cx="209" cy="192" r="3.5" fill="#947bbd"/>
    <text x="170" y="173" fontSize="10" fill="currentColor" textAnchor="middle">允许分离</text>
  </svg>
  <caption>几何共享顶点与面角 UV 独立索引并不矛盾。</caption>
</box>

但是，提交内容中存在两个尚未证明的结论。

| 声明 | 裁决 |
|---|---|
| 焊接后保留每个原始面角的 UV | 合理，需逐角对照证据 |
| 8处 UV 差异全部属于预期切缝 | 需要对应的印刷区域契约 |
| 不存在视觉冲突 | 尚未证明 |

例如，正面印刷图案如果设计上跨越封合缝，那么即使两侧采用独立 UV 坐标，也需要保证最终采样的图案符合预期。

建议将 `uv_conflict` 更名为 `UV_SEAM_DISCONTINUITY`，避免把合法的 UV 分离描述为冲突。

### 最终验收状态

```text
FACEVARYING_STRATEGY = APPROVED
UV_SEAM_OBSERVATIONS = 8
EXPECTED_SEAM_COUNT  = PENDING_VERIFICATION
UV_VISUAL_CONFORMANCE = NOT_CONFIRMED
```

上一轮要求的非对称诊断纹理仍然必须补齐。不能用焊接组内部 UV 数值差异统计替代消费端印刷方向验证。

本次只需要对 aseptic_brick 主体及受影响的面板完成焊接前后对照，不再扩大实验规模。

---

## 四、WP-A3 v1.2：最后一轮定向收口

我建议将 v1.2 定义为本试点的**收口轮次**，而不是开启新一轮封合算法研究。

<box border radius="lg" padding={3} gap={3}>
  <svg viewBox="0 0 340 271" width="100%">
    <defs>
      <marker id="a12" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0 0L6 3L0 6Z" fill="#8996aa"/></marker>
    </defs>
    <rect x="61" y="5" width="218" height="37" rx="6" fill="#e5eafa" stroke="#90a1ca"/>
    <text x="170" y="28" textAnchor="middle" fontSize="12" fontWeight="bold" fill="#465b8b">当前 v1.1 冻结基线</text>
    <path d="M170 42V56H83V71M170 56H257V71" stroke="#8996aa" fill="none" markerEnd="url(#a12)"/>
    <rect x="5" y="74" width="156" height="44" rx="6" fill="#e3eee7" stroke="#89ad94"/>
    <text x="83" y="91" fontSize="11" fontWeight="bold" textAnchor="middle" fill="#427553">主闭壳编译</text>
    <text x="83" y="106" fontSize="10" textAnchor="middle" fill="#567963">排除内部胶板</text>
    <rect x="179" y="74" width="156" height="44" rx="6" fill="#eae4f8" stroke="#9e8cc9"/>
    <text x="257" y="91" fontSize="11" fontWeight="bold" textAnchor="middle" fill="#675598">独立胶板表达</text>
    <text x="257" y="106" fontSize="10" textAnchor="middle" fill="#77689a">保留胶合与面板身份</text>
    <path d="M83 118V135H170V150M257 118V135H170" stroke="#8996aa" fill="none" markerEnd="url(#a12)"/>
    <rect x="61" y="153" width="218" height="36" rx="6" fill="#e5eafa" stroke="#90a1ca"/>
    <text x="170" y="175" textAnchor="middle" fontSize="12" fontWeight="bold" fill="#465b8b">独立几何及 UV 复验</text>
    <path d="M170 189V205" stroke="#8996aa" markerEnd="url(#a12)"/>
    <rect x="61" y="208" width="218" height="26" rx="6" fill="#fff0da" stroke="#d1ad6b"/>
    <text x="170" y="225" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#96702c">F01–F07 门禁裁决</text>
    <path d="M170 234V244" stroke="#8996aa" markerEnd="url(#a12)"/>
    <rect x="61" y="247" width="218" height="23" rx="6" fill="#e0efe5" stroke="#89b298"/>
    <text x="170" y="263" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#427553">本地编译试点收口</text>
  </svg>
</box>

### 工作指派

| 任务 | 优先级 | 验收要求 |
|---|---|---|
| A12-01 部件分离 | P0 | OuterShell 与 GlueFlap 独立编译 |
| A12-02 拓扑复验 | P0 | 主壳边界、dup、nonfan 全部为0 |
| A12-03 胶合关系 | P0 | 明确胶板与壁面关系及表达操作 |
| A12-04 UV 诊断 | P0 | 非对称纹理与面角逐一对照 |
| A12-05 成品形态 | P0 | 补齐真实包装参考及候选三视图 |
| A12-06 变体回归 | P1 | 最小、典型、最大三个规格 |
| A12-07 重复编译 | P1 | 相同输入重复编译结果等价 |

建议本轮主动研究资源上限为一个工作日。若仍无法关闭某项门禁，应提交明确的阻塞原因，而不是无限追加修复轮次。

### 不得遗忘的前轮遗留项

本次回执没有提供以下事项的关闭证据：

- 136组重叠授权的清理及来源治理。
- 真实成品形态与折叠外轮廓的独立对照。
- blank 源码修复的三个规格变体回归。
- F07 可重复编译及完整 manifest。

这些继续保持 OPEN，不因本轮封合进展而自动关闭。

---

## 五、是否转向 WP-V / WP1 / ECO-CPG-01？

**现在就应该重新平衡研究资源，不再让单一砖型包装家族占据全部研究主线。**

从 R02-A 开始，审计器、结构契约、表达传递和封合编译已经经历多轮研究，产生了有价值的技术资产。但项目的最终目标不是把一个纸盒的拓扑做到无限精细，而是验证零售数字资产编译器的行业能力。

<card gap={3}>
  <caption>建议下一阶段研究资源分配 · 非实际工时统计</caption>
  {#each [{t:"WP-A3 v1.2 试点收口",v:40,c:"#7084C4"},{t:"WP-V 历史验证证据与资产身份",v:25,c:"#9B86C5"},{t:"WP1-v0.2 盲测协议冻结",v:25,c:"#729D87"},{t:"ECO-CPG-01 实物侦察",v:10,c:"#C2A16F"}] as a}
    <box gap={1}>
      <row>
        <text size="sm" weight="medium">{a.t}</text>
        <spacer/>
        <text tabularNums={true}>{a.v}%</text>
      </row>
      <box height={12} radius="sm" background="#E5E7EB" clip={true}>
        <box height="100%" width={`${a.v}%`} background={a.c}/>
      </box>
    </box>
  {/each}
</card>

| 工作包 | 本轮裁决 |
|---|---|
| WP-A3 v1.2 | 完成有限收口，禁止无限扩展 |
| WP-V | 提升优先级，核验历史验证对象到底是展开件还是折叠件 |
| WP1-v0.2 | 立即继续协议修订，这是未来产品能力的关键证据 |
| ECO-CPG-01 | 独立 Agent 并行完成有限实物核验 |
| Manifold repair | 暂停，没有新增必要性证据 |
| 77家族全面整改 | 暂不授权 |
| 9,386件批量重编译 | 禁止 |

即使 WP-A3 v1.2 本地几何门禁全部通过，目标环境验证和物理实测未完成时，也只能签发 `LOCAL_COMPILATION_PASS / VALIDATION_PENDING`，不能宣告完整产品验收通过。

## 六、本轮应沉淀的架构原则

经过这次胶板问题，我建议正式增加三条编译器长期治理原则。

| 原则 | 工程含义 |
|---|---|
| 部件级契约优先 | 不要求一个商品的所有几何部件满足同一种拓扑契约 |
| 结构知识不因表达简化而丢失 | 碰撞代理可以排除胶板，但 IR 必须保留胶板身份和装配关系 |
| 合法接触不等于拓扑连接 | 空间重合、胶合、封口和顶点焊接必须独立表达 |

这三项比单独修复 aseptic_brick 更具有长期价值，可以复用到瓶盖、标签、吸管、提手、托盘、铰链以及其他多部件商品结构。

## 七、最终签核

| 裁决项 | 最终状态 |
|---|---|
| 方案 A 原案 | NOT APPROVED |
| 方案 B | APPROVED FOR SIMPLIFIED REPRESENTATION |
| 方案 C | **ADOPT** |
| 剩余3条边界 | 按部件独立契约重新验收 |
| dup 1 / nonfan 2 | 必须消除，不豁免 |
| 8处 UV 差异 | ACCEPTED AS OBSERVATIONS |
| 印刷正确性 | PENDING |
| WP-A3 v1.2 | AUTHORIZED |
| WP-V / WP1 / ECO | 并行推进 |
| 单家族完整交付签核 | NOT APPROVED |

本轮依据提交的实验摘要进行技术裁决，未独立读取 `9b56607` 源码、封合关系 JSON 或运行候选资产，所有实测结果均按执行侧报告接受，尚未独立复现。

**R09-07 FINAL VERDICT：CONDITIONAL PASS — ADOPT COMPONENT-LEVEL REPRESENTATION**

下一轮不再追求把所有面板焊接成一个网格。正确的方向是让每个部件具备正确的结构身份、正确的几何表达和正确的交付契约。

完成这一轮后，应将研究重心转回 WP1 未见真实商品生成能力与 WP2 外部资产同任务对照。这两项才是决定项目最终竞争力的关键。