# GPT 架构设计评审全记录

- 会话: 6afda74e-a9fc-83ea-9e58-1144b40273fd (chatgpt.com, 2026-11-18)
- 抓取: backend-api Bearer + mapping 时间序全量
- 三轮: R1 总体方案 V1.0 / R2 六项裁决+M1冻结 / R3 TDE孪生训练方向
- 共 4 条 assistant 消息, 49256 字符

<!-- assistant msg @2026-11-18T13:25:46.526Z len=29178 -->

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


====================[ASSISTANT MESSAGE]====================

<!-- assistant msg @2026-11-18T13:32:33.285Z len=5749 -->

# 第二轮架构评审：六项裁决

<row align="center" gap={2}>
  <badge color="success">总体 APPROVE</badge>
  <badge color="success">建议冻结 M1</badge>
</row>

## 1. DielineForge 整体移至 M3

<badge color="success">AGREE — 完全同意</badge>

M1/M2 不应引入 DielineForge。

理由：参数化模板已经知道每个面板的尺寸、邻接关系和展开位置，直接生成 2D 几何才是正确路径。再引入通用展开器，相当于把已知的结构重新交给一个通用算法求解，既增加复杂度，也没有实际收益。

明确分工：

- M1：Geometry IR → 自研 2D Layout → SVG/PDF。
- M2：扩展模板及布局规则，仍然自研输出。
- M3：仅在 3D 网格需要展开时，评估 DielineForge 等通用展开工具。

GPL 风险也随之从 M1/M2 主链中移除。

但有一条纪律：M3 引入 DielineForge 时仍需独立进行许可证和组合分发审查，不能因为 CLI 隔离就自动认定法律边界安全。

## 2. 折叠验证脱离 Blender

<badge color="success">AGREE WITH CONDITIONS</badge>

我同意 Blender 不进入 M1 的验收门。纯 Python 数值验证更适合作为核心几何引擎的测试方式，也更容易在无显示环境下实现可重复 CI。

建议验证分为三个层次：

1. **运动学验证**：以面板邻接图为基础，围绕共享折线进行刚体旋转，验证折叠角度及顶点闭合。
2. **几何验证**：检查面板之间的非法穿插、粘口接合和最终几何位置。
3. **拓扑验证**：检查共享边一致性、边界闭合及折叠后的连接关系。

这里我有一个技术修正：不能只用 NumPy 做顶点旋转，然后比较最终顶点坐标。还必须检查面板内部的相交情况，否则两个面板可能顶点都正确，却在中间发生穿插。

建议 M1 采用：

- NumPy：刚体变换和折叠运动学。
- Shapely：二维几何和轮廓运算。
- Trimesh 或自研三角面片检测：三维相交测试，视实际复杂度选用。

Blender 的职责仅为本地可视化：

- 输出折叠状态 PNG。
- 方便人工观察结构。
- 不决定 QA PASS/FAIL。
- 不成为核心运行依赖。

**重要限制：M1 只验证已知模板的规定折叠路径，不承诺任意复杂折叠过程的碰撞自由性。**

## 3. Geometry IR V0.1 冻结

<badge color="success">建议冻结：5 个顶层对象</badge>

我建议顶层严格控制为五个对象，不要把每个制造细节都设计成独立顶层对象。

| 顶层字段 | 类型 | 语义 |
|---|---|---|
| `meta` | object | IR 版本、单位、坐标系、创建信息及来源 |
| `package` | object | 包装类型、整体尺寸、材料和模板身份 |
| `panels` | array | 所有面板的二维轮廓、三维参考几何和语义角色 |
| `edges` | array | 面板之间的连接关系、折叠属性和边界制造语义 |
| `features` | array | 粘口、开窗、提手、出血、套准标记等附加制造特征 |

这里有一个关键决定：**不再单独建立 cuts、folds、glue_tabs、bleeds 四个顶层数组。**

它们统一进入 `edges` 或 `features`：

- 面板连接和折线属于 `edges`。
- CUT 边界属于 `edges` 的边界语义。
- 粘口、开窗、出血属于 `features`。
- 山折、谷折属于 `edges` 的折叠语义。

这样既控制顶层复杂度，也保留未来扩展空间。

另外，证据溯源不应该被遗漏。V0.1 将证据作为尺寸、材料和结构参数的附属属性，不另建顶层 `evidence` 对象。这样既可以保留 MEASURED、DERIVED、INFERRED 等状态，也不会扩大顶层协议。

## 4. 与母仓完全独立

<badge color="success">AGREE — 完全同意</badge>

