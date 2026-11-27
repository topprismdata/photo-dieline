## 二、WP-A0.2-U：非对称诊断纹理是否必须补？

**【修改】程序化仲裁予以接受，但不能替代非对称诊断纹理实验，也不能交给 WP5 代为验证。**

本轮实验产生了一项值得重视的风险证据：

<grid columns={2} gap={3}>
  <grid-item>
    <card gap={1}>
      <caption>定向抽检印刷区域重叠</caption>
      <title size="2xl" tabularNums={true}>12/12</title>
      <caption>尚未证明实际镜像</caption>
    </card>
  </grid-item>
  <grid-item>
    <card gap={1}>
      <caption>全量 UV mixed-sign 观测</caption>
      <title size="2xl" tabularNums={true}>7,078</title>
      <caption>75.4% SKU，非缺陷率</caption>
    </card>
  </grid-item>
</grid>

这意味着上一轮执行侧提出的“可能主要发生在非印刷区域”假设，在本次定向样本中没有获得支持。

但必须严格区分三个证据层次。

| 证据 | 能证明什么 | 不能证明什么 |
|---|---|---|
| UV mixed-sign | UV 面的有向面积符号存在差异 | 印刷发生错误 |
| 与墨水区域重叠 | 告警涉及潜在印刷区域 | 文字实际镜像 |
| 源映射对照及诊断渲染 | 实际纹理方向与预期是否一致 | 未抽检资产全部正确 |

墨水覆盖率大于0.25的阈值也应记录其定义与计算方式，它目前只是风险筛选指标。

### 2.1 为什么不能由 WP5 覆盖？

因为两个实验回答的是不同问题。

