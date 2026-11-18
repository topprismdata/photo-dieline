# GPT 架构设计评审 (会话 6afda74e-a9fc-83ea-9e58-1144b40273fd, 2026-11-18)
# 抓取方式: backend-api Bearer + mapping 时间序

# 包装刀版智能重建开源项目：总体架构评审与设计方案 V1.0

<row align="center" gap={2} wrap="wrap">
  <badge color="success">建议立项</badge>
  <badge color="info">Hybrid Architecture</badge>
  <badge color="secondary">Open Source First</badge>
  <badge color="warning">Human-in-the-loop</badge>
</row>

## 一、先给架构裁决

我的建议不是简单选择 A 或 B，而是建立一个 **参数化几何为主、视觉重建为辅、3D 展开作为独立能力的混合架构**。

项目真正要解决的不是「从照片生成一个看起来像包装的 3D 模型」，而是：

**从不完整的视觉证据中，恢复具有真实尺寸、可制造结构、可验证折叠关系的包装几何，并生成印前工程文件。**

这是两个完全不同的技术问题。

- 3D 重建解决的是外观和空间几何。
- 参数化重建解决的是结构、尺寸和制造约束。
- 刀版生成解决的是二维制造几何。
- 印前 QA 解决的是交付是否可信。

不能把 TRELLIS.2 的 3D 重建成功，直接等同于刀版生成成功。

<box border radius="lg" padding={3} gap={3}>
  **推荐主线：B 主干 + A 辅助 + 独立制造几何内核**
  <box background="rgba(22,163,74,0.07)" radius="md" padding={3} gap={1}>
    <badge color="success">主干</badge>
    **B：参数化结构重建**

    照片识别 → 包装类型判断 → 尺寸标定 → 参数化拓扑 → 刀版生成。
  </box>
  <box background="rgba(59,130,246,0.07)" radius="md" padding={3} gap={1}>
    <badge color="info">辅助</badge>
    **A：视觉 3D 重建**

    TRELLIS.2 → 外观参考 → 几何约束提取 → 结构对齐 → 误差验证。
  </box>
  <box background="rgba(189,150,80,0.09)" radius="md" padding={3} gap={1}>
    <badge color="warning">独立内核</badge>
    **Manufacturing Geometry Kernel**

    统一管理面板、折线、切线、粘口、出血、材料厚度、尺寸和拓扑关系，输出 SVG/PDF 与折叠验证模型。
  </box>
  <box background="rgba(148,163,184,0.12)" radius="md" padding={3} gap={1}>
    **质量门：证据驱动**

    照片对齐、尺寸闭合、拓扑合法、刀版比例、文件完整性、人工签核。
  </box>
</box>

### 一个重要的战略取舍

我不建议把「TRELLIS.2 → DielineForge」作为 MVP 的主路径。

原因是这条路径实际上要求一个单图 3D 模型同时满足：

1. 外观正确。
2. 结构正确。
3. 尺寸正确。
4. 面板边界正确。
5. 折叠拓扑正确。
6. 展开后能够制造。

而单图重建无法天然保证这些条件。

反过来，参数化方案只需要识别包装结构，并恢复少量关键尺寸，就可以直接构造制造几何。

因此，MVP 应当先证明：

**一张手机照片 + 少量尺寸输入 → 一份正确的 1:1 参数化刀版 → 能折叠回原包装。**

这才是整个项目最重要的垂直切片。

---

## 二、总体架构

### 2.1 系统架构图

```text
                 INPUT
        ┌──────────────────────┐
        │ 手机照片 / 多角度照片 │
        │ 包装文字 / 规格 / 尺寸 │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ 01. Evidence Layer    │
        │ OCR / VLM / 图像分析  │
        │ 尺寸证据 / 置信度     │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ 02. Package Classifier│
        │ FEFCO / Gable / Rigid │
        │ 结构分类 / 模板匹配    │
        └──────────┬───────────┘
                   │
           ┌───────┴────────┐
           ▼                ▼
  ┌────────────────┐  ┌────────────────┐
  │ 03. Parametric  │  │ 04. Vision 3D  │
  │ Reconstruction │  │ Reconstruction │
  │                │  │                │
  │ 参数化拓扑      │  │ TRELLIS.2      │
  │ 尺寸约束        │  │ 几何证据       │
  │ 结构规则        │  │ 外观参考       │
  └───────┬────────┘  └───────┬────────┘
          │                  │
          └────────┬─────────┘
                   ▼
        ┌──────────────────────┐
        │ 05. Geometry Kernel  │
        │                      │
        │ Panels / Edges       │
        │ Creases / Tabs       │
        │ Bleed / Cut          │
        │ Constraints          │
        └──────────┬───────────┘
                   │
          ┌────────┴─────────┐
          ▼                  ▼
 ┌──────────────────┐ ┌──────────────────┐
 │ 06. 2D Unfolding  │ │ 07. 3D Folding   │
 │ DielineForge     │ │ Fold Simulation  │
 │ SVG / PDF        │ │ Blender          │
 └────────┬─────────┘ └────────┬─────────┘
          │                    │
          └─────────┬──────────┘
                    ▼
        ┌──────────────────────┐
        │ 08. QA & Validation  │
        │                      │
        │ Scale / Topology     │
        │ Photo Alignment      │
        │ Manufacturing Rules  │
        │ PDF / SVG Inspection │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ 09. Deliverables     │
        │ Layered SVG          │
        │ Print-ready PDF      │
        │ Folded 3D Model      │
        │ QA Report            │
        └──────────────────────┘
```

### 2.2 四个核心设计原则

| 原则 | 架构决定 |
|---|---|
| 几何与外观分离 | 视觉模型不能直接决定最终刀版 |
| 尺寸证据优先 | OCR 和 VLM 推断不能替代真实尺寸 |
| 制造几何唯一可信 | SVG、PDF、3D 都由同一个 Geometry IR 派生 |
| 失败必须可解释 | 不确定就拒绝自动交付，不用视觉相似度掩盖结构错误 |