建议正式确立 **Repository Independence** 原则：

- 不使用 Git Submodule。
- 不 import `openusd-retail-twin`。
- 不复制母仓代码。
- 不共享运行时数据库、配置和依赖环境。
- 只通过 README 互链。
- 屋顶包模板根据公开几何规则和自身需求重新实现。

唯一需要保留的是知识层面的关联：可以在文档中记录模板的结构来源、几何定义和独立验证依据。

**没有反对情形。** 即使未来两个项目需要互相使用，也优先通过稳定的 JSON Schema、SVG、GLB 等文件协议交换，而不是建立代码级耦合。

我还建议增加一个独立性验收项：

```text
M1 CI:
  checkout dieline-kit only
  install core dependencies
  run full pipeline
  no access to parent repository
```

这样才能证明它是真正独立的开源项目，而不是母仓的一个拆分目录。

## 5. CI 分层：Blender 渲染不进入 CI

<badge color="success">AGREE — 建议三层 CI</badge>

但我不建议把所有 3D 验证都移出 CI。需要区分数值验证和图像渲染。

| CI 层级 | 内容 | 执行时机 | 是否阻断合并 |
|---|---|---|---|
| L0 Unit | IR、参数、几何、尺寸、拓扑 | 每次 PR | 是 |
| L1 Integration | SVG/PDF 导出、折叠运动学、相交检测 | 每次 PR | 是 |
| L2 Release Visual | Blender headless 渲染、截图、人工检查 | Release 前 | 否，作为发布签核 |

具体建议：

**L0：纯 Python 单元测试**

- JSON Schema。
- 模板参数边界。
- 单位转换。
- 轮廓闭合。
- 面板邻接。
- CUT/SCORE 语义。
- 50mm 校验条。

**L1：完整集成测试**

- 从 PackageSpec 生成 Geometry IR。
- 生成 SVG/PDF。
- 检查 PDF 物理页面尺寸。
- 运行折叠运动学。
- 检查折叠闭合残差。
- 检查面板相交。
- 检查异常输入拒绝机制。

这层必须在 GitHub Actions 无显示环境运行。

**L2：Release Visual**

本地运行 Blender headless，生成：

- 折叠状态渲染图。
- 正面、侧面、顶部视角。
- 必要时生成与真实照片的并排对比。

人工确认渲染没有明显结构异常后，才允许发布。

还有一个建议：把 L2 的截图保存为 Release Artifact，而不是把每次渲染结果提交进 Git 仓库。只有经过人工批准的 Golden Render 才进入版本管理。

<box border radius="lg" padding={3} gap={2}>
  **CI 最终原则**
  <row align="center" justify="between">
    Python 几何与制造验证
    <badge color="success">必须自动 PASS</badge>
  </row>
  <row align="center" justify="between">
    Blender 渲染
    <badge color="secondary">Release 辅助</badge>
  </row>
  <row align="center" justify="between">
    人工结构复核
    <badge color="warning">发布签核</badge>
  </row>
</box>

## 6. 仓库名称终审

<badge color="warning">建议调整名称</badge>

我补做了 GitHub 公开检索，比较了几个候选名称及相关包装项目。

发现一个值得重视的竞争信号：<Link ref="turn726804search0" title="Die Cut Studio"/> 已经提供参数化刀版、折叠预览和 1:1 PDF/SVG/DXF 导出；<Link ref="turn726804search1" title="PackBox"/> 也覆盖了参数化盒型与折叠模拟。另有 <Link ref="turn726804search2" title="Origami-3Dfolder-ai"/> 涉及从展开图到 3D 折叠。

这不意味着名称冲突，但意味着不能把项目简单定位为又一个 Dieline Generator。

名称判断：

| 候选 | 判断 | 原因 |
|---|---|---|
| dieline-kit | 不首选 | 太通用，搜索辨识度弱 |
| photo-dieline | <badge color="success">推荐</badge> | 突出照片输入和项目差异 |
| dieline-from-photo | 可选 | 意义明确，但较长 |
| unfold-kit | 不推荐 | 容易被理解为通用网格展开工具 |
| packfold | 不推荐 | 容易与现有包装折叠项目混淆 |

<box border radius="lg" padding={3} gap={2}>
  <badge color="success">最终推荐</badge>
  <title size="2xl">PhotoDieline</title>
  <text color="secondary" size="sm">From physical packaging to manufacturing geometry.</text>
  **GitHub 仓库建议：**

  `topprismdata/photo-dieline`

  Python 包建议：`photo-dieline`

  导入名称：`photo_dieline`
