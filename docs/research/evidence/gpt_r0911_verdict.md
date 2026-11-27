# R09-11 正式裁决｜G1 证据复核与 WP1-v0.3 协议冻结审查

**总体裁决：CONDITIONAL PASS。G1 尚未关闭，G2 暂不授权；WP1-v0.3 再次拒绝冻结。**

本轮出现了两个值得高度关注的问题：

第一，G1 证据台账内部出现直接矛盾：S0 的绕向一致性在不变量台账中为 `true`，在体积复算及文字结论中却为 `false`。

第二，WP1-v0.3 没有实际落实上一轮的核心统计整改，甚至出现重复终态定义。上一轮明确指出的 M2 分母矛盾和 M4 数学错误仍原样存在。

考虑到刚刚发生过 D1 测量治理事故，本轮不能再通过解释性文字替代机器证据的一致性核验。

| 裁决事项 | 正式决定 |
|---|---|
| G1-01 跨工具体积复算 | 部分通过 |
| G1-02 规范化安全门禁 | 部分通过 |
| G1-03 几何不变量 | FAIL：证据矛盾且不完整 |
| G1-04 UV 映射验证 | FAIL：验证方法不足 |
| G1-05 影响范围分离 | ACCEPTED AS REPORTED |
| G2 九件候选编译 | 暂不授权 |
| WP1-v0.3 | **REJECT FOR FREEZE** |
| WP-V / REP-IDENTITY | P0，立即推进 |
| ECO-CPG-01 | 独立并行 |

本轮依据提交的证据摘要及协议节选进行裁决，未独立读取或执行 `ec8827b` 完整源码，不签发制品级独立验收证明。

---

## 一、G1-01｜S0 平移不变性破缺的数学定性

**裁决：【修改后接受】这是有效的异常证据，但需要准确限定数学含义。**