这里我特别强调 Geometry IR。

不要让参数化模板直接输出 SVG，也不要让 Blender 直接输出最终刀版。

所有路线必须汇入同一个中间表示（Intermediate Representation）。

这会决定项目未来能否从三个模板扩展到三十种包装结构。

## 三、Geometry IR：整个项目最重要的技术资产

我建议把 Geometry IR 设计成项目的核心公共协议，而不只是一个内部数据结构。

它是参数化重建、TRELLIS 几何提取、DielineForge 适配器、SVG/PDF 导出器、3D 折叠器之间的共同语言。

### 3.1 IR 的对象模型

<box border radius="lg" padding={3} gap={2}>
  <box background="rgba(59,130,246,0.08)" radius="md" padding={2}>
    **PackageSpec**

    包装身份、单位、材料、尺寸、类型、来源证据
  </box>
  <box align="center">
    <icon name="arrow-down" color="secondary" size="lg"/>
  </box>
  <grid columns={2} gap={2}>
    <grid-item>
      <box background="rgba(22,163,74,0.07)" radius="md" padding={2} height="100%">
        **Panels**

        面板、边界、平面、相邻关系
      </box>
    </grid-item>
    <grid-item>
      <box background="rgba(22,163,74,0.07)" radius="md" padding={2} height="100%">
        **Edges**

        边、连接、边界类型、共享关系
      </box>
    </grid-item>
    <grid-item>
      <box background="rgba(189,150,80,0.09)" radius="md" padding={2} height="100%">
        **Folds**

        山谷折、山折、折角、折叠顺序
      </box>
    </grid-item>
    <grid-item>
      <box background="rgba(189,150,80,0.09)" radius="md" padding={2} height="100%">
        **Features**

        粘口、开窗、提手、切口、出血
      </box>
    </grid-item>
  </grid>
  <box align="center">
    <icon name="arrow-down" color="secondary" size="lg"/>
  </box>
  <box background="rgba(59,130,246,0.08)" radius="md" padding={2}>
    **Manufacturing Constraints**

    材料厚度、压痕补偿、粘接余量、印刷安全区、工艺约束
  </box>
  <box align="center">
    <icon name="arrow-down" color="secondary" size="lg"/>
  </box>
  <box border={{size:1,color:"#76B900"}} radius="md" padding={2}>
    **Derived Geometry**

    2D 展开坐标 + 3D 折叠坐标 + 制造路径
  </box>
</box>

### 3.2 必须明确的对象

| 对象 | 关键字段 | 作用 |
|---|---|---|
| Package | package_id, type, units | 包装身份 |
| Panel | id, boundary, role | 面板 |
| Edge | id, panel_a, panel_b | 面板连接 |
| Fold | edge_id, fold_type, angle | 折叠关系 |
| Cut | geometry, cut_type | 裁切线 |
| GlueTab | geometry, target_panel | 粘接结构 |
| Bleed | offset, region | 出血 |
| Material | thickness, grain, score_rule | 材料与加工 |
| Evidence | source, value, uncertainty | 证据溯源 |
| Constraint | expression, tolerance | 几何约束 |

其中有三个特别重要的设计决定：

**第一，折线不是普通的线段。**

它需要有语义：

- MOUNTAIN：山折
- VALLEY：谷折
- SCORE：压痕
- CUT：裁切
- PERFORATION：虚线/易撕线

CUT 和 SCORE 必须是不同的制造对象，而不是仅仅使用不同颜色绘制的 SVG 路径。

**第二，所有坐标统一使用 mm。**

内部采用浮点毫米，导出时再转换成 SVG 的物理尺寸和 PDF 页面坐标。禁止在模块间传递未经声明的像素坐标。

**第三，证据和几何必须分开。**

例如：

```text
Panel.width = 68.3 mm
Evidence:
  source = USER_MEASUREMENT
  confidence = MEASURED
  uncertainty = ±0.2 mm
```

不要把 VLM 推断的 68.3mm 和卡尺实测的 68.3mm 当成同一种数据。

另外，我建议给每一个参数设置状态：

- MEASURED：实测
- DERIVED：由约束计算
- INFERRED：模型推断
- DEFAULTED：采用默认值
- UNRESOLVED：尚未解决

这将直接服务于后面的 QA 门禁。

---

## 四、五个关键技术问题的裁决

### 4.1 A/B/混合路线：明确 B 为主，A 为辅

我的判断：

| 维度 | A：3D 展开 | B：参数化重建 |
|---|---|---|
| 几何完整性 | 需要重建和规整 | 由结构规则保证 |
| 尺寸精度 | 单图难保证 | 可直接使用实测 |
| 面板语义 | 需要推断 | 模板天然具有 |
| 标准盒型 | 有冗余 | 非常适合 |
| 非标结构 | 有一定潜力 | 需要新增模板 |
| 屋顶包 | 容易被曲面误导 | 有现成拓扑基础 |
| 工程可控性 | 较低 | 较高 |
| MVP 可行性 | 低 | 高 |

建议未来的路由逻辑：

```text
              Photo
                |
                v
        Package Recognition
                |
        +-------+-------+
        |               |
     Known Type       Unknown Type
        |               |
        v               v
   Parametric       Human Review
   Reconstruction       |
        |               v
        |          3D Geometry
        |          Extraction
        |               |
        +-------+-------+
                |
                v
          Geometry IR
                |
                v
         Manufacturing QA
```

但我不建议把 A 定义为单纯的「非标兜底」。

原因是 A 还有一个重要价值：它可以作为 B 的独立视觉证据。

例如：

- B 构造一个 68.3 × 68.3 × 105.2mm 的屋顶包。
- A 从照片生成一个外观模型。
- 将两者对齐，检查顶部坡面、面板轮廓、整体比例是否吻合。
- 发现偏差时，返回尺寸或结构确认。

A 不一定生成最终刀版，但可以帮助识别 B 的错误。