</box>

这里需要说明检索边界：公开搜索没有提供足够证据证明 `photo-dieline` 在 GitHub、PyPI 和商标层面绝对未被占用，因此目前是命名推荐，不是名称可用性法律保证。正式创建前仍需检查仓库创建结果、PyPI 名称和商标。

我的最终选择是 **photo-dieline，而不是 dieline-kit**。

理由不是名称更好听，而是它更准确地表达项目的核心入口，也有利于未来和普通参数化刀版生成器区分。

---

## M1 冻结范围最终表述

**M1（两周、单人垂直切片）正式冻结为：** 以 `photo-dieline` 独立 MIT 仓库为载体，选择已有基础的 gable-top 屋顶包作为唯一 Golden Sample，输入真实包装照片、用户提供的关键实测尺寸及人工确认的包装类型，通过独立定义的 Geometry IR V0.1（固定五个顶层对象：meta、package、panels、edges、features）生成参数化制造几何；由自研 2D Layout Engine 直接输出分层 1:1 SVG/PDF，并通过纯 Python 折叠运动学、几何相交检测、尺寸闭合和文件物理尺寸检查完成自动 QA；Blender 仅用于本地折叠可视化，不进入 CI 验收门；不引入 TRELLIS.2、DielineForge、母仓代码或运行时依赖，不开发自动包装分类和非标包装重建，不承诺未经印厂验证的 PRINT-READY。M1 交付完整源码、Schema、Golden Sample、SVG/PDF、折叠验证数据、QA Report、CI 和技术文档，全部核心测试可在无显示环境独立运行。

<box border radius="lg" padding={3} gap={2}>
  <row align="center" justify="between">
    **第二轮架构评审**
    <badge color="success">APPROVED</badge>
  </row>
  <title size="xl" color="success">进入架构冻结</title>
  <text color="secondary" size="sm">冻结范围：M1。M2/M3 保留为未来扩展，不作为本轮开发承诺。</text>
  **冻结后的关键决定：**
  - 主仓：`topprismdata/photo-dieline`
  - License：MIT
  - Geometry IR：V0.1，5 个顶层对象
  - 2D 引擎：自研
  - 折叠验收：纯 Python
  - Blender：仅可视化
  - DielineForge：M3 再评估
  - 母仓：完全独立
</box>

**评审意见：不再增加 M1 功能，不再扩展技术选型。可以进入架构冻结与实施。**


====================[ASSISTANT MESSAGE]====================

<!-- assistant msg @2026-11-18T13:35:30.863Z len=11159 -->

# 第三轮架构评审：Twins Data Engine（TDE）

<row align="center" gap={2}>
  <badge color="success">方向 APPROVE</badge>
  <badge color="success">不推翻 M1</badge>
  <badge color="info">建议纳入 M2 主轨</badge>
</row>

**我的核心裁决：TDE 应成为参数化主干的训练数据基础设施，而不是另一条独立的刀版生成路线。**

这次新方向实际上补上了原架构中一个重要缺口：此前我们有参数化模板、几何内核和 QA，但缺少规模化的视觉识别与参数恢复能力。

现在可以形成一个更完整的闭环：

**参数化生成 → 合成孪生数据 → 模型学习 → 真实照片识别 → 参数化几何重建 → 制造 QA。**

这与母仓货架 SDG → YOLO 微调的经验具有很强的方法论一致性。

但有一个重要区别：货架检测主要学习视觉目标识别；包装重建还必须学习结构参数之间的几何约束。不能只追求分类准确率。

---

## 1. TDE 插入位置：M2 主轨，并行建设，不设独立 M2.5

<badge color="success">裁决：M2 并行主轨</badge>

不建议单独设 M2.5。

原因是 TDE 与模板扩展存在强依赖：

- 没有模板，就没有可信的参数真值。
- 没有 Geometry IR，就没有统一标签协议。
- 没有折叠验证，就不能判断合成样本的结构是否有效。
- 没有模板扩展，训练数据会不断重复同一种结构。

因此，M2 应拆成两个并行工作流：

| 工作流 A | 工作流 B |
|---|---|
| 模板库扩展 | Twins Data Engine |
| FEFCO 0201 | 参数域采样 |
| Gable-top 完善 | 自动生成配对数据 |
| 结构约束完善 | Blender 域随机化 |
| Manufacturing Profile | 数据集版本与质量审计 |

两条工作流共享 Geometry IR 和 QA，但不互相阻塞所有工作。

### TDE 的位置

