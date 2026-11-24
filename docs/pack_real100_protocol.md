# Pack-Real100 外部真值集 — 采集契约 v0.1 (WP1)

> 依据: GPT R1 判决 P0-01 — "三方尺寸对账 0.0mm 不足以证明几何正确: 三个测量对象均来自
> 同一参数母本, 即使全为零也可能是同源错误"。破局 = 每品类 ≥1 件**独立实物参照** (卡尺实测
> + 称重 + 实拍), 与生成链零共享参数源。

## 1. 参照记录 schema (每品类一条, r5_ledger.validate_anchor 兼容)

```json
{
  "ref_id": "PR-gable-001",
  "category": "gable_top",
  "product_name": "味全 300mL 白桃汁屋顶包",
  "purchase_source": "便利店/京东, 日期",
  "caliper_dims_mm": {"W": [57.1, 57.0, 57.1], "D": [38.2, 38.1, 38.2], "H": [112.4, 112.5, 112.3]},
  "scale_resolution_mm": 0.02,
  "weight_g": [23.1, 23.0, 23.1],
  "empty_weight_g": null,
  "content_volume_ml": 300,
  "board_kind": "liquid_brick",
  "photos": ["front.jpg", "back.jpg", "unfolded_if_available.jpg"],
  "dieline_source": "公开刀版 URL 或 自扫展开图 (许可声明)",
  "measured_by": "人员ID", "measured_date": "2026-12-xx",
  "anchors": [ "v0.1-A 九字段 (instrument/calibration/independence/correlation/adjudication)" ]
}
```

每维度 **≥3 次重复** → u_ref = 极差/√3 (复用 r5_ledger.u_ref, 零新约定)。

## 2. 对账口径 (与生成链的关系)

- 外部参照 vs 生成资产: `r5_ledger.compare(measured, ...)`, 接受界 = max(1mm, 2·u_ref) —
  与生成链**零共享源**, 这是独立正确性证据 (相对同源三方对账的增量);
- 判据措辞: "与实物参照的一致性", 禁"精度 X mm";
- 同源三方对账保留为**内部一致性门** (G05), 两层证据分开报告 (R1 要求)。

## 3. 品类覆盖矩阵骨架 (Coverage Matrix, R1 P0-03)

维度: 结构类别 (盒型拓扑) × 工艺类别 (封口/粘合/螺旋盖) × 商品语义类别 (乳/饮/食品/日化)。
矩阵分母 = 真实零售包装需求清单 (来源: 超市实拍盘点 + 冷柜对账台账既有品类)。
产物: `docs/pack10k_coverage_matrix.md` — 逐格标注 已覆盖(族ID)/未覆盖/故意不做。

## 4. 采集批次建议

首批 20 件 (4 试点家族各 5 件实售 SKU), 覆盖 W/D/H 分布两端; 与 R5 真实试验共用采购批次
(一次采购双用途: R5 观测 + Pack-Real 参照), 采购清单已在 r5_runbook §0。