**架构原则：A 提供视觉证据，B 负责制造几何。**

### 4.2 绝对尺寸标定：不能让单张照片承担不可能完成的任务

这里我建议区分三个问题：

1. 图像像素到真实长度的换算。
2. 包装各个面之间的几何关系。
3. 最终印前尺寸是否满足要求。

这三件事不能混为一谈。

#### 各种标定方式的评价

| 方法 | 作用 | 可靠性 | 定位 |
|---|---|---|---|
| 硬币参照 | 局部尺度参考 | 低至中 | 辅助 |
| A4 纸角 | 已知平面尺度 | 中 | 辅助 |
| 用户输入长宽高 | 直接尺寸约束 | 高（取决于测量） | 主方法 |
| OCR 规格字样 | 产品身份识别 | 低 | 仅辅助 |
| 多角度照片 | 结构和透视恢复 | 中 | 强烈推荐 |
| 卡尺测量 | 局部关键尺寸 | 高 | 精度验证 |

特别提醒：458mL 只能说明产品容量，不能推出屋顶包的真实尺寸。不同包装结构完全可能有相同容量。

#### 我建议的最小摩擦标定协议

<box border radius="lg" padding={3} gap={3}>
  **第一步：拍摄包装**

  <AsyncImage query="rectangular paperboard gable top carton product photographed front three quarter view white background" aspectRatio="16:9" width="100%"/>
  - 正面三分之四视角。
  - 尽可能拍摄顶部和底部。
  - 避免手指遮挡折线和边界。
  - 上传规格文字清晰的照片。
  <divider color="subtle"/>
  **第二步：输入三个外形尺寸**

  <grid columns={3} gap={2}>
    <grid-item>
      <text color="secondary" size="xs">长度 L</text>
      <title size="xl" color="default" tabularNums>68.3</title>
      <text size="xs" color="secondary">mm</text>
    </grid-item>
    <grid-item>
      <text color="secondary" size="xs">宽度 W</text>
      <title size="xl" color="default" tabularNums>68.3</title>
      <text size="xs" color="secondary">mm</text>
    </grid-item>
    <grid-item>
      <text color="secondary" size="xs">高度 H</text>
      <title size="xl" color="default" tabularNums>105.2</title>
      <text size="xs" color="secondary">mm</text>
    </grid-item>
  </grid>
  <text color="secondary" size="xs">以上仅为架构方案中的尺寸示例，不代表从照片测得。</text>
  <divider color="subtle"/>
  **第三步：自动识别结构，人工确认**

  - 识别屋顶包 / 折叠纸盒 / 瓦楞箱。
  - 识别顶部结构、封口鳍片、粘接边。
  - 提示尚未确认的结构尺寸。
  <divider color="subtle"/>
  **第四步：输出尺寸可信度报告**

  - 已测量尺寸。
  - 模型推断尺寸。
  - 待确认尺寸。
  - 预计误差及是否允许进入印前流程。
</box>

#### 一个必须补充的细节

三个尺寸并不一定足以生成刀版。

例如屋顶包还需要：

- 顶部坡面高度。
- 屋脊封口鳍片尺寸。
- 封口方式。
- 底部封合方式。
- 面板之间的连接关系。
- 纸板厚度和折痕补偿。

所以建议使用「最小必需参数」机制：

每种包装类型自己定义参数集，只有影响结构或制造的参数才要求用户补充。

**精度建议：**

- 初始尺寸重建目标：关键尺寸误差 ≤ 0.5mm。
- MVP 自动验证目标：与已知 CAD/实测基准相比，关键几何误差 ≤ 0.5mm。
- P1 优化目标：关键尺寸误差 ≤ 0.25mm。
- 最终交付：必须符合具体印厂提供的工艺公差。

注意：这些是项目建议的验收目标，不是宣称所有印刷工艺都采用 ±0.5mm 的统一公差。CGATS 包装生产清单明确要求刀版、出血、印刷及压线公差根据具体生产参数确定；3M 的包装刀版规范也区分了不同材料的出血要求。<Cite refs={["turn546067search60","turn546067search63"]}/>

### 4.3 TRELLIS.2 密面实体如何转换为可展开单面壳？

我不建议直接采用：

```text
Dense Mesh
    ↓
RANSAC
    ↓
Planar Mesh
    ↓
DielineForge
```

这条链路看起来简单，但容易出现严重的拓扑错误。

例如：

- 两个相邻面被错误合并。
- 屋顶斜面与侧面边界消失。
- 一个真实折线被拟合成连续曲面。
- 纸盒厚度被识别成两个独立面板。
- 非流形修复改变了实际边界。

尤其是屋顶包，不能只根据法线夹角来判断面板边界。

#### 我建议的转换方式：Structure-constrained Reconstruction

<box border radius="lg" padding={3} gap={2}>
  <box background="rgba(59,130,246,0.07)" radius="md" padding={2}>
    **Step 1 — Mesh Analysis**

    法线、曲率、连通域、对称性、局部厚度分析
  </box>
  <box align="center"><icon name="arrow-down" color="secondary"/></box>
  <box background="rgba(59,130,246,0.07)" radius="md" padding={2}>
    **Step 2 — Surface Segmentation**

    RANSAC 平面拟合 + 法线聚类 + 几何边界检测
  </box>
  <box align="center"><icon name="arrow-down" color="secondary"/></box>
  <box background="rgba(22,163,74,0.07)" radius="md" padding={2}>
    **Step 3 — Semantic Topology Matching**

    与包装类型先验匹配，识别面板、折线、粘口
  </box>
  <box align="center"><icon name="arrow-down" color="secondary"/></box>
  <box background="rgba(22,163,74,0.07)" radius="md" padding={2}>
    **Step 4 — Parametric Surface Reconstruction**

    用平面和参数曲面重建面板，恢复共享边界和拓扑
  </box>
  <box align="center"><icon name="arrow-down" color="secondary"/></box>
  <box background="rgba(189,150,80,0.09)" radius="md" padding={2}>
    **Step 5 — Developability Check**

    检查平面可展开性、边长一致性、折叠闭合性
  </box>
  <box align="center"><icon name="arrow-down" color="secondary"/></box>
  <box border radius="md" padding={2}>
    **Step 6 — Geometry IR**
    
    合格结构进入制造几何内核；无法解释的结构拒绝自动生成
  </box>
