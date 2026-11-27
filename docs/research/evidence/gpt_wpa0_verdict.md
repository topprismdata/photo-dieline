### P0-02｜UV crack 分类器仍存在语义错误

v2 修复了单端匹配遗漏，这是正确的。但以下规则不能直接作为质量裁决：

| v2 匹配规则 | 我的裁决 |
|---|---|
| 两端均匹配 → 合法接缝 | 不充分，实际上仅能说明共享边两端 UV 坐标连续 |
| 恰一端匹配 → crack | 不成立，可能是合法 UV 图集切割 |
| 两端均不匹配 → 独立图集切割 | 不充分，也可能是非预期的纹理错位 |

<card gap={2}>
  <svg viewBox="0 0 340 145" width="100%">
    {#each [0,1,2] as i}
      <g transform={`translate(${i*113+8},8)`}>
        <path d="M8 80L48 15L48 80Z" fill="#d5e7fb" stroke="#547eb9" strokeWidth="1.5"/>
        <path d={i===0?"M48 15L88 15L48 80Z":i===1?"M65 15L102 15L48 80Z":"M68 5L103 13L68 69Z"} fill="#e5d9f8" stroke="#8d64c6" strokeWidth="1.5"/>
        <circle cx="48" cy="15" r="3" fill="#547eb9"/>
        <circle cx="48" cy="80" r="3" fill="#547eb9"/>
        <circle cx={i===0?48:i===1?65:68} cy={i===2?5:15} r="3" fill="#8d64c6"/>
        <circle cx={i===2?68:48} cy={i===2?69:80} r="3" fill="#8d64c6"/>
      </g>
    {/each}
    <g textAnchor="middle" fontSize="11" fill="currentColor">
      <text x="56" y="108">两端连续</text>
      <text x="169" y="108">单端连续</text>
      <text x="282" y="108">两端不连续</text>
      <text x="56" y="127" fill="#25845b">坐标连续</text>
      <text x="169" y="127" fill="#9a742c">待语义判定</text>
      <text x="282" y="127" fill="#9a742c">待语义判定</text>
    </g>
  </svg>
  <caption>同一几何共享边在 UV 空间中的三种映射关系。单端断开不必然是缺陷。</caption>
</card>

建议将分类器拆成两层：

| 层级 | 输出 |
|---|---|
| L1：客观测量 | CONTINUOUS / PARTIAL_DISCONTINUITY / FULL_DISCONTINUITY |
| L2：结构语义裁决 | EXPECTED_SEAM / UNEXPECTED_SEAM / UNKNOWN |

L1 只负责描述测量事实，L2 必须依据印刷区域、图集切割意图或三角化前的面角映射契约进行裁决。

还需要明确：端点必须按照**几何顶点身份**对应，而不是仅根据四个 UV 坐标之间的任意匹配来判断。否则交换两个面角也可能被误认为合法连续。

OpenUSD 官方规范允许 faceVarying primvar 表达 UV 接缝，索引型 primvar 还可以表达独立的属性共享拓扑。<Cite refs={["turn427412search0","turn427412search3"]}/>

因此，原报告中的“裂缝 0”需要降级为：

> 在当前检测规则下，未发现被分类为异常的单端 UV 不连续；接缝语义合法性尚未验证。

### P0-03｜顶点并查集不足以完成逐壳审计

两个立方体仅共享一个顶点时，顶点并查集可能将它们归入同一个连通分量，但这不能证明它们组成一个合法流形壳体。

<card gap={2}>
  <svg viewBox="0 0 330 130" width="100%">
    {#each [{x:12,y:13},{x:75,y:49},{x:180,y:13},{x:258,y:49}] as p}
      <g transform={`translate(${p.x},${p.y})`}>
        <path d="M0 18L32 0L63 18L31 36Z" fill="#c4ddf0" stroke="#587b9c"/>
        <path d="M0 18V54L31 72V36Z" fill="#adcbe8" stroke="#587b9c"/>
        <path d="M31 36L63 18V54L31 72Z" fill="#87afd7" stroke="#587b9c"/>
      </g>
    {/each}
    <circle cx="75" cy="67" r="5" fill="#d24d4d" stroke="white" strokeWidth="1.5"/>
    <text x="75" y="125" fontSize="10" textAnchor="middle" fill="currentColor">仅共享顶点</text>
    <text x="250" y="125" fontSize="10" textAnchor="middle" fill="currentColor">独立壳体</text>
  </svg>
  <caption>顶点连接关系不能替代面邻接关系和顶点局部流形检测。</caption>
</card>

必须补充三个独立检查：面通过共享边形成的连通分量、顶点邻域流形性、各壳体独立绕向与体积。

尤其不能把多个壳体的符号体积求和后统一判定。一个较大的正向壳体可能掩盖一个较小的反向壳体。

另外，闭壳正体积也不是局部绕向全部正确的充分条件。仍须检查共享边的方向一致性，并考虑实体内腔的壳体方向语义。

### P0-04｜USD 属性与往返检查仍未完成

上一轮明确要求验证 G03 的面角索引正确性、G05 的 USD 往返保持，以及负尺度变换下的绕向处理。本轮七例未覆盖这些要求。

OpenUSD 已提供 `UsdGeomPrimvar.ComputeFlattened()` 来解析索引型 primvar；USD 几何方向还需要结合 `orientation` 和变换矩阵处理。<Cite refs={["turn427412search5","turn427412search2"]}/>

建议直接采用官方 API 解析属性，不自行重新实现 USD 索引语义。

样本没有显式 normals 属性，可以将显式法线检查标记为 `NOT_APPLICABLE`，但不得声称法线正确性已通过验收。

---

## 二、7 例测试是否足够？

**不够。**

上一轮要求的16项测试尚未完整覆盖，而且本轮 N3 的预期判定本身需要修正。

不要求为了数量而增加大量重复用例。建议保留现有七例，修改 N3，再补充以下17例具有独立判别意义的测试。

### WP-A0.1 强制测试补充清单

| 编号 | 测试内容 | 预期结果 |
|---|---|---|
| T08 | 闭壳仅一个面绕向反转 | G02 FAIL |
| T09 | 合法三角形开壳，3 条边界边 | PASS |
| T10 | 同一条边被三个面共享 | G01 FAIL |
| T11 | 两个闭壳仅共享一个顶点 | 非流形顶点 FAIL |
| T12 | 两个独立正常闭壳 | 分别 PASS |
| T13 | 两个独立闭壳，其中一个反向 | 反向壳 FAIL |
| T14 | 合法闭壳与合法开壳混合 | 按各自契约裁决 |
| T15 | 三个不同索引构成共线几何三角 | 几何退化 FAIL |
| T16 | 合法 indexed faceVarying UV | PASS |
| T17 | UV indices 越界或长度错误 | G03 FAIL |
| T18 | UV 面角交换但面积仍非零 | 面角对应契约 FAIL |
| T19 | 合法单端 UV 不连续 | EXPECTED_SEAM |
| T20 | 非预期双端 UV 不连续 | UNEXPECTED_SEAM |
| T21 | 负尺度变换下的合法资产 | 按 USD 方向语义正确裁决 |
| T22 | USD 往返后 UV 属性丢失 | G05 FAIL |
| T23 | 三角化前后几何边界改变 | G01 边界保持 FAIL |
| T24 | 开壳但缺乏预期结构契约 | CONTRACT_UNKNOWN |

原有 N3 应增加两套契约断言：预期 SOLID 时 FAIL；明确允许该开口形态时才可以 PASS。

### 增加独立实现交叉检查

这是上轮要求、但本轮尚未交付的内容。

| 检查对象 | 独立参考实现 |
|---|---|
| 闭合性 | trimesh `is_watertight` |
| 绕向一致性 | trimesh `is_winding_consistent` |
| 符号体积 | trimesh 与人工解析值 |
| USD UV 索引解析 | pxr 官方 API |
| UV 连续性及面角对应 | 独立编写的人工真值断言 |

第三方工具也不是绝对真值。发生结果分歧时，必须回到人工可解析的几何构造与明确的结构契约进行仲裁。

本轮建议验收门槛：

- 24 个测试用例全部符合预先定义的预期。
- 独立参考实现的适用检查项全部一致，或存在经过解释的合理差异。
- 改变顶点编号、三角形排列顺序、整体平移等不改变结构语义的操作，不得改变相应质量裁决。
- 数值容差、坐标单位及退化判据提前冻结。
- 对非法输入、缺失属性和未知契约不得静默输出 PASS。

## 三、是否授权进入 WP-A1？

**授权开展探索性重判，不授权签发正式质量结论。**

具体权限如下：

| 操作 | 授权 |
|---|---|
| v2 对107件资产只读扫描 | 允许 |
| 收集原始几何观测数据 | 允许 |
| 对比 v1/v2 分类变化 | 允许 |
| 识别尚未登记的结构契约 | 允许 |
| 发布107件正式通过率 | 不允许 |
| 据此批量修复生产资产 | 不允许 |
| 覆盖9,386件冻结资产 | 不允许 |
| WP-A0.1通过后重新执行WP-A1 | 允许，作为正式送审候选 |

这样可以保持研究进度，不必让测量工具整改阻塞全部数据收集，同时避免把尚未校准的测量结果升级为正式工程结论。

---

## 四、下一步工作指派

新增一个短周期整改包 **WP-A0.1**，不扩大研究范围，不引入新的大型研发任务。

<card gap={3}>
  <caption>下一阶段任务依赖关系</caption>
  <svg viewBox="0 0 340 295" width="100%">
    <defs>
      <marker id="arrow9" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0 0L6 3L0 6Z" fill="#8190a3"/></marker>
    </defs>
    <rect x="65" y="5" width="210" height="38" rx="6" fill="#e3eaf8" stroke="#8c9fcc"/>
    <text x="170" y="20" fontWeight="bold" fontSize="12" textAnchor="middle" fill="#41577e">WP-A0.1 审计器收口</text>
    <text x="170" y="34" fontSize="10" textAnchor="middle" fill="#52678a">四项 P0 + 补充测试</text>
    <path d="M170 43V58H83V72 M170 58H257V72" fill="none" stroke="#8190a3" markerEnd="url(#arrow9)"/>
    <rect x="4" y="75" width="158" height="47" rx="6" fill="#e3eaf8" stroke="#8c9fcc"/>
    <rect x="178" y="75" width="158" height="47" rx="6" fill="#eae5fa" stroke="#a394d2"/>
    <text x="83" y="94" fontSize="11" fontWeight="bold" textAnchor="middle" fill="#41577e">24例真值测试</text>
    <text x="83" y="109" fontSize="10" textAnchor="middle" fill="#52678a">独立实现交叉检查</text>
    <text x="257" y="94" fontSize="11" fontWeight="bold" textAnchor="middle" fill="#625095">WP-A1 探索性扫描</text>
    <text x="257" y="109" fontSize="10" textAnchor="middle" fill="#625095">收集107件原始证据</text>
    <path d="M83 122V138H170V153 M257 122V138H170" fill="none" stroke="#8190a3" markerEnd="url(#arrow9)"/>
    <rect x="65" y="156" width="210" height="35" rx="6" fill="#fff1d9" stroke="#d0a453"/>
    <text x="170" y="177" fontSize="12" textAnchor="middle" fontWeight="bold" fill="#926923">G-A0 审计器验收门禁</text>
    <path d="M170 191V207" stroke="#8190a3" markerEnd="url(#arrow9)"/>
    <rect x="65" y="210" width="210" height="32" rx="6" fill="#e3eaf8" stroke="#8c9fcc"/>
    <text x="170" y="230" fontSize="11" fontWeight="bold" textAnchor="middle" fill="#41577e">WP-A1 正式重新审计</text>
    <path d="M170 242V258" stroke="#8190a3" markerEnd="url(#arrow9)"/>
    <rect x="65" y="261" width="210" height="30" rx="6" fill="#dcefe5" stroke="#86b59d"/>
    <text x="170" y="280" fontSize="11" fontWeight="bold" textAnchor="middle" fill="#397351">缺陷分类冻结 → 根因实验</text>
  </svg>
</card>

### 4.1 工作包及交付物

| 工作包 | 优先级 | 交付要求 |
|---|---|---|
| WP-A0.1 | P0 | 审计器 v2.1、24例真值测试、独立对照报告 |
| WP-A1 | P0 | 107件原始观测、契约映射及重新裁决 |
| WP-V | 并行 | 历史 Validator 身份与证据追溯，继续执行 |
| WP-P | 并行 | WP1-v0.2 冻结协议修订，继续执行 |
| WP-A2 | 等待A1相关结论 | D1 与购物车历史故障因果实验 |

### 4.2 下一轮送审文件

{@body const fs=[["auditor_core.py","v2.1 审计器源码"],["wp_a0_selftest.py","完整真值与负向测试"],["auditor_contract.md","观测、契约、裁决三层定义及数值容差"],["wp_a0_crosscheck.json","独立参考实现逐项对照结果"],["wp_a0_results.json","逐项原始测试输出"],["wp_a1_preview.json","107件探索性原始观测，不含正式质量签核"]]}
<card gap={2}>
  {#each fs as f}
    <row align="center">
      <icon name="file-code" color="secondary" size="lg"/>
      <box flex={1} gap=0>
        **{f[0]}**
        <caption>{f[1]}</caption>
      </box>
    </row>
  {/each}
  <button block variant="outline" color="secondary" onClick={()=>GenUI.copy(fs.map(f=>f.join(" — ")).join("\n"))}>复制送审清单</button>
</card>

下一轮应提交源码与可执行测试，而不只是文字报告。外部 LLM 阅读报告属于方法评审，不等于独立程序复现。

## 五、需要沉淀为长期工程资产的发现

本轮实际上发现了一个比三角化算法更重要的问题：**资产审计体系必须以结构语义为基础。**

建议正式确立以下三层架构，并纳入商品数字对象本体与编译器契约。

<box border radius="lg" padding={3} gap={2}>
  <box background="surface" border radius="md" padding={3}>
    <text color="secondary" size="xs">L1 · OBSERVATION</text>
    **客观几何观测**

    <text size="sm">边界、体积、绕向、连通性、UV 坐标、尺寸。</text>
  </box>
  <row justify="center"><icon name="arrow-down" color="secondary"/></row>
  <box background="surface" border radius="md" padding={3}>
    <text color="secondary" size="xs">L2 · CONTRACT</text>
    **结构与交付契约**

    <text size="sm">实体、开壳、展开图、印刷接缝、物理用途。</text>
  </box>
  <row justify="center"><icon name="arrow-down" color="secondary"/></row>
  <box background="surface" border radius="md" padding={3}>
    <text color="secondary" size="xs">L3 · VERDICT</text>
    **质量裁决**

    <text size="sm">PASS / FAIL / NOT_APPLICABLE / UNKNOWN</text>
  </box>
</box>

这三个层次不能混用。

如果审计器根据测量出来的实际形态反向决定资产应该是什么，那么几乎所有缺陷都有可能通过重新分类而被解释为合法结构。

这正是零售数字资产编译器区别于普通网格修复工具的一个重要能力：它不仅要知道几何是什么，还必须知道几何**应该是什么**。

---

## 六、最终签核

| 裁决项 | 结论 |
|---|---|
| D2 数学错误整改 | CLOSED |
| D3 闭壳/开壳契约 | OPEN |
| UV 分类器对称性修复 | ACCEPTED |
| UV 接缝语义正确性 | OPEN |
| 逐壳连通与流形检测 | OPEN |
| 7/7 自测结果 | ACCEPTED AS REPORTED |
| WP-A0 正式关闭 | NOT APPROVED |
| WP-A1 探索性执行 | AUTHORIZED |
| 下一送审对象 | WP-A0.1 |

本轮没有收到 `auditor_core.py` 和测试脚本原文，因此以上为设计与方法裁决，不是代码级独立验收。

**R09-01 FINAL VERDICT：CONDITIONAL PASS**

执行侧立即开展 WP-A0.1。本轮不再增加研究方向，集中关闭上述四项 P0，把审计器真正建设成可复现、可解释、可独立验收的质量测量工具。