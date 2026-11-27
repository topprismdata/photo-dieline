## 二、A3-02｜三表达契约是否可冻结？

**【修改】三表达架构正式批准，但具体契约仍有两个 P0 问题。**

| 表达 | 提议 | 裁决 |
|---|---|---|
| blank | FLAT_PATTERN + allowed_overlap | 修改后冻结 |
| visual | SOLID + UV + 镜像 UNKNOWN | 暂不冻结 |
| collision | 简化 SOLID | 同意，补充物理用途门禁 |

### P0-01｜allowed_overlap 台账存在过度授权

这是本轮我最不同意的地方。

提交的台账包含136组允许重叠关系，其中 `sb0–sb7` 与 `sf0–sf7` 这16个面板之间的全部两两组合，占120组。

<card gap={3}>
  <grid columns={2}>
    <grid-item>
      <caption>允许重叠关系总数</caption>
      <title size="2xl" tabularNums={true}>136</title>
    </grid-item>
    <grid-item>
      <caption>16个面板的全连接组合</caption>
      <title size="2xl" tabularNums={true}>120</title>
    </grid-item>
  </grid>
  <svg viewBox="0 0 340 175" width="100%">
    {#each Array.from({length:16},(_,i)=>i) as i}
      {#each Array.from({length:16},(_,j)=>j).filter(j=>j>i) as j}
        <line x1={170+68*Math.cos(i*Math.PI/8)} y1={85+68*Math.sin(i*Math.PI/8)} x2={170+68*Math.cos(j*Math.PI/8)} y2={85+68*Math.sin(j*Math.PI/8)} stroke="#bfa2ad" strokeOpacity=".24" strokeWidth=".7"/>
      {/each}
    {/each}
    {#each Array.from({length:16},(_,i)=>i) as i}
      <circle cx={170+68*Math.cos(i*Math.PI/8)} cy={85+68*Math.sin(i*Math.PI/8)} r="5" fill={i<8?"#6686c1":"#9475c1"} stroke="white"/>
      <text x={170+85*Math.cos(i*Math.PI/8)} y={88+80*Math.sin(i*Math.PI/8)} fontSize="9" textAnchor="middle" fill="currentColor">{i<8?`sb${i}`:`sf${i-8}`}</text>
    {/each}
  </svg>
  <box height={13} direction="row" gap={0} radius="full" clip={true}>
    <box background="#C68178" width="88.24%"/>
    <box background="#A9B7CD" width="11.76%"/>
  </box>
  <caption>88.2%的允许关系来自一个16面板全连接集合。依据本轮提交列表计数。</caption>
</card>

我不能接受这种无差别的两两重叠授权直接进入正式契约。

尤其是执行侧已经证明 net 面板实际面积交叠为0，那么为什么 blank 契约还需要登记136组允许重叠关系？

存在三种可能：

| 可能原因 | 处置 |
|---|---|
| 台账实际上描述折叠态重叠 | 迁移到 folded assembly 契约 |
| 台账由当前几何接触自动推导 | 只能作为 L1 观测，不得作为 L2 授权 |
| 台账来自明确结构设计 | 逐类补充来源、适用状态与允许条件 |

建议立即将关系区分为：

```text
observed_overlap
expected_overlap
allowed_overlap
forbidden_overlap
```

其中 `allowed_overlap` 必须有独立的设计依据，不能由实际检测到的重叠自动生成。

**blank 在没有明确例外设计证据的情况下，默认不允许面板内部正面积重叠；共享边与共享顶点不属于面积重叠。**

### P0-02｜visual=SOLID 尚需确认交付必要性

上一轮已经提出视觉表达与碰撞表达分离。当前将 visual 强制设为 SOLID，需要给出产品层面的理由。

| 用途 | 推荐表达 |
|---|---|
| 货架照片生成 | 正确的外部视觉表面 |
| 商品陈列仿真 | 视觉网格 + 封闭碰撞代理 |
| 包装制造仿真 | 带板材厚度及真实装配关系的结构模型 |
| 液体或容积计算 | 满足相应闭合及内部容积要求的实体表达 |

这些用途的几何要求不同。

我允许本试点选择闭合外壳作为 visual 的验收目标，但不能由此推出所有77个结构家族的视觉资产必须是单一 SOLID。

此外，`镜像 UNKNOWN` 可以作为当前验收状态，但不能成为正式契约中允许未知印刷正确性的规则。

建议冻结以下目标：

| 表达 | 推荐契约 |
|---|---|
| blank | 无非预期面积重叠的 FLAT_PATTERN |
| visual | 结构正确、外观完整、UV 正确的 FOLDED_PRODUCT |
| collision | 满足目标仿真用途的简化闭合代理 |

若本试点选择 visual 闭合外壳，则保留这一约束并完成验收，不允许在封合失败后临时撤销。

---

## 三、A3-04｜blank 家族源码级修复

**【同意】批准保留 `brick_family.py` 中五处面板绕向修复，作为候选分支的正式整改成果。**

这是目前最接近完整关闭的工作项。

<box border radius="lg" padding={3} gap={2}>
  <grid columns={2}>
    <grid-item>
      <box gap={1}>
        <svg viewBox="0 0 145 100" width="100%">
          <rect x="13" y="15" width="59" height="70" fill="#dce7f8" stroke="#8195bf"/>
          <rect x="72" y="15" width="59" height="70" fill="#f0dedb" stroke="#b78279"/>
          <path d="M67 24V75L63 68M77 24V75L81 68" fill="none" stroke="#b6554b" strokeWidth="2.5"/>
          <text x="42" y="52" fontSize="10" textAnchor="middle" fill="#526e9f">面板 A</text>
          <text x="103" y="52" fontSize="10" textAnchor="middle" fill="#9b625b">面板 B</text>
        </svg>
        **修复前**
        <text color="danger" weight="medium">FAIL</text>
        <caption>共享边方向冲突</caption>
      </box>
    </grid-item>
    <grid-item>
      <box gap={1}>
        <svg viewBox="0 0 145 100" width="100%">
          <rect x="13" y="15" width="59" height="70" fill="#dce7f8" stroke="#8195bf"/>
          <rect x="72" y="15" width="59" height="70" fill="#dceee3" stroke="#80a98b"/>
          <path d="M67 24V75L63 68M77 75V24L81 31" fill="none" stroke="#42865a" strokeWidth="2.5"/>
          <text x="42" y="52" fontSize="10" textAnchor="middle" fill="#526e9f">面板 A</text>
          <text x="103" y="52" fontSize="10" textAnchor="middle" fill="#548363">面板 B</text>
        </svg>
        **修复后**
        <text color="success" weight="medium">PASS（报告值）</text>
        <caption>共享边方向一致性恢复</caption>
      </box>
    </grid-item>
  </grid>
  <caption>绕向修复机制示意，非实际网格截图。</caption>
</box>

本轮证据支持将 D1 次根因重新登记为：

`D1-ROOT-02：面板局部绕向约定不一致`

不再将其登记为已经证实的 net 排样面积重叠问题。

但是，源码级修改可能影响后续折叠变换与 UV 面角顺序，因此保留修复需要补齐以下回归门禁。

| 回归项 | 验收要求 |
|---|---|
| 面板坐标集合 | 修复前后保持 |
| 面板面积 | 保持 |
| 二维外轮廓 | 保持 |
| 面板内部面积交叠 | 仍为0 |
| FOLD 边端点身份 | 保持正确 |
| fold_all 三维坐标 | 无非预期变化 |
| 印刷面角对应 | 不因绕向反转而错位 |

建议增加同家族最小、典型、最大三个合法规格变体进行候选回归，不扩大至其他家族。

**裁决状态：SOURCE FIX APPROVED / CANDIDATE RETAINED / RELEASE PENDING。**

---

## 四、A3-03｜是否批准 closure_relations 台账？

**【修改后同意】正式批准。这是下一步的主线方向。**

空间焊接实验的负结果很有价值。

<grid columns={2} gap={2}>
  <grid-item>
    <card gap={1}>
      <caption>解析 FOLD 焊接</caption>
      <title size="xl">1 个连通壳</title>
      <caption>24个顶点，尚未闭合</caption>
    </card>
  </grid-item>
  <grid-item>
    <card gap={1}>
      <caption>空间近似焊接</caption>
      <title size="xl">24 → 16</title>
      <caption>边界边减少，但引入新缺陷</caption>
    </card>
  </grid-item>
</grid>

这证明边界边数量下降不能单独作为修复成功指标。

空间焊接减少了8条边界边，却引入退化三角形、重复边及非流形顶点。因此这一候选方案应登记为负向实验结果，不再继续调整吸附阈值寻找偶然 PASS。

### 4.1 修改封合关系类型的定义

我同意增加 `closure_relations`，但不完全同意当前三类关系与焊接行为的直接对应。

| 关系 | 物理语义 | 默认编译行为 |
|---|---|---|
| FOLD | 同一板材上的折线 | 共享拓扑连接 |
| GLUE_BOND | 胶合连接 | 保留胶合关系，不默认合并全部接触面 |
| FOLD_MEET | 折叠后空间相遇 | 仅检查位置与姿态，不默认焊接 |
| SEAL_JOIN | 明确形成外壳闭合缝 | 按端点映射建立拓扑连接 |
| END_CAP | 封口面板或封口结构 | 验证真实封口面，不凭空补洞 |

`GLUE_BOND` 不能直接等同于 weld。

例如，两个纸板面通过胶层贴合，在实际物理结构中仍是两层独立材料。如果直接把它们焊接成一个表面，可能改变厚度、拓扑及结构身份。

### 4.2 建议增加独立的 topology_action 字段

将结构关系与编译行为分离。

```json
{
  "relation_id": "closure_001",
  "representation": "folded_visual",
  "assembly_state": "FINAL_SEALED",
  "relation_type": "SEAL_JOIN",
  "side_a": {
    "panel_id": "panel_a",
    "edge_id": "edge_a"
  },
  "side_b": {
    "panel_id": "panel_b",
    "edge_id": "edge_b"
  },
  "endpoint_mapping": "REVERSED",
  "topology_action": "WELD_EDGE",
  "source": "family_design_contract",
  "tolerance_mm": null
}
```

以上是建议的数据结构示例，不代表已经确认的真实封合关系。数值容差必须在实验前登记。

`topology_action` 建议至少支持 `WELD_EDGE`、`KEEP_SEPARATE`、`CONTACT_ONLY` 和 `TRIM_AND_JOIN`。

这样可以做到：同一种物理连接关系，在制造模型、视觉外壳和碰撞代理中采用不同的合法表达策略。

### 4.3 用剩余24条边界边建立完整账本

这是本轮最小、最有效的研究动作。

不需要先为全部面板建立复杂的装配本体。先将当前24条边界边逐条登记。

<box border radius="lg" padding={3} gap={2}>
  <svg viewBox="0 0 340 220" width="100%">
    <rect x="68" y="5" width="204" height="36" rx="6" fill="#e3eafa" stroke="#8799c9"/>
    <text x="170" y="28" fontSize="12" fontWeight="bold" textAnchor="middle" fill="#425b90">24条实际边界边</text>
    <path d="M170 41V55H86V69M170 55H254V69" fill="none" stroke="#8694aa"/>
    <rect x="5" y="69" width="162" height="43" rx="6" fill="#e5eafa" stroke="#8e9dc5"/>
    <text x="86" y="86" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#465c8e">有明确封合对象</text>
    <text x="86" y="100" textAnchor="middle" fontSize="10" fill="#637496">结构证据支持连接</text>
    <rect x="173" y="69" width="162" height="43" rx="6" fill="#eee8f8" stroke="#9e8bc6"/>
    <text x="254" y="86" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#6b5596">无明确封合对象</text>
    <text x="254" y="100" textAnchor="middle" fontSize="10" fill="#7c6a9d">合法边界或结构异常</text>
    <path d="M86 112V134M254 112V134" stroke="#8694aa"/>
    <rect x="5" y="134" width="162" height="38" rx="6" fill="#e1efe6" stroke="#87ac93"/>
    <text x="86" y="157" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#407452">解析连接与几何核验</text>
    <rect x="173" y="134" width="162" height="38" rx="6" fill="#fff0da" stroke="#cda967"/>
    <text x="254" y="157" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#987332">保持或报告结构缺失</text>
    <path d="M86 172V184H254V172M170 184V193" fill="none" stroke="#8694aa"/>
    <rect x="68" y="193" width="204" height="26" rx="5" fill="#edf0f6" stroke="#a0abc0"/>
    <text x="170" y="210" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#53647f">每条边均具有可解释的终态</text>
  </svg>
</box>

最终每条边必须属于以下某一种状态：

| 状态 | 含义 |
|---|---|
| JOINED | 已按设计关系连接 |
| LEGAL_BOUNDARY | 契约允许保留 |
| INTERNAL_LAYER | 属于内部独立材料层 |
| MISSING_CLOSURE | 存在应封合但未封合的结构 |
| GEOMETRY_MISMATCH | 设计要求连接，但实际几何不匹配 |
| UNKNOWN | 缺乏足够结构依据 |

如果最终 visual 契约要求闭合 SOLID，则不能存在未解决的开放边界。合法的独立内部层也必须在相应独立部件契约下管理，而不能混入闭合外壳。

---

## 五、A3-05 UV 诊断与封合台账的执行顺序

**裁决：两者并行，但 UV 必须设置焊接前、焊接后两次检查。**

不能等全部封合完成之后才开始 UV 验证。

因为本轮已经修改了五处面板绕向，下一轮还将修改拓扑等价类、顶点索引与封合关系。如果最后才发现印刷错误，将无法确定是哪一次操作引入的。

<box border radius="lg" padding={3} gap={2}>
  <svg viewBox="0 0 340 300" width="100%">
    <defs>
      <marker id="uv06" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0 0L6 3L0 6Z" fill="#8493aa"/></marker>
    </defs>
    <rect x="63" y="5" width="214" height="36" rx="6" fill="#e3eafa" stroke="#8b9bc7"/>
    <text x="170" y="27" fontSize="12" fontWeight="bold" fill="#40598a" textAnchor="middle">冻结当前 v1 候选基线</text>
    <path d="M170 41V54H82V69M170 54H258V69" fill="none" stroke="#8493aa" markerEnd="url(#uv06)"/>
    <rect x="4" y="72" width="156" height="48" rx="6" fill="#e9e3f9" stroke="#9b89c9"/>
    <text x="82" y="90" fontSize="11" fontWeight="bold" fill="#655293" textAnchor="middle">A3-05a · UV 基线</text>
    <text x="82" y="105" fontSize="10" fill="#78669d" textAnchor="middle">非对称纹理、面角对照</text>
    <rect x="180" y="72" width="156" height="48" rx="6" fill="#e3eafa" stroke="#8b9bc7"/>
    <text x="258" y="90" fontSize="11" fontWeight="bold" fill="#40598a" textAnchor="middle">A3-03a · 封合台账</text>
    <text x="258" y="105" fontSize="10" fill="#596e96" textAnchor="middle">24条边界逐条仲裁</text>
    <path d="M258 120V139" stroke="#8493aa" markerEnd="url(#uv06)"/>
    <rect x="180" y="142" width="156" height="36" rx="6" fill="#e3eafa" stroke="#8b9bc7"/>
    <text x="258" y="164" fontSize="11" fontWeight="bold" fill="#40598a" textAnchor="middle">A3-03b · 解析封合</text>
    <path d="M82 120V191H170V207M258 178V191H170" fill="none" stroke="#8493aa" markerEnd="url(#uv06)"/>
    <rect x="63" y="210" width="214" height="39" rx="6" fill="#e9e3f9" stroke="#9b89c9"/>
    <text x="170" y="226" fontSize="11" fontWeight="bold" fill="#655293" textAnchor="middle">A3-05b · UV 回归</text>
    <text x="170" y="240" fontSize="10" fill="#78669d" textAnchor="middle">验证封合前后印刷保持</text>
    <path d="M170 249V265" stroke="#8493aa" markerEnd="url(#uv06)"/>
    <rect x="63" y="268" width="214" height="30" rx="6" fill="#e0efe5" stroke="#87ab92"/>
    <text x="170" y="287" fontSize="12" fontWeight="bold" fill="#417653" textAnchor="middle">F01–F07 正式复验</text>
  </svg>
</box>

### UV 基线实验的最小要求

沿用此前已经指定的非对称诊断纹理，不增加新的视觉研究范围。

必须能够识别面板 ID、左上与右下角、印刷朝向，以及每个三角形对应的原始面角。

先证明当前五处绕向修改没有破坏印刷映射，再证明后续解析封合没有引入新的 UV 错误。

---

## 六、下一轮工作指派

下一轮命名为 **WP-A3 v1.1 — Closure Semantics & UV Preservation**。

本轮只关闭已发现的问题，不增加新家族、不扩大资产数量、不启动 Manifold 通用修复路线。

| 任务编号 | 优先级 | 执行内容 | 建议资源上限 |
|---|---|---|---|
| A3-01-CLOSE | P0 | 真实成品参考与候选三视图对照 | 1小时 |
| A3-02-CLOSE | P0 | 清理136组重叠授权的来源与适用表达 | 1小时 |
| A3-03a | P0 | 24条边界边及封合关系台账 | 半天 |
| A3-03b | P0 | 按关系与角点身份编译封合 | 半天 |
| A3-04-REG | P1 | blank 源码修复的三个规格变体回归 | 2小时 |
| A3-05a | P1 | 封合前 UV 诊断基线 | 并行 |
| A3-05b | P1 | 封合后 UV 保持验证 | 封合完成后 |
| A3-06 | P1 | 七项门禁重新验收 | 最后执行 |

以上资源上限是研究范围建议，不是团队已经确认的工期。

### 下一轮送审制品

{@body const tasks=[["product_shape_arbitration.md","真实包装、参数定义及候选三视图"],["representation_contract_v1.1.md","三表达契约及重叠授权治理"],["closure_relations.json","24条边界边逐条映射及设计依据"],["closure_compilation_results.json","解析封合前后拓扑与尺寸数据"],["blank_regression.json","三个规格变体源码修复回归"],["uv_diagnostic_before_after/","封合前后非对称纹理及面角证据"],["wp_a3_v1.1_results.json","F01–F07复验结果"]]}
{@body const [done,setDone]=DIL.useState(tasks.map(()=>false))}
<card gap={2}>
  <row align="center">
    **R09-07 送审清单**
    <spacer/>
    <caption>{done.filter(Boolean).length}/7</caption>
  </row>
  {#each tasks as a,i}
    <checkbox checked={done[i]} onChange={v=>setDone(old=>old.map((x,j)=>j===i?v:x))}>
      **{a[0]}**
      <caption>{a[1]}</caption>
    </checkbox>
  {/each}
  <button block variant="outline" color="secondary" onClick={()=>GenUI.copy(tasks.map((a,i)=>(done[i]?"[x] ":"[ ] ")+a.join(" — ")).join("\n"))}><icon name="copy" size="sm"/> 复制执行清单</button>
</card>

WP-REP-AUDIT、WP-V、WP1-v0.2 仍然保持并行，不因本试点暂停。

---

## 七、当前研究的一个重要架构结论

我认为，经过这几轮实验，我们已经发现结构家族 IR 中至少存在四类不能互相替代的关系。

<box border radius="lg" padding={3} gap={2}>
  <box background="#E6ECFA" radius="md" padding={3}>
    <text color="#455D91" weight="medium">第一层：制造关系 Manufacturing</text>
    <text color="#52688F" size="sm">切割、折线、板材、胶板、展开布局。</text>
  </box>
  <row justify="center"><icon name="arrow-down" color="secondary"/></row>
  <box background="#ECE6FA" radius="md" padding={3}>
    <text color="#695197" weight="medium">第二层：装配关系 Assembly</text>
    <text color="#78649B" size="sm">折叠姿态、接触、胶合、封口及重叠。</text>
  </box>
  <row justify="center"><icon name="arrow-down" color="secondary"/></row>
  <box background="#E4EAF7" radius="md" padding={3}>
    <text color="#49618D" weight="medium">第三层：表达关系 Representation</text>
    <text color="#5D7095" size="sm">顶点焊接、独立曲面、实体外壳、碰撞代理。</text>
  </box>
  <row justify="center"><icon name="arrow-down" color="secondary"/></row>
  <box background="#E2EFE6" radius="md" padding={3}>
    <text color="#407653" weight="medium">第四层：验证关系 Validation</text>
    <text color="#507E60" size="sm">预期结构与实际编译结果之间的证据及裁决。</text>
  </box>
</box>

FOLD 属于结构及装配知识，WELD 属于几何表达操作，两者不能简单画等号。

同样，实际观测到 OVERLAP，不代表设计契约允许 OVERLAP。

这些关系的区分，应作为商品数字对象本体建设的重要研究成果沉淀，而不是只在 brick 家族中写几个特殊补丁。

不过，本轮不授权开展独立的大规模本体重构，只要求新建的 `closure_relations` 遵循上述语义分离原则。

---

## 八、最终签核

| 裁决项 | 最终状态 |
|---|---|
| 独立闭式 bbox 公式 | ACCEPTED AS REPORTED |
| 最终商品形态正确性 | PENDING |
| 三表达架构 | ADOPT |
| 136组重叠授权 | NOT APPROVED AS SUBMITTED |
| blank 五处绕向源码修复 | APPROVED AS CANDIDATE |
| FOLD 解析焊接成果 | ACCEPTED |
| 空间近似焊接 | REJECTED AS PRODUCTION METHOD |
| closure_relations | ADOPT WITH AMENDMENTS |
| UV 诊断 | REQUIRED BEFORE AND AFTER CLOSURE |
| WP-A3 v1.1 | AUTHORIZED |
| 全量重新编译 | PROHIBITED |

**R09-06 FINAL VERDICT：CONDITIONAL PASS — AUTHORIZE SEMANTIC CLOSURE COMPILATION**

特别强调：下一轮不以边界边数量归零作为唯一目标，也不以所有审计器红灯消失作为成功标准。

**我们需要的是每一条连接、每一次重叠、每一个封合面都有明确的结构依据，并且编译结果忠实保留这种依据。** 这才是零售数字资产编译器应该建立的核心能力。