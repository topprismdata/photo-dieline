# GPT 架构设计评审 (会话 6afda74e-a9fc-83ea-9e58-1144b40273fd, 2026-11-18)
# 抓取方式: backend-api Bearer + mapping 时间序

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
