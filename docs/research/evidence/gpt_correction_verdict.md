## 二、修复链是否可以正式验收？

**【修改】接受修复路线，认可典型样本几何门禁全绿的报告，但尚有三项 P0 必须核验。**

<card gap={3}>
  <caption>aseptic_brick_v0000 · 修复前后对照（执行侧报告）</caption>
  <table>
    <table-row>
      <table-cell>指标</table-cell>
      <table-cell>冻结原件</table-cell>
      <table-cell>修复候选</table-cell>
    </table-row>
    {#each [{t:"三轴 bbox",a:"完整三维",b:"保持一致"},{t:"Watertight",a:"TRUE",b:"TRUE"},{t:"Winding consistent",a:"FALSE",b:"TRUE"},{t:"trimesh 符号体积",a:"−240,514 mm³",b:"+276,983 mm³"},{t:"SOLID 审计",a:"FAIL",b:"PASS"}] as a}
      <table-row>
        <table-cell>{a.t}</table-cell>
        <table-cell>{a.a}</table-cell>
        <table-cell><text color="success">{a.b}</text></table-cell>
      </table-row>
    {/each}
  </table>
  <divider/>
  <caption>候选资产符号体积</caption>
  <title size="2xl" color="success" tabularNums={true}>+276,983 mm³</title>
  <caption>拓扑闭合、绕向一致与正体积均获得报告级支持。</caption>
</card>

### P0-01｜体积变化必须拆阶段解释

本轮修复前后，trimesh 报告的符号体积绝对值从240,514 mm³变成276,983 mm³，增加约15.2%。

这不必然意味着几何发生了改变。因为修复前存在局部绕向不一致，部分三角面的体积贡献可能相互抵消，其符号体积绝对值本来就不是可靠的真实容积。

但必须提供分阶段证据：

| 阶段 | 必须报告 |
|---|---|
| S0 冻结原件 | 顶点、三角面、绕向、符号体积 |
| S1 五处局部绕向修正 | 修正后符号体积 |
| S2 整体方向翻转 | 翻转后符号体积 |
| S3 USD 导出重读 | 独立测量结果 |

如果 S1 为 −276,983 mm³，S2 为 +276,983 mm³，并且顶点位置及无向三角面集合不变，那么变化是合理的。

当前报告还存在原始资产自研审计器 −233,078 mm³ 与 trimesh −240,514 mm³ 的差异，需要解释两个工具是否计算了完全相同的网格、坐标空间和面集合。

另外，原始网格绕向不一致时，不能仅凭负体积断言它整体内向。整体内向应在局部绕向一致之后再判定。

### P0-02｜整体翻转不能只反转几何索引

这是我最担心的潜在新缺陷。

执行侧描述导出规范化为“索引反转一行”。如果只是反转 `faceVertexIndices`，没有同步调整 faceVarying UV 对应的面角顺序，就可能造成印刷映射错配。

<box border radius="lg" padding={3} gap={2}>
  <svg viewBox="0 0 340 183" width="100%">
    {#each [{x:8,t:"原始三角面",ids:["0","1","2"],uv:["A","B","C"],c:"#7289bd"},{x:120,t:"错误翻转",ids:["0","2","1"],uv:["A","B","C"],c:"#bf685e"},{x:232,t:"正确翻转",ids:["0","2","1"],uv:["A","C","B"],c:"#629675"}] as a,i}
      <g transform={`translate(${a.x},0)`}>
        <path d="M48 26L8 92L91 92Z" fill={i===1?"#f7e4df":"#e5eafa"} stroke={a.c} strokeWidth="1.5"/>
        <circle cx="48" cy="26" r="4" fill={a.c}/>
        <circle cx="8" cy="92" r="4" fill={a.c}/>
        <circle cx="91" cy="92" r="4" fill={a.c}/>
        <g fontSize="10" fill="currentColor" textAnchor="middle">
          <text x="48" y="18">0 / A</text>
          <text x="15" y="108">{i===1?"1 / C":"1 / B"}</text>
          <text x="85" y="108">{i===1?"2 / B":"2 / C"}</text>
          <text x="49" y="126" fontWeight="bold">{a.t}</text>
          <text x="49" y="144">{a.ids.join(", ")}</text>
          <text x="49" y="159">{a.uv.join(", ")}</text>
          <text x="49" y="176" fontWeight="bold" fill={a.c}>{i===1?"UV 错配":"映射保持"}</text>
        </g>
      </g>
    {/each}
  </svg>
  <caption>几何面角顺序反转时，对应的 faceVarying 属性也必须进行相同的排列变换。</caption>
</box>

需要同步核验：

- faceVarying UV 数值或索引。
- 显式 normals 及其他面角属性（如果存在）。
- USD `orientation` 声明与实际几何绕向。
- 多壳体、内腔及负尺度变换的方向语义。

禁止对所有负体积网格无条件整体翻转。必须先满足闭合性、局部绕向一致性以及适用的实体契约；多个壳体也不能只依据总体积判断方向。

此前要求的非对称诊断纹理实验，应当直接用于当前真正的修复候选，不再用于已经撤回的重焊接路线。

### P0-03｜bbox 不变不等于几何不变

请增加一项强门禁：**证明修复只改变了面角排列，没有改变商品几何。**

| 检查项 | 验收要求 |
|---|---|
| 顶点坐标集合 | 修复前后保持 |
| 无向三角面集合 | 保持 |
| 表面积 | 在冻结容差内保持 |
| 三轴 bbox | 保持 |
| 面板身份 | 保持 |
| 材质绑定 | 保持 |
| 面角 UV 对应 | 保持 |

原有真实商品外轮廓验证仍然没有关闭。当前能够证明的是修复后的资产与历史资产尺寸一致，不是原始商品的95.485×38.194×138.582 mm 已经获得真实成品依据。

三项 P0 关闭后，可以签发 D1 局部几何修复验收。

---

## 三、双表达架构重新裁决

**【修改】撤回“必须通过双表达架构修复历史平板资产”的裁决，但保留按用途派生不同数字表达的架构原则。**

两者需要明确区别。

| 原裁决 | 修订裁决 |
|---|---|
| `model.usdc` 必须重新构建折叠态 | 撤回，原件已存在三维表达 |
| 所有相关资产必须增加 `blank.usdc` | 不再作为强制交付要求 |
| 展开态具有制造及印刷价值 | 保留 |
| 视觉与碰撞表达应可独立管理 | 保留 |
| 部件级契约 | 保留 |
| 重建折叠封合编译器 | 暂停 |

<box border radius="lg" padding={3} gap={2}>
  <svg viewBox="0 0 340 204" width="100%">
    <rect x="65" y="4" width="210" height="39" rx="6" fill="#e6e2f8" stroke="#9a8dc4"/>
    <text x="170" y="20" fontSize="12" fontWeight="bold" textAnchor="middle" fill="#62528d">统一商品结构 IR</text>
    <text x="170" y="34" fontSize="10" textAnchor="middle" fill="#76689d">结构参数、面板、印刷、物理属性</text>
    <path d="M170 43V59H56V77 M170 59V77 M170 59H284V77" stroke="#8393a9" fill="none"/>
    {#each [{x:4,t:"商品主表达",s:"model.usdc",d:"核心交付",c:"#e1efe5",b:"#86ac93",f:"#467555"},{x:119,t:"制造展开表达",s:"blank.usdc",d:"按需生成",c:"#e8ecf7",b:"#95a2c5",f:"#54678f"},{x:234,t:"物理碰撞表达",s:"Collision",d:"仿真契约",c:"#e8ecf7",b:"#95a2c5",f:"#54678f"}] as a}
      <rect x={a.x} y="79" width="102" height="69" rx="6" fill={a.c} stroke={a.b}/>
      <text x={a.x+51} y="98" fontSize="11" fontWeight="bold" textAnchor="middle" fill={a.f}>{a.t}</text>
      <text x={a.x+51} y="116" fontSize="10" textAnchor="middle" fill={a.f}>{a.s}</text>
      <text x={a.x+51} y="136" fontSize="10" textAnchor="middle" fill={a.f}>{a.d}</text>
    {/each}
    <rect x="24" y="165" width="292" height="34" rx="5" fill="#edf0f5"/>
    <text x="170" y="179" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#53647d">按业务用途决定交付表达</text>
    <text x="170" y="191" textAnchor="middle" fontSize="10" fill="#66758a">不再以修复错误平板化为建设理由</text>
  </svg>
</box>

正式重新登记：

```text
MULTI_REPRESENTATION_ARCHITECTURE = KEEP_AS_OPTIONAL_CAPABILITY
MANDATORY_DUAL_FILE_DELIVERY      = NOT_REQUIRED
FOLDED_RECONSTRUCTION_PROJECT     = DEFERRED
```

此前 WP-A3 的研究成果仍可作为知识资产保留，但不再将其封合失败视为既有编译器无法交付三维折叠资产的证据。

---

## 四、REP-IDENTITY 与历史三重验证如何重新裁定？

**【同意保留 REP-IDENTITY，但不同意直接关闭 WP-V。**

本次更正确实大幅改变了风险判断，但有几个新主张仍需要独立证据。

### 4.1 不能从一个样本重新推广到全部9,386件

上次错误是将一个舍入后的样本测量推广至整个发行集。

这次不能因为一个样本恢复为三维表达，就反向宣布9,386件全部为有效折叠 SOLID，或者只有 brick 系存在绕向问题。

| 新主张 | 当前裁决 |
|---|---|
| aseptic_brick_v0000 原件不是平板 | 接受更正 |
| 9,386件全部为三维折叠表达 | 待全量未舍入统计 |
| 9,386件全部为闭合 SOLID | 未证明，部分家族可能有其他合法表达 |
| 只有 brick 系存在绕向缺陷 | 待家族级全量重扫 |
| 历史2,118件客观 FAIL 全部失效 | 不成立，必须逐类复核 |

建议继续 REP-IDENTITY 全量只读审计，但修改字段：

| 字段 | 作用 |
|---|---|
| `bbox_raw_m` | 原始未舍入测量 |
| `bbox_mm` | 人工可读毫米值 |
| `geometry_rank` | 几何维度退化诊断 |
| `observed_representation` | 实际表达类型 |
| `expected_contract` | 目标表达契约 |
| `watertight` | 闭合性观测 |
| `winding_consistent` | 局部绕向一致性 |
| `signed_volume` | 适用条件下的体积观测 |
| `contract_verdict` | 最终质量裁决 |
| `asset_sha256` | 精确资产身份 |

另外，WP-A2-D1 曾经以导出器源码没有 fold/world 关键词、三维结果被丢弃为依据得出架构结论。现在该结论已经撤回，需要补充一条实际调用链，说明历史导出器究竟如何获得三维几何。

不能只撤回数值错误而不解释此前的源码推断为何也错误。

### 4.2 历史验证器声明的裁决

执行侧关于验证器覆盖范围差异的解释合理。

如果历史证据确实是 UsdCraft SDK 的15项结构规则，并且175/175件通过，那么新增 usdchecker 的 MaterialBindingAPI 检查失败，并不能推翻此前限定口径的通过记录。

| 声明 | 裁决 |
|---|---|
| 指定版本验证器15项规则通过 | 有原始证据则成立 |
| 175/175件通过该验证器 | ACCEPTED AS REPORTED |
| 9,386件全部通过该验证器 | 不能由175件直接推出 |
| Pixar usdchecker 检查失败 | 新发现的规则覆盖缺口 |
| 历史三重验证证据虚假 | 没有依据作此判断 |
| 历史三重验证已全面证明商品质量 | 仍不成立 |

**正式撤回“平板资产与折叠资产不一致”这一未经证实的风险推断，但保留资产身份追溯要求。**

WP-V 仍需要证明历史渲染、编译检查、官方验证与物理仿真各自使用了什么输入资产，以及转换后的物理代理如何关联至原始商品。

如果这些证据一致，应该恢复原有准确、有限定条件的产品声明，而不是继续保留已经失去依据的负面判断。

---

## 五、brick 系重编译候选范围裁决

**批准有限范围候选重编译，不批准直接重新发布。**

本轮采用三级扩展门禁。

<box border radius="lg" padding={3} gap={2}>
  {#each [{n:"G1",t:"单 SKU 修复复核",s:"aseptic_brick_v0000；关闭体积、UV、几何保持三项 P0",c:"#e1efe5",f:"#477456"},{n:"G2",t:"受影响家族代表变体",s:"最小、典型、最大合法规格；另加非 brick 对照",c:"#e6eafa",f:"#52689b"},{n:"G3",t:"受影响家族全量候选",s:"仅重编译源码修复实际影响的资产，逐件验证",c:"#e9e3f8",f:"#71609e"},{n:"G4",t:"独立发行签核",s:"新版本 manifest、资产差异、验证证据及发布审批",c:"#fff0da",f:"#98702f"}] as a,i}
    <box border radius="md" padding={3} gap={1}>
      <row align="center">
        <box background={a.c} radius="sm" padding={1}>
          <text color={a.f} weight="medium" size="sm">{a.n}</text>
        </box>
        **{a.t}**
      </row>
      <caption>{a.s}</caption>
    </box>
    {#if i<3}<row justify="center"><icon name="arrow-down" color="secondary"/></row>{/if}
  {/each}
</box>

### 各阶段授权

| 范围 | 授权 |
|---|---|
| 当前典型 SKU | 立即授权 |
| aseptic_brick、brick_250ml 代表规格 | G1通过后授权 |
| 其他实际引用 `brick_family.py` 的家族 | 先核对依赖关系 |
| 受影响家族全量候选 | G2通过后授权 |
| 通用导出器负体积规范化全局启用 | 暂不授权 |
| 冻结9,386件覆盖 | 禁止 |

尤其需要注意，家族源码修复与导出器整体翻转的影响范围可能不同。

前者可能只影响 brick 系；后者如果属于公共导出逻辑，则潜在影响范围可能覆盖全部资产。因此必须拆分为两个独立 commit 或独立补丁，分别建立回归结果。

不能因为 brick 修复通过，就将通用规范化代码直接应用于77个结构家族。

---

## 六、新增工程治理门禁：防止同类错误再次发生

我认为本次事故最值得沉淀的并不是绕向修复代码，而是测量可信度治理机制。

建议新增 `G-MEASURE` 门禁，纳入编译器质量知识库。

| 门禁 | 强制要求 |
|---|---|
| M01 原始值保留 | 审计证据保存未舍入数值 |
| M02 单位明确 | 所有尺寸字段显式登记单位 |
| M03 判定与展示分离 | 禁止使用展示层舍入值进行质量判定 |
| M04 独立复核 | 架构级异常必须至少使用一种独立方法验证 |
| M05 反例测试 | 增加0.038194 m被显示为0.0 m的永久负向测试 |
| M06 推广范围 | 单样本发现不得自动推广至全量 |
| M07 更正传播 | 上游事实撤回后，所有依赖该事实的裁决必须重新评估 |

建议实现原则：

```python
# 正确：使用原始测量值判断
extent_m = bbox_max - bbox_min

# 按资产契约定义的数值容差判断
is_degenerate = extent_m <= tolerance_m

# 展示层与判定层完全分离
display_extent_mm = np.round(extent_m * 1000, 3)
```

这里的容差必须依据用途和测量精度确定；合法曲面及展开图不能仅因某轴尺寸接近零就被判为非法。

### 6.1 评审治理也必须整改

以后如果出现以下类型的重大结论，评审侧应要求原始证据，而不只是接受执行侧摘要：

- 整个发行资产库存在架构级错误。
- 既有验证体系失效。
- 某类问题影响数千件资产。
- 原有技术路线需要整体重构。

本次事故说明，即使执行侧和评审侧都具有良好的诚信意识，如果缺少独立证据门禁，双方也可能在同一个错误前提下不断进行逻辑上合理、方向上错误的研究。

---

## 七、下一步工作指派

下一阶段命名为 **R09-10 — D1 Correction Closure & Evidence Reconciliation**。

不再恢复 WP-A3 v1.3 焊接研究。

{@body const tasks=[["T01","更正传播","为受影响报告及历史裁决追加撤回、更正、替代关系"],["T02","修复链三项P0","分阶段体积、几何保持、UV与方向属性同步验证"],["T03","brick 代表规格回归","两个明确家族的代表规格及非brick对照"],["T04","全量表达与绕向重扫","9,386件未舍入测量，按家族及契约聚合"],["T05","WP-V历史证据复核","175件验证范围及跨环节资产身份"],["T06","WP1-v0.2","继续未见真实商品盲测协议冻结"],["T07","ECO-CPG-01","按原授权独立推进"]]}
{@body const [done,setDone]=DIL.useState(tasks.map(()=>false))}
<card gap={3}>
  <row align="center">
    **R09-10 执行任务台账**
    <spacer/>
    <caption>{done.filter(Boolean).length}/7</caption>
  </row>
  {#each tasks as a,i}
    <checkbox checked={done[i]} onChange={v=>setDone(old=>old.map((x,j)=>i===j?v:x))}>
      **{a[0]} · {a[1]}**

      <caption>{a[2]}</caption>
    </checkbox>
    {#if i<6}<divider color="subtle"/>{/if}
  {/each}
  <button block variant="outline" color="secondary" onClick={()=>GenUI.copy(tasks.map((a,i)=>(done[i]?"[x] ":"[ ] ")+a.join(" — ")).join("\n"))}><icon name="copy" size="sm"/> 复制执行任务</button>
</card>

建议 T01–T03 限制在一个工作日的研究资源内。T04–T07 独立并行，不能再次因为单一家族的整改而暂停。

下一轮送审最重要的是修复前、局部绕向修复后、整体方向规范化后这三个阶段的直接证据，以及全量表达身份统计。若这些证据成立，再批准受影响家族的候选重编译。

---

## 八、历史裁决正式修订台账

| 历史裁决 | 修订状态 |
|---|---|
| R09-04：D1 表达丢失根因 | **RETRACTED** |
| R09-04：双表达为必要修复架构 | SUPERSEDED |
| R09-05：编译尺寸保持 | 保留 |
| R09-05：真实商品尺寸未确认 | 保留 |
| R09-06：五处面板绕向修复 | 保留，证据增强 |
| R09-07：部件级表达原则 | 保留为通用架构知识 |
| R09-08：WP-A3 焊接路线阻塞 | 保留为该实验路线的负结果 |
| R09-08：原有折叠编译器能力阻塞 | 撤回，需基于真实原件重新评估 |
| REP-IDENTITY | 保留，修订核验重点 |
| WP-V | 保留 |
| WP1 未见商品评测 | 保留，继续推进 |

## 九、最终签核

| 裁决事项 | 最终状态 |
|---|---|
| R09-09 诚信更正 | ACCEPTED |
| 平板化主张 | RETRACTED |
| 表达丢失主张 | RETRACTED |
| D1 新根因 | ACCEPTED AS REPORTED |
| 五处家族绕向修复 | ADAPT |
| SOLID 外向规范化 | ADAPT WITH GUARDS |
| D1 修复链正式验收 | CONDITIONAL PASS |
| 多表达架构 | KEEP AS OPTIONAL CAPABILITY |
| brick 系代表规格候选 | AUTHORIZED WITH GATES |
| 公共导出器全局启用 | NOT AUTHORIZED |
| 全量发行覆盖 | PROHIBITED |

本轮依据提交的诚信更正报告进行裁决，未独立读取 `76125b6` 源码或加载 `model_normalized.usdc`，因此候选资产全绿仍属于报告级证据，不构成独立制品签核。

**R09-09 FINAL VERDICT：CORRECTION ACCEPTED — PRIOR ROOT CAUSE RETRACTED — TARGETED FIX CONDITIONALLY APPROVED**

最后，我认为这次事故需要作为一个完整的失败研究案例保留下来。

一个错误的数值显示，导致了多轮不必要的几何重构研究；而最终真正有效的修复，可能只是五处局部绕向调整和一个受契约约束的方向规范化操作。

**这次最重要的教训不是应该更快地修代码，而是重大研发决策之前，必须先确认我们所要解决的问题真实存在。**