</box>

我的关键建议是：RANSAC 负责提出候选面，不负责最终决定包装拓扑。

最终的拓扑应当由几何证据与结构先验共同决定。

#### 精度和技术边界

这里需要区分两种精度：

| 指标 | 定义 | 建议 |
|---|---|---|
| 外观重建误差 | 网格与照片投影的偏差 | 视觉 QA |
| 面板几何误差 | 面板轮廓和边长误差 | ≤0.5mm |
| 折线位置误差 | 实际折线与重建折线偏差 | ≤0.5mm |
| 展开闭合误差 | 2D 展开重新折叠后的几何残差 | ≤0.2mm（已知基准测试） |

以上数值是分阶段工程目标，并不代表 TRELLIS.2 单图输出可以达到这些精度。

特别是最后一项，需要通过已知几何的基准模型测试，而不是仅凭渲染结果判定。

**最重要的技术取舍：不要把 TRELLIS.2 的密面网格作为印刷精度的来源。**

它适合做外观参考和几何证据，不应成为制造尺寸的权威数据源。

### 4.4 GPL-3.0：如何保持主体 MIT？

<badge color="success">建议采用进程隔离</badge>

这里的法律判断需要谨慎：子进程调用并不自动保证法律意义上的独立作品。

GNU FAQ 明确指出，进程、管道、Socket、命令行参数通常是区分独立程序的因素，但还要考察通信语义；如果交换高度耦合的复杂内部数据结构，仍可能被视为一个组合程序。<Cite refs={["turn546067search0","turn546067search3"]}/>

我的建议：

**不要将 DielineForge 作为 Python import 依赖，也不要复制其代码。**

建议采用以下结构：

```text
topprism-dieline/
│
├── LICENSE                 MIT
├── THIRD_PARTY_NOTICES.md
├── pyproject.toml
│
├── src/
│   └── dieline/
│       ├── core/
│       ├── geometry/
│       ├── parametric/
│       ├── vision/
│       ├── calibration/
│       ├── export/
│       └── qa/
│
├── adapters/
│   └── dielineforge/
│       ├── README.md
│       ├── adapter.py
│       └── protocol.py
│
├── external/
│   └── README.md
│
└── tests/
```

具体纪律：

1. DielineForge 作为独立安装、独立运行的外部程序。
2. 通过 CLI 参数和标准文件格式交换数据。
3. 输入输出使用 SVG、OBJ、JSON 等公开格式。
4. 不导入其 Python 模块。
5. 不将其源代码复制进 MIT 主仓。
6. 明确标记外部工具的 GPL-3.0 许可证及版本。
7. CI 提供有/无 DielineForge 两种测试路径。

另外，Geometry IR 不要直接使用 DielineForge 的内部数据结构作为公共协议。

#### 一个容易忽略的问题

GPL 不会因为使用其程序就自动覆盖所有生成的 SVG/PDF。GNU 对程序输出的版权范围有专门解释，通常程序生成的输出不因使用 GPL 程序就自动变成 GPL。<Cite refs={["turn546067search3"]}/>

但是，最终的组合分发边界需要看实际代码、调用方式和发行形态，不能只凭「CLI」两个字作法律结论。正式公开前应让开源许可证律师审阅一次。

### 4.5 QA 门设计：区分生成成功和印前可交付

这是我认为最容易被低估的部分。

系统能够输出 SVG，不等于输出了印厂能使用的刀版。

建议建立三种状态：

<box border radius="lg" padding={3} gap={2}>
  <row align="center" justify="between">
    **DRAFT**
    <badge color="secondary">可查看</badge>
  </row>
  文件已生成，但结构、尺寸或制造规则尚未全部验证。
  <divider color="subtle"/>
  <row align="center" justify="between">
    **VALIDATED**
    <badge color="success">技术验证通过</badge>
  </row>
  几何、尺寸、折叠、文件完整性全部通过规定测试。
  <divider color="subtle"/>
  <row align="center" justify="between">
    **PRINT-READY**
    <badge color="success">印厂签核</badge>
  </row>
  已匹配具体材料、印刷工艺、刀模及印厂规范，并经人工确认。
</box>

尤其要防止系统把 VALIDATED 自动升级为 PRINT-READY。

---

## 五、印前 QA：哪些是 MVP 硬门？

我建议按 P0、P1、P2 分级。

| QA 项目 | MVP | P1 | 判定方式 |
|---|---|---|---|
| 1:1 物理尺寸 | P0 | — | SVG/PDF 页面物理尺寸 |
| 50mm 校验条 | P0 | — | 导出尺寸检测 |
| CUT / SCORE 分层 | P0 | — | 图层与路径语义检查 |
| 闭合轮廓 | P0 | — | 几何算法 |
| 非流形拒绝 | P0 | — | 拓扑检查 |
| 面板边界闭合 | P0 | — | 拓扑检查 |
| 折叠回包 | P0 | — | 3D 几何检查 |
| 尺寸闭合 | P0 | — | 约束检查 |
| 粘口与出血 | P0 | — | 参数和几何检查 |
| 面板数量对账 | P0 | — | 类型先验检查 |
| 原照片对齐 | P1 | — | 图像匹配 |
| 纸板利用率 | P1 | — | 排版计算 |
| 材料纹理方向 | P1 | — | 制造参数 |
| 纸厚补偿 | P1 | — | 材料参数 |
| 印刷套准风险 | P1 | — | 印厂参数 |
| 自动识别非标结构 | P2 | — | 视觉与结构推理 |

其中有几个判据必须再明确一下。

**第一，50mm 校验条必须是真正的 50mm。**

