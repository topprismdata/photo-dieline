# 门禁 V2 变异矩阵逐 ID 对账 (回应 GPT R3 §4.4)

- 探针: `audits/probes/probe12_gate_contract.py` (probe5 失效串修正版); 原始输出: `gate_v2_replay.log`
- 基线: baseline `(none)` = VALIDATED (G01 照片门按 batch 口径不计入整体状态, 其余九门 PASS)
- **探针 30 项 (此前口径 "27 项" 是 R1 时代 probe5_qa_matrix 的条数, 本轮 probe12 扩到 30, 未说明, 已更正)**
- 结果: **30/30 全部被预期机制拒绝**; 26 项由指定门 FAIL → DRAFT; 4 项为入口显式拒绝 (非崩溃):
  - #12 W=nan / #13 W=inf → `ValueError: 非法参数 W=… (须正的有限数)` (R3 后补 isfinite: 此前 nan 会穿透 `v<=0` 在 shapely 深处崩 GEOSException —— GPT 问的 "BUILD-EXC 是预期拒绝还是意外崩溃", 修复前是意外崩溃, 修复后是入口拒绝)
  - #16 全部 mt_va → SCORE → `ARError: 折线 e_glue 语义非法: 'SCORE' (须 MOUNTAIN/VALLEY)` (构建期显式拒绝)
  - #14 实测冲突 → `ARError: 实测值与几何参数不一致: W 几何=50mm 实测=45mm (|Δ|=5.000mm > 0.5mm)` (输入被拒)
- "变异是否真正改变目标几何/语义": 每项均为单点破坏 (折向向量/参数值/mt_va/面板坐标/SVG 字节/PDF 内容流), 破坏面见标签; #30 "诱饵 50mm 线" 专测 G08 是否几何量测校验条而非搜索字符串 (未缩放的真实 50mm 线段存在, 校验条实际 25mm, 仍被拒)

| # | 探针 | 实测 | FAIL 门 | 预期机制 |
|---|---|---|---|---|
| 1 | glue tdir → (−1,0,0) [粘口折向盒外] | DRAFT | G04 | G04 闭合判据 (粘口远缘偏离前脸 glue_w) |
| 2 | flapB tdir → (0,0,−1) [背底板下垂未折] | DRAFT | G04 | G04 (flapB 远缘中点不达对侧) |
| 3 | flapL tdir → (−1,0,0) [左底板折到墙外] | DRAFT | G04 | G04 (左右底板远缘不汇合) |
| 4 | flapR tdir → (1,0,0) [右底板折到墙外] | DRAFT | G04 | G04 同上 |
| 5 | finB tdir = finF tdir [两鳍重合穿插] | DRAFT | G04 | G04 (fin.top_gap ≠ fin_gap_mm) |
| 6 | finB tdir → (0,−1,0) [鳍倒伏] | DRAFT | G04 | G04 同上 |
| 7 | flapL 高 W/2 → W [左右底板穿插] | DRAFT | G04 | G04 (flapL.far.x0 ≠ 0) |
| 8 | glue 宽 12 → 2 [粘口宽错] | DRAFT | G04 | G04 (粘口远缘内移量 ≠ glue_w) |
| 9 | fin_gap_mm=40 (≥2·Ef) [超域] | DRAFT | G02,G04 | G02 参数域 (鳍倾角 ≥90°) |
| 10 | Hr=0.001 [屋脊近退化] | DRAFT | G02 | G02 参数域 (坡角 <5°) |
| 11 | W=nan | BUILD-EXC | — | 入口 ValueError (isfinite) |
| 12 | W=inf | BUILD-EXC | — | 入口 ValueError (isfinite) |
| 13 | params W=50 vs 实测 W=45 | ARError | — | 入口 ARError (实测优先合同) |
| 14 | 全部 mt_va M↔V 互换 | DRAFT | G04 | G04 fold_semantics (观察面约定) |
| 15 | 全部 mt_va → SCORE | BUILD-EXC | — | 构建期 ARError (语义枚举非法) |
| 16 | e_bk_sl tdir 加轴分量 [不垂直铰链] | DRAFT | G04 | G04 hinge_orthogonality |
| 17 | front 左移 5mm [面积重叠] | DRAFT | G03,G04,G05 | G03 展开图两两不重叠 |
| 18 | 第三块板共享折线 [非流形] | DRAFT | G03 | G03 折线共享边一致性 |
| 19 | front 改挂悬空板对角线 [错挂] | DRAFT | G03,G04 | G03 (折线端点不在父面板边上) |
| 20 | finB 上移 1mm [网断开] | DRAFT | G03,G04 | G03 单部件并集 |
| 21 | SVG 缩半 (非 1:1) | DRAFT | G07 | G07 独立 XML 解析 (页尺寸/几何越界) |
| 22 | SVG 几何清空只留层壳 | DRAFT | G07 | G07 逐层内容计数 |
| 23 | SVG CUT↔CREASE-VALLEY 语义互换 | DRAFT | G07 | G07 逐层几何核对 (层名与内容错位) |
| 24 | SVG 删除 50mm 校验条 | DRAFT | G07 | G07 校验条几何存在性 |
| 25 | SVG 校验条改 40mm | DRAFT | G07 | G07 校验条长度 50±容差 |
| 26 | PDF 校验条 50→40mm | DRAFT | G08 | G08 pypdf 独立解析 + 校验条 |
| 27 | PDF 内容流清空只剩 INFO 文本 | DRAFT | G08 | G08 图层挂载/几何计数 |
| 28 | PDF MediaBox 改 A4 | DRAFT | G08 | G08 MediaBox = 页面尺寸 |
| 29 | PDF 整体缩半 + 诱饵 50mm 线 | DRAFT | G08 | G08 (校验条实测 25mm; 诱饵线不构成通过) |
| 30 | PDF 内容流前插 0.5 缩放 cm | DRAFT | G08 | G08 同上 |

## 回答 GPT R3 §4.4 的四个问题

1. **BUILD-EXC 是预期拒绝还是意外崩溃?** 修复后三项全部为显式拒绝 (2×ValueError 非法参数, 1×ARError 语义非法), 无意外崩溃。修复前 W=nan 确为意外崩溃 (GEOSException), 已修。
2. **ARError 是探针自身异常还是被测系统拒绝?** 是被测系统显式拒绝 (实测冲突合同), 探针注入合法 JSON 后调用 build(), 系统主动 raise。
3. **拒绝是否来自预期门禁?** 见表 "FAIL 门" 列: 26/26 DRAFT 项全部包含预期门; 未出现"被不相关异常拦下"的项。
4. **变异是否真正改变了目标几何或语义?** 是; 每项附破坏面说明。此前 probe5 有两项 no-op (PDF 坐标串写错 / flapL 写成正确值), 修正后回放才暴露真漏洞 —— 本表为修正后矩阵。