<box border radius="lg" padding={3} gap={2}>
  <box background="rgba(22,163,74,0.08)" radius="md" padding={3}>
    **Parametric Template Engine**

    生成已知结构和参数真值
  </box>
  <box align="center"><icon name="arrow-down" color="secondary"/></box>
  <box background="rgba(59,130,246,0.08)" radius="md" padding={3}>
    **Twins Data Engine**

    参数采样 → 3D → Blender 渲染 → 数据集
  </box>
  <box align="center"><icon name="arrow-down" color="secondary"/></box>
  <box background="rgba(59,130,246,0.08)" radius="md" padding={3}>
    **Learning Pipeline**

    T1 分类 → T2 参数回归
  </box>
  <box align="center"><icon name="arrow-down" color="secondary"/></box>
  <box background="rgba(22,163,74,0.08)" radius="md" padding={3}>
    **Existing Manufacturing Pipeline**

    用户确认 / 参数约束 → Geometry IR → SVG/PDF → QA
  </box>
</box>

### TDE 与用户手输三尺寸的关系

这里我建议明确一个原则：

**模型预测值永远不能覆盖 MEASURED 实测值。**

把参数来源分为五级：

| 来源 | Evidence Status | 优先级 |
|---|---|---:|
| 卡尺/可靠实测 | MEASURED | 最高 |
| 已知 CAD 或可信规格文件 | VERIFIED_SOURCE | 高 |
| 几何约束计算 | DERIVED | 中高 |
| 模型回归 | INFERRED | 中低 |
| 系统默认 | DEFAULTED | 最低 |

举例：

用户实测长度 68.3mm，模型预测 67.6mm。

系统不能自动选择 67.6mm，而应该：

1. 保留 MEASURED 68.3mm。
2. 记录 INFERRED 67.6mm。
3. 计算 0.7mm 差异。
4. 检查是否存在透视、结构识别或测量错误。
5. 超出阈值时要求复核。

另外，模型应该支持缺失参数补全，而不是强制要求用户永远输入三个尺寸。

当模型有足够置信度时，可以减少问答；但关键尺寸仍必须满足测量证据或经过验证的约束条件。

**TDE 的产品价值不是取消用户测量，而是减少用户需要测量的次数。**

## 2. T1 + T2 是否取代 M3 的手工识别与问答？

<badge color="success">裁决：同意学习实现，但保留人工兜底</badge>

我建议调整原来的 M3 计划。

原来 M3 中的：
- 自动包装类型推荐；
- 关键尺寸问答；
- 视觉辅助参数识别；

应当改为以 T1+T2 学习模型为核心，人工问答只处理不确定和冲突情况。

但不能把这理解成完全取消问答。

### T1：Package Classification

输入照片，输出包装结构类别及概率分布。

例如：

| 类别 | 预测概率 |
|---|---:|
| Gable-top | 0.94 |
| Folding Carton | 0.03 |
| RSC Carton | 0.02 |
| Other | 0.01 |

分类模型必须支持 UNKNOWN / OUT_OF_SCOPE，而不是强制从已有模板中选一个。

建议验收指标：

- Macro-F1。
- 各类别 Recall。
- UNKNOWN 拒识能力。
- 不同拍摄条件下的分类稳定性。

### T2：Parametric Regression

输入照片及 T1 输出的结构类别，预测模板参数。

例如：

```text
package_type: gable_top

predicted_parameters:
  length_mm: 68.1
  width_mm: 68.5
  body_height_mm: 104.8
  roof_height_mm: 24.2

confidence:
  length: ...
  width: ...
  body_height: ...
  roof_height: ...
```

这里我建议使用**结构条件化的多任务回归**，而不是一个模型直接回归所有包装的所有参数。

例如 Gable-top 和 FEFCO 0201 的参数空间完全不同。

更重要的是，回归结果必须经过模板约束检查：

- 参数范围是否合法？
- 面板尺寸是否闭合？
- 是否满足结构比例约束？
- 是否与照片证据矛盾？
- 是否存在多个可能的结构解释？

模型预测的参数不能直接无条件进入制造输出。

### 建议的智能化工作流