不能只在 SVG 中写一个宽度为 50 的路径，而应检查其最终 PDF 页面物理尺寸。建议同时检查 PDF 页面 MediaBox、单位转换和 SVG `width/height`。

**第二，刀版周长不等于纸板利用率。**

刀版周长可以作为制造复杂度的参考，但纸板利用率还需要考虑排版方向、板材尺寸、间距、套准、旋转和材料方向。

不要把这两个指标混为一谈。

**第三，折叠闭合不能只看渲染图片。**

需要有数值化的几何判据：

- 相邻面共享边一致。
- 折叠后关键顶点距离满足阈值。
- 不存在不允许的面板穿插。
- 粘口接合区域具有有效重叠。

**第四，原照片对齐不能直接作为 MVP 唯一硬门。**

因为手机照片的透视、光照、遮挡、镜头畸变都可能影响图像相似度。

MVP 应当优先在已知尺寸、已知结构的基准包装上做数值对账，照片对齐作为辅助证据。

## 六、模块划分与仓库目录设计

我建议采用 Python 主体，几何内核与外部程序适配器保持边界清晰。

不要一开始引入微服务、消息队列、数据库集群或复杂前端。这个项目最初是一个本地可运行的几何工程工具链。

### 6.1 建议目录

```text
topprism-dieline/
│
├── README.md
├── LICENSE
├── NOTICE
├── THIRD_PARTY_NOTICES.md
├── pyproject.toml
├── Makefile
│
├── docs/
│   ├── architecture.md
│   ├── geometry-ir.md
│   ├── calibration-protocol.md
│   ├── manufacturing-rules.md
│   ├── qa-specification.md
│   ├── licensing.md
│   └── adr/
│
├── schemas/
│   ├── package-spec.schema.json
│   ├── geometry-ir.schema.json
│   └── qa-report.schema.json
│
├── src/
│   └── dieline/
│       │
│       ├── core/
│       │   ├── models.py
│       │   ├── units.py
│       │   ├── geometry_ir.py
│       │   └── validation.py
│       │
│       ├── evidence/
│       │   ├── image.py
│       │   ├── ocr.py
│       │   ├── measurements.py
│       │   └── provenance.py
│       │
│       ├── calibration/
│       │   ├── reference_object.py
│       │   ├── perspective.py
│       │   ├── camera.py
│       │   └── uncertainty.py
│       │
│       ├── recognition/
│       │   ├── classifier.py
│       │   ├── features.py
│       │   └── review.py
│       │
│       ├── parametric/
│       │   ├── registry.py
│       │   ├── rectangular.py
│       │   ├── fefco/
│       │   ├── gable_top/
│       │   └── rigid_box/
│       │
│       ├── vision3d/
│       │   ├── trellis_adapter.py
│       │   ├── mesh_analysis.py
│       │   ├── segmentation.py
│       │   ├── planar_reconstruction.py
│       │   └── topology_matching.py
│       │
│       ├── geometry/
│       │   ├── planar.py
│       │   ├── topology.py
│       │   ├── offset.py
│       │   ├── intersections.py
│       │   └── developability.py
│       │
│       ├── folding/
│       │   ├── fold_graph.py
│       │   ├── kinematics.py
│       │   └── collision.py
│       │
│       ├── manufacturing/
│       │   ├── cut.py
│       │   ├── crease.py
│       │   ├── glue.py
│       │   ├── bleed.py
│       │   └── material.py
│       │
│       ├── export/
│       │   ├── svg.py
│       │   ├── pdf.py
│       │   └── report.py
│       │
│       ├── qa/
│       │   ├── scale.py
│       │   ├── topology.py
│       │   ├── folding.py
│       │   ├── print.py
│       │   └── pipeline.py
│       │
│       └── cli/
│           └── main.py
│
├── adapters/
│   └── dielineforge/
│       ├── README.md
│       ├── runner.py
│       └── converter.py
│
├── templates/
│   ├── gable_top/
│   └── fefco/
│
├── examples/
│   ├── gable_top/
│   └── fefco_0201/
│
└── tests/
    ├── unit/
    ├── integration/
    ├── golden/
    ├── geometry/
    ├── manufacturing/
    └── fixtures/
```

这里有一个特别重要的取舍：

**TRELLIS.2 不应该被直接安装成主项目的强制依赖。**

它有自己的模型权重、运行环境、内存需求和硬件限制。

建议采用可选依赖和独立适配器：

```text
Core Installation
    ├── Geometry IR
    ├── Parametric Templates
    ├── SVG / PDF
    └── QA

Optional Vision Installation
    ├── TRELLIS.2 Adapter
    ├── Mesh Processing
    └── Vision Models
```

这样没有 GPU、没有 MPS、没有模型权重的用户，仍然可以完整使用参数化刀版能力。

### 6.2 各模块接口

我建议统一采用以下几个核心接口。

| 模块 | 输入 | 输出 |
|---|---|---|
| Evidence | Images, Text | EvidenceBundle |
| Calibration | EvidenceBundle, Measurements | CalibratedDimensions |
| Recognition | EvidenceBundle | PackageHypothesis |
| Parametric | PackageSpec | GeometryIR |
| Vision3D | Image | MeshEvidence |
| Geometry | GeometryIR | ValidatedGeometry |
| Folding | GeometryIR | FoldedModel |
| Manufacturing | GeometryIR | ManufacturingIR |
| Export | ManufacturingIR | SVG / PDF |
| QA | 全部产物 | QAReport |

例如主入口可以是：

```python
result = build_dieline(
    images=["front.jpg", "top.jpg"],
    package_type="gable_top",
    measurements={
        "length_mm": 68.3,
        "width_mm": 68.3,
        "height_mm": 105.2,
    },
    material={
        "thickness_mm": 0.45,
    },
)

assert result.qa.status == "VALIDATED"
```

这是接口设计示意，不是已经实现的 API。

#### 我建议额外增加一个重要接口：Template Contract

