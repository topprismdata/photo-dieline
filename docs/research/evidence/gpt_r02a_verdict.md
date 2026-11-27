## 二、D1–D4 缺陷分类与根因裁决

**缺陷分类作为初步诊断可以接受，但不能作为最终根因分类。** 目前混合了几何现象、拓扑缺陷、结构表达意图和生成端故障四个不同层次。

| 分类 | 缺陷现象 | 根因可信度 | 裁决 |
|---|---|---|---|
| D1 | 平板化、重复边、绕向异常 | 中 | 优先定位生成端与导出端之间的责任边界 |
| D2 | 奇数边界、疑似裂缝 | 低 | 奇数边界是异常检测线索，不是裂缝的充分证据 |
| D3 | 零体积、零厚度面板 | 中低 | 需要先确定该部件的设计语义 |
| D4 | 零面积 UV 三角 | 中 | 缺陷现象明确，但根因及修复方式尚未证明 |

### D1：优先级最高，但禁止直接补洞

对于 `aseptic_brick` 和 `brick_250ml`，如果最终交付目标是完整的立体商品，而 bbox Y=0，那么这已经是严重的结构表达错误，不只是三角化质量问题。

应沿编译链检查：

<box border radius="lg" padding={3}>
  <svg viewBox="0 0 320 232" width="100%">
    {#each [{y:5,t:"结构家族参数",s:"是否具有完整三维规格"},{y:52,t:"参数化原始几何",s:"是否错误输出平面展开态"},{y:99,t:"三角化与面角映射",s:"是否引入重复边或坐标退化"},{y:146,t:"USD 编译与变换",s:"是否丢失坐标轴或变换信息"},{y:193,t:"最终 USD 资产",s:"独立测量 bbox、拓扑、UV"}] as a,i}
      <rect x="30" y={a.y} width="260" height="36" rx="5" fill={i===4?"#fbe8e6":"#e9edf8"} stroke={i===4?"#cc766e":"#95a4cd"}/>
      <text x="160" y={a.y+14} fontSize="11" fontWeight="bold" fill="#37456b" textAnchor="middle">{a.t}</text>
      <text x="160" y={a.y+27} fontSize="9.5" fill="#606e89" textAnchor="middle">{a.s}</text>
      {#if i<4}<path d={`M160 ${a.y+36}v9 m-3 -4l3 4 3 -4`} fill="none" stroke="#8390a5"/>{/if}
    {/each}
  </svg>
  <caption>逐阶段记录几何快照，找到第一个出现退化的阶段。</caption>
</box>

如果原始几何已经错误，修复三角化算法没有意义。如果原始几何正确而 USD 输出退化，则不能修改结构家族来掩盖导出器错误。

### D2：必须撤回一个错误推论

报告中的“边界边为奇数 → 必有重复面/裂缝”不成立。

一个合法三角形开壳具有三条边界边；一个由三个三角形构成的合法五边形曲面具有五条边界边。

对于三角网格，如果每条内部边恰好被两个面共享，则：

\[
3F=2E_{\mathrm{internal}}+E_{\mathrm{boundary}}
\]

因此，边界边数量的奇偶性与三角面数量的奇偶性一致，并不存在边界边必须为偶数的普遍约束。

正确的检查对象应该是边界环是否符合结构设计意图、边界顶点的连接关系、非流形边、重复面、非预期断缝和 T-junction。

**裁决：D2 全部相关样本必须重新判定。G01 的 90/107 暂不得作为正式质量基线。**

### D3：零厚度不必然是错误

必须在商品数字对象本体中引入明确的几何表达契约。

| 表达契约 | 合法零厚度 | 必须闭合 |
|---|---|---|
| 实体 SOLID | 否 | 是 |
| 开口容器 OPEN_SHELL | 视具体用途 | 否 |
| 曲面 SURFACE | 是 | 否 |
| 包装展开图 FLAT_PATTERN | 是 | 否 |
| 碰撞代理 COLLISION_PROXY | 依据碰撞体类型 | 依据碰撞体类型 |

同时，购物车黑色渲染的因果关系尚未成立。零厚度、面绕向、法线以及背面剔除是不同变量。不能仅凭发现零厚度，就确定它是黑色渲染的根因。

需要用同一个面板分别改变厚度、绕向、法线和渲染器背面处理设置，其他条件固定，观察哪个变量能够独立导致并消除历史故障。

### D4：禁止把删除 UV 退化面作为默认修复

几何三角形有效但 UV 三角形退化，直接删除该几何面可能制造新的洞、改变物理结构，或者破坏印刷区域。

应先检查：

- 是否本来就是不使用图像纹理的面。
- 是否存在面角 UV 索引错配。
- 是否是图集映射算法把多个面角压缩到了同一点或同一直线。
- 是否由于三角化后的面角属性未正确继承。

OpenUSD 对 faceVarying 数据有明确的面角对应关系要求，应直接以其规范作为验收依据，而不是另建私有解释。<Cite refs={["turn547334search1","turn547334search3"]}/>

### 2.1 缺陷分类完整性

建议在 D1–D4 之外增加以下审计类别，但不扩大本轮修复范围。

| 编号 | 补充检查 |
|---|---|
| D5 | 零面积几何面、非法索引、NaN/Inf |
| D6 | 非流形顶点、自相交、重叠面 |
| D7 | 三角化前后表面积、边界和结构变化 |
| D8 | UV 面角索引错配、意外镜像、印刷区域错位 |
| D9 | USD orientation、subdivisionScheme、变换语义不一致 |

这些是待检查的缺陷类型，不代表当前资产已经存在这些缺陷。

---

## 三、五项处置建议正式裁决

| 编号 | 处置建议 | 裁决 | 执行约束 |
|---|---|---|---|
| 1 | ApplyMaterialBindingAPI | **ADOPT** | 采用官方 Schema API，新增候选导出版本及回归门禁。 |
| 2 | Manifold / trimesh 对照 | **TRIAL** | 分开测试两个工具，不预设它们具备相同修复能力。 |
| 3 | 零厚度面板实体化 | **ADAPT** | 仅对设计契约要求实体的部件实施，不普遍增厚。 |
| 4 | UV 退化面抑制 | **TRIAL** | 优先修复映射，禁止未经验证直接删除有效几何面。 |
| 5 | 候选版本对照，不覆盖冻结集 | **KEEP** | 继续执行，作为强制治理纪律。 |

### 3.1 MaterialBindingAPI：直接采纳标准

OpenUSD 已经提供 `UsdShade.MaterialBindingAPI.Apply()`，这是标准接口，不需要自行开发替代机制。<Cite refs={["turn547334search0","turn547334search14"]}/>

对于存在直接材质绑定的典型导出场景：

```python
binding_api = UsdShade.MaterialBindingAPI.Apply(prim)
binding_api.Bind(material)
```

实际实现还需要正确处理 GeomSubset、集合绑定及继承关系，不应无差别地给所有 Mesh prim 添加 API。

验收必须同时证明：验证器对应错误消失、原有有效材质绑定没有改变、几何与 UV 不发生变化。

### 3.2 Manifold 与 trimesh：不能混成一个实验组

这两个工具的能力定位不同。

trimesh 提供绕向调整、孔洞填补等网格修复功能；Manifold 主要面向可靠的流形实体建模与布尔运算，对输入网格有相应约束，并非任意损坏网格的通用修复器。<Cite refs={["turn547334search24","turn547334search25","turn547334search26"]}/>

应采用以下四组对照：

| 实验组 | 方法 |
|---|---|
| B0 | 冻结原始输出 |
| B1 | 现有生成端或导出端定向修复 |
| B2 | trimesh 局部网格修复 |
| B3 | Manifold 实体重建或布尔运算 |

所有组使用相同的输入资产、相同的测量工具、相同的验收规则。

对照指标沿用 R02 原定六项指标，另外必须记录包装结构语义、尺寸、合法开口、面角 UV、材质分区是否被破坏。

**拓扑正确只是必要条件，不能以破坏包装设计意图为代价获得拓扑 PASS。**

例如，一个补洞算法把纸杯杯口封闭后，可能提高闭合网格通过率，却降低真实商品资产质量。

---

## 四、usdchecker 红灯与历史合规声明

**裁决：P0 级证据一致性问题，启动独立审计；但暂不判定历史验证结果虚假。**

当前可以确认的是，执行侧报告两个样本在本地指定版本的 usdchecker 中未通过，其中一个通过了自研几何审计。这证明不同检查体系覆盖范围不同。

OpenUSD 官方验证规则确实包含 `MaterialBindingApiAppliedValidator` 及对应的 `MissingMaterialBindingAPI` 错误定义。<Cite refs={["turn547334search16","turn547334search18"]}/>

但 OpenUSD usdchecker 与 NVIDIA 验证器之间不能直接画等号。

### 4.1 立即建立验证器身份台账

历史和当前验证分别记录以下字段：

| 字段 | 必须登记的证据 |
|---|---|
| validator_id | 验证器正式名称 |
| source | 官方仓库、发行包来源 |
| version | 版本号及 commit SHA（适用时） |
| executable_hash | 可执行文件或程序包哈希 |
| usd_runtime | USD SDK 及依赖版本 |
| ruleset | 启用和禁用的完整规则 |
| command | 实际执行命令与参数 |
| environment | 操作系统及运行环境 |
| asset_sha256 | 被检测资产的精确哈希 |
| scope | 全量、抽样或特定品类 |
| exit_code | 原始退出码 |
| raw_log | 完整原始输出 |
| verdict | PASS / FAIL / SKIP / NOT_RUN |

缺失的历史字段明确标记 `UNKNOWN`，不得根据现在的配置反推历史配置。

### 4.2 执行交叉验证矩阵

| 验证对象 | 历史原版验证器 | 当前 usdchecker |
|---|---|---|
| 历史原始资产（哈希一致） | 复跑 | 复跑 |
| 当前 brick 样本 | 执行 | 执行 |
| 当前 rsc 样本 | 执行 | 执行 |
| MaterialBindingAPI 修复候选 | 执行 | 执行 |
| 人工构造缺失 API 的负样本 | 执行 | 执行 |

目标不是让两个工具机械地给出相同结果，而是确定差异来自资产版本、验证器版本、规则覆盖、环境还是执行范围。

若历史验证器暂时不可复现，记录 `HISTORICAL_VALIDATION_UNREPRODUCIBLE`，不允许默认为历史通过已经重新得到证明。

### 4.3 对外声明处理

| 历史声明 | 当前处置 |
|---|---|
| 通过某版本、某规则集的验证器 | 有原始证据则保留 |
| 所有资产均通过官方 USD 验证 | 暂停使用，等待范围复核 |
| 所有资产符合全部 USD 规范 | 禁止使用 |
| 全部资产具有物理真实性 | 禁止以验证器通过作为唯一依据 |

尤其要注意，当前对外页面及已生成的宣传信息图中，涉及“全部通过 USD 验证与物理仿真”的措辞，需要与实际验证对象、规则和样本范围逐一核对。

**保留历史原文，追加更正记录；不得静默覆盖历史证据。**

---

## 五、WP1 盲测协议冻结裁决

**裁决：REVISE BEFORE FREEZE。**

当前协议已经具备基本框架，但尚不具备正式冻结条件。核心原因是它仍可能产生一个数值很高、却不能代表真实行业覆盖能力的结果。

| 协议要素 | 完整性评分 | 裁决 |
|---|---:|---|
| 真实未见样本来源 | 8/10 | 基本成立 |
| 抽样与独立性 | 6/10 | 需补充 |
| 分母定义 | 4/10 | 必须修改 |
| 评价指标 | 5/10 | 必须扩充 |
| 失败判定 | 7/10 | 需补充 |
| 统计方法 | 5/10 | 必须修改 |
| 冻结治理 | 8/10 | 基本成立 |

### P0-01｜禁止把规格缺失与超域混为一类

这是当前 WP1 最严重的问题。

“商品规格缺失”属于输入数据可用性问题，而“结构超出已知包装家族”很可能正是 WP1 要测量的能力缺口。

不能因为一个真实商品没有被现有 77 个结构家族覆盖，就将它从覆盖率分母中剔除。

举一个假设性例子：

<card gap={3}>
  <caption>假设抽取 100 件真实商品（非实验结果）</caption>
  <row align="center">
    <title size="xl" color="default" tabularNums={true}>100</title>
    <caption>真实需求样本</caption>
  </row>
  <box height={24} radius="md" direction="row" gap={0} clip={true}>
    <box background="#42976E" width="50%"/>
    <box background="#E0A04C" width="10%"/>
    <box background="#D16D66" width="20%"/>
    <box background="#9AA8BF" width="15%"/>
    <box background="#D8DDE6" width="5%"/>
  </box>
  {#each [{t:"成功交付",n:50,c:"#42976E"},{t:"命中家族但生成失败",n:10,c:"#E0A04C"},{t:"未知结构",n:20,c:"#D16D66"},{t:"关键规格缺失",n:15,c:"#9AA8BF"},{t:"预定义产品域之外",n:5,c:"#D8DDE6"}] as a}
    <row align="center">
      <box background={a.c} size="10px" radius="sm"/>
      <text size="sm">{a.t}</text>
      <spacer/>
      **{a.n}**
    </row>
  {/each}
  <divider/>
  <grid columns={2}>
    <grid-item>
      <caption>错误剔除未知结构后的覆盖率</caption>
      <title size="2xl" color="danger">100%</title>
      <caption>60 ÷ 60</caption>
    </grid-item>
    <grid-item>
      <caption>有效输入商品结构覆盖率</caption>
      <title size="2xl">75%</title>
      <caption>60 ÷ 80</caption>
    </grid-item>
    <grid-item>
      <caption>结构命中后生成成功率</caption>
      <title size="xl">83.3%</title>
      <caption>50 ÷ 60</caption>
    </grid-item>
    <grid-item>
      <caption>域内端到端交付率</caption>
      <title size="xl">52.6%</title>
      <caption>50 ÷ 95</caption>
    </grid-item>
  </grid>
</card>

同一批样本可以同时产生 100%、83.3% 和 52.6% 的数字。如果不治理分母，指标将失去决策意义。

### P0-02｜建立互斥、完备的逐件终态

建议冻结以下七种终态：

| 状态 | 定义 |
|---|---|
| OUT_OF_SCOPE | 不属于预先冻结的产品适用域 |
| INPUT_INSUFFICIENT | 域内商品，但合法输入不足 |
| FAMILY_NOT_COVERED | 输入充分，现有家族不能表达 |
| FAMILY_ADAPTATION_REQUIRED | 必须修改家族模板 |
| GENERATION_FAILED | 家族适用，但生成或验收失败 |
| VALIDATION_PENDING | 已生成，部分必需验证尚未完成 |
| DELIVERED | 无模板改造，通过全部必需验收 |

七个状态数量之和必须等于 100，每件商品只能有一个最终状态。中间过程可以另外记录。

只有 `OUT_OF_SCOPE` 可以从产品域覆盖率的分母中剔除，且产品域定义必须早于样本抽取。

### P0-03｜补齐四层成功率指标

冻结以下四个主要指标，不再仅报告命中后的生成成功率。

| 指标 | 分子 | 分母 |
|---|---|---|
| 输入可用率 | 输入充分的域内商品 | 全部域内商品 |
| 结构覆盖率 | 无需改造即可表达的商品 | 输入充分的域内商品 |
| 条件生成成功率 | 完整验收通过的商品 | 无需改造即可表达的商品 |
| 端到端交付率 | 完整验收通过的商品 | 全部域内商品 |

另行报告全部 100 件样本的交付率、域外比例、家族改造率、失败原因分布。

**端到端交付率应该是 WP1 的首要业务指标。**

### P0-04｜不能只有合规门禁，必须有真实商品一致性门禁

这是第二个关键缺陷。

author_compile、官方 Validator、MuJoCo 通过，并不能证明生成的资产与目标商品一致。

假如输入一盒牛奶，编译器输出一个合规、可仿真、但长宽高错误的纸盒，当前协议仍可能将其判定为成功。

新增：

| 门禁 | 验收对象 |
|---|---|
| W1 | 包装结构家族与真实商品一致 |
| W2 | 外形尺寸及关键结构尺寸一致 |
| W3 | 开口、封合、铰接等结构特征一致 |
| W4 | 印刷区域、方向、图案对应关系符合交付等级 |
| W5 | 质量与物理属性符合目标交付等级 |
| W6 | 编译、标准合规及适用的物理测试通过 |

尺寸误差阈值需要结合测量精度和业务用途在冻结协议中明确，不能等看到实验结果以后再制定。

没有真实质量数据的商品，不得宣称质量属性已被真实商品验证；没有铰接结构的商品不应强制执行铰接门禁，应标记 `NOT_APPLICABLE`。

### P0-05｜冻结合法输入与盲测隔离

“从未参与家族设计与调参”需要具有可审计的操作定义。

必须冻结：

- 商品主数据快照及哈希。
- GTIN、品牌、商品系列与结构变体的去重规则。
- 编译器 commit、77 家族版本、生成配置及门禁版本。
- 合法输入字段，例如尺寸、材质、包装形态、商品印刷图等。
- 仅用于评测的参考照片、人工标注和测量数据。

推荐采用双角色分工：

<box border radius="lg" padding={3} gap={2}>
  <grid columns={2} gap={2}>
    <grid-item>
      <box background="surface-secondary" radius="md" padding={3}>
        **样本与评测侧**

        <text size="sm">掌握真实商品、标准答案、参考图及验收规则。</text>
      </box>
    </grid-item>
    <grid-item>
      <box background="surface-secondary" radius="md" padding={3}>
        **编译执行侧**

        <text size="sm">只能取得预定义合法输入及冻结编译器。</text>
      </box>
    </grid-item>
  </grid>
  <svg viewBox="0 0 300 55" width="100%">
    <path d="M75 0V13H225V0 M150 13V23" fill="none" stroke="#8b99b0" strokeWidth="1.5"/>
    <rect x="70" y="23" width="160" height="28" rx="5" fill="#e8edf8" stroke="#9aa8c3"/>
    <text x="150" y="41" fontSize="11" fontWeight="bold" textAnchor="middle" fill="#374c76">独立比对与统一裁决</text>
  </svg>
</box>

此外，“与 9,386 冻结基线零接触声明”措辞不准确。编译器本身已经基于此前积累的结构家族开发。

建议改成：**盲测目标商品及保留评测证据未参与编译器开发、调参和候选生成过程。**

### P0-06｜统计方法修正

“全部指标附带 95% 置信区间，n 小于 150 时使用精确二项”不成立。

精确二项置信区间适用于相应二项抽样模型下的比例指标，不适用于人工耗时、机器成本等连续变量，也不能不考虑抽样设计就直接用于分层总体推断。

冻结要求：

| 指标类型 | 统计方法 |
|---|---|
| 简单随机样本二项比例 | Wilson 或 Clopper–Pearson 区间 |
| 分层抽样总体比例 | 按实际总体层权重估计，采用相应分层方差或重抽样方法 |
| 人工及机器耗时 | 均值、中位数、P90，必要时采用适当的 Bootstrap 区间 |
| 失败率 | 报告分子、分母及失败分类 |
| 样本稀少的家族 | 描述性统计，不强行推断总体表现 |

100 个 SKU 可以作为 WP1-Pilot，但不足以单独证明 77 个结构家族的全面可靠性，更不能直接代表整个零售行业。

建议正式命名为 **WP1-Pilot-100**。

### P0-07｜单位成本必须具有经济学含义

人工分钟与机器分钟不可直接相加作为经济成本。它们可以分别作为资源消耗量记录，但经济成本应该采用：

\[
C_i=r_h t_{h,i}+r_m t_{m,i}+C_{\mathrm{external},i}
\]

其中人工费率、机器费率及外部服务费用均提前冻结，并报告失败样本成本和返工成本。

最终还应报告：

\[
C_{\mathrm{delivered}}=
\frac{\text{全部样本实际发生的成本}}
{\text{成功交付资产数量}}
\]

否则失败越多，反而可能因为只统计成功件而让单位成本看起来越低。

### P0-08｜环境未就绪不得提前宣告成功

WP1 可以在冻结后分阶段运行，但如果 NVIDIA Validator 或适用的物理测试没有完成，相关样本只能登记为 `VALIDATION_PENDING`。

不得使用本地自研门禁替代官方验证，再计入最终成功率。

---

## 六、下一轮执行安排与送审要求

我不建议立即启动大规模资产修复。下一轮首先需要解决测量工具、缺陷事实和盲测协议三方面的问题。

<card gap={3}>
  <row align="center">
    <title size="md">R09 工作包</title>
    <spacer/>
    <caption>建议工期：5 个工作日</caption>
  </row>
  <caption>以下为建议排期，非已经确认的团队资源安排。</caption>
  {#each [{n:"WP-A0",t:"审计器独立验收",s:0,d:2,c:"#6078C5"},{n:"WP-A1",t:"107 件缺陷重新分类",s:2,d:1,c:"#6078C5"},{n:"WP-A2",t:"D1 与黑色渲染根因实验",s:3,d:2,c:"#8064C4"},{n:"WP-V",t:"验证器证据追溯",s:0,d:3,c:"#C18B43"},{n:"WP-M",t:"MaterialBindingAPI 候选修复",s:3,d:2,c:"#42976E"},{n:"WP-P",t:"WP1 协议 v0.2",s:0,d:2,c:"#6078C5"}] as a}
    <box gap={1}>
      <row>
        <text weight="medium" size="sm">{a.n} · {a.t}</text>
      </row>
      <grid columns={5} gap={1}>
        {#each Array.from({length:5},(_,i)=>i) as i}
          <grid-item>
            <box height={12} radius="sm" background={i>=a.s&&i<a.s+a.d?a.c:"#E5E7EB"}/>
          </grid-item>
        {/each}
      </grid>
    </box>
  {/each}
  <grid columns={5} gap={1}>
    {#each [1,2,3,4,5] as d}
      <grid-item><text textAlign="center" size="xs" color="secondary">Day {d}</text></grid-item>
    {/each}
  </grid>
</card>

下一轮必须提交以下六项制品。

{@body const tasks=[["R02-A0","审计器验收报告、合成真值测试集与负向测试"],["R02-A1","107 件重新审计结果、失败集合交叉表"],["R02-A2","D1 首个故障阶段定位及购物车单变量因果实验"],["R02-V","验证器身份台账、历史证据复核报告"],["R02-M","MaterialBindingAPI 候选修复与回归报告"],["WP1-v0.2","补齐八项 P0 的新版盲测协议"]]}
{@body const [done,setDone]=DIL.useState([false,false,false,false,false,false])}
<card gap={3}>
  <row align="center">
    **R09 送审清单**
    <spacer/>
    <caption>{done.filter(Boolean).length}/6</caption>
  </row>
  {#each tasks as t,i}
    <checkbox checked={done[i]} onChange={v=>setDone(old=>old.map((x,j)=>i===j?v:x))}>
      **{t[0]}**

      <caption>{t[1]}</caption>
    </checkbox>
  {/each}
  <button block color="secondary" variant="outline" onClick={()=>GenUI.copy(tasks.map((t,i)=>(done[i]?"[x] ":"[ ] ")+t.join(" — ")).join("\n"))}><icon name="copy" size="sm"/> 复制执行清单</button>
</card>

Manifold/trimesh 正式修复对照实验，应在 R02-A0 与 A1 完成之后启动，避免使用错误的审计器对候选工具进行胜负裁决。

## 七、战略层评价

我认为 R02-A 目前最有价值的产出，并不是发现了多少件不合格资产，而是暴露出了我们此前资产质量体系中的三个认知漏洞：

| 此前容易形成的判断 | 本轮应该建立的正确认知 |
|---|---|
| 渲染效果好，资产就正确 | 视觉正确不等于几何正确 |
| 官方验证器通过，资产就合规 | 合规必须限定工具、版本与规则集 |
| 参数化能够生成大量 SKU，就具备行业覆盖能力 | 已知样本生成能力不等于未知真实商品交付能力 |

这些发现说明，将项目从“零售数字资产生成工具”升级为“零售数字资产编译器”的方向是合理的。

真正成熟的编译器不仅能够生成结果，还应该理解结构语义、拒绝不合法的输入、明确输出契约，并且能够解释失败发生在哪个阶段。

这也是未来值得沉淀到商品数字对象本体和编译器质量知识库中的长期资产。

---

## 八、最终签核

| 裁决事项 | 最终决定 |
|---|---|
| R02-A 缺陷发现 | ACCEPTED |
| R02-A 审计方法验收 | CONDITIONAL PASS |
| D1–D4 根因确认 | NOT CONFIRMED |
| MaterialBindingAPI | ADOPT |
| Manifold/trimesh | TRIAL |
| 零厚度实体化 | ADAPT |
| UV 退化面抑制 | TRIAL |
| 冻结资产保护 | KEEP |
| 历史合规声明 | UNDER REVIEW |
| WP1 正式冻结 | NOT APPROVED |
| WP1 实验启动 | PROHIBITED BEFORE FREEZE |

**R08 FINAL VERDICT：CONDITIONAL PASS**

批准进入审计器整改、根因定位、验证器复核与协议修订阶段。不批准批量修复 9,386 件冻结资产，不批准 WP1 正式开跑。

下一轮最重要的验收对象不是修复了多少资产，而是：**我们是否已经建立了一套值得信任的资产质量测量体系。**