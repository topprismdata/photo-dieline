## 二、P0-02｜方向规范化门控实现

**【修改后同意】默认 `False` 符合暂不全局启用的授权约束；但功能开关不等于算法安全门禁。**

本次以下设计予以接受。

| 实现项 | 裁决 |
|---|---|
| normalize_orientation 默认 False | PASS |
| 试点显式开启 | PASS |
| 几何索引与 faceVarying UV 同步反转 | APPROVED AS REPORTED |
| customData 记录规范化意图 | APPROVED |
| normals 缺失时 NOT_APPLICABLE | APPROVED |
| 仅依据负体积触发整体翻转 | 不充分 |

### 2.1 必须增加规范化前置条件

不能将当前方案简化为：

```python
if normalize_orientation and signed_volume < 0:
    reverse_faces()
```

原因是负体积可能来自局部绕向混乱、多壳体方向抵消、内腔、错误变换或者其他不满足实体契约的情况。

推荐的逻辑是：

```python
if normalize_orientation:
    require_solid_contract()
    require_closed_mesh()
    require_consistent_winding()
    require_valid_geometry()
    require_supported_shell_configuration()

    if signed_volume < -volume_tolerance:
        reverse_face_indices()
        reverse_facevarying_attributes()
```

上述为逻辑示意，并非可直接投入生产的完整代码。

本轮只要求支持已明确的单闭壳 brick 试点。遇到多壳体、内腔或尚未处理的方向变换语义，可以直接拒绝规范化，不需要立即研发通用解决方案。

### 2.2 增加四类最小负向测试

| 编号 | 输入 | 预期 |
|---|---|---|
| N-ORI-01 | 局部绕向混乱的负体积网格 | 不允许直接整体翻转后宣告 PASS |
| N-ORI-02 | 开放曲面或零体积网格 | 拒绝 SOLID 外向规范化 |
| N-ORI-03 | 已正确外向的闭壳 | 不修改几何及面角属性 |
| N-ORI-04 | 不支持的多壳体或内腔 | 明确拒绝或登记待处理 |

另需验证规范化重复执行的幂等性：已经正确外向的资产再次执行规范化，不应发生第二次翻转。

### 2.3 customData 不替代 USD 标准属性

`normalized-outward` 作为审计元数据是合理的，但仍需核对实际 `orientation` 声明、面绕向和坐标变换是否一致。

同样，`normals NOT_APPLICABLE` 只表示没有显式法线属性需要同步处理，不代表消费端计算的法线已经正确。

**P0-02 最终裁决：门控设计通过，安全前置条件及实际面角回归待补。**

---

## 三、P0-03｜T25 是否可以永久固化？

**【同意】批准 T25 纳入永久回归测试。但不接受它代替具体 SKU 的几何不变量验证。**

T25 是一个很好的反例测试。

<box border radius="lg" padding={3} gap={2}>
  <svg viewBox="0 0 340 190" width="100%">
    <g transform="translate(15,12)">
      <rect x="8" y="5" width="132" height="132" rx="3" fill="none" stroke="#9aa7ba" strokeDasharray="5 4"/>
      <path d="M28 46L75 20L121 45L73 71Z" fill="#d1def5" stroke="#6f87b8"/>
      <path d="M28 46L73 71V127L28 100Z" fill="#e0e8f8" stroke="#6f87b8"/>
      <path d="M73 71L121 45V100L73 127Z" fill="#aabfe4" stroke="#6f87b8"/>
    </g>
    <g transform="translate(185,12)">
      <rect x="8" y="5" width="132" height="132" rx="3" fill="none" stroke="#9aa7ba" strokeDasharray="5 4"/>
      <path d="M74 15L25 72L75 140L124 72Z" fill="#ddd3f1" stroke="#9078bd"/>
      <path d="M74 15L75 82L124 72Z" fill="#bca9e0" stroke="#9078bd"/>
      <path d="M25 72L75 82L75 140Z" fill="#cbbce9" stroke="#9078bd"/>
      <path d="M75 82L124 72L75 140Z" fill="#a995d4" stroke="#9078bd"/>
      <path d="M74 15L25 72L75 82Z" fill="#e6def6" stroke="#9078bd"/>
    </g>
    <g fill="currentColor" fontSize="12" textAnchor="middle">
      <text x="90" y="165" fontWeight="bold">单位立方体</text>
      <text x="90" y="181">V = 1</text>
      <text x="260" y="165" fontWeight="bold">同 bbox 八面体</text>
      <text x="260" y="181">V = 1/6</text>
    </g>
  </svg>
  <caption>示意：两个网格可以拥有相同的轴对齐包围盒，但内部几何与体积完全不同。</caption>
