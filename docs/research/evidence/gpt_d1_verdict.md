### 1.1 新发现：折叠几何的尺寸尚未证明正确

报告中的数字值得进一步核验。

| 维度 | 输入规格 | 候选折叠资产 bbox | 差值 |
|---|---:|---:|---:|
| 宽 W | 57.3 mm | 95.5 mm | +38.2 mm |
| 深 D | 38.2 mm | 38.2 mm | 0 |
| 高 Hb + hr | 126.6 mm | 138.6 mm | +12.0 mm |

如果 Hb + hr 对应目标商品总高，那么候选资产的宽度增加了66.7%，高度增加了9.5%。

这些差值可能来自未完全折叠的翻板、胶板、底部结构，或者参数定义与整体包围盒的差异。但当前证据不足以认定是哪一种。

特别是：

- 宽度增量恰好等于 D。
- 高度增量恰好等于 hr。

这种关系值得优先检查折叠角度、封口面板以及底部翻板的最终姿态。

**不能把 Y 从0恢复到38.2 mm，就认定折叠几何已经正确。**

因此，D1 的表达丢失根因可以接受，但报告中“生成端全程正确”的表述需要撤回，改为：

> 生成端已经产生非退化的三维折叠几何，但其最终形态、尺寸及封合状态尚未验收。

此外，上一轮要求六件资产逐阶段证据，本轮正文只展示了一个 SKU 的完整快照。其余样本需要在证据台账中补齐，不必重新启动研究。

---

## 二、根因能否推广至全部9,386件？

**【修改】同意将其升级为系统性架构议题，不同意未经核验就宣布全部9,386件资产错误。**

必须区分以下三个命题。

| 命题 | 当前裁决 |
|---|---|
| 9,386件资产共用同一导出路径 | 待源码调用关系核验 |
| 9,386件最终 model.usdc 均为平板表达 | 待全量资产统计核验 |
| 9,386件均不满足可仿真商品交付契约 | 待表达用途及产品定义核验 |

同一导出函数不必然意味着所有分支、输入和最终输出完全相同。

但如果执行侧的判断经过验证属实，那么问题将非常严重。