<box border radius="lg" padding={3} gap={2}>
  **真实照片输入**
  <box align="center"><icon name="arrow-down" color="secondary"/></box>
  <box background="rgba(59,130,246,0.08)" radius="md" padding={3}>
    **T1 分类**

    识别包装类型，给出置信度和候选类别。
  </box>
  <box align="center"><icon name="arrow-down" color="secondary"/></box>
  <box background="rgba(59,130,246,0.08)" radius="md" padding={3}>
    **T2 参数回归**

    预测长度、宽度、高度及类型专属参数。
  </box>
  <box align="center"><icon name="arrow-down" color="secondary"/></box>
  <box background="rgba(189,150,80,0.09)" radius="md" padding={3}>
    **Evidence Reconciliation**

    MEASURED 优先，模型补全缺失参数，冲突触发人工确认。
  </box>
  <box align="center"><icon name="arrow-down" color="secondary"/></box>
  <box background="rgba(22,163,74,0.08)" radius="md" padding={3}>
    **Parametric Template**

    输出 Geometry IR，进入原有制造 QA。
  </box>
</box>

我的进一步建议：模型输出不应该只有一个预测数字，还应该输出预测不确定性。

对于参数回归，可以采用分位数回归或经过校准的预测区间。比如：

```text
length:
  estimate: 68.1 mm
  interval_90: [67.4, 68.8]
  evidence: INFERRED
```

这比单纯给出一个 0.95 的模型置信度更有工程价值。

---

## 3. Sim2Real：必须先冻结真实照片 Golden Test Set

<badge color="warning">最高风险：必须设独立验证门</badge>

我认为这次新方向最大的风险不是合成数据量不够，而是：

**模型学会了 Blender 的世界，却没有学会真实包装的世界。**

尤其是包装照片有一些合成渲染很难自然覆盖的现象：

- 纸板微小凹凸和压痕。
- 封口变形。
- 纸张纤维与涂层差异。
- 真实印刷偏色和网点。
- 手机镜头畸变与自动锐化。
- 手持遮挡、反光和不均匀光照。
- 真实包装制造误差。

所以我不接受只用合成测试集报告 T1/T2 成绩。

### 3.1 先冻结真实照片基准集

建议在 TDE 训练之前建立 Real Golden Set。

第一阶段不需要很大，但必须有代表性。

建议首批：

| 数据集 | 数量 | 用途 |
|---|---:|---|
| Synthetic Train | 20,000+ | 初始训练 |
| Synthetic Validation | 3,000+ | 超参数选择 |
| Real Development | 100–200 | 真实域调试 |
| Real Golden Test | 200–300 | 独立最终评估 |

这里的数字是首期建议规模，不是统计学保证。

Real Golden Test 必须：

1. 真实包装实物拍摄。
2. 有真实尺寸或可靠 CAD 基准。
3. 包含不同手机、拍摄距离、角度和光照。
4. 包含不同包装材料和表面状态。
5. 测试样本与训练样本按物理产品和拍摄会话隔离。
6. 在首次模型训练前冻结，并保存数据集版本及校验哈希。

特别强调：不能将同一实物的不同角度照片随机分到训练集和测试集，否则会产生严重的数据泄漏。

### 3.2 三阶段 Sim2Real 验证协议

<box border radius="lg" padding={3} gap={3}>
  <box gap={1}>
    <badge color="info">Experiment A</badge>
    **Synthetic-only Baseline**

    只用合成数据训练，在真实 Golden Test 上测试。

    目的：测量纯合成数据的迁移能力。
  </box>
  <divider color="subtle"/>
  <box gap={1}>
    <badge color="info">Experiment B</badge>
    **Domain Randomization Ablation**

    分别调整光照、背景、相机、材质、印刷、遮挡和图像退化强度。

    目的：确定哪些随机化因素真正改善真实域表现。
  </box>
  <divider color="subtle"/>
  <box gap={1}>
    <badge color="info">Experiment C</badge>
    **Synthetic + Real Fine-tuning**

    使用训练集中的少量真实标注数据进行混合训练或微调。

    目的：判断真实数据是否能显著改善性能，以及改善是否具有跨产品泛化能力。
  </box>
</box>

注意：Real Development 可以参与训练迭代，但 Real Golden Test 永远不能参与训练、阈值选择和模型选择。

### 3.3 域随机化不能只追求随机程度

建议建立六组可控变量：

| 随机化维度 | 主要变化 |
|---|---|
| Camera | 焦距、透视、畸变、拍摄距离 |
| Lighting | 色温、方向、强度、阴影 |
| Material | 纸板粗糙度、反射、折痕 |
| Print | 色偏、纹理、印刷图案、网点 |
| Environment | 背景、桌面、场景、遮挡 |
| Image Quality | 模糊、噪声、压缩、曝光 |

但是必须避免一个错误：随机化越强，不代表真实域泛化越好。

例如把包装变成严重扭曲、不可见的状态，虽然增加了数据多样性，却可能让模型学习到真实业务中不存在的分布。