</box>

问题在于，上轮要求的 P0-03 是：

> 证明 aseptic_brick 修复前后只改变绕向，没有改变商品几何与印刷映射。

而 T25 证明的是：

> 审计器能够区分具有相同 bbox、不同体积的几何对象。

两者不是同一个验收命题。

### 必须增加实际资产对照台账

| 不变量 | S0→S1 家族修复 | S1→S2 方向规范化 |
|---|---|---|
| 顶点坐标集合 | 必须验证 | 必须验证 |
| 无向三角面多重集合 | 必须验证 | 必须验证 |
| 表面积 | 必须验证 | 必须验证 |
| 三轴 bbox | 已报告一致 | 已报告一致 |
| 面板身份 | 必须验证 | 必须验证 |
| 材质绑定 | 必须验证 | 必须验证 |
| 几何顶点与 UV 面角对应 | 必须验证 | 必须验证 |
| 符号体积 | 允许变化 | 仅符号翻转 |

建议对每个三角面的三个空间坐标进行规范排序后建立多重集合比较，避免顶点重新编号影响几何等价判断，也避免遗漏重复面数量变化。

对于 UV，则比较对应的几何面角与纹理坐标组合，而不是仅比较两组 UV 数值集合。

**本轮无需新增复杂测试框架。直接对 S0、S1、S2 三个制品生成一份 `geometry_invariance.json` 即可。**

P0-03 最终状态：

```text
T25_REGRESSION = APPROVED
SKU_GEOMETRY_INVARIANCE = PENDING_EVIDENCE
```

---

## 四、WP1-Pilot-100 v0.2 正式协议审查

**裁决：REVISE BEFORE FREEZE。**

本轮协议比 v0.1 有明显进步，但我必须指出：虽然执行侧声明八项 P0 全部修订，实际仍有多项没有按原裁决落实。

### 4.1 原八项 P0 逐条复核

| 原门禁 | v0.2 状态 | 裁决理由 |
|---|---|---|
| P0-01 输入不足与超域分离 | 未解决 | 七种终态中没有 INPUT_INSUFFICIENT |
| P0-02 互斥完备终态 | 未解决 | 缺少 FAMILY_NOT_COVERED，NOT_APPLICABLE 不应是商品终态 |
| P0-03 四层成功率 | 未解决 | M2 分母矛盾、M4 公式错误、缺少明确的输入可用率 |
| P0-04 真实商品一致性 | 部分解决 | 尺寸阈值已定义，但结构、封合形态、印刷最终裁决仍不完整 |
| P0-05 合法输入与隔离 | 部分解决 | 编译器版本已冻结，但样本总体、抽样脚本、种子及泄漏检查未完整登记 |
| P0-06 统计方法 | 未解决 | 仍要求所有指标使用精确二项置信区间 |
| P0-07 经济成本 | 基本解决 | 成本公式正确，还需零成功分母及失败成本归属规则 |
| P0-08 环境未完成语义 | 基本解决 | VALIDATION_PENDING 定义正确，但 M4 与其发生数学冲突 |

附加事项：

| 事项 | 裁决 |
|---|---|
| WP1-Pilot-100 命名 | APPROVED |
| DIM-01 的 1mm / 1% 阈值 | 可作为 Pilot 冻结候选 |
| 无真实质量数据不得宣称质量已验证 | APPROVED |
| 无铰接商品不执行铰接门禁 | APPROVED |

---

## 五、WP1 必须修改的核心问题

### 5.1 七种终态必须重新整理

现有协议缺少两个非常重要的失败来源：

一是真实商品输入规格不足，二是现有结构家族根本无法覆盖该商品。

