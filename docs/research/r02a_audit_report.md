# R02-A 独立实验报告：三角化与面角 UV 正确性审计

- 日期：2026-11-27
- 性质：R02-A 送审件（按 `engineering_verdicts.md` 共识，单变量纪律：只审计三角化+面角 UV 正确性，不动材质/光照/印刷/渲染参数）
- 审计工具：`scripts/audit_r02a.py`（只读，不修改任何冻结资产）
- 样本：107 个 SKU（77 结构家族各取首个 + 随机 30，seed=42），来自 `output/pack10k_scale10k/` 冻结发行集
- 证据：`evidence/r02a_results.json`（逐件原文）、`evidence/usdcheck_brick.txt`、`evidence/usdcheck_rsc.txt`

## 一、六门禁结果

| 门禁 | 结果 | 说明 |
|---|---|---|
| G01 纯三角化+流形边界 | **90/107 过** | 17 件有重复有向边/奇数边界（裂缝）缺陷，见缺陷分类 |
| G02 面绕向/法线方向 | **94/107 过** | 闭壳体积≤0 与开壳绕向翻转两类 |
| G03 faceVarying UV | **96/107 过** | 11 件退化 UV 面（零面积 UV 三角）|
| G04 UV 接缝连续性 | **裂缝 0** | 77 处接缝全部为图集合法切割，无一端连续一端断裂的 crack |
| G05 USD 导出重读保持 | **107/107 过** | points/faceVertexIndices 二次读取字节级一致 |
| G06 历史故障回归复现 | **复现成功** | `output/nv960_usd/shopping_cart.usdc` 逐壳审计：大量部件为**零厚度平板**（bbox 一维为 0，符号体积 ≈0），绕向不可判定——即设备棚拍"黑色渲染"事件的根因（薄壳在 Cycles 严格背向剔除下退化）。已建最小复现样本 |

## 二、缺陷分类（17 件 G01/G02 失败 + 11 件 G03 失败）

| 类 | 缺陷 | 涉及家族/样本 | 特征 |
|---|---|---|---|
| D1 | 平板化+重复边+绕向翻转 | aseptic_brick、brick_250ml（全部抽中变体，100% 复现）| 20 tris/12 pts，bbox Y=0（**平板展开态**？），7 条重复有向边 + 7 条奇数边界 + 7 处相邻翻转——系统性导出缺陷 |
| D2 | 奇数边界裂缝（开壳）| prism_dust、mailer_diecut、window_box、slide_box、tray_6corner、food_sushi_tray、tray_liner | 边界边 15-29 且为奇数 → 必有重复面/裂缝 |
| D3 | 零体积闭壳 | clamp_shell、display_counter（vol≈-0.000）+ nv960 购物车全部面板 | bbox 一维为 0 的平板被当闭壳导出 |
| D4 | 退化 UV 面 | food_fries_sleeve、food_bento、food_clamshell、tray_4corner/6corner/domelid/lid_overfit/wedge、clamp_shell、display_counter | 每件 3-5 个零面积 UV 三角 |

## 三、交叉验证（官方工具）

- `usdchecker` 对抽中样本 **exit=1**：`usdShadeValidators:MaterialBindingApiAppliedValidator.MissingMaterialBindingAPI`（有材质绑定但 prim 未 apply MaterialBindingAPI）——**两件样本均失败**（含我方审计通过件 rsc）。
- **口径差异声明**：此结果与既有合规台账"过 NVIDIA 原版验证器"表述存在出入，需核对当初验证器版本/参数/样本范围。usdchecker 不检查流形/绕向/UV——本审计覆盖了官方工具的盲区，两套检查互补而非互斥。

## 四、根因假设（未修复，留待裁决阶段）

- D1：brick 家族几何生成端输出平板展开态 + `_solid_triangles_mm` 对重复顶点多边形产重边——导出器缺陷假设（需读生成端代码定位）。
- D2：折叠面的共点合并遗漏，奇数边界=沿折缝的重复三角。
- D3：`_box` 薄壁件以零厚度平板表达（设计图省料），未按实体导出——这也是设备类渲染伪影的总根因。
- D4：UV 图集对折缝小面未做合并/抑制。

## 五、处置建议（BUILD/TRIAL/ADAPT 候选，待对照实验）

1. ADAPT（小改导出器）：所有带材质绑定的 prim 显式 `ApplyMaterialBindingAPI`——消除 usdchecker 红灯。
2. TRIAL：以 Manifold/trimesh 做修复对照（D1/D2 补洞+去重+定向），与手写修复比正确性/成本。
3. ADAPT：零厚度面板按实体厚度重导出（D3），逐家族灰盒确认。
4. ADAPT：UV 图集剔除/合并零面积 UV 面（D4）。
5. 全部修复以**候选版本对照**进行，不覆盖冻结发行集（共识约束）。

## 六、局限

- 单机 macOS、pxr 本地实现；未跑 Isaac/官方 Omniverse 验证器（Linux 门）。
- 审计器自身逻辑经人工复核（首轮误判开壳为非流形，已修正区分闭壳/开壳）；`evidence/` 留全部原文可复核。
- 未定位生成端代码根因（属修复阶段，单变量纪律到此为止）。
