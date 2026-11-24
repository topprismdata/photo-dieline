# B0-B 冻结协议 (R3 round3_verdict.md §3; 本文档先于实验提交, 结果后至)

冻结时间: 2026-11-24 · 求解器: `src/photo_dieline/measurement/solve.py` 现役版 (本提交扩展多视角
`extra_views` 与共享焦距乘数 `free_fx`; 单视角路径逐位不变, 72 测试过)。

## 变体 (确定性, 覆盖常规+极端)

| id | 模型 | 参数 (mm) |
|---|---|---|
| g_regular | gable_top | W45 D45 Hb100 Hr12 Ef14 gap3.0 |
| g_wide | gable_top | W60 D28 Hb90 Hr10 Ef12 gap3.0 |
| g_tall | gable_top | W32 D32 Hb160 Hr14 Ef16 gap3.0 |
| g_deep | gable_top | W50 D70 Hb80 Hr9 Ef11 gap3.0 |
| c_regular | cuboid | W80 D50 H120 |
| c_extreme | cuboid | W100 D25 H80 |

## 视角 (az/el/roll 度, d_eye 米; FX = 50/36×768 px)

- `tq` 三分之四: (35, 18, −4, 0.81) · `front` 正面: (0, 2, 0, 0.90) · `near` 近正面: (8, 6, −2, 0.85)
- `v3_comp` 三互补: (35,18,−4,0.81) / (140,10,3,0.75) / (270,30,0,0.90)
- `v3_dup` 三近重复: (30,16,−3,0.80) / (40,20,−5,0.82) / (35,14,−2,0.79)

## 种子与配对

master 种子不入随机流; 每样本 `rng = default_rng(sha1("B0B|group|cond|variant|rep")[:16])`。
同组内各条件共享 (variant, rep) 种子 → **配对观测** (同几何同噪声底, 条件间只差被测变量)。每组 5 rep。

## 条件矩阵 (B01–B06, 按 R3 §3.1)

- **B01 尺度先验**: gable × 锚 {none, one_edge(Hb)} × 4 变体 × 5; + 先验失配 prior 模式 gap_true ∈ {2.5, 3.5}; + cuboid × {none, one_edge} × 2 × 5
- **B02 观测退化**: 视角 {front, near, tq} × 锚 {none, one_edge} × 6 变体 × 5 (预期退化格: front/near × none)
- **B03 噪声结构** (gable, one_edge): {iid, bias0.5, bias1, bias2, corr, miscorr, misspts} × 4 × 5
  - bias: 角点向投影质心内缩 m px + iid 0.3; corr: 面/顶组共享 2px 偏移 (front[0,1,4,5]/back[2,3,6,7]/roof[8..13]) + iid 0.5; miscorr: 交换相邻鳍顶 10↔11 + iid 0.3; misspts: 删两山墙尖 (idx 8,9)
- **B04 内参** (配对): 求解端 fx × {0.95, 0.98, 1.02, 1.05} (渲染真值 fx) × 6 变体 × 5, one_edge; + 部分未知: 渲染 fx×{0.97, 1.05}, 求解名义 fx + `free_fx=True` (共享乘数 s)
- **B05 视角数量**: 视角组 {tq×1, v3_comp, v3_dup} × 锚 {none, one_edge} × 6 变体 × 5
- **B06 组合压力**: corr + 渲染 fx×1.05 + free_fx + v3_dup × 锚 {none, one_edge} × 6 变体 × 5 (高置信错误 = 报警未触发且超容差)

## 指标 (R3 §3.4 全七项) 与判据

- TOL = 1.0 mm (|err_W| 或 |err_D| 超 1.0mm 记超容差); 误差只统计**未被锚定的自由参数**
- 报警规则 (冻结): `delivery != MANUFACTURING_DIMENSIONS` 或 `rms_px > 3.0` 或 `n_distinct_minima ≥ 2`
- 不可辨识召回: 预期退化格中 delivery==REFUSED 或 identifiability∈{WEAK,UNIDENTIFIABLE} 的比例
- 误拒率: 合法可辨识格 (one_edge × 正常视角/噪声) 中非 MANUFACTURING 的比例
- 2σ 经验覆盖率: 接受样本中 |err| ≤ 2σ 的比例 (自由维合并)
- 风险-覆盖率曲线: 汇集全部 one_edge 行, τ 取 sigma_W 十分位扫点, 接受 = MANUFACTURING 且 sigma_W ≤ τ

## 范围裁剪 (如实声明)

逐视角独立未知焦距不做 (与眼距完全简并, 无解可证); 六视角延后 (R3: 先证 3>1); B03 cuboid 不做 (交付模板是 gable)。
偏差与负结果一律入 findings, 不回改本协议。