这两个状态恰恰是 WP1 应该测量的能力缺口，不能遗漏。

另外，`NOT_APPLICABLE` 应是单项门禁状态，不是整个 SKU 的最终状态。

建议冻结以下八种终态：

| 终态 | 定义 |
|---|---|
| OUT_OF_SCOPE | 不属于预先冻结的产品适用域 |
| INPUT_INSUFFICIENT | 域内商品，但缺少必需合法输入 |
| FAMILY_NOT_COVERED | 输入充分，无适用结构家族 |
| FAMILY_ADAPTATION_REQUIRED | 存在候选家族，但必须修改模板 |
| CONTRACT_UNKNOWN | 家族适用，但必要交付契约无法判定 |
| GATE_FAIL | 生成失败或任一必需门禁明确失败 |
| VALIDATION_PENDING | 尚无明确失败，但必需验证未完成 |
| SUCCESS | 所有适用的必需门禁通过 |

所有终态必须互斥，总计恰好100件。

若某件商品已经有一个必需门禁 FAIL，即使另一个验证尚未运行，也应归为 `GATE_FAIL`，不能放入 `VALIDATION_PENDING` 隐藏失败。

### 5.2 M2 存在分母矛盾

当前正文写的是：

> 首次编译即 SUCCESS 的样本数 / 命中样本数

但分母列又写成 M1 分母，即100减去域外样本。

这两个指标含义不同：

- 除以命中数，是条件生成成功率。
- 除以域内样本数，是端到端交付率。

不能共用一个指标名称。

### 5.3 M4 公式错误

当前定义：

\[
M4=\frac{SUCCESS-VALIDATION\_PENDING}{N_{\mathrm{domain}}}
\]

由于 SUCCESS 和 VALIDATION_PENDING 已经是互斥终态，再进行相减没有统计意义，甚至可能产生负数。

下面提供一个可用于协议负向测试的示例。

