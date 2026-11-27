# R09-13 正式裁决｜历史验证器身份追溯与独立补丁验收

**总体裁决：CONDITIONAL PASS。历史验证器身份追溯取得实质性突破，MaterialBindingAPI 补丁获得单件候选验收；WP1-v0.4.1 仍不批准冻结。**

本轮最有价值的成果是找到了历史验证器源码及实际运行记录，并主动纠正了175件与202条记录之间的统计错误。这比此前仅依靠 `validator.name` 字段判断验证器身份具有更高的证据价值。

但 WP1 的核心整改要求仍未提供关闭证据。

| 裁决事项 | 正式决定 |
|---|---|
| NVIDIA SDK 实物身份追溯 | ACCEPTED AS REPORTED |
| 历史175→202口径更正 | ACCEPTED |
| 202条 PASS 运行记录 | ACCEPTED AS REPORTED |
| 历史验证器完整证据链 | 最小补证后关闭 |
| MaterialBindingAPI 独立补丁 | 单件候选 PASS |
| WP1-v0.4.1 | **REJECT FOR FREEZE** |
| G1 | 保持 OPEN |
| 分级焊接研究 | 继续延期 |
| ECO-CPG-01 | 立即独立执行 |

本轮依据提交的实物追溯摘要进行裁决，尚未独立读取 `ddc1d87` 仓库源码、202条原始运行记录或候选 USD 文件。

---

## 一、历史175件验证器身份追溯

**【原则同意】接受验证器实物来源追溯成果，不再要求重复开展验证器身份研究。**

### 1.1 历史数量更正成立