<box border radius="lg" padding={3} gap={2}>
  <grid columns={2} gap={2}>
    <grid-item>
      <box gap={1}>
        <svg viewBox="0 0 155 140" width="100%">
          {#each [{x:15,y:48,w:35,h:65},{x:50,y:48,w:25,h:65},{x:75,y:48,w:35,h:65},{x:110,y:48,w:25,h:65},{x:15,y:25,w:35,h:23},{x:75,y:25,w:35,h:23},{x:15,y:113,w:35,h:20},{x:75,y:113,w:35,h:20}] as p,i}
            <rect x={p.x} y={p.y} width={p.w} height={p.h} fill={i%2===0?"#d6e4f8":"#e5def8"} stroke="#7788bb"/>
          {/each}
          <path d="M50 48V113M75 48V113M110 48V113M15 48H50M75 48H110" stroke="#7683af" strokeDasharray="3 3"/>
          <text x="32" y="80" fontSize="9" textAnchor="middle" fill="#5b6f9f">PRINT</text>
          <text x="92" y="80" fontSize="9" textAnchor="middle" fill="#5b6f9f">PRINT</text>
        </svg>
        **FLAT_PATTERN**
        <caption>展开、刀版、印刷及制造表达</caption>
      </box>
    </grid-item>
    <grid-item>
      <box gap={1}>
        <svg viewBox="0 0 155 140" width="100%">
          <path d="M38 30L83 13L119 32L73 50Z" fill="#d5ddf8" stroke="#7181b8"/>
          <path d="M38 30L73 50V130L38 108Z" fill="#e2e7fa" stroke="#7181b8"/>
          <path d="M73 50L119 32V112L73 130Z" fill="#aebfe7" stroke="#7181b8"/>
          <path d="M38 48L73 68V96L38 76Z" fill="#7c94d2"/>
          <path d="M73 68L119 50V78L73 96Z" fill="#647cbf"/>
          <text x="55" y="77" fontSize="8" fill="#fff" textAnchor="middle" transform="rotate(29 55 77)">PRINT</text>
        </svg>
        **FOLDED_PRODUCT**
        <caption>货架、展示、感知及物理仿真表达</caption>
      </box>
    </grid-item>
  </grid>
  <divider/>
  两种表达都有价值，但不能互相替代。
</box>

### 2.1 新增 P0：全量表达身份审计

直接利用已有9,386件全量扫描结果，不重新渲染，不重新编译。

增加以下字段：

| 字段 | 用途 |
|---|---|
| family_id | 结构家族身份 |
| exporter_entry | 实际导出入口 |
| exporter_branch | 实际导出分支 |
| bbox_xyz_local | 局部空间包围盒 |
| bbox_xyz_world | 世界空间包围盒 |
| planar_geometry | 是否为平面几何 |
| declared_representation | 声明的表达类型 |
| observed_representation | 实际观测表达类型 |
| intended_use | 设计交付用途 |
| representation_match | 表达是否符合用途 |

最终必须提供按家族汇总的数量表，而不是只给出“同构”的文字结论。

### 2.2 复核既有质量证据的资产身份

这是本轮另一个必须追查的问题。

过去的渲染、USD 验证、物理仿真是否使用的是同一个资产？

| 历史证据 | 必须追溯 |
|---|---|
| 商品棚拍渲染 | 使用 fold world、Blender 网格还是最终 model.usdc？ |
| USD 验证器 | 实际验证的是展开件还是折叠件？ |
| MuJoCo 仿真 | 使用真实包装网格还是独立生成的代理体？ |
| Pack10K 对照实验 | 评分对象与最终发行资产是否一致？ |

如果不同环节使用了不同表达，那么这些实验结果可能各自成立，但不能共同证明同一个发行资产已经通过三重验证。

我建议将这个问题命名为：

**`P0-REP-IDENTITY：跨验证环节资产表达身份一致性`。**

并入现有 WP-V 验证器追溯任务，不另建大型工作包。

在证据核清前，既有9,386件冻结集继续保留，但暂停将其整体描述为已经验证的折叠商品仿真资产库。

---

## 三、修复路线正式裁决

执行侧提出的 A、B、C 实际上不是三个互斥选项。

C 是产品与架构决策；A、B 是该架构下的几何实现选择。

| 路线 | 层次 | 裁决 |
|---|---|---|
| A：IR 拓扑驱动解析焊接 | 编译算法 | TRIAL，优先研究 |
| B：trimesh / Manifold | 几何基础设施 | TRIAL，限定职责 |
| C：双表达架构 | 产品与输出契约 | **ADOPT** |

### 3.1 路线 C：正式采纳双表达架构

但我建议对方案做一项重要扩展：不要把“折叠商品表达”等同于“必须是一个闭合 SOLID”。

商品视觉表达、物理碰撞表达及制造表达可能需要不同的几何结构。

<box border radius="lg" padding={3} gap={2}>
  <svg viewBox="0 0 340 310" width="100%">
    <defs>
      <marker id="repArr" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0 0L6 3L0 6Z" fill="#8694ab"/></marker>
    </defs>
    <rect x="65" y="5" width="210" height="42" rx="6" fill="#e5e5fa" stroke="#998bc9"/>
    <text x="170" y="22" textAnchor="middle" fontSize="12" fontWeight="bold" fill="#60518e">统一商品结构 IR</text>
    <text x="170" y="37" textAnchor="middle" fontSize="10" fill="#6e638e">参数 / 面板 / 接缝 / 印刷映射</text>
    <path d="M170 47V65H83V82 M170 65H257V82" fill="none" stroke="#8694ab" markerEnd="url(#repArr)"/>
    <rect x="5" y="85" width="156" height="47" rx="6" fill="#e8edf8" stroke="#95a5c8"/>
    <text x="83" y="103" textAnchor="middle" fontSize="12" fontWeight="bold" fill="#425b89">展开态编译</text>
    <text x="83" y="118" textAnchor="middle" fontSize="10" fill="#607493">Net IR</text>
    <rect x="179" y="85" width="156" height="47" rx="6" fill="#e8edf8" stroke="#95a5c8"/>
    <text x="257" y="103" textAnchor="middle" fontSize="12" fontWeight="bold" fill="#425b89">折叠态编译</text>
    <text x="257" y="118" textAnchor="middle" fontSize="10" fill="#607493">Folded Assembly IR</text>
    <path d="M83 132V153 M257 132V153" stroke="#8694ab" markerEnd="url(#repArr)"/>
    <rect x="5" y="156" width="156" height="49" rx="6" fill="#e5edf9" stroke="#95a5c8"/>
    <text x="83" y="175" textAnchor="middle" fontSize="12" fontWeight="bold" fill="#425b89">blank.usdc</text>
    <text x="83" y="190" textAnchor="middle" fontSize="10" fill="#607493">FLAT_PATTERN</text>
    <rect x="179" y="156" width="156" height="49" rx="6" fill="#e1f0e6" stroke="#86af94"/>
    <text x="257" y="175" textAnchor="middle" fontSize="12" fontWeight="bold" fill="#427552">model.usdc</text>
    <text x="257" y="190" textAnchor="middle" fontSize="10" fill="#527e60">FOLDED_PRODUCT</text>
    <path d="M257 205V219H177V238 M257 219H296V238" fill="none" stroke="#8694ab" markerEnd="url(#repArr)"/>
    <rect x="121" y="241" width="112" height="46" rx="6" fill="#e1f0e6" stroke="#86af94"/>
    <text x="177" y="259" fontSize="11" fontWeight="bold" fill="#427552" textAnchor="middle">Visual Mesh</text>
    <text x="177" y="275" fontSize="10" fill="#527e60" textAnchor="middle">外观与印刷</text>
    <rect x="240" y="241" width="95" height="46" rx="6" fill="#e1f0e6" stroke="#86af94"/>
    <text x="287" y="259" fontSize="11" fontWeight="bold" fill="#427552" textAnchor="middle">Collision</text>
    <text x="287" y="275" fontSize="10" fill="#527e60" textAnchor="middle">物理代理</text>
    <text x="83" y="225" textAnchor="middle" fontSize="10" fill="#607493">制造及印刷用途</text>
  </svg>
  <caption>建议冻结的双主表达架构。折叠商品内部允许视觉与碰撞表示分离。</caption>
</box>

推荐的候选交付目录：

```text
sku/
├── model.usdc
├── blank.usdc
├── print.png
└── manifest.json
```

manifest 至少需要登记商品身份、IR 版本、表达类型、目标用途、源参数哈希和各表达独立的验证状态。

没有展开图语义的商品不强制生成 `blank.usdc`。它是适用于相应结构家族的可选表达，而非全部资产的必备文件。

该目录结构是下一版候选契约，不授权直接覆盖现有发行目录。

### 3.2 路线 A：解析焊接优先，但停止盲目手搓

我更倾向于利用 IR 已经具备的结构知识，而不是把整个问题交给通用网格修复算法。

因为我们已经拥有：

- 面板身份。
- 父子折叠关系。
- 折线位置。
- 印刷面角对应。
- 胶板及功能面板的结构语义。

这些信息正是普通网格修复工具所缺乏的。

但12条 FOLD 边构成生成树，只能证明面板展开关系具备相应的树结构，**不能证明最终折叠后的闭合缝、封口约束和几何接触全部正确。**

建议区分三种关系：

| IR 关系 | 编译行为 |
|---|---|
| FOLD | 根据明确的共享折线建立面板对应 |
| SEAL / JOIN | 按最终闭合契约连接对应边 |
| GLUE_OVERLAP | 保留内贴或重叠语义，不自动焊接为同一表面 |

后两项为建议新增的关系类型，需核对现有 IR 是否已有等价表达，避免重复定义。

这比对所有空间距离小于某个阈值的顶点执行全局吸附更可靠。

### 3.3 路线 B：成熟几何库作为基础组件，而非语义修复器

**批准 TRIAL，不批准整体外包折叠结构重建。**

| 工作内容 | 处理建议 |
|---|---|
| 网格拓扑诊断 | 优先复用成熟库 |
| 顶点合并、重复面检测 | trimesh TRIAL |
| 局部绕向修正 | trimesh TRIAL |
| 有效实体布尔运算 | Manifold TRIAL |
| 折叠状态与角度确定 | IR 负责 |
| 胶板是否保留 | 结构语义负责 |
| 印刷面角继承 | 编译器负责 |
| 真实商品尺寸验收 | 独立契约负责 |

如果输入本身存在未完全折叠的翻板、错误的封口状态或不正确的整体尺寸，通用网格库即使能够把它处理为闭合流形，也没有解决真实业务问题。

**不能用几何库输出 PASS 来替代商品结构正确性。**

### 3.4 UV 携带结论暂不接受

报告中“同面板顶点序天然一一对应，因此印刷纹理无镜像风险”的表述过于绝对。

面角对应关系可以通过 IR 保留，但折叠变换、三角化、顶点重编号、绕向修正和焊接过程都必须正确传递面角属性。

上一轮 WP-A0.2-U 的非对称诊断纹理实验继续保留，并可直接并入本轮候选编译器验收。

---

## 四、下一轮主线：建立第一个正确的折叠商品编译闭环

不再要求执行侧继续广泛研究审计器，也不批准立即重新编译9,386件资产。

下一轮只完成一件最重要的事情：

**让一个真实结构家族从规格输入，经统一 IR，正确生成展开态、折叠态及适用的碰撞表达，并完成独立验收。**

### WP-A3｜Folded Asset Compiler Pilot

建议以 aseptic_brick 为第一试点。

<card gap={3}>
  <caption>候选编译方案对照</caption>
  {#each [{id:"B0",t:"冻结发行基线",d:"现有平板 model.usdc"},{id:"B1",t:"折叠面板装配基线",d:"直接输出 fold world，保留独立面板"},{id:"B2",t:"IR 驱动结构连接",d:"按面板、折线和闭合关系建立拓扑"},{id:"B3",t:"成熟库辅助编译",d:"B2 加 trimesh / Manifold 的适用操作"}] as a,i}
    <row align="center">
      <box background="surface-secondary" radius="md" size="38px" align="center" justify="center">
        <text weight="medium">{a.id}</text>
      </box>
      <box flex={1} gap={0}>
        **{a.t}**
        <caption>{a.d}</caption>
      </box>
    </row>
    {#if i<3}<divider/>{/if}
  {/each}
</card>

B1 不要求通过实体闭合门禁，它的价值是提供一个不经过焊接的折叠几何基线。

B2、B3 必须使用相同的折叠输入及表达契约。如果需要比较 trimesh 与 Manifold，则进一步拆分为独立实验组，不能混合后统一归因。

### 七项试点验收门禁

| 门禁 | 验收要求 |
|---|---|
| F01 表达正确 | blank 与 model 分别满足各自契约 |
| F02 尺寸正确 | 三轴包围盒及关键结构尺寸符合独立规格 |
| F03 装配正确 | 折角、封口、翻板及胶板位置符合设计意图 |
| F04 几何正确 | 不存在契约禁止的退化、非流形或绕向错误 |
| F05 印刷正确 | 面角映射保持，非对称诊断纹理方向正确 |
| F06 物理表达正确 | 碰撞代理、质量及适用物理属性符合契约 |
| F07 编译可重复 | 相同输入及版本产生等价输出，证据可追溯 |

F06 中的实际物理仿真仍须在适用目标环境完成。在此之前标记 `VALIDATION_PENDING`，不能提前记为完整通过。

尺寸容差、折角容差和封口要求必须在候选实验前明确，不能根据输出结果倒推验收阈值。

---

## 五、对项目现状的战略重估

如果全量表达身份审计证实过去的 `model.usdc` 主要是展开件，那么我们需要重新理解此前建设的资产成果。

| 已积累资产 | 是否仍有价值 |
|---|---|
| 77个参数化结构家族 | 有价值，核心结构知识资产 |
| 9,386 SKU 规格及印刷数据 | 有价值，商品表达输入资产 |
| Net IR 及展开图 | 有价值，制造与包装设计表达 |
| fold_all 折叠能力 | 有价值，但需完成结构验收 |
| 既有渲染结果 | 保留价值，需核对实际输入表达 |
| 折叠 USD 商品资产交付能力 | 需要重新验证 |

不能因为发现输出架构问题，就否定此前所有研究成果；也不能因为已有大量有价值的输入资产，就继续声称折叠商品编译器已经完成。

本轮真正揭示的是一个尚未打通的产品能力缺口。

---

## 六、下一轮工作指派

| 工作包 | 优先级 | 指派 |
|---|---|---|
| WP-A3-FOLD | P0 | 核验95.5×38.2×138.6 mm 折叠结果与商品规格的差异，定位未封合或尺寸异常 |
| WP-A3-REP | P0 | 建立双表达候选编译接口及 manifest 契约 |
| WP-A3-TOPO | P0 | 完成 B1/B2/B3 几何编译对照 |
| WP-REP-AUDIT | P0 | 9,386件全量表达身份统计，只读执行 |
| WP-V | P0 | 增加历史渲染、验证器与仿真资产身份追溯 |
| WP-A0.2-U | P1 | 合并至折叠候选资产的诊断纹理实验 |
| WP1-v0.2 | P1 | 继续协议修订，暂不启动正式盲测 |

### 下一轮送审清单

{@body const tasks=[["fold_dimension_audit.json","折叠尺寸差异、面板状态及原因"],["representation_contract.md","双表达架构及部件用途契约"],["folded_compiler_trial.json","B0/B1/B2/B3 对照结果"],["representation_inventory.json","9,386件实际表达分类台账"],["validation_identity_ledger.json","历史渲染、验证及仿真的资产身份追溯"],["candidate_assets/","候选 USD、诊断纹理、manifest 及验收证据"]]}
{@body const [done,setDone]=DIL.useState(tasks.map(()=>false))}
<card gap={2}>
  <row align="center">
    **R09-05 送审制品**
    <spacer/>
    <caption>{done.filter(Boolean).length}/6</caption>
  </row>
  {#each tasks as a,i}
    <checkbox checked={done[i]} onChange={v=>setDone(old=>old.map((x,j)=>i===j?v:x))}>
      **{a[0]}**
      <caption>{a[1]}</caption>
    </checkbox>
  {/each}
  <button block variant="outline" color="secondary" onClick={()=>GenUI.copy(tasks.map((a,i)=>(done[i]?"[x] ":"[ ] ")+a.join(" — ")).join("\n"))}><icon name="copy" size="sm"/> 复制执行任务</button>
</card>

## 七、最终签核

| 裁决事项 | 最终状态 |
|---|---|
| D1 表达丢失根因定位 | ACCEPTED |
| 生成端三维几何完全正确 | NOT CONFIRMED |
| 9,386件全部平板化 | PENDING FULL AUDIT |
| 双表达产品架构 | ADOPT |
| IR 解析连接 | TRIAL |
| 成熟几何库辅助 | TRIAL |
| 印刷无镜像风险 | NOT CONFIRMED |
| WP-A3 试点执行 | AUTHORIZED |
| 冻结发行集批量覆盖 | PROHIBITED |

**R09-04 FINAL VERDICT：ROOT CAUSE ACCEPTED — DUAL REPRESENTATION ARCHITECTURE APPROVED**

下一步不是修复9,386个模型，而是先证明编译器能够正确交付一个完整的折叠商品。

一个结构家族的正确编译闭环，比9,386个尚未明确表达契约的资产更有工程价值。