{@body const states=[{t:"域外",v:5},{t:"输入不足",v:10},{t:"家族未覆盖",v:20},{t:"需要改造",v:10},{t:"契约未知",v:5},{t:"门禁失败",v:15},{t:"验证待完成",v:10},{t:"成功",v:25}]}
<card gap={3}>
  <caption>WP1 指标公式测试 · 假设100件样本，非实测结果</caption>
  <box direction="row" gap={0} height={24} radius="md" clip={true}>
    {#each states as a,i}
      <box width={`${a.v}%`} background={["#CCD2DC","#AAB7CA","#CF8075","#DDB176","#A695C8","#B85D59","#E0C78C","#659C7B"][i]}/>
    {/each}
  </box>
  <grid columns={2} gap={2}>
    {#each states as a,i}
      <grid-item>
        <row align="center">
          <box size="9px" radius="sm" background={["#CCD2DC","#AAB7CA","#CF8075","#DDB176","#A695C8","#B85D59","#E0C78C","#659C7B"][i]}/>
          <text size="sm">{a.t}</text>
          <spacer/>
          **{a.v}**
        </row>
      </grid-item>
    {/each}
  </grid>
  <divider/>
  <grid columns={2} gap={3}>
    <grid-item>
      <caption>输入可用率</caption>
      <title size="xl" tabularNums={true}>89.5%</title>
      <caption>85 / 95</caption>
    </grid-item>
    <grid-item>
      <caption>无需改造的结构覆盖率</caption>
      <title size="xl" tabularNums={true}>64.7%</title>
      <caption>55 / 85</caption>
    </grid-item>
    <grid-item>
      <caption>条件生成成功率</caption>
      <title size="xl" tabularNums={true}>45.5%</title>
      <caption>25 / 55</caption>
    </grid-item>
    <grid-item>
      <caption>端到端交付率</caption>
      <title size="xl" tabularNums={true}>26.3%</title>
      <caption>25 / 95</caption>
    </grid-item>
  </grid>
  <divider/>
  <row align="center">
    <box flex={1}>
      <caption>当前 M4 错误公式</caption>
      <title size="lg" color="danger">15.8%</title>
      <caption>(25 − 10) / 95</caption>
    </box>
    <box flex={1}>
      <caption>实际域内成功交付率</caption>
      <title size="lg">26.3%</title>
      <caption>25 / 95</caption>
    </box>
  </row>
</card>

### 5.4 推荐直接采用以下冻结指标

不要继续使用含义模糊的 M1–M4 旧定义。

设：

- \(N_d\)：域内样本数。
- \(N_i\)：输入充分的域内样本数。
- \(N_f\)：无需改造即可表达的样本数。
- \(N_s\)：首次冻结编译尝试中完整验收成功的样本数。

| 指标 | 公式 |
|---|---|
| M1 输入可用率 | \(N_i/N_d\) |
| M2 结构覆盖率 | \(N_f/N_i\) |
| M3 条件一次交付成功率 | \(N_s/N_f\) |
| M4 端到端交付率 | \(N_s/N_d\) |
| M5 单位成功交付成本 | 全部实际成本 / 成功数 |

四层能力指标应满足以下闭合关系：

\[
M4=M1\times M2\times M3
\]

前提是各计数集合使用相同口径，且分母非零。

这可以直接固化为统计脚本门禁，用来发现分母漂移。

验证完备率作为辅助指标单独报告：

\[
R_{\mathrm{validation}}=
\frac{\text{已完成全部适用必需外部验证的候选数}}
{\text{进入外部验证阶段的候选数}}
\]

完成验证不等于通过验证，验证通过率另行统计。

若任一指标分母为0，登记 `UNDEFINED`，不得报告为0%或100%。

---

## 六、真实商品一致性门禁复核

### 6.1 DIM-01：批准作为 Pilot 阈值

逐轴：

\[
|\hat d-d|\leq\max(1\text{ mm},0.01d)
\]

这个阈值可以作为首轮零售数字资产 Pilot 的工程验收标准，但不是制造级尺寸公差，也不是通用行业标准。

{@body const [dim,setDim]=DIL.useState("57.3")}
{@body const d=Number(dim)}
<card gap={3}>
  **DIM-01 尺寸容差验证器**
  <label>目标商品尺寸（mm）</label>
  <input inputType="number" value={dim} onChange={setDim}/>
  {#if Number.isFinite(d)&&d>0}
    <grid columns={2}>
      <grid-item>
        <caption>允许绝对误差</caption>
        <title size="2xl" tabularNums={true}>±{Math.max(1,d*.01).toFixed(3)}</title>
        <caption>mm</caption>
      </grid-item>
      <grid-item>
        <caption>允许相对误差</caption>
        <title size="2xl" tabularNums={true}>{(Math.max(1,d*.01)/d*100).toFixed(2)}%</title>
      </grid-item>
    </grid>
    <divider/>
    <caption>合格输出范围</caption>
    **{(d-Math.max(1,d*.01)).toFixed(3)} – {(d+Math.max(1,d*.01)).toFixed(3)} mm**
  {:else}
    <caption>请输入有效的正数尺寸。</caption>
  {/if}
</card>

但必须明确参考尺寸来自真实成品外轮廓，而不是生成器内部参数或自产资产的解析 bbox。

此前 brick 的研究已经充分暴露了这个风险。

### 6.2 QUAL-01：无数据不等于不适用

需要纠正以下语义：

> 无真实实测质量数据 → NOT_APPLICABLE。

质量对于物理商品通常是适用属性，只是当前缺乏真实测量证据。

应该区分：

| 情况 | 状态 |
|---|---|
| 商品没有铰接结构 | NOT_APPLICABLE |
| 商品存在质量属性，但没有实测质量 | REFERENCE_UNAVAILABLE |
| 实测质量存在，但候选尚未验证 | NOT_RUN |
| 实测与候选质量符合阈值 | PASS |

可以冻结一个不要求真实质量实测的基础交付等级，但必须限制成功声明的含义。

例如，基础视觉资产成功不代表真实质量已经验证；物理交付等级则必须具备相应的质量及碰撞参数验收依据。

### 6.3 ART-01：同意

无铰接结构的商品，其铰接专项门禁确实不适用。

这一项可以关闭。

### 6.4 PRINT-01：仍然是风险识别，不是完整门禁

`PRINT_MIRROR_RISK` 只是提示可能存在印刷方向风险。

此前 R02-A 的大量 mixed-sign 告警已经证明，不能仅凭 UV 符号或墨水区域重叠直接裁决镜像错误。

应明确最终状态：

| 情况 | 裁决 |
|---|---|
| 预期印刷区域及面角映射一致 | PASS |
| 已确认镜像、错位或错误图案 | FAIL |
| 缺少必要印刷参考 | REFERENCE_UNAVAILABLE |
| 尚未完成验证 | NOT_RUN |

如果 WP1 只接收匿名尺寸，没有合法的真实商品印刷输入，那么就不能同时宣称测试了真实商品级印刷还原能力。

### 6.5 增加两项必要门禁

| 门禁 | 内容 |
|---|---|
| STR-01 | 商品包装结构、形态及预期结构家族一致性 |
| ASM-01 | 成品开口、封合、盖件及关键装配状态一致性 |

一个尺寸完全正确的长方体，不一定就是目标真实商品。

这两项门禁不要求复杂的自动视觉识别，可以由独立评测侧依据预先冻结的参考证据进行逐件判定。

---

## 七、抽样、隔离、统计及成本

### 7.1 抽样协议仍需补齐

v0.2 没有完整保留 v0.1 的分层随机抽样规则。100件真实商品如何选出，是实验能否代表实际需求的关键。

冻结前必须登记：

| 冻结项 | 要求 |
|---|---|
| 商品主数据总体 | 来源、范围、版本及哈希 |
| 分层规则 | 品类 × 包装形态 |
| 抽样规则 | 分层分配、随机种子、抽样脚本哈希 |
| 去重规则 | GTIN、商品系列及近似规格变体 |
| 产品适用域 | 先于抽样冻结 |
| 合法输入字段 | 尺寸、结构类别、材质、印刷图等允许字段 |
| 保留评测数据 | 独立参考图、真实测量值、人工结构标签 |
| 未见性证据 | 样本未参与家族设计、调参或训练 |

还需要区分两个研究问题：

**已知结构家族内的未见 SKU 泛化**，与**未覆盖结构家族的识别和拒绝能力**。

两者都应该在 Pilot 中体现，而不能把第二类样本排除出覆盖率分母。

### 7.2 统计方法必须修正

**再次否决“全部指标使用95%精确二项置信区间”。**

| 指标类型 | 推荐统计方法 |
|---|---|
| 满足二项模型的简单随机比例 | Wilson 或 Clopper–Pearson |
| 分层总体比例 | 使用抽样层权重及相应分层方差估计 |
| 人工时间及机器时间 | 均值、中位数、P90 |
| 单位交付成本 | 点估计及适当的重抽样区间 |
| 小样本家族 | 原始数量及描述性统计 |

如果 Pilot 的主要目的是探索能力缺口，也可以只报告固定100件样本的描述性结果，不强行推断整个零售行业的总体比例。

这比使用不适用的置信区间更严谨。

### 7.3 成本模型基本通过

目前公式正确：

\[
C_i=r_ht_{h,i}+r_mt_{m,i}+C_{\mathrm{ext},i}
\]

以及：

\[
C_{\mathrm{delivered}}=\frac{\sum_iC_i}{N_s}
\]

还需冻结三个细节：失败样本成本归属、公共批处理成本分摊方式，以及零成功时单位成功交付成本登记为不可计算。

首次编译成本与后续模板改造成本应分开报告，避免把返工后的成功计入一次交付成功率。

---

## 八、下一轮正式执行指派

建议将下一轮限定为 **R09-11 — G1 Evidence Closure & WP1 Protocol Freeze Candidate**。

不扩大研发范围，不重新启动 WP-A3 焊接研究。

### 8.1 D1 G1 门禁关闭条件

| 任务 | 必须提交 |
|---|---|
| G1-01 | 同一原件跨工具体积差异复算 |
| G1-02 | 方向规范化前置条件与负向测试 |
| G1-03 | S0/S1/S2 实际几何不变量台账 |
| G1-04 | 面角属性保持及非对称诊断纹理 |
| G1-05 | 家族修复与导出器修复影响范围分离 |

**上述五项关闭后，授权进入 G2，不需要再进行一轮架构方案讨论。**

G2 的候选范围冻结为：

| 家族 | 候选数量 |
|---|---:|
| aseptic_brick | 最小、典型、最大各1件 |
| brick_250ml | 最小、典型、最大各1件 |
| 非 brick 对照 | 3件 |
| 合计 | 9件 |

非 brick 对照应覆盖正常闭壳、合法开壳以及多部件资产，且默认关闭规范化时不能产生非预期输出变化。

G2 通过后才允许申请受影响家族的全量候选重编译，仍然禁止覆盖历史发行资产。

### 8.2 WP1-v0.3 整改范围

只修改协议，不启动模型或商品生成实验。

{@body const tasks=[["WP1-01","八种互斥完备终态","恢复输入不足、结构未覆盖；移除SKU级NOT_APPLICABLE"],["WP1-02","指标数学闭合","修正M1–M5及独立验证完备率"],["WP1-03","商品一致性门禁","增加STR-01、ASM-01，修正质量缺失及印刷语义"],["WP1-04","抽样与隔离","冻结总体、分层、种子、去重及合法输入"],["WP1-05","统计方法","区分比例、分层统计、成本及连续变量"],["WP1-06","成本与环境","处理零分母、返工、公共成本及验证待完成"],["WP1-07","协议机器测试","构造100件模拟终态，验证总数、分母和指标恒等式"]]}
{@body const [done,setDone]=DIL.useState(tasks.map(()=>false))}
<card gap={3}>
  <row align="center">
    **WP1-v0.3 冻结整改清单**
    <spacer/>
    <caption>{done.filter(Boolean).length}/7</caption>
  </row>
  {#each tasks as a,i}
    <checkbox checked={done[i]} onChange={v=>setDone(old=>old.map((x,j)=>i===j?v:x))}>
      **{a[0]} · {a[1]}**

      <caption>{a[2]}</caption>
    </checkbox>
  {/each}
  <button block variant="outline" color="secondary" onClick={()=>GenUI.copy(tasks.map((a,i)=>(done[i]?"[x] ":"[ ] ")+a.join(" — ")).join("\n"))}><icon name="copy" size="sm"/> 复制执行清单</button>
</card>

我特别要求 WP1-07 成为正式门禁。

刚刚发生的 D1 数值测量事故已经说明：研究指标不仅要在文档中定义正确，还必须通过可以执行的反例验证。

建议至少测试全部域外、全部输入不足、零成功、全部验证待完成、部分明确失败、全部成功等边界情况。

---

## 九、最终签核

| 裁决项 | 最终状态 |
|---|---|
| P0-01 体积变化数学解释 | ACCEPTED |
| P0-01 跨工具体积对账 | OPEN |
| P0-02 默认关闭门控 | APPROVED |
| P0-02 规范化安全前置条件 | REQUIRED |
| P0-03 T25 | APPROVED |
| P0-03 真实候选几何不变量 | PENDING |
| D1 G1 | CONDITIONAL PASS |
| brick G2 九件候选 | G1通过后授权 |
| 通用导出器全局启用 | NOT AUTHORIZED |
| WP1-Pilot-100 定位 | APPROVED |
| WP1-v0.2 | REVISE BEFORE FREEZE |
| WP1-v0.3 | AUTHORIZED FOR PROTOCOL REVISION |
| WP-V / REP-IDENTITY / ECO | 继续独立并行 |
| 9,386件全量重编译 | PROHIBITED |

**R09-10 FINAL VERDICT：CONDITIONAL PASS — G1 EVIDENCE CLOSURE REQUIRED — WP1 FREEZE DEFERRED**

最后强调，本轮不应再次陷入长周期的单家族修复。G1 剩余问题主要属于证据补齐与安全门禁，不属于新的几何算法研究。

而 WP1 的重要性已经超过 brick 局部修复。我们必须确保未来得到的第一个真实商品盲测结果，无论是30%还是90%，都能够准确反映编译器的真实能力，而不是分母、终态或统计公式设计出来的数字。