我建议保留三档：

- REALISTIC：符合真实拍摄分布。
- MODERATE：扩大正常拍摄变化范围。
- STRESS：极端情况，仅用于鲁棒性测试。

三档分别报告，不能混成一个总成绩。

### 3.4 设立明确的 Sim2Real 放行门

建议 T1/T2 都必须分别通过以下测试：

| 指标 | 首期建议门槛 |
|---|---:|
| T1 Real Macro-F1 | ≥0.90 |
| T1 各主要类别 Recall | ≥0.85 |
| T2 关键尺寸 MAE | ≤1.0mm |
| T2 关键尺寸误差 P90 | ≤2.0mm |
| 模板约束合法率 | ≥99% |
| UNKNOWN 拒识 | 单独报告 Precision / Recall |

这些是首期研究目标，不是已经证明可达到的性能承诺。

还要增加一项特别重要的指标：

**参数进入制造主干后的最终几何通过率。**

因为模型预测 68.3mm 并不代表它生成的整张刀版正确。

我建议单独统计：

- 参数预测正确率。
- Geometry IR 生成成功率。
- Geometry QA 通过率。
- 人工修正比例。
- 最终制造验证通过率。

只有最后一项才能真正说明 TDE 给主项目带来了多少价值。

## 4. TDE 是否强化 ADR-001：模型永远不直接生成刀版？

<badge color="success">STRONGLY AGREE — 强化 ADR-001</badge>

我认为这次方向反而让 ADR-001 更有说服力，而且应该把它升级为不可轻易改变的架构原则。

**生成模型负责理解照片，参数化内核负责构造制造几何。**

我建议正式划定三个能力边界：

| 层次 | 技术 | 输出 | 权威性 |
|---|---|---|---|
| Perception | T1 分类模型 | 包装类型 | 识别建议 |
| Parameter Inference | T2 回归模型 | 模板参数及不确定性 | 参数建议 |
| Manufacturing Geometry | Geometry IR + 模板引擎 | 真实制造几何 | 唯一权威 |

T3 也不能改变这个原则。

即使未来训练 photo→Geometry IR 模型，也应当把它定义为候选结构生成器，而不是最终制造文件生成器。

它输出的候选 IR 必须：

1. 通过 JSON Schema。
2. 通过拓扑约束。
3. 通过尺寸闭合。
4. 通过折叠运动学。
5. 通过制造规则。
6. 通过人工或其他独立证据复核。

最终仍由统一的 Geometry Kernel 规范化并导出 SVG/PDF。

### 我建议新增 ADR-009

<box border radius="lg" padding={3} gap={2}>
  <badge color="success">PROPOSED — FREEZE</badge>
  **ADR-009：Learning-to-Parameter, Not Learning-to-Manufacture**

  所有学习模型仅负责包装类型识别、参数推断及候选结构提出。最终制造几何必须由经过验证的参数化模板与 Geometry Kernel 生成。任何学习模型不得绕过制造几何验证直接发布刀版文件。

  **核心理由：**
  - 保持尺寸可追溯。
  - 保持制造规则确定性。
  - 降低生成模型幻觉风险。
  - 维持 SVG/PDF 输出一致性。
  - 允许模型独立升级而不破坏制造内核。
</box>

### 对三条结构数据来源的额外审查

我原则上批准三路来源，但有一个需要补充的治理门。

| 来源 | 裁决 | 处理方式 |
|---|---|---|
| 自有参数化模板 | <badge color="success">GO</badge> | 作为最高可信度的 Ground Truth |
| Sketchfab CC 资产 | <badge color="warning">CONDITIONAL</badge> | 逐资产核验许可证、作者、改编和再分发条件 |
| PackBox / DieCutStudio 输出 | <badge color="warning">CONDITIONAL</badge> | 先核验代码许可、输出版权和使用条款 |

尤其不能认为开源软件输出的刀版就天然可以作为 MIT 项目的训练数据或公开数据集。

我建议 TDE 为每条样本增加：

- `source_type`
- `source_uri`
- `source_license`
- `author`
- `derivative_status`
- `redistribution_allowed`
- `commercial_use_allowed`
- `dataset_split`
- `generator_version`

如果某资产只能用于内部实验，就必须在数据集中隔离，不能混入公开发布的训练数据包。

此外，**自有模板随机生成的数据虽然可以无限增加数量，但不等于无限增加独立信息。** 应该按参数空间、结构变体和真实制造边界衡量覆盖度，而不是用合成图片数量作为项目成绩。

---

