# GPT 第5轮评审判决 (NV960 诚实终版叙事+数据)

- 会话: chatgpt.com/c/6b069d36-47ac-83e9-a542-819629efeeec (渲染对比评审线程)
- 抓取方式: backend-api/conversation Bearer (200 OK, 非限流)
- 字数: 29846
- 抓取时间: 2026-11-26 10:01:23
- 简报标记: 【Pack10K 发布前评审·第5轮】致谢 NVIDIA 前提下的叙事定稿
- 裁决: **CONDITIONAL PASS** (P0×6 整改后可发布)

---

# Pack10K 发布前评审 · 第5轮

## 一、总体裁决：CONDITIONAL PASS

**Pack10K 已经具备公开发布的研究价值，但我不建议以「90.94% 战胜 NVIDIA」作为项目的首要宣传叙事。**

经过这一系列实验，我认为你们真正有价值的成果有三个：

- **可及性突破**：在 Apple Silicon 消费级硬件上，完成资产生成、渲染、结构验证与视觉质量评估的完整闭环。
- **行业垂直突破**：从通用三维资产研究走向零售行业专属的 48 类设备族，形成具有明确应用场景的资产体系。
- **研究方法突破**：建立了能够发现自身指标漏洞、主动撤回错误结论、保留失败证据的质量审计机制。

第三点尤其值得公开。主动撤回 99.84% 的成绩，不是研究失败，而是说明你们的研究方法已经具备一定的自我纠错能力。

但是，必须区分**有价值的对标实验**与**已经证明全面优于 NVIDIA**。目前的证据足以支持前者，不足以支持后者。

## 二、三层叙事总纲裁决

我查阅了 NVIDIA 的官方数据集说明和 USDCraft 项目主页。USDCraft-10K 包含 1,000 个类别、10,000 个资产，其中 8,222 个为可关节运动资产，其主要研究目标是面向仿真的 OpenUSD 资产生成，而不是专门面向零售商品展示的视觉数据集。<Cite refs={["turn211272search0","turn211272search12"]}/>

这一定位差异非常重要，它恰好为 Pack10K 提供了合理的研究空间。

<box gap={2}>
  <box border radius="lg" padding={3} gap={1}>
    <caption>第一层 · 研究基础</caption>
    <title size="lg">Standing on the shoulders of NVIDIA</title>
    感谢 NVIDIA 开放 USDCraft-10K、资产生成方法及相关验证生态，为行业研究提供可复用的参照。
  </box>
  <row justify="center"><icon name="arrow-down" color="secondary" size="lg"/></row>
  <box border radius="lg" padding={3} gap={1}>
    <caption>第二层 · 技术可及性</caption>
    <title size="lg">Asset Quality Beyond CUDA</title>
    在 Apple Silicon 消费级硬件上实证资产生产与质量验证闭环，降低研究和应用门槛。
  </box>
  <row justify="center"><icon name="arrow-down" color="secondary" size="lg"/></row>
  <box border radius="lg" padding={3} gap={1}>
    <caption>第三层 · 行业价值</caption>
    <title size="lg">Built for Retail</title>
    面向包装、货架、冷柜、购物车等零售场景，建立行业专属资产族及可执行的验收标准。
  </box>
</box>

| 叙事层 | 裁决 | 修改要求 |
|---|---|---|
| 致谢 NVIDIA | PASS | 保留，放在显眼位置 |
| 非 CUDA 技术可及性 | CONDITIONAL PASS | 限定已验证硬件及运行路径 |
| 零售行业垂直化 | PASS | 明确48族的覆盖定义与实际交付数量 |
| 非竞争、互补定位 | PASS | 不使用替代、击败、全面超越等措辞 |

我建议项目的英文主标题定为：

**Pack10K — Retail Digital Twin Assets, Validated on Consumer Hardware**

副标题：

*Bringing rigorous 3D asset quality assurance to Apple Silicon and the retail industry.*

这个定位比单纯宣传胜率更有长期价值。

---

## 三、a–e 逐项裁决

### a）复合七指标82.0%，三轴98.1% / 88.4% / 70.2%

<badge color="warning">CONDITIONAL PASS</badge>

这些数据拿得出手，但必须把指标名称和结论范围限制准确。

