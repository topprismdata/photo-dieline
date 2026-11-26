# Sim2Real 价值实证协议 — Gable 屋顶包 (冻结于取数前)

## 目的

证明 Pack10K/TDE 合成渲染语料的**下游实用价值**: 仅用合成渲染训练的尺寸比例模型,
对**真实屋顶包照片**的几何比例预测达到可用精度。回应当前仓库诚实记录
(`data/frozen10-web/sim2real_report.json`: NOT MEASURABLE — 域错配, gable 模型误测瓦楞箱)。

## 模型与语料 (冻结, 不重训)

- 模型: `runs/e0rel/best.pt` (ResNet18, 比例输出 W/Hb, D/Hb, Hr/Hb, Ef/Hb)
- 语料: `output/tde_mve` gable_top 5010 样本 / 30 结构变体
- 合成基线 (val 比例 MAE): 1.66% (`sim2real_report.json.summary.baseline_synthetic`)

## 评测集 M1 (data/frozen_gable/)

- 真实屋顶包照片 ≥8 张, 跨 ≥3 来源渠道 (DDG 采购配方, 溯源 PROVENANCE)
- 每张: 前视或前+侧视, 屋顶可见, 无强裁切; Vision 逐张验真 (确认屋顶包形态, 剔除砖型/瓶装)
- 真值比例: 优先官方公布尺寸 (厂商 fact sheet), 缺则像素标注 (双人/双次标注差 <3% 才收)
- 沿用 `eval_frozen10.py` 契约 + I1/I2 相机豁免 (WEB-SOURCED, 逐张披露)

## 预注册判据 (取数前冻结)

| 指标 | 判定 |
|---|---|
| 主判据 | W/Hb 与 D/Hb 的 raw MAE (真实照片) |
| 价值成立 | MAE ≤ 8% |
| 弱价值 | 8% < MAE ≤ 12% |
| 无价值 (诚实负结果) | MAE > 12% → 照实发布, 列为后续工作 |
| 辅助 | Hr/Hb (屋顶高) 若 ≥50% 样本屋顶可量则报, 否则 N/A |
| 披露 | 合成→真实 gap (pp), 逐张 MAE, 渠道清单, 全部照实 |

## 边界 (诚实声明, 取数前冻结)

1. NVIDIA SimReady 无屋顶包品类 → **同任务下游对比不可测**;
   NVIDIA 对照证据保持 nv960 V-gate 层 (20.8% vs 100%), 不越界宣称。
2. 相机参数不可追溯 → I1/I2 豁免 (与 frozen10-web 同路径), 不冒充标定级精度。
3. 本实验证明的是「合成语料有下游迁移价值」, 不构成「全面超越 NVIDIA」。
4. 结果无论正负, 进 `docs/reviews/` 并 GPT 复核后才谈任何发布。