每种包装模板必须声明：

```text
Template:
  id
  version
  package_family

Required Parameters:
  ...

Optional Parameters:
  ...

Generated Panels:
  ...

Generated Folds:
  ...

Generated Cuts:
  ...

Constraints:
  ...

Validation Rules:
  ...
```

这意味着未来增加一种新包装时，不需要改动核心几何内核。

只需要实现一个新的模板。

这才是可持续扩展的架构。

---

## 七、M1 / M2 / M3 里程碑

我建议严格控制范围。

特别是 M1：两周内，一个人必须能够完成真正端到端的垂直切片。

不要在 M1 做视觉模型微调，不要做通用包装识别，不要做完整 TRELLIS 集成。

### M1：两周，证明核心管线成立

<badge color="success">P0 · 必须完成</badge>

**目标：一个已知结构包装，从照片和尺寸输入，到 1:1 刀版，再到折叠 3D 验证。**

我建议选择你们已有的 458mL 屋顶包参数化结构作为第一个案例。

这比重新从零做一个 FEFCO 0201 更能复用现有资产，也更容易验证你们真正关心的屋顶包拓扑。

<AsyncImageGroup query={["gable top carton unfolded packaging dieline technical drawing crease cut lines","gable top milk carton 3d unfolded folding stages technical illustration"]} aspectRatio="5:4" layout="carousel"/>

**M1 工作拆分**

| 时间 | 工作 | 交付 |
|---|---|---|
| Day 1–2 | Geometry IR 定义 | JSON Schema |
| Day 3–4 | 屋顶包模板适配 | Gable-top Template |
| Day 5–6 | 参数化刀版生成 | SVG |
| Day 7–8 | PDF 导出及物理尺寸验证 | PDF |
| Day 9–10 | 3D 折叠模型 | Blender / Mesh |
| Day 11–12 | QA 自动测试 | QA Report |
| Day 13–14 | 黄金样本测试、修复、文档 | Release Candidate |

**M1 必须交付的文件：**

```text
artifacts/
├── input/
│   └── reference_photo.jpg
│
├── package-spec.json
├── geometry-ir.json
│
├── dieline.svg
├── dieline.pdf
│
├── folded.glb
├── folded.png
│
└── qa-report.json
```

这里的 GLB 是建议增加的交付格式，方便后续在浏览器或其他 3D 工具中检查折叠结果。

**M1 验收标准**

1. 使用一张真实照片作为视觉参照。
2. 用户提供已知真实尺寸。
3. 自动生成参数化 Geometry IR。
4. 导出正确物理尺寸的分层 SVG/PDF。
5. 50mm 校验条通过。
6. 折叠模型能够闭合。
7. 面板、折线、粘口数量与模板定义一致。
8. 已知基准尺寸误差不超过 0.5mm。
9. 所有 P0 QA 通过。
10. 不依赖 TRELLIS.2 也能完成整个管线。

注意：M1 的照片识别可以先使用人工确认的包装类型，不能把人工输入包装成自动识别能力。

### M2：建立可扩展的包装结构库

<badge color="info">P1 · 产品能力扩展</badge>

目标：从一个成功案例扩展为一套包装类型体系。

建议开发顺序：

<box gap={3}>
  <row align="center" gap={3}>
    <AsyncImage query="FEFCO 0201 regular slotted corrugated carton box technical drawing" aspectRatio="1:1" maxWidth="104px"/>
    <box flex="1" gap={1}>
      **FEFCO 0201**

      <text color="secondary" size="xs">标准瓦楞箱，验证规则化面板、摇盖和粘接关系。</text>
      <badge color="success">优先</badge>
    </box>
  </row>
  <divider color="subtle"/>
  <row align="center" gap={3}>
    <AsyncImage query="gable top carton packaging unfolded dieline template" aspectRatio="1:1" maxWidth="104px"/>
    <box flex="1" gap={1}>
      **Gable-top**

      <text color="secondary" size="xs">继续完善坡面、封口鳍片、底部结构和材料补偿。</text>
      <badge color="success">已有基础</badge>
    </box>
  </row>
  <divider color="subtle"/>
  <row align="center" gap={3}>
    <AsyncImage query="rigid box two piece lid and base packaging dieline" aspectRatio="1:1" maxWidth="104px"/>
    <box flex="1" gap={1}>
      **Rigid Box**

      <text color="secondary" size="xs">验证天地盖及多片材料组合。</text>
      <badge color="secondary">后续</badge>
    </box>
  </row>
</box>

M2 还要完成：

- 多角度照片输入。
- OCR 规格识别。
- 自动包装类型推荐。
- 关键尺寸问答。
- 参数不确定性传播。
- DielineForge CLI 适配器。
- 图像对齐 QA。
- 真实纸板厚度及折痕补偿。

这里我建议参考 FEFCO 的包装分类体系，但不要把它简单理解为一个可以随意复制和重新发布的免费模板库。FEFCO 官方第 12 版包含 0200、0300、0400、0600 等系列，官方资料标注了版权保留。我们可以实现兼容的结构规则，但应单独核实标准图纸、插图和具体内容的再分发许可。<Cite refs={["turn546067search1","turn546067search62"]}/>

### M3：视觉驱动的半自动重建

<badge color="discovery">P2 · 智能化扩展</badge>

目标：从已知包装结构扩展到未知结构。

重点：

1. TRELLIS.2 接入完整管线。
2. Mesh Analysis。
3. 面板分割。
4. RANSAC 平面候选。
5. 拓扑匹配。
6. 参数化曲面重建。
7. 自动生成候选 Geometry IR。
8. 与照片及尺寸证据交叉验证。
9. 人工修订非标结构。
10. 不确定性报告。

这一阶段不要承诺「任意包装照片自动生成可印刷刀版」。

建议将产品能力定义为：

- 已支持结构：自动生成，满足门禁后可验证。
- 相似结构：辅助重建，人工确认。
- 非标结构：提供候选几何和交互式修订。
- 无法可靠重建：拒绝自动交付。