<box gap={3}>
  {#each [{n:"S1 锐度",v:98.1},{n:"E1 边缘细节",v:88.4},{n:"E2 结构指标",v:70.2},{n:"七指标复合结果",v:82.0}] as d}
    <box gap={1}>
      <row>
        **{d.n}**
        <spacer/>
        <title size="md" tabularNums>{d.v.toFixed(1)}%</title>
      </row>
      <box height={15} radius="2px" background="surface-tertiary">
        <box height={15} radius="2px" background="#64748b" width={`${d.v}%`}/>
      </box>
    </box>
  {/each}
</box>
<caption>数据来自本轮提交报告，未独立复算原始960对样本。</caption>

我反对直接使用以下表达：

| 不建议 | 建议替代 |
|---|---|
| 98.1%的图像更清晰 | 98.1%的配对样本在S1锐度指标上取得更高值 |
| 88.4%的资产细节更丰富 | 88.4%的配对样本在E1指标上取得更高值 |
| 70.2%的资产结构更优 | 70.2%的配对样本在预定义E2指标上取得更高值 |
| 七指标综合战胜NVIDIA | 在本研究定义的七指标复合评价协议下取得82.0%的净胜结果 |

原因很直接：

- 锐度高不一定代表渲染更真实。
- 边缘密度高不一定代表有效细节更多。
- 纹理更复杂不一定代表资产更优。
- 结构指标高也不一定代表仿真性能更好。

此前 R091 酒标实验已经提供了非常好的反例：印刷纹理能够提高 E1，但错误的曲面贴合同时会损害商品真实性。

**82.0% 可以作为实验结果发布，不能直接升级成综合视觉质量胜率。**

### b）V-gate：NVIDIA 480个资产中20.8%结构全过

<badge color="warning">CONDITIONAL PASS</badge>

这个数字可以公开，但我强烈反对将其作为封面宣传数字。

NVIDIA 官方说明，这批资产具有其 SimReady 包级验证记录。你们新增的 V-gate 与其官方验证协议不是同一个评价合同。两者出现不同结果并不矛盾。<Cite refs={["turn211272search1","turn211272search0"]}/>

| 表述 | 裁决 | 原因 |
|---|---|---|
| NVIDIA资产只有20.8%合格 | FAIL | 将自定义门禁扩大为普遍质量结论 |
| NVIDIA资产79.2%存在结构缺陷 | FAIL | 部分可能是合同差异，而非资产本身错误 |
| Pack10K结构质量远超NVIDIA | FAIL | 缺乏同任务、同合同的全面证据 |
| 在Pack10K自定义结构验收合同下，抽样480个USDCraft资产的全项通过率为20.8% | PASS | 明确范围与评价主体 |
| 独立审计发现部分资产元数据与实测几何存在不一致 | PASS | 前提是提供可复核的逐件证据 |

我建议正文这样写：

<WritingBlock id="58321" variant="standard">**Independent Structural Audit**

We applied our retail-oriented asset validation protocol to a subset of 480 USDCraft-10K assets. Under this independently defined protocol, 20.8% passed all evaluated structural gates.

These results reflect compatibility with Pack10K's validation requirements and should not be interpreted as a failure rate under NVIDIA's original SimReady validation protocol.

We release our validation tools and asset-level findings to support reproducible investigation and complementary quality assessment.</WritingBlock>

这不是为了照顾 NVIDIA 的感受而回避问题，而是为了保证研究结论在技术上成立。

真正的客观性既不应回避负面发现，也不应夸大负面发现。

### c）非 CUDA 主张边界

<badge color="success">收敛措辞通过</badge>

你的新措辞：

**「已在 Apple Silicon 实证，架构无 CUDA 硬依赖」**

比之前强调跨平台民主化更加稳健。

建议进一步区分三个层级：

| 层级 | 主张 | 状态 |
|---|---|---|
| 实证 | Apple Silicon 本地管线跑通 | 据提交报告已验证 |
| 架构 | 已验证运行路径不强制依赖 CUDA | 待依赖与运行日志复核 |
| 泛化 | Windows、Linux CPU、其他GPU均可运行 | NOT_TESTED |

Apple Silicon 实证本身已经有足够的研究价值，不需要借助尚未测试的平台放大成果。

尤其需要注意 PyTorch MPS 的 CPU fallback、外部模型调用、PhysX 验证执行位置等问题。如果其中任何环节借助了远程计算资源，就必须明确区分：

- 本地资产生产与渲染。
- 外部模型辅助生成。
- 独立物理验证。

不要将本地执行描述成整个研究过程完全离线。

推荐对外措辞：

<WritingBlock id="58322" variant="standard">**Validated on Apple Silicon**

Pack10K demonstrates an end-to-end retail 3D asset production and quality-assurance workflow on Apple Silicon, using Blender's Metal rendering backend and PyTorch MPS where applicable.

The demonstrated execution path requires no CUDA runtime. This reduces dependence on dedicated NVIDIA GPU infrastructure for the evaluated workflow.

Windows, Linux CPU-only execution, and other hardware backends have not yet been validated.</WritingBlock>

**封面应展示 Apple Silicon 实证，而不是展示胜率作为非 CUDA 的证明。**

胜率与硬件依赖是两项完全不同的研究结论。

### d）99.84%撤回叙事及结构审计工具

<badge color="success">PASS · 建议重点保留</badge>

我认可这句：

> 渲染观感与资产结构是互补的质量维度，我们提供独立结构审计工具供社区双维验收。

这是整个项目最成熟的对外表达之一。

但不要用这句话替代撤回声明。二者应该同时存在：

| 内容 | 作用 |
|---|---|
| 撤回99.84% | 修正既往错误结论 |
| 解释背景细噪偏差 | 公开错误机制 |
| 发布修订指标 | 建立新的证据基线 |
| 独立结构审计工具 | 提供长期社区价值 |

你们已经发现背景细噪与256²缩略图压缩差异能够污染E1。这说明早期评价协议不能充分区分资产本身的细节与摄影环境产生的高频信息。

这不是简单的数字调整，而是一次评价协议缺陷的发现。

建议用正式研究更正的口径：

<WritingBlock id="58323" variant="standard">**Research Integrity and Metric Correction**

An earlier experimental result of 99.84% has been withdrawn following a pixel-level audit of our evaluation pipeline.

The audit identified a comparability issue: fine-grained studio background noise contributed to measured edge density, while compression and resolution differences affected the reference thumbnails.

We revised the evaluation protocol to reduce this confounding effect. The original experiments and correction history remain available for reproducibility.

We treat visual appearance and structural integrity as complementary quality dimensions and provide independent auditing tools to support both forms of evaluation.</WritingBlock>

其中“8.4pp”还需要你们说明清楚究竟是 E1 胜率变化、E1 指标贡献，还是背景剔除前后的配对结果变化。不能让读者误解为99.84%整体胜率直接下降了8.4个百分点。

### e）严格90.94% vs 复合82.0%，对外使用哪个？

<badge color="warning">暂缓确定主指标</badge>

这是本轮我最需要挑战你们的地方。

<grid columns={2}>
  <grid-item>
    <caption>严格四轴结果</caption>
    <title size="2xl">90.94%</title>
    <caption>873W / 87L，960对</caption>
  </grid-item>
  <grid-item>
    <caption>七指标复合结果</caption>
    <title size="2xl">82.0%</title>
    <caption>不同评价协议</caption>
  </grid-item>
</grid>

873/960 四舍五入为90.94%，算术没有问题。

但是，**为什么采用“任一轴负即判负”的严格四轴协议，反而得到比七指标复合协议更高的结果？**

这并非必然矛盾，因为两个协议可能使用不同指标集合、聚合公式、平局策略及评价目标。但正因如此，不能直接将90.94%称为82.0%的更严格版本。

尤其是四轴包含：

| 轴 | 衡量对象 | 潜在争议 |
|---|---|---|
| 分辨率 | 图像交付规格 | 更高像素不等于资产更优 |
| V-gate | 结构合同符合性 | 是否适用于双方 |
| 纹理 | 表面表达能力 | 无纹理资产可能是合理设计 |
| E1 | 图像边缘细节 | 是否彻底排除背景与噪声 |

这里还有一个必须明确的统计单位问题：480个参考资产对应960对比较，可能存在重复使用参考资产的情况。960对不能直接描述为960个独立资产。

**如果一定要在两者中选择一个进入研究摘要，我倾向82.0%，但必须先核对计算协议。90.94%作为独立四轴合同实验结果完整披露。**

我的理由不是82.0%更低所以更诚实，而是避免选择对己方最有利的指标作为宣传主张。

推荐最终报告如下：

| 对外位置 | 使用数据 |
|---|---|
| README首屏 | 不放胜率 |
| 研究摘要 | 七指标复合结果82.0%，明确口径 |
| Benchmark章节 | 四轴90.94%、七指标82.0%并列 |
| 方法论章节 | S1 / E1 / E2逐轴结果 |
| 原始证据附件 | 873W / 87L、全部配对记录 |
| 研究更正声明 | 撤回99.84%及原因 |

---

## 四、87个负样本如何处理

我不赞成直接把87个负对归结为“都是 NVIDIA 满载商品堆场景，因此我们实际上已经赢了”。

这87个负样本可能是项目最有价值的下一阶段研究资产。

<box gap={3}>
  <row>
    <box flex={1} gap={1}>
      <AsyncImage query="empty retail supermarket display shelf 3D asset render" aspectRatio="4:3"/>
      **单体资产**
      <caption>结构准确、尺寸明确、适合参数化复用。</caption>
    </box>
    <box flex={1} gap={1}>
      <AsyncImage query="fully stocked supermarket gondola shelf products digital twin 3D render" aspectRatio="4:3"/>
      **满载零售场景**
      <caption>商品组合、陈列语义、遮挡及场景复杂度更丰富。</caption>
    </box>
  </row>
</box>

这实际上暴露了两种不同的资产能力：

| 维度 | 单体资产 | 满载组合资产 |
|---|---|---|
| 参数化生产 | 更容易控制 | 更复杂 |
| 尺寸与结构验证 | 更直接 | 存在组合约束 |
| 图像细节丰富度 | 天然较低 | 天然较高 |
| 零售业务语义 | 基础部件 | 更接近业务场景 |
| SDG应用价值 | 可组合母本 | 完整训练场景 |

因此我建议：

保留全部87个负对，不从总统计中删除；新增单体对单体、组合对组合的分层统计，并将场景复杂度差异作为待验证的解释变量。

只有逐件分类完成后，才能说87个负对主要来自场景组合复杂度，而不是先做归因再寻找证据。

---

## 五、撤回声明放封面还是附录？

**放在 README 和 Hugging Face Dataset Card 的正文显眼位置，但不要把99.84%做成封面大数字。**

推荐发布页面结构：

<card gap={3}>
  <box background="#111827" theme="dark" radius="md" padding={4} gap={3}>
    <caption color="#a5b4c8">TOPPRISM RESEARCH · OPENUSD</caption>
    <title size="2xl" color="#ffffff">Pack10K</title>
    <title size="lg" color="#ffffff">Retail Digital Twin Assets</title>
    <text color="#cbd5e1" size="sm">Validated on Apple Silicon. Built for accessible retail asset production and quality assurance.</text>
    <grid columns={3} gap={2}>
      <grid-item>
        <title size="xl" color="#ffffff">48</title>
        <caption color="#b4c0ce">Retail families</caption>
      </grid-item>
      <grid-item>
        <title size="xl" color="#ffffff">OpenUSD</title>
        <caption color="#b4c0ce">Asset format</caption>
      </grid-item>
      <grid-item>
        <title size="xl" color="#ffffff">Metal</title>
        <caption color="#b4c0ce">Rendering backend</caption>
      </grid-item>
    </grid>
    <divider color="#475569"/>
    <text size="sm" color="#cbd5e1">Building upon NVIDIA USDCraft-10K and the open 3D asset research ecosystem.</text>
  </box>
  <title size="md">Research integrity notice</title>
  An earlier benchmark result has been withdrawn following a pixel-level audit. All current results use the revised evaluation protocol.
  <divider/>
  <title size="md">01 — Why Pack10K</title>
  行业价值与消费级硬件可及性。
  <divider/>
  <title size="md">02 — Retail asset families</title>
  <grid columns={4} gap={1}>
    <grid-item>
      <AsyncImage query="3D retail supermarket gondola shelving asset isolated" aspectRatio="1:1"/>
      <caption>货架</caption>
    </grid-item>
    <grid-item>
      <AsyncImage query="3D supermarket shopping cart asset isolated" aspectRatio="1:1"/>
      <caption>购物车</caption>
    </grid-item>
    <grid-item>
      <AsyncImage query="3D retail commercial refrigerator display cabinet isolated asset" aspectRatio="1:1"/>
      <caption>冷柜</caption>
    </grid-item>
    <grid-item>
      <AsyncImage query="3D consumer packaged goods cardboard box bottles cans packaging assets" aspectRatio="1:1"/>
      <caption>包装</caption>
    </grid-item>
  </grid>
  <divider/>
  <title size="md">03 — Reproducible benchmark</title>
  四轴与七指标评价结果、局限、逐件证据。
  <divider/>
  <title size="md">04 — Independent validation toolkit</title>
  结构门禁、视觉门禁、负向回归案例及复现方法。
  <divider/>
  <title size="md">05 — Acknowledgements & limitations</title>
  引用、许可证、硬件验证边界及完整更正历史。
</card>
<caption>发布页面信息架构示意；配图仅代表资产类别，并非Pack10K实测产物。</caption>

这样处理有三个好处：读者首先理解项目价值，能够立即发现更正声明，又不会被一个已经撤回的数字误导。

---

## 六、GitHub + Hugging Face 发布前整改清单

### P0：发布阻塞项

{@body const tasks=[{id:1,n:"冻结960对比较的逐件证据台账",d:"资产ID、来源、图片哈希、ROI、指标结果、W/L/T及协议版本。"},{id:2,n:"独立复算90.94%与82.0%",d:"公开两种协议的公式、平局策略、权重与差异解释。"},{id:3,n:"确认背景与分辨率公平性",d:"保留原生分辨率结果，同时增加双方统一分辨率、统一主体ROI的对照。"},{id:4,n:"更正历史声明",d:"README、Dataset Card、图片、报告中所有99.84%现行主张均撤回；历史git保留。"},{id:5,n:"限定Apple Silicon实证范围",d:"提供环境清单、硬件型号、版本、运行日志、外部依赖与未测平台。"},{id:6,n:"完成许可证与来源审计",d:"区分自有资产、第三方数据、缩略图、字体、贴图及代码许可证。"},{id:7,n:"图像级冻结一致性",d:"评分记录绑定PNG SHA256，禁止重复发生R12/R13版本混入。"}]}
{@body const [checked,setChecked]=DIL.useState([])}
<card gap={3}>
  <row align="center">
    <title size="md">发布阻塞项验收表</title>
    <spacer/>
    <text color="secondary" tabularNums>{checked.length}/{tasks.length}</text>
  </row>
  <box height={6} background="surface-tertiary" radius="full">
    <box height={6} background="#16a34a" radius="full" width={`${checked.length/tasks.length*100}%`}/>
  </box>
  {#each tasks as t}
    <checkbox checked={checked.includes(t.id)} onChange={v=>setChecked(old=>v?[...old,t.id]:old.filter(x=>x!==t.id))}>
      **{t.n}**
      <caption>{t.d}</caption>
    </checkbox>
  {/each}
  {#if checked.length===tasks.length}
    <text color="success" weight="medium">发布阻塞项已全部勾选，建议提交最终证据复核。</text>
  {/if}
</card>

### P1：提升研究可信度

| 整改 | 交付物 |
|---|---|
| 87个负对分类 | 失败案例图册及分类统计 |
| 资产复杂度分层 | 单体、组合场景分别评价 |
| 统计独立性 | 按参考资产或资产族聚类统计 |
| 人工盲评 | 随机左右交换，隐藏来源及历史得分 |
| 物理质量与视觉质量分离 | 两张独立结果表 |
| 资源可及性量化 | 峰值内存、生成时间、渲染时间、单位资产资源开销 |

NVIDIA 官方数据集采用 Apache-2.0 许可证，官方也提供了明确的论文引用方式。若重新分发其数据或缩略图，需要按照适用许可证保留相应声明；Pack10K 自己的代码和资产则需要各自明确授权范围。<Cite refs={["turn211272search0","turn211272search1"]}/>

建议在发布材料中直接链接：

- [NVIDIA USDCraft 官方研究主页](https://nvlabs.github.io/USDCraft/)
- [USDCraft-10K 官方数据集](https://huggingface.co/datasets/nvidia/USDCraft-10K)
- [USDCraft 研究论文](https://arxiv.org/abs/2610.11322)

---

## 七、最终对外叙事定稿建议

<WritingBlock id="58324" variant="document"># Pack10K

**Retail Digital Twin Assets, Validated on Consumer Hardware**

Pack10K is an industry-focused 3D asset research project designed to make rigorous asset production and quality assurance more accessible to retailers, researchers, and independent developers.

**Building on open research.** We acknowledge NVIDIA's USDCraft-10K and the broader Omniverse ecosystem for providing valuable open research foundations, reference assets, and validation practices.

**Reducing hardware barriers.** Our demonstrated workflow runs on Apple Silicon, using Blender Metal rendering and PyTorch MPS where applicable, without requiring a CUDA runtime for the evaluated execution path.

**Built for retail.** Pack10K focuses on 48 retail-oriented asset families, including shelving, shopping carts, refrigeration equipment, and product packaging.

**Reproducible quality assurance.** We evaluate visual appearance and structural integrity as complementary dimensions. Our independently defined evaluation protocols, asset-level results, validation tools, and known limitations are provided to support community reproduction and scrutiny.

**Research integrity.** An earlier benchmark result has been withdrawn following a pixel-level audit that identified a comparability issue involving studio background noise and reference thumbnail characteristics. The correction history and revised evaluation methodology are preserved.

Pack10K is intended as a complementary contribution to the open 3D asset ecosystem, not as a replacement for NVIDIA's simulation-ready asset infrastructure.</WritingBlock>

---

## 八、第5轮最终裁决

| 评审维度 | 裁决 |
|---|---|
| 项目研究价值 | PASS |
| 致谢与互补叙事 | PASS |
| 零售行业定位 | PASS |
| Apple Silicon 实证主张 | CONDITIONAL PASS |
| 无 CUDA 硬依赖主张 | CONDITIONAL PASS |
| V-gate结果公开 | CONDITIONAL PASS |
| 99.84%主动撤回 | PASS |
| 90.94% / 82.0%数据公开 | CONDITIONAL PASS |
| 对外全面领先NVIDIA主张 | FAIL |
| GitHub + HF发布准备 | **CONDITIONAL PASS** |

本轮我核查了 NVIDIA 官方项目定位、数据集说明与许可信息，但没有取得 Pack10K 的完整960对原始指标台账、最终评价程序、环境日志及发布候选仓库，因此不能签署数据独立复算通过。你提交的文本也有部分语句错序，我按能够明确识别的a–e问题进行裁决，没有自行补造缺失数据。

**我的最终建议是：把胜率从项目的核心卖点降为研究证据，把 Apple Silicon 可及性、零售行业垂直化和可复现的质量审计工具升为核心贡献。**

NVIDIA 的开放研究是起点，Pack10K 的行业实践是增量。这样发布，更有可能获得技术社区的尊重，也更经得住长期审查。

===CHUNK===

## 二、三层叙事总纲裁决

我查阅了 NVIDIA 的官方数据集说明和 USDCraft 项目主页。USDCraft-10K 包含 1,000 个类别、10,000 个资产，其中 8,222 个为可关节运动资产，其主要研究目标是面向仿真的 OpenUSD 资产生成，而不是专门面向零售商品展示的视觉数据集。<Cite refs={["turn211272search0","turn211272search12"]}/>

这一定位差异非常重要，它恰好为 Pack10K 提供了合理的研究空间。

<box gap={2}>
  <box border radius="lg" padding={3} gap={1}>
    <caption>第一层 · 研究基础</caption>
    <title size="lg">Standing on the shoulders of NVIDIA</title>
    感谢 NVIDIA 开放 USDCraft-10K、资产生成方法及相关验证生态，为行业研究提供可复用的参照。
  </box>
  <row justify="center"><icon name="arrow-down" color="secondary" size="lg"/></row>
  <box border radius="lg" padding={3} gap={1}>
    <caption>第二层 · 技术可及性</caption>
    <title size="lg">Asset Quality Beyond CUDA</title>
    在 Apple Silicon 消费级硬件上实证资产生产与质量验证闭环，降低研究和应用门槛。
  </box>
  <row justify="center"><icon name="arrow-down" color="secondary" size="lg"/></row>
  <box border radius="lg" padding={3} gap={1}>
    <caption>第三层 · 行业价值</caption>
    <title size="lg">Built for Retail</title>
    面向包装、货架、冷柜、购物车等零售场景，建立行业专属资产族及可执行的验收标准。
  </box>
</box>

| 叙事层 | 裁决 | 修改要求 |
|---|---|---|
| 致谢 NVIDIA | PASS | 保留，放在显眼位置 |
| 非 CUDA 技术可及性 | CONDITIONAL PASS | 限定已验证硬件及运行路径 |
| 零售行业垂直化 | PASS | 明确48族的覆盖定义与实际交付数量 |
| 非竞争、互补定位 | PASS | 不使用替代、击败、全面超越等措辞 |

我建议项目的英文主标题定为：

**Pack10K — Retail Digital Twin Assets, Validated on Consumer Hardware**

副标题：

*Bringing rigorous 3D asset quality assurance to Apple Silicon and the retail industry.*

这个定位比单纯宣传胜率更有长期价值。

---

## 三、a–e 逐项裁决

### a）复合七指标82.0%，三轴98.1% / 88.4% / 70.2%

<badge color="warning">CONDITIONAL PASS</badge>

这些数据拿得出手，但必须把指标名称和结论范围限制准确。

<box gap={3}>
  {#each [{n:"S1 锐度",v:98.1},{n:"E1 边缘细节",v:88.4},{n:"E2 结构指标",v:70.2},{n:"七指标复合结果",v:82.0}] as d}
    <box gap={1}>
      <row>
        **{d.n}**
        <spacer/>
        <title size="md" tabularNums>{d.v.toFixed(1)}%</title>
      </row>
      <box height={15} radius="2px" background="surface-tertiary">
        <box height={15} radius="2px" background="#64748b" width={`${d.v}%`}/>
      </box>
    </box>
  {/each}
</box>
<caption>数据来自本轮提交报告，未独立复算原始960对样本。</caption>

我反对直接使用以下表达：

| 不建议 | 建议替代 |
|---|---|
| 98.1%的图像更清晰 | 98.1%的配对样本在S1锐度指标上取得更高值 |
| 88.4%的资产细节更丰富 | 88.4%的配对样本在E1指标上取得更高值 |
| 70.2%的资产结构更优 | 70.2%的配对样本在预定义E2指标上取得更高值 |
| 七指标综合战胜NVIDIA | 在本研究定义的七指标复合评价协议下取得82.0%的净胜结果 |

原因很直接：

- 锐度高不一定代表渲染更真实。
- 边缘密度高不一定代表有效细节更多。
- 纹理更复杂不一定代表资产更优。
- 结构指标高也不一定代表仿真性能更好。

此前 R091 酒标实验已经提供了非常好的反例：印刷纹理能够提高 E1，但错误的曲面贴合同时会损害商品真实性。

**82.0% 可以作为实验结果发布，不能直接升级成综合视觉质量胜率。**

### b）V-gate：NVIDIA 480个资产中20.8%结构全过

<badge color="warning">CONDITIONAL PASS</badge>

这个数字可以公开，但我强烈反对将其作为封面宣传数字。

NVIDIA 官方说明，这批资产具有其 SimReady 包级验证记录。你们新增的 V-gate 与其官方验证协议不是同一个评价合同。两者出现不同结果并不矛盾。<Cite refs={["turn211272search1","turn211272search0"]}/>

| 表述 | 裁决 | 原因 |
|---|---|---|
| NVIDIA资产只有20.8%合格 | FAIL | 将自定义门禁扩大为普遍质量结论 |
| NVIDIA资产79.2%存在结构缺陷 | FAIL | 部分可能是合同差异，而非资产本身错误 |
| Pack10K结构质量远超NVIDIA | FAIL | 缺乏同任务、同合同的全面证据 |
| 在Pack10K自定义结构验收合同下，抽样480个USDCraft资产的全项通过率为20.8% | PASS | 明确范围与评价主体 |
| 独立审计发现部分资产元数据与实测几何存在不一致 | PASS | 前提是提供可复核的逐件证据 |

我建议正文这样写：

<WritingBlock id="58321" variant="standard">**Independent Structural Audit**

We applied our retail-oriented asset validation protocol to a subset of 480 USDCraft-10K assets. Under this independently defined protocol, 20.8% passed all evaluated structural gates.

These results reflect compatibility with Pack10K's validation requirements and should not be interpreted as a failure rate under NVIDIA's original SimReady validation protocol.

We release our validation tools and asset-level findings to support reproducible investigation and complementary quality assessment.</WritingBlock>

这不是为了照顾 NVIDIA 的感受而回避问题，而是为了保证研究结论在技术上成立。

真正的客观性既不应回避负面发现，也不应夸大负面发现。

### c）非 CUDA 主张边界

<badge color="success">收敛措辞通过</badge>

你的新措辞：

**「已在 Apple Silicon 实证，架构无 CUDA 硬依赖」**

比之前强调跨平台民主化更加稳健。

建议进一步区分三个层级：

| 层级 | 主张 | 状态 |
|---|---|---|
| 实证 | Apple Silicon 本地管线跑通 | 据提交报告已验证 |
| 架构 | 已验证运行路径不强制依赖 CUDA | 待依赖与运行日志复核 |
| 泛化 | Windows、Linux CPU、其他GPU均可运行 | NOT_TESTED |

Apple Silicon 实证本身已经有足够的研究价值，不需要借助尚未测试的平台放大成果。

尤其需要注意 PyTorch MPS 的 CPU fallback、外部模型调用、PhysX 验证执行位置等问题。如果其中任何环节借助了远程计算资源，就必须明确区分：

- 本地资产生产与渲染。
- 外部模型辅助生成。
- 独立物理验证。

不要将本地执行描述成整个研究过程完全离线。

推荐对外措辞：

<WritingBlock id="58322" variant="standard">**Validated on Apple Silicon**

Pack10K demonstrates an end-to-end retail 3D asset production and quality-assurance workflow on Apple Silicon, using Blender's Metal rendering backend and PyTorch MPS where applicable.

The demonstrated execution path requires no CUDA runtime. This reduces dependence on dedicated NVIDIA GPU infrastructure for the evaluated workflow.

Windows, Linux CPU-only execution, and other hardware backends have not yet been validated.</WritingBlock>

**封面应展示 Apple Silicon 实证，而不是展示胜率作为非 CUDA 的证明。**

胜率与硬件依赖是两项完全不同的研究结论。

### d）99.84%撤回叙事及结构审计工具

<badge color="success">PASS · 建议重点保留</badge>

我认可这句：

> 渲染观感与资产结构是互补的质量维度，我们提供独立结构审计工具供社区双维验收。

这是整个项目最成熟的对外表达之一。

但不要用这句话替代撤回声明。二者应该同时存在：

| 内容 | 作用 |
|---|---|
| 撤回99.84% | 修正既往错误结论 |
| 解释背景细噪偏差 | 公开错误机制 |
| 发布修订指标 | 建立新的证据基线 |
| 独立结构审计工具 | 提供长期社区价值 |

你们已经发现背景细噪与256²缩略图压缩差异能够污染E1。这说明早期评价协议不能充分区分资产本身的细节与摄影环境产生的高频信息。

这不是简单的数字调整，而是一次评价协议缺陷的发现。

建议用正式研究更正的口径：

<WritingBlock id="58323" variant="standard">**Research Integrity and Metric Correction**

An earlier experimental result of 99.84% has been withdrawn following a pixel-level audit of our evaluation pipeline.

The audit identified a comparability issue: fine-grained studio background noise contributed to measured edge density, while compression and resolution differences affected the reference thumbnails.

We revised the evaluation protocol to reduce this confounding effect. The original experiments and correction history remain available for reproducibility.

We treat visual appearance and structural integrity as complementary quality dimensions and provide independent auditing tools to support both forms of evaluation.</WritingBlock>

其中“8.4pp”还需要你们说明清楚究竟是 E1 胜率变化、E1 指标贡献，还是背景剔除前后的配对结果变化。不能让读者误解为99.84%整体胜率直接下降了8.4个百分点。

### e）严格90.94% vs 复合82.0%，对外使用哪个？

<badge color="warning">暂缓确定主指标</badge>

这是本轮我最需要挑战你们的地方。

<grid columns={2}>
  <grid-item>
    <caption>严格四轴结果</caption>
    <title size="2xl">90.94%</title>
    <caption>873W / 87L，960对</caption>
  </grid-item>
  <grid-item>
    <caption>七指标复合结果</caption>
    <title size="2xl">82.0%</title>
    <caption>不同评价协议</caption>
  </grid-item>
</grid>

873/960 四舍五入为90.94%，算术没有问题。

但是，**为什么采用“任一轴负即判负”的严格四轴协议，反而得到比七指标复合协议更高的结果？**

这并非必然矛盾，因为两个协议可能使用不同指标集合、聚合公式、平局策略及评价目标。但正因如此，不能直接将90.94%称为82.0%的更严格版本。

尤其是四轴包含：

| 轴 | 衡量对象 | 潜在争议 |
|---|---|---|
| 分辨率 | 图像交付规格 | 更高像素不等于资产更优 |
| V-gate | 结构合同符合性 | 是否适用于双方 |
| 纹理 | 表面表达能力 | 无纹理资产可能是合理设计 |
| E1 | 图像边缘细节 | 是否彻底排除背景与噪声 |

这里还有一个必须明确的统计单位问题：480个参考资产对应960对比较，可能存在重复使用参考资产的情况。960对不能直接描述为960个独立资产。

**如果一定要在两者中选择一个进入研究摘要，我倾向82.0%，但必须先核对计算协议。90.94%作为独立四轴合同实验结果完整披露。**

我的理由不是82.0%更低所以更诚实，而是避免选择对己方最有利的指标作为宣传主张。

推荐最终报告如下：

| 对外位置 | 使用数据 |
|---|---|
| README首屏 | 不放胜率 |
| 研究摘要 | 七指标复合结果82.0%，明确口径 |
| Benchmark章节 | 四轴90.94%、七指标82.0%并列 |
| 方法论章节 | S1 / E1 / E2逐轴结果 |
| 原始证据附件 | 873W / 87L、全部配对记录 |
| 研究更正声明 | 撤回99.84%及原因 |

---

## 四、87个负样本如何处理

我不赞成直接把87个负对归结为“都是 NVIDIA 满载商品堆场景，因此我们实际上已经赢了”。

这87个负样本可能是项目最有价值的下一阶段研究资产。

<box gap={3}>
  <row>
    <box flex={1} gap={1}>
      <AsyncImage query="empty retail supermarket display shelf 3D asset render" aspectRatio="4:3"/>
      **单体资产**
      <caption>结构准确、尺寸明确、适合参数化复用。</caption>
    </box>
    <box flex={1} gap={1}>
      <AsyncImage query="fully stocked supermarket gondola shelf products digital twin 3D render" aspectRatio="4:3"/>
      **满载零售场景**
      <caption>商品组合、陈列语义、遮挡及场景复杂度更丰富。</caption>
    </box>
  </row>
</box>

这实际上暴露了两种不同的资产能力：

| 维度 | 单体资产 | 满载组合资产 |
|---|---|---|
| 参数化生产 | 更容易控制 | 更复杂 |
| 尺寸与结构验证 | 更直接 | 存在组合约束 |
| 图像细节丰富度 | 天然较低 | 天然较高 |
| 零售业务语义 | 基础部件 | 更接近业务场景 |
| SDG应用价值 | 可组合母本 | 完整训练场景 |

因此我建议：

保留全部87个负对，不从总统计中删除；新增单体对单体、组合对组合的分层统计，并将场景复杂度差异作为待验证的解释变量。

只有逐件分类完成后，才能说87个负对主要来自场景组合复杂度，而不是先做归因再寻找证据。

---

## 五、撤回声明放封面还是附录？

**放在 README 和 Hugging Face Dataset Card 的正文显眼位置，但不要把99.84%做成封面大数字。**

推荐发布页面结构：

<card gap={3}>
  <box background="#111827" theme="dark" radius="md" padding={4} gap={3}>
    <caption color="#a5b4c8">TOPPRISM RESEARCH · OPENUSD</caption>
    <title size="2xl" color="#ffffff">Pack10K</title>
    <title size="lg" color="#ffffff">Retail Digital Twin Assets</title>
    <text color="#cbd5e1" size="sm">Validated on Apple Silicon. Built for accessible retail asset production and quality assurance.</text>
    <grid columns={3} gap={2}>
      <grid-item>
        <title size="xl" color="#ffffff">48</title>
        <caption color="#b4c0ce">Retail families</caption>
      </grid-item>
      <grid-item>
        <title size="xl" color="#ffffff">OpenUSD</title>
        <caption color="#b4c0ce">Asset format</caption>
      </grid-item>
      <grid-item>
        <title size="xl" color="#ffffff">Metal</title>
        <caption color="#b4c0ce">Rendering backend</caption>
      </grid-item>
    </grid>
    <divider color="#475569"/>
    <text size="sm" color="#cbd5e1">Building upon NVIDIA USDCraft-10K and the open 3D asset research ecosystem.</text>
  </box>
  <title size="md">Research integrity notice</title>
  An earlier benchmark result has been withdrawn following a pixel-level audit. All current results use the revised evaluation protocol.
  <divider/>
  <title size="md">01 — Why Pack10K</title>
  行业价值与消费级硬件可及性。
  <divider/>
  <title size="md">02 — Retail asset families</title>
  <grid columns={4} gap={1}>
    <grid-item>
      <AsyncImage query="3D retail supermarket gondola shelving asset isolated" aspectRatio="1:1"/>
      <caption>货架</caption>
    </grid-item>
    <grid-item>
      <AsyncImage query="3D supermarket shopping cart asset isolated" aspectRatio="1:1"/>
      <caption>购物车</caption>
    </grid-item>
    <grid-item>
      <AsyncImage query="3D retail commercial refrigerator display cabinet isolated asset" aspectRatio="1:1"/>
      <caption>冷柜</caption>
    </grid-item>
    <grid-item>
      <AsyncImage query="3D consumer packaged goods cardboard box bottles cans packaging assets" aspectRatio="1:1"/>
      <caption>包装</caption>
    </grid-item>
  </grid>
  <divider/>
  <title size="md">03 — Reproducible benchmark</title>
  四轴与七指标评价结果、局限、逐件证据。
  <divider/>
  <title size="md">04 — Independent validation toolkit</title>
  结构门禁、视觉门禁、负向回归案例及复现方法。
  <divider/>
  <title size="md">05 — Acknowledgements & limitations</title>
  引用、许可证、硬件验证边界及完整更正历史。
</card>
<caption>发布页面信息架构示意；配图仅代表资产类别，并非Pack10K实测产物。</caption>

这样处理有三个好处：读者首先理解项目价值，能够立即发现更正声明，又不会被一个已经撤回的数字误导。

---

## 六、GitHub + Hugging Face 发布前整改清单

### P0：发布阻塞项

{@body const tasks=[{id:1,n:"冻结960对比较的逐件证据台账",d:"资产ID、来源、图片哈希、ROI、指标结果、W/L/T及协议版本。"},{id:2,n:"独立复算90.94%与82.0%",d:"公开两种协议的公式、平局策略、权重与差异解释。"},{id:3,n:"确认背景与分辨率公平性",d:"保留原生分辨率结果，同时增加双方统一分辨率、统一主体ROI的对照。"},{id:4,n:"更正历史声明",d:"README、Dataset Card、图片、报告中所有99.84%现行主张均撤回；历史git保留。"},{id:5,n:"限定Apple Silicon实证范围",d:"提供环境清单、硬件型号、版本、运行日志、外部依赖与未测平台。"},{id:6,n:"完成许可证与来源审计",d:"区分自有资产、第三方数据、缩略图、字体、贴图及代码许可证。"},{id:7,n:"图像级冻结一致性",d:"评分记录绑定PNG SHA256，禁止重复发生R12/R13版本混入。"}]}
{@body const [checked,setChecked]=DIL.useState([])}
<card gap={3}>
  <row align="center">
    <title size="md">发布阻塞项验收表</title>
    <spacer/>
    <text color="secondary" tabularNums>{checked.length}/{tasks.length}</text>
  </row>
  <box height={6} background="surface-tertiary" radius="full">
    <box height={6} background="#16a34a" radius="full" width={`${checked.length/tasks.length*100}%`}/>
  </box>
  {#each tasks as t}
    <checkbox checked={checked.includes(t.id)} onChange={v=>setChecked(old=>v?[...old,t.id]:old.filter(x=>x!==t.id))}>
      **{t.n}**
      <caption>{t.d}</caption>
    </checkbox>
  {/each}
  {#if checked.length===tasks.length}
    <text color="success" weight="medium">发布阻塞项已全部勾选，建议提交最终证据复核。</text>
  {/if}
</card>

### P1：提升研究可信度

| 整改 | 交付物 |
|---|---|
| 87个负对分类 | 失败案例图册及分类统计 |
| 资产复杂度分层 | 单体、组合场景分别评价 |
| 统计独立性 | 按参考资产或资产族聚类统计 |
| 人工盲评 | 随机左右交换，隐藏来源及历史得分 |
| 物理质量与视觉质量分离 | 两张独立结果表 |
| 资源可及性量化 | 峰值内存、生成时间、渲染时间、单位资产资源开销 |

NVIDIA 官方数据集采用 Apache-2.0 许可证，官方也提供了明确的论文引用方式。若重新分发其数据或缩略图，需要按照适用许可证保留相应声明；Pack10K 自己的代码和资产则需要各自明确授权范围。<Cite refs={["turn211272search0","turn211272search1"]}/>

建议在发布材料中直接链接：

- [NVIDIA USDCraft 官方研究主页](https://nvlabs.github.io/USDCraft/)
- [USDCraft-10K 官方数据集](https://huggingface.co/datasets/nvidia/USDCraft-10K)
- [USDCraft 研究论文](https://arxiv.org/abs/2610.11322)

---

## 七、最终对外叙事定稿建议

<WritingBlock id="58324" variant="document"># Pack10K

**Retail Digital Twin Assets, Validated on Consumer Hardware**

Pack10K is an industry-focused 3D asset research project designed to make rigorous asset production and quality assurance more accessible to retailers, researchers, and independent developers.

**Building on open research.** We acknowledge NVIDIA's USDCraft-10K and the broader Omniverse ecosystem for providing valuable open research foundations, reference assets, and validation practices.

**Reducing hardware barriers.** Our demonstrated workflow runs on Apple Silicon, using Blender Metal rendering and PyTorch MPS where applicable, without requiring a CUDA runtime for the evaluated execution path.

**Built for retail.** Pack10K focuses on 48 retail-oriented asset families, including shelving, shopping carts, refrigeration equipment, and product packaging.

**Reproducible quality assurance.** We evaluate visual appearance and structural integrity as complementary dimensions. Our independently defined evaluation protocols, asset-level results, validation tools, and known limitations are provided to support community reproduction and scrutiny.

**Research integrity.** An earlier benchmark result has been withdrawn following a pixel-level audit that identified a comparability issue involving studio background noise and reference thumbnail characteristics. The correction history and revised evaluation methodology are preserved.

Pack10K is intended as a complementary contribution to the open 3D asset ecosystem, not as a replacement for NVIDIA's simulation-ready asset infrastructure.</WritingBlock>

---

## 八、第5轮最终裁决

| 评审维度 | 裁决 |
|---|---|
| 项目研究价值 | PASS |
| 致谢与互补叙事 | PASS |
| 零售行业定位 | PASS |
| Apple Silicon 实证主张 | CONDITIONAL PASS |
| 无 CUDA 硬依赖主张 | CONDITIONAL PASS |
| V-gate结果公开 | CONDITIONAL PASS |
| 99.84%主动撤回 | PASS |
| 90.94% / 82.0%数据公开 | CONDITIONAL PASS |
| 对外全面领先NVIDIA主张 | FAIL |
| GitHub + HF发布准备 | **CONDITIONAL PASS** |

本轮我核查了 NVIDIA 官方项目定位、数据集说明与许可信息，但没有取得 Pack10K 的完整960对原始指标台账、最终评价程序、环境日志及发布候选仓库，因此不能签署数据独立复算通过。你提交的文本也有部分语句错序，我按能够明确识别的a–e问题进行裁决，没有自行补造缺失数据。

**我的最终建议是：把胜率从项目的核心卖点降为研究证据，把 Apple Silicon 可及性、零售行业垂直化和可复现的质量审计工具升为核心贡献。**

NVIDIA 的开放研究是起点，Pack10K 的行业实践是增量。这样发布，更有可能获得技术社区的尊重，也更经得住长期审查。