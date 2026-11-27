# 更正报告：D1 根因修正与修复链全绿验证（R09-09 诚信更正）

- 日期：2026-11-27
- 性质：**执行侧主动更正**——撤回 WP-A2-D1 报告中的"平板化"主张；提交修复链全绿证据
- 触发：未舍入数值复核（R09-08 裁决后自查）

## 一、更正内容

**撤回**：WP-A2-D1 报告"冻结 model.usdc 为 FLAT_PATTERN 平板展开件（bbox Y=0）"。
**错误来源**：我方以 `np.round(ext, 1)` 打印 bbox（y=0.0382m 显示为 0.0）并手写 "flat_axis: Y (extent==0)" 标签——显示假象被当作事实写入报告。

**未舍入复核（同一样本 aseptic_brick_v0000 冻结件）**：
- bbox = [95.485, 38.194, 138.582] mm — **完整三维折叠体**（y=38.194mm 即 D）
- 符号体积 = −233,078 mm³ — 封闭实体、**绕向内向**
- trimesh：watertight **TRUE**（封闭）、winding **FALSE**（不一致）、volume −240,514 mm³

## 二、D1 真实根因（修正版）

aseptic_brick/brick 家族折叠体的缺陷 = **面板绕向不一致 + 整体内向约定**：
1. net 定义层 5 个面板对绕向反向（底部反折链 4 + triR）——家族 net 定义缺陷（已定位并源码修复）
2. 折叠体整体绕向为内向约定（体积为负）——导出器未规范化外向

与 R09-03 报告的差异：D1 是**绕向缺陷**（拓扑/方向），不是"表达丢失/平板化"。三重验证史无欺——USDCraft SDK 结构验证器（15 项）不检查绕向/体积符号，175/175 PASS 的口径对该验证器为真；Pixar usdchecker 的 MaterialBindingAPI 红灯为**覆盖缺口**（我们从未声称过 usdchecker），非虚假。

## 三、修复链证据（全绿）

| 步骤 | 操作 | 结果 |
|---|---|---|
| 1 | 家族源码修复：5 个面板对 net 绕向反向修正（候选路径，冻结集未动）| net 相邻边 0 反向对（15 合法）|
| 2 | 修复后家族重导出候选 model_fixed.usdc | trimesh winding **TRUE**（7 重复边消除）+ watertight TRUE + bbox 与解析一致 |
| 3 | 导出规范化：SOLID 契约负体积整体翻转（索引反转一行）| **审计 SOLID 全过 PASS + findings 空** |
| 4 | trimesh 独立复核 | watertight TRUE + winding TRUE + volume **+276,983 mm³（正=外向）**|
| 5 | bbox 对照解析值 | 95.485/38.194/138.582 mm 逐位一致 |

修复 = 家族绕向修正（5 处）+ 导出器负体积规范化（一处）——合计两处小改，无焊接/无重拓扑。

## 四、受影响的前序裁决（请 GPT 重新裁定）

| 前序裁决 | 基于的事实 | 更正后建议 |
|---|---|---|
| D1 表达丢失 ACCEPTED | 平板化证据（错误）| **撤回**；代之以"绕向缺陷+内向约定"已修复（本报告证据）|
| 双表达架构 ADOPT | model.usdc 非折叠体 | 请重裁：blank 表达对刀版/印刷用途是否保留（前提事实已变）；folded SOLID 现已可正确交付 |
| REP-IDENTITY P0 | 9,386 件平板化 PENDING | 重估：9,386 件实为折叠 SOLID（内向/不一致家族仅 brick 系），REP-IDENTITY 字段仍建议登记但内容改为绕向/契约状态 |
| 全量重编译 PROHIBITED | 维持 | 维持（家族修复仅 brick 系受影响，约数百件重编译候选需另审）|

## 五、证据文件

- `output/candidates/aseptic_brick_v0000/wp_fixed/model_normalized.usdc`（修复+规范化候选）
- 未舍入复核输出见本报告表格；审计器 v2.2 判 SOLID PASS