---

## 八、风险排序 Top 5

我按对项目北极星的影响排序，而不是按开发难度排序。

| 排名 | 风险 | 严重度 | 发生概率 | 缓解策略 |
|---|---|---|---|---|
| 1 | 单照片尺寸不可观测 | 极高 | 高 | 实测尺寸优先、证据等级 |
| 2 | 3D 外观正确但拓扑错误 | 极高 | 高 | 参数化主干、拓扑约束 |
| 3 | 刀版数学正确但无法制造 | 极高 | 中高 | 材料、压痕、粘口、印厂规则 |
| 4 | 模板覆盖率不足 | 高 | 高 | 插件式 Template Contract |
| 5 | GPL/第三方资产许可污染 | 高 | 中 | CLI 隔离、SBOM、许可证审计 |

### 风险 1：单照片尺寸不可观测

这是整个项目的物理限制，不是模型能力不足。

如果没有真实尺度参照，照片只能提供比例和视觉结构，无法唯一恢复真实尺寸。

**解决办法：**

不要追求完全无输入。

把人工补充三个尺寸，视为产品正常交互，而不是系统失败。

### 风险 2：3D 重建与制造结构不一致

这是 A 路线最大的风险。

**解决办法：**

3D 只作为几何证据，Geometry IR 才是最终权威。

### 风险 3：刀版正确不等于可制造

这是容易导致客户实际损失的风险。

例如纸板厚度、折弯补偿、压线宽度、粘口尺寸和出血都可能改变最终结构。

3M 的包装规范就明确区分了刀版轮廓、出血区域、禁印区域等概念，并针对纸板与瓦楞材料给出不同出血示例。<Cite refs={["turn546067search63"]}/>

**解决办法：**

建立 Manufacturing Profile，而不是在模板中硬编码所有工艺参数。

### 风险 4：模板库覆盖不足

**解决办法：**

将模板视为可扩展的独立模块，而不是将每一种包装写入核心算法。

### 风险 5：开源许可与资产来源不清

**解决办法：**

建立第三方软件及数据资产台账：

- 代码许可证。
- 模型权重许可证。
- 训练数据来源。
- 模板和标准图纸版权。
- 示例图片版权。
- 输出文件中的第三方素材。

不要因为代码是 MIT，就声称整条管线使用的所有模型、数据和模板都是 MIT。

---

## 九、建议的技术栈

我不建议一开始追求技术栈的多样化。

| 层次 | 建议 | 选择理由 |
|---|---|---|
| 核心语言 | Python | 复用现有环境 |
| 数据协议 | JSON Schema | 跨模块和跨语言 |
| 几何处理 | NumPy + Shapely | 二维几何与拓扑 |
| 网格分析 | Trimesh | 网格检查与处理 |
| CAD 交换 | SVG / DXF | 便于下游制造工具使用 |
| PDF | pypdf + SVG 转 PDF 工具 | 文件导出与检查 |
| 3D | Blender Python API | 复用现有工程资产 |
| 视觉 | TRELLIS.2 + OpenCV | 外观和几何证据 |
| OCR | PaddleOCR / Tesseract 可选 | 包装文字识别 |
| 测试 | pytest | 自动化验收 |
| CLI | Typer | 本地命令行工具 |
| 文档 | Markdown | 开源协作 |

补充两点：

- SVG 和 PDF 应该是首要交付，DXF 是建议增加的交换格式，不应成为 M1 的前置依赖。
- 如果未来支持工业 CAD 交换，再考虑 STEP 或其他专业格式，不要现在就引入完整 CAD 内核。

另外，PDF 应当有明确的印前图层命名、颜色和线型约定，但实际颜色映射应由 Manufacturing Profile 配置，而不是宣称某个颜色方案就是所有印厂通用标准。

## 十、MVP 最终验收清单

建议把以下内容作为 GitHub Issue / Milestone 的正式验收合同。