<card gap={3}>
  <caption>历史验证记录数量对账</caption>
  <row align="center">
    <box flex={1}>
      <caption>原台账</caption>
      <title size="2xl" tabularNums={true}>175</title>
    </box>
    <icon name="arrow-right" color="secondary" size="xl"/>
    <box flex={1}>
      <caption>更正后</caption>
      <title size="2xl" tabularNums={true}>202</title>
    </box>
  </row>
  <row>
    <text color="secondary" size="sm">variant 少记</text>
    <spacer/>
    **+25**
  </row>
  <row>
    <text color="secondary" size="sm">dairy 漏记</text>
    <spacer/>
    **+2**
  </row>
  <divider/>
  <caption>202条运行记录构成</caption>
  {#each [{t:"TDE",v:100},{t:"Variant",v:60},{t:"NV960",v:20},{t:"Liquor",v:16},{t:"Legacy",v:4},{t:"Dairy",v:2}] as a}
    <box gap={1}>
      <row>
        <text size="sm">{a.t}</text>
        <spacer/>
        <text weight="medium" tabularNums={true}>{a.v}</text>
      </row>
      <box height={10} background="surface-secondary" radius="sm" clip={true}>
        <box height="100%" width={`${a.v/100*100}%`} background="#758BC0" radius="sm"/>
      </box>
    </box>
  {/each}
  <divider/>
  <row align="center">
    <caption>执行侧报告通过记录</caption>
    <spacer/>
    <title size="xl" color="success">202 / 202</title>
  </row>
</card>

数量闭合：

\[
16+2+20+60+100+4=202
\]

原台账：

\[
16+0+20+35+100+4=175
\]

因此，175→202 的算术更正成立。

但建议暂时使用“202条验证运行记录”，而不是直接宣称“202件独立资产”。不同实验组之间是否存在同一资产重复运行，需要通过资产哈希去重确认。

### 1.2 验证器身份的证据等级提升

| 证据 | 当前状态 |
|---|---|
| SDK 源码实物 | 已找到 |
| 文件指纹 | 已记录16位 SHA256 前缀 |
| 文件大小 | 已记录61,645 bytes |
| 后端接口 | 已确认 generic / physx / newton |
| 历史运行记录 | 已找到202条 |
| 历史执行入口与 SDK 调用关系 | 已报告，原始调用证据待固定 |
| 官方上游版本 | 尚未展示 |
| 15项与10项检查映射 | 尚未展示 |

本轮可以关闭“没有找到历史验证器实物”这一问题。

但仍不能仅凭版权声明、文件大小及本地源码路径，就证明历史运行时实际调用的是该文件的这个版本。

### 1.3 最小补证，不再启动新研究

只需要在现有台账补齐以下字段：

| 编号 | 必须登记 |
|---|---|
| V-C01 | 完整64位 SHA256、官方来源 commit 或版本 |
| V-C02 | 历史调用脚本、实际 backend 参数及验证器文件关联 |
| V-C03 | 202条记录对应的唯一资产数及资产哈希 |
| V-C04 | 官方15项与历史10项检查的对应关系 |

特别是 V-C04，本轮报告仍未回答上一轮提出的规则数量差异。

如果历史10项是另一层自审，官方15项属于 SDK 独立运行，那么将两份结果分别登记即可，不需要强行建立一一对应关系。

完成以上字段后，允许执行侧关闭验证器身份专项，不再增加评审轮次。

### 1.4 对外声明恢复条件

在上述证据固定后，可以恢复限定口径的历史技术声明：

> 历史实验累计记录202次指定版本 USDCraft SDK 验证通过，具体检查范围、后端配置及资产身份见验证台账。

不允许将其扩大为9,386件资产全部经过 NVIDIA 验证，或全部通过真实物理行为测试。

---

## 二、WP1-v0.4.1 是否签发 FROZEN？

**【不同意】本轮仍然没有提交上一轮明确要求的核心整改证据。**

上一轮要求的不是将机器测试写入协议正文，而是修复统计函数本身。

| R09-12 强制要求 | 本轮提交状态 |
|---|---|
| 删除 M4 错误公式及钳制 | 未展示 |
| M0 全域外时为0% | 未展示 |
| M4 = Ns / Nd | 未展示 |
| W11：10成功、60待验证 | 未提交 |
| W12：全域外边界测试 | 未提交 |
| W13：非法计数拒绝 | 未提交 |
| 完整协议正文 | 未提交 |
| W01–W13 全部通过 | 仍报告10/10 |

**10/10 PASS 不是本轮验收标准，13/13 才是上一轮明确指定的标准。**

### 必须验证的三个反例

<card gap={3}>
  <caption>WP1 冻结前最后三个关键反例</caption>
  <row align="start">
    <box flex={1} gap={1}>
      **W11 · 成功与待验证混合**
      <caption>100件域内，10件成功，60件待验证</caption>
    </box>
    <title size="xl" color="success">10%</title>
  </row>
  <divider/>
  <row align="start">
    <box flex={1} gap={1}>
      **W12 · 全部域外**
      <caption>100件全部属于适用域之外</caption>
    </box>
    <box align="end" gap={1}>
      **M0 = 0%**
      <caption>M1–M4 = UNDEFINED</caption>
    </box>
  </row>
  <divider/>
  <row align="start">
    <box flex={1} gap={1}>
      **W13 · 非法计数**
      <caption>域内80件，输入充分85件</caption>
    </box>
    <text color="danger" weight="medium">REJECT</text>
  </row>
</card>

此外，执行侧提出：

> 改公式必须先改 selftest。

这条治理规则需要修改。

测试预期应来自已经批准的研究协议，而不是随着被测公式自由修改。正确的变更顺序是：

**协议变更获得批准 → 修改独立测试预期 → 修改实现 → 执行回归。**

否则，错误公式和错误测试可以同时修改，继续产生全绿结果。

### WP1 下一轮最小交付

不再接受长篇说明，只提交以下四份制品：

| 制品 | 内容 |
|---|---|
| 完整协议正文 | 唯一有效的终态、指标、抽样及门禁定义 |
| `wp1_metrics.py` | 实际生产统计函数 |
| `wp1_protocol_selftest.py` | W01–W13 |
| 测试原始结果 | 每项输入、预期、实际、判决 |

WP1-v0.4.1 当前状态：

```text
PROTOCOL_STATUS = PROPOSED
METRIC_FORMULA_VERIFIED = false
REQUIRED_SELFTEST_COUNT = 13
REPORTED_SELFTEST_COUNT = 10
FREEZE = REJECTED
EXPERIMENT_START = NOT_AUTHORIZED
```

---

## 三、MaterialBindingAPI 独立补丁验收

**【同意】批准单件候选补丁验收，保留独立补丁路线。**

<card gap={3}>
  <caption>aseptic_brick_v0000 · usdchecker 回归（报告值）</caption>
  <grid columns={2}>
    <grid-item>
      <box gap={1}>
        <caption>修复前</caption>
        <title size="xl" color="danger">FAIL</title>
        **exit = 1**
        <caption>MaterialBindingApiAppliedValidator</caption>
      </box>
    </grid-item>
    <grid-item>
      <box gap={1}>
        <caption>修复后</caption>
        <title size="xl" color="success">PASS</title>
        **exit = 0**
        <caption>Success!</caption>
      </box>
    </grid-item>
  </grid>
</card>

显式应用 `MaterialBindingAPI.Apply()` 的修复方向，与此前发现的 USD 规范兼容性缺口相符。

本次补丁独立于绕向修复，这一点符合单变量实验纪律。

### 3.1 一个需要核查的实现细节

报告列出三处 Apply：

| 位置 | 裁决 |
|---|---|
| Body visual | 原则接受 |
| visual | 原则接受 |
| collision | 需核对实际材质绑定用途 |

如果 collision prim 确实存在合法的材质绑定，则应用相应 API 合理。

如果不存在材质绑定，就不必为了统一形式无条件增加 schema。应依据实际绑定操作决定，而不是对所有 prim 一律 Apply。

### 3.2 授权最小回归

本轮批准额外三个非 brick 代表资产的独立补丁回归，不需要等待 G1。

| 对照类型 | 数量 |
|---|---:|
| 普通单部件资产 | 1 |
| 多部件资产 | 1 |
| 包含独立碰撞代理的资产 | 1 |

要求验证：

- usdchecker 完整结果。
- 几何坐标及拓扑保持。
- 材质绑定目标保持。
- 无新增验证器红灯。
- 与绕向规范化补丁保持隔离。

如果三件均通过，可以接受该补丁为通用导出器的候选规范兼容性修复，但仍不授权覆盖冻结发行集。

```text
MATERIAL_BINDING_FIX = ACCEPTED_AS_CANDIDATE
SINGLE_ASSET_REGRESSION = PASS_AS_REPORTED
CROSS_FAMILY_REGRESSION = AUTHORIZED
BULK_RELEASE = NOT_AUTHORIZED
```

---

## 四、G1 分级焊接延期项如何处置？

**裁决：继续延期，并从 D1 当前修复关键路径中移除。**

D1 更正之后，我们已经明确：冻结原件并非平板展开件，也不是必须通过重新焊接才能形成三维几何。

因此当前存在两条不同的技术路线。

<box border radius="lg" padding={3} gap={3}>
  <svg viewBox="0 0 340 210" width="100%">
    <rect x="60" y="5" width="220" height="34" rx="6" fill="#e5eafa" stroke="#8b9ac2"/>
    <text x="170" y="26" fontSize="12" fontWeight="bold" fill="#465b89" textAnchor="middle">D1 根因更正</text>
    <path d="M170 39V55H83V72M170 55H257V72" stroke="#8795aa" fill="none"/>
    <rect x="5" y="73" width="156" height="44" rx="6" fill="#e0eee5" stroke="#8aaf95"/>
    <text x="83" y="90" fontSize="11" fontWeight="bold" fill="#427553" textAnchor="middle">原有编译器修复</text>
    <text x="83" y="105" fontSize="10" fill="#547b62" textAnchor="middle">绕向修正 + 规范化</text>
    <rect x="179" y="73" width="156" height="44" rx="6" fill="#edf0f5" stroke="#a0aabd"/>
    <text x="257" y="90" fontSize="11" fontWeight="bold" fill="#586780" textAnchor="middle">WP-A3 重构路线</text>
    <text x="257" y="105" fontSize="10" fill="#6e7b90" textAnchor="middle">封合 / 分级焊接</text>
    <path d="M83 117V138M257 117V138" stroke="#8795aa"/>
    <rect x="5" y="140" width="156" height="30" rx="5" fill="#e0eee5" stroke="#8aaf95"/>
    <text x="83" y="159" fontSize="11" fontWeight="bold" fill="#427553" textAnchor="middle">G1 → G2 → 家族候选</text>
    <rect x="179" y="140" width="156" height="30" rx="5" fill="#edf0f5" stroke="#a0aabd"/>
    <text x="257" y="159" fontSize="11" fontWeight="bold" fill="#586780" textAnchor="middle">ARCHIVED / DEFERRED</text>
    <text x="83" y="190" fontSize="11" textAnchor="middle" fill="#427553">当前修复主线</text>
    <text x="257" y="190" fontSize="11" textAnchor="middle" fill="#758195">独立研究储备</text>
  </svg>
  <caption>不再将错误根因衍生的封合重构研究作为现有编译器修复的前置条件。</caption>
</box>

| 研究事项 | 处置 |
|---|---|
| TRIAL-CLOSURE-CONSTRAINT-TRACE | 保留归档 |
| FOLD→SEAL→GLUE 分级焊接 | 不启动 |
| Manifold repair | 不启动 |
| 部件级表达契约 | 保留为长期架构知识 |
| G1 绕向修复证据 | 继续完成 |
| G2 九件候选 | G1关闭后执行 |

本次没有提交 G1 剩余原始证据，因此其状态保持不变。

---

## 五、ECO-CPG-01：立即执行，不再延期

我建议下一轮将 ECO-CPG-01 提升为独立 P0 研究任务。

原因很简单：项目已经投入大量资源解决资产编译质量问题，但对这些资产能否产生实际零售感知价值，仍然缺少足够的外部实物证据。

本轮严格执行此前批准的有限侦察范围。

| 任务 | 交付要求 |
|---|---|
| E01 数据来源 | 官方下载入口、版本、文件清单 |
| E02 许可证 | 数据、图片、标注及商业使用限制 |
| E03 实物下载 | 文件大小、SHA256、实际可解包性 |
| E04 数据统计 | 图像数量、分辨率、类别、标注框数量 |
| E05 视觉抽检 | 固定种子抽取30张，生成可视化检查图 |
| E06 标注核验 | 包围框坐标、类别语义、遮挡与异常标注 |
| E07 与现有资产对照 | 商品纹理、包装结构、陈列密度、相机和场景差异 |

维持此前5GB、2小时的有限侦察预算。不启动大规模训练。

重点不是再次总结 Neurolabs 的论文或宣传材料，而是实际下载数据、查看图像和标注，验证此前研究判断。

---

## 六、下一阶段资源调整

<card gap={3}>
  <caption>建议研究资源分配</caption>
  {#each [{t:"ECO-CPG-01 实物侦察",v:35,c:"#779A83"},{t:"WP1 协议最终收口",v:25,c:"#9180BE"},{t:"G1 原始证据关闭",v:20,c:"#768AC1"},{t:"WP-V / REP-IDENTITY 收口",v:15,c:"#A9B4C9"},{t:"MaterialBindingAPI 回归",v:5,c:"#B6A078"}] as a}
    <box gap={1}>
      <row>
        <text size="sm" weight="medium">{a.t}</text>
        <spacer/>
        **{a.v}%**
      </row>
      <box height={12} background="surface-secondary" radius="sm" clip={true}>
        <box width={`${a.v}%`} height="100%" background={a.c}/>
      </box>
    </box>
  {/each}
  <caption>建议投入比例，非实际工时统计。</caption>
</card>

## 七、R09-14 正式执行台账

{@body const tasks=[["T01","WP-V 历史身份收口","完整哈希、实际调用关系、202条记录去重及规则数量解释"],["T02","WP1 协议冻结","生产统计函数、完整协议、W01–W13原始结果"],["T03","MaterialBindingAPI","三个非brick资产独立回归"],["T04","G1","关闭此前已明确的四项遗留证据"],["T05","G2","仅在G1全部通过后执行九件候选"],["T06","REP-IDENTITY","完成测量分类、用途契约及跨环节身份追溯"],["T07","ECO-CPG-01","立即完成数据下载、许可证、30张图像及标注实物核验"]]}
{@body const [done,setDone]=DIL.useState(tasks.map(()=>false))}
<card gap={3}>
  <row align="center">
    **执行清单**
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

## 八、最终签核

| 裁决事项 | 最终状态 |
|---|---|
| 历史验证器实物追溯 | ACCEPTED AS REPORTED |
| 175→202算术更正 | APPROVED |
| 验证器身份完整闭环 | MINIMAL EVIDENCE REQUIRED |
| MaterialBindingAPI 单件补丁 | PASS AS REPORTED |
| MaterialBindingAPI 跨家族回归 | AUTHORIZED |
| WP1-v0.4.1 | **REJECT FOR FREEZE** |
| G1 | OPEN |
| G2 | CONDITIONAL AUTHORIZATION |
| 分级焊接 | DEFERRED |
| ECO-CPG-01 | P0 AUTHORIZED |
| 全量重编译及发行 | PROHIBITED |

**R09-13 FINAL VERDICT：CONDITIONAL PASS — HISTORICAL VALIDATOR EVIDENCE ADVANCED — MATERIAL BINDING FIX ACCEPTED — WP1 FREEZE REJECTED**

最后提出一项执行纪律要求：下一轮不再接受仅修改协议文字、增加章节或重复声明测试通过的 WP1 整改报告。必须提交实际统计函数及13例原始测试结果。

同时，**下一份优先送审件应当是 ECO-CPG-01 实物侦察报告。** 我们需要将一部分研究资源从内部工程合规重新转向外部证据和零售业务价值验证。