<card gap={3}>
  <caption>三阶段体积测量对照 · 单位 mm³</caption>
  <table>
    <table-row>
      <table-cell>阶段</table-cell>
      <table-cell align="end">Origin</table-cell>
      <table-cell align="end">Translated</table-cell>
      <table-cell align="end">trimesh</table-cell>
    </table-row>
    {#each [{s:"S0",a:"−233,078",b:"+14,880,595",c:"−240,514"},{s:"S1",a:"−276,983",b:"−276,983",c:"−276,983"},{s:"S2",a:"+276,983",b:"+276,983",c:"+276,983"}] as a,i}
      <table-row>
        <table-cell>**{a.s}**</table-cell>
        <table-cell align="end">{a.a}</table-cell>
        <table-cell align="end"><text color={i===0?"danger":"default"}>{a.b}</text></table-cell>
        <table-cell align="end">{a.c}</table-cell>
      </table-row>
    {/each}
  </table>
  <divider/>
  <row align="center">
    <box flex={1}>
      <caption>S0 平移前后差值</caption>
      <title size="xl" color="danger" tabularNums={true}>15,113,673</title>
    </box>
    <box flex={1}>
      <caption>S1 / S2 平移前后差值</caption>
      <title size="xl" color="success">0</title>
    </box>
  </row>
  <caption>以上按提交的整数显示值计算，尚未核验原始浮点精度。</caption>
</card>

### 1.1 数学推导

三角网格的符号体积为：

\[
V=\frac16\sum_i
\mathbf a_i\cdot(\mathbf b_i\times\mathbf c_i)
\]

当所有顶点平移向量 \(\mathbf t\) 后：

\[
V'-V=
\frac13\mathbf t\cdot
\sum_i\mathbf A_i
\]

其中 \(\mathbf A_i\) 是第 \(i\) 个三角面的有向面积向量。

对于正确闭合且绕向一致的网格：

\[
\sum_i\mathbf A_i=\mathbf 0
\]

因此：

\[
V'=V
\]

S0 出现显著平移依赖，说明其有向面积向量未满足相应的闭合抵消条件。

这与局部绕向不一致的诊断相符。

但是，需要补充两个限定：

- 平移不变性破缺不只可能由绕向错误引起，开放边界、缺面等情况也可能产生该现象。
- 平移不变性成立也不是绕向正确的充分条件，某些错误面片的面积向量可能恰好相互抵消。

因此，应把它登记为**独立数学交叉证据**，而不是新的唯一绕向判定算法。

### 1.2 trimesh 口径仍需备注

S0 的三种体积结果已经不具有可靠的实体体积解释，但这并不意味着三个算法之间的差异无需追查。

只要求补充：

| 字段 | 要求 |
|---|---|
| translation_vector | 实际平移向量及单位 |
| area_vector_sum | 有向面积向量总和 |
| predicted_volume_delta | 按上述公式计算的理论变化 |
| measured_volume_delta | 实际变化 |
| trimesh_volume_method | 版本、算法口径及调用参数 |

理论变化与实际变化应在预先登记的数值容差内一致。

S0 的体积应该统一标记：

```text
SIGNED_VOLUME_VALIDITY = INVALID_FOR_SOLID_MEASUREMENT
```

**G1-01：PARTIAL PASS，补齐上述数学对账后即可关闭。**

---

## 二、G1-02｜方向规范化安全门禁

**裁决：【部分通过】五项前置检查方向正确，但没有完整落实上一轮要求。**

| 前置检查 | 当前状态 |
|---|---|
| 有限数值 | 已报告实现 |
| 非退化三角面 | 已报告实现 |
| 非流形边检查 | 已报告实现 |
| 闭合性 | 已报告实现 |
| 局部绕向一致性 | 已报告实现 |
| 明确 SOLID 契约 | 未展示 |
| 单闭壳配置限制 | 未展示 |
| 非流形顶点检查 | 未展示 |
| USD orientation 与变换语义 | 未展示 |
| 近零体积拒绝 | 未展示 |

上一轮明确要求，本阶段只支持经过确认的单闭壳实体，不需要立即解决多壳体、内腔及复杂变换。

但不支持这些情形，就必须明确拒绝，而不是没有相应检查。

### 2.1 负向测试没有覆盖最重要的触发场景

本轮五例测试具有价值，但以下用例仍然缺失。

| 测试 | 预期结果 |
|---|---|
| 闭合但局部绕向混乱的负体积网格 | UNSAFE_SKIP |
| 已正确外向的单闭壳 | 不翻转 |
| 两个独立闭壳 | 当前版本拒绝整体规范化 |
| 不明确方向语义的负尺度变换 | 拒绝或明确处理 |
| 重复执行规范化 | 第二次执行不产生变化 |

其中第一个测试尤其重要，因为它正是冻结 S0 资产的实际问题。

还需要明确 `UNSAFE_SKIP` 只是规范化操作被拒绝，不代表该资产成功交付。

**G1-02：PARTIAL PASS。保留现有实现，增加最小安全约束和回归，不扩大算法范围。**

---

## 三、G1-03｜几何不变量台账存在直接矛盾

**裁决：FAIL，必须纠正证据文件。**

### 3.1 S0 绕向状态矛盾

<box border radius="lg" padding={3} gap={2}>
  <grid columns={2} gap={2}>
    <grid-item>
      <caption>G1-01 与文字解释</caption>
      **S0 winding_consistent**

      <title size="xl" color="danger">FALSE</title>
    </grid-item>
    <grid-item>
      <caption>G1-03 不变量 JSON</caption>
      **S0 winding_consistent**

      <title size="xl" color="success">TRUE</title>
    </grid-item>
  </grid>
  <divider/>
  两份证据描述同一阶段，却给出了互相排斥的结果。不能同时成立。
</box>

必须查明：

- 是否加载了不同的 USD 文件。
- 是否在测量过程中执行了自动修复。
- 是否使用了不同的网格处理选项。
- 是否复制了其他阶段的结果。

不要直接将 JSON 中的 `true` 手工改成 `false`。必须重新运行对应证据脚本，并记录每个阶段的文件 SHA256。

### 3.2 不变量要求仍未真正落实

当前提交的数据都是聚合统计。

| 不变量 | 本轮是否证明 |
|---|---|
| 顶点数量相同 | 是 |
| 三角面数量相同 | 是 |
| bbox 相同 | 是，报告精度下 |
| 表面积相同 | 是，报告精度下 |
| 无向边数量相同 | 是 |
| 顶点坐标集合完全相同 | **否** |
| 无向三角面多重集合相同 | **否** |
| 面板身份及材质绑定相同 | **否** |
| 面角属性对应保持 | **否** |

这些聚合值全部一致，也不能证明两个网格完全等价。

此前已经批准 T25 永久回归，正是为了防止将相同 bbox 误认为几何相同。本轮却又用另一组聚合指标替代了实际几何等价证明。

### 3.3 最小整改方式

直接生成以下机器可验证字段：

```json
{
  "comparison": "S1_to_S2",
  "source_sha256": "...",
  "target_sha256": "...",
  "vertex_coordinate_multiset_equal": true,
  "undirected_triangle_multiset_equal": true,
  "material_binding_equal": true,
  "panel_identity_equal": true,
  "corner_attribute_mapping_equal": true,
  "signed_volume_negation": true
}
```

以上是验收字段示例，不是已取得的实测结果。

对 S0→S1 与 S1→S2 分别执行。必须使用冻结容差，必要时保留原始值与差异记录。

**不要再提交只有顶点数、面数、bbox 和面积的替代证据。**

---

## 四、G1-04｜面内仿射自洽能否替代跨导出逐角验证？

**明确裁决：不能。非对称诊断纹理仍然必须完成消费端验证。**

本轮提出的仿射残差检查存在一个根本性的数学局限。

### 4.1 任意非退化三角形之间都可以建立仿射映射

对于一个非共线的三角形，给定其三个顶点及任意三个对应二维坐标，通常可以求出一个仿射映射，使三个顶点精确匹配。

即使把其中两个 UV 面角交换，仍然可能得到零残差。

<box border radius="lg" padding={3} gap={2}>
  <svg viewBox="0 0 340 214" width="100%">
    {#each [{x:12,t:"正确映射",labels:["A","B","C"],color:"#69977A"},{x:182,t:"错误面角交换",labels:["A","C","B"],color:"#BE7369"}] as a,i}
      <g transform={`translate(${a.x},0)`}>
        <path d="M68 12L10 72L126 72Z" fill="#e1e9f8" stroke="#8194bf"/>
        <g fontSize="11" textAnchor="middle" fill="#435a80">
          <text x="68" y="9">0</text><text x="8" y="88">1</text><text x="128" y="88">2</text>
        </g>
        <path d="M68 90V107m-4-5l4 5 4-5" stroke="#8894a8" fill="none"/>
        <path d="M68 118L10 178L126 178Z" fill={i===0?"#e1efe6":"#f7e1df"} stroke={a.color}/>
        <g fontSize="12" fontWeight="bold" textAnchor="middle" fill={a.color}>
          <text x="68" y="115">{a.labels[0]}</text>
          <text x="8" y="193">{a.labels[1]}</text>
          <text x="128" y="193">{a.labels[2]}</text>
          <text x="68" y="210">{a.t}</text>
        </g>
      </g>
    {/each}
  </svg>
  <grid columns={2} gap={2}>
    <grid-item>
      <text textAlign="center" color="success" weight="medium">仿射残差可以为0</text>
    </grid-item>
    <grid-item>
      <text textAlign="center" color="danger" weight="medium">仿射残差也可以为0</text>
    </grid-item>
  </grid>
  <caption>示意反例：如果仿射映射由被检三角形自身的三个对应点拟合，面角交换也可以满足仿射自洽。</caption>
</box>

因此，如果本轮所谓的20/20仿射一致，是逐三角面独立拟合再计算残差，那么这个指标无法证明没有角交换、没有镜像，也无法证明真实印刷正确。

如果使用的是独立预先定义的面板变换，而不是用被检点重新拟合，则需要提交明确的公式和参考坐标来源，才能重新评估。

### 4.2 四面 cross-export mismatch 不允许直接豁免

执行侧提出 triR 圆交点重排造成合法 UV 重算，这是一个可以接受的解释假设。

但必须区分两个阶段：

| 阶段 | 验收要求 |
|---|---|
| S0→S1 家族修复 | 允许有依据的 UV 重算，但必须符合原始印刷设计 |
| S1→S2 整体绕向翻转 | 几何面角与 UV 的物理对应必须保持 |

如果 S1→S2 仍有无法解释的 UV 对应变化，就是方向规范化引入的回归缺陷。

### 4.3 消费端实验必须做，但不一定使用完整 Blender 棚拍管线

我不会要求重新接入复杂摄影渲染流程。

允许使用 Blender 最小场景或其他能够正确读取 USD 材质与 faceVarying 属性的独立消费端。

实验仅需：

| 制品 | 验证目的 |
|---|---|
| S1 + 非对称诊断纹理 | 建立翻转前基线 |
| S2 + 相同诊断纹理 | 验证翻转后映射保持 |
| 预期面板印刷映射 | 独立正确性参考 |
| 故意交换两个 UV 面角的负样本 | 证明验证方法确实能检出错误 |

要求覆盖受影响面板，而不是只渲染一个正面视角。

**PRINT-01 是未来商品评测门禁，不能替代当前修复代码自身的回归门禁。**

G1-04 最终状态：

```text
AFFINE_SELF_CONSISTENCY = ACCEPTED_AS_OBSERVATION
UV_CORNER_PRESERVATION  = NOT_PROVEN
CONSUMER_RENDER_CHECK   = REQUIRED
G1_04                   = OPEN
```

---

## 五、G1-05｜影响范围分离

**裁决：【同意】接受执行侧报告的家族依赖范围和默认关闭设计。**

| 修复类型 | 当前确认范围 |
|---|---|
| `_brick_net / _brick_world` | aseptic_brick、brick_250ml |
| gable_screw_cap | 独立生成函数 |
| gable_fin_gap_wide | 独立生成函数 |
| 通用方向规范化 | 默认关闭 |

但“默认 False”只能证明方向规范化逻辑按设计不会被激活，不能自动证明新版本导出器生成的所有其他内容均字节不变。

G2 中仍保留三个非 brick 对照资产进行默认关闭行为回归。

**G1-05：PASS AS REPORTED，不再单独追加源码依赖研究。**

---

## 六、G1 整体门禁状态

<card gap={3}>
  <caption>五项正式验收状态</caption>
  {#each [{n:"G1-01",t:"体积数学对账",s:"部分通过",c:"warning"},{n:"G1-02",t:"规范化安全门禁",s:"部分通过",c:"warning"},{n:"G1-03",t:"实际几何不变量",s:"FAIL",c:"danger"},{n:"G1-04",t:"UV 属性与消费端",s:"FAIL",c:"danger"},{n:"G1-05",t:"影响范围分离",s:"通过（报告级）",c:"success"}] as a}
    <row align="center">
      <box flex={1} gap={0}>
        **{a.n}**
        <caption>{a.t}</caption>
      </box>
      <text color={a.c} weight="medium">{a.s}</text>
    </row>
    <divider/>
  {/each}
  <title size="2xl" tabularNums={true}>1 / 5</title>
  <caption>报告级完全关闭项：1；部分通过项：2；未通过项：2。</caption>
</card>

G2 九件候选编译仍然保持待授权状态。

但不需要等待下一轮架构讨论。只要上述四项遗留证据通过既定门禁，即可按 R09-10 已批准的条件进入 G2。

---

## 七、WP1-v0.3：拒绝冻结

**这是本轮最需要严肃指出的问题。上一轮已经明确提供了可以直接采用的终态和指标定义，但 v0.3 送审文本没有落实。**

我不认为这是新的研究难题，更像是协议编辑、版本合并或送审前自检失败。

### 7.1 终态表存在三个明确错误

| 问题 | 实际情况 |
|---|---|
| 标题声明七种终态 | 实际列出10行、8种不同标签 |
| INSUFFICIENT_SPEC / COVERAGE_GAP | 各重复定义两次 |
| CONTRACT_UNKNOWN | 被删除 |
| NOT_APPLICABLE | 仍错误地作为 SKU 终态 |

上一轮已经明确要求八种互斥完备终态。

建议停止对原表进行局部追加修改，直接整体替换。

<card gap={2}>
  **v0.4 唯一有效终态表**

  | 终态 | 含义 |
  |---|---|
  | OUT_OF_SCOPE | 预冻结适用域之外 |
  | INPUT_INSUFFICIENT | 域内输入不足 |
  | FAMILY_NOT_COVERED | 输入充分但家族未覆盖 |
  | FAMILY_ADAPTATION_REQUIRED | 需要修改家族 |
  | CONTRACT_UNKNOWN | 必要交付契约未知 |
  | GATE_FAIL | 生成或必要门禁失败 |
  | VALIDATION_PENDING | 无明确失败，但必要验证未完成 |
  | SUCCESS | 全部必要验收完成且通过 |

  <caption>NOT_APPLICABLE 只能用于单项门禁，不得作为 SKU 终态。</caption>
  <button block variant="outline" color="secondary" onClick={()=>GenUI.copy("OUT_OF_SCOPE\nINPUT_INSUFFICIENT\nFAMILY_NOT_COVERED\nFAMILY_ADAPTATION_REQUIRED\nCONTRACT_UNKNOWN\nGATE_FAIL\nVALIDATION_PENDING\nSUCCESS")}>复制冻结枚举</button>
</card>

如果已经确定某个必需门禁失败，则最终状态应为 `GATE_FAIL`，不能因为同时存在其他未知或未运行项而掩盖失败。

### 7.2 指标公式仍是旧版错误公式

上一轮已经否决：

\[
M4=\frac{SUCCESS-VALIDATION\_PENDING}{N_d}
\]

本轮仍然原样提交。

下面的交互反例可以直接用于测试协议计算逻辑。

{@body const [success,setSuccess]=DIL.useState(10)}
{@body const [pending,setPending]=DIL.useState(60)}
<card gap={3}>
  **WP1 错误公式反例测试**

  <row align="center">
    <label>SUCCESS</label>
    <spacer/>
    **{success} 件**
  </row>
  <slider min={0} max={100-pending} step={1} value={success} onChange={setSuccess}/>
  <row align="center">
    <label>VALIDATION_PENDING</label>
    <spacer/>
    **{pending} 件**
  </row>
  <slider min={0} max={100-success} step={1} value={pending} onChange={setPending}/>
  <caption>假设域内样本为100件，其余终态合计{100-success-pending}件。</caption>
  <divider/>
  <grid columns={2}>
    <grid-item>
      <caption>v0.3 错误 M4</caption>
      <title size="2xl" color="danger">{success-pending}%</title>
    </grid-item>
    <grid-item>
      <caption>正确端到端交付率</caption>
      <title size="2xl" color="default">{success}%</title>
    </grid-item>
  </grid>
</card>

所谓完备率出现负数，已经足以证明公式不能冻结。

### 7.3 冻结指标直接采用上一轮方案

| 指标 | 唯一有效公式 |
|---|---|
| M1 输入可用率 | \(N_i/N_d\) |
| M2 结构覆盖率 | \(N_f/N_i\) |
| M3 条件一次交付成功率 | \(N_s/N_f\) |
| M4 端到端交付率 | \(N_s/N_d\) |
| M5 单位交付成本 | \(\sum C_i/N_s\) |

其中：

- \(N_d\)：域内商品数。
- \(N_i\)：输入充分的域内商品数。
- \(N_f\)：现有家族无需改造即可覆盖的商品数。
- \(N_s\)：首次冻结编译尝试最终完整交付成功的商品数。

必须满足：

\[
N_s\leq N_f\leq N_i\leq N_d\leq100
\]

在分母非零情况下：

\[
M1\times M2\times M3=M4
\]

验证完备率单独作为辅助指标，不得从成功数中减去待验证数。

---

## 八、WP1 上一轮七项整改复核

| 上轮任务 | v0.3 状态 | 本轮理由 |
|---|---|---|
| WP1-01 八种互斥终态 | FAIL | 重复定义、遗漏、错误保留 |
| WP1-02 指标数学闭合 | FAIL | M2 与 M4 旧错误未修 |
| WP1-03 商品一致性门禁 | 未提供完整证据 | 未见 STR、ASM 及质量缺失语义整改 |
| WP1-04 抽样与隔离 | 部分通过 | 分层及随机抽样已报告补充，缺完整冻结证据 |
| WP1-05 统计方法 | 未提供证据 | 未见分层估计与成本区间整改 |
| WP1-06 成本与环境 | 部分通过 | 基本公式保留，零分母及公共成本规则未展示 |
| WP1-07 协议机器测试 | 未提交 | 必须执行 |

另外，“持样方先冻结交 GPT 保管”需要修改。

GPT 可以协助审核抽样协议及证据，但不应作为唯一的样本托管或保密隔离设施。盲测样本应由独立持样方在受控存储中保存，评审侧持有清单哈希及必要的审计证据，执行侧只获得协议允许的输入字段。

**WP1-v0.3：REJECT FOR FREEZE。**

下一版不得继续通过追加段落修补旧协议，应生成一份无重复、无历史残留、唯一有效的 v0.4 完整正文。

---

## 九、增加协议机器门禁，停止反复文字整改

我建议立即建立一个很小的协议一致性测试脚本：

`wp1_protocol_selftest.py`

不需要构建新的评测平台。先用确定性模拟数据验证协议定义。

| 测试编号 | 模拟条件 | 预期 |
|---|---|---|
| W01 | 100件全部域外 | 域内比例 UNDEFINED |
| W02 | 100件全部输入不足 | 输入可用率0 |
| W03 | 输入充分但家族全部未覆盖 | 结构覆盖率0 |
| W04 | 100件全部验证待完成 | 交付率0 |
| W05 | 100件全部成功 | 四层比例均100% |
| W06 | 同时存在 FAIL 与未验证 | FAIL 不被 PENDING 覆盖 |
| W07 | 零成功交付 | 单位交付成本不可计算 |
| W08 | 混合100件终态 | 计数闭合、指标恒等式成立 |
| W09 | 重复 SKU 或重复终态定义 | 拒绝统计 |
| W10 | NOT_APPLICABLE 单项门禁 | 不生成非法 SKU 终态 |

此外，测试脚本使用的终态枚举与报告统计公式应与正式协议有明确的版本关联，避免测试代码正确而文档仍然保留旧公式。

这十项通过后再送审。不接受仅提供文字说明而没有机器测试结果。

---

## 十、下一步优先级与任务指派

本轮最重要的管理决定是：**不允许 G1 与 WP1 的反复整改继续阻塞 WP-V 和 ECO。**

<card gap={3}>
  <caption>R09-12 建议研究资源分配</caption>
  {#each [{t:"WP-V + REP-IDENTITY",v:40,c:"#7186BF"},{t:"WP1-v0.4 协议收口",v:30,c:"#9582BF"},{t:"G1 剩余证据收口",v:20,c:"#779B86"},{t:"ECO-CPG-01",v:10,c:"#B6A078"}] as a}
    <box gap={1}>
      <row align="center">
        <text size="sm" weight="medium">{a.t}</text>
        <spacer/>
        **{a.v}%**
      </row>
      <box height={12} radius="sm" background="#E5E7EB" clip={true}>
        <box width={`${a.v}%`} height="100%" background={a.c}/>
      </box>
    </box>
  {/each}
  <caption>建议资源配比，非实际人员及工时记录。</caption>
</card>

### 正式任务台账

{@body const tasks=[["T01","WP-V / REP-IDENTITY 联合报告","P0：历史验证器、9,386件未舍入表达统计、跨环节资产身份"],["T02","WP1-v0.4 完整替换","P0：八终态、五指标、完整协议及10例机器测试"],["T03","G1-01 数学对账","平移向量、有向面积和、理论与实际差值"],["T04","G1-02 安全门禁","补齐单闭壳限制、方向语义、负向测试及幂等性"],["T05","G1-03 实体证据","修正S0矛盾、三阶段几何多重集合与属性比较"],["T06","G1-04 UV 真值实验","非对称纹理、S1/S2消费端对照及故意错配负样本"],["T07","ECO-CPG-01","继续已授权的有限数据集实物核验"]]}
{@body const [done,setDone]=DIL.useState(tasks.map(()=>false))}
<card gap={3}>
  <row align="center">
    **R09-12 执行清单**
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
  <button block color="secondary" variant="outline" onClick={()=>GenUI.copy(tasks.map((a,i)=>(done[i]?"[x] ":"[ ] ")+a.join(" — ")).join("\n"))}><icon name="copy" size="sm"/> 复制执行任务</button>
</card>

G1 剩余事项建议限定半个工作日的主动研究资源。它们都是证据与安全门禁问题，不应重新演变为几何算法研究。

G2 不需要重新设计实验，G1 全部关闭后按既有九件候选范围执行。

---

## 十一、最终签核

| 裁决项 | 最终状态 |
|---|---|
| S0 平移不变性破缺 | ACCEPTED AS CORROBORATING EVIDENCE |
| S0 三口径解释 | PARTIAL PASS |
| 方向规范化默认关闭 | APPROVED |
| 规范化安全门禁完整性 | PARTIAL PASS |
| S0/S1/S2 几何不变量 | FAIL |
| 面内仿射自洽替代逐角验证 | REJECTED |
| 消费端诊断纹理 | REQUIRED |
| G1-05 影响范围分离 | ACCEPTED AS REPORTED |
| G1 整体 | NOT CLOSED |
| G2 九件候选 | DEFERRED UNTIL G1 PASS |
| WP1-v0.3 | **REJECT FOR FREEZE** |
| WP1-v0.4 | AUTHORIZED |
| WP-V + REP-IDENTITY | P0 |
| ECO-CPG-01 | PARALLEL AUTHORIZED |
| 冻结发行集 | 保持不变 |

**R09-11 FINAL VERDICT：CONDITIONAL PASS — EVIDENCE INCONSISTENCY MUST BE CLOSED — WP1 FREEZE REJECTED**

最后，我需要指出当前协作流程本身的问题。

我们已经多次明确 G1 的验收要求和 WP1 的计算公式，但执行侧反复提交没有真正落实原裁决的整改件。特别是 WP1，本轮不是技术能力不足，而是没有把已经确定的要求完整转换为制品。

建议下一轮执行侧送审前增加一道强制门禁：**逐条读取上一轮裁决，建立“要求—实现—测试—证据”四列追溯表，未满足的明确申报 OPEN，不得笼统声明全部整改完成。**

这比继续增加评审轮次更重要。