{@body const checks = [
["输入","能够读取真实包装照片","自动检查文件、分辨率和格式"],
["输入","接受用户输入的真实尺寸","所有尺寸明确使用 mm"],
["输入","记录尺寸来源和不确定性","MEASURED / INFERRED 等状态有效"],
["几何","生成合法 Geometry IR","JSON Schema 验证通过"],
["几何","面板拓扑闭合","无悬空边、非法共享边"],
["几何","折线语义正确","CUT / SCORE / MOUNTAIN / VALLEY 区分"],
["几何","已知基准关键尺寸误差 ≤0.5mm","Golden Test"],
["刀版","输出 1:1 SVG","物理单位和尺寸检查通过"],
["刀版","输出 PDF","页面尺寸与 SVG 一致"],
["刀版","50mm 校验条正确","导出后物理尺寸检查通过"],
["刀版","分层结构正确","裁切、压线、粘口、出血分别识别"],
["3D","可以折叠回实体","闭合残差符合基准阈值"],
["3D","无非法穿插","几何检查通过"],
["QA","报告所有失败项","机器可读取 JSON"],
["工程","不安装 TRELLIS 也能运行","Core 独立安装测试"],
["许可","主体 MIT 与第三方依赖隔离","许可证清单完整"]
]}
{@body const [done,setDone] = DIL.useState([])}
<box border radius="lg" padding={3} gap={3}>
  <row align="center" justify="between">
    **MVP 验收进度**
    <title size="xl" color="default" tabularNums>{done.length}/{checks.length}</title>
  </row>
  <box background="surface-tertiary" height="7px" radius="full" clip>
    <box background="#16A34A" height="7px" radius="full" width={`${done.length/checks.length*100}%`}/>
  </box>
  <text color="secondary" size="xs">可用于后续开发验收，勾选仅表示验收记录，不代表当前项目已经实现。</text>
  {#each checks as item,i}
    <checkbox key={i} checked={done.includes(i)} onChange={v=>setDone(old=>v?[...old,i]:old.filter(x=>x!==i))}>
      <box gap={1}>
        **{item[0]} · {item[1]}**
        <text color="secondary" size="xs">{item[2]}</text>
      </box>
    </checkbox>
  {/each}
  <button block color="secondary" variant="outline" onClick={()=>GenUI.copy(checks.map((x,i)=>`${done.includes(i)?"[x]":"[ ]"} ${x.join(" — ")}`).join("\n"))}>
    <icon name="copy" size="xs"/> 复制验收清单
  </button>
</box>

有一个必须强调的边界：

以上全部通过，只代表 M1 的已知结构样本达到技术验证要求。要正式宣称「印厂可交付」，还必须通过具体印厂的材料、刀模、压痕和印刷工艺审查。

---

## 十一、开源项目名称

我推荐以下几个名字：

| 名称 | 含义 | 评价 |
|---|---|---|
| **DielineKit** | 包装刀版工具箱 | 简短、直观 |
| PackFold | 包装展开与折叠 | 易懂 |
| DielineAI | AI 刀版生成 | 容易限制未来定位 |
| FoldCraft | 包装折叠结构构造 | 品牌感较好 |
| PackGeometry | 包装几何内核 | 技术定位明确 |
| FlatPack | 三维到二维展开 | 名称较通用 |

<box border radius="lg" padding={3} gap={2}>
  <badge color="success">首选建议</badge>
  <title size="2xl">DielineKit</title>
  <text color="secondary" size="sm">A photo-to-manufacturing dieline toolkit.</text>
  **建议仓库：**

  `github.com/topprismdata/dieline-kit`

  **建议定位：**

  Open-source toolkit for reconstructing packaging geometry and generating manufacturing-ready dielines from product photos and measurements.

  <button block onClick={()=>GenUI.copy("https://github.com/topprismdata/dieline-kit")}>
    <icon name="copy" size="xs"/> 复制仓库地址
  </button>
</box>

名称最终使用前还需要检查 GitHub 仓库占用、PyPI 包名及商标冲突。

---

## 十二、架构评审最终决议

我把整个方案收敛成以下 8 项架构决策，建议正式写入 `docs/adr/`。

| ADR | 决策 | 状态 |
|---|---|---|
| ADR-001 | 参数化重建为主，视觉重建为辅 | <badge color="success">APPROVE</badge> |
| ADR-002 | Geometry IR 作为唯一制造几何协议 | <badge color="success">APPROVE</badge> |
| ADR-003 | 真实尺寸优先，视觉推断不能替代实测 | <badge color="success">APPROVE</badge> |
| ADR-004 | TRELLIS.2 作为可选独立能力 | <badge color="success">APPROVE</badge> |
| ADR-005 | DielineForge 采用独立 CLI 适配 | <badge color="success">APPROVE WITH LEGAL REVIEW</badge> |
| ADR-006 | 先做一个完整包装模板的垂直切片 | <badge color="success">APPROVE</badge> |
| ADR-007 | SVG/PDF/3D 均从统一几何协议派生 | <badge color="success">APPROVE</badge> |
| ADR-008 | VALIDATED 与 PRINT-READY 分离 | <badge color="success">APPROVE</badge> |

### 我的最终建议：不要把项目做成一个 AI 包装生成器

我希望这个项目最后形成三个有长期价值的开源资产：

<box border radius="lg" padding={3} gap={3}>
  <row align="center" gap={3}>
    <AsyncImage query="technical packaging carton dieline vector drawing CAD linework" aspectRatio="1:1" maxWidth="88px"/>
    <box flex="1" gap={1}>
      **1. Packaging Geometry Knowledge**

      各类包装的参数化结构、拓扑关系和制造规则。
    </box>
  </row>
  <divider color="subtle"/>
  <row align="center" gap={3}>
    <AsyncImage query="folding paperboard packaging 3d carton unfolded to folded CAD engineering visualization" aspectRatio="1:1" maxWidth="88px"/>
    <box flex="1" gap={1}>
      **2. Geometry Reconstruction Engine**

      从照片、尺寸和视觉证据恢复制造几何。
    </box>
  </row>
  <divider color="subtle"/>
  <row align="center" gap={3}>
    <AsyncImage query="professional packaging dieline print production cut crease glue layers technical layout" aspectRatio="1:1" maxWidth="88px"/>
    <box flex="1" gap={1}>
      **3. Manufacturing Validation Engine**

      从几何正确走向真实印前交付。
    </box>
  </row>
</box>

### 下一步执行顺序

我建议不要再继续扩展技术调研，而是进入架构冻结和 M1 开发准备。

1. 冻结 Geometry IR V0.1。
2. 从母仓提取屋顶包参数化结构，定义独立接口，不直接复制母仓业务代码。
3. 确定一个真实屋顶包作为 Golden Sample，保留实测尺寸、照片和已有 CAD/参数化基准。
4. 写出 M1 的 16 项自动验收测试。
5. 建立 `topprismdata/dieline-kit`，采用 MIT 主体。
6. 两周内完成完整垂直切片。

**我特别希望守住一个原则：M1 宁愿只支持一种包装，但必须真正做到照片、实测尺寸、参数化结构、1:1 刀版、折叠验证、QA 报告完整闭环。**

这比先支持十种包装、却无法保证任何一种真正可印刷，更有开源项目价值。

参考的关键资料：

- <Link ref="turn546067search1" title="FEFCO 官方包装结构编码体系"/>
- <Link ref="turn546067search0" title="GNU GPL 官方 FAQ：独立程序与组合程序边界"/>
- <Link ref="turn546067search60" title="CGATS 包装生产信息与刀版规范清单"/>
- <Link ref="turn546067search63" title="3M Global Packaging Dieline Requirements"/>
- <Link ref="turn546067search62" title="FEFCO 第 12 版结构目录"/>

我的架构评审结论是：**APPROVE TO START M1。** 暂不批准将 M1 扩展成通用单图自动重建系统，也不批准将未经过印厂验证的文件宣传为 PRINT-READY。
