## 二、下一步路线：分级焊接、Manifold，还是并行对照？

**裁决：目前三个选项均不立即启动。若后续恢复专项研究，优先选择 A，但必须修改实验目标。**

我不同意执行侧当前提出的根因假设已经足以指导下一轮修复。

### 2.1 根因假设存在一个数学问题

报告认为：

> 折叠链与封合边共享的交界顶点，导致超过两个面共边，简单顶点合并产生同向共边。

需要区分以下三种完全不同的情况：

<grid columns={3} gap={2}>
  <grid-item>
    <box border radius="md" padding={2}>
      <svg viewBox="0 0 105 100" width="100%">
        {#each Array.from({length:6},(_,i)=>i) as i}
          <path d={`M52 48L${52+40*Math.cos(i*Math.PI/3)} ${48+40*Math.sin(i*Math.PI/3)}L${52+40*Math.cos((i+1)*Math.PI/3)} ${48+40*Math.sin((i+1)*Math.PI/3)}Z`} fill="#dce8f8" stroke="#7895be"/>
        {/each}
        <circle cx="52" cy="48" r="4" fill="#43895f"/>
      </svg>
      **多面共顶点**
      <caption>可能完全合法，不必然产生非流形。</caption>
    </box>
  </grid-item>
  <grid-item>
    <box border radius="md" padding={2}>
      <svg viewBox="0 0 105 100" width="100%">
        <path d="M52 10L8 47L52 88Z" fill="#dce8f8" stroke="#7895be"/>
        <path d="M52 10L97 47L52 88Z" fill="#e6dcf7" stroke="#9b7fc6"/>
        <path d="M52 10L73 39L52 88Z" fill="#efc6bf" stroke="#bc6a5b"/>
        <path d="M52 10V88" stroke="#b95049" strokeWidth="3"/>
      </svg>
      **三面共边**
      <caption>对于流形外壳，属于拓扑缺陷。</caption>
    </box>
  </grid-item>
  <grid-item>
    <box border radius="md" padding={2}>
      <svg viewBox="0 0 105 100" width="100%">
        <path d="M51 10L8 47L51 88Z" fill="#dce8f8" stroke="#7895be"/>
        <path d="M54 10L97 47L54 88Z" fill="#e6dcf7" stroke="#9b7fc6"/>
        <path d="M48 20V75L44 68M58 20V75L54 68" stroke="#b95049" strokeWidth="2.5" fill="none"/>
      </svg>
      **两面同向共边**
      <caption>可能是绕向错误，而非三面共边。</caption>
    </box>
  </grid-item>
</grid>

`dup-directed`、`nonfan` 和 `degenerate-3d` 可能具有共同根因，但不能仅凭它们同时出现就认定因果关系成立。

尤其是退化三角形，值得优先检查是否有同一个三角形的两个原始角点被错误归入了同一个拓扑等价类。

### 2.2 分级焊接并不天然解决问题

如果 FOLD、SEAL、GLUE 使用的是同一组顶点等价约束，并且最终只是通过并查集合并顶点，那么改变这些约束的执行顺序，原则上不会改变最终等价类。

因此：

| 实验路线 | 当前裁决 | 理由 |
|---|---|---|
| A. 分级焊接 | DEFERRED | 可以定位首个错误约束，但单纯改变焊接顺序未必能解决错误 |
| B. Manifold repair | DEFERRED | 尚未证明通用实体重建符合当前包装结构及印刷语义 |
| C. 两者并行 | NOT AUTHORIZED | 当前缺乏足够证据证明两条路线值得同时投入 |

未来若重新启动 A，应将实验命名为：

**`TRIAL-CLOSURE-CONSTRAINT-TRACE`——封合约束逐项追踪实验。**

它的目标不是通过分级焊接碰出一个 PASS，而是定位第一个导致错误拓扑等价类的封合约束。

<box border radius="lg" padding={3} gap={2}>
  <svg viewBox="0 0 340 247" width="100%">
    {#each [{y:5,t:"FOLD 基线",s:"记录面角、边及顶点等价类"},{y:54,t:"逐条加入 SEAL 约束",s:"每次只加入一条明确封合关系"},{y:103,t:"检查拓扑变化",s:"退化 / 重复面 / 边关联数 / link graph"},{y:152,t:"定位首个异常约束",s:"记录涉及面板、角点与错误合并路径"},{y:201,t:"修正结构关系或表达策略",s:"不靠自动补洞掩盖错误"}] as a,i}
      <rect x="30" y={a.y} width="280" height="38" rx="6" fill={i===3?"#f7e3df":"#e7ebf8"} stroke={i===3?"#c07a6c":"#8fa0c9"}/>
      <text x="170" y={a.y+15} fontSize="12" fontWeight="bold" textAnchor="middle" fill={i===3?"#a75549":"#465b86"}>{a.t}</text>
      <text x="170" y={a.y+29} fontSize="10" textAnchor="middle" fill="#63728c">{a.s}</text>
      {#if i<4}<path d={`M170 ${a.y+38}v10m-3 -4l3 4 3-4`} fill="none" stroke="#8493a8"/>{/if}
    {/each}
  </svg>
  <caption>未来恢复专项时的诊断路线。本轮仅归档，不启动。</caption>
</box>

GLUE 默认保持独立结构关系，不纳入主闭壳的顶点合并过程。

只有当结构姿态、封合关系、输入几何均已经确认正确，而剩余问题明确属于成熟几何库擅长处理的实体构建问题时，再启动 Manifold TRIAL。

---

## 三、WP-A3 v1.2 七项任务的最终状态

执行侧报告中有几项将“制品已经产出”与“门禁已经通过”混用，需要在收口时纠正。

| 任务 | 最终状态 | 理由 |
|---|---|---|
| A12-01 部件分离 | ACCEPTED | 已报告独立 prim 生成 |
| A12-02 拓扑复验 | BLOCKED | 六类审计异常尚存 |
| A12-03 胶合关系 | ACCEPTED AS REPORTED | 已登记关系，但未完成独立几何验证 |
| A12-04 UV 映射 | PARTIAL | 角序身份映射成立不等于印刷正确，且存在5处退化 UV |
| A12-05 成品三视图 | PARTIAL | 三视图已生成，但真实成品对照证据未在本次提交中展示 |
| A12-06 规格变体 | FAIL | 三个变体均失败，且存在缺失 st 属性 |
| A12-07 确定性 | PASS AS REPORTED | 已报告确定性成立，需保留具体复现口径 |

### 3.1 三个规格同因失败是重要证据

<card gap={3}>
  <caption>WP-A3 v1.2 规格变体试验</caption>
  {#each [{t:"min",d:"99.4 × 39.8 × 138.5 mm"},{t:"typ",d:"95.5 × 38.2 × 138.6 mm"},{t:"max",d:"154.1 × 61.6 × 214.9 mm"}] as a}
    <row align="center">
      <box flex={1} gap={1}>
        **{a.t}**
        <caption>{a.d}</caption>
      </box>
      <text color="danger" weight="medium">FAIL</text>
    </row>
    <divider/>
  {/each}
  <title size="2xl" tabularNums={true}>0 / 3</title>
  <caption>共同报告：dup-directed 5、nonfan 3、几何退化及边界异常。</caption>
</card>

这种高度一致的异常特征支持公共拓扑编译逻辑存在系统性问题的判断，但尚不足以证明三个变体的首个错误约束完全相同。

不应该再逐规格调整焊接容差。

另外，变体组中 `uv:no-st` 与典型候选中的退化 UV 必须分别登记。如果变体组未携带纹理，仅用于几何诊断，就不能称为完整资产回归测试。

---

## 四、为什么现在必须调整研究重心？

从 R02-A 到 WP-A3 v1.2，我们已经在同一个包装结构家族上经历多轮研究。

继续投入当然有可能最终解决封合问题，但目前需要重新审视它与项目最终目标的关系。

| 研究问题 | 当前战略重要性 |
|---|---|
| 一个砖型包装能否形成严格闭壳 | 局部工程能力 |
| 9,386件历史发行资产究竟是什么表达 | 基础产品事实 |
| 历史三重验证是否对应同一个资产 | 产品可信度 |
| 未见真实商品能否自动生成 | 核心竞争力 |
| 现有资产能否支撑真实零售感知 | 下游商业价值 |
| 能否降低商品数字化生产成本 | 商业可行性 |

**WP-A3 已经充分暴露了编译器的结构表达问题，但继续深挖它，当前的边际研究价值正在下降。**

我们还没有回答更关键的产品问题：现有77个结构家族究竟有多少能够满足真实零售需求，以及现有9,386件资产到底哪些能力已经成立。

因此，下一阶段不是继续围绕单一砖型包装优化，而是进行全局产品事实核查与核心能力评测准备。

## 五、下一阶段资源重新分配

<card gap={3}>
  <caption>建议研究资源分配 · 下一阶段</caption>
  {#each [{t:"WP-V + WP-REP-AUDIT",s:"历史验证与资产表达身份",v:40,c:"#687EC1"},{t:"WP1-v0.2",s:"真实未见商品盲测协议",v:35,c:"#8D79C5"},{t:"ECO-CPG-01",s:"外部合成数据集实物核验",v:20,c:"#6C9A80"},{t:"WP-A3",s:"阻塞归档与研究资产沉淀",v:5,c:"#B0B7C4"}] as a}
    <box gap={1}>
      <row align="center">
        <text weight="medium" size="sm">{a.t}</text>
        <spacer/>
        **{a.v}%**
      </row>
      <box height={12} radius="sm" background="#E5E7EB" clip={true}>
        <box height="100%" width={`${a.v}%`} background={a.c}/>
      </box>
      <caption>{a.s}</caption>
    </box>
  {/each}
</card>

以上为建议分配比例，不是执行侧已经确认的人员或工时安排。

### P0 主线一：WP-V + WP-REP-AUDIT

这是我目前最希望看到的下一份报告。

必须回答：

| 问题 | 必须提交的证据 |
|---|---|
| 9,386件中多少是平板表达？ | 全量三轴及表达分类台账 |
| 历史渲染使用了什么资产？ | 渲染输入路径、版本与哈希 |
| 原版验证器验证了什么？ | 验证器身份、规则、资产哈希及日志 |
| MuJoCo 使用了什么？ | 真实网格、碰撞代理及转换关系 |
| 三重验证是否对应同一商品表达？ | 跨环节证据链 |

这一工作不依赖 aseptic_brick 修复成功，也不应该继续延期。

### P0 主线二：WP1-v0.2

完成上一轮八项 P0 协议整改，尤其是：

- 真实未见商品的抽样与隔离规则。
- 输入不足、结构未知和生成失败的独立分母。
- 端到端交付率及真实商品一致性门禁。
- 规格、外观、物理属性及经济成本的验收规则。

WP1 可以先冻结评测协议，不需要等待全部77个家族修复。

事实上，编译器当前存在的失败也应成为未来 WP1 的真实测量对象，而不是在测试前通过排除问题家族来美化结果。

**但必须明确冻结哪个编译器版本接受评测。协议冻结不自动授权正式实验启动。**

### P1 并行支线：ECO-CPG-01

按此前授权，完成 Neurolabs CPGDet-129 的下载可用性、许可证、图像及标注结构核验。

其价值是研究我们的资产库能否降低真实零售感知的数据建设成本，并解释此前合成数据迁移实验的负结果。

不启动大规模模型训练，不扩大竞品研究范围。

---

## 六、R09-09 正式任务台账

{@body const tasks=[["T01","WP-A3 阻塞归档","冻结 v1.2 制品、失败样本、研究结论及恢复条件"],["T02","WP-REP-AUDIT","9,386件实际资产表达分类与用途核查"],["T03","WP-V","历史验证器及跨环节资产身份追溯"],["T04","WP1-v0.2","八项P0整改后的完整盲测协议"],["T05","ECO-CPG-01","CPGDet-129有限实物核验"]]}
{@body const [done,setDone]=DIL.useState(tasks.map(()=>false))}
<card gap={3}>
  <row align="center">
    **下一阶段执行清单**
    <spacer/>
    <caption>{done.filter(Boolean).length}/5</caption>
  </row>
  {#each tasks as a,i}
    <checkbox checked={done[i]} onChange={v=>setDone(old=>old.map((x,j)=>i===j?v:x))}>
      **{a[0]} · {a[1]}**

      <caption>{a[2]}</caption>
    </checkbox>
    {#if i<4}<divider/>{/if}
  {/each}
  <button block variant="outline" color="secondary" onClick={()=>GenUI.copy(tasks.map((a,i)=>(done[i]?"[x] ":"[ ] ")+a.join(" — ")).join("\n"))}><icon name="copy" size="sm"/> 复制执行任务</button>
</card>

### WP-A3 恢复条件

满足以下任意一项，再申请恢复专项研究：

| 条件 | 恢复理由 |
|---|---|
| WP1 证明砖型封合问题是主要交付瓶颈 | 有明确的业务优先级依据 |
| 发现多个家族共用同一错误拓扑模块 | 修复具有规模化收益 |
| 找到独立成熟实现，可显著降低编译复杂度 | 存在新的技术路径证据 |
| 获得真实成品结构与完整封合设计资料 | 可以解决当前语义不确定性 |

在此之前，不自动启动 WP-A3 v1.3。

---

## 七、最终签核

| 裁决事项 | 最终状态 |
|---|---|
| WP-A3 v1.2 阻塞申报 | ACCEPTED |
| WP-A3 本阶段研究 | CLOSED_WITH_BLOCKER |
| 部件级表达架构 | KEEP |
| 胶板唯一根因假设 | NOT SUPPORTED |
| 分级焊接实验 | DEFERRED |
| Manifold repair | DEFERRED |
| 单家族正确编译闭环 | NOT ACHIEVED |
| WP-V / WP-REP-AUDIT | P0 AUTHORIZED |
| WP1-v0.2 | P0 AUTHORIZED |
| ECO-CPG-01 | PARALLEL AUTHORIZED |
| 批量重编译及发行 | PROHIBITED |

本轮依据提交的 JSON 及阻塞报告进行裁决，未独立执行 `9c227b6` 源码、加载候选 USD 或查看 `three_views.png`。因此不签发制品级独立验收证明。

**R09-08 FINAL VERDICT：CLOSED WITH BLOCKER — SHIFT RESEARCH PRIORITY**

这次应该严格执行我们此前建立的研究治理原则：失败必须沉淀为知识资产，但不要求每一项研究都以技术成功结束。

现在最重要的不是把一个砖型包装继续焊接下去，而是重新建立对整个零售数字资产编译器真实能力的认识。

**下一轮首要送审对象：WP-V + WP-REP-AUDIT 联合报告，以及 WP1-v0.2 冻结候选协议。**