## 五、TDE 插入后的 M1/M2/M3 最终重排

我建议不改变 M1，只重构 M2 和 M3。TDE 的数据协议、训练管线和模型评估都进入 M2，T1/T2 从原 M3 提前，T3 保留远期研究。

| 阶段 | 核心任务 | 交付物 | 验收目标 |
|---|---|---|---|
| **M1** | 原定参数化垂直切片 | Gable-top、Geometry IR、SVG/PDF、纯 Python 折叠 QA | 原冻结范围全部通过 |
| **M2-A** | 模板库扩展 | FEFCO 0201、Gable-top 完善、Template Contract | 多模板统一 IR |
| **M2-B** | Twins Data Engine | 参数采样、3D 生成、Blender 渲染、数据集构建 | 孪生数据自动生成和可追溯 |
| **M2-C** | 真实数据基准 | Real Golden Set、标注规范、数据版本管理 | 独立测试集冻结 |
| **M2-D** | T1 分类模型 | 包装类型识别、UNKNOWN 拒识 | 真实域分类验证 |
| **M2-E** | T2 参数回归 | 类型条件化参数预测、置信区间 | 真实域尺寸与几何验证 |
| **M3-A** | 视觉重建增强 | TRELLIS.2、Mesh Analysis、非标结构辅助 | 视觉证据与参数化结构融合 |
| **M3-B** | 智能交互 | 自动补全参数、冲突检测、最少问答 | 降低人工测量与确认成本 |
| **M3-C** | T3 研究 | Photo→Candidate Geometry IR | 探索端到端结构生成，不绕过制造 QA |

### 建议的执行依赖关系

```text
M1: Parametric Manufacturing Core
                |
                v
       +--------+---------+
       |                  |
       v                  v
M2-A Template Engine   M2-B TDE
       |                  |
       +--------+---------+
                |
                v
       M2-C Real Golden Set
                |
                v
          +-----+-----+
          |           |
          v           v
       T1 Class    T2 Regression
          |           |
          +-----+-----+
                |
                v
       Evidence Reconciliation
                |
                v
       Parametric Geometry IR
                |
                v
       Manufacturing QA
                |
                v
            M3 Vision
                |
                v
         T3 Exploratory
```

这里有一个执行顺序上的细节：M2-B 可以先用 M1 的 Gable-top 模板开始开发，不必等待 M2-A 的所有模板完成；M2-C 的真实 Golden Set 应尽早冻结，不能等模型训练完成才开始采集。

## 六、最终架构决议

建议在现有 ADR-001 至 ADR-008 之外，增加以下三项：

| ADR | 新决策 | 裁决 |
|---|---|---|
| ADR-009 | Learning-to-Parameter, Not Learning-to-Manufacture | <badge color="success">APPROVE</badge> |
| ADR-010 | Synthetic-to-Real Evaluation Protocol | <badge color="success">APPROVE</badge> |
| ADR-011 | Dataset Provenance & Licensing | <badge color="success">APPROVE</badge> |

我的最终判断：

**TDE 不是给项目增加一条 AI 功能，而是把项目从一个参数化刀版工具，升级为一个具有持续学习能力的包装几何重建系统。**

但要守住三个边界：

1. **M1 不动。** 先完成确定性的制造几何闭环。
2. **M2 建立数据飞轮。** 模板生成真值，真值训练模型，真实照片验证模型。
3. **M3 扩展视觉智能。** 模型提高输入自动化程度，但不接管制造几何的最终决定权。

我尤其赞成将母仓的货架 SDG → YOLO 微调经验迁移过来，但不要简单复制训练流程。包装项目需要增加结构拓扑、参数约束、折叠闭合和制造可行性这些独有的标签与验证机制。

<box border radius="lg" padding={3} gap={2}>
  <title size="xl" color="success">第三轮评审：APPROVE</title>
  **最终冻结意见**

  - M1：维持原冻结范围。
  - TDE：纳入 M2 主轨，与模板扩展并行。
  - T1/T2：提前到 M2。
  - Sim2Real：独立 Golden Test 硬门。
  - T3：保留 M3 研究，不作为交付承诺。
  - ADR-001：强化，不修改。
  - 新增 ADR-009/010/011。
</box>

**我认为现在已经形成了一个非常清晰的长期技术路线：先有可信的几何真值，再有规模化孪生数据，最后让模型学习如何从真实照片恢复这些几何真值。**

这条路线值得投入，而且比直接训练一个端到端照片生成刀版模型稳健得多。


====================[ASSISTANT MESSAGE]====================

