# R09-05 正式裁决｜WP-A3 折叠资产编译试点 v0

**总体裁决：CONDITIONAL PASS（试点研究进展通过，单家族正确编译闭环尚未成立）。**

本轮已经证明双表达编译路径可以产出候选资产，也进一步缩小了几何问题的范围。但我不同意执行侧关于尺寸正确性已经完全证明的结论。

此外，blank 与 folded 目前均为 FAIL，不能将其解释为仅剩少量工程收尾工作。需要先解决结构语义和独立验收依据，再完成拓扑编译。

| 裁决事项 | 正式决定 |
|---|---|
| A. 折叠尺寸正确性 | 部分通过，不关闭 |
| B. blank 排样重复边 | 按结构语义分类，不统一净化 |
| C. 焊接实现路线 | **选择 IR 驱动解析焊接** |
| D. 单家族正确编译闭环 | 尚未达到 |
| E. 下一步 | 授权 WP-A3 v1 定向整改 |
| 冻结9,386件资产 | 保持不变 |

## 一、A｜尺寸对照证据是否足够？

**裁决：【修改】接受编译尺寸保持证据，不接受真实商品尺寸正确性已经证明。**

这是两个不同的验收命题。

<card gap={3}>
  <caption>第一层：折叠计算结果与 USD 输出一致性</caption>
  <table>
    <table-row>
      <table-cell>维度</table-cell>
      <table-cell align="end">Analytic</table-cell>
      <table-cell align="end">USD bbox</table-cell>
      <table-cell align="end">绝对误差</table-cell>
    </table-row>
    {#each [{n:"W",a:"95.485",b:"95.490",d:"0.005"},{n:"D",a:"38.194",b:"38.190",d:"0.004"},{n:"H",a:"138.582",b:"138.580",d:"0.002"}] as a}
      <table-row>
        <table-cell>{a.n}</table-cell>
        <table-cell align="end">{a.a}</table-cell>
        <table-cell align="end">{a.b}</table-cell>
        <table-cell align="end"><text color="success">{a.d}</text></table-cell>
      </table-row>
    {/each}
  </table>
  <caption>单位：mm。依据执行侧报告。</caption>
  <title size="lg" color="success">编译尺寸保持：PASS AS REPORTED</title>
  <divider/>
  <caption>第二层：折叠结果与目标商品规格一致性</caption>
  <table>
    <table-row>
      <table-cell>维度</table-cell>
      <table-cell align="end">原始规格</table-cell>
      <table-cell align="end">折叠结果</table-cell>
      <table-cell align="end">差值</table-cell>
    </table-row>
    {#each [{n:"W",a:"57.3",b:"95.49",d:"+38.19"},{n:"D",a:"38.2",b:"38.19",d:"−0.01"},{n:"H*",a:"126.6",b:"138.58",d:"+11.98"}] as a}
      <table-row>
        <table-cell>{a.n}</table-cell>
        <table-cell align="end">{a.a}</table-cell>
        <table-cell align="end">{a.b}</table-cell>
        <table-cell align="end"><text color={a.n==="D"?"default":"danger"}>{a.d}</text></table-cell>
      </table-row>
    {/each}
  </table>
  <caption>* 暂按 Hb + hr 为目标总高，须核实参数正式定义。</caption>
  <title size="lg" color="warning">商品尺寸正确性：NOT CONFIRMED</title>
</card>

如果 `analytic_bbox` 也是从 `fold_all` 的三维点计算得到，那么当前实验本质上是：

\[
\operatorname{BBox}(\text{fold world})
\approx
\operatorname{BBox}(\text{USD})
\]

它证明了导出过程没有明显改变折叠几何的整体尺寸，但没有证明折叠几何本身符合商品规格。

<box border radius="lg" padding={3} gap={2}>
  <svg viewBox="0 0 340 205" width="100%">
    <defs>
      <marker id="a3arrow" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0 0L6 3L0 6Z" fill="#8393aa"/></marker>
    </defs>
    <rect x="70" y="5" width="200" height="37" rx="5" fill="#e5eafa" stroke="#8b9aca"/>
    <text x="170" y="20" fontSize="12" fontWeight="bold" textAnchor="middle" fill="#465d94">独立商品规格</text>
    <text x="170" y="34" fontSize="10" textAnchor="middle" fill="#5b6f98">目标尺寸与封合状态</text>
    <path d="M170 42V79" stroke="#c28b42" strokeDasharray="4 3" markerEnd="url(#a3arrow)"/>
    <rect x="184" y="49" width="107" height="20" rx="4" fill="#fff0d9"/>
    <text x="237" y="63" fontSize="10" textAnchor="middle" fill="#9e702d">尚未验证的环节</text>
    <rect x="70" y="82" width="200" height="40" rx="5" fill="#e5eafa" stroke="#8b9aca"/>
    <text x="170" y="98" fontSize="12" textAnchor="middle" fontWeight="bold" fill="#465d94">fold_all 折叠几何</text>
    <text x="170" y="113" fontSize="10" textAnchor="middle" fill="#5b6f98">95.485 × 38.194 × 138.582</text>
    <path d="M170 122V158" stroke="#52966d" strokeWidth="2" markerEnd="url(#a3arrow)"/>
    <text x="185" y="143" fontSize="10" fill="#397c54">已验证的尺寸保持</text>
    <rect x="70" y="161" width="200" height="40" rx="5" fill="#e1f0e6" stroke="#86af94"/>
    <text x="170" y="177" fontSize="12" fontWeight="bold" textAnchor="middle" fill="#39734e">USD 输出</text>
    <text x="170" y="192" fontSize="10" textAnchor="middle" fill="#527b61">95.490 × 38.190 × 138.580</text>
  </svg>
  <caption>验证了下游传递一致性，尚未验证上游折叠结果的正确性。</caption>
</box>

### 下一步最小补证

不需要再次测量 USD bbox。需要回答以下四个问题：

| 编号 | 必须回答的问题 |
|---|---|
| A01 | `analytic_bbox` 是独立理论公式，还是从 fold world 顶点计算？ |
| A02 | W、D、Hb、hr 的正式参数语义是什么？ |
| A03 | 哪些面板导致宽度额外增加38.2 mm？ |
| A04 | 哪些面板导致高度额外增加12 mm？ |

尤其是宽度增量近似 D、高度增量近似 hr，这种规律性值得继续调查。

正式状态拆分为：

```text
DIMENSION_PRESERVATION = PASS_AS_REPORTED
DIMENSION_CONFORMANCE  = NOT_CONFIRMED
FOLD_STATE_CORRECTNESS = NOT_CONFIRMED
```

不批准撤回上一轮对真实商品尺寸正确性的保留意见。

---

## 二、B｜blank 排样重复边是否属于真实缺陷？

**裁决：【修改】不能仅凭重复有向边与边界不可走，认定 FLAT_PATTERN 存在真实排样缺陷。**

这里需要进一步区分包装展开图的三种结构关系。

<grid columns={3} gap={2}>
  <grid-item>
    <box border radius="md" padding={2}>
      <svg viewBox="0 0 100 110" width="100%">
        <rect x="8" y="18" width="42" height="76" fill="#dce7fb" stroke="#738bbc"/>
        <rect x="50" y="18" width="42" height="76" fill="#e8def9" stroke="#9278bf"/>
        <path d="M50 18V94" stroke="#566c9e" strokeWidth="2" strokeDasharray="4 3"/>
      </svg>
      **共享折线**
      <caption>两个面板共享同一边，属于设计关系。</caption>
    </box>
  </grid-item>
  <grid-item>
    <box border radius="md" padding={2}>
      <svg viewBox="0 0 100 110" width="100%">
        <rect x="8" y="18" width="60" height="76" fill="#dce7fb" stroke="#738bbc"/>
        <path d="M68 28L88 39V75L68 84Z" fill="#e9ddf9" stroke="#9278bf"/>
        <path d="M68 28V84" stroke="#9278bf" strokeDasharray="3 3"/>
      </svg>
      **胶合翻板**
      <caption>展开时通常独立，折叠后允许设计重叠。</caption>
    </box>
  </grid-item>
  <grid-item>
    <box border radius="md" padding={2}>
      <svg viewBox="0 0 100 110" width="100%">
        <rect x="8" y="18" width="56" height="76" fill="#dce7fb" stroke="#738bbc"/>
        <rect x="37" y="35" width="55" height="59" fill="#e9ddf9" stroke="#9278bf" fillOpacity=".8"/>
        <rect x="37" y="35" width="27" height="59" fill="#d99791" fillOpacity=".8" stroke="#b85853"/>
      </svg>
      **展开态重叠**
      <caption>对于单张板材刀版，非预期面积重叠通常是缺陷。</caption>
    </box>
  </grid-item>
</grid>

特别注意：**胶板在折叠后与壁面重叠合法，不代表胶板在二维展开图中与其他面板面积重叠也合法。**

执行侧必须先回答 blank 的产品用途。

| 表达用途 | 正确验收方式 |
|---|---|
| 制造刀版 | 检查二维面板内部重叠、外部切割轮廓、折线及连通性 |
| 面板语义展示 | 允许独立面板，但必须保留面板身份与关系 |
| 印刷图集 | 检查印刷区域、有效映射与允许的复用规则 |

如果 blank 是面板集合的可视化表达，则不一定要求合并成一个全局流形网格。

如果 blank 是实际生产使用的单张纸板展开刀版，则需要证明面板内部不存在未经允许的正面积重叠。

### B 项最小仲裁实验

直接对原始二维 polygon 执行以下检查，不先修改三角网格。

| 检查项 | 验收依据 |
|---|---|
| 面板内部面积交叠 | 两个 polygon 的实际交集面积 |
| 合法共享边 | IR 中明确登记的 FOLD / JOIN |
| 重复面板 | 面板 ID 与几何来源 |
| 外轮廓 | 面板并集的二维边界 |
| 胶板位置 | 原始展开图结构规格 |

建议试用 Shapely 执行二维 polygon 交集、并集及有效性诊断，不需要自主开发二维多边形布尔运算。

但禁止直接通过 polygon union 消除异常后宣布刀版正确。并集操作可能掩盖错误重叠及面板身份丢失。

**B 最终裁决：TRIAL。先完成二维面板关系仲裁，再决定是否修复 blank 几何。**

---

## 三、C｜解析焊接还是 Manifold repair？

**明确裁决：选择 IR 驱动的解析焊接，暂不授权 Manifold repair 作为本轮主修复路径。**

理由不是排斥成熟几何库，而是当前已知问题发生在结构关系向网格索引传递的过程中。我们应该修复这种关系，而不是要求通用算法猜测设计意图。

### 3.1 推荐的拓扑编译路线

<box border radius="lg" padding={3} gap={2}>
  <svg viewBox="0 0 340 306" width="100%">
    <defs>
      <marker id="topoarr" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0 0L6 3L0 6Z" fill="#8393a8"/></marker>
    </defs>
    {#each [{y:4,t:"1. 面板局部角点身份",s:"(panel_id, corner_id)"},{y:64,t:"2. IR 显式连接约束",s:"FOLD / JOIN / SEAL"},{y:124,t:"3. 构建拓扑等价类",s:"并查集：仅合并语义相同角点"},{y:184,t:"4. 重建全局顶点与三角面",s:"保留独立 faceVarying UV"},{y:244,t:"5. 独立几何验收",s:"闭合、绕向、尺寸、印刷映射"}] as a,i}
      <rect x="27" y={a.y} width="286" height="44" rx="6" fill={i===4?"#e1efe6":"#e7eafa"} stroke={i===4?"#86aa91":"#929dc9"}/>
      <text x="170" y={a.y+17} textAnchor="middle" fontSize="12" fontWeight="bold" fill="#41577c">{a.t}</text>
      <text x="170" y={a.y+33} textAnchor="middle" fontSize="10" fill="#60718b">{a.s}</text>
      {#if i<4}<path d={`M170 ${a.y+44}v13`} stroke="#8393a8" markerEnd="url(#topoarr)"/>{/if}
    {/each}
  </svg>
  <caption>拓扑连接由结构知识确定，空间坐标用于验证，不用于猜测连接关系。</caption>
</box>

这里的关键是先构造角点等价类，再生成最终网格索引。

不要在逐面板导出时不断修改已经生成的全局顶点列表，否则很容易再次出现索引失配、孤立三角形和部分焊接。

### 3.2 FOLD 边不足以构建闭合实体

执行侧此前提到12条 FOLD 关系构成13面板的生成树。

生成树可以确定面板之间的折叠关系，但最终闭合包装还需要额外的封合关系。

<grid columns={2} gap={3}>
  <grid-item>
    <box border radius="md" padding={2}>
      <svg viewBox="0 0 145 120" width="100%">
        {#each [0,1,2,3] as i}
          <rect x={12+i*31} y="30" width="30" height="62" fill={i%2?"#e6dff9":"#dce7fa"} stroke="#7a8abc"/>
        {/each}
        {#each [1,2,3] as i}
          <path d={`M${11+i*31} 30V92`} stroke="#5d78ad" strokeWidth="2" strokeDasharray="4 3"/>
        {/each}
      </svg>
      **FOLD 生成树**
      <caption>描述面板如何连接和折叠。</caption>
    </box>
  </grid-item>
  <grid-item>
    <box border radius="md" padding={2}>
      <svg viewBox="0 0 145 120" width="100%">
        <path d="M35 29L78 12L113 31L70 50Z" fill="#e6dff9" stroke="#7a8abc"/>
        <path d="M35 29L70 50V110L35 89Z" fill="#dce7fa" stroke="#7a8abc"/>
        <path d="M70 50L113 31V91L70 110Z" fill="#b8c6eb" stroke="#7a8abc"/>
        <path d="M70 50V110" stroke="#348f5b" strokeWidth="3" strokeDasharray="4 2"/>
      </svg>
      **最终封合关系**
      <caption>额外连接闭合后的对应边。</caption>
    </box>
  </grid-item>
</grid>

因此必须分别验证：

| 关系 | 要求 |
|---|---|
| FOLD | 对应边端点身份及折叠后几何位置一致 |
| JOIN / SEAL | 闭合边匹配及封合状态正确 |
| GLUE_OVERLAP | 保留胶板语义，不进行无差别顶点合并 |
| UV_CORNER | 保持面板局部角点与印刷属性的关联 |

如果两个待连接角点在折叠空间中距离超出预设容差，应报告折叠或装配异常，而不是强行吸附。

### 3.3 本轮禁止全局空间焊接作为最终方案

空间焊接可以保留为实验对照，但不能成为默认生产策略。

因为它无法区分：

- 结构上应该连接的两个角点。
- 仅仅空间位置重合的两个独立角点。
- 胶板与壁面之间的设计重叠。
- 因折叠错误产生的非预期重合。

Manifold 可以在后续用于已经具备清晰实体语义的网格布尔运算与有效性检查，但不应承担本轮的包装装配语义推断任务。

**C 最终裁决：IR-BASED TOPOLOGY COMPILATION — AUTHORIZED。**

---

## 四、D｜WP-A3 是否达到单家族正确编译闭环？

**裁决：未达到。**

按 R09-04 冻结的七项门禁重新判定：

| 门禁 | 当前状态 | 理由 |
|---|---|---|
| F01 双表达 | 部分通过 | 两个文件均已产出，但尚未符合各自完整契约 |
| F02 尺寸 | 部分通过 | 编译保持已证明，目标商品尺寸未证明 |
| F03 装配 | 未通过验收 | 折角、翻板、胶板与封合状态未独立核验 |
| F04 几何 | FAIL | blank 与 folded 均存在报告中的拓扑问题 |
| F05 印刷 | 待验证 | 面角重构已实现，但没有独立映射及诊断纹理证据 |
| F06 物理 | NOT_RUN | 碰撞代理与实际物理行为尚未验收 |
| F07 可重复编译 | 待验证 | 未提交重复编译及完整 manifest 对照 |

<box border radius="lg" padding={3} gap={2}>
  <caption>WP-A3 v0 完整门禁验收情况</caption>
  <row align="center">
    <title size="2xl" tabularNums={true}>0 / 7</title>
    <caption>完整关闭的门禁</caption>
  </row>
  <box direction="row" gap={1} height={18}>
    {#each ["#D8A65B","#D8A65B","#AAB4C6","#CB7169","#AAB4C6","#AAB4C6","#AAB4C6"] as c}
      <box flex={1} background={c} radius="sm"/>
    {/each}
  </box>
  <row wrap="wrap" gap={3}>
    <row align="center" gap={1}><box size="10px" background="#D8A65B" radius="sm"/><caption>部分通过 2</caption></row>
    <row align="center" gap={1}><box size="10px" background="#CB7169" radius="sm"/><caption>明确失败 1</caption></row>
    <row align="center" gap={1}><box size="10px" background="#AAB4C6" radius="sm"/><caption>待验证 4</caption></row>
  </row>
</box>

这不意味着本轮没有取得进展，而是必须区分研发进展和产品验收。

目前可以正式确认的研究成果包括：表达传递链已经打通，候选文件已经生成，折叠坐标至 USD 的尺寸保持获得证据支持，以及拓扑连接问题进一步定位。

### 另外：需要重新确认是否真的要求 folded visual mesh 为 SOLID

上一轮已经批准视觉网格与碰撞代理分离。

建议 aseptic_brick 至少区分以下三个部件或表达契约：

| 表达 | 建议契约 |
|---|---|
| blank | FLAT_PATTERN |
| folded visual | FOLDED_PRODUCT 下的明确面板装配或闭合外壳契约 |
| collision | 合法的封闭碰撞代理 |

如果产品要求交付带真实板材厚度的闭合实体，则必须满足实体门禁。

如果产品要求的是商品外观与货架刚体仿真，那么正确的视觉面板装配加独立碰撞代理，可能比强行将所有纸板、胶板合并成一个闭合实体更合适。

这不是降低验收标准，而是选择与真实交付用途一致的表达方式。但必须在下一轮实验前冻结，不能根据焊接结果反向选择契约。

---

## 五、E｜下一轮任务指派

下一轮命名为 **WP-A3 v1 — Semantic Topology Compilation**。

不增加 SKU，不更换结构家族，不全面重构编译器。集中完成 aseptic_brick 的正确编译闭环。

| 任务 | 优先级 | 交付要求 |
|---|---|---|
| A3-01 尺寸与折叠姿态仲裁 | P0 | 独立规格、面板状态、异常 bbox 来源 |
| A3-02 表达契约冻结 | P0 | blank、visual、collision 各自验收规则 |
| A3-03 IR 解析连接 | P0 | 角点等价类、FOLD 与封合关系编译 |
| A3-04 blank 二维仲裁 | P0 | 面板重叠面积及设计关系台账 |
| A3-05 UV 诊断 | P1 | 源面角、USD 面角、非对称纹理对照 |
| A3-06 七门禁复测 | P1 | 逐项结果及失败证据 |

### 5.1 建议执行顺序

<box border radius="lg" padding={3}>
  <svg viewBox="0 0 340 275" width="100%">
    <defs>
      <marker id="seqarr" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0 0L6 3L0 6Z" fill="#8291a8"/></marker>
    </defs>
    <rect x="65" y="5" width="210" height="36" rx="6" fill="#e6eafa" stroke="#8c9dce"/>
    <text x="170" y="27" textAnchor="middle" fontSize="12" fontWeight="bold" fill="#465c8e">尺寸与表达契约冻结</text>
    <path d="M170 41V55H83V69 M170 55H257V69" fill="none" stroke="#8291a8" markerEnd="url(#seqarr)"/>
    <rect x="5" y="72" width="156" height="44" rx="6" fill="#e8e3f8" stroke="#9b89cb"/>
    <text x="83" y="89" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#655394">blank 二维仲裁</text>
    <text x="83" y="104" textAnchor="middle" fontSize="10" fill="#7765a1">面板关系与交叠</text>
    <rect x="179" y="72" width="156" height="44" rx="6" fill="#e8e3f8" stroke="#9b89cb"/>
    <text x="257" y="89" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#655394">IR 解析拓扑编译</text>
    <text x="257" y="104" textAnchor="middle" fontSize="10" fill="#7765a1">角点与封合关系</text>
    <path d="M83 116V129H170V145 M257 116V129H170" fill="none" stroke="#8291a8" markerEnd="url(#seqarr)"/>
    <rect x="65" y="148" width="210" height="35" rx="6" fill="#e6eafa" stroke="#8c9dce"/>
    <text x="170" y="170" textAnchor="middle" fontSize="12" fontWeight="bold" fill="#465c8e">UV 与几何独立验证</text>
    <path d="M170 183V198" stroke="#8291a8" markerEnd="url(#seqarr)"/>
    <rect x="65" y="201" width="210" height="30" rx="6" fill="#fff0da" stroke="#ceaa69"/>
    <text x="170" y="220" textAnchor="middle" fontSize="12" fontWeight="bold" fill="#98702e">F01–F07 验收</text>
    <path d="M170 231V242" stroke="#8291a8" markerEnd="url(#seqarr)"/>
    <rect x="65" y="245" width="210" height="28" rx="6" fill="#e1efe6" stroke="#87ad94"/>
    <text x="170" y="263" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#417553">试点通过后才允许扩展家族</text>
  </svg>
</box>

### 5.2 下一轮送审制品

{@body const items=[["dimension_conformance.json","参数正式定义、独立目标尺寸及异常面板定位"],["representation_contract.md","展开态、视觉态、碰撞代理验收契约"],["panel_topology_ledger.json","角点等价类、FOLD/JOIN/SEAL连接及未匹配项"],["blank_polygon_audit.json","二维面板交集、合法共享边及重叠裁决"],["uv_mapping_evidence/","面角对应与非对称诊断纹理"],["wp_a3_v1_results.json","F01–F07逐项验收"],["candidate_assets/","候选USD与manifest，不覆盖冻结资产"]]}
{@body const [checked,setChecked]=DIL.useState(items.map(()=>false))}
<card gap={2}>
  <row align="center">
    **WP-A3 v1 送审清单**
    <spacer/>
    <caption>{checked.filter(Boolean).length}/7</caption>
  </row>
  {#each items as a,i}
    <checkbox checked={checked[i]} onChange={v=>setChecked(old=>old.map((x,j)=>i===j?v:x))}>
      **{a[0]}**
      <caption>{a[1]}</caption>
    </checkbox>
  {/each}
  <button block variant="outline" color="secondary" onClick={()=>GenUI.copy(items.map((a,i)=>(checked[i]?"[x] ":"[ ] ")+a.join(" — ")).join("\n"))}><icon name="copy" size="sm"/> 复制执行清单</button>
</card>

既有 WP-REP-AUDIT、WP-V、WP1-v0.2 继续独立并行，不需要等待本试点全部完成。

---

## 六、需要沉淀的工程原则

本轮暴露的三个问题具有长期价值，建议纳入编译器知识库。

| 工程误区 | 应建立的原则 |
|---|---|
| 输出与中间结果一致，就证明输出正确 | 传递一致性不等于业务正确性 |
| 网格存在重叠，就进行统一净化 | 几何处理必须服从结构语义 |
| 一个商品必须对应一个闭合网格 | 同一商品允许多种用途明确的数字表达 |

我认为第三条尤其重要。

我们正在建设的是零售数字资产编译器，不是通用闭合网格生成器。真正的竞争力应该来自对商品结构、包装制造、视觉表达和物理用途的理解，以及在不同用途之间进行确定性编译的能力。

---

## 七、最终签核

| 裁决项 | 最终状态 |
|---|---|
| 双表达候选文件生成 | ACCEPTED |
| 编译尺寸保持 | PASS AS REPORTED |
| 真实商品尺寸正确性 | NOT CONFIRMED |
| blank 重复边根因 | PENDING SEMANTIC ARBITRATION |
| IR 解析焊接 | AUTHORIZED |
| Manifold repair 主路线 | DEFERRED |
| UV 正确性 | NOT CONFIRMED |
| WP-A3 单家族正确编译闭环 | NOT APPROVED |
| WP-A3 v1 整改 | AUTHORIZED |
| 批量重编译 | PROHIBITED |

本轮根据提交的 JSON 和实验摘要进行评审，未独立读取或执行 `51c259e` 源码，也未实际加载两个候选 USD 文件。因此上述签核是技术方案与报告级裁决，不是制品级独立验收。

**R09-05 FINAL VERDICT：CONDITIONAL PASS — AUTHORIZE SEMANTIC TOPOLOGY COMPILATION**

下一轮最优先解决的不是如何把12个开壳焊接起来，而是先证明这12个面板已经处于正确的折叠位置。

否则，焊接成功也可能只是得到了一个拓扑正确、商品结构错误的资产。