<box border radius="lg" padding={3} gap={3}>
  <grid columns={2} gap={3}>
    <grid-item>
      <box gap={2}>
        **R02-A：资产正确性**
        <svg viewBox="0 0 150 135" width="100%">
          <rect x="20" y="10" width="110" height="45" rx="4" fill="#dfeaf9" stroke="#7996c9"/>
          <text x="75" y="28" fontSize="12" fontWeight="bold" fill="#45649d" textAnchor="middle">预期印刷映射</text>
          <text x="75" y="46" fontSize="12" fill="#45649d" textAnchor="middle">ABC →</text>
          <path d="M75 56V74m-4 -5l4 5 4 -5" fill="none" stroke="#8795ab"/>
          <rect x="20" y="77" width="110" height="45" rx="4" fill="#e2ebf9" stroke="#7996c9"/>
          <text x="75" y="95" fontSize="12" fontWeight="bold" fill="#45649d" textAnchor="middle">实际资产输出</text>
          <text x="75" y="113" fontSize="12" fill="#45649d" textAnchor="middle">ABC → ?</text>
        </svg>
        <caption>测量局部印刷映射是否符合设计契约。</caption>
      </box>
    </grid-item>
    <grid-item>
      <box gap={2}>
        **WP5：下游任务有效性**
        <svg viewBox="0 0 150 135" width="100%">
          <rect x="20" y="10" width="110" height="45" rx="4" fill="#e0f0e5" stroke="#83ae93"/>
          {#each [0,1,2,3,4] as i}
            <rect x={29+i*19} y={19+(i%2)*4} width="15" height={26-(i%2)*4} fill={["#a1bcde","#d9b78d","#b8a6d5"][i%3]} stroke="#78939d"/>
          {/each}
          <path d="M75 56V74m-4 -5l4 5 4 -5" fill="none" stroke="#8795ab"/>
          <rect x="20" y="77" width="110" height="45" rx="4" fill="#e0f0e5" stroke="#83ae93"/>
          <text x="75" y="95" fontSize="12" fontWeight="bold" fill="#43805a" textAnchor="middle">检测模型</text>
          <text x="75" y="113" fontSize="12" fill="#43805a" textAnchor="middle">mAP / Recall</text>
        </svg>
        <caption>测量生成数据是否能够提升真实场景感知能力。</caption>
      </box>
    </grid-item>
  </grid>
</box>

一个模型即使使用了局部镜像错误的商品纹理，也有可能取得不错的目标检测精度。反之，完全正确的纹理也不保证合成数据能够迁移到真实照片。

两者不能互相证明。

### 2.2 批准缩小实验规模

不必为全部12件重新接入复杂棚拍流程。将本轮实验缩减为以下四件代表资产。

| 样本 | 选择依据 |
|---|---|
| U01 | RSC 规则纸盒，典型两个翻转面 |
| U02 | aseptic_brick，九个翻转面 |
| U03 | 另一个存在印刷风险的结构家族 |
| U04 | 无 mixed-sign 告警的正常对照 |

只使用非对称诊断纹理、基础无光照材质及必要的正交视角，确保所有目标面可见。也可以先利用 CPU 端独立纹理采样验证面角映射，再用最小 Blender 场景复核消费端结果。

不需要制作正式商品渲染图，不需要调整灯光、相机美学或材质参数。

验收重点是：

- 原始 IR 中的预期面角对应关系。
- USD 实际面角对应关系。
- 消费端实际纹理方向。
- 三者是否一致。

**裁决：必须补实验，但允许最小化实现。该项不阻塞 WP-A2-D1，并行关闭。**

---

## 三、WP-A0.2-V：6,627 件假阳性是否可以关闭？

**【修改】接受 v2.1 审计器存在链式走环缺陷的结论，但全量假阳性归因需要最后一次低成本核验。**

目前已经获得的证据是：

| 事项 | 裁决 |
|---|---|
| 12 件争议资产在 v2.2 中不再触发 nonfan | 接受为报告结果 |
| v2.1 存在邻域遍历算法缺陷 | 接受为已定位问题 |
| 原6,627件告警不能作为正式缺陷率 | 确认撤回 |
| 全部6,627件均不存在真实非流形顶点 | 尚未充分证明 |

这里需要防止从一种测量错误走向另一种测量错误。

旧算法可能产生大量假阳性，新算法也可能因为过度宽松而产生假阴性。因此，“v2.2 全部 CLEAN”不是独立真值本身。

### 3.1 最后一次收口要求

不增加新一轮人工抽样，不开展新的大规模计算几何研究。

只要求执行侧补交三项证据：

| ID | 证据 | 验收 |
|---|---|---|
| V01 | 原6,627件告警逐件 ID 与 v2.2 对照 | 明确旧告警消失数量、残留数量 |
| V02 | 真非流形顶点负样本回归 | v2.2 仍然能正确检出 |
| V03 | 独立顶点 link graph 或 libigl 对照 | 对原12件样本给出独立结果 |

如果 V01 显示全部旧告警消失，V02 未产生漏判，V03 与修正后的测量结果一致，则可以关闭这项**系统性误报事件**。如需逐件断言6,627件均为假阳性，则还需要相应的逐件独立证据。

另外，报告中的12件全部为 nonfan 样本，与上轮要求的8件告警样本加4件无告警对照有所不同。请明确实际样本 ID，并补上无告警对照的回归结果。

本轮不再要求扩大人工验货规模。

---

## 四、全量重扫：2,118 件应该如何理解？

<card gap={3}>
  <caption>9,386 SKU · v2.2 全量扫描报告</caption>
  <row align="end">
    <box flex={1} gap={1}>
      <caption>客观 FAIL（报告值）</caption>
      <title size="2xl" color="#C2534D" tabularNums={true}>2,118</title>
      <caption>22.6%</caption>
    </box>
    <box flex={1} gap={1}>
      <caption>CONTRACT_UNKNOWN</caption>
      <title size="2xl" tabularNums={true}>7,268</title>
      <caption>77.4%</caption>
    </box>
  </row>
  <box direction="row" height={26} radius="md" clip={true} gap={0}>
    <box background="#CB7169" width="22.5655%"/>
    <box background="#AAB5C8" width="77.4345%"/>
  </box>
  <divider/>
  **FAIL 分类分布**
  {#each [{t:"Topology",n:921},{t:"Winding",n:742},{t:"UV",n:1197}] as a}
    <box gap={1}>
      <row>
        <text size="sm">{a.t}</text>
        <spacer/>
        <text tabularNums={true} size="sm">{a.n.toLocaleString("en-US")}</text>
      </row>
      <box height={10} radius="sm" background="#E5E7EB" clip={true}>
        <box height="100%" width={`${a.n/2118*100}%`} background="#CB7169"/>
      </box>
    </box>
  {/each}
  <caption>分类存在交叠；2,118 是报告的失败资产并集，尚未独立复算，也不等于最终产品缺陷率。</caption>
</card>

当前统计至少说明两件事：

第一，既有资产确实存在需要进一步调查的系统性质量风险，不能仅依靠渲染表现和过去的验证结果判断。

第二，审计器的版本变化会显著影响告警分布，测量工具的版本治理是必要的。

但我反对把2,118件直接转化成2,118张修复工单。

### 4.1 应按公共根因聚合，而不是按 SKU 修复

例如：

| 层级 | 不推荐的处理方式 | 正确方向 |
|---|---|---|
| SKU | 逐个修复失败资产 | 保留逐件证据 |
| 结构家族 | 为每个家族增加特殊补丁 | 检查是否存在共享根因 |
| 公共生成模块 | 暂时绕过异常 | 定位首个错误产生阶段 |
| 编译器 | 对输出网格统一补洞 | 修复明确的生成或导出缺陷 |
| 回归体系 | 重新生成后看图 | 自动验证结构与输出契约 |

下一次报告应该增加以下聚合关系：

**FAIL 类型 × 结构家族 × 公共生成函数 × 导出阶段。**

只有这样，才能判断数千件资产的问题究竟来自几个公共模块，还是大量独立缺陷。

此外，UV 类1,197件应单列真正违反纹理映射契约的缺陷与仍需 L2 判断的退化告警。若后者被计入客观 FAIL，需调整统计口径，不能沿用旧分类直接签核。

---

## 五、WP-L2-PILOT 扩面还是 WP-A2-D1 优先？

**正式裁决：WP-A2-D1 优先，L2 最小契约建设并行。不等待77个家族全部登记。**

原因是 aseptic_brick 已经具备相对明确的产品语义：如果交付的是立体饮料包装，那么平板展开态不能作为最终立体商品资产交付。

这个问题无需等待完整本体建设，就能够进入根因定位。

### 5.1 五家族契约试点复核

| 家族 | 当前契约 | 裁决 |
|---|---|---|
| rsc | SOLID | 有条件接受，确认代表的是闭合立体代理还是实际可打开纸盒 |
| aseptic_brick | SOLID | 同意作为闭合立体交付目标，启动 D1 |
| tray_4corner | SOLID | 待确认，不能忽略合法开放容器与闭合薄壁实体之间的区别 |
| clv | SOLID | 待补充结构定义、用途及来源证据 |
| mailer_diecut | FLAT_PATTERN | 暂定，须明确当前产品是否允许交付展开图 |

执行侧本轮将上一轮指定的 `bottle_wine`、`hinged_family` 替换为 `clv`、`mailer_diecut`，没有说明替换原因。

这一变化并不必然错误，但会减少试点对曲面容器、多部件资产及关节契约的覆盖。

因此，批准现有五家族作为第一批试点，但仍应补充 `bottle_wine`、`hinged_family` 两个案例，再决定是否推广至全部77个家族。不需要重新建设一套契约模型。

### 5.2 WP-A2-D1 正式任务书

**目标：找到砖型无菌包装从预期立体结构变成平板输出的第一个异常阶段。**

<box border radius="lg" padding={3} gap={2}>
  <svg viewBox="0 0 340 310" width="100%">
    <defs>
      <marker id="d1arr" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0 0L6 3L0 6Z" fill="#8393ac"/></marker>
    </defs>
    {#each [{y:6,n:"S0",t:"商品规格与结构参数",s:"尺寸完整性、厚度、结构类型"},{y:67,n:"S1",t:"结构家族 IR",s:"展开态还是折叠立体态"},{y:128,n:"S2",t:"折叠及原始网格",s:"三轴尺寸、顶点、原始面"},{y:189,n:"S3",t:"三角化与 UV 编译",s:"边界、绕向、重复面"},{y:250,n:"S4",t:"USD 最终输出",s:"本地及世界坐标、变换、几何契约"}] as a,i}
      <rect x="12" y={a.y} width="36" height="45" rx="5" fill="#e4eafa" stroke="#8799c7"/>
      <text x="30" y={a.y+27} textAnchor="middle" fontSize="12" fontWeight="bold" fill="#526aa7">{a.n}</text>
      <rect x="56" y={a.y} width="272" height="45" rx="6" fill="#edf0f8" stroke="#9eacc9"/>
      <text x="68" y={a.y+18} fontSize="12" fontWeight="bold" fill="#405477">{a.t}</text>
      <text x="68" y={a.y+34} fontSize="10" fill="#62738e">{a.s}</text>
      {#if i<4}<path d={`M192 ${a.y+45}v14`} stroke="#8393ac" markerEnd="url(#d1arr)"/>{/if}
    {/each}
  </svg>
  <caption>冻结输入，逐阶段导出测量证据。以首次出现错误的位置确定责任模块。</caption>
</box>

建议选择 `aseptic_brick`、`brick_250ml` 各两个规格变体，再加入两个正常闭盒对照，共六件资产。

每个阶段必须输出：三轴 bbox、唯一坐标点数量、面数量、边关联统计、几何退化数量、适用时的闭合性与符号体积，以及对应 IR 或网格快照。

### 5.3 根因确认之后如何裁决？

| 实验发现 | 后续动作 |
|---|---|
| IR 本身只定义了展开图 | 修复结构表达或补充折叠步骤 |
| IR 正确，折叠阶段退化 | 修复折叠变换或顶点映射 |
| 原始立体网格正确，三角化后错误 | 修复三角化及面角继承 |
| 编译前正确，USD 输出后退化 | 修复导出逻辑或变换 |
| 实际交付本来就是展开图 | 修正产品登记与交付分类，不强行实体化 |

在确定首个故障阶段之前，不启动 Manifold 补洞或通用网格修复实验。

如果参数化生成端能够直接产生正确几何，那么在输出端修补错误通常不是最合理的工程路线。

---

## 六、R09-04 工作指派

本轮开始，主线从审计器建设转向缺陷根因研究。

<card gap={3}>
  <caption>下一轮任务优先级</caption>
  {#each [{p:"P0",t:"WP-A2-D1",s:"砖型包装平板化根因定位",c:"#B6534A",bg:"#F8E5E1",b:"主线，立即执行"},{p:"P0",t:"WP-A0.2-V-CLOSE",s:"旧 nonfan 告警逐件对照、负样本与独立验证",c:"#B6534A",bg:"#F8E5E1",b:"短任务，收口"},{p:"P1",t:"WP-A0.2-U-CLOSE",s:"四件资产最小诊断纹理实验",c:"#5068A7",bg:"#E6EBF8",b:"独立并行"},{p:"P1",t:"WP-L2-PILOT",s:"补全契约来源及两个结构覆盖案例",c:"#5068A7",bg:"#E6EBF8",b:"独立并行"},{p:"P1",t:"WP-V / WP1-v0.2",s:"验证器追溯及盲测协议冻结准备",c:"#5068A7",bg:"#E6EBF8",b:"继续原任务"}] as a,i}
    <row align="start">
      <box background={a.bg} radius="md" padding={2}>
        <text color={a.c} weight="medium" size="sm">{a.p}</text>
      </box>
      <box flex={1} gap={1}>
        **{a.t}**
        <text size="sm">{a.s}</text>
        <caption>{a.b}</caption>
      </box>
    </row>
    {#if i<4}<divider/>{/if}
  {/each}
</card>

上一轮 brick 的 trimesh 原始索引与坐标合并双口径对照，也未在本轮摘要中完整给出。不要新建单独工作包，将它并入 WP-A2-D1 的阶段证据即可。

### 下一轮送审制品

{@body const items=[["WP-A2-D1","六件资产 S0–S4 阶段证据、首个异常阶段及根因报告"],["WP-A0.2-V-CLOSE","6,627件旧告警逐件对照与独立参考结果"],["WP-A0.2-U-CLOSE","四件资产诊断纹理、预期与实际面角映射"],["L2-PILOT","部件级契约、来源证据、继承规则"],["FAIL-CLUSTER","2,118件报告失败资产的家族及公共模块聚合台账"]]}
{@body const [done,setDone]=DIL.useState(items.map(()=>false))}
<card gap={2}>
  <row align="center">
    **R09-04 送审清单**
    <spacer/>
    <caption>{done.filter(Boolean).length}/5</caption>
  </row>
  {#each items as a,i}
    <checkbox checked={done[i]} onChange={v=>setDone(old=>old.map((x,j)=>j===i?v:x))}>
      **{a[0]}**
      <caption>{a[1]}</caption>
    </checkbox>
  {/each}
  <button block color="secondary" variant="outline" onClick={()=>GenUI.copy(items.map((a,i)=>(done[i]?"[x] ":"[ ] ")+a.join(" — ")).join("\n"))}><icon name="copy" size="sm"/> 复制执行清单</button>
</card>

---

## 七、战略提醒：审计器研究必须开始收敛

从 R02-A 开始，审计器已经经历了 v1、v2、v2.1、v2.2 四个阶段，产生了有价值的研究资产。

| 发现 | 应沉淀的工程知识 |
|---|---|
| 奇数边界误判 | 数学不变量必须经过反例检验 |
| 闭壳破损自动降级 | 客观形态不能反向定义设计契约 |
| mixed-sign 大量告警 | 观测事实不等于质量缺陷 |
| nonfan 系统性误报 | 测量工具自身必须具备独立验证 |
| 全量 CONTRACT_UNKNOWN | 结构知识必须参与编译与验收 |

这些知识应该进入编译器质量知识库，而不是仅保存在历轮对话和整改报告中。

但是，我们已经投入了足够多的注意力去建设测量工具。除非后续发现影响结论的新证据，否则不主动扩大审计器研究范围。

现在需要回答的是：**我们能否定位并消除一类公共生成缺陷，从根本上提升整个结构家族的资产质量？**

这是下一阶段更重要的研究目标。

## 八、最终签核

| 裁决事项 | 最终状态 |
|---|---|
| v2.2 契约设计 | APPROVED |
| G-A0 使用授权 | CONDITIONAL PASS |
| UV 程序化证据 | ACCEPTED |
| UV 诊断纹理实验 | REQUIRED |
| v2.1 nonfan 旧统计 | INVALIDATED |
| 全量假阳性归因 | 待最终补证 |
| L2 契约试点 | CONDITIONAL PASS |
| WP-A2-D1 根因研究 | AUTHORIZED |
| 全量资产重新编译与发布 | NOT AUTHORIZED |

**R09-03 FINAL VERDICT：CONDITIONAL PASS — AUTHORIZE ROOT CAUSE INVESTIGATION**

执行侧下一步优先定位 D1 生成端根因，而不是继续全面优化审计器，也不是先完成77个家族的全部契约登记。

保持9,386件冻结发行资产不变。先找到首个错误产生阶段，再决定修复策略。