<!-- assistant msg @2026-11-18T13:37:33.044Z len=2740 -->

## 五、TDE 插入后的 M1/M2/M3 最终重排

我建议不改变 M1，只重构 M2 和 M3。TDE 的数据协议、训练管线和模型评估都进入 M2，T1/T2 从原 M3 提前，T3 保留远期研究。

| 阶段 | 核心任务 | 交付物 | 验收目标 |
|---|---|---|---|
| **M1** | 原定参数化垂直切片 | Gable-top、Geometry IR、SVG/PDF、纯 Python 折叠 QA | 原冻结范围全部通过 |
| **M2-A** | 模板库扩展 | FEFCO 0201、Gable-top 完善、Template Contract | 多模板统一 IR |
| **M2-B** | Twins Data Engine | 参数采样、3D 生成、Blender 渲染、数据集构建 | 孪生数据自动生成和可追溯 |
| **M2-C** | 真实数据基准 | Real Golden Set、标注规范、数据版本管理 | 独立测试集冻结 |
| **M2-D** | T1 分类模型 | 包装类型识别、UNKNOWN 拒识 | 真实域分类验证 |
| **M2-E** | T2 参数回归 | 类型条件化参数预测、置信区间 | 真实域尺寸与几何验证 |
| **M3-A** | 视觉重建增强 | TRELLIS.2、Mesh Analysis、非标结构辅助 | 视觉证据与参数化结构融合 |
| **M3-B** | 智能交互 | 自动补全参数、冲突检测、最少问答 | 降低人工测量与确认成本 |
| **M3-C** | T3 研究 | Photo→Candidate Geometry IR | 探索端到端结构生成，不绕过制造 QA |

### 建议的执行依赖关系

```text
M1: Parametric Manufacturing Core
                |
                v
       +--------+---------+
       |                  |
       v                  v
M2-A Template Engine   M2-B TDE
       |                  |
       +--------+---------+
                |
                v
       M2-C Real Golden Set
                |
                v
          +-----+-----+
          |           |
          v           v
       T1 Class    T2 Regression
          |           |
          +-----+-----+
                |
                v
       Evidence Reconciliation
                |
                v
       Parametric Geometry IR
                |
                v
       Manufacturing QA
                |
                v
            M3 Vision
                |
                v
         T3 Exploratory
```

这里有一个执行顺序上的细节：M2-B 可以先用 M1 的 Gable-top 模板开始开发，不必等待 M2-A 的所有模板完成；M2-C 的真实 Golden Set 应尽早冻结，不能等模型训练完成才开始采集。

## 六、最终架构决议

建议在现有 ADR-001 至 ADR-008 之外，增加以下三项：

| ADR | 新决策 | 裁决 |
|---|---|---|
| ADR-009 | Learning-to-Parameter, Not Learning-to-Manufacture | <badge color="success">APPROVE</badge> |
| ADR-010 | Synthetic-to-Real Evaluation Protocol | <badge color="success">APPROVE</badge> |
| ADR-011 | Dataset Provenance & Licensing | <badge color="success">APPROVE</badge> |

我的最终判断：

**TDE 不是给项目增加一条 AI 功能，而是把项目从一个参数化刀版工具，升级为一个具有持续学习能力的包装几何重建系统。**

但要守住三个边界：

1. **M1 不动。** 先完成确定性的制造几何闭环。
2. **M2 建立数据飞轮。** 模板生成真值，真值训练模型，真实照片验证模型。
3. **M3 扩展视觉智能。** 模型提高输入自动化程度，但不接管制造几何的最终决定权。

我尤其赞成将母仓的货架 SDG → YOLO 微调经验迁移过来，但不要简单复制训练流程。包装项目需要增加结构拓扑、参数约束、折叠闭合和制造可行性这些独有的标签与验证机制。

<box border radius="lg" padding={3} gap={2}>
  <title size="xl" color="success">第三轮评审：APPROVE</title>
  **最终冻结意见**

  - M1：维持原冻结范围。
  - TDE：纳入 M2 主轨，与模板扩展并行。
  - T1/T2：提前到 M2。
  - Sim2Real：独立 Golden Test 硬门。
  - T3：保留 M3 研究，不作为交付承诺。
  - ADR-001：强化，不修改。
  - 新增 ADR-009/010/011。
</box>

**我认为现在已经形成了一个非常清晰的长期技术路线：先有可信的几何真值，再有规模化孪生数据，最后让模型学习如何从真实照片恢复这些几何真值。**

这条路线值得投入，而且比直接训练一个端到端照片生成刀版模型稳健得多。